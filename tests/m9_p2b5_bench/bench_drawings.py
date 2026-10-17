"""BENCHMARK DRAWINGS - writes each benchmark case (bench_cases.py) as

    dxf(case, path)                  a DXF plan drawn with tools/arch_synth's plan writer (A-WALL, A-DOOR, A-GLAZ,
                                     A-COL, A-TEXT layers; a sheet frame and title), mirrored and turned as the case
                                     says, or the case's own drawn primitives (arcs, bulges); an `encoding` writes the
                                     same plan another way (nested / non-uniform blocks, metres, polylines, Arabic words
                                     and DIMENSIONs, a window block, an XREF)
    raster(case, path, mm_per_px)    a PNG of the same linework (walls, glazing, door leaves and swings, room words),
                                     with an optional 'scan' degradation (blur, noise, a 0.4 degree skew)
    vector_pdf(case, path)           a one-page PDF whose linework is vector paths at a known scale

Synthetic geometry only. Every file is deterministic (fixed seeds, fixed DXF metadata)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import arch_synth as AS                            # noqa: E402

FRAME = AS.FRAMES["GF"]
PDF_SCALE = 100.0                                             # 1:100 (drawing mm per paper mm)


class _Rec:
    """records the calls tools/arch_synth makes on a modelspace, so the plan can be turned by any angle."""

    def __init__(self):
        self.ops = []

    def add_line(self, a, b, dxfattribs):
        self.ops.append(("LINE", (a, b), dxfattribs))

    def add_blockref(self, name, p, dxfattribs):
        self.ops.append(("INSERT", (name, p), dxfattribs))

        class _B:
            def add_auto_attribs(self_, d):
                return self_
        return _B()

    def add_text(self, text, dxfattribs):
        rec = ["TEXT", [text, None], dxfattribs]
        self.ops.append(rec)

        class _T:
            def set_placement(self_, p):
                rec[1][1] = p
                return self_
        return _T()

    def add_lwpolyline(self, pts, close=False, dxfattribs=None):
        self.ops.append(("PLINE", (list(pts), close), dxfattribs or {}))

    def add_hatch(self, dxfattribs):
        rec = ["HATCH", [], dxfattribs]
        self.ops.append(rec)

        class _H:
            class paths:
                @staticmethod
                def add_polyline_path(pts, is_closed=True):
                    rec[1].append(list(pts))

            def set_solid_fill(self_):
                return None
        return _H()


def _turn(case):
    """the case's placement: x -> -x about the plan centre when `mirror`, then a turn by `rotate_deg` about it."""
    th = math.radians(case.get("rotate_deg") or 0.0)
    m = -1.0 if case.get("mirror") else 1.0
    xs, ys = [p[0] for p in case["outer"]], [p[1] for p in case["outer"]]
    c = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)

    def T(p):
        x, y = m * (p[0] - c[0]), p[1] - c[1]
        return (c[0] + x * math.cos(th) - y * math.sin(th), c[1] + x * math.sin(th) + y * math.cos(th))
    return T, math.degrees(th)


def _drawn(rec, case):
    """the case's own primitives (bench_cases 'draw'), in the recorder's form."""
    for d in case["draw"]:
        if d[0] == "LINE":
            rec.add_line(d[2], d[3], dxfattribs={"layer": d[1]})
        elif d[0] == "ARC":
            rec.ops.append(("ARC", (d[2], d[3], d[4], d[5]), {"layer": d[1]}))
        elif d[0] == "PLINE":
            rec.ops.append(("BPLINE", (list(d[2]), d[3]), {"layer": d[1]}))
        elif d[0] == "INSERT":
            rec.add_blockref(d[2], d[3], dxfattribs={"layer": d[1], "rotation": d[4], "xscale": d[5], "yscale": d[6]})
        elif d[0] == "TEXT":
            rec.add_text(d[2], dxfattribs={"layer": d[1], "height": d[4]}).set_placement(d[3])


