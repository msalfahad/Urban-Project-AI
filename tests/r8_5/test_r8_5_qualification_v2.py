"""R8.5 §2-§6, §23-§25 — decoder qualification V2: capability SIGNATURES (interactions), not flat features.

Every qualification here is built from signatures actually present in a (synthetic) qualification scene
with an all-PASS verdict map, then asked to cover a DIFFERENT target scene. Tests A-G are the brief's
negative cases; the V1 flat envelope is shown to over-cover A (the R8.4 defect)."""

from __future__ import annotations

import pytest

from engine.source import cad_profile as P
from engine.source import decoder_pins as PINS
from engine.source import qualification as Q
from engine.source.findings import SourceFinding
from engine.source import findings as F
from tests.r8_0 import libredwg_builder as B
from tests.r8_0.k1_harness import _imports, apply_test_schema_extensions

BUILD = PINS.PINS["LIBREDWG_DWGREAD"][0]["sha256"]
AREA = P.MeasurementMethod("FLOOR_AREA", scale_dependent=True)
ARC = {"kind": "ARC", "c": (1000.0, 0.0), "r": 500.0, "a0": 0.0, "a1": 90.0}
LINE = {"kind": "LINE", "a": (0.0, 0.0), "b": (2000.0, 0.0)}
STRAIGHT = {"kind": "LWPOLYLINE", "pts": [(0.0, 0.0), (1000.0, 0.0), (1000.0, 800.0)], "bulges": [0.0, 0.0, 0.0]}
BULGED = {"kind": "LWPOLYLINE", "pts": [(0.0, 0.0), (1000.0, 0.0)], "bulges": [0.4142, 0.0]}


def ins(block, at=(0.0, 0.0), scale=(1.0, 1.0), rot=0.0, extrusion=(0.0, 0.0, 1.0)):
    return {"kind": "INSERT", "block": block, "at": at, "scale": scale, "rot": rot, "extrusion": extrusion}


def doc(scene):
    _, _, lm = _imports()
    dec = B.build(scene)
    return apply_test_schema_extensions(dec, lm.to_document(dec)), dec


def sigs(scene):
    return Q.capability_signatures(doc(scene)[0])


def qualify(scene, verdict="PASS", qid="Q2-TEST", build=BUILD):
    s = sigs(scene)
    verdicts = {k: verdict for keys in s.values() for k in keys}
    return Q.DecoderQualificationV2(qid, "LIBREDWG_DWGREAD_JSON", build, Q.QUALIFIED, Q.signature_states(s, verdicts),
                                    ("c" * 64,), "INDEPENDENT_DXF->EZDXF K2", "PASS")


def kinds(sigset, kind):
    return {s for s in sigset if s.startswith(f"KIND={kind}|")}


def test_a_marginal_features_do_not_combine():
    qual_scene = {"blocks": {"A": {"entities": [ARC]}, "L": {"entities": [LINE]}},
                  "entities": [ins("A", at=(50.0, 0.0)), ins("L", scale=(-1.0, 1.0))]}
    target = {"blocks": {"A": {"entities": [ARC]}}, "entities": [ins("A", scale=(-1.0, 1.0))]}
    cov = Q.coverage_v2(sigs(target), [qualify(qual_scene)], BUILD)
    arc_unc = [u for u in cov["uncovered"] if u[0].startswith("KIND=ARC|")]
    assert not cov["covered"] and arc_unc and all(u[1] == Q.NOT_EXERCISED for u in arc_unc)
    assert all("REFLECTION" in u[0] and "NET=NET_REFLECTED" in u[0] for u in arc_unc)
    # the R8.4 flat envelope WOULD have covered it: that is the over-breadth V2 removes
    dq, _ = doc(qual_scene)
    dt, dect = doc(target)
    p_q, p_t = Q.source_feature_profile(dq), Q.source_feature_profile(dt, dect)
    env = Q.QualificationEnvelope(p_q.entity_kinds, p_q.transform_classes, p_q.max_block_depth,
                                  max_handle_bytes=p_t.handle.max_byte_size)
    assert env.covers(p_t) == ()


def test_b_straight_polyline_does_not_qualify_bulged():
    q = {"blocks": {"P": {"entities": [STRAIGHT]}}, "entities": [ins("P", scale=(-1.0, 1.0))]}
    t = {"blocks": {"P": {"entities": [BULGED]}}, "entities": [ins("P", scale=(-1.0, 1.0))]}
    assert kinds(sigs(q), "LWPOLYLINE_STRAIGHT") and kinds(sigs(t), "LWPOLYLINE_BULGE")
    cov = Q.coverage_v2(sigs(t), [qualify(q)], BUILD)
    assert any(u[0].startswith("KIND=LWPOLYLINE_BULGE|") for u in cov["uncovered"])


