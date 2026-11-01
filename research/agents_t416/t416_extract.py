"""T-416 own drawing read: every ground-beam BAND of the GROUND BEAMS PLAN (two parallel layer-1 face lines), its drawn
length, what the band passes through (column / neck outlines by handle, frame by frame; the other bands = junctions;
the S-BW rings) and its net (face-to-face) length.

    .work/venv/bin/python -I research/agents_t416/t416_extract.py "<.work/private>/ST7757.dxf"           # check
    .work/venv/bin/python -I research/agents_t416/t416_extract.py "<.work/private>/ST7757.dxf" --write   # rebuild

Writes values, DXF handles and lengths in m only (no coordinate, no drawing text, no name) to
research/agents_t416/ALSENAN_T416_INPUT.json.

Method (every villa; the rules are R-T416-1 .. 5 in t416_rules.py):
  * BAND: two layer-1 LINEs of the GROUND BEAMS PLAN frame (T-141 frame) parallel within 1 degree, 150 .. 450 mm apart,
    with no other parallel layer-1 line between them, over the interval where both are drawn (their common
    projection). Each band has a direction (X, Y or oblique O), a drawn width and a DRAWN length (that common interval,
    along the band centreline). An ARC pair (concentric layer-1 arcs 150 .. 450 mm apart) is a curved band measured
    on the centreline radius over the common sweep.
  * SUPPORTS along a band: the band centreline is cut by (a) the S-COL.BON closed column outlines of the frame read,
    (b) the S-BW rings (lift shaft / pit and the other S-BW ring), (c) the other bands (junction squares). Each cut is
    an interval on the centreline; the union of all cuts is what the band passes through; drawn - union = NET, the
    face-to-face concrete of the beam itself (Q-61 C; R-CONC-OWN-1: the column / neck owns the joint).
  * FRAMES: the GROUND BEAMS PLAN (p.3) outlines are the primary read. The same columns are read on the FOUNDATION
    PLAN (p.2) and the COLUMN & AXIS PLAN (p.1), frames equal in size and offset by whole sheet pitches (the offset is
    checked on the S-BOUN plot polylines as T-141 does); the GROUND FLOOR ROOF SLAB frame (p.4) is read too but it draws
    the columns ABOVE the slab, not the neck through the beam (shown, never used for the beam deduction). A column
    outline is the same column when its centroid lies within 0.30 m of the GBP centroid after the shift.
  * The band centreline is also the AXIS reading: the drawn length is what a lump length 'through the supports' runs.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "ALSENAN_T416_INPUT.json"
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
GBP = (78929.89653886131, 29036.09943562183, 114124.2067251332, 57066.43175431111)   # T-141 GROUND BEAMS PLAN frame
FP_X0 = 117654.3026476346                                                          # T-141 FOUNDATION PLAN frame x0
PITCH = FP_X0 - GBP[0]
FRAMES = {"FP": +1, "CAP": +2, "GFRS": -1}      # p.2, p.1, p.4 in sheet pitches from the GBP frame
W_MIN, W_MAX = 150.0, 450.0
SAME_COL_MM = 300.0
RANK = {"X": 0, "Y": 1, "O": 2, "C": 3}
REACH_MM = 3000.0
FENCE_HANDLES = ("7FE", "7FC", "810")   # GROUND BEAMS PLAN fence band (T-253 / T-403 / T-407), S-BOUN


def _r(x, n=4):
    return round(float(x) + 0.0, n)


def _in(frame_x0, x, y):
    return frame_x0 <= x <= frame_x0 + (GBP[2] - GBP[0]) and GBP[1] <= y <= GBP[3]


def read(dxf):
    import ezdxf
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union

    doc = ezdxf.readfile(dxf)
    msp = doc.modelspace()
    # frame offset check on the plot outline (as research/agents_t141/run_t141_alsenan.py)
    xs = {}
    for e in msp.query("LWPOLYLINE[layer=='S-BOUN']"):
        p = [tuple(v[:2]) for v in e.get_points()]
        for k, x0 in (("GBP", GBP[0]), ("FP", FP_X0)):
            if _in(x0, *p[0]):
                xs.setdefault(k, []).append(min(x for x, _ in p))
    if not xs.get("GBP") or not xs.get("FP") or abs(min(xs["FP"]) - min(xs["GBP"]) - PITCH) > 1.0:
        raise SystemExit("plot outline offset does not match the frame pitch: no frame-to-frame column read")

    lines, arcs = [], []
    for e in msp.query('LINE[layer=="1"]'):
        s, t = e.dxf.start, e.dxf.end
        if _in(GBP[0], (s.x + t.x) / 2, (s.y + t.y) / 2) and s.distance(t) > 50:
            lines.append((e.dxf.handle, (s.x, s.y), (t.x, t.y)))
    for e in msp.query('ARC[layer=="1"]'):
        c = e.dxf.center
        if _in(GBP[0], c.x, c.y):
            arcs.append((e.dxf.handle, (c.x, c.y), e.dxf.radius, e.dxf.start_angle % 360, e.dxf.end_angle % 360))

    def unit(a, b):
        L = math.dist(a, b)
        return ((b[0] - a[0]) / L, (b[1] - a[1]) / L)

    bands = []
    for i, (h1, a1, b1) in enumerate(lines):
        u = unit(a1, b1)
        if u[0] < -1e-9 or (abs(u[0]) < 1e-9 and u[1] < 0):
            u = (-u[0], -u[1])
        n = (-u[1], u[0])
        for h2, a2, b2 in lines[i + 1:]:
            v = unit(a2, b2)
            if abs(u[0] * v[1] - u[1] * v[0]) > math.sin(math.radians(1.0)):
                continue
            off = (a2[0] - a1[0]) * n[0] + (a2[1] - a1[1]) * n[1]
            if not (W_MIN <= abs(off) <= W_MAX):
                continue
            p1 = sorted(((a1[0] * u[0] + a1[1] * u[1]), (b1[0] * u[0] + b1[1] * u[1])))
            p2 = sorted(((a2[0] * u[0] + a2[1] * u[1]), (b2[0] * u[0] + b2[1] * u[1])))
            lo, hi = max(p1[0], p2[0]), min(p1[1], p2[1])
            if hi - lo < 50:
                continue
            o1 = a1[0] * n[0] + a1[1] * n[1]
            # no other parallel line strictly between the two faces over the common interval
            between = False
            for h3, a3, b3 in lines:
                if h3 in (h1, h2):
                    continue
                w = unit(a3, b3)
                if abs(u[0] * w[1] - u[1] * w[0]) > math.sin(math.radians(1.0)):
                    continue
                o3 = a3[0] * n[0] + a3[1] * n[1]
                if min(o1, o1 + off) + 5 < o3 < max(o1, o1 + off) - 5:
                    p3 = sorted(((a3[0] * u[0] + a3[1] * u[1]), (b3[0] * u[0] + b3[1] * u[1])))
                    if min(hi, p3[1]) - max(lo, p3[0]) > 50:
                        between = True
                        break
            if between:
                continue
            oc = o1 + off / 2
            p_lo = (lo * u[0] + oc * n[0], lo * u[1] + oc * n[1])
            p_hi = (hi * u[0] + oc * n[0], hi * u[1] + oc * n[1])
            ang = math.degrees(math.atan2(u[1], u[0])) % 180
            d = "X" if (ang < 1 or ang > 179) else ("Y" if abs(ang - 90) < 1 else "O")
            bands.append({"id": f"{h1}+{h2}", "faces": sorted([h1, h2]), "dir": d, "width_m": _r(abs(off) / 1e3, 3),
                          "drawn_m": _r((hi - lo) / 1e3), "_cl": LineString([p_lo, p_hi]),
                          "_poly": LineString([p_lo, p_hi]).buffer(abs(off) / 2, cap_style=2)})
    for i, (h1, c1, r1, s1, e1) in enumerate(arcs):
        for h2, c2, r2, s2, e2 in arcs[i + 1:]:
            if math.dist(c1, c2) > 5 or not (W_MIN <= abs(r1 - r2) <= W_MAX):
                continue

            def span(s, e):
                return (s, e if e > s else e + 360)
            A, B = span(s1, e1), span(s2, e2)
            lo, hi = max(A[0], B[0]), min(A[1], B[1])
            if hi - lo <= 0:
                A, B = (A[0] + 360, A[1] + 360), B
                lo, hi = max(A[0], B[0]), min(A[1], B[1])
            rc = (r1 + r2) / 2
            pts = [(c1[0] + rc * math.cos(math.radians(lo + (hi - lo) * k / 96)),
                    c1[1] + rc * math.sin(math.radians(lo + (hi - lo) * k / 96))) for k in range(97)]
            cl = LineString(pts)
            bands.append({"id": f"ARC:{h1}+{h2}", "faces": sorted([h1, h2]), "dir": "C",
                          "width_m": _r(abs(r1 - r2) / 1e3, 3), "drawn_m": _r(cl.length / 1e3),
                          "sweep_deg": _r(hi - lo, 3), "r_centre_m": _r(rc / 1e3, 3),
                          "_cl": cl, "_poly": cl.buffer(abs(r1 - r2) / 2, cap_style=2)})

    # supports: columns per frame, S-BW rings
    cols = {k: [] for k in ("GBP",) + tuple(FRAMES)}
    rings = []
    for e in msp.query('LWPOLYLINE[layer=="S-COL.BON" | layer=="S-BW"]'):
        if not e.closed:
            continue
        p = Polygon([tuple(v)[:2] for v in e.get_points("xy")]).buffer(0)
        c = p.centroid
        if e.dxf.layer == "S-BW":
            if _in(GBP[0], c.x, c.y):
                rings.append((e.dxf.handle, p))
            continue
        if _in(GBP[0], c.x, c.y):
            cols["GBP"].append((e.dxf.handle, p))
        for k, m in FRAMES.items():
            if _in(GBP[0] + m * PITCH, c.x, c.y):
                from shapely.affinity import translate
                cols[k].append((e.dxf.handle, translate(p, xoff=-m * PITCH)))

    def cut(cl, poly):
        g = cl.intersection(poly)
        if g.is_empty:
            return []
        parts = list(g.geoms) if hasattr(g, "geoms") else [g]
        out = []
        for q in parts:
            if q.length < 1.0:
                continue
            a, b = cl.project(q.interpolate(0.0)), cl.project(q.interpolate(q.length))
            out.append((min(a, b), max(a, b)))
        return out

    def union_len(iv):
        iv = sorted(iv)
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
        return tot

    for b in bands:
        cl = b["_cl"]
        L = cl.length
        sup = {"rings": [], "junctions": []}
        iv_common = []
        for h, p in rings:
            for a, z in cut(cl, p.buffer(0.5)):
                sup["rings"].append({"handle": h, "m": _r((z - a) / 1e3, 3), "a_m": _r(a / 1e3), "b_m": _r(z / 1e3),
                                     "at_end": a < 2 or z > L - 2})
                iv_common.append((a, z))
        for o in bands:
            if o is b or o["dir"] == b["dir"] and o["dir"] in "XY":
                continue
            # a junction square inside two bands is owned once (R-T416-2): X over Y, straight over curved / oblique
            owner = o if RANK[o["dir"]] < RANK[b["dir"]] else b
            for a, z in cut(cl, o["_poly"].buffer(0.5)):
                if z - a < 20:
                    continue
                sup["junctions"].append({"band": o["id"], "m": _r((z - a) / 1e3, 3), "a_m": _r(a / 1e3),
                                         "b_m": _r(z / 1e3), "at_end": a < 2 or z > L - 2,
                                         "owned_here": owner is b})
                if owner is not b:
                    iv_common.append((a, z))
        by_frame = {}
        for k in cols:
            ivs, rows = [], []
            for h, p in cols[k]:
                for a, z in cut(cl, p.buffer(0.5)):
                    rows.append({"handle": h, "m": _r((z - a) / 1e3, 3), "a_m": _r(a / 1e3), "b_m": _r(z / 1e3),
                                 "at_end": a < 2 or z > L - 2})
                    ivs.append((a, z))
            by_frame[k] = {"columns": rows, "net_m": _r((L - union_len(iv_common + ivs)) / 1e3),
                           "columns_only_m": _r(union_len(ivs) / 1e3)}
        b["supports"] = sup
        b["frames"] = by_frame
        b["junctions_and_rings_m"] = _r(union_len(iv_common) / 1e3)
    # END SUPPORT of a straight band: from each end of the drawn face lines, walk outward on the centreline (1 mm) while
    # the point stays inside another band, a GBP column outline or an S-BW ring; the extent is what a length taken
    # 'to the far face of the support' adds there (the axis reading adds half of it). Curved / oblique bands: not walked.
    from shapely.geometry import Point
    stuff = unary_union([o["_poly"] for o in bands] + [p for _, p in cols["GBP"]] + [p for _, p in rings]).buffer(1.0)
    for b in bands:
        b["end_support_m"] = None
        if b["dir"] not in "XY":
            continue
        (x0, y0), (x1, y1) = b["_cl"].coords[0], b["_cl"].coords[-1]
        ux, uy = (x1 - x0) / b["_cl"].length, (y1 - y0) / b["_cl"].length
        same = [o["_poly"] for o in bands if o is not b and o["dir"] == b["dir"]]
        ends = []
        for (px, py), s in (((x0, y0), -1.0), ((x1, y1), +1.0)):
            t, stop, ring = 1.0, "LINE_END", False
            while t <= REACH_MM:
                q = Point(px + s * ux * t, py + s * uy * t)
                if not stuff.contains(q):
                    break
                if any(g.contains(q) for g in same):
                    stop = "THROUGH"          # the line continues in a collinear band: the support is shared
                    break
                if any(p.contains(q) for _, p in rings):
                    ring = True
                t += 1.0
            if t > REACH_MM:
                stop = "REACH"
            ends.append({"m": _r((t - 1.0) / 1e3, 3), "stop": stop, "ring": ring})
        b["end_support_m"] = ends
    # END COLUMNS frame by frame (O-T407-1): where a straight band's drawn face lines stop at a column outside the band,
    # the same column on FP / CAP / GFRS may have its near face elsewhere; the net on that frame moves by that shift
    # (the face lines are drawn on the GBP only; the beam runs to the neck face of whichever frame is read).
    gb_poly = dict(cols["GBP"])
    same = {}
    for h, p in cols["GBP"]:
        for k in FRAMES:
            hit = [q for hh, q in cols[k] if q.centroid.distance(p.centroid) < SAME_COL_MM]
            same[(h, k)] = hit[0] if len(hit) == 1 else None
    for b in bands:
        b["end_columns"] = []
        for k in ("GBP",) + tuple(FRAMES):
            b["frames"][k]["net_with_end_faces_m"] = b["frames"][k]["net_m"]
        if b["dir"] not in "XY":
            continue
        cl = b["_cl"]
        (x0, y0), (x1, y1) = cl.coords[0], cl.coords[-1]
        ux, uy = (x1 - x0) / cl.length, (y1 - y0) / cl.length
        for end, (px, py), sgn in ((0, (x0, y0), -1.0), (1, (x1, y1), +1.0)):
            probe = Point(px + sgn * ux * 5.0, py + sgn * uy * 5.0)
            hits = [h for h, p in cols["GBP"] if p.buffer(0.5).contains(probe)]
            if len(hits) != 1:
                continue
            h = hits[0]

            def near(poly):
                pr = [vx * ux + vy * uy for vx, vy in poly.exterior.coords]
                return max(pr) if sgn < 0 else min(pr)
            g = near(gb_poly[h])
            row = {"end": end, "handle": h, "net_shift_m": {}}
            for k in FRAMES:
                q = same[(h, k)]
                if q is None:
                    row["net_shift_m"][k] = None
                    continue
                d = (near(q) - g) * (-1.0 if sgn < 0 else 1.0)       # + = the face recedes: the beam is longer
                row["net_shift_m"][k] = _r(d / 1e3, 4)
                b["frames"][k]["net_with_end_faces_m"] = _r(b["frames"][k]["net_with_end_faces_m"] + d / 1e3)
            b["end_columns"].append(row)
    # R-T416-5 guard: the GROUND BEAMS PLAN fence band (S-BOUN 7FE / 7FC / 810, T-253 / T-403 / T-407) shares no
    # length with any house band centreline
    fence = []
    for h in FENCE_HANDLES:
        e = doc.entitydb.get(h)
        if e is not None and e.dxftype() == "LWPOLYLINE":     # the outline of the 0.20 band strip (closed by its ends)
            fence.append(Polygon([tuple(v)[:2] for v in e.get_points("xy")]).buffer(0))
    fz = unary_union(fence).buffer(-1.0) if fence else None     # strictly inside the fence strip
    guard = {"fence_handles_found": len(fence),
             "house_centreline_inside_fence_band_m": _r(sum(b["_cl"].intersection(fz).length for b in bands) / 1e3)
             if fz is not None else None}
    # the same column on two frames: centroid within SAME_COL_MM
    pairs = []
    for h, p in cols["GBP"]:
        row = {"GBP": h}
        for k in FRAMES:
            hit = [hh for hh, q in cols[k] if q.centroid.distance(p.centroid) < SAME_COL_MM]
            row[k] = hit[0] if len(hit) == 1 else None
        pairs.append(row)
    for b in bands:
        b.pop("_cl")
        b.pop("_poly")
    return bands, pairs, guard


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    dxf = argv[0]
    if hashlib.sha256(Path(dxf).read_bytes()).hexdigest() != DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    bands, pairs, guard = read(dxf)
    doc = {"schema": "T416_GB_BANDS_INPUT_V1", "structural_sha256": DXF_SHA, "frame": "T-141 GROUND BEAMS PLAN",
           "frames": {"GBP": "p.3 GROUND BEAMS PLAN (primary)", "FP": "p.2 FOUNDATION PLAN",
                      "CAP": "p.1 COLUMN & AXIS PLAN", "GFRS": "p.4 GROUND FLOOR ROOF SLAB (columns above the slab: shown only)"},
           "bands": sorted(bands, key=lambda b: (b["dir"], b["id"])), "column_frames": pairs, "guards": guard}
    txt = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        OUT.write_text(txt, encoding="utf-8")
        print("written", OUT.name, len(bands), "bands")
    else:
        same = OUT.exists() and OUT.read_text(encoding="utf-8") == txt
        print("REPRODUCED" if same else "DIFFERS")
        if not same:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
