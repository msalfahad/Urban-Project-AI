"""T-221 ROOF_FALLS_V1: the rise of a screed-to-falls surface over a flat roof slab, from the drawn drains and the printed
fall, and the per-zone FFL -> structural-top relation of the zones T-214 held (any villa; unwired research module).

Physical element. A roof / terrace drains because the layer between the structural slab and the finished surface varies:
it is t0 thick at a drain (rainwater outlet) and t0 + z(p) at a point p, where z(p) is the rise of the falls surface
above the drain level. The build-up of a roof zone is therefore not a number but a field: b(p) = t0 + z(p) + the
constant layers (membrane, insulation, protection, tile + bed) where the set specifies them. A constant drawn layer can
never be that build-up (T-214 rule CONSTANT_LAYER_VS_FALLS).

What the drawings can fix and what they cannot:
  * the drains (outlet positions) and the fall (printed '1 %'; where no fall is printed the owner's Q-45 fallback, an
    ASSUMED - OWNER-APPROVED value, is used for the fall only) fix z(p) up to the layout of ridges and valleys;
  * the layout of the planes (ridges / valleys / cross-falls) is rarely drawn. Two bounds follow from the fall alone:
      - EIKONAL (lower bound): with every fall at least the printed gradient g, z(p) >= g x (shortest path inside the
        roof from p to its nearest drain). No buildable surface that honours g everywhere is lower;
      - AXIS (layout of the drawn edge arrows): the surface falls g across to the parapet line and then g along it to
        the drain: z(p) = g x (shortest axis-parallel (L1) path to the nearest drain). For a narrow strip both bounds
        nearly coincide; for a wide roof they differ by up to a factor sqrt(2).
    The range [EIKONAL, AXIS] is a range from a NAMED cause (FALL_LAYOUT_NOT_DRAWN), never averaged.
  * t0 (the screed at the outlet), the membrane / insulation / protection layers: printed or HELD. Never 0.
  * which point a printed finished roof level refers to (drain? high point? the marker position?) is not stated by a
    single level mark on a roof with falls: a printed finished roof level is never the structural top (FINISHED_AS_
    STRUCTURAL) and never b = 0.

Owner manual method kept beside (OWNER_QUESTIONS_ANSWERED Q-41 / Q-45): roofs and balconies get a screed over the
membrane as its own line, thickness not given; roof bed 'depending on slope and manhole each 1 m 0.5 %'; Lead 2026-10-20:
a printed 1 % governs, 0.5 % applies only where no slope is printed. The owner gives no t0 either.

A printed bound can test a layout: a parapet detail that requires the RC upstand to be 'more than the height of roof
finishing' bounds b at the parapet line; evaluate_parapet() reports PROVEN / VIOLATED / NOT PROVEN per bound.
"""
from __future__ import annotations

import heapq
import math

import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely import contains_xy

METHOD = "ROOF_FALLS_V1"
MODELS = ("EIKONAL", "AXIS")
SCALE = {"m": 1.0, "mm": 0.001}
EPS = 1e-6


def _k(units):
    if units not in SCALE:
        raise ValueError(f"unknown units {units!r}")
    return SCALE[units]


def _num(v, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise ValueError(f"{what}: a number is required, got {v!r}")
    return float(v)


def _metric(model):
    if model == "EIKONAL":
        return lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1])
    if model == "AXIS":
        return lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1])
    raise ValueError(f"unknown model {model!r}")


def _reflex_vertices(poly):
    """Vertices where the interior angle exceeds 180 deg: the only places a shortest path inside the roof bends."""
    ring = list(poly.exterior.coords)[:-1]
    ccw = poly.exterior.is_ccw
    out = []
    n = len(ring)
    for i in range(n):
        a, b, c = ring[i - 1], ring[i], ring[(i + 1) % n]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if (cross < -EPS and ccw) or (cross > EPS and not ccw):
            out.append(b)
    return out


