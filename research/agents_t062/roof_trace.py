"""T-062 diagnostic (read only): why a room label lies in no closed room face, and what the drawing around it measures.

For every room-vocabulary label that the ARCH_TAKEOFF_V2.9 run leaves in no room (tools/label_census.py, status
SILENT_OMISSION / NO_ROOM) this script:
  1. tests the label against the run's OWN boundary set (the first arrangement `arch_rooms.spaces` builds: lines of the
     WALL / COLUMN / WINDOW layers, opening thresholds, wall caps, door closures); a label in no bounded face of that
     arrangement lies in the unbounded face: no room can carry it (`topology.sites_of` returns bounded faces only);
  2. for each layer the run typed OTHER, adds that layer's lines to the same arrangement and reports whether a bounded
     face now holds the label, before and after the hand closure below, with the face's boundary roles;
  3. hand closure (diagnostic only, never an engine rule): a line of that layer whose end touches no boundary line is
     extended along its own direction to the first boundary line within arch_rooms.THIN_LIMIT_M (0.45 m, the engine's
     own "inside a wall thickness" limit); every extension on the face is listed with its length and what it meets;
  4. measures the face: A = the area inside the drawn edge (net of closed circles inside it, which are listed), its
     perimeter split into the layer's own edges (the parapet / edge line), building edges (wall, column, window,
     threshold) and closures; B = A widened to the next line of the same layer drawn parallel outside each edge
     (the edge band width is MEASURED per edge, never assumed; edges with no parallel line are not widened).
Nothing is decided here: which of A or B a rule means is an owner question (UP-WP-ROOF-001 says "the drawn exterior
space area"). Output: counts, entity handles, areas and lengths only (no coordinates, no text of the drawing).

Usage (Python 3.11 venv, repo root):
  python research/agents_t062/roof_trace.py <drawing.dxf> <out.json> [--layer-roles roles.json]
"""
from __future__ import annotations

import collections
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shapely.geometry import LineString, Point, Polygon  # noqa: E402
from shapely.ops import linemerge, nearest_points, unary_union  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

from engine.source import arch_rooms as AR  # noqa: E402
from engine.source import arch_v27 as V27  # noqa: E402
from engine.source import member_detection as MD  # noqa: E402
from engine.source import topology as TP  # noqa: E402

BUILDING = {"WALL", "COLUMN", "WINDOW", "WINDOW_THRESHOLD", "DOOR_THRESHOLD", "PASSAGE_THRESHOLD", "WALL_CAP",
            "DOOR_CLOSURE"}
NOT_GEOMETRY = {"TEXT"}


def capture(drawing, method="ARCH_TAKEOFF_V2.9", layer_roles=None):
    """run the architectural route once; keep, per plan region, the inputs of arch_rooms.spaces and the item list of its
    first arrangement (pass 1). The patched functions are restored afterwards."""
    from tools import urban_boq_m9 as M
    cap, cur = {}, [None]
    o_spaces, o_build = AR.spaces, TP.build

    def spaces(ents, roles, unit_m, **kw):
        cur[0] = kw.get("region_id")
        cap[cur[0]] = {"builds": []}
        r = o_spaces(ents, roles, unit_m, **kw)
        cap[cur[0]].update(ents=ents, roles=roles, unit_m=unit_m, res=r)
        cur[0] = None
        return r

    def build(items, eps):
        if cur[0] is not None:
            cap[cur[0]]["builds"].append((list(items), eps))
        return o_build(items, eps)
    AR.spaces, TP.build = spaces, build
    try:
        res = M.arch_compute(str(drawing), method=method, layer_roles=layer_roles)
    finally:
        AR.spaces, TP.build = o_spaces, o_build
    return res, cap


def _geom(it):
    if it.kind == "SEGMENT":
        x1, y1, x2, y2 = it.geometry
        return LineString([(x1, y1), (x2, y2)])
    if it.kind == "ARC":
        cx, cy, r, a0, a1 = it.geometry
        n = max(8, int((a1 - a0) * 32))
        return LineString([(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n))
                           for i in range(n + 1)])
    cx, cy, r = it.geometry
    return Point(cx, cy).buffer(r, 128).exterior


def layer_items(ents, layer, eps, role):
    out = [AR._seg_item(s, role) for s in ents["segments"] if s["layer"] == layer and math.dist(s["a"], s["b"]) > eps]
    out += [AR._arc_item(a, role) for a in ents["arcs"] if a["layer"] == layer]
    out += [TP.BoundaryItem(c["id"], "CIRCLE", (c["c"][0], c["c"][1], c["r"]), role + "_CIRCLE")
            for c in ents.get("circles", ()) if c["layer"] == layer]
    return out


