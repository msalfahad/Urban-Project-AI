"""MASONRY CENTRELINE RUN (T-027, MASONRY_CENTRELINE_V1) - the masonry run of one floor per wall thickness, measured
on the wall CENTRELINE including corners, T-junctions and wall ends (UP-WALL-GEOM-001, OWNER_APPROVED: "centreline
(masonry run)"; each face is for finishing only). A new piece, NOT wired into any method: no released quantity moves.

    measure(walls, unit_m=None, openings=(), columns_m=(), floor=None) -> floor record (see FIELDS below)

Input: the wall records of ONE floor as `engine.source.arch_walls.walls()["walls"]` gives them (each straight band:
`centreline` [P0, P1] in drawing units at mid-thickness, `t_m`, `family`, `gross_lm` = the band extent with its
openings, `columns_in_wall_lm`; curved bands carry `curved`; ARCH_TAKEOFF_V2.8 stubs carry `stub`). The band extent
already reaches a free wall end and runs through a T-junction on the side of the wall that runs through (its back
face is continuous); what it leaves out is the corner piece of an L, where both bands stop at the other's inner face.

Junction rules (geometry only; t_A, t_B thicknesses, theta the angle between the two centrelines, X the meeting point
of the two centrelines, h_B = t_B / (2 |sin theta|) the half width of B measured along A):
    FREE_END      the end touches no other band: kept (the band extent reaches the end cap).
    T (stem)      A ends on B's near face (|d_A - h_B| <= JOIN_TOL_M) and B runs past X by at least h_A: the stem is
                  the clear length to B's face, B runs through (a T or cross piece is counted once, in the wall that
                  runs through). Also an L where the drawing already gives one band the whole corner piece: the
                  stem stops on its near face, the band holding the piece ends on the stem's far face (d_A = -h_B);
                  both are kept as drawn.
    L             A ends on B's near face, B ends on A's near face (X beyond B's end by h_A): both run on to X, the
                  centreline meeting point. Area check: A gains t_A h_B, B gains t_B h_A; at 90 deg the two make the
                  t_A x t_B corner piece, counted once.
    CROSS_SPLIT   two collinear bands of one family face each other across exactly the width of a crossing band that
                  is itself split there (four stems, no band running through): one pair is joined across the piece
                  when the two walls are of ONE family (the metres are the same whichever runs through); of TWO
                  families the piece is HELD (which wall runs through is not on the drawing; no rule chooses).
    OPENING_GAP   two collinear bands of one family separated by exactly the width of an opening of the floor
                  (centre on their centreline): joined, the opening is in the masonry run (openings are listed with
                  their widths, never deducted from the metres).
    HELD          any other meeting (an end inside another band, a corner whose pieces neither meet nor overlap
                  cleanly, two L candidates at one end, a curved band met off its tangent end): the end is left as
                  drawn and the meeting is listed with the largest metres it could add; nothing is guessed.

Columns standing in the wall line are concrete, not wall (UP-COL-ORIENT-001): with `columns_m` (polygons in metres)
every centreline stretch inside a column is cut, extensions included; without them the band's own
`columns_in_wall_lm` (engine.source.arch_walls) is subtracted and the record says so.

Never: a masonry m2 or m3 (UP-MAS-HEIGHT-001 REQUIRES_CONFIRMATION, owner Q-60 open: HELD with the reason, value
None, never a default height, never 0); a material inferred from a thickness; an opening deducted from the metres;
a missing floor or family given 0 (no band -> status NO_WALL_BANDS, value None).
"""

from __future__ import annotations

import math
from collections import defaultdict

