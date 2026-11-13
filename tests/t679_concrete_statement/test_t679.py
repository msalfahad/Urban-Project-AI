"""T-679 R-T679-1 concrete reconciliation statement. Villa V679 is hand-made (not the development villa); the last tests
rebuild the development-villa statement from committed files only and check it against the line index and the master
census to the last digit."""
from __future__ import annotations

import json
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t679"))
import t679_rules as R  # noqa: E402

FAMS = [{"code": "F-FOOT", "item_codes": ["STR.CONC.FOOTING"]},
        {"code": "F-COL", "item_codes": ["STR.CONC.COLUMN", "STR.CONC.NECK"]},
        {"code": "F-RB", "item_codes": ["STR.REBAR"]}]


def ln(lid, code, cls, net=None, lo=None, hi=None, unit="m3", binding=None):
    return {"line_id": lid, "item_code": code, "class": cls, "measured_net": net, "held_low": lo, "held_high": hi,
            "unit": unit, "binding": {"binding": binding} if binding else None, "element_id": lid}


def villa():
    # V679 by hand: pads P1 1.2 x 1.2 x 0.5 = 0.72, P2 1.5 x 1.0 x 0.5 = 0.75 (released), P3 depth not printed:
    # 1.0 x 1.0 x (0.4 .. 0.6) = 0.4 .. 0.6 (HELD bounded); C1 0.2 x 0.4 x 3.0 = 0.24 released VERIFIED_WHOLE;
    # C2 0.2 x 0.5 x 3.0 = 0.3 released VERIFIED_COMPONENT; neck N1 height not printed: blank; C3 not built (excluded);
    # a rebar line (another trade) is ignored.
    lines = [ln("L-P1", "STR.CONC.FOOTING", "RELEASED", 0.72), ln("L-P2", "STR.CONC.FOOTING", "RELEASED", 0.75),
             ln("L-P3", "STR.CONC.FOOTING", "HELD", lo=0.4, hi=0.6),
             ln("L-C1", "STR.CONC.COLUMN", "RELEASED", 0.24, binding="VERIFIED_WHOLE"),
             ln("L-C2", "STR.CONC.COLUMN", "RELEASED", 0.3, binding="VERIFIED_COMPONENT"),
             ln("L-N1", "STR.CONC.NECK", "HELD"), ln("L-C3", "STR.CONC.COLUMN", "EXCLUDED"),
             ln("L-R1", "STR.REBAR", "RELEASED", 12.5, unit="kg")]
    causes = {"L-P3": {"cause_class": "DESIGNER ITEM"}, "L-N1": {"cause_class": "OPEN BOUND"}}
    return lines, causes


def test_family_subtotals_and_trade_total_hand():
    lines, causes = villa()
    a = R.aggregate(lines, FAMS, causes, prefix="STR.CONC", unit="m3")
    f = R.scope_view(a["families"]["F-FOOT"])
    assert f["released"] == {"lines": 2, "m3": "1.47"}                            # 0.72 + 0.75
    assert f["held_bounded"]["low"] == "0.4" and f["held_bounded"]["high"] == "0.6"
    assert f["engine_range"] == ["1.87", "2.07"]                                    # no blank: closed range
    c = R.scope_view(a["families"]["F-COL"])
    assert c["released"] == {"lines": 2, "m3": "0.54"}                            # 0.24 + 0.30
    assert c["held_blank"] == {"lines": 1, "high": "OPEN", "by_cause": {"DESIGNER ITEM": 0, "OPEN BOUND": 1,
                                                                         "MEASURABLE NOW": 0}}
    assert c["engine_range"] == ["0.54", "OPEN"]                                    # blank never 0
    assert c["excluded"] == {"lines": 1}
    assert c["verified_share"] == {"whole": "1 / 3", "whole_m3": "0.24", "component": "1 / 3", "component_m3": "0.3"}
    t = R.scope_view(a["total"])
    assert t["lines"] == 7 and t["released"]["m3"] == "2.01" and t["engine_range"] == ["2.41", "OPEN"]
    assert "F-RB" not in a["families"]


