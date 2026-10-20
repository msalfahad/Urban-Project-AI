"""STAIR FLOOR RESIDUE V1 - the floor finish of a room face that holds stair flights, a stair well or a stair opening.

    face_residue(face, *, voids, segments, arcs, unit_m, floor_points=()) -> record

Opt-in, not wired: no method version reads it yet (ARCH_TAKEOFF_V2.9 .. V2.12 and arch_floor.split_face are untouched).
It answers, for one face, which m2 are floor finish, which are stair and which are open to below, each with its evidence:

1. TREADS, exact. The tread quads of all flights drawn inside the face are UNITED (shapely, GEOS) and intersected with
   the face exactly. A winder quad that is not convex and two flights whose quads overlap are then counted once.
   (arch_floor._treads clips each quad on its own with plane_poly.region_area_in_convex: wrong on a non-convex quad,
   and an overlap of two flights is deducted twice.) Flights seen through the opening (drawn_on_plan_below) are the
   stair of the plan below: deducted here (no floor at this level), counted on the plan below, never twice.
2. VOID, exact: the face inside the outlined void windows (open to below, never floor).
3. RESIDUE CELLS (only where the stair passes through this slab: the face has an outlined void, or a flight that
   continues a stair of the plan below - drawn_on_plan_below / stacked_over). The face is cut by the drawn linework of
   the stair (every segment / arc on the layers the flights were read from, the void window, the tread quads and the
   face boundary). A cell that is not tread and not void, is reached from a tread or the void through cells of the same
   kind, and is not floor (the largest free cell, and every cell holding a given floor point such as a door) is
   enclosed by the stair's own drawing: it is not reachable floor.
       VOID_RESIDUE      a residue piece that touches the void: inside the stair opening (slab edge / balustrade line
                         to the void outline); never floor (UP-QTY-STATUS-001: listed as its own line, not hidden)
       STAIR_FOOTPRINT   any other residue piece: landing, well gap or stair edge between the stair's own lines; it
                         takes the stair line, never the room's porcelain (UP-STAIR-005: marble stair n porcelain = 0)
   On a storey where the stair does not pass through the slab (the lowest plan: floor under and around a rising stair)
   the cells are listed as NOT_ASSESSED and nothing is deducted.
4. FOOT OF A FLIGHT (HELD). Two straight flights of one stair side by side (a dog-leg) usually end on one line. When
   one flight's last tread line stops short of its neighbour's end, the strip between them (the flight's width x the
   difference) is either the flight's foot or the floor it arrives on; when that strip is open to the floor cell the
   drawing does not settle it, so it is HELD as a range (low = deducted, high = floor), never a number and never 0.
5. MISSING OUTLINE (HELD). A flight without tread quads or a void referenced by the face without an outline: the floor
   of that face is HELD (net None) with the reason; it is never released and never 0.

Rules: UP-STAIR-002 (stair geometry from the drawing), UP-STAIR-005 (a landing is marble, never also porcelain),
UP-QTY-STATUS-001 (released / held / unsupported; missing never 0), arch_floor FLOOR AREA RECONCILIATION (every m2 in
one category or an explicit residual), owner Q-56 A (the floor pieces keep their own rows; this piece only removes
what is not floor). Project-agnostic: no layer name, room name, size or coordinate of any project; layers are taken
from the flights the engine detected. The only tolerances are numeric (drawing noise), named below.
"""

from __future__ import annotations

import math

from shapely import set_precision
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import polygonize, unary_union

POLICY_ID = "STAIR_FLOOR_RESIDUE_V1"
GRID_M = 1e-4            # 0.1 mm: coordinates snapped to this grid before the linework is noded (drawing noise only)
AREA_EPS_M2 = 1e-4       # pieces below this are noise, not reported
TOUCH_M = 1e-3           # two cells touch when they share at least this length of boundary
EXTEND_M = 2e-3          # each drawn stair line is extended 2 mm at both ends before noding, so a line drawn to a wall
                         # or to another line closes its cell under rotation / snapping noise (the overhang is a dangle)
ARC_STEPS_PER_RAD = 16   # arc discretisation (about 3.6 deg per chord)
RULES = ("UP-STAIR-002", "UP-STAIR-005", "UP-QTY-STATUS-001", "ARCH_FLOOR_RECONCILIATION_V1", "OWNER-Q-56-A")


def _poly(points, u):
    p = Polygon([(x * u, y * u) for x, y in points])
    return p if p.is_valid else p.buffer(0)


