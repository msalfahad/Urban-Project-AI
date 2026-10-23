"""T-206: reproducible registration of the structural 'Sunken slab.' panels against the sanitary sheets.

Reads the two PRIVATE PDFs from a folder outside the repository (Drive "Alsenan chalet project": ST7757.pdf and
sanitary-7757.pdf, decoded into .work/private) and writes only numbers: panel and fixture-group extents in PLOT metres
(origin at the plot frame's top-left corner as drawn, u along the 31.37 m side, v along the 15.00 m side).

Method (vector, no raster): (1) the plot frame is the one path of each plan sheet whose box has the plot's 31.37 / 15.00
ratio (ST p.4 / p.5 and sanitary sheets 2 / 3: 2.0914 / 2.0916); each sheet is mapped to plot metres by that box
(1:100 on ST, a reduced plot on the sanitary set). (2) Sunken panels: groups of 45-degree hatch lines whose spacing is
the legend's 'Sunken slab.' spacing (about 7.1 pt; the cantilever hatch is about 2.8 pt). (3) Wet fixtures: the
sanitary sheets draw fixtures in blue (0, 0, 1) and floor drains / rain-water items in orange (1, 0.75, 0); blue paths
are grouped (gap 0.4 m). (4) Each panel lists the fixture groups that overlap it; each fixture group lists whether a
sunken panel covers it. Nothing here is a quantity.

    python3 -I research/agents_t206/t206_sunken_registration.py <private folder> [--write]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLOT_U, PLOT_V = 31.37, 15.00
SHEETS = {"1F": {"st_page": 4, "san_page": 2}, "2F": {"st_page": 5, "san_page": 3}}
SUNKEN_GAP_PT = (6.6, 7.6)
GROUP_GAP_M = 0.4


def _frame(page, fitz):
    m = page.rotation_matrix
    best = None
    for x in page.get_drawings():
        r = x["rect"].transform(m)
        if r.height > 100 and abs(r.width / r.height - PLOT_U / PLOT_V) < 0.002 and r.width > 400:
            if best is None or r.width > best.width:
                best = r
    if best is None:      # frame drawn as separate lines: two equal horizontal lines at the plot ratio apart
        hs = []
        for x in page.get_drawings():
            for it in x["items"]:
                if it[0] == "l":
                    a, b = it[1] * m, it[2] * m
                    if abs(a.y - b.y) < 0.3 and abs(a.x - b.x) > 400:
                        hs.append((round(min(a.x, b.x), 1), round(max(a.x, b.x), 1), a.y))
        for x0, x1, y0 in hs:
            for u0, u1, y1 in hs:
                h = y1 - y0
                if (u0, u1) == (x0, x1) and h > 100 and abs((x1 - x0) / h - PLOT_U / PLOT_V) < 0.002:
                    best = fitz.Rect(x0, y0, x1, y1)
    if best is None:
        raise ValueError(f"page {page.number + 1}: no plot frame with the 31.37 / 15.00 ratio")
    return best


def _to_plot(r, frame):
    return (round((r.x0 - frame.x0) / frame.width * PLOT_U, 2), round((r.y0 - frame.y0) / frame.height * PLOT_V, 2),
            round((r.x1 - frame.x0) / frame.width * PLOT_U, 2), round((r.y1 - frame.y0) / frame.height * PLOT_V, 2))


def _group(rects, gap):
    groups = []
    for r in rects:
        hit = [g for g in groups if g[0] - gap <= r[2] and r[0] <= g[2] + gap and g[1] - gap <= r[3] and r[1] <= g[3] + gap]
        g = [r[0], r[1], r[2], r[3], 1]
        for h in hit:
            g = [min(g[0], h[0]), min(g[1], h[1]), max(g[2], h[2]), max(g[3], h[3]), g[4] + h[4]]
            groups.remove(h)
        groups.append(g)
    return groups


def sunken_panels(page, fitz):
    m, frame = page.rotation_matrix, _frame(page, fitz)
    segs = []
    for x in page.get_drawings():
        for it in x["items"]:
            if it[0] != "l":
                continue
            a, b = it[1] * m, it[2] * m
            if math.hypot(b.x - a.x, b.y - a.y) < 3:
                continue
            ang = math.degrees(math.atan2(-(b.y - a.y), b.x - a.x)) % 180
            if 43 < ang < 47:
                segs.append(fitz.Rect(a, b).normalize())
    groups = []
    for s in segs:
        hit = [g for g in groups if fitz.Rect(g["r"].x0 - 4, g["r"].y0 - 4, g["r"].x1 + 4, g["r"].y1 + 4).intersects(s)]
        if hit:
            g = hit[0]
            g["r"] |= s
            g["s"].append(s)
            for h in hit[1:]:
                g["r"] |= h["r"]
                g["s"] += h["s"]
                groups.remove(h)
        else:
            groups.append({"r": fitz.Rect(s), "s": [s]})
    out = []
    for g in groups:
        cs = sorted({round(((s.x0 + s.x1) / 2 + (s.y0 + s.y1) / 2) / math.sqrt(2), 1) for s in g["s"]})
        gaps = sorted(round(b - a, 1) for a, b in zip(cs, cs[1:]) if b - a > 0.5)
        if len(g["s"]) < 4 or not gaps:
            continue
        sunk = sum(1 for x in gaps if SUNKEN_GAP_PT[0] <= x <= SUNKEN_GAP_PT[1])
        inside = fitz.Rect(frame).intersects(g["r"])
        if inside and sunk >= 3:         # a mixed group (a column hatch beside the panel) still carries its 7.1 pt run
            out.append({"extent_m": _to_plot(g["r"], frame), "hatch_lines": len(g["s"]),
                        "median_gap_pt": gaps[len(gaps) // 2]})
    return sorted(out, key=lambda p: (p["extent_m"][1], p["extent_m"][0]))


def fixture_groups(page, fitz):
    m, frame = page.rotation_matrix, _frame(page, fitz)
    blue, drains = [], []
    for x in page.get_drawings():
        col = tuple(round(v, 2) for v in (x.get("color") or ()))
        r = x["rect"].transform(m)
        if not fitz.Rect(frame).contains(r):
            continue
        e = _to_plot(r, frame)
        if col == (0.0, 0.0, 1.0):
            blue.append(e)
        elif col == (1.0, 0.75, 0.0) and x.get("fill") and max(r.width, r.height) < 12:
            drains.append(e)
    groups = _group(blue, GROUP_GAP_M)
    rows = []
    for g in groups:
        n_fd = sum(1 for d in drains if g[0] - 0.6 <= d[0] <= g[2] + 0.6 and g[1] - 0.6 <= d[1] <= g[3] + 0.6)
        rows.append({"extent_m": [round(v, 2) for v in g[:4]], "fixture_paths": g[4], "filled_orange_nearby": n_fd})
    return sorted(rows, key=lambda r: (r["extent_m"][1], r["extent_m"][0]))


def _overlap(a, b, tol=0.3):
    return a[0] - tol <= b[2] and b[0] - tol <= a[2] and a[1] - tol <= b[3] and b[1] - tol <= a[3]


def register(private):
    import pymupdf as fitz  # private-data reader only; the module tests never import it
    st = fitz.open(str(Path(private) / "ST7757.pdf"))
    san = fitz.open(str(Path(private) / "sanitary-7757.pdf"))
    out = {}
    for storey, pg in SHEETS.items():
        panels = sunken_panels(st[pg["st_page"] - 1], fitz)
        fixtures = [f for f in fixture_groups(san[pg["san_page"] - 1], fitz) if f["fixture_paths"] >= 3]
        for p in panels:
            p["fixture_groups_overlapping"] = [i for i, f in enumerate(fixtures) if _overlap(p["extent_m"], f["extent_m"])]
        for i, f in enumerate(fixtures):
            f["under_sunken_panel"] = any(i in p["fixture_groups_overlapping"] for p in panels)
        out[storey] = {"st_page": pg["st_page"], "sanitary_sheet": pg["san_page"], "sunken_panels": panels,
                       "fixture_groups": fixtures}
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    res = register(sys.argv[1])
    text = json.dumps(res, indent=1)
    if "--write" in sys.argv:
        (HERE / "SUNKEN_REGISTRATION.json").write_text(text + "\n", encoding="utf-8")
    print(text)
