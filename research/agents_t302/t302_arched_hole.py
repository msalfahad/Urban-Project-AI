"""T-302 rules: the developed hole an arched opening leaves in a CURVED (cylindrical) wall, per face.

Research module (R-T302-1), not a rule version file. Physical element first: a hole through a wall whose faces are
coaxial cylinders (plan arcs about one centre). The elevation is an orthographic projection: a point of the wall at
plan position P is drawn at elevation abscissa u = (P - O) . e (O a plan point on the elevation's u = 0 axis, e the
plan unit vector of the elevation's +u direction), at its true height. The drawn head H(u) is the projection of the
head on the face the elevation shows (the REFERENCE face, the one nearest the viewer).

On a face of radius r between plan angles a1 .. a2 the developed hole is

    A(r) = integral over phi of h(phi) * r dphi            (developed arc length element ds = r dphi)

with h(phi) the head height above the hole's bottom at that point of the face:
- on the reference face h(phi) = H(u_ref(phi)) - sill (what the elevation shows);
- on another face the drawing shows no head. Two constructions consistent with a drawn head:
  RADIAL: the soffit runs radially (h at angle phi equals the reference face's h at the same angle; reveals radial);
  PRISMATIC: the soffit runs along the view direction (h = H(u_face(phi))).
  Unless the soffit is drawn (a section), that face's hole is HELD (BOUNDED) between the two, never a midpoint.

Never: the projected (elevation) area used as the developed hole on a curved face; the window line's area (a window
measure, e.g. Q-76 A) used as the hole; a hole larger than the developed width x crown rectangle; a missing radius as 0.
Integration is exact per piece: the angle range is split where u(phi) meets a vertex of the head polyline, then
20-point Gauss-Legendre on each smooth piece (the integrand is smooth between vertices).
"""
from __future__ import annotations

import bisect
import math

R_ID = "R-T302-1"
STATUS_CONFIRMED = "DRAWING-CONFIRMED"
STATUS_BOUNDED = "HELD (BOUNDED)"
STATUS_HELD = "HELD"
REG_TOL_MM = 0.5

_GL_X, _GL_W = None, None


def _gauss_legendre(n=20):
    """Nodes / weights on [-1, 1] by Newton on the Legendre polynomial (no numpy needed)."""
    global _GL_X, _GL_W
    if _GL_X is not None:
        return _GL_X, _GL_W
    xs, ws = [], []
    for i in range(1, n + 1):
        x = math.cos(math.pi * (i - 0.25) / (n + 0.5))
        for _ in range(100):
            p0, p1 = 1.0, x
            for k in range(2, n + 1):
                p0, p1 = p1, ((2 * k - 1) * x * p1 - (k - 1) * p0) / k
            dp = n * (x * p1 - p0) / (x * x - 1)
            dx = p1 / dp
            x -= dx
            if abs(dx) < 1e-15:
                break
        xs.append(x)
        ws.append(2 / ((1 - x * x) * dp * dp))
    _GL_X, _GL_W = xs, ws
    return xs, ws


class Refused(ValueError):
    """A deduction basis the rule refuses; `.code` names it."""

    def __init__(self, code, msg):
        super().__init__(f"{code}: {msg}")
        self.code = code


