"""TS01 - ROOM / SPACE TOPOLOGY METHOD on CANONICAL_MEASUREMENT_INPUT (R8.8, SHADOW).

    canonical input --validate(TS01 contract)--> COMPLETE
        --> geometry role admission (geometry_role)          only positively admitted parts bound a site
        --> opening closures from proven doors (topology)     never inferred for an open passage
        --> certified topology (topology + topology_policy)   two builds, eps_n and eps_r
        --> sites with labels, contents, issues, status

A method-input contract (canonical_input.MethodContract) declares what TS01 consumes; any declared field missing,
duplicated, cross-revision or with unresolved visibility -> METHOD_INPUT_INCOMPLETE and no sites at all.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

from collections import defaultdict

from . import canonical_input as CI
from . import geometry_role as GR
from . import topology as T
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


def run(inp: CI.CanonicalMeasurementInput, *, frame_insert, expected_revision_id=None, selected_region_id=None,
        contract=TS01) -> dict:
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
    res["roles"] = adm
    res["openings"] = status
    res["closures"] = closures
    res["counts"] = {"admitted_boundary": len(items), "closures": len(closures), "probes": len(probes),
                     "labels": len(labels)}
    out.update(res)
    out["state"] = res["state"]
    return out
