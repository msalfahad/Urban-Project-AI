"""Tests for E5 — Approval & Audit Log (append-only)."""

import pytest

from engine.audit_log import AuditLog, AuditEntry


def test_record_appends_and_returns():
    log = AuditLog()
    e = log.record(actor="Eng. Fahad", action="approve", entity="project:TEST-x")
    assert isinstance(e, AuditEntry)
    assert len(log) == 1
    assert log.entries[0].actor == "Eng. Fahad"


def test_entry_is_immutable():
    log = AuditLog()
    e = log.record(actor="a", action="edit_rate", entity="boqItem:1",
                   field="costRate", from_value=28, to_value=30)
    with pytest.raises(Exception):
        e.to_value = 99  # frozen dataclass


def test_actor_and_action_required():
    log = AuditLog()
    with pytest.raises(ValueError):
        log.record(actor="", action="approve", entity="x")
    with pytest.raises(ValueError):
        log.record(actor="a", action="", entity="x")


def test_reads_filter_by_entity_and_actor():
    log = AuditLog()
    log.record(actor="a", action="approve", entity="p1")
    log.record(actor="b", action="edit", entity="p1", field="rate", from_value=1, to_value=2)
    log.record(actor="a", action="approve", entity="p2")
    assert len(log.for_entity("p1")) == 2
    assert len(log.by_actor("a")) == 2


def test_entries_view_is_readonly_copy():
    log = AuditLog()
    log.record(actor="a", action="x", entity="e")
    view = log.entries
    assert isinstance(view, tuple)
    # mutating the view can't affect the log
    with pytest.raises(AttributeError):
        view.append("nope")  # tuples have no append


def test_change_is_fully_captured():
    log = AuditLog()
    e = log.record(actor="Eng. Fahad", action="override_quantity",
                   entity="boqItem:conc", field="qty", from_value=352.44,
                   to_value=380, reason="concrete over-order for waste",
                   ref="خرسانة مسلحة/ورقة1")
    d = e.to_dict()
    assert d["from_value"] == 352.44 and d["to_value"] == 380
    assert d["reason"] and d["ref"]
