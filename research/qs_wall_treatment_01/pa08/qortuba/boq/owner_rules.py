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
from collections import Counter, defaultdict
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.boq import material_identity as MI, opening_source_search as OS

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
    ("US-11", "THERE_IS_NO_DEFAULT_WINDOW_HEIGHT",
     "a window, sliding door or glazed opening whose height is absent from the source is OWNER_INPUT_REQUIRED.  No "
     "figure is assumed for it - not 1.50 m, not 1.20 m, not anything - and the owner is asked",
     "V2 §1", []),
    ("US-12", "ASK_IN_WORDS_A_PERSON_CAN_ACT_ON",
     "an owner is never asked about an internal identifier.  Every question names the room, the opening type, the "
     "width and what the opening joins; where that is still ambiguous a numbered plan crop is produced.  The opaque "
     "id stays in the audit column",
     "V2 §1, §8, §9", []),
    ("US-13", "INTERIOR_DOORS_ARE_PVC_EXTERIOR_OPENINGS_ARE_ALUMINIUM",
     "interior doors - bedrooms, bathrooms, internal service rooms and any other internal door - are PVC and are "
     "billed as their own schedule.  Aluminium carries exterior doors, windows and exterior sliding systems only, and "
     "internal door area is never called an aluminium quantity",
     "V2 §3", ["the single aluminium doors row of OWNER RULES V1"]),
    ("US-14", "WATERPROOFING_ROOM_TYPES_ARE_ENUMERATED",
     "bathroom, WC, shower, kitchen, pantry / preparation kitchen, iron room, washing room and laundry all receive "
     "waterproofing: a floor membrane by area and an upturn of 0.15 m along the GROSS room perimeter, doorways not "
     "deducted, unless a project specification explicitly overrides it",
     "V2 §4", ["US-04 and US-05 are widened, not replaced: the method is unchanged and the room list is now explicit"]),
    ("US-15", "A_CEILING_IS_PRICED_BY_AREA_UNTIL_A_CEILING_DRAWING_EXISTS",
     "the ceiling is one priced line in m2 over the established ceiling plan area.  Cornice, cove lighting, bulkheads, "
     "shadow gaps, decorative perimeters and gypsum feature lengths are NOT_ESTABLISHED and are never inferred from a "
     "room perimeter",
     "V2 §7", ["R-23 and R-24 as PAYABLE items: the historical cornice run is precedent, not a Qortuba quantity"]),
    ("US-16", "AN_OPEN_PASSAGE_IS_AN_OPENING_WITH_NOTHING_IN_IT",
     "OPEN_PASSAGE is a physical opening type: a real interruption in the wall with no door leaf or system in it.  It "
     "is not PVC, it is not aluminium, and it never appears in a door or window procurement schedule or door count.  "
     "It does interrupt blockwork, plaster, paint, wall ceramic, skirting and the hidden profile, according to its "
     "dimensions and the finishes on each side",
     "OPEN-PASSAGE RULE CORRECTION", []),
    ("US-17", "AN_OPEN_PASSAGE_HAS_NO_ASSUMED_HEIGHT",
     "an open passage is either OPEN_PASSAGE_FULL_HEIGHT, where its height IS the applicable wall height and no top "
     "reveal exists, or OPEN_PASSAGE_WITH_HEAD, where the owner supplies the opening height and left, right and top "
     "reveals all apply under US-07.  Until the owner states which, HEIGHT_STATUS is OWNER_INPUT_REQUIRED: the door "
     "default TD-02 never reaches it, and the width deduction from the linear path proceeds without waiting",
     "OPEN-PASSAGE RULE CORRECTION", ["TD-02 is explicitly barred from open passages"]),
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
    ("QP-09", "QORTUBA_SKIRTING_WINDOW_DEDUCTION", "DEDUCT_EVERY_WINDOW_WIDTH", None, "owner confirmation",
     "the owner has read the two figures and chosen: the clear WIDTH of every door, sliding door and window comes off "
     "the hidden skirting and hidden profile path, whether or not wall stands below the opening.  The question is "
     "closed and is not asked again"),
    ("QP-10", "QORTUBA_HIDDEN_SKIRTING_PATH", 81.789, "LM", "owner confirmation + OPEN-PASSAGE RULE CORRECTION",
     "the payable hidden skirting path, fixed by the owner under QP-09 and corrected under QP-17: the two open "
     "passages interrupt the path and their clear widths come off it, which 86.589 lm did not do"),
    ("QP-11", "QORTUBA_HIDDEN_PROFILE_PATH", 81.789, "LM", "owner confirmation + OPEN-PASSAGE RULE CORRECTION",
     "the payable hidden profile path: the same path as QP-10, issued as a separate BOQ item under US-08"),
    ("QP-17", "QORTUBA_OPEN_PASSAGES", "2 x 1.200 m", "M", "OPEN-PASSAGE RULE CORRECTION",
     "the owner has identified two of the five unresolved gaps as open passages: the 1.200 m gap between the Hall and "
     "the Lobby, and the 1.200 m gap between the Master bedroom and the Dressing room.  Each interrupts the skirting "
     "and hidden profile path of BOTH rooms it joins, so 4 x 1.200 = 4.800 lm leaves the path; each carries no "
     "height and no procurement line"),
    ("QP-18", "QORTUBA_OPEN_PASSAGE_VERTICAL_CONDITION", "ANSWERED", None, "QS WORKFLOW V1 §A",
     "the owner has given both: the Hall / Lobby passage is OPEN_PASSAGE_FULL_HEIGHT at the 3.000 m wall height, with "
     "left and right reveals and no top; the Master bedroom / Dressing room passage is OPEN_PASSAGE_WITH_HEAD at "
     "2.200 m, with left, right and top reveals"),
    ("QP-19", "QORTUBA_OPEN_PASSAGE_WITH_HEAD_HEIGHT", 2.200, "M", "QS WORKFLOW V1 §A",
     "an EXPLICIT QORTUBA OWNER INPUT for the Master bedroom / Dressing room passage, rank 2 on the priority ladder.  "
     "It is not TD-02: the two figures coincide, and a coincidence is not a provenance.  If TD-02 ever moves, this "
     "does not"),
    ("QP-20", "QORTUBA_OPENING_ROOM_ATTRIBUTION", "THE_TWO_ROOMS_IT_JOINS", None, "QS WORKFLOW V1 §B",
     "where the two rooms an opening actually joins are established, that pair - not the host band's full room list - "
     "decides which trade quantity waits on it.  A dry-room opening does not block bathroom ceramic, pantry ceramic "
     "or tile preparation unless frozen geometry puts it in one of those faces"),
    ("QP-12", "QORTUBA_HALL_PANTRY_GLAZED_OPENING_HEIGHT", 2.200, "M", "V2 §2",
     "the owner has given the height of the glazed opening between the Hall and the Pantry.  This is a real dimension "
     "under an owner override, not a default, so 2.750 x 2.200 = 6.050 m2 is deducted from every dependent wall area"),
    ("QP-13", "QORTUBA_PANTRY_WATERPROOFING", "APPLIES", None, "V2 §4",
     "the Pantry receives waterproofing under US-14: a floor membrane over its measured area and an upturn along its "
     "GROSS perimeter, which is not the skirting path"),
    ("QP-14", "QORTUBA_DRY_FLOOR_FINISH", "PORCELAIN", None, "V2 §6",
     "the dry internal floor finish is porcelain, which releases the dry floor area that was waiting on a schedule"),
    ("QP-15", "QORTUBA_CEILING_BASIS", "AREA_ONLY", "M2", "V2 §7",
     "the ceiling is priced by area alone for this project; no decor length is carried"),
    ("QP-16", "QORTUBA_INTERIOR_DOORS", "PVC", None, "V2 §3",
     "all seven Qortuba apartment doors are interior - each is seen from two apartment rooms on the frozen floor-level "
     "boundary - so all seven are PVC and none belongs to the aluminium package"),
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


