"""Where each R8 contract will live in production — the ONE place names are bound.

R8.0 writes the tests before the code. Every production symbol the tests
will call is named here and nowhere else, so R8.1 may choose different
module names by editing this table (a reviewed change), never by editing
test assertions.

A target that does not exist yet raises TargetNotImplemented. Tests that
call it are registered TARGET_NOT_IMPLEMENTED in R8_0_EXPECTED_FAILURES.json
and marked strict-xfail on exactly that exception, so:
  * today they report XFAIL (the contract is written, the code is not);
  * the day the module appears they run for real, and a pass shows up as a
    strict XPASS failure until the register is updated — the ratchet.

Dependency rule (R8.0 brief §6, §21): engine.source.* must not import
engine.qs_core or engine.ingest. The qs_core targets below are downstream
consumers of source observations.
"""

from __future__ import annotations

import importlib


class TargetNotImplemented(ImportError):
    """The production module/function for an R8 contract does not exist yet."""


TARGETS = {
    # source fidelity (engine/source) -------------------------------------
    "K1_REALISE": "engine.source.cad.kernel:realise",
    "K2_REALISE": "engine.source.cad.kernel_ezdxf:realise",
    "OCS_PLAN_FRAME": "engine.source.cad.kernel_ocs:plan_frame",
    "CAPABILITY_REGISTER": "engine.source.cad.census:capability_register",
    "CAD_TEXT_PLAIN": "engine.source.cad.text:plain",
    "DIMENSION_MEASURE": "engine.source.cad.dimensions:measured",
    "SOURCE_REPRESENTATION_DIGEST": "engine.source.digests:source_representation_digest",
    "REALISED_GEOMETRY_DIGEST": "engine.source.digests:realised_geometry_digest",
    "RECONCILE": "engine.source.reconcile:reconcile",
    "UNIT_CONTEXT": "engine.source.units:resolve_unit_context",
    "FRAMES": "engine.source.frames:resolve_frames",
    "FRAME_EVIDENCE": "engine.source.frames:independent_evidence",
    "SOURCE_PROFILE": "engine.source.source_profile:evaluate",
    "SOURCE_DELTA": "engine.source.deltas:classify",
    # downstream evidence (engine/qs_core) -------------------------------
    "FACT_POLICY_RESOLVE": "engine.qs_core.fact_policy:resolve",
    "FACT_POLICY_LOAD": "engine.qs_core.fact_policy:load_policy",
    "SCOPE_APPLIES": "engine.qs_core.scope_selector:applies",
    "SCOPE_VALIDATE": "engine.qs_core.scope_selector:validate",
    "TRANSCRIPTION_PROMOTE": "engine.qs_core.transcription:promote",
    "TRANSCRIPTION_RECORD": "engine.qs_core.transcription:record",
    "CLAIM_FROM": "engine.qs_core.evidence:claim_from_producer",
    "PUBLISH_WITH_FRAME": "engine.qs_core.quantities:publish_with_frame",
}


def resolve(name):
    spec = TARGETS[name]
    mod_name, _, attr = spec.partition(":")
    try:
        mod = importlib.import_module(mod_name)
    except ModuleNotFoundError as err:
        raise TargetNotImplemented(f"{name} -> {spec}: module not implemented ({err.name})") from None
    fn = getattr(mod, attr, None)
    if fn is None:
        raise TargetNotImplemented(f"{name} -> {spec}: symbol not implemented")
    return fn


def call(name, *args, **kwargs):
    return resolve(name)(*args, **kwargs)
