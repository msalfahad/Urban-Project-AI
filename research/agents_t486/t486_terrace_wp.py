"""T-486: balcony / terrace waterproofing applicability census (B8-07), every villa. Research piece, not wired.

Physical element first (ERS s.2 step 1): an EXTERNAL HORIZONTAL SURFACE EXPOSED TO RAIN (a slab top open to the sky)
whatever the label says. Each candidate zone is classified on drawing evidence, in this order:

1. exposure: open to the sky? (no element above on the floor plan above / the roof plan). Not exposed -> the surface
   is a floor under a roof: NOT_APPLICABLE (no exterior membrane). Unknown -> HELD.
2. WP layer: an exposed slab top falls under the owner rule UP-WP-ROOF-001 (purpose 'exterior horizontal surfaces
   exposed to water'; Q-24: measured like a bathroom floor, membrane + 0.20 m upturn on walls / parapets). A project
   detail that prints another build-up governs (detail_overrides).
3. function: ACCESSIBLE (a door opens onto it) -> terrace / balcony function (B8-07); NOT accessible -> roof function
   (B8-06). The function names the family; the membrane is ONE physical layer and is counted ONCE.
4. double count: the membrane m2 that a roof WP line (FIN.WP.ROOF, B8-06) already carries over the same physical
   surface is CARRIED, never added again; only the uncarried remainder is a new quantity, and a remainder that is not
   explained is flagged (never silently dropped, never forced to 0).
5. a zone that needs WP but has no measured area stays HELD with area None (never 0); an applicable zone with an area
   but no line is MISSING (a blank line to fill, its family named).

Geometry (zone_geometry): the membrane area is the zone outline less the solid footprints that stand on the slab (built
elements: piers, columns, planters' walls) and less the openings (voids); each boundary piece is typed UPTURN (a wall,
parapet or pier face: UP-WP-003 0.20 m) or OPEN_EDGE (a slab edge or a void edge: a termination by detail, its
treatment HELD, the length measured). Units: metres in, metres out; a 'unit_m' factor converts drawing units first.
"""
from __future__ import annotations

import math

import shapely
from shapely.geometry import LineString, Polygon

METHOD = "T486_TERRACE_WP_CENSUS_V1"
UPTURN_H_M = 0.20                    # UP-WP-003 / Q-24 (owner): wall / parapet upturn height; a project detail overrides
GRID_M = 1e-6                        # every input and boolean result is snapped to a 1 micrometre grid, so faces that
                                     # coincide in the drawing coincide exactly after rotation / units (no slivers)

NOT_APPLICABLE = "NOT_APPLICABLE"
CARRIED = "CARRIED_BY_ROOF_LINE"
MISSING = "MISSING"
HELD = "HELD"

FAMILY_TERRACE = "B8-07"
FAMILY_ROOF = "B8-06"


def _poly(points, unit_m=1.0):
    return shapely.set_precision(Polygon([(x * unit_m, y * unit_m) for x, y in points]), GRID_M)


def _line(points, unit_m=1.0):
    return shapely.set_precision(LineString([(x * unit_m, y * unit_m) for x, y in points]), GRID_M)


def unary_union(geoms):
    return shapely.union_all(list(geoms), grid_size=GRID_M)


def _diff(a, b):
    return _clean(shapely.difference(a, b, grid_size=GRID_M), a)


def _inter(a, b):
    return _clean(shapely.intersection(a, b, grid_size=GRID_M), a)


def _clean(geom, like):
    """keep only the parts of the dimension of the first operand (a snapped overlay can leave lower-dimension bits)."""
    dim = shapely.get_dimensions(like)
    parts = [x for x in shapely.get_parts(geom) if shapely.get_dimensions(x) == dim]
    return shapely.union_all(parts, grid_size=GRID_M) if parts else shapely.from_wkt(
        "POLYGON EMPTY" if dim == 2 else "LINESTRING EMPTY")


def _areal(geom):
    """the polygonal part of a boolean result (a cut can leave touching lines or points beside the polygons)."""
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return geom
    return unary_union(x for x in getattr(geom, "geoms", ()) if x.geom_type in ("Polygon", "MultiPolygon"))


