"""T-191 POOL_STEEL_REV2 on hand-calculated synthetic pools (NOT Alsenan: a round-ended pool in mm, a rectangle, a
small D; other sizes, covers, bars).  Hand values are written out with explicit arithmetic below, not taken from the
module.  Regression guards (ENGINEERING_REASONING_STANDARD s.4 C), each with a normal and an adverse case:
  - a FINISHED water depth used as the RC wall height for the bar lengths (the rev1 / D-T183-1 error),
  - a held count range whose high end carries the low count (HIGH_FROM_COUNT_B),
  - '/m' and '/cm' read as anything but a maximum c/c spacing (exact division, closed loop vs open run),
  - an undimensioned bar leg turned into a number, a printed count re-counted, a held lap counted as 0 or as net.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S = _load("t191_pool_steel", "research/agents_t191/t191_pool_steel.py")
T183 = _load("t183_pool_rc_for_t191", "research/agents_t183/t183_pool_rc.py")

KG12, KG10, KG16 = 144 / 162, 100 / 162, 256 / 162

# Round-ended (stadium) pool, mm: half circles r 1500 joined by 4000 straight sides; walls 250, base 300;
# rim +0.40, structure line -1.10 -> wall 1.50; finished floor -1.04 (build-up 60).
STADIUM = {
    "unit": "mm",
    "outline": {"kind": "STADIUM", "r": 1500, "s": 4000},
    "wall_t": 250, "base_t": 300,
    "levels": {"rim": 400, "base_top_structural": -1100, "finished_floor": -1040, "floor_buildup": 60},
    "soil_cover": 70, "nonsoil_cover": 40, "main_dirs": ["x"], "lap_d_factors": [40, 70],
    "populations": {"P": {
        "WV_OUT": {"n_per_m": 5, "d": 12, "shape": "STRAIGHT"},
        "WV_IN": {"n_per_m": 5, "d": 12, "shape": "TOP_HOOK_BOTTOM_BOX"},
        "WH_OUT": {"s": 0.25, "d": 10}, "WH_IN": {"s": 0.25, "d": 10},
        "F_MAIN": {"n_per_m": 5, "d": 12}, "F_DIST": {"n_per_m": 4, "d": 10},
        "RIM": {"count": 2, "d": 16}}},
}


def approx(x, tol=1e-6):
    return pytest.approx(x, abs=tol)


def _stadium_P(r, s=4.0):
    return 2 * s + 2 * math.pi * r


def _rows(inp):
    g = S.load(inp)
    pop = inp["populations"]["P"]
    rows, held = S.population_rows(pop, g["outer"], g["wall_t"], g["base_t"], g["wall_h"], g["c_s"], g["c_n"],
                                   hoops="high", main_dir="x")
    return {r["mark"]: r for r in rows}, held, g


# ---------------------------------------------------------------- normal: the round-ended pool by hand

def test_stadium_wall_height_from_the_structure_line():
    g = S.load(STADIUM)
    assert g["wall_h"] == approx(1.50)          # 0.40 - (-1.10); the finished depth 1.44 is NOT the height


def test_stadium_outer_verticals_by_hand():
    rows, _, _ = _rows(STADIUM)
    P = _stadium_P(1.5 - (0.070 + 0.006))       # 8 + 2 pi 1.424 = 16.947256
    assert P == approx(16.947256, 1e-6)
    n = math.ceil(P / 0.2)                      # 84.74 -> 85 (closed loop: no '+1')
    assert n == 85 and rows["WV_OUT"]["count"] == 85
    v = 0.30 + 1.50 - 0.070 - 0.040 - 0.012     # 1.678
    assert rows["WV_OUT"]["length_m"] == approx(v)
    assert rows["WV_OUT"]["kg"] == approx(85 * 1.678 * KG12)          # 126.782...


def test_stadium_water_verticals_hook_and_box_by_hand():
    rows, _, _ = _rows(STADIUM)
    t_in = 0.25 - 0.040 - 0.006                  # 0.204
    P = _stadium_P(1.5 - t_in)                   # 16.142999
    assert rows["WV_IN"]["count"] == math.ceil(P / 0.2) == 81
    w = t_in - 0.076                             # 0.128 bar line to bar line
    box_h = 0.30 - 0.070 - 0.040 - 0.012         # 0.178
    L = 1.678 + w + 2 * w + box_h                # 2.240
    assert rows["WV_IN"]["length_m"] == approx(2.240)
    assert rows["WV_IN"]["length_m"] == approx(L)
    assert rows["WV_IN"]["kg"] == approx(81 * 2.240 * KG12)


def test_stadium_hoops_count_range_and_ring_lengths():
    rows, held, g = _rows(STADIUM)
    assert S.count_hoops(1.50, 0.25) == (6, 7)
    P_out = _stadium_P(1.5 - (0.070 + 0.012 + 0.005))        # 16.878141
    P_in = _stadium_P(1.5 - (0.25 - 0.040 - 0.012 - 0.005))  # 1.307 -> 16.212033
    assert rows["WH_OUT"]["count"] == 7 and rows["WH_OUT"]["m"] == approx(7 * P_out)
    assert rows["WH_IN"]["m"] == approx(7 * P_in)
    rows_lo, _ = S.population_rows(STADIUM["populations"]["P"], g["outer"], g["wall_t"], g["base_t"], g["wall_h"],
                                   g["c_s"], g["c_n"], hoops="low")
    lo = {r["mark"]: r for r in rows_lo}
    assert lo["WH_OUT"]["count"] == 6


def test_stadium_floor_mesh_edge_bars_by_hand():
    rows, _, _ = _rows(STADIUM)
    r = 1.5 - 0.082                               # bar ends inside the outer verticals: 0.070 + 0.012
    l_eff = 2 * r - 0.012                         # 2.824 across y, centre to centre
    n = math.ceil(l_eff * 5) + 1                  # ceil(14.12) + 1 = 16
    assert n == 16
    pos = [0.006 + k * l_eff / (n - 1) for k in range(n)]
    m = sum(4.0 + 2 * math.sqrt(max(r * r - (p - r) ** 2, 0.0)) for p in pos)
    assert rows["FB_MAIN_X"]["count"] == 16 and rows["FB_MAIN_X"]["m"] == approx(m)
    assert rows["FT_MAIN_X"]["m"] == approx(m)    # both mats
    l_eff_y = 4.0 + 2 * r - 0.010                 # dist bars along y, spread across x
    n_y = math.ceil(l_eff_y * 4) + 1
    assert rows["FB_DIST_Y"]["count"] == n_y == 29   # ceil(27.304) + 1


def test_stadium_rim_printed_count_never_recounted():
    rows, _, _ = _rows(STADIUM)
    assert rows["RIM"]["count"] == 2
    t0, t1 = 0.070 + 0.012 + 0.008, 0.25 - 0.040 - 0.012 - 0.008
    assert rows["RIM"]["m"] == approx(_stadium_P(1.5 - t0) + _stadium_P(1.5 - t1))


def test_stadium_held_lap_is_a_range_outside_the_net():
    led = S.ledger(STADIUM)
    p = led["populations"]["P"]
    lo, hi = p["laps_kg_range_procurement"]
    assert lo > 0 and hi > lo                     # held, never 0
    # hand: hoop ring 16.878 m > 12 m -> 2 pieces, 2 laps at 40 d = 0.40 m (and at 70 d = 0.70 m)
    assert S.ring_laps(16.878141, 0.40) == 2 and S.ring_laps(16.878141, 0.70) == 2
    assert S.ring_laps(11.0, 0.40) == 1           # a closed ring under the stock length still needs its closing lap
    assert S.ring_laps(11.7, 0.40) == 2           # 11.7 + 0.4 > 12
    net = sum(m["high"]["kg"] for m in p["marks"].values())
    assert net == approx(p["kg_high"], 0.02)      # laps not inside the net


# ---------------------------------------------------------------- adverse: finished depth as the wall height

def test_finished_depth_as_wall_height_is_refused():
    bad = dict(STADIUM, levels=None, wall_h=1440, finished_depth=1440, floor_buildup=60)
    with pytest.raises(S.PoolSteelError, match="FINISHED"):
        S.load(bad)


def test_finished_depth_alone_holds_the_population_never_zero():
    held = dict(STADIUM, levels={"rim": 400, "finished_floor": -1040})
    led = S.ledger(held)
    assert led["wall_h_m"] is None
    assert led["populations"]["P"]["kg"] is None and led["populations"]["P"]["status"] == "HELD"


def test_rev1_error_reproduced_and_measured():
    """the under-measure of the rev1 error on the verticals = count x build-up x kg/m"""
    g = S.load(STADIUM)
    pop = STADIUM["populations"]["P"]
    good, _ = S.population_rows(pop, g["outer"], g["wall_t"], g["base_t"], 1.50, g["c_s"], g["c_n"])
    bad, _ = S.population_rows(pop, g["outer"], g["wall_t"], g["base_t"], 1.44, g["c_s"], g["c_n"])
    gv = {r["mark"]: r for r in good}
    bv = {r["mark"]: r for r in bad}
    assert gv["WV_OUT"]["kg"] - bv["WV_OUT"]["kg"] == approx(85 * 0.06 * KG12)


def test_wall_height_and_levels_both_refused():
    with pytest.raises(S.PoolSteelError):
        S.load(dict(STADIUM, wall_h=1500))


# ---------------------------------------------------------------- adverse: count meaning and held items

def test_exact_division_closed_loop_and_open_run():
    assert S.count_closed_loop(14.0, 0.2) == 70          # not 71: a closed loop has no end bar
    assert S.count_open_run(3.0, 0.2) == 16              # k = 15 -> 16 (spacing exactly s)
    assert S.count_open_run(3.0001, 0.2) == 17
    with pytest.raises(S.PoolSteelError):
        S.count_open_run(0.0, 0.2)


def test_high_end_carries_high_counts():
    g = S.load(STADIUM)
    rg = S.population_range(STADIUM["populations"]["P"], g["outer"], g["wall_t"], g["base_t"], g["wall_h"],
                            g["c_s"], g["c_n"], main_dirs=("x",))
    assert rg["high"]["hoops"] == "high" and rg["low"]["hoops"] == "low"
    hi = {r["mark"]: r for r in rg["high"]["rows"]}
    lo = {r["mark"]: r for r in rg["low"]["rows"]}
    assert hi["WH_OUT"]["count"] == 7 and lo["WH_OUT"]["count"] == 6


def test_unprinted_nonsoil_cover_is_bounded_by_the_cage_fit():
    inp = dict(STADIUM, nonsoil_cover=None)
    g = S.load(inp)
    pop = inp["populations"]["P"]
    assert S.c_n_max(pop, 0.25, 0.07) == approx(0.25 - 0.07 - (0.012 + 0.010 + 0.010 + 0.012))   # 0.136
    rg = S.population_range(pop, g["outer"], g["wall_t"], g["base_t"], g["wall_h"], g["c_s"], None)
    assert {round(r["c_n"], 3) for r in rg["readings"]} == {0.0, 0.136}
    assert rg["low"]["kg"] < rg["high"]["kg"]
    with pytest.raises(S.PoolSteelError):
        S.population_rows(pop, g["outer"], 0.25, 0.30, 1.5, 0.07, 0.20)        # cage does not fit


def test_undimensioned_leg_is_held_not_measured():
    pop = dict(STADIUM["populations"]["P"], WV_OUT={"n_per_m": 5, "d": 12, "shape": "L_LEG_FLOOR_BOTTOM"})
    g = S.load(STADIUM)
    rows, held = S.population_rows(pop, g["outer"], g["wall_t"], g["base_t"], g["wall_h"], g["c_s"], g["c_n"])
    r = {x["mark"]: x for x in rows}
    assert r["WV_OUT"]["length_m"] == approx(1.678)       # vertical only; leg not added
    leg = [h for h in held if h["mark"] == "WV_OUT_LEG"][0]
    assert leg["status"] == "HELD_LENGTH" and leg["count"] == 85
    assert leg["drawn_minimum_m_each"] == approx(0.204 - 0.076)


def test_missing_soil_cover_and_unknown_shape_refused():
    with pytest.raises(S.PoolSteelError):
        S.ledger(dict(STADIUM, soil_cover=None))
    pop = dict(STADIUM["populations"]["P"], WV_IN={"n_per_m": 5, "d": 12, "shape": "SPIRAL"})
    g = S.load(STADIUM)
    with pytest.raises(S.PoolSteelError):
        S.population_rows(pop, g["outer"], g["wall_t"], g["base_t"], g["wall_h"], g["c_s"], g["c_n"])


# ---------------------------------------------------------------- invariance: units, rotation, mirror

def _total(inp):
    return S.ledger(inp)["populations"]["P"]["kg_high"]


def test_units_mm_cm_m_identical():
    cm = dict(STADIUM, unit="cm", outline={"kind": "STADIUM", "r": 150, "s": 400}, wall_t=25, base_t=30,
              levels={"rim": 40, "base_top_structural": -110, "finished_floor": -104, "floor_buildup": 6},
              soil_cover=7, nonsoil_cover=4)
    m = dict(STADIUM, unit="m", outline={"kind": "STADIUM", "r": 1.5, "s": 4.0}, wall_t=0.25, base_t=0.30,
             levels={"rim": 0.40, "base_top_structural": -1.10, "finished_floor": -1.04, "floor_buildup": 0.06},
             soil_cover=0.07, nonsoil_cover=0.04)
    assert _total(cm) == approx(_total(STADIUM), 0.01) and _total(m) == approx(_total(STADIUM), 0.01)


def test_rect_rotation_90_with_both_directions_carried():
    base = dict(STADIUM, outline={"kind": "RECT", "a": 5000, "b": 3000}, main_dirs=["x", "y"])
    rot = dict(base, outline={"kind": "RECT", "a": 3000, "b": 5000})
    lb, lr = S.ledger(base)["populations"]["P"], S.ledger(rot)["populations"]["P"]
    assert lb["kg_low"] == approx(lr["kg_low"], 0.01) and lb["kg_high"] == approx(lr["kg_high"], 0.01)


def test_rect_by_hand_walls():
    rect = dict(STADIUM, outline={"kind": "RECT", "a": 5000, "b": 3000})
    rows, _, _ = _rows(rect)
    P = 2 * (5.0 - 2 * 0.076) + 2 * (3.0 - 2 * 0.076)     # 9.696 + 5.696 = 15.392
    assert rows["WV_OUT"]["count"] == math.ceil(P / 0.2) == 77   # 76.96 -> 77


def test_d_outline_matches_t183_geometry_and_is_mirror_free():
    o = S.Outline("D", r=2.0, b=1.2)
    t = T183.Outline("D", r=2.0, b=1.2)
    assert o.area() == approx(t.area()) and o.perimeter() == approx(t.perimeter())
    for p in (0.3, 1.0, 2.5, 3.1):
        assert o.chord("x", p) == approx(t._chord("along_back", p))
    for p in (0.2, 1.7, 3.9):
        assert o.chord("y", p) == approx(t._chord("across_back", p))
    # inward offset of a D: perimeter drops by (4 + pi) t (two straight sides, the back and the arc)
    assert o.offset(0.1).perimeter() == approx(o.perimeter() - (4 + math.pi) * 0.1)
    # mirror about the axis: chords symmetric about x = r
    assert o.chord("y", 2.0 - 0.7) == approx(o.chord("y", 2.0 + 0.7))
