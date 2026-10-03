"""R8.4 §18-§22, §35 — reference-region DESIGNATION replaces bare reference=True; deterministic
region candidates are candidates, never designations; UNKNOWN regions never inherit plan authority."""

from __future__ import annotations

import pytest

from engine.source import findings as F
from engine.source import frame as FR
from engine.source import region_candidates as RC
from tests.r8_0 import libredwg_builder as B
from tests.r8_0.k1_harness import _imports, apply_test_schema_extensions

SHA = "d" * 64


def verified_unit(policy=None):
    ev = list(FR.declaration_evidence(4, "MS", SHA)[0]) + [
        FR.UnitEvidence("PLOT", FR.NATIVE_UNIT, FR.KNOWN_PLOT_DIMENSION, "MS", ("AUTHORED:PLOT",), 1.0,
                        source_sha256=SHA, producer=FR.HUMAN),
        FR.UnitEvidence("NOTE", FR.NATIVE_UNIT, FR.EXPLICIT_UNIT_NOTE, "MS", ("AUTHORED:NOTE",), 1.0, source_sha256=SHA)]
    kw = {"policy": policy} if policy else {}
    return FR.unit_context(SHA, "MS", FR.MODEL_SPACE, ev, insunits=4, **kw)


def des(basis=FR.SOURCE_PLAN_LABEL, producer=FR.ENGINE, review=FR.ACCEPTED, **kw):
    base = dict(designation_id=f"DES:{basis}", source_sha256=SHA, coordinate_space_id="MS", region_id="PLAN",
                basis=basis, source_ref="TEXT:H1F 'GROUND FLOOR PLAN'", producer=producer, review_status=review)
    base.update(kw)
    return FR.ReferenceRegionDesignation(**base)


def plan(unit, **kw):
    return FR.region_transform(unit, "PLAN", FR.MODEL_SPACE_PLAN, **kw)


def codes(r):
    return {f.code for f in r.findings}


def test_bare_reference_confers_no_authority_under_v2():
    r = plan(verified_unit(), reference=True)
    assert r.status == FR.UNCONFIRMED and not r.reference and FR.FINAL_MEASUREMENT not in r.allowed_use
    assert F.REFERENCE_REGION_UNDESIGNATED in codes(r)


def test_v1_bare_reference_reproducible():
    r = plan(verified_unit(FR.RELEASE_V1), reference=True)
    assert r.status == FR.VERIFIED and r.status_reason == "REFERENCE_REGION_BY_DEFINITION" and r.policy_id == FR.RELEASE_V1_ID


@pytest.mark.parametrize("basis", [FR.SOURCE_PLAN_LABEL, FR.PROJECT_ADAPTER_CLAIM, FR.DETERMINISTIC_REGION_ROLE,
                                   FR.OTHER_AUTHORIZED_EVIDENCE])
def test_accepted_machine_basis_verifies_and_is_recorded(basis):
    u = verified_unit()
    r = plan(u, reference=True, designation=des(basis))
    assert r.status == FR.VERIFIED and r.reference and r.designation_id == f"DES:{basis}" and r.reference_basis == basis
    assert FR.FINAL_MEASUREMENT in FR.measurement_frame(u, r).allowed_use


def test_human_designation_needs_author_time_and_authorised_role():
    u = verified_unit()
    ok = plan(u, designation=des(FR.HUMAN_DESIGNATION, FR.HUMAN, author="M", timestamp="2026-09-30T10:00Z",
                                 author_role="PROJECT_ARCHITECT"))
    assert ok.status == FR.CONFIRMED_BY_HUMAN and FR.FINAL_MEASUREMENT in ok.allowed_use
    for bad, why in ((des(FR.HUMAN_DESIGNATION, FR.HUMAN, author="M", author_role="PROJECT_ARCHITECT"), "INCOMPLETE"),
                     (des(FR.HUMAN_DESIGNATION, FR.HUMAN, author="M", timestamp="t", author_role="VISITOR"), "ROLE"),
                     (des(FR.HUMAN_DESIGNATION, FR.ENGINE, author="M", timestamp="t", author_role="PROJECT_OWNER"),
                      "INCOMPLETE")):
        r = plan(u, designation=bad)
        assert r.status == FR.UNCONFIRMED and F.REFERENCE_REGION_DESIGNATION_REJECTED in codes(r)
        assert any(why in f.detail for f in r.findings if f.code == F.REFERENCE_REGION_DESIGNATION_REJECTED)


@pytest.mark.parametrize("bad", [
    des(review=FR.CANDIDATE), des(review="PENDING_REVIEW"), des(producer=FR.AGENT), des(source_sha256="e" * 64),
    des(coordinate_space_id="OTHER"), des(region_id="ELSEWHERE"), des(basis="VIBES"), des(source_ref="")])
def test_candidate_agent_or_mismatched_designation_is_rejected(bad):
    r = plan(verified_unit(), reference=True, designation=bad)
    assert r.status != FR.VERIFIED and not r.reference and F.REFERENCE_REGION_DESIGNATION_REJECTED in codes(r)


