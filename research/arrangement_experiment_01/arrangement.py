"""The hard physical arrangement - research only.

WHAT THIS IS

Every credible piece of PHYSICAL boundary the frozen E1.4 evidence layer
admits is noded into edges, and the edges are polygonized into faces.
Every point of the drawn fabric then lies in exactly one face. That is
the whole proposition: a representation that is TOTAL, so that "open" is
a kind of answer rather than the absence of one.

WHAT IT MAY NOT BE GIVEN

Dimension and witness lines, hidden and overhead geometry, counters,
cabinet fronts, door swing arcs as material, the pool water contour as
masonry, annotation, and any soft semantic boundary. The E1.4 capability
and line-semantics gates decide this; nothing is re-classified here.

THE ONE THING THAT IS ADDED

A cell has to be bounded or it leaks across the floor. Where a doorway or
an unclassified gap interrupts the fabric, a NON-MATERIAL edge is carried
across it so the cell closes. It is marked as carrying no material, as
contributing no wall length, and as either not separating (a classified
portal) or not settled (an unclassified gap). That is the opposite of
inventing a wall: the edge exists to hold the topology and its own record
disqualifies it from every material question.

WALL THICKNESS IS NOT ROOM

Polygonizing wall faces produces faces INSIDE the walls. They are found
and classified as material solid before anything is grouped, because the
thing this experiment groups is free space.

CURVES

shapely has no exact arc. For the topology an arc is linearised at a
recorded tolerance; its analytical identity - centre, radius, angles, the
source entity - is kept in the curve provenance register, and the
linearisation is never written back over the source.
"""

from __future__ import annotations

import hashlib
import math

from research.arrangement_experiment_01 import protocol as P

# How finely an arc is linearised for the topology only.
ARC_TOPOLOGY_TOLERANCE_MM = 2.0
# Nodes closer than this are the same node.
NODE_SNAP_MM = 1.0
# A face this thin, bounded by both faces of one wall body, is the wall.
WALL_FACE_MAX_THICKNESS_MM = 600.0
# Below this a face is a sliver of the noding, not a space.
SLIVER_AREA_MM2 = 10_000.0

A_LINEARISATION_IS_NOT_THE_GEOMETRY = (
    "an arc is linearised only so that a topology library can node it. "
    "The analytical arc is kept with its centre, radius and angles, and "
    "any length or area that matters is taken from the analytical source. "
    "A chord is never called an arc")


def _key(p, snap=NODE_SNAP_MM):
    return (round(p[0] / snap) * snap, round(p[1] / snap) * snap)


def _eid(pts):
    """An edge's identity: its own geometry, independent of direction."""
    fwd = tuple(_key(p) for p in pts)
    rev = tuple(reversed(fwd))
    best = fwd if fwd <= rev else rev
    return "E-" + hashlib.sha256(repr(best).encode()).hexdigest()[:12]


