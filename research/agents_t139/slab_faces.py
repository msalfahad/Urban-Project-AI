"""T-139 hand-reading helper (research only, NOT engine code): faces of the three roof-slab plans of a structural DXF.

Polygonises the drawn edge lines (layers 1, 5, S-COL.BON, S-BOUN, S-BEAM; straight lines extended 20 mm at both ends so
that drafting gaps at junctions close) inside each sheet window, and lists every face with its area, minimum rotated
rectangle, centroid and the texts / tag blocks inside it. It decides NOTHING: classification is done face by face, by
eye on the drawing, in slab_ledger.py.

Usage: python -I slab_faces.py <structural.dxf> <out.json>
Windows are drawing millimetres of the Alsenan ST sheet (GF / 1F / 2F roof-slab plans, section details left out by the
classification, not by the window). No drawing file or client text is written: only areas, centroids (drawing metres),
tag values and beam / bar marks."""
import json
import math
import sys

import ezdxf
from shapely.geometry import LineString, Point
from shapely.ops import polygonize, unary_union

SHEETS = {"GF": (40500, 74500, 35500, 51000), "1F": (11500, 36000, 35500, 51000), "2F": (-27000, -2000, 35500, 51000)}
EDGE = {"1", "5", "S-COL.BON", "S-BOUN", "S-BEAM"}
EXT = 0.02   # m


def _arc(c, r, a0, a1, n=48):
    if a1 < a0:
        a1 += 360
    return [(c.x + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             c.y + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def faces(doc, win):
    x0, x1, y0, y1 = win
    inb = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    lines, texts = [], []
    for e in doc.modelspace():
        t = e.dxftype()
        if not e.dxf.is_supported("layer"):
            continue
        lay = e.dxf.layer
        if t == "TEXT":
            p = e.dxf.insert
            if inb((p.x, p.y)) and lay.startswith("S-TEXT"):
                texts.append((e.dxf.text.strip(), p.x / 1000, p.y / 1000))
            continue
        if t == "INSERT":
            p = e.dxf.insert
            if inb((p.x, p.y)):
                vt = [v.dxf.text.strip() for v in e.virtual_entities() if v.dxftype() == "TEXT"]
                if e.dxf.name.lower() == "t" and len(vt) == 2:          # thickness tag block 'T' over its value
                    texts.append(("T " + vt[1], p.x / 1000, p.y / 1000))
            continue
        pts = None
        if t == "LINE":
            pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        elif t == "LWPOLYLINE":
            pts = [q[:2] for q in e.get_points()]
            if e.closed:
                pts.append(pts[0])
        elif t == "ARC":
            pts = _arc(e.dxf.center, e.dxf.radius, e.dxf.start_angle, e.dxf.end_angle)
        elif t == "CIRCLE":
            pts = _arc(e.dxf.center, e.dxf.radius, 0, 360, 96)
        if not pts or lay not in EDGE or not any(inb(p) for p in pts):
            continue
        pts = [(a / 1000, b / 1000) for a, b in pts]
        if len(pts) == 2:
            (ax, ay), (bx, by) = pts
            L = math.hypot(bx - ax, by - ay)
            if L > 0:
                ux, uy = (bx - ax) / L, (by - ay) / L
                pts = [(ax - ux * EXT, ay - uy * EXT), (bx + ux * EXT, by + uy * EXT)]
        lines.append(LineString(pts))
    # T + value written as two TEXTs (1F / 2F sheets): pair a 'T' with the nearest '16' / '18' below it
    for s, x, y in list(texts):
        if s == "T":
            near = [(math.hypot(x2 - x, y2 - y), s2) for s2, x2, y2 in texts if s2 in ("16", "18")]
            if near and min(near)[0] < 0.5:
                texts.append(("T " + min(near)[1], x, y))
    fs = [f for f in polygonize(unary_union(lines)) if f.area > 0.02]
    fs.sort(key=lambda f: (-round(f.centroid.y, 0), f.centroid.x))
    out = []
    for f in fs:
        c = list(f.minimum_rotated_rectangle.exterior.coords)
        d = sorted([math.dist(c[0], c[1]), math.dist(c[1], c[2])])
        out.append({"area": round(f.area, 4), "w": round(d[0], 3), "l": round(d[1], 3),
                    "cx": round(f.centroid.x, 3), "cy": round(f.centroid.y, 3),
                    "texts": [s for s, x, y in texts if f.contains(Point(x, y))], "wkt": f.wkt})
    return out


def main(argv=None):
    dxf, out = (argv or sys.argv[1:])[:2]
    doc = ezdxf.readfile(dxf)
    res = {}
    for sh, win in SHEETS.items():
        fl = faces(doc, win)
        for i, f in enumerate(fl):
            f["id"] = f"{sh}-{i:03d}"
        res[sh] = fl
    json.dump(res, open(out, "w"))
    for sh, fl in res.items():
        print(sh, len(fl), "faces")


if __name__ == "__main__":
    main()
