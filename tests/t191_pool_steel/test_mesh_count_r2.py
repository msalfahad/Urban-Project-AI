"""T-191 r2 (D-T191-2): an open '/m' mesh carries the count RANGE A (density, ceil(n x L_eff)) .. B (maximum c/c
spacing, ceil(L_eff / s) + 1) until the element's OWN evidence fixes the meaning; a closed loop is unaffected.
The footing meaning (T-171: maximum spacing) is never carried to a pool base by default (ERS s.3).

Hand values are written out below (synthetic pools, NOT Alsenan), plus one regression on the committed Alsenan
input (printed dimensions only) for the low / high ends the checker re-counted.
Adverse cases: an open mesh where A != B (the low end must take A, the high end B), an exact division (A and B still
differ by the edge bar), a meaning fixed without evidence (refused), an unknown meaning (refused).
"""

from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t191_pool_steel_r2", ROOT / "research/agents_t191/t191_pool_steel.py")
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

KG12, KG10 = 144 / 162, 100 / 162

# round-ended pool in mm (same as test_pool_steel.STADIUM; restated so this file stands alone)
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

# rectangle in m: 4.00 x 3.00 outer, soil cover 0.05, verticals d12 -> bar-end outline 3.876 x 2.876
RECT = {
    "unit": "m",
    "outline": {"kind": "RECT", "a": 4.0, "b": 3.0},
    "wall_t": 0.20, "base_t": 0.30, "wall_h": 1.20,
    "soil_cover": 0.05, "nonsoil_cover": 0.03, "main_dirs": ["x"],
    "populations": {"P": {"WV_OUT": {"n_per_m": 5, "d": 12}, "F_MAIN": {"n_per_m": 5, "d": 12}}},
}


def approx(x, tol=1e-6):
    return pytest.approx(x, abs=tol)


def _rows(inp, **kw):
    g = S.load(inp)
    rows, _ = S.population_rows(inp["populations"]["P"], g["outer"], g["wall_t"], g["base_t"], g["wall_h"],
                                g["c_s"], g["c_n"], main_dir="x", **kw)
    return {r["mark"]: r for r in rows}


def _stadium_chords(n):
    r = 1.5 - 0.082                      # bar-end outline: 0.070 soil cover + 0.012 outer vertical
    l_eff = 2 * r - 0.012                # 2.824 centre to centre across y
    pos = [0.006 + k * l_eff / (n - 1) for k in range(n)]
    return sum(4.0 + 2 * math.sqrt(max(r * r - (p - r) ** 2, 0.0)) for p in pos)


# ---------------------------------------------------------------- normal: counts by hand

def test_open_mesh_density_and_max_spacing_counts_differ():
    # stadium main bars: 5 x 2.824 = 14.12 -> A 15 (density); ceil(14.12) + 1 = 16 (max spacing)
    assert S.count_mesh(2.824, 1 / 5) == (15, 16)
    a, b = _rows(STADIUM, mesh_count="A"), _rows(STADIUM, mesh_count="B")
    assert a["FB_MAIN_X"]["count"] == 15 and b["FB_MAIN_X"]["count"] == 16
    assert a["FB_MAIN_X"]["m"] == approx(_stadium_chords(15))
    assert b["FB_MAIN_X"]["m"] == approx(_stadium_chords(16))
    assert a["FT_MAIN_X"]["m"] == approx(a["FB_MAIN_X"]["m"])          # both mats take the same reading
    # dist bars d10 along y across x: l_eff = 4.0 + 2 x 1.418 - 0.010 = 6.826; 4 x 6.826 = 27.304 -> 28 .. 29
    assert a["FB_DIST_Y"]["count"] == 28 and b["FB_DIST_Y"]["count"] == 29
    assert a["FB_MAIN_X"]["status"] == "HELD_COUNT_RANGE"


def test_rectangle_mesh_by_hand():
    # across y: 2.876 - 0.012 = 2.864; 5 x 2.864 = 14.32 -> A 15, B 16; every chord = 3.876 m
    a, b = _rows(RECT, mesh_count="A"), _rows(RECT, mesh_count="B")
    assert a["FB_MAIN_X"]["count"] == 15 and a["FB_MAIN_X"]["m"] == approx(15 * 3.876)
    assert b["FB_MAIN_X"]["count"] == 16 and b["FB_MAIN_X"]["m"] == approx(16 * 3.876)
    assert b["FB_MAIN_X"]["kg"] - a["FB_MAIN_X"]["kg"] == approx(3.876 * KG12)   # one bar per mat


def test_closed_loop_both_meanings_agree():
    # outer verticals of the rectangle at 0.056 in: P = 2 (3.888 + 2.888) = 13.552; ceil(5 x 13.552 = 67.76) = 68
    P = 2 * ((4.0 - 2 * 0.056) + (3.0 - 2 * 0.056))
    assert S.count_closed_loop(P, 1 / 5) == math.ceil(5 * P) == 68
    assert _rows(RECT, mesh_count="A")["WV_OUT"]["count"] == _rows(RECT, mesh_count="B")["WV_OUT"]["count"] == 68


