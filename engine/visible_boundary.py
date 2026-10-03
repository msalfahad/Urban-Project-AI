"""E1.3 — what bounds this point, taken by looking out from it.

The first attempt at an open region's boundary used a local window to
close the material into a walkable face. A cold challenge destroyed it,
and correctly. Two things compound:

    engine.cad_geometry.boundary_of() walks face.exterior only, so the
    HOLES of a face are dropped; and

    for a seed that no drawn material encloses, the smallest face
    containing it is the free space AROUND the building's blocks. Its
    exterior is the window, and the real rooms inside it are exactly the
    holes that get dropped.

The result was a figure made of the window with the rooms it had flowed
around cut out of it - which is what the challenger saw and named: "the
WASH room and the KITCHEN are each drawn as their own closed black
rings, held out as islands inside the area. An adjacent room can only
become an island if the surrounding figure has flowed around it."

So this module does not build a face at all. It stands at the point the
label sits on and looks outwards. In every direction either drawn
material is the first thing met - and that stretch of material bounds
this point - or nothing is, and the drawing establishes no boundary that
way. The runs of material come back in order, and between consecutive
runs sits a connector whose two ends are REAL WALL ENDS, so the chain
carries no window and no invented extent anywhere.
"""

from __future__ import annotations

import hashlib
import math

MODEL = "A_BOUNDARY_IS_WHAT_THIS_POINT_CAN_SEE_V1"

# How far out to look. A ray that reaches this without meeting material
# has established that nothing bounds the point that way, within a
# distance far larger than any room on a domestic floor.
DEFAULT_REACH_MM = 30000.0

# Rays are cast at every material endpoint, nudged either side so a run's
# true extent is captured, plus a uniform fan so that a gap between two
# runs cannot be missed entirely.
ENDPOINT_NUDGE_RAD = 1e-5
UNIFORM_RAYS = 720

# Two consecutive rays that meet the same entity belong to one run.
# A run shorter than this is noise from a grazing hit at a corner.
MIN_RUN_MM = 20.0

NO_WINDOW_IS_INVOLVED = (
    "every element of this chain has both ends on drawn material. A run "
    "of material ends where the material ends; a connector spans from one "
    "real wall end to the next. Nothing here is the edge of a search "
    "window, a reach limit or any other artefact of the method, so every "
    "coordinate in the chain is a coordinate the drawing gives")

WHAT_AN_UNBOUNDED_DIRECTION_MEANS = (
    "where a ray reaches the full search distance without meeting drawn "
    "material, the drawing establishes no boundary in that direction. "
    "That is a result about the drawing. The distance the ray travelled "
    "is not - it is the search distance, and it is never reported as "
    "geometry")


