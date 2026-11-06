"""T-573: ceilings vs a reference takeoff by room group and face class (R-T573-1). Synthetic villa "C573" (not the
training villa) by hand, orientation / unit / missing-data adverse cases; then the development villa: the candidate's
ceiling lines (V3.0.58) against the freelancer's decor, paint and plaster rows (repository files only)."""
from __future__ import annotations

import json
import re
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t573"))
import t573_rules as R  # noqa: E402
import t573_alsenan as A  # noqa: E402

D = Decimal

# ---- villa "C573" (hand) --------------------------------------------------------------------------------------------
# R1 bedroom 4.00 x 3.50 = 14.00 m2 board; beam along the 4.00 side, bulkhead 0.40 deep x 0.30 drop:
#    vertical face 4.00 x 0.30 = 1.20 m2 (BULKHEAD, its own line); the board stays 14.00 (the soffit under the drop is
#    still board, the room area does not change).
# H1 hall 6.00 x 5.00 = 30.00 less light well 2.00 x 1.50 = 3.00 (NO_CEILING) less stair zone 1.00 x 3.00 = 3.00
#    (STAIR_SOFFIT class, HELD) = 24.00 m2 board.
# His rows: r1 bedroom 14.20, r2 hall 30.00 (whole room), c1 cornice 15.00 lm; his paint = 44.20 + 0.10 x 15.00 = 45.70.
# By hand (ours - his): R1 14.00 - 14.20 = -0.20 (room size, UNRESOLVED, -1.41 %); H1 24.00 - 30.00 = -6.00 =
#    light well -3.00 ENGINE_RIGHT + stair zone -3.00 HELD (0 .. 3.00); board total 38.00 - 44.20 = -6.20;
#    bulkhead +1.20 (not in his rows); cove 0 - 15.00 lm HELD (no detail); paint 39.20 - 45.70 = -6.50 =
#    -6.20 board + 1.20 bulkhead - 1.50 his cove strips.
R1 = [("0", "0"), ("4.00", "0"), ("4.00", "3.50"), ("0", "3.50")]
H1 = [("0", "0"), ("6.00", "0"), ("6.00", "5.00"), ("0", "5.00")]
WELL = [("1", "1"), ("3", "1"), ("3", "2.5"), ("1", "2.5")]
STAIR = [("4.5", "1"), ("5.5", "1"), ("5.5", "4"), ("4.5", "4")]


def lines():
    return {"Lr1": {"class": "BOARD", "unit": "m2", "value": "14.00", "status": "DRAWING-CONFIRMED"},
            "Lh1": {"class": "BOARD", "unit": "m2", "value": "24.00", "status": "DRAWING-CONFIRMED"},
            "Lbk": {"class": "BULKHEAD", "unit": "m2", "value": "1.20", "status": "ASSUMED - OWNER-APPROVED"},
            "Lst": {"class": "STAIR_SOFFIT", "unit": "m2", "value": None, "status": "HELD"}}


def rows():
    return {"r1": {"unit": "m2", "value": "14.20"}, "r2": {"unit": "m2", "value": "30.00"},
            "c1": {"unit": "lm", "value": "15.00"}}


def groups():
    return [
        {"id": "R1", "unit": "m2", "lines": ["Lr1"], "rows": ["r1"],
         "causes": [{"label": "room size", "verdict": "UNRESOLVED", "amount": "-0.20", "source": "hand"}]},
        {"id": "H1", "unit": "m2", "lines": ["Lh1"], "rows": ["r2"],
         "causes": [{"label": "light well: no ceiling", "verdict": "ENGINE_RIGHT", "amount": "-3.00", "source": "h"},
                    {"label": "stair zone", "verdict": "HELD", "amount": "-3.00", "bound": ("0", "3.00"),
                     "source": "h"}]},
        {"id": "BULK", "unit": "m2", "lines": ["Lbk"], "rows": [],
         "causes": [{"label": "bulkhead faces", "verdict": "NOT_IN_HIS_ROWS", "amount": "1.20", "source": "h"}]},
        {"id": "STAIR", "unit": "m2", "lines": ["Lst"], "rows": [],
         "causes": [{"label": "stair soffit held", "verdict": "HELD", "amount": "0", "bound": ("0", None),
                     "source": "h"}]},
        {"id": "COVE", "unit": "lm", "lines": [], "rows": ["c1"],
         "causes": [{"label": "no cove detail", "verdict": "HELD", "amount": "-15.00", "bound": ("0", None),
                     "source": "h"}]},
    ]


