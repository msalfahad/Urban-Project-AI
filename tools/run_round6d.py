"""Round 6D on P7757: the two repairs, the pantry, and the stairs.

§17. Seven answers and no prices:

    A  the generic wall stretch-ownership repair
    B  the fitting / host-wall precedence repair
    C  what changed in the physical-space register since round 6C
    D  the pantry classification: CLOSED / OPEN_AMERICAN / UNKNOWN
    E  the pantry's functional-zone evidence
    F  the pantry's actual host walls
    G  the stair assemblies, tread by tread and riser by riser

Nothing here prices anything, applies a waste factor or writes a BOQ.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import fitting_band as fband
from engine import floor_register as freg
from engine import functional_zone as fz
from engine import round6d_selftest as r6d
from engine import semantic_seed as seeds_mod
from engine import space_register as sreg
from tools import run_round6c as r6c

STAGE = "ROUND_6D_GEOMETRY_REPAIRS_PANTRY_AND_STAIRS"

# §8. P7757's own finish rule, disclosed as a PROJECT rule and applied to
# nothing but this project's report.
P7757_STAIR_FINISH = "STAIR_MARBLE_SURROUNDING_FLOOR_PORCELAIN"

# What round 6C released, to compare against. Not a target: a baseline.
ROUND_6C = {"MEASURED_CANDIDATE_AREA_M2": 269.1838,
            "MEASURED_CANDIDATES": 40,
            "RELEASE_ELIGIBLE_GEOMETRY_AREA_M2": 26.3085,
            "RELEASE_ELIGIBLE_GEOMETRY": 6}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _faces(rep, rows) -> list:
    face_of = {}
    for r in rep.rows:
        c = r.clear
        face_of[r.space_id] = [
            {"axis": f.axis, "fixed_mm": f.fixed_mm,
             "length_mm": f.length_mm, "basis": f.basis,
             "wall_band_id": f.wall_band_id, "face_id": f.face_id}
            for f in (c.boundary_faces if c is not None else ())]
    out = []
    for row in rows:
        row = dict(row)
        row["boundary_faces"] = face_of.get(row["space_id"], [])
        out.append(row)
    return out


def _stretch_audit(rep) -> dict:
    """§17A. Does any line have two owners left?"""
    by_line: dict = {}
    for wr in rep.walls:
        for w in wr.walls:
            for f in (w.face_a_mm, w.face_b_mm):
                for lo, hi in w.owned_mm:
                    # the line the engine itself would call one line
                    by_line.setdefault(
                        (w.region_id, w.axis, round(f / 1.0)), []
                    ).append((lo, hi, w.wall_id))
    clashes = []
    for key, rows in sorted(by_line.items()):
        rows.sort()
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                if a[2] == b[2]:
                    continue
                ov = min(a[1], b[1]) - max(a[0], b[0])
                if ov > 1.0:
                    clashes.append({"line": list(key), "a": a[2],
                                    "b": b[2],
                                    "overlap_mm": round(ov, 1)})
    walls = [w for wr in rep.walls for w in wr.walls]
    return {
        "bands": len(walls),
        "bands_owning_several_disjoint_stretches": sum(
            1 for w in walls if len(w.owned_mm) > 1),
        "two_walls_owning_one_stretch_of_one_line": len(clashes),
        "clashes": clashes[:10],
        "what_this_proves": (
            "a wall owns the stretches it is drawn along and the gaps "
            "inside itself, and nothing that belongs to the wall next to "
            "it. A hull could not say that"),
    }


def _fitting_audit(rep) -> dict:
    """§17B. Which bands are fittings, and what they were refused."""
    out = []
    for f in rep.fittings:
        for _k, st in sorted((f.fittings or {}).items()):
            rec = st.record()
            rec["drawing_region_id"] = f.region_id
            out.append(rec)
    rooms_at_a_front = []
    fits = {k: v for f in rep.fittings
            for k, v in (f.fittings or {}).items()}
    for r in rep.rows:
        c = r.clear
        if c is None:
            continue
        for face in c.boundary_faces:
            st = fits.get(face.wall_band_id)
            if st is not None and abs(face.fixed_mm - st.far_face_mm) \
                    <= fband.SAME_PLACE_MM:
                rooms_at_a_front.append(
                    {"space_id": r.space_id, "fitting": st.lining_id})
    return {
        "fittings": len(out),
        "rooms_measured_to_a_fitting_front": len(rooms_at_a_front),
        "detail": out,
        "what_this_proves": (
            "no room's clear internal finish face is at the front of a "
            "fitting. The room a fitting stands in is measured to the "
            "wall behind it"),
    }


def run(decode_json: str, *, supervised_json: str = "",
        sections_json: str = "") -> dict:
    r6ds = r6d.assert_frozen()

    decode = json.loads(Path(decode_json).read_text(encoding="utf-8"))
    nd = adapter.normalize(decode, source_file="P7757_ARCHITECTURAL.dwg",
                           source_hash="7f61f3acdd62d62d")
    sections = {}
    if sections_json and Path(sections_json).exists():
        sections = json.loads(Path(sections_json).read_text(
            encoding="utf-8")).get("sections", {})
    rep = measure.measure(
        nd, cprofile.build(nd), semantic=seeds_mod.classify(nd.texts),
        sections=sections,
        project_rules={"stair_finish_rule": P7757_STAIR_FINISH})

    supervised, note = {}, "none supplied"
    if supervised_json and Path(supervised_json).exists():
        data = json.loads(Path(supervised_json).read_text(encoding="utf-8"))
        supervised = data.get("assignments", {})
        note = supervised_json

    built = freg.assemble(nd, rep, supervised=supervised)
    register, roles = built["register"], built["roles"]
    rows = _faces(rep, built["rows"])
    zones = fz.assess(rows, register.labels, floor_of=built["floor_of"],
                      fittings=built["linings"],
                      wall_bands=[w for wr in rep.walls for w in wr.walls])

    assemblies = [a for s in rep.stairs for a in s.assemblies]
    refused = [x for s in rep.stairs for x in s.refused]

    # §12. The same square metre may not be marble and porcelain.
    double = []
    from shapely.wkt import loads

    by_id = {r["space_id"]: r for r in rows}
    for a in assemblies:
        try:
            foot = loads(a.footprint_wkt)
        except Exception:      # noqa: BLE001
            continue
        for e in register.entries:
            if not e.released:
                continue
            g = (by_id.get(e.space_id) or {}).get("polygon")
            if g is None:
                continue
            try:
                shared = g.intersection(foot).area
            except Exception:      # noqa: BLE001
                continue
            if shared > 1000.0:
                double.append({"space_id": e.space_id,
                               "stair_id": a.stair_id,
                               "shared_m2": round(shared / 1e6, 4)})

    # A stair may not measure more tread than its own footprint covers.
    over = [{"stair_id": a.stair_id,
             "tread_m2": round(a.tread_m2, 4),
             "footprint_m2": round(a.footprint_area_m2, 4),
             "reported_as": a.record()["MEASURED_NET"]["TREAD_M2"],
             "exceptions": list(a.exceptions)}
            for a in assemblies
            if a.tread_m2 > a.footprint_area_m2 + 0.001]

    areas = register.areas()
    out = {
        "stage": STAGE,
        "source": {"file": "P7757_ARCHITECTURAL.dwg",
                   "sha256_16": "7f61f3acdd62d62d"},
        "supervised_floor_assignment": note,
        "section_evidence": (sections_json or "none supplied"),
        "synthetics_that_passed_first": {
            "round_6d": f"{r6ds['passed']}/{r6ds['cases']}",
            "ROUND_6D_SYNTHETIC_HASH": r6ds["ROUND_6D_SYNTHETIC_HASH"]},
        "A_wall_stretch_ownership": _stretch_audit(rep),
        "B_fitting_and_host_wall_precedence": _fitting_audit(rep),
        "C_register_changes_since_round_6c": {
            "round_6c": ROUND_6C,
            "round_6d": {k: areas[k] for k in ROUND_6C},
            "by_candidate_role": register.counts()["by_candidate_role"],
            "labels_mapped_exactly_once":
                register.counts()["labels_mapped_exactly_once"],
            "protected_geometry": r6c._protected(rows),
            "false_negative_candidates":
                r6c._false_negative_analysis(rows, register),
        },
        "D_E_F_pantry": zones.record(),
        "G_stairs": {
            "counts": {
                "assemblies": len(assemblies),
                "flights": sum(len(a.flights) for a in assemblies),
                "treads": sum(len(f.treads) for a in assemblies
                              for f in a.flights),
                "risers": sum(len(f.risers) for a in assemblies
                              for f in a.flights),
                "landings": sum(len(a.landings) for a in assemblies),
                "runs_refused_as_not_a_stair": len(refused),
                "riser_quantity_established": sum(
                    1 for a in assemblies if a.riser_m2 is not None),
            },
            "project_rule": P7757_STAIR_FINISH,
            "MEASURED_NET_TOTALS": {
                "TREAD_M2": (None if any(
                    a.record()["MEASURED_NET"]["TREAD_M2"] is None
                    for a in assemblies)
                    else round(sum(a.tread_m2 for a in assemblies), 4)),
                "TREAD_M2_ESTABLISHED_ASSEMBLIES_ONLY": round(sum(
                    a.tread_m2 for a in assemblies
                    if a.record()["MEASURED_NET"]["TREAD_M2"]
                    is not None), 4),
                "RISER_M2": (None if any(a.riser_m2 is None
                                         for a in assemblies)
                             else round(sum(a.riser_m2 or 0.0
                                            for a in assemblies), 4)),
                "LANDING_M2": round(sum(a.landing_m2
                                        for a in assemblies), 4),
                "NOSING_LM": round(sum(a.nosing_lm for a in assemblies), 3),
                "STAIR_SKIRTING_LM": None,
                "this_is": ("measured net. No waste factor, no "
                            "procurement quantity and no price"),
            },
            "assemblies": [a.record() for a in assemblies],
            "refused": refused,
        },
        "a_stair_never_measures_more_than_it_covers": {
            "assemblies_measuring_more_tread_than_footprint": len(over),
            "detail": over,
            "rule": ("two flights side by side share their tread "
                     "positions. Each tread is clipped to its own flight"),
        },
        "marble_and_porcelain_do_not_overlap": {
            "released_rooms_sharing_a_stair_footprint": len(double),
            "detail": double,
            "rule": ("where the stair finish is marble the same square "
                     "metre is not also porcelain"),
        },
        "areas_kept_apart": areas,
        "completeness_per_floor": sreg.completeness(register),
        "drawing_regions": roles.counts(),
        "what_this_run_is_not": (
            "no TradeMeasurementZone engine, no floor ceramic, no wall "
            "ceramic, no waste rule, no pricing, no contractor rates and "
            "no Firebase"),
    }
    out["ROUND_6D_REPORT_HASH"] = _sha(
        json.dumps(out, sort_keys=True, default=str))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decode-json", required=True)
    ap.add_argument("--supervised", default="")
    ap.add_argument("--sections", default="")
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    rec = run(a.decode_json, supervised_json=a.supervised,
              sections_json=a.sections)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(
            json.dumps(rec, indent=2, ensure_ascii=False, default=str)
            + "\n", encoding="utf-8")
        print(f"wrote {a.json}")
    print(json.dumps({
        "ROUND_6D_REPORT_HASH": rec["ROUND_6D_REPORT_HASH"],
        "A": {k: v for k, v in rec["A_wall_stretch_ownership"].items()
              if k != "clashes" and k != "what_this_proves"},
        "B": {k: v for k, v in
              rec["B_fitting_and_host_wall_precedence"].items()
              if k != "detail" and k != "what_this_proves"},
        "C": rec["C_register_changes_since_round_6c"]["round_6d"],
        "D_E_F": rec["D_E_F_pantry"]["counts"],
        "G": rec["G_stairs"]["counts"],
        "totals": rec["G_stairs"]["MEASURED_NET_TOTALS"],
        "double_count": rec["marble_and_porcelain_do_not_overlap"][
            "released_rooms_sharing_a_stair_footprint"],
        "tread_over_footprint": rec[
            "a_stair_never_measures_more_than_it_covers"][
                "assemblies_measuring_more_tread_than_footprint"],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
