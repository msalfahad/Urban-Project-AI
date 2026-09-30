"""CAD_VALIDATION_PROFILE (R8.3 §22, §41) — may this CAD observation support this use?

A measurement is FINAL-eligible only when EVERY requirement that applies to it passes:

    A CAPABILITY      the source kind's capability row permits the use
    B MAPPING         the kind's route mapping is established (VERIFIED*)
    C SOURCE          source conservation balanced; decode pin REGISTERED or REPRODUCED
    D ROUTES          K1 realised it without a GEOMETRY-blocking finding, and the
                      reconciliation requirement of the PARSER_INDEPENDENCE_POLICY holds
    E UNIT            the UNIT_CONTEXT permits FINAL
    F REGION          the REGION_MEASUREMENT_TRANSFORM permits FINAL
    G FRAME           the composed MEASUREMENT_FRAME permits FINAL
    H FINDINGS        no finding IN SCOPE is BLOCKING in a domain the method depends on
    I DOWNSTREAM      the downstream geometry stack can preserve / measure this kind

Good geometry never cures bad units (E-G are independent of A-D) and verified units never
cure missing / xref / unsupported geometry (A-D, H are independent of E-G).

SCOPE. Findings are scoped: those on this observation, its instance path, the region
being measured (region_findings, supplied by the caller) and document-wide findings
(obs_id None, no scope). An unsupported OLE object in a title block does not block an
unrelated floor region, because its finding is not in that region's scope.

METHOD. The measurement method must DECLARE scale_dependent. A method with
scale_dependent = False (a count by established identity) skips E-G and I; a method that
does not declare it is never assumed count-only (§15, §38).

BOUNDARY (§40). qs_core will consume ProfileResult (eligible uses, blocking requirements
with their domains, the frame status and the evidence ids) — never raw INSUNITS, viewport
scales or decoder detail. R8.3 is SHADOW: no production module consumes this yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import capability as C
from . import decoder_pins as PINS
from . import findings as F
from . import frame as FR
from . import qualification as Q
from . import reconcile as R

# ---------------------------------------------------------------- parser-independence policy (data)
OPTION_A = "A_INDEPENDENT_PARSER_ALWAYS"
OPTION_B = "B_INDEPENDENT_PARSER_ON_RISK_OR_QUALIFICATION"
OPTION_C = "C_INDEPENDENT_PARSER_ADDITIONAL_CONFIDENCE"

PARSER_RISK_CODES = frozenset({F.HANDLE_VALUE_TRUNCATED, F.ROUTE_DECODE_FAILED, F.SOURCE_TYPE_CONFLICT,
                               F.SOURCE_MAPPING_UNVERIFIED})


PARSER_POLICY_V1_ID = "URBAN_PARSER_INDEPENDENCE_V1"
PARSER_POLICY_V2_ID = "URBAN_PARSER_INDEPENDENCE_V2"


@dataclass(frozen=True)
class ParserIndependencePolicy:
    """Claude's recommendation (R8.3 §23, kept in R8.4): option B. An independent parser (AutoCAD /
    ODA export reconciled K1 vs K2) is REQUIRED for a scope when a parser-risk finding is in scope,
    when the decode pin is not REGISTERED / REPRODUCED, for benchmark qualification, and for the
    first migration consumer; otherwise a qualified decoder + K1 + source conservation +
    capability gates suffice.

    V1 (R8.3, reproducible): "qualified" = the build's sha256 is in `qualified_builds` — global.
    V2 (R8.4, default): "qualified" = a DecoderQualification for this build whose ENVELOPE covers
    the source's feature profile (qualification.qualification_for). `qualified_builds` is kept for
    V1 compatibility only and ignored by V2. `qualifications` is EMPTY today: no build has passed
    a real independent-parser comparison (no independent export was supplied in R8.4)."""
    option: str = OPTION_B
    qualified_builds: frozenset = frozenset()
    require_for_benchmark: bool = True
    policy_id: str = PARSER_POLICY_V1_ID
    qualifications: tuple = ()


PARSER_POLICY_V1 = ParserIndependencePolicy()
PARSER_POLICY_V2 = ParserIndependencePolicy(policy_id=PARSER_POLICY_V2_ID)
DEFAULT_PARSER_POLICY = PARSER_POLICY_V2

CAD_PROFILE_V1_ID = "URBAN_CAD_PROFILE_V1"
CAD_PROFILE_V2_ID = "URBAN_CAD_PROFILE_V2"


@dataclass(frozen=True)
class CadProfilePolicy:
    """Versioned CAD profile (R8.4 §32). V1 = R8.3 behaviour (global qualified builds, frame
    release V1). V2 = envelope qualification, frame release V2, region designation required
    for a reference region's authority (frame.region_transform)."""
    profile_id: str
    parser_policy: ParserIndependencePolicy
    frame_policy: object


