"""R8.11 lab: Qortuba rebuilt with wall bands + zero-material wall-end closures (TOPOLOGY_CLOSURE_POLICY_V1), the
semantic class authority, object-footprint policies and the run manifest; the six rows with full provenance.

    python3 research/external_engine_lab/r8_11_qortuba.py <work> <register_dir> [code_commit]

Project semantics live here only. The wall-band, cap, near-miss and closure rules were frozen in engine/source
(commit 5895981) BEFORE the first Qortuba run. One post-freeze amendment (A1, WALL_BAND_POLICY_V2) was made after
the first run and is recorded with the frozen run's own results (it can only remove candidates; the authorised
closure set is unchanged). No source geometry is edited and no CAD entity is created: a closure is a derived,
reversible, zero-material record.
"""

from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_10_claims as CL                                                                     # noqa: E402
import r8_10_qortuba as Q10                                                                   # noqa: E402
import r8_8_topology as LAB                                                                   # noqa: E402
from engine.source import geometry_role as GR, owner_claims as OC, owner_scope as OS          # noqa: E402
from engine.source import role_authority as RA, room_topology as RT, run_manifest as RM       # noqa: E402
from engine.source import topology as T, topology_closures as TC, topology_policy as TP       # noqa: E402
from engine.source import trade_regions as TR, wall_bands as WB                               # noqa: E402

C = LAB.C
ROWS = LAB.ROUND1
UNL = Q10.UNL
handle = Q10.handle
FROZEN_COMMIT = "5895981"
FROZEN_V1_RESULT = {          # the first Qortuba run, WALL_BAND_POLICY_V1 exactly as frozen (before amendment A1)
    "NEW_K2": {"bands": 33, "closures": {"AUTHORISED_FOR_SHADOW": ["TC-aea10821cffe20ff"],
                                         "DIAGNOSTIC_PASS": ["TC-afadb7261888249e", "TC-bf49f65df1238aa5",
                                                             "TC-d34896b88d4f5e08"],
                                         "TOPOLOGY_CLOSURE_UNRESOLVED": ["TC-15aae08f263d7ca0", "TC-46f92c3b43e4035f",
                                                                         "TC-6c869e2577a6020f",
                                                                         "TC-a573660d53d92d11"]},
               "passages": 17, "rows": {"Q-03": 17.7425, "Q-03P": 11.685, "Q-11": 17.7425, "Q-12": 11.685,
                                        "Q-13": "BLOCKED_MULTIPLE: BLOCKED_ROLE, BLOCKED_TRADE_RULE",
                                        "Q-14": "BLOCKED_ROLE"}},
    "OLD_K1": {"bands": 35, "closures": {"AUTHORISED_FOR_SHADOW": [], "DIAGNOSTIC_PASS": 3,
                                         "TOPOLOGY_CLOSURE_UNRESOLVED": 4}, "passages": 15}}

# ---------------------------------------------------------------------------------------------- authorities
OWNER_RULES = Q10.OWNER_RULES
SPACE_CLASSES = TR.SemanticClassRule(
    "QORTUBA-SPACE-CLASS", 1, "PROJECT_OWNER_RULE (owner rule store, rank 2)",
    (f"{OWNER_RULES}: US-01 WET_SERVICE_ROOM_CERAMIC", f"{OWNER_RULES}: QP-07 QORTUBA_CERAMIC_SERVICE_ROOMS = "
     "BATH x3 + PAINTRY", f"{OWNER_RULES}: QP-14 QORTUBA_DRY_FLOOR_FINISH = PORCELAIN"),
    {"project": "QORTUBA", "region": C.REGION_ID, "plan": CL.PLAN},
    by_label={"BATH": "WET_ROOM", "PAINTRY": "SERVICE_ROOM"}, otherwise_class="DRY_INTERNAL_ROOM",
    scope_labels=tuple(sorted(LAB.apartment_names() - {"BATH", "PAINTRY"})))
FLOOR_BY_CLASS = {"WET_ROOM": "CERAMIC_WET_FLOOR", "SERVICE_ROOM": "CERAMIC_SERVICE_FLOOR",
                  "DRY_INTERNAL_ROOM": "PORCELAIN_DRY_FLOOR"}
FLOOR_RULE = TR.class_rule_as_treatment(
    "QORTUBA-FLOOR-TREATMENT", 2, "FLOOR_FINISH", "PROJECT_OWNER_RULE (owner rule store, rank 2)",
    Q10.FLOOR_RULE.source_refs, SPACE_CLASSES, FLOOR_BY_CLASS, TR.POLICY_UNRESOLVED)
CEILING_FOOTPRINT = TR.TradeObjectFootprintPolicy(
    "QORTUBA-CEILING-OBJECT-FOOTPRINT", 1, "CEILING", TR.ANY_NON_PARTITION_OBJECT, TR.FOOTPRINT_INCLUDED,
    "OWNER_CLAIM", {"revision": C.REV_NEW_ID, "region": C.REGION_ID, "spaces": "the Q-14 claim's space ids"},
    (C.Q14_CLAIM,))
FOOTPRINT_POLICIES = (CEILING_FOOTPRINT,)          # FLOOR_FINISH: none exists (searched; see OBJECT_FOOTPRINT_POLICY)
OBJECT_ROLES = (GR.FURNITURE, GR.SANITARY_FIXTURE)  # proven non-partition object roles (footprint question applies)


def ceiling_rule():
    return Q10.ceiling_rule()


def rule_for(rid):
    return ceiling_rule() if rid == "Q-14" else FLOOR_RULE


# ---------------------------------------------------------------------------------------------- runs
def run(inp, name, facts, pc=(), xc=(), closure_policy=None, provenance=None):
    u = CL.attach_xref_facts(LAB.UNREALISED[name], facts)
    r = LAB.run(inp, u, part_claims=pc, xref_claims=xc, closure_policy=closure_policy, provenance=provenance)
    r["_unit2"] = (inp.unit_native_to_mm ** 2) / 1e6
    r["_unit_mm"] = inp.unit_native_to_mm
    return r


def runs(work, commit=None):
    inps, all_new, facts = Q10.inputs(work)
    pc, xc, raw = CL.load()
    i_new, i_old = inps["NEW_K2"], inps["OLD_K1"]
    prov = {"code_commit": commit, "lab": "research/external_engine_lab/r8_11_qortuba.py"}
    return {"inputs": inps, "facts": facts, "claims": (pc, xc, raw),
            "new_r810": run(i_new, "NEW_K2", facts, pc, xc),
            "new": run(i_new, "NEW_K2", facts, pc, xc, TC.POLICY_ID, prov),
            "old_r810": run(i_old, "OLD_K1", facts, pc, xc),
            "old": run(i_old, "OLD_K1", facts, pc, xc, TC.POLICY_ID, prov)}


