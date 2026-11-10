"""T-667 own read (values only): the pool outline on the GROUND BEAMS PLAN and its relation to the footing outlines of
the FOUNDATION PLAN and the plot line, from the structural DXF (Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf',
decoded into .work/private). Prints areas and clearances in metres; writes no position, no text, no name.

The two plan frames share the plot line: the ground-beam frame's boundary band polyline 7FE spans 31.37 m like the
foundation plan's plot line 1658, both frames have the plot's lower edge at the same y, so the frame shift is the
difference of the two plot left edges (checked: the pool back lies on the plot's right edge in the ground-beam frame).

    .work/venv/bin/python -I research/agents_t667/t667_extract.py <ST dxf> [<out.json>]
"""
from __future__ import annotations

import hashlib
import json
import math
import sys

import ezdxf
from ezdxf import bbox
from ezdxf.path import make_path
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

POOL_OUT, POOL_WATER = "7C6", "7C5"       # S-BW, ground beams plan
GB_FRAME_BAND = "7FE"                     # S-BOUN band polyline of the ground-beam frame (31.37 m wide)
PLOT = "1658"                             # S-BOUN plot line, foundation plan
PITS = ["165C", "1663", "1664", "1665", "1666", "1667", "1668", "1669", "166A", "166B", "166C", "166D", "180C",
        "180F", "1ABF", "1ADB", "1B07", "1B19", "1B1A", "1B1B", "1B24", "1B2A", "1B2B"]
FOUR_LINES = {"10F0": ["10F0", "10F1", "10F2", "10F3"], "10F8": ["10F8", "10F9", "10FA", "10FB"],
              "1100": ["1100", "1101", "1102", "1103"]}
P = 0.10                                  # printed blinding projection of the pits (ST p.13) and protection 5 + 5 cm
SKIP = ("RTEXT", "TEXT", "MTEXT", "DIMENSION", "HATCH", "INSERT", "ATTRIB", "ATTDEF")


def _poly(e, n=4096):
    """closed LWPOLYLINE in m; a bulge arc is sampled on its true circle (included angle 4 atan(bulge), positive =
    counter-clockwise), not through the cubic Bezier of make_path (which lies about 0.03 % of the arc area outside)."""
    v = [(float(a[0]), float(a[1]), float(a[4])) for a in e.get_points()]
    pts = []
    for i, (x, y, b) in enumerate(v):
        pts.append((x / 1000.0, y / 1000.0))
        if abs(b) > 1e-12:
            x2, y2 = v[(i + 1) % len(v)][:2]
            th = 4.0 * math.atan(b)
            mx, my, dx, dy = (x + x2) / 2, (y + y2) / 2, x2 - x, y2 - y
            d = math.hypot(dx, dy)
            h = (d / 2) / math.tan(th / 2)
            cx, cy = mx - h * dy / d, my + h * dx / d
            r = math.hypot(x - cx, y - cy)
            a0 = math.atan2(y - cy, x - cx)
            k = max(8, int(n * abs(th) / math.pi))
            pts += [((cx + r * math.cos(a0 + th * j / k)) / 1000.0, (cy + r * math.sin(a0 + th * j / k)) / 1000.0)
                    for j in range(1, k)]
    return Polygon(pts)


def _bb(e):
    b = bbox.extents([e])
    return b.extmin.x / 1000.0, b.extmin.y / 1000.0, b.extmax.x / 1000.0, b.extmax.y / 1000.0


