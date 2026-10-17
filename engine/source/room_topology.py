"""TS01 - ROOM / SPACE TOPOLOGY METHOD on CANONICAL_MEASUREMENT_INPUT (R8.8, SHADOW).

    canonical input --validate(TS01 contract)--> COMPLETE
        --> geometry role admission (geometry_role)          only positively admitted parts bound a site
        --> opening closures from proven doors (topology)     never inferred for an open passage
        --> certified topology (topology + topology_policy)   two builds, eps_n and eps_r
        --> sites with labels, contents, issues, status
        --> independent GEOS cross-check (topology_crosscheck)  a straight-edged site GEOS cannot reproduce
                                                                 (area + boundary provenance) -> REVIEW_REQUIRED

A method-input contract (canonical_input.MethodContract) declares what TS01 consumes; any declared field missing,
duplicated, cross-revision or with unresolved visibility -> METHOD_INPUT_INCOMPLETE and no sites at all.

Project-agnostic; stdlib only (the cross-check imports shapely lazily).
"""

from __future__ import annotations

from collections import defaultdict

from . import canonical_input as CI
from . import geometry_role as GR
from . import wall_bands as WB
from . import owner_claims as OC
from . import region_membership as RM
from . import role_authority as RA
from . import text_role as TX
from . import semantic_zones as SZ
from . import topology as T
from . import topology_closures as TC
from . import topology_crosscheck as XC
from . import topology_policy as TP

TS01 = CI.MethodContract(
    method_id="TS01_CERTIFIED_ROOM_TOPOLOGY",
    version="1",
    input_fields=("revision", "region_id", "frame_id", "unit_native_to_mm", "unit_claim_id"),
    part_fields=("source_revision_id", "source_handle", "instance_path", "block_identity", "source_part_id",
                 "part_index", "layer", "visibility", "curve_kind", "geometry"),
    text_fields=("source_revision_id", "text_identity", "source_handle", "instance_path", "block_identity",
                 "text_value", "world_placement", "visibility"),
    dimension_fields=(),
    accepted_part_kinds=("SEGMENT", "ARC", "CIRCLE", "ELLIPTICAL_ARC"),
    declared_exclusions={},
    visibility_relevant=True,
    region_review_blocks=True,
    hidden_excluded=True,
    evidence={"accepted_part_kinds": "ELLIPTICAL_ARC is accepted as INPUT: it is role-admitted like any part; a "
                                     "boundary-role ellipse is BOUNDARY_CURVE_UNSUPPORTED and blocks the sites it "
                                     "touches; an ellipse in a proven opening symbol is excluded by role",
              "dimension_fields": "TS01 reads no dimension record"},
)


def max_abs_coordinate(parts) -> float:
    """The numeric tolerance's coordinate magnitude from the FULL exact extent of every part (both segment end
    points, arc / circle / ellipse extrema), never from whichever values sit in tuple positions 0 and 1 (R8.9)."""
    m = 1.0
    for p in parts:
        b = RM.exact_bbox(p.kind, p.geometry)
        if b is not None:
            m = max(m, *(abs(v) for v in b))
    return m


def _occ(rec, assemblies=frozenset()):
    return GR._occurrence(rec, assemblies)


LINEAR = ("SEGMENT", "ARC", "CIRCLE")


