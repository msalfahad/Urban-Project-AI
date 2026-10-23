"""CURVED_GEOMETRY_CHECK_V1 (T-197, residential review R4): curved and partial geometry completeness.

A pure CHECK, NOT wired into any method version (ARCH_TAKEOFF_V2.9 .. V3.0.x and route G are unchanged): it produces
issue rows, never a BOQ quantity. Standard library only; imports no engine module. Any villa.

Why (PROJECT_UNDERSTANDING_ASSESSMENT s.6 R4; ENGINEERING_REASONING_STANDARD s.3: the basis of a measure before its
arithmetic): an element that follows an arc on plan has several honest lengths (outer arc, inner arc, a face arc, the
centreline arc, the chord of each, the chord an elevation projects) and two honest plan areas (the true area with its arcs,
the chord polygon). Four times on the development villa a line was measured as a straight strip, on an unnamed basis, on
part of the arc only, or twice on the same arc. This module names, for every ledger / candidate line on a curved element,
the basis its value actually matches, and raises:

  BASIS_UNNAMED   the line does not say which basis it measures (the matching candidates are listed)
  BASIS_MISMATCH  the line names a basis but its value is another one (or none)
  STRAIGHTENED    a chord basis (or a value that only a chord explains) on a QUANTITY line of an element that follows
                  the arc (an elevation / identity chord is not a quantity and is not flagged)
  PARTIAL         only part of the curved outline is measured: the line covers a strict subset of the arcs, or its
                  value equals the straight parts alone, or it is below every basis; element level: the lines of an
                  expected family leave part of the element's arcs uncovered
  OVER_OUTLINE    the value exceeds every basis of the true outline (a region tool leaking past the drawn face)
  DOUBLE_ARC      two ACTIVE quantity lines of one BOQ family measure the same arc (same circle, overlapping sweep,
                  and for plan areas the material on the same side of it)
  NOT_MEASURED    an element of an expected family that no active line of that family touches (information)

Geometry input (one element = one physical element, ELEMENT_REGISTER id where one exists):
  {"element_id", "kind": WALL | WALL_FACE | PARAPET | SLAB_EDGE | OPENING | ROOM_CONTOUR | RING | POOL_WALL | OTHER,
   "units": "m" | "mm" (required: nothing is guessed), "ref": sheet / file / layer / handles (required),
   "follows_arc": True (default) | False (built straight although drawn on a curve),
   "pieces": [piece, ...], "loops": [{"pieces": [piece ids], "hole": bool}, ...] (needed for plan areas),
   "expected_families": [BOQ family, ...] (optional: element-level coverage)}
  piece = {"piece_id", "role": OUTER | INNER | FACE | CENTRELINE | GAP, one of
             {"line": [(x, y), (x, y)]}
             {"centre", "radius", "start", "end", "mid"} (realised arc: three points fix the sweep side)
             {"centre", "radius", "start_angle", "end_angle", "extrusion_z"} (DXF ARC, OCS, degrees, CCW about the
                                                                               extrusion)
             {"a", "b", "bulge", "extrusion_z"} (one LWPOLYLINE span, OCS)}
  OUTER / INNER are the larger / smaller radius curve of a band (owner Q-39 wording), FACE a single drawn face (a room
  contour, a facade side), CENTRELINE an explicitly drawn centreline, GAP a virtual closing line (a door gap in a room
  contour). An OCS with extrusion_z < 0 (a mirrored entity) maps (x, y) -> (-x, y): the bulge side flips with it
  (historical defect B1 is about exactly this side).

Line input (one ledger / candidate line):
  {"line_id", "element_id", "family" (BOQ family, e.g. CONC.BEAM, OPENING_SUPPLY), "measure": LENGTH | PLAN_AREA,
   "value", "units", "basis": OUTER_ARC | INNER_ARC | FACE_ARC | CENTRELINE_ARC | CHORD | PROJECTED_CHORD |
   TRUE_AREA | CHORD_AREA | None, "chord_role" (role of the chord for CHORD / PROJECTED_CHORD),
   "purpose": QUANTITY | IDENTITY, "covers": [piece ids] | None (None = the whole element),
   "deductions" (what the line states it subtracted, same unit; default 0), "status": ACTIVE | SUPERSEDED,
   "chord_rule": a cited owner rule that sets a chord (then CHORD_BY_RULE, information, never STRAIGHTENED), "ref"}

Guards (ValueError: a wrong input never becomes a finding): units missing or not m / mm; a radius above 500 m or a
line above 1 km (millimetres given as metres); a realised arc whose points are not on its circle; coincident arc ends
with no mid point (full circle or nothing cannot be told); a mid point contradicting a stated direction; an unknown
role / basis / measure / purpose / status; a CHORD basis without chord_role; a line on an unknown element or covering
an unknown piece; a PLAN_AREA line on an element without loops; a loop that does not close.
"""

