"""E1.2 — a role belongs to an interval, never to an entity.

E1.1 asked "what is this line?" and answered once per line. This module
asks "what is this stretch of this line?" and answers once per stretch,
because the evidence changes along the line and the answer has to change
with it.

Five corrections the external review of E1.1 required, all of them here:

    §3  PAIRING EVIDENCE IS INTERVAL LOCAL. The support of a counter-face
        is the UNION of its fragments, the entity is cut at the union's
        edges, and only the covered stretch receives
        PAIRED_WALL_FACE_EVIDENCE. Every supporting fragment is kept in
        provenance - E1.1 recorded one partner where the decision came
        from several

    §4  A SMALL CLOSED LOOP IS A COLUMN CANDIDATE, NOT A COLUMN. E1.1
        established 220 wall faces from loop size alone. A loop needs
        structural evidence - a column family, block lineage, hatch, grid
        or wall connectivity - and without it stays
        COLUMN_CANDIDATE_UNRESOLVED and bounds nothing

    §5  COLLINEARITY IS NOT MATERIAL. Lying on the same infinite line as a
        wall is COLLINEAR_GEOMETRIC_CONTINUATION. Becoming wall needs the
        BAND to continue too, and a LEVEL, dimension, fixture or casework
        interval never inherits a wall role by lying in line with one

    §6  DOUBLE LINEWORK IS NOT NECESSARILY A WALL. A paired band that
        joins the wall network at neither end may be a wall, a counter, a
        bar, casework, a low partition or glazing. CAD cannot tell those
        apart, so it says AMBIGUOUS_PAIRED_BAND and the question goes to
        the visual challenger rather than to a threshold

    §2  and none of it is ever written back onto the parent entity
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from engine import atomic_interval as ai
from engine import cad_geometry as cg

MODEL = "A_ROLE_BELONGS_TO_AN_INTERVAL_NOT_AN_ENTITY_V1"

# --- interval roles ------------------------------------------------------
MATERIAL_WALL_FACE = "MATERIAL_WALL_FACE"
GLAZING = "GLAZING"
COLUMN = "COLUMN"
COLUMN_CANDIDATE_UNRESOLVED = "COLUMN_CANDIDATE_UNRESOLVED"
AMBIGUOUS_PAIRED_BAND = "AMBIGUOUS_PAIRED_BAND"
CASEWORK = "CASEWORK"
CABINET_FRONT = "CABINET_FRONT"
COUNTER_EDGE = "COUNTER_EDGE"
FIXTURE = "FIXTURE"
FURNITURE = "FURNITURE"
STAIR_GEOMETRY = "STAIR_GEOMETRY"
POOL_CONTOUR = "POOL_CONTOUR"
POOL_INTERNAL_GEOMETRY = "POOL_INTERNAL_GEOMETRY"
DIMENSION_LINE = "DIMENSION_LINE"
DIMENSION_WITNESS = "DIMENSION_WITNESS"
CONSTRUCTION_LINE = "CONSTRUCTION_LINE"
DOOR = "DOOR"
ANNOTATION = "ANNOTATION"
LEVEL_OR_GRID_ANNOTATION = "LEVEL_OR_GRID_ANNOTATION"
UNKNOWN = "UNKNOWN"

ROLES = (MATERIAL_WALL_FACE, GLAZING, COLUMN, COLUMN_CANDIDATE_UNRESOLVED,
         AMBIGUOUS_PAIRED_BAND, CASEWORK, CABINET_FRONT, COUNTER_EDGE,
         FIXTURE, FURNITURE, STAIR_GEOMETRY, POOL_CONTOUR,
         POOL_INTERNAL_GEOMETRY, DIMENSION_LINE, DIMENSION_WITNESS,
         CONSTRUCTION_LINE, DOOR, ANNOTATION, LEVEL_OR_GRID_ANNOTATION,
         UNKNOWN)

MAY_BOUND_MATERIAL = (MATERIAL_WALL_FACE, GLAZING, COLUMN, POOL_CONTOUR)

# Roles that can never take part in the parallel reasoning, because what
# they ARE does not depend on what runs beside them.
NOT_MATERIAL_CANDIDATE = (DIMENSION_LINE, DIMENSION_WITNESS, ANNOTATION,
                          LEVEL_OR_GRID_ANNOTATION, DOOR, CONSTRUCTION_LINE,
                          POOL_INTERNAL_GEOMETRY, STAIR_GEOMETRY)

# --- how a paired band may read (§6) ------------------------------------
BAND_WALL = "WALL"
BAND_COUNTER = "COUNTER"
BAND_BAR = "BAR"
BAND_CASEWORK = "CASEWORK"
BAND_LOW_PARTITION = "LOW_PARTITION"
BAND_GLAZING = "GLAZING"
BAND_OTHER_BUILT = "OTHER_BUILT_FEATURE"
BAND_UNRESOLVED = "UNRESOLVED"
PAIRED_BAND_READINGS = (BAND_WALL, BAND_COUNTER, BAND_BAR, BAND_CASEWORK,
                        BAND_LOW_PARTITION, BAND_GLAZING, BAND_OTHER_BUILT,
                        BAND_UNRESOLVED)

DOUBLE_LINEWORK_IS_NOT_NECESSARILY_A_WALL = (
    "two parallel lines a wall's thickness apart may be a wall, a counter, "
    "a bar, a run of casework, a low partition or glazing. In plan they "
    "are the same drawing. Closure is not evidence and neither is the area "
    "it would produce, so where CAD cannot separate them this says so and "
    "the question goes to a pass that can look")

# --- evidence ------------------------------------------------------------
EV_PAIRED_WALL_FACE = "PAIRED_WALL_FACE_EVIDENCE"
EV_SUPPORT_UNION = "SUPPORTED_BY_A_UNION_OF_PARTNER_FRAGMENTS"
EV_UNSUPPORTED_REMAINDER = "NO_PARALLEL_PARTNER_RUNS_ALONG_THIS_STRETCH"
EV_NOTHING_BETWEEN = "NOTHING_DRAWN_BETWEEN_THE_TWO_FACES"
EV_BAND_JOINS_NETWORK = "THE_BAND_JOINS_THE_WALL_NETWORK"
EV_BAND_JOINS_NOTHING = "THE_BAND_JOINS_THE_WALL_NETWORK_AT_NEITHER_END"
EV_JUNCTION_BOTH_ENDS = "BOTH_ENDS_TERMINATE_AT_A_JUNCTION"
EV_JUNCTION_ONE_END = "ONE_END_TERMINATES_AT_A_JUNCTION"
EV_FREE_ENDS = "NEITHER_END_TERMINATES_AT_A_JUNCTION"
EV_COLLINEAR_GEOMETRIC = "COLLINEAR_GEOMETRIC_CONTINUATION"
EV_MATERIAL_CONTINUATION = "MATERIAL_WALL_CONTINUATION_ESTABLISHED"
EV_CASEWORK_DEPTH = "STANDS_OFF_AN_ESTABLISHED_WALL_FACE_AT_FITTED_UNIT_DEPTH"
EV_SHORT_RETURN = "SHORT_ORTHOGONAL_RETURN_BACK_TO_THAT_WALL"
EV_SPANS_WALL_TO_CASEWORK = "RUNS_FROM_A_WALL_FACE_TO_A_CASEWORK_FACE"
EV_DETAIL_FAMILY = "ONE_OF_A_CLOSE_PARALLEL_FAMILY_TOO_FINE_FOR_A_WALL"
EV_COINCIDENT_DUPLICATE = "DUPLICATED_COINCIDENT_LINEWORK"
EV_TOO_SHORT = "SHORTER_THAN_AN_ISOLATED_WALL_FACE_CAN_BE"
EV_DIMENSION_LAYER = "ITS_LAYER_DEFAULT_IS_DIMENSION_BEARING"
EV_ANNOTATION_LAYER = "ITS_LAYER_DEFAULT_IS_ANNOTATION"
EV_LEVEL_LAYER = "ITS_LAYER_CARRIES_LEVELS_OR_GRID_MARKS"
EV_DOOR_LAYER = "ITS_LAYER_DEFAULT_IS_DOOR_GEOMETRY"
EV_CURVE_SEMANTIC = "CLASSIFIED_BY_CURVE_SEMANTICS"
EV_STAIR_ASSEMBLY = "A_TREAD_OR_STRINGER_OF_A_DETECTED_STAIR_ASSEMBLY"

# --- column evidence (§4) ------------------------------------------------
EV_COL_LOOP = "A_SMALL_CLOSED_LOOP"
EV_COL_FAMILY = "ONE_OF_A_REPEATED_FAMILY_OF_LOOPS_OF_THE_SAME_SIZE"
EV_COL_LAYER_IS_STRUCTURAL = "ITS_LAYER_HOLDS_ALMOST_NOTHING_BUT_SUCH_LOOPS"
EV_COL_BLOCK_LINEAGE = "PLACED_BY_A_BLOCK_USED_REPEATEDLY_FOR_THIS_SHAPE"
EV_COL_HATCH = "A_HATCH_OR_FILL_LIES_INSIDE_THE_LOOP"
EV_COL_GRID = "ITS_CENTRES_LINE_UP_WITH_OTHER_LOOPS_ON_A_GRID"
EV_COL_WALL_CONNECTIVITY = "THE_LOOP_MEETS_ESTABLISHED_WALL_FACES"
COLUMN_EVIDENCE = (EV_COL_LOOP, EV_COL_FAMILY, EV_COL_LAYER_IS_STRUCTURAL,
                   EV_COL_BLOCK_LINEAGE, EV_COL_HATCH, EV_COL_GRID,
                   EV_COL_WALL_CONNECTIVITY)
# The loop itself is never evidence of structure; it is what raises the
# question. At least this many OTHER kinds must agree before a loop is a
# column that may bound a space.
COLUMN_EVIDENCE_REQUIRED = 2
# Repetition says "these are the same object". It does not say the object
# is structural: a row of identical wardrobes repeats and lines up too. So
# at least one evidence must be structural in KIND.
STRUCTURAL_IN_KIND = ("ITS_LAYER_HOLDS_ALMOST_NOTHING_BUT_SUCH_LOOPS",
                      "PLACED_BY_A_BLOCK_USED_REPEATEDLY_FOR_THIS_SHAPE",
                      "A_HATCH_OR_FILL_LIES_INSIDE_THE_LOOP",
                      "THE_LOOP_MEETS_ESTABLISHED_WALL_FACES")

A_SMALL_LOOP_IS_A_QUESTION = (
    "a small closed loop is a COLUMN_CANDIDATE. Furniture, a fixture, a "
    "planter, a duct and a pier all draw one. Size is the question, not "
    "the answer, and a candidate with no structural evidence stays "
    "COLUMN_CANDIDATE_UNRESOLVED and bounds nothing")

COLLINEARITY_IS_NOT_MATERIAL = (
    "lying on the same infinite line as a wall face is a geometric fact "
    "about coordinates. It says nothing about what was built along this "
    "stretch, and a LEVEL mark, a dimension, a fixture or a cabinet front "
    "never becomes a wall by being in line with one")

# --- GENERAL construction dimensions (unchanged from E1.1) --------------
WALL_SEPARATION_MIN_MM = 75.0
WALL_SEPARATION_MAX_MM = 400.0
AMBIGUOUS_SEPARATION_MAX_MM = 450.0
CASEWORK_DEPTH_MIN_MM = 450.0
CASEWORK_DEPTH_MAX_MM = 800.0
MIN_PAIR_OVERLAP_MM = 300.0
OFFSET_BUCKET_MM = 10.0
COINCIDENT_MM = 2.0
PARALLEL_DEG = 3.0
ANGLE_BINS = int(round(180.0 / PARALLEL_DEG))
JUNCTION_TURN_DEG = 20.0
JUNCTION_TOL_MM = 30.0
MIN_ISOLATED_WALL_FACE_MM = 300.0
# Two wall BANDS meeting at a corner do not meet at a point: the inner
# face stops one wall thickness short of where the outer face turns. So
# band connectivity is judged at wall-thickness range, not at the 30 mm
# used for a line-to-line junction. At 30 mm the site's own boundary wall
# was disconnected from its own corners.
BAND_JUNCTION_TOL_MM = WALL_SEPARATION_MAX_MM

# A WALL FACE RUNS TO THE CORNER IT MEETS. Its partner turns the corner
# one wall thickness earlier, so the last stretch of a face is routinely
# unsupported - and it is the same wall. A supported run may therefore
# reach its entity's own end when the tail left over is no longer than one
# wall thickness. That is bounded by construction and cannot become the
# whole-entity promotion E1.1 was corrected for.
CORNER_REACH_MM = WALL_SEPARATION_MAX_MM
EV_RUN_REACHES_ITS_OWN_END = "THE_SUPPORTED_RUN_REACHES_THIS_FACES_OWN_END"
DETAIL_FAMILY_MIN_MEMBERS = 3
DETAIL_FAMILY_LENGTH_RATIO = 0.5
COLUMN_MIN_AREA_M2 = 0.04
COLUMN_MAX_AREA_M2 = 4.0
COLUMN_MIN_SIDE_MM = 150.0
COLUMN_MAX_SIDE_MM = 2500.0
COLUMN_MAX_ASPECT = 4.0
COLUMN_FAMILY_MIN = 3
COLUMN_FAMILY_SIZE_TOL = 0.20
COLUMN_LAYER_SHARE = 0.60
GRID_TOL_MM = 50.0

HIGH, MEDIUM, LOW, NOT_ESTABLISHED = "HIGH", "MEDIUM", "LOW", "NOT_ESTABLISHED"

SCOPE = ("GENERAL construction geometry. No project dimension, room name, "
         "region id, layer name or coordinate appears in this module")


def model_hash() -> str:
    parts = ([MODEL] + list(ROLES) + list(PAIRED_BAND_READINGS)
             + list(COLUMN_EVIDENCE)
             + [f"{WALL_SEPARATION_MIN_MM}", f"{WALL_SEPARATION_MAX_MM}",
                f"{CASEWORK_DEPTH_MIN_MM}", f"{CASEWORK_DEPTH_MAX_MM}",
                f"{COLUMN_EVIDENCE_REQUIRED}"])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------------- geometry

def _dir(p):
    dx, dy = p.x2 - p.x1, p.y2 - p.y1
    n = math.hypot(dx, dy)
    return None if n <= 0 else (dx / n, dy / n)


def _bin(u):
    return int(round((math.degrees(math.atan2(u[1], u[0])) % 180.0)
                     / PARALLEL_DEG)) % ANGLE_BINS


def _dist_point_seg(pt, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    n2 = dx * dx + dy * dy
    if n2 <= 0:
        return math.hypot(pt[0] - a[0], pt[1] - a[1])
    t = max(0.0, min(1.0, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / n2))
    return math.hypot(a[0] + t * dx - pt[0], a[1] + t * dy - pt[1])


def _t_of_point(p, pt) -> float:
    dx, dy = p.x2 - p.x1, p.y2 - p.y1
    n2 = dx * dx + dy * dy
    if n2 <= 0:
        return 0.0
    return max(0.0, min(1.0,
                        ((pt[0] - p.x1) * dx + (pt[1] - p.y1) * dy) / n2))


# --------------------------------------------------------- the pass body

@dataclass
class Support:
    """A stretch of one entity that a parallel partner runs along."""
    lo: float                      # in the target's t parameter
    hi: float
    offset_mm: float
    partners: tuple = ()           # dicts: object_id, t_start, t_end, handle
    nothing_between: bool = True
    reached: tuple = ()


def _partners_by_offset(p, meta, bins, roles_of, prims_by_id):
    """Every parallel partner, grouped by offset, in P'S OWN PARAMETER.

    The union of the fragments at one offset is what supports P, so a
    counter-face broken by three openings supports P exactly where its
    pieces run and nowhere else.
    """
    u, span, b, L = meta[p.object_id]
    nx, ny = -u[1], u[0]
    off = p.x1 * nx + p.y1 * ny
    groups = {}
    for bb in ((b - 1) % ANGLE_BINS, b, (b + 1) % ANGLE_BINS):
        for q in bins.get(bb, ()):
            if q.object_id == p.object_id:
                continue
            if roles_of.get(q.object_id) in NOT_MATERIAL_CANDIDATE:
                continue
            d1 = abs(off - (q.x1 * nx + q.y1 * ny))
            d2 = abs(off - (q.x2 * nx + q.y2 * ny))
            if abs(d1 - d2) > JUNCTION_TOL_MM:
                continue
            d = (d1 + d2) / 2.0
            if d < COINCIDENT_MM or d > CASEWORK_DEPTH_MAX_MM:
                continue
            t1 = _t_of_point(p, (q.x1, q.y1))
            t2 = _t_of_point(p, (q.x2, q.y2))
            lo, hi = min(t1, t2), max(t1, t2)
            # only the part of q that actually lies beside p
            qa = q.x1 * u[0] + q.y1 * u[1]
            qb = q.x2 * u[0] + q.y2 * u[1]
            if max(qa, qb) <= span[0] or min(qa, qb) >= span[1]:
                continue
            if (hi - lo) * L < 1.0:
                continue
            key = round(d / OFFSET_BUCKET_MM)
            g = groups.setdefault(key, {"offset": d, "ranges": [],
                                        "partners": []})
            g["offset"] = min(g["offset"], d)
            g["ranges"].append((lo, hi))
            g["partners"].append({
                "object_id": q.object_id,
                "dwg_handle": q.provenance.handle,
                "layer": q.provenance.layer,
                "offset_mm": round(d, 3),
                "supports_t_start": round(lo, 9),
                "supports_t_end": round(hi, 9),
                "supports_mm": round((hi - lo) * L, 3)})
    return groups


def _supports(p, groups, *, lo_mm, hi_mm, L) -> list:
    """Union the fragments in each offset bucket inside a separation band."""
    out = []
    for g in groups.values():
        d = g["offset"]
        if not (lo_mm <= d <= hi_mm):
            continue
        runs = ai.union(g["ranges"])
        # THE MINIMUM IS ON THE UNION, NOT ON EACH PIECE. Whether a band
        # exists at this offset at all is asked once, of everything the
        # partner fragments cover together; where the band exists, every
        # stretch it covers is supported, however the openings broke it.
        if ai.total(runs) * L < MIN_PAIR_OVERLAP_MM:
            continue
        for (a, b) in runs:
            reached = []
            if a * L <= CORNER_REACH_MM and a > 0:
                a, _ = 0.0, reached.append(EV_RUN_REACHES_ITS_OWN_END)
            if (1.0 - b) * L <= CORNER_REACH_MM and b < 1.0:
                b, _ = 1.0, reached.append(EV_RUN_REACHES_ITS_OWN_END)
            # nothing drawn between the two faces over THIS stretch
            margin = WALL_SEPARATION_MIN_MM * 0.2
            blocked = False
            for h in groups.values():
                dd = h["offset"]
                if not (margin < dd < d - margin):
                    continue
                if ai.total(ai.intersect(ai.union(h["ranges"]), a, b)) \
                        >= 0.5 * (b - a):
                    blocked = True
                    break
            # EVERY fragment that established the band at this offset is
            # kept, each marked with whether it covers THIS stretch. The
            # decision was made from the union, so the union is the
            # provenance - E1.1 recorded one partner and lost the rest.
            parts = []
            for x in g["partners"]:
                row = dict(x)
                row["overlaps_this_run"] = bool(
                    x["supports_t_end"] > a and x["supports_t_start"] < b)
                parts.append(row)
            parts.sort(key=lambda r: (not r["overlaps_this_run"],
                                      r["supports_t_start"]))
            out.append(Support(lo=a, hi=b, offset_mm=d,
                               partners=tuple(parts),
                               nothing_between=not blocked,
                               reached=tuple(sorted(set(reached)))))
    return out


def establish(primitives, *, layer_defaults=None, dimension_layers=(),
              annotation_layers=(), level_layers=(), door_layers=(),
              glazing_layers=(), stair_object_ids=(), curve_roles=None,
              hatch_primitives=()) -> dict:
    """An atomic-interval role register for every drawn entity."""
    layer_defaults = dict(layer_defaults or {})
    curve_roles = dict(curve_roles or {})
    stair_ids = set(stair_object_ids or ())

    prims = [p for p in primitives if p.kind in ("SEGMENT", "ARC", "CIRCLE")]
    by_id = {p.object_id: p for p in prims}

    # --- phase 0: what an entity is FOR, whole-entity and exclusionary ---
    #
    # These are the only whole-entity decisions in E1.2, and every one of
    # them REMOVES a candidate rather than promoting one. A dimension is a
    # dimension along its whole length; nothing here can make a wall.
    whole = {}
    for p in prims:
        lay = p.provenance.layer
        default = layer_defaults.get(lay, cg.ROLE_UNRESOLVED)
        if p.object_id in stair_ids:
            whole[p.object_id] = (STAIR_GEOMETRY, EV_STAIR_ASSEMBLY)
        elif lay in dimension_layers or default == cg.DIMENSION_WITNESS:
            whole[p.object_id] = (
                (DIMENSION_WITNESS if p.length_mm < 1000.0
                 else DIMENSION_LINE), EV_DIMENSION_LAYER)
        elif lay in level_layers:
            whole[p.object_id] = (LEVEL_OR_GRID_ANNOTATION, EV_LEVEL_LAYER)
        elif lay in annotation_layers or default == cg.ANNOTATION_ONLY:
            whole[p.object_id] = (ANNOTATION, EV_ANNOTATION_LAYER)
        elif lay in door_layers:
            whole[p.object_id] = (DOOR, EV_DOOR_LAYER)
        elif lay in glazing_layers:
            whole[p.object_id] = (GLAZING, "ITS_LAYER_DEFAULT_IS_GLAZING")
        elif p.object_id in curve_roles:
            whole[p.object_id] = (curve_roles[p.object_id]["entity_role"],
                                  EV_CURVE_SEMANTIC)
    roles_of = {k: v[0] for k, v in whole.items()}

    # --- index the straight geometry --------------------------------
    segs = [p for p in prims if p.kind == "SEGMENT" and p.length_mm > 0]
    meta, bins = {}, {}
    for p in segs:
        u = _dir(p)
        if u is None:
            continue
        t1 = p.x1 * u[0] + p.y1 * u[1]
        t2 = p.x2 * u[0] + p.y2 * u[1]
        b = _bin(u)
        meta[p.object_id] = (u, (min(t1, t2), max(t1, t2)), b, p.length_mm)
        bins.setdefault(b, []).append(p)

    # --- phase 1: interval-local support -----------------------------
    wall_support, case_support, groups_of = {}, {}, {}
    for p in segs:
        if roles_of.get(p.object_id) in NOT_MATERIAL_CANDIDATE:
            continue
        g = _partners_by_offset(p, meta, bins, roles_of, by_id)
        groups_of[p.object_id] = g
        L = p.length_mm
        wall_support[p.object_id] = [
            s for s in _supports(p, g, lo_mm=WALL_SEPARATION_MIN_MM,
                                 hi_mm=WALL_SEPARATION_MAX_MM, L=L)
            if s.nothing_between]
        case_support[p.object_id] = _supports(
            p, g, lo_mm=CASEWORK_DEPTH_MIN_MM, hi_mm=CASEWORK_DEPTH_MAX_MM,
            L=L)

    # --- cut points ---------------------------------------------------
    endpoints = {}
    for p in segs:
        endpoints.setdefault(_key(p.x1, p.y1), []).append(p.object_id)
        endpoints.setdefault(_key(p.x2, p.y2), []).append(p.object_id)

    cuts = {p.object_id: [] for p in prims}
    for p in segs:
        oid = p.object_id
        for s in wall_support.get(oid, ()):
            cuts[oid].append((s.lo, ai.CUT_PARTNER_START))
            cuts[oid].append((s.hi, ai.CUT_PARTNER_END))
        for s in case_support.get(oid, ()):
            cuts[oid].append((s.lo, ai.CUT_PARTNER_START))
            cuts[oid].append((s.hi, ai.CUT_PARTNER_END))
        # somebody else's end landing on this line, or crossing it
        for q in _near(p, segs, meta, bins):
            for pt in ((q.x1, q.y1), (q.x2, q.y2)):
                if _dist_point_seg(pt, (p.x1, p.y1), (p.x2, p.y2)) \
                        <= JUNCTION_TOL_MM:
                    cuts[oid].append((_t_of_point(p, pt),
                                      ai.CUT_INTERSECTION))
    return _build(prims, segs, cuts, wall_support, case_support, groups_of,
                  whole, meta, endpoints, by_id, layer_defaults,
                  hatch_primitives, curve_roles)


def _key(x, y, snap=1.0):
    return (round(x / snap), round(y / snap))


def _near(p, segs, meta, bins):
    """Segments whose bounding box is near p's. Keeps the cut scan local."""
    x0, x1 = min(p.x1, p.x2) - JUNCTION_TOL_MM, max(p.x1, p.x2) + JUNCTION_TOL_MM
    y0, y1 = min(p.y1, p.y2) - JUNCTION_TOL_MM, max(p.y1, p.y2) + JUNCTION_TOL_MM
    out = []
    for q in segs:
        if q.object_id == p.object_id:
            continue
        if max(q.x1, q.x2) < x0 or min(q.x1, q.x2) > x1:
            continue
        if max(q.y1, q.y2) < y0 or min(q.y1, q.y2) > y1:
            continue
        out.append(q)
    return out


