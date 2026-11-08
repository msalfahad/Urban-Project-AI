"""T-618 DRAWING READ (research, unwired): the drawn evidence behind three small finishes residuals, read by HANDLE on
the architectural DXF (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, decoded into .work/private only):

  1. ST-02 round-stair corner landing (RS-LD): its four sides (west = last riser of the east-going flight 141, north =
     first riser of the north-going flight 144, east = the stair's outer edge 4AF / 4B6, south = wall 336 + column 2FC6)
     and the WALLED length on each side (layer-1 wall lines and S-COL.BON column outlines lying on the side).
  2. ST-03 entrance stair E1 upper landing (the +1.00 porch): its four sides (west = top nosing 30A, north = wall 34C,
     east = wall 9D / main door / wall 9E, south = wall 15A / pantry door / 15B) and the walled length on each side.
  3. Door-step openings: the leaf width of each exterior door block (insert x-extent x |xscale|), beside the T-592 wall
     gap; and the sea-gate panel drawn on the elevation (27FA, T-361).

Writes T618_DRAWN.json: handles, roles and lengths only (no coordinate, no drawing text, no client name). The builder
t618_alsenan.py reads only that JSON.

    .work/venv/bin/python -I research/agents_t618/t618_extract.py --dxf <P7757.dxf> --write
    .work/venv/bin/python -I research/agents_t618/t618_extract.py --dxf <P7757.dxf>          (re-read, compare)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t618_rules as R  # noqa: E402

sys.path.insert(0, str(HERE.parent / "agents_t606"))
import t606_extract as X6  # noqa: E402
import t606_rules as R6  # noqa: E402

OUT = HERE / "T618_DRAWN.json"

# landing = (x handle, y handle, x handle, y handle): the rectangle is bounded by the x of two vertical edges and the
# y of two horizontal edges; each side names the drawn edge that bounds it (role) for the record.
LANDINGS = {
    "ST-02:RS-LD": {"x0": "141", "x1": "4B6", "y0": "336", "y1": "144",
                    "roles": {"W": "last riser of the east-going flight (141, hidden layer 2)",
                              "E": "outer edge of the north-going flight (end of 4B6 / riser ends 144 .. 4B5)",
                              "S": "wall 336 + column 2FC6",
                              "N": "first riser of the north-going flight (144, hidden layer 2)"}},
    "ST-03:E1-LD": {"x0": "30A", "x1": "9D", "y0": "15A", "y1": "34C",
                    "roles": {"W": "top nosing of flight E1 (30A, layer 5)", "E": "wall 9D / main door / wall 9E",
                              "S": "wall 15A / pantry door / wall 15B", "N": "wall 34C"}},
}
DOOR_BLOCKS = {"D-GF-01": "15E", "D-GF-03": "1B5", "D-GF-05": "192", "D-GF-09": "3FF", "D-GF-15": "2D8"}
ELEVATION = {"D-GF-15 elevation panel": "27FA"}
OFFSET_OUTLINES = ("1F-CUR.ours", "2F-CORR.ours")    # the two UNRESOLVED rooms, as T-606 chains them by handle
OFFSET_T_MM = 1.0   # probe offset (mm) for the outline's offset coefficient k: P(t) = P + 2 k t, A(t) = A + P t + k t^2
TOL = 60.0        # mm: a wall line 'on' a side lies within 0.06 m of it (a 0.05 band or companion is not a wall)


def _x(e, which):
    if e.dxftype() == "LINE":
        return (e.dxf.start[0] + e.dxf.end[0]) / 2 if which == "mid" else None
    raise R.RuleError(f"handle {e.dxf.handle}: expected a LINE")


def _coord(e, axis):
    """The constant coordinate of an axis-parallel LINE (x for a vertical line, y for a horizontal one)."""
    if e.dxftype() != "LINE":
        raise R.RuleError(f"handle {e.dxf.handle}: expected a LINE, got {e.dxftype()}")
    s, t = e.dxf.start, e.dxf.end
    i = 0 if axis == "x" else 1
    if abs(s[i] - t[i]) > 1.0:
        raise R.RuleError(f"handle {e.dxf.handle}: not parallel to the {'y' if axis == 'x' else 'x'} axis")
    return s[i]


def _segments(msp):
    """Every layer-1 LINE and every edge of a closed S-COL.BON polyline, as (layer, handle, x0, y0, x1, y1)."""
    out = []
    for e in msp.query("LINE"):
        if e.dxf.layer == "1":
            out.append(("1", e.dxf.handle, e.dxf.start[0], e.dxf.start[1], e.dxf.end[0], e.dxf.end[1]))
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.layer == "S-COL.BON" and e.closed:
            p = [q[:2] for q in e.get_points()]
            for a, b in zip(p, p[1:] + p[:1]):
                out.append(("S-COL.BON", e.dxf.handle, a[0], a[1], b[0], b[1]))
    return out


def walled(segs, side, c, lo, hi):
    """Walled length (m) on a side at constant coordinate c over [lo, hi] (mm), and the handles that make it."""
    iv, hs = [], set()
    for lay, h, x0, y0, x1, y1 in segs:
        if side in ("N", "S"):
            if abs(y0 - y1) > 1.0 or abs(y0 - c) > TOL:
                continue
            a, b = sorted((x0, x1))
        else:
            if abs(x0 - x1) > 1.0 or abs(x0 - c) > TOL:
                continue
            a, b = sorted((y0, y1))
        a, b = max(a, lo), min(b, hi)
        if b - a > 1.0:
            iv.append((a, b))
            hs.add(h)
    iv.sort()
    tot, cur = 0.0, None
    for a, b in iv:
        if cur is None or a > cur[1]:
            if cur:
                tot += cur[1] - cur[0]
            cur = [a, b]
        else:
            cur[1] = max(cur[1], b)
    if cur:
        tot += cur[1] - cur[0]
    return round(tot / 1000.0, 6), sorted(hs)


def _chain_points(geom, chain):
    """The outline polygon of a T-606 handle chain (R-T606-1 vertices; arcs flattened at 0.5 deg for the polygon only)."""
    n = len(chain)
    verts = []
    for i in range(n):
        ta, ga = geom[chain[i - 1][0]]
        tb, gb = geom[chain[i][0]]
        if ta == "LINE" and tb == "LINE":
            verts.append(R6._line_line(ga, gb))
        elif ta == "LINE":
            verts.append(R6._line_circle(ga, gb[0], gb[1]))
        else:
            verts.append(R6._line_circle(gb, ga[0], ga[1]))
    pts, arcs, ortho = [], 0, True
    for i in range(n):
        p, q = verts[i], verts[(i + 1) % n]
        t, g = geom[chain[i][0]]
        if t == "LINE":
            pts.append(p)
            if abs(p[0] - q[0]) > 1.0 and abs(p[1] - q[1]) > 1.0:
                ortho = False
        else:
            arcs += 1
            ortho = False
            import math
            c, r, s0, s1 = g
            mid = (s0 + ((s1 - s0) % 360.0) / 2.0) % 360.0
            a0, sw = R6._sweep(R6._ang(c, p), R6._ang(c, q), mid)
            k = max(2, int(abs(sw) / 0.5))
            for j in range(k):
                a = math.radians(a0 + sw * j / k)
                pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return pts, arcs, ortho


def offset_coefficient(geom, chain):
    """k of the outline from a +-1 mm mitred offset (shapely): k = (P(+t) - P(-t)) / (4 t)."""
    from shapely.geometry import Polygon
    poly = Polygon(_chain_points(geom, chain)[0])
    t = OFFSET_T_MM
    up = poly.buffer(t, join_style=2, mitre_limit=50.0)
    dn = poly.buffer(-t, join_style=2, mitre_limit=50.0)
    return (up.length - dn.length) / (4 * t), poly.length / 1000.0, poly.area / 1e6


def read(dxf_path):
    import ezdxf
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    db = doc.entitydb
    segs = _segments(msp)
    out = {"schema": "T618_DRAWN_V1", "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf)",
           "units": "m", "landings": {}, "door_blocks": {}, "elevation": {}}
    for lid, L in LANDINGS.items():
        x0 = _coord(db[L["x0"]], "x")
        x1 = _coord(db[L["x1"]], "x") if db[L["x1"]].dxf.start[0] == db[L["x1"]].dxf.end[0] else None
        if x1 is None:      # 4B6 is a 0.05 horizontal stub: the flight's outer edge is its west end
            e = db[L["x1"]]
            x1 = min(e.dxf.start[0], e.dxf.end[0])
        y0 = _coord(db[L["y0"]], "y")
        y1 = _coord(db[L["y1"]], "y")
        xa, xb = sorted((x0, x1))
        ya, yb = sorted((y0, y1))
        sides = {}
        for s, c, lo, hi in (("S", ya, xa, xb), ("N", yb, xa, xb), ("W", xa, ya, yb), ("E", xb, ya, yb)):
            w, hs = walled(segs, s, c, lo, hi)
            sides[s] = {"length": round((hi - lo) / 1000.0, 6), "walled": w, "wall_handles": hs, "role": L["roles"][s]}
        out["landings"][lid] = {"x_m": round((xb - xa) / 1000.0, 6), "y_m": round((yb - ya) / 1000.0, 6),
                                "edges": {k: L[k] for k in ("x0", "x1", "y0", "y1")}, "sides": sides}
    for oid, h in DOOR_BLOCKS.items():
        e = db[h]
        blk = doc.blocks.get(e.dxf.name)
        xs = [v for ln in blk if ln.dxftype() == "LINE" for v in (ln.dxf.start[0], ln.dxf.end[0])]
        out["door_blocks"][oid] = {"insert": h, "leaf_block_width": round((max(xs) - min(xs)) * abs(e.dxf.xscale)
                                                                           / 1000.0, 6)}
    for k, h in ELEVATION.items():
        e = db[h]
        out["elevation"][k] = {"handle": h, "length": round(((e.dxf.end[0] - e.dxf.start[0]) ** 2 +
                                                             (e.dxf.end[1] - e.dxf.start[1]) ** 2) ** 0.5 / 1000.0, 6)}
    geom6, _ = X6._segs(msp)
    out["offset"] = {}
    for oid in OFFSET_OUTLINES:
        chain = X6.OUTLINES[oid][2]
        k, P, A = offset_coefficient(geom6, chain)
        _, arcs, ortho = _chain_points(geom6, chain)
        pts = _chain_points(geom6, chain)[0]
        x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
        y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
        cell = []
        for e in msp.query("LINE"):
            a, b = e.dxf.start, e.dxf.end
            if (x0 - 50 <= min(a[0], b[0]) and max(a[0], b[0]) <= x1 + 50 and y0 - 50 <= min(a[1], b[1])
                    and max(a[1], b[1]) <= y1 + 50):
                cell.append([e.dxf.handle, e.dxf.layer, round(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 / 1000.0,
                                                              6)])
        out["offset"][oid] = {"handles": [h for h, _ in chain], "k": round(k, 4), "arcs": arcs, "orthogonal": ortho,
                              "polygon_P_flattened": round(P, 4), "polygon_A": round(A, 4),
                              "cell_x_m": round((x1 - x0) / 1000.0, 6), "cell_y_m": round((y1 - y0) / 1000.0, 6),
                              "cell_lines": sorted(cell)}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    d = read(a.dxf)
    txt = json.dumps(d, indent=1, sort_keys=True) + "\n"
    if a.write:
        OUT.write_text(txt)
        print(f"T-618 extract: wrote {OUT.name}")
        return 0
    same = OUT.exists() and OUT.read_text() == txt
    print("T-618 extract: re-read " + ("identical" if same else "DIFFERS"))
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
