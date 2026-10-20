"""FACADE_PASSAGE_WALLS_V1 (T-109): the walls of an open-air passage are exterior faces; the passage mouth is not a
building opening. A check piece: NOT wired into any method version (ARCH_TAKEOFF_V2.9 .. V2.12 and their FACADE and
OPENING outputs are unchanged); nothing here is read by a released line.

The defect (found on the development villa, every villa can have it): two parts of a building stand side by side with
a narrow strip of outside ground between them (a side passage). Their front faces are collinear, so the opening census
reads the open end of the strip as a doorless wall opening (kind PASSAGE, its thresholds closing it on both faces) and
the facade outline (UP-FACADE-001: the outer cycle of the plan topology, every opening closed on its outer face)
crosses the strip on that threshold. The two walls along the strip, real exterior faces, drop out of the run; the
mouth, which is no wall, is counted instead; and the mouth is released as a building opening (ARCH.PASSAGE nr).

What the drawing must show before a passage is read as outside air (every test is a drawn fact, none is a size limit):
  1. MOUTH: an edge of the facade outline that is a PASSAGE threshold (no door symbol, no leaf, no glazing in the gap:
     the census's own PASSAGE kind).
  2. SPACE: the faces behind the mouth, joined only through further PASSAGE thresholds (a doorless strip split by the
     census into pieces). A door, a window, a glazing line or a wall stops the search: they are the building envelope.
  3. NOT A ROOM: no room label, room tag or fixture lies in the space. A labelled space behind a doorless opening is the
     building's interior (an entrance hall without a door is still measured as the engine does): KEPT, nothing changes.
  4. AN OPEN MOUTH: at least one mouth has nothing drawn across it. A mouth with a non-building element drawn across it
     on both faces (two parallel lines of one layer that is not a building wall, jamb to jamb: a boundary wall or a fence
     wall) is CLOSED_BY_ELEMENT: the element's body is not part of the space and its faces are not the building's
     facade; the passage walls run to the element's inner face. A single line across a mouth (no thickness) is HELD.
  5. OPEN TO THE SKY, or OPEN AT BOTH ENDS: some part of the space lies under no plate above (the outline of the floor
     above and any roof given, in this floor's coordinates), or two or more mouths are open (a covered breezeway is
     still outside air). A space fully covered with a single open mouth (a car porch, or a room whose door the census
     missed) is HELD with both runs: the plan alone does not say which (an elevation or a section does).
  When 1-5 hold the space is OPEN_AIR: run = walked - every mouth edge on the outline + every building face that bounds
  the space (walls, columns, wall caps, and the door and window thresholds in them: UP-FACADE-001 includes openings in
  the run). Faces against the element body and the element's own outer face are not counted. Each mouth is listed as
  NOT_A_BUILDING_OPENING. The part of the walls under the plate above is listed (covered_m) with the soffit area
  (covered_m2): the run is geometry only; heights (owner Q-07) and finishes are not touched here.

Rules: UP-FACADE-001 (REQUIRES_CONFIRMATION: the facade is the exterior face of the wall network), UP-WALL-GEOM-001 (a
wall band is two drawn faces at its thickness), UP-QTY-STATUS-001 (what the drawing does not settle is HELD with its
possible values, never one picked and never 0). Owner Q-25: no gap-size limit is assumed anywhere here.

API (lengths in metres, shapely 2):
    passage_walls(ring, faces, *, labels=(), above=None, other_lines=None, levels=(), eps_m=EPS_M) -> dict
    faces_from_arrangement(arr, unit_m) -> {face id: {"polygon", "edges"}}   (engine.source.topology arrangement)
"""

from __future__ import annotations

import math

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

POLICY = "FACADE_PASSAGE_WALLS_V1"
EPS_M = 0.001                       # drawing noise: two points this close are one point (1 mm; not a gap limit)
ANG_EPS = 1e-4                      # parallel test on unit vectors (sin of the angle)
MOUTH_ROLE = "PASSAGE_THRESHOLD"
BUILDING_FACE_ROLES = ("WALL", "COLUMN", "WALL_CAP", "WINDOW", "GLAZING", "DOOR_CLOSURE")
RULES = ("UP-FACADE-001", "UP-WALL-GEOM-001", "UP-QTY-STATUS-001", "owner Q-25 (no assumed gap limit)")


# ============================================================================================ small geometry
def _len(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _unit(a, b):
    L = _len(a, b)
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L) if L > 0 else (0.0, 0.0)


