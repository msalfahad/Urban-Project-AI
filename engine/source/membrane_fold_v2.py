"""MEMBRANE FOLD V2 (task T-076, opt-in; no released method or quantity changed) - the owner's strip method for the
membrane to BUY, computed on real room outlines (any rotation, mirror, units, collinear points, L / U shapes), with
the BOQ upturn line on the walls only and one doorway transition line per door (owner Q-35 answer C, 2026-10-19).

Why a new piece: wp_install.continuous_fold (V2.6, frozen in place) computes the owner's method only for a 4-point
axis-parallel rectangle whose doorway depth equals the upturn height; on Alsenan it is computed for none of the 14 wet
areas (6 - 24 ring points, 2 rooms at 45 degrees, 0.12 - 0.15 m doorways). This module is a new version beside it.

The method (owner Q-30 worked example, his words in short; Q-35 C: "strips 0.20 m longer at both ends whatever sits in
the wall"; UP-WP-001 roll 1.00 x 10.00 m, UP-WP-002 lap 0.10 m, UP-WP-003 upturn 0.20 m):
    across the span:  the first strip covers W - h of floor, each next full strip W - lap, the last strip is cut to
                      (remaining floor + lap + h); a span with span + 2h <= W takes one strip of span + 2h
                      (= wp_install.continuous_fold's count n = ceil((span + 2h - W) / (W - lap)) + 1)
    along the strip:  the strip is as long as the floor it covers + h + h; a band of the floor that falls apart into
                      separate pieces (a U shape, a pier) gives one strip per piece (the room is split into the
                      rectangles the strips actually cover; T-074 ran one strip over the whole band)
    splice:           a strip longer than the roll is spliced with the end lap (lap) as wp_install does
    cut m2           = sum of strip width x strip length (the owner's "membrane cut", his 16.28 m2)
    roll length used = sum of strip lengths: a strip narrower than the roll still uses its length of the 1.00 m roll
    rolls if alone   = the strips packed into whole rolls by length (membrane_layout.pack_rolls), never net area / roll
                       area (UP-WP-001); the owner's own count ceil(cut / roll area) is shown beside it and a
                      difference is flagged, never hidden
Both strip directions (along the room's longest wall, and across it) are always reported; the module selects
neither (Lead note on Q-30). Each direction is laid from the lower wall of the room frame and, beside it, from the
opposite wall (a notch can fall in another band); a room with walls in more than one frame (a 45 degree wall) also
shows the strips of its other wall frames (walls of at least 1 m and 10 % of the boundary, at most 3; the short
chords of a curved wall are not frames). The project rolls are packed per direction set, all shown.

Coverage check (no assumption is taken as proof): the developed surface = the floor + a flap h wide outward of every
boundary edge (wall, door, open edge alike: Q-35 C) must lie inside the strips' sheets laid flat. What is not
covered (a slanted wall the straight strip end reaches only at h x cos, an inner wall parallel to the strips with less
than h of sheet beyond it) is reported in m2 as UPTURN_SHORTFALL, never silently 0 and never patched by an assumed
piece. Internal (reflex) corners are counted (each needs a corner piece by detail, outside the owner's method).

The BOQ lines of the area (Q-35 C, Q-37 A):
    FIN.WP.UPTURN       walls only: WALL + COLUMN + WINDOW_THRESHOLD lm x h (UP-WP-003 eligible roles)
    doorway transitions one line per door (by opening id; a door edge without an id is listed per room and flagged)
    thresholds          open edges / passages (and glazing edges, UP-WP-003 "by detail") as their own lm lines
A role summary that is missing makes the upturn line HELD (None, never 0); the strips and the rolls do not depend on it.

    clean_ring(ring, unit_m)              -> the ring in metres without repeated and collinear points
    room_frame(ring)                      -> the angle (degrees) of the room's longest wall, mod 180
    strips(poly, h, W, lap, along)        -> the strips of one direction in the room's own frame
    fold(polygon, ...)                    -> both directions, the coverage check, the counts, the flags
    boq_lines(roles_lm, doors, h)         -> walls-only upturn, door transitions, thresholds
    area(...)                             -> one membrane-table row (fold + lines)
    project(rows, ...)                    -> per-area rows, per-floor and project sums, rolls packed per direction set
Project-agnostic. shapely 2 for the band intersections (requirements.txt)."""

from __future__ import annotations

import math

from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.ops import unary_union