def topology_inputs(inp: CI.CanonicalMeasurementInput, *, frame_insert, eps_n, eps_r=None, claims=(),
                    occurrence_claims=None, inferred_doors=None):
    """(items, probes, labels, roles result, closures, opening status, symbol probes per door) - deterministic.

    R8.9 role authority (role_authority): occurrence contexts (building assemblies from positive evidence), source-
    scoped role claims, boundary authority grades (an admitted line touching no other boundary is NOT admitted:
    UNCONNECTED_BOUNDARY_CANDIDATE, blocking), and the separator candidates for the consequence check (stored in
    the roles result)."""
    adm = GR.admit(inp, frame_insert=frame_insert, eps=eps_n)
    troles = TX.classify(inp, frame_insert=frame_insert, claims=claims)
    ctx = RA.occurrence_contexts(inp, adm, frame_insert, occurrence_claims, text_roles=troles, eps=eps_n)
    assemblies = frozenset(o for o, v in ctx.items() if v["context"] == RA.BUILDING_ASSEMBLY)
    if assemblies:
        adm = GR.admit(inp, frame_insert=frame_insert, eps=eps_n, assemblies=assemblies)
    roles, claim_rec = RA.apply_claims(inp, adm["roles"], claims)
    adm["roles"], adm["claims"], adm["occurrence_contexts"] = roles, claim_rec, ctx
    if inferred_doors:                     # A2: door-motif occurrences (entity_role_inference), never by name
        adm["doors"] = dict(adm["doors"])
        adm["inferred_doors"] = {}
        for o, sig in sorted(inferred_doors.items()):
            keys = [p.identity.key for p in inp.parts if p.visibility == CI.VISIBLE and _occ(p, assemblies) == o]
            if o in adm["doors"] or not keys or any(roles[k].role != GR.OPENING_SYMBOL for k in keys
                                                    if k == sig["swing_part"]):
                adm["inferred_doors"][o] = "NOT_ADMITTED (already a door, absent, or its swing is not OPENING_SYMBOL)"
                continue
            adm["doors"][o] = sig
            adm["inferred_doors"][o] = "ADMITTED"
    items, probes, door_probes, cands = [], [], defaultdict(list), []
    for p in sorted(inp.parts, key=lambda q: q.identity.key or ""):
        if p.visibility != CI.VISIBLE:
            continue
        a = roles[p.identity.key]
        if a.role in GR.TOPOLOGY_ADMITTED and p.kind in LINEAR:
            items.append(T.BoundaryItem(p.identity.key, p.kind, tuple(p.geometry), a.role))
            continue
        pb = T.Probe(p.identity.key, p.kind, tuple(p.geometry), a.role, _occ(p, assemblies))
        probes.append(pb)
        if a.role == GR.OPENING_SYMBOL:
            door_probes[_occ(p, assemblies)].append(pb)
        rule = a.rule_id.split("/")[0]
        if p.kind in LINEAR and (rule in RA.LAYER_ONLY_EXCLUSION_RULES or a.role in GR.TOPOLOGY_BLOCKING):
            cands.append((T.BoundaryItem(p.identity.key, p.kind, tuple(p.geometry), a.role),
                          "UNKNOWN" if a.role in GR.TOPOLOGY_BLOCKING else rule))
    grades = RA.grade_boundaries(items, eps_r) if eps_r else {}
    unconnected = [it for it in items if grades.get(it.source_id, {}).get("grade") == RA.CANDIDATE]
    if unconnected:
        drop = {it.source_id for it in unconnected}
        items = [it for it in items if it.source_id not in drop]
        for it in unconnected:
            probes.append(T.Probe(it.source_id, it.kind, it.geometry, RA.UNCONNECTED_BOUNDARY_CANDIDATE,
                                  "E" + it.source_id))
            cands.append((T.BoundaryItem(it.source_id, it.kind, it.geometry, RA.UNCONNECTED_BOUNDARY_CANDIDATE),
                          "UNKNOWN"))
        probes.sort(key=lambda z: z.source_id)
    adm["near_miss_pool"] = [c for c in cands if c[0].kind == "SEGMENT"
                             and (c[1] == "UNKNOWN" or c[1] in RA.PRESENTATION_EXCLUSION_RULES)]
    if eps_r:                                     # excluded linework counts only where it bridges the network
        cands = [c for c in cands if c[1] == "UNKNOWN"] + \
            RA.bridging_subset([c for c in cands if c[1] != "UNKNOWN"], items, eps_r)
    adm["grades"], adm["separator_candidates"] = grades, cands
    adm["semantic_candidates"] = [T.BoundaryItem(p.identity.key, p.kind, tuple(p.geometry), GR.SEMANTIC_BOUNDARY)
                                  for p in sorted(inp.parts, key=lambda q: q.identity.key or "")
                                  if p.visibility == CI.VISIBLE and p.kind in LINEAR
                                  and roles[p.identity.key].role == GR.SEMANTIC_BOUNDARY]
    closures, status = T.opening_closures(adm["doors"], items, eps_n)
    adm["door_audit"] = T.opening_audit(adm["doors"], items, eps_n)
    e_r = eps_r if eps_r else TP.eps_authored(inp.unit_native_to_mm)
    g_closures, g_status, g_open = T.glazing_closures(items, eps_n, e_r) if e_r else ([], {}, {})
    closures = closures + g_closures
    status = dict(status)
    adm["glazing"] = g_status
    adm["glazed_openings"] = g_open
    adm["text_roles"] = troles
    placed = [t for t in sorted(inp.texts, key=lambda q: q.identity.key or "")
              if t.visibility == CI.VISIBLE and t.value and t.x is not None and t.y is not None]
    labels = [T.LabelText(t.identity.key, _occ(t, assemblies), t.value, t.x, t.y) for t in placed
              if troles[t.identity.key].role == TX.ROOM_LABEL_ESTABLISHED]
    adm["unresolved_texts"] = [T.LabelText(t.identity.key, _occ(t, assemblies), t.value, t.x, t.y) for t in placed
                               if troles[t.identity.key].role in TX.UNRESOLVED]
    return items, probes, labels, adm, closures, status, door_probes


