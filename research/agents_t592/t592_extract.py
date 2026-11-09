"""T-592 development-villa DRAWING READ (research, unwired): per external door / gate step, the WALL GAP (masonry
opening) on each face, the drawn nosing edge and its companion, the frame jamb widths of the door block, and the
printed levels REACHABLE on each side of the opening (R-T592-1 (d)), read BY ENTITY HANDLE from the architectural DXF
(Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip, decoded into .work/private only).

    .work/venv/bin/python -I research/agents_t592/t592_extract.py --dxf <P7757.dxf> --write
    .work/venv/bin/python -I research/agents_t592/t592_extract.py --dxf <P7757.dxf>          (re-read, compare)

Method (in the insert's own frame: x along the wall over the block span, y across it, face y = 0 and y = depth):
  * wall gap on a face: the layer 1 / 5 lines lying on that face (|dy| <= 10 mm) and parallel to it; the gap is the
    distance between the last line end left of the opening centre and the first line start right of it; a line that
    runs THROUGH the opening on a face (a fence face drawn across a gate) gives no gap on that face;
  * nosing edge: the layer 5 line on the step face inside the span (T-584 handles); companion: the layer 2 line 0.050
    uphill; where the face line runs through (the gate), the visible edge is read from the companion (equal to the
    edge at every house door, Checker T-584);
  * jambs: the door block's frame rectangles at each end of the span (block lines at x = span ends);
  * reachable levels: every printed level text (or the +-0.00 datum block LEL) that a straight sight line from a start
    point on that side reaches without crossing ANY drawn line (all model-space LINE / LWPOLYLINE / ARC except the
    TEXT layer, plus the exploded door / arch blocks), directly or through ONE waypoint of a 0.25 m grid visible from the
    start (two legs). Start points: 0.08 m beyond the low face; on the high side beyond the door leaf swing and beside the
    closing jamb (outside the swing arc) and inside the swing; the union of what they reach. Region
    figures only (handles + figures); no coordinate, no drawing text other than level figures, no client name.
Writes T592_DRAWN.json; the builder t592_alsenan.py reads only that JSON."""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "T592_DRAWN.json"
MM = 0.001
LEVEL_RE = re.compile(r"^[+\-]?\d+\.\d\d$")
# opening id -> (insert handle, step face y in block units: 0 = the face carrying the layer-5 edge, high side sign)
OPENINGS = {
    "D-GF-01": "15E",
    "D-GF-03": "1B5",
    "D-GF-05": "192",
    "D-GF-09": "3FF",
    "D-GF-15": "2D8",
}
GRID = 0.25 / MM          # waypoint grid step (block units = mm)


