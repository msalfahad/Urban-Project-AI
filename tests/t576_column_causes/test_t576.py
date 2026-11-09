"""T-576: column measured-set differences restated as signed causes (R-T576-1 / -2), beam UNTRACED against a complete
support allowance (R-T576-3), joint owned once (R-T576-4). Hand villa "V576" (not the training villa), adverse cases,
then the development villa from merged repository files (the private rebuild only when the workbook is present)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t576"))
import t576_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t576" / "out" / "T576_COLUMN_CAUSES.json"
PRIVATE_WB = ROOT.parent / "private" / "concrete_rebar.xlsx"
D = Decimal


# ---- villa "V576" (hand) -----------------------------------------------------------------------------------------
# Column 0.30 x 0.60 (A 0.18), storey 4.20 slab top to slab top, beam 0.60 deep framing into it.
#   clear height (beam owns the joint): 3.60 x 0.18 = 0.648 m3; through height (column owns): 4.20 x 0.18 = 0.756 m3;
#   joint + head 0.60 x 0.18 = 0.108 m3, owned once.
def test_hand_clear_vs_through_is_the_joint():
    sp = R.member_height_split(A="0.18", h_e="4.20", base_drop="0", his_h="3.60", d_ctrl="0.60")
    assert R.d6(D("0.18") * D("3.60")) == D("0.648000")
    assert R.d6(D("0.18") * D("4.20")) == D("0.756000")
    assert sp == {"JOINT_HEAD": D("0.108000"), "BASE": D("0"), "GLOBAL_DEPTH": D("0.000000")}
    assert R.classify("JOINT_HEAD") == "RULE_DIFFERENCE"


def test_hand_global_depth_both_signs():
    # his one 0.75 depth on a 0.60 beam: his clear height 3.45 is 0.15 short of his own convention -> +0.027 ENGINE_RIGHT
    sp = R.member_height_split(A="0.18", h_e="4.20", base_drop="0", his_h="3.45", d_ctrl="0.60")
    assert sp["JOINT_HEAD"] == D("0.108000") and sp["GLOBAL_DEPTH"] == D("0.027000")
    # on a 0.85 beam his 0.75 is 0.10 too long under his own convention -> -0.018
    sp = R.member_height_split(A="0.18", h_e="4.20", base_drop="0", his_h="3.45", d_ctrl="0.85")
    assert sp["GLOBAL_DEPTH"] == D("-0.018000")
    assert sum(v for v in sp.values()) == D("0.135000")                 # = A x (4.20 - 3.45), invariant


def test_hand_open_depth_split_at_printed_lower_end():
    # framing beam printed 0.60, a second unlabelled framing member unprinted: D_ctrl >= 0.60
    sp = R.member_height_split(A="0.18", h_e="4.20", base_drop="0", his_h="3.45", d_low="0.60")
    assert sp[R.SPLIT_OPEN_LOW] is True
    assert sp["JOINT_HEAD"] == D("0.108000") and sp["GLOBAL_DEPTH"] == D("0.027000")   # GD is the UPPER end
    with pytest.raises(R.Refused):
        R.member_height_split(A="0.18", h_e="4.20", base_drop="0", his_h="3.45")      # no printed depth: stays open


def test_hand_base_drop_and_storey_term():
    # a member standing on a lower datum (base 0.70 below the storey base)
    sp = R.member_height_split(A="0.18", h_e="4.90", base_drop="0.70", his_h="3.45", d_ctrl="0.60")
    assert sp["BASE"] == D("0.126000") and sum(sp.values()) == R.d6(D("0.18") * D("1.45"))
    assert R.storey_term("4.20", "3.45", "0.75") == D("0")
    assert R.storey_term("4.20", "3.40", "0.75") == D("0.050000")      # his frame differs: its own term, never folded


def test_mirror_rotation_units():
    a = R.member_height_split(A=D("0.60") * D("0.30"), h_e="4.20", base_drop="0", his_h="3.60", d_ctrl="0.60")
    b = R.member_height_split(A=D("0.30") * D("0.60"), h_e="4.20", base_drop="0", his_h="3.60", d_ctrl="0.60")
    assert a == b
    with pytest.raises(R.Refused):
        R.member_height_split(A="0.18", h_e="4200", base_drop="0", his_h="3.60", d_ctrl="0.60")
    with pytest.raises(R.Refused):
        R.d6("600 mm")
    with pytest.raises(R.Refused):
        R.d6("21.7%")
    with pytest.raises(R.Refused):
        R.d6(None)


def test_count_verdicts():
    assert R.count_verdict(drawn_n=4, registered_n=4, conflict_positions=False) == "ENGINE_RIGHT"
    assert R.count_verdict(drawn_n=4, registered_n=4, conflict_positions=True) == "CONFLICT_BOUNDED"
    assert R.count_verdict(drawn_n=3, registered_n=4, conflict_positions=False) == "UNRESOLVED"
    with pytest.raises(R.Refused):
        R.classify("COUNT")


# ---- adverse --------------------------------------------------------------------------------------------------------
def test_adverse_joint_in_both_or_neither():
    assert R.joint_once(column_to="SLAB_TOP", beam_through=False) == "COLUMN"
    assert R.joint_once(column_to="SOFFIT", beam_through=True) == "BEAM"
    with pytest.raises(R.Refused):
        R.joint_once(column_to="SLAB_TOP", beam_through=True)            # 0.108 billed twice
    with pytest.raises(R.Refused):
        R.joint_once(column_to="SOFFIT", beam_through=False)             # 0.108 billed nowhere


def test_adverse_conflict_by_majority_refused():
    with pytest.raises(R.Refused):
        R.refuse_majority({"C8": ["FP", "CAP"], "C7": ["GBP"]})
    assert R.refuse_majority({"C3": ["FP", "CAP", "GBP"]}) == "C3"
    rd = R.readings({"P1": ["C8", "C7", "C8"], "P2": ["C", "C3"]})
    assert len(rd) == 4 and {"P1": "C7", "P2": "C"} in rd                # every reading kept
    with pytest.raises(R.Refused):
        R.readings({"P1": ["C8", "C8"]})


def test_adverse_class_table_and_pct():
    with pytest.raises(R.Refused):
        R.class_table([{"term": "X", "class": "MAJORITY", "m3": "1"}])
    t = R.class_table([{"class": "RULE_DIFFERENCE", "m3": "0.108"}, {"class": "ENGINE_RIGHT", "m3": "-0.027"}])
    assert t == {"RULE_DIFFERENCE": D("0.108000"), "ENGINE_RIGHT": D("-0.027000")}
    assert R.pct("0.135", "0.621") == D("21.74")                         # = 0.75 / 3.45: a pure head-depth ratio
    with pytest.raises(R.Refused):
        R.pct("0.1", "0")


def test_hand_beam_allowance_complete_vs_missing():
    # V576 beam B5 0.20 x 0.60: straight piece 3.00 between two columns 0.40; curved piece (area 0.40 m2 -> 2.00 m
    # equivalent) closing on a 0.30 carrier at one end and tangent at the other. His row 6.20 m.
    pieces = [{"piece": "S", "ends": [{"kind": "COLUMN", "width_m": "0.4", "member": "K1"},
                                      {"kind": "COLUMN", "width_m": "0.4", "member": "K2"}]},
              {"piece": "ARC", "ends": [{"kind": "CARRIER", "width_m": "0.3", "member": "B9"},
                                        {"kind": "TANGENT", "width_m": "0", "member": "B9 face"}]}]
    a, miss = R.allowance(pieces)
    assert a == D("1.100000") and miss == []
    resid = -(D("6.20") - D("5.00")) * D("0.20") * D("0.60")              # -0.144
    cls = R.untraced_test(his_minus_engine_m3=resid, b="0.20", D="0.60", allowance_m=a, missing=miss)
    assert cls[0] == "BEYOND_ALLOWANCE" and cls[2] == D("-0.010800")     # 1.20 m longer, allowance 1.10 (+0.01 tol)
    # straight-only allowance (the curved piece's end not recorded): NOT_DETERMINABLE, never UNRESOLVED
    a2, miss2 = R.allowance([pieces[0], {"piece": "ARC", "ends": None}])
    assert miss2 == ["ARC"]
    assert R.untraced_test(his_minus_engine_m3=resid, b="0.20", D="0.60", allowance_m=a2,
                           missing=miss2)[0] == "NOT_DETERMINABLE"
    # a held unlabelled piece is never an allowance end
    with pytest.raises(R.Refused):
        R.allowance([{"piece": "X", "ends": [{"kind": "HELD_PIECE", "width_m": "0.5", "member": "H"}]}])


# ---- development villa from committed files ------------------------------------------------------------------------
def _doc():
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_dev_readings_close_per_mark_and_storey():
    doc = _doc()
    assert len(doc["readings"]) == 4
    for r in doc["readings"]:
        for st in ("GF", "1F"):
            ms = r["columns"][st]["measured_set"]
            rows = [m for m in r["columns"][st]["marks_all"] if m["in_measured_set"]]
            assert [m["mark"] for m in rows] == ms["marks"]
            assert sum(D(m["engine_m3"]) for m in rows) == D(ms["engine_m3"])
            terms = sum(D(t["m3"]) for m in rows for t in m["terms"])
            assert terms == D(ms["diff_m3"]) == D(ms["engine_m3"]) - D(ms["his_m3"])
            assert sum(D(v) for v in ms["by_class_m3"].values()) == D(ms["diff_m3"])
            assert r["columns"][st]["storey_term_m3"] == "0.000000"
            assert "UNRESOLVED" not in ms["by_class_m3"] and "ENGINE_WRONG" not in ms["by_class_m3"]


def test_dev_merged_reading_equals_t572_and_split():
    doc = _doc()
    t572 = json.loads((ROOT / "research" / "agents_t572" / "out" / "T572_HELD_BOUNDS.json").read_text(encoding="utf-8"))
    m = [r for r in doc["readings"] if r["reading"] == {"10AE": "C3", "10E0": "C8"}][0]["columns"]
    for st in ("GF", "1F"):
        assert m[st]["measured_set"]["diff_m3"] == t572["measured_set"][f"columns_{st}"]["diff"]
    gf, f1 = m["GF"]["measured_set"], m["1F"]["measured_set"]
    assert gf["pct"] == "10.18" and gf["by_class_m3"] == {"ENGINE_RIGHT": "-0.860000", "RULE_DIFFERENCE": "2.033750"}
    assert gf["net_of_rule_difference_pct"] == "-7.46"
    assert f1["pct"] == "21.74" and f1["by_class_m3"] == {"RULE_DIFFERENCE": "0.460000", "ENGINE_RIGHT": "0.095000"}
    # 1F +21.74 % is the head-depth ratio 0.75 / 3.45 on members whose count and section agree
    assert R.pct(D("0.75"), D("3.45")) == D(f1["pct"])


def test_dev_conflict_reading_changes_the_set():
    doc = _doc()
    by = {(r["reading"]["10AE"], r["reading"]["10E0"]): r["columns"] for r in doc["readings"]}
    # 10AE never moves the measured set (its marks carry other held lines); 10E0 does
    for e in ("C7", "C8"):
        assert by[("C", e)]["GF"]["measured_set"] == by[("C3", e)]["GF"]["measured_set"]
    c7 = by[("C3", "C7")]["GF"]["measured_set"]
    assert c7["pct"] == "2.80" and c7["by_class_m3"]["CONFLICT_BOUNDED"] == "-0.843750"
    assert "C8" in c7["marks"] and "C7" not in c7["marks"]


def test_dev_beam_b7_complete_allowance():
    sys.path.insert(0, str(ROOT / "research" / "agents_t576"))
    import t576_alsenan as A
    b = A.beam_b7()
    assert json.loads(json.dumps(b)) == _doc()["beam_gf_b7"]
    assert b["t545_reclass_check"] == "BEYOND_ALLOWANCE"                 # merged T-545 allowance 1.55 reproduces UNTRACED
    assert b["result"]["class"] == "THROUGH_SUPPORT" and b["result"]["UNTRACED_m3"] == "0.000000"
    assert b["result"]["THROUGH_SUPPORT_m3"] == b["mark_residual_m3"] == "-0.354452"
    assert b["sensitivity_ring_carriers"]["CB1 ends only"]["untraced_m3"] == "-0.015452"


@pytest.mark.skipif(not PRIVATE_WB.exists(), reason="private workbook absent")
def test_private_rebuild_equals_committed():
    sys.path.insert(0, str(ROOT / "research" / "agents_t576"))
    import t576_alsenan as A
    assert json.loads(json.dumps(A.build(str(PRIVATE_WB)))) == _doc()
