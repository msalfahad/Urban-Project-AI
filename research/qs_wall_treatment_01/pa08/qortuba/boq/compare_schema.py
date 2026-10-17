"""Compare the audited Qortuba pricing matrix against the Urban Projects BOQ schema learned from previous projects.

The matrix's pricing units were mine, chosen from general surveying convention.  The library's are the house's, read from its
own workbooks.  Where the two agree, the assumption is retired and the unit becomes sourced.  Where they differ, the house
wins and the Qortuba row is marked for restructuring: no Qortuba quantity is recomputed here, and no historical figure is
carried across.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
PRC = Path(PR.OUT_DIR) / "pa08_qortuba_pricing"

VERDICTS = ("UNIT_CONFIRMED_BY_HOUSE_BOQ", "UNIT_WRONG_HOUSE_USES_ANOTHER", "ROW_NEEDS_RESTRUCTURING",
            "NO_HOUSE_PRECEDENT", "MAPS_CLEANLY_NOW", "STILL_NEEDS_OWNER_OR_PROJECT_DATA")

# Qortuba item number -> the house BOQ item it belongs to, with the verdict on my assumed unit.
# One row per Qortuba item that has a counterpart or a gap worth naming.
MAP = [
    ("C-01", "FLOOR_CERAMIC_TOTAL", "M2", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "اجمالي الارضيات is priced م2, exactly as assumed", "the finishes schedule, to fix which rooms are ceramic"),
    ("C-02", "FLOOR_CERAMIC_TOTAL", "M2", "ROW_NEEDS_RESTRUCTURING",
     "the house gives a named special room its own cover line, as it does for ارضيات حمام السباحه; the three bathrooms "
     "should become their own line rather than a second half of the floor total",
     "the finishes schedule"),
    ("C-03", "WALL_CERAMIC_TOTAL", "M2", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "اجمالي الحوائط is priced م2 and the detail sheet multiplies a run length by a height, which is the conversion already "
     "written on this row", "the wall tiling height"),
    ("C-04", "WALL_CERAMIC_TOTAL", "M2", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "same item; the house splits wet rooms from dry on the decor and render lines, so a separate preparation line fits",
     "the wall tiling height"),
    ("C-05", "SKIRTING_CERAMIC_TOTAL", "LM", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "اجمالي النعلات is priced م.ط with no deduction column used on the cover",
     "the house sheet shows no skirting deduction, so the remaining question is the finish, not the rule"),
    ("C-06", None, "LM", "NO_HOUSE_PRECEDENT",
     "no profile-above-skirting item exists anywhere in the historical library; the nearest is كرانيش, which is a ceiling "
     "cornice and not this product", "the owner naming which BOQ item the black profile is billed under"),
    ("C-07", None, "LM", "NO_HOUSE_PRECEDENT",
     "the ceramic covers carry no زوايا item at all.  The house does measure زوايا ونهايات, but under plaster, in م.ط and "
     "halved by the rule 2م=1م.  Whether ceramic corners follow that rule is not written anywhere",
     "the owner confirming whether ceramic corners bill like plaster corners"),
    ("C-09", None, "NR", "NO_HOUSE_PRECEDENT", "no fixture items appear on any historical ceramic cover",
     "the sanitary drawings, and the owner confirming these are ceramic-trade items"),
    ("CL-01", "GYPSUM_DECOR_DRY_ROOMS", "M2", "ROW_NEEDS_RESTRUCTURING",
     "the house splits ديكور الصالات والغرف from ديكور الحمامات والمطابخ as two priced lines; one flat ceiling area is not "
     "a house row", "the ceiling finish type and the dry/wet split"),
    ("CL-02", "CORNICE_DRY_ROOMS", "LM", "ROW_NEEDS_RESTRUCTURING",
     "unit confirmed: كرانيش is priced م.ط.  But the house splits it dry against wet, so one perimeter line becomes two",
     "the reflected ceiling plan, to say where cornice actually runs"),
    ("CL-03", "GYPSUM_DECOR_DRY_ROOMS", "M2", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "ديكور جبس is priced م2", "a reflected ceiling plan"),
    ("B-01", "BLOCKWORK_200", "M2", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "مبانى سمك 20 سم is priced م2, built as count x length x height; the assumed unit and the conversion both match",
     "the wall height"),
    ("B-02", "BLOCKWORK_150", "M2", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "مبانى سمك 15سم is priced م2", "the wall height"),
    ("B-09", "BLOCKWORK_150", "M2", "ROW_NEEDS_RESTRUCTURING",
     "the house does not carry an openings row: deductions are two columns, خصم فراغات كلى and نصف, against each wall row",
     "the opening heights"),
    ("B-10", "BLOCKWORK_EXTERNAL", "M2", "ROW_NEEDS_RESTRUCTURING",
     "the house prices مبانى الخارجي as an item of its own, separate from the thickness items.  The Qortuba rows are cut by "
     "thickness only and do not separate external from internal",
     "none for the split itself: the takeoff already records each wall's rooms on side A and side B"),
    ("IP-01", "INTERNAL_PLASTER", "M2", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "مساح م2, built as run length x storey height, which is the conversion already on this row",
     "the internal plaster height"),
    ("IP-02", "RENDER_TO_WET_ROOMS", "M2", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "طرطشة حمامات ومطابخ is a real house item priced م2, so the tile-preparation row was correctly separated",
     "the internal plaster height"),
    ("IP-03", "INTERNAL_PLASTER", "M2", "ROW_NEEDS_RESTRUCTURING",
     "no separate column-face item exists on the house plaster invoice; column faces fall inside مساح م2",
     "the internal plaster height"),
    ("IP-04", "DOOR_JAMB_PLASTER", "M2", "UNIT_WRONG_HOUSE_USES_ANOTHER",
     "reveals were carried in LM.  The house measures شرشوب أبواب in م2, as count x girth x depth",
     "the opening heights and the reveal depth"),
    ("EP-01", "EXTERNAL_PLASTER", "M2", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "مساح خارجى م2, openings deducted at half", "the building elevations"),
    ("PT-01", "WALL_PAINT", "M2", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "صبغ الحوائط م2, built as run length x storey height, openings deducted at half",
     "the wall height"),
    ("PT-02", "DECOR_PAINT_WITH_COVE_LIGHT", "M2", "ROW_NEEDS_RESTRUCTURING",
     "the house does not price a flat ceiling paint: it prices صبغ الديكور مع الكوف لايت against the decor area",
     "the ceiling design, to give a decor area rather than a flat ceiling area"),
    ("AL-01", "ALUMINIUM_WINDOWS", "M2", "ROW_NEEDS_RESTRUCTURING",
     "unit confirmed as م2 and the conversion count x width x height matches.  But the house prices two cover items, "
     "اجمالي الأبواب and اجمالي الشبابيك, with the individual openings as detail rows; seven separate priced units is not a "
     "house row", "the opening heights"),
    ("AL-08", "ALUMINIUM_WINDOWS", "M2", "UNIT_WRONG_HOUSE_USES_ANOTHER",
     "a count was carried as a priced row.  In the house bill the count is a multiplier inside the area and is never the "
     "priced quantity", "the opening heights"),
    ("RL-01", "INTERNAL_RAILING", "LM", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "دربزين داخلي is priced م.ط.  The house carries one railing line and does not split sloped from horizontal",
     "a railing layout and specification"),
    ("RL-02", "INTERNAL_RAILING", "LM", "ROW_NEEDS_RESTRUCTURING",
     "the house has one railing item, not a stair item and a balcony item", "a railing layout"),
    ("WP-01", "WET_AREA_WATERPROOFING_FLOOR", "M2", "MAPS_CLEANLY_NOW",
     "عازل ارضيات حمامات is priced م2 and Qortuba already has the three bathroom floor areas in م2",
     "the waterproofing specification confirms the system, but the quantity itself is in the house unit already"),
    ("WP-02", "WET_AREA_WATERPROOFING_UPTURN", "LM", "UNIT_WRONG_HOUSE_USES_ANOTHER",
     "the upturn was carried as م2 needing an upturn height.  The house prices نعلات العازل للحمامات in م.ط, so NO height "
     "is needed at all and the measured bathroom perimeter is already the house quantity",
     "the house sheet does not state whether the perimeter is taken gross or net at the door, so that one question remains"),
    ("WP-03", "ROOF_WATERPROOFING", "M2", "MAPS_CLEANLY_NOW",
     "عازل اسطح و ملاحق is priced م2 and Qortuba has the roof area in م2",
     "confirmation that the roof is in this contract"),
    ("WP-04", "ROOF_WATERPROOFING", "M2", "MAPS_CLEANLY_NOW",
     "the terrace falls under عازل اسطح و ملاحق, the annexe part of the same item",
     "confirmation that the terrace is in this contract"),
    ("MR-01", "STAIR_AND_LANDING_MARBLE", "M2", "ROW_NEEDS_RESTRUCTURING",
     "the house prices اجمالي الدرج والبسطات as ONE combined area.  The Qortuba rows split tread, riser, landing, nosing "
     "and skirting into five, which is not the house structure", "the stair section"),
    ("MR-02", "STAIR_AND_LANDING_MARBLE", "M2", "ROW_NEEDS_RESTRUCTURING",
     "treads are not a separate priced item in the house bill", "the stair section"),
    ("MR-03", "STAIR_AND_LANDING_MARBLE", "M2", "ROW_NEEDS_RESTRUCTURING",
     "risers are not a separate priced item in the house bill", "the stair section"),
    ("MR-04", "STAIR_AND_LANDING_MARBLE", "M2", "ROW_NEEDS_RESTRUCTURING",
     "landings are inside the combined item", "the stair section"),
    ("MR-05", "STAIR_SIDE_PIECE", "NR", "UNIT_WRONG_HOUSE_USES_ANOTHER",
     "nosing was carried in LM.  The house counts التواشيح in عدد, one per step", "the stair section, for the step count"),
    ("MR-06", "STAIR_SKIRTING_MARBLE", "LM", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "اجمالي النعلات under رخام is priced م.ط", "the stair section, for the sloped developed length"),
    ("CN-01", "CONCRETE_FOOTINGS", "M3", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "concrete is priced م³, built as width x length x height x count, with a خصم volume column",
     "the structural drawings"),
    ("ST-01", "REINFORCEMENT_STEEL", "TON", "UNIT_CONFIRMED_BY_HOUSE_BOQ",
     "steel is carried in طن as a column beside the concrete items, not as a workbook of its own",
     "the structural drawings"),
    ("OT-01", "ALUMINIUM_DOORS", "M2", "UNIT_WRONG_HOUSE_USES_ANOTHER",
     "doors were carried as a count in the other-items section.  The house prices اجمالي الأبواب in م2 under aluminium",
     "the opening heights"),
]

# house items with no Qortuba counterpart at all
MISSING_FROM_QORTUBA = [
    ("RENDER_UNDER_SKIRTING", "طرطشة تحت نعلة", "M2",
     "a render band behind the skirting, priced on its own line",
     "Qortuba has the skirting run; the band height is not established"),
    ("PLASTER_CORNERS_AND_ENDS", "زوايا ونهايات", "LM",
     "corner and end beads measured as running length and halved by the stated rule 2م=1م",
     "Qortuba does not count internal corners or wall ends; the geometry exists in the boundary segments but was never "
     "cut into corners and ends"),
    ("EXTERNAL_CORNERS_JOINTS_AND_BEADS", "زوايا وفواصل ومبروم", "LM",
     "external corners, movement joints and rounded beads, same halving rule",
     "needs the elevations"),
    ("DECOR_PAINT_WITH_COVE_LIGHT", "صبغ الديكور مع الكوف لايت", "M2",
     "paint to the decorative ceiling including the cove light detail",
     "needs the ceiling design"),
    ("COURTYARD_FLOOR", "ارضيات الحوش", "M2",
     "courtyard floor as a scope of its own",
     "Qortuba's terraces are measured but the house treats a حوش as its own cover section; a scope decision"),
    ("COURTYARD_SKIRTING", "نعلات الحوش", "LM", "courtyard skirting", "same scope decision"),
    ("ROOF_WATERPROOFING_UPTURN", "نعلات العازل الاسطح", "LM",
     "the roof upturn, priced by linear metre",
     "Qortuba measures the roof AREA but never its perimeter, so this quantity does not exist yet"),
    ("STAIR_SIDE_PIECE", "التواشيح", "NR", "one side piece per step, counted",
     "needs the step count from the stair section"),
    ("POOL_BATHROOM_FLOOR", "ارضيات حمام السباحه", "M2",
     "the house gives a named special room its own cover line",
     "a Qortuba convention question rather than a missing measurement"),
    ("PLASTER_LUMP_SUM_ITEM", "فرفيس مقطوعية", "NR",
     "the house structure allows a lump sum line inside a measured bill",
     "no Qortuba equivalent; worth knowing the shape is permitted"),
]


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
    return name


def finish():
    lib = json.loads((OUT / "URBAN_PROJECTS_BOQ_SCHEMA_LIBRARY.json").read_text("utf-8"))
    aud = json.loads((PRC / "QORTUBA_FINAL_PRICING_AUDIT.json").read_text("utf-8"))
    by_no = {r["ITEM_NO"]: r for r in aud["ROWS"]}
    by_canon = {r["CANONICAL_ITEM"]: r for r in lib["ROWS"]}

    rows = []
    for no, canon, house_unit, verdict, why, needs in MAP:
        q = by_no.get(no)
        h = by_canon.get(canon) if canon else None
        rows.append({
            "QORTUBA_ITEM_NO": no,
            "QORTUBA_ITEM": (q["DESCRIPTION_EN"] if q else None),
            "QORTUBA_ASSUMED_UNIT": (q["UNIT"] if q else None),
            "QORTUBA_MEASURED_INPUT": (q["MEASURED_INPUT"] if q else None),
            "HOUSE_BOQ_ITEM": canon,
            "HOUSE_RAW_ARABIC": (h["RAW_ARABIC_ITEM"] if h else None),
            "HOUSE_PRICING_UNIT": (h["PRICING_UNIT"] if h else house_unit),
            "HOUSE_FORMULA_PATTERN": (h["FORMULA_PATTERN"] if h else None),
            "HOUSE_DEDUCTION_RULE": (h["DEDUCTION_RULE_IF_EXPLICIT"] if h else None),
            "SOURCE_WORKBOOK": (h["SOURCE_WORKBOOK"] if h else None),
            "SOURCE_SHEET": (h["SOURCE_SHEET"] if h else None),
            "VERDICT": verdict, "WHY": why, "STILL_NEEDS": needs,
        })

    q_units = {r["ITEM_NO"]: r["UNIT"] for r in aud["ROWS"]}
    confirmed = [r for r in rows if r["VERDICT"] == "UNIT_CONFIRMED_BY_HOUSE_BOQ"]
    wrong = [r for r in rows if r["VERDICT"] == "UNIT_WRONG_HOUSE_USES_ANOTHER"]
    restr = [r for r in rows if r["VERDICT"] == "ROW_NEEDS_RESTRUCTURING"]
    nohouse = [r for r in rows if r["VERDICT"] == "NO_HOUSE_PRECEDENT"]
    clean = [r for r in rows if r["VERDICT"] == "MAPS_CLEANLY_NOW"]

    out = {
        "ARTIFACT": "QORTUBA_VERSUS_HOUSE_BOQ_SCHEMA",
        "RULE": "where the two disagree the house BOQ wins, because it is the source and my unit was an assumption.  No "
                "Qortuba quantity is recomputed here and no historical figure is carried across.",
        "SCHEMA_LIBRARY_ITEMS": lib["COUNT"], "QORTUBA_AUDIT_ROWS": aud["COUNT"],
        "ROWS": rows, "COUNT": len(rows),
        "BY_VERDICT": dict(Counter(r["VERDICT"] for r in rows)),
        "ANSWER_1_UNITS_CORRECT": [{"ITEM_NO": r["QORTUBA_ITEM_NO"], "UNIT": r["HOUSE_PRICING_UNIT"],
                                    "HOUSE_ITEM": r["HOUSE_RAW_ARABIC"], "WHY": r["WHY"]} for r in confirmed],
        "ANSWER_2_UNITS_WRONG": [{"ITEM_NO": r["QORTUBA_ITEM_NO"], "ASSUMED": r["QORTUBA_ASSUMED_UNIT"],
                                  "HOUSE_UNIT": r["HOUSE_PRICING_UNIT"], "HOUSE_ITEM": r["HOUSE_RAW_ARABIC"],
                                  "WHY": r["WHY"]} for r in wrong],
        "ANSWER_3_ROWS_NEEDING_RESTRUCTURING": [{"ITEM_NO": r["QORTUBA_ITEM_NO"], "HOUSE_ITEM": r["HOUSE_RAW_ARABIC"],
                                                 "WHY": r["WHY"]} for r in restr],
        "ANSWER_4_HOUSE_ITEMS_MISSING_FROM_QORTUBA": [
            {"HOUSE_BOQ_ITEM": c, "RAW_ARABIC": ar, "PRICING_UNIT": u, "WHAT_IT_IS": what, "QORTUBA_POSITION": pos}
            for c, ar, u, what, pos in MISSING_FROM_QORTUBA],
        "ANSWER_5_MAPS_CLEANLY_NOW": [{"ITEM_NO": r["QORTUBA_ITEM_NO"], "HOUSE_ITEM": r["HOUSE_RAW_ARABIC"],
                                       "UNIT": r["HOUSE_PRICING_UNIT"],
                                       "QORTUBA_MEASURED_INPUT": r["QORTUBA_MEASURED_INPUT"],
                                       "WHY": r["WHY"], "REMAINING": r["STILL_NEEDS"]} for r in clean + wrong
                                      if r["QORTUBA_MEASURED_INPUT"] and r["QORTUBA_MEASURED_INPUT"]["VALUE"] is not None
                                      and r["HOUSE_PRICING_UNIT"] == (r["QORTUBA_MEASURED_INPUT"]["UNIT"] or "").replace("LM", "LM")],
        "ANSWER_6_STILL_NEEDS_OWNER_OR_PROJECT_DATA": sorted({r["STILL_NEEDS"] for r in rows if r["STILL_NEEDS"]}),
        "NO_HOUSE_PRECEDENT": [{"ITEM_NO": r["QORTUBA_ITEM_NO"], "QORTUBA_ITEM": r["QORTUBA_ITEM"], "WHY": r["WHY"],
                                "NEEDS": r["STILL_NEEDS"]} for r in nohouse],
        "HOUSE_CONVENTIONS_QORTUBA_MUST_ADOPT": lib["HOUSE_CONVENTIONS"],
    }
    written = [write("QORTUBA_VERSUS_HOUSE_BOQ_SCHEMA", out)]

    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip().splitlines()
    fr = {"ARTIFACT": "FREEZE_QORTUBA_VERSUS_HOUSE_BOQ_SCHEMA",
          "SCHEMA_LIBRARY_DIGEST": json.loads((OUT / "FREEZE_URBAN_PROJECTS_BOQ_SCHEMA_LIBRARY.json").read_text("utf-8"))["DIGEST"],
          "QORTUBA_GEOMETRY_CHANGED": "NONE", "QORTUBA_QUANTITIES_RECOMPUTED": 0,
          "HISTORICAL_QUANTITIES_USED_AS_QORTUBA_INPUTS": 0,
          "GIT_HEAD_AT_FREEZE": head,
          "WORKING_TREE_AT_FREEZE": {"CLEAN": not dirty, "UNCOMMITTED_PATHS": [l[3:] for l in dirty][:20]},
          "CONTENTS": {n: hashlib.sha256((OUT / f"{n}.json").read_bytes()).hexdigest() for n in written},
          "COUNT": len(written)}
    fr["DIGEST"] = hashlib.sha256(json.dumps({k: v for k, v in fr.items() if k != "DIGEST"}, sort_keys=True, default=str).encode()).hexdigest()
    write("FREEZE_QORTUBA_VERSUS_HOUSE_BOQ_SCHEMA", fr)
    return {"COMPARISON": out, "FREEZE": fr}


if __name__ == "__main__":
    o = finish()
    c = o["COMPARISON"]
    print("FREEZE", o["FREEZE"]["DIGEST"][:16], "| mapped rows", c["COUNT"])
    print("verdicts:", c["BY_VERDICT"])
    print()
    print("2. UNITS WRONG:")
    for r in c["ANSWER_2_UNITS_WRONG"]:
        print(f"   {r['ITEM_NO']}  assumed {r['ASSUMED']:4s} -> house {r['HOUSE_UNIT']:4s}  {r['HOUSE_ITEM']}")
    print()
    print("5. MAPS CLEANLY NOW:")
    for r in c["ANSWER_5_MAPS_CLEANLY_NOW"]:
        mi = r["QORTUBA_MEASURED_INPUT"]
        print(f"   {r['ITEM_NO']}  {mi['VALUE']} {mi['UNIT']} -> {r['HOUSE_ITEM']} ({r['UNIT']})")
    print()
    print("4. HOUSE ITEMS MISSING FROM QORTUBA:", len(c["ANSWER_4_HOUSE_ITEMS_MISSING_FROM_QORTUBA"]))
    for r in c["ANSWER_4_HOUSE_ITEMS_MISSING_FROM_QORTUBA"]:
        print(f"   {r['RAW_ARABIC']:34s} {r['PRICING_UNIT']:4s} {r['WHAT_IT_IS'][:60]}")
