"""E90 — turn a pixel region into an ordered rectilinear ring of runs.

The matcher needs the region's boundary as a SEARCH GUIDE: an ordered
sequence of axis-aligned runs, each of which can then be matched to real
vector geometry. A pixel mask on its own is not that — it is a blob — so
this module traces the blob's outline and collapses it into runs.

Two things it must get right, because both have bitten this project before:

  1. THE RING IS ORDERED. A bag of boundary segments cannot rebuild a
     polygon: the corners come from consecutive runs meeting, so the order
     IS the structure. Traced as directed unit edges chained head-to-tail.

  2. THE FRAME IS NOT THE IDENTITY. This sheet's raster and vector axes are
     related by SWAP_FLIP_Y — vector-x follows pixel-y. So a run that is
     vertical in the image is HORIZONTAL in the drawing, and the axis is
     read off the converted endpoints rather than assumed from the pixel
     direction. Getting this backwards is what made the first leak map
     report 27 of 30 frontiers as having no vector separator.

Everything here is approximate by construction — it is pixel work. The runs
carry pixel-derived coordinates only so the matcher knows WHERE TO LOOK.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

AXIS_H = "H"
AXIS_V = "V"


@dataclass(frozen=True)
class BoundaryRun:
    """One axis-aligned stretch of a region's traced outline.

    `axis` and the coordinates are in DRAWING millimetres, converted through
    the frame. `axis` is H when the run holds a constant vector-y and spans
    vector-x, V when it holds a constant vector-x.
    """

    run_index: int
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    pixel_length: int

    @property
    def length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    def record(self) -> dict:
        return {"run_index": self.run_index, "axis": self.axis,
                "APPROXIMATE_fixed_mm": round(self.fixed_mm, 1),
                "APPROXIMATE_interval_mm": [round(self.start_mm, 1),
                                            round(self.end_mm, 1)],
                "APPROXIMATE_length_mm": round(self.length_mm, 1),
                "pixel_length": self.pixel_length,
                "this_is": ("a SEARCH GUIDE traced from pixels. No "
                            "coordinate here may be released")}


def trace(labels, label: int, frame, px_mm: float,
          *, min_run_px: int = 2) -> list:
    """The region's outer ring, as ordered runs in drawing millimetres."""
    lab = np.asarray(labels)
    mask = lab == label
    if not mask.any():
        return []

    # Work in a padded sub-window: the ring is local, and padding means the
    # neighbour tests never fall off the array.
    ys, xs = np.nonzero(mask)
    r0, r1 = int(ys.min()), int(ys.max())
    c0, c1 = int(xs.min()), int(xs.max())
    sub = np.zeros((r1 - r0 + 3, c1 - c0 + 3), bool)
    sub[1:-1, 1:-1] = mask[r0:r1 + 1, c0:c1 + 1]

    edges = _unit_edges(sub)
    if not edges:
        return []
    ring = _chain(edges)
    if len(ring) < 4:
        return []

    # Collapse consecutive unit edges with the same direction into runs, in
    # PIXEL space, then convert each run's endpoints through the frame.
    runs_px = _collapse(ring)

    out, n = [], 0
    for (ar, ac), (br, bc) in runs_px:
        length_px = max(abs(br - ar), abs(bc - ac))
        if length_px < min_run_px:
            continue
        # Corner (r, c) in sub-window space -> pixel centre in the full
        # image -> drawing millimetres.
        ax, ay = frame.to_vector((ac + c0 - 1) * px_mm, (ar + r0 - 1) * px_mm)
        bx, by = frame.to_vector((bc + c0 - 1) * px_mm, (br + r0 - 1) * px_mm)
        n += 1
        if abs(ay - by) <= abs(ax - bx):
            out.append(BoundaryRun(n, AXIS_H, (ay + by) / 2.0,
                                   min(ax, bx), max(ax, bx), length_px))
        else:
            out.append(BoundaryRun(n, AXIS_V, (ax + bx) / 2.0,
                                   min(ay, by), max(ay, by), length_px))
    return out


def _unit_edges(mask) -> dict:
    """Directed unit edges of the mask boundary, tail corner -> heads.

    Each pixel contributes an edge for every side whose neighbour is
    outside. The directions are chosen so that the region stays on one
    consistent side, which is what makes the chaining unambiguous.

    Found by shifted array comparisons rather than by looping over pixels.
    A 365 m² region is ~3.1 million pixels and a per-pixel loop over all of
    them took seconds, while the boundary itself is only a few thousand
    edges: the slices reduce the work from the region's AREA to its
    PERIMETER. The mask is padded by the caller, so a shifted comparison
    needs no wraparound — only an index offset.
    """
    m = np.asarray(mask)
    edges: dict = {}

    def add(rows, cols, dr0, dc0, dr1, dc1):
        for r, c in zip((rows + 1).tolist(), (cols + 1).tolist()):
            edges.setdefault((r + dr0, c + dc0), []).append(
                (r + dr1, c + dc1))

    core = m[1:-1, 1:-1]
    # top side open: (r,c) -> (r,c+1)
    add(*np.nonzero(core & ~m[:-2, 1:-1]), 0, 0, 0, 1)
    # right side open: (r,c+1) -> (r+1,c+1)
    add(*np.nonzero(core & ~m[1:-1, 2:]), 0, 1, 1, 1)
    # bottom side open: (r+1,c+1) -> (r+1,c)
    add(*np.nonzero(core & ~m[2:, 1:-1]), 1, 1, 1, 0)
    # left side open: (r+1,c) -> (r,c)
    add(*np.nonzero(core & ~m[1:-1, :-2]), 1, 0, 0, 0)
    return edges


