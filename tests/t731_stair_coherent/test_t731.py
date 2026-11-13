"""T-731: a stair reading is coherent only between printed levels (R-T731-1); restating a line never raises its low
(R-T731-2). Villa V731 is hand-made (not the development villa): GF +0.20, printed half landing +1.90, 1F +3.60
(storey 3.40); section 10 + 10 = 20 risers, structural plan 11 + 10 = 21; going 0.28, waist T 0.15, lane 1.10. Hand
figures are written out in each test. The last tests rebuild the development-villa ledger from committed files (the
drawing facts are constants in the builder; no drawing is opened)."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t731"))
import t731_rules as R  # noqa: E402
import t731_alsenan as A  # noqa: E402

R725 = R.R725
LV = [R.PrintedLevel("GF", 0.20, "level mark"), R.PrintedLevel("LD", 1.90, "dimension 170 above GF"),
      R.PrintedLevel("1F", 3.60, "level mark")]
BRK = {"F1": "LD"}
SEC_READ = (("F1", 10), ("F2", 10))
PLAN_READ = (("F1", 11), ("F2", 10))
G, T, W = 0.28, 0.15, 1.10


# ---------------------------------------------------------------- R-T731-1 normal
def test_section_reading_uniform_and_coherent():
    s = R.segments("S", SEC_READ, "section", LV, BRK)
    # 1.70 / 10 = 0.17 and 1.70 / 10 = 0.17
    assert [(x.n, round(x.r, 12)) for x in s] == [(10, 0.17), (10, 0.17)]
    assert R.uniform_misses("S", SEC_READ, LV, BRK) == []


def test_plan_reading_coherent_piecewise():
    s = R.segments("Q", PLAN_READ, "structural plan", LV, BRK)
    # 1.70 / 11 = 0.154545..., then 1.70 / 10 = 0.17: count x riser = printed rise in each segment
    assert abs(s[0].r - 1.70 / 11) < 1e-15 and abs(s[1].r - 0.17) < 1e-15
    assert abs(s[0].n * s[0].r - 1.70) < 1e-12 and abs(s[1].n * s[1].r - 1.70) < 1e-12


def test_no_intermediate_level_printed_uniform_is_coherent():
    lv = [LV[0], LV[2]]
    s = R.segments("Q2", PLAN_READ, "structural plan", lv, {})
    assert len(s) == 1 and abs(s[0].r - 3.40 / 21) < 1e-15
    assert R.uniform_misses("Q2", PLAN_READ, lv, {}) == []


def test_coherent_high_differs_from_uniform_by_hand():
    # well-side profile of the 11-line flight at the coherent 0.154545 vs the uniform 3.40 / 21 = 0.161905:
    # O = 10 x 1/2 x g x r + T x 10 g x sec(r)
    # coherent: 0.216364 + 0.15 x 2.80 x 1.142211 (0.479729) = 0.696092
    # uniform:  0.226667 + 0.15 x 2.80 x 1.155141 (0.485159) = 0.711826 (+0.015734, a high the uniform overstates)
    def hand(r):
        return 10 * 0.5 * G * r + T * 10 * G * math.hypot(G, r) / G
    for r in (1.70 / 11, 3.40 / 21):
        assert abs(R725.side_profile(r, G, T, 11, 0.0, 10 * G, clip_floor=False) - hand(r)) < 1e-12
    assert round(hand(1.70 / 11), 6) == 0.696092 and round(hand(3.40 / 21), 6) == 0.711826


# ---------------------------------------------------------------- R-T731-1 adverse
def test_adverse_uniform_rise_missing_a_printed_landing_refused():
    m = R.uniform_misses("Q-uniform", PLAN_READ, LV, BRK)
    # 0.20 + 11 x 3.40 / 21 = 1.980952 against the printed 1.90: miss +0.080952 > 0.005
    assert m == [("LD", 1.90, 1.980952, 0.080952)]


def test_adverse_miss_within_print_precision_is_not_a_miss():
    lv = [LV[0], R.PrintedLevel("LD", 1.99, "dimension"), LV[2]]   # 0.20 + 11 x 0.161905 = 1.980952: 0.009 off
    assert len(R.uniform_misses("Q", PLAN_READ, lv, BRK)) == 1
    lv = [LV[0], R.PrintedLevel("LD", 1.98, "dimension"), LV[2]]   # 0.000952 off < 0.005
    assert R.uniform_misses("Q", PLAN_READ, lv, BRK) == []


def test_adverse_count_from_one_source_rise_from_another_still_refused():
    with pytest.raises(R.Refused, match="R-T725-1"):
        R725.Reading("mixed", 3.40, PLAN_READ, "plan", "section 20", total_declared=20)


def test_adverse_drawn_count_changed_refused():
    with pytest.raises(R.Refused, match=r"R-T731-1 \(d\)"):
        R.check_drawn_counts("P", (("F1", 10), ("F2", 9)), {"F2": 10})
    R.check_drawn_counts("S", SEC_READ, {"F2": 10})


def test_adverse_units_mm_refused():
    lv = [R.PrintedLevel(x.name, x.level_m * 1000, x.source) for x in LV]
    with pytest.raises(R.Refused, match="not a riser"):
        R.segments("mm", SEC_READ, "section", lv, BRK)


def test_adverse_skipped_or_unprinted_level_refused():
    with pytest.raises(R.Refused, match="not printed"):
        R.segments("x", SEC_READ, "section", LV, {"F1": "LD2"})
    lv4 = LV[:2] + [R.PrintedLevel("MID", 2.60, "mark")] + LV[2:]
    with pytest.raises(R.Refused, match="skipped"):
        R.segments("x", SEC_READ, "section", lv4, {"F1": "LD", "F2": "1F"})
    with pytest.raises(R.Refused, match="count source"):
        R.segments("x", SEC_READ, "", LV, BRK)


def test_adverse_zero_count_segment_refused():
    with pytest.raises(R.Refused, match="no riser"):
        R.segments("x", (("F1", 0), ("F2", 20)), "section", LV, BRK)


def test_mirror_and_rotation_do_not_change_a_reading():
    # a reading is counts and printed levels only: a mirrored / rotated plan gives the same segments
    a = R.segments("Q", PLAN_READ, "structural plan", LV, BRK)
    b = R.segments("Q-mirror", tuple(reversed(tuple(reversed(PLAN_READ)))), "structural plan (mirrored)", LV, BRK)
    assert [(x.n, x.r) for x in a] == [(x.n, x.r) for x in b]


# ---------------------------------------------------------------- R-T731-2
def test_low_never_raised_by_the_coherent_rule():
    # old low 0.50 came from a reading now refused; the coherent readings sit at 0.60 / 0.70: low stays 0.50, flagged
    x = R.restate(0.50, 0.90, {"S": (0.60, 0.80), "Q": (0.70, 0.75)})
    assert x["low"] == 0.50 and x["flag"] == "LOW_KEPT_REFUSED_SOURCE" and x["high"] == 0.80
    assert abs(x["high_moved"] + 0.10) < 1e-12


def test_low_may_fall_and_high_may_fall_named():
    x = R.restate(0.65, 0.90, {"S": (0.60, 0.80), "Q": (0.70, 0.75)})
    assert x["low"] == 0.60 and x["flag"] is None and abs(x["low_moved"] + 0.05) < 1e-12


def test_adverse_zero_or_missing_reading_refused():
    with pytest.raises(R.Refused, match="never 0"):
        R.restate(0.5, None, {"S": (0.0, 1.0)})
    with pytest.raises(R.Refused, match="no coherent reading"):
        R.restate(0.5, None, {})
    x = R.restate(0.5, None, {"S": (0.6, None), "Q": (0.7, 0.8)})
    assert x["high"] is None


# ---------------------------------------------------------------- development villa (committed inputs only)
@pytest.fixture(scope="module")
def built():
    return A.build()


def test_dev_villa_ledger_reproduced(built):
    js = json.dumps(built, indent=1, sort_keys=True, default=str) + "\n"
    assert A.OUT_JSON.read_text(encoding="utf-8") == js
    assert A.OUT_MD.read_text(encoding="utf-8") == A.report_md(built)


def test_dev_villa_readings(built):
    assert set(built["readings_coherent"]) == {"A", "B"}
    assert set(built["readings_refused"]) == {"P", "B28-uniform", "B27-as-recorded"}
    b = built["readings_coherent"]["B"]["segments"]
    assert [(s["n"], s["r"]) for s in b] == [(16, 0.15625), (12, round(2.0 / 12, 9))]
    assert built["readings_refused"]["B28-uniform"]["misses"] == [["LD", 3.5, 3.571429, 0.071429]] or \
        built["readings_refused"]["B28-uniform"]["misses"] == [("LD", 3.5, 3.571429, 0.071429)]


def test_dev_villa_restated_highs_only(built):
    by = {x["line_id"]: x for x in built["restated"]}
    assert by["L-9c3643da524267bf47f6"]["low_new"] == "0.679193"
    assert by["L-9c3643da524267bf47f6"]["high_new"] == "0.843465"     # was 0.854426
    assert by["L-d9790e457fd530487553"]["cap_new"] == "0.862807"      # was 0.873917
    assert by["L-ffd491ad529ee2251982"]["low_new"] == "7.678894"      # unchanged
    assert by["L-7863355dfcb68a681d2d"]["low_new"] == "1.213428"      # 1.213429 half-up -> directed floor
    assert by["L-7863355dfcb68a681d2d"]["reading_sums_new"]["B"] == "1.366662"
    assert built["effects_beside"]["MS1-L concrete high m3 (side O x 1.20)"]["T-731 coherent B"] == "1.023763"


def test_dev_villa_remeasure_residuals_zero(built):
    vals = [x for x in built["remeasure"] if x["own_m3"] is not None]
    assert len(vals) == 4 and all(x["residual_m3"] == 0.0 for x in vals)
