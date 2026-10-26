"""T-307 geometry: the support class of every bottom-bar END of a suspended-slab panel, read from the drawn faces
(research only; shapely; every villa). Input = the polygonised faces of a roof-slab plan (T-139 slab_faces.py output:
slab panels, beam bands / column / junction pieces, openings, stairs) with their T-139 classes. Bar lines are placed
exactly as T-152 places them (readings A and B; T-152 `_segments` / probe re-used read only); for each end the ray
past the slab face is walked face by face:

  * another SLAB panel of the sheet within 0.80 m (T-152 probe)                 -> CONTINUOUS (or STEP_EDGE, sunken)
  * beam-class pieces, then a SLAB panel (band wider than the probe)            -> CONTINUOUS_WIDE_BEAM (or STEP_EDGE)
  * ONE beam band (long piece, l >= BAND_MIN_L) crossed square (crossing = its
    drawn width within SQUARE_TOL; mark width, where a mark is printed in the
    band, equal to the schedule width), then no slab                            -> EDGE_BEAM, w = crossing length
  * no beam-class face at the slab edge                                          -> OPENING_EDGE
  * anything else (column / junction piece, two pieces, oblique, conflict)      -> IRREGULAR_SUPPORT
The class decides the end basis (t307_bar_ends.end_basis); no length is invented here.
"""

import math

from shapely.geometry import LineString, Point

BEAM_CLASSES = {"BEAM_OR_COLUMN", "BEAM", "BEAM_HELD"}
PROBE = 0.80          # T-152 continuity probe (m)
WALK_MAX = 2.0        # m: longest support walked past a slab face
STEP = 0.003          # m: sample point past a boundary
SQUARE_TOL = 0.005    # m: crossing length vs the band's drawn width
BAND_MIN_L = 1.0      # m: a beam band is a long piece; shorter pieces are columns / junctions (irregular support)
MARK_TOL = 0.005


def _seg_from(ray_pt, u, poly, s0):
    """length of the ray inside poly starting at distance s0 (the piece that contains s0 + STEP)."""
    far = (ray_pt[0] + u[0] * (s0 + WALK_MAX), ray_pt[1] + u[1] * (s0 + WALK_MAX))
    ray = LineString([(ray_pt[0] + u[0] * s0, ray_pt[1] + u[1] * s0), far])
    g = ray.intersection(poly.buffer(1e-7))
    best = None
    for q in getattr(g, "geoms", [g]):
        if q.is_empty or q.geom_type != "LineString":
            continue
        a = min(Point(ray.coords[0]).distance(Point(c)) for c in q.coords)
        if a <= STEP + 1e-6:
            best = q.length if best is None else max(best, q.length)
    return best


def _face_at(pt, faces):
    for fid, f in faces.items():
        if f["poly"].contains(Point(pt)):
            return fid
    return None


