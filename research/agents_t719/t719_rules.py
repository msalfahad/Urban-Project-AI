"""T-719 rules (research, unwired; every villa): the VOID REGISTER, one source for floor / ceiling deductions and the
double-height wall bands (R-T709-1).

Physical element (ERS 2.1). A VOID is a drawn opening through a floor slab: a light well / double-height space, a stair
well, a lift or service shaft, a dome / skylight opening. It has an outline (closed by drawn handles) on the plan of the
slab it pierces, and it spans from the floor of the storey below to the soffit above the opening's top.

R-T719-1 PLACEMENT. A void belongs to the plan of the slab it pierces (the UPPER storey). On that storey no floor finish
         exists inside the outline. On the storey below it is DOUBLE HEIGHT: no ceiling at that storey's own level inside
         the projected outline; the ceiling over the double-height volume is the one at the top, carried once. A stair
         well is a void on the upper floor only: the flights rising from the lower floor are stair finish counted on the
         lower floor, never a void of the lower floor.
R-T719-2 FLOOR ONCE. Inside the outline, the named floor deductions of the storey's floor-finish line(s) sum to the face
         area inside the outline (tolerance TOL_M2). Less -> NOT_DEDUCTED (the line still carries floor where none is
         built); more -> DEDUCTED_TWICE (two named deductions cover the same m2, e.g. two flight footprints summed where
         they overlap). Each named deduction is checked against the area of its own geometry inside the outline.
R-T719-3 CEILING ONCE. On the storey below, the ceiling deductions inside the projected outline sum to the face area
         inside it (same test). Above the void, one ceiling line carries the top; a second line naming the same m2 (for
         example a 'ceiling over void' line beside a group line that already holds it) is DOUBLE_COUNT_RISK while either
         is blank, DEDUCTED_TWICE once both are valued.
R-T719-4 OUTSIDE. A void whose outline meets no internal face carries no internal floor / ceiling line: EXTERIOR, named
         for the exterior lines it touches (slab top, soffit, edge); never 0 by omission, never in an internal line.
R-T719-5 NO OUTLINE. A void word or symbol without a closed outline is VOID_EXTENT_UNRESOLVED: HELD, nothing deducted,
         nothing guessed (never 0, never a default size).

Statuses (WORKFLOW_CONTROLS s.5): DRAWING-CONFIRMED (outline closed by handles), HELD, UNKNOWN; check results:
DEDUCTED_ONCE, NOT_DEDUCTED, DEDUCTED_TWICE, DOUBLE_COUNT_RISK, EXTERIOR, VOID_EXTENT_UNRESOLVED.
"""
from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

TOL_M2 = Decimal("0.005")          # half a 0.10 x 0.10 tile: below drawing precision of an outline
D = Decimal


def q6(x):
    return D(str(x)).quantize(D("0.000001"), rounding=ROUND_HALF_EVEN)


def shoelace(pts):
    """plan area of a closed polygon (list of (x, y) in metres), sign-free."""
    s = D(0)
    n = len(pts)
    for i in range(n):
        x1, y1 = (D(str(v)) for v in pts[i])
        x2, y2 = (D(str(v)) for v in pts[(i + 1) % n])
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def placement(void):
    """R-T719-1: (floor without floor finish, storey that is double height) for a void record
    {'pierces': <upper storey>, 'below': <storey below or None>, 'kind': ...}."""
    if not void.get("pierces"):
        raise ValueError("a void needs the slab it pierces (the upper storey)")
    return void["pierces"], void.get("below")


def floor_check(face_in_outline_m2, deductions, tol=TOL_M2):
    """R-T719-2 / -3. deductions: [(name, m2 inside the outline)] as the line states them. Returns (result, residual)
    with residual = face - sum (positive = carried, negative = deducted twice)."""
    if face_in_outline_m2 is None:
        return "VOID_EXTENT_UNRESOLVED", None
    face = q6(face_in_outline_m2)
    tot = sum((q6(m) for _, m in deductions), D(0))
    r = face - tot
    if face == 0:
        return "EXTERIOR", q6(0)
    if abs(r) <= tol:
        return "DEDUCTED_ONCE", q6(r)
    return ("NOT_DEDUCTED" if r > 0 else "DEDUCTED_TWICE"), q6(r)


def overlap_excess(pieces_m2, union_m2, tol=TOL_M2):
    """two named pieces summed where they overlap: sum - union (>= 0). Above tol it is a DEDUCTED_TWICE cause."""
    ex = sum((q6(p) for p in pieces_m2), D(0)) - q6(union_m2)
    return q6(ex), ex > tol


def ceiling_top_lines(lines_on_same_m2):
    """R-T719-3: the lines that carry the ceiling over one double-height area. lines: [(line id, value or None)]."""
    n = len(lines_on_same_m2)
    if n == 0:
        return "NOT_DEDUCTED"            # no ceiling over the void at all: an omission, named
    if n == 1:
        return "DEDUCTED_ONCE"
    if all(v is not None for _, v in lines_on_same_m2):
        return "DEDUCTED_TWICE"
    return "DOUBLE_COUNT_RISK"


def register_row(vid, pierces, below, outline_m2, evidence, lines, status=None):
    """one register row; outline_m2 None -> VOID_EXTENT_UNRESOLVED (R-T719-5), HELD, never 0."""
    if outline_m2 is None:
        return {"void": vid, "pierces": pierces, "below": below, "outline_m2": None, "status": "HELD",
                "result": "VOID_EXTENT_UNRESOLVED", "evidence": evidence, "lines": lines}
    return {"void": vid, "pierces": pierces, "below": below, "outline_m2": str(q6(outline_m2)),
            "status": status or "DRAWING-CONFIRMED", "evidence": evidence, "lines": lines}
