"""T-104: MEMBRANE_FOLD_V4, the owner's strip method laid in every wall frame of an area (owner Q-49 A: fewest rolls,
tie: shorter strip metres). Synthetic, hand-calculated outlines only (none is the development villa). Roll 1.00 x 10.00 m,
lap 0.10 m, upturn 0.20 m (UP-WP-001 / 002 / 003). Bands across a span S (MEMBRANE_FOLD_V2._bands): n = ceil((S + 0.40 -
1.00) / 0.90) + 1; band k's floor is [0, 0.80] for k = 0, then [0.90 k - 0.10, 0.90 k + 0.80]; the last band is cut to
the remaining floor + lap + upturn; a strip is the floor's extent across its band + 0.20 + 0.20.

KITCHEN (owner's Q-30 example) 4.00 x 3.00: one wall frame; along: 4 strips 1.00 / 1.00 / 1.00 / 0.70 x 4.40 = 17.60 m,
2 rolls; across: 5 x 3.40 = 17.00 m, 3 rolls. V4 = V3: 2 rolls, 17.60 m.

WEDGE (0,0) (2.40,0) (0.60,1.80) (0,1.80): a W.C. whose longest wall is the 45 degree wall (1.80 x sqrt 2 = 2.546 m >
2.40), so V3 lays strips only parallel / square to it.
  V3's best (strips parallel to the 45 degree wall, first strip on it): span = 2.40 / sqrt 2 = 1.6971 m -> 3 bands.
  A line at distance t from the wall is x + y = c, c = 2.40 - t sqrt 2; its extent along the wall is the range of
  u = (x - y) / sqrt 2 over the slab. Band 0 (t 0..0.80, c 1.2686..2.40): u from (1.80 - 3.60) / sqrt 2 = -1.2728 to
  2.40 / sqrt 2 = 1.6971 -> 2.9698 + 0.40 = 3.3698 m. Band 1 (t 0.80..1.6971, c 0..1.2686): 1.2686 sqrt 2 = 1.7941 + 0.40
  = 2.1941 m. Band 2 (upturn-only at the far corner, 0.2971 wide): 0.1941 + 0.40 = 0.5941 m. Sum 6.1581 m, 1 roll.
  V4's best (frame of the 2.40 m wall, strips square to it, first strip on the 1.80 m wall at x = 0): span 2.40 ->
  3 bands; the height is 1.80 for x <= 0.60 and 2.40 - x beyond: band 0 (x 0..0.80) 1.80 + 0.40 = 2.20; band 1
  (x 0.80..1.70) 1.60 + 0.40 = 2.00; band 2 (x 1.70..2.40, 1.00 wide) 0.70 + 0.40 = 1.10. Sum 5.30 m, 1 roll:
  0.8581 m less strip, same roll (the Alsenan wedge W.C. case of T-098, other sizes).
  Patches of the V4 layout: 2 corner triangles where a band boundary meets the 45 degree wall (legs (sqrt 2 - 1) x
  0.20 = 0.0828 m, 0.0034 m2 each) and the mitred acute (45 degree) corner beyond the last strip (legs 0.2828 m,
  0.04 m2).

TRAP (0,0) (3.50,0) (1.00,2.50) (0,2.50): longest wall the 45 degree one (2.50 sqrt 2 = 3.536 m > 3.50).
  V3: every layout over 10 m (best, strips parallel to the 45 degree wall from it: span 3.50 / sqrt 2 = 2.4749 m, 4
  bands: c in [2.3686, 3.50]: u from -2.50 / sqrt 2 to 3.50 / sqrt 2 -> 4.2426 + 0.40 = 4.6426; c in [1.0958, 2.3686]:
  2.3686 sqrt 2 + 0.40 = 3.7497; c in [0, 1.0958]: 1.5497 + 0.40 = 1.9497; the upturn-only strip 0.402; 10.7441 m) ->
  2 rolls under every reading of owner Q-58.
  V4 (frame of the 3.50 m wall, strips square to it, first strip on the 2.50 m wall): span 3.50 -> 5 bands; height 2.50
  for x <= 1.00, 3.50 - x beyond: 2.50 + 0.40 = 2.90, 2.90, (3.50 - 1.70) + 0.40 = 2.20, (3.50 - 2.60) + 0.40 = 1.30,
  the 0.30 m upturn-only strip at the far corner 0.10 + 0.40 = 0.50: 9.80 m. Patches 0.2828 + 0.0828 + 0.0828 m long.
  Q-58 A (patches from this area's own side trim: the 0.30 strip leaves 0.70 x 0.50) and C (patches by detail): 9.80 m
  in 1 roll; Q-58 B (every piece from a roll): 9.80 + 0.4485 = 10.2485 m > 10 -> 2 rolls. So V4 changes the count
  (2 -> 1 under A and C): HELD_Q58 with low 1 / high 2, never 0, flagged ANOTHER_WALL_FRAME_CHANGES_ROLLS.

V3 TAIL DEFECT (found by T-104): in the WEDGE's own V3 frame, the layout parallel to the 45 degree wall started from the
opposite corner has strips 2.00 + 3.3698 + 3.0426 = 8.4125 m and a 0.04 m2 corner triangle (0.2828 x 0.2828); V3 reads
that triangle's size from a residual carrying a 5e-17 m wide tail along a sheet edge, 3.08 m long, so it counts 2 rolls
under Q-58 A / B. Measured on the cleaned piece: 8.4125 + 0.2828 + 2 x 0.1172 = 8.93 m -> 1 roll under every reading."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import membrane_cutting_plan_v2 as CP      # noqa: E402
from engine.source import membrane_fold_v2 as F2              # noqa: E402
from engine.source import membrane_fold_v3 as F3              # noqa: E402
from engine.source import membrane_fold_v4 as F4              # noqa: E402

KITCHEN = [(0, 0), (4, 0), (4, 3), (0, 3)]
WEDGE = [(0, 0), (2.4, 0), (0.6, 1.8), (0, 1.8)]
TRAP = [(0, 0), (3.5, 0), (1.0, 2.5), (0, 2.5)]
S2 = math.sqrt(2.0)


def _xf(pts, *, scale=1.0, mirror=False, deg=0.0, shift=(0.0, 0.0), roll=0):
    a = math.radians(deg)
    out = []
    for x, y in pts:
        if mirror:
            x = -x
        x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        out.append(((x + shift[0]) * scale, (y + shift[1]) * scale))
    out = out[roll:] + out[:roll]
    return out[::-1] if mirror else out


def _strips(f, i):
    return [(s["width_m"], s["length_m"]) for s in f["layouts_v4"][i]["strips"]]


def _public(lay):
    drop = {"index", "frame", "frame_deg", "strips_run_deg", "longest_wall_frame", "name", "patch_sizes_cleaned",
            "patches", "_sheets"}
    return {k: v for k, v in lay.items() if k not in drop}


# ------------------------------------------------------------------------------------------------ frames
def test_frames_kitchen_one_wedge_two_longest_first():
    fk = F4.fold(KITCHEN)
    assert [x["frame_deg"] for x in fk["frames_v4"]] == [0.0]
    assert len(fk["layouts_v4"]) == 4
    fw = F4.fold(WEDGE)
    fr = fw["frames_v4"]
    assert [x["frame_deg"] for x in fr] == [135.0, 0.0]
    assert fr[0]["is_longest_wall_frame"] and fr[0]["frame_deg"] == pytest.approx(F2.room_frame(WEDGE))
    assert fr[0]["longest_edge_m"] == pytest.approx(1.8 * S2, abs=1e-4)
    assert fr[1]["walls_lm"] == pytest.approx(2.4 + 1.8 + 0.6, abs=1e-4)
    assert len(fw["layouts_v4"]) == 8


@pytest.mark.parametrize("pts", [KITCHEN, TRAP, [(0, 0), (6, 0), (6, 2), (2, 2), (2, 4), (0, 4)]])
def test_first_four_layouts_are_v3s_where_no_patch_tail(pts):
    f = F4.fold(pts)
    for a, b in zip(f["layouts_v4"][:4], f["layouts_v3"]):
        assert a["patch_sizes_cleaned"] == 0
        assert _public(a) == {k: v for k, v in b.items() if k not in ("patches", "_sheets")}
        assert [(q["kind"], q["m2"], q["along_m"], q["across_m"]) for q in a["patches"]] == \
            [(q["kind"], q["m2"], q["along_m"], q["across_m"]) for q in b["patches"]]


# ------------------------------------------------------------------------------------------------ hand fixtures
def test_kitchen_unchanged():
    f = F4.fold(KITCHEN)
    c = f["choice_v4"]
    assert c["state"] == "RELEASED" and c["rolls"] == 2 and c["strip_metres"] == pytest.approx(17.60)
    assert _strips(f, c["layout"]) == [(1.0, 4.4), (1.0, 4.4), (1.0, 4.4), (0.7, 4.4)]
    assert f["layouts_v4"][2]["strip_metres"] == pytest.approx(17.00) and f["layouts_v4"][2]["rolls_by_basis"] == \
        {"Q58_A": 3, "Q58_B": 3, "Q58_C": 3}
    assert c["saves_vs_v3"] == {"strip_m": 0.0, "rolls_by_reading": {"Q58_A": 0, "Q58_B": 0, "Q58_C": 0}}
    assert "ANOTHER_WALL_FRAME_CHOSEN" not in f["flags_v4"]


def test_wedge_v3_best_by_hand():
    f = F4.fold(WEDGE)
    v3 = f["choice_v4"]["v3_choice"]
    assert v3["layout"] == 0 and v3["strip_metres"] == pytest.approx(6.1581, abs=1e-4)
    got = _strips(f, 0)
    assert got[0][1] == pytest.approx(2.4 / S2 + 1.8 / S2 + 0.4, abs=1e-4)               # u -1.2728 .. 1.6971
    assert got[1][1] == pytest.approx((2.4 - 0.8 * S2) * S2 + 0.4, abs=1e-4)          # 2.1941
    assert got[2][0] == pytest.approx(2.4 / S2 + 0.2 - 1.6, abs=1e-5)                    # 0.2971 wide
    assert got[2][1] == pytest.approx((2.4 - 1.6 * S2) * S2 + 0.4, abs=1e-3)             # 0.5941
    assert v3["rolls_by_reading"] == {"Q58_A": 1, "Q58_B": 1, "Q58_C": 1}


def test_wedge_v4_square_to_the_short_wall_saves_metres_not_rolls():
    f = F4.fold(WEDGE)
    c = f["choice_v4"]
    assert c["state"] == "RELEASED" and c["rolls"] == 1
    assert c["frame_deg"] == 0.0 and c["strips_run_deg"] == 90.0 and c["start"] == F4.LOWER
    assert _strips(f, c["layout"]) == [(1.0, 2.2), (1.0, 2.0), (1.0, 1.1)]
    assert c["strip_metres"] == pytest.approx(5.30)
    assert c["saves_vs_v3"]["strip_m"] == pytest.approx(0.8581, abs=1e-4)
    assert c["saves_vs_v3"]["rolls_by_reading"] == {"Q58_A": 0, "Q58_B": 0, "Q58_C": 0}
    assert "ANOTHER_WALL_FRAME_CHOSEN" in f["flags_v4"] and "ANOTHER_WALL_FRAME_CHANGES_ROLLS" not in f["flags_v4"]
    tri = sorted((q["m2"], q["sides_m"]) for q in f["layouts_v4"][c["layout"]]["patches"])
    leg = (S2 - 1) * 0.2
    assert [x[0] for x in tri] == [pytest.approx(leg * leg / 2, abs=1e-6)] * 2 + [pytest.approx(0.04, abs=1e-6)]
    assert tri[0][1][:2] == (pytest.approx(leg, abs=1e-4),) * 2
    assert tri[2][1][:2] == (pytest.approx(0.2 * S2, abs=1e-4),) * 2
    assert all(q["shape"] == F4.CORNER_TRIANGLE for q in f["layouts_v4"][c["layout"]]["patches"])
    assert "CORNER_TRIANGLES_IN_CHOSEN_LAYOUT" in f["flags_v4"]


def test_trap_another_frame_changes_rolls_held_under_q58():
    f = F4.fold(TRAP)
    c = f["choice_v4"]
    v3 = c["v3_choice"]
    assert v3["strip_metres"] == pytest.approx(10.7441, abs=1e-4)
    assert _strips(f, 0) == [(1.0, 4.642641), (1.0, 3.749747), (1.0, 1.949747), (0.174874, 0.402)]
    assert (3.5 + 2.5) / S2 + 0.4 == pytest.approx(4.642641, abs=1e-5)                  # band 0 by hand
    assert (3.5 - 0.8 * S2) * S2 + 0.4 == pytest.approx(3.749747, abs=1e-5)             # band 1
    assert (3.5 - 1.7 * S2) * S2 + 0.4 == pytest.approx(1.949747, abs=1e-5)             # band 2
    assert v3["rolls_by_reading"] == {"Q58_A": 2, "Q58_B": 2, "Q58_C": 2}
    assert min(x["strip_metres"] for x in f["layouts_v4"][:4]) > 10.0                   # every V3 layout over a roll
    assert c["frame_deg"] == 0.0 and c["strips_run_deg"] == 90.0
    assert _strips(f, c["layout"]) == [(1.0, 2.9), (1.0, 2.9), (1.0, 2.2), (1.0, 1.3), (0.3, 0.5)]
    assert c["strip_metres"] == pytest.approx(9.80)
    rd = {b: x["rolls"] for b, x in c["by_reading"].items()}
    assert rd == {"Q58_A": 1, "Q58_B": 2, "Q58_C": 1}
    lay = f["layouts_v4"][c["layout"]]
    assert sorted(q["along_m"] for q in lay["patches"]) == [pytest.approx((S2 - 1) * 0.2, abs=1e-5)] * 2 + \
        [pytest.approx(0.2 * S2, abs=1e-5)]
    assert 0.2 * S2 + 2 * (S2 - 1) * 0.2 == pytest.approx(0.448528, abs=1e-5)
    assert 9.80 + 0.448528 > 10.0
    assert c["state"] == "HELD_Q58" and c["rolls"] is None and c["rolls_bounded"] == {"low": 1, "high": 2}
    assert "ANOTHER_WALL_FRAME_CHANGES_ROLLS" in f["flags_v4"] and "CHOSEN_ROLLS_DEPEND_ON_Q58" in f["flags_v4"]
    p = F4.purchase(f)
    assert p["state"] == "HELD_Q58" and p["rolls"] is None and p["leftover_m"] is None
    assert p["cutting_plan_q58_a"]["rolls"] == 1 and len(p["cutting_plan"]) == 2


def test_v3_tail_defect_corrected_in_its_own_frame():
    f = F4.fold(WEDGE)
    old = f["layouts_v3"][1]
    new = f["layouts_v4"][1]
    assert old["strip_metres"] == new["strip_metres"] == pytest.approx(2.0 + 3.369848 + 3.042641, abs=1e-4)
    big = [q for q in old["patches"] if q["m2"] == pytest.approx(0.04, abs=1e-6)][0]
    assert big["along_m"] > 3.0                                         # the defect: a 0.04 m2 triangle 3.08 m long
    assert old["rolls_by_basis"] == {"Q58_A": 2, "Q58_B": 2, "Q58_C": 1}
    fixed = [q for q in new["patches"] if q["m2"] == pytest.approx(0.04, abs=1e-6)][0]
    assert fixed["along_m"] == pytest.approx(0.2 * S2, abs=1e-5) and fixed["across_m"] == pytest.approx(0.2 * S2, abs=1e-5)
    assert new["rolls_by_basis"] == {"Q58_A": 1, "Q58_B": 1, "Q58_C": 1}
    assert new["patch_sizes_cleaned"] >= 1
    assert sum(q["m2"] for q in new["patches"]) == pytest.approx(sum(q["m2"] for q in old["patches"]), abs=1e-6)
    assert "V3_COUNT_CORRECTED_IN_ITS_OWN_FRAME" in f["flags_v4"]


# ------------------------------------------------------------------------------------------------ adversarial
@pytest.mark.parametrize("name,pts", [("kitchen", KITCHEN), ("wedge", WEDGE), ("trap", TRAP)])
@pytest.mark.parametrize("kw", [dict(scale=1000.0), dict(mirror=True), dict(deg=30.0, shift=(12.5, -7.25)),
                                dict(deg=-63.0, mirror=True, scale=1000.0, roll=2), dict(roll=1)])
def test_choice_invariant_to_units_mirror_rotation_start_vertex(name, pts, kw):
    unit = 0.001 if kw.get("scale") == 1000.0 else 1.0
    a = F4.fold(pts)["choice_v4"]
    b = F4.fold(_xf(pts, **kw), unit_m=unit)["choice_v4"]
    assert b["state"] == a["state"] and b["rolls"] == a["rolls"] and b["rolls_bounded"] == a["rolls_bounded"]
    assert {k: x["rolls"] for k, x in b["by_reading"].items()} == {k: x["rolls"] for k, x in a["by_reading"].items()}
    assert b["strip_metres"] == pytest.approx(a["strip_metres"], abs=2e-3)
    assert b["v3_choice"]["strip_metres"] == pytest.approx(a["v3_choice"]["strip_metres"], abs=2e-3)


@pytest.mark.parametrize("pts,holes", [(KITCHEN, ()), (WEDGE, ()), (TRAP, ()),
                                       ([(0, 0), (4, 0), (4, 3), (0, 3)],
                                        [[(2.0, 1.2), (2.25, 1.45), (2.0, 1.7), (1.75, 1.45)]]),
                                       ([(0, 0), (5, 0), (5, 1.2), (3.8, 2.4), (0, 2.4)], ())])
def test_never_worse_than_v3_and_plan_repacks(pts, holes):
    f = F4.fold(pts, holes=holes)
    p3 = CP.purchase(f)
    c = f["choice_v4"]
    for b in F4.BASES:
        assert c["by_reading"][b]["rolls"] <= p3["rolls_by_reading"][b]["rolls"]
    if c["by_reading"]["Q58_B"]["rolls"] == p3["rolls_by_reading"]["Q58_B"]["rolls"]:
        assert c["by_reading"]["Q58_B"]["strip_metres"] <= p3["strip_length_m"] + 1e-9
    p = F4.purchase(f)                                     # re-packs the cutting plan and checks the count
    assert p["residual_after_m2"] == 0.0
    if p["state"] == "RELEASED":
        assert len(p["cutting_plan"]) == p["rolls"] and p["leftover_m"] >= 0


def test_hole_edges_are_frames():
    f = F4.fold([(0, 0), (4, 0), (4, 3), (0, 3)], holes=[[(2.0, 1.2), (2.25, 1.45), (2.0, 1.7), (1.75, 1.45)]])
    assert sorted(x["frame_deg"] for x in f["frames_v4"]) == [0.0, 45.0]
    assert any(q["kind"] == F3.PATCH_OPENING for x in f["layouts_v4"] for q in x["patches"]) or \
        all(x["residual_after_m2"] == 0.0 for x in f["layouts_v4"])


# ------------------------------------------------------------------------------------------------ held, never 0
@pytest.mark.parametrize("args,reason", [
    (dict(polygon=None), "NO_OUTLINE"),
    (dict(polygon=KITCHEN, spec={"lap_m": None}), "MISSING_INPUT_LAP_M"),
    (dict(polygon=KITCHEN, spec={"lap_m": 1.5}), "LAP_NOT_SMALLER_THAN_ROLL"),
    (dict(polygon=[(0, 0), (1, 0), (2, 0)]), "OUTLINE_NOT_USABLE"),
    (dict(polygon=[(0, 0), (2, 2), (2, 0), (0, 2)]), "OUTLINE_NOT_USABLE")])
def test_held_never_zero(args, reason):
    r = F4.plan(**args, floor="F", room_id="R")
    assert r["state"] == "HELD" and r["purchase"] is None and r["reason"].startswith(reason)


def test_plan_released_row_and_policy():
    r = F4.plan(WEDGE, floor="GF", room_id="W1", name="W.C.")
    p = r["purchase"]
    assert r["state"] == "COMPUTED" and p["state"] == "RELEASED" and p["rolls"] == 1
    assert p["strip_length_m"] == pytest.approx(5.30) and p["leftover_m"] == pytest.approx(10.0 - 5.30 - 0.448528,
                                                                                            abs=1e-4)
    assert p["saves_vs_v3"]["strip_m"] == pytest.approx(0.8581, abs=1e-4)
    pol = F4.policy_record()
    assert pol["method"] == "MEMBRANE_FOLD_V4" and "opt-in" in pol["replaces_nothing"]
