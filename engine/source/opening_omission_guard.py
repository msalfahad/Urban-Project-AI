"""OPENING OMISSION GUARD (T-077): every drawn window and door appears once - MEASURED by the engine, or HELD with
the traced reason it is not - never silently lost and never 0.

T-040 found, on the development villa, two drawn windows that are in no engine output (no opening, no held record):
a curved glazing run in a STRAIGHT wall gap (the curved-opening reader, UP-OPEN-CURVED-001, only reads gaps of curved
wall bands) and a 0.50 m window whose wall gap a column outline overlaps by a few centimetres (the column split of
lintel_measure.openings keeps only pieces of at least 0.50 m and drops the rest without a record). It also found one
engine door element with no door block (its swing is a loose arc, not a block). This method piece reports, per plan
frame, every piece of drawn opening evidence once. It is NOT wired into a released method: no frozen file, no
released method, no opening and no quantity is changed; nothing it HOLDS becomes a quantity.

    guard(openings, glazing, swings=None, door_elements=(), walls=(), columns=(), wall_arcs=(), dims=(),
          frame=None, unit_m=None, tol_m=0.001) -> {"windows", "doors", "clusters", "summary"}

    openings      the engine openings of ONE frame (arch_rooms.spaces()["openings"]): straight records carry the band
                  frame u, n, s0, s1, o0, o1 (drawing units), curved ones also "curved" (centre_du, radii_du,
                  angles_rad); "opening_id", "kind" (WINDOW / DOOR / PASSAGE), "width_m"
    glazing       the WINDOW-role linework of the frame: {"segments": [{"id", "a", "b"}], "arcs": [{"id", "c", "r",
                  "s", "e", "dir"}]} (arch_plan.region_entities format; bulge polylines arrive exploded)
    swings        door swings {occ: {"hinge", "radius", ...}} (arch_rooms.door_swings); occ "<insert>|<arc>@..."
                  is a block symbol, an occ without "@" a loose arc
    door_elements engine door elements of the frame (door_model, DOOR_SCHEDULE): "element_id", "swings",
                  "section", "released", "structural_opening_width_m"
    walls         wall-role segments {"id", "a", "b"} (cause diagnosis only)
    columns       column outlines [[(x, y), ...]] (cause diagnosis only)
    wall_arcs     wall-role arcs (curved cause diagnosis only)
    dims          printed dimensions [{"id", "kind": "LINEAR" | "ARC", "value_du", "p1", "p2", "centre"}]: a printed
                  value that matches a measured span is reported next to it (evidence, never a release)
    unit_m        metres per drawing unit; None = units not established (lengths stay None, UNITS_MISSING)
    tol_m         numerical coincidence (a point on a line, two endpoints that touch); never a drafting-gap closure

Records (UP-QTY-STATUS-001: every drawn element reported once, released, held or excluded; never 0):
    window  MEASURED  ENGINE_WINDOW          an engine WINDOW opening (the engine's count line); its glazing clusters
            HELD      WINDOW_NOT_IN_ENGINE   glazing that lies in no engine opening, with "cause" (below), the
                                             measured spans as width CANDIDATES and any matching printed dimension;
                                             no width, height or area is released (UP-OPEN-SCHED-001: no height is
                                             printed for the plan; UP-OPEN-CURVED-001 covers curved wall bands only)
    door    MEASURED  ENGINE_DOOR_RELEASED   an engine door element released by the engine
            HELD      ENGINE_DOOR_HELD       an engine door element the engine holds (its own section kept)
            HELD      SWING_NOT_IN_ENGINE    a drawn swing that no engine door element uses
    every door record names its symbol: BLOCK (a block insert), LOOSE_ARC (a swing drawn as a plain arc) or NONE.
Causes of a held window (diagnostic: the first that holds, from the frame's own wall lines and columns):
    CURVED_GLAZING_WITHOUT_CURVED_WALL_BAND  most of the glazing is arcs and no wall arc is concentric with it: the
                                             gap is straight (or absent), UP-OPEN-CURVED-001 does not read it
    CURVED_GLAZING_CURVED_GAP_REFUSED        concentric wall arcs exist, the curved gap was refused (V2.9 reasons)
    NO_JAMB_AT_BOTH_ENDS / NO_JAMB_AT_ONE_END no wall line across the glazing at its end(s) (within 30 mm)
    GAP_UNDER_MIN_GAP                        jamb to jamb is narrower than the 0.50 m opening minimum
    COLUMN_CUT_PIECE_UNDER_MIN_GAP           a column outline stands in the gap and every remaining piece is narrower
                                             than 0.50 m (lintel_measure._split_at_columns drops such pieces)
    WALL_BAND_NOT_READ                       jambs and a clear piece exist: the band faces were not paired (traced no
                                             further here)
General: no layer, block, room or project name is coded; mirrored, rotated, mm and m plans read alike (vectors and
distances only). Stdlib only.
"""

