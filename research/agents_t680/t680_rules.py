"""R-T680-1 .. -3: STAIR-SHAFT PLASTER / PAINT STOREY-BAND LINES, round 2 (every villa; research provenance, proposed;
no new rule value, nothing wired or released).

R-T680-1 HEAD FROM VECTOR GEOMETRY INTO A HELD SHAFT OPENING. A shaft-face opening held as a band (its sill / head
  printed nowhere) takes its sill and head from a Checker-verified VECTOR-geometry record (UP-OPEN-GEOM-001 proposal,
  T-201 convention): status DRAWING-CONFIRMED, a vector view named (DWF / DXF / vector PDF), sill < head, both in
  metres, the width equal to the face opening's drawn width within 0.02 m, and the opening inside the face region.
  A raster-scaled value (a scan, 'scaled', 'px') is refused: it stays a candidate and the band stays HELD. The opening
  is then deducted in both cases (low and high) by its own rectangle, once, where it does not overlap a contact.

R-T680-2 A STOREY-BAND LINE KEEPS ITS SHARE OF THE PIER RETURNS. When one continuous shaft face (Q-72, R-SHAFT-1) is
  split into storey-band lines, every physically built piece of the face goes to exactly one band: a pier / column
  return (projection depth x exposed vertical length) is split at the same storey marks as the face. A band line
  without its returns, or a whole-face total that differs from the sum of its bands, is refused (the T-173 bands
  dropped 1.21 .. 1.22 m2 of returns: no line carried them).

R-T680-3 A BLANK LINE TAKES A BOUND ONLY FROM THE CURRENT INPUTS. A candidate-blank line whose bound lives only in an
  overlay row is restated from the current face model (same corrections, the newly established openings applied)
  before it is offered for wiring; the bound must satisfy 0 < low <= high. A face whose top datum is missing (no
  printed roof / soffit level and no owner-approved fallback) gives no number: the line stays HELD by name, never 0.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from shapely.geometry import LineString, box
from shapely.ops import unary_union


class RuleError(ValueError):
    """A term is missing, refused or inconsistent (held, never 0)."""


VECTOR_VIEWS = ("DWF", "DXF", "DWG", "VECTOR")
RASTER_MARKS = ("scaled", "raster", "px", "scan")


def q3(x) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def S(x) -> str:
    return format(q3(x), "f")


# ---------------------------------------------------------------- R-T680-1

def opening_from_geometry(held: dict, rec: dict, face_region: list) -> dict:
    """held: the face opening as the face model holds it ({id, u: [u0, u1], status HELD}); rec: the vector record
    ({id, status, view, sill_m, head_m, width_m, source}). -> opening dict with a rect, deducted in both cases."""
    for k in ("id", "status", "view", "sill_m", "head_m", "width_m", "source"):
        if rec.get(k) in (None, ""):
            raise RuleError(f"{held.get('id')}: vector record lacks {k!r} (held, never 0)")
    if rec["status"] != "DRAWING-CONFIRMED":
        raise RuleError(f"{held['id']}: record status {rec['status']!r} is not DRAWING-CONFIRMED")
    src = (rec["view"] + " " + rec["source"]).lower()
    if any(m in src for m in RASTER_MARKS) and not any(v.lower() in rec["view"].lower() for v in VECTOR_VIEWS):
        raise RuleError(f"{held['id']}: raster-scaled value refused (a candidate only, the band stays HELD)")
    if not any(v.lower() in rec["view"].lower() for v in VECTOR_VIEWS):
        raise RuleError(f"{held['id']}: view {rec['view']!r} is not a vector source")
    sill, head, w = (float(rec[k]) for k in ("sill_m", "head_m", "width_m"))
    if sill > 100 or head > 100 or w > 20:
        raise RuleError(f"{held['id']}: values look like millimetres, not metres")
    if head <= sill:
        raise RuleError(f"{held['id']}: head {head} not above sill {sill}")
    u0, u1 = held["u"]
    if abs((u1 - u0) - w) > 0.02:
        raise RuleError(f"{held['id']}: drawn width {w} differs from the face opening {u1 - u0:.3f} by > 0.02 m")
    G = unary_union([box(r[0], r[2], r[1], r[3]) for r in face_region])
    o = box(u0, sill, u1, head)
    if o.difference(G).area > 1e-9:
        raise RuleError(f"{held['id']}: opening {sill} .. {head} lies partly outside the face region")
    return {"id": held["id"], "status": "PRINTED", "evidence": "DRAWING-CONFIRMED", "rect": [u0, u1, sill, head],
            "source": rec["source"]}


# ---------------------------------------------------------------- R-T680-2

def returns_by_band(net_geom, returns: list, marks: list) -> list:
    """Pier-return area per storey band: depth x the exposed vertical length of net_geom at the return's u, clipped
    to the band. marks = the storey marks (z); bands are (-inf, m1), (m1, m2), ..., (mk, +inf)."""
    if net_geom.is_empty:
        return [0.0] * (len(marks) + 1)
    zmin, zmax = net_geom.bounds[1] - 1, net_geom.bounds[3] + 1
    edges = [zmin] + list(marks) + [zmax]
    out = []
    for lo, hi in zip(edges, edges[1:]):
        a = 0.0
        for rt in returns:
            if rt.get("depth") is None or rt["depth"] <= 0:
                raise RuleError("pier return depth missing or not positive (held, never 0)")
            a += rt["depth"] * net_geom.intersection(LineString([(rt["u"], lo), (rt["u"], hi)])).length
        out.append(a)
    return out


def check_bands_sum(whole: float, bands: list, tol: float = 0.005) -> None:
    if abs(whole - sum(bands)) > tol:
        raise RuleError(f"whole face {whole:.4f} != sum of bands {sum(bands):.4f}: a piece is in no band")


# ---------------------------------------------------------------- R-T680-3

def face_top(roof_mark, buildup, slab_t):
    """Plaster top of a shaft face = roof mark - build-up - slab thickness; a missing datum is HELD (None)."""
    if roof_mark is None or slab_t is None or buildup is None:
        return None
    return float(roof_mark) - float(buildup) - float(slab_t)


def line_bound(low, high, why_if_none: str) -> dict:
    if low is None or high is None:
        return {"class": "HELD", "held_low": None, "held_high": None, "measured_net": None, "why": why_if_none}
    lo, hi = q3(low), q3(high)
    if lo <= 0 or lo > hi:
        raise RuleError(f"bound {lo} .. {hi} refused (0 < low <= high)")
    return {"class": "HELD", "held_low": format(lo, "f"), "held_high": format(hi, "f"), "measured_net": None}


def restate(before_low, before_high, after: dict) -> dict:
    """Change per line, low and high, in m2 (before None = blank)."""
    def d(a, b):
        if a is None or b is None:
            return None
        return S(Decimal(str(b)) - Decimal(str(a)))
    return {"before": [None if before_low is None else S(before_low), None if before_high is None else S(before_high)],
            "after": [after["held_low"], after["held_high"]],
            "delta": [d(before_low, after["held_low"]), d(before_high, after["held_high"])]}
