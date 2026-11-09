"""T-529: WP_APPLICABILITY_RULES_V2, exposure step (proposed NEW rule version; research piece, unwired).

Supersedes ONLY R-WP-APPL-EXPOSED-1 of engine/source/wp_applicability_rules_v1.py (T-494, provenance T-486), whose
'covered above, open at a side -> HELD' left every ledge / loggia / balcony-type surface undecided. Every other V1
rule (FUNCTION, ONCE, UPTURN, EDGE, DRAIN) is reused unchanged by calling V1 component_rows() on the classified parts.
V1 and every existing rule / knowledge version file stay untouched; promotion into engine/source is a later step.

Physical element first (ERS s.2.1): an exterior slab top is wetted by water that can REACH it: rain falling through
open sky, and driven rain / run-off entering through any side that is open to the outside air. It is dry only when a
cover is above it AND every side is closed up to that cover. Decided from drawn geometry and printed details only,
never from an angle (no design rain angle is printed or held in an owner rule; ERS 'no assumptions').

  R-WP-APPL-EXPOSED-2a  OPEN-SKY PART. The surface less the plan union of every drawn cover above it (slab / roof /
                        canopy outline on the plan above or the roof plan; glazing counts as a cover only where its
                        outline is drawn) is open to the sky -> EXPOSED.
  R-WP-APPL-EXPOSED-2b  COVERED PART OPEN AT A SIDE -> EXPOSED. A covered part with any boundary open to the outside
                        air (slab edge, void edge, railing, parapet, or its interface with the open-sky part where no
                        enclosing screen is drawn) is the balcony condition: UP-WP-ROOF-001 (OWNER_APPROVED, purpose
                        'exterior horizontal surfaces exposed to water', scope 'balconies, terraces and roofs drawn as
                        spaces', area 'the drawn exterior space area') waterproofs a balcony over its whole drawn area,
                        with no deduction for the floor above it. A membrane is also continuous: it ends at an upturn,
                        an edge, a threshold or a drawn joint, never at the plan shadow of a slab overhead.
  R-WP-APPL-EXPOSED-2c  COVERED PART CLOSED ROUND -> NOT_APPLICABLE (a floor under a roof): every side is a wall, or
                        glazing whose head is drawn closing to the cover, or an enclosing screen drawn on the cover line.
  R-WP-APPL-EXPOSED-2d  HELD (bound shown, never 0): sides closed but the cover outline not established; a side closed
                        only by glazing without a drawn head, or a side of unknown kind, and no open side.
  R-WP-APPL-EXPOSED-2e  A PRINTED DETAIL GOVERNS: a project detail / section that draws the membrane extent decides it
                        (UP-WP-ROOF-001 'by specification'); the quantity is that extent within the surface, cited.

The covered / open split is always reported with every boundary's drawing source, also where it does not change the
quantity (the screed, finish and threshold details use it). Units: coordinates x unit_m = metres; m2 / lm out.
Scope: every villa (agent-derived scope reading of UP-WP-ROOF-001, provenance T-529; NOT an owner decision).
"""
from __future__ import annotations

import math

import shapely
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

RULE_VERSION = "WP_APPLICABILITY_RULES_V2"
SUPERSEDES = "R-WP-APPL-EXPOSED-1 (WP_APPLICABILITY_RULES_V1); every other V1 rule reused unchanged"
GRID_M = 1e-6
TOL_M = 1e-3                    # 1 mm: a boundary piece shorter than this is not a side
MAX_SLAB_M2 = 1.0e4             # a single exterior slab above 10,000 m2 is a unit error (mm read as m), refused

EXPOSED, COVERED, HELD = "EXPOSED", "COVERED", "HELD"
OPEN_KINDS = {"OPEN_EDGE", "VOID_EDGE", "SLAB_EDGE", "RAILING", "PARAPET"}   # air passes: open to the outside
CLOSED_KINDS = {"WALL"}                                                     # closed up to the cover
GLAZING = "GLAZING"                                                         # closed only with a drawn head
BASIS = {
    "2a": "R-WP-APPL-EXPOSED-2a (open to the sky in plan; UP-WP-ROOF-001 purpose)",
    "2b": "R-WP-APPL-EXPOSED-2b (covered, open at a side: balcony condition, UP-WP-ROOF-001 scope / area)",
    "2c": "R-WP-APPL-EXPOSED-2c (covered and closed round: a floor under a roof)",
    "2d": "R-WP-APPL-EXPOSED-2d (exposure not established)",
    "2e": "R-WP-APPL-EXPOSED-2e (printed detail governs)",
}