UNREALISED_CODES = ("UNHANDLED", "CUSTOM_CLASS", "PROXY", "SKIPPED", "UNSUPPORTED", "UNSUPPORTED_FRAME",
                    "XREF_CONTENT_NOT_IN_SOURCE", "XREF_NOT_RESOLVED", "XREF_UNLOADED", "MISSING_BLOCK_DEFINITION",
                    "NESTING_LIMIT", "UNVERIFIED_FOR_QTO_USE")
UNREALISED_BOUNDARY_LAYER = "UNREALISED_ENTITY_ON_BOUNDARY_LAYER"
UNREALISED_IN_SITE = "UNREALISED_ENTITY_POSSIBLY_IN_SITE"


UNREALISED_REVIEW_REGION = "REGION_REVIEW_REQUIRED"
OCCURRENCE_REVIEW = "OCCURRENCE_REVIEW_REQUIRED"


def _disjoint(a, b):
    return a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]


def unrealised_accounting(unrealised, inp, res, frame_insert, occurrence_contexts=None, xref_claims=()):
    """Source entities the route could not realise (custom / proxy / unhandled / xref content / carried fills) have
    no placed geometry, so the topology never sees them. R8.9: they are excluded ONLY on POSITIVE evidence; the
    absence of realised peers on the same layer proves nothing about where an unrealised entity is.

    Positive evidence, in order:
      IN_SHEET_FRAME_OCCURRENCE          its top-level occurrence is the region's sheet-frame occurrence
      PRESENTATION_OCCURRENCE            its top-level occurrence is an established presentation / frame occurrence
      PLACEMENT (u["extent"])            its own source placement (e.g. the ACIS body's vertices and B-spline
                                         control points through the body transform - convex-hull bound) is
                                         OUTSIDE the region, or meets no bounded site, or meets these sites
      OCCURRENCE_FULLY_OUTSIDE           every realised record of its occurrence is exactly outside the region
                                         (occurrence-level evidence, recorded as such)
    Otherwise it is LOCALISED as far as the source structure allows and blocks there:
      wall / column / glazing layer or unknown layer   -> the whole input (a boundary may be missing)
      inside an occurrence present in the region       -> OCCURRENCE_REVIEW_REQUIRED on the sites that occurrence
                                                          touches (or the whole input if it touches none)
      model space / occurrence not localisable          -> REGION_REVIEW_REQUIRED (the whole input)

    R8.10: a MISSING XREF occurrence (content not in the source) is classified by owner_claims.xref_state into the
    four-state model: proven outside by its own placement, owner-confirmed non-contributing to THIS region (an
    occurrence-scoped reviewed claim), or XREF_MISSING_POTENTIALLY_CONTRIBUTING (blocks the input). A cleared
    occurrence stays in `recorded` (provenance is never deleted)."""
    occurrence_contexts = occurrence_contexts or {}
    out = {"blocking_input": [], "site_issues": defaultdict(list), "recorded": []}
    occ_in = {(p.identity.instance_handles or ())[0] for p in inp.parts if p.identity.instance_handles}
    outside_occ = set(inp.notes.get("occurrences_fully_outside", ()))
    bounds = inp.notes.get("clip_bounds")
    occ_sites = defaultdict(set)
    for p in inp.parts:
        top = (p.identity.instance_handles or (None,))[0]
        if top is not None:
            occ_sites[top] |= set(res["probe_sites"].get(p.identity.key, ()))
            for s_ in res["sites"]:
                if p.identity.key in s_["boundary_source_ids"]:
                    occ_sites[top].add(s_["site_id"])
    sites = res["sites"]
    for u in sorted(unrealised, key=lambda z: (z["obs_id"] or "", z["code"])):
        if u["code"] not in UNREALISED_CODES:
            continue
        path = tuple(u.get("path") or ())
        top = path[0] if path else None
        ctx = occurrence_contexts.get(top, {}).get("context") if top else None
        ext = u.get("extent")
        if top is not None and frame_insert is not None and top == frame_insert:
            out["recorded"].append(dict(u, disposition="IN_SHEET_FRAME_OCCURRENCE"))
            continue
        if ctx in (RA.SHEET_FRAME, RA.PRESENTATION):
            out["recorded"].append(dict(u, disposition="PRESENTATION_OCCURRENCE"))
            continue
        if ext is not None:
            if bounds is not None and _disjoint(ext, bounds):
                out["recorded"].append(dict(u, disposition=OC.XREF_MISSING_BUT_PROVEN_OUTSIDE_REGION
                                            if u["code"] in OC.XREF_CODES
                                            else "OUTSIDE_SELECTED_MEASUREMENT_REGION_BY_PLACEMENT"))
                continue
            hit = sorted(s_["site_id"] for s_ in sites if not _disjoint(ext, s_["bbox"]))
            if not hit:
                out["recorded"].append(dict(u, disposition="NOT_IN_ANY_BOUNDED_SITE_BY_PLACEMENT"))
                continue
            for sid in hit:
                out["site_issues"][sid].append(u["obs_id"])
            out["recorded"].append(dict(u, disposition=UNREALISED_IN_SITE + "_BY_PLACEMENT", sites=hit))
            continue
        if top is not None and top in outside_occ and top not in occ_in:
            out["recorded"].append(dict(u, disposition="OUTSIDE_REGION_BY_OCCURRENCE",
                                        strength="OCCURRENCE_LEVEL: every realised record of the occurrence is "
                                                 "exactly outside; the unrealised child's own extent is unknown"))
            continue
        if u["code"] in OC.XREF_CODES:
            st, cid, why = OC.xref_state(u, xref_claims, inp)
            if st == OC.XREF_MISSING_OWNER_CONFIRMED_NONCONTRIBUTING:
                out["recorded"].append(dict(u, disposition=st, claim=cid))
            else:
                out["blocking_input"].append(dict(u, disposition=st, why=why))
            continue
        lr = GR.layer_role(u.get("layer"))
        if u.get("layer") is None:
            out["blocking_input"].append(dict(u, disposition="UNREALISED_ENTITY_LAYER_UNKNOWN"))
            continue
        if lr in GR.BOUNDARY_LAYER_ROLES:
            out["blocking_input"].append(dict(u, disposition=UNREALISED_BOUNDARY_LAYER))
            continue
        if top is not None and top in occ_in and occ_sites.get(top):
            for sid in sorted(occ_sites[top]):
                out["site_issues"][sid].append(u["obs_id"])
            out["recorded"].append(dict(u, disposition=OCCURRENCE_REVIEW, sites=sorted(occ_sites[top])))
            continue
        out["blocking_input"].append(dict(u, disposition=UNREALISED_REVIEW_REGION,
                                          why="no positive evidence of its placement: absence of realised peers "
                                              "on its layer is not evidence"))
    return out


