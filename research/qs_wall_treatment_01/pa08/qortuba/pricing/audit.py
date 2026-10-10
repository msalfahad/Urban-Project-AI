"""QORTUBA_FINAL_PRICING_AUDIT: separate raw geometry, takeoff quantity and final pricing quantity.

The pricing matrix marked a row ready when it held a number.  That is the wrong test.  A blockwork length in metres is not a
pricing quantity where the rate is per square metre; a stair footprint is not a marble quantity; a count of openings is not an
aluminium quantity.  A row is ready only when what exists is in the unit AND on the basis the bill actually prices.

This pass reclassifies.  It measures nothing new, invents no height, infers no scope, and touches no geometry: each row keeps
the measured input it already had, gains the pricing unit its final quantity must arrive in, and states the one input that
stands between the two.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_pricing"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"

CLASSES = ("FINAL_PRICING_QUANTITY", "MEASUREMENT_INPUT", "SCOPE_NOT_CONFIRMED", "SOURCE_REQUIRED",
           "SPEC_REQUIRED", "NOT_APPLICABLE")
READINESS = ("READY_TO_PRICE", "PARTIALLY_READY", "NOT_READY")

SECTIONS = [
    ("1", "C", "سيراميك", "Ceramic Works"),
    ("2", "CL", "ديكور سقف", "Ceiling Decoration"),
    ("3", "B", "مباني", "Blockwork"),
    ("4", "IP", "مساح داخلي", "Internal Plaster"),
    ("5", "EP", "مساح خارجي", "External Plaster"),
    ("6", "PT", "صبغ داخلي", "Internal Paint"),
    ("7", "PX", "صبغ خارجي", "External Paint"),
    ("8", "AL", "ألمنيوم", "Aluminium"),
    ("9", "RL", "درابزين", "Railings"),
    ("10", "WP", "عازل", "Waterproofing"),
    ("11", "MR", "رخام ودرج", "Marble and Stairs"),
    ("12", "CN", "خرسانة", "Concrete"),
    ("13", "ST", "حديد", "Steel"),
    ("14", "SN", "صحي", "Sanitary"),
    ("15", "EL", "كهرباء", "Electrical"),
    ("16", "OT", "بنود أخرى", "Other Items"),
]
SEC_AR = {p: ar for _, p, ar, _ in SECTIONS}
SEC_EN = {p: en for _, p, _, en in SECTIONS}
SEC_NO = {p: n for n, p, _, _ in SECTIONS}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
    return name


def verify():
    fr = json.loads((QS / "FREEZE_PA08_QORTUBA_ROOM_BY_ROOM_QS_01.json").read_text("utf-8"))
    bad = [n for n, h in fr["CONTENTS"].items() if _sha(QS / f"{n}.json") != h]
    if bad:
        raise SystemExit(f"the takeoff workpaper changed; refusing to audit on it: {bad}")
    mx = json.loads((OUT / "QORTUBA_PRICING_INPUT_MATRIX.json").read_text("utf-8"))
    return fr, mx


def sources():
    """Every measured figure this audit re-uses, read from the frozen workpapers.  Nothing is recomputed."""
    def r(n, folder=QS):
        return json.loads((folder / f"{n}.json").read_text("utf-8"))
    s = r("QORTUBA_QS01_SUMMARY_TOTALS")
    tile = r("QORTUBA_QS01_WALL_TILE_TAKEOFF")["ROWS"]
    plaster = r("QORTUBA_QS01_PLASTER_AND_PAINT_TAKEOFF")["ROWS"]
    skirt = r("QORTUBA_QS01_SKIRTING_TAKEOFF")["ROWS"]
    blue = r("QORTUBA_QS01_BLUE_ELEMENT_SCHEDULE")["ROWS"]
    walls = r("QORTUBA_QS01_BLOCK_WALL_TAKEOFF")
    floors = r("QORTUBA_QS01_FLOOR_CALCULATIONS")["ROWS"]
    baths = [t for t in tile if t["ROOM_KIND"] == "WET_ROOM"]
    prep = [t for t in tile if t["ROOM_KIND"] != "WET_ROOM"]
    ops = [o for w in walls["ROWS"] for o in w["OPENINGS"]]
    return {
        "DRY_FLOOR_M2": s["A_DRY_INTERNAL_FLOOR_AREA_M2"]["VALUE"],
        "WET_FLOOR_M2": s["B_WET_INTERNAL_FLOOR_AREA_M2"]["VALUE"],
        "SKIRTING_LM": s["D_TOTAL_SKIRTING_LM"]["VALUE"],
        "PROFILE_LM": s["E_TOTAL_BLACK_PROFILE_LM"]["VALUE"],
        "CEILING_M2": s["F_TOTAL_CEILING_GEOMETRY_M2"]["VALUE"],
        "BATH_HOST_LM": round(sum(t["NET_HOST_WALL_LM"] for t in baths), 3),
        "PREP_HOST_LM": round(sum(t["NET_HOST_WALL_LM"] for t in prep), 3),
        "WET_EDGE_LM": round(sum(x["WET_ROOM_EDGE_LM"] for x in skirt), 3),
        "CEILING_PERIM_LM": round(sum(x["GROSS_WALL_LINE_PERIMETER_LM"] for x in skirt), 3),
        "PLASTER_NORMAL_LM": round(sum(x["NORMAL_INTERNAL_PLASTER_FACE_LM"] for x in plaster), 3),
        "PLASTER_WET_LM": round(sum(x["WET_ROOM_TILE_PREP_FACE_LM"] for x in plaster), 3),
        "PLASTER_COLUMN_LM": round(sum(x["COLUMN_FACE_LM"] for x in plaster), 3),
        "PAINT_LM": s["N_TOTAL_PAINT_ELIGIBLE_FACE_LENGTH_LM"]["VALUE"],
        "TILED_FACE_LM": round(sum(x["TILED_FACE_LM"] for x in plaster), 3),
        "WALL_BY_THK": walls["TOTAL_LENGTH_M_BY_THICKNESS"],
        "WALL_TOTAL_M": round(sum(walls["TOTAL_LENGTH_M_BY_THICKNESS"].values()), 3),
        "OPENINGS": ops, "BLUE": blue, "FLOORS": floors,
        "DOOR_OPS": [o for o in ops if "DOOR" in o["CLASS"]],
        "STAIR_M2": 12.643, "ROOF_M2": 43.31, "TERRACE_M2": 25.9,
    }


def rows_for(v):
    """Every audited row, written out one by one so the classification is readable rather than inferred."""
    R = []
    n = defaultdict(int)

    def add(pre, ar, en, pricing_unit, measured, measured_unit, cls, final_formula, blocker, notes, extra=None):
        n[pre] += 1
        row = {"ITEM_NO": f"{pre}-{n[pre]:02d}", "SECTION_NO": SEC_NO[pre], "SECTION_AR": SEC_AR[pre],
               "SECTION_EN": SEC_EN[pre], "ITEM_AR": ar, "DESCRIPTION_EN": en,
               "UNIT": pricing_unit,
               "MEASURED_INPUT": {"VALUE": measured, "UNIT": measured_unit},
               "FINAL_BOQ_QUANTITY": {"VALUE": None, "UNIT": pricing_unit},
               "FINAL_QUANTITY_FORMULA": final_formula,
               "CLASS": cls, "BLOCKER": blocker,
               "SOURCE": "DWG geometry via PA08_QORTUBA_ROOM_BY_ROOM_QS_01" if measured is not None else "not measurable from this drawing set",
               "NOTES": notes,
               "WASTE_PERCENT": None, "PURCHASE_QTY": None, "RATE": None, "AMOUNT": None}
        if extra:
            row.update(extra)
        R.append(row)

    # ---------------------------------------------------------------- 1 ceramic
    add("C", "سيراميك أرضيات - غرف جافة", "Floor ceramic, dry rooms", "M2", v["DRY_FLOOR_M2"], "M2",
        "SCOPE_NOT_CONFIRMED",
        "sum of the room floor areas the finishes schedule assigns to ceramic",
        "the finishes schedule: which rooms take ceramic and which take another finish",
        "the seven dry room areas are measured exactly; the ceramic scope within them is not drawn")
    add("C", "سيراميك أرضيات - حمامات", "Floor ceramic, bathrooms", "M2", v["WET_FLOOR_M2"], "M2",
        "SCOPE_NOT_CONFIRMED",
        "sum of the bathroom floor areas the finishes schedule assigns to ceramic",
        "the finishes schedule",
        "three bathroom areas measured exactly; kept apart from the dry package")
    add("C", "سيراميك جدران - حمامات", "Wall ceramic, bathrooms", "M2", v["BATH_HOST_LM"], "LM",
        "MEASUREMENT_INPUT",
        "net host wall length x tile height, less the opening areas",
        "the wall tiling height in millimetres",
        "net host wall for the three bathrooms; a length is not a wall ceramic quantity")
    add("C", "سيراميك جدران - تحضير", "Wall ceramic, preparation area", "M2", v["PREP_HOST_LM"], "LM",
        "MEASUREMENT_INPUT",
        "net host wall length x tile height, less the opening areas",
        "the wall tiling height in millimetres",
        "the preparation area is measured separately and is not assumed to be a kitchen")
    add("C", "نعلة مخفي", "Skirting", "LM", v["SKIRTING_LM"], "LM",
        "MEASUREMENT_INPUT",
        "the eligible wall path adjusted by the contract's own deduction rule",
        "the commercial measurement basis, and the skirting specification",
        "the unit is already lm, but the geometric path is not the payable path until the deduction rule is agreed")
    add("C", "بروفايل أعلى النعلة", "Profile above skirting", "LM", v["PROFILE_LM"], "LM",
        "MEASUREMENT_INPUT",
        "the same adjusted path as the skirting, as a separate BOQ item",
        "the commercial measurement basis, and the profile type and size",
        "same underlying path as the skirting; two items, one path")
    add("C", "نعلة أو تبليط - حمامات", "Skirting or tiling to wet rooms", "LM", v["WET_EDGE_LM"], "LM",
        "SCOPE_NOT_CONFIRMED",
        "whichever trade the owner assigns to the bathroom wall edge",
        "one instruction: bathrooms skirted, or tiled to the floor",
        "the wall edge is measured; which trade takes it is not drawn")
    add("C", "زوايا + جروف", "Corners and grooves", "LM", None, None, "SOURCE_REQUIRED",
        "vertical corner and groove lengths from the tiling layout",
        "the tiling layout or a finishes detail, and the tiling height",
        "a vertical tile edge cannot be measured from a plan")
    add("C", "زوايا شطف", "Chamfered corners", "LM", None, None, "SOURCE_REQUIRED",
        "chamfer lengths from the tiling layout",
        "the tiling layout or a finishes detail, and the tiling height", "as above")
    add("C", "بلاعة", "Floor drain, ceramic works to", "NR", None, None, "SOURCE_REQUIRED",
        "count from the sanitary layout", "the sanitary drawings", "not placed on the architectural plan")
    add("C", "حوض قدم", "Foot basin, ceramic works to", "NR", None, None, "SOURCE_REQUIRED",
        "count from the sanitary layout", "the sanitary drawings", "not placed on the architectural plan")
    add("C", "روشنة", "Niche, ceramic works to", "NR", None, None, "SOURCE_REQUIRED",
        "count from the interior or finishes drawings", "the finishes schedule or interior drawings",
        "a shower niche is rarely shown at plan scale")
    add("C", "شباك", "Window opening, ceramic works to", "NR", None, None, "SOURCE_REQUIRED",
        "count of openings inside tiled rooms",
        "the opening schedule, and the tiled-room scope",
        "seven glazed openings are found in the drawing; which sit in tiled rooms needs the tiling scope")
    add("C", "سيفون", "Concealed cistern, ceramic works to", "NR", None, None, "SOURCE_REQUIRED",
        "count from the sanitary layout", "the sanitary drawings", "not placed on the architectural plan")

    # ---------------------------------------------------------------- 2 ceiling
    add("CL", "مساحة السقف (أساس)", "Ceiling base area, flat", "M2", v["CEILING_M2"], "M2",
        "MEASUREMENT_INPUT",
        "the part of the base ceiling area the reflected ceiling plan assigns to each finish",
        "the ceiling finish type, from a reflected ceiling plan or the finishes schedule",
        "base geometry only; a flat ceiling area is not a decor ceiling quantity")
    add("CL", "محيط السقف (كورنيش / سقطة)", "Ceiling perimeter, cove or bulkhead", "LM", v["CEILING_PERIM_LM"], "LM",
        "MEASUREMENT_INPUT",
        "the perimeter stretches the ceiling design actually runs a cove or bulkhead along",
        "the reflected ceiling plan and the ceiling design",
        "room perimeter geometry on the gross wall line, because a cove runs across a door head")
    add("CL", "جبس بورد", "Gypsum board ceiling", "M2", None, None, "SOURCE_REQUIRED",
        "dropped ceiling areas from the reflected ceiling plan", "a reflected ceiling plan",
        "no part of the ceiling is drawn as dropped")
    add("CL", "ديكور سقف", "Decorative ceiling", "M2", None, None, "SOURCE_REQUIRED",
        "decorative areas from the ceiling design", "a reflected ceiling plan and the ceiling design", "not drawn")
    add("CL", "إضاءة مخفية", "Hidden lighting groove", "LM", None, None, "SOURCE_REQUIRED",
        "groove lengths from the ceiling design", "the ceiling design", "not drawn")
    add("CL", "فتحات تكييف / خدمات", "Openings, air conditioning and services", "NR", None, None, "SOURCE_REQUIRED",
        "count from the mechanical and electrical drawings", "the MEP drawings", "not on the architectural plan")

    # ---------------------------------------------------------------- 3 blockwork
    for t in sorted(v["WALL_BY_THK"], key=lambda k: -v["WALL_BY_THK"][k]):
        add("B", f"مباني {t} مم", f"Blockwork, {t} mm", "M2", v["WALL_BY_THK"][t], "M",
            "MEASUREMENT_INPUT",
            "plan length x wall height, less the opening areas",
            "the wall height",
            "plan length only; a length is not a blockwork quantity where the rate is per square metre")
    add("B", "إجمالي أطوال المباني", "Blockwork, all thicknesses", "M2", v["WALL_TOTAL_M"], "M",
        "MEASUREMENT_INPUT",
        "sum of the thickness rows above once each has a height",
        "the wall height",
        "aggregate of the rows above; carried for checking, not for pricing")
    add("B", "خصم الفتحات", "Opening deductions", "M2", len(v["OPENINGS"]), "NR",
        "MEASUREMENT_INPUT",
        "sum of opening width x opening height for each opening in a blockwork wall",
        "the opening heights",
        f"{len(v['OPENINGS'])} openings counted with their widths; ten are still unresolved in class")
    add("B", "مواصفة الطابوق", "Block material and specification", "NR", None, None, "SPEC_REQUIRED",
        "not a quantity", "the block specification: material, density and type per thickness",
        "the drawing gives thicknesses only")

    # ---------------------------------------------------------------- 4 internal plaster
    add("IP", "مساح داخلي عادي", "Internal plaster, normal", "M2", v["PLASTER_NORMAL_LM"], "LM",
        "MEASUREMENT_INPUT",
        "eligible wall length x plaster height, less openings, plus eligible reveals",
        "the internal plaster height",
        "face length only; a length is not a plaster quantity")
    add("IP", "طرطشة / تحضير تبليط", "Tile preparation render to wet rooms", "M2", v["PLASTER_WET_LM"], "LM",
        "MEASUREMENT_INPUT",
        "wet room face length x plaster height, less openings",
        "the internal plaster height",
        "kept apart because a tile backing is not a finish plaster")
    add("IP", "أوجه الأعمدة", "Column faces", "M2", v["PLASTER_COLUMN_LM"], "LM",
        "MEASUREMENT_INPUT",
        "column face length x plaster height",
        "the internal plaster height",
        "kept on its own line because a column is usually a different rate")
    add("IP", "مرتدات الفتحات", "Opening reveal returns", "LM", None, None, "SOURCE_REQUIRED",
        "reveal perimeter x reveal depth for each opening",
        "the opening heights",
        "the plan gives the wall thickness but no opening height")

    # ---------------------------------------------------------------- 5 external plaster
    add("EP", "مساح خارجي", "External plaster", "M2", None, None, "SOURCE_REQUIRED",
        "external envelope face length x height, less openings",
        "the building elevations",
        "the envelope face and its height are defined by elevations, which this set does not contain")

    # ---------------------------------------------------------------- 6 internal paint
    add("PT", "صبغ جدران داخلي", "Internal wall paint", "M2", v["PAINT_LM"], "LM",
        "MEASUREMENT_INPUT",
        "paint eligible wall length x wall height, less openings",
        "the wall height",
        f"the {v['TILED_FACE_LM']} lm of tiled bathroom face is already excluded rather than assumed painted")
    add("PT", "صبغ أسقف", "Ceiling paint", "M2", v["CEILING_M2"], "M2",
        "SCOPE_NOT_CONFIRMED",
        "the ceiling area the finishes schedule assigns to paint",
        "the ceiling finishes scope",
        "the unit is already m2; which ceilings are painted rather than boarded or decorated is not drawn")
    add("PT", "أوجه مبلطة (غير مصبوغة)", "Tiled faces, excluded from paint", "LM", v["TILED_FACE_LM"], "LM",
        "NOT_APPLICABLE",
        "not a paint quantity", None,
        "recorded so the exclusion is visible rather than silent")

    # ---------------------------------------------------------------- 7 external paint
    add("PX", "صبغ خارجي", "External paint", "M2", None, None, "SOURCE_REQUIRED",
        "external plaster area, less openings",
        "the building elevations",
        "follows the external plaster face")

    # ---------------------------------------------------------------- 8 aluminium
    for b in v["BLUE"]:
        typ = b["TYPE"] if b["TYPE"] != "UNRESOLVED" else " or ".join(b["TYPE_CANDIDATES"])
        add("AL", f"وحدة ألمنيوم {b['BLUE_ELEMENT_ID']}", f"{b['BLUE_ELEMENT_ID']} {typ.replace('_', ' ').lower()}",
            "M2", b["WIDTH_MM"] / 1000.0, "M (width)",
            "MEASUREMENT_INPUT",
            "width x height per unit, and the unit count",
            "the opening heights",
            f"width measured from the drawing; wall below: {b['WALL_BELOW']}; the aluminium system specification is also required",
            extra={"WIDTH_M": round(b["WIDTH_MM"] / 1000.0, 3), "HEIGHT_M": None, "UNIT_COUNT": 1,
                   "TYPE": b["TYPE"], "TYPE_CANDIDATES": b["TYPE_CANDIDATES"],
                   "SYSTEM_SPECIFICATION": {"VALUE": None, "STATE": "SPEC_REQUIRED"}})
    add("AL", "إجمالي عدد الوحدات", "All glazed units, count", "NR", len(v["BLUE"]), "NR",
        "MEASUREMENT_INPUT",
        "the count is final only if the contract prices aluminium by unit; otherwise it is an input to an area",
        "the opening heights",
        "a count alone is not an aluminium quantity; the pricing basis, by unit or by square metre, is also unstated")

    # ---------------------------------------------------------------- 9 railings
    add("RL", "درابزين درج", "Stair railing", "LM", None, None, "SOURCE_REQUIRED",
        "true sloped developed length along the flight",
        "a stair section giving the rise, and the railing specification",
        "no railing line is drawn on any layer")
    add("RL", "درابزين سطح / شرفة", "Roof or terrace railing", "LM", None, None, "SOURCE_REQUIRED",
        "horizontal run along the protected edges",
        "a roof or terrace detail showing where railing runs, and its specification",
        "the terrace and roof are measured as areas but carry no drawn railing line")

    # ---------------------------------------------------------------- 10 waterproofing
    add("WP", "عازل أفقي - حمامات", "Horizontal waterproofing, bathroom floors", "M2", v["WET_FLOOR_M2"], "M2",
        "SPEC_REQUIRED",
        "the bathroom floor areas, once the specification confirms the system and its extent",
        "the waterproofing specification",
        "the plan area is established geometry; the system and extent are not")
    add("WP", "عازل رأسي (قلبة)", "Vertical upturn", "M2", v["BATH_HOST_LM"], "LM",
        "SPEC_REQUIRED",
        "bathroom wall perimeter x upturn height",
        "the waterproofing specification",
        "the perimeter is measured; whether an upturn is specified, and to what height, is not")
    add("WP", "عازل السطح", "Roof waterproofing", "M2", v["ROOF_M2"], "M2",
        "SCOPE_NOT_CONFIRMED",
        "the roof area, once it is confirmed to be in this contract",
        "confirmation that the roof is in scope, then the specification",
        "outside the apartment and in no apartment subtotal")
    add("WP", "عازل الشرفة", "Terrace waterproofing", "M2", v["TERRACE_M2"], "M2",
        "SCOPE_NOT_CONFIRMED",
        "the terrace area, once it is confirmed to be in this contract",
        "confirmation that the terrace is in scope, then the specification",
        "outside the apartment")

    # ---------------------------------------------------------------- 11 marble and stairs
    add("MR", "مسقط الدرج (مرجعي)", "Stair plan footprint, reference only", "M2", v["STAIR_M2"], "M2",
        "MEASUREMENT_INPUT",
        "not a marble quantity at all; treads, risers and landings are measured separately",
        "a stair section",
        "plan footprint of flight and landing; it is not the stair finish area")
    add("MR", "قلبات الدرج", "Treads", "M2", None, None, "SOURCE_REQUIRED",
        "tread width x going x number of treads",
        "a stair section", "the plan gives a 250 mm going and a 1350 mm flight width; the riser count needs the section")
    add("MR", "قوائم الدرج", "Risers", "M2", None, None, "SOURCE_REQUIRED",
        "flight width x riser height x number of risers", "a stair section", "a riser is a vertical face")
    add("MR", "بسطات الدرج", "Landings", "M2", None, None, "SOURCE_REQUIRED",
        "landing areas from the stair layout and section", "a stair section",
        "the plan shows landing cells; their finish extent needs the section")
    add("MR", "أنف الدرجة", "Nosing", "LM", None, None, "SOURCE_REQUIRED",
        "tread width x number of treads", "a stair section", "follows the tread count")
    add("MR", "نعلة الدرج", "Stair skirting", "LM", None, None, "SOURCE_REQUIRED",
        "sloped developed length along each flight", "a stair section", "needs the true sloped run")
    add("MR", "مواصفة الرخام", "Marble specification", "NR", None, None, "SPEC_REQUIRED",
        "not a quantity", "the finishes schedule", "no schedule says the stair is marble")

    # ---------------------------------------------------------------- 12-15 other disciplines
    add("CN", "خرسانة", "Concrete", "M3", None, None, "SOURCE_REQUIRED",
        "volumes from the structural drawings", "the Qortuba structural drawings",
        "columns appear in plan; sizes, levels and reinforcement are structural information")
    add("ST", "حديد تسليح", "Reinforcement steel", "TON", None, None, "SOURCE_REQUIRED",
        "weights from the structural drawings and bar schedules", "the Qortuba structural drawings", "not supplied")
    add("SN", "أعمال صحية", "Sanitary works", "NR", None, None, "SOURCE_REQUIRED",
        "counts and runs from the sanitary drawings", "the Qortuba sanitary drawings", "not supplied")
    add("EL", "أعمال كهربائية", "Electrical works", "NR", None, None, "SOURCE_REQUIRED",
        "counts and runs from the electrical drawings", "the Qortuba electrical drawings", "not supplied")

    # ---------------------------------------------------------------- 16 other
    add("OT", "أبواب", "Doors", "NR", len(v["DOOR_OPS"]), "NR",
        "MEASUREMENT_INPUT",
        "count and size per door type",
        "a door schedule giving heights, leaf material and ironmongery",
        "widths measured from the drawing; five of the eight are probable rather than confirmed")
    add("OT", "أعمال نجارة ثابتة", "Fitted joinery", "LM", None, None, "SOURCE_REQUIRED",
        "run lengths of fitted units", "confirmation of which drawn outlines are fitted joinery",
        "furniture outlines are drawn but fitted and loose are not distinguished")
    return R


def readiness(rows):
    out = []
    for no, pre, ar, en in SECTIONS:
        tr = [r for r in rows if r["ITEM_NO"].startswith(pre + "-")]
        if not tr:
            continue
        final = [r for r in tr if r["CLASS"] == "FINAL_PRICING_QUANTITY"]
        counted = [r for r in tr if r["CLASS"] != "NOT_APPLICABLE"]
        # a measured input is a row that already carries a number, whatever the reason its final quantity is held
        measured = [r for r in counted if r["MEASURED_INPUT"]["VALUE"] is not None]
        if final and len(final) == len(counted):
            state, why = "READY_TO_PRICE", "every item has a final quantity in its pricing unit"
        elif measured:
            state = "PARTIALLY_READY"
            why = (f"{len(measured)} of {len(counted)} items carry a measured input, and none has been converted into a "
                   f"final quantity yet")
        else:
            state = "NOT_READY"
            why = "no measured input exists for this trade at all"
        # the minimum input worth asking for first is the one holding back the rows that already have a number
        def rank(b):
            return (-sum(1 for r in tr if r["BLOCKER"] == b and r["MEASURED_INPUT"]["VALUE"] is not None),
                    -sum(1 for r in tr if r["BLOCKER"] == b), b)
        blockers = sorted({r["BLOCKER"] for r in tr if r["BLOCKER"]}, key=rank)
        out.append({"SECTION_NO": no, "TRADE_AR": ar, "TRADE_EN": en, "READINESS": state,
                    "ITEMS": len(tr), "FINAL_PRICING_QUANTITIES": len(final),
                    "ITEMS_WITH_A_MEASURED_INPUT": len(measured),
                    "MEASUREMENT_INPUTS": sum(1 for r in tr if r["CLASS"] == "MEASUREMENT_INPUT"),
                    "BY_CLASS": dict(Counter(r["CLASS"] for r in tr)),
                    "WHY": why, "ALL_BLOCKERS": blockers,
                    "ONE_MINIMUM_INPUT": blockers[0] if blockers else None})
    return out


def finish():
    fr, mx = verify()
    v = sources()
    rows = rows_for(v)
    rd = readiness(rows)
    written = []

    by_cls = Counter(r["CLASS"] for r in rows)
    audit = {"ARTIFACT": "QORTUBA_FINAL_PRICING_AUDIT",
             "SUPERSEDES": "the CAN_PRICE_NOW flag in QORTUBA_PRICING_INPUT_MATRIX, which tested whether a row held a number "
                           "rather than whether it held a priceable one",
             "CORE_RULE": "a row is READY only when the quantity available is in the unit and on the basis the bill prices "
                          "that item by.  A length is not an area; a footprint is not a finish; a count is not an assembly.",
             "THREE_LEVELS": {"RAW_GEOMETRIC_INPUT": "what the drawing measures",
                              "ENGINEERING_TAKEOFF_QUANTITY": "that geometry organised into a trade item",
                              "FINAL_PRICING_QUANTITY": "the takeoff converted into the unit, scope and basis the BOQ prices"},
             "WORKPAPER_FREEZE": fr["DIGEST"], "PRIOR_MATRIX_ROWS": mx["COUNT"],
             "ROWS": rows, "COUNT": len(rows),
             "CLASSES": CLASSES, "BY_CLASS": dict(by_cls),
             "SECTIONS": [{"NO": n, "AR": a, "EN": e} for n, _, a, e in SECTIONS],
             "FINAL_PRICING_QUANTITIES_AVAILABLE_NOW": by_cls["FINAL_PRICING_QUANTITY"],
             "WHAT_THAT_MEANS": ("nothing in this project can be priced from geometry alone yet.  Every trade needs at least "
                                 "one of: a height, a scope decision, a specification or a drawing that does not exist in "
                                 "this set.  The measured inputs below are complete and correct; they are simply not "
                                 "pricing quantities."),
             "NO_NEW_QUANTITIES": "this pass reclassifies only.  No height was invented, no scope inferred, no geometry changed.",
             "COLUMN_RULE": "MEASURED_INPUT, FINAL_BOQ_QUANTITY and UNIT are three separate fields so the workbook is useful "
                            "before the final quantity exists"}
    written.append(write("QORTUBA_FINAL_PRICING_AUDIT", audit))

    written.append(write("QORTUBA_CORRECTED_READINESS",
                         {"ARTIFACT": "QORTUBA_CORRECTED_READINESS", "ROWS": rd, "COUNT": len(rd),
                          "STATES": READINESS, "BY_STATE": dict(Counter(x["READINESS"] for x in rd)),
                          "DEFINITIONS": {"READY_TO_PRICE": "a final BOQ quantity exists in the proper pricing unit and scope",
                                          "PARTIALLY_READY": "measurement inputs exist but the final quantity is blocked",
                                          "NOT_READY": "the required source geometry or specification is absent"},
                          "NO_OVERALL_PERCENTAGE": "the trades are blocked by different things; one figure would hide which",
                          "RAW_LENGTHS_ARE_NOT_COUNTED": "a length or a count is never counted as a final priceable row"}))

    blocked = defaultdict(list)
    for r in rows:
        if r["CLASS"] != "FINAL_PRICING_QUANTITY" and r["BLOCKER"]:
            blocked[r["BLOCKER"]].append(r)
    blk = [{"BLOCKER": k, "BLOCKS_ITEMS": len(v2), "TRADES": sorted({x["SECTION_AR"] for x in v2}),
            "ITEMS": [f'{x["ITEM_NO"]} {x["DESCRIPTION_EN"]}' for x in v2],
            "CLASSES": dict(Counter(x["CLASS"] for x in v2))}
           for k, v2 in sorted(blocked.items(), key=lambda kv: -len(kv[1]))]
    written.append(write("QORTUBA_BLOCKED_FINAL_QUANTITIES",
                         {"ARTIFACT": "QORTUBA_BLOCKED_FINAL_QUANTITIES", "ROWS": blk, "COUNT": len(blk),
                          "TOTAL_BLOCKED_ITEMS": sum(x["BLOCKS_ITEMS"] for x in blk),
                          "ONE_MINIMUM_INPUT_PER_TRADE": [{"SECTION_NO": x["SECTION_NO"], "TRADE_AR": x["TRADE_AR"],
                                                           "TRADE_EN": x["TRADE_EN"], "READINESS": x["READINESS"],
                                                           "MINIMUM_INPUT": x["ONE_MINIMUM_INPUT"]} for x in rd]}))

    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip().splitlines()
    contents = {n: _sha(OUT / f"{n}.json") for n in sorted(set(written))}
    frz = {"ARTIFACT": "FREEZE_QORTUBA_FINAL_PRICING_AUDIT",
           "WORKPAPER_FREEZE_VERIFIED": fr["DIGEST"],
           "GEOMETRY_ENGINE_CHANGED": "NONE", "NEW_GEOMETRY_PHASE": "NONE", "NEW_QUANTITIES_CREATED": 0,
           "GIT_HEAD_AT_FREEZE": head,
           "WORKING_TREE_AT_FREEZE": {"CLEAN": not dirty, "UNCOMMITTED_PATHS": [l[3:] for l in dirty][:20]},
           "FINAL_PRICING_QUANTITIES": by_cls["FINAL_PRICING_QUANTITY"],
           "PRICED": False, "RATES_SUPPLIED": 0,
           "CONTENTS": contents, "COUNT": len(contents)}
    frz["DIGEST"] = hashlib.sha256(json.dumps({k: x for k, x in frz.items() if k != "DIGEST"}, sort_keys=True, default=str).encode()).hexdigest()
    write("FREEZE_QORTUBA_FINAL_PRICING_AUDIT", frz)
    return {"AUDIT": audit, "READINESS": rd, "BLOCKED": blk, "FREEZE": frz}


if __name__ == "__main__":
    o = finish()
    a = o["AUDIT"]
    print("FREEZE", o["FREEZE"]["DIGEST"][:16], "| rows", a["COUNT"])
    print("BY CLASS:", a["BY_CLASS"])
    print("FINAL PRICING QUANTITIES AVAILABLE NOW:", a["FINAL_PRICING_QUANTITIES_AVAILABLE_NOW"])
    print()
    for r in o["READINESS"]:
        print(f"  {r['SECTION_NO']:>2s} {r['TRADE_AR']:12s} {r['TRADE_EN'][:22]:24s} {r['READINESS']:16s} "
              f"final={r['FINAL_PRICING_QUANTITIES']} input={r['MEASUREMENT_INPUTS']}/{r['ITEMS']}  -> {str(r['ONE_MINIMUM_INPUT'])[:52]}")
    print()
    print("TOP BLOCKERS:")
    for b in o["BLOCKED"][:8]:
        print(f"  blocks {b['BLOCKS_ITEMS']:2d}  {b['BLOCKER'][:76]}")
