"""URBAN-SRD-1 and URBAN-RGD-1 — identity digests, NOT reconciliation.

SOURCE_REPRESENTATION_DIGEST (URBAN-SRD-1)
    "What exact normalised representation did this decoder route produce?"
    Computed over a route's representation records (see
    cad/libredwg_map.representation_records for the D1 route). It says
    nothing about whether the geometry is right.

REALISED_GEOMETRY_DIGEST (URBAN-RGD-1)
    "What physical geometry does Urban say exists?" Computed over realised
    plan primitives in MILLIMETRES. Geometry only: no handle, type, layer or
    traversal direction; a curve is its point set (centre, radius, sorted end
    points, mid-sweep point).

A digest is an IDENTITY / CHANGE detector. Two correct routes may differ by
harmless float noise and still straddle a rounding boundary; K1-vs-K2
agreement is decided by tolerance-aware reconciliation (R8.2), never by
comparing these hashes.

Canonical numbers, frozen in R8.0 before any real-project comparison:
realised 1e-6 mm, source 1e-9 native/radian, ROUND_HALF_EVEN on
Decimal(repr(float)), -0 -> 0, non-finite values marked, never rounded.
Justification (unchanged): float64 noise at building extents (<= 1e7 mm) is
~1e-9 mm; 1e-6 mm is 1000x above it and 1000x below drafting precision.
"""

from __future__ import annotations

import hashlib
import json
import math
from decimal import ROUND_HALF_EVEN, Decimal

REALISED_QUANTUM = Decimal("0.000001")
SOURCE_QUANTUM = Decimal("0.000000001")
SRD_PREFIX = "URBAN-SRD-1"
RGD_PREFIX = "URBAN-RGD-1"


def quantise(value, quantum: Decimal) -> str:
    d = Decimal(repr(float(value))).quantize(quantum, rounding=ROUND_HALF_EVEN)
    if d == 0:
        d = abs(d)
    return format(d, "f")


def canonical_source_value(v):
    if isinstance(v, bool) or v is None or isinstance(v, str) or isinstance(v, int):
        return v
    if isinstance(v, float):
        return quantise(v, SOURCE_QUANTUM) if math.isfinite(v) else f"NONFINITE:{v!r}"
    if isinstance(v, (list, tuple)):
        return [canonical_source_value(x) for x in v]
    if isinstance(v, dict):
        return {k: canonical_source_value(x) for k, x in sorted(v.items())}
    return repr(v)


def _lines(records) -> list:
    return sorted(json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=True) for r in records)


def source_representation_digest_of_records(records, route_id: str) -> str:
    return hashlib.sha256("\n".join([SRD_PREFIX, str(route_id)] + _lines(records)).encode()).hexdigest()


# ------------------------------------------------------------------ realised

def _as_physical(realised) -> dict:
    """Accept K1's RealisedGeometry or its contract dict (the same Urban-owned shape)."""
    if isinstance(realised, dict):
        return realised
    return realised.as_contract_dict()


def _p(pt, k):
    return [quantise(pt[0] * k, REALISED_QUANTUM), quantise(pt[1] * k, REALISED_QUANTUM)]


def realised_records(realised, unit_to_mm) -> list:
    if unit_to_mm is None or not (unit_to_mm > 0):
        raise ValueError("REALISED_GEOMETRY_DIGEST requires an established unit_to_mm; K1 never assumes one")
    k = float(unit_to_mm)
    phys = _as_physical(realised)
    recs = []
    for a, b in phys.get("segments", []):
        recs.append({"k": "SEGMENT", "p": sorted([_p(a, k), _p(b, k)])})
    for arc in phys.get("arcs", []):
        c = arc["CENTER"]
        r = arc.get("RADIUS")
        if r is None:
            r = math.hypot(arc["P0"][0] - c[0], arc["P0"][1] - c[1])
        recs.append({"k": "CIRCULAR_ARC", "c": _p(c, k), "r": quantise(r * k, REALISED_QUANTUM),
                     "e": sorted([_p(arc["P0"], k), _p(arc["P1"], k)]), "m": _p(arc["PM"], k)})
    for bl in phys.get("bulges", []):
        c = bl["CENTER"]
        r = math.hypot(bl["VERTEX_A"][0] - c[0], bl["VERTEX_A"][1] - c[1])
        recs.append({"k": "CIRCULAR_ARC", "c": _p(c, k), "r": quantise(r * k, REALISED_QUANTUM),
                     "e": sorted([_p(bl["VERTEX_A"], k), _p(bl["VERTEX_B"], k)]), "m": _p(bl["ARC_MIDPOINT"], k)})
    # kinds added in R8.1; absent from the R8.0 golden scenes, so the vectors are unchanged
    for c in phys.get("circles", []):
        recs.append({"k": "CIRCLE", "c": _p(c["CENTER"], k), "r": quantise(c["RADIUS"] * k, REALISED_QUANTUM)})
    for e in phys.get("elliptical_arcs", []):
        major, minor_len = principal_axes(e["AXIS_U"], e["AXIS_V"])
        recs.append({"k": "ELLIPTICAL_ARC", "c": _p(e["CENTER"], k), "m": _p(e["MID_SWEEP_POINT"], k),
                     "e": sorted([_p(e["START_POINT"], k), _p(e["END_POINT"], k)]),
                     "major": _p(major, k), "minor": quantise(minor_len * k, REALISED_QUANTUM),
                     "full": bool(e.get("FULL"))})
    return recs


def principal_axes(u, v):
    """Canonical (semi-major vector, semi-minor length) of C + cos t*u + sin t*v.

    Conjugate semi-diameters are not unique for one ellipse; its principal
    axes are, so the digest does not depend on the parameterisation. The
    semi-major vector is normalised to point into x > 0 (or +y when x = 0)."""
    a00 = u[0] * u[0] + v[0] * v[0]
    a11 = u[1] * u[1] + v[1] * v[1]
    a01 = u[0] * u[1] + v[0] * v[1]
    tr, dt = a00 + a11, a00 * a11 - a01 * a01
    disc = math.sqrt(max(tr * tr / 4.0 - dt, 0.0))
    l1, l2 = tr / 2.0 + disc, max(tr / 2.0 - disc, 0.0)
    phi = 0.5 * math.atan2(2.0 * a01, a00 - a11)
    dx, dy = math.cos(phi), math.sin(phi)
    if dx < 0 or (dx == 0 and dy < 0):
        dx, dy = -dx, -dy
    a = math.sqrt(l1)
    return (dx * a, dy * a), math.sqrt(l2)


def realised_geometry_digest(realised, unit_to_mm) -> str:
    return hashlib.sha256("\n".join([RGD_PREFIX] + _lines(realised_records(realised, unit_to_mm))).encode()).hexdigest()