def topo(inp, pc):
    tol = TP.tolerances(RT.max_abs_coordinate(inp.parts), inp.unit_native_to_mm)
    pcl, _ = OC.role_claims(pc, inp)
    items, probes, labels, adm, closures, status, _ = RT.topology_inputs(
        inp, frame_insert=C.FRAME_INSERT, eps_n=tol["eps_n"], eps_r=tol["eps_r"], claims=tuple(pcl))
    return {"items": items, "probes": probes, "labels": labels, "tol": tol, "adm": adm}


# ---------------------------------------------------------------------------------------------- exclusion groups
def exclusion_groups(res, tp, site):
    """The site's layer-excluded separator candidates, attributed PER SOURCE ENTITY: what each one alone would
    separate (diagnostic arrangement; authority untouched), and whether it is a non-partition object."""
    ex = (site.get("consequence") or {}).get("exclusion")
    if not ex:
        return []
    cands = [c for c in res["roles"]["separator_candidates"] if c[1] != "UNKNOWN"]
    roles = res["roles"]["roles"]
    out = []
    for h in sorted({handle(x) for x in ex["sources"]}, key=lambda z: (len(z), z)):
        mine = [c for c in cands if handle(c[0].source_id) == h]
        a = RA.separator_analysis(res, tp["items"] + list(res["closures"]), mine, eps_n=tp["tol"]["eps_n"],
                                  eps_r=tp["tol"]["eps_r"], labels=tp["labels"])
        e = a["sites"].get(site["site_id"], {"effect": "NONE", "hypothetical_sites": []})
        hyp = sorted(e.get("hypothetical_sites", []), key=lambda z: -z["area"])
        role = sorted({roles[c[0].source_id].role for c in mine})
        obj = all(r in OBJECT_ROLES for r in role)
        out.append({"source": h, "roles": role, "origins": sorted({c[1] for c in mine}),
                    "object_class": TR.ANY_NON_PARTITION_OBJECT if obj else "PARTITION_OR_WALL_END_CANDIDATE",
                    "effect": e["effect"],
                    "pockets_m2": [round(x["area"] * res["_unit2"], 4) for x in hyp[1:] if not x["labels_inside"]]})
    return out


def group_materiality(g, rule):
    if g["effect"] == "NONE":
        return TR.NON_MATERIAL, "cannot change the site"
    if g["effect"] == "SEPARATES_LABELS" or g["object_class"] != TR.ANY_NON_PARTITION_OBJECT:
        return TR.MATERIAL, ("a line closing a wall core / a possible partition: material to every area trade "
                             "whatever the footprint policy")
    tr, pid = TR.footprint_treatment(rule.trade, TR.ANY_NON_PARTITION_OBJECT, FOOTPRINT_POLICIES)
    if tr == TR.FOOTPRINT_INCLUDED:
        return TR.NON_MATERIAL, f"{pid}: the trade includes the footprint of a non-partition object"
    return TR.MATERIAL, f"{rule.rule_id}: no authority says how {rule.trade} treats this object's footprint"


# ---------------------------------------------------------------------------------------------- trade layer
def materiality(s, rule, res):
    """R8.10 materiality of unknown-role objects, now through the object-footprint policies (R8.11)."""
    if T.TOPOLOGY_ROLE_UNRESOLVED not in s["issues"] and RA.UNKNOWN_OBJECT_IN_SITE not in s["issues"]:
        return None
    un = (s.get("consequence") or {}).get("unknown")
    srcs = set(s.get("blocked_by", []))
    analysed = {c.source_id for c, o in res["roles"]["separator_candidates"] if o == "UNKNOWN"}
    if any(c.source_id in srcs and c.role == RA.UNCONNECTED_BOUNDARY_CANDIDATE
           for c, o in res["roles"]["separator_candidates"]):
        return {"state": TR.MATERIAL, "why": "an unconnected wall-layer candidate could be a wall", "sources": sorted(srcs)}
    if srcs - analysed:
        return {"state": TR.MATERIAL, "why": "blocking sources the consequence analysis did not include",
                "sources": sorted(srcs - analysed)}
    return dict(TR.object_materiality(un, rule, FOOTPRINT_POLICIES), sources=sorted(srcs))


def implicit_objects(res, site):
    """Proven non-partition objects (furniture / sanitary fixtures) whose geometry lies in the site: the topology
    convention leaves their footprint INSIDE the site - an implicit FOOTPRINT_INCLUDED."""
    arr, sites = res["_arr"], res["sites"]
    roles = res["roles"]["roles"]
    out = Counter()
    for k, a in roles.items():
        if a.role not in OBJECT_ROLES:
            continue
        kind_g = res["_probe_geom"].get(k)
        if kind_g is None:
            continue
        kind, g = kind_g
        pt = ((g[0] + g[2]) / 2, (g[1] + g[3]) / 2) if kind == "SEGMENT" else (g[0], g[1])
        sid, _ = T.locate(arr, sites, pt, 0.0)
        if sid == site["site_id"]:
            out[a.role] += 1
    return dict(out)