PHYSICAL_ISSUES = (T.TOLERANCE_SENSITIVE, T.ZERO_WIDTH_SLIVER, T.TOPOLOGY_ROLE_UNRESOLVED, T.OPENING_CLOSURE_UNRESOLVED,
                   T.SITE_ID_COLLISION, XC.GEOS_CROSSCHECK_DISAGREES, RA.ROLE_CONFLICT_SEPARATOR,
                   "UNREALISED_ENTITY_ON_BOUNDARY_LAYER", "UNREALISED_ENTITY_POSSIBLY_IN_SITE",
                   "OCCURRENCE_REVIEW_REQUIRED", "REGION_REVIEW_REQUIRED", "UNREALISED_ENTITY_LAYER_UNKNOWN",
                   "XREF_MISSING_POTENTIALLY_CONTRIBUTING", RA.NEAR_MISS_BOUNDARY_GAP, RA.NETWORK_ROLE_CONFLICT)
SEMANTIC_ISSUES = (T.MULTIPLE_SEMANTIC_LABELS, T.LABEL_ON_BOUNDARY, T.LABEL_OCCURRENCE_SPLIT,
                   "TEXT_ROLE_UNRESOLVED_IN_SITE")


def classify_issues(site) -> None:
    """R8.9: physical (topology) vs semantic (labels) vs trade (objects inside a stable site) issues. The overall
    `status` keeps its R8.8 meaning (CERTIFIED only with no issue at all)."""
    iss = set(site["issues"])
    site["physical_issues"] = sorted(iss & set(PHYSICAL_ISSUES))
    site["semantic_issues"] = sorted(iss & set(SEMANTIC_ISSUES))
    site["trade_issues"] = sorted(iss - set(PHYSICAL_ISSUES) - set(SEMANTIC_ISSUES))
    site["physical_status"] = T.CERTIFIED if not site["physical_issues"] else T.REVIEW_REQUIRED