def opening_register_from_source():
    """The completed register: type and height as the exhaustive source search established them."""
    out = []
    for r in OS.finish_register()["ROWS"]:
        out.append({
            "OPENING_ID": r["OPENING_ID"], "TYPE": r["TYPE"],
            "WIDTH_M": r["WIDTH_M"], "WIDTH_SOURCE": r["WIDTH_SOURCE"],
            "HEIGHT_M": r["HEIGHT_M"], "HEIGHT_SOURCE": r["HEIGHT_SOURCE"],
            "HEIGHT_STATE": ("TEMPORARY_OWNER_DEFAULT" if r["HEIGHT_M"] is not None else "NOT_ESTABLISHED"),
            "SOURCE": "QORTUBA_OPENING_REGISTER_COMPLETED",
            "STATUS": r["STATUS"],
            "HOST_WALL_ID": r["HOST_WALL_ID"], "HOST_WALL_THICKNESS_MM": r["HOST_WALL_THICKNESS_MM"],
            "ROOMS": ([x.strip() for x in r["ROOM"].split(",")] if r["ROOM"] else []),
            "ROOM_ID": r["ROOM_ID"],
            "OPEN_PASSAGE_SUBTYPE": r["OPEN_PASSAGE_SUBTYPE"], "REVEAL_SIDES": r["REVEAL_SIDES"],
            "INSIDE_APARTMENT": bool(r["ROOM"]),
            "IS_AN_OPENING_THROUGH_THE_WALL": r["IS_AN_OPENING_THROUGH_THE_WALL"],
            "INTERRUPTS_AT_FLOOR_LEVEL": r["INTERRUPTS_AT_FLOOR_LEVEL"],
            "BLUE_ELEMENT_ID": r["BLUE_ELEMENT_ID"], "SITE_CLASS": r["SITE_CLASS"], "TYPE_CONFLICT": None,
            "NOTE": " | ".join(x for x in (r["EVIDENCE"], r["WHY_NOT_AN_OPENING"], r["PDF_READER"]) if x),
        })
    return out


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
def room_rows(skirt, openings, glazed=None, human=None):
    """One row per interior room, built only from its frozen boundary segments."""
    door_h = TEMPORARY_DEFAULTS[1][2]
    # every opening that has a height, charged to the rooms that actually lose wall area to it
    ded = defaultdict(list)
    for h in (human or []):
        if h["HEIGHT_M"] is None or not h["IS_AN_OPENING_THROUGH_THE_WALL"]:
            continue
        for rid in h["ROOM_IDS_FOR_DEDUCTION"]:
            ded[rid].append(h)
    # OPEN-PASSAGE RULE CORRECTION: an open passage interrupts the skirting and the hidden profile exactly as a
    # doorway does, so its CLEAR WIDTH leaves the linear path.  This deduction needs no height and does not wait for
    # one.  The frozen boundary traced these two gaps as continuous wall face, so the width was never taken out.
    passage = defaultdict(list)
    for h in (human or []):
        if h["TYPE"] == "OPEN_PASSAGE" and h["IS_AN_OPENING_THROUGH_THE_WALL"]:
            for rid in h["ROOM_IDS_FOR_DEDUCTION"]:
                passage[rid].append(h)
    by_room = defaultdict(list)
    for g in (glazed or []):
        if g.get("ROOM_ID") and g["WALL_BELOW"]:
            by_room[g["ROOM_ID"]].append(g)
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
        pas = passage.get(x["ROOM_ID"], [])
        pas_w = sum(p["WIDTH_M"] for p in pas)
        skirting = 0.0 if ceramic else max(gross - sum(doors) - sum(glaz) - pas_w, 0.0)
        # §1 of the audit: glazed elements that stand in this room with wall BELOW them.  They do not interrupt the
        # boundary path, so they are not deducted here - and they are carried so the alternative reading is computable.
        sills = by_room.get(x["ROOM_ID"], [])
        sill_w = sum(g["WIDTH_M"] for g in sills)
        skirting_all = 0.0 if ceramic else max(skirting - sill_w, 0.0)
        rows.append({
            "ROOM_ID": x["ROOM_ID"], "ROOM": x["ROOM"], "ROOM_NAME": name,
            "FINISH_CLASS": "CERAMIC_SERVICE_ROOM" if ceramic else "DRY_ROOM",
            "FINISH_RULE": "US-01 + QP-07" if ceramic else "no ceramic rule applies",
            "WAS_WET_IN_WORKPAPER": x["WET_OR_DRY"] == "WET",
            "GROSS_WALL_LINE_LM": r3(gross), "WALL_FACE_LM": r3(face), "COLUMN_FACE_LM": r3(col),
            "DOOR_OPENING_LM": r3(sum(doors)), "GLAZED_OPENING_LM": r3(sum(glaz)),
            "OPEN_PASSAGE_LM": r3(pas_w),
            "OPEN_PASSAGES_DEDUCTED": [{"OPENING_ID": p["OPENING_ID"], "DESCRIPTION": p["DESCRIPTION"],
                                        "WIDTH_M": p["WIDTH_M"]} for p in pas],
            "DOOR_WIDTHS_M": [r3(d) for d in sorted(doors, reverse=True)],
            "GLAZED_WIDTHS_M": [r3(g) for g in sorted(glaz, reverse=True)],
            "SKIRTING_LM": r3(skirting),
            "HIDDEN_PROFILE_LM": r3(skirting),
            "WINDOW_WITH_WALL_BELOW_IDS": [g["BLUE_ELEMENT_ID"] for g in sills],
            "WINDOW_WITH_WALL_BELOW_WIDTH_LM": r3(sill_w),
            "SKIRTING_LM_IF_ALL_WINDOW_WIDTHS_DEDUCTED": r3(skirting_all),
            "HIDDEN_PROFILE_LM_IF_ALL_WINDOW_WIDTHS_DEDUCTED": r3(skirting_all),
            "GROSS_WALL_AREA_M2": r4(gross * 3.0),
            "DOOR_DEDUCTION_M2": r4(sum(d * door_h for d in doors)),
            "OPENING_DEDUCTION_M2": r4(sum(h["WIDTH_M"] * h["HEIGHT_M"] for h in ded.get(x["ROOM_ID"], []))),
            "OPENINGS_DEDUCTED": [{"OPENING_ID": h["OPENING_ID"], "DESCRIPTION": h["DESCRIPTION"],
                                   "W": h["WIDTH_M"], "H": h["HEIGHT_M"],
                                   "AREA_M2": r4(h["WIDTH_M"] * h["HEIGHT_M"])} for h in ded.get(x["ROOM_ID"], [])],
            "GLAZED_DEDUCTION_M2": None if glaz else 0.0,
            "GLAZED_PENDING_WIDTH_M": r3(sum(glaz)) or None,
            "SKIRTING_ARITHMETIC": (f"{gross:.3f} gross wall line - {sum(doors):.3f} doors - {sum(glaz):.3f} glazed"
                                    + (f" - {pas_w:.3f} open passage" if pas_w else "")
                                    + f" = {skirting:.3f} lm" if not ceramic else
                                    "0.000 lm: US-02, the wall ceramic reaches the floor ceramic"),
        })
    return rows