from engine.source import membrane_layout as ML

METHOD_ID = "MEMBRANE_FOLD_V2"
EPS = 1e-9
COLLINEAR_TOL_M = 0.001          # a vertex within 1 mm of the line through its neighbours is collinear
DUP_TOL_M = 0.0005               # vertices closer than 0.5 mm are one vertex
COVER_TOL_M2 = 1e-4              # uncovered area below 1 cm2 is numerical
FRAME_MIN_WALL_M, FRAME_MIN_SHARE, FRAME_MAX_OTHER = 1.0, 0.10, 3   # another wall frame is shown when its walls are at
#                                  least 1 m and 10 % of the boundary (the chords of a curved wall are not frames), at most 3
ALONG_LONG, ACROSS = "ALONG_LONGEST_WALL", "ACROSS_LONGEST_WALL"
DIRECTIONS = (ALONG_LONG, ACROSS)
ELIGIBLE = ("wall", "column", "window_threshold")
THRESHOLD_ROLES = ("other", "passage", "glazing_edge", "zone_line")
ROLE_ALIASES = {"glazing": "glazing_edge"}      # the typed ring (wp_geometry) says GLAZING, the room runs glazing_edge
SLIVER_LM = 0.01                                 # a threshold run under 1 cm is a drawing sliver, listed, not a line
RULES = ("UP-WP-001", "UP-WP-002", "UP-WP-003", "UP-WP-005", "UP-WP-LAY-001", "UP-WP-DOOR-001", "UP-QTY-STATUS-001",
         "owner Q-30 (kitchen worked example)", "owner Q-35 C", "owner Q-37 A", "owner Q-24 (roofs like a bathroom)")
DEFAULT = {"roll_width_m": 1.00, "roll_length_m": 10.00, "lap_m": 0.10, "upturn_h_m": 0.20}


class FoldError(ValueError):
    pass


def _r(x, n=4):
    return None if x is None else round(x + 0.0, n)


# ------------------------------------------------------------------------------------------------ geometry
def clean_ring(ring, unit_m=1.0):
    """the ring in metres: closing point, repeated points (DUP_TOL_M) and collinear points (COLLINEAR_TOL_M from the
    line through the kept neighbours) removed, repeated until stable. -> (points, removed count)."""
    pts = [(float(p[0]) * unit_m, float(p[1]) * unit_m) for p in ring]
    if len(pts) > 1 and math.dist(pts[0], pts[-1]) <= DUP_TOL_M:
        pts = pts[:-1]
    n0 = len(pts)
    changed = True
    while changed and len(pts) > 3:
        changed = False
        out = []
        for p in pts:
            if out and math.dist(p, out[-1]) <= DUP_TOL_M:
                changed = True
                continue
            out.append(p)
        if len(out) > 1 and math.dist(out[0], out[-1]) <= DUP_TOL_M:
            out.pop()
            changed = True
        pts = out
        k = 0
        while k < len(pts) and len(pts) > 3:
            a, b, c = pts[k - 1], pts[k], pts[(k + 1) % len(pts)]
            L = math.dist(a, c)
            if L > EPS:
                d = abs((c[0] - a[0]) * (b[1] - a[1]) - (c[1] - a[1]) * (b[0] - a[0])) / L
                between = ((b[0] - a[0]) * (c[0] - a[0]) + (b[1] - a[1]) * (c[1] - a[1])) / (L * L)
                if d <= COLLINEAR_TOL_M and -EPS <= between <= 1 + EPS:
                    pts.pop(k)
                    changed = True
                    continue
            k += 1
    return pts, n0 - len(pts)


def room_frame(ring):
    """the angle of the longest edge (degrees, in [0, 180)): turning the room by minus this angle lays its longest
    wall along x (the room's own frame). Ties go to the first edge."""
    best, ang = -1.0, 0.0
    n = len(ring)
    for i in range(n):
        p, q = ring[i], ring[(i + 1) % n]
        L = math.dist(p, q)
        if L > best + 1e-6:
            best, ang = L, math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
    a = ang % 180.0
    return 0.0 if a > 180.0 - 1e-7 else a


def _orthogonal(poly):
    ring = list(poly.exterior.coords)[:-1]
    for h in poly.interiors:
        ring += list(h.coords)[:-1]
    n = len(ring)
    return all(abs(ring[i][0] - ring[(i + 1) % n][0]) <= 1e-6 or abs(ring[i][1] - ring[(i + 1) % n][1]) <= 1e-6
               for i in range(n))