class _Field:
    """Shortest-path distance to the nearest drain inside a simple polygon, in one metric (visibility graph)."""

    def __init__(self, poly, drains, model):
        self.poly = poly
        self.cover = poly.buffer(1e-7)
        self.d = _metric(model)
        self.drains = drains
        self.nodes = list(drains) + _reflex_vertices(poly)
        nd = len(self.nodes)
        dist = [math.inf] * nd
        owner = [None] * nd
        heap = []
        for i in range(len(drains)):
            dist[i], owner[i] = 0.0, i
            heap.append((0.0, i))
        heapq.heapify(heap)
        while heap:
            du, u = heapq.heappop(heap)
            if du > dist[u]:
                continue
            for v in range(nd):
                if v == u or not self._visible(self.nodes[u], self.nodes[v]):
                    continue
                alt = du + self.d(self.nodes[u], self.nodes[v])
                if alt < dist[v] - 1e-12:
                    dist[v], owner[v] = alt, owner[u]
                    heapq.heappush(heap, (alt, v))
        self.ndist, self.nowner = dist, owner

    def _visible(self, a, b):
        if math.hypot(a[0] - b[0], a[1] - b[1]) < EPS:
            return True
        return self.cover.covers(LineString([a, b]))

    def at(self, p):
        best, who = math.inf, None
        for i, n in enumerate(self.nodes):
            if math.isinf(self.ndist[i]) or not self._visible(p, n):
                continue
            v = self.d(p, n) + self.ndist[i]
            if v < best:
                best, who = v, self.nowner[i]
        return best, who


def falls_field(outline, drains, slope, units="m", step=0.05):
    """Rise of the falls surface over one roof zone, both models. outline: polygon vertices (x, y); drains: outlet points
    on or inside the outline; slope: the fall as a fraction (0.01 = 1 %). Returns per model: max rise, mean rise,
    integral of the rise (m3 per m of nothing: the volume above the t0 plane), the far point, and per-drain catchment
    areas. Refuses: no drain (DRAINS_NOT_DRAWN), a drain outside the zone, slope <= 0 (a flat layer is not a fall)."""
    k = _k(units)
    if not drains:
        raise ValueError("DRAINS_NOT_DRAWN: a falls surface needs at least one drawn outlet")
    g = _num(slope, "slope")
    if g <= 0:
        raise ValueError("slope must be > 0: a constant layer is not a fall (CONSTANT_LAYER_VS_FALLS)")
    pts = [(_num(x, "outline x") * k, _num(y, "outline y") * k) for x, y in outline]
    poly = Polygon(pts)
    if not poly.is_valid or poly.area <= 0:
        raise ValueError("the outline is not a valid simple polygon")
    dr = [(_num(x, "drain x") * k, _num(y, "drain y") * k) for x, y in drains]
    for p in dr:
        if poly.buffer(1e-6).disjoint(Point(p)):
            raise ValueError(f"drain {p} lies outside the zone outline")
    s = _num(step, "step")
    x0, y0, x1, y1 = poly.bounds
    xs = np.arange(x0 + s / 2, x1, s)
    ys = np.arange(y0 + s / 2, y1, s)
    X, Y = np.meshgrid(xs, ys)
    inside = contains_xy(poly, X, Y)
    cells = list(zip(X[inside].tolist(), Y[inside].tolist()))
    cell_a = s * s
    # the field's maximum lies on the outline or on a catchment boundary: sample the outline vertices too
    edge = []
    for a, b in zip(pts, pts[1:] + pts[:1]):
        n = max(1, int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / (s / 5))))
        edge += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n)]
    probes = cells + edge
    out = {"area_m2": round(poly.area, 4), "slope": g, "step_m": s, "models": {}}
    for model in MODELS:
        f = _Field(poly, dr, model)
        zmax, far, tot = -1.0, None, 0.0
        catch = [0.0] * len(dr)
        for i, p in enumerate(probes):
            d, who = f.at(p)
            if math.isinf(d):
                raise ValueError(f"point {p} cannot reach a drain inside the zone")
            if d > zmax:
                zmax, far = d, p
            if i < len(cells):
                tot += d * cell_a
                catch[who] += cell_a
        mean_d = tot / (len(cells) * cell_a)
        out["models"][model] = {
            "rise_max_m": round(g * zmax, 4), "path_max_m": round(zmax, 3), "far_point": [round(far[0], 3),
                                                                                       round(far[1], 3)],
            "rise_mean_m": round(g * mean_d, 4),
            "volume_above_t0_m3": round(g * mean_d * poly.area, 4),
            "catchment_m2": [round(c * poly.area / (len(cells) * cell_a), 3) for c in catch]}
    out["resolution_m"] = round(g * s * math.sqrt(2), 5)
    return out


