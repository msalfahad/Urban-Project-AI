"""T-627 drawing read (research, unwired): the width and height of every opening behind the B12 opening-area rows,
read independently from the architectural drawings (R-T627-1 evidence rules in t627_rules.py).

Sources (Drive "Alsenan chalet project", decoded into .work/private only; nothing of them is committed):
  - P7757_DXF_COMPRESSED.zip (P7757.dxf): the three floor plans (window symbol lines + their masonry jamb lines, door
    blocks + the wall-face lines that end at the masonry jambs) and the SOUTH EAST / NORTH WEST elevations with their
    printed DIMENSION chains;
  - the architectural .dwf (DWF 6 vector plot of the same model space, read with research/agents_t201/w2d_reader.py,
    read only): the SOUTH WEST / NORTH EAST elevations, SECTION A-A and the FENCE ELEVATION, which the DXF lacks.

Output: T627_DRAWN.json (metres, handles of DXF entities, view names; no coordinate, no drawing text).

How a value is read (every villa):
  width  = distance between the two masonry jamb lines (windows: the layer-1 lines that cap the symbol band; doors:
           the ends of the wall-face lines on BOTH faces, which must agree);
  height = a printed DIMENSION segment bound to the opening (its two definition points on the opening's vertical
           chain, the chain's x inside the opening's printed width segment), else the drawn outline in a vector view
           bound to the plan opening: the view's along-facade offset is solved by voting over every window of that
           floor (an opening binds only when its outline's left edge lies within 15 mm of the prediction AND the
           outline width equals the plan jamb width within 20 mm); a door outline that matches only the door block
           (frame) width, not the masonry, is reported as a CANDIDATE, never a binding.
  datum  = the DXF's own +-0.00 chain tick (DIMENSION 100 between +-0.00 and +1.00 on the NW elevation), carried to
           the DWF by the translation that maps the DXF NW jamb lines of the twin arched windows onto the DWF's.
"""
from __future__ import annotations

import collections
import json
import math
import sys
from decimal import Context, Decimal, localcontext
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "agents_t201"))

SCHEMA = "T627_DRAWN/1"

# plan frames (drawing x ranges, mm) and the window symbol line that seeds each opening's group (T-150 register ids)
FLOORS = {"GF": (-162000, -124000), "1F": (-206000, -168000), "2F": (-250000, -212000)}
WINDOW_SYMBOL = {  # id -> (floor, a symbol line handle of its group)
    "W02": ("GF", "262"), "W05": ("GF", "3D9"), "W06": ("GF", "3E6"), "W07": ("GF", "3F3"),
    "W08": ("GF", "3B2"), "W09": ("GF", "3BF"), "W10": ("GF", "3CC"), "W11": ("GF", "342"), "W12": ("GF", "348"),
    "W01": ("GF", "352"),
    "W13": ("1F", "C5A"), "W14": ("1F", "C43"), "W15": ("1F", "BC3"), "W16": ("1F", "C93"), "W18": ("1F", "C36"),
    "W19": ("1F", "CF1"), "W20": ("1F", "CFE"), "W21": ("1F", "CD5"), "W22": ("1F", "CC8"), "W23": ("1F", "CBB"),
    "W24": ("1F", "D0B"), "W25": ("1F", "CE2"),
    "W26": ("2F", "12CF"), "W27": ("2F", "1342"), "W28": ("2F", "1334"), "W29": ("2F", "1327"),
}
DOOR_INSERT = {"D-GF-01": ("GF", "15E"), "D-GF-03": ("GF", "1B5"), "D-GF-05": ("GF", "192"), "D-GF-06": ("GF", "33E"),
               "D-GF-09": ("GF", "3FF"), "D-2F-01": ("2F", "12BA")}

# printed elevation dimensions (DXF handles): id -> {"width": handle, "height": handle, "view": ...}
PRINTED = {
    "W13": {"view": "SOUTH EAST ELEVATION", "width": "2C15", "height": "2A9C"},
    "W26": {"view": "SOUTH EAST ELEVATION", "width": "2C15", "height": "2AB8"},
    "W14": {"view": "SOUTH EAST ELEVATION", "width": "2B9B", "height": "2B47"},
    "W18": {"view": "NORTH WEST ELEVATION", "width": "2D8D", "height": "2EFA"},
    "W17": {"view": "NORTH WEST ELEVATION", "width": "2D53", "height": "2E97"},
}
DXF_DATUM_DIM = "29EE"     # NW elevation chain: 100 from the +-0.00 tick to the +1.00 tick

