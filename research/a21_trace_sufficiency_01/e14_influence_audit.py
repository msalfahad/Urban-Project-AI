"""Did E1.4 influence the frozen subset? Audited honestly, not asserted.

The answer is YES for three of the five rule clauses. This module says
exactly where, and then tests whether it CHANGED anything by re-deriving
the subset from the declared case subjects alone - text written from the
owner's own case directive, which predates E1.4 being consulted for
anything here.

The subset is NOT changed and NOT refrozen. This is a disclosure.

    python3 -m research.a21_trace_sufficiency_01.e14_influence_audit
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from research.a21_trace_sufficiency_01 import protocol as P
from research.a21_trace_sufficiency_01 import subset as SUB

OUT = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")
SUBSET_SRC = Path("research/a21_trace_sufficiency_01/subset.py")
PILOT = Path("data/experiments/A21_VISUAL_QS_PILOT_01/"
             "PILOT_CASE_SELECTION.json")

# ------------------------------------------------------------------
# clause by clause: what each one read
# ------------------------------------------------------------------
CLAUSE_AUDIT = {
    "ORDINARY_WALL_WITH_PRINTED_DIMENSION": {
        "READ_E1_4": True,
        "EXACTLY_WHAT": (
            "E1_4_PHYSICAL_BOUNDARY_CHAIN_REGISTER.json -> per candidate "
            "CHAIN element types -> MATERIAL_WALL_FACE and "
            "MATERIAL_CONTINUITY_SPAN as a fraction of chain length"),
        "PICKED": "CASE-1-NORMAL-PLASTER",
    },
    "AN_OPENING": {
        "READ_E1_4": True,
        "EXACTLY_WHAT": (
            "the same register -> DOOR_PORTAL count per candidate, "
            "thresholded at greater than zero"),
        "PICKED": "CASE-3-DOOR-AND-WINDOW",
    },
    "AN_AMBIGUOUS_OR_OPEN_BOUNDARY": {
        "READ_E1_4": True,
        "EXACTLY_WHAT": (
            "the same register -> 1 minus the material fraction. Note "
            "DOOR_PORTAL counts as non-material, which is why an opening "
            "case scored highest on openness"),
        "PICKED": "CASE-3-DOOR-AND-WINDOW",
    },
    "A_STAIR_OR_VERTICAL_CONDITION": {
        "READ_E1_4": False,
        "EXACTLY_WHAT": "the case's declared subject, hard-coded",
        "PICKED": "CASE-4-STAIR",
    },
    "A_PARAPET_BALUSTRADE_DISTINCTION": {
        "READ_E1_4": False,
        "EXACTLY_WHAT": "the case's declared subject, hard-coded",
        "PICKED": "CASE-6-ROOF-PARAPET",
    },
}

# ------------------------------------------------------------------
# the counterfactual: the same five characteristics, from DECLARED
# SUBJECT TEXT only. That text was written from the owner's own case
# directive and contains no E1.4 output and no A21 answer.
# ------------------------------------------------------------------
DECLARED_SUBJECT_RULE = {
    "ORDINARY_WALL_WITH_PRINTED_DIMENSION":
        "the case whose declared subject names a gross wall face",
    "AN_OPENING":
        "the case whose declared subject names door and window deductions",
    "AN_AMBIGUOUS_OR_OPEN_BOUNDARY":
        "NOT DERIVABLE from declared subject text - no case declares it",
    "A_STAIR_OR_VERTICAL_CONDITION": "the case whose subject is the stair",
    "A_PARAPET_BALUSTRADE_DISTINCTION":
        "the case whose subject is the parapet",
}


def declared_subject_subset() -> dict:
    sel = json.loads(PILOT.read_text("utf-8"))
    tests = {c["CASE_ID"]: (c.get("WHAT_IT_TESTS") or "").lower()
             for c in sel["ROOM_CASES"]}
    assign = {}
    assign["ORDINARY_WALL_WITH_PRINTED_DIMENSION"] = next(
        (c for c, t in sorted(tests.items()) if "wall face" in t), None)
    assign["AN_OPENING"] = next(
        (c for c, t in sorted(tests.items())
         if "door" in t and "window" in t), None)
    assign["AN_AMBIGUOUS_OR_OPEN_BOUNDARY"] = None      # not derivable
    assign["A_STAIR_OR_VERTICAL_CONDITION"] = "CASE-4-STAIR"
    assign["A_PARAPET_BALUSTRADE_DISTINCTION"] = "CASE-6-ROOF-PARAPET"
    return assign


def source_reads() -> dict:
    """What files does subset.py actually open? Read from its own AST."""
    tree = ast.parse(SUBSET_SRC.read_text("utf-8"))
    consts = [n.value for n in ast.walk(tree)
              if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    return {
        "PATHS_NAMED_IN_THE_RULE_MODULE":
            sorted({c for c in consts if "/" in c and c.endswith(".json")}),
        "ANY_A21_RESULT_FILE_NAMED": sorted(
            {c for c in consts
             if any(k in c for k in ("a21_raw", "improved_raw", "FREEZE",
                                     "reader", "PASS"))}),
    }


def audit() -> dict:
    frozen = json.loads(
        (OUT / "PILOT_SUBSET_SELECTION.json").read_text("utf-8"))
    cf = declared_subject_subset()
    cf_subset = sorted({v for v in cf.values() if v})
    frozen_subset = sorted(frozen["SUBSET"])

    body = {
        "PHASE_ID": P.PHASE_ID,
        "ARTIFACT": "E1_4_INFLUENCE_AUDIT",
        "QUESTION": ("did the frozen four-case subset rule depend on E1.4 "
                     "chains, E1.4 boundaries, E1.4 quantities, or prior "
                     "A21 success/failure values?"),
        "ANSWER": {
            "E1_4_CHAINS": "YES - three of the five clauses read them",
            "E1_4_BOUNDARIES": (
                "YES - the chain register IS the boundary evidence; the "
                "chain element types are boundary classifications"),
            "E1_4_QUANTITIES": (
                "NO - no area, length or quantity field was read. Only "
                "element TYPE COUNTS were read"),
            "PRIOR_A21_SUCCESS_OR_FAILURE": (
                "NO - the rule module names no A21 result file and opens "
                "none; see SOURCE_READS below"),
        },
        "CLAUSE_BY_CLAUSE": CLAUSE_AUDIT,
        "SOURCE_READS": source_reads(),
        "COUNTERFACTUAL": {
            "RULE": DECLARED_SUBJECT_RULE,
            "ASSIGNMENT_WITHOUT_E1_4": cf,
            "SUBSET_WITHOUT_E1_4": cf_subset,
            "FROZEN_SUBSET": frozen_subset,
            "MEMBERSHIP_IDENTICAL": cf_subset == frozen_subset,
            "WHAT_THE_E1_4_CLAUSES_ACTUALLY_CHANGED": (
                "nothing in the membership. Clause 1 and clause 2 land on "
                "the same two cases the declared subjects name. Clause 3 "
                "is the only one that needed E1.4 at all, and it landed on "
                "CASE-3, which clause 2 had already selected"),
        },
        "THE_HONEST_POSITION": (
            "the influence was real and it was avoidable. Three clauses "
            "consulted a downstream interpretation when the case "
            "directive already carried enough to choose. That it changed "
            "no membership is luck, not design - had the chain register "
            "ranked differently, the subset would have differed and the "
            "contamination would have been invisible"),
        "WHAT_WAS_NOT_DONE": (
            "the subset is NOT changed, NOT refrozen and NOT re-derived. "
            "It stands exactly as frozen at "
            "f4ecb254e55fb155806bf5b336b61945b979db157913a7cbe78ecc5cef8fe83c"),
        "GOING_FORWARD": (
            "E1.4 is now sealed out of source requirements, sandbox "
            "membership, trace placement and A21 interpretation. The "
            "RECEPTION 26-of-29 observation is held as a sealed future "
            "reconciliation note and is used for nothing in this phase"),
    }
    p = OUT / "E1_4_INFLUENCE_AUDIT.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return {"SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "E1_4_INFLUENCED_THE_RULE": True,
            "CLAUSES_THAT_READ_E1_4": [k for k, v in CLAUSE_AUDIT.items()
                                       if v["READ_E1_4"]],
            "MEMBERSHIP_IDENTICAL_WITHOUT_IT":
                body["COUNTERFACTUAL"]["MEMBERSHIP_IDENTICAL"],
            "SUBSET_WITHOUT_E1_4": cf_subset,
            "FROZEN_SUBSET": frozen_subset}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
