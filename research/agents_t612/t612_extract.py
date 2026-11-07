"""T-612 DRAWING READ (research, unwired): the GF open room outline re-measured by HANDLE chain (R-T606-1 step 1,
R-T612-1) on the architectural DXF (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, decoded into
.work/private only): the engine face (line L-71e2e002, gross 56.006096), the drawn gross outline his two rows' area
re-adds to (T-427), the drawn pieces his gross may walk (door / opening reveals, the wash-lobby mouth, the solids inside
the outline) and the candidate split lines between his two rows. Writes T612_DRAWN.json: handles, roles, lengths and
areas only (no coordinate, no drawing text, no client name). The builder t612_alsenan.py reads only that JSON.

    .work/venv/bin/python -I research/agents_t612/t612_extract.py --dxf <P7757.dxf> --write
    .work/venv/bin/python -I research/agents_t612/t612_extract.py --dxf <P7757.dxf>          (re-read, compare)

Arc edges: an ARC entity, or one bulge segment of an LWPOLYLINE (the curved glazing), converted to its circle and
sweep (bulge b: included angle 4 atan b, ccw for b > 0) and handed to R-T606-1 as an ARC edge. Columns: every closed
S-COL.BON polyline of the storey; a column that cuts the outline's boundary is a notch (R-T606-1); a column wholly inside
the outline is an INTERIOR SOLID (its area and perimeter reported, never a hole in the perimeter: R-T612-1.2).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "agents_t606"))
import t612_rules as R  # noqa: E402

OUT = HERE / "T612_DRAWN.json"
W, V, LE, Zn, CH = "WALL", "VOID_EDGE", "LANDING_EDGE", "ZONE_EDGE", "CHORD"

# the east side of the room, its curved glazing and the north side, shared by both readings
_NE = [("B5", W), ("E0", W), ("97", W), ("27D#1", W), ("2E4", W), ("222", W), ("20F", W), ("AB", W), ("158", W),
       ("AE", W)]
OUTLINES = {
    "GF-OPEN.face": ("GF", "L-71e2e002", _NE + [("A8", Zn), ("30F", Zn), ("104", W)],
                     "engine face GF-RC99C2A: south side on the band / curb line prolonged west to the west wall, "
                     "east end of the band, facade east of the band"),
    "GF-OPEN.full": ("GF", None, _NE + [("104", W)],
                     "drawn gross outline: west wall to the south facade, band, curb, pantry strips and the solids "
                     "under the 1F facade inside (T-427 147.658 m2)"),
}
# drawn pieces of a gross outline that a reading may walk into: id -> (kind, width ends, depth faces)
# kind DOOR / OPENING: a reveal adds 2 x depth to the perimeter and width x depth to the area
ADDONS = {
    "D200 door reveals (west wall, 2.00)": ("DOOR", ("AB", "AC"), ("AB", "9D")),
    "D120 stair-hall door reveals (1.00)": ("DOOR", ("20F", "20E"), ("20F", "220")),
    "D115 wash-lobby door reveals (1.00)": ("DOOR", ("2E4", "2E3"), ("2E4", "2E1")),
    "D120 west door reveals (1.00)": ("DOOR", ("158", "159"), ("158", "15A")),
    "lift landing door reveals (1.00)": ("DOOR", ("20D", "20E"), ("20D", "21D")),
    "wash-lobby mouth (open to the room)": ("OPENING", ("2DC", "2DC"), ("2DC", "2DB")),
}
# drawn solids wholly inside the gross outline that touch each other: one island (columns by handle, a wall by its two
# face lines, overlapped extent)
ISLANDS = {"solids under the 1F south facade (columns + wall)": [("COL", "2FD2"), ("WALL", ("336", "337")),
                                                                   ("COL", "2FC6")]}


def _arc_from_bulge(p, q, b):
    """(centre, r, start_deg, end_deg) of the ccw arc from p to q (b > 0) or q to p (b < 0)."""
    theta = 4 * math.atan(abs(b))
    c = math.dist(p, q)
    r = c / (2 * math.sin(theta / 2))
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    ux, uy = (q[0] - p[0]) / c, (q[1] - p[1]) / c
    h = r * math.cos(theta / 2)        # signed: < 0 for an arc of more than 180 deg (centre on the bulge side)
    s = 1 if b > 0 else -1
    cx, cy = mx - s * uy * h, my + s * ux * h
    a0 = math.degrees(math.atan2(p[1] - cy, p[0] - cx)) % 360
    a1 = math.degrees(math.atan2(q[1] - cy, q[0] - cx)) % 360
    return ((cx, cy), r, a0, a1) if b > 0 else ((cx, cy), r, a1, a0)


def _segs(msp):
    geom, mids = {}, []
    for e in msp:
        t = e.dxftype()
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            geom[e.dxf.handle] = ("LINE", ((a.x, a.y), (b.x, b.y)))
            if e.dxf.layer == "1":
                mids.append((a.x + b.x) / 2)
        elif t == "ARC":
            c = e.dxf.center
            geom[e.dxf.handle] = ("ARC", ((c.x, c.y), e.dxf.radius, e.dxf.start_angle, e.dxf.end_angle))
        elif t == "LWPOLYLINE":
            pts = [(q[0], q[1], q[4]) for q in e.get_points()]
            for i, (x, y, b) in enumerate(pts[:-1] if not e.closed else pts):
                j = (i + 1) % len(pts)
                if b:
                    geom[f"{e.dxf.handle}#{i}"] = ("ARC", _arc_from_bulge((x, y), pts[j][:2], b))
    return geom, sorted(mids)


def _storeys(msp, mids):
    clusters, cur = [], []
    for x in mids:
        if cur and x - cur[-1] > 8000:
            clusters.append(cur)
            cur = []
        cur.append(x)
    clusters.append(cur)
    out = {}
    for e in msp.query("INSERT"):
        if e.dxf.name == "GF":
            tx = e.dxf.insert.x
            near = [c for c in clusters if c[0] - 10000 <= tx <= c[-1] + 10000]
            c = max(near, key=len)
            out["GF"] = (c[0] - 1000, c[-1] + 1000)
    return out


def _gap(geom, ha, hb):
    pa, pb = geom[ha][1], geom[hb][1]
    return min(math.dist(p, q) for p in pa for q in pb)


def _depth(geom, ha, hb):
    (x1, y1), (x2, y2) = geom[ha][1]
    px, py = geom[hb][1][0]
    return abs((x2 - x1) * (y1 - py) - (x1 - px) * (y2 - y1)) / math.dist((x1, y1), (x2, y2))


def _wall_rect(geom, ha, hb):
    """the rectangle between two parallel horizontal or vertical face lines over their overlapped extent."""
    (a1, a2), (b1, b2) = geom[ha][1], geom[hb][1]
    if abs(a1[1] - a2[1]) < 1e-6 and abs(b1[1] - b2[1]) < 1e-6:
        lo, hi = max(min(a1[0], a2[0]), min(b1[0], b2[0])), min(max(a1[0], a2[0]), max(b1[0], b2[0]))
        return [(lo, a1[1]), (hi, a1[1]), (hi, b1[1]), (lo, b1[1])]
    if abs(a1[0] - a2[0]) < 1e-6 and abs(b1[0] - b2[0]) < 1e-6:
        lo, hi = max(min(a1[1], a2[1]), min(b1[1], b2[1])), min(max(a1[1], a2[1]), max(b1[1], b2[1]))
        return [(a1[0], lo), (a1[0], hi), (b1[0], hi), (b1[0], lo)]
    raise R.RuleError(f"{ha} / {hb} are not parallel axis lines")


def read(path):
    import ezdxf

    doc = ezdxf.readfile(path)
    assert doc.header.get("$INSUNITS") == 4, "drawing units are not mm"
    msp = doc.modelspace()
    geom, mids = _segs(msp)
    a0, b0 = _storeys(msp, mids)["GF"]
    cols = []
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.layer == "S-COL.BON" and e.closed:
            p = [(q[0], q[1]) for q in e.get_points()]
            if a0 < p[0][0] < b0:
                cols.append((e.dxf.handle, p))
    out = {"schema": "T612_DRAWN_V1", "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf)",
           "units": "m / m2", "rule": R.RULE_ID, "outlines": {}, "addons": {}, "islands": {}}
    for oid, (s, line, chain, note) in OUTLINES.items():
        for h, _ in chain:
            g = geom[h][1]
            if not a0 < g[0][0] < b0:
                raise R.RuleError(f"{oid}: {h} is not on the {s} plan")
        res = R.outline_gross(geom, chain, cols)
        out["outlines"][oid] = {"storey": s, "engine_line": line, "note": note, "perimeter": str(res["perimeter"]),
                                "area": str(res["area"]), "notch_lm": str(res["notch_lm"]),
                                "wall_lm": str(res["wall_lm"]), "virtual_lm": str(res["virtual_lm"]),
                                "notches": res["notches"], "interior_solids": res["interior_solids"],
                                "edges": [{"handle": e["handle"], "role": e["role"], "lm": str(e["lm"])}
                                          for e in res["edges"]]}
    for name, (kind, (wa, wb), (da, db)) in ADDONS.items():
        w = (_gap(geom, wa, wb) if wa != wb else math.dist(*geom[wa][1])) / 1000
        d = _depth(geom, da, db) / 1000
        out["addons"][name] = {"kind": kind, "width_handles": [wa, wb], "depth_handles": [da, db],
                               "width": str(R.q6(w)), "depth": str(R.q6(d)), "dP": str(R.q6(2 * d)),
                               "dA": str(R.q6(w * d))}
    colmap = dict(cols)
    for name, parts in ISLANDS.items():
        pieces = [(h, colmap[h]) if k == "COL" else ("/".join(h), _wall_rect(geom, *h)) for k, h in parts]
        out["islands"][name] = R.island(pieces)
    out["grid_test"] = _grid_test(geom, a0, b0)
    out["grid_test_3m_margin"] = _grid_test(geom, a0, b0, 3000.0)   # the entrance porch outside D200 included
    return out


HIS_ENTRANCE = ("14.76", "10.46")   # his row 15 (perimeter, area): the grid test target; numbers only


def _grid_test(geom, a0, b0, margin=0.0):
    """every axis rectangle whose sides lie on a drawn horizontal / vertical LINE or a column corner inside the GF open
    room's drawn gross outline box: does any reproduce his entrance row (P and A within his rounding), with 0, 1 or 2
    door reveals of 0.20 walked? A figure match is a coincidence unless every side of the rectangle is drawn over at
    least half its length (otherwise its sides are lines of other elements far away). Returns counts only."""
    import itertools
    full = OUTLINES["GF-OPEN.full"][2]
    box_h = [geom[h][1] for h, _ in full if geom[h][0] == "LINE"]
    xs0 = [p[0] for s in box_h for p in s]
    ys0 = [p[1] for s in box_h for p in s]
    X1, X2, Y1, Y2 = min(xs0) - margin, max(xs0) + margin, min(ys0) - margin, max(ys0) + margin
    xs, ys = {}, {}
    for h, (t, g) in geom.items():
        if t != "LINE" or "#" in h:
            continue
        (x1, y1), (x2, y2) = g
        if not (X1 - 1 <= min(x1, x2) <= X2 and Y1 - 1 <= min(y1, y2) <= Y2):
            continue
        if abs(x1 - x2) < 1e-6 and X1 <= x1 <= X2:
            xs.setdefault(round(x1, 1), []).append((min(y1, y2), max(y1, y2)))
        if abs(y1 - y2) < 1e-6 and Y1 <= y1 <= Y2:
            ys.setdefault(round(y1, 1), []).append((min(x1, x2), max(x1, x2)))

    def support(segs, lo, hi):          # share of the side lo .. hi that drawn lines on its position carry
        return sum(max(0.0, min(b, hi) - max(a, lo)) for a, b in segs) / (hi - lo)

    hp, ha = float(HIS_ENTRANCE[0]), float(HIS_ENTRANCE[1])
    t = float(R.half_unit(2))
    n, hits, carried = 0, 0, 0
    for x1, x2 in itertools.combinations(sorted(xs), 2):
        for y1, y2 in itertools.combinations(sorted(ys), 2):
            w, h = (x2 - x1) / 1000, (y2 - y1) / 1000
            n += 1
            for dp in (0.0, 0.4, 0.8):
                if abs(2 * (w + h) + dp - hp) < t and abs(w * h - ha) < t:
                    hits += 1
                    # a drawn reading needs every side carried by drawn lines over at least half its length
                    if min(support(xs[x1], y1, y2), support(xs[x2], y1, y2), support(ys[y1], x1, x2),
                           support(ys[y2], x1, x2)) >= 0.5:
                        carried += 1
    return {"x_positions": len(xs), "y_positions": len(ys), "rectangles": n, "reproducing_both": hits,
            "reproducing_both_with_sides_drawn": carried}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    d = read(a.dxf)
    txt = json.dumps(d, indent=1, sort_keys=True) + "\n"
    if a.write:
        OUT.write_text(txt, encoding="utf-8")
        print("written", OUT.name)
    else:
        print("re-read", "identical" if OUT.exists() and OUT.read_text(encoding="utf-8") == txt else "DIFFERS")
    for k, v in d["outlines"].items():
        print(k, v["perimeter"], v["area"], "notch", v["notch_lm"], "virtual", v["virtual_lm"],
              "solids", v["interior_solids"])
        for e in v["edges"]:
            print("   ", e["handle"], e["role"], e["lm"])
        print("   notches", v["notches"])
    for k, v in d["addons"].items():
        print(k, v["width"], v["depth"])
    for k, v in d["islands"].items():
        print("island", k, v)
    print("grid", d["grid_test"], d["grid_test_3m_margin"])


if __name__ == "__main__":
    main()