POLICY_ID = "MASONRY_CENTRELINE_V1"
RULES = ("UP-WALL-GEOM-001", "UP-COL-ORIENT-001", "UP-MAS-HEIGHT-001", "UP-QTY-STATUS-001")
JOIN_TOL_M = 0.02            # an end "on" a face: within 2 cm (drafting tolerance, the arch_walls SAME_BAND_M is 5 cm)
PARALLEL_SIN = math.sin(math.radians(10.0))   # two bands under 10 deg apart never form a junction with each other
COLLINEAR_OFF_M = 0.01       # two bands on one centreline line: offsets within 1 cm
COLLINEAR_ANG = math.radians(0.5)
MAX_GAP_M = 3.0              # a collinear gap longer than this is never joined (largest opening or crossing piece)
HEIGHT_HELD = {"status": "HELD", "value": None,
               "reason": "UP-MAS-HEIGHT-001 REQUIRES_CONFIRMATION: the masonry height rule is not owner-confirmed "
                         "(owner question Q-60 open); block m2 and m3 wait on it, never a default height"}


# ---------------------------------------------------------------------------------------------------------- helpers
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _unit(v):
    n = math.hypot(*v)
    return (v[0] / n, v[1] / n)


def _family(t_m):
    """a thickness family to the centimetre, as engine.source.arch_walls._family (0.195 and 0.204 are one 0.20)."""
    return f"{round(t_m * 100) / 100:.2f}"