def _snap(g):
    return shapely.set_precision(g, GRID_M)


def _poly(points, unit_m):
    p = Polygon([(x * unit_m, y * unit_m) for x, y in points]).buffer(0)
    return _snap(p)


def _line(points, unit_m):
    return _snap(LineString([(x * unit_m, y * unit_m) for x, y in points]))


def _src_ok(src):
    return isinstance(src, str) and src.strip() != ""


def _areal(g):
    if g.is_empty:
        return Polygon()
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    return unary_union([x for x in getattr(g, "geoms", []) if x.geom_type in ("Polygon", "MultiPolygon")]) \
        if hasattr(g, "geoms") else Polygon()


def _linear(g):
    if g.is_empty:
        return []
    if g.geom_type == "LineString":
        return [g]
    if g.geom_type == "MultiLineString":
        return list(g.geoms)
    if hasattr(g, "geoms"):
        out = []
        for x in g.geoms:
            out += _linear(x)
        return out
    return []


def classify_surface(surface):
    """one exterior slab surface -> exposure decision per part.

    surface keys:
      zone_id; outline: [(x, y)] closed ring; unit_m (default 1.0);
      boundary: [{run, kind (OPEN_EDGE / VOID_EDGE / SLAB_EDGE / RAILING / PARAPET / WALL / GLAZING / UNKNOWN),
                  coords [(x, y), ...], source, head_drawn (GLAZING only: True / False / None)}] covering the outline;
      covers: None (cover outline NOT established) or a list (possibly empty = nothing above, established) of
              {id, kind (SLAB / ROOF / CANOPY / GLAZING), outline [(x, y)], source, outline_drawn (GLAZING: bool)};
      screens: [{id, kind WALL / GLAZING, coords, source, head_drawn}] enclosing elements drawn across the surface;
      detail: None or {extent: [(x, y)] ring | 'WHOLE' | 'NONE', source} (a printed membrane extent).
    returns {zone_id, area_m2, open_m2, covered_m2, parts: [...], membrane_m2 (None if any part HELD), held_bound_m2,
             status, basis, evidence}."""
    zid = surface["zone_id"]
    u = float(surface.get("unit_m", 1.0))
    if not u > 0:
        raise ValueError(f"{zid}: unit_m must be positive")
    poly = _poly(surface["outline"], u)
    if poly.is_empty or poly.area <= 0:
        raise ValueError(f"{zid}: outline has no area")
    if poly.area > MAX_SLAB_M2:
        raise ValueError(f"{zid}: area {poly.area:.1f} m2 implausible for one slab surface (units: mm read as m?)")

    # ---- boundary runs: each must carry a kind and a source, and together they must reconcile with the outline -----
    runs = []
    for b in surface.get("boundary") or ():
        if not _src_ok(b.get("source")):
            raise ValueError(f"{zid}: boundary run {b.get('run')} has no drawing source")
        runs.append(dict(b, geom=_line(b["coords"], u)))
    perim = poly.exterior.length + sum(i.length for i in poly.interiors)
    if not runs:
        raise ValueError(f"{zid}: no boundary runs: the sides are not described")
    seg_runs = _assign(poly, runs)
    unclaimed = sum(lm for lm, owner in seg_runs if owner is None)
    on = sum(lm for lm, owner in seg_runs if owner is not None)
    if unclaimed > max(0.002, 1e-4 * perim) or abs(on - perim) > max(0.002, 1e-4 * perim):
        raise ValueError(f"{zid}: boundary runs cover {on:.6f} lm of a {perim:.6f} lm outline (pieces do not reconcile)")

    # ---- printed detail (2e) governs ---------------------------------------------------------------------------------
    det = surface.get("detail")
    if det is not None:
        if not _src_ok(det.get("source")):
            raise ValueError(f"{zid}: a membrane detail without a cited source is refused")
        ext = det["extent"]
        if ext == "WHOLE":
            m2 = poly.area
        elif ext == "NONE":
            m2 = 0.0
        else:
            m2 = _areal(poly.intersection(_poly(ext, u))).area
        return {"zone_id": zid, "area_m2": round(poly.area, 6), "open_m2": None, "covered_m2": None,
                "parts": [{"part": "DETAIL", "area_m2": round(m2, 6), "decision": EXPOSED if m2 > 0 else COVERED,
                           "basis": BASIS["2e"], "evidence": [det["source"]]}],
                "membrane_m2": round(m2, 6), "held_bound_m2": None, "status": "MEASURED", "basis": BASIS["2e"],
                "evidence": [det["source"]]}

    covers = surface.get("covers")

    # ---- cover outline not established ---------------------------------------------------------------------------------
    if covers is None:
        if any(lm > TOL_M for lm, o in seg_runs if o is not None and o["kind"] in OPEN_KINDS):
            # open at a side: exposed whichever way the cover runs (2a where open sky, 2b where covered)
            return _result(zid, poly, None, None,
                           [_part("WHOLE", poly, EXPOSED, BASIS["2a"] + " / " + BASIS["2b"],
                                  ["open side(s): " + ", ".join(f"{r['run']} ({r['source']})" for r in runs if r["kind"] in OPEN_KINDS),
                                   "cover outline not established: the covered / open split is NOT reported"])])
        return _result(zid, poly, None, None,
                       [_part("WHOLE", poly, HELD, BASIS["2d"], ["no open side drawn and the cover outline is not "
                                                                  "established: open sky or a roof cannot be told"],
                              held_reason="cover outline not established")])

    cov_geoms = []
    for c in covers:
        if not _src_ok(c.get("source")):
            raise ValueError(f"{zid}: cover {c.get('id')} has no drawing source")
        if c.get("kind") == GLAZING and c.get("outline_drawn") is not True:
            # a glazed cover whose outline / frame is not drawn cannot place the cover edge
            return _result(zid, poly, None, None,
                           [_part("WHOLE", poly, HELD, BASIS["2d"], [f"glazed cover {c.get('id')}: outline not drawn"],
                                  held_reason="glazed cover without a drawn outline")])
        cov_geoms.append(_poly(c["outline"], u))
    cover = _snap(unary_union(cov_geoms)) if cov_geoms else Polygon()
    covered = _areal(_snap(poly.intersection(cover))) if not cover.is_empty else Polygon()
    open_part = _areal(_snap(poly.difference(cover))) if not cover.is_empty else poly
    parts = []
    if open_part.area > GRID_M:
        parts.append(_part("OPEN_SKY", open_part, EXPOSED, BASIS["2a"],
                           ["not under " + (", ".join(f"{c['id']} ({c['source']})" for c in covers) or "any cover")]))

    screens = []
    for s in surface.get("screens") or ():
        if not _src_ok(s.get("source")):
            raise ValueError(f"{zid}: screen {s.get('id')} has no drawing source")
        screens.append(dict(s, geom=_line(s["coords"], u)))

    pieces = list(covered.geoms) if covered.geom_type == "MultiPolygon" else ([covered] if not covered.is_empty else [])
    for i, cp in enumerate(pieces):
        if cp.area <= GRID_M:
            continue
        # every boundary segment of the covered piece is owned once: a screen on it, else an outline run, else the
        # interface with the open-sky part (open air: no enclosing element drawn on it)
        acc = {}
        for lm, owner in _assign(cp, screens + runs, fallback=open_part):
            if owner is None or owner == "FALLBACK":     # on the cover line (the cut), no element drawn on it
                key = ("interface with the open-sky part", "OPEN_EDGE", None, "geometry: cover edge")
            else:
                key = (owner.get("run") or owner.get("id"), owner["kind"], owner.get("head_drawn"), owner["source"])
            acc[key] = acc.get(key, 0.0) + lm
        sides = [(k[0], k[1], lm, k[2], k[3]) for k, lm in acc.items() if lm > TOL_M]
        open_sides = [s for s in sides if s[1] in OPEN_KINDS]
        unsure = [s for s in sides if (s[1] == GLAZING and s[3] is not True) or
                  (s[1] not in OPEN_KINDS and s[1] not in CLOSED_KINDS and s[1] != GLAZING)]
        evid = [f"{s[0]}: {s[1]} {s[2]:.6f} lm ({s[4]})" for s in sides]
        name = "COVERED" if len(pieces) == 1 else f"COVERED_{i + 1}"
        if open_sides:
            parts.append(_part(name, cp, EXPOSED, BASIS["2b"], evid, open_sides_lm=round(sum(s[2] for s in open_sides), 6)))
        elif unsure:
            parts.append(_part(name, cp, HELD, BASIS["2d"], evid,
                               held_reason="enclosure not established: " + ", ".join(
                                   f"{s[0]} ({'glazing without a drawn head' if s[1] == GLAZING else s[1]})"
                                   for s in unsure)))
        else:
            parts.append(_part(name, cp, COVERED, BASIS["2c"], evid))
    return _result(zid, poly, open_part, covered, parts)


