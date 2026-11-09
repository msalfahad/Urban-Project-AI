"""T-559: B9 blockwork leftover (opening census opening by opening, R-T559-1) and the parapet edge-member ownership
check (R-T559-2). Synthetic villa "B559" (not the training villa), hand calculations, adverse cases; then the
development villa from merged repository files (the opening table needs the private workbook rows: skipped without)."""
from __future__ import annotations

import random
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t559"))
import t559_rules as R  # noqa: E402
import t559_alsenan as A  # noqa: E402

# ---- villa "B559" (hand) -----------------------------------------------------------------------------------------
# Engine openings: D1 door 0.90 at the owner fallback head 2.20 (Q-55 C) -> 1.98; W1 window 1.20 printed sill 1.00 /
# head 2.50 -> 1.80; A1 arched window by its true outline 2.00 m2; H1 door HELD (not deducted); D2 door 0.80 -> 1.76
# that he does not deduct. His units: 1.00 x 2.40 (D1), 1.20 x 2.00 (W1), 1.20 x 2.00 (A1), 0.90 x 2.40 (H1),
# 0.60 x 0.80 (no engine opening). Census: engine 7.54, his 9.84 -> -2.30. By hand:
#   D1 width (0.90 - 1.00) x 2.40 = -0.24 UNRESOLVED; height 1.98 - 0.90 x 2.40 = -0.18 RULE_DIFFERENCE
#   W1 height 1.80 - 1.20 x 2.00 = -0.60 ENGINE_RIGHT; A1 outline 2.00 - 2.40 = -0.40 ENGINE_RIGHT
#   H1 -2.16 HELD; D2 +1.76 UNRESOLVED; his 0.60 x 0.80 -0.48 UNRESOLVED       sum -2.30
ENG = [{"id": "D1", "w_m": "0.90", "ded_m2": "1.98", "h_basis": "Q55C"},
       {"id": "W1", "w_m": "1.20", "ded_m2": "1.80", "h_basis": "PRINTED"},
       {"id": "A1", "w_m": None, "ded_m2": "2.00", "h_basis": "OUTLINE"},
       {"id": "H1", "w_m": "0.90", "ded_m2": None, "h_basis": "HELD"},
       {"id": "D2", "w_m": "0.80", "ded_m2": "1.76", "h_basis": "Q55C"}]
HIS = [{"uid": "u1", "w_m": "1.00", "h_m": "2.40"}, {"uid": "u2", "w_m": "1.20", "h_m": "2.00"},
       {"uid": "u3", "w_m": "1.20", "h_m": "2.00"}, {"uid": "u4", "w_m": "0.90", "h_m": "2.40"},
       {"uid": "u5", "w_m": "0.60", "h_m": "0.80"}]
PAIRS = [("D1", "u1", ""), ("W1", "u2", ""), ("A1", "u3", ""), ("H1", "u4", "")]


def census(**kw):
    a = dict(floor="B559", engine=ENG, his=HIS, pairs=PAIRS, engine_census_m2="7.54", his_census_m2="9.84")
    a.update(kw)
    return R.opening_census(**a)


def test_b559_hand_split():
    res = census()
    assert Decimal(res["delta"]) == Decimal("-2.30")
    bc = {k: Decimal(v) for k, v in R.by_cause(res["rows"]).items()}
    assert bc == {"UNRESOLVED": Decimal("-0.24") + Decimal("1.76") - Decimal("0.48"),
                  "RULE_DIFFERENCE": Decimal("-0.18"), "ENGINE_RIGHT": Decimal("-1.00"), "HELD": Decimal("-2.16")}


def test_pair_order_does_not_matter():
    base = R.by_cause(census()["rows"])
    for seed in range(5):
        p = PAIRS[:]
        random.Random(seed).shuffle(p)
        assert R.by_cause(census(pairs=p)["rows"]) == base


def test_width_within_5mm_is_tolerance():
    eng = ENG[:1] + [{"id": "W8", "w_m": "1.501", "ded_m2": "2.2515", "h_basis": "PRINTED"}]
    his = HIS[:1] + [{"uid": "x", "w_m": "1.50", "h_m": "2.00"}]
    res = R.opening_census(floor="B", engine=eng, his=his, pairs=[("D1", "u1", ""), ("W8", "x", "")],
                           engine_census_m2="4.2315", his_census_m2="5.40")
    w = [r for r in res["rows"] if r["name"].startswith("B W8") and r["term"] == "width"]
    assert w[0]["cause"] == "TOLERANCE" and Decimal(w[0]["delta"]) == Decimal("0.002")


def test_held_opening_with_a_deduction_refused():
    eng = [dict(e) for e in ENG]
    eng[3]["ded_m2"] = "2.16"
    with pytest.raises(R.RuleError):
        census(engine=eng, engine_census_m2="9.70")


