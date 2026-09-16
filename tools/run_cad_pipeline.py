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
from engine import space_enclosure as enc
from engine import wall_role as wroles
from engine.reference_mapping import refuse_if_sealed


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
        "wall_roles": wall_rep.record(),
        "measurement": rep.record(),
        "PROJECT_2_CAD_BASELINE_HASH": _baseline(nd, prof, rep, src_hash),
        "PROJECT_2_CAD_ROUND2_HASH": _round2_hash(
            nd, prof, rep, src_hash, r2),
        "PROJECT_2_CAD_ROUND3_HASH": _round3_hash(
            nd, prof, rep, src_hash, r2, r3),
        "no_human_reference_was_opened": True,
        "what_is_absent_from_this_record": (
            "any benchmark, any architect take-off total, any manual "
            "quantity, any Excel, any structural or sanitary quantity"),
    }


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
        "PROJECT_2_CAD_BASELINE_HASH": rec.get(
            "PROJECT_2_CAD_BASELINE_HASH"),
        "PROJECT_2_CAD_ROUND2_HASH": rec.get("PROJECT_2_CAD_ROUND2_HASH"),
        "PROJECT_2_CAD_ROUND3_HASH": rec.get("PROJECT_2_CAD_ROUND3_HASH"),
        "round_3_freeze": rec.get("round_3_freeze"),
        "adapter_freeze": rec.get("adapter_freeze"),
        "counts": rec.get("measurement", {}).get("counts"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
