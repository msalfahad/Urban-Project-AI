"""T-160 helper: read the dome bays of a structural slab plan from a DXF (drawing units mm -> m).

For each dome centre given (approximate, drawing metres) it reads, from the drawing only:
  - the concentric CIRCLE / ARC radii about that centre (ring inner / outer faces),
  - the four bay faces: the nearest straight beam edge line on each side of the centre (layer filter),
    and the next parallel line beyond it (the member's far face),
  - the column outlines (closed polylines on the column layer) within 3 m,
and prints one JSON document (DOMES_INPUT shape) on stdout. Nothing is written to disk.

Usage: python -I read_bays.py <dxf> <cx,cy> [<cx,cy> ...] [--beam-layers 1,5] [--column-layer S-COL.BON]
Private drawings stay outside the repository; only the measured numbers are kept (refer to the file by its Drive title).
"""
import json
import math
import sys

import ezdxf

MM = 0.001


def _lines(msp, layers):
    out = []
    for e in msp:
        if e.dxftype() == "LINE" and e.dxf.layer in layers:
            a, b = e.dxf.start, e.dxf.end
            out.append((a.x * MM, a.y * MM, b.x * MM, b.y * MM))
    return out


def _faces(lines, cx, cy, reach=3.2):
    """nearest axis-parallel line on each side that spans the centre's ordinate, then the next one beyond."""
    side = {"W": [], "E": [], "S": [], "N": []}
    for x1, y1, x2, y2 in lines:
        if abs(x1 - x2) < 1e-6 and min(y1, y2) <= cy <= max(y1, y2):
            d = x1 - cx
            if 0 < d <= reach:
                side["E"].append(d)
            elif -reach <= d < 0:
                side["W"].append(-d)
        if abs(y1 - y2) < 1e-6 and min(x1, x2) <= cx <= max(x1, x2):
            d = y1 - cy
            if 0 < d <= reach:
                side["N"].append(d)
            elif -reach <= d < 0:
                side["S"].append(-d)
    res = {}
    for k, ds in side.items():
        ds = sorted(set(round(d, 6) for d in ds))
        res[k] = {"inner_d_m": ds[0] if ds else None, "far_d_m": ds[1] if len(ds) > 1 else None}
    return res


def read(dxf, centres, beam_layers=("1", "5"), column_layer="S-COL.BON"):
    doc = ezdxf.readfile(dxf)
    msp = doc.modelspace()
    lines = _lines(msp, set(beam_layers))
    out = []
    for cx, cy in centres:
        radii, arcs = set(), []
        ccx, ccy = cx, cy
        cols = []
        for e in msp:
            t = e.dxftype()
            if t in ("CIRCLE", "ARC"):
                c = e.dxf.center
                if math.hypot(c.x * MM - cx, c.y * MM - cy) < 0.01 and e.dxf.radius * MM > 1.0:
                    radii.add(round(e.dxf.radius * MM, 7))
                    arcs.append({"layer": e.dxf.layer, "r_m": round(e.dxf.radius * MM, 7), "type": t,
                                 "start_deg": round(e.dxf.start_angle, 3) if t == "ARC" else 0.0,
                                 "end_deg": round(e.dxf.end_angle, 3) if t == "ARC" else 360.0})
                    ccx, ccy = c.x * MM, c.y * MM
            elif t == "LWPOLYLINE" and e.dxf.layer == column_layer and e.closed:
                pts = [(p[0] * MM, p[1] * MM) for p in e.get_points("xy")]
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                if math.hypot((min(xs) + max(xs)) / 2 - cx, (min(ys) + max(ys)) / 2 - cy) < 3.0:
                    cols.append([round(min(xs) - cx, 6), round(min(ys) - cy, 6), round(max(xs) - cx, 6),
                                 round(max(ys) - cy, 6)])
        rs = sorted(radii)
        out.append({"centre_m": [round(ccx, 6), round(ccy, 6)], "radii_m": rs, "arcs": arcs,
                    "faces": _faces(lines, ccx, ccy), "columns_rel_m": sorted(cols)})
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    bl, cl = ("1", "5"), "S-COL.BON"
    if "--beam-layers" in args:
        i = args.index("--beam-layers"); bl = tuple(args[i + 1].split(",")); del args[i:i + 2]
    if "--column-layer" in args:
        i = args.index("--column-layer"); cl = args[i + 1]; del args[i:i + 2]
    cs = [tuple(map(float, a.split(","))) for a in args[1:]]
    print(json.dumps(read(args[0], cs, bl, cl), indent=1))
