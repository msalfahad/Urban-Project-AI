"""E1.3 §7, §8, §10 — existing is not the same as showing.

A structural column can be entirely real and still have nothing to do
with the shape of the room it stands in. If the architect's wall face
runs straight past it, the column is inside or behind the wall; the
plasterer never sees it and the room's clear internal face is the
architectural line. E1.2 did not make that distinction, so Driver's
lower corner was cut away by a column outline on S-COL.BON although the
architectural face runs straight across that location.

Three questions, kept apart because they have different answers and
different evidence:

    does this column EXIST                  -> COLUMN_EXISTENCE_STATUS
    is it EXPOSED into the room             -> EXPOSED_TO_ROOM_STATUS
    does it own the room's CLEAR FACE       -> CLEAR_FACE_OWNERSHIP_STATUS

Nothing here deletes a column. Both geometries are kept; what changes is
which of them the room's measurement boundary follows.
"""

from __future__ import annotations

import hashlib
import math

MODEL = "A_COLUMN_MAY_EXIST_WITHOUT_OWNING_THE_ROOM_FACE_V1"

# ------------------------------------------------------- existence status
STRUCTURAL_COLUMN_CONFIRMED = "STRUCTURAL_COLUMN_CONFIRMED"
COLUMN_CANDIDATE_UNRESOLVED = "COLUMN_CANDIDATE_UNRESOLVED"
NOT_A_COLUMN = "NOT_A_COLUMN"
EXISTENCE_STATUSES = (STRUCTURAL_COLUMN_CONFIRMED,
                      COLUMN_CANDIDATE_UNRESOLVED, NOT_A_COLUMN)

# -------------------------------------------------------- exposure status
EXPOSED_TO_ROOM = "EXPOSED_TO_ROOM"
NOT_EXPOSED_TO_ROOM = "NOT_EXPOSED_TO_ROOM"
EXPOSURE_UNRESOLVED = "EXPOSURE_UNRESOLVED"
EXPOSURE_STATUSES = (EXPOSED_TO_ROOM, NOT_EXPOSED_TO_ROOM,
                     EXPOSURE_UNRESOLVED)

# ------------------------------------------------------- ownership status
ARCHITECTURAL_FACE_OWNS = "ARCHITECTURAL_FACE_OWNS_THE_CLEAR_BOUNDARY"
COLUMN_FACE_OWNS = "COLUMN_FACE_OWNS_THE_CLEAR_BOUNDARY"
CLEAR_FACE_OWNERSHIP_UNRESOLVED = "CLEAR_FACE_OWNERSHIP_UNRESOLVED"
OWNERSHIP_STATUSES = (ARCHITECTURAL_FACE_OWNS, COLUMN_FACE_OWNS,
                      CLEAR_FACE_OWNERSHIP_UNRESOLVED)

STRUCTURAL_OBJECT_BEHIND_FINISH_FACE = "STRUCTURAL_OBJECT_BEHIND_FINISH_FACE"

# ------------------------------------------------------ exposure evidence
EV_ARCH_FACE_TERMINATES_AT_THE_COLUMN = (
    "THE_ARCHITECTURAL_WALL_FACE_VISIBLY_TERMINATES_AT_THE_COLUMN")
EV_ARCH_FINISH_WRAPS_THE_COLUMN = (
    "THE_ARCHITECTURAL_FINISH_LINE_WRAPS_THE_COLUMN")
EV_PROTRUDES_BEYOND_THE_FINISH_FACE = (
    "THE_COLUMN_PROTRUDES_BEYOND_THE_FINISHED_WALL_FACE")
EV_RASTER_SHOWS_THE_PROTRUSION = (
    "THE_SOURCE_RASTER_VISIBLY_SHOWS_THE_PROTRUSION")
EV_ARCH_LAYER_DRAWS_THE_RETURN = (
    "AN_ARCHITECTURAL_LAYER_EXPLICITLY_DRAWS_THE_EXPOSED_RETURN")
