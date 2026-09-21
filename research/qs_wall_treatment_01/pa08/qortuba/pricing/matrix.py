"""QORTUBA_PRICING_INPUT_MATRIX: the frozen room-by-room takeoff, reorganised into the trades a bill is priced by.

This module measures nothing.  It reads frozen registers, verifies their digests first, and re-cuts what is already there from
rooms into trades.  The room rows stay underneath as the calculation backup; the trade row is the deliverable.

Six layers are kept apart on every row, because collapsing them is how a geometric length quietly becomes a purchase order:

    MEASURED_GEOMETRY     what the drawing says is there
    COMMERCIAL_SCOPE      what the contract says is payable, which is not the same thing
    WASTE                 the allowance on top
    PROCUREMENT           what is actually bought
    RATE                  the price
    AMOUNT                the product

Only the first is ever filled here.  A row with no rate carries no amount, and a row with no established quantity carries no
number at all.
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
R3 = Path(PR.OUT_DIR) / "pa08_qortuba_r3"
R2 = Path(PR.OUT_DIR) / "pa08_qortuba_r2"

STATUSES = ("SOURCE_ESTABLISHED", "OWNER_INPUT_REQUIRED", "SPEC_REQUIRED", "DRAWING_REQUIRED", "HUMAN_REVIEW")
READINESS = ("READY_TO_PRICE", "PARTIALLY_READY", "NOT_READY")

TRADES = [
    ("A", "CERAMIC_AND_PORCELAIN", "سيراميك"),
    ("B", "CEILING_DECOR", "ديكور سقف"),
    ("C", "BLOCKWORK", "مباني"),
    ("D", "INTERNAL_PLASTER", "مساح داخلي"),
    ("E", "EXTERNAL_PLASTER", "مساح خارجي"),
    ("F", "INTERNAL_PAINT", "صبغ داخلي"),
    ("G", "EXTERNAL_PAINT", "صبغ خارجي"),
    ("H", "ALUMINIUM", "ألمنيوم"),
    ("I", "RAILINGS", "درابزين"),
    ("J", "WATERPROOFING", "عازل"),
    ("K", "MARBLE_AND_STAIRS", "رخام ودرج"),
    ("L", "OTHER_TRADES", "بنود أخرى"),
]
TRADE_AR = {code: ar for code, _, ar in TRADES}
TRADE_NAME = {code: name for code, name, _ in TRADES}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
    return name


def verify_inputs():
    """Read nothing until the workpaper freezes verify."""
    checked = []
    for folder, name in ((QS, "PA08_QORTUBA_ROOM_BY_ROOM_QS_01"), (R3, "PA08_QORTUBA_R3")):
        fr = json.loads((folder / f"FREEZE_{name}.json").read_text("utf-8"))
        bad = [n for n, h in fr["CONTENTS"].items() if not (folder / f"{n}.json").exists() or _sha(folder / f"{n}.json") != h]
        if bad:
            raise SystemExit(f"{name} changed on disk, refusing to build a pricing matrix on it: {bad}")
        checked.append({"FREEZE": name, "DIGEST": fr["DIGEST"], "ARTIFACTS": len(fr["CONTENTS"]), "VERIFIED": True})
    return checked


def reg(folder, name):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


EMPTY_LAYERS = {
    "MEASURED_GEOMETRY": None,          # filled per row
    "COMMERCIAL_SCOPE": {"VALUE": None, "STATE": "SOURCE_REQUIRED",
                         "WHY": "no contract measurement rules for this project have been supplied; a geometric quantity is "
                                "not a payable quantity until they are"},
    "WASTE_PERCENT": {"VALUE": None, "STATE": "OWNER_INPUT_REQUIRED",
                      "WHY": "waste depends on tile size, pattern and cutting, which the owner or the spec sets"},
    "PROCUREMENT_QUANTITY": {"VALUE": None, "STATE": "BLOCKED_BY_WASTE_AND_COMMERCIAL_SCOPE"},
    "RATE": {"VALUE": None, "STATE": "NOT_SUPPLIED", "WHY": "no rate has been given for this project"},
    "AMOUNT": {"VALUE": None, "STATE": "BLOCKED_BY_RATE"},
}


def row(trade, item, subitem, qty, unit, source, formula, status, missing, unlock, confidence,
        review="READY_FOR_OWNER_REVIEW", extra=None):
    """One priced-later line.  A number only ever appears beside the basis that produced it."""
    can = status == "SOURCE_ESTABLISHED" and qty is not None
    layers = json.loads(json.dumps(EMPTY_LAYERS))
    layers["MEASURED_GEOMETRY"] = {"VALUE": qty, "UNIT": unit, "STATE": status, "FORMULA": formula}
    out = {"TRADE_CODE": trade, "TRADE": TRADE_NAME[trade], "TRADE_AR": TRADE_AR[trade],
           "ITEM": item, "SUBITEM": subitem,
           "QUANTITY": qty, "UNIT": unit, "SOURCE": source, "FORMULA": formula, "STATUS": status,
           "CAN_PRICE_NOW": "YES" if can else "NO",
           "CAN_PRICE_NOW_MEANS": "the quantity is established and needs only a rate; it does not mean a rate exists",
           "MISSING_INPUT": missing, "SINGLE_NEXT_INPUT_TO_UNLOCK": unlock,
           "CONFIDENCE": confidence, "REVIEW_STATUS": review, "LAYERS": layers}
    if extra:
        out.update(extra)
    return out


def build():
    ver = verify_inputs()
    inv = reg(QS, "QORTUBA_ROOM_REGISTER")["ROWS"]
    floors = reg(QS, "QORTUBA_QS01_FLOOR_CALCULATIONS")["ROWS"]
    skirt = reg(QS, "QORTUBA_QS01_SKIRTING_TAKEOFF")["ROWS"]
    prof = reg(QS, "QORTUBA_QS01_PROFILE_TAKEOFF")["ROWS"]
    tile = reg(QS, "QORTUBA_QS01_WALL_TILE_TAKEOFF")["ROWS"]
    walls = reg(QS, "QORTUBA_QS01_BLOCK_WALL_TAKEOFF")
    plaster = reg(QS, "QORTUBA_QS01_PLASTER_AND_PAINT_TAKEOFF")["ROWS"]
    ceil = reg(QS, "QORTUBA_QS01_CEILING_TAKEOFF")["ROWS"]
    blue = reg(QS, "QORTUBA_QS01_BLUE_ELEMENT_SCHEDULE")["ROWS"]
    summ = reg(QS, "QORTUBA_QS01_SUMMARY_TOTALS")

    dry = summ["A_DRY_INTERNAL_FLOOR_AREA_M2"]["VALUE"]
    wet = summ["B_WET_INTERNAL_FLOOR_AREA_M2"]["VALUE"]
    sk_dry = summ["D_TOTAL_SKIRTING_LM"]["VALUE"]
    pf_tot = summ["E_TOTAL_BLACK_PROFILE_LM"]["VALUE"]
    ceil_tot = summ["F_TOTAL_CEILING_GEOMETRY_M2"]["VALUE"]
    host = summ["J_TOTAL_BATHROOM_AND_PREPARATION_WALL_CERAMIC_M2"]["WHAT_IS_ESTABLISHED"]
    perim = round(sum(x["GROSS_WALL_LINE_PERIMETER_LM"] for x in skirt), 3)
    acc = defaultdict(float)
    for x in inv:
        if not x["INSIDE_APARTMENT"]:
            acc[x["ZONE_KIND"]] += x["RASTER_AREA_M2"]
    zones = {k: round(v, 4) for k, v in acc.items()}
    dry_names = " + ".join(f"{f['ROOM']} {f['METHOD_A_CAD_POLYGON_AREA_M2']}" for f in floors if f["WET_OR_DRY"] == "DRY")
    wet_names = " + ".join(f"{f['ROOM']} {f['METHOD_A_CAD_POLYGON_AREA_M2']}" for f in floors if f["WET_OR_DRY"] == "WET")
    QSSRC = "QORTUBA_ROOM_BY_ROOM_QS_01, frozen room workpapers from the architectural DWG"

    rows = []

    # ---------------------------------------------------------------- A ceramic and porcelain
    rows += [
        row("A", "FLOOR_FINISH", "dry internal floor area", dry, "M2", QSSRC, dry_names,
            "SOURCE_ESTABLISHED", None,
            "none for the quantity; a rate and the finish specification are needed before it is priced",
            "HIGH: every room measured from its own bounding lines and cross-checked against the raster"),
        row("A", "FLOOR_FINISH", "bathroom floor area", wet, "M2", QSSRC, wet_names,
            "SOURCE_ESTABLISHED", None,
            "none for the quantity; kept separate from the dry package until a trade rule says they combine",
            "HIGH"),
        row("A", "FLOOR_FINISH", "floor finish material by room", None, "M2", QSSRC,
            "geometry is established for all ten rooms; which rooms take ceramic and which take another finish is not drawn",
            "SPEC_REQUIRED", "the finishes schedule",
            "the finishes schedule",
            "NOT_APPLICABLE: this is a specification question, not a measurement"),
        row("A", "WALL_CERAMIC", "bathroom and preparation wall ceramic", None, "M2", QSSRC,
            f"NET_HOST_WALL {host} lm x tiling height; the length is established and the height is not",
            "OWNER_INPUT_REQUIRED", "the wall tiling height",
            "the wall tiling height in millimetres",
            "HIGH on the length, NONE on the area",
            extra={"ESTABLISHED_COMPONENT": {"NET_HOST_WALL_LM": host, "STATE": "SOURCE_ESTABLISHED"},
                   "BY_ROOM": [{"ROOM": t["ROOM"], "NET_HOST_WALL_LM": t["NET_HOST_WALL_LM"],
                                "ROOM_KIND": t["ROOM_KIND"]} for t in tile]}),
        row("A", "SKIRTING", "skirting, dry rooms", sk_dry, "LM", QSSRC,
            " + ".join(f"{x['ROOM']} {x['NET_SKIRTING_LM']}" for x in skirt if x["WET_OR_DRY"] == "DRY"),
            "SOURCE_ESTABLISHED", None,
            "none for the quantity; the skirting height and material are a specification question",
            "HIGH: eligible wall line with doors and one floor-level glazed opening deducted"),
        row("A", "SKIRTING", "skirting or tiling to wet rooms", None, "LM", QSSRC,
            f"{round(sum(x['WET_ROOM_EDGE_LM'] for x in skirt), 3)} lm of bathroom wall edge is measured; whether it is "
            f"skirted or tiled to the floor is not drawn",
            "OWNER_INPUT_REQUIRED", "whether the bathrooms are skirted or tiled at the floor",
            "one instruction: bathrooms skirted, or tiled to floor",
            "HIGH on the length, NONE on which trade takes it",
            extra={"ESTABLISHED_COMPONENT": {"WET_ROOM_WALL_EDGE_LM": round(sum(x["WET_ROOM_EDGE_LM"] for x in skirt), 3),
                                             "STATE": "SOURCE_ESTABLISHED"}}),
        row("A", "PROFILE", "black profile above skirting", pf_tot, "LM", QSSRC,
            "the same eligible wall path as the skirting, issued as a separate BOQ item on the owner's statement that the "
            "profile sits directly above it",
            "SOURCE_ESTABLISHED", None,
            "none for the quantity; the profile type, size and finish are a specification question",
            "HIGH on the path, SPEC_REQUIRED on the product",
            extra={"SEPARATE_BOQ_ITEM_SHARING_ONE_PATH": True,
                   "PROFILE_TYPE_AND_SIZE": {"VALUE": None, "STATE": "SPEC_REQUIRED"}}),
        row("A", "TILE_TRIM", "tile corners, grooves and chamfers", None, "LM",
            "not modelled: these are vertical tile-edge lengths",
            "a tiled internal or external corner is a vertical line whose length is the tiling height, and a groove is a "
            "finishes detail; neither is derivable from a plan",
            "DRAWING_REQUIRED", "the tiling height and a finishes detail showing where corners, grooves and chamfers occur",
            "the wall tiling height in millimetres",
            "NONE: no geometry exists for this item"),
    ]

    # ---------------------------------------------------------------- B ceiling decor
    rows += [
        row("B", "FLAT_CEILING", "flat ceiling plan geometry", ceil_tot, "M2", QSSRC,
            " + ".join(f"{c['ROOM']} {c['CEILING_GEOMETRIC_AREA_M2']}" for c in ceil),
            "SOURCE_ESTABLISHED", None,
            "none for the quantity; the ceiling finish is a specification question",
            "HIGH: each room checked for voids, stair openings, shafts and open-to-above, and none found"),
        row("B", "CEILING_PERIMETER", "perimeter for cove, bulkhead or shadow gap", perim, "LM", QSSRC,
            " + ".join(f"{x['ROOM']} {x['GROSS_WALL_LINE_PERIMETER_LM']}" for x in skirt),
            "SOURCE_ESTABLISHED", None,
            "none for the quantity; whether a cove or bulkhead is built, and its profile, is a specification question",
            "HIGH on the length: the full wall line, with no door deduction, because a cove runs across a door head",
            extra={"WHY_DIFFERENT_FROM_SKIRTING": "the skirting stops at a door opening and a ceiling cove runs over it, so "
                                                  "this is the gross wall line and not the skirting net"}),
        row("B", "GYPSUM_DECOR_CEILING", "gypsum or decorative ceiling area", None, "M2",
            "not drawn", "no reflected ceiling plan exists, so no part of the ceiling is known to be dropped or decorative",
            "DRAWING_REQUIRED", "a reflected ceiling plan",
            "a reflected ceiling plan",
            "NONE"),
        row("B", "CEILING_FINISH", "ceiling finish type", None, "M2",
            "not drawn", "the flat geometry above is released; which part is paint, gypsum board or decor is not stated",
            "SPEC_REQUIRED", "the ceiling finishes schedule",
            "the finishes schedule",
            "NOT_APPLICABLE"),
    ]

    # ---------------------------------------------------------------- C blockwork
    thk = walls["TOTAL_LENGTH_M_BY_THICKNESS"]
    ops = [o for w in walls["ROWS"] for o in w["OPENINGS"]]
    for t in sorted(thk, key=lambda k: -thk[k]):
        rows.append(row("C", "WALL_LENGTH", f"{t} mm wall, plan length", thk[t], "M", QSSRC,
                        f"sum of the accepted {t} mm wall bands on this floor; each band's rooms on side A and side B are "
                        f"listed in the block wall takeoff",
                        "SOURCE_ESTABLISHED", None,
                        "none for the quantity; a wall height and the block specification are needed to turn it into an area",
                        "HIGH" if thk[t] >= 1.0 else
                        f"HUMAN_REVIEW: only {thk[t] * 1000:.0f} mm of wall at this thickness, which is more likely a "
                        f"drafting artefact than a wall"))
    rows += [
        row("C", "WALL_AREA", "blockwork area, all thicknesses", None, "M2", QSSRC,
            f"sum of plan lengths x wall height; the lengths are established ({round(sum(thk.values()), 3)} m in total) and "
            f"no height exists in this drawing set",
            "OWNER_INPUT_REQUIRED", "the wall height",
            "the floor-to-soffit wall height in millimetres",
            "HIGH on the lengths, NONE on the area",
            extra={"ESTABLISHED_COMPONENT": {"TOTAL_WALL_LENGTH_M": round(sum(thk.values()), 3),
                                             "BY_THICKNESS": thk, "STATE": "SOURCE_ESTABLISHED"}}),
        row("C", "OPENING_DEDUCTIONS", "openings in the accepted walls", len(ops), "NR", QSSRC,
            "openings recorded on the accepted wall bands, with their spans: "
            + ", ".join(f"{o['CLASS']} {o['SPAN_MM']:.0f} mm" for o in sorted(ops, key=lambda z: -z["SPAN_MM"])[:8]) + " ...",
            "SOURCE_ESTABLISHED", None,
            "the opening heights, to convert the counted spans into deducted areas",
            "the opening heights, which come with the aluminium and door schedules",
            "MEDIUM: ten of the nineteen openings are still UNRESOLVED in class",
            extra={"OPENING_SPANS_MM": sorted(round(o["SPAN_MM"]) for o in ops),
                   "BY_CLASS": dict(Counter(o["CLASS"] for o in ops)),
                   "DEDUCTED_AREA": {"VALUE": None, "STATE": "BLOCKED_BY_OPENING_HEIGHTS"}}),
        row("C", "BLOCK_SPECIFICATION", "block material and type", None, "NR",
            "not drawn", "the drawing gives thicknesses only; material, density and type are not annotated",
            "SPEC_REQUIRED", "the block specification",
            "the block specification: material, density and type per thickness",
            "NOT_APPLICABLE"),
    ]

    # ---------------------------------------------------------------- D / E plaster
    plast = summ["M_TOTAL_PLASTERABLE_FACE_LENGTH_LM"]["VALUE"]
    col_lm = round(sum(x["COLUMN_FACE_LM"] for x in plaster), 3)
    wet_prep = round(sum(x["WET_ROOM_TILE_PREP_FACE_LM"] for x in plaster), 3)
    normal = round(sum(x["NORMAL_INTERNAL_PLASTER_FACE_LM"] for x in plaster), 3)
    rows += [
        row("D", "PLASTER_FACE", "normal internal plaster face length", normal, "LM", QSSRC,
            " + ".join(f"{x['ROOM']} {x['NORMAL_INTERNAL_PLASTER_FACE_LM']}" for x in plaster
                       if x["NORMAL_INTERNAL_PLASTER_FACE_LM"]),
            "SOURCE_ESTABLISHED", None,
            "none for the quantity; a plaster height turns it into an area",
            "HIGH"),
        row("D", "PLASTER_FACE", "wet room tile-preparation face length", wet_prep, "LM", QSSRC,
            " + ".join(f"{x['ROOM']} {x['WET_ROOM_TILE_PREP_FACE_LM']}" for x in plaster if x["WET_ROOM_TILE_PREP_FACE_LM"]),
            "SOURCE_ESTABLISHED", None,
            "none for the quantity; kept separate because a tile backing is not the same trade as a finish plaster",
            "HIGH"),
        row("D", "PLASTER_FACE", "column faces", col_lm, "LM", QSSRC,
            " + ".join(f"{x['ROOM']} {x['COLUMN_FACE_LM']}" for x in plaster if x["COLUMN_FACE_LM"]),
            "SOURCE_ESTABLISHED", None,
            "none for the quantity; columns are kept on their own line because they are usually a different rate",
            "HIGH"),
        row("D", "PLASTER_AREA", "internal plaster area", None, "M2", QSSRC,
            f"{plast} lm of plasterable face x plaster height, less openings, plus reveals",
            "OWNER_INPUT_REQUIRED", "the internal plaster height",
            "the internal plaster height in millimetres",
            "HIGH on the length, NONE on the area",
            extra={"ESTABLISHED_COMPONENT": {"TOTAL_PLASTERABLE_FACE_LM": plast, "STATE": "SOURCE_ESTABLISHED"}}),
        row("D", "REVEALS", "opening reveal returns", None, "LM", QSSRC,
            "a reveal return needs the opening's depth and its height; the plan gives the wall thickness but no opening height",
            "DRAWING_REQUIRED", "the opening heights",
            "the opening heights",
            "NONE"),
        row("E", "EXTERNAL_PLASTER", "external plaster face and area", None, "M2",
            "not derivable from this plan alone",
            "the plan shows wall bands whose far side is outside the apartment, but the building envelope face and its height "
            "are defined by elevations, which this drawing set does not contain",
            "DRAWING_REQUIRED", "the elevations",
            "the building elevations",
            "NONE"),
    ]

    # ---------------------------------------------------------------- F / G paint
    paint = summ["N_TOTAL_PAINT_ELIGIBLE_FACE_LENGTH_LM"]["VALUE"]
    tiled = round(sum(x["TILED_FACE_LM"] for x in plaster), 3)
    rows += [
        row("F", "WALL_PAINT", "paint eligible wall face length", paint, "LM", QSSRC,
            " + ".join(f"{x['ROOM']} {x['PAINT_ELIGIBLE_FACE_LM']}" for x in plaster if x["PAINT_ELIGIBLE_FACE_LM"]),
            "SOURCE_ESTABLISHED", None,
            "none for the quantity; a wall height turns it into an area",
            "HIGH",
            extra={"EXCLUDED_TILED_FACE_LM": tiled,
                   "WHY": "the three bathrooms are tiled in this drawing's own terms, so their wall faces are excluded from "
                          "the paint length rather than assumed painted"}),
        row("F", "WALL_PAINT", "internal wall paint area", None, "M2", QSSRC,
            f"{paint} lm of paint eligible face x wall height, less openings",
            "OWNER_INPUT_REQUIRED", "the wall height",
            "the floor-to-ceiling height in millimetres",
            "HIGH on the length, NONE on the area"),
        row("F", "CEILING_PAINT", "ceiling paint geometry", ceil_tot, "M2", QSSRC,
            "the flat ceiling geometry, carried on its own line because a ceiling rate is not a wall rate",
            "SOURCE_ESTABLISHED", None,
            "none for the quantity; whether every ceiling is painted is a specification question",
            "HIGH on the geometry, SPEC_REQUIRED on the scope"),
        row("G", "EXTERNAL_PAINT", "external paint area", None, "M2",
            "not derivable from this plan alone",
            "external paint follows the external plaster face, which needs elevations",
            "DRAWING_REQUIRED", "the elevations",
            "the building elevations",
            "NONE"),
    ]

    # ---------------------------------------------------------------- H aluminium
    for b in blue:
        typ = b["TYPE"] if b["TYPE"] != "UNRESOLVED" else " or ".join(b["TYPE_CANDIDATES"])
        rows.append(row("H", "GLAZED_UNIT", f"{b['BLUE_ELEMENT_ID']} {typ}", None, "M2", QSSRC,
                        f"width {b['WIDTH_MM']:.0f} mm is measured; area needs a height",
                        "DRAWING_REQUIRED", "the opening height",
                        "the opening heights",
                        "HIGH on the width, NONE on the area",
                        extra={"WIDTH_MM": b["WIDTH_MM"], "HEIGHT_MM": None, "UNIT_COUNT": 1,
                               "TYPE": b["TYPE"], "TYPE_CANDIDATES": b["TYPE_CANDIDATES"],
                               "WALL_BELOW": b["WALL_BELOW"], "ROOMS": b["ROOMS"],
                               "PRICING_UNIT_STATUS": {"VALUE": None, "STATE": "SPEC_REQUIRED",
                                                       "WHY": "aluminium is priced by m2 or by unit depending on the "
                                                              "supplier's quotation basis; neither is stated"}}))
    rows.append(row("H", "GLAZED_UNIT", "all glazed units, count", len(blue), "NR", QSSRC,
                    f"{len(blue)} glazed elements found on the WINDOW layer, grouped by their frame lines",
                    "SOURCE_ESTABLISHED", None,
                    "none for the count; heights are needed for areas",
                    "HIGH on the count",
                    extra={"TOTAL_WIDTH_LM": round(sum(b["WIDTH_MM"] for b in blue) / 1000, 3),
                           "BY_TYPE": dict(Counter(b["TYPE"] for b in blue))}))

    # ---------------------------------------------------------------- I railings
    rows += [
        row("I", "STAIR_RAILING", "stair railing developed length", None, "LM",
            "not drawn", "no railing, handrail or balustrade geometry exists on any layer of this drawing, and a sloped "
                         "developed length needs the flight's rise, which needs a section",
            "DRAWING_REQUIRED", "a stair section and a railing detail",
            "the stair section",
            "NONE"),
        row("I", "BALCONY_OR_ROOF_RAILING", "horizontal railing length", None, "LM",
            "not drawn", f"the terrace and roof edges are measured as areas ({zones.get('EXTERNAL_TERRACE')} m2 terrace "
                         f"and {zones.get('OPEN_ROOF')} m2 roof) but no railing line is drawn along them",
            "DRAWING_REQUIRED", "the railing layout and type",
            "a roof or terrace detail showing where railing runs, and its type",
            "NONE"),
    ]

    # ---------------------------------------------------------------- J waterproofing
    rows += [
        row("J", "WET_AREA_WATERPROOFING", "bathroom floor waterproofing", wet, "M2", QSSRC,
            wet_names, "SOURCE_ESTABLISHED", None,
            "none for the quantity; the membrane specification is a separate question",
            "HIGH: the same three bathroom floor areas"),
        row("J", "WET_AREA_WATERPROOFING", "vertical upturn", None, "LM", QSSRC,
            f"the bathroom wall perimeter is {round(sum(t['NET_HOST_WALL_LM'] for t in tile if t['ROOM_KIND'] == 'WET_ROOM'), 3)} "
            f"lm; the upturn height and whether an upturn is specified at all are not drawn",
            "SPEC_REQUIRED", "the waterproofing specification and upturn height",
            "the waterproofing specification, including the upturn height",
            "HIGH on the perimeter, NONE on the upturn"),
        row("J", "ROOF_WATERPROOFING", "roof waterproofing area", zones["OPEN_ROOF"], "M2", QSSRC,
            "the cell labelled ROOF on this plan, measured from its own bounding lines",
            "SOURCE_ESTABLISHED", None,
            "whether the roof is in this contract, and the membrane specification",
            "confirmation that the roof is in scope, then the membrane specification",
            "HIGH on the area, SCOPE not confirmed",
            extra={"SCOPE_NOTE": "outside the apartment; kept on its own line and in no apartment subtotal"}),
        row("J", "TERRACE_WATERPROOFING", "terrace waterproofing area", zones["EXTERNAL_TERRACE"], "M2", QSSRC,
            "the two external terrace strips east of the hall and master bedroom",
            "SOURCE_ESTABLISHED", None,
            "whether the terrace is in this contract, and the membrane specification",
            "confirmation that the terrace is in scope",
            "HIGH on the area, SCOPE not confirmed",
            extra={"SCOPE_NOTE": "outside the apartment"}),
    ]

    # ---------------------------------------------------------------- K marble and stairs
    treads = [x for x in inv if x["ZONE_KIND"] == "STAIR" and x["BBOX_MM"] and abs((x["BBOX_MM"][3] - x["BBOX_MM"][1]) - 250) <= 5]
    tread_rows = sorted({round(x["BBOX_MM"][1]) for x in treads})
    rows += [
        row("K", "STAIR_PLAN", "stair plan area on this floor", round(zones["STAIR"] + zones["STAIR_LANDING"], 3), "M2", QSSRC,
            f"{round(zones['STAIR'], 3)} m2 of flight plus {round(zones['STAIR_LANDING'], 3)} m2 of landing, on this floor only",
            "SOURCE_ESTABLISHED", None,
            "whether the stair is in this contract; it is outside the apartment and in no apartment subtotal",
            "confirmation that the stair is in scope",
            "HIGH on the plan area"),
        row("K", "TREAD", "tread going and flight width", None, "NR", QSSRC,
            f"the drawn treads are 250 mm going and the main flight is 1350 mm wide; {len(tread_rows)} tread positions appear "
            f"on this floor's plan, but the number of risers between floors needs a section",
            "DRAWING_REQUIRED", "the stair section",
            "the stair section",
            "HIGH on the going and width, NONE on the counts",
            extra={"TREAD_GOING_MM": 250, "FLIGHT_WIDTH_MM": 1350, "TREAD_POSITIONS_ON_THIS_PLAN": len(tread_rows),
                   "RISER_HEIGHT_MM": {"VALUE": None, "STATE": "DRAWING_REQUIRED"},
                   "RISER_COUNT": {"VALUE": None, "STATE": "DRAWING_REQUIRED"}}),
        row("K", "RISER", "riser area", None, "M2",
            "not derivable from a plan", "a riser is a vertical face; its height comes from a section",
            "DRAWING_REQUIRED", "the stair section", "the stair section", "NONE"),
        row("K", "NOSING_AND_STAIR_SKIRTING", "nosing and stair skirting length", None, "LM",
            "not derivable from a plan",
            "a nosing follows the tread count and a stair skirting follows the sloped developed length; both need the section",
            "DRAWING_REQUIRED", "the stair section", "the stair section", "NONE"),
        row("K", "MARBLE_SPECIFICATION", "stair and landing finish material", None, "M2",
            "not drawn", "no finishes schedule says whether the stair is marble, tile or anything else",
            "SPEC_REQUIRED", "the finishes schedule", "the finishes schedule", "NOT_APPLICABLE"),
    ]

    # ---------------------------------------------------------------- L other trades
    door_ops = [o for o in ops if "DOOR" in o["CLASS"]]
    rows += [
        row("L", "DOORS", "door openings, count and widths", len(door_ops), "NR", QSSRC,
            "openings classed as doors on the accepted wall bands, widths "
            + ", ".join(f"{o['SPAN_MM']:.0f}" for o in sorted(door_ops, key=lambda z: -z["SPAN_MM"])),
            "SOURCE_ESTABLISHED", None,
            "the door heights, leaf material and ironmongery",
            "the opening heights",
            "MEDIUM: five of the eight are PROBABLE rather than CONFIRMED",
            extra={"BY_CLASS": dict(Counter(o["CLASS"] for o in door_ops)),
                   "WIDTHS_MM": sorted(round(o["SPAN_MM"]) for o in door_ops)}),
        row("L", "CONCRETE", "concrete quantities", None, "M3",
            "architectural drawing only", "no structural drawing for Qortuba was supplied; columns appear in plan but their "
                                          "sizes, reinforcement and levels are structural information",
            "DRAWING_REQUIRED", "the structural drawings",
            "the Qortuba structural drawings",
            "NONE"),
        row("L", "STEEL_REINFORCEMENT", "reinforcement quantities", None, "TON",
            "architectural drawing only", "reinforcement is structural information and no structural drawing was supplied",
            "DRAWING_REQUIRED", "the structural drawings",
            "the Qortuba structural drawings",
            "NONE"),
        row("L", "SANITARY_FITTINGS", "sanitary fittings and floor gullies", None, "NR",
            "architectural drawing only",
            "gullies, cisterns and basins are sanitary information; no Qortuba sanitary drawing was supplied",
            "DRAWING_REQUIRED", "the sanitary drawings",
            "the Qortuba sanitary drawings",
            "NONE"),
        row("L", "ELECTRICAL", "electrical quantities", None, "NR",
            "architectural drawing only", "no electrical drawing was supplied",
            "DRAWING_REQUIRED", "the electrical drawings", "the Qortuba electrical drawings", "NONE"),
        row("L", "JOINERY", "fitted joinery runs", None, "LM",
            "partially drawn",
            "furniture outlines are drawn on the FIRNTUR and B-FURNI layers, but the engine does not distinguish a fitted "
            "wardrobe or base unit from loose furniture, so no joinery run is released",
            "HUMAN_REVIEW", "confirmation of which drawn outlines are fitted joinery",
            "the owner or the interior drawings confirming which outlines are fitted",
            "NONE"),
    ]
    return ver, rows, {"ZONES": zones, "PERIMETER_LM": perim}


# ---------------------------------------------------------------------------- §5 readiness by trade
def readiness(rows):
    out = []
    for code, name, ar in TRADES:
        tr = [r for r in rows if r["TRADE_CODE"] == code]
        ready = [r for r in tr if r["CAN_PRICE_NOW"] == "YES"]
        blocked = [r for r in tr if r["CAN_PRICE_NOW"] == "NO"]
        if not tr:
            continue
        if not blocked:
            state, why = "READY_TO_PRICE", "every item in this trade carries an established quantity"
        elif ready:
            state = "PARTIALLY_READY"
            why = (f"{len(ready)} of {len(tr)} items carry an established quantity; the rest are blocked by "
                   + ", ".join(sorted({r["MISSING_INPUT"] for r in blocked if r["MISSING_INPUT"]})))
        else:
            state = "NOT_READY"
            why = "no item in this trade has an established quantity: " + \
                  "; ".join(sorted({r["MISSING_INPUT"] for r in blocked if r["MISSING_INPUT"]}))
        out.append({"TRADE_CODE": code, "TRADE": name, "TRADE_AR": ar, "READINESS": state,
                    "ITEMS": len(tr), "ITEMS_WITH_AN_ESTABLISHED_QUANTITY": len(ready),
                    "ITEMS_BLOCKED": len(blocked), "WHY": why,
                    "UNLOCKS": sorted({r["SINGLE_NEXT_INPUT_TO_UNLOCK"] for r in blocked if r["SINGLE_NEXT_INPUT_TO_UNLOCK"]}),
                    "READY_ITEMS": [f'{r["ITEM"]} / {r["SUBITEM"]}' for r in ready]})
    return out


def unlock_register(rows):
    """§4: the one next thing that would release each blocked item, grouped so a single answer shows everything it frees."""
    by_unlock = defaultdict(list)
    for r in rows:
        if r["CAN_PRICE_NOW"] == "NO" and r["SINGLE_NEXT_INPUT_TO_UNLOCK"]:
            by_unlock[r["SINGLE_NEXT_INPUT_TO_UNLOCK"]].append(r)
    out = []
    for k, v in sorted(by_unlock.items(), key=lambda kv: -len(kv[1])):
        kind = ("OWNER_INPUT" if any(x["STATUS"] == "OWNER_INPUT_REQUIRED" for x in v)
                else "DRAWING" if any(x["STATUS"] == "DRAWING_REQUIRED" for x in v)
                else "SPECIFICATION" if any(x["STATUS"] == "SPEC_REQUIRED" for x in v)
                else "REVIEW")
        out.append({"NEXT_INPUT": k, "KIND": kind, "UNBLOCKS_ITEMS": len(v),
                    "TRADES": sorted({x["TRADE"] for x in v}),
                    "ITEMS": [f'{x["TRADE_AR"]} / {x["ITEM"]} / {x["SUBITEM"]}' for x in v]})
    heights = [x for x in out if "height in millimetres" in x["NEXT_INPUT"]]
    if heights:
        for x in heights:
            x["PART_OF_A_FAMILY"] = {
                "FAMILY": "VERTICAL_HEIGHTS",
                "MEMBERS": sorted(h["NEXT_INPUT"] for h in heights),
                "NOTE": "these are different numbers and are asked for separately, but one building section, or one owner "
                        "statement of the storey heights, would supply all of them at once"}
    return out


# ---------------------------------------------------------------------------- §6 the Excel shape
def excel_structure(rows, ready):
    sections = []
    for code, name, ar in TRADES:
        tr = [r for r in rows if r["TRADE_CODE"] == code]
        if not tr:
            continue
        sections.append({"SECTION_AR": ar, "SECTION_EN": name, "TRADE_CODE": code,
                         "ROWS": [{"البند": f'{r["ITEM"]} / {r["SUBITEM"]}',
                                   "الوصف": r["FORMULA"],
                                   "الوحدة": r["UNIT"],
                                   "الكمية": r["QUANTITY"],
                                   "الهالك %": None,
                                   "كمية الشراء": None,
                                   "سعر الوحدة": None,
                                   "الإجمالي": None,
                                   "مصدر الكمية": r["SOURCE"],
                                   "حالة الاعتماد": r["STATUS"],
                                   "ملاحظات": r["MISSING_INPUT"] or ""} for r in tr]})
    return {"ARTIFACT": "QORTUBA_EXCEL_TRADE_STRUCTURE",
            "SHAPE": "one worksheet per trade section, trades as the top level and rooms underneath as calculation backup",
            "COLUMNS": ["البند", "الوصف", "الوحدة", "الكمية", "الهالك %", "كمية الشراء", "سعر الوحدة", "الإجمالي",
                        "مصدر الكمية", "حالة الاعتماد", "ملاحظات"],
            "COLUMN_NOTES": {"الكمية": "measured geometry only; blank where no quantity is established",
                             "الهالك %": "left blank: waste is an owner or specification input, never derived from geometry",
                             "كمية الشراء": "left blank: it follows the waste percentage and the commercial scope",
                             "سعر الوحدة": "left blank: no rate has been supplied for this project",
                             "الإجمالي": "left blank: no rate, so no amount",
                             "حالة الاعتماد": "one of " + ", ".join(STATUSES)},
            "SECTIONS": sections, "SECTION_COUNT": len(sections),
            "BACKUP_SHEETS": ["QORTUBA_ROOM_REGISTER", "QORTUBA_QS01_FLOOR_CALCULATIONS",
                              "QORTUBA_QS01_SKIRTING_TAKEOFF", "QORTUBA_QS01_PROFILE_TAKEOFF",
                              "QORTUBA_QS01_WALL_TILE_TAKEOFF", "QORTUBA_QS01_BLOCK_WALL_TAKEOFF",
                              "QORTUBA_QS01_PLASTER_AND_PAINT_TAKEOFF", "QORTUBA_QS01_CEILING_TAKEOFF",
                              "QORTUBA_QS01_BLUE_ELEMENT_SCHEDULE", "QORTUBA_HUMAN_QS_SHEET"],
            "ROOM_DATA_STAYS_UNDERNEATH": "the room rows are the calculation backup; the trade row is what gets priced",
            "NOT_PRICED": "no rate was supplied, so no rate or amount cell is filled anywhere in this structure"}


def finish():
    ver, rows, extra = build()
    rd = readiness(rows)
    written = []
    matrix = {"ARTIFACT": "QORTUBA_PRICING_INPUT_MATRIX",
              "WORKPAPER": "PA08_QORTUBA_ROOM_BY_ROOM_QS_01, verified by digest before this matrix was built",
              "INPUT_FREEZES_VERIFIED": ver,
              "ROWS": rows, "COUNT": len(rows),
              "TRADES": [{"CODE": c, "EN": n, "AR": a} for c, n, a in TRADES],
              "STATUSES": STATUSES,
              "BY_STATUS": dict(Counter(r["STATUS"] for r in rows)),
              "BY_TRADE": dict(Counter(r["TRADE"] for r in rows)),
              "CAN_PRICE_NOW": dict(Counter(r["CAN_PRICE_NOW"] for r in rows)),
              "SUPPORTING_ZONES_M2": extra["ZONES"],
              "LAYER_RULE": "MEASURED_GEOMETRY, COMMERCIAL_SCOPE, WASTE, PROCUREMENT, RATE and AMOUNT are separate fields on "
                            "every row.  Only the first is filled here: a geometric quantity is not a payable quantity, and "
                            "neither is a purchase quantity.",
              "CAN_PRICE_NOW_IS_SUPERSEDED": {
                  "BY": "QORTUBA_FINAL_PRICING_AUDIT",
                  "WHY": "the CAN_PRICE_NOW flag on these rows tests whether a row holds a number, not whether it holds a "
                         "priceable one.  A blockwork length in metres is not a pricing quantity where the rate is per square "
                         "metre.  Read the audit's CLASS field instead; these rows remain as the trade cut they describe."},
              "NO_RATE_RULE": "no rate was supplied for this project, so no row carries a rate or an amount",
              "ROOM_DATA": "the room-by-room calculations remain the supporting workpaper and are unchanged by this matrix"}
    written.append(write("QORTUBA_PRICING_INPUT_MATRIX", matrix))
    written.append(write("QORTUBA_PRICING_READINESS_SUMMARY",
                         {"ARTIFACT": "QORTUBA_PRICING_READINESS_SUMMARY", "ROWS": rd, "COUNT": len(rd),
                          "STATES": READINESS, "BY_STATE": dict(Counter(x["READINESS"] for x in rd)),
                          "NO_OVERALL_PERCENTAGE": "no combined readiness figure is produced; the trades are blocked by "
                                                   "different things and one number would hide which"}))
    unl = unlock_register(rows)
    written.append(write("QORTUBA_MINIMUM_INPUTS_TO_UNLOCK",
                         {"ARTIFACT": "QORTUBA_MINIMUM_INPUTS_TO_UNLOCK", "ROWS": unl, "COUNT": len(unl),
                          "BY_KIND": dict(Counter(x["KIND"] for x in unl)),
                          "RULE": "each entry is the single next thing that would release the items under it; nothing is "
                                  "requested that is not needed by a named item"}))
    written.append(write("QORTUBA_EXCEL_TRADE_STRUCTURE", excel_structure(rows, rd)))

    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip().splitlines()
    contents = {n: _sha(OUT / f"{n}.json") for n in sorted(set(written))}
    fr = {"ARTIFACT": "FREEZE_QORTUBA_PRICING_INPUT_MATRIX", "PROJECT_ALIAS": "QORTUBA",
          "BUILT_FROM": ver, "GEOMETRY_ENGINE_CHANGED": "NONE", "NEW_GEOMETRY_PHASE": "NONE",
          "WHAT_THIS_IS": "a re-cut of frozen room workpapers into trade order; it measures nothing and changes nothing",
          "GIT_HEAD_AT_FREEZE": head,
          "WORKING_TREE_AT_FREEZE": {"CLEAN": not dirty, "UNCOMMITTED_PATHS": [l[3:] for l in dirty][:20]},
          "PRICED": False, "RATES_SUPPLIED": 0,
          "CONTENTS": contents, "COUNT": len(contents)}
    fr["DIGEST"] = hashlib.sha256(json.dumps({k: v for k, v in fr.items() if k != "DIGEST"}, sort_keys=True, default=str).encode()).hexdigest()
    write("FREEZE_QORTUBA_PRICING_INPUT_MATRIX", fr)
    return {"MATRIX": matrix, "READINESS": rd, "UNLOCK": unl, "FREEZE": fr}


if __name__ == "__main__":
    o = finish()
    print("FREEZE", o["FREEZE"]["DIGEST"][:16], "| rows", o["MATRIX"]["COUNT"], "| can price now", o["MATRIX"]["CAN_PRICE_NOW"])
    print()
    for r in o["READINESS"]:
        print(f"  {r['TRADE_AR']:12s} {r['TRADE'][:22]:24s} {r['READINESS']:16s} {r['ITEMS_WITH_AN_ESTABLISHED_QUANTITY']}/{r['ITEMS']}")
    print()
    print("MINIMUM INPUTS:")
    for u in o["UNLOCK"]:
        print(f"  [{u['KIND']:13s}] unblocks {u['UNBLOCKS_ITEMS']:2d}  {u['NEXT_INPUT'][:78]}")
