"""T-688 own re-measure of the development villa's 1F slab panels (sheet 'FIRST FLOOR ROOF SLAB', frame FR04 of the
INVENTORY) from the private structural DXF copy, with a noding of its own (not the engine's band / face detector).

Drive "Alsenan chalet project" / 'ST7757 dxf.dxf', decoded with `agent_env.sh decode` into .work/private (never
committed). Writes NUMBERS ONLY to out/T688_OWN_1F_PANELS.json: engine element ids, own face areas, classes; no
coordinate, label text, client name or drawing content.

Noding (own): every LINE / LWPOLYLINE (bulges flattened) / ARC / CIRCLE of the layers that draw member and slab edges
('1', 'S-COL.BON', 'S-BOUN') inside the frame; arcs flattened to a 0.2 mm sagitta; every open segment end extended by
EXT_MM along its own direction (closes unnoded ends that stop short of their carrier); shapely unary_union + polygonize.
Engine cells are located BY POSITION: the M5 1F slab map (committed SVG, one polygon per engine cell) is placed on the
drawing by a scale + offset fitted on the cells whose area is unique, then each engine cell's representative point is
looked up in the own faces (never matched by area alone).

    .work/venv/bin/python -I research/agents_t688/t688_measure.py --dxf .work/private/st7757.dxf [--write]
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INVENTORY = "research/urban_engine_m4_correctness/st7757_route_g/INVENTORY.json"
SVG = "research/urban_engine_m5_concrete_reconciliation/visual/03b_SLAB_MAP_1F.svg"
INDEX = "research/agents_t677/out/LINE_INDEX_V3_0_66.json"
OUT = HERE / "out" / "T688_OWN_1F_PANELS.json"
FRAME, STOREY = "FR04", "1F"
EDGE_LAYERS = ("1", "S-COL.BON", "S-BOUN")
EXT_MM, SAGITTA_MM = 30.0, 0.2


def _layer(e):
    try:
        return e.dxf.layer
    except Exception:  # RTEXT and similar carry no layer attribute
        return None


def read_frame(dxf_path, box):
    import ezdxf
    from shapely.geometry import LineString
    doc = ezdxf.readfile(dxf_path)
    x0, y0, x1, y1 = box

    def inb(p):
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1

    edges, openings, inner = [], [], []
    for e in doc.modelspace():
        lay, t = _layer(e), e.dxftype()
        if lay is None:
            continue
        pts = None
        if t == "LINE":
            pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        elif t in ("ARC", "CIRCLE"):
            pts = [(q.x, q.y) for q in e.flattening(SAGITTA_MM)]
        elif t == "LWPOLYLINE":
            raw = list(e.get_points())
            if any(abs(q[4]) > 1e-12 for q in raw):
                for v in e.virtual_entities():
                    seg = ([(v.dxf.start.x, v.dxf.start.y), (v.dxf.end.x, v.dxf.end.y)] if v.dxftype() == "LINE"
                           else [(q.x, q.y) for q in v.flattening(SAGITTA_MM)])
                    if all(inb(p) for p in seg) and lay in EDGE_LAYERS:
                        edges.append(LineString(seg))
                continue
            pts = [(q[0], q[1]) for q in raw] + ([(raw[0][0], raw[0][1])] if e.closed else [])
        if not pts or len(pts) < 2 or not all(inb(p) for p in pts):
            continue
        g = LineString(pts)
        if lay in EDGE_LAYERS:
            edges.append(g)
        elif lay == "S-OPENING":
            openings.append(g)
        elif lay in ("2", "ST"):
            inner.append(g)
    return edges, openings, inner


def extend(g, d):
    from shapely.geometry import LineString
    c = list(g.coords)
    if d <= 0 or len(c) < 2 or c[0] == c[-1]:
        return g

    def mv(a, b):
        dx, dy = a[0] - b[0], a[1] - b[1]
        n = math.hypot(dx, dy) or 1.0
        return (a[0] + dx / n * d, a[1] + dy / n * d)
    c[0], c[-1] = mv(c[0], c[1]), mv(c[-1], c[-2])
    return LineString(c)


def faces_of(edges, ext=EXT_MM):
    from shapely.ops import polygonize, unary_union
    return list(polygonize(unary_union([extend(g, ext) for g in edges])))


def svg_cells(path):
    txt = (ROOT / path).read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r'<polygon points="([^"]+)"[^>]*><title>(SITE-[0-9a-f]+) ([0-9.]+) m2', txt):
        pts = [tuple(float(v) for v in p.split(",")) for p in m.group(1).split()]
        out[m.group(2)] = {"pts": pts, "m2": float(m.group(3))}
    return out


def fit_transform(cells, faces):
    """scale + offset (y flipped) from the cells whose engine area matches exactly one own face within 0.01 m2."""
    from shapely.geometry import Polygon
    pairs = []
    for cid, c in cells.items():
        if c["m2"] < 2.0:
            continue
        hits = [f for f in faces if abs(f.area / 1e6 - c["m2"]) < 0.01]
        if len(hits) == 1:
            sb, fb = Polygon(c["pts"]).bounds, hits[0].bounds
            pairs.append((sb, fb))
    if len(pairs) < 3:
        raise SystemExit("T-688: fewer than 3 unique cells to place the M5 map on the drawing")
    sx = sum((fb[2] - fb[0]) / (sb[2] - sb[0]) for sb, fb in pairs) / len(pairs)
    sy = sum((fb[3] - fb[1]) / (sb[3] - sb[1]) for sb, fb in pairs) / len(pairs)
    ox = sum(fb[0] - sx * sb[0] for sb, fb in pairs) / len(pairs)
    oy = sum(fb[1] + sy * sb[3] for sb, fb in pairs) / len(pairs)
    return (lambda p: (ox + sx * p[0], oy - sy * p[1])), len(pairs)


def run(dxf_path):
    from shapely.geometry import Point, Polygon
    inv = json.loads((ROOT / INVENTORY).read_text(encoding="utf-8"))[0]
    box = next(f["box"] for f in inv["frames"] if f["frame_id"] == FRAME)
    edges, openings, inner = read_frame(dxf_path, box)
    faces = faces_of(edges)
    cells = svg_cells(SVG)
    tf, n_fit = fit_transform(cells, faces)
    idx = json.loads((ROOT / INDEX).read_text(encoding="utf-8"))
    lines = [x for x in idx["lines"] if x["item_code"] == "STR.CONC.SLAB" and x["element_id"].split(":")[2] == STOREY]
    used, rows = {}, []
    for x in sorted(lines, key=lambda r: r["line_id"]):
        cid = x["element_id"].split(":")[-1]
        c = cells.get(cid)
        own = None
        if c:
            rp = Polygon([tf(p) for p in c["pts"]]).representative_point()
            hits = [i for i, f in enumerate(faces) if f.contains(rp)]
            if len(hits) == 1:
                own = hits[0]
        net = x["measured_net"]
        row = {"line_id": x["line_id"], "engine_cell": cid, "class": x["class"],
               "engine_m3": net, "engine_m2": round(float(net) / 0.16, 6) if net else None,
               "own_face": own, "own_m2": round(faces[own].area / 1e6, 6) if own is not None else None}
        if own is not None:
            used.setdefault(own, []).append(x["line_id"])
        rows.append(row)
    shared = {k: v for k, v in used.items() if len(v) > 1}
    # physical census of the frame's other faces >= 2 m2 (classes by drawn evidence, not by the engine)
    census = []
    from shapely.ops import unary_union
    plan = unary_union([f for f in faces if f.area / 1e6 <= 60.0])
    parts = list(getattr(plan, "geoms", [plan]))
    plan = next(p for p in parts if any(p.contains(faces[k].representative_point()) for k in used))
    for i, f in enumerate(faces):
        a = f.area / 1e6
        if i in used or a < 2.0 or a > 60.0 or not plan.contains(f.representative_point()):
            continue
        pcs = [f.intersection(g) for g in openings]
        pcs = [g for g in pcs if g.length > 1.0]
        n_op = len(pcs)
        if n_op >= 2 and unary_union(pcs).envelope.area / f.envelope.area < 0.8:   # R-T688-1 (b) span
            n_op = 0
        n_in = sum(1 for g in inner if f.intersection(g).length > 1.0)
        mrr = f.minimum_rotated_rectangle
        xs = list(mrr.exterior.coords)
        w = min(math.dist(xs[0], xs[1]), math.dist(xs[1], xs[2]))
        cls = ("STAIR_ZONE" if n_in >= 5 else "OPENING" if n_op >= 2 else "BAND" if w <= 600.0 else "OTHER")
        census.append({"own_face": i, "m2": round(a, 6), "class": cls, "opening_lines": n_op, "inner_lines": n_in,
                       "narrow_width_mm": round(w, 1)})
    rel = [r for r in rows if r["class"] == "RELEASED"]
    return {"schema": "URBAN_T688_OWN_1F_PANELS_V1", "source": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' "
            "(private copy; numbers only)", "frame": FRAME, "noding": {"layers": list(EDGE_LAYERS), "ext_mm": EXT_MM,
            "sagitta_mm": SAGITTA_MM, "faces": len(faces), "placement_cells": n_fit},
            "lines": rows, "shared_faces": shared, "census": sorted(census, key=lambda r: -r["m2"]),
            "released_engine_m2": round(sum(r["engine_m2"] for r in rel), 6),
            "released_own_m2": round(sum(r["own_m2"] for r in rel if r["own_m2"] is not None), 6),
            "released_unlocated": [r["line_id"] for r in rel if r["own_m2"] is None]}


def ground_face(dxf_path, engine_m2=1.14, frame="FR08"):
    """F-V-P18-2: the ground-plan face(s) of the engine cell's area that carry a level mark of their own, with the
    widths of the faces sharing an edge with it (numbers only)."""
    import ezdxf
    from shapely.geometry import Point
    inv = json.loads((ROOT / INVENTORY).read_text(encoding="utf-8"))[0]
    box = next(f["box"] for f in inv["frames"] if f["frame_id"] == frame)
    edges, _, _ = read_frame(dxf_path, box)
    faces = faces_of([e for e in edges], ext=1.0)
    doc = ezdxf.readfile(dxf_path)
    marks = []
    for e in doc.modelspace():
        if e.dxftype() == "TEXT" and _layer(e) == "LEVEL":
            p = e.dxf.insert
            if box[0] <= p.x <= box[2] and box[1] <= p.y <= box[3]:
                marks.append((p.x, p.y, e.dxf.text.strip()))

    def dims(f):
        xs = list(f.minimum_rotated_rectangle.exterior.coords)
        a, b = math.dist(xs[0], xs[1]) / 1000, math.dist(xs[1], xs[2]) / 1000
        return round(min(a, b), 4), round(max(a, b), 4)
    hits = []
    for i, f in enumerate(faces):
        if abs(f.area / 1e6 - engine_m2) > 0.005:
            continue
        own_marks = [m[2] for m in marks if f.contains(Point(m[0], m[1]))]
        if not own_marks:
            continue
        nb = []
        for j, g in enumerate(faces):
            if j != i and f.intersection(g).length > 100.0:
                w, ln_ = dims(g)
                nb.append({"shared_edge_m": round(f.intersection(g).length / 1000, 4), "width_m": w, "length_m": ln_,
                           "own_marks": [m[2] for m in marks if g.contains(Point(m[0], m[1]))]})
        w, ln_ = dims(f)
        hits.append({"m2": round(f.area / 1e6, 6), "width_m": w, "length_m": ln_, "own_marks": own_marks,
                     "neighbours": sorted(nb, key=lambda r: r["width_m"])})
    return {"frame": frame, "engine_m2": engine_m2, "level_marks_in_frame": len(marks), "faces": hits}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    out = run(a.dxf)
    out["f_v_p18_2"] = ground_face(a.dxf)
    print(json.dumps(out["f_v_p18_2"], indent=1))
    print(json.dumps({k: v for k, v in out.items() if k not in ("lines",)}, indent=1)[:3000])
    for r in out["lines"]:
        print(r)
    if a.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
