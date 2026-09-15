"""E101 — a doorway means three different things, so it gets three models.

Round 3's report said "reopening every portal dropped topology recall from
75% to 58.3%", and that sentence was the symptom of a conflation: one
binary portal operation was being asked to serve three questions at once.

    MATERIAL_GEOMETRY        is there wall material across the opening?
                             NO. Zero. Blockwork, plaster, deductions.

    ROOM_PARTITION_TOPOLOGY  are these two distinct physical spaces?
                             YES. The doorway closes the ROOM boundary
                             VIRTUALLY, with zero material.

    NAVIGABLE_FREE_SPACE     can a person walk through?
                             YES. Open. Circulation only.

A bedroom and its ensuite are one opening, two rooms and one navigable
connection SIMULTANEOUSLY, and a system that cannot hold all three at once
will keep trading one for another. Navigability must never define QS room
identity: that is what merged the rooms.

The rule that makes this generalise across architects (§3): DRAWN DOOR INK
IS EVIDENCE, NOT A BOUNDARY. A leaf, a swing arc, a threshold or a jamb
symbol may support the claim that a portal exists. None of them may become
the room's boundary merely because rasterising the sheet turned its ink
into a barrier — one architect hatches thresholds and another does not, and
a room topology that depends on which is a room topology that does not
travel.

So the room partition is built from WALL MATERIAL plus explicit
PORTAL_PARTITION_BOUNDARY objects, each carrying zero material and its own
evidence grade. Uncertainty about a portal makes the PARTITION diagnostic;
it never merges the rooms (§5).
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine.evidence_tiers import (GRADE_RANK, PORTAL_DOCUMENT_VALIDATED,
                                   PORTAL_DRAWING_VALIDATED,
                                   PORTAL_SOURCE_VALIDATED,
                                   PORTAL_UNVALIDATED)

# The three models. Named so a caller must say which question it is asking.
MATERIAL_GEOMETRY = "MATERIAL_GEOMETRY"
ROOM_PARTITION_TOPOLOGY = "ROOM_PARTITION_TOPOLOGY"
NAVIGABLE_FREE_SPACE = "NAVIGABLE_FREE_SPACE"

MODELS = (MATERIAL_GEOMETRY, ROOM_PARTITION_TOPOLOGY, NAVIGABLE_FREE_SPACE)

WHAT_EACH_MODEL_IS_FOR = {
    MATERIAL_GEOMETRY: (
        "blockwork, plaster, opening deductions, wall material. A doorway "
        "is OPEN here and carries zero material"),
    ROOM_PARTITION_TOPOLOGY: (
        "room polygons, floor areas, room identity, bedroom vs bathroom. A "
        "doorway CLOSES the room boundary virtually, still with zero "
        "material"),
    NAVIGABLE_FREE_SPACE: (
        "circulation and connectivity, if and when they are needed. A "
        "doorway is PASSABLE here. This model may NEVER define room "
        "identity"),
}

# What the partition can claim, by the evidence behind its portals (§5).
PARTITION_RELEASABLE = "ROOM_PARTITION_RELEASABLE"
PARTITION_DIAGNOSTIC = "ROOM_PARTITION_DIAGNOSTIC"
PARTITION_UNRESOLVED = "ROOM_PARTITION_UNRESOLVED"

# A partition may be released only from this grade up. Below it the
# partition still EXISTS — it is simply diagnostic.
RELEASABLE_FROM = PORTAL_DRAWING_VALIDATED


@dataclass(frozen=True)
class PortalPartitionBoundary:
    """A room boundary across an opening. ZERO MATERIAL, by definition.

    §4. This participates in ROOM_PARTITION_TOPOLOGY and never in the
    MATERIAL wall solid. Its four length measures follow the existing
    ontology, and `material_present_length_mm` is zero — not unknown, not
    small: there is no material across a doorway, and a trade that needs
    material must ask for the measure that says so.
    """

    boundary_id: str
    portal_id: str
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    host_wall_band_id: str = ""
    evidence_grade: str = PORTAL_UNVALIDATED
    why: str = ""

    @property
    def opening_length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    @property
    def space_boundary_length_mm(self) -> float:
        """The room's boundary DOES run across the opening."""
        return self.opening_length_mm

    @property
    def host_wall_gross_length_mm(self) -> float:
        """The host wall's gross run includes the opening it hosts."""
        return self.opening_length_mm

    @property
    def material_present_length_mm(self) -> float:
        """Zero. There is no wall material across a doorway."""
        return 0.0

    @property
    def may_release(self) -> bool:
        return (GRADE_RANK.get(self.evidence_grade, 0)
                >= GRADE_RANK[RELEASABLE_FROM])

    def record(self) -> dict:
        return {
            "boundary_id": self.boundary_id,
            "portal_id": self.portal_id,
            "axis": self.axis,
            "fixed_mm": round(self.fixed_mm, 2),
            "interval_mm": [round(self.start_mm, 2), round(self.end_mm, 2)],
            "host_wall_band_id": self.host_wall_band_id,
            "evidence_grade": self.evidence_grade,
            "may_release": self.may_release,
            "lengths_mm": {
                "SPACE_BOUNDARY_LENGTH": round(
                    self.space_boundary_length_mm, 1),
                "HOST_WALL_GROSS_LENGTH": round(
                    self.host_wall_gross_length_mm, 1),
                "MATERIAL_PRESENT_LENGTH": self.material_present_length_mm,
                "OPENING_LENGTH": round(self.opening_length_mm, 1),
            },
            "participates_in": ROOM_PARTITION_TOPOLOGY,
            "never_participates_in": (
                f"{MATERIAL_GEOMETRY}: this boundary carries zero material, "
                "so it may not enter a wall solid or a material quantity"),
            "why": self.why,
        }