def read(dxf_path):
    import ezdxf
    from shapely.geometry import LineString
    from shapely.strtree import STRtree

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    assert doc.header.get("$INSUNITS") == 4, "drawing units are not mm"
    levels = []
    for e in msp.query("TEXT"):
        t = e.dxf.text.strip()
        if LEVEL_RE.match(t):
            levels.append((e.dxf.handle, t, (e.dxf.insert.x, e.dxf.insert.y)))
    for e in msp.query("INSERT"):
        if e.dxf.name == "LEL":
            levels.append((e.dxf.handle, "+-0.00", (e.dxf.insert.x, e.dxf.insert.y)))
    ents = [e for e in msp.query("LINE LWPOLYLINE ARC") if e.dxf.layer != "TEXT"]
    for ins in msp.query("INSERT"):
        if ins.dxf.name[:1] in "Dd" or ins.dxf.name in ("AR1", "arch120"):
            ents += [v for v in ins.virtual_entities() if v.dxftype() in ("LINE", "LWPOLYLINE", "ARC")]
    geoms = []
    for e in ents:
        if e.dxftype() == "LINE":
            geoms.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
        elif e.dxftype() == "ARC":
            geoms.append(LineString([(v.x, v.y) for v in e.flattening(10)]))
        else:
            pts = [(q[0], q[1]) for q in e.get_points()]
            if e.closed:
                pts.append(pts[0])
            if len(pts) > 1:
                geoms.append(LineString(pts))
    tree = STRtree(geoms)

    def clear(a, b):
        s = LineString([a, b])
        return not any(geoms[i].intersects(s) for i in tree.query(s))

    face_lines = [(q.dxf.handle, q.dxf.layer, q.dxf.start, q.dxf.end) for q in msp.query("LINE")
                  if q.dxf.layer in ("1", "5", "2")]
    out = {}
    for oid, h in OPENINGS.items():
        ins = doc.entitydb.get(h)
        assert ins is not None and ins.dxftype() == "INSERT", (oid, h)
        blk = doc.blocks.get(ins.dxf.name)
        bl = [b for b in blk if b.dxftype() == "LINE"]
        xs = [v for b in bl for v in (b.dxf.start.x, b.dxf.end.x)]
        span = (min(xs), max(xs))
        c = (span[0] + span[1]) / 2
        # wall depth = the frame jamb's across-wall extent at x = span[0]
        jy = [v for b in bl if abs(b.dxf.start.x - span[0]) < 1e-6 and abs(b.dxf.end.x - span[0]) < 1e-6
              for v in (b.dxf.start.y, b.dxf.end.y)]
        depth = max(jy) - min(jy)
        # jamb widths: the short block lines along x at y = 0 starting at a span end
        def jamb(at):
            w = [abs(b.dxf.end.x - b.dxf.start.x) for b in bl if abs(b.dxf.start.y) < 1e-6 and abs(b.dxf.end.y) < 1e-6
                 and min(abs(b.dxf.start.x - at), abs(b.dxf.end.x - at)) < 1e-6]
            return min(w) if w else None
        jambs = (jamb(span[0]), jamb(span[1]))
        m = ins.matrix44()
        inv = m.copy()
        inv.inverse()
        faces = {"0": {"left": None, "right": None, "through": []}, "depth": {"left": None, "right": None, "through": []}}
        edges = []
        for lh, lay, s, e in face_lines:
            a, b = inv.transform(s), inv.transform(e)
            if abs(a.y - b.y) > 2 or abs(a.x - b.x) < 1:
                continue
            x0, x1 = min(a.x, b.x), max(a.x, b.x)
            y = (a.y + b.y) / 2
            for fk, fy in (("0", 0.0), ("depth", depth)):
                if abs(y - fy) > 10 or lay == "2":
                    continue
                if span[0] - 60 <= x0 and x1 <= span[1] + 60:
                    continue                      # an edge inside the opening is not a wall line
                if x0 < c < x1:
                    faces[fk]["through"].append(lh)
                elif x1 <= c and x1 >= span[0] - 400 and (faces[fk]["left"] is None or x1 > faces[fk]["left"][1]):
                    faces[fk]["left"] = (lh, x1)
                elif x0 >= c and x0 <= span[1] + 400 and (faces[fk]["right"] is None or x0 < faces[fk]["right"][1]):
                    faces[fk]["right"] = (lh, x0)
            if span[0] - 60 <= x0 and x1 <= span[1] + 60 and -60 <= y <= 60 and lay in ("5", "2"):
                edges.append({"handle": lh, "layer": lay, "length_m": round((x1 - x0) * MM, 6),
                              "offset_from_face_m": round(y * MM, 3)})
        gaps = {}
        for fk, f in faces.items():
            if f["through"] or f["left"] is None or f["right"] is None:
                gaps[fk] = {"gap_m": None, "through": sorted(f["through"])}
            else:
                gaps[fk] = {"gap_m": round((f["right"][1] - f["left"][1]) * MM, 6),
                            "ends": [f["left"][0], f["right"][0]], "through": [],
                            "ends_vs_block_span_m": [round((f["left"][1] - span[0]) * MM, 3),
                                                     round((span[1] - f["right"][1]) * MM, 3)]}
        # reachable levels, low side (y < 0) and high side (beyond the door leaf swing)
        def reach(starts_local, sign, y0):
            starts = [tuple(m.transform((x, y, 0)))[:2] for x, y in starts_local]
            way = []
            for i in range(-40, 41):
                for j in range(1, 61):
                    w = tuple(m.transform((c + i * GRID, y0 + sign * j * GRID, 0)))[:2]
                    if any(clear(p, w) for p in starts):
                        way.append(w)
            got = {}
            for lh, t, p in levels:
                if min(math.dist(s, p) for s in starts) > 20000:
                    continue
                if any(clear(s, p) for s in starts) or any(clear(w, p) for w in way):
                    got.setdefault(t, []).append(lh)
            return {k: sorted(v) for k, v in sorted(got.items())}
        low = reach([(c, -80.0)], -1, 0.0)
        leaf = max(abs(b.dxf.end.y) for b in bl)
        high = reach([(c, leaf + 60.0), (span[1] - 25.0, depth + 60.0), (c, depth + 80.0)], 1, depth)
        out[oid] = {"insert": h, "block": ins.dxf.name, "block_span_m": round((span[1] - span[0]) * MM, 3),
                    "wall_depth_m": round(depth * MM, 3), "jambs_m": [round(j * MM, 3) if j else None for j in jambs],
                    "wall_gap_face0": gaps["0"], "wall_gap_face_depth": gaps["depth"],
                    "edges_on_face0": sorted(edges, key=lambda z: (z["offset_from_face_m"], z["handle"])),
                    "levels_reachable_low": low, "levels_reachable_high": high}
    plan = sorted({t for _, t, _ in levels})
    return {"schema": "T592_DRAWN_V1", "drawing": "Drive 'Alsenan chalet project' P7757_DXF_COMPRESSED.zip "
            "(architectural DXF), read by handle", "units": "m", "openings": out, "plan_level_figures": plan,
            "detail_sheets": "none: no door / threshold detail or section in the DXF (24 distinct model-space texts) "
                             "or the PDF set (T-360 sheet census: plans, elevations, sections A-A / B-B, fence sheet)"}


def main(argv):
    if "--dxf" not in argv:
        raise SystemExit("--dxf <P7757.dxf> required (private input, .work/private)")
    got = read(argv[argv.index("--dxf") + 1])
    txt = json.dumps(got, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        OUT.write_text(txt, encoding="utf-8")
        print(f"wrote {OUT.name}")
    else:
        print("REPRODUCED" if OUT.exists() and OUT.read_text(encoding="utf-8") == txt else "DIFFERS")


if __name__ == "__main__":
    main(sys.argv[1:])
