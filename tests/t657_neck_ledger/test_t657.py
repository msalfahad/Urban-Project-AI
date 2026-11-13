"""T-657: column necks bounded on both ends from printed drawings (research/agents_t657, R-T657-1 .. 4). Hand villa
"V657" (not the training villa) with normal and adverse cases, then the development-villa ledger rebuilt from merged
repository files."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t657"))
import t657_rules as R  # noqa: E402
import t657_necks as N  # noqa: E402

D = Decimal
OUT = ROOT / "research" / "agents_t657" / "out" / "T657_NECK_LEDGER.json"


# ---- villa "V657" (hand) -----------------------------------------------------------------------------------------
# Neck 0.30 x 0.60 (0.18 m2) on a 0.40 deep pad; ground-beam / GF column base printed +0.80; sheet prints 'excavation not
# less than 1.50 below the plot level +-0.00', a 0.17 stack under the footing and the single-row detail 'LESS THAN
# 2.5m' (footing underside .. upper ground beam); one ground-beam row drawn.
#   low  h = 0.80 + 1.50 - 0.17 - 0.40 = 1.73  -> 0.18 x 1.73 = 0.311400 m3
#   high h = 2.50 - 0.40              = 2.10  -> 0.18 x 2.10 = 0.378000 m3
def test_hand_normal_bounded_both_ends():
    hl, hh, lo, hi, why = R.neck_range(D("0.80"), D("1.50"), D("0.17"), [D("0.40")], [D("0.18")], D("2.50"),
                                       one_gb_row_drawn=True)
    assert (hl, hh, lo, hi, why) == (D("1.73"), D("2.10"), D("0.311400"), D("0.378000"), None)


def test_hand_section_and_depth_candidates_take_each_end():
    # two sections 0.15 / 0.18, two depths 0.30 / 0.40 (two readings): low = 0.15 x (2.13 - 0.40) ; high = 0.18 x 2.20
    hl, hh, lo, hi, _ = R.neck_range(D("0.80"), D("1.50"), D("0.17"), [D("0.30"), D("0.40")], [D("0.18"), D("0.15")],
                                     D("2.50"), one_gb_row_drawn=True)
    assert (hl, hh, lo, hi) == (D("1.73"), D("2.20"), D("0.259500"), D("0.396000"))


def test_hand_mirrored_or_rotated_plan_is_the_same_neck():
    a = R.neck_range(D("0.80"), D("1.50"), D("0.17"), [D("0.30"), D("0.40")], [D("0.15"), D("0.18")], D("2.50"),
                     one_gb_row_drawn=True)
    b = R.neck_range(D("0.80"), D("1.50"), D("0.17"), [D("0.40"), D("0.30")], [D("0.18"), D("0.15")], D("2.50"),
                     one_gb_row_drawn=True)
    assert a == b


def test_adverse_missing_footing_depth_stays_held():
    with pytest.raises(R.Refused):
        R.neck_range(D("0.80"), D("1.50"), D("0.17"), [None], [D("0.18")], D("2.50"), one_gb_row_drawn=True)


def test_adverse_missing_top_or_min_depth_stays_held():
    with pytest.raises(R.Refused):
        R.neck_low_height(None, D("1.50"), D("0.17"), [D("0.40")])
    with pytest.raises(R.Refused):
        R.neck_low_height(D("0.80"), None, D("0.17"), [D("0.40")])


def test_adverse_no_printed_condition_gives_no_typical_upper():
    with pytest.raises(R.Refused):
        R.neck_high_height(D("2.50"), [D("0.40")], one_gb_row_drawn=True, detail_printed=False)


def test_adverse_lower_beam_row_drawn_upper_open():
    hh, why = R.neck_high_height(D("2.50"), [D("0.40")], one_gb_row_drawn=False)
    assert hh is None and "lower ground-beam row" in why


def test_adverse_pit_raft_of_supplier_depth_upper_open():
    hl, hh, lo, hi, why = R.neck_range(D("0.80"), D("1.50"), D("0.17"), [D("0.55")], [D("0.18")], D("2.50"),
                                       one_gb_row_drawn=True, pit_raft_unprinted=True)
    assert hh is None and hi is None and lo == D("0.284400") and "R-T657-2" in why


def test_adverse_contradiction_refused():
    # printed minimum 2.00 with top +0.95: low 0.95 + 2.00 - 0.17 - 0.40 = 2.38 > single-row high 2.10
    with pytest.raises(R.Refused):
        R.neck_range(D("0.95"), D("2.00"), D("0.17"), [D("0.40")], [D("0.18")], D("2.50"), one_gb_row_drawn=True)


def test_adverse_units_mm_refused():
    with pytest.raises(R.Refused):
        R.neck_high_height(D("2500"), [D("0.40")], one_gb_row_drawn=True)
    with pytest.raises(R.Refused):
        R.neck_low_height(D("0.80"), D("1500"), D("0.17"), [D("0.40")])


def test_value_only_on_two_printed_levels_never_midpoint():
    assert R.neck_value(D("-0.30"), D("-1.20"), [D("0.16")]) == D("0.144000")
    with pytest.raises(R.Refused):
        R.neck_value(D("0.80"), None, [D("0.18")])
    with pytest.raises(R.Refused):
        R.neck_value(D("0.80"), D("-1.00"), [D("0.15"), D("0.18")])


# ---- development villa (committed inputs only) -------------------------------------------------------------------
@pytest.fixture(scope="module")
def doc():
    return N.build()


def test_rebuild_equals_committed(doc):
    assert json.loads(OUT.read_text(encoding="utf-8")) == json.loads(json.dumps(doc, ensure_ascii=False))


def test_every_line_once_and_counts(doc):
    ids = [r["line_id"] for r in doc["necks"]]
    assert len(ids) == len(set(ids)) == 36
    t = doc["totals"]
    assert (t["valued"], t["bounded_as_drawn"], t["lower_only"]) == (0, 32, 4)
    assert t["family_low_m3"] == "9.723900" and t["family_high_m3"] is None
    assert t["bounded_part"] == {"lines": 32, "low_m3": "8.772400", "high_m3": "11.346000"}
    assert t["lift_lower_only_m3"] == "0.951500"
    assert t["before_candidate_generic"] == {"low_m3": "3.075000", "high_m3": "15.375000", "lines_with_range": 35,
                                             "blank_lines": 1}


def test_lift_necks_open_by_name_never_zero(doc):
    lift = [r for r in doc["necks"] if r["footing"] == "FF"]
    assert len(lift) == 4
    for r in lift:
        assert r["m3_high"] is None and "D-43" in r["high_item"] and D(r["m3_low"]) > 0


def test_bounds_ordered_and_inside_generic_range(doc):
    for r in doc["necks"]:
        lo = D(r["m3_low"])
        assert lo > 0
        if r["m3_high"] is not None:
            assert lo <= D(r["m3_high"])
            assert D(r["h_high_m"]) == D("2.50") - min(D(x) for x in r["footing_H_m"])
        c = r["candidate_range_generic_T167"]
        if c:
            assert D(c[0]) <= lo and (r["m3_high"] is None or D(r["m3_high"]) <= D(c[1]))


def test_key_necks_by_hand(doc):
    by = {(r["mark"], r["position"]): r for r in doc["necks"]}
    r = by[("C11", "10BA")]   # 0.30 x 1.10 on F13 (H 0.50), top +0.95: 0.33 x 1.78 .. 0.33 x 2.00
    assert (r["m3_low"], r["m3_high"]) == ("0.587400", "0.660000")
    r = by[("C3", "10CC")]    # 0.30 x 0.50 on F12 (H 0.70): 0.15 x 1.58 .. 0.15 x 1.80
    assert (r["m3_low"], r["m3_high"]) == ("0.237000", "0.270000")
    r = by[("CN", "17C5")]    # the one blank line: 0.09 x 1.08 .. 0.09 x 2.00
    assert r["candidate_range_generic_T167"] is None and (r["m3_low"], r["m3_high"]) == ("0.097200", "0.180000")
