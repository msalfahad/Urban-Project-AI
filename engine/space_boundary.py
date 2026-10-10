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
                            OPENING_LENGTH, SPACE_BOUNDARY_LENGTH, LengthSet,
                            coverage, total)

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
# Not produced yet. Named now so the geometry table can already say what it
# would be worth, rather than being widened later to let something through.
FAMILY_CAD = "CAD_ENTITY"

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
    # A CAD entity is the top of the source hierarchy and still pairs: one
    # family never validates a portal, whatever family it is.
    frozenset({FAMILY_CAD, FAMILY_GEOMETRY}): PORTAL_VALIDATED,
    frozenset({FAMILY_CAD, FAMILY_SYMBOL}): PORTAL_VALIDATED,
    frozenset({FAMILY_CAD, FAMILY_DOCUMENT}): PORTAL_VALIDATED,
    # Correlated: geometry implies the topology observation on the same gap.
    frozenset({FAMILY_GEOMETRY, FAMILY_TOPOLOGY}): PORTAL_PROBABLE,
    frozenset({FAMILY_TOPOLOGY, FAMILY_SEMANTIC}): PORTAL_CANDIDATE,
    frozenset({FAMILY_GEOMETRY, FAMILY_SEMANTIC}): PORTAL_PROBABLE,
}

# Families that can never carry a portal on their own, however strong.
NEVER_ALONE = (FAMILY_TOPOLOGY, FAMILY_SEMANTIC, FAMILY_GEOMETRY)


# Strength order, so "the best approved combination present" is computable.
PORTAL_RANK = {PORTAL_UNRESOLVED: 0, PORTAL_CANDIDATE: 1,
               PORTAL_PROBABLE: 2, PORTAL_VALIDATED: 3}


def _best(table: dict, fams: frozenset, rank: dict):
    """The strongest approved combination CONTAINED IN this evidence set.

    Exact-match lookup was not monotonic: a swing arc added to an approved
    GEOMETRY+SYMBOL pair produced a three-family set that matched nothing and
    fell through to a lower cap. Evidence must never make an answer worse.
    """
    hits = [(rank[v], v, k) for k, v in table.items() if k <= fams]
    if not hits:
        return None
    _, status, key = max(hits, key=lambda h: (h[0], len(h[2])))
    return status, key


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
    best = _best(COMBINATIONS, fams, PORTAL_RANK)
    if best is not None:
        status, key = best
        why = (f"{'+'.join(sorted(key))} is an approved combination"
               + (f" (with {'+'.join(sorted(fams - key))} also present)"
                  if fams - key else "")
               + (" — but GEOMETRY and TOPOLOGY are correlated on one gap, so "
                  "it caps at PROBABLE" if status == PORTAL_PROBABLE else ""))
        return status, why
    if len(fams) >= 3:
        return PORTAL_PROBABLE, (
            f"{len(fams)} families ({'+'.join(sorted(fams))}), no approved "
            "combination among them — capped at PROBABLE")
    return PORTAL_CANDIDATE, (
        f"{'+'.join(sorted(fams))} is not an approved combination")

# ------------------------------------------- existence and geometry are two

# "Is there a door here?" and "do we know exactly where its jambs are?" are
# different questions, and the single status answered neither cleanly.
#
# SYMBOL + DOCUMENT can prove a door EXISTS beyond argument — the schedule says
# D-04 and the swing symbol is drawn — while saying nothing about where its
# jambs actually fall on the wall line. A space-boundary edge is a piece of
# geometry: it needs the second answer, not the first.

EXISTENCE_UNRESOLVED = "PORTAL_EXISTENCE_UNRESOLVED"
EXISTENCE_CANDIDATE = "PORTAL_EXISTENCE_CANDIDATE"
EXISTENCE_PROBABLE = "PORTAL_EXISTENCE_PROBABLE"
EXISTENCE_VALIDATED = "PORTAL_EXISTENCE_VALIDATED"

EXISTENCE_STATUSES = (EXISTENCE_UNRESOLVED, EXISTENCE_CANDIDATE,
                      EXISTENCE_PROBABLE, EXISTENCE_VALIDATED)
