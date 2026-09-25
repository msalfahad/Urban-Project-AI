"""Which room is this opening in, and therefore which standard applies to it?

A standard that gives a window height by room use is useless until the room is known.  R5 handed every window
the same category, so one number answered a bedroom, a kitchen, a hall and a bathroom - and the fact that it was
drawn from an approved guide made it look evidenced.  A project-wide default is not a resolution; it is a guess
wearing a citation.

So the room is resolved from geometry, its label is read from the source, and only then is a category looked up
in a mapping the CALLER supplies.  The engine holds no label vocabulary: which words a drawing uses for its
rooms is a property of the drawing, and a mapping written into the engine would be one project's dictionary
imposed on the next.  Where the room or the category cannot be resolved, the height is a question and the width
is published on its own.
"""

from __future__ import annotations

from engine.qs_core import evidence as EV, geom

ROOM_RESOLVED = "HOST_ROOM_RESOLVED"
ROOM_AMBIGUOUS = "HOST_ROOM_AMBIGUOUS"
ROOM_NOT_FOUND = "HOST_ROOM_NOT_FOUND"

CATEGORY_RESOLVED = "CATEGORY_RESOLVED"
CATEGORY_UNMAPPED = "CATEGORY_NOT_IN_THE_MAPPING"
CATEGORY_NO_ROOM = "CATEGORY_UNRESOLVED_BECAUSE_THE_ROOM_IS"

# What a space IS, for the purpose of deciding whether a room-use standard can be read from it.  A window
# normally separates an occupied room from the outside; the standard belongs to the occupied side.  Which of
# a drawing's labels mean "outside" is a property of the drawing, so the CALLER classifies - the engine only
# knows that the two kinds behave differently.
ENCLOSED_ROOM = "ENCLOSED_ROOM"
EXTERNAL_OR_OPEN = "EXTERNAL_OR_OPEN_AREA"
ROLE_UNKNOWN = "SPACE_ROLE_UNKNOWN"

SIDE_A, SIDE_B = "SIDE_A", "SIDE_B"


def _side_of(candidate, space, axis):
    """Which side of the opening's own wall line this space lies on, along the wall's normal."""
    cx, cy = candidate.centre
    here = cy if axis == geom.AXIS_X else cx          # the wall's normal is across its axis
    above = below = 0.0
    for r in space.rects:
        lo, hi = (r.y0, r.y1) if axis == geom.AXIS_X else (r.x0, r.x1)
        mid = (lo + hi) / 2.0
        area = (r.x1 - r.x0) * (r.y1 - r.y0)
        if mid >= here:
            above += area
        else:
            below += area
    if above == below:
        return None
    return SIDE_B if above > below else SIDE_A