def main(src, dst=None):
    sha = hashlib.sha256(open(src, "rb").read()).hexdigest()
    doc = ezdxf.readfile(src)
    db, msp = doc.entitydb, doc.modelspace()
    pool, water = _poly(db[POOL_OUT]), _poly(db[POOL_WATER])
    bx0, by0, bx1, _ = _bb(db[GB_FRAME_BAND])
    px0, py0, px1, py1 = _bb(db[PLOT])
    if abs((bx1 - bx0) - (px1 - px0)) > 0.005:
        raise SystemExit("frames differ in width: no shared plot line")
    dx = px0 - bx0
    out = {"schema": "URBAN_T667_POOL_READ_V1", "dxf_sha256": sha,
           "plot_m": [round(px1 - px0, 4), round(py1 - py0, 4)]}
    # the outline in its own frame (values only)
    verts = list(db[POOL_OUT].get_points())
    out["pool_outline"] = {"entity": db[POOL_OUT].dxftype(), "closed": bool(db[POOL_OUT].closed),
                           "vertices": len(verts), "bulges": [round(float(v[4]), 4) for v in verts],
                           "area_m2_flattened": round(pool.area, 6), "perimeter_m_flattened": round(pool.length, 6),
                           "water_area_m2_flattened": round(water.area, 6)}
    xs = [v[0] / 1000.0 for v in verts]
    out["pool_back_on_plot_edge_gap_m"] = round(abs(max(xs) - bx1), 6)
    out["pool_back_length_m"] = round(max(v[1] for v in verts) / 1000.0 - min(v[1] for v in verts) / 1000.0, 6)
    # the band in the ground-beam frame: does it run along the pool back?
    band = LineString([(x / 1000.0, y / 1000.0) for x, y, *_ in db[GB_FRAME_BAND].get_points()])
    back = LineString([(max(xs), min(v[1] for v in verts) / 1000.0), (max(xs), max(v[1] for v in verts) / 1000.0)])
    out["band_7FE_length_along_pool_back_m"] = round(band.intersection(back.buffer(0.001)).length, 6)
    # clearances from the pool outline to every drawn line within 1 m (ground-beam frame), by layer
    near = {}
    for e in msp:
        if e.dxftype() in SKIP or e.dxf.handle in (POOL_OUT, POOL_WATER):
            continue
        try:
            pts = [(v.x / 1000.0, v.y / 1000.0) for v in make_path(e).flattening(0.5)]
        except Exception:
            continue
        if len(pts) < 2:
            continue
        d = LineString(pts).distance(pool)
        if 0.0001 < d < 1.0:
            lay = e.dxf.layer
            near[lay] = round(min(near.get(lay, 9.0), d), 4)
    out["nearest_drawn_line_by_layer_m"] = dict(sorted(near.items()))
    # into the foundation frame
    from shapely import affinity
    pool_f = affinity.translate(pool, xoff=dx, yoff=0.0)
    plot = box(px0, py0, px1, py1)
    grown = pool_f.buffer(P, join_style=2, mitre_limit=10.0)
    out["pool_grown_0.10_m2"] = round(grown.area, 6)
    out["pool_grown_inside_plot_m2"] = round(grown.intersection(plot).area, 6)
    out["pool_grown_beyond_plot_m2"] = round(grown.difference(plot).area, 6)
    near_f = {}
    for e in msp:
        if e.dxftype() in SKIP or e.dxf.handle in PITS or e.dxf.handle == PLOT:
            continue
        try:
            pts = [(v.x / 1000.0, v.y / 1000.0) for v in make_path(e).flattening(0.5)]
        except Exception:
            continue
        if len(pts) < 2 or any(e.dxf.handle in hs for hs in FOUR_LINES.values()):
            continue
        d = LineString(pts).distance(pool_f)
        if d < 1.0:
            near_f[e.dxf.layer] = round(min(near_f.get(e.dxf.layer, 9.0), d), 4)
    out["foundation_frame_nearest_line_by_layer_m"] = dict(sorted(near_f.items()))
    pits = {}
    for h in PITS:
        e = db[h]
        pits[h] = _poly(e) if e.dxftype() == "LWPOLYLINE" else Polygon(
            box(*_bb(e)).exterior.coords)
    for h, hs in FOUR_LINES.items():
        b = [_bb(db[k]) for k in hs]
        pits[h] = box(min(x[0] for x in b), min(x[1] for x in b), max(x[2] for x in b), max(x[3] for x in b))
    ov = {}
    for h, g in pits.items():
        gg = g.buffer(P, join_style=2, mitre_limit=10.0).intersection(plot)
        a_out = g.intersection(pool_f).area
        a_core_grown = gg.intersection(pool_f).area
        a_grown = gg.intersection(grown.intersection(plot)).area
        if a_grown > 1e-9 or g.distance(pool_f) < 1.0:
            ov[h] = {"outline_m2": round(g.area, 6), "outline_over_pool_outline_m2": round(a_out, 6),
                     "pit_layer_over_pool_outline_m2": round(a_core_grown, 6),
                     "pit_layer_over_pool_grown_in_plot_m2": round(a_grown, 6),
                     "outline_over_pool_grown_in_plot_m2": round(g.intersection(grown.intersection(plot)).area, 6),
                     "clearance_outline_to_pool_m": round(g.distance(pool_f), 6)}
    out["pits_near_pool"] = ov
    # frame check: the columns of the ground-beam frame, shifted by dx, fall inside the footing outlines
    cols = [e for e in msp.query('LWPOLYLINE[layer=="S-COL.BON"]')
            if e.closed and bx0 <= _bb(e)[0] and _bb(e)[2] <= bx1 and py0 <= _bb(e)[1] and _bb(e)[3] <= py1]
    inside = 0
    for e in cols:
        c = affinity.translate(_poly(e), xoff=dx, yoff=0.0).centroid
        inside += any(g.buffer(0.001).contains(c) for g in pits.values())
    out["frame_check_columns_inside_a_footing"] = [inside, len(cols)]
    union_layer = unary_union([g.buffer(P, join_style=2, mitre_limit=10.0) for g in pits.values()]).intersection(plot)
    out["outline_union_over_pool_grown_in_plot_m2"] = round(
        unary_union(list(pits.values())).intersection(grown.intersection(plot)).area, 6)
    out["pit_layer_union_over_pool_grown_in_plot_m2"] = round(union_layer.intersection(grown.intersection(plot)).area, 6)
    s = json.dumps(out, indent=1)
    if dst:
        open(dst, "w").write(s)
    print(s)


if __name__ == "__main__":
    main(*sys.argv[1:])
