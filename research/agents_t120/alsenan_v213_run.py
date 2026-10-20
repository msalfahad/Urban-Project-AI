"""T-120 read-only run for the verifier: ARCH_TAKEOFF_V2.12 and ARCH_TAKEOFF_V2.13 on the same architectural DXF (the
development villa's Drive copy, P7757_DXF_COMPRESSED.zip), with the pantry's printed size typed as a project data
record (owner Q-37 A, Q-17 A). Prints the V2.13 purchase rows (areas, counts, metres and engine room ids only), the
Q-58 A proof of every area V2.12 holds on Q-58, the typed wet zones and every BOQ line that differs. Nothing is
written into the repository.

    python3 -I research/agents_t120/alsenan_v213_run.py <P7757.dxf> --out <scratch>/t120.json \
        [--zone-floor GF --zone-code PANTRY --zone-length 4.50 --zone-width 3.00 --zone-sheet "<sheet>"]

Project inputs as T-096: research/agents_t010/sanitary_reading.json and research/agents_t071/alsenan_facts.json.
The zone record is built from the arguments (the printed size the verifier reads on the plan; T-114 read 450 x 300 on
the ground-floor plan sheet); without --zone-length no record is given and V2.13 must equal V2.12 on the zone."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

PID = "development-villa-t120"


def _key(ln):
    loc = ln["location"]
    return "|".join(str(x) for x in (ln["item_code"], loc.get("floor"), loc.get("room_id"), loc.get("element_id"),
                                     ln["unit"]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    ap.add_argument("--zone-floor", default="GF")
    ap.add_argument("--zone-code", default="PANTRY")
    ap.add_argument("--zone-length", type=float)
    ap.add_argument("--zone-width", type=float)
    ap.add_argument("--zone-sheet", default="ground floor plan")
    a = ap.parse_args(argv)
    from engine.source import arch_measure as AM
    from engine.source import arch_v213 as AV
    from tools import urban_boq_m9 as M
    facts = {"schema": AM.FACTS_SCHEMA,
             "sanitary_by_room": json.loads((ROOT / "research/agents_t010/sanitary_reading.json").read_text(
                 encoding="utf-8"))["items"],
             "exterior_spaces": json.loads((ROOT / "research/agents_t071/alsenan_facts.json").read_text(
                 encoding="utf-8"))}
    f13 = dict(facts)
    if a.zone_length is not None:
        f13["project_data"] = {"schema": "URBAN_PROJECT_DATA_FILE_V1", "project": PID, "records": [{
            "key": f"WET_ZONE_SIZE_{a.zone_floor}_{a.zone_code}", "project": PID, "kind": "table", "unit": "none",
            "value": {"length_m": a.zone_length, "width_m": a.zone_width}, "status": "DRAWING-VERIFIED",
            "drawing_file": Path(a.drawing).name, "drawing_number": "architectural set",
            "revision": "no revision printed", "sheet": a.zone_sheet,
            "reference": f"printed {a.zone_length:.2f} x {a.zone_width:.2f} m at the {a.zone_code} label",
            "applies_to": {"floors": [a.zone_floor], "members": [a.zone_code]},
            "reviewer_or_source": "verifier hand reading (T-114 read the same printed size)", "entered_by": "TYPED"}]}
    b12, a12, _ = M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.12", facts=facts, project_id=PID)
    b13, a13, _ = M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.13", facts=f13, project_id=PID)
    q = {}
    for tag, b in (("12", b12), ("13", b13)):
        q[tag] = {_key(x): (x["measured_net"], x["evidence_state"], (x.get("bounded_range") or {}).get("low"),
                            (x.get("bounded_range") or {}).get("high")) for x in b["lines"]}
    rows = AV.purchase_rows(a13["v211"]["membrane_table"])
    proofs = {f"{s}|{r['floor']}|{r['room_id']}": {k: (r["purchase"] or {}).get(k) for k in (
        "state", "rolls", "rolls_by_reading", "proof_q58_a", "layouts_tried_q58_a", "reason")}
        for s, st in a13["v211"]["membrane_table"]["systems"].items() for r in st["rows"]
        if (r.get("purchase") or {}).get("state") != "RELEASED"}
    out = {"purchase": rows, "q58_areas": proofs, "typed_wet_zones": a13["v211"]["typed_wet_zones"],
           "zones_held_v2_12": a12["v211"]["wet_zones_held"],
           "changed_from_v2_12": {k: [q["12"][k], q["13"][k]] for k in sorted(set(q["12"]) & set(q["13"]))
                                  if q["12"][k] != q["13"][k]},
           "only_v2_12": sorted(set(q["12"]) - set(q["13"])),
           "only_v2_13": {k: q["13"][k] for k in sorted(set(q["13"]) - set(q["12"]))},
           "lines": {"v2_12": len(b12["lines"]), "v2_13": len(b13["lines"])},
           "release_report": a13["run"]["v2_13"]["release_report"]}
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    for r in rows:
        print({k: r.get(k) for k in ("system", "floor", "room_id", "state", "floor_m2", "layout", "rolls",
                                     "rolls_q58_a", "rolls_q58_b", "rolls_q58_c", "strip_length_m", "leftover_m")})
    for k, v in proofs.items():
        pr = v.get("proof_q58_a") or {}
        print(k, v["state"], v["rolls"], {x: y["rolls"] for x, y in (v["rolls_by_reading"] or {}).items()},
              "proven" if pr.get("proven") else v.get("layouts_tried_q58_a"))
    print("zones:", out["typed_wet_zones"])
    print(len(out["changed_from_v2_12"]), "V2.12 lines changed:", out["changed_from_v2_12"])
    print(len(out["only_v2_12"]), "only in V2.12;", len(out["only_v2_13"]), "only in V2.13:", out["only_v2_13"])
    print(out["lines"], out["release_report"])


if __name__ == "__main__":
    main()