def model_hash() -> str:
    parts = [MODEL, str(DEFAULT_REACH_MM), str(UNIFORM_RAYS),
             str(MIN_RUN_MM)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _ray_hit(seed, ang, segs, tree, reach):
    """The nearest drawn material along this ray, or None."""
    from shapely.geometry import LineString, Point

    far = (seed[0] + reach * math.cos(ang), seed[1] + reach * math.sin(ang))
    ray = LineString([seed, far])
    best, best_d, best_pt = None, None, None
    for idx in tree.query(ray):
        i = int(idx)
        hit = ray.intersection(segs[i]["line"])
        if hit.is_empty:
            continue
        pts = ([hit] if hit.geom_type == "Point"
               else list(getattr(hit, "geoms", [])) or
               [Point(c) for c in getattr(hit, "coords", [])])
        for p in pts:
            if p.geom_type != "Point":
                continue
            d = math.hypot(p.x - seed[0], p.y - seed[1])
            if d <= 1e-6:
                continue
            if best_d is None or d < best_d:
                best, best_d, best_pt = i, d, (p.x, p.y)
    if best is None:
        return None
    return {"seg": best, "dist": best_d, "point": best_pt}



WHAT_LIES_PAST_A_WALL_END = (
    "the sight line slipped past the end of a piece of drawn material and "
    "landed on something behind it. A wall end is where one space stops "
    "being separated from the next, so what stands beyond it bounds that "
    "next space and not this point. It is left out of the chain, and the "
    "chain stops at the wall end")


def _shadow_past_wall_ends(seed, samples, segs, tree, ends_xy, *,
                           tol_mm=2.0):
    """Mark every sample whose hit lies behind a wall end the sweep passed."""
    n = len(samples)
    if n < 3 or not ends_xy:
        return

    def dist(i):
        h = samples[i]["hit"]
        return None if h is None else h["dist"]

    def at_a_wall_end(i):
        h = samples[i]["hit"]
        if h is None:
            return False
        px, py = h["point"]
        return any(math.hypot(px - ex, py - ey) <= tol_mm
                   for (ex, ey) in ends_xy)

    events = []
    for i in range(n):
        j = (i + 1) % n
        di, dj = dist(i), dist(j)
        if di is None or dj is None or abs(di - dj) <= tol_mm:
            continue
        if di < dj and at_a_wall_end(i):
            events.append((i, +1, di))      # sweeping forward, past end i
        elif dj < di and at_a_wall_end(j):
            events.append((j, -1, dj))      # sweeping backward, past end j

    for start, step, near in events:
        k = (start + step) % n
        for _ in range(n - 1):
            d = dist(k)
            if d is None or d <= near + tol_mm:
                break
            samples[k]["BEHIND_A_WALL_END"] = True
            samples[k]["why_behind"] = WHAT_LIES_PAST_A_WALL_END
            k = (k + step) % n


def look_around(seed, segments, *, reach_mm=DEFAULT_REACH_MM,
                uniform_rays=UNIFORM_RAYS) -> dict:
    """Stand at `seed` and record what bounds it, in order, all the way round.

    `segments` are dicts with `points` (a densified polyline of drawn
    material) and whatever provenance the caller wants carried through.
    """
    from shapely.geometry import LineString
    from shapely.strtree import STRtree

    segs = []
    for s in segments:
        pts = list(s.get("points") or ())
        if len(pts) < 2:
            continue
        segs.append(dict(s, line=LineString(pts)))
    if not segs:
        return {"MODEL": MODEL, "runs": [], "rays": 0,
                "why": "no drawn material lies within reach of this point"}

    tree = STRtree([s["line"] for s in segs])
    ends_xy = [e["point"] for e in free_ends(segments)]

    angles = set()
    for i in range(uniform_rays):
        angles.add(2.0 * math.pi * i / uniform_rays)
    for s in segs:
        for (x, y) in s["line"].coords:
            a = math.atan2(y - seed[1], x - seed[0])
            angles.add(a - ENDPOINT_NUDGE_RAD)
            angles.add(a)
            angles.add(a + ENDPOINT_NUDGE_RAD)
    ordered = sorted(a % (2.0 * math.pi) for a in angles)

    samples = []
    for a in ordered:
        h = _ray_hit(seed, a, segs, tree, reach_mm)
        samples.append({"angle": a, "hit": h})

    # A sight line that slips PAST A WALL END lands on whatever stands
    # behind it, and what stands behind a wall end bounds a different
    # space, not this one. The drawing marks the moment it happens: the
    # distance jumps, and the near side of the jump sits on an endpoint of
    # material that nothing else touches - a wall end. From there until
    # the sweep comes back to something as close as that wall end, every
    # hit is behind it, and none of it is recorded as bounding this point.
    _shadow_past_wall_ends(seed, samples, segs, tree, ends_xy)

    # group consecutive samples that met the same entity into one run
    runs, cur = [], None
    for smp in samples:
        h = None if smp.get("BEHIND_A_WALL_END") else smp["hit"]
        key = None if h is None else segs[h["seg"]].get("key", h["seg"])
        if cur is not None and cur["key"] == key:
            cur["samples"].append(smp)
            continue
        if cur is not None:
            runs.append(cur)
        cur = {"key": key, "seg": None if h is None else h["seg"],
               "samples": [smp]}
    if cur is not None:
        runs.append(cur)
    # the fan wraps: if first and last runs are the same entity, join them
    if len(runs) > 1 and runs[0]["key"] == runs[-1]["key"]:
        runs[0]["samples"] = runs[-1]["samples"] + runs[0]["samples"]
        runs.pop()

    out = []
    for r in runs:
        hits = [s["hit"] for s in r["samples"]
                if s["hit"] is not None and not s.get("BEHIND_A_WALL_END")]
        if r["key"] is None or not hits:
            out.append({"KIND": "NOTHING_MET",
                        "angle_from": r["samples"][0]["angle"],
                        "angle_to": r["samples"][-1]["angle"],
                        "why": WHAT_AN_UNBOUNDED_DIRECTION_MEANS})
            continue
        a, b = hits[0]["point"], hits[-1]["point"]
        if math.hypot(b[0] - a[0], b[1] - a[1]) < MIN_RUN_MM:
            out.append({"KIND": "NOTHING_MET",
                        "angle_from": r["samples"][0]["angle"],
                        "angle_to": r["samples"][-1]["angle"],
                        "why": "only a grazing corner hit, too short to be "
                               "a bounding run of material"})
            continue
        src = segs[r["seg"]]
        out.append({
            "KIND": "MATERIAL_RUN",
            "start_mm": [round(a[0], 3), round(a[1], 3)],
            "end_mm": [round(b[0], 3), round(b[1], 3)],
            "angle_from": r["samples"][0]["angle"],
            "angle_to": r["samples"][-1]["angle"],
            **{k: v for k, v in src.items()
               if k not in ("points", "line", "key")},
        })
    return {"MODEL": MODEL, "runs": out, "rays": len(samples),
            "reach_mm": reach_mm,
            "material_runs": sum(1 for r in out if r["KIND"] == "MATERIAL_RUN"),
            "directions_with_nothing_met":
                sum(1 for r in out if r["KIND"] == "NOTHING_MET"),
            "no_window_is_involved": NO_WINDOW_IS_INVOLVED,
            "what_an_unbounded_direction_means":
                WHAT_AN_UNBOUNDED_DIRECTION_MEANS}


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "DEFAULT_REACH_MM": DEFAULT_REACH_MM,
        "UNIFORM_RAYS": UNIFORM_RAYS,
        "ENDPOINT_NUDGE_RAD": ENDPOINT_NUDGE_RAD,
        "MIN_RUN_MM": MIN_RUN_MM,
        "why": {
            "no_window_is_involved": NO_WINDOW_IS_INVOLVED,
            "what_an_unbounded_direction_means":
                WHAT_AN_UNBOUNDED_DIRECTION_MEANS,
        },
    }