def ops(case):
    """the plan as primitive operations in world coordinates (mm)."""
    rec = _Rec()
    if "draw" in case:
        _drawn(rec, case)
    else:
        AS._plan(rec, rooms=case["rooms"], outer=case["outer"], labels=case["labels"], words=case["words"],
                 openings=case["openings"], columns=case["columns"], level="+0.00", treads=(), origin=FRAME[2],
                 dx=0.0, dy=0.0, mirror=False, quarter_turns=0)
    T, deg = _turn(case)
    mir = bool(case.get("mirror"))
    out = []
    for kind, data, att in rec.ops:
        att = dict(att)
        if kind == "LINE":
            out.append((kind, (T(data[0]), T(data[1])), att))
        elif kind == "INSERT":
            if mir:                                       # Mx R(r) S(sx, sy) = R(-r) S(-sx, sy)
                att["rotation"] = -att.get("rotation", 0.0)
                att["xscale"] = -att.get("xscale", 1.0)
            att["rotation"] = (att.get("rotation", 0.0) + deg) % 360
            out.append((kind, (data[0], T(data[1])), att))
        elif kind == "ARC":
            (cx, cy), r, a0, a1 = data
            if mir:
                a0, a1 = 180.0 - a1, 180.0 - a0
            out.append((kind, (T((cx, cy)), r, (a0 + deg) % 360, (a1 + deg) % 360), att))
        elif kind == "BPLINE":
            out.append((kind, ([(*T(p[:2]), -p[2] if mir else p[2]) for p in data[0]], data[1]), att))
        elif kind == "TEXT":
            out.append((kind, (data[0], T(data[1])), att))
        elif kind == "PLINE":
            out.append((kind, ([T(p) for p in data[0]], data[1]), att))
        elif kind == "HATCH":
            out.append((kind, [[T(p) for p in path] for path in data], att))
    return out


def _arc_pts(c, r, a0, a1, step=1.0):
    """an arc (degrees, counter-clockwise a0 -> a1) as points on a fixed grid of whole `step` degrees plus its ends:
    two concentric arcs flattened this way have parallel chords (the vision readers pair wall faces by parallels)."""
    a1 = a1 if a1 > a0 else a1 + 360.0
    k0, k1 = math.floor(a0 / step) + 1, math.ceil(a1 / step) - 1
    angs = [a0] + [k * step for k in range(k0, k1 + 1) if a0 + 1e-9 < k * step < a1 - 1e-9] + [a1]
    return [(c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a))) for a in angs]


def _bulge_pts(pts, closed):
    out = []
    seq = list(pts) + ([pts[0]] if closed else [])
    for (x0, y0, b), (x1, y1, _) in zip(seq, seq[1:]):
        if abs(b) < 1e-12:
            out += [(x0, y0), (x1, y1)]
            continue
        th = 4.0 * math.atan(b)                           # the included angle, signed (+ counter-clockwise)
        ch = math.dist((x0, y0), (x1, y1))
        r = ch / (2.0 * math.sin(abs(th) / 2.0))
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        d = r * math.cos(th / 2.0)                        # centre offset from the chord mid point, to the left
        ux, uy = (x1 - x0) / ch, (y1 - y0) / ch
        c = (mx - uy * d * math.copysign(1, b), my + ux * d * math.copysign(1, b))
        a0 = math.degrees(math.atan2(y0 - c[1], x0 - c[0]))
        a1 = a0 + math.degrees(th)
        seg = _arc_pts(c, r, min(a0, a1), max(a0, a1))
        out += seg if th > 0 else seg[::-1]
    return out


def truth_polygons(case):
    """the truth room polygons (and column squares) in world coordinates (mm); an arc room is flattened at 0.05 deg
    (the chord error at r 2.5 m is 1e-3 mm)."""
    T, _ = _turn(case)
    rooms = {k: [T(p) for p in v] for k, v in case["rooms"].items()}
    for k, a in (case.get("arc_room") or {}).items():
        ring = list(a["straight"]) + _arc_pts(a["centre"], a["r"], a["a0_deg"], a["a1_deg"], step=0.05)[:-1]
        rooms[k] = [T(p) for p in ring]
    cols = [[T(p) for p in ((x, y), (x + 400, y), (x + 400, y + 400), (x, y + 400))] for x, y in case["columns"]]
    labels = {k: T(p) for k, p in case["labels"].items()}
    return rooms, cols, labels


