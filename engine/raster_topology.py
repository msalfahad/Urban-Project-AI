"""E87 — find the space in the picture. Measure nothing.

Global vector topology could not discover the floor: 32 labelled rooms sat in
one merged blob because five hairline gaps and a few unestablished extensions
left the wall solid porous. A raster render does not care about a 0.3 mm gap
in a polyline — ink is ink — so the image can separate rooms the vector solid
merges.

This module therefore answers exactly one question: WHERE ARE THE CONNECTED
SPACES. It answers it in PIXELS, and every quantity it emits is named
approximate. A pixel coordinate may become a drawing coordinate only as a
SEARCH WINDOW for the vector matcher — never as a released millimetre.

Two rules keep it honest:

  1. It builds from the DRAWING RENDER and the ESTABLISHED WALL SOLID. It
     never reads the golden regions, the human overlay, the space map's room
     list or any benchmark. Those may SCORE this output afterwards (§16) and
     may not build it, or the metric would be measuring itself.

  2. Diagnostic wall hypotheses are soft: they are reported as proposals and
     are not burned into the barrier mask. Portals stay PASSABLE, because a
     doorway is how two rooms connect and closing it would manufacture the
     separation we are trying to detect.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

import numpy as np

from engine.geometry import label_regions, outside_region_ids

ALGORITHM = "INK_AND_ESTABLISHED_SOLID_BARRIER_CONNECTED_COMPONENTS_V1"

# Barrier provenance, so a separation can be traced to what caused it.
BARRIER_RENDERED_INK = "RENDERED_INK"
BARRIER_ESTABLISHED_SOLID = "ESTABLISHED_WALL_SOLID"
BARRIER_DIAGNOSTIC_SOFT = "DIAGNOSTIC_WALL_HYPOTHESIS_SOFT_PROPOSAL_ONLY"

# A region smaller than this is a glyph, a hatch cell or a dimension tick,
# not a space. Stated in m² because that is the unit a human can argue with.
MIN_REGION_M2 = 0.8
# Two regions are adjacent if their pixels come within this many pixels of
# each other — i.e. they are separated by a thin barrier rather than by the
# width of the building.
ADJACENCY_REACH_PX = 6
# A barrier stretch narrower than this, between two regions, looks like a
# doorway rather than a wall.
MAX_OPENING_BARRIER_PX = 22
# Below this the two regions are all but touching: a hairline, not a door.
MIN_OPENING_BARRIER_PX = 1


@dataclass(frozen=True)
class CandidateOpening:
    """A place where two regions are separated by very little barrier.

    A candidate, emphatically: the pixels say "thin here", which is what a
    doorway looks like and also what a badly-rendered wall junction looks
    like. Width is reported in pixels AND in approximate mm, and neither may
    become an opening width — §3 forbids exactly that.
    """

    opening_id: str
    region_a: str
    region_b: str
    centroid_px: tuple
    centroid_mm: tuple
    barrier_thickness_px: int
    approximate_width_mm: float
    pixel_count: int
    why: str = ""

    def record(self) -> dict:
        return {
            "candidate_opening_id": self.opening_id,
            "between": [self.region_a, self.region_b],
            "centroid_px": list(self.centroid_px),
            "SEARCH_WINDOW_centroid_mm": [round(v, 1)
                                          for v in self.centroid_mm],
            "barrier_thickness_px": self.barrier_thickness_px,
            "APPROXIMATE_width_mm": round(self.approximate_width_mm, 1),
            "pixel_count": self.pixel_count,
            "may_not_supply": ("an opening width. This is a localisation "
                              "for the vector matcher, not a measurement"),
            "why": self.why,
        }


@dataclass(frozen=True)
class RegionAdjacency:
    region_a: str
    region_b: str
    contact_px: int
    min_barrier_px: int
    candidate_opening_ids: tuple[str, ...] = ()

    def record(self) -> dict:
        return {"between": [self.region_a, self.region_b],
                "contact_px": self.contact_px,
                "thinnest_barrier_px": self.min_barrier_px,
                "candidate_opening_ids": list(self.candidate_opening_ids)}


@dataclass
class Topology:
    """The automatic result, before anything scores it."""

    regions: list = field(default_factory=list)
    adjacencies: list = field(default_factory=list)
    openings: list = field(default_factory=list)
    soft_barrier_proposals: list = field(default_factory=list)
    labels: object = None                 # the label map, for the matcher
    region_label_of: dict = field(default_factory=dict)
    px_mm: float = 0.0
    provenance: dict = field(default_factory=dict)
    notes: dict = field(default_factory=dict)

    @property
    def output_hash(self) -> str:
        """Hash of the automatic output, so §16 can score a FROZEN result."""
        payload = "|".join(
            f"{r.region_id}:{r.pixel_count}:{r.centroid_mm[0]:.1f},"
            f"{r.centroid_mm[1]:.1f}" for r in self.regions)
        payload += "||" + "|".join(
            f"{a.region_a}-{a.region_b}:{a.contact_px}"
            for a in self.adjacencies)
        # Openings are part of the automatic output §16 scores, so they are
        # part of what gets frozen. A hash that ignored them would let the
        # opening set change under a "frozen" result.
        payload += "||" + "|".join(
            f"{o.opening_id}:{o.region_a}-{o.region_b}:"
            f"{o.barrier_thickness_px}:{o.pixel_count}"
            for o in self.openings)
        return hashlib.sha256(payload.encode()).hexdigest()[:24]

    def record(self, *, region_limit: int = 200) -> dict:
        return {
            "AUTOMATIC_TOPOLOGY_OUTPUT_HASH": self.output_hash,
            "algorithm": ALGORITHM,
            "regions": len(self.regions),
            "adjacencies": len(self.adjacencies),
            "candidate_openings": len(self.openings),
            "soft_barrier_proposals": len(self.soft_barrier_proposals),
            "total_APPROXIMATE_area_m2": round(
                sum(r.approximate_area_m2 for r in self.regions), 2),
            "by_confidence": dict(Counter(
                _confidence_band(r.confidence) for r in self.regions)),
            "region_rows": [r.record() for r in self.regions[:region_limit]],
            "adjacency_rows": [a.record() for a in self.adjacencies],
            "candidate_opening_rows": [o.record() for o in self.openings],
            "soft_barrier_proposal_rows": list(self.soft_barrier_proposals),
            "built_from": (
                "the drawing render and the ESTABLISHED wall solid only. "
                "No golden region, no human overlay, no room list and no "
                "benchmark entered this result — those may SCORE it "
                "afterwards and may not build it"),
            "diagnostic_walls_were": (
                "reported as soft proposals and NOT burned into the barrier "
                "mask. A hypothesis may not create a separation"),
            "portals_were": (
                "left PASSABLE. A doorway is how two rooms connect, and "
                "closing it would manufacture the separation this stage "
                "exists to detect"),
            "what_this_may_not_supply": (
                "a wall coordinate, a wall thickness, an opening width, a "
                "released area or a released perimeter. Pixel coordinates "
                "here are SEARCH WINDOWS for the vector matcher"),
            "provenance": dict(self.provenance),
            "notes": dict(self.notes),
        }


def _confidence_band(c: float | None) -> str:
    if c is None:
        return "UNSCORED"
    if c >= 0.75:
        return "HIGH"
    return "MODERATE" if c >= 0.5 else "LOW"


# ----------------------------------------------------------- the pipeline

def build(seg, frame, *, established_solid=None, diagnostic_solid=None,
          portal_barriers=(), min_region_m2: float = MIN_REGION_M2,
          drawing_id: str = "", revision: str = "") -> Topology:
    """Segment the render into connected spaces, reinforced by vector walls.

    `seg` is the existing Segmentation (render, ink mask, px_mm). `frame` is
    the measured pixel-to-vector mapping. The established solid is rasterised
    and unioned into the barrier mask as STRONG evidence; the diagnostic
    solid is only described.
    """
    from engine.space_objects import TopologyRegion, TOPOLOGY_PROPOSED

    px = float(seg.px_mm)
    ink = np.asarray(seg.wall_mask, dtype=bool)
    h, w = ink.shape

    barrier = ink.copy()
    solid_px = 0
    if established_solid is not None and not established_solid.is_empty:
        solid_mask = _rasterise(established_solid, frame, px, (h, w))
        solid_px = int(solid_mask.sum())
        barrier |= solid_mask

    # Portals stay passable: carve accepted barrier openings back OUT of the
    # mask so a doorway cannot separate two rooms in the image.
    reopened_px = 0
    for b in portal_barriers:
        poly = getattr(b, "polygon", None)
        if poly is None or getattr(poly, "is_empty", True):
            continue
        hole = _rasterise(poly, frame, px, (h, w))
        reopened_px += int((barrier & hole).sum())
        barrier &= ~hole

    free = ~barrier
    lab = label_regions(free)
    outside = outside_region_ids(lab)

    px_m2 = (px / 1000.0) ** 2
    ids, counts = np.unique(lab, return_counts=True)

    regions, region_of_label = [], {}
    n = 0
    for rid, count in zip(ids.tolist(), counts.tolist()):
        if rid == 0 or rid in outside:
            continue
        if count * px_m2 < min_region_m2:
            continue
        n += 1
        region_id = f"RTR-{n:04d}"
        region_of_label[int(rid)] = region_id
        ys, xs = np.nonzero(lab == rid)
        cx, cy = float(xs.mean()), float(ys.mean())
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        regions.append(TopologyRegion(
            region_id=region_id,
            source="RASTER_SEGMENTATION_WITH_VECTOR_BARRIERS",
            approximate_area_m2=count * px_m2,
            centroid_mm=frame.to_vector((cx + 0.5) * px, (cy + 0.5) * px),
            bbox_mm=frame.bbox_to_vector((x0 * px, y0 * px,
                                          x1 * px, y1 * px)),
            pixel_count=int(count),
            confidence=_confidence(count * px_m2, xs, ys),
            status=TOPOLOGY_PROPOSED,
            provenance={"raster_label": int(rid), "algorithm": ALGORITHM,
                        "dpi": seg.dpi, "ink_threshold": seg.ink_threshold,
                        "px_mm": round(px, 4)},
            why=("one connected component of the render's free space after "
                 "established wall material was added as a barrier and "
                 "accepted portal openings were reopened")))

    adjacencies, openings = _adjacency(lab, region_of_label, frame, px)

    # Re-emit regions carrying their adjacency, now that it is known.
    by_id = {r.region_id: r for r in regions}
    adj_of: dict = {}
    open_of: dict = {}
    for a in adjacencies:
        adj_of.setdefault(a.region_a, []).append(a.region_b)
        adj_of.setdefault(a.region_b, []).append(a.region_a)
        for oid in a.candidate_opening_ids:
            open_of.setdefault(a.region_a, []).append(oid)
            open_of.setdefault(a.region_b, []).append(oid)
    regions = [
        TopologyRegion(
            **{**r.__dict__,
               "adjacent_region_ids": tuple(sorted(
                   set(adj_of.get(r.region_id, ())))),
               "candidate_opening_ids": tuple(sorted(
                   set(open_of.get(r.region_id, ()))))})
        for r in (by_id[k] for k in sorted(by_id))]

    soft = _soft_proposals(established_solid, diagnostic_solid)

    return Topology(
        regions=regions, adjacencies=adjacencies, openings=openings,
        soft_barrier_proposals=soft, labels=lab,
        region_label_of={v: k for k, v in region_of_label.items()},
        px_mm=px,
        provenance={
            "algorithm": ALGORITHM,
            "drawing_id": drawing_id, "drawing_revision": revision,
            "source_path": getattr(seg, "source_path", ""),
            "source_sha256": getattr(seg, "source_sha256", "")[:16],
            "dpi": seg.dpi, "ink_threshold": seg.ink_threshold,
            "px_mm": round(px, 4),
            "frame": getattr(frame, "name", ""),
            "min_region_m2": min_region_m2,
            "established_solid_barrier_px": solid_px,
            "portal_pixels_reopened": reopened_px,
        },
        notes={
            "regions_below_min_area_dropped": int(sum(
                1 for rid, c in zip(ids.tolist(), counts.tolist())
                if rid != 0 and rid not in outside
                and c * px_m2 < min_region_m2)),
            "outside_components": len(outside),
            "why_outside_is_dropped": (
                "components touching the sheet border are the paper, the "
                "margin and the title block, not spaces in the building"),
        })


def _confidence(area_m2: float, xs, ys) -> float:
    """How much this component looks like a room, from the pixels alone.

    Deliberately crude and deliberately NOT trained on the answer: a big
    component that fills its own bounding box compactly looks more like a
    room than a thin sliver threading between hatch lines. It ranks regions
    for review; it is not a probability and nothing gates on it.
    """
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    box = max((x1 - x0 + 1) * (y1 - y0 + 1), 1)
    fill = float(len(xs)) / box
    size = min(area_m2 / 12.0, 1.0)          # 12 m² is an unremarkable room
    return round(0.5 * fill + 0.5 * size, 3)


def _rasterise(poly, frame, px: float, shape) -> np.ndarray:
    """Vector polygon -> pixel mask, by covering each part's own footprint.

    Coarse on purpose. This mask is a BARRIER for segmentation, never a
    measurement, so half a pixel of error at an edge cannot reach a
    quantity.

    Testing pixel centres across the whole polygon's bounding box is
    hopeless here: the wall solid's bbox is the whole building, which is
    millions of containment tests for 117 m² of actual wall. So each PART is
    rasterised into its own small box, and a part that IS its own envelope —
    which an axis-aligned wall rectangle is — is filled directly and
    exactly, with no per-pixel predicate at all.
    """
    from shapely.geometry import box as shbox
    from shapely.prepared import prep

    h, w = shape
    out = np.zeros(shape, bool)
    parts = (list(poly.geoms) if hasattr(poly, "geoms") else [poly])

    for part in parts:
        if part.is_empty or part.area <= 0.0:
            continue
        r0, r1, c0, c1 = _pixel_box(part.bounds, frame, px, shape)
        if r1 < r0 or c1 < c0:
            continue
        # An axis-aligned rectangle covers its pixel box exactly.
        if part.equals(part.envelope):
            out[r0:r1 + 1, c0:c1 + 1] = True
            continue
        # A non-rectangular part is cut into RECTANGLES first. After the
        # union, wall runs merge into L, T and comb shapes whose bounding
        # boxes span the whole building, and testing every pixel centre
        # inside such a box cost minutes of CPU. Wall geometry is
        # rectilinear, so a sweep over the part's own x-coordinates cuts it
        # into rectangles exactly and each takes the fast path above.
        for rect in _rect_decompose(part):
            rr0, rr1, cc0, cc1 = _pixel_box(rect.bounds, frame, px, shape)
            if rr1 >= rr0 and cc1 >= cc0:
                out[rr0:rr1 + 1, cc0:cc1 + 1] = True
    return out


def _rect_decompose(part, *, max_slabs: int = 600) -> list:
    """Cut a rectilinear polygon into rectangles by a vertical sweep.

    Exact for axis-aligned geometry, which is what a wall solid is. A part
    with more distinct x-coordinates than `max_slabs` is not the
    rectilinear shape this assumes, so its envelope is used instead — a
    barrier slightly too generous, never one too small, and this mask
    segments rather than measures.
    """
    from shapely.geometry import box as shbox

    xs = sorted({round(x, 4) for x, _ in part.exterior.coords})
    if len(xs) < 2 or len(xs) > max_slabs:
        return [part.envelope]

    miny, maxy = part.bounds[1], part.bounds[3]
    out = []
    for a, b in zip(xs, xs[1:]):
        if b <= a:
            continue
        slab = part.intersection(shbox(a, miny, b, maxy))
        if slab.is_empty:
            continue
        for piece in (slab.geoms if hasattr(slab, "geoms") else [slab]):
            if not piece.is_empty and piece.area > 0:
                out.append(piece.envelope)
    return out


def _pixel_box(bounds, frame, px: float, shape) -> tuple:
    """The pixel rows/cols a vector bounding box can touch.

    The frame is an axis swap and/or flip, so a vector box maps to a pixel
    box: mapping the four corners and taking the extremes is exact, not an
    approximation.
    """
    h, w = shape
    minx, miny, maxx, maxy = bounds
    corners = [frame.to_raster(x, y) for x, y in
               ((minx, miny), (minx, maxy), (maxx, miny), (maxx, maxy))]
    rows = [c[1] / px for c in corners]
    cols = [c[0] / px for c in corners]
    return (max(int(min(rows)), 0), min(int(max(rows)) + 1, h - 1),
            max(int(min(cols)), 0), min(int(max(cols)) + 1, w - 1))


def _adjacency(lab, region_of_label: dict, frame, px: float):
    """Which regions are separated by little enough to be worth a look.

    Two regions are adjacent when their pixels come within ADJACENCY_REACH_PX
    of each other. The THINNEST barrier between them is the interesting
    number: a wall-thick separation is a wall, and a door-thick one is a
    candidate opening.
    """
    lab = np.asarray(lab)
    h, w = lab.shape
    keep = np.zeros(lab.max() + 1, bool)
    for k in region_of_label:
        keep[k] = True

    contact: dict = {}
    thinnest: dict = {}
    where: dict = {}

    def note(a: int, b: int, gap: int, row: int, col: int) -> None:
        ra, rb = region_of_label[a], region_of_label[b]
        key = (ra, rb) if ra < rb else (rb, ra)
        contact[key] = contact.get(key, 0) + 1
        if gap < thinnest.get(key, 10**9):
            thinnest[key] = gap
        if gap <= MAX_OPENING_BARRIER_PX:
            where.setdefault(key, []).append((row, col, gap))

    # Scan each row and column for pairs of different labels separated by a
    # short run of barrier. This finds face-to-face gaps in both axes, which
    # is what a doorway or a hairline junction looks like in the image.
    for axis in (0, 1):
        arr = lab if axis == 0 else lab.T
        for i in range(arr.shape[0]):
            line = arr[i]
            nz = np.flatnonzero(line)
            if nz.size < 2:
                continue
            prev_j, prev_v = -1, 0
            for j in nz.tolist():
                v = int(line[j])
                if not keep[v]:
                    prev_j, prev_v = j, v
                    continue
                if prev_v and keep[prev_v] and prev_v != v:
                    gap = j - prev_j - 1
                    if 0 <= gap <= ADJACENCY_REACH_PX + MAX_OPENING_BARRIER_PX:
                        row, col = ((i, (prev_j + j) // 2) if axis == 0
                                    else ((prev_j + j) // 2, i))
                        note(prev_v, v, gap, row, col)
                prev_j, prev_v = j, v

    openings, adjacencies = [], []
    n = 0
    for key in sorted(contact):
        hits = where.get(key, [])
        oids = []
        if hits:
            # One opening per contiguous cluster of thin contacts, so a
            # single doorway is one candidate rather than fifty pixels.
            for cluster in _cluster(hits):
                n += 1
                rows = [c[0] for c in cluster]
                cols = [c[1] for c in cluster]
                gap = min(c[2] for c in cluster)
                cy, cx = float(np.mean(rows)), float(np.mean(cols))
                if gap < MIN_OPENING_BARRIER_PX:
                    continue
                oid = f"RTO-{n:04d}"
                oids.append(oid)
                openings.append(CandidateOpening(
                    opening_id=oid, region_a=key[0], region_b=key[1],
                    centroid_px=(int(cx), int(cy)),
                    centroid_mm=frame.to_vector((cx + 0.5) * px,
                                                (cy + 0.5) * px),
                    barrier_thickness_px=int(gap),
                    approximate_width_mm=len(cluster) * px,
                    pixel_count=len(cluster),
                    why=("the barrier between these two regions is only "
                         f"{gap} px thick across {len(cluster)} px of "
                         "contact, which is what a doorway looks like in "
                         "the render — and also what an unclosed wall "
                         "junction looks like, so it is a CANDIDATE")))
        adjacencies.append(RegionAdjacency(
            region_a=key[0], region_b=key[1], contact_px=contact[key],
            min_barrier_px=int(thinnest.get(key, -1)),
            candidate_opening_ids=tuple(oids)))
    return adjacencies, openings


def _cluster(hits, *, reach: int = 8) -> list:
    """Group thin-contact pixels into ONE candidate per physical opening.

    Chaining each hit against the previously sorted one does not work: the
    same doorway is found once per scan row and once per scan column, and
    sorted order jumps between them, so a single door came out as hundreds
    of candidates. This is a real spatial clustering — pixels within `reach`
    of each other in both axes belong to one opening — done by bucketing
    into cells of side `reach` and flood-filling neighbouring cells, so it
    stays linear in the number of hits.
    """
    # One entry per pixel, keeping the thinnest barrier seen there.
    best: dict = {}
    for row, col, gap in hits:
        key = (row, col)
        if gap < best.get(key, 10**9):
            best[key] = gap

    cells: dict = {}
    for (row, col) in best:
        cells.setdefault((row // reach, col // reach), []).append((row, col))

    seen, out = set(), []
    for cell in sorted(cells):
        if cell in seen:
            continue
        stack, group = [cell], []
        seen.add(cell)
        while stack:
            cy, cx = stack.pop()
            group.extend(cells.get((cy, cx), ()))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nxt = (cy + dy, cx + dx)
                    if nxt in cells and nxt not in seen:
                        seen.add(nxt)
                        stack.append(nxt)
        out.append([(r, c, best[(r, c)]) for r, c in sorted(group)])
    return out


def _soft_proposals(established, diagnostic) -> list:
    """What the diagnostic solid WOULD have added, had it been allowed to."""
    if diagnostic is None or getattr(diagnostic, "is_empty", True):
        return []
    extra = (diagnostic if established is None
             else diagnostic.difference(established))
    if extra.is_empty:
        return []
    parts = (list(extra.geoms) if hasattr(extra, "geoms") else [extra])
    out = []
    for i, part in enumerate(sorted(parts, key=lambda p: -p.area), 1):
        if part.area < 1e-6:
            continue
        out.append({
            "soft_barrier_id": f"RSB-{i:04d}",
            "source": BARRIER_DIAGNOSTIC_SOFT,
            "area_m2": round(part.area / 1e6, 4),
            "centroid_mm": [round(v, 1) for v in
                            (part.centroid.x, part.centroid.y)],
            "used_as_a_barrier": False,
            "why": ("diagnostic wall material. It is offered as a soft "
                    "proposal so a later stage can ask what separation it "
                    "would create, and it is NOT in the barrier mask: a "
                    "hypothesis may not manufacture a room"),
        })
    return out[:60]
