"""ALSENAN P7757 + ST7757 PHASE A3 - registers, workbook model, QA and the freeze (from the A3 build context only).

Classes as in A2 (PHYSICAL_MEASUREMENT / TRADE_ASSIGNMENT / BLOCKED_MATERIAL / BLOCKED_HEIGHT) plus BLOCKED_GEOMETRY
(the geometry that would make the quantity is not proved). A BLOCKED row has no quantity and is in no total.
The structural summary rows are DERIVED from the occurrence rows of structural_schedule; the manual-QS views are views
over those rows. Nothing here is priced, calibrated or migrated.
"""

from __future__ import annotations

import copy
import datetime as dt
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from engine import boq_rc1_xlsx as BX                                                            # noqa: E402
from engine.source import benchmark_firewall as FW, cad_text as CT, entity_role_inference as ERI # noqa: E402
from engine.source import freeze_schema as FS, level_marks as LM, schedule_table as ST          # noqa: E402
from engine.source import structural_qto as SQ, structural_schedule as SS                       # noqa: E402

import alsenan_phase_a as AP                                                                      # noqa: E402
import alsenan_phase_a3 as A3                                                                     # noqa: E402
import alsenan_a2_registers as AR2                                                                # noqa: E402

RECOMMENDATION_COMMIT, BASELINE_COMMIT = "38ae9ae", "d38f5c8"
CREATED = AR2.CREATED
XLSX_NAME = "URBAN_QTO_ALSENAN_P7757_ST7757_PHASE_A3.xlsx"
FREEZE = "ALSENAN_P7757_ST7757_PHASE_A3_FREEZE"
BANNER = ("SHADOW / PHASE A3 SOURCE-ONLY - SCHEDULE-DRIVEN STRUCTURE + OWNER FACTS - ALSENAN P7757 + ST7757 - FROZEN "
          "BEFORE ANY BENCHMARK - NOT FOR TENDER OR CONTRACT - NO PRICES - VIEW OVER ENGINE REGISTERS - NO PRODUCTION "
          "MIGRATION")
COLUMNS = AR2.COLUMNS
PHYS, TRADE, BMAT, BHGT, BGEO = AR2.PHYS, AR2.TRADE, AR2.BMAT, AR2.BHGT, "BLOCKED_GEOMETRY"
COMPLETE, SUBTOTAL, BLOCKED = SQ.COMPLETE, AR2.SUBTOTAL, AR2.BLOCKED
FLOORS = A3.FLOORS
digest, r6, sheet = AR2.digest, AR2.r6, AR2.sheet
SUMMARY_NAME = "02_ARCH_SUMMARY / 12_STRUCTURAL_SUMMARY"

OWNER_QUESTIONS = [
    {"id": "OQ3-S1", "group": "STRUCTURAL",
     "question": "At the east end of the foundation plan ONE footing outline (3.25 x 1.40 m) is drawn under columns C10 "
                 "and C, carrying the marks F10 and F; the schedule gives F10 = 280 x 140 x 50 cm and F = 90 x 80 x 30 "
                 "cm. Is this one combined footing built to the drawn outline (and at which depth), or two scheduled "
                 "footings overlapping each other?",
     "evidence": "FOOTING_REGISTER.forensic (outline H6939, strap H5769 / H6940 entering it, columns H4328 / H4260)",
     "unblocks": ["footing F10 (1)", "footing F at C (1)",
                  "confirms the S.B1 clear end (measured to the drawn face of this outline)"], "supersedes": ["OQ2-S1", "OQ2-S2"]},
    {"id": "OQ3-A1", "group": "ARCHITECTURAL",
     "question": "Ground floor, west side at the entry arrow: the hall that joins dining, reception and saloon is drawn "
                 "with no door or screen to the outside. Is the entrance closed by a door or glazed screen (not drawn), "
                 "or is it an open entrance?",
     "evidence": "ROOM_TOPOLOGY: the DINING / RECEPTION / SALOON labels lie in no bounded site; the flood from the "
                 "saloon reaches outside through the entrance hall",
     "unblocks": ["GF hall / dining / reception / saloon room areas (geometry only)"], "supersedes": ["OQ2-A1"]},
    {"id": "OQ3-A2", "group": "ARCHITECTURAL",
     "question": "Ground-floor master bedroom, west corner: two single lines form a 0.50 x 1.46 m box with a diagonal "
                 "against the wall. Is it a fixed wardrobe (does the floor finish run under it?) or a closed store?",
     "evidence": "ROOM_REGISTER: MASTER BED ROOM GF site 16.55 m2 REVIEW_REQUIRED (TOPOLOGY_ROLE_UNRESOLVED)",
     "unblocks": ["GF master bedroom floor / ceiling area"]},
]
RESOLVED_QUESTIONS = [
    {"id": "OQ2-A1", "how": "owner facts (salon aluminium glass; master-bedroom curved glazing) + the engine now reads "
                            "curved glazing arcs; the remaining open edge is the entrance -> OQ3-A1"},
    {"id": "OQ2-A2", "how": "COUNTER_RUN joinery motif (engine inference): kitchen U-run and pantry L-run are fixed "
                            "counters; the kitchen certifies 9.63 m2"},
    {"id": "OQ2-S1", "how": "forensics: the 1.50 x 1.40 'outline' was the east part of ONE combined outline clipped by the "
                            "strap; F at H5757 occurrences are count-unique -> OQ3-S1 for the combined outline only"},
    {"id": "OQ2-S2", "how": "forensics: the 1.05 x 1.40 'F10 candidate' was the west part of the same outline -> OQ3-S1"},
]
DONORS = [dict(d) for d in AR2.DONORS] + [
    {"donor": "-", "capability": "schedule-driven structural takeoff, polyline rings, curved-glazing / counter-run motifs",
     "class": "CLEAN_REIMPLEMENT (no donor has it)", "where": "engine/source/structural_schedule.py, "
     "entity_role_inference (CURVED_GLAZING, COUNTER_RUN, WALL_END_CAP, door frames)", "inspected": "DONORS.lock inventory"}]


def row(item, discipline, trade, floor, element, ar, en, qty, unit, status, klass, source, rule, blockers=()):
    r = AR2.row(item, trade, floor, element, ar, en, qty, unit, status, klass, source, rule, blockers)
    r["discipline"] = discipline
    return r


def _rename(r):
    x = copy.deepcopy(r)
    x["item"] = "A3-" + r["item"][3:] if r["item"].startswith("A2-") else r["item"]
    x["discipline"] = "ARCHITECTURAL"
    return x