from __future__ import annotations

import math

METHOD = "CURVED_GEOMETRY_CHECK_V1"
RULES = ("ENGINEERING_REASONING_STANDARD.md s.3 (the basis of a measure before its arithmetic)",
         "proposed UP-CURVE-BASIS-001 (every line on a curved element names its basis; T-197)",
         "proposed UP-OPEN-CONSIST-001 (basis named per line; T-194)",
         "owner Q-39 C (a window curved on plan: outer arc for the supply measure)",
         "WORKFLOW_CONTROLS s.5 (findings hold lines, never become 0)")

ROLES = ("OUTER", "INNER", "FACE", "CENTRELINE", "GAP")
KINDS = ("WALL", "WALL_FACE", "PARAPET", "SLAB_EDGE", "OPENING", "ROOM_CONTOUR", "RING", "POOL_WALL", "OTHER")
MEASURES = ("LENGTH", "PLAN_AREA")
PURPOSES = ("QUANTITY", "IDENTITY")
STATUSES = ("ACTIVE", "SUPERSEDED")
LENGTH_BASES = {"OUTER_ARC": ("ARC", "OUTER"), "INNER_ARC": ("ARC", "INNER"), "FACE_ARC": ("ARC", "FACE"),
                "CENTRELINE_ARC": ("ARC", "CENTRELINE"), "CHORD": ("CHORD", None), "PROJECTED_CHORD": ("CHORD", None)}
AREA_BASES = {"TRUE_AREA": "TRUE", "CHORD_AREA": "CHORD"}
CODES = ("BASIS_UNNAMED", "BASIS_MISMATCH", "STRAIGHTENED", "PARTIAL", "OVER_OUTLINE", "DOUBLE_ARC", "NOT_MEASURED",
         "CHORD_BY_RULE")
TOL_LEN = 0.01        # m: a line within 1 cm of a basis matches it; 2 cm does not
TOL_AREA = 0.01       # m2
TOL_POINT = 5e-4      # m: an arc end / mid point within 0.5 mm of its circle; loop ends within 0.5 mm close
TOL_CIRCLE = 1e-3     # m: two arcs on the same circle (centre and radius within 1 mm)
MAX_RADIUS_M = 500.0
MAX_LINE_M = 1000.0
TWO_PI = 2.0 * math.pi
SCALE = {"m": 1.0, "mm": 0.001}


# ------------------------------------------------------------------------------------------------------- geometry
def _scale(units, what):
    if units not in SCALE:
        raise ValueError(f"{what}: units must be 'm' or 'mm', got {units!r} (nothing is guessed)")
    return SCALE[units]


def _pt(p, k, what):
    if p is None or len(p) < 2:
        raise ValueError(f"{what}: point missing")
    return (float(p[0]) * k, float(p[1]) * k)


def _ocs(p, z):
    """OCS -> WCS in plan for a plan-normal extrusion: (0, 0, -1) maps x to -x (arbitrary axis algorithm)."""
    return (-p[0], p[1]) if z < 0 else (p[0], p[1])


def _ang(c, p):
    return math.atan2(p[1] - c[1], p[0] - c[0])


class Arc:
    """A circular arc in WCS metres: centre, radius, start angle, signed sweep (+ = CCW in plan)."""

    __slots__ = ("centre", "r", "a0", "sweep", "start", "end", "mid")

    def __init__(self, centre, r, a0, sweep):
        self.centre, self.r, self.a0, self.sweep = centre, r, a0, sweep
        self.start = self.at(0.0)
        self.end = self.at(1.0)
        self.mid = self.at(0.5)

    def at(self, t):
        a = self.a0 + self.sweep * t
        return (self.centre[0] + self.r * math.cos(a), self.centre[1] + self.r * math.sin(a))

    @property
    def length(self):
        return self.r * abs(self.sweep)

    @property
    def chord(self):
        return math.dist(self.start, self.end)

    @property
    def segment(self):
        """Area between the arc and its chord: r^2 / 2 (theta - sin theta)."""
        th = abs(self.sweep)
        return self.r * self.r / 2.0 * (th - math.sin(th))

    def reversed(self):
        return Arc(self.centre, self.r, self.a0 + self.sweep, -self.sweep)

    def interval(self):
        """CCW angular interval [lo, lo + width) with lo in [0, 2 pi)."""
        if self.sweep >= 0:
            return self.a0 % TWO_PI, self.sweep
        return (self.a0 + self.sweep) % TWO_PI, -self.sweep


