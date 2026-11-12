"""T-726: shaft residual binding and once-across-lines (R-T726-1 .. -3). Villa K726 is hand-made (not the development
villa): a dog-leg stair shaft 2.40 x 4.80 (inner faces), floors +0.00 / +3.60 / +7.20, roof soffit +10.60, one continuous
face per wall from +0.00 to +10.60 (10.60 m); a landing room on the upper floor walks the shaft's two long faces over its
own 1.20 m landing and has one open slab edge 2.40 (no wall). Hand: N face 2.40 x 10.60 = 25.44; the room chain
1.20 + 1.20 (shaft faces) + 2.40 (open edge) + its own walls 6.00 = 10.80, room face = 6.00.
The last tests rebuild the development-villa result from committed files."""
from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t726"))
import t726_rules as R  # noqa: E402

FACES = [{"id": "N", "width": "2.40", "h_lo": "10.60", "h_hi": "10.60"},
         {"id": "S", "width": "2.40", "h_lo": "3.45", "h_hi": "3.60"},
         {"id": "W", "width": "4.80", "h_lo": "10.60", "h_hi": "10.60"},
         {"id": "E", "width": "4.80", "h_lo": "10.60", "h_hi": "10.60"}]
LEVELS_IN = ["+0.00", "+3.60", "+7.20", "+10.60"]


# ---- R-T726-1 group of a row ----------------------------------------------------------------------------------------
def test_normal_continuation_row_joins_its_group():
    rows = [(10, 30.0, None), (11, 12.0, 42.0), (12, None, None), (13, 5.0, 5.0)]
    g = R.group_of(rows, 11)
    assert g["rows"] == [10, 11] and g["status"] == "ESTABLISHED" and g["J"] == X("42")
    assert R.group_of(rows, 13)["rows"] == [13]


def test_adverse_subtotal_that_does_not_add_up_is_not_a_group():
    g = R.group_of([(1, 30.0, None), (2, 12.0, 43.0)], 2)
    assert g["status"] == "NOT_ESTABLISHED"


def test_adverse_bad_cells():
    with pytest.raises(ValueError):
        R.groups([(1, float("nan"), None), (2, 1.0, 2.0)])
    with pytest.raises(ValueError):
        R.groups([(1, True, None), (2, 1.0, 2.0)])
    assert R.groups([(1, None, 5.0)])[0]["status"] == "NOT_ESTABLISHED"      # a subtotal over no line


# ---- R-T726-2 binding ------------------------------------------------------------------------------------------------
def test_normal_full_height_face_binds():
    res, d = R.bind("2.40", "10.60", FACES, LEVELS_IN, [])
    assert res == "BOUND" and [h["face"] for h in d["height_hits"]] == ["N"]


def test_normal_in_scope_level_interval_binds_once():
    res, d = R.bind("2.40", "7.20", FACES[:1], LEVELS_IN, [])
    assert res == "BOUND" and d["in_scope_level_intervals"] == [["0.00", "7.20"]] and d["height_hits"] == []
    # two faces 2.40 wide (N and S): the part interval cannot say which one
    assert R.bind("2.40", "7.20", FACES, LEVELS_IN, [])[0] == "AMBIGUOUS"


def test_adverse_two_faces_same_size_is_ambiguous():
    faces = FACES + [{"id": "N2", "width": "2.45", "h_lo": "10.55", "h_hi": "10.60"}]
    assert R.bind("2.40", "10.60", faces, LEVELS_IN, [])[0] == "AMBIGUOUS"


def test_adverse_row_on_no_face_stays_unbound_and_out_of_scope_levels_never_bind():
    res, d = R.bind("2.40", "5.40", FACES, LEVELS_IN, [])
    assert res == "NO_FACE" and d["height_hits"] == []
    res, d = R.bind("2.40", "5.40", FACES, LEVELS_IN, ["+1.80"])           # +1.80 printed outside the shaft
    assert res.startswith("NO_FACE") and "OUT_OF_SCOPE" in res
    assert d["out_of_scope_level_intervals"] == [["1.80", "7.20"]]


