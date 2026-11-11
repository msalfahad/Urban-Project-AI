"""T-711: one-sided bounds / named blanks of the concrete blank tail (R-T711-1 .. 3). Villa V711 is hand-made (not the
development villa): a lift raft H 0.60 founded at least 1.20 m below EG on a 0.15 m stack, GF slab top +0.60, four
lift necks 0.30 x 0.30 / 0.30 x 0.40 (two printed readings), pit ring 0.80 m2 net; a stair flight read two ways; a roof
parapet of two runs. The last tests rebuild the development-villa census from committed files only."""
from __future__ import annotations

import json
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t711"))
import t711_rules as R  # noqa: E402

V = dict(min_depth="1.20", stack="0.15", H="0.60", supplier_item="V711-L1 pit depth (supplier)")


# ------------------------------------------------------------------ R-T711-1 normal (hand)
def test_raft_top_highest_hand():
    assert R.raft_top_highest(min_depth="1.20", stack="0.15", H="0.60") == X("-0.45")


def test_neck_floor_takes_smallest_section_hand():
    b = R.below_supplier_raft(top_level="0.60", areas_m2=["0.12", "0.09"], **V)
    assert b["h_low_m"] == X("1.05")                     # +0.60 - (-0.45)
    assert b["area_min_m2"] == X("0.09")
    assert b["at_least"] == X("0.094500") and b["at_most"] is None and "supplier" in b["open_by"]


def test_pit_ring_floor_hand():
    b = R.below_supplier_raft(top_level="0.60", areas_m2=["0.80"], **V)
    assert b["at_least"] == X("0.840000")                 # 0.80 x 1.05


def test_floor_is_directed_down():
    b = R.below_supplier_raft(top_level="0.60", areas_m2=["0.0333333"], **V)
    assert b["at_least"] == X("0.034999")                 # 0.034999965 floored, never rounded up


def test_deeper_pit_only_raises_the_floor():
    shallow = R.below_supplier_raft(top_level="0.60", areas_m2=["0.80"], **V)["at_least"]
    deeper = R.below_supplier_raft(top_level="0.60", areas_m2=["0.80"], **{**V, "min_depth": "1.80"})["at_least"]
    assert deeper > shallow


# ------------------------------------------------------------------ R-T711-1 adverse
def test_upper_end_refused_while_supplier_depth():
    with pytest.raises(R.Refused):
        R.below_supplier_raft(top_level="0.60", areas_m2=["0.80"], upper="2.00", **V)


@pytest.mark.parametrize("bad", [dict(min_depth=None), dict(stack=None), dict(H=None), dict(H="600"),
                                 dict(min_depth="1200"), dict(supplier_item="")])
def test_missing_or_mm_or_unnamed_refused(bad):
    with pytest.raises(R.Refused):
        R.below_supplier_raft(top_level="0.60", areas_m2=["0.80"], **{**V, **bad})


def test_missing_area_and_zero_area_refused():
    with pytest.raises(R.Refused):
        R.below_supplier_raft(top_level="0.60", areas_m2=[], **V)
    with pytest.raises(R.Refused):
        R.below_supplier_raft(top_level="0.60", areas_m2=["0"], **V)


def test_top_below_raft_refused():
    with pytest.raises(R.Refused):
        R.below_supplier_raft(top_level="-0.50", areas_m2=["0.80"], **V)


# ------------------------------------------------------------------ R-T711-2
def test_min_over_readings_hand():
    m = R.min_over_readings({"A": {"flight": "0.50", "turn": "0.10"}, "B": {"flight": "0.40", "turn": "0.25"}})
    assert m["at_least"] == X("0.600000") and m["governing_reading"] == "A"
    assert m["componentwise_min"] == X("0.500000") <= m["at_least"]
    assert m["at_most"] is None


