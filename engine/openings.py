"""E34 (spike) — opening candidates from vector geometry, on accumulated evidence.

Raster door-gap bridging failed on this project and the failure is worth keeping:
printed fixtures act as false jambs on raw ink, so bridging either swallowed
small rooms (a bathroom went from 3.95 m² to 0.51 m²) or failed to seal at all on
the sparser vector-only mask. It stays available as diagnostic evidence and is
not the authoritative source.

The vector layer is better raw material, but not because of door swings. A survey
of AR-00 found 2,399 bezier curves of which only ~43 have door-scale chords —
fewer than a villa floor has doors. Swings are decomposed, drawn as polylines, or
simply absent: a sliding door, a pocket door, an open transition and a double door
may have no arc at all. So a swing is supporting evidence and never a condition.

What this module does instead is accumulate independent signals and refuse to let
any one of them decide:

  A  a gap in a run of PAIRED wall faces — the seed, and the reason a fixture
     line cannot start a candidate: a fixture is drawn as a single line
  B  jamb geometry — a short perpendicular segment at each end of the gap
  C  a door leaf line inside the gap
  D  a swing arc whose endpoints sit near the gap
  E  two different mapped spaces on opposite sides of the gap
  F  a gap width inside a plausible band for its type

A candidate needs several of these. One signal — a 900 mm hole in a wall — is not
a door; it is a hole in a wall, and on this drawing some of those holes are
between a room and a duct.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import Decimal

# Candidate confidence. Only VALIDATED may change an automatically released NET
# quantity; PROBABLE goes to A1/A2 or a human; the rest are recorded and ignored.
VALIDATED = "VALIDATED"
PROBABLE = "PROBABLE"
AMBIGUOUS = "AMBIGUOUS"
REJECTED = "REJECTED"

# What the gap might be. UNCLASSIFIED is honest and common.
DOOR = "DOOR"
DOUBLE_DOOR = "DOUBLE_DOOR"
WINDOW = "WINDOW"
OPEN_TRANSITION = "OPEN_TRANSITION"
UNCLASSIFIED = "UNCLASSIFIED"

# Plausible clear widths in mm. Deliberately wide and overlapping: the bands
# propose a type, they never confirm one.
WIDTH_BANDS = (
    (600, 900, DOOR),              # a narrow internal door
    (700, 1100, DOOR),
    (1100, 1900, DOUBLE_DOOR),
    (600, 2500, WINDOW),
    (1900, 6000, OPEN_TRANSITION),
)

# Evidence codes, so a candidate can be audited rather than trusted.
E_PAIRED_GAP = "PAIRED_WALL_FACE_GAP"
E_JAMB_BOTH = "JAMBS_BOTH_ENDS"
E_JAMB_ONE = "JAMB_ONE_END"
E_LEAF = "DOOR_LEAF_LINE"
E_SWING = "SWING_ARC"
E_TWO_SPACES = "TWO_MAPPED_SPACES"
E_WIDTH = "PLAUSIBLE_WIDTH"

# SAME_REGION_BOTH_SIDES is topology evidence, NOT opening evidence. I had it in
# STRONG, which conflated two different claims: "the raster may be
# under-segmented here" and "there is a door here". The first is true and
# valuable; the second does not follow. The same observation is equally
# consistent with a missing wall boundary, an open transition, a threshold, a
# false vector gap, or fixture linework.
E_SAME_REGION = "SAME_REGION_BOTH_SIDES"
TOPOLOGY_SPLIT_EVIDENCE = frozenset({E_SAME_REGION})

# EVIDENCE FAMILIES. Counting signals is not enough, because several signals can
# be different measurements of ONE underlying construction: a paired-face gap,
# jambs at its ends and the wall-pair interruption all come out of the same
# vector pairing. Three correlated observations are not three independent
# proofs, so validation is judged by how many FAMILIES agree.
GEOMETRY, TOPOLOGY, SYMBOL, DOCUMENT, SEMANTIC = (
    "GEOMETRY", "TOPOLOGY", "SYMBOL", "DOCUMENT", "SEMANTIC")

EVIDENCE_FAMILY = {
    E_PAIRED_GAP: GEOMETRY,
    E_JAMB_BOTH: GEOMETRY,
    E_JAMB_ONE: GEOMETRY,
    E_LEAF: SYMBOL,
    E_SWING: SYMBOL,
    E_TWO_SPACES: TOPOLOGY,
    E_SAME_REGION: TOPOLOGY,
    E_WIDTH: None,                  # a width band is not evidence of anything
}

# A production opening needs corroboration from a second family. Geometry alone,
# however much of it, is one construction seen several ways.
MIN_FAMILIES_FOR_VALIDATED = 2


class OpeningError(RuntimeError):
    """A candidate could not be assessed from the geometry supplied."""


@dataclass
class OpeningCandidate:
    """A gap that might be an opening, and everything known about it."""

    opening_candidate_id: str
    axis: str                       # H or V — the wall's own direction
    fixed_mm: float                 # the wall line's constant coordinate
    start_mm: float
    end_mm: float
    evidence: list[str] = field(default_factory=list)
    adjacent_space_ids: tuple[str, ...] = ()
    candidate_type: str = UNCLASSIFIED
    height_mm: int | None = None    # never guessed; E34 proper reads a schedule
    geometry_sources: tuple[str, ...] = ("VECTOR_PDF_PAIRED_FACES",)
    wall_segment_id: str = ""
    note: str = ""

    @property
    def width_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    @property
    def strong_evidence(self) -> list[str]:
        return [e for e in self.evidence if EVIDENCE_FAMILY.get(e)]

    @property
    def families(self) -> set[str]:
        """Which independent kinds of evidence support this candidate."""
        return {f for f in (EVIDENCE_FAMILY.get(e) for e in self.evidence) if f}

    @property
    def topology_split_evidence(self) -> list[str]:
        """Evidence that a REGION may need splitting — a separate question."""
        return [e for e in self.evidence if e in TOPOLOGY_SPLIT_EVIDENCE]

    @property
    def suggests_region_split(self) -> bool:
        """Should this region be split? Asked and answered separately from
        whether the connecting feature is a door."""
        return bool(self.topology_split_evidence)

    @property
    def confidence_status(self) -> str:
        """Accumulated evidence decides. No single signal can.

        Requiring two different mapped spaces was circular and is gone: the
        segmentation is known to merge real rooms, so a true opening inside one
        has the same region on both sides and was unreachable by construction.

        Counting signals was also wrong, in the opposite direction. A paired-face
        gap, jambs at its ends and the wall-pair interruption are one vector
        construction observed three ways, and three correlated observations are
        not three proofs. So VALIDATED needs evidence from at least two
        independent FAMILIES; evidence concentrated in one family, however much
        of it, stops at PROBABLE.
        """
        if not self.width_plausible:
            return REJECTED
        fams = self.families
        n = len(self.strong_evidence)
        if len(fams) >= MIN_FAMILIES_FOR_VALIDATED and n >= 3:
            return VALIDATED
        if n >= 2:
            return PROBABLE
        if n >= 1:
            return AMBIGUOUS
        return REJECTED

    @property
    def width_plausible(self) -> bool:
        return any(lo <= self.width_mm <= hi for lo, hi, _ in WIDTH_BANDS)

    def proposed_types(self) -> list[str]:
        return sorted({t for lo, hi, t in WIDTH_BANDS
                       if lo <= self.width_mm <= hi})

    def record(self) -> dict:
        return {
            "opening_candidate_id": self.opening_candidate_id,
            "wall_segment_id": self.wall_segment_id,
            "adjacent_space_ids": list(self.adjacent_space_ids),
            "candidate_type": self.candidate_type,
            "proposed_types": self.proposed_types(),
            "axis": self.axis, "fixed_mm": round(self.fixed_mm, 1),
            "start_mm": round(self.start_mm, 1), "end_mm": round(self.end_mm, 1),
            "width_mm": round(self.width_mm, 1),
            "height_mm": self.height_mm,
            "evidence": list(self.evidence),
            "strong_evidence_count": len(self.strong_evidence),
            "evidence_families": sorted(self.families),
            "suggests_region_split": self.suggests_region_split,
            "topology_split_evidence": self.topology_split_evidence,
            "geometry_sources": list(self.geometry_sources),
            "confidence_status": self.confidence_status,
            "note": self.note,
        }


def _collinear_groups(faces, tol_mm: float = 12.0):
    """Wall faces that lie on the same line, so a gap between them is real."""
    groups: dict[tuple[str, int], list] = {}
    for ori, fixed, a, b in faces:
        key = (ori, int(round(fixed / tol_mm)))
        groups.setdefault(key, []).append((min(a, b), max(a, b)))
    for (ori, k), runs in groups.items():
        yield ori, k * tol_mm, sorted(runs)


def gaps_in_paired_faces(faces, *, min_gap_mm: float = 500,
                         max_gap_mm: float = 6000):
    """Every gap along a run of collinear paired wall faces.

    This is signal A and the seed for every candidate. Starting from PAIRED
    faces is what stops a fixture line opening a candidate: a shower tray, a
    wardrobe and a door leaf are drawn as single lines, so they never appear
    here at all.
    """
    out = []
    for ori, fixed, runs in _collinear_groups(faces):
        merged = [list(runs[0])]
        for a, b in runs[1:]:
            if a <= merged[-1][1] + 1:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        for (a1, b1), (a2, b2) in zip(merged, merged[1:]):
            gap = a2 - b1
            if min_gap_mm <= gap <= max_gap_mm:
                out.append((ori, fixed, b1, a2))
    return out


def find_candidates(faces, *, jambs=None, leaves=None, arcs=None,
                    space_at=None, id_prefix: str = "OC") -> list[OpeningCandidate]:
    """Assemble candidates from a seed gap plus whatever else corroborates it.

    `space_at(axis, fixed_mm, along_mm, side)` returns the mapped space id on one
    side of the gap, or None. `jambs`, `leaves` and `arcs` are optional geometry
    in mm; each absent signal simply does not contribute, and a candidate with
    too little support ends up AMBIGUOUS or REJECTED rather than dropped.
    """
    jambs = jambs or []
    leaves = leaves or []
    arcs = arcs or []
    out: list[OpeningCandidate] = []
    for i, (ori, fixed, a, b) in enumerate(gaps_in_paired_faces(faces), 1):
        c = OpeningCandidate(f"{id_prefix}-{i:04d}", ori, fixed, a, b)
        c.evidence.append(E_PAIRED_GAP)
        if c.width_plausible:
            c.evidence.append(E_WIDTH)

        ends_hit = sum(1 for end in (a, b)
                       if any(_near_perpendicular(j, ori, fixed, end)
                              for j in jambs))
        if ends_hit == 2:
            c.evidence.append(E_JAMB_BOTH)
        elif ends_hit == 1:
            c.evidence.append(E_JAMB_ONE)

        mid = (a + b) / 2
        if any(_inside_gap(l, ori, fixed, a, b) for l in leaves):
            c.evidence.append(E_LEAF)
        if any(_arc_near(arc, ori, fixed, mid) for arc in arcs):
            c.evidence.append(E_SWING)

        if space_at is not None:
            left = space_at(ori, fixed, mid, -1)
            right = space_at(ori, fixed, mid, +1)
            sides = tuple(s for s in (left, right) if s)
            c.adjacent_space_ids = sides
            if left and right and left != right:
                c.evidence.append(E_TWO_SPACES)
            elif left and right and left == right:
                c.evidence.append(E_SAME_REGION)
                c.note = (f"the same space ({left}) on both sides — an opening "
                          "inside an under-segmented region looks exactly like "
                          "this, so this is a topology candidate, not a phantom")
            elif len(sides) < 2:
                c.note = ("only one side is a mapped space — may open onto a "
                          "duct, a shaft or unmapped area")
        types = c.proposed_types()
        c.candidate_type = types[0] if len(types) == 1 else UNCLASSIFIED
        out.append(c)
    return out


def _near_perpendicular(seg, ori: str, fixed: float, at: float,
                        tol_mm: float = 80.0) -> bool:
    """A short segment crossing the wall line at one end of the gap — a jamb."""
    s_ori, s_fixed, s_a, s_b = seg
    if s_ori == ori:
        return False
    return (abs(s_fixed - at) <= tol_mm
            and min(s_a, s_b) - tol_mm <= fixed <= max(s_a, s_b) + tol_mm)


def _inside_gap(seg, ori: str, fixed: float, a: float, b: float,
                tol_mm: float = 120.0) -> bool:
    """A line starting in the gap — a door leaf drawn open."""
    s_ori, s_fixed, s_a, s_b = seg
    if s_ori == ori:
        return False
    return (a - tol_mm <= s_fixed <= b + tol_mm
            and abs(min(s_a, s_b) - fixed) <= tol_mm * 3)


def _arc_near(arc, ori: str, fixed: float, mid: float,
              tol_mm: float = 400.0) -> bool:
    """A bezier whose chord starts near the middle of the gap.

    The tolerance is tight on purpose. At 1500 mm this signal fired on 82 of 94
    candidates on AR-00 — with 2,399 arcs scattered across a villa floor, almost
    every gap has one within a metre and a half. A signal that fires on 87% of
    candidates is not evidence about any of them.
    """
    x1, y1, x2, y2 = arc
    px, py = ((mid, fixed) if ori == "H" else (fixed, mid))
    return min(math.hypot(x1 - px, y1 - py), math.hypot(x2 - px, y2 - py)) <= tol_mm


def summarise(cands: list[OpeningCandidate]) -> dict:
    """Counts by status and by evidence, for the spike report."""
    import collections
    by_status = collections.Counter(c.confidence_status for c in cands)
    by_ev = collections.Counter(e for c in cands for e in c.evidence)
    return {
        "candidates": len(cands),
        "by_status": dict(by_status),
        "by_evidence": dict(by_ev),
        "validated_widths": sorted(round(c.width_mm) for c in cands
                                   if c.confidence_status == VALIDATED),
    }
