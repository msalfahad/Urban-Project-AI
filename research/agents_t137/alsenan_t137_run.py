"""T-137 read-only run: every area ARCH_TAKEOFF_V2.13 hands to MEMBRANE_FOLD_V3 (wet areas, roofs) on an architectural
DXF (the development villa's Drive copy), each layout proved by MEMBRANE_COVERAGE_PROOF_V1: the four V3 layouts that
ARCH_TAKEOFF_V2.12 / V2.13 count from and every V4 / V5 wall-frame layout, with the layout each method chooses marked.
Engine room ids, lengths, areas and counts only; nothing is written into the repository.

    python3 -I research/agents_t137/alsenan_t137_run.py <P7757.dxf> --out <scratch>/t137.json \
        [--dump-inputs <scratch>/inputs.json] [--zone-floor GF --zone-code PANTRY --zone-length 4.50 --zone-width 3.00 --zone-sheet "ground floor plan"]

Project inputs as T-096 / T-120 / T-124: research/agents_t010/sanitary_reading.json, research/agents_t071/alsenan_facts.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

PID = "development-villa-t137"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    ap.add_argument("--zone-floor", default="GF")
    ap.add_argument("--zone-code", default="PANTRY")
    ap.add_argument("--zone-length", type=float)
    ap.add_argument("--zone-width", type=float)
    ap.add_argument("--zone-sheet", default="ground floor plan")
    ap.add_argument("--dump-inputs", help="also write the folded outlines (JSON) to this scratch path, never the repo")
    a = ap.parse_args(argv)
    from engine.source import arch_measure as AM
    from engine.source import membrane_fold_v3 as F3
    from engine.source import membrane_fold_v5 as F5
    from tools import urban_boq_m9 as M
    facts = {"schema": AM.FACTS_SCHEMA,
             "sanitary_by_room": json.loads((ROOT / "research/agents_t010/sanitary_reading.json").read_text(
                 encoding="utf-8"))["items"],
             "exterior_spaces": json.loads((ROOT / "research/agents_t071/alsenan_facts.json").read_text(
                 encoding="utf-8"))}
    if a.zone_length is not None:
        facts["project_data"] = {"schema": "URBAN_PROJECT_DATA_FILE_V1", "project": PID, "records": [{
            "key": f"WET_ZONE_SIZE_{a.zone_floor}_{a.zone_code}", "project": PID, "kind": "table", "unit": "none",
            "value": {"length_m": a.zone_length, "width_m": a.zone_width}, "status": "DRAWING-VERIFIED",
            "drawing_file": Path(a.drawing).name, "drawing_number": "architectural set",
            "revision": "no revision printed", "sheet": a.zone_sheet,
            "reference": f"printed {a.zone_length:.2f} x {a.zone_width:.2f} m at the {a.zone_code} label",
            "applies_to": {"floors": [a.zone_floor], "members": [a.zone_code]},
            "reviewer_or_source": "hand reading (T-114 read the same printed size)", "entered_by": "TYPED"}]}
    seen, real_area, real_fold = [], F3.area, F3.fold

    def spy_area(**kw):
        r = real_area(**kw)
        seen.append(("area", kw))
        return r

    def spy_fold(polygon, *, holes=(), unit_m=1.0, spec=None):
        r = real_fold(polygon, holes=holes, unit_m=unit_m, spec=spec)
        seen.append(("fold", {"polygon": polygon, "holes": holes, "unit_m": unit_m, "spec": spec}))
        return r
    F3.area, F3.fold = spy_area, spy_fold
    try:
        M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.13", facts=facts, project_id=PID)
    finally:
        F3.area, F3.fold = real_area, real_fold
    # one entry per outline folded (area() folds through fold(); keep the area() call, then any fold() of its own)
    def _k(kw):
        return (repr(kw["polygon"]), repr(tuple(kw.get("holes") or ())), kw.get("unit_m", 1.0))
    named = {_k(kw) for kind, kw in seen if kind == "area"}
    areas, keys = [], set()
    for kind, kw in seen:
        key = _k(kw)
        if key in keys or (kind == "fold" and key in named):
            continue
        keys.add(key)
        areas.append((kind, kw))
    from engine.source import membrane_coverage_proof_v1 as P
    if a.dump_inputs:
        Path(a.dump_inputs).write_text(json.dumps([{k: kw.get(k) for k in ("floor", "room_id", "polygon", "holes",
                                                                         "unit_m", "spec")} for _k, kw in areas],
                                                  default=list), encoding="utf-8")
    rows = []
    for kind, kw in areas:
        try:
            r = P.prove_fold(kw["polygon"], holes=kw.get("holes") or (), unit_m=kw.get("unit_m", 1.0), spec=kw.get("spec"))
        except Exception as ex:                       # an outline the fold refuses is listed, never dropped
            rows.append({"floor": kw.get("floor"), "room_id": kw.get("room_id"), "state": "HELD", "reason": str(ex)})
            continue
        keep = ("layout", "verdict", "failures", "warnings", "surface_m2", "laid_m2", "residue_m2", "numerical_m2",
                "residues", "patches", "declared_patch_m2", "double_need", "double_need_m2", "bands", "bands_needed",
                "projection", "rolls_by_basis", "upturn_only_strips", "frame")
        rows.append({"via": kind, "floor": kw.get("floor"), "room_id": kw.get("room_id"), "floor_m2": r["floor_m2"],
                     "holes": len(kw.get("holes") or ()), "verdict": r["verdict"],
                     "chosen_v213": r["chosen_v213"], "chosen_v5": r["chosen_v5"],
                     "v3": [{k: x[k] for k in keep} for x in r["v3"]],
                     "v4": [{k: x[k] for k in keep + ("index", "name", "frame_deg") if k in x} for x in r["v4"]]})
    Path(a.out).write_text(json.dumps(rows, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    for r in rows:
        if "v3" not in r:
            print(r)
            continue
        c3, c5 = r["chosen_v213"], r["chosen_v5"]
        s3 = r["v3"][c3["layout"]] if c3["layout"] is not None else None
        s5 = r["v4"][c5["layout"]]
        bad = sorted({f.split(":")[0] for x in r["v3"] + r["v4"] for f in x["failures"]})
        print(f"{r['floor']} {r['room_id']} {r['floor_m2']} m2 holes {r['holes']} | all layouts {r['verdict']} {bad} | "
              f"V2.13 {c3['state']} {c3['rolls']} rolls: {c3['verdict']}, patches {s3 and s3['declared_patch_m2']} m2, "
              f"residue {s3 and s3['residue_m2']} m2, double {s3 and s3['double_need_m2']} | "
              f"V5 {c5['state']} {c5['rolls_by_reading']}: {c5['verdict']}, patches {s5['declared_patch_m2']} m2, "
              f"residue {s5['residue_m2']} m2, double {s5['double_need_m2']}")


if __name__ == "__main__":
    main()