def closures(base, extra, eps, max_len):
    """hand closure: each straight line of `extra` whose end touches nothing is extended along its own direction to the
    first line of base + extra within max_len (drawing units)."""
    hard = list(base) + list(extra)
    geos = [_geom(i) for i in hard]
    tree = STRtree(geos)
    own = {id(i) for i in extra}
    out = []
    for k, it in enumerate(hard):
        if id(it) not in own or it.kind != "SEGMENT":
            continue
        x1, y1, x2, y2 = it.geometry
        L = math.hypot(x2 - x1, y2 - y1)
        for (px, py), (dx, dy) in (((x1, y1), ((x1 - x2) / L, (y1 - y2) / L)), ((x2, y2), ((x2 - x1) / L, (y2 - y1) / L))):
            P = Point(px, py)
            if any(j != k and geos[j].distance(P) <= 2 * eps for j in tree.query(P.buffer(2 * eps))):
                continue
            ray = LineString([(px + dx * 2 * eps, py + dy * 2 * eps), (px + dx * max_len, py + dy * max_len)])
            hits = []
            for j in tree.query(ray.buffer(2 * eps)):          # within 2 eps of the ray: a corner grazed by
                if j != k and geos[j].distance(ray) <= 2 * eps:   # float error still counts (rotated drawings)
                    q = nearest_points(geos[j], ray)[1]
                    hits.append((P.distance(q), hard[j].role, hard[j].source_id))
            if hits:
                d = min(h[0] for h in hits)
                meets = sorted({(h[1], h[2]) for h in hits if abs(h[0] - d) <= 2 * eps})
                out.append((TP.BoundaryItem("CLOSE|" + it.source_id, "SEGMENT", (px, py, px + dx * d, py + dy * d),
                                            "CLOSURE"), it.source_id, d, meets))
    return out


def _faces(arr, unit_m):
    sag = V27.ARC_SAGITTA_M / unit_m
    out = []
    for st in TP.sites_of(arr, "T062", "T062"):
        out.append((st, V27.cycle_points(arr, st["cycle"], sag), [V27.cycle_points(arr, h, sag) for h in st["hole_cycles"]]))
    return out


def _holding(faces, x, y):
    hit = [f for f in faces if len(f[1]) > 2 and MD.point_in_poly(x, y, f[1]) and
           not any(len(h) > 2 and MD.point_in_poly(x, y, h) for h in f[2])]
    return min(hit, key=lambda f: f[0]["area"]) if hit else None


def _edge_len(arr, ei):
    e = arr.edges[ei]
    if e["kind"] == "S":
        return math.dist(arr.nodes[e["n0"]], arr.nodes[e["n1"]])
    return e["prim"].r * (e["t1"] - e["t0"])


def _outer_length(g, r):
    """outer boundary length after a 1 mm closing + opening (float hairlines and spikes at joined bands removed)."""
    g = g.buffer(r, join_style="mitre").buffer(-2 * r, join_style="mitre").buffer(r, join_style="mitre")
    return sum(p.exterior.length for p in getattr(g, "geoms", [g]) if not p.is_empty)