def test_density_on_the_bar_end_extent_lies_inside_the_range():
    # E = L_eff + d; n d < 1, so ceil(n E) is A or B, never outside
    for l_eff, n, d in ((2.824, 5, 0.012), (3.318, 7, 0.014), (2.990, 5, 0.012), (3.000, 5, 0.012)):
        a, b = S.count_mesh(l_eff, 1 / n)
        assert a <= math.ceil(round(n * (l_eff + d), 9)) <= b


def test_ledger_low_end_on_a_high_end_on_b():
    led = S.ledger(STADIUM)["populations"]["P"]
    assert led["low_reading"]["mesh_count"] == "A" and led["high_reading"]["mesh_count"] == "B"
    assert led["low_reading"]["hoops"] == "low" and led["high_reading"]["hoops"] == "high"
    g = S.load(STADIUM)
    rows, _ = S.population_rows(STADIUM["populations"]["P"], g["outer"], g["wall_t"], g["base_t"], g["wall_h"],
                                g["c_s"], g["c_n"], hoops="low", main_dir="x", mesh_count="A")
    assert led["kg_low"] == approx(round(sum(r["kg"] for r in rows), 2), 0.005)
    assert led["marks"]["FB_MAIN_X"]["low"]["count"] == 15 and led["marks"]["FB_MAIN_X"]["high"]["count"] == 16
    assert "A density .. B max spacing" in led["status"]


# ---------------------------------------------------------------- adverse

def test_exact_division_still_carries_the_edge_bar_range():
    # L_eff 3.000 at 5/m: density 15 bars, max spacing 15 + 1 = 16 (the '+1' is the meaning, not rounding)
    assert S.count_mesh(3.0, 0.2) == (15, 16)


def test_footing_meaning_not_carried_without_this_elements_evidence():
    inp = copy.deepcopy(STADIUM)
    inp["mesh_count_meaning"] = "MAX_SPACING"                      # e.g. borrowed from the footings (T-171)
    with pytest.raises(S.PoolSteelError):
        S.load(inp)
    inp["mesh_count_evidence"] = "   "
    with pytest.raises(S.PoolSteelError):
        S.load(inp)
    inp["mesh_count_meaning"] = "SOMETHING"
    inp["mesh_count_evidence"] = "x"
    with pytest.raises(S.PoolSteelError):
        S.load(inp)


def test_meaning_fixed_by_cited_evidence_gives_one_count():
    inp = copy.deepcopy(STADIUM)
    inp["mesh_count_meaning"] = "MAX_SPACING"
    inp["mesh_count_evidence"] = "synthetic: base plan dimensions an edge bar 50 mm from each wall face"
    led = S.ledger(inp)["populations"]["P"]
    assert led["low_reading"]["mesh_count"] == led["high_reading"]["mesh_count"] == "B"
    assert led["marks"]["FB_MAIN_X"]["low"]["count"] == led["marks"]["FB_MAIN_X"]["high"]["count"] == 16
    inp["mesh_count_meaning"] = "DENSITY"
    led = S.ledger(inp)["populations"]["P"]
    assert led["marks"]["FB_MAIN_X"]["low"]["count"] == led["marks"]["FB_MAIN_X"]["high"]["count"] == 15


def test_unknown_mesh_count_refused():
    with pytest.raises(S.PoolSteelError):
        _rows(STADIUM, mesh_count="C")


# ---------------------------------------------------------------- regression on the committed (printed-only) input

def test_alsenan_input_low_end_on_count_a():
    inp = json.load(open(ROOT / "research/agents_t191/ALSENAN_POOL_STEEL_INPUT.json", encoding="utf-8"))
    led = S.ledger(inp)["populations"]
    r1, r2 = led["R1_deep_end_detail"], led["R2_shallow_end_detail"]
    # r1 handed in 839.34 / 583.08 on count B alone; the base mats on A take 2 x (3.611 + 3.614) / 2 x 2 x 2.658 kg off
    assert r1["kg_low"] == approx(824.89, 0.006) and r1["kg_high"] == approx(883.59, 0.006)
    assert r2["kg_low"] == approx(572.45, 0.006) and r2["kg_high"] == approx(617.96, 0.006)
    m = r1["marks"]["FB_MAIN_X"]
    assert (m["low"]["count"], m["high"]["count"]) == (24, 25)        # 7 x 3.318 = 23.23 -> 24; + 1 = 25
    assert (r1["marks"]["FB_DIST_Y"]["low"]["count"], r1["marks"]["FB_DIST_Y"]["high"]["count"]) == (20, 21)
