"""T-391 own drawing read (run on private inputs; writes VALUES, ids and DXF handles only, no coordinates).

    .work/venv/bin/python -I research/agents_t391/t391_extract.py "<.work/private>/ST7757 dxf.dxf" \
        --svg <run>/v29/structural/overlays_m4/Slab_thickness_basis_SH08.svg \
        --faces <run>/v29/structural/SLAB_FACES.csv --out research/agents_t391/OWN_GROUND_T391.json

GROUND BEAMS PLAN frame of the structural DXF (the T-141 frame box, a drawing-sheet extent, not a quantity): every
layer-1 band edge (LINE / ARC), every S-COL.BON column edge and outline and the S-BW lift / pit rings are noded and
polygonised (shapely). Each face is one piece of the plan: a COLUMN piece (inside an S-COL.BON outline), a LIFT piece
(inside an S-BW ring), a BEAM strip (equivalent width under 0.36 m from area and perimeter), or a slab PANEL. The faces
of the engine's ground-slab cells are read from the route-G overlay of the same run (the overlay is scaled onto the
DXF by one rectangular face, both axes) and each engine cell is bound to the own faces it covers by more than half.
Areas in m2 to 0.0001; nothing typed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

GBP = (78929.89653886131, 29036.09943562183, 114124.2067251332, 57066.43175431111)   # T-141 GROUND BEAMS PLAN frame
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
BEAM_W_MAX = 0.36


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _arc_pts(e, n=48):
    a0 = math.radians(e.dxf.start_angle)
    a1 = math.radians(e.dxf.end_angle)
    if a1 < a0:
        a1 += 2 * math.pi
    c, r = e.dxf.center, e.dxf.radius
    return [(c.x + r * math.cos(a0 + (a1 - a0) * i / n), c.y + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def eq_width(area_m2, per_m):
    disc = per_m * per_m - 16 * area_m2
    return (per_m - math.sqrt(disc)) / 4 if disc >= 0 else math.sqrt(area_m2)


def read(dxf):
    import ezdxf
    from ezdxf import bbox as BB
    from shapely.geometry import LineString, Polygon
    from shapely.ops import polygonize, unary_union
    doc = ezdxf.readfile(dxf)
    segs, cols, rings = [], [], []
    for e in doc.modelspace():
        try:
            layer = e.dxf.layer
            b = BB.extents([e])
        except Exception:
            continue
        if not b.has_data or not (GBP[0] <= b.center.x <= GBP[2] and GBP[1] <= b.center.y <= GBP[3]):
            continue
        t = e.dxftype()
        if layer == "1" and t == "LINE" or layer == "S-COL.BON" and t == "LINE":
            segs.append((e.dxf.handle, [tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]]))
        elif layer == "1" and t == "ARC":
            segs.append((e.dxf.handle, _arc_pts(e)))
        elif layer in ("S-COL.BON", "S-BW") and t == "LWPOLYLINE":
            p = [tuple(v)[:2] for v in e.get_points("xy")]
            if e.closed:
                p = p + [p[0]]
            segs.append((e.dxf.handle, p))
            if e.closed and layer == "S-COL.BON":
                cols.append((e.dxf.handle, Polygon(p)))
            if e.closed and layer == "S-BW":
                rings.append((e.dxf.handle, Polygon(p)))
    lines = [LineString(p) for _, p in segs]
    faces = list(polygonize(unary_union(lines)))
    out = []
    for f in sorted(faces, key=lambda f: (-round(f.area), f.representative_point().x)):
        a, per = f.area / 1e6, f.length / 1e3
        kind = None
        for h, c in cols:
            if c.buffer(5).contains(f):
                kind = "COLUMN"
                host = h
                break
        if kind is None:
            for h, c in rings:
                if c.buffer(5).contains(f) and f.area / c.area > 0.5:
                    kind, host = "LIFT", h
                    break
        if kind is None:
            host = ""
            kind = "BEAM" if eq_width(a, per) < BEAM_W_MAX else "PANEL"
        edge = sorted({h for h, p in segs if LineString(p).distance(f.exterior) < 2 and
                       LineString(p).intersection(f.exterior.buffer(2)).length > 50})
        out.append({"face": "", "kind": kind, "host": host, "area_m2": round(a, 4),
                    "eq_width_m": round(eq_width(a, per), 3), "edge_handles": edge, "_g": f})
    for i, r in enumerate(out, 1):
        r["face"] = f"OWN-{i:03d}"
    return out, cols + rings


def gb_bounds(out, cols_rings):
    """Drawn envelope of a lump ground-beam length: LOW = the beam strips at the 0.30 printed width (face to face);
    HIGH = LOW + the extent of every column / ring along each strip direction it adjoins (a length run through every
    support). Straight strips only take a direction; curved strips add to LOW only."""
    import math as _m
    strips, low = [], 0.0
    for r in out:
        if r["kind"] != "BEAM":
            continue
        f = r["_g"]
        low += r["area_m2"] / 0.30
        c = list(f.minimum_rotated_rectangle.exterior.coords)
        e1, e2 = _m.dist(c[0], c[1]), _m.dist(c[1], c[2])
        dx, dy = (c[1][0] - c[0][0], c[1][1] - c[0][1]) if e1 >= e2 else (c[2][0] - c[1][0], c[2][1] - c[1][1])
        ang = abs(_m.degrees(_m.atan2(dy, dx))) % 180
        d = "X" if (ang < 2 or ang > 178) else ("Y" if abs(ang - 90) < 2 else "")
        if d:
            strips.append((d, f))
    cross = 0.0
    for _, c in cols_rings:
        b = c.bounds
        for d, ext in (("X", (b[2] - b[0]) / 1e3), ("Y", (b[3] - b[1]) / 1e3)):
            if any(sd == d and sf.distance(c) < 5 for sd, sf in strips):
                cross += ext
    return [round(low, 4), round(low + cross, 4)]


def bind_engine(out, svg, faces_csv):
    from shapely.affinity import affine_transform
    from shapely.geometry import Polygon
    s = Path(svg).read_text(encoding="utf-8")
    eng = {}
    for pts, title in re.findall(r'<polygon[^>]*points="([^"]+)"[^>]*>(?:<title>([^<]*)</title>)?', s):
        if title.startswith("SITE-"):
            eng[title.split()[0]] = Polygon([tuple(map(float, q.split(","))) for q in pts.split()]).buffer(0)
    meta = {r["COMPONENT_ID"].split(":")[-1]: r for r in csv.DictReader(open(faces_csv, encoding="utf-8"))
            if ":GROUND:" in r["COMPONENT_ID"]}
    # scale: the unique rectangular engine face whose net area equals one own panel to 0.0001 m2 and has 4 vertices
    ref = None
    for k, g in eng.items():
        if k in meta and len(g.exterior.coords) == 5:
            for r in out:
                if r["kind"] == "PANEL" and abs(r["area_m2"] - float(meta[k]["AREA_NET_M2"])) < 1e-4 and \
                        len(r["_g"].exterior.coords) == 5:
                    ref = (g, r["_g"])
                    break
        if ref:
            break
    eb, ob = ref[0].bounds, ref[1].bounds
    kx = (ob[2] - ob[0]) / (eb[2] - eb[0])
    ky = (ob[3] - ob[1]) / (eb[3] - eb[1])
    rows = []
    for k in sorted(meta):
        g = affine_transform(eng[k], [kx, 0, 0, -ky, ob[0] - eb[0] * kx, ob[1] + eb[3] * ky])
        hits = [r["face"] for r in out if g.intersection(r["_g"]).area / r["_g"].area > 0.5]
        m = meta[k]
        rows.append({"engine_cell": "SITE-" + k[5:] if not k.startswith("SITE-") else k, "region": m["REGION"],
                     "gross_m2": round(float(m["AREA_GROSS_M2"]), 4), "member_overlap_m2":
                     round(float(m["MEMBER_OVERLAP_M2"] or 0), 4), "net_m2": round(float(m["AREA_NET_M2"]), 4),
                     "own_faces": hits})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("structural")
    ap.add_argument("--svg", required=True)
    ap.add_argument("--faces", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if _sha(a.structural) != DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    out, supports = read(a.structural)
    bounds = gb_bounds(out, supports)
    binding = bind_engine(out, a.svg, a.faces)
    for r in out:
        r.pop("_g")
    doc = {"schema": "T391_OWN_GROUND_V1", "structural_sha256": DXF_SHA, "frame": "T-141 GROUND BEAMS PLAN",
           "faces": out, "engine_binding": binding,
           "gb_bounds_m": bounds}
    Path(a.out).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    from collections import Counter
    c = Counter(r["kind"] for r in out)
    print({k: (c[k], round(sum(r["area_m2"] for r in out if r["kind"] == k), 4)) for k in c})


if __name__ == "__main__":
    main()
