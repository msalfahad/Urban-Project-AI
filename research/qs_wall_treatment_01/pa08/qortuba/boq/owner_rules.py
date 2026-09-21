"""OWNER RULES V1: the owner's declarations, stored once, and the Qortuba quantities they release.

Three things happen here and they are kept apart.  The owner's rules are recorded at the level the owner set them, with the
historical precedents they supersede named rather than quietly dropped.  The Qortuba parameters are recorded as project
values, not as company policy.  And the affected quantities are recomputed arithmetically from the FROZEN measurement
registers - no geometry is re-read, no room re-measured, no opening re-detected.

The rule that governs everything below is the priority order: a project drawing beats an owner override, an owner override
beats an Urban standard, an Urban standard beats a temporary default, and a temporary default beats a question.  A
historical precedent sits outside that ladder entirely until the owner puts it on one.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
PRC = Path(PR.OUT_DIR) / "pa08_qortuba_pricing"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"

# ---------------------------------------------------------------------------- §A the permanent priority ladder
PRIORITY = [
    (1, "PROJECT_DRAWING_OR_SPECIFICATION", "an actual source dimension always wins"),
    (2, "EXPLICIT_PROJECT_OWNER_OVERRIDE", "the owner speaking about this project"),
    (3, "APPROVED_URBAN_STANDARD", "company practice the owner has declared"),
    (4, "APPROVED_TEMPORARY_DEFAULT", "a stated placeholder, never source truth"),
    (5, "UNKNOWN_ASK_OWNER", "the only level at which a question may be asked"),
]
HISTORICAL_POSITION = ("a historical BOQ precedent sits on NO rung of this ladder.  It becomes usable only when the owner "
                       "promotes it to an Urban standard or adopts it for the current project")

# ---------------------------------------------------------------------------- §S rules promoted to URBAN_STANDARD
# (id, title, statement, source section, what it supersedes)
URBAN_STANDARDS = [
    ("US-01", "WET_SERVICE_ROOM_CERAMIC",
     "bathroom, WC, shower, kitchen, iron room, washing room, laundry and equivalent owner-approved service rooms take "
     "ceramic or porcelain to BOTH floor and walls, and the wall ceramic continues down to the floor finish",
     "C", []),
    ("US-02", "NO_SKIRTING_IN_A_FULLY_CERAMIC_ROOM",
     "where ceramic floor meets full wall ceramic there is no normal ceramic skirting, no hidden skirting and no hidden "
     "profile: the wall tile reaches the floor tile and there is nothing for a skirting to do",
     "C, O", ["R-26"]),
    ("US-03", "NO_PAINT_ON_A_FULLY_CERAMIC_FACE",
     "normal wall paint is zero on a fully ceramic wall face, and normal plaster is not used as the ceramic backing: the "
     "tile preparation / tartusha / render trade carries that face instead",
     "C", []),
    ("US-04", "WATERPROOFING_IS_A_FLOOR_MEMBRANE_PLUS_A_150_MM_UPTURN",
     "wet-room waterproofing is two items: a horizontal floor membrane measured in m2, and a vertical upturn of 0.15 m "
     "measured along the wet-room perimeter",
     "N", []),
    ("US-05", "THE_MEMBRANE_UPTURN_IS_NOT_BROKEN_AT_A_DOORWAY",
     "the upturn is continuous around the wet-room perimeter and the doorway is NOT deducted, because a membrane that "
     "stops at a threshold is not a waterproof room",
     "N2", ["R-17 is confirmed as to unit and corrected as to path"]),
    ("US-06", "FULL_OPENING_DEDUCTION_FOR_WALL_AREA_TRADES",
     "blockwork, internal plaster, internal paint and equivalent wall-area trades deduct the FULL opening area, width x "
     "height, for every door, window, sliding door and glazed opening",
     "F, I, J, K", ["R-02", "R-07", "R-09", "R-13"]),
    ("US-07", "PLASTER_AND_PAINT_REVEALS_AT_0_25_M",
     "after an opening is deducted from plaster or paint, the finishable reveals are added back at a depth of 0.25 m on "
     "the left, the right and the top.  The sill is not included",
     "H", []),
    ("US-08", "HIDDEN_SKIRTING_AND_HIDDEN_PROFILE_SHARE_ONE_PAYABLE_PATH",
     "the hidden system is two BOQ items measured in linear metres along the SAME payable path, priced at the same rate "
     "per linear metre, and kept as two rows whose amounts are never merged",
     "D1", ["R-36 is confirmed"]),
    ("US-09", "NORMAL_SKIRTING_IS_A_SEPARATE_SYSTEM",
     "normal skirting is one linear-metre item, and on the same pricing basis its unit rate is half the hidden skirting "
     "rate.  This is a rate rule and it changes no quantity; an explicit project rate overrides it",
     "D2", []),
    ("US-10", "SOURCE_DIMENSIONS_OVERRIDE_DEFAULTS",
     "an actual drawing dimension is never overwritten by a default, and a default never becomes source truth",
     "A, G", []),
]

# ---------------------------------------------------------------------------- §B/§S Qortuba project values
QORTUBA_PROJECT_RULES = [
    ("QP-01", "QORTUBA_WALL_TILE_HEIGHT", 3.00, "M", "B", "wall ceramic height for this project only"),
    ("QP-02", "QORTUBA_BLOCKWORK_HEIGHT", 3.00, "M", "B", "blockwork height for this project only"),
    ("QP-03", "QORTUBA_INTERNAL_PLASTER_HEIGHT", 3.00, "M", "B", "internal plaster height for this project only"),
    ("QP-04", "QORTUBA_INTERNAL_PAINT_HEIGHT", 3.00, "M", "B", "internal paint height for this project only"),
    ("QP-05", "QORTUBA_RENDER_BAND_BEHIND_SKIRTING", None, None, "B",
     "NOT_APPLICABLE: Qortuba carries no render band behind the skirting"),
    ("QP-06", "QORTUBA_SKIRTING_SYSTEM", "HIDDEN", None, "B, D1",
     "Qortuba uses the hidden skirting + hidden profile system, so both items run on one payable path"),
    ("QP-07", "QORTUBA_CERAMIC_SERVICE_ROOMS", "BATH x3 + PAINTRY", None, "C",
     "the three bathrooms follow US-01; the Qortuba تحضير / PAINTRY is treated as a preparation/kitchen service zone "
     "for the CERAMIC takeoff, the owner's scope for that instruction"),
    ("QP-08", "QORTUBA_FIXED_CABINET_DEDUCTION", None, None, "E",
     "NOT_APPLICABLE: no fixed cabinet, wardrobe or joinery is deducted from Qortuba skirting or profile"),
]

# ---------------------------------------------------------------------------- §G the one temporary default
TEMPORARY_DEFAULTS = [
    ("TD-01", "DEFAULT_DOOR_WIDTH", 1.00, "M", "G",
     "applies only to a normal door with NO source-established width.  Every Qortuba door width IS source-established, "
     "so this value is stored and never used here"),
    ("TD-02", "DEFAULT_DOOR_HEIGHT", 2.20, "M", "G",
     "applies to a normal door with no source-established height, which is every Qortuba door: the drawing set carries "
     "no heights at all.  It is a placeholder and it is flagged on every quantity that consumed it"),
]
NO_DEFAULT_FOR = ("WINDOW", "SLIDING_DOOR", "GLAZED_OPENING", "UNKNOWN")

# ---------------------------------------------------------------------------- §A/§S what the owner has now overruled
SUPERSEDED = [
    ("R-02", "مساح داخلى", "the half opening deduction on internal plaster",
     "US-06", "Qortuba deducts the full opening area.  The historical rule stays on file as "
              "CONTRACTOR_SPECIFIC_REFERENCE_ONLY"),
    ("R-07", "مساح خارجي", "the half opening deduction on external plaster", "US-06",
     "same correction, same file status; Qortuba measures no external plaster yet"),
    ("R-09", "صبغ", "the half opening deduction on paint", "US-06",
     "paint was asked separately and answered the same way, which is what a separate question is for"),
    ("R-13", "مبانى", "the choice between the full and half blockwork deduction columns", "US-06",
     "the owner chose the full column.  The historical sheet's ambiguity no longer blocks Qortuba"),
    ("R-05", "مساح داخلى", "the render band behind the skirting", "QP-05",
     "the house prices such a band; Qortuba has none, so the item is closed rather than left waiting for a height"),
    ("R-17", "عازل حمام+مطابخ", "the wet-area upturn measured in linear metres", "US-04, US-05",
     "the unit is confirmed by the owner and the PATH is corrected: the doorway is no longer deducted"),
    ("R-26", "سيراميك", "ceramic skirting as a priced item in a wet room", "US-02",
     "in a fully ceramic room there is no skirting of any kind, so the item does not arise"),
]

# ---------------------------------------------------------------------------- §Q the dependency graph
# parameter -> the quantities a change in it must recalculate, and nothing else
DEPENDENCIES = {
    "QORTUBA_WALL_TILE_HEIGHT": ["WALL_CERAMIC_BATHROOMS", "WALL_CERAMIC_SERVICE"],
    "QORTUBA_BLOCKWORK_HEIGHT": ["BLOCKWORK_BY_THICKNESS"],
    "QORTUBA_INTERNAL_PLASTER_HEIGHT": ["INTERNAL_PLASTER", "TILE_PREPARATION"],
    "QORTUBA_INTERNAL_PAINT_HEIGHT": ["INTERNAL_PAINT"],
    "DEFAULT_DOOR_HEIGHT": ["WALL_CERAMIC_BATHROOMS", "WALL_CERAMIC_SERVICE", "BLOCKWORK_BY_THICKNESS",
                            "INTERNAL_PLASTER", "INTERNAL_PAINT", "TILE_PREPARATION", "OPENING_REVEALS"],
    "REVEAL_DEPTH": ["OPENING_REVEALS"],
    "UPTURN_HEIGHT": ["WATERPROOFING_UPTURN_AREA_REFERENCE"],
    "CERAMIC_SERVICE_ROOM_SET": ["SKIRTING", "HIDDEN_PROFILE", "INTERNAL_PLASTER", "INTERNAL_PAINT",
                                 "TILE_PREPARATION", "WALL_CERAMIC_SERVICE", "FLOOR_CERAMIC_SERVICE"],
    "SKIRTING_DEDUCTION_SET": ["SKIRTING", "HIDDEN_PROFILE"],
}
NEVER_RERUN = ["wall detection", "room detection", "opening detection", "floor polygons", "band topology",
               "boundary classification"]

REVEAL_DEPTH = 0.25
UPTURN_HEIGHT = 0.15
NORMAL_SKIRTING_RATE_FACTOR = 0.50

CERAMIC_ROOM_NAMES = ("BATH", "PAINTRY")
WALL_FACE_CLASSES = ("SKIRTING_ELIGIBLE_WALL", "COLUMN_FACE", "WET_ROOM_EDGE")
OPENING_CLASSES = ("DOOR_OPENING", "FLOOR_LEVEL_GLAZED_OPENING")
OPENING_TYPES = ("DOOR", "WINDOW", "SLIDING_DOOR", "GLAZED_OPENING", "UNKNOWN")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
    return name


def reg(folder, name):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


def verify_inputs():
    checked = []
    for folder, name in ((QS, "PA08_QORTUBA_ROOM_BY_ROOM_QS_01"),
                         (OUT, "URBAN_BOQ_RULE_REGISTRY")):
        fr = json.loads((folder / f"FREEZE_{name}.json").read_text("utf-8"))
        bad = [n for n, h in fr["CONTENTS"].items()
               if not (folder / f"{n}.json").exists() or _sha(folder / f"{n}.json") != h]
        if bad:
            raise SystemExit(f"{name} changed on disk, refusing to recalculate on it: {bad}")
        checked.append({"FREEZE": name, "DIGEST": fr["DIGEST"], "ARTIFACTS": len(fr["CONTENTS"]), "VERIFIED": True})
    return checked


def r3(x):
    return None if x is None else round(x + 0.0, 3)


def r4(x):
    return None if x is None else round(x + 0.0, 4)


# ---------------------------------------------------------------------------- §P one register, every opening in it
SITE_TYPE = {"CONFIRMED_DOOR_OPENING": "DOOR", "PROBABLE_DOOR_OPENING": "DOOR",
             "CONFIRMED_WINDOW_OPENING": "WINDOW", "UNRESOLVED": "UNKNOWN"}
BLUE_TYPE = {"WINDOW_WITH_WALL_BELOW": "WINDOW", "FULL_HEIGHT_WINDOW": "WINDOW", "SLIDING_DOOR": "SLIDING_DOOR",
             "OTHER_GLAZING": "GLAZED_OPENING", "UNRESOLVED": "UNKNOWN"}

APARTMENT_ROOMS = {"HALL / whgm", "M.B.ROOM", "BED.ROOM", "PAINTRY", "DRESS", "BATH", "UNLABELLED_INTERNAL_SPACE"}


def opening_register(walls, blue):
    """Every opening with a type, a width, a height and a status.  An UNKNOWN type never reaches a final quantity."""
    rows, by_site = [], {}
    for w in walls["ROWS"]:
        rooms = sorted({r for r in (w["ROOM_SIDE_A"] + w["ROOM_SIDE_B"]) if r in APARTMENT_ROOMS})
        for o in w["OPENINGS"]:
            t = SITE_TYPE[o["CLASS"]]
            row = {
                "OPENING_ID": o["SITE_ID"], "TYPE": t,
                "WIDTH_M": r3(o["SPAN_MM"] / 1000), "WIDTH_SOURCE": "QORTUBA_QS01_BLOCK_WALL_TAKEOFF opening site span",
                "HEIGHT_M": (TEMPORARY_DEFAULTS[1][2] if t == "DOOR" else None),
                "HEIGHT_SOURCE": ("TD-02 APPROVED_TEMPORARY_DEFAULT" if t == "DOOR" else None),
                "HEIGHT_STATE": ("TEMPORARY_OWNER_DEFAULT" if t == "DOOR" else "NOT_ESTABLISHED"),
                "SOURCE": "opening site register, frozen",
                "STATUS": ("USABLE" if t == "DOOR" else "BLOCKS_WALL_AREA_TRADES"),
                "HOST_WALL_ID": w["WALL_ID"], "HOST_WALL_THICKNESS_MM": w["THICKNESS_MM"],
                "ROOMS": rooms, "INSIDE_APARTMENT": bool(rooms),
                "SITE_CLASS": o["CLASS"], "BLUE_ELEMENT_ID": None, "TYPE_CONFLICT": None,
                "NOTE": ("a 150 mm span is a wall-end artefact rather than an opening, and is carried so the ambiguity is "
                         "visible rather than filtered away" if o["SPAN_MM"] <= 150 else None),
            }
            by_site[o["SITE_ID"]] = row
            rows.append(row)
    for b in blue:
        t = BLUE_TYPE[b["TYPE"]]
        sid = b["OPENING_SITE_ID"]
        if sid and sid in by_site:
            r = by_site[sid]
            r["BLUE_ELEMENT_ID"] = b["BLUE_ELEMENT_ID"]
            if r["TYPE"] != t:
                r["TYPE_CONFLICT"] = (f"the opening-site classifier reads {r['SITE_CLASS']}, the blue-element classifier "
                                      f"reads {b['TYPE']}.  The site classification is kept because it rests on the wall "
                                      f"band's own evidence; the disagreement is recorded, not resolved by preference")
            if not r["ROOMS"] and b["ROOMS"]:
                r["ROOMS"] = sorted(set(b["ROOMS"]) & APARTMENT_ROOMS)
            continue
        rows.append({
            "OPENING_ID": b["BLUE_ELEMENT_ID"], "TYPE": t,
            "WIDTH_M": r3(b["WIDTH_MM"] / 1000), "WIDTH_SOURCE": "QORTUBA_QS01_BLUE_ELEMENT_SCHEDULE frame width",
            "HEIGHT_M": None, "HEIGHT_SOURCE": None, "HEIGHT_STATE": "NOT_ESTABLISHED",
            "SOURCE": "blue element schedule, frozen",
            "STATUS": "BLOCKS_WALL_AREA_TRADES",
            "HOST_WALL_ID": None, "HOST_WALL_THICKNESS_MM": b["FRAME_DEPTH_MM"],
            "ROOMS": sorted(set(b["ROOMS"]) & APARTMENT_ROOMS), "INSIDE_APARTMENT": True,
            "SITE_CLASS": None, "BLUE_ELEMENT_ID": b["BLUE_ELEMENT_ID"], "TYPE_CONFLICT": None,
            "NOTE": "no opening site and no host room: this window was never attributed to a wall or a room, so no "
                    "wall-area trade can deduct it even once a height arrives",
        })
    return rows


# ---------------------------------------------------------------------------- the per-room arithmetic
def room_rows(skirt, openings):
    """One row per interior room, built only from its frozen boundary segments."""
    door_h = TEMPORARY_DEFAULTS[1][2]
    rows = []
    for x in skirt:
        name = x["ROOM"].split(" /")[0]
        ceramic = name in CERAMIC_ROOM_NAMES
        segs = x["SEGMENTS"]
        gross = sum(s["LENGTH_MM"] for s in segs) / 1000
        face = sum(s["LENGTH_MM"] for s in segs if s["SEGMENT_CLASS"] in WALL_FACE_CLASSES) / 1000
        doors = [s["LENGTH_MM"] / 1000 for s in segs if s["SEGMENT_CLASS"] == "DOOR_OPENING"]
        glaz = [s["LENGTH_MM"] / 1000 for s in segs if s["SEGMENT_CLASS"] == "FLOOR_LEVEL_GLAZED_OPENING"]
        col = sum(s["LENGTH_MM"] for s in segs if s["SEGMENT_CLASS"] == "COLUMN_FACE") / 1000
        # §E: deduct the clear WIDTH of openings from a linear quantity.  A column face is not an opening, so the
        # skirting runs across it; §E's do-not-deduct list is about things that are not openings, and a column is one.
        skirting = 0.0 if ceramic else gross - sum(doors) - sum(glaz)
        rows.append({
            "ROOM_ID": x["ROOM_ID"], "ROOM": x["ROOM"], "ROOM_NAME": name,
            "FINISH_CLASS": "CERAMIC_SERVICE_ROOM" if ceramic else "DRY_ROOM",
            "FINISH_RULE": "US-01 + QP-07" if ceramic else "no ceramic rule applies",
            "WAS_WET_IN_WORKPAPER": x["WET_OR_DRY"] == "WET",
            "GROSS_WALL_LINE_LM": r3(gross), "WALL_FACE_LM": r3(face), "COLUMN_FACE_LM": r3(col),
            "DOOR_OPENING_LM": r3(sum(doors)), "GLAZED_OPENING_LM": r3(sum(glaz)),
            "DOOR_WIDTHS_M": [r3(d) for d in sorted(doors, reverse=True)],
            "GLAZED_WIDTHS_M": [r3(g) for g in sorted(glaz, reverse=True)],
            "SKIRTING_LM": r3(skirting),
            "HIDDEN_PROFILE_LM": r3(skirting),
            "GROSS_WALL_AREA_M2": r4(gross * 3.0),
            "DOOR_DEDUCTION_M2": r4(sum(d * door_h for d in doors)),
            "GLAZED_DEDUCTION_M2": None if glaz else 0.0,
            "GLAZED_PENDING_WIDTH_M": r3(sum(glaz)) or None,
            "SKIRTING_ARITHMETIC": (f"{gross:.3f} gross wall line - {sum(doors):.3f} doors - {sum(glaz):.3f} glazed "
                                    f"= {skirting:.3f} lm" if not ceramic else
                                    "0.000 lm: US-02, the wall ceramic reaches the floor ceramic"),
        })
    return rows


def wall_rows(walls, openings):
    """Blockwork, one row per wall band, at the owner's 3.00 m height with the full opening deduction."""
    H = 3.00
    by_wall = defaultdict(list)
    for o in openings:
        if o["HOST_WALL_ID"]:
            by_wall[o["HOST_WALL_ID"]].append(o)
    rows = []
    for w in walls["ROWS"]:
        ops = by_wall.get(w["WALL_ID"], [])
        usable = [o for o in ops if o["HEIGHT_M"] is not None]
        pending = [o for o in ops if o["HEIGHT_M"] is None]
        gross = w["LENGTH_M"] * H
        ded = sum(o["WIDTH_M"] * o["HEIGHT_M"] for o in usable)
        rows.append({
            "WALL_ID": w["WALL_ID"], "THICKNESS_MM": w["THICKNESS_MM"], "LENGTH_M": w["LENGTH_M"],
            "ROOMS": sorted({r for r in w["ROOM_SIDE_A"] + w["ROOM_SIDE_B"] if r in APARTMENT_ROOMS}),
            "HEIGHT_M": H, "HEIGHT_RULE": "QP-02",
            "GROSS_AREA_M2": r4(gross),
            "OPENING_DEDUCTION_M2": r4(ded),
            "NET_AREA_M2": (None if pending else r4(gross - ded)),
            "OPENINGS_DEDUCTED": [{"OPENING_ID": o["OPENING_ID"], "TYPE": o["TYPE"], "W": o["WIDTH_M"],
                                   "H": o["HEIGHT_M"]} for o in usable],
            "OPENINGS_PENDING": [{"OPENING_ID": o["OPENING_ID"], "TYPE": o["TYPE"], "W": o["WIDTH_M"],
                                  "WHY": "no height, and no default is permitted for this type"} for o in pending],
            "STATUS": "PARTIALLY_CALCULATED" if pending else "FINAL_QUANTITY_AVAILABLE",
            "ARITHMETIC": (f"{w['LENGTH_M']:.3f} x {H:.2f} = {gross:.4f} m2 gross"
                           + (f" - {ded:.4f} m2 openings = {gross - ded:.4f} m2 net" if not pending
                              else f" - {ded:.4f} m2 resolved openings, {len(pending)} opening(s) still unheighted")),
        })
    return rows


