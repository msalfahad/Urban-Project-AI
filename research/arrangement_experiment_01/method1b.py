"""METHOD 1B - building the atomic planar arrangement under frozen rules.

Every decision this module makes is the one written in method1b_protocol,
which was hashed before this file existed. Nothing here resolves a role,
admits an edge or classifies a cell by looking at how much area results.

THE SHAPE OF THE METHOD

    1. every interval is asked one question - does the source establish
       that something physical is here, and what is it - and the answer
       is its PLANAR_PARTITION_CAPABILITY. NON_SEPARATOR does not enter.
    2. structural objects enter as ONE closed footprint each, never as
       their constituent linework.
    3. established non-floor contours enter carrying no material, no wall
       length and no finish face.
    4. openings enter as portal breaks that connect the cells either side.
    5. the faces are formed, and formed a SECOND time without the
       unresolved edges, so that a cell which exists only because of
       geometry nobody has identified can be told apart from one that
       does not.
    6. the cells are classified in the pre-declared order, and the
       unbounded exterior is the library's own, not a frame.
"""

from __future__ import annotations

import hashlib
import math

from engine import boundary_capability as bcap
from engine import cad_entity_role as cer
from engine import cad_geometry as cg
from engine import curve_semantics as cs
from engine import interval_role as ir
from engine import line_semantics as ls
from research.arrangement_experiment_01 import method1b_protocol as R

# ------------------------------------------------------------ identity


def _key(p, snap=R.NODE_SNAP_MM):
    return (round(p[0] / snap) * snap, round(p[1] / snap) * snap)


def _eid(pts):
    """An edge's identity is its own geometry, independent of direction."""
    fwd = tuple(_key(p) for p in pts)
    rev = tuple(reversed(fwd))
    best = fwd if fwd <= rev else rev
    return "E-" + hashlib.sha256(repr(best).encode()).hexdigest()[:12]


def _vid(p):
    return "V-" + hashlib.sha256(repr(_key(p)).encode()).hexdigest()[:12]