def resolve_host_room(candidate, spaces, tolerance, space_role=None):
    """The room whose USE decides this opening's standard, from the two sides of the wall it sits in.

    An opening separates what is on one side of its wall from what is on the other.  Reading the room off
    whichever labelled polygon happens to be nearest ignores that entirely: on this drawing it let an external
    roof terrace compete on equal terms with the bedroom on the other side of the glass, and three windows
    were reported ambiguous because the two sides were a few centimetres apart in distance.

    So the sides are separated first, using the host wall's own axis and normal, and then classified.  One
    enclosed room facing one external or open area is not an ambiguity - it is the ordinary external window,
    and the standard belongs to the enclosed side.  Two enclosed rooms genuinely is an ambiguity.  The
    classification comes from the caller, because which of a drawing's words mean "outside" is the drawing's
    business and not the engine's.
    """
    cx, cy = candidate.centre
    axis = candidate.axis or (geom.AXIS_X if abs(candidate.span) else geom.AXIS_X)
    reach = max(candidate.span, (candidate.depth or 0.0) * 2.0, tolerance * 20)
    role_of = space_role or (lambda _s: ROLE_UNKNOWN)

    near = []
    for s in spaces:
        if s.floor != candidate.floor or not s.rects:
            continue
        d = min(geom.distance_point_to_rect(cx, cy, r) for r in s.rects)
        if d <= reach:
            near.append((round(d, 6), s))
    near.sort(key=lambda t: (t[0], t[1].room_id))

    published = []
    for d, s in near:
        published.append({"ROOM_ID": s.room_id, "LABEL": s.label, "LABEL_STATUS": s.label_status,
                          "AREA_M2": round(s.area, 6), "DISTANCE_M": d,
                          "SIDE": _side_of(candidate, s, axis), "ROLE": role_of(s)})
    sides = {SIDE_A: [r for r in published if r["SIDE"] == SIDE_A],
             SIDE_B: [r for r in published if r["SIDE"] == SIDE_B],
             None: [r for r in published if r["SIDE"] is None]}
    geometry = {"WALL_AXIS": axis, "OPENING_CENTRE": [cx, cy], "REACH_M": round(reach, 6),
                "SIDES": {k or "ASTRIDE_THE_WALL": [r["ROOM_ID"] for r in v] for k, v in sides.items()}}

    if not near:
        return {"STATUS": ROOM_NOT_FOUND, "ROOM_ID": None, "LABEL": None, "AREA_M2": None,
                "CANDIDATES": published, "REACH_M": round(reach, 6), "GEOMETRY": geometry,
                "WHY": "no space lies within this opening's own extent of it"}

    labelled = [r for r in published if r["LABEL"]]
    if not labelled:
        return {"STATUS": ROOM_NOT_FOUND, "ROOM_ID": near[0][1].room_id, "LABEL": None,
                "AREA_M2": round(near[0][1].area, 6), "CANDIDATES": published,
                "REACH_M": round(reach, 6), "GEOMETRY": geometry,
                "WHY": "the spaces around this opening carry no label the source states"}

    enclosed = [r for r in labelled if r["ROLE"] == ENCLOSED_ROOM]
    external = [r for r in labelled if r["ROLE"] == EXTERNAL_OR_OPEN]
    unknown = [r for r in labelled if r["ROLE"] not in (ENCLOSED_ROOM, EXTERNAL_OR_OPEN)]

    def resolved(row, why):
        return {"STATUS": ROOM_RESOLVED, "ROOM_ID": row["ROOM_ID"], "LABEL": row["LABEL"],
                "AREA_M2": row["AREA_M2"], "DISTANCE_M": row["DISTANCE_M"], "SIDE": row["SIDE"],
                "ROLE": row["ROLE"], "CANDIDATES": published, "REACH_M": round(reach, 6),
                "GEOMETRY": geometry, "WHY": why}

    # the ordinary external window: occupied room one side, open air the other
    if len(enclosed) == 1 and not unknown:
        return resolved(enclosed[0],
                        ("one enclosed room and %d external or open area(s) meet at this opening; the "
                         "room-use standard belongs to the enclosed side" % len(external))
                        if external else
                        "exactly one enclosed room is within reach of this opening")
    if len(enclosed) > 1:
        return {"STATUS": ROOM_AMBIGUOUS, "ROOM_ID": None, "LABEL": None, "AREA_M2": None,
                "CANDIDATES": published, "REACH_M": round(reach, 6), "GEOMETRY": geometry,
                "WHY": f"{len(enclosed)} enclosed rooms meet at this opening; which room's use applies is "
                       "not decidable from geometry alone"}
    if enclosed and unknown:
        return {"STATUS": ROOM_AMBIGUOUS, "ROOM_ID": None, "LABEL": None, "AREA_M2": None,
                "CANDIDATES": published, "REACH_M": round(reach, 6), "GEOMETRY": geometry,
                "WHY": "one enclosed room and %d space(s) the source does not classify meet at this opening; "
                       "an unclassified space is not evidence that the enclosed side is the only one"
                       % len(unknown)}
    if external and not enclosed and not unknown:
        return {"STATUS": ROOM_NOT_FOUND, "ROOM_ID": None, "LABEL": None, "AREA_M2": None,
                "CANDIDATES": published, "REACH_M": round(reach, 6), "GEOMETRY": geometry,
                "WHY": "every space at this opening is external or open; a room-use standard needs an "
                       "occupied room and there is none"}

    # nothing classified: fall back to the label evidence alone, and say so
    if len(labelled) == 1:
        return resolved(labelled[0],
                        "exactly one named space is within reach, and the source classifies no space here")
    return {"STATUS": ROOM_AMBIGUOUS, "ROOM_ID": None, "LABEL": None, "AREA_M2": None,
            "CANDIDATES": published, "REACH_M": round(reach, 6), "GEOMETRY": geometry,
            "WHY": f"{len(labelled)} named spaces are within reach and the source classifies none of them as "
                   "enclosed or external, so the side that owns the standard cannot be identified"}


