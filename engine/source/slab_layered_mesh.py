"""SLAB LAYERED MESH - plan callouts, thickness tags and top / bottom rate meshes on straight-edged slab panels (generic).

Reading a plan
  parse_rate_callout(text)     'N%%cD/m' -> {count N, dia_mm D, basis PER_M}; 'N%%cD/Top' -> {count, dia_mm, basis COUNT,
                               layer TOP}. A text without a bar symbol is never a bar: 'T 18', 'T', '18' and '(T&B)'
                               return None.
  parse_layer_qualifier(text)  '(T&B)' -> (BOTTOM, TOP); '(T)' / 'TOP' -> (TOP,); '(B)' / 'BOTTOM' -> (BOTTOM,); else
                               None. A lone 'T' or 'B' counts only in brackets (a bare 'T' is a thickness tag's
                               letter). A layer qualifier names faces only; it never states a plan direction.
  thickness_tag(texts, centre, radius)
                               a closed circle holding exactly one 'T' and one whole number n (5 <= n <= 100) is a slab
                               thickness of n cm -> {thickness_mm: 10 n}; anything else -> None. Never a bar diameter.
  baseline_direction(rotation) a text running along x -> X, along y -> Y, otherwise None.
  bind_to_bar_graphic(point, rotation, lines, max_offset, group_gap)
                               the drawn bar line(s) parallel to the text baseline nearest the text: the nearest line
                               and any parallel line within group_gap of it (a double line is one graphic). The text's
                               projection must fall on the line's extent. None when nothing is within max_offset.

A mesh on a straight-edged panel (polygon points in mm; edge i runs from points[i] to points[i + 1])
  Bars of direction X run along x and are distributed across y; bars of direction Y run along y across x.
  band_ends(points, direction) cuts the panel into bands of the distribution coordinate at every vertex. For each band
     it gives the width, the integral of the bar run over the band (exact for straight edges), the mean run and, for
     every interval inside the band, the edge the bars start on and the edge they end on.
  layer_quantity(points, direction, rate_per_m, dia_mm, end_class, stop=None)
     one layer of one bar family. full = rate x sum(band integral) = rate x area (never rounded, never +1). With a stop
     rule {ratio, fraction, classes}, every band end on an edge whose class is in classes carries a stop zone of
     ratio x fraction x rate x (band integral): the ratio is applied to the local run of each bar line. Stop zones are
     kept apart and reported, never netted silently: released = full - stop zones.
  edge_zone_length(points, direction, edges, ratio, rate_per_m)
     rate x ratio x sum(band integral) over every band end on the given edges (a bar reaching ratio x the local run
     from the face of those edges).

Stdlib + engine.source.slab_rebar_qto only. No project data.
"""

from __future__ import annotations

import math
import re

from engine.source import slab_rebar_qto as SR

X = "X"
Y = "Y"
DIRECTIONS = (X, Y)
TOP = "TOP"
BOTTOM = "BOTTOM"
PER_M = "PER_M"
COUNT = "COUNT"
TOL = 1e-9

_BAR = r"(?:%%[cC]|[ØøΦφ])"
_RATE = re.compile(r"^\s*(\d+)\s*" + _BAR + r"\s*(\d+)\s*/\s*(m|M|top|Top|TOP)\s*$")
_QUAL = {"T&B": (BOTTOM, TOP), "B&T": (BOTTOM, TOP), "TOP": (TOP,), "BOT": (BOTTOM,), "BOTTOM": (BOTTOM,)}
_QUAL_BRACKETED = {**_QUAL, "T": (TOP,), "B": (BOTTOM,)}      # a lone letter counts only inside brackets


class SlabLayeredMeshError(ValueError):
    pass


# ------------------------------------------------------------------ plan reading
def parse_rate_callout(text):
    """A bar callout: 'N<bar symbol>D/m' (rate per metre) or 'N<bar symbol>D/Top' (explicit count, top). None if the
    text is not a bar callout (no bar symbol, no '/m' or '/Top')."""
    m = _RATE.match(text or "")
    if not m:
        return None
    n, d, tail = int(m.group(1)), int(m.group(2)), m.group(3).upper()
    if n <= 0 or d <= 0:
        return None
    if tail == "M":
        return {"count": n, "dia_mm": d, "basis": PER_M, "layer": None}
    return {"count": n, "dia_mm": d, "basis": COUNT, "layer": TOP}


