"""Alsenan S2 adapter checks (project data): the brief's known issues must come out of the GENERIC detectors run on
the frozen S1 census - no flag id or Alsenan answer is written into the engine."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
S1 = ROOT / "research" / "alsenan_structural_census_s1"
S2 = ROOT / "research" / "alsenan_structural_s2"
sys.path.insert(0, str(S2))


@pytest.fixture(scope="module")
def run():
    import build_flags_s2 as A
    from engine.source import flag_detectors as FD
    idx, regs = A.load_s1()
    view = A.build_view(regs)
    return {"idx": idx, "regs": regs, "view": view, "flags": FD.detect(view)}


def _by(flags, detector):
    return [f for f in flags if f["detector"] == detector]


def test_s1_census_unchanged_and_consumed_by_hash(run):
    out = json.loads((S2 / "INDEX.json").read_text())
    assert out["s1_registers_consumed"] == {k: v["sha256"] for k, v in run["idx"]["registers"].items()}
    assert out["s1_census_modified"] is False and out["rebar_kg_calculated"] is False
    for k, v in run["idx"]["registers"].items():
        assert hashlib.sha256((S1 / v["file"]).read_bytes()).hexdigest() == v["sha256"]


def test_frozen_outputs_reproduce(run):
    flags = json.loads((S2 / "ALSENAN_ENGINEERING_FLAGS.json").read_text())["flags"]
    assert [(f["flag_id"], f["flag_key"]) for f in flags] == [(f["flag_id"], f["flag_key"]) for f in run["flags"]]


def test_required_issues_arise_from_generic_conditions(run):
    F = run["flags"]
    types = [set(c["value"] for c in f["context"].get("supporting_evidence", [])) | {f["source_a"]["value"],
                                                                                     f["source_b"]["value"]}
             for f in _by(F, "type_conflicts")]
    assert {"C3", "C"} in [t & {"C3", "C"} for t in types] and any({"C8", "C7"} <= t for t in types)
    assert _by(F, "single_level_members") and _by(F, "presence_gaps")                       # CN distinction
    band = _by(F, "band_gaps")
    assert len(band) == 1 and band[0]["issue_type"] == "RULE_GAP" and "80" in band[0]["issue_summary"]
    assert {o["answer"] for o in band[0]["answer_options"]} == {"50cm < L < 80cm", "80cm < L < 120cm"}
    tr = {f["issue_type"] for f in _by(F, "transverse_rules")}
    assert tr == {"AMBIGUOUS_APPLICABILITY", "ENGINEERING_METHOD_REQUIRED"}                 # 6/m sets + tie zone
    comp = _by(F, "competing_tags")
    assert any({f["source_a"]["value"], f["source_b"]["value"]} == {"F", "F10"} for f in comp)  # F / F10
    assert any({f["source_a"]["value"], f["source_b"]["value"]} == {"CB3", "B3"} for f in comp)  # one span, 2 marks
    assert any(f["context"] == {} and "BOXED" in f["affected_facts"] for f in _by(F, "unresolved_semantics"))
    assert any("SB2" in f["issue_summary"] for f in _by(F, "duplicate_definitions"))
    assert len(_by(F, "span_mismatches")) == 4                                            # CB4, CB5 x2, CB8
    assert {f["source_b"]["value"] for f in _by(F, "table_gaps")} == {160, 180}           # temperature table
    rd = {f["element_type"] for f in _by(F, "rule_dependent_elements")}
    assert {"STAIR", "GROUND_SLAB", "LIFT_PIT", "FOOTING", "BEAM", "SLAB"} <= rd           # stair / ground slab ...


def test_no_flag_is_hardcoded_in_the_adapter():
    src = (S2 / "build_flags_s2.py").read_text(encoding="utf-8")
    for token in ("STR-COL-", "STR-BEA-", "STR-FOO-", "flag_id\"] =", "make_flag("):
        assert token not in src, token


def test_claim_store_is_project_bound_and_empty_until_answered():
    c = json.loads((S2 / "ALSENAN_PROJECT_CLAIMS.json").read_text())
    assert c["claims"] == [] and c["project_id"] == "ALSENAN-ST7757"
    p = json.loads((S2 / "ALSENAN_RULE_PROMOTION_REGISTRY.json").read_text())
    assert p["registry"] == [] and all(x["state"] == "PROJECT_ONLY" for x in p["proposable_lessons"])


def test_every_open_flag_has_question_and_help(run):
    q = json.loads((S2 / "ALSENAN_CONSULTANT_QUESTIONS.json").read_text())
    h = json.loads((S2 / "ALSENAN_REVIEW_HELPER.json").read_text())
    open_ids = {f["flag_id"] for f in run["flags"] if f["status"] in ("OPEN", "PROVISIONAL_INTERPRETATION")}
    assert {x["flag_id"] for x in q} == open_ids == {x["flag_id"] for x in h}
    for x in q:
        assert x["QUESTION_TO_CONSULTANT"] and x["WHERE_TO_LOOK"]


def test_component_release_never_zeroes_an_element():
    r = json.loads((S2 / "ALSENAN_COMPONENT_RELEASE.json").read_text())
    by_el = {}
    for c in r["components"]:
        by_el.setdefault(c["element_id"], set()).add(c["release_state"])
    partial = [e for e, s in by_el.items() if "BLOCKED" in s and s - {"BLOCKED"}]
    assert partial  # blocked components coexist with released / lower-bound ones on the same element
    assert "kg" not in json.dumps(r["totals"])