EV_VISUAL_SEES_THE_COLUMN_IN_THE_ROOM = (
    "THE_COLD_SOURCE_ONLY_PASS_READ_A_COLUMN_STANDING_IN_THIS_ROOM")

EXPOSURE_EVIDENCE = (
    EV_ARCH_FACE_TERMINATES_AT_THE_COLUMN,
    EV_ARCH_FINISH_WRAPS_THE_COLUMN,
    EV_PROTRUDES_BEYOND_THE_FINISH_FACE,
    EV_RASTER_SHOWS_THE_PROTRUSION,
    EV_ARCH_LAYER_DRAWS_THE_RETURN,
    EV_VISUAL_SEES_THE_COLUMN_IN_THE_ROOM,
)

# The one observation that settles NON-exposure on its own: the finish
# face does not deviate, so there is nothing of the column in the room.
EV_ARCH_FACE_CONTINUES_STRAIGHT_ACROSS = (
    "AN_ARCHITECTURAL_WALL_FACE_CONTINUES_STRAIGHT_ACROSS_THE_COLUMN")

# ------------------------------------------------------------------- prose
EXISTENCE_IS_NOT_OWNERSHIP = (
    "a column that exists inside a wall is a fact about the structure and "
    "not a fact about the room. The room's clear internal face is what a "
    "finishing trade meets, and it meets plaster, not the pier behind it")

NEITHER_STATUS_MAY_DEFORM_A_ROOM_WITHOUT_EXPOSURE = (
    "an unresolved column and a confirmed but unexposed column have the "
    "same effect on the room boundary: none. Exposure is the evidence that "
    "licenses a structural outline to cut into a room, and without it the "
    "architectural face stands")

BOTH_GEOMETRIES_ARE_KEPT = (
    "nothing is deleted. The structural outline stays in the register with "
    "its own identity and its own evidence; what this module decides is "
    "which geometry the room's clear internal boundary follows")

A_TOUCHED_WALL_IS_NOT_A_STRUCTURE = (
    "a boxed riser, a wardrobe, a cabinet run and a service enclosure all "
    "meet established wall faces. Contact with a wall says where a thing "
    "is, not what it is made of")


def model_hash() -> str:
    parts = ([MODEL] + list(EXISTENCE_STATUSES) + list(EXPOSURE_STATUSES)
             + list(OWNERSHIP_STATUSES) + list(EXPOSURE_EVIDENCE)
             + [EV_ARCH_FACE_CONTINUES_STRAIGHT_ACROSS])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------------- geometry
def _line_of(seg, *, tol_deg=2.0):
    """(unit direction, signed offset) of the infinite line a face lies on."""
    (ax, ay), (bx, by) = seg
    dx, dy = bx - ax, by - ay
    n = math.hypot(dx, dy)
    if n <= 0:
        return None
    ux, uy = dx / n, dy / n
    if (ux, uy) < (0.0, 0.0):
        ux, uy = -ux, -uy
    # signed distance from the origin to the line, along its normal
    off = -uy * ax + ux * ay
    return (ux, uy, off)


def _same_line(la, lb, *, angle_tol_deg=2.0, offset_tol_mm=2.0) -> bool:
    if la is None or lb is None:
        return False
    dot = abs(la[0] * lb[0] + la[1] * lb[1])
    if dot < math.cos(math.radians(angle_tol_deg)):
        return False
    return abs(la[2] - lb[2]) <= offset_tol_mm


def _t_along(line, pt) -> float:
    return line[0] * pt[0] + line[1] * pt[1]


