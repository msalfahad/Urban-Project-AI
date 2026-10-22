"""MASONRY CENTRELINE RUN V2 (T-125, MASONRY_CENTRELINE_V2) - the masonry run of one floor per wall thickness on the
wall CENTRELINE (UP-WALL-GEOM-001), with the evidence checks that MASONRY_CENTRELINE_V1 (T-027) lacks, and the five
lengths of owner Q-69 B per run. A new piece, NOT wired into any method: no released quantity moves. V1 is untouched
and is reused unchanged for the junction work (T / L / cross / opening gap / held), so every V1 rule still holds.

    measure(walls, unit_m=None, openings=(), columns_m=None, floor=None, evidence=None) -> floor record
    evidence_from_ents(ents, roles) -> evidence (wall-layer face segments, glazing linework, door swings)

What V2 adds, all from the floor's own drawing (never a project constant):
  1. UNDRAWN SPLIT. Along every straight band the stretches where NEITHER face is drawn on a wall-role layer are found.
     A stretch is kept in the run only when something in it says it is part of the wall: a column (concrete, cut later
     by UP-COL-ORIENT-001), a crossing band (a junction piece), a door / window opening record, a passage opening with
     a head line (the wall face continued over the gap) or a symbol block, or glazing linework inside the band
     (a GLAZED stretch). Any other stretch (open floor, a garden edge or a passage mouth drawn on another layer) splits
     the band; the split-out metres are listed, never dropped silently. V1 then re-joins collinear pieces only by its
     OPENING_GAP rule (opening width = gap, gap <= 3.0 m), fed only the openings that carry such evidence.
  2. DOORWAY AT A FREE END. A band end with no band at it whose centreline, carried on, reaches the near face of a
     non-parallel band within MAX_GAP_M, with a door record or a door swing (hinge in the gap, leaf no longer than the
     gap) in that gap and nothing else in between: the end is carried to that face (the doorway is in the run, as an
     opening between two jambs is); V1 then sees a T stem there. A jamb stub standing on that face (both faces drawn
     on a wall layer, or its own wall record) is wall, not doorway: the doorway is the gap between the jambs, the
     stub stays in the physical length (T-169, defect D-T125-1; under the L-P9-04 0.05 m convention it is listed).
  3. CURVED GLAZED BAY. Concentric glazing arcs (a curved glass line) whose chord covers an undrawn stretch of a
     straight band (parallel, within the band's reach): the glass mid circle is carried to the band centreline (as
     centrelines meet at an L); the chord between the two meeting points leaves the band and the arc between them joins
     the run in that band's family as glass; a curved masonry stub lying on that circle is absorbed once (masonry).
  4. GLAZED LINES. Glazing linework (straight or curved) standing on its own, outside every wall band, at least
     GLAZED_MIN_M long: listed as a GLAZED line with its metres; its thickness family is not drawn (glass has no block
     thickness), so it is reported beside the families, never added to one and never dropped.
  5. Q-69 B LENGTHS per run (owner 2026-10-20 18:45): (1) architectural run (V1 basis: openings in the run),
     (2) physical blockwork at the plan cut = (1) less every opening, doorway and glazed stretch in the run, (3) glass /
     aluminium length (window openings + glazed stretches + glazed lines), (4) masonry above / below openings and
     glazing: HELD per opening (heights and elevations are not read here; T-108), (5) the net block area inputs
     (physical length, the openings with widths, the height HELD under owner Q-60 A until T-108). No opening is
     deducted twice: (2) plus the opening widths re-adds to (1).
  6. CHECKS. Per floor the plan identity sum(run x t) = the area of the union of the run strips, each junction end
     carried over the other wall's half width (L corners, T stems), within 1 mm x t per piece; piers shorter than
     4 t are listed as linear items (still in the run); every bridged stretch is listed with what bridged it.

Inputs: `walls` as engine.source.arch_walls gives them; `openings` as the arch run gives them (kind, width_m,
position.centre_m in metres, evidence.marks); `columns_m` the wall stage's column outlines in metres (REQUIRED:
without them V1 over-counts L corners; None -> every family HELD, reason given); `evidence` from evidence_from_ents
(REQUIRED for the split: None -> the record is HELD, V1 figures are not re-published as V2).

Never: a masonry m2 or m3 (owner Q-60 heights belong to T-108: HELD, None); a material from a thickness; an opening
deducted from the architectural run; a missing floor or family given 0; a split stretch dropped without a listing.
"""

from __future__ import annotations

import math
from collections import defaultdict

from engine.source import masonry_centreline as V1

POLICY_ID = "MASONRY_CENTRELINE_V2"
RULES = ("UP-WALL-GEOM-001", "UP-COL-ORIENT-001", "UP-MAS-HEIGHT-001", "UP-QTY-STATUS-001", "OWNER-Q-60-A",
         "OWNER-Q-69-B")
JOIN_TOL_M = V1.JOIN_TOL_M          # 2 cm: a face line "on" a band face, an end "on" a face
MAX_GAP_M = V1.MAX_GAP_M            # 3.0 m: the widest opening a run is carried across
MIN_STRETCH_M = 0.05                # an undrawn stretch shorter than this is a drafting artefact (L-P9-04 convention)
JAMB_STUB_MIN_M = 0.05              # T-169: a jamb stub at a free-end doorway this long or longer is wall (L-P9-04)
FACE_ANG = math.radians(1.0)        # a face segment parallel to the band within 1 deg
COVER_SHARE = 0.5                   # a column / band / glazing covers a stretch when it covers half of it or more
SWING_REACH_M = 0.10                # a door hinge within 10 cm of the gap (frame / jamb set-back)
SWING_LEAF_M = (0.5, 1.3)           # a door leaf radius (engine.source.arch_plan.DOOR_RADIUS_M)
SWING_FRAME_M = 0.25                # a doorway is at most the leaf plus its two frames / jamb set-backs
GLAZED_MIN_M = 1.0                  # glazing on its own shorter than this is a window detail, not a glass line
GLAZED_SET_M = 0.45                 # the glazing lines of one glass line lie within a wall thickness (BAND_T_M max)
ARC_CENTRE_TOL_M = 0.05             # concentric glazing arcs: centres within 5 cm
BAY_REACH_M = 0.30                  # a curved bay's chord within t/2 + 30 cm of the band centreline (frame depth)
BAY_END_TOL_M = 0.15                # the glazing's chord ends no more than 15 cm beyond the undrawn stretch ...
BAY_COVER = 0.8                     # ... and covers at least 80 % of it (the glass stops at the jambs / faces)
BAY_ANG = math.radians(5.0)
PIER_T = 4.0                        # a piece shorter than 4 t is a pier (scout R-08)
EVIDENCE_KINDS = ("DOOR", "WINDOW")
OPEN_FIT_M, OPEN_FIT_SHARE = 0.10, 0.10   # an undrawn stretch longer than its openings by more than this is listed
HEIGHT_HELD = {"status": "HELD", "value": None,
               "reason": "owner Q-60 A: the block height is the underside of the beam (or slab) above each wall; heights "
                         "are measured in T-108 (masonry area), not by the run: never a default height, never 0"}
