"""R8.3 — UNIT_CONTEXT, unit-evidence independence, REGION_MEASUREMENT_TRANSFORM, MEASUREMENT_FRAME.

Cases follow the brief: region/frame 1-12 (§36), unit A-L (§37). All synthetic; no project value.
"""

from __future__ import annotations

import dataclasses

import pytest

from engine.source import findings as F
from engine.source import frame as FR

SHA = "a" * 64
SPACE = "MS"


def ev(eid, kind, value, lineage, question=FR.NATIVE_UNIT, scope=SPACE, **kw):
    return FR.UnitEvidence(eid, question, kind, scope, tuple(lineage), value, source_sha256=kw.pop("sha", SHA), **kw)


def decl(code=4):
    return list(FR.declaration_evidence(code, SPACE, SHA)[0])


def plot_dim(v=1.0, eid="E_PLOT"):
    return ev(eid, FR.KNOWN_PLOT_DIMENSION, v, ["AUTHORED:PLOT_CERTIFICATE:1"], producer=FR.HUMAN)


def unit_note(v=1.0, eid="E_NOTE"):
    return ev(eid, FR.EXPLICIT_UNIT_NOTE, v, [f"AUTHORED:{SHA}:TEXT:77"])


def uc(evidence, insunits=4, **kw):
    # R8.3 semantics are pinned to URBAN_FRAME_RELEASE_V1 so the round stays reproducible for audit;
    # V2 (R8.4 default) is tested in tests/r8_4/test_r8_4_human_confirmation.py
    kw.setdefault("policy", FR.RELEASE_V1)
    return FR.unit_context(SHA, SPACE, FR.MODEL_SPACE, evidence, insunits=insunits, **kw)


def human(v, sha=SHA, eid="E_HUMAN"):
    return ev(eid, FR.HUMAN_CONFIRMATION, v, ["HUMAN:mohammad"], producer=FR.HUMAN, author="mohammad",
              timestamp="2026-10-01T09:00:00Z", sha=sha)


def verified_unit():
    return uc(decl(4) + [plot_dim(), unit_note()])


# ---------------------------------------------------------------- frozen thresholds (§19)

def test_frozen_thresholds_are_the_r8_values():
    assert FR.AGREEMENT_REL == 0.005 and FR.CHECKED_DIM_ABS_MM == 2.0 and FR.CHECKED_DIM_REL == 0.002
    assert "R8 revised spec v1" in FR.THRESHOLD_SOURCE


def test_agreement_boundary():
    assert uc(decl(4) + [plot_dim(1.0049), unit_note(1.0)]).status == FR.VERIFIED
    assert uc(decl(4) + [plot_dim(1.0060), unit_note(1.0)]).status == FR.CONFLICT


# ---------------------------------------------------------------- unit cases A-L (§37)

def test_A_insunits_alone_is_not_verified():
    u = uc(decl(4))
    assert u.status == FR.UNCONFIRMED and FR.FINAL_MEASUREMENT not in u.allowed_use
    assert u.declared_native_to_mm == 1.0 and u.machine_support == "DECLARATION_ONLY"


def test_B_matching_independent_authored_evidence_verifies():
    u = verified_unit()
    assert u.status == FR.VERIFIED and u.native_to_mm == 1.0 and FR.FINAL_MEASUREMENT in u.allowed_use


def test_B2_one_independent_class_is_provisional():
    assert uc(decl(4) + [plot_dim()]).status == FR.PROVISIONAL


def test_C_insunits_contradicted_by_independent_evidence_is_conflict():
    u = uc(decl(1) + [plot_dim(1.0)])                      # inch declared, one class says mm
    assert u.status == FR.CONFLICT and u.native_to_mm is None
    assert F.UNIT_DECLARATION_CONFLICT in {f.code for f in u.findings}


def test_C2_two_agreeing_classes_contradicting_the_declaration_are_provisional_not_verified():
    """Frozen spec: '>= 2 agreeing kinds that contradict a declaration' -> PROVISIONAL."""
    u = uc(decl(1) + [plot_dim(1000.0), unit_note(1000.0)])
    assert u.status == FR.PROVISIONAL and u.native_to_mm == 1000.0
    assert F.UNIT_DECLARATION_CONTRADICTED in {f.code for f in u.findings}