CAD_PROFILE_V1 = CadProfilePolicy(CAD_PROFILE_V1_ID, PARSER_POLICY_V1, FR.RELEASE_V1)
CAD_PROFILE_V2 = CadProfilePolicy(CAD_PROFILE_V2_ID, PARSER_POLICY_V2, FR.RELEASE_V2)
DEFAULT_CAD_PROFILE = CAD_PROFILE_V2


@dataclass(frozen=True)
class MeasurementMethod:
    method_id: str
    scale_dependent: bool | None           # MUST be declared; None -> never count-only
    requires_identity: bool = False
    benchmark_qualification: bool = False


@dataclass(frozen=True)
class SourceValidationContext:
    """What is known about the source as a whole (produced once per source)."""
    conservation_balanced: bool
    decode_pin_status: str                  # decoder_pins.decode_status(...)
    decoder_binary_sha256: str | None
    document_findings: tuple = ()           # findings with obs_id None
    reconciliation: dict | None = None      # {"verdict", "parser_independence", "by_key": {(handle, path): status}}
    feature_profile: object = None          # qualification.SourceFeatureProfile (V2 envelope check)


@dataclass(frozen=True)
class ProfileResult:
    requirements: tuple                     # ((id, PASS|FAIL|NOT_APPLICABLE, reason, domain), ...)
    final_eligible: bool
    eligible_uses: tuple
    blocking: tuple
    frame_status: str | None
    evidence_ids: tuple = ()

    def as_dict(self):
        return {"requirements": [dict(zip(("id", "status", "reason", "domain"), r)) for r in self.requirements],
                "final_eligible": self.final_eligible, "eligible_uses": list(self.eligible_uses),
                "blocking": [dict(zip(("id", "status", "reason", "domain"), r)) for r in self.blocking],
                "frame_status": self.frame_status, "evidence_ids": list(self.evidence_ids)}


GEOMETRY_DOMAINS = (F.GEOMETRY, F.GEOMETRY_COMPLETENESS, F.SOURCE_COMPLETENESS)
SCALE_DOMAINS = (F.MEASUREMENT_FRAME, F.DOWNSTREAM_SUPPORT)
IDENTITY_DOMAINS = (F.IDENTITY, F.SEMANTICS)


def _domains_for(method: MeasurementMethod):
    d = set(GEOMETRY_DOMAINS)
    if method.scale_dependent:
        d |= set(SCALE_DOMAINS)
    if method.requires_identity:
        d |= set(IDENTITY_DOMAINS)
    return d


def _in_scope(f, obs_id, instance_path, region_ids):
    if f.obs_id is not None:
        return f.obs_id == obs_id and (not f.instance_path or tuple(f.instance_path) == tuple(instance_path))
    if f.scope:
        return f.scope in region_ids
    return True                                           # document-wide