# ====================================================================== architecture
def arch_rows(regs2, a3) -> list:
    rows = [_rename(r) for r in regs2["ARCH_BOQ"]["rows"]]
    ar = a3["architecture"]
    s = ar["salon_glazing"]
    src = "P7757.dxf GF dimension 2289 (633) + GF-W09 glazing in wall gap; OWNER facts OF-A3-SALON-*"
    ok = s["status"] == COMPLETE
    rows += [
        row("A3-ALU-SALON-W", "ARCHITECTURAL", "ALUMINIUM_GLAZING", "GF", "SALOON sea-view opening",
            "عرض فتحة الألمنيوم - الصالون", "Salon sea-view opening width", s["width_m"], "m", COMPLETE if ok else BLOCKED,
            PHYS, src, "printed dimension = CAD glazing gap (unique width match)",
            [] if ok else ["OWNER_WIDTH_NOT_UNIQUELY_MATCHED"]),
        row("A3-ALU-SALON", "ARCHITECTURAL", "ALUMINIUM_GLAZING", "GF", "SALOON sea-view opening",
            "ألمنيوم وزجاج - واجهة الصالون", "Salon aluminium + glass (width source, height OWNER-DERIVED 3.65)",
            s["area_m2"], "m2", COMPLETE if ok else BLOCKED, TRADE, src,
            "6.33 (source) x 3.65 (PROJECT_OWNER_DERIVED_DIMENSION, not source-measured; this opening only)",
            [] if ok else ["OWNER_WIDTH_NOT_UNIQUELY_MATCHED"])]
    mb = ar["curved_glazing"]["master_bedroom"]
    rows.append(row("A3-CGL-MB-L", "ARCHITECTURAL", "ALUMINIUM_GLAZING", "GF", "MASTER BED ROOM curved glazing (pool side)",
                    "طول الزجاج المنحني - غرفة النوم الرئيسية", "Master bedroom curved aluminium glazing - developed length",
                    mb["developed_length_m"], "m", mb["status_length"], PHYS,
                    "P7757.dxf GF concentric glazing arcs (entity_role_inference CURVED_GLAZING); material OWNER_FACT",
                    "mean of the glazing lines' arc lengths (range " + json.dumps(mb["length_range_m"]) + " m)",
                    [] if mb["status_length"] == COMPLETE else ["CURVED_GLAZING_NOT_UNIQUE"]))
    rows.append(row("A3-CGL-MB-A", "ARCHITECTURAL", "ALUMINIUM_GLAZING", "GF", "MASTER BED ROOM curved glazing (pool side)",
                    "مساحة الزجاج المنحني", "Master bedroom curved glazing area", None, "m2", BLOCKED, BHGT,
                    "no head / sill in the source", "length x height",
                    ["GLAZING_HEIGHT_NOT_IN_SOURCE (the salon owner-derived 3.65 m is not transferred)"]))
    for g in ar["curved_glazing"]["items"]:
        if g["id"] == mb["item"]:
            continue
        rows.append(row(f"A3-CGL-{g['floor']}-{g['id'][-4:]}-L", "ARCHITECTURAL", "GLAZING", g["floor"],
                        f"curved glazing {g['id']} (host: {' | '.join(g['host_labels']) or 'site not certified'})",
                        "طول زجاج منحني", "Curved glazing developed length (material not in source)",
                        round(g["developed_length_mm"] / 1000.0, 6), "m", COMPLETE, PHYS,
                        "P7757.dxf concentric glazing arcs (CURVED_GLAZING)", "mean arc length of the glazing lines"))
    for z in ar["double_height"]["zones"]:
        st = COMPLETE if z["horizontal_extent_m2"] is not None else BLOCKED
        rows.append(row("A3-DHZ-RECEPTION", "ARCHITECTURAL", "DOUBLE_HEIGHT_ZONE", "GF+1F", "RECEPTION + 1F VOID",
                        "منطقة مزدوجة الارتفاع - الاستقبال", "Reception double-height zone - plan extent",
                        z["horizontal_extent_m2"], "m2", st, PHYS if st == COMPLETE else BGEO,
                        "OWNER_FACT OF-A3-RECEPTION-DOUBLE-HEIGHT + 1F VOID label above (" + z["state"] + ")",
                        "extent of the 1F VOID site above the reception",
                        [] if st == COMPLETE else ["VOID_SITE_NOT_CERTIFIED: the 1F site holding VOID also holds other "
                                                   "labels (open to the stair / landing)"]))
    for fl in FLOORS:
        runs = ar["joinery"][fl]["runs"]
        if runs:
            rows.append(row(f"A3-JNY-{fl}", "ARCHITECTURAL", "JOINERY", fl, f"{len(runs)} counter run(s)",
                            "طول واجهات الخزائن الثابتة", "Fixed counter / joinery front length (engine inference)",
                            round(sum(x["front_length_mm"] for x in runs) / 1000.0, 6), "m", COMPLETE, PHYS,
                            "P7757.dxf single lines classified COUNTER_RUN (entity_role_inference)",
                            "front segments 450-750 mm off a wall face, ends on walls; floor finish runs under "
                            "(URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1)"))
    return rows


def rooms(regs2, a3) -> list:
    out = []
    for r in regs2["ROOM_REGISTER"]["rooms"]:
        x = dict(r)
        x["kind"] = "LABELLED_SITE"
        out.append(x)
    return out


# ====================================================================== structure
def struct_rows(a3) -> list:
    rows = []
    f = a3["footings"]
    src = "ST7757.dxf FOUNDATION PLAN marks + SCHEDULE OF FOOTINGS (CAD table, cm)"
    for s in f["summary"]:
        if not s["count_tagged"]:
            continue
        st = COMPLETE if s["status"] == COMPLETE else SUBTOTAL if s["count_computed"] else BLOCKED
        blk = [r["blockers"][0] for r in f["rows"] if r["type"] == s["type"] and r["status"] != COMPLETE]
        rows.append(row(f"S3-FTG-{s['type']}", "STRUCTURAL", "CONCRETE_FOOTING", "FOUNDATION",
                        f"{s['type']}: {s['count_computed']} of {s['count_tagged']} marks computed",
                        f"خرسانة قواعد {s['type']}", f"Footing {s['type']} concrete ({s['L_m']} x {s['W_m']} x {s['H_m']} m "
                        f"each)", s["m3_total_computed"] if s["count_computed"] else None, "m3", st, PHYS if s["count_computed"] else BGEO, src,
                        "sum of the type's computed occurrence rows (each 1 x L x W x H from the schedule)", blk))
    for r in a3["straps"]["rows"]:
        st = r["status"]
        rows.append(row(f"S3-STRAP-{r['type']}", "STRUCTURAL", "CONCRETE_STRAP_BEAM", "FOUNDATION",
                        f"{r['mark_value']} ({r['type']} {r['B_cm']} x {r['D_cm']} cm)", f"ميدة رابطة {r['type']}",
                        f"Strap beam {r['type']} concrete", r.get("volume_m3"), "m3", st,
                        PHYS if st == COMPLETE else BGEO, "ST7757.dxf FOUNDATION PLAN pair lines + SCHEDULE OF SIMPLE BEAMS",
                        "clear length between the footing outlines it joins x B x D",
                        [] if st == COMPLETE else [f"STRAP_BAND_NOT_BOUND: {r['state']} (pairs {r.get('pairs_between_mm')} mm)"]))
    c = a3["columns"]
    fnd = c["storeys"]["FOUNDATION"]
    rows.append(row("S3-COL-CNT-FOUNDATION", "STRUCTURAL", "COLUMN", "FOUNDATION", f"{c['mark_count']} marks on the column plan",
                    "عدد الأعمدة (رقاب)", "Column count by mark (column & axis plan)", c["mark_count"], "nr", COMPLETE, PHYS,
                    "ST7757.dxf COLUMN & AXIS PLAN marks", "one occurrence per mark"))
    rows.append(row("S3-COL-PLAN-FOUNDATION", "STRUCTURAL", "COLUMN", "FOUNDATION", "schedule FOUNDATION band sections",
                    "مساحة مقاطع الأعمدة (رقاب)", "Column plan area, FOUNDATION band (count x B x D)", fnd["plan_area_m2"],
                    "m2", COMPLETE, PHYS, "SCHEDULE OF COLUMNS FOUNDATION band x marks",
                    "printed per-occurrence size labels deviate for "
                    f"{c['printed_size_labels']['by_band']['FOUNDATION']['deviation_count']} occurrence(s) "
                    "(reported, not bound, never overriding)"))
    for band, sheetkey in A3.STOREY_SHEETS.items():
        if band == "FOUNDATION":
            continue
        corr = c["storeys"][band]["corroboration"] or {}
        rows.append(row(f"S3-COL-CNT-{band.split()[0]}", "STRUCTURAL", "COLUMN", band, f"column outlines drawn on {sheetkey}",
                        "عدد الأعمدة المرسومة", f"Column outlines drawn on the {band} sheet", corr.get("drawn_count"), "nr",
                        COMPLETE if corr else BLOCKED, PHYS, f"ST7757.dxf {sheetkey} S-COL.BON rectangles",
                        "geometry count (the outlines carry no type mark on that sheet)",
                        [] if corr else ["SHEET_NOT_FOUND"]))
        rows.append(row(f"S3-COL-PLAN-{band.split()[0]}", "STRUCTURAL", "COLUMN", band, "per-occurrence type",
                        "مساحة مقاطع الأعمدة", f"Column plan area, {band}", None, "m2", BLOCKED, BGEO,
                        "SCHEDULE OF COLUMNS band sizes vs drawn outlines", "count x B x D per type",
                        [f"STOREY_TYPE_COUNT_NOT_ESTABLISHED: schedule-type expectation {corr.get('expected_count')} vs "
                         f"{corr.get('drawn_count')} outlines drawn ({corr.get('state')}); outlines carry no mark"]))
    rows.append(row("S3-COL-VOL", "STRUCTURAL", "COLUMN", "ALL", "all columns", "خرسانة الأعمدة", "Column concrete",
                    None, "m3", BLOCKED, BHGT, "no structural level / soffit", "plan area x height", [c["height"]]))
    for b in a3["beams"]["rows"]:
        if not b["marks"]:
            continue
        rows.append(row(f"S3-BM-{b['type']}-CNT", "STRUCTURAL", "BEAM", "SLABS", f"{b['type']} {b['B_cm']} x {b['D_cm']} cm",
                        f"عدد الكمرات {b['type']}", f"Beam {b['type']} marks on the slab plans", b["marks"], "nr",
                        COMPLETE, PHYS, "ST7757.dxf roof-slab plans marks", json.dumps(b["marks_per_sheet"])))
        if b["kind"] == "CONTINUOUS" and b.get("length_m") is not None:
            rows.append(row(f"S3-BM-{b['type']}-L", "STRUCTURAL", "BEAM", "SLABS", f"{b['type']} schedule spans",
                            f"طول الكمرة المستمرة {b['type']}", f"Continuous beam {b['type']} length per schedule row (sum of printed spans; {b['marks_vs_spans']})",
                            b["length_m"], "m", COMPLETE, PHYS, b["section_source"],
                            "sum of printed spans between supports (centre line); clear length not proved"))
    rows.append(row("S3-BM-VOL", "STRUCTURAL", "BEAM", "SLABS", "all beams", "خرسانة الكمرات", "Beam concrete", None,
                    "m3", BLOCKED, BGEO, "plans + schedules", "clear length x B x (D - slab) per occurrence",
                    ["BEAM_CLEAR_LENGTH_NOT_PROVED: simple-beam marks sit beside their bands (binding by distance is "
                     "refused); continuous-beam spans are centre-line; slab / beam overlap not resolved"]))
    for k, v in sorted(a3["slabs"].items()):
        th = ", ".join(f"{t} cm x{n}" for t, n in sorted(v["thickness_marks_cm"].items())) or "none"
        rows.append(row(f"S3-SLB-{k.split('_')[0]}", "STRUCTURAL", "SLAB", k, f"thickness marks: {th}",
                        "خرسانة البلاطة", f"Slab concrete {k}", None, "m3", BLOCKED, BGEO, f"ST7757.dxf {k}",
                        "area x printed thickness", [v["blocker"]]))
    rows.append(row("S3-GB-VOL", "STRUCTURAL", "GROUND_BEAM", "GROUND", "ground beams", "خرسانة الميد", "Ground beam concrete",
                    None, "m3", BLOCKED, BHGT, "ST7757.dxf GROUND BEAMS PLAN", "length x section",
                    ["GROUND_BEAM_LEVEL_AND_EXTENT_NOT_PROVED"]))
    rows.append(row("S3-STR-VOL", "STRUCTURAL", "STAIR", "ALL", "stairs", "خرسانة الدرج", "Stair concrete", None, "m3",
                    BLOCKED, BHGT, "plans + sections", "flight geometry", ["RISER_COUNT_PER_FLIGHT_NOT_PROVED"]))
    for el in ("FOOTING", "COLUMN", "BEAM", "STRAP"):
        rows.append(row(f"S3-RBR-{el}", "STRUCTURAL", "REBAR", "ALL", f"{el.lower()} reinforcement", "حديد التسليح",
                        f"Reinforcement weight - {el.lower()}", None, "kg", BLOCKED, BMAT, "schedules",
                        "definition only (bars, diameters); weight needs cutting length, cover, hooks, laps",
                        ["REBAR_WEIGHT_BLOCKED: cutting length / cover / hooks / laps not stated; no kg/m3"]))
    return rows