def wall_rows(walls, openings, identity=None):
    """Blockwork, one row per wall band - but only where the band is a masonry wall.

    A column, a stair shaft and a drafting arrow all report a thickness.  None of them is blockwork, so none of them
    produces an area here; they are carried as geometric reference so the exclusion is visible rather than silent.
    """
    H = 3.00
    ident = {r["WALL_ID"]: r for r in (identity if identity is not None else MI.wall_identity())}
    by_wall = defaultdict(list)
    for o in openings:
        if o["HOST_WALL_ID"]:
            by_wall[o["HOST_WALL_ID"]].append(o)
    rows = []
    for w in walls["ROWS"]:
        idr = ident[w["WALL_ID"]]
        ops = by_wall.get(w["WALL_ID"], [])
        usable = [o for o in ops if o["HEIGHT_M"] is not None]
        pending = [o for o in ops if o["HEIGHT_M"] is None]
        masonry = idr["BLOCKWORK_CONFIRMED"]
        gross = w["LENGTH_M"] * H if masonry else 0.0
        ded = sum(o["WIDTH_M"] * o["HEIGHT_M"] for o in usable) if masonry else 0.0
        rows.append({
            "WALL_ID": w["WALL_ID"], "THICKNESS_MM": w["THICKNESS_MM"], "LENGTH_M": w["LENGTH_M"],
            "ROOMS": sorted({r for r in w["ROOM_SIDE_A"] + w["ROOM_SIDE_B"] if r in APARTMENT_ROOMS}),
            "PHYSICAL_OBJECT_CLASS": idr["PHYSICAL_OBJECT_CLASS"],
            "BLOCKWORK_CONFIRMED": masonry,
            "THICKNESS_ITEM_ESTABLISHED": idr["THICKNESS_ITEM_ESTABLISHED"],
            "IDENTITY_EVIDENCE": idr["EVIDENCE"],
            "HEIGHT_M": H if masonry else None, "HEIGHT_RULE": "QP-02" if masonry else None,
            "GROSS_AREA_M2": (r4(gross) if masonry else None),
            "OPENING_DEDUCTION_M2": (r4(ded) if masonry else None),
            "NET_AREA_M2": (None if (pending or not masonry) else r4(gross - ded)),
            "OPENINGS_DEDUCTED": [{"OPENING_ID": o["OPENING_ID"], "TYPE": o["TYPE"], "W": o["WIDTH_M"],
                                   "H": o["HEIGHT_M"]} for o in usable],
            "OPENINGS_PENDING": [{"OPENING_ID": o["OPENING_ID"], "TYPE": o["TYPE"], "W": o["WIDTH_M"],
                                  "WHY": "no height, and no default is permitted for this type"} for o in pending],
            "STATUS": ("GEOMETRIC_REFERENCE_ONLY" if not masonry
                       else "PARTIALLY_CALCULATED" if pending
                       else "FINAL_QUANTITY_AVAILABLE"),
            "ARITHMETIC": ((f"{w['LENGTH_M']:.3f} x {H:.2f} = {gross:.4f} m2 gross"
                            + (f" - {ded:.4f} m2 openings = {gross - ded:.4f} m2 net" if not pending
                               else f" - {ded:.4f} m2 resolved openings, {len(pending)} opening(s) still unheighted"))
                           if masonry else
                           f"no blockwork area: this band is a {idr['PHYSICAL_OBJECT_CLASS']}, and {w['LENGTH_M']:.3f} m "
                           f"of plan length is carried as geometric reference only"),
        })
    return rows


def _aliases(room):
    """A room answers to its full label and to its canonical name; matching on one only loses HALL / whgm."""
    return {room["ROOM"], room["ROOM_NAME"]}


def _pending_for(room_name, openings):
    """Openings that touch a room and cannot yet be deducted.

    A wall band lists every room along its length, so a 600 mm site on a 14 m external wall reaches all four rooms
    that wall touches even though it stands in one of them.  Over-flagging is the safe direction where nothing better
    is known - it delays a quantity, it never inflates one - but it is not better than knowing.  §B of QS WORKFLOW V1:
    where the two rooms an opening actually joins ARE established, that pair decides which quantity waits on it, and
    the band's other rooms are not charged with a dependency the geometry does not support.
    """
    names = {room_name} if isinstance(room_name, str) else set(room_name)
    out = []
    for o in openings:
        if o["HEIGHT_M"] is not None or not o.get("IS_AN_OPENING_THROUGH_THE_WALL", True):
            continue
        joins = o.get("ROOMS_JOINED")
        if not (names & set(joins if joins else o["ROOMS"])):
            continue
        out.append(o)
    return out


def q(qid, trade, item, value, unit, status, formula, rules, param_source, rooms=None, temp=False,
      residual=None, supersedes=None, note=None, extra=None):
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
        **(extra or {}),
    }


