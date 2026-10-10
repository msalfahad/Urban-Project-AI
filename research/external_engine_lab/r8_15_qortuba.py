"""R8.15 lab: Qortuba AFTER the frozen skirting blind run - the six rows rebuilt from the TS01 sites with the duct as
owner obstacle authority, marble thresholds (Urban wet / service rule + the explicit entrance fact), the
M.B.ROOM / DRESS passage FULL HEIGHT, the Hall / Lobby soffit out of the ceiling, the skirting row, reveals.

    python3 research/external_engine_lab/r8_15_qortuba.py <work> <register_dir> [code_commit]

Owner facts enter ONLY the trade / authority layers, after the frozen V5 topology. Project semantics live here only.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_14_qortuba as R14                                                                   # noqa: E402
import r8_15_skirting_blind as SB                                                             # noqa: E402
from engine.source import door_transition as DT, marble_thresholds as MT, obstacle_authority as OA  # noqa: E402
from engine.source import opening_reveals as OR, owner_facts as OF, owner_method_facts as MF  # noqa: E402
from engine.source import run_manifest as RM, trade_strips as TS, wall_bands as WB, wall_contact_path as WC  # noqa

Q11, R13, LAB, C = R14.Q11, R14.R13, R14.LAB, R14.C
ROWS = R14.ROWS
REG15 = ROOT / "tests/r8_15/registers"
RULES = ROOT / "data/registry/URBAN_OWNER_METHOD_RULES.json"
DUCT, MBD, ENTR = ("QORTUBA-NEW-BED-ROOM-DUCT-OWNER-001", "QORTUBA-NEW-MB-DRESS-PASSAGE-FULL-HEIGHT-OWNER-001",
                   "QORTUBA-NEW-MAIN-ENTRANCE-MARBLE-OWNER-001")
OUTSIDE = R14.OUTSIDE_UNIT
handle = R14.handle
# room types for the MARBLE trade (trade-scoped): exact labels only; QP-07's PAINTRY = kitchen equivalence is scoped
# to the CERAMIC takeoff and is NOT marble authority
MARBLE_ROOM_TYPES = {"BATH": ("BATHROOM", "US-01 + QP-07 + R8.13 §4: BATH is a bathroom"),
                     "PAINTRY": ("PANTRY_SERVICE_ROOM", "QP-07 names PAINTRY a kitchen / preparation zone FOR THE "
                                 "CERAMIC TAKEOFF only; the owner did not name pantry for the marble rule")}
DRY_TYPE = ("DRY_INTERNAL_ROOM", "class rule QORTUBA-SPACE-CLASS@v2: not a bathroom, kitchen, laundry or ironing room")
US07_DEPTH = 0.25
QP03_HEIGHT = 3.00


def jl(p):
    return json.loads(Path(p).read_text())


def physical_facts():
    return {f.fact_id: f for f in SB.physical_facts()}


def marble_rule():
    return MT.rule_from_record(jl(RULES)["rules"][0])


def room_type(side):
    if side.get("scope") == OUTSIDE or side.get("zones") is None:
        return None, "outside the measured unit / no site: no apartment room type"
    for z in side["zones"]:
        if z in MARBLE_ROOM_TYPES:
            return MARBLE_ROOM_TYPES[z]
    if side.get("class") == "DRY_INTERNAL_ROOM":
        return DRY_TYPE
    return None, "no authoritative room type"


# ---------------------------------------------------------------------------------------------- thresholds
def thresholds(res, inp, mfacts, binds, pbinds, rule):
    """R8.14 threshold records (strip, plane, sides) re-allocated with marble evidence where it applies."""
    base = R14.thresholds(res, inp, mfacts, binds)
    sites = {s["site_id"]: s for s in res["sites"]}
    eps_r = Q11.TP.tolerances(Q11.RT.max_abs_coordinate(inp.parts), inp.unit_native_to_mm)["eps_r"]
    unit2 = res["_unit2"]
    entr = [(f, b) for f, b in pbinds if f.fact_id == ENTR and b["binding"] == "APPLIES"]
    entr_occ = {"I" + p.split("|")[2] for f, _ in entr for p, _fp, _r in f.parts}
    out = []
    for t in base:
        types = {k: room_type(t[f"side_{k}"]) for k in ("A", "B")}
        rule_ev = MT.rule_evidence(rule, {k: v[0] for k, v in types.items()})
        explicit = MT.explicit_evidence(entr[0][0].ref, entr[0][0].statement) \
            if entr and t["door_occurrence"] in entr_occ else None
        ev = MT.choose(explicit, rule_ev) if t["_alloc"] is not None else None
        alloc, marble = t["_alloc"], None
        if ev is not None:
            s = sites[t["physical_site"]]
            alloc = DT.allocate(s["area"], s["perimeter"], t["_alloc"]["plane"], t["side_A"], t["side_B"],
                                eps_r=eps_r, marble=ev)
            marble = MT.record(t["threshold"], alloc, ev, unit_to_mm=inp.unit_native_to_mm)
        cls = (MT.TRADE if marble else None) or {DT.CONTINUOUS: "DRY_DRY_CONTINUOUS_PORCELAIN",
                                                 DT.SPLIT: "DRY_WET_SPLIT_AT_DOOR_PLANE"}.get(
            (alloc or {}).get("state"), "OUTSIDE_MEASURED_SCOPE" if t["allocation_state"] == OUTSIDE else
            "UNRESOLVED")
        if marble:
            cls = "MAIN_ENTRANCE_MARBLE_EXPLICIT" if ev["kind"] == MT.EXPLICIT else "URBAN_WET_SERVICE_MARBLE_RULE"
        rec = {k: v for k, v in t.items() if k != "_alloc"}
        rec.update({"room_types": {k: {"type": v[0], "authority": v[1]} for k, v in types.items()},
                    "rule_evaluation": rule_ev, "explicit_fact": explicit["ref"] if explicit else None,
                    "classification": cls, "marble": marble,
                    "allocation_state": alloc["state"] if alloc else t["allocation_state"],
                    "allocation_authority": ([ev["ref"]] if marble else t["allocation_authority"]),
                    "regions": [dict(r, area_m2=round(r["area"] * unit2, 6)) for r in (alloc or {}).get("regions", [])],
                    "reconciles": alloc is None or sum(r["area"] for r in alloc["regions"]) ==
                    sites[t["physical_site"]]["area"], "_alloc": alloc,
                    "r8_14_allocation_state": t["allocation_state"]})
        out.append(rec)
    return out


# ---------------------------------------------------------------------------------------------- rows
def heads_for(res, inp, owner_passage, mfacts, binds, pbinds):
    bound = {f.fact_id: b["binding"] == "APPLIES" for f, b in binds}
    pb = {f.fact_id: b["binding"] == "APPLIES" for f, b in pbinds}
    pf = {f.fact_id: f for f, _ in pbinds}
    hp = R14.hall_passage(res, owner_passage) if owner_passage else None
    mb_keys = {k for k, _fp, _r in pf[MBD].parts} if MBD in pf else set()
    parts = {q.identity.key: q for q in inp.parts}
    mb_segs = {tuple(sorted((tuple(round(v, 6) for v in parts[k].geometry[:2]), tuple(round(v, 6) for v in
                                                                               parts[k].geometry[2:4]))))
               for k in mb_keys if k in parts and parts[k].kind == "SEGMENT"}
    heads, why = {}, {}
    for p in res.get("passages") or []:
        pid = p["passage_id"]
        jam = {tuple(sorted(tuple(round(v, 6) for v in q) for q in j["segment"])) for j in p.get("jamb_faces", [])}
        if hp is not None and pid == hp["passage_id"] and bound.get(R14.F_SOFFIT):
            heads[pid], why[pid] = OR.WITH_HEAD, mfacts[R14.F_SOFFIT].ref
        elif pb.get(MBD) and p["target"] in mb_keys and jam and jam <= mb_segs:     # target face + jamb cap bound
            heads[pid], why[pid] = OR.FULL_HEIGHT, pf[MBD].ref
        else:
            heads[pid], why[pid] = None, "NOT_ESTABLISHED"
    return heads, why


def build_rows(res, inp, revision_id, ths, owner_passage, floor_policy, mfacts, binds, pbinds, obstacles):
    rows = R14.R13_rows(res, inp, revision_id, owner_passage, floor_policy)
    heads, head_why = heads_for(res, inp, owner_passage, mfacts, binds, pbinds)
    strips = R13.strips(res)
    alloc = {t["threshold"]: t["_alloc"] for t in ths}
    for rid in ROWS:
        row = rows[rid]
        rule = Q11.rule_for(rid)
        with R13.lab_rules():
            tr = R13.site_treatments(res, Q11.rule_for(rid))
        want = Q10_ROW(rid)
        sites = {u["site"] for u in row["sites_used"]}
        aud = []
        for s in strips:
            a = TS.audit_v2(s, sites, tr, want, trade=rule.trade, allocation=alloc.get(s["id"]), head=heads.get(s["id"]))
            if a["state"] != TS.NOT_IN_ROW:
                a["contribution_m2"] = round(a["contribution_m2"] * (res["_unit2"] if s["kind"] == "THRESHOLD" and
                                                                     a.get("regions") else 1.0), 6)
                if s["kind"] == "OPEN_PASSAGE":
                    a["head_authority"] = head_why.get(s["id"])
                aud.append(a)
        eff = TS.row_effect_v2(aud)
        base = round(sum(u["area_m2"] for u in row["sites_used"]), 6)
        row.update(strip_audit=aud, strip_effect=eff, base_site_area_m2=base)
        rel = [b for b in row["release_blockers"] if not (
            b.startswith("PASSAGE_SOFFIT_ALLOCATION") and eff["soffit_exclusion_m2"] > 0) and not (
            b.startswith("OBJECT_FOOTPRINT_IMPLICIT") and rid == "Q-13" and floor_policy is not None)]
        add = []
        ex = [a for a in aud if a["state"] == TS.EXCLUDED]
        if ex:
            add.append(f"STRIP_ALLOCATION: {len(ex)} door-threshold strip(s) ({round(sum(a['area_m2'] for a in ex), 6)} "
                       "m2) have no allocation authority")
        hd = [a for a in aud if a["state"] == TS.HEAD_UNRESOLVED]
        if hd:
            add.append("PASSAGE_HEAD_CONDITION_NOT_ESTABLISHED: " + "; ".join(f"{a['strip']} ({a['area_m2']} m2)"
                                                                               for a in hd))
        duct = [o for o in obstacles if o["site"] in sites]
        for o in duct:
            if not o["authorised"]:
                add.append(f"OBSTACLE_AUTHORITY_UNPROVEN: {o['hole_area_m2']} m2 excluded by isolated loop(s) "
                           f"{o['entities']}")
        row["duct_treatment"] = [{"site": o["site"], "hole_area_m2": o["hole_area_m2"], "authorised": o["authorised"],
                                  "facts": o["facts"], "effect": "EXCLUDED_FROM_ROOM_FLOOR" if rule.trade != TS.CEILING
                                  else "EXCLUDED_FROM_NORMAL_CEILING"} for o in duct]
        row["release_blockers"] = rel[:-1] + add + rel[-1:]
        row["marble_thresholds_touching"] = [{"threshold": a["strip"], "marble_area_m2": round(a["area_m2"], 6),
                                              "row_contribution_m2": a["contribution_m2"]}
                                             for a in aud if a["state"] == DT.MARBLE]
        if row["state"] == "COMPUTED_SHADOW":
            if eff["blocking"]:
                row["state"], row["value"] = "BLOCKED_TRADE_RULE", None
            else:
                row["value"] = round(base + eff["threshold_contribution_m2"] - eff["soffit_exclusion_m2"], 4)
    return rows, heads, head_why


def Q10_ROW(rid):
    return R14.Q10.ROW_TREATMENT[rid]


def obstacle_audit(res, inp, pbinds):
    auth = OA.entity_authority(res["wall_bands"]["isolated_loops"], pbinds)
    out = []
    for s in res["sites"]:
        h = OA.site_holes(s, res["wall_bands"]["isolated_loops"], auth, res["_unit2"])
        if h is not None:
            h["labels"] = sorted({v for vs in LAB.stamps(s).values() for v in vs})
            h["site_area_m2"] = round(s["area_m2"], 6)
            out.append(h)
    loops = {x["entity"]: x["segments"] for x in res["wall_bands"]["isolated_loops"]}
    parts = {p.identity.key: p for p in inp.parts}
    outer = {}
    for ent, segs in loops.items():
        pts = [tuple(parts[k].geometry[:2]) for k in sorted(segs)]
        outer[handle(ent + "|0")] = round(OA.shoelace(pts) * res["_unit2"], 6)
    return auth, out, outer


def digests(row, rid, policies, facts_row, reviews, facts_release):
    ta = row["trade_authority"]
    rad = RM.row_authority_digest(
        row["run_input_digest"], row_id=rid, row_method=f"TS01 (WALL_BAND_POLICY_V5) + trade layer + {TS.POLICY_ID_V2} + "
        f"{DT.POLICY_ID} + {MT.POLICY_ID} + {OA.POLICY_ID} + {OR.POLICY_ID} (lab rows)", trade_rules=[ta["rule"]],
        semantic_class_rules=[f"{R13.SPACE_CLASSES_V2.rule_id}@v{R13.SPACE_CLASSES_V2.version}"] if rid != "Q-14" else [],
        footprint_policies=[f"{p.policy_id}@v{p.version}:{p.trade}:{p.treatment}" for p in policies],
        row_claims=row["claims_applied"], owner_facts_applied=facts_row)
    rel = RM.release_input_digest(rad["digest"], source_anchor_state="DWG_DXF_IDENTITY_NOT_ESTABLISHED", reviews=reviews,
                                  release_policy="SHADOW_ONLY_NO_RELEASE_GATE", release_blockers=row["release_blockers"],
                                  owner_facts_applied=facts_release)
    return {"TOPOLOGY_RUN_INPUT_DIGEST": row["run_input_digest"], "ROW_AUTHORITY_DIGEST": rad,
            "RELEASE_INPUT_DIGEST": rel}


def reveals(res, inp, pfact, mfacts, pbinds, heads, owner_passage):
    u = inp.unit_native_to_mm / 1000
    hp = R14.hall_passage(res, owner_passage)
    out = {}
    out[hp["passage_id"]] = OR.passage_reveals(
        hp, head=OR.WITH_HEAD, clear_height=pfact.statement.get("clear_height_m"),
        jamb_authority={OR.LEFT_JAMB: f"{pfact.ref}: H2430 REAL_WALL_END", OR.RIGHT_JAMB: f"{pfact.ref}: H2431 REAL_WALL_END"},
        finish=mfacts[R14.F_REVEAL].statement["surfaces"], unit_to_m=u, default_depth_m=US07_DEPTH,
        default_ref="US-07 PLASTER_AND_PAINT_REVEALS_AT_0_25_M", height_basis="WITH_HEAD: 2.20 m (owner passage fact)",
        source_refs=[mfacts[R14.F_REVEAL].ref, mfacts[R14.F_SOFFIT].ref, pfact.ref])
    pf = {f.fact_id: f for f, _ in pbinds}
    for p in res["passages"]:
        if heads.get(p["passage_id"]) == OR.FULL_HEIGHT:
            out[p["passage_id"]] = OR.passage_reveals(
                p, head=OR.FULL_HEIGHT, clear_height=QP03_HEIGHT,
                jamb_authority={OR.LEFT_JAMB: f"source: drawn band-end cap (jamb face of {p['band_id']}); "
                                              f"{pf[MBD].ref}"},
                jamb_absent={OR.RIGHT_JAMB: f"ABUTS_CONTINUOUS_WALL_FACE (H{handle(p['target'])})"},
                finish={OR.LEFT_JAMB: None}, unit_to_m=u, default_depth_m=US07_DEPTH,
                default_ref="US-07 PLASTER_AND_PAINT_REVEALS_AT_0_25_M",
                height_basis="FULL_HEIGHT -> the applicable wall height (US-17); QP-03 internal plaster height 3.00 m "
                             "(Qortuba project value, not re-confirmed for this revision)",
                source_refs=[pf[MBD].ref])
    return out


def skirting(res, inp, ths):
    """The skirting row: the frozen policy + method, recomputed (must equal the blind record) + counterfactuals."""
    eps = Q11.TP.tolerances(Q11.RT.max_abs_coordinate(inp.parts), inp.unit_native_to_mm)["eps_r"]
    dry, wet = SB.dry_and_wet_sites(res)
    r = SB.run(res, inp, dry, wet, eps=eps)
    blind = jl(REG15 / "BLIND_QORTUBA_SKIRTING_RESULT.json")
    u = inp.unit_native_to_mm / 1000
    dry_ids = {s for s, _ in dry}
    door_returns = []
    for t in ths:
        for k in ("A", "B"):
            sd = t[f"side_{k}"]
            if sd.get("site") in dry_ids:
                door_returns.append({"threshold": t["threshold"], "side": k, "site": sd["site"],
                                     "two_jambs_to_frame_plane_m": round(2 * t["thickness_mm"] / 2 / 1000, 6)})
    tclosure_jambs = round(r["excluded_lm"][WC.TOPOLOGY_CLOSURE], 6)
    ret = round(r["passage_jamb_return_counterfactual_lm"] + tclosure_jambs +
                math.fsum(d["two_jambs_to_frame_plane_m"] for d in door_returns), 6)
    return {"recomputed": r, "blind": blind, "reproduces_blind": r["SKIRTING_LM"] == blind["SKIRTING_LM"] and
            r["per_site"] == json.loads(json.dumps(blind["per_site"], default=str)),
            "door_jamb_returns": door_returns, "passage_jambs_lm": round(r["passage_jamb_return_counterfactual_lm"] +
                                                                          tclosure_jambs, 6),
            "return_to_frame_counterfactual_lm": ret,
            "SKIRTING_LM_WITH_RETURNS_COUNTERFACTUAL": round(r["SKIRTING_LM"] + ret, 6),
            "post_blind_observation": {"id": "V2-O1", "what": "the Hall / Lobby passage record lists ONE jamb face "
                                       "(its own band end); the far jamb (the target band end) is a TOPOLOGY_CLOSURE "
                                       "edge, not OPENING_JAMB", "effect": "none on the published value (both are "
                                       "zero); the return counterfactual adds it explicitly",
                                       "action": "next round (no post-result edit to the frozen policy)"},
            "unit_m": u}


def doors_without_threshold(res, inp):
    """Doors whose second face closure was never formed (closure B absent): the reveal strip then lies INSIDE a room
    site. Measured from the source jamb caps (the A-closure hits): depth = the extent both caps share beyond A."""
    u = inp.unit_native_to_mm
    parts = {p.identity.key: p for p in inp.parts}
    cl = {c.source_id: c.geometry for c in res["closures"] if c.source_id.startswith("CLOSURE|")}
    out = []
    for occ, st in sorted(res["openings"].items()):
        if st.get("closure_b") or not st.get("closure_a"):
            continue
        a = cl[st["closure_a"]]
        (x0, y0), (x1, y1) = a[:2], a[2:]
        L = math.dist((x0, y0), (x1, y1))
        n = (-(y1 - y0) / L, (x1 - x0) / L)
        ext = {+1: [], -1: []}
        for k in st["hits"]:
            g = parts[k].geometry
            offs = [(px - x0) * n[0] + (py - y0) * n[1] for px, py in ((g[0], g[1]), (g[2], g[3]))]
            ext[+1].append(max(0.0, max(offs)))
            ext[-1].append(max(0.0, -min(offs)))
        side = max((+1, -1), key=lambda sd: min(ext[sd]))
        depth = min(ext[side])
        mid = ((x0 + x1) / 2 + n[0] * side * depth / 2, (y0 + y1) / 2 + n[1] * side * depth / 2)
        sid = R14._locate(res, mid)
        site = next((x for x in res["sites"] if x["site_id"] == sid), None)
        out.append({"door_occurrence": occ, "closure_a": st["closure_a"], "closure_b": None,
                    "jamb_caps": [handle(k) for k in st["hits"]], "width_mm": round(L * u, 2),
                    "reveal_depth_mm": round(depth * u, 2), "reveal_area_m2": round(L * depth * res["_unit2"], 6),
                    "jamb_cap_lm_in_room": round(2 * depth * u / 1000, 6),
                    "reveal_inside_site": sid, "site_labels": sorted({v for vs in LAB.stamps(site).values() for v in vs})
                    if site else [],
                    "why": "the caps cross closure A away from their end points (the two wall faces are offset at the "
                           "door), so topology_closures never forms closure B (frozen policy, R8.11)",
                    "effects": {"floor": "the reveal floor lies in that room's site (dry <-> dry here: continuity, no "
                                         "value change)",
                                "ceiling": "the door-head reveal is counted as normal ceiling (door thresholds are "
                                           "NOT_IN_TRADE for CEILING)",
                                "skirting": "the two jamb caps enter the path as REAL_WALL_FACE (a return, against "
                                            "NO_RETURN)", "marble": "a wet door here would miss its marble threshold"}})
    return out


# ---------------------------------------------------------------------------------------------- the build
def build(work, commit=None):
    R = R13.runs(work, commit)
    new, old = R["new"], R["old"]
    inp_new, inp_old = R["inputs"]["NEW_K2"], R["inputs"]["OLD_K1"]
    blindv5 = jl(R14.REG14 / "BLIND_QORTUBA_V5_RESULT.json")
    reproduces = {"closures": sorted(c["closure_id"] for c in new["topology_closures"]["closures"]) ==
                  sorted(c["closure_id"] for c in blindv5["NEW_K2"]["closures"]),
                  "topology_digest": new["run_manifest"]["RUN_INPUT_DIGEST"] == blindv5["NEW_K2"]["run_input_digest"]}
    pfact, b_new, per, domains = R14.R12.compare_fact(R14.OF11.load()[0], inp_new, new)
    owner_passage = R14.OF11.hall_lobby_passage(inp_new, new, {"fact": pfact.ref, "state": b_new["binding"]})
    mf13 = R13.finish_facts()
    b13 = [(f, MF.bind(f, inp_new)) for f in mf13]
    floor_pol = MF.policies_for(b13, trade="FLOOR_FINISH", space_classes=["DRY_INTERNAL_ROOM"],
                                finish="PORCELAIN_DRY_FLOOR")[0]
    mfacts = R14.method_facts()
    binds_new = [(f, MF.bind(f, inp_new)) for f in mfacts.values()]
    binds_old = [(f, MF.bind(f, inp_old)) for f in mfacts.values()]
    pf = physical_facts()
    pb_new = [(f, OF.bind(f, inp_new)) for f in pf.values()]
    pb_old = [(f, OF.bind(f, inp_old)) for f in pf.values()]
    rule = marble_rule()
    auth_new, obst_new, outer_new = obstacle_audit(new, inp_new, pb_new)
    auth_old, obst_old, _ = obstacle_audit(old, inp_old, pb_old)
    ths_new = thresholds(new, inp_new, mfacts, binds_new, pb_new, rule)
    ths_old = thresholds(old, inp_old, mfacts, binds_old, pb_old, rule)
    rows_new, heads, head_why = build_rows(new, inp_new, C.REV_NEW_ID, ths_new, owner_passage, floor_pol, mfacts,
                                           binds_new, pb_new, obst_new)
    rows_old, _, _ = build_rows(old, inp_old, C.REV_OLD_ID, ths_old, None, None, mfacts, binds_old, pb_old, obst_old)
    rev = reveals(new, inp_new, pfact, mfacts, pb_new, heads, owner_passage)
    hp = R14.hall_passage(new, owner_passage)
    q14a = {a["strip"]: a for a in rows_new["Q-14"]["strip_audit"]}
    guard = OR.ownership_guard([(hp["passage_id"], "TOP_SOFFIT")] +
                               [(pid, "CEILING") for pid, a in q14a.items() if a["kind"] == "OPEN_PASSAGE" and
                                a["state"] == TS.INCLUDED])
    sk = skirting(new, inp_new, ths_new)
    dwt = doors_without_threshold(new, inp_new)
    for d in dwt:
        if d["reveal_inside_site"] in {u["site"] for u in rows_new["Q-14"]["sites_used"]}:
            r = rows_new["Q-14"]
            r["release_blockers"].insert(len(r["release_blockers"]) - 1,
                                         f"DOOR_REVEAL_INSIDE_ROOM_SITE: door {d['door_occurrence']} ({d['width_mm']} x "
                                         f"{d['reveal_depth_mm']} mm) has no second face closure; its "
                                         f"{d['reveal_area_m2']} m2 head reveal is counted as ceiling")
            r["counterfactual_door_reveal_excluded"] = round(r["value"] - d["reveal_area_m2"], 4)
        if d["reveal_inside_site"] in sk["recomputed"]["per_site"]:
            sk.setdefault("release_blockers", []).append(
                f"DOOR_REVEAL_INSIDE_ROOM_SITE: door {d['door_occurrence']}: its two jamb caps "
                f"({d['jamb_cap_lm_in_room']} lm) are on the path as wall face (against NO_RETURN)")
            sk["counterfactual_without_that_return_lm"] = round(sk["recomputed"]["SKIRTING_LM"] -
                                                                d["jamb_cap_lm_in_room"], 6)
    marble = [t["marble"] for t in ths_new if t["marble"]]
    mq = MT.quantities(marble)
    facts_row = {rid: [] for rid in ROWS}
    for rid in ROWS:
        aud = rows_new[rid]["strip_audit"]
        if any(a["state"] == DT.CONTINUOUS for a in aud):
            facts_row[rid].append(mfacts[R14.F_CONT].ref)
        if any(a["state"] == DT.SPLIT for a in aud):
            facts_row[rid].append(mfacts[R14.F_SPLIT].ref)
        for a in aud:
            if a["state"] == DT.MARBLE:
                t = next(x for x in ths_new if x["threshold"] == a["strip"])
                facts_row[rid] += t["allocation_authority"]
        for d in rows_new[rid]["duct_treatment"]:
            facts_row[rid] += d["facts"]
    facts_row["Q-13"] = [R13.finish_facts()[0].ref] + facts_row["Q-13"]
    if q14a.get(hp["passage_id"], {}).get("state") == TS.SOFFIT_EXCLUDED:
        facts_row["Q-14"].append(mfacts[R14.F_SOFFIT].ref)
    facts_row["Q-14"] += sorted({a["head_authority"] for a in rows_new["Q-14"]["strip_audit"]
                                 if a.get("head_authority", "").startswith(MBD)})
    pol_of = {rid: ((Q11.CEILING_FOOTPRINT,) if rid == "Q-14" else ((floor_pol,) if rid == "Q-13" else ())) for rid in ROWS}
    reviews = [f"{c['closure_id']}:CORROBORATED_BY_OWNER({pfact.ref})" for c in new["topology_closures"]["closures"]
               if set(map(handle, c["source_evidence_ids"])) & {"2430", "2431"}]
    dig = {rid: digests(rows_new[rid], rid, pol_of[rid], sorted(set(facts_row[rid])), reviews if rid == "Q-14" else [],
                        [pfact.ref] if rid == "Q-14" else []) for rid in ROWS}
    freeze14 = jl(R14.REG14 / "R8_14_V5_FREEZE.json")
    auth = [c for c in new["topology_closures"]["closures"] if c["release"] == R14.TC.AUTHORISED_FOR_SHADOW]
    cre = {c["closure_id"]: dict(R14.CR.evaluate(c["release"], {
        "POLICY_FROZEN": WB.policy_record()["digest"] == freeze14["wall_band_policy"]["digest"] and
        R14.TC.policy_record()["digest"] == freeze14["closure_policy"]["digest"],
        "CROSS_ROUTE_AGREEMENT": None, "OWNER_OR_SOURCE_CORROBORATION": all(x["matrix"] == R14.OF.AGREES for x in per),
        "SOURCE_ANCHOR": False, "HUMAN_REVIEW": None}), evidence_parts=[handle(x) for x in c["source_evidence_ids"]],
        geometry=[round(v, 4) for v in c["geometry"]]) for c in auth}
    return {"R": R, "new": new, "old": old, "inp_new": inp_new, "reproduces": reproduces, "pfact": pfact,
            "owner_passage": owner_passage, "mfacts": mfacts, "pfacts": pf, "pb_new": pb_new, "pb_old": pb_old,
            "rule": rule, "floor_policy": floor_pol, "thresholds_new": ths_new, "thresholds_old": ths_old,
            "rows_new": rows_new, "rows_old": rows_old, "heads": heads, "head_why": head_why, "reveals": rev,
            "ownership_guard": guard, "hall_passage": hp, "obstacles_new": obst_new, "obstacles_old": obst_old,
            "authority_new": auth_new, "authority_old": auth_old, "loop_outer_area_m2": outer_new,
            "skirting": sk, "doors_without_threshold": dwt, "marble": marble, "marble_quantities": mq, "dig": dig, "facts_row": facts_row,
            "closure_release": cre, "source_anchor": R14.source_anchor(), "det": R13.shuffle_check(work, new),
            "blindv5": blindv5}


def main(work, regdir, commit=None):
    import r8_15_registers as REGS
    regs, ctx = REGS.registers(build(work, commit))
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: (v["state"], v["value"]) for k, v in ctx["rows_new"].items()}, indent=1))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
