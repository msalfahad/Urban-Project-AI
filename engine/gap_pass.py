"""E1.3 §5, §6 — re-decide every gap the geometry pass found.

The frozen E1.2 geometry is kept exactly as it is. Finding the gaps -
dangling wall ends, collinearity, the width between them - was never the
defect and that pass still does it. What it must no longer do is DECIDE
what a gap is, because it decided on shape alone.

So the candidate gaps come out of the frozen pass and every one of them
is classified again here, against the drawing's own evidence: what stands
in the gap, what door entities are actually there, and the wall
thicknesses this drawing uses. Only a gap that classifies as a portal
closes a boundary. The rest are recorded as junctions, as places where
material continues, as open edges, or as questions.
"""

from __future__ import annotations

import math

from engine import cad_geometry as cg
from engine import gap_ontology as go

MODEL = "EVERY_GAP_IS_RECLASSIFIED_AGAINST_THE_DRAWINGS_OWN_EVIDENCE_V1"

# How far from the gap's mid-line a crossing element may sit and still be
# read as standing IN it. Derived from the gap itself, never a constant.
OCCUPANCY_SHARE_OF_GAP = 0.75


def _mid(a, b):
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _dist_point_seg(p, a, b) -> float:
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    n = dx * dx + dy * dy
    if n <= 0:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / n))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def _angle_between(a, b, c, d) -> float:
    u = math.atan2(b[1] - a[1], b[0] - a[0])
    v = math.atan2(d[1] - c[1], d[0] - c[0])
    x = abs(math.degrees(u - v)) % 180.0
    return min(x, 180.0 - x)


def occupancy_of(jamb_a, jamb_b, *, material_segments, structural_ids=(),
                 host_ids=()) -> list:
    """§6 — what, if anything, is standing in this gap?

    Standing IN the gap means CROSSING IT: the element's own geometry
    meets the span between the two jambs. Being near the gap is not
    enough - the counter-face of the very wall the gap is cut into is
    always near it, and reading that as occupancy would make every
    doorway a junction.

    A cross wall landing in the gap, a column sitting in it, any other
    material band crossing it: each makes the boundary continue rather
    than open. The host walls on either side are excluded, because a gap
    is by definition between them, and so is anything running along the
    gap rather than across it.
    """
    from shapely.geometry import LineString

    gap = math.hypot(jamb_b[0] - jamb_a[0], jamb_b[1] - jamb_a[1])
    if gap <= 0:
        return []
    span = LineString([jamb_a, jamb_b])
    # a crossing element may stop a hair short of the span it lands on
    tol = min(cg.SNAP_MM * 2.0, gap * 0.1)
    found = []
    for s in material_segments:
        oid = getattr(s, "object_id", "")
        if oid in host_ids:
            continue
        try:
            pts = s.points(tol_mm=cg.DENSIFY_TOL_MM)
        except Exception:
            continue
        if len(pts) < 2:
            continue
        line = LineString(pts)
        if line.distance(span) > tol:
            continue
        ang = _angle_between(jamb_a, jamb_b, pts[0], pts[-1])
        if ang < 20.0:
            # it runs ALONG the gap, not across it: this is the other face
            # of the same wall, or its collinear continuation
            continue
        if oid in structural_ids:
            found.append(go.OCC_COLUMN_OR_PIER)
        elif ang >= 45.0:
            found.append(go.OCC_PERPENDICULAR_WALL)
        else:
            found.append(go.OCC_OTHER_MATERIAL_BAND)
    return sorted(set(found))


def door_evidence_near(jamb_a, jamb_b, door_segments) -> list:
    """Is a door leaf, swing arc or door block actually drawn in this gap?

    engine.cad_geometry.close_openings looks for door geometry among the
    primitives it was given, and it is given MATERIAL geometry - which a
    door leaf is not. So it never finds one, and every gap falls through
    to the jamb-pair reading. The evidence is gathered here instead, from
    the intervals whose role is DOOR.
    """
    from shapely.geometry import LineString

    gap = math.hypot(jamb_b[0] - jamb_a[0], jamb_b[1] - jamb_a[1])
    if gap <= 0 or not door_segments:
        return []
    span = LineString([jamb_a, jamb_b])
    # a leaf swings off the opening it fills, so its geometry sits within
    # about its own width of the gap it belongs to
    reach = gap
    hits = []
    for s in door_segments:
        try:
            pts = s.points(tol_mm=cg.DENSIFY_TOL_MM)
        except Exception:
            continue
        if len(pts) < 2:
            continue
        if LineString(pts).distance(span) <= reach:
            hits.append(getattr(s, "object_id", ""))
    return sorted({h for h in hits if h})


