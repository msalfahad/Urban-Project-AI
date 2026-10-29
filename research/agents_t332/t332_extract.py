"""T-332 private reader: the drawn faces that merges after formwork r5 (T-308) re-opened, read by DXF handle.

    python3 -I research/agents_t332/t332_extract.py <'ST7757 dxf.dxf'> research/agents_t332/ALSENAN_T332_INPUT.json

Reads ONLY the handles named below on Drive "Alsenan chalet project" / 'ST7757 dxf.dxf' (sha256 9f9d1179...) and writes
lengths, areas, radii and handles (no coordinate, no text content). Every value is exact from the entity's vertices and
bulges (a bulge b spans 4 atan(b); arc length = r x sweep), never sampled. Units: the DXF is in mm; output in m.

Faces re-read (each re-opened by a merge after T-308 / V3.0.18):
  * pool (T-183 r2 geometry, T-320 envelope): S-BW 7C6 (outer D, closed) and 7C5 (water D, open: its 5th vertex closes
    the back), per segment kind (straight back / sides / curve);
  * F8 1B24 vs the pool envelope (T-320 F-T320-02: the p.7 layers 0.10 outside the outer face): the envelope is 7C6
    buffered 0.10 with round joins (= T-320's A10 = A + P x 0.10 + pi 0.10^2), carried to the foundation sheet by the
    sheet translation the lift ring proves (10EB on the foundation sheet vs 7C2 on the ground-beams sheet, T-205 / T-322);
    output: the overlap area (check against T-189 / T-320 1.296442 m2) and the length of each F8 face inside it;
  * lift pit (T-322 / T-204): ring S-BW 10EB (outer) / 10EA (inner) and the four columns S-COL.BON 1099 / 1093 / 1096 /
    1090 standing in the band: the length of each ring face NOT covered by a column (a column face, not a wall face);
  * FF raft 1B2B and F12 1ABF outlines (T-322 / T-320 confirm their schedule sizes);
  * ring ground beam arcs 157 (inner) / 158 (outer) (T-255 changed only its concrete END closure): radius and sweep.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import ezdxf
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

MM = 1000.0


def _verts(doc, h):
    e = doc.entitydb.get(h)
    if e is None or e.dxftype() != "LWPOLYLINE":
        raise SystemExit(f"handle {h}: not an LWPOLYLINE")
    return [(float(x), float(y), float(b)) for x, y, b in e.get_points("xyb")], bool(e.closed), e.dxf.layer


def _segments(v, closed):
    n = len(v)
    out = []
    for i in range(n if closed else n - 1):
        x0, y0, b = v[i]
        x1, y1, _ = v[(i + 1) % n]
        c = math.hypot(x1 - x0, y1 - y0)
        if b == 0.0:
            out.append({"kind": "LINE", "len": c / MM})
        else:
            th = 4.0 * math.atan(abs(b))
            r = c / (2.0 * math.sin(th / 2.0))
            out.append({"kind": "ARC", "len": r * th / MM, "r": r / MM, "sweep_deg": math.degrees(th)})
    return out


def _poly(v, closed, step_deg=0.25):
    """Polygon of the outline with each bulge densified (for overlaps only; lengths come from _segments)."""
    pts = []
    n = len(v)
    for i in range(n if closed else n - 1):
        x0, y0, b = v[i]
        x1, y1, _ = v[(i + 1) % n]
        pts.append((x0, y0))
        if b:
            th = 4.0 * math.atan(b)
            c = math.hypot(x1 - x0, y1 - y0)
            r = c / (2.0 * math.sin(abs(th) / 2.0))
            mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            d = math.sqrt(max(r * r - (c / 2.0) ** 2, 0.0))
            ux, uy = (x1 - x0) / c, (y1 - y0) / c
            s = 1.0 if (b > 0) == (abs(th) < math.pi) else -1.0
            cx, cy = mx - s * uy * d, my + s * ux * d
            if abs(abs(th) - math.pi) < 1e-9:
                cx, cy = mx, my
            a0 = math.atan2(y0 - cy, x0 - cx)
            k = max(int(abs(math.degrees(th)) / step_deg), 2)
            for j in range(1, k):
                a = a0 + th * j / k
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    if not closed:
        pts.append((v[-1][0], v[-1][1]))
    return Polygon(pts)


def read(dxf_path):
    doc = ezdxf.readfile(dxf_path)
    out = {"schema": "T332_ALSENAN_INPUT_V1", "source": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'",
           "units": "m, m2", "handles": {}}

    # pool
    pool = {}
    for h, name in (("7C6", "outer"), ("7C5", "water")):
        v, closed, layer = _verts(doc, h)
        segs = _segments(v, closed)
        pool[name] = {"handle": h, "layer": layer, "closed_in_dxf": closed,
                      "segments": [{k: round(s[k], 6) if isinstance(s[k], float) else s[k] for k in s} for s in segs],
                      "perimeter": round(sum(s["len"] for s in segs), 6),
                      "curved": round(sum(s["len"] for s in segs if s["kind"] == "ARC"), 6)}
    out["pool"] = pool

    # sheet translation from the lift ring (foundation 10EB vs ground-beams 7C2)
    vf, _, _ = _verts(doc, "10EB")
    vg, _, _ = _verts(doc, "7C2")
    dx = min(p[0] for p in vf) - min(p[0] for p in vg)
    dy = min(p[1] for p in vf) - min(p[1] for p in vg)
    sz = lambda vv: (round((max(p[0] for p in vv) - min(p[0] for p in vv)) / MM, 4),
                     round((max(p[1] for p in vv) - min(p[1] for p in vv)) / MM, 4))
    out["sheet_translation_ground_to_foundation"] = {"from": "7C2", "to": "10EB", "dx_m": round(dx / MM, 4),
                                                     "dy_m": round(dy / MM, 4), "same_size": sz(vf) == sz(vg)}

    # F8 vs pool envelope
    v6, c6, _ = _verts(doc, "7C6")
    outer = _poly([(x + dx, y + dy, b) for x, y, b in v6], c6)
    env = outer.buffer(100.0, quad_segs=64)
    v8, c8, _ = _verts(doc, "1B24")
    f8 = Polygon([(x, y) for x, y, _ in v8])
    faces = []
    for i in range(len(v8)):
        a = (v8[i][0], v8[i][1])
        b = (v8[(i + 1) % len(v8)][0], v8[(i + 1) % len(v8)][1])
        seg = LineString([a, b])
        inside = seg.intersection(env).length
        side = "N" if a[1] == b[1] and a[1] == max(p[1] for p in v8) else (
            "S" if a[1] == b[1] else ("E" if a[0] == max(p[0] for p in v8) else "W"))
        faces.append({"face": side, "len": round(seg.length / MM, 6), "inside_envelope": round(inside / MM, 6)})
    out["f8_vs_pool"] = {"f8": "1B24", "f8_size": sz(v8),
                         "overlap_f8_outer_m2": round(f8.intersection(outer).area / MM ** 2, 6),
                         "overlap_f8_envelope_m2": round(f8.intersection(env).area / MM ** 2, 6),
                         "faces": faces}

    # lift pit ring and columns
    ro, _, _ = _verts(doc, "10EB")
    ri, _, _ = _verts(doc, "10EA")
    cols = unary_union([Polygon([(x, y) for x, y, _ in _verts(doc, h)[0]]).buffer(1e-6, join_style=2)
                        for h in ("1099", "1093", "1096", "1090")])
    ring = {}
    for h, name in (("10EB", "outer"), ("10EA", "inner")):
        v, _, _ = _verts(doc, h)
        tot = 0.0
        free = 0.0
        for i in range(len(v)):
            seg = LineString([(v[i][0], v[i][1]), (v[(i + 1) % len(v)][0], v[(i + 1) % len(v)][1])])
            tot += seg.length
            free += seg.difference(cols).length
        ring[name] = {"handle": h, "size": sz(v), "perimeter": round(tot / MM, 6),
                      "not_on_a_column": round(free / MM, 6)}
    band = Polygon([(x, y) for x, y, _ in ro]).difference(Polygon([(x, y) for x, y, _ in ri]))
    ring["band_gross_m2"] = round(band.area / MM ** 2, 6)
    ring["band_net_of_columns_m2"] = round(band.difference(cols).area / MM ** 2, 6)
    ring["columns"] = ["1099", "1093", "1096", "1090"]
    out["lift_ring"] = ring

    for h, name in (("1B2B", "FF"), ("1ABF", "F12")):
        v, _, _ = _verts(doc, h)
        out.setdefault("footings", {})[name] = {"handle": h, "size": sz(v)}

    arcs = {}
    for h in ("157", "158"):
        e = doc.entitydb.get(h)
        sw = (e.dxf.end_angle - e.dxf.start_angle) % 360.0
        arcs[h] = {"r": round(e.dxf.radius / MM, 6), "sweep_deg": round(sw, 6),
                   "len": round(e.dxf.radius / MM * math.radians(sw), 6)}
    out["ring_ground_beam_arcs"] = arcs
    return out


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if len(a) != 2:
        raise SystemExit(__doc__)
    data = read(a[0])
    Path(a[1]).write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(data, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
