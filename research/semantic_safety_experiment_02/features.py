"""Canonical architectural features, built from source geometry alone.

The sampling unit is the FEATURE, not the seed and not the interval. Every
interval on the floor belongs to exactly one feature, so no feature can be
sampled twice - which is the defect the frozen experiments exposed twice
over, once in their own sampling and once in the scoring canonicalisation
that tried to repair it afterwards.

Nothing here consults a semantic answer. Features are grown from entity
identity, endpoints, intersection, parallelism and block membership, and
growth stops on a declared geometric extent cap, because without one the
wall network is a single component and the whole floor is one feature.
"""

from __future__ import annotations

import math

from research.semantic_safety_experiment_02 import protocol as P


def parent_of(interval_id: str) -> str:
    return interval_id.split(":", 1)[-1].rsplit("#", 1)[0]


def _vec(iv):
    return (iv.end_mm[0] - iv.start_mm[0], iv.end_mm[1] - iv.start_mm[1])


def _unit(iv):
    dx, dy = _vec(iv)
    n = math.hypot(dx, dy)
    return (dx / n, dy / n) if n else (1.0, 0.0)


def _angle(iv):
    dx, dy = _vec(iv)
    return math.degrees(math.atan2(dy, dx)) % 180.0


def parallel(a, b, deg=P.PARALLEL_DEG) -> bool:
    d = abs(_angle(a) - _angle(b)) % 180.0
    return min(d, 180.0 - d) <= deg


def offset_overlap(a, b):
    ux, uy = _unit(a)
    nx, ny = -uy, ux
    ax, ay = a.start_mm
    o1 = (b.start_mm[0] - ax) * nx + (b.start_mm[1] - ay) * ny
    o2 = (b.end_mm[0] - ax) * nx + (b.end_mm[1] - ay) * ny
    t1 = (b.start_mm[0] - ax) * ux + (b.start_mm[1] - ay) * uy
    t2 = (b.end_mm[0] - ax) * ux + (b.end_mm[1] - ay) * uy
    lo, hi = sorted((t1, t2))
    return ((abs(o1) + abs(o2)) / 2.0,
            max(0.0, min(hi, a.length_mm) - max(lo, 0.0)))


def endpoints_meet(a, b, tol=P.JOIN_MM) -> bool:
    for p in (a.start_mm, a.end_mm):
        for q in (b.start_mm, b.end_mm):
            if math.hypot(p[0] - q[0], p[1] - q[1]) <= tol:
                return True
    return False


def _box(members):
    xs = [v for iv in members for v in (iv.start_mm[0], iv.end_mm[0])]
    ys = [v for iv in members for v in (iv.start_mm[1], iv.end_mm[1])]
    return [min(xs), min(ys), max(xs), max(ys)]


def _extent(box):
    return max(box[2] - box[0], box[3] - box[1])


def relation(a, b, *, block_of):
    """Why two intervals belong to one drawn thing. Source evidence only."""
    out = []
    if a.parent_object_id == b.parent_object_id:
        out.append("SAME_PARENT_ENTITY")
    if endpoints_meet(a, b):
        out.append("SHARED_ENDPOINT")
    if parallel(a, b):
        off, ov = offset_overlap(a, b)
        if ov >= P.MIN_PARALLEL_OVERLAP_MM and 0.0 < off <= P.FEATURE_OFFSET_MM:
            out.append("PARALLEL_PAIR")
    ba, bb = block_of.get(a.interval_id), block_of.get(b.interval_id)
    if ba and ba == bb:
        out.append("COMMON_BLOCK")
    return out