EXISTENCE_RANK = {s: i for i, s in enumerate(EXISTENCE_STATUSES)}

GEOMETRY_UNRESOLVED = "PORTAL_GEOMETRY_UNRESOLVED"
GEOMETRY_CANDIDATE = "PORTAL_GEOMETRY_CANDIDATE"
GEOMETRY_PROBABLE = "PORTAL_GEOMETRY_PROBABLE"
GEOMETRY_VALIDATED = "PORTAL_GEOMETRY_VALIDATED"

GEOMETRY_STATUSES = (GEOMETRY_UNRESOLVED, GEOMETRY_CANDIDATE,
                     GEOMETRY_PROBABLE, GEOMETRY_VALIDATED)
GEOMETRY_RANK = {s: i for i, s in enumerate(GEOMETRY_STATUSES)}

# Which combinations prove a door IS THERE.
EXISTENCE_COMBINATIONS = {
    frozenset({FAMILY_GEOMETRY, FAMILY_SYMBOL}): EXISTENCE_VALIDATED,
    frozenset({FAMILY_GEOMETRY, FAMILY_DOCUMENT}): EXISTENCE_VALIDATED,
    frozenset({FAMILY_SYMBOL, FAMILY_DOCUMENT}): EXISTENCE_VALIDATED,
    # Correlated on one gap: the geometry that shows the gap is the geometry
    # that shows closing it closes the room.
    frozenset({FAMILY_CAD, FAMILY_SYMBOL}): EXISTENCE_VALIDATED,
    frozenset({FAMILY_CAD, FAMILY_DOCUMENT}): EXISTENCE_VALIDATED,
    frozenset({FAMILY_CAD, FAMILY_GEOMETRY}): EXISTENCE_VALIDATED,
    frozenset({FAMILY_GEOMETRY, FAMILY_TOPOLOGY}): EXISTENCE_PROBABLE,
    frozenset({FAMILY_GEOMETRY, FAMILY_SEMANTIC}): EXISTENCE_PROBABLE,
    frozenset({FAMILY_TOPOLOGY, FAMILY_SEMANTIC}): EXISTENCE_CANDIDATE,
}

# Which combinations fix WHERE it is. Every one of them contains a family that
# carries coordinates, and that is the whole rule.
GEOMETRY_BEARING = (FAMILY_GEOMETRY, FAMILY_CAD)

GEOMETRY_COMBINATIONS = {
    frozenset({FAMILY_GEOMETRY, FAMILY_SYMBOL}): GEOMETRY_VALIDATED,
    frozenset({FAMILY_GEOMETRY, FAMILY_DOCUMENT}): GEOMETRY_VALIDATED,
    frozenset({FAMILY_CAD, FAMILY_GEOMETRY}): GEOMETRY_VALIDATED,
    frozenset({FAMILY_CAD, FAMILY_SYMBOL}): GEOMETRY_VALIDATED,
    frozenset({FAMILY_CAD, FAMILY_DOCUMENT}): GEOMETRY_VALIDATED,
    frozenset({FAMILY_GEOMETRY, FAMILY_TOPOLOGY}): GEOMETRY_PROBABLE,
    frozenset({FAMILY_GEOMETRY, FAMILY_SEMANTIC}): GEOMETRY_PROBABLE,
}

# The geometry status a space-boundary edge needs before it may be drawn.
GEOMETRY_SUFFICIENT = (GEOMETRY_PROBABLE, GEOMETRY_VALIDATED)


def existence_status_for(families: set) -> tuple[str, str]:
    """Does a portal exist here? Non-geometric evidence counts fully."""
    fams = frozenset(families)
    if not fams:
        return EXISTENCE_UNRESOLVED, "no evidence of any kind"
    best = _best(EXISTENCE_COMBINATIONS, fams, EXISTENCE_RANK)
    if best is not None:
        st, key = best
        why = (f"{'+'.join(sorted(key))} is an approved existence combination"
               + (f" (with {'+'.join(sorted(fams - key))} also present)"
                  if fams - key else ""))
        if st == EXISTENCE_PROBABLE:
            why += (" — but these families are correlated on one gap, so it "
                    "caps at PROBABLE")
        return st, why
    if len(fams) == 1:
        return EXISTENCE_CANDIDATE, (
            f"{next(iter(fams))} alone. One family never validates a portal")
    if len(fams) >= 3:
        return EXISTENCE_PROBABLE, (
            f"{len(fams)} families ({'+'.join(sorted(fams))}) with no approved "
            "combination among them — capped at PROBABLE")
    return EXISTENCE_CANDIDATE, (
        f"{'+'.join(sorted(fams))} is not an approved existence combination")