def consequences(res, items, adm, labels, tol, unit_native_to_mm=None) -> None:
    """R8.9 consequence check (role_authority.separator_analysis), run SEPARATELY for layer-only exclusions and for
    unknown geometry so each effect is attributed to its own origin; folded into the site issues, plus the site's
    weakest boundary authority grade."""
    cands = adm.get("separator_candidates", [])
    groups = {"exclusion": [c for c in cands if c[1] != "UNKNOWN"], "unknown": [c for c in cands if c[1] == "UNKNOWN"]}
    sep = {g: RA.separator_analysis(res, items, cs, eps_n=tol["eps_n"], eps_r=tol["eps_r"], labels=labels)
           for g, cs in groups.items()}
    res["separators"] = sep
    nm = {"band_native": None, "near_misses": [], "state": "NOT_RUN: no unit, no physical review band"}
    if unit_native_to_mm:
        nm = RA.near_miss_analysis(res, items, adm.get("near_miss_pool", []), eps_n=tol["eps_n"], eps_r=tol["eps_r"],
                                   band=RA.NEAR_MISS_REVIEW_BAND_MM / float(unit_native_to_mm), labels=labels)
    res["near_misses"] = nm
    nm_sites = defaultdict(list)
    for m in nm["near_misses"]:
        for sid, e in m["sites"].items():
            if e["effect"] == "CHANGES_AREA" or not m["admitted"]:   # admitted gap between labelled rooms: R8.8
                nm_sites[sid].append({"source": m["source"], "origin": m["origin"], "effect": e["effect"],
                                      "gaps_native": m["gaps_native"]})
    unknown_ids = {c.source_id for c, _ in groups["unknown"]}
    grades = adm.get("grades", {})
    for s_ in res["sites"]:
        ex, un = sep["exclusion"]["sites"].get(s_["site_id"]), sep["unknown"]["sites"].get(s_["site_id"])
        iss = set(s_["issues"])
        if ex:
            issue, level = RA.consequence_issue(ex)
            if level == "NOTE":
                s_.setdefault("trade_notes", []).append(issue)
            elif issue:
                iss.add(issue)
        blocked = set(s_.get("blocked_by", []))
        if blocked and blocked <= unknown_ids and (un is None or un["effect"] == "NONE"):
            # every blocking source is linear geometry that cannot change this site: the PHYSICAL site stands;
            # what the object is remains a trade question
            iss = (iss - {T.TOPOLOGY_ROLE_UNRESOLVED}) | {RA.UNKNOWN_OBJECT_IN_SITE}
        if s_["site_id"] in nm_sites:
            iss.add(RA.NEAR_MISS_BOUNDARY_GAP)
            s_["near_miss"] = nm_sites[s_["site_id"]]
        s_["issues"] = sorted(iss)
        s_["consequence"] = {g: {"effect": e["effect"], "sources": e["sources"], "origins": e["origins"]}
                             for g, e in (("exclusion", ex), ("unknown", un)) if e}
        g = [grades[x]["grade"] for x in s_["boundary_source_ids"] if x in grades]
        s_["authority_grade"] = min(g, key=lambda z: RA.GRADE_ORDER[z]) if g else None
        s_["status"] = T.CERTIFIED if not s_["issues"] else T.REVIEW_REQUIRED