@dataclass(frozen=True)
class Answer:
    """One model's answer about one pair of spaces."""

    model: str
    connected: bool
    basis: str
    status: str = ""

    def record(self) -> dict:
        return {"model": self.model, "connected": self.connected,
                "status": self.status, "basis": self.basis,
                "used_for": WHAT_EACH_MODEL_IS_FOR[self.model]}


@dataclass
class Report:
    """All three answers, for every pair of spaces that share a portal."""

    rows: list = field(default_factory=list)
    boundaries: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    @property
    def output_hash(self) -> str:
        payload = "|".join(
            f"{r['between'][0]}-{r['between'][1]}:"
            f"{r['ROOM_PARTITION_TOPOLOGY']['status']}" for r in self.rows)
        payload += "||" + "|".join(
            f"{b.boundary_id}:{b.evidence_grade}" for b in self.boundaries)
        return hashlib.sha256(payload.encode()).hexdigest()[:24]

    def record(self) -> dict:
        part = [r[ROOM_PARTITION_TOPOLOGY] for r in self.rows]
        return {
            "THREE_TOPOLOGY_OUTPUT_HASH": self.output_hash,
            "models": list(MODELS),
            "what_each_model_is_for": dict(WHAT_EACH_MODEL_IS_FOR),
            "pairs": len(self.rows),
            "partition_by_status": dict(Counter(
                a["status"] for a in part)),
            "material_openings": sum(
                1 for r in self.rows
                if r[MATERIAL_GEOMETRY]["connected"]),
            "navigable_connections": sum(
                1 for r in self.rows
                if r[NAVIGABLE_FREE_SPACE]["connected"]),
            "rooms_kept_distinct": sum(
                1 for r in self.rows
                if not r[ROOM_PARTITION_TOPOLOGY]["connected"]),
            "portal_partition_boundaries": [
                b.record() for b in self.boundaries],
            "total_partition_boundary_length_m": round(sum(
                b.space_boundary_length_mm for b in self.boundaries)
                / 1000, 3),
            "total_partition_material_length_m": round(sum(
                b.material_present_length_mm for b in self.boundaries)
                / 1000, 3),
            "rows": list(self.rows),
            "the_conflation_this_prevents": (
                "one binary portal operation cannot serve three questions. "
                "A bedroom and its ensuite are one opening, two rooms and "
                "one navigable connection at the same time, and a system "
                "that holds only one of those keeps trading it for another"),
            "why_door_ink_is_not_a_boundary": (
                "a leaf, a swing arc or a threshold is EVIDENCE that a "
                "portal exists. None of them may become the room's "
                "boundary because rasterising the sheet turned its ink "
                "into a barrier: one architect hatches thresholds and "
                "another does not, so a room topology resting on that does "
                "not travel between architects"),
            "notes": dict(self.notes),
        }


