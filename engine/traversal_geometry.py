"""E1.4 §18 - a path is not a boundary, and a boundary is not material.

E1.3 walked a boundary and wrote one chain. That chain carried three
different things in one list, and told them apart with a single flag on
each element:

  the ORDER the walk went in - which face was entered from which end,
  where it turned, where it crossed, where it stopped;

  the BOUNDARY of the region - the geometry that encloses it, each
  stretch appearing once however many times the walk passed along it;

  the MATERIAL the boundary is made of - the wall bodies that stand on
  those stretches, each body being one body whether the walk saw one of
  its faces or both.

A single drawn line with no established thickness makes the difference
visible. The walk runs up one side of it and back down the other, because
both of its sides face this space. That is two steps in the traversal and
it is correct. It is ONE stretch of boundary and ONE piece of material,
and anything that reads the traversal as a length reads that line twice.

Nothing here is a quantity. No plaster, no skirting, no wall area, no
BOQ. What this module does is decide WHICH register a later stage must
read for which question, so that the double step in the traversal can
never reach a length:

  physical boundary length            -> UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY
  wall material length                -> MATERIAL_CONTRIBUTION_GEOMETRY
  a future plaster or skirting length  -> MATERIAL_CONTRIBUTION_GEOMETRY,
      with the number of faces of each body that face this region carried
      as its own field, because how many faces a finish covers is that
      finish's question and not the traversal's
  what the walk did, and in what order -> TRAVERSAL_PATH

The three objects are built from the same walk in one pass, so they
cannot drift apart.
"""

from __future__ import annotations

import math

MODEL = "A_PATH_IS_NOT_A_BOUNDARY_AND_A_BOUNDARY_IS_NOT_MATERIAL_V1"

# the three objects this module separates
TRAVERSAL_PATH = "TRAVERSAL_PATH"
UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY = "UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY"
MATERIAL_CONTRIBUTION_GEOMETRY = "MATERIAL_CONTRIBUTION_GEOMETRY"

# what a stretch of boundary is
MATERIAL_FACE = "MATERIAL_FACE"
WALL_END_FACE = "WALL_END_ACROSS_ITS_OWN_THICKNESS"
PORTAL_SPAN = "PORTAL_SPAN_ACROSS_A_CLASSIFIED_GAP"
OPEN_STATION = "BOUNDARY_OPEN_AT_THIS_STATION"
TURN_WITHOUT_GEOMETRY = "TURN_THAT_CROSSES_NOTHING"

BOUNDARY_KINDS = (MATERIAL_FACE, WALL_END_FACE, PORTAL_SPAN)

# tolerances. Geometry identity is decided at the drawing's own precision
POINT_SNAP_MM = 0.001
ANGLE_BUCKET_DEG = 0.05
OFFSET_BUCKET_MM = 0.5

A_PATH_MAY_VISIT_THE_SAME_MATERIAL_TWICE = (
    "the traversal is a record of what the walk did. A single drawn line "
    "whose thickness is not established has both of its sides facing this "
    "space, and the walk goes up one side and back down the other. Two "
    "steps on one piece of material is the correct traversal and it is "
    "not two pieces of boundary")

A_TURN_ACROSS_NOTHING_HAS_NO_LENGTH = (
    "the turn at the end of a single drawn line crosses no thickness, "
    "because no thickness is established for that line. It is a step in "
    "the traversal with no geometry, and it contributes nothing to any "
    "length. A turn across an ESTABLISHED thickness is different: that "
    "stretch is the end of the wall, it is drawn material, and its length "
    "is the thickness the pairing established")

A_PORTAL_IS_BOUNDARY_BUT_NOT_MATERIAL = (
    "a classified gap is crossed because the boundary of the space "
    "continues across it. The span encloses the region and belongs to its "
    "physical boundary. No wall stands on it, so it contributes no wall "
    "material and no wall finish")

