"""E31D — the material wall graph and the space boundary graph are not the same.

The gap map settled it. BTH-05 has three sides at 100% coverage and one
1054 mm gap. BED-01 has three at ~100% and one 1200 mm gap. Those are doors.

    -------------------        -------------------
                        DOOR

For BLOCKWORK, PLASTER and OPENINGS the gap is real and the material wall graph
must stay OPEN across it. For identifying the bedroom FLOOR POLYGON the room
still needs a boundary there. Both are true at once, so there are two graphs:

    MATERIAL_WALL_GRAPH    what is built. Open at every doorway.
    SPACE_BOUNDARY_GRAPH   what encloses a room. May cross a doorway on a
                           VIRTUAL boundary carrying zero material.

A room that closes only because of a virtual portal boundary is MORE correct
than one closed by inventing wall material across its door — and the failure
to distinguish them is why 0 of 4 controls "failed" when three of them were
essentially complete.

THE HARD INVARIANT. A virtual boundary has material_length_mm == 0, and the
type refuses to be constructed otherwise. It contributes zero blockwork, zero
plaster, zero physical wall length. `material_length_mm` is the only length a
quantity engine may read, and on a virtual boundary it is always zero.

    NEVER TURN A VIRTUAL BOUNDARY INTO A PHYSICAL WALL.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# What a boundary interval is made of.
PHYSICAL_WALL = "PHYSICAL_WALL"
VIRTUAL_PORTAL = "VIRTUAL_SPACE_BOUNDARY"
OPEN_TRANSITION = "OPEN_PLAN_TRANSITION"

# How much a gap is believed to be a doorway. Evidence families, as everywhere.
PORTAL_CANDIDATE = "PORTAL_CANDIDATE"
PORTAL_PROBABLE = "PORTAL_PROBABLE"
PORTAL_VALIDATED = "PORTAL_VALIDATED"
PORTAL_UNRESOLVED = "PORTAL_UNRESOLVED"

PORTAL_STATUSES = (PORTAL_CANDIDATE, PORTAL_PROBABLE, PORTAL_VALIDATED,
                   PORTAL_UNRESOLVED)

# Why a boundary interval is not wall.
GAP_DOOR = "DOOR_OR_PORTAL_GAP"
GAP_OPEN_PLAN = "OPEN_PLAN_TRANSITION"
GAP_MISSING_EXTRACTION = "MISSING_WALL_EXTRACTION"
GAP_UNRESOLVED = "UNRESOLVED"

FAMILY_GEOMETRY = "GEOMETRY"
FAMILY_SYMBOL = "SYMBOL"
FAMILY_TOPOLOGY = "TOPOLOGY"
FAMILY_DOCUMENT = "DOCUMENT"
FAMILY_SEMANTIC = "SEMANTIC"

E_BANDS_FACE_EACH_OTHER = "PAIRED_BANDS_TERMINATE_FACING_EACH_OTHER"
E_PLAUSIBLE_SPAN = "SPAN_IN_THE_DOOR_RANGE"
E_JAMB_CAPS = "END_CAPS_AT_BOTH_JAMBS"
E_SWING_ARC = "DOOR_SWING_ARC_NEARBY"
E_CLOSES_A_BOUNDARY = "GAP_CLOSES_AN_OTHERWISE_COMPLETE_BOUNDARY"

EVIDENCE_FAMILY = {
    E_BANDS_FACE_EACH_OTHER: FAMILY_GEOMETRY,
    E_PLAUSIBLE_SPAN: FAMILY_GEOMETRY,
    E_JAMB_CAPS: FAMILY_GEOMETRY,
    E_SWING_ARC: FAMILY_SYMBOL,
    E_CLOSES_A_BOUNDARY: FAMILY_TOPOLOGY,
}
MIN_FAMILIES_FOR_VALIDATED = 2

# A doorway's clear span. Wide, because it is EVIDENCE and not a test:
# "gap size alone = door" is exactly the rule this module refuses.
MIN_DOOR_MM = 600.0
MAX_DOOR_MM = 1500.0
# Beyond this a gap is an open-plan transition, not a doorway.
MAX_PORTAL_MM = 2500.0


class SpaceBoundaryError(RuntimeError):
    """A boundary was asserted that would put material where there is none."""


@dataclass(frozen=True)
class BoundaryInterval:
    """One stretch of a room's boundary, and what it is made of.

    `material_length_mm` is the ONLY length a quantity engine may read. On a
    virtual portal it is zero and the type enforces that on construction.
    """

    interval_id: str
    space_id: str
    side: str
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    boundary_type: str
    material_length_mm: float
    wall_band_ids: tuple[str, ...] = ()
    portal_id: str = ""
    why: str = ""

    def __post_init__(self):
        if self.boundary_type in (VIRTUAL_PORTAL, OPEN_TRANSITION) \
                and self.material_length_mm != 0.0:
            raise SpaceBoundaryError(
                f"{self.interval_id} is a {self.boundary_type} carrying "
                f"{self.material_length_mm} mm of material. A virtual boundary "
                "has ZERO wall material: it contributes no blockwork, no "
                "plaster and no physical wall length, and a quantity engine "
                "reading this field must never be handed anything else")
        if self.boundary_type == PHYSICAL_WALL and self.material_length_mm <= 0:
            raise SpaceBoundaryError(
                f"{self.interval_id} is a PHYSICAL_WALL with no material "
                "length. A wall that is not there is not a wall")

    @property
    def span_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    @property
    def is_virtual(self) -> bool:
        return self.boundary_type in (VIRTUAL_PORTAL, OPEN_TRANSITION)

    def record(self) -> dict:
        return {"interval_id": self.interval_id, "space_id": self.space_id,
                "side": self.side, "boundary_type": self.boundary_type,
                "span_mm": round(self.span_mm, 1),
                "material_length_mm": round(self.material_length_mm, 1),
                "wall_band_ids": list(self.wall_band_ids),
                "portal_id": self.portal_id, "is_virtual": self.is_virtual,
                "why": self.why}


@dataclass(frozen=True)
class PortalCandidate:
    """A gap that may be a doorway, with the families that say so."""

    portal_id: str
    space_id: str
    side: str
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    status: str
    evidence: tuple[str, ...] = ()
    gap_class: str = GAP_UNRESOLVED
    why: str = ""

    @property
    def span_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    @property
    def families(self) -> set:
        return {EVIDENCE_FAMILY[e] for e in self.evidence
                if e in EVIDENCE_FAMILY}

    @property
    def may_close_a_space(self) -> bool:
        """Only PROBABLE or VALIDATED portals may carry a virtual boundary."""
        return self.status in (PORTAL_PROBABLE, PORTAL_VALIDATED)

    def record(self) -> dict:
        return {"portal_id": self.portal_id, "space_id": self.space_id,
                "side": self.side, "span_mm": round(self.span_mm, 1),
                "status": self.status, "gap_class": self.gap_class,
                "evidence": list(self.evidence),
                "families": sorted(self.families),
                "may_close_a_space": self.may_close_a_space, "why": self.why}


def classify_gap(space_id: str, side: str, axis: str, fixed: float,
                 lo: float, hi: float, *, caps=(), bands_face_each_other: bool,
                 other_sides_complete: bool, swing_arcs=()) -> PortalCandidate:
    """What is this gap? Evidence families, never span alone.

    "gap size alone = door" would classify a missing wall as a doorway and a
    doorway as a missing wall with equal confidence. Span is ONE geometric
    observation among several.
    """
    span = abs(hi - lo)
    ev = []
    if MIN_DOOR_MM <= span <= MAX_DOOR_MM:
        ev.append(E_PLAUSIBLE_SPAN)
    if bands_face_each_other:
        ev.append(E_BANDS_FACE_EACH_OTHER)
    jamb = [c for c in caps
            if abs(c.at_mm - lo) < 400 or abs(c.at_mm - hi) < 400]
    if len(jamb) >= 2:
        ev.append(E_JAMB_CAPS)
    if any(abs(a - (lo + hi) / 2) < span for a in swing_arcs):
        ev.append(E_SWING_ARC)
    if other_sides_complete:
        ev.append(E_CLOSES_A_BOUNDARY)

    fams = {EVIDENCE_FAMILY[e] for e in ev}
    if span > MAX_PORTAL_MM:
        status, gap_class = PORTAL_UNRESOLVED, GAP_OPEN_PLAN
        why = (f"{span:.0f} mm is far wider than a doorway. This is an "
               "open-plan transition or a missing wall, and it is not closed "
               "on a portal hypothesis")
    elif len(fams) >= MIN_FAMILIES_FOR_VALIDATED:
        status, gap_class = PORTAL_PROBABLE, GAP_DOOR
        why = (f"{span:.0f} mm gap with {len(fams)} independent evidence "
               f"families: {', '.join(sorted(fams))}")
    elif ev:
        status, gap_class = PORTAL_CANDIDATE, GAP_UNRESOLVED
        why = ("one evidence family only. A gap this size is equally a "
               "doorway and a wall the extractor missed")
    else:
        status, gap_class = PORTAL_UNRESOLVED, GAP_MISSING_EXTRACTION
        why = ("no portal evidence at all: most likely a wall the extractor "
               "did not recover")
    return PortalCandidate(
        portal_id=f"PT-{space_id}-{side}-{int(lo)}", space_id=space_id,
        side=side, axis=axis, fixed_mm=fixed, start_mm=lo, end_mm=hi,
        status=status, evidence=tuple(ev), gap_class=gap_class, why=why)


def build_space_boundary(space_id: str, sides: dict, portals) -> list:
    """The room's boundary as intervals: wall where there is wall, virtual
    where a probable portal explains the gap, and nothing invented anywhere.

    `sides` maps side -> {"axis", "fixed", "lo", "hi", "covered": [(a,b)...],
    "gaps": [(a,b)...]}.
    """
    by_gap = {(p.side, round(p.start_mm)): p for p in portals}
    out: list[BoundaryInterval] = []
    n = 0
    for side, d in sides.items():
        for a, b in d["covered"]:
            n += 1
            out.append(BoundaryInterval(
                interval_id=f"BI-{space_id}-{n:03d}", space_id=space_id,
                side=side, axis=d["axis"], fixed_mm=d["fixed"],
                start_mm=a, end_mm=b, boundary_type=PHYSICAL_WALL,
                material_length_mm=b - a,
                wall_band_ids=tuple(d.get("band_ids", ())),
                why="a wall band covers this interval"))
        for a, b in d["gaps"]:
            p = by_gap.get((side, round(a)))
            n += 1
            if p is not None and p.may_close_a_space:
                out.append(BoundaryInterval(
                    interval_id=f"BI-{space_id}-{n:03d}", space_id=space_id,
                    side=side, axis=d["axis"], fixed_mm=d["fixed"],
                    start_mm=a, end_mm=b, boundary_type=VIRTUAL_PORTAL,
                    material_length_mm=0.0, portal_id=p.portal_id,
                    why=("a probable doorway. This interval closes the room "
                         "and carries NO wall material: zero blockwork, zero "
                         "plaster, zero physical wall length")))
            else:
                # NOT closed. An unexplained gap leaves the boundary open,
                # because closing it would be inventing either a wall or a door.
                out.append(BoundaryInterval(
                    interval_id=f"BI-{space_id}-{n:03d}", space_id=space_id,
                    side=side, axis=d["axis"], fixed_mm=d["fixed"],
                    start_mm=a, end_mm=b, boundary_type=OPEN_TRANSITION,
                    material_length_mm=0.0,
                    portal_id=p.portal_id if p else "",
                    why=(p.why if p else
                         "no wall and no portal evidence: the boundary stays "
                         "open here")))
    return out


def material_length_m(intervals) -> float:
    """The only wall length a quantity engine may read from a boundary."""
    return sum(i.material_length_mm for i in intervals) / 1000


def space_closes(intervals) -> bool:
    """Is every interval either wall or an explained portal?"""
    return all(i.boundary_type in (PHYSICAL_WALL, VIRTUAL_PORTAL)
               for i in intervals)


def summary(intervals, portals) -> dict:
    return {
        "intervals": len(intervals),
        "by_boundary_type": dict(Counter(i.boundary_type for i in intervals)),
        "material_length_m": round(material_length_m(intervals), 2),
        "virtual_length_m": round(
            sum(i.span_mm for i in intervals if i.is_virtual) / 1000, 2),
        "virtual_material_length_m": 0.0,
        "portals": len(portals),
        "portals_by_status": dict(Counter(p.status for p in portals)),
        "portals_by_gap_class": dict(Counter(p.gap_class for p in portals)),
        "note": ("virtual boundaries carry ZERO material length. The virtual "
                 "SPAN is reported so it can be audited; it is never a "
                 "quantity"),
    }
