"""T-620: statement V11 + scorecard V11 (R-T620-1, R-T613-1). Committed JSON only; no private input, nothing written."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal as D
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t620"))
import t620_build as B  # noqa: E402
import t620_scorecard as SC  # noqa: E402

E = B.StatementError


@pytest.fixture(scope="module")
def st10():
    return B.v10_statement()


@pytest.fixture(scope="module")
def src():
    return B.load_sources()


@pytest.fixture(scope="module")
def st(st10, src):
    return B.build_from(st10, src)


@pytest.fixture(scope="module")
def sc(st):
    return SC.build(st, SC.load(SC.V10_SCORECARD, SC.V10_SCORECARD_SHA256))


def _sec(st, sid):
    return {c["section_id"]: c for lv in SC.LEVELS for c in st.get(lv, [])}[sid]


# ---------------------------------------------------------------- reproduction and V10 carried byte-equal
def test_statement_reproduces_committed(st):
    assert st == json.loads(B.JSON_OUT.read_text(encoding="utf-8"))
    assert B.to_markdown(st) == B.MD_OUT.read_text(encoding="utf-8")


def test_scorecard_reproduces_committed_and_pins(sc):
    assert SC.dumps(sc) == SC.OUT_JSON.read_text()
    assert SC.markdown(sc) == SC.OUT_MD.read_text()
    SC.load(SC.STATEMENT, SC.STATEMENT_SHA256)   # the committed statement is the pinned one


def test_v10_keys_byte_equal(st, st10):
    for k in st10:
        if k not in B.EXTENDED:
            assert json.dumps(st[k], sort_keys=True) == json.dumps(st10[k], sort_keys=True), k
    assert st["reports_covered"][:len(st10["reports_covered"])] == st10["reports_covered"]


def test_scorecard_v10_unchanged_by_this_task():
    import t613_scorecard as S
    sc10 = S.build(S.load_statement())
    assert S.dumps(sc10) == S.OUT_JSON.read_text()          # the T-613 tool and output stay as merged


# ---------------------------------------------------------------- B10: totals unchanged, no class moves (Checker re-add)
@pytest.mark.parametrize("sid10,sid11", [("T-545/beams@V10", "T-545/beams@V11"), ("T-551/columns@V10", "T-551/columns@V10")])
def test_b10_totals_and_classes_unchanged(st, st10, sid10, sid11):
    a, b = _sec(st10, sid10), _sec(st, sid11)
    for k in ("reference_total", "engine_valued", "difference", "by_class"):
        assert a[k] == b[k]
    assert [(r["name"], r["class"], r["delta"]) for r in a["rows"]] == [(r["name"], r["class"], r["delta"]) for r in b["rows"]]


def test_b10_table_hand_readd(sc):
    t = [t for t in sc["trade_tables"] if t["trade_code"] == "B10" and t["unit"] == "m3"][0]
    # beams 66.093875 + columns 28.5465 + necks 8.805 + lift walls 2.4 + footing 77.6305 + blinding 47.055
    assert D(t["reference_total"]) == D("66.093875") + D("28.5465") + D("8.805") + D("2.4") + D("77.6305") + D("47.055")
    assert D(t["by_class"]["UNRESOLVED"]) == D("2.369278") + D("-0.435")


def test_t600_residuals_stay_unresolved_and_reproduce(st, src):
    bm = _sec(st, "T-545/beams@V11")
    assert bm["pair_residual_v11"]["through_support_unresolved_m3"] == "2.248826"
    gf = [r for r in bm["rows"] if r["name"].startswith("GF: THROUGH_SUPPORT residual")][0]
    assert gf["class"] == "UNRESOLVED" and gf["t600_v11"]["residual_R_m3"] == src["T-600"]["storeys"]["GF"]["residual_m3"]
    assert D(gf["t600_v11"]["through_support_T_m3"]) - D(gf["t600_v11"]["joint_head_J_m3"]) == D("0.740916")
    marks = {p["mark"]: p for p in gf["t600_v11"]["proposals_only"]}
    assert set(marks) == {"B2", "CB5", "CB6", "CB7"} and marks["CB6"]["basis"] == "CONDITIONAL"
    assert all(c["kind"] == "HELD" for c in marks["CB7"]["per_column"])   # CB7 at HELD columns stays HELD


def test_adverse_short_term_entered_as_a_class_refused(st):
    bm = copy.deepcopy(_sec(st, "T-545/beams@V11"))
    bm["rows"].append({"name": "GF: B4 group SHORT", "class": "UNRESOLVED_SHORT", "delta": "0.634737", "t600_term": True})
    with pytest.raises(E):
        B.refuse_bound_as_row(bm)
    bm["rows"][-1]["class"] = "UNRESOLVED"     # a SHORT balancing term as an UNRESOLVED row is refused too
    with pytest.raises(E):
        B.refuse_bound_as_row(bm)


# ---------------------------------------------------------------- (a) merged-only folds
def test_adverse_fold_from_unmerged_task_refused():
    with pytest.raises(E):
        B.require_merged("T-622")              # READY at the claim, not merged
    with pytest.raises(E):
        B._restate({"section_id": "X", "rows": []}, "X@V11", "T-623")


def test_adverse_merged_register_without_source_refused(monkeypatch):
    monkeypatch.setitem(B.SRC, "T-999", ROOT / "research/agents_t999/out/NONE.json")
    with pytest.raises(E):
        B.require_merged("T-999", dict(B.MERGED, **{"T-999": ("deadbeef", "x")}))


# ---------------------------------------------------------------- (b) restated rows keep their keys
def test_adverse_restated_row_class_change_refused(st10):
    old = B.of_record(st10, "T-578/rails")
    new = copy.deepcopy(old)
    new["section_id"] = "T-578/rails@V11"
    new["rows"][3]["class"] = "ENGINE_RIGHT"
    with pytest.raises(E):
        B.check_rows_kept(old, new)
    new = copy.deepcopy(old)
    new["section_id"] = "T-578/rails@V11"
    new["rows"][3]["evidence_status"] = "CHECKER_VERIFIED"   # evidence moves only in an evidence fold
    with pytest.raises(E):
        B.check_rows_kept(old, new)


def test_restating_a_superseded_section_refused(st10):
    with pytest.raises(E):
        B.of_record(st10, "T-545/beams@V9")


# ---------------------------------------------------------------- (c) ranges, never points
def test_stair_ranges_and_reconciliation(st):
    s = _sec(st, "T-574/skirting-stairs@V11")
    rr = s["residual_range_v11"]
    assert rr["UNRESOLVED"] == ["OPEN", "-1.639049"] and rr["t618_statement_row"] == "0.710951"
    assert D("-1.639049") + D("2.35") == D("0.710951")
    ends = [r["range_v11"] for r in s["rows"] if "range_v11" in r]
    assert ends == [["2.320000", "2.899456"], [None, "-2.388505"], [None, "-2.150000"]]
    assert all(r["delta"] != "0.710951" for r in s["rows"])     # the point is never a row
    rl = [r for r in _sec(st, "T-578/rails@V11")["rows"] if "range_v11" in r]
    assert rl[0]["range_v11"] == [None, "0.226"]


def test_adverse_row_delta_not_its_range_end_refused(st):
    s = copy.deepcopy(_sec(st, "T-578/rails@V11"))
    r = [r for r in s["rows"] if "range_v11" in r][0]
    r["range_v11"] = [None, "0.000"]
    with pytest.raises(E):
        B.refuse_bound_as_row(s)


# ---------------------------------------------------------------- T-616 lintel APART row (Checker hand re-add)
def test_lintel_apart_readd(st):
    s = _sec(st, "T-571/lintel-count-implied@V11")
    assert s["kind"] == "IMPLIED_COUNT"
    assert sum(D(r["delta"]) for r in s["rows"]) == D(s["difference"]) == D(54) - D(60)
    assert s["by_class"]["ENGINE_RIGHT"] == "-2" and s["by_class"]["UNRESOLVED"] == "-4"
    er, un = s["class_range_v11"]["ENGINE_RIGHT"], s["class_range_v11"]["UNRESOLVED"]
    assert D(er[0]) + D(un[1]) == D(er[1]) + D(un[0]) == D(-6)
    assert st["class_shift_v11"]["apart"][0]["apart"] is True
    assert st["class_shift_v11"]["scored"].startswith("none")


# ---------------------------------------------------------------- T-621 evidence
def test_floor_tile_evidence(st, sc):
    s = _sec(st, "T-553/floor-tile@V11")
    ev = [r.get("evidence_status") for r in s["rows"]]
    assert [i for i, e in enumerate(ev) if e == "CHECKER_VERIFIED"] == [6, 17, 19]
    assert ev.count("DRAWING_CONFIRMED") == 37 and ev[0] is None and "NOT_REMEASURED" in s["rows"][0]["evidence_v11"]
    c = [c for c in sc["reference_lines"] if c["section_id"] == "T-553/floor-tile@V11"][0]
    assert c["line_status"] == "PARTIALLY VERIFIED 3 / 41"
    assert c["status_count"]["UNKNOWN"] == 1 and c["by_class"] == s["by_class"]


# ---------------------------------------------------------------- (d) F-T613-5: one HELD-blank count
def test_held_blank_one_count(st, sc):
    h = st["held_blank_reconciliation_v11"]
    assert h == [dict(h[0], section_id="T-560/rebar@V9", held_blank_lines=799, in_compared_rows=798,
                      in_not_comparable_blocks={"T-560/rebar-tank": 1})]
    t = [t for t in sc["trade_tables"] if t["trade_code"] == "B11"][0]
    assert t["held_blank_lines_of_record"] == 799 and t["held_inside_rows"]["blank_lines"] == 798


def test_adverse_held_blank_mismatch_refused(st10):
    st = copy.deepcopy(st10)
    st["not_comparable"] = [n for n in st["not_comparable"] if n.get("block_id") != "T-560/rebar-tank"]
    rec = {"T-560/rebar@V9": B.of_record(st, "T-560/rebar@V9")}
    with pytest.raises(E):
        B.held_blank_reconciliation(st, rec)


def test_held_blank_synthetic_fixture():
    """Non-Alsenan: a section of 5 blank lines = 3 in rows + 2 in a NO_ROW block of the same report and unit."""
    sec = {"report": "T-X", "unit": "t", "engine_held": {"held_blank_lines": 5},
           "rows": [{"engine_held_blank_lines": 1}, {"engine_held_blank_lines": 2}, {}]}
    st = {"not_comparable": [{"report": "T-X", "unit": "t", "block_id": "T-X/tank", "engine_held_blank_lines": "2"},
                             {"report": "T-X", "unit": "m3", "block_id": "T-X/other", "engine_held_blank_lines": "4"}]}
    out = B.held_blank_reconciliation(st, {"T-X/s": sec})
    assert out[0]["in_not_comparable_blocks"] == {"T-X/tank": 2}
    sec["engine_held"]["held_blank_lines"] = 6                     # an unnamed line is refused, never absorbed
    with pytest.raises(E):
        B.held_blank_reconciliation(st, {"T-X/s": sec})


# ---------------------------------------------------------------- scorecard V11
def test_scorecard_changes_named_and_no_pct_beside_held(sc):
    ch = {c["line"]: c for c in sc["changes_from_v10"]}
    assert set(ch) == {"T-545/beams", "T-553/floor-tile", "T-574/skirting-stairs", "T-578/rails",
                       "T-574/skirting-room", "T-577/marble-lm", "T-571/lintel-count-implied"}
    assert ch["T-553/floor-tile"]["cause"].startswith("T-621")
    assert ch["T-545/beams"]["changed"].startswith("none")
    for c in sc["reference_lines"]:
        assert c["pct_of_reference"] is None or not c["held_rows"]


def test_adverse_altered_statement_refused(tmp_path):
    p = tmp_path / "s.json"
    p.write_bytes(SC.STATEMENT.read_bytes() + b" ")
    with pytest.raises(SC.ScorecardError):
        SC.load(p, SC.STATEMENT_SHA256)
