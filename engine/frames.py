"""E23F — the transform between the vector page frame and the raster frame.

This existed as an assumption written inline in two tools:

    "the vector frame is the unrotated page and the raster is the rendered
     page; on a 270-degree rotation the axes swap"

The axes do swap. They also FLIP, and the comment did not say so, so gate G8
and the whole vector-raster correspondence in the previous round were computed
against geometry that was mirrored. The numbers were confidently wrong.

So the transform is now measured, not reasoned about. `fit()` scores every
candidate against the raster wall mask by sampling points along known heavy
vector strokes and asking how many land on wall pixels. On AR-00 the answer is
unambiguous:

    identity        0.077        rot180          0.056
    swap            0.135        swap+flipx      0.019
    rot90           0.069        SWAP+FLIPY      1.000
    rot270          0.142        swap+flipboth   0.015

A 1.000 against a 0.142 runner-up is not a judgement call. And because it is
measured, a differently-rotated sheet from another project will be measured
too, rather than inheriting this one's answer.

    ORDER IS NEVER IDENTITY, AND NEITHER IS A COMMENT.
"""

from __future__ import annotations

from dataclasses import dataclass

IDENTITY = "IDENTITY"
SWAP = "SWAP"
SWAP_FLIP_Y = "SWAP_FLIP_Y"
SWAP_FLIP_X = "SWAP_FLIP_X"
SWAP_FLIP_BOTH = "SWAP_FLIP_BOTH"
ROT90 = "ROT90"
ROT180 = "ROT180"
ROT270 = "ROT270"

# A fit below this is not a transform, it is a coincidence.
MIN_ACCEPTABLE_FIT = 0.80
# And it must beat the runner-up by this much, or the answer is ambiguous.
MIN_MARGIN = 0.20


class FrameError(RuntimeError):
    """The two frames could not be related without guessing."""


@dataclass(frozen=True)
class Frame:
    """One measured mapping from vector page mm to raster mm."""

    name: str
    raster_w_mm: float
    raster_h_mm: float
    fit: float = 0.0
    runner_up: float = 0.0

    def to_raster(self, x: float, y: float) -> tuple[float, float]:
        w, h = self.raster_w_mm, self.raster_h_mm
        if self.name == IDENTITY:
            return (x, y)
        if self.name == SWAP:
            return (y, x)
        if self.name == SWAP_FLIP_Y:
            return (y, h - x)
        if self.name == SWAP_FLIP_X:
            return (w - y, x)
        if self.name == SWAP_FLIP_BOTH:
            return (w - y, h - x)
        if self.name == ROT90:
            return (h - y, x)
        if self.name == ROT180:
            return (w - x, h - y)
        if self.name == ROT270:
            return (y, w - x)
        raise FrameError(f"unknown frame {self.name!r}")

    def to_vector(self, rx: float, ry: float) -> tuple[float, float]:
        w, h = self.raster_w_mm, self.raster_h_mm
        if self.name == IDENTITY:
            return (rx, ry)
        if self.name == SWAP:
            return (ry, rx)
        if self.name == SWAP_FLIP_Y:
            return (h - ry, rx)
        if self.name == SWAP_FLIP_X:
            return (ry, w - rx)
        if self.name == SWAP_FLIP_BOTH:
            return (h - ry, w - rx)
        if self.name == ROT90:
            return (ry, h - rx)
        if self.name == ROT180:
            return (w - rx, h - ry)
        if self.name == ROT270:
            return (w - ry, rx)
        raise FrameError(f"unknown frame {self.name!r}")

    def bbox_to_vector(self, bbox_mm) -> tuple[float, float, float, float]:
        """A raster bbox in vector coordinates, corners re-ordered after any
        flip. Mapping corners without re-ordering produces an inverted box that
        silently overlaps nothing."""
        x0, y0, x1, y1 = bbox_mm
        pts = [self.to_vector(x, y)
               for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    def record(self) -> dict:
        return {"frame": self.name, "fit": round(self.fit, 3),
                "runner_up": round(self.runner_up, 3),
                "raster_w_mm": round(self.raster_w_mm, 1),
                "raster_h_mm": round(self.raster_h_mm, 1)}


CANDIDATES = (IDENTITY, SWAP, SWAP_FLIP_Y, SWAP_FLIP_X, SWAP_FLIP_BOTH,
              ROT90, ROT180, ROT270)


def fit(segments, wall_mask, px_mm: float, *, samples: int = 12,
        max_segments: int = 60) -> Frame:
    """Measure which mapping puts vector walls on raster wall pixels.

    `segments` should be strokes likely to BE walls — long heavy ones — but the
    fit does not depend on them all being walls: a wrong transform scores near
    zero whatever is fed to it, which is what makes this a measurement rather
    than another assumption.
    """
    import numpy as np

    h, w = wall_mask.shape
    wm, hm = w * px_mm, h * px_mm
    if not segments:
        raise FrameError(
            "no segments to fit with; a frame asserted without a measurement "
            "is the assumption this module exists to replace")

    scores: dict[str, float] = {}
    for name in CANDIDATES:
        f = Frame(name, wm, hm)
        hit = tot = 0
        for s in segments[:max_segments]:
            for t in np.linspace(0.15, 0.85, samples):
                x = s.x0_mm + (s.x1_mm - s.x0_mm) * t
                y = s.y0_mm + (s.y1_mm - s.y0_mm) * t
                rx, ry = f.to_raster(x, y)
                c, r = int(rx / px_mm), int(ry / px_mm)
                if 0 <= r < h and 0 <= c < w:
                    tot += 1
                    hit += bool(wall_mask[r, c])
        scores[name] = hit / tot if tot else 0.0

    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    best, runner = ranked[0], ranked[1]
    if best[1] < MIN_ACCEPTABLE_FIT:
        raise FrameError(
            f"the best frame {best[0]} fits only {best[1]:.3f} of sampled wall "
            f"points. Below {MIN_ACCEPTABLE_FIT} this is a coincidence, not a "
            "transform, and using it would mirror every comparison")
    if best[1] - runner[1] < MIN_MARGIN:
        raise FrameError(
            f"{best[0]} ({best[1]:.3f}) and {runner[0]} ({runner[1]:.3f}) fit "
            "almost equally well. An ambiguous frame must be resolved, not "
            "picked")
    return Frame(best[0], wm, hm, fit=best[1], runner_up=runner[1])