# --------------------------------------------------------------------------
# Mouths.
#
# The first version of this module looked out from the point and took the
# first material met in every direction. In a room that opens onto another
# room that is not a boundary: the ray leaves through the opening and
# lands on the far wall of a space twenty metres away, and that wall is
# not what bounds the point. The overlay showed it plainly - a PANTRY
# whose proposed boundary reached into the stair core and the bathrooms.
#
# What stops the sight line is the mouth of the opening: the span from
# one wall end to the wall end facing it. Both of those are places the
# drawing puts material and then stops putting it, so a mouth is read off
# the drawing and never invented. A mouth carries the boundary across and
# contributes no material; what class of thing it is - a door, a junction
# in the drafting, or an edge that is simply open - is the gap ontology's
# decision, not this module's.

# A material endpoint that nothing else touches is a wall end.
FREE_END_TOL_MM = 2.0

A_MOUTH_IS_NOT_A_WALL = (
    "a mouth spans from one wall end to the wall end facing it. Both ends "
    "are drawn material. The span itself is not: it contributes no wall "
    "length, and what kind of opening it is, is decided by the gap "
    "ontology against the drawing's own evidence")


def free_ends(segments, *, tol_mm=FREE_END_TOL_MM):
    """The endpoints of drawn material that no other drawn material touches.

    Each one carries the direction the material runs AWAY from it - the
    way the wall would continue if it continued - because that is what
    decides whether two ends face each other across a gap.
    """
    from shapely.geometry import LineString, Point
    from shapely.strtree import STRtree

    lines, keep = [], []
    for s in segments:
        pts = list(s.get("points") or ())
        if len(pts) < 2:
            continue
        lines.append(LineString(pts))
        keep.append(s)
    if not lines:
        return []
    tree = STRtree(lines)

    out = []
    for i, ln in enumerate(lines):
        coords = list(ln.coords)
        for p, inward in ((coords[0], coords[1]), (coords[-1], coords[-2])):
            pt = Point(p)
            touched = False
            for idx in tree.query(pt.buffer(tol_mm)):
                j = int(idx)
                if j == i:
                    continue
                if lines[j].distance(pt) <= tol_mm:
                    touched = True
                    break
            if touched:
                continue
            dx, dy = p[0] - inward[0], p[1] - inward[1]
            n = math.hypot(dx, dy) or 1.0
            out.append({"point": (p[0], p[1]),
                        "heading": (dx / n, dy / n),
                        "object_id": keep[i].get("object_id"),
                        "source": keep[i]})
    return out


def _clear_of_material(a, b, lines, tree, *, tol_mm):
    """True when the open span a..b meets no drawn material between its ends."""
    from shapely.geometry import LineString, Point

    span = LineString([a, b])
    ends = (Point(a), Point(b))
    for idx in tree.query(span):
        ln = lines[int(idx)]
        hit = span.intersection(ln)
        if hit.is_empty:
            continue
        parts = ([hit] if hit.geom_type in ("Point", "LineString")
                 else list(getattr(hit, "geoms", [])))
        for p in parts:
            if p.geom_type == "LineString":
                if p.length > tol_mm:
                    return False
                p = p.interpolate(0.5, normalized=True)
            if p.geom_type != "Point":
                return False
            if min(p.distance(e) for e in ends) > tol_mm:
                return False
    return True


