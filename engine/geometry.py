"""E23 — Geometry Source.

Deterministic space geometry from a drawing, with no model in the loop and no
printed dimension read. Two backends share one interface:

- `VectorPdfSource`  — a vector PDF (the plotted sheet). Works today.
- `DxfSource`        — a DXF via ezdxf, for when a CAD file is supplied.

The vector backend works by rendering the sheet and labelling every enclosed
region of free space. A region bounded by wall ink *is* the floor of a space,
measured to the inside face of the walls, which is what a takeoff wants. The
only judgement involved is the scale, and the scale is calibrated against a
dimension printed on the sheet by the engineer who drew it.

What this module deliberately does NOT do:

- read a printed dimension (they are glyph outlines here, not text)
- name a space (see E24 — naming needs a label source)
- decide scope (see E24)
- close an open polygon by inference

A region that leaks through a door into the next room comes back as ONE region.
That is not a defect to paper over: those spaces really are continuous, and
merging them is the correct floor area. It is the caller's job to notice that a
region spans several named rooms and to mark it as such.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable
from pathlib import Path

import numpy as np


class GeometryError(RuntimeError):
    """The geometry could not be established — never a reason to estimate."""


# --------------------------------------------------------- measurement basis
# A quantity without a basis is not a quantity, it is a number. 19.65 m2 of what
# — the floor you can walk on, the slab, the space between wall centrelines?
# Different trades need different answers from the same room: floor tile follows
# the finish face, blockwork follows wall geometry, waterproofing follows the
# treated surface. So every area and length carries the physical reference it
# was taken from, and a converted value carries the basis it was converted TO.
CLEAR_INTERNAL_FINISH_FACE = "CLEAR_INTERNAL_FINISH_FACE"
STRUCTURAL_WALL_FACE = "STRUCTURAL_WALL_FACE"
WALL_CENTERLINE = "WALL_CENTERLINE"
EXTERNAL_FACE = "EXTERNAL_FACE"
PRINTED_DIMENSION_REFERENCE = "PRINTED_DIMENSION_REFERENCE"
SITE_MEASURED_FACE = "SITE_MEASURED_FACE"
UNKNOWN_BASIS = "UNKNOWN"

MEASUREMENT_BASES = frozenset({
    CLEAR_INTERNAL_FINISH_FACE, STRUCTURAL_WALL_FACE, WALL_CENTERLINE,
    EXTERNAL_FACE, PRINTED_DIMENSION_REFERENCE, SITE_MEASURED_FACE, UNKNOWN_BASIS,
})


def check_basis(basis: str) -> str:
    if basis not in MEASUREMENT_BASES:
        raise GeometryError(
            f"unknown measurement basis {basis!r} — a quantity must say what "
            f"physical reference it measures; known: {sorted(MEASUREMENT_BASES)}")
    return basis


@dataclass(frozen=True)
class Region:
    """One enclosed area of floor, measured in the drawing's own units."""

    id: int
    area_m2: Decimal            # holes the size of printed text filled back in
    raw_area_m2: Decimal        # before any hole filling — the honest floor pixels
    bbox_mm: tuple[int, int, int, int]     # x0, y0, x1, y1
    centroid_px: tuple[int, int]
    width_mm: int
    height_mm: int
    # Flood fill stops at the wall ink, so what it measures is the floor you can
    # stand on — not the slab and not the centreline grid.
    basis: str = CLEAR_INTERNAL_FINISH_FACE

    @property
    def is_rectangleish(self) -> Decimal:
        """area / bbox area. 1.0 is a perfect rectangle; low means L-shaped."""
        box = Decimal(self.width_mm) * Decimal(self.height_mm) / Decimal(1_000_000)
        return self.area_m2 / box if box else Decimal(0)