def zone_geometry(outline, *, footprints=(), openings=(), open_edges=(), clip=None, unit_m=1.0):
    """membrane plan area and boundary split of one zone.

    outline: ring of the zone (inside the wall / parapet faces, to the slab edge where no parapet stands);
    footprints: rings of solid elements standing on the slab (deducted; their faces are UPTURN);
    openings: rings of voids through the slab (deducted; their edges are OPEN_EDGE);
    open_edges: polylines of the outline that are slab edges with no wall or parapet (OPEN_EDGE);
    clip: optional ring that cuts the zone into the part measured here (e.g. the part open to the sky); a boundary
    piece made by the cut is CONTINUATION (the slab goes on into the neighbouring part), neither upturn nor edge.
    -> {gross_m2, footprints_m2, openings_m2, net_m2, perimeter_lm, upturn_lm, open_edge_lm, opening_edge_lm,
        continuation_lm}"""
    g = _poly(outline, unit_m)
    if not g.is_valid or g.area <= 0:
        raise ValueError("zone outline is not a valid ring")
    fp = unary_union([_poly(r, unit_m) for r in footprints]) if footprints else None
    op = unary_union([_poly(r, unit_m).buffer(0) for r in openings]) if openings else None
    cl = _poly(clip, unit_m) if clip is not None else None
    whole = g
    if fp is not None:
        whole = _diff(whole, fp)
    if op is not None:
        whole = _diff(whole, op)
    net = _areal(_inter(whole, cl)) if cl is not None else whole
    bnd = net.boundary
    per = bnd.length
    oe = unary_union([_line(p, unit_m) for p in open_edges]) if open_edges else None
    open_lm = _inter(bnd, oe).length if oe is not None else 0.0
    opening_lm = _inter(bnd, op.boundary).length if op is not None else 0.0
    cont_lm = _diff(bnd, whole.boundary).length if cl is not None else 0.0
    upturn = per - open_lm - opening_lm - cont_lm
    if upturn < -1e-4:
        raise ValueError("boundary pieces overlap: open edges, openings or continuations counted twice")
    base = _inter(g, cl) if cl is not None else g
    fp_a = _inter(base, fp).area if fp is not None else 0.0
    op_a = ((_diff(_inter(base, op), fp) if fp is not None else _inter(base, op)).area if op is not None else 0.0)
    return {"gross_m2": round(base.area, 6), "footprints_m2": round(fp_a, 6), "openings_m2": round(op_a, 6),
            "net_m2": round(net.area, 6), "perimeter_lm": round(per, 6), "upturn_lm": round(max(upturn, 0.0), 6),
            "open_edge_lm": round(open_lm, 6), "opening_edge_lm": round(opening_lm, 6),
            "continuation_lm": round(cont_lm, 6)}


def transformed(ring, *, angle_deg=0.0, mirror=False):
    """a ring rotated about the origin and / or mirrored in the y axis (test helper for adverse cases)."""
    a = math.radians(angle_deg)
    out = []
    for x, y in ring:
        if mirror:
            x = -x
        out.append((x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)))
    return out