ABOVE_BELOW_HELD = {"status": "HELD", "value": None,
                    "reason": "owner Q-69 B (4): masonry above / below an opening or glazing needs its head / sill "
                              "heights or the elevations; not read by the plan run (T-108)"}


# --------------------------------------------------------------------------------------------------------- evidence
def evidence_from_ents(ents, roles):
    """the floor's own linework by layer role (engine.source.arch_plan.layer_roles): wall-role face segments,
    window-role glazing (segments and arcs) and door-role swing arcs, in drawing units."""
    def role(lay):
        return roles.get(lay)
    segs = ents.get("segments") or ()
    arcs = ents.get("arcs") or ()
    return {"face_segments": [(tuple(s["a"]), tuple(s["b"])) for s in segs if role(s["layer"]) == "WALL"],
            "glazing_segments": [(tuple(s["a"]), tuple(s["b"])) for s in segs if role(s["layer"]) == "WINDOW"],
            "glazing_arcs": [{"c": tuple(a["c"]), "r": a["r"], "s": tuple(a["s"]), "e": tuple(a["e"]),
                              "m": tuple(a["m"])} for a in arcs if role(a["layer"]) == "WINDOW"],
            "door_arcs": [{"c": tuple(a["c"]), "r": a["r"]} for a in arcs if role(a["layer"]) == "DOOR"]}


def _merge(ivs):
    out = []
    for lo, hi in sorted(ivs):
        if out and lo <= out[-1][1] + 1e-9:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def _covered(ivs, lo, hi):
    return sum(max(0.0, min(b, hi) - max(a, lo)) for a, b in ivs)


class _Band:
    """a straight band in metres: p0, unit u, normal n, length L, half thickness h."""

    def __init__(self, w, k):
        a, b = w["centreline"][0], w["centreline"][-1]
        self.w, self.id, self.t = w, w.get("wall_id"), float(w["t_m"])
        self.family = w.get("family") or V1._family(self.t)
        self.p0 = (a[0] * k, a[1] * k)
        p1 = (b[0] * k, b[1] * k)
        self.L = math.dist(self.p0, p1)
        self.u = V1._unit(V1._sub(p1, self.p0))
        self.n = (-self.u[1], self.u[0])
        self.h = self.t / 2

    def su(self, p):
        d = V1._sub(p, self.p0)
        return V1._dot(d, self.u), V1._dot(d, self.n)

    def at(self, s):
        return (self.p0[0] + self.u[0] * s, self.p0[1] + self.u[1] * s)


def _line_cover(band, segs, k, off_lo, off_hi):
    """the stations of `band` covered by segments parallel to it whose offsets lie in [off_lo, off_hi] (metres)."""
    out = []
    for a, b in segs:
        pa, pb = (a[0] * k, a[1] * k), (b[0] * k, b[1] * k)
        if math.dist(pa, pb) <= 0:
            continue
        v = V1._unit(V1._sub(pb, pa))
        if abs(V1._cross(v, band.u)) > math.sin(FACE_ANG):
            continue
        (sa, oa), (sb, ob) = band.su(pa), band.su(pb)
        if not (off_lo <= oa <= off_hi and off_lo <= ob <= off_hi):
            continue
        lo, hi = max(0.0, min(sa, sb)), min(band.L, max(sa, sb))
        if hi > lo:
            out.append((lo, hi))
    return _merge(out)


def _face_cover(band, segs, k):
    tol = JOIN_TOL_M
    return _merge(_line_cover(band, segs, k, band.h - tol, band.h + tol) +
                  _line_cover(band, segs, k, -band.h - tol, -band.h + tol))


def _undrawn(band, cover):
    out, c = [], 0.0
    for lo, hi in cover:
        if lo - c > MIN_STRETCH_M:
            out.append((c, lo))
        c = max(c, hi)
    if band.L - c > MIN_STRETCH_M:
        out.append((c, band.L))
    return out


def _poly_cover(band, polys):
    """stations of the band centreline inside polygons (metres)."""
    if not polys:
        return []
    from shapely.geometry import LineString
    ln = LineString([band.p0, band.at(band.L)])
    out = []
    for P in polys:
        if not ln.intersects(P):
            continue
        g = ln.intersection(P)
        for part in getattr(g, "geoms", [g]):
            cs = list(getattr(part, "coords", []))
            if len(cs) >= 2:
                ss = [band.su(c)[0] for c in cs]
                out.append((max(0.0, min(ss)), min(band.L, max(ss))))
    return _merge(out)


def _opening_evidence(o):
    """an opening that says the gap is part of a wall: a door / window record (a symbol or glazing), or a passage
    with a head line (the wall face continued across the gap) or a symbol block drawn in it."""
    if o.get("kind") in EVIDENCE_KINDS or o.get("door_symbol"):
        return "SYMBOL"
    ev = o.get("evidence") or {}
    if (ev.get("glazing_lm") or 0) > 0:
        return "GLAZING"
    mk = ev.get("marks") or {}
    if o.get("width_m") is not None and float(o["width_m"]) > MAX_GAP_M:
        return None                   # a symbol-less gap wider than any opening a run is carried across
    if (mk.get("head_lines") or 0) >= 1:
        return "HEAD_LINE"
    if mk.get("blocks"):
        return "SYMBOL_BLOCK"
    return None


def _openings_m(openings):
    out = []
    for o in openings or ():
        c = (o.get("position") or {}).get("centre_m")
        if c is None:
            continue
        out.append((o, (float(c[0]), float(c[1])), _opening_evidence(o)))
    return out


# ------------------------------------------------------------------------------------------------ glazing groupings
def _arc_sweep(a):
    """(start angle, sweep) of an arc record from its start, mid and end points (radians, sweep > 0)."""
    c = a["c"]
    ang = [math.atan2(p[1] - c[1], p[0] - c[0]) for p in (a["s"], a["m"], a["e"])]
    d1 = (ang[1] - ang[0]) % (2 * math.pi)
    d2 = (ang[2] - ang[0]) % (2 * math.pi)
    if d1 <= d2:                     # counter-clockwise from s through m to e
        return ang[0], d2
    return ang[2], (2 * math.pi - d2)


