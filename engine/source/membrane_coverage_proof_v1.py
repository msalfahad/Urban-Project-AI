"""MEMBRANE COVERAGE PROOF V1 (task T-137; a checker piece: read by no method, no quantity is changed or released here).
An independent proof that a membrane strip layout covers every piece of the surface the membrane must cover, or that
every piece it leaves is a DECLARED patch line (counted, with area and place). Why (research scout answer R-07): the
step-upturn miss on a roof (a 4.20 x 0.20 m upturn of a step edge parallel to the strips, 17 vs 18 rolls) came from
reading a strip at one line of its 1.00 m width; MEMBRANE_FOLD_V3 (T-096) fixed that case, but its own coverage check
is built from its own surface (MEMBRANE_FOLD_V3.required) and its own sheets, so it cannot catch an error in either.
This piece rebuilds both from first principles and tests the layout against them.

    surface       built here from the outline alone, edge by edge (never MEMBRANE_FOLD_V3.required): the floor, one
                  h-wide flap outward of every outer edge (h = upturn 0.20 m, UP-WP-003; Q-35 C: walls, doors and open
                  edges alike), the mitred corner piece at every convex outer corner (the strips are h longer at both
                  ends, Q-35 C; the T-094 hand method), the openings / obstructions cut out, and one h-wide flap
                  inside every opening edge (owner Q-29), no corner squares there. Compared with
                  MEMBRANE_FOLD_V3.required: a difference is a SURFACE_MISMATCH, never hidden.
    proof         R = difference(set_precision(surface, g), set_precision(union of the laid sheets, g), grid_size=g),
                  g = 0.001 m (R-07: GEOS snap rounding puts every result vertex on the grid). Every polygon of R is
                  (a) numerical: at most MEMBRANE_FOLD_V2.COVER_TOL_M2 (1 cm2, the engine's coverage limit; summed and
                  shown; a piece over it only by the snapping, perimeter x g, is judged on its unsnapped residue), (b) inside a DECLARED patch of the layout (the patch's box holds it; the patch's m2 must equal the
                  unsnapped residue its box holds within the engine limit 1 cm2), or (c) an UNDECLARED_RESIDUE: a
                  failure. A declared patch that covers no residue is PATCH_WITHOUT_RESIDUE (a counted piece that is not
                  needed); a patch box larger than the bounding box of its residue by more than 2 g is a warning
                  PATCH_BOX_LARGER_THAN_RESIDUE (the roll counts cut the piece at the box size).
    sheets        each laid sheet against its strip record (length = x extent, width = across extent <= roll width,
                  spliced pieces <= roll length with the end lap, UP-WP-002); the side lap between consecutive bands
                  >= lap; a joint between two sheets of one band over the surface has the end lap (a seam that
                  lies under a third sheet, e.g. the next band's side lap, is closed by it); the number of bands
                  >= the fewest that can span the surface across: ceil((D - lap) / (W - lap)) with D its extent across
                  the strips (the floor's extent + 2h). (R-07 wrote ceil(D / 0.90); that overstates the bound by one when D - 0.10 is a multiple
                  of 0.90, e.g. D = 1.00 m takes one strip, so the exact form is used.)
    projection    R-07's strip-length rule, per band: the surface inside the band's whole sheet extent, projected on
                  the strip axis, against the union of the band's sheets; the metres the sheets fall short of the
                  projection are shown per band (each must be closed by a patch or by a sheet of the next band).
    double need   where two flaps (or a flap and the floor) lie on the same flat place, one flat sheet cannot rise on
                  both faces: the union surface is then smaller than the membrane needed. Each such place is listed
                  with its m2: ADJACENT (the two edges meet: an internal corner of the floor or of an opening, h x h at
                  a right angle; MEMBRANE_FOLD_V2 counts these corners, "corner pieces by detail") or OPPOSED (two
                  faces of a wall, pier or slot thinner than 2h, or a flap over the floor beyond a wall thinner than
                  h): no Urban rule covers how that membrane is cut, so the place is NOT proven by a flat proof and is
                  reported, never assumed covered.
    frame         the layout frame is the engine's (MEMBRANE_FOLD_V3._frame / MEMBRANE_FOLD_V4._frame_at, turned by
                  _to_layout); this piece checks it instead of trusting it: every corner of the turned outline mapped
                  back to drawing units lies on a corner of the outline as given (within g) and the areas agree.
    verdict       PROVEN (no failure, no double need), PROVEN_EXCEPT_DETAIL (no failure; double-need places listed by
                  detail) or FAILED (every failure listed). Roll counts are not touched: a failure is a defect report.

    surface(ring, holes, h)                     -> the surface, its flaps, corners and double-need places (metres)
    prove(p, sheets, patches, spec)             -> the proof of one layout (p and sheets in the strip frame)
    prove_fold(polygon, holes, unit_m, spec)    -> MEMBRANE_FOLD_V5.fold proved layout by layout (the V3 layouts read by
                                                   ARCH_TAKEOFF_V2.12 / V2.13 and every V4 / V5 wall-frame layout), with
                                                   the layouts each method chooses marked
Rules: UP-WP-001 (roll 1.00 x 10.00 m), UP-WP-002 (lap 0.10 m), UP-WP-003 (upturn 0.20 m), UP-WP-005, owner Q-24
addendum (whole strips with cut edges), Q-29, Q-35 C, Q-49 A (each area alone), Q-58 A (conditional: prove corners and
terminations), UP-QTY-STATUS-001 (a held or unproven place is never 0). Project-agnostic: no layer, room name, size or
count of any project. shapely 2 (requirements.txt)."""