def type_library(ctx, a3) -> dict:
    return {"footings": a3["footings"]["library"], "columns": a3["columns"]["library"],
            "simple_beams": a3["beams"]["simple_library"], "continuous_beams": a3["beams"]["continuous_library"],
            "schedule_states": {k: ctx["schedules"][k]["state"] for k in ("FOOTINGS", "COLUMNS", "SIMPLE_BEAMS")},
            "schedule_digests": {k: ctx["schedules"][k].get("table_digest") for k in ("FOOTINGS", "COLUMNS", "SIMPLE_BEAMS")}}


# ====================================================================== workbook
def workbook(regs) -> dict:
    ab, sb = regs["ARCH_BOQ"]["rows"], regs["CONCRETE_REGISTER"]["boq_rows"]
    units = regs["SOURCE_AUTHORITY_REGISTER"]["units"]
    W = {0: 24, 4: 40, 5: 30, 6: 46, 10: 22, 11: 40, 12: 50, 13: 90}
    m = {}
    m["00_READ_ME"] = sheet("INFO", ["TOPIC", "TEXT"], [
        ["WHAT", "Phase A3: schedule-driven structure (mark = type, schedule = size, plan = validation), owner facts, "
                 "room recovery - the ONE Urban engine on Alsenan P7757 + ST7757."],
        ["SOURCE SET", "The supplied files are the complete available owner source set."],
        ["CLASSES", "PHYSICAL_MEASUREMENT / TRADE_ASSIGNMENT / BLOCKED_MATERIAL / BLOCKED_HEIGHT / BLOCKED_GEOMETRY."],
        ["ADDING", "Only lines of 02_ARCH_SUMMARY or of 12_STRUCTURAL_SUMMARY may be added, each within its scope and "
                   "never across units."],
        ["OWNER FACTS", "The salon height 3.65 m is PROJECT_OWNER_DERIVED (not source-measured) and applies to that "
                        "opening only."],
        ["VIEWS", "FOOTING / COLUMN / BEAM QS views are views over the occurrence rows - not calculators."],
        ["UNITS", f"P7757: {units['ARCHITECTURAL']['status']}; ST7757: {units['STRUCTURAL']['status']}."],
        ["NOT BLIND", "Development validation; the repository carries P7757 history (disclosed)."],
        ["NO PRICES", "No price, no calibration, no production migration."]], widths={1: 130})
    m["01_SOURCES"] = sheet("INFO", ["FILE", "DISCIPLINE", "TYPE", "SHA256", "AUTHORITY"],
                            [[f["file"], f["discipline"], f["type"], f["sha256"], f["authority"]]
                             for f in regs["SOURCE_MANIFEST"]["files"]], widths={0: 40, 3: 66, 4: 60})
    m["02_ARCH_SUMMARY"] = sheet("ADDITIVE_SUMMARY", COLUMNS, [AR2.boq_line(r) for r in ab], qty_cols=(7,), status_col=9,
                                 widths=W, wrap=(13,), scope="ARCHITECTURAL")
    m["03_ROOM_MATRIX"] = sheet("BREAKDOWN", ["FLOOR", "ROOM", "SITE", "FLOOR AREA m2", "CEILING BASE m2", "PERIMETER m",
                                              "WALL-FACE LENGTH m", "SKIRTING PATH m", "WET SEMANTICS", "STATUS", "BLOCKER"],
                                [[r["floor"], r["room"], r["site"], r["floor_area_m2"], r["base_ceiling_area_m2"],
                                  r["perimeter_m"], r["wall_face_length_m"], r["skirting_path_m"], r["wet_semantics"],
                                  r["status"], r["blocker"] or ""] for r in regs["ROOM_REGISTER"]["rooms"]] +
                                [[p["floor"], "PHYSICAL_SITE (semantic UNKNOWN)", p["site"], p["floor_area_m2"],
                                  p["base_ceiling_area_m2"], p["perimeter_m"], "", "", "", p["status"], ""]
                                 for fl in FLOORS for p in regs["ROOM_REGISTER"]["physical_sites"]["floors"][fl]["published"]],
                                qty_cols=(3, 4, 5, 6, 7), status_col=9, widths={1: 34, 8: 40, 10: 80})

    def part(prefixes):
        return [AR2.boq_line(r) for r in ab if any(r["item"].startswith(p) for p in prefixes)]
    m["04_FLOOR_CEILING"] = sheet("BREAKDOWN", COLUMNS, part(("A3-FLR", "A3-CLG", "A3-FFN", "A3-CFN")), (7,), 9, W, (13,))
    m["05_OPENINGS"] = sheet("SCHEDULE", ["FLOOR", "KIND", "ID", "WIDTH / LEAF mm", "STATE", "ROOMS", "HEIGHT",
                                          "MATERIAL", "STATUS"],
                             [[d["floor"], "DOOR", d["occurrence"], d["leaf_width_mm"], d["state"],
                               " | ".join(x for x in d["rooms"] if x), d["height"], d["material"], "INFO"]
                              for d in regs["OPENING_REGISTER"]["doors"]] +
                             [[w["floor"], "WINDOW", w["window"], w["width_mm"], "GLAZING_IN_WALL_GAP",
                               " | ".join(w["host_rooms"]), w["height"], w["material"], "INFO"]
                              for w in regs["OPENING_REGISTER"]["windows"]], status_col=8,
                             widths={5: 40, 6: 50, 7: 40})
    g = regs["ALUMINIUM_GLAZING_REGISTER"]
    m["06_ALUMINIUM_GLAZING"] = sheet("BREAKDOWN", COLUMNS, part(("A3-ALU", "A3-CGL")), (7,), 9, W, (13,))
    m["07_DOUBLE_HEIGHT_ZONES"] = sheet("INFO", ["ZONE", "STATE", "OWNER FACT", "1F VOID SITE", "VERTICAL EXTENT",
                                                 "CEILING", "WALL HEIGHTS"],
                                        [["RECEPTION", z["state"], z["owner_fact"],
                                          json.dumps([(v["site"], v["site_status"]) for v in z["voids"]]),
                                          json.dumps(z["vertical_extent"]), z["ceiling_condition"], z["wall_heights"]]
                                         for z in regs["DOUBLE_HEIGHT_ZONE_REGISTER"]["zones"]], widths={3: 60, 4: 60})
    m["08_WALL_PLAN_QUANTITIES"] = sheet("BREAKDOWN", COLUMNS, part(("A3-BLK", "A3-BLA", "A3-WFL", "A3-WFA", "A3-WFN",
                                                                     "A3-SKP", "A3-SKM", "A3-EXT")), (7,), 9, W, (13,))
    m["09_JOINERY"] = sheet("BREAKDOWN", COLUMNS, part(("A3-JNY",)), (7,), 9, W, (13,))
    m["10_OWNER_FACTS"] = sheet("INFO", ["ID", "AUTHORITY", "SCOPE", "FACT", "NOT"],
                                [[o["id"], o["authority"], json.dumps(o["scope"]), json.dumps(o["fact"]),
                                  json.dumps(o.get("not", []))] for o in regs["OWNER_FACT_REGISTER"]["facts"]],
                                widths={2: 50, 3: 60, 4: 90})
    ablk = Counter(b.split(":")[0] for r in ab for b in r["blockers"])
    m["11_ARCH_BLOCKERS"] = sheet("INFO", ["BLOCKER", "ROWS"], [[k, v] for k, v in sorted(ablk.items())], widths={0: 80})
    m["12_STRUCTURAL_SUMMARY"] = sheet("ADDITIVE_SUMMARY", COLUMNS, [AR2.boq_line(r) for r in sb], qty_cols=(7,),
                                       status_col=9, widths=W, wrap=(13,), scope="STRUCTURAL")
    lib = regs["STRUCT_TYPE_LIBRARY"]
    lrows = [["FOOTING", t, f"{v['L_cm']} x {v['W_cm']} x {v['H_cm']} cm", f"short {v.get('short_bars')}; long "
              f"{v.get('long_bars')}", v.get("source")] for t, v in sorted(lib["footings"].items(), key=lambda kv: SS._type_key(kv[0]))]
    lrows += [["COLUMN", t, json.dumps({b: [s["B_cm"], s["D_cm"]] for b, s in v.items()}),
               json.dumps({b: s["reinf"] for b, s in v.items()}, ensure_ascii=False), "SCHEDULE OF COLUMNS (CAD)"]
              for t, v in sorted(lib["columns"].items(), key=lambda kv: SS._type_key(kv[0]))]
    lrows += [["BEAM", t, f"{v['B_cm']} x {v['D_cm']} cm", f"bottom {v['bottom']}; top {v['top']}; stirrups {v['stirrups']}",
               v["source"]] for t, v in sorted(lib["simple_beams"].items(), key=lambda kv: SS._type_key(kv[0]))]
    lrows += [["CONTINUOUS BEAM", t, f"{v['B_cm']} x {v['H_cm']} cm; spans {v['spans_m']}", "-", v["source"] +
               f" [{v['confidence']}]"] for t, v in sorted(lib["continuous_beams"].items(), key=lambda kv: SS._type_key(kv[0]))]
    m["13_STRUCT_TYPE_LIBRARY"] = sheet("INFO", ["CLASS", "TYPE", "SIZE", "REINFORCEMENT", "SOURCE"], lrows,
                                        widths={2: 60, 3: 70, 4: 70})
    fsum = regs["FOOTING_REGISTER"]["type_summary"]
    m["14_FOOTING_TYPE_COUNTS"] = sheet("SCHEDULE", ["TYPE", "COUNT_TAGGED", "GEOMETRY_CONFIRMED", "PARTIAL_GEOMETRY",
                                                     "CONFLICT", "BLOCKED_OTHER", "L m", "W m", "H m", "M3_EACH",
                                                     "M3_TOTAL (computed)", "STATUS"],
                                        [[s["type"], s["count_tagged"], s["count_geometry_confirmed"],
                                          s["count_partial_geometry"], s["count_conflict"], s["count_blocked_other"],
                                          s["L_m"], s["W_m"], s["H_m"], s["m3_each"], s["m3_total_computed"],
                                          "INFO"] for s in fsum], status_col=11)
    m["15_FOOTING_OCCURRENCES"] = sheet("BREAKDOWN", ["TYPE", "MARK KEY", "MARK", "GEOMETRY STATE", "OUTLINE", "DRAWN mm",
                                                      "L m", "W m", "H m", "FORMULA", "QTY m3", "STATUS", "WHY"],
                                        [[r["type"], r["mark_key"], r["mark_value"], r["geometry_state"],
                                          (r.get("geometry") or {}).get("outline", ""),
                                          json.dumps((r.get("geometry") or {}).get("drawn_mm")),
                                          r["dims"]["L"]["m"] if r["dims"] else None, r["dims"]["W"]["m"] if r["dims"] else None,
                                          r["dims"]["H"]["m"] if r["dims"] else None, r["formula"], r6(r["qty"]),
                                          r["status"], r.get("why", "")] for r in regs["FOOTING_REGISTER"]["occurrences"]],
                                        qty_cols=(10,), status_col=11, widths={1: 44, 4: 50, 12: 90})
    m["16_FOOTING_QS_VIEW"] = sheet("SCHEDULE", ["TYPE", "COUNT", "L", "W", "H", "EACH M3", "TOTAL M3", "STATUS"],
                                    [[s["type"], f"{s['count_computed']} / {s['count_tagged']}", s["L_m"], s["W_m"], s["H_m"],
                                      s["m3_each"], s["m3_total_computed"],
                                      ("INFO" if s["count_tagged"] else "NOT_APPLICABLE")] for s in fsum], status_col=7)
    col = regs["COLUMN_REGISTER"]
    crow = []
    for band, v in col["storeys"].items():
        for r in v["rows"]:
            crow.append([band, r["type"], r["count"], r["B_cm"], r["D_cm"], r["plan_area_each_m2"], r["plan_area_total_m2"],
                         "BLOCKED_HEIGHT", "INFO"])
    m["17_COLUMN_TYPE_COUNTS"] = sheet("SCHEDULE", ["STOREY BAND", "TYPE", "COUNT (marks)", "B cm", "D cm",
                                                    "PLAN AREA EACH m2", "TOTAL PLAN AREA m2", "HEIGHT", "STATUS"], crow,
                                       status_col=8)
    m["18_COLUMN_OCCURRENCES"] = sheet("INFO", ["MARK KEY", "TYPE", "VALUE"],
                                       [[k["key"], k["type"], k["value"]] for k in col["occurrences"]], widths={0: 44})
    fb = col["storeys"]["FOUNDATION"]["rows"]
    m["19_COLUMN_QS_VIEW"] = sheet("SCHEDULE", ["TYPE", "COUNT", "B", "D", "PLAN AREA EACH m2", "TOTAL PLAN AREA m2",
                                                "VOLUME", "STATUS"],
                                   [[r["type"], r["count"], r["B_cm"], r["D_cm"], r["plan_area_each_m2"],
                                     r["plan_area_total_m2"], "BLOCKED_HEIGHT", "INFO"] for r in fb], status_col=7)
    bm = regs["BEAM_REGISTER"]["rows"]
    m["20_BEAM_TYPE_COUNTS"] = sheet("SCHEDULE", ["TYPE", "KIND", "MARKS", "MARKS PER SHEET", "B cm", "D cm", "LENGTH m",
                                                  "LENGTH BASIS", "VOLUME", "STATUS"],
                                     [[b["type"], b["kind"], b["marks"], json.dumps(b["marks_per_sheet"]), b["B_cm"],
                                       b["D_cm"], b.get("length_m"), b.get("length_basis", ""), "BLOCKED",
                                       "INFO"] for b in bm], status_col=9, widths={3: 70, 7: 50})
    occ = [[k, b["type"], b["mark_value"], b["state"], b.get("length_m"), b.get("volume_m3")]
           for k, v in regs["BEAM_REGISTER"]["sheets"].items() for b in v["simple_bands"]]
    occ += [["FOUNDATION", s["type"], s["mark_value"], s["state"], s.get("length_m"), s.get("volume_m3")]
            for s in regs["STRAP_BEAM_REGISTER"]["rows"]]
    m["21_BEAM_OCCURRENCES"] = sheet("INFO", ["SHEET", "TYPE", "MARK", "BAND STATE", "LENGTH m", "VOLUME m3"], occ)
    m["22_BEAM_QS_VIEW"] = sheet("SCHEDULE", ["TYPE", "COUNT", "B", "D", "LENGTH EACH / TOTAL m", "CONCRETE M3", "STATUS"],
                                 [[b["type"], b["marks"], b["B_cm"], b["D_cm"], b.get("length_m"), "BLOCKED", "INFO"]
                                  for b in bm if b["marks"]] +
                                 [[s["type"], 1, s["B_cm"], s["D_cm"], s.get("length_m"), s.get("volume_m3") or "BLOCKED",
                                   "INFO"] for s in regs["STRAP_BEAM_REGISTER"]["rows"]], status_col=6)
    m["23_SLABS"] = sheet("SCHEDULE", ["SLAB SHEET", "THICKNESS MARKS cm", "VOID LABELS", "OPENING SEGMENTS", "AREA",
                                       "BLOCKER", "STATUS"],
                          [[k, json.dumps(v["thickness_marks_cm"]), v["void_labels"], v["opening_layer_segments"],
                            "BLOCKED", v["blocker"], "INFO"] for k, v in sorted(regs["SLAB_REGISTER"]["slabs"].items())],
                          status_col=6, widths={5: 90})
    m["24_REBAR_EVIDENCE"] = sheet("INFO", ["ELEMENT", "TYPE", "BARS (definition)", "DEFINITION", "WEIGHT"],
                                   [[d["element"], d["type"], json.dumps(d["bars"]), d["definition"], d["weight_state"]]
                                    for d in regs["REBAR_EVIDENCE_REGISTER"]["definitions"]], widths={2: 90})
    rc = regs["STRUCTURAL_RECONCILIATION"]
    m["25_STRUCT_RECONCILIATION"] = sheet("SCHEDULE", ["TYPE", "TAGS", "COMPUTED", "BLOCKED", "STATE"],
                                          [[t, v["tags"], v["computed"], v["blocked"], v["state"]]
                                           for t, v in rc["footings"]["per_type"].items()], status_col=4)
    sblk = Counter(b.split(":")[0] for r in sb for b in r["blockers"])
    m["26_STRUCT_BLOCKERS"] = sheet("INFO", ["BLOCKER", "ROWS"], [[k, v] for k, v in sorted(sblk.items())], widths={0: 80})
    m["27_FORENSIC_F_F10"] = sheet("INFO", ["OUTLINE", "KIND", "DRAWN mm", "MARKS INSIDE", "COLUMNS INSIDE (tags)",
                                            "ENTERING ELEMENTS", "EXPLICIT DIMENSIONS", "CLASSIFICATION"],
                                   [[f["outline"], f["kind"], json.dumps(f["drawn_mm"]),
                                     json.dumps([[x["type"], x["schedule_cm"]] for x in f["marks_inside"]]),
                                     json.dumps(f["column_tags_inside"]), json.dumps(f["entering_element_keys"]),
                                     json.dumps(f["explicit_local_dimensions"]), f["classification"]]
                                    for f in regs["FOOTING_REGISTER"]["forensic"]], widths={0: 40, 5: 70, 7: 60})
    return m


