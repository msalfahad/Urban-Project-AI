"""Generic structural review engine (S2) - synthetic, project-independent tests.

No project coordinates, marks or totals: every case is built here from invented members (TYPE-A, TYPE-B ...).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from engine.source import engineering_flags as EF
from engine.source import flag_detectors as FD
from engine.source import project_claims as PC
from engine.source import question_helper as QH
from engine.source import rule_promotion as RP
from engine.source import structural_authority as SA

ROOT = Path(__file__).resolve().parents[2]
REF = {"drawing": "SYN-01.dxf", "sheet_title": "SYNTHETIC PLAN", "page": 1}


def ev(value, authority, desc, **ref):
    return {"value": value, "authority": authority, "description": desc, "source_ref": dict(REF, **ref)}


def view(**collections):
    return dict({"project_id": "PRJ-SYN", "drawing_revision": "R0"}, **collections)


# ---------------------------------------------------------------------------------------------- 1 plan vs local
def test_plan_says_one_type_schedule_or_local_says_another():
    # two plan tags disagree (equal tier) -> SOURCE_CONFLICT; a local element note outranks both
    cands = [ev("TYPE-A", SA.PLAN_MEMBER_TAG, "plan 1 tag", text="TYPE-A"),
             ev("TYPE-B", SA.PLAN_MEMBER_TAG, "plan 2 tag", text="TYPE-B")]
    d = SA.resolve("MEMBER_TYPE", cands)
    assert d["state"] == SA.SOURCE_CONFLICT and d["value"] is None
    d2 = SA.resolve("MEMBER_TYPE", cands + [ev("TYPE-B", SA.LOCAL_ELEMENT_NOTE, "note on the member")])
    assert d2["state"] == SA.RESOLVED_WITH_OVERRIDE and d2["value"] == "TYPE-B"
    assert [o["value"] for o in d2["overridden"]] == ["TYPE-A"]
    flags = FD.detect(view(type_evidence=[{"element_type": "COLUMN", "element_id": "EL-1", "evidence": cands,
                                           "quantity": 2, "unit": "nr"}]))
    assert len(flags) == 1 and flags[0]["issue_type"] == "SOURCE_CONFLICT" and flags[0]["release_effect"] == EF.BLOCKED


def test_shared_definition_field_is_not_blocked_by_a_type_conflict():
    cands = [ev("TYPE-A", SA.PLAN_MEMBER_TAG, "plan 1"), ev("TYPE-B", SA.PLAN_MEMBER_TAG, "plan 2")]
    defs = {"TYPE-A": {"section": [30, 50], "reinforcement": "8x16"}, "TYPE-B": {"section": [30, 50],
                                                                               "reinforcement": "10x16"}}
    f = FD.detect(view(type_evidence=[{"element_type": "COLUMN", "element_id": "EL-1", "evidence": cands,
                                       "definitions": defs}]))[0]
    assert "section" not in f["affected_facts"] and "reinforcement" in f["affected_facts"]
    assert "CONCRETE" not in f["trade"]


# ---------------------------------------------------------------------------------------------- 2 single level
def test_member_existing_on_one_floor_only_is_flagged_not_dropped():
    flags = FD.detect(view(single_level_members=[{"element_type": "COLUMN", "member_type": "TYPE-N",
                                                  "level": "LEVEL-0", "element_ids": ["N1", "N2"],
                                                  "peers_continue": True, "quantity": 2, "unit": "nr"}]))
    assert len(flags) == 1 and flags[0]["issue_type"] == "AMBIGUOUS_APPLICABILITY"
    assert flags[0]["status"] == EF.PROVISIONAL and flags[0]["element_ids"] == ["N1", "N2"]
    assert not FD.detect(view(single_level_members=[{"element_type": "COLUMN", "member_type": "TYPE-N",
                                                     "level": "LEVEL-0", "element_ids": ["N1"],
                                                     "peers_continue": False}]))


# ---------------------------------------------------------------------------------------------- 3 band boundary
def test_exact_rule_boundary_uncovered_is_a_rule_gap():
    bands = [{"band_id": "B1", "description": "x <= 10"}, {"band_id": "B2", "description": "10 < x < 20"},
             {"band_id": "B3", "description": "20 < x < 30"}]
    items = [{"element_type": "COLUMN", "element_id": f"E{i}", "member_type": "TYPE-C", "rule_ref": "R-BAND",
              "rule_text": "synthetic band rule", "value": 20, "value_unit": "cm", "state": "BOUNDARY_GAP",
              "bands": bands, "quantity": 1, "unit": "nr"} for i in range(3)]
    f = FD.detect(view(band_lookups=items))
    assert len(f) == 1 and f[0]["issue_type"] == "RULE_GAP" and len(f[0]["element_ids"]) == 3
    assert {o["answer"] for o in f[0]["answer_options"]} == {b["description"] for b in bands}
    assert f[0]["generic_rule_candidate"]  # offered for review, never applied


# ---------------------------------------------------------------------------------------------- 4 local > default
def test_local_detail_overrides_project_default():
    d = SA.resolve("SLAB_THICKNESS", [ev(160, SA.PROJECT_GENERAL_NOTE, "general note"),
                                      ev(180, SA.LOCAL_ELEMENT_NOTE, "panel mark")])
    assert d["value"] == 180 and d["authority"] == SA.LOCAL_ELEMENT_NOTE
    assert d["state"] == SA.RESOLVED_WITH_OVERRIDE and d["overridden"][0]["value"] == 160
    assert SA.resolve("SLAB_THICKNESS", [])["state"] == SA.BLOCKED  # no fallback is invented


# ---------------------------------------------------------------------------------------------- 5 equal authorities
def test_two_equal_authority_sources_conflict():
    # for MEMBER_SECTION a local detail and the schedule are comparable -> conflict, never a pick
    d = SA.resolve("MEMBER_SECTION", [ev([30, 60], SA.LOCAL_DETAIL, "detail"),
                                      ev([30, 50], SA.MEMBER_SCHEDULE, "schedule")])
    assert d["state"] == SA.SOURCE_CONFLICT and len(d["conflicting"]) == 2
    # the order is per fact type: a project may rank them differently
    orders = dict(SA.DEFAULT_ORDERS, MEMBER_SECTION=[[SA.MEMBER_SCHEDULE], [SA.LOCAL_DETAIL]])
    d2 = SA.resolve("MEMBER_SECTION", d["candidates"], orders=orders)
    assert d2["value"] == [30, 50]


# ---------------------------------------------------------------------------------------------- 6 claim resolves
def _flag():
    return FD.detect(view(competing_tags=[{"element_type": "FOOTING", "element_id": "FT-X",
                                           "candidates": ["TYPE-P", "TYPE-Q"], "quantity": 1, "unit": "nr"}]))[0]


def test_human_project_claim_resolves_conflict():
    f = _flag()
    c = PC.make_claim(project_id="PRJ-SYN", claim_id="CL-1", kind=PC.ADJUDICATION, fact="member_type",
                      value="TYPE-Q", source_person="engineer", date="2026-01-01", drawing_revision="R0",
                      flag_keys=[f["flag_key"]])
    out, log = PC.apply_to_flags([f], [c], project_id="PRJ-SYN", drawing_revision="R0")
    assert out[0]["status"] == EF.RESOLVED and out[0]["resolution"] == "TYPE-Q"
    assert out[0]["resolution_source"] == "CL-1" and log[0]["result"] == "RESOLVED"
    # the authority model records the adjudication with the conflicting sources kept
    d = SA.resolve("MEMBER_TYPE", [ev("TYPE-P", SA.PLAN_MEMBER_TAG, "a"), ev("TYPE-Q", SA.PLAN_MEMBER_TAG, "b")],
                   adjudication={"value": "TYPE-Q", "claim_id": "CL-1"})
    assert d["state"] == SA.RESOLVED_BY_CLAIM and len(d["conflicting"]) == 2


# ---------------------------------------------------------------------------------------------- 7 no leakage
def test_claim_cannot_leak_to_another_project_or_revision():
    f = _flag()
    other = dict(f, project_id="PRJ-OTHER")
    c = PC.make_claim(project_id="PRJ-SYN", claim_id="CL-1", kind=PC.ADJUDICATION, fact="member_type",
                      value="TYPE-Q", source_person="engineer", date="2026-01-01", drawing_revision="R0",
                      flag_keys=[f["flag_key"]])
    out, log = PC.apply_to_flags([other], [c], project_id="PRJ-OTHER", drawing_revision="R0")
    assert out[0]["status"] == EF.OPEN and log[0]["result"] == PC.PROJECT_MISMATCH
    out, log = PC.apply_to_flags([f], [c], project_id="PRJ-SYN", drawing_revision="R1")
    assert out[0]["status"] == EF.OPEN and log[0]["result"] == PC.REVISION_MISMATCH
    a = PC.make_claim(project_id="PRJ-SYN", claim_id="CL-2", kind=PC.ASSERTION, fact="depth", value=1.2,
                      source_person="engineer", date="2026-01-01", drawing_revision="R0",
                      element_filter={"element_type": "PIT", "element_id": ["P1"]})
    assert PC.applicability(a, project_id="PRJ-SYN", drawing_revision="R0",
                            element={"element_type": "PIT", "element_id": "P1"}) == PC.APPLIES
    assert PC.applicability(a, project_id="PRJ-SYN", drawing_revision="R0",
                            element={"element_type": "PIT", "element_id": "P2"}) == PC.SCOPE_MISMATCH
    # supersession: the newer claim applies, the older stays stored
    b = PC.make_claim(project_id="PRJ-SYN", claim_id="CL-3", kind=PC.ASSERTION, fact="depth", value=1.4,
                      source_person="engineer", date="2026-02-01", drawing_revision="R0",
                      element_filter={"element_type": "PIT"}, supersedes="CL-2")
    assert PC.active([a, b]) == [b]
    assert PC.applicability(a, project_id="PRJ-SYN", drawing_revision="R0", claims=[a, b],
                            element={"element_type": "PIT", "element_id": "P1"}) == PC.SUPERSEDED_CLAIM


# ---------------------------------------------------------------------------------------------- 8 component release
def test_known_component_releasable_while_unknown_component_blocked():
    f = FD.detect(view(unresolved_semantics=[{"element_type": "FOOTING", "field": "EXTRA_CAGE",
                                              "member_types": ["TYPE-P"], "raw_values": {"TYPE-P": "2+3"},
                                              "element_ids": ["FT-1"]}]))[0]
    comps = [{"element_id": "FT-1", "component": "BOTTOM_BARS", "trade": "REINFORCEMENT", "quantity": 100.0,
              "unit": "kg", "depends_on": ["reinforcement"]},
             {"element_id": "FT-1", "component": "EXTRA_CAGE", "trade": "REINFORCEMENT", "quantity": None,
              "unit": "kg", "depends_on": ["EXTRA_CAGE"]},
             {"element_id": "FT-1", "component": "CONCRETE", "trade": "CONCRETE", "quantity": 1.5, "unit": "m3",
              "depends_on": ["section"]}]
    rel = {c["component"]: c["release_state"] for c in EF.component_release(comps, [f])}
    assert rel == {"BOTTOM_BARS": EF.VERIFIED, "EXTRA_CAGE": EF.BLOCKED, "CONCRETE": EF.VERIFIED}
    tot = EF.release_totals(EF.component_release(comps, [f]))
    assert tot["REINFORCEMENT|kg"]["released"] == 100.0 and tot["CONCRETE|m3"]["released"] == 1.5
    # a type conflict blocks type-dependent bars but a lower-bound flag keeps the proven part
    lb = dict(f, flag_key="LB", affected_facts=["reinforcement"], release_effect=EF.LOWER_BOUND)
    rel2 = {c["component"]: c["release_state"] for c in EF.component_release(comps, [lb])}
    assert rel2["BOTTOM_BARS"] == EF.LOWER_BOUND and rel2["CONCRETE"] == EF.VERIFIED


# ---------------------------------------------------------------------------------------------- 9 audit history
def test_resolved_flag_preserves_audit_history():
    f = _flag()
    f1 = EF.transition(f, EF.PROVISIONAL, by="engine", note="interim reading")
    f2 = EF.transition(f1, EF.SENT, by="reviewer", at="2026-01-02")
    f3 = EF.transition(f2, EF.ANSWERED, by="consultant", at="2026-01-05", resolution="TYPE-P",
                       resolution_source="letter-7")
    f4 = EF.transition(f3, EF.RESOLVED, by="reviewer", at="2026-01-06", resolution="TYPE-P",
                       resolution_source="letter-7")
    assert [h["to"] for h in f4["history"]] == [EF.OPEN, EF.PROVISIONAL, EF.SENT, EF.ANSWERED, EF.RESOLVED]
    assert f["status"] == EF.OPEN and len(f["history"]) == 1          # the original is not mutated
    with pytest.raises(ValueError):
        EF.transition(f4, EF.OPEN, by="x")                          # resolved cannot silently reopen
    assert EF.transition(f4, EF.SUPERSEDED, by="x")["history"][-2]["to"] == EF.RESOLVED


# ---------------------------------------------------------------------------------------------- 10 promotion
def test_generic_promotion_cannot_happen_automatically():
    c = PC.make_claim(project_id="PRJ-SYN", claim_id="CL-9", kind=PC.ADJUDICATION, fact="band",
                      value="upper band", source_person="engineer", date="2026-01-01", drawing_revision="R0",
                      flag_keys=["k"])
    assert c["promotion_state"] == RP.PROJECT_ONLY
    with pytest.raises(ValueError):    # project marks may not leak into a generic statement
        RP.propose(statement="TYPE-C uses 3 ties", condition="TYPE-C", consequence="3 ties", source_claims=[c],
                   proposer="analyst", at="t", forbidden_terms=["TYPE-C"])
    cand = RP.propose(statement="At an uncovered band limit use the upper band",
                      condition="value equals a printed limit included by no band",
                      consequence="detail with the upper band", source_claims=[c], proposer="analyst", at="t",
                      forbidden_terms=["TYPE-C"])
    assert cand["state"] == RP.GENERIC_CANDIDATE and RP.approved([cand]) == []
    with pytest.raises(ValueError):
        RP.review(cand, reviewer="analyst", at="t", approve=True, note="self approval")
    ok = RP.review(cand, reviewer="chief engineer", at="t2", approve=True, note="checked on two projects")
    assert RP.approved([cand, ok]) == [ok] and ok["history"][0]["to"] == RP.GENERIC_CANDIDATE


# ---------------------------------------------------------------------------------------------- helper + summary
def test_question_and_help_blocks_are_generated_from_context():
    f = FD.detect(view(transverse_rules=[{
        "element_type": "COLUMN", "rule_ref": "R-TIES", "rule_text": "column ties 6 per metre", "per_metre": True,
        "zone_length_state": "BLOCKED", "element_ids": ["E1", "E2"],
        "bands": [{"band_id": "B2", "closed_ties_per_set": 2, "element_ids": ["E2"]}],
        "source_refs": [dict(REF, handle="AB12", layer="S-TEXT", text="TIES 6/m")]}]))
    assert {x["issue_type"] for x in f} == {"AMBIGUOUS_APPLICABILITY", "ENGINEERING_METHOD_REQUIRED"}
    q = QH.consultant_question(f[0])
    for k in ("PLAIN_LANGUAGE_ISSUE", "WHY_IT_MATTERS", "WHERE_TO_LOOK", "WHAT_THE_DRAWING_SAYS",
              "ENGINE_CURRENT_INTERPRETATION", "QUESTION_TO_CONSULTANT", "QUANTITY_BOQ_IMPACT"):
        assert q[k] not in (None, "", [])
    h = QH.help_mode(f[0])
    assert "tie" in h["TERMS_EXPLAINED"] and any("AB12" in s for s in h["WHAT_TO_SEARCH_IN_AUTOCAD"])
    assert any("TIES 6/m" in s for s in h["WHAT_TO_SEARCH_IN_AUTOCAD"]) and h["WHAT_WOULD_EACH_ANSWER_CHANGE"]
    s = EF.summary(f)
    assert s["by_discipline"]["STRUCTURAL"]["total"] == 2 and s["final_quantity_pending_consultant"] is True
    assert "2 structural flags open" in s["front_summary_lines"] and s["pricing_integrated"] is False


def test_flag_keys_are_stable_and_ids_deterministic():
    items = [{"element_type": "BEAM", "element_id": f"BM-{i}", "tag": "TYPE-X", "candidates": ["L1", "L2"]}
             for i in (3, 1, 2)]
    a = FD.detect(view(ambiguous_bindings=items))
    b = FD.detect(view(ambiguous_bindings=list(reversed(items))))
    assert [(f["flag_id"], f["flag_key"]) for f in a] == [(f["flag_id"], f["flag_key"]) for f in b]
    assert a[0]["flag_id"] == "STR-BEA-001"


# ---------------------------------------------------------------------------------------------- firewall
GENERIC = ["structural_authority.py", "engineering_flags.py", "project_claims.py", "rule_promotion.py",
           "question_helper.py", "flag_detectors.py"]


def test_generic_modules_hold_no_project_data():
    names = re.compile(r"alsenan|st7757|p7757|qortuba|rashed|160 ?mm|44\.19", re.I)
    marks = re.compile(r"\b(?:C|F|SB|CB|GB|B)\d{1,2}\b|\bX\d{2}-Y\d{2}\b")   # member marks / grid refs (upper case)
    for m in GENERIC:
        src = (ROOT / "engine" / "source" / m).read_text(encoding="utf-8")
        hits = names.findall(src) + marks.findall(src)
        assert not hits, (m, hits[:5])


def test_schemas_are_complete():
    for mod, name in ((EF, "ENGINEERING_FLAG_SCHEMA"), (SA, "SOURCE_AUTHORITY_MODEL"), (PC, "PROJECT_CLAIM_SCHEMA"),
                      (QH, "QUESTION_HELPER_SCHEMA"), (RP, "RULE_PROMOTION_SCHEMA")):
        s = mod.schema()
        assert s["schema"] == name and s["rules"]
    assert set(EF.schema()["issue_types"]) >= {"SOURCE_CONFLICT", "RULE_GAP", "MISSING_DIMENSION",
                                               "MISSING_SCHEDULE", "UNBOUND_OCCURRENCE", "AMBIGUOUS_APPLICABILITY",
                                               "MISSING_DETAIL", "UNIT_CONFLICT", "REVISION_CONFLICT",
                                               "ENGINEERING_METHOD_REQUIRED"}
