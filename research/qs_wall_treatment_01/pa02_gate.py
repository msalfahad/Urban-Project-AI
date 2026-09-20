"""PA02.5 - incremental A22 (new faces only), ledger additions, rebuilt
OWNER_DECISION_QUEUE (after source exhaustion) and the gate report inputs.

    python3 -m research.qs_wall_treatment_01.pa02_gate
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine import owner_decision_queue as ODQ
from engine import supersession_ledger as SL
from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)


def run() -> dict:
    d1 = json.loads((OUT / "D1_LEVEL_IDENTITY.json").read_text("utf-8"))
    dh = json.loads((OUT / "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json").read_text("utf-8"))
    ref = json.loads((OUT / "ROOF_EDGES_FACADE_FINISH_KERB.json").read_text("utf-8"))
    tw = json.loads((OUT / "TRADES_WET_OPENINGS_FLOORS_COVERAGE.json").read_text("utf-8"))
    cols = json.loads((OUT / "COLUMN_FACE_REGISTER.json").read_text("utf-8"))["COLUMNS"]
    tr = json.loads((OUT / "PLASTER_QUANTITY_TRACE.json").read_text("utf-8"))
    dual = json.loads((OUT / "DUAL_BASIS_v3.json").read_text("utf-8"))
    rb = dual["CONTRACTOR_RULEBOOK"]
    old_led = json.loads((OUT / "REVISION_SUPERSESSION_LEDGER.json").read_text("utf-8"))
    # ---- incremental A22 on the new components only ------------------------------------
    items = []
    def item(iid, where, eng, eb, con, cb, drivers, cls, indep, shared, note=None):
        delta = round(con - eng, 4) if isinstance(eng, (int, float)) and isinstance(con, (int, float)) else None
        items.append({"ITEM_ID": iid, "LOCATION": where, "ENGINEERING": eng, "ENGINEERING_BASIS": eb, "CONTRACTOR": con, "CONTRACTOR_BASIS": cb,
                      "DELTA_CONTRACTOR_MINUS_ENGINEERING": delta, "DRIVERS": drivers, "CLASS": cls, "SOURCE_INDEPENDENCE": indep,
                      "SHARED_ASSUMPTIONS": shared, "CONDITIONAL": "IF_BENCHMARK_IS_P7757", "NEVER_AVERAGED": True, "NOTE": note})
    stw = dh["STAIR_WALL_GROSS_SUBTOTAL_BY_STOREY_M2"]
    eng_stair = round(sum(stw.values()), 3)
    con_stair = round(2 * (2.50 + 6.45) * rb["HEIGHT_STAIRWELL"]["VALUE"], 3)
    item("A22-5-STAIR-WELL", "block stair well, 4 faces x 3 storeys", eng_stair, "per-storey faces +0.30/+5.50/+9.70/+13.90 x printed 2.50 x 6.45 well (gross, interruptions listed)",
         con_stair, f"site record: stair-well walls one line at {rb['HEIGHT_STAIRWELL']['VALUE']} m x the same perimeter",
         ["HEIGHT_RULE_DIFFERENCE", "MEASUREMENT_BASIS_DIFFERENCE"], "MEASUREMENT_BASIS_DIFFERENCE",
         "engineering: sections + printed well dimensions; contractor: site record", ["perimeter"],
         "the 12.90 line and the storey split differ by 0.70 (the +0.30 foot) and by nothing else on gross; landings and the top window are not deducted on either side")
    ne = next(l for l in tr["LINES"] if l["LINE_ID"] == "FACE:F-NE-SOLID-ROOFSIDE")
    item("A22-5-NE-ROOFSIDE-CORRECTED", "NE parapet roof-side (corrected 1.40 face)", ne["VALUE"], "18.87 x 1.40 (band separate)", round(18.87 * 1.70, 3),
         "18.87 x 1.70 parapet rule", ["HEIGHT_RULE_DIFFERENCE"], "MEASUREMENT_BASIS_DIFFERENCE", "engineering: A-A + NE elevation; contractor: site record", ["length"],
         "supersedes A22-4-FACE:F-NE-SOLID-ROOFSIDE (1.652 face)")
    c = next(x for x in cols if x["COLUMN_ID"].startswith("LOOP-059"))
    item("A22-5-COLUMN-FACES", "LOOP-059 exposed girth", c["EXPOSED_PLASTERABLE_GIRTH_LM"], "4 exposed faces (free-standing) of the 30 x 60 section",
         None, "not itemised in the record as a girth", ["UNRESOLVED"], "UNRESOLVED", "engineering only", [], "the record's column item identity is not established")
    wet = tw["WET_ROOM_REGISTER"]
    item("A22-5-WET-ROOM-LENGTHS", "GF wet rooms", wet["GF_WALL_LENGTH_LM_PROVISIONAL"], "E1.4 material chain lengths (lm), area NOT_ESTABLISHED",
         None, "record lists tile-preparation areas by room (not compared: no engineering area yet)", ["SCOPE_DIFFERENCE"], "SCOPE_DIFFERENCE", "different sources", [],
         "lengths only; an area comparison waits for the wet-room treatment height")
    item("A22-5-SE-FACADE-NET", "SE facade net faces", round(sum(v["NET_M2"] for v in ref["SE_FACADE_FACES"].values() if v["NET_M2"]), 3),
         "GEOMETRIC_REFERENCE_ONLY (finish system unknown): tower 51.24 + main block 36.42 net of openings", None,
         "whole-facade heights x lengths, half openings (record)", ["SCOPE_DIFFERENCE", "OPENING_RULE_DIFFERENCE", "HEIGHT_RULE_DIFFERENCE"], "SCOPE_DIFFERENCE",
         "different sources", [], "no external plaster quantity exists on the engineering side until the finish system is classified")
    # ---- ledger additions ------------------------------------------------------------------
    L = list(old_led["ENTRIES"])
    def led(i, prev, art, mark, by, ev):
        L.append(SL.entry(ledger_id=i, previous_statement=prev, previous_artifact=art, mark=mark, replaced_by=by, evidence=ev, date="2026-09-20"))
    led("L-08", "DWG elevation blob = SOUTH EAST elevation (mirrored)", "ROOF_EDGE_PLAN_TO_ELEVATION_LINK_REGISTER.json DWG_ELEVATION_SAME_FAMILY", "CORRECTED_BY_OWNER_EVIDENCE",
        "the blob is the NORTH WEST elevation (printed 155 / 269 / 305 / 230 match the NW raster sheet); its +9.856 / +9.883 lines belong to the NW roof edge",
        "D1_LEVEL_IDENTITY.json CORRECTION; nat_NW page 6")
    led("L-09", "NE parapet roof-side face 1.652 m (A-A hatch)", "PARAPET_ASSEMBLY_REGISTER.json v1 / PLASTER_QUANTITY_TRACE v4 (first run)", "SUPERSEDED",
        "face 1.40 to the band underside (+11.10) + 0.20 band: A-A hatch 1.62 = 1.40 + 0.20; NE elevation wall top +11.27 by chain scale", "ROOF_EDGES_FACADE_FINISH_KERB.json ROOF_EDGE_REGISTER NE")
    led("L-10", "GF-RECEPTION-DOUBLE-HEIGHT: DOUBLE_HEIGHT_PLASTER_HEIGHT unknown", "P7757_WALL_TREATMENT_ESTIMATE_v3.json face-set plan (frozen)", "SUPERSEDED",
        "the FF void over the reception is a stair well bounded by railings; no wall stands on its boundary; reception walls are normal-height faces", "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json")
    led("L-11", "NW-THIN-EDGE-ELEMENT: material unknown (solid upstand vs screen)", "OWNER_DECISION_QUEUE.json (PA01)", "SUPERSEDED",
        "X-lattice balustrade on a low curved kerb (NW elevation page 6; B-B thin element with cap); zero plaster for the lattice", "ROOF_EDGES_FACADE_FINISH_KERB.json NW_SEA_VIEW")
    led("L-12", "SW-PARAPET-HEIGHT: no source", "OWNER_DECISION_QUEUE.json (PA01)", "SUPERSEDED",
        "the SE elevation's end pier SEG-04 is the SW parapet end-on: ~1.35 above the base line (PROVISIONAL, PROPOSED_CORRESPONDENCE)", "ROOF_EDGES_FACADE_FINISH_KERB.json SW")
    led("L-13", "D1 as an owner A/B choice between +9.70 and +9.88", "OWNER_DECISION_QUEUE.json (PA01) D1-SE-ROOFSIDE-BOTTOM", "SUPERSEDED",
        "dual basis preserved (visible-finish 1.22 / executed 1.40); the open item is the roof build-up thickness (information), not a binary", "D1_LEVEL_IDENTITY.json")
    led("L-14", "D2 column girth 1.80 lm taken as 2 x (0.30 + 0.60)", "PLASTER_QUANTITY_TRACE v4 D2:COLUMN:LOOP-059", "SUPERSEDED_IN_PART",
        "girth rebuilt face by face: all four faces exposed (free-standing), so the value stands at 1.80 with the per-face record", "COLUMN_FACE_REGISTER.json")
    # ---- rebuilt owner queue ------------------------------------------------------------------
    Q = []
    def q(**k):
        Q.append(ODQ.item(**k))
    q(DECISION_ID="D1-ROOF-BUILDUP-INFO", LOCATION="roof +9.70 terrace, all parapet roof-side faces", TRADE="ROOF_SIDE_PARAPET plaster",
      QUESTION="What roof build-up sits on the +9.70 slab (screed / insulation / tiles) and how thick is it? Is +9.88 the finished roof level?",
      WHY_SOURCE_HIERARCHY_FAILED="sections draw no build-up; roof build-up detail SOURCE_NOT_PROVIDED; two edges draw a level line 0.16-0.18 above the slab",
      AVAILABLE_EVIDENCE=["D1_LEVEL_IDENTITY.json (eight level fields, sources exhausted)", "SE raster base line ~+9.90", "DWG NW elevation lines +9.856 / +9.883", "structural +9.70 on the slab"],
      OPTION_A="build-up ~0.18: +9.88 is the finished roof; visible-finish face 1.22, executed face 1.40 (both carried)",
      OPTION_B="no build-up: the two bases coincide at 1.40", OPTION_C_IF_REQUIRED="other thickness: state it",
      QUANTITY_IMPACT_IF_KNOWN={"m2_between_bases_SE_solid": d1["D1_DUAL_BASIS"]["QUANTITY_DIFFERENCE_M2"], "per_metre_run": 0.18},
      BLOCKS_WHAT="nothing: both bases are carried", CAN_OTHER_WORK_CONTINUE=True, VISUAL_CARD="decision_cards/D1_SE_PARAPET_SOURCE_CARD.png; visual_qa/SE_ELEVATION_FACES.png",
      PRIORITY="INFORMATION", TECHNICAL_RECOMMENDATION="carry both; executed basis (from the slab) for site quantities, visible-finish basis for engineering net")
    q(DECISION_ID="D3-BENCHMARK-IDENTITY", LOCATION="contractor workbook (uploads b324a3e7 / c495ff6e), Invoice No. 5", TRADE="reconciliation only",
      QUESTION="Is Invoice No. 5 / this plaster workbook definitely the P7757 contractor / site record?",
      WHY_SOURCE_HIERARCHY_FAILED="no project identifier inside the workbook", AVAILABLE_EVIDENCE=["BENCHMARK_RECONCILIATION.json", "DUAL_BASIS_v3.json"],
      OPTION_A="yes -> reconciliation unconditional", OPTION_B="no -> reconciliation withdrawn; geometry unaffected", OPTION_C_IF_REQUIRED=None,
      QUANTITY_IMPACT_IF_KNOWN="none on engineering geometry", BLOCKS_WHAT="unconditional A22 only", CAN_OTHER_WORK_CONTINUE=True,
      VISUAL_CARD="none (identity)", PRIORITY="CLASSIFICATION_ONLY")
    q(DECISION_ID="NE-PARAPET-EXTERNAL-FINISH", LOCATION="roof +9.70, NE (neighbour) parapet outer face 18.27 m x 1.40", TRADE="PARAPET_PLASTER (external)",
      QUESTION="Is the neighbour-facing outer face of the NE parapet plastered?",
      WHY_SOURCE_HIERARCHY_FAILED="no elevation of the neighbour side exists in the set; finishes specification SOURCE_NOT_PROVIDED; sources exhausted",
      AVAILABLE_EVIDENCE=["geometric face 25.58 m2 (18.27 x 1.40) GEOMETRIC_REFERENCE_ONLY", "A-A PAR-07 hatched cut"],
      OPTION_A="plastered like the roof side", OPTION_B="not finished (boundary condition)", OPTION_C_IF_REQUIRED="other trade",
      QUANTITY_IMPACT_IF_KNOWN={"m2_if_eligible": round(18.27 * 1.40, 3)}, BLOCKS_WHAT="one parapet line", CAN_OTHER_WORK_CONTINUE=True,
      VISUAL_CARD="visual_qa/ROOF_PLAN_EDGES.png; visual_qa/NE_PARAPET_TOP.png", PRIORITY="QUANTITY_AFFECTING_SMALL", TECHNICAL_RECOMMENDATION="A (a 1.40 m parapet face above a neighbour wall is normally finished)")
    q(DECISION_ID="EXTERNAL-FINISH-SYSTEM", LOCATION="plain external faces: tower, main block, annex (SE); NE / NW facades", TRADE="EXTERNAL_PLASTER / CLADDING_BASE",
      QUESTION="Which external finish system applies to the plain facade faces (plaster, cladding over plaster base, cladding only)? The entrance arch is confirmed cladding.",
      WHY_SOURCE_HIERARCHY_FAILED="searched: elevations (no hatch / notes), sections (B-B outer skin element unexplained), DWG layers (no finish layer), no detail sheets, no finish notes; sources exhausted",
      AVAILABLE_EVIDENCE=["EXTERNAL_FINISH_REGISTER (5 elements classified)", "SE net faces: tower 51.24, main block 36.42 m2 GEOMETRIC_REFERENCE_ONLY"],
      OPTION_A="plaster on all plain faces", OPTION_B="cladding (stone / GRC) over a plaster base coat", OPTION_C_IF_REQUIRED="mixed by face: state which",
      QUANTITY_IMPACT_IF_KNOWN="the whole EXTERNAL_PLASTER category (SE reference net 87.65 m2 so far)", BLOCKS_WHAT="EXTERNAL_PLASTER lines", CAN_OTHER_WORK_CONTINUE=True,
      VISUAL_CARD="visual_qa/SE_FACADE_OPENINGS.png", PRIORITY="CLASSIFICATION_ONLY", TECHNICAL_RECOMMENDATION="answer per face group; the geometric net is ready for either")
    q(DECISION_ID="SW-PARAPET-HEIGHT-CONFIRM", LOCATION="roof +9.70, SW edge parapet 4.33 m", TRADE="ROOF_SIDE_PARAPET plaster",
      QUESTION="Confirm the SW parapet height: the SE elevation shows it end-on ~1.35 above the base line (~1.53 above the slab) - is that its height along the whole edge?",
      WHY_SOURCE_HIERARCHY_FAILED="no section cuts it and no elevation faces it; the end-on view is PROPOSED_CORRESPONDENCE",
      AVAILABLE_EVIDENCE=["SE elevation SEG-04 polygon (0.33 wide, rounded top)", "DWG lines 4.325 / 4.125"],
      OPTION_A="yes: 1.53 above the slab along the edge (carried PROVISIONAL)", OPTION_B="no: site measure supplied", OPTION_C_IF_REQUIRED=None,
      QUANTITY_IMPACT_IF_KNOWN={"m2_roof_side_candidate": round(1.53 * 4.125, 3)}, BLOCKS_WHAT="one parapet line", CAN_OTHER_WORK_CONTINUE=True,
      VISUAL_CARD="visual_qa/SE_ELEVATION_FACES.png (pier at the left end)", PRIORITY="QUANTITY_AFFECTING_SMALL", TECHNICAL_RECOMMENDATION="A")
    gate = ODQ.stop_gate(Q)
    withdrawn = ["NW-THIN-EDGE-ELEMENT (resolved from the NW elevation: lattice on a kerb)", "SW-PARAPET-HEIGHT (replaced by a confirmation item)",
                 "D1-SE-ROOFSIDE-BOTTOM as an A/B choice (replaced by the build-up information item)"]
    technical = [{"ID": "T-STAIR-SPINE", "WHAT": "role and height of the 10 cm element between the block-stair flights (balustrade wall vs wall)", "SOURCE_TO_CHECK": "A-A native at the flights; FF sheet section marks"},
                 {"ID": "T-STAIR-UNDERSIDE", "WHAT": "flight soffits from A-A slopes x the printed 1.20 flight width", "SOURCE_TO_CHECK": "A-A native"},
                 {"ID": "T-FF-WALLS", "WHAT": "first-floor room faces (E1.4-style chains on the FF copy)", "SOURCE_TO_CHECK": "DWG FF copy"},
                 {"ID": "T-ANNEX-PARAPET-RUN", "WHAT": "trace the +4.30 annex roof parapet run line by line", "SOURCE_TO_CHECK": "DWG FF copy outline"},
                 {"ID": "T-NE-NW-OPENINGS", "WHAT": "NE / NW facade openings (the NW elevation prints 155 / 269 / 305 widths)", "SOURCE_TO_CHECK": "pages 6 / 7 + DWG NW elevation blob (authored!)"},
                 {"ID": "T-WET-HEIGHT", "WHAT": "wet-room treatment height (tile height) from the finishes schedule if provided", "SOURCE_TO_CHECK": "SOURCE_NOT_PROVIDED"},
                 {"ID": "T-KERB-CURVE", "WHAT": "ink-trace the kerb ogee at native resolution (now a 6-vertex polyline lower bound)", "SOURCE_TO_CHECK": "page 4 native"}]
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "PA02_GATE", "A22_INCREMENTAL_V5": {"ITEMS": items, "SCOPE": "new components only; PA01 items not rerun"},
           "OWNER_DECISION_QUEUE_V2": Q, "STOP_GATE": gate, "WITHDRAWN_FROM_QUEUE": withdrawn, "TECHNICAL_FOLLOW_UPS_NOT_OWNER": technical,
           "BENCHMARK_RECONCILIATION": "CONDITIONAL_IF_P7757", "BENCHMARK_IDENTITY": "OWNER_CONFIRMATION_REQUIRED"}
    (OUT / "PA02_GATE.json").write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    (OUT / "OWNER_DECISION_QUEUE.json").write_text(json.dumps({"PHASE_ID": P.PHASE_ID, "ARTIFACT": "OWNER_DECISION_QUEUE", "VERSION": "v2 (PA02)", "QUEUE": Q, "STOP_GATE": gate,
                                                                "WITHDRAWN": withdrawn, "TECHNICAL_FOLLOW_UPS_NOT_OWNER": technical}, indent=2, default=str) + "\n", encoding="utf-8")
    (OUT / "A22_RECONCILIATION_REGISTER_v5.json").write_text(json.dumps({"PHASE_ID": P.PHASE_ID, "ARTIFACT": "A22_RECONCILIATION_REGISTER", "VERSION": "v5 (incremental)", "ITEMS": items,
                                                                          "NOT_MAJORITY_VOTING": True, "NO_TUNING": True}, indent=2, default=str) + "\n", encoding="utf-8")
    ledger = dict(old_led, ENTRIES=L)
    (OUT / "REVISION_SUPERSESSION_LEDGER.json").write_text(json.dumps(ledger, indent=2, default=str) + "\n", encoding="utf-8")
    return {"A22": [(i["ITEM_ID"], i["ENGINEERING"], i["CONTRACTOR"], i["CLASS"]) for i in items], "QUEUE": [(x["DECISION_ID"], x["PRIORITY"]) for x in Q], "GATE": gate, "LEDGER": len(L)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
