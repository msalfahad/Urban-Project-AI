"""BEAM_SUPPORT_V1 (T-229, unwired, stdlib only; rollback: delete the folder).

Which drawn members SUPPORT a beam and which only START on it, and what a beam line loses or bills twice when it is
cut, or billed through, at the wrong member. ERS s.2-s.3; rule R-CONC-OWN-1 (proposed T-189, applied T-192 / T-220);
rule proposal R-BEAM-CONT-1 (this task, research/agents_t229/R-BEAM-CONT-1.json).

Physical element (drawing-derived method). A beam is one physical member from support to support. A member SUPPORTS
the beam only when it starts below the beam and continues up to its soffit (a column or neck under the slab: SOLID
column hatch on the slab plan of that storey; a bearing wall; a deeper beam the beam frames into). A member that STARTS
on the beam (planted column 'P.C', the turned upper part of a 'T.C': pattern hatch on the slab plan of the storey below
its own) is CARRIED: the beam runs continuous under it at its full section (ST7757.pdf p.15 'BEAM CARRYING PLANTED
COL. DETAIL' draws exactly this) and owns that concrete.

So, for a beam measured as pieces (route G bands):
    gap between two collinear pieces of one beam = the part of the beam the line does not bill.
      covered by SUPPORT members        -> the support owns that part (route G 'column footprint split out'): PASS;
      the part of the gap BESIDE a narrower support, inside the beam's drawn width (beam wider than the column)
                                          -> no line bills it: BEAM_SHORT_BESIDE_SUPPORT (the beam keeps it,
                                             R-CONC-OWN-1 'a gap is never closed by a zero');
      covered only by CARRIED members or by nothing but the beam's own drawn edges
                                          -> CUT_AT_CARRIED (refused cut): the whole gap is beam, BEAM_SHORT;
      no member and no drawn edge across it -> UNDETERMINED (HELD, bounded by the gap, never 0).
    piece end stopping at a CARRIED member's face while the beam's drawn edges continue to a support face
                                          -> END_SHORT_AT_CARRIED: the strip from that face to the support face is beam.
    a SUPPORT footprint billed THROUGH by a beam piece (share >= THROUGH_MIN) while the column line in the same state
    also bills it (full storey interval, or a ledger joint line) -> DOUBLE: owner by R-CONC-OWN-1 precedence
    (column > beam, route G basis 'column footprint split out'), the beam line is over-billed by share x A x D;
    when the column line is built to the soffit of the member billed through it (T-220 record) -> PASS, beam owns.
Missing depth (a projection strip whose section is not printed) -> HELD with the plan area, volume None, never 0.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

SCHEMA = "BEAM_SUPPORT_V1"
UNITS = {"m": 1.0, "cm": 0.01, "mm": 0.001}
THROUGH_MIN = 0.95      # share of a footprint inside a billed piece for 'billed through'
SUPPORT_FULL = 0.95     # share of a gap covered by supports for a pure support cut (rest = fit residual, named)
NET_MAX = 0.02          # share at or below which a member does not occupy the gap / footprint
ANG_TOL_DEG = 1.0       # collinearity of two pieces of one beam
OFF_TOL = 0.03          # m, lateral offset of two pieces of one beam
SUPPORT_KINDS = ("COLUMN_BELOW", "WALL_BELOW", "BEAM_SUPPORT")
CARRIED_KINDS = ("CARRIED_COLUMN",)


class Refused(ValueError):
    """A request the rules refuse (the message names the rule)."""


def to_m(v, unit):
    if v is None:
        return None
    if unit not in UNITS:
        raise Refused(f"UNKNOWN_UNIT: {unit!r}")
    return float(v) * UNITS[unit]


# ---------------------------------------------------------------- plan geometry (convex polygons, stdlib only)
def area(p):
    return 0.5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))


def _ccw(p):
    return p if area(p) > 0 else list(reversed(p))


def clip(subject, clipper):
    """Sutherland-Hodgman: subject polygon clipped by a convex polygon."""
    out = list(subject)
    c = _ccw(list(clipper))
    for i in range(len(c)):
        a, b = c[i], c[(i + 1) % len(c)]
        inside = lambda q: (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0]) >= -1e-12
        def cut(p, q):
            dx, dy = q[0] - p[0], q[1] - p[1]
            den = (b[0] - a[0]) * dy - (b[1] - a[1]) * dx
            t = ((b[0] - a[0]) * (a[1] - p[1]) - (b[1] - a[1]) * (a[0] - p[0])) / den
            return (p[0] + t * dx, p[1] + t * dy)
        inp, out = out, []
        for j in range(len(inp)):
            p, q = inp[j - 1], inp[j]
            if inside(q):
                if not inside(p):
                    out.append(cut(p, q))
                out.append(q)
            elif inside(p):
                out.append(cut(p, q))
        if not out:
            return []
    return out


def inter_area(a, b):
    """Area of the intersection of two convex polygons."""
    r = clip(_ccw(list(a)), b)
    return abs(area(r)) if len(r) >= 3 else 0.0


def rect(cx, cy, w, d, angle_deg=0.0, mirror=False):
    """Rectangle w (along the local x) x d centred on (cx, cy), turned by angle_deg; mirror flips x."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for x, y in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
        X, Y = cx + x * ca - y * sa, cy + x * sa + y * ca
        pts.append((-X, Y) if mirror else (X, Y))
    return _ccw(pts)


