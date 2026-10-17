"""Generic tests: the graphic evidence policy (engine.source.graphic_evidence) and the delta release record
(engine.source.delta_release). Synthetic only; no project data."""

import json
import shutil

import pytest

from engine.source import delta_release as DR
from engine.source import graphic_evidence as GE

ALL_TRUE = {c: True for c in GE.DERIVATION_CONDITIONS}


# ------------------------------------------------------------------ graphic classes
def test_four_graphic_classes_and_their_quantity_rule():
    assert GE.CLASSES == ("GRAPHIC_EXPLICIT_DIMENSIONED", "GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY",
                          "GRAPHIC_EXPLICIT_SHAPE_ONLY", "GRAPHIC_NTS_OR_UNDIMENSIONED")
    assert GE.may_quantify(GE.GRAPHIC_EXPLICIT_DIMENSIONED)[0] is True
    assert GE.may_quantify(GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY, ALL_TRUE)[0] is True
    assert GE.may_quantify(GE.GRAPHIC_EXPLICIT_SHAPE_ONLY, ALL_TRUE)[0] is False
    assert GE.may_quantify(GE.GRAPHIC_NTS_OR_UNDIMENSIONED, ALL_TRUE)[0] is False
    assert GE.may_quantify(GE.NO_GRAPHIC_EVIDENCE)[0] is False
    with pytest.raises(GE.GraphicPolicyError):
        GE.may_quantify("GRAPHIC_LOOKS_RIGHT")


@pytest.mark.parametrize("missing", GE.DERIVATION_CONDITIONS)
def test_rule_b_needs_every_condition(missing):
    cond = dict(ALL_TRUE, **{missing: False})
    ok, why = GE.may_quantify(GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY, cond)
    assert not ok and missing in why
    del cond[missing]                                       # a missing condition counts as not holding
    assert not GE.may_quantify(GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY, cond)[0]
    with pytest.raises(GE.GraphicPolicyError):
        GE.admit_length(GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY, 250.0, basis=GE.PROJECT_SOURCE_GEOMETRY,
                        conditions=cond)


@pytest.mark.parametrize("cls", GE.CLASSES)
def test_nts_or_plotted_scale_never_creates_a_measured_length(cls):
    for nts in (True, False):
        with pytest.raises(GE.GraphicPolicyError):
            GE.admit_length(cls, 312.0, basis=GE.PLOTTED_SCALE, conditions=ALL_TRUE, nts=nts)
    with pytest.raises(GE.GraphicPolicyError):
        GE.portion("LEG", cls, shape_found=True, length_mm=312.0, basis=GE.PLOTTED_SCALE, conditions=ALL_TRUE)


def test_only_dimensioned_or_fully_derived_portions_carry_length():
    assert GE.admit_length(GE.GRAPHIC_EXPLICIT_DIMENSIONED, 400.0, basis=GE.PRINTED_DIMENSION) == 400.0
    assert GE.admit_length(GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY, 260.0, basis=GE.PROJECT_SOURCE_GEOMETRY,
                           conditions=ALL_TRUE) == 260.0
    with pytest.raises(GE.GraphicPolicyError):                # a derivation is not a printed dimension
        GE.admit_length(GE.GRAPHIC_EXPLICIT_DIMENSIONED, 400.0, basis=GE.PROJECT_SOURCE_GEOMETRY)
    with pytest.raises(GE.GraphicPolicyError):
        GE.admit_length(GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY, 260.0, basis=GE.PRINTED_DIMENSION,
                        conditions=ALL_TRUE)
    for cls in (GE.GRAPHIC_EXPLICIT_SHAPE_ONLY, GE.GRAPHIC_NTS_OR_UNDIMENSIONED, GE.NO_GRAPHIC_EVIDENCE):
        for basis in (GE.PRINTED_DIMENSION, GE.PROJECT_SOURCE_GEOMETRY):
            with pytest.raises(GE.GraphicPolicyError):
                GE.admit_length(cls, 100.0, basis=basis, conditions=ALL_TRUE)