def _parts(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g] if g.area > EPS else []
    return [p for p in getattr(g, "geoms", ()) if isinstance(p, Polygon) and p.area > EPS]


def _bands(span, h, W, lap):
    """floor intervals [a, b] across the span and each strip's width and sheet extent [s0, s1] (the owner's count)."""
    if span + 2 * h <= W + EPS:
        return [{"a": 0.0, "b": span, "w": span + 2 * h, "s0": -h, "s1": span + h}]
    D = span + 2 * h
    n = math.ceil((D - W) / (W - lap) - EPS) + 1
    out = []
    for i in range(n):
        s0 = -h + i * (W - lap)
        s1 = s0 + W if i < n - 1 else span + h
        a = 0.0 if i == 0 else s0 + lap
        b = min(s1, span) if i == n - 1 else min(s0 + W, span)
        out.append({"a": a, "b": b, "w": s1 - s0, "s0": s0, "s1": s1})
    return out


def strips(poly, h, W, L, lap):
    """the strips of one direction: poly in the strip frame (strips run along x, the span is across y). -> list of
    strips {band, width_m, floor_from_m, floor_to_m, length_m, x0, x1, s0, s1, pieces, piece_lengths_m}."""
    x0, y0, x1, y1 = poly.bounds
    span = y1 - y0
    out = []
    for i, bd in enumerate(_bands(span, h, W, lap)):
        a, b = bd["a"], bd["b"]
        if b - a <= 1e-6:                     # an upturn-only strip at the far wall: the floor its sheet lies over
            a, b = max(0.0, bd["s0"]), span
        if b - a <= 1e-6:
            a = max(0.0, span - 1e-3)
        cut = poly.intersection(box(x0 - 1.0, y0 + a, x1 + 1.0, y0 + b))
        comps = sorted(_parts(cut), key=lambda p: p.bounds[0])
        if not comps:
            raise FoldError(f"band {i} covers no floor")
        # pieces whose x-extents touch or overlap are one strip (a strip is one straight piece of sheet)
        runs = []
        for c in comps:
            cx0, _, cx1, _ = c.bounds
            if runs and cx0 <= runs[-1][1] + 2 * h + EPS:
                runs[-1][1] = max(runs[-1][1], cx1)
            else:
                runs.append([cx0, cx1])
        for (sx0, sx1) in runs:
            Ls = (sx1 - sx0) + 2 * h
            k = 1 if Ls <= L + EPS else math.ceil((Ls - L) / (L - lap) - EPS) + 1
            lens = [L] * (k - 1) + [Ls - (k - 1) * (L - lap)] if k > 1 else [Ls]
            out.append({"band": i, "width_m": _r(bd["w"], 6), "floor_from_m": _r(a, 6), "floor_to_m": _r(b, 6),
                        "length_m": _r(Ls, 6), "x0": sx0 - h, "x1": sx1 + h, "s0": y0 + bd["s0"],
                        "s1": y0 + bd["s1"], "pieces": k, "piece_lengths_m": [_r(x, 6) for x in lens]})
    return out


def _flaps(poly, h, holes=False):
    """the developed surface beyond the floor: one h-wide rectangle outward of the floor at every edge of the outer
    ring (holes=False) or of the obstruction / opening rings (holes=True: the flaps lie inside each hole), no corner
    squares."""
    out = []
    rings = [list(r.coords) for r in poly.interiors] if holes else [list(poly.exterior.coords)]
    for ring in rings:
        pts = ring[:-1]
        sa = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                 for i in range(len(pts)))
        sgn = 1.0 if sa > 0 else -1.0                     # the right of the ring's own direction is outside it
        if holes:
            sgn = -sgn                                    # a hole: the floor is outside the ring, its flap inside
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            d = (q[0] - p[0], q[1] - p[1])
            Ld = math.hypot(*d)
            if Ld <= EPS:
                continue
            nx, ny = d[1] / Ld * sgn, -d[0] / Ld * sgn
            out.append(Polygon([p, q, (q[0] + nx * h, q[1] + ny * h), (p[0] + nx * h, p[1] + ny * h)]))
    return out


