"""Topology recovery — is this one polygon actually two rooms?

The correction that produced this module: a gap with the SAME region on both
sides was reported as a phantom, and that was wrong. We already know this
segmentation merges real spaces — the washroom is absorbed into a neighbour and
BED-04 still contains an unseparated 1600 x 3000 bathroom. A gap whose two sides
land in one region is precisely what an opening inside an under-segmented region
looks like. Rejecting that class threw away the recovery signal for both known
defects.

So a gap is classified, never discarded:

  INTERIOR_OPENING           two different mapped spaces either side
  INTRA_REGION_TOPOLOGY      the same region both sides — a possible split
  EXTERIOR_OPENING           outside on one side (needs the envelope classifier)
  UNMAPPED_SPACE             a region that is not a mapped space
  DRAWING_NOISE              provably not on one wall system
  UNRESOLVED                 not enough evidence to say

And topology recovery comes BEFORE opening measurement, because if the room
polygons are wrong then perfect door measurement afterwards cannot fix the
takeoff.

A dashed run is treated the same way. A dashed line on a plan may be a
threshold, a shower kerb, an opening, a change of finish, a bulkhead or a
reference line. What matters first is whether it CAN close or split a region;
what kind of boundary it is comes later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

# Gap / boundary classes. None of these is a rejection.
INTERIOR_OPENING = "INTERIOR_OPENING_CANDIDATE"
INTRA_REGION = "INTRA_REGION_TOPOLOGY_CANDIDATE"
EXTERIOR_OPENING = "EXTERIOR_OPENING_CANDIDATE"
UNMAPPED_SPACE = "UNMAPPED_SPACE_CANDIDATE"
DRAWING_NOISE = "DRAWING_NOISE"
UNRESOLVED = "UNRESOLVED"

# What a recovered boundary might be. Deliberately decided later than detection.
TOPOLOGY_BOUNDARY = "TOPOLOGY_BOUNDARY_CANDIDATE"
DOOR_OPENING = "DOOR_OPENING"
OPEN_TRANSITION = "OPEN_TRANSITION"
THRESHOLD = "THRESHOLD"
NON_PHYSICAL_BOUNDARY = "NON_PHYSICAL_BOUNDARY"
OTHER = "OTHER"

VALIDATED = "VALIDATED"
PROBABLE = "PROBABLE"
AMBIGUOUS = "AMBIGUOUS"
REJECTED = "REJECTED"

# Why a line was not kept as a wall face. A count of these is the only honest way
# to answer "is 1.5% retention too low?" — loosening a tolerance before knowing
# which one rejected the lines would be tuning in the dark.
NO_PARTNER_IN_RANGE = "NO_PARALLEL_PARTNER_IN_THICKNESS_RANGE"
TOO_THIN = "NEAREST_PARTNER_THINNER_THAN_MIN"
TOO_THICK = "NEAREST_PARTNER_THICKER_THAN_MAX"
INSUFFICIENT_OVERLAP = "INSUFFICIENT_OVERLAP"
NOT_MUTUAL = "NEAREST_PAIRING_NOT_MUTUAL"
KEPT = "KEPT"


class TopologyError(RuntimeError):
    """A topology question could not be answered from the geometry supplied."""


@dataclass(frozen=True)
class WallPair:
    """Two parallel faces proven to be the two sides of one wall.

    Pair identity is the thing the earlier spike lacked. It grouped faces that
    were merely collinear within 12 mm, so two unrelated features on the same
    line produced an invented gap between them. A gap now has to lie along ONE
    pair.
    """

    pair_id: str
    axis: str                      # H or V
    face_a_mm: float               # the two faces' constant coordinates
    face_b_mm: float
    start_mm: float                # the overlap they share
    end_mm: float

    @property
    def thickness_mm(self) -> float:
        return abs(self.face_b_mm - self.face_a_mm)

    @property
    def centreline_mm(self) -> float:
        return (self.face_a_mm + self.face_b_mm) / 2

    @property
    def length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)


def merge_collinear(lines, *, tol_mm: float = 2.0, join_mm: float = 25.0):
    """Join fragments of one drawn line back into the line the architect drew.

    This is input preparation, not a loosened tolerance, and the diagnostic is
    what made it necessary. Of AR-00's 35,355 axis-aligned segments, 28,566 are
    shorter than 100 mm, and 95.6% of all lines were rejected for
    INSUFFICIENT_OVERLAP against a 300 mm minimum. A 40 mm fragment cannot
    overlap anything by 300 mm — but forty such fragments in a row are a wall
    face several metres long, and the pairing test should see the face rather
    than the forty pieces.

    Fragments are joined when they lie on the same line within `tol_mm` and the
    end-to-end gap between them is at most `join_mm`. That gap has to stay small:
    joining across a doorway would erase the very break this module exists to
    find.
    """
    groups: dict[tuple[str, int], list] = {}
    for ori, fixed, a, b in lines:
        groups.setdefault((ori, int(round(fixed / tol_mm))), []).append(
            (min(a, b), max(a, b), fixed))
    out = []
    for (ori, _), runs in groups.items():
        runs.sort()
        cur_a, cur_b, cur_f = runs[0]
        for a, b, f in runs[1:]:
            if a - cur_b <= join_mm:
                cur_b = max(cur_b, b)
            else:
                out.append((ori, cur_f, cur_a, cur_b))
                cur_a, cur_b, cur_f = a, b, f
        out.append((ori, cur_f, cur_a, cur_b))
    return out


def pairing_diagnostic(lines, px_mm: Decimal, *, min_thickness_mm: int = 60,
                       max_thickness_mm: int = 400, min_overlap_mm: int = 300
                       ) -> dict[str, int]:
    """Why each line was or was not kept as a wall face.

    Answers "is 1.5% retention too low?" with a reason rather than a guess. A
    drawing genuinely full of fixture, hatch, dimension and text linework will
    show NO_PARALLEL_PARTNER dominating; a detector that is too strict will show
    INSUFFICIENT_OVERLAP or NOT_MUTUAL dominating instead.
    """
    lo = float(Decimal(min_thickness_mm) / px_mm)
    hi = float(Decimal(max_thickness_mm) / px_mm)
    need = float(Decimal(min_overlap_mm) / px_mm)
    by_ori: dict[str, list] = {"H": [], "V": []}
    for ln in lines:
        by_ori.setdefault(ln[0], []).append(ln)

    counts: dict[str, int] = {k: 0 for k in (
        KEPT, NO_PARTNER_IN_RANGE, TOO_THIN, TOO_THICK, INSUFFICIENT_OVERLAP,
        NOT_MUTUAL)}

    for group in by_ori.values():
        # nearest partner within range, plus the reason when there is none
        best: dict = {}
        for ln in group:
            _, fixed, a, b = ln
            chosen, gap_best, saw_thin, saw_thick, saw_short = None, None, 0, 0, 0
            for cand in group:
                if cand is ln:
                    continue
                _, f2, a2, b2 = cand
                gap = abs(f2 - fixed)
                if gap < lo:
                    saw_thin += 1
                    continue
                if gap > hi:
                    saw_thick += 1
                    continue
                if min(b, b2) - max(a, a2) < need:
                    saw_short += 1
                    continue
                if gap_best is None or gap < gap_best:
                    chosen, gap_best = cand, gap
            best[ln] = (chosen, saw_thin, saw_thick, saw_short)

        for ln, (partner, thin, thick, short) in best.items():
            if partner is None:
                if short:
                    counts[INSUFFICIENT_OVERLAP] += 1
                elif thin:
                    counts[TOO_THIN] += 1
                elif thick:
                    counts[TOO_THICK] += 1
                else:
                    counts[NO_PARTNER_IN_RANGE] += 1
                continue
            back = best.get(partner, (None,))[0]
            if back is not None and abs(back[1] - ln[1]) < 1e-6:
                counts[KEPT] += 1
            else:
                counts[NOT_MUTUAL] += 1
    return counts


def wall_pairs(lines, px_mm: Decimal, *, min_thickness_mm: int = 60,
               max_thickness_mm: int = 400, min_overlap_mm: int = 300
               ) -> list[WallPair]:
    """Mutually-nearest face pairs, with identity kept.

    Same pairing rule as `paired_wall_faces`, which stays as it is for callers
    that only want the faces. The difference is the return value: a pair knows
    both its faces, so a gap can be required to lie along one wall.
    """
    lo = float(Decimal(min_thickness_mm) / px_mm)
    hi = float(Decimal(max_thickness_mm) / px_mm)
    need = float(Decimal(min_overlap_mm) / px_mm)
    by_ori: dict[str, list] = {"H": [], "V": []}
    for ln in lines:
        by_ori.setdefault(ln[0], []).append(ln)

    out: list[WallPair] = []
    n = 0
    for ori, group in by_ori.items():
        near = {}
        for ln in group:
            _, fixed, a, b = ln
            chosen, gap_best = None, None
            for cand in group:
                if cand is ln:
                    continue
                _, f2, a2, b2 = cand
                gap = abs(f2 - fixed)
                if not (lo <= gap <= hi):
                    continue
                if min(b, b2) - max(a, a2) < need:
                    continue
                if gap_best is None or gap < gap_best:
                    chosen, gap_best = cand, gap
            near[ln] = chosen
        seen = set()
        for ln, partner in near.items():
            if partner is None or near.get(partner) is not ln:
                continue
            key = tuple(sorted((id(ln), id(partner))))
            if key in seen:
                continue
            seen.add(key)
            n += 1
            _, f1, a1, b1 = ln
            _, f2, a2, b2 = partner
            out.append(WallPair(f"WP-{n:04d}", ori, f1, f2,
                                max(min(a1, b1), min(a2, b2)),
                                min(max(a1, b1), max(a2, b2))))
    return out


@dataclass
class GapCandidate:
    """A break along ONE wall pair, classified rather than accepted or binned."""

    gap_id: str
    pair_id: str
    axis: str
    centreline_mm: float
    start_mm: float
    end_mm: float
    thickness_mm: float
    gap_class: str = UNRESOLVED
    region_ids: tuple[int, ...] = ()
    space_ids: tuple[str, ...] = ()
    evidence: list[str] = field(default_factory=list)
    note: str = ""

    @property
    def width_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    @property
    def suggests_split(self) -> bool:
        """Would validating this gap split one region into two?"""
        return self.gap_class == INTRA_REGION

    def record(self) -> dict:
        return {"gap_id": self.gap_id, "pair_id": self.pair_id, "axis": self.axis,
                "centreline_mm": round(self.centreline_mm, 1),
                "start_mm": round(self.start_mm, 1), "end_mm": round(self.end_mm, 1),
                "width_mm": round(self.width_mm, 1),
                "wall_thickness_mm": round(self.thickness_mm, 1),
                "gap_class": self.gap_class, "region_ids": list(self.region_ids),
                "space_ids": list(self.space_ids), "evidence": list(self.evidence),
                "suggests_split": self.suggests_split, "note": self.note}


# A gap at the END of a wall run is a corner or a junction, not an opening. On
# AR-00 this is the dominant confound: of 45 INTRA_REGION candidates, 21 were
# wider than 2 m, which is a wall terminating rather than a doorway. Perpendicular
# junction detection is NOT yet implemented, so callers must treat wide
# candidates with suspicion and the width bands below are the only filter.
WALL_TERMINATION_SUSPECT_MM = 1200.0


def gaps_along_pairs(pairs: list[WallPair], face_runs, *,
                     min_gap_mm: float = 500, max_gap_mm: float = 6000,
                     tol_mm: float = 12.0) -> list[GapCandidate]:
    """Breaks in the shared extent of each wall pair.

    `face_runs` maps a face's constant coordinate to the along-axis runs drawn on
    it. A gap qualifies only where BOTH faces of the pair are interrupted at the
    same place: one face stopping while the other continues is a recess, a
    nib or a change of thickness, not an opening.
    """
    out: list[GapCandidate] = []
    n = 0
    for p in pairs:
        runs_a = _merged(face_runs.get(_key(p.axis, p.face_a_mm, tol_mm), []))
        runs_b = _merged(face_runs.get(_key(p.axis, p.face_b_mm, tol_mm), []))
        for ga in _gaps(runs_a, min_gap_mm, max_gap_mm):
            for gb in _gaps(runs_b, min_gap_mm, max_gap_mm):
                lo, hi = max(ga[0], gb[0]), min(ga[1], gb[1])
                if hi - lo < min_gap_mm:
                    continue
                n += 1
                out.append(GapCandidate(
                    f"GC-{n:04d}", p.pair_id, p.axis, p.centreline_mm, lo, hi,
                    p.thickness_mm,
                    evidence=["BOTH_FACES_INTERRUPTED_AT_THE_SAME_PLACE"],
                    note=("" if hi - lo <= WALL_TERMINATION_SUSPECT_MM else
                          f"{hi - lo:.0f} mm is wide for an opening — more likely "
                          "the wall run ending at a corner or junction. "
                          "Perpendicular junction detection is not implemented.")))
    return out


def _key(axis: str, fixed: float, tol_mm: float) -> tuple[str, int]:
    return (axis, int(round(fixed / tol_mm)))


def _merged(runs):
    if not runs:
        return []
    rs = sorted((min(a, b), max(a, b)) for a, b in runs)
    out = [list(rs[0])]
    for a, b in rs[1:]:
        if a <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def _gaps(runs, min_gap: float, max_gap: float):
    return [(r1[1], r2[0]) for r1, r2 in zip(runs, runs[1:])
            if min_gap <= r2[0] - r1[1] <= max_gap]


def classify_gap(gap: GapCandidate, *, region_at, space_of, outside_ids) -> GapCandidate:
    """Put the gap in a class. Nothing is thrown away.

    `region_at(axis, centreline_mm, along_mm, side)` returns a raster region id
    or None; `space_of(region_id)` maps it to a mapped space or None.
    """
    mid = (gap.start_mm + gap.end_mm) / 2
    left = region_at(gap.axis, gap.centreline_mm, mid, -1)
    right = region_at(gap.axis, gap.centreline_mm, mid, +1)
    gap.region_ids = tuple(r for r in (left, right) if r is not None)
    ls, rs = space_of(left), space_of(right)
    gap.space_ids = tuple(s for s in (ls, rs) if s)

    if left is None and right is None:
        gap.gap_class = UNRESOLVED
        gap.note = "neither side resolved to a region"
    elif (left in outside_ids) or (right in outside_ids):
        gap.gap_class = EXTERIOR_OPENING
        gap.note = "one side connects to the sheet border"
    elif ls and rs and ls != rs:
        gap.gap_class = INTERIOR_OPENING
    elif left is not None and left == right:
        if ls:
            gap.gap_class = INTRA_REGION
            gap.note = (f"both sides fall in {ls}: a real opening inside an "
                        "under-segmented region would look exactly like this")
        else:
            gap.gap_class = UNMAPPED_SPACE
            gap.note = f"both sides fall in unmapped region {left}"
    elif not gap.space_ids:
        gap.gap_class = UNMAPPED_SPACE
    else:
        gap.gap_class = UNRESOLVED
        gap.note = "one mapped space and one unresolved side"
    return gap


@dataclass
class SplitCandidate:
    """A proposal that one region is really two, and the evidence for it."""

    topology_candidate_id: str
    parent_region_id: int
    parent_space_id: str
    boundary_axis: str
    boundary_mm: float
    boundary_start_mm: float
    boundary_end_mm: float
    boundary_kind: str = TOPOLOGY_BOUNDARY
    evidence: list[str] = field(default_factory=list)
    proposed_child_areas_m2: tuple = ()
    printed_reference: str = ""
    status: str = AMBIGUOUS
    note: str = ""

    def record(self) -> dict:
        return {"topology_candidate_id": self.topology_candidate_id,
                "parent_region_id": self.parent_region_id,
                "parent_space_id": self.parent_space_id,
                "boundary": {"axis": self.boundary_axis,
                             "at_mm": round(self.boundary_mm, 1),
                             "from_mm": round(self.boundary_start_mm, 1),
                             "to_mm": round(self.boundary_end_mm, 1),
                             "kind": self.boundary_kind},
                "evidence": list(self.evidence),
                "proposed_child_areas_m2": [str(a) for a in self.proposed_child_areas_m2],
                "printed_reference": self.printed_reference,
                "status": self.status, "note": self.note}
