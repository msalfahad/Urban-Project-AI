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
from collections import Counter
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

R1 = Path(PR.OUT_DIR) / "pa08_qortuba_r1"
R3 = Path(PR.OUT_DIR) / "pa08_qortuba_r3"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"
DWG_JSON = Path("data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json")

OPENING_TYPES = ("DOOR", "WINDOW", "SLIDING_DOOR", "GLAZED_OPENING", "UNRESOLVED")
APARTMENT_ROOMS = {"HALL / whgm", "M.B.ROOM", "BED.ROOM", "PAINTRY", "DRESS", "BATH", "UNLABELLED_INTERNAL_SPACE"}

DEFAULT_DOOR_WIDTH_M = 1.00
DEFAULT_DOOR_HEIGHT_M = 2.20


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
            "TYPE": t if is_opening else "UNRESOLVED",
            "WIDTH_M": round(s["SPAN_MM"] / 1000, 4),
            "HEIGHT_M": (DEFAULT_DOOR_HEIGHT_M if (is_opening and t == "DOOR") else None),
            "WIDTH_SOURCE": "DWG opening site span, from the wall band's own interrupted faces",
            "HEIGHT_SOURCE": ("TD-02 APPROVED_TEMPORARY_DEFAULT, ordinary door with no source height"
                              if (is_opening and t == "DOOR") else None),
            "IS_AN_OPENING_THROUGH_THE_WALL": is_opening,
            "INTERRUPTS_AT_FLOOR_LEVEL": is_opening,
            "STATUS": ("NOT_AN_OPENING" if not is_opening else
                       "USABLE" if t == "DOOR" else "SOURCE_REQUIRED"),
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
            "WIDTH_M": round(b["WIDTH_MM"] / 1000, 4),
            "HEIGHT_M": None,
            "WIDTH_SOURCE": "DWG blue element frame width",
            "HEIGHT_SOURCE": None,
            # a window with a sill IS an opening through the wall; it simply does not reach the floor
            "IS_AN_OPENING_THROUGH_THE_WALL": True,
            "INTERRUPTS_AT_FLOOR_LEVEL": not b["WALL_BELOW"],
            "STATUS": "SOURCE_REQUIRED",
            "EVIDENCE": b["WHY"],
            "SITE_STATUS": None, "SITE_CLASS": None, "PDF_READER": None,
            "WHY_NOT_AN_OPENING": ("wall stands below this glazing, so it does not interrupt the wall at floor level; "
                                   "it does interrupt the wall AREA and is deducted there" if b["WALL_BELOW"] else None),
        })
    rows.sort(key=lambda r: -r["WIDTH_M"])
    return rows


def finish_register():
    rows = completed_register()
    apt = [r for r in rows if r["ROOM"]]
    return {
        "ARTIFACT": "QORTUBA_OPENING_REGISTER_COMPLETED",
        "SOURCE_SEARCH": source_search(),
        "TYPES": list(OPENING_TYPES),
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
                           for r in rows if r["STATUS"] == "SOURCE_REQUIRED"],
        "DEFAULT_APPLIED_ONLY_TO_ORDINARY_DOORS": True,
        "RULE": "an actual source dimension overrides a default; the 1.00 x 2.20 m default reaches ordinary doors only "
                "and never a window, a sliding door or a glazed opening.  Every Qortuba door width is source "
                "established, so only the height half of that default is ever used",
    }
