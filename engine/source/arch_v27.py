"""ARCH_TAKEOFF_V2.7 (M9 Phase 2B-7) - the drawing-interpretation corrections proven by independent acceptance tests
(tests/m9_p2b7). Every function here is reached only by the V2.7 call path (its callers pass a v27 flag); V1 .. V2.6
never import this module.

    layer_roles(ents, unit_m, override, tol, geom)   the V2.6 layer roles plus (Phase 2B-6 experiment C, hardened):
        COLUMN   closed rectangles of ANY orientation drawn as one polyline or four LINEs, filled or crossed; three or
                 more need a column section (>= COLUMN_MIN_AREA_M2: a 0.15 m drain grating is not a column); one or two
                 need the same section, every one bound to a wall, and they explain the layer's linework
        DOOR     one exploded / inserted door: a swing with its leaf hinged at a wall-gap jamb, its symbols explaining
                 >= SINGLE_SHARE of the layer, and no line of the layer in a door-free wall gap
        WINDOW   one to three glazing lines in door-free wall gaps (no swing hinged in the gap, no door-role line); a
                 layer carrying door swings is never typed WINDOW
        refusals a layer whose geometry fits two roles, or a column candidate geometry cannot decide (too small, free
                 standing alone, not explaining its layer), stays OTHER with an explicit record
    loose_rects(segs, unit_m)                        the column candidate rectangles (any orientation)
    jamb_reconstruction(...)                         a door's structural opening from its own jamb lines when every
                                                     remainder of the wall gap is proven wall on both faces; a wider
                                                     opening is kept with the remainder's nature
    cycle_points(arr, cyc, sag)                      a face boundary with its arc edges flattened (sagitta <= sag)
    arc_bands(ents, wall_l, unit_m, loc, probe)      curved wall bands (concentric wall arcs a wall thickness apart)
Project-agnostic; stdlib only."""

from __future__ import annotations

import math
import re
from collections import defaultdict

from engine.source import arch_plan as AP
from engine.source import opening_census as OC
from engine.source import opening_gaps as OG

POLICY_ID = "ARCH_TAKEOFF_V2_7_CORRECTIONS"
COLUMN_MIN_AREA_M2 = 0.04             # a column section is at least 0.20 x 0.20 m; a smaller marked square is a drain,
#                                       a grating or a symbol (Phase 2B-6 D-P6-03)
SINGLE_SHARE = 0.8                    # one or two instances must explain this share of their layer's linework
SINGLE_WINDOW_SHARE = 0.9
SINGLE_WINDOW_MAX_SEGMENTS = 3
WALL_BAND_GUARD_M = 5.0               # a layer with this much paired wall face drawn on BOTH faces in runs of at least
#                                       arch_plan.LONG_BAND_M is a wall candidate, never searched for columns (a row of
#                                       aligned columns spans a long band but draws only its columns' own sides)
RECT_TOL_M = 0.002                    # corner meeting tolerance of a candidate rectangle
RECT_RIGHT_DEG = 1.0
MARK_TOL_M = 0.02
WALL_BOUND_TOL_M = 0.02
HINGE_AT_JAMB_M = 0.15
LEAF_OVER_GAP_M = 0.10
MIXED_MIN_M = 0.05                    # a door layer's line in a door-free wall gap longer than this makes it two roles
MAX_RECT_SEGMENTS = 20000             # rectangle search is skipped on larger layers (recorded)


def _len(s):
    return math.dist(s["a"], s["b"])


def loose_rects(segs, unit_m, tol_m=RECT_TOL_M):
    """closed rectangles of any orientation formed by four segments (one polyline or four LINEs) whose ends meet within
    tol and whose corners are right angles within RECT_RIGHT_DEG; both sides within arch_plan.COLUMN_SIDE_M ->
    [{"corners", "w_m", "h_m", "area_m2", "ids"}] (each rectangle once)."""
    tol = tol_m / unit_m
    key = lambda p: (round(p[0] / tol), round(p[1] / tol))          # noqa: E731
    at = defaultdict(list)
    for s in segs:
        for p, q in ((s["a"], s["b"]), (s["b"], s["a"])):
            at[key(p)].append((s, tuple(q)))
    sin_tol = math.sin(math.radians(RECT_RIGHT_DEG))
    out, seen = [], set()
    for s in segs:
        a, b = tuple(s["a"]), tuple(s["b"])
        for s2, c in at.get(key(b), ()):
            if s2 is s:
                continue
            for s3, d in at.get(key(c), ()):
                if s3 is s or s3 is s2:
                    continue
                for s4, e in at.get(key(d), ()):
                    if s4 in (s, s2, s3) or math.dist(e, a) > tol:
                        continue
                    ids = frozenset(x["id"] for x in (s, s2, s3, s4))
                    if ids in seen or len(ids) < 4:
                        continue
                    pts = [a, b, c, d]
                    ok = True
                    for i in range(4):
                        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % 4]
                        v1, v2 = (p0[0] - p1[0], p0[1] - p1[1]), (p2[0] - p1[0], p2[1] - p1[1])
                        n1, n2 = math.hypot(*v1), math.hypot(*v2)
                        if n1 <= 0 or n2 <= 0 or abs(v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2) > sin_tol:
                            ok = False
                            break
                    if not ok:
                        continue
                    w, h = math.dist(a, b) * unit_m, math.dist(b, c) * unit_m
                    if AP.COLUMN_SIDE_M[0] <= w <= AP.COLUMN_SIDE_M[1] and AP.COLUMN_SIDE_M[0] <= h <= AP.COLUMN_SIDE_M[1]:
                        seen.add(ids)
                        out.append({"corners": pts, "w_m": w, "h_m": h, "area_m2": w * h, "ids": ids})
    return out


def in_convex(p, poly, tol):
    """point in a convex polygon (either orientation), with tolerance (drawing units)."""
    sgn = 0
    for i in range(len(poly)):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
        L = math.hypot(x1 - x0, y1 - y0)
        c = ((x1 - x0) * (p[1] - y0) - (y1 - y0) * (p[0] - x0)) / L if L else 0.0
        if abs(c) <= tol:
            continue
        if sgn == 0:
            sgn = 1 if c > 0 else -1
        elif (c > 0) != (sgn > 0):
            return False
    return True


def _marked(r, segs, hatches, unit_m):
    """a candidate rectangle is a column symbol when a hatch fills it or a line crosses it (a diagonal)."""
    tol = MARK_TOL_M / unit_m
    if any(h.get("ring") and all(in_convex(p, r["corners"], tol) for p in h["ring"]) for h in hatches):
        return "FILLED"
    for x in segs:
        if x["id"] in r["ids"]:
            continue
        if in_convex(x["a"], r["corners"], tol) and in_convex(x["b"], r["corners"], tol) and \
                _len(x) * unit_m >= 0.5 * min(r["w_m"], r["h_m"]):
            return "CROSSED"
    return None


def _d_point_seg(p, a, b):
    return AP._d_point_seg(p, a, b)


def _wall_bound(r, wall_segs, unit_m):
    """a rectangle bound to the wall network: one of its sides lies on a wall line (collinear within tol, overlapping
    at least half the side), or a wall line ends on its boundary."""
    tol = WALL_BOUND_TOL_M / unit_m
    pts = r["corners"]
    sides = [(pts[i], pts[(i + 1) % 4]) for i in range(4)]
    for s in wall_segs:
        if any(_d_point_seg(p, a, b) <= tol for p in (s["a"], s["b"]) for a, b in sides):
            return True                                   # a wall line ends on the rectangle
        for a, b in sides:
            L = math.dist(a, b)
            if L <= 0:
                continue
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            if abs((s["a"][0] - a[0]) * uy - (s["a"][1] - a[1]) * ux) > tol or \
                    abs((s["b"][0] - a[0]) * uy - (s["b"][1] - a[1]) * ux) > tol:
                continue                                  # not on this side's line
            t0, t1 = sorted(((s["a"][0] - a[0]) * ux + (s["a"][1] - a[1]) * uy,
                             (s["b"][0] - a[0]) * ux + (s["b"][1] - a[1]) * uy))
            if min(t1, L) - max(t0, 0.0) >= 0.5 * L:
                return True                               # the side lies on a wall face
    return False


def _explained(segs, rects, unit_m):
    tol = MARK_TOL_M / unit_m
    tot = sum(_len(x) for x in segs)
    inside = sum(_len(x) for x in segs if any(in_convex(x["a"], r["corners"], tol) and
                                              in_convex(x["b"], r["corners"], tol) for r in rects))
    return round(inside / tot, 4) if tot else 0.0