def site_decision(s, rid, rule, names, internal, res, tp):
    zn = Q10.site_zone_names(s, names, internal)
    sem_state = res["semantic"]["sites"].get(s["site_id"], {}).get("state", "")
    dec = TR.zone_decision(zn, rule, unresolved_texts=[t["value"] for t in s.get("unresolved_texts", [])],
                           authored_trade_boundary="MULTIPLE_SEMANTIC_ZONES_ESTABLISHED" in sem_state)
    dec["space_classes"] = {n: SPACE_CLASSES.space_class(n) for n in zn if n != UNL} if rid != "Q-14" else None
    treats = set(v for v in dec["treatments"].values() if v)
    want = Q10.ROW_TREATMENT[rid]
    if want not in treats:
        return False, [], dec
    bl = []
    if dec["state"] == TR.REQUIRED:
        bl.append(("SEMANTIC_ZONE", T.MULTIPLE_SEMANTIC_LABELS, dec["why"]))
    elif dec["state"] == TR.UNRESOLVED:
        bl.append(("SEMANTIC_ZONE" if dec["unresolved_texts"] else "TRADE_RULE", "TRADE_TREATMENT_UNRESOLVED",
                   dec["why"]))
    mat = materiality(s, rule, res)
    groups = []
    for iss in s["issues"]:
        if iss in (T.MULTIPLE_SEMANTIC_LABELS, RA.UNKNOWN_OBJECT_IN_SITE):
            continue
        if iss == T.TOPOLOGY_ROLE_UNRESOLVED:
            if mat and mat["state"] == TR.NON_MATERIAL:
                continue
            bl.append(("ROLE_AUTHORITY", iss, [handle(x) for x in (mat or {}).get("sources", s["blocked_by"])][:12]))
            if mat and "no authority says how this trade treats an object footprint" in mat["why"]:
                bl.append(("TRADE_RULE", "OBJECT_FOOTPRINT_POLICY_UNRESOLVED", f"{rule.rule_id}: {rule.trade}"))
            continue
        if iss == RA.ROLE_CONFLICT_SEPARATOR:                  # R8.11: per source entity, per trade
            groups = exclusion_groups(res, tp, s)
            for g in groups:
                st, why = group_materiality(g, rule)
                g[f"materiality_{rule.trade}"] = {"state": st, "why": why}
                if st != TR.MATERIAL:
                    continue
                if g["object_class"] == TR.ANY_NON_PARTITION_OBJECT:
                    bl.append(("TRADE_RULE", "OBJECT_FOOTPRINT_POLICY_UNRESOLVED",
                               {"source": g["source"], "roles": g["roles"], "pockets_m2": g["pockets_m2"]}))
                else:
                    bl.append(("ROLE_AUTHORITY", iss, {"source": g["source"], "roles": g["roles"],
                                                       "pockets_m2": g["pockets_m2"], "why": why}))
            continue
        cls = Q10.BLOCKER_CLASS.get(iss, "PHYSICAL_TOPOLOGY")
        detail = None
        if iss == RA.NEAR_MISS_BOUNDARY_GAP:
            detail = [{"source": handle(m["source"]), "gap_mm": [round(g * res["_unit_mm"], 2)
                                                                for g in m["gaps_native"]]} for m in s["near_miss"]]
        bl.append((cls, iss, detail))
    if mat and mat["state"] == TR.MATERIAL and T.TOPOLOGY_ROLE_UNRESOLVED not in s["issues"]:
        bl.append(("ROLE_AUTHORITY", "OBJECT_ROLE_MATERIAL_TO_TRADE", mat["why"]))
    if rid == "Q-14":
        claim = C.claims()[C.Q14_CLAIM]
        sp = LAB.claim_space_id(zn) or UNL
        a = OS.applies(claim, project="QORTUBA", revision_id=res["_revision_id"], purpose=OS.SHADOW_DIAGNOSTIC,
                       region_id=C.REGION_ID, space_id=sp, item="Q-14|CEILING_BY_AREA")
        if a["state"] != OS.APPLIES:
            bl.append(("OWNER_FACT", "Q14_CEILING_BASIS_" + a["state"], a.get("mismatched")))
    dec = dict(dec, object_materiality=mat, exclusion_groups=groups)
    return True, bl, dec


def _blocker_sig(bl):
    return sorted({(c, i) for c, i, _ in bl})


def rows_r811(res, tp, revision_id, manifest=None):
    names = LAB.apartment_names()
    lab_sites, internal_sites = LAB.apartment_sites(res)
    internal = {s["site_id"] for s in internal_sites}
    res["_revision_id"] = revision_id
    zones, th = res["semantic"]["zones"], res["semantic"]["thresholds"]
    bands = (res.get("wall_bands") or {}).get("bands", [])
    closures = (res.get("topology_closures") or {}).get("closures", [])
    passages = res.get("passages") or []
    applied = [c for c in res["owner_claims"]["part_claims"] if c["applied_parts"]]
    out = {}
    for rid in ROWS:
        rule = rule_for(rid)
        used, blockers, decisions = [], [], {}
        for s in sorted(lab_sites + internal_sites, key=lambda z: z["site_id"]):
            sel, bl, dec = site_decision(s, rid, rule, names, internal, res, tp)
            if not sel:
                continue
            decisions[s["site_id"]] = dec
            rec = {"site": s["site_id"], "zones": Q10.site_zone_names(s, names, internal),
                   "area_m2": round(s["area_m2"], 6)}
            if bl:
                blockers.append(dict(rec, blockers=[{"class": c, "issue": i, "detail": d} for c, i, d in bl]))
            else:
                used.append(dict(rec, decision=dec["state"]))
        classes = sorted({b["class"] for x in blockers for b in x["blockers"]})
        state = ("COMPUTED_SHADOW" if used and not classes else "NO_SITE" if not used and not classes else
                 Q10.STATE_OF[classes[0]] if len(classes) == 1 else
                 "BLOCKED_MULTIPLE: " + ", ".join(Q10.STATE_OF[c] for c in classes))
        sids = {u["site"] for u in used} | {b["site"] for b in blockers}
        bsrc = {x for s in res["sites"] if s["site_id"] in sids for x in s["boundary_source_ids"]}
        row_bands = sorted(b["band_id"] for b in bands if {b["face_a"], b["face_b"]} & bsrc)
        row_closures = sorted(c["closure_id"] for c in closures if TC.PREFIX + c["closure_id"] in bsrc)
        openings = sorted({x for x in bsrc if x.startswith("CLOSURE|")})
        imp = {s["site_id"]: implicit_objects(res, s) for s in res["sites"] if s["site_id"] in sids}
        release = []
        if revision_id == C.REV_NEW_ID:
            release.append("SOURCE_ANCHOR: the claims and the measurement are anchored to the DXF "
                           f"{C.NEW_DXF[:12]}...; DWG {Q10.DWG_CANDIDATE[:12]}... identity NOT_ESTABLISHED")
        if rule.trade == "FLOOR_FINISH" and any(imp.values()):
            release.append("OBJECT_FOOTPRINT_IMPLICIT: proven furniture / fixture footprints are inside the measured "
                           "floor by the topology convention, not by a FLOOR_FINISH footprint authority")
        release.append("SHADOW_ONLY: no baseline approval, no migration transaction, no release gate passed")
        out[rid] = {
            "state": state, "value": round(sum(u["area_m2"] for u in used), 4) if state == "COMPUTED_SHADOW" else None,
            "physical_site_ids": sorted(sids), "sites_used": used, "blockers": blockers, "blocker_classes": classes,
            "trade_authority": {"rule": f"{rule.rule_id}@v{rule.version}", "authority": rule.authority,
                                "refs": list(rule.source_refs), "row_treatment": Q10.ROW_TREATMENT[rid],
                                "semantic_class_rule": None if rid == "Q-14" else
                                f"{SPACE_CLASSES.rule_id}@v{SPACE_CLASSES.version}"},
            "footprint_authority": dict(zip(("treatment", "policy"), TR.footprint_treatment(
                rule.trade, TR.ANY_NON_PARTITION_OBJECT, FOOTPRINT_POLICIES))),
            "implicit_object_footprints": {k: v for k, v in imp.items() if v},
            "zone_decisions": decisions,
            "semantic_zone_ids": sorted(z["zone_id"] for z in zones if z["physical_site_id"] in sids),
            "wall_bands": row_bands, "topology_closures_applied": row_closures, "opening_closures": openings,
            "threshold_sites": [{"threshold": t["threshold_id"], "site": t["physical_site_id"], "opening": t["opening"],
                                 "area_m2": round(t["area"] * res["_unit2"], 6), "sides": t["sides"],
                                 "allocation": t["allocation"]} for t in th if sids & set(t["sides"])],
            "open_passage_sites": [{"passage": p["passage_id"], "width_mm": round(p["width_mm"], 1),
                                    "area_m2": round(p["area_m2"], 4), "allocation": p["trade_allocation"]}
                                   for p in passages if p.get("strip_in_site") in sids],
            "claims_applied": sorted(f"{c['claim_id']}@v{c['version']}" for c in applied
                                     if set(c["applied_parts"]) & bsrc) +
            ([C.Q14_CLAIM] if rid == "Q-14" and revision_id == C.REV_NEW_ID else []),
            "source_anchor": {"revision": revision_id, "dxf_sha256": res["run_manifest"]["source_anchor_sha256"],
                              "dwg_identity": "NOT_ESTABLISHED" if revision_id == C.REV_NEW_ID else None},
            "run_id": res["run_manifest"]["run_id"], "run_input_digest": res["run_manifest"]["RUN_INPUT_DIGEST"],
            "release_blockers": release}
        tl = {"run_input_digest": out[rid]["run_input_digest"], "row": rid, "trade_rule": out[rid]["trade_authority"],
              "footprint_policies": [f"{p_.policy_id}@v{p_.version}:{p_.trade}:{p_.treatment}" for p_ in
                                     FOOTPRINT_POLICIES], "row_claims": out[rid]["claims_applied"],
              "space_classes": [SPACE_CLASSES.rule_id, SPACE_CLASSES.version, sorted(SPACE_CLASSES.by_label.items()),
                                SPACE_CLASSES.otherwise_class, list(SPACE_CLASSES.scope_labels)]}
        out[rid]["row_input_digest"] = RM._digest(tl)
        out[rid]["row_input_digest_covers"] = sorted(tl)
    return out


