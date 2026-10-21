"""T-089 membrane cutting plan: every expected value below is written by hand from the room sizes and the owner's
strip method (Q-30 kitchen worked example; roll 1.00 x 10.00 m UP-WP-001, lap 0.10 m UP-WP-002, upturn 0.20 m
UP-WP-003; Q-49 A: each room alone, the layout with the fewest whole rolls, tie: the shorter strip metres). The
hand arithmetic is in each docstring. Synthetic rooms only: no client project."""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET

import pytest

from engine.source import membrane_cutting_plan as C
from engine.source import membrane_fold_v2 as F

A = pytest.approx


def rect(x, y, x0=0.0, y0=0.0):
    return [(x0, y0), (x0 + x, y0), (x0 + x, y0 + y), (x0, y0 + y)]


def turn(ring, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(p[0] * c - p[1] * s, p[0] * s + p[1] * c) for p in ring]


def cand(a, direction, start):
    return next(c for c in a["candidates"] if c["direction"] == direction and c["start"] == start)


def pieces(a):
    return [p for s in a["selected"]["strip_list"] for p in s["pieces"]]


def check_identities(a):
    """rolls x roll length = strip metres + leftover; every piece in exactly one roll and inside it; cut + trim =
    metres x roll width; per-roll leftover = roll length - used."""
    sp = a["spec"]
    s = a["selected"]
    assert a["rolls_to_buy"] * sp["roll_length_m"] == A(a["strip_metres"] + a["leftover_m"], abs=1e-3)
    assert a["cut_m2"] + a["side_trim_m2"] == A(a["strip_metres"] * sp["roll_width_m"], abs=1e-3)
    n = sum(len(r["pieces"]) for r in s["rolls"])
    assert n == len(pieces(a))
    for r in s["rolls"]:
        assert r["used_m"] <= sp["roll_length_m"] + 1e-6
        assert r["leftover_m"] == A(sp["roll_length_m"] - r["used_m"], abs=1e-4)
    for p in pieces(a):
        assert p["length_m"] <= sp["roll_length_m"] + 1e-6
        assert p["to_m"] - p["from_m"] == A(p["length_m"], abs=1e-4)
        assert p["to_m"] <= sp["roll_length_m"] + 1e-6


# ------------------------------------------------------------------------------------------------ owner's examples
def test_owner_kitchen_3x4_chooses_along_two_rolls():
    """3.00 x 4.00 m (owner Q-30 / Q-49 example). Along the 4 m wall: floor 0.80 + 0.90 + 0.90 + 0.40 = 3.00 m, the
    4th strip 0.40 + 0.10 + 0.20 = 0.70 m wide; 4 strips of 4.00 + 0.40 = 4.40 m = 17.60 m; two per 10 m roll = 2
    rolls, each 8.80 used, 1.20 left = 2.40 m left; cut 3 x 4.40 + 0.70 x 4.40 = 16.28 m2; side trim 0.30 x 4.40 =
    1.32 m2. Across the 3 m wall: span 4.00 + 0.40 = 4.40 -> ceil(3.40 / 0.90) + 1 = 5 strips of 3.00 + 0.40 = 3.40
    m = 17.00 m; two per roll (3 x 3.40 = 10.20 > 10) = 3 rolls. Q-49 A: along (2 < 3). Lower bound ceil(17.60 / 10)
    = 2: optimal."""
    a = C.plan(rect(3.0, 4.0), floor="X", room_id="K", group="WET_AREA")
    assert a["state"] == "COMPUTED"
    s = a["selected"]
    assert s["direction"] == F.ALONG_LONG
    assert [(x["width_m"], x["length_m"]) for x in s["strip_list"]] == [(1.0, 4.4), (1.0, 4.4), (1.0, 4.4),
                                                                        (0.7, 4.4)]
    assert a["rolls_to_buy"] == 2 and a["strip_metres"] == A(17.60) and a["leftover_m"] == A(2.40)
    assert [r["leftover_m"] for r in s["rolls"]] == [A(1.20), A(1.20)]
    assert a["cut_m2"] == A(16.28) and a["side_trim_m2"] == A(1.32)
    assert s["proof_state"] == "OPTIMAL_AT_LOWER_BOUND" and s["lower_bound"] == 2
    ac = cand(a, F.ACROSS, C.LOWER)
    assert ac["strips"] == 5 and ac["strip_metres"] == A(17.00) and ac["rolls_to_buy"] == 3
    assert "LAYOUT_CHANGES_ROLLS" in a["flags"]
    # the opposite start wall of the same direction is the same layout mirrored: a tie, listed, quantities equal
    assert "TIE_SAME_ROLLS_AND_METRES" in a["flags"]
    assert a["tied_with"][0]["start"] == C.OPPOSITE
    check_identities(a)