def _pending_for(room_name, openings):
    """Openings that touch a room and cannot yet be deducted.

    Attribution is deliberately over-inclusive: a wall band lists every room along its length, so a 600 mm site on a
    14 m external wall is flagged against all four rooms that wall touches even though it stands in one of them.  An
    over-flag is the safe direction - it delays a quantity, it never inflates one.
    """
    return [o for o in openings if o["HEIGHT_M"] is None and room_name in o["ROOMS"]]


def q(qid, trade, item, value, unit, status, formula, rules, param_source, rooms=None, temp=False,
      residual=None, supersedes=None, note=None):
    """One recalculated quantity.  §V: the measured net quantity stands alone; waste and procurement stay empty."""
    return {
        "QUANTITY_ID": qid, "TRADE": trade, "BOQ_ITEM": item,
        "MEASURED_NET_QUANTITY": r4(value) if isinstance(value, float) else value, "UNIT": unit,
        "STATUS": status, "FORMULA": formula,
        "RULE_ID": rules, "PARAMETER_SOURCE": param_source,
        "USES_TEMPORARY_DEFAULT": temp,
        "TEMPORARY_DEFAULT_WARNING": ("TD-02 DEFAULT_DOOR_HEIGHT 2.20 m is a placeholder, not a source dimension.  Every "
                                      "figure it touches moves when a real door height arrives" if temp else None),
        "RESIDUAL_OPENINGS": residual or [],
        "ROOMS": rooms or [],
        "SUPERSEDES": supersedes,
        "WASTE_FACTOR": None,
        "PROCUREMENT_QUANTITY": None,
        "WASTE_WHY": "§V: no waste percentage has been given, so none is assumed and no procurement quantity exists",
        "NOTE": note,
    }