def test_D_same_declaration_through_two_parsers_is_one_lineage():
    d1 = FR.declaration_evidence(6, SPACE, SHA, parser="LIBREDWG")[0][0]
    d2 = FR.declaration_evidence(6, SPACE, SHA, parser="EZDXF")[0][0]
    assert len(FR.independence_classes([d1, d2], FR.NATIVE_UNIT)) == 1
    # a declaration is never physical evidence however many parsers read it
    assert uc([d1, d2], insunits=6).status == FR.UNCONFIRMED


def test_E_same_ocr_model_run_twice_is_not_independent():
    a = ev("OCR1", FR.DIMENSION_DISPLAY, 1.0, ["TRANSCRIPTION:ocr-model-x@cfg1", "DOCUMENT:pdf1"])
    b = ev("OCR2", FR.EXPLICIT_UNIT_NOTE, 1.0, ["TRANSCRIPTION:ocr-model-x@cfg1", "DOCUMENT:pdf1"])
    assert len(FR.independence_classes([a, b], FR.NATIVE_UNIT)) == 1
    assert uc(decl(4) + [a, b]).status == FR.PROVISIONAL        # one class, not two


def test_F_plausibility_only_cannot_verify():
    p1 = ev("P1", FR.GEOMETRY_PLAUSIBILITY, 1000.0, ["PLAUSIBILITY:villa-width"])
    p2 = ev("P2", FR.GEOMETRY_PLAUSIBILITY, 1000.0, ["PLAUSIBILITY:door-width"])
    u = uc([p1, p2], insunits=0)
    assert u.status == FR.BLOCKED and ("P1", "PLAUSIBILITY_SUPPORT_ONLY") in u.excluded_evidence


def test_G_human_confirmation_is_confirmed_by_human_never_verified():
    u = uc(decl(4) + [plot_dim(), human(1.0)])
    assert u.status == FR.CONFIRMED_BY_HUMAN and u.machine_status == FR.PROVISIONAL
    assert u.confirmation["author"] == "mohammad"
    assert FR.FINAL_MEASUREMENT in u.allowed_use                 # policy: human over agreeing physical evidence


def test_G2_human_agreeing_with_the_declaration_is_final_eligible_but_still_not_verified():
    u = uc(decl(4) + [human(1.0)])
    assert u.status == FR.CONFIRMED_BY_HUMAN and u.machine_status == FR.UNCONFIRMED
    assert FR.FINAL_MEASUREMENT in u.allowed_use


def test_G2b_human_confirmation_in_a_vacuum_is_never_final():
    u = uc([human(1.0)], insunits=0)
    assert u.status == FR.CONFIRMED_BY_HUMAN and FR.FINAL_MEASUREMENT not in u.allowed_use
    closed = FR.ReleasePolicy(policy_id=FR.RELEASE_V1_ID, human_confirmed_final=False, require_role_and_scope=False)
    assert FR.FINAL_MEASUREMENT not in uc(decl(4) + [human(1.0)], policy=closed).allowed_use


def test_G3_human_may_resolve_a_declaration_conflict_the_evidence_points_away_from():
    u = uc(decl(1) + [plot_dim(1000.0), human(1000.0)])
    assert u.machine_status == FR.CONFLICT and u.status == FR.CONFIRMED_BY_HUMAN and u.native_to_mm == 1000.0
    assert FR.FINAL_MEASUREMENT in u.allowed_use


def test_G3b_human_never_overrides_admitted_physical_evidence():
    assert uc(decl(4) + [plot_dim(1.0), human(1000.0)]).status == FR.CONFLICT
    assert uc(decl(4) + [plot_dim(1.0), unit_note(10.0), human(1.0)]).status == FR.CONFLICT   # physical conflict stays


