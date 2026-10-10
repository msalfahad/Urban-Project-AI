"""R8.4 §11-§13, §34 — capability-scoped DECODER_QUALIFICATION (tests A-I).

A build is qualified for the ENVELOPE an independent comparison exercised, never globally.
Handle risk is judged by representation (byte size vs value, collisions, reference resolution),
never by an object count."""

from __future__ import annotations

import pytest

from engine.source import cad_profile as P
from engine.source import decoder_pins as PINS
from engine.source import findings as F
from engine.source import qualification as Q
from engine.source.findings import SourceFinding
from tests.r8_0 import libredwg_builder as B
from tests.r8_0.k1_harness import _imports, apply_test_schema_extensions
from tests.r8_0.scenes import CURVES_BLOCK, _insert

BUILD = PINS.PINS["LIBREDWG_DWGREAD"][0]["sha256"]
OTHER_BUILD = "b" * 64
AREA = P.MeasurementMethod("FLOOR_AREA", scale_dependent=True)


def doc_of(scene):
    _, _, lm = _imports()
    dec = B.build(scene)
    return apply_test_schema_extensions(dec, lm.to_document(dec)), dec


PLAIN = {"entities": [{"kind": "LINE", "a": (0, 0), "b": (3000, 0)}, {"kind": "ARC", "c": (0, 0), "r": 500.0,
                                                                        "a0": 0.0, "a1": 90.0}]}
BLOCKY = {"blocks": {"CURVES": CURVES_BLOCK}, "entities": [_insert("CURVES", at=(10.0, 0.0), rot=30.0)]}
MIRRORED = {"blocks": {"CURVES": CURVES_BLOCK}, "entities": [_insert("CURVES", scale=(-1.0, 1.0))]}
NONUNI = {"blocks": {"CURVES": CURVES_BLOCK}, "entities": [_insert("CURVES", scale=(2.0, 1.0))]}


def profile(scene):
    d, dec = doc_of(scene)
    return Q.source_feature_profile(d, dec)


def envelope_for(p, **over):
    kw = dict(entity_kinds=p.entity_kinds, transform_classes=p.transform_classes, max_block_depth=p.max_block_depth,
              minsert=p.minsert, dynamic_blocks=p.dynamic_blocks, xref=p.xref, max_handle_bytes=p.handle.max_byte_size)
    kw.update(over)
    return Q.QualificationEnvelope(**kw)


def qual(env, build=BUILD, status=Q.QUALIFIED):
    extra = dict(reconciliation_verdict="PASS", reference_source_sha256=("c" * 64,),
                 independent_route="INDEPENDENT_DXF->EZDXF K2") if status == Q.QUALIFIED else {}
    return Q.DecoderQualification("Q-TEST", "LIBREDWG_DWGREAD_JSON", build, status, env, **extra)


def parser(p, quals, findings=(), build=BUILD):
    policy = P.ParserIndependencePolicy(policy_id=P.PARSER_POLICY_V2_ID, qualifications=tuple(quals))
    ctx = P.SourceValidationContext(True, PINS.REGISTERED, build, feature_profile=p)
    return P.parser_requirement(ctx, findings, AREA, policy)


def test_a_no_qualification_requires_an_independent_parser():
    p = profile(PLAIN)
    st, why = parser(p, [])
    assert st == "FAIL" and "no QUALIFIED envelope" in why
    # R8.5: default moved to URBAN_PARSER_INDEPENDENCE_V3 (capability signatures); V2 kept reproducible
    assert P.PARSER_POLICY_V2.policy_id == P.PARSER_POLICY_V2_ID and P.PARSER_POLICY_V2.qualifications == ()


def test_b_profile_inside_envelope_is_covered():
    p = profile(BLOCKY)
    assert Q.TRANSFORM_CLASSES and {Q.ROTATION, Q.TRANSLATION} <= p.transform_classes and p.max_block_depth == 1
    st, why = parser(p, [qual(envelope_for(p))])
    assert st == "PASS" and "inside envelope Q-TEST" in why


def test_c_entity_kind_outside_envelope_is_uncovered():
    p = profile(PLAIN)
    env = envelope_for(p, entity_kinds=frozenset({"LINE"}))
    got = Q.qualification_for(BUILD, p, [qual(env)])
    assert not got["covered"] and "ENTITY_KIND:ARC" in got["uncovered"]
    assert parser(p, [qual(env)])[0] == "FAIL"


@pytest.mark.parametrize("scene,cls", [(MIRRORED, Q.REFLECTION), (NONUNI, Q.NON_UNIFORM_SCALE)])
def test_d_transform_class_outside_envelope_is_uncovered(scene, cls):
    exercised = profile(BLOCKY)
    p = profile(scene)
    assert cls in p.transform_classes
    got = Q.qualification_for(BUILD, p, [qual(envelope_for(exercised))])
    assert f"TRANSFORM:{cls}" in got["uncovered"]


def test_e_depth_and_feature_flags_must_be_exercised():
    nested = {"blocks": {"CURVES": CURVES_BLOCK, "OUTER": {"entities": [_insert("CURVES")]}},
              "entities": [_insert("OUTER")]}
    p = profile(nested)
    assert p.max_block_depth == 2
    shallow = envelope_for(p, max_block_depth=1)
    assert "BLOCK_DEPTH:2>1" in Q.qualification_for(BUILD, p, [qual(shallow)])["uncovered"]
    flagged = Q.SourceFeatureProfile(p.entity_kinds, p.transform_classes, 0, True, True, True, p.handle)
    miss = Q.qualification_for(BUILD, flagged, [qual(envelope_for(p))])["uncovered"]
    assert {"FEATURE:MINSERT", "FEATURE:DYNAMIC_BLOCKS", "FEATURE:XREF"} <= set(miss)