def quantities(rooms, walls_calc, openings, floors, summ, ceil):
    door_h = TEMPORARY_DEFAULTS[1][2]
    dry = [r for r in rooms if r["FINISH_CLASS"] == "DRY_ROOM"]
    cer = [r for r in rooms if r["FINISH_CLASS"] == "CERAMIC_SERVICE_ROOM"]
    bath = [r for r in cer if r["ROOM_NAME"] == "BATH"]
    serv = [r for r in cer if r["ROOM_NAME"] != "BATH"]

    apt_doors = [o for o in openings if o["TYPE"] == "DOOR" and o["INSIDE_APARTMENT"]]
    # A genuine orphan is a glazed element inside the apartment with NO host wall and NO host room.  An unresolved site
    # on a wall that touches no apartment room is not an orphan - it is simply outside the scope, and saying otherwise
    # would smear a stair-wall ambiguity across every apartment quantity.
    orphan = [o for o in openings if o["HEIGHT_M"] is None and not o["ROOMS"] and o["HOST_WALL_ID"] is None]
    orphan_res = [{"OPENING_ID": o["OPENING_ID"], "TYPE": o["TYPE"], "WIDTH_M": o["WIDTH_M"],
                   "HOST_WALL_THICKNESS_MM": o["HOST_WALL_THICKNESS_MM"],
                   "WHY": "no host wall and no host room were ever established for this glazed element, so no wall "
                          "area can deduct it even once a height arrives"}
                  for o in orphan]

    def res(rs):
        out, seen = [], set()
        for r in rs:
            for o in _pending_for(r["ROOM_NAME"], openings):
                if o["OPENING_ID"] in seen:
                    continue
                seen.add(o["OPENING_ID"])
                out.append({"OPENING_ID": o["OPENING_ID"], "TYPE": o["TYPE"], "WIDTH_M": o["WIDTH_M"],
                            "ROOMS": o["ROOMS"], "WHY": "no height established, and §G permits no default for this type"})
        return out

    def rev(ds):
        return sum(REVEAL_DEPTH * (2 * door_h + o["WIDTH_M"]) for o in ds)

    dry_dry = [o for o in apt_doors if not (set(o["ROOMS"]) & set(CERAMIC_ROOM_NAMES))]
    mixed = [o for o in apt_doors if set(o["ROOMS"]) & set(CERAMIC_ROOM_NAMES)]

    sk = sum(r["SKIRTING_LM"] for r in dry)
    wet_floor = summ["B_WET_INTERNAL_FLOOR_AREA_M2"]["VALUE"]
    serv_floor = r4(sum(f["METHOD_A_CAD_POLYGON_AREA_M2"] for f in floors
                        if f["ROOM"].split(" /")[0] in CERAMIC_ROOM_NAMES and f["WET_OR_DRY"] == "DRY"))
    dry_floor = r4(summ["A_DRY_INTERNAL_FLOOR_AREA_M2"]["VALUE"] - serv_floor)
    wet_perim = sum(r["GROSS_WALL_LINE_LM"] for r in bath)

    rows = []
    # ---- 1 and 2: the hidden system, one path, two items
    arith = " + ".join(f"{r['ROOM_NAME']} {r['SKIRTING_LM']:.3f}" for r in dry)
    for qid, item in (("Q-01", "HIDDEN_SKIRTING"), ("Q-02", "HIDDEN_PROFILE_ABOVE_SKIRTING")):
        rows.append(q(qid, "بروفايل" if qid == "Q-02" else "سيراميك", item, sk, "LM", "FINAL_QUANTITY_AVAILABLE",
                      f"gross wall line less door and glazed opening WIDTHS, dry rooms only: {arith} = {sk:.3f} lm",
                      ["US-02", "US-08", "QP-06", "QP-07", "QP-08"],
                      "floor-level boundary classification, frozen; no height and no wall-level opening enters a "
                      "linear quantity",
                      rooms=[r["ROOM_NAME"] for r in dry],
                      supersedes={"PREVIOUS": summ["D_TOTAL_SKIRTING_LM"]["VALUE"], "UNIT": "LM",
                                  "WHY": "PAINTRY leaves the skirting entirely under US-01/QP-07 (-11.150), and the "
                                         "column faces in HALL and DRESS join it because §E deducts openings and a "
                                         "column is not an opening (+1.550)"},
                      note="both items are FINAL because a skirting depends only on where wall meets floor, and that "
                           "classification is complete for every millimetre of every room boundary"))
    # ---- 3 and 4: waterproofing
    rows.append(q("Q-03", "عازل حمام+مطابخ", "WET_AREA_WATERPROOFING_FLOOR", wet_floor, "M2",
                  "FINAL_QUANTITY_AVAILABLE",
                  " + ".join(f"{f['ROOM']} {f['METHOD_A_CAD_POLYGON_AREA_M2']}" for f in floors
                             if f["WET_OR_DRY"] == "WET") + f" = {wet_floor} m2",
                  ["US-04"], "frozen floor polygons, unchanged", rooms=["BATH", "BATH", "BATH"]))
    rows.append(q("Q-04", "عازل حمام+مطابخ", "WET_AREA_WATERPROOFING_UPTURN", wet_perim, "LM",
                  "FINAL_QUANTITY_AVAILABLE",
                  "GROSS bathroom perimeter, doorways NOT deducted: "
                  + " + ".join(f"{r['ROOM_NAME']} {r['GROSS_WALL_LINE_LM']:.3f}" for r in bath)
                  + f" = {wet_perim:.3f} lm",
                  ["US-04", "US-05"], "frozen boundary segments, summed gross",
                  rooms=["BATH", "BATH", "BATH"],
                  supersedes={"PREVIOUS": summ["H_TOTAL_BATHROOM_HOST_WALL_LM"]["VALUE"], "UNIT": "LM",
                              "WHY": "the earlier figure was the door-deducted host-wall path.  US-05 forbids breaking "
                                     "the membrane at a threshold, so the 2.625 lm of doorway is restored"}))
    rows.append(q("Q-04R", "عازل حمام+مطابخ", "WET_AREA_UPTURN_VERTICAL_AREA_REFERENCE", wet_perim * UPTURN_HEIGHT,
                  "M2", "FINAL_QUANTITY_AVAILABLE",
                  f"{wet_perim:.3f} lm x {UPTURN_HEIGHT:.2f} m = {wet_perim * UPTURN_HEIGHT:.4f} m2",
                  ["US-04"], "derived from Q-04",
                  note="MATERIAL AND ENGINEERING REFERENCE ONLY.  The BOQ item is the linear metre in Q-04 and this "
                       "area must never be priced beside it"))
    # ---- 5: wall ceramic
    bath_gross = sum(r["GROSS_WALL_AREA_M2"] for r in bath)
    bath_ded = sum(r["DOOR_DEDUCTION_M2"] for r in bath)
    rows.append(q("Q-05", "سيراميك", "WALL_CERAMIC_BATHROOMS", bath_gross - bath_ded, "M2", "PARTIALLY_CALCULATED",
                  f"gross perimeter {sum(r['GROSS_WALL_LINE_LM'] for r in bath):.3f} lm x 3.00 m = {bath_gross:.4f} m2, "
                  f"less full door areas {bath_ded:.4f} m2 = {bath_gross - bath_ded:.4f} m2.  The gross path is used so "
                  f"the tiled strip above each door head is kept; no ceramic reveal is added (§L)",
                  ["US-01", "US-06", "QP-01", "TD-02"], "QP-01 height 3.00 m; TD-02 door height 2.20 m",
                  rooms=["BATH", "BATH", "BATH"], temp=True, residual=res(bath) + orphan_res))
    serv_gross = sum(r["GROSS_WALL_AREA_M2"] for r in serv)
    serv_ded = sum(r["DOOR_DEDUCTION_M2"] for r in serv)
    rows.append(q("Q-06", "سيراميك", "WALL_CERAMIC_SERVICE_ROOM", serv_gross - serv_ded, "M2", "PARTIALLY_CALCULATED",
                  f"PAINTRY gross perimeter {sum(r['GROSS_WALL_LINE_LM'] for r in serv):.3f} lm x 3.00 m "
                  f"= {serv_gross:.4f} m2, less full door areas {serv_ded:.4f} m2",
                  ["US-01", "QP-01", "QP-07"], "QP-01 height 3.00 m",
                  rooms=[r["ROOM_NAME"] for r in serv], residual=res(serv) + orphan_res,
                  note="the 2.750 m opening between HALL and PAINTRY is recorded on the HALL side of the frozen "
                       "boundary and as wall on the PAINTRY side.  It is carried here as a pending deduction on the "
                       "PAINTRY side too, because the wall register puts the opening in that wall"))
    # ---- 6: blockwork
    by_t = defaultdict(lambda: {"L": 0.0, "G": 0.0, "D": 0.0, "F": 0, "P": 0, "FIN": 0.0, "PEND": 0.0})
    for w in walls_calc:
        b = by_t[str(int(w["THICKNESS_MM"]))]
        b["L"] += w["LENGTH_M"]; b["G"] += w["GROSS_AREA_M2"]; b["D"] += w["OPENING_DEDUCTION_M2"]
        if w["STATUS"] == "FINAL_QUANTITY_AVAILABLE":
            b["F"] += 1; b["FIN"] += w["NET_AREA_M2"]
        else:
            b["P"] += 1; b["PEND"] += w["GROSS_AREA_M2"] - w["OPENING_DEDUCTION_M2"]
    for t in sorted(by_t, key=lambda k: -by_t[k]["L"]):
        b = by_t[t]
        # a glazed element sits in a wall of its own frame depth, so it can only move a thickness that matches it
        mine = [o for o in orphan_res if str(int(o["HOST_WALL_THICKNESS_MM"])) == t]
        rows.append(q(f"Q-07-{t}", "مبانى", f"BLOCKWORK_{t}", b["FIN"] + b["PEND"], "M2",
                      "FINAL_QUANTITY_AVAILABLE" if (b["P"] == 0 and not mine) else "PARTIALLY_CALCULATED",
                      f"{b['L']:.3f} m x 3.00 m = {b['G']:.4f} m2 gross, less {b['D']:.4f} m2 of full opening areas "
                      f"= {b['FIN'] + b['PEND']:.4f} m2",
                      ["US-06", "QP-02", "TD-02"], "QP-02 height 3.00 m; TD-02 door height 2.20 m",
                      temp=b["D"] > 0,
                      residual=([] if b["P"] == 0 else [{"WALLS_WITH_AN_UNHEIGHTED_OPENING": b["P"],
                                                         "AREA_STILL_MOVING_M2": r4(b["PEND"])}]) + mine,
                      supersedes={"PREVIOUS": None, "UNIT": "M2",
                                  "WHY": "no blockwork area existed before: the height was missing and the deduction "
                                         "column was undecided.  US-06 and QP-02 settle both"},
                      note=f"{b['F']} wall bands are fully resolved and {b['P']} still carry an opening with no height"))
    # ---- 7 and 8: plaster and paint, the same faces
    dry_gross = sum(r["GROSS_WALL_AREA_M2"] for r in dry)
    dry_ded = sum(r["DOOR_DEDUCTION_M2"] for r in dry)
    rev_dry, rev_mix = rev(dry_dry), rev(mixed)
    per_room = " + ".join(f"{r['ROOM_NAME']} {r['GROSS_WALL_AREA_M2']:.3f}" for r in dry)
    for qid, item, trade in (("Q-08", "INTERNAL_PLASTER", "مساح داخلى"), ("Q-09", "WALL_PAINT", "صبغ")):
        rows.append(q(qid, trade, item, dry_gross - dry_ded + rev_dry, "M2", "PARTIALLY_CALCULATED",
                      f"gross dry wall area {per_room} = {dry_gross:.4f} m2, less full door areas {dry_ded:.4f} m2, "
                      f"plus {len(dry_dry)} dry-to-dry door reveals at 0.25 x (2 x 2.20 + width) = {rev_dry:.4f} m2, "
                      f"giving {dry_gross - dry_ded + rev_dry:.4f} m2",
                      ["US-06", "US-07", "US-03", "QP-03" if qid == "Q-08" else "QP-04", "TD-02"],
                      f"{'QP-03' if qid == 'Q-08' else 'QP-04'} height 3.00 m; TD-02 door height 2.20 m; "
                      f"US-07 reveal depth 0.25 m",
                      rooms=[r["ROOM_NAME"] for r in dry], temp=True, residual=res(dry) + orphan_res,
                      supersedes={"PREVIOUS": None, "UNIT": "M2",
                                  "WHY": "no area existed before: the height was missing and the deduction rule was "
                                         "the contractor's half-opening convention, which US-06 replaces"},
                      note=f"plaster and paint cover the same dry faces, so the two figures are equal by construction "
                           f"and not by coincidence.  A further {rev_mix:.4f} m2 of reveal belongs to the {len(mixed)} "
                           f"doors that open into a ceramic room; whether that reveal is plastered or tiled is a "
                           f"finishes detail and it is held out of both figures"))
    rows.append(q("Q-10", "مساح داخلى", "TILE_PREPARATION_TARTUSHA",
                  sum(r["GROSS_WALL_AREA_M2"] for r in cer) - sum(r["DOOR_DEDUCTION_M2"] for r in cer), "M2",
                  "PARTIALLY_CALCULATED",
                  f"ceramic-room gross wall area {sum(r['GROSS_WALL_AREA_M2'] for r in cer):.4f} m2 less full door "
                  f"areas {sum(r['DOOR_DEDUCTION_M2'] for r in cer):.4f} m2",
                  ["US-03", "US-01", "QP-03", "TD-02"], "QP-03 height 3.00 m; TD-02 door height 2.20 m",
                  rooms=[r["ROOM_NAME"] for r in cer], temp=True, residual=res(cer) + orphan_res,
                  note="US-03: normal plaster is not the ceramic backing.  These faces leave the plaster item and "
                       "become the tile preparation item; no reveal is added, because US-07 is written for plaster "
                       "and paint"))
    # ---- floors
    rows.append(q("Q-11", "سيراميك", "FLOOR_CERAMIC_WET_ROOMS", wet_floor, "M2", "FINAL_QUANTITY_AVAILABLE",
                  f"the three bathroom floor polygons, unchanged = {wet_floor} m2",
                  ["US-01", "M"], "frozen floor polygons", rooms=["BATH", "BATH", "BATH"]))
    rows.append(q("Q-12", "سيراميك", "FLOOR_CERAMIC_SERVICE_ROOM", serv_floor, "M2", "FINAL_QUANTITY_AVAILABLE",
                  f"the PAINTRY floor polygon, unchanged = {serv_floor} m2",
                  ["US-01", "QP-07", "M"], "frozen floor polygons", rooms=[r["ROOM_NAME"] for r in serv],
                  supersedes={"PREVIOUS": None, "UNIT": "M2",
                              "WHY": "this area sat inside the undifferentiated dry floor total, waiting on a finishes "
                                     "schedule.  QP-07 gives it a finish"}))
    rows.append(q("Q-13", "سيراميك", "FLOOR_FINISH_DRY_ROOMS", dry_floor, "M2", "SPEC_REQUIRED",
                  f"dry internal floor {summ['A_DRY_INTERNAL_FLOOR_AREA_M2']['VALUE']} m2 less the PAINTRY "
                  f"{serv_floor} m2 now carried as ceramic = {dry_floor} m2",
                  ["M"], "frozen floor polygons",
                  note="§M keeps dry and wet apart until the finish scope is known.  Which dry rooms take ceramic is "
                       "still a finishes schedule question and no rule above answers it"))
    # ---- 9: ceiling paint
    rows.append(q("Q-14", "صبغ", "CEILING_PAINT", None, "M2", "SOURCE_REQUIRED",
                  f"{ceil} m2 of flat ceiling geometry exists, but no rule above establishes a ceiling paint scope",
                  [], "none",
                  note="the house precedent R-10 prices paint to the DECOR ceiling and no flat ceiling paint at all.  "
                       "Without a ceiling design there is no decor area, so this stays a drawing question rather than "
                       "a quantity.  It is named so the absence is visible"))
    return rows