def on_the_sheet_border(iv, rect, tol) -> bool:
    """Is this interval part of the SHEET rather than the FLOOR?

    The drawing region isolator establishes, frozen and deterministically,
    the rectangle this plan occupies on its sheet. The frame that
    rectangle is measured from, and the title block in its corner, are
    DRAWING, not BUILDING - and nothing in a floor plan is drawn flush
    against the sheet border.

    The test is applied to the INTERVAL, before any grouping, so a frame
    line can never join a plan feature and drag it out of the sample with
    it. Dropping whole features afterwards would have done that.
    """
    x0, y0, x1, y1 = rect
    for x, y in (iv.start_mm, iv.end_mm):
        if (abs(x - x0) <= tol or abs(x - x1) <= tol
                or abs(y - y0) <= tol or abs(y - y1) <= tol
                or x < x0 - tol or x > x1 + tol
                or y < y0 - tol or y > y1 + tol):
            return True
    return False


def build(intervals, *, block_of, sheet_rect=None,
          sheet_tol=P.SHEET_BORDER_TOL_MM):
    """Grow every interval into exactly one canonical feature.

    `sheet_rect` is the drawing region's own boundary rectangle. When it
    is given, intervals belonging to the sheet are removed HERE, before a
    single feature is grown, so the canonical feature population is built
    from floor geometry alone. SAFETY_SAMPLE_02 never asked, and sampled
    four frame sides and a title block as floor content.
    """
    from shapely.geometry import LineString
    from shapely.strtree import STRtree

    ivs = sorted((iv for iv in intervals if iv.length_mm > 0),
                 key=lambda x: x.interval_id)
    sheet_ivs = []
    if sheet_rect is not None:
        keep = []
        for iv in ivs:
            (sheet_ivs if on_the_sheet_border(iv, sheet_rect, sheet_tol)
             else keep).append(iv)
        ivs = keep
    build.sheet_intervals_removed = [iv.interval_id for iv in sheet_ivs]
    by_id = {iv.interval_id: iv for iv in ivs}
    geoms = [LineString([iv.start_mm, iv.end_mm]) for iv in ivs]
    tree = STRtree(geoms)
    reach = max(P.FEATURE_OFFSET_MM, P.JOIN_MM) + 1.0

    def near(iv):
        g = LineString([iv.start_mm, iv.end_mm]).buffer(reach)
        return [ivs[int(i)] for i in tree.query(g)]

    assigned, features = {}, []
    for seed in ivs:
        if seed.interval_id in assigned:
            continue
        members = [seed]
        box = _box(members)
        evidence, queue = [], [seed]
        assigned[seed.interval_id] = True
        while queue:
            cur = queue.pop(0)
            for cand in sorted(near(cur), key=lambda x: x.interval_id):
                if cand.interval_id in assigned:
                    continue
                if len(members) >= P.MAX_FEATURE_MEMBERS:
                    break
                why = relation(cur, cand, block_of=block_of)
                if not why:
                    continue
                if len(members) >= P.MAX_FEATURE_MEMBERS:
                    continue
                trial = _box(members + [cand])
                if _extent(trial) > P.MAX_FEATURE_EXTENT_MM:
                    continue
                assigned[cand.interval_id] = True
                members.append(cand)
                box = trial
                evidence.append({"FROM": cur.interval_id,
                                 "TO": cand.interval_id,
                                 "RELATIONS": why})
                queue.append(cand)
        features.append({
            "SEED_INTERVAL_ID": seed.interval_id,
            "SOURCE_INTERVAL_IDS": sorted(m.interval_id for m in members),
            "SOURCE_ENTITY_IDS": sorted({m.parent_object_id
                                         for m in members}),
            "ORIGINATING_SEED_IDS": [seed.interval_id],
            "MERGE_EVIDENCE": evidence,
            "bounding_box_mm": [round(v, 3) for v in box],
            "extent_mm": round(_extent(box), 3),
            "members": len(members),
            "_members": members,
        })
    for n, f in enumerate(sorted(features,
                                 key=lambda x: x["SEED_INTERVAL_ID"]),
                          start=1):
        f["CANONICAL_FEATURE_ID"] = f"{P.CANONICAL_ID_PREFIX}{n:04d}"
    return sorted(features, key=lambda x: x["CANONICAL_FEATURE_ID"])