def reclassify(closure, *, material_segments, structural_ids=(),
               band_offsets_mm=(), visual_doorways_near=None,
               door_segments=(),
               junction_gap_mm=cg.JUNCTION_GAP_MM,
               max_barrier_mm=cg.MAX_DOUBLE_LEAF_MM) -> dict:
    """Classify every candidate gap, and keep only real portals as barriers.

    `visual_doorways_near` is an optional callable taking a midpoint and
    returning True where the cold source-only pass read a doorway. It
    supplies one of the circumstantial evidences and never a confirming
    one: a reader saying "that looks like a door" is not the author
    drawing one.
    """
    thick = go.thickness_families(band_offsets_mm)
    confirmed_widths = []
    rows, barriers, open_edges = [], [], []

    ordered = list(closure.get("rows", ()))
    by_bar = {id(b): b for b in closure.get("barriers", ())}
    bars = list(closure.get("barriers", ()))

    # first pass: the confirmed doors, so their widths can form a family
    doors_at = {}
    for i, r in enumerate(ordered):
        a, b = [tuple(p) for p in r["jamb_endpoints_mm"]]
        hits = (list(r.get("door_entities_in_the_gap") or ())
                or door_evidence_near(a, b, door_segments))
        doors_at[i] = hits
        if hits:
            confirmed_widths.append(float(r["gap_mm"]))
    widths = go.width_families(confirmed_widths)

    for i, r in enumerate(ordered):
        a, b = [tuple(p) for p in r["jamb_endpoints_mm"]]
        gap = float(r["gap_mm"])
        hosts = tuple(r.get("host_wall_faces") or ())
        occ = occupancy_of(a, b, material_segments=material_segments,
                           structural_ids=structural_ids, host_ids=hosts)

        conf = []
        if doors_at.get(i):
            conf.append(go.EV_DOOR_LEAF_OR_SWING)

        prob = []
        if len(hosts) >= 2:
            prob.append(go.EV_JAMB_GEOMETRY)
        fam_w = go.matches_a_width_family(gap, widths)
        if fam_w and not conf:
            prob.append(go.EV_WIDTH_FAMILY)
        if visual_doorways_near is not None and visual_doorways_near(_mid(a, b)):
            prob.append(go.EV_VISUAL_DOORWAY)

        fam_t = go.matches_a_thickness_family(gap, thick)
        cls = go.classify(gap_mm=gap, junction_gap_mm=junction_gap_mm,
                          max_barrier_mm=max_barrier_mm,
                          confirming_evidence=conf, probable_evidence=prob,
                          occupancy=occ, thickness_family=fam_t,
                          collinear=r.get("grade") != cg.GRADE_JUNCTION
                          or gap <= junction_gap_mm)

        bar = bars[i] if i < len(bars) else None
        keep = None
        if cls["GAP_CLASS"] in go.IS_A_PORTAL:
            keep, role = bar, cg.VIRTUAL_PORTAL_BOUNDARY
        elif cls["GAP_CLASS"] in go.MATERIAL_CONTINUES_ACROSS:
            keep, role = bar, cg.CAD_JUNCTION_REPAIR
        else:
            role = None
            open_edges.append({
                "GAP_CLASS": cls["GAP_CLASS"],
                "start_mm": [round(a[0], 3), round(a[1], 3)],
                "end_mm": [round(b[0], 3), round(b[1], 3)],
                "gap_mm": round(gap, 2),
                "host_wall_faces": list(hosts),
                "why": "; ".join(cls["notes"]),
            })
        if keep is not None:
            barriers.append(cg.BoundarySegment(
                kind=keep.kind, x1=keep.x1, y1=keep.y1, x2=keep.x2,
                y2=keep.y2, role=role, object_id=keep.object_id,
                entity_type=keep.entity_type, layer=keep.layer,
                evidence=tuple(list(keep.evidence)
                               + [f"E1_3_GAP_CLASS={cls['GAP_CLASS']}"]),
                confidence=("HIGH" if cls["GAP_CLASS"]
                            == go.CONFIRMED_DOOR_PORTAL else "MEDIUM")))

        rows.append({
            "GAP_ID": f"GAP-{i + 1:03d}",
            **cls,
            "E1_2_GRADE_FOR_COMPARISON": r.get("grade"),
            "E1_2_WOULD_HAVE_CLOSED_IT": r.get("grade") in (
                cg.OPENING_GRADE_DOOR_ENTITY, cg.OPENING_GRADE_JAMB_PAIR,
                cg.GRADE_JUNCTION),
            "start_mm": [round(a[0], 3), round(a[1], 3)],
            "end_mm": [round(b[0], 3), round(b[1], 3)],
            "host_wall_faces": list(hosts),
            "door_entities_in_the_gap": list(doors_at.get(i) or ()),
            "BOUNDARY_ROLE": role,
            "closes_the_boundary": role is not None,
            "contributes_material": False,
        })

    counts = {c: sum(1 for r in rows if r["GAP_CLASS"] == c)
              for c in go.GAP_CLASSES}
    return {
        "MODEL": MODEL,
        "rows": rows,
        "barriers": barriers,
        "open_or_unresolved_edges": open_edges,
        "counts_by_class": counts,
        "wall_thickness_families_inferred": thick,
        "opening_width_families_from_confirmed_doors": widths,
        "candidate_gaps": len(rows),
        "closed_as_portal": sum(1 for r in rows
                                if r["GAP_CLASS"] in go.IS_A_PORTAL),
        "closed_as_material_continuity": sum(
            1 for r in rows if r["GAP_CLASS"] in go.MATERIAL_CONTINUES_ACROSS),
        "left_open": len(open_edges),
        "E1_2_WOULD_HAVE_CLOSED": sum(1 for r in rows
                                      if r["E1_2_WOULD_HAVE_CLOSED_IT"]),
        "a_junction_and_a_door_are_different_ontologies":
            go.A_JUNCTION_AND_A_DOOR_ARE_DIFFERENT_ONTOLOGIES,
    }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "OCCUPANCY_SHARE_OF_GAP": OCCUPANCY_SHARE_OF_GAP,
        "gap_ontology": go.frozen_parameters(),
        "geometry_reused_unchanged": (
            "engine.cad_geometry.close_openings finds the candidate gaps and "
            "is not modified. This pass replaces what is concluded from "
            "them, never how they are found"),
    }