def test_held_never_agreement_or_zero():
    rows = census()["rows"]
    h = [r for r in rows if r["name"].startswith("B559 H1")]
    assert len(h) == 1 and h[0]["cause"] == "HELD" and Decimal(h[0]["delta"]) == Decimal("-2.16")


def test_opening_paired_twice_refused():
    with pytest.raises(R.RuleError):
        census(pairs=PAIRS + [("D1", "u5", "")])
    with pytest.raises(R.RuleError):
        census(pairs=PAIRS + [("D2", "u1", "")])


def test_census_must_close():
    with pytest.raises(R.RuleError):
        census(engine_census_m2="7.50")
    with pytest.raises(R.RuleError):
        census(his_census_m2="9.80")


@pytest.mark.parametrize("bad", [{"uid": "m", "w_m": "900", "h_m": "2.40"}, {"uid": "m", "w_m": "0.90", "h_m": "2400"},
                                 {"uid": "m", "w_m": None, "h_m": "2.40"}])
def test_mm_and_none_refused(bad):
    with pytest.raises(R.RuleError):
        census(his=HIS + [bad])


# ---- R-T559-2 fixture: parapet 10 m on a 0.20 x 0.55 edge beam, printed 1.00 above the finish --------------------
def test_parapet_on_edge_member_hand():
    r = R.parapet_on_edge_member(length_m="10", h_above_finish_m="1.00", edge_b_m="0.20",
                                 edge_depth_below_slab_top_m="0.55")
    assert Decimal(r["masonry_m2"]) == Decimal("10.00") and Decimal(r["edge_beam_m3"]) == Decimal("1.100")


@pytest.mark.parametrize("datum", ["SLAB_SOFFIT", "MEMBER_SOFFIT", "SLAB_TOP"])
def test_masonry_from_below_the_finish_refused_when_downstand_drawn(datum):
    with pytest.raises(R.RuleError):
        R.parapet_on_edge_member(length_m="10", h_above_finish_m="1.55", edge_b_m="0.20",
                                 edge_depth_below_slab_top_m="0.55", masonry_datum=datum)


def test_edge_member_mm_refused():
    with pytest.raises(R.RuleError):
        R.parapet_on_edge_member(length_m="10000", h_above_finish_m="1.00", edge_b_m="0.20",
                                 edge_depth_below_slab_top_m="0.55")


def _ln(eid, cls, lid):
    return {"item_code": "STR.CONC.BEAM", "element_id": eid, "class": cls, "line_id": lid, "measured_net": 1.1,
            "held_low": None, "held_high": None}


def test_carriage_once_omitted_double():
    bands = [{"storey": "GF", "band": "BAND0001", "mark": "E1", "run": "R1"},
             {"storey": "GF", "band": "BAND0002", "mark": "E2", "run": "R2"}]
    lines = [_ln("HL:BEAM_LEDGER:GF:BM-1#BAND0001", "RELEASED", "L1"), _ln("P-C:BEAMS:GF:BAND0001", "EXCLUDED", "L2"),
             _ln("P-C:BEAMS:1F:BAND0002", "RELEASED", "L3")]          # same band id, other storey: not this band
    out = R.edge_member_carriage(bands, lines)
    assert [o["state"] for o in out] == ["CARRIED_ONCE", "OMITTED"] and out[0]["excluded_twins"] == 1
    with pytest.raises(R.RuleError):
        R.edge_member_carriage(bands[:1], lines + [_ln("P-C:BEAMS:GF:BAND0001", "HELD", "L4")])


# ---- development villa (merged repository files) ------------------------------------------------------------------
def test_alsenan_edge_members_carried_once_and_run_heights():
    doc = A.build(None)
    assert doc["edge_summary"] == {"CARRIED_ONCE": len(A.EDGE_BANDS), "OMITTED": 0}
    held = sorted(c["band"] + "@" + c["storey"] for c in doc["edge_members"] if c["line_class"] == "HELD")
    assert held == ["BAND0001.3@2F", "BAND0006.1@2F", "BAND0014@1F", "BAND0023@1F", "BAND0025@1F"]
    assert Decimal(doc["per_run_sum_m2"]).quantize(Decimal("0.0001")) == Decimal("7.6307")
    assert Decimal(doc["openings_t550_m2"]) == Decimal("-26.2840")


def test_alsenan_engine_openings_match_t292_and_register():
    A.check_engine_openings()


def test_alsenan_opening_table_private():
    p = A.PRIVATE_DEFAULT
    if not p.exists():
        pytest.skip("his opening rows are private (.work/private/t559/his_openings.json)")
    doc = A.build(p)
    bc = {k: Decimal(v) for k, v in doc["by_cause"].items()}
    assert sum(bc.values()) == Decimal("25.9224370")
    assert bc["HELD"] == Decimal("-23.37") and bc["RULE_DIFFERENCE"] == Decimal("-3.90")
    assert bc["ENGINE_RIGHT"] == Decimal("-5.3245") and bc["TOLERANCE"] == Decimal("0.0105")
    assert bc["UNRESOLVED"] == Decimal("58.506437")