def answer_pair(space_a: str, space_b: str, *, portal=None,
                material_between: bool = False) -> dict:
    """The three answers for one pair of spaces.

    `portal` is a PortalPartitionBoundary or None. `material_between` says
    whether continuous wall material separates the pair apart from any
    opening.
    """
    material_connected = (not material_between) and portal is not None
    if portal is None and not material_between:
        # Nothing separates them and no portal explains a connection: this
        # is an unresolved gap, not a doorway.
        material_connected = True

    if portal is not None:
        partition_connected = False
        status = (PARTITION_RELEASABLE if portal.may_release
                  else PARTITION_DIAGNOSTIC)
        partition_basis = (
            f"a PORTAL_PARTITION_BOUNDARY closes the room boundary across "
            f"the opening with zero material, on {portal.evidence_grade} "
            "evidence. The rooms stay distinct; the grade decides whether "
            "the partition may be released")
        nav_connected = True
        nav_basis = ("the opening is passable. This says nothing about "
                     "whether they are one room")
    elif material_between:
        partition_connected = False
        status = PARTITION_RELEASABLE
        partition_basis = ("continuous wall material separates them. No "
                           "portal is needed to keep them distinct")
        nav_connected = False
        nav_basis = "no opening connects them"
    else:
        partition_connected = True
        status = PARTITION_UNRESOLVED
        partition_basis = (
            "no material separates them and no portal evidence explains "
            "the gap, so whether these are one space or two is UNRESOLVED. "
            "They are reported as one region and may not be released as "
            "either")
        nav_connected = True
        nav_basis = "the gap is open, whatever it turns out to be"

    return {
        "between": [space_a, space_b],
        MATERIAL_GEOMETRY: Answer(
            MATERIAL_GEOMETRY, material_connected,
            ("there is no wall material across the opening"
             if material_connected else
             "continuous wall material stands between them")).record(),
        ROOM_PARTITION_TOPOLOGY: Answer(
            ROOM_PARTITION_TOPOLOGY, partition_connected, partition_basis,
            status).record(),
        NAVIGABLE_FREE_SPACE: Answer(
            NAVIGABLE_FREE_SPACE, nav_connected, nav_basis).record(),
    }


def boundary_from_portal(portal, grade: str, *, boundary_id: str = ""
                         ) -> PortalPartitionBoundary:
    """Build the partition boundary for one graded portal."""
    axis = getattr(portal, "axis", "")
    lo = min(getattr(portal, "jamb_a_mm", 0.0),
             getattr(portal, "jamb_b_mm", 0.0))
    hi = max(getattr(portal, "jamb_a_mm", 0.0),
             getattr(portal, "jamb_b_mm", 0.0))
    poly = getattr(portal, "polygon", None)
    fixed = 0.0
    if poly is not None and not poly.is_empty:
        minx, miny, maxx, maxy = poly.bounds
        fixed = (miny + maxy) / 2.0 if axis == "H" else (minx + maxx) / 2.0
    pid = getattr(portal, "portal_id", "")
    return PortalPartitionBoundary(
        boundary_id=boundary_id or f"PPB-{pid}", portal_id=pid, axis=axis,
        fixed_mm=fixed, start_mm=lo, end_mm=hi,
        host_wall_band_id=getattr(portal, "host_wall_band_id", ""),
        evidence_grade=grade,
        why=("closes the room boundary across a drawn opening with zero "
             "material. It exists because a portal is supported here, not "
             "because any door graphic closed a pixel"))


def build(pairs, *, boundaries=(), notes=None) -> Report:
    """`pairs` is an iterable of (space_a, space_b, portal, material)."""
    rep = Report(boundaries=list(boundaries), notes=dict(notes or {}))
    for a, b, portal, material in pairs:
        rep.rows.append(answer_pair(a, b, portal=portal,
                                    material_between=material))
    rep.notes.setdefault("door_ink_used_as_a_boundary", 0)
    return rep


def partition_status(boundaries) -> dict:
    """What the room partition as a whole may claim."""
    items = list(boundaries)
    if not items:
        return {"status": PARTITION_RELEASABLE,
                "why": "no opening participates in this partition"}
    weakest = min(GRADE_RANK.get(b.evidence_grade, 0) for b in items)
    status = (PARTITION_RELEASABLE
              if weakest >= GRADE_RANK[RELEASABLE_FROM]
              else PARTITION_DIAGNOSTIC)
    return {
        "status": status,
        "boundaries": len(items),
        "by_grade": dict(Counter(b.evidence_grade for b in items)),
        "weakest_grade": next(
            g for g, r in sorted(GRADE_RANK.items(), key=lambda kv: kv[1])
            if r == weakest),
        "why": (
            "every opening this partition depends on is validated to at "
            f"least {RELEASABLE_FROM}"
            if status == PARTITION_RELEASABLE else
            "at least one opening this partition depends on is not "
            "validated to the releasable grade. The partition still "
            "EXISTS and the rooms stay distinct — it is DIAGNOSTIC, which "
            "is different from merging them"),
        "what_uncertainty_does_not_do": (
            "merge the two rooms. Treating an unproven doorway as "
            "navigable and calling the result one space is how a bedroom "
            "and a bathroom became one region"),
    }
