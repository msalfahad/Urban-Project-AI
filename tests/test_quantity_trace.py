"""E44 — a quantity that can be traced back to the drawing it came from."""

from __future__ import annotations

import pytest

from engine.quantity_trace import (DRAFT, QuantityTrace, TraceError,
                                   TraceLedger, quantity_id)


def q(**kw):
    base = dict(quantity_id=quantity_id("23010", "2F", "BTH-03", "CERWALL",
                                        "GROSS"),
                space_id="BTH-03", use="GROSS_CERAMIC_WALL", unit="m2")
    base.update(kw)
    return QuantityTrace(**base)


def test_the_id_is_readable_and_structured():
    assert quantity_id("23010", "2F", "BTH-03", "CERWALL", "GROSS") == (
        "Q-23010-2F-BTH03-CERWALL-GROSS-001")


def test_the_id_does_not_depend_on_list_position():
    """A positional id loses Bathroom-03's identity on the first inserted room,
    and revision comparison is exactly the thing that needs it kept."""
    import inspect

    from engine import quantity_trace
    src = inspect.getsource(quantity_trace.quantity_id)
    for forbidden in ("enumerate", "index", "position", "row_number"):
        assert forbidden not in src, forbidden


def test_the_same_quantity_gets_the_same_id_next_revision():
    a = quantity_id("23010", "2F", "BTH-03", "CERWALL", "GROSS")
    b = quantity_id("23010", "2F", "BTH-03", "CERWALL", "GROSS")
    assert a == b


def test_gross_and_net_are_never_the_same_quantity():
    assert quantity_id("23010", "2F", "B1", "CER", "GROSS") != quantity_id(
        "23010", "2F", "B1", "CER", "NET")


def test_a_basis_nobody_stated_is_refused():
    """A gross figure read as net is an under-measure nobody notices."""
    with pytest.raises(TraceError, match="GROSS, NET or DIRECT"):
        quantity_id("23010", "2F", "B1", "CER", "MAYBE")


def test_a_value_without_a_release_status_is_refused():
    """A figure printed without the status that governs it gets quoted."""
    with pytest.raises(TraceError, match="release status"):
        q(value=8.6)


def test_a_value_with_a_status_is_accepted():
    t = q(value=8.6, release_status="READY",
          quantity_role="RELEASABLE_QUANTITY")
    assert t.is_released


def test_a_ready_candidate_is_not_yet_a_released_quantity():
    """READY says the dependencies are met. RELEASABLE_QUANTITY says the
    number may go in a takeoff. A candidate has the first and not the second."""
    t = q(value=8.6, release_status="READY")
    assert t.quantity_role == "CANDIDATE"
    assert not t.is_released


def test_a_blocked_quantity_is_not_released_even_with_a_value():
    t = q(value=8.6, release_status="BLOCKED_HEIGHT", primary_blocker="height")
    assert not t.is_released


def test_the_record_shows_empty_provenance_rather_than_omitting_it():
    """An absent key reads as "not applicable"; an empty one reads as "nobody
    established this". They are different facts."""
    r = q().record()
    for key in ("trade_rule_id", "assembly_id", "height_id", "opening_ids",
                "drawing_preview_reference", "highlight_geometry_reference"):
        assert key in r


def test_a_trace_says_what_it_cannot_answer():
    gaps = q().gaps()
    assert any("trade rule" in g for g in gaps)
    assert any("boundary geometry" in g for g in gaps)


def test_a_net_quantity_naming_no_openings_is_a_gap():
    t = q(use="NET_CERAMIC_WALL")
    assert any("NET quantity names no openings" in g for g in t.gaps())


def test_two_quantities_cannot_share_an_id():
    led = TraceLedger("23010")
    led.add(q())
    with pytest.raises(TraceError, match="already exists"):
        led.add(q())


def test_the_ledger_reports_how_many_traces_have_gaps():
    led = TraceLedger("23010", traces=[q()])
    out = led.summary()
    assert out["quantities"] == 1 and out["traces_with_gaps"] == 1
    assert out["by_validation_status"] == {DRAFT: 1}