def _face_each_other(a, b, *, junction_mm, cos_lim):
    """The pairing rule a doorway has to satisfy, and a corner repair need not.

    Taken unchanged from how a gap between two wall ends is proposed in the
    first place: a doorway lies ALONG a wall, so the span has to continue
    BOTH walls along their own lines. A corner gap is perpendicular by
    nature and is admitted on proximity alone. Two ends that satisfy
    neither are not facing each other and the span between them is not the
    mouth of anything.
    """
    pa, pb = a["point"], b["point"]
    gap = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
    if gap <= 0.0:
        return False, gap, None
    if gap <= junction_mm:
        return True, gap, "A_CORNER_GAP_ADMITTED_ON_PROXIMITY"
    ux, uy = (pb[0] - pa[0]) / gap, (pb[1] - pa[1]) / gap
    ha, hb = a["heading"], b["heading"]
    if (ha[0] * ux + ha[1] * uy >= cos_lim
            and hb[0] * -ux + hb[1] * -uy >= cos_lim):
        return True, gap, "BOTH_WALLS_RUN_TOWARD_EACH_OTHER_ALONG_THEIR_LINES"
    return False, gap, None


def mouths(seed, segments, *, reach_mm=DEFAULT_REACH_MM,
           tol_mm=FREE_END_TOL_MM, junction_mm=None, collinear_deg=None,
           max_ends=400):
    """Spans from one wall end to the wall end facing it, shortest first.

    A span is taken only when the two ends face each other by the same
    rule that proposes a gap anywhere else in this system, both ends can
    be seen from `seed`, nothing is built along the span, and it crosses
    no span already taken.
    """
    from shapely.geometry import LineString
    from shapely.strtree import STRtree

    from . import cad_geometry as cg
    if junction_mm is None:
        junction_mm = cg.JUNCTION_GAP_MM
    if collinear_deg is None:
        collinear_deg = cg.COLLINEAR_DEG
    cos_lim = math.cos(math.radians(collinear_deg))

    lines = []
    for s in segments:
        pts = list(s.get("points") or ())
        if len(pts) < 2:
            continue
        lines.append(LineString(pts))
    if not lines:
        return []
    tree = STRtree(lines)

    ends = free_ends(segments, tol_mm=tol_mm)
    if seed is None:
        # every wall end on the floor, with no point of view involved
        seen = sorted(ends, key=lambda e: (e["point"][0], e["point"][1]))
    else:
        ends = [e for e in ends
                if math.hypot(e["point"][0] - seed[0],
                              e["point"][1] - seed[1]) <= reach_mm]
        # a wall end this point cannot see cannot be the mouth of the
        # space this point stands in
        seen = []
        for e in ends:
            if _clear_of_material(seed, e["point"], lines, tree,
                                  tol_mm=tol_mm):
                seen.append(e)
        seen.sort(key=lambda e: math.hypot(e["point"][0] - seed[0],
                                           e["point"][1] - seed[1]))
        seen = seen[:max_ends]

    pairs = []
    for i in range(len(seen)):
        for j in range(i + 1, len(seen)):
            ok, gap, why = _face_each_other(
                seen[i], seen[j], junction_mm=junction_mm, cos_lim=cos_lim)
            if not ok or gap <= tol_mm:
                continue
            pairs.append((gap, i, j, why))
    pairs.sort(key=lambda r: r[0])

    taken, taken_lines = [], []
    for gap, i, j, why in pairs:
        a, b = seen[i]["point"], seen[j]["point"]
        if not _clear_of_material(a, b, lines, tree, tol_mm=tol_mm):
            continue
        span = LineString([a, b])
        if any(span.crosses(ln) for ln in taken_lines):
            continue
        taken_lines.append(span)
        taken.append({
            "points": [a, b],
            "IS_A_MOUTH": True,
            "span_mm": round(gap, 3),
            "TWO_ENDS_FACE_EACH_OTHER_BECAUSE": why,
            "mouth_start_mm": [round(a[0], 3), round(a[1], 3)],
            "mouth_end_mm": [round(b[0], 3), round(b[1], 3)],
            "wall_end_object_ids": [seen[i].get("object_id"),
                                    seen[j].get("object_id")],
            "key": f"MOUTH::{seen[i].get('object_id')}::"
                   f"{seen[j].get('object_id')}::{round(gap, 3)}",
            "why": A_MOUTH_IS_NOT_A_WALL,
        })
    return taken
