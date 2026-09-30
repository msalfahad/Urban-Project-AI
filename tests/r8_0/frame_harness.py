"""R8.3 test-side adapter: the R8.0 frame / unit contract schema -> PRODUCTION engine/source/frame.py
and cad_profile.py. A reviewed change, like k1_harness.py for K1 / reconcile.

The adapter only TRANSLATES the frozen R8.0 input vocabulary into production evidence records
and reads the production result back into the R8.0 field names. It computes no status, applies
no rule and never supplies a value the fixture does not carry. Every translation is listed:

  UNIT_CONTEXT
    header.INSUNITS                   -> frame.declaration_evidence (a DECLARATION)
    GEOMETRY_PLAUSIBILITY suggests U  -> GEOMETRY_PLAUSIBILITY item, value mm(U)   (support only)
    PRINTED_DIMENSION display_mm, geometry_native
                                      -> DIMENSION_DISPLAY, value display_mm / geometry_native
                                         (the display unit is GIVEN in millimetres by the fixture)
    INFERRED_UNIT suggests U          -> CANDIDATE (review CANDIDATE), value mm(U)
    raster {dpi, page_size_in, pixels}-> RASTER_PAGE space: dpi as the DECLARATION (mm per pixel),
                                         page size / pixel count as KNOWN_PLOT_DIMENSION
  FRAMES
    layouts.PAPER.viewports           -> PAPER_SPACE_VIEWPORT regions under a PAPER_LAYOUT unit context
    regions[*].scale_evidence strings -> region-scoped observations WITHOUT a value (a sheet scale
                                         "1:100" is a plot scale, not a model-space local scale)
    regions[*].native_unit_to_mm      -> NATIVE_UNIT evidence scoped to the region (U-1 test)
    scale_text "... 1:A (x.. of plan 1:B)" -> EXPLICIT_SCALE_NOTE, value A / B
    dimlfac + dimensions display/geometry  -> DIMENSION_STYLE, value display / geometry
    force {region: value}             -> an AUTHORISED human claim of that value (role URBAN_QS_LEAD, scoped to
                                         the region): a forced value is at most such a claim (R8.4, V2)
    overrides [{status, by}]          -> FrameRegistry.set_status (always refused)
    accept_enlargement                -> an AGENT candidate with no value
  FRAME_EVIDENCE
    AUTO_DIMENSION                    -> DIMENSION_GEOMETRY (circular with the geometry it measures)
    OVERRIDDEN_DIMENSION_TEXT         -> DIMENSION_DISPLAY in the DOCUMENT_SOURCE family of the drawing
    DWG_GEOMETRY / PDF_PLOT plot_of X -> OTHER_SOURCE_DOCUMENT sharing PRIMITIVE:X
    VECTOR_PAGE / RASTER_RENDER of X  -> OTHER_SOURCE_DOCUMENT sharing PRIMITIVE:X
    claimed_independent               -> ignored (a claim is not lineage)
"""

from __future__ import annotations

import math
import re

from engine.source import cad_profile as P
from engine.source import frame as FR

from .targets import TargetNotImplemented

SHA = "0" * 64
UNIT_MM = {"METRE": 1000.0, "CENTIMETRE": 10.0, "MILLIMETRE": 1.0, "INCH": 25.4, "FOOT": 304.8}
CONFLICT_CODES = {"UNIT_DECLARATION_CONFLICT", "UNIT_EVIDENCE_CONFLICT", "UNIT_PLAUSIBILITY_QUESTION",
                  "REGION_SCALE_CONFLICT", "FRAME_CONFLICT"}