def _build(prims, segs, cuts, wall_support, case_support, groups_of, whole,
           meta, endpoints, by_id, layer_defaults, hatch_primitives,
           curve_roles):
    """Cut every entity, then decide a role for every interval."""
    intervals = {}
    for p in prims:
        rows = ai.cut(p, cuts.get(p.object_id, []), prefix="E1_2")
        for iv in rows:
            iv.role = UNKNOWN
            iv.confidence = NOT_ESTABLISHED
        intervals[p.object_id] = rows

    # --- phase 0 applied to every interval of an excluded entity -------
    WHY0 = {
        DIMENSION_LINE: "dimension geometry describes the building; it is "
                        "not the building",
        DIMENSION_WITNESS: "an extension line of a dimension",
        LEVEL_OR_GRID_ANNOTATION: "a level mark or grid line. It records a "
                                  "height or a setting-out reference and "
                                  "nothing was built along it",
        ANNOTATION: "annotation is writing about the drawing",
        DOOR: "a door leaf or swing. It stands IN an opening and is not "
              "the wall beside it",
        GLAZING: "glazing is built material and may bound a space",
        STAIR_GEOMETRY: "a tread or stringer of a detected stair assembly",
    }
    for oid, (role, ev) in whole.items():
        for iv in intervals.get(oid, ()):
            iv.role = role
            iv.confidence = MEDIUM
            iv.evidence = (ev,)
            iv.why = WHY0.get(role, curve_roles.get(oid, {}).get("why", ""))
            iv.may_bound_material = role in MAY_BOUND_MATERIAL

    # --- phase 1: paired-band support, interval by interval ------------
    band_of = {}
    for p in segs:
        oid = p.object_id
        if oid in whole:
            continue
        L = p.length_mm
        sup = wall_support.get(oid, [])
        for iv in intervals[oid]:
            mid = (iv.t_start + iv.t_end) / 2.0
            hit = next((s for s in sup if s.lo - 1e-9 <= mid <= s.hi + 1e-9),
                       None)
            if hit is None:
                iv.evidence = (EV_UNSUPPORTED_REMAINDER,)
                iv.why = ("no parallel partner runs along this stretch, so "
                          "nothing here says a wall was built")
                continue
            iv.evidence = (EV_PAIRED_WALL_FACE, EV_NOTHING_BETWEEN)
            if len(hit.partners) > 1:
                iv.evidence += (EV_SUPPORT_UNION,)
            elif sum(1 for x in hit.partners
                     if x.get("overlaps_this_run")) > 1:
                iv.evidence += (EV_SUPPORT_UNION,)
            iv.evidence += tuple(hit.reached)
            iv.supporting_partner_intervals = hit.partners
            iv.role = "_BAND"
            band_of[iv.interval_id] = frozenset(
                {oid} | {x["object_id"] for x in hit.partners})
            iv.provenance["band_offset_mm"] = round(hit.offset_mm, 3)
            if iv.length_mm < MIN_ISOLATED_WALL_FACE_MM:
                iv.evidence += (EV_TOO_SHORT,)

    # --- phase 2: does the band join the wall network? -----------------
    #
    # CONNECTIVITY IS A PROPERTY OF THE BAND, NOT OF A CUT. An entity is
    # cut wherever the evidence changes, so an interval's end is usually
    # in the middle of a wall. The question "does this join anything?" is
    # therefore asked at the ends of the SUPPORTED RUN - the contiguous
    # stretch a counter-face runs along - and the answer is carried to
    # every interval inside it.
    runs = []
    for p in segs:
        oid = p.object_id
        if oid in whole:
            continue
        sup = wall_support.get(oid, [])
        if not sup:
            continue
        band = frozenset({oid} | {x["object_id"] for s in sup
                                  for x in s.partners})
        for (lo, hi) in ai.union([(s.lo, s.hi) for s in sup]):
            runs.append({"oid": oid, "lo": lo, "hi": hi, "band": band,
                         "a": ai.point_at(p, lo), "b": ai.point_at(p, hi),
                         "offset": min(s.offset_mm for s in sup)})
    for r in runs:
        met = []
        for end in (r["a"], r["b"]):
            hit = False
            for o in runs:
                # THE SAME BAND means the two faces of ONE wall - each is
                # the other's partner. Excluding every run that merely
                # shares a partner somewhere cut the site's own boundary
                # wall off from its corners.
                if o is r or o["oid"] == r["oid"]:
                    continue
                if o["oid"] in r["band"] and r["oid"] in o["band"]:
                    continue
                if _dist_point_seg(end, o["a"], o["b"]) \
                        > BAND_JUNCTION_TOL_MM:
                    continue
                if _turn_pts(r["a"], r["b"], o["a"], o["b"]) \
                        < JUNCTION_TURN_DEG:
                    continue
                hit = True
                break
            met.append(hit)
        r["joins"] = met

    for r in runs:
        joins = r["joins"]
        for iv in intervals[r["oid"]]:
            if iv.role != "_BAND":
                continue
            mid = (iv.t_start + iv.t_end) / 2.0
            if not (r["lo"] - 1e-9 <= mid <= r["hi"] + 1e-9):
                continue
            if not any(joins):
                iv.role = AMBIGUOUS_PAIRED_BAND
                iv.confidence = NOT_ESTABLISHED
                iv.evidence += (EV_BAND_JOINS_NOTHING, EV_FREE_ENDS)
                iv.conflicting_evidence = tuple(PAIRED_BAND_READINGS)
                iv.may_bound_material = False
                iv.why = DOUBLE_LINEWORK_IS_NOT_NECESSARILY_A_WALL
                continue
            iv.role = MATERIAL_WALL_FACE
            iv.evidence += (EV_BAND_JOINS_NETWORK,
                            EV_JUNCTION_BOTH_ENDS if all(joins)
                            else EV_JUNCTION_ONE_END)
            iv.confidence = HIGH if all(joins) else MEDIUM
            if EV_TOO_SHORT in iv.evidence and not all(joins) \
                    and (r["hi"] - r["lo"]) * p_length(intervals, r) \
                    < MIN_ISOLATED_WALL_FACE_MM:
                iv.role = UNKNOWN
                iv.confidence = LOW
                iv.may_bound_material = False
                iv.why = ("paired but shorter than an isolated wall face "
                          "can be, and joined at only one end")
                continue
            iv.may_bound_material = True
            iv.why = (f"a counter-face runs along this stretch "
                      f"{iv.provenance.get('band_offset_mm')} mm away with "
                      "nothing drawn between them, and the band joins the "
                      "wall network")

    # --- phase 3: detail families, on unsupported stretches only -------
    _detail_families(segs, intervals, whole, meta, groups_of)

    # --- phase 4: columns ----------------------------------------------
    columns = _columns(segs, intervals, whole, hatch_primitives, by_id)

    # --- phase 5: casework standing off an ESTABLISHED wall interval ----
    _casework(segs, intervals, whole, case_support, by_id)

    # --- phase 6: collinear continuation, material only if the band
    #              continues too --------------------------------------
    _collinear(segs, intervals, whole, meta, groups_of, by_id)

    for rows in intervals.values():
        for iv in rows:
            if iv.role == "_BAND":
                iv.role = UNKNOWN
                iv.may_bound_material = False
            iv.may_bound_material = (iv.role in MAY_BOUND_MATERIAL
                                     and iv.confidence in (HIGH, MEDIUM))
            if iv.role == UNKNOWN and not iv.why:
                iv.why = ("nothing established what was built along this "
                          "stretch, and UNKNOWN never bounds material")

    flat = [iv for rows in intervals.values() for iv in rows]
    counts = {}
    for iv in flat:
        counts[iv.role] = counts.get(iv.role, 0) + 1
    per_entity = {}
    for oid, rows in intervals.items():
        per_entity[oid] = sorted({iv.role for iv in rows})
    mixed = {k: v for k, v in per_entity.items() if len(v) > 1}
    return {
        "intervals": intervals,
        "flat": flat,
        "columns": columns,
        "counts_by_role": counts,
        "interval_count": len(flat),
        "entity_count": len(prims),
        "entities_with_more_than_one_role": len(mixed),
        "entities_with_more_than_one_role_rows": mixed,
        "intervals_that_may_bound_material":
            sum(1 for iv in flat if iv.may_bound_material),
        "material_length_mm": round(sum(iv.length_mm for iv in flat
                                        if iv.may_bound_material), 3),
    }