def test_owner_3x3_picture_two_rolls_and_why_not_one():
    """3.00 x 3.00 m (the owner's picture). Either way: span 3.00 + 0.40 = 3.40 -> ceil(2.40 / 0.90) + 1 = 4 strips;
    the 4th 3.40 - 3 x 0.90 = 0.70 m wide; each 3.00 + 0.40 = 3.40 m = 13.60 m: two per roll -> 2 rolls, 6.40 m left;
    cut 3 x 3.40 + 0.70 x 3.40 = 12.58 m2, trim 0.30 x 3.40 = 1.02 m2. The picture's 1 roll (3 strips x 3.20 m)
    leaves out the upturn on all four walls and the laps (Q-24 addendum open point): the method gives 2."""
    a = C.plan(rect(3.0, 3.0), floor="X", room_id="B", group="WET_AREA")
    assert a["rolls_to_buy"] == 2 and a["selected"]["strips"] == 4
    assert a["strip_metres"] == A(13.60) and a["leftover_m"] == A(6.40)
    assert a["cut_m2"] == A(12.58) and a["side_trim_m2"] == A(1.02)
    assert {c["rolls_to_buy"] for c in a["candidates"]} == {2}
    assert "LAYOUT_CHANGES_ROLLS" not in a["flags"]
    check_identities(a)


# ------------------------------------------------------------------------------------------------ adversarial
def test_strip_over_ten_metres_is_spliced_and_tie_goes_to_shorter_metres():
    """12.00 x 1.50 m. Along: span 1.50 + 0.40 = 1.90 -> 2 strips of 1.00 m, each 12.00 + 0.40 = 12.40 m > 10 m:
    spliced with the 0.10 m end lap: pieces 10.00 + 2.50 (12.40 - 9.90). Pieces 10, 10, 2.5, 2.5 -> 3 rolls (2.50 +
    2.50 share one), 25.00 m, 5.00 m left; cut 25.00 m2 (the lap is membrane cut), trim 0. Across: span 12.40 ->
    ceil(11.40 / 0.90) + 1 = 14 strips of 1.50 + 0.40 = 1.90 m = 26.60 m; 5 per roll -> 3 rolls. Both 3 rolls: the
    tie goes to the shorter metres (Q-49 A): along, 25.00 < 26.60."""
    a = C.plan(rect(12.0, 1.5), floor="X", room_id="R", group="ROOF")
    s = a["selected"]
    assert s["direction"] == F.ALONG_LONG
    assert [p["length_m"] for p in s["strip_list"][0]["pieces"]] == [A(10.0), A(2.5)]
    assert a["rolls_to_buy"] == 3 and a["strip_metres"] == A(25.0) and a["leftover_m"] == A(5.0)
    assert a["cut_m2"] == A(25.0) and a["side_trim_m2"] == A(0.0)
    assert s["fold_v2_cut_m2"] == A(24.8)                   # fold V2's strip x length, without the splice lap
    ac = cand(a, F.ACROSS, C.LOWER)
    assert ac["strips"] == 14 and ac["strip_metres"] == A(26.6) and ac["rolls_to_buy"] == 3
    assert "STRIP_SPLICED_WITH_END_LAP" in a["flags"] and "LAYOUT_CHANGES_ROLLS" not in a["flags"]
    # each 10.00 m piece takes a roll of its own; the two 2.50 m pieces share the third
    assert sorted(r["used_m"] for r in s["rolls"]) == [A(5.0), A(10.0), A(10.0)]
    check_identities(a)


def test_l_shaped_room():
    """L: 4 x 2 m plus 2 x 2 m on its left half (outline 0,0 4,0 4,2 2,2 2,4 0,4), floor 12.00 m2. Along x (span
    4.00 + 0.40 -> 5 bands: floor 0-0.80, 0.80-1.70, 1.70-2.60, 2.60-3.50, 3.50-4.00; the last 0.80 m wide): bands
    1-3 reach the 4 m leg (band 3 crosses y = 2: one piece of sheet 0-4 m) -> 4.40 m; bands 4-5 the 2 m leg -> 2.40 m;
    18.00 m -> [4.40 + 4.40], [4.40 + 2.40 + 2.40] = 2 rolls, 2.00 m left; cut 3 x 4.40 + 2.40 + 0.80 x 2.40 = 17.52
    m2, trim 0.20 x 2.40 = 0.48. Started from the opposite wall the 0.80 m strip lies on the 4 m leg: trim 0.20 x 4.40
    = 0.88, the same rolls and metres (a tie, listed with its trim)."""
    a = C.plan([(0, 0), (4, 0), (4, 2), (2, 2), (2, 4), (0, 4)], floor="X", room_id="L", group="WET_AREA")
    assert a["floor_m2"] == A(12.0)
    s = a["selected"]
    assert sorted(x["length_m"] for x in s["strip_list"]) == [A(2.4), A(2.4), A(4.4), A(4.4), A(4.4)]
    assert a["rolls_to_buy"] == 2 and a["strip_metres"] == A(18.0) and a["leftover_m"] == A(2.0)
    assert a["cut_m2"] == A(17.52) and a["side_trim_m2"] == A(0.48)
    assert any(t["side_trim_m2"] == A(0.88) for t in a["tied_with"])
    assert a["upturn_shortfall_m2"] == A(0.0)
    check_identities(a)