# ---------------------------------------------------------------------------------------------- cap analysis
def _part(inp, h):
    return next(p for p in inp.parts if p.identity.source_handle == h and not p.identity.instance_handles)


def _segments_ending_at(tp, pt, eps):
    out = []
    for it in tp["items"]:
        if it.kind == "SEGMENT":
            a, b = it.geometry[:2], it.geometry[2:]
            if math.dist(a, pt) <= eps or math.dist(b, pt) <= eps:
                out.append(it)
    return out


def cap_analysis(inp, res, tp, h):
    """Blind structural classification of one drawn line through the generic path:
    WALL_END_CAP_PROVEN / WALL_END_CAP_CANDIDATE (it corroborates an established band's aligned end),
    NOT_WALL_CAP (it is the jamb line of a glazed opening: glazing ends on it), UNRESOLVED (no established band
    end there - with the structural reason)."""
    p = _part(inp, h)
    key = p.identity.key
    g = [float(v) for v in p.geometry]
    eps = tp["tol"]["eps_r"]
    review = RA.NEAR_MISS_REVIEW_BAND_MM / inp.unit_native_to_mm
    role = res["roles"]["roles"][key]
    rec = {"handle": h, "layer": p.layer, "role": role.role, "rule": role.rule_id,
           "geometry": [round(v, 2) for v in g], "length_mm": round(math.dist(g[:2], g[2:]) * inp.unit_native_to_mm, 1),
           "authority_grade": res["roles"]["grades"].get(key, {}).get("grade")}
    bands = res["wall_bands"]["bands"]
    closures = {c["band_id"]: c for c in res["topology_closures"]["closures"]}
    for b in bands:
        for e in b["ends"]:
            for cap in e.get("drawn_caps", []):
                if cap["source"] == key:
                    c = closures.get(b["band_id"])
                    return dict(rec, classification=cap["grade"], band_id=b["band_id"],
                                faces=[handle(b["face_a"]), handle(b["face_b"])],
                                band_width_mm=round(b["width"] * inp.unit_native_to_mm, 1), end_kind=e["kind"],
                                gap_to_face_ends_mm=[round(cap["gap_to_face_a_end"] * inp.unit_native_to_mm, 2),
                                                     round(cap["gap_to_face_b_end"] * inp.unit_native_to_mm, 2)],
                                shortfall_across_mm=round(cap["shortfall_across"] * inp.unit_native_to_mm, 2),
                                offset_along_mm=round(cap["offset_along_band"] * inp.unit_native_to_mm, 2),
                                closure=None if c is None else {k: c[k] for k in ("closure_id", "release", "geometry",
                                                                                   "physical_material", "reversible")},
                                closure_geometry_is_face_end_points=True)
    glazing_on_it = sorted({handle(it.source_id) for it in tp["items"] if it.role == GR.GLAZING_BOUNDARY and any(
        _near_line(q, g, eps * 2) for q in (it.geometry[:2], it.geometry[2:]))})
    if glazing_on_it:
        return dict(rec, classification=WB.NOT_WALL_CAP, glazing_ending_on_it=glazing_on_it,
                    reason="the line is the jamb of a glazed opening: glazing lines end on it; no wall band ends "
                           "here (the glazing lies inside the wall strip, so the faces form no band)")
    faces = {}
    for end in (g[:2], g[2:]):
        for it in tp["items"]:
            if it.kind == "SEGMENT" and it.role == GR.TOPOLOGY_BOUNDARY and any(
                    math.dist(q, end) <= review for q in (it.geometry[:2], it.geometry[2:])):
                faces[handle(it.source_id)] = it
    in_band = {handle(x): b["band_id"] for b in bands for x in (b["face_a"], b["face_b"])}
    why = []
    for fh, it in sorted(faces.items()):
        frag = [handle(s.source_id) for s in tp["items"] if s.kind == "SEGMENT" and s.source_id != it.source_id
                and _collinear_touching(s.geometry, it.geometry, eps)]
        why.append({"face": fh, "in_established_band": in_band.get(fh), "collinear_fragments": frag})
    return dict(rec, classification=WB.CAP_UNRESOLVED, faces_at_its_ends=why,
                reason="no ESTABLISHED wall band ends here, so the line corroborates nothing and no closure exists")


def _near_line(q, g, eps):
    (x1, y1, x2, y2) = g
    L = math.dist((x1, y1), (x2, y2))
    if L == 0:
        return False
    t = ((q[0] - x1) * (x2 - x1) + (q[1] - y1) * (y2 - y1)) / (L * L)
    if t < -eps / L or t > 1 + eps / L:
        return False
    px, py = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
    return math.dist(q, (px, py)) <= eps


def _collinear_touching(a, b, eps):
    """a and b share an end point and a lies on b's (infinite) line: one face drawn in fragments."""
    if not any(math.dist(p, q) <= eps for p in (a[:2], a[2:]) for q in (b[:2], b[2:])):
        return False
    L = math.dist(b[:2], b[2:])
    if L == 0:
        return False
    return all(abs((p[0] - b[0]) * (b[3] - b[1]) - (p[1] - b[1]) * (b[2] - b[0])) / L <= eps for p in (a[:2], a[2:]))