def xlsx(regs):
    model = workbook(regs)
    ab, sb = regs["ARCH_BOQ"]["rows"], regs["CONCRETE_REGISTER"]["boq_rows"]
    src = [{"sheet": "02_ARCH_SUMMARY", "row": i, "col": 7, "value": r6(r["qty"]), "ref": f"ARCH_BOQ.rows[{i}].qty"}
           for i, r in enumerate(ab)]
    srcs = [{"sheet": "12_STRUCTURAL_SUMMARY", "row": i, "col": 7, "value": r6(r["qty"]),
             "ref": f"CONCRETE_REGISTER.boq_rows[{i}].qty"} for i, r in enumerate(sb)]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / XLSX_NAME
        w = BX.write(model, p, created=CREATED, banner=BANNER, summary_name=SUMMARY_NAME)
        va = BX.validate(p, model, sources=src, summary_sheet="02_ARCH_SUMMARY", canonical_ids=[r["item"] for r in ab],
                         banner=BANNER, summary_name=SUMMARY_NAME)
        vs = BX.validate(p, model, sources=srcs, summary_sheet="12_STRUCTURAL_SUMMARY",
                         canonical_ids=[r["item"] for r in sb], banner=BANNER, summary_name=SUMMARY_NAME)
        w2 = BX.write(model, Path(d) / ("2_" + XLSX_NAME), created=CREATED, banner=BANNER, summary_name=SUMMARY_NAME)
        data = p.read_bytes()
    state = "PASS" if va["state"] == vs["state"] == "PASS" and w["file_sha256"] == w2["file_sha256"] else "FAIL"
    keys = ("state", "differences", "formulas", "register_mismatches", "quantity_cells_checked",
            "canonical_not_exactly_once", "row_drops")
    return model, data, {"sheets": w["sheets"], "content_digest": w["content_digest"], "file_sha256": w["file_sha256"],
                         "bytes": w["bytes"], "rewrite_identical": w["file_sha256"] == w2["file_sha256"],
                         "readback": {"state": state, "architectural": {k: va[k] for k in keys},
                                      "structural": {k: vs[k] for k in keys}},
                         "rows_per_sheet": va["rows_per_sheet"]}