def quantities(rooms, walls_calc, openings, floors, summ, ceil, glazed=None, ceil_rows=(), human_reg=()):
    door_h = TEMPORARY_DEFAULTS[1][2]
    # §B: the two rooms an opening actually joins, where the plan reading or the floor-level boundary established
    # them.  This is what _pending_for prefers over the host band's full room list.
    joined = {h["OPENING_ID"]: h["ROOMS_FOR_DEDUCTION"] for h in (human_reg or []) if h["ROOMS_FOR_DEDUCTION"]}
    for o in openings:
        o["ROOMS_JOINED"] = joined.get(o["OPENING_ID"])
    dry = [r for r in rooms if r["FINISH_CLASS"] == "DRY_ROOM"]
    cer = [r for r in rooms if r["FINISH_CLASS"] == "CERAMIC_SERVICE_ROOM"]
    bath = [r for r in cer if r["ROOM_NAME"] == "BATH"]
    serv = [r for r in cer if r["ROOM_NAME"] != "BATH"]

    apt_doors = [o for o in openings if o["TYPE"] == "DOOR" and o["INSIDE_APARTMENT"]]
    # A genuine orphan is a glazed element inside the apartment with NO host wall and NO host room.  An unresolved site
    # on a wall that touches no apartment room is not an orphan - it is simply outside the scope, and saying otherwise
    # would smear a stair-wall ambiguity across every apartment quantity.
    hosted = {g["BLUE_ELEMENT_ID"]: g for g in (glazed or []) if g["ROOM"]}
    for o in openings:
        g = hosted.get(o["OPENING_ID"])
        if g and not o["ROOMS"]:
            o["ROOMS"] = [g["ROOM"]]
            o["NOTE"] = (f"host room {g['ROOM']} attributed from the frozen band centreline and room bounding box "
                         f"({g['ROOM_BASIS']}); DIAGNOSTIC, not a source statement")
    orphan = [o for o in openings if o["HEIGHT_M"] is None and not o["ROOMS"] and o["HOST_WALL_ID"] is None
              and o.get("IS_AN_OPENING_THROUGH_THE_WALL", True)]
    orphan_res = [{"OPENING_ID": o["OPENING_ID"], "TYPE": o["TYPE"], "WIDTH_M": o["WIDTH_M"],
                   "HOST_WALL_THICKNESS_MM": o["HOST_WALL_THICKNESS_MM"],
                   "WHY": "no host wall and no host room were ever established for this glazed element, so no wall "
                          "area can deduct it even once a height arrives"}
                  for o in orphan]

    def res(rs):
        out, seen = [], set()
        for r in rs:
            for o in _pending_for(_aliases(r), openings):
                if o["OPENING_ID"] in seen:
                    continue
                seen.add(o["OPENING_ID"])
                out.append({"OPENING_ID": o["OPENING_ID"], "TYPE": o["TYPE"], "WIDTH_M": o["WIDTH_M"],
                            "ROOMS": o["ROOMS"], "WHY": "no height established, and §G permits no default for this type"})
        return out

    def rev(ds):
        """US-07 reveals: 0.25 m on each side that exists.

        A door and a passage with a head both have a left, a right and a top.  A full-height passage has no head, so
        there is no top to finish and only the two jambs are added - the sill is excluded for all of them (§H).
        """
        out = 0.0
        for o in ds:
            h = o["HEIGHT_M"] if o["HEIGHT_M"] is not None else door_h
            sides = o.get("REVEAL_SIDES") or ("LEFT", "RIGHT", "TOP")
            out += REVEAL_DEPTH * (2 * h if "LEFT" in sides else 0.0)
            out += REVEAL_DEPTH * (o["WIDTH_M"] if "TOP" in sides else 0.0)
        return out

    # a passage is finished like any other opening: it is not procured, but its jambs are plastered and painted
    apt_pass = [o for o in openings if o["TYPE"] == "OPEN_PASSAGE" and o["INSIDE_APARTMENT"]
                and o["HEIGHT_M"] is not None]
    # §B again: whether an opening's reveal is a dry-room reveal is decided by the rooms it actually joins, not by
    # every room its host band runs past.
    def _sides(o):
        return set(o.get("ROOMS_JOINED") or o["ROOMS"])

    dry_dry = [o for o in apt_doors + apt_pass if not (_sides(o) & set(CERAMIC_ROOM_NAMES))]
    mixed = [o for o in apt_doors + apt_pass if _sides(o) & set(CERAMIC_ROOM_NAMES)]

    sk = sum(r["SKIRTING_LM"] for r in dry)
    wet_floor = summ["B_WET_INTERNAL_FLOOR_AREA_M2"]["VALUE"]
    serv_floor = r4(sum(f["METHOD_A_CAD_POLYGON_AREA_M2"] for f in floors
                        if f["ROOM"].split(" /")[0] in CERAMIC_ROOM_NAMES and f["WET_OR_DRY"] == "DRY"))
    dry_floor = r4(summ["A_DRY_INTERNAL_FLOOR_AREA_M2"]["VALUE"] - serv_floor)
    wet_perim = sum(r["GROSS_WALL_LINE_LM"] for r in bath)

    rows = []
    # ---- 1 and 2: the hidden system, one path, two items
    arith = " + ".join(f"{r['ROOM_NAME']} {r['SKIRTING_LM']:.3f}" for r in dry)
    sk_all = sum(r["SKIRTING_LM_IF_ALL_WINDOW_WIDTHS_DEDUCTED"] for r in dry)
    sills = [g for g in (glazed or []) if g["WALL_BELOW"]]
    dry_names = {r["ROOM_NAME"] for r in dry} | {r["ROOM"] for r in dry}
    dry_sills = [g for g in sills if g["ROOM"] in dry_names]
    # QP-17: exactly which room path loses which passage width, so the correction can be read off the row
    pas_detail = [{"ROOM": r["ROOM_NAME"], "ROOM_ID": r["ROOM_ID"], "OPENING_ID": p["OPENING_ID"],
                   "DESCRIPTION": p["DESCRIPTION"], "WIDTH_M": p["WIDTH_M"],
                   "PATH_BEFORE_LM": r3(r["SKIRTING_LM_IF_ALL_WINDOW_WIDTHS_DEDUCTED"] + r["OPEN_PASSAGE_LM"]),
                   "PATH_AFTER_LM": r["SKIRTING_LM_IF_ALL_WINDOW_WIDTHS_DEDUCTED"]}
                  for r in dry for p in r["OPEN_PASSAGES_DEDUCTED"]]
    pas_total = sum(r["OPEN_PASSAGE_LM"] for r in dry)
    for qid, item in (("Q-01", "HIDDEN_SKIRTING"), ("Q-02", "HIDDEN_PROFILE_ABOVE_SKIRTING")):
        rows.append(q(qid, "بروفايل" if qid == "Q-02" else "سيراميك", item, sk_all, "LM",
                      "FINAL_QUANTITY_AVAILABLE",
                      f"gross wall line less the clear WIDTH of every door, sliding door, window and open passage, "
                      f"dry rooms only: "
                      + " + ".join(f"{r['ROOM_NAME']} {r['SKIRTING_LM_IF_ALL_WINDOW_WIDTHS_DEDUCTED']:.3f}"
                                   for r in dry) + f" = {sk_all:.3f} lm",
                      ["US-02", "US-08", "QP-06", "QP-07", "QP-08", "QP-09", "QP-10" if qid == "Q-01" else "QP-11"],
                      "floor-level boundary classification, frozen; no height enters a linear quantity",
                      rooms=[r["ROOM_NAME"] for r in dry],
                      supersedes={"PREVIOUS": summ["D_TOTAL_SKIRTING_LM"]["VALUE"], "UNIT": "LM",
                                  "WHY": "PAINTRY leaves the skirting entirely under US-01/QP-07 (-11.150), and the "
                                         "column faces in HALL and DRESS join it because §E deducts openings and a "
                                         "column is not an opening (+1.550)"},
                      note="FINAL under QP-09 and QP-17: the owner has read both figures and fixed the rule.  Every "
                           "door, sliding door and window width comes off the path, whether or not wall stands below "
                           f"the opening, and so does every open passage.  The superseded reading, which left the "
                           f"{len(dry_sills)} windows with wall below on the path, gave {sk:.3f} lm and is retained "
                           f"only as an audit trail",
                      extra={"VALUE_UNDER_THE_SUPERSEDED_READING": r3(sk),
                             "SUPERSEDED_READING_CLOSED_BY": "QP-09, owner confirmation",
                             "VALUE_BEFORE_THE_OPEN_PASSAGE_CORRECTION": r3(sk_all + pas_total),
                             "OPEN_PASSAGE_DEDUCTION_LM": r3(pas_total),
                             "OPEN_PASSAGES_DEDUCTED": pas_detail,
                             "WINDOW_WIDTHS_DEDUCTED": [{"ID": g["BLUE_ELEMENT_ID"], "ROOM": g["ROOM"],
                                                         "WIDTH_M": g["WIDTH_M"], "WALL_BELOW": True,
                                                         "HOST_WALL_ID": g["HOST_WALL_ID"]}
                                                        for g in dry_sills]}))
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
    serv_perim = sum(r["GROSS_WALL_LINE_LM"] for r in serv)
    rows.append(q("Q-03P", "عازل حمام+مطابخ", "PANTRY_WATERPROOFING_FLOOR", serv_floor, "M2",
                  "FINAL_QUANTITY_AVAILABLE",
                  " + ".join(f"{f['ROOM']} {f['METHOD_A_CAD_POLYGON_AREA_M2']}" for f in floors
                             if f["ROOM"].split(" /")[0] in CERAMIC_ROOM_NAMES and f["WET_OR_DRY"] == "DRY")
                  + f" = {serv_floor} m2",
                  ["US-14", "QP-13"], "frozen floor polygons, unchanged", rooms=[r["ROOM_NAME"] for r in serv],
                  supersedes={"PREVIOUS": None, "UNIT": "M2",
                              "WHY": "US-14 names the pantry / preparation kitchen among the waterproofed rooms, so "
                                     "the area that was measured and unassigned now has a trade"}))
    rows.append(q("Q-04P", "عازل حمام+مطابخ", "PANTRY_WATERPROOFING_UPTURN", serv_perim, "LM",
                  "FINAL_QUANTITY_AVAILABLE",
                  "GROSS pantry perimeter, doorways NOT deducted: "
                  + " + ".join(f"{r['ROOM_NAME']} {r['GROSS_WALL_LINE_LM']:.3f}" for r in serv)
                  + f" = {serv_perim:.3f} lm",
                  ["US-14", "US-05", "QP-13"], "frozen boundary segments, summed gross",
                  rooms=[r["ROOM_NAME"] for r in serv],
                  note="the GROSS room perimeter, not the skirting path.  The pantry's skirting is zero under US-02 "
                       "and would have been the wrong figure to reach for"))
    rows.append(q("Q-04PR", "عازل حمام+مطابخ", "PANTRY_UPTURN_VERTICAL_AREA_REFERENCE", serv_perim * UPTURN_HEIGHT,
                  "M2", "FINAL_QUANTITY_AVAILABLE",
                  f"{serv_perim:.3f} lm x {UPTURN_HEIGHT:.2f} m = {serv_perim * UPTURN_HEIGHT:.4f} m2",
                  ["US-14"], "derived from Q-04P",
                  note="MATERIAL AND ENGINEERING REFERENCE ONLY, as Q-04R is for the bathrooms"))
    rows.append(q("Q-04R", "عازل حمام+مطابخ", "WET_AREA_UPTURN_VERTICAL_AREA_REFERENCE", wet_perim * UPTURN_HEIGHT,
                  "M2", "FINAL_QUANTITY_AVAILABLE",
                  f"{wet_perim:.3f} lm x {UPTURN_HEIGHT:.2f} m = {wet_perim * UPTURN_HEIGHT:.4f} m2",
                  ["US-04"], "derived from Q-04",
                  note="MATERIAL AND ENGINEERING REFERENCE ONLY.  The BOQ item is the linear metre in Q-04 and this "
                       "area must never be priced beside it"))
    # ---- 5: wall ceramic
    bath_gross = sum(r["GROSS_WALL_AREA_M2"] for r in bath)
    bath_ded = sum(r["OPENING_DEDUCTION_M2"] for r in bath)
    rows.append(q("Q-05", "سيراميك", "WALL_CERAMIC_BATHROOMS", bath_gross - bath_ded, "M2", "PARTIALLY_CALCULATED",
                  f"gross perimeter {sum(r['GROSS_WALL_LINE_LM'] for r in bath):.3f} lm x 3.00 m = {bath_gross:.4f} m2, "
                  f"less full door areas {bath_ded:.4f} m2 = {bath_gross - bath_ded:.4f} m2.  The gross path is used so "
                  f"the tiled strip above each door head is kept; no ceramic reveal is added (§L)",
                  ["US-01", "US-06", "QP-01", "TD-02"], "QP-01 height 3.00 m; TD-02 door height 2.20 m",
                  rooms=["BATH", "BATH", "BATH"], temp=True, residual=res(bath) + orphan_res,
                  note="no opening is pending against this row any more: under QP-20 a dry-room opening no longer "
                       "blocks bathroom ceramic.  It stays PARTIALLY_CALCULATED for one reason only - the door "
                       "heights inside it are still TD-02, a placeholder - and it becomes final when a real door "
                       "height arrives"))
    serv_gross = sum(r["GROSS_WALL_AREA_M2"] for r in serv)
    serv_ded = sum(r["OPENING_DEDUCTION_M2"] for r in serv)
    rows.append(q("Q-06", "سيراميك", "WALL_CERAMIC_SERVICE_ROOM", serv_gross - serv_ded, "M2", "PARTIALLY_CALCULATED",
                  f"PAINTRY gross perimeter {sum(r['GROSS_WALL_LINE_LM'] for r in serv):.3f} lm x 3.00 m "
                  f"= {serv_gross:.4f} m2, less full door areas {serv_ded:.4f} m2",
                  ["US-01", "QP-01", "QP-07"], "QP-01 height 3.00 m",
                  rooms=[r["ROOM_NAME"] for r in serv], residual=res(serv) + orphan_res,
                  note="the 2.750 m opening between HALL and PAINTRY is recorded on the HALL side of the frozen "
                       "boundary and as wall on the PAINTRY side.  It is carried here as a pending deduction on the "
                       "PAINTRY side too, because the wall register puts the opening in that wall"))
    # ---- 6: blockwork
    by_t = defaultdict(lambda: {"L": 0.0, "G": 0.0, "D": 0.0, "F": 0, "P": 0, "FIN": 0.0, "PEND": 0.0,
                                "REF_L": 0.0, "REF_N": 0, "CLASSES": set(), "AMB": 0.0})
    for w in walls_calc:
        b = by_t[str(int(w["THICKNESS_MM"]))]
        b["CLASSES"].add(w["PHYSICAL_OBJECT_CLASS"])
        if not w["BLOCKWORK_CONFIRMED"]:
            b["REF_L"] += w["LENGTH_M"]; b["REF_N"] += 1
            continue
        b["L"] += w["LENGTH_M"]; b["G"] += w["GROSS_AREA_M2"]; b["D"] += w["OPENING_DEDUCTION_M2"]
        if not w["THICKNESS_ITEM_ESTABLISHED"]:
            b["AMB"] += w["LENGTH_M"]
        if w["STATUS"] == "FINAL_QUANTITY_AVAILABLE":
            b["F"] += 1; b["FIN"] += w["NET_AREA_M2"]
        else:
            b["P"] += 1; b["PEND"] += w["GROSS_AREA_M2"] - w["OPENING_DEDUCTION_M2"]
    for t in sorted(by_t, key=lambda k: -by_t[k]["L"]):
        b = by_t[t]
        cls = sorted(b["CLASSES"])
        if b["L"] == 0.0:
            rows.append(q(f"Q-07-{t}", "مبانى", f"BLOCKWORK_{t}", None, "M2", "NOT_APPLICABLE",
                          f"{b['REF_L']:.3f} m of plan length at this spacing, and not one metre of it is a masonry "
                          f"wall: the bands are {', '.join(cls)}",
                          [], "QORTUBA_WALL_OBJECT_IDENTITY, from the frozen material band register",
                          note="NO BLOCKWORK QUANTITY EXISTS AT THIS THICKNESS.  A pair of faces with a measured "
                               "spacing is not masonry; the plan length is kept as geometric reference only"))
            continue
        # a glazed element sits in a wall of its own frame depth, so it can only move a thickness that matches it
        mine = [o for o in orphan_res if str(int(o["HOST_WALL_THICKNESS_MM"])) == t]
        amb = ([{"THICKNESS_ITEM_AMBIGUOUS_LENGTH_M": r3(b["AMB"]),
                 "WHY": "the two faces may be a doubled line rather than two sides of a wall, so which thickness item "
                        "this length bills under is not established.  The AREA does not move; the BOQ line might"}]
               if b["AMB"] > 0 else [])
        final = b["P"] == 0 and not mine and not amb
        rows.append(q(f"Q-07-{t}", "مبانى", f"BLOCKWORK_{t}", b["FIN"] + b["PEND"], "M2",
                      "FINAL_QUANTITY_AVAILABLE" if final else "PARTIALLY_CALCULATED",
                      f"confirmed masonry only: {b['L']:.3f} m x 3.00 m = {b['G']:.4f} m2 gross, less {b['D']:.4f} m2 "
                      f"of full opening areas = {b['FIN'] + b['PEND']:.4f} m2",
                      ["US-06", "QP-02", "TD-02"], "QP-02 height 3.00 m; TD-02 door height 2.20 m",
                      temp=b["D"] > 0,
                      residual=([] if b["P"] == 0 else [{"WALLS_WITH_AN_UNHEIGHTED_OPENING": b["P"],
                                                         "AREA_STILL_MOVING_M2": r4(b["PEND"])}]) + mine + amb,
                      supersedes={"PREVIOUS": None, "UNIT": "M2",
                                  "WHY": "no blockwork area existed before: the height was missing and the deduction "
                                         "column was undecided.  US-06 and QP-02 settle both"},
                      extra={"EXCLUDED_AS_NOT_MASONRY": {"BANDS": b["REF_N"], "PLAN_LENGTH_M": r3(b["REF_L"]),
                                                         "CLASSES": cls}},
                      note=f"{b['F']} masonry bands are fully resolved and {b['P']} still carry an opening with no "
                           f"height; {b['REF_N']} band(s) at this spacing are not masonry and contribute nothing"))
    # ---- 7 and 8: plaster and paint, the same faces
    dry_gross = sum(r["GROSS_WALL_AREA_M2"] for r in dry)
    dry_ded = sum(r["OPENING_DEDUCTION_M2"] for r in dry)
    rev_dry, rev_mix = rev(dry_dry), rev(mixed)
    per_room = " + ".join(f"{r['ROOM_NAME']} {r['GROSS_WALL_AREA_M2']:.3f}" for r in dry)
    for qid, item, trade in (("Q-08", "INTERNAL_PLASTER", "مساح داخلى"), ("Q-09", "WALL_PAINT", "صبغ")):
        rows.append(q(qid, trade, item, dry_gross - dry_ded + rev_dry, "M2", "PARTIALLY_CALCULATED",
                      f"gross dry wall area {per_room} = {dry_gross:.4f} m2, less full door areas {dry_ded:.4f} m2, "
                      f"plus {len(dry_dry)} dry-to-dry opening reveals at 0.25 x (2 x height [+ width where a head "
                      f"exists]) = {rev_dry:.4f} m2, "
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
                  sum(r["GROSS_WALL_AREA_M2"] for r in cer) - sum(r["OPENING_DEDUCTION_M2"] for r in cer), "M2",
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
    dry_rooms = [f for f in floors if f["ROOM"].split(" /")[0] not in CERAMIC_ROOM_NAMES]
    checked = r4(sum(f["METHOD_A_CAD_POLYGON_AREA_M2"] for f in dry_rooms))
    rows.append(q("Q-13", "سيراميك", "PORCELAIN_FLOOR_DRY_ROOMS", checked, "M2", "FINAL_QUANTITY_AVAILABLE",
                  " + ".join(f"{f['ROOM']} {f['METHOD_A_CAD_POLYGON_AREA_M2']}" for f in dry_rooms)
                  + f" = {checked} m2",
                  ["QP-14", "US-01"], "frozen floor polygons, re-totalled after the service-room exclusions",
                  rooms=[f["ROOM"] for f in dry_rooms],
                  extra={"SUBTOTAL_VERIFIED_AGAINST_THE_FROZEN_REGISTER": True,
                         "DRY_TOTAL_BEFORE_SERVICE_EXCLUSIONS": summ["A_DRY_INTERNAL_FLOOR_AREA_M2"]["VALUE"],
                         "PANTRY_EXCLUDED_M2": serv_floor,
                         "ROOM_BREAKDOWN": [{"ROOM": f["ROOM"], "AREA_M2": f["METHOD_A_CAD_POLYGON_AREA_M2"]}
                                            for f in dry_rooms]},
                  supersedes={"PREVIOUS": None, "UNIT": "M2",
                              "WHY": "the area was blocked on a finishes schedule; QP-14 supplies the finish"},
                  note="re-totalled room by room from the frozen polygons rather than taken from the earlier subtotal, "
                       "because the pantry left the dry set after that subtotal was written.  The six rooms sum to "
                       f"{checked} m2 and the room breakdown is kept in the calculation backup"))
    # ---- §7 aluminium: an area per opening, subtotalled by type.  A count is a multiplier, never a quantity
    # §3/§11: three separate schedules, because an internal door is not an aluminium item
    by_trade = defaultdict(list)
    for h in human_reg or []:
        if h["IS_AN_OPENING_THROUGH_THE_WALL"] and h["INSIDE_APARTMENT"]:
            by_trade[h["MATERIAL_TRADE"]].append(h)
    for qid, item, group, trade in (("Q-15", "ALUMINIUM_EXTERNAL_WINDOWS", by_trade["ALUMINIUM"], "ألمنيوم"),
                                    ("Q-16", "PVC_INTERNAL_DOORS", by_trade["PVC"], "أبواب PVC"),
                                    ("Q-17", "INTERNAL_GLAZED_OPENING",
                                     by_trade["INTERNAL_GLAZED_OPENING"], "زجاج داخلي")):
        sched = [{"OPENING_ID": o["OPENING_ID"], "TYPE": o["TYPE"], "ROOM": o["ROOM"],
                  "DESCRIPTION": o["DESCRIPTION"], "MATERIAL_TRADE": o["MATERIAL_TRADE"],
                  "COUNT": 1,
                  "WIDTH_M": o["WIDTH_M"], "HEIGHT_M": o["HEIGHT_M"],
                  "AREA_M2": (r4(o["WIDTH_M"] * o["HEIGHT_M"]) if o["HEIGHT_M"] is not None else None),
                  "STATUS": ("CALCULATED" if o["HEIGHT_M"] is not None else "OWNER_INPUT_REQUIRED"),
                  "WHY": (None if o["HEIGHT_M"] is not None else
                          "US-11: there is no default window height, so the owner is asked")} for o in group]
        done = [x for x in sched if x["AREA_M2"] is not None]
        area = round(sum(x["AREA_M2"] for x in done), 4) if done else None
        # the AREA is established once a height exists; which openings fall under the aluminium package rather than a
        # joinery one is a finishes question, and material identity is part of being final
        # a physical opening area is not a pricing quantity.  §12 of OWNER INPUTS V2: the PVC schedule waits on a
        # pricing basis (per door/set or by m2) and the internal glazing waits on its commercial trade.
        settled = sched and len(done) == len(sched)
        rows.append(q(qid, trade, item, area, "M2",
                      "PROJECT_RULE_REQUIRED" if (settled and qid in ("Q-16", "Q-17")) else
                      "FINAL_QUANTITY_AVAILABLE" if settled else
                      "PARTIALLY_CALCULATED" if done else "OWNER_INPUT_REQUIRED",
                      " + ".join(f"{x['DESCRIPTION']} {x['WIDTH_M']:.3f} x "
                                 + (f"{x['HEIGHT_M']:.2f}" if x["HEIGHT_M"] else "height?")
                                 for x in sched) or "no opening of this type",
                      ["US-13", "TD-02", "QP-16"] if qid == "Q-16" else
                      ["US-13", "QP-12"] if qid == "Q-17" else ["US-11", "US-13"],
                      "TD-02 door height 2.20 m" if qid == "Q-16" else
                      "QP-12 owner-supplied height 2.200 m" if qid == "Q-17" else
                      "none: US-11 forbids a default window height",
                      temp=bool(done) and qid == "Q-16",
                      residual=[{"OPENING_ID": x["OPENING_ID"], "TYPE": x["TYPE"], "WIDTH_M": x["WIDTH_M"],
                                 "WHY": x["WHY"]} for x in sched if x["AREA_M2"] is None],
                      extra={"SCHEDULE": sched, "OPENINGS": len(sched), "COUNT": len(sched), "RESOLVED": len(done),
                             "PHYSICAL_OPENING_AREA_M2": {"VALUE": area, "STATE": "ESTABLISHED" if settled
                                                          else "PARTIAL"},
                             "FINAL_PRICING_QUANTITY": (
                                 {"VALUE": None, "STATE": "PROJECT_RULE_REQUIRED",
                                  "WAITING_ON": "whether PVC doors are priced per door / per set or by m2",
                                  "OPTIONS": ["per door", "per set", "by m2"],
                                  "WHY": "the physical opening area is established; the pricing UNIT is not, and a "
                                         "quantity in the wrong unit is not a pricing quantity"}
                                 if qid == "Q-16" else
                                 {"VALUE": None, "STATE": "PROJECT_RULE_REQUIRED",
                                  "WAITING_ON": "the commercial material and trade of this internal glazed opening",
                                  "WHY": "2.750 x 2.200 = 6.050 m2 is physically established and used in every "
                                         "dependent wall deduction; which trade carries the product is not"}
                                 if qid == "Q-17" else
                                 {"VALUE": area, "STATE": "ESTABLISHED" if settled else "PENDING"}),
                             "TRADE_SEPARATION": "US-13: interior doors are PVC and are never billed as aluminium; "
                                                 "aluminium carries exterior openings only",
                             "COUNT_IS_NOT_THE_QUANTITY": "a count is a multiplier: the priced quantity is the sum of "
                                                          "width x height over the schedule above"},
                      note=("PHYSICAL QUANTITY ESTABLISHED, FINAL PRICING QUANTITY PENDING - waiting on "
                            + ("whether PVC doors are priced per door, per set or by m2 (O-09).  "
                               if qid == "Q-16" else
                               "the commercial material and trade of this glazed opening (O-10).  ")
                            if qid in ("Q-16", "Q-17") else "") + ("count, width, height and area, one row per "
                            "opening.  " +
                            ("all seven Qortuba apartment doors are interior - each is seen from two apartment rooms "
                             "on the frozen boundary - so all seven are PVC under US-13 and none is an aluminium item"
                             if qid == "Q-16" else
                             "an internal glazed opening between two apartment rooms: not an aluminium envelope item, "
                             "and its product is classified separately" if qid == "Q-17" else
                             "no area is released until every height is supplied: US-11 permits no default and §11 "
                             "requires count, width, height and area before an aluminium pricing quantity exists"))))

    # ---- 9: ceiling paint
    rows.append(q("Q-14", "ديكور جبس", "CEILING_BY_AREA", ceil, "M2", "FINAL_QUANTITY_AVAILABLE",
                  " + ".join(f"{c['ROOM']} {c['CEILING_GEOMETRIC_AREA_M2']}" for c in ceil_rows) + f" = {ceil} m2",
                  ["US-15", "QP-15"], "frozen ceiling geometry register, unchanged",
                  extra={"DECOR_LENGTHS_NOT_CARRIED": ["cornice", "cove lighting", "bulkhead", "shadow gap",
                                                       "decorative perimeter", "gypsum feature length"],
                         "CEILING_PERIMETER_NOT_A_PAYABLE_ITEM_LM": 153.125},
                  supersedes={"PREVIOUS": None, "UNIT": "M2",
                              "WHY": "the ceiling had no priced line at all: the house precedent prices decor and no "
                                     "ceiling design exists.  US-15 gives it an area line instead"},
                  note="one line, priced by area.  The 153.125 lm ceiling perimeter measured earlier is NOT carried "
                       "as a payable decor item: under US-15 nothing is inferred from a room perimeter without a "
                       "ceiling drawing.  A rate per m2 is all this row now needs"))
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
        ("O-03", "whether the Pantry takes waterproofing as well as ceramic",
         "US-14 + QP-13 = yes: floor membrane 11.685 m2 and a gross-perimeter upturn of 11.150 lm"),
        ("O-04", "the ceiling scope", "US-15 + QP-15 = priced by area, 138.510 m2, with no decor length carried"),
        ("V2-01", "the height of the glazed opening between the Hall and the Pantry", "QP-12 = 2.200 m"),
        ("V2-02", "the dry floor finish", "QP-14 = porcelain, which releases 108.9625 m2"),
        ("V2-03", "whether interior doors are aluminium",
         "US-13 + QP-16 = no: they are PVC and carry their own schedule"),
        ("OP-01", "what the 1.200 m gap between the Hall and the Lobby is",
         "US-16 + QP-17 = an OPEN_PASSAGE: no door leaf, no procurement line, and its width leaves the linear path"),
        ("OP-02", "what the 1.200 m gap between the Master bedroom and the Dressing room is",
         "US-16 + QP-17 = an OPEN_PASSAGE, on the same terms"),
        ("OP-03", "the vertical condition of the Hall / Lobby passage",
         "QP-18 = OPEN_PASSAGE_FULL_HEIGHT at the 3.000 m wall height: 1.200 x 3.000 = 3.600 m2, left and right "
         "reveals, no top"),
        ("OP-04", "the vertical condition of the Master bedroom / Dressing room passage",
         "QP-18 + QP-19 = OPEN_PASSAGE_WITH_HEAD at 2.200 m: 1.200 x 2.200 = 2.640 m2, left, right and top reveals"),
    ]


STILL_OPEN = [
    ("O-06", "PROJECT_INPUT", "the height of each of the six exterior windows, asked one at a time",
     "US-11 forbids a default window height, so each window is asked in its own row of QORTUBA_OWNER_QUESTIONS with "
     "its room and its width, and none is given another's height",
     "the aluminium schedule, and the plaster, paint, blockwork and ceramic of every wall they stand in"),
    ("O-07", "PROJECT_INPUT", "what three remaining openings actually are: door, open passage, window or something "
     "else",
     "two of the original five are answered - the owner has confirmed both 1.200 m gaps as open passages.  Three are "
     "still open: the 2.700 m gap between a Bedroom and the Hall, and the two 1.100 m gaps at the ends of the same "
     "short Bedroom wall facing the stair landing.  Each has its own crop and none is inferred",
     "the wall-area trades of the rooms they stand in"),
    ("O-09", "PROJECT_RULE", "whether the 7 interior PVC doors are priced per door, per set, or by m2",
     "the physical side is settled — 7 doors, 16.665 m2 of opening area — but a physical area is not a pricing "
     "quantity.  Until the basis is given, FINAL_PRICING_QUANTITY stays empty rather than defaulting to the m2 that "
     "happens to be measured",
     "the PVC door schedule only.  No wall-area trade waits on it: the widths are already deducted"),
    ("O-10", "PROJECT_RULE", "the commercial material and trade of the internal glazed opening between the Hall and "
     "the Pantry",
     "2.750 x 2.200 = 6.050 m2 is physically established and frozen, but no source says whether it is aluminium "
     "glazing, a PVC screen, a timber-framed panel or joinery, and US-13 forbids placing it under aluminium by "
     "resemblance",
     "the internal glazing line only.  The opening is already deducted from the walls around it"),
    ("O-05", "PROJECT_RULE", "whether the 2م=1م halving of corners and wall ends applies",
     "unchanged and still unasked-for: Qortuba has not cut its boundary into corners and ends, so the answer releases "
     "nothing yet",
     "plaster corners and ends"),
    ("O-08", "SPEC_REQUIRED", "the ceramic, porcelain, membrane and ceiling specifications, and the rates",
     "every quantity that is final is final as a QUANTITY.  Products and rates are a separate conversation, named "
     "here so the absence is visible rather than assumed",
     "pricing, not measurement"),
]


def finish():
    ver = verify_inputs()
    skirt = reg(QS, "QORTUBA_QS01_SKIRTING_TAKEOFF")["ROWS"]
    walls = reg(QS, "QORTUBA_QS01_BLOCK_WALL_TAKEOFF")
    blue = reg(QS, "QORTUBA_QS01_BLUE_ELEMENT_SCHEDULE")["ROWS"]
    floors = reg(QS, "QORTUBA_QS01_FLOOR_CALCULATIONS")["ROWS"]
    summ = reg(QS, "QORTUBA_QS01_SUMMARY_TOTALS")
    ceil = summ["F_TOTAL_CEILING_GEOMETRY_M2"]["VALUE"]

    completed = OS.finish_register()
    ops = opening_register_from_source()
    glazed = MI.glazed_hosts()
    ident = MI.wall_identity()
    human = OS.human_register()
    rooms = room_rows(skirt, ops, glazed, human)
    wcalc = wall_rows(walls, ops, ident)
    qs = quantities(rooms, wcalc, ops, floors, summ, ceil, glazed, reg(QS, "QORTUBA_QS01_CEILING_TAKEOFF")["ROWS"], human)

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

    ident_art = {"ARTIFACT": "QORTUBA_WALL_OBJECT_IDENTITY",
                 "RULE": "two faces with a measured spacing are a geometric pair.  Only a masonry wall may become a "
                         "blockwork quantity; a column, a shaft and a drafting arrow all report a thickness too",
                 "CLASSES": list(MI.OBJECT_CLASSES), "ROWS": ident, "COUNT": len(ident),
                 "BY_CLASS": dict(Counter(r["PHYSICAL_OBJECT_CLASS"] for r in ident)),
                 "LENGTH_M_BY_THICKNESS_AND_CLASS": MI.summary(),
                 "BLOCKWORK_CONFIRMED_BANDS": sum(1 for r in ident if r["BLOCKWORK_CONFIRMED"]),
                 "BLOCKWORK_CONFIRMED_LENGTH_M": r3(sum(r["LENGTH_M"] for r in ident if r["BLOCKWORK_CONFIRMED"])),
                 "EXCLUDED_LENGTH_M": r3(sum(r["LENGTH_M"] for r in ident if not r["BLOCKWORK_CONFIRMED"])),
                 "GEOMETRY_RECOMPUTED": 0}
    glaze_art = {"ARTIFACT": "QORTUBA_GLAZED_ELEMENT_HOSTS",
                 "RULE": "every glazed element joined to the wall band it stands in and the room that band bounds, by "
                         "lookup over frozen centrelines and bounding boxes.  Room attribution is DIAGNOSTIC",
                 "ROWS": glazed, "COUNT": len(glazed),
                 "INTERRUPTS_THE_WALL_IN_PLAN": [g["BLUE_ELEMENT_ID"] for g in glazed if g["INTERRUPTS_THE_WALL_IN_PLAN"]],
                 "WALL_BELOW": [g["BLUE_ELEMENT_ID"] for g in glazed if g["WALL_BELOW"]],
                 "WITHOUT_A_ROOM": [g["BLUE_ELEMENT_ID"] for g in glazed if not g["ROOM"]],
                 "GEOMETRY_RECOMPUTED": 0}
    wall_art = {"ARTIFACT": "QORTUBA_BLOCKWORK_RECALC", "ROWS": wcalc, "COUNT": len(wcalc),
                "BLOCKWORK_CONFIRMED_BANDS": sum(1 for w in wcalc if w["BLOCKWORK_CONFIRMED"]),
                "EXCLUDED_AS_NOT_MASONRY": sum(1 for w in wcalc if not w["BLOCKWORK_CONFIRMED"]),
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
    blocked = [x for x in qs if x["STATUS"] in ("SOURCE_REQUIRED", "SPEC_REQUIRED", "PROJECT_RULE_REQUIRED",
                                                "OWNER_INPUT_REQUIRED")]
    na = [x for x in qs if x["STATUS"] == "NOT_APPLICABLE"]
    quant = {
        "ARTIFACT": "QORTUBA_RECALCULATED_QUANTITIES_V1",
        "RULE": "every figure below is arithmetic over the FROZEN measurement registers.  No geometry was re-read, no "
                "room re-measured and no opening re-detected",
        "ROWS": qs, "COUNT": len(qs),
        "BY_STATUS": {k: sum(1 for x in qs if x["STATUS"] == k) for k in
                      ("FINAL_QUANTITY_AVAILABLE", "PARTIALLY_CALCULATED", "OWNER_INPUT_REQUIRED",
                       "PROJECT_RULE_REQUIRED", "SPEC_REQUIRED", "SOURCE_REQUIRED", "NOT_APPLICABLE")},
        "FINAL": [{"QUANTITY_ID": x["QUANTITY_ID"], "BOQ_ITEM": x["BOQ_ITEM"],
                   "VALUE": x["MEASURED_NET_QUANTITY"], "UNIT": x["UNIT"]} for x in final],
        "PARTIAL": [{"QUANTITY_ID": x["QUANTITY_ID"], "BOQ_ITEM": x["BOQ_ITEM"],
                     "VALUE_SO_FAR": x["MEASURED_NET_QUANTITY"], "UNIT": x["UNIT"],
                     "OPENINGS_STILL_PENDING": len(x["RESIDUAL_OPENINGS"])} for x in partial],
        "BLOCKED": [{"QUANTITY_ID": x["QUANTITY_ID"], "BOQ_ITEM": x["BOQ_ITEM"], "STATUS": x["STATUS"],
                     "VALUE_SO_FAR": x["MEASURED_NET_QUANTITY"], "WHY": x["NOTE"]} for x in blocked],
        "NOT_APPLICABLE": [{"QUANTITY_ID": x["QUANTITY_ID"], "BOQ_ITEM": x["BOQ_ITEM"], "WHY": x["NOTE"]} for x in na],
        "OBJECT_IDENTITY_SOURCE": "QORTUBA_WALL_OBJECT_IDENTITY: every wall band classified from the frozen material "
                                  "band register before any area was formed",
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

    written = [write(o["ARTIFACT"], o) for o in (store, completed, opening, ident_art, glaze_art, room_art,
                                                 wall_art, quant, quest)]
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
    return {"RULES": store, "COMPLETED": completed, "OPENINGS": opening, "IDENTITY": ident_art, "GLAZED": glaze_art, "ROOMS": room_art,
            "WALLS": wall_art, "QUANTITIES": quant, "QUESTIONS": quest, "FREEZE": fr}


if __name__ == "__main__":
    o = finish()
    print("FREEZE", o["FREEZE"]["DIGEST"][:16])
    print("rules:", o["RULES"]["COUNTS"])
    print("source search:", o["COMPLETED"]["SOURCE_SEARCH"]["CONCLUSION"][:90], "...")
    print("completed register:", o["COMPLETED"]["BY_TYPE"], "| not an opening:",
          len(o["COMPLETED"]["NOT_AN_OPENING"]))
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
    print("RULE/SPEC/SOURCE BLOCKED:")
    for x in o["QUANTITIES"]["BLOCKED"]:
        print(f"   {x['QUANTITY_ID']:8s} {x['BOQ_ITEM']:38s} {str(x['VALUE_SO_FAR']):>10}  {x['STATUS']}")
    print("NOT APPLICABLE:", [x["QUANTITY_ID"] for x in o["QUANTITIES"]["NOT_APPLICABLE"]])
    print("object identity:", o["IDENTITY"]["BY_CLASS"], "| masonry lm", o["IDENTITY"]["BLOCKWORK_CONFIRMED_LENGTH_M"],
          "| excluded lm", o["IDENTITY"]["EXCLUDED_LENGTH_M"])
    print("closed questions:", o["QUESTIONS"]["CLOSED_COUNT"], "| still open:", o["QUESTIONS"]["STILL_OPEN_COUNT"])
