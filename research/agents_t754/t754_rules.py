"""R-T754-1 .. -4 1.0.0 (every villa): exterior paint edge residuals in lm (OWNER RULE PAINT 2026-11-12,
UP-FIN-PAINT-002 1.0.0 reading B: door / window / corner edges are lm items, the area is the plaster area; R-T746-*,
R-T751-1 .. -4 unchanged and in force).

Physical element: one exposed arris (an external corner, the edge where a rendered face turns into an opening reveal,
or the edge of a slab-edge band) counted once in lm, decided from what the plan and the elevation draw.

R-T754-1 DOOR EDGE FROM THE DRAWN FRAME. Per external door: jambs and head are decided separately.
  - Jambs: the plan block's frame posts closed over the FULL wall depth with their outer edges at the drawn masonry
    jambs (T-746 census) -> the frame covers the jamb reveal: 0 lm. Posts drawn set back from the face by a printed /
    drawn depth s > 0 -> 2 x h. Posts off the masonry gap (POSITION CONFLICT) or no frame drawn -> HELD 0 .. 2 x h.
  - Head: a head member drawn (section / detail / elevation depth) over the full wall depth -> 0; drawn set back -> w;
    not drawn anywhere -> HELD 0 .. w with the missing drawing fact named. An elevation that shows the frame face
    only (no depth) does NOT decide the head: a face width is not a depth.
  - Missing h or w -> HELD blank, never 0. Units m; a size > 20 (mm read as m) or <= 0 is refused.
R-T754-2 SLAB-EDGE BAND ON THE ELEVATION. Under a 1F wall over open air, the slab edge is decided only from a vector
  view that sees it: a band drawn (two horizontals at printed / drawn levels) and FLUSH with the wall above -> one arris
  (the soffit edge) = the edge length; PROJECTING -> two arrises; drawn as ONE plane with no horizontal between the
  piece below and the wall above -> no slab-edge arris on that face (0, DRAWING-CONFIRMED by the absence over the
  measured span only); not visible on any vector view (hidden behind a front plane, raster sheet only) -> HELD blank
  with the cause, never 0.
R-T754-3 COPLANAR JUNCTION IS NOT A CORNER. A plan junction of two faces is a convex arris in a height band only when
  the elevation that sees both faces draws an edge line there. When the faces' true lengths sum to the projected
  length of their common top line (|diff| <= 0.001 m: every face parallel to the view plane) AND no vertical line
  crosses the band inside that span, the faces are one plane in that band: NOT_A_CORNER, 0 lm. Either test failing
  leaves the corner as it was.
R-T754-4 HOST BY THE FACE BAND. An arris part between two levels is hosted on the face whose band covers that interval
  at the arris (bottom <= lo and top >= hi); one such face -> its line; none -> NO_HOST (blank, never a neighbour);
  two or more on different lines -> AMBIGUOUS (held, both named).
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

RULE_IDS = ("R-T754-1", "R-T754-2", "R-T754-3", "R-T754-4")
VERSION = "1.0.0"
Q = Decimal("0.000001")
MAX_SIZE_M = Decimal("20")
TOL = Decimal("0.001")


class RuleError(ValueError):
    pass


def D(x):
    return Decimal(str(x))


def s6(x):
    return str(D(x).quantize(Q, rounding=ROUND_HALF_UP))


def _size(name, v):
    if v is None:
        return None
    v = D(v)
    if v <= 0 or v > MAX_SIZE_M:
        raise RuleError(f"{name} {v} m refused (<= 0, or millimetres read as metres)")
    return v


# R-T754-1 ------------------------------------------------------------------------------------------------------
JAMB_STATES = ("FULL_DEPTH_AT_JAMBS", "SET_BACK", "POSITION_CONFLICT", "NOT_DRAWN")
HEAD_STATES = ("FULL_DEPTH", "SET_BACK", "NOT_DRAWN")


def door_edges(w, h, jamb_state, head_state, missing_head_fact=None):
    """-> {'jambs': [lo, hi] | None, 'head': [lo, hi] | None, 'lm': [lo, hi] | None, 'state', 'missing'}."""
    if jamb_state not in JAMB_STATES or head_state not in HEAD_STATES:
        raise RuleError(f"unknown state {jamb_state} / {head_state}")
    w, h = _size("w", w), _size("h", h)
    missing = []
    if w is None or h is None:
        return {"jambs": None, "head": None, "lm": None, "state": "HELD_BLANK",
                "missing": ["opening size not printed"]}
    two_h = 2 * h
    jambs = {"FULL_DEPTH_AT_JAMBS": (D(0), D(0)), "SET_BACK": (two_h, two_h),
             "POSITION_CONFLICT": (D(0), two_h), "NOT_DRAWN": (D(0), two_h)}[jamb_state]
    if jamb_state == "POSITION_CONFLICT":
        missing.append("which frame stands in the masonry gap (block width vs wall gap)")
    if jamb_state == "NOT_DRAWN":
        missing.append("door frame on the plan")
    head = {"FULL_DEPTH": (D(0), D(0)), "SET_BACK": (w, w), "NOT_DRAWN": (D(0), w)}[head_state]
    if head_state == "NOT_DRAWN":
        if not missing_head_fact:
            raise RuleError("a head left open must name the drawing fact that is missing")
        missing.append(missing_head_fact)
    lo, hi = jambs[0] + head[0], jambs[1] + head[1]
    return {"jambs": [s6(jambs[0]), s6(jambs[1])], "head": [s6(head[0]), s6(head[1])], "lm": [s6(lo), s6(hi)],
            "state": "POINT" if lo == hi else "HELD_BOUND", "missing": missing}


# R-T754-2 ------------------------------------------------------------------------------------------------------
SLAB_VIEWS = ("BAND_FLUSH", "BAND_PROJECTING", "ONE_PLANE", "NOT_VISIBLE")


def slab_edge_arris(length, view, cause=None):
    """-> {'lm': [lo, hi] | None, 'state', 'cause'}; length in m of the edge portion."""
    if view not in SLAB_VIEWS:
        raise RuleError(f"unknown view {view}")
    L = _size("length", length)
    if view == "NOT_VISIBLE":
        if not cause:
            raise RuleError("a hidden slab edge must name why no vector view sees it")
        return {"lm": None, "state": "HELD_BLANK", "cause": cause}
    if L is None:
        return {"lm": None, "state": "HELD_BLANK", "cause": "edge length not measured"}
    n = {"BAND_FLUSH": 1, "BAND_PROJECTING": 2, "ONE_PLANE": 0}[view]
    return {"lm": [s6(n * L), s6(n * L)], "state": "DRAWING-CONFIRMED", "cause": cause}


# R-T754-3 ------------------------------------------------------------------------------------------------------
def coplanar_junction(true_lengths, projected_dx, verticals_inside):
    """true_lengths: the faces' plan lengths along the top line; projected_dx: that line's length in the elevation;
    verticals_inside: handles of vertical lines crossing the band strictly inside the span between the two junction
    positions being tested. -> 'NOT_A_CORNER' | 'CORNER_STANDS'."""
    if not true_lengths or projected_dx is None:
        raise RuleError("lengths and the projected top line are required")
    tot = sum(_size("face", x) for x in true_lengths)
    if abs(tot - D(projected_dx)) <= TOL and not verticals_inside:
        return "NOT_A_CORNER"
    return "CORNER_STANDS"


# R-T754-4 ------------------------------------------------------------------------------------------------------
def host_by_band(lo, hi, faces):
    """faces: [(face_id, line, bottom, top)] meeting at the arris. -> (state, [face ids], line | None)."""
    lo, hi = D(lo), D(hi)
    if hi <= lo:
        raise RuleError("an arris part needs top > bottom")
    cover = [(f, ln) for f, ln, b, t in faces if b is not None and t is not None and D(b) <= lo and D(t) >= hi]
    if not cover:
        return "NO_HOST", [], None
    lines = sorted({ln for _, ln in cover})
    if len(lines) > 1:
        return "AMBIGUOUS", [f for f, _ in cover], None
    return "HOSTED", [f for f, _ in cover], lines[0]


def sum_bounds(items):
    lo = sum((D(x[0]) for x in items), D(0))
    hi = sum((D(x[1]) for x in items), D(0))
    return [s6(lo), s6(hi)]