def _turn(a, b) -> float:
    return _turn_pts(a.start_mm, a.end_mm, b.start_mm, b.end_mm)


def _turn_pts(a0, a1, b0, b1) -> float:
    ua = math.atan2(a1[1] - a0[1], a1[0] - a0[0])
    ub = math.atan2(b1[1] - b0[1], b1[0] - b0[0])
    d = abs(math.degrees(ua - ub)) % 180.0
    return min(d, 180.0 - d)


def p_length(intervals, run) -> float:
    rows = intervals.get(run["oid"], ())
    return sum(iv.length_mm for iv in rows) or 1.0


def _detail_families(segs, intervals, whole, meta, groups_of):
    """Strokes of comparable length, finer apart than a wall is thick."""
    for p in segs:
        oid = p.object_id
        if oid in whole:
            continue
        fine = []
        for g in groups_of.get(oid, {}).values():
            if g["offset"] >= WALL_SEPARATION_MIN_MM:
                continue
            for x in g["partners"]:
                ratio = x["supports_mm"] / max(p.length_mm, 1e-9)
                if ratio >= DETAIL_FAMILY_LENGTH_RATIO:
                    fine.append(x)
        if len(fine) < DETAIL_FAMILY_MIN_MEMBERS - 1:
            continue
        for iv in intervals[oid]:
            if iv.role not in (UNKNOWN,):
                continue
            iv.role = FIXTURE
            iv.confidence = MEDIUM
            iv.evidence = iv.evidence + (EV_DETAIL_FAMILY,)
            iv.supporting_partner_intervals = tuple(fine[:4])
            iv.why = (f"{len(fine) + 1} strokes of comparable length lie "
                      "closer together than any wall is thick. That is "
                      "hatch, a leaf or a tiled detail")