def category_for(room, mapping, resolver=None):
    """Look the room's own evidence up in the caller's mapping.  No default, and no fallback category."""
    if room["STATUS"] != ROOM_RESOLVED:
        return {"STATUS": f"{CATEGORY_NO_ROOM}_{room['STATUS']}", "CATEGORY": None, "SOURCE": None,
                "ROOM": room, "WHY": room["WHY"]}
    label, area = room["LABEL"], room["AREA_M2"]
    if resolver is not None:
        category, how = resolver(label, area)
        if category:
            return {"STATUS": CATEGORY_RESOLVED, "CATEGORY": category, "SOURCE": how, "ROOM": room,
                    "WHY": f"the source calls this room {label!r}, which the mapping resolves to {category} "
                           f"by {how}"}
        return {"STATUS": CATEGORY_UNMAPPED, "CATEGORY": None, "SOURCE": how, "ROOM": room,
                "WHY": f"the source calls this room {label!r} and the mapping does not cover it"}
    if label in (mapping or {}):
        return {"STATUS": CATEGORY_RESOLVED, "CATEGORY": mapping[label], "SOURCE": "EXPLICIT_LABEL_MAP",
                "ROOM": room,
                "WHY": f"the source calls this room {label!r}, which the mapping resolves directly"}
    return {"STATUS": CATEGORY_UNMAPPED, "CATEGORY": None, "SOURCE": None, "ROOM": room,
            "WHY": f"the source calls this room {label!r} and the mapping does not cover it"}


def standard_claim(category_record, table, reference, what="height"):
    """Turn a resolved category into an evidence claim at guide rank, carrying its own provenance.

    The claim is scoped to the opening it was resolved for, so it cannot drift onto another one, and it ranks
    where a guide ranks - below anything the drawing or the owner states for this object.
    """
    if category_record["STATUS"] != CATEGORY_RESOLVED:
        return None
    row = (table or {}).get(category_record["CATEGORY"])
    if not row:
        return None
    value = row.get("H") if what == "height" else row.get("W")
    if value is None:
        return None
    return EV.Claim(value, EV.APPROVED_GUIDE, f"{reference}::{category_record['CATEGORY']}",
                    {"WHAT": f"{what} for a {category_record['CATEGORY']} in the applicable standard",
                     "ROOM_ID": category_record["ROOM"]["ROOM_ID"],
                     "ROOM_LABEL": category_record["ROOM"]["LABEL"],
                     "CATEGORY_SOURCE": category_record["SOURCE"],
                     "MAPPING_PROVENANCE": category_record["WHY"]})


def build_register(records):
    """The register of what each opening's room and category turned out to be, and why."""
    rows = sorted(records, key=lambda r: r["OPENING_REF"])
    resolved = [r for r in rows if r["CATEGORY"]["STATUS"] == CATEGORY_RESOLVED]
    categories = sorted({r["CATEGORY"]["CATEGORY"] for r in resolved})
    return {
        "REGISTER": rows,
        "OPENINGS": len(rows),
        "CATEGORY_RESOLVED": len(resolved),
        "CATEGORY_UNRESOLVED": len(rows) - len(resolved),
        "DISTINCT_CATEGORIES": categories,
        "DISTINCT_CATEGORY_COUNT": len(categories),
        "DISTINCT_ROOMS": sorted({r["ROOM"]["ROOM_ID"] for r in rows if r["ROOM"]["ROOM_ID"]}),
        "RULE": "a category comes from the host room's own label, through a mapping the caller supplies.  "
                "There is no project-wide default: an opening whose room or category is unresolved publishes "
                "its width and leaves its height a question",
        "STATUSES": [ROOM_RESOLVED, ROOM_AMBIGUOUS, ROOM_NOT_FOUND, CATEGORY_RESOLVED, CATEGORY_UNMAPPED],
    }