def _glazed_arcs(arcs, k):
    """concentric glazing arcs grouped into glass lines: [{centre, r_mid, sweep, a0, length_m, ends, members}]."""
    items = []
    for a in arcs:
        c = (a["c"][0] * k, a["c"][1] * k)
        a0, sw = _arc_sweep(a)
        items.append({"c": c, "r": a["r"] * k, "a0": a0, "sw": sw})
    used, out = set(), []
    for i, A in enumerate(items):
        if i in used:
            continue
        grp = [i]
        for j, B in enumerate(items):
            if j <= i or j in used:
                continue
            if math.dist(A["c"], B["c"]) <= ARC_CENTRE_TOL_M and abs(A["r"] - B["r"]) <= GLAZED_SET_M:
                # sweeps overlap (mid angle of B within A's sweep, or the reverse)
                mb = (B["a0"] + B["sw"] / 2 - A["a0"]) % (2 * math.pi)
                ma = (A["a0"] + A["sw"] / 2 - B["a0"]) % (2 * math.pi)
                if mb <= A["sw"] or ma <= B["sw"]:
                    grp.append(j)
        rs = [items[g]["r"] for g in grp]
        if len(grp) < 2 or max(rs) - min(rs) > GLAZED_SET_M:
            continue
        used.update(grp)
        rm = (max(rs) + min(rs)) / 2
        sw = sum(items[g]["sw"] for g in grp) / len(grp)          # the members' mean sweep at the mid radius
        c = A["c"]
        ends = []
        for t in (0, 1):                                            # the mean of the members' end points
            ps = [(c[0] + items[g]["r"] * math.cos(items[g]["a0"] + t * items[g]["sw"]),
                   c[1] + items[g]["r"] * math.sin(items[g]["a0"] + t * items[g]["sw"])) for g in grp]
            ends.append((sum(q[0] for q in ps) / len(ps), sum(q[1] for q in ps) / len(ps)))
        e0, e1 = ends
        if rm * sw < GLAZED_MIN_M:
            continue
        out.append({"kind": "CURVED", "centre": c, "r_mid_m": rm, "sweep_rad": sw, "length_m": rm * sw,
                    "ends": (e0, e1), "set_m": max(rs) - min(rs), "members": len(grp),
                    "mid_angle": items[grp[0]]["a0"] + items[grp[0]]["sw"] / 2})
    return out


def _glazed_straight(segs, k, bands):
    """parallel glazing segments grouped into straight glass lines standing outside every wall band."""
    items = []
    for a, b in segs:
        pa, pb = (a[0] * k, a[1] * k), (b[0] * k, b[1] * k)
        L = math.dist(pa, pb)
        if L < GLAZED_MIN_M:
            continue
        items.append((pa, pb, L))
    used, out = set(), []
    for i, (pa, pb, L) in enumerate(items):
        if i in used:
            continue
        u = V1._unit(V1._sub(pb, pa))
        n = (-u[1], u[0])
        grp = [i]
        for j, (qa, qb, M) in enumerate(items):
            if j <= i or j in used:
                continue
            v = V1._unit(V1._sub(qb, qa))
            if abs(V1._cross(u, v)) > math.sin(FACE_ANG):
                continue
            oq = [V1._dot(V1._sub(q, pa), n) for q in (qa, qb)]
            sq = sorted(V1._dot(V1._sub(q, pa), u) for q in (qa, qb))
            if max(abs(x) for x in oq) <= GLAZED_SET_M and min(sq[1], L) - max(sq[0], 0.0) >= 0.5 * min(L, M):
                grp.append(j)
        if len(grp) < 2:
            continue
        ss, oo = [], []
        for g in grp:
            for q in items[g][:2]:
                ss.append(V1._dot(V1._sub(q, pa), u))
                oo.append(V1._dot(V1._sub(q, pa), n))
        mid_off = (max(oo) + min(oo)) / 2
        e0 = (pa[0] + u[0] * min(ss) + n[0] * mid_off, pa[1] + u[1] * min(ss) + n[1] * mid_off)
        e1 = (pa[0] + u[0] * max(ss) + n[0] * mid_off, pa[1] + u[1] * max(ss) + n[1] * mid_off)
        mid = ((e0[0] + e1[0]) / 2, (e0[1] + e1[1]) / 2)
        if any(_inside_band(B, mid) for B in bands):
            used.update(grp)
            continue                  # glazing of a window inside a wall band: the band's opening, not a glass line
        used.update(grp)
        out.append({"kind": "STRAIGHT", "length_m": max(ss) - min(ss), "ends": (e0, e1),
                    "set_m": max(oo) - min(oo), "members": len(grp)})
    return out


def _inside_band(B, p, reach=JOIN_TOL_M):
    s, o = B.su(p)
    return -reach <= s <= B.L + reach and abs(o) <= B.h + reach


