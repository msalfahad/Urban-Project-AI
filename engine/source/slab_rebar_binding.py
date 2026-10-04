"""SLAB REBAR BINDING (V3b) - bind slab reinforcement annotations to drawn bars and to the panel they reinforce.

Generic for plan-drawn slab reinforcement (one annotation per bar family, e.g. "5Ø10/m", "8Ø16/m", "3Ø14", "4Ø16/Top"):

    parse(text)                          -> {"kind": PER_M | COUNT, "n", "dia_mm", "top", "both_ways"} or None
    ray_hit(p, d, segments, ...)         -> distance from p along unit d to the first support line (None = open)
    bind(annotations, bars, supports)    -> one record per annotation

Binding (never nearest text alone):
  1. the bar direction is the annotation direction (text rotation); a drawn bar is a candidate only when it is parallel
     (within ANGLE_TOL) and the annotation lies within BIND_DIST of it, its projection inside the bar's extent;
     the closest candidate wins, a tie within TIE_MM is AMBIGUOUS (candidates kept);
  2. distribution width = clear distance between the support lines hit by two rays cast perpendicular to the bar
     from its midpoint (from the annotation point when the panel carries text only);
  3. PER_M: count = floor(width / spacing) + 1 with spacing = 1 m / n; COUNT: n bars;
  4. the drawn bar is a SYMBOL (its drawn length is schematic): the bar length is the clear span between the supports
     along the bar direction (rays from the bar midpoint) plus an embedment into each support; the support width is
     the distance from its near face to its far face (a second ray hit, <= MAX_SUPPORT); embedment = support width
     - cover (EMBED_RULE, a detailing rule recorded on every record, never hidden); a support whose far face is not
     found gives anchorage state OPEN and the record is PARTIAL (clear span only);
  5. Route B (check): the drawn bar length vs the clear span is reported, never used as the quantity.

Diagonal (corner) bars are bars like any other: their direction is their own angle. A record whose width or span is
open (a ray found no support) is UNBOUND, never estimated - except a COUNT annotation bound to a drawn bar whose span
rays are open (an edge / cantilever bar outside the panel grid): DRAWN_EXTENT, length = the drawn developed length of
the bar (a polyline bar with its bends), reported as such for the caller to label.
A drawn bar may be a polyline ("path": [(x, y), ...]): its direction is its longest leg, its drawn length the developed
length of the path.
dedupe(records): a later annotation with the same bar family (kind, n, Ø, top) and direction over the same panel
(the clear panel rectangle in the bar frame, rounded to PANEL_ROUND) is DUPLICATE_LABEL and never counted.
Units: model units (mm). Stdlib only, project-agnostic.
"""

from __future__ import annotations

import hashlib
import json
import math
import re

POLICY_ID = "SLAB_REBAR_BINDING_V1"
ANGLE_TOL_DEG = 8.0
BIND_DIST = 700.0
TIE_MM = 50.0
MIN_HIT = 30.0
MAX_RAY = 15000.0
MAX_SUPPORT = 600.0
EMBED_RULE = "BAR_TO_FAR_SUPPORT_FACE_LESS_COVER"
PANEL_ROUND = 50.0
RE_PER_M = re.compile(r"^\s*(\d+)\s*(?:%%[cC]|[ØøΦφ])\s*(\d+)\s*/\s*m\b", re.I)
RE_COUNT = re.compile(r"^\s*(\d+)\s*(?:%%[cC]|[ØøΦφ])\s*(\d+)\s*(/\s*top)?\s*$", re.I)


def parse(text):
    t = (text or "").strip()
    m = RE_PER_M.match(t)
    if m:
        return {"kind": "PER_M", "n": int(m[1]), "dia_mm": int(m[2]), "top": "TOP" in t.upper(),
                "both_ways": "E.W" in t.upper()}
    m = RE_COUNT.match(t)
    if m:
        return {"kind": "COUNT", "n": int(m[1]), "dia_mm": int(m[2]), "top": bool(m[3]), "both_ways": False}
    return None


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return (dx / L, dy / L) if L else (0.0, 0.0)


def _ang(u, v):
    c = abs(u[0] * v[0] + u[1] * v[1])
    return math.degrees(math.acos(min(1.0, c)))