def _cross(u, v):
    return u[0] * v[1] - u[1] * v[0]


def _off(p, o, u):
    return _cross(u, (p[0] - o[0], p[1] - o[1]))


def _proj(p, o, u):
    return u[0] * (p[0] - o[0]) + u[1] * (p[1] - o[1])


def _covered(lines, a, b, eps_m):
    """[(line, offset)] of lines parallel to a-b that cover a-b end to end, offset = signed distance from the a-b
    line (left of a->b positive)."""
    u = _unit(a, b)
    L = _len(a, b)
    out = []
    for ln in lines:
        p, q = ln["a"], ln["b"]
        if _len(p, q) <= eps_m or abs(_cross(_unit(p, q), u)) > ANG_EPS:
            continue
        d0, d1 = _off(p, a, u), _off(q, a, u)
        if abs(d0 - d1) > eps_m:
            continue
        lo, hi = sorted((_proj(p, a, u), _proj(q, a, u)))
        if lo <= eps_m and hi >= L - eps_m:
            out.append((ln, 0.5 * (d0 + d1)))
    return out


def _roles(e):
    return tuple(e.get("roles") or (e.get("role") or "NONE",))


def _is_building_face(e):
    rr = _roles(e)
    if MOUTH_ROLE in rr:
        return False
    return any(r in BUILDING_FACE_ROLES or (r.endswith("_THRESHOLD") and r != MOUTH_ROLE) for r in rr)


def _opening_of(e):
    for s in e.get("sources") or ():
        s = str(s)
        if s.startswith("THR|"):
            return s.split("|")[1]
    return None


def _ekey(e):
    a, b = e["a"], e["b"]
    k = (round(a[0], 6), round(a[1], 6), round(b[0], 6), round(b[1], 6))
    k2 = (k[2], k[3], k[0], k[1])
    return min(k, k2)


# ============================================================================================ the check
def passage_walls(ring, faces, *, labels=(), above=None, other_lines=None, levels=(), eps_m=EPS_M):
    """ring: the facade outline as consecutive edges {"a", "b", "roles", "len_m", "straight", "sources", "inner": id of
    the bounded face behind the edge}. faces: {face id: {"polygon": [[x, y], ...], "edges": [{"a", "b", "roles",
    "len_m", "straight", "sources", "other": the face id across the edge, None for the outside}]}} (bounded faces of
    the plan topology, metres). labels: [[x, y]] points of room labels, room tags and fixtures. above: None (not read)
    or [polygon] plates above this floor in its coordinates. other_lines: None (not read) or [{"a", "b", "layer"}]
    straight lines of layers that are not building walls. levels: [{"at": [x, y], "value": text}] printed level marks
    (evidence only). -> {"policy", "state": RESOLVED | HELD_RANGE | NO_PASSAGE | NO_OUTLINE, "walked_m", "run_m" (every
    OPEN_AIR passage applied), "range_m" ([low, high] when a passage is HELD), "passages": [...],
    "not_building_openings": [opening ids]}"""
    out = {"policy": POLICY, "rules": list(RULES)}
    R = list(ring or ())
    if len(R) < 3:
        return dict(out, state="NO_OUTLINE", walked_m=None, run_m=None, range_m=None, passages=[],
                    not_building_openings=[], why="no closed outline was given")
    walked = sum(float(e.get("len_m", _len(e["a"], e["b"]))) for e in R)
    mouths = [i for i, e in enumerate(R) if MOUTH_ROLE in _roles(e)]
    if not mouths:
        return dict(out, state="NO_PASSAGE", walked_m=round(walked, 6), run_m=round(walked, 6), range_m=None,
                    passages=[], not_building_openings=[], why="no doorless passage threshold on the outline")
    F = faces or {}
    polys = {k: Polygon(v["polygon"]) for k, v in F.items() if len(v.get("polygon") or ()) >= 3}
    plate = unary_union([Polygon(p) for p in above if len(p) >= 3]) if above else None
    regions, seen_face = [], {}
    wall_end_gaps = []
    for i in mouths:
        f0 = R[i].get("inner")
        if f0 is not None and f0 in F and any("WALL_CAP" in _roles(e) for e in F[f0]["edges"]):
            # the threshold runs across the end of a wall band (its cap is drawn): a gap in the wall's face line,
            # not the mouth of a space; the run keeps it as the wall's outer face
            wall_end_gaps.append({"edge_index": i, "opening_id": _opening_of(R[i]),
                                  "len_m": round(float(R[i].get("len_m", _len(R[i]["a"], R[i]["b"]))), 6),
                                  "why": "WALL_END_GAP: the face behind this piece of the threshold is a wall end "
                                         "closed by its cap; the outer face of that wall, kept in the run"})
            continue
        if f0 is None or f0 not in F:
            regions.append({"mouth_edges": [i], "faces": None})
            continue
        if f0 in seen_face:
            regions[seen_face[f0]]["mouth_edges"].append(i)
            continue
        reg, stack = {f0}, [f0]
        while stack:
            k = stack.pop()
            for e in F[k]["edges"]:
                o = e.get("other")
                if o is not None and o in F and o not in reg and _roles(e) == (MOUTH_ROLE,):
                    reg.add(o)
                    stack.append(o)
        idx = len(regions)
        for k in reg:
            seen_face[k] = idx
        regions.append({"mouth_edges": [i], "faces": reg})
    res = [_region(R, F, polys, r, labels, plate, above is not None, other_lines, levels, eps_m) for r in regions]
    applied = sum(r["delta_m"] for r in res if r["state"] == "OPEN_AIR")
    run = walked + applied
    held = [r for r in res if r["state"] == "HELD"]
    lo = run + sum(min(0.0, r["delta_m"]) for r in held if r["delta_m"] is not None)
    hi = run + sum(max(0.0, r["delta_m"]) for r in held if r["delta_m"] is not None)
    unknown = any(r["delta_m"] is None for r in held)
    state = "HELD_RANGE" if held else "RESOLVED"
    nbo = sorted({m["opening_id"] for r in res if r["state"] == "OPEN_AIR" for m in r["mouths"] if m["opening_id"]})
    return dict(out, state=state, walked_m=round(walked, 6), run_m=round(run, 6),
                range_m=(None if not held else [round(lo, 6), round(hi, 6)] if not unknown else "NOT_ESTABLISHED"),
                passages=res, not_building_openings=nbo, wall_end_gaps=wall_end_gaps)


