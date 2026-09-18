"""E1.1 §C — the source sheet, admitted as a SECOND REPRESENTATION.

E1 v1 drew its overlays on its own pale CAD linework, so every picture it
produced agreed with it by construction. A reviewer looking at the actual
sheet saw wedges cut through a pool and a kitchen boundary running along
a cabinet, because the sheet shows what was DRAWN FOR A BUILDER.

So E1.1 admits the original ground-floor raster and registers it against
the CAD, for one purpose:

    TO CHALLENGE OR CORROBORATE A ROLE THAT CAD EVIDENCE ALREADY PROPOSED

and never for these:

    it is NOT an independent source of truth. The sheet was plotted FROM
    this DWG, so the two are one design family and agreement between them
    shows the reading was faithful, not that the design is right

    it NEVER calculates geometry. No boundary, length, area or coordinate
    in any E1.1 register comes from a pixel

Registration itself is measured, not assumed: the CAD linework is drawn
at candidate scales and rotations and correlated against the sheet's ink,
and the fit is reported with the transform. Where the fit is not
established, the raster checks return NOT_ESTABLISHED and the release
gate treats that as a reason for human review, never as a pass.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

MODEL = "THE_SHEET_IS_A_SECOND_REPRESENTATION_NOT_A_SECOND_SOURCE_V1"

CROSS_REPRESENTATION_CORROBORATION = "CROSS_REPRESENTATION_CORROBORATION"
NEVER_INDEPENDENT_SOURCE_TRUTH = (
    "the sheet was plotted from this DWG. It is the SAME DESIGN SOURCE "
    "FAMILY, so agreement is cross-representation corroboration and never "
    "independent confirmation")
RASTER_DOES_NOT_CALCULATE_GEOMETRY = (
    "no boundary, length, area or coordinate in E1.1 comes from a pixel. "
    "CAD remains the analytical geometry source; the raster may only "
    "support or challenge a role CAD already proposed")

ALLOWED_USES = ("ENTITY_ROLE_QA", "LABEL_PLACEMENT_QA",
                "VISUAL_BOUNDARY_PLAUSIBILITY", "CASEWORK_WALL_DISTINCTION",
                "STAIR_AND_CURVED_OBJECT_INTERPRETATION")

# --- probe outcomes ------------------------------------------------------
WALL_BAND = "THE_SOURCE_RASTER_SHOWS_A_WALL_BAND_HERE"
SINGLE_STROKE = "THE_SOURCE_RASTER_SHOWS_ONE_THIN_STROKE_HERE"
NO_INK = "THE_SOURCE_RASTER_SHOWS_NO_STROKE_HERE"
NOT_ESTABLISHED = "RASTER_REGISTRATION_NOT_ESTABLISHED"

# --- GENERAL parameters --------------------------------------------------
INK_LEVEL = 190                 # 8-bit grey darker than this is ink
WORK_LONG_EDGE = 900            # the coarse search resolution
MIN_QUALITY = 0.45              # share of CAD ink landing on sheet ink
PROBE_SAMPLES = 9
BAND_MIN_MM = 75.0
BAND_MAX_MM = 400.0
BAND_SHARE = 0.5

SCOPE = ("GENERAL raster/vector registration. No project coordinate, page "
         "number or expected dimension appears here")


def model_hash() -> str:
    parts = [MODEL] + list(ALLOWED_USES) + [f"{INK_LEVEL}",
                                            f"{WORK_LONG_EDGE}",
                                            f"{MIN_QUALITY}"]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


@dataclass
class Registration:
    """How the sheet and the CAD line up, and how well."""

    image_path: str = ""
    image_px: tuple = ()
    rotation_deg: float = 0.0
    px_per_mm: float = 0.0
    ox: float = 0.0
    oy: float = 0.0
    cx_mm: float = 0.0
    cy_mm: float = 0.0
    quality: float = 0.0
    established: bool = False
    method: str = "SCALE_AND_ROTATION_SEARCH_WITH_FFT_TRANSLATION"

    def to_px(self, x_mm, y_mm) -> tuple:
        a = math.radians(self.rotation_deg)
        dx, dy = x_mm - self.cx_mm, y_mm - self.cy_mm
        xr = dx * math.cos(a) - dy * math.sin(a)
        yr = dx * math.sin(a) + dy * math.cos(a)
        return (self.ox + xr * self.px_per_mm,
                self.oy - yr * self.px_per_mm)

    def to_mm(self, px, py) -> tuple:
        """The inverse transform, so a reading taken in sheet pixels can
        be placed on the CAD. It moves a LOCATION, never a boundary."""
        if not self.px_per_mm:
            return (0.0, 0.0)
        xr = (px - self.ox) / self.px_per_mm
        yr = -(py - self.oy) / self.px_per_mm
        a = -math.radians(self.rotation_deg)
        dx = xr * math.cos(a) - yr * math.sin(a)
        dy = xr * math.sin(a) + yr * math.cos(a)
        return (self.cx_mm + dx, self.cy_mm + dy)

    def mm_per_px(self) -> float:
        return 1.0 / self.px_per_mm if self.px_per_mm else 0.0

    def record(self) -> dict:
        return {
            "source_raster": self.image_path,
            "image_px": list(self.image_px),
            "REGISTRATION_ESTABLISHED": self.established,
            "rotation_deg": self.rotation_deg,
            "px_per_mm": round(self.px_per_mm, 8),
            "mm_per_px": round(self.mm_per_px(), 4),
            "origin_px": [round(self.ox, 2), round(self.oy, 2)],
            "cad_centre_mm": [round(self.cx_mm, 3), round(self.cy_mm, 3)],
            "fit_quality_share_of_cad_ink_on_sheet_ink": round(
                self.quality, 4),
            "minimum_quality_to_establish": MIN_QUALITY,
            "method": self.method,
            "corroboration_kind": CROSS_REPRESENTATION_CORROBORATION,
            "never_independent_source_truth": NEVER_INDEPENDENT_SOURCE_TRUTH,
            "raster_does_not_calculate_geometry":
                RASTER_DOES_NOT_CALCULATE_GEOMETRY,
            "allowed_uses": list(ALLOWED_USES),
        }


def _ink(image, level=INK_LEVEL):
    import numpy as np
    return (np.asarray(image) < level).astype("float32")


def _render(primitives, size, *, cx, cy, s, rot):
    from PIL import Image, ImageDraw
    img = Image.new("L", size, 0)
    d = ImageDraw.Draw(img)
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)

    def T(x, y):
        dx, dy = x - cx, y - cy
        xr, yr = dx * ca - dy * sa, dx * sa + dy * ca
        return (size[0] / 2 + xr * s, size[1] / 2 - yr * s)

    for p in primitives:
        if p.kind == "SEGMENT":
            d.line([T(p.x1, p.y1), T(p.x2, p.y2)], fill=255, width=1)
        elif p.kind in ("ARC", "CIRCLE"):
            n = 24
            a0 = p.start_angle
            sw = ((p.end_angle - p.start_angle) % (2 * math.pi)
                  if p.kind == "ARC" else 2 * math.pi)
            d.line([T(p.cx + p.radius * math.cos(a0 + sw * i / n),
                      p.cy + p.radius * math.sin(a0 + sw * i / n))
                    for i in range(n + 1)], fill=255, width=1)
    return img


def register(image_path, primitives, *, extent, rotations=(0, 90, 180, 270),
             scale_lo=None, scale_hi=None, steps=110) -> Registration:
    """Find the scale, rotation and offset that put the CAD on the sheet."""
    import numpy as np
    from PIL import Image

    img = Image.open(image_path).convert("L")
    full = img.size
    f = WORK_LONG_EDGE / max(full)
    work = (max(1, int(full[0] * f)), max(1, int(full[1] * f)))
    A = _ink(img.resize(work, Image.LANCZOS))
    FA = np.fft.rfft2(A)

    x0, y0, x1, y1 = extent
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    span = max(x1 - x0, y1 - y0) or 1.0
    lo = scale_lo if scale_lo else 0.25 * max(work) / span
    hi = scale_hi if scale_hi else 1.35 * max(work) / span

    prims = [p for p in primitives if p.kind in ("SEGMENT", "ARC", "CIRCLE")]
    best = None
    for rot in rotations:
        for k in range(steps + 1):
            s = lo + (hi - lo) * k / steps
            B = _ink(_render(prims, work, cx=cx, cy=cy, s=s, rot=rot),
                     level=1)
            B = 1.0 - B                      # _render paints 255 on 0
            tot = B.sum()
            if tot < 50:
                continue
            C = np.fft.irfft2(FA * np.conj(np.fft.rfft2(B)), A.shape)
            i = int(np.argmax(C))
            q = float(C.flat[i]) / tot
            if best is None or q > best[0]:
                best = (q, rot, s, np.unravel_index(i, A.shape))

    if best is None:
        return Registration(image_path=str(image_path), image_px=full)
    q, rot, s, (dy, dx) = best
    h, w = A.shape
    dx = dx - w if dx > w / 2 else dx
    dy = dy - h if dy > h / 2 else dy
    reg = Registration(
        image_path=str(image_path), image_px=full, rotation_deg=float(rot),
        px_per_mm=float(s) / f,
        ox=(work[0] / 2.0 + float(dx)) / f,
        oy=(work[1] / 2.0 + float(dy)) / f,
        cx_mm=cx, cy_mm=cy, quality=float(q),
        established=bool(q >= MIN_QUALITY))
    return reg


# ------------------------------------------------------------ the probes

class Sheet:
    """The registered sheet, answering questions about ink."""

    def __init__(self, reg: Registration):
        from PIL import Image
        import numpy as np
        self.reg = reg
        self.ok = reg.established
        self.image = Image.open(reg.image_path).convert("L") if self.ok \
            else None
        self.grey = np.asarray(self.image) if self.ok else None

    def _dark(self, x_mm, y_mm) -> bool:
        px, py = self.reg.to_px(x_mm, y_mm)
        gx, gy = int(round(px)), int(round(py))
        g = self.grey
        if g is None or not (0 <= gy < g.shape[0] and 0 <= gx < g.shape[1]):
            return False
        lo_y, hi_y = max(0, gy - 1), min(g.shape[0], gy + 2)
        lo_x, hi_x = max(0, gx - 1), min(g.shape[1], gx + 2)
        return bool((g[lo_y:hi_y, lo_x:hi_x] < INK_LEVEL).any())

    def stroke_profile(self, x1, y1, x2, y2) -> str:
        """Is this line drawn as a wall band, or as one thin stroke?"""
        if not self.ok:
            return NOT_ESTABLISHED
        L = math.hypot(x2 - x1, y2 - y1)
        if L <= 0:
            return NOT_ESTABLISHED
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        nx, ny = -uy, ux
        band = single = blank = 0
        for i in range(1, PROBE_SAMPLES + 1):
            t = L * i / (PROBE_SAMPLES + 1)
            px, py = x1 + ux * t, y1 + uy * t
            if not self._dark(px, py):
                blank += 1
                continue
            found = False
            for sign in (1, -1):
                d = BAND_MIN_MM
                while d <= BAND_MAX_MM:
                    if self._dark(px + nx * d * sign, py + ny * d * sign):
                        found = True
                        break
                    d += 20.0
                if found:
                    break
            if found:
                band += 1
            else:
                single += 1
        n = PROBE_SAMPLES
        if blank >= n * BAND_SHARE:
            return NO_INK
        if band >= (n - blank) * BAND_SHARE:
            return WALL_BAND
        return SINGLE_STROKE

    def crop(self, x0_mm, y0_mm, x1_mm, y1_mm, *, pad_mm=0.0):
        """The part of the sheet covering a mm rectangle, upright."""
        if not self.ok:
            return None
        pts = [self.reg.to_px(x, y)
               for x in (x0_mm - pad_mm, x1_mm + pad_mm)
               for y in (y0_mm - pad_mm, y1_mm + pad_mm)]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        box = (int(max(0, min(xs))), int(max(0, min(ys))),
               int(min(self.image.size[0], max(xs))),
               int(min(self.image.size[1], max(ys))))
        if box[2] <= box[0] or box[3] <= box[1]:
            return None
        return self.image.crop(box), box


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "ALLOWED_USES": list(ALLOWED_USES),
        "INK_LEVEL": INK_LEVEL,
        "WORK_LONG_EDGE": WORK_LONG_EDGE,
        "MIN_QUALITY": MIN_QUALITY,
        "PROBE_SAMPLES": PROBE_SAMPLES,
        "BAND_MIN_MM": BAND_MIN_MM,
        "BAND_MAX_MM": BAND_MAX_MM,
        "SCOPE": SCOPE,
        "why": {
            "never_independent_source_truth": NEVER_INDEPENDENT_SOURCE_TRUTH,
            "raster_does_not_calculate_geometry":
                RASTER_DOES_NOT_CALCULATE_GEOMETRY,
        },
    }
