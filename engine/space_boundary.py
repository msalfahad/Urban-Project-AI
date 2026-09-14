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

from engine.lengths import (HOST_WALL_GROSS_LENGTH, MATERIAL_PRESENT_LENGTH,
                            OPENING_LENGTH, SPACE_BOUNDARY_LENGTH, LengthSet)

# What a boundary interval is made of. The virtual classes are NOT
# interchangeable: a door inside a wall and a semantic transition between a
# dining zone and a saloon are different objects with different lengths.
PHYSICAL_WALL = "PHYSICAL_WALL"

# A door or window inside a host wall. Zero material, but the host wall
# continues conceptually through it, so it belongs to the gross line.
HOST_WALL_OPENING = "HOST_WALL_OPENING_BOUNDARY"

# An open-plan transition. Zero material AND zero host wall: there is no wall
# here to be gross about, and it must never become one.
OPEN_PLAN_VIRTUAL = "OPEN_PLAN_VIRTUAL_BOUNDARY"

# Anything else supported in future. Named so it cannot be quietly reused.
OTHER_VIRTUAL = "OTHER_VIRTUAL_TOPOLOGY_BOUNDARY"

VIRTUAL_TYPES = (HOST_WALL_OPENING, OPEN_PLAN_VIRTUAL, OTHER_VIRTUAL)

# Kept so older readers do not silently get a different meaning.
VIRTUAL_PORTAL = HOST_WALL_OPENING
OPEN_TRANSITION = OPEN_PLAN_VIRTUAL

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

# APPROVED EVIDENCE COMBINATIONS, not "any two families".
#
# GEOMETRY and TOPOLOGY are CORRELATED here and counting them as two
# independent proofs was wrong: the same gap geometry produces both "there is a
# gap" and "closing the gap closes the room". One observation seen twice is one
# observation. So the table says which combinations are actually independent.
COMBINATIONS = {
    frozenset({FAMILY_GEOMETRY, FAMILY_SYMBOL}): PORTAL_VALIDATED,
    frozenset({FAMILY_GEOMETRY, FAMILY_DOCUMENT}): PORTAL_VALIDATED,
    frozenset({FAMILY_SYMBOL, FAMILY_DOCUMENT}): PORTAL_VALIDATED,
    # Correlated: geometry implies the topology observation on the same gap.
    frozenset({FAMILY_GEOMETRY, FAMILY_TOPOLOGY}): PORTAL_PROBABLE,
    frozenset({FAMILY_TOPOLOGY, FAMILY_SEMANTIC}): PORTAL_CANDIDATE,
    frozenset({FAMILY_GEOMETRY, FAMILY_SEMANTIC}): PORTAL_PROBABLE,
}

# Families that can never carry a portal on their own, however strong.
NEVER_ALONE = (FAMILY_TOPOLOGY, FAMILY_SEMANTIC, FAMILY_GEOMETRY)


def status_for(families: set) -> tuple[str, str]:
    """The approved status for this combination of evidence families.

    A combination not in the table is capped at PROBABLE when it holds three or
    more families, and at CANDIDATE otherwise. Nothing reaches VALIDATED by
    accumulating correlated observations.
    """
    fams = frozenset(families)
    if not fams:
        return PORTAL_UNRESOLVED, "no evidence of any kind"
    if len(fams) == 1:
        only = next(iter(fams))
        return PORTAL_CANDIDATE, (
            f"{only} alone. Span alone is never sufficient, topology alone is "
            "never sufficient, and semantic alone is never sufficient")
    if fams in COMBINATIONS:
        status = COMBINATIONS[fams]
        why = (f"{'+'.join(sorted(fams))} is an approved combination"
               + (" — but GEOMETRY and TOPOLOGY are correlated on one gap, so "
                  "it caps at PROBABLE" if status == PORTAL_PROBABLE else ""))
        return status, why
    if len(fams) >= 3:
        return PORTAL_PROBABLE, (
            f"{len(fams)} families ({'+'.join(sorted(fams))}), no approved "
            "combination among them — capped at PROBABLE")
    return PORTAL_CANDIDATE, (
        f"{'+'.join(sorted(fams))} is not an approved combination")