def passage_sites(passages, res, unit_native_to_mm):
    """OPEN_PASSAGE_SITE records with the sites on both sides of the strip (it stays physically connected)."""
    out = []
    arr, sites = res["_arr"], res["sites"]
    for p in passages:
        (a, b, c, d) = p["polygon"]
        w = p["wall_thickness"]
        mid_long = [((a[0] + d[0]) / 2, (a[1] + d[1]) / 2), ((b[0] + c[0]) / 2, (b[1] + c[1]) / 2)]
        cen = ((a[0] + c[0]) / 2, (a[1] + c[1]) / 2)
        sides = []
        for m in mid_long:
            vx, vy = m[0] - cen[0], m[1] - cen[1]
            n = (vx * vx + vy * vy) ** 0.5 or 1.0
            q = (m[0] + vx / n * w / 2, m[1] + vy / n * w / 2)
            sides.append(T.locate(arr, sites, q, 0.0)[0])
        inside, _ = T.locate(arr, sites, cen, 0.0)
        out.append(dict(p, area_m2=p["area_native"] * unit_native_to_mm ** 2 / 1e6,
                        width_mm=p["width"] * unit_native_to_mm, thickness_mm=w * unit_native_to_mm,
                        strip_in_site=inside, adjacent_sites=sides,
                        reveals={"jambs": p["jamb_faces"], "soffit": "the strip footprint (only if a head exists)",
                                 "double_count_guard": "jamb faces and soffit are opening surfaces: never also a room "
                                                       "wall perimeter or a ceiling area"}))
    return out