from __future__ import annotations

import math

import shapely
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from engine.source import membrane_fold_v2 as F2
from engine.source import membrane_fold_v3 as F3

METHOD_ID = "MEMBRANE_COVERAGE_PROOF_V1"
GRID_M = 0.001                      # R-07: the proof grid (1 mm); GEOS puts every result vertex on it
NUMERIC_M2 = F2.COVER_TOL_M2        # 1 cm2: the engine's coverage limit (MEMBRANE_FOLD_V2), not a new tolerance
EPS = F2.EPS
PROVEN, PROVEN_DETAIL, FAILED = "PROVEN", "PROVEN_EXCEPT_DETAIL", "FAILED"
ADJACENT, OPPOSED = "ADJACENT_EDGES_CORNER", "OPPOSED_FACES_OR_THIN_WALL"
RULES = ("UP-WP-001", "UP-WP-002", "UP-WP-003", "UP-WP-005", "owner Q-24 addendum", "owner Q-29", "owner Q-35 C",
         "owner Q-49 A", "owner Q-58 A (conditional)", "UP-QTY-STATUS-001")


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _parts(g):
    if g is None or g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g] if g.area > 0 else []
    out = []
    for x in getattr(g, "geoms", ()):
        out += _parts(x)
    return out


def _signed_area(pts):
    n = len(pts)
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))


def _ring(coords):
    pts = [(float(x), float(y)) for x, y in coords]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    return pts


