"""EXTERIOR SPACES (T-071): roofs, balconies, pools, voids and gardens drawn on a layer of their own, measured round
their held label. Method piece, NOT wired into a released method: arch_rooms.py, room_label_guard.py and every frozen
room builder are untouched; no released face, room or quantity changes.

Why (T-062, research/agents_t062): an exterior label (ROOF, BALCONY / TERRACE, POOL, VOID, GARDEN) often lies in no
closed room because the room builder admits only WALL / COLUMN / WINDOW lines, while the parapet, pool or void outline
is drawn on a layer the run types OTHER, and the parapet line often stops a few centimetres short of the wall it meets.
ROOM_LABEL_GUARD_V1 (T-061) already HOLDS such a label (ROOM_LABEL_NO_FACE, no area). This piece attaches the drawn
geometry to that held record and releases only what an owner rule covers:

    trace(labels, building, layers, unit_m, openings=(), facts=None, reach_m=None) -> {"records", "summary", ...}

    labels    texts of ONE plan frame that the guard holds: {"id", "value" (or "text"), "x", "y"}; only texts that
              ROOM_VOCAB_V2 types as an exterior code (EXTERIOR_CODES) are traced, the rest is passed by (counted)
    building  the frame's room-builder boundary items (the first arrangement of arch_rooms.spaces: walls, columns,
              windows, thresholds, wall caps, door closures): BoundaryItem-like (source_id, kind, geometry, role) with
              kind SEGMENT (x1, y1, x2, y2), ARC (cx, cy, r, a0, a1 radians, counter-clockwise) or CIRCLE (cx, cy, r)
    layers    {layer: [items]} the lines of each layer the run typed OTHER, same item format (items_of_layer builds
              them from the intake entities)
    unit_m    metres per drawing unit (required: no length is guessed without units; None -> every record HELD
              UNITS_MISSING with no area)
    openings  recognised opening elements of the run (door / window / passage openings, door swings, gates):
              {"id", "kind", "polygon": [(x, y), ...]} or {"id", "kind", "segment": (x1, y1, x2, y2)}
    facts     optional project facts, never engine constants: {"inner_shapes": {<source id of the shape's line>:
              {"treatment": "OPENING" | "MEMBRANE_UNDER", "source": "<drawing / owner answer>"}}}
    reach_m   how far a free parapet end is searched along its own direction for the line it should meet (default:
              arch_rooms.THIN_LIMIT_M, the engine's existing "inside a wall thickness" limit). It is a search reach,
              not a gap-size rule: owner Q-25 closes EVERY drafting gap and names no size limit; a gap beyond the reach
              is simply not found, and the label then stays HELD (never released on a guess, never 0)

Per traced label, for every OTHER layer whose lines (with the building lines and the found closures) close a face
round it: A = the area inside the drawn edge (net of the closed shapes inside it), A's perimeter split into the
layer's own edges, building edges and closures, every closure with its length, what it meets and what lies on it,
the closed shapes inside, and B = A widened by the band of the layer's own edges (the parallel line of the same layer
outside each edge, MEASURED, never assumed). B is reported for review only: the owner chose A (Q-24).

Status (UP-QTY-STATUS-001: every exterior label reported once, never 0, never dropped):
  ROOF      RELEASED_METHOD_PIECE on owner Q-24 (measured like a bathroom floor, UP-WP-003): membrane over A (inside
            the parapet), upturn 0.20 m on the whole A boundary (parapet, walls, closures) plus round each closed shape
            inside that is an opening (Q-24 dome answer, Q-29 skylights); every gap closed and listed (Q-25). HELD when
            no single layer closes the face (NO_CLOSING_LAYER, AMBIGUOUS_BOUNDARY_LAYER), when a gap has an opening
            element on it (GAP_HAS_OPENING), or for the part of an unidentified closed shape inside (INNER_SHAPE_
            UNIDENTIFIED: its area is shown and held; the rest of the roof is released)
  BALCONY   (balcony / terrace) membrane over A PROVISIONAL (UP-WP-ROOF-001 "drawn exterior space area", as
            owner_finish_scope.exterior_wp_lines); upturn HELD EXTERIOR_WP_UPTURN_BY_SPECIFICATION (same function)
  POOL      geometry attached, HELD POOL_NO_MEMBRANE_RULE (no Urban rule makes a pool a membrane row; its concrete is
            the concrete ledger's)
  GARDEN    geometry attached, HELD EXTERIOR_SCOPE_UNRESOLVED (knowledge 1.5.0 OQ-04)
  VOID      UNSUPPORTED VOID_OPEN_TO_BELOW (excluded by rule; outline attached for the census)

General: no layer, room or project name is coded; mm and m, rotated and mirrored plans read alike. shapely 2.
"""