def h2430_pairing(tp, eps):
    """Why the H2430 wall band is NOT established under the frozen policy (structural facts, recomputed)."""
    by = {handle(it.source_id): it for it in tp["items"] if it.kind == "SEGMENT"}
    f477, f471, f470 = by["477"], by["471"], by["470"]
    sep = abs(f477.geometry[1] - f471.geometry[1])
    cross = sorted({handle(it.source_id) for it in tp["items"] if it.kind == "SEGMENT" and it.role ==
                    GR.STRUCTURAL_OBSTACLE and min(it.geometry[0], it.geometry[2]) < 109608.08 and
                    max(it.geometry[0], it.geometry[2]) > 109308.08 and
                    min(it.geometry[1], it.geometry[3]) <= 15029.72 + eps and
                    max(it.geometry[1], it.geometry[3]) >= 15049.72 - eps})
    return {"face_above": "477", "face_above_span_x": [f477.geometry[0], f477.geometry[2]],
            "faces_below": {"470": [f470.geometry[0], f470.geometry[2]], "471": [f471.geometry[0], f471.geometry[2]]},
            "separation_mm": round(sep * 10, 1),
            "finding": "the lower face is drawn as two collinear fragments (H470 + H471) against one upper face (H477). "
                       "WALL_BAND_POLICY_V1/V2 tests 'mutual nearest' over each face's FULL length: H477's nearest "
                       "lower partner is H470 (a tie at 200 mm with H471, broken by source id), so H471 has no mutual "
                       "partner; the H470 / H477 strip is crossed by the column outline " + ", ".join(cross) +
                       " (STRUCTURAL_OBSTACLE), so that pair is no band either. No band => no aligned end => H2430 "
                       "corroborates nothing.",
            "column_in_strip": cross,
            "not_done_in_r8_11": "a fragment-aware pairing (mutual nearest over the OVERLAP; collinear face fragments "
                                 "as one face in the safety test) is generic, but it was identified AFTER seeing the "
                                 "Qortuba result; adopting it now would calibrate the frozen rule to H2430. It is "
                                 "engineering action E-R8.12-01 (synthetic tests first, then a blind re-run)."}


# ---------------------------------------------------------------------------------------------- registers
def _m2(res, a):
    return a * res["_unit2"]


def site_by_id(res, sid):
    return next((s for s in res["sites"] if s["site_id"] == sid), None)


def stamps_of(res, sid):
    s = site_by_id(res, sid)
    return sorted({v for vs in LAB.stamps(s).values() for v in vs}) if s else []


def hall(res):
    return next(s for s in res["sites"] if any("HALL" in v for v in LAB.stamps(s).values()))


def passage_register(res, inp):
    names = LAB.apartment_names()
    out = []
    for p in res["passages"]:
        z = sorted(set(stamps_of(res, p["strip_in_site"])) & names)
        out.append({"passage_id": p["passage_id"], "kind": p["kind"], "band_id": p["band_id"],
                    "band_end": p["band_end"], "end_kind": p["end_kind"],
                    "target": handle(p["target"]) if "|H" in p["target"] else p["target"],
                    "width_mm": round(p["width_mm"], 1), "wall_thickness_mm": round(p["thickness_mm"], 1),
                    "area_m2": round(p["area_m2"], 4), "polygon": [[round(v, 2) for v in q] for q in p["polygon"]],
                    "jamb_faces": [{"band_id": j["band_id"], "segment": [[round(v, 2) for v in q] for q in j["segment"]]}
                                   for j in p["jamb_faces"]],
                    "head_condition": p["head_condition"], "physically_connected": p["physically_connected"],
                    "strip_in_site": p["strip_in_site"], "site_zones": z,
                    "adjacent_sites": p["adjacent_sites"], "trade_allocation": p["trade_allocation"],
                    "reveals": p["reveals"], "kind_note": "OPEN_PASSAGE_SITE: a doorless strip through a wall line; "
                                                          "a DOOR_THRESHOLD_SITE is a separate record"})
    return out


def qp_audit(passages_new, passages_old, res_new, inp_new):
    """QP-17 / QP-18 / QP-19 (old revision, owner) as CORROBORATION ONLY of the new revision's geometric findings."""
    def find(ps, zones, width):
        return [p["passage_id"] for p in ps if set(zones) <= set(p["site_zones"]) and abs(p["width_mm"] - width) <= 1]
    mbd_new, mbd_old = find(passages_new, ["M.B.ROOM", "DRESS"], 1200), find(passages_old, ["M.B.ROOM", "DRESS"], 1200)
    gap = (109893.40 - 109773.76) * inp_new.unit_native_to_mm
    return {
        "QP-17_M.B.ROOM/DRESS_1.200": {"new_revision": mbd_new, "old_revision": mbd_old,
                                       "status": "CORROBORATED_BY_OWNER_RULE" if mbd_new else "NOT_DETECTED",
                                       "basis": "CORROBORATION_ONLY: the owner rule is about the old revision"},
        "QP-17_HALL/LOBBY_1.200": {"new_revision": [], "old_revision": [],
                                   "status": "NOT_DETECTED_AS_PASSAGE_SITE",
                                   "geometric_gap_between_face_ends_mm": round(gap, 1),
                                   "why": "the passage's west jamb is the H471/H477 wall end, which is no established "
                                          "band (face fragmentation, see H2430); the east jamb (H2296/H2297) is a band "
                                          "end and is closed by the authorised zero-material closure",
                                   "basis": "CORROBORATION_ONLY"},
        "QP-18": {"HALL/LOBBY": "OPEN_PASSAGE_FULL_HEIGHT (no head, no soffit)",
                  "M.B.ROOM/DRESS": "OPEN_PASSAGE_WITH_HEAD (left, right and top reveals)",
                  "new_revision_head_in_source": "NOT_ESTABLISHED_IN_SOURCE (plan geometry carries no head)",
                  "basis": "CORROBORATION_ONLY: never transferred to the new revision as a claim"},
        "QP-19": {"M.B.ROOM/DRESS_head_m": 2.2, "basis": "CORROBORATION_ONLY (old revision)",
                  "soffit_guard": "if a head exists its soffit is an opening surface: never also ceiling area "
                                  "(Q-14) nor a room wall face"}}


