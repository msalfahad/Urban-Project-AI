"""CONCRETE CURVED STRIPS - wall strips drawn as concentric curved edges (bulge polylines, ARCs, CIRCLEs).

Why: the frozen strip builder (concrete_completeness._describe_group / _parallel_pairs) pairs straight LINEs only, so a
wall drawn with arcs (a D-shaped or round pool, a curved retaining wall) loses its curved part. This module is a NEW
method piece that measures that curved part. It is not wired into any released method; the frozen builder is unchanged.

Rules
  UP-KB-PREC-001  as drawn: every number comes from the drawn edges (radius, centre, sweep), never from a default.
  UP-WALL-GEOM-001  curved stubs are wall: a concentric pair of curved edges at a wall width is a wall strip.
  UP-QTY-STATUS-001  every curved edge is reported once: MEASURED (in a strip), HELD (with a reason) or UNSUPPORTED.
                     A curve the method cannot pair is HELD, never dropped and never 0.

Input curves (drawing units; `unit_m` = metres per drawing unit, e.g. 0.001 for a drawing in mm)
  {"type": "ARC", "c": (x, y), "r": r, "start": deg, "end": deg, "extrusion": (0, 0, +-1)}   DXF ARC in its OCS
  {"type": "ARC", "c": (x, y), "r": r, "s": (x, y), "m": (x, y), "e": (x, y)}               intake arc (3 points)
  {"type": "CIRCLE", "c": (x, y), "r": r, "extrusion": ...}
  {"type": "LWPOLYLINE", "points": [(x, y, bulge), ...], "closed": bool, "extrusion": ...}
  Every curve may carry "id" and "layer". A polyline's straight segments are not curves: they are counted in
  `straight_segments` and left to the straight-line builder.

Bulge (DXF): bulge b = tan(theta / 4), theta the included angle, b > 0 counter-clockwise from vertex i to i + 1.
  chord L, centre = chord midpoint + left normal x (L / 2) x (1 - b^2) / (2 b), radius = L (1 + b^2) / (4 |b|).
  A -Z extrusion maps an OCS point (x, y) to the world point (-x, y) and reverses the turning direction.

Pairing (per concentric group: centres within `centre_tol_m`, the same 1 mm as arch_v28.curved_stubs)
  Two radii r1 < r2 are partners when wmin <= r2 - r1 <= wmax and their angular coverages overlap. A radius with two or
  more partners is ambiguous: its curves are HELD CURVED_STRIP_AMBIGUOUS (no guess which pair is the wall). A strip
  exists where both edges are drawn (curved_member_geometry.band_segments): plan area = annular sector
  sweep / 2 x (r2^2 - r1^2), length on the centreline (r1 + r2) / 2 x sweep. Edge sweep not covered by the other edge
  is HELD CURVED_STRIP_UNPAIRED with its arc length.

Nothing here names a project, a sheet, a layer or a handle.
"""

from __future__ import annotations

import math

from engine.source import curved_member_geometry as CG

METHOD = "CONCRETE_CURVED_STRIPS_V1"
RULES = ("UP-KB-PREC-001", "UP-WALL-GEOM-001", "UP-QTY-STATUS-001")
CENTRE_TOL_M = 1e-3            # concentric test, as arch_v28.curved_stubs (1 mm)
RADIUS_TOL_M = 1e-6            # two edges with radii closer than this are one edge
BULGE_MIN = 1e-12              # |bulge| below this is a straight segment (DXF bulge 0)


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _pt(p):
    return p is not None and len(p) >= 2 and _num(p[0]) and _num(p[1])


def _flip(ext):
    """True for a -Z extrusion, False for +Z; anything else is not planar here."""
    ex = tuple(float(v) for v in (ext or (0.0, 0.0, 1.0)))
    if len(ex) != 3 or abs(ex[0]) > 1e-9 or abs(ex[1]) > 1e-9 or abs(abs(ex[2]) - 1.0) > 1e-9:
        raise CG.CurvedGeometryError(f"extrusion {ext} is not +Z or -Z")
    return ex[2] < 0


def bulge_arc(p1, p2, bulge):
    """one polyline segment with a bulge -> a CCW world arc {"c", "r", "start", "sweep"} (same units as the points)."""
    if not (_pt(p1) and _pt(p2) and _num(bulge)) or abs(bulge) < BULGE_MIN:
        raise CG.CurvedGeometryError("not a curved segment")
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    L = math.hypot(dx, dy)
    if L <= 0:
        raise CG.CurvedGeometryError("zero-length chord")
    b = float(bulge)
    k = (L / 2.0) * (1.0 - b * b) / (2.0 * b)
    cx, cy = (p1[0] + p2[0]) / 2.0 - dy / L * k, (p1[1] + p2[1]) / 2.0 + dx / L * k
    r = L * (1.0 + b * b) / (4.0 * abs(b))
    sweep = math.degrees(4.0 * math.atan(abs(b)))
    first = p1 if b > 0 else p2
    start = CG.norm_deg(math.degrees(math.atan2(first[1] - cy, first[0] - cx)))
    return {"c": (cx, cy), "r": r, "start": start, "sweep": sweep}


