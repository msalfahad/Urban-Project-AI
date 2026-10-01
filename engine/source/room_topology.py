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
from . import region_membership as RM
from . import role_authority as RA
from . import topology as T
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
                    occurrence_claims=None):
    """(items, probes, labels, roles result, closures, opening status, symbol probes per door) - deterministic.

    R8.9 role authority (role_authority): occurrence contexts (building assemblies from positive evidence), source-
    scoped role claims, boundary authority grades (an admitted line touching no other boundary is NOT admitted:
    UNCONNECTED_BOUNDARY_CANDIDATE, blocking), and the separator candidates for the consequence check (stored in
    the roles result)."""
    adm = GR.admit(inp, frame_insert=frame_insert, eps=eps_n)
    ctx = RA.occurrence_contexts(inp, adm, frame_insert, occurrence_claims)
    assemblies = frozenset(o for o, v in ctx.items() if v["context"] == RA.BUILDING_ASSEMBLY)
    if assemblies:
        adm = GR.admit(inp, frame_insert=frame_insert, eps=eps_n, assemblies=assemblies)
    roles, claim_rec = RA.apply_claims(inp, adm["roles"], claims)
    adm["roles"], adm["claims"], adm["occurrence_contexts"] = roles, claim_rec, ctx
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
    if eps_r:                                     # excluded linework counts only where it bridges the network
        cands = [c for c in cands if c[1] == "UNKNOWN"] + \
            RA.bridging_subset([c for c in cands if c[1] != "UNKNOWN"], items, eps_r)
    adm["grades"], adm["separator_candidates"] = grades, cands
    closures, status = T.opening_closures(adm["doors"], items, eps_n)
    e_r = eps_r if eps_r else TP.eps_authored(inp.unit_native_to_mm)
    g_closures, g_status, g_open = T.glazing_closures(items, eps_n, e_r) if e_r else ([], {}, {})
    closures = closures + g_closures
    status = dict(status)
    adm["glazing"] = g_status
    adm["glazed_openings"] = g_open
    labels = [T.LabelText(t.identity.key, _occ(t, assemblies), t.value, t.x, t.y)
              for t in sorted(inp.texts, key=lambda q: q.identity.key or "")
              if t.visibility == CI.VISIBLE and t.value and t.x is not None and t.y is not None]
    return items, probes, labels, adm, closures, status, door_probes


UNREALISED_CODES = ("UNHANDLED", "CUSTOM_CLASS", "PROXY", "SKIPPED", "UNSUPPORTED", "UNSUPPORTED_FRAME",
                    "XREF_CONTENT_NOT_IN_SOURCE", "XREF_NOT_RESOLVED", "XREF_UNLOADED", "MISSING_BLOCK_DEFINITION",
                    "NESTING_LIMIT", "UNVERIFIED_FOR_QTO_USE")
UNREALISED_BOUNDARY_LAYER = "UNREALISED_ENTITY_ON_BOUNDARY_LAYER"
UNREALISED_IN_SITE = "UNREALISED_ENTITY_POSSIBLY_IN_SITE"


def unrealised_accounting(unrealised, inp, res, frame_insert):
    """Source entities the route could not realise (custom / proxy / unhandled / xref content / carried fills) have
    no placed geometry, so the topology never sees them. They are never ignored silently:
      * inside the region's frame occurrence -> they belong to the sheet frame (no room content);
      * on a WALL / COLUMN / GLAZING layer -> the whole input is INCOMPLETE (a boundary may be missing);
      * on a layer whose realised parts touch a bounded site -> every such site gets UNREALISED_IN_SITE (blocking);
      * otherwise -> recorded, with the evidence (no realised part of that layer lies in any bounded site)."""
    out = {"blocking_input": [], "site_issues": defaultdict(list), "recorded": []}
    occ_in = {_occ(p) for p in inp.parts}
    layer_sites = defaultdict(set)
    for p in inp.parts:
        for sid in res["probe_sites"].get(p.identity.key, ()):
            layer_sites[p.layer].add(sid)
    for u in sorted(unrealised, key=lambda z: (z["obs_id"] or "", z["code"])):
        if u["code"] not in UNREALISED_CODES:
            continue
        path = tuple(u.get("path") or ())
        top = ("I" + path[0]) if path else None
        if top is not None and top not in occ_in:
            continue                                            # inside an occurrence outside the region
        if path and frame_insert is not None and path[0] == frame_insert:
            out["recorded"].append(dict(u, disposition="IN_SHEET_FRAME_OCCURRENCE"))
            continue
        lr = GR.layer_role(u.get("layer"))
        if u.get("layer") is None:
            out["blocking_input"].append(dict(u, disposition="UNREALISED_ENTITY_LAYER_UNKNOWN"))
            continue
        if lr in GR.BOUNDARY_LAYER_ROLES:
            out["blocking_input"].append(dict(u, disposition=UNREALISED_BOUNDARY_LAYER))
            continue
        sites = sorted(layer_sites.get(u.get("layer"), ()))
        if sites:
            for sid in sites:
                out["site_issues"][sid].append(u["obs_id"])
            out["recorded"].append(dict(u, disposition=UNREALISED_IN_SITE, sites=sites))
        else:
            out["recorded"].append(dict(u, disposition="NOT_IN_ANY_BOUNDED_SITE_BY_LAYER_EVIDENCE",
                                        evidence="no realised part of this layer in the region touches a bounded site"))
    return out


PHYSICAL_ISSUES = (T.TOLERANCE_SENSITIVE, T.ZERO_WIDTH_SLIVER, T.TOPOLOGY_ROLE_UNRESOLVED, T.OPENING_CLOSURE_UNRESOLVED,
                   T.SITE_ID_COLLISION, XC.GEOS_CROSSCHECK_DISAGREES, RA.ROLE_CONFLICT_SEPARATOR,
                   "UNREALISED_ENTITY_ON_BOUNDARY_LAYER", "UNREALISED_ENTITY_POSSIBLY_IN_SITE",
                   "OCCURRENCE_REVIEW_REQUIRED")
