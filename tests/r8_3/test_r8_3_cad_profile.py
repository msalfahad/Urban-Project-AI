"""R8.3 — CAD_VALIDATION_PROFILE: FINAL eligibility (§22, §38, §41), parser-independence policy
(§23), decoder pins (§3, §4) and anti-calibration (§49)."""

from __future__ import annotations

import re
from pathlib import Path

from engine.source import cad_profile as P
from engine.source import decoder_pins as PINS
from engine.source import findings as F
from engine.source import frame as FR
from engine.source.findings import SourceFinding

ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 64
BUILD = PINS.PINS["LIBREDWG_DWGREAD"][0]["sha256"]
AREA = P.MeasurementMethod("FLOOR_AREA", scale_dependent=True)
COUNT = P.MeasurementMethod("DOOR_COUNT", scale_dependent=False, requires_identity=True)
UNDECLARED = P.MeasurementMethod("SOMETHING", scale_dependent=None)
QUALIFIED = P.ParserIndependencePolicy(qualified_builds=frozenset({BUILD}))


def _ev(eid, kind, lineage, producer=FR.ENGINE):
    return FR.UnitEvidence(eid, FR.NATIVE_UNIT, kind, "MS", (lineage,), 1.0, source_sha256=SHA, producer=producer)


def frames(verified=True):
    decl = list(FR.declaration_evidence(4, "MS", SHA)[0])
    extra = [_ev("E1", FR.KNOWN_PLOT_DIMENSION, "AUTHORED:PLOT", FR.HUMAN), _ev("E2", FR.EXPLICIT_UNIT_NOTE, "AUTHORED:NOTE")]
    u = FR.unit_context(SHA, "MS", FR.MODEL_SPACE, decl + (extra if verified else []), insunits=4)
    r = FR.region_transform(u, "PLAN", FR.MODEL_SPACE_PLAN, reference=True)
    return u, r, FR.measurement_frame(u, r)


def ctx(**kw):
    base = dict(conservation_balanced=True, decode_pin_status=PINS.REGISTERED, decoder_binary_sha256=BUILD)
    base.update(kw)
    return P.SourceValidationContext(**base)


def run(kind="LINE", method=AREA, c=None, verified=True, policy=QUALIFIED, **kw):
    u, r, f = frames(verified)
    return P.evaluate(kind, "D1:5", (), method, c or ctx(), f, u, r, parser_policy=policy, **kw)


def failed(res):
    return {r[0] for r in res.blocking}


def test_everything_established_is_final_eligible():
    res = run()
    assert res.final_eligible and FR.FINAL_MEASUREMENT in res.eligible_uses and not res.blocking


def test_verified_geometry_with_provisional_frame_is_not_final():
    res = run(verified=False)
    assert not res.final_eligible and {"E_UNIT", "G_FRAME"} <= failed(res)
    assert FR.PREVIEW_MEASUREMENT in res.eligible_uses


def test_verified_frame_with_a_geometry_blocker_is_not_final():
    res = run(observation_findings=(SourceFinding(F.OWNER_UNRESOLVED, "D1:5"),))
    assert not res.final_eligible and "H_FINDINGS" in failed(res)


def test_identity_blocker_only_does_not_stop_unrelated_geometry_measurement():
    res = run(observation_findings=(SourceFinding(F.DYNAMIC_BLOCK_IDENTITY_UNVERIFIED, "D1:5"),))
    assert res.final_eligible


def test_identity_blocker_does_stop_an_identity_count():
    res = run(kind="INSERT", method=COUNT,
              observation_findings=(SourceFinding(F.DYNAMIC_BLOCK_IDENTITY_UNVERIFIED, "D1:5"),))
    assert not res.final_eligible and "H_FINDINGS" in failed(res)


def test_exact_ellipse_is_retained_but_scale_dependent_final_is_blocked():
    res = run(kind="ELLIPSE")
    assert not res.final_eligible and "I_DOWNSTREAM" in failed(res)


def test_scale_independent_count_proceeds_without_a_final_frame():
    res = run(kind="INSERT", method=COUNT, verified=False)
    assert res.final_eligible and res.eligible_uses == (FR.COUNT_ONLY,)
    assert all(r[1] == "NOT_APPLICABLE" for r in res.requirements if r[0] in ("E_UNIT", "F_REGION", "G_FRAME"))


def test_undeclared_scale_dependence_is_never_assumed_count_only():
    res = run(kind="INSERT", method=UNDECLARED, verified=False)
    assert not res.final_eligible and "METHOD" in failed(res)


def test_good_geometry_never_cures_bad_units():
    u = FR.unit_context(SHA, "MS", FR.MODEL_SPACE,
                        list(FR.declaration_evidence(1, "MS", SHA)[0]) + [_ev("E1", FR.KNOWN_PLOT_DIMENSION, "AUTHORED:P")],
                        insunits=1)
    r = FR.region_transform(u, "PLAN", FR.MODEL_SPACE_PLAN, reference=True)
    res = P.evaluate("LINE", "D1:5", (), AREA, ctx(), FR.measurement_frame(u, r), u, r, parser_policy=QUALIFIED)
    assert u.status == FR.CONFLICT and not res.final_eligible and FR.PREVIEW_MEASUREMENT not in res.eligible_uses