def answered_questions():
    """§R: a question the owner has answered is closed, and closed questions are listed so they are not re-asked."""
    return [
        ("D-01", "the clear wall height for blockwork", "QP-02 = 3.00 m"),
        ("D-02", "the internal plaster height", "QP-03 = 3.00 m"),
        ("D-03", "the bathroom and preparation tiling height", "QP-01 = 3.00 m"),
        ("D-04", "the wall height for paint", "QP-04 = 3.00 m"),
        ("D-06", "the render band height behind the skirting", "QP-05 = NOT_APPLICABLE"),
        ("D-07", "whether the profile shares the skirting's payable path", "US-08 = yes, one path, two items"),
        ("D-08", "whether the skirting takes a deduction", "US-02 + §E = opening WIDTHS only, no cabinet deduction"),
        ("D-09", "whether the membrane upturn is broken at a doorway", "US-05 = no, the gross perimeter is used"),
        ("D-10", "the blockwork deduction column, full or half", "US-06 = full opening area"),
        ("D-11", "whether Qortuba inherits the plaster half deduction", "US-06 = no, full opening area"),
        ("D-12", "whether Qortuba inherits the paint half deduction", "US-06 = no, full opening area"),
    ]


STILL_OPEN = [
    ("O-01", "PROJECT_INPUT", "the door, window and glazed opening HEIGHTS",
     "TD-02 covers normal doors as a temporary default only.  §G forbids a default for windows, sliding doors and "
     "glazed panels, so seven glazed elements and ten unclassified sites still carry no height",
     "every wall-area trade"),
    ("O-02", "DRAWING_REQUIRED", "which room each of the six unattributed windows stands in",
     "the six windows have measured widths and no host room, so no room's wall area can deduct them even after a "
     "height arrives",
     "wall ceramic, plaster, paint, blockwork"),
    ("O-03", "PROJECT_RULE", "whether the PAINTRY takes waterproofing as well as ceramic",
     "the owner's PAINTRY instruction is scoped to the ceramic takeoff.  US-01 lists kitchens among the wet service "
     "rooms, so the floor membrane may follow; the quantities are measured and waiting on one word",
     "PAINTRY floor membrane 11.6825 m2 and upturn 11.150 lm"),
    ("O-04", "DRAWING_REQUIRED", "the ceiling paint scope",
     "the house prices paint to the decor ceiling only, and no ceiling design exists",
     "ceiling paint"),
    ("O-05", "PROJECT_RULE", "whether the 2م=1م halving of corners and wall ends applies",
     "unchanged from before and still unasked-for: Qortuba has not cut its boundary into corners and ends, so the "
     "answer releases nothing yet",
     "plaster corners and ends"),
]


