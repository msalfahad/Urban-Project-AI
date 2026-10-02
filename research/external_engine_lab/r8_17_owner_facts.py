"""R8.17 lab: record the owner's HALL / PAINTRY sliding glass door as a source-bound PHYSICAL fact, and the normal
window sill fact v2 (same owner statement, trade scope widened to wall-face surfaces). Run once; the committed files
are then only verified.

    python3 research/external_engine_lab/r8_17_owner_facts.py <work>

Physical fact (data/registry/OWNER_PHYSICAL_FACTS.json):
  QORTUBA-NEW-HALL-PAINTRY-SLIDING-GLASS-DOOR-OWNER-001  OPENING_CONSTRUCTION (glazing lines H533 / H542)
Method fact (data/registry/OWNER_METHOD_FACTS.json):
  QORTUBA-NEW-NORMAL-WINDOWS-ABOVE-FLOOR-OWNER-001@v2    WINDOW_FLOOR_CONTACT, trades SKIRTING + WALL_FACE
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_13_qortuba as R13                                                                   # noqa: E402
import r8_15_owner_facts as F15                                                               # noqa: E402
from engine.source import opening_facts as OPF                                                # noqa: E402

FACTS = ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json"
METHOD = ROOT / "data/registry/OWNER_METHOD_FACTS.json"
SLIDE = "QORTUBA-NEW-HALL-PAINTRY-SLIDING-GLASS-DOOR-OWNER-001"
WIN = "QORTUBA-NEW-NORMAL-WINDOWS-ABOVE-FLOOR-OWNER-001"
SLIDE_PARTS = {"QORTUBA_REV_NEW|H533||SEGMENT|0": "SLIDING_GLASS_DOOR_GLAZING (PAINTRY-side track)",
               "QORTUBA_REV_NEW|H542||SEGMENT|0": "SLIDING_GLASS_DOOR_GLAZING (HALL-side track, on the HALL face)"}


def sliding_door(inp) -> dict:
    by_key = {p.identity.key: p for p in inp.parts}
    return {
        "fact_id": SLIDE, "version": 1, "kind": OPF.KIND, "authority": ["PROJECT_OWNER"],
        "received": "R8.17 brief §1-§2 (owner reviewed the exact highlighted source-plan location)",
        "scope": F15.scope(inp), "allowed_domains": list(OPF.ALLOWED_DOMAINS),
        "parts": [F15._part(by_key[k], r) for k, r in SLIDE_PARTS.items()],
        "statement": {
            "text": "the ~2.75 m internal glazed opening between HALL and PAINTRY is A SLIDING GLASS DOOR that reaches "
                    "the FINISHED FLOOR",
            "physical_class": "SLIDING_GLAZED_DOOR", "floor_contact": "OPENING_TO_FLOOR", "wall_below": "NONE",
            "skirting_across_opening": "NONE", "hidden_profile_across_opening": "NONE (US-08: same path)",
            "jambs": "door jambs: ZERO skirting (URBAN-SKIRTING-OPENING-METHOD@v1 DOOR_PRESENT)",
            "occurrence": {"rooms": ["HALL", "PAINTRY"], "approx_width_m": 2.75,
                           "width_meaning": "identification only - the deterministic width is the source geometry",
                           "closures": ["CLOSURE|GLAZED|QORTUBA_REV_NEW|H533||SEGMENT|0|F1",
                                        "CLOSURE|GLAZED|QORTUBA_REV_NEW|H533||SEGMENT|0|F2",
                                        "CLOSURE|GLAZED|QORTUBA_REV_NEW|H542||SEGMENT|0|F1",
                                        "CLOSURE|GLAZED|QORTUBA_REV_NEW|H542||SEGMENT|0|F2"]},
            "resolves": "R8.16 FLOOR_CONTACT_UNPROVEN (withheld 2.75 lm) for THIS occurrence only",
            "window_fact": f"{WIN} does NOT apply (not a normal window)",
            "height": "NOT stated by this fact (wall-face opening height: QP-12, recorded separately)"},
        "transfer_forbidden": F15.TRANSFER + ["any other glazed opening ('all glazed openings are sliding doors')"],
        "never": ["a normal window", "SKIRTING_CONTINUITY_UNDER_WINDOW", "a low wall under the glass",
                  "a doorless opening", "a topology edit", "a quantity"]}


def window_v2(v1: dict) -> dict:
    f = copy.deepcopy(v1)
    f["version"] = 2
    f["received"] = v1["received"] + "; v2 (R8.17): the SAME owner statement, trade scope widened"
    f["scope"] = {k: v for k, v in v1["scope"].items() if k not in ("trade", "space_classes")}
    f["scope"]["trades"] = ["SKIRTING", "WALL_FACE_SURFACE"]
    f["scope"]["space_classes"] = ["DRY_INTERNAL_ROOM", "WET_SERVICE_ROOM", "SERVICE_ROOM"]
    f["statement"] = dict(v1["statement"], wall_face_use="POSITION ONLY: proves that a normal window lies within a "
                          "stated wall-finish height (sill + window height); never a quantity, never a sill "
                          "dimension in an area")
    f["relations"] = [{"rule": f"{WIN}@v1", "relation": "CORROBORATING",
                       "why": "same meaning and value (sill ~1.00 m); v2 only names the wall-face trades the owner "
                              "statement already covers - v1 stays on file for the frozen R8.16 records"}]
    return f


def main(work):
    inps, _, _ = R13.Q10.inputs(work)
    inp = inps["NEW_K2"]
    raw = json.loads(FACTS.read_text())
    raw["facts"] = [f for f in raw["facts"] if f["fact_id"] != SLIDE] + [sliding_door(inp)]
    raw["SCHEMA"] = "URBAN_OWNER_PHYSICAL_FACTS_V3"
    FACTS.write_text(json.dumps(raw, indent=1, ensure_ascii=False) + "\n")
    m = json.loads(METHOD.read_text())
    v1 = next(f for f in m["facts"] if f["fact_id"] == WIN and f["version"] == 1)
    m["facts"] = [f for f in m["facts"] if not (f["fact_id"] == WIN and f["version"] == 2)] + [window_v2(v1)]
    METHOD.write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n")
    print(len(raw["facts"]), "physical facts;", len(m["facts"]), "method facts")


if __name__ == "__main__":
    main(sys.argv[1])