def _mouth_record(R, i, other_lines, reg_polys, eps_m):
    e = R[i]
    a, b = tuple(map(float, e["a"])), tuple(map(float, e["b"]))
    rec = {"edge_index": i, "opening_id": _opening_of(e), "len_m": round(float(e.get("len_m", _len(a, b))), 6),
           "at": [[round(a[0], 6), round(a[1], 6)], [round(b[0], 6), round(b[1], 6)]]}
    if other_lines is None:
        return dict(rec, cls="NOT_READ", why="the lines of other layers were not read: whether an element closes this "
                                             "mouth is not known")
    outer = _covered(other_lines, a, b, eps_m)
    outer = [(ln, d) for ln, d in outer if abs(d) <= eps_m]
    if not outer:
        return dict(rec, cls="OPEN_MOUTH", why="nothing is drawn across the mouth")
    # the element's inner face: the nearest line of the same layer, parallel, covering the mouth, on the space side
    u = _unit(a, b)
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    side = None
    for p in reg_polys:
        q = p.representative_point()
        s = _off((q.x, q.y), a, u)
        if abs(s) > eps_m:
            side = 1.0 if s > 0 else -1.0
            break
    layers = {ln.get("layer") for ln, _ in outer}
    inner = [(ln, d) for ln, d in _covered(other_lines, a, b, eps_m)
             if ln.get("layer") in layers and side is not None and side * d > eps_m]
    if not inner:
        return dict(rec, cls="HELD_LINE_ONLY", why="one line is drawn across the mouth (no second face of the same "
                                                   "layer): an element without a thickness, a gate or a railing; "
                                                   "not settled by the plan")
    ln, d = min(inner, key=lambda x: abs(x[1]))
    t = abs(d)
    band = Polygon([a, b, (b[0] - u[1] * d, b[1] + u[0] * d), (a[0] - u[1] * d, a[1] + u[0] * d)])
    return dict(rec, cls="CLOSED_BY_ELEMENT", element_t_m=round(t, 6), element_layer=ln.get("layer"),
                band=band, why="two parallel lines of one non-building layer (%s) cross the mouth jamb to jamb, %.3f m "
                               "apart: an element (a boundary or fence wall) closes it; not the building's facade"
                               % (ln.get("layer"), t), mid=mid)


