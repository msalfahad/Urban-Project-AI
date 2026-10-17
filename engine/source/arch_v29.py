"""ARCH_TAKEOFF_V2.9 (Phase N10) - curved wall openings (generic; stdlib only). Read only by ARCH_TAKEOFF_V2.9.

D-P9-01 / D-P9-02. A curved wall band is two concentric wall-layer arcs a wall thickness apart (arch_v27.arc_bands).
A gap in it is an OPENING exactly when a straight band's gap is one (lintel_measure.openings): both faces stop over
the same angular span and a jamb line (on a wall layer, along the radius) closes the band at each end. Then:

    curved_gaps(ents, wall_layers, unit_m)     -> (gaps, rejected)  the jambed gaps of the curved bands; a gap with a
                                                  missing jamb, faces stopping at different angles, a wall arc inside
                                                  it, a sweep over 180 degrees or a mid-band arc under MIN_GAP_M is
                                                  rejected with its reason (never an opening)
    glazing_in(gap, ents, layers, unit_m)      -> the glazing inside the gap's annular sector: concentric arcs whose
                                                  radius lies strictly between the two faces, and segments whose middle
                                                  lies there (faceted glazing); the share of the gap's sweep covered
    curved_glazing_roles(ents, L, unit_m, override)
                                               -> layer roles where an OTHER layer whose linework lies mostly inside
                                                  the curved (and straight) wall gaps, with at least one concentric
                                                  glazing arc covering half a curved gap, is a WINDOW layer (D-P9-01);
                                                  a declared role is never changed
    curved_openings(gaps, ents, win_layers, swings, unit_m, served)
                                               -> [opening record]: DOOR (a free swing hinged at a jamb whose leaf
                                                  fits the gap's chord), WINDOW (glazing over at least half the
                                                  sweep, the straight rule), else PASSAGE
    thresholds(op)                             -> [(opening_id, BoundaryItem)]: the gap closed on BOTH wall faces by
                                                  arcs of the faces' own radii (zero material, as the straight
                                                  thresholds), so the room ends at its own wall face and the piece in
                                                  the wall thickness is a reveal / threshold face (D-P9-02: never
                                                  floor); the glazing arc splits that piece, as straight glazing does
    room_side(ops, faces)                      -> each curved opening's room side and width basis

The opening record carries the straight fields the downstream readers use on the opening's CHORD FRAME: u the tangent
at the gap's middle angle, n the outward radial there, s0 / s1 the room-face chord ends, o0 / o1 the two faces at
the middle angle, centre at mid wall and mid angle. Its "curved" record is the geometry itself: centre and radii (in
drawing units too, as the straight records' frame), angles,
angles, every published basis of engine.source.curved_opening (MIN_RADIUS_ARC, MID_BAND_ARC, MAX_RADIUS_ARC, CHORD)
and the glazing radii. width_m is the arc of the face the rooms meet (ROOM_SIDE_ARC): MAX_RADIUS_ARC when only the
outer face bounds a room, else MIN_RADIUS_ARC (the inner face; also when rooms meet both faces - recorded, the outer
room's deduction then rests on the inner arc - or no room meets it).
"""

from __future__ import annotations

import math

from engine.source import arch_v27 as V27
from engine.source import curved_opening as CO
from engine.source import topology as TP

POLICY_ID = "ARCH_TAKEOFF_V2_9_CURVED_OPENINGS"
TWO_PI = 2.0 * math.pi
BAND_T_M = (0.10, 0.45)              # the wall-band thickness range (arch_plan.BAND_T_M)
CENTRE_TOL_M = V27.ARC_CENTRE_TOL_M  # concentric within 2 mm (arch_v27.arc_bands)
RADIUS_TOL_M = 0.001                 # one face radius within 1 mm; glazing strictly inside the faces by this
END_TOL_M = 0.005                    # arcs of one face closer than 5 mm along the arc are one face run
SPLAY_M = 0.03                       # the faces may stop up to 30 mm apart along the arc (a jamb not quite radial;
                                     # the straight band gaps' jamb tolerance, lintel_measure: 30 mm)