AN_OPEN_STATION_ESTABLISHES_NO_GEOMETRY = (
    "where the walk runs out, nothing is drawn across the opening and "
    "nothing is established. The station is recorded so that the region "
    "is known to be unclosed. No span is invented across it and no "
    "length is added for it")

A_FACE_FINISH_READS = (
    "a finish is applied to faces, so a stage that needs plaster or "
    "skirting reads FACES_WALKED_ON_THIS_REGIONS_SIDE against "
    "BODY_RUN_LENGTH_MM, or reads the faces themselves. A wall standing "
    "in a room with both of its sides in that room is one wall with two "
    "finished faces. A single drawn line walked up and back is one wall "
    "with ONE face, because one line is one face however many times the "
    "walk passed along it, and that is what stops the U-turn reaching a "
    "finish quantity")

A_BODY_IS_ONE_BODY = (
    "a wall body is one body whether the walk passed along one of its "
    "faces or both. Its run along its own axis is recorded once, and the "
    "number of its faces that face this region is recorded beside it as "
    "its own fact. Two faces facing one space is a property of the wall, "
    "not twice as much wall")

NO_QUANTITY_IS_CALCULATED_IN_E1_4 = (
    "these registers carry geometry ownership only. E1.4 calculates no "
    "quantity, opens no workbook and reconciles nothing")

WHICH_REGISTER_ANSWERS_WHICH_QUESTION = {
    "physical boundary length": UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY,
    "region enclosure and area": UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY,
    "wall material length": MATERIAL_CONTRIBUTION_GEOMETRY,
    "future plaster length": MATERIAL_CONTRIBUTION_GEOMETRY,
    "future skirting length": MATERIAL_CONTRIBUTION_GEOMETRY,
    "what the walk did and in what order": TRAVERSAL_PATH,
}