def arc_from_points(centre, r, start, end, mid=None, direction=None, what="arc"):
    """Realised arc (three points). The mid point fixes the side; without it the stated direction does."""
    if r <= 0:
        raise ValueError(f"{what}: radius must be > 0")
    for name, p in (("start", start), ("end", end), ("mid", mid)):
        if p is not None and abs(math.dist(centre, p) - r) > TOL_POINT + 1e-9 * r:
            raise ValueError(f"{what}: {name} point is {math.dist(centre, p) - r:+.6f} m off its circle")
    a_s, a_e = _ang(centre, start), _ang(centre, end)
    ccw = (a_e - a_s) % TWO_PI
    closed = math.dist(start, end) <= TOL_POINT
    if mid is None:
        if closed:
            raise ValueError(f"{what}: start = end and no mid point: a full circle or nothing cannot be told")
        if direction not in ("CCW", "CW"):
            raise ValueError(f"{what}: give a mid point or a direction (CCW / CW)")
        sweep = ccw if direction == "CCW" else -(TWO_PI - ccw)
        return Arc(centre, r, a_s, sweep)
    off = (_ang(centre, mid) - a_s) % TWO_PI
    if closed:
        # start = end with a mid point on the circle: a full circle; its sense only from a stated direction
        sweep = -TWO_PI if direction == "CW" else TWO_PI
    else:
        sweep = ccw if off < ccw else -(TWO_PI - ccw)
    if direction in ("CCW", "CW") and not closed and (sweep > 0) != (direction == "CCW"):
        raise ValueError(f"{what}: the mid point says {'CCW' if sweep > 0 else 'CW'}, the record says {direction}")
    return Arc(centre, r, a_s, sweep)


def arc_from_dxf_arc(centre, r, start_angle, end_angle, extrusion_z=1.0, what="ARC"):
    """DXF ARC: OCS centre, degrees, CCW about the extrusion; 360 deg when the angles are equal."""
    sw = math.radians((end_angle - start_angle) % 360.0 or 360.0)
    a0 = math.radians(start_angle)
    pts = [(centre[0] + r * math.cos(a0 + sw * t), centre[1] + r * math.sin(a0 + sw * t)) for t in (0.0, 0.5, 1.0)]
    c = _ocs(centre, extrusion_z)
    s, m, e = (_ocs(p, extrusion_z) for p in pts)
    if abs(sw - TWO_PI) < 1e-12:
        return Arc(c, r, _ang(c, s), TWO_PI if extrusion_z >= 0 else -TWO_PI)
    return arc_from_points(c, r, s, e, m, what=what)


def arc_from_bulge(a, b, bulge, extrusion_z=1.0, what="bulge"):
    """One LWPOLYLINE span A -> B with bulge = tan(theta / 4); positive = CCW about the extrusion (OCS)."""
    c = math.dist(a, b)
    if c <= 0:
        raise ValueError(f"{what}: coincident span ends")
    th = 4.0 * math.atan(abs(bulge))
    r = c / (2.0 * math.sin(th / 2.0))
    s = abs(bulge) * c / 2.0                                    # sagitta
    mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    nx, ny = -(b[1] - a[1]) / c, (b[0] - a[0]) / c              # left normal of A -> B
    sg = 1.0 if bulge > 0 else -1.0
    mid = (mx - sg * nx * s, my - sg * ny * s)                  # a CCW span lies to the right of its chord
    ux, uy = mx - mid[0], my - mid[1]
    k = r / math.hypot(ux, uy)
    centre = (mid[0] + ux * k, mid[1] + uy * k)
    A, B, M, C = (_ocs(p, extrusion_z) for p in (a, b, mid, centre))
    return arc_from_points(C, r, A, B, M, what=what)