def _assign(poly, owners, fallback=None):
    """split the polygon boundary into its straight segments and give each to the first owner line lying on it
    (segment midpoint within 1 mm and both ends within 1 mm), else to 'FALLBACK' when it lies on `fallback`'s
    boundary, else to None. -> [(length_m, owner)]. Each segment is counted once (no corner double count)."""
    rings = [poly.exterior] + list(poly.interiors) if poly.geom_type == "Polygon" else \
        [r for g in poly.geoms for r in [g.exterior] + list(g.interiors)]
    fb = fallback.boundary if fallback is not None and not fallback.is_empty else None
    verts = [Point(v) for o in owners for v in (o["geom"].coords[0], o["geom"].coords[-1])]
    out = []
    for ring in rings:
        c = list(ring.coords)
        for a, b in zip(c, c[1:]):
            seg0 = LineString([a, b])
            if seg0.length <= 0:
                continue
            # node the segment at every owner end point lying on it (a run may end inside an outline segment)
            ts = sorted({0.0, 1.0} | {seg0.project(v, normalized=True) for v in verts if seg0.distance(v) <= TOL_M})
            for t0, t1 in zip(ts, ts[1:]):
                pa, pb = seg0.interpolate(t0, normalized=True), seg0.interpolate(t1, normalized=True)
                seg = LineString([pa, pb])
                if seg.length <= 1e-9:
                    continue
                m = seg.interpolate(0.5, normalized=True)
                owner = None
                for o in owners:
                    g = o["geom"]
                    if g.distance(m) <= TOL_M and g.distance(pa) <= TOL_M and g.distance(pb) <= TOL_M:
                        owner = o
                        break
                if owner is None and fb is not None and fb.distance(m) <= TOL_M:
                    owner = "FALLBACK"
                out.append((seg.length, owner))
    return out