# ---------------------------------------------------------------- UNIT_CONTEXT
def unit_context(header=None, evidence=(), raster=None):
    if raster:
        dpi = raster["dpi"]
        w_in = raster["page_size_in"][0]
        px = raster["pixels"][0]
        ev = [FR.UnitEvidence("DPI", FR.NATIVE_UNIT, FR.UNIT_HEADER_DECLARATION, "PAGE", ("AUTHORED:RASTER:DPI",),
                              25.4 / dpi, producer=FR.DECODER, source_sha256=SHA),
              FR.UnitEvidence("PAGE_SIZE", FR.NATIVE_UNIT, FR.KNOWN_PLOT_DIMENSION, "PAGE", ("AUTHORED:RASTER:PAGE_SIZE",),
                              w_in * 25.4 / px, producer=FR.DECODER, source_sha256=SHA)]
        u = FR.unit_context(SHA, "PAGE", FR.RASTER_PAGE, ev, insunits=None)
        return _unit_out(u, ev)
    ins = (header or {}).get("INSUNITS")
    ev = list(FR.declaration_evidence(ins, "MODEL", SHA)[0])
    for i, e in enumerate(evidence or ()):
        k = e["kind"]
        if k == "GEOMETRY_PLAUSIBILITY":
            ev.append(FR.UnitEvidence(f"P{i}", FR.NATIVE_UNIT, FR.GEOMETRY_PLAUSIBILITY, "MODEL",
                                      (f"PLAUSIBILITY:{i}",), UNIT_MM[e["suggests"]], source_sha256=SHA))
        elif k == "PRINTED_DIMENSION":
            ev.append(FR.UnitEvidence(f"D{i}", FR.NATIVE_UNIT, FR.DIMENSION_DISPLAY, "MODEL",
                                      (f"AUTHORED:{SHA}:DIMENSION:{i}", FR.family_lineage(FR.DIMENSION_DISPLAY, SHA)),
                                      e["display_mm"] / e["geometry_native"], source_sha256=SHA))
        elif k == "INFERRED_UNIT":
            ev.append(FR.UnitEvidence(f"I{i}", FR.NATIVE_UNIT, FR.GEOMETRY_PLAUSIBILITY if e.get("producer") ==
                                      "GEOMETRY_PLAUSIBILITY" else FR.OTHER_SOURCE_DOCUMENT, "MODEL",
                                      (f"INFERENCE:{i}",), UNIT_MM[e["suggests"]], source_sha256=SHA,
                                      producer=FR.ENGINE, review_status=FR.CANDIDATE))
        else:
            raise ValueError(f"no translation for R8.0 evidence kind {k!r}")
    u = FR.unit_context(SHA, "MODEL", FR.MODEL_SPACE, ev, insunits=ins)
    return _unit_out(u, ev)


def _unit_out(u, ev):
    codes = {f.code for f in u.findings}
    applied = u.native_to_mm
    inferred = [e for e in ev if e.review_status == FR.CANDIDATE]
    return {"status": u.status, "final_allowed": FR.FINAL_MEASUREMENT in u.allowed_use,
            "conflict": u.status == FR.CONFLICT or bool(codes & CONFLICT_CODES),
            "native_unit_to_mm": u.native_to_mm,
            "plausibility_counted_toward_verified": any(e.kind == FR.GEOMETRY_PLAUSIBILITY and e.evidence_id in u.evidence_ids
                                                        for e in ev),
            "inferred_unit_applied": any(applied is not None and FR._agree(applied, e.derived_value) and
                                         not any(FR._agree(applied, d.derived_value) for d in ev
                                                 if d.kind == FR.UNIT_HEADER_DECLARATION)
                                         for e in inferred),
            "findings": sorted(codes)}


# ---------------------------------------------------------------- FRAMES
def _scale_from_text(t):
    nums = [int(x) for x in re.findall(r"1\s*:\s*(\d+)", t)]
    return nums[0] / nums[1] if len(nums) >= 2 else None


