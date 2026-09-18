"""E1.4 — a column is not confirmed while its own geometry disagrees.

THE DEFECT THIS REPLACES

External review of frozen E1.3 found a loop classified as a structural
column whose recorded footprint_box_mm spans roughly 600 x 2600 mm while
its recorded size_mm reads 600 x 250 mm. Two numbers describing one
footprint, an order of magnitude apart in one direction, and the
classification survived.

No structural classification may outlive an internal geometry
inconsistency. A 600 x 2600 figure may be a column, a pier, a wall stub,
a duct or a stair nosing - but whatever it is, a classifier that reports
its size as 600 x 250 does not know which, and must say so.

WHERE THE TWO NUMBERS CAME FROM

Reproducing it showed the disagreement is in the derivation. size_mm is
the bounding box of the polygonized FACE - the loop itself. The
footprint_box_mm the E1.3 register carries is the bounding box of the
whole ENTITIES that contribute sides to that loop, and a member entity
can be a wall line several metres long whose contribution to the loop is
250 mm of it. So the 2600 is a wall, not a column, and a register that
calls it a footprint says something untrue about its own subject.

That is a finding either way, and a strong one: a loop whose sides are
parts of long wall lines is a corner of the room's fabric, not a
discrete column. The two boxes are derived and reported separately here,
and the reach of each member beyond the footprint is a fact about the
candidate rather than a reason to keep quiet.

WHAT THIS DOES

Every candidate's geometry is derived here, from its own closed loop, and
cross-checked against what was reported about it. Where they disagree the
candidate is UNRESOLVED and the disagreement is recorded with both
numbers.

WHAT IT REFUSES TO DO

Nothing is deleted. A candidate that fails is still a real drawn figure
and keeps its geometry; only the claim that it is a structural column is
withheld.

And no candidate becomes a column merely because it is a closed loop,
because it repeats, because it touches a wall, because part of it lies on
a structural layer, or because it resembles another loop. LAYER EVIDENCE
IS EVIDENCE, NOT TRUTH: it raises a candidate and never settles it.
"""

from __future__ import annotations

import hashlib
import math

MODEL = "NO_STRUCTURAL_CLASSIFICATION_SURVIVES_ITS_OWN_INCONSISTENCY_V1"

STRUCTURAL_COLUMN_CONFIRMED = "STRUCTURAL_COLUMN_CONFIRMED"
STRUCTURAL_COLUMN_UNRESOLVED = "STRUCTURAL_COLUMN_UNRESOLVED"
NOT_A_STRUCTURAL_COLUMN = "NOT_A_STRUCTURAL_COLUMN"

EXISTENCE_STATUSES = (STRUCTURAL_COLUMN_CONFIRMED,
                      STRUCTURAL_COLUMN_UNRESOLVED,
                      NOT_A_STRUCTURAL_COLUMN)

# How far the derived and reported figures may differ and still agree.
SIZE_TOLERANCE_MM = 5.0
# A closed loop whose two sides differ by more than this is not a compact
# footprint. It is not thereby disqualified - it is a reason to look.
COMPACT_ASPECT_LIMIT = 4.0

LAYER_EVIDENCE_IS_EVIDENCE_NOT_TRUTH = (
    "a structural layer is where the author put something. It raises a "
    "candidate and settles nothing: a wall stub, a duct, a plinth and a "
    "stair nosing all end up on structural layers too. Nothing becomes a "
    "column because of its layer, because it is closed, because it "
    "repeats, because it touches a wall, or because it resembles another "
    "loop")

NOTHING_IS_DELETED = (
    "a candidate that fails validation keeps its geometry and its "
    "identity as a drawn figure. What is withheld is only the claim that "
    "it is a structural column. Deleting drawn material to tidy a "
    "classification loses the drawing")

WHY_SELF_CONSISTENCY_COMES_FIRST = (
    "the derived footprint and the reported size describe the same thing. "
    "If they disagree, at least one is wrong and nothing downstream can "
    "tell which. Every other question about the candidate - exposure, "
    "clear-face ownership - is asked of a geometry that has to be settled "
    "first")


