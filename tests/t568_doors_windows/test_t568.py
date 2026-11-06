"""T-568: doors and windows by type, nr and m2 apart, every opening once by id (R-T568-1). Synthetic villa "B568"
(not the training villa), hand calculations, adverse cases; then the development villa: the candidate's door / window
lines rebuilt from their openings (always), and the comparison with the freelancer (private workbooks: skipped
without them)."""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t568"))
import t568_rules as R  # noqa: E402
import t568_alsenan as A  # noqa: E402

ALU, PVC, WIN = "DOOR.EXTERNAL.ALUMINIUM", "DOOR.INTERNAL.PVC", "WINDOW.ALUMINIUM"

# ---- villa "B568" (hand) -----------------------------------------------------------------------------------------
# Door marks: DA aluminium 1.00 (head Q-55 C 2.20 -> 2.200), DB internal 0.80 (DB1 GF, DB2 1F -> 1.760 each),
# DC internal 0.90 (1F -> 1.980). Window marks: WA 1.20 x 1.50 printed (1.800; read on the GF plan AND the elevation:
# one opening), WB arched 1.00 wide, crown of the opening 2.00 (Q-32 A enclosing rectangle 2.000), WH 1.50 HELD
# (height not printed; bounds 2.25 .. 3.00).
# His rows: r1 GF ALU 1 x 1.00 x 2.40; r2 GF PVC 1 x 0.80 x 2.40; r3 1F PVC 1 x 0.90 x 2.40; r4 GF WIN 1 x 1.20 x 2.00;
# r5 1F WIN 1 x 1.00 x 2.00; r6 1F WIN 1 x 1.50 x 2.00; r7 2F WIN 1 x 0.60 x 0.80.
# By hand (ours - his):
#   ALU  nr 1 - 1 = 0;   m2 2.200 - 2.400 = -0.200 = DA height (Q-55 C)                     RULE_DIFFERENCE
#   PVC  nr 3 - 2 = +1 (DB2 drawn leaf, ENGINE_RIGHT); m2 5.500 - 4.080 = +1.420 =
#        DB1 height 1.760 - 1.920 = -0.160 + DC height 1.980 - 2.160 = -0.180 (RULE_DIFFERENCE -0.340) + DB2 +1.760
#   WIN  nr 3 - 4 = -1 (his 0.60 x 0.80 on 2F, no opening of ours: UNRESOLVED); m2 3.800 - 7.880 = -4.080 =
#        WA height 1.800 - 2.400 = -0.600 ENGINE_RIGHT; WB 2.000 = 2.000; WH HELD -3.000; his only -0.480 UNRESOLVED
OPS = [
    {"id": "DA", "storey": "GF", "cls": ALU, "w_m": "1.00", "area_m2": "2.200", "basis": "Q55C", "source": "plan"},
    {"id": "DB1", "storey": "GF", "cls": PVC, "w_m": "0.80", "area_m2": "1.760", "basis": "Q55C", "source": "plan"},
    {"id": "DB2", "storey": "1F", "cls": PVC, "w_m": "0.80", "area_m2": "1.760", "basis": "Q55C", "source": "plan"},
    {"id": "DC", "storey": "1F", "cls": PVC, "w_m": "0.90", "area_m2": "1.980", "basis": "Q55C", "source": "plan"},
    {"id": "WA", "storey": "GF", "cls": WIN, "w_m": "1.20", "area_m2": "1.800", "basis": "PRINTED", "source": "plan"},
    {"id": "WA", "storey": "GF", "cls": WIN, "w_m": "1.20", "area_m2": "1.800", "basis": "PRINTED",
     "source": "elevation"},
    {"id": "WB", "storey": "1F", "cls": WIN, "w_m": "1.00", "area_m2": "2.000", "basis": "Q32A", "source": "elev"},
    {"id": "WH", "storey": "1F", "cls": WIN, "w_m": "1.50", "area_m2": None, "basis": "HELD", "source": "plan",
     "bounds": ["2.25", "3.00"]},
]
ROWS = [
    {"row": "r1", "storey": "GF", "cls": ALU, "n": 1, "w_m": "1.00", "h_m": "2.40", "m2": "2.40"},
    {"row": "r2", "storey": "GF", "cls": PVC, "n": 1, "w_m": "0.80", "h_m": "2.40", "m2": "1.92"},
    {"row": "r3", "storey": "1F", "cls": PVC, "n": 1, "w_m": "0.90", "h_m": "2.40", "m2": "2.16"},
    {"row": "r4", "storey": "GF", "cls": WIN, "n": 1, "w_m": "1.20", "h_m": "2.00", "m2": "2.40"},
    {"row": "r5", "storey": "1F", "cls": WIN, "n": 1, "w_m": "1.00", "h_m": "2.00", "m2": "2.00"},
    {"row": "r6", "storey": "1F", "cls": WIN, "n": 1, "w_m": "1.50", "h_m": "2.00", "m2": "3.00"},
    {"row": "r7", "storey": "2F", "cls": WIN, "n": 1, "w_m": "0.60", "h_m": "0.80", "m2": "0.48"},
]
PAIRS = [("DA", "r1", ""), ("DB1", "r2", ""), ("DC", "r3", ""), ("WA", "r4", ""), ("WB", "r5", ""), ("WH", "r6", "")]
VERD = {"DB2": {"count": "ENGINE_RIGHT"}, "DB1": {"count": "ENGINE_RIGHT"}}