def geometry_status_for(families: set) -> tuple[str, str]:
    """Do we know WHERE it is? Without a coordinate-bearing family, no.

    This is the refinement that matters: however strongly SYMBOL + DOCUMENT
    prove a door exists, neither of them says where its jambs fall. Drawing an
    exact closure line from non-geometric evidence would be inventing a
    measurement and calling it validated.
    """
    fams = frozenset(families)
    if not fams:
        return GEOMETRY_UNRESOLVED, "no evidence of any kind"
    if not (fams & set(GEOMETRY_BEARING)):
        return GEOMETRY_UNRESOLVED, (
            f"{'+'.join(sorted(fams))} may establish that a portal EXISTS, but "
            "no family here carries coordinates. Exact jambs, width and "
            "closure line remain unresolved, and a boundary must not be drawn "
            "from non-geometric evidence")
    best = _best(GEOMETRY_COMBINATIONS, fams, GEOMETRY_RANK)
    if best is not None:
        st, key = best
        why = (f"{'+'.join(sorted(key))} fixes the opening's position"
               + (f" (with {'+'.join(sorted(fams - key))} also present)"
                  if fams - key else "")
               + (" — correlated families, so it caps at PROBABLE"
                  if st == GEOMETRY_PROBABLE else ""))
        return st, why
    if len(fams) == 1:
        return GEOMETRY_CANDIDATE, (
            "geometry alone locates the gap but nothing corroborates that the "
            "gap is an opening rather than missing extraction")
    return GEOMETRY_PROBABLE, (
        f"{'+'.join(sorted(fams))} includes a coordinate-bearing family with "
        "corroboration, but is not an approved combination — capped at "
        "PROBABLE")


# ------------------------------------------------- an opening needs a host

# An opening floating between two unrelated walls is not a hole in a wall. It
# may still close a space, but it may not add its width to any wall's GROSS
# line, because there is no wall there whose gross line it could be part of.
HOST_UNRESOLVED = "HOST_WALL_UNRESOLVED"