# --------------------------------------------------------------- geometry
def _seg_len(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _poly_len(pts):
    return sum(_seg_len(pts[k], pts[k + 1]) for k in range(len(pts) - 1))


def _rd(p):
    return (round(p[0] / POINT_SNAP_MM) * POINT_SNAP_MM,
            round(p[1] / POINT_SNAP_MM) * POINT_SNAP_MM)


def geometry_key(points):
    """The identity of a drawn stretch, independent of the direction walked.

    ORDER IS NEVER IDENTITY. A face entered from its far end is the same
    face, and a span crossed the other way is the same span, so the key
    is taken from the two orderings and the smaller one is kept.
    """
    fwd = tuple(_rd(p) for p in points)
    rev = tuple(reversed(fwd))
    return fwd if fwd <= rev else rev


def _bucket(a, b):
    """Collinearity bucket: a direction in [0, 180) and a signed offset."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    if n <= 0.0:
        return None
    ang = math.degrees(math.atan2(dy, dx)) % 180.0
    if ang >= 180.0 - ANGLE_BUCKET_DEG / 2.0:
        ang -= 180.0
    # the direction is taken from the bucket and not from the segment, so a
    # segment drawn the other way lands in the same bucket with the same
    # offset. ORDER IS NEVER IDENTITY, and neither is the way round a line
    # happens to have been drawn
    r = math.radians(ang)
    ux, uy = math.cos(r), math.sin(r)
    off = -uy * a[0] + ux * a[1]          # perpendicular offset of the line
    return (round(ang / ANGLE_BUCKET_DEG), round(off / OFFSET_BUCKET_MM))


def _merged_length(segments, *, collapse_offset=False):
    """Total length of a set of segments, counting overlap once.

    Segments that are collinear and overlap are the same stretch of
    boundary drawn twice. Merging them removes the overlap; segments that
    only touch end to end merge without changing the total.

    With `collapse_offset` the perpendicular offset is dropped, so the
    two faces of one wall body project onto the body's own axis and the
    body's run is measured once. That is used ONLY within a single body,
    where the faces are the same wall seen from its two sides.
    """
    groups, removed = {}, 0.0
    for a, b in segments:
        key = _bucket(a, b)
        if key is None:
            continue
        ang = math.radians(key[0] * ANGLE_BUCKET_DEG)
        ux, uy = math.cos(ang), math.sin(ang)
        ta = a[0] * ux + a[1] * uy
        tb = b[0] * ux + b[1] * uy
        gk = (key[0],) if collapse_offset else key
        groups.setdefault(gk, []).append((min(ta, tb), max(ta, tb)))
    total = 0.0
    for key, ivs in groups.items():
        raw = sum(hi - lo for lo, hi in ivs)
        ivs.sort()
        lo, hi = ivs[0]
        merged = 0.0
        for s, e in ivs[1:]:
            if s > hi:
                merged += hi - lo
                lo, hi = s, e
            else:
                hi = max(hi, e)
        merged += hi - lo
        total += merged
        removed += raw - merged
    return total, removed


def _segments(points):
    return [(points[k], points[k + 1]) for k in range(len(points) - 1)]


# ------------------------------------------------------------- traversal
def traverse(steps, pieces, *, mates=None, gap_by_id=None,
             face_points=None):
    """Build the three objects from one walk.

    `steps` is the step list `engine.boundary_walk.walk` produced.
    `mates` maps a piece to the pieces that are the other face of the same
    wall body, as `boundary_walk.mate_map` returns it - it is what tells
    this module which body a face belongs to, and whether a thickness was
    established for it at all.
    `face_points` may override the points of a piece, for a caller that
    carries an arc's drawn points separately from its ends.
    """
    mates = mates or {}
    gap_by_id = gap_by_id or {}
    face_points = face_points or {}

    path, boundary, open_stations = [], {}, []
    bodies = {}
    traversal_mm = 0.0

    def body_of(i):
        """The identity of the wall body a face belongs to.

        Taken from the faces themselves and not from a position in any
        list: the body is the set of geometry keys of this face and of the
        faces paired with it.
        """
        keys = [geometry_key(_pts(i))]
        thickness, family = None, None
        for m in mates.get(i, ()):
            keys.append(geometry_key(_pts(m["mate"])))
            if thickness is None:
                thickness = m["thickness_mm"]
                family = m["matched_family_mm"]
        return tuple(sorted(keys)), thickness, family

    def _pts(i):
        if i in face_points:
            return [tuple(p) for p in face_points[i]]
        return [tuple(p) for p in pieces[i]["coords"]]

    for order, st in enumerate(steps):
        kind = st["STEP"]
        if kind == "MATERIAL_WALL_FACE" or kind == "EXPOSED_COLUMN_FACE" \
                or kind == "GLAZING_BOUNDARY":
            i = st["piece"]
            pts = _pts(i)
            walked = (pts if st.get("entered_at_end", 0) == 0
                      else list(reversed(pts)))
            key = geometry_key(pts)
            length = _poly_len(pts)
            first = key not in boundary
            path.append({
                "ORDER": order, "STEP": kind, "BOUNDARY_KIND": MATERIAL_FACE,
                "GEOMETRY_KEY_HASH": _hash(key),
                "entered_from_mm": list(walked[0]),
                "left_at_mm": list(walked[-1]),
                "length_mm": round(length, 3),
                "THIS_STRETCH_IS_NEW_TO_THE_BOUNDARY": first,
                "why_a_repeat_is_not_more_boundary":
                    None if first else A_PATH_MAY_VISIT_THE_SAME_MATERIAL_TWICE,
            })
            traversal_mm += length
            if first:
                boundary[key] = {
                    "BOUNDARY_KIND": MATERIAL_FACE,
                    "points_mm": [list(p) for p in pts],
                    "length_mm": round(length, 3),
                    "object_id": pieces[i].get("object_id") or "",
                    "layer": pieces[i].get("layer"),
                    "boundary_role": pieces[i].get("boundary_role"),
                    "TIMES_WALKED": 1,
                }
            else:
                boundary[key]["TIMES_WALKED"] += 1
            bkey, thickness, family = body_of(i)
            b = bodies.setdefault(bkey, {
                "THICKNESS_ESTABLISHED": thickness is not None,
                "THICKNESS_MM": thickness,
                "MATCHED_THICKNESS_FAMILY_MM": family,
                "faces": {}, "segments": [], "end_faces_mm": 0.0,
                "TRAVERSAL_LENGTH_ATTRIBUTED_MM": 0.0,
            })
            b["TRAVERSAL_LENGTH_ATTRIBUTED_MM"] += length
            if key not in b["faces"]:
                b["faces"][key] = round(length, 3)
                b["segments"].extend(_segments(pts))

        elif kind == "WALL_END_RETURN":
            a, z = tuple(st["at_mm"]), tuple(st["to_mm"])
            key = geometry_key([a, z])
            length = _seg_len(a, z)
            first = key not in boundary
            path.append({
                "ORDER": order, "STEP": kind, "BOUNDARY_KIND": WALL_END_FACE,
                "GEOMETRY_KEY_HASH": _hash(key),
                "entered_from_mm": list(a), "left_at_mm": list(z),
                "length_mm": round(length, 3),
                "THIS_STRETCH_IS_NEW_TO_THE_BOUNDARY": first,
                "WALL_THICKNESS_MM": st.get("thickness_mm"),
            })
            traversal_mm += length
            if first:
                boundary[key] = {
                    "BOUNDARY_KIND": WALL_END_FACE,
                    "points_mm": [list(a), list(z)],
                    "length_mm": round(length, 3),
                    "WALL_THICKNESS_MM": st.get("thickness_mm"),
                    "why": st.get("why"), "TIMES_WALKED": 1,
                }
            else:
                boundary[key]["TIMES_WALKED"] += 1
            i = st.get("mate_piece")
            if i is not None:
                bkey, thickness, family = body_of(i)
                b = bodies.setdefault(bkey, {
                    "THICKNESS_ESTABLISHED": thickness is not None,
                    "THICKNESS_MM": thickness,
                    "MATCHED_THICKNESS_FAMILY_MM": family,
                    "faces": {}, "segments": [], "end_faces_mm": 0.0,
                    "TRAVERSAL_LENGTH_ATTRIBUTED_MM": 0.0,
                })
                if first:
                    b["end_faces_mm"] += length

        elif kind == "SINGLE_LINE_WALL_END_TURN":
            path.append({
                "ORDER": order, "STEP": kind,
                "BOUNDARY_KIND": TURN_WITHOUT_GEOMETRY,
                "at_mm": list(st["at_mm"]), "length_mm": 0.0,
                "THIS_STRETCH_IS_NEW_TO_THE_BOUNDARY": False,
                "why": A_TURN_ACROSS_NOTHING_HAS_NO_LENGTH,
            })

        elif kind == "ACROSS_A_CLASSIFIED_GAP":
            a, z = tuple(st["start_mm"]), tuple(st["end_mm"])
            key = geometry_key([a, z])
            length = _seg_len(a, z)
            first = key not in boundary
            path.append({
                "ORDER": order, "STEP": kind, "BOUNDARY_KIND": PORTAL_SPAN,
                "GEOMETRY_KEY_HASH": _hash(key),
                "gap": st.get("gap"), "GAP_CLASS": st.get("GAP_CLASS"),
                "entered_from_mm": list(a), "left_at_mm": list(z),
                "length_mm": round(length, 3),
                "THIS_STRETCH_IS_NEW_TO_THE_BOUNDARY": first,
                "CONTRIBUTES_MATERIAL": False,
                "why": A_PORTAL_IS_BOUNDARY_BUT_NOT_MATERIAL,
            })
            traversal_mm += length
            if first:
                boundary[key] = {
                    "BOUNDARY_KIND": PORTAL_SPAN,
                    "points_mm": [list(a), list(z)],
                    "length_mm": round(length, 3),
                    "gap": st.get("gap"), "GAP_CLASS": st.get("GAP_CLASS"),
                    "CONTRIBUTES_MATERIAL": False, "TIMES_WALKED": 1,
                }
            else:
                boundary[key]["TIMES_WALKED"] += 1

        elif kind == "BOUNDARY_RUNS_OUT_HERE":
            open_stations.append({
                "ORDER": order, "at_mm": list(st.get("at_mm", [])),
                "why": st.get("why"),
                "ESTABLISHES_NO_GEOMETRY": True,
                "no_span_is_invented_here":
                    AN_OPEN_STATION_ESTABLISHES_NO_GEOMETRY,
            })
            path.append({
                "ORDER": order, "STEP": kind, "BOUNDARY_KIND": OPEN_STATION,
                "at_mm": list(st.get("at_mm", [])), "length_mm": 0.0,
                "THIS_STRETCH_IS_NEW_TO_THE_BOUNDARY": False,
            })

        else:
            path.append({"ORDER": order, "STEP": kind,
                         "BOUNDARY_KIND": None, "length_mm": 0.0,
                         "THIS_STRETCH_IS_NEW_TO_THE_BOUNDARY": False,
                         "why": "this step carries no geometry"})

    # ---- the unique physical boundary, with collinear overlap counted once
    segments = []
    for row in boundary.values():
        segments.extend(_segments([tuple(p) for p in row["points_mm"]]))
    unique_mm, overlap_mm = _merged_length(segments)
    by_kind = {}
    for row in boundary.values():
        by_kind[row["BOUNDARY_KIND"]] = round(
            by_kind.get(row["BOUNDARY_KIND"], 0.0) + row["length_mm"], 3)

    # ---- the material, one row per wall body
    material = []
    for bkey, b in bodies.items():
        run_mm, body_overlap = _merged_length(b["segments"],
                                              collapse_offset=True)
        face_mm, _ = _merged_length(b["segments"])
        faces = len(b["faces"])
        material.append({
            "BODY_ID": _hash(bkey),
            "FACE_GEOMETRY_KEY_HASHES": [_hash(k) for k in b["faces"]],
            "THICKNESS_ESTABLISHED": b["THICKNESS_ESTABLISHED"],
            "THICKNESS_MM": b["THICKNESS_MM"],
            "MATCHED_THICKNESS_FAMILY_MM": b["MATCHED_THICKNESS_FAMILY_MM"],
            "FACES_WALKED_ON_THIS_REGIONS_SIDE": faces,
            "BOTH_SIDES_FACE_THIS_REGION": faces > 1,
            # the wall, measured along itself, once
            "BODY_RUN_LENGTH_MM": round(run_mm, 3),
            # the drawn faces of it this region is on the side of
            "FACE_LENGTH_ON_THIS_REGIONS_SIDE_MM": round(face_mm, 3),
            "WALL_END_FACE_LENGTH_MM": round(b["end_faces_mm"], 3),
            "TRAVERSAL_LENGTH_ATTRIBUTED_MM":
                round(b["TRAVERSAL_LENGTH_ATTRIBUTED_MM"], 3),
            "COLLINEAR_OVERLAP_NOT_COUNTED_MM": round(body_overlap, 3),
            "WALL_MATERIAL_LENGTH_READS": "BODY_RUN_LENGTH_MM",
            "A_FACE_FINISH_READS": A_FACE_FINISH_READS,
            "A_BODY_IS_ONE_BODY": A_BODY_IS_ONE_BODY,
        })
    material.sort(key=lambda r: r["BODY_ID"])

    body_run_mm = sum(r["BODY_RUN_LENGTH_MM"] for r in material)
    return {
        "MODEL": MODEL,
        "WHICH_REGISTER_ANSWERS_WHICH_QUESTION":
            dict(WHICH_REGISTER_ANSWERS_WHICH_QUESTION),
        "NO_QUANTITY_IS_CALCULATED_IN_E1_4": NO_QUANTITY_IS_CALCULATED_IN_E1_4,
        TRAVERSAL_PATH: {
            "steps": path,
            "TRAVERSAL_LENGTH_MM": round(traversal_mm, 3),
            "STEPS_THAT_REPEAT_A_STRETCH": sum(
                1 for s in path
                if s["BOUNDARY_KIND"] in BOUNDARY_KINDS
                and not s["THIS_STRETCH_IS_NEW_TO_THE_BOUNDARY"]),
            "A_PATH_MAY_VISIT_THE_SAME_MATERIAL_TWICE":
                A_PATH_MAY_VISIT_THE_SAME_MATERIAL_TWICE,
        },
        UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY: {
            "stretches": [dict(GEOMETRY_KEY_HASH=_hash(k), **v)
                          for k, v in sorted(
                              boundary.items(), key=lambda kv: _hash(kv[0]))],
            "PHYSICAL_BOUNDARY_LENGTH_MM": round(unique_mm, 3),
            "LENGTH_BY_KIND_MM": by_kind,
            "COLLINEAR_OVERLAP_NOT_COUNTED_MM": round(overlap_mm, 3),
            "DUPLICATION_THE_TRAVERSAL_WOULD_HAVE_ADDED_MM":
                round(traversal_mm - unique_mm, 3),
            "OPEN_STATIONS": open_stations,
            "PHYSICAL_BOUNDARY_IS_COMPLETE": not open_stations,
        },
        MATERIAL_CONTRIBUTION_GEOMETRY: {
            "bodies": material,
            "BODIES": len(material),
            "BODY_RUN_LENGTH_MM": round(body_run_mm, 3),
            "FACE_LENGTH_ON_THIS_REGIONS_SIDE_MM": round(sum(
                r["FACE_LENGTH_ON_THIS_REGIONS_SIDE_MM"] for r in material), 3),
            "WALL_END_FACE_LENGTH_MM": round(
                sum(r["WALL_END_FACE_LENGTH_MM"] for r in material), 3),
            "BODIES_WITH_NO_ESTABLISHED_THICKNESS": sum(
                1 for r in material if not r["THICKNESS_ESTABLISHED"]),
            "BODIES_FACING_THIS_REGION_ON_BOTH_SIDES": sum(
                1 for r in material if r["BOTH_SIDES_FACE_THIS_REGION"]),
            "A_PORTAL_IS_BOUNDARY_BUT_NOT_MATERIAL":
                A_PORTAL_IS_BOUNDARY_BUT_NOT_MATERIAL,
        },
    }


def _hash(key):
    import hashlib
    return hashlib.sha256(repr(key).encode()).hexdigest()[:16]


A_TRAVERSAL_MAY_NEVER_BE_READ_AS_A_LENGTH = (
    "TRAVERSAL_LENGTH_MM is the distance the walk travelled. It is a "
    "diagnostic. Any stage that needs a length reads the register named "
    "for its question in WHICH_REGISTER_ANSWERS_WHICH_QUESTION")


def assert_no_stretch_is_counted_twice(out):
    """No geometry key may contribute to the boundary length more than once."""
    seen = set()
    for s in out[UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY]["stretches"]:
        k = s["GEOMETRY_KEY_HASH"]
        if k in seen:
            raise AssertionError(
                "A_STRETCH_OF_BOUNDARY_APPEARS_TWICE = " + k)
        seen.add(k)
    u = out[UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY]["PHYSICAL_BOUNDARY_LENGTH_MM"]
    t = out[TRAVERSAL_PATH]["TRAVERSAL_LENGTH_MM"]
    if u > t + 1e-6:
        raise AssertionError(
            "THE_BOUNDARY_CANNOT_BE_LONGER_THAN_THE_WALK = "
            f"{u} > {t}")
    return True
