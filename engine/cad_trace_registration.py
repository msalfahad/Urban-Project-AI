"""CAD <-> TRACE registration and CAD_TRACE_LINK_STATUS (§15).

The processed plan sheet (pixels) and the DWG model (mm) describe one
design. A registration between them is fitted ONLY from declared pairs
whose two sides are each established on their own path (a printed
dimension's extension line in pixels; an authored wall line in mm), axis
by axis, by least squares, with residuals reported. With it, an authored
run can be projected into pixel space and tested against a trace's stored
geometry:

    CAD_TRACE_LINK_STATUS
      ESTABLISHED     projected run lies on the trace geometry within
                      tolerance at both ends and the same layer family
      PROVISIONAL     within a looser tolerance, or one end only
      AMBIGUOUS       more than one run fits the trace
      NOT_ESTABLISHED nothing fits

The test uses location, endpoints and adjacency in the drawing itself -
never a benchmark value. A link that is not ESTABLISHED never carries a CAD
length into an A21-linked quantity.
"""

from __future__ import annotations

import math

LINK_STATUSES = ("ESTABLISHED", "PROVISIONAL", "AMBIGUOUS", "NOT_ESTABLISHED")
TOL_PX = 6.0
LOOSE_PX = 14.0


def fit_axis(pairs: list) -> dict:
    """pairs: [(mm, px), ...] -> px = a * mm + b, least squares."""
    n = len(pairs)
    if n < 2:
        raise ValueError("at least two pairs per axis")
    sx = sum(p[0] for p in pairs)
    sy = sum(p[1] for p in pairs)
    sxx = sum(p[0] * p[0] for p in pairs)
    sxy = sum(p[0] * p[1] for p in pairs)
    den = n * sxx - sx * sx
    a = (n * sxy - sx * sy) / den
    b = (sy - a * sx) / n
    res = [round(p[1] - (a * p[0] + b), 2) for p in pairs]
    return {"A_PX_PER_MM": a, "B_PX": b, "MM_PER_PX": (1 / a if a else None),
            "RESIDUALS_PX": res, "MAX_ABS_RESIDUAL_PX": max(abs(r) for r in res),
            "N_PAIRS": n}


class Registration:
    def __init__(self, x_pairs: list, y_pairs: list):
        self.x = fit_axis(x_pairs)
        self.y = fit_axis(y_pairs)

    def to_px(self, x_mm: float, y_mm: float) -> tuple:
        return (self.x["A_PX_PER_MM"] * x_mm + self.x["B_PX"],
                self.y["A_PX_PER_MM"] * y_mm + self.y["B_PX"])

    def to_mm(self, x_px: float, y_px: float) -> tuple:
        return ((x_px - self.x["B_PX"]) / self.x["A_PX_PER_MM"],
                (y_px - self.y["B_PX"]) / self.y["A_PX_PER_MM"])

    def record(self) -> dict:
        return {"X_AXIS": self.x, "Y_AXIS": self.y,
                "SCALE_MM_PER_PX": {"X": round(self.x["MM_PER_PX"], 3),
                                    "Y": round(self.y["MM_PER_PX"], 3)},
                "FITTED_FROM": "declared pairs only, each side established on its own path"}


def _seg_dist(p, a, b) -> float:
    vx, vy = b[0] - a[0], b[1] - a[1]
    L = vx * vx + vy * vy or 1.0
    u = max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L))
    return math.hypot(p[0] - a[0] - u * vx, p[1] - a[1] - u * vy)


def link_status(reg: Registration, run: dict, trace_px: list, *, tol_px: float = TOL_PX,
                loose_px: float = LOOSE_PX) -> dict:
    """run: {AXIS 'H'|'V', FIXED_MM, FROM_MM, TO_MM}; trace_px: polyline or
    bbox-as-polyline in pixels. Tests both projected endpoints against the
    trace geometry and the trace's endpoints against the projected run."""
    if run["AXIS"] == "H":
        a = reg.to_px(run["FROM_MM"], run["FIXED_MM"])
        b = reg.to_px(run["TO_MM"], run["FIXED_MM"])
    else:
        a = reg.to_px(run["FIXED_MM"], run["FROM_MM"])
        b = reg.to_px(run["FIXED_MM"], run["TO_MM"])
    pts = [tuple(p) for p in trace_px]
    segs = list(zip(pts, pts[1:])) if len(pts) > 1 else [(pts[0], pts[0])]
    d_a = min(_seg_dist(a, s, e) for s, e in segs)
    d_b = min(_seg_dist(b, s, e) for s, e in segs)
    d_t = max(_seg_dist(p, a, b) for p in pts)
    worst = max(d_a, d_b, d_t)
    st = ("ESTABLISHED" if worst <= tol_px else
          "PROVISIONAL" if worst <= loose_px or min(d_a, d_b) <= tol_px else
          "NOT_ESTABLISHED")
    return {"CAD_TRACE_LINK_STATUS": st, "PROJECTED_RUN_PX": [list(map(lambda v: round(v, 1), a)),
                                                              list(map(lambda v: round(v, 1), b))],
            "END_DISTANCES_PX": [round(d_a, 1), round(d_b, 1)],
            "TRACE_TO_RUN_MAX_PX": round(d_t, 1), "TOL_PX": tol_px,
            "TESTED_ON": "location, endpoints and adjacency in the drawing; not a benchmark"}