def test_G3c_human_contradicting_a_candidate_constraint_is_not_final():
    c = FR.UnitEvidence("CS", FR.NATIVE_UNIT, FR.DIMENSION_STYLE, SPACE, ("AUTHORED:DS", "ASSUMPTION:X"), None,
                        derived_set=(100.0, 1000.0), source_sha256=SHA, review_status=FR.CANDIDATE)
    u = uc(decl(1) + [c, human(25.4)], insunits=1)
    assert u.status == FR.CONFIRMED_BY_HUMAN and FR.FINAL_MEASUREMENT not in u.allowed_use


def test_G4_human_contradicting_verified_evidence_is_conflict():
    assert uc(decl(4) + [plot_dim(), unit_note(), human(1000.0)]).status == FR.CONFLICT


def test_H_agent_cannot_admit_evidence_or_set_status():
    a = ev("AG1", FR.EXPLICIT_UNIT_NOTE, 1.0, ["TRANSCRIPTION:agent"], producer=FR.AGENT)   # claims ADMITTED
    b = ev("AG2", FR.KNOWN_PLOT_DIMENSION, 1.0, ["TRANSCRIPTION:agent2"], producer=FR.AGENT)
    u = uc(decl(4) + [a, b])
    assert u.status == FR.UNCONFIRMED
    assert ("AG1", "AGENT_CANNOT_ADMIT_EVIDENCE") in u.excluded_evidence
    assert F.AGENT_STATUS_ESCALATION_REJECTED in {f.code for f in u.findings}
    reg = FR.FrameRegistry(SHA)
    reg.add_unit_context(u)
    with pytest.raises(FR.FrameStatusError, match="AGENT"):
        reg.set_status(u.unit_context_id, FR.VERIFIED, FR.AGENT)
    with pytest.raises(FR.FrameStatusError):
        reg.set_status(u.unit_context_id, FR.CONFIRMED_BY_HUMAN, FR.HUMAN)
    with pytest.raises(dataclasses.FrozenInstanceError):
        u.status = FR.VERIFIED                                       # noqa  (records are immutable)


def test_H2_agent_candidate_can_lower_but_never_raise():
    cand = ev("AGC", FR.EXPLICIT_UNIT_NOTE, 1000.0, ["TRANSCRIPTION:agent"], producer=FR.AGENT,
              review_status=FR.CANDIDATE)
    assert uc(decl(4) + [cand]).status == FR.CONFLICT               # reveals a contradiction
    agree = ev("AGC2", FR.EXPLICIT_UNIT_NOTE, 1.0, ["TRANSCRIPTION:agent"], producer=FR.AGENT,
               review_status=FR.CANDIDATE)
    assert uc(decl(4) + [agree]).status == FR.UNCONFIRMED           # agreement adds nothing


def test_I_insunits_zero_infers_no_default():
    e, finding = FR.declaration_evidence(0, SPACE, SHA)
    assert e == () and finding.code == F.UNIT_DECLARATION_UNITLESS
    u = uc([], insunits=0)
    assert u.status == FR.BLOCKED and u.native_to_mm is None and u.declared_native_to_mm is None


def test_J_declaration_changes_but_physical_evidence_does_not():
    phys = [plot_dim(1.0), unit_note(1.0)]
    assert uc(decl(4) + phys).status == FR.VERIFIED
    assert uc(decl(5) + phys, insunits=5).status == FR.PROVISIONAL   # overruled declaration: never VERIFIED
    assert uc(decl(5) + [plot_dim(1.0)], insunits=5).status == FR.CONFLICT


def test_K_human_confirmation_for_another_source_hash_is_inadmissible():
    u = uc(decl(4) + [plot_dim(), human(1.0, sha="b" * 64)])
    assert u.status == FR.PROVISIONAL
    assert ("E_HUMAN", "HUMAN_CONFIRMATION_SOURCE_MISMATCH") in u.excluded_evidence
    assert F.HUMAN_CONFIRMATION_SOURCE_MISMATCH in {f.code for f in u.findings}


def test_L_two_dimension_checks_from_one_dimension_style_are_one_class():
    style = f"AUTHORED:{SHA}:DIMSTYLE:39"
    d1 = ev("DIM1", FR.DIMENSION_DISPLAY, 1.0, [style, f"AUTHORED:{SHA}:DIMENSION:101"])
    d2 = ev("DIM2", FR.DIMENSION_STYLE, 1.0, [style])
    assert len(FR.independence_classes([d1, d2], FR.NATIVE_UNIT)) == 1
    assert uc(decl(4) + [d1, d2]).status == FR.PROVISIONAL


