"""T-669 own drawing read (private input; prints only derived geometry in m, relative to a local origin).

Usage (from the checkout root, on the decoded private copy only):
    .work/venv/bin/python -I research/agents_t669/t669_extract.py .work/private/<ST dxf>

Reads 'ST7757 dxf.dxf' (Drive 'Alsenan chalet project', read-only, decoded into .work/private) and prints, as JSON:
  (a) F-T665-1 annex SE corner of the GROUND BEAMS PLAN: the four edge lines of run #1 (10B / 7D1) and run #2
      (F8 / 7D4), every S-COL.BON outline within 11 m of the corner, every entity touching the 0.30 x 0.30 corner
      square, in a local frame (origin = the outer corner, x along run #2 away from the corner, y along run #1);
  (b) the SECOND FLOOR ROOF SLAB plan: the 2F column outlines (40F / 412 / 415 / 418 / 41B / 41E / 421 / 424) relative
      to column 40F's south-west corner, every S-TEXT-SLAB / LEVEL text inside the plan's layer-1 outline, and the
      LEVEL texts outside it.
Nothing is written. The committed READS in t669_alsenan.py are these printed values (m), checked by the Checker.
"""
from __future__ import annotations

import json
import sys

import ezdxf
from ezdxf import bbox

U = 0.001


def main(path):
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    by = {e.dxf.handle: e for e in msp}

    def seg(h):
        e = by[h]
        return (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)

    def pts(h):
        return [(p[0], p[1]) for p in by[h].get_points()]

    # (a) origin = outer corner = east end of F8 = south end of 10B
    (a0, a1) = seg("F8")
    ox, oy = max(a0[0], a1[0]), a0[1]
    loc = lambda x, y: (round((ox - x) * U, 4), round((y - oy) * U, 4))  # noqa: E731
    a = {"origin": "outer corner of the annex SE ground-beam L (F8 east end = 10B south end)", "edges": {},
         "columns_within_11m": {}, "touching_square": []}
    for h in ("10B", "7D1", "F8", "7D4"):
        p, q = seg(h)
        a["edges"][h] = [loc(*p), loc(*q)]
    for e in msp:
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "S-COL.BON":
            ps = [loc(x, y) for x, y in pts(e.dxf.handle)]
            xs, ys = [p[0] for p in ps], [p[1] for p in ps]
            if min(xs) < 11 and max(xs) > -1 and min(ys) < 11 and max(ys) > -1:
                a["columns_within_11m"][e.dxf.handle] = [min(xs), min(ys), max(xs), max(ys)]
    for e in msp:
        try:
            b = bbox.extents([e])
        except Exception:  # noqa: BLE001
            continue
        if not b.has_data:
            continue
        x0, y0 = loc(b.extmax.x, b.extmin.y)
        x1, y1 = loc(b.extmin.x, b.extmax.y)
        if x0 <= 0.3 and x1 >= 0 and y0 <= 0.3 and y1 >= 0 and (x1 - x0) < 20 and (y1 - y0) < 20:
            a["touching_square"].append([e.dxf.handle, e.dxftype(), e.dxf.layer, [x0, y0, x1, y1]])

    # (b) 2F roof slab plan, relative to column 40F's south-west corner
    c0 = pts("40F")
    bx, by_ = min(p[0] for p in c0), min(p[1] for p in c0)
    rel = lambda x, y: (round((x - bx) * U, 3), round((y - by_) * U, 3))  # noqa: E731
    cols = {}
    for h in ("40F", "412", "415", "418", "41B", "41E", "421", "424"):
        ps = [rel(*p) for p in pts(h)]
        xs, ys = [p[0] for p in ps], [p[1] for p in ps]
        cols[h] = [min(xs), min(ys), max(xs), max(ys), round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3)]
    ext = [1e9, 1e9, -1e9, -1e9]
    for e in msp:
        if e.dxftype() == "LINE" and e.dxf.layer == "1":
            for v in (e.dxf.start, e.dxf.end):
                x, y = rel(v.x, v.y)
                if -6 <= x <= 16 and -11 <= y <= 12:
                    ext = [min(ext[0], x), min(ext[1], y), max(ext[2], x), max(ext[3], y)]
    inside, outside_levels = [], []
    for e in msp:
        if e.dxftype() in ("TEXT", "MTEXT") and e.dxf.layer in ("S-TEXT-SLAB", "LEVEL"):
            x, y = rel(e.dxf.insert.x, e.dxf.insert.y)
            if not (-6 <= x <= 16 and -11 <= y <= 12):
                continue
            s = e.dxf.text if e.dxftype() == "TEXT" else e.text
            row = [e.dxf.handle, e.dxf.layer, s, x, y]
            if ext[0] <= x <= ext[2] and ext[1] <= y <= ext[3]:
                inside.append(row)
            elif e.dxf.layer == "LEVEL":
                outside_levels.append(row)
    b = {"origin": "column 40F south-west corner", "columns": cols, "plan_outline_layer1": ext,
         "texts_inside": inside, "level_texts_outside": outside_levels}
    print(json.dumps({"a_corner": a, "b_2f_roof": b}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