JAMB_TOL_M = 0.01                    # a jamb line joins the two face ends within 10 mm (arch_v27.JAMB_TOL_M)
MIN_GAP_M = 0.40                     # mid-band arc of the smallest opening (arch_plan.layer_roles window gaps)
MAX_SWEEP_RAD = math.pi              # a curved opening sweeps at most half a turn
GLAZING_SHARE = 0.5                  # glazing over this share of the gap makes a WINDOW (the straight rule)
LAYER_SHARE = 0.5                    # a layer is glazing when this share of its linework lies in wall gaps
HINGE_AT_JAMB_M = 0.30               # a door hinge at a jamb (arch_rooms.HINGE_AT_GAP_M)
LEAF_FIT_M = 0.15                    # the leaf fits the chord within this or 25 % (arch_rooms.DOOR_LEAF_FIT_M)
ROOM_CLASSES = ("ROOM", "MIXED", "MERGED", "UNLABELLED")


# ------------------------------------------------------------------------------------------- angular intervals
def _adiff(a, b):
    return abs((a - b + math.pi) % TWO_PI - math.pi)


def _union(ivs, tol):
    """merged CCW intervals on the circle (start in [0, 2 pi)); intervals closer than tol (rad) join. A covered
    circle -> [(0, 2 pi)]."""
    xs = sorted((a0 % TWO_PI, a0 % TWO_PI + (a1 - a0)) for a0, a1 in ivs)
    merged = []
    for a0, a1 in xs:
        if merged and a0 <= merged[-1][1] + tol:
            merged[-1][1] = max(merged[-1][1], a1)
        else:
            merged.append([a0, a1])
    changed = True
    while changed and len(merged) > 1:            # the last interval may run past 2 pi into the first ones
        changed = False
        last = merged[-1]
        if last[1] - TWO_PI >= merged[0][0] - tol:
            merged.pop()
            merged[0] = [last[0] - TWO_PI, max(merged[0][1], last[1] - TWO_PI)]
            while len(merged) > 1 and merged[1][0] <= merged[0][1] + tol:
                merged[0][1] = max(merged[0][1], merged.pop(1)[1])
            changed = True
    if any(b - a >= TWO_PI - tol for a, b in merged):
        return [(0.0, TWO_PI)]
    return [tuple(m) for m in merged]


def _complement(merged):
    if not merged or merged == [(0.0, TWO_PI)]:
        return []
    out = []
    for i, (_a0, a1) in enumerate(merged):
        nxt = merged[(i + 1) % len(merged)][0] + (TWO_PI if i == len(merged) - 1 else 0.0)
        if nxt > a1:
            out.append((a1, nxt))
    return out


def _in_sweep(ang, th0, th1, tol=0.0):
    d = (ang - th0) % TWO_PI
    return d <= (th1 - th0) + tol or d >= TWO_PI - tol


def _pt(c, r, th):
    return c[0] + r * math.cos(th), c[1] + r * math.sin(th)