def _region(R, F, polys, r, labels, plate, above_read, other_lines, levels, eps_m):
    mrec_idx = r["mouth_edges"]
    if r["faces"] is None:
        return {"state": "HELD", "why": "MOUTH_FACE_NOT_GIVEN: the face behind the mouth is not known",
                "mouths": [{"edge_index": i, "opening_id": _opening_of(R[i])} for i in mrec_idx], "delta_m": None}
    reg = set(r["faces"])
    reg_polys = [polys[k] for k in reg if k in polys]
    # every edge of the region's faces that lies on the outline is a mouth of it (a region can have several)
    ring_keys = {_ekey(e): i for i, e in enumerate(R)}
    for k in reg:
        for e in F[k]["edges"]:
            if e.get("other") is None and _roles(e) == (MOUTH_ROLE,):
                j = ring_keys.get(_ekey(e))
                if j is not None and j not in mrec_idx:
                    mrec_idx.append(j)
    mouths = [_mouth_record(R, i, other_lines, reg_polys, eps_m) for i in sorted(mrec_idx)]
    area = unary_union(reg_polys) if reg_polys else None
    base = {"faces": sorted(reg, key=str), "area_m2": round(area.area, 6) if area is not None else None,
            "levels": [lv for lv in levels if area is not None and area.buffer(eps_m).contains(Point(lv["at"]))]}
    pub = [{k: v for k, v in m.items() if k not in ("band", "mid")} for m in mouths]
    named = [p for p in labels if area is not None and area.buffer(-eps_m).contains(Point(p))]
    if named:
        return dict(base, state="KEPT", mouths=pub, delta_m=0.0, labels_inside=len(named),
                    why="LABELLED_SPACE: a room label, tag or fixture lies in the space behind the doorless opening: "
                        "the building's interior; the outline stands as the engine walks it")
    if any(m["cls"] == "NOT_READ" for m in mouths):
        return dict(base, state="HELD", mouths=pub, delta_m=None,
                    why="LINES_NOT_READ: what is drawn across the mouths is not known")
    # the element bodies across closed mouths are not part of the space
    bands = [m["band"].buffer(eps_m) for m in mouths if m["cls"] == "CLOSED_BY_ELEMENT"]
    body = {k for k in reg if k in polys and any(bd.contains(polys[k]) for bd in bands)}
    space = reg - body
    sp_area = unary_union([polys[k] for k in space if k in polys]) if space else None
    walls, inner_lines, unclassified = [], 0.0, []
    for k in sorted(space, key=str):
        for e in F[k]["edges"]:
            o = e.get("other")
            if o in space or o is None:
                continue                     # inside the space, or on the outline (a mouth, already counted)
            L = float(e.get("len_m", _len(e["a"], e["b"])))
            if o in body:
                inner_lines += L             # the element's inner face
                continue
            if _is_building_face(e):
                ln = LineString([e["a"], e["b"]])
                cov = ln.intersection(plate).length if plate is not None and ln.length > 0 else 0.0
                walls.append({"len_m": round(L, 6), "roles": list(_roles(e)), "opening_id": _opening_of(e),
                              "covered_m": round(cov * (L / ln.length) if ln.length > 0 else 0.0, 6),
                              "at": [[round(e["a"][0], 6), round(e["a"][1], 6)],
                                     [round(e["b"][0], 6), round(e["b"][1], 6)]]})
            else:
                unclassified.append({"len_m": round(L, 6), "roles": list(_roles(e))})
    removed = sum(m["len_m"] for m in mouths)
    added = sum(w["len_m"] for w in walls)
    delta = added - removed
    covered_m2 = sp_area.intersection(plate).area if (plate is not None and sp_area is not None) else None
    open_sky_m2 = (sp_area.area - covered_m2) if covered_m2 is not None else None
    open_mouths = [m for m in mouths if m["cls"] == "OPEN_MOUTH"]
    rec = dict(base, mouths=pub, space_area_m2=round(sp_area.area, 6) if sp_area is not None else None,
               walls=walls, walls_m=round(added, 6), mouths_m=round(removed, 6), delta_m=round(delta, 6),
               element_inner_face_m=round(inner_lines, 6),
               covered_m2=None if covered_m2 is None else round(covered_m2, 6),
               open_sky_m2=None if open_sky_m2 is None else round(open_sky_m2, 6),
               covered_walls_m=round(sum(w["covered_m"] for w in walls), 6),
               openings_onto=sorted({w["opening_id"] for w in walls if w["opening_id"]}))
    if unclassified:
        return dict(rec, state="HELD", unclassified=unclassified,
                    why="UNCLASSIFIED_BOUNDARY: %.3f m of the space's boundary is neither a building face nor a "
                        "passage threshold; what bounds the space is not settled" % sum(x["len_m"] for x in unclassified))
    if any(m["cls"] == "HELD_LINE_ONLY" for m in mouths):
        return dict(rec, state="HELD", why="a mouth is crossed by a single line (no element thickness): not settled")
    if not open_mouths:
        return dict(rec, state="HELD", why="NO_OPEN_MOUTH: every mouth is closed by an element; a court enclosed by "
                                           "boundary walls is not settled by the plan")
    if len(open_mouths) >= 2:
        return dict(rec, state="OPEN_AIR", why="OPEN_AT_TWO_ENDS: doorless, glassless and unlabelled, open at %d "
                                               "mouths: outside air whether roofed or not" % len(open_mouths))
    if not above_read:
        return dict(rec, state="HELD", why="ROOF_NOT_READ: one open mouth and no plate above was given: an open "
                                           "passage or a covered space the plan alone does not settle")
    if open_sky_m2 is not None and open_sky_m2 > eps_m:
        return dict(rec, state="OPEN_AIR", why="OPEN_TO_THE_SKY: doorless, glassless and unlabelled, open at its "
                                               "mouth and %.3f m2 of it under no plate above: outside air"
                                               % open_sky_m2)
    return dict(rec, state="HELD", why="COVERED_ONE_MOUTH: the whole space is under the plate above and has one open "
                                       "mouth: a covered porch or a room whose door the census missed; an elevation "
                                       "or section settles it")


