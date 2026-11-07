"""T-592 external door step, ONE payable length (R-T592-1): a non-Alsenan hand fixture (door 0.90 clear in a 1.00
masonry opening: stone 1.00, nosing 0.90), adverse cases (both lengths on one line, a riser from a level outside the
step's region, two levels in one region, nosing longer than the stone, equal levels, units), and the development-villa
build pinned (byte-identical rebuild, hand totals, D-GF-09 riser, gate re-read, no coordinates)."""
from __future__ import annotations

import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t592"
sys.path.insert(0, str(HERE))
R = importlib.import_module("t592_rules")
_spec = importlib.util.spec_from_file_location("t592_alsenan", HERE / "t592_alsenan.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

D = Decimal


def _ok(low="+0.30"):
    return R.outside_level([low])


# ---- hand fixture (Villa K592, not Alsenan) --------------------------------------------------------------------------
def test_fixture_stone_is_the_masonry_opening_nosing_beside():
    r = R.door_step("K-D1", "1.00", "0.90", "+0.45", _ok())
    assert r["payable_lm"] == D("1.00") and r["nosing_lm"] == D("0.90") and r["jambs_lm"] == D("0.10")
    assert r["riser_m"] == D("0.15") and r["riser_m2"] == D("0.1500") and r["nr"] == 1
    assert r["status"] == "DRAWING-CONFIRMED"


def test_fixture_in_mm_equals_m():
    r = R.door_step("K-D1", "1000", "900", "+0.45", _ok(), unit="mm")
    assert r["payable_lm"] == D("1.00") and r["riser_m2"] == D("0.15")


def test_fixture_two_doors_one_payable_lm_hand_total():
    a = R.door_step("K-D1", "1.00", "0.90", "+0.45", _ok())
    b = R.door_step("K-D2", "0.90", "0.80", "+0.45", _ok())
    assert R.payable_line([a, b]) == D("1.90")              # 1.00 + 0.90, never 1.70 (edges) or 3.60 (both)
    assert a["riser_m2"] + b["riser_m2"] == D("0.2850")     # 1.90 x 0.15


def test_fixture_no_edge_is_not_applicable():
    r = R.door_step("K-D3", "1.00", None, "+1.00", _ok("+1.00"))
    assert r["status"] == "NOT_APPLICABLE" and r["nr"] == 0 and r["payable_lm"] is None
    assert R.payable_line([r]) == D(0)


def test_fixture_region_with_one_figure_confirms_repeated_marks():
    o = R.outside_level(["+0.15", "+0.15", "+0.15"])
    assert o["status"] == "DRAWING-CONFIRMED" and o["low"] == D("0.15")


def test_fixture_datum_mark_reads_as_zero():
    assert R.outside_level(["%%p0.00"])["low"] == D(0) and R.outside_level(["+-0.00"])["low"] == D(0)


# ---- adverse ---------------------------------------------------------------------------------------------------------
def test_adverse_both_lengths_on_one_line_refused():
    r = R.door_step("K-D1", "1.00", "0.90", "+0.45", _ok())
    r["nosing_payable"] = True
    with pytest.raises(R.RuleError, match="both the piece length and the nosing"):
        R.payable_line([r])


def test_adverse_riser_from_a_level_not_in_the_region_refused():
    with pytest.raises(R.RuleError, match="not printed in the step's low-side region"):
        R.riser_from("+0.30", "+-0.00", ["+0.15"])       # the plan's datum behind a fence never sets the riser


def test_adverse_two_levels_in_one_region_hold_with_bound():
    o = R.outside_level(["+0.15", "+-0.00"])
    assert o["status"] == "HELD" and o["low"] is None and o["bound"] == (D(0), D("0.15"))
    r = R.door_step("K-D1", "1.00", "0.90", "+0.30", o)
    assert r["status"] == "HELD" and r["riser_m2"] is None and r["riser_m2_bound"] == (D("0.15"), D("0.30"))


def test_adverse_no_level_in_region_holds_never_zero():
    o = R.outside_level([], plan_levels=["+-0.00", "+0.15", "+0.30"], high="+0.30")
    assert o["status"] == "HELD" and o["bound"] == (D(0), D("0.30"))
    r = R.door_step("K-D1", "0.90", "0.80", "+0.30", o)
    assert r["riser_m2"] is None and r["riser_m2_bound"] == (D(0), D("0.270"))
    assert R.outside_level([])["bound"] is None


def test_adverse_nosing_longer_than_the_stone_refused():
    with pytest.raises(R.RuleError, match="longer than the stone"):
        R.door_step("K-D1", "0.90", "1.00", "+0.45", _ok())


def test_adverse_edge_between_equal_levels_refused():
    with pytest.raises(R.RuleError, match="equal"):
        R.door_step("K-D1", "1.00", "0.90", "+0.30", _ok("+0.30"))
    with pytest.raises(R.RuleError, match="equal"):
        R.riser_from("+0.30", "+0.30", ["+0.30"])


def test_adverse_units_and_unknowns():
    with pytest.raises(R.RuleError):
        R.length("1.00", unit="cm")
    with pytest.raises(R.RuleError):
        R.length("0")
    with pytest.raises(R.RuleError):
        R.D(None)
    with pytest.raises(R.RuleError):
        R.book("lm", "m2")
    with pytest.raises(R.RuleError, match="HELD, never 0"):
        R.payable_line([{"opening": "K-D9", "payable_lm": None, "status": "HELD"}])


# ---- development villa (pinned) --------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def built():
    return A.build()


def test_alsenan_rebuild_byte_identical(built):
    txt = json.dumps(built, indent=1, sort_keys=True) + "\n"
    assert A.OUT.read_text(encoding="utf-8") == txt


def test_alsenan_house_doors_one_payable_lm(built):
    t = built["totals"]
    assert t["house_payable_lm"] == "3.8" and t["house_nosing_lm_attribute"] == "3.5" and t["house_nr"] == 4
    assert t["house_riser_m2"] == "0.570"                  # 3.80 x 0.15
    for oid in A.HOUSE:
        r = built["openings"][oid]
        assert r["payable_lm"] == r["t325_strip_width_m"]   # the stone = the owning strip line's width


def test_alsenan_d_gf_09_riser_from_its_region(built):
    r = built["openings"]["D-GF-09"]
    assert r["status"] == "DRAWING-CONFIRMED" and r["riser_m"] == "0.15" and r["riser_m2"] == "0.135"
    assert list(r["outside_region_levels"]) == ["+0.15"] and "40B" in r["outside_region_levels"]["+0.15"]
    assert r["drawing_conflict"] and abs(D(r["edge_vs_gap_residual_m"])) <= A.TOL


def test_alsenan_gate_reread(built):
    g = built["openings"]["D-GF-15"]
    assert (g["payable_lm"], g["nosing_lm"], g["riser_m"], g["riser_m2"]) == ("1.0", "0.9", "0.15", "0.150")
    assert list(g["outside_region_levels"]) == ["+-0.00"] and g["inside_level"] == "+0.15"
    assert g["owning_line"] is None                          # NO_LINE today: FR-T592-2


def test_alsenan_compare_units_apart_no_pct(built):
    c = built["compare"]
    assert c["unit"] == "lm" and c["pct"] is None and c["gap_with_gate_lm"] == "-2.9" and c["gap_house_lm"] == "-3.9"


def test_alsenan_changed_input_stops_the_build(monkeypatch):
    monkeypatch.setitem(A.PINS, A.DRAWN, "0000000000000000")
    with pytest.raises(R.RuleError, match="changed"):
        A.build()


def test_alsenan_drawn_json_has_no_coordinates():
    d = json.loads((HERE / "T592_DRAWN.json").read_text(encoding="utf-8"))

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                assert k not in ("x", "y", "insert_point", "coords", "position")
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            assert abs(x) < 25, x                            # lengths / offsets in m only, never a drawing coordinate
    walk(d)