# DWF views (x range of the plot, mm after the Units transform) and how the plan axis runs along each
VIEWS = {
    "SOUTH WEST ELEVATION": {"x": (-410000, -372000), "axis": "x", "sign": -1},
    "NORTH EAST ELEVATION": {"x": (-475000, -440000), "axis": "x", "sign": 1},
    "SECTION A-A": {"x": (-505000, -476000), "axis": "y", "sign": 1},
    "SECTION B-B": {"x": (-545000, -505000), "axis": "x", "sign": None},
    "FENCE ELEVATION": {"x": (-575000, -540000), "axis": "y", "sign": None},
}
VIEW_Y = (-858000, -834000)
TOL_EDGE, TOL_W = 15.0, 20.0


def shown(dm) -> str | None:
    """the text the DIMENSION displays on the sheet (from its rendered block), digits only, or None."""
    blk = dm.get_geometry_block()
    if blk is None:
        return None
    for t in blk.query("MTEXT TEXT"):
        raw = t.plain_text() if t.dxftype() == "MTEXT" else t.dxf.text
        txt = "".join(ch for ch in raw if ch.isdigit() or ch == ".")
        if txt:
            return txt
    return None


def q3(x) -> str:
    # T-656: the module's only Decimal arithmetic, in its own local 40-digit context (never the caller's precision)
    with localcontext(Context(prec=40)):
        return str(Decimal(repr(float(x))).quantize(Decimal("0.001")))


def _seg(e):
    s, t = e.dxf.start, e.dxf.end
    return (s.x, s.y), (t.x, t.y)


# ---------------------------------------------------------------- plan: windows ---------------------------------------
def window_plan(doc, msp, seed):
    """the symbol group of the seed line and its two masonry jamb lines (layer 1, perpendicular, spanning the band)."""
    e0 = doc.entitydb[seed]
    (sx, sy), (tx, ty) = _seg(e0)
    hor = abs(ty - sy) < 1
    lo, hi = (min(sx, tx), max(sx, tx)) if hor else (min(sy, ty), max(sy, ty))
    c0 = sy if hor else sx
    group = []
    for e in msp.query("LINE[layer=='W']"):
        (ax, ay), (bx, by) = _seg(e)
        if hor and abs(ay - by) < 1 and abs(min(ax, bx) - lo) < 2 and abs(max(ax, bx) - hi) < 2 and abs(ay - c0) < 400:
            group.append((e.dxf.handle, ay))
        if not hor and abs(ax - bx) < 1 and abs(min(ay, by) - lo) < 2 and abs(max(ay, by) - hi) < 2 \
                and abs(ax - c0) < 400:
            group.append((e.dxf.handle, ax))
    cs = [c for _, c in group]
    cmin, cmax = min(cs), max(cs)
    jambs = []
    for e in msp.query("LINE[layer=='1']"):
        (ax, ay), (bx, by) = _seg(e)
        if hor and abs(ax - bx) < 1:
            y0, y1 = sorted((ay, by))
            if y0 <= cmin + 1 and y1 >= cmax - 1 and y1 - y0 < 400 and lo - 400 < ax < hi + 400:
                jambs.append((ax, e.dxf.handle))
        if not hor and abs(ay - by) < 1:
            x0, x1 = sorted((ax, bx))
            if x0 <= cmin + 1 and x1 >= cmax - 1 and x1 - x0 < 400 and lo - 400 < ay < hi + 400:
                jambs.append((ay, e.dxf.handle))
    jambs.sort()
    if len(jambs) != 2:
        raise ValueError(f"window {seed}: {len(jambs)} jamb lines, expected 2")
    (j0, h0), (j1, h1) = jambs
    dims = []                       # printed plan DIMENSIONs whose two definition points sit on the two jambs
    for dm in msp.query("DIMENSION"):
        if not (dm.dxf.hasattr("defpoint2") and dm.dxf.hasattr("defpoint3")):
            continue
        a, b = dm.dxf.defpoint2, dm.dxf.defpoint3
        ka, kb = sorted((a.x, b.x) if hor else (a.y, b.y))
        ca, cb = (a.y, b.y) if hor else (a.x, b.x)
        if abs(ka - j0) <= 10 and abs(kb - j1) <= 10 and abs(ca - c0) < 6000 and abs(cb - c0) < 6000:
            dims.append({"handle": dm.dxf.handle, "measured": q3(dm.get_measurement() / 1000), "shown": shown(dm)})
    return {"printed_width_dims": sorted(dims, key=lambda x: x["handle"]),"symbol_handles": sorted(h for h, _ in group), "jamb_handles": [h0, h1], "width": q3((j1 - j0) / 1000),
            "_axis": "x" if hor else "y", "_iv": (j0, j1), "_c": (cmin + cmax) / 2}