def ray_hit(p, d, segments, min_t=MIN_HIT, max_t=MAX_RAY):
    """Smallest t > min_t with p + t d on a segment ((x0, y0, x1, y1)); None when nothing is hit within max_t."""
    best = None
    for x0, y0, x1, y1 in segments:
        ex, ey = x1 - x0, y1 - y0
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-12:
            continue
        qx, qy = x0 - p[0], y0 - p[1]
        t = (qx * ey - qy * ex) / den
        s = (qx * d[1] - qy * d[0]) / den
        if min_t < t <= max_t and -1e-9 <= s <= 1 + 1e-9 and (best is None or t < best):
            best = t
    return best


def _clear(p, d, supports):
    a = ray_hit(p, d, supports)
    b = ray_hit(p, (-d[0], -d[1]), supports)
    return (a + b) if (a is not None and b is not None) else None, a, b


def support_width(p, d, t_near, supports):
    """Width of the support whose near face is at p + t_near d: the next line hit beyond it (<= MAX_SUPPORT)."""
    if t_near is None:
        return None
    q = (p[0] + d[0] * t_near, p[1] + d[1] * t_near)
    w = ray_hit(q, d, supports, min_t=MIN_HIT, max_t=MAX_SUPPORT)
    return w


def _count(kind, n, width_mm):
    if kind == "COUNT":
        return n
    s = 1000.0 / n
    return int(math.floor(width_mm / s + 1e-9)) + 1


def bind(annotations, bars, supports, cover_mm=25.0) -> list:
    """annotations [{"id", "text", "x", "y", "rotation_deg"}]; bars [{"id", "x0", "y0", "x1", "y1"}];
    supports [(x0, y0, x1, y1)] beam / slab-edge lines the reinforcement spans between."""
    out = []
    for a in annotations:
        sp = parse(a["text"])
        if sp is None:
            continue
        th = math.radians(a.get("rotation_deg") or 0.0)
        dt = (math.cos(th), math.sin(th))
        p = (a["x"], a["y"])
        cands = []
        for b in bars:
            pa, pb = _leg(b)
            u = _unit(pa, pb)
            if u == (0.0, 0.0) or _ang(u, dt) > ANGLE_TOL_DEG:
                continue
            L = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
            tproj = (p[0] - pa[0]) * u[0] + (p[1] - pa[1]) * u[1]
            if not (-BIND_DIST <= tproj <= L + BIND_DIST):
                continue
            dist = abs((p[0] - pa[0]) * u[1] - (p[1] - pa[1]) * u[0])
            if dist <= BIND_DIST:
                cands.append((dist + max(0.0, -tproj, tproj - L), b, u, L))
        cands.sort(key=lambda c: (c[0], c[1]["id"]))
        rec = {"annotation": a["id"], "text": a["text"].strip(), **sp, "candidates": [c[1]["id"] for c in cands[:3]]}
        if cands and len(cands) > 1 and cands[1][0] - cands[0][0] < TIE_MM and cands[1][3] != cands[0][3]:
            rec.update(state="AMBIGUOUS", why="two drawn bars within the tie distance")
            out.append(rec)
            continue
        if cands:
            _, b, u, L = cands[0]
            pa, pb = _leg(b)
            q = ((pa[0] + pb[0]) / 2.0, (pa[1] + pb[1]) / 2.0)
            rec.update(bar=b["id"], binding="DRAWN_BAR", drawn_length_mm=_developed(b))
        else:
            u, q = dt, p
            rec.update(bar=None, binding="TEXT_ONLY_PANEL", drawn_length_mm=None)
        n_ = (-u[1], u[0])
        width, a1, a2 = _clear(q, n_, supports)
        span, s1, s2 = _clear(q, u, supports)
        if span is not None and width is not None:
            cu = _canon(u)
            cn = (-cu[1], cu[0])
            pu = sorted((q[0] + u[0] * t) * cu[0] + (q[1] + u[1] * t) * cu[1] for t in (s1, -s2))
            pn = sorted((q[0] + n_[0] * t) * cn[0] + (q[1] + n_[1] * t) * cn[1] for t in (a1, -a2))
            rec["panel"] = [round(v / PANEL_ROUND) for v in pu + pn]
        w1 = support_width(q, u, s1, supports)
        w2 = support_width(q, (-u[0], -u[1]), s2, supports)
        rec.update(direction=[round(u[0], 6), round(u[1], 6)], width_mm=width, clear_span_mm=span,
                   support_widths_mm=[w1, w2], embed_rule=EMBED_RULE, cover_mm=cover_mm)
        if span is None and sp["kind"] == "COUNT" and rec["binding"] == "DRAWN_BAR":
            rec.update(state="DRAWN_EXTENT", count=sp["n"], length_mm=rec["drawn_length_mm"], anchorage="AS_DRAWN",
                       why="count bar outside the panel grid: drawn developed length (not dimensioned)")
            rec["total_length_m"] = rec["count"] * rec["length_mm"] / 1000.0
            out.append(rec)
            continue
        if span is None or (sp["kind"] == "PER_M" and width is None):
            rec.update(state="UNBOUND", why="a ray found no support line (open panel) - not estimated")
            out.append(rec)
            continue
        rec["count"] = _count(sp["kind"], sp["n"], width or 0.0)
        if w1 is not None and w2 is not None:
            rec["embed_mm"] = [w1 - cover_mm, w2 - cover_mm]
            rec["length_mm"] = span + rec["embed_mm"][0] + rec["embed_mm"][1]
            rec["anchorage"] = "BOTH_SUPPORTS_MEASURED"
            rec["state"] = "BOUND" if rec["binding"] == "DRAWN_BAR" else "BOUND_TEXT_ONLY"
        else:
            rec["embed_mm"] = [None if w1 is None else w1 - cover_mm, None if w2 is None else w2 - cover_mm]
            rec["length_mm"] = span
            rec["anchorage"] = "OPEN"
            rec["state"] = "PARTIAL"
        rec["total_length_m"] = rec["count"] * rec["length_mm"] / 1000.0
        if rec.get("drawn_length_mm"):
            rec["route_b_drawn_vs_span"] = {"drawn_mm": rec["drawn_length_mm"], "clear_span_mm": span,
                                           "note": "drawn bar is a symbol; never the quantity"}
        out.append(rec)
    return out