def classify(zone):
    """one candidate zone -> census row. zone keys:
    zone_id, label (ROOF / BALCONY / TERRACE / None), exposed (True / False / None), below (HABITABLE / EXTERIOR /
    None), doors (int or None: doors opening onto it), membrane_m2 (float or None), upturn_lm, open_edge_lm,
    carried (list of {line_id, item_code, m2}: roof WP lines over the SAME physical surface), evidence (list of str)."""
    zid = zone["zone_id"]
    row = {"zone_id": zid, "label": zone.get("label"), "below": zone.get("below"), "doors": zone.get("doors"),
           "exposed": zone.get("exposed"), "membrane_m2": zone.get("membrane_m2"),
           "upturn_lm": zone.get("upturn_lm"), "open_edge_lm": zone.get("open_edge_lm"),
           "evidence": list(zone.get("evidence") or ()), "carried_m2": 0.0, "carried_by": [], "add_m2": None,
           "residual_m2": None, "flags": []}
    exp = zone.get("exposed")
    if exp is False:
        row.update(wp_layer="NO (a floor under a roof)", status=NOT_APPLICABLE, family=None, function="COVERED",
                   add_m2=0.0)
        return row
    if exp is None:
        row.update(wp_layer="UNKNOWN (exposure not established)", status=HELD, family=None, function="UNKNOWN")
        row["flags"].append("EXPOSURE_UNKNOWN")
        return row
    row["wp_layer"] = "YES (UP-WP-ROOF-001: exposed slab top)"
    doors = zone.get("doors")
    if zone.get("label") == "BALCONY" or (doors or 0) > 0:
        func, fam = "TERRACE_OR_BALCONY", FAMILY_TERRACE
    elif doors is None:
        func, fam = "UNKNOWN_ACCESS", None
        row["flags"].append("ACCESS_UNKNOWN")
    else:
        func, fam = "ROOF", FAMILY_ROOF
    row.update(function=func, family=fam)
    carried = [dict(c) for c in zone.get("carried") or ()]
    row["carried_by"] = carried
    area = zone.get("membrane_m2")
    if carried and all(c.get("m2") is None for c in carried):
        # the roof line over this surface is itself HELD: nothing is carried, nothing may be added (never 0)
        row.update(status=HELD, carried_m2=None)
        row["flags"].append("CARRIED_BY_A_HELD_LINE")
        return row
    if carried and any(c.get("m2") is None for c in carried):
        raise ValueError(f"{zid}: carried lines mix held and measured quantities")
    cm = sum(c["m2"] for c in carried)
    row["carried_m2"] = round(cm, 6)
    if area is None:
        row["status"] = HELD
        row["flags"].append("AREA_NOT_MEASURED")
        if carried:
            row["status"] = CARRIED
            row["add_m2"] = 0.0
            row["flags"].append("CARRIED_LINE_NOT_CLOSED_BY_OWN_MEASURE")
        return row
    if carried:
        res = round(area - cm, 6)
        row["residual_m2"] = res
        row["status"] = CARRIED
        row["add_m2"] = 0.0
        if abs(res) > float(zone.get("residual_tol_m2", 0.05)):
            row["flags"].append("CARRIED_RESIDUAL_UNEXPLAINED")
        return row
    row["status"] = MISSING
    row["add_m2"] = round(area, 6)
    return row


def census(zones):
    """every zone -> rows + per-family totals of NEW membrane m2 (uncarried, measured) and of HELD zones."""
    rows = [classify(z) for z in zones]
    ids = [r["zone_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("a zone is listed twice")
    fam = {}
    for r in rows:
        f = r.get("family") or "UNASSIGNED"
        t = fam.setdefault(f, {"new_m2": 0.0, "carried_m2": 0.0, "missing_zones": [], "held_zones": [],
                               "carried_zones": [], "not_applicable_zones": []})
        if r["status"] == MISSING:
            t["new_m2"] = round(t["new_m2"] + r["add_m2"], 6)
            t["missing_zones"].append(r["zone_id"])
        elif r["status"] == HELD:
            t["held_zones"].append(r["zone_id"])
        elif r["status"] == CARRIED:
            t["carried_m2"] = round(t["carried_m2"] + (r["carried_m2"] or 0.0), 6)
            t["carried_zones"].append(r["zone_id"])
        else:
            t["not_applicable_zones"].append(r["zone_id"])
    return {"method": METHOD, "rows": rows, "families": fam}


def upturn_m2(upturn_lm):
    """vertical membrane area of an upturn run (UP-WP-003 0.20 m); None stays None."""
    return None if upturn_lm is None else round(upturn_lm * UPTURN_H_M, 6)


__all__ = ["census", "classify", "zone_geometry", "transformed", "upturn_m2", "UPTURN_H_M", "NOT_APPLICABLE",
           "CARRIED", "MISSING", "HELD", "FAMILY_TERRACE", "FAMILY_ROOF"]