def _face_geom(face, u):
    if face.get("polygon_m"):
        outer = Polygon(face["polygon_m"])
        holes = [Polygon(h) for h in face.get("hole_polygons_m") or ()]
    else:
        outer = _poly(face["polygon"], u)
        holes = [_poly(h, u) for h in face.get("hole_polygons") or ()]
    g = outer if outer.is_valid else outer.buffer(0)
    for h in holes:
        g = g.difference(h if h.is_valid else h.buffer(0))
    return g


def _area(g):
    return 0.0 if g is None or g.is_empty else float(g.area)


def _polys(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    if isinstance(g, MultiPolygon):
        return list(g.geoms)
    return [x for x in getattr(g, "geoms", ()) if isinstance(x, Polygon) and x.area > 0]


def _arc_points(a, u):
    cx, cy = a["c"]
    r = a["r"]
    ang = [math.atan2(p[1] - cy, p[0] - cx) for p in (a["s"], a.get("m") or a["s"], a["e"])]
    t0, tm, t1 = ang
    two = 2 * math.pi
    # sweep from s to e through m (counter-clockwise if m lies on the ccw way, else clockwise)
    ccw = (t1 - t0) % two
    sweep = ccw if (tm - t0) % two <= ccw else -((t0 - t1) % two)
    n = max(2, int(abs(sweep) * ARC_STEPS_PER_RAD) + 1)
    return [((cx + r * math.cos(t0 + sweep * k / n)) * u, (cy + r * math.sin(t0 + sweep * k / n)) * u)
            for k in range(n + 1)]


def _flight_axis(fl, u):
    """(unit axis along the run, unit across, run interval, across interval) of a straight flight, in metres."""
    quads = [[(x * u, y * u) for x, y in q] for q in fl["tread_quads"]]
    cen = [(sum(p[0] for p in q) / len(q), sum(p[1] for p in q) / len(q)) for q in quads]
    dx, dy = cen[-1][0] - cen[0][0], cen[-1][1] - cen[0][1]
    n = math.hypot(dx, dy)
    if n <= 0:
        return None
    ax = (dx / n, dy / n)
    cr = (-ax[1], ax[0])
    pts = [p for q in quads for p in q]
    run = [p[0] * ax[0] + p[1] * ax[1] for p in pts]
    acr = [p[0] * cr[0] + p[1] * cr[1] for p in pts]
    return ax, cr, (min(run), max(run)), (min(acr), max(acr))


def _extended(a, b):
    d = math.dist(a, b)
    if d <= 0:
        return LineString([a, b])
    ex, ey = (b[0] - a[0]) / d * EXTEND_M, (b[1] - a[1]) / d * EXTEND_M
    return LineString([(a[0] - ex, a[1] - ey), (b[0] + ex, b[1] + ey)])


def _strip(ax, cr, run_iv, acr_iv):
    pts = []
    for r, c in ((run_iv[0], acr_iv[0]), (run_iv[1], acr_iv[0]), (run_iv[1], acr_iv[1]), (run_iv[0], acr_iv[1])):
        pts.append((ax[0] * r + cr[0] * c, ax[1] * r + cr[1] * c))
    return Polygon(pts)


def _touch(a, b):
    """a and b share at least TOUCH_M of boundary (within the snapping noise)."""
    if a.is_empty or b.is_empty or a.distance(b) > GRID_M * 5:
        return False
    return a.boundary.intersection(b.buffer(GRID_M * 5)).length >= TOUCH_M


def face_residue(face, *, voids=(), segments=(), arcs=(), unit_m=1.0, floor_points=()):
    """-> record for one face. face: an arch_rooms face / room (polygon or polygon_m, hole polygons, face_id,
    voids [{void_id}], symbols_inside.stair_flights [{flight_id, layer, also_drawn_on, kind, tread_quads,
    drawn_on_plan_below, stacked_over}]); voids: [{void_id, corners}] in drawing units (the outlined void windows of
    this plan); segments: [{layer, a, b}] and arcs: [{layer, c, r, s, m, e}] of the plan in drawing units;
    floor_points: points known to be floor (door / passage centres, drawing units)."""
    u = unit_m
    F = set_precision(_face_geom(face, u), GRID_M)
    flights = list((face.get("symbols_inside") or {}).get("stair_flights") or ())
    rec = {"policy": POLICY_ID, "face_id": face.get("face_id"), "room_id": face.get("room_id"),
           "face_m2": round(_area(F), 6), "rules": list(RULES), "pieces": [], "held": [], "not_assessed": []}
    # 5. missing outlines -> HELD, never 0
    missing = [fl.get("flight_id") for fl in flights if not fl.get("tread_quads")]
    by_id = {v.get("void_id"): v for v in voids or ()}
    vids = [v.get("void_id") for v in face.get("voids") or ()]
    missing_v = [i for i in vids if not (by_id.get(i) or {}).get("corners")]
    if missing or missing_v:
        why = []
        if missing:
            why.append("STAIR_OUTLINE_MISSING: flight(s) " + ", ".join(map(str, missing)) + " have no tread outline")
        if missing_v:
            why.append("VOID_OUTLINE_MISSING: void(s) " + ", ".join(map(str, missing_v)) + " have no outline")
        rec.update(status="HELD", floor_net_m2=None, floor_net_low_m2=None, floor_net_high_m2=None,
                   reason="; ".join(why) + " - the floor of this face cannot be separated from the stair / opening")
        return rec
    # 2. void, exact
    V = unary_union([_poly(by_id[i]["corners"], u) for i in vids]) if vids else Polygon()
    V = set_precision(V.intersection(F), GRID_M) if not V.is_empty else Polygon()
    # 1. treads, exact union (own flights first; a flight of the plan below seen through the opening counted once)
    own = [fl for fl in flights if not fl.get("drawn_on_plan_below")]
    below = [fl for fl in flights if fl.get("drawn_on_plan_below")]
    fpoly = {fl.get("flight_id"): unary_union([_poly(q, u) for q in fl["tread_quads"]]) for fl in flights}
    T_own = unary_union([fpoly[fl.get("flight_id")] for fl in own]) if own else Polygon()
    T_below = unary_union([fpoly[fl.get("flight_id")] for fl in below]) if below else Polygon()
    T_own = T_own.intersection(F).difference(V)
    T_below = T_below.intersection(F).difference(V).difference(T_own)
    quad_sum = sum(_area(_poly(q, u).intersection(F)) for fl in flights for q in fl["tread_quads"])
    T_all = unary_union([T_own, T_below])
    rec["void_m2"] = round(_area(V), 6)
    rec["stair_flights_m2"] = round(_area(T_own), 6)
    rec["stair_below_seen_m2"] = round(_area(T_below), 6)
    rec["treads_quad_sum_m2"] = round(quad_sum, 6)
    rec["treads_counted_once_m2"] = round(_area(unary_union([fpoly[k] for k in fpoly]).intersection(F)), 6)
    free = F.difference(V).difference(T_all)
    passes = (not V.is_empty) or any(fl.get("drawn_on_plan_below") or fl.get("stacked_over") for fl in flights)
    rec["scope"] = ("STAIR_PASSES_THROUGH_SLAB" if passes else
                    ("LOWEST_STOREY_NOT_ASSESSED" if flights else "NO_STAIR_NO_VOID"))
    if not flights and V.is_empty:
        a0 = face.get("area_m2") if face.get("area_m2") is not None else _area(F)
        rec.update(status="RELEASED", floor_net_m2=round(a0, 6), floor_net_low_m2=round(a0, 6),
                   floor_net_high_m2=round(a0, 6))
        return rec
    # 3. cells of the face cut by the stair's own linework
    layers = set()
    for fl in flights:
        layers.add(fl.get("layer"))
        layers.update(fl.get("also_drawn_on") or ())
    lines = [LineString(r.exterior.coords) for r in _polys(F)]
    lines += [LineString(i.coords) for r in _polys(F) for i in r.interiors]
    lines += [LineString(r.exterior.coords) for r in _polys(V)]
    for fl in flights:
        lines += [LineString([(x * u, y * u) for x, y in q] + [(q[0][0] * u, q[0][1] * u)]) for q in fl["tread_quads"]]
    Fb = F.buffer(GRID_M * 10)
    for s in segments or ():
        if s.get("layer") in layers:
            ls = _extended((s["a"][0] * u, s["a"][1] * u), (s["b"][0] * u, s["b"][1] * u))
            if ls.length > 0 and ls.intersects(Fb):
                lines.append(ls.intersection(Fb))
    for a in arcs or ():
        if a.get("layer") in layers:
            ls = LineString(_arc_points(a, u))
            if ls.intersects(Fb):
                lines.append(ls.intersection(Fb))
    noded = unary_union([set_precision(x, GRID_M) for x in lines if not x.is_empty])
    cells = []
    for c in polygonize(noded):
        c = c.intersection(F)
        for p in _polys(c):
            if p.area <= AREA_EPS_M2:
                continue
            kind = ("VOID" if _area(p.intersection(V)) >= 0.5 * p.area else
                    "TREAD" if _area(p.intersection(T_all)) >= 0.5 * p.area else "FREE")
            cells.append({"g": p, "kind": kind})
    fcells = [c for c in cells if c["kind"] == "FREE"]
    if fcells:
        floor_ids = {id(max(fcells, key=lambda c: c["g"].area))}
        for pt in floor_points or ():
            P = Point(pt[0] * u, pt[1] * u)
            floor_ids |= {id(c) for c in fcells if c["g"].buffer(GRID_M * 10).contains(P)}
    else:
        floor_ids = set()
    seeds = [c for c in cells if c["kind"] in ("VOID", "TREAD")]
    reached, todo = [], list(seeds)
    seen = {id(c) for c in seeds}
    while todo:
        c = todo.pop()
        for d in fcells:
            if id(d) in seen or id(d) in floor_ids:
                continue
            if _touch(c["g"], d["g"]):
                seen.add(id(d))
                reached.append(d)
                todo.append(d)
    R = unary_union([c["g"] for c in reached]).difference(V).difference(T_all) if reached else Polygon()
    floor_cells = unary_union([c["g"] for c in fcells if id(c) in floor_ids]) if floor_ids else Polygon()
    # 4. foot of a flight short of its neighbour's end: HELD when open to the floor cell
    held = Polygon()
    if passes:
        straight = [(fl, _flight_axis(fl, u)) for fl in flights if fl.get("kind") == "STRAIGHT"]
        straight = [(fl, a) for fl, a in straight if a]
        for fl, (ax, cr, run, acr) in straight:
            for side in (-1, 1):
                end = run[1] if side > 0 else run[0]
                best = end
                for g, (ax2, cr2, run2, acr2) in straight:
                    if g is fl or abs(ax[0] * ax2[0] + ax[1] * ax2[1]) < 0.999:
                        continue                                   # not parallel
                    pr = sorted(p[0] * ax[0] + p[1] * ax[1] for q in g["tread_quads"] for p in
                                [(x * u, y * u) for x, y in q])
                    pc = sorted(p[0] * cr[0] + p[1] * cr[1] for q in g["tread_quads"] for p in
                                [(x * u, y * u) for x, y in q])
                    side_by_side = pc[0] >= acr[1] - GRID_M or pc[-1] <= acr[0] + GRID_M
                    overlap_run = min(pr[-1], run[1]) - max(pr[0], run[0]) > 0
                    if not (side_by_side and overlap_run and _touch_or_near(fpoly[g.get("flight_id")],
                                                                            fpoly[fl.get("flight_id")], R)):
                        continue
                    e2 = pr[-1] if side > 0 else pr[0]
                    if side * (e2 - best) > 0:
                        best = e2
                if side * (best - end) <= GRID_M:
                    continue
                st = _strip(ax, cr, (min(end, best), max(end, best)), acr).intersection(F).difference(V)
                st = st.difference(T_all)
                if _area(st.intersection(floor_cells)) > AREA_EPS_M2:
                    held = unary_union([held, st])
                    rec["held"].append({"piece": f"FOOT:{fl.get('flight_id')}:{'end' if side > 0 else 'start'}",
                                        "category": "STAIR_FOOT_UNSETTLED", "status": "HELD",
                                        "m2": round(_area(st), 6),
                                        "dims_m": [round(acr[1] - acr[0], 4), round(abs(best - end), 4)],
                                        "reason": "the flight's last tread line stops short of the parallel flight's "
                                                  "end; the strip between (flight width x the difference) is open to "
                                                  "the floor, so the drawing does not settle foot of the flight or "
                                                  "floor: range, low = not floor, high = floor"})
    R = R.difference(held)
    if passes:
        # per cell: in the opening (touches the void), a closed element beside ONE straight flight that is open to the
        # floor (balustrade / upstand / stringer drawn outside the flight's width: floor or not is not settled -> HELD),
        # or the stair's own footprint (landing, well, edge)
        bands = {}
        for fl in flights:
            if fl.get("kind") == "STRAIGHT":
                a = _flight_axis(fl, u)
                if a:
                    bands[fl.get("flight_id")] = a
        cat_geoms = {"VOID_RESIDUE": [], "STAIR_FOOTPRINT": [], "SIDE_ELEMENT_UNSETTLED": []}
        for c in reached:
            g = c["g"].intersection(R)
            for p in _polys(g):
                if p.area <= AREA_EPS_M2 * 0.01:
                    continue
                if not V.is_empty and _touch(p, V):
                    cat_geoms["VOID_RESIDUE"].append(p)
                    continue
                tf = [fl.get("flight_id") for fl in flights if _touch(p, fpoly[fl.get("flight_id")])]
                beside = False
                if len(tf) == 1 and tf[0] in bands and not floor_cells.is_empty and _touch(p, floor_cells):
                    ax, cr, run, acr = bands[tf[0]]
                    cx = p.centroid.x * cr[0] + p.centroid.y * cr[1]
                    beside = not (acr[0] - GRID_M <= cx <= acr[1] + GRID_M)
                cat_geoms["SIDE_ELEMENT_UNSETTLED" if beside else "STAIR_FOOTPRINT"].append(p)
        k = 0
        for cat in ("VOID_RESIDUE", "STAIR_FOOTPRINT", "SIDE_ELEMENT_UNSETTLED"):
            G = unary_union(cat_geoms[cat]) if cat_geoms[cat] else Polygon()
            for p in sorted(_polys(G), key=lambda g: (-g.area, round(g.centroid.x, 3), round(g.centroid.y, 3))):
                if p.area <= AREA_EPS_M2:
                    continue
                k += 1
                tf = sorted(str(fl.get("flight_id")) for fl in flights if _touch(p, fpoly[fl.get("flight_id")]))
                mr = p.minimum_rotated_rectangle
                ed = sorted({round(math.dist(a, b), 4) for a, b in zip(mr.exterior.coords, mr.exterior.coords[1:])})
                row = {"piece": f"R{k:02d}", "category": cat, "m2": round(p.area, 6), "touches_flights": tf,
                       "bounding_rect_m": ed}
                if cat == "SIDE_ELEMENT_UNSETTLED":
                    row.update(status="HELD", reason="a closed element drawn on the stair's layers beside one flight, "
                               "outside its width and open to the floor (balustrade, upstand or stringer): the plan "
                               "does not say whether the floor finish runs under it; range, low = not floor, "
                               "high = floor")
                    rec["held"].append(row)
                else:
                    row.update(status="DEDUCTED", line="stair (UP-STAIR-005)" if cat == "STAIR_FOOTPRINT" else
                               "opening (not floor, open to below)")
                    rec["pieces"].append(row)
    else:
        rec["not_assessed"] = [{"m2": round(p.area, 6), "reason": "lowest storey: floor under / around a rising "
                                "stair is not settled by the plan; left in the floor line as before"}
                               for p in _polys(R) if p.area > AREA_EPS_M2]
    void_res = sum(p["m2"] for p in rec["pieces"] if p["category"] == "VOID_RESIDUE")
    stair_res = sum(p["m2"] for p in rec["pieces"] if p["category"] == "STAIR_FOOTPRINT")
    held_m2 = sum(h["m2"] for h in rec["held"])
    a0 = face.get("area_m2") if face.get("area_m2") is not None else _area(F)
    base = a0 - _area(V) - _area(T_own) - _area(T_below)
    low = base - (void_res + stair_res + held_m2 if passes else 0.0)
    rec.update(void_residue_m2=round(void_res, 6), stair_footprint_m2=round(stair_res, 6),
               held_m2=round(held_m2, 6), floor_before_residue_m2=round(base, 6),
               floor_net_low_m2=round(low, 6), floor_net_high_m2=round(low + held_m2, 6))
    if held_m2 > 0:
        rec.update(status="HELD_RANGE", floor_net_m2=None)
    else:
        rec.update(status="RELEASED", floor_net_m2=round(low, 6))
    # conservation: the face's own area less void and treads (the ledger) = the free floor of the exact geometry; the
    # residue and held pieces are parts of that free floor, so floor (low) + residue + held = the ledger exactly
    geo = _area(free)
    rec["conservation"] = {"face_m2": round(a0, 6), "free_floor_ledger_m2": round(base, 6),
                           "free_floor_geometry_m2": round(geo, 6),
                           "state": "BALANCED" if abs(base - geo) <= 0.01 else "RESIDUAL_UNRESOLVED"}
    return rec


def _touch_or_near(a, b, R):
    """two flights belong to one stair when they touch, or a residue piece touches both (a well between them)."""
    if _touch(a, b) or a.distance(b) <= GRID_M:
        return True
    return any(_touch(p, a) and _touch(p, b) for p in _polys(R))


def policy_record():
    return {"policy_id": POLICY_ID, "grid_m": GRID_M, "area_eps_m2": AREA_EPS_M2, "touch_m": TOUCH_M,
            "extend_m": EXTEND_M,
            "rules": list(RULES), "wired": False}
