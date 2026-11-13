"""T-689 R-T689-1 (joint transfer of a slab-top lower bound to the supporting columns), R-T689-2 (a held range moves
only towards a drawn datum; missing stays HELD, never 0), R-T689-3 (a designer item per cause).
Villa V689 is hand-made (not the development villa); the last tests rebuild the development-villa table from committed
files only (the own DXF read is committed as values; the drawing never is)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t689"))
import t689_rules as R  # noqa: E402

# V689 by hand. Roof plate, finished mark +7.50, slab top not printed. Down-stand beam RB printed 20 x 60 spans the
# clear 4.00 m between columns K1 and K2 (base +3.20 APPROVED, section 0.20 x 0.40 = 0.08 m2). A window drawn under
# RB, jambs 1.00 .. 2.20 from K1's face, head drawn +6.40 (read tolerance 0.010). Column K3 stands elsewhere on the
# plate. Hand: top_RB >= 6.40 - 0.010 + 0.60 = 6.990; K1 / K2 height >= 6.990 - 3.20 = 3.790 m;
# K1 m3 low = 0.08 x 3.790 = 0.303200 (before: a printed head +5.90 + slab 0.15 -> 6.05 - 3.20 = 2.85 -> 0.2280).
BEAM = {"id": "RB", "depth": "0.60", "stand": "DOWN", "span": ("0", "4.00")}
WIN = {"id": "WX", "head_abs": "6.40", "tol": "0.010", "status": "DRAWING-CONFIRMED", "at": ("1.00", "2.20")}


def mirror(h, span="4.00"):
    a, b = h["at"]
    return dict(h, at=(str(X(span) - X(b)), str(X(span) - X(a))))


def test_normal_joint_transfer_by_hand():
    top = R.beam_top_lower_bound(beam=BEAM, heads=[WIN], finished_mark="7.50")
    assert top["state"] == "BOUNDED" and X(top["s_lo"]) == X("6.990000") and top["governing"] == "WX"
    h = R.support_column_height_lo(top_lo=top["s_lo"], base="3.20", supports={"K1", "K2"}, column="K1")
    assert X(h) == X("3.790000")
    after = R.narrow(before=(X("0.228"), X("0.344")), after=(R.q6(X("0.08") * X(h)), X("0.344")),
                     source={"kind": "DRAWN_HEAD_UNDER_PRINTED_BEAM", "ref": "R-T689-1 WX under RB"})
    assert after["state"] == "HELD" and X(after["low"]) == X("0.303200") and X(after["high"]) == X("0.344000")


def test_mirrored_plan_same_bound():
    a = R.beam_top_lower_bound(beam=BEAM, heads=[WIN], finished_mark="7.50")
    b = R.beam_top_lower_bound(beam=BEAM, heads=[mirror(WIN)], finished_mark="7.50")
    assert a["s_lo"] == b["s_lo"]


def test_highest_governs_and_order_free():
    w2 = dict(WIN, id="WY", head_abs="6.45", tol="0.020", at=("2.50", "3.10"))
    a = R.beam_top_lower_bound(beam=BEAM, heads=[WIN, w2])
    b = R.beam_top_lower_bound(beam=BEAM, heads=[w2, WIN])
    assert a == b and X(a["s_lo"]) == X("7.030000") and a["governing"] == "WY"


@pytest.mark.parametrize("bad, msg", [
    (dict(WIN, status="ASSUMED - OWNER-APPROVED"), "cannot bound"),
    (dict(WIN, at=("3.50", "4.30")), "not inside the clear span"),
])
def test_adverse_heads_refused(bad, msg):
    with pytest.raises(R.Refused, match=msg):
        R.beam_top_lower_bound(beam=BEAM, heads=[bad])


@pytest.mark.parametrize("beam, msg", [
    (dict(BEAM, stand="OPEN"), "not settled"),
    (dict(BEAM, stand="UP"), "not settled"),
    (dict(BEAM, depth=None), "not printed"),
    (dict(BEAM, depth="600"), "in metres"),
])
def test_adverse_beam_refused(beam, msg):
    with pytest.raises(R.Refused, match=msg):
        R.beam_top_lower_bound(beam=beam, heads=[WIN])


def test_contradiction_flagged_not_bounded():
    top = R.beam_top_lower_bound(beam=dict(BEAM, depth="1.20"), heads=[dict(WIN, head_abs="6.40")], finished_mark="7.50")
    assert top["state"] == "FLAGGED"


def test_non_support_column_refused_and_plate_named():
    with pytest.raises(R.Refused, match="not a support"):
        R.support_column_height_lo(top_lo="6.99", base="3.20", supports={"K1", "K2"}, column="K3")
    p = R.plate_transfer(top_lo="6.99", base="3.20", one_plane=False, why_not="thickness printed inside the plate")
    assert p == {"state": "REFUSED", "why": "thickness printed inside the plate"}
    assert R.plate_transfer(top_lo="6.99", base="3.20", one_plane=True) == {"state": "BOUNDED", "h_lo": X("3.790000")}


@pytest.mark.parametrize("after, source, msg", [
    ((X("0.20"), X("0.344")), {"kind": "DRAWN", "ref": "x"}, "widening"),
    ((X("0.30"), X("0.40")), {"kind": "DRAWN", "ref": "x"}, "widening"),
    ((X("0.286"), X("0.286")), {"kind": "MIDPOINT", "ref": "mid"}, "not a drawing datum"),
    ((X("0.30"), X("0.344")), {"kind": "FREELANCER", "ref": "his row"}, "not a drawing datum"),
    ((X("0.30"), X("0.344")), {"kind": "SCALED_NTS", "ref": "section scaled"}, "not a drawing datum"),
    ((X("0.30"), X("0.344")), {"kind": "DRAWN"}, "named"),
    ((None, X("0.344")), {"kind": "DRAWN", "ref": "x"}, "cannot be dropped"),
    ((X("0"), X("0.344")), {"kind": "DRAWN", "ref": "x"}, "never 0"),
])
def test_adverse_narrowing_refused(after, source, msg):
    with pytest.raises(R.Refused, match=msg):
        R.narrow(before=(X("0.228"), X("0.344")), after=after, source=source)


def test_close_only_on_equal_ends_and_missing_top_stays_held():
    c = R.narrow(before=(X("0.228"), X("0.344")), after=(X("0.30"), X("0.30")),
                 source={"kind": "PRINTED_LEVEL", "ref": "slab top +6.95 printed"})
    assert c["state"] == "CLOSED"
    k = R.keep((X("0.228"), X("0.344")), "D-99 roof slab top not printed")
    assert k["state"] == "HELD" and X(k["low"]) > 0
    k2 = R.keep((None, None), "D-99 top datum missing")
    assert k2["state"] == "HELD" and k2["low"] is None and k2["high"] is None  # blank, never 0
    with pytest.raises(R.Refused):
        R.keep((X("0.228"), X("0.344")), "")
    with pytest.raises(R.Refused, match="never 0"):
        R.keep((X("0"), X("0")), "D-99")


def test_register_gap_per_cause_and_width_share():
    lines = [{"line_id": "A", "causes": [{"kind": "SECTION", "item": None}, {"kind": "TOP DATUM", "item": "D-9"}]},
             {"line_id": "B", "causes": [{"kind": "DEPTH", "item": "D-8"}]}, {"line_id": "C", "causes": []}]
    assert R.register_gaps(lines, {"D-9", "D-8"}) == [("A", "SECTION"), ("C", "NO_CAUSE")]
    top, tot = R.width_share([{"line_id": "a", "low": "0", "high": "0.5"}, {"line_id": "b", "low": "0.1", "high": "0.4"},
                              {"line_id": "c", "low": "0.2", "high": "0.3"}])
    assert top == ["a", "b"] and tot == X("0.900000")


# ---------------------------------------------------------------------------------------------- development villa
sys.path.insert(0, str(ROOT / "research" / "agents_t689"))
import t689_alsenan as A  # noqa: E402


@pytest.fixture(scope="module")
def res():
    return A.build()


def test_dev_outputs_reproduce(res):
    js = json.dumps(res, indent=1, sort_keys=True, default=str) + "\n"
    assert (ROOT / "research/agents_t689/out/T689_HELD_RANGES.json").read_text() == js
    assert (ROOT / "research/agents_t689/out/T689_HELD_RANGES.md").read_text() == A.md(res)


def test_dev_totals_equal_index(res):
    idx = json.loads((ROOT / "research/agents_t682/out/LINE_INDEX_V3_0_67.json").read_text())
    for ic, f in res["families"].items():
        L = [l for l in idx["lines"] if l["item_code"] == ic and l["class"] == "HELD" and l["held_low"] is not None]
        assert f["bounded_lines"] == len(L)
        assert X(f["before"][0]) == sum((X(str(l["held_low"])) for l in L), X(0)).quantize(X("0.000001"))
    assert res["families"]["STR.CONC.COLUMN"]["width_before"] == "3.005900"
    assert res["families"]["STR.CONC.BEAM"]["width_before"] == "2.429481"


def test_dev_b8_bound_and_only_its_support_moves(res):
    b = res["b8_bound"]
    assert b["s_lo"] == "12.937000" and b["governing"] == "W28" and b["h_lo_412"] == X("3.287000")
    assert b["plate_transfer"]["state"] == "REFUSED"
    moved = [r for r in res["lines"] if r["after"] != r["before"]]
    assert [r["line_id"] for r in moved] == ["L-919a5749ef79759e01ca"]
    assert moved[0]["after"] == ["0.328700", "0.425000"]
    assert res["families"]["STR.CONC.COLUMN"]["width_reduced_m3"] == "0.025700"
    assert res["families"]["STR.CONC.BEAM"]["width_reduced_m3"] == "0.000000"
    assert res["conditional_on_one_plane_m3"] == "0.133640"


def test_dev_every_top_line_has_items_except_named_gap(res):
    assert res["register_gaps"] == [["L-541c7e565bb93ecdb78b", "SECTION"]]
    for r in res["lines"]:
        assert r["after_state"] == "HELD" and X(r["after"][1]) > 0


# ---- next related item: blank conflict lines bounded (V689 by hand: column K4 drawn 0.20 x 0.40, schedule 0.25 x
# 0.50; annex height 3.10 .. 3.85 from a drawn head under a printed beam): 0.08 x 3.10 = 0.248 .. 0.125 x 3.85 = 0.48125
def test_conflict_bound_by_hand_and_order_free():
    a = R.conflict_bound(areas=(X("0.08"), X("0.125")), height=(X("3.10"), X("3.85")), item="D-9")
    b = R.conflict_bound(areas=(X("0.125"), X("0.08")), height=(X("3.10"), X("3.85")), item="D-9")
    assert a == b and a["low"] == X("0.248000") and a["high"] == X("0.481250") and a["state"] == "HELD"


@pytest.mark.parametrize("areas, height", [((X("0.08"), None), (X("3.1"), X("3.85"))),
                                           ((X("0.08"), X("0.125")), (None, X("3.85"))),
                                           ((X("0.08"), X("0.125")), None)])
def test_conflict_bound_missing_stays_blank_never_0(areas, height):
    r = R.conflict_bound(areas=areas, height=height, item="D-9")
    assert r["state"] == "HELD" and r["low"] is None and r["high"] is None


def test_conflict_bound_adverse():
    with pytest.raises(R.Refused):
        R.conflict_bound(areas=(X("0.08"), X("0.125")), height=(X("3.85"), X("3.10")), item="D-9")
    with pytest.raises(R.Refused):
        R.conflict_bound(areas=(X("80000"), X("0.125")), height=(X("3.10"), X("3.85")), item="D-9")  # mm2 not m2


def test_dev_blank_lines_bounded(res):
    b = res["blank_to_bounded"]
    assert b["column_blank_before"] == 7 and b["column_blank_after"] == 2
    assert (b["low"], b["high"]) == ("1.382780", "2.231250")
    got = {r["line_id"]: tuple(r["after"]) for r in b["lines"]}
    assert got["L-694a75c84dd6e4bb4491"] == ("0.263520", "0.506250")
    assert got["L-bc01297b1c4a4c45a15f"] == ("0.328700", "0.510000")
    # none of the five is in D-66's registered handle list: a register gap each (R-T689-3)
    assert len(b["register_gaps"]) == 5