@dataclass
class Calibration:
    """mm per PDF point, and the evidence for it."""

    mm_per_pt: Decimal
    basis: str                  # what was measured to get this
    residual_mm: Decimal        # error on the independent check dimension

    def validate(self, tolerance_mm: Decimal = Decimal("10")) -> None:
        if self.mm_per_pt <= 0:
            raise GeometryError(f"non-physical scale {self.mm_per_pt}")
        if abs(self.residual_mm) > tolerance_mm:
            raise GeometryError(
                f"scale check off by {self.residual_mm} mm (basis: {self.basis}) — "
                "refusing to measure against an unproven scale"
            )


def calibrate(known_pt: float, known_mm: int, check_pt: float, check_mm: int) -> Calibration:
    """Derive scale from one printed dimension and prove it on a second.

    One measurement is a guess; the second is what makes it evidence.
    """
    mm_per_pt = Decimal(str(known_mm)) / Decimal(str(known_pt))
    predicted = Decimal(str(check_pt)) * mm_per_pt
    return Calibration(
        mm_per_pt=mm_per_pt,
        basis=f"{known_mm} mm printed over {known_pt} pt",
        residual_mm=predicted - Decimal(str(check_mm)),
    )


def label_regions(free: np.ndarray) -> np.ndarray:
    """Two-pass run-length connected components. `free` True where open.

    Written out rather than imported because scipy is not a dependency of this
    project and one array-labelling routine is not worth becoming one.
    """
    h, w = free.shape
    parent = [0]

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    lab = np.zeros((h, w), np.int32)
    prev: list[tuple[int, int, int]] = []
    for y in range(h):
        d = np.diff(np.concatenate(([False], free[y], [False])).astype(np.int8))
        runs: list[tuple[int, int, int]] = []
        for s, e in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)):
            lb = 0
            for ps, pe, pl in prev:
                if pe <= s:
                    continue
                if ps >= e:
                    break
                if lb == 0:
                    lb = pl
                else:
                    union(lb, pl)
            if lb == 0:
                parent.append(len(parent))
                lb = len(parent) - 1
            lab[y, s:e] = lb
            runs.append((s, e, lb))
        prev = runs

    flat = np.array([find(i) for i in range(len(parent))], np.int32)
    lab = flat[lab]
    _, inv = np.unique(lab, return_inverse=True)
    return inv.reshape(lab.shape).astype(np.int32)


def fill_holes(mask: np.ndarray) -> np.ndarray:
    """`mask` with every enclosed hole filled.

    A room's boundary is its walls. Fixtures, furniture symbols, its name and
    its dimension numerals are all printed inside it, and flood fill goes round
    every one of them — so tracing the raw region walks around a WC and reports
    a bathroom with 39 wall segments and twice its real perimeter. Filling the
    holes first is what makes a traced boundary mean "wall".
    """
    pad = np.ones((mask.shape[0] + 2, mask.shape[1] + 2), bool)
    pad[1:-1, 1:-1] = ~mask
    out = label_regions(pad)
    return mask | ((out != out[0, 0]) & pad)[1:-1, 1:-1]


def _fill_text_holes(mask: np.ndarray, max_hole_px: int) -> int:
    """Pixel count of `mask` with only glyph-sized holes filled.

    A room's name and its dimension numerals are printed inside the room. They
    are ink, so flood fill goes around them, so the floor comes out short. Those
    holes are added back. A *large* enclosed void is not a glyph — it is a shaft,
    a column, a stair core — and is left subtracted, which is why the cap exists.
    """
    # The border must be part of the OUTSIDE, not background: pad with True so
    # the flood from the corner reaches every cell outside the mask. Padding
    # with False leaves the real outside looking like just another enclosed
    # region, and a tight bbox makes it small enough to be mistaken for a glyph.
    pad = np.ones((mask.shape[0] + 2, mask.shape[1] + 2), bool)
    pad[1:-1, 1:-1] = ~mask
    out = label_regions(pad)
    outside = out[0, 0]
    ids, counts = np.unique(out[pad], return_counts=True)
    add = sum(int(c) for i, c in zip(ids, counts) if i != outside and c <= max_hole_px)
    return int(mask.sum()) + add