@dataclass(frozen=True)
class HostedOpening:
    """A portal with the wall it is a hole in, named.

    `host_wall_band_id` is the gate on HOST_WALL_GROSS_LENGTH. Without it the
    opening still has a width and may still close a room, but it contributes
    nothing to a gross host-wall measurement, because nobody has said which
    wall it is gross of.
    """

    portal_id: str
    host_wall_band_id: str
    jamb_a_mm: float
    jamb_b_mm: float
    closure_line: tuple[tuple[float, float], tuple[float, float]]
    closure_basis: str
    why: str = ""

    @property
    def opening_width_mm(self) -> float:
        return abs(self.jamb_b_mm - self.jamb_a_mm)

    @property
    def has_host(self) -> bool:
        return bool(self.host_wall_band_id
                    and self.host_wall_band_id != HOST_UNRESOLVED)

    @property
    def contributes_host_gross(self) -> bool:
        """Only a hole in a NAMED wall belongs to that wall's gross line."""
        return self.has_host and bool(self.closure_basis)

    def record(self) -> dict:
        return {"portal_id": self.portal_id,
                "host_wall_band_id": self.host_wall_band_id or HOST_UNRESOLVED,
                "jamb_a_mm": round(self.jamb_a_mm, 1),
                "jamb_b_mm": round(self.jamb_b_mm, 1),
                "opening_width_mm": round(self.opening_width_mm, 1),
                "closure_line": [list(p) for p in self.closure_line],
                "closure_basis": self.closure_basis,
                "has_host": self.has_host,
                "contributes_host_gross": self.contributes_host_gross,
                "why": self.why}


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
        # §12 — an opening may only add to a GROSS HOST-WALL line once it has
        # said which wall it is a hole in. An opening floating between two
        # unrelated walls closes a space perfectly well and belongs to no
        # wall's gross measurement.
        if (self.boundary_type == HOST_WALL_OPENING and host
                and not self.host_wall_band_id):
            raise SpaceBoundaryError(
                f"{self.interval_id} claims {host} mm of HOST_WALL_GROSS "
                "without naming a host wall band. An opening between two "
                "unrelated walls is not a hole in either of them, and cannot "
                "join a gross line that belongs to neither")

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
    existence_status: str = EXISTENCE_UNRESOLVED
    geometry_status: str = GEOMETRY_UNRESOLVED
    existence_why: str = ""
    geometry_why: str = ""
    hosted: HostedOpening | None = None

    @property
    def span_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    @property
    def families(self) -> set:
        return {EVIDENCE_FAMILY[e] for e in self.evidence
                if e in EVIDENCE_FAMILY}

    @property
    def exists(self) -> bool:
        return self.existence_status in (EXISTENCE_PROBABLE,
                                         EXISTENCE_VALIDATED)

    @property
    def geometry_known(self) -> bool:
        return self.geometry_status in GEOMETRY_SUFFICIENT

    @property
    def may_close_a_space(self) -> bool:
        """A boundary EDGE is geometry, so GEOMETRY status is what gates it.

        A door proven to exist by SYMBOL + DOCUMENT but whose jambs nobody has
        located does not get a closure line drawn for it. Its existence is
        recorded and its geometry stays unresolved — which is a better report
        than a plausible line in roughly the right place.
        """
        return self.geometry_known

    def record(self) -> dict:
        return {"portal_id": self.portal_id, "space_id": self.space_id,
                "side": self.side, "span_mm": round(self.span_mm, 1),
                "status": self.status, "gap_class": self.gap_class,
                "evidence": list(self.evidence),
                "families": sorted(self.families),
                "existence_status": self.existence_status,
                "geometry_status": self.geometry_status,
                "existence_why": self.existence_why,
                "geometry_why": self.geometry_why,
                "portal_exists": self.exists,
                "portal_geometry_known": self.geometry_known,
                "hosted_opening": (self.hosted.record() if self.hosted
                                   else None),
                "may_close_a_space": self.may_close_a_space, "why": self.why}


