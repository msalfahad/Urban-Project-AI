"""T-426 own drawing read (values, DXF handles and lengths in m only; no coordinate, no drawing text is committed).

    .work/venv/bin/python -I research/agents_t426/t426_extract.py "<.work/private>/ST7757.dxf"           # check
    .work/venv/bin/python -I research/agents_t426/t426_extract.py "<.work/private>/ST7757.dxf" --write   # rebuild

1. SECTION-MARK CENSUS of the GROUND BEAMS PLAN frame (p.3, T-141 frame): every TEXT / MTEXT in model space inside the
   frame and every text inside the blocks inserted there, classified: column / neck mark ('C<n>', 'CN', 'C<n>/F<n>',
   'CN/FN', 'C'), footing / strap mark ('F<n>', 'S.B<n>'), level ('+-0.00' style), slab tag ('T=..cm', bar callout),
   title, other. A SECTION MARK is any text that names a beam size ('<b>x<h>', '<b>X<h>'), a beam type ('G.B', 'GB<n>',
   'TB<n>', 'B<n>') or a section cut ('SECTION', 'SEC'). Result: count per class and the number of section marks.
2. SUPPORT READ for the bands the census needs at a support / class limit (F-1, the 5 m reading): for each named band,
   every S-COL.BON outline of the GBP / FP / CAP frames within 0.60 m of the band strip: its handle, whether the band
   centreline cuts it, its along-band extent (from the band's start) and its clear gap to the nearer band face; and the
   layer-1 bands of the other direction whose strip touches the band (the beams that land on it or cross it) with
   their along-band position. The band faces are the T-416 handles.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "ALSENAN_T426_READ.json"
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
GBP = (78929.89653886131, 29036.09943562183, 114124.2067251332, 57066.43175431111)   # T-141 / T-416 frame
FP_X0 = 117654.3026476346
PITCH = FP_X0 - GBP[0]
FRAMES = {"GBP": 0, "FP": +1, "CAP": +2}
BANDS = {"7DC+7DD": ("7DC", "7DD"), "7E7+7E8": ("7E7", "7E8"), "177+7CD": ("177", "7CD"), "184+7CF": ("184", "7CF"),
         "7E1+7E2": ("7E1", "7E2")}
NEAR_MM = 600.0

SECTION_RE = re.compile(r"(\d+\s*[xX]\s*\d+)|(\bG\.?\s?B\b)|(\bGB\s*\d)|(\bTB\s*\d)|(^B\s*\d+$)|(SECTION)|(\bSEC\b)",
                        re.I)
CLASSES = [
    ("column_or_neck_mark", re.compile(r"^(C\d*|CN)(/F\w*)?$|^CN/FN$", re.I)),
    ("footing_or_strap_mark", re.compile(r"^(F\d+|FF|FN|S\.?B\d*)$", re.I)),
    ("level", re.compile(r"^(%%p|\+|-)\d+\.\d+$", re.I)),
    ("slab_tag_or_bar_callout", re.compile(r"(T=\d+\s*cm)|(%%c\d+)|(\d+\s*%%c)", re.I)),
    ("title_or_scale", re.compile(r"(PLAN)|(^\(1:\d+\)$)", re.I)),
    ("load_tag", re.compile(r"^\(L\.L\)$", re.I)),
]


def _inside(x, y, k=0):
    x0 = GBP[0] + FRAMES[k] * PITCH if isinstance(k, str) else GBP[0]
    return x0 <= x <= x0 + (GBP[2] - GBP[0]) and GBP[1] <= y <= GBP[3]


def _classify(t):
    t = t.strip()
    if SECTION_RE.search(t):
        return "SECTION_MARK"
    for name, rx in CLASSES:
        if rx.search(t):
            return name
    return "other"


def census(doc):
    msp = doc.modelspace()
    counts, n = {}, 0
    for e in msp:
        typ = e.dxftype()
        if typ in ("TEXT", "MTEXT"):
            p = e.dxf.insert
            if not _inside(p.x, p.y):
                continue
            t = e.dxf.text if typ == "TEXT" else e.plain_text()
            c = _classify(t)
            counts[c] = counts.get(c, 0) + 1
            n += 1
        elif typ == "INSERT":
            p = e.dxf.insert
            if not _inside(p.x, p.y):
                continue
            blk = doc.blocks.get(e.dxf.name)
            texts = [x.dxf.text if x.dxftype() == "TEXT" else x.plain_text()
                     for x in (blk.query("TEXT MTEXT") if blk is not None else [])]
            texts += [a.dxf.text for a in e.attribs]
            for t in texts:
                c = _classify(t)
                counts["in_block:" + c] = counts.get("in_block:" + c, 0) + 1
                n += 1
    marks = sum(v for k, v in counts.items() if k.endswith("SECTION_MARK"))
    return {"texts_read": n, "by_class": dict(sorted(counts.items())), "section_marks": marks}


def supports(doc):
    from shapely.affinity import translate
    from shapely.geometry import LineString, Polygon

    msp = doc.modelspace()
    ents = doc.entitydb
    lines = []
    for e in msp.query('LINE[layer=="1"]'):
        s, t = e.dxf.start, e.dxf.end
        if _inside((s.x + t.x) / 2, (s.y + t.y) / 2) and s.distance(t) > 50:
            lines.append((e.dxf.handle, (s.x, s.y), (t.x, t.y)))
    cols = []
    for e in msp.query('LWPOLYLINE[layer=="S-COL.BON"]'):
        if not e.closed:
            continue
        p = Polygon([tuple(v)[:2] for v in e.get_points("xy")]).buffer(0)
        c = p.centroid
        for k, m in FRAMES.items():
            if _inside(c.x - m * PITCH, c.y):
                cols.append((k, e.dxf.handle, translate(p, xoff=-m * PITCH)))
    out = {}
    for bid, (h1, h2) in BANDS.items():
        a1, b1 = ents[h1].dxf.start, ents[h1].dxf.end
        a2, b2 = ents[h2].dxf.start, ents[h2].dxf.end
        L1 = math.dist((a1.x, a1.y), (b1.x, b1.y))
        u = ((b1.x - a1.x) / L1, (b1.y - a1.y) / L1)
        if u[0] < -1e-9 or (abs(u[0]) < 1e-9 and u[1] < 0):
            u = (-u[0], -u[1])
        n = (-u[1], u[0])

        def along(x, y):
            return x * u[0] + y * u[1]

        def across(x, y):
            return x * n[0] + y * n[1]
        o1, o2 = across(a1.x, a1.y), across(a2.x, a2.y)
        lo_o, hi_o = min(o1, o2), max(o1, o2)
        s_lo = max(min(along(a1.x, a1.y), along(b1.x, b1.y)), min(along(a2.x, a2.y), along(b2.x, b2.y)))
        s_hi = min(max(along(a1.x, a1.y), along(b1.x, b1.y)), max(along(a2.x, a2.y), along(b2.x, b2.y)))
        oc = (lo_o + hi_o) / 2
        cl = LineString([(s_lo * u[0] + oc * n[0], s_lo * u[1] + oc * n[1]),
                         (s_hi * u[0] + oc * n[0], s_hi * u[1] + oc * n[1])])
        strip = cl.buffer((hi_o - lo_o) / 2, cap_style=2)
        rows = []
        for k, h, p in cols:
            if p.distance(strip) > NEAR_MM:
                continue
            xs = [along(x, y) - s_lo for x, y in p.exterior.coords]
            os_ = [across(x, y) for x, y in p.exterior.coords]
            gap = 0.0 if (max(os_) >= lo_o and min(os_) <= hi_o) else min(abs(min(os_) - hi_o), abs(lo_o - max(os_)))
            rows.append({"frame": k, "handle": h, "cut_by_centreline": bool(cl.intersects(p)),
                         "along_from_m": round(min(xs) / 1e3, 4) + 0.0, "along_to_m": round(max(xs) / 1e3, 4) + 0.0,
                         "gap_to_band_face_m": round(gap / 1e3, 4) + 0.0})
        meets = []
        for h, a, b in lines:
            if h in (h1, h2):
                continue
            L = math.dist(a, b)
            w = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            if abs(w[0] * u[0] + w[1] * u[1]) > 0.02:       # perpendicular lines only
                continue
            seg = LineString([a, b])
            if seg.distance(strip) > 5.0:
                continue
            meets.append({"handle": h, "along_m": round((along(*a) - s_lo) / 1e3, 4) + 0.0})
        out[bid] = {"faces": [h1, h2], "drawn_m": round((s_hi - s_lo) / 1e3, 4) + 0.0,
                    "width_m": round((hi_o - lo_o) / 1e3, 4) + 0.0,
                    "columns_near": sorted(rows, key=lambda r: (r["along_from_m"], r["frame"])),
                    "perpendicular_face_lines_touching": sorted(meets, key=lambda r: (r["along_m"], r["handle"]))}
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    dxf = argv[0]
    if hashlib.sha256(Path(dxf).read_bytes()).hexdigest() != DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    import ezdxf
    doc = ezdxf.readfile(dxf)
    res = {"schema": "T426_GB_READ_V1", "structural_sha256": DXF_SHA,
           "frame": "T-141 GROUND BEAMS PLAN (p.3); FP / CAP one / two sheet pitches east (T-416)",
           "gbp_text_census": census(doc), "bands": supports(doc)}
    txt = json.dumps(res, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        OUT.write_text(txt, encoding="utf-8")
        print("written", OUT.name)
    else:
        same = OUT.exists() and OUT.read_text(encoding="utf-8") == txt
        print("REPRODUCED" if same else "DIFFERS")
        if not same:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