def table(pairs=PAIRS, ops=OPS, rows=ROWS):
    return R.type_table(openings=R.openings_once(ops), units=R.his_units(rows), pairs=pairs, verdicts=VERD)


def test_b568_by_hand():
    t = table()
    assert t[ALU]["nr"]["ours_minus_his"] == 0 and t[ALU]["nr"]["by_cause"] == {}
    assert Decimal(t[ALU]["m2"]["ours_minus_his"]) == Decimal("-0.2") and {k: Decimal(v) for k, v in t[ALU]["m2"]["by_cause"].items()} == {"RULE_DIFFERENCE": Decimal("-0.2")}
    assert t[PVC]["nr"]["ours_minus_his"] == 1 and t[PVC]["nr"]["by_cause"] == {"ENGINE_RIGHT": "1"}
    assert Decimal(t[PVC]["m2"]["ours_minus_his"]) == Decimal("1.420")
    assert {k: Decimal(v) for k, v in t[PVC]["m2"]["by_cause"].items()} == {
        "ENGINE_RIGHT": Decimal("1.760"), "RULE_DIFFERENCE": Decimal("-0.340")}
    w = t[WIN]
    assert w["nr"]["ours_settled"] == 3 and w["nr"]["his"] == 4 and w["nr"]["by_cause"] == {"UNRESOLVED": "-1"}
    assert Decimal(w["m2"]["ours_settled"]) == Decimal("3.800") and Decimal(w["m2"]["his"]) == Decimal("7.88")
    assert {k: Decimal(v) for k, v in w["m2"]["by_cause"].items()} == {
        "ENGINE_RIGHT": Decimal("-0.600"), "HELD": Decimal("-3.00"), "UNRESOLVED": Decimal("-0.48")}
    assert w["m2"]["ours_held"] == ["WH"] and w["m2"]["ours_held_bounds"] == {"WH": ["2.25", "3.00"]}


def test_one_opening_on_two_plans_counted_once():
    ops = R.openings_once(OPS)
    assert list(ops).count("WA") == 1 and ops["WA"]["sources"] == ["plan", "elevation"]
    assert table()[WIN]["nr"]["ours_settled"] == 3


def test_opening_counted_on_two_storeys_refused():
    bad = OPS + [dict(OPS[4], storey="1F", source="1F plan")]
    with pytest.raises(R.RuleError, match="two storeys"):
        R.openings_once(bad)


def test_two_readings_with_different_sizes_refused():
    bad = OPS + [dict(OPS[4], area_m2="2.400", source="elevation 2")]
    with pytest.raises(R.RuleError, match="differ on area_m2"):
        R.openings_once(bad)


def test_area_compared_as_nr_refused():
    t = table()
    assert Decimal(R.compare(t, WIN, "m2", "m2")["his"]) == Decimal("7.88")
    with pytest.raises(R.RuleError, match="never mixed"):
        R.compare(t, WIN, "nr", "m2")
    with pytest.raises(R.RuleError, match="never mixed"):
        R.compare(t, PVC, "m2", "nr")


def test_nr_and_m2_rows_never_mixed():
    for cls, rec in table().items():
        for r in rec["rows"]:
            assert r["unit"] in ("nr", "m2")
            if r["unit"] == "nr":
                assert Decimal(r["delta"]) in (Decimal(-1), Decimal(0), Decimal(1))


