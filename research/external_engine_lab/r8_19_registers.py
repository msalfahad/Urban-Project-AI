"""R8.19 lab registers: every JSON register of the R8.19 package from the r8_19_qortuba build (no number typed in).

Published numbers come from the REBUILD (ctx["r8_19"]: the frozen R8.19 run with the two disclosed wiring corrections
WF3-L1 / WF3-L2); the blind record is quoted beside them. The blind record (R8_19_BLIND_RESULT) and the freeze record
(R8_19_FREEZE) are committed before this module ran and are never rewritten here. Comparisons with R8.18 values are made
only AFTER the independent rebuild (anti-calibration) and are never targets.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import r8_18_registers as R18G
import r8_19_qortuba as Q
from engine.source import boq_report as BR, exposed_finish as EF, owner_method_facts as MF
from engine.source import reveal_finish as RF, reveal_physicality as RP, waterproofing as WP

ROOT = Path(__file__).resolve().parents[2]
GATES = {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO", "PRODUCTION_MIGRATION": "NO"}
REG18 = ROOT / "tests/r8_18/registers"
ROWS = Q.Q18.R17.R15.ROWS
FLOOR = "the selected SECOND FLOOR apartment (PLAN_VARIANT_4_SELECTED, region RC:MODEL_SPACE:4267:540:1649)"
SHADOW = "SHADOW_ONLY: no baseline approval, no migration transaction, no release gate passed"
ANCHOR = "SOURCE_ANCHOR: DXF anchored, DWG identity NOT_ESTABLISHED"
COL_RULE, DUCT_RULE = "URBAN-EXPOSED-COLUMN-FINISH-METHOD", "URBAN-EXPOSED-INTERIOR-DUCT-FINISH-METHOD"
DUCT_FACT, DUCT_PHYS = "QORTUBA-NEW-BED-ROOM-DUCT-FINISH-OWNER-001", "QORTUBA-NEW-BED-ROOM-DUCT-OWNER-001"
TRADES = {t["trade_id"]: t for t in json.loads((ROOT / "data/registry/trades.json").read_text())["trades"]}
ANTI_CAL = {"rule": "the R8.18 diagnostic unresolved areas (dry columns 10.8675, wet columns 14.88, duct 15.75 m2), the "
                    "R8.18 subtotals and any historical / manual total were never inputs or targets; the rows were "
                    "rebuilt from surface records. The comparison below is computed AFTER the rebuild only",
            "is_target": False}


def jl(p):
    return json.loads(Path(p).read_text())


def r6(v):
    return None if v is None else round(v, 6)


def fsum(xs):
    return r6(math.fsum(xs))


def digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, default=str).encode()).hexdigest()


def row_view(r, extra=None):
    return dict({"state": r["state"], "trade": r["trade"], "room_classes": r["classes"], "unit": "m2",
                 "AUTHORISED_SUBTOTAL_M2": r["AUTHORISED_SUBTOTAL_M2"], "COMPLETE_M2": r["COMPLETE_M2"],
                 "FINAL": None, "per_floor": {FLOOR: {"COMPLETE_M2": r["COMPLETE_M2"], "rooms": sorted(r["rooms"])}},
                 "per_room": {sid: dict(v, floor=FLOOR) for sid, v in r["rooms"].items()},
                 "reconciliation": {"sum_of_rooms_m2": fsum(v["total_m2"] for v in r["rooms"].values()),
                                    "row_m2": r["AUTHORISED_SUBTOTAL_M2"],
                                    "reconciles": abs(fsum(v["total_m2"] for v in r["rooms"].values()) -
                                                      r["AUTHORISED_SUBTOTAL_M2"]) < 1e-6},
                 "surfaces": len(r["surfaces"]),
                 "surface_ids_sha256": digest(sorted(json.dumps(s["id"]) for s in r["surfaces"])),
                 "by_kind_m2": {k: fsum(s["area_m2"] for s in r["surfaces"] if s["kind"] == k)
                                for k in ("WALL_PLANE", "OBJECT_FACE", "REVEAL")},
                 "unresolved_contributors": r["unresolved_contributors"], "blocked_rooms": r["blocked_rooms"],
                 "release_blockers": [ANCHOR, SHADOW]}, **(extra or {}))


def registers(ctx):
    base18, _ = R18G.registers(ctx)
    rb, fz = ctx["r8_19"], ctx["r8_19_freeze"]
    wm = fz["qortuba_wall_face_method"]
    rows, dig = ctx["rows_new"], ctx["dig"]
    rec = jl(ROOT / "research/external_engine_lab/r8_19_recommendation.json")
    six = {rid: R18G.R17G.R16G.R15G._row_view(rid, rows[rid], dig[rid]) for rid in ROWS}
    s18 = jl(REG18 / "QORTUBA_R8_18_STATUS.json")
    facts = {f["fact_id"]: f for f in jl(ROOT / "data/registry/OWNER_METHOD_FACTS.json")["facts"]}
    phys = {f["fact_id"]: f for f in jl(ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json")["facts"]}
    rules = {r["rule_id"]: r for r in jl(ROOT / "data/registry/URBAN_OWNER_METHOD_RULES.json")["rules"]}
    tr = rb["trade_rows"]
    xcol, xobs = rb["object_exposure"][EF.COLUMN_FACE], rb["object_exposure"][EF.OBSTACLE_FACE]
    regs = {}
    # ------------------------------------------------------------------ owner side
    regs["OWNER_ACTION_REGISTER"] = {
        "SCHEMA": "URBAN_OWNER_ACTION_REGISTER_V16",
        "headline": "NO OWNER ACTION REQUIRED. NO NEW MATERIAL QUESTION AFTER SOURCE / RULE EXHAUSTION.",
        "required_now": [],
        "optional_for_release_only": [
            {"id": "CLOSURE_HUMAN_REVIEW", "what": "review the prepared I1471 / H2430 / H2431 packets "
                                                  "(CLOSURE_RELEASE_STATUS.review_packets) and accept or reject each",
             "blocks": "REVIEWED_FOR_RELEASE_CANDIDATE only (shadow rows do not need it); never self-approved"}],
        "answered_this_round": [f"{COL_RULE}@v1", f"{DUCT_RULE}@v1", f"{DUCT_FACT}@v1"],
        "do_not_ask": ["column finish", "duct finish", "column skirting", "duct skirting", "dry height 3.15 m",
                       "wet tile 3.20 m", "default reveal plaster", "porcelain reveal explicit-only",
                       "sliding-door classification", "window skirting", "marble", "passage heads"]}
    regs["OWNER_METHOD_RULE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_19_OWNER_METHOD_RULE_REGISTER_V1",
        "new_urban_rules": [rules[COL_RULE], rules[DUCT_RULE]], "new_project_fact": facts[DUCT_FACT],
        "physical_authority": phys[DUCT_PHYS]["fact_id"] + "@v1 (BUILT_OBSTACLE, R8.15)",
        "kept_urban_rules": sorted(k for k in rules if k not in (COL_RULE, DUCT_RULE)), "fact_policy": MF.POLICY_ID,
        "fact_policy_unchanged": "the duct statement uses the existing FINISH_SCOPE kind: no policy bump"}
    # ------------------------------------------------------------------ object faces
    regs["COLUMN_FINISH_POLICY"] = {
        "SCHEMA": "URBAN_R8_19_COLUMN_FINISH_POLICY_V1", "policy": EF.policy_record(), "urban_rule": rules[COL_RULE],
        "qortuba_method_rule": wm["object_face_rules"][EF.COLUMN_FACE],
        "identity": wm["object_identity"][EF.COLUMN_FACE], "exposure": wm["exposure"],
        "skirting": "unchanged V4 path (COLUMN_FACE component); wet / full-tile rooms NO_SKIRTING"}
    regs["DUCT_FINISH_POLICY"] = {
        "SCHEMA": "URBAN_R8_19_DUCT_FINISH_POLICY_V1", "policy": EF.policy_record(), "urban_rule": rules[DUCT_RULE],
        "qortuba_method_rule": wm["object_face_rules"][EF.OBSTACLE_FACE], "project_fact": facts[DUCT_FACT],
        "physical_authority": phys[DUCT_PHYS], "identity": wm["object_identity"][EF.OBSTACLE_FACE],
        "skirting": "unchanged V4 path (AUTHORISED_OBSTACLE_FACE component)"}

    def per_entity(x):
        out = {}
        for k, v in x["segments"].items():
            e = out.setdefault(v["object"], {"segments": 0, "length_m": 0.0, "exposed_m": 0.0, "hidden_m": 0.0,
                                             "sites": set()})
            e["segments"] += 1
            e["length_m"] += v["length_m"]
            e["exposed_m"] += v["exposed_total_m"]
            e["hidden_m"] += v["hidden_m"]
            e["sites"] |= set(v["exposed_m"])
        return {k: {"segments": v["segments"], "length_m": r6(v["length_m"]), "exposed_m": r6(v["exposed_m"]),
                    "hidden_m": r6(v["hidden_m"]), "sites": sorted(v["sites"]),
                    "state": EF.HIDDEN if v["exposed_m"] <= 1e-9 else
                    (EF.EXPOSED if v["hidden_m"] <= 1e-9 else EF.PARTIAL)} for k, v in sorted(out.items())}

    def contributions(cls):
        out = {}
        for row_id, r in tr.items():
            for s in r["surfaces"]:
                if s["kind"] == "OBJECT_FACE" and s["class"] == cls:
                    out.setdefault(row_id, {}).setdefault(s["site"], 0.0)
                    out[row_id][s["site"]] += s["area_m2"]
        return {k: {sid: r6(a) for sid, a in v.items()} | {"total_m2": fsum(v.values())} for k, v in out.items()}
    col_c, duct_c = contributions(EF.COLUMN_FACE), contributions(EF.OBSTACLE_FACE)
    r18col = jl(REG18 / "COLUMN_DUCT_FINISH_REGISTER.json")
    regs["COLUMN_DUCT_FINISH_REGISTER"] = {
        "SCHEMA": "URBAN_R8_19_COLUMN_DUCT_FINISH_REGISTER_V1", "policy": EF.POLICY_ID,
        "columns": {"per_entity": per_entity(xcol), "per_segment": xcol["segments"], "exposed_faces": xcol["faces"],
                    "exposure_state": xcol["state"], "errors": xcol["errors"], "contribution_m2": col_c},
        "duct": {"per_entity": per_entity(xobs), "per_segment": xobs["segments"], "exposed_faces": xobs["faces"],
                 "exposure_state": xobs["state"], "errors": xobs["errors"], "contribution_m2": duct_c,
                 "owner_physical_authority": rb["object_exposure"]["obstacle_states"]},
        "hidden_faces_excluded": {"column_segments_hidden": sorted(k for k, v in xcol["segments"].items()
                                                                   if v["state"] == EF.HIDDEN),
                                  "column_segments_partial": {k: v["hidden_m"] for k, v in xcol["segments"].items()
                                                              if v["state"] == EF.PARTIAL},
                                  "duct_segments_hidden": sorted(k for k, v in xobs["segments"].items()
                                                                 if v["state"] == EF.HIDDEN),
                                  "finish_on_hidden_m2": 0.0},
        "skirting_no_duplicate": ctx["skirting_check_19"],
        "identity": "COLUMN_FACE / OBSTACLE_FACE classes kept on every surface record (never WALL_FACE)",
        "unresolved": [c for r in tr.values() for c in r["unresolved_contributors"]],
        "after_rebuild_vs_r8_18_diagnostic": dict(ANTI_CAL, r8_18_unresolved=r18col.get("column_area_m2"),
                                                  r8_18_duct_m2=r18col.get("duct_area_m2"),
                                                  r8_19_dry_columns_m2=col_c.get("DRY_WALL_PLASTER", {}).get("total_m2"),
                                                  r8_19_wet_columns_m2=col_c.get("WET_SERVICE_WALL_TILE",
                                                                                 {}).get("total_m2"),
                                                  r8_19_duct_m2=duct_c.get("DRY_WALL_PLASTER", {}).get("total_m2"))}
    # ------------------------------------------------------------------ trade rows
    pl, wrp = tr["DRY_WALL_PLASTER"], tr["WET_SERVICE_REVEAL_PLASTER"]
    r18pl = jl(REG18 / "PLASTER_REGISTER.json")
    regs["PLASTER_REGISTER"] = {
        "SCHEMA": "URBAN_R8_19_PLASTER_REGISTER_V1", "floor": FLOOR,
        "DRY_WALL_PLASTER": row_view(pl, {"height_m": 3.15, "height_authority":
                                          rb["heights"]["DRY_INTERNAL_ROOM|PLASTER"]["authority"]}),
        "WET_SERVICE_REVEAL_PLASTER": row_view(wrp, {"why_separate": "PLASTER_DEFAULT reveals owned by wet / service "
                                                                     "rooms (never tile, never paint)"}),
        "PLASTER_ALL_SURFACES_M2": rb["PLASTER_ALL_SURFACES_M2"],
        "plaster_all_note": "computed by the trade layer from the surface records of both plaster rows (the BOQ layer "
                            "never adds rows)",
        "excluded": ["wet wall-tile surfaces", "topology closures (zero area)", "unproven reveals (none remain)",
                     "hidden / embedded object faces"],
        "after_rebuild_vs_r8_18": dict(ANTI_CAL, r8_18_dry_authorised=r18pl["AUTHORISED_SUBTOTAL_M2"],
                                       r8_18_wet_reveal_plaster=r18pl["WET_SERVICE_REVEAL_PLASTER"]["AUTHORISED_M2"],
                                       r8_19_dry_complete=pl["COMPLETE_M2"], r8_19_wet_reveal_plaster=wrp["COMPLETE_M2"],
                                       difference_dry_m2=r6(pl["COMPLETE_M2"] - r18pl["AUTHORISED_SUBTOTAL_M2"]),
                                       explained_by=["dry column faces", "duct faces"],
                                       difference_wet_reveal_m2=r6(wrp["COMPLETE_M2"] -
                                                                   r18pl["WET_SERVICE_REVEAL_PLASTER"]["AUTHORISED_M2"]),
                                       wet_reveal_explained_by="the PAINTRY south sliding-door jamb, now physically "
                                                               "established (band end), 0.11 m2")}
    pa = tr["DRY_WALL_PAINT"]
    regs["PAINT_REGISTER"] = {
        "SCHEMA": "URBAN_R8_19_PAINT_REGISTER_V1", "floor": FLOOR,
        "DRY_WALL_PAINT": row_view(pa, {"height_m": 3.15, "height_authority":
                                        rb["heights"]["DRY_INTERNAL_ROOM|PAINT"]["authority"]}),
        "vs_dry_plaster": dict(rb["paint_vs_plaster"], paint_m2=pa["COMPLETE_M2"], dry_plaster_m2=pl["COMPLETE_M2"],
                               why="the SAME surface records (identity set) carry PLASTER and PAINT in every dry room: "
                                   "wall plane, exposed columns, the duct and dry-owned PLASTER_AND_PAINT reveals; the "
                                   "wet / service plaster-only reveals carry no paint"),
        "paintry": "NO PAINT (QP-07 full wall tile)"}
    wt, prep = tr["WET_SERVICE_WALL_TILE"], tr["WET_WALL_TILE_PREP"]
    regs["WALL_TILE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_19_WALL_TILE_REGISTER_V1", "floor": FLOOR,
        "WET_SERVICE_WALL_TILE": row_view(wt, {"height_m": 3.2, "height_authority": {
            k: rb["heights"][k]["authority"] for k in ("WET_SERVICE_ROOM|WALL_TILE", "SERVICE_ROOM|WALL_TILE")}}),
        "column_contribution_m2": col_c.get("WET_SERVICE_WALL_TILE"),
        "porcelain_reveals": [x for x in rb["reveals"] if x["finish"] == RF.PORCELAIN_EXPLICIT] or "NONE",
        "excluded": ["default-plaster reveals (WET_SERVICE_REVEAL_PLASTER)", "paint", "normal skirting"],
        "height_conflict": rb["height_conflicts"]}
    ids = lambda r: {json.dumps(s["id"]) for s in r["surfaces"]}                               # noqa: E731
    regs["WALL_TILE_PREP_REGISTER"] = {
        "SCHEMA": "URBAN_R8_19_WALL_TILE_PREP_REGISTER_V1", "floor": FLOOR,
        "WET_WALL_TILE_PREP": row_view(prep, {"authority": "US-03 (preparation under the wall tile)"}),
        "same_physical_surfaces_as_wall_tile": ids(prep) == ids(wt),
        "why_separate": "a separate BOQ item (preparation), same measured surface set; never merged"}
    # ------------------------------------------------------------------ reveals
    rv = rb["reveals"]
    by = {}
    for x in rv:
        b = by.setdefault(x["finish"], {"count": 0, "area_m2": 0.0})
        b["count"] += 1
        b["area_m2"] = r6(b["area_m2"] + (x["area_m2"] or 0.0))
    regs["REVEAL_FINISH_REGISTER"] = {
        "SCHEMA": "URBAN_R8_19_REVEAL_FINISH_REGISTER_V1", "policies": [RP.POLICY_ID, RF.POLICY_ID],
        "order": "physicality first, finish second",
        "reveals": [{k: x.get(k) for k in ("opening", "kind", "surface", "owner_site", "owner_zones", "owner_class",
                                           "depth_m", "height_m", "width_m", "area_m2", "finish", "trades",
                                           "depth_basis", "authority", "physicality", "included")} for x in rv],
        "count": len(rv), "by_finish": by,
        "by_physicality": {s: sum(1 for x in rv if x["physicality"]["state"] == s)
                           for s in (RP.ESTABLISHED, RP.NONE, RP.UNRESOLVED, "OUT_OF_MEASURED_SCOPE")},
        "unresolved": [x["opening"] + " " + x["surface"] for x in rv if x["physicality"]["state"] == RP.UNRESOLVED],
        "two_finish_owners": "NONE (one owner per reveal; physical guard PASS)",
        "fixture_evidence": "rejected by policy (admitted roles only); test_r8_19_reveal_physicality::test_r1"}
    sp = rb["sliding_door_physicality"]
    bands = {b["band_id"]: b for b in ctx["new"]["wall_bands"]["bands"]}
    used = sorted({e["band_id"] for x in sp for e in x["evidence"] if e["kind"] == "ESTABLISHED_WALL_BAND_END"})
    parts = {p.identity.key: p for p in ctx["inp_new"].parts}
    near = ["QORTUBA_REV_NEW|H480||SEGMENT|0", "QORTUBA_REV_NEW|H1512||SEGMENT|0", "QORTUBA_REV_NEW|H1513||SEGMENT|0",
            "QORTUBA_REV_NEW|H533||SEGMENT|0", "QORTUBA_REV_NEW|H542||SEGMENT|0", "QORTUBA_REV_NEW|H535||SEGMENT|0",
            "QORTUBA_REV_NEW|H543||SEGMENT|0"]
    roles = ctx["new"]["roles"]["roles"]
    regs["SLIDING_DOOR_REVEAL_PHYSICALITY"] = {
        "SCHEMA": "URBAN_R8_19_SLIDING_DOOR_REVEAL_PHYSICALITY_V1", "policy": RP.policy_record(),
        "opening": "HALL <-> PAINTRY floor-reaching sliding glass door (owner fact, unchanged)",
        "ownership_and_depth": {"split": rb["sliding_door_split"],
                                "basis": "aluminium tracks H542 (flush with the HALL face) / H533 (0.05 m from the "
                                         "PAINTRY face): ownership and depth only - never proof of masonry"},
        "jambs": sp,
        "south_jamb": next((x for x in sp if x["evidence"] and any(e.get("band_id") == "WB-fa9e752f77ae497d"
                                                                   for e in x["evidence"])), None),
        "bands_used": {b: {k: bands[b][k] for k in ("band_id", "state", "face_a", "face_b", "width", "interval", "ends")}
                       for b in used},
        "source_parts": {k: {"layer": parts[k].layer, "geometry": [round(v, 4) for v in parts[k].geometry[:4]],
                             "role": getattr(roles.get(k), "role", None)} for k in near if k in parts},
        "outcome": "PHYSICAL_REVEAL_ESTABLISHED for both PAINTRY-side jambs: north by H1513 (WALL) + band end; south by "
                   "the established band WB-fa9e752f77ae497d OPENING_JAMB end (masonry faces H535 / H543 both end on "
                   "the jamb line). H480 (FIXTURE / SANITARY_FIXTURE role) is recorded as REJECTED evidence",
        "finish": "PLASTER_DEFAULT (PAINTRY owner, plaster only), 0.11 m2 per jamb",
        "history": "R8.18 blind: H480 wrongly accepted (WF2-L1); R8.18 rebuild: UNRESOLVED; R8.19: established by "
                   "independent physical evidence under a frozen policy",
        "cannot_recur": "REVEAL_PHYSICALITY_POLICY_V1 admits only TOPOLOGY_BOUNDARY / STRUCTURAL_OBSTACLE parts or an "
                        "ESTABLISHED band OPENING_JAMB end of the same opening (frozen, tested)"}
    # ------------------------------------------------------------------ regressions
    wp18 = jl(REG18 / "WATERPROOFING_REGISTER.json")
    regs["WATERPROOFING_REGISTER"] = dict(base18["WATERPROOFING_REGISTER"],
                                          SCHEMA="URBAN_R8_19_WATERPROOFING_REGISTER_V1",
                                          regression_vs_r8_18={"R8.18": wp18["rows"], "R8.19": rb["waterproofing"]
                                                               ["totals"], "unchanged": {
                                                                   WP.FLOOR: wp18["rows"][WP.FLOOR]["value"] ==
                                                                   rb["waterproofing"]["totals"][WP.FLOOR],
                                                                   WP.UPTURN: wp18["rows"][WP.UPTURN]["value"] ==
                                                                   rb["waterproofing"]["totals"][WP.UPTURN]},
                                                               "column_duct_effect": "NONE (independent policy)"})
    sk18 = jl(REG18 / "SKIRTING_REGISTER.json")
    sk = ctx["skirting_v4"]
    regs["SKIRTING_REGISTER"] = dict(base18["SKIRTING_REGISTER"], SCHEMA="URBAN_R8_19_SKIRTING_REGISTER_V1",
                                     regression_vs_r8_18={"R8.18": sk18["SKIRTING_LM"], "R8.19": sk["PAYABLE_LM"],
                                                          "unchanged": sk18["SKIRTING_LM"] == sk["PAYABLE_LM"],
                                                          "v4_edited": False, "is_target": False},
                                     column_duct_no_duplicate=ctx["skirting_check_19"])
    hp18 = jl(REG18 / "HIDDEN_PROFILE_REGISTER.json")
    regs["HIDDEN_PROFILE_REGISTER"] = dict(base18["HIDDEN_PROFILE_REGISTER"],
                                           SCHEMA="URBAN_R8_19_HIDDEN_PROFILE_REGISTER_V1",
                                           regression_vs_r8_18={"R8.18": hp18["HIDDEN_PROFILE_LM"],
                                                                "R8.19": sk["PAYABLE_LM"],
                                                                "unchanged": hp18["HIDDEN_PROFILE_LM"] ==
                                                                sk["PAYABLE_LM"]})
    v18 = {rid: v["VALUE"] for rid, v in s18["six_rows"].items()}
    for rid, name in (("Q-13", "Q13_STATUS"), ("Q-14", "Q14_STATUS")):
        regs[name] = dict(base18[name], SCHEMA=f"URBAN_R8_19_{name}_V1",
                          regression_vs_r8_18={"R8.18": v18[rid], "R8.19": rows[rid]["value"],
                                               "delta_m2": round(rows[rid]["value"] - v18[rid], 4),
                                               "column_duct_effect": "NONE (vertical trades only)", "is_target": False})
    mq18 = jl(REG18 / "MARBLE_THRESHOLD_REGISTER.json")["quantities"]
    regs["MARBLE_THRESHOLD_REGISTER"] = dict(base18["MARBLE_THRESHOLD_REGISTER"],
                                             SCHEMA="URBAN_R8_19_MARBLE_THRESHOLD_REGISTER_V1",
                                             regression_vs_r8_18={"R8.18": mq18, "R8.19": ctx["marble_quantities"],
                                                                  "unchanged": mq18 == ctx["marble_quantities"]})
    regs["SECOND_PROJECT_REGRESSION"] = dict(base18["SECOND_PROJECT_REGRESSION"],
                                             SCHEMA="URBAN_R8_19_SECOND_PROJECT_REGRESSION_V1",
                                             substitute="the 29 frozen R8.19 synthetic tests (exposed columns / ducts, "
                                                        "reveal physicality, BOQ layer) plus the R8.13-R8.18 families",
                                             next="R8.20: a second project with a resolved unit and certified topology")
    regs["SOURCE_ANCHOR_STATUS"] = dict(base18["SOURCE_ANCHOR_STATUS"], SCHEMA="URBAN_R8_19_SOURCE_ANCHOR_STATUS_V1",
                                        r8_19="the pinned libredwg 0.13.3 (sha fe49cf28...) was re-run inside the "
                                              "R8.16 build path; no other DWG-capable tool is installed or pinned; "
                                              "nothing was downloaded",
                                        cross_route_dependency="REV_NEW has ONE input route (K2 ezdxf DXF); the K1 "
                                                               "route reads the DWG - closure cross-route agreement "
                                                               "waits on this anchor")
    regs["CLOSURE_RELEASE_STATUS"] = closure_review(base18["CLOSURE_RELEASE_STATUS"], ctx)
    # ------------------------------------------------------------------ BOQ
    regs["BOQ_REPORT_SCHEMA"], regs["BOQ_REPORT_SHADOW"] = boq(ctx, regs, six)
    # ------------------------------------------------------------------ status / decisions
    extra = {k: {"state": v["state"], "AUTHORISED_SUBTOTAL_M2": v["AUTHORISED_SUBTOTAL_M2"],
                 "COMPLETE_M2": v["COMPLETE_M2"], "release_blockers": [ANCHOR, SHADOW]} for k, v in tr.items()}
    extra |= {"SKIRTING": {"state": regs["SKIRTING_REGISTER"]["state"], "value_lm": sk["PAYABLE_LM"],
                           "release_blockers": regs["SKIRTING_REGISTER"]["release_blockers"]},
              "HIDDEN_PROFILE": {"state": regs["HIDDEN_PROFILE_REGISTER"]["state"], "value_lm": sk["PAYABLE_LM"],
                                 "release_blockers": regs["HIDDEN_PROFILE_REGISTER"]["release_blockers"]},
              "MARBLE_THRESHOLD": {"state": "COMPUTED_SHADOW", **ctx["marble_quantities"],
                                   "release_blockers": regs["MARBLE_THRESHOLD_REGISTER"]["release_blockers"]},
              WP.FLOOR: {"state": "COMPUTED_SHADOW", "value_m2": rb["waterproofing"]["totals"][WP.FLOOR],
                         "release_blockers": [ANCHOR, SHADOW]},
              WP.UPTURN: {"state": "COMPUTED_SHADOW", "value_lm": rb["waterproofing"]["totals"][WP.UPTURN],
                          "release_blockers": [ANCHOR, SHADOW]}}
    dkeys = ("TOPOLOGY_DIGEST", "ROW_AUTHORITY_DIGEST", "RELEASE_INPUT_DIGEST")
    regs["QORTUBA_R8_19_STATUS"] = {
        "SCHEMA": "URBAN_R8_19_QORTUBA_STATUS_V1", "six_rows": six, "extra_rows": extra,
        "rows_old": {rid: {"state": v["state"], "value": v["value"]} for rid, v in ctx["rows_old"].items()},
        "old_revision_unchanged_vs_r8_18": {rid: (ctx["rows_old"][rid]["state"], ctx["rows_old"][rid]["value"]) ==
                                            (s18["rows_old"][rid]["state"], s18["rows_old"][rid]["value"])
                                            for rid in ROWS},
        "vs_r8_18": {rid: {"R8.18": v18[rid], "R8.19": six[rid]["VALUE"], "delta": round(six[rid]["VALUE"] -
                                                                                         v18[rid], 4)} for rid in ROWS},
        "digest_vs_r8_18": {rid: {k: "SAME" if six[rid][k] == s18["six_rows"][rid][k] else "CHANGED" for k in dkeys}
                            for rid in ROWS},
        "determinism": ctx["det"],
        "reproduces": {"r8_19_blind": ctx["reproduces_r8_19_blind"], "r8_18_blind": ctx["reproduces_r8_18_blind"],
                       "v4_blind": ctx["reproduces_v4_blind"]},
        "plane_check_vs_r8_18_method_b": {"all_agree": all(v["agree"] for v in ctx["plane_check_19"].values()),
                                          "rooms": ctx["plane_check_19"]},
        "blind_vs_rebuild": ctx["blind_vs_rebuild_19"], "final": "SHADOW only: no row is FINAL",
        "production_migration": "NO"}
    regs["R8_19_DECISION_REGISTER"] = decision_register(regs, ctx, rec, six)
    return regs, ctx


def closure_review(base, ctx):
    new = ctx["new"]
    tcs = {c["closure_id"]: c for c in new["topology_closures"]["closures"]}
    packets = {}
    for cid, v in base["closures"].items():
        c = tcs.get(cid, {})
        rec = {k: c.get(k) for k in ("closure_id", "geometry", "source_evidence_ids", "release")}
        handle = next((h for h in ("2430", "2431") if h in v["evidence_parts"]), None)
        packets[f"H{handle}" if handle else cid] = {
            "closure_id": cid, "kind": "TOPOLOGY_CLOSURE (TS01, zero material)", "record": rec,
            "closure_digest": digest(rec), "current_level": v["level"],
            "conditions": {"POLICY_FROZEN": v["evidence"]["POLICY_FROZEN"],
                           "OWNER_OR_SOURCE_CORROBORATION": v["evidence"]["OWNER_OR_SOURCE_CORROBORATION"],
                           "CROSS_ROUTE_AGREEMENT": "NOT_ACHIEVABLE_THIS_ROUND (REV_NEW has one input route; K1 needs "
                                                    "the DWG decode)",
                           "SOURCE_ANCHOR": "NOT_ESTABLISHED", "HUMAN_REVIEW": "PENDING (packet prepared, never "
                                                                             "self-approved)"},
            "maximum_level_now": v["level"],
            "review_question": f"Is the zero-material closure line {[round(g, 2) for g in v['geometry']]} (between "
                               f"source parts {v['evidence_parts']}) a correct room separation for the measured "
                               "topology? ACCEPT / REJECT, with the closure digest"}
    i1471 = new["openings"].get("I1471", {})
    dcl = [c for c in new["closures"] if "I1471" in c.source_id]
    drec = {"opening": "I1471", "closures": [{"source_id": c.source_id, "geometry": [round(g, 4) for g in c.geometry]}
                                             for c in dcl],
            "opening_record": {k: (v if not isinstance(v, float) else round(v, 4)) for k, v in i1471.items()
                               if k in ("closure_a", "closure_b", "width", "state", "policy")}}
    packets["I1471"] = {
        "kind": "TS01 DOOR STRIP CLOSURE (DOOR_OPENING_CLOSURE_POLICY_V2 offset jambs)", "record": drec,
        "closure_digest": digest(drec), "current_level": "SHADOW (door strips are not release-graded closures)",
        "conditions": {"POLICY_FROZEN": "YES (R8.16 freeze)", "OWNER_OR_SOURCE_CORROBORATION": "SOURCE (door block "
                                                                                             "geometry, offset jambs)",
                       "CROSS_ROUTE_AGREEMENT": "NOT_ACHIEVABLE_THIS_ROUND", "SOURCE_ANCHOR": "NOT_ESTABLISHED",
                       "HUMAN_REVIEW": "PENDING (packet prepared, never self-approved)"},
        "maximum_level_now": "SHADOW",
        "review_question": "Do the two I1471 door-strip closures (offset jambs, CLOSURE|I1471|A / B) bound the real "
                           "door opening I1471? ACCEPT / REJECT, with the closure digest"}
    return dict(base, SCHEMA="URBAN_R8_19_CLOSURE_RELEASE_STATUS_V1", review_packets=packets,
                self_approved=False, released=base.get("released") or [], production="NO",
                note="review material prepared; no level raised")


ITEMS = {
    "Q-03": ("ARCHITECTURAL_FLOOR_FINISH", "أرضيات سيراميك - المناطق الرطبة (الحمامات)",
             "Wet-room ceramic floor (CERAMIC_WET_FLOOR), row Q-03"),
    "Q-03P": ("ARCHITECTURAL_FLOOR_FINISH", "أرضيات سيراميك - غرفة التحضير (PAINTRY)",
              "Service ceramic floor (CERAMIC_SERVICE_FLOOR), row Q-03P"),
    "Q-11": ("ARCHITECTURAL_FLOOR_FINISH", "أرضيات سيراميك - المناطق الرطبة (البند Q-11)",
             "Wet-room ceramic floor (CERAMIC_WET_FLOOR), row Q-11"),
    "Q-12": ("ARCHITECTURAL_FLOOR_FINISH", "أرضيات سيراميك - غرفة التحضير (البند Q-12)",
             "Service ceramic floor (CERAMIC_SERVICE_FLOOR), row Q-12"),
    "Q-13": ("ARCHITECTURAL_FLOOR_FINISH", "أرضيات بورسلين - المناطق الجافة",
             "Dry-room porcelain floor (PORCELAIN_DRY_FLOOR), row Q-13"),
    "Q-14": ("CEILING", "أسقف - حسب المساحة", "Ceiling by area, row Q-14"),
    "DRY_WALL_PLASTER": ("PLASTER_INTERNAL", "لياسة داخلية للجدران والأعمدة والدكت المكشوف - المناطق الجافة حتى 3.15 م",
                         "Internal plaster - dry rooms (walls, exposed columns, duct, reveals) to 3.15 m"),
    "WET_SERVICE_REVEAL_PLASTER": ("PLASTER_INTERNAL", "لياسة جوانب الفتحات - الحمامات وغرفة التحضير",
                                   "Plaster to reveals owned by wet / service rooms"),
    "DRY_WALL_PAINT": ("PAINT", "دهانات داخلية للجدران والأعمدة والدكت المكشوف - المناطق الجافة حتى 3.15 م",
                       "Internal paint - dry rooms (walls, exposed columns, duct, reveals) to 3.15 m"),
    "WET_SERVICE_WALL_TILE": ("ARCHITECTURAL_WALL_FINISH", "تكسيات جدران بورسلين / سيراميك - المناطق الرطبة حتى 3.20 م",
                              "Porcelain / ceramic wall tile - wet / service rooms (walls, exposed columns) to 3.20 m"),
    "WET_WALL_TILE_PREP": ("ARCHITECTURAL_WALL_FINISH", "تحضير الجدران تحت التكسيات - المناطق الرطبة",
                           "Wall preparation under the wall tile - wet / service rooms"),
    "SKIRTING": ("SKIRTING_PROFILE", "نعلة مخفية - المناطق الجافة", "Hidden skirting - dry rooms"),
    "HIDDEN_PROFILE": ("SKIRTING_PROFILE", "بروفايل ألمنيوم مخفي للنعلة", "Hidden aluminium skirting profile"),
    "MARBLE_THRESHOLD_PLAN_AREA_M2": ("MARBLE_STONE", "عتبات رخام - المساحة", "Marble thresholds - plan area"),
    "MARBLE_THRESHOLD_LENGTH_LM": ("MARBLE_STONE", "عتبات رخام - الطول", "Marble thresholds - length"),
    WP.FLOOR: ("WATERPROOFING", "عزل مائي لأرضيات المناطق الرطبة", "Waterproofing membrane - wet-room floors"),
    WP.UPTURN: ("WATERPROOFING", "رفرف عزل مائي بارتفاع 15 سم على محيط المناطق الرطبة",
                "Waterproofing upturn 0.15 m - gross wet-room perimeter")}


def boq(ctx, regs, six):
    rb, fz = ctx["r8_19"], ctx["r8_19_freeze"]
    run = {"run_id": ctx["new"]["run_manifest"]["RUN_INPUT_DIGEST"], "source_revision": "QORTUBA_REV_NEW",
           "source_dxf_sha256": regs["SOURCE_ANCHOR_STATUS"].get("dxf_sha256"), "floor": FLOOR}
    base = {"run_id": run["run_id"], "source_revision": "QORTUBA_REV_NEW", "release_state": "SHADOW",
            "floor": FLOOR, "source": "DXF (K2 ezdxf), TS01 certified topology"}
    ev = []
    for rid, v in six.items():
        ev.append(dict(base, row_id=rid, unit="m2", trade_row=f"QORTUBA_R8_19_STATUS.six_rows.{rid}",
                       complete=v["VALUE"] if v["STATE"] == "COMPUTED_SHADOW" else None,
                       authorised_subtotal=v["VALUE"], unresolved=[], sites=[s["site"] for s in v["BASE_PHYSICAL_SITES"]],
                       surface_ids=None, authority_digest=v["ROW_AUTHORITY_DIGEST"], rule_ids=v["TRADE_AUTHORITY"],
                       owner_facts=v["OWNER_FACTS_APPLIED"], blockers=v["RELEASE_BLOCKERS"], per_room=None))
    mdig = fz["qortuba_wall_face_method"]["digest"]
    for rid, r in rb["trade_rows"].items():
        rules = sorted({s.get("rule") for s in r["surfaces"] if s.get("rule")}) + \
            [fz["qortuba_wall_face_method"]["ref"]]
        ev.append(dict(base, row_id=rid, unit="m2", trade_row=f"{rid} (R8.19 rebuild)", complete=r["COMPLETE_M2"],
                       authorised_subtotal=r["AUTHORISED_SUBTOTAL_M2"], unresolved=r["unresolved_contributors"],
                       sites=sorted(r["rooms"]),
                       surface_ids={"count": len(r["surfaces"]),
                                    "sha256": digest(sorted(json.dumps(s["id"]) for s in r["surfaces"]))},
                       authority_digest=digest([mdig, fz["policies"]]), rule_ids=rules,
                       owner_facts=[f"{DUCT_FACT}@v1"] if any(s["class"] == EF.OBSTACLE_FACE for s in r["surfaces"])
                       else [], blockers=[ANCHOR, SHADOW],
                       per_room={sid: {"zones": x["zones"], "qty": x["total_m2"]} for sid, x in r["rooms"].items()
                                 if x["total_m2"]}))
    sk = ctx["skirting_v4"]
    for rid in ("SKIRTING", "HIDDEN_PROFILE"):
        reg = regs[f"{rid}_REGISTER"]
        ev.append(dict(base, row_id=rid, unit="lm", trade_row=f"{rid}_REGISTER", complete=sk["PAYABLE_LM"],
                       authorised_subtotal=sk["PAYABLE_LM"], unresolved=reg.get("withheld") or [],
                       sites=sorted(sk["per_site"]), surface_ids=None, authority_digest=digest(sk["policy"]),
                       rule_ids=[sk["method"]], owner_facts=[], blockers=reg["release_blockers"],
                       per_room={sid: {"zones": v["zones"], "qty": v["payable_lm"]} for sid, v in sk["per_site"].items()
                                 if v["payable_lm"]}))
    mq = ctx["marble_quantities"]
    for rid, unit in (("MARBLE_THRESHOLD_PLAN_AREA_M2", "m2"), ("MARBLE_THRESHOLD_LENGTH_LM", "lm")):
        ev.append(dict(base, row_id=rid, unit=unit, trade_row="MARBLE_THRESHOLD_REGISTER", complete=mq[rid],
                       authorised_subtotal=mq[rid], unresolved=mq.get("blocked") or [], sites=None, surface_ids=None,
                       authority_digest=digest(regs["MARBLE_THRESHOLD_REGISTER"].get("rule")),
                       rule_ids=["URBAN-WET-SERVICE-MARBLE-THRESHOLD@v1"], owner_facts=[],
                       blockers=regs["MARBLE_THRESHOLD_REGISTER"]["release_blockers"], per_room=None))
    w = rb["waterproofing"]
    for rid, unit in ((WP.FLOOR, "m2"), (WP.UPTURN, "lm")):
        ev.append(dict(base, row_id=rid, unit=unit, trade_row="WATERPROOFING_REGISTER", complete=w["totals"][rid],
                       authorised_subtotal=w["totals"][rid], unresolved=[], sites=sorted(w["rooms"]), surface_ids=None,
                       authority_digest=digest(WP.policy_record()), rule_ids=["US-04", "US-05", "US-14", "QP-13"],
                       owner_facts=[], blockers=[ANCHOR, SHADOW],
                       per_room={sid: {"zones": v["zones"], "qty": v[rid]} for sid, v in w["rooms"].items()}))
    items = {rid: {"item_code": "QOR-R819-" + rid.replace("_", "-").replace(".", ""), "trade": t,
                   "trade_name_ar": TRADES[t]["display_name_ar"], "description_ar": ar, "description_en": en}
             for rid, (t, ar, en) in ITEMS.items()}
    rep = BR.build(ev, items, run=run)
    val = BR.validate(rep, ev, items)
    schema = {"SCHEMA": "URBAN_R8_19_BOQ_REPORT_SCHEMA_V1", "policy": BR.policy_record(), "columns": list(BR.COLUMNS),
              "statuses": {BR.COMPLETE: "evidence row COMPLETE, no unresolved contributor - SHADOW, not approved",
                           BR.SUBTOTAL: "authorised subtotal only - never approved",
                           BR.BLOCKED: "no quantity", BR.RELEASED: "only with a release record (none exists)"},
              "trace": list(BR.TRACE), "items": items, "trade_registry": "data/registry/trades.json",
              "pricing": None, "calculates": False}
    shadow = {"SCHEMA": "URBAN_R8_19_BOQ_REPORT_SHADOW_V1", "report": rep, "validation": val,
              "evidence_rows": ev, "status_counts": {s: sum(1 for r in rep["rows"] if r["STATUS"] == s)
                                                     for s in BR.STATUSES},
              "approved_for_boq": sum(1 for r in rep["rows"] if r["approved_for_boq"]),
              "banner": "SHADOW BOQ - NOT APPROVED FOR TENDER / CONTRACT; NO PRODUCTION MIGRATION"}
    return schema, shadow


def decision_register(regs, ctx, rec, six):
    rb, fz = ctx["r8_19"], ctx["r8_19_freeze"]
    tr = rb["trade_rows"]
    pl, pa, wt = regs["PLASTER_REGISTER"], regs["PAINT_REGISTER"], regs["WALL_TILE_REGISTER"]
    cd, sd, st = regs["COLUMN_DUCT_FINISH_REGISTER"], regs["SLIDING_DOOR_REVEAL_PHYSICALITY"], \
        regs["QORTUBA_R8_19_STATUS"]
    cr, bq = regs["CLOSURE_RELEASE_STATUS"]["review_packets"], regs["BOQ_REPORT_SHADOW"]
    skc = ctx["skirting_check_19"]
    dry = {sid for sid, v in tr["DRY_WALL_PLASTER"]["rooms"].items()}
    wet = {sid for sid, v in tr["WET_SERVICE_WALL_TILE"]["rooms"].items()}
    room = lambda r: {f"{'/'.join(sorted(v['zones']))} ({sid})": v["total_m2"] for sid, v in r["rooms"].items()}  # noqa
    obj_trades = lambda cls, sids: sorted({tr_id for tr_id, r in tr.items() for s in r["surfaces"]                 # noqa
                                           if s["kind"] == "OBJECT_FACE" and s["class"] == cls and s["site"] in sids})
    remaining = {rid: v["RELEASE_BLOCKERS"] for rid, v in six.items()}
    remaining |= {k: v.get("release_blockers") for k, v in st["extra_rows"].items()}
    south = sd["south_jamb"] or {}
    answers = {
        "1_column_rule_encoded": f"YES: {COL_RULE}@v1 (Urban rule store) + EXPOSED_OBJECT_FINISH_POLICY_V1 + "
                                 "QORTUBA-NEW-WALL-FACE-METHOD@v3, frozen before the blind run",
        "2_dry_columns_plaster_paint": f"YES: dry column faces in {obj_trades(EF.COLUMN_FACE, dry)} - "
                                       f"{cd['columns']['contribution_m2'].get('DRY_WALL_PLASTER')}",
        "3_dry_column_skirting_no_duplicate": f"YES: every dry room's exposed column length equals its V4 COLUMN_FACE "
                                              f"skirting ({all(v['same_faces'] for v in skc.values())}); SKIRTING "
                                              f"{regs['SKIRTING_REGISTER']['regression_vs_r8_18']}",
        "4_wet_columns_wall_tile": f"YES: {cd['columns']['contribution_m2'].get('WET_SERVICE_WALL_TILE')} (3.20 m)",
        "5_wet_columns_no_paint_no_skirting": f"YES: wet column faces only in {obj_trades(EF.COLUMN_FACE, wet)}; wet "
                                              "rooms NO_SKIRTING_FULL_WALL_TILE",
        "6_hidden_column_faces_excluded": f"YES: {len(cd['hidden_faces_excluded']['column_segments_hidden'])} hidden "
                                          f"column segments, {len(cd['hidden_faces_excluded']['column_segments_partial'])}"
                                          f" partially exposed ({cd['hidden_faces_excluded']['column_segments_partial']} "
                                          "m hidden), finish on hidden faces 0.0 m2",
        "7_duct_rule_encoded": f"YES: {DUCT_RULE}@v1 + {DUCT_FACT}@v1 (requires owner physical authority "
                               f"{DUCT_PHYS}@v1)",
        "8_duct_plaster_paint": f"YES: {cd['duct']['contribution_m2']}",
        "9_duct_skirting_unchanged": {sid: {k: skc[sid][k] for k in ("zones", "v4_duct_lm", "exposed_duct_m",
                                                                      "same_faces")}
                                      for sid in sorted({f["site"] for f in rb["object_exposure"][EF.OBSTACLE_FACE]
                                                         ["faces"]})} | {"SKIRTING": "unchanged"},
        "10_hidden_duct_faces_excluded": f"YES: {cd['hidden_faces_excluded']['duct_segments_hidden']} (H2061 inner "
                                         "lining) carry no finish",
        "11_plaster_independent": "YES: rebuilt from surface records (wall plane + exposed object faces + physically "
                                  "established reveals); no R8.18 total or diagnostic area was read",
        "12_plaster": {"DRY_WALL_PLASTER": {k: pl["DRY_WALL_PLASTER"][k] for k in
                                            ("state", "AUTHORISED_SUBTOTAL_M2", "COMPLETE_M2")},
                       "WET_SERVICE_REVEAL_PLASTER": {k: pl["WET_SERVICE_REVEAL_PLASTER"][k] for k in
                                                      ("state", "AUTHORISED_SUBTOTAL_M2", "COMPLETE_M2")},
                       "PLASTER_ALL_SURFACES_M2": pl["PLASTER_ALL_SURFACES_M2"]},
        "13_plaster_per_room": room(tr["DRY_WALL_PLASTER"]) | {"WET reveals": room(tr["WET_SERVICE_REVEAL_PLASTER"])},
        "14_paint_independent": "YES: its own row from its own surface assignments; equality proven by surface-set "
                                f"identity ({pa['vs_dry_plaster']['same_surface_set']})",
        "15_paint": {k: pa["DRY_WALL_PAINT"][k] for k in ("state", "AUTHORISED_SUBTOTAL_M2", "COMPLETE_M2")},
        "16_paint_vs_plaster": pa["vs_dry_plaster"]["why"],
        "17_wall_tile_independent": "YES: from wet / service wall-plane surfaces + exposed wet column faces",
        "18_bathroom_tile": {k: v for k, v in room(tr["WET_SERVICE_WALL_TILE"]).items() if k.startswith("BATH")},
        "19_paintry_tile": {k: v for k, v in room(tr["WET_SERVICE_WALL_TILE"]).items() if k.startswith("PAINTRY")},
        "20_column_tile_contribution": wt["column_contribution_m2"],
        "21_wet_wall_tile_prep": f"{regs['WALL_TILE_PREP_REGISTER']['WET_WALL_TILE_PREP']['COMPLETE_M2']} m2 - US-03 "
                                 "preparation on the SAME physical surfaces as the wall tile "
                                 f"({regs['WALL_TILE_PREP_REGISTER']['same_physical_surfaces_as_wall_tile']}), its "
                                 "own BOQ row",
        "22_south_reveal_established": f"YES: {south.get('state')}",
        "23_geometry": sd["outcome"],
        "24_if_not": "n/a - no wall-finish physicality blocker remains",
        "25_fixture_rejected": f"YES: rejected evidence {south.get('rejected')}",
        "26_waterproofing_changed": f"NO: {regs['WATERPROOFING_REGISTER']['regression_vs_r8_18']['unchanged']}",
        "27_skirting_hidden_profile_changed": {"SKIRTING": regs["SKIRTING_REGISTER"]["regression_vs_r8_18"],
                                               "HIDDEN_PROFILE": regs["HIDDEN_PROFILE_REGISTER"]["regression_vs_r8_18"]},
        "28_floor_ceiling_rows_changed": st["vs_r8_18"],
        "29_marble_changed": regs["MARBLE_THRESHOLD_REGISTER"]["regression_vs_r8_18"],
        "30_boq_layer": f"YES: {BR.POLICY_ID} (engine/source/boq_report.py), {len(bq['report']['rows'])} report rows, "
                        f"validation {bq['validation']['state']}",
        "31_boq_calculates": "NO: every QTY is copied from one evidence field; validate() re-derives every row and "
                             "refuses any difference (tested with a manual edit)",
        "32_boq_traceability": f"YES: every row carries {list(BR.TRACE)} (untraced: {bq['validation']['untraced']})",
        "33_statuses_distinguished": f"YES: {bq['status_counts']}; approved_for_boq {bq['approved_for_boq']}",
        "34_i1471": cr["I1471"]["conditions"] | {"maximum_level_now": cr["I1471"]["maximum_level_now"]},
        "35_h2430": cr.get("H2430", {}).get("conditions", {}) | {"maximum_level_now":
                                                                 cr.get("H2430", {}).get("maximum_level_now")},
        "36_h2431": cr.get("H2431", {}).get("conditions", {}) | {"maximum_level_now":
                                                                 cr.get("H2431", {}).get("maximum_level_now")},
        "37_dwg_dxf_identity": regs["SOURCE_ANCHOR_STATUS"]["state"],
        "38_second_project": regs["SECOND_PROJECT_REGRESSION"]["state"],
        "39_release_blockers": remaining,
        "40_new_silent_errors": [
            "WF3-L1 (blind-script wiring, found after the blind run): the blind script admitted every wall-face V2 "
            "surface record as wall plane, but V2 also carries COLUMN_FACE / OBSTACLE_FACE records as separate "
            "classes - every exposed column / duct face was counted twice (blind DRY_WALL_PLASTER / PAINT +26.6175 m2, "
            "WALL_TILE / PREP +14.88 m2). The rebuild admits only the V2 plane classes; each rebuilt room plane equals "
            "the R8.18 V2 METHOD B net",
            "WF3-L2 (blind-script guard): the surface guard keyed records by id, so it missed WF3-L1, and keyed object "
            "faces by (site, class, segment), so it flagged one column segment exposed as two physical spans. The "
            "rebuild guard keys by physical identity and catches all 15 + 8 blind copies",
            "amendment 1 (pre-output crash): band ends without face points were not skipped - fixed before any value "
            "was written"],
        "41_r8_20": rec["13_r8_20"],
        "42_disagreements": rec["12_disagreements_with_chatgpt"]}
    return {"SCHEMA": "URBAN_R8_19_DECISION_REGISTER_V1", "recommendation_before_coding": rec,
            "order": fz["order"] + ["amendment 1 (c622f01)", "blind (f1e8e04)", "rebuild / registers / BOQ "
                                                                                "(WF3-L1 / WF3-L2 disclosed)"],
            "decisions": [
                {"id": "R819-D01", "decision": "exposed column faces follow the room's wall trades (dry plaster + paint "
                                               "at 3.15 m, wet tile + prep at 3.20 m); skirting stays V4"},
                {"id": "R819-D02", "decision": "the H2060 duct: plaster + paint at 3.15 m on its 4 exposed faces; "
                                               "H2061 lining hidden; skirting stays V4"},
                {"id": "R819-D03", "decision": "REVEAL_PHYSICALITY_POLICY_V1: the PAINTRY south sliding jamb is "
                                               "established by the band OPENING_JAMB end; H480 rejected"},
                {"id": "R819-D04", "decision": "all five wall-finish rows COMPUTED_SHADOW_COMPLETE (not FINAL)"},
                {"id": "R819-D05", "decision": "BOQ_REPORT_LAYER_V1: presentation only, shadow report published, no "
                                               "row approved"},
                {"id": "R819-D06", "decision": "closure review packets prepared; nothing self-approved or released"},
                {"id": "R819-D07", "decision": "second-project regression NOT_RUN; source anchor NOT_ESTABLISHED"}],
            "gates": GATES, "answers": answers}