# ------------------------------------------------------------------------------------------- the gaps
def curved_gaps(ents, wall_layers, unit_m):
    """-> (gaps, rejected). gap: {"layer", "centre", "r1", "r2" (drawing units), "th0", "th1" (rad, th1 > th0),
    "jambs": [segment id at th0, at th1], "face_arcs": [ids]}; rejected: [{"layer", "r1_m", "r2_m", "sweep_rad",
    "reason"}]."""
    wall_l = set(wall_layers)
    tmin, tmax = BAND_T_M[0] / unit_m, BAND_T_M[1] / unit_m
    ctol, rtol = CENTRE_TOL_M / unit_m, RADIUS_TOL_M / unit_m
    jtol = JAMB_TOL_M / unit_m
    wall_segs = [s for s in ents["segments"] if s["layer"] in wall_l]
    gaps, rejected = [], []
    for lay in sorted(wall_l):
        arcs = [a for a in ents["arcs"] if a["layer"] == lay]
        clusters = []                                  # concentric groups: [centre, [arcs]]
        for a in sorted(arcs, key=lambda x: (round(x["c"][0], 6), round(x["c"][1], 6), x["r"], x["id"])):
            for cl in clusters:
                if math.dist(cl[0], a["c"]) <= ctol:
                    cl[1].append(a)
                    break
            else:
                clusters.append([tuple(a["c"]), [a]])
        for c, members in clusters:
            radii = []                                 # [r, [arcs]] one face radius each
            for a in sorted(members, key=lambda x: x["r"]):
                if radii and a["r"] - radii[-1][0] <= rtol:
                    radii[-1][1].append(a)
                else:
                    radii.append([a["r"], [a]])
            for i in range(len(radii)):
                for j in range(i + 1, len(radii)):
                    r1, r2 = radii[i][0], radii[j][0]
                    if not tmin <= r2 - r1 <= tmax:
                        continue
                    g1 = _complement(_union([V27._arc_iv(a) for a in radii[i][1]], END_TOL_M / unit_m / r1))
                    g2 = _complement(_union([V27._arc_iv(a) for a in radii[j][1]], END_TOL_M / unit_m / r2))
                    for th0, th1 in g1:
                        rec = {"layer": lay, "r1_m": round(r1 * unit_m, 6), "r2_m": round(r2 * unit_m, 6),
                               "sweep_rad": round(th1 - th0, 9)}
                        m = next(((h0, h1) for h0, h1 in g2 if _adiff(h0, th0) * r2 * unit_m <= SPLAY_M and
                                  _adiff(h1, th1) * r2 * unit_m <= SPLAY_M), None)
                        if m is None:
                            rejected.append(dict(rec, reason="FACES_STOP_AT_DIFFERENT_ANGLES"))
                            continue
                        if th1 - th0 > MAX_SWEEP_RAD:
                            rejected.append(dict(rec, reason="SWEEP_OVER_HALF_A_TURN"))
                            continue
                        if (th1 - th0) * (r1 + r2) / 2 * unit_m < MIN_GAP_M:
                            rejected.append(dict(rec, reason="NARROWER_THAN_MIN_GAP"))
                            continue
                        between = [a["id"] for k in range(i + 1, j) for a in radii[k][1]
                                   if V27._overlap(V27._arc_iv(a), (th0, th1))]
                        if between:
                            rejected.append(dict(rec, reason="WALL_ARC_INSIDE_THE_GAP"))
                            continue
                        h0 = th0 + ((m[0] - th0 + math.pi) % TWO_PI - math.pi)     # the outer face's own ends
                        h1 = th1 + ((m[1] - th1 + math.pi) % TWO_PI - math.pi)
                        jambs = []
                        for th, h in ((th0, h0), (th1, h1)):
                            p1, p2 = _pt(c, r1, th), _pt(c, r2, h)
                            hit = sorted(s["id"] for s in wall_segs
                                         if (math.dist(s["a"], p1) <= jtol and math.dist(s["b"], p2) <= jtol) or
                                         (math.dist(s["a"], p2) <= jtol and math.dist(s["b"], p1) <= jtol))
                            jambs.append(hit[0] if hit else None)
                        if None in jambs:
                            rejected.append(dict(rec, reason="NO_JAMB_LINE_AT_" + ("BOTH_ENDS" if jambs == [None, None]
                                                                                   else "ONE_END")))
                            continue
                        gaps.append({"layer": lay, "centre": c, "r1": r1, "r2": r2, "th0": th0, "th1": th1,
                                     "outer_th": (h0, h1), "jambs": jambs,
                                     "face_arcs": sorted(a["id"] for a in radii[i][1] + radii[j][1])})
    gaps.sort(key=lambda g: (g["layer"], round(g["centre"][0], 6), round(g["centre"][1], 6), round(g["r1"], 6),
                             round(g["th0"] % TWO_PI, 9)))
    return gaps, rejected