# ---------------------------------------------------------------- plan: doors -----------------------------------------
def door_plan(doc, msp, handle):
    """masonry opening of a door block: the gap between wall-face line ends on each face, both faces must agree."""
    e = doc.entitydb[handle]
    p = e.dxf.insert
    r = e.dxf.rotation % 180
    hor = r < 45 or r > 135
    faces = collections.defaultdict(list)
    for l in msp.query("LINE"):
        if l.dxf.layer != "1":          # wall faces; layer-5 lines inside a doorway are threshold / frame lines
            continue
        (ax, ay), (bx, by) = _seg(l)
        if hor and abs(ay - by) < 1 and abs(ay - p.y) <= 250:
            a, b = sorted((ax - p.x, bx - p.x))
            if b > -2000 and a < 2000:
                faces[round(ay - p.y)].append((a, b, l.dxf.handle))
        if not hor and abs(ax - bx) < 1 and abs(ax - p.x) <= 250:
            a, b = sorted((ay - p.y, by - p.y))
            if b > -2000 and a < 2000:
                faces[round(ax - p.x)].append((a, b, l.dxf.handle))
    # the block's leaf spans 0 .. +-1000 along the wall (sign by rotation / mirror); the gap must overlap it
    gaps = {}
    for off, segs in faces.items():
        segs.sort()
        for (a0, b0, h0), (a1, b1, h1) in zip(segs, segs[1:]):
            g0, g1 = b0, a1
            if 500 < g1 - g0 < 1300 and g0 < 300 and g1 > -300 and (g0 > -1300 and g1 < 1300):
                gaps[off] = (g0, g1, h0, h1)
    if len(gaps) < 2:
        raise ValueError(f"door {handle}: masonry gap found on {len(gaps)} face(s)")
    ws = {q3((g1 - g0) / 1000) for g0, g1, _, _ in gaps.values()}
    if len(ws) != 1:
        raise ValueError(f"door {handle}: faces disagree {sorted(ws)}")
    o = sorted(gaps)
    g0, g1, h0, h1 = gaps[o[0]]
    base = p.x if hor else p.y
    sgn = 1 if (g0 + g1) > 0 else -1
    # D1xx blocks draw a 1.00 m frame from the insert point toward the opening (T-568: 'the D120 block is the frame')
    frame = tuple(sorted((base, base + sgn * 1000))) if e.dxf.name.upper().startswith("D1") else None
    levels = []                     # printed plan LEVEL texts within 3.0 m of the leaf, by side of the wall
    for t in msp.query("TEXT[layer=='LEVEL']"):
        q = t.dxf.insert
        along, across = ((q.x - p.x), (q.y - p.y)) if hor else ((q.y - p.y), (q.x - p.x))
        if abs(along - sgn * 500) <= 3000 and abs(across) <= 3000:
            levels.append({"handle": t.dxf.handle, "level": t.dxf.text.strip(), "side": "+" if across > 0 else "-",
                           "distance": q3(math.hypot(along - sgn * 500, across) / 1000)})
    return {"block": e.dxf.name, "insert_handle": handle, "width": ws.pop(),
            "plan_levels": sorted(levels, key=lambda r: float(r["distance"])),
            "face_handles": sorted({h for v in gaps.values() for h in v[2:]}),
            "faces": len(gaps), "_axis": "x" if hor else "y", "_iv": (base + g0, base + g1), "_frame": frame,
            "_c": p.y if hor else p.x}


# ---------------------------------------------------------------- printed elevation dimensions -------------------------
def printed(doc):
    out = {}
    for oid, d in PRINTED.items():
        w, h = doc.entitydb[d["width"]], doc.entitydb[d["height"]]
        wx = sorted((w.dxf.defpoint2.x, w.dxf.defpoint3.x))
        hx = h.dxf.defpoint2.x
        inside = wx[0] - 5 <= hx <= wx[1] + 5 or wx[0] - 5 <= h.dxf.defpoint3.x <= wx[1] + 5
        out[oid] = {"view": d["view"], "width_dim": d["width"], "height_dim": d["height"],
                    "width_measured": q3(w.get_measurement() / 1000), "height_measured": q3(h.get_measurement() / 1000),
                    "width_shown": shown(w), "height_shown": shown(h),
                    "chain_inside_width_segment": inside}
    dd = doc.entitydb[DXF_DATUM_DIM]
    if round(dd.get_measurement()) != 1000:
        raise ValueError("datum chain is not the 100 cm +-0.00 / +1.00 segment")
    return out, min(dd.dxf.defpoint2.y, dd.dxf.defpoint3.y)


