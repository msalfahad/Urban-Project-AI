"""T-623 rules (research, unwired): an UNKNOWN residual row of a reconciled concrete line is closed only by a per-row
re-measure from the drawing, for any villa.

Context. The reconciled-quantities statement (T-609 V10) carries per line a list of residual rows (reference - engine,
m3) with a class. A row whose class was proposed by a worker and never re-measured is UNKNOWN in the scorecard (T-613
R-T613-1). T-623 re-measures each such row of the two biggest concrete lines (B10-07 beams, B10 columns).

R-T623-1 ROW RE-MEASURE. For every row:
      own_m3     = the drawn solid the row is about, measured again from the drawing (faces / outlines / arcs by
                   handle, printed section or schedule depth), never copied from the engine line or the reference;
      ref_m3     = the reference rows of the same component (his b x D x L x n, or his count x his unit);
      own_delta  = ref_m3 - own_m3 (the statement sign);
      drift      = own_delta - statement delta.
      |drift| <= TOL_M3 (0.001 m3)                                     -> RE-MEASURED, class confirmed or changed;
      |drift|  > TOL_M3 and the drift has a named physical cause      -> RE-MEASURED with a DRIFT term (named);
      otherwise                                                         -> refused (no silent acceptance).
      A row whose quantity depends on a designer item stays HELD by name (D-xx), never 0. A row that is a closure
      term of a pair (THROUGH_SUPPORT residual) is RE-MEASURED only in the parts the drawing measures; the rest stays
      UNRESOLVED with its bounds, never relabelled as a cause.
R-T623-2 LINE SPLIT CLOSES EXACTLY. The per-line UNKNOWN delta (sum of the line's UNKNOWN rows in the statement) is
      split into named causes (Decimal, 6 dp) that re-add exactly; a cause named BALANCE / SHORT / REMAINDER / PLUG /
      OTHER / RESIDUAL / ADJUSTMENT is a balancing term, never a class, and is refused.
R-T623-3 EACH PIECE ONCE. A drawn piece (storey, band or outline handle) enters one row's own measure only; a node or a
      band end already owned by a column line (UP-CONC-JOINT-001, R-T600-1) or by another beam piece (R-T610-1,
      R-T614-1) is cited, never measured into a second row.
"""
from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP

RULE_ID = "R-T623-1..3"
TOL_M3 = Decimal("0.001")
CLASSES = ("ENGINE_RIGHT", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "TOLERANCE", "UNRESOLVED", "HELD")
STATUSES = ("RE-MEASURED", "RE-MEASURED (PARTS)", "HELD")
BALANCING = ("BALANCE", "SHORT", "REMAINDER", "PLUG", "OTHER", "RESIDUAL", "ADJUSTMENT")


class Refused(ValueError):
    """A rule of R-T623-1 .. 3 refuses the input."""


