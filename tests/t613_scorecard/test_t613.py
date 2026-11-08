"""T-613: scorecard tables from the reconciled statement V10 (R-T613-1). Synthetic villa "S613" (not the training
villa) by hand: a base section superseded by a V10 restatement, a section of record unchanged, a nested measured set
apart, a statement totals entry for each; adverse cases (a HELD counted as 0, two units summed, two reference kinds
summed, a VERIFIED row with no Checker verdict, rows not re-adding, a totals entry that moved, a % beside HELD), then
the committed training-villa statement V10 (research output only; no private input): sha pin, rebuild identical, the
section-of-record set equal to T-609's own resolver, hand re-adds of two trade tables, pending work never folded in."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t613"))
import t613_scorecard as T  # noqa: E402

Dd = Decimal
E = T.ScorecardError
CHK = "Checker 2026-11-01 10:00 (S613 Gate A): own re-measure 2 / 2 components AGREE, re-added"


# ------------------------------------------------------------------------------- S613 by hand ---------------------
# Tiles (m2): his 100.0, ours 90.0 -> +10.0 = ENGINE_RIGHT +4.0 (VERIFIED) + HELD +5.0 (bath walls held) + UNRESOLVED
# +1.0 (worker). V10 restates the UNRESOLVED +1.0 as RULE_DIFFERENCE (verdict PV); totals never move.
# Skirting (lm): his 50.0, ours 52.0 -> -2.0 = ENGINE_RIGHT -2.0 VERIFIED (1 row) -> a fully VERIFIED line.
# Treads (lm): his 20.0, ours 0 -> +20.0 = HELD 20.0 (flight held) + a HELD row at delta 0 with bound 0 .. 3.5.
# Nested set (m2): a measured subset of the tiles, % printed -5.00: apart, never added, no %.
def s613() -> dict:
    tiles_v1 = {"section_id": "S613/tiles", "trade": "B3 floor tile", "unit": "m2", "reference_kind": "FREELANCER",
                "reference_total": "100.0", "engine_valued": "90.0", "difference": "10.0",
                "difference_pct_of_reference": "10.00",
                "by_class": {"ENGINE_RIGHT": "4.0", "ENGINE_WRONG": "0", "RULE_DIFFERENCE": "0", "HELD": "5.0",
                             "TOLERANCE": "0", "UNRESOLVED": "1.0"},
                "rows": [{"name": "room A outline", "class": "ENGINE_RIGHT", "delta": "4.0", "unit": "m2",
                          "evidence_status": "CHECKER_VERIFIED", "evidence_verdict": CHK},
                         {"name": "bath walls held", "class": "HELD", "delta": "5.0", "unit": "m2",
                          "evidence_status": "WORKER_PROPOSED"},
                         {"name": "corridor residual", "class": "UNRESOLVED", "delta": "1.0", "unit": "m2",
                          "evidence_status": "WORKER_PROPOSED"}]}
    tiles_v10 = copy.deepcopy(tiles_v1)
    tiles_v10.update(section_id="S613/tiles@V10", difference_pct_of_reference=None)
    tiles_v10["by_class"].update(UNRESOLVED="0", RULE_DIFFERENCE="1.0")
    tiles_v10["rows"][2].update({"class": "RULE_DIFFERENCE", "evidence_status": "PARTIALLY_VERIFIED",
                                 "evidence_verdict": "Checker 2026-11-02 (S613 rule) PARTIALLY VERIFIED 1 / 2"})
    skirt = {"section_id": "S613/skirting", "trade": "B6 skirting", "unit": "lm", "reference_kind": "FREELANCER",
             "reference_total": "50.0", "engine_valued": "52.0", "difference": "-2.0",
             "difference_pct_of_reference": "-4.00",
             "by_class": {"ENGINE_RIGHT": "-2.0", "ENGINE_WRONG": "0", "RULE_DIFFERENCE": "0", "HELD": "0",
                          "TOLERANCE": "0", "UNRESOLVED": "0"},
             "rows": [{"name": "hall returns", "class": "ENGINE_RIGHT", "delta": "-2.0", "unit": "lm",
                       "evidence_status": "CHECKER_VERIFIED", "evidence_verdict": CHK}]}
    treads = {"section_id": "S613/treads", "trade": "B7 treads", "unit": "lm", "reference_kind": "FREELANCER",
              "reference_total": "20.0", "engine_valued": "0", "difference": "20.0",
              "difference_pct_of_reference": None,
              "by_class": {"ENGINE_RIGHT": "0", "ENGINE_WRONG": "0", "RULE_DIFFERENCE": "0", "HELD": "20.0",
                           "TOLERANCE": "0", "UNRESOLVED": "0"},
              "rows": [{"name": "flight held", "class": "HELD", "delta": "20.0", "unit": "lm",
                        "evidence_status": "PARTIALLY_VERIFIED", "evidence_verdict": "Checker PARTIALLY VERIFIED"},
                       {"name": "landing nosing, location not established", "class": "HELD", "delta": "0",
                        "unit": "lm", "bound": ["0", "3.5"], "evidence_status": "WORKER_PROPOSED"}]}
    nested = {"section_id": "S613/tiles-measured", "kind": "LIKE_FOR_LIKE_MEASURED_SET", "trade": "B3 floor tile",
              "unit": "m2", "reference_kind": "FREELANCER", "reference_total": "40.0", "engine_valued": "42.0",
              "difference": "-2.0", "difference_pct_of_reference": "-5.00",
              "by_class": {"ENGINE_RIGHT": "-2.0", "ENGINE_WRONG": "0", "RULE_DIFFERENCE": "0", "HELD": "0",
                           "TOLERANCE": "0", "UNRESOLVED": "0"},
              "rows": [{"name": "room A measured", "class": "ENGINE_RIGHT", "delta": "-2.0", "unit": "m2",
                        "evidence_status": "WORKER_PROPOSED"}]}

    def tot(sec):
        return {k: sec[k] for k in ("reference_total", "engine_valued", "difference", "unit", "trade")} | {
            "by_class": dict(sec["by_class"]), "sections": [sec["section_id"]]}
    return {"sections": [tiles_v1, skirt, treads], "sections_v7": [nested], "sections_v10": [tiles_v10],
            "supersedes_v10": {"S613/tiles": "S613/tiles@V10", "beside_x": "beside_y"},
            "totals": [tot(tiles_v1), tot(skirt), tot(treads)], "not_comparable": [], "reports_pending": [],
            "schema_v10": "S613", "released_quantities_changed": 0}


def test_s613_tables_by_hand():
    sc = T.build(s613(), pending=())
    assert sc["sections_of_record"] == 4 and sc["superseded_not_read"] == ["S613/tiles"]
    ids = [c["section_id"] for c in sc["reference_lines"]]
    assert ids == ["S613/skirting", "S613/treads", "S613/tiles@V10"]          # superseded base never read
    assert [a["section_id"] for a in sc["apart"]] == ["S613/tiles-measured"]
    tb = {(t["trade_code"], t["unit"]): t for t in sc["trade_tables"]}
    assert set(tb) == {("B3", "m2"), ("B6", "lm"), ("B7", "lm")}               # two lm trades never one table
    b3 = tb[("B3", "m2")]
    assert (b3["reference_total"], b3["engine_valued"], b3["difference"]) == ("100.0", "90.0", "10.0")
    assert b3["by_class"]["RULE_DIFFERENCE"] == "1.0" and b3["by_class"]["UNRESOLVED"] == "0"   # V10, not the base
    assert b3["status_count"] == {"VERIFIED": 1, "PARTIALLY VERIFIED": 1, "DRAWING-CONFIRMED": 0, "HELD": 1,
                                  "UNKNOWN": 0}
    assert b3["status_signed"]["HELD"] == "5.0"                                # HELD keeps its quantity
    lines = {c["section_id"]: c for c in sc["reference_lines"]}
    assert lines["S613/skirting"]["line_status"] == "VERIFIED"
    assert lines["S613/skirting"]["pct_of_reference"] == "-4.00"               # as printed, labelled
    assert "NOT a verdict" in lines["S613/skirting"]["pct_note"]
    assert lines["S613/tiles@V10"]["line_status"] == "PARTIALLY VERIFIED 1 / 3 (+1 rows PV)"
    tr = lines["S613/treads"]
    assert tr["line_status"] == "HELD 2 / 2" and tr["held_rows"] == 2
    assert tr["held_bound_add"] == ["0", "3.5"] and tr["pct_of_reference"] is None
    assert sc["apart"][0]["pct_of_reference"] is None and "nested" in sc["apart"][0]["pct_note"]
    chk = {t["totals_section"]: t for t in sc["statement_totals_check"]}
    assert chk["S613/tiles"]["section_of_record"] == "S613/tiles@V10"
    assert chk["S613/tiles"]["by_class"].startswith("SUPERSEDED")
    assert chk["S613/skirting"]["by_class"] == "EQUAL"
    assert sc["residual_by_unit_reference_kind_and_class"]["lm / FREELANCER"]["HELD"] == "20.0"


def test_s613_verified_rows_cite_a_checker_verdict():
    sc = T.build(s613(), pending=())
    for c in sc["reference_lines"]:
        for r in c["rows"]:
            if r["status"] == "VERIFIED":
                assert r["checker_citation"] and "Checker" in r["checker_citation"]


# ------------------------------------------------------------------------------- S613 adverse ---------------------
def _sec(st, sid):
    return next(s for lv in T.LEVELS for s in st.get(lv, []) if s["section_id"] == sid)


def test_held_counted_as_zero_refused():
    st = s613()
    del _sec(st, "S613/treads")["rows"][1]["bound"]
    with pytest.raises(E, match="HELD counted as 0"):
        T.build(st, pending=())
    st = s613()
    _sec(st, "S613/treads")["rows"][1]["bound"] = ["0", "0"]
    with pytest.raises(E, match="HELD counted as 0"):
        T.build(st, pending=())


def test_two_units_refused():
    st = s613()
    _sec(st, "S613/skirting")["rows"][0]["unit"] = "m2"
    with pytest.raises(E, match="two units"):
        T.build(st, pending=())
    sc = T.build(s613(), pending=())
    a = next(c for c in sc["reference_lines"] if c["unit"] == "lm")
    b = next(c for c in sc["reference_lines"] if c["unit"] == "m2")
    with pytest.raises(E, match="two units"):
        T.sum_group("B6", "lm", "FREELANCER", [a, b])
    c = dict(a, reference_kind="OWNER_QUESTION_FIGURE")
    with pytest.raises(E, match="two reference kinds"):
        T.sum_group("B6", "lm", "FREELANCER", [a, c])


def test_verified_without_component_verdict_refused():
    st = s613()
    _sec(st, "S613/skirting")["rows"][0]["evidence_verdict"] = "CHECKER_CONFIRMED"   # a bare stamp, no verdict
    with pytest.raises(E, match="VERIFIED without a cited Checker verdict"):
        T.build(st, pending=())
    st = s613()
    r = _sec(st, "S613/skirting")["rows"][0]
    del r["evidence_status"], r["evidence_verdict"]
    r["verification"] = "CHECKER_VERIFIED"
    with pytest.raises(E, match="VERIFIED without a cited Checker verdict"):
        T.build(st, pending=())


def test_pre_stamp_class_confirmation_is_not_verified():
    st = s613()
    r = _sec(st, "S613/skirting")["rows"][0]
    del r["evidence_status"], r["evidence_verdict"]
    r.update(verification="CHECKER_CONFIRMED", verification_basis=CHK)
    sc = T.build(st, pending=())
    line = next(c for c in sc["reference_lines"] if c["section_id"] == "S613/skirting")
    assert line["line_status"] == "UNKNOWN 0 / 1" and line["rows"][0]["sub"].startswith("class confirmed")


def test_rows_not_re_adding_and_moved_totals_refused():
    st = s613()
    _sec(st, "S613/tiles@V10")["rows"][0]["delta"] = "4.5"
    with pytest.raises(E, match="re-add"):
        T.build(st, pending=())
    st = s613()
    _sec(st, "S613/skirting")["engine_valued"] = "51.0"
    with pytest.raises(E, match="reference - engine"):
        T.build(st, pending=())
    st = s613()
    st["totals"][0]["reference_total"] = "101.0"
    with pytest.raises(E, match="section of record"):
        T.build(st, pending=())
    st = s613()
    st["totals"][1]["by_class"]["ENGINE_RIGHT"] = "-1.0"
    st["totals"][1]["by_class"]["UNRESOLVED"] = "-1.0"
    with pytest.raises(E, match="by class differs from its own section"):
        T.build(st, pending=())


def test_pct_beside_held_suppressed_and_loops_refused():
    st = s613()
    _sec(st, "S613/treads")["difference_pct_of_reference"] = "100"
    sc = T.build(st, pending=())
    tr = next(c for c in sc["reference_lines"] if c["section_id"] == "S613/treads")
    assert tr["pct_of_reference"] is None and tr["pct_note"].startswith("suppressed")
    st = s613()
    st["supersedes_v10"]["S613/tiles@V10"] = "S613/tiles"
    with pytest.raises(E, match="loop"):
        T.of_record("S613/tiles", T.supersession(st))
    st = s613()
    st["supersedes_v10"]["S613/skirting"] = "S613/skirting@V99"
    with pytest.raises(E, match="absent"):
        T.build(st, pending=())


# ------------------------------------------------------------------------------- training villa statement V10 ----
@pytest.fixture(scope="module")
def real():
    st = T.load_statement()
    return st, T.build(st)


def test_statement_pinned_and_rebuild_identical(real):
    st, sc = real
    assert T.OUT_JSON.read_text() == T.dumps(sc)
    assert T.OUT_MD.read_text() == T.markdown(sc)
    with pytest.raises(E, match="sha256"):   # a file that is not the pinned statement is refused
        T.load_statement(Path(__file__))


def test_sections_of_record_match_t609_resolver(real):
    st, sc = real
    sys.path.insert(0, str(ROOT / "research" / "agents_t609"))
    import t609_adapters as A9
    sup = A9.supersession(st)
    theirs = [k for k in A9.all_sections(st) if k not in sup]
    assert sorted(theirs) == sorted([c["section_id"] for c in sc["reference_lines"]] +
                                    [a["section_id"] for a in sc["apart"]])
    assert sc["sections_of_record"] == 48 and sc["scored_sections"] == 36 and sc["apart_sections"] == 12
    assert not any(c["section_id"] in sup for c in sc["reference_lines"])   # never an older superseded section


def test_hand_re_add_two_trade_tables(real):
    _, sc = real
    tb = {(t["trade_code"], t["unit"], t["reference_kind"]): t for t in sc["trade_tables"]}
    # B12 nr: alu doors his 5 / ours 6 (-1 ENGINE_RIGHT, VERIFIED by the T-568 own census) + windows his 29 / ours
    # 28 (+1 HELD: W02): reference 34, engine 34, difference 0 = -1 + 1; never read as agreement (HELD 1 stands).
    b12 = tb[("B12", "nr", "FREELANCER")]
    assert (b12["reference_total"], b12["engine_valued"], b12["difference"]) == ("34", "34", "0")
    assert b12["by_class"]["ENGINE_RIGHT"] == "-1" and b12["by_class"]["HELD"] == "1"
    assert b12["status_count"]["HELD"] == 1 and b12["status_count"]["VERIFIED"] == 1
    # B10 m3: beams@V10 + columns@V10 + necks + lift walls + footing line + blinding.
    b10 = tb[("B10", "m3", "FREELANCER")]
    ref = Dd("66.093875") + Dd("28.5465") + Dd("8.805") + Dd("2.4") + Dd("77.6305") + Dd("47.055")
    eng = Dd("66.321054") + Dd("19.7765") + Dd("0") + Dd("0") + Dd("67.6945") + Dd("12.734438")
    assert Dd(b10["reference_total"]) == ref == Dd("230.530875")
    assert Dd(b10["engine_valued"]) == eng == Dd("166.526492")
    assert Dd(b10["difference"]) == ref - eng
    # the joint rule moves the same 2.66625 m3 between beam (+) and column (-): it nets to 0 in the trade (one cause)
    assert Dd(b10["by_class"]["RULE_DIFFERENCE"]) == 0
    assert Dd(b10["by_class"]["HELD"]) == Dd("7.376418") + Dd("10.34925") + Dd("8.805") + Dd("1.65") + \
        Dd("10.564") + Dd("34.320562")


def test_held_never_zero_never_correct_and_no_pct_beside_held(real):
    _, sc = real
    for c in sc["reference_lines"]:
        if c["held_rows"]:
            assert c["pct_of_reference"] is None and c["line_status"] != "VERIFIED"
        for r in c["rows"]:
            if r["status"] == "HELD" and Dd(r["delta"]) == 0:
                assert r["held_bound"] and r["held_bound"][1] != "0"
            if r["status"] == "VERIFIED":
                assert "Checker" in (r["checker_citation"] or "")
    for a in sc["apart"]:
        assert a.get("pct_of_reference") is None


def test_pending_never_folded_in(real):
    st, sc = real
    tasks = [p["task"] for p in sc["pending_not_in_v10"]]
    assert {"T-600", "T-608", "T-616"} <= set(tasks)
    beams = next(c for c in sc["reference_lines"] if c["section_id"] == "T-545/beams@V10")
    assert beams["by_class"]["UNRESOLVED"] == "2.369278"                     # T-600 residual stays as in V10
    lint = next(a for a in sc["apart"] if a["section_id"] == "T-571/lintel-count-implied@V8")
    assert lint["difference"] == "-6"                                         # T-616 split not folded in
    assert "accuracy" not in T.markdown(sc).replace("not an accuracy claim", "").replace(
        "no product accuracy figure", "")


def test_no_client_text_in_outputs(real):
    _, sc = real
    txt = T.dumps(sc) + T.markdown(sc)
    assert not any("؀" <= ch <= "ۿ" for ch in txt)
    assert "reference_basis" not in txt
