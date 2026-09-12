"""E25 — Wall Segment & Dimension Ownership.

The Test 1 failures that survived E23 were all ownership failures: a 6350 read
off the bathroom strip and applied to the dining room, a 2450 borrowed from the
neighbouring dress room, a bathroom merged into a bedroom because their shared
door is drawn as a gap. Every one of them is the same mistake — a number that
belongs to one boundary being spent on another.

So this module never works with loose dimensions. It works with *boundaries*.
Every wall segment is derived from the wall body actually drawn between two
spaces, and carries the space it bounds, what is on the other side, and how it
was established. A dimension that cannot be tied to a boundary does not get used.

Door openings are the hard part, because a door is drawn as an absence. A gap is
treated as an opening only when it is a jamb pair: bounded on both sides by wall
running along the gap's own axis, and no wider than a door. Every bridge is
recorded as an Opening with its measured width — nothing is quietly repaired.
A gap that fails the test stays open and the boundary is flagged OPEN, which is
the honest answer for an open-plan transition and the reason the dining room
never becomes a rectangle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable

import numpy as np

# What is on the far side of a boundary run.
WALL = "WALL"                 # solid wall body — a real, measurable wall face
OPENING = "OPENING"           # proven jamb pair: a door or window
OPEN = "OPEN"                 # open-plan transition into another space
EXTERNAL = "EXTERNAL"         # the outside of the building

VALIDATED = "VALIDATED"
UNRESOLVED = "UNRESOLVED"


class WallError(RuntimeError):
    """A boundary could not be established — flagged, never invented."""


@dataclass(frozen=True)
class Opening:
    """A gap in a wall that was proved to be a jamb pair."""

    id: str
    width_mm: int
    axis: str                      # "H" or "V" — the wall's own direction
    at_px: tuple[int, int]
    max_allowed_mm: int

    @property
    def provenance(self) -> str:
        return (f"jamb pair, {self.axis} wall, gap {self.width_mm} mm "
                f"<= door limit {self.max_allowed_mm} mm")


@dataclass(frozen=True)
class WallSegment:
    """One straight run of a space's boundary."""

    wall_id: str
    space_id: str
    side: str                      # N / S / E / W — which face of the space
    start_px: tuple[int, int]
    end_px: tuple[int, int]
    length_mm: int
    far_side: str                  # WALL / OPENING / OPEN / EXTERNAL
    adjoining_space: str | None
    classification: str            # INTERNAL / EXTERNAL
    opening_ids: tuple[str, ...] = ()
    source_drawing: str = ""
    source_revision: str = ""
    validation: str = VALIDATED
    note: str = ""

    @property
    def length_m(self) -> Decimal:
        return Decimal(self.length_mm) / 1000

    @property
    def is_measurable_wall(self) -> bool:
        """Only a real wall face carries a wall finish."""
        return self.far_side in (WALL, OPENING, EXTERNAL)


@dataclass
class SpaceWalls:
    """Every boundary run of one space, and what they add up to."""

    space_id: str
    segments: list[WallSegment] = field(default_factory=list)
    openings: list[Opening] = field(default_factory=list)

    @property
    def perimeter_m(self) -> Decimal:
        """Every boundary run, open transitions included — the closed outline."""
        return sum((s.length_m for s in self.segments), Decimal(0))

    @property
    def wall_length_m(self) -> Decimal:
        """Only runs that are actually wall. This is what a wall finish follows."""
        return sum((s.length_m for s in self.segments if s.is_measurable_wall), Decimal(0))

    @property
    def open_length_m(self) -> Decimal:
        return sum((s.length_m for s in self.segments if s.far_side == OPEN), Decimal(0))

    @property
    def opening_deduction_m(self) -> Decimal:
        return sum((Decimal(o.width_mm) / 1000 for o in self.openings), Decimal(0))

    @property
    def is_closed(self) -> bool:
        """A space with no open transition is a provable closed boundary."""
        return self.open_length_m == 0

    @property
    def status(self) -> str:
        return VALIDATED if self.is_closed else UNRESOLVED


# --------------------------------------------------------------------- masks