def architectural_face_continues_across(column_box, architectural_faces,
                                        *, pad_mm=1.0, angle_tol_deg=2.0,
                                        offset_tol_mm=2.0) -> dict:
    """§8: does an architectural face run straight past this column?

    The test is made against COLLINEAR RUNS, not single entities. A wall
    face in CAD is cut into intervals at every intersection, so each piece
    of it STOPS at the column it passes; asking whether one piece spans
    the footprint would answer no for every column ever drawn inside a
    wall. What continuing across means is that the same infinite line
    carries architectural material on BOTH sides of the footprint.

    `architectural_faces` are ((x1,y1),(x2,y2)) pairs of ESTABLISHED
    architectural material faces - never structural-layer geometry, which
    is the thing being tested.
    """
    x0, y0, x1, y1 = column_box
    x0, y0 = x0 - pad_mm, y0 - pad_mm
    x1, y1 = x1 + pad_mm, y1 + pad_mm
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    half = max(x1 - x0, y1 - y0) / 2.0

    # the lines that pass through the footprint at all
    by_line = {}
    for i, seg in enumerate(architectural_faces or ()):
        ln = _line_of(seg)
        if ln is None:
            continue
        # distance from the footprint centre to this infinite line
        d = abs(-ln[1] * cx + ln[0] * cy - ln[2])
        if d > half:
            continue
        key = None
        for k in by_line:
            if _same_line(k, ln, angle_tol_deg=angle_tol_deg,
                          offset_tol_mm=offset_tol_mm):
                key = k
                break
        by_line.setdefault(key or ln, []).append((i, seg, ln))

    lo_t = _t_along((1.0, 0.0, 0.0), (x0, y0))
    for ln, members in by_line.items():
        t_lo = _t_along(ln, (x0, y0))
        t_hi = _t_along(ln, (x1, y1))
        for corner in ((x0, y1), (x1, y0)):
            t = _t_along(ln, corner)
            t_lo, t_hi = min(t_lo, t), max(t_hi, t)
        before, after = [], []
        for (i, seg, _l) in members:
            ta, tb = _t_along(ln, seg[0]), _t_along(ln, seg[1])
            if max(ta, tb) <= t_lo + pad_mm:
                before.append(i)
            elif min(ta, tb) >= t_hi - pad_mm:
                after.append(i)
        if before and after:
            return {
                "continues_across": True,
                "architectural_faces_before_the_footprint": sorted(before)[:6],
                "architectural_faces_after_the_footprint": sorted(after)[:6],
                "why": ("the same architectural line carries material on "
                        "both sides of this footprint, so the finish runs "
                        "past the column and the column is behind it"),
            }
    return {
        "continues_across": False,
        "architectural_faces_before_the_footprint": [],
        "architectural_faces_after_the_footprint": [],
        "why": ("no architectural line was found carrying material on both "
                "sides of this footprint"),
    }


def existence(*, column_evidence=(), structural_in_kind=(),
              evidence_required=2) -> dict:
    """Is this a structural column, or only a loop the size of one?"""
    ev = sorted(set(column_evidence or ()))
    sik = sorted(set(structural_in_kind or ()) & set(ev))
    ok = len(ev) >= evidence_required and bool(sik)
    return {
        "COLUMN_EXISTENCE_STATUS": (STRUCTURAL_COLUMN_CONFIRMED if ok
                                    else COLUMN_CANDIDATE_UNRESOLVED),
        "evidence": ev,
        "evidence_that_is_structural_in_kind": sik,
        "evidence_required": evidence_required,
        "a_touched_wall_is_not_a_structure": A_TOUCHED_WALL_IS_NOT_A_STRUCTURE,
    }


def exposure(*, exposure_evidence=(),
             architectural_face_continues=None) -> dict:
    """Is any of it in the room?"""
    ev = sorted({e for e in (exposure_evidence or ())
                 if e in EXPOSURE_EVIDENCE})
    if architectural_face_continues and not ev:
        status = NOT_EXPOSED_TO_ROOM
        why = ("an architectural wall face continues straight across this "
               "column and nothing shows any part of it in the room")
    elif ev:
        status = EXPOSED_TO_ROOM
        why = "evidence places part of this column in the room: " + \
              ", ".join(ev)
        if architectural_face_continues:
            why += (". An architectural face also runs across it, so the "
                    "two readings disagree and the exposure evidence is "
                    "what carries the decision")
    else:
        status = EXPOSURE_UNRESOLVED
        why = ("nothing establishes whether any part of this column shows "
               "in the room, and nothing establishes that it does not")
    return {
        "EXPOSED_TO_ROOM_STATUS": status,
        "exposure_evidence": ev,
        "architectural_face_continues_across": bool(
            architectural_face_continues),
        "why": why,
    }