def model_hash() -> str:
    parts = [MODEL, str(SIZE_TOLERANCE_MM), str(COMPACT_ASPECT_LIMIT)] \
        + list(EXISTENCE_STATUSES)
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def derive_geometry(loop) -> dict:
    """Everything about a closed loop, computed from the loop itself."""
    pts = [(float(x), float(y)) for x, y in (loop or ())]
    if len(pts) < 3:
        return {"DERIVED": False,
                "why": "fewer than three points is not a closed footprint"}
    if pts[0] != pts[-1]:
        pts = pts + [pts[0]]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    per = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
              for i in range(len(pts) - 1))
    area = abs(sum(pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]
                   for i in range(len(pts) - 1))) / 2.0
    longest = max(
        math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        for i in range(len(pts) - 1))
    short, long_ = (min(w, h), max(w, h))
    return {
        "DERIVED": True,
        "derived_bbox_width_mm": round(w, 3),
        "derived_bbox_height_mm": round(h, 3),
        "derived_perimeter_mm": round(per, 3),
        "derived_area_mm2": round(area, 3),
        "longest_member_extent_mm": round(longest, 3),
        "vertices": len(pts) - 1,
        "aspect_ratio": round(long_ / short, 3) if short > 0 else None,
        "footprint_is_compact": (
            short > 0 and (long_ / short) <= COMPACT_ASPECT_LIMIT),
    }


MEMBER_REACH_TOLERANCE_MM = 5.0

A_MEMBER_IS_NOT_THE_FOOTPRINT = (
    "the loop's own ring is the footprint. A member entity that carries "
    "on past that ring is a longer line one part of which is a side of "
    "this loop, and its full extent is not this candidate's size. The "
    "reach is recorded because a loop whose sides are parts of long lines "
    "is a corner of built fabric rather than a discrete figure")


def derive_from_members(members, *, expect_centre_mm=None,
                        max_side_mm=None) -> dict:
    """Re-derive a candidate's closed footprint from its own member segments.

    `members` are dicts with `object_id`, `a` and `b`. The ring is found
    by polygonizing them - the same operation that proposed the loop in
    the first place, done again here so E1.4 owns the geometry it judges
    rather than inheriting a number.

    `expect_centre_mm` picks between faces when the members enclose more
    than one; without it, the largest face is taken and that is said.
    """
    pairs = [(m, (tuple(m["a"]), tuple(m["b"]))) for m in members or ()
             if m.get("a") is not None and m.get("b") is not None]
    segs = [seg for _m, seg in pairs]
    xs = [p[0] for seg in segs for p in seg]
    ys = [p[1] for seg in segs for p in seg]
    extents = ([round(min(xs), 3), round(min(ys), 3),
                round(max(xs), 3), round(max(ys), 3)] if xs else None)
    out = {
        "MEMBER_ENTITY_EXTENTS_BOX_MM": extents,
        "member_count": len(segs),
        "a_member_is_not_the_footprint": A_MEMBER_IS_NOT_THE_FOOTPRINT,
    }
    if len(segs) < 3:
        return {**out, "LOOP_RING": None,
                "LOOP_RING_ESTABLISHED": False,
                "why": "fewer than three member segments cannot close a loop"}
    try:
        from shapely.geometry import LineString, Point
        from shapely.ops import polygonize, unary_union
    except Exception:                                  # pragma: no cover
        return {**out, "LOOP_RING": None,
                "LOOP_RING_ESTABLISHED": False,
                "why": "no geometry library is available to close the loop"}
    faces = list(polygonize(unary_union(
        [LineString([a, b]) for a, b in segs])))
    if max_side_mm is not None:
        kept = []
        for f in faces:
            fx = [c[0] for c in f.exterior.coords]
            fy = [c[1] for c in f.exterior.coords]
            if max(max(fx) - min(fx), max(fy) - min(fy)) <= max_side_mm:
                kept.append(f)
        faces = kept or faces
    if not faces:
        return {**out, "LOOP_RING": None,
                "LOOP_RING_ESTABLISHED": False,
                "why": ("these members do not close a loop. Whatever "
                        "proposed this candidate, its own sides do not "
                        "enclose a footprint now")}
    if expect_centre_mm is not None and len(faces) > 1:
        want = Point(expect_centre_mm)
        faces.sort(key=lambda f: f.centroid.distance(want))
        picked, how = faces[0], "THE_FACE_NEAREST_THE_REPORTED_CENTRE"
    else:
        faces.sort(key=lambda f: -f.area)
        picked, how = faces[0], ("THE_ONLY_FACE_THESE_MEMBERS_CLOSE"
                                 if len(faces) == 1 else
                                 "THE_LARGEST_FACE_THESE_MEMBERS_CLOSE")
    ring = [(round(c[0], 3), round(c[1], 3)) for c in picked.exterior.coords]
    rx = [p[0] for p in ring]
    ry = [p[1] for p in ring]
    box = (min(rx), min(ry), max(rx), max(ry))
    beyond = []
    for m, (a, b) in pairs:
        reach = max(box[0] - min(a[0], b[0]), max(a[0], b[0]) - box[2],
                    box[1] - min(a[1], b[1]), max(a[1], b[1]) - box[3])
        if reach > MEMBER_REACH_TOLERANCE_MM:
            beyond.append({"object_id": m.get("object_id"),
                           "reaches_beyond_the_footprint_mm": round(reach, 3)})
    return {
        **out,
        "LOOP_RING": [list(p) for p in ring],
        "LOOP_RING_ESTABLISHED": True,
        "HOW_THE_FACE_WAS_CHOSEN": how,
        "faces_these_members_close": len(faces),
        "FOOTPRINT_BOX_FROM_THE_LOOPS_OWN_RING_MM": [round(v, 3)
                                                     for v in box],
        "MEMBERS_REACHING_BEYOND_THE_FOOTPRINT": beyond,
        "SIDES_OF_THIS_LOOP_ARE_PARTS_OF_LONGER_LINES": bool(beyond),
    }