def test_c_depth_one_does_not_qualify_nested_reflected_depth_three():
    q = {"blocks": {"A": {"entities": [ARC]}}, "entities": [ins("A")]}
    t = {"blocks": {"A": {"entities": [ARC]}, "M": {"entities": [ins("A", scale=(-1.0, 1.0))]},
                    "O": {"entities": [ins("M")]}}, "entities": [ins("O")]}
    tgt = kinds(sigs(t), "ARC")
    assert tgt and all("DEPTH=3" in s and "REFLECTION" in s for s in tgt)
    cov = Q.coverage_v2(sigs(t), [qualify(q)], BUILD)
    assert {u[0] for u in cov["uncovered"]} >= tgt


def test_d_default_ocs_does_not_qualify_negative_z_arc():
    q = {"entities": [ARC]}
    t = {"entities": [dict(ARC, extrusion=(0.0, 0.0, -1.0))]}
    assert any("EXT=NEG_Z" in s for s in kinds(sigs(t), "ARC"))
    assert not Q.coverage_v2(sigs(t), [qualify(q)], BUILD)["covered"]


def test_e_ordinary_block_does_not_qualify_dynamic_anonymous():
    q = {"blocks": {"DOOR": {"entities": [ARC]}}, "entities": [ins("DOOR")]}
    t = {"blocks": {"*U7": {"entities": [ARC]}}, "entities": [ins("*U7")]}
    assert any("CTX=DYNAMIC_ANONYMOUS" in s for s in kinds(sigs(t), "ARC"))
    assert not Q.coverage_v2(sigs(t), [qualify(q)], BUILD)["covered"]


def _sig(handle):
    return Q.signature("LINE", set(), 1, 0, "DEFAULT", frozenset(), True, handle)


def _q_from(signatures):
    return Q.DecoderQualificationV2("Q2-H", "LIBREDWG", BUILD, Q.QUALIFIED,
                                    tuple((s, Q.EXERCISED_AND_PASS, 1, 0) for s in signatures), ("c" * 64,), "IND", "PASS")


def test_f_two_byte_handles_do_not_qualify_three_byte():
    assert Q.handle_class("2894") == Q.H12 and Q.handle_class(f"{0x012894}+3B") == Q.H3_CONSISTENT
    cov = Q.coverage_v2({_sig(Q.H3_CONSISTENT): []}, [_q_from([_sig(Q.H12)])], BUILD)
    assert not cov["covered"] and cov["uncovered"][0][1] == Q.NOT_EXERCISED


def test_g_consistent_three_byte_does_not_qualify_the_inconsistency_domain():
    assert Q.handle_class("10388+3B") == Q.H3_INCONSISTENT          # 3 bytes declared, value fits in 2
    assert not Q.coverage_v2({_sig(Q.H3_INCONSISTENT): []}, [_q_from([_sig(Q.H3_CONSISTENT)])], BUILD)["covered"]
    assert Q.coverage_v2({_sig(Q.H3_INCONSISTENT): []}, [_q_from([_sig(Q.H3_INCONSISTENT)])], BUILD)["covered"]


def test_reference_domains_have_their_own_signatures():
    s = sigs({"blocks": {"A": {"entities": [ARC]}}, "entities": [ins("A")]})
    assert any(x.startswith("REF=INSERT_LINEAGE|") for x in s) and any(x.startswith("REF=BLOCK_RECORD_LINEAGE|") for x in s)


def test_double_reflection_is_its_own_signature():
    one = kinds(sigs({"blocks": {"A": {"entities": [ARC]}}, "entities": [ins("A", scale=(-1.0, 1.0))]}), "ARC")
    two = kinds(sigs({"blocks": {"A": {"entities": [ARC]}, "M": {"entities": [ins("A", scale=(-1.0, 1.0))]}},
                      "entities": [ins("M", scale=(1.0, -1.0))]}), "ARC")
    assert all("NET=NET_REFLECTED" in x for x in one) and all("NET=NET_DIRECT" in x and "REFLECTION" in x for x in two)
    assert not one & two