from __future__ import annotations

import math

POLICY = "OPENING_OMISSION_GUARD_V1"
RULES = ("UP-QTY-STATUS-001", "UP-OPEN-SCHED-001", "UP-OPEN-CURVED-001", "UP-QA-001")
MIN_GAP_M = 0.50            # the band-opening minimum of lintel_measure.openings (min_gap_m) - checked by a test
BIND_SHARE = 0.5            # glazing belongs to an opening when half its length lies in the opening (arch_rooms:
                            # a gap is a WINDOW when its glazing covers half its width; arch_v29.GLAZING_SHARE)
CURVED_SHARE = 0.5          # a cluster is curved when arcs make at least half of its length
PERP_COS = 0.02             # a jamb line is across the opening axis within about 1.1 degrees
JAMB_REACH_M = 0.03         # a jamb line stands at the glazing's end within the band-gap jamb tolerance (30 mm,
                            # lintel_measure.openings jamb_tol)
DIM_REACH_M = 3.0           # a printed dimension is looked for within this distance of the opening (evidence only)
PRINT_TOL_M = 0.005         # a printed value matches a measured span within 5 mm (the curved-face agreement)
SAMPLES = 8                 # points per piece for the share tests


# ------------------------------------------------------------------------------------------------- geometry helpers
def _sweep(a):
    cx, cy = a["c"]
    a0 = math.atan2(a["s"][1] - cy, a["s"][0] - cx)
    a1 = math.atan2(a["e"][1] - cy, a["e"][0] - cx)
    if a.get("dir") == "CW":
        a0, a1 = a1, a0
    if a1 <= a0:
        a1 += 2.0 * math.pi
    return a0, a1


def _arc_len(a):
    a0, a1 = _sweep(a)
    return a["r"] * (a1 - a0)


def _arc_pts(a, n=SAMPLES):
    a0, a1 = _sweep(a)
    return [(a["c"][0] + a["r"] * math.cos(a0 + (a1 - a0) * (i + 0.5) / n),
             a["c"][1] + a["r"] * math.sin(a0 + (a1 - a0) * (i + 0.5) / n)) for i in range(n)]


def _seg_pts(s, n=SAMPLES):
    return [(s["a"][0] + (s["b"][0] - s["a"][0]) * (i + 0.5) / n,
             s["a"][1] + (s["b"][1] - s["a"][1]) * (i + 0.5) / n) for i in range(n)]