def _three_point_arc(c, r, s, m, e):
    ang = lambda p: CG.norm_deg(math.degrees(math.atan2(p[1] - c[1], p[0] - c[0])))     # noqa: E731
    a0, am, a1 = ang(s), ang(m), ang(e)
    sw = CG.norm_deg(a1 - a0)
    if sw < CG.TOL:
        return {"c": tuple(c), "r": r, "start": 0.0, "sweep": 360.0}
    if CG.norm_deg(am - a0) > sw:                       # the mid point is on the other side: clockwise from s to e
        return {"c": tuple(c), "r": r, "start": a1, "sweep": 360.0 - sw}
    return {"c": tuple(c), "r": r, "start": a0, "sweep": sw}


def world_curves(curve):
    """one input curve -> ([world arc in drawing units, ...], straight segment count). Raises on bad data."""
    t = (curve.get("type") or "").upper()
    if t in ("ARC", "CIRCLE"):
        c, r = curve.get("c"), curve.get("r")
        if not (_pt(c) and _num(r)) or r <= 0:
            raise CG.CurvedGeometryError("arc without a centre or a positive radius")
        if t == "CIRCLE":
            return [CG.world_arc(c[:2], r, extrusion=curve.get("extrusion") or (0, 0, 1), full=True)], 0
        if all(_pt(curve.get(k)) for k in ("s", "m", "e")):
            return [_three_point_arc(c[:2], float(r), curve["s"], curve["m"], curve["e"])], 0
        if _num(curve.get("start")) and _num(curve.get("end")):
            return [CG.world_arc(c[:2], r, curve["start"], curve["end"], curve.get("extrusion") or (0, 0, 1))], 0
        raise CG.CurvedGeometryError("arc without start / end angles or start / mid / end points")
    if t in ("LWPOLYLINE", "POLYLINE"):
        pts = curve.get("points") or []
        if len(pts) < 2:
            raise CG.CurvedGeometryError("polyline with fewer than two vertices")
        flip = _flip(curve.get("extrusion"))
        verts = []
        for p in pts:
            if not _pt(p):
                raise CG.CurvedGeometryError("polyline vertex without x / y")
            b = p[2] if len(p) > 2 and p[2] is not None else 0.0
            if not _num(b):
                raise CG.CurvedGeometryError("polyline vertex with a bad bulge")
            verts.append(((-p[0], p[1]) if flip else (p[0], p[1]), -b if flip else b))
        n = len(verts) if curve.get("closed") else len(verts) - 1
        arcs, straight = [], 0
        for i in range(n):
            (p1, b), (p2, _) = verts[i], verts[(i + 1) % len(verts)]
            if abs(b) < BULGE_MIN:
                straight += 1
            elif math.dist(p1, p2) > 0:
                arcs.append(bulge_arc(p1, p2, b))
        return arcs, straight
    raise CG.CurvedGeometryError(f"curve type {t or '?'} is not supported here")


def _held(reason, edge, sweep, **extra):
    rec = {"status": "HELD", "reason": reason, "id": edge["id"], "layer": edge["layer"], "r_m": round(edge["r"], 6),
           "centre": edge["c"], "sweep_deg": round(sweep, 9), "length_m": round(edge["r"] * math.radians(sweep), 6),
           "method": METHOD, "rules": list(RULES)}
    rec.update(extra)
    return rec


def _subtract(intervals, cut):
    """angular intervals minus cut (both [(start, sweep)]) -> [(start, sweep)]."""
    out = []
    for s, w in CG.merge_intervals(intervals):
        pieces = [(s, s + w)]
        for c0, cw in CG.merge_intervals(cut) if cut else []:
            for k in (-360.0, 0.0, 360.0):
                lo, hi = c0 + k, c0 + k + cw
                nxt = []
                for a, b in pieces:
                    if hi <= a + CG.TOL or lo >= b - CG.TOL:
                        nxt.append((a, b))
                        continue
                    if lo > a + CG.TOL:
                        nxt.append((a, lo))
                    if hi < b - CG.TOL:
                        nxt.append((hi, b))
                pieces = nxt
        out.extend((CG.norm_deg(a), b - a) for a, b in pieces if b - a > 1e-7)
    return out