def pieces_from_polyline(prefix, role, vertices, closed=False, extrusion_z=1.0):
    """[(x, y, bulge), ...] in OCS -> ordered pieces (bulge on the vertex that starts the span)."""
    out, n = [], len(vertices)
    spans = range(n) if closed else range(n - 1)
    for i in spans:
        x0, y0, b0 = vertices[i]
        x1, y1 = vertices[(i + 1) % n][:2]
        pid = f"{prefix}.{i}"
        if abs(b0) < 1e-12:
            out.append({"piece_id": pid, "role": role,
                        "line": [_ocs((x0, y0), extrusion_z), _ocs((x1, y1), extrusion_z)]})
        else:
            out.append({"piece_id": pid, "role": role, "a": (x0, y0), "b": (x1, y1), "bulge": b0,
                        "extrusion_z": extrusion_z})
    return out


class Piece:
    __slots__ = ("pid", "role", "arc", "a", "b")

    def __init__(self, pid, role, arc=None, a=None, b=None):
        self.pid, self.role, self.arc = pid, role, arc
        self.a, self.b = (arc.start, arc.end) if arc is not None else (a, b)

    @property
    def length(self):
        return self.arc.length if self.arc is not None else math.dist(self.a, self.b)

    @property
    def chord(self):
        return math.dist(self.a, self.b)


def _piece(rec, k, eid):
    pid = rec.get("piece_id")
    if not pid:
        raise ValueError(f"{eid}: every piece has a piece_id")
    role = rec.get("role")
    if role not in ROLES:
        raise ValueError(f"{eid} / {pid}: role {role!r} not in {ROLES}")
    what = f"{eid} / {pid}"
    if "line" in rec:
        a, b = _pt(rec["line"][0], k, what), _pt(rec["line"][1], k, what)
        if math.dist(a, b) > MAX_LINE_M:
            raise ValueError(f"{what}: a {math.dist(a, b):.1f} m line: millimetres given as metres?")
        return Piece(pid, role, a=a, b=b)
    z = float(rec.get("extrusion_z", 1.0))
    if "bulge" in rec:
        arc = arc_from_bulge(_pt(rec["a"], k, what), _pt(rec["b"], k, what), float(rec["bulge"]), z, what)
    elif "start_angle" in rec:
        arc = arc_from_dxf_arc(_pt(rec["centre"], k, what), float(rec["radius"]) * k, float(rec["start_angle"]),
                               float(rec["end_angle"]), z, what)
    elif "start" in rec:
        mid = _pt(rec["mid"], k, what) if rec.get("mid") is not None else None
        arc = arc_from_points(_pt(rec["centre"], k, what), float(rec["radius"]) * k, _pt(rec["start"], k, what),
                              _pt(rec["end"], k, what), mid, rec.get("direction"), what)
    else:
        raise ValueError(f"{what}: a piece is a line, a realised arc, a DXF ARC or a bulge span")
    if arc.r > MAX_RADIUS_M:
        raise ValueError(f"{what}: radius {arc.r:.1f} m: millimetres given as metres?")
    return Piece(pid, role, arc=arc)


def _loop_signed_area(pieces):
    """Chain the pieces end to end (each may be reversed) and return the signed area: shoelace of the chord polygon
    plus sign(sweep) x segment of every arc, both in traversal order; plus the oriented pieces."""
    if not pieces:
        raise ValueError("an empty loop")
    rest = list(pieces)
    first = rest.pop(0)
    chain = [(first, False)]
    cur = first.b
    while rest:
        for i, p in enumerate(rest):
            if math.dist(p.a, cur) <= TOL_POINT:
                chain.append((p, False)); cur = p.b; rest.pop(i); break
            if math.dist(p.b, cur) <= TOL_POINT:
                chain.append((p, True)); cur = p.a; rest.pop(i); break
        else:
            raise ValueError(f"loop does not close: no piece starts at {cur} (after {chain[-1][0].pid})")
    if math.dist(cur, first.a) > TOL_POINT:
        raise ValueError(f"loop does not close: {math.dist(cur, first.a):.6f} m gap at {first.pid}")
    area = 0.0
    for p, rev in chain:
        a, b = (p.b, p.a) if rev else (p.a, p.b)
        area += (a[0] * b[1] - b[0] * a[1]) / 2.0
        if p.arc is not None:
            sw = -p.arc.sweep if rev else p.arc.sweep
            area += math.copysign(p.arc.segment, sw)
    return area, chain


