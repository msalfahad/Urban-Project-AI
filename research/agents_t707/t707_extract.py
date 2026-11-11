"""T-707 own read of the structural DXF (private copy; Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf').
Writes values only (handles, panel sizes in m, thickness values, adjacency, counts): no coordinate, no drawing content.

    python3 -I research/agents_t707/t707_extract.py <ST dxf> --write

What it reads on the SECOND FLOOR ROOF SLAB plan (outline 397 W / 39A E / 392 S / 38D N, as T-669 / T-689):
  - the beam bands drawn on layer '1' inside the outline (edge pairs 0.20 apart) -> the slab panels between them;
  - every TEXT inside the outline on S-TEXT-SLAB: thickness pairs 'T' + value, '(T&B)' marks, level marks;
  - the linetype of every entity inside (a step / hidden line would be dashed) and any INSERT (section mark);
  - the level marks printed elsewhere on the same drawing (the designer's convention for a level change);
  - the general note 7D (S-NOTE) and the column outlines (T-689 handles) -> which panels each column touches.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import ezdxf

OUT = Path(__file__).resolve().parent / "out" / "T707_OWN_READ.json"
COLS = {"40F": "C2 2F (tank)", "412": "C2 2F", "415": "C5 2F", "418": "C9 2F", "41B": "C2 2F", "41E": "C2 2F",
        "421": "C1 2F", "424": "C3 2F (tank)", "778": "PC-2F"}
TOL = 1.0  # mm


def main(path, write):
    raw = Path(path).read_bytes()
    doc = ezdxf.readfile(path)
    msp, db = doc.modelspace(), doc.entitydb
    x0, x1 = db.get("397").dxf.start[0], db.get("39A").dxf.start[0]
    y0, y1 = db.get("392").dxf.start[1], db.get("38D").dxf.start[1]
    W, H = x1 - x0, y1 - y0
    inside = lambda x, y: -TOL <= x - x0 <= W + TOL and -TOL <= y - y0 <= H + TOL

    # beam edge lines (layer '1') inside the outline
    hs, vs = [], []
    for e in msp.query('LINE[layer=="1"]'):
        (ax, ay, *_), (bx, by, *_) = e.dxf.start, e.dxf.end
        if not (inside(ax, ay) and inside(bx, by)):
            continue
        if abs(ay - by) < TOL:
            hs.append((round(ay - y0), round(min(ax, bx) - x0), round(max(ax, bx) - x0)))
        elif abs(ax - bx) < TOL:
            vs.append((round(ax - x0), round(min(ay, by) - y0), round(max(ay, by) - y0)))
    # panels: clear rectangles between the bands, read off the band edges (mm, local, NOT committed)
    xb = sorted({v[0] for v in vs})            # 0, 200, 2700, 2900, 4700, 4900, 7900, 8100
    xcl = [(xb[i], xb[i + 1]) for i in range(1, len(xb) - 2, 2)]  # clear x strips between band pairs
    panels = []
    for (pa, pb) in xcl:
        # horizontal edges spanning this strip
        ys = sorted({h[0] for h in hs if h[1] <= pa + 60 and h[2] >= pb - 60} | {0, round(H)})
        ys = [y for y in ys]
        # bands are pairs 200 apart; clear spans are between consecutive band pairs
        bands, i = [], 0
        while i < len(ys):
            if i + 1 < len(ys) and ys[i + 1] - ys[i] <= 200 + TOL:
                bands.append((ys[i], ys[i + 1])); i += 2
            else:
                bands.append((ys[i], ys[i])); i += 1
        for j in range(len(bands) - 1):
            panels.append({"x": (pa, pb), "y": (bands[j][1], bands[j + 1][0])})
    texts = []
    for t in msp.query("TEXT MTEXT"):
        x, y = t.dxf.insert[0], t.dxf.insert[1]
        if not inside(x, y):
            continue
        s = (t.dxf.text if t.dxftype() == "TEXT" else t.plain_text()).strip()
        texts.append((t.dxf.handle, t.dxf.layer, s, x - x0, y - y0))
    for i, p in enumerate(sorted(panels, key=lambda p: (-p["y"][0], p["x"][0])), 1):
        p["id"] = f"P{i}"
    inp = lambda p, x, y: p["x"][0] <= x <= p["x"][1] and p["y"][0] <= y <= p["y"][1]
    for p in panels:
        own = [t for t in texts if inp(p, t[3], t[4])]
        p["thickness_texts"] = []
        for h, lay, s, x, y in own:
            if s == "T":
                v = [t for t in own if t[2].isdigit() and abs(t[3] - x) < 400 and 0 < y - t[4] < 500]
                p["thickness_texts"].append({"T": h, "value": v[0][0], "cm": int(v[0][2])} if v else {"T": h})
        p["t_and_b_marks"] = [h for h, lay, s, x, y in own if s == "(T&B)"]
        p["size_m"] = [round((p["x"][1] - p["x"][0]) / 1000, 3), round((p["y"][1] - p["y"][0]) / 1000, 3)]
    # columns -> panels touched (a panel corner or edge on the column outline, 1 band width = 200 mm)
    cols = {}
    for h, name in COLS.items():
        e = db.get(h)
        pts = [(a - x0, b - y0) for a, b, *_ in e.get_points()]
        cx0, cx1 = min(p[0] for p in pts), max(p[0] for p in pts)
        cy0, cy1 = min(p[1] for p in pts), max(p[1] for p in pts)
        touch = [p["id"] for p in panels
                 if p["x"][0] - 200 - TOL <= cx1 and cx0 <= p["x"][1] + 200 + TOL
                 and p["y"][0] - 200 - TOL <= cy1 and cy0 <= p["y"][1] + 200 + TOL]
        cols[h] = {"member": name, "section_drawn_m": [round((cx1 - cx0) / 1000, 3), round((cy1 - cy0) / 1000, 3)],
                   "panels_touched": sorted(touch, key=lambda s: int(s[1:]))}
    # B8 (label 79E, band 38D / 38E, clear span 412 east face -> 415 west face): the panels on its south side
    def _bx(h):
        q = [a - x0 for a, b, *_ in db.get(h).get_points()]
        return min(q), max(q)
    b8a, b8b = _bx("412")[1], _bx("415")[0]
    y38e = db.get("38E").dxf.start[1] - y0
    b8_panels = sorted((p["id"] for p in panels if abs(p["y"][1] - y38e) <= TOL
                        and p["x"][0] < b8b and p["x"][1] > b8a), key=lambda s: int(s[1:]))
    # plane evidence inside the outline
    lts, inserts, levels_inside, n_inside = set(), 0, [], 0
    for e in msp:
        try:
            t = e.dxftype()
            if t == "LINE":
                pts = [e.dxf.start, e.dxf.end]
            elif t == "LWPOLYLINE":
                pts = [(a, b) for a, b, *_ in e.get_points()]
            elif t in ("ARC", "CIRCLE"):
                pts = [e.dxf.center]
            elif t in ("TEXT", "MTEXT", "INSERT"):
                pts = [e.dxf.insert]
            elif t == "HATCH":
                pts = [v for p in e.paths for v in getattr(p, "vertices", [])] or None
            else:
                continue
        except Exception:
            continue
        if not pts or not all(inside(p[0], p[1]) for p in pts):
            continue
        n_inside += 1
        if e.dxftype() == "INSERT":
            inserts += 1
        lt = e.dxf.get("linetype", "BYLAYER")
        if lt.upper() == "BYLAYER":
            lt = doc.layers.get(e.dxf.layer).dxf.linetype
        lts.add(lt.upper())
    for h, lay, s, x, y in texts:
        if lay == "LEVEL" or s.startswith(("+", "%%p", "-0", "-1")):
            levels_inside.append(h)
    levels_sheet = sorted({t.dxf.text.strip() for t in msp.query('TEXT[layer=="LEVEL"]')})
    lv_970 = [t.dxf.handle for t in msp.query('TEXT[layer=="LEVEL"]') if t.dxf.text.strip() == "+9.70"]
    note = db.get("7D")
    res = {
        "schema": "T707_OWN_READ_V1",
        "source": {"file": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'", "bytes": len(raw),
                   "sha256": hashlib.sha256(raw).hexdigest()},
        "sfrs_outline_m": [round(W / 1000, 3), round(H / 1000, 3)],
        "beam_edge_lines_inside": len(hs) + len(vs),
        "panels": [{k: p[k] for k in ("id", "size_m", "thickness_texts", "t_and_b_marks")}
                   for p in sorted(panels, key=lambda p: int(p["id"][1:]))],
        "columns": cols,
        "b8_south_panels": b8_panels,
        "plane_evidence": {"entities_checked_inside": n_inside, "linetypes_inside": sorted(lts),
                           "inserts_inside": inserts,
                           "level_texts_inside": levels_inside, "level_values_printed_on_the_drawing": levels_sheet,
                           "level_970_marks_beside_the_outline": lv_970,
                           "water_tank_label": "1A85" if db.get("1A85") is not None else None},
        "general_note": {"handle": "7D", "layer": note.dxf.layer, "contains_16": "16" in note.dxf.text,
                         "reading": "T-044 r2 decoded: all slabs cast 16 cm unless stated otherwise (ST p.8 note 18)"},
    }
    if write:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps(res, indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1], "--write" in sys.argv)