def _jamb_stub(A, E, od, g, faces, k, others):
    """T-169 (defect D-T125-1): the jamb stub standing on the near face of the wall across a free-end doorway.

    Seen from the free end E of band A along od, the wall across has its near face at g. A jamb stub is wall drawn
    on that face towards E: BOTH of A's face lines (offsets +-t/2) drawn on a wall-role layer, unbroken from the face
    back to the stub's end (a nib the drawing gives no closing line or wall record of its own), or a collinear wall
    record (an arch_v28 RETURN_STUB) standing in the gap on that face. Its length is wall, not doorway:
      >= JAMB_STUB_MIN_M (the L-P9-04 stub convention, 0.05 m): status WALL, the doorway is g - stub;
      (a wall record is WALL at any length: V1 measures it, so the end stops at it and nothing counts twice);
      shorter face lines: status BELOW_L-P9-04_LISTED, a drafting artefact by that convention: the doorway stays
      g, the stub is listed (never dropped silently);
      one face only drawn: status ONE_FACE_LISTED (a frame or a lining line is not a wall): doorway g, listed.
    Returns {status, stub_m, basis, record_id, faces_m, rule}."""
    nrm = (-od[1], od[0])
    faces_m = []
    for side in (1.0, -1.0):
        ivs = []
        for a, b in faces:
            pa, pb = (a[0] * k, a[1] * k), (b[0] * k, b[1] * k)
            if math.dist(pa, pb) <= 0:
                continue
            if abs(V1._cross(V1._unit(V1._sub(pb, pa)), od)) > math.sin(FACE_ANG):
                continue
            qa, qb = V1._dot(V1._sub(pa, E), od), V1._dot(V1._sub(pb, E), od)
            oa, ob = V1._dot(V1._sub(pa, E), nrm), V1._dot(V1._sub(pb, E), nrm)
            if abs(oa - side * A.h) > JOIN_TOL_M or abs(ob - side * A.h) > JOIN_TOL_M:
                continue
            lo, hi = max(0.0, min(qa, qb)), min(g, max(qa, qb))
            if hi > lo:
                ivs.append((lo, hi))
        ext = 0.0
        for lo, hi in reversed(_merge(ivs)):
            if hi >= g - JOIN_TOL_M:
                ext = g - lo
            break
        faces_m.append(round(ext, 4))
    face_stub = min(faces_m)
    rec_stub, rec_id = 0.0, None
    for D in others:
        if abs(V1._cross(D.u, od)) >= V1.PARALLEL_SIN:
            continue
        if abs(V1._dot(V1._sub(D.p0, E), nrm)) > A.h + JOIN_TOL_M:
            continue
        q = sorted(V1._dot(V1._sub(p, E), od) for p in (D.p0, D.at(D.L)))
        if q[0] > JOIN_TOL_M and q[1] >= g - JOIN_TOL_M and q[0] < g - 1e-6 and g - q[0] > rec_stub:
            rec_stub, rec_id = g - q[0], D.id
    out = {"rule": "L-P9-04 (stubs under 0.05 m are drafting artefacts; T-169)", "faces_m": faces_m,
           "record_id": rec_id}
    if rec_stub > 0:                   # a wall record V1 measures itself: the free end stops at it (never twice)
        stub, basis = rec_stub, "WALL_RECORD"
    else:
        stub, basis = face_stub, "FACE_LINES"
    out.update(stub_m=round(stub, 4), basis=basis)
    if stub >= JAMB_STUB_MIN_M - 1e-9 or basis == "WALL_RECORD":
        out["status"] = "WALL"
        out["note"] = ("jamb stub on the face of the wall across: wall (in the run and in the physical blockwork "
                       "length), not doorway" + ("; it is its own wall record, the free end stops at it"
                                                 if basis == "WALL_RECORD" else ""))
    elif stub >= 1e-3:
        out["status"] = "BELOW_L-P9-04_LISTED"
        out["note"] = "shorter than 0.05 m: a drafting artefact by L-P9-04; left in the doorway, listed here"
    elif max(faces_m) >= 1e-3:
        out["status"] = "ONE_FACE_LISTED"
        out["stub_m"] = round(max(faces_m), 4)
        out["note"] = "one face line only on the wall layer (not a wall piece by itself): left in the doorway, listed"
    else:
        out["status"] = "NONE"
    return out


# ------------------------------------------------------------------------------------------------------ the measure
def _sub_record(w, k, s0, s1, band, idx):
    """a part [s0, s1] (metres along the band) of a straight wall record, in the record's drawing units."""
    a, b = band.at(s0), band.at(s1)
    r = dict(w)
    r["wall_id"] = f"{w.get('wall_id')}#{idx}"
    r["centreline"] = [(a[0] / k, a[1] / k), (b[0] / k, b[1] / k)]
    r["gross_lm"] = round(s1 - s0, 9)
    r["columns_in_wall_lm"] = 0.0
    r["_parent"] = w.get("wall_id")
    r["_span"] = (s0, s1)
    return r