def run(inp: CI.CanonicalMeasurementInput, *, frame_insert, expected_revision_id=None, selected_region_id=None,
        contract=TS01, unrealised=None, claims=(), occurrence_claims=None, part_claims=(), xref_claims=(),
        closure_policy=None, provenance=None, inferred_doors=None) -> dict:
    v = CI.validate(inp, contract, expected_revision_id=expected_revision_id, selected_region_id=selected_region_id)
    out = {"method_id": contract.method_id, "validation": v, "state": v["state"], "sites": None}
    if v["state"] != CI.COMPLETE:
        return out
    m = max_abs_coordinate(inp.parts)
    tol = TP.tolerances(m, inp.unit_native_to_mm)
    if not tol["valid"]:
        out.update(state=T.UNIT_UNRESOLVED, tolerances=tol)
        return out
    pclaims, prec = OC.role_claims(part_claims, inp)           # R8.10: part-scoped claims -> role authority only
    items, probes, labels, adm, closures, status, door_probes = topology_inputs(
        inp, frame_insert=frame_insert, eps_n=tol["eps_n"], eps_r=tol["eps_r"], claims=tuple(claims) + tuple(pclaims),
        occurrence_claims=occurrence_claims, inferred_doors=inferred_doors)
    wb, tcs = None, []
    if closure_policy is not None:                      # R8.11: wall bands + zero-material wall-end closures
        if closure_policy != TC.POLICY_ID:
            raise ValueError(f"unknown closure policy {closure_policy!r}")
        pool = [(T.BoundaryItem(p.source_id, p.kind, p.geometry, p.role), p.role) for p in probes
                if p.kind == "SEGMENT"]
        wb = WB.detect(items, eps_r=tol["eps_r"], band_review=RA.NEAR_MISS_REVIEW_BAND_MM / inp.unit_native_to_mm,
                       revision_id=inp.revision.revision_id, region_id=inp.region_id, labels=labels,
                       texts=inp.texts, unit_native_to_mm=inp.unit_native_to_mm, cap_pool=pool,
                       extra_targets=closures, eps_n=tol["eps_n"],
                       physical_authority={k for c in prec for k in c["applied_parts"]})
        tcs = TC.derive(wb["bands"], revision_id=inp.revision.revision_id, region_id=inp.region_id)
        TC.diagnose(items, closures, tcs, labels, wb["bands"], eps_n=tol["eps_n"], eps_r=tol["eps_r"])
        closures = closures + [c.as_item() for c in tcs if c.release == TC.AUTHORISED_FOR_SHADOW]
    res = T.analyse(items + closures, probes, labels, revision_id=inp.revision.revision_id, region_id=inp.region_id,
                    unit_native_to_mm=inp.unit_native_to_mm, max_abs_coordinate=m,
                    blocking_roles=GR.TOPOLOGY_BLOCKING + (RA.UNCONNECTED_BOUNDARY_CANDIDATE,), opening_status=status,
                    opening_symbol_occurrences=door_probes, glazed_openings=adm["glazed_openings"])
    consequences(res, items + closures, adm, labels, tol, inp.unit_native_to_mm)
    net = RA.network_review(res, items, adm.get("grades", {}), adm["roles"], inp.texts, eps_r=tol["eps_r"],
                            unit_native_to_mm=inp.unit_native_to_mm,
                            paired_faces=set(wb["face_ids_in_bands"]) if wb else ())
    res["network_review"] = net
    for sid in sorted({x for v in net.values() if v["state"] == RA.NETWORK_ROLE_CONFLICT for x in v["sites"]}):
        s_ = next(z for z in res["sites"] if z["site_id"] == sid)
        s_["issues"] = sorted(set(s_["issues"]) | {RA.NETWORK_ROLE_CONFLICT})
        s_["status"] = T.REVIEW_REQUIRED
    for lt in adm["unresolved_texts"]:                 # a text of unresolved role inside a site: semantic review
        sid, _ = T.locate(res["_arr"], res["sites"], (lt.x, lt.y), 0.0)
        if sid is not None:
            s_ = next(z for z in res["sites"] if z["site_id"] == sid)
            s_["issues"] = sorted(set(s_["issues"]) | {TX.TEXT_ROLE_UNRESOLVED_IN_SITE})
            s_.setdefault("unresolved_texts", []).append({"text": lt.text_id, "value": lt.value})
            s_["status"] = T.REVIEW_REQUIRED
    xc = XC.check(res, items + closures, tol["eps_n"])
    for s_ in res["sites"]:
        st = xc["per_site"].get(s_["site_id"], {}).get("state", xc["state"])
        s_["crosscheck"] = st
        if st == XC.DISAGREES:
            s_["issues"] = sorted(set(s_["issues"]) | {XC.GEOS_CROSSCHECK_DISAGREES})
            s_["status"] = T.REVIEW_REQUIRED
    res["crosscheck"] = {k: v for k, v in xc.items() if k != "per_site"}
    res["crosscheck"]["disagreements"] = {k: v for k, v in sorted(xc["per_site"].items()) if v["state"] == XC.DISAGREES}
    res["crosscheck"]["inconclusive"] = {k: v for k, v in sorted(xc["per_site"].items())
                                         if v["state"] in (XC.PHASE_SENSITIVE_INCONCLUSIVE, XC.CHECK_INPUT_INVALID)}
    if unrealised is not None:
        acc = unrealised_accounting(unrealised, inp, res, frame_insert, adm.get("occurrence_contexts"), xref_claims)
        res["unrealised"] = {"blocking_input": acc["blocking_input"], "recorded": acc["recorded"],
                             "sites": {k: sorted(v) for k, v in acc["site_issues"].items()}}
        block = sorted({b["disposition"] for b in acc["blocking_input"]})
        for s_ in res["sites"]:
            add = set(block)
            if s_["site_id"] in acc["site_issues"]:
                add.add(UNREALISED_IN_SITE)
            if add:
                s_["issues"] = sorted(set(s_["issues"]) | add)
                s_["status"] = T.REVIEW_REQUIRED
    else:
        res["unrealised"] = {"state": "NOT_SUPPLIED: the caller did not account for unrealised source entities"}
    for s_ in res["sites"]:
        classify_issues(s_)
    obst = SZ.obstacle_interiors(res, adm["roles"])
    for s_ in res["sites"]:
        if s_["site_id"] in obst:
            s_["kind"] = "OBSTACLE_INTERIOR"
            s_["obstacle"] = obst[s_["site_id"]]
    res["semantic"] = SZ.build(res, items + closures, adm["semantic_candidates"], labels, eps_n=tol["eps_n"],
                               eps_r=tol["eps_r"])
    if wb is not None:
        res["wall_bands"] = {"policy": WB.policy_record(), "bands": [vars(b) for b in wb["bands"]],
                             "spans": wb["spans"], "chains": wb["chains"], "chain_breaks": wb["chain_breaks"],
                             "unsupported_runs": wb["unsupported_runs"],
                             "chain_id_collisions": wb["chain_id_collisions"],
                             "isolated_loops": wb["isolated_loops"],
                             "physical_authority_entities": wb["physical_authority_entities"]}
        res["topology_closures"] = {"policy": TC.policy_record(), "closures": [c.record() for c in tcs]}
        res["passages"] = passage_sites(wb["passages"], res, inp.unit_native_to_mm)
    res["roles"] = adm
    res["owner_claims"] = {"part_claims": prec, "xref_claims": [f"{c.claim_id}@v{c.version}" for c in xref_claims],
                           "evidence_version": OC.evidence_version(part_claims, xref_claims, claims)}
    res["openings"] = status
    res["closures"] = closures
    res["counts"] = {"admitted_boundary": len(items), "closures": len(closures), "probes": len(probes),
                     "labels": len(labels)}
    out.update(res)
    out["state"] = res["state"]
    from . import run_manifest as RM                       # R8.11: every result names its exact inputs
    out["run_manifest"] = RM.build(inp, out, method_id=contract.method_id, contract_version=contract.version,
                                   closure_policy=closure_policy, provenance=provenance)
    return out