def run_length(mask: np.ndarray, axis: int) -> np.ndarray:
    """Length of the maximal True-run containing each cell, along `axis`."""
    m = mask if axis == 0 else mask.T
    h, _ = m.shape
    idx = np.arange(h)[:, None] * np.ones((1, m.shape[1]), int)
    prev = np.where(~m, idx, -1)
    np.maximum.accumulate(prev, axis=0, out=prev)
    nxt = np.where(~m, idx, h)
    nxt = np.minimum.accumulate(nxt[::-1], axis=0)[::-1]
    out = np.where(m, nxt - prev - 1, 0)
    return out if axis == 0 else out.T


def orientation(wall: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Wall pixels that run vertically, and those that run horizontally.

    This is what separates a jamb from the middle of a room. "Wall above and
    wall below" also describes an empty room; only "wall above and below, both
    part of a *vertical* wall" describes a doorway.
    """
    v = run_length(wall, 0)
    h = run_length(wall, 1)
    return wall & (v > h), wall & (h >= v)


def _bridge_axis(wall: np.ndarray, gate: np.ndarray, max_gap: int, axis: int) -> np.ndarray:
    g = gate if axis == 0 else gate.T
    m = wall if axis == 0 else wall.T
    h = g.shape[0]
    idx = np.arange(h)[:, None] * np.ones((1, g.shape[1]), int)
    prev = np.where(g, idx, -1)
    np.maximum.accumulate(prev, axis=0, out=prev)
    nxt = np.where(g, idx, h)
    nxt = np.minimum.accumulate(nxt[::-1], axis=0)[::-1]
    gap = nxt - prev - 1
    fill = (~m) & (prev >= 0) & (nxt < h) & (gap > 0) & (gap <= max_gap)
    return fill if axis == 0 else fill.T


def bridge_openings(wall: np.ndarray, max_gap_px: int) -> tuple[np.ndarray, np.ndarray]:
    """Close proven jamb pairs. Returns (closed wall, the bridge pixels only)."""
    if max_gap_px <= 0:
        return wall, np.zeros_like(wall)
    vert, horiz = orientation(wall)
    v = _bridge_axis(wall, vert, max_gap_px, 0)
    h = _bridge_axis(wall, horiz, max_gap_px, 1)
    return wall | v | h, v | h


# ----------------------------------------------------------------- segments

_SIDES = {"N": (-1, 0), "S": (1, 0), "W": (0, -1), "E": (0, 1)}


def _runs(cells: np.ndarray, horizontal: bool) -> list[tuple[int, int, int]]:
    """Maximal straight runs of True. Returns (fixed, start, end) triples."""
    out = []
    arr = cells if horizontal else cells.T
    for i in np.flatnonzero(arr.any(axis=1)):
        row = arr[i]
        d = np.diff(np.concatenate(([False], row, [False])).astype(np.int8))
        for s, e in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)):
            out.append((int(i), int(s), int(e)))
    return out


def space_walls(space_id: str, labels: np.ndarray, region_id: int,
                wall: np.ndarray, bridges: np.ndarray, px_mm: Decimal,
                outside_id: int | None = None, *, drawing: str = "",
                revision: str = "", id_to_space: dict[int, str] | None = None,
                min_run_mm: int = 100, max_opening_mm: int = 0,
                fill_region: bool = True) -> SpaceWalls:
    """Decompose one space's boundary into wall segments with provenance.

    `fill_region` closes the holes that printed fixtures, text and dimension
    numerals punch in the region before tracing. Without it the boundary walks
    around every WC and glyph and the perimeter roughly doubles — measuring the
    furniture, not the room. Turn it off only when the holes ARE the subject.
    """
    R = labels == region_id
    if not R.any():
        raise WallError(f"{space_id}: region {region_id} is not in the label map")
    if fill_region:
        from engine.geometry import fill_holes
        R = fill_holes(R)
    sw = SpaceWalls(space_id=space_id)
    id_to_space = id_to_space or {}
    n_open = 0

    for side, (dy, dx) in _SIDES.items():
        # beyond[y, x] tells what sits on the `side` neighbour of (y, x):
        # rolling by -dy/-dx brings that neighbour's value onto (y, x).
        def look(arr, step=1):
            return np.roll(np.roll(arr, -dy * step, 0), -dx * step, 1)

        edge = R & ~look(R)                  # cells of R whose neighbour leaves R
        far_wall, far_bridge, far_lab = look(wall), look(bridges), look(labels)

        for kind, cells in (
            (OPENING, edge & far_bridge),
            (WALL, edge & far_wall & ~far_bridge),
            (OPEN, edge & ~far_wall & ~far_bridge),
        ):
            if not cells.any():
                continue
            for fixed, s, e in _runs(cells, horizontal=side in ("N", "S")):
                length = int(Decimal(e - s) * px_mm)
                if length < min_run_mm:
                    continue
                # (row, col) of the run's midpoint, and its two ends
                mid_rc = ((fixed, (s + e) // 2) if side in ("N", "S")
                          else ((s + e) // 2, fixed))
                if side in ("N", "S"):
                    a, b = (s, fixed), (e, fixed)
                else:
                    a, b = (fixed, s), (fixed, e)

                adj = None
                classification = "INTERNAL"
                if kind == OPEN:
                    adj = id_to_space.get(int(far_lab[mid_rc]),
                                          f"region-{int(far_lab[mid_rc])}")
                elif kind in (WALL, OPENING) and outside_id is not None:
                    # march past the wall body; whatever space is on the other
                    # side decides internal vs external. Never guessed from
                    # position on the sheet.
                    reach = max(2, int(Decimal(600) / px_mm))
                    beyond_id = None
                    for step in range(1, reach + 1):
                        v = int(look(labels, step)[mid_rc])
                        if not look(wall, step)[mid_rc]:
                            beyond_id = v
                            break
                    if beyond_id == outside_id:
                        classification = "EXTERNAL"
                    elif beyond_id is not None and beyond_id != 0:
                        adj = id_to_space.get(beyond_id, f"region-{beyond_id}")

                ids: tuple[str, ...] = ()
                if kind == OPENING:
                    n_open += 1
                    oid = f"{space_id}-OP{n_open:02d}"
                    sw.openings.append(Opening(
                        id=oid, width_mm=length,
                        axis="H" if side in ("N", "S") else "V",
                        at_px=a, max_allowed_mm=max_opening_mm))
                    ids = (oid,)

                sw.segments.append(WallSegment(
                    wall_id=f"{space_id}-{side}{len(sw.segments) + 1:02d}",
                    space_id=space_id, side=side, start_px=a, end_px=b,
                    length_mm=length, far_side=kind, adjoining_space=adj,
                    classification=classification,
                    opening_ids=ids, source_drawing=drawing, source_revision=revision,
                    validation=VALIDATED if kind != OPEN else UNRESOLVED,
                    note="" if kind != OPEN else "open-plan transition — not a wall",
                ))
    return sw


def duplicate_walls(all_walls: Iterable[SpaceWalls], px_mm: Decimal,
                    max_wall_mm: int = 600) -> list[tuple[str, str, int]]:
    """Find the segment pairs that are the two faces of one shared wall.

    A wall between two rooms is measured once by each room, and that is correct
    — each room's finish stops at its own face. What is NOT correct is adding
    both faces into one wall-area total as if they were different walls. This
    reports every such pair so a caller can see, and prove, which lengths are
    two sides of the same block.

    A pair qualifies when the segments face each other, sit no further apart
    than a wall is thick, and actually overlap along their length.
    """
    segs = [s for w in all_walls for s in w.segments if s.far_side in (WALL, OPENING)]
    opposite = ({"N", "S"}, {"E", "W"})
    pairs: list[tuple[str, str, int]] = []
    for i, a in enumerate(segs):
        for b in segs[i + 1:]:
            if a.space_id == b.space_id or {a.side, b.side} not in opposite:
                continue
            # start_px is always (x, y). A N/S run (a horizontal wall) extends
            # along x and is offset in y; an E/W run is the other way round.
            along = 0 if a.side in ("N", "S") else 1
            off = 1 - along
            a0, a1 = (a.start_px[along], a.end_px[along]), a.start_px[off]
            b0, b1 = (b.start_px[along], b.end_px[along]), b.start_px[off]
            offset = abs(Decimal(a1 - b1)) * px_mm
            if offset > max_wall_mm:
                continue
            lo = max(min(a0), min(b0))
            hi = min(max(a0), max(b0))
            overlap = int(Decimal(hi - lo) * px_mm)
            if overlap <= 0:
                continue
            pairs.append((a.wall_id, b.wall_id, overlap))
    return pairs
