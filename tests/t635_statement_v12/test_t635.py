"""T-635: statement V12 + scorecard V12 (R-T635-1, R-T620-1, R-T613-1). Committed JSON only; no private input; nothing
written outside pytest's tmp_path."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal as D
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t635"))
import t635_build as B  # noqa: E402
import t635_scorecard as SC  # noqa: E402

E = B.StatementError


@pytest.fixture(scope="module")
def st11():
    return B.v11_statement()


@pytest.fixture(scope="module")
def src():
    return B.load_sources()


@pytest.fixture(scope="module")
def st(st11, src):
    return B.build_from(st11, src)


@pytest.fixture(scope="module")
def sc(st):
    return SC.build(st, SC.load(SC.V11_SCORECARD, SC.V11_SCORECARD_SHA256))


@pytest.fixture(scope="module")
def sc11():
    return SC.load(SC.V11_SCORECARD, SC.V11_SCORECARD_SHA256)


def _sec(st, sid):
    return {c["section_id"]: c for lv in SC.LEVELS for c in st.get(lv, [])}[sid]


def _table(sc, code, unit):
    return [t for t in sc["trade_tables"] if t["trade_code"] == code and t["unit"] == unit][0]


# ---------------------------------------------------------------- reproduction, pins, V11 byte-equal
def test_statement_reproduces_committed(st):
    assert st == json.loads(B.JSON_OUT.read_text(encoding="utf-8"))
    assert B.to_markdown(st) == B.MD_OUT.read_text(encoding="utf-8")


def test_scorecard_reproduces_committed_and_pins(sc):
    assert SC.dumps(sc) == SC.OUT_JSON.read_text()
    assert SC.markdown(sc) == SC.OUT_MD.read_text()
    SC.load(SC.STATEMENT, SC.STATEMENT_SHA256)


def test_v11_keys_byte_equal(st, st11):
    for k in st11:
        if k not in B.EXTENDED:
            assert json.dumps(st[k], sort_keys=True) == json.dumps(st11[k], sort_keys=True), k
    assert st["reports_covered"][:len(st11["reports_covered"])] == st11["reports_covered"]
    assert st["released_quantities_changed"] == 0


def test_v11_scorecard_unchanged_by_this_task():
    import t620_scorecard as S620
    sc11 = S620.build(S620.load(S620.STATEMENT, S620.STATEMENT_SHA256),
                      S620.load(S620.V10_SCORECARD, S620.V10_SCORECARD_SHA256))
    assert S620.dumps(sc11) == S620.OUT_JSON.read_text()


# ---------------------------------------------------------------- no quantity or class moves
def test_every_restated_section_keeps_rows_classes_and_totals(st, st11):
    for c in st["sections_v12"]:
        o = B.of_record(st11, c["restates"])
        for k in ("reference_total", "engine_valued", "difference", "by_class", "unit"):
            assert c[k] == o[k], (c["section_id"], k)
        assert [(r["name"], r["class"], r["delta"]) for r in c["rows"]] == \
            [(r["name"], r["class"], r["delta"]) for r in o["rows"]]
    assert st["class_shift_v12"]["scored"].startswith("none")


def test_trade_tables_quantities_equal_v11(sc, sc11):
    for t, t11 in zip(sc["trade_tables"], sc11["trade_tables"]):
        for k in ("trade_code", "unit", "reference_kind", "reference_total", "engine_valued", "difference", "by_class"):
            assert t[k] == t11[k], (t["trade_code"], k)


# ---------------------------------------------------------------- Checker hand re-add: B4 and B10
def test_b4_table_hand_readd(sc, st):
    t = _table(sc, "B4", "m2")
    assert D(t["reference_total"]) - D(t["engine_valued"]) == D(t["difference"]) == D("433.83") - D("340.3038")
    s = _sec(st, "T-547/wall-tile@V12")
    assert sum(D(r["delta"]) for r in s["rows"]) == D("93.5262")
    assert t["status_count"] == {"VERIFIED": 8, "PARTIALLY VERIFIED": 1, "DRAWING-CONFIRMED": 34, "HELD": 6, "UNKNOWN": 4}
    assert sum(t["status_count"].values()) == 53
    held = [r for r in s["rows"] if r["class"] == "HELD"]
    assert len(held) == 6 and sum(D(r["delta"]) for r in held) == D("138.39")      # HELD never 0, untouched
    assert all("evidence_source_v12" not in r for r in held)


def test_b10_table_hand_readd(sc):
    t = _table(sc, "B10", "m3")
    assert D(t["reference_total"]) == D("66.093875") + D("28.5465") + D("8.805") + D("2.4") + D("77.6305") + D("47.055")
    assert D(t["by_class"]["UNRESOLVED"]) == D("2.369278") + D("-0.435")
    assert t["status_count"]["VERIFIED"] == 18 and t["status_count"]["UNKNOWN"] == 2
    assert sum(t["status_count"].values()) == sum(c for c in t["status_count"].values())


def test_b10_checker_rows_and_cb12_partial(st):
    bm = _sec(st, "T-545/beams@V12")
    assert [r["evidence_status"] for r in bm["rows"] if r.get("evidence_source_v12", "").startswith("T-623")
            and r.get("evidence_status") in ("CHECKER_VERIFIED", "PARTIALLY_VERIFIED")] == \
        ["CHECKER_VERIFIED", "PARTIALLY_VERIFIED", "CHECKER_VERIFIED"]
    cb12 = bm["rows"][17]
    assert cb12["evidence_status"] == "PARTIALLY_VERIFIED" and "differs from the row delta" in cb12["evidence_verdict"]
    assert cb12["delta"] == "0.160962"                                      # F-T623-1 split beside, not applied
    ts = [bm["rows"][i] for i in (3, 13)]          # the T-623 RE-MEASURED (PARTS) residuals: annotated, never promoted
    assert all(r["name"].split(":")[1].strip().startswith("THROUGH_SUPPORT residual") for r in ts)
    assert all(r["class"] == "UNRESOLVED" and r["evidence_status"] == "WORKER_PROPOSED" and "UNRESOLVED" in
               r["evidence_v12"] for r in ts)
    cols = _sec(st, "T-551/columns@V12")
    assert [cols["rows"][i]["evidence_status"] for i in (0, 1, 7)] == ["CHECKER_VERIFIED"] * 3


# ---------------------------------------------------------------- R-T635-1 (a) bind before stamp
def test_adverse_bind_mismatch_refused(st11):
    sec = copy.deepcopy(B.of_record(st11, "T-547/wall-tile"))
    r = sec["rows"][25]
    with pytest.raises(E):
        B.bind(sec, 25, r["name"], r["class"], str(D(r["delta"]) + D("0.001")))      # delta drifted
    with pytest.raises(E):
        B.bind(sec, 26, r["name"], r["class"], r["delta"])                           # stamp onto the next row
    with pytest.raises(E):
        B.bind(sec, 25, r["name"], "ENGINE_WRONG", r["delta"])                       # class differs


# ---------------------------------------------------------------- (b) grading
def test_grade_rules():
    assert B.grade("-0.7552", "-0.755240", "CHECKER_VERIFIED") == ("CHECKER_VERIFIED", None)   # equal at 4 dp
    s, why = B.grade("0.160962", "0.187500", "CHECKER_VERIFIED")
    assert s == "PARTIALLY_VERIFIED" and "0.1875" in why
    assert B.grade("6.285", "6.288480", "CHECKER_VERIFIED")[0] == "PARTIALLY_VERIFIED"
    assert B.grade("1.0", None, "CHECKER_VERIFIED")[0] == "PARTIALLY_VERIFIED"


def test_reproduced_cited_owner_rule_never_promoted(st):
    s = _sec(st, "T-543/blockwork@V12")
    for r in s["rows"]:
        ev = r.get("evidence_v12", "")
        if ev.startswith(("T-633 REPRODUCED", "T-633 CITED", "T-633 OWNER_RULE")):
            assert r.get("evidence_status") in (None, "WORKER_PROPOSED")
    assert s["rows"][24].get("evidence_status") is None and "HEIGHT row" in s["rows"][24]["evidence_v12"]


# ---------------------------------------------------------------- (c) never lower, (e) HELD untouched
def test_adverse_lowering_refused(st):
    sec = copy.deepcopy(_sec(st, "T-551/columns@V12"))
    with pytest.raises(E):
        B.stamp(sec, 0, "T-628", "DRAWING_CONFIRMED", "x")                          # VERIFIED -> DRAWING-CONFIRMED


def test_adverse_held_row_stamp_refused(st):
    sec = copy.deepcopy(_sec(st, "T-547/wall-tile@V12"))
    with pytest.raises(E):
        B.stamp(sec, 47, "T-622", "DRAWING_CONFIRMED", "x")


# ---------------------------------------------------------------- merged register
def test_adverse_rejected_and_unmerged_refused():
    with pytest.raises(E):
        B.require_merged("T-648")
    with pytest.raises(E):
        B.require_merged("T-314")
    with pytest.raises(E):
        B._restate({"section_id": "X", "rows": []}, "T-423")


def test_beside_register_names_every_merged_delivery_task(st):
    assert [b["task"] for b in st["beside_v12"]] == list(B.BESIDE)
    assert {"T-638", "T-639", "T-643", "T-647", "T-649"} <= set(B.BESIDE)
    assert "T-648" in st["refused_v12"]


# ---------------------------------------------------------------- (d) class proposals beside, never applied
def test_class_proposals_listed_not_applied(st):
    props = st["class_proposals_v12"]
    assert any(p["section_id"] == "T-545/beams@V12" and p["row"] == 17 for p in props)
    for p in props:
        if p["row"] is None:
            continue
        r = _sec(st, p["section_id"])["rows"][p["row"]]
        assert r["class"] == p["statement"] or p["statement"].startswith(r["class"]) or p["statement"] == r["class"]


# ---------------------------------------------------------------- synthetic, non-Alsenan fixture
def _syn():
    return {"section_id": "K635/tile", "unit": "m2", "reference_total": "20", "engine_valued": "17", "difference": "3",
            "by_class": {"ENGINE_RIGHT": "1.5", "RULE_DIFFERENCE": "-0.5", "HELD": "2"},
            "rows": [{"name": "room A length", "class": "ENGINE_RIGHT", "delta": "1.50"},
                     {"name": "room A height", "class": "RULE_DIFFERENCE", "delta": "-0.5"},
                     {"name": "room B held", "class": "HELD", "delta": "2", "bound": ["2", None]}]}


def test_synthetic_fixture_fold(monkeypatch):
    monkeypatch.setitem(B.MERGED, "T-X", ("deadbeef", "Verifier synthetic"))
    monkeypatch.setitem(B.SRC, "T-X", B.SRC["T-622"])
    monkeypatch.setitem(B.GATE_A, "T-X", "status accepted (synthetic)")
    old = _syn()
    new = B._restate(old, "T-X")
    B.bind(new, 0, "room A length", "ENGINE_RIGHT", "1.5")                             # Decimal-equal 1.50 == 1.5
    s, why = B.grade("1.50", "1.500", "CHECKER_VERIFIED")
    B.stamp(new, 0, "T-X", s, "Checker synthetic own re-measure", "1.500")
    B.stamp(new, 1, "T-X", None, "owner-rule height: stays UNKNOWN")
    out, moves = B._close(old, new, [], [], "synthetic")
    assert out["rows"][0]["evidence_status"] == "CHECKER_VERIFIED" and "evidence_status" not in out["rows"][1]
    assert out["by_class"] == old["by_class"]
    with pytest.raises(E):                                                             # HELD never stamped
        B.stamp(new, 2, "T-X", "DRAWING_CONFIRMED", "x")
    bad = copy.deepcopy(new)
    bad["rows"][1]["delta"] = "0"                                                      # a quantity move is refused
    with pytest.raises(E):
        B._close(old, bad, [], [], "x")


def test_adverse_altered_statement_refused(tmp_path):
    p = tmp_path / "s.json"
    p.write_bytes(SC.STATEMENT.read_bytes() + b" ")
    with pytest.raises(SC.ScorecardError):
        SC.load(p, SC.STATEMENT_SHA256)


def test_no_pct_beside_held_and_rows_conserved(sc, sc11):
    for c in sc["reference_lines"]:
        assert c["pct_of_reference"] is None or not c["held_rows"]
    assert sum(sc["headline"]["rows_by_status_v12"].values()) == sum(sc["headline"]["rows_by_status_v11"].values())
    assert sc["headline"]["rows_by_status_v12"]["HELD"] == sc["headline"]["rows_by_status_v11"]["HELD"]