from __future__ import annotations

import math
from collections import defaultdict

import shapely
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import linemerge, polygonize, unary_union
from shapely.strtree import STRtree

from engine.source import room_vocab as RV

POLICY = "EXTERIOR_SPACES_V1"
RULES = ("UP-WP-ROOF-001", "UP-WP-003", "UP-QTY-STATUS-001")
OWNER_ANSWERS = ("Q-24", "Q-25", "Q-29")
EXTERIOR_CODES = ("ROOF", "BALCONY", "POOL", "VOID", "GARDEN")
UPTURN_H_M = 0.20                       # UP-WP-003 (owner Q-03: 0.20 m), applied to roofs by owner Q-24
GAP_LAP_M = 0.10                        # owner Q-25: membrane over a gap with a 0.10 m overlap (UP-WP-002 lap); shown
SAGITTA_M = 0.001                       # arc / circle chord tolerance (1 mm)
SNAP_M = 0.001                          # numerical coincidence (two lines touch); not a drafting-gap threshold
OPENING_WORDS = (r"DOME", r"SKY\s*LIGHT", r"قبة", r"قبه", r"سكاي\s*لايت", r"منور")   # a closed shape so labelled is
#   an opening in the roof membrane: Q-24 ("the circle dome ... add 20cm upturn around circle"), Q-29 (dome = skylight)

MEMBRANE_BASIS = {
    "ROOF": ("RELEASED_METHOD_PIECE", None, "owner Q-24: like a bathroom floor (UP-WP-003): membrane inside the parapet "
                                            "(A) + 0.20 m upturn on parapet, walls and closures; gaps closed (Q-25)"),
    "BALCONY": ("PROVISIONAL", None, "UP-WP-ROOF-001: drawn exterior space area (owner_finish_scope.exterior_wp_lines)"),
    "POOL": ("HELD", "POOL_NO_MEMBRANE_RULE", "no Urban rule makes a pool a membrane row; pool concrete is measured in "
                                              "the concrete ledger"),
    "GARDEN": ("HELD", "EXTERIOR_SCOPE_UNRESOLVED", "knowledge 1.5.0 OQ-04: exterior yard scope not decided"),
    "VOID": ("UNSUPPORTED", "VOID_OPEN_TO_BELOW", "a void is open to below: excluded by rule"),
}


# ------------------------------------------------------------------------------------------------- items -> lines

def _f(it, k, i):
    return it[k] if isinstance(it, dict) else getattr(it, k) if hasattr(it, k) else it[i]


def _parts(it):
    return _f(it, "source_id", 0), _f(it, "kind", 1), tuple(_f(it, "geometry", 2)), _f(it, "role", 3)


def _arc_pts(cx, cy, r, a0, a1, sag):
    sweep = a1 - a0
    step = 2 * math.acos(max(-1.0, 1 - sag / r)) if r > sag else sweep
    n = max(2, int(math.ceil(abs(sweep) / max(step, 1e-9))))
    return [(cx + r * math.cos(a0 + sweep * i / n), cy + r * math.sin(a0 + sweep * i / n)) for i in range(n + 1)]


def _line(kind, g, sag):
    if kind == "SEGMENT":
        return LineString([(g[0], g[1]), (g[2], g[3])])
    if kind == "ARC":
        return LineString(_arc_pts(*g, sag))
    if kind == "CIRCLE":
        pts = _arc_pts(g[0], g[1], g[2], 0.0, 2 * math.pi, sag)
        return LineString(pts[:-1] + [pts[0]])            # exactly closed ring
    raise ValueError(f"unknown boundary item kind {kind!r}")


def items_of_layer(ents, layer, role="OWN"):
    """BoundaryItem-like tuples (source_id, kind, geometry, role) of one layer from the intake entities
    (segments {"id","a","b"}, arcs {"id","c","r","s","e","dir"}, circles {"id","c","r"})."""
    out = []
    for s in ents.get("segments", ()):
        if s.get("layer") == layer and tuple(s["a"]) != tuple(s["b"]):
            out.append((s["id"], "SEGMENT", (s["a"][0], s["a"][1], s["b"][0], s["b"][1]), role))
    for a in ents.get("arcs", ()):
        if a.get("layer") == layer:
            cx, cy = a["c"]
            a0 = math.atan2(a["s"][1] - cy, a["s"][0] - cx)
            a1 = math.atan2(a["e"][1] - cy, a["e"][0] - cx)
            if a.get("dir") == "CW":
                a0, a1 = a1, a0
            if a1 <= a0:
                a1 += 2 * math.pi
            out.append((a["id"], "ARC", (cx, cy, a["r"], a0, a1), role))
    for c in ents.get("circles", ()):
        if c.get("layer") == layer:
            out.append((c["id"], "CIRCLE", (c["c"][0], c["c"][1], c["r"]), role))
    return out


