"""R-T739-1 on a synthetic, non-Alsenan line index (two trades, three units): the normal case re-adds by hand, and the
adverse cases (held quantity, two units, bounded vs released, missing unit, duplicate line, missing cause) refuse or
stay apart. No repository data is read or written."""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t739"))
import t739_rules as R  # noqa: E402


def ln(i, code, unit, cls, q=None, lo=None, hi=None):
    return {"line_id": f"L-{i:020x}", "item_code": code, "unit": unit, "class": cls, "measured_net": q,
            "held_low": lo, "held_high": hi}


TRADE = {"X.SLAB": "T1 Concrete", "X.FORM": "T1 Concrete", "X.TILE": "T2 Floors", "X.SKIRT": "T2 Floors"}

# hand-calculated fixture (a two-storey 12 x 9 m house, not Alsenan):
#   slab 12 x 9 x 0.20 = 21.6 m3 released; roof slab bounded 0.18 .. 0.22 x 108 = 19.44 .. 23.76 m3; stair slab blank
#   formwork soffit 108 m2 released; edge 42 x 0.20 = 8.4 m2 AT_LEAST (height unknown above 0.20)
#   tiles 96.5 m2 released + wet room 6.25 .. 7.5 m2 bounded; skirting 38.4 lm released + 4.2 lm AT_MOST; 1 excluded
FIX = [
    ln(1, "X.SLAB", "m3", "RELEASED", q=21.6),
    ln(2, "X.SLAB", "m3", "HELD", lo=19.44, hi=23.76),
    ln(3, "X.SLAB", "m3", "HELD"),
    ln(4, "X.FORM", "m2", "RELEASED", q=108.0),
    ln(5, "X.FORM", "m2", "HELD", lo=8.4),
    ln(6, "X.TILE", "m2", "RELEASED", q=96.5),
    ln(7, "X.TILE", "m2", "HELD", lo=6.25, hi=7.5),
    ln(8, "X.SKIRT", "lm", "RELEASED", q=38.4),
    ln(9, "X.SKIRT", "lm", "HELD", hi=4.2),
    ln(10, "X.SKIRT", "lm", "EXCLUDED"),
]


def test_normal_hand_readd():
    a = R.aggregate(FIX, TRADE.get)["trade_unit"]
    c = a[("T1 Concrete", "m3")]
    assert c[R.RELEASED]["released"] == Decimal("21.6")
    assert (c[R.BOUNDED]["low"], c[R.BOUNDED]["high"]) == (Decimal("19.44"), Decimal("23.76"))
    assert c[R.BLANK]["n"] == 1 and c[R.BLANK]["released"] == 0 and c[R.BLANK]["low"] == 0
    t = R.range_text(c, "m3")
    assert t["total"] is None and "41.04 .. 45.36 m3" in t["text"] and "1 BLANK" in t["text"]
    f = a[("T1 Concrete", "m2")]
    assert f[R.RELEASED]["released"] == Decimal("108") and f[R.AT_LEAST]["low"] == Decimal("8.4")
    assert "AT_LEAST (>= 8.4)" in R.range_text(f, "m2")["text"]
    s = a[("T2 Floors", "lm")]
    assert s[R.AT_MOST]["high"] == Decimal("4.2") and s[R.EXCLUDED]["n"] == 1
    tiles = a[("T2 Floors", "m2")]
    assert R.range_text(tiles, "m2")["text"].endswith("= 102.75 .. 104 m2")


def test_two_units_never_summed():
    a = R.aggregate(FIX, TRADE.get)["trade_unit"]
    assert ("T1 Concrete", "m3") in a and ("T1 Concrete", "m2") in a
    assert a[("T1 Concrete", "m3")][R.RELEASED]["released"] == Decimal("21.6")   # not 21.6 + 108


def test_bounded_never_enters_released():
    a = R.aggregate(FIX, TRADE.get)["trade_unit"]
    assert a[("T2 Floors", "m2")][R.RELEASED]["released"] == Decimal("96.5")
    assert a[("T2 Floors", "m2")][R.RELEASED]["n"] == 1


def test_all_released_prints_a_total():
    t = R.range_text(R.aggregate([ln(1, "X.SLAB", "m3", "RELEASED", q=1.25), ln(2, "X.SLAB", "m3", "RELEASED", q=2)],
                                 TRADE.get)["trade_unit"][("T1 Concrete", "m3")], "m3")
    assert t["total"] == "3.25"


@pytest.mark.parametrize("bad", [
    ln(1, "X.SLAB", "m3", "HELD", q=5.0),                 # a held quantity is never released
    ln(1, "X.SLAB", "m3", "RELEASED"),                    # released without a quantity
    ln(1, "X.SLAB", "m3", "RELEASED", q=1.0, lo=0.5),     # released with a bound
    ln(1, "X.SLAB", "m3", "HELD", lo=3.0, hi=2.0),        # low > high
    ln(1, "X.SLAB", "m3", "EXCLUDED", q=0.0),             # excluded with a quantity (0 is a quantity)
    ln(1, "X.SLAB", "m3", "PARTIAL", q=1.0),              # unknown class
    ln(1, "X.SLAB", "", "RELEASED", q=1.0),               # no unit
])
def test_adverse_refused(bad):
    with pytest.raises(R.AggregationError):
        R.aggregate([bad], TRADE.get)


def test_duplicate_line_refused():
    with pytest.raises(R.AggregationError):
        R.aggregate([FIX[0], FIX[0]], TRADE.get)


def test_mirror_order_independent():
    a = R.aggregate(FIX, TRADE.get)["trade_unit"]
    b = R.aggregate(list(reversed(FIX)), TRADE.get)["trade_unit"]
    for k in a:
        for s in R.STATES:
            assert all(a[k][s][f] == b[k][s][f] for f in ("n", "released", "low", "high"))


def test_cause_latest_wins_and_finding():
    held = ["L-a", "L-b", "L-c", "L-d"]
    recs = [(600, "T-600 x", "L-a", "old cause"), (700, "T-700 y", "L-a", "new cause"), (650, "T-650 z", "L-b", " ")]
    out, findings = R.resolve_causes(held, recs, {"L-b": "DG-1 APPLIED: basis"}, {"L-c": ("census", "DESIGNER: D-1")})
    assert out["L-a"]["cause"] == "new cause" and out["L-a"]["also_stated_by"] == ["T-600 x"]
    assert out["L-b"]["source"].startswith("Checker downgrade")      # a blank record text is no cause
    assert out["L-c"]["cause"] == "DESIGNER: D-1"
    assert findings == ["L-d"]                                       # listed, never given a cause


def test_prefix_resolution_unique_only():
    ids = {"L-" + "ab" * 10, "L-" + "ab" * 4 + "cd" * 6}
    by = {}
    for i in ids:
        by.setdefault(i[:10], []).append(i)
    assert R.resolve_prefix("L-abababab", ids, by) is None           # ambiguous prefix: never guessed
    assert R.resolve_prefix("L-ababababcd", ids, by) == "L-" + "ab" * 4 + "cd" * 6
    assert R.resolve_prefix("L-" + "ef" * 10, ids, by) is None


def test_pct_range_open_and_closed():
    assert R.pct_range(Decimal(90), Decimal(5), Decimal(15), Decimal(100), False) == "-5.00 .. +5.00 %"
    assert R.pct_range(Decimal(90), Decimal(5), Decimal(15), Decimal(100), True) == "at least -5.00 %, upper end open"
    assert R.pct_range(Decimal(1), Decimal(0), Decimal(0), Decimal(0), False) == "reference 0: no %"