def test_shape_found_length_blocked():
    p = GE.portion("END_HOOK_1", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY, shape_found=True)
    assert p["state"] == GE.SHAPE_FOUND_LENGTH_BLOCKED and p["length_mm"] is None and p["shape"] == "SOURCE_FOUND"
    q = GE.portion("END_TREATMENT_1", GE.NO_GRAPHIC_EVIDENCE, shape_found=False)
    assert q["state"] == GE.BLOCKED_UNQUANTIFIED and q["shape"] == "NOT_DRAWN"
    with pytest.raises(GE.GraphicPolicyError):                # shape-only cannot be given a length
        GE.portion("UPTURN_LEG_1", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY, shape_found=True, length_mm=200.0,
                   basis=GE.PROJECT_SOURCE_GEOMETRY, conditions=ALL_TRUE)
    k = GE.portion("STRAIGHT_RUN", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY, shape_found=True, length_mm=860.0,
                   known_segment=True)
    assert k["state"] == GE.KNOWN_STRAIGHT_SEGMENT and k["length_basis"] == "FROZEN_SOURCE_QUANTITY"
    d = GE.portion("CORE", GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY, shape_found=True, length_mm=1040.0,
                   basis=GE.PROJECT_SOURCE_GEOMETRY, conditions=ALL_TRUE)
    assert d["state"] == GE.DERIVED_LOWER_BOUND


def test_policy_record_names_the_scale_rule():
    r = GE.policy_record()
    assert r["length_bases_refused"] == [GE.PLOTTED_SCALE] and set(r["rules"]) == {"A", "B", "C", "D", "SCALE"}


# ------------------------------------------------------------------ delta records
def _rec(**kw):
    base = dict(delta_id="D1", change_kind=DR.NO_CHANGE, frozen_baseline="X (stamp)", baseline_component_id="O:C",
                old_state="LOWER_BOUND", old_known_quantity=10.0, new_project_source="", source_page="",
                source_handles="", graphic_evidence_class=GE.NO_GRAPHIC_EVIDENCE, new_component_model="",
                delta_known_quantity=0.0, new_blocked_components=[], new_release_state=DR.LOWER_BOUND)
    base.update(kw)
    return DR.record(**base)


def test_record_carries_all_brief_fields():
    r = _rec()
    assert set(DR.FIELDS) <= set(r) and r["NEW_KNOWN_QUANTITY"] == 10.0


def test_delta_never_subtracts_and_never_creates_verified():
    with pytest.raises(DR.DeltaReleaseError):
        _rec(delta_known_quantity=-1.0)
    with pytest.raises(DR.DeltaReleaseError):
        _rec(new_release_state=DR.VERIFIED)
    with pytest.raises(DR.DeltaReleaseError):                 # even a frozen VERIFIED cannot be re-asserted by a change
        _rec(old_state=DR.VERIFIED, new_release_state=DR.VERIFIED, change_kind=DR.FACET_ADDED)
    assert _rec(old_state=DR.VERIFIED, new_release_state=DR.VERIFIED)["NEW_RELEASE_STATE"] == DR.VERIFIED