class Element:
    def __init__(self, rec):
        eid = rec.get("element_id")
        if not eid:
            raise ValueError("every element has an element_id")
        self.eid = eid
        if not rec.get("ref"):
            raise ValueError(f"{eid}: every element names its drawing reference (ref)")
        if rec.get("kind") not in KINDS:
            raise ValueError(f"{eid}: kind {rec.get('kind')!r} not in {KINDS}")
        self.kind, self.ref = rec["kind"], rec["ref"]
        k = _scale(rec.get("units"), eid)
        self.follows_arc = rec.get("follows_arc", True) is not False
        self.expected = tuple(rec.get("expected_families") or ())
        self.pieces = {}
        for pr in rec.get("pieces") or ():
            p = _piece(pr, k, eid)
            if p.pid in self.pieces:
                raise ValueError(f"{eid}: piece {p.pid} twice")
            self.pieces[p.pid] = p
        self.loops = []                     # (signed area, hole, chain)
        for lp in rec.get("loops") or ():
            ids = lp.get("pieces") or ()
            unknown = [i for i in ids if i not in self.pieces]
            if unknown:
                raise ValueError(f"{eid}: loop names unknown pieces {unknown}")
            try:
                area, chain = _loop_signed_area([self.pieces[i] for i in ids])
            except ValueError as exc:
                raise ValueError(f"{eid}: {exc}") from None
            self.loops.append((area, bool(lp.get("hole")), chain))
        self.side = {}                      # piece id -> IN / OUT: material inside / outside the arc's circle
        for area, hole, chain in self.loops:
            o = 1.0 if area > 0 else -1.0
            for p, rev in chain:
                if p.arc is None:
                    continue
                sw = -p.arc.sweep if rev else p.arc.sweep
                inside = (sw > 0) == (o > 0)
                if hole:
                    inside = not inside
                self.side[p.pid] = "IN" if inside else "OUT"

    def _band(self):
        o = [p.arc for p in self.pieces.values() if p.arc is not None and p.role == "OUTER"]
        i = [p.arc for p in self.pieces.values() if p.arc is not None and p.role == "INNER"]
        if not o or not i:
            return False
        c = o[0].centre
        if any(math.dist(a.centre, c) > TOL_CIRCLE for a in o + i):
            return False
        return abs(sum(abs(a.sweep) for a in o) - sum(abs(a.sweep) for a in i)) <= 1e-6

    @property
    def curved(self):
        return any(p.arc is not None for p in self.pieces.values())

    def arcs(self, covers=None, roles=None):
        return [p for p in self.pieces.values() if p.arc is not None and (covers is None or p.pid in covers)
                and (roles is None or p.role in roles)]

    # ---------------------------------------------------------------- candidate values (geometry, never a quantity)
    def length_candidates(self, covers=None):
        out = {}
        ps = [p for p in self.pieces.values() if covers is None or p.pid in covers]
        roles = sorted({p.role for p in ps if p.role != "GAP"})
        gap = sum(p.length for p in ps if p.role == "GAP")
        for role in roles:
            rp = [p for p in ps if p.role == role]
            if not any(p.arc is not None for p in rp):
                out[f"ARC:{role}"] = sum(p.length for p in rp) + gap
                continue
            out[f"ARC:{role}"] = sum(p.length for p in rp) + gap
            out[f"CHORD:{role}"] = sum(p.chord for p in rp) + gap
            straight = sum(p.length for p in rp if p.arc is None) + gap
            if straight > 0:
                out[f"STRAIGHT:{role}"] = straight
        if covers is None and "ARC:CENTRELINE" not in out and self._band():
            # a band of constant thickness: centreline = mean of its two faces (exact for concentric arcs of equal
            # sweep and for square corners); derived only when the OUTER and INNER arcs are such a band
            out["ARC:CENTRELINE"] = (out["ARC:OUTER"] + out["ARC:INNER"]) / 2.0
            if "CHORD:OUTER" in out and "CHORD:INNER" in out:
                out["CHORD:CENTRELINE"] = (out["CHORD:OUTER"] + out["CHORD:INNER"]) / 2.0
        return out

    def area_candidates(self):
        if not self.loops:
            return {}
        true = chord = 0.0
        for area, hole, chain in self.loops:
            poly = 0.0
            for p, rev in chain:
                a, b = (p.b, p.a) if rev else (p.a, p.b)
                poly += (a[0] * b[1] - b[0] * a[1]) / 2.0
            s = -1.0 if hole else 1.0
            true += s * abs(area)
            chord += s * abs(poly)
        return {"TRUE:AREA": true, "CHORD:AREA": chord}