def _chains(segs):
    """wall-face segments chained end to end where exactly two meet: a closed chain is a wall band ring."""
    from collections import defaultdict
    key = lambda p: (round(p[0], 6), round(p[1], 6))                     # noqa: E731
    adj = defaultdict(list)
    for i, (a, b) in enumerate(segs):
        adj[key(a)].append(i)
        adj[key(b)].append(i)
    used, out = set(), []
    for i in range(len(segs)):
        if i in used:
            continue
        used.add(i)
        ch = [segs[i][0], segs[i][1]]
        for end in (-1, 0):
            while True:
                k = key(ch[end])
                nxt = [j for j in adj[k] if j not in used]
                if len(adj[k]) != 2 or not nxt:
                    break
                used.add(nxt[0])
                a, b = segs[nxt[0]]
                q = b if key(a) == k else a
                ch.append(q) if end == -1 else ch.insert(0, q)
        closed = len(ch) > 3 and key(ch[0]) == key(ch[-1])
        out.append((ch[:-1] if closed else ch, closed))
    return out


def _window_inserts(case):
    """(insert point, rotation, xscale) of a unit glazing block (1000 along the wall) for every window of the case."""
    T, deg = _turn(case)
    out = []
    for kind, axis, lo, hi, s0, s1, _ in case["openings"]:
        if kind == "WINDOW":
            p, r = ((hi, s0), 90.0) if axis == "x" else ((s0, lo), 0.0)
            out.append((T(p), (r + deg) % 360, (s1 - s0) / 1000.0))
    return out


