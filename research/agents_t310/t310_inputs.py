"""T-310: the URBAN_V3049_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.49 (engine.source.arch_v3049), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build). The door / line keys, the pool figures
and their held parts are READ from those files; typed here are only the entry selection, the action per entry, the
1F east bath re-measure the Checker printed in the T-303 verdict (its words, below) and the two duplicate transition
lines, whose door the Checker named by closure id (bound below by the candidate's own element id, asserted).

  research/agents_t303/WP_WET_ROOF_POOL_INVENTORY_T303.csv   T-303 (MERGED 1d3f69b0, Verifier 2026-10-26 01:06 UTC,
      Gate A PASS; own re-measures: 1F east bath floor 2.250 x 2.100, boundary 8.700 lm, door 0.800, the 0.500 east
      opening a WINDOW (layer-W glazing, no leaf) with the NW-elevation sill 0.84 (T-144 W18): walls-only 7.900 lm x
      0.20 = 1.580 m2, ENGINE_WRONG -0.100; the 3 termination lines on that window have no membrane edge; transitions:
      2 doors twice (closures D2:495, D2:825), 3 doors none (OP-017, OP-018, OP-010); pantry box 13.500 gross,
      O-T303-01: the 0.045 m2 column of T-286 to be ruled before any WHOLE claim);
  research/agents_t309/POOL_MEMBRANE_LINES_T309.json        T-309 (MERGED 834ada3e, Verifier 2026-10-26 05:05 UTC,
      Gate A PASS; own re-read of the pool detail by handle: layer order and faces AGREE);
  research/agents_t286/summary_t286.json                    T-286 (MERGED e861e390, Verifier 2026-10-25 09:51 UTC,
      Gate A PASS): pantry box 13.500, column 2FAE notch 0.045 m2 (0.900 x 0.050).

PANTRY COLUMN RULING (O-T303-01, this task, own re-read of P7757.dxf by handle, ERS s.2): the S-COL.BON outline 2FAE
(1.100 x 0.250, closed) overlaps the printed box (faces AE / B3 / A6 / 158, DIMENSIONs 5D5 3000.0 and 5E1 4500.0) by
0.900 x 0.050 = 0.045000 m2 at its north-west corner: the column stands 50 mm proud of the drawn 200 mm wall face 158
over 0.900 m. A column is not floor: the membrane is laid on the slab face and turns up the column face, it does not
run under the column. Every other wet room's floor line follows the drawn outline round its column corners (the
Checker's own example in O-T303-01: the dewaneya wash steps round a 0.0175 m2 corner), so the pantry line takes the
same rule: 13.500 - 0.045 = 13.455 m2 (DRAWING-CONFIRMED). Residual risk, named: the architectural wall line 158 does
not draw the 50 mm step; if the designer sets the column flush with the wall face the floor is the whole 13.500.

    python3 -I research/agents_t310/t310_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INV = ROOT / "research/agents_t303/WP_WET_ROOF_POOL_INVENTORY_T303.csv"
POOL = ROOT / "research/agents_t309/POOL_MEMBRANE_LINES_T309.json"
S286 = ROOT / "research/agents_t286/summary_t286.json"
PINS = {INV: "9d8ceb614dbc901cf7620820a37e4aa37ef784b5f4d9dde48fb06d261149083e",
        POOL: "48e07a7c34c3858d853b51fa47782faafdc38239a462d7bae1d766d6f81bfcfd",
        S286: "989167e1f3950ebae4665299eb78000160059fda8ae6da40708a8ac50dc8abf9"}
SOURCES = {
    "T-303": {"task": "T-303", "file": "research/agents_t303/WP_WET_ROOF_POOL_INVENTORY_T303.csv", "sha256": PINS[INV],
              "merge_commit": "1d3f69b0",
              "checker_run": "Verifier 2026-10-26 01:06 UTC (Gate A PASS; own re-measures: 1F east bath 8.700 - 0.800 "
                             "= 7.900 lm x 0.20 = 1.580 m2, W18 sill 0.84; transitions 2 doors twice / 3 none; pool "
                             "layers printed MISSING; O-T303-01 pantry column)"},
    "T-309": {"task": "T-309", "file": "research/agents_t309/POOL_MEMBRANE_LINES_T309.json", "sha256": PINS[POOL],
              "merge_commit": "834ada3e",
              "checker_run": "Verifier 2026-10-26 05:05 UTC (Gate A PASS; own re-read of the pool detail by handle: "
                             "HATCH 1851 outer, 184E between it and the concrete, base + both outer faces to the wall "
                             "top, nothing on the water side)"},
    "T-286": {"task": "T-286", "file": "research/agents_t286/summary_t286.json", "sha256": PINS[S286],
              "merge_commit": "e861e390",
              "checker_run": "Verifier 2026-10-25 09:51 UTC (Gate A PASS; pantry box closure 13.500 - 0.045 column)"},
}
# the 1F east bath (T-074 room 1F-12): the Checker's own re-measure in the T-303 verdict (e)(1), his words
EAST_BATH = {"room": "1F-12", "line": "L-60f100105399a9bdfb08", "before": 1.48, "boundary_lm": 8.700,
             "door_widths_m": [0.800], "window": {"kind": "WINDOW", "id": "W18", "sill_m": 0.84},
             "terminations": ("L-0a7238edb9989d99d37a", "L-1ef59757a75524c397d7", "L-8fb80f626889e06f6f97")}
PANTRY_LINE, PANTRY_BEFORE = "L-f32abcdb3b4db6877c64", 13.5
# duplicate transition lines (0 inventory elements in T-303) -> the door the Checker named by closure; the binding
# is asserted against the candidate line's own element id in research/agents_t310/v3049_run.py (closure in the id)
DUPLICATES = {"L-b60811f60f8fdc9a4447": ("D-GF-02", "D2:495"), "L-e0c34550b13267b4e0f7": ("D-GF-10", "D2:825")}
# Checker's candidate opening ids (per floor) and the candidate's doorway line of each (bound in v3049_run.py)
MISSING_DOORS = {"D-GF-11": ("GF", "OP-017", "L-e3ffb8005f85e89113cb"), "D-GF-12": ("GF", "OP-018", "L-9cbc8b1b9ebf6e79df66"),
                 "D-1F-06": ("1F", "OP-010", "L-bdf48c327992229649ca")}
TEMPLATE_TRANSITION = "L-aed6f48195f99648c3f3"
POOL_TEMPLATE_CODE = "WP.FOUNDATION.FOOTING_MEMBRANE"   # a membrane line whose documents / trade the pool lines share
POOL_CODE = {"WP.POOL_TANK.POOL_MEMBRANE": "WP.POOL.MEMBRANE",
             "WP.POOL_TANK.POOL_PROTECTION_SCREED": "WP.POOL.PROTECTION_SCREED"}
POOL_BASIS = {"WP.POOL.MEMBRANE": "base underside 10.935564 + outer back 5.600000 + outer sides 5.075000 + outer arc "
                                  "7.971791 m2 (T-309 face ledger, closure residual 0.000000)",
              "WP.POOL.PROTECTION_SCREED": "0.05 m on the same faces: base sheet 0.578469 + back 0.288000 + sides "
                                           "0.253750 + arc 0.404284 m3 (T-309 face ledger)"}
POOL_FACES = [{"face": "BASE_UNDERSIDE"}, {"face": "OUTER_BACK"}, {"face": "OUTER_SIDES"}, {"face": "OUTER_ARC"}]


def _bytes(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.name}: sha256 differs from the merged file (edited input)")
    return b


def inventory():
    return list(csv.DictReader(io.StringIO(_bytes(INV).decode("utf-8"))))


def build(project_id):
    """-> the URBAN_V3049_INPUTS_V1 doc (the pool lines share documents / trade with the first candidate line of
    POOL_TEMPLATE_CODE, picked by the engine)."""
    inv = inventory()
    trans = {r["element"].split(":", 1)[1]: r for r in inv if r["item_code"] == "FIN.WP.DOORWAY_TRANSITION"}
    pool = json.loads(_bytes(POOL).decode("utf-8"))
    s286 = json.loads(_bytes(S286).decode("utf-8"))
    up = next(r for r in inv if r["line_id"] == EAST_BATH["line"])
    if abs(float(up["qty"]) - 1.58) > 1e-9 or up["element"] != EAST_BATH["room"]:
        raise SystemExit("T-303 inventory: the 1F east bath upturn row is not 1.58 m2 on 1F-12")
    fl = next(r for r in inv if r["line_id"] == PANTRY_LINE)
    if abs(float(fl["qty"]) - PANTRY_BEFORE) > 1e-9:
        raise SystemExit("T-303 inventory: the pantry floor row is not 13.500 m2")
    notch = s286["pantry"]["box"]["column_2FAE_notch_m2"]
    box = s286["pantry"]["closure"]["box_m2"]
    ents = [{"action": "REVALUE_UPTURN", "line_id": EAST_BATH["line"], "before": EAST_BATH["before"],
             "boundary_lm": EAST_BATH["boundary_lm"], "door_widths_m": EAST_BATH["door_widths_m"],
             "openings_not_deducted": [EAST_BATH["window"]], "value": float(up["qty"]),
             "evidence_status": "DRAWING-CONFIRMED", "source_tasks": ["T-303"],
             "basis": "1F east bath (1F-12) walls-only upturn (Q-35 C): boundary 8.700 lm incl. the 0.800 door "
                      "crossing; the 0.500 east opening is window W18 with its sill 0.84 above the 0.20 upturn "
                      "(Checker own re-measure, T-303 verdict (e)(1)): ENGINE_WRONG -0.100 m2 (-6.3 %)"}]
    for lid in EAST_BATH["terminations"]:
        ents.append({"action": "NOT_APPLICABLE", "line_id": lid, "item_code": "FIN.WP.TERMINATION",
                     "source_tasks": ["T-303"], "basis": "T-303 verdict (e)(1)",
                     "evidence": "membrane termination on window W18 of the 1F east bath: the sill stands 0.84 m "
                                 "above the floor, the 0.20 m upturn runs on under it: no membrane edge exists "
                                 "(Checker own read: layer-W glazing, no leaf or arc, NW elevation 839.27 / 2160.73)"})
    ents.append({"action": "REVALUE_FLOOR", "line_id": PANTRY_LINE, "before": PANTRY_BEFORE, "gross_m2": box,
                 "deductions": [{"what": "column 2FAE intrusion 0.900 x 0.050", "m2": notch,
                                 "evidence": "S-COL.BON outline inside the printed box, own re-read this run"}],
                 "value": round(box - notch, 6), "evidence_status": "DRAWING-CONFIRMED",
                 "source_tasks": ["T-286", "T-303"],
                 "residual_risk": "the architectural wall line does not draw the 50 mm column step; a column set "
                                  "flush by the designer gives the whole 13.500 m2 (+0.045)",
                 "basis": "pantry (Q-37 A) membrane on the floor face: printed box 4.500 x 3.000 less the column "
                          "standing 50 mm proud of the wall over 0.900 m, as every other wet room follows its drawn "
                          "outline round a column (O-T303-01 ruled from the drawing)"})
    for door in sorted(trans):
        r = trans[door]
        if r["status"] == "IN_LINE":
            ents.append({"action": "KEY_DOOR", "line_id": r["line_id"], "door_id": door, "source_tasks": ["T-303"],
                         "basis": f"T-303 inventory: door {door} ({r['owner']}) carried by this line"})
    for lid, (door, closure) in sorted(DUPLICATES.items()):
        car = trans[door]
        if car["status"] != "IN_LINE":
            raise SystemExit(f"T-303 inventory: door {door} has no carrying line")
        ents.append({"action": "NOT_APPLICABLE", "line_id": lid, "item_code": "FIN.WP.DOORWAY_TRANSITION",
                     "door_id": door, "carried_by": car["line_id"], "closure": closure, "source_tasks": ["T-303"],
                     "basis": "T-303 verdict (e)(2): the same door booked from both room sides",
                     "evidence": f"second transition line of door {door} (closure {closure}, booked from the other "
                                 f"room side); 0 inventory elements"})
    for door, (floor, cand, doorway) in sorted(MISSING_DOORS.items()):
        r = trans[door]
        if r["status"] != "MISSING" or r["floor"] != floor:
            raise SystemExit(f"T-303 inventory: door {door} is not MISSING on {floor}")
        ents.append({"action": "ADD_HELD_DOOR", "door_id": door, "rooms": r["owner"].split("|"), "floor": r["floor"],
                     "candidate_opening": cand, "template_line": TEMPLATE_TRANSITION, "doorway_line": doorway,
                     "source_tasks": ["T-303"],
                     "basis": f"T-303 inventory: door {door} (candidate opening {cand}) has a doorway line and no "
                              f"transition (Checker own count)",
                     "held_items": "transition detail not printed (T-303); width x depth as the sibling doorway "
                                   "line once the detail is known"})
    for p in pool:
        code = POOL_CODE[p["key"].split("[")[0]]
        lo, hi = p["held_part_bound"]
        ents.append({"action": "ADD_POOL_LAYER", "item_code": code, "unit": p["unit"],
                     "element_id": "WP-T310:POOL-1:" + code.split(".")[-1], "floor": "GF", "value": p["quantity"],
                     "evidence_status": p["status"], "template_code": POOL_TEMPLATE_CODE, "faces": POOL_FACES,
                     "held_part": {"what": "upstand faces +0.15 .. +0.30 on the deck edges (8.997787 x 0.15)",
                                   "low": lo, "high": hi,
                                   "cause": "C9: the pool detail draws the layer to the wall top, the architectural "
                                            "cut leaves the upstand exposed above the +0.15 deck (UNRESOLVED)"},
                     "function_held": ("function HELD (waterproofing or thermal insulation not stated, S8.2); "
                                       "product and laps not printed") if code == "WP.POOL.MEMBRANE" else None,
                     "source_tasks": ["T-309"], "basis": POOL_BASIS[code]})
    # T-310 r2: the default guard re-check at integration (T-212 P2), the V3.0.7 guard inputs unchanged (as V3.0.8 ..
    # V3.0.12, t146 / t211 / t231), no new printed record
    sys.path.insert(0, str(ROOT / "research" / "agents_t193"))
    import t193_inputs as L7   # noqa: E402
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V3049_INPUTS_V1", "project_id": project_id, "sources": list(SOURCES.values()),
            "entries": ents, "guard": g}


if __name__ == "__main__":
    d = build(sys.argv[1] if len(sys.argv) > 1 else None)
    from collections import Counter
    print(json.dumps({"entries": len(d["entries"]), "by_action": Counter(e["action"] for e in d["entries"])},
                     indent=1))
