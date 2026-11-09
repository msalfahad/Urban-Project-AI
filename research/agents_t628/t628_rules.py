"""T-628 rules (research, unwired): the residual rows of the keyed footing line (pads + straps + boundary band) and of
the lift pit walls are closed only by a per-row re-measure from the structural drawing, for any villa.

Context. Statement V11 (T-620) carries T-551/footing-line (5 rows, reference 77.6305 vs engine 67.6945 m3) and
T-551/lift-walls (2 rows, 2.4 vs 0 m3); none was re-measured row by row. T-628 measures each row again from the
drawing (outline handles x schedule depth, strap faces, the plot band, the pit ring) and classes it.

R-T628-1 FOOTING ROW BY OUTLINE. A footing mark's own volume = sum over its drawn outlines (each outline once, its tag
      bound inside it, else to the nearest outline within 1.0 m whose drawn size equals the tag's schedule row) of
      drawn plan area x schedule depth. The drawn size must equal the schedule L x W (either orientation, 5 mm) on
      every outline that is not notched; an outline whose plan is smaller than its bounding rectangle is NOTCHED only
      when the missing piece lies inside another footing outline (the designer drew the intersection once: the
      other outline owns it). COUNT term = (reference count - drawn count) x the reference unit volume; a COUNT term
      on a mark whose drawn size disagrees with its schedule row is refused (that is a SECTION question, not COUNT).
      An outline carrying two different tags is CONFLICT: HELD with the bound of the two readings, never 0.
R-T628-2 EACH PLAN REGION ONCE. Across footings, straps, the boundary band and pit walls a plan region enters one
      member's volume only: sum of member plans must equal their union (a shared EDGE is not an overlap); an overlap
      enters a total only with its named owner (the deeper / earlier-poured member: footing over strap and band,
      F9 over FN). A member crossing another at a DIFFERENT elevation shares no volume (vertical overlap 0); where
      either level is not printed the crossing is HELD by name (owner Q-28 2026-10-19), never deducted silently.
R-T628-3 STRAP CLEAR LENGTH. A strap's length is its axis outside the union of the footing outlines it joins (clear
      face to face, on the axis); volume = schedule width x schedule depth x clear axis length. Where the schedule
      prints two rows for one mark, the drawn face spacing selects the row only if exactly one row is within 5 % of it;
      else SECTION_CONFLICT, HELD.
R-T628-4 HELD BOUND PROVENANCE. A HELD row's comparison bound is quoted only from a basis not marked UNSUPPORTED by a
      downgrade record; an unsupported bound is replaced, in the row's note, by the drawing range with its source
      (the class stays HELD; the line stays blank; the replacement is a fix row for the statement).
R-T628-5 PIT RING ONCE. Pit wall plan = outer pit outline - inner shaft outline - the column outlines inside the ring
      (the columns / necks own their pieces, R-T394-6); a reference ring that keeps the column pieces is SCOPE_DOUBLE
      by the column plan x the reference height. Wall height not printed -> HELD by the designer item, never 0.
"""
from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP

RULE_ID = "R-T628-1..5"
TOL_M3 = Decimal("0.001")
SIZE_TOL_M = 0.005
SECTION_TOL = 0.05
CLASSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "TOLERANCE", "UNRESOLVED",
           "HELD")
BALANCING = ("BALANCE", "SHORT", "REMAINDER", "PLUG", "OTHER", "RESIDUAL", "ADJUSTMENT")


class Refused(ValueError):
    """A rule of R-T628-1 .. 5 refuses the input."""