# ------------------------------------------------------------------------------------------------- closures

def _free_end_rays(own, alll, tree, snap):
    """(segment source id, end point, unit direction) of each straight own-layer line end that touches no other line."""
    out = []
    for sid, kind, g, _r, ln in own:
        if kind != "SEGMENT":
            continue
        (x1, y1), (x2, y2) = (g[0], g[1]), (g[2], g[3])
        L = math.hypot(x2 - x1, y2 - y1)
        if L <= snap:
            continue
        for (px, py), (dx, dy) in (((x1, y1), ((x1 - x2) / L, (y1 - y2) / L)), ((x2, y2), ((x2 - x1) / L, (y2 - y1) / L))):
            P = Point(px, py)
            if any(alll[j][4] is not ln and alll[j][4].distance(P) <= snap for j in tree.query(P.buffer(snap))):
                continue
            out.append((sid, (px, py), (dx, dy), ln))
    return out


def _closures(own, alll, openings, reach, snap):
    geos = [x[4] for x in alll]
    tree = STRtree(geos)
    op_tree = STRtree([o[2] for o in openings]) if openings else None
    found, refused = [], []
    for sid, (px, py), (dx, dy), ln in _free_end_rays(own, alll, tree, snap):
        ray = LineString([(px + dx * snap, py + dy * snap), (px + dx * reach, py + dy * reach)])
        best = None
        for j in tree.query(ray.buffer(snap)):
            g = geos[j]
            if g is ln or g.distance(ray) > snap:
                continue
            hit = g.intersection(ray)
            pts = [hit] if hit.geom_type == "Point" else list(getattr(hit, "geoms", [])) if not hit.is_empty else []
            ds = [math.hypot(p.x - px, p.y - py) for p in pts if p.geom_type == "Point"]
            if not ds:                                     # grazes within snap without crossing (rotated corners)
                ds = [Point(px, py).distance(g)]
            d = min(ds)
            if best is None or d < best[0] - snap:
                best = (d, [alll[j]])
            elif abs(d - best[0]) <= snap:
                best[1].append(alll[j])
        if best is None:
            continue
        d, metas = best
        seg = LineString([(px, py), (px + dx * d, py + dy * d)])
        rec = {"from_line": sid, "length_du": d, "meets": sorted({(m[3], m[0]) for m in metas}), "segment": seg}
        on = [openings[k] for k in (op_tree.query(seg.buffer(snap)) if op_tree is not None else ())
              if openings[k][2].distance(seg) <= snap]
        if on:
            rec["openings_on_gap"] = sorted({(o[1], o[0]) for o in on})
            refused.append(rec)
        else:
            found.append(rec)
    return found, refused


# ------------------------------------------------------------------------------------------------- one face

def _noded(lines, grid):
    """node the lines on a grid far below any drafting size (SNAP_M / 10): endpoints that coincide up to float error
    (an arc ending on a line end, a rotated corner) join; nothing of drawing size is moved or closed."""
    return shapely.union_all(lines, grid_size=grid) if grid else unary_union(lines)


def _face_of(lines, x, y, grid=None):
    pt = Point(x, y)
    for p in polygonize(_noded(lines, grid)):
        if p.contains(pt):
            return p
    return None


def _classify_ring(coords, tagged, tree, snap):
    """length per class along a ring; each piece takes the class of the line it lies on (closure > own > building)."""
    out = defaultdict(float)
    srcs = defaultdict(set)
    pri = {"CLOSURE": 0, "OWN": 2}                 # a piece on a building line and an own line is a building edge
    for a, b in zip(coords, coords[1:]):
        seg = LineString([a, b])
        if seg.length == 0:
            continue
        m = seg.interpolate(0.5, normalized=True)
        hits = [tagged[j] for j in tree.query(m.buffer(snap)) if tagged[j][4].distance(m) <= snap]
        if not hits:
            out["other"] += seg.length
            continue
        h = min(hits, key=lambda t: pri.get(t[1], 1))
        cls = {"CLOSURE": "closure", "OWN": "own_layer_edge"}.get(h[1], "building")
        out[cls] += seg.length
        srcs[cls].add(h[0])
    return out, srcs