def registers(work, commit=None):
    R = runs(work, commit)
    new, old = R["new"], R["old"]
    inp_new, inp_old = R["inputs"]["NEW_K2"], R["inputs"]["OLD_K1"]
    pc, xc, raw = R["claims"]
    tp_new, tp_old = topo(inp_new, pc), topo(inp_old, pc)
    for res, tp in ((new, tp_new), (old, tp_old), (R["new_r810"], tp_new), (R["old_r810"], tp_old)):
        res["_probe_geom"] = {p.source_id: (p.kind, p.geometry) for p in tp["probes"]}
    rows_new = rows_r811(new, tp_new, C.REV_NEW_ID)
    rows_old = rows_r811(old, tp_old, C.REV_OLD_ID)
    rows_new_810 = Q10.rows_r810(R["new_r810"], C.REV_NEW_ID, R["new_r810"]["owner_claims"]["part_claims"])
    rows_old_810 = Q10.rows_r810(R["old_r810"], C.REV_OLD_ID)
    eps = tp_new["tol"]["eps_r"]
    caps = {h: cap_analysis(inp_new, new, tp_new, h) for h in ("2430", "2431", "1316")}
    caps["2430"]["pairing"] = h2430_pairing(tp_new, eps)
    caps["2430"]["old_revision_counterpart"] = "H553 (WALL layer) caps the band at x = 109808.08 in the old revision: " \
                                               "corroboration only (a different drawing; never transferred)"
    caps["2431"]["old_revision_counterpart"] = "none drawn on DIM; the old revision's passage geometry differs"
    caps["1316"]["old_revision_counterpart"] = "not compared (a window jamb line)"
    hall_810, hall_811 = hall(R["new_r810"]), hall(new)
    nm810 = [m for m in R["new_r810"]["near_misses"]["near_misses"]]
    nm811 = [m for m in new["near_misses"]["near_misses"]]
    leak = {"hall_site_r8_10": hall_810["site_id"], "hall_area_r8_10_m2": round(hall_810["area_m2"], 4),
            "hall_site_r8_11": hall_811["site_id"], "hall_area_r8_11_m2": round(hall_811["area_m2"], 4),
            "removed_m2": round(hall_810["area_m2"] - hall_811["area_m2"], 4),
            "hall_issues_r8_10": hall_810["issues"], "hall_issues_r8_11": hall_811["issues"],
            "the_0_6493_m2_leak": "CLOSED: the H2296/H2297 band end is closed by the authorised zero-material closure "
                                  "(face end points, not H2431's coordinates); the separated piece is a pure band "
                                  "interior and leaves the HALL; NEAR_MISS_BOUNDARY_GAP is gone from the HALL",
            "the_0_3813_m2_core": "STILL INSIDE the HALL: H2430's band is not established (see H2430) - the HALL keeps "
                                  "ROLE_CONFLICT_SEPARATOR for it",
            "the_2_3914_m2_pocket": "H1663 dining set against the wall: a FURNITURE object, never a wall; its footprint "
                                    "is a trade-policy question (ceiling: included by the Q-14 claim; floor: no "
                                    "authority)"}
    pas_new, pas_old = passage_register(new, inp_new), passage_register(old, inp_old)
    regs = {}
    wb_pol = new["wall_bands"]["policy"]
    regs["WALL_BAND_REGISTER"] = {
        "SCHEMA": "URBAN_R8_11_WALL_BAND_REGISTER_V1", "policy": wb_pol, "frozen_at_commit": FROZEN_COMMIT,
        "amendment_A1": wb_pol["amendments"], "frozen_v1_first_run": FROZEN_V1_RESULT,
        "means": "TOPOLOGY_OBSTACLE_GEOMETRY - not masonry, not a material quantity",
        "NEW_K2": [_band_rec(b, inp_new) for b in new["wall_bands"]["bands"]],
        "OLD_K1": [_band_rec(b, inp_old) for b in old["wall_bands"]["bands"]],
        "counts": {k: dict(Counter(b["state"] for b in r["wall_bands"]["bands"])) for k, r in (("NEW_K2", new),
                                                                                              ("OLD_K1", old))},
        "end_kinds": {k: dict(Counter(e["kind"] for b in r["wall_bands"]["bands"] for e in b["ends"]))
                      for k, r in (("NEW_K2", new), ("OLD_K1", old))},
        "cap_analysis": caps,
        "network_paired_face_corroboration": {k: dict(Counter(v["state"] for v in r["network_review"].values()))
                                              for k, r in (("NEW_K2", new), ("OLD_K1", old),
                                                           ("NEW_K2_R8_10", R["new_r810"]))}}
    regs["TOPOLOGY_CLOSURE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_11_TOPOLOGY_CLOSURE_REGISTER_V1", "policy": new["topology_closures"]["policy"],
        "NEW_K2": [_closure_rec(c, new) for c in new["topology_closures"]["closures"]],
        "OLD_K1": [_closure_rec(c, old) for c in old["topology_closures"]["closures"]],
        "applied": {k: [c["closure_id"] for c in r["topology_closures"]["closures"]
                        if c["release"] == TC.AUTHORISED_FOR_SHADOW] for k, r in (("NEW_K2", new), ("OLD_K1", old))},
        "leak": leak, "separation": ["A SOURCE GEOMETRY: never rewritten", "B TOPOLOGY CLOSURE: these records",
                                     "C SOURCE CORRECTION CLAIM: none in R8.11"],
        "material": "NONE for every closure: no wall length, wall area, plaster, paint, skirting or opening width"}
    regs["NEAR_MISS_REGISTER"] = {
        "SCHEMA": "URBAN_R8_11_NEAR_MISS_REGISTER_V1", "band_mm": RA.NEAR_MISS_REVIEW_BAND_MM,
        "basis": RA.NEAR_MISS_BASIS, "review_only": True,
        "NEW_K2_R8_10": [_nm_rec(m, inp_new) for m in nm810], "NEW_K2_R8_11": [_nm_rec(m, inp_new) for m in nm811],
        "OLD_K1_R8_11": [_nm_rec(m, inp_old) for m in old["near_misses"]["near_misses"]],
        "reading": "H2431 is still 9.2 mm short (a source fact, never edited); with the closure in place the slit "
                   "opens into nothing, so it is no longer a near-miss that changes a site. H1316 (window jamb, 1.4 mm gaps) is a near-miss in an unlabelled window "
                   "strip site that no row uses. Nothing was joined because it was < 50 mm away."}
    regs["OPEN_PASSAGE_SITE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_11_OPEN_PASSAGE_SITE_REGISTER_V1", "NEW_K2": pas_new, "OLD_K1": pas_old,
        "frozen_v1_passages": {"NEW_K2": FROZEN_V1_RESULT["NEW_K2"]["passages"],
                               "OLD_K1": FROZEN_V1_RESULT["OLD_K1"]["passages"],
                               "removed_by_A1": "every 150-200 mm strip through a receiving wall's core"},
        "qp_audit": qp_audit(pas_new, pas_old, new, inp_new),
        "no_width_rule": "a 3.45 m strip and a 1.2 m strip are both recorded: the engine applies no size rule; what a "
                         "trade does with a strip is an allocation rule (none exists: NOT_ALLOCATED)"}
    regs["THRESHOLD_SITE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_11_THRESHOLD_SITE_REGISTER_V1",
        "NEW_K2": [{"threshold": t["threshold_id"], "site": t["physical_site_id"], "opening": t["opening"],
                    "area_m2": round(_m2(new, t["area"]), 6), "sides": t["sides"], "allocation": t["allocation"]}
                   for t in new["semantic"]["thresholds"]],
        "distinction": {"DOOR_THRESHOLD_SITE": "the strip under a door leaf between two door jamb caps, closed by the "
                                               "door closure; separate TS01 site; allocation TRADE_RULE_REQUIRED",
                        "OPEN_PASSAGE_SITE": "a doorless strip through a wall line, physically connected, inside the "
                                             "adjacent site; allocation NOT_ALLOCATED",
                        "never": "a passage strip is never moved into a room to match a total; a door threshold is "
                                 "never treated as a passage"},
        "wet_rows_new": {"ROOM_FOOTPRINT_m2": rows_new["Q-03"]["value"],
                         "THRESHOLD_FOOTPRINT_m2": round(sum(t["area_m2"] for t in rows_new["Q-03"]["threshold_sites"]),
                                                         4)}}
    regs["OBJECT_FOOTPRINT_POLICY"] = {
        "SCHEMA": "URBAN_R8_11_OBJECT_FOOTPRINT_POLICY_V1", "treatments": [TR.FOOTPRINT_INCLUDED, TR.FOOTPRINT_DEDUCTED,
                                                                         TR.ROLE_REQUIRED, TR.NOT_APPLICABLE],
        "policies": [vars(CEILING_FOOTPRINT) | {"source_refs": list(CEILING_FOOTPRINT.source_refs)}],
        "CEILING": {"policy": f"{CEILING_FOOTPRINT.policy_id}@v1", "authority": C.Q14_CLAIM,
                    "reading": "the owner's Q-14 claim: ceiling footprint = the space's floor footprint with no "
                               "deduction; an object standing in the space is no deduction class"},
        "FLOOR_FINISH": {"policy": None, "state": "UNRESOLVED",
                         "searched": [f"{OWNER_RULES}: US-01..US-20, QP-01..QP-22 (QP-08 covers skirting / profile "
                                      "only: no wardrobe deduction from SKIRTING - not floor)",
                                      "data/registry/OWNER_SOURCE_CLAIMS.json (2 claims, neither about objects)",
                                      "PA08 R2 cells method (historical precedent, not authority)",
                                      "the Q-14 claim (ceiling only; never transferred to the floor)"],
                         "not_used": ["historic quantity", "desired Q-13 total", "common construction practice alone"]},
        "implicit_path": {"state": TR.IMPLICIT, "finding": "proven furniture / sanitary-fixture footprints are inside "
                                                           "every measured floor area by the topology convention (they "
                                                           "are not boundaries). For FLOOR_FINISH no authority states "
                                                           "this: recorded per row as a RELEASE blocker (SHADOW rows "
                                                           "unchanged)",
                          "rows_affected": {rid: rows_new[rid]["implicit_object_footprints"]
                                            for rid in ROWS if rows_new[rid]["implicit_object_footprints"]}},
        "role_vs_footprint": "object role (what it is) and footprint treatment (what a trade does with it) are separate "
                             "records: H1663 stays FURNITURE, the wardrobes stay ROLE_UNRESOLVED; the ceiling proceeds "
                             "through its footprint policy, the floor does not"}
    regs["SEMANTIC_CLASS_REGISTER"] = {
        "SCHEMA": "URBAN_R8_11_SEMANTIC_CLASS_REGISTER_V1",
        "rule": {"rule_id": SPACE_CLASSES.rule_id, "version": SPACE_CLASSES.version,
                 "authority": SPACE_CLASSES.authority, "refs": list(SPACE_CLASSES.source_refs),
                 "scope": SPACE_CLASSES.scope, "by_label": SPACE_CLASSES.by_label,
                 "otherwise_class": SPACE_CLASSES.otherwise_class, "scope_labels": list(SPACE_CLASSES.scope_labels)},
        "floor_treatment_by_class": FLOOR_BY_CLASS, "floor_rule": f"{FLOOR_RULE.rule_id}@v{FLOOR_RULE.version}",
        "classes_in_use": {rid: {sid: d.get("space_classes") for sid, d in rows_new[rid]["zone_decisions"].items()}
                           for rid in ("Q-03", "Q-03P", "Q-13")},
        "equivalence_with_r8_10": {rid: {"r8_10": (rows_new_810[rid]["state"], rows_new_810[rid]["value"]),
                                         "r8_11": (rows_new[rid]["state"], rows_new[rid]["value"])}
                                   for rid in ("Q-03", "Q-03P", "Q-11", "Q-12")},
        "never": "a raw label string is not a trade identity: 'Bath', 'BATH ' or 'M.B ROOM' map to no class"}
    man = new["run_manifest"]
    regs["QTO_RUN_MANIFEST"] = {"SCHEMA": "URBAN_R8_11_QTO_RUN_MANIFEST_REGISTER_V1",
                                "NEW_K2": man, "OLD_K1": old["run_manifest"],
                                "NEW_K2_WITHOUT_CLOSURES": {k: R["new_r810"]["run_manifest"][k]
                                                            for k in ("run_id", "RUN_INPUT_DIGEST")},
                                "rule": "same inputs + same claims + same policies => same RUN_INPUT_DIGEST; the code "
                                        "commit is provenance (CODE_BOUND_DIGEST), never part of the input digest"}
    sh = shuffled_digest(work)
    regs["QTO_RUN_MANIFEST"]["determinism_shuffled_source_order"] = dict(
        sh, same_digest=sh["RUN_INPUT_DIGEST"] == man["RUN_INPUT_DIGEST"],
        same_closures=sh["closures"] == sorted((c["closure_id"], c["release"])
                                               for c in new["topology_closures"]["closures"]),
        same_bands=sh["bands"] == sorted(b["band_id"] for b in new["wall_bands"]["bands"]),
        same_hall_area=sh["hall_m2"] == round(hall(new)["area_m2"], 6))
    q13, q14 = rows_new["Q-13"], rows_new["Q-14"]
    regs["Q13_STATUS"] = _row_status("Q-13", q13, rows_new_810["Q-13"], rows_old["Q-13"])
    regs["Q13_STATUS"]["sole_blocker_test"] = {
        "question": "is the floor-under-object fact the ONLY remaining Q-13 blocker?",
        "answer": "NO", "other_blockers": sorted({f"{b['class']}:{b['issue']}:{(b['detail'] or {}).get('source', '')}"
                                                  if isinstance(b["detail"], dict) else f"{b['class']}:{b['issue']}"
                                                  for x in q13["blockers"] for b in x["blockers"]
                                                  if b["issue"] != "OBJECT_FOOTPRINT_POLICY_UNRESOLVED"}),
        "consequence": "no owner question is asked in R8.11"}
    regs["Q14_STATUS"] = _row_status("Q-14", q14, rows_new_810["Q-14"], rows_old["Q-14"])
    regs["Q14_STATUS"]["path_to_computed_shadow"] = (
        "only the H2430 wall core (0.3813 m2) still blocks: under the frozen band policy its faces form no band. A "
        "fragment-aware band rule (E-R8.12-01) frozen with synthetic tests BEFORE a blind re-run is the only route "
        "that does not calibrate to this drawing; a reviewed SOURCE_CORRECTION or TOPOLOGY_CLOSURE claim is the other")
    regs["QORTUBA_R8_11_STATUS"] = {
        "SCHEMA": "URBAN_R8_11_QORTUBA_STATUS_V1",
        "scope": {"plan": CL.PLAN, "region": C.REGION_ID, "frame": C.FRAME_ID, "revision": C.REV_NEW_ID,
                  "anchor_dxf": C.NEW_DXF, "dwg_candidate": Q10.DWG_CANDIDATE, "dwg_identity": "NOT_ESTABLISHED"},
        "closure_policy": TC.POLICY_ID, "wall_band_policy": WB.POLICY_ID,
        "rows": {"NEW_K2_R8_11": rows_new,
                 "OLD_K1_R8_11": {k: {"state": v["state"], "value": v["value"], "blocker_classes": v["blocker_classes"]}
                                  for k, v in rows_old.items()},
                 "NEW_K2_R8_10_REPRODUCED": {k: {"state": v["state"], "value": v["value"]}
                                             for k, v in rows_new_810.items()},
                 "OLD_K1_R8_10_REPRODUCED": {k: {"state": v["state"], "value": v["value"]}
                                             for k, v in rows_old_810.items()}},
        "old_revision_unchanged_by_closures": {k: (rows_old[k]["state"], rows_old[k]["value"]) ==
                                               (rows_old_810[k]["state"], rows_old_810[k]["value"]) for k in ROWS},
        "hall": leak, "final": "SHADOW only: no row is FINAL"}
    ctx = {"R": R, "rows_new": rows_new, "rows_old": rows_old, "rows_new_810": rows_new_810,
           "rows_old_810": rows_old_810, "tp_new": tp_new, "caps": caps, "leak": leak}
    return regs, ctx


