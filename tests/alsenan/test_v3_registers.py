"""Alsenan V3a final BOQ - frozen registers (built twice from 245b4d3, byte-identical), the post-freeze benchmark
evaluation and the Qortuba V3 shadow. These tests read the frozen JSON only."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "tests/alsenan/registers_v3"
EVAL = ROOT / "tests/alsenan/registers_v3_eval"
pytestmark = pytest.mark.skipif(not REG.exists(), reason="V3 registers not frozen yet")
IN_TOTAL = ("COMPUTED", "PARTIAL")


def R(n, d=REG):
    return json.loads((d / f"{n}.json").read_text())


def _digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def test_register_digests_match_the_freeze_and_qa_passes():
    fz = R("FINAL_FREEZE")
    assert fz["phase"] == "V3a" and len(fz["register_digests"]) == 16
    for n, d in fz["register_digests"].items():
        assert _digest(R(n)) == d, n
    assert fz["boq_digest"] == _digest(R("BOQ_LINES")["lines"])
    qa = R("FINAL_QA")
    assert qa["state"] == "PASS" and all(qa["checks"].values())


def test_master_matrix_is_the_sum_of_like_lines_and_nothing_blocked_or_review_enters_a_total():
    lines = R("BOQ_LINES")["lines"]
    want = defaultdict(float)
    for x in lines:
        assert x["status"] in ("COMPUTED", "PARTIAL", "REVIEW", "BLOCKED", "NOT_IN_SOURCE"), x["line_id"]
        if x["status"] not in IN_TOTAL:
            assert x["status"] != "BLOCKED" or x["qty"] in (None, 0, 0.0), x["line_id"]
        elif x["sumrow"]:
            want[(x["trade"], x["sumrow"], x["unit"])] += x["qty"] or 0.0
    rows = R("MASTER_MATRIX")["rows"]
    assert len({(r["trade"], r["item"], r["unit"]) for r in rows}) == len(rows)
    for r in rows:
        assert abs(r["total"] - want.get((r["trade"], r["item"], r["unit"]), 0.0)) < 1e-3, r
        if r["status"] == "REVIEW":
            assert "REVIEW" in r["statuses"] and r["total"] == 0.0


def test_rebar_reports_net_and_procurement_and_never_a_ratio():
    m = {(r["item"]): r for r in R("MASTER_MATRIX")["rows"] if r["trade"] == "REBAR"}
    net, proc = m["Net design weight (complete sets)"], m["Procurement weight incl. laps (complete sets)"]
    assert net["status"] == proc["status"] == "COMPUTED" and proc["total"] >= net["total"] > 0
    assert m["Bar sets / members not computable"]["status"] == "BLOCKED"
    assert "kg/m3" not in json.dumps(R("REBAR_REGISTER")).replace(" ", "").lower()


def test_build_up_fallback_is_never_labelled_source_and_closures_carry_no_material():
    for x in R("BOQ_LINES")["lines"]:
        if "0.10" in (x["formula"] or "") and "build" in (x["formula"] or "").lower():
            assert "URBAN_FALLBACK" in (x["authority"] or "") + (x["formula"] or ""), x["line_id"]
    assert R("FINAL_QA")["checks"]["closures_zero_material"] and R("FINAL_QA")["checks"]["fallback_labelled"]


def test_evaluation_ran_after_this_exact_freeze_and_is_evaluation_only():
    ev = R("BENCHMARK_EVALUATION_V3", EVAL)
    assert ev["run"] == "AFTER_FREEZE" and ev["evaluation_only"] is True
    assert ev["v3_freeze_sha256"] == hashlib.sha256((REG / "FINAL_FREEZE.json").read_bytes()).hexdigest()
    assert R("FINAL_QA")["checks"]["benchmark_not_read"]


def test_qortuba_rc1_reference_unchanged_by_the_v3_engines():
    q = R("QORTUBA_V3_SHADOW", EVAL)
    assert q["state"] == "UNCHANGED" and q["frozen_sites"] == q["v3_sites"] == 72
    assert q["text_roles_v3_identical_sites"] and q["v3_two_pass_identical_sites"]