def parse_layer_qualifier(text):
    """Faces named by a stand-alone qualifier such as '(T&B)'. Returns a tuple of faces or None. It never returns a
    plan direction: '(T&B)' says top and bottom, not X and Y."""
    s = (text or "").strip()
    table = _QUAL
    if s.startswith("(") and s.endswith(")"):
        s, table = s[1:-1], _QUAL_BRACKETED
    s = re.sub(r"\s+", "", s).upper()
    return table.get(s)


def thickness_tag(texts, centre, radius):
    """texts: [(text, (x, y))]. Exactly one 'T' and one whole number inside the circle -> a slab thickness."""
    inside = [(t or "").strip() for t, p in texts if math.dist(p, centre) <= radius]
    inside = [t for t in inside if t]
    letters = [t for t in inside if t.upper() == "T"]
    num = [t for t in inside if t.isdigit()]
    if len(inside) != 2 or len(letters) != 1 or len(num) != 1:
        return None
    n = int(num[0])
    if not 5 <= n <= 100:
        return None
    return {"thickness_mm": 10 * n, "value_cm": n}


def baseline_direction(rotation_deg, tol_deg=1.0):
    r = float(rotation_deg) % 180.0
    if min(r, 180.0 - r) <= tol_deg:
        return X
    if abs(r - 90.0) <= tol_deg:
        return Y
    return None


def _line_direction(a, b, tol_deg=1.0):
    ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    return baseline_direction(ang, tol_deg)


def bind_to_bar_graphic(point, rotation_deg, lines, *, max_offset=400.0, group_gap=150.0):
    """lines: [(handle, a, b)]. The nearest bar line parallel to the text baseline whose extent covers the text's
    projection, plus every parallel line within group_gap of it. Returns {direction, handles, offset} or None."""
    d = baseline_direction(rotation_deg)
    if d is None:
        return None
    k = 0 if d == X else 1                       # coordinate along the bar
    cand = []
    for h, a, b in lines:
        if _line_direction(a, b) != d:
            continue
        lo, hi = sorted((a[k], b[k]))
        if not lo - TOL <= point[k] <= hi + TOL:
            continue
        off = abs(point[1 - k] - a[1 - k])
        if off <= max_offset:
            cand.append((off, h, a[1 - k]))
    if not cand:
        return None
    cand.sort()
    off0, _, pos0 = cand[0]
    group = sorted(h for off, h, pos in cand if abs(pos - pos0) <= group_gap)
    return {"direction": d, "handles": group, "offset": off0}


# ------------------------------------------------------------------ mesh on a straight-edged panel
def _check_polygon(points):
    if len(points) < 3:
        raise SlabLayeredMeshError("a panel needs at least three points")
    a = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
        a += x0 * y1 - x1 * y0
    if abs(a) <= TOL:
        raise SlabLayeredMeshError("degenerate panel")
    return abs(a) / 2.0


def polygon_area(points):
    return _check_polygon(points)


def band_ends(points, direction):
    """[{t0, t1, width_mm, integral_mm2, run_mm, ends: [(start_edge, end_edge, integral_mm2)]}] for one direction."""
    if direction not in DIRECTIONS:
        raise SlabLayeredMeshError(f"direction must be one of {DIRECTIONS}: {direction!r}")
    _check_polygon(points)
    pts = [(float(x), float(y)) for x, y in points] if direction == X else [(float(y), float(x)) for x, y in points]
    edges = list(zip(pts, pts[1:] + pts[:1]))
    ts = sorted({round(p[1], 9) for p in pts})
    out = []
    for t0, t1 in zip(ts, ts[1:]):
        if t1 - t0 <= TOL:
            continue
        tm = (t0 + t1) / 2.0
        cr = []
        for i, ((xa, ya), (xb, yb)) in enumerate(edges):
            if (ya < tm < yb) or (yb < tm < ya):
                def xat(t, xa=xa, ya=ya, xb=xb, yb=yb):
                    return xa + (t - ya) * (xb - xa) / (yb - ya)
                cr.append((xat(tm), i, (xat(t0) + xat(t1)) / 2.0))
        if len(cr) % 2:
            raise SlabLayeredMeshError(f"odd crossing count at {direction} t = {tm}")
        cr.sort()
        ends = []
        for k in range(0, len(cr), 2):
            integ = (cr[k + 1][2] - cr[k][2]) * (t1 - t0)          # mean chord x width (exact for straight edges)
            if integ <= TOL:
                continue
            ends.append((cr[k][1], cr[k + 1][1], integ))
        if not ends:
            continue
        integ = math.fsum(e[2] for e in ends)
        out.append({"t0": t0, "t1": t1, "width_mm": t1 - t0, "integral_mm2": integ, "run_mm": integ / (t1 - t0),
                    "ends": ends})
    return out