def _band_widths(face, own_lines, reach, snap):
    """per own-layer edge piece: the distance to the first parallel own-layer line outside the face (measured)."""
    widths = defaultdict(float)
    tree = STRtree(own_lines) if own_lines else None
    ext = list(face.exterior.coords)
    filled = Polygon(face.exterior)
    for a, b in zip(ext, ext[1:]):
        seg = LineString([a, b])
        if seg.length <= 50 * snap or tree is None:
            continue
        m = seg.interpolate(0.5, normalized=True)
        if not any(own_lines[j].distance(m) <= snap for j in tree.query(m.buffer(snap))):
            continue                                        # not an own-layer edge
        ux, uy = (b[0] - a[0]) / seg.length, (b[1] - a[1]) / seg.length
        w = None
        for nx, ny in ((uy, -ux), (-uy, ux)):
            if filled.contains(Point(m.x + nx * 20 * snap, m.y + ny * 20 * snap)):
                continue
            ray = LineString([(m.x + nx * 2 * snap, m.y + ny * 2 * snap), (m.x + nx * reach, m.y + ny * reach)])
            ds = []
            for j in tree.query(ray):
                g = own_lines[j]
                if g.distance(m) <= snap or not g.intersects(ray):
                    continue
                hit = g.intersection(ray)
                ds += [m.distance(p) for p in ([hit] if hit.geom_type == "Point" else getattr(hit, "geoms", []))]
            if ds:
                w = min(ds)
        widths[None if w is None else round(w, 6)] += seg.length
    return widths


def _measure(face, tagged, own_lines, unit_m, reach, snap):
    tree = STRtree([t[4] for t in tagged])
    u, u2 = unit_m, unit_m * unit_m
    ext, ext_src = _classify_ring(list(face.exterior.coords), tagged, tree, snap)
    holes = []
    for k, ring in enumerate(face.interiors):
        cls, src = _classify_ring(list(ring.coords), tagged, tree, snap)
        hp = Polygon(ring)
        holes.append({"hole": k, "area_m2": round(hp.area * u2, 3), "perimeter_lm": round(ring.length * u, 3),
                      "lines": sorted(set().union(*src.values())) if src else [], "polygon_du": hp})
    filled = Polygon(face.exterior)
    widths = _band_widths(face, own_lines, reach, snap)
    known = {w: L for w, L in widths.items() if w is not None}
    w_dom = max(known, key=known.get) if known else None
    B = None
    if w_dom is not None:
        own_edges = []
        for a, b in zip(list(face.exterior.coords), list(face.exterior.coords)[1:]):
            seg = LineString([a, b])
            m = seg.interpolate(0.5, normalized=True)
            if seg.length == 0:
                continue
            hits = [tagged[j] for j in tree.query(m.buffer(snap)) if tagged[j][4].distance(m) <= snap]
            if hits and all(h[1] in ("OWN", "CLOSURE") for h in hits):    # parapet edges and their closures widen
                own_edges.append(seg)
        runs = linemerge(unary_union(own_edges)) if own_edges else None
        runs = list(getattr(runs, "geoms", [runs])) if runs is not None else []
        band = unary_union([r.buffer(w_dom, cap_style="flat", join_style="mitre") for r in runs]).difference(filled)
        band = unary_union([p for p in getattr(band, "geoms", [band]) if not p.is_empty and p.distance(filled) <= snap])
        Bg = unary_union([filled, band]).difference(unary_union([h["polygon_du"] for h in holes]) if holes else Polygon())
        Bg = unary_union([g for g in getattr(Bg, "geoms", [Bg]) if g.area * u2 >= 1e-3])
        Bo = Bg.buffer(1e-3 / u, join_style="mitre").buffer(-2e-3 / u, join_style="mitre").buffer(1e-3 / u, join_style="mitre")
        B = {"band_width_m": round(w_dom * u, 3), "area_m2": round(Bg.area * u2, 3),
             "outer_perimeter_lm": round(sum(p.exterior.length for p in getattr(Bo, "geoms", [Bo]) if not p.is_empty) * u, 3)}
    return {"A_net_m2": round(face.area * u2, 3), "A_filled_m2": round(filled.area * u2, 3),
            "A_perimeter_lm": {k: round(v * u, 3) for k, v in sorted(ext.items())},
            "A_outer_perimeter_lm": round(face.exterior.length * u, 3),
            "own_edge_band_m_by_length": {("none" if w is None else str(round(w * u, 3))): round(L * u, 3)
                                          for w, L in sorted(widths.items(), key=lambda t: (t[0] is None, t[0] or 0))},
            "B_review_only": B, "holes": holes}