def test_verified_units_never_cure_unsupported_or_xref_geometry():
    for code in (F.XREF_NOT_RESOLVED, F.UNSUPPORTED, F.CUSTOM_CLASS):
        res = run(region_findings=(SourceFinding(code, "D1:99", (), "", scope=None),))
        assert not res.final_eligible and "H_FINDINGS" in failed(res), code


def test_an_unsupported_object_elsewhere_does_not_block_this_region():
    ole = SourceFinding(F.SKIPPED, "D1:777")                           # an OLE in the title block
    res = run(observation_findings=(ole,))
    assert res.final_eligible


def test_unbalanced_conservation_or_unestablished_pin_blocks_final():
    assert "C_SOURCE" in failed(run(c=ctx(conservation_balanced=False)))
    assert "C_SOURCE" in failed(run(c=ctx(decode_pin_status=PINS.NOT_ESTABLISHED, decoder_binary_sha256=None)))
    assert run(c=ctx(decode_pin_status=PINS.REPRODUCED_BY_REGISTERED_BUILD, decoder_binary_sha256=BUILD)).final_eligible


# ---------------------------------------------------------------- parser-independence policy (§23)

TRUNC = SourceFinding(F.HANDLE_VALUE_TRUNCATED)                       # document-wide


def test_option_b_requires_an_independent_parser_when_parser_risk_is_in_scope():
    res = run(c=ctx(document_findings=(TRUNC,)))
    assert "D_ROUTES" in failed(res)
    ok = run(c=ctx(document_findings=(TRUNC,),
                   reconciliation={"verdict": "PASS", "parser_independence": "INDEPENDENT_PARSER"}))
    assert ok.final_eligible


def test_option_b_today_behaves_like_option_a_because_no_build_is_qualified():
    res = run(policy=P.DEFAULT_PARSER_POLICY)
    assert P.DEFAULT_PARSER_POLICY.qualified_builds == frozenset()
    assert "D_ROUTES" in failed(res)


def test_shared_parser_reconciliation_never_satisfies_the_parser_requirement():
    res = run(c=ctx(document_findings=(TRUNC,), reconciliation={"verdict": "PASS", "parser_independence": "SHARED_PARSER"}))
    assert "D_ROUTES" in failed(res)


def test_benchmark_qualification_always_requires_an_independent_parser():
    bench = P.MeasurementMethod("BENCH_AREA", scale_dependent=True, benchmark_qualification=True)
    assert "D_ROUTES" in failed(run(method=bench))


def test_option_c_accepts_a_registered_build_without_risk():
    c_policy = P.ParserIndependencePolicy(option=P.OPTION_C)
    assert run(policy=c_policy).final_eligible
    assert "D_ROUTES" in failed(run(policy=c_policy, c=ctx(document_findings=(TRUNC,))))


# ---------------------------------------------------------------- decoder pins (§3, §4, §17)

def test_historical_decodes_are_reproduced_by_the_registered_build():
    for sha, rec in PINS.REPRODUCTIONS.items():
        assert PINS.decode_status(sha) == PINS.REPRODUCED_BY_REGISTERED_BUILD
        assert rec["binary_sha256"] == BUILD
    assert PINS.decode_status("0" * 64) == PINS.NOT_ESTABLISHED


def test_handle_defect_is_attributed_only_after_pinned_reproduction():
    d = PINS.KNOWN_REPRESENTATION_DEFECTS["PINNED_LIBREDWG_DWGREAD_JSON_HANDLE_REPRESENTATION_DEFECT"]
    assert d["binary_sha256"] == BUILD and d["previous_name"] == "OBSERVED_HANDLE_TRUNCATION_IN_EXISTING_LIBREDWG_JSON"
    assert d["layer"].startswith("NOT_LOCALISED")


def test_build_provenance_is_recorded_honestly():
    bp = PINS.PINS["LIBREDWG_DWGREAD"][0]["build_provenance"]
    assert bp["status"] == "BUILD_CONFIGURATION_NOT_FULLY_RECORDED" and "CFLAGS" in bp


# ---------------------------------------------------------------- anti-calibration (§49)

PROJECT_NUMBERS = ("146.97", "146.7697", "935.94", "921.72", "140.9111")
PROJECT_WORDS = re.compile(r"(?i)al\s*rashed|alrashed|qortuba|qurtoba|p7757")


def test_frame_and_profile_modules_carry_no_project_value_or_name():
    for name in ("frame.py", "cad_profile.py", "reconcile.py"):
        text = (ROOT / "engine/source" / name).read_text()
        assert not PROJECT_WORDS.search(text), name
        assert not any(n in text for n in PROJECT_NUMBERS), name


def test_thresholds_are_not_derived_from_project_quantities():
    text = (ROOT / "engine/source/frame.py").read_text()
    assert "AGREEMENT_REL = 0.005" in text and "CHECKED_DIM_ABS_MM = 2.0" in text
    assert "CHECKED_DIM_REL = 0.002" in text