def dxf(case, path):
    """the case as a DXF. encoding (bench_cases ENCODED; the WCS geometry stays the base case's):
    nested_walls - the A-WALL lines inside block WALLS_IN, inserted non-uniformly scaled in block WALLS_OUT, inserted
                   mirrored / turned / moved in model space (the block contents are the inverse transform of the plan)
    metres       - $INSUNITS 6, every coordinate and text height / 1000
    polylines    - the wall faces chained into LWPOLYLINEs (closed bands; every other ring, from the first, written
                   as two open runs)
    dimensions   - linear DIMENSIONs (layer A-DIM): one across each room outside the plan, one inside a room with a
                   text override
    window_block - the glazing lines as INSERTs of a unit block WIN1000
    xref_walls   - the A-WALL lines replaced by an INSERT of an external reference whose file is not supplied"""
    import ezdxf
    enc = case.get("encoding") or {}
    k = 0.001 if enc.get("metres") else 1.0                  # drawing units per mm
    S = lambda p: (p[0] * k, p[1] * k)                       # noqa: E731
    fixed = ezdxf.options.write_fixed_meta_data_for_testing
    ezdxf.options.write_fixed_meta_data_for_testing = True
    try:
        doc = ezdxf.new("R2018")
        doc.header["$INSUNITS"] = 6 if enc.get("metres") else 4
        blk = doc.blocks.new("DOOR1000")
        blk.add_line((0, 0), (1000 * k, 0), dxfattribs={"layer": "0"})
        blk.add_arc((0, 0), 1000 * k, 0, 90, dxfattribs={"layer": "0"})
        msp = doc.modelspace()
        (x0, y0), (x1, y1), org, title = FRAME
        msp.add_lwpolyline([S((x0, y0)), S((x1, y0)), S((x1, y1)), S((x0, y1))], close=True,
                           dxfattribs={"layer": "A-FRAME"})
        msp.add_text(title, dxfattribs={"layer": "A-TITLE", "height": 500 * k}).set_placement(S((x0 + 2000, y0 + 1500)))
        allops = ops(case)
        walls = [d for kind, d, att in allops if kind == "LINE" and att.get("layer") == "A-WALL"]
        skip_walls = any(enc.get(x) for x in ("nested_walls", "polylines", "xref_walls"))
        skip_glaz = bool(enc.get("window_block"))
        for kind, data, att in allops:
            if kind == "LINE":
                if (skip_walls and att.get("layer") == "A-WALL") or (skip_glaz and att.get("layer") == "A-GLAZ"):
                    continue
                msp.add_line(S(data[0]), S(data[1]), dxfattribs=att)
            elif kind == "INSERT":
                msp.add_blockref(data[0], S(data[1]), dxfattribs=att)
            elif kind == "TEXT":
                att = dict(att, height=att.get("height", 200) * k)
                msp.add_text(data[0], dxfattribs=att).set_placement(S(data[1]))
            elif kind == "PLINE":
                msp.add_lwpolyline([S(q) for q in data[0]], close=data[1], dxfattribs=att)
            elif kind == "ARC":
                c, r, a0, a1 = data
                msp.add_arc(S(c), r * k, a0, a1, dxfattribs=att)
            elif kind == "BPLINE":
                msp.add_lwpolyline([(*S(q[:2]), 0, 0, q[2]) for q in data[0]], format="xyseb", close=data[1],
                                   dxfattribs=att)
            elif kind == "HATCH":
                h = msp.add_hatch(dxfattribs=att)
                h.set_solid_fill()
                for q in data:
                    h.paths.add_polyline_path([S(v) for v in q], is_closed=True)
        if enc.get("nested_walls"):
            nw = enc["nested_walls"]
            (ix, iy), rot, ox = nw["outer_insert"], math.radians(nw["outer_rotation"]), nw["outer_xscale"]
            sx, sy = nw["inner_scale"]

            def local(p):                                     # (M1 M2)^-1 p, M1 = T R(rot) S(ox, 1), M2 = S(sx, sy)
                u, v = p[0] - ix, p[1] - iy
                u, v = u * math.cos(rot) + v * math.sin(rot), -u * math.sin(rot) + v * math.cos(rot)
                return (u / ox / sx, v / sy)
            inner = doc.blocks.new("WALLS_IN")
            for a, b in walls:
                inner.add_line(local(S(a)), local(S(b)), dxfattribs={"layer": "0"})
            outer = doc.blocks.new("WALLS_OUT")
            outer.add_blockref("WALLS_IN", (0, 0), dxfattribs={"layer": "0", "xscale": sx, "yscale": sy})
            msp.add_blockref("WALLS_OUT", (ix, iy), dxfattribs={"layer": "A-WALL", "rotation": nw["outer_rotation"],
                                                                "xscale": ox})
        if enc.get("polylines"):
            for n, (ch, closed) in enumerate(_chains(walls)):
                pts = [S(q) for q in ch]
                if closed and n % 2 == 0:                     # this ring written as two open runs
                    m = len(pts) // 2
                    msp.add_lwpolyline(pts[:m + 1], dxfattribs={"layer": "A-WALL"})
                    msp.add_lwpolyline(pts[m:] + [pts[0]], dxfattribs={"layer": "A-WALL"})
                else:
                    msp.add_lwpolyline(pts, close=closed, dxfattribs={"layer": "A-WALL"})
        if enc.get("xref_walls"):
            doc.add_xref_def(enc["xref_walls"], "WALLS_XREF")
            msp.add_blockref("WALLS_XREF", (0, 0), dxfattribs={"layer": "A-WALL"})
        if enc.get("window_block"):
            win = doc.blocks.new("WIN1000")
            for f in (1 / 3, 2 / 3):
                win.add_line((0, 200 * k * f), (1000 * k, 200 * k * f), dxfattribs={"layer": "0"})
            for p0, r, w in _window_inserts(case):
                msp.add_blockref("WIN1000", S(p0), dxfattribs={"layer": "A-GLAZ", "rotation": r, "xscale": w})
        if enc.get("dimensions"):
            T, _ = _turn(case)
            for n, (name, poly) in enumerate(sorted(case["rooms"].items())):
                xs, ys = [q[0] for q in poly], [q[1] for q in poly]
                d = msp.add_linear_dim(base=S(T((min(xs), -900))), p1=S(T((min(xs), 0))), p2=S(T((max(xs), 0))),
                                       dxfattribs={"layer": "A-DIM"})
                d.render()
                if n == 0:                                    # inside the room, its text overridden
                    d = msp.add_linear_dim(base=S(T((min(xs), min(ys) + 600))), p1=S(T((min(xs), min(ys) + 600))),
                                           p2=S(T((max(xs), min(ys) + 600))), text="<> CLEAR",
                                           dxfattribs={"layer": "A-DIM"})
                    d.render()
        doc.classes.add_required_classes(doc.dxfversion)
        doc.classes.classes = dict(sorted(doc.classes.classes.items()))
        doc.saveas(str(path))
    finally:
        ezdxf.options.write_fixed_meta_data_for_testing = fixed
    return str(path)


