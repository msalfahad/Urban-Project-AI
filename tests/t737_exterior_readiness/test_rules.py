"""R-T737-1 on a synthetic villa W737 (not the development villa), every figure by hand.

W737: ground floor F.F.L. +0.40 with a plinth from the ground 0.00, ground storey +0.40 .. +3.60, a ground roof
parapet +3.60 .. +4.10 on side E-1, a first floor +3.60 .. +6.80 whose side S-1 also faces the lower roof from +2.80
(the two-F.F.L. case: the part +2.80 .. +3.60 belongs to the ground line), and a first-floor parapet +6.80 .. +7.60.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in ("agents_t737", "agents_t728"):
    sys.path.insert(0, str(ROOT / "research" / p))
import t737_rules as R  # noqa: E402
import t728_rules as B  # noqa: E402


def F(floor, side, portion, kind, bottom, top, line):
    return {"floor": floor, "side": side, "portion": portion, "kind": kind, "bottom": bottom, "top": top, "line": line}


FACES = [
    F("GF", "N-1", "EDGE", "plinth", 0.0, 0.4, "PLINTH"), F("GF", "N-1", "EDGE", "storey", 0.4, 3.6, "L-GF"),
    F("GF", "E-1", "EDGE", "plinth", 0.0, 0.4, "PLINTH"), F("GF", "E-1", "EDGE", "storey", 0.4, 3.6, "L-GF"),
    F("GF", "E-1", "EDGE", "parapet", 3.6, 4.1, "PAR-GF"),
    F("GF", "E-1", "COVERED", "storey", 0.4, 3.6, "L-GF"),
    F("1F", "S-1", "OVER", "over_lower_roof", 2.8, 3.6, "L-GF"), F("1F", "S-1", "STOREY", "storey", 3.6, 6.8, "L-1F"),
    F("1F", "S-1", "PARAPET", "parapet", 6.8, 7.6, "PAR-1F"),
    F("1F", "W-1", "STOREY", "storey", 3.6, 6.8, "L-1F"),
    F("1F", "W-1", "SLAB", "slab_edge", None, None, "SLAB-1F"),
]


def segs(res):
    return [(a, b, line, m) for a, b, line, m in res["segments"]]


# ---- rule 4: normal cases ------------------------------------------------------------------------------------------
def test_corner_cut_at_every_face_level_by_hand():
    res = R.split_arris({"id": "c1", "floor": "GF", "sides": ["N-1", "E-1"], "bottom": 0.0, "top": 4.1}, FACES)
    # E-1 EDGE holds the whole 4.10 m: plinth 0.40 + storey 3.20 + parapet 0.50 (N-1 holds only 3.60)
    assert res["state"] == "SPLIT"
    assert segs(res) == [(0.0, 0.4, "PLINTH", 0.4), (0.4, 3.6, "L-GF", 3.2), (3.6, 4.1, "PAR-GF", 0.5)]
    assert R.group_by_line([(s[2], s[3]) for s in res["segments"]]) == {"PLINTH": 0.4, "L-GF": 3.2, "PAR-GF": 0.5}


def test_two_ffl_corner_part_on_the_lower_line():
    res = R.split_arris({"id": "c2", "floor": "1F", "sides": ["S-1", "W-1"], "bottom": 2.8, "top": 6.8}, FACES)
    assert segs(res) == [(2.8, 3.6, "L-GF", 0.8), (3.6, 6.8, "L-1F", 3.2)]


def test_mirror_order_of_sides_same_split():
    a = R.split_arris({"id": "m", "floor": "1F", "sides": ["S-1", "W-1"], "bottom": 2.8, "top": 7.6}, FACES)
    b = R.split_arris({"id": "m", "floor": "1F", "sides": ["W-1", "S-1"], "bottom": 2.8, "top": 7.6}, FACES)
    assert segs(a) == segs(b) == [(2.8, 3.6, "L-GF", 0.8), (3.6, 6.8, "L-1F", 3.2), (6.8, 7.6, "PAR-1F", 0.8)]


def test_units_mm_input_is_not_metres():
    # a span given in mm holds nothing on a metre face set: it is NO_HOST, never silently cut at metre levels
    res = R.split_arris({"id": "u", "floor": "1F", "sides": ["S-1"], "bottom": 2800.0, "top": 6800.0}, FACES)
    assert res["state"] == "NO_HOST" and segs(res)[0][2] is None


# ---- rule 4: adverse ------------------------------------------------------------------------------------------------
def test_parapet_part_never_carried_twice_and_sum_is_the_span():
    res = R.split_arris({"id": "c3", "floor": "1F", "sides": ["S-1", "W-1"], "bottom": 3.6, "top": 7.6}, FACES)
    lines = [s[2] for s in res["segments"]]
    assert lines.count("PAR-1F") == 1 and "L-1F" in lines
    assert abs(sum(s[3] for s in res["segments"]) - 4.0) < 1e-9


def test_part_above_every_face_is_no_host_never_a_neighbour():
    res = R.split_arris({"id": "c4", "floor": "GF", "sides": ["E-1"], "bottom": 0.0, "top": 4.5}, FACES)
    assert res["state"] == "PARTIAL"
    assert segs(res)[-1] == (4.1, 4.5, None, 0.4)


def test_equal_stacks_with_different_lines_are_ambiguous_not_split():
    faces = [F("GF", "X", "A", "storey", 0.0, 3.0, "L1"), F("GF", "X", "B", "storey", 0.0, 3.0, "L2")]
    res = R.split_arris({"id": "c5", "floor": "GF", "sides": ["X"], "bottom": 0.0, "top": 3.0}, faces)
    assert res["state"] == "AMBIGUOUS" and res["segments"] == []


def test_face_without_levels_is_not_a_host():
    res = R.split_arris({"id": "c6", "floor": "1F", "sides": ["W-1"], "bottom": 3.6, "top": 6.8}, FACES)
    assert segs(res) == [(3.6, 6.8, "L-1F", 3.2)]       # the slab edge (no printed depth) is never used


def test_zero_height_arris_refused_and_zero_segment_refused():
    with pytest.raises(R.CensusError):
        R.split_arris({"id": "z", "floor": "GF", "sides": ["N-1"], "bottom": 1.0, "top": 1.0}, FACES)
    with pytest.raises(R.CensusError):
        R.group_by_line([("L-GF", 0.0)])


# ---- rule 1 ---------------------------------------------------------------------------------------------------------
IDX = [
    {"line_id": "L-host", "item_code": "FIN.EXT.FINISH", "unit": "m2", "element_id": "GF-FACADE:facade",
     "class": "HELD", "measured_net": None, "held_low": None, "held_high": None},
    {"line_id": "L-nbr", "item_code": "FIN.EXT.FINISH", "unit": "m2", "element_id": "1F-FACADE:facade",
     "class": "HELD", "measured_net": None, "held_low": None, "held_high": None},
    {"line_id": "L-moved", "item_code": "FIN.EXT.FINISH", "unit": "m2", "element_id": "2F-FACADE:facade",
     "class": "HELD", "measured_net": None, "held_low": 10.0, "held_high": 12.0},
]
BLANK_BEFORE = {"state": "BLOCKED_RFI", "value": None, "low": None, "high": None}


def chg(lid, el):
    return {"action": "CHANGE", "line_id": lid, "element_id": el, "before": BLANK_BEFORE}


def test_live_host_and_free_new_line():
    k = dict(item_code="FIN.EXT.FINISH", unit="m2")
    assert R.classify_stage_line(chg("L-host", "GF-FACADE:facade"), IDX, **k)["census"] == R.LIVE
    add = {"action": "ADD", "line_id": "L-new", "element_id": "GF-FACADE:PLINTH"}
    assert R.classify_stage_line(add, IDX, **k)["census"] == R.LIVE_NEW


def test_gone_host_never_maps_to_a_neighbour():
    k = dict(item_code="FIN.EXT.FINISH", unit="m2")
    c = R.classify_stage_line(chg("L-gone", "1F-FACADE:facade"), IDX, **k)
    assert c["census"] == R.GONE and c["host_now"] is None     # L-nbr carries that element id: not used


def test_moved_host_is_stale_with_the_moved_figure():
    k = dict(item_code="FIN.EXT.FINISH", unit="m2")
    c = R.classify_stage_line(chg("L-moved", "2F-FACADE:facade"), IDX, **k)
    assert c["census"] == R.STALE and (c["host_now"]["held_low"], c["host_now"]["held_high"]) == (10.0, 12.0)


def test_unit_or_code_change_is_stale_and_element_swap_is_stale():
    c = R.classify_stage_line(chg("L-host", "GF-FACADE:facade"), IDX, item_code="FIN.EXT.FINISH", unit="lm")
    assert c["census"] == R.STALE
    c = R.classify_stage_line(chg("L-host", "2F-FACADE:facade"), IDX, item_code="FIN.EXT.FINISH", unit="m2")
    assert c["census"] == R.STALE


def test_add_collisions_by_element_or_line_id():
    k = dict(item_code="FIN.EXT.FINISH", unit="m2")
    assert R.classify_stage_line({"action": "ADD", "line_id": None, "element_id": "1F-FACADE:facade"}, IDX,
                                 **k)["census"] == R.COLLISION
    assert R.classify_stage_line({"action": "ADD", "line_id": "L-host", "element_id": "X"}, IDX,
                                 **k)["census"] == R.COLLISION


def test_malformed_rows_refused():
    k = dict(item_code="FIN.EXT.FINISH", unit="m2")
    with pytest.raises(R.CensusError):
        R.classify_stage_line({"action": "CHANGE", "line_id": None, "element_id": "x"}, IDX, **k)
    with pytest.raises(R.CensusError):
        R.classify_stage_line({"action": "MOVE", "line_id": "L-host", "element_id": "x"}, IDX, **k)


# ---- rules 2 and 5 --------------------------------------------------------------------------------------------------
def test_source_census():
    assert R.source_census({"a": "1", "b": "2", "c": "3"}, {"a": "1", "b": "9"}) == \
        {"a": R.SAME, "b": R.CHANGED, "c": R.ABSENT}


def test_post_stage_host_state_and_bead_follows_r_t728():
    assert R.post_stage_host_state({"state": "PROVISIONAL", "value": 117.3, "low": None, "high": None}) == R.RELEASED
    assert R.post_stage_host_state({"state": "BOUNDED_EXPOSURE", "value": None, "low": 1.0, "high": 2.0}) == R.BOUNDED
    assert R.post_stage_host_state({"state": "BLOCKED_RFI", "value": None, "low": None, "high": None}) == R.BLANK
    # the same arris part: released with a released host, a HELD point on a bounded host, never 0
    assert B.bead_state(B.MEASURED, 3.2, None, None, R.RELEASED)["value"] == 3.2
    held = B.bead_state(B.MEASURED, 3.2, None, None, R.BOUNDED, host_cause="host bounded")
    assert (held["state"], held["low"], held["high"], held["value"]) == (B.HELD_BOUND, 3.2, 3.2, None)


def test_post_stage_host_state_adverse():
    with pytest.raises(R.CensusError):
        R.post_stage_host_state({"state": "MEASURED", "value": 0.0, "low": None, "high": None})
    with pytest.raises(R.CensusError):
        R.post_stage_host_state({"state": "BOUNDED_EXPOSURE", "value": None, "low": 5.0, "high": 4.0})
    with pytest.raises(R.CensusError):
        R.post_stage_host_state({"state": "BOUNDED_EXPOSURE", "value": None, "low": None, "high": 4.0})


def test_git_blob_id_matches_git():
    assert R.git_blob_id(b"") == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"      # git's empty blob