def _seg_len(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _length(pts):
    return sum(_seg_len(pts[k], pts[k + 1]) for k in range(len(pts) - 1))


# ------------------------------------------------- 1. the admission pass

REFUSED_NOT_A_SEPARATOR = "THE_ESTABLISHED_ROLE_SEPARATES_NOTHING"
REFUSED_NO_ROLE = "NO_ROLE_IS_ESTABLISHED_FOR_THIS_LINEWORK"
REFUSED_LINE_SEMANTICS = "ESTABLISHED_AS_OUTSIDE_THE_CUT_PLANE"
REFUSED_STRUCTURAL_CHANNEL = "REPRESENTED_BY_ITS_OBJECT_FOOTPRINT"
REFUSED_ZERO_LENGTH = "THE_INTERVAL_HAS_NO_LENGTH"


def non_floor_capability(interval, *, curve_roles, round_objects) -> tuple:
    """§5 - is this a non-floor region boundary, or is it unresolved?

    Three conditions, all from frozen E1.4 evidence and none of them the
    shape of the curve or the size of the face it would close.
    """
    oid = interval.parent_object_id
    row = (curve_roles or {}).get(oid) or {}
    sem = row.get("curve_semantic")
    conf = row.get("confidence")
    obj = (round_objects or {}).get(row.get("round_object"))

    named = bool(obj is not None and getattr(obj, "named_by", None))
    right_ring = sem in R.NON_FLOOR_CONTOUR_SEMANTICS
    confident = conf in R.NON_FLOOR_MIN_CONFIDENCE

    why = {
        "CURVE_SEMANTIC": sem,
        "CURVE_SEMANTIC_CONFIDENCE": conf,
        "REGION_IDENTIFIED_BY_SOURCE_EVIDENCE_OTHER_THAN_ITS_SHAPE": named,
        "REGION_NAMED_BY": getattr(obj, "named_by", None),
        "REGION_IDENTITY": getattr(obj, "identity", None),
        "IT_IS_AN_OUTLINE_RING_OF_THAT_REGION": right_ring,
        "CONFIDENCE_IS_SUFFICIENT": confident,
    }
    if named and right_ring and confident:
        return R.NON_FLOOR_REGION_BOUNDARY, why
    return R.UNRESOLVED, why


def admit(intervals, *, semantics, curve_roles, round_objects,
          column_object_ids):
    """One row per interval: its capability, and whether it enters.

    `column_object_ids` are the objects represented by a structural
    footprint, so that their constituent intervals are refused here and
    counted rather than silently dropped.
    """
    rows = []
    for iv in intervals:
        role = iv.role
        line = (semantics.get(iv.interval_id) or {}).get(
            "LINE_SEMANTICS_STATUS")
        cap = R.BY_ROLE.get(role, R.NON_SEPARATOR)
        why_non_floor = None
        admitted, refused = False, None

        if iv.length_mm <= 0:
            refused = REFUSED_ZERO_LENGTH
        elif role == ir.UNKNOWN:
            refused = REFUSED_NO_ROLE
        elif cap == R.NON_SEPARATOR:
            refused = REFUSED_NOT_A_SEPARATOR
        elif line in R.VETOED_BY_LINE_SEMANTICS:
            refused = REFUSED_LINE_SEMANTICS
        elif role == ir.COLUMN:
            # §4 - a column speaks through its object's closed footprint
            refused = REFUSED_STRUCTURAL_CHANNEL
        else:
            if cap == R.NON_FLOOR_REGION_BOUNDARY:
                cap, why_non_floor = non_floor_capability(
                    iv, curve_roles=curve_roles, round_objects=round_objects)
            admitted = True

        rows.append({
            "INTERVAL_ID": iv.interval_id,
            "PARENT_OBJECT_ID": iv.parent_object_id,
            "SEMANTIC_ROLE": role,
            "LINE_SEMANTICS_STATUS": line,
            "length_mm": round(iv.length_mm, 3),
            "PLANAR_PARTITION_CAPABILITY": cap if admitted else R.NON_SEPARATOR
            if refused in (REFUSED_NOT_A_SEPARATOR, REFUSED_NO_ROLE) else cap,
            "ADMITTED_TO_THE_ARRANGEMENT": admitted,
            "REFUSED_BECAUSE": refused,
            "NON_FLOOR_EVIDENCE": why_non_floor,
            "REPRESENTED_BY_A_STRUCTURAL_FOOTPRINT": (
                iv.parent_object_id in column_object_ids
                if role == ir.COLUMN else False),
        })
    return rows


# ------------------------------------------------ 2. structural objects

FOOTPRINT_NOT_ESTABLISHED = "THE_OBJECTS_OWN_LOOP_RING_IS_NOT_ESTABLISHED"
FOOTPRINT_WITHDRAWN = "VALIDATION_WITHDREW_THE_STRUCTURAL_CLAIM"


def structural_footprints(column_rows):
    """§4 - one closed outer footprint per object, and nothing else."""
    out = []
    for row in column_rows:
        status = row.get("COLUMN_EXISTENCE_STATUS")
        cap = R.STRUCTURAL_ADMISSION.get(status)
        ring = row.get("LOOP_RING") or row.get(
            "FOOTPRINT_RING_MM") or row.get("loop_ring")
        established = bool(row.get("LOOP_RING_ESTABLISHED")) and ring
        rec = {
            "STRUCTURAL_OBJECT_ID": row.get("COLUMN_ID"),
            "COLUMN_EXISTENCE_STATUS": status,
            "STRUCTURAL_EXISTENCE": status,
            "MEMBER_OBJECT_IDS": sorted(row.get("member_object_ids") or ()),
            "member_intervals_not_admitted_individually": True,
            "LOOP_RING_ESTABLISHED": bool(row.get("LOOP_RING_ESTABLISHED")),
            "CLEAR_FACE_OWNERSHIP_STATUS": row.get(
                "CLEAR_FACE_OWNERSHIP_STATUS"),
            "ownership_did_not_decide_admission": True,
            "PLANAR_PARTITION_CAPABILITY": cap,
            "ring_mm": None,
        }
        if cap is None:
            rec["ARRANGEMENT_BOUNDARY_RELEVANCE"] = FOOTPRINT_WITHDRAWN
            rec["ADMITTED_TO_THE_ARRANGEMENT"] = False
        elif not established:
            rec["ARRANGEMENT_BOUNDARY_RELEVANCE"] = FOOTPRINT_NOT_ESTABLISHED
            rec["ADMITTED_TO_THE_ARRANGEMENT"] = False
        else:
            pts = [tuple(float(v) for v in p) for p in ring]
            if pts[0] != pts[-1]:
                pts.append(pts[0])
            rec["ring_mm"] = [list(p) for p in pts]
            rec["perimeter_mm"] = round(_length(pts), 3)
            rec["ARRANGEMENT_BOUNDARY_RELEVANCE"] = (
                "ONE_CLOSED_OUTER_FOOTPRINT")
            rec["ADMITTED_TO_THE_ARRANGEMENT"] = True
        out.append(rec)
    return out


# ----------------------------------------------------- 3. the edge build


def _curve_provenance(iv, parent, pts):
    """§10 - the analytical arc, and how far the chords stray from it."""
    if iv is None or iv.kind not in (cg.ARC, cg.CIRCLE) or parent is None:
        return None
    r = getattr(parent, "radius", None)
    worst = 0.0
    if r:
        for k in range(len(pts) - 1):
            c = _seg_len(pts[k], pts[k + 1])
            half = min(c / 2.0, float(r))
            worst = max(worst, float(r) - math.sqrt(max(float(r) ** 2
                                                        - half ** 2, 0.0)))
    return {
        "SOURCE_CURVE_ID": iv.parent_object_id,
        "SOURCE_CURVE_TYPE": iv.kind,
        "SOURCE_INTERVAL_ID": iv.interval_id,
        "centre_mm": [getattr(parent, "cx", None), getattr(parent, "cy", None)],
        "radius_mm": r,
        "TOPOLOGY_APPROXIMATION": "CHORD_POLYLINE_FOR_NODING_ONLY",
        "TOPOLOGY_LINEARISATION_TOLERANCE_MM": R.ARC_TOPOLOGY_TOLERANCE_MM,
        "MAX_APPROXIMATION_ERROR_MM": round(worst, 6),
        "a_chord_is_never_an_arc": R.A_CHORD_IS_NEVER_AN_ARC,
    }


def edge_record(pts, *, capability, semantic_role, entity_ids, interval_ids,
                curve=None, ownership=None, portal=None, non_floor=None,
                structural=None):
    material = capability in R.MAY_CARRY_MATERIAL
    wall_len_allowed = capability in R.MAY_CARRY_WALL_LENGTH
    sep = (True if capability in R.PHYSICALLY_SEPARATES else
           False if capability in R.EXPLICITLY_DOES_NOT_SEPARATE else
           "UNRESOLVED")
    ln = round(_length(pts), 3)
    rec = {
        "EDGE_ID": _eid(pts),
        "SOURCE_ENTITY_IDS": sorted(set(entity_ids or ())),
        "SOURCE_INTERVAL_IDS": sorted(set(interval_ids or ())),
        "SEMANTIC_ROLE": semantic_role,
        "PLANAR_PARTITION_CAPABILITY": capability,
        "MATERIAL_PRESENT": bool(material),
        "PHYSICAL_SEPARATION": sep,
        "CAN_OWN_CLEAR_FINISH_FACE": ownership,
        "WALL_LENGTH_CONTRIBUTION_ALLOWED": bool(wall_len_allowed),
        "WALL_LENGTH_CONTRIBUTION_MM": ln if wall_len_allowed else 0.0,
        "ADJACENT_CELL_IDS": [],
        "PROVENANCE": {
            "points_mm": [list(p) for p in pts],
            "length_mm": ln,
            "VERTEX_IDS": [_vid(pts[0]), _vid(pts[-1])],
            "CURVE": curve,
            "PORTAL": portal,
            "NON_FLOOR": non_floor,
            "STRUCTURAL_OBJECT": structural,
        },
    }
    if capability == R.NON_FLOOR_REGION_BOUNDARY:
        rec.update(dict(R.NON_FLOOR_EDGES_CARRY))
        rec["NON_FLOOR_SUBROLE"] = R.NON_FLOOR_SUBROLE_UNRESOLVED
        rec["the_subrole_is_recorded_separately"] = (
            R.THE_SUBROLE_IS_RECORDED_SEPARATELY)
    if capability == R.PORTAL_BREAK:
        rec["NO_FAKE_MATERIAL_EDGE_ACROSS_THE_OPENING"] = True
    return rec


def _dedupe(edges):
    by_id = {}
    for e in edges:
        got = by_id.get(e["EDGE_ID"])
        if got is None:
            by_id[e["EDGE_ID"]] = e
            continue
        got["SOURCE_ENTITY_IDS"] = sorted(
            set(got["SOURCE_ENTITY_IDS"]) | set(e["SOURCE_ENTITY_IDS"]))
        got["SOURCE_INTERVAL_IDS"] = sorted(
            set(got["SOURCE_INTERVAL_IDS"]) | set(e["SOURCE_INTERVAL_IDS"]))
    return list(by_id.values())


# --------------------------------------------------- 4. faces and cells


def _lines(edges, *, only=None, without=None):
    """The geometry handed to the topology library, on the declared grid.

    NODE_SNAP_MM is what "the same node" means in this method. Two faces
    of a wall that meet at a corner one thousandth of a millimetre apart
    are one corner in the drawing and must be one node here, or the face
    never closes. The snap applies to the topology ONLY: every edge keeps
    its exact points in its own provenance and no length or area is ever
    taken from a snapped copy.
    """
    from shapely.geometry import LineString
    snap = R.NODE_SNAP_MM
    out = []
    for e in edges:
        cap = e["PLANAR_PARTITION_CAPABILITY"]
        if only is not None and cap not in only:
            continue
        if without is not None and cap in without:
            continue
        pts = [(round(x / snap) * snap, round(y / snap) * snap)
               for x, y in e["PROVENANCE"]["points_mm"]]
        ded = [pts[0]] + [p for i, p in enumerate(pts[1:], 1)
                          if p != pts[i - 1]]
        if len(ded) >= 2:
            out.append(LineString(ded))
    return out


def faces_of(edges, *, only=None, without=None):
    from shapely.ops import polygonize, unary_union
    lines = _lines(edges, only=only, without=without)
    if not lines:
        return []
    return list(polygonize(unary_union(lines)))


def build(edges):
    """The arrangement, plus the two counterfactuals the rules require."""
    faces = faces_of(edges)
    cells = []
    for n, f in enumerate(sorted(faces, key=lambda g: -g.area), start=1):
        rp = f.representative_point()
        cells.append({
            "CELL_ID": f"C-{n:05d}",
            "area_mm2": round(f.area, 3),
            "perimeter_mm": round(f.length, 3),
            "representative_point_mm": [round(rp.x, 3), round(rp.y, 3)],
            "_geom": f,
        })
    return cells


def attach(cells, edges, *, tol_mm=R.NODE_SNAP_MM):
    """Which edges bound which cell, which cells share one, and the outside."""
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    from shapely.strtree import STRtree

    geoms = [LineString([tuple(p) for p in e["PROVENANCE"]["points_mm"]])
             for e in edges]
    tree = STRtree(geoms)
    for c in cells:
        ring = c["_geom"].exterior
        buf = ring.buffer(tol_mm)
        on = []
        for idx in tree.query(buf):
            j = int(idx)
            shared = geoms[j].intersection(buf)
            if not shared.is_empty and shared.length > tol_mm:
                on.append(edges[j]["EDGE_ID"])
        c["BOUNDING_EDGE_IDS"] = sorted(set(on))

    owner = {}
    for c in cells:
        for eid in c["BOUNDING_EDGE_IDS"]:
            owner.setdefault(eid, []).append(c["CELL_ID"])
    for e in edges:
        e["ADJACENT_CELL_IDS"] = sorted(owner.get(e["EDGE_ID"], []))

    # the unbounded exterior is the library's own: the complement of the
    # union of the bounded faces. No computational frame is introduced.
    outside = unary_union([c["_geom"] for c in cells]) if cells else None
    touching_outside = set()
    if outside is not None and not outside.is_empty:
        skin = outside.boundary
        for c in cells:
            if c["_geom"].exterior.intersection(skin.buffer(tol_mm)).length \
                    > tol_mm:
                touching_outside.add(c["CELL_ID"])

    by_id = {e["EDGE_ID"]: e for e in edges}
    for c in cells:
        adj, through_portal = set(), set()
        for eid in c["BOUNDING_EDGE_IDS"]:
            others = [x for x in owner.get(eid, ()) if x != c["CELL_ID"]]
            adj |= set(others)
            if by_id[eid]["PLANAR_PARTITION_CAPABILITY"] == R.PORTAL_BREAK:
                through_portal |= set(others)
        if c["CELL_ID"] in touching_outside:
            adj.add(R.OUTSIDE_CELL_ID)
        c["ADJACENT_CELL_IDS"] = sorted(adj)
        c["CONNECTED_THROUGH_A_PORTAL"] = sorted(through_portal)
    return cells, edges, sorted(touching_outside)


def _extent(geom):
    x0, y0, x1, y1 = geom.bounds
    return (x1 - x0, y1 - y0)


def classify(cells, edges, *, mates_by_object, structural_rings,
             non_floor_faces, surviving_faces):
    """The pre-declared order, first test that answers wins."""
    from shapely.geometry import Point
    from shapely.strtree import STRtree

    by_id = {e["EDGE_ID"]: e for e in edges}
    obstacle_tree = STRtree(structural_rings) if structural_rings else None
    non_floor_tree = STRtree(non_floor_faces) if non_floor_faces else None
    survive_tree = STRtree(surviving_faces) if surviving_faces else None

    def inside(tree, polys, pt):
        if tree is None:
            return False
        return any(polys[int(i)].contains(pt) for i in tree.query(pt))

    for c in cells:
        pt = Point(*c["representative_point_mm"])
        bounding = [by_id[e] for e in c["BOUNDING_EDGE_IDS"] if e in by_id]
        material = [e for e in bounding if e["MATERIAL_PRESENT"]]
        unresolved = [e for e in bounding
                      if e["PLANAR_PARTITION_CAPABILITY"] == R.UNRESOLVED]
        parents = set()
        for e in material:
            for oid in e["SOURCE_ENTITY_IDS"]:
                parents.add(oid.split("#")[0])
        paired = any(m in parents
                     for p in parents for m in mates_by_object.get(p, ()))
        w, h = _extent(c["_geom"])
        thin = min(w, h) <= R.WALL_FACE_MAX_THICKNESS_MM
        all_material = bool(bounding) and len(material) == len(bounding)
        survives = inside(survive_tree, surviving_faces, pt)

        if c["area_mm2"] <= R.SLIVER_AREA_MM2:
            klass, test = R.MATERIAL_SOLID_CELL, "1_SLIVER"
        elif all_material and thin and paired:
            klass, test = (R.MATERIAL_SOLID_CELL,
                           "2_INSIDE_ONE_PAIRED_WALL_BODY")
        elif inside(obstacle_tree, structural_rings, pt):
            klass, test = R.OBSTACLE_CELL, "3_INSIDE_A_STRUCTURAL_FOOTPRINT"
        elif all_material and thin:
            klass, test = (R.OBSTACLE_CELL,
                           "4_THIN_AND_ALL_MATERIAL_BUT_UNPAIRED")
        elif inside(non_floor_tree, non_floor_faces, pt):
            klass, test = (R.NON_FLOOR_CELL,
                           "5_INSIDE_AN_ESTABLISHED_NON_FLOOR_REGION")
        elif unresolved and not survives:
            klass, test = (R.UNRESOLVED_CELL,
                           "6_CLOSURE_DEPENDS_ON_UNRESOLVED_EDGES")
        else:
            klass, test = R.FREE_SPACE_CELL, "7_OTHERWISE"

        c["CELL_CLASS"] = klass
        c["DECIDED_BY"] = test
        c["why_this_class"] = dict(R.CELL_CLASSIFICATION_ORDER)[test]
        c["bounding_edges"] = len(bounding)
        c["bounding_edges_carrying_material"] = len(material)
        c["bounding_edges_that_are_unresolved"] = len(unresolved)
        c["SURVIVES_WITHOUT_UNRESOLVED_EDGES"] = bool(survives)
        c["min_extent_mm"] = round(min(w, h), 3)
        c["max_extent_mm"] = round(max(w, h), 3)
        c["IT_IS_A_NODING_SLIVER"] = c["area_mm2"] <= R.SLIVER_AREA_MM2
    return cells


# ------------------------------------- 5. what a case's representation is


def representation(cells, edges, *, anchor_mm):
    """§13 - three named tests, no area anywhere in any of them."""
    from shapely.geometry import LineString, Point

    pt = Point(*anchor_mm)
    by_id = {e["EDGE_ID"]: e for e in edges}
    home = None
    for c in cells:
        if c["_geom"].contains(pt):
            home = c
            break

    tests = {
        "ANCHOR_LANDS_IN_A_BOUNDED_CELL": home is not None,
        "THE_CELL_IS_NOT_MATERIAL_OR_SLIVER": None,
        "NO_HARD_SEPARATOR_RUNS_THROUGH_THE_CELL": None,
    }
    if home is None:
        return {
            "VERDICT": R.NO_MEANINGFUL_CELL_REPRESENTATION,
            "CELL_ID": None, "CELL_CLASS": None,
            "TESTS": tests,
            "FAILED_TEST": "ANCHOR_LANDS_IN_A_BOUNDED_CELL",
            "CELLS_IN_THE_REPRESENTATION": [],
            "why": ("the label anchor falls in the unbounded exterior: the "
                    "arrangement encloses nothing where the drawing puts "
                    "this label"),
        }

    tests["THE_CELL_IS_NOT_MATERIAL_OR_SLIVER"] = (
        home["CELL_CLASS"] != R.MATERIAL_SOLID_CELL
        and not home["IT_IS_A_NODING_SLIVER"])

    interior = home["_geom"]
    through = []
    for eid in set(e["EDGE_ID"] for e in edges) - set(
            home["BOUNDING_EDGE_IDS"]):
        e = by_id[eid]
        if e["PLANAR_PARTITION_CAPABILITY"] != R.HARD_PHYSICAL_SEPARATOR:
            continue
        ln = LineString([tuple(p) for p in e["PROVENANCE"]["points_mm"]])
        if ln.intersection(interior).length > R.NODE_SNAP_MM:
            through.append(eid)
    tests["NO_HARD_SEPARATOR_RUNS_THROUGH_THE_CELL"] = not through

    # the cells reachable from here through portal breaks alone
    by_cell = {c["CELL_ID"]: c for c in cells}
    seen, stack = {home["CELL_ID"]}, [home["CELL_ID"]]
    while stack:
        cid = stack.pop()
        for nxt in by_cell[cid].get("CONNECTED_THROUGH_A_PORTAL", ()):
            if nxt in by_cell and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)

    failed = [k for k, v in tests.items() if v is False]
    return {
        "VERDICT": (R.MEANINGFUL_ATOMIC_CELL_REPRESENTATION if not failed
                    else R.NO_MEANINGFUL_CELL_REPRESENTATION),
        "CELL_ID": home["CELL_ID"],
        "CELL_CLASS": home["CELL_CLASS"],
        "TESTS": tests,
        "FAILED_TEST": failed[0] if failed else None,
        "HARD_SEPARATORS_RUNNING_THROUGH_THE_CELL": sorted(through),
        "CELLS_IN_THE_REPRESENTATION": sorted(seen),
        "CELLS_REACHED_THROUGH_PORTAL_BREAKS": sorted(seen - {
            home["CELL_ID"]}),
        "no_area_was_compared_to_anything": R.AREA_CLOSENESS_IS_NOT_A_TEST,
    }