def finish():
    ver = verify_inputs()
    skirt = reg(QS, "QORTUBA_QS01_SKIRTING_TAKEOFF")["ROWS"]
    walls = reg(QS, "QORTUBA_QS01_BLOCK_WALL_TAKEOFF")
    blue = reg(QS, "QORTUBA_QS01_BLUE_ELEMENT_SCHEDULE")["ROWS"]
    floors = reg(QS, "QORTUBA_QS01_FLOOR_CALCULATIONS")["ROWS"]
    summ = reg(QS, "QORTUBA_QS01_SUMMARY_TOTALS")
    ceil = summ["F_TOTAL_CEILING_GEOMETRY_M2"]["VALUE"]

    ops = opening_register(walls, blue)
    rooms = room_rows(skirt, ops)
    wcalc = wall_rows(walls, ops)
    qs = quantities(rooms, wcalc, ops, floors, summ, ceil)

    store = {
        "ARTIFACT": "URBAN_OWNER_RULES_V1",
        "PRIORITY": [{"RANK": r, "LEVEL": l, "MEANING": m} for r, l, m in PRIORITY],
        "WHERE_HISTORICAL_PRECEDENT_SITS": HISTORICAL_POSITION,
        "URBAN_STANDARDS": [{"RULE_ID": i, "TITLE": t, "STATEMENT": s, "OWNER_SECTION": sec,
                             "RULE_LEVEL": "URBAN_STANDARD", "APPLIES_AUTOMATICALLY_BELOW_DRAWINGS": True,
                             "SUPERSEDES": sup} for i, t, s, sec, sup in URBAN_STANDARDS],
        "QORTUBA_PROJECT_RULES": [{"RULE_ID": i, "PARAMETER": p, "VALUE": v, "UNIT": u, "OWNER_SECTION": sec,
                                   "RULE_LEVEL": "QORTUBA_PROJECT_RULE", "APPLIES_TO_OTHER_PROJECTS": False,
                                   "WHY": w} for i, p, v, u, sec, w in QORTUBA_PROJECT_RULES],
        "TEMPORARY_DEFAULTS": [{"RULE_ID": i, "PARAMETER": p, "VALUE": v, "UNIT": u, "OWNER_SECTION": sec,
                                "RULE_LEVEL": "APPROVED_TEMPORARY_DEFAULT", "IS_SOURCE_TRUTH": False,
                                "WHY": w} for i, p, v, u, sec, w in TEMPORARY_DEFAULTS],
        "NO_DEFAULT_PERMITTED_FOR": list(NO_DEFAULT_FOR),
        "SUPERSEDED_HISTORICAL_RULES": [{"RULE_ID": i, "TRADE": t, "WHAT": w, "SUPERSEDED_BY": by,
                                         "NEW_FILE_STATUS": "CONTRACTOR_SPECIFIC_REFERENCE_ONLY", "WHY": why}
                                        for i, t, w, by, why in SUPERSEDED],
        "COMMERCIAL_RATE_RULES": [{"RULE_ID": "US-09", "RULE": "NORMAL_SKIRTING_UNIT_RATE = 0.50 x "
                                                              "HIDDEN_SKIRTING_UNIT_RATE",
                                   "FACTOR": NORMAL_SKIRTING_RATE_FACTOR, "CHANGES_QUANTITY": False,
                                   "OVERRIDDEN_BY": "any explicit project rate"},
                                  {"RULE_ID": "US-08", "RULE": "HIDDEN_PROFILE_UNIT_RATE = HIDDEN_SKIRTING_UNIT_RATE",
                                   "FACTOR": 1.0, "CHANGES_QUANTITY": False,
                                   "AMOUNTS_MERGED": False}],
        "DEPENDENCY_GRAPH": DEPENDENCIES,
        "STAGES_NEVER_RERUN_BY_A_RULE_CHANGE": NEVER_RERUN,
        "COUNTS": {"URBAN_STANDARD": len(URBAN_STANDARDS), "QORTUBA_PROJECT_RULE": len(QORTUBA_PROJECT_RULES),
                   "APPROVED_TEMPORARY_DEFAULT": len(TEMPORARY_DEFAULTS), "SUPERSEDED": len(SUPERSEDED)},
    }

    opening = {
        "ARTIFACT": "QORTUBA_OPENING_REGISTER",
        "RULE": "§P: every opening carries an id, a type, a width, a height, a source and a status.  An UNKNOWN type "
                "never enters a final quantity, because the trade rule needs the type to know whether a default applies",
        "TYPES": list(OPENING_TYPES),
        "ROWS": ops, "COUNT": len(ops),
        "BY_TYPE": {t: sum(1 for o in ops if o["TYPE"] == t) for t in OPENING_TYPES},
        "WITH_A_USABLE_HEIGHT": sum(1 for o in ops if o["HEIGHT_M"] is not None),
        "WITHOUT_A_HEIGHT": sum(1 for o in ops if o["HEIGHT_M"] is None),
        "WITHOUT_A_HOST_ROOM": [o["OPENING_ID"] for o in ops if not o["ROOMS"] and o["INSIDE_APARTMENT"]],
        "TYPE_CONFLICTS": [{"OPENING_ID": o["OPENING_ID"], "WHY": o["TYPE_CONFLICT"]} for o in ops
                           if o["TYPE_CONFLICT"]],
        "WIDTHS_ARE_SOURCE_ESTABLISHED": True,
        "HEIGHTS_IN_THE_DRAWING_SET": 0,
    }

    room_art = {"ARTIFACT": "QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC",
                "RULE": "one row per interior room, rebuilt from its frozen boundary segments and nothing else",
                "ROWS": rooms, "COUNT": len(rooms),
                "CERAMIC_SERVICE_ROOMS": [r["ROOM_NAME"] for r in rooms
                                          if r["FINISH_CLASS"] == "CERAMIC_SERVICE_ROOM"],
                "ROOMS_THAT_CHANGED_CLASS": [{"ROOM": r["ROOM_NAME"], "WAS": "DRY", "NOW": r["FINISH_CLASS"],
                                              "RULE": r["FINISH_RULE"]} for r in rooms
                                             if r["FINISH_CLASS"] == "CERAMIC_SERVICE_ROOM"
                                             and not r["WAS_WET_IN_WORKPAPER"]],
                "GEOMETRY_RECOMPUTED": 0}

    wall_art = {"ARTIFACT": "QORTUBA_BLOCKWORK_RECALC", "ROWS": wcalc, "COUNT": len(wcalc),
                "HEIGHT_M": 3.00, "HEIGHT_RULE": "QP-02",
                "POPULATION": "all 41 wall bands the frozen takeoff records, unchanged.  Some of them bound the stair "
                              "and the common circulation rather than the apartment; splitting that population is a "
                              "scope decision no rule above makes, so it is named here instead of taken",
                "WALLS_TOUCHING_NO_APARTMENT_ROOM": sum(1 for w in wcalc if not w["ROOMS"]),
                "WALLS_FINAL": sum(1 for w in wcalc if w["STATUS"] == "FINAL_QUANTITY_AVAILABLE"),
                "WALLS_PARTIAL": sum(1 for w in wcalc if w["STATUS"] == "PARTIALLY_CALCULATED"),
                "GEOMETRY_RECOMPUTED": 0}

    final = [x for x in qs if x["STATUS"] == "FINAL_QUANTITY_AVAILABLE"]
    partial = [x for x in qs if x["STATUS"] == "PARTIALLY_CALCULATED"]
    blocked = [x for x in qs if x["STATUS"] in ("SOURCE_REQUIRED", "SPEC_REQUIRED")]
    quant = {
        "ARTIFACT": "QORTUBA_RECALCULATED_QUANTITIES_V1",
        "RULE": "every figure below is arithmetic over the FROZEN measurement registers.  No geometry was re-read, no "
                "room re-measured and no opening re-detected",
        "ROWS": qs, "COUNT": len(qs),
        "BY_STATUS": {k: sum(1 for x in qs if x["STATUS"] == k) for k in
                      ("FINAL_QUANTITY_AVAILABLE", "PARTIALLY_CALCULATED", "SPEC_REQUIRED", "SOURCE_REQUIRED")},
        "FINAL": [{"QUANTITY_ID": x["QUANTITY_ID"], "BOQ_ITEM": x["BOQ_ITEM"],
                   "VALUE": x["MEASURED_NET_QUANTITY"], "UNIT": x["UNIT"]} for x in final],
        "PARTIAL": [{"QUANTITY_ID": x["QUANTITY_ID"], "BOQ_ITEM": x["BOQ_ITEM"],
                     "VALUE_SO_FAR": x["MEASURED_NET_QUANTITY"], "UNIT": x["UNIT"],
                     "OPENINGS_STILL_PENDING": len(x["RESIDUAL_OPENINGS"])} for x in partial],
        "BLOCKED": [{"QUANTITY_ID": x["QUANTITY_ID"], "BOQ_ITEM": x["BOQ_ITEM"], "WHY": x["NOTE"]} for x in blocked],
        "QUANTITIES_USING_A_TEMPORARY_DEFAULT": [x["QUANTITY_ID"] for x in qs if x["USES_TEMPORARY_DEFAULT"]],
        "WASTE_APPLIED_ANYWHERE": False,
        "RATES_SUPPLIED": 0,
        "GEOMETRY_STAGES_RERUN": 0,
    }

    quest = {"ARTIFACT": "QORTUBA_QUESTION_LEDGER",
             "RULE": "§R: an answered question is closed and is never asked again unless a new project overrides it, a "
                     "drawing conflicts with it, or the owner changes the standard",
             "CLOSED": [{"DECISION_ID": d, "QUESTION": qq, "ANSWERED_BY": a} for d, qq, a in answered_questions()],
             "CLOSED_COUNT": len(answered_questions()),
             "STILL_OPEN": [{"ID": i, "KIND": k, "QUESTION": qq, "WHY": w, "BLOCKS": b}
                            for i, k, qq, w, b in STILL_OPEN],
             "STILL_OPEN_COUNT": len(STILL_OPEN)}

    written = [write(o["ARTIFACT"], o) for o in (store, opening, room_art, wall_art, quant, quest)]
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip().splitlines()
    fr = {"ARTIFACT": "FREEZE_URBAN_OWNER_RULES_V1",
          "INPUT_FREEZES_VERIFIED": ver,
          "QORTUBA_GEOMETRY_CHANGED": "NONE",
          "GEOMETRY_STAGES_RERUN": 0,
          "NEW_TAKEOFF_PHASES_CREATED": 0,
          "HISTORICAL_BOQ_REINTERPRETED": False,
          "WASTE_APPLIED": False,
          "GIT_HEAD_AT_FREEZE": head,
          "WORKING_TREE_AT_FREEZE": {"CLEAN": not dirty, "UNCOMMITTED_PATHS": [l[3:] for l in dirty][:20]},
          "CONTENTS": {n: _sha(OUT / f"{n}.json") for n in written},
          "COUNT": len(written)}
    fr["DIGEST"] = hashlib.sha256(json.dumps({k: v for k, v in fr.items() if k != "DIGEST"},
                                             sort_keys=True, default=str).encode()).hexdigest()
    write("FREEZE_URBAN_OWNER_RULES_V1", fr)
    return {"RULES": store, "OPENINGS": opening, "ROOMS": room_art, "WALLS": wall_art, "QUANTITIES": quant,
            "QUESTIONS": quest, "FREEZE": fr}