def measure(walls, unit_m=None, openings=(), columns_m=None, floor=None, evidence=None):
    """the V2 masonry centreline run of one floor (see the module docstring)."""
    walls = list(walls or ())
    rec = {"policy": POLICY_ID, "rules": list(RULES), "floor": floor, "status": None, "unit_m": None,
           "by_thickness": [], "runs": [], "stretches": [], "doorways": [], "jamb_stubs": [], "bays": [],
           "glazed_lines": [], "piers": [], "identity": None, "held": [], "v1": None, "height": dict(HEIGHT_HELD)}
    if not walls:
        rec["status"] = "NO_WALL_BANDS"
        rec["why"] = "no wall band on this floor: the masonry run is not measured (None, never 0)"
        return rec
    k = unit_m if unit_m is not None else V1.drawing_unit(walls)
    if k is None:
        rec["status"] = "HELD"
        rec["why"] = "the drawing unit cannot be read from the bands (gross_lm / centreline length disagree)"
        return rec
    rec["unit_m"] = k
    missing = [n for n, v in (("columns_m", columns_m), ("evidence", evidence)) if v is None]
    if missing:
        rec["status"] = "HELD"
        rec["why"] = ("required input not given: " + ", ".join(missing) + " (column outlines: without them L corners "
                      "are over-counted; evidence: without the face linework no band can be checked for open floor); "
                      "V1 figures are not re-published as V2")
        return rec
    from shapely.geometry import Polygon
    col_polys = [Polygon(p) for p in columns_m if len(p) >= 3]
    ops = _openings_m(openings)
    straight_w = [w for w in walls if not w.get("curved") and w.get("centreline")
                  and not (w.get("stub") and w.get("kind") != "RETURN_STUB")
                  and math.dist(w["centreline"][0], w["centreline"][-1]) > 0]
    other_w = [w for w in walls if w not in straight_w]
    bands = [_Band(w, k) for w in straight_w]
    bays = _glazed_arcs(evidence.get("glazing_arcs") or (), k)
    glz_lines = _glazed_straight(evidence.get("glazing_segments") or (), k, bands)
    faces = evidence.get("face_segments") or ()
    glz = evidence.get("glazing_segments") or ()

    # 1. undrawn stretches: classify, keep or split
    pieces_w = []                      # the band records V1 measures
    span_tags = defaultdict(list)      # band id -> [(s0, s1, tag, ref)] kept stretches with an opening or glazing
    bay_used = set()
    for B in bands:
        cover = _face_cover(B, faces, k)
        cols = _poly_cover(B, col_polys)
        cuts = []
        for lo, hi in _undrawn(B, cover):
            L = hi - lo
            mid = B.at((lo + hi) / 2)
            st = {"floor": floor, "wall_id": B.id, "family": B.family, "from_m": round(lo, 4), "to_m": round(hi, 4),
                  "length_m": round(L, 4), "bridged_by": None, "ref": None, "in_run": True}
            # a curved glazed bay over this stretch (fix 3)
            bay = None
            for bi, g in enumerate(bays):
                if bi in bay_used:
                    continue
                (s0, o0), (s1, o1) = B.su(g["ends"][0]), B.su(g["ends"][1])
                ch = V1._unit(V1._sub(g["ends"][1], g["ends"][0]))
                if abs(V1._cross(ch, B.u)) > math.sin(BAY_ANG):
                    continue
                if max(abs(o0), abs(o1)) > B.h + BAY_REACH_M:
                    continue
                a, b = sorted((s0, s1))
                if a >= lo - BAY_END_TOL_M and b <= hi + BAY_END_TOL_M and b - a >= BAY_COVER * (hi - lo):
                    bay = (bi, g)
                    break
            covered_col = _covered(cols, lo, hi)
            cross = [C for C in bands if C is not B and abs(V1._cross(C.u, B.u)) >= V1.PARALLEL_SIN
                     and _inside_band(C, mid, reach=0.0)]
            op = [(o, ev) for o, c, ev in ops if ev and lo - JOIN_TOL_M <= B.su(c)[0] <= hi + JOIN_TOL_M
                  and abs(B.su(c)[1]) <= B.h + JOIN_TOL_M]
            glz_cov = _covered(_line_cover(B, glz, k, -B.h - JOIN_TOL_M, B.h + JOIN_TOL_M), lo, hi)
            if bay is not None:
                bi, g = bay
                bay_used.add(bi)
                cut, arc, sw, basis = (lo, hi), g["length_m"], g["sweep_rad"], "GLAZING_ENDS"
                # the glass mid circle carried to the straight centreline (the run's own line, as at an L corner):
                # the chord leaves the band between the two meeting points, the arc between them joins the run
                c, rm = g["centre"], g["r_mid_m"]
                sc, dc = B.su(c)
                if abs(dc) < rm:
                    phi = math.acos(abs(dc) / rm)
                    th0 = math.atan2(-B.n[1] * math.copysign(1, dc), -B.n[0] * math.copysign(1, dc))
                    dm = abs((g["mid_angle"] - th0 + math.pi) % (2 * math.pi) - math.pi)
                    sw2 = 2 * phi if dm <= phi else 2 * math.pi - 2 * phi
                    half = rm * math.sin(phi)
                    a, b = sc - half, sc + half
                    if abs(a - lo) <= BAY_REACH_M + B.h and abs(b - hi) <= BAY_REACH_M + B.h and \
                            a >= -JOIN_TOL_M and b <= B.L + JOIN_TOL_M:
                        cut, arc, sw, basis = (max(a, 0.0), min(b, B.L)), rm * sw2, sw2, "CENTRELINE_MEETING"
                st.update(bridged_by="CURVED_GLAZED_BAY", in_run=False, from_m=round(cut[0], 4), to_m=round(cut[1], 4),
                          length_m=round(cut[1] - cut[0], 4),
                          ref=f"arc r {rm:.3f} m, sweep {sw:.4f} rad ({basis})")
                cuts.append(cut)
                rec["bays"].append({"floor": floor, "wall_id": B.id, "family": B.family,
                                    "chord_m": round(cut[1] - cut[0], 4), "arc_m": round(arc, 4),
                                    "r_mid_m": round(rm, 4), "sweep_rad": round(sw, 6), "basis": basis,
                                    "glazing_drawn_arc_m": round(g["length_m"], 4),
                                    "glazing_set_m": round(g["set_m"], 4), "_c": c, "_rm": rm, "_t": B.t,
                                    "status": "GLAZED_LINE: the arc replaces the chord in the run (owner Q-69 B: "
                                              "glass, not blockwork; masonry above / below HELD)"})
            elif covered_col >= COVER_SHARE * L and L - covered_col <= MIN_STRETCH_M:
                st.update(bridged_by="COLUMN")
            elif cross:
                st.update(bridged_by="CROSSING_BAND", ref=",".join(sorted(str(C.id) for C in cross)))
                # both walls drawn through the crossing (each band runs on past the other): split both here, and
                # V1's cross rule counts the piece once (one family) or holds it (two families)
                if all(-JOIN_TOL_M <= C.su(mid)[0] - B.h / max(abs(V1._cross(C.u, B.u)), 1e-9) and
                       C.su(mid)[0] + B.h / max(abs(V1._cross(C.u, B.u)), 1e-9) <= C.L + JOIN_TOL_M for C in cross):
                    st.update(bridged_by="CROSSING_THROUGH_BOTH",
                              note="both walls run through: split here, V1 cross rule (one family: joined once; two "
                                   "families: HELD)")
                    cuts.append((lo, hi))
            elif op:
                o, ev = op[0]
                st.update(bridged_by=f"OPENING_{ev}", ref=",".join(str(x.get("opening_id")) for x, _e in op),
                          kind=o.get("kind"), width_m=o.get("width_m"))
                span_tags[B.id].append((lo, hi, o.get("kind") or "OPENING", o.get("opening_id")))
                wsum = sum(float(x.get("width_m") or 0.0) for x, _e in op)
                if L - wsum > max(OPEN_FIT_M, OPEN_FIT_SHARE * L):
                    rec["held"].append({"what": "STRETCH_PARTLY_EVIDENCED", "wall_id": B.id, "family": B.family,
                                        "stretch_m": round(L, 4), "openings_m": round(wsum, 4),
                                        "max_lm": round(L - wsum, 4),
                                        "reason": "the undrawn stretch is longer than the openings in it: kept in the "
                                                  "run as V1 keeps it, but up to max_lm of it may be open floor"})
            elif glz_cov >= COVER_SHARE * L:
                st.update(bridged_by="GLAZING_IN_BAND")
                span_tags[B.id].append((lo, hi, "GLAZED", None))
            else:
                st.update(bridged_by=None, in_run=False,
                          reason="neither face drawn on a wall layer and no column, crossing wall, door / window, "
                                 "passage head line, symbol block or glazing in the stretch: not wall; the band "
                                 "is split here")
                cuts.append((lo, hi))
            rec["stretches"].append(st)
        # the kept parts of the band
        parts, c = [], 0.0
        for lo, hi in sorted(cuts):
            if lo - c > 1e-9:
                parts.append((c, lo))
            c = max(c, hi)
        if B.L - c > 1e-9:
            parts.append((c, B.L))
        if len(parts) == 1 and parts[0] == (0.0, B.L):
            r = dict(B.w)
            r["_parent"], r["_span"] = B.id, (0.0, B.L)
            pieces_w.append(r)
        else:
            for i, (lo, hi) in enumerate(parts):
                pieces_w.append(_sub_record(B.w, k, lo, hi, B, i + 1))
    # a curved wall stub lying on a bay's circle is the masonry end of that bay: it is in the bay's arc, once
    absorbed = []
    for w in other_w:
        if not (w.get("stub") and w.get("centreline")):
            continue
        ps = [(q[0] * k, q[1] * k) for q in (w["centreline"][0], w["centreline"][-1])]
        for b in rec["bays"]:
            if all(abs(math.dist(q, b["_c"]) - b["_rm"]) <= b["_t"] / 2 + JOIN_TOL_M for q in ps):
                L = float(w.get("gross_lm") or 0.0)
                b["masonry_in_arc_m"] = round(b.get("masonry_in_arc_m", 0.0) + L, 4)
                b.setdefault("masonry_pieces", []).append(w.get("wall_id"))
                absorbed.append(w)
                break
    other_w = [w for w in other_w if all(w is not a for a in absorbed)]
    for b in rec["bays"]:
        for kk in ("_c", "_rm", "_t"):
            b.pop(kk, None)
    # glazed bays that matched no band and glass lines on their own: listed, family not drawn
    for bi, g in enumerate(bays):
        if bi not in bay_used and not any(_inside_band(B, g["ends"][0], B.h) and _inside_band(B, g["ends"][1], B.h)
                                          for B in bands):
            rec["glazed_lines"].append({"floor": floor, "kind": "CURVED", "length_m": round(g["length_m"], 4),
                                        "r_mid_m": round(g["r_mid_m"], 4), "glazing_set_m": round(g["set_m"], 4)})
    for g in glz_lines:
        rec["glazed_lines"].append({"floor": floor, "kind": "STRAIGHT", "length_m": round(g["length_m"], 4),
                                    "glazing_set_m": round(g["set_m"], 4)})
    for g in rec["glazed_lines"]:
        g["status"] = ("GLAZED_LINE (owner Q-69 B): in the architectural run, not blockwork; its wall family is not "
                       "drawn (the glass has no block thickness), so it is listed beside the families, never added to "
                       "one; masonry above / below HELD")

    # 2. doorways at free ends (fix 2): carry the end to the near face of the wall across the doorway
    pbands = [_Band(w, k) for w in pieces_w]
    door_arcs = [{"c": (a["c"][0] * k, a["c"][1] * k), "r": a["r"] * k} for a in evidence.get("door_arcs") or ()]
    for A, w in zip(pbands, pieces_w):
        for end in (0, 1):
            E = A.at(0.0 if end == 0 else A.L)
            od = (-A.u[0], -A.u[1]) if end == 0 else A.u
            touching, best = False, None
            for C in pbands:
                if C is A:
                    continue
                sn = V1._cross(A.u, C.u)
                if abs(sn) < V1.PARALLEL_SIN:
                    continue
                # where A's centreline carried on meets C's centreline, and C's near face along A
                d = V1._sub(C.p0, E)
                a = V1._cross(d, C.u) / V1._cross(od, C.u)
                X = (E[0] + od[0] * a, E[1] + od[1] * a)
                xs = C.su(X)[0]
                hC, hA = C.h / abs(sn), A.h / abs(sn)
                if not (-hA - JOIN_TOL_M <= xs <= C.L + hA + JOIN_TOL_M):
                    continue
                g = a - hC
                if g <= JOIN_TOL_M and a >= -hC - JOIN_TOL_M:
                    touching = True
                    break
                if JOIN_TOL_M < g <= MAX_GAP_M and (best is None or g < best[0]):
                    best = (g, C)
            if touching or best is None:
                continue
            g, C = best
            # a jamb stub standing on C's near face (T-169, defect D-T125-1): wall, not doorway
            jamb = _jamb_stub(A, E, od, g, faces, k, [D for D in pbands if D is not A])
            gd = g - jamb["stub_m"] if jamb["status"] == "WALL" else g      # the doorway between the jambs
            if gd <= JOIN_TOL_M:
                continue
            # nothing else in the gap: no column, no parallel band (a collinear neighbour is V1's opening gap)
            gap_mid = (E[0] + od[0] * gd / 2, E[1] + od[1] * gd / 2)
            if any(P.distance(_pt(gap_mid)) <= A.h for P in col_polys):
                continue
            if any(D is not A and abs(V1._cross(A.u, D.u)) < V1.PARALLEL_SIN and
                   any(_inside_band(D, (E[0] + od[0] * gd * f, E[1] + od[1] * gd * f), 0.0)
                       for f in (0.25, 0.5, 0.75))
                   for D in pbands):
                continue
            # door evidence in the gap (the doorway between the jambs, gd)
            why = None
            for o, c, ev in ops:
                if o.get("kind") != "DOOR" and not o.get("door_symbol"):
                    continue
                sa = V1._dot(V1._sub(c, E), od)
                oa = V1._dot(V1._sub(c, E), (-od[1], od[0]))
                if -JOIN_TOL_M <= sa <= gd + JOIN_TOL_M and abs(oa) <= A.h + JOIN_TOL_M and \
                        o.get("width_m") is not None and float(o["width_m"]) <= gd + JOIN_TOL_M and \
                        gd <= float(o["width_m"]) + SWING_FRAME_M:
                    why = ("DOOR_RECORD", o.get("opening_id"), o.get("width_m"))
                    break
            if why is None:
                for sw in door_arcs:
                    sa = V1._dot(V1._sub(sw["c"], E), od)
                    oa = V1._dot(V1._sub(sw["c"], E), (-od[1], od[0]))
                    if -SWING_REACH_M <= sa <= gd + SWING_REACH_M and abs(oa) <= A.h + SWING_REACH_M and \
                            SWING_LEAF_M[0] <= sw["r"] <= min(SWING_LEAF_M[1], gd + JOIN_TOL_M) and \
                            gd <= sw["r"] + SWING_FRAME_M:
                        why = ("DOOR_SWING", None, round(sw["r"], 4))
                        break
            if why is None:
                continue
            # move the record's end to C's near face; a jamb stub drawn only as face lines is carried with it (in the
            # run, as wall); a jamb stub that is its own wall record stays that record's run: the end stops at it
            s0, s1 = w["_span"]
            P0, P1 = w["centreline"][0], w["centreline"][-1]
            reach = gd if jamb["basis"] == "WALL_RECORD" and jamb["status"] == "WALL" else g
            Pn = (E[0] + od[0] * reach, E[1] + od[1] * reach)
            if end == 0:
                w["centreline"] = [(Pn[0] / k, Pn[1] / k), P1]
            else:
                w["centreline"] = [P0, (Pn[0] / k, Pn[1] / k)]
            w["gross_lm"] = round(math.dist(w["centreline"][0], w["centreline"][-1]) * k, 9)
            w["_doorway"] = w.get("_doorway", []) + [(g, E, od, gd)]
            dw = {"floor": floor, "wall_id": w["wall_id"], "end": end, "gap_m": round(gd, 4),
                  "to_wall": C.id, "evidence": why[0], "opening_id": why[1], "width_or_leaf_m": why[2],
                  "face_to_face_m": round(g, 4)}
            if jamb["status"] != "NONE":
                js = dict(jamb, floor=floor, wall_id=w["wall_id"], end=end, to_wall=C.id)
                dw["jamb_stub"] = js
                rec["jamb_stubs"].append(js)
            rec["doorways"].append(dw)

    # 3. V1 on the checked records (its junction rules, its column cut, its opening-gap join)
    v1_ops = [o for o, c, ev in ops if ev]
    v1 = V1.measure(pieces_w + other_w, unit_m=k, openings=v1_ops, columns_m=columns_m, floor=floor)
    rec["v1"] = {kk: v1.get(kk) for kk in ("status", "junctions", "held", "column_basis")}
    rec["held"] = rec["held"] + list(v1.get("held") or [])

    # 4. the five Q-69 lengths per run
    by_id = {w["wall_id"]: w for w in pieces_w}
    fam = defaultdict(lambda: defaultdict(float))
    for p in v1.get("pieces") or ():
        members = [p["wall_id"]] + list(p.get("joined") or [])
        run = float(p["run_lm"])
        f = p.get("family")
        opn = []
        if p["wall_id"] in by_id:
            ws = [by_id[m] for m in members if m in by_id]
            base = _Band(ws[0], k)
            ss = []
            for wv in ws:
                ss += [base.su((q[0] * k, q[1] * k))[0] for q in (wv["centreline"][0], wv["centreline"][-1])]
            lo, hi = min(ss), max(ss)
            gaps = [(g, E, od) for wv in ws for g, E, od, _gd in wv.get("_doorway", ())]
            for o, c, ev in ops:
                sc, oc = base.su(c)
                if any(-JOIN_TOL_M <= V1._dot(V1._sub(c, E), od) <= g + JOIN_TOL_M for g, E, od in gaps):
                    continue              # the door of a doorway at a free end: counted once, as the doorway
                if lo - JOIN_TOL_M <= sc <= hi + JOIN_TOL_M and abs(oc) <= base.h + JOIN_TOL_M and \
                        o.get("width_m") is not None:
                    opn.append({"what": o.get("kind") or "OPENING", "opening_id": o.get("opening_id"),
                                "width_m": round(float(o["width_m"]), 4), "evidence": ev})
            for wv in ws:
                for lo2, hi2, tag, ref in span_tags.get(wv["_parent"], ()):
                    if tag == "GLAZED" and wv["_span"][0] - 1e-6 <= lo2 and hi2 <= wv["_span"][1] + 1e-6:
                        opn.append({"what": "GLAZED_STRETCH", "opening_id": None, "width_m": round(hi2 - lo2, 4),
                                    "evidence": "GLAZING_IN_BAND"})
                for _g, _E, _od, gd in wv.get("_doorway", ()):
                    opn.append({"what": "DOORWAY_AT_FREE_END", "opening_id": None, "width_m": round(gd, 4),
                                "evidence": "DOOR_RECORD_OR_SWING"})
        op_lm = sum(x["width_m"] for x in opn)
        glass = sum(x["width_m"] for x in opn if x["what"] in ("WINDOW", "GLAZED_STRETCH"))
        physical = run - op_lm
        row = {"floor": floor, "run_id": p["wall_id"], "members": members, "family": f, "t_m": p.get("t_m"),
               "ends": p.get("ends"), "arch_run_lm": round(run, 4), "openings_in_run": opn,
               "openings_lm": round(op_lm, 4), "physical_blockwork_lm": round(physical, 4),
               "glass_aluminium_lm": round(glass, 4), "masonry_above_below": dict(ABOVE_BELOW_HELD),
               "net_area_inputs": {"physical_blockwork_lm": round(physical, 4), "openings": opn,
                                   "height": dict(HEIGHT_HELD)}}
        if physical < -JOIN_TOL_M:
            row["check"] = "OPENINGS_EXCEED_RUN: an opening record overlaps a column or another run; HELD"
            rec["held"].append({"what": "RUN_OPENINGS", "run_id": p["wall_id"], "reason": row["check"]})
        rec["runs"].append(row)
        if run < PIER_T * float(p.get("t_m") or 0) and not str(p["wall_id"]).startswith("ARCBAND"):
            rec["piers"].append({"floor": floor, "run_id": p["wall_id"], "family": f, "run_lm": round(run, 4),
                                 "note": "shorter than 4 t: a pier, listed as a linear item (kept in the run)"})
        F = fam[f]
        F["arch_run_lm"] += run
        F["openings_lm"] += op_lm
        F["physical_blockwork_lm"] += physical
        F["glass_aluminium_lm"] += glass
        F["runs"] += 1
    for b in rec["bays"]:
        F = fam[b["family"]]
        mas = float(b.get("masonry_in_arc_m") or 0.0)
        glass = b["arc_m"] - mas
        F["arch_run_lm"] += b["arc_m"]
        F["glass_aluminium_lm"] += glass
        F["openings_lm"] += glass
        F["physical_blockwork_lm"] += mas
        F["runs"] += 1
        rec["runs"].append({"floor": floor, "run_id": f"BAY|{b['wall_id']}", "members": b.get("masonry_pieces", []),
                            "family": b["family"], "arch_run_lm": b["arc_m"],
                            "openings_in_run": [{"what": "CURVED_GLAZED_BAY", "width_m": round(glass, 4)}],
                            "openings_lm": round(glass, 4), "physical_blockwork_lm": round(mas, 4),
                            "glass_aluminium_lm": round(glass, 4), "masonry_above_below": dict(ABOVE_BELOW_HELD)})
    v1fam = {r["family"]: r for r in v1.get("by_thickness") or ()}
    split_out = defaultdict(float)
    for st in rec["stretches"]:
        if not st["in_run"] and st["bridged_by"] is None:
            split_out[st["family"]] += st["length_m"]
    for f in sorted(set(fam) | set(v1fam)):
        F, R = fam[f], v1fam.get(f) or {}
        v2_held = sum(h["max_lm"] for h in rec["held"] if h.get("what") == "STRETCH_PARTLY_EVIDENCED"
                      and h.get("family") == f)
        rec["by_thickness"].append({
            "family": f, "status": ("MEASURED_WITH_HELD_PIECES" if v2_held else (R.get("status") or "MEASURED")),
            "arch_run_lm": round(F["arch_run_lm"], 4), "physical_blockwork_lm": round(F["physical_blockwork_lm"], 4),
            "openings_lm": round(F["openings_lm"], 4), "glass_aluminium_lm": round(F["glass_aluminium_lm"], 4),
            "masonry_above_below": dict(ABOVE_BELOW_HELD), "net_area_inputs": "per run (runs[].net_area_inputs)",
            "held_max_lm": round((R.get("held_max_lm") or 0.0) + v2_held, 6), "columns_lm": R.get("columns_lm"),
            "split_out_lm": round(split_out.get(f, 0.0), 4), "runs": int(F["runs"]),
            "block_m2": dict(HEIGHT_HELD), "block_m3": dict(HEIGHT_HELD)})
    rec["glazed_lines_lm"] = round(sum(g["length_m"] for g in rec["glazed_lines"]), 4)
    rec["identity"] = _identity(v1, pieces_w + other_w, k, col_polys)
    rec["status"] = "MEASURED" if not rec["held"] else "MEASURED_WITH_HELD_PIECES"
    return rec


