"""A gap in a wall is not a door, and a door is not a width.

Round 3 measured 2 spaces on P7757 and released none. It traced the cause
exactly: `SALOON`'s left side is drawn in two pieces and then stops, and
nothing wall-like stands across the remaining stretch. The enclosure's
refusal was correct — something must close that side, and the only honest
candidate is an OPENING.

The temptation is obvious and it is the one thing this round forbids:

    DO NOT SOLVE THIS BY BRIDGING EVERY GAP.

Bridging every gap would close every room, and it would do it by asserting
material and topology that nobody drew. So this module produces HYPOTHESES
with EVIDENCE, and the grade of that evidence decides what the hypothesis
is allowed to do:

    GRADE A   a transformed door assembly — one INSERT whose resolved
              geometry is a door — landing in a wall interruption whose
              jambs correspond to it
    GRADE B   swing or leaf geometry plus a supported wall interruption
    GRADE C   supported opening geometry: the wall is pierced through both
              faces and its reveals are drawn, but no door is
    GRADE D   a gap, and nothing else

    WALL GAP ALONE CANNOT CREATE A ROOM-PARTITION PORTAL.

Grade D closes nothing, ever. That is the whole safety property, and it is
why P7757 may still measure zero rooms after this round: if the drawing
really does have unexplained holes, unexplained holes is the answer.

CLASS COMES FROM EVIDENCE, NEVER FROM WIDTH

A 900 mm hole is not a door because it is 900 mm wide, and a 3 m hole is
not an archway because it is 3 m wide. Width is MEASURED and REPORTED —
three times over, from three independent sources that are compared and
never averaged — but no class is inferred from it.

BLOCK NAMES ARE EVIDENCE, NOT AUTHORITY

`if block starts with "D": portal = True` is forbidden, and nothing here
does it. A block's NAME contributes one supporting observation; its
resolved GEOMETRY — translated, rotated, scaled, nested — is what has to
land in a real wall interruption before anything is graded above D.

A WINDOW IS NOT A DOOR

A window interrupts material and keeps the room boundary. It is not a
passage, and it may never leak a room polygon out to the exterior.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from engine import cad_profile as cprofile
from engine import space_enclosure as enc
from engine.boundary_authority import ROOM_BOUNDARY_ELIGIBLE

CLASSIFIER = "CAD_OPENING_EVIDENCE_CLASSIFIER_V1"

# ------------------------------------------------------------- the ontology
DOOR_WITH_LEAF = "DOOR_WITH_LEAF"
DOOR_PORTAL = "DOOR_PORTAL"
DOORLESS_ARCHWAY = "DOORLESS_ARCHWAY"
WINDOW_OPENING = "WINDOW_OPENING"
OPEN_PLAN_CONNECTION = "OPEN_PLAN_CONNECTION"
UNRESOLVED_WALL_GAP = "UNRESOLVED_WALL_GAP"
NON_OPENING_GEOMETRY = "NON_OPENING_GEOMETRY"
UNKNOWN = "UNKNOWN"

CLASSES = (DOOR_WITH_LEAF, DOOR_PORTAL, DOORLESS_ARCHWAY, WINDOW_OPENING,
           OPEN_PLAN_CONNECTION, UNRESOLVED_WALL_GAP, NON_OPENING_GEOMETRY,
           UNKNOWN)

WHERE_EACH_CLASS_COMES_FROM = {
    DOOR_WITH_LEAF: "a wall interruption with a door leaf drawn in it",
    DOOR_PORTAL: "a wall interruption with a swing arc or a resolved door "
                 "assembly, but no leaf line",
    DOORLESS_ARCHWAY: "a wall pierced through both faces with its reveals "
                      "drawn, and no door symbol of any kind",
    WINDOW_OPENING: "a wall interruption spanned by window lines",
    OPEN_PLAN_CONNECTION: "NOT produced here. It is produced by the "
                          "room-partition graph, where two identities share "
                          "one geometric face with no partition between "
                          "them. There is no gap to classify in that case",
    UNRESOLVED_WALL_GAP: "a gap between two collinear wall runs, with no "
                         "reveal and no symbol. Grade D. It closes nothing",
    NON_OPENING_GEOMETRY: "one face is interrupted while the other face of "
                          "the same wall runs continuously across it — "
                          "material still stands there, so it is a drafting "
                          "break or a fixture, not an opening",
    UNKNOWN: "evidence exists but does not compose into any of the above",
}

# ------------------------------------------------------------- the grades
GRADE_A = "GRADE_A_TRANSFORMED_DOOR_ASSEMBLY_WITH_JAMB_CORRESPONDENCE"
GRADE_B = "GRADE_B_SWING_OR_LEAF_WITH_SUPPORTED_INTERRUPTION"
GRADE_C = "GRADE_C_SUPPORTED_OPENING_GEOMETRY_NO_DOOR"
GRADE_D = "GRADE_D_WALL_GAP_ONLY"
GRADE_NONE = "NO_OPENING_EVIDENCE"

GRADE_RANK = {GRADE_NONE: -1, GRADE_D: 0, GRADE_C: 1, GRADE_B: 2,
              GRADE_A: 3}

# What each grade is ALLOWED to do. This table is the safety property.
MAY_CLOSE_BOUNDARY_FROM = GRADE_C      # may close a room polygon
MAY_PARTITION_FROM = GRADE_B           # may assert two distinct rooms

# ------------------------------------------------------------- the evidence
E_FACE_INTERRUPTION = "WALL_FACE_INTERRUPTION"
E_THROUGH_INTERRUPTION = "BOTH_WALL_FACES_INTERRUPTED_OVER_ONE_INTERVAL"
E_OPPOSITE_FACE_CONTINUOUS = "OPPOSITE_FACE_RUNS_CONTINUOUSLY_ACROSS_IT"
E_JAMB = "JAMB_OR_REVEAL_DRAWN_AT_AN_END"
E_JAMBS_BOTH_ENDS = "JAMBS_DRAWN_AT_BOTH_ENDS"
E_SWING_ARC = "SWING_ARC_CENTRED_ON_A_JAMB"
E_DOOR_LEAF = "DOOR_LEAF_LINE_FROM_A_JAMB"
E_BLOCK_ASSEMBLY = "ONE_TRANSFORMED_INSERT_SUPPLIES_THE_DOOR_GEOMETRY"
E_BLOCK_NAME = "BLOCK_NAME_IS_CONSISTENT_WITH_A_DOOR"
E_WINDOW_LINES = "LINES_PARALLEL_TO_THE_WALL_SPAN_THE_INTERRUPTION"
E_AUTHORED_DIMENSION = "AN_AUTHORED_DIMENSION_BRACKETS_THE_INTERRUPTION"
E_SYMBOL_SPANS_THE_OPENING = "THE_DOOR_GEOMETRY_SPANS_THE_OPENING"
E_SYMBOL_DOES_NOT_SPAN = "THE_DOOR_GEOMETRY_DOES_NOT_SPAN_THE_OPENING"

# --------------------------------------------------------- frozen tolerances
#
# Every one of these is DERIVED from a constant this engine already froze
# in an earlier round, so round 4 introduces no new tuned number. That is
# not a stylistic preference: a fresh tolerance chosen while looking at
# P7757 would be a P7757 rule wearing a general name.

# A gap the frozen enclosure would itself flood straight across is not a
# gap. `space_enclosure.JUNCTION_REACH_MM`.
MIN_GAP_MM = enc.JUNCTION_REACH_MM

# Two lines are the same line when they agree to the enclosure's own
# collinearity tolerance.
COLLINEAR_TOL_MM = enc.COLLINEAR_JOIN_MM

# How near a mark must be to a gap end to be AT that gap end. The smallest
# separation this engine will call a wall — anything inside it is not a
# separate place. `cad_profile.MIN_WALL_THICKNESS_MM`.
JAMB_REACH_MM = cprofile.MIN_WALL_THICKNESS_MM

# The band within which two parallel faces are the two faces of ONE wall.
# The profile's own paired-face band, unchanged.
MIN_WALL_MM = cprofile.MIN_WALL_THICKNESS_MM
MAX_WALL_MM = cprofile.MAX_WALL_THICKNESS_MM


@dataclass(frozen=True)
class Interruption:
    """A stretch of one wall face with no line on it, between two runs."""

    interruption_id: str
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    left_band: str
    right_band: str

    @property
    def length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    def record(self) -> dict:
        return {"interruption_id": self.interruption_id, "axis": self.axis,
                "fixed_mm": round(self.fixed_mm, 2),
                "interval_mm": [round(self.start_mm, 2),
                                round(self.end_mm, 2)],
                "length_mm": round(self.length_mm, 1),
                "between_bands": [self.left_band, self.right_band]}


@dataclass(frozen=True)
class WidthObservations:
    """Three independent readings of one width. NEVER averaged."""

    geometric_mm: float | None = None
    block_name_raw: str = ""
    block_name_as_mm: float | None = None
    block_name_as_cm_in_mm: float | None = None
    dimension_display: float | None = None
    dimension_normalized_mm: float | None = None

    def _verdict(self, value) -> str:
        if value is None or self.geometric_mm is None:
            return "NOT_PRESENT"
        return ("AGREE" if abs(value - self.geometric_mm) <= JAMB_REACH_MM
                else "DISAGREE")

    @property
    def block_name_reading(self) -> str:
        """Which unit reading of the name, if either, matches geometry."""
        if self._verdict(self.block_name_as_mm) == "AGREE":
            return "AS_MILLIMETRES"
        if self._verdict(self.block_name_as_cm_in_mm) == "AGREE":
            return "AS_CENTIMETRES"
        if self.block_name_raw:
            return "NEITHER_READING_AGREES"
        return "NOT_PRESENT"

    def record(self) -> dict:
        return {
            "GEOMETRIC_OPENING_WIDTH_MM": (
                None if self.geometric_mm is None
                else round(self.geometric_mm, 1)),
            "BLOCK_NAME_WIDTH_OBSERVATION": {
                "raw": self.block_name_raw,
                "read_as_millimetres": self.block_name_as_mm,
                "read_as_centimetres_in_mm": self.block_name_as_cm_in_mm,
                "which_reading_agrees_with_geometry":
                    self.block_name_reading,
                "authority": ("NONE. A name is a supporting observation. "
                              "The geometry is the measurement"),
            },
            "DIMENSION_WIDTH_OBSERVATION": {
                "display_value": self.dimension_display,
                "normalized_mm": (
                    None if self.dimension_normalized_mm is None
                    else round(self.dimension_normalized_mm, 1)),
                "verdict": self._verdict(self.dimension_normalized_mm),
            },
            "never": ("these three are never averaged. Where they "
                      "disagree, the disagreement is the finding"),
        }


@dataclass(frozen=True)
class Opening:
    """One opening HYPOTHESIS, with everything that supports it."""

    opening_id: str
    region_id: str
    opening_class: str
    grade: str
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    host_bands: tuple = ()
    wall_faces_mm: tuple = ()
    widths: WidthObservations = field(default_factory=WidthObservations)
    evidence: tuple = ()
    symbol_ids: tuple = ()
    block_names: tuple = ()
    leaf_length_mm: float | None = None
    swing_radius_mm: float | None = None
    why: str = ""
    host_status: str = "HOST_ESTABLISHED"

    @property
    def opening_length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    @property
    def may_close_boundary(self) -> bool:
        """May this close a room polygon at all?"""
        if self.host_status != "HOST_ESTABLISHED":
            return False
        if self.opening_class in (UNRESOLVED_WALL_GAP, NON_OPENING_GEOMETRY,
                                  UNKNOWN):
            return False
        return GRADE_RANK[self.grade] >= GRADE_RANK[MAY_CLOSE_BOUNDARY_FROM]

    @property
    def may_partition_rooms(self) -> bool:
        """May this assert TWO DISTINCT PHYSICAL SPACES?

        Doors only, and only from grade B. An archway may close a polygon
        and still leave the relation UNRESOLVED (§7), and a window is not
        a room-to-room relation at all (§9).
        """
        if self.opening_class not in (DOOR_WITH_LEAF, DOOR_PORTAL):
            return False
        if self.host_status != "HOST_ESTABLISHED":
            return False
        return GRADE_RANK[self.grade] >= GRADE_RANK[MAY_PARTITION_FROM]

    @property
    def is_navigable(self) -> bool:
        """A window is not a passage."""
        return self.opening_class in (DOOR_WITH_LEAF, DOOR_PORTAL,
                                      DOORLESS_ARCHWAY,
                                      OPEN_PLAN_CONNECTION)

    def record(self) -> dict:
        return {
            "opening_id": self.opening_id,
            "drawing_region_id": self.region_id,
            "opening_class": self.opening_class,
            "evidence_grade": self.grade,
            "axis": self.axis,
            "fixed_mm": round(self.fixed_mm, 2),
            "interval_mm": [round(self.start_mm, 2), round(self.end_mm, 2)],
            "OPENING_LENGTH_MM": round(self.opening_length_mm, 1),
            "host_wall_bands": list(self.host_bands),
            "host_status": self.host_status,
            "wall_faces_mm": [round(v, 2) for v in self.wall_faces_mm],
            "widths": self.widths.record(),
            "evidence": list(self.evidence),
            "symbol_provenance": list(self.symbol_ids),
            "block_names_observed": list(self.block_names),
            "leaf_length_observation_mm": (
                None if self.leaf_length_mm is None
                else round(self.leaf_length_mm, 1)),
            "swing_radius_observation_mm": (
                None if self.swing_radius_mm is None
                else round(self.swing_radius_mm, 1)),
            "may_close_a_room_boundary": self.may_close_boundary,
            "may_assert_two_distinct_rooms": self.may_partition_rooms,
            "navigable": self.is_navigable,
            "why": self.why,
        }


@dataclass
class OpeningReport:
    openings: list = field(default_factory=list)
    interruptions: list = field(default_factory=list)
    unmatched_symbols: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def by_class(self) -> dict:
        return dict(Counter(o.opening_class for o in self.openings
                            ).most_common())

    def by_grade(self) -> dict:
        return dict(Counter(o.grade for o in self.openings).most_common())

    def doors(self) -> list:
        return [o for o in self.openings
                if o.opening_class in (DOOR_WITH_LEAF, DOOR_PORTAL)]

    def windows(self) -> list:
        return [o for o in self.openings
                if o.opening_class == WINDOW_OPENING]

    def doorless(self) -> list:
        return [o for o in self.openings
                if o.opening_class in (DOORLESS_ARCHWAY,
                                       OPEN_PLAN_CONNECTION)]

    def unresolved_gaps(self) -> list:
        return [o for o in self.openings
                if o.opening_class == UNRESOLVED_WALL_GAP]

    def closing(self) -> list:
        return [o for o in self.openings if o.may_close_boundary]

    def counts(self) -> dict:
        return {
            "wall_interruptions": len(self.interruptions),
            "opening_hypotheses": len(self.openings),
            "door_candidates": len(self.doors()),
            "window_candidates": len(self.windows()),
            "doorless_openings": len(self.doorless()),
            "unresolved_wall_gaps": len(self.unresolved_gaps()),
            "may_close_a_boundary": len(self.closing()),
            "may_partition_rooms": sum(1 for o in self.openings
                                       if o.may_partition_rooms),
            "unmatched_door_symbols": len(self.unmatched_symbols),
            "by_class": self.by_class(),
            "by_grade": self.by_grade(),
        }

    def record(self, *, limit: int = 40) -> dict:
        return {
            "classifier": CLASSIFIER,
            "CAD_OPENING_CLASSIFIER_HASH": classifier_hash(),
            "classes": list(CLASSES),
            "where_each_class_comes_from": dict(WHERE_EACH_CLASS_COMES_FROM),
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "openings": [o.record() for o in self.openings[:limit]],
            "unmatched_symbols": list(self.unmatched_symbols[:limit]),
            "the_invariant": (
                "WALL GAP ALONE CANNOT CREATE A ROOM-PARTITION PORTAL. "
                "Grade D closes nothing; a window never becomes a "
                "room-to-room passage; a name never promotes a grade"),
            "notes": dict(self.notes),
        }


def frozen_parameters() -> dict:
    return {
        "CLASSIFIER": CLASSIFIER,
        "MIN_GAP_MM": MIN_GAP_MM,
        "COLLINEAR_TOL_MM": COLLINEAR_TOL_MM,
        "JAMB_REACH_MM": JAMB_REACH_MM,
        "WALL_BAND_MM": [MIN_WALL_MM, MAX_WALL_MM],
        "MAY_CLOSE_BOUNDARY_FROM": MAY_CLOSE_BOUNDARY_FROM,
        "MAY_PARTITION_FROM": MAY_PARTITION_FROM,
        "why": {
            "no_new_number": (
                "every tolerance here is an earlier round's frozen "
                "constant: the enclosure's junction reach and collinearity "
                "tolerance, and the profile's wall-thickness band. A fresh "
                "tolerance chosen while looking at P7757 would be a P7757 "
                "rule wearing a general name"),
            "no_width_band": (
                "there is deliberately NO table of plausible door widths. "
                "Width is measured three ways and compared; no class is "
                "inferred from it"),
            "grades": (
                "D closes nothing. C may close a polygon but never asserts "
                "two rooms. B and A may do both, and only for doors"),
        },
    }


def classifier_hash() -> str:
    parts = [CLASSIFIER, "|".join(CLASSES),
             "|".join(f"{k}={v}" for k, v in sorted(GRADE_RANK.items())),
             str(MIN_GAP_MM), str(COLLINEAR_TOL_MM), str(JAMB_REACH_MM),
             str(MIN_WALL_MM), str(MAX_WALL_MM),
             MAY_CLOSE_BOUNDARY_FROM, MAY_PARTITION_FROM]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------- wall interruptions

def _face_runs(candidates) -> dict:
    """Merge every wall-like band onto its own line. Returns line -> runs."""
    lines: dict = defaultdict(list)
    for c in candidates:
        lo, hi = sorted((c.start_mm, c.end_mm))
        key = (c.axis, round(c.fixed_mm / COLLINEAR_TOL_MM))
        lines[key].append((lo, hi, c.object_id, c.fixed_mm))
    out = {}
    for key, runs in lines.items():
        runs.sort()
        merged = []
        for lo, hi, oid, fixed in runs:
            if merged and lo - merged[-1][1] <= MIN_GAP_MM:
                prev = merged[-1]
                merged[-1] = (prev[0], max(prev[1], hi),
                              prev[2], prev[3] + [oid], prev[4])
            else:
                merged.append((lo, hi, oid, [oid], fixed))
        out[key] = merged
    return out


def _interruptions(candidates, *, region_id: str) -> list:
    """Every stretch of a wall face with nothing drawn on it, BETWEEN runs.

    A gap at the END of a run is not an interruption — it is a wall that
    stops, and calling it an opening would be exactly the bridging this
    round forbids.
    """
    out = []
    for (axis, _k), merged in sorted(_face_runs(candidates).items()):
        for a, b in zip(merged, merged[1:]):
            gap_lo, gap_hi = a[1], b[0]
            if gap_hi - gap_lo <= MIN_GAP_MM:
                continue
            out.append(Interruption(
                interruption_id=f"INT-{region_id}-{axis}-"
                                f"{round(a[4], 1)}-{round(gap_lo, 1)}",
                axis=axis, fixed_mm=a[4], start_mm=gap_lo, end_mm=gap_hi,
                left_band=a[2], right_band=b[2]))
    return out


def _covered(merged_runs, lo: float, hi: float) -> bool:
    """Does some merged run cover this whole interval?"""
    return any(r[0] <= lo + MIN_GAP_MM and r[1] >= hi - MIN_GAP_MM
               for r in merged_runs)


# ------------------------------------------------------------ door evidence

def _segments_near(primitives, axis, fixed, lo, hi, faces):
    """Segments in the neighbourhood of one interruption."""
    pad = max(JAMB_REACH_MM, abs(hi - lo))
    out = []
    for p in primitives:
        if p.kind != "SEGMENT":
            continue
        xs, ys = sorted((p.x1, p.x2)), sorted((p.y1, p.y2))
        if axis == "H":
            u0, u1, v0, v1 = xs[0], xs[1], ys[0], ys[1]
        else:
            u0, u1, v0, v1 = ys[0], ys[1], xs[0], xs[1]
        if u1 < lo - pad or u0 > hi + pad:
            continue
        lof = min(faces) if faces else fixed
        hif = max(faces) if faces else fixed
        if v1 < lof - pad or v0 > hif + pad:
            continue
        out.append((p, u0, u1, v0, v1))
    return out


def _jambs(near, axis, lo, hi, faces):
    """Perpendicular marks closing the reveal at an end of the opening."""
    found = {}
    lof, hif = (min(faces), max(faces)) if faces else (None, None)
    for p, u0, u1, v0, v1 in near:
        if p.axis == "SKEW" or p.axis == axis:
            continue          # a jamb crosses the wall, it does not run along
        if u1 - u0 > JAMB_REACH_MM:
            continue          # it sits at one station along the wall
        for end in (lo, hi):
            if abs(u0 - end) > JAMB_REACH_MM:
                continue
            if lof is not None and (v0 > lof + JAMB_REACH_MM
                                    or v1 < hif - JAMB_REACH_MM):
                continue      # it must span the wall, not graze it
            if lof is not None and (v0 < lof - JAMB_REACH_MM
                                    or v1 > hif + JAMB_REACH_MM):
                # A reveal stops at the wall faces. A line that starts at
                # a jamb and carries on past them is going somewhere: that
                # is a door leaf, and reading it as a reveal would take the
                # strongest evidence on the drawing and file it as the
                # weakest.
                continue
            found[round(end, 3)] = p.object_id
    return found


def _window_lines(near, axis, lo, hi, faces):
    """Lines parallel to the wall that span the whole interruption."""
    if not faces:
        return []
    lof, hif = min(faces), max(faces)
    out = []
    for p, u0, u1, v0, v1 in near:
        if p.axis != axis:
            continue
        if u0 > lo + JAMB_REACH_MM or u1 < hi - JAMB_REACH_MM:
            continue
        if v0 < lof - JAMB_REACH_MM or v1 > hif + JAMB_REACH_MM:
            continue
        if any(abs(v0 - f) <= COLLINEAR_TOL_MM for f in faces):
            # The wall's OWN face is not glazing. Without this the outer
            # face of a wall whose inner face is merely broken reads as a
            # window pane, and a drafting break becomes an opening.
            continue
        out.append(p.object_id)
    return out


def _footprint(axis, lo, hi, faces, wall_mm):
    """The opening's own box, grown by the thickness of its own wall.

    A door's hinge does not sit ON the wall face: it sits inside the frame,
    a little way in. How far in is a property of the drawing, not a number
    this engine may choose — so the allowance is the WALL'S OWN THICKNESS,
    measured here, and the test is whether the symbol sits IN the opening
    rather than exactly at its corner.

    An earlier version demanded coincidence with a jamb point and missed
    almost every door on a real drawing by tens of millimetres.
    """
    t = max(wall_mm, JAMB_REACH_MM)
    f0, f1 = (min(faces), max(faces)) if faces else (0.0, 0.0)

    def inside(x, y) -> bool:
        u, v = (x, y) if axis == "H" else (y, x)
        return (lo - t <= u <= hi + t) and (f0 - t <= v <= f1 + t)

    return inside


def _inset_mm(x, y, axis, lo, hi) -> float:
    """How far along the wall this hinge sits from its nearest jamb."""
    u = x if axis == "H" else y
    return min(abs(u - lo), abs(u - hi))


def _spans(items, width_mm: float) -> bool:
    """Does the door geometry account for the whole opening?

    `items` are (length, inset) pairs — a leaf or a swing radius, and how
    far its hinge sits inside the reveal. A single leaf spans when the leaf
    plus the frame either side equals the opening; a pair spans when both
    leaves and the frames do. A 900 mm leaf beside a 9.45 m hole accounts
    for 900 mm of it, and on P7757 that pairing graded a 9.45 m gap as a
    door and released a "room" whose entire boundary was opening.

    Every quantity here is measured on this drawing. There is no idea of
    how wide a door ought to be.
    """
    for length, inset in items:
        if abs(length + 2 * inset - width_mm) <= JAMB_REACH_MM:
            return True
    if len(items) > 1:
        total = sum(length for length, _ in items)
        inset = min(i for _, i in items)
        if abs(total + 2 * inset - width_mm) <= JAMB_REACH_MM:
            return True
    return False


def _arcs_at(primitives, inside, width_mm: float) -> list:
    """Swing arcs centred on a jamb of THIS opening — and no other arc.

    An arc whose centre is not at a jamb is not this door's swing, which
    is what keeps an annotation arc, or a swing drawn away from any wall,
    from grading a portal it has nothing to do with.

    The radius must also CORRESPOND: a swing is the leaf sweeping its own
    opening, so its radius cannot exceed the opening it is offered to. That
    is a comparison between two MEASURED quantities on this drawing, not a
    band of plausible door sizes — there is no such band anywhere in this
    module, and this rule contains no absolute number.
    """
    out = []
    for p in primitives:
        if p.kind != "ARC":
            continue
        if p.radius > width_mm + JAMB_REACH_MM:
            continue
        if inside(p.cx, p.cy):
            out.append(p)
    return out


def _leaves(near, inside, jamb_ids, axis, faces, width_mm):
    """A line LEAVING a jamb — the door leaf, drawn open.

    A reveal also starts at a jamb, so a leaf is distinguished by going
    somewhere: it must reach outside the wall band. Without that test every
    archway's own reveal would read as a door leaf and grade itself up.
    """
    lof = min(faces) if faces else None
    hif = max(faces) if faces else None
    out = []
    for p, *_rest in near:
        if p.object_id in jamb_ids or p.length_mm <= JAMB_REACH_MM:
            continue
        if p.length_mm > width_mm + JAMB_REACH_MM:
            # A leaf is the door panel: it fills its own opening and does
            # not exceed it. Without this, a 10.23 m wall line that happens
            # to end near a jamb was read as the leaf of a 150 mm gap, and
            # one line graded doors all over the drawing. Again a
            # correspondence between two measured quantities, with no
            # absolute size in it.
            continue
        if not (inside(p.x1, p.y1) or inside(p.x2, p.y2)):
            continue
        if lof is not None:
            ends = ((p.y1, p.y2) if axis == "H" else (p.x1, p.x2))
            if not any(v < lof - JAMB_REACH_MM or v > hif + JAMB_REACH_MM
                       for v in ends):
                continue      # it stays inside the wall: a reveal, not a leaf
        out.append(p)
    return out


def _name_width(names) -> tuple:
    """The digits in a block name, read BOTH ways and asserted neither."""
    import re

    for n in names:
        runs = re.findall(r"\d+", n)
        if runs:
            raw = max(runs, key=len)
            v = float(raw)
            return raw, v, v * 10.0
    return "", None, None


def _dimension_width(dimensions, axis, lo, hi, fixed):
    """An authored dimension bracketing this interruption."""
    best, gap = None, None
    for d in dimensions:
        if axis == "H":
            if abs(d.y1 - d.y2) > COLLINEAR_TOL_MM:
                continue
            dlo, dhi = sorted((d.x1, d.x2))
            off = abs(d.y1 - fixed)
        else:
            if abs(d.x1 - d.x2) > COLLINEAR_TOL_MM:
                continue
            dlo, dhi = sorted((d.y1, d.y2))
            off = abs(d.x1 - fixed)
        if abs(dlo - lo) > JAMB_REACH_MM or abs(dhi - hi) > JAMB_REACH_MM:
            continue
        if best is None or off < gap:
            best, gap = d, off
    return best


# --------------------------------------------------------------- the driver

def apply_band_roles(report, band_roles) -> OpeningReport:
    """Re-read every opening's host AFTER the authority has spoken.

    The authority needs the openings before it can run — a plot wall with
    a gate in it does not close, and an outer ring that does not close is
    not recognised as one, which is how a site boundary went missing. So
    the classifier runs first, its closures let the authority see the ring,
    and this puts the authority's verdict back onto the openings.

    Nothing is reclassified and no grade moves. Only the question "may this
    opening's host close a room at all" is answered, and answering it NO
    is what keeps a gate out of a room's boundary.
    """
    roles = dict(band_roles or {})
    out = []
    for o in report.openings:
        status, why = "HOST_ESTABLISHED", o.why
        for band in o.host_bands:
            if band in roles and ROOM_BOUNDARY_ELIGIBLE not in roles[band]:
                status = "HOST_IS_NOT_A_ROOM_BOUNDARY"
                why = o.why + (". Its host band may not close a room, so "
                               "neither may this opening — a gate in a plot "
                               "wall is not an internal room separator")
                break
        out.append(Opening(**{**o.__dict__, "host_status": status,
                             "why": why}))
    report.openings = out
    return report


def classify(candidates, *, primitives=(), instances=(), dimensions=(),
             region_id: str = "DR-001", band_roles=None) -> OpeningReport:
    """Every opening hypothesis in ONE drawing region, with its grade.

    `candidates` are the wall-like bands of this region and NOTHING else —
    §1 is enforced by the caller handing a region's own geometry in.
    """
    rep = OpeningReport()
    runs = _face_runs(candidates)
    ints = _interruptions(candidates, region_id=region_id)
    rep.interruptions = ints
    prims = list(primitives)
    roles = dict(band_roles or {})

    # Which INSERT placed each primitive, so a door assembly can be seen as
    # ONE object rather than a pile of arcs. The adapter has already
    # resolved translation, rotation, scale and nesting.
    block_of = {p.object_id: (p.provenance.block_path[-1]
                              if p.provenance.block_path else "")
                for p in prims}
    lineage_of = {p.object_id: p.provenance.instance_path for p in prims}

    used_symbols = set()
    # A pierced wall is interrupted on BOTH faces, so the same opening is
    # reached twice — once from each face. It is ONE opening.
    emitted = set()

    for n, iv in enumerate(sorted(ints, key=lambda i: (i.axis, i.fixed_mm,
                                                       i.start_mm)), 1):
        oid = f"OPN-{region_id}-{n:04d}"
        lo, hi = iv.start_mm, iv.end_mm

        # --- is the wall pierced, or is this one face only? -------------
        #
        # ONE opposite face, not every parallel line in the band. A first
        # version accepted them all, so a wall near two others collected
        # three "faces", the opening's extent spread across the lot, and
        # the same door symbol ended up claimed by several openings — which
        # the matcher then, correctly by its own rules, called ambiguous.
        # On P7757 that made 638 of 841 hosts ambiguous and closed almost
        # nothing. The opposite face of a wall is the BEST match, singular.
        best_partner, best_overlap = None, 0.0
        best_cover, best_cover_sep = None, None
        for (axis2, _k), merged in runs.items():
            if axis2 != iv.axis:
                continue
            f2 = merged[0][4]
            sep = abs(f2 - iv.fixed_mm)
            if sep < MIN_WALL_MM or sep > MAX_WALL_MM:
                continue
            if _covered(merged, lo, hi):
                if best_cover_sep is None or sep < best_cover_sep:
                    best_cover, best_cover_sep = f2, sep
                continue
            for other in ints:
                if other.axis != iv.axis or other is iv:
                    continue
                if abs(other.fixed_mm - f2) > COLLINEAR_TOL_MM:
                    continue
                ov = min(hi, other.end_mm) - max(lo, other.start_mm)
                if ov > best_overlap:
                    best_partner, best_overlap = other, ov

        faces, opposite_continuous = [iv.fixed_mm], False
        partner = best_partner
        if partner is not None:
            faces.append(partner.fixed_mm)
        elif best_cover is not None:
            opposite_continuous = True
            faces.append(best_cover)

        if partner is not None:
            lo = max(lo, partner.start_mm)
            hi = min(hi, partner.end_mm)
            f_lo, f_hi = min(faces), max(faces)
            # The same pierced wall is reached once from each of its faces,
            # and on a real drawing a third parallel line in the band can
            # make the two arrivals disagree about which face is opposite.
            # Anything overlapping this one in BOTH directions is this same
            # opening seen again.
            if any(a == iv.axis
                   and min(hi, b_hi) - max(lo, b_lo) > 0
                   and min(f_hi, g_hi) - max(f_lo, g_lo) > 0
                   for a, b_lo, b_hi, g_lo, g_hi in emitted):
                continue
            emitted.add((iv.axis, lo, hi, f_lo, f_hi))

        host_bands = tuple(sorted({iv.left_band, iv.right_band}
                                  | ({partner.left_band, partner.right_band}
                                     if partner else set())))

        # --- gather the evidence ---------------------------------------
        ev = [E_FACE_INTERRUPTION]
        if partner is not None:
            ev.append(E_THROUGH_INTERRUPTION)
        if opposite_continuous and partner is None:
            ev.append(E_OPPOSITE_FACE_CONTINUOUS)

        near = _segments_near(prims, iv.axis, iv.fixed_mm, lo, hi, faces)
        jambs = _jambs(near, iv.axis, lo, hi, faces)
        if jambs:
            ev.append(E_JAMB)
        if len(jambs) >= 2:
            ev.append(E_JAMBS_BOTH_ENDS)

        mid_face = sum(faces) / len(faces)
        width_mm = abs(hi - lo)
        wall_here = (max(faces) - min(faces)) if len(faces) > 1 else 0.0
        inside = _footprint(iv.axis, lo, hi, faces, wall_here)
        arcs = _arcs_at(prims, inside, width_mm)
        leaves = _leaves(near, inside, set(jambs.values()), iv.axis,
                         faces, width_mm)
        windows = _window_lines(near, iv.axis, lo, hi, faces)

        # DOES THE DOOR GEOMETRY EXPLAIN THIS OPENING?
        #
        # A leaf fills the opening it swings in, and a pair of leaves fills
        # it between them. A 900 mm leaf beside a 9.45 m hole explains 900
        # mm of it and nothing else — and on P7757 that is exactly what
        # happened: one such pairing graded a 9.45 m gap GRADE_B and
        # released a "room" whose entire boundary was opening. This
        # compares two measured lengths on this drawing and contains no
        # idea of how wide a door ought to be.
        leaf_items = [
            (p.length_mm,
             _inset_mm(p.x1 if inside(p.x1, p.y1) else p.x2,
                       p.y1 if inside(p.x1, p.y1) else p.y2,
                       iv.axis, lo, hi))
            for p in leaves]
        arc_items = [(p.radius, _inset_mm(p.cx, p.cy, iv.axis, lo, hi))
                     for p in arcs]
        door_spans = (_spans(leaf_items, width_mm)
                      or _spans(arc_items, width_mm))

        symbol_ids, names = [], []
        if arcs:
            ev.append(E_SWING_ARC)
            symbol_ids += [p.object_id for p in arcs]
        if leaves:
            ev.append(E_DOOR_LEAF)
            symbol_ids += [p.object_id for p in leaves]
        if windows:
            ev.append(E_WINDOW_LINES)
            symbol_ids += list(windows)
        if arcs or leaves:
            ev.append(E_SYMBOL_SPANS_THE_OPENING if door_spans
                      else E_SYMBOL_DOES_NOT_SPAN)
        used_symbols.update(symbol_ids)

        # ONE transformed INSERT supplying the door geometry is the
        # strongest CAD evidence there is — and it is the geometry that
        # counts, not the name it was filed under.
        assembly = ""
        door_syms = [p.object_id for p in arcs] + [p.object_id for p in leaves]
        lineages = {lineage_of.get(s, ()) for s in door_syms}
        if door_syms and len(lineages) == 1 and next(iter(lineages)):
            assembly = block_of.get(door_syms[0], "")
            ev.append(E_BLOCK_ASSEMBLY)
        names = sorted({block_of[s] for s in symbol_ids
                        if block_of.get(s)})
        if assembly:
            ev.append(E_BLOCK_NAME)

        dim = _dimension_width(dimensions, iv.axis, lo, hi, iv.fixed_mm)
        if dim is not None:
            ev.append(E_AUTHORED_DIMENSION)

        raw, as_mm, as_cm = _name_width(names)
        widths = WidthObservations(
            geometric_mm=abs(hi - lo),
            block_name_raw=raw, block_name_as_mm=as_mm,
            block_name_as_cm_in_mm=as_cm,
            dimension_display=(None if dim is None else dim.display_value),
            dimension_normalized_mm=(None if dim is None
                                     else dim.normalized_mm))

        # --- class, from the evidence and never from the width ----------
        #
        # TWO different kinds of support, because they answer different
        # questions. THROUGH says the wall is pierced rather than one line
        # being broken. REVEALS say somebody drew an opening here rather
        # than leaving a hole.
        #
        # A door may rest on THROUGH alone: plenty of architects draw the
        # leaf and the swing and no reveal at all. A DOORLESS opening may
        # not — with no door symbol and no reveal, what is on the paper is
        # a gap, and a gap alone closes nothing.
        through = partner is not None
        reveals = len(jambs) >= 2
        supported = through or reveals
        wall_mm = wall_here
        if (wall_mm and abs(hi - lo) < wall_mm
                and not (arcs or leaves or windows)):
            klass, grade = NON_OPENING_GEOMETRY, GRADE_NONE
            why = (f"the gap is {abs(hi - lo):.0f} mm and the wall it "
                   f"pierces is {wall_mm:.0f} mm thick. Nothing passes "
                   "through an opening narrower than the wall around it: "
                   "this is a break in a drawn line, and it is NOT bridged")
        elif opposite_continuous and partner is None and not (arcs or leaves
                                                              or windows):
            klass, grade = NON_OPENING_GEOMETRY, GRADE_NONE
            why = ("the other face of this wall runs continuously across "
                   "the gap, so material still stands here. A break in one "
                   "drawn line is not an opening")
        elif windows and not (arcs or leaves) and supported:
            klass = WINDOW_OPENING
            grade = GRADE_C
            why = ("lines parallel to the wall span the interruption. A "
                   "window interrupts material and keeps the room "
                   "boundary; it is not a passage between rooms")
        elif leaves and supported and door_spans:
            klass = DOOR_WITH_LEAF
            grade = GRADE_A if assembly and len(jambs) >= 1 else GRADE_B
            why = ("a door leaf is drawn from a jamb of a supported wall "
                   "interruption" + (", and one transformed INSERT supplies "
                                     "the whole assembly" if assembly
                                     else ""))
        elif arcs and supported and door_spans:
            klass = DOOR_PORTAL
            grade = GRADE_A if assembly and len(jambs) >= 1 else GRADE_B
            why = ("a swing arc is centred on a jamb of a supported wall "
                   "interruption" + (", from one transformed INSERT"
                                     if assembly else ""))
        elif (arcs or leaves) and not door_spans:
            klass, grade = (DOORLESS_ARCHWAY, GRADE_C) if reveals else \
                (UNRESOLVED_WALL_GAP, GRADE_D)
            why = ("door geometry sits near this opening but does not span "
                   f"it: the hole is {width_mm:.0f} mm and the leaves and "
                   "swings drawn in it do not add up to that. It is not "
                   "explained, so it is not graded as a door")
        elif (arcs or leaves or windows) and not supported:
            klass, grade = UNKNOWN, GRADE_D
            why = ("opening geometry sits here, but the wall is interrupted "
                   "on one face only and no reveal is drawn. The symbol is "
                   "not enough on its own")
        elif reveals:
            klass, grade = DOORLESS_ARCHWAY, GRADE_C
            why = ("the wall is pierced and its reveals are drawn, but "
                   "nothing says door. This may close a polygon; it may "
                   "NOT assert that the two sides are separate rooms")
        else:
            klass, grade = UNRESOLVED_WALL_GAP, GRADE_D
            why = ("a gap between two collinear wall runs, with no reveal "
                   "and no symbol — not even when both faces stop at the "
                   "same place. WALL GAP ALONE CANNOT CREATE A "
                   "ROOM-PARTITION PORTAL, so this closes nothing")

        # §9 and the site gate: an opening in a boundary that may not close
        # a room cannot become a room's portal either.
        host_status = "HOST_ESTABLISHED"
        for band in host_bands:
            if band in roles and ROOM_BOUNDARY_ELIGIBLE not in roles[band]:
                host_status = "HOST_IS_NOT_A_ROOM_BOUNDARY"
                why += (". Its host band may not close a room, so neither "
                        "may this opening — a gate in a plot wall is not an "
                        "internal room separator")
                break

        rep.openings.append(Opening(
            opening_id=oid, region_id=region_id, opening_class=klass,
            grade=grade, axis=iv.axis, fixed_mm=mid_face,
            start_mm=lo, end_mm=hi, host_bands=host_bands,
            wall_faces_mm=tuple(sorted(faces)), widths=widths,
            evidence=tuple(ev), symbol_ids=tuple(sorted(set(symbol_ids))),
            block_names=tuple(names),
            leaf_length_mm=(max(p.length_mm for p in leaves)
                            if leaves else None),
            swing_radius_mm=(max(p.radius for p in arcs) if arcs else None),
            why=why, host_status=host_status))

    # Door geometry that matched no wall interruption at all. Case S (a
    # swing drawn away from any wall) and case T (an annotation arc) live
    # here, and neither of them grades anything.
    for p in prims:
        if p.kind == "ARC" and p.object_id not in used_symbols:
            rep.unmatched_symbols.append({
                "provenance": p.object_id,
                "kind": "ARC",
                "block": block_of.get(p.object_id, ""),
                "radius_mm": round(p.radius, 1),
                "verdict": "NOT_AN_OPENING",
                "why": ("no wall interruption has a jamb at this arc's "
                        "centre. An arc that is not at a doorway is not a "
                        "door, whatever it is drawn to look like")})

    rep.notes["what_this_stage_refuses"] = (
        "to bridge a gap. A hypothesis is produced for every interruption "
        "and the GRADE decides what it may do. Grade D — a gap and nothing "
        "else — closes nothing at all")
    rep.notes["names"] = (
        "block names appear as observations and in the width cross-check. "
        "No name promotes a grade and no name creates a portal")
    return rep
