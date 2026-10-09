"""Recovery of an unfaced plan region: exact partition, evidence classes, tiling proof, mesh cover fit.

Generic and free of project constants. Geometry is in plan millimetres (shapely).

    partition(domain, barriers)          the faces that the drawn barrier lines cut a domain into; nothing is
                                         closed, extended or snapped that the drawing does not close
    tiling_proof(domain, parts)          union, sum, overlap and gap areas: a partition covers the domain once
    classify(part, evidence)             one lane per part, from drawn evidence only; a part that no evidence
                                         identifies is CLASSIFICATION_BLOCKED, never a slab by default
    mesh_cover_fit(...)                  whether stacked bar directions and two covers fit in a thickness

Lanes:
    GROUND_SLAB_CANDIDATE        a cell bounded by structural members, with no stair, opening or wall evidence
    LIFT_PIT_OPENING             the unhatched island of a hatched pit-wall ring
    STRUCTURAL_BEAM_OR_WALL      a hatched wall ring, a closed column outline or a beam band
    STAIR_OR_SPECIAL_STRUCTURE   a cell holding at least `min_treads` tread lines
    OUTSIDE_BUILDING             outside the building envelope
    CLASSIFICATION_BLOCKED       a sliver or a part whose evidence disagrees

A GROUND_SLAB_CANDIDATE is a population record only. This module gives it no thickness and no mesh.
"""

from __future__ import annotations

import math

GROUND_SLAB_CANDIDATE = "GROUND_SLAB_CANDIDATE"
LIFT_PIT_OPENING = "LIFT_PIT_OPENING"
STRUCTURAL_BEAM_OR_WALL = "STRUCTURAL_BEAM_OR_WALL"
STAIR_OR_SPECIAL_STRUCTURE = "STAIR_OR_SPECIAL_STRUCTURE"
OUTSIDE_BUILDING = "OUTSIDE_BUILDING"
CLASSIFICATION_BLOCKED = "CLASSIFICATION_BLOCKED"
LANES = (GROUND_SLAB_CANDIDATE, LIFT_PIT_OPENING, STRUCTURAL_BEAM_OR_WALL, STAIR_OR_SPECIAL_STRUCTURE,
         OUTSIDE_BUILDING, CLASSIFICATION_BLOCKED)
WITHIN = 0.999          # share of a part's area inside one evidence region for the part to take its class
TOUCH = 0.001           # a smaller share is a shared edge or rounding, not evidence


class RegionRecoveryError(ValueError):
    pass


def _geom():
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import polygonize, unary_union
    return LineString, Point, Polygon, polygonize, unary_union


# ------------------------------------------------------------------ partition
def partition(domain, barriers, *, eps_mm2=1e-3):
    """The faces of the arrangement of `barriers` (LineStrings) and the domain's own boundary, inside `domain`
    (a Polygon or MultiPolygon, holes allowed).

    Faces are sorted by (-area, x, y) of their representative point. A barrier that touches the domain only at a
    point or lies outside it changes nothing. Lines are not extended, snapped or closed."""
    LineString, Point, Polygon, polygonize, unary_union = _geom()
    if domain.is_empty or domain.area <= 0:
        raise RegionRecoveryError("empty domain")
    probe = domain.buffer(1.0)
    lines = [b for b in barriers if b.length > 0 and b.intersects(probe)]
    net = unary_union([domain.boundary] + lines)
    faces = []
    for f in polygonize(net):
        if f.area <= eps_mm2:
            continue
        rp = f.representative_point()
        if domain.contains(rp):
            faces.append(f)
    faces.sort(key=lambda f: (-round(f.area, 6), round(f.representative_point().x, 3),
                              round(f.representative_point().y, 3)))
    return faces


def tiling_proof(domain, parts, *, tol_mm2=1.0):
    """Areas in mm2: the parts must cover the domain exactly once."""
    _, _, _, _, unary_union = _geom()
    u = unary_union(parts) if parts else None
    s = math.fsum(p.area for p in parts)
    overlap = math.fsum(parts[i].intersection(parts[j]).area for i in range(len(parts))
                        for j in range(i + 1, len(parts)) if parts[i].intersects(parts[j]))
    gap = domain.difference(u).area if u is not None else domain.area
    excess = u.difference(domain).area if u is not None else 0.0
    out = {"domain_mm2": domain.area, "sum_mm2": s, "union_mm2": u.area if u is not None else 0.0,
           "overlap_mm2": overlap, "gap_mm2": gap, "excess_mm2": excess}
    out["exact"] = (abs(s - domain.area) <= tol_mm2 and overlap <= tol_mm2 and gap <= tol_mm2
                    and excess <= tol_mm2)
    return out