# A doorway's clear span. Wide, because it is EVIDENCE and not a test:
# "gap size alone = door" is exactly the rule this module refuses.
MIN_DOOR_MM = 600.0
MAX_DOOR_MM = 1500.0
# Beyond this a gap is an open-plan transition, not a doorway.
MAX_PORTAL_MM = 2500.0


class SpaceBoundaryError(RuntimeError):
    """A boundary was asserted that would put material where there is none."""


# Where a virtual closure line actually runs. It does not simply connect
# arbitrary gap endpoints: a room's area depends on it.
CLEAR_INTERNAL_FINISH_FACE = "CLEAR_INTERNAL_FINISH_FACE"
HOST_WALL_CENTRELINE = "HOST_WALL_CENTRELINE"
CLOSURE_BASIS_UNRESOLVED = "CLOSURE_BASIS_UNRESOLVED"


@dataclass(frozen=True)
class BoundaryInterval:
    """One stretch of a room's boundary, with EVERY length it has.

    A doorway is four facts at once and they are stored as four:

        material_present   0        no wall material stands here
        opening            1054 mm  a real opening
        space_boundary     1054 mm  the room closes across it
        host_wall_gross    1054 mm  the host wall continues through it

    Collapsing them into one number makes at least three trades wrong. An
    OPEN_PLAN_VIRTUAL boundary differs again: zero material AND zero host wall,
    because there is no wall here to be gross about.
    """

    interval_id: str
    space_id: str
    side: str
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    boundary_type: str
    lengths: LengthSet = field(default_factory=LengthSet)
    wall_band_ids: tuple[str, ...] = ()
    portal_id: str = ""
    closure_basis: str = ""
    jamb_ids: tuple[str, ...] = ()
    host_wall_band_id: str = ""
    why: str = ""

    def __post_init__(self):
        mat = self.lengths.material_present_mm
        host = self.lengths.host_wall_gross_mm
        if self.boundary_type in VIRTUAL_TYPES and mat not in (0.0, None):
            raise SpaceBoundaryError(
                f"{self.interval_id} is a {self.boundary_type} with "
                f"{mat} mm of material present. A virtual boundary has ZERO "
                "actual wall material: no blockwork, no plaster, no physical "
                "wall length")
        if self.boundary_type == OPEN_PLAN_VIRTUAL and host not in (0.0, None):
            raise SpaceBoundaryError(
                f"{self.interval_id} is an OPEN_PLAN_VIRTUAL_BOUNDARY with "
                f"{host} mm of host wall. There is no wall here to be gross "
                "about, and a semantic transition must never become one")
        if self.boundary_type == PHYSICAL_WALL and not mat:
            raise SpaceBoundaryError(
                f"{self.interval_id} is a PHYSICAL_WALL with no material "
                "length. A wall that is not there is not a wall")
        if self.boundary_type == HOST_WALL_OPENING and not self.closure_basis:
            raise SpaceBoundaryError(
                f"{self.interval_id} closes a room across an opening without "
                "stating where the closure line runs. Room area depends on "
                "it, so the basis is required")

    @property
    def span_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    @property
    def is_virtual(self) -> bool:
        return self.boundary_type in VIRTUAL_TYPES

    @property
    def material_length_mm(self) -> float:
        """Actual material. Kept for readers that want exactly this basis."""
        return self.lengths.material_present_mm or 0.0

    def record(self) -> dict:
        return {"interval_id": self.interval_id, "space_id": self.space_id,
                "side": self.side, "boundary_type": self.boundary_type,
                "span_mm": round(self.span_mm, 1),
                "is_virtual": self.is_virtual,
                "closure_basis": self.closure_basis,
                "host_wall_band_id": self.host_wall_band_id,
                "jamb_ids": list(self.jamb_ids),
                "wall_band_ids": list(self.wall_band_ids),
                "portal_id": self.portal_id,
                **self.lengths.record(), "why": self.why}


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
    status, why = status_for(fams)
    if not ev:
        status, gap_class = PORTAL_UNRESOLVED, GAP_MISSING_EXTRACTION
        why = ("no portal evidence at all: most likely a wall the extractor "
               "did not recover")
    elif span > MAX_PORTAL_MM:
        # WIDTH IS EVIDENCE, NOT A PHYSICAL RULE. Large openings exist. A wide
        # gap is not automatically an open-plan transition — it is a gap whose
        # span does not by itself support a doorway hypothesis, and it needs
        # the other families to say what it is.
        gap_class = GAP_OPEN_PLAN if status == PORTAL_CANDIDATE else GAP_DOOR
        status = min(status, PORTAL_PROBABLE, key=lambda s: (
            PORTAL_STATUSES.index(s)))
        why = (f"{span:.0f} mm is wider than a typical doorway, so span "
               "supports no door hypothesis here. Large openings exist and "
               "width is evidence only: " + why)
    else:
        gap_class = GAP_DOOR if status in (
            PORTAL_PROBABLE, PORTAL_VALIDATED) else GAP_UNRESOLVED
        why = f"{span:.0f} mm gap. " + why
    return PortalCandidate(
        portal_id=f"PT-{space_id}-{side}-{int(lo)}", space_id=space_id,
        side=side, axis=axis, fixed_mm=fixed, start_mm=lo, end_mm=hi,
        status=status, evidence=tuple(ev), gap_class=gap_class, why=why)


