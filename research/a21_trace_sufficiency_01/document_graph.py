"""PATH A - deterministic document cross-reference candidates.

It says only: THIS SHEET MAY BE RELEVANT TO THIS QUESTION. It measures
nothing, reads no result, and never consults E1.4.

What it can genuinely decide, from drawing-set structure alone:
  * floor identity      - a ground-floor question needs the ground floor plan
  * facade direction    - a south-east question needs the south-east elevation
  * roof relationship   - a roof-level question needs the roof-level plan
  * vertical condition  - a height, a stair or a parapet cannot be resolved
                          on a plan at all, so a vertical source is required
  * schedule existence  - whether the set contains a schedule sheet at all

What it CANNOT decide, and says so rather than guessing: WHICH section
cuts a given room. That was tested, not assumed - the CAD decode carries
89 text objects, none of them a sheet title or an A-SEC / B-SEC marker,
and the long-line candidates on the plan are indistinguishable from plot
boundaries and centre lines. So when a height is needed, BOTH sections
are raised, which is the conservative answer and exactly the omission
that produced DEV-02 and DEV-03.

    python3 -m research.a21_trace_sufficiency_01.document_graph
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.a21_trace_sufficiency_01 import protocol as P
from research.a21_trace_sufficiency_01 import source_sufficiency as S

OUT = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")

SECTION_SHEETS = ("SECTION_A_A", "SECTION_B_B")
ELEVATION_BY_DIRECTION = {
    "south-east": "SOUTH_EAST_ELEVATION", "south east": "SOUTH_EAST_ELEVATION",
    "south-west": "SOUTH_WEST_ELEVATION", "south west": "SOUTH_WEST_ELEVATION",
    "north-west": "NORTH_WEST_ELEVATION", "north west": "NORTH_WEST_ELEVATION",
    "north-east": "NORTH_EAST_ELEVATION", "north east": "NORTH_EAST_ELEVATION",
}
PLAN_BY_FLOOR = {
    "ground floor": "GROUND_FLOOR_PLAN",
    "first floor": "FIRST_FLOOR_PLAN",
    "roof": "SECOND_FLOOR_ROOF_PLAN",
}
HEIGHT_WORDS = ("area", "face", "plaster", "underside", "capping",
                "parapet", "wall surfaces", "deduction", "reveal")
VERTICAL_WORDS = ("stair", "parapet", "underside", "facade", "capping")
OPENING_WORDS = ("door", "window", "opening", "glazing", "reveal")

# ------------------------------------------------------------------
# what was TESTED and found not deterministically resolvable
# ------------------------------------------------------------------
SECTION_CUT_LINES_ARE_NOT_RESOLVABLE = {
    "CLAIM": "which section cuts which room cannot be decided from this "
             "drawing set deterministically",
    "HOW_IT_WAS_TESTED": [
        "searched all 89 CAD text objects for SEC / SECTION / ELEVATION / "
        "PLAN / A-A / B-B - zero matches; the decode carries room labels "
        "and level marks only, and sheet titles live in paper space",
        "searched the ground-floor region for a dedicated section-line "
        "layer - there is none; layer 5 carries ordinary building "
        "geometry alongside any candidate",
        "searched for long spanning segments - the candidates are "
        "indistinguishable from plot boundaries and centre lines",
    ],
    "CONSEQUENCE": (
        "when a question needs a height, BOTH sections are raised by this "
        "path as REQUIRED, not one. Omission is the asymmetric risk"),
}

MISSING_FROM_THE_SET = {
    "DOOR_AND_WINDOW_SCHEDULE": (
        "no sheet in the ten-sheet set is a schedule. Opening HEIGHTS "
        "therefore have no source anywhere in the supplied drawings"),
    "FINISHES_SPECIFICATION": (
        "no sheet in the set is a finishes schedule or specification. The "
        "rule that turns a storey height into a treated height has no "
        "source in the supplied drawings"),
}


def analyse(case_id: str, question: str, sheets: dict) -> list:
    q = question.lower()
    found = []

    def add(sheet, status, reason):
        found.append({"SHEET_ID": sheet, "REQUIREMENT_STATUS": status,
                      "REASON": reason})

    for key, sheet in PLAN_BY_FLOOR.items():
        if key in q and sheet in sheets:
            add(sheet, "REQUIRED",
                f"floor identity: the question names the {key}, and this "
                f"is that level's plan - it carries the subject's location "
                f"and plan geometry")
            break

    for key, sheet in ELEVATION_BY_DIRECTION.items():
        if key in q and sheet in sheets:
            add(sheet, "REQUIRED",
                f"facade direction: the question names the {key} facade "
                f"and this is the elevation of that direction")
            break

    if any(w in q for w in HEIGHT_WORDS):
        for s in SECTION_SHEETS:
            add(s, "REQUIRED",
                "a height is needed and a height cannot be established on "
                "a plan. Which of the two sections carries it cannot be "
                "decided from the drawing set (see "
                "SECTION_CUT_LINES_ARE_NOT_RESOLVABLE), so both are raised "
                "rather than guessing one and repeating DEV-02 / DEV-03")

    if "stair" in q and "FIRST_FLOOR_PLAN" in sheets:
        add("FIRST_FLOOR_PLAN", "POSSIBLY_RELEVANT",
            "a stair rising from this floor arrives at the floor above, so "
            "the plan above may carry its upper geometry. Not required: "
            "the question is about the flight from the ground floor")

    if "roof parapet" in q and "SECOND_FLOOR_ROOF_PLAN" in sheets:
        add("SECOND_FLOOR_ROOF_PLAN", "REQUIRED",
            "roof relationship: the parapet runs along the roof edge and "
            "only the roof-level plan gives that run in plan")

    schedules = []
    if any(w in q for w in OPENING_WORDS):
        schedules.append("DOOR_AND_WINDOW_SCHEDULE")
    if any(w in q for w in HEIGHT_WORDS):
        schedules.append("FINISHES_SPECIFICATION")

    # de-duplicate, keeping the strongest status per sheet
    rank = {"REQUIRED": 0, "OPTIONAL_CONTEXT": 1, "POSSIBLY_RELEVANT": 2}
    best = {}
    for f in found:
        k = f["SHEET_ID"]
        if k not in best or rank[f["REQUIREMENT_STATUS"]] < rank[
                best[k]["REQUIREMENT_STATUS"]]:
            best[k] = f
    return sorted(best.values(), key=lambda f: f["SHEET_ID"]), schedules


def build() -> dict:
    idx = json.loads((OUT / "SHEET_INDEX.json").read_text("utf-8"))
    sheets = idx["SHEETS"]
    cases = []
    for cid, q in sorted(S.QUESTIONS.items()):
        rels, scheds = analyse(cid, q, sheets)
        cases.append({
            "CASE_ID": cid, "QUESTION": q,
            "SHEET_RELATIONSHIPS": rels,
            "REQUIRED_SCHEDULES": scheds,
            "SCHEDULES_PRESENT_IN_THE_SET": [],
            "MISSING_SOURCE": [s for s in scheds if s in MISSING_FROM_THE_SET],
        })
    body = {
        "PHASE_ID": P.PHASE_ID,
        "ARTIFACT": "DOCUMENT_GRAPH_CANDIDATES",
        "PATH": "DOCUMENT_GRAPH",
        "IT_ONLY_SAYS": "THIS SHEET MAY BE RELEVANT TO THIS QUESTION",
        "IT_MEASURES_NOTHING": True,
        "E1_4_WAS_NOT_CONSULTED": True,
        "SIGNALS_USED": [
            "sheet identity and drawing-set structure",
            "floor identity", "facade direction", "roof relationship",
            "vertical-condition requirement", "schedule existence",
        ],
        "SECTION_CUT_LINES_ARE_NOT_RESOLVABLE":
            SECTION_CUT_LINES_ARE_NOT_RESOLVABLE,
        "MISSING_FROM_THE_SET": MISSING_FROM_THE_SET,
        "NOT_THE_WHOLE_SET": (
            "no case raises all ten sheets. The three elevations whose "
            "direction does not match, and the fence sheet, are raised by "
            "nothing and are not mounted anywhere"),
        "CASES": cases,
    }
    p = OUT / "DOCUMENT_GRAPH_CANDIDATES.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return {"SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "PER_CASE": {c["CASE_ID"]: [
                f"{r['SHEET_ID']}:{r['REQUIREMENT_STATUS']}"
                for r in c["SHEET_RELATIONSHIPS"]] for c in cases},
            "MISSING": {c["CASE_ID"]: c["MISSING_SOURCE"] for c in cases}}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