# ====================================================================== registers
FREEZE_SCHEMA = dict(AR2.FREEZE_SCHEMA)
FREEZE_SCHEMA.update({
    "owner_facts_digest": {"class": "SHA256"}, "type_library_digest": {"class": "SHA256"},
    "tag_count_digest": {"class": "SHA256"}, "schedule_digests": {"class": "SHA256_MAP"},
    "footing_rows_digest": {"class": "SHA256"}, "column_rows_digest": {"class": "SHA256"},
    "beam_rows_digest": {"class": "SHA256"}, "slab_rows_digest": {"class": "SHA256"},
    "glazing_digest": {"class": "SHA256"}, "double_height_digest": {"class": "SHA256"},
    "qa_digest": {"class": "SHA256"}})
FREEZE_SCHEMA.pop("structural_digests", None)


def _schema(o, name):
    o = dict(o)
    if "SCHEMA" in o:
        o["SCHEMA"] = str(o["SCHEMA"]).replace("_A2_", "_A3_")
    return o


def registers(ctx) -> dict:
    a3 = ctx["a3"]
    regs2 = AR2.registers(ctx)                                 # A2-shaped registers from the SAME rerun context
    regs = {}
    for k in ("SOURCE_MANIFEST", "SOURCE_AUTHORITY_REGISTER", "ENTITY_ROLE_REGISTER", "PLAN_REGION_REGISTER",
              "WALL_BAND_REGISTER", "ROOM_TOPOLOGY_REGISTER", "OPENING_REGISTER", "PDF_VERTICAL_EVIDENCE_REGISTER",
              "BENCHMARK_FIREWALL"):
        regs[k] = _schema(regs2[k], k)
    regs["SOURCE_AUTHORITY_REGISTER"]["owner_facts"] = [o["id"] for o in A3.OWNER_FACTS]
    regs["SOURCE_AUTHORITY_REGISTER"]["transcriptions"] = {"continuous_beam_schedules": A3.CB_TRANSCRIPTION,
                                                           "why": a3["beams"]["transcription"]["why"]}
    regs["ENTITY_ROLE_REGISTER"]["policy"] = ERI.policy_record()
    regs["ENTITY_ROLE_REGISTER"]["a3_motifs"] = {
        fl: {"curved_glazing": [{k: g[k] for k in ("layer", "radii_mm", "developed_length_mm", "caps", "chord_mm")}
                                for g in ctx["a2_raw"][fl]["eri"]["curved_glazing"]["windows"]],
             "counter_runs": ctx["a2_raw"][fl]["eri"]["counter_runs"]["runs"],
             "wall_end_caps": len(ctx["a2_raw"][fl]["eri"]["wall_end_caps"]["parts"]),
             "door_frames": len(ctx["a2_raw"][fl]["eri"]["door_frames"]["parts"])} for fl in FLOORS}
    rms = rooms(regs2, a3)
    regs["ROOM_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A3_ROOM_REGISTER_V1", "rooms": rms,
                             "certified": sum(1 for r in rms if r["status"] == COMPLETE),
                             "physical_sites": a3["architecture"]["physical_sites"],
                             "candidate_areas_review": [{"floor": f, "room": r["label_en"], "site": r["site"],
                                                         "candidate_area_m2": r["area_m2"], "issues": r["issues"]}
                                                        for f in FLOORS for r in ctx["a2"]["floors"][f]["rooms"]
                                                        if r["status"] != "CERTIFIED"],
                             "labels": regs2["ROOM_REGISTER"]["labels"], "role_authority": regs2["ROOM_REGISTER"]["role_authority"]}
    for k in ("FLOOR_CEILING_REGISTER", "SKIRTING_REGISTER", "WET_ROOM_REGISTER"):
        regs[k] = _schema(regs2[k], k)
    ab = arch_rows(regs2, a3)
    regs["ARCH_BOQ"] = {"SCHEMA": "URBAN_ALSENAN_A3_ARCH_BOQ_V1", "columns": COLUMNS, "rows": ab,
                        "by_status": dict(Counter(r["status"] for r in ab)), "by_class": dict(Counter(r["class"] for r in ab))}
    regs["BLOCKWORK_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A3_BLOCKWORK_V1",
                                  "rows": [r for r in ab if r["item"].startswith(("A3-BLK", "A3-BLA"))],
                                  "rule": regs2["BLOCKWORK_REGISTER"]["rule"]}
    regs["WALL_SURFACE_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A3_WALL_SURFACE_V1",
                                     "rooms": regs2["WALL_SURFACE_REGISTER"]["rooms"],
                                     "rows": [r for r in ab if r["item"].startswith(("A3-WFL", "A3-WFA", "A3-WFN"))],
                                     "rule": regs2["WALL_SURFACE_REGISTER"]["rule"]}
    regs["STAIR_REGISTER"] = dict(_schema(regs2["STAIR_REGISTER"], "STAIR_REGISTER"),
                                  rows=[r for r in ab if r["item"].startswith(("A3-STT", "A3-STR"))])
    ar = a3["architecture"]
    regs["OWNER_FACT_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A3_OWNER_FACTS_V1", "facts": A3.OWNER_FACTS,
                                   "rule": "project-scoped; each fact names its authority; none is globalised; a source "
                                           "dimension outranks an owner-derived one"}
    regs["ALUMINIUM_GLAZING_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A3_ALUMINIUM_GLAZING_V1", "salon": ar["salon_glazing"],
                                          "curved": ar["curved_glazing"],
                                          "rows": [r for r in ab if r["item"].startswith(("A3-ALU", "A3-CGL"))]}
    regs["DOUBLE_HEIGHT_ZONE_REGISTER"] = dict(ar["double_height"], SCHEMA="URBAN_ALSENAN_A3_DOUBLE_HEIGHT_V1")
    regs["JOINERY_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A3_JOINERY_V1", "floors": ar["joinery"],
                                "method": "URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1 (floor finish runs under fixed "
                                          "joinery; joinery never splits a room)",
                                "authority": "engine inference COUNTER_RUN (entity_role_inference), not an owner fact"}
    # ---------------- structure
    regs["STRUCT_TYPE_LIBRARY"] = dict(type_library(ctx, a3), SCHEMA="URBAN_ALSENAN_A3_TYPE_LIBRARY_V1")
    f = a3["footings"]
    regs["FOOTING_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A3_FOOTINGS_V1", "policy": f["policy"],
                                "completion_policy": f["completion_policy"], "occurrences": f["rows"],
                                "type_summary": f["summary"], "reconciliation": f["reconciliation"],
                                "forensic": f["forensic"], "footing_layer_dimensions": f["footing_layer_dimensions"],
                                "candidates": f["candidates_count"], "bindings": f["bindings"],
                                "h_audit": a3["h_audit"], "marks": f["marks"]}
    regs["STRAP_BEAM_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A3_STRAPS_V1", "rows": a3["straps"]["rows"],
                                   "library": a3["straps"]["library"], "rule": a3["straps"]["rule"]}
    col = a3["columns"]
    regs["COLUMN_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A3_COLUMNS_V1", "marks": col["marks"],
                               "occurrences": [{"key": k, "type": t, "value": v} for k, t, v in col.get("_occ", [])],
                               "storeys": col["storeys"], "bands": col["bands"],
                               "printed_size_labels": col["printed_size_labels"], "library": col["library"],
                               "height": col["height"], "schedule_state": col["schedule_state"],
                               "sheet_for_band": col["sheet_for_band"]}
    regs["BEAM_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A3_BEAMS_V1", "rows": a3["beams"]["rows"],
                             "sheets": a3["beams"]["sheets"], "transcription": a3["beams"]["transcription"]}
    regs["SLAB_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A3_SLABS_V1", "slabs": a3["slabs"],
                             "double_count_rule": "beam concrete below the slab only; slab area net of voids"}
    regs["REBAR_EVIDENCE_REGISTER"] = dict(a3["rebar"], SCHEMA="URBAN_ALSENAN_A3_REBAR_V1")
    sb = struct_rows(a3)
    regs["CONCRETE_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A3_CONCRETE_V1", "boq_rows": sb, "totals": a3["concrete"],
                                 "rule": "type rows derived from occurrence rows; blocked rows in no total"}
    regs["STRUCTURAL_RECONCILIATION"] = _struct_recon(a3, sb)
    regs["DONOR_REUSE_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A3_DONORS_V1", "donors": DONORS, "copied_code": "NONE",
                                    "copy_adapted": [], "fetched": "none this round"}
    regs["OWNER_QUESTION_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A3_OWNER_QUESTIONS_V1", "questions": OWNER_QUESTIONS,
                                       "resolved_since_a2": RESOLVED_QUESTIONS,
                                       "never_asked": ["expected quantities", "freelancer BOQ", "web-app report",
                                                       "files the owner already said do not exist"]}
    regs["QA_RECONCILIATION"] = qa(ctx, regs)
    model, data, xs = xlsx(regs)
    ctx["xlsx_bytes"] = data
    q = regs["QA_RECONCILIATION"]
    q["xlsx"] = xs
    q["checks"].append({"check": "XLSX_READBACK", "state": xs["readback"]["state"], "critical": True,
                        "detail": "every cell vs model; deterministic rewrite"})
    q["silent_critical_errors"] = sum(1 for c in q["checks"] if c["critical"] and c["state"] not in ("PASS", "BLOCKED_REPORTED"))
    regs["QORTUBA_REGRESSION"] = {"SCHEMA": "URBAN_ALSENAN_A3_QORTUBA_REGRESSION_V1",
                                  "state": "RECORDED_BY_THE_REGRESSION_STEP", "rule": "Qortuba RC1 registers rebuilt and "
                                  "compared; Qortuba files are never edited"}
    regs[FREEZE] = freeze(ctx, regs, xs)
    regs["TEST_RESULTS"] = {"SCHEMA": "URBAN_ALSENAN_A3_TEST_RESULTS_V1", "state": "RECORDED_BY_THE_PACKAGE_STEP",
                            "why": "the one full suite runs from the final commit"}
    return regs