class HeadProfile:
    """The drawn head: a polyline (u, H) in the elevation, u strictly increasing, heights above the elevation datum."""

    def __init__(self, pts):
        pts = [(float(u), float(h)) for u, h in pts]
        if len(pts) < 2:
            raise Refused("BAD_PROFILE", "a head needs at least two points")
        for (u0, _), (u1, _) in zip(pts, pts[1:]):
            if not u1 > u0:
                raise Refused("BAD_PROFILE", "u must increase strictly along the head polyline")
        self.pts = pts
        self._us = [u for u, _ in pts]

    @property
    def umin(self):
        return self.pts[0][0]

    @property
    def umax(self):
        return self.pts[-1][0]

    @property
    def crown(self):
        return max(h for _, h in self.pts)

    def __call__(self, u, tol=1e-9):
        if u < self.umin - tol or u > self.umax + tol:
            raise Refused("OUTSIDE_HEAD", f"u {u:.4f} outside the drawn head {self.umin:.4f} .. {self.umax:.4f}")
        u = min(max(u, self.umin), self.umax)
        i = min(max(bisect.bisect_right(self._us, u) - 1, 0), len(self.pts) - 2)
        (a, b), (c, d) = self.pts[i], self.pts[i + 1]
        return b + (d - b) * (u - a) / (c - a)

    def projected_area(self, u1, u2, sill=0.0):
        """Elevation (projected) area under the head between u1 < u2, above `sill`: exact for a polyline."""
        knots = sorted({u1, u2, *[u for u, _ in self.pts if u1 < u < u2]})
        return sum((b - a) * ((self(a) + self(b)) / 2 - sill) for a, b in zip(knots, knots[1:]))


class Elevation:
    """Registration of the elevation on the plan: u = (P - origin) . e, e a unit plan vector."""

    def __init__(self, origin, e):
        n = math.hypot(*e)
        if n == 0:
            raise Refused("BAD_AXIS", "elevation axis has no direction")
        self.ox, self.oy = origin
        self.ex, self.ey = e[0] / n, e[1] / n

    def u_on(self, centre, r, phi):
        x, y = centre[0] + r * math.cos(phi), centre[1] + r * math.sin(phi)
        return (x - self.ox) * self.ex + (y - self.oy) * self.ey


def register(elev, centre, r_ref, a1_deg, a2_deg, drawn_jambs_u, tol=REG_TOL_MM):
    """The plan jambs on the reference face projected by `elev` must fall on the drawn elevation jambs (both ends,
    order-free) within `tol` (drawing units). Returns (ok, residuals)."""
    if r_ref is None:
        return False, None
    pu = sorted(elev.u_on(centre, r_ref, math.radians(a)) for a in (a1_deg, a2_deg))
    du = sorted(drawn_jambs_u)
    res = [p - d for p, d in zip(pu, du)]
    return all(abs(x) <= tol for x in res), res


def developed_hole(prof, elev, centre, r_face, a1_deg, a2_deg, sill=0.0, model="RADIAL", r_ref=None):
    """Developed hole on the face of radius r_face between plan angles a1 < a2 (degrees, CCW).
    model RADIAL needs r_ref (the reference face radius); PRISMATIC reads the head at the face's own projection.
    Returns the area in drawing units squared. A missing radius is not a number: Refused('MISSING_RADIUS')."""
    if r_face is None or (model == "RADIAL" and r_ref is None):
        raise Refused("MISSING_RADIUS", "face or reference radius not established: HELD, never 0")
    if not a2_deg > a1_deg:
        raise Refused("BAD_RANGE", "angles must increase (a1 < a2)")
    r_read = r_ref if model == "RADIAL" else r_face
    if model not in ("RADIAL", "PRISMATIC"):
        raise Refused("BAD_MODEL", model)
    p1, p2 = math.radians(a1_deg), math.radians(a2_deg)
    # u(phi) = C + r_read * cos(phi - beta): split where it meets a head vertex
    beta = math.atan2(elev.ey, elev.ex)
    C = (centre[0] - elev.ox) * elev.ex + (centre[1] - elev.oy) * elev.ey
    cuts = {p1, p2}
    for uk, _ in prof.pts:
        c = (uk - C) / r_read
        if -1 <= c <= 1:
            base = math.acos(c)
            for s in (beta + base, beta - base):
                for k in range(-2, 3):
                    t = s + 2 * math.pi * k
                    if p1 < t < p2:
                        cuts.add(t)
    knots = sorted(cuts)
    xs, ws = _gauss_legendre()
    total = 0.0
    for a, b in zip(knots, knots[1:]):
        m, hw = (a + b) / 2, (b - a) / 2
        for x, w in zip(xs, ws):
            phi = m + hw * x
            h = prof(elev.u_on(centre, r_read, phi)) - sill
            if h < -1e-9:
                raise Refused("HEAD_BELOW_SILL", f"head {h:.4f} below the sill")
            total += w * hw * h * r_face
    return total