# ============================================================================================ engine adapter
def faces_from_arrangement(arr, unit_m, step_m=0.05):
    """bounded faces of an engine.source.topology arrangement in metres: {face index: {"polygon", "edges"}}; each edge
    {"a", "b", "len_m", "roles", "straight", "sources", "other": the face across (None for an unbounded face)}. Arcs
    are flattened for the polygon only (their true length is kept in len_m). A door closure edge has role
    DOOR_CLOSURE (as facade_gap_closure.ring_from_arrangement)."""
    owner = {}
    for k, f in enumerate(arr.faces):
        for h in f["cycle"]:
            owner[(h[0], h[1])] = k
    out = {}
    for k, f in enumerate(arr.faces):
        if not f["cycle"] or f["area"] <= 0:
            continue
        pts, edges = [], []
        for ei, fw in f["cycle"]:
            e = arr.edges[ei]
            a = arr.nodes[e["n0"] if fw else e["n1"]]
            b = arr.nodes[e["n1"] if fw else e["n0"]]
            if e["kind"] == "S":
                L = _len(a, b) * unit_m
                pts.append([a[0] * unit_m, a[1] * unit_m])
            else:
                pr = e["prim"]
                L = pr.r * (e["t1"] - e["t0"]) * unit_m
                t0, t1 = (e["t0"], e["t1"]) if fw else (e["t1"], e["t0"])
                n = max(2, int(math.ceil(abs(t1 - t0) * pr.r * unit_m / step_m)))
                for i in range(n):
                    x, y = pr.point(t0 + (t1 - t0) * i / n)
                    pts.append([x * unit_m, y * unit_m])
            o = owner.get((ei, not fw))
            if o is not None and arr.faces[o]["area"] <= 0:
                o = None
            src = sorted(str(s) for s in e["sources"])
            roles = sorted(e["roles"]) or ["NONE"]
            if any(s.startswith("CLOSURE|") for s in src):
                roles = ["DOOR_CLOSURE"]
            edges.append({"a": [a[0] * unit_m, a[1] * unit_m], "b": [b[0] * unit_m, b[1] * unit_m], "len_m": L,
                          "roles": roles, "straight": e["kind"] == "S", "sources": src, "other": o})
        out[k] = {"polygon": pts, "edges": edges}
    return out


def ring_with_inner(arr, k, unit_m, wall_t_by_source=None):
    """facade_gap_closure.ring_from_arrangement(arr, k, ...) with "inner": the bounded face behind each edge."""
    from engine.source import facade_gap_closure as G
    owner = {}
    for j, f in enumerate(arr.faces):
        for h in f["cycle"]:
            owner[(h[0], h[1])] = j
    ring = G.ring_from_arrangement(arr, k, unit_m, wall_t_by_source)
    for e, (ei, fw) in zip(ring, arr.faces[k]["cycle"]):
        o = owner.get((ei, not fw))
        e["inner"] = o if o is not None and arr.faces[o]["area"] > 0 else None
    return ring