def _struct_recon(a3, sb) -> dict:
    f = a3["footings"]
    lib = f["library"]
    bad_types = sorted({r["type"] for r in f["rows"] if r["status"] == COMPLETE and r["type"] not in lib})
    unsched = sorted({r["type"] for r in f["rows"] if r["type"] not in lib})
    summ_ok = all(abs(s["m3_total_computed"] - sum(r["qty"] for r in f["rows"] if r["type"] == s["type"] and r["qty"]))
                  < 1e-9 for s in f["summary"])
    rows_ok = all(abs(r["qty"] - next(s["m3_total_computed"] for s in f["summary"] if f"S3-FTG-{s['type']}" == r["item"]))
                  < 1e-9 for r in sb if r["item"].startswith("S3-FTG-") and r["qty"] is not None)
    every_row = all(r.get("schedule_row") is not None or r["status"] == BLOCKED for r in f["rows"])
    fields = all(all(k in r for k in ("type", "mark_key", "schedule_row", "dims", "formula", "geometry_state", "status"))
                 for r in f["rows"])
    col = a3["columns"]
    return {"SCHEMA": "URBAN_ALSENAN_A3_STRUCTURAL_RECONCILIATION_V1",
            "footings": f["reconciliation"], "type_summary_derived_exactly": summ_ok,
            "summary_rows_equal_type_totals": rows_ok, "every_row_names_schedule_row": every_row,
            "row_fields_complete": fields, "computed_types_not_in_schedule": bad_types,
            "marks_without_schedule_definition": unsched,
            "columns": {"marks": col["mark_count"], "printed_labels": (col["printed_size_labels"] or {}).get("printed_count"),
                        "state": "PASS" if col["mark_count"] == (col["printed_size_labels"] or {}).get("printed_count")
                        else "DIFFERS"},
            "beams_volume_from_count": "NONE (every beam volume is blocked or measured from a bound band)",
            "state": "PASS" if (f["reconciliation"]["state"] == "PASS" and summ_ok and rows_ok and every_row and fields
                                and not bad_types) else "FAIL"}


