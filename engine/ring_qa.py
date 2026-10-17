"""E1.4 §19 - the ring invariants, written into the run.

E1.3 established two facts about a ring the hard way, and enforced both
inside the mechanism where nothing could read them afterwards.

The first: a polygon built from an ordered list of points closes itself.
A chain of 3.738 m whose steps did not meet became a 1.619 m^2 polygon,
because shapely joined the two loose ends with a line 1.95 m long that
nobody had drawn. The area was impossible for the chain it came from and
the register said nothing about it.

The second: repairing a self-touching ring changes it. buffer(0) drops a
spur, and the perimeter of what comes back is not the perimeter of what
went in, so a check made after the repair passes on geometry the drawing
does not support.

This module records both, per candidate, as QA fields of the run. They
are diagnostics. None of them is a target, none is a quantity, and a
number here is never the answer to "how big is this room" - it is the
answer to "is the ring this chain made the chain's own ring".

A repaired polygon can never establish geometry the raw chain did not.
Every field below is measured on the RAW ring first, and the repair is
reported as something that happened to it, not as the thing measured.
"""

from __future__ import annotations

import math

MODEL = "A_RING_IS_ONLY_ITS_OWN_CHAIN_AND_QA_SAYS_SO_OUT_LOUD_V1"

CLOSURE_TOLERANCE_MM = 1.0
PERIMETER_TOLERANCE_MM = 1.0
ISOPERIMETRIC_TOLERANCE = 1.0e-6

# CHAIN_CONTINUITY_STATUS
CONTINUOUS = "EVERY_STEP_MEETS_THE_ONE_BEFORE_IT"
CLOSED_ON_ITSELF = "CONTINUOUS_AND_THE_LAST_STEP_MEETS_THE_FIRST"
BROKEN = "A_STEP_DOES_NOT_MEET_THE_ONE_BEFORE_IT"
OPEN_ENDED = "CONTINUOUS_BUT_THE_CHAIN_DOES_NOT_RETURN_TO_ITS_START"
TOO_SHORT = "FEWER_THAN_THREE_POINTS"

A_POLYGON_CLOSES_ITSELF = (
    "a polygon constructor joins the last point to the first whether or "
    "not anything is drawn there. MAX_UNDRAWN_CLOSURE_MM is the length of "
    "the longest line the polygon would have had to invent. Where it "
    "exceeds the closure tolerance the ring is not this chain's ring and "
    "no area may be taken from it")

A_REPAIR_IS_NOT_A_MEASUREMENT = (
    "POLYGON_REPAIR_APPLIED records that the raw ring was not a valid "
    "polygon and was repaired. Every length here is measured on the raw "
    "ring, before the repair, because the repair can drop a spur and "
    "return a shorter perimeter than the chain that was walked")

WHY_THE_ISOPERIMETRIC_CHECK = (
    "no closed curve encloses more area than a circle of its perimeter. "
    "A ring whose area exceeds perimeter^2 / 4pi is not a ring at all - "
    "the number came from somewhere other than the geometry. It is a "
    "coarse check and it catches the class of failure that matters: an "
    "area that the chain cannot have produced")

WHY_PORTAL_ORIENTATION_IS_CHECKED = (
    "a classified gap is stored with its two ends in the order the gap "
    "was FOUND in, which need not be the order the walk crosses it. Taken "
    "as given, an 800 mm and a 1000 mm doorway entered two rings "
    "backwards and each read as a notch cut out of the room. The check "
    "asks, of every span in the ring, whether it starts where the walk "
    "had got to")

THESE_ARE_QA_DIAGNOSTICS_NOT_TARGET_QUANTITIES = (
    "these fields say whether a ring is its chain's own ring. They are "
    "not quantities, they are not compared with any benchmark, and no "
    "part of the mechanism may read them to choose a boundary")