def parser_requirement(ctx: SourceValidationContext, scope_findings, method: MeasurementMethod,
                       policy: ParserIndependencePolicy, key=None):
    """(status, reason) of requirement D's parser half."""
    risk = sorted({f.code for f in scope_findings if f.code in PARSER_RISK_CODES})
    pin_ok = ctx.decode_pin_status in (PINS.REGISTERED, PINS.REPRODUCED_BY_REGISTERED_BUILD)
    rec = ctx.reconciliation or {}
    indep = rec.get("parser_independence") == "INDEPENDENT_PARSER"
    rec_ok = rec.get("verdict") in (R.PASS, R.WARN)
    if key is not None and rec.get("by_key") is not None:
        rec_ok = rec_ok and rec["by_key"].get(key) in (R.PASS, R.WARN)
    if policy.policy_id == PARSER_POLICY_V2_ID:
        qual = Q.qualification_for(ctx.decoder_binary_sha256, ctx.feature_profile, policy.qualifications)
        build_ok, build_why = qual["covered"], qual["reason"]
    else:
        build_ok = ctx.decoder_binary_sha256 in policy.qualified_builds
        build_why = "decoder build not qualified by any independent-parser comparison"
    need = (policy.option == OPTION_A or risk or not pin_ok
            or (method.benchmark_qualification and policy.require_for_benchmark)
            or (policy.option == OPTION_B and not build_ok))
    if policy.option == OPTION_C and pin_ok and not risk:
        need = False
    if not need:
        return "PASS", ("qualified decoder build, no parser-risk finding in scope" if policy.policy_id != PARSER_POLICY_V2_ID
                        else f"{build_why}; no parser-risk finding in scope")
    if indep and rec_ok:
        return "PASS", "independent-parser reconciliation PASS for this scope"
    why = []
    if risk:
        why.append("parser-risk findings in scope: " + ",".join(risk))
    if not pin_ok:
        why.append(f"decode pin {ctx.decode_pin_status}")
    if not build_ok:
        why.append(build_why)
    why.append("independent-parser reconciliation " + ("not PASS" if indep else "not available"))
    return "FAIL", "; ".join(why)