def classify_gap(space_id: str, side: str, axis: str, fixed: float,
                 lo: float, hi: float, *, caps=(), bands_face_each_other: bool,
                 other_sides_complete: bool, swing_arcs=(),
                 host_wall_band_id: str = "",
                 closure_basis: str = "") -> PortalCandidate:
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
    ex_status, ex_why = existence_status_for(fams)
    geo_status, geo_why = geometry_status_for(fams)
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
    pid = f"PT-{space_id}-{side}-{int(lo)}"
    # §12 — the opening names the wall it is a hole in, or says it has none.
    # Without a host, the width is still a width and still closes a space; it
    # simply belongs to no wall's GROSS line, because no wall was named.
    line = (((lo, fixed), (hi, fixed)) if axis == "H"
            else ((fixed, lo), (fixed, hi)))
    hosted = HostedOpening(
        portal_id=pid, host_wall_band_id=host_wall_band_id or HOST_UNRESOLVED,
        jamb_a_mm=lo, jamb_b_mm=hi, closure_line=line,
        closure_basis=(closure_basis if geo_status in GEOMETRY_SUFFICIENT
                       else CLOSURE_BASIS_UNRESOLVED),
        why=("the wall band this opening interrupts" if host_wall_band_id else
             "no host wall band named: this opening is not part of any wall's "
             "gross line"))
    return PortalCandidate(
        portal_id=pid, space_id=space_id,
        side=side, axis=axis, fixed_mm=fixed, start_mm=lo, end_mm=hi,
        status=status, evidence=tuple(ev), gap_class=gap_class, why=why,
        existence_status=ex_status, geometry_status=geo_status,
        existence_why=ex_why, geometry_why=geo_why, hosted=hosted)


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
                # §12 — the host comes from the portal's own hosted-opening
                # record, by portal id. It is NOT taken from whichever band id
                # happens to sit first in this side's list.
                host_id = (p.hosted.host_wall_band_id
                           if p.hosted and p.hosted.has_host else "")
                hosted_gross = bool(p.hosted and p.hosted.contributes_host_gross)
                out.append(BoundaryInterval(
                    interval_id=f"BI-{space_id}-{n:03d}", space_id=space_id,
                    side=side, axis=d["axis"], fixed_mm=d["fixed"],
                    start_mm=a, end_mm=b, boundary_type=HOST_WALL_OPENING,
                    # FOUR FACTS. No material, a real opening, the room closes
                    # across it, and — WHEN IT HAS A HOST — the host wall
                    # continues through it for every trade whose approved rule
                    # is gross-then-deduct. Without a host the fourth fact is
                    # NOT ESTABLISHED, which is not the same as zero.
                    lengths=LengthSet(space_boundary_mm=L,
                                      host_wall_gross_mm=(L if hosted_gross
                                                          else None),
                                      material_present_mm=0.0, opening_mm=L),
                    portal_id=p.portal_id, closure_basis=closure_basis,
                    jamb_ids=tuple(p.evidence),
                    host_wall_band_id=host_id,
                    why=("a supported opening in a host wall. Zero material "
                         "stands here; the room closes across it; and the "
                         "gross host-wall line runs through it"
                         if hosted_gross else
                         "a supported opening with no named host wall band. "
                         "It closes the space; it joins no gross line")))
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
    return total(intervals, MATERIAL_PRESENT_LENGTH)


# ------------------------------------------------- how good is a closure?

# §8 — "BED-01 closes" was true of a MODEL, not of the building. The interval
# model walks four sides taken from a bounding box, and BED-01 fills 77.3% of
# its own box. A closure proved that way is a diagnostic result: it says the
# sides we looked at were covered, not that a polygon exists.
NOT_CLOSED = "NOT_CLOSED"
DIAGNOSTIC_INTERVAL_CLOSURE = "DIAGNOSTIC_INTERVAL_CLOSURE"
VALIDATED_PHYSICAL_FACE = "VALIDATED_PHYSICAL_FACE"

CLOSURE_GRADES = (NOT_CLOSED, DIAGNOSTIC_INTERVAL_CLOSURE,
                  VALIDATED_PHYSICAL_FACE)


def space_closes(intervals) -> bool:
    """Is every interval either wall or a supported host-wall opening?

    A MODEL result. `closure_grade` is the one to report, because this answer
    alone reads as a claim about the building.
    """
    return all(i.boundary_type in (PHYSICAL_WALL, HOST_WALL_OPENING)
               for i in intervals)


def closure_grade(intervals, *, vector_face_id: str = "",
                  interval_sides_from_bbox: bool = True) -> dict:
    """How much a closure is worth: a covered model, or a real polygon.

    Only a face generated by planar topology on the space boundary graph is a
    VALIDATED_PHYSICAL_FACE. Interval coverage over four sides earns
    DIAGNOSTIC_INTERVAL_CLOSURE and no more, and says why in the same breath —
    the sides it covered came from a rectangle nobody proved.
    """
    if not space_closes(intervals):
        return {"closure_grade": NOT_CLOSED, "vector_face_id": "",
                "why": ("at least one interval is neither wall nor a "
                        "geometry-supported opening")}
    if vector_face_id:
        return {"closure_grade": VALIDATED_PHYSICAL_FACE,
                "vector_face_id": vector_face_id,
                "why": ("a planar face on the SPACE_BOUNDARY_GRAPH encloses "
                        "this space: the polygon exists, it was not assumed")}
    return {
        "closure_grade": DIAGNOSTIC_INTERVAL_CLOSURE, "vector_face_id": "",
        "why": ("every interval of the modelled boundary is covered, but no "
                "planar face has been generated for this space. "
                + ("The sides walked came from a bounding box, and a room "
                   "that fills 77% of its box has sides the box invented — so "
                   "this is a statement about the model, not about the "
                   "building" if interval_sides_from_bbox else
                   "The closure is a property of the interval model"))}