def test_positive_delta_needs_an_allowed_basis():
    ok = _rec(change_kind=DR.QUANTITY_RELEASED, old_known_quantity=0, delta_known_quantity=4.2,
              quantity_basis=DR.BASIS_DERIVED, graphic_evidence_class=GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY,
              derivation_conditions=ALL_TRUE)
    assert ok["DELTA_KNOWN_QUANTITY"] == 4.2
    bad = [dict(quantity_basis=DR.BASIS_DERIVED, graphic_evidence_class=GE.GRAPHIC_EXPLICIT_SHAPE_ONLY,
                derivation_conditions=ALL_TRUE),
           dict(quantity_basis=DR.BASIS_DERIVED, graphic_evidence_class=GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY,
                derivation_conditions=dict(ALL_TRUE, ENDPOINTS_DETERMINISTIC=False)),
           dict(quantity_basis=DR.BASIS_PRINTED, graphic_evidence_class=GE.GRAPHIC_NTS_OR_UNDIMENSIONED),
           dict(quantity_basis=DR.BASIS_PLOTTED, graphic_evidence_class=GE.GRAPHIC_EXPLICIT_DIMENSIONED),
           dict(quantity_basis=DR.BASIS_NONE, graphic_evidence_class=GE.GRAPHIC_EXPLICIT_DIMENSIONED)]
    for b in bad:
        with pytest.raises(DR.DeltaReleaseError):
            _rec(change_kind=DR.QUANTITY_RELEASED, old_known_quantity=0, delta_known_quantity=4.2, **b)
    with pytest.raises(DR.DeltaReleaseError):                 # released steel is a lower bound
        _rec(change_kind=DR.QUANTITY_RELEASED, delta_known_quantity=1.0, quantity_basis=DR.BASIS_SCHEDULE,
             new_release_state=DR.BLOCKED_UNQUANTIFIED)
    with pytest.raises(DR.DeltaReleaseError):                 # new steel must be declared as a release
        _rec(change_kind=DR.FACET_ADDED, delta_known_quantity=1.0, quantity_basis=DR.BASIS_SCHEDULE)


def test_ownership_transfer_carries_no_quantity():
    t = _rec(change_kind=DR.OWNERSHIP_TRANSFER, old_known_quantity=0.0, old_state="BLOCKED_UNQUANTIFIED",
             new_release_state=DR.TRANSFERRED_OUT)
    assert t["NEW_RELEASE_STATE"] == DR.TRANSFERRED_OUT
    with pytest.raises(DR.DeltaReleaseError):
        _rec(change_kind=DR.OWNERSHIP_TRANSFER, old_known_quantity=3.0, new_release_state=DR.TRANSFERRED_OUT)
    with pytest.raises(DR.DeltaReleaseError):
        _rec(change_kind=DR.OWNERSHIP_TRANSFER, old_known_quantity=0.0, new_release_state=DR.LOWER_BOUND)


def test_delta_conservation():
    recs = [_rec(), _rec(delta_id="D2", old_known_quantity=0, change_kind=DR.QUANTITY_RELEASED,
                         delta_known_quantity=2.5, quantity_basis=DR.BASIS_SCHEDULE)]
    c = DR.conservation(10.0, recs, 12.5)
    assert c["all_pass"] and c["delta_known"] == 2.5
    assert not DR.conservation(10.0, recs, 10.0)["all_pass"]
    assert not DR.conservation(11.0, recs, 13.5)["checks"]["frozen_known_carried"]


def test_verify_frozen_detects_an_edited_baseline(tmp_path):
    pkg = tmp_path / "research" / "stage"
    pkg.mkdir(parents=True)
    (tmp_path / "engine.py").write_text("x = 1\n")
    (pkg / "OUT.csv").write_text("a,b\n1,2\n")
    m = {"round": "SX", "engine_commit_stamp": "abc+code:1",
         "code": {"engine.py": DR.sha256(tmp_path / "engine.py")}, "inputs": {},
         "outputs": {"OUT.csv": DR.sha256(pkg / "OUT.csv")}}
    (pkg / "MANIFEST.json").write_text(json.dumps(m))
    f = DR.verify_frozen(pkg / "MANIFEST.json", tmp_path)
    assert f["files_checked"] == 2 and f["engine_commit_stamp"] == "abc+code:1"
    shutil.copy(pkg / "OUT.csv", tmp_path / "keep.csv")
    (pkg / "OUT.csv").write_text("a,b\n1,3\n")
    with pytest.raises(DR.DeltaReleaseError):
        DR.verify_frozen(pkg / "MANIFEST.json", tmp_path)
