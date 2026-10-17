"""E1.1 — a layer does not establish what an entity IS.

E1 v1 read a layer profile, found that layers `1`, `5`, `W` and `2` hold
mostly paired faces, and then treated EVERY line on those layers as a
MATERIAL_WALL_FACE. Its own provenance register said, honestly:

    ENTITY_ESTABLISHED_ROLE = NOT_ESTABLISHED_PER_ENTITY

and it released boundaries built from those entities anyway. In this
drawing layer `5` carries the kitchen's wall AND the kitchen's cabinet
front; layer `W` carries 50 mm detail strokes. So the released Kitchen
ran along a cabinet front 500 mm inside the room, and the released Pantry
walked over counter geometry.

The correction is a hierarchy, not a threshold:

    LAYER_DEFAULT_ROLE      candidate-generation evidence ONLY
    ENTITY_ESTABLISHED_ROLE required before a segment may bound material

A layer being wall-heavy never establishes anything on its own, and
UNKNOWN never releases.

WHAT SEPARATES A WALL FROM A CABINET, generally:

    A WALL SEPARATES TWO SPACES. It is drawn as two faces with the wall
    body between them, and its ends land on other walls.

    CASEWORK STANDS INSIDE ONE SPACE. It is drawn as a single face
    standing off a wall at fitted-unit depth, with short returns back to
    that wall, and its ends stop in open room.

Both tests are ordinary construction geometry. Neither knows what a
kitchen is, neither names a room, and no coordinate of this project
appears anywhere in this module.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from engine import cad_geometry as cg

MODEL = "A_LAYER_DOES_NOT_ESTABLISH_AN_ENTITY_ROLE_V1"

# --- the sixteen entity roles -------------------------------------------
MATERIAL_WALL_FACE = "MATERIAL_WALL_FACE"
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
GLAZING = "GLAZING"
DOOR = "DOOR"
ANNOTATION = "ANNOTATION"
UNKNOWN = "UNKNOWN"

ENTITY_ROLES = (MATERIAL_WALL_FACE, CASEWORK, CABINET_FRONT, COUNTER_EDGE,
                FIXTURE, FURNITURE, STAIR_GEOMETRY, POOL_CONTOUR,
                POOL_INTERNAL_GEOMETRY, DIMENSION_LINE, DIMENSION_WITNESS,
                CONSTRUCTION_LINE, GLAZING, DOOR, ANNOTATION, UNKNOWN)

# The only established roles a released physical boundary may be built
# from. Everything else - casework, fixtures, furniture, pool internals,
# dimensions, construction lines, annotation and UNKNOWN - may be recorded
# where it lies and may never act as a room wall.
MAY_BOUND_MATERIAL = (MATERIAL_WALL_FACE, GLAZING, POOL_CONTOUR)

UNKNOWN_CANNOT_RELEASE_AS_MATERIAL_WALL = (
    "an entity whose role is not established is UNKNOWN, and UNKNOWN may "
    "not act as a room wall. A boundary built from it would be a wall "
    "nobody drew, dressed in a DWG handle")

A_LAYER_IS_CANDIDATE_GENERATION_ONLY = (
    "LAYER_DEFAULT_ROLE proposes which entities are WORTH TESTING. It "
    "never establishes what one of them is. A layer that is 70 percent "
    "wall-like is 30 percent something else, and in this drawing that "
    "something else was the kitchen cabinet run")

# --- confidence ---------------------------------------------------------
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"
NOT_ESTABLISHED = "NOT_ESTABLISHED"

# --- evidence -----------------------------------------------------------
EV_PAIRED_WALL_FACE = "PAIRED_COUNTER_FACE_AT_WALL_THICKNESS"
EV_NOTHING_BETWEEN = "NOTHING_DRAWN_BETWEEN_THE_TWO_FACES"
EV_WALL_JUNCTION_BOTH_ENDS = "BOTH_ENDS_TERMINATE_AT_A_JUNCTION"
EV_WALL_JUNCTION_ONE_END = "ONE_END_TERMINATES_AT_A_JUNCTION"
EV_FREE_ENDS = "NEITHER_END_TERMINATES_AT_A_JUNCTION"
EV_COLLINEAR_RUN = "CONTINUES_AN_ESTABLISHED_WALL_FACE_COLLINEARLY"
EV_CASEWORK_DEPTH = "STANDS_OFF_AN_ESTABLISHED_WALL_FACE_AT_FITTED_UNIT_DEPTH"
EV_SHORT_RETURN = "SHORT_ORTHOGONAL_RETURN_BACK_TO_THAT_WALL"
EV_SPANS_WALL_TO_CASEWORK = "RUNS_FROM_A_WALL_FACE_TO_A_CASEWORK_FACE"
EV_DETAIL_FAMILY = "ONE_OF_A_CLOSE_PARALLEL_FAMILY_TOO_FINE_FOR_A_WALL"
EV_TOO_SHORT = "SHORTER_THAN_AN_ISOLATED_WALL_FACE_CAN_BE"
EV_DIMENSION_LAYER = "ITS_LAYER_DEFAULT_IS_DIMENSION_BEARING"
EV_ANNOTATION_LAYER = "ITS_LAYER_DEFAULT_IS_ANNOTATION"
EV_DOOR_LAYER = "ITS_LAYER_DEFAULT_IS_DOOR_GEOMETRY"
EV_CURVE_SEMANTIC = "CLASSIFIED_BY_CURVE_SEMANTICS"
EV_STAIR_ASSEMBLY = "A_TREAD_OR_STRINGER_OF_A_DETECTED_STAIR_ASSEMBLY"
EV_BLOCK_LINEAGE = "PLACED_BY_A_BLOCK_WHOSE_LINEAGE_IS_NOT_WALL_LIKE"
EV_RASTER_SINGLE_STROKE = "THE_SOURCE_RASTER_SHOWS_ONE_THIN_STROKE_HERE"
EV_RASTER_WALL_BAND = "THE_SOURCE_RASTER_SHOWS_A_WALL_BAND_HERE"
EV_AMBIGUOUS_SEPARATION = "PARALLEL_PARTNER_SITS_BETWEEN_THE_TWO_BANDS"
EV_COINCIDENT_DUPLICATE = "DUPLICATED_COINCIDENT_LINEWORK"
EV_COLUMN_LOOP = "A_SMALL_CLOSED_LOOP_THE_SIZE_OF_A_COLUMN"
EV_PARTNER_NOT_MATERIAL_CANDIDATE = (
    "THE_ONLY_PARALLEL_PARTNER_IS_A_DIMENSION_OR_ANNOTATION_ENTITY")

EVIDENCE = (EV_PAIRED_WALL_FACE, EV_NOTHING_BETWEEN,
            EV_WALL_JUNCTION_BOTH_ENDS, EV_WALL_JUNCTION_ONE_END,
            EV_FREE_ENDS, EV_COLLINEAR_RUN, EV_CASEWORK_DEPTH,
            EV_SHORT_RETURN, EV_SPANS_WALL_TO_CASEWORK, EV_DETAIL_FAMILY,
            EV_TOO_SHORT, EV_DIMENSION_LAYER, EV_ANNOTATION_LAYER,
            EV_DOOR_LAYER, EV_CURVE_SEMANTIC, EV_STAIR_ASSEMBLY,
            EV_BLOCK_LINEAGE, EV_RASTER_SINGLE_STROKE,
            EV_RASTER_WALL_BAND, EV_AMBIGUOUS_SEPARATION,
            EV_COINCIDENT_DUPLICATE, EV_PARTNER_NOT_MATERIAL_CANDIDATE,
            EV_COLUMN_LOOP)

# --- GENERAL construction dimensions ------------------------------------
#
# These are ordinary building ranges, not this project's dimensions. A
# masonry or concrete wall in plan is drawn as two faces somewhere between
# a thin partition and a thick structural wall. A fitted unit - base
# cabinet, counter, wardrobe, vanity - stands off the wall by a depth that
# is deliberately DEEPER than any ordinary wall, which is exactly why the
# two can be told apart without knowing what room they are in.
WALL_SEPARATION_MIN_MM = 75.0
WALL_SEPARATION_MAX_MM = 400.0
AMBIGUOUS_SEPARATION_MAX_MM = 450.0
CASEWORK_DEPTH_MIN_MM = 450.0
CASEWORK_DEPTH_MAX_MM = 800.0

# A pair of faces must actually run along each other to be one wall.
#
# A WALL'S TWO FACES ARE RARELY DRAWN AS TWO LINES. An opening breaks one
# face into pieces while the other runs on, so the partner of a 600 mm
# wall face is often three collinear fragments at the same offset. The
# overlap below is therefore measured against the UNION of the fragments
# at one offset, not against any single line - which is why a wall beside
# a door stopped being invisible.
MIN_PAIR_OVERLAP_SHARE = 0.50
MIN_PAIR_OVERLAP_MM = 300.0
OFFSET_BUCKET_MM = 10.0

# Parallel within this angle is parallel; a junction turns by more.
PARALLEL_DEG = 3.0
JUNCTION_TURN_DEG = 20.0
JUNCTION_TOL_MM = 30.0

# An isolated stroke shorter than this cannot establish a wall face on its
# own. It may still BE wall, as a piece of a longer collinear run, and the
# collinear test gives it that chance.
MIN_ISOLATED_WALL_FACE_MM = 300.0

# Three or more parallel strokes finer than a wall are hatch, a door leaf,
# a tiled detail - drawing about the building, not the building. They must
# be strokes of comparable length: a wall face with four 80 mm hatch ticks
# alongside it is a wall, not a family.
DETAIL_FAMILY_MIN_MEMBERS = 3
DETAIL_FAMILY_LENGTH_RATIO = 0.5

# Two lines drawn on top of each other are ONE line drawn twice. Duplicated
# linework is common in a long-lived drawing, and it must not be mistaken
# for a fine parallel family.
COINCIDENT_MM = 2.0

# A wall face continues on the far side of a doorway. A fragment lying on
# the SAME infinite line as an established face, within one opening's
# width of it, is part of that same face - which is how a drawing that
# breaks its linework at every opening still describes one wall.
COLLINEAR_CONTINUATION_MM = 2400.0

# A COLUMN IS A SMALL CLOSED LOOP. Structural columns are drawn as their
# own outline, not as a pair of long faces, so the pairing test cannot see
# them. A short ring enclosing a plausible column footprint is built
# material and may bound a space.
COLUMN_MIN_AREA_M2 = 0.04
COLUMN_MAX_AREA_M2 = 4.0
COLUMN_MAX_SIDE_MM = 2500.0
COLUMN_MIN_SIDE_MM = 150.0
COLUMN_MAX_ASPECT = 4.0

SCOPE = ("GENERAL construction geometry. No project dimension, room name, "
         "region id or coordinate appears in this module, and none of "
         "these ranges was chosen by looking at an expected answer")


class EntityRoleError(RuntimeError):
    """Something asked this module to establish a role it cannot."""


def model_hash() -> str:
    parts = ([MODEL] + list(ENTITY_ROLES) + list(EVIDENCE)
             + [f"{WALL_SEPARATION_MIN_MM}", f"{WALL_SEPARATION_MAX_MM}",
                f"{CASEWORK_DEPTH_MIN_MM}", f"{CASEWORK_DEPTH_MAX_MM}",
                f"{MIN_ISOLATED_WALL_FACE_MM}"])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


@dataclass
class EntityRole:
    """What ONE drawn entity is, and what licensed saying so."""

    object_id: str = ""
    dwg_handle: int | None = None
    layer: str = ""
    entity_type: str = ""
    kind: str = ""
    length_mm: float = 0.0
    layer_default_role: str = ""
    established_role: str = UNKNOWN
    confidence: str = NOT_ESTABLISHED
    evidence: tuple = ()
    partners: tuple = ()
    why: str = ""

    @property
    def may_bound_material(self) -> bool:
        return (self.established_role in MAY_BOUND_MATERIAL
                and self.confidence in (HIGH, MEDIUM))

    def boundary_role(self, *, column_layers=cg.COLUMN_LAYERS_DEFAULT) -> str:
        """The cad_geometry boundary role this established role licenses."""
        if not self.may_bound_material:
            return cg.ROLE_UNRESOLVED
        if self.established_role == GLAZING:
            return cg.GLAZING_BOUNDARY
        if self.layer in column_layers:
            return cg.COLUMN_FACE
        if self.kind in (cg.ARC, cg.CIRCLE, "ARC", "CIRCLE"):
            return cg.CURVED_MATERIAL_FACE
        return cg.MATERIAL_WALL_FACE

    def record(self) -> dict:
        return {
            "object_id": self.object_id,
            "dwg_handle": self.dwg_handle,
            "layer": self.layer,
            "entity_type": self.entity_type,
            "kind": self.kind,
            "length_mm": round(self.length_mm, 3),
            "LAYER_DEFAULT_ROLE": self.layer_default_role,
            "layer_default_is_candidate_generation_only":
                A_LAYER_IS_CANDIDATE_GENERATION_ONLY,
            "ENTITY_ESTABLISHED_ROLE": self.established_role,
            "confidence": self.confidence,
            "MAY_BOUND_MATERIAL": self.may_bound_material,
            "evidence": list(self.evidence),
            "partner_entities": list(self.partners),
            "why": self.why,
        }


# ------------------------------------------------------------- geometry

def _line(prim):
    return (prim.x1, prim.y1, prim.x2, prim.y2)


def _dir(prim):
    dx, dy = prim.x2 - prim.x1, prim.y2 - prim.y1
    n = math.hypot(dx, dy)
    if n <= 0:
        return None
    return (dx / n, dy / n)


ANGLE_BINS = int(round(180.0 / PARALLEL_DEG))


def _angle_bin(u, deg=PARALLEL_DEG):
    """Direction modulo 180 degrees, quantised. A face has no preferred
    end, so a line and its reverse are the same direction here.

    The result is taken modulo the bin count. A line a hair off due west
    lands at 179.99 degrees and rounds to bin 60, which is bin 0 - and
    while those two were stored apart, a 600 mm wall stub beside a door
    could not see the 850 mm face running along it 200 mm away.
    """
    a = math.degrees(math.atan2(u[1], u[0])) % 180.0
    return int(round(a / deg)) % ANGLE_BINS


def _offset_and_span(prim, u):
    """Signed distance from the origin along the normal, and the interval
    the segment occupies along its own direction."""
    nx, ny = -u[1], u[0]
    off = prim.x1 * nx + prim.y1 * ny
    t1 = prim.x1 * u[0] + prim.y1 * u[1]
    t2 = prim.x2 * u[0] + prim.y2 * u[1]
    return off, (min(t1, t2), max(t1, t2))


def _overlap(a, b):
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    return max(0.0, hi - lo)


def _close(p, q, tol):
    return math.hypot(p[0] - q[0], p[1] - q[1]) <= tol


# --------------------------------------------------------------- the pass

def _column_loops(segs) -> set:
    """Object ids on small closed loops - column and pier outlines."""
    try:
        from shapely.geometry import LineString, Point
        from shapely.ops import polygonize, unary_union
        from shapely.strtree import STRtree
    except Exception:
        return set()
    short = [p for p in segs if p.length_mm <= COLUMN_MAX_SIDE_MM]
    if not short:
        return set()
    lines = [LineString([(p.x1, p.y1), (p.x2, p.y2)]) for p in short]
    try:
        faces = list(polygonize(unary_union(lines)))
    except Exception:
        return set()
    tree = STRtree(lines)
    out = set()
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
            continue                       # a 40 mm sliver is hatch
        ring = list(f.exterior.coords)
        for u, v in zip(ring, ring[1:]):
            mid = Point((u[0] + v[0]) / 2.0, (u[1] + v[1]) / 2.0)
            for idx in tree.query(mid.buffer(SNAP := 2.0)):
                if lines[int(idx)].distance(mid) <= SNAP:
                    out.add(short[int(idx)].object_id)
    return out


def establish(primitives, *, layer_defaults=None, dimension_layers=(),
              annotation_layers=(), door_layers=(), glazing_layers=(),
              stair_object_ids=(), curve_roles=None, block_roles=None,
              raster_probe=None) -> dict:
    """Establish a role for EVERY drawn entity, or leave it UNKNOWN.

    `layer_defaults` maps a layer to its LAYER_DEFAULT_ROLE, which is used
    to decide what is worth testing and to rule annotation out. It never
    establishes anything by itself.

    `raster_probe(prim) -> str|None` may return EV_RASTER_WALL_BAND or
    EV_RASTER_SINGLE_STROKE. It is CROSS-REPRESENTATION corroboration from
    the same design family and can only support or challenge a role that
    CAD evidence already proposed - it never creates one.
    """
    layer_defaults = dict(layer_defaults or {})
    curve_roles = dict(curve_roles or {})
    block_roles = dict(block_roles or {})
    stair_ids = set(stair_object_ids or ())

    roles: dict[str, EntityRole] = {}
    segs = []
    for p in primitives:
        r = EntityRole(object_id=p.object_id, dwg_handle=p.provenance.handle,
                       layer=p.provenance.layer,
                       entity_type=p.provenance.entity_type,
                       kind=p.kind, length_mm=p.length_mm,
                       layer_default_role=layer_defaults.get(
                           p.provenance.layer, cg.ROLE_UNRESOLVED))
        roles[p.object_id] = r
        if p.kind == "SEGMENT" and p.length_mm > 0:
            segs.append(p)

    # --- roles that come from somewhere other than parallel geometry ----
    #
    # ORDER MATTERS AND IS DECLARED. What a layer is FOR - dimensions,
    # annotation, door leaves - is settled first, because a dimension line
    # that happens to lie inside a circle is still a dimension line. Then
    # a tread of a detected stair, then curve semantics, then block
    # lineage. Only what none of those claim reaches the geometry tests.
    for p in primitives:
        r = roles[p.object_id]
        lay = p.provenance.layer
        if lay in dimension_layers or r.layer_default_role == (
                cg.DIMENSION_WITNESS):
            r.established_role = (DIMENSION_WITNESS if p.length_mm < 1000.0
                                  else DIMENSION_LINE)
            r.confidence = MEDIUM
            r.evidence = (EV_DIMENSION_LAYER,)
            r.why = ("dimension geometry describes the building; it is not "
                     "the building")
            continue
        if lay in annotation_layers or r.layer_default_role == (
                cg.ANNOTATION_ONLY):
            r.established_role = ANNOTATION
            r.confidence = MEDIUM
            r.evidence = (EV_ANNOTATION_LAYER,)
            r.why = "annotation is writing about the drawing"
            continue
        if lay in door_layers:
            r.established_role = DOOR
            r.confidence = MEDIUM
            r.evidence = (EV_DOOR_LAYER,)
            r.why = ("a door leaf or swing. It stands IN an opening and is "
                     "not the wall beside it")
            continue
        if lay in glazing_layers:
            r.established_role = GLAZING
            r.confidence = MEDIUM
            r.evidence = ("ITS_LAYER_DEFAULT_IS_GLAZING",)
            r.why = "glazing is built material and may bound a space"
            continue
        if p.object_id in stair_ids:
            r.established_role = STAIR_GEOMETRY
            r.confidence = MEDIUM
            r.evidence = (EV_STAIR_ASSEMBLY,)
            r.why = ("a member of a detected stair assembly. A tread is "
                     "not a room wall")
            continue
        if p.object_id in curve_roles:
            r.established_role = curve_roles[p.object_id]["entity_role"]
            r.confidence = curve_roles[p.object_id].get("confidence", MEDIUM)
            r.evidence = (EV_CURVE_SEMANTIC,
                          curve_roles[p.object_id]["curve_semantic"])
            r.why = curve_roles[p.object_id].get("why", "")
            continue
        if p.object_id in block_roles:
            r.established_role = block_roles[p.object_id]
            r.confidence = LOW
            r.evidence = (EV_BLOCK_LINEAGE,)
            r.why = "placed by a block whose lineage is not wall-like"

    # --- index the straight geometry by direction ------------------------
    bins: dict[int, list] = {}
    meta = {}
    for p in segs:
        u = _dir(p)
        if u is None:
            continue
        b = _angle_bin(u)
        off, span = _offset_and_span(p, u)
        meta[p.object_id] = (u, off, span, b)
        bins.setdefault(b, []).append(p)

    # neighbouring bins matter: 179.5 degrees and 0.5 degrees are parallel
    def bin_neighbours(b):
        for d in (-1, 0, 1):
            yield (b + d) % ANGLE_BINS

    def parallel_partners(p):
        """Every parallel segment that runs ALONG this one, with offset.

        Both the partner's offset and its span are measured IN THIS
        SEGMENT'S OWN FRAME, so a partner drawn in the opposite direction
        is still recognised as running along it.
        """
        u, off, span, b = meta[p.object_id]
        nx, ny = -u[1], u[0]
        out, seen = [], set()
        for bb in bin_neighbours(b):
            for q in bins.get(bb, ()):
                if q.object_id == p.object_id or q.object_id in seen:
                    continue
                seen.add(q.object_id)
                d = abs(off - (q.x1 * nx + q.y1 * ny))
                d2 = abs(off - (q.x2 * nx + q.y2 * ny))
                if abs(d - d2) > JUNCTION_TOL_MM:
                    continue                      # not actually parallel
                t1 = q.x1 * u[0] + q.y1 * u[1]
                t2 = q.x2 * u[0] + q.y2 * u[1]
                ov = _overlap(span, (min(t1, t2), max(t1, t2)))
                if ov <= 0:
                    continue
                out.append(((d + d2) / 2.0, ov, q))
        out.sort(key=lambda r: (r[0], -r[1]))
        return out

    partners = {p.object_id: parallel_partners(p) for p in segs}

    # A DIMENSION LINE RUNS PARALLEL TO THE WALL IT MEASURES, and in this
    # drawing it does so about 135 mm away - inside the wall-thickness
    # band. Pairing with one turned a kitchen cabinet front into a wall
    # face. So only entities that could themselves be built material may
    # take part in the parallel reasoning below.
    NOT_MATERIAL_CANDIDATE = (DIMENSION_LINE, DIMENSION_WITNESS, ANNOTATION,
                              DOOR, POOL_INTERNAL_GEOMETRY,
                              CONSTRUCTION_LINE, STAIR_GEOMETRY)

    def candidate(q) -> bool:
        return roles[q.object_id].established_role not in NOT_MATERIAL_CANDIDATE

    def real_partners(p):
        """Parallel partners that could be material, duplicates removed."""
        out = []
        for d, ov, q in partners[p.object_id]:
            if not candidate(q):
                continue
            if d < COINCIDENT_MM:
                continue
            out.append((d, ov, q))
        return out

    def duplicates(p):
        return [q for d, ov, q in partners[p.object_id]
                if d < COINCIDENT_MM and ov >= 0.9 * min(p.length_mm,
                                                         q.length_mm)]

    def _offset_groups(p):
        """Parallel partners gathered by OFFSET, with the union of their
        overlap along this segment. Fragments of one face count once."""
        u, off, span, _b = meta[p.object_id]
        groups = {}
        for d, ov, q in real_partners(p):
            key = round(d / OFFSET_BUCKET_MM)
            uq = _dir(q)
            t1 = q.x1 * u[0] + q.y1 * u[1]
            t2 = q.x2 * u[0] + q.y2 * u[1]
            lo = max(span[0], min(t1, t2))
            hi = min(span[1], max(t1, t2))
            if hi <= lo:
                continue
            g = groups.setdefault(key, {"d": d, "spans": [], "members": []})
            g["spans"].append((lo, hi))
            g["members"].append(q)
            g["d"] = min(g["d"], d) if g["members"] else d
        out = []
        for key, g in groups.items():
            merged, total = [], 0.0
            for lo, hi in sorted(g["spans"]):
                if merged and lo <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
                else:
                    merged.append((lo, hi))
            total = sum(hi - lo for lo, hi in merged)
            out.append((g["d"], total, g["members"]))
        out.sort(key=lambda r: (r[0], -r[1]))
        return out

    def pairs_as_wall(p):
        """A counter-face at wall thickness, running along it, with
        nothing drawn in between. The counter-face may be fragments."""
        best = None
        groups = _offset_groups(p)
        for d, ov, members in groups:
            if d < WALL_SEPARATION_MIN_MM or d > WALL_SEPARATION_MAX_MM:
                continue
            longest = max(q.length_mm for q in members)
            if ov < max(MIN_PAIR_OVERLAP_MM,
                        MIN_PAIR_OVERLAP_SHARE * min(p.length_mm, longest,
                                                     ov if ov else 1e9)):
                continue
            margin = WALL_SEPARATION_MIN_MM * 0.2
            blocked = any(margin < dd < d - margin and ov2 >= 0.5 * ov
                          for dd, ov2, _m in groups)
            if blocked:
                continue
            if best is None or ov > best[1]:
                best = (d, ov, members[0])
        return best

    def ambiguous_partner(p):
        for d, ov, members in _offset_groups(p):
            if WALL_SEPARATION_MAX_MM < d <= AMBIGUOUS_SEPARATION_MAX_MM \
                    and ov >= MIN_PAIR_OVERLAP_MM:
                return (d, ov, members[0])
        return None

    def detail_family(p):
        """Strokes of COMPARABLE LENGTH, finer apart than a wall is thick."""
        fine = [q for d, ov, q in real_partners(p)
                if d < WALL_SEPARATION_MIN_MM
                and ov >= 0.5 * min(p.length_mm, q.length_mm)
                and DETAIL_FAMILY_LENGTH_RATIO <= (
                    q.length_mm / max(p.length_mm, 1e-9))
                <= 1.0 / DETAIL_FAMILY_LENGTH_RATIO]
        return fine if len(fine) >= DETAIL_FAMILY_MIN_MEMBERS - 1 else []

    # endpoint junctions: another MATERIAL-CANDIDATE segment touching this
    # end and turning away from it
    ends = {}
    for p in segs:
        ends[p.object_id] = ((p.x1, p.y1), (p.x2, p.y2))

    def _point_on(pt, q, tol):
        ax, ay, bx, by = _line(q)
        dx, dy = bx - ax, by - ay
        n2 = dx * dx + dy * dy
        if n2 <= 0:
            return False
        t = max(0.0, min(1.0, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / n2))
        return math.hypot(ax + t * dx - pt[0], ay + t * dy - pt[1]) <= tol

    def junctions(p, *, among=None):
        u = meta[p.object_id][0]
        pool = among if among is not None else segs
        hit = [False, False]
        for i, e in enumerate(ends[p.object_id]):
            for q in pool:
                if q.object_id == p.object_id or not candidate(q):
                    continue
                uq = _dir(q)
                if uq is None:
                    continue
                turn = abs(math.degrees(math.acos(
                    max(-1.0, min(1.0, u[0] * uq[0] + u[1] * uq[1])))))
                turn = min(turn, 180.0 - turn)
                if turn < JUNCTION_TURN_DEG:
                    continue
                if _point_on(e, q, JUNCTION_TOL_MM):
                    hit[i] = True
                    break
        return hit

    # --- pass 1: wall faces ---------------------------------------------
    undecided = [p for p in segs
                 if roles[p.object_id].established_role == UNKNOWN]
    junction_cache = {}
    for p in undecided:
        r = roles[p.object_id]
        dups = duplicates(p)
        pair = pairs_as_wall(p)
        if pair is None:
            fam = detail_family(p)
            if fam:
                r.established_role = FIXTURE
                r.confidence = MEDIUM
                r.evidence = (EV_DETAIL_FAMILY,)
                r.partners = tuple(q.object_id for q in fam[:4])
                r.why = (f"{len(fam) + 1} strokes of comparable length lie "
                         "closer together than any wall is thick. That is "
                         "hatch, a leaf or a tiled detail, not wall faces")
                continue
            amb = ambiguous_partner(p)
            if amb is not None:
                r.evidence += (EV_AMBIGUOUS_SEPARATION,)
            if not real_partners(p) and partners[p.object_id]:
                r.evidence += (EV_PARTNER_NOT_MATERIAL_CANDIDATE,)
            continue
        d, ov, q = pair
        j = junction_cache.get(p.object_id)
        if j is None:
            j = junctions(p)
            junction_cache[p.object_id] = j
        ev = [EV_PAIRED_WALL_FACE, EV_NOTHING_BETWEEN]
        if dups:
            ev.append(EV_COINCIDENT_DUPLICATE)
        if all(j):
            ev.append(EV_WALL_JUNCTION_BOTH_ENDS)
            conf = HIGH
        elif any(j):
            ev.append(EV_WALL_JUNCTION_ONE_END)
            conf = MEDIUM
        else:
            # A WALL STUB BESIDE AN OPENING HAS FREE ENDS BY DEFINITION.
            # The pairing is the evidence that something was built here;
            # the junctions only say how sure. Treating free ends as
            # disqualifying left a villa floor with 284 faces and seven
            # closed cells, which is not caution, it is blindness.
            ev.append(EV_FREE_ENDS)
            conf = MEDIUM
        if p.length_mm < MIN_ISOLATED_WALL_FACE_MM:
            ev.append(EV_TOO_SHORT)
            conf = LOW if conf == HIGH else NOT_ESTABLISHED
        if raster_probe is not None:
            seen = raster_probe(p)
            if seen == EV_RASTER_WALL_BAND:
                ev.append(EV_RASTER_WALL_BAND)
            elif seen == EV_RASTER_SINGLE_STROKE:
                ev.append(EV_RASTER_SINGLE_STROKE)
                conf = LOW if conf == HIGH else conf
        r.established_role = (MATERIAL_WALL_FACE if conf in (HIGH, MEDIUM)
                              else UNKNOWN)
        r.confidence = conf if conf in (HIGH, MEDIUM) else NOT_ESTABLISHED
        r.evidence = tuple(ev)
        r.partners = (q.object_id,)
        r.why = (f"a counter-face runs along it {d:.0f} mm away with "
                 f"nothing drawn between them over {ov:.0f} mm"
                 if r.established_role == MATERIAL_WALL_FACE else
                 "paired, but not enough of a wall to be established as one")

    # --- pass 2: columns, which are loops rather than pairs -------------
    for oid in _column_loops(segs):
        r = roles.get(oid)
        if r is None or r.established_role != UNKNOWN:
            continue
        r.established_role = MATERIAL_WALL_FACE
        r.confidence = MEDIUM
        r.evidence = (EV_COLUMN_LOOP,)
        r.why = ("one side of a small closed loop the size of a column. A "
                 "column is built material and bounds the space around it")

    # --- pass 3: casework standing off an established wall face ----------
    walls = [p for p in segs
             if roles[p.object_id].established_role == MATERIAL_WALL_FACE]
    for p in segs:
        r = roles[p.object_id]
        if r.established_role != UNKNOWN:
            continue
        stood_off = None
        for d, ov, q in partners[p.object_id]:
            if not (CASEWORK_DEPTH_MIN_MM <= d <= CASEWORK_DEPTH_MAX_MM):
                continue
            if roles[q.object_id].established_role != MATERIAL_WALL_FACE:
                continue
            if ov < max(MIN_PAIR_OVERLAP_MM,
                        MIN_PAIR_OVERLAP_SHARE * min(p.length_mm,
                                                     q.length_mm)):
                continue
            stood_off = (d, ov, q)
            break
        if stood_off is None:
            continue
        d, ov, q = stood_off
        ev = [EV_CASEWORK_DEPTH]
        j = junctions(p)
        if not any(j):
            ev.append(EV_FREE_ENDS)
        returns = [x for x in segs
                   if x.object_id != p.object_id
                   and x.length_mm <= CASEWORK_DEPTH_MAX_MM * 1.2
                   and any(_point_on(e, p, JUNCTION_TOL_MM)
                           for e in ends[x.object_id])
                   and any(_point_on(e, q, JUNCTION_TOL_MM)
                           for e in ends[x.object_id])]
        if returns:
            ev.append(EV_SHORT_RETURN)
        r.established_role = CABINET_FRONT
        r.confidence = HIGH if returns else MEDIUM
        r.evidence = tuple(ev)
        r.partners = (q.object_id,) + tuple(x.object_id for x in returns[:3])
        r.why = (f"it runs parallel to an established wall face {d:.0f} mm "
                 "away, which is deeper than a wall and is fitted-unit "
                 "depth. Casework stands INSIDE one space; a wall "
                 "separates two")
        for x in returns:
            rx = roles[x.object_id]
            if rx.established_role in (UNKNOWN, MATERIAL_WALL_FACE):
                if rx.established_role == MATERIAL_WALL_FACE and \
                        rx.confidence == HIGH:
                    continue
                rx.established_role = COUNTER_EDGE
                rx.confidence = MEDIUM
                rx.evidence = (EV_SPANS_WALL_TO_CASEWORK, EV_SHORT_RETURN)
                rx.partners = (p.object_id, q.object_id)
                rx.why = ("it runs from a wall face to a casework face, so "
                          "it is the end or return of the fitted unit")

    # --- pass 4: collinear continuation of an established face -----------
    established = [p for p in segs
                   if roles[p.object_id].established_role == MATERIAL_WALL_FACE]
    for p in segs:
        r = roles[p.object_id]
        if r.established_role != UNKNOWN:
            continue
        u, off, span, b = meta[p.object_id]
        for q in established:
            uq, offq, spanq, bq = meta[q.object_id]
            if bq not in set(bin_neighbours(b)):
                continue
            flip = 1.0 if (u[0] * uq[0] + u[1] * uq[1]) >= 0 else -1.0
            if abs(off - flip * offq) > JUNCTION_TOL_MM:
                continue
            lo, hi = sorted((spanq[0] * flip, spanq[1] * flip))
            if min(abs(span[0] - hi), abs(span[1] - lo)) > \
                    COLLINEAR_CONTINUATION_MM \
                    and _overlap(span, (lo, hi)) <= 0:
                continue
            r.established_role = MATERIAL_WALL_FACE
            r.confidence = MEDIUM
            r.evidence = (EV_COLLINEAR_RUN,)
            r.partners = (q.object_id,)
            r.why = ("collinear with an established wall face and within "
                     "one opening's width of it, so it is the same face "
                     "continuing past a door")
            break

    # --- pass 5: anything a casework face touches and nothing else -------
    casework = [p for p in segs
                if roles[p.object_id].established_role in (CABINET_FRONT,
                                                           COUNTER_EDGE,
                                                           CASEWORK)]
    for p in segs:
        r = roles[p.object_id]
        if r.established_role != UNKNOWN:
            continue
        touching = [c for c in casework
                    if any(_point_on(e, c, JUNCTION_TOL_MM)
                           for e in ends[p.object_id])]
        if touching and p.length_mm <= CASEWORK_DEPTH_MAX_MM * 1.5:
            r.established_role = CASEWORK
            r.confidence = MEDIUM
            r.evidence = (EV_SPANS_WALL_TO_CASEWORK,)
            r.partners = tuple(c.object_id for c in touching[:3])
            r.why = ("a short run landing on established casework, so it "
                     "belongs to the fitted unit rather than the room")
            continue
        if r.established_role == UNKNOWN:
            r.why = (r.why or UNKNOWN_CANNOT_RELEASE_AS_MATERIAL_WALL)

    counts = {}
    for r in roles.values():
        counts[r.established_role] = counts.get(r.established_role, 0) + 1
    return {
        "roles": roles,
        "counts": counts,
        "entities": len(roles),
        "may_bound_material": sum(1 for r in roles.values()
                                  if r.may_bound_material),
        "unknown_blocked_from_material": counts.get(UNKNOWN, 0),
    }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "ENTITY_ROLES": list(ENTITY_ROLES),
        "MAY_BOUND_MATERIAL": list(MAY_BOUND_MATERIAL),
        "EVIDENCE": list(EVIDENCE),
        "WALL_SEPARATION_MIN_MM": WALL_SEPARATION_MIN_MM,
        "WALL_SEPARATION_MAX_MM": WALL_SEPARATION_MAX_MM,
        "AMBIGUOUS_SEPARATION_MAX_MM": AMBIGUOUS_SEPARATION_MAX_MM,
        "CASEWORK_DEPTH_MIN_MM": CASEWORK_DEPTH_MIN_MM,
        "CASEWORK_DEPTH_MAX_MM": CASEWORK_DEPTH_MAX_MM,
        "MIN_PAIR_OVERLAP_SHARE": MIN_PAIR_OVERLAP_SHARE,
        "MIN_PAIR_OVERLAP_MM": MIN_PAIR_OVERLAP_MM,
        "MIN_ISOLATED_WALL_FACE_MM": MIN_ISOLATED_WALL_FACE_MM,
        "PARALLEL_DEG": PARALLEL_DEG,
        "JUNCTION_TURN_DEG": JUNCTION_TURN_DEG,
        "JUNCTION_TOL_MM": JUNCTION_TOL_MM,
        "DETAIL_FAMILY_MIN_MEMBERS": DETAIL_FAMILY_MIN_MEMBERS,
        "SCOPE": SCOPE,
        "why": {
            "a_layer_is_candidate_generation_only":
                A_LAYER_IS_CANDIDATE_GENERATION_ONLY,
            "unknown_cannot_release_as_material_wall":
                UNKNOWN_CANNOT_RELEASE_AS_MATERIAL_WALL,
            "what_separates_a_wall_from_a_cabinet": (
                "a wall separates two spaces and is drawn as two faces "
                "with its body between them; casework stands inside one "
                "space, a single face at fitted-unit depth off a wall, "
                "with short returns back to it"),
        },
    }