# ------------------------------------------------------------------------------------------------- inner shapes

def _inner_treatment(hole, texts, facts):
    import re
    hp = hole["polygon_du"]
    inside = [t for t in texts if hp.contains(Point(t["x"], t["y"]))]
    for t in inside:
        v = (t.get("value") or t.get("text") or "").upper()
        if any(re.search(p, v) for p in OPENING_WORDS):
            return "OPENING", f"label '{t.get('id')}' inside the shape names a dome / skylight (owner Q-24, Q-29)"
    for sid in hole["lines"]:
        f = ((facts or {}).get("inner_shapes") or {}).get(sid)
        if f:
            return f["treatment"], "project fact: " + str(f.get("source"))
    return None, "INNER_SHAPE_UNIDENTIFIED: no label or project fact says what the closed shape is (opening, dome, " \
                 "plinth, tank base): whether the membrane runs under it is not decided"


# ------------------------------------------------------------------------------------------------- the trace

def _norm_openings(openings):
    out = []
    for o in openings or ():
        if o.get("polygon"):
            g = Polygon(o["polygon"])
            g = g if g.is_valid and g.area > 0 else LineString(o["polygon"])
        elif o.get("line") is not None:
            g = o["line"]
        elif o.get("segment"):
            x1, y1, x2, y2 = o["segment"]
            g = LineString([(x1, y1), (x2, y2)])
        else:
            continue
        out.append((o.get("id"), o.get("kind"), g))
    return out


def trace(labels, building, layers, unit_m, openings=(), facts=None, reach_m=None, frame=None, texts=None):
    if reach_m is None:
        from engine.source.arch_rooms import THIN_LIMIT_M
        reach_m = THIN_LIMIT_M
    ops = _norm_openings(openings)
    texts = list(texts if texts is not None else labels or ())
    records, passed = [], 0
    for t in labels or ():
        text = t.get("value", t.get("text"))
        cls = RV.classify(text or "")
        if cls["status"] not in ("TYPED", "HELD_COMPOUND") or cls["code"] not in EXTERIOR_CODES:
            passed += 1
            continue
        code = cls["code"]
        rec = {"policy": POLICY, "frame": frame, "text_id": t.get("id"), "text": text, "code": code,
               "candidates": {}, "layer": None, "status": None, "reason": None, "membrane_m2": None,
               "upturn_lm": None, "upturn_m2": None, "held_part_m2": None, "basis": None}
        if not unit_m or unit_m <= 0:
            rec.update(status="HELD", reason="UNITS_MISSING", basis="no drawing units: no length or area converted")
            records.append(rec)
            continue
        if t.get("x") is None or t.get("y") is None:
            rec.update(status="HELD", reason="LABEL_NO_POSITION")
            records.append(rec)
            continue
        snap, reach = SNAP_M / unit_m, reach_m / unit_m
        sag = SAGITTA_M / unit_m
        btag = []
        for it in building or ():
            sid, kind, g, role = _parts(it)
            btag.append((sid, role, kind, g, _line(kind, g, sag)))
        for layer in sorted(layers or {}):
            own = []
            for it in layers[layer]:
                sid, kind, g, _role = _parts(it)
                if kind == "SEGMENT" and math.hypot(g[2] - g[0], g[3] - g[1]) <= snap:
                    continue
                own.append((sid, "OWN", kind, g, _line(kind, g, sag)))
            if not own:
                continue
            alll = [(s, r, None, r, ln) for s, r, k, g, ln in btag] + [(s, "OWN", None, "OWN", ln) for s, _r, k, g, ln in own]
            own5 = [(s, k, g, "OWN", ln) for s, _r, k, g, ln in own]
            found, refused = _closures(own5, [(a[0], a[1], None, a[3], a[4]) for a in alll], ops, reach, snap)
            lines = [a[4] for a in alll] + [c["segment"] for c in found]
            face = _face_of(lines, float(t["x"]), float(t["y"]), snap / 10)
            if face is None:
                if refused:                                 # would a refused gap (opening on it) close the face?
                    f2 = _face_of(lines + [c["segment"] for c in refused], float(t["x"]), float(t["y"]), snap / 10)
                    if f2 is not None:
                        near = [c for c in refused if f2.exterior.distance(c["segment"]) <= snap]
                        rec["candidates"][layer] = {"face_du": None, "gaps_with_opening": _gap_rows(near, unit_m)}
                continue
            refused = [c for c in refused if any(r.distance(c["segment"]) <= snap
                                                 for r in [face.exterior] + list(face.interiors))]
            tagged = [(a[0], a[1], None, None, a[4]) for a in alll] + [("CLOSE|" + c["from_line"], "CLOSURE", None, None, c["segment"]) for c in found]
            m = _measure(face, tagged, [o[4] for o in own], unit_m, reach, snap)
            rings = [face.exterior] + list(face.interiors)
            m["closures"] = _gap_rows([c for c in found if any(
                r.distance(c["segment"].interpolate(0.5, normalized=True)) <= snap for r in rings)], unit_m)
            m["gaps_with_opening"] = _gap_rows(refused, unit_m)
            m["labels_in_face"] = sorted(x.get("id") for x in texts if x.get("x") is not None and
                                         face.contains(Point(float(x["x"]), float(x["y"]))))
            m["face_du"] = face
            rec["candidates"][layer] = m
        _decide(rec, code, texts, facts, unit_m)
        _one_face_once(rec, records, unit_m)
        records.append(rec)
    rel = [r for r in records if r["status"] in ("RELEASED_METHOD_PIECE", "PROVISIONAL") and r["membrane_m2"] is not None]
    summary = {"policy": POLICY, "frame": frame, "traced": len(records), "texts_passed_by": passed,
               "by_status": {s: sum(1 for r in records if r["status"] == s) for s in
                             ("RELEASED_METHOD_PIECE", "PROVISIONAL", "HELD", "UNSUPPORTED")},
               "membrane_m2_by_code": {c: round(sum(r["membrane_m2"] for r in rel if r["code"] == c), 3)
                                       for c in sorted({r["code"] for r in rel})},
               "roof_upturn_lm": round(sum(r["upturn_lm"] for r in rel if r["code"] == "ROOF"), 3),
               "held_part_m2": round(sum(r.get("held_part_m2") or 0 for r in rel), 3),
               "labels_counted_with_another": sum(1 for r in records if r.get("counted_with")),
               "reach_m": reach_m, "rules": list(RULES), "owner_answers": list(OWNER_ANSWERS)}
    assert sum(summary["by_status"].values()) == len(records)          # every exterior label reported once
    return {"records": records, "summary": summary}