def test_assumption_bearing_evidence_is_candidate_only():
    """A dimension display turns into a unit only under a display-unit assumption."""
    d = ev("DIMX", FR.DIMENSION_DISPLAY, 1000.0, [f"AUTHORED:{SHA}:DIMSTYLE:39", "ASSUMPTION:DISPLAY_UNIT_CM"])
    u = uc(decl(1) + [d], insunits=1)
    assert ("DIMX", "ASSUMPTION_UNRESOLVED") in u.excluded_evidence and u.status == FR.CONFLICT


def test_checked_dimension_residual_failure_blocks():
    good = FR.CheckedDimension("D1", 1000.0, 1000.5)                # 0.5 mm at 1 mm/unit
    bad = FR.CheckedDimension("D2", 1000.0, 1010.0)                 # 10 mm > max(2, 2)
    assert uc(decl(4) + [plot_dim(), unit_note()], checked_dimensions=(good,)).status == FR.VERIFIED
    u = uc(decl(4) + [plot_dim(), unit_note()], checked_dimensions=(good, bad))
    assert u.status == FR.BLOCKED and "D2" in u.status_reason


def test_one_lineage_disagreeing_with_itself_is_conflict():
    a = ev("S1", FR.DIMENSION_DISPLAY, 1.0, ["AUTHORED:SHEET_PLAN"])
    b = ev("S2", FR.DIMENSION_DISPLAY, 10.0, ["AUTHORED:SHEET_PLAN"])
    assert uc(decl(4) + [a, b]).status == FR.CONFLICT


def test_evidence_requires_lineage():
    with pytest.raises(ValueError):
        ev("X", FR.KNOWN_PLOT_DIMENSION, 1.0, [])


# ---------------------------------------------------------------- one UNIT_CONTEXT per space (U-1)

def test_u1_one_unit_context_per_coordinate_space():
    reg = FR.FrameRegistry(SHA)
    reg.add_unit_context(uc(decl(4)))
    with pytest.raises(ValueError, match="U-1"):
        reg.add_unit_context(FR.unit_context(SHA, SPACE, FR.MODEL_SPACE, decl(4), 4, unit_context_id="UC:other"))


def test_u1_a_detail_cannot_redefine_native_unit():
    e = ev("DETAIL_UNIT", FR.EXPLICIT_UNIT_NOTE, 10.0, ["AUTHORED:DETAIL"], scope="R_DETAIL")
    u = uc(decl(4) + [e])
    assert "DETAIL_UNIT" not in u.evidence_ids and u.status == FR.UNCONFIRMED
    assert F.UNIT_REDEFINITION_REJECTED in {f.code for f in u.findings}


def test_each_layout_has_its_own_context():
    reg = FR.FrameRegistry(SHA)
    reg.add_unit_context(uc(decl(4)))
    lay = FR.unit_context(SHA, "LAYOUT1", FR.PAPER_LAYOUT, [], insunits=None)
    reg.add_unit_context(lay)
    assert len(reg.units) == 2


# ---------------------------------------------------------------- region / frame cases 1-12 (§36)

def rev(eid, value, region, lineage, kind=FR.EXPLICIT_SCALE_NOTE):
    return FR.UnitEvidence(eid, FR.REGION_SCALE, kind, region, tuple(lineage), value, source_sha256=SHA)


def test_1_normal_model_space_plan():
    u = verified_unit()
    r = FR.region_transform(u, "PLAN", FR.MODEL_SPACE_PLAN, reference=True)
    f = FR.measurement_frame(u, r)
    assert r.status == FR.VERIFIED and r.local_scale == 1.0 and f.status == FR.VERIFIED
    assert FR.FINAL_MEASUREMENT in f.allowed_use and f.mm_per_native == 1.0