def _band_rec(b, inp):
    u = inp.unit_native_to_mm
    return {"band_id": b["band_id"], "faces": [handle(b["face_a"]), handle(b["face_b"])], "state": b["state"],
            "width_mm": round(b["width"] * u, 1), "overlap_mm": round((b["interval"][1] - b["interval"][0]) * u, 1),
            "ends": [{"end": e["end"], "kind": e["kind"],
                      "caps": [{"source": handle(c["source"]), "role": c["role"], "grade": c["grade"]}
                               for c in e.get("drawn_caps", [])],
                      "receiving_face": [handle(x) for x in e.get("receiving_face", [])]} for e in b["ends"]],
            "evidence": {k: (v if not isinstance(v, list) else [handle(x) if isinstance(x, str) else x for x in v])
                         for k, v in b["evidence"].items()}}


def _closure_rec(c, res):
    return {"closure_id": c["closure_id"], "band_id": c["band_id"], "kind": c["closure_kind"], "rule": c["derivation_rule"],
            "release": c["release"], "geometry": [round(v, 2) for v in c["geometry"]],
            "source_evidence": [handle(x) for x in c["source_evidence_ids"]], "authority": c["authority"],
            "physical_material": c["physical_material"], "affects_topology": c["affects_topology"],
            "affects_wall_quantity": c["affects_wall_quantity"],
            "affects_finish_quantity": c["affects_finish_quantity"], "reversible": c["reversible"],
            "corroboration": [{"source": handle(x["source"]), "role": x["role"], "grade": x["grade"]}
                              for x in c["corroboration"]],
            "safety": {"label_partition_unchanged": c["safety"].get("label_partition_unchanged"),
                       "area_balance_ok": c["safety"].get("area_balance_ok"), "passes": c["safety"].get("passes"),
                       "separated_pieces": [{"area_m2": round(p["area"] * res["_unit2"], 4),
                                             "pure_band_interior": p["pure_band_interior"], "from_site": p["from_site"],
                                             "boundary": [x if x.startswith(TC.PREFIX) else handle(x)
                                                          for x in p["boundary"]]}
                                            for p in c["safety"].get("separated_pieces", [])]}}