# ------------------------------------------------------------------------------------------------ the surface
def surface(ring, holes=(), h=0.20):
    """the surface to cover, built edge by edge from the outline (metres, any frame). -> dict with "union" (Polygon /
    MultiPolygon), "floor", "flaps" [{ring, edge, poly}], "corners" [convex outer corner pieces], "double_need"."""
    outer = _ring(ring)
    if len(outer) < 3:
        raise ValueError("an outline needs at least 3 points")
    hs = [_ring(x) for x in holes or () if len(_ring(x)) >= 3]
    floor = Polygon(outer, hs)
    repaired = False
    if not floor.is_valid:
        # an opening that touches the outline at a point is valid as drawn, but turning it into a layout frame can
        # leave a 1e-15 m crossing; it is repaired only when the repair keeps the area (rotation noise, not a shape)
        polys = _parts(shapely.make_valid(floor))
        fixed = max(polys, key=lambda g: g.area) if polys else None
        want = abs(_signed_area(outer)) - sum(abs(_signed_area(x)) for x in hs)
        if fixed is not None and abs(fixed.area - want) <= 1e-6 * max(1.0, want):
            floor, repaired = fixed, True
        else:
            raise ValueError("the outline is not a simple polygon with an area")
    if floor.area <= EPS:
        raise ValueError("the outline is not a simple polygon with an area")
    flaps, corners = [], []
    for ri, pts in enumerate([outer] + hs):
        n = len(pts)
        ccw = _signed_area(pts) > 0
        out_sign = 1.0 if ccw else -1.0          # the right-hand normal of a ccw ring points outside it
        if ri > 0:
            out_sign = -out_sign                 # an opening: the floor is outside its ring, the flap lies inside it
        normals = []
        for i in range(n):
            p, q = pts[i], pts[(i + 1) % n]
            d = (q[0] - p[0], q[1] - p[1])
            L = math.hypot(*d)
            if L <= EPS:
                normals.append(None)
                continue
            nx, ny = d[1] / L * out_sign, -d[0] / L * out_sign
            normals.append((nx, ny))
            flaps.append({"ring": ri, "edge": i, "length_m": L, "normal": (nx, ny),
                          "poly": Polygon([p, q, (q[0] + nx * h, q[1] + ny * h), (p[0] + nx * h, p[1] + ny * h)])})
        if ri > 0:
            continue                             # Q-29 opening flaps: no corner squares (as MEMBRANE_FOLD_V2._flaps)
        for i in range(n):
            n0, n1 = normals[i - 1], normals[i]
            if n0 is None or n1 is None:
                continue
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
            cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            convex = cross > 1e-12 if ccw else cross < -1e-12
            if not convex:
                continue
            dot = n0[0] * n1[0] + n0[1] * n1[1]
            if dot <= -1 + 1e-9:
                continue
            k = h / (1.0 + dot)                  # the mitre point b + (n0 + n1) h / (1 + n0.n1)
            m = (b[0] + (n0[0] + n1[0]) * k, b[1] + (n0[1] + n1[1]) * k)
            piece = Polygon([b, (b[0] + n0[0] * h, b[1] + n0[1] * h), m, (b[0] + n1[0] * h, b[1] + n1[1] * h)])
            corners.append({"vertex": i, "mitre_ratio": _r(math.dist(b, m) / h, 4),
                            "poly": piece if piece.is_valid else piece.buffer(0)})
    hole_union = unary_union([Polygon(x) for x in hs]) if hs else None
    body = unary_union([Polygon(outer)] + [f["poly"] for f in flaps if f["ring"] == 0] + [c["poly"] for c in corners])
    if hole_union is not None:
        body = body.difference(hole_union)
    inner = unary_union([f["poly"] for f in flaps if f["ring"] > 0]) if hs else None
    union = body if inner is None else unary_union([body, inner])
    return {"union": union, "body": body, "openings": inner, "floor": floor, "flaps": flaps, "corners": corners,
            "repaired_after_turn": repaired,
            "double_need": _double_need(floor, flaps, [len(outer)] + [len(x) for x in hs])}


def _adjacent(f, g, sizes):
    if f["ring"] != g["ring"]:
        return False
    n = sizes[f["ring"]]
    return (f["edge"] - g["edge"]) % n in (1, n - 1)


def _double_need(floor, flaps, sizes):
    """places where one flat sheet would have to serve two faces: two flaps on the same place, or a flap over floor."""
    out = []
    for i in range(len(flaps)):
        f = flaps[i]
        over_floor = f["poly"].intersection(floor).area
        if over_floor > NUMERIC_M2:
            out.append({"kind": OPPOSED, "what": "flap over the floor (a wall thinner than h)",
                        "edges": [(f["ring"], f["edge"])], "m2": _r(over_floor),
                        "centre": tuple(_r(v, 4) for v in f["poly"].intersection(floor).centroid.coords[0])})
        for j in range(i + 1, len(flaps)):
            g = flaps[j]
            if not f["poly"].intersects(g["poly"]):
                continue
            ov = f["poly"].intersection(g["poly"])
            if ov.area <= NUMERIC_M2:
                continue
            adj = _adjacent(f, g, sizes)
            out.append({"kind": ADJACENT if adj else OPPOSED,
                        "what": "internal corner" if adj else "two faces closer than 2h (wall, pier or slot)",
                        "edges": [(f["ring"], f["edge"]), (g["ring"], g["edge"])], "m2": _r(ov.area),
                        "centre": tuple(_r(v, 4) for v in ov.centroid.coords[0])})
    return out