def _pt(p):
    from shapely.geometry import Point
    return Point(p)


def _identity(v1, records, k, col_polys=()):
    """sum(run x t) of the straight pieces = the area of the union of their strips, each junction end carried over
    the other wall's far face (an L corner piece and a T stem's seat are then inside the union once); the column
    outlines are cut from the union (concrete, UP-COL-ORIENT-001) as V1 cuts them from the run. Curved pieces add
    arc x t exactly to both sides and are left out. A piece whose own strip less the columns is not its run x t (a
    column standing in only part of the wall width: V1's centreline cut removes the full width) is listed with its
    share, so the floor difference is explained piece by piece."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    by = {w["wall_id"]: w for w in records}
    strips, total, listed = [], 0.0, []
    cols_u = unary_union(col_polys) if col_polys else None
    junc = defaultdict(list)
    for j in v1.get("junctions") or ():
        if j.get("kind") in ("L", "T_STEM") and "end" in j:
            junc[j["members"][0]].append((j["end"], j["members"][1:]))
    pieces = [p for p in v1.get("pieces") or () if p["wall_id"] in by and not by[p["wall_id"]].get("curved")]
    n_ok = 0
    for p in pieces:
        w = by[p["wall_id"]]
        t = float(p["t_m"])
        joined = [by[m] for m in p.get("joined") or () if m in by]
        pts = [(q[0] * k, q[1] * k) for ww in [w] + joined for q in (ww["centreline"][0], ww["centreline"][-1])]
        a0 = (w["centreline"][0][0] * k, w["centreline"][0][1] * k)
        a1 = (w["centreline"][-1][0] * k, w["centreline"][-1][1] * k)
        u = V1._unit(V1._sub(a1, a0))
        n = (-u[1], u[0])
        ss = [V1._dot(V1._sub(q, a0), u) for q in pts]
        lo, hi = min(ss), max(ss)
        ext = list(p.get("corner_ext_m") or [0.0, 0.0])
        # each junction end is carried on to the far face of the wall it meets (an L corner square, a T stem's seat):
        # inside the other wall's strip, so the union counts that square once
        e = [0.0, 0.0]
        for end, others in junc.get(p["wall_id"], ()):
            E = (a0[0] + u[0] * ((lo - ext[0]) if end == 0 else (hi + ext[1])),
                 a0[1] + u[1] * ((lo - ext[0]) if end == 0 else (hi + ext[1])))
            od = (-u[0], -u[1]) if end == 0 else u
            for o in others:
                if o not in by:
                    continue
                b0 = (by[o]["centreline"][0][0] * k, by[o]["centreline"][0][1] * k)
                b1 = (by[o]["centreline"][-1][0] * k, by[o]["centreline"][-1][1] * k)
                v = V1._unit(V1._sub(b1, b0))
                sn = V1._cross(od, v)
                if abs(sn) < V1.PARALLEL_SIN:
                    continue
                dX = V1._cross(V1._sub(b0, E), v) / sn          # E + dX od lies on the other centreline
                e[end] = max(e[end], dX + float(by[o]["t_m"]) / 2 / abs(sn))
        s0 = lo - ext[0] - max(e[0], 0.0)
        s1 = hi + ext[1] + max(e[1], 0.0)
        poly = Polygon([(a0[0] + u[0] * s + n[0] * o, a0[1] + u[1] * s + n[1] * o)
                        for s, o in ((s0, -t / 2), (s1, -t / 2), (s1, t / 2), (s0, t / 2))])
        strips.append(poly)
        total += float(p["run_lm"]) * t
        if cols_u is not None and float(p.get("columns_lm") or 0) > 0:
            flat = Polygon([(a0[0] + u[0] * s + n[0] * o, a0[1] + u[1] * s + n[1] * o)
                            for s, o in ((lo - ext[0], -t / 2), (hi + ext[1], -t / 2), (hi + ext[1], t / 2),
                                         (lo - ext[0], t / 2))])
            d = flat.difference(cols_u).area - float(p["run_lm"]) * t
            if abs(d) > 0.001 * t:
                listed.append({"run_id": p["wall_id"], "m2": round(d, 6), "lm_equiv": round(d / t, 4),
                               "reason": "a column stands in only part of the wall width: the run cuts the full "
                                         "width over the column stretch; the strip beside the column is in no run"})
        n_ok += 1
    if not strips:
        return None
    U = unary_union(strips)
    if col_polys:
        U = U.difference(unary_union(col_polys))         # columns are concrete: out of both sides
    U = U.area
    # the carried-over seats sit inside the through wall (counted there): remove what lies outside the pieces' own
    # union only by construction; the union counts every square metre once
    diff = U - total
    tmax = max(float(p["t_m"]) for p in pieces)
    tol = 0.001 * tmax * n_ok
    expl = sum(x["m2"] for x in listed)
    status = "PASS" if abs(diff) <= tol else ("PASS_WITH_LISTED_PIECES" if abs(diff - expl) <= tol else "DIFFERS")
    return {"strip_union_m2": round(U, 6), "sum_run_x_t_m2": round(total, 6), "diff_m2": round(diff, 6),
            "tolerance_m2": round(tol, 6), "pieces": n_ok, "listed": listed, "listed_m2": round(expl, 6),
            "status": status,
            "note": "a difference = a piece counted twice (negative) or a junction piece in no run (positive); "
                    "45 deg and held ends are listed in held[] and explain their own share"}


def measure_floors(floors):
    """{floor: {"walls", "openings", "columns_m", "ents", "roles", "unit_m"}} -> {floor: measure(...)}."""
    out = {}
    for fl, f in floors.items():
        ev = evidence_from_ents(f["ents"], f["roles"]) if f.get("ents") is not None else None
        out[fl] = measure(f.get("walls"), unit_m=f.get("unit_m"), openings=f.get("openings") or (),
                          columns_m=f.get("columns_m"), floor=fl, evidence=ev)
    return out


def policy_record():
    return {"policy_id": POLICY_ID, "rules": list(RULES), "reuses": V1.POLICY_ID, "join_tol_m": JOIN_TOL_M,
            "max_gap_m": MAX_GAP_M, "min_stretch_m": MIN_STRETCH_M, "jamb_stub_min_m": JAMB_STUB_MIN_M,
            "glazed_min_m": GLAZED_MIN_M,
            "never": ["a masonry m2 or m3 (Q-60 heights: T-108)", "an opening deducted from the architectural run",
                      "a split stretch dropped without a listing", "a glazed line added to a block family",
                      "a missing input given 0 or replaced by V1 figures"]}