def cross_check(derived, reported_size_mm) -> dict:
    """Do the derived footprint and the reported size describe one thing?"""
    if not derived.get("DERIVED"):
        return {"DERIVED_GEOMETRY_SELF_CONSISTENT": False,
                "why": derived.get("why", "no geometry was derived")}
    if not reported_size_mm or len(tuple(reported_size_mm)) != 2:
        return {
            "DERIVED_GEOMETRY_SELF_CONSISTENT": False,
            "reported_size_mm": None,
            "why": ("nothing was reported to cross-check the derived "
                    "footprint against, so self-consistency is not "
                    "established"),
        }
    rw, rh = (float(reported_size_mm[0]), float(reported_size_mm[1]))
    dw = derived["derived_bbox_width_mm"]
    dh = derived["derived_bbox_height_mm"]
    # a footprint may be reported in either order
    direct = (abs(dw - rw) <= SIZE_TOLERANCE_MM
              and abs(dh - rh) <= SIZE_TOLERANCE_MM)
    swapped = (abs(dw - rh) <= SIZE_TOLERANCE_MM
               and abs(dh - rw) <= SIZE_TOLERANCE_MM)
    ok = direct or swapped
    return {
        "DERIVED_GEOMETRY_SELF_CONSISTENT": bool(ok),
        "reported_size_mm": [rw, rh],
        "derived_size_mm": [dw, dh],
        "matched_in_reported_order": bool(direct),
        "matched_with_the_two_sides_swapped": bool(swapped and not direct),
        "worst_disagreement_mm": round(
            min(max(abs(dw - rw), abs(dh - rh)),
                max(abs(dw - rh), abs(dh - rw))), 3),
        "tolerance_mm": SIZE_TOLERANCE_MM,
        "why": ("the derived footprint and the reported size describe the "
                "same figure and agree" if ok else
                "the derived footprint and the reported size describe the "
                "same figure and do not agree. Nothing downstream can tell "
                "which is wrong, so the structural claim is withheld"),
    }


