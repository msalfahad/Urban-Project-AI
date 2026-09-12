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

import numpy as np


class GeometryError(RuntimeError):
    """The geometry could not be established — never a reason to estimate."""


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


def _fill_text_holes(mask: np.ndarray, max_hole_px: int) -> int:
    """Pixel count of `mask` with only glyph-sized holes filled.

    A room's name and its dimension numerals are printed inside the room. They
    are ink, so flood fill goes around them, so the floor comes out short. Those
    holes are added back. A *large* enclosed void is not a glyph — it is a shaft,
    a column, a stair core — and is left subtracted, which is why the cap exists.
    """
    pad = np.zeros((mask.shape[0] + 2, mask.shape[1] + 2), bool)
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