def _seg_len(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def edge_role(boundary_role, interval_role, *, is_portal=False,
              is_unresolved=False, exposed=False):
    """What KIND of hard boundary an edge is. Nothing is reclassified."""
    if is_portal:
        return P.CONFIRMED_DOOR_PORTAL
    if is_unresolved:
        return P.UNRESOLVED_EDGE
    if interval_role == "GLAZING":
        return P.GLAZING_BOUNDARY
    if interval_role == "COLUMN":
        return (P.EXPOSED_STRUCTURAL_OBSTACLE if exposed
                else P.COLUMN_INTRUSION)
    return P.MATERIAL_WALL


def build(pieces, *, portals=(), unresolved=(), role_of=None,
          exposed_ids=frozenset()):
    """Node the physical edges and polygonize them into faces.

    `pieces` are the noded material pieces E1.4 already produced, each
    carrying its source entity. `portals` and `unresolved` are the spans
    that close a cell without building anything.
    """
    from shapely.geometry import LineString, Polygon
    from shapely.ops import polygonize, unary_union

    role_of = role_of or (lambda oid: None)
    edges, lines = [], []

    def add(pts, *, role, oid, interval_id, material, curve=None,
            gap_id=None, gap_class=None):
        pts = [tuple(float(x) for x in p) for p in pts]
        if len(pts) < 2 or _seg_len(pts[0], pts[-1]) <= 0 and len(pts) == 2:
            return
        e = {
            "EDGE_ID": _eid(pts),
            "EDGE_ROLE": role,
            "points_mm": [list(p) for p in pts],
            "length_mm": round(sum(_seg_len(pts[k], pts[k + 1])
                                   for k in range(len(pts) - 1)), 3),
            "SOURCE_ENTITY_IDS": [oid] if oid else [],
            "SOURCE_INTERVAL_IDS": [interval_id] if interval_id else [],
            "MATERIAL_PRESENT": bool(material),
            "WALL_LENGTH_CONTRIBUTION_MM": (
                round(sum(_seg_len(pts[k], pts[k + 1])
                          for k in range(len(pts) - 1)), 3) if material
                else 0.0),
            "PHYSICAL_SEPARATION": (
                True if role in P.SEPARATES else
                False if role in P.DOES_NOT_SEPARATE else "UNRESOLVED"),
            "CURVE_PROVENANCE": curve,
            "PORTAL_RELATION": ({"GAP_ID": gap_id, "GAP_CLASS": gap_class}
                                if gap_id else None),
        }
        edges.append(e)
        lines.append(LineString(pts))

    for pc in pieces:
        oid = pc.get("object_id") or ""
        parent = oid.split("#")[0]
        iv_role = role_of(oid)
        add(pc["coords"],
            role=edge_role(pc.get("boundary_role"), iv_role,
                           exposed=parent in exposed_ids),
            oid=oid, interval_id=pc.get("key"), material=True,
            curve=pc.get("curve"))

    for g in portals:
        add([tuple(g["start_mm"]), tuple(g["end_mm"])],
            role=P.CONFIRMED_DOOR_PORTAL, oid="", interval_id=None,
            material=False, gap_id=g.get("GAP_ID"),
            gap_class=g.get("GAP_CLASS"))

    for g in unresolved:
        add([tuple(g["start_mm"]), tuple(g["end_mm"])],
            role=P.UNRESOLVED_EDGE, oid="", interval_id=None,
            material=False, gap_id=g.get("GAP_ID"),
            gap_class=g.get("GAP_CLASS"))

    # de-duplicate by geometric identity, merging provenance
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
    edges = list(by_id.values())

    faces = list(polygonize(unary_union(lines)))
    cells = []
    for n, f in enumerate(sorted(faces, key=lambda g: -g.area), start=1):
        cells.append({
            "CELL_ID": f"C-{n:05d}",
            "area_mm2": round(f.area, 3),
            "perimeter_mm": round(f.length, 3),
            "representative_point_mm": [round(f.representative_point().x, 3),
                                        round(f.representative_point().y, 3)],
            "_geom": f,
        })
    return {"edges": edges, "cells": cells,
            "a_linearisation_is_not_the_geometry":
                A_LINEARISATION_IS_NOT_THE_GEOMETRY}


def attach_edges_to_cells(cells, edges, *, tol_mm=NODE_SNAP_MM):
    """Which edges bound which cell, and which cells share an edge."""
    from shapely.geometry import LineString
    from shapely.strtree import STRtree

    geoms = [LineString([tuple(p) for p in e["points_mm"]]) for e in edges]
    tree = STRtree(geoms)
    for c in cells:
        ring = c["_geom"].exterior
        on = []
        for idx in tree.query(ring.buffer(tol_mm)):
            j = int(idx)
            shared = geoms[j].intersection(ring.buffer(tol_mm))
            if not shared.is_empty and shared.length > tol_mm:
                on.append(edges[j]["EDGE_ID"])
        c["BOUNDING_EDGE_IDS"] = sorted(set(on))
    owner = {}
    for c in cells:
        for eid in c["BOUNDING_EDGE_IDS"]:
            owner.setdefault(eid, []).append(c["CELL_ID"])
    for e in edges:
        e["ADJACENT_CELL_IDS"] = sorted(owner.get(e["EDGE_ID"], []))
    for c in cells:
        adj = set()
        for eid in c["BOUNDING_EDGE_IDS"]:
            adj |= set(owner.get(eid, []))
        adj.discard(c["CELL_ID"])
        c["ADJACENT_CELL_IDS"] = sorted(adj)
    return cells, edges


def classify_cells(cells, edges, *, mates_by_object=None):
    """Free space, or the inside of a wall, or an obstacle.

    A face bounded mostly by faces of ONE wall body is that wall's own
    inside. A small face wedged between material is a junction sliver.
    Everything else that is bounded and not tiny is free space.
    """
    mates_by_object = mates_by_object or {}
    by_id = {e["EDGE_ID"]: e for e in edges}
    for c in cells:
        bounding = [by_id[e] for e in c["BOUNDING_EDGE_IDS"] if e in by_id]
        material = [e for e in bounding if e["MATERIAL_PRESENT"]]
        parents = set()
        for e in material:
            for oid in e["SOURCE_ENTITY_IDS"]:
                parents.add(oid.split("#")[0])
        paired = any(m in parents
                     for p in parents for m in mates_by_object.get(p, ()))
        w, h = _extent(c["_geom"])
        thin = min(w, h) <= WALL_FACE_MAX_THICKNESS_MM
        all_material = bounding and len(material) == len(bounding)

        if c["area_mm2"] <= SLIVER_AREA_MM2:
            klass, why = P.MATERIAL_SOLID_CELL, (
                "smaller than the sliver threshold: this is a junction "
                "artefact of noding, not a space")
        elif all_material and thin and paired:
            klass, why = P.MATERIAL_SOLID_CELL, (
                "bounded only by drawn material, thin, and its bounding "
                "faces belong to one paired wall body. This is the inside "
                "of the wall and it is not floor")
        elif all_material and thin:
            klass, why = P.OBSTACLE_CELL, (
                "bounded only by drawn material and thin, but no pairing "
                "establishes it as one wall body. It is an obstacle, and "
                "what kind is not settled here")
        else:
            klass, why = P.FREE_SPACE_CELL, (
                "bounded, larger than a sliver, and not the inside of a "
                "wall body")
        c["CELL_CLASS"] = klass
        c["why_this_class"] = why
        c["bounding_edges"] = len(bounding)
        c["bounding_edges_carrying_material"] = len(material)
        c["min_extent_mm"] = round(min(w, h), 3)
        c["max_extent_mm"] = round(max(w, h), 3)
    return cells


def _extent(geom):
    x0, y0, x1, y1 = geom.bounds
    return (x1 - x0, y1 - y0)