def _wall_gaps(by, roles, unit_m, geom, mt):
    gaps_of = geom.band_gaps if geom is not None else OG.band_gaps
    out = []
    for lay in sorted(l for l, r in roles.items() if r == AP.WALL):
        if geom is not None:
            geom.context = f"layer_roles_v27|gaps|{lay}"
        for b in AP._bands(by[lay], unit_m, geom):
            for g in gaps_of(b, min_gap=0.4 / unit_m, jamb_tol=0.03 / unit_m, obstacles=(),
                             column_reach=0.06 / unit_m, closures=(), merge_tol=mt):
                out.append((b, g))
    return out


def _in_gap(p, b, g, pad):
    lo, hi = sorted((b["A"]["off"], b["B"]["off"]))
    su = p[0] * b["u"][0] + p[1] * b["u"][1]
    so = p[0] * b["n"][0] + p[1] * b["n"][1]
    return g["s0"] - pad <= su <= g["s1"] + pad and lo - pad <= so <= hi + pad


def paired_long_m(bands, unit_m):
    """the run of a layer's bands drawn on BOTH faces, counted in pieces of at least arch_plan.LONG_BAND_M (wall
    evidence). A band's span runs from its first to its last face piece; a row of aligned columns makes one long band
    whose faces are drawn only across each column."""
    from engine.source import arch_walls as AW
    tot = 0.0
    for b in bands:
        both = AW._iv_intersect(AW._cover(b["A"], b["lo"], b["hi"]), AW._cover(b["B"], b["lo"], b["hi"]))
        tot += sum((hi - lo) * unit_m for lo, hi in both if (hi - lo) * unit_m >= AP.LONG_BAND_M)
    return tot