def test_held_blank_never_becomes_zero_adverse():
    lines, causes = villa()
    a = R.aggregate(lines, FAMS, causes, prefix="STR.CONC", unit="m3")
    v = R.scope_view(a["codes"]["STR.CONC.NECK"])
    assert v["released"]["m3"] == "0" and v["released"]["lines"] == 0
    assert v["engine_range"][1] == "OPEN" and v["held_blank"]["lines"] == 1
    with pytest.raises(R.Refused):
        R.D(None)


def test_reference_apart_pct_suppressed_beside_held():
    lines, causes = villa()
    a = R.aggregate(lines, FAMS, causes, prefix="STR.CONC", unit="m3")
    keys = [{"key": "K.FOOT", "reference_id": "r1", "item_codes": ["STR.CONC.FOOTING"]},
            {"key": "K.COL", "reference_id": "r2", "item_codes": ["STR.CONC.COLUMN"]}]
    refs = {"r1": {"qty": 1.6, "unit": "m3"}, "r2": {"qty": 0.6, "unit": "m3"}}
    rows = R.compare(keys, refs, a["codes"], unit="m3")
    assert rows[0]["difference_ref_minus_released"] == "0.13" and rows[0]["pct_of_reference"] is None   # 1.6 - 1.47
    assert "HELD" in rows[0]["pct_note"]
    # columns only (neck not in the key): no HELD line -> % printed: (0.6 - 0.54) / 0.6 = 10.00 %
    assert rows[1]["difference_ref_minus_released"] == "0.06" and rows[1]["pct_of_reference"] == "10.00"
    assert R.not_keyed(a["codes"], keys) == ["STR.CONC.NECK"]


@pytest.mark.parametrize("bad, why", [
    (ln("L-X", "STR.CONC.FOOTING", "RELEASED"), "RELEASED without a number"),
    (ln("L-X", "STR.CONC.FOOTING", "HELD", net=0.3), "released number"),
    (ln("L-X", "STR.CONC.FOOTING", "HELD", lo=0.3), "one bound only"),
    (ln("L-X", "STR.CONC.FOOTING", "HELD", lo=0.6, hi=0.4), "not ordered"),
    (ln("L-X", "STR.CONC.FOOTING", "RELEASED", 0.3, unit="m2"), "units never mixed"),
    (ln("L-X", "STR.CONC.TANK", "RELEASED", 0.3), "NO_FAMILY"),
    (ln("L-X", "STR.CONC.FOOTING", "EXCLUDED", 0.3), "EXCLUDED line carries"),
    (ln("L-X", "STR.CONC.FOOTING", "HELD", binding="VERIFIED_WHOLE"), "never verified"),
])
def test_refusals_adverse(bad, why):
    lines, causes = villa()
    causes["L-X"] = {"cause_class": "DESIGNER ITEM"}
    with pytest.raises(R.Refused, match=why):
        R.aggregate(lines + [bad], FAMS, causes, prefix="STR.CONC", unit="m3")


def test_held_without_cause_refused_and_double_owner_refused():
    lines, causes = villa()
    del causes["L-N1"]
    with pytest.raises(R.Refused, match="no census cause"):
        R.aggregate(lines, FAMS, causes, prefix="STR.CONC", unit="m3")
    lines, causes = villa()
    with pytest.raises(R.Refused, match="DOUBLY_OWNED"):
        R.aggregate(lines, FAMS + [{"code": "F-DUP", "item_codes": ["STR.CONC.NECK"]}], causes, prefix="STR.CONC",
                    unit="m3")
    with pytest.raises(R.Refused, match="listed twice"):
        R.aggregate(lines + [lines[0]], FAMS, causes, prefix="STR.CONC", unit="m3")