def measure(arr, face, layer_lines, unit_m, band_max, circle_items=()):
    """A, its perimeter split and B (A widened by the measured band of each own-layer edge)."""
    st, poly, holes = face
    sag = V27.ARC_SAGITTA_M / unit_m
    split = collections.defaultdict(float)
    own_chains, circle_len, circ_src = [], 0.0, set()
    for ei, fw in st["cycle"]:
        roles = set(arr.edges[ei]["roles"])
        ln = _edge_len(arr, ei) * unit_m
        if any(r.endswith("_CIRCLE") for r in roles):
            circle_len += ln
            circ_src.update(arr.edges[ei]["sources"])
            continue
        if roles & BUILDING:
            split["building"] += ln
        elif "CLOSURE" in roles:
            split["closure"] += ln
            own_chains.append(LineString(V27.cycle_points(arr, [(ei, fw)], sag) + [arr.nodes[arr.edges[ei]["n1" if fw else "n0"]]]))
        elif "OWN" in roles:
            split["own_layer_edge"] += ln
            own_chains.append(LineString(V27.cycle_points(arr, [(ei, fw)], sag) + [arr.nodes[arr.edges[ei]["n1" if fw else "n0"]]]))
        else:
            split["other"] += ln
    outer = Polygon(poly, [h for h in holes if len(h) > 2]).buffer(0)   # holes and pinched loops excluded
    circles_on = [{"circle": i.source_id, "radius_m": round(i.geometry[2] * unit_m, 3),
                   "area_m2": round(math.pi * (i.geometry[2] * unit_m) ** 2, 3)} for i in circle_items if i.source_id in circ_src]
    A_net = st["area"] * unit_m ** 2
    # measured band: for each own edge, the first line of the same layer parallel outside it within band_max
    tree = STRtree([g for g in layer_lines])
    widths = []
    pieces = []
    for ch in own_chains:
        if ch.length * unit_m < 0.05:
            continue
        m = ch.interpolate(0.5, normalized=True)
        a, b = ch.coords[0], ch.coords[-1]
        L = math.dist(a, b) or 1.0
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        w = None
        for nx, ny in ((uy, -ux), (-uy, ux)):
            if outer.contains(Point(m.x + nx * 1e-3 / unit_m * 20, m.y + ny * 1e-3 / unit_m * 20)):
                continue
            ray = LineString([(m.x + nx * 1e-6, m.y + ny * 1e-6), (m.x + nx * band_max, m.y + ny * band_max)])
            ds = [Point(m.x, m.y).distance(layer_lines[j].intersection(ray)) for j in tree.query(ray)
                  if layer_lines[j].intersects(ray) and layer_lines[j].distance(Point(m.x, m.y)) > 1e-6]
            ds = [d for d in ds if d * unit_m > 0.01]
            if ds:
                w = min(ds)
        widths.append((round(w * unit_m, 3) if w else None, ch.length * unit_m))
        if w:
            pieces.append(ch.buffer(w, cap_style="flat", join_style="mitre"))
    filled = Polygon(outer.exterior) if outer.geom_type == "Polygon" else unary_union([Polygon(g.exterior) for g in outer.geoms])
    inner_holes = filled.difference(outer)                               # closed shapes inside A (domes, voids)

    def widen(parts):
        band = unary_union(parts).difference(filled) if parts else Polygon()
        band = unary_union([p for p in getattr(band, "geoms", [band]) if not p.is_empty and p.distance(filled) * unit_m < 0.01])
        out = unary_union([filled, band]).difference(inner_holes)
        return unary_union([g for g in getattr(out, "geoms", [out]) if g.area * unit_m ** 2 >= 1e-3])   # drop slivers
    B = widen(pieces)
    wsum = collections.defaultdict(float)
    for w, ln in widths:
        wsum[str(w)] += ln
    # the dominant measured width (the width found on the longest share of the edge), applied to every own edge
    known = {k: v for k, v in wsum.items() if k != "None"}
    w_dom = float(max(known, key=known.get)) if known else None
    merged = linemerge(unary_union(own_chains)) if own_chains else None      # one chain per run: mitred corners
    runs = list(getattr(merged, "geoms", [merged])) if merged is not None else []
    B_dom = widen([r.buffer(w_dom / unit_m, cap_style="flat", join_style="mitre") for r in runs]) if w_dom else outer
    return {"A_net_m2": round(A_net, 3), "A_filled_m2": round(filled.area * unit_m ** 2, 3),
            "circle_edges_lm": round(circle_len, 3),
            "A_perimeter_lm": {k: round(v, 3) for k, v in sorted(split.items())},
            "band_width_m_by_length": {k: round(v, 3) for k, v in sorted(wsum.items())},
            "circles_on_face": circles_on,
            "B_first_line_outer_m2": round(B.area * unit_m ** 2, 3),
            "dominant_band_width_m": w_dom,
            "B_dominant_width_outer_m2": round(B_dom.area * unit_m ** 2, 3),
            "B_dominant_width_outer_perimeter_lm": round(_outer_length(B_dom, 1e-3 / unit_m) * unit_m, 3),
            "shapes_inside_A_m2": round(inner_holes.area * unit_m ** 2, 3)}