def _reflex_corners(poly):
    pts = list(poly.exterior.coords)[:-1]
    n = len(pts)
    sa = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    sgn = 1.0 if sa > 0 else -1.0
    c = 0
    for i in range(n):
        a, b, d = pts[i - 1], pts[i], pts[(i + 1) % n]
        cr = (b[0] - a[0]) * (d[1] - b[1]) - (b[1] - a[1]) * (d[0] - b[0])
        if cr * sgn < -1e-9:
            c += 1
    return c


def _layout(p, spec):
    """the strips of p (strip frame) started at its lower edge, their coverage check and their counts."""
    h, W, L, lap = spec["upturn_h_m"], spec["roll_width_m"], spec["roll_length_m"], spec["lap_m"]
    ss = strips(p, h, W, L, lap)
    sheets = unary_union([box(s["x0"], s["s0"], s["x1"], s["s1"]) for s in ss])
    developed = unary_union([p] + _flaps(p, h))
    short = developed.difference(sheets).area
    hole_req = sum(r.length for r in p.interiors) * h
    hole_flaps = unary_union(_flaps(p, h, holes=True)) if hole_req else None
    # each face of a hole needs its own h-wide flap; where two flaps overlap (the hole's corners, a hole narrower than
    # 2h) one piece of sheet cannot rise on both faces, so only the union of the flaps inside the sheets counts
    hole_cov = hole_flaps.intersection(sheets).area if hole_req else 0.0
    cut = sum(s["width_m"] * s["length_m"] for s in ss)
    lengths = [x for s in ss for x in s["piece_lengths_m"]]
    bins, packing = ML.pack_rolls(lengths, L)
    by_area = math.ceil(round(cut, 6) / (W * L) - EPS) if cut > EPS else 0
    rolls = len(bins)
    return {"strips": len(ss), "span_across_m": _r(p.bounds[3] - p.bounds[1]),
            "strip_list": [{k: s[k] for k in ("band", "width_m", "length_m", "floor_from_m", "floor_to_m", "pieces")}
                           for s in ss],
            "cut_m2": _r(cut), "roll_length_used_m": _r(sum(lengths)), "consumed_m2": _r(sum(lengths) * W),
            "rolls_if_alone": rolls, "rolls_by_cut_area": by_area, "roll_count_bases_differ": rolls != by_area,
            "rolls_lower_bound": packing.get("lower_bound"), "packing_proven": packing.get("proven"),
            "gross_offcut_if_alone_m2": _r(rolls * W * L - cut),
            "upturn_shortfall_m2": _r(short if short > COVER_TOL_M2 else 0.0),
            "hole_upturn": None if not hole_req else {
                "required_m2": _r(hole_req), "covered_by_strips_m2": _r(hole_cov),
                "own_pieces_m2": _r(max(hole_req - hole_cov, 0.0)),
                "note": "hole faces x h; the strips' sheet folded into the hole counts once where flaps overlap"},
            "piece_lengths_m": lengths}


def _direction(poly_frame, direction, spec):
    """one strip direction, laid from the lower edge of the room frame; the layout started from the opposite wall
    (the same direction mirrored across the span) is computed too and shown beside it, never selected."""
    p = poly_frame if direction == ALONG_LONG else affinity.rotate(poly_frame, 90.0, origin=(0.0, 0.0))
    low = _layout(p, spec)
    high = _layout(affinity.scale(p, 1.0, -1.0, origin=(0.0, 0.0)), spec)
    other = {k: high[k] for k in ("strips", "cut_m2", "roll_length_used_m", "rolls_if_alone", "rolls_by_cut_area",
                                  "upturn_shortfall_m2")}
    other["strip_list"] = [(s["width_m"], s["length_m"]) for s in high["strip_list"]]
    return dict(low, direction=direction, start="LOWER_EDGE_OF_ROOM_FRAME", other_start=other,
                start_changes_cut_m2=_r(high["cut_m2"] - low["cut_m2"]),
                start_changes_rolls=high["rolls_if_alone"] != low["rolls_if_alone"])


def _edge_directions(ring):
    """distinct wall directions (degrees mod 90, 0.5 degree classes) with their total length, longest first."""
    acc = {}
    n = len(ring)
    for i in range(n):
        p, q = ring[i], ring[(i + 1) % n]
        L = math.dist(p, q)
        a = round((math.degrees(math.atan2(q[1] - p[1], q[0] - p[0])) % 90.0) * 2) / 2 % 90.0
        acc[a] = acc.get(a, 0.0) + L
    return sorted(acc.items(), key=lambda kv: -kv[1])