def drawing_unit(walls):
    """metres per drawing unit from the straight bands themselves (gross_lm / centreline length), or None when the
    bands disagree (> 1e-6 relative) or none is usable."""
    ks = []
    for w in walls:
        if w.get("curved") or w.get("stub") or not w.get("centreline") or not w.get("gross_lm"):
            continue
        a, b = w["centreline"][0], w["centreline"][-1]
        d = math.dist(a, b)
        if d > 0:
            ks.append(w["gross_lm"] / d)
    if not ks:
        return None
    k = sorted(ks)[len(ks) // 2]
    return k if all(abs(x - k) <= 1e-6 * k for x in ks) else None


class _Piece:
    """one straight band on its centreline, in metres; s0 / s1 are the end stations along u from P0."""

    def __init__(self, w, unit_m):
        self.w = w
        self.id = w.get("wall_id")
        self.t = float(w["t_m"])
        self.family = w.get("family") or _family(self.t)
        a = (w["centreline"][0][0] * unit_m, w["centreline"][0][1] * unit_m)
        b = (w["centreline"][-1][0] * unit_m, w["centreline"][-1][1] * unit_m)
        self.p0 = a
        self.u = _unit(_sub(b, a))
        self.n = (-self.u[1], self.u[0])
        self.s = [0.0, math.dist(a, b)]          # current end stations (ends may move: L extension, joins)
        self.ext = [0.0, 0.0]                    # metres added at each end (L corners)
        self.ends = [None, None]                 # junction record id per end
        self.joined_into = None                  # a collinear piece merged into another one
        self.cols_lm = float(w.get("columns_in_wall_lm") or 0.0)

    def at(self, s):
        return (self.p0[0] + self.u[0] * s, self.p0[1] + self.u[1] * s)

    def end_pt(self, k):
        return self.at(self.s[k])

    def out_dir(self, k):
        return (-self.u[0], -self.u[1]) if k == 0 else self.u

    def station(self, p):
        return _dot(_sub(p, self.p0), self.u)

    def offset(self, p):
        return _dot(_sub(p, self.p0), self.n)


def _meet(A, B):
    """the centrelines' meeting point and |sin theta|, or None for near-parallel bands."""
    sn = _cross(A.u, B.u)
    if abs(sn) < PARALLEL_SIN:
        return None
    # A.p0 + a u_A = B.p0 + b u_B
    d = _sub(B.p0, A.p0)
    a = _cross(d, B.u) / sn
    return A.at(a), abs(sn)


# ------------------------------------------------------------------------------------------------- collinear joins
def _collinear(A, B):
    if A.family != B.family:
        return False
    if abs(_cross(A.u, B.u)) > math.sin(COLLINEAR_ANG):
        return False
    return abs(A.offset(B.p0)) <= COLLINEAR_OFF_M


def _gap(A, B):
    """(gap metres, A end index, B end index) of two collinear pieces facing each other, or None when they overlap."""
    a0, a1 = sorted(A.s)
    bs = sorted(A.station(B.end_pt(k)) for k in (0, 1))
    if bs[0] >= a1:
        ka = 1 if A.s[1] >= A.s[0] else 0
        kb = min((0, 1), key=lambda k: A.station(B.end_pt(k)))
        return bs[0] - a1, ka, kb
    if bs[1] <= a0:
        ka = 0 if A.s[0] <= A.s[1] else 1
        kb = max((0, 1), key=lambda k: A.station(B.end_pt(k)))
        return a0 - bs[1], ka, kb
    return None


def _crossing_pieces(A, ka, gap, pieces):
    """the non-parallel pieces whose band fills exactly the gap beyond A's end ka (their width along A = gap)."""
    E = A.end_pt(ka)
    mid = (E[0] + A.out_dir(ka)[0] * gap / 2, E[1] + A.out_dir(ka)[1] * gap / 2)
    out = []
    for C in pieces:
        if C is A or C.joined_into is not None:
            continue
        m = _meet(A, C)
        if m is None:
            continue
        X, sn = m
        if math.dist(X, mid) > JOIN_TOL_M or abs(C.t / sn - gap) > 2 * JOIN_TOL_M:
            continue
        out.append(C)
    return out


def _opening_in_gap(A, ka, gap, openings):
    E = A.end_pt(ka)
    mid = (E[0] + A.out_dir(ka)[0] * gap / 2, E[1] + A.out_dir(ka)[1] * gap / 2)
    for o in openings:
        c = (o.get("position") or {}).get("centre_m")
        w = o.get("width_m")
        if not c or w is None:
            continue
        if math.dist(tuple(c), mid) <= max(A.t / 2, JOIN_TOL_M) + JOIN_TOL_M and abs(w - gap) <= 2 * JOIN_TOL_M:
            return o
    return None


def _join(A, ka, B, kb):
    """B is merged into A: A's end ka moves to B's far end."""
    far = B.end_pt(1 - kb)
    A.s[ka] = A.station(far)
    A.ext[ka] += B.ext[1 - kb]
    A.cols_lm += B.cols_lm
    B.joined_into = A.id


# ------------------------------------------------------------------------------------------------------ the measure
def measure(walls, unit_m=None, openings=(), columns_m=(), floor=None):
    """the masonry centreline run of one floor per thickness family (see the module docstring)."""
    walls = list(walls or ())
    rec = {"policy": POLICY_ID, "rules": list(RULES), "floor": floor, "unit_m": None, "status": None,
           "by_thickness": [], "junctions": [], "held": [], "pieces": [], "openings_listed": [],
           "column_basis": None, "height": dict(HEIGHT_HELD)}
    if not walls:
        rec["status"] = "NO_WALL_BANDS"
        rec["why"] = "no wall band on this floor: the masonry run is not measured (None, never 0)"
        return rec
    if unit_m is None:
        unit_m = drawing_unit(walls)
    if unit_m is None:
        rec["status"] = "HELD"
        rec["why"] = "the drawing unit cannot be read from the bands (gross_lm / centreline length disagree)"
        return rec
    rec["unit_m"] = unit_m
    straight = [_Piece(w, unit_m) for w in walls if not w.get("curved") and w.get("centreline")
                and not (w.get("stub") and w.get("kind") != "RETURN_STUB")
                and math.dist(w["centreline"][0], w["centreline"][-1]) > 0]
    other = [w for w in walls if w.get("curved") or (w.get("stub") and w.get("kind") != "RETURN_STUB")]
    jid = [0]

    def junction(kind, members, **kw):
        jid[0] += 1
        j = {"junction_id": f"J{jid[0]:03d}", "kind": kind, "members": members, **kw}
        rec["junctions"].append(j)
        return j["junction_id"]

    # 1. collinear joins: an opening gap, or a crossing where no band runs through
    cross_seen, cross_ends = set(), set()
    for A in straight:
        for B in straight:
            if A is B or A.joined_into or B.joined_into or not _collinear(A, B):
                continue
            g = _gap(A, B)
            if g is None or g[0] > MAX_GAP_M:
                continue
            gap, ka, kb = g
            if gap <= JOIN_TOL_M:
                _join(A, ka, B, kb)
                junction("ABUTTING_JOIN", [A.id, B.id], gap_m=round(gap, 6))
                continue
            o = _opening_in_gap(A, ka, gap, openings)
            if o is not None:
                _join(A, ka, B, kb)
                junction("OPENING_GAP", [A.id, B.id], gap_m=round(gap, 6), opening_id=o.get("opening_id"))
                continue
            cs = _crossing_pieces(A, ka, gap, straight)
            if not cs:
                continue
            # does a crossing band run through the gap? then A and B are stems on it (the T rule below)
            through = []
            for C in cs:
                X, _sn = _meet(A, C)
                xc = C.station(X)
                lo, hi = sorted(C.s)
                if lo + A.t / 2 - JOIN_TOL_M <= xc <= hi - A.t / 2 + JOIN_TOL_M:
                    through.append(C)
            if through:
                continue
            fams = {C.family for C in cs}
            if fams == {A.family}:
                _join(A, ka, B, kb)
                junction("CROSS_SPLIT", [A.id, B.id] + [C.id for C in cs], gap_m=round(gap, 6),
                         decision="one family: the pair is joined across the crossing piece")
            else:
                key = frozenset([A.id, B.id] + [C.id for C in cs])
                if key in cross_seen:
                    continue
                cross_seen.add(key)
                X0 = _meet(A, cs[0])[0]
                cross_ends.update({(A.id, ka), (B.id, kb)})
                for C in cs:
                    cross_ends.add((C.id, min((0, 1), key=lambda k: math.dist(C.end_pt(k), X0))))
                cfam = sorted(fams)
                rec["held"].append({"what": "CROSS_PIECE", "members": [A.id, B.id] + [C.id for C in cs],
                                    "families": [A.family] + cfam, "max_lm_by_family": {
                                        A.family: round(gap, 6), **{C.family: round(A.t, 6) for C in cs}},
                                    "reason": "a crossing of two thickness families with no band running through: "
                                              "which wall runs through is not on the drawing and no Urban rule "
                                              "chooses; the piece is in neither family"})
                junction("CROSS_HELD", [A.id, B.id] + [C.id for C in cs], gap_m=round(gap, 6))
    live = [P for P in straight if P.joined_into is None]

    # 2. the ends: free, stem of a T, L corner, or held (classified on the drawn extents, then moved)
    moves = []
    for A in live:
        for ka in (0, 1):
            if (A.id, ka) in cross_ends:
                A.ends[ka] = "CROSS_HELD"           # the crossing piece is held once, in rec["held"]
                continue
            E = A.end_pt(ka)
            od = A.out_dir(ka)
            hits = []
            for B in live:
                if B is A:
                    continue
                m = _meet(A, B)
                if m is None:
                    continue
                X, sn = m
                dA = _dot(_sub(X, E), od)            # A's end to X, positive beyond the end
                hB, hA = B.t / (2 * sn), A.t / (2 * sn)
                lo, hi = sorted(B.s)
                xB = B.station(X)
                eB = min(xB - lo, hi - xB)           # X inside B's extent (+) or beyond its nearer end (-)
                if eB < -hA - JOIN_TOL_M or dA > hB + JOIN_TOL_M or dA < -hB - JOIN_TOL_M:
                    continue                          # B does not reach A's end
                if abs(dA - hB) <= JOIN_TOL_M:
                    if eB >= hA - JOIN_TOL_M:
                        hits.append(("T", B, dA, hB))
                    elif abs(eB + hA) <= JOIN_TOL_M:
                        hits.append(("L", B, dA, hB))
                    else:
                        hits.append(("HELD", B, dA, hB))
                elif abs(dA + hB) <= JOIN_TOL_M and abs(eB + hA) <= JOIN_TOL_M:
                    hits.append(("T", B, dA, hB))     # A ends on B's far face: A holds the whole corner, B is the stem
                else:
                    hits.append(("HELD", B, dA, hB))  # A's end inside B's band, or a partial corner
            kinds = [h[0] for h in hits]
            if not hits:
                A.ends[ka] = "FREE_END"
            elif "T" in kinds and "L" not in kinds and "HELD" not in kinds:
                A.ends[ka] = "T_STEM"
            elif kinds == ["L"]:
                _k, B, dA, hB = hits[0]
                A.ends[ka] = "L"
                moves.append((A, ka, dA))            # to the centreline meeting point, applied after every end
            else:                                    # two corner candidates, or a T and an L at one end
                A.ends[ka] = "HELD"
            if A.ends[ka] == "HELD":
                mx = max(abs(h[2]) + h[3] for h in hits)
                rec["held"].append({"what": "JUNCTION", "wall_id": A.id, "end": ka, "family": A.family,
                                    "meets": [h[1].id for h in hits], "kinds": kinds,
                                    "max_lm": round(mx, 6),
                                    "reason": "the end meets " + ", ".join(sorted({h[1].id for h in hits})) +
                                              " in no clean T or L (inside a band, a partial corner or two corner "
                                              "candidates): left as drawn; up to max_lm more is not measured"})
            if hits:
                junction(A.ends[ka], [A.id] + [h[1].id for h in hits], end=ka)

    for A, ka, dA in moves:
        A.ext[ka] = dA
        A.s[ka] += dA if ka == 1 else -dA

    # 3. lengths, columns cut
    col_polys = []
    if columns_m:
        from shapely.geometry import LineString, Polygon
        col_polys = [Polygon(p) for p in columns_m if len(p) >= 3]
        rec["column_basis"] = "COLUMN_POLYGONS: the centreline stretch inside a column is cut (UP-COL-ORIENT-001)"
    else:
        rec["column_basis"] = ("BAND_COLUMNS_IN_WALL_LM: no column polygons given; the band's own columns_in_wall_lm "
                               "(engine.source.arch_walls) is subtracted; a column inside an L extension is not seen")
    fam = defaultdict(lambda: {"run_lm": 0.0, "pieces": 0, "drawn_lm": 0.0, "corner_ext_lm": 0.0, "columns_lm": 0.0,
                               "curved_lm": 0.0, "stub_lm": 0.0, "held_max_lm": 0.0})
    for P in live:
        a, b = P.end_pt(0), P.end_pt(1)
        L = math.dist(a, b)
        if col_polys:
            from shapely.geometry import LineString
            ln = LineString([a, b])
            cut = sum(ln.intersection(c).length for c in col_polys if ln.intersects(c))
        else:
            cut = P.cols_lm
        run = L - cut
        f = fam[P.family]
        f["run_lm"] += run
        f["pieces"] += 1
        f["drawn_lm"] += L - sum(P.ext)
        f["corner_ext_lm"] += sum(P.ext)
        f["columns_lm"] += cut
        if P.w.get("stub"):
            f["stub_lm"] += run
        rec["pieces"].append({"wall_id": P.id, "family": P.family, "t_m": P.t, "ends": list(P.ends),
                              "corner_ext_m": [round(x, 6) for x in P.ext], "columns_lm": round(cut, 6),
                              "run_lm": round(run, 6),
                              "joined": [p.id for p in straight if p.joined_into == P.id]})
    for w in other:                                  # curved bands and curved stubs: their own centreline arc
        f = fam[w.get("family") or _family(float(w["t_m"]))]
        cu = w.get("curved") or {}
        L = (cu.get("bases_lm") or {}).get("MID_BAND_ARC", w.get("gross_lm"))
        if L is None:
            rec["held"].append({"what": "CURVED_LENGTH", "wall_id": w.get("wall_id"),
                                "reason": "a curved wall with no centreline arc length"})
            continue
        cut = 0.0 if col_polys else float(w.get("columns_in_wall_lm") or 0.0)
        f["run_lm"] += L - cut
        f["pieces"] += 1
        f["curved_lm"] += L - cut
        f["columns_lm"] += cut
        rec["pieces"].append({"wall_id": w.get("wall_id"), "family": w.get("family"), "t_m": w.get("t_m"),
                              "ends": ["CURVED", "CURVED"], "corner_ext_m": [0.0, 0.0], "columns_lm": round(cut, 6),
                              "run_lm": round(L - cut, 6), "joined": [],
                              "basis": "MID_BAND_ARC (the centreline arc, UP-WALL-GEOM-001)"})
    for h in rec["held"]:
        if h["what"] == "JUNCTION":
            fam[h["family"]]["held_max_lm"] += h["max_lm"]
        elif h["what"] == "CROSS_PIECE":
            for fm, v in h["max_lm_by_family"].items():
                fam[fm]["held_max_lm"] += v

    # 4. openings listed per family (never deducted)
    ids = {w.get("wall_id"): (w.get("family") or _family(float(w["t_m"]))) for w in walls}
    op_lm = defaultdict(float)
    for o in openings or ():
        fm = ids.get(o.get("host_wall"))
        if fm is None and o.get("wall_t_m") is not None:
            fm = _family(float(o["wall_t_m"]))
        rec["openings_listed"].append({"opening_id": o.get("opening_id"), "kind": o.get("kind"),
                                       "width_m": o.get("width_m"), "family": fm, "host_wall": o.get("host_wall")})
        if fm is not None and o.get("width_m") is not None:
            op_lm[fm] += float(o["width_m"])
    for k in sorted(fam):
        f = fam[k]
        rec["by_thickness"].append({
            "family": k, "masonry_run_lm": round(f["run_lm"], 6),
            "status": "RELEASED_GEOMETRY" if f["held_max_lm"] == 0 else "MEASURED_WITH_HELD_PIECES",
            "held_max_lm": round(f["held_max_lm"], 6), "pieces": f["pieces"], "drawn_lm": round(f["drawn_lm"], 6),
            "corner_ext_lm": round(f["corner_ext_lm"], 6), "columns_lm": round(f["columns_lm"], 6),
            "curved_lm": round(f["curved_lm"], 6), "stub_lm": round(f["stub_lm"], 6),
            "openings_lm_listed": round(op_lm.get(k, 0.0), 6) if openings else None,
            "plan_strip_m2": round(f["run_lm"] * float(k), 6),
            "block_m2": dict(HEIGHT_HELD), "block_m3": dict(HEIGHT_HELD)})
    rec["status"] = "MEASURED" if not rec["held"] else "MEASURED_WITH_HELD_PIECES"
    return rec


def measure_arch(arch, openings_by_floor=True, columns_by_floor=None):
    """every floor of an arch_compute() result: {floor: measure(...)} (a floor with no band -> NO_WALL_BANDS)."""
    out = {}
    ops = defaultdict(list)
    if openings_by_floor:
        for o in arch.get("openings") or ():
            ops[o.get("floor")].append(o)
    for w in arch.get("walls") or ():
        fl = w.get("floor")
        key = fl if fl not in out else f"{fl}|{w.get('region_id')}"
        out[key] = measure(w.get("walls"), openings=ops.get(fl, ()),
                           columns_m=(columns_by_floor or {}).get(fl, ()), floor=fl)
    return out


def policy_record():
    return {"policy_id": POLICY_ID, "rules": list(RULES), "join_tol_m": JOIN_TOL_M, "max_gap_m": MAX_GAP_M,
            "never": ["a masonry m2 or m3 without an owner-confirmed height (Q-60)", "an opening deducted from the run",
                      "a material inferred from a thickness", "a column stretch counted as wall",
                      "a crossing of two families given to one of them without a rule", "a missing floor given 0"]}