def layer_quantity(points, direction, rate_per_m, dia_mm, end_class, stop=None):
    """One layer of one bar family over a panel. end_class: {edge index: class}. stop: None or {ratio, fraction,
    classes}. Returns full / stop zones / released equivalent lengths (m) and kg, and the band rows."""
    bands = band_ends(points, direction)
    area = polygon_area(points)
    q = SR.rate_strip_length(rate_per_m, [(b["width_mm"], b["run_mm"]) for b in bands])
    if abs(q["integral_m2"] * 1e6 - area) > 1e-6 * max(area, 1.0):
        raise SlabLayeredMeshError("strip integral does not cover the panel")
    if stop is not None:
        ratio, fraction = float(stop["ratio"]), float(stop["fraction"])
        if not (0.0 < ratio <= 0.5 and 0.0 < fraction <= 1.0):
            raise SlabLayeredMeshError(f"stop rule out of range: {stop!r}")
        classes = set(stop["classes"])
    zones, rows = [], []
    for j, b in enumerate(bands):
        for s, e, integ in b["ends"]:
            row = {"band": j, "t0": b["t0"], "t1": b["t1"], "width_mm": b["width_mm"], "integral_mm2": integ,
                   "start_edge": s, "end_edge": e, "start_class": end_class.get(s), "end_class": end_class.get(e),
                   "stop_m": 0.0}
            if stop is not None:
                for side, edge in (("START", s), ("END", e)):
                    if end_class.get(edge) in classes:
                        L = ratio * fraction * float(rate_per_m) * integ / 1e6
                        zones.append({"band": j, "side": side, "edge": edge, "class": end_class.get(edge),
                                      "length_m": L})
                        row["stop_m"] += L
            rows.append(row)
    full = q["length_m"]
    stop_m = math.fsum(z["length_m"] for z in zones)
    um = SR.unit_mass(dia_mm)
    return {"direction": direction, "rate_per_m": float(rate_per_m), "dia_mm": float(dia_mm), "area_m2": area / 1e6,
            "distribution_width_m": q["width_m"], "equivalent_count": q["equivalent_count"],
            "mean_run_m": q["mean_run_m"], "full_m": full, "stop_zone_m": stop_m, "released_m": full - stop_m,
            "unit_mass_kg_m": um, "full_kg": full * um, "stop_zone_kg": stop_m * um,
            "released_kg": (full - stop_m) * um, "stop_zones": zones, "bands": rows,
            "physical_bbs_count": q["physical_bbs_count"]}


def edge_zone_length(points, direction, edges, ratio, rate_per_m):
    """rate x ratio x sum of band integrals over the band ends on the given edges (m)."""
    if not 0.0 < float(ratio) <= 1.0:
        raise SlabLayeredMeshError(f"ratio out of range: {ratio!r}")
    if float(rate_per_m) <= 0:
        raise SlabLayeredMeshError(f"rate must be positive: {rate_per_m!r}")
    edges = set(edges)
    tot = []
    for b in band_ends(points, direction):
        for s, e, integ in b["ends"]:
            tot.extend(integ for edge in (s, e) if edge in edges)
    return float(rate_per_m) * float(ratio) * math.fsum(tot) / 1e6
