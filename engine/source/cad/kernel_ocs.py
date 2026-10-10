"""OCS -> WCS for K1: an Urban-owned Arbitrary Axis Algorithm, fail-closed.

R8.1 DECISION (Option A, see 03_OCS_DECISION.md): this is a CLEAN
REIMPLEMENTATION from the published DXF semantics. U-C4N/Autocad-MCP
backends/ocs.py @ cdb10638 was used as a REFERENCE for behaviour only (which
entities are OCS-borne; that a -Z frame reverses sweeps); no code was
copied. It deliberately does NOT use ezdxf.math.OCS: the R8.2 K2 route
realises through ezdxf, and a shared OCS implementation would make K1 and
K2 fail together in exactly the domain their comparison exists to test.

Arbitrary Axis Algorithm (DXF Reference, "Object Coordinate Systems"):
    N  = extrusion normalised
    if |Nx| < 1/64 and |Ny| < 1/64:  Ax = Wy x N     (Wy = (0,1,0))
    else:                            Ax = Wz x N     (Wz = (0,0,1))
    Ax normalised;  Ay = N x Ax normalised
    WCS point = x*Ax + y*Ay + z*N

Plan realisation is exact only when N is +/-Z. Anything else cannot be
expressed as 2D plan geometry from (x, y) and raises UNSUPPORTED_FRAME.
A missing-but-malformed, zero, non-finite, wrong-length or non-numeric
extrusion raises FRAME_UNREADABLE. Nothing here ever returns an identity
frame for a value it could not read.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..findings import FRAME_UNREADABLE, UNSUPPORTED_FRAME

AAA_THRESHOLD = 1.0 / 64.0
# |Nx|, |Ny| of a UNIT normal above which the frame is not plan-expressible.
# float64 carries ~2.2e-16 relative precision; 1e-12 admits only decoder
# rounding of an exact +/-Z normal. Chosen from number representation alone.
PLAN_NORMAL_EPS = 1e-12


class SourceFrameError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class PlanFrame:
    """Plan part of an OCS: WCS_xy = x*ax + y*ay."""

    ax: tuple
    ay: tuple
    normal_z_sign: int

    @property
    def linear(self) -> tuple:          # (a, b, c, d) for Affine2.linear
        return (self.ax[0], self.ax[1], self.ay[0], self.ay[1])


def _cross(u, v):
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def _norm(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def validate_normal(extrusion) -> tuple:
    """A readable, finite, non-zero 3-vector, normalised — or FRAME_UNREADABLE."""
    if isinstance(extrusion, (str, bytes)) or not isinstance(extrusion, (list, tuple)) or len(extrusion) != 3:
        raise SourceFrameError(FRAME_UNREADABLE, f"extrusion {extrusion!r} is not a 3-vector")
    vals = []
    for v in extrusion:
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise SourceFrameError(FRAME_UNREADABLE, f"extrusion {extrusion!r} has a non-numeric component")
        vals.append(float(v))
    n = _norm(vals)
    if n == 0.0:
        raise SourceFrameError(FRAME_UNREADABLE, f"extrusion {extrusion!r} is the zero vector")
    return (vals[0] / n, vals[1] / n, vals[2] / n)


def arbitrary_axes(extrusion) -> tuple:
    """(Ax, Ay, N) for any readable extrusion, including tilted ones."""
    n = validate_normal(extrusion)
    if abs(n[0]) < AAA_THRESHOLD and abs(n[1]) < AAA_THRESHOLD:
        ax = _cross((0.0, 1.0, 0.0), n)
    else:
        ax = _cross((0.0, 0.0, 1.0), n)
    la = _norm(ax)
    ax = (ax[0] / la, ax[1] / la, ax[2] / la)
    ay = _cross(n, ax)
    ly = _norm(ay)
    ay = (ay[0] / ly, ay[1] / ly, ay[2] / ly)
    return ax, ay, n


def plan_frame(extrusion) -> PlanFrame:
    """The OCS as a plan map, or a SourceFrameError naming why it is not one."""
    ax, ay, n = arbitrary_axes(extrusion)
    if abs(n[0]) > PLAN_NORMAL_EPS or abs(n[1]) > PLAN_NORMAL_EPS:
        raise SourceFrameError(UNSUPPORTED_FRAME,
                               f"normal {tuple(round(v, 12) for v in n)} is not +/-Z; (x, y) does not fix a plan point")
    return PlanFrame(ax=(ax[0], ax[1]), ay=(ay[0], ay[1]), normal_z_sign=1 if n[2] > 0 else -1)


def plan_normal_sign(extrusion) -> int:
    """+1 / -1 for a +/-Z normal; raises like plan_frame otherwise (ELLIPSE)."""
    return plan_frame(extrusion).normal_z_sign