SEMANTIC_ISSUES = (T.MULTIPLE_SEMANTIC_LABELS, T.LABEL_ON_BOUNDARY, T.LABEL_OCCURRENCE_SPLIT)


def classify_issues(site) -> None:
    """R8.9: physical (topology) vs semantic (labels) vs trade (objects inside a stable site) issues. The overall
    `status` keeps its R8.8 meaning (CERTIFIED only with no issue at all)."""
    iss = set(site["issues"])
    site["physical_issues"] = sorted(iss & set(PHYSICAL_ISSUES))
    site["semantic_issues"] = sorted(iss & set(SEMANTIC_ISSUES))
    site["trade_issues"] = sorted(iss - set(PHYSICAL_ISSUES) - set(SEMANTIC_ISSUES))
    site["physical_status"] = T.CERTIFIED if not site["physical_issues"] else T.REVIEW_REQUIRED


def consequences(res, items, adm, labels, tol) -> None:
    """R8.9 consequence check (role_authority.separator_analysis), run SEPARATELY for layer-only exclusions and for
    unknown geometry so each effect is attributed to its own origin; folded into the site issues, plus the site's
    weakest boundary authority grade."""
    cands = adm.get("separator_candidates", [])
    groups = {"exclusion": [c for c in cands if c[1] != "UNKNOWN"], "unknown": [c for c in cands if c[1] == "UNKNOWN"]}
    sep = {g: RA.separator_analysis(res, items, cs, eps_n=tol["eps_n"], eps_r=tol["eps_r"], labels=labels)
           for g, cs in groups.items()}
    res["separators"] = sep
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
        s_["issues"] = sorted(iss)
        s_["consequence"] = {g: {"effect": e["effect"], "sources": e["sources"], "origins": e["origins"]}
                             for g, e in (("exclusion", ex), ("unknown", un)) if e}
        g = [grades[x]["grade"] for x in s_["boundary_source_ids"] if x in grades]
        s_["authority_grade"] = min(g, key=lambda z: RA.GRADE_ORDER[z]) if g else None
        s_["status"] = T.CERTIFIED if not s_["issues"] else T.REVIEW_REQUIRED


def run(inp: CI.CanonicalMeasurementInput, *, frame_insert, expected_revision_id=None, selected_region_id=None,
        contract=TS01, unrealised=None, claims=(), occurrence_claims=None) -> dict:
    v = CI.validate(inp, contract, expected_revision_id=expected_revision_id, selected_region_id=selected_region_id)
    out = {"method_id": contract.method_id, "validation": v, "state": v["state"], "sites": None}
    if v["state"] != CI.COMPLETE:
        return out
    m = max_abs_coordinate(inp.parts)
    tol = TP.tolerances(m, inp.unit_native_to_mm)
    if not tol["valid"]:
        out.update(state=T.UNIT_UNRESOLVED, tolerances=tol)
        return out
    items, probes, labels, adm, closures, status, door_probes = topology_inputs(
        inp, frame_insert=frame_insert, eps_n=tol["eps_n"], eps_r=tol["eps_r"], claims=claims,
        occurrence_claims=occurrence_claims)
    res = T.analyse(items + closures, probes, labels, revision_id=inp.revision.revision_id, region_id=inp.region_id,
                    unit_native_to_mm=inp.unit_native_to_mm, max_abs_coordinate=m,
                    blocking_roles=GR.TOPOLOGY_BLOCKING + (RA.UNCONNECTED_BOUNDARY_CANDIDATE,), opening_status=status,
                    opening_symbol_occurrences=door_probes, glazed_openings=adm["glazed_openings"])
    consequences(res, items + closures, adm, labels, tol)
    xc = XC.check(res, items + closures, tol["eps_n"])
    for s_ in res["sites"]:
        st = xc["per_site"].get(s_["site_id"], {}).get("state", xc["state"])
        s_["crosscheck"] = st
        if st == XC.DISAGREES:
            s_["issues"] = sorted(set(s_["issues"]) | {XC.GEOS_CROSSCHECK_DISAGREES})
            s_["status"] = T.REVIEW_REQUIRED
    res["crosscheck"] = {k: v for k, v in xc.items() if k != "per_site"}
    res["crosscheck"]["disagreements"] = {k: v for k, v in sorted(xc["per_site"].items()) if v["state"] == XC.DISAGREES}
    if unrealised is not None:
        acc = unrealised_accounting(unrealised, inp, res, frame_insert)
        res["unrealised"] = {"blocking_input": acc["blocking_input"], "recorded": acc["recorded"],
                             "sites": {k: sorted(v) for k, v in acc["site_issues"].items()}}
        for s_ in res["sites"]:
            if s_["site_id"] in acc["site_issues"] or acc["blocking_input"]:
                s_["issues"] = sorted(set(s_["issues"]) | {UNREALISED_IN_SITE if not acc["blocking_input"]
                                                          else UNREALISED_BOUNDARY_LAYER})
                s_["status"] = T.REVIEW_REQUIRED
    else:
        res["unrealised"] = {"state": "NOT_SUPPLIED: the caller did not account for unrealised source entities"}
    for s_ in res["sites"]:
        classify_issues(s_)
    res["roles"] = adm
    res["openings"] = status
    res["closures"] = closures
    res["counts"] = {"admitted_boundary": len(items), "closures": len(closures), "probes": len(probes),
                     "labels": len(labels)}
    out.update(res)
    out["state"] = res["state"]
    return out