# ---------------------------------------------------------------- DWF ---------------------------------------------------
def _dwf_segments(path):
    import w2d_reader as W
    (name, g), = W.read_dwf_graphics(path)
    tr = g["units"]
    segs = []
    for pl in g["polylines"]:
        P = [W.to_model(p, tr) for p in pl]
        segs.extend(zip(P, P[1:]))
    return segs


def _rects(segs, x0, x1):
    hs, vs = [], []
    for a, b in segs:
        if not (x0 < a[0] < x1 and VIEW_Y[0] < a[1] < VIEW_Y[1]):
            continue
        if abs(a[1] - b[1]) < 3 and abs(a[0] - b[0]) > 250:
            hs.append((min(a[0], b[0]), max(a[0], b[0]), a[1]))
        elif abs(a[0] - b[0]) < 3 and abs(a[1] - b[1]) > 250:
            vs.append((a[0], min(a[1], b[1]), max(a[1], b[1])))
    out = set()
    for xa, ya0, ya1 in vs:
        for xb, yb0, yb1 in vs:
            if not (250 < xb - xa < 7000) or abs(ya0 - yb0) > 6 or abs(ya1 - yb1) > 6:
                continue
            top = any(abs(y - ya1) < 6 and h0 < xa + 6 and h1 > xb - 6 for h0, h1, y in hs)
            bot = any(abs(y - ya0) < 6 and h0 < xa + 6 and h1 > xb - 6 for h0, h1, y in hs)
            if top and bot:
                out.add((round(xa, 1), round(xb - xa, 1), round(ya0, 1), round(ya1, 1)))
    return sorted(out)


def dwf_datum(segs, doc, msp, y0_dxf):
    """DWF +-0.00 = DXF +-0.00 + dy, dy voted from the DXF NW jamb lines (2.10 .. 2.22 m verticals) onto the DWF's."""
    dxf = [(l.dxf.start.x, min(l.dxf.start.y, l.dxf.end.y), abs(l.dxf.start.y - l.dxf.end.y))
           for l in msp.query("LINE") if -390000 < l.dxf.start.x < -340000
           and abs(l.dxf.start.x - l.dxf.end.x) < 1 and 2100 < abs(l.dxf.start.y - l.dxf.end.y) < 2220]
    dwf = [(a[0], min(a[1], b[1]), abs(a[1] - b[1])) for a, b in segs if -440000 < a[0] < -410000
           and abs(a[0] - b[0]) < 2 and 2100 < abs(a[1] - b[1]) < 2220]
    votes = collections.Counter()
    for x, y, L in dxf:
        for X, Y, M in dwf:
            if abs(L - M) < 3:
                votes[(round(X - x), round(Y - y))] += 1
    (dx, dy), n = votes.most_common(1)[0]
    return y0_dxf + dy, n, len(dxf)