def test_board_area_by_hand_and_bulkhead_apart():
    assert R.board_area(R1) == D("14.00")
    assert R.bulkhead_face("4.00", "0.30") == D("1.20")
    assert R.board_area(H1, openings=[WELL], other_class=[STAIR]) == D("24.00")
    assert R.board_line("14.00", [("BOARD", "14.00")]) == D("14.00")
    assert R.paint_of("14.00", "1.20") + R.paint_of("24.00") == D("39.20")


def test_bulkhead_vertical_added_into_ceiling_area_refused():
    with pytest.raises(R.RuleError, match="BULKHEAD face inside a BOARD"):
        R.board_line("15.20", [("BOARD", "14.00"), ("BULKHEAD", "1.20")])
    with pytest.raises(R.RuleError, match="COVE face inside a BOARD"):
        R.board_line("15.50", [("BOARD", "14.00"), ("COVE", "1.50")])     # a 0.10 strip by convention


@pytest.mark.parametrize("tf", [
    lambda x, y: (-x, y),                                   # mirror
    lambda x, y: (y, -x),                                   # -90 deg
    lambda x, y: (x * D("0.8") - y * D("0.6") + 7, x * D("0.6") + y * D("0.8") - 3),   # 36.87 deg + translation
    lambda x, y: (-(x * D("0.6") + y * D("0.8")), x * D("0.8") - y * D("0.6")),        # mirror + rotation
])
def test_orientation_invariant(tf):
    t = lambda poly: [tf(D(a), D(b)) for a, b in poly]   # noqa: E731
    assert R.board_area(t(H1), openings=[t(WELL)], other_class=[t(STAIR)]) == D("24.00")
    assert R.board_area(t(R1)) == D("14.00")


def test_units_mm_and_unknown_refused():
    assert R.board_area([(0, 0), (4000, 0), (4000, 3500), (0, 3500)], unit="mm") == D("14.00")
    assert R.bulkhead_face(4000, 300, unit="mm") == D("1.20")
    with pytest.raises(R.RuleError, match="unknown"):
        R.board_area(R1, unit="cm")
    with pytest.raises(R.RuleError):
        R.board_area(R1, openings=[H1])                     # deduction larger than the room


def test_reconcile_by_hand():
    t = R.reconcile(groups(), lines(), rows())
    g = {x["id"]: x for x in t["groups"]}
    assert g["R1"]["gap"] == D("-0.20") and g["R1"]["pct"] == D("-1.41")
    assert g["H1"]["gap"] == D("-6.00") and g["H1"]["pct"] is None and g["H1"]["held_bound"] == [0, D("3.00")]
    assert g["BULK"]["pct"] is None                         # scope difference: no %
    assert g["COVE"]["held_bound"][1] is None
    assert t["totals"]["m2"] == {"ours": D("39.20"), "his": D("44.20")}
    assert t["totals"]["lm"] == {"ours": D("0"), "his": D("15.00")}
    assert R.like_for_like(t) == (D("14.00"), D("14.20"), D("-0.20"), D("-1.41"))
    # paint view by hand: 39.20 - 45.70 = -6.20 + 1.20 - 1.50
    assert D("39.20") - D("45.70") == D("-6.20") + D("1.20") - D("1.50")


def _mut(fn):
    g, ln, rw = groups(), lines(), rows()
    fn(g, ln, rw)
    return lambda: R.reconcile(g, ln, rw)