def _decode(handles, refs=()):
    objs = [{"handle": list(h), "type": 19} for h in handles]
    if refs:
        objs[0]["layer"] = list(refs[0])
    return {"OBJECTS": objs}


def test_f_handle_risk_is_representation_not_object_count():
    # a SMALL decode with a 3-byte handle printed with a 16-bit value: inconsistent -> risk
    small = Q.handle_representation(_decode([(0, 1, 0x20), (0, 3, 0x2894)]))
    assert small.objects == 2 and small.size_value_inconsistent == 1
    # a LARGE decode whose handles are all consistently represented: no representation risk
    large = Q.handle_representation(_decode([(0, 2 if v > 0xFF else 1, v) for v in range(1, 70001) if v <= 0xFFFF]))
    assert large.objects > 65000 and large.size_value_inconsistent == 0 and large.value_collisions == 0
    # a genuinely 3-byte value is consistent
    ok = Q.handle_representation(_decode([(0, 3, 0x012894)]))
    assert ok.size_value_inconsistent == 0 and ok.max_byte_size == 3
    p = profile(PLAIN)
    risky = Q.SourceFeatureProfile(p.entity_kinds, p.transform_classes, 0, False, False, False, small)
    env = envelope_for(p, max_handle_bytes=3)
    assert "HANDLE_SIZE_VALUE_INCONSISTENT" in Q.qualification_for(BUILD, risky, [qual(env)])["uncovered"]
    env2 = envelope_for(p, max_handle_bytes=3, handle_size_value_inconsistency_exercised=True)
    assert Q.qualification_for(BUILD, risky, [qual(env2)])["covered"]
    wide = Q.SourceFeatureProfile(p.entity_kinds, p.transform_classes, 0, False, False, False, ok)
    assert "HANDLE_BYTES:3>2" in Q.qualification_for(BUILD, wide, [qual(envelope_for(p, max_handle_bytes=2))])["uncovered"]


def test_g_collisions_and_unresolved_references():
    col = Q.handle_representation(_decode([(0, 3, 0x2894), (0, 1, 0x2894 & 0xFF), (0, 2, 0x2894)]))
    assert col.value_collisions == 1
    unres = Q.handle_representation(_decode([(0, 1, 0x20), (0, 1, 0x21)], refs=[(5, 1, 0x99)]))
    assert unres.unresolved_absolute_refs == 1
    p = profile(PLAIN)
    bad = Q.SourceFeatureProfile(p.entity_kinds, p.transform_classes, 0, False, False, False, unres)
    everything = envelope_for(p, max_handle_bytes=8, handle_size_value_inconsistency_exercised=True,
                              handle_collisions_exercised=True)
    assert "HANDLE_UNRESOLVED_ABSOLUTE_REFERENCES" in Q.qualification_for(BUILD, bad, [qual(everything)])["uncovered"]


def test_h_only_an_executed_pass_comparison_qualifies():
    p = profile(PLAIN)
    with pytest.raises(ValueError):
        Q.DecoderQualification("Q-X", "LIBREDWG", BUILD, Q.QUALIFIED, envelope_for(p))   # no route / PASS
    with pytest.raises(ValueError):
        Q.DecoderQualification("Q-X", "LIBREDWG", BUILD, Q.QUALIFIED, envelope_for(p), ("c" * 64,),
                               "INDEPENDENT", "BLOCK")
    for st in (Q.NOT_EXECUTED, Q.BLOCKED_EXTERNAL_INPUT, Q.FAILED):
        got = Q.qualification_for(BUILD, p, [qual(envelope_for(p), status=st)])
        assert not got["covered"] and st in got["reason"]


def test_i_scope_build_risk_and_v1_reproducible():
    p = profile(PLAIN)
    q = qual(envelope_for(p))
    assert parser(p, [q], build=OTHER_BUILD)[0] == "FAIL"                 # other build: not covered
    assert Q.qualification_for(BUILD, None, [q])["uncovered"] == ("FEATURE_PROFILE_ABSENT",)
    risk = [SourceFinding(F.HANDLE_VALUE_TRUNCATED)]
    st, why = parser(p, [q], findings=risk)                                # covered, but a risk finding in scope
    assert st == "FAIL" and "HANDLE_VALUE_TRUNCATED" in why
    v1 = P.ParserIndependencePolicy(qualified_builds=frozenset({BUILD}))  # R8.3 semantics: global, reproducible
    ctx = P.SourceValidationContext(True, PINS.REGISTERED, BUILD)
    assert P.parser_requirement(ctx, (), AREA, v1)[0] == "PASS"
    assert P.parser_requirement(ctx, (), AREA, P.PARSER_POLICY_V2)[0] == "FAIL"


def test_cad_profile_versions_are_explicit():
    assert P.CAD_PROFILE_V2.profile_id == "URBAN_CAD_PROFILE_V2"      # R8.5: default is V3
    assert P.CAD_PROFILE_V1.parser_policy.policy_id == P.PARSER_POLICY_V1_ID
    assert P.CAD_PROFILE_V2.frame_policy.policy_id == "URBAN_FRAME_RELEASE_V2"
