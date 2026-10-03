"""E46 — entity identity across revisions, and refusing to fake a baseline."""

from __future__ import annotations

from engine.revision_entities import (ADDED, BY_GEOMETRY, BY_ID,
                                      GEOMETRY_CHANGED, NO_PRIOR, REMOVED,
                                      SCOPE_CHANGED, UNCHANGED, UNMATCHED,
                                      compare, match_spaces)

A = [{"space_id": "BTH-03", "scope": "IN_SCOPE", "room_type": "BATHROOM",
      "floor_area_m2": 4.08, "centroid_mm": (1000, 1000)}]


def test_one_revision_reports_no_baseline_not_zero_changes():
    """They look identical in a report and mean opposite things."""
    out = compare(None, {"revision_id": "MAR.2023"})
    assert out["status"] == NO_PRIOR
    assert out["entity_changes"] == []
    assert "NOT a report of zero changes" in out["why"]


def test_an_unchanged_space_is_matched_by_its_stable_id():
    out = compare({"spaces": A}, {"spaces": A})
    assert out["summary"] == {UNCHANGED: 1}
    assert out["matched_by"] == {BY_ID: 1}


def test_a_room_that_moved_100mm_keeps_its_identity():
    """Bathroom-03 must stay Bathroom-03 after a wall move."""
    moved = [{"space_id": "NEW-ID", "scope": "IN_SCOPE",
              "room_type": "BATHROOM", "floor_area_m2": 4.08,
              "centroid_mm": (1100, 1000)}]
    m = match_spaces(A, moved)
    assert m["NEW-ID"] == ("BTH-03", BY_GEOMETRY)


def test_a_room_across_the_building_is_not_the_same_room():
    far = [{"space_id": "OTHER", "centroid_mm": (40000, 40000)}]
    assert match_spaces(A, far)["OTHER"] == ("", UNMATCHED)


def test_identity_never_comes_from_list_position():
    import inspect

    from engine import revision_entities
    src = inspect.getsource(revision_entities.match_spaces)
    for forbidden in ("enumerate", "zip(prior", "[i]"):
        assert forbidden not in src, forbidden


def test_an_area_change_beyond_noise_is_a_geometry_change():
    bigger = [dict(A[0], floor_area_m2=4.9)]
    assert compare({"spaces": A}, {"spaces": bigger})["summary"] == {
        GEOMETRY_CHANGED: 1}


def test_measurement_noise_is_not_reported_as_a_redesign():
    same = [dict(A[0], floor_area_m2=4.10)]
    assert compare({"spaces": A}, {"spaces": same})["summary"] == {UNCHANGED: 1}


def test_a_scope_decision_is_its_own_kind_of_change():
    out = compare({"spaces": A},
                  {"spaces": [dict(A[0], scope="OUT_OF_SCOPE")]})
    assert out["summary"] == {SCOPE_CHANGED: 1}


def test_added_and_removed_are_both_reported():
    out = compare({"spaces": A}, {"spaces": [
        {"space_id": "NEW", "centroid_mm": (40000, 40000)}]})
    assert out["summary"] == {ADDED: 1, REMOVED: 1}


def test_a_percentage_change_is_none_when_there_is_nothing_to_divide_by():
    out = compare({"spaces": [], "quantities": []},
                  {"spaces": [], "quantities": [
                      {"quantity_id": "Q-1", "value": 5.0}]})
    assert out["quantity_deltas"][0]["percentage_change"] is None
    assert out["quantity_deltas"][0]["absolute_change"] is None
