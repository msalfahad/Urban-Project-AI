"""T-603: reconciled-quantities statement V9 (T-590 / T-591 provenance reclasses, T-598 nosing beside, F-C-T593-1
stair-skirting one-element guard). Synthetic villa "S603" (not the training villa) by hand for R-T603-1 with adverse
cases (a delta moved, a row not RULE_DIFFERENCE, a row named twice, a total edited instead of reclassed, a MERGED
pointer without its rule, both skirting forms summed, a flight low that is not the element low), then the merged
training-villa sources (committed research outputs only; no private input): V8 carried byte-equal, class moves per
unit re-added, the joint rows of record and the counted-apart row, T-591 40 / 76 / 1, nosing closure, the guard."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t603"))
import t603_adapters as A  # noqa: E402
import t603_build as B  # noqa: E402

Dd = Decimal
E = A.StatementError


# ------------------------------------------------------------------------------- S603 by hand ---------------------
# S603 columns: his 10.5 m3, engine 10.0 -> reference - engine +0.5 = joint head -0.5 (RD) + beam through +0.8 (RD)
# + count +0.2 (ENGINE_RIGHT). No rule version for the joint: both RD rows -> UNRESOLVED (+0.3), count stays.
def _sec() -> dict:
    rows = [{"name": "GF: JOINT_HEAD", "delta": "-0.5", "class": "RULE_DIFFERENCE", "verification": "CHECKER_CONFIRMED"},
            {"name": "GF: THROUGH_SUPPORT", "delta": "0.8", "class": "RULE_DIFFERENCE",
             "verification": "WORKER_PROPOSED"},
            {"name": "GF: COUNT", "delta": "0.2", "class": "ENGINE_RIGHT", "verification": "CHECKER_CONFIRMED"}]
    return {"section_id": "S603/columns", "unit": "m3", "reference_total": "10.5", "engine_valued": "10.0",
            "difference": "0.5", "difference_pct_of_reference": None, "rows": rows}


def _ev(r):
    return A.V9_EVID[r["verification"]]


def _moves(d1="-0.5"):
    return {"GF: JOINT_HEAD": {"to": "UNRESOLVED", "tag": "S-1", "delta": d1},
            "GF: THROUGH_SUPPORT": {"to": "UNRESOLVED", "tag": "S-1", "delta": "0.8"}}


def test_s603_reclass_by_hand():
    sec, mv = A.reclass(_sec(), "S603/columns@V9", _moves(), "v", _ev)
    assert (sec["reference_total"], sec["engine_valued"], sec["difference"]) == ("10.5", "10.0", "0.5")
    bc = {k: Dd(v) for k, v in sec["by_class"].items() if Dd(v)}
    assert bc == {"UNRESOLVED": Dd("0.3"), "ENGINE_RIGHT": Dd("0.2")}
    assert Dd(sec["by_class_gross_abs"]["UNRESOLVED"]) == Dd("1.3")
    assert [m["delta"] for m in mv] == ["-0.5", "0.8"] and all(m["from"] == "RULE_DIFFERENCE" for m in mv)
    j = [r for r in sec["rows"] if r["name"] == "GF: JOINT_HEAD"][0]
    assert j["evidence_status"] == A.CV and j["was_class"] == "RULE_DIFFERENCE"      # (e) evidence stays
    assert sec["restates"] == "S603/columns"


def test_s603_delta_moved_refused():
    with pytest.raises(E, match="audited"):
        A.reclass(_sec(), "S603/columns@V9", _moves("-0.4"), "v", _ev)


def test_s603_not_rule_difference_refused():
    mv = {"GF: COUNT": {"to": "UNRESOLVED", "tag": "S-1", "delta": "0.2"}}
    with pytest.raises(E, match="RULE_DIFFERENCE"):
        A.reclass(_sec(), "S603/columns@V9", mv, "v", _ev)


def test_s603_row_twice_refused():
    sec = _sec()
    sec["rows"].append(dict(sec["rows"][0], delta="0"))
    sec["rows"][2]["delta"] = "0.7"
    with pytest.raises(E, match="not once"):
        A.reclass(sec, "S603/columns@V9", _moves(), "v", _ev)


def test_s603_reclass_may_not_set_delta():
    mv = _moves()
    mv["GF: JOINT_HEAD"]["set"] = {"delta": "0"}
    with pytest.raises(E, match="delta or a name"):
        A.reclass(_sec(), "S603/columns@V9", mv, "v", _ev)


def test_s603_total_edited_instead_of_split_refused():
    sec, _ = A.reclass(_sec(), "S603/columns@V9", _moves(), "v", _ev)
    bad = copy.deepcopy(sec)
    bad["reference_total"], bad["difference"] = "10.2", "0.2"
    bad["rows"] = [r for r in bad["rows"] if r["name"] != "GF: THROUGH_SUPPORT"] + [
        dict(bad["rows"][1], delta="0.5")]
    with pytest.raises(E, match="total edited"):
        A.check_section_totals(_sec(), bad)


def test_pointer_states():
    rule = {"task": "T-X", "status": "REJECTED", "status_line": "REJECTED", "rule_id": "UP-X-001"}
    assert A.joint_class(rule, "") == "UNRESOLVED"
    with pytest.raises(E, match="not in docs/RULES_INDEX"):
        A.joint_class(dict(rule, status="MERGED"), "| UP-Y-001 | 1.0.0 |")
    assert A.joint_class(dict(rule, status="MERGED"), "| UP-X-001 | 1.0.0 | LEAD_ADOPTED |") == "RULE_DIFFERENCE"


# ------------------------------------------------------------------------------- (f) two forms, one element ------
# S603 stair: P1 pitch 1.0 / zigzag 1.4, P2 pitch 2.0 / zigzag 2.5 (two forms each), P3 held 0 .. 0.3 (one form).
# Element = [1.0 + 2.0, 1.4 + 2.5] = [3.0, 3.9]; the sum over forms 6.9 is refused anywhere.
def _mrows(z2="2.5", dup=False):
    def r(p, f, lo, hi, lid):
        return {"beside": {"piece": p, "form": f}, "after": {"held_low": lo, "held_high": hi}, "line_id": lid}
    out = [r("P1", "SLOPED", 1.0, 1.0, "L1"), r("P1", "ZIGZAG", 1.4, 1.4, "L2"), r("P2", "SLOPED", 2.0, 2.0, "L3"),
           r("P2", "ZIGZAG", float(z2), float(z2), "L4"), r("P3", "SLOPED", 0.0, 0.3, "L5")]
    if dup:
        out.append(r("P1", "SLOPED", 1.0, 1.0, "L6"))
    return out


def _st(low="3.0", hi="3.9", extra=None):
    rows = [{"name": "ST-01 main: flight skirting, 2 two-form pieces", "class": "HELD", "delta": low,
             "bound": [low, hi], "unit": "lm"}] + (extra or [])
    return {"sections_v8": [{"section_id": "T-574/skirting-stairs", "unit": "lm", "rows": rows}]}


def test_two_forms_by_hand():
    e = A.skirting_element(_mrows())
    assert e["range_lm"] == ["3.0", "3.9"] and e["sum_over_forms_refused_lm"] == "6.9"
    assert e["two_form_pieces"] == 2 and list(e["held_one_form_pieces"]) == ["P3"] and e["summed"] is False
    A.refuse_form_sum(_st(), e)


def test_both_forms_summed_refused():
    e = A.skirting_element(_mrows())
    with pytest.raises(E, match="SLOPED \\+ ZIGZAG"):
        A.refuse_form_sum(_st(extra=[{"name": "ST-01 total", "class": "HELD", "delta": "6.9", "unit": "lm"}]), e)


def test_flight_low_not_element_low_refused():
    e = A.skirting_element(_mrows())
    with pytest.raises(E, match="element low"):
        A.refuse_form_sum(_st(low="3.4", hi="3.9"), e)
    with pytest.raises(E, match="below the element high"):
        A.refuse_form_sum(_st(low="3.0", hi="3.5"), e)


def test_form_pieces_adverse():
    with pytest.raises(E, match="pitch <= zigzag"):
        A.skirting_element(_mrows(z2="1.9"))
    with pytest.raises(E, match="twice"):
        A.skirting_element(_mrows(dup=True))


# ------------------------------------------------------------------------------- training villa ------------------
@pytest.fixture(scope="module")
def st():
    return B.build()


def test_rebuild_identical(st):
    assert st == json.loads(B.JSON_OUT.read_text(encoding="utf-8"))
    assert B.to_markdown(st) == B.MD_OUT.read_text(encoding="utf-8")


def test_v8_byte_equal(st):
    st8 = B.v8_statement()
    B.check_v8_unchanged(st, st8)
    bad = copy.deepcopy(st)
    bad["sections_v8"][0]["rows"][0]["delta"] = "999"
    with pytest.raises(E, match="V8 key sections_v8 changed"):
        B.check_v8_unchanged(bad, st8)


def test_class_moves_per_unit(st):
    rec = st["class_shift_v9"]["of_record"]
    assert rec["m3"]["RULE_DIFFERENCE -> UNRESOLVED"] == {"n": 6, "signed": "2.369278", "gross": "7.701778"}
    assert rec["t"]["RULE_DIFFERENCE -> UNRESOLVED"] == {"n": 6, "signed": "34.814694", "gross": "34.814694"}
    assert rec["lm"] == {"RULE_DIFFERENCE -> ENGINE_WRONG": {"n": 1, "signed": "0.30", "gross": "0.30"}}
    assert st["class_shift_v9"]["all_rows"]["m3"]["RULE_DIFFERENCE -> UNRESOLVED"]["n"] == 33


def test_joint_rows_and_apart(st):
    sp = st["structural_provenance_v9"]
    j = sp["joint_rows"]
    assert j["of_record"] == {"n": 5, "signed_m3": "2.248826", "gross_m3": "7.581326"}
    assert j["all_audited_in_record_sections"] + j["superseded_audited_beside"] == 37
    assert [(g["row"], g["delta"]) for g in sp["counted_apart"]] == [("GF: UNTRACED -> GF B7 UNRESOLVED", "0.120452")]
    assert sp["joint_rule_pointer"]["status"] == "REJECTED" and sp["joint_rule_pointer"]["in_rules_index"] is False
    p = sp["pairs_per_storey"]["by_storey"]
    assert (p["GF"]["net_m3"], p["1F"]["net_m3"], p["2F"]["net_m3"]) == ("0.620464", "1.208362", "0.42")
    for c in st["sections_v9"]:
        assert all(r["class"] != "RULE_DIFFERENCE" for r in c["rows"] if r.get("tag") == A.TAG_JOINT)


def test_sections_close_and_totals_unchanged(st):
    old = A.all_sections(B.v8_statement())
    for c in st["sections_v9"]:
        A.check_section_totals(old[c["restates"]], c)
        if any(r["class"] == "HELD" for r in c["rows"]):
            assert c["difference_pct_of_reference"] is None
    bad = copy.deepcopy([c for c in st["sections_v9"] if c["section_id"] == "T-551/columns@V9"][0])
    bad["engine_valued"] = "20.0"
    with pytest.raises(E, match="total edited"):
        A.check_section_totals(old["T-551/columns"], bad)


def test_finishes_provenance(st):
    fp = st["finishes_provenance_v9"]
    assert fp["counts_live"] == {"SOURCED": 40, "SOURCED_RECITE": 76, "NONE": 1}
    assert len(fp["annotations"]) + len(fp["overtaken_by_v8"]) + len(fp["none_row"]) == 117
    assert fp["citations_corrected"]["F-T591-2"]["rows"] == 8
    assert fp["citations_corrected"]["F-T591-3"]["governing"] == "Q-24"
    room = [c for c in st["sections_v9"] if c["section_id"] == "T-574/skirting-room@V9"][0]
    assert Dd(room["by_class"]["ENGINE_WRONG"]) == Dd("0.30") and Dd(room["by_class"]["RULE_DIFFERENCE"]) == Dd("43.32")


def test_nosing_beside(st):
    n = st["beside_v9"][0]
    lm = n["units"]["lm"]
    assert (Dd(lm["his"]), Dd(lm["ours_valued"]), Dd(lm["gap_his_minus_ours"])) == \
        (Dd("123.2"), Dd("107.37144"), Dd("15.82856"))
    assert Dd(lm["residual"]) == 0 and sum(Dd(v) for v in lm["by_class"].values()) == Dd("15.82856")
    assert n["units"]["nr"]["gap_his_minus_ours"] == 7 and n["valued"] == "0" and n["difference_added"] is False
    assert Dd(n["added_by_t598_lm_by_status"]["DRAWING-CONFIRMED"]) == Dd("2.30")


def test_stair_skirting_one_element(st):
    e = st["stair_skirting_element_v9"]
    assert e["range_lm"] == ["17.009049", "23.300481"] and e["two_form_pieces"] == 13
    A.refuse_form_sum(st, e)
    bad = copy.deepcopy(st)
    bad["sections_v9"][0]["note_bad"] = "40.309530"
    with pytest.raises(E, match="SLOPED \\+ ZIGZAG"):
        A.refuse_form_sum(bad, e)


def test_pin_drift_refused(monkeypatch):
    monkeypatch.setitem(A.PINS, A.T590_JSON, "0" * 64)
    with pytest.raises(E, match="sha256"):
        A.load(A.T590_JSON)