# ------------------------------------------------------------------ classification
def _share(part, region):
    return part.intersection(region).area / part.area if part.area else 0.0


def classify(part, *, envelope=None, openings=(), walls=(), columns=(), beam_bands=(), treads=(), min_treads=4,
             sliver_mm2=1000.0):
    """(lane, kind, evidence) for one part, from the evidence a caller read off the drawing.

    envelope     building envelope polygon (None: not tested)
    openings     [(id, polygon)] unhatched islands of hatched pit-wall rings
    walls        [(id, polygon)] hatched wall regions (islands removed)
    columns      [(id, polygon)] closed column outlines
    beam_bands   [(id, polygon)] beam centreline buffered by half its width (flat caps)
    treads       [(id, LineString)] tread lines; a tread counts when its midpoint is in the part

    Order: sliver, outside, opening, wall, column, beam, stair. A part partly inside an opening, wall, column or band
    but not within one of them is CLASSIFICATION_BLOCKED (its evidence disagrees). A part with none of that evidence
    is a GROUND_SLAB_CANDIDATE."""
    _, Point, _, _, _ = _geom()
    if part.area < sliver_mm2:
        return CLASSIFICATION_BLOCKED, "SLIVER", {"area_mm2": part.area}
    if envelope is not None and _share(part, envelope) < WITHIN:
        return OUTSIDE_BUILDING, "OUTSIDE_ENVELOPE", {"inside_share": _share(part, envelope)}
    partial = []
    for lane, kind, regions in ((LIFT_PIT_OPENING, "PIT_OPENING", openings),
                                (STRUCTURAL_BEAM_OR_WALL, "WALL", walls),
                                (STRUCTURAL_BEAM_OR_WALL, "COLUMN", columns),
                                (STRUCTURAL_BEAM_OR_WALL, "BEAM", beam_bands)):
        for rid, reg in regions:
            sh = _share(part, reg)
            if sh >= WITHIN:
                return lane, kind, {"evidence_id": rid, "share": sh}
            if sh > TOUCH:
                partial.append({"kind": kind, "evidence_id": rid, "share": sh})
    if partial:
        return CLASSIFICATION_BLOCKED, "EVIDENCE_DISAGREES", {"partial": partial}
    inside = [tid for tid, ln in treads if part.contains(Point(ln.interpolate(0.5, normalized=True)))]
    if len(inside) >= min_treads:
        return STAIR_OR_SPECIAL_STRUCTURE, "STAIR_FLIGHT_ZONE", {"treads": inside}
    return GROUND_SLAB_CANDIDATE, "CELL_BETWEEN_MEMBERS", {"treads": inside}


# ------------------------------------------------------------------ cover fit
def mesh_cover_fit(thickness_mm, bar_dias_mm, cover_bottom_mm, cover_top_mm):
    """Depth a mesh needs: bottom cover + every stacked bar diameter + top cover.

    One mesh 'each way' is two crossing directions, so its bars stack once: bar_dias_mm = (d_x, d_y). Top and bottom
    mats (T&B) are two meshes: (d_x, d_y, d_x, d_y). Nothing is assumed about spacers or tolerances."""
    if thickness_mm is None or thickness_mm <= 0:
        raise RegionRecoveryError("thickness must be a positive source value")
    if any(d is None or d <= 0 for d in bar_dias_mm) or not bar_dias_mm:
        raise RegionRecoveryError("bar diameters must be positive")
    if cover_bottom_mm is None or cover_top_mm is None:
        return {"required_mm": None, "available_mm": thickness_mm, "margin_mm": None, "fits": None}
    need = cover_bottom_mm + math.fsum(bar_dias_mm) + cover_top_mm
    return {"required_mm": need, "available_mm": thickness_mm, "margin_mm": thickness_mm - need,
            "fits": need <= thickness_mm}