def _columns(segs, intervals, whole, hatch_primitives, by_id):
    """A small closed loop is a QUESTION. Structural evidence answers it."""
    try:
        from shapely.geometry import LineString, Point
        from shapely.ops import polygonize, unary_union
    except Exception:
        return {"loops": [], "note": "shapely unavailable"}
    short = [p for p in segs
             if p.length_mm <= COLUMN_MAX_SIDE_MM and p.object_id not in whole]
    if not short:
        return {"loops": []}
    lines = [LineString([(p.x1, p.y1), (p.x2, p.y2)]) for p in short]
    try:
        faces = list(polygonize(unary_union(lines)))
    except Exception:
        return {"loops": []}

    loops = []
    for f in faces:
        a = f.area / 1e6
        if not (COLUMN_MIN_AREA_M2 <= a <= COLUMN_MAX_AREA_M2):
            continue
        xs = [c[0] for c in f.exterior.coords]
        ys = [c[1] for c in f.exterior.coords]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if max(w, h) > COLUMN_MAX_SIDE_MM or min(w, h) < COLUMN_MIN_SIDE_MM:
            continue
        if max(w, h) / max(min(w, h), 1e-9) > COLUMN_MAX_ASPECT:
            continue
        members = []
        ring = list(f.exterior.coords)
        for u, v in zip(ring, ring[1:]):
            mid = ((u[0] + v[0]) / 2.0, (u[1] + v[1]) / 2.0)
            for i, q in enumerate(short):
                if _dist_point_seg(mid, (q.x1, q.y1), (q.x2, q.y2)) <= 2.0:
                    members.append(q)
                    break
        loops.append({"centre": (f.centroid.x, f.centroid.y),
                      "w": w, "h": h, "area_m2": a,
                      "members": members,
                      "layers": sorted({q.provenance.layer for q in members}),
                      "blocks": sorted({b for q in members
                                        for b in getattr(q.provenance,
                                                         "block_path", ())}),
                      "evidence": []})

    # --- the evidence a loop may earn ---------------------------------
    for L in loops:                                     # repeated family
        same = [M for M in loops
                if abs(M["w"] - L["w"]) <= COLUMN_FAMILY_SIZE_TOL * L["w"]
                and abs(M["h"] - L["h"]) <= COLUMN_FAMILY_SIZE_TOL * L["h"]]
        if len(same) >= COLUMN_FAMILY_MIN:
            L["evidence"].append(EV_COL_FAMILY)
            L["family_size"] = len(same)
    # A LAYER IS STRUCTURAL WHEN ALMOST EVERYTHING ON IT IS SUCH A LOOP.
    # Counting loop MEMBERSHIPS instead of distinct entities made the main
    # wall layer look structural, because one entity can sit on several
    # loops and the share went over one.
    layer_total, layer_ids = {}, {}
    for p in segs:
        layer_total[p.provenance.layer] = layer_total.get(
            p.provenance.layer, 0) + 1
    for L in loops:
        for q in L["members"]:
            layer_ids.setdefault(q.provenance.layer, set()).add(q.object_id)
    structural_layers = {lay for lay, ids in layer_ids.items()
                         if len(ids) / max(layer_total.get(lay, 1), 1)
                         >= COLUMN_LAYER_SHARE}
    block_counts = {}
    for L in loops:
        for b in L["blocks"]:
            block_counts[b] = block_counts.get(b, 0) + 1
    hatch_pts = [(getattr(h, "x1", 0.0), getattr(h, "y1", 0.0))
                 for h in hatch_primitives or ()]
    centres = [L["centre"] for L in loops]
    for L in loops:
        if any(lay in structural_layers for lay in L["layers"]):
            L["evidence"].append(EV_COL_LAYER_IS_STRUCTURAL)
        if any(block_counts.get(b, 0) >= COLUMN_FAMILY_MIN
               for b in L["blocks"]):
            L["evidence"].append(EV_COL_BLOCK_LINEAGE)
        cx, cy = L["centre"]
        if any(abs(px - cx) <= max(L["w"], L["h"]) and
               abs(py - cy) <= max(L["w"], L["h"]) for px, py in hatch_pts):
            L["evidence"].append(EV_COL_HATCH)
        # A GRID RELATIONSHIP IS BETWEEN LOOPS OF THE SAME FAMILY. Any
        # three small loops share an axis somewhere; three loops of the
        # same size on one axis are a structural line.
        aligned = sum(
            1 for M in loops
            if M is not L
            and abs(M["w"] - L["w"]) <= COLUMN_FAMILY_SIZE_TOL * L["w"]
            and abs(M["h"] - L["h"]) <= COLUMN_FAMILY_SIZE_TOL * L["h"]
            and (abs(M["centre"][0] - cx) <= GRID_TOL_MM
                 or abs(M["centre"][1] - cy) <= GRID_TOL_MM))
        if aligned >= 3:
            L["evidence"].append(EV_COL_GRID)
            L["grid_partners"] = aligned
        touches = False
        for q in L["members"]:
            for other in segs:
                if other.object_id == q.object_id:
                    continue
                if any(x.role == MATERIAL_WALL_FACE
                       for x in intervals.get(other.object_id, ())) and \
                        _dist_point_seg((q.x1, q.y1),
                                        (other.x1, other.y1),
                                        (other.x2, other.y2)) \
                        <= JUNCTION_TOL_MM:
                    touches = True
                    break
            if touches:
                break
        if touches:
            L["evidence"].append(EV_COL_WALL_CONNECTIVITY)

    rows = []
    for n, L in enumerate(loops, start=1):
        ev = sorted(set(L["evidence"]))
        structural = [x for x in ev if x in STRUCTURAL_IN_KIND]
        established = (len(ev) >= COLUMN_EVIDENCE_REQUIRED
                       and bool(structural))
        role = COLUMN if established else COLUMN_CANDIDATE_UNRESOLVED
        for q in L["members"]:
            for iv in intervals.get(q.object_id, ()):
                # A column is material, so naming one is not a promotion
                # over an ambiguous band - it is the specific answer the
                # band was waiting for. An interval already established as
                # a wall face is left alone.
                if iv.role not in (UNKNOWN, FIXTURE, AMBIGUOUS_PAIRED_BAND):
                    continue
                iv.role = role
                iv.confidence = MEDIUM if established else NOT_ESTABLISHED
                iv.evidence = iv.evidence + (EV_COL_LOOP,) + tuple(ev)
                iv.may_bound_material = established
                iv.why = (
                    "one side of a small closed loop with structural "
                    "evidence beside it, so it is a column and bounds the "
                    "space around it" if established else
                    A_SMALL_LOOP_IS_A_QUESTION)
                if not established:
                    iv.conflicting_evidence = (
                        "FURNITURE", "FIXTURE", "PLANTER", "DUCT",
                        "CASEWORK", "COLUMN")
        rows.append({
            "LOOP_ID": f"LOOP-{n:03d}",
            "centre_mm": [round(L["centre"][0], 2), round(L["centre"][1], 2)],
            "size_mm": [round(L["w"], 1), round(L["h"], 1)],
            "area_m2_rendering_only": round(L["area_m2"], 4),
            "layers": L["layers"],
            "blocks": L["blocks"],
            "member_object_ids": [q.object_id for q in L["members"]],
            "STRUCTURAL_EVIDENCE": ev,
            "evidence_that_is_structural_in_kind": structural,
            "evidence_count": len(ev),
            "evidence_required": COLUMN_EVIDENCE_REQUIRED,
            "at_least_one_must_be_structural_in_kind": True,
            "ROLE": role,
            "MAY_BOUND_MATERIAL": established,
            "a_small_loop_is_a_question": A_SMALL_LOOP_IS_A_QUESTION,
        })
    return {"loops": rows,
            "loops_seen": len(loops),
            "established_as_column": sum(1 for r in rows
                                         if r["ROLE"] == COLUMN),
            "unresolved": sum(1 for r in rows
                              if r["ROLE"] == COLUMN_CANDIDATE_UNRESOLVED),
            "structural_layers_found": sorted(structural_layers)}