def evaluate_parapet(rise_max_edge, upstand, t0=None, layers=None):
    """A printed parapet rule 'RC upstand more than the height of roof finishing' against a falls range at the parapet
    line. rise_max_edge: (lo, hi) of the largest rise on the parapet line; t0 / layers: printed values or None (HELD).
    PROVEN when even hi + every known layer stays below the upstand with every unknown taken as 0 AND no unknown is left;
    VIOLATED when lo alone already reaches it; otherwise NOT PROVEN with the remaining allowance named."""
    lo, hi = (_num(v, "rise") for v in rise_max_edge)
    u = _num(upstand, "upstand")
    known = sum(_num(v, "layer") for v in (layers or {}).values() if v is not None)
    unknown = [n for n, v in (layers or {}).items() if v is None]
    if t0 is None:
        unknown = ["t0 (screed at the outlet)"] + unknown
    else:
        known += _num(t0, "t0")
    if lo + known >= u:
        return {"status": "VIOLATED", "detail": f"rise {lo:.3f} + known layers {known:.3f} >= upstand {u:.3f}"}
    if not unknown and hi + known < u:
        return {"status": "PROVEN", "margin_m": round(u - hi - known, 4)}
    return {"status": "NOT PROVEN", "allowance_left_m": [round(u - hi - known, 4), round(u - lo - known, 4)],
            "unknown": unknown}


ZONE_KINDS = ("DRY", "WET", "SUNKEN", "ROOF", "TERRACE")


def zone_status(zone):
    """The FFL -> structural-top relation of one zone, drawing-derived and owner method side by side (statuses of
    WORKFLOW_CONTROLS s.5). zone keys: zone_id, kind, ffl {value, kind}, evidence (list of dicts), owner (list), and for
    roofs / terraces: falls (output of falls_field) or None, t0 (printed) or None.
    Refusals (ValueError): FINISHED_AS_STRUCTURAL, DRY_LAYER_TO_WET, CONSTANT_LAYER_VS_FALLS, ALLOWANCE_AS_DATUM."""
    zid, kind = zone["zone_id"], zone["kind"]
    if kind not in ZONE_KINDS:
        raise ValueError(f"{zid}: unknown kind {kind!r}")
    ffl = zone.get("ffl") or {}
    if ffl.get("kind") not in ("FFL", "FINISHED_ROOF"):
        raise ValueError(f"{zid}: the zone datum must be a finished level")
    for e in zone.get("evidence", []):
        src = e.get("source")
        if src == "PRINTED_TOP" and e.get("kind") in ("FFL", "FINISHED_ROOF"):
            raise ValueError(f"{zid}: FINISHED_AS_STRUCTURAL: a finished level offered as the structural top")
        if src == "DRAWN_LAYER" and e.get("cut_zone_kind") == "DRY" and kind in ("WET", "SUNKEN"):
            raise ValueError(f"{zid}: DRY_LAYER_TO_WET: a dry-floor layer is never carried to a {kind} zone")
        if src == "DRAWN_LAYER" and kind in ("ROOF", "TERRACE") and e.get("constant_layer", True):
            raise ValueError(f"{zid}: CONSTANT_LAYER_VS_FALLS: a constant drawn layer is not a roof build-up")
    for o in zone.get("owner", []):
        if o.get("used_as") == "LEVEL_DATUM" and o.get("scope") != "LEVEL_DATUM":
            raise ValueError(f"{zid}: ALLOWANCE_AS_DATUM: owner item {o.get('rule')} has scope {o.get('scope')}")
    printed = [e for e in zone.get("evidence", []) if e.get("source") == "PRINTED_TOP"]
    res = {"zone_id": zid, "kind": kind, "ffl": ffl["value"], "owner_beside": zone.get("owner", [])}
    if printed:
        top = _num(printed[0]["value"], f"{zid} printed top")
        res.update(status="DRAWING-CONFIRMED", structural_top=top, b=round(ffl["value"] - top, 4))
        return res
    missing = []
    if kind == "SUNKEN" and zone.get("drop") is None:
        missing.append("the printed drop of the sunken panel")
    if kind in ("ROOF", "TERRACE"):
        fl = zone.get("falls")
        if fl is None:
            missing.append("the outlets (no drain drawn) and so the falls surface")
        else:
            res["falls_rise_max_m"] = [fl["models"]["EIKONAL"]["rise_max_m"], fl["models"]["AXIS"]["rise_max_m"]]
            res["falls_status"] = "DRAWING-CONFIRMED range (FALL_LAYOUT_NOT_DRAWN)"
        if zone.get("t0") is None:
            missing.append("t0, the screed at the outlet")
        missing.append("the reference point of the printed finished roof level (drain, high point or marker)")
        missing.extend(zone.get("layers_missing", []))
    if kind == "WET":
        missing.append("a printed wet build-up or a section through the wet zone")
        missing.extend(zone.get("layers_missing", []))
    res.update(status="HELD", structural_top=None, b=None, missing=missing)
    return res
