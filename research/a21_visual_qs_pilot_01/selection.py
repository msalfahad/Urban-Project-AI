"""Mechanical pilot-case selection. Declared as code, hashed, then applied.

The rule below uses ROOM IDENTITY and DETERMINISTIC BOUNDARY EVIDENCE only.
It never reads a room area, a quantity, a benchmark or any prior answer, and
it never prefers a case because the deterministic engine handles it well -
that would be selecting on the answer by a slower route.

    python3 -m research.a21_visual_qs_pilot_01.selection
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from research.a21_visual_qs_pilot_01 import protocol as P

E14 = Path("data/runs/7757/e1_4")
OUT = Path("data/experiments/A21_VISUAL_QS_PILOT_01")

# Treatment class from the room's drawn name, against the directive's own
# vocabulary in section 8. Names only - never areas.
TILE_PREP_NAMES = ("KITCHEN", "PANTRY", "WASH", "W.C", "BATH", "SHOWER",
                   "LAUNDRY", "IRONING")
NOT_A_ROOM_NAMES = ("SWIMMING POOL", "COURT", "GARDEN")

WINDOW_LAYER = "W"

SELECTION_RULE = (
    "classify every ground-floor label seed by its DRAWN NAME into "
    "TILE_PREP, NOT_A_ROOM or NORMAL_PLASTER. Then fill each required case "
    "type in the declared order, excluding rooms already chosen, breaking "
    "every tie by lowest CANDIDATE_ID ascending. No area, quantity, "
    "benchmark or prior answer is read at any point")

WHY_THESE_INPUTS_ARE_NOT_A_LEAK = (
    "room NAME and boundary EVIDENCE are not quantities. Using 'this room "
    "is called KITCHEN' to route it to tile prep is applying the owner's "
    "own rule. Using 'the engine measured it at 12.4 m2' would be "
    "selecting on the answer. Only the first kind is read here")


def _klass(name: str) -> str:
    n = (name or "").upper().strip()
    if any(t in n for t in NOT_A_ROOM_NAMES):
        return "NOT_A_ROOM"
    if any(t in n for t in TILE_PREP_NAMES):
        return "TILE_PREP"
    return "NORMAL_PLASTER"


def rule_hash() -> str:
    parts = [SELECTION_RULE, WHY_THESE_INPUTS_ARE_NOT_A_LEAK, WINDOW_LAYER]
    parts += list(TILE_PREP_NAMES) + list(NOT_A_ROOM_NAMES)
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def main() -> int:
    ch = json.loads(
        (E14 / "E1_4_PHYSICAL_BOUNDARY_CHAIN_REGISTER.json").read_text())
    rooms = []
    for c in ch["CANDIDATES"]:
        els = (c.get("CHAIN") or {}).get("CHAIN") or []
        rooms.append({
            "CANDIDATE_ID": c["CANDIDATE_ID"],
            "IDENTITY_AS_DRAWN": c.get("IDENTITY_AS_DRAWN"),
            "TREATMENT_CLASS": _klass(c.get("IDENTITY_AS_DRAWN")),
            "confirmed_door_portals": sum(
                1 for e in els if e["CHAIN_ELEMENT"] == "DOOR_PORTAL"),
            "window_layer_members": sum(
                1 for e in els if str(e.get("layer")) == WINDOW_LAYER),
            "PHYSICAL_REGION_KEY": c.get("PHYSICAL_REGION_KEY"),
        })
    rooms.sort(key=lambda r: r["CANDIDATE_ID"])
    taken, cases = set(), []

    def pick(case_id, need, why):
        for r in rooms:
            if r["CANDIDATE_ID"] in taken:
                continue
            if need(r):
                taken.add(r["CANDIDATE_ID"])
                cases.append({"CASE_ID": case_id, "WHAT_IT_TESTS": why,
                              "SELECTED_BY": "MECHANICAL_RULE", **r})
                return r
        cases.append({"CASE_ID": case_id, "WHAT_IT_TESTS": why,
                      "SELECTED_BY": None,
                      "STATUS": "NO_CANDIDATE_MEETS_THE_RULE"})
        return None

    # 1 - a plain normal-plaster room: fewest openings, so the baseline
    #     gross-wall calculation is tested without deduction noise
    plain = [r for r in rooms if r["TREATMENT_CLASS"] == "NORMAL_PLASTER"]
    fewest = min((r["confirmed_door_portals"] for r in plain), default=0)
    pick("CASE-1-NORMAL-PLASTER",
         lambda r: (r["TREATMENT_CLASS"] == "NORMAL_PLASTER"
                    and r["confirmed_door_portals"] == fewest),
         "normal internal plaster, baseline gross wall face")

    # 2 - a ceramic / tile-prep room
    pick("CASE-2-TILE-PREP",
         lambda r: r["TREATMENT_CLASS"] == "TILE_PREP",
         "tartusha / tile preparation, must NOT enter normal plaster")

    # 3 - a room carrying BOTH a confirmed door portal and window-layer
    #     geometry, so deductions and reveals are both exercised
    pick("CASE-3-DOOR-AND-WINDOW",
         lambda r: (r["TREATMENT_CLASS"] == "NORMAL_PLASTER"
                    and r["confirmed_door_portals"] >= 1
                    and r["window_layer_members"] >= 1),
         "door and window deductions, reveals and steel profiles")

    write = {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "SELECTION_RULE": SELECTION_RULE,
        "SELECTION_RULE_HASH": rule_hash(),
        "why_these_inputs_are_not_a_leak": WHY_THESE_INPUTS_ARE_NOT_A_LEAK,
        "THE_RULE_WAS_HASHED_BEFORE_IT_WAS_APPLIED": True,
        "TREATMENT_CLASS_COUNTS": dict(
            Counter(r["TREATMENT_CLASS"] for r in rooms)),
        "ROOM_CASES": cases,
        "NON_ROOM_CASES": [
            {"CASE_ID": "CASE-4-STAIR",
             "WHAT_IT_TESTS": "stair wall plaster and stair underside, "
                              "kept separate",
             "SOURCE": "GROUND_FLOOR_PLAN p1 + SECTION_A-A p8 + "
                       "SECTION_B-B p9",
             "SELECTED_BY": "the only stair rising from the ground floor, "
                            "established by E1.4 stair geometry and visible "
                            "in both sections"},
            {"CASE-5": None, "CASE_ID": "CASE-5-EXTERNAL-FACADE",
             "WHAT_IT_TESTS": "external plaster, one facade, one floor",
             "SOURCE": "SOUTH_EAST_ELEVATION p4",
             "SELECTED_BY": "lowest-numbered elevation sheet in the source "
                            "set - mechanical and blind to content"},
            {"CASE_ID": "CASE-6-ROOF-PARAPET",
             "WHAT_IT_TESTS": "parapet external face, internal roof-side "
                              "face and capping, parameterised",
             "SOURCE": "2nd_FLOOR_ROOF_PLAN p3 + SOUTH_EAST_ELEVATION p4 "
                       "+ SECTION_A-A p8",
             "SELECTED_BY": "the parapet run on the SAME facade as CASE-5, "
                            "so the two share an envelope and can be "
                            "cross-checked"},
        ],
        "ALL_ROOMS_CONSIDERED": rooms,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "PILOT_CASE_SELECTION.json"
    p.write_text(json.dumps(write, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    print(json.dumps({"SELECTION_RULE_HASH": rule_hash(),
                      "TREATMENT_CLASS_COUNTS":
                          write["TREATMENT_CLASS_COUNTS"],
                      "CASES": [{k: c.get(k) for k in
                                 ("CASE_ID", "CANDIDATE_ID",
                                  "IDENTITY_AS_DRAWN",
                                  "confirmed_door_portals",
                                  "window_layer_members")}
                                for c in cases]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