def _d(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _poly_len(pts):
    return sum(_d(pts[k], pts[k + 1]) for k in range(len(pts) - 1))


def continuity(step_points, *, snap_mm=CLOSURE_TOLERANCE_MM):
    """Where the walk's steps fail to meet each other, and by how much.

    Continuity is a property of the STEPS, not of the vertex list. Two
    consecutive vertices of a ring are legitimately far apart - they are
    the two ends of one drawn face. What may not be far apart is the last
    point of one step and the first point of the next, because nothing is
    drawn between them.
    """
    breaks = []
    prev = None
    for k, pts in enumerate(step_points or ()):
        pts = [tuple(q) for q in pts if q is not None]
        if not pts:
            continue
        if prev is not None:
            d = _d(prev, pts[0])
            if d > snap_mm:
                breaks.append({"between_mm": [list(prev), list(pts[0])],
                               "distance_mm": round(d, 3),
                               "AFTER_STEP": k - 1, "BEFORE_STEP": k})
        prev = pts[-1]
    return breaks


def assess(*, ring, chain_length_mm, seed=None, chain_breaks=None,
           step_points=None, portal_spans=(), snap_mm=CLOSURE_TOLERANCE_MM,
           perimeter_tolerance_mm=PERIMETER_TOLERANCE_MM):
    """The nine QA fields for one candidate's ring.

    `ring` is the ordered vertex list the walk produced and
    `chain_length_mm` the length of the chain as walked.
    `step_points` is the same walk as a list of per-step point lists; give
    it and continuity is measured here, from the steps themselves.
    `chain_breaks` is what the walk itself reported about its continuity,
    used when `step_points` is not supplied - the walk is then the
    authority on where its steps failed to meet and this module records
    what it said rather than guessing from the vertex list.
    `seed` is the label anchor the region was sought from, and
    `portal_spans` the spans of classified gap the walk crossed, each
    {"GAP_ID", "start_mm", "end_mm"}.
    """
    ring = [tuple(p) for p in (ring or [])]
    out = {
        "MODEL": MODEL,
        "RAW_CHAIN_LENGTH_MM": round(float(chain_length_mm), 3),
        "RAW_RING_PERIMETER_MM": None,
        "CHAIN_CONTINUITY_STATUS": TOO_SHORT,
        "MAX_UNDRAWN_CLOSURE_MM": None,
        "RING_CONSISTS_ONLY_OF_CHAIN": None,
        "RING_ENCLOSES_SEED": None,
        "POLYGON_REPAIR_APPLIED": None,
        "ISOPERIMETRIC_CHECK": None,
        "PORTAL_ORIENTATION_CHECK": None,
        "THESE_ARE_QA_DIAGNOSTICS_NOT_TARGET_QUANTITIES":
            THESE_ARE_QA_DIAGNOSTICS_NOT_TARGET_QUANTITIES,
        "A_POLYGON_CLOSES_ITSELF": A_POLYGON_CLOSES_ITSELF,
        "A_REPAIR_IS_NOT_A_MEASUREMENT": A_REPAIR_IS_NOT_A_MEASUREMENT,
    }
    if len(ring) < 3:
        out["RING_VERTICES"] = len(ring)
        return out

    if step_points is not None:
        breaks = continuity(step_points, snap_mm=snap_mm)
        out["CONTINUITY_MEASURED_FROM"] = "THE_STEPS_OF_THIS_WALK"
    else:
        breaks = [dict(b) for b in (chain_breaks or ())]
        out["CONTINUITY_MEASURED_FROM"] = (
            "WHAT_THE_WALK_REPORTED_ABOUT_ITS_OWN_STEPS")
    closing = _d(ring[-1], ring[0])
    undrawn = [b.get("distance_mm", 0.0) for b in breaks]
    if closing is not None and closing > snap_mm:
        undrawn.append(round(closing, 3))
    out["RING_VERTICES"] = len(ring)
    out["CHAIN_BREAKS"] = breaks
    out["THE_CLOSING_DISTANCE_MM"] = (None if closing is None
                                      else round(closing, 3))
    out["MAX_UNDRAWN_CLOSURE_MM"] = round(max(undrawn), 3) if undrawn else 0.0
    if breaks:
        out["CHAIN_CONTINUITY_STATUS"] = BROKEN
    elif closing is not None and closing > snap_mm:
        out["CHAIN_CONTINUITY_STATUS"] = OPEN_ENDED
    else:
        out["CHAIN_CONTINUITY_STATUS"] = CLOSED_ON_ITSELF
    if chain_breaks:
        out["BREAKS_THE_WALK_ITSELF_REPORTED"] = chain_breaks

    from shapely.geometry import LinearRing, Point, Polygon

    closed = ring + ([ring[0]] if _d(ring[-1], ring[0]) > 0.0 else [])
    raw_perimeter = _poly_len(closed)
    out["RAW_RING_PERIMETER_MM"] = round(raw_perimeter, 3)

    # the ring may consist of nothing but the chain that was walked. The
    # difference is length the polygon added by itself
    added = raw_perimeter - float(chain_length_mm)
    out["LENGTH_THE_RING_ADDED_BY_ITSELF_MM"] = round(added, 3)
    out["RING_CONSISTS_ONLY_OF_CHAIN"] = abs(added) <= perimeter_tolerance_mm

    try:
        raw = Polygon(closed)
    except Exception as exc:                       # a ring shapely refuses
        out["POLYGON_REPAIR_APPLIED"] = "THE_RAW_RING_IS_NOT_A_POLYGON"
        out["why"] = str(exc)
        return out

    out["RAW_RING_IS_SIMPLE"] = bool(LinearRing(closed).is_simple)
    out["RAW_RING_IS_VALID"] = bool(raw.is_valid)
    out["RAW_RING_AREA_MM2"] = round(abs(raw.area), 3)
    if raw.is_valid:
        out["POLYGON_REPAIR_APPLIED"] = False
        geom = raw
    else:
        repaired = raw.buffer(0)
        out["POLYGON_REPAIR_APPLIED"] = True
        out["REPAIRED_PERIMETER_MM"] = round(repaired.length, 3)
        out["REPAIRED_AREA_MM2"] = round(repaired.area, 3)
        out["LENGTH_THE_REPAIR_REMOVED_MM"] = round(
            raw_perimeter - repaired.length, 3)
        out["THE_REPAIR_IS_NOT_THE_MEASUREMENT"] = A_REPAIR_IS_NOT_A_MEASUREMENT
        geom = repaired

    # the ring must contain the point it was walked from
    if seed is not None:
        out["RING_ENCLOSES_SEED"] = bool(geom.covers(Point(seed)))
        out["SEED_MM"] = [seed[0], seed[1]]

    # no closed curve encloses more than a circle of the same perimeter
    area = abs(raw.area)
    bound = raw_perimeter ** 2 / (4.0 * math.pi)
    out["ISOPERIMETRIC_CHECK"] = {
        "RAW_AREA_MM2": round(area, 3),
        "THE_MOST_THIS_PERIMETER_COULD_ENCLOSE_MM2": round(bound, 3),
        "RATIO": round(area / bound, 9) if bound > 0 else None,
        "PASSED": area <= bound * (1.0 + ISOPERIMETRIC_TOLERANCE),
        "why": WHY_THE_ISOPERIMETRIC_CHECK,
    }

    out["PORTAL_ORIENTATION_CHECK"] = portal_orientation(
        ring, portal_spans, snap_mm=snap_mm)
    return out


def portal_orientation(ring, spans, *, snap_mm=CLOSURE_TOLERANCE_MM):
    """Does every span of classified gap sit in the ring the way it was crossed?

    A span is right when its two ends are consecutive vertices of the
    ring. It is backwards when they appear in the ring the other way
    round from the way the walk went, and it is absent when the ring does
    not carry it at all.
    """
    rows = []
    n = len(ring)
    for sp in spans or ():
        a, z = tuple(sp["start_mm"]), tuple(sp["end_mm"])
        found = None
        for k in range(n - 1):
            p, q = ring[k], ring[k + 1]
            if _d(p, a) <= snap_mm and _d(q, z) <= snap_mm:
                found = "AS_STORED"
                break
            if _d(p, z) <= snap_mm and _d(q, a) <= snap_mm:
                found = "REVERSED_FROM_STORED"
                break
        rows.append({
            "GAP_ID": sp.get("GAP_ID"),
            "SPAN_LENGTH_MM": round(_d(a, z), 3),
            "HOW_THE_RING_CARRIES_IT": found or "NOT_CONSECUTIVE_IN_THE_RING",
            "THE_SPAN_IS_A_SINGLE_STEP_OF_THE_RING": found is not None,
        })
    return {
        "spans": rows,
        "EVERY_SPAN_IS_ONE_STEP_OF_THE_RING": all(
            r["THE_SPAN_IS_A_SINGLE_STEP_OF_THE_RING"] for r in rows),
        "SPANS_THE_RING_DOES_NOT_CARRY": sum(
            1 for r in rows
            if not r["THE_SPAN_IS_A_SINGLE_STEP_OF_THE_RING"]),
        "why": WHY_PORTAL_ORIENTATION_IS_CHECKED,
    }


REQUIRED_FIELDS = (
    "RAW_CHAIN_LENGTH_MM",
    "RAW_RING_PERIMETER_MM",
    "CHAIN_CONTINUITY_STATUS",
    "MAX_UNDRAWN_CLOSURE_MM",
    "RING_CONSISTS_ONLY_OF_CHAIN",
    "RING_ENCLOSES_SEED",
    "POLYGON_REPAIR_APPLIED",
    "ISOPERIMETRIC_CHECK",
    "PORTAL_ORIENTATION_CHECK",
)


def assert_every_required_field_is_written(row):
    """The run must carry all nine. A missing field is a silent invariant."""
    missing = [f for f in REQUIRED_FIELDS if f not in row]
    if missing:
        raise AssertionError(
            "RING_QA_FIELD_NOT_WRITTEN_INTO_THE_RUN = " + ",".join(missing))
    return True


A_RING_MAY_NOT_BE_ESTABLISHED_BY_ITS_REPAIR = (
    "where RING_CONSISTS_ONLY_OF_CHAIN is false, or "
    "MAX_UNDRAWN_CLOSURE_MM exceeds the closure tolerance, or the "
    "isoperimetric check fails, or the ring does not enclose its seed, "
    "the candidate is not established by this ring. The repair does not "
    "change that and no area is taken from it")


def establishes_geometry(row, *, snap_mm=CLOSURE_TOLERANCE_MM):
    """Whether this ring establishes the candidate's geometry at all."""
    reasons = []
    if row.get("CHAIN_CONTINUITY_STATUS") != CLOSED_ON_ITSELF:
        reasons.append(row.get("CHAIN_CONTINUITY_STATUS"))
    if (row.get("MAX_UNDRAWN_CLOSURE_MM") or 0.0) > snap_mm:
        reasons.append("THE_POLYGON_WOULD_HAVE_CLOSED_AN_UNDRAWN_GAP")
    if row.get("RING_CONSISTS_ONLY_OF_CHAIN") is not True:
        reasons.append("THE_RING_DID_NOT_CLOSE_ON_THE_CHAIN")
    if row.get("RING_ENCLOSES_SEED") is False:
        reasons.append("THE_RING_DOES_NOT_CONTAIN_ITS_SEED")
    iso = row.get("ISOPERIMETRIC_CHECK") or {}
    if iso.get("PASSED") is False:
        reasons.append("THE_AREA_EXCEEDS_WHAT_THIS_PERIMETER_CAN_ENCLOSE")
    po = row.get("PORTAL_ORIENTATION_CHECK") or {}
    if po.get("EVERY_SPAN_IS_ONE_STEP_OF_THE_RING") is False:
        reasons.append("A_SPAN_IS_NOT_ONE_STEP_OF_THE_RING")
    return {
        "RING_ESTABLISHES_GEOMETRY": not reasons,
        "WHY_NOT": reasons,
        "A_RING_MAY_NOT_BE_ESTABLISHED_BY_ITS_REPAIR":
            A_RING_MAY_NOT_BE_ESTABLISHED_BY_ITS_REPAIR,
    }