def _part(name, g, decision, basis, evidence, **kw):
    d = {"part": name, "area_m2": round(g.area, 6), "decision": decision, "basis": basis, "evidence": list(evidence),
         "geom": g}
    d.update(kw)
    return d


def _result(zid, poly, open_part, covered, parts):
    held = [p for p in parts if p["decision"] == HELD]
    exp = [p for p in parts if p["decision"] == EXPOSED]
    m2 = None if held else round(sum(p["area_m2"] for p in exp), 6)
    status = "HELD" if held and not exp else ("PART_HELD" if held else "MEASURED")
    return {"zone_id": zid, "area_m2": round(poly.area, 6),
            "open_m2": None if open_part is None else round(open_part.area, 6),
            "covered_m2": None if covered is None else round(covered.area, 6),
            "parts": parts, "membrane_m2": m2,
            "measured_part_m2": round(sum(p["area_m2"] for p in exp), 6),
            "held_bound_m2": round(sum(p["area_m2"] for p in held), 6) if held else None,
            "status": status, "basis": sorted({p["basis"] for p in parts}),
            "evidence": [e for p in parts for e in p["evidence"]]}


def v1_exposure(decision_result):
    """the V1 'exposure' value for a zone that is ONE part (V1 component_rows then applies FUNCTION / ONCE / UPTURN /
    EDGE / DRAIN unchanged): EXPOSED -> 'EXPOSED', COVERED -> 'COVERED', HELD -> None (exposure not established).
    A zone split into parts of different decisions is refused here: split it into one V1 zone per part first."""
    ds = {p["decision"] for p in decision_result["parts"]}
    if len(ds) != 1:
        raise ValueError(f"{decision_result['zone_id']}: parts decide differently {sorted(ds)}: one V1 zone per part")
    d = ds.pop()
    return {EXPOSED: "EXPOSED", COVERED: "COVERED", HELD: None}[d]


def edge_distances(part_geom, cover_edge):
    """information only (never a quantity): nearest / farthest point of a covered part behind a cover edge (m)."""
    pts = list(part_geom.exterior.coords) if part_geom.geom_type == "Polygon" else \
        [c for g in part_geom.geoms for c in g.exterior.coords]
    ds = [cover_edge.distance(Point(p)) for p in pts]
    return round(min(ds), 6), round(max(ds), 6)


def transformed(ring, *, angle_deg=0.0, mirror=False, dx=0.0, dy=0.0):
    a = math.radians(angle_deg)
    out = []
    for x, y in ring:
        x = -x if mirror else x
        out.append((x * math.cos(a) - y * math.sin(a) + dx, x * math.sin(a) + y * math.cos(a) + dy))
    return out


__all__ = ["classify_surface", "v1_exposure", "edge_distances", "transformed", "RULE_VERSION", "EXPOSED", "COVERED",
           "HELD", "BASIS"]
