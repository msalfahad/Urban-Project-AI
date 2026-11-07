"""T-587: reconciled-quantities statement V7 adapters for T-576 (columns m3 by cause), T-578 (rails lm; nosing
cross-reference), T-583 (bar components t, beside) and T-584 (stair steps lm / nr; E1 / door steps in T-577 lm).
Synthetic villa "S587" (not the training villa) by hand: 2 column marks + 1 planted 1F column, 1 rail system,
1 stair; adverse cases (a worker-proposed row stamped VERIFIED, lm added to an m2 section / headline, one reference cell
owned by two sections, a high-open range given a high, a restated section whose totals moved, a V6 key changed), then
the merged training-villa sources (committed research outputs only; no private input)."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t587"))
import t587_adapters as A  # noqa: E402
import t587_build as B  # noqa: E402

Dd = Decimal
E = A.StatementError


# ------------------------------------------------------------------------------- T-576 columns (m3) ---------------
# S587 GF measured set, storey 4.50 m, his head depth 0.75 m:
#   M1: two drawn 0.20 x 0.50 (0.10 m2) columns x 4.50 = 0.90 m3; his ONE row 0.45 -> COUNT ours - his +0.45
#       (ENGINE_RIGHT); joint head on the one matched member 0.10 m3 (RULE_DIFFERENCE).
#   M2: one 0.20 x 0.667 column, engine 0.60 m3; joint head +0.08 (RD), global depth -0.02 (ENGINE_RIGHT).
#   engine 1.50; ours - his = 0.45 + 0.10 + 0.08 - 0.02 = 0.61 -> his 0.89; reference - engine = -0.61
#   (-68.54 %); by class ENGINE_RIGHT -0.43, RULE_DIFFERENCE -0.18.
# S587 1F: planted P1 engine 0.42 m3, joint head +0.07 -> his 0.35.
# V5 split of the same sets: GF COUNT -0.45, JOINT_HEAD -0.10, GLOBAL_DEPTH +0.02, HEIGHT_OPEN -0.08 UNRESOLVED
# (moves into JOINT_HEAD); 1F JOINT_HEAD -0.05, HEIGHT_OPEN -0.02 UNRESOLVED.
def _cols(conflict: bool = False) -> dict:
    m1 = [{"term": "COUNT", "class": "CONFLICT_BOUNDED" if conflict else "ENGINE_RIGHT", "m3": "0.45"},
          {"term": "JOINT_HEAD", "class": "RULE_DIFFERENCE", "m3": "0.10"}]
    gf = {"marks_all": [{"mark": "M1", "in_measured_set": True, "terms": m1},
                        {"mark": "M2", "in_measured_set": True,
                         "terms": [{"term": "JOINT_HEAD", "class": "RULE_DIFFERENCE", "m3": "0.08"},
                                   {"term": "GLOBAL_DEPTH", "class": "ENGINE_RIGHT", "m3": "-0.02"}]},
                        {"mark": "MX", "in_measured_set": False, "terms": [{"term": "HELD", "class": "HELD",
                                                                             "m3": "-9"}]}],
          "measured_set": {"marks": ["M1", "M2"], "engine_m3": "1.50", "his_m3": "0.89", "diff_m3": "0.61",
                           "open_counter_terms": []}}
    ff = {"marks_all": [{"mark": "P1", "in_measured_set": True,
                         "terms": [{"term": "JOINT_HEAD", "class": "RULE_DIFFERENCE", "m3": "0.07"}]}],
          "measured_set": {"marks": ["P1"], "engine_m3": "0.42", "his_m3": "0.35", "diff_m3": "0.07",
                           "open_counter_terms": []}}
    return {"GF": gf, "1F": ff}


def _s576() -> dict:
    return {"readings": [{"reading": {"10AE": "C3", "10E0": "C8"}, "columns": _cols()},
                         {"reading": {"10AE": "C", "10E0": "C8"}, "columns": _cols()},
                         {"reading": {"10AE": "C3", "10E0": "C7"}, "columns": _cols(conflict=True)}]}


def _v5() -> dict:
    def r(n, d, c):
        return {"name": n, "delta": d, "class": c}
    return {"sections_v5": [
        {"section_id": "T-572/measured-columns_GF", "reference_total": "0.89", "engine_valued": "1.50",
         "reference_basis": "S587 his rows", "rows": [r("columns_GF: COUNT", "-0.45", "ENGINE_RIGHT"),
                                                      r("columns_GF: JOINT_HEAD", "-0.10", "RULE_DIFFERENCE"),
                                                      r("columns_GF: GLOBAL_DEPTH", "0.02", "ENGINE_RIGHT"),
                                                      r("columns_GF: HEIGHT_OPEN", "-0.08", "UNRESOLVED")]},
        {"section_id": "T-572/measured-columns_1F", "reference_total": "0.35", "engine_valued": "0.42",
         "reference_basis": "S587 his rows", "rows": [r("columns_1F: JOINT_HEAD", "-0.05", "RULE_DIFFERENCE"),
                                                      r("columns_1F: HEIGHT_OPEN", "-0.02", "UNRESOLVED")]}]}


def test_t576_columns_by_hand():
    secs, moves = A.t576_sections(_s576(), _v5())
    gf = [c for c in secs if c["section_id"] == "T-576/columns-GF"][0]
    assert (gf["reference_total"], gf["engine_valued"], gf["difference"]) == ("0.89", "1.50", "-0.61")
    assert gf["difference_pct_of_reference"] == "-68.54" and gf["closure_residual"] == "0.00"
    assert Dd(gf["by_class"]["ENGINE_RIGHT"]) == Dd("-0.43") and Dd(gf["by_class"]["RULE_DIFFERENCE"]) == Dd("-0.18")
    ev = {r["name"]: r["evidence_status"] for r in gf["rows"]}
    assert ev["GF M1: COUNT"] == A.CV and ev["GF M1: JOINT_HEAD"] == A.PV and ev["GF M2: GLOBAL_DEPTH"] == A.WP
    assert [(m["delta"], m["from"], m["to"]) for m in moves] == [("-0.08", "UNRESOLVED", "RULE_DIFFERENCE"),
                                                                 ("-0.02", "UNRESOLVED", "RULE_DIFFERENCE")]
    alt = [c for c in secs if c["section_id"] == "T-576/columns-GF-reading-10E0-C7"][0]
    cnt = [r for r in alt["rows"] if r["name"] == "GF M1: COUNT"][0]
    assert cnt["class"] == "UNRESOLVED" and cnt["tag"] == "F-T587-4" and cnt["evidence_status"] == A.WP
    assert alt["difference_pct_of_reference"] is None and alt["reading_of_record"] is False


def test_t576_adverse_restate_moved_and_unmapped():
    v5 = _v5()
    v5["sections_v5"][0]["engine_valued"] = "1.40"                  # a rewrite, not a restatement
    with pytest.raises(E, match="differs from V5"):
        A.t576_sections(_s576(), v5)
    v5 = _v5()
    v5["sections_v5"][0]["rows"][2]["delta"] = "0.03"                # a term other than JOINT_HEAD moves
    with pytest.raises(E, match="GLOBAL_DEPTH"):
        A.t576_sections(_s576(), v5)
    d = _s576()
    d["readings"][0]["columns"]["GF"]["marks_all"][0]["terms"][0]["class"] = "GUESS"
    with pytest.raises(E, match="not mapped"):
        A.t576_sections(d, _v5())


def test_adverse_worker_proposed_row_stamped_verified():
    secs, _ = A.t576_sections(_s576(), _v5())
    gf = copy.deepcopy([c for c in secs if c["section_id"] == "T-576/columns-GF"][0])
    B.expected_evidence(gf["section_id"], gf["rows"][0])            # the map answers for every row
    for r in gf["rows"]:
        if r["term"] == "GLOBAL_DEPTH":
            r["evidence_status"] = A.CV                              # PLAUSIBLE only in the verdict
    with pytest.raises(E, match="stamped CHECKER_VERIFIED, the verdict gives WORKER_PROPOSED"):
        A.audit_evidence(gf, lambda r: B.expected_evidence(gf["section_id"], r))
    with pytest.raises(E, match="not a status"):
        A.stamp({"name": "x"}, "VERIFIED", "v")


# ------------------------------------------------------------------------------- T-578 rails (lm) -----------------
# S587: his one typed figure 2.00 lm; ours: balustrade 3.00 (flight 1.20 + level pieces 1.80) + guard 2.00 = 5.00.
# his - ours = -3.00 = guards -2.00 (ER) + flight run -1.20 (ER) + residual +0.20 (UNRESOLVED); held 0 with bound.
def _s578() -> dict:
    causes = [
        {"label": "roof / terrace guards S1", "verdict": "ENGINE_RIGHT", "kind": "SCOPE", "amount": "-2.00"},
        {"label": "ST-01 balustrade run RL-07 S587", "verdict": "ENGINE_RIGHT", "kind": "SCOPE", "amount": "-1.20"},
        {"label": "unexplained residual", "verdict": "UNRESOLVED", "kind": "RESIDUAL", "amount": "0.20"},
        {"label": "held pieces", "verdict": "HELD", "kind": "HELD", "amount": "0", "bound": ["0.5", None]},
        {"label": "both sides", "verdict": "AGREE", "kind": "MEASURE", "amount": "0"}]
    return {"rails_lm": {"sign": "his - ours", "ours": {"total": "5.00", "held_bound": {}, "by_family": {}},
                         "his": {"cell": "S.B1", "value": "2.00"}, "causes": causes, "pct_withheld": "HELD",
                         "like_for_like_hypothesis_A": {}, "reader_lines_retired": {}},
            "code_closure": {"FIN.RAILING": {"valued_lm": "3.00"}, "MET.RAILING.GUARD": {"valued_lm": "2.00"},
                             "FIN.STAIR.STEP_LM": {"valued_lm": "4.6"}, "nosing_lines_in_candidate": 0}}


def test_t578_rails_by_hand():
    sec = A.t578_rails(_s578())
    assert (sec["reference_total"], sec["engine_valued"], sec["difference"]) == ("2.00", "5.00", "-3.00")
    assert Dd(sec["by_class"]["ENGINE_RIGHT"]) == Dd("-3.20") and Dd(sec["by_class"]["UNRESOLVED"]) == Dd("0.20")
    assert sec["difference_pct_of_reference"] is None and len(sec["beside"]["agree_rows"]) == 1
    ev = {r["name"]: r["evidence_status"] for r in sec["rows"]}
    assert ev["ST-01 balustrade run RL-07 S587"] == A.CV and ev["roof / terrace guards S1"] == A.PV
    assert ev["held pieces"] == A.WP


def test_t578_adverse_candidate_mismatch():
    d = _s578()
    d["code_closure"]["FIN.RAILING"]["valued_lm"] = "2.90"
    with pytest.raises(E, match="candidate railing"):
        A.t578_rails(d)


# ------------------------------------------------------------------------------- T-584 steps (lm / nr) ------------
# S587 stair ST-01: 4 drawn treads, front edge 1.150 -> ours 4 x 1.15 = 4.60 lm; his 5 pieces x 1.20 = 6.00 lm.
# ours - his = -1.40 = width 4 x (1.15 - 1.20) = -0.20 (ER) + arrival edge 1 x 1.20 = -1.20 (RD). nr: 4 vs 5 (-1 RD).
# E1 (ST-03) stays with the marble lm section (owner of his cells).
def _s584() -> dict:
    lm = [{"id": "ST-01", "ours": "4.60", "his": "6.00", "gap": "-1.40",
           "causes": [{"label": "width", "verdict": "ENGINE_RIGHT", "kind": "MEASURE", "amount": "-0.20"},
                      {"label": "arrival edge", "verdict": "RULE_DIFFERENCE", "kind": "MEASURE", "amount": "-1.20"}]},
          {"id": "ST-03", "ours": "0", "his": "2.0", "gap": "-2.0",
           "causes": [{"label": "E1", "verdict": "ENGINE_OMISSION", "kind": "MEASURE", "amount": "-2.0"}]}]
    nr = [{"id": "ST-01", "ours": "4", "his": "5", "gap": "-1",
           "causes": [{"label": "arrival", "verdict": "RULE_DIFFERENCE", "kind": "MEASURE", "amount": "-1"}]},
          {"id": "ST-03", "ours": "0", "his": "1", "gap": "-1",
           "causes": [{"label": "E1", "verdict": "ENGINE_OMISSION", "kind": "MEASURE", "amount": "-1"}]}]
    return {"sign": "ours - his", "tables": {"stairs": {"lm": lm, "nr": nr,
                                                       "m2": [{"his": "8.0"}]}}}


def test_t584_steps_by_hand():
    secs, nc = A.t584_sections(_s584(), _s578())
    lm = [c for c in secs if c["unit"] == "lm"][0]
    nr = [c for c in secs if c["unit"] == "nr"][0]
    assert (lm["reference_total"], lm["engine_valued"], lm["difference"]) == ("6.00", "4.60", "1.40")
    assert Dd(lm["by_class"]["ENGINE_RIGHT"]) == Dd("0.20") and Dd(lm["by_class"]["RULE_DIFFERENCE"]) == Dd("1.20")
    assert (nr["reference_total"], nr["engine_valued"], nr["difference"]) == ("5", "4", "1")
    assert all(r["evidence_status"] == A.PV for r in lm["rows"])
    assert nc[0]["reference_total"] == "6.00" and nc[0]["difference_pct_of_reference"] is None


def test_adverse_lm_added_to_m2():
    secs, _ = A.t584_sections(_s584(), _s578())
    lm = copy.deepcopy([c for c in secs if c["unit"] == "lm"][0])
    lm["unit"] = "m2"                                                  # an lm row inside an m2 section
    with pytest.raises(E, match="in lm, section in m2"):
        A.close_section(lm)
    with pytest.raises(E, match="summed into a m2 headline"):
        A.by_class_evidence(secs[0]["rows"], "m2", lambda r: r["evidence_status"])


def test_adverse_one_cell_two_sections():
    d = _s578()
    d["nosing_lm"] = {"groups": [{"stair": "ST-01", "his_cells": "S.B23", "his": "6.00", "ours": "4.6",
                                  "held_bound": None, "causes": []},
                                 {"stair": "ST-03", "his_cells": "S.B23", "his": "2.0", "ours": "2.0",
                                  "held_bound": None, "causes": []}],
                      "totals": {"his": "8", "ours": "6.6", "gap": "1.4", "held_n": 0}}
    d["nosing_nr"] = {"totals": {"his": "6", "ours": 5, "gap": "1"}}
    secs, _ = A.t584_sections(_s584(), d)
    marble = {"engine_valued": "0", "rows": [{"name": "E1_STEPS: x", "delta": "2.0"}]}
    with pytest.raises(E, match="owned by two sections"):
        A.t578_nosing_xref(d, secs, marble)
    d["nosing_lm"]["groups"][1]["his_cells"] = "S.B16"
    x = A.t578_nosing_xref(d, secs, marble)
    assert x["difference_added"] is False and [c["owned_by_section"] for c in x["census"]] == \
        ["T-584/stair-steps-lm", "T-577/marble-lm@V7"]


# ------------------------------------------------------------------------------- T-583 high-open rows (t) ---------
def test_adverse_high_open_rows():
    ok = {"row_id": "R1", "unit": "t", "status": "HELD_RANGE_HIGH_OPEN", "t_low": 0.1, "t_high": None,
          "t_high_bounded_part": 0.2}
    A.check_high_open(ok)
    with pytest.raises(E, match="no high"):
        A.check_high_open(dict(ok, t_high=0.2))                       # a bounded part shown as a high
    with pytest.raises(E, match="inside a t block"):
        A.check_high_open(dict(ok, unit="kg"))
    with pytest.raises(E, match="carried as a value"):
        A.check_high_open(dict(ok, value=0.15))
    with pytest.raises(E, match="HELD_BLANK"):
        A.check_high_open({"row_id": "R2", "unit": "t", "status": "HELD_BLANK", "t_low": 0.1, "missing": "h"})


# ------------------------------------------------------------------------------- training villa (merged sources) --
@pytest.fixture(scope="module")
def st():
    return B.build()


def test_build_reproduces_committed_output(st):
    assert st == json.loads(B.JSON_OUT.read_text(encoding="utf-8"))
    assert B.to_markdown(st) == B.MD_OUT.read_text(encoding="utf-8")


def test_v6_carried_byte_equal(st):
    st6 = B.v6_statement()
    B.check_v6_unchanged(st, st6)
    bad = copy.deepcopy(st)
    bad["sections_v6"][0]["difference"] = "0"
    with pytest.raises(E, match="sections_v6 changed"):
        B.check_v6_unchanged(bad, st6)
    assert st["released_quantities_changed"] == 0


def test_alsenan_sections_close_and_restate(st):
    secs = {c["section_id"]: c for c in st["sections_v7"]}
    for c in secs.values():
        assert sum((Dd(r["delta"]) for r in c["rows"]), Dd(0)) == Dd(c["reference_total"]) - Dd(c["engine_valued"])
    gf, ff = secs["T-576/columns-GF"], secs["T-576/columns-1F"]
    assert (gf["difference"], gf["by_class"]["ENGINE_RIGHT"], gf["by_class"]["RULE_DIFFERENCE"]) == \
        ("-1.173750", "0.860000", "-2.033750")
    assert (ff["difference"], ff["by_class"]["RULE_DIFFERENCE"]) == ("-0.555000", "-0.460000")
    assert secs["T-578/rails"]["difference"] == "-35.919174"
    assert (secs["T-584/stair-steps-lm"]["reference_total"], secs["T-584/stair-steps-lm"]["engine_valued"]) == \
        ("109.2", "67.850")
    m = secs["T-577/marble-lm@V7"]
    e1 = [r for r in m["rows"] if r.get("tag") == "F-T587-3"][0]
    assert (e1["class"], e1["delta"], e1["evidence_status"]) == ("ENGINE_WRONG", "11.2", A.CV)
    assert m["difference"] == "-35.13" and "UNRESOLVED" in m["by_class"]
    assert secs["T-545/beams@V7"]["by_class"]["UNRESOLVED"] == "0"


def test_alsenan_headline_labels_proposed(st):
    h = {x["section_id"]: x for x in st["headline_v7"]}
    assert h["T-577/marble-m2"]["by_class_evidence"]["ENGINE_RIGHT"] == {A.WP: "-11.6888"}   # F-C-T586-1
    assert h["T-577/marble-nr"]["by_class_evidence"]["ENGINE_RIGHT"] == {A.WP: "-47"}
    assert h["T-577/marble-lm"]["superseded_by"] == "T-577/marble-lm@V7"
    assert "ENGINE_RIGHT -11.6888 [WP -11.6888]" in B.to_markdown(st)


def test_alsenan_cells_once_and_beside(st):
    x = [b for b in st["beside_v7"] if b["block_id"] == "T-578/nosing-xref"][0]
    assert [c["owned_by_section"] for c in x["census"]] == ["T-584/stair-steps-lm"] * 2 + ["T-577/marble-lm@V7"]
    assert x["difference_added"] is False and x["candidate_line"] is False
    b = [b for b in st["beside_v7"] if b["block_id"] == "T-583/dome-lift-components"][0]
    assert (b["at_least_t"], b["valued_t"], b["bounded_part_t_not_a_high"]) == ("0.767783", "0", "1.164174")
    assert b["expected_after_v8_rebar_rows"]["held_high"] == "OPEN"
    ids = [c["section_id"] for k in ("sections", "sections_v5", "sections_v6", "sections_v7") for c in st[k]]
    assert len(ids) == len(set(ids))