def test_mirrored_readings_same_floor():
    a = R.min_over_readings({"A": {"f": "0.50", "t": "0.10"}, "B": {"f": "0.40", "t": "0.25"}})
    b = R.min_over_readings({"B": {"t": "0.10", "f": "0.50"}, "A": {"t": "0.25", "f": "0.40"}})
    assert a["at_least"] == b["at_least"]


def test_partial_or_mismatched_reading_refused():
    with pytest.raises(R.Refused):
        R.min_over_readings({"A": {"f": "0.50", "t": None}, "B": {"f": "0.40", "t": "0.25"}})
    with pytest.raises(R.Refused):
        R.min_over_readings({"A": {"f": "0.50"}, "B": {"f": "0.40", "t": "0.25"}})


# ------------------------------------------------------------------ parapet floor
def test_parapet_floor_hand():
    f = R.parapet_floor([{"run": "N", "top_lo_m2": "2.00"}, {"run": "E", "top_lo_m2": "1.50"}], "0.30")
    assert f["at_least"] == X("1.050000") and f["at_most"] is None


def test_parapet_run_without_top_refused_never_zero():
    with pytest.raises(R.Refused):
        R.parapet_floor([{"run": "N", "top_lo_m2": None}], "0.30")


def test_parapet_with_no_printed_height_stays_held_with_item():
    b = R.blank_named(item="V711-D2 parapet height above the roof", why="no height printed on any sheet",
                      per_unit="2.00 m2 top per m of height")
    s = R.statement("L-V711-P", "V711#PARAPET", "BLANK_NAMED", item=b["item"])
    assert s["at_least_m3"] is None and s["measured_net"] is None and s["class_after"] == "HELD"


# ------------------------------------------------------------------ R-T711-3 / statement guard
def test_blank_without_item_or_reason_refused():
    with pytest.raises(R.Refused):
        R.blank_named(item="", why="x")
    with pytest.raises(R.Refused):
        R.blank_named(item="D-1", why="")


@pytest.mark.parametrize("kw", [dict(cls="AT_LEAST", at_least="0"), dict(cls="AT_LEAST", at_least=None),
                                dict(cls="AT_LEAST", at_least="0.5", at_most="0.9"),
                                dict(cls="BLANK_NAMED", at_least="0.1", item="D-1"), dict(cls="BLANK_NAMED"),
                                dict(cls="RANGE", at_least="0.1")])
def test_statement_never_zero_never_range(kw):
    cls = kw.pop("cls")
    with pytest.raises(R.Refused):
        R.statement("L-x", "E-x", cls, **kw)


# ------------------------------------------------------------------ development villa (committed files only)
@pytest.fixture(scope="module")
def ledger():
    sys.path.insert(0, str(ROOT / "research" / "agents_t711"))
    import t711_alsenan as A
    return A.build()


def test_census_15_by_id(ledger):
    assert ledger["census"] == {"lines": 15, "at_least": 11, "blank_named": 4}
    assert len({r["line_id"] for r in ledger["lines"]}) == 15


def test_family_floors(ledger):
    f = ledger["families"]
    assert f["STR.CONC.NECK"]["at_least_m3"] == "0.951500"
    assert f["STR.CONC.LIFT"]["at_least_m3"] == "1.903000" and f["STR.CONC.LIFT"]["blank_named"] == 1
    assert f["STR.CONC.PARAPET"]["at_least_m3"] == "8.050942"
    assert f["STR.CONC.STAIR"]["at_least_m3"] == "1.568446" and f["STR.CONC.STAIR"]["blank_named"] == 3


def test_no_line_gets_zero_or_upper_end(ledger):
    for r in ledger["lines"]:
        assert r["at_most_m3"] is None and r["measured_net"] is None
        assert r["at_least_m3"] is None or X(r["at_least_m3"]) > 0
        assert r["item"]


def test_committed_ledger_matches_rebuild(ledger):
    p = ROOT / "research" / "agents_t711" / "out" / "T711_LEDGER.json"
    assert json.loads(p.read_text()) == json.loads(json.dumps(ledger, sort_keys=True, default=str))
