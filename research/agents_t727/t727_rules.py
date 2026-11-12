"""T-727 rules (research, unwired; every villa): deductions over a VOID are the UNION of the named pieces, one ceiling
face has one line, and a deduction check reads the list the net was computed from.

Physical element (ERS 2.1). Inside a slab opening (light well, stair well, shaft) of an upper storey nothing is floor:
the opening is one physical area. The pieces that name it (the void window, the flights seen through it, the cells
between them) are labels on that one area; where two labels overlap (two flight footprints meeting on a 0.05 m nosing
strip) the area is still built once. Above a double-height volume one ceiling closes it, at the top; it belongs to the
ceiling face of the storey whose roof / slab closes the volume.

R-T727-1 UNION, NOT SUM. The deduction of a floor (or ceiling) face inside a void outline is the area of the UNION of
         the named pieces inside the face. Pieces are stated as union increments in a fixed order (each piece less every
         earlier piece), so their sum equals the union; a piece's own full area is never added beside an overlapping one.
         A check that finds sum(pieces) - union > TOL names the overlap (pieces, m2) and the line is DEDUCTED_TWICE only if
         the line's NET was computed from that sum (R-T727-3).
R-T727-2 ONE FACE, ONE LINE. A ceiling (or floor) area belongs to exactly one line: the line whose face geometry
         contains it at the level where it is built (the top of a double-height volume = the ceiling face of the storey
         whose slab / roof closes it, when the plan above draws no opening there). Any other line naming the same m2 is
         EXCLUDED with cause DUPLICATE_FACE and the owner's id: blank, never valued, never 0 by omission of the owner.
         A ceiling face in two valued lines is DEDUCTED_TWICE (here: counted twice); one valued + one blank is
         DOUBLE_COUNT_RISK until the blank one is EXCLUDED by this rule.
R-T727-3 PROVENANCE OF THE CHECK. A deduction check is valid only against the deduction list the line's net was computed
         from (the piece record that set measured_net), never against a superseded base list carried on the same line:
         face - (pieces of that record) - (later named deductions) must re-add to measured_net within TOL before the
         record is used. A base list that disagrees is ENGINE_LIST_STALE (a list defect), not a quantity defect.
R-T727-4 NO OUTLINE STAYS HELD. A void without a drawn opening outline (a dome drawn 'above', a word without a closed
         outline) deducts nothing and values nothing: HELD with its cause, never 0, never a default size (R-T719-5).
"""
from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

D = Decimal
TOL_M2 = D("0.005")          # as R-T719 (half a 0.10 x 0.10 tile: below the drawing precision of an outline)


def q6(x):
    return D(str(x)).quantize(D("0.000001"), rounding=ROUND_HALF_EVEN)


def union_increments(pieces):
    """R-T727-1 on shapely geometries. pieces: [(name, geometry)] in a fixed order. Returns ([(name, increment area)],
    union area, sum of full areas) in the geometry's units squared. Each increment = piece less every earlier piece."""
    from shapely.ops import unary_union
    out, seen, tot = [], None, 0.0
    for name, g in pieces:
        tot += g.area
        inc = g if seen is None else g.difference(seen)
        out.append((name, inc.area))
        seen = g if seen is None else unary_union([seen, g])
    return out, (seen.area if seen is not None else 0.0), tot


def overlap_named(pieces_full_m2, union_m2, tol=TOL_M2):
    """sum of full piece areas - union (>= 0) and whether it exceeds tol (a DEDUCTED_TWICE cause if the net used the sum)."""
    ex = q6(sum((q6(p) for p in pieces_full_m2), D(0)) - q6(union_m2))
    return ex, ex > tol


def deduction_check(face_in_outline_m2, deductions, tol=TOL_M2):
    """R-T719-2 restated for R-T727-1: (result, residual) with residual = face - sum(deductions).
    deductions are the UNION increments the net used. None face -> VOID_EXTENT_UNRESOLVED (HELD)."""
    if face_in_outline_m2 is None:
        return "VOID_EXTENT_UNRESOLVED", None
    face = q6(face_in_outline_m2)
    if face == 0:
        return "EXTERIOR", q6(0)
    r = face - sum((q6(m) for _, m in deductions), D(0))
    if abs(r) <= tol:
        return "DEDUCTED_ONCE", q6(r)
    return ("NOT_DEDUCTED" if r > 0 else "DEDUCTED_TWICE"), q6(r)


def net_provenance(face_m2, record_rows, later_rows, measured_net, tol=TOL_M2):
    """R-T727-3: the record re-adds to the line's net? -> ('RECORD_OF_NET' | 'NOT_THE_NET_RECORD', residual)."""
    r = q6(face_m2) - sum((q6(m) for _, m in record_rows), D(0)) - sum((q6(m) for _, m in later_rows), D(0)) \
        - q6(measured_net)
    return ("RECORD_OF_NET" if abs(r) <= tol else "NOT_THE_NET_RECORD"), q6(r)


def face_owner(area_id, lines):
    """R-T727-2. lines: [{'line_id', 'face_contains': bool, 'value': number or None}] that name area_id.
    Returns {'owner': id or None, 'excluded': [(id, cause)], 'result': ...}. Exactly one containing line owns it."""
    owners = [ln for ln in lines if ln["face_contains"]]
    if len(owners) != 1:
        return {"owner": None, "excluded": [], "result": "OWNER_UNRESOLVED" if owners else "NOT_CARRIED",
                "area": area_id}
    own = owners[0]
    others = [ln for ln in lines if ln is not own]
    valued_others = [ln for ln in others if ln.get("value") is not None]
    if valued_others:
        result = "DEDUCTED_TWICE" if own.get("value") is not None else "OWNER_BLANK_OTHER_VALUED"
    else:
        result = "ONCE"
    return {"owner": own["line_id"], "area": area_id, "result": result,
            "excluded": [(ln["line_id"], f"DUPLICATE_FACE of {own['line_id']}") for ln in others]}


def held_void(vid, cause):
    """R-T727-4: a void with no drawn outline."""
    return {"void": vid, "status": "HELD", "result": "VOID_EXTENT_UNRESOLVED", "m2": None, "cause": cause,
            "deducted_from": []}