# ------------------------------------------------------------------------------------------------ one layout
def _intervals(geom, axis=0):
    """the projection of a geometry's polygons on an axis as merged intervals."""
    iv = sorted((g.bounds[axis], g.bounds[axis + 2]) for g in _parts(geom))
    out = []
    for a, b in iv:
        if out and a <= out[-1][1] + GRID_M:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def _gap(need, have):
    """metres of the intervals `need` not inside the intervals `have`."""
    tot = 0.0
    for a, b in need:
        cur = a
        for c, d in have:
            if d <= cur or c >= b:
                continue
            if c > cur:
                tot += c - cur
            cur = max(cur, d)
        if cur < b:
            tot += b - cur
    return tot


def _sheet_checks(sheets, strips, spec, surf, floor):
    """the laid sheets against their strip records, the laps and the band-count bound. -> (failures, info)."""
    W, L, lap = spec["roll_width_m"], spec["roll_length_m"], spec["lap_m"]
    fails, tol = [], 1e-6
    if len(sheets) != len(strips):
        fails.append(f"SHEET_RECORD_COUNT: {len(sheets)} sheets laid, {len(strips)} strips recorded")
    for k, (sh, st) in enumerate(zip(sheets, strips), 1):
        x0, s0, x1, s1, _kind = sh
        if abs((x1 - x0) - st["length_m"]) > tol:
            fails.append(f"STRIP_LENGTH: S{k} laid {x1 - x0:.4f} m, recorded {st['length_m']:.4f} m")
        if abs((s1 - s0) - st["width_m"]) > tol:
            fails.append(f"STRIP_WIDTH: S{k} laid {s1 - s0:.4f} m, recorded {st['width_m']:.4f} m")
        if st["width_m"] > W + tol:
            fails.append(f"STRIP_WIDER_THAN_ROLL: S{k} {st['width_m']:.4f} m")
        ps = st["piece_lengths_m"]
        if any(x > L + tol for x in ps):
            fails.append(f"PIECE_LONGER_THAN_ROLL: S{k} {max(ps):.4f} m")
        if abs(sum(ps) - (len(ps) - 1) * lap - st["length_m"]) > 1e-5:
            fails.append(f"SPLICE: S{k} pieces {ps} do not make {st['length_m']:.4f} m with {lap} m end laps")
    bands = {}
    for sh, st in zip(sheets, strips):
        bands.setdefault(st["band"], []).append(sh)
    order = sorted(bands)
    ext = {b: (min(s[1] for s in bands[b]), max(s[3] for s in bands[b])) for b in order}
    for a, b in zip(order, order[1:]):
        ov = ext[a][1] - ext[b][0]
        if ov < lap - tol:
            fails.append(f"SIDE_LAP: bands {a}/{b} overlap {ov:.4f} m < {lap} m")
    union = surf
    for b in order:
        ss = sorted(bands[b], key=lambda s: s[0])
        for i in range(len(ss)):
            for j in range(i + 1, len(ss)):
                p, q = ss[i], ss[j]
                ov = min(p[2], q[2]) - max(p[0], q[0])
                if ov < -tol or ov >= lap - tol:
                    continue
                xj = (max(p[0], q[0]) + min(p[2], q[2])) / 2.0
                lo, hi = max(p[1], q[1]), min(p[3], q[3])
                if hi - lo <= tol:
                    continue
                others = unary_union([box(o[0], o[1], o[2], o[3]) for o in sheets if o is not p and o is not q])
                seam = union.intersection(LineString([(xj, lo), (xj, hi)]))
                if not others.is_empty:
                    seam = seam.difference(others)         # a seam under a third sheet (a band's side lap) is closed
                if seam.length > GRID_M:
                    fails.append(f"END_LAP: band {b} joint at {xj:.3f} m laps {max(ov, 0.0):.4f} m < {lap} m over "
                                 f"{seam.length:.3f} m of surface")
    h = spec["upturn_h_m"]
    y0, y1 = floor.bounds[1] - h, floor.bounds[3] + h     # the floor and its upturn across (a mitred corner tip
    D = y1 - y0                                           # beyond it is a corner patch, proved by the residue)
    need = max(1, math.ceil((D - lap) / (W - lap) - 1e-9)) if D > W + tol else 1
    if len(order) < need:
        fails.append(f"BAND_COUNT: {len(order)} bands < {need} needed to span {D:.4f} m")
    if order and (ext[order[0]][0] > y0 + GRID_M or ext[order[-1]][1] < y1 - GRID_M):
        fails.append(f"BANDS_SHORT_ACROSS: bands {ext[order[0]][0]:.4f}..{ext[order[-1]][1]:.4f}, surface "
                     f"{y0:.4f}..{y1:.4f}")
    proj = []
    for b in order:
        lo, hi = ext[b]
        need_iv = _intervals(surf.intersection(box(surf.bounds[0] - 1, lo, surf.bounds[2] + 1, hi)))
        have_iv = _intervals(unary_union([box(s[0], s[1], s[2], s[3]) for s in bands[b]]))
        proj.append({"band": b, "projection_m": _r(sum(q - p for p, q in need_iv), 4),
                     "laid_m": _r(sum(q - p for p, q in have_iv), 4), "short_of_projection_m": _r(_gap(need_iv, have_iv), 4)})
    return fails, {"bands": len(order), "bands_needed": need, "extent_across_m": _r(D, 4), "projection": proj}