def _casework(segs, intervals, whole, case_support, by_id):
    """A face standing off an ESTABLISHED wall interval at unit depth."""
    def wall_intervals(oid):
        return [iv for iv in intervals.get(oid, ())
                if iv.role == MATERIAL_WALL_FACE]

    fronts = []
    for p in segs:
        oid = p.object_id
        if oid in whole:
            continue
        for s in case_support.get(oid, ()):
            backing = [x for x in s.partners if wall_intervals(x["object_id"])]
            if not backing:
                continue
            for iv in intervals[oid]:
                mid = (iv.t_start + iv.t_end) / 2.0
                if not (s.lo - 1e-9 <= mid <= s.hi + 1e-9):
                    continue
                if iv.role not in (UNKNOWN, FIXTURE, AMBIGUOUS_PAIRED_BAND):
                    continue
                iv.role = CABINET_FRONT
                iv.confidence = MEDIUM
                iv.evidence = iv.evidence + (EV_CASEWORK_DEPTH,)
                iv.supporting_partner_intervals = tuple(backing)
                iv.may_bound_material = False
                iv.why = (f"this stretch runs parallel to an established "
                          f"wall face {s.offset_mm:.0f} mm away, which is "
                          "deeper than a wall and is fitted-unit depth. "
                          "Casework stands INSIDE one space; a wall "
                          "separates two")
                fronts.append((p, iv, backing))

    # returns: a short run from a wall face to a casework face
    for p in segs:
        oid = p.object_id
        if oid in whole:
            continue
        for iv in intervals[oid]:
            if iv.role != UNKNOWN or iv.length_mm > CASEWORK_DEPTH_MAX_MM * 1.2:
                continue
            hits_front = any(
                _dist_point_seg(end, f_iv.start_mm, f_iv.end_mm)
                <= JUNCTION_TOL_MM
                for _q, f_iv, _b in fronts
                for end in (iv.start_mm, iv.end_mm))
            if not hits_front:
                continue
            iv.role = COUNTER_EDGE
            iv.confidence = MEDIUM
            iv.evidence = iv.evidence + (EV_SPANS_WALL_TO_CASEWORK,
                                         EV_SHORT_RETURN)
            iv.may_bound_material = False
            iv.why = ("a short run landing on an established casework face, "
                      "so it is the end or return of the fitted unit")


