"""§8 — two statuses, because one word was answering two questions."""

from __future__ import annotations

import pytest

from engine.takeoff_status import (BLOCKED_FOR_FINAL_BOQ, COMPLETE,
                                   NO_VALIDATED_OUTPUT, READY_FOR_FINAL_BOQ,
                                   StatusError, TopLevelStatus,
                                   VALIDATED_PARTIAL, assess)

BASE = dict(uses_total=13, uses_with_ready_spaces=1, net_uses_ready=0,
            validated_physical_spaces=15, total_in_scope_spaces=17,
            openings_validated=0, signed_trade_rules=2,
            unresolved_topology_spaces=2, graph_gate_passed=False)


def test_coverage_and_boq_are_separate_answers():
    """The report said BLOCKED; the dashboard said VALIDATED_PARTIAL. Both were
    defensible readings of one field, which is the problem."""
    s = assess(**BASE)
    assert s.coverage_status == VALIDATED_PARTIAL
    assert s.boq_status == BLOCKED_FOR_FINAL_BOQ


def test_progress_on_coverage_is_never_permission_to_bill():
    """A takeoff that is 90% covered is 0% quotable. BOQ readiness is a
    conjunction, not a proportion."""
    s = assess(**{**BASE, "uses_with_ready_spaces": 12,
                  "validated_physical_spaces": 17})
    assert s.coverage_status == VALIDATED_PARTIAL
    assert s.boq_status == BLOCKED_FOR_FINAL_BOQ


def test_nothing_validated_is_its_own_coverage_state():
    s = assess(**{**BASE, "uses_with_ready_spaces": 0,
                  "validated_physical_spaces": 0})
    assert s.coverage_status == NO_VALIDATED_OUTPUT


def test_a_blocked_boq_must_name_its_blockers():
    s = assess(**BASE)
    assert s.boq_blockers
    assert any("opening" in b for b in s.boq_blockers)
    with pytest.raises(StatusError, match="naming no blocker"):
        TopLevelStatus(VALIDATED_PARTIAL, BLOCKED_FOR_FINAL_BOQ, "x", ())


def test_a_ready_boq_may_not_still_list_blockers():
    with pytest.raises(StatusError, match="blockers still listed"):
        TopLevelStatus(COMPLETE, READY_FOR_FINAL_BOQ, "x", ("something",))


def test_everything_clear_reaches_ready_for_final_boq():
    s = assess(uses_total=13, uses_with_ready_spaces=13, net_uses_ready=4,
               validated_physical_spaces=17, total_in_scope_spaces=17,
               openings_validated=40, signed_trade_rules=8,
               unresolved_topology_spaces=0, graph_gate_passed=True,
               openings_deduction_ready=True)
    assert s.coverage_status == COMPLETE
    assert s.boq_status == READY_FOR_FINAL_BOQ
    assert s.boq_blockers == ()


def test_no_arithmetic_connects_coverage_to_boq_readiness():
    """No amount of coverage earns a BOQ, so nothing computes one from the
    other."""
    import inspect

    from engine import takeoff_status
    src = inspect.getsource(takeoff_status.assess)
    # The blocker list is built from the underlying states only. No coverage
    # variable may appear in any condition that decides a blocker.
    body = src.split("blockers = []", 1)[1].split("return TopLevelStatus", 1)[0]
    for forbidden in ("coverage", "creason"):
        assert forbidden not in body, forbidden


# --- §22 the opening blocker must state what is actually true ---------------

def test_validated_openings_do_not_produce_no_opening_validated():
    """Two portals reached GEOMETRY_VALIDATED and the workbook still said 'no
    opening validated'. The sentence was simply false."""
    s = assess(uses_total=13, uses_with_ready_spaces=2, net_uses_ready=0,
               validated_physical_spaces=2, total_in_scope_spaces=23,
               openings_validated=2, signed_trade_rules=2,
               unresolved_topology_spaces=3, graph_gate_passed=False,
               openings_deduction_ready=False)
    joined = " | ".join(s.boq_blockers)
    assert "no opening is validated anywhere" not in joined
    assert "2 opening(s) are validated" in joined
    assert "deductions are not complete or production-approved" in joined


def test_zero_validated_openings_still_says_so_plainly():
    s = assess(uses_total=13, uses_with_ready_spaces=1, net_uses_ready=0,
               validated_physical_spaces=1, total_in_scope_spaces=23,
               openings_validated=0, signed_trade_rules=2,
               unresolved_topology_spaces=1, graph_gate_passed=False)
    assert any("no opening is validated anywhere" in b for b in s.boq_blockers)


def test_validated_openings_with_approved_deductions_raise_no_opening_blocker():
    s = assess(uses_total=13, uses_with_ready_spaces=13, net_uses_ready=4,
               validated_physical_spaces=17, total_in_scope_spaces=17,
               openings_validated=40, signed_trade_rules=8,
               unresolved_topology_spaces=0, graph_gate_passed=True,
               openings_deduction_ready=True)
    assert not any("opening" in b for b in s.boq_blockers)