def _nm_rec(m, inp):
    return {"source": handle(m["source"]), "origin": m["origin"], "admitted": m.get("admitted"),
            "gap_mm": [round(g * inp.unit_native_to_mm, 2) for g in m["gaps_native"]],
            "sites": {k: v["effect"] for k, v in m["sites"].items()}}


def _row_status(rid, row, r810, old):
    return {"SCHEMA": f"URBAN_R8_11_{rid.replace('-', '')}_STATUS_V1", "row": rid, "state": row["state"],
            "value": row["value"], "blocker_classes": row["blocker_classes"], "blockers": row["blockers"],
            "sites_used": row["sites_used"], "trade_authority": row["trade_authority"],
            "footprint_authority": row["footprint_authority"], "release_blockers": row["release_blockers"],
            "r8_10": {"state": r810["state"], "value": r810["value"], "blocker_classes": r810["blocker_classes"]},
            "old_revision": {"state": old["state"], "value": old["value"]}, "final": False,
            "run_input_digest": row["run_input_digest"], "row_input_digest": row["row_input_digest"]}


def shuffled_digest(work, seed=7):
    """Determinism: shuffled source order => the same RUN_INPUT_DIGEST, closure ids and values."""
    inps, _, facts = Q10.inputs(work)
    pc, xc, _ = CL.load()
    inp = inps["NEW_K2"]
    parts = list(inp.parts)
    random.Random(seed).shuffle(parts)
    texts = list(inp.texts)
    random.Random(seed + 1).shuffle(texts)
    r = run(replace(inp, parts=tuple(parts), texts=tuple(texts)), "NEW_K2", facts, pc, xc, TC.POLICY_ID)
    return {"RUN_INPUT_DIGEST": r["run_manifest"]["RUN_INPUT_DIGEST"],
            "closures": sorted((c["closure_id"], c["release"]) for c in r["topology_closures"]["closures"]),
            "bands": sorted(b["band_id"] for b in r["wall_bands"]["bands"]),
            "hall_m2": round(hall(r)["area_m2"], 6)}


def main(work, regdir, commit=None):
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    regs, ctx = registers(work, commit)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: (v["state"], v["value"]) for k, v in ctx["rows_new"].items()}, indent=1))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