def _collinear(segs, intervals, whole, meta, groups_of, by_id):
    """Collinear with a wall is geometry. Becoming wall needs the band.

    A stretch lying on the same infinite line as an established wall face
    is recorded as COLLINEAR_GEOMETRIC_CONTINUATION. It becomes
    MATERIAL_WALL_CONTINUATION_ESTABLISHED only when the WALL BAND
    continues over it as well - a counter-face at the same offset, on the
    same side - and never when the entity is annotation, a level mark, a
    dimension, a fixture or casework.
    """
    banned = (DIMENSION_LINE, DIMENSION_WITNESS, ANNOTATION,
              LEVEL_OR_GRID_ANNOTATION, DOOR, CONSTRUCTION_LINE, FIXTURE,
              FURNITURE, CASEWORK, CABINET_FRONT, COUNTER_EDGE,
              STAIR_GEOMETRY, POOL_INTERNAL_GEOMETRY)
    established = []
    for oid, rows in intervals.items():
        for iv in rows:
            if iv.role == MATERIAL_WALL_FACE and oid in meta:
                established.append((oid, iv))
    if not established:
        return
    for p in segs:
        oid = p.object_id
        if oid in whole or oid not in meta:
            continue
        u, span, b, L = meta[oid]
        nx, ny = -u[1], u[0]
        off = p.x1 * nx + p.y1 * ny
        for iv in intervals[oid]:
            if iv.role in banned or iv.role == MATERIAL_WALL_FACE:
                continue
            partner_oid = None
            for (qoid, q_iv) in established:
                if qoid == oid:
                    continue
                qu, qspan, qb, qL = meta[qoid]
                if abs(qu[0] * u[0] + qu[1] * u[1]) < math.cos(
                        math.radians(PARALLEL_DEG)):
                    continue
                d = abs(off - (q_iv.start_mm[0] * nx + q_iv.start_mm[1] * ny))
                if d > JUNCTION_TOL_MM:
                    continue
                gap = min(
                    _dist_point_seg(iv.start_mm, q_iv.start_mm, q_iv.end_mm),
                    _dist_point_seg(iv.end_mm, q_iv.start_mm, q_iv.end_mm))
                if gap > cg.MAX_DOUBLE_LEAF_MM:
                    continue
                partner_oid = (qoid, q_iv)
                break
            if partner_oid is None:
                continue
            qoid, q_iv = partner_oid
            band = q_iv.provenance.get("band_offset_mm")
            continues = False
            for g in groups_of.get(oid, {}).values():
                if band is None:
                    break
                if abs(g["offset"] - band) > OFFSET_BUCKET_MM:
                    continue
                if ai.total(ai.intersect(ai.union(g["ranges"]),
                                         iv.t_start, iv.t_end)) * L \
                        >= 0.5 * iv.length_mm:
                    continues = True
                    break
            iv.evidence = iv.evidence + (EV_COLLINEAR_GEOMETRIC,)
            if continues:
                iv.role = MATERIAL_WALL_FACE
                iv.confidence = MEDIUM
                iv.evidence = iv.evidence + (EV_MATERIAL_CONTINUATION,)
                iv.may_bound_material = True
                iv.why = ("collinear with an established wall face AND the "
                          "wall band continues over this stretch, so the "
                          "same wall continues past an opening")
            else:
                iv.conflicting_evidence = iv.conflicting_evidence + (
                    "THE_WALL_BAND_DOES_NOT_CONTINUE_OVER_THIS_STRETCH",)
                # The role is not touched, so neither is its account of
                # itself. An interval already established as something else
                # - a COLUMN carrying structural evidence, say - keeps the
                # reason it was established, and this pass only adds the
                # fact that it also happens to lie in line with a wall.
                if iv.role == UNKNOWN:
                    iv.why = COLLINEARITY_IS_NOT_MATERIAL


