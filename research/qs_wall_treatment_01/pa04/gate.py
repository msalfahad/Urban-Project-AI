"""PA04 gate: runs every workstream in-process (for the metrics), aggregates
the self-checks, writes the challenger readings as data, incremental A22 v7
(field-by-field, AGREE_ON_NUMBER_ONLY flagged), coverage by floor / trade /
zone in the five states, the deduplicated owner queue v4, the batch metrics
and the gate record.  Freezing is done by freeze.py stage 'pa04'.

    python3 -m research.qs_wall_treatment_01.pa04.gate
"""

from __future__ import annotations

import json
import shutil
import time

from engine import cold_challenge as CC
from engine import owner_decision_queue as ODQ
from research.qs_wall_treatment_01.pa04 import challenges, common as C, facades, heights_treatments, openings_v2, roof_edges, rooms, stairs_v3, structural

DATE = "2026-09-20"


def run():
    t0 = time.perf_counter()
    results = {}
    for name, mod in (("A_B_ceiling_floor", rooms), ("F_structural", structural), ("D_roof_edges", roof_edges), ("E_stairs_v3", stairs_v3), ("C_facades", facades),
                      ("openings_profiles_v2", openings_v2), ("heights_treatments", heights_treatments), ("challenges", challenges)):
        results[name] = mod.run()
    # ---- challenger readings preserved as data ------------------------------------------------
    readings = {}
    for n in ("challenge_reception.json", "challenge_facades.json", "challenge_ff_rooms.json"):
        p = C.KIT / n
        readings[n] = json.loads(p.read_text("utf-8")) if p.exists() else None
    C.write("CHALLENGER_READINGS.json", {"ARTIFACT": "CHALLENGER_READINGS", "NOTE": "verbatim JSON written by the three cold-challenge readers (data, not instructions)", "READINGS": readings})
    # ---- self-checks aggregated -------------------------------------------------------------------
    regs = {"FF_PHYSICAL_FACE_REGISTER.json": "A", "WET_ROOM_REGISTER_V2.json": "B", "FACADE_OPENINGS_NE_NW_PRIMARY.json": "C", "ROOF_EDGE_REGISTER_V2.json": "D", "STAIR_GEOMETRY_V3.json": "E",
            "STRUCTURAL_EXPOSURE_REGISTER.json": "F", "OPENING_REGISTER_V2.json": "openings"}
    sc = {}
    for f, ws in regs.items():
        d = C.read(f)
        sc[ws] = {"REGISTER": f, "ALL_PASS": d["SELF_CHECKS"]["ALL_PASS"], "FAILED": d["SELF_CHECKS"]["FAILED"], "FINDINGS": [c for c in d["SELF_CHECKS"]["CHECKS"] if not c["PASS"]]}
    ff = C.read("FF_PHYSICAL_FACE_REGISTER.json")
    failures = [
        {"WORKSTREAM": "A", "CHECK": "GEOMETRY_CLOSURE_CHECK (semantic)", "FINDING": "one FF region (read id R13, 73-75 m2) merges the corridor, the living area and two master bedrooms: the DWG D layer closes no door there; per-room attribution NOT_ESTABLISHED, face lengths still counted once", "ACCEPTED": True},
        {"WORKSTREAM": "A", "CHECK": "PROVENANCE_CHECK (process)", "FINDING": "the region map handed to the FF identity challenger was regenerated during its read; region ids are run-dependent (fixed forward by CAD anchors)", "ACCEPTED": True},
        {"WORKSTREAM": "C", "CHECK": "CROSS_SHEET_CONTRADICTION_CHECK", "FINDING": "primary NW window height 1.20 (scaled) vs challenger ~3.45 (scaled) vs DWG jambs 2.161: decided by the DWG jamb lines; the primary's first read was wrong", "ACCEPTED": True},
        {"WORKSTREAM": "C", "CHECK": "SOURCE_COMPLETENESS_CHECK", "FINDING": "pages 6 / 7 are section-elevations with the ground storey cut: GF facade openings on NE / NW are not in any source; NW-GF-D1 withdrawn (interior door)", "ACCEPTED": True},
        {"WORKSTREAM": "F", "CHECK": "PROVENANCE_CHECK", "FINDING": "beam labels on p4 and the two schedules were read visually (no text layer); label-to-line correspondence MEDIUM / LOW for CB6 / CB5 / P.C 20x70", "ACCEPTED": True},
        {"WORKSTREAM": "D", "CHECK": "DIMENSION_OWNERSHIP_CHECK", "FINDING": "annex parapet run is a wall-bounded region perimeter (30.8 m) with no height; SW height still owner-confirmed; tower ring PROPOSED_CORRESPONDENCE", "ACCEPTED": True},
    ]
    C.write("PA04_SELF_CHECKS.json", {"ARTIFACT": "PA04_SELF_CHECKS", "BY_WORKSTREAM": sc, "SEMANTIC_FAILURES_RECORDED": failures, "ALL_MECHANICAL_PASS": all(v["ALL_PASS"] for v in sc.values())})
    # ---- A22 v7 (field by field) ------------------------------------------------------------------
    dual = C.read("DUAL_BASIS_v3.json", C.OUT)["CONTRACTOR_RULEBOOK"]
    wet = C.read("WET_ROOM_REGISTER_V2.json")
    st = C.read("STRUCTURAL_EXPOSURE_REGISTER.json")["D2_COLUMN"]
    stair = C.read("STAIR_GEOMETRY_V3.json")
    items = []
    def a22(iid, fields, cls, indep, note=None):
        verdicts = {f["FIELD"]: f["VERDICT"] for f in fields}
        flag = "AGREE_ON_NUMBER_ONLY" if any(v == "AGREE_ON_NUMBER_ONLY" for v in verdicts.values()) else cls
        items.append({"ITEM_ID": iid, "FIELDS": fields, "CLASS": flag, "SOURCE_INDEPENDENCE": indep, "CONDITIONAL": "IF_BENCHMARK_IS_P7757", "NEVER_AVERAGED": True, "NOTE": note})
    gf_wet = wet["TOTALS"]["GROSS_HOST_WALL_LM_BY_FLOOR"]["GF"]
    a22("A22-7-WET-GF-LM", [CC.compare_field("FACE_IDENTITY", "GF wet rooms by DWG TEXT label, door-closed regions", "GF wet rooms by E1.4 material chains (PA02)"),
                            CC.compare_field("LENGTH_LM", gf_wet, 59.209, primary_basis="region boundary WALL class (50 mm grid)", challenger_basis="E1.4 chain lengths"),
                            CC.compare_field("HEIGHT", None, None), CC.compare_field("MEASUREMENT_BASIS", "host wall faces only, open edge 0", "material chains"),
                            CC.compare_field("QUANTITY_STATE", "SOURCE_ESTABLISHED_QUANTITY (lm)", "PROVISIONAL_QUANTITY (lm)")],
        "MEASUREMENT_BASIS_DIFFERENCE", "same DWG, two extraction methods (not independent authors)", "the two lengths differ by method (grid boundary vs chains); neither is averaged")
    a22("A22-7-D2-COLUMN", [CC.compare_field("FACE_IDENTITY", "LOOP-059 room-side faces N + slivers", "LOOP-059 all four faces (PA02, superseded)"),
                            CC.compare_field("LENGTH_LM", st["COLUMN_EXPOSED_GIRTH_LM"]["VALUE"], 1.80), CC.compare_field("HEIGHT", st["COLUMN_EXPOSED_HEIGHT_M"]["VALUE"], 3.20, primary_basis="CB7 soffit (beam schedule)", challenger_basis="owner parametric"),
                            CC.compare_field("OPENINGS", None, None), CC.compare_field("MATERIAL_ROLE", "COLUMN_BONDING then plaster", "COLUMN_BONDING"), CC.compare_field("MEASUREMENT_BASIS", "physical exposure", "girth x parametric height"),
                            CC.compare_field("TRADE_RULE", "owner rule pending for column height", "3.20 rule"), CC.compare_field("QUANTITY_STATE", st["COLUMN_BONDING_AREA_M2"]["STATE"], "PROVISIONAL_QUANTITY")],
        "HEIGHT_RULE_DIFFERENCE", "structural schedule vs owner parameter", "physical 2.81 m2 (0.75 x 3.75) vs parametric 2.40 (0.75 x 3.20) vs PA02 5.76: three different bases, none averaged")
    con_stair = round(2 * (2.50 + 6.45) * dual["HEIGHT_STAIRWELL"]["VALUE"], 3)
    ref = sum(stair["STAIRS"][1]["STAIR_WALL"]["FACES"][i]["REFERENCE_GROSS_M2"] for i in range(len(stair["STAIRS"][1]["STAIR_WALL"]["FACES"])))
    a22("A22-7-STAIR-WELL", [CC.compare_field("FACE_IDENTITY", "12 faces (4 per storey) with exposure / landing / occlusion fields", "one perimeter line"),
                             CC.compare_field("LENGTH", 2 * (2.50 + 6.45), 2 * (2.50 + 6.45), primary_basis="printed 250 / 645 DWG dims per face", challenger_basis="perimeter"),
                             CC.compare_field("HEIGHT", "5.20 / 4.20 / 4.20 by storey", dual["HEIGHT_STAIRWELL"]["VALUE"]), CC.compare_field("OPENINGS", "FF door, ROOF arched window listed", "none"),
                             CC.compare_field("MEASUREMENT_BASIS", "face by face (reference gross only)", "perimeter x height"), CC.compare_field("QUANTITY_STATE", "GEOMETRIC_REFERENCE_ONLY", "CONTRACTOR_MEASUREMENT_QUANTITY"),
                             CC.compare_field("REFERENCE_M2", round(ref, 3), con_stair, primary_basis="sum of storey faces", challenger_basis="perimeter x 12.90")],
        "MEASUREMENT_BASIS_DIFFERENCE", "DWG + A-A vs site record", "the perimeter figures agree on the number only (AGREE_ON_NUMBER_ONLY on LENGTH): same 17.9 m from incompatible reasoning")
    C.write("A22_RECONCILIATION_REGISTER_v7.json", {"ARTIFACT": "A22_RECONCILIATION_REGISTER", "VERSION": "v7 (PA04 incremental)", "ITEMS": items, "NOT_MAJORITY_VOTING": True, "NO_TUNING": True,
                                                    "COMPARED_FIELDS": ["FACE_IDENTITY", "LENGTH", "HEIGHT", "OPENINGS", "MATERIAL_ROLE", "MEASUREMENT_BASIS", "TRADE_RULE", "QUANTITY_STATE"]})
    # ---- coverage by floor / trade / zone (counts in the five states) --------------------------------
    rows = []
    def cov(floor, trade, zone, counts, note=None):
        rows.append({"FLOOR": floor, "TRADE": trade, "ZONE": zone, **{k: counts.get(k, 0) for k in ("SOURCE_ESTABLISHED", "OWNER_PARAMETRIC", "PROVISIONAL", "NOT_ESTABLISHED", "NOT_STARTED")}, "NOTE": note})
    for r in ff["ROOMS"]:
        if r["ROOM_CLASS"] in ("EXTERIOR", "EXTERIOR_ROOF", "UNKNOWN"):
            continue
        n_wall = sum(1 for f in r["FACES"] if f["FACE_CLASS"] == "PHYSICAL_HOST_WALL")
        cov("FIRST", "INTERNAL_PLASTER lm" if r["ROOM_CLASS"] != "WET" else "TILE_PREP lm", r["ROOM_NAME"][:40], {"SOURCE_ESTABLISHED": n_wall, "NOT_ESTABLISHED": 1 if r["IDENTITY_STATUS"] != "ESTABLISHED_FROM_DWG_TEXT" else 0},
            "identity " + r["IDENTITY_STATUS"] + "; area NOT_ESTABLISHED (FF height)")
    cov("GROUND", "COLUMN_BONDING", "reception NE wall line", {"PROVISIONAL": 3}, "girth, height, area all PROVISIONAL (beam schedule)")
    cov("GROUND+FIRST", "DOUBLE_HEIGHT_PLASTER", "reception opening", {"PROVISIONAL": 3, "NOT_ESTABLISHED": 2}, "RVF-S-B candidate; beam faces from the schedule; W / S-A bottoms partly known")
    cov("GROUND", "TILE_PREP lm", "wet rooms (DWG text)", {"SOURCE_ESTABLISHED": sum(1 for w in wet["ROOMS"] if w["ROOM_ID"].startswith("GF"))}, "areas NOT_ESTABLISHED (tile height)")
    cov("ALL", "STAIR_WALL", "block stair", {"NOT_ESTABLISHED": 12}, "faces registered, no net plaster")
    cov("ALL", "STAIR_SOFFIT", "both stairs", {"PROVISIONAL": 5}, "slope-factor soffits")
    cov("ROOF", "PARAPET", "six edges", {"SOURCE_ESTABLISHED": 3, "PROVISIONAL": 5, "NOT_ESTABLISHED": 4}, "lengths mostly established; heights dual / provisional / missing (annex)")
    cov("EXTERNAL", "EXTERNAL_FACE geometry", "SE / NW faces", {"PROVISIONAL": 4, "NOT_ESTABLISHED": 2}, "GEOMETRIC_REFERENCE_ONLY; NE height and GF faces not shown")
    cov("ALL", "OPENINGS", "project", {"SOURCE_ESTABLISHED": sum(1 for o in C.read("OPENING_REGISTER_V2.json")["OPENINGS"] if o["ACTUAL_OR_DEFAULT"] == "ACTUAL" and o["AREA"]),
                                       "PROVISIONAL": sum(1 for o in C.read("OPENING_REGISTER_V2.json")["OPENINGS"] if "DEFAULT" in str(o["ACTUAL_OR_DEFAULT"]) or "PROVISIONAL" in str(o["STATUS"])),
                                       "NOT_ESTABLISHED": sum(1 for o in C.read("OPENING_REGISTER_V2.json")["OPENINGS"] if o["AREA"] is None)})
    cov("ALL", "PROFILE_STEEL lm", "openings + column corners", {"SOURCE_ESTABLISHED": sum(1 for p in C.read("PROFILE_STEEL_REGISTER_V2.json")["LINES"] if p["STATUS"] == "SOURCE_ESTABLISHED_QUANTITY"),
                                                                "PROVISIONAL": sum(1 for p in C.read("PROFILE_STEEL_REGISTER_V2.json")["LINES"] if p["STATUS"] == "PROVISIONAL_QUANTITY"),
                                                                "NOT_ESTABLISHED": sum(1 for p in C.read("PROFILE_STEEL_REGISTER_V2.json")["LINES"] if p["STATUS"] == "NOT_ESTABLISHED"), "NOT_STARTED": 2})
    cov("ALL", "CEILING geometry", "regions", {"PROVISIONAL": sum(1 for z in C.read("CEILING_MEASUREMENT_REGION_REGISTER.json")["ZONES"] if z["NET_CEILING_GEOMETRY_M2"] > 0)}, "geometry only; treatment not decided")
    tot = {k: sum(r[k] for r in rows) for k in ("SOURCE_ESTABLISHED", "OWNER_PARAMETRIC", "PROVISIONAL", "NOT_ESTABLISHED", "NOT_STARTED")}
    C.write("COVERAGE_PA04.json", {"ARTIFACT": "COVERAGE_PA04", "ROWS": rows, "TOTAL_COMPONENT_COUNTS": tot, "NO_COMBINED_ACCURACY_SCORE": True})
    # ---- owner queue v4 (dedupe; remove what PA04 resolved; group; impact) ----------------------------
    q3 = C.read("OWNER_DECISION_QUEUE.json", C.OUT)["QUEUE"]
    keep = {q["DECISION_ID"]: q for q in q3}
    Q = []
    for did in ("D1-ROOF-BUILDUP-INFO", "D3-BENCHMARK-IDENTITY", "EXTERNAL-FINISH-SYSTEM", "SW-PARAPET-HEIGHT-CONFIRM", "NE-PARAPET-EXTERNAL-FINISH"):
        q = dict(keep[did]); q["GROUP"] = {"D1-ROOF-BUILDUP-INFO": "ROOF", "SW-PARAPET-HEIGHT-CONFIRM": "ROOF", "NE-PARAPET-EXTERNAL-FINISH": "ROOF / EXTERNAL FINISH", "EXTERNAL-FINISH-SYSTEM": "EXTERNAL FINISH", "D3-BENCHMARK-IDENTITY": "RECONCILIATION"}[did]
        Q.append(q)
    rs = dict(keep["RECEPTION-SECTION-SOURCE"])
    rs["GROUP"] = "RECEPTION"
    rs["PA04_UPDATE"] = "cold challenge agreed on every plan edge (south wall same plane both floors, flight against it; no section cuts it); beam schedule gives CB6 20x75 on the north edge, CB7 20x75 on the NE line, P.C 20x70 (LOW) at the garden opening"
    rs["QUANTITY_IMPACT_IF_KNOWN"] = {"RVF-S-B_m2_if_continuous": round(2.05 * 8.54, 3), "RVF-N-BEAM_face_m2_provisional": round(5.87 * 0.59, 3), "RVF-S-A-FF_m2_if_PC_lintel": round(3.82 * (9.54 - 4.80), 3)}
    Q.append(rs)
    Q.append(ODQ.item(DECISION_ID="FF-HEIGHT-RULE", LOCATION="first floor rooms (FF_PHYSICAL_FACE_REGISTER: 21 regions, 6 wet)", TRADE="INTERNAL_PLASTER / TILE_PREP",
                      QUESTION="Which plaster height applies to first-floor normal rooms (owner rule as for the GF 3.20, or full storey 4.20 less ceiling), and which tile-preparation height to wet rooms?",
                      WHY_SOURCE_HIERARCHY_FAILED="no finishes schedule; the sections give the 4.20 storey and no ceiling level; the owner's 3.20 is authorised for the GF only",
                      AVAILABLE_EVIDENCE=["HEIGHT_PARAMETER_TABLE (FIRST_NORMAL_INTERNAL NOT_ESTABLISHED)", "FF host-wall lm per room established"],
                      OPTION_A="extend 3.20 to the FF as an owner parameter", OPTION_B="storey height less a stated ceiling drop", OPTION_C_IF_REQUIRED="per-room values",
                      QUANTITY_IMPACT_IF_KNOWN={"FF_host_wall_lm_bedroom_class": ff["BY_ROOM_CLASS"].get("BEDROOM", {}).get("HOST_WALL_LM"), "FF_wet_lm": wet["TOTALS"]["GROSS_HOST_WALL_LM_BY_FLOOR"]["FF"]},
                      BLOCKS_WHAT="every FF plaster / tile-prep area", CAN_OTHER_WORK_CONTINUE=True, VISUAL_CARD="kit/region_map_FF.png", PRIORITY="QUANTITY_AFFECTING_SMALL",
                      TECHNICAL_RECOMMENDATION="A as a parametric quantity, kept separate from the GF revision", GROUP="HEIGHT RULES"))
    gate = ODQ.stop_gate(Q)
    resolved = ["none of the PA03 questions was resolved automatically; NE-PARAPET-EXTERNAL-FINISH gains the challenger's reading (parapet line +11.30 scaled; no finish note on page 7)"]
    C.write("OWNER_DECISION_QUEUE_V4.json", {"ARTIFACT": "OWNER_DECISION_QUEUE", "VERSION": "v4 (PA04)", "QUEUE": Q, "STOP_GATE": gate, "RESOLVED_AUTOMATICALLY": resolved, "GROUPS": sorted({q["GROUP"] for q in Q}), "D3_NOT_RE_ASKED": True})
    # ---- metrics --------------------------------------------------------------------------------------
    m = dict(C.METRICS)
    arts = m.pop("ARTIFACTS", [])
    metrics = {"ARTIFACT": "PA04_METRICS", "PER_WORKSTREAM": m, "TOTAL_RUNTIME_S_IN_PROCESS": round(time.perf_counter() - t0, 1),
               "AI_CALLS": {"COLD_CHALLENGE_READERS": 3, "ARCHITECTURE_REVIEW_AGENT": 1, "ORCHESTRATOR_VISUAL_READS": 12, "NOTE": "reader token use: ~121k / 135k / 132k (from the harness usage lines)"},
               "DETERMINISTIC_OPERATIONS": sum(v.get("DETERMINISTIC_OPS", 0) for v in m.values()),
               "OWNER_DECISIONS": {"CREATED": 1, "RESOLVED": 0, "CARRIED": 6}, "SOURCE_REQUESTS": ["door / window schedule", "finishes schedule", "section or stair detail through the reception opening", "annex parapet detail"],
               "ARTIFACTS_WRITTEN": sorted(set(arts)) + ["PA04_METRICS.json", "PA04_GATE.json"]}
    C.write("PA04_METRICS.json", metrics)
    C.write("PA04_GATE.json", {"ARTIFACT": "PA04_GATE", "WORKSTREAMS": {k: "DONE" for k in results}, "SELF_CHECKS_ALL_MECHANICAL_PASS": all(v["ALL_PASS"] for v in sc.values()),
                               "SEMANTIC_FAILURES": len(failures), "COLD_CHALLENGES": {k: results["challenges"][k][0] for k in results["challenges"]}, "STOP_GATE": gate,
                               "BOUNDARIES": ["no final total", "no BOQ approval", "no pricing", "no procurement", "no material recipe", "no payment certification", "no Firebase / Manager Agent write"]})
    return {"SELF_CHECKS": {k: v["FAILED"] for k, v in sc.items()}, "A22": [(i["ITEM_ID"], i["CLASS"]) for i in items], "COVERAGE_TOTALS": tot, "QUEUE": [(q["DECISION_ID"], q["PRIORITY"]) for q in Q], "GATE": gate,
            "CHALLENGES": results["challenges"]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