def fold(polygon, *, holes=(), unit_m=1.0, spec=None):
    """the owner's strip method on one floor outline (drawing units x unit_m = metres), both directions."""
    spec = dict(DEFAULT, **(spec or {}))
    ring, removed = clean_ring(polygon, unit_m)
    if len(ring) < 3:
        raise FoldError("an outline needs at least 3 points")
    hs = [clean_ring(hh, unit_m)[0] for hh in holes or ()]
    poly = Polygon(ring, [x for x in hs if len(x) >= 3])
    if not poly.is_valid or poly.area <= EPS:
        raise FoldError("the outline is not a simple polygon with an area")
    ang = room_frame(ring)
    c = poly.centroid
    pf = affinity.rotate(poly, -ang, origin=(c.x, c.y))
    pf = affinity.translate(pf, -pf.bounds[0], -pf.bounds[1])
    shape = "RECTANGLE" if len(ring) == 4 and not hs and _orthogonal(pf) else (
        "ORTHOGONAL" if _orthogonal(pf) else "NON_ORTHOGONAL")
    opts = [_direction(pf, d, spec) for d in DIRECTIONS]
    frames = []
    if shape == "NON_ORTHOGONAL":             # the room has walls in more than one frame: every other frame shown
        per = sum(math.dist(ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring)))
        cands = [(a, lm) for a, lm in _edge_directions(ring)
                 if min(abs(a - ang % 90.0), 90.0 - abs(a - ang % 90.0)) > 0.5 and
                 lm >= max(FRAME_MIN_WALL_M, FRAME_MIN_SHARE * per)]
        for a, lm in cands[:FRAME_MAX_OTHER]:
            pa = affinity.rotate(poly, -a, origin=(c.x, c.y))
            pa = affinity.translate(pa, -pa.bounds[0], -pa.bounds[1])
            alt = []
            for d in DIRECTIONS:
                q = pa if d == ALONG_LONG else affinity.rotate(pa, 90.0, origin=(0.0, 0.0))
                lay = _layout(q, spec)
                alt.append({"strips_run_deg": _r((a + (0.0 if d == ALONG_LONG else 90.0)) % 180.0, 2),
                            **{k: lay[k] for k in ("strips", "cut_m2", "roll_length_used_m", "rolls_if_alone",
                                                   "rolls_by_cut_area", "upturn_shortfall_m2")},
                            "strip_list": [(x["width_m"], x["length_m"]) for x in lay["strip_list"]]})
            frames.append({"frame_deg_mod90": a, "walls_lm_in_frame": _r(lm), "directions": alt})
    floor = poly.area
    perim = poly.exterior.length + sum(r.length for r in poly.interiors)
    flags = []
    if removed:
        flags.append("COLLINEAR_POINTS_REMOVED")
    if ang > 1e-6:
        flags.append("ROTATED_FRAME")
    if shape == "NON_ORTHOGONAL":
        flags.append("NON_ORTHOGONAL_WALLS")
    if hs:
        flags.append("OBSTRUCTION_INSIDE")
    if any(o["upturn_shortfall_m2"] for o in opts):
        flags.append("UPTURN_SHORTFALL")
    if len({o["rolls_if_alone"] for o in opts}) > 1:
        flags.append("DIRECTION_CHANGES_ROLLS")
    if any(o["start_changes_rolls"] for o in opts):
        flags.append("START_WALL_CHANGES_ROLLS")
    if frames:
        flags.append("SEVERAL_WALL_FRAMES")
    if any(o["roll_count_bases_differ"] for o in opts):
        flags.append("ROLL_COUNT_BASES_DIFFER")
    reflex = _reflex_corners(poly)
    hole_lm = sum(r.length for r in poly.interiors)
    if reflex:
        flags.append("INTERNAL_CORNER_PIECES_BY_DETAIL")
    return {"method": METHOD_ID, "state": "COMPUTED", "shape": shape, "points_in": len(polygon),
            "points_used": len(ring), "collinear_or_repeated_removed": removed, "frame_deg": _r(ang, 4),
            "floor_m2": _r(floor), "boundary_lm": _r(perim), "upturn_h_m": spec["upturn_h_m"],
            "surface_full_boundary_m2": _r(floor + perim * spec["upturn_h_m"]),
            "internal_corners": reflex,
            "obstruction_upturn": None if not hs else {
                "lm": _r(hole_lm), "m2": _r(hole_lm * spec["upturn_h_m"]),
                "note": "faces of a column / shaft / opening inside the area: per direction, the part the strips' "
                        "sheet can fold up (hole_upturn.covered_by_strips_m2) and the part needing its own pieces "
                        "(hole_upturn.own_pieces_m2, by detail)"},
            "directions": opts, "other_frames": frames, "selected": None,
            "direction_changes_rolls": "DIRECTION_CHANGES_ROLLS" in flags, "flags": flags,
            "spec": {k: spec[k] for k in DEFAULT}}


