"""T-694 own read of the private ST DXF copy (Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf', decoded only into
.work/private): the three 'P.C' member texts, their leaders and the column outlines within 3 m, and the size texts /
dimensions within 0.60 m of the outlines named in the D-66 register gap. Writes values only, every position RELATIVE
to its own text or outline (no drawing coordinate is committed).

    python3 -I research/agents_t694/t694_extract.py <private dxf> [--write]
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

import ezdxf

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "T694_OWN_READ.json"
PC_TEXTS = ("544", "548", "77C")
GAP_OUTLINES = ("34A", "34D", "356", "350", "415", "77B", "778")
SIZE_RE = re.compile(r"\d+\s*[xX*]\s*\d+")


def box(e):
    pts = [(p[0], p[1]) for p in e.get_points()]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def dist(p, b):
    return math.hypot(max(b[0] - p[0], 0, p[0] - b[2]), max(b[1] - p[1], 0, p[1] - b[3]))


def text_of(e):
    return e.dxf.text if e.dxftype() == "TEXT" else e.plain_text()


def main(argv):
    src = Path(argv[0])
    doc = ezdxf.readfile(src)
    msp = doc.modelspace()
    cols = {e.dxf.handle: box(e) for e in msp.query("LWPOLYLINE") if e.dxf.layer == "S-COL.BON"}
    lead = [e for e in msp.query("LWPOLYLINE") if e.dxf.layer == "S-TEXT-SLAB"]
    cases = []
    for h in PC_TEXTS:
        t = doc.entitydb.get(h)
        o = (t.dxf.insert.x, t.dxf.insert.y)
        far = None
        lh = None
        for e in lead:
            pts = [(p[0], p[1]) for p in e.get_points()]
            if any(math.hypot(q[0] - o[0], q[1] - o[1]) < 600 for q in pts):
                far = max(pts, key=lambda q: math.hypot(q[0] - o[0], q[1] - o[1]))
                lh = e.dxf.handle
        near = {k: b for k, b in cols.items() if dist(o, b) < 3000 or (far and dist(far, b) < 3000)}
        rel = {k: [round(b[0] - o[0]), round(b[1] - o[1]), round(b[2] - o[0]), round(b[3] - o[1])]
               for k, b in sorted(near.items())}
        cases.append({"handle": h, "text": t.dxf.text, "at": [0, 0], "leader": lh,
                      "leader_far": [round(far[0] - o[0]), round(far[1] - o[1])] if far else None, "outlines": rel})
    texts = list(msp.query("TEXT MTEXT"))
    dims = list(msp.query("DIMENSION"))
    gap = {}
    for h in GAP_OUTLINES:
        b = cols[h]
        near_t = [(t.dxf.handle, text_of(t)[:24], round(dist((t.dxf.insert.x, t.dxf.insert.y), b)))
                  for t in texts if dist((t.dxf.insert.x, t.dxf.insert.y), b) <= 600]
        nd = 0
        for d in dims:
            pts = [p for p in (d.dxf.get("defpoint"), d.dxf.get("defpoint2"), d.dxf.get("defpoint3")) if p is not None]
            if any(dist((p.x, p.y), b) <= 600 for p in pts):
                nd += 1
        gap[h] = {"drawn_mm": [round(b[2] - b[0]), round(b[3] - b[1])], "texts_within_600": near_t,
                  "size_texts_within_600": [x for x in near_t if SIZE_RE.search(x[1])], "dimensions_within_600": nd}
    pc_any = sorted({text_of(t) for t in texts if re.search(r"P\.C|PLANT", text_of(t), re.I)})
    out = {"schema": "URBAN_T694_OWN_READ_V1", "source": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'",
           "sha256": hashlib.sha256(src.read_bytes()).hexdigest(), "bytes": src.stat().st_size,
           "tol_mm": 600, "cases": cases, "gap_outlines": gap, "pc_texts_in_file": pc_any}
    s = json.dumps(out, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        OUT.write_text(s, encoding="utf-8")
    print(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