def test_designation_never_overrides_contradicting_region_evidence():
    note = FR.UnitEvidence("PLAN:1:50", FR.REGION_SCALE, FR.EXPLICIT_SCALE_NOTE, "PLAN", ("AUTHORED:PLAN:NOTE",), 0.02,
                           source_sha256=SHA)
    r = plan(verified_unit(), evidence=[note], designation=des())
    assert r.status != FR.VERIFIED and FR.FINAL_MEASUREMENT not in r.allowed_use


def test_unknown_region_is_blocked_without_evidence_and_cannot_be_reference():
    u = verified_unit()
    r = FR.region_transform(u, "X", FR.MODEL_SPACE_UNKNOWN)
    assert r.status == FR.BLOCKED and r.status_reason.startswith("U-2")
    assert not {FR.FINAL_MEASUREMENT, FR.PREVIEW_MEASUREMENT} & set(r.allowed_use)
    with pytest.raises(ValueError):
        FR.region_transform(u, "X", FR.MODEL_SPACE_UNKNOWN, reference=True)
    with pytest.raises(ValueError):
        FR.region_transform(u, "X", FR.MODEL_SPACE_UNKNOWN, designation=des(region_id="X"))


def test_u2_detail_and_paper_space_rules_kept():
    u = verified_unit()
    assert FR.region_transform(u, "D", FR.MODEL_SPACE_DETAIL).status_reason == "U-2: DETAIL_SCALE_WITHOUT_REGION_EVIDENCE"
    assert FR.measurement_authority(FR.PAPER_SPACE_VIEWPORT) == (False, "MEASURE_IN_MODEL_FRAME")


def test_evidence_digest_versions_region_and_frame():
    u = verified_unit()
    a, b = plan(u, designation=des()), plan(u, designation=des())
    assert a.evidence_digest == b.evidence_digest
    c = plan(u, designation=des(FR.PROJECT_ADAPTER_CLAIM))
    assert c.evidence_digest != a.evidence_digest
    u2 = FR.unit_context(SHA, "MS", FR.MODEL_SPACE, list(FR.declaration_evidence(4, "MS", SHA)[0]), insunits=4)
    fa, fb = FR.measurement_frame(u, a), FR.measurement_frame(u2, plan(u2, designation=des()))
    assert fa.evidence_digest != fb.evidence_digest


# ---------------------------------------------------------------- region candidates

def _box(x0, y0, w, h):
    pts = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h), (x0, y0)]
    return [{"kind": "LINE", "a": pts[i], "b": pts[i + 1]} for i in range(4)] + [
        {"kind": "LINE", "a": (x0 + w * t / 10, y0), "b": (x0 + w * t / 10, y0 + h)} for t in range(1, 10)]


SCENE = {"entities": _box(0, 0, 20000, 15000) + _box(60000, 0, 8000, 8000) + _box(0, 40000, 9000, 6000) + [
    {"kind": "TEXT", "at": (1000, 1000), "text": "GROUND FLOOR PLAN 1:100"},
    {"kind": "TEXT", "at": (61000, 1000), "text": "DETAIL A 1:20"},
    {"kind": "TEXT", "at": (500, 40500), "text": "NOTES"}]}


def cands(scene=SCENE):
    _, kernel, lm = _imports()
    dec = B.build(scene)
    doc = apply_test_schema_extensions(dec, lm.to_document(dec))
    return RC.candidates(doc, kernel.realise(doc), "MS")["candidates"]


def test_candidates_are_deterministic_and_never_designations():
    a, b = cands(), cands()
    assert [c.candidate_id for c in a] == [c.candidate_id for c in b] and len(a) == 3
    assert all(c.review_status == FR.CANDIDATE and c.producer == FR.ENGINE for c in a)
    roles = sorted(c.role_candidate for c in a)
    assert roles == [RC.DETAIL, RC.PLAN, RC.UNKNOWN]


def test_candidate_regions_get_no_plan_authority_without_designation():
    u = verified_unit()
    by = {c.role_candidate: c for c in cands()}
    p = RC.region_for(u, by[RC.PLAN])
    assert p.region_kind == FR.MODEL_SPACE_PLAN and p.status == FR.UNCONFIRMED and FR.FINAL_MEASUREMENT not in p.allowed_use
    d = RC.region_for(u, by[RC.DETAIL])
    assert d.region_kind == FR.MODEL_SPACE_DETAIL and d.status == FR.BLOCKED
    x = RC.region_for(u, by[RC.UNKNOWN])
    assert x.region_kind == FR.MODEL_SPACE_UNKNOWN and x.status == FR.BLOCKED
    assert not {FR.FINAL_MEASUREMENT, FR.PREVIEW_MEASUREMENT} & set(x.allowed_use)
    cand = by[RC.PLAN]
    accepted = FR.ReferenceRegionDesignation("DES:1", SHA, "MS", cand.candidate_id, FR.PROJECT_ADAPTER_CLAIM,
                                             "adapter window reviewed", FR.ENGINE, FR.ACCEPTED)
    assert RC.region_for(u, cand, accepted).status == FR.VERIFIED


def test_mixed_role_labels_stay_unknown():
    scene = {"entities": _box(0, 0, 20000, 15000) + [{"kind": "TEXT", "at": (1000, 1000), "text": "PLAN"},
                                                    {"kind": "TEXT", "at": (2000, 1000), "text": "SECTION A-A"}]}
    (c,) = cands(scene)
    assert c.role_candidate == RC.UNKNOWN and "several role classes" in c.notes
