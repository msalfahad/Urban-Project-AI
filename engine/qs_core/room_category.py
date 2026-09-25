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


def resolve_host_room(candidate, spaces, tolerance):
    """The space the opening opens into, from the geometry of both.

    An opening in an external wall faces one internal space; an opening in a partition faces two, and that is
    an ambiguity to report rather than a coin to toss.  Distance is measured from the opening's own centre, so
    this works whether or not the opening has a resolved depth.
    """
    cx, cy = candidate.centre
    reach = max(candidate.span, (candidate.depth or 0.0) * 2.0, tolerance * 20)
    near = []
    for s in spaces:
        if s.floor != candidate.floor or not s.rects:
            continue
        d = min(geom.distance_point_to_rect(cx, cy, r) for r in s.rects)
        if d <= reach:
            near.append((round(d, 6), s))
    near.sort(key=lambda t: (t[0], t[1].room_id))

    published = [{"ROOM_ID": s.room_id, "LABEL": s.label, "LABEL_STATUS": s.label_status,
                  "AREA_M2": round(s.area, 6), "DISTANCE_M": d} for d, s in near]
    if not near:
        return {"STATUS": ROOM_NOT_FOUND, "ROOM_ID": None, "LABEL": None, "AREA_M2": None,
                "CANDIDATES": published, "REACH_M": round(reach, 6),
                "WHY": "no space lies within this opening's own extent of it"}
    labelled = [(d, s) for d, s in near if s.label]
    if len(labelled) == 1:
        d, s = labelled[0]
        return {"STATUS": ROOM_RESOLVED, "ROOM_ID": s.room_id, "LABEL": s.label,
                "AREA_M2": round(s.area, 6), "DISTANCE_M": d, "CANDIDATES": published,
                "REACH_M": round(reach, 6),
                "WHY": "exactly one named space is within reach of this opening"}
    if not labelled:
        return {"STATUS": ROOM_NOT_FOUND, "ROOM_ID": near[0][1].room_id, "LABEL": None,
                "AREA_M2": round(near[0][1].area, 6), "CANDIDATES": published,
                "REACH_M": round(reach, 6),
                "WHY": "the spaces around this opening carry no label the source states"}
    return {"STATUS": ROOM_AMBIGUOUS, "ROOM_ID": None, "LABEL": None, "AREA_M2": None,
            "CANDIDATES": published, "REACH_M": round(reach, 6),
            "WHY": f"{len(labelled)} named spaces are within reach and the opening faces more than one of "
                   "them; which room's standard applies is not decidable from geometry alone"}


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