def _chain(edges: dict) -> list:
    """Walk the directed edges into the longest closed ring.

    At a pinch point — two region pixels touching only at a corner — a tail
    has two possible heads. Taking them in a fixed order keeps the walk
    deterministic; the ring may cut such a pinch off, which is correct for
    a measurement guide: a one-pixel diagonal touch is not a doorway.
    """
    best: list = []
    starts = sorted(edges)
    used_pairs: set = set()
    # Computed ONCE. Inside the per-start loop this summed every edge for
    # every candidate start, which is quadratic in the boundary length and
    # cost 5 seconds on a single large region.
    limit = sum(len(v) for v in edges.values()) + 8
    for start in starts:
        if not edges.get(start):
            continue
        path = [start]
        node = start
        guard = 0
        while guard < limit:
            guard += 1
            heads = edges.get(node)
            if not heads:
                break
            nxt = None
            for cand in heads:
                if (node, cand) not in used_pairs:
                    nxt = cand
                    break
            if nxt is None:
                break
            used_pairs.add((node, nxt))
            path.append(nxt)
            node = nxt
            if node == start:
                break
        if node == start and len(path) > len(best):
            best = path
    return best


def _collapse(ring: list) -> list:
    """Join consecutive unit edges running the same way into one run."""
    if len(ring) < 2:
        return []
    out = []
    anchor = ring[0]
    prev = ring[0]
    for point in ring[1:]:
        d_prev = (prev[0] - anchor[0], prev[1] - anchor[1])
        d_next = (point[0] - prev[0], point[1] - prev[1])
        straight = (d_prev == (0, 0)
                    or (d_prev[0] == 0) == (d_next[0] == 0))
        if not straight:
            out.append((anchor, prev))
            anchor = prev
        prev = point
    out.append((anchor, prev))
    return out


# ------------------------------------------------------- simplification

# A traced ring is a pixel staircase: an ink edge that is not exactly on the
# pixel grid produces a one-pixel jag every few pixels, and a real room came
# out as 292 runs for a 25 m perimeter. Those jags are rendering artefacts,
# not features of the building — this project has already measured the same
# effect from the other side, where a raster region's perimeter was 4.7x
# that of the square with its own area.
#
# So the ring is simplified rectilinearly BEFORE matching. The threshold is
# in millimetres and must sit above the pixel pitch (10.8 mm here) and below
# the smallest real feature: a pier or a door jamb is >= 100 mm, and a
# doorway is ~900 mm, so both survive.
MIN_SIGNIFICANT_RUN_MM = 100.0


def simplify(runs: list, *, min_run_mm: float = MIN_SIGNIFICANT_RUN_MM
             ) -> list:
    """Drop staircase jags, keeping an ordered alternating ring.

    A short run is removed by merging its two neighbours, which are
    necessarily on the same axis (the ring alternates), into one run. The
    surviving fixed coordinate is the LONGER neighbour's: the dominant line
    is the one the draughtsman drew, and averaging would move the boundary
    off both of them.
    """
    work = [(r.axis, r.fixed_mm, r.start_mm, r.end_mm, r.pixel_length)
            for r in runs]
    if len(work) < 5:
        return list(runs)

    changed = True
    while changed and len(work) > 4:
        changed = False
        # Shortest first, so removing one jag cannot mask another.
        order = sorted(range(len(work)),
                       key=lambda i: abs(work[i][3] - work[i][2]))
        for i in order:
            if abs(work[i][3] - work[i][2]) >= min_run_mm:
                break
            n = len(work)
            if n <= 4:
                break
            prev, nxt = work[(i - 1) % n], work[(i + 1) % n]
            if prev[0] != nxt[0]:
                continue                  # not a jag: a genuine corner pair
            keep = prev if (abs(prev[3] - prev[2])
                            >= abs(nxt[3] - nxt[2])) else nxt
            merged = (prev[0], keep[1],
                      min(prev[2], nxt[2], prev[3], nxt[3]),
                      max(prev[2], nxt[2], prev[3], nxt[3]),
                      prev[4] + nxt[4])
            keep_idx = [j for j in range(n)
                        if j not in {i, (i - 1) % n, (i + 1) % n}]
            rebuilt = [work[j] for j in keep_idx]
            insert_at = min((i - 1) % n, len(rebuilt))
            rebuilt.insert(insert_at, merged)
            work = rebuilt
            changed = True
            break

    return [BoundaryRun(k + 1, a, f, s, e, p)
            for k, (a, f, s, e, p) in enumerate(work)]