def _one_face_once(rec, earlier, unit_m):
    """two labels in one face (e.g. two ROOF texts on one roof) measure that face once: the later label keeps its
    status and geometry but carries no quantity (counted_with = the first label's id); never counted twice."""
    lay = rec.get("layer")
    f = (rec["candidates"].get(lay) or {}).get("face_du") if lay else None
    if f is None:
        return
    tol = (1e-3 / unit_m) ** 2 * 100
    for e in earlier:
        g = (e["candidates"].get(e.get("layer")) or {}).get("face_du") if e.get("layer") else None
        if g is not None and e.get("counted_with") is None and abs(g.area - f.area) <= tol and \
                f.symmetric_difference(g).area <= tol:
            rec["counted_with"] = e["text_id"]
            for k in ("membrane_m2", "upturn_lm", "upturn_m2", "held_part_m2", "upturn_round_openings_lm"):
                if rec.get(k) is not None:
                    rec[k] = None
            rec["gap_cover"] = []
            return


def _gap_rows(rows, unit_m):
    return [{"from_line": r["from_line"], "length_m": round(r["length_du"] * unit_m, 3),
             "meets": [m[0] for m in r["meets"]], "meets_lines": [m[1] for m in r["meets"]],
             **({"openings_on_gap": [list(o) for o in r["openings_on_gap"]]} if r.get("openings_on_gap") else {})}
            for r in rows]