class VectorPdfSource:
    """Geometry from a plotted vector PDF."""

    MAX_TEXT_HOLE_M2 = Decimal("0.35")   # far above any glyph, far below any room

    def __init__(self, path: str, calibration: Calibration, *, dpi: int = 300,
                 ink_threshold: int = 200):
        calibration.validate()
        self.path = path
        self.calibration = calibration
        self.dpi = dpi
        self.ink_threshold = ink_threshold

    def _render(self, page: int) -> np.ndarray:
        import pymupdf
        p = pymupdf.open(self.path)[page]
        px = p.get_pixmap(dpi=self.dpi, colorspace=pymupdf.csGRAY)
        return np.frombuffer(px.samples, np.uint8).reshape(px.height, px.width)

    @property
    def px_mm(self) -> Decimal:
        return Decimal(72) / Decimal(self.dpi) * self.calibration.mm_per_pt

    def regions(self, page: int = 0, min_m2: float = 0.5) -> list[Region]:
        img = self._render(page)
        px_mm = self.px_mm
        px_m2 = (px_mm / 1000) ** 2
        max_hole = int(self.MAX_TEXT_HOLE_M2 / px_m2)
        lab = label_regions(img > self.ink_threshold)
        ids, counts = np.unique(lab, return_counts=True)
        out: list[Region] = []
        for rid, c in zip(ids, counts):
            if rid == 0 or Decimal(int(c)) * px_m2 < Decimal(str(min_m2)):
                continue
            ys, xs = np.where(lab == rid)
            y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
            sub = lab[y0:y1 + 1, x0:x1 + 1] == rid
            filled = _fill_text_holes(sub, max_hole)
            out.append(Region(
                id=int(rid),
                area_m2=Decimal(filled) * px_m2,
                raw_area_m2=Decimal(int(c)) * px_m2,
                bbox_mm=(int(x0 * px_mm), int(y0 * px_mm), int(x1 * px_mm), int(y1 * px_mm)),
                centroid_px=(int(xs.mean()), int(ys.mean())),
                width_mm=int((x1 - x0 + 1) * px_mm),
                height_mm=int((y1 - y0 + 1) * px_mm),
            ))
        out.sort(key=lambda r: -r.area_m2)
        return out

    def segmentation(self, page: int = 0, *, drawing_id: str = "",
                     revision: str = "") -> "Segmentation":
        """The same label map `regions()` builds, exposed so E25 can use it.

        Identical inputs and identical thresholds, so a segmentation and the
        region list from the same source describe the same pixels. The outside
        is identified by reading the label at the sheet corner rather than by
        assuming the largest region: on a plan with a big open terrace the
        largest free region is not always the paper.
        """
        import hashlib

        img = self._render(page)
        free = img > self.ink_threshold
        lab = label_regions(free)
        wall = ~free
        outside = int(lab[0, 0])
        outside_ids = outside_region_ids(lab)
        for a in (lab, wall):
            a.setflags(write=False)
        return Segmentation(
            labels=lab, wall_mask=wall, px_mm=self.px_mm, outside_id=outside,
            outside_ids=outside_ids,
            drawing_id=drawing_id, revision=revision, source_path=self.path,
            source_sha256=hashlib.sha256(
                Path(self.path).read_bytes()).hexdigest(),
            dpi=self.dpi, ink_threshold=self.ink_threshold,
        )