# ------------------------------------------------------------------------------------------------ BOQ lines
def boq_lines(roles_lm, doors=(), h=0.20):
    """Q-35 C: the upturn line on the walls only, one transition line per door, the open / passage / glazing edges
    as threshold lines. roles_lm: {wall, column, window_threshold, door, passage, other, glazing_edge, zone_line} in
    metres (upper-case wp_geometry roles accepted: WALL, GLAZING, ...), or
    None (then the upturn and threshold lines are HELD, never 0). doors: [{opening_id, width_m}] found on the ring."""
    if roles_lm is None:
        return {"upturn": {"state": "HELD", "lm": None, "m2": None,
                           "reason": "the boundary edges are not typed (wall / door / open): walls-only upturn unknown"},
                "door_transitions": [{"opening_id": d.get("opening_id"), "width_m": d.get("width_m")} for d in doors],
                "thresholds": None, "unidentified_door_lm": None}
    roles_lm = {ROLE_ALIASES.get(str(k).lower(), str(k).lower()): v for k, v in roles_lm.items()}
    walls = sum(roles_lm.get(k) or 0.0 for k in ELIGIBLE)
    door_lm = roles_lm.get("door") or 0.0
    listed = sum(d.get("width_m") or 0.0 for d in doors)
    unid = door_lm - listed
    tr = [{"opening_id": d.get("opening_id"), "width_m": _r(d.get("width_m")), "line": "FIN.WP.DOORWAY_TRANSITION",
           "unit": "pcs", "qty": 1, "rule": "UP-WP-DOOR-001 / Q-35 C"} for d in doors]
    if unid > 0.02:
        tr.append({"opening_id": None, "width_m": _r(unid), "line": "FIN.WP.DOORWAY_TRANSITION", "unit": "pcs",
                   "qty": None, "flag": "DOOR_EDGE_WITHOUT_OPENING_ID",
                   "note": "a door edge on the ring that the opening census did not list: the count is held (it may be "
                           "the same door as a neighbour's edge)"})
    th = [{"role": k, "lm": _r(roles_lm[k]), "line": "FIN.WP.THRESHOLD",
           "rule": "UP-WP-003 (by detail)" + ("; Q-37 A" if k == "other" else "")}
          for k in THRESHOLD_ROLES if (roles_lm.get(k) or 0.0) >= SLIVER_LM]
    slivers = {k: _r(roles_lm[k], 6) for k in THRESHOLD_ROLES if 1e-9 < (roles_lm.get(k) or 0.0) < SLIVER_LM}
    return {"upturn": {"state": "MEASURED", "lm": _r(walls), "m2": _r(walls * h), "roles": list(ELIGIBLE),
                       "rule": "UP-WP-003 eligible roles; Q-35 C walls only"},
            "door_transitions": tr, "thresholds": th, "unidentified_door_lm": _r(max(unid, 0.0)),
            "sliver_lm": slivers}


def area(*, floor, room_id, polygon, holes=(), unit_m=1.0, roles_lm=None, doors=(), name=None, spec=None):
    """one row of the membrane table: the strips of both directions and the area's BOQ lines."""
    spec = dict(DEFAULT, **(spec or {}))
    try:
        f = fold(polygon, holes=holes, unit_m=unit_m, spec=spec)
    except FoldError as ex:
        return {"floor": floor, "room_id": room_id, "name": name, "state": "HELD", "reason": str(ex), "fold": None,
                "lines": boq_lines(None, doors, spec["upturn_h_m"])}
    return {"floor": floor, "room_id": room_id, "name": name, "state": "COMPUTED", "fold": f,
            "lines": boq_lines(roles_lm, doors, spec["upturn_h_m"])}


