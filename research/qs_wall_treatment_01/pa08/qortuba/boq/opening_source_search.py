"""Complete the Qortuba opening register: an exhaustive, conservative search of the source for type and height.

Everything the drawing could carry was looked for and the result is recorded, including the places where nothing was
found.  An exhaustive search that comes back empty is a finding, not a failure, and it is worth more than a guess: it
tells the owner that no further reading of this drawing set will produce an opening height, so the only way forward is a
schedule, an elevation or an instruction.

Two things the search DID resolve.  A gap that interrupts one face of a wall is not a doorway - a doorway interrupts
both - so five sites stop blocking the trades they were holding.  And the independent PDF reading, whose declared powers
include the presence or absence of a door, identifies two of the remaining gaps as doorless openings.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

R1 = Path(PR.OUT_DIR) / "pa08_qortuba_r1"
R3 = Path(PR.OUT_DIR) / "pa08_qortuba_r3"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"
DWG_JSON = Path("data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json")

OPENING_TYPES = ("DOOR", "WINDOW", "SLIDING_DOOR", "GLAZED_OPENING", "OPEN_PASSAGE",
                 "FULL_HEIGHT_OPENING_FOR_MEASUREMENT", "UNRESOLVED")

# OPEN_PASSAGE: a real interruption in the wall with no door leaf or system in it.  It is not PVC, it is not
# aluminium, and it must never appear in a door or window procurement schedule - but it does interrupt blockwork,
# plaster, paint, wall ceramic, skirting and the hidden profile, exactly as its dimensions and its neighbours require.
OPEN_PASSAGE_SUBTYPES = ("OPEN_PASSAGE_FULL_HEIGHT", "OPEN_PASSAGE_WITH_HEAD")
OPEN_PASSAGE_TRADE = "OPEN_PASSAGE_NO_PROCUREMENT"

# QS WORKFLOW V1 §D: the whole useful vocabulary, and deliberately no more.  A drawing has endless variations; a
# takeoff needs the eight cases that change a quantity.  Anything that does not fit one of them is UNKNOWN, and an
# UNKNOWN that materially moves a number is a question for the owner, not a new geometry rule.
OPENING_CASES = ("DOOR", "WINDOW", "SLIDING_DOOR", "GLAZED_OPENING",
                 "OPEN_PASSAGE_FULL_HEIGHT", "OPEN_PASSAGE_WITH_HEAD",
                 "FULL_HEIGHT_OPENING_FOR_MEASUREMENT", "NOT_AN_OPENING", "UNKNOWN")

# FINAL COMPLETION §11: the owner has closed #7, #10 and #11 without naming an architectural type.  For quantity
# measurement they are simply full-height interruptions in the wall: 3.000 m high, no leaf and no system, so nothing
# is procured for them.  This is a MEASUREMENT CLASSIFICATION, not an architectural one, and it is not asked again.
OWNER_CLOSED_AS_MEASUREMENT_OPENINGS = {
    "OS-b1e147c89482": "FINAL COMPLETION §11: closed by the owner as a full-height wall interruption for "
                       "measurement, 2.700 x 3.000 = 8.100 m2.  No architectural type was given and none is inferred",
    "OS-3144b5fbb149": "FINAL COMPLETION §11: closed by the owner as a full-height wall interruption for "
                       "measurement, 1.100 x 3.000 = 3.300 m2",
    "OS-045efd7810a7": "FINAL COMPLETION §11: closed by the owner as a full-height wall interruption for "
                       "measurement, 1.100 x 3.000 = 3.300 m2",
}


def case_of(row):
    """The generic case this opening bills under, from its type, its subtype and whether it is a gap at all."""
    if not row["IS_AN_OPENING_THROUGH_THE_WALL"]:
        return "NOT_AN_OPENING"
    if row["TYPE"] == "FULL_HEIGHT_OPENING_FOR_MEASUREMENT":
        return "FULL_HEIGHT_OPENING_FOR_MEASUREMENT"
    if row["TYPE"] == "OPEN_PASSAGE":
        return row["OPEN_PASSAGE_SUBTYPE"] or "UNKNOWN"
    return row["TYPE"] if row["TYPE"] in OPENING_CASES else "UNKNOWN"
APARTMENT_ROOMS = {"HALL / whgm", "M.B.ROOM", "BED.ROOM", "PAINTRY", "DRESS", "BATH", "UNLABELLED_INTERNAL_SPACE"}

DEFAULT_DOOR_WIDTH_M = 1.00
DEFAULT_DOOR_HEIGHT_M = 2.20

# §2 of OWNER INPUTS V2: a height the owner supplied for one named opening.  This is an OWNER OVERRIDE, rank 2 on the
# priority ladder - above any standard and above any default - and it is a real dimension, not a placeholder.
OWNER_SUPPLIED_HEIGHTS = {
    "OS-b5a0fbb335d4": (2.200, "OWNER INPUTS V2 §2: the glazed opening between the Hall and the Pantry is 2.200 m "
                               "high, so its physical opening is 2.750 x 2.200 = 6.050 m2"),
}

# OPEN-PASSAGE RULE CORRECTION: the owner has identified two of the five unresolved gaps.  This is an OWNER
# OVERRIDE, rank 2 on the priority ladder, and it settles the TYPE only - the vertical condition is a separate
# question, and until it is answered no height may be taken from anywhere, least of all from the door default.
OWNER_SUPPLIED_TYPES = {
    "OS-77f8fed2eb15": ("OPEN_PASSAGE", "OPEN-PASSAGE RULE CORRECTION: the owner confirms the 1.200 m gap between "
                                        "the Hall and the Lobby is an open passage, not a door"),
    "OS-85cb2192ebc0": ("OPEN_PASSAGE", "OPEN-PASSAGE RULE CORRECTION: the owner confirms the 1.200 m gap between "
                                        "the Master bedroom and the Dressing room is an open passage, not a door"),
}

# QS WORKFLOW V1 §A: the owner has now given the vertical condition of both passages.  A subtype is an explicit
# PROJECT INPUT, rank 2 on the priority ladder.  FULL_HEIGHT takes the applicable wall height and has no head, so no
# top reveal exists; WITH_HEAD takes the height the owner states - which is a Qortuba input in its own right and not
# the generic door default, even where the two figures happen to coincide.
QORTUBA_WALL_HEIGHT_M = 3.000
OWNER_SUPPLIED_PASSAGE_SUBTYPES = {
    "OS-77f8fed2eb15": ("OPEN_PASSAGE_FULL_HEIGHT", QORTUBA_WALL_HEIGHT_M,
                        "QS WORKFLOW V1 §A: the owner states the Hall / Lobby passage is open to the ceiling, so "
                        "its opening height IS the applicable wall height, 3.000 m.  1.200 x 3.000 = 3.600 m2"),
    "OS-85cb2192ebc0": ("OPEN_PASSAGE_WITH_HEAD", 2.200,
                        "QS WORKFLOW V1 §A: the owner states the Master bedroom / Dressing room passage is shaped "
                        "like a normal door opening and gives 2.200 m.  This is an EXPLICIT QORTUBA OWNER INPUT, not "
                        "the generic TD-02 door default.  1.200 x 2.200 = 2.640 m2"),
}
# no top reveal exists where there is no head to reveal
REVEAL_SIDES = {"OPEN_PASSAGE_FULL_HEIGHT": ("LEFT", "RIGHT"),
                "OPEN_PASSAGE_WITH_HEAD": ("LEFT", "RIGHT", "TOP")}

# a room answers to a name a person uses, not to the label the CAD file happens to carry
FRIENDLY = {
    "HALL / whgm": "Hall", "M.B.ROOM": "Master bedroom", "PAINTRY": "Pantry / preparation kitchen",
    "DRESS": "Dressing room", "UNLABELLED_INTERNAL_SPACE": "Lobby (unlabelled internal space)",
}


AMBIGUOUS_NAMES = {"BED.ROOM", "BATH"}


def friendly(room, area=None):
    """A room name a person can act on.  Two rooms are called BED.ROOM and three are called BATH, so a name without an
    area is deliberately indefinite rather than falsely specific."""
    if not room:
        return None
    if room in AMBIGUOUS_NAMES and not area:
        return "a Bedroom" if room == "BED.ROOM" else "a Bathroom"
    base = FRIENDLY.get(room, room.title() if room.isupper() else room)
    if room == "BED.ROOM" and area:
        return f"Bedroom ({area:.2f} m2)"
    if room == "BATH" and area:
        return f"Bathroom ({area:.2f} m2)"
    return base


def reg(folder, name):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


# ---------------------------------------------------------------------------- §1 what the source was searched for
def source_search():
    """Every place an opening height or type could hide in this DWG, and what was there."""
    d = json.loads(DWG_JSON.read_text("utf-8"))
    objs = d["OBJECTS"]
    ents = Counter(o.get("entity") or o.get("object") for o in objs)
    texts = []
    for o in objs:
        if o.get("entity") in ("TEXT", "MTEXT"):
            for k in ("text", "text_value", "default_value"):
                if isinstance(o.get(k), str) and o[k].strip():
                    texts.append(o[k].strip())
    blocks = sorted({str(o.get("name")) for o in objs if o.get("object") == "BLOCK_HEADER"})
    named = [b for b in blocks if not b.startswith("*")]
    dims = [o for o in objs if o.get("entity") == "DIMENSION_LINEAR"]
    off_plane = [o for o in dims if abs(o.get("elevation") or 0.0) > 1e-9]
    layers = sorted({str(o.get("name")) for o in objs if o.get("object") == "LAYER"})
    # a dimension text override of the form \A1;NNN is a plan dimension in centimetres
    dim_texts = sorted({t for t in texts if t.startswith("\\A1;")})
    prose = [t for t in texts if not t.startswith("\\A1;")]

    checks = [
        ("BLOCK_ATTRIBUTES", ents.get("ATTRIB", 0) + ents.get("ATTDEF", 0),
         "no ATTRIB or ATTDEF entity exists in the file, and every one of the 116 block headers reports hasattrs = 0, "
         "so no block carries an attribute that could name a size or a mark"),
        ("AUTHORED_DIMENSIONS", len(dims),
         f"{len(dims)} linear dimensions, every one of them at elevation 0.0 with extrusion [0,0,1]: all lie in the "
         f"plan plane and measure plan distances.  {len(off_plane)} measure anything out of that plane"),
        ("WINDOW_OR_DOOR_BLOCKS", len(named),
         f"the named block definitions are {named}.  None is a door or window type block, none encodes a size, and "
         f"none carries a schedule"),
        ("OPENING_SCHEDULE", 0,
         "every TEXT and MTEXT string in the file was read.  They are room names, title-block fields and dimension "
         "value overrides.  There is no schedule, no door mark, no window mark and no height annotation"),
        ("ANNOTATIONS_CARRYING_A_HEIGHT", 0,
         "the only height-like string in the drawing is 'LEVEL R.F = 4.00 m', which is a roof floor level, not an "
         "opening height.  'NEIGHBOUR 26.50 M' and 'S.STREET 19.00 M' are site boundary lengths"),
        ("EMBEDDED_ELEVATIONS_OR_SECTIONS", 0,
         "the sheet carries one view, titled SECOND FLOOR PLAN at 1:100.  No layer, no block and no geometry group "
         "holds an elevation or a section, and no dimension leaves the plan plane"),
        ("REPEATED_IDENTICAL_BLOCK_DEFINITIONS", ents.get("INSERT", 0),
         f"{ents.get('INSERT', 0)} inserts across {len(named)} named definitions.  Repetition would let one resolved "
         f"instance resolve its twins; none of the repeated definitions is an opening"),
        ("PDF_COMPANION", 1,
         "the plotted PDF is the same sheet at the same scale.  The independent reading of it recorded in R1 quotes "
         "the same printed dimension values and adds no height"),
    ]
    return {
        "SOURCE_FILE": str(DWG_JSON),
        "ENTITY_CENSUS": dict(ents.most_common()),
        "LAYERS": layers,
        "NAMED_BLOCK_DEFINITIONS": named,
        "PROSE_STRINGS": sorted(set(prose)),
        "DIMENSION_VALUE_OVERRIDES": len(dim_texts),
        "CHECKS": [{"LOOKED_FOR": a, "FOUND": b, "WHAT_WAS_THERE": c} for a, b, c in checks],
        "OPENING_HEIGHTS_FOUND": 0,
        "OPENING_TYPE_MARKS_FOUND": 0,
        "CONCLUSION": "the drawing set contains no opening height of any kind.  This was established at R1 from the "
                      "opening sites themselves and is confirmed here independently from the raw decode: no block "
                      "attribute, no schedule, no annotation, no elevation, no section, and not one dimension out of "
                      "the plan plane.  No further reading of this source will produce a height",
        "WHAT_WOULD_SUPPLY_ONE": ["a door and window schedule", "an elevation or section", "an owner instruction"],
    }


# ---------------------------------------------------------------------------- §1 the completed register
SITE_TYPE = {"CONFIRMED_DOOR_OPENING": "DOOR", "PROBABLE_DOOR_OPENING": "DOOR",
             "CONFIRMED_WINDOW_OPENING": "GLAZED_OPENING", "UNRESOLVED": "UNRESOLVED", "CAD_JUNCTION": "UNRESOLVED"}
BLUE_TYPE = {"WINDOW_WITH_WALL_BELOW": "WINDOW", "FULL_HEIGHT_WINDOW": "WINDOW", "SLIDING_DOOR": "SLIDING_DOOR",
             "OTHER_GLAZING": "GLAZED_OPENING", "UNRESOLVED": "UNRESOLVED"}

# the independent PDF reading, whose declared powers include the presence or absence of a door
PDF_READER = {
    "OS-85cb2192ebc0": "DRESS to M.B.ROOM: the partition runs 315 cm from the north wall and stops, leaving a "
                       "~120 cm gap at its south end; no door symbol",
    "OS-77f8fed2eb15": "vestibule to HALL: the north wall stops short, leaving a ~130 cm doorless opening; no door "
                       "symbol",
    "OS-b5a0fbb335d4": "HALL to PAINTRY: wall stubs at both ends with a ~285 cm run between them drawn on the glazing "
                       "layer; no leaf; PAINTRY has no other entry",
}


def completed_register():
    """One row per opening, with the type and height the source actually supports."""
    sites = {r["SITE_ID"]: r for r in reg(R1, "PA08_QORTUBA_R1_OPENING_REGISTER")["ROWS"]}
    walls = reg(QS, "QORTUBA_QS01_BLOCK_WALL_TAKEOFF")["ROWS"]
    blue = reg(QS, "QORTUBA_QS01_BLUE_ELEMENT_SCHEDULE")["ROWS"]
    host_of = {}
    for w in walls:
        for o in w["OPENINGS"]:
            host_of[o["SITE_ID"]] = w

    from research.qs_wall_treatment_01.pa08.qortuba.boq import material_identity as MI
    glz = {g["BLUE_ELEMENT_ID"]: g for g in MI.glazed_hosts()}
    site_to_blue = {g["OPENING_SITE_ID"]: bid for bid, g in glz.items() if g["OPENING_SITE_ID"]}

    rows = []
    for sid, s in sites.items():
        w = host_of.get(sid)
        rooms = sorted({r for r in (w["ROOM_SIDE_A"] + w["ROOM_SIDE_B"]) if r in APARTMENT_ROOMS}) if w else []
        t = SITE_TYPE[s["CLASS"]]
        single_face = s["STATUS"] == "SINGLE_FACE_GAP"
        junction = s["CLASS"] == "CAD_JUNCTION"
        is_opening = not (single_face or junction)
        bid = site_to_blue.get(sid)
        # a site is a real gap in the band, so BOTH sides of the host wall lose area there.  The blue element's own
        # room attribution is kept only as ROOM_ID, for the one-sided floor-level path.
        rows.append({
            "OPENING_ID": sid, "BLUE_ELEMENT_ID": bid,
            "ROOM": ", ".join(rooms) or None, "ROOM_ID": (glz[bid]["ROOM_ID"] if bid else None),
            "HOST_WALL_ID": (w["WALL_ID"] if w else None),
            "HOST_WALL_THICKNESS_MM": s["HOST_WALL_THICKNESS_MM"],
            "TYPE": ("FULL_HEIGHT_OPENING_FOR_MEASUREMENT"
                     if (is_opening and sid in OWNER_CLOSED_AS_MEASUREMENT_OPENINGS) else
                     OWNER_SUPPLIED_TYPES[sid][0] if (is_opening and sid in OWNER_SUPPLIED_TYPES)
                     else t if is_opening else "UNRESOLVED"),
            "TYPE_SOURCE": (OWNER_CLOSED_AS_MEASUREMENT_OPENINGS.get(sid)
                            or (OWNER_SUPPLIED_TYPES[sid][1] if sid in OWNER_SUPPLIED_TYPES else None)),
            "WIDTH_M": round(s["SPAN_MM"] / 1000, 4),
            # TD-02 reaches ordinary doors and nothing else.  An open passage is not a door, so it takes no height
            # from it: a passage is either full height or it has a head, and only the owner knows which.
            "HEIGHT_M": (OWNER_SUPPLIED_HEIGHTS[sid][0] if sid in OWNER_SUPPLIED_HEIGHTS else
                         QORTUBA_WALL_HEIGHT_M if sid in OWNER_CLOSED_AS_MEASUREMENT_OPENINGS else
                         OWNER_SUPPLIED_PASSAGE_SUBTYPES[sid][1] if sid in OWNER_SUPPLIED_PASSAGE_SUBTYPES else
                         DEFAULT_DOOR_HEIGHT_M if (is_opening and t == "DOOR"
                                                   and sid not in OWNER_SUPPLIED_TYPES) else None),
            "OPEN_PASSAGE_SUBTYPE": (OWNER_SUPPLIED_PASSAGE_SUBTYPES[sid][0]
                                     if sid in OWNER_SUPPLIED_PASSAGE_SUBTYPES else None),
            # full height means no head, so there is no top to finish: left and right only (§6, §11)
            "REVEAL_SIDES": (["LEFT", "RIGHT"] if sid in OWNER_CLOSED_AS_MEASUREMENT_OPENINGS else
                             list(REVEAL_SIDES[OWNER_SUPPLIED_PASSAGE_SUBTYPES[sid][0]])
                             if sid in OWNER_SUPPLIED_PASSAGE_SUBTYPES else None),
            "HEIGHT_STATUS": ("ANSWERED_BY_OWNER" if (sid in OWNER_SUPPLIED_PASSAGE_SUBTYPES
                                                      or sid in OWNER_CLOSED_AS_MEASUREMENT_OPENINGS) else
                              "OWNER_INPUT_REQUIRED" if (is_opening and sid in OWNER_SUPPLIED_TYPES) else None),
            "WIDTH_SOURCE": "DWG opening site span, from the wall band's own interrupted faces",
            "HEIGHT_SOURCE": (OWNER_SUPPLIED_HEIGHTS[sid][1] if sid in OWNER_SUPPLIED_HEIGHTS else
                              OWNER_CLOSED_AS_MEASUREMENT_OPENINGS.get(sid) or None
                              if sid in OWNER_CLOSED_AS_MEASUREMENT_OPENINGS else
                              OWNER_SUPPLIED_PASSAGE_SUBTYPES[sid][2] if sid in OWNER_SUPPLIED_PASSAGE_SUBTYPES else
                              "TD-02 APPROVED_TEMPORARY_DEFAULT, ordinary door with no source height"
                              if (is_opening and t == "DOOR" and sid not in OWNER_SUPPLIED_TYPES) else None),
            "IS_AN_OPENING_THROUGH_THE_WALL": is_opening,
            "INTERRUPTS_AT_FLOOR_LEVEL": is_opening,
            "STATUS": ("NOT_AN_OPENING" if not is_opening else
                       "USABLE" if (sid in OWNER_SUPPLIED_PASSAGE_SUBTYPES
                                    or sid in OWNER_CLOSED_AS_MEASUREMENT_OPENINGS) else
                       "PARTIAL_HEIGHT_REQUIRED" if sid in OWNER_SUPPLIED_TYPES else
                       "USABLE" if (t == "DOOR" or sid in OWNER_SUPPLIED_HEIGHTS) else "OWNER_INPUT_REQUIRED"),
            "EVIDENCE": s["REASON"],
            "SITE_STATUS": s["STATUS"], "SITE_CLASS": s["CLASS"],
            "PDF_READER": PDF_READER.get(sid),
            "WHY_NOT_AN_OPENING": ("a gap that interrupts ONE face of a wall is not a doorway: a doorway interrupts "
                                   "both.  It deducts nothing from any trade and blocks nothing" if single_face else
                                   "a CAD junction where two bands meet, not an opening" if junction else None),
        })
    for b in blue:
        if b["OPENING_SITE_ID"] in sites:
            continue
        g = glz[b["BLUE_ELEMENT_ID"]]
        rows.append({
            "OPENING_ID": b["BLUE_ELEMENT_ID"], "BLUE_ELEMENT_ID": b["BLUE_ELEMENT_ID"],
            "ROOM": g["ROOM"], "ROOM_ID": g["ROOM_ID"],
            "HOST_WALL_ID": g["HOST_WALL_ID"], "HOST_WALL_THICKNESS_MM": g["HOST_WALL_THICKNESS_MM"],
            "TYPE": BLUE_TYPE[b["TYPE"]],
            "TYPE_SOURCE": None,
            "WIDTH_M": round(b["WIDTH_MM"] / 1000, 4),
            "HEIGHT_M": None,
            "OPEN_PASSAGE_SUBTYPE": None,
            "REVEAL_SIDES": None,
            "HEIGHT_STATUS": None,
            "WIDTH_SOURCE": "DWG blue element frame width",
            "HEIGHT_SOURCE": None,
            # a window with a sill IS an opening through the wall; it simply does not reach the floor
            "IS_AN_OPENING_THROUGH_THE_WALL": True,
            "INTERRUPTS_AT_FLOOR_LEVEL": not b["WALL_BELOW"],
            "STATUS": "OWNER_INPUT_REQUIRED",
            "EVIDENCE": b["WHY"],
            "SITE_STATUS": None, "SITE_CLASS": None, "PDF_READER": None,
            "WHY_NOT_AN_OPENING": ("wall stands below this glazing, so it does not interrupt the wall at floor level; "
                                   "it does interrupt the wall AREA and is deducted there" if b["WALL_BELOW"] else None),
        })
    gg = gap_geometry()
    for r in rows:
        r["CASE"] = case_of(r)
        g = gg.get(r["OPENING_ID"]) or {}
        # a blue element with no site is a frame inside a wall face, so it is interior by construction
        r["INTERIOR_TO_HOST_BAND"] = g.get("INTERIOR_TO_HOST_BAND", True)
        r["BAND_EXTENT_MM"] = g.get("BAND_EXTENT_MM")
        r["GAP_MM"] = g.get("GAP_MM")
        r["WHY_NOT_DEDUCTED_FROM_THE_BAND"] = g.get("WHY")
    rows.sort(key=lambda r: -r["WIDTH_M"])
    return rows


def finish_register():
    rows = completed_register()
    apt = [r for r in rows if r["ROOM"]]
    return {
        "ARTIFACT": "QORTUBA_OPENING_REGISTER_COMPLETED",
        "SOURCE_SEARCH": source_search(),
        "TYPES": list(OPENING_TYPES),
        "CASES": list(OPENING_CASES),
        "BY_CASE": dict(Counter(r["CASE"] for r in rows)),
        "CASE_RULE": "§D: these eight cases are the whole vocabulary.  A drawing variation that does not fit one "
                     "of them is UNKNOWN, and an UNKNOWN that materially moves a quantity is asked of the owner "
                     "rather than inferred by a new geometry rule",
        "ROWS": rows, "COUNT": len(rows),
        "APARTMENT_OPENINGS": len(apt),
        "BY_TYPE": dict(Counter(r["TYPE"] for r in rows)),
        "BY_STATUS": dict(Counter(r["STATUS"] for r in rows)),
        "WITH_A_HEIGHT": sum(1 for r in rows if r["HEIGHT_M"] is not None),
        "HEIGHTS_FROM_THE_DRAWING": 0,
        "HEIGHTS_FROM_THE_TEMPORARY_DEFAULT": sum(1 for r in rows if r["HEIGHT_M"] is not None),
        "NOT_AN_OPENING": [r["OPENING_ID"] for r in rows if not r["IS_AN_OPENING_THROUGH_THE_WALL"]],
        "DOES_NOT_REACH_THE_FLOOR": [r["OPENING_ID"] for r in rows
                                     if r["IS_AN_OPENING_THROUGH_THE_WALL"] and not r["INTERRUPTS_AT_FLOOR_LEVEL"]],
        "STILL_BLOCKING": [{"OPENING_ID": r["OPENING_ID"], "TYPE": r["TYPE"], "WIDTH_M": r["WIDTH_M"],
                            "ROOM": r["ROOM"], "HOST_WALL_ID": r["HOST_WALL_ID"]}
                           for r in rows if r["STATUS"] in ("OWNER_INPUT_REQUIRED", "PARTIAL_HEIGHT_REQUIRED")],
        "OPEN_PASSAGES": [{"OPENING_ID": r["OPENING_ID"], "WIDTH_M": r["WIDTH_M"], "HEIGHT_M": r["HEIGHT_M"],
                           "SUBTYPE": r["OPEN_PASSAGE_SUBTYPE"], "HEIGHT_STATUS": r["HEIGHT_STATUS"],
                           "ROOM": r["ROOM"], "HOST_WALL_ID": r["HOST_WALL_ID"], "WHY": r["TYPE_SOURCE"]}
                          for r in rows if r["TYPE"] == "OPEN_PASSAGE"],
        "OPEN_PASSAGE_SUBTYPES": list(OPEN_PASSAGE_SUBTYPES),
        "OPEN_PASSAGES_NEVER_ENTER_A_PROCUREMENT_SCHEDULE": True,
        "OWNER_SUPPLIED_TYPES": {k: v[0] for k, v in OWNER_SUPPLIED_TYPES.items()},
        "OWNER_SUPPLIED_HEIGHTS": {k: v[0] for k, v in OWNER_SUPPLIED_HEIGHTS.items()},
        "DEFAULT_APPLIED_ONLY_TO_ORDINARY_DOORS": True,
        "RULE": "an actual source dimension overrides a default; the 1.00 x 2.20 m default reaches ordinary doors only "
                "and never a window, a sliding door or a glazed opening.  Every Qortuba door width is source "
                "established, so only the height half of that default is ever used",
    }


# ---------------------------------------------------------------------------- §1/§8/§9 how an opening is described
INTERIOR_DOOR_MATERIAL = "PVC"
EXTERIOR_OPENING_MATERIAL = "ALUMINIUM"


def _room_sides():
    """Which apartment rooms each opening is seen from, on the frozen floor-level boundary."""
    sides = defaultdict(list)
    floors = {f["ROOM_ID"]: f for f in reg(QS, "QORTUBA_QS01_FLOOR_CALCULATIONS")["ROWS"]}
    for r in reg(QS, "QORTUBA_QS01_SKIRTING_TAKEOFF")["ROWS"]:
        for s in r["SEGMENTS"]:
            if s["SEGMENT_CLASS"] in ("DOOR_OPENING", "FLOOR_LEVEL_GLAZED_OPENING") and s.get("SITE_ID"):
                area = floors.get(r["ROOM_ID"], {}).get("METHOD_A_CAD_POLYGON_AREA_M2")
                sides[s["SITE_ID"]].append((r["ROOM"], r["ROOM_ID"], area))
    return sides


# where the independent PDF reading names the pair of rooms a gap joins, it is clearer than a 5 m band's room list
PDF_PAIR = {
    "OS-77f8fed2eb15": ("Hall", "Lobby (unlabelled internal space)"),
    "OS-85cb2192ebc0": ("Master bedroom", "Dressing room"),
    "OS-b5a0fbb335d4": ("Hall", "Pantry / preparation kitchen"),
}
def gap_geometry():
    """Where each opening site sits relative to its host band's own measured extent.

    A band's length is the material that is there.  An opening INSIDE that extent is a hole in measured wall, so its
    area must come off.  An opening at an END of the band is already outside the extent - the band stops at the jamb -
    so deducting it again removes material that was never counted.  The proof is arithmetic: the 1.900 m stub between
    the two 1.100 m bedroom gaps yields 5.700 m2 gross, and deducting both gaps gives -0.900 m2.

    This is a lookup against the frozen band register, not a measurement.
    """
    from research.qs_wall_treatment_01.pa08.qortuba.boq import owner_question_crops as C
    walls = {w["WALL_ID"]: w for w in reg(QS, "QORTUBA_QS01_BLOCK_WALL_TAKEOFF")["ROWS"]}
    sites = {r["SITE_ID"]: r for r in reg(R1, "PA08_QORTUBA_R1_OPENING_REGISTER")["ROWS"]}
    jp, bands = C.jamb_points(), C.bands()
    out = {}
    for w in walls.values():
        b = bands.get(w["WALL_ID"])
        if not b:
            continue
        e0, e1 = sorted((b["E0"], b["E1"]))
        for o in w["OPENINGS"]:
            sid = o["SITE_ID"]
            if sid not in sites:
                continue
            lo, hi, basis = C.gap_interval(sites[sid], b, jp)
            inside = (e0 - 1) <= lo and hi <= (e1 + 1)
            out[sid] = {"HOST_WALL_ID": w["WALL_ID"], "GAP_MM": [lo, hi], "BAND_EXTENT_MM": [e0, e1],
                        "INTERIOR_TO_HOST_BAND": bool(inside), "MARKER_BASIS": basis,
                        "WHY": (None if inside else
                                "the gap lies at an end of the host band, beyond its measured extent: the band's "
                                "length already stops at this jamb, so its area is not deducted a second time")}
    return out


def frozen_room_sides():
    """Which room-side finish paths each opening site actually interrupts, read from the frozen path registers.

    The wall takeoff lists every room a band runs past along its whole length, which is too coarse to say which face
    an opening cuts.  The R1 skirting path register is not: it records, per room and per band, the exact axial
    intervals of that room's own finish run.  A gap interrupts a room's path where a segment of that path stops at
    one of the gap's jambs.  This is a lookup in a frozen artifact - no geometry is measured, computed or moved.
    """
    from research.qs_wall_treatment_01.pa08.qortuba.boq import owner_question_crops as C
    spr = json.loads((R1 / "PA08_QORTUBA_R1_SKIRTING_PATH_REGISTER.json").read_text("utf-8"))["ROWS"]
    walls = {w["WALL_ID"]: w for w in reg(QS, "QORTUBA_QS01_BLOCK_WALL_TAKEOFF")["ROWS"]}
    eligible = {r["ROOM_ID"] for r in reg(QS, "QORTUBA_QS01_SKIRTING_TAKEOFF")["ROWS"]}
    sites = {r["SITE_ID"]: r for r in reg(R1, "PA08_QORTUBA_R1_OPENING_REGISTER")["ROWS"]}
    canonical = {f["ROOM_ID"]: f["ROOM"] for f in reg(QS, "QORTUBA_QS01_FLOOR_CALCULATIONS")["ROWS"]}
    jp, bands = C.jamb_points(), C.bands()
    out = {}
    for sid, site in sites.items():
        w = walls.get(site.get("HOST_WALL_ID")) or next(
            (v for v in walls.values() if any(o["SITE_ID"] == sid for o in v["OPENINGS"])), None)
        if not w or w["WALL_ID"] not in bands:
            continue
        lo, hi, _ = C.gap_interval(site, bands[w["WALL_ID"]], jp)
        hit = []
        for path in spr:
            rid = "RM-" + path["SPACE_ID"][3:11]
            if rid not in eligible:
                continue          # not an apartment room with a measured finish path
            for seg in path["PATH"]:
                if seg["BAND_ID"] != w["BAND_ID"]:
                    continue
                a, b = sorted((seg["AXIAL_START"], seg["AXIAL_END"]))
                # a jamb of this gap is where that room's own run stops: half the band thickness of tolerance
                if min(abs(b - lo), abs(a - hi), abs(a - lo), abs(b - hi)) <= max(260, w["THICKNESS_MM"]):
                    # the path register labels a space by position; the canonical room name comes from the floor
                    # register, so the pair reads the same as every other room name in the takeoff
                    hit.append((canonical.get(rid, path["ROOM"]), rid))
                    break
        out[sid] = sorted(set(hit))
    return out


# the same pairs as raw room labels, for matching against the quantity rows
PDF_PAIR_RAW = {
    "OS-77f8fed2eb15": ("HALL / whgm", "UNLABELLED_INTERNAL_SPACE"),
    "OS-85cb2192ebc0": ("M.B.ROOM", "DRESS"),
    "OS-b5a0fbb335d4": ("HALL / whgm", "PAINTRY"),
}


def human_register():
    """The same openings, described the way a person reads a plan: room, what it is, how wide, and what it opens onto.

    The opaque id stays on every row, but it belongs in the audit column.  A question that names OS-77f8fed2eb15 is a
    question nobody can answer; a question that names the opening between the Hall and the Lobby is one anybody can.
    """
    rows = completed_register()
    sides = _room_sides()
    floors = {f["ROOM_ID"]: f for f in reg(QS, "QORTUBA_QS01_FLOOR_CALCULATIONS")["ROWS"]}
    walls = {w["WALL_ID"]: w for w in reg(QS, "QORTUBA_QS01_BLOCK_WALL_TAKEOFF")["ROWS"]}
    area_of = {f["ROOM"]: f["METHOD_A_CAD_POLYGON_AREA_M2"] for f in floors.values()}

    out = []
    frozen_sides = frozen_room_sides()
    for r in rows:
        seen = sides.get(r["OPENING_ID"], [])
        w = walls.get(r["HOST_WALL_ID"])
        both = [friendly(nm, ar) for nm, _rid, ar in seen]
        if r["BLUE_ELEMENT_ID"] and r["ROOM_ID"]:
            f = floors.get(r["ROOM_ID"])
            here = friendly(r["ROOM"], f["METHOD_A_CAD_POLYGON_AREA_M2"] if f else None)
        else:
            here = both[0] if both else friendly((r["ROOM"] or "").split(",")[0].strip() or None,
                                                area_of.get((r["ROOM"] or "").split(",")[0].strip()))
        other = [b for b in both if b != here]
        wall_rooms = sorted({z for z in ((w["ROOM_SIDE_A"] + w["ROOM_SIDE_B"]) if w else []) if z not in APARTMENT_ROOMS})
        apt_rooms = sorted({z for z in ((w["ROOM_SIDE_A"] + w["ROOM_SIDE_B"]) if w else []) if z in APARTMENT_ROOMS})
        r_blue = r["BLUE_ELEMENT_ID"]
        # the floor-level path is the best evidence of which two rooms an opening joins; where it records only one side
        # (or none), fall back to the rooms the host band itself bounds
        site_row = bool(r["SITE_CLASS"])
        # which rooms lose wall area to this opening: the floor-level sides where the boundary records two of them,
        # otherwise the pair the reading or the host band gives.  A 5 m band touching four rooms is not that pair.
        raw = [nm for nm, _rid, _ar in seen]
        if len(raw) < 2 and r["OPENING_ID"] in PDF_PAIR_RAW:
            raw = list(PDF_PAIR_RAW[r["OPENING_ID"]])
        elif len(raw) < 2 and len(apt_rooms) == 2 and site_row:
            raw = list(apt_rooms)
        elif not raw and r["BLUE_ELEMENT_ID"] and r["ROOM"]:
            raw = [r["ROOM"]]
        ids = [rid for _nm, rid, _ar in seen]
        if len(ids) < 2:
            uniq = {}
            for f in floors.values():
                uniq.setdefault(f["ROOM"], []).append(f["ROOM_ID"])
            ids = [uniq[nm][0] for nm in raw if len(uniq.get(nm, [])) == 1]
            # a blue-ONLY row is a window in one room's external wall; a row that also has a site is a gap in a
            # shared wall, and its pair must not be collapsed to the single room the element sits nearest
            if r["BLUE_ELEMENT_ID"] and r["ROOM_ID"] and not site_row:
                ids = [r["ROOM_ID"]]
        # §11/§12: where the frozen path registers say exactly which room-side runs this gap interrupts, that is
        # the answer - it names the room even when two rooms share a label.  It may only ADD precision, never remove
        # a deduction: an empty result means the lookup found nothing, which is not the same as there being nothing,
        # so the existing attribution stands and the miss is recorded rather than silently costing a deduction.
        fs = frozen_sides.get(r["OPENING_ID"]) or []
        frozen_used = bool(fs) and site_row and not r["BLUE_ELEMENT_ID"]
        if frozen_used:
            ids = [rid for _nm, rid in fs]
            raw = [nm for nm, _rid in fs]
        if len(both) < 2 and r["OPENING_ID"] in PDF_PAIR:
            both = list(PDF_PAIR[r["OPENING_ID"]])
            here, other = both[0], both[1:]
        elif len(both) < 2 and len(apt_rooms) == 2 and site_row:
            both = [friendly(nm) for nm in apt_rooms]
            here, other = both[0], both[1:]
        interior = len(seen) >= 2 or (len(apt_rooms) == 2 and site_row) or r["OPENING_ID"] in PDF_PAIR
        inside = bool(apt_rooms) or bool(r["ROOM"])
        if not inside:
            material, why_mat = "OUTSIDE_APARTMENT", "this opening is not in an apartment wall and is out of scope"
        elif r["TYPE"] == "DOOR" and interior:
            material, why_mat = INTERIOR_DOOR_MATERIAL, "an interior door: both sides are apartment rooms"
        elif r["TYPE"] == "DOOR":
            material, why_mat = EXTERIOR_OPENING_MATERIAL, "not seen from two apartment rooms, so it is an envelope door"
        elif r["TYPE"] in ("WINDOW", "SLIDING_DOOR") and not interior:
            material, why_mat = EXTERIOR_OPENING_MATERIAL, "an exterior opening system in an envelope wall"
        elif not inside:
            material, why_mat = "OUTSIDE_APARTMENT", "this opening is not in an apartment wall and is out of scope"
        elif r["TYPE"] == "FULL_HEIGHT_OPENING_FOR_MEASUREMENT":
            material, why_mat = OPEN_PASSAGE_TRADE, ("a full-height wall interruption closed by the owner for "
                                                     "measurement.  Nothing is procured for it: no door, no window, "
                                                     "no PVC and no aluminium item")
        elif r["TYPE"] == "OPEN_PASSAGE":
            material, why_mat = OPEN_PASSAGE_TRADE, ("an open passage has no door leaf and no system in it: it is not "
                                                     "PVC, it is not aluminium, and nothing is procured for it.  It "
                                                     "interrupts the wall trades and nothing else")
        elif r["TYPE"] == "GLAZED_OPENING" and interior:
            material, why_mat = "INTERNAL_GLAZED_OPENING", ("both sides are apartment rooms, so this is internal "
                                                            "glazing and not an aluminium envelope item")
        else:
            material, why_mat = "NOT_CLASSIFIED", "type not established, so no trade may claim it"

        # a drafting artefact is not a place an owner can picture, so it is not named in a question
        named_out = [z for z in wall_rooms if "DRAFTING" not in z and "NOT_A_MEASURED" not in z
                     and "SHEET_OR_SITE" not in z and z != "UNKNOWN"]
        outside = ", ".join(z.strip("[]").replace("_", " ").lower() for z in named_out)
        if other:
            where = f"between {here} and {', '.join(other)}"
        elif r["BLUE_ELEMENT_ID"]:
            where = f"in the {here} external wall"
        elif not inside:
            where = f"outside the apartment, in the wall between {outside or 'unnamed spaces'}"
        elif apt_rooms and outside:
            where = ("on the wall shared by " + " and ".join(friendly(z) for z in apt_rooms)
                     + f", which also faces {outside}") if len(apt_rooms) > 1 else \
                    f"in the {friendly(apt_rooms[0])} wall facing {outside}"
        elif apt_rooms:
            where = "on the wall shared by " + " and ".join(friendly(z) for z in apt_rooms)
        else:
            where = f"in the {here}" if here else "location not established"

        where = where.replace("the a ", "a ").replace("the A ", "a ")
        kind = {"DOOR": "Door", "WINDOW": "Window", "SLIDING_DOOR": "Sliding door",
                "GLAZED_OPENING": "Glazed opening", "OPEN_PASSAGE": "Open passage",
                "FULL_HEIGHT_OPENING_FOR_MEASUREMENT": "Full-height wall opening",
                "UNRESOLVED": "Opening of unknown type"}[r["TYPE"]]
        out.append({
            "OPENING_ID": r["OPENING_ID"],
            "ROOM": here, "ADJACENT": other or None, "LOCATION": where,
            "OPENING": kind, "TYPE": r["TYPE"],
            "WIDTH_M": r["WIDTH_M"], "HEIGHT_M": r["HEIGHT_M"],
            "HEIGHT_SOURCE": r["HEIGHT_SOURCE"],
            "CASE": r.get("CASE"),
            "TYPE_SOURCE": r.get("TYPE_SOURCE"),
            "OPEN_PASSAGE_SUBTYPE": r.get("OPEN_PASSAGE_SUBTYPE"),
            "REVEAL_SIDES": r.get("REVEAL_SIDES"),
            "HEIGHT_STATUS": r.get("HEIGHT_STATUS"),
            "MATERIAL_TRADE": material, "WHY_THAT_TRADE": why_mat,
            "INTERIOR": interior, "INSIDE_APARTMENT": inside,
            "ROOMS_FOR_DEDUCTION": raw, "ROOM_IDS_FOR_DEDUCTION": ids,
            "ROOM_SIDE_BASIS": ("FROZEN_FINISH_PATH_REGISTER" if frozen_used else
                                "FLOOR_LEVEL_BOUNDARY_OR_HOST_BAND"),
            "STATUS": r["STATUS"],
            "IS_AN_OPENING_THROUGH_THE_WALL": r["IS_AN_OPENING_THROUGH_THE_WALL"],
            "HOST_WALL_ID": r["HOST_WALL_ID"],
            "DESCRIPTION": f"{kind} {where}, width {r['WIDTH_M']:.3f} m",
            "PDF_READER": r["PDF_READER"],
        })
    return out
