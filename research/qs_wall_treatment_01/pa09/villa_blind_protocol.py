"""The protocol for the full villa, written before the drawings arrive.

A blind validation is only worth running if the rules are fixed before anybody can see how the answer comes out.  The
owner holds a completed historical BOQ for this villa.  If it is read - even glanced at, even "just for the room
list" - the takeoff stops being evidence about whether the system works and becomes an exercise in reproducing a
number somebody already has.  So the protocol is written first, and the seal is a rule the code can check rather than
an intention somebody remembers.

Two things carry over from Qortuba and one thing must not.  The METHOD carries: how an opening is deducted, which
rooms are wet, what a reveal is, that a measurement is not a price.  The WORKFLOW carries: read everything, take off
what is certain, ask once, recalculate only what depends on the answer.  The PROJECT VALUES do not: Qortuba's 3.00 m
wall, 2.20 m door and 1.500 m window are measurements of one flat, and a villa nobody has measured gets read or asked.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa09_villa_blind"
QORTUBA = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
PHASE_ID = "FULL_VILLA_BLIND_VALIDATION_01"

# What the takeoff may read before it is frozen, and what it may not.  The second list is the whole point.
MAY_READ_BEFORE_FREEZE = [
    "architectural plans, sections and elevations supplied for this villa",
    "structural drawings",
    "MEP drawings",
    "door, window and finishes schedules that are part of the drawing set",
    "written specifications",
    "the approved Urban Projects standards",
    "the owner's answers to questions this takeoff asks",
]
SEALED_UNTIL_FREEZE = [
    "the historical BOQ quantities",
    "the historical contractor measurements",
    "the historical rates",
    "the historical totals",
    "the historical quotation",
    "any summary, screenshot or recollection of the above",
]

# §25: every discrepancy lands in exactly one of these, and the first four are not failures.
DISCREPANCY_CLASSES = {
    "CLOSE_AGREEMENT": "the same item measured two ways, agreeing within the declared tolerance",
    "SCOPE_DIFFERENCE": "the two figures cover different extents of work; neither is wrong about its own scope",
    "COMMERCIAL_RULE_DIFFERENCE": "the same physical thing billed under a different convention - a halving, a "
                                  "bundling, a different height basis",
    "SOURCE_INFORMATION_MISSING": "the drawing set does not carry what the historical BOQ was priced from, so we "
                                  "could not have measured it",
    "OWNER_INPUT_DIFFERENCE": "our figure rests on an owner answer that differs from what was built or assumed",
    "ENGINE_ERROR": "we measured the drawing wrongly.  This is the only class that is a defect in this system",
    "NOT_COMPARABLE": "the historical line has no counterpart in our takeoff, or ours has none in theirs",
}
# Only ENGINE_ERROR counts against the system.  Saying so in advance is what stops it being decided afterwards.
CLASSES_THAT_ARE_DEFECTS = ["ENGINE_ERROR"]

TOLERANCE = {"CLOSE_AGREEMENT_PCT": 2.0,
             "WHY": "declared before the comparison, so a figure cannot be called close because it turned out close"}

COMPARISON_FIELDS = ["TRADE", "ITEM", "OUR_QUANTITY", "OUR_UNIT", "HISTORICAL_QUANTITY", "HISTORICAL_UNIT",
                     "ABSOLUTE_DELTA", "DELTA_PCT", "SCOPE_DIFFERENCE", "MEASUREMENT_BASIS_DIFFERENCE",
                     "ENGINE_ERROR_IF_ANY", "OWNER_INPUT_DEPENDENCY", "CLASS", "STATUS"]

# §"SUCCESS TEST": what is being measured about the SYSTEM, not about the villa.
SUCCESS_METRICS = [
    ("OWNER_QUESTIONS", "count", "how many questions the owner had to answer.  Fewer is better only if the answers "
                                 "were the ones that mattered; a question avoided by a guess is worse than a "
                                 "question asked"),
    ("MANUAL_INTERVENTIONS", "count", "times a human had to do something the workflow could not, other than answer a "
                                      "question"),
    ("MAJOR_QUANTITIES_MISSED", "count", "trades or items the takeoff did not produce at all and should have"),
    ("QUANTITY_DELTAS_BY_TRADE", "table", "our figure against the historical one, per trade, after unsealing"),
    ("ENGINE_CODE_CHANGES", "count", "shared extraction or calculation code changed during the run.  A high count "
                                     "means the system is being fitted to one villa"),
    ("TIME_DRAWINGS_TO_EXCEL", "duration", "from the first drawing read to the final workbook"),
]

# The development rule that decides whether an ambiguity becomes a question or a code change.
AMBIGUITY_POLICY = {
    "DEFAULT": "ASK_THE_OWNER",
    "CHANGE_SHARED_CODE_ONLY_IF": ["the defect is deterministic",
                                   "it repeats within this project or across projects",
                                   "it is likely to affect future projects"],
    "NEVER": ["write a geometry rule for a one-off drawing quirk",
              "build an inference to avoid a ten-second question",
              "widen a rule so one awkward case passes"],
    "WHY": "the goal is not autonomous CAD interpretation at all costs.  It is fast, accurate, traceable, repeatable "
           "and reviewable, and a short question beats a long inference on every one of those except speed of typing",
}

STEPS = [
    "read every supplied drawing and specification",
    "produce the first takeoff of everything already certain",
    "apply the approved Urban standards; read or ask for every project value",
    "return ONE consolidated owner-question batch, in plain language, with marked crops where words are not enough",
    "store the owner's answers as project inputs",
    "recalculate only the quantities that depend on them",
    "produce the trade-based Urban Projects Excel",
    "produce the structured DRAFT quantity records",
    "freeze FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF and record the digest and commit",
    "ONLY THEN unseal the historical BOQ and compare",
]


def carried_from_qortuba():
    """The standards that travel, read from the sealed benchmark rather than retyped."""
    seal = json.loads((QORTUBA / "QORTUBA_BENCHMARK_SEAL.json").read_text("utf-8"))
    return seal["RULES"]


def finish():
    rules = carried_from_qortuba()
    rec = {
        "ARTIFACT": "FULL_VILLA_BLIND_PROTOCOL",
        "PHASE_ID": PHASE_ID,
        "WRITTEN_BEFORE_ANY_DRAWING_WAS_READ": True,
        "PURPOSE": "to find out whether the Urban Projects QS system is practically usable on a whole villa, by "
                   "measuring it blind and only then looking at the BOQ the owner already holds",
        "STEPS": STEPS,
        "MAY_READ_BEFORE_FREEZE": MAY_READ_BEFORE_FREEZE,
        "SEALED_UNTIL_FREEZE": SEALED_UNTIL_FREEZE,
        "WHY_SEALED": "a takeoff that has seen the answer is not evidence about the system.  The seal is what makes "
                      "the comparison mean something, and it costs nothing to keep",
        "DISCREPANCY_CLASSES": DISCREPANCY_CLASSES,
        "CLASSES_THAT_ARE_DEFECTS": CLASSES_THAT_ARE_DEFECTS,
        "TOLERANCE": TOLERANCE,
        "COMPARISON_FIELDS": COMPARISON_FIELDS,
        "THE_FROZEN_FIGURE_IS_NEVER_MOVED": "no blind quantity is altered to improve a comparison.  A delta is "
                                            "understood and classified; it is not closed",
        "SUCCESS_METRICS": [{"METRIC": m, "KIND": k, "WHY": w} for m, k, w in SUCCESS_METRICS],
        "AMBIGUITY_POLICY": AMBIGUITY_POLICY,
        "CARRIES_FROM_QORTUBA": rules["CARRIES_TO_THE_NEXT_PROJECT"],
        "CARRIES_COUNT": rules["CARRIES_COUNT"],
        "DOES_NOT_CARRY_FROM_QORTUBA": rules["DOES_NOT_CARRY"],
        "DOES_NOT_CARRY_COUNT": rules["DOES_NOT_CARRY_COUNT"],
        "PROJECT_VALUES_ARE_READ_OR_ASKED": "wall height, door height, window height, tile height, finishes and room "
                                            "uses are measurements of a building.  Qortuba's are Qortuba's",
        "NO_MANAGER_INTEGRATION_DURING_VALIDATION": True,
        "INPUTS_PRESENT": sorted(p.name for p in OUT.glob("*")) if OUT.exists() else [],
        "STATUS": "AWAITING_DRAWINGS",
        "WHAT_IS_NEEDED_TO_START": "the villa drawing set.  No villa drawing, schedule or specification is present in "
                                   "this repository, so step 1 cannot begin",
    }
    rec["DIGEST"] = hashlib.sha256(
        json.dumps({k: v for k, v in rec.items() if k != "INPUTS_PRESENT"},
                   sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "FULL_VILLA_BLIND_PROTOCOL.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False, default=str),
                                                        "utf-8")
    return rec


if __name__ == "__main__":
    r = finish()
    print(f"{r['PHASE_ID']}  protocol {r['DIGEST']}  status {r['STATUS']}")
    print(f"carries from Qortuba: {r['CARRIES_COUNT']} Urban standards")
    print(f"does NOT carry:       {r['DOES_NOT_CARRY_COUNT']} Qortuba project values")
    print(f"sealed until freeze:  {len(r['SEALED_UNTIL_FREEZE'])} kinds of historical information")
    print(f"inputs present:       {r['INPUTS_PRESENT'] or 'none'}")