def prove(p, sheets, strips, patches, spec, *, v3_required_m2=None):
    """the proof of one layout. p: the outline in the strip frame (strips along x); sheets: [(x0, s0, x1, s1, kind)];
    strips: the layout's strip records (same order); patches: the layout's declared patches (box in the strip frame)."""
    h = spec["upturn_h_m"]
    srf = surface(list(p.exterior.coords), [list(r.coords) for r in p.interiors], h)
    req = shapely.set_precision(srf["union"], GRID_M)
    laid = shapely.set_precision(unary_union([box(s[0], s[1], s[2], s[3]) for s in sheets]), GRID_M)
    R = shapely.difference(req, laid, grid_size=GRID_M)
    fails, warns = [], []
    if v3_required_m2 is not None and abs(srf["union"].area - v3_required_m2) > 1e-3:
        fails.append(f"SURFACE_MISMATCH: built {srf['union'].area:.4f} m2, MEMBRANE_FOLD_V3 {v3_required_m2:.4f} m2")
    sf, info = _sheet_checks(sheets, strips, spec, srf["union"], srf["floor"])
    fails += sf
    numerical, residues = 0.0, []
    pboxes = [box(*q["box"]).buffer(2 * GRID_M, join_style="mitre") for q in patches]
    raw = None
    for r in _parts(R):
        if r.area > NUMERIC_M2 and r.area <= NUMERIC_M2 + r.length * GRID_M:
            # at the limit only by the snapping: the piece's unsnapped residue decides (engine limit, raw geometry)
            if raw is None:
                raw = srf["union"].difference(unary_union([box(s[0], s[1], s[2], s[3]) for s in sheets]))
            if raw.intersection(r.buffer(GRID_M, join_style="mitre")).area <= NUMERIC_M2:
                numerical += r.area
                continue
        if r.area <= NUMERIC_M2:
            numerical += r.area
            continue
        hit = [i for i, pb in enumerate(pboxes) if pb.intersection(r).area >= r.area - max(r.length * GRID_M, 1e-7)]
        rb = r.bounds
        row = {"m2": _r(r.area), "box": tuple(_r(v, 4) for v in rb),
               "along_m": _r(rb[2] - rb[0], 4), "across_m": _r(rb[3] - rb[1], 4), "patch": hit[0] if hit else None}
        if not hit:
            fails.append(f"UNDECLARED_RESIDUE: {r.area:.4f} m2 at {row['box']} ({row['along_m']} x {row['across_m']} m)")
        residues.append(row)
    # the declared patches against the unsnapped residue (exact: a patch's m2 is the engine's own exact piece)
    if raw is None:
        raw = srf["union"].difference(unary_union([box(s[0], s[1], s[2], s[3]) for s in sheets]))
    raw_parts = [g for g in _parts(raw) if g.area > NUMERIC_M2]
    raw_used = [0.0] * len(patches)
    raw_box = [None] * len(patches)
    for g in raw_parts:
        hit = [i for i, pb in enumerate(pboxes) if pb.intersection(g).area >= g.area - 1e-7]
        # a piece the engine split into several patches (MEMBRANE_FOLD_V4 cleaning) is shared by their boxes
        share = [(hit[0], g)] if hit else [(i, pb.intersection(g)) for i, pb in enumerate(pboxes)
                                           if pb.intersection(g).area > 1e-9]
        for i, k in share:
            raw_used[i] += k.area
            gb = k.bounds
            ob = raw_box[i]
            raw_box[i] = gb if ob is None else (min(ob[0], gb[0]), min(ob[1], gb[1]), max(ob[2], gb[2]),
                                                max(ob[3], gb[3]))
    pat = []
    for i, q in enumerate(patches):
        qb, bb = q["box"], raw_box[i]
        st = "MATCHED"
        if bb is None:
            st = "PATCH_WITHOUT_RESIDUE" if q["m2"] > NUMERIC_M2 else "NUMERICAL"
            if st == "PATCH_WITHOUT_RESIDUE":
                fails.append(f"PATCH_WITHOUT_RESIDUE: patch {i} {q['m2']} m2 at {qb}")
        elif abs(raw_used[i] - q["m2"]) > NUMERIC_M2:
            st = "PATCH_AREA_MISMATCH"
            fails.append(f"PATCH_AREA_MISMATCH: patch {i} declares {q['m2']} m2, residue {raw_used[i]:.6f} m2")
        elif ((qb[2] - qb[0]) - (bb[2] - bb[0]) > 2 * GRID_M or (qb[3] - qb[1]) - (bb[3] - bb[1]) > 2 * GRID_M):
            st = "PATCH_BOX_LARGER_THAN_RESIDUE"
            warns.append(f"PATCH_BOX_LARGER_THAN_RESIDUE: patch {i} cut {qb[2] - qb[0]:.4f} x {qb[3] - qb[1]:.4f} m for "
                         f"a residue {bb[2] - bb[0]:.4f} x {bb[3] - bb[1]:.4f} m (the roll counts cut it at the box size)")
        pat.append({"patch": i, "kind": q.get("kind"), "declared_m2": q["m2"], "residue_m2": _r(raw_used[i]),
                    "along_m": q.get("along_m"), "across_m": q.get("across_m"), "state": st})
    if srf["repaired_after_turn"]:
        warns.append("OUTLINE_INVALID_AFTER_TURN: the outline turned into this layout frame crosses itself by "
                     "rotation noise (an opening touching the outline); repaired here with its area kept, the fold "
                     "used it as it was")
    dn = srf["double_need"]
    verdict = FAILED if fails else (PROVEN_DETAIL if dn else PROVEN)
    return {"method": METHOD_ID, "verdict": verdict, "failures": fails, "warnings": warns, "grid_m": GRID_M,
            "surface_m2": _r(srf["union"].area, 4), "floor_m2": _r(srf["floor"].area, 4),
            "laid_m2": _r(laid.area, 4), "residue_m2": _r(R.area), "numerical_m2": _r(numerical),
            "residues": residues, "patches": pat, "declared_patch_m2": _r(sum(q["m2"] for q in patches)),
            "double_need": dn, "double_need_m2": {k: _r(sum(x["m2"] for x in dn if x["kind"] == k)) for k in
                                                   (ADJACENT, OPPOSED)},
            "convex_corners": len(srf["corners"]), **info}


