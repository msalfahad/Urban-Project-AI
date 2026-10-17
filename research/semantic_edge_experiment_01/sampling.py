"""Mechanical sampling and local feature assembly. No meaning is inferred.

Two stages, both deterministic and both blind to the semantic answer:

    WHICH NEIGHBOURHOODS DO WE LOOK AT   the ten strata of the frozen
                                         protocol, quota-filled in stable
                                         id order
    WHICH ENTITIES GO IN THE PICTURE     the assembly rules, which ask
                                         only what must be shown together
                                         for a local architectural feature
                                         to be understandable at all

Nothing here reads a role in order to decide anything except eligibility,
and eligibility is the absence of a settled role, which is the population
the experiment exists to sample from.
"""

from __future__ import annotations

import hashlib
import math

from engine import cad_entity_role as cer
from engine import interval_role as ir
from research.semantic_edge_experiment_01 import protocol as P

# Roles that count as linework the deterministic layer DID settle, used
# for the hull, for the door and stair proximity tests and for the
# casework offset test. Never to decide what a sampled thing means.
ESTABLISHED_MATERIAL = (ir.MATERIAL_WALL_FACE, ir.GLAZING, ir.COLUMN)
UNSETTLED_ROLES = (ir.COLUMN_CANDIDATE_UNRESOLVED, ir.AMBIGUOUS_PAIRED_BAND)
WEAK_CONFIDENCE = (cer.NOT_ESTABLISHED, cer.LOW, "")


def eligible(iv) -> bool:
    """The population: what the deterministic layer did not settle."""
    if iv.length_mm <= 0:
        return False
    if iv.role == ir.UNKNOWN:
        return True
    if iv.role in UNSETTLED_ROLES:
        return True
    return iv.confidence in WEAK_CONFIDENCE


# ---------------------------------------------------------------- geometry

def _vec(iv):
    return (iv.end_mm[0] - iv.start_mm[0], iv.end_mm[1] - iv.start_mm[1])


def _unit(iv):
    dx, dy = _vec(iv)
    n = math.hypot(dx, dy)
    return (dx / n, dy / n) if n else (1.0, 0.0)


def _angle_deg(iv):
    dx, dy = _vec(iv)
    return math.degrees(math.atan2(dy, dx)) % 180.0


def _parallel(a, b, deg=P.PARALLEL_DEG) -> bool:
    d = abs(_angle_deg(a) - _angle_deg(b)) % 180.0
    return min(d, 180.0 - d) <= deg


def _offset_and_overlap(a, b):
    """b's perpendicular offset from a, and how far they run together."""
    ux, uy = _unit(a)
    nx, ny = -uy, ux
    ax, ay = a.start_mm
    o1 = (b.start_mm[0] - ax) * nx + (b.start_mm[1] - ay) * ny
    o2 = (b.end_mm[0] - ax) * nx + (b.end_mm[1] - ay) * ny
    t1 = (b.start_mm[0] - ax) * ux + (b.start_mm[1] - ay) * uy
    t2 = (b.end_mm[0] - ax) * ux + (b.end_mm[1] - ay) * uy
    lo, hi = sorted((t1, t2))
    overlap = max(0.0, min(hi, a.length_mm) - max(lo, 0.0))
    return (abs(o1) + abs(o2)) / 2.0, overlap


def _near(a, b) -> float:
    """Cheap distance between two interval chords."""
    from shapely.geometry import LineString
    return LineString([a.start_mm, a.end_mm]).distance(
        LineString([b.start_mm, b.end_mm]))


def _endpoints_meet(a, b, tol) -> bool:
    for p in (a.start_mm, a.end_mm):
        for q in (b.start_mm, b.end_mm):
            if math.hypot(p[0] - q[0], p[1] - q[1]) <= tol:
                return True
    return False


# ------------------------------------------------------------ the strata