def curved_strips(curves, unit_m, strip_width_m, centre_tol_m=CENTRE_TOL_M):
    """curves (drawing units) -> {"strips": [...], "held": [...], "unsupported": [...], "straight_segments": n,
    "totals": {...}}. strip_width_m = (wmin, wmax) in metres, from the profile (STRIP_WIDTH_M); never defaulted here.
    Every curve appears once: in a strip, as HELD or as UNSUPPORTED. Missing data never becomes 0."""
    res = {"method": METHOD, "rules": list(RULES), "strips": [], "held": [], "unsupported": [], "straight_segments": 0}
    curves = list(curves or [])
    ok_unit = _num(unit_m) and unit_m > 0
    ok_w = (strip_width_m is not None and len(strip_width_m) == 2 and all(_num(w) for w in strip_width_m)
            and 0 < strip_width_m[0] <= strip_width_m[1])
    if not (ok_unit and ok_w):
        reason = "UNIT_UNKNOWN" if not ok_unit else "STRIP_WIDTH_UNKNOWN"
        res["unsupported"] = [{"status": "UNSUPPORTED", "reason": reason, "id": c.get("id"), "layer": c.get("layer"),
                               "method": METHOD} for c in curves]
        res["totals"] = None
        return res
    wmin, wmax = strip_width_m
    edges = []                                          # world arcs in metres
    for i, c in enumerate(curves):
        cid = c.get("id", f"curve{i}")
        try:
            arcs, straight = world_curves(c)
        except (CG.CurvedGeometryError, TypeError, ValueError) as exc:
            res["unsupported"].append({"status": "UNSUPPORTED", "reason": "BAD_CURVE_DATA", "detail": str(exc),
                                       "id": cid, "layer": c.get("layer"), "method": METHOD})
            continue
        res["straight_segments"] += straight
        for k, a in enumerate(arcs):
            edges.append({"id": cid if len(arcs) == 1 else f"{cid}#{k}", "layer": c.get("layer"),
                          "c": (a["c"][0] * unit_m, a["c"][1] * unit_m), "r": a["r"] * unit_m,
                          "start": a["start"], "sweep": a["sweep"]})
    # concentric groups, then one edge per radius (several arcs on one circle are covered once)
    groups = []
    for e in edges:
        for g in groups:
            if math.dist(g[0]["c"], e["c"]) <= centre_tol_m:
                g.append(e)
                break
        else:
            groups.append([e])
    for g in groups:
        rings = []
        for e in sorted(g, key=lambda x: x["r"]):
            if rings and abs(rings[-1]["r"] - e["r"]) <= RADIUS_TOL_M:
                rings[-1]["arcs"].append(e)
            else:
                rings.append({"r": e["r"], "arcs": [e]})
        for rg in rings:
            rg["iv"] = CG.merge_intervals([(a["start"], a["sweep"]) for a in rg["arcs"]])
        partners = {i: [] for i in range(len(rings))}
        for i, a in enumerate(rings):
            for j in range(i + 1, len(rings)):
                w = rings[j]["r"] - a["r"]
                if wmin - 1e-9 <= w <= wmax + 1e-9 and CG.intersect_intervals(a["iv"], rings[j]["iv"]):
                    partners[i].append(j)
                    partners[j].append(i)
        covered = {i: [] for i in range(len(rings))}
        ambiguous = {i for i, p in partners.items() if len(p) > 1}
        ambiguous |= {j for i in ambiguous for j in partners[i]}
        for i in range(len(rings)):
            for j in partners[i]:
                if j < i or i in ambiguous or j in ambiguous:
                    continue
                inner, outer = rings[i], rings[j]
                segs = CG.band_segments([{"c": x["c"], "r": inner["r"], "start": x["start"], "sweep": x["sweep"]}
                                         for x in inner["arcs"]],
                                        [{"c": x["c"], "r": outer["r"], "start": x["start"], "sweep": x["sweep"]}
                                         for x in outer["arcs"]], ctol=centre_tol_m)
                for s in segs:
                    res["strips"].append({
                        "status": "MEASURED", "kind": "CURVED_STRIP", "centre": inner["arcs"][0]["c"],
                        "r_inner_m": round(s["r1"], 6), "r_outer_m": round(s["r2"], 6),
                        "strip_width_m": round(s["width"], 6), "start_deg": round(s["start"], 9),
                        "sweep_deg": round(s["sweep"], 9), "strip_length_m": round(s["centreline_length"], 6),
                        "area_m2": round(s["area"], 6),
                        "edges": sorted({x["id"] for x in inner["arcs"] + outer["arcs"]}),
                        "layers": sorted({str(x["layer"]) for x in inner["arcs"] + outer["arcs"]}),
                        "method": METHOD, "rules": list(RULES)})
                    covered[i].append((s["start"], s["sweep"]))
                    covered[j].append((s["start"], s["sweep"]))
        for i, rg in enumerate(rings):
            for a in rg["arcs"]:
                if i in ambiguous:
                    res["held"].append(_held("CURVED_STRIP_AMBIGUOUS", a, a["sweep"],
                                             partner_radii_m=[round(rings[j]["r"], 6) for j in partners[i]]))
                    continue
                for s, w in _subtract([(a["start"], a["sweep"])], covered[i]):
                    res["held"].append(_held("CURVED_STRIP_UNPAIRED", a, w, start_deg=round(s, 9)))
    res["totals"] = {"strip_area_m2": round(sum(s["area_m2"] for s in res["strips"]), 6),
                     "strip_length_m": round(sum(s["strip_length_m"] for s in res["strips"]), 6),
                     "n_strips": len(res["strips"]), "n_held": len(res["held"]),
                     "n_unsupported": len(res["unsupported"])}
    return res