def test_2_two_model_space_regions_share_one_unit_context():
    u = verified_unit()
    reg = FR.FrameRegistry(SHA)
    reg.add_unit_context(u)
    f1 = reg.add_region(FR.region_transform(u, "GF", FR.MODEL_SPACE_PLAN, reference=True))
    f2 = reg.add_region(FR.region_transform(u, "FF", FR.MODEL_SPACE_PLAN))
    assert f1.unit_context_id == f2.unit_context_id and len(reg.units) == 1
    assert f2.status == FR.UNCONFIRMED                               # a non-reference plan must earn its scale


def test_3_enlarged_detail_with_explicit_scale_note():
    u = verified_unit()
    r = FR.region_transform(u, "DET", FR.MODEL_SPACE_DETAIL,
                            [rev("N1", 0.2, "DET", [f"AUTHORED:{SHA}:TEXT:DETAIL_1_20"])])
    assert r.status == FR.PROVISIONAL and r.local_scale == 0.2
    assert FR.FINAL_MEASUREMENT not in FR.measurement_frame(u, r).allowed_use


def test_4_enlarged_detail_with_no_evidence_is_blocked():
    u = verified_unit()
    r = FR.region_transform(u, "DET", FR.MODEL_SPACE_DETAIL)
    assert r.status == FR.BLOCKED and r.local_scale is None
    assert FR.measurement_frame(u, r).allowed_use == (FR.COUNT_ONLY,)


def test_5_paper_space_viewport_is_never_measurement_authority():
    u = FR.unit_context(SHA, "LAYOUT1", FR.PAPER_LAYOUT, [], insunits=None)
    r = FR.region_transform(u, "VP1", FR.PAPER_SPACE_VIEWPORT,
                            [rev("V1", 0.01, "VP1", [f"AUTHORED:{SHA}:VIEWPORT:9"], FR.PAPERSPACE_VIEWPORT_SCALE),
                             rev("V2", 0.01, "VP1", [f"AUTHORED:{SHA}:TEXT:SCALE"]),
                             rev("V3", 0.01, "VP1", [f"AUTHORED:{SHA}:SCALEBAR:1"], FR.SCALE_BAR)])
    assert FR.FINAL_MEASUREMENT not in r.allowed_use and FR.PREVIEW_MEASUREMENT not in r.allowed_use
    assert set(r.allowed_use) <= {FR.ANNOTATION_MAPPING, FR.COUNT_ONLY}


def test_6_rotated_region_keeps_its_scale():
    import math
    u = verified_unit()
    c, s = math.cos(0.7), math.sin(0.7)
    r = FR.region_transform(u, "ROT", FR.MODEL_SPACE_PLAN, matrix=(c, -s, 0, s, c, 0), reference=True)
    assert abs(r.rotation_rad - 0.7) < 1e-12 and not r.reflection and r.status == FR.VERIFIED


def test_7_reflected_region_is_recorded():
    u = verified_unit()
    r = FR.region_transform(u, "MIR", FR.MODEL_SPACE_PLAN, matrix=(-1, 0, 0, 0, 1, 0), reference=True)
    assert r.reflection and r.status == FR.VERIFIED


def test_8_region_scale_evidence_conflicting_with_the_plan_convention():
    u = verified_unit()
    r = FR.region_transform(u, "PLAN2", FR.MODEL_SPACE_PLAN,
                            [rev("N2", 0.01, "PLAN2", [f"AUTHORED:{SHA}:TEXT:1_100"])])
    assert r.status == FR.CONFLICT and FR.measurement_frame(u, r).status == FR.CONFLICT


def test_9_verified_unit_provisional_region():
    u = verified_unit()
    r = FR.region_transform(u, "DET", FR.MODEL_SPACE_DETAIL, [rev("N1", 0.2, "DET", ["AUTHORED:N1"])])
    f = FR.measurement_frame(u, r)
    assert (u.status, r.status, f.status) == (FR.VERIFIED, FR.PROVISIONAL, FR.PROVISIONAL)


def test_10_provisional_unit_verified_region():
    u = uc(decl(4) + [plot_dim()])
    r = FR.region_transform(u, "PLAN", FR.MODEL_SPACE_PLAN, reference=True)
    f = FR.measurement_frame(u, r)
    assert (u.status, r.status, f.status) == (FR.PROVISIONAL, FR.VERIFIED, FR.PROVISIONAL)
    assert FR.FINAL_MEASUREMENT not in f.allowed_use


