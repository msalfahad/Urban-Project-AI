"""TS01 V3 - the frozen TS01 room topology (room_topology) with two injection points, nothing else changed:

    text_roles       text roles computed by text_role_v3 (tag families scoped to the SOURCE revision, not the plan
                     region; legacy Arabic tag texts follow their tag) instead of text_role.classify on one region
    extra_closures   zero-material closures from opening_completion (double-leaf doors, door-evidenced wall gaps);
                     they bound sites only - affects_wall_quantity / affects_finish_quantity stay False
    extra_opening_status   the opening state of the doors those closures close (merged over the frozen state)

The result also carries "_items" (the admitted boundary items, an engine object like "_arr").

With text_roles=None, extra_closures=() and extra_opening_status=None the result (less "_items") equals room_topology.run (tested). The two functions below are
copies of room_topology.topology_inputs / run (frozen, pinned by earlier freezes) with only those lines changed.
"""

from __future__ import annotations

from collections import defaultdict

from . import canonical_input as CI
from . import geometry_role as GR
from . import wall_bands as WB
from . import owner_claims as OC
from . import role_authority as RA
from . import text_role as TX
from . import semantic_zones as SZ
from . import topology as T
from . import topology_closures as TC
from . import topology_crosscheck as XC
from . import topology_policy as TP
from .room_topology import (LINEAR, TS01, UNREALISED_IN_SITE, _occ, classify_issues, consequences,  # noqa: F401
                            max_abs_coordinate, passage_sites, unrealised_accounting)

POLICY_ID = "TS01_V3_INJECTION_POINTS_V1"


def topology_inputs(inp: CI.CanonicalMeasurementInput, *, frame_insert, eps_n, eps_r=None, claims=(),
                    occurrence_claims=None, inferred_doors=None, text_roles=None):
    """(items, probes, labels, roles result, closures, opening status, symbol probes per door) - deterministic.

    R8.9 role authority (role_authority): occurrence contexts (building assemblies from positive evidence), source-
    scoped role claims, boundary authority grades (an admitted line touching no other boundary is NOT admitted:
    UNCONNECTED_BOUNDARY_CANDIDATE, blocking), and the separator candidates for the consequence check (stored in
    the roles result)."""
    adm = GR.admit(inp, frame_insert=frame_insert, eps=eps_n)
    troles = text_roles if text_roles is not None else TX.classify(inp, frame_insert=frame_insert, claims=claims)
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




def run(inp: CI.CanonicalMeasurementInput, *, frame_insert, expected_revision_id=None, selected_region_id=None,
        contract=TS01, unrealised=None, claims=(), occurrence_claims=None, part_claims=(), xref_claims=(),
        closure_policy=None, provenance=None, inferred_doors=None, extra_closures=(), text_roles=None,
        extra_opening_status=None) -> dict:
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
        occurrence_claims=occurrence_claims, inferred_doors=inferred_doors, text_roles=text_roles)
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
    closures = closures + list(extra_closures)          # V3: zero-material closures from opening_completion
    if extra_opening_status:                            # V3: the opening state of the doors those closures close
        status = dict(status, **extra_opening_status)
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
    out["_items"] = items                                  # V3: admitted boundary items (for opening_completion)
    return out