def test_key_map_code_in_two_keys_refused_and_reference_unit():
    lines, causes = villa()
    a = R.aggregate(lines, FAMS, causes, prefix="STR.CONC", unit="m3")
    with pytest.raises(R.Refused, match="two keys"):
        R.compare([{"key": "A", "reference_id": "r", "item_codes": ["STR.CONC.COLUMN"]},
                   {"key": "B", "reference_id": "r", "item_codes": ["STR.CONC.COLUMN"]}],
                  {"r": {"qty": 1, "unit": "m3"}}, a["codes"], unit="m3")
    with pytest.raises(R.Refused, match="reference unit"):
        R.compare([{"key": "A", "reference_id": "r", "item_codes": ["STR.CONC.COLUMN"]}],
                  {"r": {"qty": 1, "unit": "m2"}}, a["codes"], unit="m3")


def test_mirror_and_order_invariance():
    lines, causes = villa()
    a1 = R.scope_view(R.aggregate(lines, FAMS, causes, prefix="STR.CONC", unit="m3")["total"])
    a2 = R.scope_view(R.aggregate(list(reversed(lines)), FAMS, causes, prefix="STR.CONC", unit="m3")["total"])
    assert a1 == a2


def test_exact_decimal_no_float_drift():
    # 0.1 + 0.2 as floats is 0.30000000000000004; the stored repr is summed exactly
    lines = [ln("A", "STR.CONC.FOOTING", "RELEASED", 0.1), ln("B", "STR.CONC.FOOTING", "RELEASED", 0.2)]
    a = R.aggregate(lines, FAMS, {}, prefix="STR.CONC", unit="m3")
    assert a["total"]["released"] == X("0.3")


# ------------------------------------------------------------------ development villa, committed files only
sys.path.insert(0, str(ROOT / "research" / "agents_t679"))
import t679_alsenan as A  # noqa: E402


@pytest.fixture(scope="module")
def st():
    return A.build()


def test_committed_outputs_reproduce(st):
    assert (A.OUT_JSON.read_text(encoding="utf-8") == A.dumps(st))
    assert (A.OUT_MD.read_text(encoding="utf-8") == A.md(st))


def test_subtotals_reproduce_line_index_to_last_digit(st):
    idx = json.loads((ROOT / A.INDEX).read_text(encoding="utf-8"))
    lines = [x for x in idx["lines"] if x["item_code"].startswith("STR.CONC")]
    rel = sum((X(repr(x["measured_net"])) for x in lines if x["class"] == "RELEASED"), X(0))
    lo = sum((X(repr(x["held_low"])) for x in lines if x["held_low"] is not None), X(0))
    hi = sum((X(repr(x["held_high"])) for x in lines if x["held_high"] is not None), X(0))
    t = st["trade_total"]
    assert X(t["released"]["m3"]) == rel and X(t["held_bounded"]["low"]) == lo and X(t["held_bounded"]["high"]) == hi
    assert t["lines"] == len(lines) == 596
    fam_rel = sum((X(v["released"]["m3"]) for v in st["families"].values()), X(0))
    code_rel = sum((X(v["released"]["m3"]) for v in st["item_codes"].values()), X(0))
    assert fam_rel == code_rel == rel
    assert sum(v["held_blank"]["lines"] for v in st["families"].values()) == t["held_blank"]["lines"]


def test_every_held_line_has_a_cause_and_counts_equal_census(st):
    assert len(st["held_lines"]) == st["trade_total"]["held_bounded"]["lines"] + st["trade_total"]["held_blank"]["lines"]
    assert all(h["cause_class"] in R.CAUSE_CLASSES and h["cause"] for h in st["held_lines"])
    assert st["candidate"]["master_census_agrees"] == len(st["families"]) == 14
    assert {s["line_id"] for s in st["held_cause_supplement"]} == set(A.SUPPLEMENT)


def test_reference_never_a_quantity_and_pct_rule(st):
    for r in st["reference_apart"]["keys"]:
        held = r["engine"]["held_bounded"]["lines"] + r["engine"]["held_blank"]["lines"]
        assert (r["pct_of_reference"] is None) == (held > 0)
        assert X(r["reference"]) - X(r["engine"]["released"]["m3"]) == X(r["difference_ref_minus_released"])
    slab = next(r for r in st["reference_apart"]["keys"] if r["key"] == "CONC.SLAB")
    assert slab["pct_of_reference"] == "-0.77" and slab["engine"]["verified_share"]["whole"] == "62 / 62"
