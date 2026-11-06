"""T-551: B10 column / neck / footing (+ straps + band) / blinding concrete reconciled against a freelancer by component
(research/agents_t551, R-T551-1 .. 4). Hand villa "V551" (not the training villa) with both conventions; adverse cases;
then the committed development-villa tables, checked from merged repository files (the rebuild from the private
workbook runs only when it is present)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t551"))
import t551_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t551" / "out" / "T551_COLUMN_FOOTING_RECONCILE.json"
LINE_INDEX = ROOT / "research" / "agents_t507" / "out" / "LINE_INDEX_V3_0_57.json"
T545 = ROOT / "research" / "agents_t545" / "out" / "T545_BEAM_RECONCILE.json"
PRIVATE_WB = ROOT.parent / "private" / "concrete_rebar.xlsx"
D = Decimal

# ---- villa "V551" (hand) ----------------------------------------------------------------------------------------
# Footing 2.00 x 1.80 x 0.50 = 1.800, bottom -1.90 (top -1.40); neck 0.30 x 0.50 from the footing top to the tie-beam
# top -0.20: 1.20 m = 0.180; column 0.25 x 0.50 from the ground slab top +0.00 to the roof slab top +3.50 under a roof
# slab 0.20 thick over a gross 20.00 m2 panel.
#   TO_SLAB_TOP + NET : column 0.125 x 3.50 = 0.4375; slab (20.00 - 0.125) x 0.20 = 3.9750 -> 4.4125
#   TO_SOFFIT + GROSS : column 0.125 x 3.30 = 0.4125; slab 20.00 x 0.20 = 4.0000            -> 4.4125
#   the solid: 1.800 + 0.180 + 4.4125 = 6.3925 m3 in both conventions. Blinding 2.20 x 2.00 x 0.10 = 0.440 m3 is plain
#   concrete and never enters it.
COL = dict(col_b=0.25, col_c=0.50, h_top=3.50, t=0.20, slab_area_gross=20.00)


def test_hand_column_slab_both_conventions_same_solid():
    a = R.column_slab_volumes(**COL, column_basis="TO_SLAB_TOP", slab_basis="NET")
    b = R.column_slab_volumes(**COL, column_basis="TO_SOFFIT", slab_basis="GROSS")
    assert a == (D("0.4375"), D("3.975"), D("4.4125"))
    assert b[0] == D("0.4125") and b[1] == D("4.0") and b[2] == a[2]


def test_hand_footing_neck_column_through_slab_total():
    neck = R.neck_volume(b=0.30, c=0.50, top_level=-0.20, footing_bottom=-1.90, footing_depth=0.50,
                         measured_from="FOOTING_TOP")
    assert neck == D("0.180")
    footing = D("2.00") * D("1.80") * D("0.50")
    for basis in (("TO_SLAB_TOP", "NET"), ("TO_SOFFIT", "GROSS")):
        tot = footing + neck + R.column_slab_volumes(**COL, column_basis=basis[0], slab_basis=basis[1])[2]
        assert tot == D("6.3925")
    assert R.structural_total([{"item_code": "STR.CONC.FOOTING", "m3": "1.800"},
                               {"item_code": "STR.CONC.NECK", "m3": "0.180"},
                               {"item_code": "STR.CONC.COLUMN", "m3": "0.4375"},
                               {"item_code": "STR.CONC.SLAB", "m3": "3.975"}]) == D("6.392500")


def test_hand_mirror_and_rotation_invariant():
    a = R.column_slab_volumes(**COL, column_basis="TO_SLAB_TOP", slab_basis="NET")
    b = R.column_slab_volumes(**{**COL, "col_b": 0.50, "col_c": 0.25}, column_basis="TO_SLAB_TOP", slab_basis="NET")
    assert a == b


@pytest.mark.parametrize("pair", [("TO_SLAB_TOP", "GROSS"), ("TO_SOFFIT", "NET")])
def test_adverse_column_slab_overlap_twice_or_nowhere_refused(pair):
    with pytest.raises(R.Refused):
        R.column_slab_volumes(**COL, column_basis=pair[0], slab_basis=pair[1])


def test_adverse_neck_from_footing_bottom_refused():
    with pytest.raises(R.Refused):
        R.neck_volume(b=0.30, c=0.50, top_level=-0.20, footing_bottom=-1.90, footing_depth=0.50,
                      measured_from="FOOTING_BOTTOM")


def test_adverse_blinding_in_structural_total_refused():
    with pytest.raises(R.Refused):
        R.structural_total([{"item_code": "STR.CONC.FOOTING", "m3": "1.800"},
                            {"item_code": "STR.CONC.BLINDING", "m3": "0.440"}])


def test_adverse_units_mm_kg_percent_refused():
    with pytest.raises(R.Refused):
        R.column_slab_volumes(**{**COL, "col_b": 250, "col_c": 500}, column_basis="TO_SLAB_TOP", slab_basis="NET")
    with pytest.raises(R.Refused):
        R.structural_total([{"item_code": "STR.CONC.COLUMN", "m3": "12.5", "unit": "kg"}])
    with pytest.raises(R.Refused):
        R.d6("58.386 kg")
    with pytest.raises(R.Refused):
        R.component_table("1", "2", {"COUNT": "-50%"})


def test_adverse_held_as_zero_and_missing_refused():
    with pytest.raises(R.Refused):
        R.structural_total([{"item_code": "STR.CONC.COLUMN", "class": "HELD", "m3": 0}])
    assert R.structural_total([{"item_code": "STR.CONC.COLUMN", "class": "HELD", "m3": None},
                               {"item_code": "STR.CONC.COLUMN", "m3": "0.45"}]) == D("0.450000")
    with pytest.raises(R.Refused):
        R.d6(None)
    with pytest.raises(R.Refused):
        R.component_table("0.9", "1.2", {"COUNT": "0.0", "HELD": "0"}, held_his_share="0.3")


# Column split (R-T551-1), one storey x mark K1: his 3 rows 0.20 x 0.50 x 3.20 = 0.96; engine two members A 0.10 on the
# storey base +1.00 to the slab top (h 3.60, D_ctrl 0.60: 0.36 each) + one member based +0.40 (h 4.20: 0.42) + 1 held.
# COUNT (4 - 3) x 0.32 = +0.32; HELD -0.32; SECTION 0; JOINT_HEAD 3 x 0.10 x 0.60 = +0.18; BASE 0.10 x 0.60 = +0.06;
# height 2 x 0.10 x 0.40 + 0.10 x 1.00 = 0.18 -> GLOBAL_DEPTH 0.18 - 0.18 - 0.06 = -0.06; residual 1.14 - 0.96 = +0.18.
K1 = dict(his_n=3, his_b=0.20, his_c=0.50, his_h=3.20, held_n=1, storey_base=1.00,
          valued=[{"A": "0.10", "h": "3.60", "base": "1.00", "d_ctrl": "0.60", "m3": "0.36"},
                  {"A": "0.10", "h": "3.60", "base": "1.00", "d_ctrl": "0.60", "m3": "0.36"},
                  {"A": "0.10", "h": "4.20", "base": "0.40", "d_ctrl": "0.60", "m3": "0.42"}])


def test_hand_column_split():
    k, e, f = R.column_mark_split(**K1)
    assert (e, f) == (D("1.14"), D("0.96"))
    assert {n: v for n, v in k.items() if v} == {"COUNT": D("0.32"), "HELD": D("-0.32"), "JOINT_HEAD": D("0.18"),
                                                 "BASE": D("0.06"), "GLOBAL_DEPTH": D("-0.06")}
    open_ = R.column_mark_split(**{**K1, "valued": [dict(v, d_ctrl=None) for v in K1["valued"]]})[0]
    assert open_["HEIGHT_OPEN"] == D("0.18") and open_["JOINT_HEAD"] == 0
    none = R.column_mark_split(**{**K1, "his_n": 0, "his_b": None, "his_c": None, "his_h": None})[0]
    assert none["COUNT"] == D("1.14") and none["HELD"] == 0


def test_adverse_column_line_not_A_times_h_refused():
    with pytest.raises(R.Refused):
        R.column_mark_split(**{**K1, "valued": [dict(K1["valued"][0], m3="0.40")]})


# Footing split (R-T551-2): his F1 3 rows 1.50 x 1.50 x 0.40 = 0.90; engine 0.90, 0.90, 0.90 and 0.80 (an intersection
# owned by a deeper footing) + 1 held: COUNT (5 - 3) x 0.90 = +1.80; HELD -0.90; OVERLAP -0.10; residual 3.50 - 2.70.
def test_hand_footing_split_and_untraced():
    k, e, f = R.footing_mark_split(his_n=3, his_unit_m3="0.90", valued_m3=["0.90", "0.90", "0.90", "0.80"], held_n=1,
                                   cause="OVERLAP")
    assert (e, f) == (D("3.5"), D("2.7"))
    assert {n: v for n, v in k.items() if v} == {"COUNT": D("1.8"), "HELD": D("-0.9"), "OVERLAP": D("-0.1")}
    k2 = R.footing_mark_split(his_n=3, his_unit_m3="0.90", valued_m3=["0.90", "0.90", "0.90", "0.80"], held_n=1)[0]
    assert k2["UNTRACED"] == D("-0.1") and k2["OVERLAP"] == 0


def test_adverse_open_sum_refused():
    with pytest.raises(R.Refused):
        R.component_table("3.5", "2.7", {"COUNT": "1.8", "HELD": "-0.9"})


def test_held_bound_class():
    assert R.held_bound_class("1.96", "2.176", "2.275") == "BELOW"
    assert R.held_bound_class("8.604", "7.2204", "7.2204") == "ABOVE"
    assert R.held_bound_class("0.225", "0.075", "0.375") == "INSIDE"
    assert R.held_bound_class("0.345", None, None) == "UNBOUNDED"
    with pytest.raises(R.Refused):
        R.held_bound_class("0.3", "0.4", "0.2")


# ---- development villa: committed tables, merged repository files ------------------------------------------------
@pytest.fixture(scope="module")
def doc():
    return json.loads(OUT.read_text(encoding="utf-8"))


def _lines(code):
    return [x for x in json.loads(LINE_INDEX.read_text(encoding="utf-8"))["lines"] if x["item_code"] == code]


def _rel(code, pred=lambda x: True):
    return sum((D(str(x["measured_net"])).quantize(D("0.000001")) for x in _lines(code)
                if x["class"] == "RELEASED" and pred(x)), D(0))


def test_dev_engine_figures_from_line_index(doc):
    c = doc["columns"]
    gf = _rel("STR.CONC.COLUMN", lambda x: x["element_id"].endswith("|GF"))
    up = _rel("STR.CONC.COLUMN", lambda x: not x["element_id"].endswith("|GF"))
    assert D(c["GF"]["engine_m3"]) == gf == D("15.4925")
    assert D(c["1F"]["engine_m3"]) == up == D("4.284")                  # 1F lines + the two 1F planted columns
    assert D(c["2F"]["engine_m3"]) == 0 and D(doc["necks"]["engine_m3"]) == 0
    assert D(doc["footing_line"]["engine_m3"]) == _rel("STR.CONC.FOOTING") + _rel("STR.CONC.STRAP") == D("67.6945")
    assert D(doc["blinding"]["engine_released_m3"]) == _rel("STR.CONC.BLINDING")
    n = _lines("STR.CONC.NECK")
    assert len(n) == doc["necks"]["engine_held_lines"] == 36 and all(x["class"] == "HELD" for x in n)
    lo = sum((D(str(x["held_low"])) for x in n if x["held_low"] is not None), D(0))
    hi = sum((D(str(x["held_high"])) for x in n if x["held_high"] is not None), D(0))
    assert [D(v) for v in doc["necks"]["engine_held_bound_m3"]] == [lo, hi]


def test_dev_tables_close_exactly(doc):
    tabs = list(doc["columns"].values()) + [doc["necks"], doc["lift_walls"], doc["footing_line"]]
    for t in tabs:
        s = sum((D(c["m3"]) for c in t["components"].values()), D(0))
        assert s == D(t["residual_m3"]) == D(t["engine_m3"]) - D(t["his_m3"])
        if D(t["his_m3"]) and any(c["verdict"] == "HELD" for c in t["components"].values()):
            assert D(t["components"]["HELD"]["m3"]) < 0                  # held never closed as 0
    b = doc["blinding"]
    for end in ("held_low_end", "held_high_end"):
        assert sum(D(v) for v in b[end].values()) == D(b["residual_m3"]) == D(b["engine_released_m3"]) - D(b["his_m3"])


def test_dev_blinding_kept_out_of_structural(doc):
    fams = {"STR.CONC.COLUMN", "STR.CONC.FOOTING", "STR.CONC.STRAP"}
    rel = [{"item_code": x["item_code"], "m3": x["measured_net"]} for x in json.loads(
        LINE_INDEX.read_text(encoding="utf-8"))["lines"] if x["item_code"] in fams and x["class"] == "RELEASED"]
    tot = R.structural_total(rel)
    assert tot == D(doc["columns"]["GF"]["engine_m3"]) + D(doc["columns"]["1F"]["engine_m3"]) + D(
        doc["footing_line"]["engine_m3"])
    with pytest.raises(R.Refused):
        R.structural_total(rel + [{"item_code": "STR.CONC.BLINDING", "m3": doc["blinding"]["engine_released_m3"]}])


def test_dev_pairing_reads_t545(doc):
    b = json.loads(T545.read_text(encoding="utf-8"))
    for st, p in doc["column_beam_pairing"].items():
        ts = b["floors"][st]["components"]["THROUGH_SUPPORT"]["m3"]
        assert D(p["beam_THROUGH_SUPPORT_m3"]) == D(ts)
        jh = doc["columns"][st]["components"].get("JOINT_HEAD", {"m3": "0"})["m3"]
        assert D(p["column_JOINT_HEAD_m3"]) == D(jh) and D(p["net_m3"]) == D(jh) + D(ts)


def test_dev_no_freelancer_rows_tracked(doc):
    txt = OUT.read_text(encoding="utf-8")
    for k in ("\"label\"", "\"row\"", "\"b\"", "\"n\"", "formula"):
        assert k not in txt


@pytest.mark.skipif(not PRIVATE_WB.exists(), reason="private workbook absent")
def test_dev_rebuild_equals_committed(doc):
    import t551_alsenan as A
    new, his = A.build(str(PRIVATE_WB))
    got = json.loads(json.dumps(A.summary(new), ensure_ascii=False))
    want = {k: v for k, v in doc.items() if k not in ("schema", "candidate", "note")}
    assert got == want
    # R-T551-4 classes on the held lines that a row of his carries (information only)
    ftg = {h["mark"]: h["class"] for h in new["footing_line"]["held_beside_his"]}
    assert ftg["F10"] == "BELOW" and ftg["BAND"] == "ABOVE"
    assert ftg["SB1 in footing"].startswith("NO_ROW_OF_HIS") and ftg["SB3 in footing"].startswith("NO_ROW_OF_HIS")
    nk = new["necks"]["held_beside_his"]
    assert {h["class"] for h in nk if h["his_share_m3"]} <= {"INSIDE", "UNBOUNDED"}
    assert sum(1 for h in nk if h["his_share_m3"] is None) == 2
    col = new["columns"]["held_beside_his"]
    assert {h["class"] for h in col if h["storey"] == "2F"} == {"UNBOUNDED"}
    assert {h["class"] for h in col if h["storey"] == "UNKNOWN"} <= {"NO_ROW_OF_HIS", "NO_ROW_OF_HIS, UNBOUNDED"}
    # HELD (R-T394-2 convention) = his share on the held lines his rows carry + held drawn members beyond his count of
    # the mark (GF C3, 1F C8, 1F C9: 0.46875 + 0.621 + 0.690), which COUNT carries back with the opposite sign
    held_share = sum((D(h["his_share_m3"]) for h in col if h["his_share_m3"]), D(0))
    assert held_share == D("10.349250")
    assert held_share + D("1.779750") == -sum(D(t["components"]["HELD"]["m3"]) for t in doc["columns"].values())
    beyond = [h for h in col if h["storey"] in ("GF", "1F") and h["his_share_m3"] is None]
    assert sorted((h["storey"], h["mark"]) for h in beyond) == [("1F", "C6"), ("1F", "C8"), ("1F", "C9"),
                                                                 ("GF", "C3")]