A_LOOP_MADE_OF_LONGER_LINES_IS_NOT_A_DISCRETE_MEMBER = (
    "the sides of this loop are parts of lines that carry on past it, so "
    "what closes here is a corner of the fabric those lines build and not "
    "a figure standing on its own. A discrete structural member is drawn "
    "as a figure; a rectangle formed where two long walls cross is a "
    "rectangle in the walls. It is kept, with its geometry, and it is not "
    "confirmed as a column")


def assess(candidate) -> dict:
    """One candidate's existence status, and why.

    `candidate` carries `loop` (the closed footprint), optionally
    `reported_size_mm`, and whatever evidence was gathered about it:
    `on_structural_layer`, `repeats_as_a_family`, `touches_a_wall`,
    `has_a_block_reference`, `resembles_another_loop`, and
    `sides_are_parts_of_longer_lines` from derive_from_members.
    """
    derived = derive_geometry(candidate.get("loop"))
    checked = cross_check(derived, candidate.get("reported_size_mm"))
    consistent = checked["DERIVED_GEOMETRY_SELF_CONSISTENT"]

    raising = [k for k in ("on_structural_layer", "repeats_as_a_family",
                           "touches_a_wall", "has_a_block_reference",
                           "resembles_another_loop")
               if candidate.get(k)]

    if candidate.get("sides_are_parts_of_longer_lines"):
        return {
            "COLUMN_EXISTENCE_STATUS": STRUCTURAL_COLUMN_UNRESOLVED,
            "DERIVED_GEOMETRY_SELF_CONSISTENT": consistent,
            "evidence_raising_it_as_structure": raising,
            "SIDES_OF_THIS_LOOP_ARE_PARTS_OF_LONGER_LINES": True,
            "layer_evidence_is_evidence_not_truth":
                LAYER_EVIDENCE_IS_EVIDENCE_NOT_TRUTH,
            "nothing_is_deleted": NOTHING_IS_DELETED,
            "why": A_LOOP_MADE_OF_LONGER_LINES_IS_NOT_A_DISCRETE_MEMBER,
            **derived,
            **{k: v for k, v in checked.items() if k != "why"},
            "self_consistency_why": checked.get("why"),
        }

    if not consistent:
        status = STRUCTURAL_COLUMN_UNRESOLVED
        why = ("its own geometry does not agree with what was reported "
               "about it, so what this figure is has not been established")
    elif not derived.get("footprint_is_compact"):
        status = STRUCTURAL_COLUMN_UNRESOLVED
        why = (f"the footprint is {derived['aspect_ratio']} times longer "
               "than it is wide. A figure that long may be a pier, a wall "
               "stub, a duct or a nosing, and the drawing has not "
               "established which")
    elif not raising:
        status = STRUCTURAL_COLUMN_UNRESOLVED
        why = ("the geometry is self-consistent and compact, and nothing "
               "in the drawing raises it as structure. A compact closed "
               "loop on its own is not a column")
    else:
        status = STRUCTURAL_COLUMN_CONFIRMED
        why = ("the geometry is self-consistent and compact, and the "
               "drawing raises it as structure: " + ", ".join(raising))

    return {
        "COLUMN_EXISTENCE_STATUS": status,
        "DERIVED_GEOMETRY_SELF_CONSISTENT": consistent,
        "evidence_raising_it_as_structure": raising,
        "layer_evidence_is_evidence_not_truth":
            LAYER_EVIDENCE_IS_EVIDENCE_NOT_TRUTH,
        "nothing_is_deleted": NOTHING_IS_DELETED,
        "why": why,
        **derived,
        **{k: v for k, v in checked.items() if k != "why"},
        "self_consistency_why": checked.get("why"),
    }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "EXISTENCE_STATUSES": list(EXISTENCE_STATUSES),
        "SIZE_TOLERANCE_MM": SIZE_TOLERANCE_MM,
        "COMPACT_ASPECT_LIMIT": COMPACT_ASPECT_LIMIT,
        "why": {
            "self_consistency_comes_first": WHY_SELF_CONSISTENCY_COMES_FIRST,
            "layer_evidence_is_evidence_not_truth":
                LAYER_EVIDENCE_IS_EVIDENCE_NOT_TRUTH,
            "nothing_is_deleted": NOTHING_IS_DELETED,
        },
    }