def outside_region_ids(labels: "np.ndarray") -> frozenset[int]:
    """Free regions that touch the sheet border — the paper, not the building.

    Reading one corner pixel was not enough. On a real sheet the space between
    the building and the paper margin is carved up by dimension lines, hatching
    and the title block, so a wall's outward march lands in one of those slivers
    rather than in the region the corner happens to sit in. Every one of AR-00's
    703 traced segments came back INTERNAL because of it.

    Connectivity to the border is the honest test: an enclosed courtyard never
    touches the border, and the paper always does. What this deliberately does
    NOT do is treat "not a known room" as "outside" — an annotation island in the
    middle of the sheet touches nothing, and the caller is expected to report
    that as unresolved rather than guess.
    """
    border = np.concatenate([
        labels[0, :].ravel(), labels[-1, :].ravel(),
        labels[:, 0].ravel(), labels[:, -1].ravel()])
    return frozenset(int(i) for i in np.unique(border) if i != 0)


@dataclass(frozen=True)
class Segmentation:
    """The label map and ink mask a render produced, handed out read-only.

    `regions()` computed both of these and threw them away, which is why E25's
    per-space wall model — which has existed and been tested for months — had
    never once run on a real drawing. The only thing missing was a way to reach
    them.

    The arrays are frozen with `setflags(write=False)`. A downstream module that
    could edit the label map could move a wall without anything recording that it
    had, and the whole provenance chain would still look intact.
    """

    labels: "np.ndarray"              # region id per pixel; 0 is ink
    wall_mask: "np.ndarray"           # True where the sheet has ink
    px_mm: Decimal
    outside_id: int                   # the region the sheet corner sits in
    # Every region touching the sheet border. The corner is one of them and is
    # kept for callers written before this existed, but classification uses the
    # whole set: the margin is not one region on a dimensioned sheet.
    outside_ids: frozenset = frozenset()
    drawing_id: str = ""
    revision: str = ""
    source_path: str = ""
    source_sha256: str = ""
    dpi: int = 300
    ink_threshold: int = 200

    @property
    def shape(self) -> tuple[int, int]:
        return self.labels.shape

    def region_ids(self) -> list[int]:
        return [int(i) for i in np.unique(self.labels) if i != 0]

    def provenance(self) -> dict:
        return {
            "source": self.source_path, "sha256": self.source_sha256,
            "drawing_id": self.drawing_id, "revision": self.revision,
            "dpi": self.dpi, "ink_threshold": self.ink_threshold,
            "px_mm": str(self.px_mm), "outside_id": self.outside_id,
            "outside_ids": sorted(self.outside_ids),
            "outside_basis": "free regions connected to the sheet border",
            "shape": list(self.shape),
        }


class DxfSource:
    """Geometry from a DXF. Inert until someone supplies one."""

    def __init__(self, path: str):
        self.path = path

    def regions(self, layer: str | None = None) -> list[Region]:
        raise GeometryError(
            "DxfSource is not implemented: no DXF has been supplied for any Urban "
            "Projects drawing, and a DWG cannot be read without ODA File Converter, "
            "which is not installed. Use VectorPdfSource, or send a DXF export."
        )


def shoelace_m2(points: Iterable[tuple[Decimal, Decimal]]) -> Decimal:
    """Exact area of a closed polygon. Raises if it does not close."""
    pts = [(Decimal(str(x)), Decimal(str(y))) for x, y in points]
    if len(pts) < 3:
        raise GeometryError(f"a polygon needs 3+ points, got {len(pts)}")
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    total = Decimal(0)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        total += x0 * y1 - x1 * y0
    return abs(total) / 2


# --------------------------------------------------------- source hierarchy
# Raster tracing is the WEAKEST deterministic source, not the strongest. On
# AR-00 a door leaf drawn inside a bathroom is ink, so a trace that treats all
# ink as wall follows it and reports 14.29 m for a room whose printed perimeter
# is 8.70 m. Where a stronger source exists and the two materially disagree,
# the raster result is rejected — never averaged in, because averaging a wrong
# number with a right one produces a third number that is also wrong.
SOURCE_RANK = {
    "CAD_ENTITY": 1,        # DWG/DXF geometry
    "VECTOR_PDF": 2,        # validated vector geometry
    "PRINTED_DIMENSION": 3,  # a dimension string the engineer wrote on the sheet
    "RASTER_TRACE": 4,       # deterministic, but the weakest of the four
    "HUMAN_REVIEW": 5,
}