def check_deduction(area, basis, developed_width, crown_above_sill, curved=True):
    """Guard on a hole offered as a finish / masonry deduction. Refuses: PROJECTED_AS_DEVELOPED (an elevation area on
    a curved face), WINDOW_AREA_AS_HOLE (the window line's measure), HOLE_EXCEEDS_RECTANGLE (more than developed
    width x crown), MISSING (None is HELD, never 0). Returns the area unchanged when it passes."""
    if area is None:
        raise Refused("MISSING", "hole not established: HELD, never 0")
    if basis == "PROJECTED" and curved:
        raise Refused("PROJECTED_AS_DEVELOPED", "an elevation area is not the developed hole on a curved face")
    if basis == "WINDOW_LINE":
        raise Refused("WINDOW_AREA_AS_HOLE", "the window line's area is a window measure, not the hole")
    if basis != "DEVELOPED":
        raise Refused("BAD_BASIS", basis)
    cap = developed_width * crown_above_sill
    if area > cap + 1e-9:
        raise Refused("HOLE_EXCEEDS_RECTANGLE", f"{area:.4f} > developed width x crown {cap:.4f}")
    if area < 0:
        raise Refused("NEGATIVE", f"{area:.4f}")
    return area


def face_record(name, prof, elev, centre, r_face, a1, a2, r_ref, sill, soffit_drawn=False, registered=True):
    """One face of the hole: developed width, both constructions, status. On the reference face the two coincide;
    elsewhere the face is HELD (BOUNDED) unless the soffit is drawn. Unregistered elevation: HELD (A5)."""
    width = r_face * math.radians(a2 - a1) if r_face is not None else None
    if r_face is None or r_ref is None:
        return dict(face=name, radius=r_face, developed_width=width, radial=None, prismatic=None, lo=None, hi=None,
                    status=STATUS_HELD, held_item="radius not established")
    rad = developed_hole(prof, elev, centre, r_face, a1, a2, sill, "RADIAL", r_ref)
    try:
        pri = developed_hole(prof, elev, centre, r_face, a1, a2, sill, "PRISMATIC")
    except Refused as x:
        if x.code != "OUTSIDE_HEAD":
            raise
        return dict(face=name, radius=r_face, developed_width=width, radial=rad, prismatic=None, lo=None, hi=None,
                    status=STATUS_HELD, held_item="the PRISMATIC construction leaves the drawn head: no bound pair")
    lo, hi = min(rad, pri), max(rad, pri)
    crown = prof.crown - sill
    for v in (lo, hi):
        check_deduction(v, "DEVELOPED", width, crown)
    if not registered:
        status, item = STATUS_HELD, "plan and elevation do not register on the jambs (A5)"
    elif abs(r_face - r_ref) < 1e-9 or soffit_drawn:
        status, item = STATUS_CONFIRMED, ""
    else:
        status, item = STATUS_BOUNDED, "head soffit through the wall thickness not drawn (RADIAL vs PRISMATIC)"
    return dict(face=name, radius=r_face, developed_width=width, radial=rad, prismatic=pri, lo=lo, hi=hi,
                status=status, held_item=item)


def piece_net(face_gross, hole_lo, hole_hi):
    """Wall piece around the hole: gross face minus the hole; net lo takes the larger hole."""
    if hole_lo is None or hole_hi is None:
        raise Refused("MISSING", "hole HELD: the piece is HELD, never gross and never 0")
    if hole_hi > face_gross + 1e-9:
        raise Refused("HOLE_EXCEEDS_FACE", f"{hole_hi:.4f} > {face_gross:.4f}")
    return face_gross - hole_hi, face_gross - hole_lo
