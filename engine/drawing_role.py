"""What does this drawing region actually SHOW — and of which floor?

Round 6B measured 69 polygons and called them geometry. Seven of them were
whole-sheet faces of 50 to 1,072 m2, five were the same 28.27 m2 strip
repeated once in every region, and nothing in the engine could say that a
region might be an elevation, a detail or a title block rather than a
floor plan. A room quantity taken from an elevation is not a small error.

So before any room is measured, each region is asked two questions:

    WHAT DOES IT SHOW      plan, roof, site, elevation, section, detail...
    WHICH FLOOR            and the honest answer is often that nobody said

**P7757 CARRIES NO TITLE TEXT AT ALL.** Its 89 decoded strings are room
stamps, level marks, 'NEIGHBOUR', 'STREET' and 'SEA VIEW'. There is no
'GROUND FLOOR PLAN' to read, because the sheet's titles are drawn in an
SHX font this decoder does not resolve. That is a fact about the source,
not a gap in effort, and it is why `floor_level` on this drawing is
`FLOOR_LEVEL_NOT_ESTABLISHED` from the drawing alone.

A SUPERVISED FLOOR ASSIGNMENT MAY BE SUPPLIED, and it is then carried as
supplied — `provenance = SUPERVISED_AUDIT`, never `DERIVED_FROM_DRAWING`.
No region id is hardcoded anywhere in this module: an assignment arrives
as data, keyed on what the region IS, and a region that no assignment
names keeps the honest answer.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

MODEL = "DRAWING_REGION_ROLE_AND_FLOOR_V1"

# --- §3 the roles --------------------------------------------------------
FLOOR_PLAN = "FLOOR_PLAN"
ROOF_PLAN = "ROOF_PLAN"
SITE_PLAN = "SITE_PLAN"
AREA_DIAGRAM = "AREA_DIAGRAM"
ELEVATION = "ELEVATION"
SECTION = "SECTION"
DETAIL = "DETAIL"
SCHEDULE = "SCHEDULE"
UNKNOWN = "UNKNOWN"

ROLES = (FLOOR_PLAN, ROOF_PLAN, SITE_PLAN, AREA_DIAGRAM, ELEVATION,
         SECTION, DETAIL, SCHEDULE, UNKNOWN)

# Only these may produce a room quantity. UNKNOWN may not: a region nobody
# has identified is not a floor plan by default. A ROOF PLAN is included
# because on this building type the roof carries habitable rooms — and a
# roof plan that encloses rooms IS the plan of that level.
BOQ_ELIGIBLE_ROLES = (FLOOR_PLAN, ROOF_PLAN)

FLOOR_NOT_ESTABLISHED = "FLOOR_LEVEL_NOT_ESTABLISHED"

DERIVED = "DERIVED_FROM_THE_DRAWING"
SUPERVISED = "SUPERVISED_AUDIT"

# --- the evidence, all of it structural ----------------------------------
EV_ENCLOSED_SPACES = "IT_ENCLOSES_SPACES_WITH_WALL_BANDS"
EV_OPENINGS = "DOORS_AND_WINDOWS_ARE_DRAWN_IN_THOSE_WALLS"
EV_ROOM_STAMPS = "ROOM_NAMES_ARE_STAMPED_INSIDE_THOSE_SPACES"
EV_NO_ENCLOSURE = "NOTHING_IN_IT_IS_ENCLOSED"
EV_NO_OPENING = "NO_OPENING_IS_DRAWN_ANYWHERE_IN_IT"
EV_SITE_BOUNDARY = "A_SITE_BOUNDARY_ENCLOSES_THE_FABRIC"
EV_SMALL_EXTENT = "ITS_EXTENT_IS_A_SMALL_FRACTION_OF_THE_PLAN_REGIONS"
EV_TITLE_TEXT = "ITS_OWN_TITLE_TEXT_SAYS_SO"
EV_NO_TITLE_TEXT = "NO_TITLE_TEXT_IN_THIS_DRAWING_DECODES"

EVIDENCE = (EV_ENCLOSED_SPACES, EV_OPENINGS, EV_ROOM_STAMPS,
            EV_NO_ENCLOSURE, EV_NO_OPENING, EV_SITE_BOUNDARY,
            EV_SMALL_EXTENT, EV_TITLE_TEXT, EV_NO_TITLE_TEXT)

# A region whose extent is under this share of the largest region's is not
# a plan of the same building. It is a fraction of the drawing's OWN
# largest region, never a millimetre figure.
DETAIL_EXTENT_SHARE = 0.1

# Words that name what a drawing shows, in the two languages this project
# reads. Matched only against text that is LARGER than the room stamps in
# the same region — a title is drawn bigger than a room name.
TITLE_WORDS = {
    FLOOR_PLAN: ("FLOOR PLAN", "GROUND FLOOR", "FIRST FLOOR",
                 "SECOND FLOOR", "TYPICAL FLOOR", "PLAN"),
    ROOF_PLAN: ("ROOF PLAN", "ROOF"),
    SITE_PLAN: ("SITE PLAN", "SITE", "LOCATION PLAN"),
    ELEVATION: ("ELEVATION", "FRONT ELEVATION", "SIDE ELEVATION"),
    SECTION: ("SECTION", "CROSS SECTION"),
    DETAIL: ("DETAIL", "TYPICAL DETAIL"),
    SCHEDULE: ("SCHEDULE", "DOOR SCHEDULE", "WINDOW SCHEDULE"),
    AREA_DIAGRAM: ("AREA", "AREA DIAGRAM", "AREA STATEMENT"),
}

FLOOR_WORDS = (
    ("GROUND FLOOR", "GROUND"),
    ("FIRST FLOOR", "FIRST"),
    ("SECOND FLOOR", "SECOND"),
    ("ROOF", "ROOF"),
    ("BASEMENT", "BASEMENT"),
    ("MEZZANINE", "MEZZANINE"),
)


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "ROLES": list(ROLES),
        "BOQ_ELIGIBLE_ROLES": list(BOQ_ELIGIBLE_ROLES),
        "EVIDENCE": list(EVIDENCE),
        "DETAIL_EXTENT_SHARE": DETAIL_EXTENT_SHARE,
        "why": {
            "a_floor_is_required_too": (
                "an eligible role is not enough. A region whose floor "
                "nobody established contributes to no floor register, "
                "because a room that belongs to no storey cannot be "
                "reconciled against anything"),
            "unknown_is_not_a_floor_plan": (
                "only a region established as a FLOOR_PLAN may produce a "
                "room quantity. A region nobody has identified produces "
                "none, which is the whole point of asking"),
            "no_region_id_is_hardcoded": (
                "a supervised assignment arrives as DATA keyed on what a "
                "region is. This module contains no project's region ids"),
            "a_title_is_bigger_than_a_room_name": (
                "title text is matched only above the height this region "
                "REPEATS — its body text — so a room called PLAN ROOM "
                "cannot retitle a drawing, and the title is not excluded "
                "for being the tallest string in its own region"),
            "extent_is_a_share_not_a_size": (
                "a detail is small RELATIVE to this drawing's own largest "
                "region. No millimetre figure decides it"),
        },
    }


def model_hash() -> str:
    parts = ([MODEL] + list(ROLES) + list(EVIDENCE)
             + [DERIVED, SUPERVISED, FLOOR_NOT_ESTABLISHED,
                str(DETAIL_EXTENT_SHARE)])
    for role, words in sorted(TITLE_WORDS.items()):
        parts.append(role + "=" + "|".join(words))
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


@dataclass
class RegionRole:
    region_id: str = ""
    drawing_role: str = UNKNOWN
    floor_level: str = FLOOR_NOT_ESTABLISHED
    role_provenance: str = DERIVED
    floor_provenance: str = DERIVED
    title_evidence: tuple = ()
    evidence: tuple = ()
    confidence: str = "NOT_ESTABLISHED"
    extent_mm: tuple = ()
    counts: dict = field(default_factory=dict)
    why: str = ""

    @property
    def may_release_rooms(self) -> bool:
        """An eligible role AND a floor to put the rooms on.

        A region whose floor nobody has established cannot contribute to
        any floor's register: its rooms would belong to no storey, and a
        quantity that belongs to no storey cannot be checked against
        anything.
        """
        return (self.drawing_role in BOQ_ELIGIBLE_ROLES
                and self.floor_level != FLOOR_NOT_ESTABLISHED)

    def record(self) -> dict:
        return {
            "drawing_region_id": self.region_id,
            "drawing_role": self.drawing_role,
            "floor_level": self.floor_level,
            "role_provenance": self.role_provenance,
            "floor_provenance": self.floor_provenance,
            "drawing_title_evidence": list(self.title_evidence),
            "plan_section_elevation_evidence": list(self.evidence),
            "confidence": self.confidence,
            "extent_mm": [round(v, 1) for v in self.extent_mm],
            "counts": dict(self.counts),
            "may_release_room_quantities": self.may_release_rooms,
            "why": self.why,
        }


@dataclass
class RoleReport:
    roles: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def of(self, region_id: str) -> RegionRole:
        for r in self.roles:
            if r.region_id == region_id:
                return r
        return RegionRole(region_id=region_id)

    def counts(self) -> dict:
        return {
            "regions": len(self.roles),
            "by_role": dict(Counter(r.drawing_role
                                    for r in self.roles).most_common()),
            "by_floor": dict(Counter(r.floor_level
                                     for r in self.roles).most_common()),
            "may_release_room_quantities": sum(
                1 for r in self.roles if r.may_release_rooms),
            "floor_established": sum(
                1 for r in self.roles
                if r.floor_level != FLOOR_NOT_ESTABLISHED),
        }

    def record(self) -> dict:
        return {
            "model": MODEL,
            "DRAWING_ROLE_HASH": model_hash(),
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "regions": [r.record() for r in self.roles],
            "notes": dict(self.notes),
        }


def _stamp_height(texts) -> float:
    """The height this DRAWING repeats — its body text.

    Not the tallest string, which is the title itself, and not the mean,
    which one big string moves. The most common height on the sheet is
    its room stamps and its notes; a title is drawn bigger than that.

    It is measured over the whole drawing rather than one region because
    a region may hold nothing but its own title — an elevation with no
    room in it — and a title compared only against itself is never taller
    than itself. Where a sheet's body text and its titles are the same
    height, no title is read at all, which is the honest answer.
    """
    heights = Counter(round(t.height, 1) for t in texts if t.height)
    if not heights:
        return 0.0
    top = max(heights.values())
    return min(h for h, n in heights.items() if n == top)


def _points(stamps) -> list:
    """The (x, y) of every room stamp handed in for a region, if any.

    A caller may hand in strings — and a string has no position, so it
    excludes nothing. An observation excludes itself.
    """
    out = []
    for s in stamps or ():
        x, y = getattr(s, "x", None), getattr(s, "y", None)
        if x is not None and y is not None:
            out.append((x, y))
    return out


def _title_hits(texts, stamp_height: float, stamped=()) -> list:
    """Text that titles the drawing rather than naming a room in it.

    Two independent things have to be true of it. It is NOT one of this
    region's room stamps — a room called PLAN ROOM names a room, and a
    drawing is not retitled by what is inside it — and it is drawn at
    least as big as the text this sheet repeats.

    Where a string matches words belonging to several roles, the LONGEST
    matched word wins: 'SITE PLAN' is a site plan and not a plan, even
    though 'PLAN' is inside it.
    """
    at = {(round(x, 1), round(y, 1)) for x, y in stamped}
    out = []
    for t in texts:
        if (round(t.x, 1), round(t.y, 1)) in at:
            continue
        if stamp_height and t.height < stamp_height:
            continue
        value = (t.value or "").strip().upper()
        if not value:
            continue
        best = None
        for role, words in TITLE_WORDS.items():
            for w in words:
                if w in value and (best is None or len(w) > len(best[1])):
                    best = (role, w)
        if best is not None:
            out.append((best[0], t.value.strip(), t.height))
    return out


def _floor_from(title_hits) -> str:
    for _role, value, _h in title_hits:
        up = value.upper()
        for phrase, level in FLOOR_WORDS:
            if phrase in up:
                return level
    return FLOOR_NOT_ESTABLISHED


def classify(regions, *, texts=(), spaces_by_region=None,
             openings_by_region=None, bands_by_region=None,
             sites_by_region=None, stamps_by_region=None,
             supervised=None) -> RoleReport:
    """Say what each region shows, and refuse to guess the floor.

    `supervised` is an optional mapping of region id to a declared floor
    and role. It is DATA, it is recorded as SUPERVISED_AUDIT, and nothing
    in this module knows any project's region ids without it.
    """
    rep = RoleReport()
    spaces = spaces_by_region or {}
    openings = openings_by_region or {}
    bands = bands_by_region or {}
    sites = sites_by_region or {}
    stamps = stamps_by_region or {}
    given = dict(supervised or {})

    body_h = _stamp_height(texts)
    extents = {r.region_id: (r.x1 - r.x0) * (r.y1 - r.y0) for r in regions}
    biggest = max(extents.values()) if extents else 0.0
    any_title = False

    for reg in regions:
        rid = reg.region_id
        mine = [t for t in texts if reg.contains(t.x, t.y)]
        stamp_h = body_h
        hits = _title_hits(mine, stamp_h, _points(stamps.get(rid, ())))
        if hits:
            any_title = True
        n_space = len(spaces.get(rid, ()))
        n_open = len(openings.get(rid, ()))
        n_band = len(bands.get(rid, ()))
        n_stamp = len(stamps.get(rid, ()))
        has_site = bool(sites.get(rid))

        ev = []
        if n_space and n_band:
            ev.append(EV_ENCLOSED_SPACES)
        else:
            ev.append(EV_NO_ENCLOSURE)
        if n_open:
            ev.append(EV_OPENINGS)
        else:
            ev.append(EV_NO_OPENING)
        if n_stamp:
            ev.append(EV_ROOM_STAMPS)
        if has_site:
            ev.append(EV_SITE_BOUNDARY)
        small = biggest > 0 and extents[rid] < biggest * DETAIL_EXTENT_SHARE
        if small:
            ev.append(EV_SMALL_EXTENT)
        if hits:
            ev.append(EV_TITLE_TEXT)

        role, why, conf = UNKNOWN, "", "NOT_ESTABLISHED"
        if hits:
            role = hits[0][0]
            why = f"its own title text says {hits[0][1]!r}"
            conf = "ESTABLISHED_BY_TITLE"
        elif small:
            role = DETAIL
            why = ("its extent is a small fraction of this drawing's own "
                   "largest region, and nothing in it encloses a space")
            conf = "ESTABLISHED_BY_EXTENT"
        elif has_site and n_space:
            role = SITE_PLAN
            why = "a site boundary encloses the fabric drawn inside it"
            conf = "ESTABLISHED_BY_GEOMETRY"
        elif EV_NO_ENCLOSURE in ev or EV_NO_OPENING in ev:
            role = UNKNOWN
            why = ("nothing in it is enclosed, or no opening is drawn "
                   "anywhere in it. That is not a floor plan, and this "
                   "module will not say which of elevation, section or "
                   "schedule it is without a title")
            conf = "NOT_ESTABLISHED"
        else:
            role = FLOOR_PLAN
            why = ("it encloses spaces with wall bands and draws doors "
                   "and windows in them — which is what a plan is. WHICH "
                   "floor is a separate question")
            conf = "ESTABLISHED_BY_GEOMETRY"

        floor = _floor_from(hits)
        role_prov = floor_prov = DERIVED
        sup = given.get(rid) or {}
        if sup.get("floor_level"):
            floor = sup["floor_level"]
            floor_prov = SUPERVISED
        if sup.get("drawing_role"):
            role = sup["drawing_role"]
            role_prov = SUPERVISED
            conf = "SUPPLIED_BY_SUPERVISED_AUDIT"

        rep.roles.append(RegionRole(
            region_id=rid, drawing_role=role, floor_level=floor,
            role_provenance=role_prov, floor_provenance=floor_prov,
            title_evidence=tuple(f"{v} (h={h:g})" for _r, v, h in hits),
            evidence=tuple(ev), confidence=conf,
            extent_mm=(reg.x0, reg.y0, reg.x1, reg.y1),
            counts={"spaces": n_space, "openings": n_open,
                    "wall_bands": n_band, "room_stamps": n_stamp,
                    "site_boundary": has_site},
            why=why))

    if not any_title:
        rep.notes["no_title_text_decoded"] = (
            "not one string in this drawing matches a drawing-title word. "
            "Its titles are drawn in a font this decoder does not resolve, "
            "so the floor of every region is NOT ESTABLISHED from the "
            "drawing. A supervised assignment may supply it and is carried "
            "as supplied")
    rep.notes["only_a_floor_plan_releases_rooms"] = (
        "a region that is UNKNOWN produces no room quantity. Defaulting "
        "to FLOOR_PLAN would mean measuring rooms off an elevation")
    return rep