def evaluate(kind: str, obs_id: str, instance_path, method: MeasurementMethod, ctx: SourceValidationContext,
             frame: FR.MeasurementFrame | None, unit: FR.UnitContext | None = None,
             region: FR.RegionMeasurementTransform | None = None, observation_findings=(), region_findings=(),
             k1_realised: bool = True, parser_policy: ParserIndependencePolicy = DEFAULT_PARSER_POLICY,
             reconciliation_key=None) -> ProfileResult:
    rows = []

    def add(rid, ok, reason, domain):
        rows.append((rid, ok, reason, domain))

    if method.scale_dependent is None:
        add("METHOD", "FAIL", "measurement method does not declare scale_dependent; count-only is never assumed",
            F.MEASUREMENT_FRAME)
    scale = method.scale_dependent is not False
    row = C.BY_KIND.get(kind)
    # A capability
    if row is None:
        add("A_CAPABILITY", "FAIL", f"no capability row for {kind}", F.GEOMETRY_COMPLETENESS)
    else:
        uses = set(row["downstream_allowed_uses"])
        if scale and C.FINAL_GEOMETRY not in uses:
            add("A_CAPABILITY", "FAIL", f"{kind} allows {sorted(uses)}", F.GEOMETRY)
        elif not scale and not (uses & {C.FINAL_GEOMETRY, C.IDENTITY_CANDIDATE}):
            add("A_CAPABILITY", "FAIL", f"{kind} allows {sorted(uses)}; not countable", F.IDENTITY)
        else:
            add("A_CAPABILITY", "PASS", f"{kind}: {sorted(uses)}", None)
    # B mapping (D1)
    m = row["routes"].get(C.D1) if row else None
    add("B_MAPPING", "PASS" if m and str(m).startswith("VERIFIED") else "FAIL", f"D1 mapping {m}",
        F.GEOMETRY_COMPLETENESS)
    # C source
    pin_ok = ctx.decode_pin_status in (PINS.REGISTERED, PINS.REPRODUCED_BY_REGISTERED_BUILD)
    add("C_SOURCE", "PASS" if ctx.conservation_balanced and pin_ok else "FAIL",
        f"conservation {'balanced' if ctx.conservation_balanced else 'UNBALANCED'}; decode pin {ctx.decode_pin_status}",
        F.SOURCE_COMPLETENESS)
    # H findings in scope (computed before D so D sees the same scope)
    region_ids = {x for x in (getattr(region, "region_id", None), getattr(unit, "coordinate_space_id", None)) if x}
    scoped = [f for f in list(observation_findings) + list(region_findings) + list(ctx.document_findings)
              if _in_scope(f, obs_id, instance_path, region_ids) or f in region_findings]
    doms = _domains_for(method)
    blocking = sorted({(f.code, d) for f in scoped for d in f.blocking_domains if d in doms
                       and d != F.MEASUREMENT_FRAME})         # frame domain is judged by E-G, not twice
    add("H_FINDINGS", "FAIL" if blocking else "PASS",
        "; ".join(f"{c} {d}" for c, d in blocking) or "no in-scope blocking finding in the method's domains",
        blocking[0][1] if blocking else None)
    # D routes
    k1_geom_block = any(F.GEOMETRY in f.blocking_domains for f in observation_findings)
    st, why = parser_requirement(ctx, scoped, method, parser_policy, reconciliation_key)
    d_ok = k1_realised and not k1_geom_block and st == "PASS"
    add("D_ROUTES", "PASS" if d_ok else "FAIL",
        ("K1 realised" if k1_realised and not k1_geom_block else "K1 did not realise it cleanly") + f"; parser: {why}",
        F.GEOMETRY)
    # E-G frame, I downstream
    if scale:
        for rid, rec in (("E_UNIT", unit), ("F_REGION", region), ("G_FRAME", frame)):
            if rec is None:
                add(rid, "FAIL", "absent", F.MEASUREMENT_FRAME)
                continue
            ok = FR.FINAL_MEASUREMENT in rec.allowed_use
            add(rid, "PASS" if ok else "FAIL", f"{rec.status}: {sorted(rec.allowed_use)}", F.MEASUREMENT_FRAME)
        dm = bool(row and row["downstream_measurement_supported"])
        add("I_DOWNSTREAM", "PASS" if dm else "FAIL",
            f"{kind} downstream measurement {'supported' if dm else 'NOT supported (retained exact; preview only)'}",
            F.DOWNSTREAM_SUPPORT)
    else:
        for rid in ("E_UNIT", "F_REGION", "G_FRAME", "I_DOWNSTREAM"):
            add(rid, "NOT_APPLICABLE", "method declares scale_dependent = False", None)
    fails = tuple(r for r in rows if r[1] == "FAIL")
    final = not fails
    uses = []
    if final:
        uses.append(FR.FINAL_MEASUREMENT if scale else FR.COUNT_ONLY)
    # preview: everything but the FINAL-only frame / pin / parser / downstream gates must hold
    preview_blockers = [r for r in fails if r[0] in ("METHOD", "A_CAPABILITY", "B_MAPPING", "H_FINDINGS")]
    frame_preview = frame is None or FR.PREVIEW_MEASUREMENT in frame.allowed_use
    if scale and not preview_blockers and frame_preview:
        uses.append(FR.PREVIEW_MEASUREMENT)
    ev = tuple((unit.evidence_ids if unit else ()) + (region.evidence_ids if region else ()))
    return ProfileResult(tuple(rows), final, tuple(uses), fails, frame.status if frame else None, ev)


# ---------------------------------------------------------------- V-CAD check ids (R8.4 §10)
# The R8 revised spec, later edition (sha256 17e1a9cd..., §6a) names the CAD_PROFILE checks
# V-CAD-1..6. R8.3 stated requirements A-I without that numbering (and wrongly reported the
# numbering as undefined). The mapping below is the R8.4 reviewed binding; A-I stay the
# evaluated requirements, V-CAD ids are a reporting view over them.
V_CAD_CHECKS = {
    "V-CAD-1": ("D_ROUTES", "kernel reconciliation PASS for every INSERT-placed observation used"),
    "V-CAD-2": ("C_SOURCE", "no SOURCE-scope decode conflict"),
    "V-CAD-3": ("C_SOURCE", "census frozen (source conservation balanced)"),
    "V-CAD-4": ("H_FINDINGS", "no unresolved XREF in the region"),
    "V-CAD-5": ("H_FINDINGS", "no UNHANDLED class on a profile-relevant layer of the region"),
    "V-CAD-6": (None, "parser independence recorded; the spec says not required, the R8.3 parser policy "
                      "(option B) is stricter and is what D_ROUTES enforces"),
}
UNREALISED_CLASS_CODES = frozenset({F.UNHANDLED, F.SKIPPED, F.PROXY, F.CUSTOM_CLASS, F.UNSUPPORTED})
XREF_CODES = frozenset({F.XREF_NOT_RESOLVED, F.XREF_CONTENT_NOT_IN_SOURCE, F.XREF_UNLOADED})