def _canon(u):
    return (u[0], u[1]) if (u[0] > 1e-9 or (abs(u[0]) <= 1e-9 and u[1] > 0)) else (-u[0], -u[1])


def _leg(b):
    """The bar's governing leg: the segment itself, or the longest leg of a polyline path."""
    path = b.get("path")
    if not path:
        return (b["x0"], b["y0"]), (b["x1"], b["y1"])
    legs = [(math.hypot(q[0] - p[0], q[1] - p[1]), i) for i, (p, q) in enumerate(zip(path, path[1:]))]
    _, i = max(legs, key=lambda t: (t[0], -t[1]))
    return tuple(path[i]), tuple(path[i + 1])


def _developed(b):
    path = b.get("path")
    if not path:
        return math.hypot(b["x1"] - b["x0"], b["y1"] - b["y0"])
    return sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(path, path[1:]))


def dedupe(records) -> list:
    """Mark later labels of the same bar family over the same panel and direction as DUPLICATE_LABEL."""
    seen = {}
    out = []
    for r in sorted(records, key=lambda x: str(x["annotation"])):
        r = dict(r)
        if "panel" in r and r.get("count") is not None:
            d = _canon(r["direction"])
            k = (r["kind"], r["n"], r["dia_mm"], r["top"], round(d[0], 2), round(d[1], 2), tuple(r["panel"]))
            if k in seen:
                r.update(state="DUPLICATE_LABEL", duplicate_of=seen[k],
                         why="same bar family, direction and panel as an earlier label - counted once")
            else:
                seen[k] = r["annotation"]
        out.append(r)
    return out


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "angle_tol_deg": ANGLE_TOL_DEG, "bind_dist_mm": BIND_DIST, "tie_mm": TIE_MM,
           "max_support_mm": MAX_SUPPORT, "embed_rule": EMBED_RULE,
           "rule": "annotation -> parallel drawn bar within the binding distance (projection inside the bar extent); "
                   "distribution width = clear distance between supports by perpendicular rays; per-metre count = "
                   "floor(width / spacing) + 1; length = clear span + embedment (support width - cover) at each "
                   "support; the drawn bar length is a symbol, reported only; open rays = UNBOUND (never estimated)",
           "never": ["nearest text alone when two bars compete", "a width from an open ray", "kg/m3 ratios"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