def _index(intervals):
    from shapely.geometry import LineString
    from shapely.strtree import STRtree
    geoms = [LineString([iv.start_mm, iv.end_mm]) if iv.length_mm > 0
             else LineString([iv.start_mm,
                              (iv.start_mm[0] + 1e-6, iv.start_mm[1])])
             for iv in intervals]
    return geoms, STRtree(geoms)


def _within(tree, geoms, intervals, iv, radius):
    from shapely.geometry import LineString
    g = LineString([iv.start_mm, iv.end_mm])
    out = []
    for i in tree.query(g.buffer(radius)):
        j = int(i)
        if intervals[j].interval_id == iv.interval_id:
            continue
        if geoms[j].distance(g) <= radius:
            out.append(intervals[j])
    return out


def classify_strata(intervals):
    """Every eligible seed's stratum, by the first predicate it satisfies."""
    from shapely.geometry import LineString, MultiPoint

    geoms, tree = _index(intervals)
    by_role = {}
    for iv in intervals:
        by_role.setdefault(iv.role, []).append(iv)

    pts = [p for iv in intervals if iv.role in ESTABLISHED_MATERIAL
           for p in (iv.start_mm, iv.end_mm)]
    hull = MultiPoint(pts).convex_hull if len(pts) >= 3 else None
    skin = hull.boundary if hull is not None else None

    doors = {iv.interval_id for iv in by_role.get(ir.DOOR, ())}
    stairs = {iv.interval_id for iv in by_role.get(ir.STAIR_GEOMETRY, ())}
    material = {iv.interval_id for iv in intervals
                if iv.role in ESTABLISHED_MATERIAL}

    rows = []
    for iv in intervals:
        if not eligible(iv):
            continue
        g = LineString([iv.start_mm, iv.end_mm])
        mid = g.interpolate(0.5, normalized=True)
        on_envelope = (skin is not None
                       and skin.distance(mid) <= P.ENVELOPE_BAND_MM)

        near_curve = P.CURVE_REACH_MM
        neigh = _within(tree, geoms, intervals, iv,
                        max(P.CURVE_REACH_MM, P.STAIR_REACH_MM,
                            P.DOOR_REACH_MM, P.ASSEMBLY_OFFSET_MM))
        near_door = any(n.interval_id in doors
                        and _near(iv, n) <= P.DOOR_REACH_MM for n in neigh)
        near_stair = any(n.interval_id in stairs
                         and _near(iv, n) <= P.STAIR_REACH_MM for n in neigh)
        near_arc = (iv.kind in ("ARC", "CIRCLE")
                    or any(n.kind in ("ARC", "CIRCLE")
                           and _near(iv, n) <= near_curve for n in neigh))

        offsets, wall_partners, casework_partner = set(), 0, False
        for n in neigh:
            if not _parallel(iv, n):
                continue
            off, ov = _offset_and_overlap(iv, n)
            if ov < P.MIN_PARALLEL_OVERLAP_MM or off <= 1.0:
                continue
            if off <= P.PARALLEL_FAMILY_SPAN_MM:
                offsets.add(round(off / 10.0))
            if P.WALL_SEPARATION_MIN_MM <= off <= P.WALL_SEPARATION_MAX_MM:
                wall_partners += 1
            if (n.interval_id in material
                    and P.CASEWORK_DEPTH_MIN_MM <= off
                    <= P.CASEWORK_DEPTH_MAX_MM):
                casework_partner = True

        meets_material = any(n.interval_id in material
                             and _endpoints_meet(iv, n, P.JUNCTION_MM)
                             for n in neigh)
        meets_anything = any(_endpoints_meet(iv, n, P.JUNCTION_MM)
                             for n in neigh)

        if on_envelope and len(offsets) >= P.PARALLEL_FAMILY_MIN:
            s = P.STRATUM_A
        elif len(offsets) >= P.PARALLEL_FAMILY_MIN:
            s = P.STRATUM_B
        elif near_door:
            s = P.STRATUM_C
        elif wall_partners == 1:
            s = P.STRATUM_D
        elif casework_partner:
            s = P.STRATUM_E
        elif near_stair:
            s = P.STRATUM_F
        elif near_arc:
            s = P.STRATUM_G
        elif meets_material and on_envelope:
            s = P.STRATUM_H
        elif (not meets_anything
              and iv.length_mm >= P.SEPARATOR_MIN_LENGTH_MM):
            s = P.STRATUM_I
        else:
            s = P.STRATUM_J

        rows.append({
            "INTERVAL_ID": iv.interval_id,
            "PARENT_OBJECT_ID": iv.parent_object_id,
            "STRATUM": s,
            "LAYER": iv.layer,
            "ENTITY_TYPE": iv.entity_type,
            "KIND": iv.kind,
            "length_mm": round(iv.length_mm, 3),
            "E1_4_ROLE": iv.role,
            "E1_4_CONFIDENCE": iv.confidence,
            "WHY_ELIGIBLE": ("no role is established" if iv.role == ir.UNKNOWN
                             else "the role layer marks this role unsettled"
                             if iv.role in UNSETTLED_ROLES
                             else "the role carries a weak confidence"),
            "MECHANICAL_FACTS": {
                "ON_THE_ENVELOPE_BAND": bool(on_envelope),
                "DISTINCT_PARALLEL_OFFSETS": len(offsets),
                "A_DOOR_IS_NEAR": bool(near_door),
                "PARTNERS_AT_A_WALL_THICKNESS": wall_partners,
                "A_MATERIAL_FACE_AT_FITTED_UNIT_DEPTH": bool(casework_partner),
                "STAIR_GEOMETRY_IS_NEAR": bool(near_stair),
                "A_CURVE_IS_NEAR_OR_IT_IS_ONE": bool(near_arc),
                "AN_ENDPOINT_MEETS_ESTABLISHED_MATERIAL": bool(meets_material),
                "NEITHER_END_MEETS_ANYTHING": not meets_anything,
            },
        })
    return rows, (geoms, tree)