def build_space_boundary(space_id: str, sides: dict, portals, *,
                         closure_basis: str = CLEAR_INTERNAL_FINISH_FACE
                         ) -> list:
    """The room's boundary as intervals, each carrying all of its lengths.

    `sides` maps side -> {"axis", "fixed", "lo", "hi", "covered", "gaps",
    "band_ids"}.
    """
    by_gap = {(p.side, round(p.start_mm)): p for p in portals}
    out: list[BoundaryInterval] = []
    n = 0
    for side, d in sides.items():
        band_ids = tuple(d.get("band_ids", ()))
        for a, b in d["covered"]:
            n += 1
            L = b - a
            out.append(BoundaryInterval(
                interval_id=f"BI-{space_id}-{n:03d}", space_id=space_id,
                side=side, axis=d["axis"], fixed_mm=d["fixed"],
                start_mm=a, end_mm=b, boundary_type=PHYSICAL_WALL,
                # A wall is all four things and they coincide here: it encloses
                # the space, it IS the gross host line, material stands on it,
                # and it contains no opening.
                lengths=LengthSet(space_boundary_mm=L, host_wall_gross_mm=L,
                                  material_present_mm=L, opening_mm=0.0),
                wall_band_ids=band_ids,
                why="a wall band covers this interval"))
        for a, b in d["gaps"]:
            p = by_gap.get((side, round(a)))
            n += 1
            L = b - a
            if p is not None and p.may_close_a_space:
                out.append(BoundaryInterval(
                    interval_id=f"BI-{space_id}-{n:03d}", space_id=space_id,
                    side=side, axis=d["axis"], fixed_mm=d["fixed"],
                    start_mm=a, end_mm=b, boundary_type=HOST_WALL_OPENING,
                    # FOUR FACTS. No material, a real opening, the room closes
                    # across it, and the host wall continues through it for
                    # every trade whose approved rule is gross-then-deduct.
                    lengths=LengthSet(space_boundary_mm=L,
                                      host_wall_gross_mm=L,
                                      material_present_mm=0.0, opening_mm=L),
                    portal_id=p.portal_id, closure_basis=closure_basis,
                    jamb_ids=tuple(p.evidence),
                    host_wall_band_id=band_ids[0] if band_ids else "",
                    why=("a supported opening in a host wall. Zero material "
                         "stands here; the room closes across it; and the "
                         "gross host-wall line runs through it")))
            else:
                out.append(BoundaryInterval(
                    interval_id=f"BI-{space_id}-{n:03d}", space_id=space_id,
                    side=side, axis=d["axis"], fixed_mm=d["fixed"],
                    start_mm=a, end_mm=b, boundary_type=OPEN_PLAN_VIRTUAL,
                    # Zero material AND zero host wall: no wall is here to be
                    # gross about. space_boundary is NOT established either —
                    # the room does not close across an unexplained gap.
                    lengths=LengthSet(host_wall_gross_mm=0.0,
                                      material_present_mm=0.0, opening_mm=0.0),
                    portal_id=p.portal_id if p else "",
                    why=(p.why if p else
                         "no wall and no portal evidence: the boundary stays "
                         "open here")))
    return out