def _pd(p, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def _on_arc(p, a, tol):
    if abs(math.dist(p, a["c"]) - a["r"]) > tol:
        return False
    a0, a1 = _sweep(a)
    ang = math.atan2(p[1] - a["c"][1], p[0] - a["c"][0])
    d = (ang - a0) % (2.0 * math.pi)
    return d <= (a1 - a0) + tol / max(a["r"], 1e-12)


def _ends(piece):
    return [tuple(piece["a"]), tuple(piece["b"])] if "a" in piece else [tuple(piece["s"]), tuple(piece["e"])]


def _touch(p, q, tol):
    """two glazing pieces touch: an end of one lies on the other (end to end or a T-junction) within tol."""
    for x, y in ((p, q), (q, p)):
        for e in _ends(x):
            if "a" in y:
                if _pd(e, y["a"], y["b"]) <= tol:
                    return True
            elif _on_arc(e, y, tol):
                return True
    return False


def _bbox_near(p, q, tol):
    def bb(x):
        if "a" in x:
            xs, ys = (x["a"][0], x["b"][0]), (x["a"][1], x["b"][1])
            return min(xs), min(ys), max(xs), max(ys)
        return x["c"][0] - x["r"], x["c"][1] - x["r"], x["c"][0] + x["r"], x["c"][1] + x["r"]
    a, b = bb(p), bb(q)
    return not (a[2] + tol < b[0] or b[2] + tol < a[0] or a[3] + tol < b[1] or b[3] + tol < a[1])


def clusters(glazing, tol):
    """connected groups of glazing pieces (touching end to end or at a T-junction within tol) -> [{"ids", "pieces"}]
    in a stable order; every piece in exactly one cluster."""
    pieces = [dict(s, _k="SEG") for s in (glazing or {}).get("segments") or ()] + \
             [dict(a, _k="ARC") for a in (glazing or {}).get("arcs") or ()]
    pieces.sort(key=lambda x: str(x["id"]))
    parent = list(range(len(pieces)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(pieces)):
        for j in range(i + 1, len(pieces)):
            if _bbox_near(pieces[i], pieces[j], tol) and _touch(pieces[i], pieces[j], tol):
                parent[find(i)] = find(j)
    groups = {}
    for i, p in enumerate(pieces):
        groups.setdefault(find(i), []).append(p)
    out = [{"ids": sorted(str(p["id"]) for p in g), "pieces": g} for g in groups.values()]
    out.sort(key=lambda c: c["ids"][0])
    for i, c in enumerate(out):
        c["cluster_id"] = f"GL-{i + 1:03d}"
    return out


def _piece_len(p):
    return math.dist(p["a"], p["b"]) if p["_k"] == "SEG" else _arc_len(p)


def _piece_pts(p):
    return _seg_pts(p) if p["_k"] == "SEG" else _arc_pts(p)


def _in_opening(pt, o, tol):
    cv = o.get("curved")
    if cv:
        c = cv["centre_du"]
        r1, r2 = cv["radii_du"]
        rho = math.dist(pt, c)
        if not r1 - tol <= rho <= r2 + tol:
            return False
        th0, th1, h0, h1 = cv["angles_rad"]
        a0, a1 = min(th0, h0), max(th1, h1)
        d = (math.atan2(pt[1] - c[1], pt[0] - c[0]) - a0) % (2.0 * math.pi)
        return d <= (a1 - a0) + tol / max(r1, 1e-12)
    (ux, uy), (nx, ny) = o["u"], o["n"]
    s, n = pt[0] * ux + pt[1] * uy, pt[0] * nx + pt[1] * ny
    lo, hi = sorted((o["o0"], o["o1"]))
    return o["s0"] - tol <= s <= o["s1"] + tol and lo - tol <= n <= hi + tol


def _share_in(cl, o, tol):
    tot = sum(_piece_len(p) for p in cl["pieces"])
    if tot <= 0:
        return 0.0
    ins = 0.0
    for p in cl["pieces"]:
        pts = _piece_pts(p)
        ins += _piece_len(p) * sum(1 for q in pts if _in_opening(q, o, tol)) / len(pts)
    return ins / tot


# ------------------------------------------------------------------------------------------------- cause diagnosis
def _m(v, unit_m, nd=4):
    return None if v is None or unit_m is None else round(v * unit_m, nd)


def _poly_pts(cl):
    pts = []
    for p in cl["pieces"]:
        pts += _ends(p) + _piece_pts(p)
    return pts


def _axis(cl):
    """the cluster's axis: the direction of its longest straight piece, else the chord of its two farthest points."""
    segs = [p for p in cl["pieces"] if p["_k"] == "SEG" and math.dist(p["a"], p["b"]) > 0]
    pts = _poly_pts(cl)
    longest_arc = max((p for p in cl["pieces"] if p["_k"] == "ARC"), key=_arc_len, default=None)
    if longest_arc is not None and (not segs or _arc_len(longest_arc) >= max(math.dist(s["a"], s["b"]) for s in segs)):
        a, b = longest_arc["s"], longest_arc["e"]
    elif segs:
        s = max(segs, key=lambda x: math.dist(x["a"], x["b"]))
        a, b = s["a"], s["b"]
    else:
        a, b = max(((p, q) for p in pts for q in pts), key=lambda t: math.dist(*t))
    L = math.dist(a, b) or 1.0
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    return u, (-u[1], u[0])


def _jambs(cl, u, n, walls, tol, unit_m=None):
    """the nearest wall line across the axis at each end of the glazing: (s_lo, id_lo), (s_hi, id_hi)."""
    pts = _poly_pts(cl)
    ss = [p[0] * u[0] + p[1] * u[1] for p in pts]
    oo = [p[0] * n[0] + p[1] * n[1] for p in pts]
    smin, smax, omin, omax = min(ss), max(ss), min(oo), max(oo)
    lo = hi = None
    reach = JAMB_REACH_M / unit_m if unit_m else max(smax - smin, tol) * 0.03
    for w in walls or ():
        d = (w["b"][0] - w["a"][0], w["b"][1] - w["a"][1])
        L = math.hypot(*d)
        if L <= 0 or abs((d[0] * u[0] + d[1] * u[1]) / L) > PERP_COS:
            continue
        sw = [(w["a"][0] + w["b"][0]) / 2 * u[0] + (w["a"][1] + w["b"][1]) / 2 * u[1]]
        ow = sorted(q[0] * n[0] + q[1] * n[1] for q in (w["a"], w["b"]))
        if ow[1] < omin - tol or ow[0] > omax + tol:
            continue
        s = sw[0]
        if not (smin - reach <= s <= smin + tol or smax - tol <= s <= smax + reach):
            continue
        if s <= smin + tol and (lo is None or s > lo[0] or (s == lo[0] and str(w["id"]) < lo[1])):
            lo = (s, str(w["id"]))
        if s >= smax - tol and (hi is None or s < hi[0] or (s == hi[0] and str(w["id"]) < hi[1])):
            hi = (s, str(w["id"]))
    return lo, hi, (smin, smax, omin, omax)


def _column_pieces(s_lo, s_hi, ext, u, n, columns, tol):
    omin, omax = ext[2], ext[3]
    cuts = []
    for poly in columns or ():
        ss = [p[0] * u[0] + p[1] * u[1] for p in poly]
        oo = [p[0] * n[0] + p[1] * n[1] for p in poly]
        if max(oo) < omin - tol or min(oo) > omax + tol:
            continue
        a, b = max(min(ss), s_lo), min(max(ss), s_hi)
        if b - a > tol:
            cuts.append((a, b))
    cuts.sort()
    pieces, s = [], s_lo
    for a, b in cuts + [(s_hi, s_hi)]:
        if a - s > tol:
            pieces.append((s, a))
        s = max(s, b)
    return cuts, pieces


def _printed_linear(dims, u, n, s_lo, s_hi, centre, unit_m, tol):
    out = []
    if unit_m is None:
        return out
    pt = PRINT_TOL_M / unit_m
    for d in dims or ():
        if d.get("kind") != "LINEAR" or d.get("p1") is None or d.get("p2") is None:
            continue
        a = sorted(p[0] * u[0] + p[1] * u[1] for p in (d["p1"], d["p2"]))
        if abs(a[0] - s_lo) > pt or abs(a[1] - s_hi) > pt or abs(d["value_du"] - (s_hi - s_lo)) > pt:
            continue
        mid = ((d["p1"][0] + d["p2"][0]) / 2, (d["p1"][1] + d["p2"][1]) / 2)
        if math.dist(mid, centre) * unit_m > DIM_REACH_M:
            continue
        out.append({"dim_id": d["id"], "printed_m": round(d["value_du"] * unit_m, 4), "basis": "JAMB_TO_JAMB"})
    return out


def _curved_facts(cl, wall_arcs, dims, unit_m, tol):
    arcs = [p for p in cl["pieces"] if p["_k"] == "ARC"]
    big = max(arcs, key=_arc_len)
    c = big["c"]
    runs = []                                        # [radius, summed length] of the arcs concentric with the longest
    for a in sorted((a for a in arcs if math.dist(a["c"], c) <= max(10 * tol, 0.002 * big["r"])), key=lambda x: x["r"]):
        if runs and a["r"] - runs[-1][0] <= tol:
            runs[-1][1] += _arc_len(a)
        else:
            runs.append([a["r"], _arc_len(a)])
    pts = _poly_pts(cl)
    chord = max(math.dist(p, q) for p in [e for x in cl["pieces"] for e in _ends(x)] for q in pts) if pts else None
    conc = [w for w in wall_arcs or () if math.dist(w["c"], c) <= max(10 * tol, 0.002 * big["r"])]
    printed = []
    for d in dims or ():
        if d.get("kind") != "ARC" or d.get("centre") is None or unit_m is None:
            continue
        if math.dist(d["centre"], c) * unit_m > 0.01:
            continue
        r_d = math.dist(d["p1"], d["centre"]) if d.get("p1") is not None else None
        on_glazing = r_d is not None and any(abs(r_d - a["r"]) <= PRINT_TOL_M / unit_m for a in arcs)
        printed.append({"dim_id": d["id"], "printed_m": round(d["value_du"] * unit_m, 4),
                        "radius_m": _m(r_d, unit_m), "basis": "GLAZING_ARC" if on_glazing else "ARC_AT_OTHER_RADIUS"})
    return {"centre_du": [c[0], c[1]],
            "glazing_arcs": [{"radius_m": _m(r, unit_m), "length_m": _m(L, unit_m)} for r, L in runs],
            "chord_m": _m(chord, unit_m), "concentric_wall_arcs": len(conc), "printed": printed}


def diagnose(cl, walls=(), columns=(), wall_arcs=(), dims=(), unit_m=None, tol=None, curved_rejected=()):
    """-> {"cause", "geometry", "spans", "printed", ...}: why a glazing cluster is in no engine opening."""
    tot = sum(_piece_len(p) for p in cl["pieces"])
    arc_len = sum(_piece_len(p) for p in cl["pieces"] if p["_k"] == "ARC")
    tol = tol if tol is not None else 1e-9
    out = {"glazing_length_m": _m(tot, unit_m), "pieces": len(cl["pieces"])}
    if tot > 0 and arc_len / tot >= CURVED_SHARE:
        cf = _curved_facts(cl, wall_arcs, dims, unit_m, tol)
        out.update(geometry="CURVED", curved=cf)
        u, n = _axis(cl)
        lo, hi, ext = _jambs(cl, u, n, walls, tol, unit_m)
        out["spans"] = {"jamb_to_jamb_m": _m(hi[0] - lo[0], unit_m) if lo and hi else None,
                        "jambs": [lo and lo[1], hi and hi[1]]}
        out["cause"] = ("CURVED_GLAZING_CURVED_GAP_REFUSED" if cf["concentric_wall_arcs"] else
                        "CURVED_GLAZING_WITHOUT_CURVED_WALL_BAND")
        if cf["concentric_wall_arcs"]:
            out["curved_rejected"] = list(curved_rejected or ())
        out["printed"] = cf["printed"]
        return out
    u, n = _axis(cl)
    lo, hi, ext = _jambs(cl, u, n, walls, tol, unit_m)
    out.update(geometry="STRAIGHT", spans={"glazing_extent_m": _m(ext[1] - ext[0], unit_m),
                                           "jambs": [lo and lo[1], hi and hi[1]]}, printed=[])
    if lo is None or hi is None:
        out["cause"] = "NO_JAMB_AT_BOTH_ENDS" if lo is None and hi is None else "NO_JAMB_AT_ONE_END"
        return out
    gap = hi[0] - lo[0]
    out["spans"]["jamb_to_jamb_m"] = _m(gap, unit_m)
    centre = ((lo[0] + hi[0]) / 2 * u[0] + (ext[2] + ext[3]) / 2 * n[0],
              (lo[0] + hi[0]) / 2 * u[1] + (ext[2] + ext[3]) / 2 * n[1])
    out["printed"] = _printed_linear(dims, u, n, lo[0], hi[0], centre, unit_m, tol)
    min_gap = MIN_GAP_M / unit_m if unit_m else None
    cuts, pieces = _column_pieces(lo[0], hi[0], ext, u, n, columns, tol)
    out["spans"]["column_overlap_m"] = [_m(b - a, unit_m) for a, b in cuts]
    out["spans"]["clear_pieces_m"] = [_m(b - a, unit_m) for a, b in pieces]
    if min_gap is None:
        out["cause"] = "UNITS_MISSING"
    elif gap < min_gap - tol:
        out["cause"] = "GAP_UNDER_MIN_GAP"
    elif cuts and all(b - a < min_gap - tol for a, b in pieces):
        out["cause"] = "COLUMN_CUT_PIECE_UNDER_MIN_GAP"
    else:
        out["cause"] = "WALL_BAND_NOT_READ"
    return out


# ------------------------------------------------------------------------------------------------- the guard
def _tol_du(tol_m, unit_m, glazing):
    if unit_m:
        return tol_m / unit_m
    xs = [abs(v) for s in (glazing or {}).get("segments") or () for p in (s["a"], s["b"]) for v in p]
    return max(xs, default=1.0) * 1e-9


def _symbol_kind(occ):
    if not occ:
        return "NONE"
    return "BLOCK" if "@" in str(occ) else "LOOSE_ARC"


def guard(openings, glazing, swings=None, door_elements=(), walls=(), columns=(), wall_arcs=(), dims=(),
          frame=None, unit_m=None, tol_m=0.001, curved_rejected=()):
    if unit_m is not None and not (isinstance(unit_m, (int, float)) and unit_m > 0):
        raise ValueError(f"unit_m must be a positive number of metres per drawing unit or None, got {unit_m!r}")
    tol = _tol_du(tol_m, unit_m, glazing)
    ops = list(openings or ())
    cls = clusters(glazing, tol)
    # ---- windows: bind each glazing cluster to the engine opening holding most of it (at least BIND_SHARE)
    bound = {}
    for c in cls:
        best = max(((round(_share_in(c, o, tol), 9), str(o["opening_id"])) for o in ops), default=(0.0, None))
        if best[1] is not None and best[0] >= BIND_SHARE:
            bound[c["cluster_id"]] = best[1]
            c["bound_to"], c["share"] = best[1], best[0]
        else:
            c["bound_to"], c["share"] = None, best[0]
    windows = []
    for o in ops:
        if o.get("kind") != "WINDOW":
            continue
        windows.append({"policy": POLICY, "frame": frame, "status": "MEASURED", "reason": "ENGINE_WINDOW",
                        "opening_id": o["opening_id"], "curved": bool(o.get("curved")),
                        "width_m": round(o["width_m"], 4) if o.get("width_m") is not None else None,
                        "clusters": sorted(cid for cid, oid in bound.items() if oid == o["opening_id"])})
    held_w = []
    for c in cls:
        if c["bound_to"] is not None:
            continue
        dg = diagnose(c, walls, columns, wall_arcs, dims, unit_m, tol, curved_rejected)
        held_w.append({"policy": POLICY, "frame": frame, "status": "HELD", "reason": "WINDOW_NOT_IN_ENGINE",
                       "cause": dg["cause"], "clusters": [c["cluster_id"]], "glazing_ids": c["ids"],
                       "diagnosis": dg, "width_m": None, "height_m": None, "area_m2": None,
                       "basis": "drawn glazing in no engine opening: counted and held; no width, height or area is "
                                "released (spans below are candidates, printed values are evidence)"})
    # one window per jamb pair: held clusters sharing both jambs are one drawn window
    merged = []
    for h in held_w:
        j = h["diagnosis"].get("spans", {}).get("jambs")
        twin = next((m for m in merged if j and None not in j and m["diagnosis"].get("spans", {}).get("jambs") == j),
                    None)
        if twin:
            twin["clusters"] += h["clusters"]
            twin["glazing_ids"] = sorted(twin["glazing_ids"] + h["glazing_ids"])
        else:
            merged.append(h)
    for i, h in enumerate(merged):
        h["window_id"] = f"HW-{i + 1:03d}"
    windows += merged
    for c in cls:
        c.pop("pieces", None)
    # ---- doors: every engine element once, then every drawn swing no element uses
    used = set()
    doors = []
    for e in door_elements or ():
        occs = list(e.get("swings") or ())
        used.update(occs)
        rel = bool(e.get("released"))
        doors.append({"policy": POLICY, "frame": frame, "element_id": e.get("element_id"),
                      "status": "MEASURED" if rel else "HELD",
                      "reason": "ENGINE_DOOR_RELEASED" if rel else "ENGINE_DOOR_HELD",
                      "engine_section": e.get("section"), "swings": occs,
                      "symbol": sorted({_symbol_kind(x) for x in occs}) or ["NONE"],
                      "width_m": e.get("structural_opening_width_m")})
    for occ in sorted(swings or {}):
        if occ in used:
            continue
        sw = swings[occ]
        doors.append({"policy": POLICY, "frame": frame, "element_id": None, "status": "HELD",
                      "reason": "SWING_NOT_IN_ENGINE", "swings": [occ], "symbol": [_symbol_kind(occ)],
                      "leaf_m": _m(sw.get("radius"), unit_m), "width_m": None,
                      "basis": "a drawn door swing that no engine door element uses: counted and held"})
    pieces_n = sum(len(c["ids"]) for c in cls)
    n_pieces_in = len((glazing or {}).get("segments") or ()) + len((glazing or {}).get("arcs") or ())
    assert pieces_n == n_pieces_in                                        # every glazing piece in one cluster
    assert sum(len(w["clusters"]) for w in windows) + sum(1 for c in cls if c["bound_to"] is not None and
                                                         c["bound_to"] not in {w.get("opening_id") for w in windows}) \
        == len(cls)                                                       # every cluster once (window or other kind)
    hw = [w for w in windows if w["status"] == "HELD"]
    summary = {"policy": POLICY, "rules": list(RULES), "frame": frame,
               "windows_drawn": len(windows), "windows_engine": len(windows) - len(hw), "windows_held": len(hw),
               "held_by_cause": {k: sum(1 for w in hw if w["cause"] == k) for k in sorted({w["cause"] for w in hw})},
               "glazing_clusters": len(cls),
               "clusters_in_other_openings": sum(1 for c in cls if c["bound_to"] is not None and
                                                 c["bound_to"] not in {w.get("opening_id") for w in windows}),
               "doors_drawn": len(doors), "doors_released": sum(1 for d in doors if d["status"] == "MEASURED"),
               "doors_held": sum(1 for d in doors if d["status"] == "HELD"),
               "door_symbols": {k: sum(1 for d in doors if k in d["symbol"]) for k in ("BLOCK", "LOOSE_ARC", "NONE")},
               "swings_not_in_engine": sum(1 for d in doors if d["reason"] == "SWING_NOT_IN_ENGINE"),
               "silent_omissions": 0, "unit_status": "OK" if unit_m else "UNITS_MISSING"}
    return {"windows": windows, "doors": doors, "clusters": cls, "summary": summary}


def census_rows(result):
    """one flat row per window / door record (no coordinates)."""
    rows = []
    for w in result["windows"]:
        dg = w.get("diagnosis") or {}
        rows.append({"frame": w["frame"], "element": "WINDOW", "id": w.get("opening_id") or w.get("window_id"),
                     "status": w["status"], "reason": w["reason"], "cause": w.get("cause"),
                     "width_m": w.get("width_m"), "candidates": dg.get("spans"),
                     "printed": [p["printed_m"] for p in dg.get("printed") or ()], "clusters": len(w["clusters"])})
    for d in result["doors"]:
        rows.append({"frame": d["frame"], "element": "DOOR", "id": d.get("element_id") or d["swings"][0],
                     "status": d["status"], "reason": d["reason"], "cause": None, "width_m": d.get("width_m"),
                     "candidates": None, "printed": [], "symbol": ";".join(d["symbol"])})
    return rows