def classify_end(pt, u, panel_id, faces, sheet_slabs, sunken, mark_widths):
    """-> dict(cls, w, beyond, pieces, neighbour, note). faces: id -> dict(poly, cls, w, l, marks) for one sheet;
    sheet_slabs: [(id, poly)] SLAB panels of the sheet other than this one (T-152 'others'); sunken: set of sunken
    panel ids; mark_widths: mark -> list of schedule width texts."""
    # 1. T-152 probe: a slab face within PROBE
    ray = LineString([pt, (pt[0] + u[0] * PROBE, pt[1] + u[1] * PROBE)])
    best = None
    for oid, og in sheet_slabs:
        if not ray.intersects(og):
            continue
        hit = ray.intersection(og)
        d = min(Point(pt).distance(Point(q)) for g in getattr(hit, "geoms", [hit]) for q in g.coords) \
            if not hit.is_empty else None
        if d is not None and d > 1e-4 and (best is None or d < best[0]):
            best = (d, oid)
    if best is not None:
        nb = best[1]
        step = (panel_id in sunken) or (nb in sunken)
        return dict(cls="STEP_EDGE" if step else "CONTINUOUS", w=round(best[0], 4), beyond="SLAB", pieces=0,
                    neighbour=nb, note="sunken panel at this support" if step else "")
    # 2. walk the faces past the slab edge
    s, pieces = 0.0, []
    beyond, nb = "NONE", ""
    while s < WALK_MAX:
        q = (pt[0] + u[0] * (s + STEP), pt[1] + u[1] * (s + STEP))
        fid = _face_at(q, faces)
        if fid is None:
            beyond = "NONE"
            break
        f = faces[fid]
        if f["cls"] not in BEAM_CLASSES:
            beyond, nb = f["cls"], fid
            break
        ln = _seg_from(pt, u, f["poly"], s)
        if ln is None or ln <= 1e-6:
            beyond = "UNWALKABLE"
            break
        pieces.append((fid, round(ln, 4)))
        s += ln
    else:
        beyond = "WALK_LIMIT"
    w = round(sum(p[1] for p in pieces), 4)
    if not pieces:
        return dict(cls="OPENING_EDGE", w=None, beyond=beyond, pieces=0, neighbour=nb, note="no beam face")
    f0 = faces[pieces[0][0]]
    square = len(pieces) == 1 and f0["l"] >= BAND_MIN_L and abs(pieces[0][1] - f0["w"]) <= SQUARE_TOL
    if beyond == "SLAB":
        if (panel_id in sunken) or (nb in sunken):
            return dict(cls="STEP_EDGE", w=w, beyond=beyond, pieces=len(pieces), neighbour=nb,
                        note="sunken panel beyond a %.3f m support" % w)
        if square:
            return dict(cls="CONTINUOUS_WIDE_BEAM", w=w, beyond=beyond, pieces=1, neighbour=nb,
                        note="slab beyond one %.3f m band (> T-152 probe)" % w)
        return dict(cls="IRREGULAR_SUPPORT", w=w, beyond=beyond, pieces=len(pieces), neighbour=nb,
                    note="composite support (slab beyond %.3f m of %d pieces)" % (w, len(pieces)))
    note = []
    if len(pieces) > 1:
        note.append("composite support (%d pieces)" % len(pieces))
    if beyond in ("UNWALKABLE", "WALK_LIMIT"):
        note.append("support not crossed (%s)" % beyond)
    if f0["l"] < BAND_MIN_L:
        note.append("short piece l %.3f (column / junction)" % f0["l"])
    if abs(pieces[0][1] - f0["w"]) > SQUARE_TOL:
        note.append("crossing %.3f vs drawn width %.3f (oblique)" % (pieces[0][1], f0["w"]))
    for mk in f0.get("marks", []):
        ws = mark_widths.get(mk)
        if ws is None:
            continue
        nums = []
        for t in ws:
            try:
                nums.append(float(t))
            except (TypeError, ValueError):
                note.append("mark %s width in conflict (%s)" % (mk, t))
        if nums and not any(abs(x - f0["w"]) <= MARK_TOL for x in nums):
            note.append("mark %s schedule width %s vs drawn %.3f" % (mk, "/".join(map(str, nums)), f0["w"]))
    if note:
        return dict(cls="IRREGULAR_SUPPORT", w=w, beyond=beyond, pieces=len(pieces), neighbour=nb,
                    note="; ".join(note))
    return dict(cls="EDGE_BEAM", w=w, beyond=beyond, pieces=1, neighbour=nb,
                note="band %s" % (",".join(f0.get("marks", [])) or "unmarked"))


def bar_lines(poly, axis, n, segments_fn):
    """T-152 placement: readings A (n bars centred in their strips) and B (n + 1, one on each edge); per bar line its
    segments as (length, lo end point, hi end point, unit vector)."""
    x0, y0, x1, y1 = poly.bounds
    lo, hi = (y0, y1) if axis == "x" else (x0, x1)
    H = hi - lo
    pos = {"A": [lo + (k + 0.5) * H / n for k in range(n)], "B": [lo + k * H / n for k in range(n + 1)]}
    out = {}
    for tag, cs in pos.items():
        lines = []
        for c in cs:
            segs = []
            for sg in segments_fn(poly, axis, c):
                (ax, ay), (bx, by) = sg.coords[0], sg.coords[-1]
                if (bx - ax) + (by - ay) < 0:
                    ax, ay, bx, by = bx, by, ax, ay
                u = (1.0, 0.0) if axis == "x" else (0.0, 1.0)
                segs.append((round(sg.length, 4), (ax, ay), (bx, by), u))
            lines.append(segs)
        out[tag] = lines
    return round(H, 4), out


def classify_panel(panel_id, poly, axis, n, faces, sheet_slabs, sunken, mark_widths, segments_fn):
    """-> {'A': [[(seg_len, end_lo, end_hi), ...] per bar line], 'B': ...} with end = classify_end(...)."""
    _H, lines = bar_lines(poly, axis, n, segments_fn)
    res = {}
    for tag, ls in lines.items():
        res[tag] = []
        for segs in ls:
            row = []
            for ln, a, b, u in segs:
                e0 = classify_end(a, (-u[0], -u[1]), panel_id, faces, sheet_slabs, sunken, mark_widths)
                e1 = classify_end(b, u, panel_id, faces, sheet_slabs, sunken, mark_widths)
                row.append((ln, e0, e1))
            res[tag].append(row)
    return res


def angle_ok(u):
    return math.isclose(abs(u[0]) + abs(u[1]), 1.0)