def bind_view(view, cfg, rects, plan_items, y0, band):
    """solve the along-facade offset by voting (every plan opening whose masonry width equals an outline width, on
    outlines whose bottom lies in this floor's level band), then bind each plan item; an outline claimed by two
    items binds only the one that shares its wall with another bound opening of the view, else both are AMBIGUOUS."""
    s = cfg["sign"]
    lo, hi = band
    rs = [r for r in rects if lo - 0.01 <= (r[2] - y0) / 1000 < hi - 0.01]
    votes = collections.Counter()
    for it in plan_items:
        if it["_axis"] != cfg["axis"]:
            continue
        j0, j1 = it["_iv"]
        for xa, w, ya0, ya1 in rs:
            if abs(w - (j1 - j0)) <= TOL_W:
                votes[round((xa - (j0 if s == 1 else -j1)) / 5) * 5] += 1
    if not votes:
        return None, {}
    c, n = votes.most_common(1)[0]
    if n < 2:
        return None, {}
    claims = collections.defaultdict(list)
    for it in plan_items:
        if it["_axis"] != cfg["axis"]:
            continue
        for key, iv in (("opening", it["_iv"]), ("frame", it.get("_frame"))):
            if iv is None:
                continue
            j0, j1 = iv
            left = c + (j0 if s == 1 else -j1)
            hits = [r for r in rs if abs(r[0] - left) <= TOL_EDGE and abs(r[1] - (j1 - j0)) <= TOL_W]
            if hits:
                r = max(hits, key=lambda r: r[3] - r[2])
                claims[r].append((it, key))
    walls = collections.Counter(round(it["_c"]) for v in claims.values() if len({x["id"] for x, _ in v}) == 1
                                for it, _ in v[:1])
    out = {}
    for r, v in claims.items():
        ids = {it["id"] for it, _ in v}
        if len(ids) == 1:
            for it, key in v:
                out.setdefault(it["id"], []).append((key, r, "BOUND"))
            continue
        support = {i: walls[round(next(it["_c"] for it, _ in v if it["id"] == i))] for i in ids}
        best = [i for i in ids if support[i] > 0]
        for it, key in v:
            st = "BOUND" if best == [it["id"]] else ("NOT_THIS_WALL" if best else "AMBIGUOUS")
            out.setdefault(it["id"], []).append((key, r, st))
    for i, v in out.items():
        fr = [r for k, r, st in v if k == "frame"]
        for j, (k, r, st) in enumerate(v):
            if k == "opening" and any(f != r and f[0] <= r[0] and f[0] + f[1] >= r[0] + r[1] and f[2] <= r[2]
                                      and f[3] >= r[3] for f in fr):
                v[j] = (k, r, "INNER_OF_FRAME")      # the leaf drawn inside the block's frame, not an opening outline
    return {"offset_votes": n}, out


FLOOR_BAND = {"GF": (-0.5, 5.50), "1F": (5.50, 9.70), "2F": (9.70, 14.50)}   # printed levels +5.50 / +9.70


def read(dxf_path, dwf_path):
    import ezdxf
    doc = ezdxf.readfile(dxf_path)
    if doc.header.get("$INSUNITS") != 4:
        raise ValueError("drawing units are not mm")
    msp = doc.modelspace()
    plan, items = {}, collections.defaultdict(list)
    for oid, (fl, h) in WINDOW_SYMBOL.items():
        w = window_plan(doc, msp, h)
        plan[oid] = {"floor": fl, "kind": "WINDOW", **{k: v for k, v in w.items() if not k.startswith("_")}}
        items[fl].append({"id": oid, "kind": "WINDOW", **w})
    for oid, (fl, h) in DOOR_INSERT.items():
        d = door_plan(doc, msp, h)
        plan[oid] = {"floor": fl, "kind": "DOOR", **{k: v for k, v in d.items() if not k.startswith("_")}}
        items[fl].append({"id": oid, "kind": "DOOR", **d})
    pr, y0_dxf = printed(doc)
    segs = _dwf_segments(dwf_path)
    y0, nd, nx = dwf_datum(segs, doc, msp, y0_dxf)
    views = {}
    for view, cfg in VIEWS.items():
        rects = _rects(segs, *cfg["x"])
        vb = {}
        for fl, its in items.items():
            best = None
            for sg in ((1, -1) if cfg["sign"] is None else (cfg["sign"],)):   # a section's looking direction: voted
                info, b = bind_view(view, dict(cfg, sign=sg), rects, its, y0, FLOOR_BAND[fl])
                if info is not None and (best is None or info["offset_votes"] > best[0]["offset_votes"]):
                    best = (info, b)
            if best is None:
                continue
            info, b = best
            for oid, hits in b.items():
                for key, (xa, w, ya0, ya1), st in hits:
                    vb.setdefault(oid, []).append({
                        "match": key, "status": st, "floor": fl, "offset_votes": info["offset_votes"], "width": q3(w / 1000),
                        "bottom_level": q3((ya0 - y0) / 1000), "head_level": q3((ya1 - y0) / 1000),
                        "height": q3((ya1 - ya0) / 1000)})
        views[view] = {k: sorted(v, key=lambda r: (r["match"], r["head_level"])) for k, v in sorted(vb.items())}
    return {"schema": SCHEMA,
            "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf) + the architectural .dwf",
            "units": "m", "plan": plan, "printed": pr,
            "datum": {"dxf": "NW chain DIMENSION " + DXF_DATUM_DIM + " (100: +-0.00 to +1.00)",
                      "dwf": f"translation voted by {nd} of {nx} DXF NW jamb lines"},
            "views": views}


def dumps(d) -> str:
    return json.dumps(d, indent=1, sort_keys=True, ensure_ascii=True) + "\n"