def clear_face_ownership(*, existence_status, exposure_status,
                         architectural_face_present) -> dict:
    """Which geometry does the room's clear internal boundary follow?"""
    if (existence_status == STRUCTURAL_COLUMN_CONFIRMED
            and exposure_status == EXPOSED_TO_ROOM):
        status = COLUMN_FACE_OWNS
        why = ("the column is established and established as exposed, so "
               "the room's clear face meets it")
    elif architectural_face_present:
        status = ARCHITECTURAL_FACE_OWNS
        why = ("an architectural face is present at this location and "
               "exposure is not established, so the clear internal "
               "boundary is the architectural face and the structural "
               "outline stays behind it")
    else:
        status = CLEAR_FACE_OWNERSHIP_UNRESOLVED
        why = ("no architectural face was established at this location and "
               "the column's exposure was not established either, so what "
               "the room's clear face follows here is not settled. It is "
               "not silently the structural outline")
    return {
        "CLEAR_FACE_OWNERSHIP_STATUS": status,
        "structural_object_relation": (
            STRUCTURAL_OBJECT_BEHIND_FINISH_FACE
            if status == ARCHITECTURAL_FACE_OWNS
            and existence_status == STRUCTURAL_COLUMN_CONFIRMED else None),
        "may_deform_the_clear_internal_boundary": status == COLUMN_FACE_OWNS,
        "why": why,
        "neither_status_may_deform_a_room_without_exposure":
            NEITHER_STATUS_MAY_DEFORM_A_ROOM_WITHOUT_EXPOSURE,
        "both_geometries_are_kept": BOTH_GEOMETRIES_ARE_KEPT,
    }


def assess(*, column_evidence=(), structural_in_kind=(), evidence_required=2,
           exposure_evidence=(), architectural_face_continues=None,
           architectural_face_present=None) -> dict:
    """The three questions, answered in order, in one record."""
    ex = existence(column_evidence=column_evidence,
                   structural_in_kind=structural_in_kind,
                   evidence_required=evidence_required)
    xp = exposure(exposure_evidence=exposure_evidence,
                  architectural_face_continues=architectural_face_continues)
    if architectural_face_present is None:
        architectural_face_present = bool(architectural_face_continues)
    ow = clear_face_ownership(
        existence_status=ex["COLUMN_EXISTENCE_STATUS"],
        exposure_status=xp["EXPOSED_TO_ROOM_STATUS"],
        architectural_face_present=architectural_face_present)
    return {"EXISTENCE": ex, "EXPOSURE": xp, "CLEAR_FACE_OWNERSHIP": ow,
            "existence_is_not_ownership": EXISTENCE_IS_NOT_OWNERSHIP}


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "EXISTENCE_STATUSES": list(EXISTENCE_STATUSES),
        "EXPOSURE_STATUSES": list(EXPOSURE_STATUSES),
        "OWNERSHIP_STATUSES": list(OWNERSHIP_STATUSES),
        "EXPOSURE_EVIDENCE": list(EXPOSURE_EVIDENCE),
        "EV_ARCH_FACE_CONTINUES_STRAIGHT_ACROSS":
            EV_ARCH_FACE_CONTINUES_STRAIGHT_ACROSS,
        "STRUCTURAL_OBJECT_BEHIND_FINISH_FACE":
            STRUCTURAL_OBJECT_BEHIND_FINISH_FACE,
        "why": {
            "existence_is_not_ownership": EXISTENCE_IS_NOT_OWNERSHIP,
            "neither_status_may_deform_a_room_without_exposure":
                NEITHER_STATUS_MAY_DEFORM_A_ROOM_WITHOUT_EXPOSURE,
            "both_geometries_are_kept": BOTH_GEOMETRIES_ARE_KEPT,
            "a_touched_wall_is_not_a_structure":
                A_TOUCHED_WALL_IS_NOT_A_STRUCTURE,
        },
    }