def test_pairing_invariance_and_named_move():
    # the other consistent pairing: his 0.80 GF unit is DB2's (storey unknown on his row)
    rows = [dict(r, storey=None) if r["row"] == "r2" else r for r in ROWS]
    t1 = table(rows=rows)
    t2 = table(pairs=[("DB2" if p[0] == "DB1" else p[0], p[1], p[2]) for p in PAIRS], rows=rows)
    move = R.pairing_move(t1, t2, PVC)
    assert move == {"nr": {}, "m2": {}}          # DB1 and DB2 are the same size: nothing moves
    assert t1[PVC]["m2"]["ours_minus_his"] == t2[PVC]["m2"]["ours_minus_his"]


def test_pairing_that_changes_a_total_refused():
    t1 = table()
    t2 = table(ops=[dict(o, area_m2="1.980", w_m="0.90") if o["id"] == "DB2" else o for o in OPS])
    with pytest.raises(R.RuleError, match="change the class total"):
        R.pairing_move(t1, t2, PVC)


def test_row_arithmetic_checked():
    bad = [dict(ROWS[0], m2="2.20")]
    with pytest.raises(R.RuleError, match="printed"):
        R.his_units(bad)


def test_unit_used_twice_refused():
    with pytest.raises(R.RuleError, match="no free unit"):
        table(pairs=PAIRS + [("DB2", "r2", "")])


def test_class_and_storey_must_match():
    with pytest.raises(R.RuleError, match="classes differ"):
        table(pairs=[("DA", "r2", "")])
    with pytest.raises(R.RuleError, match="paired with his row"):
        table(pairs=[("DB2", "r2", "")])


def test_held_never_zero_and_mm_refused():
    with pytest.raises(R.RuleError, match="HELD opening has no area"):
        R.openings_once([dict(OPS[7], area_m2="0")])
    with pytest.raises(R.RuleError, match="mm"):
        R.openings_once([dict(OPS[0], w_m="1000")])
    with pytest.raises(R.RuleError, match="None"):
        R.D(None)


def test_count_held_opening():
    ops = OPS + [{"id": "WX", "storey": "GF", "cls": WIN, "w_m": "6.00", "area_m2": None, "basis": "HELD",
                  "count_held": True, "source": "plan"}]
    rows = ROWS + [{"row": "r8", "storey": "GF", "cls": WIN, "n": 1, "w_m": "6.00", "h_m": "4.00", "m2": "24.00"}]
    t = table(pairs=PAIRS + [("WX", "r8", "")], ops=ops, rows=rows)
    assert t[WIN]["nr"]["by_cause"] == {"HELD": "-1", "UNRESOLVED": "-1"}
    assert Decimal(t[WIN]["m2"]["by_cause"]["HELD"]) == Decimal("-27.00")


# ---- development villa -------------------------------------------------------------------------------------------
def test_candidate_lines_rebuilt_from_their_openings():
    doc = A.build(None, None)
    keys = {c["line"] for c in doc["candidate_closure"]}
    assert "WINDOW.ALUMINIUM|1F|m2|HELD" in keys and "DOOR.EXTERNAL.ALUMINIUM|GF|pcs|SETTLED_DRAWING_CONFIRMED" in keys
    assert len(doc["drawn_leaves"]["1F internal"]) == 10 and len(doc["drawn_leaves"]["GF external"]) == 5


@pytest.mark.skipif(not (A.ALU_DEFAULT.exists() and A.MAS_DEFAULT.exists()),
                    reason="the freelancer workbooks are private (.work/private)")
def test_development_villa_against_the_freelancer():
    doc = A.build(A.ALU_DEFAULT, A.MAS_DEFAULT)
    s = doc["supply_aluminium"]
    assert (s[ALU]["nr"]["ours_settled"], s[ALU]["nr"]["his"]) == (6, 5)
    assert (s[ALU]["m2"]["ours_settled"], s[ALU]["m2"]["his"]) == ("12.760", "12.0")
    assert (s[WIN]["nr"]["ours_settled"], s[WIN]["nr"]["his"]) == (28, 29)
    assert Decimal(s[WIN]["m2"]["by_cause"]["HELD"]) == Decimal("-36.669")
    assert doc["windows_like_for_like"]["with_Q76A_W17"]["diff"] == "-3.555"
    m = doc["masonry_deduction_doors"][PVC]
    assert (m["nr"]["ours_settled"], m["nr"]["his"]) == (20, 18)