def test_11_conflicting_unit_valid_region():
    u = uc(decl(1) + [plot_dim(1.0)])
    f = FR.measurement_frame(u, FR.region_transform(u, "PLAN", FR.MODEL_SPACE_PLAN, reference=True))
    assert f.status == FR.CONFLICT and f.allowed_use == (FR.COUNT_ONLY,)
    assert F.FRAME_CONFLICT in {x.code for x in f.findings}


def test_12_human_confirmed_unit_verified_region_stays_distinguishable():
    u = uc(decl(4) + [plot_dim(), human(1.0)])
    f = FR.measurement_frame(u, FR.region_transform(u, "PLAN", FR.MODEL_SPACE_PLAN, reference=True))
    assert f.status == FR.CONFIRMED_BY_HUMAN and f.unit_status == FR.CONFIRMED_BY_HUMAN
    assert f.status != FR.VERIFIED


@pytest.mark.parametrize("us", FR.STATUSES)
@pytest.mark.parametrize("rs", FR.STATUSES)
def test_frame_is_never_stronger_than_its_weakest_component(us, rs):
    c = FR.compose_status(us, rs)
    assert FR.STRENGTH[c] == min(FR.STRENGTH[us], FR.STRENGTH[rs])


def test_future_pdf_and_raster_regions_never_final():
    u = verified_unit()
    for kind in (FR.PDF_VECTOR_REGION, FR.RASTER_REGION):
        r = FR.region_transform(u, kind, kind, [rev("a", 1.0, kind, ["AUTHORED:A"]),
                                                rev("b", 1.0, kind, ["AUTHORED:B"], FR.SCALE_BAR)])
        assert r.status == FR.VERIFIED and FR.FINAL_MEASUREMENT not in r.allowed_use
        assert F.REGION_PROFILE_NOT_APPROVED in {f.code for f in r.findings}


def test_only_a_plan_can_be_the_reference_region():
    with pytest.raises(ValueError):
        FR.region_transform(verified_unit(), "D", FR.MODEL_SPACE_DETAIL, reference=True)


def test_every_frame_finding_declares_the_measurement_frame_domain():
    """FRAME_UNREADABLE (R8.0) is an INSERT transform frame, not a measurement frame: excluded."""
    codes = [c for c in F.IMPACTS if c.startswith(("UNIT_", "REGION_", "FRAME_", "CHECKED_DIMENSION",
                                                  "HUMAN_CONFIRMATION", "AGENT_STATUS"))
             and c != F.FRAME_UNREADABLE]
    assert len(codes) == 20        # R8.3: 17; R8.4 adds HUMAN_CONFIRMATION_CONFLICT / _REVIEW_REQUIRED / _REJECTED
    assert all(F.IMPACTS[c][0][0] == F.MEASUREMENT_FRAME for c in codes)


# ---------------------------------------------------------------- constraint-set evidence

def constraint(eid, values, lineage=("AUTHORED:DIMSTYLE:1", "ASSUMPTION:DISPLAY_IN_STANDARD_UNIT")):
    return FR.UnitEvidence(eid, FR.NATIVE_UNIT, FR.DIMENSION_STYLE, SPACE, lineage, None, derived_set=tuple(values),
                           source_sha256=SHA, review_status=FR.CANDIDATE)


def test_a_constraint_set_can_contradict_a_declaration_but_never_confirm_it():
    consistent = constraint("C1", (0.1, 1.0, 100.0, 2.54, 30.48))
    assert uc(decl(4) + [consistent]).status == FR.UNCONFIRMED           # contains 1 mm: adds nothing
    inconsistent = constraint("C2", (100.0, 1000.0, 1e5, 2540.0, 30480.0))
    u = uc(decl(1) + [inconsistent], insunits=1)                          # inch not in the set
    assert u.status == FR.CONFLICT and u.contesting_candidates == ("C2",)
    assert ("C2", "CANDIDATE") in u.excluded_evidence