# ------------------------------------------------------------------------------------------------------- lines
def _line(rec, elements):
    lid = rec.get("line_id")
    if not lid:
        raise ValueError("every line has a line_id")
    eid = rec.get("element_id")
    if eid not in elements:
        raise ValueError(f"{lid}: unknown element {eid!r}")
    el = elements[eid]
    measure = rec.get("measure")
    if measure not in MEASURES:
        raise ValueError(f"{lid}: measure {measure!r} not in {MEASURES}")
    k = _scale(rec.get("units"), lid)
    v = float(rec["value"]) * (k if measure == "LENGTH" else k * k)
    if measure == "LENGTH" and v > MAX_LINE_M:
        raise ValueError(f"{lid}: {v:.1f} m on one element: millimetres given as metres?")
    if measure == "PLAN_AREA" and v > MAX_LINE_M * 100:
        raise ValueError(f"{lid}: {v:.1f} m2 on one element: square millimetres given as m2?")
    ded = float(rec.get("deductions") or 0.0) * (k if measure == "LENGTH" else k * k)
    basis = rec.get("basis") or None
    bases = LENGTH_BASES if measure == "LENGTH" else AREA_BASES
    if basis is not None and basis not in bases:
        raise ValueError(f"{lid}: basis {basis!r} is not a {measure} basis {tuple(bases)}")
    chord_role = rec.get("chord_role")
    if basis in ("CHORD", "PROJECTED_CHORD") and chord_role not in ROLES:
        raise ValueError(f"{lid}: a {basis} names the face it is taken on (chord_role)")
    purpose = rec.get("purpose", "QUANTITY")
    if purpose not in PURPOSES:
        raise ValueError(f"{lid}: purpose {purpose!r} not in {PURPOSES}")
    status = rec.get("status", "ACTIVE")
    if status not in STATUSES:
        raise ValueError(f"{lid}: status {status!r} not in {STATUSES}")
    covers = rec.get("covers")
    if covers is not None:
        covers = tuple(covers)
        bad = [c for c in covers if c not in el.pieces]
        if bad:
            raise ValueError(f"{lid}: covers unknown pieces {bad} of {eid}")
        if measure == "PLAN_AREA":
            raise ValueError(f"{lid}: a plan area covers its element's loops; give the part as its own element")
    if measure == "PLAN_AREA" and not el.loops:
        raise ValueError(f"{lid}: a PLAN_AREA line on {eid}, which has no loops")
    return {"line_id": lid, "element_id": eid, "family": rec.get("family") or "", "measure": measure, "value": v,
            "deductions": ded, "basis": basis, "chord_role": chord_role, "purpose": purpose, "status": status,
            "covers": covers, "chord_rule": rec.get("chord_rule") or None, "ref": rec.get("ref") or ""}


def _key(line):
    b = line["basis"]
    if b is None:
        return None
    if line["measure"] == "PLAN_AREA":
        return f"{AREA_BASES[b]}:AREA"
    kind, role = LENGTH_BASES[b]
    return f"{kind}:{role or line['chord_role']}"


def _matches(cands, v, tol):
    return sorted(k for k, c in cands.items() if abs(c - v) <= tol)


def _covered_arcs(line, el):
    if line["measure"] == "LENGTH":
        key = _key(line)
        role = key.split(":")[1] if key else None
        if role is None or (role == "CENTRELINE" and not el.arcs(roles=("CENTRELINE",))):
            roles = None                  # unnamed, or a derived centreline: both faces' arcs
        else:
            roles = (role,)
        return el.arcs(line["covers"], roles)
    return el.arcs()


def _overlap(p, q):
    """Arc length (on p's circle) where p and q lie on the same circle and their sweeps overlap."""
    a, b = p.arc, q.arc
    if math.dist(a.centre, b.centre) > TOL_CIRCLE or abs(a.r - b.r) > TOL_CIRCLE:
        return 0.0
    lo1, w1 = a.interval()
    lo2, w2 = b.interval()
    tot = 0.0
    for shift in (-TWO_PI, 0.0, TWO_PI):
        s, e = max(lo1, lo2 + shift), min(lo1 + w1, lo2 + w2 + shift)
        if e > s:
            tot += e - s
    return min(tot, w1, w2) * a.r


