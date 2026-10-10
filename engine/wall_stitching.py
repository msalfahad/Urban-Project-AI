"""E43 — joining wall fragments on evidence, never on proximity.

The rule this module exists to avoid is:

    gap < X mm  ->  connect

That rule would close doorways, which is the one thing the whole topology
effort is trying to find. So a stitch is a hypothesis with named evidence and a
status, in the same shape as every other decision in this engine: two
independent families before anything is called validated, and an honest
UNRESOLVED when the drawing does not say.

EVIDENCE FAMILIES. Counting five correlated observations of one vector
construction as five proofs is the error the opening spike made. The families
are kept apart so that cannot happen again:

    IDENTITY   the two fragments came from the same wall pair or source path
    GEOMETRY   axis, collinearity, separation compatibility, gap size
    CLOSURE    an end cap names both faces of the wall at this point
    CONTEXT    a junction at one end explains why the run stops there

    DO NOT PROMOTE A PROXY INTO PHYSICAL TRUTH.

    a small gap                   is not   "one wall"
    the same pair id              is not   "physically continuous"
    an end cap near a gap         is not   "the wall stops here"
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

STITCH_VALIDATED = "STITCH_VALIDATED"
STITCH_PROBABLE = "STITCH_PROBABLE"
STITCH_AMBIGUOUS = "STITCH_AMBIGUOUS"
STITCH_REJECTED = "STITCH_REJECTED"

FAMILY_IDENTITY = "IDENTITY"
FAMILY_GEOMETRY = "GEOMETRY"
FAMILY_CLOSURE = "CLOSURE"
FAMILY_CONTEXT = "CONTEXT"

# Two INDEPENDENT families before a stitch is validated. Two observations from
# one family are one observation seen twice.
MIN_FAMILIES_FOR_VALIDATED = 2

# Evidence, with the family each belongs to. A signal that agrees with almost
# every candidate carries no information, so each is stated as a test that can
# fail.
E_SAME_PAIR = "SAME_WALL_PAIR_IDENTITY"
E_SAME_PATH = "SAME_SOURCE_PATH"
E_COLLINEAR = "COLLINEAR_WITHIN_TOLERANCE"
E_SAME_AXIS = "SAME_AXIS"
E_SEPARATION_MATCH = "COMPATIBLE_FACE_SEPARATION"
E_SMALL_GAP = "GAP_BELOW_OPENING_SIZE"
E_END_CAP = "END_CAP_CLOSES_THIS_WALL"
E_JUNCTION_AT_END = "JUNCTION_EXPLAINS_THE_BREAK"

EVIDENCE_FAMILY = {
    E_SAME_PAIR: FAMILY_IDENTITY,
    E_SAME_PATH: FAMILY_IDENTITY,
    E_COLLINEAR: FAMILY_GEOMETRY,
    E_SAME_AXIS: FAMILY_GEOMETRY,
    E_SEPARATION_MATCH: FAMILY_GEOMETRY,
    E_SMALL_GAP: FAMILY_GEOMETRY,
    E_END_CAP: FAMILY_CLOSURE,
    E_JUNCTION_AT_END: FAMILY_CONTEXT,
}

# A gap at least this wide is door-sized and must never be stitched shut on
# geometry alone: closing it would erase the opening the engine is looking for.
DOOR_WIDTH_MM = 700.0
# Collinearity for two faces of the same wall run.
COLLINEAR_TOL_MM = 20.0
# Two separations this close are the same wall thickness drawn twice.
SEPARATION_TOL_MM = 20.0


class StitchError(RuntimeError):
    """A stitch was proposed that the evidence cannot carry."""


@dataclass(frozen=True)
class StitchCandidate:
    """Two fragments that might be one wall, and everything for and against."""

    stitch_id: str
    edge_a: str
    edge_b: str
    axis: str
    gap_mm: float
    centreline_difference_mm: float
    separation_difference_mm: float
    evidence: tuple[str, ...]
    status: str
    why: str

    @property
    def families(self) -> set[str]:
        return {EVIDENCE_FAMILY[e] for e in self.evidence}

    def record(self) -> dict:
        return {"stitch_id": self.stitch_id, "edge_a": self.edge_a,
                "edge_b": self.edge_b, "axis": self.axis,
                "gap_mm": round(self.gap_mm, 1),
                "centreline_difference_mm": round(
                    self.centreline_difference_mm, 1),
                "separation_difference_mm": round(
                    self.separation_difference_mm, 1),
                "evidence": list(self.evidence),
                "families": sorted(self.families), "status": self.status,
                "why": self.why}


def _end_cap_between(caps, axis: str, centreline_mm: float,
                     lo: float, hi: float, *, tol_mm: float = 80.0) -> bool:
    """Is there a wall end cap inside this gap?

    A cap across the gap says the wall STOPS here — which is evidence against
    stitching, and it is used that way. This module never reads a cap as
    permission to join.
    """
    for c in caps:
        if c.axis == axis:
            continue
        at = c.at_mm
        if not (lo - tol_mm <= at <= hi + tol_mm):
            continue
        span_lo, span_hi = min(c.span_mm), max(c.span_mm)
        if span_lo - tol_mm <= centreline_mm <= span_hi + tol_mm:
            return True
    return False


def candidates(edges, *, caps=(), junction_nodes=(), max_gap_mm: float = 2000.0
               ) -> list[StitchCandidate]:
    """Every pair of collinear fragments that could be one wall, judged.

    Judged, not joined. `stitch()` applies only the validated ones, and even
    then it records what it did.
    """
    caps = list(caps)
    junc = {(round(n.x_mm), round(n.y_mm)) for n in junction_nodes}
    by_axis: dict[str, list] = {}
    for e in edges:
        by_axis.setdefault(e.axis, []).append(e)

    out: list[StitchCandidate] = []
    n = 0
    for axis, group in by_axis.items():
        group = sorted(group, key=lambda e: (e.centreline_mm,
                                             min(e.start_mm, e.end_mm)))
        for i, a in enumerate(group):
            a_lo, a_hi = min(a.start_mm, a.end_mm), max(a.start_mm, a.end_mm)
            for b in group[i + 1:]:
                dc = abs(b.centreline_mm - a.centreline_mm)
                if dc > COLLINEAR_TOL_MM:
                    continue
                b_lo, b_hi = min(b.start_mm, b.end_mm), max(b.start_mm, b.end_mm)
                gap = max(b_lo - a_hi, a_lo - b_hi)
                if gap > max_gap_mm:
                    continue
                if gap < 0:
                    gap = 0.0
                dsep = abs(a.wall_face_separation_mm - b.wall_face_separation_mm)

                ev = [E_SAME_AXIS, E_COLLINEAR]
                if a.pair_id == b.pair_id:
                    ev.append(E_SAME_PAIR)
                if dsep <= SEPARATION_TOL_MM:
                    ev.append(E_SEPARATION_MATCH)
                if gap < DOOR_WIDTH_MM:
                    ev.append(E_SMALL_GAP)

                lo, hi = min(a_hi, b_hi), max(a_lo, b_lo)
                capped = _end_cap_between(caps, axis, a.centreline_mm, lo, hi)
                if capped:
                    ev.append(E_END_CAP)

                x = (lo + hi) / 2
                pt = ((round(x), round(a.centreline_mm)) if axis == "H"
                      else (round(a.centreline_mm), round(x)))
                if pt in junc:
                    ev.append(E_JUNCTION_AT_END)

                n += 1
                fam = {EVIDENCE_FAMILY[e] for e in ev}

                if capped:
                    status = STITCH_REJECTED
                    why = ("an end cap closes the wall inside this gap: the "
                           "drawing says the wall STOPS here, so joining "
                           "across it would erase a real wall end")
                elif dsep > SEPARATION_TOL_MM:
                    status = STITCH_REJECTED
                    why = (f"the two runs have different wall separations "
                           f"({dsep:.0f} mm apart): different walls, not one "
                           "wall in two pieces")
                elif gap >= DOOR_WIDTH_MM:
                    status = STITCH_AMBIGUOUS
                    why = (f"the gap is {gap:.0f} mm, door-sized or larger. "
                           "Stitching it shut would erase exactly the opening "
                           "this engine exists to find")
                elif len(fam) >= MIN_FAMILIES_FOR_VALIDATED and (
                        E_SAME_PAIR in ev or gap <= 60.0):
                    status = STITCH_VALIDATED
                    why = ("two independent evidence families agree and the "
                           "gap is smaller than any opening: one wall drawn "
                           "in pieces")
                elif len(fam) >= MIN_FAMILIES_FOR_VALIDATED:
                    status = STITCH_PROBABLE
                    why = ("the evidence agrees but the gap is larger than a "
                           "drafting break, so this is a hypothesis")
                else:
                    status = STITCH_AMBIGUOUS
                    why = ("only one evidence family supports this; correlated "
                           "observations of one construction are not proof")

                out.append(StitchCandidate(
                    stitch_id=f"ST-{n:05d}", edge_a=a.edge_id, edge_b=b.edge_id,
                    axis=axis, gap_mm=gap, centreline_difference_mm=dc,
                    separation_difference_mm=dsep, evidence=tuple(sorted(ev)),
                    status=status, why=why))
    return out


def summary(cands: list[StitchCandidate]) -> dict:
    by_status = Counter(c.status for c in cands)
    return {
        "candidates": len(cands),
        **{s: by_status.get(s, 0) for s in (
            STITCH_VALIDATED, STITCH_PROBABLE, STITCH_AMBIGUOUS,
            STITCH_REJECTED)},
        "validated_length_recovered_mm": round(
            sum(c.gap_mm for c in cands if c.status == STITCH_VALIDATED), 1),
        "rejected_by_end_cap": sum(
            1 for c in cands if c.status == STITCH_REJECTED
            and E_END_CAP in c.evidence),
        "ambiguous_because_door_sized": sum(
            1 for c in cands if c.status == STITCH_AMBIGUOUS
            and c.gap_mm >= DOOR_WIDTH_MM),
        "evidence_histogram": dict(Counter(
            e for c in cands for e in c.evidence)),
    }