# ------------------------------------------------------------------------------------------------ a whole fold
def _frame_check(polygon, holes, unit_m, p, back, to_drawing):
    """the engine's layout frame checked, not trusted: every corner of p mapped back lies on a corner of the outline as
    given (within the grid, drawing units x unit_m) and vice versa; the areas agree."""
    given = [F2.clean_ring(polygon, unit_m)[0]] + [F2.clean_ring(x, unit_m)[0] for x in holes or ()]
    gpts = [(x, y) for rg in given for (x, y) in rg]
    mapped = []
    for rg in [p.exterior] + list(p.interiors):
        for x, y in _ring(rg.coords):
            rx, ry = back(x, y)
            dx, dy = to_drawing(rx, ry)
            mapped.append((dx * unit_m, dy * unit_m))
    far = max((min(math.dist(m, g) for g in gpts) for m in mapped), default=0.0)
    far2 = max((min(math.dist(g, m) for m in mapped) for g in gpts), default=0.0)
    ga = Polygon(given[0], [x for x in given[1:] if len(x) >= 3]).area
    ok = far <= GRID_M and far2 <= GRID_M and abs(ga - p.area) <= 1e-6 * max(1.0, ga)
    return ok, {"max_corner_offset_m": _r(max(far, far2), 9), "area_given_m2": _r(ga), "area_layout_m2": _r(p.area)}