# ---------------------------------------------------------------- set-valued evidence fails closed (review §3-§4)

def admitted_set(eid, values, lineage):
    return FR.UnitEvidence(eid, FR.NATIVE_UNIT, FR.DIMENSION_STYLE, SPACE, (lineage,), None,
                           derived_set=tuple(values), source_sha256=SHA)


def test_declaration_inside_an_implied_set_is_not_support():
    """geometry 100, DIMLFAC 0.1, display 10: the display unit is not authored, so the set
    {0.1, 1, 100, 2.54, 30.48} mm/unit contains the declared 1 mm - and that proves nothing."""
    s = admitted_set("S", (0.1, 1.0, 100.0, 2.54, 30.48), "AUTHORED:DIMSTYLE:1")
    u = uc(decl(4) + [s])
    assert u.status == FR.UNCONFIRMED and u.machine_support == "DECLARATION_ONLY"
    assert u.status_reason == "DECLARATION_ONLY_COMPATIBLE_WITH_UNRESOLVED_SET"
    assert FR.FINAL_MEASUREMENT not in u.allowed_use
    # a second DIFFERENT-kind point class plus the set still never counts the set as a class
    assert uc(decl(4) + [s, plot_dim(1.0)]).status == FR.PROVISIONAL


def test_sets_intersect_deterministically_to_one_interpretation():
    e1 = admitted_set("E1", (1.0, 10.0, 1000.0), "AUTHORED:A")
    e2 = admitted_set("E2", (10.0, 1000.0), "AUTHORED:B")
    e3 = admitted_set("E3", (10.0,), "AUTHORED:C")
    u = uc(decl(5) + [e1, e2, e3], insunits=5)
    assert u.native_to_mm == 10.0 and u.status == FR.PROVISIONAL        # joint conclusion = one class


def test_empty_intersection_is_conflict():
    u = uc(decl(4) + [admitted_set("E1", (1.0, 10.0), "AUTHORED:A"), admitted_set("E2", (1000.0,), "AUTHORED:B")])
    assert u.status == FR.CONFLICT and u.status_reason == "SET_INTERSECTION_EMPTY"


def test_multi_member_intersection_is_unresolved_without_a_declaration():
    u = uc([admitted_set("E1", (1.0, 10.0, 1000.0), "AUTHORED:A"), admitted_set("E2", (10.0, 1000.0), "AUTHORED:B")],
           insunits=0)
    assert u.status == FR.UNCONFIRMED and u.native_to_mm is None
    assert u.status_reason == "UNRESOLVED_SET_OF_2_INTERPRETATIONS"


def test_declaration_outside_the_set_intersection_conflicts():
    u = uc(decl(1) + [admitted_set("E1", (100.0, 1000.0), "AUTHORED:A")], insunits=1)
    assert u.status == FR.CONFLICT and u.status_reason == "DECLARATION_OUTSIDE_SET_INTERSECTION"


def test_point_value_outside_the_set_intersection_conflicts():
    u = uc(decl(4) + [admitted_set("E1", (10.0, 1000.0), "AUTHORED:A"), plot_dim(1.0)])
    assert u.status == FR.CONFLICT


def test_threshold_provenance_record_matches_the_code():
    import json
    from pathlib import Path
    rec = json.loads((Path(__file__).parent / "registers/R8_3_THRESHOLD_PROVENANCE.json").read_text())
    assert rec["source_status"] == "EXTERNAL_FROZEN_SPEC_NOT_PREVIOUSLY_COMMITTED"
    c = rec["code_constants"]["engine/source/frame.py"]
    assert (c["AGREEMENT_REL"], c["CHECKED_DIM_ABS_MM"], c["CHECKED_DIM_REL"]) == (
        FR.AGREEMENT_REL, FR.CHECKED_DIM_ABS_MM, FR.CHECKED_DIM_REL)
    assert any("0.5 %" in ln and "max(2 mm, 0.2 %)" in ln for ln in rec["verbatim_excerpt"])
    assert "EXTERNAL_FROZEN_SPEC_NOT_PREVIOUSLY_COMMITTED" in FR.THRESHOLD_SOURCE
