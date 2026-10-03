"""PA03 gate: dependent quantities regenerated from the correction layer
(only what depended on the reopened items), incremental A22 v6, the owner
queue rebuilt (v3), ledger entries L-15.., a leakage scan of the new
registers and the gate record.  Frozen PA01 / PA02 quantity files are not
rewritten; corrections live in PA03_DEPENDENT_QUANTITIES.json.

    python3 -m research.qs_wall_treatment_01.pa03_gate
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from engine import owner_decision_queue as ODQ
from engine import supersession_ledger as SL
from engine import benchmark_protection as BP
from research.qs_wall_treatment_01 import protocol as P
from research.qs_wall_treatment_01.decision_queue_v4 import _num_scan

OUT = Path(P.OUT_DIR)
DATE = "2026-09-20"
NEW_REGISTERS = ["VOID_GEOMETRY_RECONCILIATION.json", "RECEPTION_VERTICAL_FACE_REGISTER.json", "STAIR_COMPONENT_REGISTER_V2.json",
                 "COLUMN_VERTICAL_EXPOSURE_REGISTER.json", "NE_ELEVATION_FINISH_ELIGIBILITY_REGISTER.json", "SE_OPENING_DIMENSION_OWNERSHIP_AUDIT.json",
                 "PA02_SOURCE_REVIEW_SUPERSESSION_LEDGER.json", "QA_RENDER_VALIDITY_REGISTER.json"]


def run() -> dict:
    void = json.loads((OUT / "VOID_GEOMETRY_RECONCILIATION.json").read_text("utf-8"))
    rv = json.loads((OUT / "RECEPTION_VERTICAL_FACE_REGISTER.json").read_text("utf-8"))
    st = json.loads((OUT / "STAIR_COMPONENT_REGISTER_V2.json").read_text("utf-8"))
    col = json.loads((OUT / "COLUMN_VERTICAL_EXPOSURE_REGISTER.json").read_text("utf-8"))["COLUMNS"][0]
    ne = json.loads((OUT / "NE_ELEVATION_FINISH_ELIGIBILITY_REGISTER.json").read_text("utf-8"))["FACES"][0]
    se = json.loads((OUT / "SE_OPENING_DIMENSION_OWNERSHIP_AUDIT.json").read_text("utf-8"))
    tr = json.loads((OUT / "PLASTER_QUANTITY_TRACE.json").read_text("utf-8"))
    tw = json.loads((OUT / "TRADES_WET_OPENINGS_FLOORS_COVERAGE.json").read_text("utf-8"))
    dual = json.loads((OUT / "DUAL_BASIS_v3.json").read_text("utf-8"))
    rb = dual["CONTRACTOR_RULEBOOK"]
    old_led = json.loads((OUT / "REVISION_SUPERSESSION_LEDGER.json").read_text("utf-8"))
    old_q = json.loads((OUT / "OWNER_DECISION_QUEUE.json").read_text("utf-8"))
    objs = void["OBJECTS_PRESERVED"]
    # ---- dependent quantities ---------------------------------------------------------------
    lines = []
    def line(**k):
        lines.append(k)
    g = col["COLUMN_EXPOSED_GIRTH_LM"]
    line(LINE_ID="PA03:D2:COLUMN:LOOP-059:girth", CATEGORY="COLUMN_BONDING", FLOOR="GROUND", ZONE="reception NE wall line (garden strip side)", UNIT="lm", VALUE=g["VALUE"],
         QUANTITY_STATE="PROVISIONAL_QUANTITY", SUPERSEDES="PLASTER_QUANTITY_TRACE D2:COLUMN:LOOP-059:girth (1.80)",
         PROVENANCE={"faces": [f["FACE"].split(" (")[0] + ": " + f["EXPOSURE"] for f in col["FACES"]], "alternative_structural_depth": col["GIRTH_ALTERNATIVES"]["STRUCTURAL_300_DEEP"], "selected": None})
    line(LINE_ID="PA03:D2:COLUMN:LOOP-059:area", CATEGORY="COLUMN_BONDING", FLOOR="GROUND", ZONE="reception NE wall line", UNIT="m2", VALUE=col["COLUMN_BONDING_AREA_M2"]["VALUE"],
         QUANTITY_STATE="NOT_ESTABLISHED", SUPERSEDES="PLASTER_QUANTITY_TRACE D2:COLUMN:LOOP-059 (5.76 m2)",
         PROVENANCE={"height": col["COLUMN_EXPOSED_HEIGHT_M"], "why": "exposed height not established (beam soffit over the column not read)"})
    line(LINE_ID="PA03:D2:COLUMN:LOOP-059:area:owner_parametric", CATEGORY="COLUMN_BONDING", FLOOR="GROUND", ZONE="reception NE wall line", UNIT="m2",
         VALUE=col["OWNER_PARAMETRIC_AREA_M2"]["VALUE"], QUANTITY_STATE="OWNER_PARAMETRIC_QUANTITY", SUPERSEDES=None,
         PROVENANCE={"basis": col["OWNER_PARAMETRIC_AREA_M2"]["BASIS"], "is_physical_area": False})
    line(LINE_ID="PA03:D2:COLUMN:LOOP-059:external_face", CATEGORY="EXTERNAL_FACADE", FLOOR="GROUND", ZONE="garden strip", UNIT="lm", VALUE=col["EXTERNAL_FACE_LM"],
         QUANTITY_STATE="GEOMETRIC_REFERENCE_ONLY", SUPERSEDES=None, PROVENANCE={"why": "external finish system unknown"})
    for f in rv["VERTICAL_FACES"]:
        line(LINE_ID=f"PA03:RECEPTION:{f['FACE_ID']}", CATEGORY="DOUBLE_HEIGHT_WALL" if "S-B" in f["FACE_ID"] or "W-FF" in f["FACE_ID"] or "S-A" in f["FACE_ID"] else "NORMAL_INTERNAL_WALL",
             FLOOR="GROUND+FIRST", ZONE="RECEPTION opening", UNIT="m2", VALUE=None, QUANTITY_STATE="NOT_ESTABLISHED", SUPERSEDES="DOUBLE_HEIGHT_AND_STAIR_REGISTERS: 'no double-height wall'",
             PROVENANCE={"length_m": f["LENGTH_M"], "height": f["HEIGHT"], "status": f["STATUS"]})
    for s in st["STAIRS"][1]["STOREY_REFERENCE_GROSS_M2"].items():
        line(LINE_ID=f"PA03:BLOCK-STAIR:{s[0]}:reference_gross", CATEGORY="STAIR_WALL", FLOOR=s[0], ZONE="block stair well", UNIT="m2", VALUE=s[1],
             QUANTITY_STATE="GEOMETRIC_REFERENCE_ONLY", SUPERSEDES=f"DOUBLE_HEIGHT_AND_STAIR_REGISTERS STAIR_WALL_GROSS_SUBTOTAL_BY_STOREY_M2[{s[0]}] (PROVISIONAL_QUANTITY)",
             PROVENANCE={"why": "four faces x storey height is a perimeter x storey figure; faces now carry exposure / openings / landing / occlusion fields without deductions"})
    elem = st["STAIRS"][1]["MID_ELEMENT"]
    line(LINE_ID="PA03:BLOCK-STAIR:MID-ELEMENT", CATEGORY="STAIR_WALL", FLOOR="GROUND+FIRST+ROOF", ZONE="block stair well", UNIT="m2", VALUE=None, QUANTITY_STATE="NOT_ESTABLISHED",
         SUPERSEDES=None, PROVENANCE={"role": elem["ROLE"], "excluded": elem["EXCLUDED_ROLES"], "eligibility": elem["PLASTER_WALL_ELIGIBILITY"]})
    # ceiling exclusion: computed only now that the void objects are fixed (directive §6); informational, outside the wall-treatment trades
    arcs = st["STAIRS"][0]["COMPONENTS"][0]["ARCS_GF"]
    r_out = max(a["R_MM"] for a in arcs) / 1000; r_in = min(a["R_MM"] for a in arcs) / 1000
    sweep = 1.6317  # inner / outer railing arc sweep (CAD-569 / CAD-573), radians
    curved_footprint = round(0.5 * sweep * (r_out ** 2 - r_in ** 2), 3)
    zone_a = objs["VOID_STAIR_ZONE"]["AREA_M2"]; slab_a = objs["SLAB_OPENING"]["AREA_M2"]
    strip_a = round(objs["STRAIGHT_FLIGHT_STRIP"]["WIDTH_M"] * objs["STRAIGHT_FLIGHT_STRIP"]["DEPTH_M"], 3)
    ceiling = {"COMPUTED_AFTER_VOID_RECONCILIATION": True, "VOID_STAIR_ZONE_M2": zone_a, "SLAB_OPENING_M2": slab_a, "STRAIGHT_FLIGHT_STRIP_M2": strip_a,
               "CURVED_FLIGHT_FOOTPRINT_M2_PROVISIONAL": curved_footprint,
               "GF_RECEPTION_CEILING": {"NO_SLAB_SOFFIT_OVER": "SLAB_OPENING (open to the FF ceiling)", "STAIR_SOFFIT_INSTEAD_OF_SLAB_OVER": "STRAIGHT_FLIGHT_STRIP + the curved flight footprint inside the SLAB_OPENING",
                                       "OPEN_TO_FF_CEILING_M2_PROVISIONAL": round(slab_a - curved_footprint, 3), "REMAINDER_OF_ZONE_M2": round(zone_a - slab_a - strip_a, 3),
                                       "REMAINDER_NOTE": "railing strips (50 mm) and the west part of the flight strip under the curved flight's landing zone; not a ceiling quantity"},
               "SCOPE": "informational for the ceiling trade; not a wall-treatment quantity; states PROVISIONAL"}
    # floor-by-floor deltas (what changes in TRADES_WET_OPENINGS_FLOORS_COVERAGE without rewriting it)
    fb = tw["FLOOR_BY_FLOOR"]
    deltas = {"GROUND": {"COLUMN_BONDING_M2": {"WAS": fb["GROUND"]["COLUMN_BONDING_M2"], "NOW": {"m2": {"OWNER_PARAMETRIC_QUANTITY": round(0.96 + 0.64 + col["OWNER_PARAMETRIC_AREA_M2"]["VALUE"], 4)}, "lm": {"PROVISIONAL_QUANTITY": round(0.3 + 0.2 + g["VALUE"], 2)},
                                                                                                     "NOTE": "LOOP-059 physical area NOT_ESTABLISHED; 2.40 is parametric (0.75 x 3.20); COL-01 / COL-02 unchanged (v3 parametric)"}},
                         "STAIR_WALL_M2": {"WAS": fb["GROUND"]["STAIR_WALL_M2"], "NOW": {"m2": {}, "GEOMETRIC_REFERENCE_ONLY": st["STAIRS"][1]["STOREY_REFERENCE_GROSS_M2"]["GF"]}},
                         "DOUBLE_HEIGHT_WALL_M2": {"WAS": "category closed (no wall)", "NOW": {"m2": {}, "NOTE": "three NOT_ESTABLISHED faces (RVF-S-B candidate, RVF-W-FF, RVF-S-A-FF)"}}},
              "FIRST": {"STAIR_WALL_M2": {"WAS": fb["FIRST"]["STAIR_WALL_M2"], "NOW": {"m2": {}, "GEOMETRIC_REFERENCE_ONLY": st["STAIRS"][1]["STOREY_REFERENCE_GROSS_M2"]["FF"]}}},
              "SECOND_ROOF": {"STAIR_WALL_M2": {"WAS": fb["SECOND_ROOF"]["STAIR_WALL_M2"], "NOW": {"m2": {}, "GEOMETRIC_REFERENCE_ONLY": st["STAIRS"][1]["STOREY_REFERENCE_GROSS_M2"]["ROOF"]}}}}
    cov_rows = [
        {"FLOOR": "GROUND", "ZONE": "RECEPTION", "TRADE": "NORMAL_INTERNAL_PLASTER / DOUBLE_HEIGHT_PLASTER", "EXPECTED_COMPONENTS": "perimeter faces + the opening's vertical faces (RVF-S-B candidate double height, RVF-W-FF, RVF-S-A-FF)",
         "ESTABLISHED_COMPONENTS": [], "PROVISIONAL_COMPONENTS": [], "UNRESOLVED_COMPONENTS": ["RVF-S-B height (no section)", "RVF-W-FF bottom (beam soffit)", "RVF-S-A-FF bottom (opening head)"],
         "NOT_STARTED_COMPONENTS": ["perimeter faces not traced"], "COVERAGE_STATUS": "PARTIAL (faces identified, none quantified)"},
        {"FLOOR": "GROUND", "ZONE": "reception NE wall line", "TRADE": "COLUMN_BONDING", "EXPECTED_COMPONENTS": "LOOP-059 + piers COL-01 / COL-02",
         "ESTABLISHED_COMPONENTS": [], "PROVISIONAL_COMPONENTS": [f"LOOP-059 {g['VALUE']} lm internal (0.85 structural depth)", "COL-01 0.30", "COL-02 0.20"],
         "UNRESOLVED_COMPONENTS": ["LOOP-059 exposed height", "LOOP-059 external face finish"], "NOT_STARTED_COMPONENTS": [], "COVERAGE_STATUS": "PARTIAL"},
        {"FLOOR": "GROUND+FIRST+ROOF", "ZONE": "block stair", "TRADE": "STAIR_WALL_PLASTER", "EXPECTED_COMPONENTS": "12 faces + mid element + landings + soffits",
         "ESTABLISHED_COMPONENTS": [], "PROVISIONAL_COMPONENTS": [], "UNRESOLVED_COMPONENTS": ["mid element role", "face deductions (landings / openings / occlusion)"],
         "NOT_STARTED_COMPONENTS": ["flight soffits", "landing soffits"], "COVERAGE_STATUS": "GEOMETRIC_REFERENCE_ONLY (12 faces registered)"}]
    dep = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "PA03_DEPENDENT_QUANTITIES", "LAYER": "PA03_SOURCE_REVIEW_CORRECTION",
           "RULE": "frozen PA01 / PA02 quantity files are not rewritten; each line here names the line it supersedes; states per line; never a total",
           "LINES": lines, "CEILING_EXCLUSION_INFORMATIONAL": ceiling, "FLOOR_BY_FLOOR_DELTAS": deltas, "COVERAGE_MATRIX_ROWS_CORRECTED": cov_rows,
           "UNCHANGED_PA02_REGISTERS": ["D1_LEVEL_IDENTITY", "ROOF_EDGES_FACADE_FINISH_KERB (SE openings confirmed in part by the ownership audit; NE band fields qualified)", "TRADES_WET_OPENINGS_FLOORS_COVERAGE except the rows above",
                                        "FACE_MEASUREMENT_REGISTER / PARAPET_ASSEMBLY_REGISTER / QS_MEASUREMENT_REGION_REGISTER / OPENING_REGISTER_v4"]}
    (OUT / "PA03_DEPENDENT_QUANTITIES.json").write_text(json.dumps(dep, indent=2, default=str) + "\n", encoding="utf-8")
    # ---- incremental A22 v6 --------------------------------------------------------------------
    items = []
    def item(iid, where, eng, eb, con, cb, drivers, cls, indep, shared, note=None):
        delta = round(con - eng, 4) if isinstance(eng, (int, float)) and isinstance(con, (int, float)) else None
        items.append({"ITEM_ID": iid, "LOCATION": where, "ENGINEERING": eng, "ENGINEERING_BASIS": eb, "CONTRACTOR": con, "CONTRACTOR_BASIS": cb,
                      "DELTA_CONTRACTOR_MINUS_ENGINEERING": delta, "DRIVERS": drivers, "CLASS": cls, "SOURCE_INDEPENDENCE": indep, "SHARED_ASSUMPTIONS": shared,
                      "CONDITIONAL": "IF_BENCHMARK_IS_P7757", "NEVER_AVERAGED": True, "NOTE": note})
    items.append({"ITEM_ID": "A22-6-VOID-PRINTED-VS-DWG-VS-A21", "LOCATION": "FF opening over the reception",
                  "PRINTED_RASTER": {"W": 5.87, "D": 4.00, "SOURCE": "FF sheet page 2 (plot of the DWG)"}, "DWG_AUTHORED": {"W": 5.87, "D": 4.00, "SOURCE": "dimension entities 587 / 400 (geometry 5870 / 4000)"},
                  "DWG_X_RECTANGLE": {"W": objs["SLAB_OPENING"]["WIDTH_M"], "D": objs["SLAB_OPENING"]["DEPTH_M"]}, "STRUCTURAL_P4_X": {"W": objs["SLAB_OPENING"]["STRUCTURAL_P4_X_M"][0], "D": objs["SLAB_OPENING"]["STRUCTURAL_P4_X_M"][1]},
                  "A21_PA02_INTERPRETATION": {"W": 5.82, "D": 2.75, "SOURCE": "PA02 read the X only"},
                  "CLASS": "IDENTITY_MAPPING_DIFFERENCE (two objects: VOID_STAIR_ZONE vs SLAB_OPENING); no numeric disagreement between printed and DWG",
                  "SOURCE_INDEPENDENCE": "raster and DWG are the same author (the sheet is plotted from the DWG): NOT independent; structural p4 is an independent author and agrees with the X",
                  "CONDITIONAL": "not a benchmark item", "NEVER_AVERAGED": True})
    items.append({"ITEM_ID": "A22-6-RECEPTION-FACES-BY-SOURCE", "LOCATION": "reception opening vertical faces",
                  "PLAN_DWG": "edges and wall layers per copy (solid vs dashed): RV-N / RV-E open with railings; RV-S-A GF opening under an FF wall; RV-S-B wall on both floors; RV-W FF wall over an open GF edge",
                  "SECTION": "none cuts or faces the opening (A-A behind it, B-B looks away)", "ELEVATION": "none shows the interior", "STRUCTURAL": "p4 X = slab opening; beam pair under the flight strip; beam lines on the north edge and at the column",
                  "SOURCE_DEPENDENCE": "single architectural source for the vertical model (plan copies); the structural set corroborates the opening, not the wall heights",
                  "CONSEQUENCE": "every vertical face stays NOT_ESTABLISHED / PROVISIONAL; DOUBLE_HEIGHT_WALL_STATUS = " + rv["DOUBLE_HEIGHT"]["DOUBLE_HEIGHT_WALL_STATUS"], "CONDITIONAL": "not a benchmark item", "NEVER_AVERAGED": True})
    item("A22-6-COLUMN-GIRTH", "LOOP-059 internal plasterable girth", g["VALUE"], "N face 0.60 + W sliver 0.05 + E sliver 0.10 (arch 250 depth); 0.85 on the structural 300 depth", None,
         "not itemised in the record as a girth", ["UNRESOLVED"], "UNRESOLVED", "engineering only", [], "supersedes A22-5-COLUMN-FACES (1.80)")
    item("A22-6-STAIR-WELL", "block stair well, 12 faces x 3 storeys", None, "GEOMETRIC_REFERENCE_ONLY (reference gross 93.08 / 75.18 / 75.18, not a quantity)",
         round(2 * (2.50 + 6.45) * rb["HEIGHT_STAIRWELL"]["VALUE"], 3), f"site record: one line at {rb['HEIGHT_STAIRWELL']['VALUE']} m x the well perimeter",
         ["MEASUREMENT_BASIS_DIFFERENCE"], "MEASUREMENT_BASIS_DIFFERENCE", "engineering: DWG dims + A-A; contractor: site record", ["perimeter 2 x (2.50 + 6.45)"],
         "supersedes A22-5-STAIR-WELL: the engineering side no longer carries a quantity, so no delta is computed")
    a22 = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "A22_RECONCILIATION_REGISTER", "VERSION": "v6 (incremental, PA03)", "ITEMS": items, "NOT_MAJORITY_VOTING": True, "NO_TUNING": True,
           "BENCHMARK_IDENTITY": "OWNER_CONFIRMATION_REQUIRED (D3, not re-asked)"}
    (OUT / "A22_RECONCILIATION_REGISTER_v6.json").write_text(json.dumps(a22, indent=2, default=str) + "\n", encoding="utf-8")
    # ---- ledger additions (forward only) --------------------------------------------------------
    L = list(old_led["ENTRIES"])
    def led(i, prev, art, mark, by, ev):
        L.append(SL.entry(ledger_id=i, previous_statement=prev, previous_artifact=art, mark=mark, replaced_by=by, evidence=ev, date=DATE))
    led("L-15", "L-10: GF-RECEPTION-DOUBLE-HEIGHT superseded because the void is a railing-bounded stair well with no wall on its boundary", "REVISION_SUPERSESSION_LEDGER L-10 (PA02)", "WITHDRAWN",
        "L-10_STATUS = REOPENED_BY_OWNER_SOURCE_REVIEW: RV-S-B carries the same wall on both floors (candidate); DOUBLE_HEIGHT_WALL_STATUS NOT_FULLY_ESTABLISHED", "RECEPTION_VERTICAL_FACE_REGISTER.json")
    led("L-16", "FF void = 5.82 x 2.75", "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json VOID", "SUPERSEDED_IN_PART",
        "SLAB_OPENING 5.82 x 2.75 (kept) inside VOID_STAIR_ZONE 5.87 x 4.00 (printed / authored); 5.87 x 4.00 is not replaced by 5.82 x 2.75", "VOID_GEOMETRY_RECONCILIATION.json")
    led("L-17", "LOOP-059 girth 1.80 lm, all four faces exposed", "COLUMN_FACE_REGISTER.json; PLASTER_QUANTITY_TRACE D2 lines (v4)", "SUPERSEDED",
        f"internal plasterable girth {g['VALUE']} lm (0.85 on the structural depth); external face 0.60 separate", "COLUMN_VERTICAL_EXPOSURE_REGISTER.json (walls CAD-822 / 823 / 783)")
    led("L-18", "D2 column bonding area 5.76 m2 (1.80 x 3.20)", "PLASTER_QUANTITY_TRACE D2:COLUMN:LOOP-059", "SUPERSEDED",
        "physical area NOT_ESTABLISHED (exposed height unknown); OWNER_PARAMETRIC 2.40 labelled", "COLUMN_VERTICAL_EXPOSURE_REGISTER.json")
    led("L-19", "NE-PARAPET-EXTERNAL-FINISH: 'no elevation of the neighbour side exists in the set'", "OWNER_DECISION_QUEUE.json v2", "CORRECTED_BY_OWNER_EVIDENCE",
        "page 7 is the NORTH EAST ELEVATION; item rewritten: finish unknown, band existence NOT_ESTABLISHED, top PROVISIONAL", "NE_ELEVATION_FINISH_ELIGIBILITY_REGISTER.json")
    led("L-20", "block stair wall subtotals 93.08 / 75.18 / 75.18 m2 PROVISIONAL_QUANTITY", "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json; A22-5-STAIR-WELL", "SUPERSEDED_IN_PART",
        "demoted to GEOMETRIC_REFERENCE_ONLY; faces kept with exposure / openings / landing / occlusion fields", "STAIR_COMPONENT_REGISTER_V2.json")
    led("L-21", "GF_PLAN_D2_COLUMN.png: column drawn free-standing (no abutting walls)", "VISUAL_QA.json (PA01)", "APPARATUS_DEFECT",
        "the overlay omitted CAD-822 / CAD-823 / CAD-783 that end on the column; PA01's 'no wall drawn around it' looked only inside the loop box", "QA_RENDER_VALIDITY_REGISTER.json")
    led("L-22", "PA02 stair register: A-A left / right walls 'continuous' faces per storey without occlusion fields", "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json STAIR_WELL_FACE_REGISTER", "SUPERSEDED",
        "STAIR_COMPONENT_REGISTER_V2 faces", "STAIR_COMPONENT_REGISTER_V2.json")
    # ---- owner queue v3 ---------------------------------------------------------------------------
    keep = {q["DECISION_ID"]: q for q in old_q["QUEUE"]}
    Q = []
    for did in ("D1-ROOF-BUILDUP-INFO", "D3-BENCHMARK-IDENTITY", "EXTERNAL-FINISH-SYSTEM", "SW-PARAPET-HEIGHT-CONFIRM"):
        q = dict(keep[did]); q["ASKED_IN"] = "PA01 / PA02 (unchanged wording; not re-asked, still open)"; Q.append(q)
    Q.append(ODQ.item(DECISION_ID="NE-PARAPET-EXTERNAL-FINISH", LOCATION="roof +9.70, NE (neighbour) parapet outer face 18.27 m; NORTH EAST ELEVATION = page 7", TRADE="PARAPET_PLASTER (external) / COPING",
                      QUESTION="Is the neighbour-facing outer face of the NE parapet plastered, and is there a coping / capping band at its top (page 7 draws a single top line)?",
                      WHY_SOURCE_HIERARCHY_FAILED="the NE elevation EXISTS (page 7) but carries no hatch, level or finish note on the parapet face; A-A hatches 1.62 (1.40 + 0.20?) while page 7 shows one top line; finishes specification SOURCE_NOT_PROVIDED",
                      AVAILABLE_EVIDENCE=["NE_ELEVATION_FINISH_ELIGIBILITY_REGISTER (SOLID_FACE_TOP PROVISIONAL, BAND_EXISTS NOT_ESTABLISHED, BAND_HEIGHT DERIVED 0.20, BAND_TRADE_ROLE UNKNOWN)",
                                          "geometric face 18.27 x 1.40 = 25.578 m2 GEOMETRIC_REFERENCE_ONLY", "visual_qa/source_crops/ne_top_zoomL.png / ne_top_zoomR.png (single top line)"],
                      OPTION_A="plastered like the roof side, with a 0.20 coping band (A-A reading)", OPTION_B="plastered, no band (page 7 reading)", OPTION_C_IF_REQUIRED="not finished (boundary condition) / other trade",
                      QUANTITY_IMPACT_IF_KNOWN={"m2_if_eligible_1_40": round(18.27 * 1.40, 3), "band_m2_if_exists": round(18.27 * 0.20, 3)}, BLOCKS_WHAT="one parapet line and one band line", CAN_OTHER_WORK_CONTINUE=True,
                      VISUAL_CARD="visual_qa/NE_PARAPET_TOP.png (overlay lines are DERIVED); visual_qa/source_crops/ne_top_full.png", PRIORITY="QUANTITY_AFFECTING_SMALL",
                      TECHNICAL_RECOMMENDATION="A for the face (a 1.40 parapet face above a neighbour wall is normally finished); band: no recommendation (sources disagree)"))
    Q.append(ODQ.item(DECISION_ID="RECEPTION-SECTION-SOURCE", LOCATION="GF reception opening (587 x 400) and its vertical faces", TRADE="DOUBLE_HEIGHT_PLASTER / NORMAL_INTERNAL_PLASTER",
                      QUESTION="Does a section, detail or stair drawing through the reception opening exist outside the delivered set (A-A and B-B do not cut it)? Is the GF opening to the garden strip (3.82 m) glazed, doored or open?",
                      WHY_SOURCE_HIERARCHY_FAILED="plan copies identify the faces (RV-S-B same wall both floors with the flight against it; FF walls over open GF edges on RV-W / RV-S-A) but no section proves any height; no D / W layer line closes the GF garden opening",
                      AVAILABLE_EVIDENCE=["RECEPTION_VERTICAL_FACE_REGISTER (four edges, four faces, all NOT_ESTABLISHED)", "VOID_GEOMETRY_RECONCILIATION", "structural p4 X and beams"],
                      OPTION_A="a section / stair detail exists: supply it (then RVF-S-B and the two overhanging faces can be measured)", OPTION_B="none exists: faces stay PROVISIONAL from the plan model with stated bottoms / tops",
                      OPTION_C_IF_REQUIRED=None, QUANTITY_IMPACT_IF_KNOWN={"RVF-S-B_m2_if_continuous_1_00_to_9_54": round(2.05 * 8.54, 3), "RVF-W-FF_m2_range": "3.95 x (4.04 + beam depth)", "RVF-S-A-FF_m2_range": "3.82 x (4.04 + lintel)"},
                      BLOCKS_WHAT="the reception's DOUBLE_HEIGHT_WALL category (three faces)", CAN_OTHER_WORK_CONTINUE=True, VISUAL_CARD="visual_qa/FF_VOID_TWO_OBJECTS.png", PRIORITY="INFORMATION",
                      TECHNICAL_RECOMMENDATION="B if nothing exists: carry RVF-S-B as PROVISIONAL 2.05 x 8.54 with the flight occlusion listed, never as a normal-height face"))
    gate = ODQ.stop_gate(Q)
    withdrawn = ["NE-PARAPET-EXTERNAL-FINISH v2 wording ('no elevation of the neighbour side exists') - rewritten (L-19)"]
    technical = [{"ID": "T-RECEPTION-PERIMETER", "WHAT": "trace the GF reception perimeter faces on the GF copy (open edges to DINING / SALOON, the garden opening, the FF walls above)", "SOURCE_TO_CHECK": "DWG GF + FF copies"},
                 {"ID": "T-BEAM-DEPTHS", "WHAT": "beam depths over the column and under the FF walls on the opening edges (beam schedule)", "SOURCE_TO_CHECK": "ST7757.pdf p7-p16 (schedules) - not yet read"},
                 {"ID": "T-STAIR-RISE", "WHAT": "riser count and rise of the main stair (soffits, RVF-S-B occlusion band)", "SOURCE_TO_CHECK": "DWG FF copy tread lines + A-A / stair detail (none in set)"},
                 {"ID": "T-BLOCK-ELEMENT", "WHAT": "10 cm element height / role from any stair detail; A-A at native resolution around the flights", "SOURCE_TO_CHECK": "page 8 native"},
                 {"ID": "T-SE-TW-D1-AN-D1", "WHAT": "witness terminations for the tower base door and annex door widths", "SOURCE_TO_CHECK": "page 4 native"},
                 {"ID": "T-FF-WALLS", "WHAT": "first-floor room faces (E1.4-style chains on the FF copy)", "SOURCE_TO_CHECK": "DWG FF copy"},
                 {"ID": "T-ANNEX-PARAPET-RUN", "WHAT": "annex +4.30 parapet run", "SOURCE_TO_CHECK": "DWG FF copy outline"},
                 {"ID": "T-NE-NW-OPENINGS", "WHAT": "NE / NW facade openings", "SOURCE_TO_CHECK": "pages 6 / 7 + DWG NW elevation blob"},
                 {"ID": "T-WET-HEIGHT", "WHAT": "wet-room treatment height", "SOURCE_TO_CHECK": "SOURCE_NOT_PROVIDED"},
                 {"ID": "T-KERB-CURVE", "WHAT": "ink-trace the SE kerb ogee at native resolution", "SOURCE_TO_CHECK": "page 4 native"}]
    # ---- leakage scan of the new registers ---------------------------------------------------------
    leaks = {}
    for a in NEW_REGISTERS + ["PA03_DEPENDENT_QUANTITIES.json"]:
        obj = json.loads((OUT / a).read_text("utf-8"))
        hits = []
        _num_scan(obj, hits)
        leaks[a] = {"BENCHMARK_KEY_OR_PHRASE_HITS": BP.scan(obj), "BENCHMARK_FIGURE_HITS": hits}
    clean = all(not v["BENCHMARK_FIGURE_HITS"] for v in leaks.values())
    frozen_ok = {}
    for fz in ("FREEZE_ESTIMATE", "FREEZE_A22", "FREEZE_FINAL", "FREEZE_DUAL", "FREEZE_OWNER_EVIDENCE", "FREEZE_SE_AUDIT"):
        rec = json.loads((OUT / f"{fz}.json").read_text("utf-8"))
        cur = {a: (hashlib.sha256((OUT / a).read_bytes()).hexdigest() if (OUT / a).exists() else None) for a in rec["ARTIFACT_SHA256"]}
        frozen_ok[fz] = SL.assert_frozen_unchanged(rec, cur)
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "PA03_GATE", "LAYER": "PA03_SOURCE_REVIEW_CORRECTION",
           "ORDER_FOLLOWED": ["A void reconciliation", "B reception vertical faces", "C double-height status", "D 10 cm stair element", "E stair face sets", "F D2 column exposed height", "freeze", "dependent quantities"],
           "A22_INCREMENTAL_V6": {"ITEMS": [i["ITEM_ID"] for i in items]}, "OWNER_DECISION_QUEUE_V3": Q, "STOP_GATE": gate, "WITHDRAWN_FROM_QUEUE": withdrawn,
           "TECHNICAL_FOLLOW_UPS_NOT_OWNER": technical, "LEAKAGE_SCAN_NEW_REGISTERS": {"CLEAN": clean, "SCANNED": leaks}, "FROZEN_OK": {k: v["OK"] for k, v in frozen_ok.items()},
           "BENCHMARK_RECONCILIATION": "CONDITIONAL_IF_P7757", "BENCHMARK_IDENTITY": "OWNER_CONFIRMATION_REQUIRED",
           "PRODUCTION_BOUNDARY": ["no BOQ", "no project total", "no pricing", "no procurement", "no Firebase / Manager Agent write", "no payment certification", "no Urban-wide rule promotion"]}
    (OUT / "PA03_GATE.json").write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    (OUT / "OWNER_DECISION_QUEUE.json").write_text(json.dumps({"PHASE_ID": P.PHASE_ID, "ARTIFACT": "OWNER_DECISION_QUEUE", "VERSION": "v3 (PA03)", "QUEUE": Q, "STOP_GATE": gate,
                                                                "WITHDRAWN": withdrawn, "TECHNICAL_FOLLOW_UPS_NOT_OWNER": technical, "D3_NOT_RE_ASKED": True}, indent=2, default=str) + "\n", encoding="utf-8")
    (OUT / "REVISION_SUPERSESSION_LEDGER.json").write_text(json.dumps(dict(old_led, ENTRIES=L, FROZEN_ARTIFACTS_UNCHANGED=frozen_ok), indent=2, default=str) + "\n", encoding="utf-8")
    return {"LINES": [(l["LINE_ID"], l["UNIT"], l["VALUE"], l["QUANTITY_STATE"]) for l in lines], "A22": [i["ITEM_ID"] for i in items], "QUEUE": [(x["DECISION_ID"], x["PRIORITY"]) for x in Q],
            "GATE": gate, "LEDGER": len(L), "LEAKAGE_CLEAN": clean, "FROZEN_OK": {k: v["OK"] for k, v in frozen_ok.items()}, "CEILING": ceiling["GF_RECEPTION_CEILING"]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