# §13 — an explicit numerical tolerance, so "holds" means something checkable
# rather than "close enough for the number I happened to print".
TOLERANCE_M = 0.001

# The conditions under which the host-wall identity is simply not the right
# equation. Each one is a real geometry, not an excuse.
EXCL_OPEN_PLAN = "OPEN_PLAN_TRANSITION_CARRIES_NO_HOST_WALL"
EXCL_UNHOSTED = "OPENING_WITH_NO_NAMED_HOST_WALL"
EXCL_CURVED = "NON_AXIS_ALIGNED_OR_CURVED_BOUNDARY"
EXCL_MIXED_BASIS = "MIXED_CLOSURE_BASES_ON_ONE_BOUNDARY"


def applicability(intervals) -> dict:
    """Does the host-wall identity even apply to this boundary?

    Forcing the equation everywhere would be its own error: an open-plan edge
    has no host wall to be gross of, so the identity is not violated there — it
    is not the applicable rule. The invariant has to know that.
    """
    exclusions = []
    if any(i.boundary_type == OPEN_PLAN_VIRTUAL for i in intervals):
        exclusions.append(EXCL_OPEN_PLAN)
    if any(i.boundary_type == HOST_WALL_OPENING and not i.host_wall_band_id
           for i in intervals):
        exclusions.append(EXCL_UNHOSTED)
    if any(i.axis not in ("H", "V") for i in intervals):
        exclusions.append(EXCL_CURVED)
    bases = {i.closure_basis for i in intervals
             if i.boundary_type == HOST_WALL_OPENING and i.closure_basis}
    if len(bases) > 1:
        exclusions.append(EXCL_MIXED_BASIS)
    return {"applies": not exclusions, "exclusions": exclusions,
            "why": ("simple hosted openings on one basis: the identity applies"
                    if not exclusions else
                    "the identity is not the applicable rule here: "
                    + ", ".join(exclusions))}


def reconcile(intervals) -> dict:
    """All five bases side by side, with the identity that should hold.

    For a room hosted by continuous walls and doors:

        HOST_WALL_GROSS = MATERIAL_PRESENT + supported HOST-WALL OPENINGS

    Reported rather than enforced: an open-plan edge carries no host wall at
    all, so the identity does not apply to every room, and forcing it where
    geometry makes it inapplicable would be its own error.
    """
    host = total(intervals, HOST_WALL_GROSS_LENGTH)
    mat = total(intervals, MATERIAL_PRESENT_LENGTH)
    opening = sum(i.lengths.opening_mm or 0.0 for i in intervals
                  if i.boundary_type == HOST_WALL_OPENING
                  and i.lengths.host_wall_gross_mm is not None) / 1000
    resid = host - (mat + opening)
    app = applicability(intervals)
    return {
        "space_boundary_length_m": round(
            total(intervals, SPACE_BOUNDARY_LENGTH), 3),
        "host_wall_gross_length_m": round(host, 3),
        "material_present_length_m": round(mat, 3),
        "opening_length_m": round(opening, 3),
        "identity_residual_m": round(resid, 3),
        "identity_applies": app["applies"],
        "identity_not_applicable_because": app["exclusions"],
        # §13 — an identity that does not apply is NOT a passing identity and
        # NOT a failing one. Reporting `holds: True` for a room the rule never
        # covered is how a vacuous pass becomes evidence of correctness.
        "identity_holds": (abs(resid) < TOLERANCE_M if app["applies"]
                           else None),
        "identity_tolerance_m": TOLERANCE_M,
        "identity": ("HOST_WALL_GROSS = MATERIAL_PRESENT + HOSTED OPENINGS, "
                     "for simple hosted openings on axis-aligned boundaries "
                     "measured on one basis. It does NOT apply to open-plan "
                     "transitions, curved geometry, mixed centreline/"
                     "finish-face bases, or non-hosted virtual boundaries"),
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