def _decide(rec, code, texts, facts, unit_m):
    """geometry status first (which face, if any), then the measurement status from the owner rule of the code."""
    st, reason, basis = MEMBRANE_BASIS[code]
    cands = {k: v for k, v in rec["candidates"].items() if v.get("face_du") is not None}
    faces = {}
    for k, v in cands.items():
        faces.setdefault((round(v["A_net_m2"], 2), round(v["A_filled_m2"], 2)), []).append(k)
    gaps = [g for v in rec["candidates"].values() for g in v.get("gaps_with_opening", ())]
    if not cands:
        geo, why = ("GAP_HAS_OPENING", "a gap round the label has an opening element drawn on it (owner Q-25: not "
                    "closed, reported)") if gaps else ("NO_CLOSING_LAYER", "no OTHER layer closes a face round the label "
                                                       "within the search reach: no area (never 0)")
    elif len(faces) > 1:
        geo, why = "AMBIGUOUS_BOUNDARY_LAYER", "different OTHER layers close different faces round the label: " + \
            "; ".join(f"{ls} -> {k[0]} m2" for k, ls in sorted(faces.items()))
    elif gaps:
        geo, why = "GAP_HAS_OPENING", "a gap on the face edge has an opening element drawn on it (owner Q-25: not closed)"
    else:
        geo, why = "CLOSED", None
    rec.update(geometry_status=geo, geometry_basis=why)
    if geo != "CLOSED" or code not in ("ROOF", "BALCONY"):
        if code in ("ROOF", "BALCONY"):
            rec.update(status="HELD", reason=geo, basis=why)
        else:
            rec.update(status=st, reason=reason, basis=basis)
        if geo == "CLOSED":
            rec["layer"] = sorted(cands)[0]
        return
    layer = sorted(cands)[0]
    c = cands[layer]
    rec["layer"] = layer
    rec["same_face_layers"] = sorted(cands)
    inner_rows, opening_lm, held_m2 = [], 0.0, 0.0
    for h in c["holes"]:
        tr, why_h = _inner_treatment(h, texts, facts)
        row = {k: h[k] for k in ("hole", "area_m2", "perimeter_lm", "lines")}
        row.update(treatment=tr or "HELD", basis=why_h)
        if tr == "OPENING":
            opening_lm += h["perimeter_lm"]
        elif tr != "MEMBRANE_UNDER":
            held_m2 += h["area_m2"]
        inner_rows.append(row)
    c["inner_shapes"] = inner_rows
    membrane = c["A_net_m2"] + sum(r["area_m2"] for r in inner_rows if r["treatment"] == "MEMBRANE_UNDER")
    perim = sum(c["A_perimeter_lm"].values())
    held = {"held_part_m2": round(held_m2, 3) if held_m2 else None,
            "held_part_reason": "INNER_SHAPE_UNIDENTIFIED" if held_m2 else None}
    if code == "ROOF":
        up = perim + opening_lm
        rec.update(status=st, reason=None, basis=basis, membrane_m2=round(membrane, 3), upturn_lm=round(up, 3),
                   upturn_m2=round(up * UPTURN_H_M, 3), upturn_round_openings_lm=round(opening_lm, 3), **held,
                   gap_cover=[{"from_line": g["from_line"], "gap_m": g["length_m"], "lap_m": GAP_LAP_M,
                               "upturn_m": UPTURN_H_M} for g in c["closures"]])
    else:
        rec.update(status=st, reason=None, basis=basis, membrane_m2=round(membrane, 3), upturn_lm=round(perim, 3),
                   upturn_m2=None, upturn_status="HELD", upturn_reason="EXTERIOR_WP_UPTURN_BY_SPECIFICATION", **held)


def report_rows(result):
    """flat rows (no geometry, no coordinates) for a census table or a JSON report."""
    out = []
    for r in result["records"]:
        row = {k: v for k, v in r.items() if k != "candidates"}
        row["candidates"] = {}
        for lay, c in r["candidates"].items():
            row["candidates"][lay] = {k: ([{kk: vv for kk, vv in h.items() if kk != "polygon_du"} for h in v]
                                          if k == "holes" else v)
                                      for k, v in c.items() if k != "face_du"}
        out.append(row)
    return out


# ------------------------------------------------------------------------------------------------- layer-role risk