# ---------------------------------------------------------------- beam pieces
@dataclass
class Piece:
    """One billed piece of a beam: axis p0 -> p1 (m), width and depth (m; depth None = not printed)."""
    id: str
    mark: str
    p0: tuple
    p1: tuple
    width: float
    depth: float | None = None
    beam: str = ""              # physical beam id (pieces of one beam share it)

    @property
    def length(self):
        return math.dist(self.p0, self.p1)

    @property
    def u(self):
        L = self.length
        return ((self.p1[0] - self.p0[0]) / L, (self.p1[1] - self.p0[1]) / L)

    def face(self, end):
        """End face (two points) at end 0 (p0) or 1 (p1)."""
        c = self.p0 if end == 0 else self.p1
        n = (-self.u[1] * self.width / 2, self.u[0] * self.width / 2)
        return (c[0] - n[0], c[1] - n[1]), (c[0] + n[0], c[1] + n[1])

    def plan(self):
        a0, a1 = self.face(0)
        b0, b1 = self.face(1)
        return _ccw([a0, b0, b1, a1])


def piece_from_quad(pid, mark, pts, depth=None, beam=""):
    """A billed rectangle given as 4 corners -> Piece (axis along the long side)."""
    q = [tuple(p) for p in pts]
    if len(q) == 5 and q[0] == q[-1]:
        q = q[:-1]
    if len(q) != 4:
        raise Refused(f"NOT_A_RECTANGLE: {pid} has {len(q)} corners")
    e01, e12 = math.dist(q[0], q[1]), math.dist(q[1], q[2])
    if e01 >= e12:   # long sides 0-1 and 2-3; ends 1-2 and 3-0
        m0 = ((q[3][0] + q[0][0]) / 2, (q[3][1] + q[0][1]) / 2)
        m1 = ((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2)
        w = e12
    else:
        m0 = ((q[0][0] + q[1][0]) / 2, (q[0][1] + q[1][1]) / 2)
        m1 = ((q[2][0] + q[3][0]) / 2, (q[2][1] + q[3][1]) / 2)
        w = e01
    return Piece(pid, mark, m0, m1, w, depth, beam)


def _ang(u, v):
    return math.degrees(math.acos(max(-1.0, min(1.0, abs(u[0] * v[0] + u[1] * v[1])))))


def collinear(a: Piece, b: Piece, ang_tol=ANG_TOL_DEG, off_tol=OFF_TOL):
    if _ang(a.u, b.u) > ang_tol:
        return False
    n = (-a.u[1], a.u[0])
    off = lambda p: (p[0] - a.p0[0]) * n[0] + (p[1] - a.p0[1]) * n[1]
    return abs(off(b.p0)) <= off_tol and abs(off(b.p1)) <= off_tol


def gap(a: Piece, b: Piece):
    """The unbilled part of one beam between two collinear pieces: quad between their facing end faces.
    Returns (polygon, axial length, width) or None when they overlap or touch."""
    if not collinear(a, b):
        raise Refused(f"NOT_COLLINEAR: {a.id} / {b.id} are not two pieces of one straight beam")
    u, o = a.u, a.p0
    n = (-u[1], u[0])
    s = lambda p: (p[0] - o[0]) * u[0] + (p[1] - o[1]) * u[1]
    ia, ib = sorted((s(a.p0), s(a.p1))), sorted((s(b.p0), s(b.p1)))
    if ib[0] < ia[0]:
        ia, ib = ib, ia
    s0, s1 = ia[1], ib[0]
    if s1 - s0 <= 1e-6:
        return None
    w = min(a.width, b.width)
    q = lambda t, k: (o[0] + u[0] * t + n[0] * k * w / 2, o[1] + u[1] * t + n[1] * k * w / 2)
    return _ccw([q(s0, -1), q(s1, -1), q(s1, 1), q(s0, 1)]), s1 - s0, w


def extension(p: Piece, end, members, reach=2.0):
    """Strip of the beam beyond end `end` of piece p up to the first SUPPORT member face inside the beam width.
    Returns (polygon, length, support id) or None when no support lies within reach."""
    c = p.p0 if end == 0 else p.p1
    d = (-p.u[0], -p.u[1]) if end == 0 else p.u
    n = (-d[1] * p.width / 2, d[0] * p.width / 2)
    best = None
    for m in members:
        if m.kind not in SUPPORT_KINDS:
            continue
        far = (c[0] + d[0] * reach, c[1] + d[1] * reach)
        strip = _ccw([(c[0] - n[0], c[1] - n[1]), (c[0] + n[0], c[1] + n[1]),
                      (far[0] + n[0], far[1] + n[1]), (far[0] - n[0], far[1] - n[1])])
        part = clip(_ccw(list(m.plan)), strip)
        if len(part) < 3 or abs(area(part)) <= 1e-9:
            continue
        t = min((q[0] - c[0]) * d[0] + (q[1] - c[1]) * d[1] for q in part)
        if t > 1e-6 and (best is None or t < best[0]):
            best = (t, m.id)
    if best is None:
        return None
    t = best[0]
    sup = next(m for m in members if m.id == best[1])
    # far contact: the support face may cross the beam obliquely; take the contact on each lateral edge of the beam
    t_far = t
    for k in (-1, 1):
        e0 = (c[0] + k * n[0] * 0.999, c[1] + k * n[1] * 0.999)
        e1 = (c[0] + k * n[0] * 0.997, c[1] + k * n[1] * 0.997)
        far0 = (e0[0] + d[0] * reach, e0[1] + d[1] * reach)
        far1 = (e1[0] + d[0] * reach, e1[1] + d[1] * reach)
        part = clip(_ccw(list(sup.plan)), _ccw([e0, e1, far1, far0]))
        if len(part) >= 3:
            t_far = max(t_far, min((q[0] - c[0]) * d[0] + (q[1] - c[1]) * d[1] for q in part))
    box_ = _ccw([(c[0] - n[0], c[1] - n[1]), (c[0] + n[0], c[1] + n[1]),
                 (c[0] + d[0] * t_far + n[0], c[1] + d[1] * t_far + n[1]),
                 (c[0] + d[0] * t_far - n[0], c[1] + d[1] * t_far - n[1])])
    beam_area = abs(area(box_)) - inter_area(sup.plan, box_)
    poly = _ccw([(c[0] - n[0], c[1] - n[1]), (c[0] + n[0], c[1] + n[1]),
                 (c[0] + d[0] * t + n[0], c[1] + d[1] * t + n[1]), (c[0] + d[0] * t - n[0], c[1] + d[1] * t - n[1])])
    return poly, t, best[1], beam_area, t_far


@dataclass
class Member:
    """A drawn member near a beam: kind COLUMN_BELOW / WALL_BELOW / BEAM_SUPPORT (supports), CARRIED_COLUMN (starts on
    the beam), PROJECTION (outer strip, section unprinted)."""
    id: str
    kind: str
    plan: list


def shares(region, members):
    """Share of a region's area covered by each member kind (members do not overlap each other)."""
    A = abs(area(region))
    if A <= 0:
        raise Refused("EMPTY_REGION")
    out = {}
    for m in members:
        s = inter_area(m.plan, region) / A
        if s > 1e-9:
            out.setdefault(m.kind, 0.0)
            out[m.kind] += s
            out.setdefault("ids", []).append((m.id, m.kind, round(s, 4)))
    return out


# ---------------------------------------------------------------- record-level evaluation (no coordinates)
def _vol(a, d):
    return None if d is None or a is None else a * d


def classify_gap(g: dict) -> dict:
    """g: {area_m2, support_share, carried_share, other_beam_share, depth_m, edges_continuous (bool | None),
    projection (bool), width_conflict (bool)}.
    Returns the class, the parts in m2 and the beam volume the line loses (m3; None = HELD, never 0)."""
    A = g["area_m2"]
    if A is None or A < 0:
        raise Refused("GAP_AREA_MISSING")
    sup = g.get("support_share", 0.0) or 0.0
    car = g.get("carried_share", 0.0) or 0.0
    oth = g.get("other_beam_share", 0.0) or 0.0
    d = g.get("depth_m")
    edges = g.get("edges_continuous")
    if sup + car + oth > 1.0 + 0.02:
        raise Refused("SHARES_EXCEED_GAP: supports, carried members and other beams overlap the same plan")
    under_sup = A * min(sup, 1.0)
    under_car = A * car
    other = A * oth
    beside = max(A - under_sup - under_car - other, 0.0)
    rec = {"area_m2": A, "under_support_m2": under_sup, "under_carried_m2": under_car, "other_beam_m2": other,
           "beside_m2": beside}
    if g.get("projection"):
        rec.update(cls="PROJECTION_CUT", status="HELD", short_m3=None,
                   reason="outer projection strip, section not printed: plan kept, volume HELD (never 0)")
        return rec
    if sup >= SUPPORT_FULL:
        rec.update(cls="SUPPORT_CUT", status="PASS", short_m3=0.0, residual_m2=beside,
                   reason="cut at a member that supports the beam; the support owns the footprint")
        return rec
    if sup > NET_MAX:
        if g.get("width_conflict"):
            rec.update(cls="SUPPORT_CUT_BESIDE", status="HELD", short_m3=None, bound_m3=_vol(beside, d),
                       reason="the beam's width is a printed / drawn CONFLICT: the part beside the support exists only "
                              "on the wider reading (HELD on the designer answer)")
            return rec
        if edges is not True:
            rec.update(cls="SUPPORT_CUT_BESIDE", status="HELD", short_m3=None, bound_m3=_vol(beside, d),
                       reason="beam wider than its support; drawn beam edges across the support not confirmed")
            return rec
        rec.update(cls="SUPPORT_CUT_BESIDE", status="BEAM_SHORT" if d is not None else "HELD",
                   short_m3=_vol(beside + under_car, d),
                   reason="beam wider than its support: the part beside the support inside the drawn beam width is "
                          "billed by no line; the beam keeps it (R-CONC-OWN-1)")
        return rec
    if car > NET_MAX or edges is True:
        if edges is False:
            rec.update(cls="CUT_AT_CARRIED", status="HELD", short_m3=None, bound_m3=_vol(A, d),
                       reason="cut at a member that starts on the beam, but the beam edges are not drawn across it")
            return rec
        rec.update(cls="CUT_AT_CARRIED", status="BEAM_SHORT" if d is not None else "HELD", short_m3=_vol(A, d),
                   reason="cut refused: the member starts ON the beam (it does not support it); the beam is "
                          "continuous under it and owns the whole gap (R-BEAM-CONT-1, R-CONC-OWN-1)")
        return rec
    rec.update(cls="CUT_NO_MEMBER", status="HELD", short_m3=None, bound_m3=_vol(A, d),
               reason="no member and no drawn edge across the gap: UNDETERMINED, bounded, never 0")
    return rec


SQUARE_MAX_M2 = 0.002   # beyond-face area at or below which the end is square to its member (fit residual)
EDGE_FULL = 0.9         # drawn-edge cover of each beam side for a confirmed shortfall
EDGE_NONE = 0.5         # below this the beam is drawn ending at the face (no shortfall)


def classify_end(e: dict) -> dict:
    """e: {touch, beyond_area_m2, beyond_closed, beyond_edge_cover [2], depth_m}.
    touch = what the end face rests on: SUPPORT / BEAM / JUNCTION_OWNER / OVER_SUPPORT / CARRIED / PROJECTION / NONE.
    beyond = the strip of the beam's width beyond the face, bounded by the members the beam frames into (a member the
    beam CARRIES does not bound it); its area is the drawn beam no line bills when the drawn beam edges run on over it.
      area <= SQUARE_MAX_M2 or the strip is open (no member closes it)  -> square end: PASS (END_AT_<touch>, END_FREE)
      edges cover both sides >= EDGE_FULL                               -> END_SHORT (BEAM_SHORT, the beam keeps it)
      edges cover a side < EDGE_NONE                                     -> the drawn beam ends at the face: PASS
      otherwise                                                          -> HELD, bounded by area x D (never 0)
    PROJECTION ends are HELD (outer strip, section unprinted)."""
    t = e["touch"]
    d = e.get("depth_m")
    if t == "PROJECTION":
        return {"cls": "END_AT_PROJECTION", "status": "HELD", "short_m3": None,
                "reason": "outer projection strip, section not printed (D-26)"}
    if t not in ("SUPPORT", "BEAM", "JUNCTION_OWNER", "OVER_SUPPORT", "CARRIED", "NONE"):
        raise Refused(f"UNKNOWN_END_TOUCH: {t!r}")
    A = e.get("beyond_area_m2")
    if A is None:
        raise Refused("BEYOND_NOT_MEASURED: every end needs its beyond-face measure")
    base = "END_FREE" if t == "NONE" else f"END_AT_{t}"
    if A <= SQUARE_MAX_M2 or not e.get("beyond_closed", False):
        if t == "CARRIED":
            return {"cls": "END_SHORT_AT_CARRIED_NO_SUPPORT", "status": "HELD", "short_m3": None,
                    "reason": "the piece stops at a member it carries and no support closes the beam behind it"}
        return {"cls": base, "status": "PASS", "short_m3": 0.0}
    cov = e.get("beyond_edge_cover") or [0.0, 0.0]
    cls = ("END_SHORT_AT_CARRIED" if t == "CARRIED" else "END_SHORT_OBLIQUE" if t in ("SUPPORT", "BEAM",
                                                                                       "JUNCTION_OWNER")
           else "END_SHORT_OF_MEMBER")
    if min(cov) >= EDGE_FULL:
        return {"cls": cls, "status": "BEAM_SHORT" if d is not None else "HELD", "short_m3": _vol(A, d),
                "beyond_area_m2": A,
                "reason": "the drawn beam runs on past the billed face to the member it frames into; no line bills "
                          "it, the beam keeps it (R-BEAM-CONT-1, R-CONC-OWN-1)"}
    if min(cov) < EDGE_NONE and t != "CARRIED":
        return {"cls": base, "status": "PASS", "short_m3": 0.0, "reason": "the drawn beam ends at the billed face"}
    return {"cls": cls, "status": "HELD", "short_m3": None, "bound_m3": _vol(A, d), "beyond_area_m2": A,
            "reason": "drawn beam edges cover the strip only in part: bounded, HELD"}


def joint_ownership(share, A_col, beam_depth, column_basis):
    """A support footprint (area A_col) and a beam piece that covers `share` of it, beam depth D.
    column_basis: FULL_INTERVAL (column line to the slab top), JOINT_LINE (ledger: column to D_ctrl + joint + head),
    TO_THROUGH_SOFFIT (column built to the soffit of the member billed through it), NONE (no column line)."""
    if share is None or A_col is None:
        raise Refused("FOOTPRINT_OR_SHARE_MISSING")
    if share < THROUGH_MIN:
        if share <= NET_MAX:
            return {"result": "PASS", "owner": "column", "double_m3": 0.0}
        part = share * A_col
        v = _vol(part, beam_depth)
        if column_basis in ("FULL_INTERVAL", "JOINT_LINE"):
            return {"result": "DOUBLE_PARTIAL", "owner": "column (precedence column > beam)", "double_m3": v,
                    "beam_overbilled_m3": v}
        return {"result": "PASS", "owner": "beam", "double_m3": 0.0}
    v = _vol(share * A_col, beam_depth)
    if column_basis in ("FULL_INTERVAL", "JOINT_LINE"):
        return {"result": "DOUBLE", "owner": "column (precedence column > beam; route G basis 'column footprint "
                                             "split out')", "double_m3": v, "beam_overbilled_m3": v}
    if column_basis == "TO_THROUGH_SOFFIT":
        return {"result": "PASS", "owner": "beam (billed through; the column stops at its soffit)", "double_m3": 0.0}
    if column_basis == "NONE":
        return {"result": "PASS", "owner": "beam (no column line in this state)", "double_m3": 0.0}
    raise Refused(f"UNKNOWN_COLUMN_BASIS: {column_basis!r}")


def beam_run(pieces_m3, gaps, ends=()):
    """One physical beam: billed piece volumes + every gap / end record (from classify_*). Returns the billed volume,
    the drawing-derived continuous volume when nothing is HELD, else HELD with the bound."""
    billed = sum(pieces_m3)
    shorts = [g.get("short_m3") for g in list(gaps) + list(ends)]
    held = [g for g in list(gaps) + list(ends) if g.get("status") == "HELD"]
    add = sum(s for s in shorts if s)
    if held:
        bound = sum(g.get("bound_m3") or 0.0 for g in held)
        return {"billed_m3": billed, "drawing_m3": None, "status": "HELD", "confirmed_short_m3": add,
                "held_bound_m3": bound if all(g.get("bound_m3") is not None for g in held) else None}
    return {"billed_m3": billed, "drawing_m3": billed + add, "short_m3": add,
            "status": "DRAWING-CONFIRMED" if add or gaps or ends else "AGREE"}


def check_claim(run: dict, claimed_m3, tol=1e-4):
    """Refuse a single figure that keeps a refused cut (billed only), or that releases a HELD run, or a missing as 0."""
    if claimed_m3 is None:
        raise Refused("MISSING_AS_NONE_NOT_A_CLAIM")
    if run["status"] == "HELD":
        raise Refused("HELD_RUN: a held beam run has no single released figure")
    if claimed_m3 == 0:
        raise Refused("MISSING_AS_ZERO")
    if abs(claimed_m3 - run["drawing_m3"]) > tol:
        if abs(claimed_m3 - run["billed_m3"]) <= tol and run.get("short_m3", 0) > tol:
            raise Refused("CUT_AT_CARRIED_MEMBER: the claim is the billed pieces only; the beam is continuous")
        raise Refused(f"DIFFERS: {claimed_m3} vs drawing-derived {run['drawing_m3']}")
    return True


def check_joint_claims(lines: list, tol=1e-6):
    """lines: [{line, contains_joint: bool, m3}] for one physical junction. Refuse a junction billed in two lines."""
    inside = [l for l in lines if l.get("contains_joint")]
    if len(inside) > 1:
        raise Refused("JOINT_OWNED_TWICE: " + " + ".join(l["line"] for l in inside))
    if not inside:
        raise Refused("JOINT_OWNED_BY_NONE: a gap is never closed by a zero")
    return inside[0]["line"]