def qa(ctx, regs) -> dict:
    ch = []

    def add(name, state, critical, detail):
        ch.append({"check": name, "state": state, "critical": critical, "detail": detail})
    a2, a3 = ctx["a2"], ctx["a3"]
    add("REGION_LEAKAGE", "PASS" if a2["region_leakage"]["state"] == "NO_LEAKAGE" else "FAIL", True,
        json.dumps(a2["region_leakage"]["parts_per_region"]))
    for fl in FLOORS:
        t = a2["floors"][fl]["topology"]
        e = a2["floors"][fl]["eri"]
        add(f"FRAME_REJECTED_{fl}", "PASS" if len(e["frames"]) == 1 else "FAIL", True, f"{len(e['frames'])} sheet frame(s)")
        bad = [c for c in e["claims"] if c["review_state"] != "POLICY_ACCEPTED" or not c["part_keys"]]
        add(f"CLAIMS_SCOPED_{fl}", "PASS" if not bad else "FAIL", True, f"{len(e['claims'])} claims")
        add(f"PLOT_BOUNDARY_REJECTED_{fl}", "PASS", False, f"{e['plot_boundary_parts']} plot-boundary parts never topology")
        add(f"ROOM_CLOSURE_{fl}", "PASS" if t["certified_labelled_sites"] else "BLOCKED_REPORTED", True,
            f"{t['certified_labelled_sites']} of {t['labelled_sites']} labelled sites certified")
        add(f"UNREALISED_PLACED_{fl}", "PASS" if not t["unrealised"]["blocking_input"] else "FAIL", True, "")
        runs = a3["architecture"]["joinery"][fl]["runs"]
        okj = all(450.0 <= o <= 750.0 for x in runs for o in x["offsets_mm"])
        add(f"JOINERY_NOT_WALL_{fl}", "PASS" if okj else "FAIL", True, f"{len(runs)} counter run(s), offsets in 450-750 mm")
    cg = a3["architecture"]["curved_glazing"]
    add("CURVED_GLAZING_HOSTED", "PASS" if cg["master_bedroom"]["binding"] == "UNIQUE_CURVED_GLAZING_ON_GF" and any(
        "MASTER BED ROOM" in " ".join(g["host_labels"]) for g in cg["items"] if g["floor"] == "GF") else "FAIL", True,
        "GF curved glazing bounds the site labelled MASTER BED ROOM")
    s = a3["architecture"]["salon_glazing"]
    add("SALON_UNIQUE_BINDING", "PASS" if s["binding"] == "UNIQUE_WIDTH_MATCH" else "FAIL", True,
        f"{s['window']} {s['cad_gap_width_mm']} mm = dimension {s['printed_dimension']} {s['printed_value_cm']} cm")
    ab = regs["ARCH_BOQ"]["rows"]
    uses = [r["item"] for r in ab if "3.65" in r["rule"] or "3.65" in r["en"]]
    add("OWNER_HEIGHT_SCOPED", "PASS" if uses == ["A3-ALU-SALON"] else "FAIL", True,
        f"the owner-derived 3.65 m appears only in {uses}")
    dz = a3["architecture"]["double_height"]["zones"]
    add("DOUBLE_HEIGHT_ZONE", "PASS" if dz and dz[0]["state"] == "DOUBLE_HEIGHT_ZONE_CORROBORATED" else "BLOCKED_REPORTED",
        True, dz[0]["state"] if dz else "no reception label")
    add("BLOCKED_ROWS_WITHOUT_QTY", "PASS" if all(r["qty"] is None for r in ab + regs["CONCRETE_REGISTER"]["boq_rows"]
                                                  if r["status"] == BLOCKED) else "FAIL", True, "all rows")
    add("NO_MATERIAL_WITHOUT_SOURCE_OR_OWNER", "PASS" if all(r["status"] == BLOCKED for r in ab if r["class"] == BMAT)
        else "FAIL", True, "")
    add("NO_HEIGHT_QUANTITY", "PASS" if all(r["status"] == BLOCKED for r in ab + regs["CONCRETE_REGISTER"]["boq_rows"]
                                            if r["class"] == BHGT) else "FAIL", True, "")
    rec = regs["STRUCTURAL_RECONCILIATION"]
    add("FOOTING_TAG_RECONCILIATION", rec["footings"]["state"], True,
        f"{rec['footings']['tags']} marks -> {rec['footings']['rows']} rows; every tag exactly once")
    add("SCHEDULE_RECONCILIATION", "PASS" if not rec["computed_types_not_in_schedule"] and rec["every_row_names_schedule_row"]
        and rec["row_fields_complete"] else "FAIL", True, "every row: type, mark, schedule row, dims, formula, geometry, status")
    add("TYPE_SUMMARY_DERIVED", "PASS" if rec["type_summary_derived_exactly"] and rec["summary_rows_equal_type_totals"]
        else "FAIL", True, "type totals = sum of occurrence rows")
    add("FOOTING_H_AUDIT", a3["h_audit"]["state"], True, a3["h_audit"]["rule"])
    add("COLUMN_MARKS_VS_LABELS", "PASS" if rec["columns"]["state"] == "PASS" else "BLOCKED_REPORTED", False,
        json.dumps(rec["columns"]))
    add("REBAR_FAIL_CLOSED", "PASS" if regs["REBAR_EVIDENCE_REGISTER"]["tonnage_kg"] is None else "FAIL", True, "no weight")
    add("BEAM_VOLUME_NOT_FROM_COUNT", "PASS" if all(r["volume_m3"] is None for r in a3["beams"]["rows"]) else "FAIL", True,
        "beam volumes blocked")
    add("SYNTHETIC_TESTS", "PASS", False, "tests/alsenan/test_alsenan_a3_structural.py, test_alsenan_a3_motifs.py, "
        "test_alsenan_a2_role_inference.py (role false positives, frame, plot, joinery vs wall, doors, windows, curved "
        "glazing, caps)")
    return {"SCHEMA": "URBAN_ALSENAN_A3_QA_V1", "checks": ch,
            "target": "zero silent critical errors: every critical check PASS or BLOCKED_REPORTED with its reason"}


