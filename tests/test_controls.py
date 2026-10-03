"""E58 — a control chosen after seeing the error is not a control."""

from __future__ import annotations

import pytest

from engine.controls import (EXCLUDED, REQUIRED_TYPES, Control, ControlError,
                             manifest, select)

SPACES = [
    {"space_id": "BTH-03", "room_type": "BATHROOM", "scope": "IN_SCOPE"},
    {"space_id": "BTH-01", "room_type": "BATHROOM", "scope": "IN_SCOPE"},
    {"space_id": "MBTH-01", "room_type": "BATHROOM", "scope": "OUT_OF_SCOPE"},
    {"space_id": "BED-04", "room_type": "BEDROOM", "scope": "IN_SCOPE"},
    {"space_id": "BED-02", "room_type": "BEDROOM", "scope": "IN_SCOPE"},
    {"space_id": "STR-01", "room_type": "STORE", "scope": "IN_SCOPE"},
    {"space_id": "WSH-01", "room_type": "WASHROOM", "scope": "IN_SCOPE"},
]


def test_the_rule_picks_the_lowest_numbered_in_scope_space_of_each_type():
    got = {c.room_type: c.space_id for c in select(SPACES)}
    assert got == {"BATHROOM": "BTH-01", "BEDROOM": "BED-02",
                   "STORE": "STR-01"}


def test_out_of_scope_spaces_are_never_controls():
    assert "MBTH-01" not in {c.space_id for c in select(SPACES)}


def test_a_space_with_a_stated_prior_defect_is_excluded():
    """BED-04's bathroom never separates from it. BED-02 is picked instead —
    and the exclusion is a STATED defect, not a room that measured badly."""
    assert "BED-04" in EXCLUDED
    assert "BED-04" not in {c.space_id for c in select(SPACES)}


def test_the_selector_refuses_to_see_a_measurement():
    """The signature is the guarantee."""
    with pytest.raises(ControlError, match="is not a control"):
        select([{"space_id": "BTH-01", "room_type": "BATHROOM",
                 "scope": "IN_SCOPE", "area_m2": 4.26}])
    with pytest.raises(ControlError, match="is not a control"):
        select([{"space_id": "BTH-01", "room_type": "BATHROOM",
                 "scope": "IN_SCOPE", "iou": 0.97}])


def test_the_set_covers_a_bathroom_a_bedroom_and_a_store():
    """One room type is not a test of an engine."""
    assert {c.room_type for c in select(SPACES)} == set(REQUIRED_TYPES)


def test_the_manifest_states_the_rule_before_any_comparison():
    m = manifest(select(SPACES))
    assert m["frozen_before_comparison"] is True
    assert "lowest-numbered" in m["selection_rule"]
    assert m["missing_types"] == []
    assert "WSH-01" in m["excluded_with_reasons"]


def test_a_missing_type_is_reported_rather_than_substituted():
    m = manifest(select([s for s in SPACES if s["room_type"] != "STORE"]))
    assert m["missing_types"] == ["STORE"]
