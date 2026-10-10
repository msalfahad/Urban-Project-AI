"""LINTEL RELEASE AUDIT - whether a released lintel's bearing, end supports and measurement have authority (generic).

A lintel detail states a minimum bearing on masonry at each end. Whether that bearing physically exists is read from
the drawn wall beyond each jamb, never assumed from the opening having a schedule row.

    bearing_reach(face_a, face_b, crossings, columns, cap, junction_max)
        1-D evidence along the wall centreline, measured outward from one jamb (mm):
          face_a, face_b   intervals [(x0, x1)] where each wall face is drawn
          crossings        [(x, beyond_a, beyond_b)]: a line crossing the wall strip at x; beyond_* tells whether it
                           runs on past that face (a cross wall's far face) or stops at it (a cap)
          columns          [(x0, x1)] where an RC column outline occupies the strip
        Masonry runs while either face is drawn; a hole in BOTH faces no longer than junction_max with both faces
        resuming after it is a wall crossing (masonry). Where the faces stop, a crossing line within one cross-wall
        thickness beyond is the far face of the wall they run into (masonry up to it): T_JUNCTION when it runs past
        both faces, L_CORNER when past one. Faces that stop where an oblique wall line meets them end at an
        OBLIQUE_JUNCTION (the masonry beyond is not read on this axis: not verified, never assumed). A column ends
        the masonry at its face (COLUMN). Returns {available, terminator, at}. Nothing is extended, snapped or
        invented.
    classify_end(available, terminator, min_bearing, column_connection)
        MASONRY_OK when available >= min_bearing; COLUMN_CONNECTION_MISSING when a column ends a shorter masonry run
        and no connection detail is stated; BEARING_NOT_VERIFIED at an oblique junction; BEARING_SHORT otherwise.
    classify_lintel(ends)
        RELEASE_AUTHORITY_CONFIRMED / BLOCKED_COLUMN_CONNECTION / BLOCKED_BEARING_REQUIREMENT (a short masonry
        bearing outranks a missing column connection: either blocks).
    stirrup_counts(length, rate_per_m, clear_span)
        the readings of an 'n/M' stirrup rate: EQUIVALENT_RATE (n x L, not an integer), RATE_COUNT ceil(n x L),
        SPACING_WITH_ENDS ceil(L / s) + 1, CLEAR_SPAN_RATE ceil(n x W). None of them is a stated layout.
    assign_overlap(a, b, released)
        one shared volume, one owner: the earlier released object in (a, b); none when neither is released.

Stdlib only. No project data.
"""

from __future__ import annotations

import math

TOL = 1e-6
REACH, T_JUNCTION, L_CORNER, WALL_END, COLUMN = "REACH", "T_JUNCTION", "L_CORNER", "WALL_END", "COLUMN"
OBLIQUE_JUNCTION = "OBLIQUE_JUNCTION"
BEARING_NOT_VERIFIED = "BEARING_NOT_VERIFIED"
MASONRY_OK, BEARING_SHORT, COLUMN_CONNECTION_MISSING = "MASONRY_OK", "BEARING_SHORT", "COLUMN_CONNECTION_MISSING"
CONFIRMED = "RELEASE_AUTHORITY_CONFIRMED"
BLOCKED_BEARING = "BLOCKED_BEARING_REQUIREMENT"
BLOCKED_COLUMN = "BLOCKED_COLUMN_CONNECTION"
SOURCE_CONFLICT = "SOURCE_CONFLICT"


class LintelAuditError(ValueError):
    pass


def _union(iv, tol=2.0):
    out = []
    for a, b in sorted((min(a, b), max(a, b)) for a, b in iv):
        if out and a <= out[-1][1] + tol:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def _covered_from(iv, x, tol=2.0):
    """end of the coverage that contains x (or starts within tol of it); None if x is not covered."""
    for a, b in _union(iv, tol):
        if a - tol <= x <= b + tol:
            return b
    return None


def bearing_reach(face_a, face_b, crossings=(), columns=(), cap=2000.0, junction_max=250.0, cross_max=400.0,
                  oblique_at=()):
    if cap <= 0:
        raise LintelAuditError("cap must be positive")
    both = _union(list(face_a) + list(face_b))
    pos = _covered_from(both, 0.0)
    if pos is None:
        pos = 0.0
    while pos < cap:
        nxt = [a for a, b in both if a > pos + TOL]
        if not nxt:
            break
        ns = min(nxt)
        resume_a = _covered_from(face_a, ns) is not None
        resume_b = _covered_from(face_b, ns) is not None
        if ns - pos <= junction_max and resume_a and resume_b and not any(pos - TOL <= x <= ns + TOL
                                                                          for x, _, _ in crossings):
            pos = _covered_from(both, ns)
            continue
        break
    term, at = (REACH, cap) if pos >= cap else (WALL_END, pos)
    if pos < cap:
        far = sorted((x, ba, bb) for x, ba, bb in crossings if pos - TOL <= x <= pos + cross_max and (ba or bb))
        if far:
            x, ba, bb = far[0]                     # the nearest far face of the wall the faces run into
            pos = max(pos, x)
            term, at = (T_JUNCTION if (ba and bb) else L_CORNER), x
        elif any(abs(x - pos) <= 5.0 for x in oblique_at):
            term, at = OBLIQUE_JUNCTION, pos
    for c0, c1 in sorted(columns):
        if c1 > TOL and c0 < pos - TOL:
            pos = max(0.0, c0)
            term, at = COLUMN, c0
            break
    return {"available": min(pos, cap), "terminator": term, "at": at}


def classify_end(available, terminator, min_bearing, column_connection=False):
    if min_bearing <= 0:
        raise LintelAuditError("min bearing must be positive")
    if available >= min_bearing - TOL:
        return MASONRY_OK
    if terminator == COLUMN and not column_connection:
        return COLUMN_CONNECTION_MISSING
    if terminator == OBLIQUE_JUNCTION:
        return BEARING_NOT_VERIFIED
    return BEARING_SHORT


def classify_lintel(ends):
    ends = list(ends)
    if not ends:
        raise LintelAuditError("no ends")
    if BEARING_SHORT in ends or BEARING_NOT_VERIFIED in ends:
        return BLOCKED_BEARING
    if COLUMN_CONNECTION_MISSING in ends:
        return BLOCKED_COLUMN
    if all(e == MASONRY_OK for e in ends):
        return CONFIRMED
    raise LintelAuditError(f"unknown end states {ends}")


def stirrup_counts(length, rate_per_m, clear_span=None):
    if length <= 0 or rate_per_m <= 0:
        raise LintelAuditError("length and rate must be positive")
    s = 1000.0 / rate_per_m
    out = {"EQUIVALENT_RATE": rate_per_m * length / 1000.0,
           "RATE_COUNT": int(math.ceil(rate_per_m * length / 1000.0 - 1e-9)),
           "SPACING_WITH_ENDS": int(math.ceil(length / s - 1e-9)) + 1}
    if clear_span is not None:
        out["CLEAR_SPAN_RATE"] = int(math.ceil(rate_per_m * clear_span / 1000.0 - 1e-9))
    return out


def assign_overlap(a, b, released):
    """a, b: object ids sharing one volume (a sorts first); released: set of released ids."""
    for x in sorted((a, b)):
        if x in released:
            return x
    return None