def test_one_nonpass_occurrence_makes_the_signature_nonpass_no_percentage():
    s = {"SIG": [("o%d" % i, ()) for i in range(1000)]}
    verdicts = {k: "PASS" for k in s["SIG"]}
    verdicts[("o999", ())] = "WARN"
    (row,) = Q.signature_states(s, verdicts)
    assert row[1] == Q.EXERCISED_NONPASS and row[2] == 999 and row[3] == 1
    for bad in ("BLOCK", "KNOWN_LIBRARY_LIMITATION", "UNMATCHED", "AMBIGUOUS", None):
        v = dict(verdicts)
        v[("o999", ())] = bad
        assert Q.signature_states(s, v)[0][1] == Q.EXERCISED_NONPASS
    q = Q.DecoderQualificationV2("Q", "R", BUILD, Q.QUALIFIED, (("OK", Q.EXERCISED_AND_PASS, 1, 0), row), ("c" * 64,),
                                 "IND", "PASS")
    assert Q.coverage_v2({"SIG": []}, [q], BUILD)["uncovered"] == [("SIG", Q.EXERCISED_NONPASS)]


def test_equivalence_is_explicit_and_none_is_admitted_in_production():
    assert Q.EQUIVALENCE_RULES == ()
    rule = Q.EquivalenceRule("EQ-TEST-01", "HANDLE=H12", "HANDLE=H3_CONSISTENT", "test-local only", ("this test",),
                             covers=lambda qs, t: qs.replace("HANDLE=H12", "HANDLE=H3_CONSISTENT") == t)
    cov = Q.coverage_v2({_sig(Q.H3_CONSISTENT): []}, [_q_from([_sig(Q.H12)])], BUILD, rules=(rule,))
    assert cov["covered"] and cov["via_equivalence"] == [(_sig(Q.H3_CONSISTENT), "EQ-TEST-01")]


def test_v2_record_refuses_unfounded_qualification():
    with pytest.raises(ValueError):
        Q.DecoderQualificationV2("Q", "R", BUILD, Q.QUALIFIED, (("S", Q.EXERCISED_NONPASS, 0, 1),), ("c" * 64,), "IND")
    with pytest.raises(ValueError):
        Q.DecoderQualificationV2("Q", "R", BUILD, Q.QUALIFIED, (("S", Q.EXERCISED_AND_PASS, 1, 0),))
    with pytest.raises(ValueError):
        Q.DecoderQualificationV2("Q", "R", BUILD, Q.QUALIFIED, (("S", Q.NOT_EXERCISED, 0, 0),), ("c" * 64,), "IND")
    blocked = Q.DecoderQualificationV2("Q", "R", BUILD, Q.BLOCKED_EXTERNAL_INPUT)
    assert not Q.coverage_v2({"S": []}, [blocked], BUILD)["covered"]
    assert blocked.schema == "URBAN_DECODER_QUALIFICATION_V2"


def test_parser_policy_v3_uses_signatures_and_v2_is_reproducible():
    scene = {"blocks": {"A": {"entities": [ARC]}}, "entities": [ins("A", at=(10.0, 0.0))]}
    s = sigs(scene)
    v3 = P.ParserIndependencePolicy(policy_id=P.PARSER_POLICY_V3_ID, qualifications=(qualify(scene),))
    ctx = P.SourceValidationContext(True, PINS.REGISTERED, BUILD, capability_signatures=s)
    assert P.parser_requirement(ctx, (), AREA, v3)[0] == "PASS"
    other = sigs({"blocks": {"A": {"entities": [ARC]}}, "entities": [ins("A", scale=(-1.0, 1.0))]})
    ctx2 = P.SourceValidationContext(True, PINS.REGISTERED, BUILD, capability_signatures=other)
    assert P.parser_requirement(ctx2, (), AREA, v3)[0] == "FAIL"
    assert P.parser_requirement(P.SourceValidationContext(True, PINS.REGISTERED, BUILD), (), AREA, v3)[0] == "FAIL"
    risk = [SourceFinding(F.HANDLE_VALUE_TRUNCATED)]
    assert P.parser_requirement(ctx, risk, AREA, v3)[0] == "FAIL"
    assert P.DEFAULT_PARSER_POLICY.policy_id == P.PARSER_POLICY_V3_ID and P.DEFAULT_PARSER_POLICY.qualifications == ()
    assert P.DEFAULT_CAD_PROFILE.profile_id == "URBAN_CAD_PROFILE_V3"
    assert P.PARSER_POLICY_V2.policy_id == P.PARSER_POLICY_V2_ID