def region_class_findings(capability_rows, region_id: str, relevant_layers, in_region=None) -> list:
    """V-CAD-5 input. Census rows for unrealised classes, re-scoped to a region by LAYER.

    `relevant_layers` is supplied by the caller: the layers the region's measured observations
    use, plus layers an adapter / region-role claim designates as walls, openings, columns,
    labels or dimensions. engine/source holds no layer names. `in_region(row) -> True | False |
    None` places a row spatially; None (an unrealised entity usually has no geometry to place)
    keeps it in scope — fail closed.

    Relevant layer  -> the census impacts, scoped to the region (BLOCKING GEOMETRY_COMPLETENESS)
    Other layer     -> REVIEW only (the spec's WARN)"""
    out = []
    layers = set(relevant_layers)
    for r in capability_rows:
        if r.get("code") not in UNREALISED_CLASS_CODES and r.get("code") not in XREF_CODES:
            continue
        where = in_region(r) if in_region else None
        if where is False:
            continue
        relevant = r.get("layer") in layers or r.get("code") in XREF_CODES
        imp = tuple((i["domain"], i["severity"]) for i in r.get("impacts", ())) if relevant else \
            ((F.GEOMETRY_COMPLETENESS, F.REVIEW),)
        out.append(F.SourceFinding(r["code"], None, (),
                                   f"{r.get('source_type')} handle {r.get('handle')} on layer {r.get('layer')!r}: "
                                   + ("profile-relevant layer of the region" if relevant else "layer not profile-relevant"),
                                   imp or None, scope=region_id))
    return out


def v_cad_view(result: ProfileResult, region_findings=()) -> dict:
    """V-CAD-n PASS/FAIL derived from an evaluated ProfileResult (reporting view only)."""
    req = {r[0]: r[1] for r in result.requirements}
    blocking = {f.code for f in region_findings if f.blocking_domains}
    out = {}
    for cid, (rid, _) in V_CAD_CHECKS.items():
        if cid == "V-CAD-5":
            out[cid] = "FAIL" if blocking & UNREALISED_CLASS_CODES else "PASS"
        elif cid == "V-CAD-4":
            out[cid] = "FAIL" if blocking & XREF_CODES else "PASS"
        elif rid is None:
            out[cid] = "RECORDED"
        else:
            out[cid] = req.get(rid, "NOT_EVALUATED")
    return out


def region_release(result: ProfileResult) -> str:
    if FR.FINAL_MEASUREMENT in result.eligible_uses:
        return "FINAL"
    if FR.PREVIEW_MEASUREMENT in result.eligible_uses:
        return "PREVIEW"
    return "BLOCKED"


def source_profile_release(profile: str, request: str, checks: dict | None = None, profile_implemented: bool = True,
                           bound_px: float | None = None, mm_per_px: float | None = None,
                           item_tolerance_mm: float | None = None) -> dict:
    """Release a source profile permits for a request (R8.0 MT-44..46). FINAL only from an
    implemented, approved CAD profile whose every check passes; vector-PDF and raster
    profiles are not production-approved, so their ceiling is PREVIEW."""
    approved = {"CAD_PROFILE": True, "VECTOR_PDF_PROFILE": False, "RASTER_PDF_PROFILE": False}
    fails = sorted(k for k, v in (checks or {}).items() if v != "PASS")
    if bound_px is not None and mm_per_px is not None and item_tolerance_mm is not None \
            and bound_px * mm_per_px > item_tolerance_mm:
        fails.append("RASTER_BOUND_EXCEEDS_ITEM_TOLERANCE")
    final_ok = approved.get(profile, False) and profile_implemented and not fails
    release = request if (request != "FINAL" or final_ok) else "PREVIEW"
    return {"profile": profile, "request": request, "release": release, "failed_checks": fails,
            "profile_approved": approved.get(profile, False) and profile_implemented}