@pytest.mark.parametrize("deg", [0.0, 30.0, 117.0])
@pytest.mark.parametrize("mirror", [False, True])
def test_rotation_mirror_and_millimetres_give_the_kitchen_numbers(deg, mirror):
    """the owner's kitchen drawn in mm (3000 x 4000), turned and mirrored: the same 2 rolls, 17.60 m, 2.40 m left,
    16.28 m2 cut (the plan is laid in the room's own frame)."""
    ring = rect(3000.0, 4000.0, 1250.0, -700.0)
    if mirror:
        ring = [(-x, y) for x, y in ring][::-1]
    a = C.plan(turn(ring, deg), unit_m=0.001, floor="X", room_id="K", group="WET_AREA")
    assert a["floor_m2"] == A(12.0, abs=1e-6)
    assert a["rolls_to_buy"] == 2 and a["strip_metres"] == A(17.6, abs=1e-4) and a["leftover_m"] == A(2.4, abs=1e-4)
    assert a["cut_m2"] == A(16.28, abs=1e-4)
    check_identities(a)


def test_roof_with_skylight_opening_gap_above_the_lower_bound():
    """roof 8.00 x 6.00 m with a 2.00 x 2.00 m skylight opening at x 3-5, y 2-4 (owner Q-29: an open area, 0.20 m
    upturn round it). Along x (span 6.40 -> 7 bands: 0-0.80, 0.80-1.70, 1.70-2.60, 2.60-3.50, 3.50-4.40, 4.40-5.30,
    5.30-6.00): bands 3 and 5 cross the opening edge and stay one piece of 8.00 + 0.40 = 8.40 m; band 4 (2.60-3.50)
    lies beside the opening: two pieces 3.00 + 0.40 = 3.40 m (gap 2.00 m > 2 x 0.20). Strips 6 x 8.40 + 2 x 3.40 =
    57.20 m. An 8.40 m piece leaves 1.60 m: no 3.40 m piece fits beside it -> 6 rolls + one for 3.40 + 3.40 = 7 rolls,
    12.80 m left. Lower bound ceil(57.20 / 10) = 6: the gap is a fact of whole pieces, proven by the exact search.
    Across (span 8.40 -> 10 bands + one 0.30 m upturn-only strip; 9 x 6.40 + 2 x 2.40 = 62.40 m): 9 rolls. Opening
    upturn: perimeter 8.00 lm x 0.20 = 1.60 m2."""
    a = C.plan(rect(8.0, 6.0), holes=[rect(2.0, 2.0, 3.0, 2.0)], floor="R", room_id="ROOF", group="ROOF")
    s = a["selected"]
    assert s["direction"] == F.ALONG_LONG
    assert sorted(x["length_m"] for x in pieces(a)) == [A(3.4)] * 2 + [A(8.4)] * 6
    assert a["rolls_to_buy"] == 7 and a["strip_metres"] == A(57.2) and a["leftover_m"] == A(12.8)
    assert s["lower_bound"] == 6 and s["proof_state"] == "PROVEN_BY_EXHAUSTIVE_SEARCH"
    assert "ROLLS_ABOVE_LOWER_BOUND" in a["flags"] and "GAP" in s["proof"]
    assert cand(a, F.ACROSS, C.LOWER)["rolls_to_buy"] == 9
    assert cand(a, F.ACROSS, C.LOWER)["strip_metres"] == A(62.4)
    o = a["opening_upturn"]
    assert o["openings"] == 1 and o["upturn_lm"] == A(8.0) and o["upturn_m2"] == A(1.6)
    assert o["folded_from_strips_m2"] + o["own_pieces_m2"] == A(1.6, abs=1e-4)
    assert o["own_pieces_in_roll_count"] is False
    check_identities(a)


