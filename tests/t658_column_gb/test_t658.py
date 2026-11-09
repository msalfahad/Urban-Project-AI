"""T-658: columns / ground beams / straps / footing HELD lines (research/agents_t658, R-T658-1 .. 6). Hand villa "V658"
(not the training villa) with normal and adverse cases, then the development-villa ledger rebuilt from pinned files."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t658"))
import t658_rules as R  # noqa: E402
import t658_alsenan as A  # noqa: E402

D = Decimal
OUT = ROOT / "research" / "agents_t658" / "out" / "T658_LEDGER.json"
# V658 sheet S-12 prints ground-beam sections: '< 3 m' 25x30, '< 6 m' 25x45, '> 6 m' 25x60 (no precedence).
V658 = [("LT3", "<", "3", ("0.25", "0.30")), ("LT6", "<", "6", ("0.25", "0.45")), ("GT6", ">", "6", ("0.25", "0.60"))]


# ---- R-T658-1 / -2 -----------------------------------------------------------------------------------------------
def test_hand_short_span_both_titles_give_range():
    # 2.40 m: '< 3' and '< 6' both hold -> 0.25 x 0.30 x 2.40 = 0.180 .. 0.25 x 0.45 x 2.40 = 0.270
    lo, hi, fl = R.span_range(D("2.40"), V658, "V658 S-12")
    assert (lo, hi, fl) == (D("0.18"), D("0.27"), ["TITLES_OVERLAP"])


def test_hand_long_span_single_title_is_a_point():
    lo, hi, fl = R.span_range(D("7.00"), V658, "V658 S-12")   # only '> 6' holds: 0.25 x 0.60 x 7 = 1.05
    assert lo == hi == D("1.05") and fl == []


def test_adverse_on_limit_takes_both_adjacent_sections():
    lo, hi, fl = R.span_range(D("6.00"), V658, "V658 S-12")   # exactly 6.00: neither '< 6' nor '> 6' holds
    assert (lo, hi) == (D("0.675"), D("0.9")) and "ON_LIMIT" in fl


def test_adverse_units_and_missing_refused():
    with pytest.raises(R.Refused):
        R.span_range("2400mm", V658, "V658")
    with pytest.raises(R.Refused):
        R.span_range(D("2400"), V658, "V658")          # 2400 m: unit slip
    with pytest.raises(R.Refused):
        R.span_range(None, V658, "V658")
    with pytest.raises(R.Refused):
        R.m("2.4", "")                                 # no source


def test_mirror_and_rotation_do_not_change_a_span_bound():
    # a mirrored / rotated plan gives the same face-to-face span: the bound depends on the length only
    a = R.span_range(D("4.10"), V658, "V658 S-12 plan")
    b = R.span_range(D("4.10"), list(reversed(V658)), "V658 S-12 plan mirrored")
    assert a[:2] == b[:2]


# ---- R-T658-3 ----------------------------------------------------------------------------------------------------
def test_hand_literal_floor_lower_only():
    # runs 3.0 + 1.5 m, b 0.25, top +0.40 to N.G. 0.00: 4.5 x 0.25 x 0.40 = 0.450 floor; high open
    f = R.literal_floor(["3.0", "1.5"], "0.25", "0.40", "0.00", "V658 S-13")
    assert f == D("0.45")
    row = R.row("L-V658-GB1", "STR.CONC.GROUND_BEAM", "V658:GB1", "LOWER_ONLY", low=f, item="designer depth item")
    assert row["high"] is None and row["low"] == "0.450000"


def test_adverse_literal_top_below_underside_refused():
    with pytest.raises(R.Refused):
        R.literal_floor(["3.0"], "0.25", "0.00", "0.10", "V658")


# ---- R-T658-4 / -5 -----------------------------------------------------------------------------------------------
def test_hand_column_ceiling_from_finished_mark():
    # schedule 20x50 = 0.10 m2, base slab top +6.95, roof finished mark +10.40: h <= 3.45 -> ceiling 0.345 m3
    assert R.column_ceiling(D("0.10"), "6.95", "10.40") == D("0.345")


def test_adverse_ceiling_refused_with_upstand_or_unknown_second_reading():
    assert R.column_ceiling(D("0.10"), "6.95", "10.40", top_may_exceed_mark=True) is None
    assert R.column_ceiling(D("0.10"), "6.95", "10.40", second_reading_unknown=True) is None


def test_adverse_schedule_and_plan_disagree_hold_both():
    lo, hi = R.conflict_range(["0.125", "0.10"], D("4.20"))   # plan 25x50 vs schedule 20x50 x 4.20
    assert (lo, hi) == (D("0.42"), D("0.525"))
    with pytest.raises(R.Refused):
        R.conflict_range(["0.10", "0.10"], D("4.20"))        # one reading is not a range


# ---- R-T658-6 ----------------------------------------------------------------------------------------------------
def test_held_never_zero_and_blank_names_item():
    with pytest.raises(R.Refused):
        R.row("L-x", "STR.CONC.COLUMN", "x", "BOUNDED", low=0, high="0.3")
    R.row("L-x", "STR.CONC.STRAP", "x", "BOUNDED", low=0, high="0.3", flags=["EXISTENCE_OPEN"])
    with pytest.raises(R.Refused):
        R.row("L-x", "STR.CONC.COLUMN", "x", "HELD_BLANK")
    with pytest.raises(R.Refused):
        R.row("L-x", "STR.CONC.COLUMN", "x", "UPPER_ONLY", high="0.4")


# ---- development villa: rebuilt from pinned committed files --------------------------------------------------------
def test_ledger_reproduces_committed_output():
    doc = A.build()
    assert json.loads(json.dumps(doc, sort_keys=True)) == json.loads(OUT.read_text(encoding="utf-8"))


def test_ledger_every_line_once_and_counts():
    doc = A.build()
    rows = doc["rows"]
    assert len(rows) == 61 and len({r["line_id"] for r in rows}) == 61
    t = doc["totals"]
    assert {k: t[k]["lines"] for k in t} == {"STR.CONC.COLUMN": 29, "STR.CONC.GROUND_BEAM": 29,
                                              "STR.CONC.STRAP": 2, "STR.CONC.FOOTING": 1}
    gb = t["STR.CONC.GROUND_BEAM"]
    assert (gb["before_low"], gb["before_high"]) == ("2.808073", "6.621731")
    assert (gb["bounded"], gb["bounded_low"], gb["bounded_high"]) == (15, "3.104473", "7.873294")
    assert (gb["lower_only"], gb["lower_only_floor"], gb["blank"]) == (8, "2.227973", 6)
    col = t["STR.CONC.COLUMN"]
    assert (col["bounded_low"], col["bounded_high"]) == ("8.034000", "10.119000")   # conflict range unchanged
    assert (col["upper_only"], col["upper_only_ceiling"], col["blank"]) == (6, "2.801250", 8)


def test_ledger_no_figure_invented_and_ranges_not_narrowed():
    for r in A.build()["rows"]:
        if r["before_low"] is not None and r["low"] is not None:
            assert D(r["low"]) <= D(r["before_low"]) and D(r["high"]) >= D(r["before_high"]), r["line_id"]
        if r["status"] == "HELD_BLANK":
            assert r["low"] is None and r["high"] is None and r["item"]
        assert "freelancer" not in json.dumps(r).lower()
