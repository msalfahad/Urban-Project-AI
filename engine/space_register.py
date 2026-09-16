"""69 polygons are not 69 rooms.

The frozen round-6B export carries real rooms, halves of rooms, whole
floor plates, stair cells, cupboard interiors, a 28.27 m2 strip repeated
once in every drawing region, and candidates nobody has resolved. Summed
as though they were rooms, they produce a number that means nothing — and
the round-6B report did exactly that when it called 269.18 m2 "released
floor area" when seven rows carrying RELEASE_ELIGIBLE_GEOMETRY total
28.56 m2.

This module builds the one thing a BOQ can stand on:

    A UNIQUE PHYSICAL-SPACE REGISTER, PER FLOOR

with four things kept apart that were being added together:

    MEASURED_CANDIDATE_AREA        every polygon that has a basis
    PHYSICAL_SPACE_AREA            the ones that are actually spaces
    RELEASE_ELIGIBLE_GEOMETRY_AREA the ones the release gate passes
    TRADE_MEASUREMENT_AREA         nothing yet. That is a later round

and three rules that were not being enforced at all:

    A PARENT MAY NOT RELEASE ALONGSIDE ITS CHILDREN
    GEOMETRY REPEATED ON EVERY PLAN IS SHEET CONTENT, NOT FIVE ROOMS
    A LABEL BELONGS TO A ROOM, NOT TO THE SMALLEST BOX AROUND THE TEXT
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import cad_profile as cprofile
from engine import fitting_band as fitting
from engine import space_enclosure as enc

MODEL = "UNIQUE_PHYSICAL_SPACE_REGISTER_V1"

# --- §2 what a candidate IS ---------------------------------------------
PHYSICAL_ROOM = "PHYSICAL_ROOM"
PHYSICAL_OPEN_SPACE = "PHYSICAL_OPEN_SPACE"
CIRCULATION = "CIRCULATION"
STAIR = "STAIR"
VOID = "VOID"
SHAFT = "SHAFT"
EXTERIOR = "EXTERIOR"
DRAWING_ARTIFACT = "DRAWING_ARTIFACT"
SUPER_REGION = "SUPER_REGION"
PARTIAL_SPACE = "PARTIAL_SPACE"
UNRESOLVED = "UNRESOLVED"

CANDIDATE_ROLES = (PHYSICAL_ROOM, PHYSICAL_OPEN_SPACE, CIRCULATION, STAIR,
                   VOID, SHAFT, EXTERIOR, DRAWING_ARTIFACT, SUPER_REGION,
                   PARTIAL_SPACE, UNRESOLVED)

# Only these are physical spaces of the building. The rest are the drawing
# talking about itself, or a question nobody has answered.
SPACE_ROLES = (PHYSICAL_ROOM, PHYSICAL_OPEN_SPACE, CIRCULATION, STAIR)

# --- §5 relations between candidates --------------------------------------
REL_PARENT = "PARENT_SUPER_REGION"
REL_CHILD = "CHILD_SPACE"
REL_DUPLICATE = "DUPLICATE_SPACE"
REL_OVERLAPPING = "OVERLAPPING_SPACE_CANDIDATES"
REL_INDEPENDENT = "INDEPENDENT"

RELATIONS = (REL_PARENT, REL_CHILD, REL_DUPLICATE, REL_OVERLAPPING,
             REL_INDEPENDENT)

# --- §6 how a label resolves ---------------------------------------------
LABEL_ONE_SPACE = "EXACTLY_ONE_PHYSICAL_SPACE"
LABEL_EXCEPTION = "IDENTITY_UNRESOLVED_EXCEPTION"

# why a label could not resolve
WHY_NO_CANDIDATE = "NO_PHYSICAL_SPACE_CONTAINS_THIS_LABEL"
WHY_ONLY_A_SUBCELL = (
    "THE_ONLY_CANDIDATE_IS_A_SUBCELL_INSIDE_A_LARGER_UNRESOLVED_SPACE")
WHY_SEVERAL = "SEVERAL_PHYSICAL_SPACES_CONTAIN_THIS_LABEL"
WHY_ARTIFACT = "THE_ONLY_CANDIDATE_IS_DRAWING_CONTENT_NOT_A_ROOM"

# --- §4 repeated sheet content -------------------------------------------
# Geometry at the same place RELATIVE TO ITS OWN REGION, in at least this
# many regions, is what the sheet repeats: a title block, a north point, a
# key plan, a legend. Two could be a pair of identical flats; three of the
# same thing in three different plans of one villa is the sheet.
REPEAT_MIN_REGIONS = 3

# Two polygons are the same polygon when their region-local bounds agree
# to within the enclosure's own collinear join. Nothing new.
SAME_PLACE_MM = enc.COLLINEAR_JOIN_MM

# A candidate thinner than the thinnest thing this project calls a wall is
# a sliver of the arrangement. The profile's own figure.
MIN_THICKNESS_MM = cprofile.MIN_WALL_THICKNESS_MM

# --- a band standing ON another band -------------------------------------
# A cabinet run, a duct casing and a bath panel are drawn with two lines
# and look exactly like a wall. What gives them away is that they SHARE A
# FACE with another established band and stand on the far side of it: a
# wall does not have a second wall glued to it over the same stretch.
# Of two stacked bands the one that RUNS FURTHER is the wall — a lining is
# fitted along part of a wall, never the other way round.
#
# A lining has two faces and they do NOT mean the same thing:
#
#   the SHARED face  is where it meets the wall. A space on that side is
#                    bounded by the wall behind, and the wall is the owner
#                    of that face — the lining merely starts there.
#   the FAR face     is the front of the fitting, standing out into the
#                    room. A candidate that stops at it is the strip the
#                    fitting leaves over, not a room.
#
# So a lining blocks only the side it projects into. Bounding a space at
# the shared face is what every wall lining does and means nothing.
LINING_FACE = "A_BAND_STANDING_ON_ANOTHER_BAND_BOUNDS_THIS_SIDE"

# --- a stair is a space, and its plan rectangle is not a room area -------
# A stair is drawn as a run of closed cells — one per tread — and paired
# tread lines look exactly like thin walls, so a tread can arrive here as
# a candidate with a clear internal basis and 1.2 m2 of floor. It is a
# space of the building either way, and its floor is measured on its
# going and its rise, never as a rectangle on plan. So it is registered
# and it releases no room area.
NOT_RELEASED_AS_A_ROOM = (STAIR,)
STAIR_NOT_A_ROOM = "A_STAIR_IS_NOT_RELEASED_AS_A_ROOM_AREA"

# A candidate is a DUPLICATE of another when they cover each other. A
# fraction of area, never an absolute one.
DUPLICATE_SHARE = 0.98
# A candidate is CONTAINED in another when nearly all of it is inside.
CONTAINED_SHARE = 0.98


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "CANDIDATE_ROLES": list(CANDIDATE_ROLES),
        "SPACE_ROLES": list(SPACE_ROLES),
        "RELATIONS": list(RELATIONS),
        "REPEAT_MIN_REGIONS": REPEAT_MIN_REGIONS,
        "DUPLICATE_SHARE": DUPLICATE_SHARE,
        "CONTAINED_SHARE": CONTAINED_SHARE,
        "MIN_THICKNESS_MM": MIN_THICKNESS_MM,
        "why": {
            "no_area_rule": (
                "no candidate is given a role because of how big it is. A "
                "3 m2 room and a 300 m2 hall are asked the same questions, "
                "and the shares here compare a candidate to ANOTHER "
                "CANDIDATE, never to a room-size prior"),
            "repetition_is_relative": (
                "sheet content repeats at the same place relative to each "
                "region's own origin. Absolute coordinates would compare "
                "one plan against another, which §1 of round 4 forbids"),
            "a_parent_never_releases_with_its_children": (
                "a floor that releases both a super-region and the rooms "
                "inside it has counted its floor area twice"),
            "the_smallest_box_is_not_the_room": (
                "a counter, a wardrobe, a vanity and a stair cell all "
                "contain text and none of them is the room that text "
                "names"),
        },
    }


def model_hash() -> str:
    parts = ([MODEL] + list(CANDIDATE_ROLES) + list(RELATIONS)
             + [LABEL_ONE_SPACE, LABEL_EXCEPTION, WHY_NO_CANDIDATE,
                WHY_ONLY_A_SUBCELL, WHY_SEVERAL, WHY_ARTIFACT,
                str(REPEAT_MIN_REGIONS), str(DUPLICATE_SHARE),
                str(CONTAINED_SHARE), str(MIN_THICKNESS_MM)])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------------- the entries

@dataclass
class Entry:
    space_id: str = ""
    region_id: str = ""
    floor_level: str = ""
    candidate_role: str = UNRESOLVED
    relation: str = REL_INDEPENDENT
    parent_id: str = ""
    children: tuple = ()
    duplicates: tuple = ()
    overlaps: tuple = ()
    area_m2: float = 0.0
    basis: str = ""
    label_raw: str = ""
    normalized_identity: str = ""
    identity_authority: str = ""
    geometry_authority: str = ""
    release_status: str = ""
    blockers: tuple = ()
    repeated_in: tuple = ()
    principal_dims_mm: tuple = ()
    cad_provenance: tuple = ()
    why: str = ""

    @property
    def is_space(self) -> bool:
        return self.candidate_role in SPACE_ROLES

    @property
    def may_release(self) -> bool:
        """A space, not a duplicate, and not a container of other spaces.

        The relation PARENT_SUPER_REGION is geometric — it says only that
        something else is inside this polygon. What withdraws the release
        is the ROLE: a container OF SPACES, which is the second pass in
        `build`. A room with a drawn-in rectangle contains a candidate
        and is still a room.
        """
        return (self.is_space and self.candidate_role != SUPER_REGION
                and self.candidate_role not in NOT_RELEASED_AS_A_ROOM
                and self.relation != REL_DUPLICATE)

    def record(self) -> dict:
        return {
            "physical_space_id": self.space_id,
            "drawing_region_id": self.region_id,
            "floor": self.floor_level,
            "candidate_role": self.candidate_role,
            "register_relation": self.relation,
            "parent_super_region": self.parent_id,
            "children": list(self.children),
            "duplicates": list(self.duplicates),
            "overlaps": list(self.overlaps),
            "area_m2": round(self.area_m2, 4),
            "principal_dims_mm": [round(v, 1)
                                  for v in self.principal_dims_mm],
            "measurement_basis": self.basis,
            "raw_label": self.label_raw,
            "normalized_identity": self.normalized_identity,
            "identity_authority": self.identity_authority,
            "geometry_authority": self.geometry_authority,
            "release_status": self.release_status,
            "blockers": list(self.blockers),
            "repeated_in_regions": list(self.repeated_in),
            "cad_provenance": list(self.cad_provenance),
            "why": self.why,
        }


@dataclass
class LabelVerdict:
    text: str = ""
    x: float = 0.0
    y: float = 0.0
    region_id: str = ""
    floor_level: str = ""
    status: str = LABEL_EXCEPTION
    space_id: str = ""
    candidates: tuple = ()
    why: str = ""

    def record(self) -> dict:
        return {"raw_text": self.text,
                "at_mm": [round(self.x, 1), round(self.y, 1)],
                "drawing_region_id": self.region_id,
                "floor": self.floor_level,
                "status": self.status,
                "physical_space_id": self.space_id,
                "candidate_spaces": list(self.candidates),
                "why": self.why}


@dataclass
class Register:
    entries: list = field(default_factory=list)
    labels: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def by_floor(self) -> dict:
        out: dict = {}
        for e in self.entries:
            out.setdefault(e.floor_level, []).append(e)
        return out

    def areas(self) -> dict:
        """§1. Four numbers that were being added together as one."""
        measured = [e for e in self.entries if e.basis and
                    e.basis.startswith("CLEAR_INTERNAL")]
        spaces = [e for e in self.entries if e.is_space]
        released = [e for e in self.entries
                    if e.release_status == "RELEASE_ELIGIBLE_GEOMETRY"
                    and e.may_release]
        return {
            "MEASURED_CANDIDATE_AREA_M2": round(
                sum(e.area_m2 for e in measured), 4),
            "MEASURED_CANDIDATES": len(measured),
            "PHYSICAL_SPACE_AREA_M2": round(
                sum(e.area_m2 for e in spaces), 4),
            "PHYSICAL_SPACES": len(spaces),
            "RELEASE_ELIGIBLE_GEOMETRY_AREA_M2": round(
                sum(e.area_m2 for e in released), 4),
            "RELEASE_ELIGIBLE_GEOMETRY": len(released),
            "TRADE_MEASUREMENT_AREA_M2": None,
            "why_these_are_not_the_same_number": (
                "a measured candidate has a basis; a physical space is a "
                "space of the building; a released one passes the release "
                "gate; and a trade measurement does not exist yet"),
        }

    def counts(self) -> dict:
        return {
            "candidates": len(self.entries),
            "by_candidate_role": dict(Counter(
                e.candidate_role for e in self.entries).most_common()),
            "by_relation": dict(Counter(
                e.relation for e in self.entries).most_common()),
            "labels": len(self.labels),
            "labels_mapped_exactly_once": sum(
                1 for v in self.labels if v.status == LABEL_ONE_SPACE),
            "labels_unmapped": sum(
                1 for v in self.labels if v.status == LABEL_EXCEPTION),
            "areas": self.areas(),
        }

    def record(self, *, limit: int = 200) -> dict:
        return {
            "model": MODEL,
            "SPACE_REGISTER_HASH": model_hash(),
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "entries": [e.record() for e in self.entries[:limit]],
            "labels": [v.record() for v in self.labels[:limit]],
            "notes": dict(self.notes),
        }


# ------------------------------------------------------- §4 repeated content

def repeated_geometry(rows, regions) -> dict:
    """Which polygons sit at the same place in region after region.

    A title block, a north point, a key plan and a legend are drawn once
    per sheet cell. Their geometry is identical relative to each region's
    own origin, and identical across regions that show different floors —
    which no room ever is.
    """
    origin = {r.region_id: (r.x0, r.y0) for r in regions}
    seen: dict = {}
    for row in rows:
        poly = row.get("polygon")
        if poly is None:
            continue
        ox, oy = origin.get(row["region_id"], (0.0, 0.0))
        x0, y0, x1, y1 = poly.bounds
        key = (round((x0 - ox) / SAME_PLACE_MM),
               round((y0 - oy) / SAME_PLACE_MM),
               round((x1 - ox) / SAME_PLACE_MM),
               round((y1 - oy) / SAME_PLACE_MM))
        seen.setdefault(key, []).append(row)
    out = {}
    for _key, group in seen.items():
        regions_hit = {r["region_id"] for r in group}
        if len(regions_hit) < REPEAT_MIN_REGIONS:
            continue
        for r in group:
            out[r["space_id"]] = tuple(sorted(regions_hit))
    return out


# -------------------------------------------------------------- the builder

def _share(a, b) -> float:
    try:
        inter = a.intersection(b).area
    except Exception:      # noqa: BLE001
        return 0.0
    return 0.0 if a.area <= 0 else inter / a.area


def _thin(poly) -> bool:
    per = poly.length
    if per <= 0:
        return True
    return (2.0 * poly.area / per) <= MIN_THICKNESS_MM


# The detector itself lives in `fitting_band`: round 6D moved it down to
# the geometry layer, where a room measured to a counter front can still
# be prevented rather than only described.
StackedBand = fitting.StackedBand


def linings(walls_by_region) -> dict:
    """Which bands stand on another band, per region. `fitting_band`."""
    return fitting.detect_by_region(walls_by_region)


def stops_at_a_fitting(row, lining_bands) -> tuple:
    """The fittings whose FRONT face bounds this candidate."""
    return fitting.stops_at_a_fitting(row, lining_bands)


def build(rows, regions, *, roles=None, floor_of=None,
          space_role_of=None, lining_bands=None) -> Register:
    """One register for a whole drawing, floor by floor.

    `rows` carry space_id, region_id, polygon, area_m2, basis,
    release_status, labels and blockers. `roles` is the drawing-role
    report; `space_role_of` maps a space to round 6's architectural role.
    """
    reg = Register()
    floor = dict(floor_of or {})
    srole = dict(space_role_of or {})
    repeats = repeated_geometry(rows, regions)

    # ---- containment, duplication and overlap, WITHIN one region -------
    rel: dict = {r["space_id"]: [REL_INDEPENDENT, "", [], [], []]
                 for r in rows}
    for region_id in {r["region_id"] for r in rows}:
        mine = [r for r in rows if r["region_id"] == region_id
                and r.get("polygon") is not None]
        for a in mine:
            for b in mine:
                if a is b:
                    continue
                sa, sb = _share(a["polygon"], b["polygon"]), _share(
                    b["polygon"], a["polygon"])
                if sa >= DUPLICATE_SHARE and sb >= DUPLICATE_SHARE:
                    rel[a["space_id"]][3].append(b["space_id"])
                elif sa >= CONTAINED_SHARE:
                    rel[a["space_id"]][0] = REL_CHILD
                    rel[a["space_id"]][1] = b["space_id"]
                    rel[b["space_id"]][2].append(a["space_id"])
                elif sa > 0.0 and sa < CONTAINED_SHARE and sb > 0.0 \
                        and sb < CONTAINED_SHARE:
                    rel[a["space_id"]][4].append(b["space_id"])

    for r in rows:
        sid = r["space_id"]
        state, parent, children, dups, overs = rel[sid]
        if children and state != REL_CHILD:
            state = REL_PARENT
        elif dups and state == REL_INDEPENDENT:
            state = REL_DUPLICATE
        elif overs and state == REL_INDEPENDENT:
            state = REL_OVERLAPPING

        poly = r.get("polygon")
        basis = r.get("basis", "")
        arch = srole.get(sid, "")
        fittings = stops_at_a_fitting(r, lining_bands)
        ev = []

        # ---- §2 the candidate role, and never from area alone ---------
        if sid in repeats:
            role = DRAWING_ARTIFACT
            ev.append(f"the same geometry appears in "
                      f"{len(repeats[sid])} drawing regions")
        elif poly is not None and _thin(poly):
            role = DRAWING_ARTIFACT
            ev.append("thinner on the mean measure than the thinnest wall "
                      "this project recognises")
        elif arch in ("VOID_OR_SHAFT_ON_EVIDENCE",):
            role = VOID
            ev.append("round 6 found positive evidence of a vertical "
                      "penetration")
        elif arch == "SHAFT":
            role = SHAFT
        elif arch == "STAIR":
            role = STAIR
        elif arch in ("EXTERIOR_SPACE_UNCLASSIFIED", "EXTERNAL_SPACE",
                      "EXTERIOR_EXTENT_UNRESOLVED"):
            role = EXTERIOR
        elif fittings:
            role = PARTIAL_SPACE
            ev.append("the front face of a band standing on another band "
                      "bounds it (" + ", ".join(
                          f"{f.lining_id} on {f.wall_id}" for f in fittings)
                      + ") — the strip a fitting leaves over, not the room "
                        "the fitting stands in")
        elif basis == "CLEAR_FACE_NOT_ESTABLISHED":
            role = PARTIAL_SPACE
            ev.append("a partition of unknown thickness bounds it")
        elif basis and basis.startswith("CLEAR_INTERNAL"):
            role = PHYSICAL_ROOM if r.get("label_raw") else \
                PHYSICAL_OPEN_SPACE
        else:
            role = UNRESOLVED
            ev.append("no measurement basis was established for it")
        blockers = list(r.get("blockers", ()))
        if fittings:
            blockers.append(LINING_FACE)
        if role in NOT_RELEASED_AS_A_ROOM:
            blockers.append(STAIR_NOT_A_ROOM)
        if state == REL_DUPLICATE:
            blockers.append("DUPLICATE_OF_ANOTHER_CANDIDATE")

        reg.entries.append(Entry(
            space_id=sid, region_id=r["region_id"],
            floor_level=floor.get(r["region_id"], ""),
            candidate_role=role, relation=state, parent_id=parent,
            children=tuple(children), duplicates=tuple(dups),
            overlaps=tuple(overs), area_m2=r.get("area_m2", 0.0) or 0.0,
            basis=basis, label_raw=r.get("label_raw", ""),
            normalized_identity=r.get("normalized_identity", ""),
            identity_authority=r.get("identity_authority", ""),
            geometry_authority=r.get("geometry_authority", ""),
            release_status=r.get("release_status", ""),
            blockers=tuple(blockers),
            repeated_in=tuple(repeats.get(sid, ())),
            principal_dims_mm=tuple(r.get("principal_dims_mm") or ()),
            cad_provenance=tuple(r.get("cad_provenance") or ()),
            why="; ".join(ev)))

    # ---- §5 a SUPER_REGION is a container OF SPACES ------------------
    # Deciding this needs every candidate's role, so it is a second pass.
    # A room with a decorative rectangle drawn in it contains a candidate
    # that is not a space, and that does not make the room a super-region:
    # nothing is released twice, because the rectangle releases nothing.
    by_id = {e.space_id: e for e in reg.entries}
    for e in reg.entries:
        if e.relation != REL_PARENT:
            continue
        kids = [by_id[c] for c in e.children if c in by_id]
        if not any(k.is_space for k in kids):
            continue
        e.candidate_role = SUPER_REGION
        e.blockers = e.blockers + (
            "A_PARENT_MAY_NOT_RELEASE_WITH_ITS_CHILDREN",)
        e.why = "; ".join(filter(None, [
            e.why,
            f"it contains {sum(1 for k in kids if k.is_space)} candidate(s) "
            "that are themselves spaces"]))

    reg.notes["a_parent_never_releases_with_its_children"] = (
        "counted both ways, a floor's area is its own double")
    reg.notes["four_areas"] = (
        "MEASURED_CANDIDATE, PHYSICAL_SPACE, RELEASE_ELIGIBLE_GEOMETRY and "
        "TRADE_MEASUREMENT are four different numbers and only the last "
        "one may ever price anything")
    return reg


# ---------------------------------------------------- §6 label to one space

def reconcile_labels(reg: Register, observations, rows, *,
                     floor_of=None) -> Register:
    """Give every authored label exactly one space, or an exception.

    NEVER the smallest polygon containing the text. A counter, a wardrobe,
    a vanity and a stair cell all contain text, and the room that text
    names is the one those things stand IN. So the candidates are the
    spaces that contain the label AND are physical spaces of the building;
    among them the SMALLEST INDEPENDENT one wins, because a child inside a
    room is the room's own subdivision — and where the only candidate is a
    subcell of something unresolved, the answer is an exception, not a
    room.
    """
    entry = {e.space_id: e for e in reg.entries}
    poly = {r["space_id"]: r.get("polygon") for r in rows}
    floor = dict(floor_of or {})
    from shapely.geometry import Point

    for o in observations:
        pt = Point(o.x, o.y)
        hits = []
        for sid, g in poly.items():
            if g is None:
                continue
            try:
                if g.contains(pt):
                    hits.append(sid)
            except Exception:      # noqa: BLE001
                continue
        region_id = (entry[hits[0]].region_id if hits else "")
        v = LabelVerdict(text=getattr(o, "text", getattr(o, "value", "")),
                         x=o.x, y=o.y, region_id=region_id,
                         floor_level=floor.get(region_id, ""),
                         candidates=tuple(hits))
        spaces = [s for s in hits if entry[s].is_space]
        artifacts = [s for s in hits if
                     entry[s].candidate_role == DRAWING_ARTIFACT]
        if not hits:
            v.why = WHY_NO_CANDIDATE
        elif not spaces and artifacts:
            v.why = WHY_ARTIFACT
        elif not spaces:
            v.why = WHY_ONLY_A_SUBCELL
        else:
            free = [s for s in spaces
                    if entry[s].candidate_role != SUPER_REGION]
            pick = free or spaces
            pick.sort(key=lambda s: entry[s].area_m2)
            rival = [s for s in pick[1:]
                     if _share(poly[pick[0]], poly[s]) < CONTAINED_SHARE]
            if rival:
                # Two spaces claim the label and neither is inside the
                # other. A smallest-one rule would answer, and half the
                # time it would be wrong.
                v.why = WHY_SEVERAL
            else:
                v.status = LABEL_ONE_SPACE
                v.space_id = pick[0]
                v.why = (f"of {len(hits)} candidate(s) containing it, "
                         f"{len(spaces)} are physical spaces, each of the "
                         "others contains it, and the smallest one that is "
                         "not a super-region is the room it names")
        reg.labels.append(v)
    return reg


def completeness(reg: Register) -> dict:
    """§13. Per floor: what was observed, what was established, what is not."""
    out = {}
    floors = sorted({e.floor_level for e in reg.entries})
    for fl in floors:
        entries = [e for e in reg.entries if e.floor_level == fl]
        labels = [v for v in reg.labels if v.floor_level == fl]
        mapped = [v for v in labels if v.status == LABEL_ONE_SPACE]
        counted = Counter(v.space_id for v in mapped)
        out[fl or "FLOOR_LEVEL_NOT_ESTABLISHED"] = {
            "authored_room_labels_detected": len(labels),
            "labels_mapped_exactly_once": sum(
                1 for v in mapped if counted[v.space_id] == 1),
            "labels_unmapped": len(labels) - len(mapped),
            "labels_mapped_to_a_space_that_several_labels_claim": sum(
                1 for v in mapped if counted[v.space_id] > 1),
            "physical_spaces_established": sum(
                1 for e in entries if e.is_space),
            "physical_spaces_unidentified": sum(
                1 for e in entries if e.is_space and not e.label_raw),
            "super_regions": sum(1 for e in entries
                                 if e.candidate_role == SUPER_REGION),
            "partial_spaces": sum(1 for e in entries
                                  if e.candidate_role == PARTIAL_SPACE),
            "non_space_artifacts": sum(
                1 for e in entries
                if e.candidate_role == DRAWING_ARTIFACT),
            "unresolved_spaces": sum(1 for e in entries
                                     if e.candidate_role == UNRESOLVED),
            "areas": {
                "MEASURED_CANDIDATE_AREA_M2": round(sum(
                    e.area_m2 for e in entries
                    if e.basis.startswith("CLEAR_INTERNAL")), 4),
                "PHYSICAL_SPACE_AREA_M2": round(sum(
                    e.area_m2 for e in entries if e.is_space), 4),
                "RELEASE_ELIGIBLE_GEOMETRY_AREA_M2": round(sum(
                    e.area_m2 for e in entries
                    if e.may_release
                    and e.release_status == "RELEASE_ELIGIBLE_GEOMETRY"),
                    4),
                "TRADE_MEASUREMENT_AREA_M2": None,
            },
        }
    return out