def layer_roles(ents, unit_m, override=None, tol="LEGACY", geom=None):
    """ARCH_TAKEOFF_V2.7: arch_plan.layer_roles with the column, single-instance door / window rules and the
    refusals above. -> the V2.6 result + "refusals" [{layer, code, reason, candidates, evidence}]."""
    mt = AP.unit_tol(unit_m, tol)
    gaps_of = geom.band_gaps if geom is not None else OG.band_gaps
    by = defaultdict(list)
    for s in ents["segments"]:
        by[s["layer"]].append(s)
    arcs_by = defaultdict(list)
    for a in ents["arcs"]:
        arcs_by[a["layer"]].append(a)
    hatch_by = defaultdict(list)
    for h in ents.get("hatches", []):
        hatch_by[h["layer"]].append(h)
    ev, cand = {}, {}
    for lay in sorted(set(by) | set(arcs_by)):
        ss = by.get(lay, [])
        if geom is not None:
            geom.context = f"layer_roles_v27|{lay}"
        bands = AP._bands(ss, unit_m, geom) if ss else []
        long_len = sum((b["hi"] - b["lo"]) * unit_m for b in bands if (b["hi"] - b["lo"]) * unit_m >= AP.LONG_BAND_M)
        swings = sum(1 for a in arcs_by.get(lay, []) if AP.is_swing(a, unit_m))
        paired = paired_long_m(bands, unit_m)
        e = {"segments": len(ss), "long_band_m": round(long_len, 3), "paired_long_m": round(paired, 3),
             "bands": len(bands), "swings": swings}
        if paired < WALL_BAND_GUARD_M and 0 < len(ss) <= MAX_RECT_SEGMENTS:
            rects = loose_rects(ss, unit_m)
            marks = [(r, _marked(r, ss, hatch_by.get(lay, []), unit_m)) for r in rects]
            marked = [r for r, m in marks if m]
            cand[lay] = {"rects": rects, "marked": marked}
            e.update(column_rects=len(rects), column_marked=len(marked),
                     column_sections=sorted({(round(min(r["w_m"], r["h_m"]), 3), round(max(r["w_m"], r["h_m"]), 3))
                                             for r in marked}))
        elif len(ss) > MAX_RECT_SEGMENTS:
            e["column_rects"] = "NOT_SEARCHED (layer too large)"
        ev[lay] = e
    roles = {lay: AP.OTHER for lay in ev}
    refusals = []

    def refuse(lay, code, reason, candidates, **kw):
        refusals.append({"layer": lay, "code": code, "reason": reason, "candidates": sorted(candidates),
                         "evidence": {k: v for k, v in ev[lay].items() if k in ("segments", "swings", "column_rects",
                                                                                "column_marked", "column_sections",
                                                                                "anchored_swings", "hinges_at_jamb",
                                                                                "single_explained",
                                                                                "share_in_door_free_gaps")} | kw})
    # 1. columns by count: three or more marked rectangles, most of them of a column section
    single_col = {}
    for lay, c in cand.items():
        m = c["marked"]
        if not m:
            continue
        struct = [r for r in m if r["area_m2"] >= COLUMN_MIN_AREA_M2 - 1e-9]
        if len(m) >= 3 and len(m) >= 0.5 * max(len(c["rects"]), 1):
            if len(struct) >= 0.5 * len(m):
                roles[lay] = AP.COLUMN
                ev[lay]["column_rule"] = "COLUMN_COUNT (>= 3 marked rectangles of a column section, any orientation)"
            else:
                refuse(lay, "COLUMN_ROLE_REFUSED", f"TOO_SMALL: {len(m)} marked rectangles, {len(m) - len(struct)} under "
                       f"the {COLUMN_MIN_AREA_M2:.2f} m2 column section (a drain grating / symbol, not a column)",
                       ["COLUMN"])
        elif len(m) <= 2:
            single_col[lay] = (m, struct)
    # 2. walls: V2.6 (primary by jambed openings, secondary joining it)
    for lay, e in ev.items():
        if roles[lay] == AP.OTHER and e["long_band_m"] >= 5.0:
            n_open = 0
            if geom is not None:
                geom.context = f"layer_roles_v27|jambed|{lay}"
            for b in AP._bands(by[lay], unit_m, geom):
                closures = [(s["id"], tuple(s["a"]), tuple(s["b"])) for s in by[lay]]
                for g in gaps_of(b, min_gap=0.5 / unit_m, jamb_tol=0.03 / unit_m, closures=closures, merge_tol=mt):
                    n_open += g["state"] == OC.OPENING
            e["jambed_openings"] = n_open
    wc = sorted((e.get("jambed_openings", 0), e["long_band_m"], lay) for lay, e in ev.items()
                if roles[lay] == AP.OTHER and e["long_band_m"] >= 5.0)
    if wc:
        _n, best, primary = wc[-1]
        best = max(e["long_band_m"] for e in ev.values())
        roles[primary] = AP.WALL
        ev[primary]["wall_rule"] = "PRIMARY (most jambed openings in paired wall faces, then the longest)"
        prim = by[primary]
        for _n2, L, lay in wc[:-1]:
            if L < AP.WALL_SHARE * best:
                continue
            ends = [p for b in AP._bands(by[lay], unit_m, geom) if (b["hi"] - b["lo"]) * unit_m >= AP.LONG_BAND_M
                    for p in AP._band_ends(b)]
            att = sum(1 for q in ends if any(AP._d_point_seg(q, s["a"], s["b"]) * unit_m <= AP.ATTACH_M for s in prim))
            share = att / len(ends) if ends else 0.0
            ev[lay]["attached_end_share"] = round(share, 4)
            if share >= 0.5:
                roles[lay] = AP.WALL
                ev[lay]["wall_rule"] = "SECONDARY (joins the primary wall network)"
    wall_only = [s for s in ents["segments"] if roles.get(s["layer"]) == AP.WALL]
    # 3. single-instance columns: one or two marked rectangles of a column section, each bound to a wall, explaining
    #    the layer; anything less decided is refused (a free-standing square may be a column, a planter, a fixture)
    for lay, (m, struct) in sorted(single_col.items()):
        if roles[lay] != AP.OTHER:
            continue
        expl = _explained(by[lay], m, unit_m)
        ev[lay]["single_explained"] = expl
        bound = [r for r in m if _wall_bound(r, wall_only, unit_m)]
        if len(struct) < len(m):
            refuse(lay, "COLUMN_ROLE_REFUSED", f"TOO_SMALL: {len(m) - len(struct)} of {len(m)} marked rectangle(s) under "
                   f"the {COLUMN_MIN_AREA_M2:.2f} m2 column section (a drain grating / symbol, not a column)", ["COLUMN"])
        elif expl < SINGLE_SHARE:
            refuse(lay, "COLUMN_ROLE_REFUSED", f"NOT_EXPLAINING_LAYER: the marked rectangle(s) explain {expl:.0%} of the "
                   f"layer's linework (< {SINGLE_SHARE:.0%})", ["COLUMN"])
        elif len(bound) < len(m):
            refuse(lay, "COLUMN_ROLE_REFUSED", f"FREE_STANDING: {len(m) - len(bound)} of {len(m)} column-size marked "
                   "rectangle(s) bound to no wall - a single free-standing square may be a column, a planter or a fixture; "
                   "geometry does not decide (declare the layer's role)", ["COLUMN"])
        else:
            roles[lay] = AP.COLUMN
            ev[lay]["column_rule"] = "COLUMN_SINGLE_INSTANCE (wall-bound column section explaining the layer)"
    wall_segs = [s for s in ents["segments"] if roles.get(s["layer"]) in (AP.WALL, AP.COLUMN)]
    gaps = _wall_gaps(by, roles, unit_m, geom, mt)
    jambs = []
    for b, g in gaps:
        lo_o, hi_o = sorted((b["A"]["off"], b["B"]["off"]))
        for sj in (g["s0"], g["s1"]):
            for off in (lo_o, hi_o):
                jambs.append((b["u"][0] * sj + b["n"][0] * off, b["u"][1] * sj + b["n"][1] * off,
                              (g["s1"] - g["s0"]) * unit_m))
    all_hinges = [a["c"] for a in ents["arcs"] if AP.is_swing(a, unit_m)]
    pad = 0.02 / unit_m

    def door_free(b, g, door_layers):
        if any(_in_gap(h, b, g, pad) for h in all_hinges):
            return False
        return not any(_in_gap(x["a"], b, g, pad) and _in_gap(x["b"], b, g, pad)
                       for lay in door_layers for x in by.get(lay, []))

    def free_gap_share(lay, door_layers):
        tot = sum(_len(x) for x in by.get(lay, []))
        ins = 0.0
        for x in by.get(lay, []):
            mid = ((x["a"][0] + x["b"][0]) / 2, (x["a"][1] + x["b"][1]) / 2)
            if any(_in_gap(mid, b, g, 1e-6) and door_free(b, g, door_layers) for b, g in gaps):
                ins += _len(x)
        return ins, tot
    # 4. doors: V2.6 (two or more anchored swings with their leaves), then one swing hinged at a wall-gap jamb whose
    #    symbol explains the layer and which draws nothing in a door-free gap
    for lay, e in ev.items():
        if roles[lay] != AP.OTHER:
            continue
        sw = [a for a in arcs_by.get(lay, []) if AP.is_swing(a, unit_m) and AP.has_leaf(a, ents["segments"], unit_m)]
        anchored = sum(1 for a in sw if any(AP._d_point_seg(a["c"], s["a"], s["b"]) * unit_m <= AP.ATTACH_M
                                             for s in wall_segs))
        e["swings_with_leaf"] = len(sw)
        e["anchored_swings"] = anchored
        if anchored >= 2 and anchored >= 0.5 * len(sw):
            roles[lay] = AP.DOOR
            continue
        if not sw:
            continue
        hinges = [(a["c"], a["r"] + LEAF_OVER_GAP_M / unit_m) for a in sw
                  if any(math.dist(a["c"], (jx, jy)) * unit_m <= HINGE_AT_JAMB_M and a["r"] * unit_m <= gw + LEAF_OVER_GAP_M
                         for jx, jy, gw in jambs)]
        e["hinges_at_jamb"] = len(hinges)
        if not hinges:
            e["single_door_rule"] = "no swing hinged at a wall-gap jamb (a wardrobe / cabinet leaf, or a symbol)"
            continue
        near = lambda p: any(math.dist(p, c) <= R for c, R in hinges)   # noqa: E731
        tot = sum(_len(x) for x in by.get(lay, [])) + sum(a["r"] * AP.sweep(a) for a in arcs_by.get(lay, []))
        ins = sum(_len(x) for x in by.get(lay, []) if near(x["a"]) and near(x["b"])) + \
            sum(a["r"] * AP.sweep(a) for a in arcs_by.get(lay, []) if near(a["s"]) and near(a["e"]))
        e["single_explained"] = round(ins / tot, 4) if tot else 0.0
        other, _t = free_gap_share(lay, [])                 # gaps holding no swing hinge (this layer's own
        #                                                     lines never make a gap a door gap)
        if other * unit_m > MIXED_MIN_M:
            e["lines_in_door_free_gaps_m"] = round(other * unit_m, 4)
            refuse(lay, "LAYER_ROLE_REFUSED", f"TWO_ROLES: the layer draws a door symbol hinged at a wall-gap jamb AND "
                   f"{other * unit_m:.3f} m of lines in door-free wall gaps (glazing) - one layer, two roles; declare its "
                   "role or split the layer", ["DOOR", "WINDOW"])
            continue
        if anchored >= 1 and anchored >= 0.5 * len(sw) and e["single_explained"] >= SINGLE_SHARE:
            roles[lay] = AP.DOOR
            e["door_rule"] = "DOOR_SINGLE_INSTANCE (a swing with its leaf hinged at a wall-gap jamb)"
        else:
            refuse(lay, "LAYER_ROLE_REFUSED", f"DOOR_NOT_EXPLAINING_LAYER: the door symbol explains "
                   f"{e['single_explained']:.0%} of the layer (< {SINGLE_SHARE:.0%})", ["DOOR"])
    refused = {r["layer"] for r in refusals}
    # 5. windows: linework inside the wall gaps; a layer carrying door swings with their leaves is never a window
    door_l = [l for l, r in roles.items() if r == AP.DOOR]
    for lay, e in ev.items():
        if roles[lay] != AP.OTHER or not by.get(lay) or lay in refused:
            continue
        if e.get("swings_with_leaf"):
            e["window_rule"] = "not applied: the layer draws door swings with their leaves"
            continue
        tot = sum(_len(s) for s in by[lay])
        inside = 0.0
        for s in by[lay]:
            mid = ((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2)
            if any(_in_gap(mid, b, g, 1e-6) for b, g in gaps):
                inside += _len(s)
        e["share_in_wall_gaps"] = round(inside / tot, 4) if tot else 0.0
        if e["share_in_wall_gaps"] >= AP.WINDOW_IN_GAP_SHARE and e["segments"] >= 4:
            roles[lay] = AP.WINDOW
            continue
        if 1 <= e["segments"] <= SINGLE_WINDOW_MAX_SEGMENTS:
            ins, tot = free_gap_share(lay, door_l)
            e["share_in_door_free_gaps"] = round(ins / tot, 4) if tot else 0.0
            if e["share_in_door_free_gaps"] >= SINGLE_WINDOW_SHARE:
                roles[lay] = AP.WINDOW
                e["window_rule"] = "WINDOW_SINGLE_INSTANCE (glazing lines in door-free wall gaps)"
    source = "INFERRED"
    if override:
        for lay, r in override.items():
            if r not in AP.ROLES:
                raise AP.PlanError(f"unknown layer role {r}")
            roles[lay] = r
        source = "OVERRIDE (project layer map) over INFERRED"
        refusals = [x for x in refusals if x["layer"] not in override]
    out = {"roles": roles, "evidence": ev, "source": source, "refusals": refusals}
    if not any(r == AP.WALL for r in roles.values()):
        return dict(out, state="BLOCKED", why="NO_WALL_LAYER: no layer carries long paired wall faces")
    return dict(out, state="RESOLVED")


def column_shapes(ents, roles, unit_m):
    """the column rectangles of the COLUMN-role layers, any orientation: (boxes, polygons). An axis-aligned one is a
    box (x0, y0, x1, y1) for every consumer of arch_rooms column boxes; a turned one is a polygon only."""
    segs = [s for s in ents["segments"] if roles.get(s["layer"]) == AP.COLUMN]
    boxes, polys = [], []
    by = defaultdict(list)
    for s in segs:
        by[s["layer"]].append(s)
    eps = 1e-3 / unit_m
    for lay in sorted(by):
        for r in loose_rects(by[lay], unit_m):
            xs, ys = [p[0] for p in r["corners"]], [p[1] for p in r["corners"]]
            aligned = all(abs(r["corners"][i][0] - r["corners"][i - 1][0]) <= eps or
                          abs(r["corners"][i][1] - r["corners"][i - 1][1]) <= eps for i in range(4))
            if aligned:
                boxes.append((min(xs), min(ys), max(xs), max(ys)))
            else:
                polys.append([tuple(p) for p in r["corners"]])
    return sorted(set(boxes)), polys


POLICY = {"policy": POLICY_ID, "column_min_area_m2": COLUMN_MIN_AREA_M2, "single_share": SINGLE_SHARE,
          "single_window_share": SINGLE_WINDOW_SHARE, "single_window_max_segments": SINGLE_WINDOW_MAX_SEGMENTS,
          "wall_band_guard_m": WALL_BAND_GUARD_M, "rect_tol_m": RECT_TOL_M, "rect_right_deg": RECT_RIGHT_DEG,
          "mark_tol_m": MARK_TOL_M, "wall_bound_tol_m": WALL_BOUND_TOL_M, "hinge_at_jamb_m": HINGE_AT_JAMB_M,
          "leaf_over_gap_m": LEAF_OVER_GAP_M, "mixed_min_m": MIXED_MIN_M}


# ------------------------------------------------------------------ door opening from its own jamb evidence (V2.7)
JAMB_TOL_M = 0.01                     # a jamb line spans the band within this, perpendicular within JAMB_DEG
JAMB_DEG = 2.0
GAP_IS_DOOR_M = 0.05                  # a gap at most this wider than the jamb span is the door's own opening
REMAINDER_MIN_M = 0.02


def _jamb_lines(o, door_segs, unit_m):
    """the door symbol's jamb lines inside the band opening: door-layer segments across the band at full thickness
    (within JAMB_TOL_M), perpendicular to the wall within JAMB_DEG, their middle between the gap's ends."""
    (ux, uy), (nx, ny) = o["u"], o["n"]
    tol = JAMB_TOL_M / unit_m
    lo_o, hi_o = sorted((o["o0"], o["o1"]))
    out = []
    for s in door_segs:
        (ax, ay), (bx, by_) = s["a"], s["b"]
        L = math.hypot(bx - ax, by_ - ay)
        if L <= 0 or abs(L - (hi_o - lo_o)) > tol:
            continue
        if abs(((bx - ax) * ux + (by_ - ay) * uy) / L) > math.sin(math.radians(JAMB_DEG)):
            continue
        ta, tb = sorted((ax * nx + ay * ny, bx * nx + by_ * ny))
        if abs(ta - lo_o) > tol or abs(tb - hi_o) > tol:
            continue
        sm = ((ax + bx) * ux + (ay + by_) * uy) / 2
        if o["s0"] - tol <= sm <= o["s1"] + tol:
            out.append((sm, s["id"]))
    return sorted(out)


def _face_is_wall(o, off, x0, x1, wall_segs, unit_m, tol_m=JAMB_TOL_M):
    """is this stretch of one band face wall? Every part of it is drawn by a wall-layer segment lying on the face, or
    is the mouth of a wall junction: two wall-layer segments perpendicular to the band, each ending on the face at one
    end of the stretch and leaving it away from the band (Phase 2B-6 experiment A)."""
    (ux, uy), (nx, ny) = o["u"], o["n"]
    tol = tol_m / unit_m
    mid_o = (o["o0"] + o["o1"]) / 2
    cover, ends = [], []
    for s in wall_segs:
        (ax, ay), (bx, by_) = s["a"], s["b"]
        L = math.hypot(bx - ax, by_ - ay)
        if L <= 0:
            continue
        sa, sb = ax * ux + ay * uy, bx * ux + by_ * uy
        ta, tb = ax * nx + ay * ny, bx * nx + by_ * ny
        if abs(ta - off) <= tol and abs(tb - off) <= tol:                     # on this face
            lo, hi = sorted((sa, sb))
            if hi > x0 + tol and lo < x1 - tol:
                cover.append((max(lo, x0), min(hi, x1)))
        elif abs(((bx - ax) * ux + (by_ - ay) * uy) / L) < math.sin(math.radians(JAMB_DEG)):   # across the face
            for s_, t_, t_other in ((sa, ta, tb), (sb, tb, ta)):
                if abs(t_ - off) <= tol and (t_other - off) * (off - mid_o) > 0:      # ends here, leaves the band
                    ends.append(s_)
    cover.sort()
    gaps, cur = [], x0
    for lo, hi in cover:
        if lo > cur + tol:
            gaps.append((cur, lo))
        cur = max(cur, hi)
    if x1 > cur + tol:
        gaps.append((cur, x1))
    for g0, g1 in gaps:
        if not (any(abs(e - g0) <= tol for e in ends) and any(abs(e - g1) <= tol for e in ends)):
            return False
    return True


def _remainder_nature(o, a, b, wall_segs, win_segs, col_segs, col_boxes, unit_m):
    (ux, uy), (nx, ny) = o["u"], o["n"]
    pad = MARK_TOL_M / unit_m
    lo_o, hi_o = sorted((o["o0"], o["o1"]))

    def inside(p):                                    # strictly inside the remainder along the wall (its ends are
        su, so = p[0] * ux + p[1] * uy, p[0] * nx + p[1] * ny       # the door's jamb and the gap's far jamb)
        return a + pad < su < b - pad and lo_o - pad <= so <= hi_o + pad
    if any(inside(((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2)) for s in col_segs) or \
            any(inside(((x0 + x1) / 2, (y0 + y1) / 2)) for x0, y0, x1, y1 in col_boxes):
        return "COLUMN"
    if any(inside(((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2)) for s in win_segs):
        return "GLAZED_SIDE_PANEL"
    faces = [_face_is_wall(o, off, a, b, wall_segs, unit_m) for off in (o["o0"], o["o1"])]
    return "WALL_BOTH_FACES" if all(faces) else "WALL_ONE_FACE" if any(faces) else "OPEN"


def jamb_reconstruction(ops, ents, roles, swings, thresholds, col_boxes, unit_m, *, match_strict):
    """every DOOR band opening: the span between its symbol's own jamb lines, and what the rest of the wall gap is.
    Narrowed (structural opening = the jamb span) only when every remainder is wall on BOTH faces (drawn wall lines
    or junction mouths); the remainders are closed by zero-material WALL boundary items on both faces, the thresholds
    and the opening's position follow, and a door held by the V2.6 review fit is released when its swing now fits the
    narrowed opening strictly (match_strict, arch_rooms.match_swings). A wider opening (open, column, glazed side
    panel, wall on one face) is kept with the remainder's nature. -> (boundary items [(id, (x0, y0, x1, y1))],
    records)."""
    door_l = {l for l, r in roles.items() if r == AP.DOOR}
    door_segs = [s for s in ents["segments"] if s["layer"] in door_l]
    wall_segs = [s for s in ents["segments"] if roles.get(s["layer"]) == AP.WALL]
    win_segs = [s for s in ents["segments"] if roles.get(s["layer"]) == AP.WINDOW]
    col_segs = [s for s in ents["segments"] if roles.get(s["layer"]) == AP.COLUMN]
    items, recs = [], []
    for o in ops:
        if o.get("kind") != "DOOR":
            continue
        gap = o["s1"] - o["s0"]
        jl = _jamb_lines(o, door_segs, unit_m)
        rec = {"opening_id": o["opening_id"], "wall_gap_m": round(gap * unit_m, 6), "jamb_lines": [i for _, i in jl]}
        if len(jl) < 2:
            o["opening_v27"] = dict(rec, decision="NO_JAMB_EVIDENCE", jamb_span_m=None,
                                    why="fewer than two jamb lines of the door symbol span the wall: the wall gap is "
                                        "the structural opening")
            recs.append(o["opening_v27"])
            continue
        lo, hi = jl[0][0], jl[-1][0]
        rec["jamb_span_m"] = round((hi - lo) * unit_m, 6)
        if gap - (hi - lo) <= GAP_IS_DOOR_M / unit_m:
            o["opening_v27"] = dict(rec, decision="GAP_IS_THE_DOOR")
            recs.append(o["opening_v27"])
            continue
        rem = [(a, b) for a, b in ((o["s0"], lo), (hi, o["s1"])) if b - a > REMAINDER_MIN_M / unit_m]
        rec["remainder"] = [{"m": round((b - a) * unit_m, 6), "nature": _remainder_nature(
            o, a, b, wall_segs, win_segs, col_segs, col_boxes, unit_m)} for a, b in rem]
        if not all(x["nature"] == "WALL_BOTH_FACES" for x in rec["remainder"]):
            o["opening_v27"] = dict(rec, decision="WIDER_OPENING_KEPT", why=(
                "the rest of the wall gap is not proven wall on both faces (" + ", ".join(
                    f"{x['m']:.3f} m {x['nature']}" for x in rec["remainder"]) + "): the structural opening is the "
                "whole gap; the door's own opening is its jamb span"))
            if o.get("door_fit_review"):
                o["door_fit_review"] += "; " + o["opening_v27"]["why"]
            recs.append(o["opening_v27"])
            continue
        (ux, uy), (nx, ny) = o["u"], o["n"]
        before = {"s0": o["s0"], "s1": o["s1"], "width_m": o["width_m"], "centre": list(o["centre"]),
                  "start_jamb": o.get("start_jamb"), "end_jamb": o.get("end_jamb")}
        mid_o = (o["o0"] + o["o1"]) / 2
        o.update(s0=lo, s1=hi, width_m=(hi - lo) * unit_m,
                 centre=(ux * (lo + hi) / 2 + nx * mid_o, uy * (lo + hi) / 2 + ny * mid_o),
                 start_jamb="JAMB_LINE:" + jl[0][1], end_jamb="JAMB_LINE:" + jl[-1][1])
        for t_ in thresholds:
            if t_["opening_id"] == o["opening_id"]:
                k = 0 if t_["id"].endswith("|0") else 1
                off = (o["o0"], o["o1"])[k]
                t_["a"] = (ux * lo + nx * off, uy * lo + ny * off)
                t_["b"] = (ux * hi + nx * off, uy * hi + ny * off)
        for i, (a, b) in enumerate(rem):
            for j, off in enumerate((o["o0"], o["o1"])):
                p = (ux * a + nx * off, uy * a + ny * off)
                q = (ux * b + nx * off, uy * b + ny * off)
                items.append((f"JAMBREM|{o['opening_id']}|{i}|{j}", (p[0], p[1], q[0], q[1])))
            # the door's own jamb closes the doorway piece: the remainder is wall mass, never a doorway strip
            sj = hi if a >= hi - 1e-9 else lo
            p = (ux * sj + nx * o["o0"], uy * sj + ny * o["o0"])
            q = (ux * sj + nx * o["o1"], uy * sj + ny * o["o1"])
            items.append((f"JAMBCAP|{o['opening_id']}|{i}", (p[0], p[1], q[0], q[1])))
        leaves = o.get("door_leaves") or ([o["door_symbol"]] if o.get("door_symbol") else [])
        strict = len(leaves) == 1 and leaves[0] in swings and \
            match_strict([o], {leaves[0]: swings[leaves[0]]}, unit_m).get(o["opening_id"]) == leaves
        released = None
        if o.get("door_fit_review") and strict:
            released = o.pop("door_fit_review")
        o["opening_v27"] = dict(rec, decision="NARROWED_TO_JAMB_SPAN", before={
            "wall_gap_m": round(before["width_m"], 6), "centre": before["centre"],
            "jambs": [before["start_jamb"], before["end_jamb"]]},
            strict_fit_after=strict, review_released=released,
            why="every remainder of the wall gap is wall on both faces: the structural opening is the jamb span")
        recs.append(o["opening_v27"])
    return items, recs


# ------------------------------------------------------------------------ arcs: room boundaries and curved walls
ARC_SAGITTA_M = 0.001
ARC_CENTRE_TOL_M = 0.002
ARC_MIN_RUN_M = 0.3
ARC_BASIS = "MID_BAND_ARC"            # the curved run on the band's centreline (the straight walls' basis); D-07


def cycle_points(arr, cyc, sag):
    """the cycle's vertices with every arc edge flattened (chord sagitta <= sag, drawing units); the arc's own
    end points stay vertices, the inserted points lie on the arc."""
    pts = []
    for ei, fw in cyc:
        e = arr.edges[ei]
        start = arr.nodes[e["n0"]] if fw else arr.nodes[e["n1"]]
        pts.append(start)
        if e["kind"] == "A":
            pr = e["prim"]
            sw = e["t1"] - e["t0"]
            step = 2 * math.acos(max(-1.0, min(1.0, 1 - sag / pr.r))) if pr.r > sag else abs(sw)
            k = max(1, math.ceil(abs(sw) / max(step, 1e-12)))
            mids = [pr.point(e["t0"] + sw * i / k) for i in range(1, k)]
            if mids and math.dist(mids[0], start) > math.dist(mids[-1], start):
                mids.reverse()
            pts += mids
    return pts


def _arc_iv(a):
    cx, cy = a["c"]
    a0 = math.atan2(a["s"][1] - cy, a["s"][0] - cx)
    a1 = math.atan2(a["e"][1] - cy, a["e"][0] - cx)
    if a.get("dir") == "CW":
        a0, a1 = a1, a0
    if a1 <= a0:
        a1 += 2 * math.pi
    return a0, a1


def _overlap(i, j):
    """the angular overlap of two CCW intervals, the second shifted by whole turns to meet the first."""
    best = None
    for k in (-1, 0, 1):
        lo, hi = max(i[0], j[0] + 2 * math.pi * k), min(i[1], j[1] + 2 * math.pi * k)
        if hi > lo and (best is None or hi - lo > best[1] - best[0]):
            best = (lo, hi)
    return best


def arc_bands(ents, wall_l, unit_m, loc, probe, family):
    """curved wall bands: two concentric wall-layer arcs (centres within ARC_CENTRE_TOL_M) whose radii differ by a wall
    thickness (arch_plan.BAND_T_M), over a common sweep of at least ARC_MIN_RUN_M on the inner arc, with no
    concentric wall arc between them. Published bases (as engine.source.curved_opening): MIN_RADIUS_ARC,
    MID_BAND_ARC, MAX_RADIUS_ARC; the run takes ARC_BASIS; strip = sweep x (r2^2 - r1^2) / 2 = MID x t (exact).
    loc / probe / family: arch_walls' side locator, probe distance and thickness family. -> wall records."""
    tmin, tmax = AP.BAND_T_M[0] / unit_m, AP.BAND_T_M[1] / unit_m
    ctol = ARC_CENTRE_TOL_M / unit_m
    out = []
    for lay in wall_l:
        arcs = [a for a in ents["arcs"] if a["layer"] == lay]
        ivs = [_arc_iv(a) for a in arcs]
        used, cands = set(), []
        for i, a in enumerate(arcs):
            for j, b in enumerate(arcs):
                if j <= i or math.dist(a["c"], b["c"]) > ctol:
                    continue
                t = abs(a["r"] - b["r"])
                if not tmin <= t <= tmax:
                    continue
                ov = _overlap(ivs[i], ivs[j])
                r1 = min(a["r"], b["r"])
                if ov is None or (ov[1] - ov[0]) * r1 * unit_m < ARC_MIN_RUN_M:
                    continue
                between = any(k not in (i, j) and math.dist(c["c"], a["c"]) <= ctol and
                              r1 < c["r"] < max(a["r"], b["r"]) and _overlap(ivs[k], ov) for k, c in enumerate(arcs))
                if not between:
                    cands.append((t, i, j, ov))
        for t, i, j, ov in sorted(cands):
            if i in used or j in used:
                continue
            used |= {i, j}
            a, b = arcs[i], arcs[j]
            r1, r2 = sorted((a["r"], b["r"]))
            th = ov[1] - ov[0]
            bases = {"MIN_RADIUS_ARC": r1 * th * unit_m, "MID_BAND_ARC": (r1 + r2) / 2 * th * unit_m,
                     "MAX_RADIUS_ARC": r2 * th * unit_m}
            L = bases[ARC_BASIS]
            t_m = (r2 - r1) * unit_m
            cx, cy = a["c"]
            am = (ov[0] + ov[1]) / 2
            pa = (cx + (r1 - probe) * math.cos(am), cy + (r1 - probe) * math.sin(am))
            pb = (cx + (r2 + probe) * math.cos(am), cy + (r2 + probe) * math.sin(am))
            sides = [loc.at(pa), loc.at(pb)]
            rm = (r1 + r2) / 2
            out.append({"wall_id": f"ARCBAND|{a['id']}|{b['id']}", "source_ids": sorted((a["id"], b["id"])),
                        "layer": lay, "t_m": round(t_m, 4),
                        "family": family(t_m), "gross_lm": round(L, 6), "net_lm": round(L, 6),
                        "columns_in_wall_lm": 0.0, "strip_m2": round(th * (r2 ** 2 - r1 ** 2) / 2 * unit_m ** 2, 6),
                        "sides": sides,
                        "kind": "EXTERNAL" if "EXTERIOR" in sides else ("INTERNAL" if sides[0] != sides[1]
                                                                         else "INSIDE_ONE_SPACE"),
                        "centreline": [(cx + rm * math.cos(ov[0]), cy + rm * math.sin(ov[0])),
                                       (cx + rm * math.cos(ov[1]), cy + rm * math.sin(ov[1]))],
                        "curved": {"centre": [cx, cy], "r1_m": round(r1 * unit_m, 6), "r2_m": round(r2 * unit_m, 6),
                                   "sweep_rad": round(th, 9), "bases_lm": {k: round(v, 6) for k, v in bases.items()},
                                   "basis": ARC_BASIS, "basis_decision": "D-07 (owner decision pending: the centreline "
                                   "basis of the straight walls is kept)"}})
    return out


# ---------------------------------------------------------------- wet-room evidence (UP-WET-002, registry 1.2.0)
LOOP_TOL_M = 0.002
BOWL_SHORT_M = (0.30, 0.50)           # a water-closet bowl drawn as a closed curve: its width ...
BOWL_LONG_M = (0.45, 0.80)            # ... and length, elongated (1.15 - 2.0 x)
BOWL_ASPECT = (1.15, 2.0)
BOWL_MIN_VERTICES = 8                 # a curve (an ellipse's chords, a bulged polyline), not a box
CISTERN_SHORT_M = (0.12, 0.30)        # the cistern: a rectangle ...
CISTERN_LONG_M = (0.30, 0.65)
FITTING_REACH_M = 0.30                # a basin's taps, waste and counter edge drawn loose within this of its block
WC_TOUCH_M = 0.05                     # the bowl's rear end within this of the cistern
WC_PERP_COS = 0.26                    # the bowl's axis across the cistern's long side (within ~15 degrees)


def _loops(segs, arcs, unit_m):
    """closed loops of loose linework: segments (and arc chords) whose end points meet pairwise (every node of
    degree two). -> [{"points", "ids", "vertices", "has_arc"}]."""
    tol = LOOP_TOL_M / unit_m
    key = lambda p: (round(p[0] / tol), round(p[1] / tol))          # noqa: E731
    edges = [(tuple(s["a"]), tuple(s["b"]), s["id"], False) for s in segs]
    for a in arcs:
        edges.append((tuple(a["s"]), tuple(a["e"]), a["id"], True))
    adj = defaultdict(list)
    for i, (p, q, _id, _arc) in enumerate(edges):
        adj[key(p)].append(i)
        adj[key(q)].append(i)
    seen, out = set(), []
    for i in range(len(edges)):
        if i in seen:
            continue
        comp, stack = set(), [i]
        while stack:
            j = stack.pop()
            if j in comp:
                continue
            comp.add(j)
            for k in (key(edges[j][0]), key(edges[j][1])):
                stack += [x for x in adj[k] if x not in comp]
        seen |= comp
        nodes = defaultdict(int)
        for j in comp:
            nodes[key(edges[j][0])] += 1
            nodes[key(edges[j][1])] += 1
        if len(comp) < 3 or any(v != 2 for v in nodes.values()):
            continue
        pts = [edges[j][0] for j in comp] + [edges[j][1] for j in comp]
        for j in comp:
            if edges[j][3]:
                a = next(x for x in arcs if x["id"] == edges[j][2])
                lo, hi = _arc_iv(a)
                pts += [(a["c"][0] + a["r"] * math.cos(lo + (hi - lo) * t / 8),
                         a["c"][1] + a["r"] * math.sin(lo + (hi - lo) * t / 8)) for t in range(1, 8)]
        out.append({"points": pts, "ids": sorted(edges[j][2] for j in comp), "vertices": len(comp),
                    "has_arc": any(edges[j][3] for j in comp)})
    return out


def _frame(pts):
    """the principal axes of a point set: centre, unit long axis, extents (long, short) in drawing units."""
    n = len(pts)
    cx, cy = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
    sxx = sum((p[0] - cx) ** 2 for p in pts) / n
    syy = sum((p[1] - cy) ** 2 for p in pts) / n
    sxy = sum((p[0] - cx) * (p[1] - cy) for p in pts) / n
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
    u = (math.cos(ang), math.sin(ang))
    v = (-u[1], u[0])
    us = [(p[0] - cx) * u[0] + (p[1] - cy) * u[1] for p in pts]
    vs = [(p[0] - cx) * v[0] + (p[1] - cy) * v[1] for p in pts]
    a, b = max(us) - min(us), max(vs) - min(vs)
    if b > a:
        u, v, a, b, us, vs = v, (-v[0], -v[1]), b, a, vs, us
    return {"c": (cx, cy), "u": u, "long": a, "short": b, "pts": pts}


def wc_shapes(segs, arcs, unit_m, wall_segs=()):
    """water closets drawn as linework (exploded, or inside an anonymously named block): a bowl (a closed, curved,
    elongated loop BOWL_*) whose rear end touches a cistern (a rectangle CISTERN_*) set across its axis.
    -> [{"bowl_ids", "cistern_ids", "bowl_m": [w, l], "cistern_m": [w, l], "against_wall"}]."""
    loops = _loops(segs, arcs, unit_m)
    bowls, cisterns = [], []
    for lp in loops:
        f = _frame(lp["points"])
        L, S = f["long"] * unit_m, f["short"] * unit_m
        if lp["vertices"] == 4 and not lp["has_arc"] and CISTERN_SHORT_M[0] <= S <= CISTERN_SHORT_M[1] and \
                CISTERN_LONG_M[0] <= L <= CISTERN_LONG_M[1]:
            cisterns.append((lp, f))
        elif (lp["vertices"] >= BOWL_MIN_VERTICES or lp["has_arc"]) and BOWL_SHORT_M[0] <= S <= BOWL_SHORT_M[1] and \
                BOWL_LONG_M[0] <= L <= BOWL_LONG_M[1] and BOWL_ASPECT[0] <= L / max(S, 1e-9) <= BOWL_ASPECT[1]:
            bowls.append((lp, f))
    out = []
    touch = WC_TOUCH_M / unit_m
    for bl, bf in bowls:
        for cl, cf in cisterns:
            if abs(bf["u"][0] * cf["u"][0] + bf["u"][1] * cf["u"][1]) > WC_PERP_COS:
                continue
            # the bowl's extreme point along its axis nearest the cistern must touch the cistern rectangle
            ends = []
            for sgn in (1, -1):
                k = max(range(len(bf["pts"])), key=lambda i: sgn * ((bf["pts"][i][0] - bf["c"][0]) * bf["u"][0] +
                                                                    (bf["pts"][i][1] - bf["c"][1]) * bf["u"][1]))
                ends.append(bf["pts"][k])
            near = min(ends, key=lambda p: math.dist(p, cf["c"]))
            du = (near[0] - cf["c"][0]) * cf["u"][0] + (near[1] - cf["c"][1]) * cf["u"][1]
            dv = (near[0] - cf["c"][0]) * -cf["u"][1] + (near[1] - cf["c"][1]) * cf["u"][0]
            if abs(du) > cf["long"] / 2 + touch or abs(dv) > cf["short"] / 2 + touch:
                continue
            # the cistern lies beyond the bowl's end (not around the bowl: a vanity counter holds its basin)
            if math.dist(bf["c"], cf["c"]) < (bf["long"] / 2 + cf["short"] / 2) * 0.8:
                continue
            wall = any(min(AP._d_point_seg(p, s["a"], s["b"]) for p in cl["points"]) * unit_m <= 0.10
                       for s in wall_segs)
            out.append({"bowl_ids": bl["ids"], "cistern_ids": cl["ids"],
                        "bowl_m": [round(bf["short"] * unit_m, 3), round(bf["long"] * unit_m, 3)],
                        "cistern_m": [round(cf["short"] * unit_m, 3), round(cf["long"] * unit_m, 3)],
                        "against_wall": wall})
    return out


# ARCH_TAKEOFF_V2.7.1 (Phase 2B-8, UP-WET-002 1.3.0): the WC linework profile. A pan's cistern stands on a wall face
# (the flush and the soil connection); its bowl is no wider than a pan; a round bowl is centred on its cistern. Loops
# beyond the profile are tried and named, so a weak resemblance is reported, never typed.
PAN_WIDTH_M = (0.32, 0.42)            # the bowl's width, elliptical or round (a seat is wider)
CISTERN_ON_WALL_M = 0.10              # the cistern within this of a wall-layer segment
ROUND_CENTRE_M = 0.05                 # a round bowl's centre within this of the cistern's centre line
CAND_SHORT_M = (0.25, 0.70)           # the curved loops tried as bowls ...
CAND_LONG_M = (0.25, 0.90)            # ... (outside the profile: a named rejection)


def _circle_pts(c, n=24):
    return [(c["c"][0] + c["r"] * math.cos(2 * math.pi * k / n), c["c"][1] + c["r"] * math.sin(2 * math.pi * k / n))
            for k in range(n)]


def wc_shapes_v271(segs, arcs, circles, unit_m, wall_segs=()):
    """ARCH_TAKEOFF_V2.7.1: water closets drawn as linework under the 1.3.0 profile. Every curved loop or circle
    touching a cistern-sized rectangle is a candidate; it is a WC when its cistern stands on a wall face, an elongated
    bowl is a pan's width and length, and a round bowl is a pan's width and centred on its cistern.
    -> (accepted [{"bowl_ids", "cistern_ids", "bowl_m", "cistern_m", "against_wall", "bowl_shape"}],
        rejected [{"bowl_ids", "cistern_ids", "bowl_m", "reason"}])."""
    loops = _loops(segs, arcs, unit_m)
    bowls, cisterns = [], []
    for lp in loops:
        f = _frame(lp["points"])
        L, S = f["long"] * unit_m, f["short"] * unit_m
        if lp["vertices"] == 4 and not lp["has_arc"] and CISTERN_SHORT_M[0] <= S <= CISTERN_SHORT_M[1] and \
                CISTERN_LONG_M[0] <= L <= CISTERN_LONG_M[1]:
            cisterns.append((lp, f))
        elif (lp["vertices"] >= BOWL_MIN_VERTICES or lp["has_arc"]) and CAND_SHORT_M[0] <= S <= CAND_SHORT_M[1] and \
                CAND_LONG_M[0] <= L <= CAND_LONG_M[1]:
            shape = "ELLIPTICAL" if L / max(S, 1e-9) >= BOWL_ASPECT[0] else "ROUND"
            bowls.append((lp["ids"], shape, f, None))
    for c in circles:
        d = 2 * c["r"] * unit_m
        if CAND_SHORT_M[0] <= d <= CAND_SHORT_M[1]:
            pts = _circle_pts(c)
            f = dict(_frame(pts), c=tuple(c["c"]), long=2 * c["r"], short=2 * c["r"])
            bowls.append(([c["id"]], "ROUND", f, c))
    touch = WC_TOUCH_M / unit_m
    accepted, rejected = [], []
    for ids, shape, bf, circ in bowls:
        for cl, cf in cisterns:
            cu, cv = cf["u"], (-cf["u"][1], cf["u"][0])
            if shape == "ELLIPTICAL":
                if abs(bf["u"][0] * cu[0] + bf["u"][1] * cu[1]) > WC_PERP_COS:
                    continue
                ends = []
                for sgn in (1, -1):
                    k = max(range(len(bf["pts"])), key=lambda i: sgn * ((bf["pts"][i][0] - bf["c"][0]) * bf["u"][0] +
                                                                        (bf["pts"][i][1] - bf["c"][1]) * bf["u"][1]))
                    ends.append(bf["pts"][k])
                near = min(ends, key=lambda p: math.dist(p, cf["c"]))
                du = (near[0] - cf["c"][0]) * cu[0] + (near[1] - cf["c"][1]) * cu[1]
                dv = (near[0] - cf["c"][0]) * cv[0] + (near[1] - cf["c"][1]) * cv[1]
                if abs(du) > cf["long"] / 2 + touch or abs(dv) > cf["short"] / 2 + touch:
                    continue
                if math.dist(bf["c"], cf["c"]) < (bf["long"] / 2 + cf["short"] / 2) * 0.8:
                    continue
                off = 0.0
            else:
                r = bf["short"] / 2
                du = (bf["c"][0] - cf["c"][0]) * cu[0] + (bf["c"][1] - cf["c"][1]) * cu[1]
                dv = (bf["c"][0] - cf["c"][0]) * cv[0] + (bf["c"][1] - cf["c"][1]) * cv[1]
                # tangent to the cistern's long side (outside it), the centre's projection on the cistern
                if abs(abs(dv) - (cf["short"] / 2 + r)) > touch or abs(du) > cf["long"] / 2:
                    continue
                off = abs(du) * unit_m
            wall = any(min(AP._d_point_seg(p, s["a"], s["b"]) for p in cl["points"]) * unit_m <= CISTERN_ON_WALL_M
                       for s in wall_segs)
            bw, bl = bf["short"] * unit_m, bf["long"] * unit_m
            why = []
            if not wall:
                why.append("CISTERN_NOT_ON_A_WALL")
            if shape == "ELLIPTICAL":
                if bw > PAN_WIDTH_M[1]:
                    why.append("BOWL_WIDER_THAN_A_WC_PAN")
                elif bw < PAN_WIDTH_M[0]:
                    why.append("BOWL_NARROWER_THAN_A_WC_PAN")
                if not BOWL_LONG_M[0] <= bl <= BOWL_LONG_M[1] or bl / max(bw, 1e-9) > BOWL_ASPECT[1]:
                    why.append("BOWL_LENGTH_NOT_A_WC_PAN")
            else:
                if bw > PAN_WIDTH_M[1]:
                    why.append("ROUND_BOWL_TOO_LARGE")
                elif bw < PAN_WIDTH_M[0]:
                    why.append("ROUND_BOWL_TOO_SMALL")
                if off > ROUND_CENTRE_M:
                    why.append("ROUND_BOWL_OFF_CISTERN_CENTRE")
            rec = {"bowl_ids": sorted(ids), "cistern_ids": cl["ids"], "bowl_m": [round(bw, 3), round(bl, 3)],
                   "cistern_m": [round(cf["short"] * unit_m, 3), round(cf["long"] * unit_m, 3)], "bowl_shape": shape,
                   "centre": list(bf["c"])}
            if why:
                rejected += [dict(rec, reason=w) for w in why]
            else:
                accepted.append(dict(rec, against_wall=True))
    return accepted, rejected


def _decimal_handle(sid):
    """an insert id of either reader (I:<hex>:<n> of arch_intake, D<k>:<dec> of an insert path) -> its decimal
    handle (str), so a fixture and the entities drawn inside it can be matched."""
    s = str(sid)
    if s.startswith("I:"):
        try:
            return str(int(s.split(":")[1], 16))
        except (IndexError, ValueError):
            return None
    return s.split(":")[-1] if re.match(r"^D\d+:\d+$", s) else None


def wet_evidence(face, fixtures, layer_ev, ents, roles, unit_m, inside, v271=False):
    """UP-WET-002 for a space with no room word and no room-tag block: what types it. -> (codes or None, label_source,
    issue, record). A wash basin alone never makes it wet; a basin with a second, independent piece of sanitary
    evidence (a water closet drawn as linework, or sanitary-layer linework that is not the basin's own) does; a
    water-closet shape alone is one geometric shape - review; ambiguous spaces stay REVIEW (no room type), never
    DRY. Spaces typed by a WC / shower / bath fixture block or by sanitary-layer linework keep the V2.6 reading.
    v271 (ARCH_TAKEOFF_V2.7.1 only): the WC linework profile of registry 1.3.0 (wc_shapes_v271, its rejections
    recorded) and the basin's own linework matched through the insert path of every entity drawn inside it; False is
    the V2.7 path, unchanged."""
    from engine.source import arch_rooms as AR
    basins = [x for x in fixtures if x["fixture"] == "BASIN"]
    wet_fx = [x for x in fixtures if x["evidences"] == "BATHROOM"]
    fx_codes = sorted({x["evidences"] for x in fixtures})
    basin_ins = {x["id"] for x in basins}
    xs, ys = [p[0] for p in face["polygon"]], [p[1] for p in face["polygon"]]
    pad = 0.05 / unit_m
    box = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)

    def in_box(p):
        return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]
    # loose linework of the space's box (a fixture set against a wall has edges ON the boundary); a shape counts when
    # its centre is inside the space
    if v271:
        basin_h = {_decimal_handle(x) for x in basin_ins} - {None}

        def own(e):
            return any(_decimal_handle(p) in basin_h for p in e.get("path") or ())
    else:
        def own(e):
            return bool(set(e.get("path") or ()) & basin_ins)
    other = [s for s in ents["segments"] if roles.get(s["layer"], AP.OTHER) == AP.OTHER and
             not own(s) and in_box(s["a"]) and in_box(s["b"])]
    o_arcs = [a for a in ents["arcs"] if roles.get(a["layer"], AP.OTHER) == AP.OTHER and
              not own(a) and in_box(a["c"])]
    wall_segs = [s for s in ents["segments"] if roles.get(s["layer"]) == AP.WALL]
    seg_by = {s["id"]: s for s in other}
    wcs = []
    if v271:
        o_circ = [c for c in ents.get("circles") or () if roles.get(c["layer"], AP.OTHER) == AP.OTHER and
                  not own(c) and in_box(c["c"])]
        excl = sum(1 for e in list(ents["segments"]) + list(ents["arcs"]) + list(ents.get("circles") or ())
                   if roles.get(e["layer"], AP.OTHER) == AP.OTHER and own(e) and
                   in_box(e["a"] if "a" in e else e["c"]))
        acc, rej = wc_shapes_v271(other, o_arcs, o_circ, unit_m, wall_segs)
        wcs = [w for w in acc if inside(*w["centre"])]
        wc_rejected = [w for w in rej if inside(*w["centre"])]
    else:
        for w in wc_shapes(other, o_arcs, unit_m, wall_segs):
            pts = [p for i in w["bowl_ids"] if i in seg_by for p in (seg_by[i]["a"], seg_by[i]["b"])]
            if pts and inside(sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)):
                wcs.append(w)
    other = [s for s in other if inside((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2)]
    rec = {"face_id": face["face_id"], "fixtures": sorted(x["fixture"] for x in fixtures), "wc_shapes": wcs}
    if v271:
        rec.update(wc_rejected=wc_rejected, basin_linework_excluded=excl, wc_profile="UP-WET-002 1.3.0")
    if fx_codes and len(fx_codes) == 1 and wet_fx and len(basins) == len(wet_fx):
        corr = []
        if wcs:
            corr.append("WC_SHAPE")
        # the basins' own fittings (taps, waste, mixer, counter edge) drawn loose beside their blocks are the basin,
        # not a second piece of evidence
        reach = FITTING_REACH_M / unit_m
        box_of = {i["id"]: i.get("box") or (i["x"], i["y"], i["x"], i["y"]) for i in ents.get("inserts") or ()}
        foot = [(b[0] - reach, b[1] - reach, b[2] + reach, b[3] + reach)
                for b in (box_of.get(x) for x in sorted(basin_ins)) if b]

        def fitting(q):
            return any(f[0] <= q[0] <= f[2] and f[1] <= q[1] <= f[3] for f in foot)
        lay = [s for s in other if any(re.search(p, AR.DM.normalize(s["layer"]).upper())
                                       for p, c in AR.FIXTURE_LAYERS if c == "BATHROOM")]
        rec["basin_fittings_excluded"] = sum(1 for s in lay if fitting(s["a"]) and fitting(s["b"]))
        lay = [s for s in lay if not (fitting(s["a"]) and fitting(s["b"]))]
        if len(lay) >= AR.FIXTURE_LAYER_MIN_SEGMENTS:
            corr.append("SANITARY_LAYER")
        rec["corroboration"] = corr
        if corr:
            rec["decision"] = "WET_BASIN_CORROBORATED"
            return ["BATHROOM"], "FIXTURES+" + "+".join(corr), (
                f"ROOM_TYPE_FROM_FIXTURES+{'+'.join(corr)}: no room word inside; a wash basin (" +
                ", ".join(x["block"] for x in basins) + ") and " + " and ".join(
                    {"WC_SHAPE": "a water closet drawn as linework", "SANITARY_LAYER": "sanitary-layer linework"}[c]
                    for c in corr) + " - two independent pieces of sanitary evidence (UP-WET-002); review"), rec
        rec["decision"] = "WET_CLASSIFICATION_REVIEW"
        return None, None, ("WET_CLASSIFICATION_REVIEW (UP-WET-002): no room word inside; it holds only wash "
                            "basin(s) (" + ", ".join(x["block"] for x in basins) + ") - a basin alone does not make a "
                            "space wet; no water closet, shower or bath is drawn: the room type is for review (no wet "
                            "and no dry scope is applied)"), rec
    if not fx_codes and not layer_ev and wcs:
        rec["decision"] = "WC_CANDIDATE_REVIEW"
        return None, None, ("WC_CANDIDATE_REVIEW (UP-WET-002): no room word inside; a water-closet shape is drawn as "
                            "linework - one geometric shape is not enough to type the space; review"), rec
    rec["decision"] = "V2_6_READING"
    return False, None, None, rec


# ---------------------------------------------------------------- per-line source entities (provenance, V2.7)
DRAWN_ID = re.compile(r"^D\d+:(\d+)(?:@(D\d+:\d+(?:/D\d+:\d+)*))?:(\d+)(~\d+)?$")


def entity_ref(sid):
    """an intake entity id -> {"id", "handle", "insert_path", "part"}: the DXF handle (hex) of the entity, the handles
    of the block inserts that place it (outermost first) and its part index (a polyline's segment); None for an engine
    item (a threshold, a closure, a cap, a zero-material wall piece)."""
    m = DRAWN_ID.match(str(sid))
    if not m:
        return None
    path = [format(int(x.split(":")[1]), "X") for x in (m.group(2) or "").split("/") if x]
    return {"id": sid, "handle": format(int(m.group(1)), "X"), "insert_path": path, "part": int(m.group(3))}


def attach_provenance(lines, rooms, faces, openings, doors, walls=(), floor=None, region_id=None, v271=False):
    """every line of a measured room carries the drawn entities that bound the room (source.entities); every opening
    and door line the door symbol and jamb entities (a window: its glazing lines; a passage: the wall faces ending at
    its jambs) of its opening; a wall line of a
    thickness family the face segments of the region's walls of that family. A line of none of these carries none
    (recorded as such). -> counts. v271 (ARCH_TAKEOFF_V2.7.1 only): a doorway-strip line carries its strip faces'
    boundary entities and the door-closure entities that close them (basis STRIP); a line still without entities says
    why (reason); False is the V2.7 path, unchanged."""
    by_face = {f["face_id"]: f for f in faces}
    room_ents = {}
    for r in rooms:
        f = by_face.get(r.get("face_id"))
        ids = sorted({x for x in (f or {}).get("boundary_source_ids") or () if entity_ref(x)})
        room_ents[r["room_id"]] = [entity_ref(x) for x in ids]
    op_ents = {}
    for o in openings:
        ids = set()
        sym = o.get("door_symbol") or ""
        if "|" in sym:
            ids.add(sym.split("|", 1)[1])
        ids |= set((o.get("opening_v27") or {}).get("jamb_lines") or ())
        # an opening's final kind decides (a gap first read as a passage can become a door at the door review)
        ids |= set(o.get({"WINDOW": "glazing_ids", "PASSAGE": "gap_ids"}.get(o.get("kind"), "-")) or ())
        op_ents[o["opening_id"]] = [e for e in (entity_ref(x) for x in sorted(ids)) if e]
    fam_ents = defaultdict(set)
    for w in walls:
        fam_ents[w["family"]] |= {x for x in w.get("source_ids") or () if entity_ref(x)}
    el_op = {el["element_id"]: el.get("opening_id") for el in (doors or {}).get("elements") or ()}
    n = {"room": 0, "opening": 0, "wall": 0, "none": 0}
    for ln in lines:
        loc = ln.get("location") or {}
        rid, el = loc.get("room_id"), str(loc.get("element_id") or "")
        fam = re.fullmatch(r"walls t=(\S+)", str(ln.get("physical_element") or ""))
        if fam and str(rid).endswith("-WALLS") and fam_ents.get(fam.group(1)):
            ln["source"]["entities"] = {"basis": "WALL_BANDS", "floor": floor, "region_id": region_id,
                                        "family": fam.group(1),
                                        "entities": [entity_ref(x) for x in sorted(fam_ents[fam.group(1)])]}
            n["wall"] += 1
            continue
        oid = el_op.get(ln.get("physical_element")) or next(
            (t for t in re.findall(r"OP-\d+", el + " " + str(loc.get("room_name_en") or "")) if t in op_ents), None)
        if rid in room_ents and room_ents[rid] and not str(ln["item_code"]).startswith(("DOOR.", "ARCH.DOOR",
                                                                                          "ARCH.WINDOW",
                                                                                          "ARCH.PASSAGE")):
            ln["source"]["entities"] = {"basis": "ROOM_BOUNDARY", "room_id": rid, "entities": room_ents[rid]}
            n["room"] += 1
        elif oid is not None:
            ln["source"]["entities"] = {"basis": "OPENING", "floor": floor, "region_id": region_id, "opening_id": oid,
                                        "entities": op_ents.get(oid) or []}
            n["opening"] += 1
        elif v271 and _strip_entities(ln, by_face):
            ids, strips = _strip_entities(ln, by_face)
            ln["source"]["entities"] = {"basis": "STRIP", "floor": floor, "region_id": region_id, "strips": strips,
                                        "entities": [entity_ref(x) for x in ids]}
            n["strip"] = n.get("strip", 0) + 1
        else:
            ln["source"]["entities"] = {"basis": "NOT_TRACED", "entities": []}
            if v271:
                ln["source"]["entities"]["reason"] = (
                    "NOT_IN_A_PLAN_REGION: the line is not measured from one region's drawn entities (a run-level "
                    "item)" if floor is None else "NO_DRAWN_ENTITY: the line is not measured from drawn entities of "
                    "its own (an engine count, a rule-derived item or a question)")
            n["none"] += 1
    return n


def _strip_entities(ln, by_face):
    """ARCH_TAKEOFF_V2.7.1: the drawn entities of a doorway-strip line - the boundary entities of its strip faces and
    the entities of the door closures that close them. -> (ids, strips) or None."""
    inp = (ln.get("calculation") or {}).get("inputs") or {}
    strips = [s for s in inp.get("strips") or () if s in by_face]
    ids = {x for s in strips for x in by_face[s].get("boundary_source_ids") or () if entity_ref(x)}
    for c in inp.get("door_closures") or ():
        ids |= {x for x in str(c).split("|")[1:] if entity_ref(x)}
    return (sorted(ids), strips) if ids else None