def select(rows):
    """Quota per stratum in stable id order, then a declared top-up."""
    rows = sorted(rows, key=lambda r: r["INTERVAL_ID"])
    picked, by_stratum, shortfalls = [], {}, {}
    for s in P.STRATA:
        pool = [r for r in rows if r["STRATUM"] == s]
        take = pool[:P.PER_STRATUM_QUOTA]
        by_stratum[s] = len(pool)
        if len(take) < P.PER_STRATUM_QUOTA:
            shortfalls[s] = {"available": len(pool),
                             "quota": P.PER_STRATUM_QUOTA}
        for r in take:
            picked.append({**r, "SELECTED_BY": "PER_STRATUM_QUOTA"})
    chosen = {r["INTERVAL_ID"] for r in picked}
    for r in rows:
        if len(picked) >= P.SAMPLE_TARGET:
            break
        if r["INTERVAL_ID"] in chosen:
            continue
        picked.append({**r, "SELECTED_BY": "TOPPED_UP"})
        chosen.add(r["INTERVAL_ID"])
    return picked, by_stratum, shortfalls


# -------------------------------------------------------- feature assembly

def assemble(seed, intervals, index, *, by_id):
    """Which entities must be shown together. No meaning is inferred."""
    from shapely.geometry import LineString

    geoms, tree = index
    radius = max(P.ASSEMBLY_OFFSET_MM, P.ASSEMBLY_HALO_MM,
                 P.CURVE_REACH_MM, P.DOOR_REACH_MM)
    g = LineString([seed.start_mm, seed.end_mm])
    halo = g.buffer(P.ASSEMBLY_HALO_MM)

    primary, context, why = [seed], [], {}
    seen = {seed.interval_id}
    for n in _within(tree, geoms, intervals, seed, radius):
        reasons = []
        d = _near(seed, n)
        if n.parent_object_id == seed.parent_object_id:
            reasons.append("COMMON_PARENT_OBJECT")
        if _endpoints_meet(seed, n, P.JOIN_MM):
            reasons.append("SHARED_ENDPOINT")
        if d <= 1.0:
            reasons.append("INTERSECTION")
        if _parallel(seed, n):
            off, ov = _offset_and_overlap(seed, n)
            if ov >= P.MIN_PARALLEL_OVERLAP_MM and off <= P.ASSEMBLY_OFFSET_MM:
                reasons.append("PARALLEL_OFFSET")
        blk = (seed.provenance or {}).get("block_id")
        if blk and blk == (n.provenance or {}).get("block_id"):
            reasons.append("COMMON_BLOCK")
        if halo.intersects(LineString([n.start_mm, n.end_mm])):
            reasons.append("LOCAL_REGION")
        if n.kind in ("ARC", "CIRCLE") and d <= P.CURVE_REACH_MM:
            reasons.append("NEARBY_ARC")
        if n.role == ir.DOOR and d <= P.DOOR_REACH_MM:
            reasons.append("NEARBY_OPENING")
        if not reasons:
            continue
        seen.add(n.interval_id)
        why[n.interval_id] = {"REASONS": sorted(set(reasons)),
                              "distance_mm": round(d, 3)}
        # an interval of the SAME CAD entity is part of the thing asked
        # about; everything else is context around it
        (primary if n.parent_object_id == seed.parent_object_id
         else context).append(n)

    context.sort(key=lambda n: (why[n.interval_id]["distance_mm"],
                                n.interval_id))
    dropped = max(0, len(context) - P.MAX_CONTEXT_ENTITIES)
    context = context[:P.MAX_CONTEXT_ENTITIES]
    members = primary + context

    xs = [v for iv in members for v in (iv.start_mm[0], iv.end_mm[0])]
    ys = [v for iv in members for v in (iv.start_mm[1], iv.end_mm[1])]
    box = [round(min(xs), 3), round(min(ys), 3),
           round(max(xs), 3), round(max(ys), 3)]

    gid = "FG-" + hashlib.sha256(
        "|".join(sorted(iv.interval_id for iv in members)).encode()
    ).hexdigest()[:12]

    return {
        "FEATURE_GROUP_ID": gid,
        "SEED_INTERVAL_ID": seed.interval_id,
        "PRIMARY_ENTITY_IDS": sorted(iv.interval_id for iv in primary),
        "CONTEXT_ENTITY_IDS": sorted(iv.interval_id for iv in context),
        "LAYERS": sorted({str(iv.layer) for iv in members}),
        "LINETYPES": sorted({str((iv.provenance or {}).get("linetype") or
                                 (by_id.get(iv.parent_object_id) and
                                  getattr(by_id[iv.parent_object_id],
                                          "linetype", "")) or "")
                             for iv in members} - {""}),
        "ENTITY_TYPES": sorted({str(iv.entity_type) for iv in members}),
        "BLOCK_IDS": sorted({str((iv.provenance or {}).get("block_id"))
                             for iv in members
                             if (iv.provenance or {}).get("block_id")}),
        "LOCAL_TOPOLOGY": {
            "members": len(members),
            "primary_members": len(primary),
            "context_members": len(context),
            "context_members_dropped_by_the_cap": dropped,
            "WHY_EACH_CONTEXT_MEMBER_IS_HERE": {
                k: v for k, v in why.items()
                if k in set(iv.interval_id for iv in context)},
            "bounding_box_mm": box,
            "extent_mm": [round(box[2] - box[0], 3),
                          round(box[3] - box[1], 3)],
        },
        "SOURCE_HANDLES": sorted({
            str((iv.provenance or {}).get("handle"))
            for iv in members if (iv.provenance or {}).get("handle")}),
        "_members": members,
        "_box": box,
    }