def layer_role_check(roles, layer_items, labels, unit_m=None):
    """T-062 risk: with no layer map the run may type a parapet layer as THE wall layer and the real wall layer OTHER.
    Symptom tested (no names): per layer, a room label is 'separated' when the innermost face of that layer's lines
    round it holds no exterior label. RISK when a WALL-typed layer encloses an exterior label (roof, balcony, pool,
    garden) and an OTHER-typed layer separates more room labels than it does: the layer roles must then be confirmed
    before any room or exterior quantity of the frame is released. Diagnostic only; nothing is changed."""
    grid = (SNAP_M / 10 / unit_m) if unit_m else None
    lab = []
    for t in labels or ():
        if t.get("x") is None:
            continue
        c = RV.classify(t.get("value", t.get("text")) or "")
        if c["status"] in ("TYPED", "HELD_COMPOUND") and c["code"]:
            lab.append((Point(float(t["x"]), float(t["y"])), c["code"] in EXTERIOR_CODES))

    def score(items):
        lines = [_line(k, g, (SAGITTA_M / unit_m) if unit_m else 1e-6) for _s, k, g, _r in (_parts(i) for i in items)]
        polys = list(polygonize(_noded(lines, grid))) if lines else []
        ext = sep = 0
        for pt, is_ext in lab:
            own = [p for p in polys if p.contains(pt)]
            if not own:
                continue
            if is_ext:
                ext += 1
                continue
            inner = min(own, key=lambda p: p.area)
            if not any(e and inner.contains(q) for q, e in lab):
                sep += 1
        return ext, sep
    others = {lay: score(it) for lay, it in layer_items.items() if roles.get(lay) == "OTHER" and it}
    out = []
    for lay, it in layer_items.items():
        if roles.get(lay) != "WALL" or not it:
            continue
        ext, sep = score(it)
        rivals = sorted(o for o, (_e, s2) in others.items() if s2 > sep)
        risk = ext > 0 and bool(rivals)
        out.append({"wall_layer": lay, "exterior_labels_enclosed": ext, "room_labels_separated": sep,
                    "other_layers_separating_more_rooms": rivals, "status": "RISK" if risk else "OK",
                    "reason": "LAYER_ROLE_PARAPET_AS_WALL" if risk else None})
    return out


def apply_role_check(result, checks):
    """a frame whose layer roles are at RISK releases nothing: every released or provisional record becomes HELD
    LAYER_ROLE_RISK (its geometry and figures kept for review); the summary is recounted."""
    risk = [c for c in checks or () if c.get("status") == "RISK"]
    if not risk:
        return result
    for r in result["records"]:
        if r["status"] in ("RELEASED_METHOD_PIECE", "PROVISIONAL"):
            r.update(status="HELD", reason="LAYER_ROLE_RISK", held_figures={k: r.get(k) for k in
                     ("membrane_m2", "upturn_lm", "upturn_m2", "held_part_m2")},
                     basis="layer roles of the frame at risk (" + ", ".join(c["wall_layer"] for c in risk) +
                           " typed WALL may be a parapet layer): confirm the layer map first")
            for k in ("membrane_m2", "upturn_lm", "upturn_m2", "held_part_m2"):
                r[k] = None
    sm = result["summary"]
    sm["by_status"] = {s: sum(1 for r in result["records"] if r["status"] == s) for s in sm["by_status"]}
    sm["membrane_m2_by_code"], sm["roof_upturn_lm"], sm["held_part_m2"] = {}, 0.0, 0.0
    sm["layer_role_risk"] = [c["wall_layer"] for c in risk]
    return result


# ------------------------------------------------------------------------------------------------- run adapter

def inputs_from_spaces(ents, roles, items, spaces_result=None):
    """the trace inputs of ONE plan region from what arch_rooms.spaces sees (read only): its entities, layer roles,
    the items of its first boundary arrangement and its result (recognised openings). Door-role arcs (swings) count as
    opening elements on a gap. Returns (building, layers, openings, texts)."""
    building = [_parts(i) for i in items]
    layers = {lay: items_of_layer(ents, lay) for lay, r in sorted((roles or {}).items()) if r == "OTHER"}
    layers = {k: v for k, v in layers.items() if v}
    openings = []
    for o in (spaces_result or {}).get("openings") or ():
        try:
            u, n = o["u"], o["n"]
            pts = [(s * u[0] + t * n[0], s * u[1] + t * n[1]) for s, t in
                   ((o["s0"], o["o0"]), (o["s1"], o["o0"]), (o["s1"], o["o1"]), (o["s0"], o["o1"]))]
        except (KeyError, TypeError):
            continue
        openings.append({"id": o.get("opening_id"), "kind": o.get("kind") or "OPENING", "polygon": pts})
    door_layers = {lay for lay, r in (roles or {}).items() if r == "DOOR"}
    for a in ents.get("arcs", ()):
        if a.get("layer") in door_layers:
            sid, kind, g, _r = items_of_layer({"arcs": [a]}, a["layer"])[0]
            openings.append({"id": sid, "kind": "DOOR_SWING", "polygon": None,
                             "line": _line(kind, g, 1e-3 * max(1.0, g[2] * 1e-3))})
    return building, layers, openings, list(ents.get("texts") or ())
