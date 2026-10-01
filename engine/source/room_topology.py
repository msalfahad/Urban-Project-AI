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


def _occ(rec):
    path = rec.identity.instance_handles or ()
    return ("I" + path[0]) if path else ("E" + str(rec.identity.source_handle))


def topology_inputs(inp: CI.CanonicalMeasurementInput, *, frame_insert, eps_n):
    """(items, probes, labels, roles result, closures, opening status, symbol probes per door) - deterministic."""
    adm = GR.admit(inp, frame_insert=frame_insert, eps=eps_n)
    roles = adm["roles"]
    items, probes, door_probes = [], [], defaultdict(list)
    for p in sorted(inp.parts, key=lambda q: q.identity.key or ""):
        if p.visibility != CI.VISIBLE:
            continue
        a = roles[p.identity.key]
        if a.role in GR.TOPOLOGY_ADMITTED and p.kind in ("SEGMENT", "ARC", "CIRCLE"):
            items.append(T.BoundaryItem(p.identity.key, p.kind, tuple(p.geometry), a.role))
        else:
            pb = T.Probe(p.identity.key, p.kind, tuple(p.geometry), a.role, _occ(p))
            probes.append(pb)
            if a.role == GR.OPENING_SYMBOL:
                door_probes[_occ(p)].append(pb)
    closures, status = T.opening_closures(adm["doors"], items, eps_n)
    e_r = TP.eps_authored(inp.unit_native_to_mm)
    g_closures, g_status, g_open = T.glazing_closures(items, eps_n, e_r) if e_r else ([], {}, {})
    closures = closures + g_closures
    status = dict(status)
    adm["glazing"] = g_status
    adm["glazed_openings"] = g_open
    labels = [T.LabelText(t.identity.key, _occ(t), t.value, t.x, t.y)
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


def run(inp: CI.CanonicalMeasurementInput, *, frame_insert, expected_revision_id=None, selected_region_id=None,
        contract=TS01, unrealised=None) -> dict:
    v = CI.validate(inp, contract, expected_revision_id=expected_revision_id, selected_region_id=selected_region_id)
    out = {"method_id": contract.method_id, "validation": v, "state": v["state"], "sites": None}
    if v["state"] != CI.COMPLETE:
        return out
    coords = [abs(c) for p in inp.parts for c in p.geometry[:2]] or [1.0]
    tol = TP.tolerances(max(coords), inp.unit_native_to_mm)
    if not tol["valid"]:
        out.update(state=T.UNIT_UNRESOLVED, tolerances=tol)
        return out
    items, probes, labels, adm, closures, status, door_probes = topology_inputs(inp, frame_insert=frame_insert,
                                                                                  eps_n=tol["eps_n"])
    res = T.analyse(items + closures, probes, labels, revision_id=inp.revision.revision_id, region_id=inp.region_id,
                    unit_native_to_mm=inp.unit_native_to_mm, max_abs_coordinate=max(coords),
                    blocking_roles=GR.TOPOLOGY_BLOCKING, opening_status=status,
                    opening_symbol_occurrences=door_probes, glazed_openings=adm["glazed_openings"])
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
    res["roles"] = adm
    res["openings"] = status
    res["closures"] = closures
    res["counts"] = {"admitted_boundary": len(items), "closures": len(closures), "probes": len(probes),
                     "labels": len(labels)}
    out.update(res)
    out["state"] = res["state"]
    return out