def frames(source, measure_in=None, overrides=None, force=None, accept_enlargement=False):
    if source.get("kind") == "VECTOR_PDF":
        return _pdf(source)
    reg = FR.FrameRegistry(SHA)
    model = reg.add_unit_context(FR.unit_context(SHA, "MODEL", FR.MODEL_SPACE, [], insunits=None))
    out, regions = {}, {}
    if "layouts" in source:
        regions["MODEL"] = FR.region_transform(model, "MODEL", FR.MODEL_SPACE_PLAN)
        for lname, lay in source["layouts"].items():
            if lname == "MODEL":
                continue
            lu = reg.add_unit_context(FR.unit_context(SHA, lname, FR.PAPER_LAYOUT, [], insunits=None))
            for vp in lay.get("viewports", ()):
                ev = [FR.UnitEvidence(f"{vp['id']}:SCALE", FR.REGION_SCALE, FR.PAPERSPACE_VIEWPORT_SCALE, vp["id"],
                                      (f"AUTHORED:{SHA}:VIEWPORT:{vp['id']}",), vp["scale"], producer=FR.DECODER,
                                      source_sha256=SHA)]
                regions[vp["id"]] = FR.region_transform(lu, vp["id"], FR.PAPER_SPACE_VIEWPORT, ev, parent_region_id="MODEL")
    unit_rejections = []
    for r in source.get("regions", ()):
        rid = r["id"]
        ev = []
        if "native_unit_to_mm" in r:
            bad = FR.UnitEvidence(f"{rid}:UNIT", FR.NATIVE_UNIT, FR.EXPLICIT_UNIT_NOTE, rid, (f"AUTHORED:{rid}",),
                                  r["native_unit_to_mm"], source_sha256=SHA)
            probe = FR.unit_context(SHA, "MODEL", FR.MODEL_SPACE, [bad], insunits=None, unit_context_id="UC:probe")
            unit_rejections += [f for f in probe.findings if f.code == "UNIT_REDEFINITION_REJECTED"]
        for j, token in enumerate(r.get("scale_evidence", ())):
            kind = FR.EXPLICIT_SCALE_NOTE if token.startswith("SCALE_TEXT") else FR.DIMENSION_STYLE
            ev.append(FR.UnitEvidence(f"{rid}:{token}", FR.REGION_SCALE, kind, rid, (f"AUTHORED:{rid}:{token}",),
                                      None, observed_value=token, source_sha256=SHA))
        if "scale_text" in r:
            v = _scale_from_text(r["scale_text"])
            ev.append(FR.UnitEvidence(f"{rid}:SCALE_TEXT", FR.REGION_SCALE, FR.EXPLICIT_SCALE_NOTE, rid,
                                      (f"AUTHORED:{SHA}:TEXT:{rid}", FR.family_lineage(FR.EXPLICIT_SCALE_NOTE, SHA)), v,
                                      observed_value=r["scale_text"], source_sha256=SHA))
        if "dimlfac" in r and r.get("dimensions"):
            d = r["dimensions"][0]
            ev.append(FR.UnitEvidence(f"{rid}:DIMSTYLE", FR.REGION_SCALE, FR.DIMENSION_STYLE, rid,
                                      (f"AUTHORED:{SHA}:DIMSTYLE:{rid}", FR.family_lineage(FR.DIMENSION_STYLE, SHA)),
                                      d["display"] / d["geometry_native"], observed_value=r["dimlfac"], source_sha256=SHA))
        if force and rid in force:
            ev.append(FR.human_confirmation(f"{rid}:FORCED", SHA, rid, force[rid]["real_per_presented"],
                                            "FORCED_OVERRIDE", "URBAN_QS_LEAD", "R8.0-MT-24", scope=(rid,),
                                            question=FR.REGION_SCALE))
        if accept_enlargement:
            ev.append(FR.UnitEvidence(f"{rid}:ACCEPTED", FR.REGION_SCALE, FR.EXPLICIT_SCALE_NOTE, rid, ("AGENT:accept",),
                                      None, producer=FR.AGENT, review_status=FR.CANDIDATE, source_sha256=SHA))
        kind = FR.MODEL_SPACE_DETAIL if (r.get("enlarged_geometry") or "scale_text" in r) else FR.MODEL_SPACE_PLAN
        regions[rid] = FR.region_transform(model, rid, kind, ev)
    for rid, rt in regions.items():
        reg.add_region(rt)
        ok, why = FR.measurement_authority(rt.region_kind)
        out[rid] = {"kind": "VIEWPORT_FRAME" if rt.region_kind == FR.PAPER_SPACE_VIEWPORT else "REGION_FRAME",
                    "parent": rt.parent_region_id, "measurement_allowed": ok, "status": rt.status,
                    "real_per_presented": rt.local_scale, "rule": rt.status_reason.split(":")[0],
                    "unit_context": "PARENT" if rt.unit_context_id == model.unit_context_id else rt.unit_context_id,
                    "independently_statused": set(rt.evidence_ids) <= {e for e in rt.evidence_ids if e.startswith(rid)},
                    "status_set_by_agent": False}
    out["frame_count"] = len([r for r in source.get("regions", ())]) or len(regions)
    if measure_in:
        ok, why = FR.measurement_authority(regions[measure_in].region_kind)
        out.update({"refused": not ok, "reason": why})
    if overrides:
        rejected = []
        for o in overrides:
            try:
                reg.set_status(o["region"], o["status"], FR.AGENT if o["by"] == "AGENT" else FR.HUMAN)
                rejected.append(False)
            except FR.FrameStatusError:
                rejected.append(True)
        out["override_rejected"] = all(rejected)
    if unit_rejections:
        out.update({"rejected": True, "rule": "U-1"})
    return out


def _pdf(source):
    u = FR.unit_context(SHA, "PAGE", FR.PDF_PAGE, [
        FR.UnitEvidence("SCALE_BAR", FR.NATIVE_UNIT, FR.SCALE_BAR, "PAGE", (f"AUTHORED:{SHA}:SCALE_BAR",),
                        source["scale_bar"]["label_m"] * 1000.0 / source["scale_bar"]["length_pt"], source_sha256=SHA)],
        insunits=None)
    a = math.radians(source["page_rotation_deg"])
    m = (round(math.cos(a), 12), round(-math.sin(a), 12), 0.0, round(math.sin(a), 12), round(math.cos(a), 12), 0.0)
    rt = FR.region_transform(u, "PAGE", FR.PDF_VECTOR_REGION, matrix=m)
    return {"PAGE": {"rotation_deg": round(math.degrees(rt.rotation_rad)) % 360,
                     "scale_bar_is_evidence": "SCALE_BAR" in u.evidence_ids, "status": u.status}}