def glazing_in(gap, ents, layers, unit_m):
    """-> {"share", "length_m", "radii_m", "arc_ids", "segment_ids"}: the glazing of the given layers inside the gap's
    annular sector (strictly between the faces), its covered share of the sweep and length."""
    c, r1, r2, th0, th1 = gap["centre"], gap["r1"], gap["r2"], gap["th0"], gap["th1"]
    ctol, rtol = CENTRE_TOL_M / unit_m, RADIUS_TOL_M / unit_m
    ivs, length, radii, arc_ids, seg_ids = [], 0.0, set(), [], []
    for a in ents["arcs"]:
        if a["layer"] not in layers or math.dist(a["c"], c) > ctol or not r1 + rtol < a["r"] < r2 - rtol:
            continue
        ov = V27._overlap((th0, th1), V27._arc_iv(a))
        if ov is None:
            continue
        ivs.append(ov)
        length += a["r"] * (ov[1] - ov[0]) * unit_m
        radii.add(round(a["r"] * unit_m, 6))
        arc_ids.append(a["id"])
    for s in ents["segments"]:
        if s["layer"] not in layers:
            continue
        m = ((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2)
        rho = math.dist(m, c)
        if not r1 + rtol < rho < r2 - rtol or not _in_sweep(math.atan2(m[1] - c[1], m[0] - c[0]), th0, th1):
            continue
        aa = sorted(((math.atan2(p[1] - c[1], p[0] - c[0]) - th0) % TWO_PI) for p in (s["a"], s["b"]))
        if aa[1] - aa[0] > math.pi:                   # the segment straddles th0
            aa = [aa[1] - TWO_PI, aa[0]]
        ivs.append((th0 + max(aa[0], 0.0), th0 + min(aa[1], th1 - th0)))
        length += math.dist(s["a"], s["b"]) * unit_m
        seg_ids.append(s["id"])
    cov = sum(b - a for a, b in _union([iv for iv in ivs if iv[1] > iv[0]], 0.0)) if ivs else 0.0
    return {"share": round(min(cov / (th1 - th0), 1.0), 6), "length_m": round(length, 6), "radii_m": sorted(radii),
            "arc_ids": sorted(arc_ids), "segment_ids": sorted(seg_ids)}


def curved_glazing_roles(ents, L, unit_m, override=None):
    """D-P9-01: an OTHER layer (never a declared one) is a WINDOW layer when at least LAYER_SHARE of its linework lies
    in the wall gaps (the curved gaps here, the straight ones by the layer's own share_in_wall_gaps) and one of its
    concentric arcs covers at least GLAZING_SHARE of a curved gap. -> (L with the roles amended and L["v29"])."""
    roles = dict(L["roles"])
    wall_l = sorted(lay for lay, r in roles.items() if r == "WALL")
    gaps, rejected = curved_gaps(ents, wall_l, unit_m)
    promoted = {}
    for lay in sorted(roles):
        if roles[lay] != "OTHER" or lay in (override or {}):
            continue
        arcs = [a for a in ents["arcs"] if a["layer"] == lay]
        if not arcs:
            continue
        segs = [s for s in ents["segments"] if s["layer"] == lay]
        tot = sum(a["r"] * (lambda iv: iv[1] - iv[0])(V27._arc_iv(a)) for a in arcs) * unit_m + \
            sum(math.dist(s["a"], s["b"]) for s in segs) * unit_m
        inside, hits = 0.0, []
        for g in gaps:
            gl = glazing_in(g, ents, {lay}, unit_m)
            if gl["arc_ids"] and gl["share"] >= GLAZING_SHARE:
                hits.append({"centre": [round(g["centre"][0], 6), round(g["centre"][1], 6)],
                             "r1_m": round(g["r1"] * unit_m, 6), "r2_m": round(g["r2"] * unit_m, 6),
                             "share": gl["share"], "glazing_radii_m": gl["radii_m"]})
            inside += gl["length_m"]
        seg_tot = sum(math.dist(s["a"], s["b"]) for s in segs) * unit_m
        inside += (L["evidence"].get(lay, {}).get("share_in_wall_gaps") or 0.0) * seg_tot
        share = inside / tot if tot > 0 else 0.0
        if hits and share >= LAYER_SHARE:
            roles[lay] = "WINDOW"
            promoted[lay] = {"rule": "CURVED_GLAZING_IN_WALL_GAPS (UP-OPEN-CURVED-001): concentric glazing arcs inside "
                                     "jambed curved wall gaps", "share_in_wall_gaps": round(share, 4),
                             "curved_gaps": hits}
    out = dict(L, roles=roles)
    out["v29"] = {"promoted": promoted, "curved_gaps": len(gaps), "curved_gaps_rejected": rejected}
    if promoted:
        out["source"] = L["source"] + " + V2.9 curved glazing"
    return out


# ------------------------------------------------------------------------------------------- the openings
def _frame(g, unit_m):
    c, r1, r2, th0, th1 = g["centre"], g["r1"], g["r2"], g["th0"], g["th1"]
    phi, half = (th0 + th1) / 2, (th1 - th0) / 2
    n = (math.cos(phi), math.sin(phi))
    u = (-math.sin(phi), math.cos(phi))
    cu, cn = c[0] * u[0] + c[1] * u[1], c[0] * n[0] + c[1] * n[1]
    rm = (r1 + r2) / 2
    return {"u": u, "n": n, "s0": cu - r1 * math.sin(half), "s1": cu + r1 * math.sin(half), "o0": cn + r1,
            "o1": cn + r2, "centre": _pt(c, rm, phi)}


def curved_openings(gaps, ents, win_layers, swings, unit_m, served=None):
    """-> [opening record] in gap order, ids COP-001 ...; served (opening_id -> [swing occ]) is updated with the doors
    and swings it already holds are not offered again."""
    served = served if served is not None else {}
    taken = {occ for v in served.values() for occ in v}
    out = []
    for g in gaps:
        oid = f"COP-{len(out) + 1:03d}"
        c, r1, r2, th0, th1 = g["centre"], g["r1"], g["r2"], g["th0"], g["th1"]
        h0, h1 = g["outer_th"]
        b = CO.bases([{"cx": c[0] * unit_m * 1000, "cy": c[1] * unit_m * 1000, "r": r * unit_m * 1000,
                       "sweep_rad": sw} for r, sw in ((r1, th1 - th0), (r2, h1 - h0))], centre_tol=CENTRE_TOL_M * 1000)
        bases = {k: round(b[k] / 1000.0, 6) for k in CO.GEOMETRIC}
        chord_mid = 2 * (r1 + r2) / 2 * math.sin((th1 - th0) / 2)
        ends = [_pt(c, r, th) for th in (th0, th1) for r in (r1, r2)]
        door, best = None, None
        for occ in sorted(swings):
            if occ in taken:
                continue
            sw = swings[occ]
            d = min(math.dist(sw["hinge"], p) for p in ends)
            if d * unit_m > HINGE_AT_JAMB_M:
                continue
            if abs(sw["radius"] - chord_mid) > max(LEAF_FIT_M / unit_m, 0.25 * chord_mid):
                continue
            if best is None or d < best:
                door, best = occ, d
        gl = glazing_in(g, ents, set(win_layers), unit_m)
        kind = "DOOR" if door else ("WINDOW" if gl["share"] >= GLAZING_SHARE else "PASSAGE")
        if door:
            served[oid] = [door]
            taken.add(door)
        rec = {"opening_id": oid, "band_id": f"CURVEDBAND|{g['layer']}|{bases['MIN_RADIUS_ARC']:.3f}|"
                                             f"{r1 * unit_m:.3f}|{r2 * unit_m:.3f}", "layer": g["layer"],
               **_frame(g, unit_m), "width_m": bases["MIN_RADIUS_ARC"], "wall_t_m": (r2 - r1) * unit_m,
               "start_jamb": g["jambs"][0], "end_jamb": g["jambs"][1], "split_at_column": False,
               "kind": kind, "door_symbol": door, "glazing_m": round(gl["length_m"], 3),
               "curved": {"centre_du": [c[0], c[1]], "radii_du": [r1, r2],
                          "centre_m": [round(c[0] * unit_m, 6), round(c[1] * unit_m, 6)],
                          "r1_m": round(r1 * unit_m, 6), "r2_m": round(r2 * unit_m, 6),
                          "theta0_rad": round(th0, 9), "theta1_rad": round(th1, 9), "sweep_rad": round(th1 - th0, 9),
                          "outer_theta0_rad": round(h0, 9), "outer_theta1_rad": round(h1, 9),
                          "outer_sweep_rad": round(h1 - h0, 9), "angles_rad": [th0, th1, h0, h1],
                          "bases_m": bases, "glazing": gl, "face_arcs": g["face_arcs"],
                          "room_side": None, "width_basis": "MIN_RADIUS_ARC"}}
        if kind == "WINDOW":
            rec["glazing_ids"] = sorted(gl["arc_ids"] + gl["segment_ids"])
        out.append(rec)
    return out


def thresholds(op, role):
    """the curved opening closed on both wall faces: THR|<id>|0 on the inner face (r1), THR|<id>|1 on the outer."""
    cv = op["curved"]
    c = cv["centre_du"]
    th0, th1, h0, h1 = cv["angles_rad"]
    return [(op["opening_id"], TP.BoundaryItem(f"THR|{op['opening_id']}|{i}", "ARC", (c[0], c[1], r, a0, a1), role))
            for i, (r, a0, a1) in enumerate(((cv["radii_du"][0], th0, th1), (cv["radii_du"][1], h0, h1)))]


def strip_geometry(face, op, unit_m, tol_m=0.002):
    """a thin face beside a curved opening: inside the opening's annular sector (within tol_m), its radial depth
    (area / its mid arc, the sweep of the face it touches) and the room-face width; the rooms meeting the wall face it
    touches. -> geometry dict for arch_completeness.strip_register."""
    cv = op["curved"]
    c = cv["centre_du"]
    r1, r2 = cv["radii_du"]
    tol = tol_m / unit_m
    th0, th1, h0, h1 = cv["angles_rad"]
    a0, a1 = min(th0, h0), max(th1, h1)
    rhos, inside = [], True
    for x, y in face["polygon"]:
        rho = math.dist((x, y), c)
        rhos.append(rho)
        if not (r1 - tol <= rho <= r2 + tol and _in_sweep(math.atan2(y - c[1], x - c[0]), a0, a1, tol / max(r1, 1e-9))):
            inside = False
    lo, hi = min(rhos), max(rhos)
    on_inner, on_outer = abs(lo - r1) <= tol, abs(hi - r2) <= tol
    sweep = (th1 - th0) if on_inner and not on_outer else (h1 - h0) if on_outer and not on_inner else \
        ((th1 - th0) + (h1 - h0)) / 2
    mid_arc = sweep * (lo + hi) / 2 * unit_m
    depth = face["area_m2"] / mid_arc if mid_arc > 0 else None
    side = (cv.get("rooms_inner_face") or [] if on_inner else []) + (cv.get("rooms_outer_face") or [] if on_outer else [])
    return {"within_opening_box": inside, "depth_m": round(depth, 4) if depth is not None else None,
            "wall_t_m": round(op["wall_t_m"], 4), "opening_width_m": round(op["width_m"], 4),
            "radial_extent_m": [round(lo * unit_m, 4), round(hi * unit_m, 4)],
            "curved_soffit_m2": round(face["area_m2"], 6),
            "extent_along_m": round(mid_arc, 4), "extent_across_m": round((hi - lo) * unit_m, 4),
            "room_face_ids": sorted(side), "curved": True}


def room_side(ops, faces):
    """each curved opening's room side from the faces it bounds (their boundary source ids): MIN_RADIUS (the inner
    face), MAX_RADIUS, BOTH or NONE; width_m becomes that face's arc (MIN_RADIUS_ARC for BOTH / NONE, recorded)."""
    for o in ops:
        if not o.get("curved"):
            continue
        oid = o["opening_id"]
        side = {0: [], 1: []}
        for f in faces:
            if f["class"] not in ROOM_CLASSES or oid not in (f.get("opening_ids") or ()):
                continue
            ids = set(f.get("boundary_source_ids") or ())
            for i in (0, 1):
                if f"THR|{oid}|{i}" in ids:
                    side[i].append(f["face_id"])
        cv = o["curved"]
        if side[0] and side[1]:
            rs, basis = "BOTH", "MIN_RADIUS_ARC"
        elif side[1]:
            rs, basis = "MAX_RADIUS", "MAX_RADIUS_ARC"
        elif side[0]:
            rs, basis = "MIN_RADIUS", "MIN_RADIUS_ARC"
        else:
            rs, basis = "NONE", "MIN_RADIUS_ARC"
        cv.update(room_side=rs, width_basis=basis, rooms_inner_face=sorted(side[0]), rooms_outer_face=sorted(side[1]))
        if rs == "BOTH":
            cv["note"] = ("CURVED_OPENING_ROOMS_BOTH_SIDES: the width is the inner face's arc; the outer room's face is "
                          f"{cv['bases_m']['MAX_RADIUS_ARC']:.4f} m")
        o["width_m"] = cv["bases_m"][basis]


def policy_record():
    return {"policy_id": POLICY_ID, "band_t_m": list(BAND_T_M), "centre_tol_m": CENTRE_TOL_M,
            "radius_tol_m": RADIUS_TOL_M, "end_tol_m": END_TOL_M, "jamb_tol_m": JAMB_TOL_M, "min_gap_m": MIN_GAP_M,
            "max_sweep_rad": MAX_SWEEP_RAD, "glazing_share": GLAZING_SHARE, "layer_share": LAYER_SHARE,
            "hinge_at_jamb_m": HINGE_AT_JAMB_M, "leaf_fit_m": LEAF_FIT_M,
            "never": ["a glazing line taken as the room boundary of a curved opening (the room ends at its own wall "
                      "face)", "a curved gap without a jamb line at both ends read as an opening",
                      "a declared layer role changed", "a mean radius used for a face's width"]}
