"""§13: BED-01's frozen diagnostic result is asserted on every run."""

import pytest

from engine import freeze_guard as fg


def _row(area=fg.FROZEN_AREA_M2, h=fg.HASH_SINCE_ROUND_1_5, sid="BED-01"):
    return {"space_id": sid, "clear_internal_area_m2": area,
            "geometry_hash": h, "status": "GEOMETRY_ACCEPTED_AND_FROZEN"}


def test_the_frozen_result_holds_under_either_recorded_hash():
    for h in fg.ACCEPTED_HASHES:
        got = fg.check([_row(h=h)])
        assert got.status == fg.HELD
        assert got.holds


def test_a_moved_area_is_a_failure_not_a_warning():
    got = fg.check([_row(area=21.34)])
    assert got.status == fg.MOVED
    assert not got.holds
    assert "may not be altered by any repair" in got.why


def test_a_hairline_area_change_still_counts_as_moved():
    """A frozen number is the number, not a neighbourhood of it."""
    got = fg.check([_row(area=fg.FROZEN_AREA_M2 + 0.002)])
    assert got.status == fg.MOVED


def test_the_reporting_precision_is_not_a_tuning_allowance():
    got = fg.check([_row(area=fg.FROZEN_AREA_M2 + 0.0004)])
    assert got.status == fg.HELD


def test_an_unknown_hash_with_the_right_area_is_flagged_not_accepted():
    got = fg.check([_row(h="deadbeefdeadbeefdeadbeef")])
    assert got.status == fg.RE_EXPRESSED
    assert got.holds          # the measurement is intact
    assert "needs a stated reason" in got.why


def test_a_missing_control_is_not_a_pass():
    got = fg.check([_row(sid="BTH-01")])
    assert got.status == fg.ABSENT
    assert not got.holds
    assert "failure to check, not a pass" in got.why


def test_the_record_keeps_the_hash_history_rather_than_rewriting_it():
    rec = fg.check([_row()]).record()
    h = rec["hash_history"]
    assert h["as_originally_frozen"] == fg.HASH_AS_ORIGINALLY_FROZEN
    assert h["since_round_1_5"] == fg.HASH_SINCE_ROUND_1_5
    assert h["superseded_at_commit"] == fg.HASH_SUPERSEDED_AT
    assert "AREA did not move" in h["why_two_hashes"]


def test_a_new_supported_polygon_becomes_a_new_record_not_a_mutation():
    rec = fg.check([_row()]).record()
    assert "NEW geometry record" in rec["what_a_new_polygon_requires"]
    assert "not mutated" in rec["what_a_new_polygon_requires"]