def test_adverse_tolerances_and_units():
    assert R.bind("2.49", "10.60", FACES, LEVELS_IN, [])[0] == "BOUND"     # 0.09 <= 0.10
    assert R.bind("2.51", "10.60", FACES, LEVELS_IN, [])[0] == "NO_FACE"   # 0.11 > 0.10
    assert R.bind("2400", "10600", FACES, LEVELS_IN, [])[0] == "NO_FACE"   # mm never silently read as m
    assert R.tol_h(X("10.66")) == X("0.1066") and R.tol_h(X("3.00")) == X("0.05")
    assert R.bind("2.40", "10.66", FACES, LEVELS_IN, [])[0] == "BOUND"     # 0.06 <= 1 % of 10.66
    assert R.bind("2.40", "10.75", FACES, LEVELS_IN, [])[0] == "NO_FACE"   # 0.15 > 1 % of 10.75


def test_adverse_held_height_face_never_binds():
    faces = [{"id": "lift", "width": "2.40", "h_lo": None, "h_hi": None}]
    res, d = R.bind("2.40", "10.60", faces, [], [])
    assert res == "NO_FACE" and d["nearest"][0]["height"] is None


def test_adverse_bad_inputs():
    with pytest.raises(ValueError):
        R.bind("0", "5.40", FACES, LEVELS_IN, [])
    with pytest.raises(ValueError):
        R.bind("2.40", None, FACES, LEVELS_IN, [])
    with pytest.raises(ValueError):
        R.bind("2.40", "5.40", [{"id": "x", "width": "2.40", "h_lo": "6", "h_hi": "5"}], [], [])


def test_mirror_and_order_do_not_change_the_result():
    a = R.bind("2.40", "10.60", FACES, LEVELS_IN, [])
    b = R.bind("2.40", "10.60", list(reversed(FACES)), list(reversed(LEVELS_IN)), [])
    assert a[0] == b[0] and a[1]["in_scope_level_intervals"] == b[1]["in_scope_level_intervals"]


# ---- R-T726-3 once across lines ------------------------------------------------------------------------------------
def test_normal_shaft_face_counted_once_across_lines():
    assert R.once("10.80", "6.00", ["1.20", "1.20"], ["2.40"])[0] == "ONCE"


def test_adverse_shaft_face_in_both_lines_is_counted_twice():
    res, d = R.once("10.80", "8.40", ["1.20", "1.20"], ["2.40"])
    assert res == "COUNTED_TWICE" and d["room_minus_expected_lm"] == "2.400000"


def test_adverse_void_edge_without_wall_gets_no_plaster():
    # the room face carries the open slab edge 2.40 as if it were a wall: plaster where nothing is built
    res, d = R.once("10.80", "8.40", ["1.20", "1.20"], ["2.40"])
    assert res == "COUNTED_TWICE" and d["expected_room_face_lm"] == "6.000000"


def test_adverse_room_drops_its_own_wall():
    assert R.once("10.80", "4.80", ["1.20", "1.20"], ["2.40"])[0] == "DROPPED"


def test_adverse_once_bad_inputs():
    with pytest.raises(ValueError):
        R.once("10.80", "-1", [], [])
    with pytest.raises(ValueError):
        R.once("2.00", "1.00", ["1.50"], ["1.00"])
    with pytest.raises(ValueError):
        R.once("nan", "1.00", [], [])


# ---- development villa ------------------------------------------------------------------------------------------------
def test_development_villa_rebuilds_identically():
    p = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t726/t726_alsenan.py"), "--check"],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def test_development_villa_pins():
    r = json.loads((ROOT / "research/agents_t726/out/T726_SHAFT_RESIDUAL.json").read_text(encoding="utf-8"))
    assert r["his_row"]["PLS"]["group_rows"] == [23, 24] and r["his_row"]["PLS"]["group_J"] == "204.420000"
    assert r["binding"]["result"] == "NO_FACE (OUT_OF_SCOPE matches only)"
    assert r["binding"]["in_scope_level_intervals"] == []
    assert r["binding"]["out_of_scope_level_intervals"] == [["0.15", "5.50"], ["4.30", "9.70"]]
    assert r["once"]["1F-13"]["result"] == "ONCE" and r["once"]["2F-01"]["result"] == "ONCE"
    assert r["reconciliation"]["bridge_sum"] == r["reconciliation"]["his_minus_engine"] == "27.350000"
    assert r["reconciliation"]["engine_change_m2"] == "0"