# ---------------------------------------------------------------- FRAME_EVIDENCE
def frame_evidence(evidence=None, real_source=None):
    if evidence is None:
        raise TargetNotImplemented("R8.0 MT-33 needs a real source (URBAN_R8_REAL_SOURCE unset)")
    items = []
    for i, e in enumerate(evidence):
        k = e["kind"]
        if k == "AUTO_DIMENSION":
            items.append(FR.UnitEvidence(f"E{i}", FR.NATIVE_UNIT, FR.DIMENSION_GEOMETRY, "MODEL",
                                         (f"AUTHORED:{SHA}:DIMSTYLE:{e['dimstyle']}", f"PRIMITIVE:GEOMETRY:{i}"),
                                         None, source_sha256=SHA))
        elif k == "OVERRIDDEN_DIMENSION_TEXT":
            items.append(FR.UnitEvidence(f"E{i}", FR.NATIVE_UNIT, FR.DIMENSION_DISPLAY, "MODEL",
                                         (f"AUTHORED:{SHA}:DIMENSION_TEXT:{i}", FR.family_lineage(FR.DIMENSION_DISPLAY, SHA)),
                                         None, source_sha256=SHA))
        elif k in ("DWG_GEOMETRY", "VECTOR_PAGE"):
            items.append(FR.UnitEvidence(f"E{i}", FR.NATIVE_UNIT, FR.OTHER_SOURCE_DOCUMENT, "MODEL",
                                         (f"PRIMITIVE:{k}",), None, source_sha256=SHA))
        elif k in ("PDF_PLOT", "RASTER_RENDER"):
            of = e.get("plot_of") or e.get("of")
            items.append(FR.UnitEvidence(f"E{i}", FR.NATIVE_UNIT, FR.OTHER_SOURCE_DOCUMENT, "MODEL",
                                         (f"PRIMITIVE:{of}", f"DOCUMENT:{k}:{i}"), None, source_sha256=SHA))
        else:
            raise ValueError(f"no translation for R8.0 evidence kind {k!r}")
    return FR.independence_report(items, FR.NATIVE_UNIT, SHA)


# ---------------------------------------------------------------- SOURCE_PROFILE
def source_profile(profile, request=None, decode=None, **kw):
    if decode is not None:
        return source_profile_decode(profile, decode)
    return P.source_profile_release(profile, request, **kw)


def source_profile_decode(profile, decode, region_id="MODEL_SPACE"):
    """R8.0 F19 decode form, bound in R8.4 (R8_CONTRACT_SUPERSESSION.json, F19 entry).

    V-CAD-5 is defined in the R8 revised spec, later edition §6a ("no UNHANDLED class on a
    profile-relevant layer of the region"). Translation only: builder decode -> production D1
    -> production K1 -> production census -> production cad_profile.region_class_findings /
    evaluate / v_cad_view. The profile-relevant layers are the layers of the region's measured
    (realised) observations — the one generic rule the spec gives; no layer name is chosen here.
    The frame is a declared-millimetre model space (the fixture carries no unit question)."""
    from engine.source import decoder_pins as PINS
    from engine.source.cad import census
    from .k1_harness import _imports, apply_test_schema_extensions
    if profile != "CAD_PROFILE":
        raise ValueError(profile)
    _, kernel, lm = _imports()
    doc = apply_test_schema_extensions(decode, lm.to_document(decode))
    real = kernel.realise(doc)
    rows = census.capability_register(doc, real)
    measured = {}
    for seg in real.segments:
        measured.setdefault(seg.lineage.obs_id, seg.lineage)
    layers = {lin.layer for lin in measured.values()}
    region_findings = P.region_class_findings(rows, region_id, layers)
    decl, _ = FR.declaration_evidence(4, "MODEL", SHA)
    u = FR.unit_context(SHA, "MODEL", FR.MODEL_SPACE, decl, insunits=4)
    rt = FR.region_transform(u, region_id, FR.MODEL_SPACE_PLAN)
    mf = FR.measurement_frame(u, rt)
    ctx = P.SourceValidationContext(True, PINS.REGISTERED, None)
    method = P.MeasurementMethod("LINEAR_LENGTH", scale_dependent=True)
    results = [P.evaluate(lin.kind, oid, (), method, ctx, mf, u, rt, region_findings=region_findings)
               for oid, lin in sorted(measured.items())]
    views = [P.v_cad_view(r, region_findings) for r in results]
    releases = [P.region_release(r) for r in results]
    worst = min(releases, key=("BLOCKED", "PREVIEW", "FINAL").index) if releases else "BLOCKED"
    out = {cid: ("FAIL" if any(v[cid] == "FAIL" for v in views) else views[0][cid] if views else "NOT_EVALUATED")
           for cid in P.V_CAD_CHECKS}
    out.update({"region_release": worst, "relevant_layers": sorted(layers),
                "region_findings": [f.as_dict() for f in region_findings]})
    return out