# ------------------------------------------------------------------------------------------------ project
def project(rows, *, roll_length_m=None):
    """per-area rows (area()), per-floor and project sums (totals only as sums of the areas, Q-35 answer), held
    rows counted beside them, rolls to buy packed for each direction set (all strips along each room's longest wall;
    all across it; each room on the direction using less roll length) - all three shown, none selected."""
    done = [r for r in rows if r["state"] == "COMPUTED"]
    held = [r for r in rows if r["state"] != "COMPUTED"]
    keys = set()
    for r in rows:
        k = (r["floor"], r["room_id"])
        if k in keys:
            raise FoldError(f"area {k} appears twice")
        keys.add(k)
    L = roll_length_m or (done[0]["fold"]["spec"]["roll_length_m"] if done else DEFAULT["roll_length_m"])
    sets = {}
    for name, pick in (("ALL_ALONG_LONGEST_WALL", lambda f: f["directions"][0]),
                       ("ALL_ACROSS_LONGEST_WALL", lambda f: f["directions"][1]),
                       ("EACH_ROOM_LESS_ROLL_LENGTH", lambda f: min(f["directions"], key=lambda o: (
                           o["roll_length_used_m"], o["cut_m2"], DIRECTIONS.index(o["direction"]))))):
        chosen = [pick(r["fold"]) for r in done]
        lens = [x for o in chosen for x in o["piece_lengths_m"]]
        bins, packing = ML.pack_rolls(lens, L) if lens else ([], {})
        sets[name] = {"rolls_to_buy": len(bins), "rolls_lower_bound": packing.get("lower_bound"), "rolls_if_each_area_alone": sum(o["rolls_if_alone"] for o in chosen),
                      "cut_m2": _r(sum(o["cut_m2"] for o in chosen)),
                      "roll_length_used_m": _r(sum(lens)), "packing_proven": packing.get("proven")}
    floors = {}
    for r in done:
        fl = floors.setdefault(r["floor"], {"floor": r["floor"], "areas": 0, "floor_m2": 0.0, "upturn_walls_lm": 0.0,
                                            "upturn_held": 0, "door_transitions": 0, "threshold_lm": 0.0})
        fl["areas"] += 1
        fl["floor_m2"] += r["fold"]["floor_m2"]
        up = r["lines"]["upturn"]
        if up["lm"] is None:
            fl["upturn_held"] += 1
        else:
            fl["upturn_walls_lm"] += up["lm"]
        fl["threshold_lm"] += sum(t["lm"] for t in r["lines"]["thresholds"] or ())
    doors = {}
    unid = []
    for r in done:
        for t in r["lines"]["door_transitions"]:
            if t["opening_id"] is None:
                unid.append({"floor": r["floor"], "room_id": r["room_id"], "width_m": t["width_m"]})
            else:
                doors.setdefault((r["floor"], t["opening_id"]), {"floor": r["floor"], "opening_id": t["opening_id"],
                                                                 "width_m": t["width_m"], "rooms": []})["rooms"].append(
                    r["room_id"])
    for d in doors.values():
        floors[d["floor"]]["door_transitions"] += 1
    up_held = sum(f["upturn_held"] for f in floors.values())
    return {"method": METHOD_ID, "rules": list(RULES), "areas": len(done), "held": len(held),
            "held_rows": [{"floor": r["floor"], "room_id": r["room_id"], "reason": r.get("reason")} for r in held],
            "floors": [{k: (_r(v) if isinstance(v, float) else v) for k, v in floors[f].items()}
                       for f in sorted(floors, key=str)],
            "floor_m2": _r(sum(r["fold"]["floor_m2"] for r in done)),
            "upturn_walls_lm": None if up_held else _r(sum(r["lines"]["upturn"]["lm"] for r in done)),
            "upturn_held_areas": up_held,
            "door_transitions": sorted(doors.values(), key=lambda d: (str(d["floor"]), str(d["opening_id"]))),
            "door_transitions_shared": sum(1 for d in doors.values() if len(d["rooms"]) > 1),
            "door_edges_without_id": unid,
            "threshold_lm": _r(sum(t["lm"] for r in done for t in r["lines"]["thresholds"] or ())),
            "direction_sets": sets, "selected": None,
            "never": ["a held area as 0", "rolls from net area / roll area", "one strip direction picked silently",
                      "an uncovered upturn as 0 or as an assumed patch"]}


def policy_record():
    return {"method": METHOD_ID, "rules": list(RULES), "defaults": dict(DEFAULT),
            "replaces_nothing": "opt-in beside wp_install.continuous_fold (V2.6); no released method reads it"}