def trace(res, cap, labels_wanted=None):
    from tools import label_census as LC
    boq, arch, intake = res
    census = LC.census_of_run(res)
    texts = {t["id"]: t for t in intake.get("texts") or ()}
    out = []
    for rec in census["labels"]:
        if rec["status"] != "SILENT_OMISSION" or (labels_wanted and rec["text_id"] not in labels_wanted):
            continue
        c = cap.get(rec["region_id"])
        t = texts[rec["text_id"]]
        row = {"text_id": rec["text_id"], "code": rec["code"], "floor": rec["floor"], "cause": rec["cause"]}
        if not c or not c["builds"]:
            row["stage"] = "NO_ARRANGEMENT (region blocked)"
            out.append(row)
            continue
        items, eps = c["builds"][0]
        u = c["unit_m"]
        base = _holding(_faces(TP.build(items, eps), u), t["x"], t["y"])
        row["engine_boundary_face"] = None if base is None else round(base[0]["area"] * u * u, 3)
        row["stage"] = ("UNBOUNDED_FACE: the label lies outside every closed face of the WALL / COLUMN / WINDOW "
                        "arrangement (engine/source/arch_rooms.py:1082-1096 builds it from those layers only; "
                        "engine/source/topology.py:594 sites_of keeps bounded faces only)") if base is None else \
            "IN_A_FACE_NOT_A_ROOM"
        cands = []
        for layer in sorted(l for l, r in c["roles"].items() if r == "OTHER" and l not in NOT_GEOMETRY):
            own = layer_items(c["ents"], layer, eps, "OWN")
            if not own:
                continue
            arr0 = TP.build(items + own, eps)
            f0 = _holding(_faces(arr0, u), t["x"], t["y"])
            cl = closures(items, [i for i in own if i.role == "OWN"], eps, AR.THIN_LIMIT_M / u)
            arr1 = TP.build(items + own + [x[0] for x in cl], eps)
            f1 = _holding(_faces(arr1, u), t["x"], t["y"])
            if f0 is None and f1 is None:
                continue
            cand = {"layer_entities": len(own), "face_without_closure_m2": None if f0 is None else round(f0[0]["area"] * u * u, 3)}
            if f1 is not None:
                st = f1[0]
                on_face = {s for ei, _ in st["cycle"] for s in arr1.edges[ei]["sources"]}
                cand["closures_on_face"] = [{"line": src, "length_m": round(d * u, 3), "meets": [m[0] for m in meets]}
                                            for it, src, d, meets in cl if it.source_id in on_face]
                cand["boundary_roles"] = dict(collections.Counter(r for ei, _ in st["cycle"] for r in arr1.edges[ei]["roles"]))
                cand["boundary_entities_own_layer"] = sorted({s for ei, _ in st["cycle"] for s in arr1.edges[ei]["sources"]
                                                             if "OWN" in arr1.edges[ei]["roles"]})
                lines = [_geom(i) for i in own if i.role == "OWN"]
                cand.update(measure(arr1, f1, lines, u, AR.THIN_LIMIT_M / u, [i for i in own if i.kind == "CIRCLE"]))
                cand["labels_in_face"] = sorted(x for x, tt in texts.items() if MD.point_in_poly(tt["x"], tt["y"], f1[1])
                                                and not any(len(h) > 2 and MD.point_in_poly(tt["x"], tt["y"], h) for h in f1[2])
                                                and AR.room_word(tt.get("value") or "")[0])
            cands.append((layer, cand))
        row["layers_that_bound_it"] = {k: v for k, v in cands}
        out.append(row)
    return {"policy": "T062_LABEL_FACE_TRACE (diagnostic)", "labels": out, "census_summary": census["summary"]}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("out")
    ap.add_argument("--layer-roles")
    ap.add_argument("--labels", help="comma-separated text ids (default: every label in no room)")
    a = ap.parse_args(argv)
    roles = json.loads(Path(a.layer_roles).read_text()) if a.layer_roles else None
    res, cap = capture(a.drawing, layer_roles=roles)
    rep = trace(res, cap, set(a.labels.split(",")) if a.labels else None)
    Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    for r in rep["labels"]:
        print(r["text_id"], r["code"], r["floor"], r.get("engine_boundary_face"), "|", r["stage"][:16])
        for lay, cnd in r.get("layers_that_bound_it", {}).items():
            print("   layer", lay, {k: cnd.get(k) for k in ("face_without_closure_m2", "A_net_m2", "A_filled_m2", "shapes_inside_A_m2",
                                                           "circles_on_face", "B_first_line_outer_m2", "dominant_band_width_m",
                                                           "B_dominant_width_outer_m2", "B_dominant_width_outer_perimeter_lm",
                                                           "A_perimeter_lm", "band_width_m_by_length",
                                                           "closures_on_face", "labels_in_face")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
