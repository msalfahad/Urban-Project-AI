"""E68 — where two rooms leaked into one component, and what is missing there.

The 738 m2 component holding 22 labelled rooms is the most valuable diagnostic
on the sheet, and treating all 851 m of unpaired stroke equally wastes it. A
leak map asks a much narrower question:

    AT THIS SPECIFIC PLACE, where two spaces are expected to be separate,
    WHAT IS ACTUALLY DRAWN?

Raster tells us WHERE to look — two segmentation regions that share a frontier
inside one free-space component are expected to be separate. Raster supplies
no millimetre of the answer. The answer comes from the vector geometry found
at that frontier, and the classes below distinguish a genuinely missing wall
from a wall that is present and merely unpaired, which are different repairs.

Ranked by what fixing each leak would UNLOCK, not by length. One separator
that splits a 22-room blob is worth more than fifty metres of stroke
elsewhere.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

# What is actually at the expected separation.
VALID_WALL_BAND_PRESENT = "VALID_WALL_BAND_PRESENT"
UNPAIRED_DOUBLE_FACE_WALL = "UNPAIRED_DOUBLE_FACE_WALL"
SINGLE_LINE_WALL_CANDIDATE = "SINGLE_LINE_WALL_CANDIDATE"
FRAGMENTED_WALL = "FRAGMENTED_WALL"
UNRESOLVED_PORTAL = "UNRESOLVED_PORTAL"
OPEN_PLAN_TRANSITION = "OPEN_PLAN_TRANSITION"
NO_VECTOR_SEPARATOR = "NO_VECTOR_SEPARATOR"
RASTER_SEGMENTATION_ERROR = "RASTER_SEGMENTATION_ERROR"
LEAK_UNRESOLVED = "UNRESOLVED"

LEAK_CAUSES = (VALID_WALL_BAND_PRESENT, UNPAIRED_DOUBLE_FACE_WALL,
               SINGLE_LINE_WALL_CANDIDATE, FRAGMENTED_WALL,
               UNRESOLVED_PORTAL, OPEN_PLAN_TRANSITION, NO_VECTOR_SEPARATOR,
               RASTER_SEGMENTATION_ERROR, LEAK_UNRESOLVED)

# Which instrument located a separation. They answer different questions:
# see build() for why only one of them is complete.
LOCALISER_NECK = "FREE_SPACE_NECK"
LOCALISER_FRONTIER = "RASTER_REGION_FRONTIER"

# Causes whose repair is in the wall extractor rather than anywhere else.
EXTRACTOR_CAUSES = (UNPAIRED_DOUBLE_FACE_WALL, SINGLE_LINE_WALL_CANDIDATE,
                    FRAGMENTED_WALL)

# How far PERPENDICULAR to the frontier a vector mark still counts as being
# AT it. This is the only direction a tolerance belongs in: along the frontier
# the mark's own drawn interval decides, which is why coverage below is an
# interval union and not a point probe.
FRONTIER_REACH_MM = 300.0
# Two raster room regions never touch: a wall's worth of pixels lies between
# them. So each region is grown by about one wall thickness before looking for
# a shared frontier. This is a SEARCH RADIUS for localisation and carries no
# measurement — a one-pixel dilation found zero frontiers on AR-00 for exactly
# this reason.
FRONTIER_SEARCH_MM = 260.0
# A frontier shorter than this is two regions touching at a corner, not a
# shared wall line.
MIN_FRONTIER_MM = 400.0
# Free space leaked from A to B, so SOMEWHERE along the frontier there is a
# gap in the accepted wall material. That gap is the aperture, and it — not
# the frontier's midpoint — is the place whose vector content answers the
# question. Below this width a gap is junction slop between two abutting
# bands, not a hole free space came through.
MIN_APERTURE_MM = 50.0
# Two spaces are a CANDIDATE SEPARATION only if what lies between them is
# about a wall thick. If the measured window is far wider, something else
# stands between them — another room, a shaft, a stair — and the pair shares
# no wall to be missing. The ceiling is taken from the drawing's own thickest
# accepted wall rather than from a constant, and this factor is the margin
# allowed above it for the segmentation boundary stopping short of the wall
# face. On AR-00 the adjacent pairs measure 238-411 mm against a 440.6 mm
# thickest wall and the non-adjacent ones 811-3190 mm, so the two populations
# are a clear factor of two apart and the margin is not load-bearing.
ADJACENCY_MARGIN_FACTOR = 1.5


@dataclass(frozen=True)
class Leak:
    """One expected separation that did not happen, and why."""

    leak_id: str
    # Which instrument located this separation, because they answer
    # different questions and only one of them is complete.
    localiser: str = LOCALISER_NECK
    passage_width_mm: float = 0.0
    channel_located: bool = True
    extent_established: bool = True
    passage_width_measured: bool = False
    labels_a: tuple[str, ...] = ()
    labels_b: tuple[str, ...] = ()
    space_geometry_id: str = ""
    space_a: str = ""
    space_b: str = ""
    frontier_mm: tuple | None = None
    frontier_length_mm: float = 0.0
    frontier_axis: str = ""
    frontier_fixed_mm: float | None = None
    # The measured extent ACROSS the frontier of whatever separates the two
    # spaces, and whether it was measured at all (a fully open transition has
    # no gap to measure, and falls back to the touch band).
    frontier_window_mm: tuple | None = None
    window_is_measured: bool = False
    frontier_along_mm: tuple | None = None
    # A frontier need not be one continuous run: an L-shaped pair of rooms
    # faces itself in several stretches, and the gaps between them are not
    # frontier at all.
    frontier_runs: int = 1
    frontier_support_mm: tuple = ()
    cause: str = LEAK_UNRESOLVED
    # Anywhere along the frontier's interval — not at one probe point.
    bands_at_frontier: tuple[str, ...] = ()
    unpaired_strokes_at_frontier: tuple[str, ...] = ()
    unpaired_classes: tuple[str, ...] = ()
    portals_at_frontier: tuple[str, ...] = ()
    # How much of the frontier each population actually covers.
    band_coverage_mm: float = 0.0
    wall_like_stroke_coverage_mm: float = 0.0
    # The widest stretch with no accepted wall material: the hole itself.
    aperture_mm: tuple | None = None
    aperture_length_mm: float = 0.0
    apertures: int = 0
    hairline_junction_gap: bool = False
    strokes_at_aperture: tuple[str, ...] = ()
    aperture_stroke_classes: tuple[str, ...] = ()
    portals_at_aperture: tuple[str, ...] = ()
    rooms_separated: int = 2
    controls_unlocked: tuple[str, ...] = ()
    why: str = ""

    @property
    def repair_is_in_the_extractor(self) -> bool:
        return (self.cause in EXTRACTOR_CAUSES
                or self.hairline_junction_gap)

    @property
    def is_an_open_aperture(self) -> bool:
        """Did free space actually have somewhere to cross here?

        Enumerating every label pair inside a merged component asks about
        separations that are already walled as well as ones that are not.
        Only an open aperture can have carried the leak, so only an open
        aperture is a repair; a walled frontier is evidence that this
        particular pair did NOT merge here.
        """
        return self.aperture_mm is not None

    @property
    def band_coverage_fraction(self) -> float:
        """Share of the frontier already carrying accepted wall material."""
        if self.frontier_length_mm <= 0.0:
            return 0.0
        return self.band_coverage_mm / self.frontier_length_mm

    def record(self) -> dict:
        return {"leak_id": self.leak_id,
                "localiser": self.localiser,
                "space_geometry_id": self.space_geometry_id,
                "between": [self.space_a, self.space_b],
                "labels_a": list(self.labels_a),
                "labels_b": list(self.labels_b),
                "passage_width_mm": round(self.passage_width_mm, 1),
                "channel_located": self.channel_located,
                "extent_established": self.extent_established,
                "frontier_axis": self.frontier_axis,
                "frontier_at_mm": (None if self.frontier_mm is None
                                   else [round(v, 1) for v in
                                         self.frontier_mm]),
                "frontier_length_mm": round(self.frontier_length_mm, 1),
                "frontier_fixed_mm": (None if self.frontier_fixed_mm is None
                                      else round(self.frontier_fixed_mm, 1)),
                "frontier_window_mm": (None if self.frontier_window_mm is None
                                       else [round(v, 1) for v in
                                             self.frontier_window_mm]),
                "window_is_measured": self.window_is_measured,
                "frontier_along_mm": (None if self.frontier_along_mm is None
                                      else [round(v, 1) for v in
                                            self.frontier_along_mm]),
                "frontier_runs": self.frontier_runs,
                "frontier_support_mm": [[round(s, 1), round(e, 1)]
                                        for s, e in self.frontier_support_mm],
                "cause": self.cause,
                "bands_at_frontier": list(self.bands_at_frontier),
                "unpaired_strokes_at_frontier": list(
                    self.unpaired_strokes_at_frontier),
                "unpaired_classes": list(self.unpaired_classes),
                "portals_at_frontier": list(self.portals_at_frontier),
                "band_coverage_mm": round(self.band_coverage_mm, 1),
                "band_coverage_fraction": round(
                    self.band_coverage_fraction, 3),
                "wall_like_stroke_coverage_mm": round(
                    self.wall_like_stroke_coverage_mm, 1),
                "aperture_mm": (None if self.aperture_mm is None
                                else [round(v, 1) for v in self.aperture_mm]),
                "aperture_length_mm": round(self.aperture_length_mm, 1),
                "apertures": self.apertures,
                "hairline_junction_gap": self.hairline_junction_gap,
                "strokes_at_aperture": list(self.strokes_at_aperture),
                "aperture_stroke_classes": list(self.aperture_stroke_classes),
                "portals_at_aperture": list(self.portals_at_aperture),
                "rooms_separated": self.rooms_separated,
                "frozen_controls_unlocked": list(self.controls_unlocked),
                "is_an_open_aperture": self.is_an_open_aperture,
                "repair_is_in_the_extractor":
                    self.repair_is_in_the_extractor,
                "why": self.why}


def frontiers(labels, region_of, *, px_mm: float, to_vector,
              min_length: float = MIN_FRONTIER_MM,
              search_mm: float = FRONTIER_SEARCH_MM,
              max_separation_mm: float | None = None) -> list:
    """Where two segmentation regions touch. RASTER LOCALISES ONLY.

    `region_of(space_id)` returns a boolean mask. Two raster room regions
    never touch — a wall's worth of pixels lies between them — so A is grown
    by about one wall thickness before looking for B. That dilation is a
    search radius and carries no measurement.

    A frontier is returned as an INTERVAL, not a point: its fixed coordinate
    (the line the two spaces divide along) and the along-axis stretch over
    which they face each other. A 6.8 m frontier probed at its midpoint
    misses every wall that runs along its other six metres, which is exactly
    how a drawing with walls present reports NO_VECTOR_SEPARATOR.

    The axis, the fixed coordinate and the extent are all computed in VECTOR
    millimetres, after `to_vector`, so a frame transform that swaps the axes
    cannot silently transpose the result.
    """
    import numpy as np
    out = []
    follows = _axis_map(to_vector)
    radius = max(1, int(round(search_mm / px_mm)))
    grown_cache: dict = {}

    def grown_of(space_id):
        if space_id not in grown_cache:
            m = region_of(space_id)
            grown_cache[space_id] = (None if m is None
                                     else _grow(m, radius))
        return grown_cache[space_id]

    for i, a in enumerate(labels):
        ma = region_of(a)
        ga = grown_of(a)
        if ma is None or ga is None:
            continue
        for b in labels[i + 1:]:
            mb = region_of(b)
            gb = grown_of(b)
            if mb is None or gb is None:
                continue
            touch = ga & mb
            if not touch.any():
                continue
            ys, xs = np.nonzero(touch)
            t_box = _box_of(xs, ys, px_mm=px_mm, to_vector=to_vector)

            # The frontier runs along whichever vector axis the touch band is
            # longer in. The OTHER axis gives the line they divide along.
            axis = ("H" if (t_box[1] - t_box[0]) >= (t_box[3] - t_box[2])
                    else "V")
            along_is_pixel_x = ((follows == "x") if axis == "H"
                                else (follows == "y"))

            # `touch` IS the set of places where A (within the search radius)
            # meets B, so its support along the frontier axis is exactly the
            # stretch over which the two spaces face each other. A bounding
            # box would instead span the gaps of an L-shaped room and invent
            # facing length that does not exist.
            present = (touch.any(axis=0) if along_is_pixel_x
                       else touch.any(axis=1))
            support = _union(_runs_to_mm(present, axis,
                                         along_is_pixel_x=along_is_pixel_x,
                                         px_mm=px_mm, to_vector=to_vector))
            if _measure(support) < min_length:
                continue

            # WHERE the dividing line is cannot be read off the touch band:
            # the dilation is one-sided, so the touch band's centre sits
            # inside B, and a segmentation region stops well short of the
            # wall face it abuts. What actually lies between the two spaces
            # is the gap — grown A meets grown B, in neither region — and its
            # perpendicular extent is a MEASURED window, not a tolerance
            # around a biased point.
            gap = ga & gb & ~ma & ~mb
            gap &= (present[None, :] if along_is_pixel_x
                    else present[:, None])
            window = _perp_window(gap if gap.any() else touch, axis,
                                  px_mm=px_mm, to_vector=to_vector)
            measured = bool(gap.any())

            separation = window[1] - window[0]
            adjacent = (max_separation_mm is None
                        or separation <= max_separation_mm)

            cx, cy = to_vector(float(xs.mean()) * px_mm,
                               float(ys.mean()) * px_mm)
            out.append({"space_a": a, "space_b": b, "axis": axis,
                        "centre_mm": (cx, cy),
                        "fixed_mm": 0.5 * (window[0] + window[1]),
                        "window_mm": window,
                        "separation_mm": separation,
                        "adjacent": adjacent,
                        "window_is_measured": measured,
                        "support_mm": support,
                        "along_mm": (support[0][0], support[-1][1]),
                        "length_mm": _measure(support)})
    return out


def _perp_window(mask, axis: str, *, px_mm: float, to_vector) -> tuple:
    """Vector-mm extent ACROSS the frontier of whatever separates the pair."""
    import numpy as np
    ys, xs = np.nonzero(mask)
    box = _box_of(xs, ys, px_mm=px_mm, to_vector=to_vector)
    return (box[2], box[3]) if axis == "H" else (box[0], box[1])


def _axis_map(to_vector) -> str:
    """Which PIXEL axis vector-x follows: "x" or "y".

    The frame transform may swap the axes (AR-00's is SWAP_FLIP_Y), so this
    is measured from the transform rather than assumed. Everything else in
    this module then works in vector millimetres only.
    """
    x0, y0 = to_vector(0.0, 0.0)
    xx, _ = to_vector(1000.0, 0.0)
    xy, _ = to_vector(0.0, 1000.0)
    return "x" if abs(xx - x0) >= abs(xy - x0) else "y"


def _runs_to_mm(present, axis: str, *, along_is_pixel_x: bool, px_mm: float,
                to_vector) -> list:
    """Vector-mm runs along `axis` for a boolean per-index presence array."""
    import numpy as np
    idx = np.nonzero(present)[0]
    if idx.size == 0:
        return []
    breaks = np.nonzero(np.diff(idx) > 1)[0]
    starts = np.concatenate(([0], breaks + 1))
    ends = np.concatenate((breaks, [idx.size - 1]))
    runs = []
    for s, e in zip(starts, ends):
        p0 = float(idx[s]) * px_mm
        p1 = float(idx[e] + 1) * px_mm
        if along_is_pixel_x:
            v0, v1 = to_vector(p0, 0.0), to_vector(p1, 0.0)
        else:
            v0, v1 = to_vector(0.0, p0), to_vector(0.0, p1)
        k = 0 if axis == "H" else 1
        runs.append((min(v0[k], v1[k]), max(v0[k], v1[k])))
    return runs


def _box_of(xs, ys, *, px_mm: float, to_vector) -> tuple:
    """Vector-mm (x0, x1, y0, y1) of a set of pixel indices.

    The frame transform is axis-aligned, so transforming the four pixel-box
    corners gives the vector box; taking min/max afterwards survives a swap
    or a flip without the caller having to know which happened.
    """
    x0, x1 = float(xs.min()) * px_mm, float(xs.max() + 1) * px_mm
    y0, y1 = float(ys.min()) * px_mm, float(ys.max() + 1) * px_mm
    pts = [to_vector(x, y) for x in (x0, x1) for y in (y0, y1)]
    vx = [p[0] for p in pts]
    vy = [p[1] for p in pts]
    return (min(vx), max(vx), min(vy), max(vy))


def _clip(spans, lo: float, hi: float) -> list:
    """Every span, oriented and cut to [lo, hi]. Zero-width spans dropped."""
    out = []
    for a, b in spans:
        a, b = (a, b) if a <= b else (b, a)
        s, e = max(a, lo), min(b, hi)
        if e > s:
            out.append((s, e))
    return out


def _union(spans) -> list:
    """Merged, sorted, disjoint intervals. Coverage is a union, not a sum."""
    if not spans:
        return []
    merged = [list(s) for s in sorted(spans)[:1]]
    for s, e in sorted(spans)[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]


def _measure(spans) -> float:
    return sum(e - s for s, e in spans)


def _gaps(spans, lo: float, hi: float) -> list:
    """What [lo, hi] is NOT covered by `spans` (which must be a union)."""
    out, cur = [], lo
    for s, e in spans:
        if s > cur:
            out.append((cur, s))
        cur = max(cur, e)
    if cur < hi:
        out.append((cur, hi))
    return out


def _subtract(a_runs, b_runs) -> list:
    """What `a_runs` covers and `b_runs` does not."""
    out = []
    for lo, hi in a_runs:
        out.extend(_gaps(_union(_clip(b_runs, lo, hi)), lo, hi))
    return out


def _overlaps(span, lo: float, hi: float) -> bool:
    a, b = (span[0], span[1]) if span[0] <= span[1] else (span[1], span[0])
    return a < hi and b > lo


def _grow(mask, radius: int):
    """Dilate a boolean mask by `radius` pixels, four-connected.

    Written out rather than imported: this is a search radius over a boolean
    array, not a geometry operation, and GEOS is not in this path.
    """
    out = mask.copy()
    for _ in range(radius):
        nxt = out.copy()
        nxt[1:, :] |= out[:-1, :]
        nxt[:-1, :] |= out[1:, :]
        nxt[:, 1:] |= out[:, :-1]
        nxt[:, :-1] |= out[:, 1:]
        out = nxt
    return out


def build(candidates, labels_inside, *, region_of, px_mm, to_vector,
          bands, strokes, portals, controls=(),
          max_wall_thickness_mm: float | None = None, seeds=None) -> tuple:
    """Every located separation inside each multi-label component, classed.

    TWO localisers, because one of them is provably incomplete on its own:

    FREE_SPACE_NECK is primary. It erodes the merged polygon and reports the
    passage each split reveals. It is complete by construction — every label
    ends up on one side of some split — and its width is a measurement of the
    opening rather than an inference about it.

    RASTER_REGION_FRONTIER is the cross-check. It finds places two rooms face
    each other, which is a narrower question: free space also leaks AROUND
    structure. On AR-00 it localised 8 open apertures inside the 22-label
    component, and 8 apertures cannot join 22 rooms, so it cannot be trusted
    alone. It remains valuable because it reads coverage along a real shared
    wall line, which is where a PARTLY missing wall shows up.

    At each located separation the raw vector geometry is read over the whole
    interval: which bands, strokes and portals run along it, how much of it
    accepted wall material covers, and what lies in the stretch that material
    leaves open. That open stretch is where free space crossed, so it is the
    stretch whose vector content names the cause.
    """
    out, n = [], 0
    control_set = set(controls)
    ceiling = (None if not max_wall_thickness_mm
               else max_wall_thickness_mm * ADJACENCY_MARGIN_FACTOR)
    audit: dict = {"components_with_two_or_more_labels": 0,
                   "necks_found": 0,
                   "necks_located": 0,
                   "labels_frozen_before_their_split": 0,
                   "shallow_seeds": [],
                   "frontiers_found": 0,
                   "not_a_candidate_separation": 0,
                   "separation_ceiling_mm": (None if ceiling is None
                                             else round(ceiling, 1)),
                   "thickest_accepted_wall_mm": (
                       None if not max_wall_thickness_mm
                       else round(max_wall_thickness_mm, 1)),
                   "rejected_separations_mm": [],
                   "windows_measured": 0,
                   "windows_fallen_back": 0,
                   "partition_complete": {}}

    for c in candidates:
        ids = tuple(labels_inside.get(c.space_geometry_id, ()))
        if len(ids) < 2:
            continue
        audit["components_with_two_or_more_labels"] += 1

        # --- primary: necks in the merged polygon itself ----------------
        if seeds:
            here = {i: seeds[i] for i in ids if i in seeds}
            found, diag = necks(c.geometry, here)
            audit["necks_found"] += len(found)
            audit["necks_located"] += sum(
                1 for f in found if f["channel_located"])
            audit["labels_frozen_before_their_split"] += len(
                diag["frozen_at_mm"])
            audit["shallow_seeds"].extend(
                {"space_id": k, "deepest_free_space_mm": v}
                for k, v in sorted(diag["seed_depth_mm"].items())
                if v < SEED_MIN_DEPTH_MM)
            audit["partition_complete"][c.space_geometry_id] = (
                _partition_check(ids, found))
            for f in found:
                n += 1
                out.append(_leak_at(f, LOCALISER_NECK, f"LK-{n:04d}",
                                    c.space_geometry_id, len(ids),
                                    control_set, bands, strokes, portals))

        # --- cross-check: where two raster regions face each other ------
        for fr in frontiers(list(ids), region_of, px_mm=px_mm,
                            to_vector=to_vector,
                            max_separation_mm=ceiling):
            audit["frontiers_found"] += 1
            if fr["window_is_measured"]:
                audit["windows_measured"] += 1
            else:
                audit["windows_fallen_back"] += 1
            if not fr["adjacent"]:
                # Not a candidate separation: these two spaces are further
                # apart than any wall in this drawing is thick, so there is
                # no shared wall here that could be missing.
                audit["not_a_candidate_separation"] += 1
                audit["rejected_separations_mm"].append(
                    {"between": [fr["space_a"], fr["space_b"]],
                     "separation_mm": round(fr["separation_mm"], 1)})
                continue
            n += 1
            out.append(_leak_at(fr, LOCALISER_FRONTIER, f"LK-{n:04d}",
                                c.space_geometry_id, len(ids), control_set,
                                bands, strokes, portals))

    audit["candidate_separations"] = n
    audit["rejected_separations_mm"] = sorted(
        audit["rejected_separations_mm"],
        key=lambda r: -r["separation_mm"])[:20]
    return out, audit


def _partition_check(ids, found) -> dict:
    """Do the reported necks account for every label in the component?

    A component holding N labels can only have been merged through at least
    N-1 passages. If the necks reported do not separate every label from
    every other, the leak map is INCOMPLETE and must say so rather than
    present its findings as the explanation.
    """
    par = {i: i for i in ids}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for f in found:
        for grp in (f["labels_a"], f["labels_b"]):
            root = find(grp[0])
            for s in grp[1:]:
                par[find(s)] = root
    # Every label the necks touched should be reachable; a label in no neck
    # at all was never separated from anything.
    touched = {s for f in found for grp in (f["labels_a"], f["labels_b"])
               for s in grp}
    singles = sorted(set(ids) - touched)
    return {"labels": len(ids),
            "passages_needed_at_least": max(0, len(ids) - 1),
            "passages_reported": len(found),
            "labels_never_separated": singles,
            "complete": not singles and len(found) >= len(ids) - 1}


def _leak_at(fr, localiser: str, leak_id: str, sg_id: str, rooms: int,
             control_set, bands, strokes, portals) -> "Leak":
    """Read the raw vector geometry at one located separation and class it."""
    from engine.unpaired_strokes import WALL_LIKE_CLASSES
    if not fr.get("extent_established", True):
        # The erosion that revealed this passage also removed most of the
        # plan, so the channel joining the two sides could not be isolated.
        # The PASSAGE WIDTH is still a measurement, but there is no located
        # stretch of drawing to read, and reading the bounding box of half
        # the floor would return every band on the sheet. Refuse instead.
        return Leak(
            leak_id=leak_id, localiser=localiser,
            passage_width_mm=fr.get("passage_width_mm", 0.0),
            channel_located=bool(fr.get("channel_located", False)),
            extent_established=False,
            passage_width_measured=True,
            labels_a=tuple(fr.get("labels_a", ())),
            labels_b=tuple(fr.get("labels_b", ())),
            space_geometry_id=sg_id,
            space_a=fr["space_a"], space_b=fr["space_b"],
            frontier_mm=fr["centre_mm"], frontier_axis=fr["axis"],
            rooms_separated=rooms, cause=LEAK_UNRESOLVED,
            controls_unlocked=tuple(sorted(
                control_set & set(fr.get("labels_a", ()))
                | control_set & set(fr.get("labels_b", ())))),
            why=(f"free space passes between these spaces through a "
                 f"{fr.get('passage_width_mm', 0.0):.0f} mm passage, and "
                 "that width IS measured"
                 + (" and its crossing point located"
                    if fr.get("channel_located") else "")
                 + ". But at this erosion radius most of the floor is "
                 "thinner than the erosion, so the passage has no bounded "
                 "extent, and reading the drawing over an unbounded extent "
                 "would return every band on the sheet and look like a "
                 "confident answer. A passage this wide is usually an "
                 "open-plan transition rather than a missing wall; the "
                 "narrow passages are where the repairs are"))
    cx, cy = fr["centre_mm"]
    axis = fr["axis"]
    at = fr["fixed_mm"]
    support = fr["support_mm"]
    lo, hi = fr["along_mm"]
    # A mark is AT this frontier if it lies in the measured window
    # between the two spaces. FRONTIER_REACH_MM is slop on a measured
    # window, not a guess at how far a wall might be: the raster
    # region boundary stops short of the wall face by an unknown
    # amount, which is exactly why the window is measured.
    w_lo = fr["window_mm"][0] - FRONTIER_REACH_MM
    w_hi = fr["window_mm"][1] + FRONTIER_REACH_MM

    def _near(items, fixed_of, span_of):
        return [it for it in items
                if getattr(it, "axis", "") == axis
                and w_lo <= fixed_of(it) <= w_hi
                and any(_overlaps(span_of(it), s, e)
                        for s, e in support)]

    near_bands = _near(bands, lambda b: b.centreline_mm,
                       lambda b: (b.start_mm, b.end_mm))
    near_strokes = _near(strokes, lambda s: s.fixed_mm,
                         lambda s: (s.start_mm, s.end_mm))
    near_portals = _near(portals, lambda q: q.fixed_mm,
                         lambda q: (q.start_mm, q.end_mm))

    # Coverage is measured over the facing support only. A band that
    # runs past the end of the frontier does not earn coverage for
    # length where the two spaces never faced each other.
    band_cov = _union([sp for s, e in support for sp in _clip(
        [(b.start_mm, b.end_mm) for b in near_bands], s, e)])
    wall_like_cov = _union([sp for s, e in support for sp in _clip(
        [(x.start_mm, x.end_mm) for x in near_strokes
         if x.stroke_class in WALL_LIKE_CLASSES], s, e)])

    # The aperture: the widest stretch where the two spaces face each
    # other with no accepted wall material between them.
    open_runs = [g for g in _subtract(support, band_cov)
                 if g[1] - g[0] >= MIN_APERTURE_MM]
    aperture = (max(open_runs, key=lambda g: g[1] - g[0])
                if open_runs else None)
    ap_len = 0.0 if aperture is None else aperture[1] - aperture[0]

    if aperture is None:
        strokes_ap, portals_ap = [], []
    else:
        a_lo, a_hi = aperture
        strokes_ap = [s for s in near_strokes
                      if _overlaps((s.start_mm, s.end_mm), a_lo, a_hi)]
        portals_ap = [q for q in near_portals
                      if _overlaps((q.start_mm, q.end_mm), a_lo, a_hi)]

    # A passage the erosion LOCATED, with accepted wall material along its
    # whole length, is not a missing wall at all: the walls are there and the
    # free space squeezed between them. That is a gap where two wall polygons
    # fail to meet, and it is repaired in the extractor, not in the source.
    junction = (localiser == LOCALISER_NECK and aperture is None
                and _measure(band_cov) > 0.0)

    cause, why = _cause(
        length=fr["length_mm"], bands=near_bands, band_cov=band_cov,
        aperture=aperture, strokes_at_aperture=strokes_ap,
        portals_at_aperture=portals_ap,
        strokes_on_frontier=near_strokes,
        junction_gap_mm=(fr.get("passage_width_mm", 0.0)
                         if junction else None))

    return Leak(
        leak_id=leak_id, localiser=localiser,
        passage_width_mm=fr.get("passage_width_mm", 0.0),
        channel_located=bool(fr.get("channel_located", True)),
        extent_established=bool(fr.get("extent_established", True)),
        labels_a=tuple(fr.get("labels_a", (fr["space_a"],))),
        labels_b=tuple(fr.get("labels_b", (fr["space_b"],))),
        space_geometry_id=sg_id,
        space_a=fr["space_a"], space_b=fr["space_b"],
        frontier_mm=(cx, cy), frontier_length_mm=fr["length_mm"],
        frontier_axis=axis, frontier_fixed_mm=at,
        frontier_window_mm=fr["window_mm"],
        window_is_measured=fr["window_is_measured"],
        frontier_along_mm=(lo, hi), frontier_runs=len(support),
        frontier_support_mm=tuple(support),
        cause=cause,
        bands_at_frontier=tuple(sorted(
            b.wall_band_id for b in near_bands)),
        unpaired_strokes_at_frontier=tuple(
            s.stroke_id for s in near_strokes),
        unpaired_classes=tuple(sorted(
            {s.stroke_class for s in near_strokes})),
        portals_at_frontier=tuple(sorted(
            q.portal_id for q in near_portals)),
        band_coverage_mm=_measure(band_cov),
        wall_like_stroke_coverage_mm=_measure(wall_like_cov),
        aperture_mm=aperture, aperture_length_mm=ap_len,
        apertures=len(open_runs), hairline_junction_gap=junction,
        strokes_at_aperture=tuple(s.stroke_id for s in strokes_ap),
        aperture_stroke_classes=tuple(sorted(
            {s.stroke_class for s in strokes_ap})),
        portals_at_aperture=tuple(sorted(
            q.portal_id for q in portals_ap)),
        rooms_separated=rooms,
        controls_unlocked=tuple(sorted(
            control_set & set(fr.get("labels_a", (fr["space_a"],)))
            | control_set & set(fr.get("labels_b",
                                       (fr["space_b"],))))),
        why=why)


def _cause(*, length: float, bands, band_cov, aperture,
           strokes_at_aperture, portals_at_aperture,
           strokes_on_frontier,
           junction_gap_mm: float | None = None) -> tuple[str, str]:
    """What is drawn where the frontier is OPEN, read in order of decisiveness.

    The frontier as a whole is not the question. Free space crossed from one
    space to the other, so it crossed through the aperture, and only what is
    at the aperture can explain it. A band covering the frontier's other four
    metres is real material and is reported as such, but it did not cause
    this leak.
    """
    from engine.unpaired_strokes import (CONFIRMED_SINGLE_LINE_WALL,
                                         FRAGMENTED_MATE,
                                         DIFFERENT_WALL_REPRESENTATION)
    covered = _measure(band_cov)
    share = 0.0 if length <= 0.0 else covered / length

    if junction_gap_mm is not None:
        return VALID_WALL_BAND_PRESENT, (
            f"{len(bands)} accepted wall band(s) run along the whole "
            f"{length:.0f} mm of this passage, and free space still crossed "
            f"it through {junction_gap_mm:.0f} mm. Nothing is missing from "
            "the drawing here: two wall polygons fail to meet, and the wall "
            "solid has a hairline hole at their junction. The repair is in "
            "the extractor, not in the source")
    if aperture is None:
        return VALID_WALL_BAND_PRESENT, (
            f"{len(bands)} accepted wall band(s) cover all {covered:.0f} mm "
            f"of this {length:.0f} mm frontier, leaving no gap wider than "
            f"{MIN_APERTURE_MM:.0f} mm. The wall IS in the solid here, so "
            "these two spaces did not merge across this frontier — they meet "
            "somewhere else, or the segmentation split one space in two")

    a_lo, a_hi = aperture
    ap = a_hi - a_lo
    where = (f"{ap:.0f} mm of this {length:.0f} mm frontier is open "
             f"({share * 100:.0f}% already walled), between {a_lo:.0f} and "
             f"{a_hi:.0f} mm")
    classes = {s.stroke_class for s in strokes_at_aperture}

    if portals_at_aperture:
        return UNRESOLVED_PORTAL, (
            f"{where}, and {len(portals_at_aperture)} portal candidate(s) "
            "sit in the opening. If one is genuinely a doorway its barrier "
            "would close the leak; if it is not, the wall behind it was "
            "never extracted")
    if CONFIRMED_SINGLE_LINE_WALL in classes:
        return SINGLE_LINE_WALL_CANDIDATE, (
            f"{where}, and a lone wall-pen run with raster support and no "
            "mate lies in the opening. The wall IS drawn; the band engine "
            "cannot express a single-line wall, so it never became material")
    if FRAGMENTED_MATE in classes:
        return FRAGMENTED_WALL, (
            f"{where}, and wall-pen fragments near an accepted band's face "
            "lie in the opening: the wall is partly recovered and its mate "
            "is broken into pieces too short to pair")
    if DIFFERENT_WALL_REPRESENTATION in classes:
        return UNPAIRED_DOUBLE_FACE_WALL, (
            f"{where}, and wall-pen geometry drawn in a form the band engine "
            "does not read lies in the opening")
    if classes:
        return UNPAIRED_DOUBLE_FACE_WALL, (
            f"{where}, and {len(strokes_at_aperture)} unpaired wall-pen "
            f"stroke(s) classified {sorted(classes)} lie in it. Something is "
            "drawn here that did not become a band")
    if bands or strokes_on_frontier:
        return NO_VECTOR_SEPARATOR, (
            f"{where}, and NOTHING is drawn in the opening — though "
            f"{len(bands)} band(s) and {len(strokes_on_frontier)} stroke(s) "
            "run along other parts of the same frontier. The separator stops "
            "short of the opening: either the drawing leaves a genuine "
            "transition here, or a stretch of wall is missing from the source")
    return NO_VECTOR_SEPARATOR, (
        f"{length:.0f} mm of frontier with NO vector mark anywhere along it. "
        "Either the drawing genuinely has no separator here (an open "
        "transition), or the segmentation split two halves of one space")


def summary(leaks, *, candidates=(), audit=None) -> dict:
    """Ranked by what fixing it unlocks. Length is not the ranking."""
    by_component: dict = {}
    for lk in leaks:
        by_component.setdefault(lk.space_geometry_id, []).append(lk)
    # An already-walled separation can never outrank an open one: it is not
    # a repair at all.
    ranked = sorted(
        leaks,
        key=lambda lk: (not lk.is_an_open_aperture,
                        -len(lk.controls_unlocked), -lk.rooms_separated,
                        -lk.aperture_length_mm, -lk.frontier_length_mm))
    open_ap = [lk for lk in leaks if lk.is_an_open_aperture]
    walled = [lk for lk in leaks if lk.band_coverage_mm > 0.0]
    bare = [lk for lk in leaks if lk.band_coverage_mm <= 0.0]
    return {
        "leaks": len(leaks),
        "by_cause": dict(Counter(lk.cause for lk in leaks)),
        "by_component": {k: len(v) for k, v in sorted(by_component.items())},
        "repairs_in_the_extractor": sum(
            1 for lk in leaks if lk.repair_is_in_the_extractor),
        "separations_examined": len(leaks),
        "by_localiser": dict(Counter(lk.localiser for lk in leaks)),
        "hairline_junction_gaps": [
            lk.record() for lk in sorted(
                (x for x in leaks if x.hairline_junction_gap),
                key=lambda x: x.passage_width_mm)],
        "passages_not_localised": sum(
            1 for lk in leaks if not lk.channel_located),
        "open_apertures": len(open_ap),
        "separations_already_walled": len(leaks) - len(open_ap),
        "what_a_hairline_junction_gap_means": (
            "the wall IS drawn and IS in the solid, and free space still "
            "crossed it: two wall polygons do not meet. Nothing is missing "
            "from the source, so no amount of better extraction of the "
            "DRAWING will close it — the repair is in how the wall solid is "
            "assembled. This is the opposite diagnosis from a missing "
            "separator and needs the opposite work"),
        "what_merged_the_components": (
            f"{len(open_ap)} open aperture(s) totalling "
            f"{sum(lk.aperture_length_mm for lk in open_ap) / 1000.0:.1f} m. "
            f"The other {len(leaks) - len(open_ap)} separation(s) examined "
            "are already fully walled: those pairs did not merge across the "
            "frontier they share, they each reach the component some other "
            "way. Repair the apertures, not the count of pairs"),
        "frontier_coverage": {
            "frontiers_partly_walled": len(walled),
            "frontiers_with_no_wall_material_anywhere": len(bare),
            "frontier_length_total_mm": round(
                sum(lk.frontier_length_mm for lk in leaks), 1),
            "accepted_band_coverage_total_mm": round(
                sum(lk.band_coverage_mm for lk in leaks), 1),
            "open_aperture_total_mm": round(
                sum(lk.aperture_length_mm for lk in leaks), 1),
            "why_this_is_reported": (
                "each frontier is probed over its whole interval and each "
                "cause is read at the widest stretch the accepted wall "
                "material leaves open. A frontier that is 80% walled is not "
                "a missing wall; it is a missing stretch of wall, and the "
                "two need different repairs")},
        "leaks_unlocking_a_frozen_control": [
            lk.record() for lk in ranked
            if lk.controls_unlocked and lk.is_an_open_aperture][:20],
        "top_ranked": [lk.record() for lk in ranked[:20]],
        "ranking": ("open aperture before already-walled, then frozen "
                    "controls unlocked, then rooms separated, then aperture "
                    "width. NOT by stroke length: one separator "
                    "that splits a 22-room component is worth more than "
                    "fifty metres of stroke elsewhere"),
        "raster_role": ("raster LOCALISED every frontier and supplied no "
                        "millimetre of any answer"),
        "pair_audit": dict(audit or {}),
    }


# ---------------------------------------------------------------------------
# Where the free space ACTUALLY crossed.
#
# Raster region adjacency answers a narrower question than the one that
# matters: it finds the places two rooms face each other. But free space does
# not only leak across a shared frontier — it also leaks AROUND structure,
# through a corridor, past the end of a wall that stops short. On AR-00 the
# face-to-face instrument localised 8 open apertures inside the 22-label
# component, and 8 apertures cannot join 22 rooms: a spanning tree needs 21
# edges. So the instrument was provably incomplete, and its incompleteness is
# not visible from its own output.
#
# The merged polygon itself knows where it crossed. A leak is a NECK: a place
# where the free space is only as wide as the opening that made it. Eroding
# the polygon and watching which rooms fall apart finds every one of them,
# and the radius at which a pair separates IS the half-width of the passage
# between them. No raster, no adjacency assumption.
# ---------------------------------------------------------------------------

NECK_STEP_MM = 25.0
# Nothing an opening can be is wider than this and still an opening rather
# than an absent wall; beyond it the two spaces are simply one space.
MAX_NECK_HALF_WIDTH_MM = 1200.0


def necks(geometry, seeds, *, step_mm: float = NECK_STEP_MM,
          max_half_width_mm: float = MAX_NECK_HALF_WIDTH_MM) -> tuple:
    """Every passage inside one free-space polygon, with its width.

    `seeds` maps a space label to a point inside the polygon. Erode by a
    growing radius and watch the polygon fall apart. Each time a piece
    splits, the channel that joined its halves was exactly this wide, and the
    labels on either side say which spaces it merged.

    The output is one record per SPLIT, not per label pair: a piece holding
    twenty labels that splits in two is one passage, not a hundred facts.

    A label whose seed erodes away before its piece splits can no longer be
    followed; it is reported as unresolved at that radius rather than
    silently attributed to one side.
    """
    live, depth = _interior_seeds(geometry, seeds, step_mm=step_mm)

    pieces = [geometry]
    at = {sid: 0 for sid in live}          # label -> index into `pieces`
    frozen: dict = {}                      # label -> radius it vanished at
    events: list = []
    r = step_mm
    while r <= max_half_width_mm:
        eroded = geometry.buffer(-r)
        kids = ([g for g in eroded.geoms]
                if eroded.geom_type.startswith("Multi")
                else ([eroded] if not eroded.is_empty else []))
        if not kids:
            break
        # Erosion is monotone, so every child lies inside exactly one parent.
        by_parent: dict = {}
        for k in kids:
            q = k.representative_point()
            for pi, parent in enumerate(pieces):
                if parent.covers(q):
                    by_parent.setdefault(pi, []).append(k)
                    break

        nxt_pieces, nxt_at = [], {}
        for pi, parent in enumerate(pieces):
            children = by_parent.get(pi, [])
            here = [sid for sid, idx in at.items()
                    if idx == pi and sid not in frozen]
            placed: dict = {}
            for sid in here:
                q = live[sid]
                hit = next((ci for ci, k in enumerate(children)
                            if k.covers(q)), None)
                if hit is None:
                    frozen[sid] = r
                else:
                    placed.setdefault(hit, []).append(sid)
            # A split is only a passage if labels ended up on both sides of
            # it; a child with no label is a piece of the same space.
            labelled = [ci for ci in placed if placed[ci]]
            if len(labelled) > 1:
                for ci in labelled[1:]:
                    others = [s for cj in labelled if cj != ci
                              for s in placed[cj]]
                    events.append(_neck_record(
                        tuple(sorted(placed[ci])), tuple(sorted(others)),
                        children[ci],
                        _union_of([children[cj] for cj in labelled
                                   if cj != ci]),
                        parent, eroded, r, step_mm=step_mm,
                        children_at_this_radius=len(labelled),
                        unresolved=tuple(sorted(
                            s for s in here if s in frozen))))
            for ci, k in enumerate(children):
                nxt_pieces.append(k)
                for sid in placed.get(ci, ()):
                    nxt_at[sid] = len(nxt_pieces) - 1
        if not nxt_pieces:
            break
        pieces, at = nxt_pieces, nxt_at
        if len(at) <= 1:
            break
        r += step_mm
    return events, {"frozen_at_mm": frozen, "seed_depth_mm": depth}


SEED_MIN_DEPTH_MM = 300.0
SEED_SEARCH_MM = 2500.0


def _interior_seeds(geometry, seeds, *, step_mm: float) -> tuple:
    """Put every label's seed somewhere the erosion will not eat first.

    A raster region's centroid can fall inside a wall — an L-shaped corridor
    has its centroid in the corner it wraps around — and snapping such a
    point to the polygon boundary is the worst possible place to stand: the
    first erosion step removes it, the label drops out of the partition, and
    the passage it was on is never reported. So each seed is moved to the
    deepest point of the free space near it, and how deep that is is
    reported, because a label with no deep interior anywhere is a fact about
    the drawing and not something to paper over.
    """
    from shapely import maximum_inscribed_circle
    from shapely.geometry import Point

    out, depth = {}, {}
    for sid, xy in seeds.items():
        q = Point(*xy)
        d = q.distance(geometry.boundary) if geometry.covers(q) else -1.0
        # Widen the search until the seed is deep enough to survive the
        # erosion: a seed in a narrow arm of an L needs to look beyond the
        # arm, and one search radius is not always enough.
        reach = SEED_SEARCH_MM
        while d < SEED_MIN_DEPTH_MM and reach <= SEED_SEARCH_MM * 8:
            near = geometry.intersection(q.buffer(reach))
            if near.geom_type.startswith("Multi"):
                near = max(near.geoms, key=lambda g: g.area, default=near)
            if near.geom_type == "Polygon" and near.area > 0.0:
                cand = Point(maximum_inscribed_circle(near).coords[0])
                cd = cand.distance(geometry.boundary)
                if geometry.covers(cand) and cd > max(d, 0.0):
                    q, d = cand, cd
            reach *= 2.0
        out[sid] = q
        depth[sid] = round(d, 1)
    return out, depth


def _cuts(prev, channel, piece_a, piece_b, step_mm: float) -> bool:
    """Does removing this channel actually separate the two sides?

    Without this the localisation is a guess that looks like an answer: a
    lens can land in the middle of a wall, or span half the floor, and still
    be reported as the place free space crossed. Cutting it out and checking
    that the two sides fall apart is the proof.
    """
    if channel.is_empty:
        return False
    rest = prev.difference(channel.buffer(step_mm))
    parts = ([g for g in rest.geoms] if rest.geom_type.startswith("Multi")
             else ([rest] if not rest.is_empty else []))
    qa, qb = piece_a.representative_point(), piece_b.representative_point()
    ia = next((i for i, g in enumerate(parts) if g.covers(qa)), None)
    ib = next((i for i, g in enumerate(parts) if g.covers(qb)), None)
    return ia is not None and ib is not None and ia != ib


def _union_of(geoms):
    from shapely.ops import unary_union
    return unary_union(list(geoms))


# A located channel whose own area is larger than this is not a passage: at
# that erosion radius most of the floor is thinner than the erosion, so the
# removed material is one connected sheet and its extent says nothing about
# where a wall is missing.
MAX_LOCATED_CHANNEL_M2 = 5.0


def _neck_record(labels_a, labels_b, piece_a, piece_b, prev, eroded,
                 r: float, *, step_mm: float,
                 children_at_this_radius: int = 2,
                 unresolved: tuple = ()) -> dict:
    """Locate the passage that just closed between two pieces.

    Two different things are wanted here and they need different geometry.

    WHERE it is: bring the two eroded pieces back into contact by growing
    each by half the distance between them. They meet in the middle of the
    channel however long it is, and clipping to the polygon keeps the result
    in real free space rather than inside a wall. Cutting that sliver out and
    checking the two sides fall apart PROVES it is the crossing.

    HOW LONG it is: the sliver is only as long as the cut. The passage's own
    extent is the connected piece of removed material it sits in — bounded
    when the rooms either side are wider than the erosion, and unbounded when
    they are not, which is exactly when the extent must not be claimed.

    Note what the WIDTH measures. A doorway is a channel as deep as the wall
    is thick and as long as the door is wide, and it is the DEPTH that the
    erosion closes first. So a 200 mm passage width is a wall's thickness,
    not a 200 mm door.
    """
    # Bring the two eroded pieces back into contact. Each is grown by half
    # the distance between them, so they meet in the middle of the channel —
    # however long that channel is — and clipping to the polygon keeps the
    # result inside real free space rather than inside a wall.
    d = piece_a.distance(piece_b)
    reach = d / 2.0 + step_mm
    channel = piece_a.buffer(reach).intersection(
        piece_b.buffer(reach)).intersection(prev)
    located = _cuts(prev, channel, piece_a, piece_b, step_mm)

    if not located:
        # Fall back to what the erosion actually removed, and take the piece
        # of it that touches both sides.
        thin = prev.difference(piece_a.union(piece_b).buffer(r))
        parts = ([g for g in thin.geoms]
                 if thin.geom_type.startswith("Multi")
                 else ([thin] if not thin.is_empty else []))
        joins = [g for g in parts
                 if g.intersects(piece_a.buffer(r + step_mm))
                 and g.intersects(piece_b.buffer(r + step_mm))]
        if joins:
            channel = _union_of(joins)
            located = _cuts(prev, channel, piece_a, piece_b, step_mm)
        if not located:
            channel = _union_of(joins) if joins else prev
    if channel.is_empty:
        channel, located = prev, False

    # The extent of the passage, as opposed to the point it was cut at.
    extent = False
    if located:
        thin = prev.difference(eroded.buffer(r))
        parts = ([g for g in thin.geoms]
                 if thin.geom_type.startswith("Multi")
                 else ([thin] if not thin.is_empty else []))
        touching = [g for g in parts if g.intersects(channel)]
        if touching:
            whole = _union_of(touching)
            if whole.area / 1e6 <= MAX_LOCATED_CHANNEL_M2:
                channel, extent = whole, True

    x0, y0, x1, y1 = channel.bounds
    w, h = x1 - x0, y1 - y0
    # The passage's long dimension runs ALONG the line a missing wall would
    # follow; the short one crosses it.
    axis = "H" if w >= h else "V"
    along = (x0, x1) if axis == "H" else (y0, y1)
    window = (y0, y1) if axis == "H" else (x0, x1)
    c = channel.representative_point()
    return {"labels_a": labels_a, "labels_b": labels_b,
            "space_a": labels_a[0], "space_b": labels_b[0],
            "axis": axis, "centre_mm": (c.x, c.y), "half_width_mm": r,
            "fixed_mm": 0.5 * (window[0] + window[1]),
            "window_is_measured": True, "adjacent": True,
            "separation_mm": window[1] - window[0],
            "passage_width_mm": 2.0 * r,
            "window_mm": window, "support_mm": [along],
            "along_mm": along, "length_mm": along[1] - along[0],
            "channel_area_m2": channel.area / 1e6,
            "channel_located": located,
            "extent_established": extent,
            "children_at_this_radius": children_at_this_radius,
            "labels_unresolved": unresolved}