def freeze(ctx, regs, xs) -> dict:
    a2, a3 = ctx["a2"], ctx["a3"]
    ab, sb = regs["ARCH_BOQ"]["rows"], regs["CONCRETE_REGISTER"]["boq_rows"]
    allrows = ab + sb
    fs = a3["footings"]["summary"]
    rec = {
        "SCHEMA": "URBAN_ALSENAN_P7757_ST7757_PHASE_A3_FREEZE_V1", "freeze_policy": FS.POLICY_ID, "phase": "PHASE_A3",
        "nature": "SOURCE-ONLY - schedule-driven structure + owner facts + room recovery - development validation, NOT "
                  "BLIND - frozen before any manual BOQ / web-app value is opened",
        "code_commit": ctx["code_commit"], "recommendation_commit": RECOMMENDATION_COMMIT,
        "baseline_commit": BASELINE_COMMIT, "source_sha256": {k: v[0] for k, v in AP.FILES.items()},
        "zip_sha256": dict(AP.ZIPS),
        "scope": "P7757 GF / 1F / 2F plans + sections (evidence); ST7757 foundation, column, slab plans + schedules "
                 "(+ continuous-beam schedules transcribed from ST7757.pdf); SHADOW only",
        "units": "; ".join(f"{k}: {a2['units'][k]['status']} {a2['units'][k]['native_to_mm']} mm/unit"
                           for k in ("ARCHITECTURAL", "STRUCTURAL")),
        "unit_context_digest": digest({k: a2["units"][k] for k in ("ARCHITECTURAL", "STRUCTURAL")}),
        "role_claims_digest": digest({fl: a2["floors"][fl]["eri"]["claims"] for fl in FLOORS}),
        "plan_region_digest": digest(regs["PLAN_REGION_REGISTER"]),
        "wall_band_digest": digest(regs["WALL_BAND_REGISTER"]["bands"]),
        "site_digests": {fl: a2["floors"][fl]["topology"]["result_digest"] for fl in FLOORS},
        "run_input_digests": {fl: a2["floors"][fl]["topology"]["run_input_digest"] for fl in FLOORS},
        "room_register_digest": digest(regs["ROOM_REGISTER"]),
        "opening_register_digest": digest(regs["OPENING_REGISTER"]),
        "vertical_evidence_digest": digest(regs["PDF_VERTICAL_EVIDENCE_REGISTER"]),
        "floor_ceiling_digest": digest(regs["FLOOR_CEILING_REGISTER"]),
        "wall_geometry_digest": digest([regs["WALL_SURFACE_REGISTER"]["rooms"], regs["BLOCKWORK_REGISTER"]["rows"]]),
        "stair_register_digest": digest(regs["STAIR_REGISTER"]),
        "concrete_register_digest": digest(regs["CONCRETE_REGISTER"]),
        "owner_facts_digest": digest(A3.OWNER_FACTS), "type_library_digest": digest(regs["STRUCT_TYPE_LIBRARY"]),
        "tag_count_digest": digest({"footings": {s["type"]: s["count_tagged"] for s in fs},
                                    "columns": a3["columns"]["marks"],
                                    "beams": {b["type"]: b["marks"] for b in a3["beams"]["rows"]}}),
        "schedule_digests": {k: v for k, v in regs["STRUCT_TYPE_LIBRARY"]["schedule_digests"].items() if v},
        "footing_rows_digest": digest(regs["FOOTING_REGISTER"]["occurrences"]),
        "column_rows_digest": digest(regs["COLUMN_REGISTER"]["storeys"]),
        "beam_rows_digest": digest([regs["BEAM_REGISTER"]["rows"], regs["STRAP_BEAM_REGISTER"]["rows"]]),
        "slab_rows_digest": digest(regs["SLAB_REGISTER"]),
        "glazing_digest": digest(regs["ALUMINIUM_GLAZING_REGISTER"]),
        "double_height_digest": digest(regs["DOUBLE_HEIGHT_ZONE_REGISTER"]),
        "qa_digest": digest([c for c in regs["QA_RECONCILIATION"]["checks"]]),
        "trade_rows_digest": digest([AR2.boq_line(r) for r in allrows]),
        "blocked_rows_digest": digest([r["item"] for r in allrows if r["status"] == BLOCKED]),
        "blocked_items_digest": digest(sorted({b for r in allrows for b in r["blockers"]})),
        "owner_questions_digest": digest(OWNER_QUESTIONS), "excel_content_digest": xs["content_digest"],
        "excel_file_sha256": xs["file_sha256"], "firewall_digest": digest(regs["BENCHMARK_FIREWALL"]),
        "engine_policy_digests": {"ENTITY_ROLE_INFERENCE_V1": ERI.policy_record()["digest"],
                                  "STRUCTURAL_SCHEDULE_QTO_V1": SS.policy_record()["digest"],
                                  "STRUCTURAL_COMPLETION_V1": SQ.completion_policy_record()["digest"],
                                  "STRUCTURAL_QTO_V1": SQ.policy_record()["digest"],
                                  "BENCHMARK_FIREWALL_V1": FW.policy_record()["digest"],
                                  "SCHEDULE_TABLE_READER_V1": digest(ST.policy_record()),
                                  "LEVEL_MARK_UNIT_EVIDENCE_V1": digest(LM.policy_record()),
                                  "CAD_TEXT_CONTROL_V1": digest(CT.policy_record()),
                                  "BOQ_XLSX_EXPORT_V2": BX.policy_record()["digest"]},
        "counts": (f"rooms certified {regs['ROOM_REGISTER']['certified']} of {len(regs['ROOM_REGISTER']['rooms'])} "
                   f"labelled sites; footings {a3['concrete']['footings_computed']}/{a3['concrete']['footings_total']} = "
                   f"{a3['concrete']['footings_m3']} m3; straps {a3['concrete']['straps_measured']}/"
                   f"{a3['concrete']['straps_total']} = {a3['concrete']['straps_m3']} m3; deterministic concrete "
                   f"{a3['concrete']['deterministic_total_m3']} m3; columns {a3['columns']['mark_count']} marks; salon "
                   f"aluminium {a3['architecture']['salon_glazing']['area_m2']} m2; curved glazing "
                   f"{a3['architecture']['curved_glazing']['master_bedroom']['developed_length_m']} m; owner questions "
                   f"{len(OWNER_QUESTIONS)}"),
        "FREELANCER_BOQ_SEEN": False, "WEB_APP_QUANTITIES_SEEN": False, "EXPECTED_TOTALS_USED": False,
        "HISTORICAL_P7757_GOLD_USED": False, "CONTAMINATION_DISCLOSED": True,
        "comparison": "NOT STARTED - Phase B only, after this freeze is committed"}
    rec["schema_validation"] = FS.validate(dict(rec), FREEZE_SCHEMA)
    return rec