# ------------------------------------------------------------------------------------------------------- check
def check(elements, lines):
    """elements, lines: input dicts as in the module docstring. Returns {method, elements, lines, issues}."""
    els = {}
    for rec in elements:
        el = Element(rec)
        if el.eid in els:
            raise ValueError(f"element {el.eid} twice")
        els[el.eid] = el
    ls, seen = [], set()
    for rec in lines:
        ln = _line(rec, els)
        if ln["line_id"] in seen:
            raise ValueError(f"line {ln['line_id']} twice")
        seen.add(ln["line_id"])
        ls.append(ln)

    issues = []

    def issue(code, el, detail, line_ids=()):
        issues.append({"id": f"CG-{len(issues) + 1:03d}", "code": code, "element_id": el,
                       "line_ids": ";".join(line_ids), "detail": detail})

    rows = []
    for ln in ls:
        el = els[ln["element_id"]]
        tol = TOL_LEN if ln["measure"] == "LENGTH" else TOL_AREA
        cands = el.length_candidates(ln["covers"]) if ln["measure"] == "LENGTH" else el.area_candidates()
        gross = ln["value"] + ln["deductions"]
        key = _key(ln)
        hit = _matches(cands, gross, tol)
        expected = cands.get(key) if key else None
        if key and expected is None:
            raise ValueError(f"{ln['line_id']}: basis {ln['basis']} ({key}) does not exist on {el.eid}")
        row = {"line_id": ln["line_id"], "element_id": el.eid, "family": ln["family"], "measure": ln["measure"],
               "status": ln["status"], "purpose": ln["purpose"], "basis": ln["basis"] or "UNNAMED",
               "value": round(ln["value"], 6), "deductions": round(ln["deductions"], 6),
               "expected": None if expected is None else round(expected, 6), "matches": hit, "codes": []}
        rows.append(row)
        if ln["status"] == "SUPERSEDED" or not el.curved:
            continue                                      # a straight element: nothing to say about arcs
        lid = (ln["line_id"],)
        unit = "m" if ln["measure"] == "LENGTH" else "m2"

        def flag(code, detail):
            row["codes"].append(code)
            issue(code, el.eid, detail, lid)

        listing = ", ".join(f"{k} {v:.4f}" for k, v in sorted(cands.items()))
        if key is None:
            flag("BASIS_UNNAMED", f"{ln['line_id']} {gross:.4f} {unit} names no basis; matches "
                                  f"{', '.join(hit) if hit else 'none'} (candidates: {listing})")
        arc_vals = [v for k, v in cands.items() if k.startswith(("ARC:", "TRUE:"))]
        all_vals = [v for k, v in cands.items() if not k.startswith("STRAIGHT:")]
        lo, hi = min(all_vals), max(arc_vals or all_vals)
        straight_hit = [h for h in hit if h.startswith("STRAIGHT:") and cands[h] > tol]
        if any(not h.startswith("STRAIGHT:") for h in hit):
            straight_hit = []                 # an arc / chord basis explains it: not the straight parts alone
        if gross > hi + tol:
            flag("OVER_OUTLINE", f"{ln['line_id']} {gross:.4f} {unit} exceeds the true outline's largest basis "
                                 f"{hi:.4f} by {gross - hi:.4f} {unit}")
        elif gross < lo - tol or straight_hit:
            what = "the straight parts alone" if straight_hit else f"below every basis (lowest {lo:.4f})"
            ref = expected if expected is not None else max(arc_vals or all_vals)
            flag("PARTIAL", f"{ln['line_id']} {gross:.4f} {unit} = {what}: {ref - gross:.4f} {unit} of the "
                            f"curved outline not measured")
        elif key and abs(gross - expected) > tol:
            flag("BASIS_MISMATCH", f"{ln['line_id']} names {ln['basis']} ({key} {expected:.4f}) but is "
                                   f"{gross:.4f} {unit}: matches {', '.join(hit) if hit else 'none'}")
        if ln["covers"] is not None and ln["measure"] == "LENGTH":
            role = key.split(":")[1] if key else None
            full = [p.pid for p in el.arcs(roles=None if role is None else (role,))]
            left = [p for p in full if p not in ln["covers"]]
            if left and not row["codes"].count("PARTIAL"):
                miss = sum(el.pieces[p].length for p in left)
                flag("PARTIAL", f"{ln['line_id']} covers {len(full) - len(left)} of the {len(full)} arcs; "
                                f"not covered {', '.join(left)} ({miss:.4f} m of arc)")
        chordish = key is not None and key.startswith("CHORD:")
        only_chord = key is None and hit and all(h.startswith("CHORD:") for h in hit)
        if ln["purpose"] == "QUANTITY" and el.follows_arc and (chordish or only_chord):
            if ln["chord_rule"]:
                flag("CHORD_BY_RULE", f"{ln['line_id']} is a chord by {ln['chord_rule']} (information)")
            else:
                flag("STRAIGHTENED", f"{ln['line_id']} {gross:.4f} {unit} is a chord "
                                     f"({key or '/'.join(hit)}) on an element that follows the arc: the arc basis "
                                     f"is {cands.get('ARC:' + (key or hit[0]).split(':')[1], float('nan')):.4f}"
                     if ln["measure"] == "LENGTH" else
                     f"{ln['line_id']} {gross:.4f} {unit} is the chord polygon; the true area is "
                     f"{cands['TRUE:AREA']:.4f}")

    # two active quantity lines of one family on the same arc
    act = [ln for ln in ls if ln["status"] == "ACTIVE" and ln["purpose"] == "QUANTITY"]
    for i, a in enumerate(act):
        for b in act[i + 1:]:
            if a["family"] != b["family"] or a["measure"] != b["measure"]:
                continue
            ea, eb = els[a["element_id"]], els[b["element_id"]]
            tot = 0.0
            for p in _covered_arcs(a, ea):
                for q in _covered_arcs(b, eb):
                    if a["measure"] == "PLAN_AREA" and ea.side.get(p.pid) != eb.side.get(q.pid):
                        continue                              # the two regions only share the boundary
                    tot += _overlap(p, q)
            if tot > TOL_LEN:
                for r in rows:
                    if r["line_id"] in (a["line_id"], b["line_id"]):
                        r["codes"].append("DOUBLE_ARC")
                issue("DOUBLE_ARC", f"{ea.eid} / {eb.eid}" if ea.eid != eb.eid else ea.eid,
                      f"{a['line_id']} and {b['line_id']} ({a['family']}) both measure {tot:.4f} m of the same arc",
                      (a["line_id"], b["line_id"]))

    # element-level coverage of its arcs by the lines of each expected family
    for el in els.values():
        for fam in el.expected:
            mine = el.arcs()
            fl = [ln for ln in act if ln["family"] == fam]
            if not mine:
                continue
            if not fl:
                issue("NOT_MEASURED", el.eid, f"no active {fam} line touches {el.eid}")
                continue
            uncovered = []
            for p in mine:
                cov = 0.0
                for ln in fl:
                    e2 = els[ln["element_id"]]
                    for q in _covered_arcs(ln, e2):
                        if ln["measure"] == "PLAN_AREA" and el.side.get(p.pid) not in (None, e2.side.get(q.pid)):
                            continue
                        cov += _overlap(p, q)
                left = p.length - min(cov, p.length)
                if left > TOL_LEN:
                    uncovered.append((p.pid, left))
            if uncovered:
                tot = sum(x for _, x in uncovered)
                extra = ""
                touching = [ln for ln in fl if ln["measure"] == "PLAN_AREA"]
                if touching and el.loops and len(touching) == len(fl):
                    have = sum(ln["value"] + ln["deductions"] for ln in touching)
                    true = el.area_candidates()["TRUE:AREA"]
                    extra = (f"; their plan areas sum to {have:.4f} of the element's {true:.4f} m2 "
                             f"({true - have:+.4f} m2 short; information, overlap between them not tested)")
                issue("PARTIAL", el.eid, f"the active {fam} lines leave {tot:.4f} m of {el.eid}'s arcs uncovered "
                                         f"({', '.join(f'{p} {x:.4f}' for p, x in uncovered)}){extra}",
                      tuple(ln["line_id"] for ln in fl))

    summary = {}
    for it in issues:
        summary[it["code"]] = summary.get(it["code"], 0) + 1
    return {"method": METHOD, "rules": RULES,
            "elements": [{"element_id": e.eid, "kind": e.kind, "ref": e.ref, "curved": e.curved,
                          "arcs": [{"piece_id": p.pid, "role": p.role, "r": round(p.arc.r, 6),
                                    "sweep_deg": round(math.degrees(p.arc.sweep), 6), "length": round(p.arc.length, 6),
                                    "chord": round(p.arc.chord, 6), "side": e.side.get(p.pid)}
                                   for p in e.arcs()],
                          "length_candidates": {k: round(v, 6) for k, v in sorted(e.length_candidates().items())},
                          "area_candidates": {k: round(v, 6) for k, v in sorted(e.area_candidates().items())}}
                         for e in els.values()],
            "lines": rows, "issues": issues, "summary": summary}