def material_length_m(intervals) -> float:
    """Actual wall material. ONE basis among five — see engine.lengths."""
    from engine.lengths import MATERIAL_PRESENT_LENGTH, total
    return total(intervals, MATERIAL_PRESENT_LENGTH)


def space_closes(intervals) -> bool:
    """Is every interval either wall or a supported host-wall opening?"""
    return all(i.boundary_type in (PHYSICAL_WALL, HOST_WALL_OPENING)
               for i in intervals)


def reconcile(intervals) -> dict:
    """All five bases side by side, with the identity that should hold.

    For a room hosted by continuous walls and doors:

        HOST_WALL_GROSS = MATERIAL_PRESENT + supported HOST-WALL OPENINGS

    Reported rather than enforced: an open-plan edge carries no host wall at
    all, so the identity does not apply to every room, and forcing it where
    geometry makes it inapplicable would be its own error.
    """
    from engine.lengths import (HOST_WALL_GROSS_LENGTH,
                                MATERIAL_PRESENT_LENGTH, OPENING_LENGTH,
                                SPACE_BOUNDARY_LENGTH, coverage, total)
    host = total(intervals, HOST_WALL_GROSS_LENGTH)
    mat = total(intervals, MATERIAL_PRESENT_LENGTH)
    opening = sum(i.lengths.opening_mm or 0.0 for i in intervals
                  if i.boundary_type == HOST_WALL_OPENING) / 1000
    resid = host - (mat + opening)
    return {
        "space_boundary_length_m": round(
            total(intervals, SPACE_BOUNDARY_LENGTH), 3),
        "host_wall_gross_length_m": round(host, 3),
        "material_present_length_m": round(mat, 3),
        "opening_length_m": round(opening, 3),
        "identity_residual_m": round(resid, 3),
        "identity_holds": abs(resid) < 0.001,
        "identity": ("HOST_WALL_GROSS = MATERIAL_PRESENT + HOST_WALL_OPENINGS. "
                     "It does not apply to open-plan edges, which carry no "
                     "host wall"),
        "coverage": {b["basis"]: b for b in (
            coverage(intervals, SPACE_BOUNDARY_LENGTH),
            coverage(intervals, HOST_WALL_GROSS_LENGTH),
            coverage(intervals, MATERIAL_PRESENT_LENGTH),
            coverage(intervals, OPENING_LENGTH))},
    }


def summary(intervals, portals) -> dict:
    return {
        "intervals": len(intervals),
        "by_boundary_type": dict(Counter(i.boundary_type for i in intervals)),
        **reconcile(intervals),
        "virtual_span_m": round(
            sum(i.span_mm for i in intervals if i.is_virtual) / 1000, 2),
        "virtual_material_length_m": 0.0,
        "portals": len(portals),
        "portals_by_status": dict(Counter(p.status for p in portals)),
        "portals_by_gap_class": dict(Counter(p.gap_class for p in portals)),
        "note": ("virtual boundaries carry ZERO material length. The virtual "
                 "SPAN is reported so it can be audited; it is never a "
                 "quantity"),
    }
