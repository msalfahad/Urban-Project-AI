"""Phase 2B-3 (ARCH_TAKEOFF_V2.5) door worked examples - WP-4 of the program: each of the ten cases shows the
existing opening, the required opening, the available wall, the geometric feasibility and the approvals; the hand
values agree with the independent reference and with the engine; no case claims structural feasibility; V2.4 differs
only where the proof found its defect (DR-06, the junction at the reading reach)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import proof_cases_doors as D                                 # noqa: E402
import proof_check as PC                                      # noqa: E402
import proof_engine as E                                      # noqa: E402

V24_FAILS = {"DR-06": {"end_constraint", "max_feasible_enlargement_m", "max_is_lower_bound"}}


@pytest.mark.parametrize("case", D.DOOR_CASES, ids=lambda c: c["id"])
def test_hand_reference_and_engine_agree(case):
    ref = PC.door_hand_vs_reference(case)
    assert len(ref) >= 5 and [r for r in ref if r["result"] != "AGREE"] == []
    rows = E.compare(case["expected"], E.door_quantities(case, E.V25))
    assert [(r["quantity"], r["expected"], r["engine"]) for r in rows if r["result"] == "FAIL"] == []


def test_v2_4_differs_only_at_the_reach_boundary():
    for c in D.DOOR_CASES:
        rows = E.compare(c["expected"], E.door_quantities(c, E.V24))
        assert {r["quantity"] for r in rows if r["result"] == "FAIL"} == V24_FAILS.get(c["id"], set()), c["id"]


def test_no_structural_feasibility_claim_without_structural_evidence():
    """every enlargement keeps the structural engineer's approval: MASONRY_INDICATED is not verified, and even a
    project rule from the structural plan (DR-05) leaves the lintel to the engineer; nothing is called structurally
    feasible."""
    for c in D.DOOR_CASES:
        q = E.door_quantities(c, E.V25)
        if q["enlargement_m"]:
            assert "structural engineer" in q["approvals"], c["id"]
            assert q["structure"] in ("MASONRY_INDICATED", "NON_STRUCTURAL_SPECIFIED"), c["id"]
            assert "STRUCTURAL" not in (q["feasibility"] or "").replace("NON_STRUCTURAL", ""), c["id"]


def test_the_as_drawn_door_is_never_changed_by_the_owner_standard():
    q = E.door_quantities(D.DR_10, E.V25)
    assert q["as_drawn_width_m"] == 0.9 and q["enlargement_m"] == 0.2 and q["door_area_m2"] is None
    assert q["assumed_area_state"] == "ASSUMED"