def d6(x) -> Decimal:
    if x is None:
        raise Refused("missing value (never 0)")
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        raise Refused("not a number")
    return Decimal(str(x)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _unit(unit):
    if unit != "m3":
        raise Refused(f"unit {unit!r}: concrete rows are m3 only")


# ------------------------------------------------------------------------------------------------ geometry
def quad_plan(face_a, face_b):
    """Drawn plan of a straight beam band from its two face segments ((x, y), (x, y)) in metres. Where both faces are
    drawn the band is certain; past that, a face may run on by at most one band width (the oblique drawn end: one face
    stops at a member face, the other at its corner); a face that runs on further is a longer line (slab edge, a face
    shared with the next member) and the band ends with its partner. Returns a shapely Polygon."""
    from shapely.geometry import Polygon
    (a0, a1), (b0, b1) = face_a, face_b
    ux, uy = a1[0] - a0[0], a1[1] - a0[1]
    ln = math.hypot(ux, uy)
    if ln == 0:
        raise Refused("zero-length face")
    ux, uy = ux / ln, uy / ln
    nx, ny = -uy, ux
    ta = sorted(p[0] * ux + p[1] * uy for p in (a0, a1))
    tb = sorted(p[0] * ux + p[1] * uy for p in (b0, b1))
    oa = a0[0] * nx + a0[1] * ny
    ob = (b0[0] * nx + b0[1] * ny + b1[0] * nx + b1[1] * ny) / 2
    w = abs(ob - oa)
    if w <= 0 or abs((b0[0] - b1[0]) * nx + (b0[1] - b1[1]) * ny) > 1e-4:
        raise Refused("faces are not two parallel lines")
    t0, t1 = max(ta[0], tb[0]), min(ta[1], tb[1])
    if t1 <= t0:
        raise Refused("faces do not overlap along the axis")
    a_lo, b_lo = [x if t0 - x <= w + 1e-9 else t0 for x in (ta[0], tb[0])]
    a_hi, b_hi = [x if x - t1 <= w + 1e-9 else t1 for x in (ta[1], tb[1])]

    def P(t, o):
        return (ux * t + nx * o, uy * t + ny * o)
    p = Polygon([P(a_lo, oa), P(a_hi, oa), P(b_hi, ob), P(b_lo, ob)]).buffer(0)
    if p.is_empty or p.area <= 0:
        raise Refused("faces do not bound a band")
    return p


def axis_strip(u, lo, hi):
    """The half-plane strip lo <= t <= hi along unit axis u (None = open)."""
    from shapely.geometry import Polygon
    big = 1e6
    lo = -big if lo is None else lo
    hi = big if hi is None else hi
    nx, ny = -u[1], u[0]
    return Polygon([(u[0] * lo - nx * big, u[1] * lo - ny * big), (u[0] * hi - nx * big, u[1] * hi - ny * big),
                    (u[0] * hi + nx * big, u[1] * hi + ny * big), (u[0] * lo + nx * big, u[1] * lo + ny * big)])


def annulus_in_box(c, r_in, r_out, box):
    """Area (m2) of the ring r_in .. r_out about c inside the rectangle box = (x0, y0, x1, y1), by exact polygon
    clipping of a 4096-gon annulus (error < 1e-6 m2 at villa radii)."""
    from shapely.geometry import Point, box as sbox
    if not (0 < r_in < r_out):
        raise Refused("ring radii")
    ring = Point(c).buffer(r_out, 1024).difference(Point(c).buffer(r_in, 1024))
    return ring.intersection(sbox(*box)).area


# ------------------------------------------------------------------------------------------------ quantities
def beam_volume(plan_m2, depth_m):
    if depth_m is None:
        raise Refused("depth not printed: HELD, never 0")
    return d6(Decimal(str(plan_m2)) * Decimal(str(depth_m)))


def count_delta(ref_n, drawn_n, ref_unit_m3):
    """COUNT term (reference - drawing): (his count - drawn count) x his unit; a drawn count is integer and >= 0."""
    if int(drawn_n) != drawn_n or drawn_n < 0 or int(ref_n) != ref_n:
        raise Refused("counts are whole numbers")
    return d6((Decimal(int(ref_n)) - Decimal(int(drawn_n))) * d6(ref_unit_m3))


def global_depth_delta(members, ref_depth):
    """GLOBAL_DEPTH (reference - engine): his column stops one uniform depth ref_depth below the slab top, the member
    stops at its own controlling depth D (the deepest beam framing in). Per member A x (D - ref_depth); a member
    whose D is not settled is refused here (HEIGHT_OPEN, its own row)."""
    tot = Decimal(0)
    for a, d in members:
        if d is None:
            raise Refused("D_ctrl open: HEIGHT_OPEN row, not GLOBAL_DEPTH")
        tot += d6(a) * (d6(d) - d6(ref_depth))
    return d6(tot)


def joint_head(members):
    """J = sum A x D_ctrl over the compared column set (UP-CONC-JOINT-001: the column line owns the joint)."""
    return d6(sum((d6(a) * d6(d) for a, d in members), Decimal(0)))


# ------------------------------------------------------------------------------------------------ rows / line
def row_status(own_delta, statement_delta, drift_cause=None, held_by=None, unit="m3"):
    """R-T623-1. Returns (status, drift)."""
    _unit(unit)
    if held_by:
        if not str(held_by).strip():
            raise Refused("HELD row needs the designer item by name")
        return "HELD", None
    drift = d6(own_delta) - d6(statement_delta)
    if abs(drift) <= TOL_M3:
        return "RE-MEASURED", drift
    if drift_cause and drift_cause.strip() and drift_cause.strip().upper() not in BALANCING:
        return "RE-MEASURED", drift
    raise Refused(f"drift {drift} m3 beyond {TOL_M3} with no named physical cause")


def check_class(cls):
    if cls is None or str(cls).upper() in BALANCING or cls not in CLASSES:
        raise Refused(f"class {cls!r} is not a class (balancing terms are refused)")
    return cls


def split_line(line_unknown_delta, causes, unit="m3"):
    """R-T623-2: named causes {name: (class, m3)} re-add exactly to the line's UNKNOWN delta."""
    _unit(unit)
    tot = Decimal(0)
    for name, (cls, m3) in causes.items():
        if not name or name.strip().split()[0].upper().strip(":") in BALANCING:
            raise Refused(f"cause {name!r} is a balancing term")
        check_class(cls)
        v = d6(m3)
        if cls == "HELD" and v == 0:
            raise Refused("HELD as 0")
        tot += v
    if tot != d6(line_unknown_delta):
        raise Refused(f"causes re-add to {tot}, line UNKNOWN delta {d6(line_unknown_delta)}: open sum")
    return tot


def pieces_once(rows):
    """R-T623-3: every (storey, piece) appears in one row's own measure only."""
    seen = {}
    for r in rows:
        for p in r.get("pieces", []):
            k = (r["storey"], p)
            if k in seen:
                raise Refused(f"piece {k} measured in two rows ({seen[k]}, {r['name']})")
            seen[k] = r["name"]
    return len(seen)
