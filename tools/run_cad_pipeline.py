"""One CAD run: decode, normalize, profile, localise, measure, freeze.

    python3 -m tools.run_cad_pipeline <dwg> --json out.json \
        --converter /path/to/dwgread

Every stage records its own hash, and the adapter's fixture freeze is
re-asserted BEFORE any measurement runs — a change that alters a synthetic
known answer fails the run rather than quietly changing what a measurement
means.

The result is frozen before any human reference is opened. There is no
benchmark in this file, no take-off total, and no manual quantity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as profile
from engine import cad_regions as regions
from engine import cad_selftest as selftest
from engine import round2_selftest as round2
from engine import round3_selftest as round3
from engine import freeze_manifest as fmanifest
from engine import round4_selftest as round4
from engine import round5_selftest as round5
from engine import space_enclosure as enc
from engine import wall_role as wroles
from engine.reference_mapping import refuse_if_sealed


# The Project-2 freezes the client asked to be preserved. Each is a
# property of ITS OWN RUN and lives in that run's artefact; recomputing one
# over new geometry is a different quantity with the same name, which is
# why they are declared here and checked against the files rather than
# recalculated. ROUND_3_SYNTHETIC_HASH is the exception: it is a property
# of the round-3 CODE, so it must still compute to the same value today.
PRESERVED = {
    "PROJECT_2_CAD_BASELINE_HASH": (
        "3edf12c66f0984330d77e248", "data/runs/7757/P7757_CAD_baseline.json"),
    "PROJECT_2_CAD_ROUND2_HASH": (
        "70e2f4c34a6b1374687fb20f", "data/runs/7757/P7757_CAD_round2.json"),
    "PROJECT_2_CAD_ROUND3_HASH": (
        "e95a4c3c4a298339d9e0adb1", "data/runs/7757/P7757_CAD_round3.json"),
    "PROJECT_2_CAD_ROUND4_HASH": (
        "75d831180085a81a2b38506f", "data/runs/7757/P7757_CAD_round4.json"),
}


def _preserved() -> dict:
    """Check the earlier artefacts still carry what they were frozen at."""
    rows = {}
    for name, (want, where) in PRESERVED.items():
        path = Path(where)
        got = ""
        if path.exists():
            try:
                text = path.read_text(errors="replace")
                got = json.loads(text).get(name, "")
            except Exception:      # noqa: BLE001
                got = "UNREADABLE"
        rows[name] = {"frozen_value": want, "recorded_in": where,
                      "still_recorded_as": got,
                      "unchanged": got == want}
    return {
        "hashes": rows,
        "all_unchanged": all(r["unchanged"] for r in rows.values()),
        "what_these_are": (
            "each is a property of the run that produced it, and it lives "
            "in that run's artefact. Recomputing one over round 4's "
            "geometry is a DIFFERENT quantity wearing the same name, so "
            "this round reports those separately and never overwrites "
            "these files"),
    }


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def run(dwg: str, *, converter: str = "", work_dir: str = "data/runs/cad_convert",
        decode_json: str = "") -> dict:
    refuse_if_sealed(dwg)
    path = Path(dwg)
    src_hash = _hash(path)

    # Both freeze gates, BEFORE anything is measured. A change that alters
    # a synthetic known answer, or that lets a site or super-region become
    # releasable, fails the run rather than changing what a measurement
    # means.
    freeze = selftest.assert_frozen()
    r2 = round2.assert_frozen()
    r3 = round3.assert_frozen()
    r4 = round4.assert_frozen()
    r5 = round5.assert_frozen()
    fmanifest.assert_no_artifact_was_rewritten()

    if decode_json and Path(decode_json).exists():
        decoded = json.loads(Path(decode_json).read_text(errors="replace"))
        decode_rec = {"reused_existing_decode": decode_json,
                      "json_sha256_16": _hash(Path(decode_json))}
    else:
        from tools.audit_cad_source import _find_converter

        conv = _find_converter(converter)
        if not conv:
            return {
                "run_outcome": "STOPPED_BEFORE_COMPLETION",
                "stopped_with": "NO_DWG_CONVERTER_AVAILABLE",
                "why": ("DWG is a proprietary binary format and no decoder "
                        "was found. NOTHING is known about this drawing, "
                        "which is NOT a finding that it is empty"),
                "every_metric_here": "NOT_ESTABLISHED",
                "source_sha256_16": src_hash,
            }
        out_json = decode_json or str(
            Path(work_dir) / (path.stem + ".json"))
        from engine import cad_source as cad

        decode_rec = cad.decode(dwg, converter=conv, out_json=out_json)
        decode_rec["json_sha256_16"] = _hash(Path(out_json))
        decoded = json.loads(Path(out_json).read_text(errors="replace"))

    nd = adapter.normalize(decoded, source_file=path.name,
                           source_hash=src_hash)
    prof = profile.build(nd)
    sweep = regions.sweep(nd.primitives)
    rep = measure.measure(nd, prof)

    # Second-stage wall roles, from occupancy rather than from layer names.
    cands = measure.wall_candidates(nd, prof.wall_like_layers())
    released_polys = [r.enclosure.polygon_wkt for r in rep.rows
                      if r.enclosure and r.enclosure.polygon_wkt]
    wall_rep = wroles.classify(
        cands, interior=_occupancy(released_polys)) if released_polys \
        else wroles.WallRoleReport()

    return {
        "run_outcome": "COMPLETED",
        "source": {"file": path.name, "sha256_16": src_hash,
                   "bytes": path.stat().st_size,
                   "format_marker": path.read_bytes()[:6].decode(
                       "latin-1", "replace")},
        "decoder": decode_rec,
        "adapter_freeze": {
            "CAD_ADAPTER_HASH": freeze["CAD_ADAPTER_HASH"],
            "CAD_FIXTURE_FREEZE_HASH": freeze["CAD_FIXTURE_FREEZE_HASH"],
            "fixtures": freeze["fixtures"], "passed": freeze["passed"],
            "failed": freeze["failed"]},
        "enclosure_freeze": {
            "algorithm": enc.ALGORITHM, "hash": enc.freeze_hash()},
        "normalization": nd.record(),
        "source_profile": prof.record(),
        "drawing_regions": {
            "algorithm": regions.ALGORITHM,
            "REGION_FREEZE_HASH": regions.freeze_hash(),
            "frozen_parameters": regions.frozen_parameters(),
            "total_marks": sweep["total_marks"],
            "cluster_count_by_distance": [
                {"distance_mm": d, "major_clusters": n}
                for d, n in sweep["counts"]],
            "plateaus": [p.record() for p in sweep["plateaus"]],
            "candidate_regions_at_most_stable_fine_partition": [
                regions.label(c, texts=nd.texts, dimensions=nd.dimensions,
                              instances=nd.instances,
                              primitives=nd.primitives)
                for c in _finest_stable(sweep)],
        },
        "round_2_freeze": {
            "ROUND_2_SYNTHETIC_HASH": r2["ROUND_2_SYNTHETIC_HASH"],
            "ENCLOSURE_ROLE_CLASSIFIER_HASH":
                r2["ENCLOSURE_ROLE_CLASSIFIER_HASH"],
            "SEMANTIC_SEED_CLASSIFIER_HASH":
                r2["SEMANTIC_SEED_CLASSIFIER_HASH"],
            "WALL_ROLE_HASH": wroles.classifier_hash(),
            "cases": r2["cases"], "passed": r2["passed"],
            "failed": r2["failed"], "safety_result": r2["safety_result"]},
        "round_3_freeze": {
            "ROUND_3_SYNTHETIC_HASH": r3["ROUND_3_SYNTHETIC_HASH"],
            "ROOM_BOUNDARY_AUTHORITY_HASH":
                r3["ROOM_BOUNDARY_AUTHORITY_HASH"],
            "MULTILINGUAL_IDENTITY_HASH": r3["MULTILINGUAL_IDENTITY_HASH"],
            "ONTOLOGY_HASH": r3["ONTOLOGY_HASH"],
            "cases": r3["cases"], "passed": r3["passed"],
            "failed": r3["failed"],
            "required_results_held": r3["required_results_held"]},
        "round_4_freeze": {
            "ROUND_4_SYNTHETIC_HASH": r4["ROUND_4_SYNTHETIC_HASH"],
            "DRAWING_REGION_HASH": r4["DRAWING_REGION_HASH"],
            "CAD_OPENING_CLASSIFIER_HASH": r4["CAD_OPENING_CLASSIFIER_HASH"],
            "PORTAL_MATCHER_HASH": r4["PORTAL_MATCHER_HASH"],
            "ROOM_PARTITION_GRAPH_HASH": r4["ROOM_PARTITION_GRAPH_HASH"],
            "cases": r4["cases"], "passed": r4["passed"],
            "failed": r4["failed"],
            "required_results_held": r4["required_results_held"]},
        "round_5_freeze": {
            "ROUND_5_SYNTHETIC_HASH": r5["ROUND_5_SYNTHETIC_HASH"],
            "FREEZE_MANIFEST_SCHEMA_HASH": r5["FREEZE_MANIFEST_SCHEMA_HASH"],
            "PHYSICAL_WALL_BAND_HASH": r5["PHYSICAL_WALL_BAND_HASH"],
            "PARTITION_CONTINUITY_HASH": r5["PARTITION_CONTINUITY_HASH"],
            "JUNCTION_RECOVERY_HASH": r5["JUNCTION_RECOVERY_HASH"],
            "FACE_SUBDIVISION_HASH": r5["FACE_SUBDIVISION_HASH"],
            "cases": r5["cases"], "passed": r5["passed"],
            "failed": r5["failed"],
            "required_results_held": r5["required_results_held"]},
        "freeze_manifest": fmanifest.manifest(),
        "wall_roles": wall_rep.record(),
        "measurement": rep.record(),
        "round_4_counts": _round4_counts(rep),
        "round_5_counts": _round5_counts(rep),
        "large_multi_observation_faces": _undersegmented(rep),
        "dimension_cross_check_status": _dimension_status(rep),
        "complete_physical_spaces": _per_complete_space(rep),
        "preserved_project_2_hashes": _preserved(),
        "PROJECT_2_CAD_ROUND5_HASH": _round5_hash(nd, prof, rep, src_hash,
                                                  r5),
        "recomputed_under_round_5": {
            "why": ("each earlier round's PROJECT hash is a property of "
                    "ITS run. Round 5 measures differently, so recomputing "
                    "those chains here produces different numbers under "
                    "the same names. They are shown for comparison only "
                    "and are NOT the preserved values, which are declared "
                    "and verified above"),
            "PROJECT_2_CAD_BASELINE_HASH_RECOMPUTED":
                _baseline(nd, prof, rep, src_hash),
            "PROJECT_2_CAD_ROUND2_HASH_RECOMPUTED":
                _round2_hash(nd, prof, rep, src_hash, r2),
            "PROJECT_2_CAD_ROUND3_HASH_RECOMPUTED":
                _round3_hash(nd, prof, rep, src_hash, r2, r3),
            "PROJECT_2_CAD_ROUND4_HASH_RECOMPUTED":
                _round4_hash(nd, prof, rep, src_hash, r4),
        },
        "no_human_reference_was_opened": True,
        "what_is_absent_from_this_record": (
            "any benchmark, any architect take-off total, any manual "
            "quantity, any Excel, any structural or sanitary quantity"),
    }


def _round4_counts(rep) -> dict:
    """§14's list, in §14's order, with nothing added and nothing merged."""
    from engine import enclosure_role as roles

    c = rep.counts()
    oc = rep.openings.counts() if rep.openings else {}
    mc = rep.matches.counts() if rep.matches else {}
    cycles = sum(g.counts()["graph_cycles"] for g in rep.graphs)
    rejected = sum(1 for r in rep.rows if r.enclosure_role in (
        roles.SITE_OR_PLOT, roles.BUILDING_ENVELOPE, roles.SUPER_REGION,
        roles.DETAIL_OR_ANNOTATION))
    return {
        "DRAWING_REGION_count": (rep.regions.counts()["drawing_regions"]
                                 if rep.regions else 0),
        "wall_boundary_candidates": rep.candidate_lines,
        "wall_like_candidates_before_authority": rep.all_candidate_lines,
        "door_candidates": oc.get("door_candidates", 0),
        "window_candidates": oc.get("window_candidates", 0),
        "validated_portals": oc.get("may_partition_rooms", 0),
        "openings_that_may_close_a_boundary": oc.get(
            "may_close_a_boundary", 0),
        "doorless_openings": oc.get("doorless_openings", 0),
        "unresolved_gaps": oc.get("unresolved_wall_gaps", 0),
        "ambiguous_portal_hosts": mc.get("ambiguous_portal_hosts", 0),
        "room_partition_graph_cycles": cycles,
        "physical_space_candidates": c["space_candidates"],
        "complete_spaces": c["complete"],
        "partial_spaces": c["partial"],
        "unresolved_spaces": c["unresolved"],
        "identity_established": c["identity_established"],
        "identity_unknown": c["identity_unknown"],
        "functional_zone_groups": c["functional_zone_groups"],
        "release_eligible": c["release_eligible"],
        "false_or_super_region_rejections": rejected,
        "by_enclosure_role": c["by_enclosure_role"],
        "openings_by_class": oc.get("by_class", {}),
        "openings_by_grade": oc.get("by_grade", {}),
        "portal_hosts_by_status": mc.get("by_status", {}),
        "unmatched_door_symbols": oc.get("unmatched_door_symbols", 0),
    }


def _round5_counts(rep) -> dict:
    """§15's list, in §15's order."""
    from engine import face_subdivision as fsub
    from engine import partition_continuity as pcont

    c = rep.counts()
    spans = [s for x in rep.continuity for s in x.spans]
    junctions = [j for x in rep.junctions for j in x.junctions]
    walls = [w for x in rep.walls for w in x.walls]
    diagnoses = [d for x in rep.subdivisions for d in x.diagnoses]
    cycles = sum(g.counts()["graph_cycles"] for g in rep.graphs)
    protected = sum(1 for s in spans
                    if s.verdict == pcont.OPENING_INTERRUPTION)
    return {
        "drawing_regions": (rep.regions.counts()["drawing_regions"]
                            if rep.regions else 0),
        "observed_wall_bands": len(walls),
        "walls_with_a_half_drawn_span": sum(
            1 for w in walls if w.half_drawn()),
        "walls_with_an_undrawn_gap": sum(1 for w in walls if w.gaps()),
        "established_physical_partitions": sum(
            1 for s in spans if s.verdict == pcont.ESTABLISHED),
        "supported_continuations": sum(
            1 for s in spans if s.verdict == pcont.SUPPORTED),
        "unresolved_gaps": sum(
            1 for s in spans if s.verdict == pcont.UNRESOLVED_GAP),
        "no_continuation": sum(
            1 for s in spans if s.verdict == pcont.NO_CONTINUATION),
        "protected_openings": protected,
        "junction_recoveries": sum(1 for j in junctions if j.is_recovered),
        "junctions_not_recovered": sum(
            1 for j in junctions if j.status == jrec_not_recovered()),
        "columns_observed": sum(len(x.columns) for x in rep.junctions),
        "room_partition_cycles": cycles,
        "physical_space_polygons": c["space_candidates"],
        "possible_undersegmented_polygons": len(diagnoses),
        "undersegmentation_by_classification": dict(
            __import__("collections").Counter(
                d.outcome for d in diagnoses).most_common()),
        "functional_zone_groups": c["functional_zone_groups"],
        "complete": c["complete"],
        "partial": c["partial"],
        "unresolved": c["unresolved"],
        "identity_established": c["identity_established"],
        "identity_unknown": c["identity_unknown"],
        "release_eligible": c["release_eligible"],
        "spaces_closed_with_a_recovered_span": c[
            "spaces_closed_with_a_recovered_span"],
        "spaces_with_material_authority": c["spaces_with_material_authority"],
        "recovered_partition_length_m": round(sum(
            x.counts()["recovered_length_m"] for x in rep.continuity), 3),
        "outcomes": list(fsub.OUTCOMES),
    }


def jrec_not_recovered() -> str:
    from engine import junction_recovery as jrec

    return jrec.NOT_RECOVERED


def _undersegmented(rep) -> list:
    """§16, for every polygon holding more than one space observation."""
    return [d.record() for x in rep.subdivisions for d in x.diagnoses]


def _dimension_status(rep) -> dict:
    """§17, stated without flattering it."""
    from engine import cad_measure as measure

    checks = [d for r in rep.rows for d in r.dimension_checks]
    counts = {v: sum(1 for d in checks if d["verdict"] == v)
              for v in (measure.AGREE, measure.DISAGREE, measure.AMBIGUOUS,
                        measure.NOT_APPLICABLE, measure.NOT_PRESENT)}
    return {
        "associations_attempted": len(checks),
        **counts,
        "what_this_is_not": (
            f"{len(checks)} associations were ATTEMPTED. "
            f"{counts[measure.AGREE]} of them are agreements between an "
            "authored dimension and a measured span. The rest found no "
            "dimension to compare, or no side to compare one against, and "
            "none of those is a validation"),
        "never": ("no geometry was adjusted to make a dimension agree, and "
                  "no dimension is required for release"),
    }


def _per_complete_space(rep) -> list:
    """§15, for every space whose boundary actually closed."""
    out = []
    for r in rep.rows:
        if not r.is_complete:
            continue
        rec = r.record()
        out.append({
            "space_id": rec["space_id"],
            "drawing_region_id": rec["drawing_region_id"],
            "polygon_hash": rec["geometry_hash"],
            "area_m2": rec["clear_area_m2"],
            "clear_internal_perimeter_m": rec["clear_internal_perimeter_m"],
            "principal_clear_dimensions_mm": rec[
                "principal_clear_dimensions_mm"],
            "boundary_trace": rec["boundary_segments"],
            "opening_table": rec["boundary_openings"],
            "room_partition_relations": rec["room_partition_relations"],
            "quantity_ontology": rec["quantity_ontology"],
            "TOPOLOGY_AUTHORITY": rec["TOPOLOGY_AUTHORITY"],
            "MATERIAL_AUTHORITY": rec["MATERIAL_AUTHORITY"],
            "material_boq_status": rec["material_boq_status"],
            "recovered_boundary_spans": rec["recovered_boundary_spans"],
            "identity": {
                "identity_observations": rec["room_name_observations"],
                "reconciled_concept": rec["normalized_identity"],
                "identity_status": rec["identity_status"],
                "independent_statements": rec[
                    "independent_identity_statements"],
                "functional_zones": rec["functional_zones"]},
            "dimension_cross_check": rec["dimension_cross_check"],
            "enclosure_role": rec["enclosure_role"],
            "physical_space_status": rec["physical_space_status"],
            "release_status": rec["release_status"],
            "blocker": rec["blocker"],
        })
    return out


def _finest_stable(sweep) -> list:
    """The clusters of the most stable partition with the most regions.

    Deliberately the FINEST stable answer rather than the coarsest: two
    sheets merged into one region cannot be separated later, while two
    halves of one sheet remain visible as neighbours.
    """
    if not sweep["plateaus"]:
        return []
    best = max(sweep["plateaus"],
               key=lambda p: (p.stability, p.major_count))
    total = sweep["total_marks"]
    for part in sweep["partitions"]:
        if part.distance_mm == best.from_mm:
            return part.major(total)
    return []


def _occupancy(polygons):
    """A point is occupied when some measured enclosure contains it."""
    from shapely.geometry import Point
    from shapely.wkt import loads

    shapes = []
    for wkt in polygons:
        try:
            shapes.append(loads(wkt))
        except Exception:   # noqa: BLE001
            continue

    def inside(x, y):
        pt = Point(x, y)
        return any(s.contains(pt) for s in shapes)

    return inside


def _round2_hash(nd, prof, rep, src_hash: str, r2: dict) -> str:
    """The round-2 baseline: round 1's components plus the new classifiers."""
    parts = [
        _baseline(nd, prof, rep, src_hash),
        f"roles={r2['ENCLOSURE_ROLE_CLASSIFIER_HASH']}",
        f"seeds={r2['SEMANTIC_SEED_CLASSIFIER_HASH']}",
        f"walls={wroles.classifier_hash()}",
        f"synthetic={r2['ROUND_2_SYNTHETIC_HASH']}",
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _round3_hash(nd, prof, rep, src_hash: str, r2: dict, r3: dict) -> str:
    """Round 2's baseline plus round 3's authority, identity and vocabulary."""
    parts = [
        _round2_hash(nd, prof, rep, src_hash, r2),
        f"authority={r3['ROOM_BOUNDARY_AUTHORITY_HASH']}",
        f"identity={r3['MULTILINGUAL_IDENTITY_HASH']}",
        f"ontology={r3['ONTOLOGY_HASH']}",
        f"synthetic={r3['ROUND_3_SYNTHETIC_HASH']}",
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _round4_hash(nd, prof, rep, src_hash: str, r4: dict) -> str:
    """The PRESERVED round-3 lineage, plus round 4's own components.

    Anchored to the frozen round-3 STRING rather than to a recomputation of
    it: round 4 changed the measurement, so recomputing round 3's chain
    here would silently redefine a hash the client asked to be preserved.
    """
    parts = [
        PRESERVED["PROJECT_2_CAD_ROUND3_HASH"][0],
        f"source={src_hash}",
        f"adapter={adapter.adapter_hash()}",
        f"normalization={nd.normalization_hash()}",
        f"profile={prof.profile_hash()}",
        f"enclosure={enc.freeze_hash()}",
        f"spaces={rep.baseline_hash()}",
        f"regions={r4['DRAWING_REGION_HASH']}",
        f"openings={r4['CAD_OPENING_CLASSIFIER_HASH']}",
        f"matcher={r4['PORTAL_MATCHER_HASH']}",
        f"graph={r4['ROOM_PARTITION_GRAPH_HASH']}",
        f"synthetic={r4['ROUND_4_SYNTHETIC_HASH']}",
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _round5_hash(nd, prof, rep, src_hash: str, r5: dict) -> str:
    """The PRESERVED round-4 lineage, plus round 5's own components.

    Anchored to round 4's frozen STRING for the same reason round 4 was
    anchored to round 3's: recomputing an earlier round's chain over new
    geometry silently redefines a hash somebody was asked to preserve.
    """
    parts = [
        PRESERVED["PROJECT_2_CAD_ROUND4_HASH"][0],
        f"manifest={r5['FREEZE_MANIFEST_SCHEMA_HASH']}",
        f"walls={r5['PHYSICAL_WALL_BAND_HASH']}",
        f"continuity={r5['PARTITION_CONTINUITY_HASH']}",
        f"junctions={r5['JUNCTION_RECOVERY_HASH']}",
        f"subdivision={r5['FACE_SUBDIVISION_HASH']}",
        f"synthetic={r5['ROUND_5_SYNTHETIC_HASH']}",
        f"source={src_hash}",
        f"adapter={adapter.adapter_hash()}",
        f"normalization={nd.normalization_hash()}",
        f"profile={prof.profile_hash()}",
        f"enclosure={enc.freeze_hash()}",
        f"spaces={rep.baseline_hash()}",
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _baseline(nd, prof, rep, src_hash: str) -> str:
    """One hash over every frozen component of this run."""
    parts = [
        f"source={src_hash}",
        f"adapter={adapter.adapter_hash()}",
        f"normalization={nd.normalization_hash()}",
        f"profile={prof.profile_hash()}",
        f"regions={regions.freeze_hash()}",
        f"enclosure={enc.freeze_hash()}",
        f"spaces={rep.baseline_hash()}",
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dwg")
    ap.add_argument("--json", default="")
    ap.add_argument("--converter", default="")
    ap.add_argument("--work-dir", default="data/runs/cad_convert")
    ap.add_argument("--decode-json", default="",
                    help="reuse an existing decode instead of re-running it")
    a = ap.parse_args(argv)
    rec = run(a.dwg, converter=a.converter, work_dir=a.work_dir,
              decode_json=a.decode_json)
    text = json.dumps(rec, indent=2, ensure_ascii=False, default=str)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {a.json}")
    print(json.dumps({
        "run_outcome": rec.get("run_outcome"),
        "PROJECT_2_CAD_ROUND5_HASH": rec.get("PROJECT_2_CAD_ROUND5_HASH"),
        "round_5_counts": rec.get("round_5_counts"),
        "preserved_project_2_hashes": rec.get(
            "preserved_project_2_hashes", {}).get("all_unchanged"),
        "round_5_freeze": rec.get("round_5_freeze"),
        "adapter_freeze": rec.get("adapter_freeze"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
