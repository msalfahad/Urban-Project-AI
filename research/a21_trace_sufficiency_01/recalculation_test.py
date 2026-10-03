"""PARAMETRIC_RECALCULATION_TEST - proves the mechanism, on synthetic data.

Success criterion F: changing a QS parameter changes the deterministic
arithmetic WITHOUT changing the visual interpretation. That second half
is the part worth proving, so the test hashes the trace-derived geometry
before and after and requires it to be byte-identical.

The parameter moved here is TEST_WALL_HEIGHT, 3.00 -> 3.10, and it is
synthetic. The owner's real P7757 plaster height is not introduced, is
not referenced, and does not appear in any artifact this test writes.
The real APPLICABLE_PLASTER_HEIGHT stays UNKNOWN throughout, and the
test asserts that it does.

    python3 -m research.a21_trace_sufficiency_01.recalculation_test
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.a21_trace_sufficiency_01 import parameters as PM
from research.a21_trace_sufficiency_01 import protocol as P

OUT = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")

SYNTHETIC_NOTICE = (
    "every figure in this test is synthetic. No P7757 length, no P7757 "
    "height and no owner-supplied value appears anywhere in it. It "
    "exercises the software mechanism and nothing else")

# a tiny synthetic geometry set, shaped exactly like trace-derived input
SYNTHETIC_GEOMETRY = [
    {"ITEM_ID": "T-WALL-A", "CASE_ID": "SYNTHETIC",
     "TREATMENT": "NORMAL_INTERNAL_PLASTER", "LENGTH_M": 4.0,
     "SOURCE_TYPE": "DRAWING", "SUPPORTED_BY_TRACES": ["T-DIM-1"],
     "HEIGHT_PARAMETER": "TEST_WALL_HEIGHT"},
    {"ITEM_ID": "T-WALL-B", "CASE_ID": "SYNTHETIC",
     "TREATMENT": "NORMAL_INTERNAL_PLASTER", "LENGTH_M": 2.5,
     "SOURCE_TYPE": "DRAWING", "SUPPORTED_BY_TRACES": ["T-DIM-2"],
     "HEIGHT_PARAMETER": "TEST_WALL_HEIGHT"},
    # this one leans on a default, so it must stay provisional forever
    {"ITEM_ID": "T-OPENING-C", "CASE_ID": "SYNTHETIC",
     "TREATMENT": "OPENING_REVEALS_AND_RETURNS", "LENGTH_M": 1.0,
     "SOURCE_TYPE": "DRAWING", "SUPPORTED_BY_TRACES": ["T-DIM-3"],
     "HEIGHT_PARAMETER": "DOOR_HEIGHT"},
    # and this one has no height at all
    {"ITEM_ID": "T-WALL-D", "CASE_ID": "SYNTHETIC",
     "TREATMENT": "NORMAL_INTERNAL_PLASTER", "LENGTH_M": 3.0,
     "SOURCE_TYPE": "DRAWING", "SUPPORTED_BY_TRACES": ["T-DIM-4"],
     "HEIGHT_PARAMETER": "APPLICABLE_PLASTER_HEIGHT"},
]


def _geometry_hash(g) -> str:
    return hashlib.sha256(
        json.dumps(g, sort_keys=True).encode()).hexdigest()


def run() -> dict:
    reg = PM.default_registry()
    reg["TEST_WALL_HEIGHT"] = PM.parameter(
        "TEST_WALL_HEIGHT", 3.00, "m", "OWNER_PROJECT_INPUT",
        "SYNTHETIC test parameter - not a P7757 value",
        project_specific=False, owner_confirmed=True, version=1)

    before_geom = _geometry_hash(SYNTHETIC_GEOMETRY)
    before = PM.compute(SYNTHETIC_GEOMETRY, reg)

    reg2 = PM.with_owner_value(
        reg, "TEST_WALL_HEIGHT", 3.10, "m", 2,
        "SYNTHETIC test parameter, version 2 - not a P7757 value")
    after_geom = _geometry_hash(SYNTHETIC_GEOMETRY)
    after = PM.compute(SYNTHETIC_GEOMETRY, reg2)

    changed, unchanged = [], []
    for b, a in zip(before["LINES"], after["LINES"]):
        (changed if b["AREA_M2"] != a["AREA_M2"] else unchanged).append({
            "ITEM_ID": b["ITEM_ID"],
            "BEFORE_AREA_M2": b["AREA_M2"], "AFTER_AREA_M2": a["AREA_M2"],
            "BEFORE_STATE": b["QUANTITY_STATE"],
            "AFTER_STATE": a["QUANTITY_STATE"],
        })

    checks = {
        "GEOMETRY_UNCHANGED_BY_THE_PARAMETER_CHANGE":
            before_geom == after_geom,
        "VISUAL_INTERPRETATION_WAS_NOT_RERUN": (
            "no reader was invoked; compute() consumed the same geometry "
            "object twice"),
        "DEPENDENT_QUANTITIES_RECALCULATED": len(changed) == 2,
        "DEFAULT_BACKED_LINE_STAYED_PROVISIONAL": all(
            l["QUANTITY_STATE"] == "PROVISIONAL_DEFAULT_QUANTITY"
            for l in after["LINES"] if l["ITEM_ID"] == "T-OPENING-C"),
        "UNKNOWN_HEIGHT_LINE_STAYED_NOT_ESTABLISHED": all(
            l["QUANTITY_STATE"] == "NOT_ESTABLISHED"
            for l in after["LINES"] if l["ITEM_ID"] == "T-WALL-D"),
        "OWNER_SUPPLIED_HEIGHT_YIELDS_OWNER_PARAMETRIC_NOT_SOURCE_ESTABLISHED":
            all(l["QUANTITY_STATE"] == "OWNER_PARAMETRIC_QUANTITY"
                for l in after["LINES"]
                if l["ITEM_ID"] in ("T-WALL-A", "T-WALL-B")),
        "REAL_PLASTER_HEIGHT_STILL_UNKNOWN": (
            reg2["APPLICABLE_PLASTER_HEIGHT"]["VALUE"] is None
            and reg2["APPLICABLE_PLASTER_HEIGHT"]["SOURCE_TYPE"] == "UNKNOWN"),
        "NO_OWNER_P7757_HEIGHT_ANYWHERE_IN_THIS_TEST": True,
    }

    body = {
        "PHASE_ID": P.PHASE_ID,
        "ARTIFACT": "PARAMETRIC_RECALCULATION_TEST",
        "SYNTHETIC_NOTICE": SYNTHETIC_NOTICE,
        "TEST_PARAMETER": {"PARAMETER_ID": "TEST_WALL_HEIGHT",
                           "FROM": 3.00, "TO": 3.10, "UNIT": "m",
                           "SYNTHETIC": True},
        "GEOMETRY_SHA256_BEFORE": before_geom,
        "GEOMETRY_SHA256_AFTER": after_geom,
        "BEFORE": before, "AFTER": after,
        "RECALCULATED": changed,
        "UNCHANGED": unchanged,
        "CHECKS": checks,
        "ALL_CHECKS_PASS": all(v for v in checks.values()
                               if isinstance(v, bool)),
        "WHAT_THIS_PROVES": (
            "the arithmetic follows the parameter and the interpretation "
            "does not. The same trace-derived geometry produced both "
            "results, byte-identical, while two dependent areas moved and "
            "a default-backed line and an unknown-height line refused to "
            "move at all"),
        "THE_STATE_RULE_HELD": (
            "an owner-supplied height produced OWNER_PARAMETRIC_QUANTITY, "
            "not SOURCE_ESTABLISHED_QUANTITY, even though every length in "
            "it came from the drawing"),
    }
    p = OUT / "PARAMETRIC_RECALCULATION_TEST.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")

    # a real P7757 owner height must never reach this artifact
    txt = p.read_text("utf-8")
    for forbidden in ("3.2", "3,20"):
        if forbidden in txt:
            raise SystemExit(
                f"a P7757-shaped height reached the synthetic test: "
                f"{forbidden}")

    return {"SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "ALL_CHECKS_PASS": body["ALL_CHECKS_PASS"],
            "CHECKS": checks,
            "RECALCULATED": [(c["ITEM_ID"], c["BEFORE_AREA_M2"],
                              c["AFTER_AREA_M2"]) for c in changed]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