ESTABLISHING_EVIDENCE = (
    EV_PAIRED_WALL_FACE, EV_SUPPORT_UNION, EV_MATERIAL_CONTINUATION,
    EV_CASEWORK_DEPTH, EV_SPANS_WALL_TO_CASEWORK, EV_DETAIL_FAMILY,
    EV_CURVE_SEMANTIC, EV_STAIR_ASSEMBLY, EV_DOOR_LAYER,
    EV_DIMENSION_LAYER, EV_ANNOTATION_LAYER, EV_LEVEL_LAYER,
) + COLUMN_EVIDENCE

COLLINEARITY_IS_A_DIAGNOSTIC_TAG = (
    "COLLINEAR_GEOMETRIC_CONTINUATION records a fact about coordinates and "
    "is attached to every stretch that lies in line with an established "
    "wall face, whatever that stretch already is. It is diagnostic, not "
    "establishing: reading its presence as the reason a role exists calls a "
    "structurally established column - or anything else that happens to lie "
    "in line with a wall - a collinear guess"
)


def established_by_collinearity_alone(interval) -> bool:
    """§5: is collinear continuation the ONLY thing holding this role up?

    True only when the stretch lies in line with a wall face, the wall band
    does not continue over it, and nothing else established what was built
    there. An interval whose role came from a paired band, from casework
    depth, from curve semantics or from column evidence is not this case,
    even though the collinear tag also sits on it.
    """
    ev = tuple(interval.evidence or ())
    if EV_COLLINEAR_GEOMETRIC not in ev:
        return False
    if EV_MATERIAL_CONTINUATION in ev:
        return False
    return not any(e in ESTABLISHING_EVIDENCE for e in ev)


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "ROLES": list(ROLES),
        "MAY_BOUND_MATERIAL": list(MAY_BOUND_MATERIAL),
        "NOT_MATERIAL_CANDIDATE": list(NOT_MATERIAL_CANDIDATE),
        "PAIRED_BAND_READINGS": list(PAIRED_BAND_READINGS),
        "COLUMN_EVIDENCE": list(COLUMN_EVIDENCE),
        "COLUMN_EVIDENCE_REQUIRED": COLUMN_EVIDENCE_REQUIRED,
        "STRUCTURAL_IN_KIND": list(STRUCTURAL_IN_KIND),
        "WALL_SEPARATION_MIN_MM": WALL_SEPARATION_MIN_MM,
        "WALL_SEPARATION_MAX_MM": WALL_SEPARATION_MAX_MM,
        "CASEWORK_DEPTH_MIN_MM": CASEWORK_DEPTH_MIN_MM,
        "CASEWORK_DEPTH_MAX_MM": CASEWORK_DEPTH_MAX_MM,
        "MIN_PAIR_OVERLAP_MM": MIN_PAIR_OVERLAP_MM,
        "OFFSET_BUCKET_MM": OFFSET_BUCKET_MM,
        "MIN_ISOLATED_WALL_FACE_MM": MIN_ISOLATED_WALL_FACE_MM,
        "CORNER_REACH_MM": CORNER_REACH_MM,
        "JUNCTION_TOL_MM": JUNCTION_TOL_MM,
        "BAND_JUNCTION_TOL_MM": BAND_JUNCTION_TOL_MM,
        "JUNCTION_TURN_DEG": JUNCTION_TURN_DEG,
        "COLUMN_MIN_AREA_M2": COLUMN_MIN_AREA_M2,
        "COLUMN_MAX_AREA_M2": COLUMN_MAX_AREA_M2,
        "COLUMN_MIN_SIDE_MM": COLUMN_MIN_SIDE_MM,
        "COLUMN_MAX_SIDE_MM": COLUMN_MAX_SIDE_MM,
        "COLUMN_MAX_ASPECT": COLUMN_MAX_ASPECT,
        "COLUMN_FAMILY_MIN": COLUMN_FAMILY_MIN,
        "COLUMN_LAYER_SHARE": COLUMN_LAYER_SHARE,
        "GRID_TOL_MM": GRID_TOL_MM,
        "SCOPE": SCOPE,
        "why": {
            "a_small_loop_is_a_question": A_SMALL_LOOP_IS_A_QUESTION,
            "collinearity_is_not_material": COLLINEARITY_IS_NOT_MATERIAL,
            "double_linework_is_not_necessarily_a_wall":
                DOUBLE_LINEWORK_IS_NOT_NECESSARILY_A_WALL,
            "evidence_licenses_only_its_own_interval":
                ai.EVIDENCE_LICENSES_ONLY_ITS_OWN_INTERVAL,
            "whole_entity_promotion_is_banned":
                ai.WHOLE_ENTITY_PROMOTION_IS_BANNED,
        },
    }