def prove_fold(polygon, *, holes=(), unit_m=1.0, spec=None, fold=None):
    """MEMBRANE_FOLD_V5.fold (computed here unless given) proved layout by layout. -> dict with "v3" (the four layouts
    ARCH_TAKEOFF_V2.12 / V2.13 read), "v4" (every wall-frame layout; the first four are the V3 frame), the layouts chosen
    by MEMBRANE_CUTTING_PLAN_V2 / ARCH_TAKEOFF_V2.13 and by MEMBRANE_FOLD_V5, and the overall verdict."""
    from engine.source import arch_v213 as AV
    from engine.source import membrane_fold_v4 as F4
    from engine.source import membrane_fold_v5 as F5
    spec = dict(F3.DEFAULT, **(spec or {}))
    f = fold if fold is not None else F5.fold(polygon, holes=holes, unit_m=unit_m, spec=spec)
    sp = f["spec"]
    frs = f["frames_v4"]

    def frame_of(fi):
        if fi == 0:
            return F3._frame(polygon, holes, unit_m)
        return F4._frame_at(polygon, holes, unit_m, frs[fi]["frame_deg"])

    def one(x, fi):
        pf, td = frame_of(fi)
        p = F3._to_layout(pf, x["direction"], x["start"])
        ok, fc = _frame_check(polygon, holes, unit_m, p, F3._back(x["direction"], x["start"]), td)
        pr = prove(p, x["_sheets"], x["strips"], x["patches"], sp, v3_required_m2=x["required_m2"])
        if not ok:
            pr["failures"].append(f"FRAME: the layout outline does not map back onto the outline ({fc})")
            pr["verdict"] = FAILED
        pr["frame"] = fc
        pr.update(layout=f"{x['direction']} / {x['start']}", rolls_by_basis=dict(x["rolls_by_basis"]),
                  patches_declared=len(x["patches"]), upturn_only_strips=x["upturn_strips"])
        return pr

    v3 = [one(x, 0) for x in f["layouts_v3"]]
    v4 = []
    for x in f["layouts_v4"]:
        pr = one(x, x["frame"])
        pr.update(index=x["index"], name=x["name"], frame_deg=x["frame_deg"])
        v4.append(pr)
    cp = AV.purchase(f)
    pick213 = next((i for i, x in enumerate(f["layouts_v3"]) if x["direction"] == cp.get("direction")
                    and x["start"] == cp.get("start")), None)
    ch5 = f["choice_v5"]
    pick5 = ch5["q58_a"]["layout"]
    worst = FAILED if any(x["verdict"] == FAILED for x in v3 + v4) else (
        PROVEN_DETAIL if any(x["verdict"] == PROVEN_DETAIL for x in v3 + v4) else PROVEN)
    return {"method": METHOD_ID, "floor_m2": f["floor_m2"], "verdict": worst, "v3": v3, "v4": v4,
            "chosen_v213": {"layout": pick213, "state": cp.get("state"), "rolls": cp.get("rolls"),
                            "rolls_bounded": cp.get("rolls_bounded"),
                            "verdict": v3[pick213]["verdict"] if pick213 is not None else None},
            "chosen_v5": {"layout": pick5, "state": ch5["state"],
                          "rolls_by_reading": {b: x["rolls"] for b, x in ch5["by_reading"].items()},
                          "verdict": v4[pick5]["verdict"]},
            "spec": dict(sp)}


def policy_record():
    return {"method": METHOD_ID, "rules": list(RULES), "grid_m": GRID_M,
            "numerical_m2": {"value": NUMERIC_M2, "source": "MEMBRANE_FOLD_V2.COVER_TOL_M2"},
            "replaces_nothing": "a checker piece: read by no method; changes no quantity"}