def test_owner_inputs_change_the_plan_never_constants():
    """lap 0.15 m on the 3 x 4 kitchen (an input, UP-WP-002): along, bands 0.80 + 0.85 + 0.85 + rest; n =
    ceil((3.40 - 1.00) / 0.85) + 1 = 4; the 4th strip from -0.20 + 3 x 0.85 = 2.35 to 3.20 = 0.85 m wide; 4 x 4.40 m
    -> 2 rolls; cut 3 x 4.40 + 0.85 x 4.40 = 16.94 m2."""
    a = C.plan(rect(3.0, 4.0), spec={"lap_m": 0.15}, floor="X", room_id="K")
    assert a["rolls_to_buy"] == 2 and a["cut_m2"] == A(16.94)
    assert a["spec"]["lap_m"] == 0.15


# ------------------------------------------------------------------------------------------------ held, never 0
@pytest.mark.parametrize("poly,spec,reason", [
    (None, None, "NO_OUTLINE"),
    ([], None, "NO_OUTLINE"),
    ([(0, 0), (1, 0), (2, 0)], None, "OUTLINE_NOT_USABLE"),
    ([(0, 0), (2, 2), (2, 0), (0, 2)], None, "OUTLINE_NOT_USABLE"),         # a bow tie
    (rect(3, 4), {"lap_m": None}, "MISSING_INPUT_LAP_M"),
    (rect(3, 4), {"roll_length_m": 0}, "MISSING_INPUT_ROLL_LENGTH_M"),
    (rect(3, 4), {"lap_m": 1.0}, "LAP_NOT_SMALLER_THAN_ROLL"),
])
def test_missing_or_broken_input_is_held_never_zero(poly, spec, reason):
    a = C.plan(poly, spec=spec, floor="X", room_id="H")
    assert a["state"] == "HELD" and a["reason"].startswith(reason)
    for k in ("rolls_to_buy", "strip_metres", "leftover_m", "cut_m2", "side_trim_m2"):
        assert a[k] is None
    assert "HELD" in C.text_table(a) and "HELD" in C.svg(a)


def test_project_totals_are_sums_of_areas_alone_and_held_counted():
    """kitchen 3 x 4 (2 rolls, 17.60 m, 2.40 left) + 3 x 3 bath (2 rolls, 13.60 m, 6.40 left) as wet areas = 4 rolls,
    31.20 m, 8.80 m left (each alone: the 2.40 + 6.40 m left are NOT pooled, Q-49 A), one held wet area listed;
    the 12 x 1.5 roof alone 3 rolls."""
    rows = [C.plan(rect(3, 4), floor="GF", room_id="K"), C.plan(rect(3, 3), floor="GF", room_id="B"),
            C.held(floor="1F", room_id="Q", reason="WET_STATUS_HELD"),
            C.plan(rect(12, 1.5), floor="RF", room_id="R1", group="ROOF")]
    p = C.project(rows)
    w = p["groups"]["WET_AREA"]
    assert w["rolls_to_buy"] == 4 and w["strip_metres"] == A(31.2) and w["leftover_m"] == A(8.8)
    assert w["membrane_cut_m2"] == A(16.28 + 12.58) and w["held"] == 1 and w["complete"] is False
    assert w["held_rows"][0]["reason"] == "WET_STATUS_HELD"
    assert p["groups"]["ROOF"]["rolls_to_buy"] == 3
    assert p["all"]["rolls_to_buy"] == 7 and p["all"]["held"] == 1
    with pytest.raises(C.PlanError):
        C.project(rows + [C.plan(rect(3, 4), floor="GF", room_id="K")])
    with pytest.raises(C.PlanError):
        C.plan(rect(3, 4), group="BALCONY_GUESS")


def test_svg_is_well_formed_and_labels_every_piece():
    a = C.plan(rect(12.0, 1.5), floor="X", room_id="R", group="ROOF")
    root = ET.fromstring(C.svg(a))
    labels = [t.text for t in root.iter("{http://www.w3.org/2000/svg}text")][1:]
    assert len(labels) == len(pieces(a)) == 4
    assert sorted(labels) == ["S1.1 R1", "S1.2 R3", "S2.1 R2", "S2.2 R3"]


def test_text_table_lists_every_strip_roll_and_proof():
    a = C.plan(rect(3.0, 4.0), floor="GF", room_id="K", name="KITCHEN")
    t = C.text_table(a)
    assert len(re.findall(r"-> roll \d", t)) == 4 and "roll 1: used 8.80 m, leftover 1.20 m" in t
    assert "OPTIMAL: 2 roll(s) = lower bound ceil(17.60 m / 10.00 m) = 2" in t
    assert "rolls 2 | strip metres 17.60 | leftover 2.40 m | membrane cut 16.28 m2 | side trim 1.32 m2" in t