def d6(x) -> Decimal:
    if x is None:
        raise Refused("missing value (never 0)")
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        raise Refused("not a number")
    return Decimal(str(x)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _unit(unit):
    if unit != "m3":
        raise Refused(f"unit {unit!r}: concrete rows are m3 only")


# ------------------------------------------------------------------------------------------------ R-T628-1
def size_agrees(bounds, L, W, tol=SIZE_TOL_M):
    """Drawn bounding size (x0, y0, x1, y1, metres) equals the schedule L x W in either orientation."""
    a, b = bounds[2] - bounds[0], bounds[3] - bounds[1]
    return (abs(a - L) <= tol and abs(b - W) <= tol) or (abs(a - W) <= tol and abs(b - L) <= tol)


def outline_status(poly, others, L, W):
    """FULL (drawn = schedule rectangle), NOTCHED (the missing piece lies inside another outline: that outline owns
    it) or refused (smaller with no owner, or a size that is not the schedule row)."""
    from shapely.geometry import box
    if not size_agrees(poly.bounds, L, W):
        raise Refused(f"drawn {poly.bounds} is not the schedule {L} x {W}: SECTION, not COUNT")
    missing = box(*poly.bounds).difference(poly)
    if missing.area <= 1e-6:
        return "FULL", 0.0
    owned = sum(missing.intersection(o).area for o in others)
    if abs(owned - missing.area) > 1e-6:
        raise Refused("outline smaller than its rectangle and the missing piece is in no other outline")
    return "NOTCHED", missing.area


def mark_volume(outlines, depth):
    """sum(drawn plan area) x schedule depth over the mark's outlines (each once)."""
    if depth is None:
        raise Refused("schedule depth not printed: HELD, never 0")
    ids = [h for h, _ in outlines]
    if len(ids) != len(set(ids)):
        raise Refused("an outline counted twice in one mark")
    return d6(sum((Decimal(str(round(a, 9))) for _, a in outlines), Decimal(0)) * d6(depth))


def count_delta(ref_n, drawn_n, ref_unit_m3):
    if int(drawn_n) != drawn_n or drawn_n < 0 or int(ref_n) != ref_n:
        raise Refused("counts are whole numbers")
    return d6((Decimal(int(ref_n)) - Decimal(int(drawn_n))) * d6(ref_unit_m3))


def conflict_bound(readings):
    """Two readings of one CONFLICT outline -> (low, high), HELD; never one of them silently."""
    vals = [d6(v) for v in readings]
    if len(vals) < 2:
        raise Refused("a CONFLICT needs two readings")
    if min(vals) <= 0:
        raise Refused("HELD as 0")
    return min(vals), max(vals)


# ------------------------------------------------------------------------------------------------ R-T628-2
def plans_once(members):
    """members = {name: polygon}. Sum of plans must equal the union (a shared edge is not an overlap); returns the
    list of overlapping pairs with area (empty when every region is counted once)."""
    import itertools
    pairs = []
    for (a, pa), (b, pb) in itertools.combinations(members.items(), 2):
        ar = pa.intersection(pb).area
        if ar > 1e-9:
            pairs.append((a, b, ar))
    return pairs


def total_once(volumes, overlaps, owners):
    """Sum member volumes {name: m3}; every overlap {(a, b): m3} must name its owner in owners {(a, b): name}, and
    the overlap is then deducted from the member that does NOT own it. An overlap with no owner refuses the sum
    (billed twice)."""
    tot = sum((d6(v) for v in volumes.values()), Decimal(0))
    for k, v in overlaps.items():
        if d6(v) == 0:
            continue
        own = owners.get(k)
        if own not in k:
            raise Refused(f"overlap {k} {v} m3 has no owner: billed twice")
        tot -= d6(v)
    return d6(tot)


def crossing_volume(plan_m2, a_bot, a_top, b_bot, b_top):
    """Shared volume of two members crossing in plan: plan x vertical overlap; a level not printed -> refused (HELD
    crossing by name, never a silent deduction); members at different elevations share 0."""
    if None in (a_bot, a_top, b_bot, b_top):
        raise Refused("crossing level not printed: HELD by name (Q-28), never deducted")
    v = max(0.0, min(a_top, b_top) - max(a_bot, b_bot))
    return d6(Decimal(str(plan_m2)) * Decimal(str(round(v, 9))))


# ------------------------------------------------------------------------------------------------ R-T628-3
def strap_axis(face_a, face_b):
    """Axis of a strap from its two face segments ((x, y), (x, y)): midpoints of the matching ends."""
    from shapely.geometry import LineString
    (a0, a1), (b0, b1) = face_a, face_b
    if math.dist(a0, b0) > math.dist(a0, b1):
        b0, b1 = b1, b0
    return LineString([((a0[0] + b0[0]) / 2, (a0[1] + b0[1]) / 2), ((a1[0] + b1[0]) / 2, (a1[1] + b1[1]) / 2)])


def strap_clear_length(axis, footings_union):
    """Clear axis length outside the footing outlines it joins (m)."""
    clear = axis.difference(footings_union)
    if clear.is_empty:
        raise Refused("strap axis lies wholly inside footings")
    return clear.length


def strap_section(rows, drawn_width):
    """Select the schedule row of a strap: one row -> it; two rows -> the single row within 5 % of the drawn width,
    else SECTION_CONFLICT (refused, HELD)."""
    if not rows:
        raise Refused("strap has no schedule row: HELD")
    if len(rows) == 1:
        return rows[0]
    fit = [r for r in rows if abs(r[0] - drawn_width) <= SECTION_TOL * r[0]]
    if len(fit) != 1:
        raise Refused("SECTION_CONFLICT: the drawn width does not select one schedule row")
    return fit[0]


def strap_volume(width, depth, length):
    return d6(Decimal(str(width)) * Decimal(str(depth)) * Decimal(str(round(length, 6))))


# ------------------------------------------------------------------------------------------------ R-T628-4
def held_bound(bound, downgrade_label, drawing_range, source):
    """Return the bound a HELD row may quote: the engine bound unless a downgrade marks it UNSUPPORTED, then the
    drawing range with its source. The row stays HELD either way."""
    if downgrade_label and "UNSUPPORTED" in str(downgrade_label).upper():
        if not drawing_range or not source:
            raise Refused("unsupported bound with no drawing range: quote nothing, HELD")
        lo, hi = d6(drawing_range[0]), d6(drawing_range[1])
        if lo > hi:
            raise Refused("range low above high")
        return {"bound": [str(lo), str(hi)], "basis": source, "replaced": str(d6(bound)) if bound is not None
                else None}
    if bound is None:
        raise Refused("no bound")
    return {"bound": [str(d6(bound)), str(d6(bound))], "basis": "engine held line", "replaced": None}


def position(value, lo, hi):
    v, lo, hi = d6(value), d6(lo), d6(hi)
    return "BELOW" if v < lo else ("ABOVE" if v > hi else "INSIDE")


# ------------------------------------------------------------------------------------------------ R-T628-5
def pit_ring(outer, inner, columns):
    """(gross ring m2, column pieces in the ring m2, net ring m2)."""
    if not inner.within(outer):
        raise Refused("shaft outline not inside the pit outline")
    ring = outer.difference(inner)
    cols = sum(ring.intersection(c).area for c in columns)
    return ring.area, cols, ring.area - cols


def scope_double(column_piece_m2, ref_height):
    return d6(Decimal(str(round(column_piece_m2, 9))) * d6(ref_height))


# ------------------------------------------------------------------------------------------------ rows / split
def row_status(own_delta, statement_delta, held_by=None, drift_cause=None, unit="m3"):
    """(status, drift): RE-MEASURED within 0.001 m3, or with a named physical drift cause; HELD rows need the item."""
    _unit(unit)
    drift = d6(own_delta) - d6(statement_delta)
    if held_by is not None:
        if not str(held_by).strip():
            raise Refused("HELD row needs the designer / owner item by name")
        if d6(own_delta) == 0:
            raise Refused("HELD as 0")
        return "HELD", drift
    if abs(drift) <= TOL_M3:
        return "RE-MEASURED", drift
    if drift_cause and drift_cause.strip().split()[0].upper().strip(":") not in BALANCING:
        return "RE-MEASURED", drift
    raise Refused(f"drift {drift} m3 beyond {TOL_M3} with no named physical cause")


def split_exact(total, causes, unit="m3"):
    """causes {name: (class, m3)} re-add exactly to total; a balancing name is refused; HELD never 0."""
    _unit(unit)
    tot = Decimal(0)
    for name, (cls, m3) in causes.items():
        if not name or name.strip().split()[0].upper().strip(":") in BALANCING:
            raise Refused(f"cause {name!r} is a balancing term")
        if cls not in CLASSES:
            raise Refused(f"class {cls!r}")
        v = d6(m3)
        if cls == "HELD" and v == 0:
            raise Refused("HELD as 0")
        tot += v
    if tot != d6(total):
        raise Refused(f"causes re-add to {tot}, total {d6(total)}: open sum")
    return tot
