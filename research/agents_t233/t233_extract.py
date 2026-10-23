"""T-233 extract: footing outlines, tags, schedule rows and blinding plans of the FOUNDATION PLAN frame of a structural
DXF, written as a VALUES-ONLY json (sizes, areas, counts, entity handles; no coordinates, no names).

    python3 -I research/agents_t233/t233_extract.py "<ST7757 dxf.dxf>" --out <scratch>/ALSENAN_FOOTING_INPUT.json

Sources (Alsenan, Drive "Alsenan chalet project", "ST7757 dxf.dxf" sha 9f9d1179): FOUNDATION PLAN frame (title block
FP); outlines = unit-square block "F" inserts scaled to size (layer S-DIM), LWPOLYLINEs on S-FOOTINGS (closed or open
where a strap enters), four-LINE squares on S-FOOTINGS; tags = S-TEXT texts ending in a footing type and the C/F,
C11/F11 tag blocks, each tag bound to ONE outline (inside it, else the nearest within 1.0 m); schedule = the FT / FTB
schedule inserts' attributes (L = attribute 'W', W = 'H', H = 'DEPHT', cm). The ground-beam plan frame draws the neck
footings again on S-FOOTINGS: those squares lie outside the foundation frame and are excluded (one element, one sheet).
Plot line = S-BOUN closed polyline 1658 (outer face of the 0.20 m band, T-065 E1 / E2).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import ezdxf
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

PROJ_M = 0.10      # ST7757.pdf p.13 'TYP. DETAIL OF ISOLATED FOOTING.': '10 | L x W | 10', '10cm Plain con.'


def _layer(e):
    try:
        return e.dxf.layer
    except Exception:
        return "?"


def _hid(src):
    """Entity handle of an outline source string."""
    parts = src.split()
    if parts[0] == "INSERT":
        return parts[2]
    return parts[1].split("+")[0]


def _frame(msp, title="FOUNDATION PLAN"):
    """Foundation frame window: the S-FOOTINGS / S-BOUN entities around the plot polyline whose frame title is FP."""
    plot = next(e for e in msp.query("LWPOLYLINE") if e.dxf.handle == "1658")
    pts = [(x, y) for x, y, *_ in plot.get_points()]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    pad = 3000.0
    return (min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad), Polygon(pts)


def extract(path):
    raw = Path(path).read_bytes()
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    (x0, x1, y0, y1), plot = _frame(msp)
    inside = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1  # noqa: E731
    fts = []
    for e in msp.query("INSERT"):
        if e.dxf.name == "F" and inside(e.dxf.insert.x, e.dxf.insert.y):
            p = e.dxf.insert
            sx, sy = abs(e.dxf.xscale), abs(e.dxf.yscale)          # mirrored inserts normalised
            if abs(e.dxf.rotation % 90) > 1e-6:
                raise ValueError("rotated footing insert: not handled")
            if abs(e.dxf.rotation % 180 - 90) < 1e-6:
                sx, sy = sy, sx
            fts.append(("INSERT F " + e.dxf.handle, box(p.x - 500 * sx, p.y - 500 * sy, p.x + 500 * sx, p.y + 500 * sy)))
    for e in msp.query("LWPOLYLINE"):
        if _layer(e) == "S-FOOTINGS":
            pts = [(x, y) for x, y, *_ in e.get_points()]
            if inside(*pts[0]):
                fts.append(("LWPOLYLINE %s %s" % (e.dxf.handle, "closed" if e.closed else "open"), Polygon(pts)))
    lines = [e for e in msp.query("LINE") if _layer(e) == "S-FOOTINGS" and inside(e.dxf.start.x, e.dxf.start.y)]
    used = set()
    for a in lines:
        if a.dxf.handle in used:
            continue
        chain, cur = [a], a.dxf.end
        for _ in range(3):
            nxt = [b for b in lines if b not in chain and (b.dxf.start - cur).magnitude < 1]
            if not nxt:
                break
            chain.append(nxt[0])
            cur = nxt[0].dxf.end
        if len(chain) == 4 and (cur - a.dxf.start).magnitude < 1:
            used.update(c.dxf.handle for c in chain)
            fts.append(("4xLINE " + "+".join(c.dxf.handle for c in chain),
                        Polygon([(c.dxf.start.x, c.dxf.start.y) for c in chain])))
    # schedule
    sched = {}
    for e in msp.query("INSERT"):
        if e.dxf.name in ("FT", "FTB"):
            at = {a.dxf.tag: a.dxf.text for a in e.attribs}
            sched[at["FO-TY"]] = dict(L=float(at["W"]) / 100, W=float(at["H"]) / 100, H=float(at["DEPHT"]) / 100,
                                      insert=e.dxf.handle)
    # tags
    tags = []
    for e in msp:
        t = e.dxftype()
        if t == "TEXT" and _layer(e) == "S-TEXT":
            s, p = e.dxf.text.strip(), e.dxf.insert
        elif t == "INSERT" and e.dxf.name in ("CF", "F11"):
            s, p = {"CF": "C/F", "F11": "C11/F11"}[e.dxf.name], e.dxf.insert
        else:
            continue
        if not inside(p.x, p.y):
            continue
        lab = s.split("/")[-1].strip()
        if lab in ("F", "FF", "FN") or (lab.startswith("F") and lab[1:].isdigit()):
            tags.append((lab, Point(p.x, p.y), e.dxf.handle))
    bound = {i: [] for i in range(len(fts))}
    unbound = []
    for lab, pt, h in tags:
        ins = [i for i, (_, g) in enumerate(fts) if g.contains(pt)]
        if len(ins) == 1:
            bound[ins[0]].append(lab)
            continue
        # outside every outline: the nearest outline within 1.0 m whose drawn size agrees with the tag's schedule
        # row (either orientation); a tie between two such outlines leaves the tag unbound (never guessed)
        row = sched.get(lab)

        def fits(g):
            if row is None:
                return False
            x0_, y0_, x1_, y1_ = g.bounds
            a_, b_ = (x1_ - x0_) / 1000.0, (y1_ - y0_) / 1000.0
            return ((abs(a_ - row["L"]) < 0.005 and abs(b_ - row["W"]) < 0.005)
                    or (abs(a_ - row["W"]) < 0.005 and abs(b_ - row["L"]) < 0.005))
        d = sorted((g.distance(pt), i) for i, (_, g) in enumerate(fts) if fits(g) and g.distance(pt) <= 1000.0)
        if d and (len(d) == 1 or d[1][0] > d[0][0] + 100.0):
            bound[d[0][1]].append(lab)
        else:
            unbound.append((lab, h))
    # clips: an outline whose area is below its bounding box with another outline's area in the missing piece
    out = []
    grown = []
    for i, (src, g) in enumerate(fts):
        mrr = g.minimum_rotated_rectangle
        c = list(mrr.exterior.coords)
        e1 = Point(c[0]).distance(Point(c[1])) / 1000.0
        e2 = Point(c[1]).distance(Point(c[2])) / 1000.0
        missing = mrr.difference(g)
        clip = []
        if missing.area > 1.0:
            clip = [_hid(fts[j][0]) for j in range(len(fts)) if j != i and fts[j][1].intersection(missing).area > 0.5 * missing.area]
        gb = g.buffer(PROJ_M * 1000.0, join_style=2)
        grown.append(gb)
        out.append(dict(id=_hid(src), source=src, tags=bound[i], a=round(e1, 4), b=round(e2, 4),
                        area=round(g.area / 1e6, 6), clipped_by=clip,
                        blind_m2=round(gb.area / 1e6, 6), blind_outside_m2=round(gb.difference(plot).area / 1e6, 6)))
    held_ids = {o["id"] for o in out if len(set(o["tags"])) != 1}
    meas = [grown[i] for i, o in enumerate(out) if o["id"] not in held_ids]
    return dict(
        schema="URBAN_T233_FOOTING_INPUT_V1",
        source=dict(file="Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'", sha256=hashlib.sha256(raw).hexdigest(),
                    frame="FOUNDATION PLAN", projection_m=PROJ_M, projection_source="ST7757.pdf p.13 typical isolated "
                    "footing details: '10 | L x W | 10', '10cm Plain con.'", thickness_m=0.10,
                    underlay="5 cm screed + 2 cm membrane (T-206 vector read): other trades, not concrete"),
        schedule=sched, outlines=out, unbound_tags=unbound,
        blinding_union_measured_m2=round(unary_union(meas).area / 1e6, 6),
        blinding_sum_measured_m2=round(sum(g.area for g in meas) / 1e6, 6),
        blinding_union_all_m2=round(unary_union(grown).area / 1e6, 6),
        band_area_m2=None,
    )


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    res = extract(a.dxf)
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(len(res["outlines"]), "outlines;", "unbound tags", res["unbound_tags"])


if __name__ == "__main__":
    main()
