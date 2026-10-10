"""R8.10 lab: Qortuba rebuilt from the owner claims (evidence version 2), trade treatment, six-row status.

    python3 research/external_engine_lab/r8_10_qortuba.py <work> <register_dir>

Project semantics live here only. The rebuild re-runs TS01 from the canonical input with the committed claims
(data/registry/OWNER_SOURCE_CLAIMS.json): no sandbox row is reused, no area is patched, no geometry edited.
Trade treatments come from the owner rule store (research/qs_wall_treatment_01/.../owner_rules.py: US-01, QP-07,
QP-14) and the owner's Q-14 claim - never from a room name by itself and never from a historical quantity.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_10_claims as CL                                                                     # noqa: E402
import r8_8_topology as LAB                                                                   # noqa: E402
from engine.source import canonical_input as CI, geometry_role as GR, owner_claims as OC     # noqa: E402
from engine.source import owner_scope as OS, role_authority as RA, room_topology as RT       # noqa: E402
from engine.source import text_role as TX, topology as T, trade_regions as TR                # noqa: E402

C = LAB.C
ROWS = LAB.ROUND1
DWG_CANDIDATE = "e4babbc2ded14d8b01d64fbfd4b373e6a09ba60c4490a56e6305a82c9e47171f"
UNL = "UNLABELLED_INTERNAL_SPACE"

# ---------------------------------------------------------------------------------------------- trade authority
OWNER_RULES = "research/qs_wall_treatment_01/pa08/qortuba/boq/owner_rules.py"
FLOOR_RULE = TR.TradeTreatmentRule(
    "QORTUBA-FLOOR-TREATMENT", 1, "FLOOR_FINISH", "PROJECT_OWNER_RULE (owner rule store, rank 2)",
    (f"{OWNER_RULES}: US-01 WET_SERVICE_ROOM_CERAMIC", f"{OWNER_RULES}: QP-07 QORTUBA_CERAMIC_SERVICE_ROOMS = "
     "BATH x3 + PAINTRY", f"{OWNER_RULES}: QP-14 QORTUBA_DRY_FLOOR_FINISH = PORCELAIN"),
    by_name={"BATH": "CERAMIC_WET_FLOOR", "PAINTRY": "CERAMIC_SERVICE_FLOOR"}, otherwise="PORCELAIN_DRY_FLOOR",
    object_footprints=TR.POLICY_UNRESOLVED)
ROW_TREATMENT = {"Q-03": "CERAMIC_WET_FLOOR", "Q-11": "CERAMIC_WET_FLOOR", "Q-03P": "CERAMIC_SERVICE_FLOOR",
                 "Q-12": "CERAMIC_SERVICE_FLOOR", "Q-13": "PORCELAIN_DRY_FLOOR", "Q-14": "CEILING_BY_AREA"}

BLOCKER_CLASS = {
    RA.NEAR_MISS_BOUNDARY_GAP: "PHYSICAL_TOPOLOGY", T.TOLERANCE_SENSITIVE: "PHYSICAL_TOPOLOGY",
    T.ZERO_WIDTH_SLIVER: "PHYSICAL_TOPOLOGY", T.OPENING_CLOSURE_UNRESOLVED: "PHYSICAL_TOPOLOGY",
    T.SITE_ID_COLLISION: "PHYSICAL_TOPOLOGY", "GEOS_CROSSCHECK_DISAGREES": "PHYSICAL_TOPOLOGY",
    RA.ROLE_CONFLICT_SEPARATOR: "ROLE_AUTHORITY", RA.NETWORK_ROLE_CONFLICT: "ROLE_AUTHORITY",
    T.TOPOLOGY_ROLE_UNRESOLVED: "ROLE_AUTHORITY",
    TX.TEXT_ROLE_UNRESOLVED_IN_SITE: "SEMANTIC_ZONE", T.LABEL_ON_BOUNDARY: "SEMANTIC_ZONE",
    T.LABEL_OCCURRENCE_SPLIT: "SEMANTIC_ZONE",
    OC.XREF_MISSING_POTENTIALLY_CONTRIBUTING: "SOURCE_COMPLETENESS", "REGION_REVIEW_REQUIRED": "SOURCE_COMPLETENESS",
    "OCCURRENCE_REVIEW_REQUIRED": "SOURCE_COMPLETENESS", "UNREALISED_ENTITY_POSSIBLY_IN_SITE": "SOURCE_COMPLETENESS",
    "UNREALISED_ENTITY_ON_BOUNDARY_LAYER": "SOURCE_COMPLETENESS", "UNREALISED_ENTITY_LAYER_UNKNOWN": "SOURCE_COMPLETENESS"}
STATE_OF = {"PHYSICAL_TOPOLOGY": "BLOCKED_PHYSICAL", "ROLE_AUTHORITY": "BLOCKED_ROLE",
            "SEMANTIC_ZONE": "BLOCKED_SEMANTIC_ZONE", "TRADE_RULE": "BLOCKED_TRADE_RULE",
            "SOURCE_COMPLETENESS": "BLOCKED_SOURCE_COMPLETENESS", "SOURCE_ANCHOR": "BLOCKED_SOURCE_ANCHOR",
            "OWNER_FACT": "BLOCKED_OWNER_FACT"}


def ceiling_rule():
    c = C.claims()[C.Q14_CLAIM]
    return TR.TradeTreatmentRule(
        "QORTUBA-Q14-CEILING-TREATMENT", 1, "CEILING", "OWNER_CLAIM", (C.Q14_CLAIM,),
        otherwise="CEILING_BY_AREA", object_footprints=TR.NOT_DEDUCTED,
        scope_names=tuple(sorted({n for sid in c.space_ids for n in sid.split(" / ")})))


def handle(key):
    return key.split("|")[1][1:] if key and "|" in key else key


def m2(res, a):
    return a * res["_unit2"]


# ---------------------------------------------------------------------------------------------- inputs / runs
def inputs(work):
    inps = LAB.inputs(Path(work))
    all_new = inps.pop("_NEW_ALL_PARTS")
    facts = CL.xref_occurrence_facts(LAB.NEW_DXF, Path(work) / "xref_facts_new.json")
    return inps, all_new, facts


def run(inp, name, facts, part_claims=(), xref_claims=()):
    u = CL.attach_xref_facts(LAB.UNREALISED[name], facts)
    r = LAB.run(inp, u, part_claims=part_claims, xref_claims=xref_claims)
    r["_unit2"] = (inp.unit_native_to_mm ** 2) / 1e6
    return r


# ---------------------------------------------------------------------------------------------- the trade layer
def site_zone_names(s, names, internal):
    if s["site_id"] in internal:
        return [UNL]
    return sorted({n for st in LAB.site_names(s, names) for n in st})


def materiality(s, rule, res):
    """Trade materiality of the unknown-role objects of one site (None when the site has none). Every blocking
    source must have been IN the diagnostic arrangement (an analysed unknown candidate): parts that end on no
    diagnostic boundary were analysed and changed nothing."""
    if T.TOPOLOGY_ROLE_UNRESOLVED not in s["issues"] and RA.UNKNOWN_OBJECT_IN_SITE not in s["issues"]:
        return None
    un = (s.get("consequence") or {}).get("unknown")
    srcs = set(s.get("blocked_by", []))
    analysed = {c.source_id for c, o in res["roles"]["separator_candidates"] if o == "UNKNOWN"}
    if any(c.source_id in srcs and c.role == RA.UNCONNECTED_BOUNDARY_CANDIDATE
           for c, o in res["roles"]["separator_candidates"]):
        return {"state": TR.MATERIAL, "why": "an unconnected wall-layer candidate could be a wall", "sources": sorted(srcs)}
    if srcs - analysed:
        return {"state": TR.MATERIAL, "why": "blocking sources the consequence analysis did not include (closed "
                                             "curves / non-linear): not analysed, so not cleared",
                "sources": sorted(srcs - analysed)}
    m = TR.object_materiality(un, rule)
    return dict(m, sources=sorted(srcs))


def site_decision(s, rid, rule, names, internal, res):
    """(selected?, blockers [(class, issue, detail)], decision record) of one apartment site for one row."""
    zn = site_zone_names(s, names, internal)
    sem_state = res["semantic"]["sites"].get(s["site_id"], {}).get("state", "")
    dec = TR.zone_decision(zn, rule, unresolved_texts=[t["value"] for t in s.get("unresolved_texts", [])],
                           authored_trade_boundary="MULTIPLE_SEMANTIC_ZONES_ESTABLISHED" in sem_state)
    treats = set(v for v in dec["treatments"].values() if v)
    want = ROW_TREATMENT[rid]
    if want not in treats and dec["state"] not in (TR.UNRESOLVED,):
        return False, [], dec
    if not treats and dec["state"] == TR.UNRESOLVED:
        return False, [], dec
    bl = []
    if dec["state"] == TR.REQUIRED:
        bl.append(("SEMANTIC_ZONE", T.MULTIPLE_SEMANTIC_LABELS, dec["why"]))
    elif dec["state"] == TR.UNRESOLVED:
        bl.append(("SEMANTIC_ZONE" if dec["unresolved_texts"] else "TRADE_RULE", "TRADE_TREATMENT_UNRESOLVED",
                   dec["why"]))
    mat = materiality(s, rule, res)
    for iss in s["issues"]:
        if iss in (T.MULTIPLE_SEMANTIC_LABELS, RA.UNKNOWN_OBJECT_IN_SITE):
            continue
        if iss == T.TOPOLOGY_ROLE_UNRESOLVED:
            if mat and mat["state"] == TR.NON_MATERIAL:
                continue
            bl.append(("ROLE_AUTHORITY", iss, [handle(x) for x in (mat or {}).get("sources", s["blocked_by"])][:12]))
            if mat and "no authority says how this trade treats an object footprint" in mat["why"]:
                bl.append(("TRADE_RULE", "OBJECT_FOOTPRINT_POLICY_UNRESOLVED", f"{rule.rule_id}: {mat['why']}"))
            continue
        cls = BLOCKER_CLASS.get(iss, "PHYSICAL_TOPOLOGY")
        detail = None
        if iss == RA.NEAR_MISS_BOUNDARY_GAP:
            detail = [{"source": handle(m["source"]), "gap_mm": [round(g * res["_unit_mm"], 2)
                                                                for g in m["gaps_native"]]} for m in s["near_miss"]]
        elif iss == RA.ROLE_CONFLICT_SEPARATOR:
            ex = (s.get("consequence") or {}).get("exclusion", {})
            detail = {"origins": ex.get("origins"), "sources": [handle(x) for x in ex.get("sources", [])]}
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
    dec = dict(dec, object_materiality=mat)
    return True, bl, dec


def rows_r810(res, revision_id, claims_used=()):
    names = LAB.apartment_names()
    lab_sites, internal_sites = LAB.apartment_sites(res)
    internal = {s["site_id"] for s in internal_sites}
    res["_revision_id"] = revision_id
    zones = res["semantic"]["zones"]
    th = res["semantic"]["thresholds"]
    out = {}
    for rid in ROWS:
        rule = ceiling_rule() if rid == "Q-14" else FLOOR_RULE
        used, blockers, decisions = [], [], {}
        for s in sorted(lab_sites + internal_sites, key=lambda z: z["site_id"]):
            sel, bl, dec = site_decision(s, rid, rule, names, internal, res)
            if not sel:
                continue
            decisions[s["site_id"]] = dec
            if bl:
                blockers.append({"site": s["site_id"], "zones": site_zone_names(s, names, internal),
                                 "area_m2": round(s["area_m2"], 6),
                                 "blockers": [{"class": c, "issue": i, "detail": d} for c, i, d in bl]})
            else:
                used.append({"site": s["site_id"], "zones": site_zone_names(s, names, internal),
                             "area_m2": round(s["area_m2"], 6), "decision": dec["state"]})
        classes = sorted({b["class"] for x in blockers for b in x["blockers"]})
        state = ("COMPUTED_SHADOW" if used and not classes else
                 "NO_SITE" if not used and not classes else
                 STATE_OF[classes[0]] if len(classes) == 1 else
                 "BLOCKED_MULTIPLE: " + ", ".join(STATE_OF[c] for c in classes))
        sids = {u["site"] for u in used} | {b["site"] for b in blockers}
        dimkeys = {k for c in claims_used for k in c.get("applied_parts", [])}
        role_claims = sorted({c["claim_id"] for c in claims_used for s_ in res["sites"] if s_["site_id"] in sids
                              and dimkeys & set(s_["boundary_source_ids"])})
        out[rid] = {
            "state": state, "value": round(sum(u["area_m2"] for u in used), 4) if state == "COMPUTED_SHADOW" else None,
            "physical_site_ids": sorted(sids), "sites_used": used, "blockers": blockers,
            "blocker_classes": classes, "trade_authority": {"rule": f"{rule.rule_id}@v{rule.version}",
                                                            "authority": rule.authority, "refs": list(rule.source_refs),
                                                            "row_treatment": ROW_TREATMENT[rid]},
            "zone_decisions": decisions,
            "semantic_zone_ids": sorted(z["zone_id"] for z in zones if z["physical_site_id"] in sids),
            "threshold_treatment": [{"threshold": t["threshold_id"], "site": t["physical_site_id"], "opening": t["opening"],
                                     "area_m2": round(m2(res, t["area"]), 6), "sides": t["sides"],
                                     "allocation": t["allocation"]} for t in th if sids & set(t["sides"])],
            "role_claims_used": role_claims,
            "migration_blockers": ["SOURCE_ANCHOR: the claims and the measurement are anchored to the DXF "
                                   f"{C.NEW_DXF[:12]}...; DWG {DWG_CANDIDATE[:12]}... identity NOT_ESTABLISHED"]
            if revision_id == C.REV_NEW_ID else []}
    return out


# ---------------------------------------------------------------------------------------------- investigations
def dim_wall_effect(new, r_before, r_after, claim_status):
    by_b = {s["site_id"]: s for s in r_before["sites"]}
    grades = r_after["roles"]["grades"]
    keys = claim_status["applied_parts"]
    lab = {s["site_id"]: s for s in r_after["sites"] if s["labels"]}
    touching = sorted({s["site_id"] for s in r_after["sites"] for k in keys if k in s["boundary_source_ids"]})
    adj = [a for a in r_after["opening_adjacency"] if set(a["sites"]) & set(touching)]
    dims = [p for p in new.parts if p.layer == "DIM"]
    roles = r_after["roles"]["roles"]
    merged_before = [s for s in r_before["sites"] if s["labels"] and len(LAB.stamps(s)) >= 3]
    return {
        "claim": claim_status["claim_id"], "parts": [
            {"handle": handle(k), "source_layer": next(p.layer for p in new.parts if p.identity.key == k),
             "role_now": roles[k].role, "rule": roles[k].rule_id, "role_before": roles[k].evidence.get("ROLE_BEFORE"),
             "authority_grade": grades.get(k, {}).get("grade"), "connected_ends": grades.get(k, {}).get("connected_ends")}
            for k in keys],
        "before_r8_9": [{"site": s["site_id"], "area_m2": round(s["area_m2"], 4), "stamps": list(LAB.stamps(s).values()),
                         "issues": s["issues"]} for s in merged_before],
        "after": [{"site": sid, "area_m2": round(lab[sid]["area_m2"], 4) if sid in lab else
                   round(next(s for s in r_after["sites"] if s["site_id"] == sid)["area_m2"], 4),
                   "stamps": list(LAB.stamps(lab[sid]).values()) if sid in lab else [],
                   "physical_status": next(s for s in r_after["sites"] if s["site_id"] == sid)["physical_status"],
                   "issues": next(s for s in r_after["sites"] if s["site_id"] == sid)["issues"]} for sid in touching],
        "opening_adjacency": adj,
        "other_dim_layer_parts": dict(Counter(roles[p.identity.key].role for p in dims if p.identity.key not in keys)),
        "other_dim_parts_admitted": sum(1 for p in dims if p.identity.key not in keys
                                        and roles[p.identity.key].role in GR.TOPOLOGY_ADMITTED),
        "reading": "BATH (5.1 m2, the 7116 / 7117 side) and BED.ROOM (19.2725 m2, the 7118 / 7119 side) are separate "
                   "physical sites again; the HALL is no longer merged with them. Every other DIM-layer part keeps its "
                   "dimension role"}


def hall_lobby_caps(new, r_after):
    """The Hall / Lobby passage wall ends drawn on the DIM layer (H2430 exact, H2431 9.2 mm short)."""
    roles = r_after["roles"]["roles"]
    out = []
    for h in ("2430", "2431"):
        p = next(q for q in new.parts if q.identity.source_handle == h and not q.identity.instance_handles)
        g = p.geometry
        out.append({"handle": h, "layer": p.layer, "role": roles[p.identity.key].role, "geometry": [round(v, 2) for v in g],
                    "length_mm": round(math.hypot(g[2] - g[0], g[3] - g[1]) * new.unit_native_to_mm, 1)})
    nm = [m for m in r_after["near_misses"]["near_misses"] if handle(m["source"]) == "2431"]
    hall = next(s for s in r_after["sites"] if any("HALL" in v for v in LAB.stamps(s).values()))
    ex = (hall.get("consequence") or {}).get("exclusion", {})
    sep = r_after["separators"]["exclusion"]["sites"].get(hall["site_id"], {})

    def pockets(entry):
        hyp = sorted(entry.get("hypothetical_sites", []), key=lambda z: -z["area"])
        return [round(h["area"] * r_after["_unit2"], 4) for h in hyp[1:] if not h["labels_inside"]]
    leak = {"exclusion_group_pockets_m2": pockets(sep),
            "exclusion_group_reading": "the HALL's exclusion group is H2430 (DIM cap: the 0.3813 m2 wall core) and "
                                       "H1663 (B-FURNI dining set touching the wall: the 2.3914 m2 pocket - an object "
                                       "against a wall, a trade note, never a wall)",
            "h2431_near_miss_pockets_m2": pockets(nm[0]["sites"][hall["site_id"]]) if nm else []}
    return {"caps": out, "old_revision": "the old revision capped this wall band on the WALL layer at x = 109808.08 "
                                         "(H553); the new revision moved the passage and drew both caps on DIM",
            "passage_between_caps_mm": round((109893.45 - 109773.76) * new.unit_native_to_mm, 1),
            "owner_rule_corroboration": "QP-17: the owner identified a 1.200 m open passage between the Hall and the "
                                        "Lobby (old revision); QP-18: OPEN_PASSAGE_FULL_HEIGHT",
            "h2430": "an exact wall-end cap; excluded by layer, so the HALL site includes the wall core it closes "
                     "(ROLE_CONFLICT_SEPARATOR; the diagnostic arrangement separates a 0.3813 m2 core)",
            "h2431": "9.2 mm short of the face it should meet: even a claim could not close it without editing "
                     "geometry; the NEAR_MISS check (R8.10) now flags the leak that was silent",
            "near_miss": [{k: v for k, v in m.items() if k != "sites"} for m in nm], "leak_areas": leak,
            "hall_issues": hall["issues"], "hall_exclusion_consequence": ex,
            "not_claimed": "the owner's DIM-wall claim names 7116-7119 only; it is not extended to these caps"}


def mb_dress(new, r_after, rows):
    s = next(z for z in r_after["sites"] if set(n for v in LAB.stamps(z).values() for n in v) >= {"M.B.ROOM", "DRESS"})
    core = next(z for z in r_after["sites"] if z["site_id"] == "SITE-c016d9fe4a46e164")
    width = core["bbox"][2] - core["bbox"][0]
    gap = core["bbox"][1] - s["bbox"][1]
    return {
        "site": s["site_id"], "area_m2": round(s["area_m2"], 4), "stamps": list(LAB.stamps(s).values()),
        "physical_status": s["physical_status"], "issues": s["issues"],
        "semantic_state": r_after["semantic"]["sites"][s["site_id"]]["state"],
        "correction_of_r8_9": "R8.9 said no wall separates DRESS from M.B.ROOM. The source has a WALL-layer stub (core "
                              f"site {core['site_id']}, {width * 10:.0f} x {(core['bbox'][3] - core['bbox'][1]) * 10:.0f}"
                              f" mm) ending {gap * 10:.0f} mm short of the opposite face: an authored partition with "
                              "an open passage. TS01 keeps ONE physical site (an open passage is not closed)",
        "passage": {"width_mm": round(gap * 10, 1), "wall_thickness_mm": round(width * 10, 1),
                    "strip_m2": round(width * gap * r_after["_unit2"], 4),
                    "owner_rule": "QP-17 / QP-18 / QP-19: open passage WITH HEAD at 2.200 m (old revision)",
                    "treatment": "the strip is part of the whole-site footprint (no closure exists); a door threshold "
                                 "is its own site - the two are not yet treated alike: POSSIBLE_FINISH_FOOTPRINT, "
                                 "allocation TRADE_RULE_REQUIRED, no value moved"},
        "Q-13": {"A_same_authoritative_treatment": rows["Q-13"]["zone_decisions"].get(s["site_id"], {}).get("treatments"),
                 "B_internal_finish_boundary": "NONE in the source (no GR-18 finish / zone line in the site)",
                 "C_trade_specific_exclusion_differs": "NONE stated by any authority",
                 "D_unknown_geometry_material_to_floor": rows["Q-13"]["zone_decisions"].get(s["site_id"], {})
                 .get("object_materiality")},
        "Q-14": {"A_same_authoritative_treatment": rows["Q-14"]["zone_decisions"].get(s["site_id"], {}).get("treatments"),
                 "object_materiality": rows["Q-14"]["zone_decisions"].get(s["site_id"], {}).get("object_materiality"),
                 "head_soffit_note": "the passage has a 2.200 m head: under US-07 its soffit is a plaster / paint "
                                     "reveal; the owner's Q-14 claim (ceiling = floor footprint, no deductions) "
                                     "governs Q-14 - a possible cross-trade overlap to review, not a Q-14 change"}}


def materiality_register(r_after, rows):
    out = {}
    for name, keys in (("FIRNTUR", ("1445", "1446", "1669", "1670", "514", "517")),):
        out[name] = {"role": "ROLE_UNRESOLVED (SOURCE_EVIDENCE_CANDIDATE: built-in wardrobe joinery, 600 mm deep "
                             "rectangle-with-diagonal symbols in DRESS; never an Urban-wide dictionary entry)",
                     "parts": list(keys)}
    out["SF3_PM"] = {"role": "ROLE_UNRESOLVED (SOURCE_EVIDENCE_CANDIDATE: sofa outline from the bound 'MY BLOCKS' "
                             "library; the library is mixed - 958 blocks incl. doors, title blocks, floors - so "
                             "membership is not furniture evidence)",
                     "occurrences": ["700047", "700051", "700052"]}
    per = {}
    for rid in ("Q-13", "Q-14"):
        for sid, d in rows[rid]["zone_decisions"].items():
            m = d.get("object_materiality")
            if m:
                per.setdefault(sid, {})[rid] = {"state": m["state"], "why": m["why"],
                                                "sources": [handle(x) for x in m.get("sources", [])][:20]}
    return {"objects": out, "per_site_per_trade": per,
            "rule": "global role truth and trade materiality are separate records: an object may stay ROLE_UNRESOLVED "
                    "while a trade that measures the whole footprint proceeds"}


# ---------------------------------------------------------------------------------------------- registers
def registers(work):
    inps, all_new, facts = inputs(work)
    pc, xc, raw = CL.load()
    new, old = inps["NEW_K2"], inps["OLD_K1"]
    r89 = run(new, "NEW_K2", facts)                                          # no claims: the R8.9 state
    r_new = run(new, "NEW_K2", facts, pc, xc)                                 # evidence version 2
    r_old = run(old, "OLD_K1", facts, pc, xc)                                 # claims never transfer
    for r, inp in ((r89, new), (r_new, new), (r_old, old)):
        r["_unit_mm"] = inp.unit_native_to_mm
    rows_new = rows_r810(r_new, C.REV_NEW_ID, r_new["owner_claims"]["part_claims"])
    rows_old = rows_r810(r_old, C.REV_OLD_ID)
    rows_89 = rows_r810(r89, C.REV_NEW_ID)
    st = r_new["owner_claims"]["part_claims"][0]
    inv = OC.xref_inventory(facts, r_new["unrealised"])
    regs = {}
    regs["OWNER_CLAIM_REGISTER"] = {
        "SCHEMA": "URBAN_R8_10_OWNER_CLAIM_REGISTER_V1", "evidence_file": str(CL.CLAIMS.relative_to(ROOT)),
        "evidence_file_sha256": CL.sha(CL.CLAIMS), "evidence_version": raw["evidence_version"],
        "previous_evidence_version": raw["previous_evidence_version"], "binding_policy": OC.policy_record(),
        "claims": [{"claim_id": c["claim_id"], "version": c["version"], "kind": c["kind"], "authority": c["authority"],
                    "scope": c["scope"], "review_state": c["review_state"], "status": c["status"]} for c in raw["claims"]],
        "flow": ["OWNER ANSWER (R8.10 brief)", "VERSIONED CLAIM (data/registry/OWNER_SOURCE_CLAIMS.json)",
                 "NEW EVIDENCE VERSION (2)", "CANONICAL INPUT (unchanged records)", "ROLE ADMISSION (part claims)",
                 "TS01", "SEMANTIC ZONES", "TRADE REGIONS", "SHADOW QUANTITIES", "QA"],
        "run_evidence_versions": {"NEW_K2_without_claims": r89["owner_claims"]["evidence_version"],
                                  "NEW_K2_evidence_v2": r_new["owner_claims"]["evidence_version"],
                                  "OLD_K1_with_claims_offered": r_old["owner_claims"]["evidence_version"]},
        "application": {"NEW_K2": r_new["owner_claims"]["part_claims"],
                        "OLD_K1": r_old["owner_claims"]["part_claims"]},
        "quantity_edits_by_claims": 0}
    regs["XREF_SCOPE_CLAIMS"] = {
        "SCHEMA": "URBAN_R8_10_XREF_SCOPE_CLAIMS_V1", "claim": CL.XREF_ID, "four_state_model": list(OC.XREF_STATES),
        "occurrences_in_source": facts, "inventory_new_revision": inv,
        "blocking_unrealised_after_claim": [{"code": b["code"], "obs_id": b["obs_id"], "disposition": b["disposition"]}
                                            for b in r_new["unrealised"]["blocking_input"]],
        "unrealised_records_total": len(LAB.UNREALISED["NEW_K2"]),
        "unrealised_dispositions": dict(Counter(x["disposition"] for x in r_new["unrealised"]["recorded"])),
        "source_complete": "NOT DECLARED: two occurrences were cleared for THIS region; the file as a whole is not "
                           "declared source-complete",
        "old_revision": "no xref in the old revision"}
    regs["DIM_WALL_CLAIMS"] = {"SCHEMA": "URBAN_R8_10_DIM_WALL_CLAIMS_V1", "claim_status": st,
                               "effect": dim_wall_effect(new, r89, r_new, st),
                               "old_revision": r_old["owner_claims"]["part_claims"][0],
                               "hall_lobby_caps": hall_lobby_caps(new, r_new)}
    fl = FLOOR_RULE
    regs["TRADE_SEMANTIC_EQUIVALENCE"] = {
        "SCHEMA": "URBAN_R8_10_TRADE_SEMANTIC_EQUIVALENCE_V1", "policy": TR.policy_record(),
        "design": "TRADE TREATMENT ASSIGNMENT: equivalence is derived (one treatment per trade from an authority "
                  "record), never declared between room names",
        "rules": {fl.rule_id: {"trade": fl.trade, "authority": fl.authority, "refs": list(fl.source_refs),
                               "by_name": fl.by_name, "otherwise": fl.otherwise,
                               "object_footprints": fl.object_footprints,
                               "otherwise_reading": "QP-07 enumerates the ceramic rooms of this project (BATH x3 + "
                                                    "PAINTRY); QP-14 sets the dry internal floor finish: every other "
                                                    "established apartment room is a dry internal room"},
                  ceiling_rule().rule_id: {"trade": "CEILING", "authority": "OWNER_CLAIM", "refs": [C.Q14_CLAIM],
                                           "otherwise": "CEILING_BY_AREA", "scope_names": list(ceiling_rule().scope_names),
                                           "object_footprints": TR.NOT_DEDUCTED,
                                           "object_reading": "the claim fixes ceiling footprint = the space's floor "
                                                             "footprint (the wall-bounded site) with NO deduction for "
                                                             "void / stair opening / shaft / open-to-above; an object "
                                                             "standing inside a space is no deduction class of it"}},
        "never_used": ["historical BOQ quantities (LEGACY values are not evidence)", "room names alone"],
        "decisions": {rid: rows_new[rid]["zone_decisions"] for rid in ("Q-13", "Q-14")}}
    regs["UNRESOLVED_ROLE_MATERIALITY"] = dict({"SCHEMA": "URBAN_R8_10_UNRESOLVED_ROLE_MATERIALITY_V1"},
                                               **materiality_register(r_new, rows_new))
    dup = TR.duplicate_occurrences(new)
    regs["DUPLICATE_OCCURRENCE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_10_DUPLICATE_OCCURRENCE_REGISTER_V1", "groups": dup,
        "sf3": [g for g in dup if "SF3" in (g["block"] or "")],
        "rule": "never deleted; coincident geometry has no area effect; a count trade needs COUNT_RULE_REQUIRED"}
    regs["THRESHOLD_SITE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_10_THRESHOLD_SITE_REGISTER_V1",
        "old_revision_wet_rows": {"ROOM_FOOTPRINT_m2": rows_old["Q-03"]["value"],
                                  "THRESHOLD_FOOTPRINT_m2": round(sum(t["area_m2"] for t in rows_old["Q-03"]
                                                                      ["threshold_treatment"]), 4),
                                  "POSSIBLE_FINISH_FOOTPRINT_m2": round((rows_old["Q-03"]["value"] or 0) + sum(
                                      t["area_m2"] for t in rows_old["Q-03"]["threshold_treatment"]), 4),
                                  "legacy_qs01_wet_floor_m2": LAB.LEGACY["OLD"]["Q-03"],
                                  "legacy_minus_room_m2": round(LAB.LEGACY["OLD"]["Q-03"] - (rows_old["Q-03"]["value"]
                                                                                            or 0), 4),
                                  "reading": "three wet-room door strips of 0.12 m2 exist; the legacy QS01 wet floor "
                                             "exceeds the TS01 room footprint by exactly ONE of them: the legacy "
                                             "method absorbed one strip into a room. TS01 keeps all three separate "
                                             "(allocation TRADE_RULE_REQUIRED); no strip is moved to match a total",
                                  "thresholds": rows_old["Q-03"]["threshold_treatment"]},
        "new_revision_wet_rows": {"ROOM_FOOTPRINT_m2": rows_new["Q-03"]["value"],
                                  "THRESHOLD_FOOTPRINT_m2": round(sum(t["area_m2"] for t in rows_new["Q-03"]
                                                                      ["threshold_treatment"]), 4),
                                  "POSSIBLE_FINISH_FOOTPRINT_m2": round((rows_new["Q-03"]["value"] or 0) + sum(
                                      t["area_m2"] for t in rows_new["Q-03"]["threshold_treatment"]), 4),
                                  "thresholds": rows_new["Q-03"]["threshold_treatment"]},
        "all_new_thresholds": [{"threshold": t["threshold_id"], "site": t["physical_site_id"], "opening": t["opening"],
                                "area_m2": round(m2(r_new, t["area"]), 6), "sides": t["sides"],
                                "allocation": t["allocation"]} for t in r_new["semantic"]["thresholds"]],
        "passage_strips": {"M.B.ROOM / DRESS": mb_dress(new, r_new, rows_new)["passage"],
                           "HALL / LOBBY": {"width_mm": round((109893.45 - 109773.76) * 10, 1),
                                            "wall_thickness_mm": 200.0,
                                            "strip_m2": round((109893.45 - 109773.76) * 20 * r_new["_unit2"], 4),
                                            "owner_rule": "QP-17 / QP-18: open passage FULL HEIGHT (old revision)"}},
        "allocation": "TRADE_RULE_REQUIRED - no authoritative rule answers it; the strip is never moved into a room to "
                      "match a total; the owner is not asked (not the only remaining issue)"}
    net = r_new["network_review"]
    regs["ROLE_AUTHORITY_ADVERSARIAL"] = {
        "SCHEMA": "URBAN_R8_10_ROLE_AUTHORITY_ADVERSARIAL_V1",
        "network_review_states": {"NEW_K2": dict(Counter(v["state"] for v in net.values())),
                                  "OLD_K1": dict(Counter(v["state"] for v in r_old["network_review"].values()))},
        "near_misses": {"NEW_K2": [{"source": handle(m["source"]), "origin": m["origin"],
                                    "gap_mm": [round(g * new.unit_native_to_mm, 2) for g in m["gaps_native"]],
                                    "sites": {k: v["effect"] for k, v in m["sites"].items()}}
                                   for m in r_new["near_misses"]["near_misses"]],
                        "OLD_K1": [handle(m["source"]) for m in r_old["near_misses"]["near_misses"]],
                        "band_mm": RA.NEAR_MISS_REVIEW_BAND_MM, "basis": RA.NEAR_MISS_BASIS},
        "finding_dimension_coincidence": "rejected as a conflict signal: five old-revision walls (H1323, H1516, H2060 "
                                         "x2, H462) are dimensioned corner to corner; coincidence = being measured",
        "tests": "tests/r8_10/test_r8_10_adversarial.py (A-F, A2, near-miss, consequence-is-not-authority)",
        "verdict": {"NETWORK alone": "NOT sufficient against A / B / C on single-line drawings: recorded as "
                                     "NETWORK_BOUNDARY_CANDIDATE (residual risk, stated)",
                    "corroborated": "NETWORK_BOUNDARY_ESTABLISHED when it separates two different label occurrences "
                                    "or a reviewed claim names it",
                    "contrary": "NETWORK_ROLE_CONFLICT for a self-dimensioned line (its own length printed at its "
                                "middle)",
                    "next": "a wall-band model (paired faces, measured thickness population of THIS drawing) is the "
                            "missing authority to make CANDIDATE blocking without false positives (R8.11)"}}
    ctx = {k: dict(Counter(v["context"] for v in r["roles"]["occurrence_contexts"].values()))
           for k, r in (("NEW_K2", r_new), ("OLD_K1", r_old))}
    regs["BUILDING_ASSEMBLY_ADVERSARIAL"] = {
        "SCHEMA": "URBAN_R8_10_BUILDING_ASSEMBLY_ADVERSARIAL_V1", "rule": RA.ASSEMBLY_RULE,
        "real_drawings": ctx, "real_assemblies_before_and_after": "none in either Qortuba revision (or P7757): the "
                                                                   "stronger rule changes no real result",
        "tests": ["detail callout + title -> UNKNOWN (fail closed)", "window detail + dimensions -> UNKNOWN",
                  "fixture block + label -> SYMBOL", "room-detail block (1 room, 1 label) -> UNKNOWN",
                  "full floor-plan block -> BUILDING_ASSEMBLY", "bound xref floor plan -> BUILDING_ASSEMBLY",
                  "wall children closing no cycle -> UNKNOWN"],
        "size_used": False}
    tr_new = r_new["roles"]["text_roles"]
    vals = {t.identity.key: t.value for t in new.texts}
    regs["TEXT_TAG_ADVERSARIAL"] = {
        "SCHEMA": "URBAN_R8_10_TEXT_TAG_ADVERSARIAL_V1", "policy": TX.policy_record(),
        "qortuba_new": dict(Counter(f"{v.role} | {v.rule_id}" for v in tr_new.values())),
        "qortuba_new_r8_9": {"ROOM_LABEL_ESTABLISHED | TR-03": 18, "ROOM_LABEL_ESTABLISHED | TR-04": 2},
        "changed_by_v2": sorted({vals[k] for k, v in tr_new.items() if v.rule_id == "TR-06"}),
        "paintry": sorted({v.rule_id for k, v in tr_new.items() if vals.get(k) == "PAINTRY"}),
        "reading": "the ROOF tag (ROOF + its Arabic text) has a composition no other room uses: it is now a candidate "
                   "(outside the apartment; no row changes). PAINTRY stays TR-04 through its family",
        "false_positive_tests": ["BATHROOM DETAIL", "BEDROOM FINISH NOTE", "MASTER BEDROOM CEILING DETAIL",
                                 "ROOM AREA", "ROOM TYPE"]}
    regs["QORTUBA_R8_10_STATUS"] = {
        "SCHEMA": "URBAN_R8_10_QORTUBA_STATUS_V1", "scope": {"plan": CL.PLAN, "region": C.REGION_ID,
                                                            "frame": C.FRAME_ID, "revision": C.REV_NEW_ID,
                                                            "anchor_dxf": C.NEW_DXF, "dwg_identity": "NOT_ESTABLISHED"},
        "other_variants": "PLAN_VARIANT_1..3 not measured (variant isolation as R8.8); miscellaneous blocks / details "
                          "outside the region are OUTSIDE_SELECTED_MEASUREMENT_REGION",
        "evidence_version": r_new["owner_claims"]["evidence_version"],
        "rows": {"NEW_K2_R8_10": rows_new, "OLD_K1_R8_10": {k: {"state": v["state"], "value": v["value"],
                                                                "blocker_classes": v["blocker_classes"]}
                                                            for k, v in rows_old.items()},
                 "NEW_K2_WITHOUT_CLAIMS_R8_9_EQUIVALENT": {k: {"state": v["state"], "value": v["value"]}
                                                           for k, v in rows_89.items()}},
        "r8_9_wording_corrected": "R8.9 implied that the two owner answers could unblock all new-revision rows. Its own "
                                  "sandbox showed Q-03 / Q-03P / Q-11 / Q-12 potentially computable and Q-13 / Q-14 "
                                  "with further blockers; R8.10's rebuild confirms exactly that",
        "m_b_room_dress": mb_dress(new, r_new, rows_new),
        "labelled_sites": [{"site": s["site_id"], "area_m2": round(s["area_m2"], 4), "stamps": list(LAB.stamps(s).values()),
                            "physical_status": s["physical_status"], "issues": s["issues"]}
                           for s in sorted(r_new["sites"], key=lambda z: -z["area"]) if s["labels"]],
        "final": "SHADOW only: no row is FINAL; source anchor, baseline approval, migration transaction and release "
                 "gates are separate"}
    return regs, {"new": r_new, "old": r_old, "r89": r89, "rows_new": rows_new, "rows_old": rows_old}


def main(work, regdir):
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    regs, ctx = registers(work)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: (v["state"], v["value"]) for k, v in ctx["rows_new"].items()}, indent=1))
    print(json.dumps({k: (v["state"], v["value"]) for k, v in ctx["rows_old"].items()}, indent=1))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:3])