@pytest.mark.parametrize("name,fn,msg", [
    ("lm row in an m2 group", lambda g, ln, rw: g[0]["rows"].append("c1"), "m2 and lm|compared in an m2"),
    ("line twice", lambda g, ln, rw: g[1]["lines"].append("Lr1"), "two groups"),
    ("row twice", lambda g, ln, rw: g[1]["rows"].append("r1"), "two groups"),
    ("not closing", lambda g, ln, rw: g[0]["causes"][0].update(amount="-0.10"), "close exactly"),
    ("held outside bound", lambda g, ln, rw: (g[1]["causes"][1].update(amount="-4.00"),
                                              g[1]["causes"][0].update(amount="-2.00")), "outside its bound"),
    ("held line with a value", lambda g, ln, rw: ln["Lst"].update(value="3.00"), "HELD with a value"),
    ("missing as 0", lambda g, ln, rw: ln["Lr1"].update(value=None), "missing never becomes 0"),
    ("VERIFIED by a worker", lambda g, ln, rw: ln["Lr1"].update(status="VERIFIED"), "Checker"),
    ("estimated shown verified", lambda g, ln, rw: ln["Lbk"].update(status="VERIFIED"), "Checker"),
    ("% on a held group", lambda g, ln, rw: g[1].update(pct=True), "bound HELD before %"),
    ("unnamed residual", lambda g, ln, rw: g[0]["causes"][0].update(label=" "), "unnamed"),
    ("line left out", lambda g, ln, rw: g[2]["lines"].remove("Lbk") or g[2]["causes"][0].update(amount="0"),
     "not every item used once"),
    ("cove in m2", lambda g, ln, rw: ln.update(Lcv={"class": "COVE", "unit": "m2", "value": "1.50",
                                                    "status": "ESTIMATED"}), "measured in lm"),
    ("unknown verdict", lambda g, ln, rw: g[0]["causes"][0].update(verdict="PROBABLY"), "unknown"),
])
def test_adverse(name, fn, msg):
    with pytest.raises(R.RuleError, match=msg):
        _mut(fn)()


def test_none_never_a_number():
    with pytest.raises(R.RuleError, match="never 0"):
        R.D(None)
    with pytest.raises(R.RuleError):
        R.compare_units("m2", "lm")


# ---- development villa (repository files only) ---------------------------------------------------------------------
@pytest.fixture(scope="module")
def built():
    return A.build()


def test_rebuild_byte_identical(built):
    assert A.OUT.read_text(encoding="utf-8") == A.dump(built)


def test_board_totals_and_closure(built):
    b = built["board"]
    assert b["totals"]["m2"] == {"ours": "366.891177", "his": "409.58", "gap": "-42.688823", "pct": "-10.42"}
    s = sum(D(g["gap"]) for g in b["groups"])
    assert s == D("-42.688823")
    for g in b["groups"]:
        assert sum(D(c["amount"]) for c in g["causes"]) == D(g["gap"])
    assert b["like_for_like_no_held"] == {"ours": "109.691183", "his": "110.05", "gap": "-0.358817", "pct": "-0.33"}
    rec = next(g for g in b["groups"] if g["id"].startswith("GF reception"))
    assert rec["gap"] == "-39.137907" and rec["held_bound"] == ["0", "26.6465"] and rec["pct"] is None


def test_every_ceiling_line_once(built):
    ids = [l for sec in ("board", "classes", "paint") for g in built[sec]["groups"] for l in g["lines"]]
    assert len(ids) == len(set(ids)) == 41 + 14 + 2 + 2 + 31     # FIN.CEILING incl. 5 exterior, bulkhead, stair, dome, paint


def test_classes_and_paint(built):
    c = {g["id"].split(" ")[0]: g for g in built["classes"]["groups"]}
    assert c["BULKHEAD"]["gap"] == "27.9345" and c["BULKHEAD"]["pct"] is None
    assert c["COVE"]["unit"] == "lm" and c["COVE"]["his"] == "427.46"
    assert c["STAIR"]["his"] == "39.99" and [x["amount"] for x in c["STAIR"]["causes"]] == ["-22.149034", "-17.840966"]
    assert c["EXTERIOR"]["gap"] == "25.292" and c["EXTERIOR"]["pct"] is None
    p = built["paint"]["groups"][0]
    assert p["gap"] == "-57.499323"
    assert [x["amount"] for x in p["causes"]] == ["-42.688823", "27.9345", "-42.745", "0"]
    assert len(built["paint"]["room_check"]) == 31


def test_no_workbook_text_or_coordinates(built):
    txt = A.OUT.read_text(encoding="utf-8") + (ROOT / "research/agents_t573/t573_alsenan.py").read_text("utf-8")
    assert not re.search("[؀-ۿ]", txt)