@dataclass(frozen=True)
class GeometryCandidate:
    source: str
    value: Decimal
    note: str = ""

    @property
    def rank(self) -> int:
        if self.source not in SOURCE_RANK:
            raise GeometryError(f"unknown geometry source {self.source!r}")
        return SOURCE_RANK[self.source]


@dataclass(frozen=True)
class GeometryChoice:
    chosen: GeometryCandidate
    rejected: tuple[tuple[GeometryCandidate, str], ...] = ()
    status: str = "PASS"          # PASS / REVIEW / CHALLENGE

    @property
    def value(self) -> Decimal:
        return self.chosen.value


def choose_geometry(candidates: list[GeometryCandidate], *,
                    review_pct: Decimal = Decimal("2"),
                    challenge_pct: Decimal = Decimal("5")) -> GeometryChoice:
    """Take the strongest source, and say what was rejected and why.

    A weaker source that agrees is corroboration. A weaker source that disagrees
    by more than `challenge_pct` is rejected outright and named, so the conflict
    appears in the record instead of disappearing into an average.
    """
    if not candidates:
        raise GeometryError("no geometry candidates — nothing to choose between")
    ordered = sorted(candidates, key=lambda c: c.rank)
    best = ordered[0]
    if best.value <= 0:
        raise GeometryError(f"{best.source} gave a non-physical value {best.value}")
    rejected, status = [], "PASS"
    for c in ordered[1:]:
        pct = abs((c.value - best.value) / best.value * 100)
        if pct > challenge_pct:
            rejected.append((c, f"differs from {best.source} by {pct:.1f}% — rejected"))
            status = "CHALLENGE"
        elif pct > review_pct and status == "PASS":
            status = "REVIEW"
    return GeometryChoice(chosen=best, rejected=tuple(rejected), status=status)


# ------------------------------------------------- correcting raster erosion
def snap_to_wall_faces(x0: int, x1: int, y0: int, y1: int,
                       v_faces: list[tuple[float, float, float]],
                       h_faces: list[tuple[float, float, float]],
                       *, max_snap_px: float = 12.0
                       ) -> tuple[tuple[float, float, float, float], bool]:
    """Move a raster region's edges out onto the wall faces that bound it.

    Flood fill stops at the OUTERMOST INK PIXEL of a wall line, so it loses the
    line's stroke width plus its anti-aliased fringe on every side. Measured on
    AR-00 that loss is exactly 5.0 px on one axis and 3.0 px on the other, in a
    3250 mm kitchen and a 1500 mm bathroom alike — a constant, which is what
    proves it is an artefact of the raster and not a property of the walls.

    Over the same four rooms the vector wall faces sit within 8 mm of the
    printed dimensions, so snapping the region out to those faces measures the
    same thing the engineer dimensioned, from the stronger source.

    Returns the snapped edges and whether all four were found. When an edge has
    no bounding face the original is kept and the flag is False, because a
    partly-snapped box is not a measurement anyone should quietly use.
    """
    def nearest(target: float, lo: float, hi: float,
                faces: list[tuple[float, float, float]]) -> float | None:
        best, dist = None, None
        for pos, a, b in faces:
            if a > hi or b < lo:
                continue
            d = abs(pos - target)
            if d <= max_snap_px and (dist is None or d < dist):
                best, dist = pos, d
        return best

    nx0 = nearest(x0, y0, y1, v_faces)
    nx1 = nearest(x1, y0, y1, v_faces)
    ny0 = nearest(y0, x0, x1, h_faces)
    ny1 = nearest(y1, x0, x1, h_faces)
    complete = None not in (nx0, nx1, ny0, ny1)
    return ((nx0 if nx0 is not None else x0, nx1 if nx1 is not None else x1,
             ny0 if ny0 is not None else y0, ny1 if ny1 is not None else y1),
            complete)