if __name__ == "__main__":
    o = finish()
    print("FREEZE", o["FREEZE"]["DIGEST"][:16])
    print("rules:", o["RULES"]["COUNTS"])
    print("openings:", o["OPENINGS"]["BY_TYPE"], "| with a height:", o["OPENINGS"]["WITH_A_USABLE_HEIGHT"],
          "| no host room:", len(o["OPENINGS"]["WITHOUT_A_HOST_ROOM"]))
    print("quantities:", o["QUANTITIES"]["BY_STATUS"])
    print()
    print("FINAL:")
    for x in o["QUANTITIES"]["FINAL"]:
        print(f"   {x['QUANTITY_ID']:8s} {x['BOQ_ITEM']:38s} {x['VALUE']:>10} {x['UNIT']}")
    print()
    print("PARTIAL:")
    for x in o["QUANTITIES"]["PARTIAL"]:
        print(f"   {x['QUANTITY_ID']:8s} {x['BOQ_ITEM']:38s} {x['VALUE_SO_FAR']:>10} {x['UNIT']}  "
              f"pending {x['OPENINGS_STILL_PENDING']}")
    print()
    print("BLOCKED:", [x["QUANTITY_ID"] for x in o["QUANTITIES"]["BLOCKED"]])
    print("closed questions:", o["QUESTIONS"]["CLOSED_COUNT"], "| still open:", o["QUESTIONS"]["STILL_OPEN_COUNT"])