def _segments(case):
    """the drawn linework as segments (mm) by layer, door blocks exploded (leaf + swing polyline), arcs and bulges
    flattened on a whole-degree grid."""
    segs = []
    for kind, data, att in ops(case):
        L = att.get("layer")
        if kind == "LINE":
            segs.append((L, [data[0], data[1]]))
        elif kind == "PLINE":
            pts = data[0] + ([data[0][0]] if data[1] else [])
            segs.append((L, pts))
        elif kind == "ARC":
            segs.append((L, _arc_pts(*data)))
        elif kind == "BPLINE":
            segs.append((L, _bulge_pts(data[0], data[1])))
        elif kind == "INSERT":
            hx, hy = data[1]
            sx, sy, r = att.get("xscale", 1.0), att.get("yscale", 1.0), math.radians(att.get("rotation", 0.0))

            def W(u, v):
                u, v = u * sx, v * sy
                return (hx + u * math.cos(r) - v * math.sin(r), hy + u * math.sin(r) + v * math.cos(r))
            segs.append((L, [W(0, 0), W(1000, 0)]))
            segs.append((L, [W(1000 * math.cos(math.radians(a)), 1000 * math.sin(math.radians(a)))
                             for a in range(0, 91, 5)]))
    return segs


def _extent(case, pad=600.0):
    pts = [p for _, s in _segments(case) for p in s]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


WALL_PEN_MM = 35.0                                            # a 0.35 mm pen at 1:100
THIN_PEN_MM = 18.0                                            # 0.18 mm: door leaves and swings, glazing


def raster(case, path, mm_per_px=10.0, scan=False, seed=7):
    """a PNG of the plan (10 mm / px is about 250 dpi at 1:100; 25 mm / px about 100 dpi); returns the pixel <-> mm
    transform {x0, y1, mm_per_px} (pixel (0, 0) at (x0, y1)) and the face-line pen width."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    x0, y0, x1, y1 = _extent(case)
    W, H = int(math.ceil((x1 - x0) / mm_per_px)), int(math.ceil((y1 - y0) / mm_per_px))
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    P = lambda p: ((p[0] - x0) / mm_per_px, (y1 - p[1]) / mm_per_px)      # noqa: E731
    for L, s in _segments(case):
        if L == "A-TEXT":
            continue
        pen = WALL_PEN_MM if L in ("A-WALL", "A-COL") else THIN_PEN_MM
        d.line([P(p) for p in s], fill=0, width=max(1, int(round(pen / mm_per_px))))
    for kind, data, att in ops(case):
        if kind == "TEXT" and att.get("height", 0) >= 200:
            font = ImageFont.load_default(size=max(6, int(round(att["height"] / mm_per_px))))
            d.text(P(data[1]), data[0], fill=0, font=font, anchor="ls")
    meta = {"x0": x0, "y1": y1, "mm_per_px": mm_per_px, "w": W, "h": H, "scan": scan, "face_pen_mm": WALL_PEN_MM}
    if scan:
        img = img.rotate(0.4, resample=Image.BILINEAR, fillcolor=255, center=(W / 2, H / 2))
        img = img.filter(ImageFilter.GaussianBlur(0.8))
        a = np.asarray(img).astype(float)
        a += np.random.default_rng(seed).normal(0, 18, a.shape)
        img = Image.fromarray(np.clip(a, 0, 255).astype("uint8"))
        meta["skew_deg"] = 0.4
    img.save(str(path))
    return meta


def vector_pdf(case, path):
    """a one-page PDF at 1:100 whose walls, glazing and doors are vector strokes; returns {x0, y0, scale}."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x0, y0, x1, y1 = _extent(case)
    wmm, hmm = (x1 - x0) / PDF_SCALE, (y1 - y0) / PDF_SCALE
    fig = plt.figure(figsize=(wmm / 25.4, hmm / 25.4))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.axis("off")
    for L, s in _segments(case):
        if L == "A-TEXT":
            continue
        ax.plot([p[0] for p in s], [p[1] for p in s], color="black", linewidth=0.2, solid_capstyle="butt")
    for kind, data, att in ops(case):
        if kind == "TEXT" and att.get("height", 0) >= 200:
            ax.text(data[1][0], data[1][1], data[0], fontsize=4)
    fig.savefig(str(path), format="pdf", metadata={"CreationDate": None, "Creator": None, "Producer": None})
    plt.close(fig)
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "scale": PDF_SCALE}
