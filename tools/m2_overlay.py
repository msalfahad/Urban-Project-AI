"""M2 OVERLAYS - source-derived visual QA: what the generic engine found, drawn on the drawing's own geometry.

Every shape is a detected object at its source coordinates (no redrawing, no schematic): beam bands coloured by
binding state, slab faces by class and thickness basis, footings by state, column outlines, and the coverage-risk
markers (unenclosed band sides, widened snaps). Labels are engine marks only (B12, F3, C2 ...), never source texts,
so no client name or free text from the drawing is reproduced.

    sheet_svgs(D)  {sheet_id: svg}        html(D, banner)  one page per detected sheet, printable to PDF
"""

from __future__ import annotations

import html as H
import re

SAFE = re.compile(r"^[A-Z]{1,4}\d{0,3}[A-Z]?$")
STATE_COLOUR = {
    "BOUND": "#1b7f4c", "BOUND_WIDTH_CONFLICT": "#b7791f", "BOUND_ARC_CHAIN": "#1b7f4c",
    "INHERITED_ALONG_LINE": "#2b6cb0", "UNBOUND": "#c53030", "MULTIPLE_MARKS": "#c05621",
    "AMBIGUOUS": "#c05621",
}
FACE_FILL = {"PRINTED_IN_PANEL": "#81c7b8", "SHEET_UNIFORM": "#b2dfd6", "CONVENTION_DEFAULT": "#f6d58e",
             "NO_THICKNESS": "#f4a259", "CONFLICTING_TAGS": "#f4a259"}
FOOT = {"CONFIRMED": "#1b7f4c", "TYPE_BY_SIZE_MATCH": "#2b6cb0", "SIZE_MISMATCH": "#b7791f",
        "COMBINED_OUTLINE": "#b7791f", "NESTED_OR_DUPLICATE": "#718096", "TYPE_NOT_IN_SCHEDULE": "#c53030"}
LEGEND = [("#1b7f4c", "beam band bound to a schedule mark / footing confirmed"),
          ("#2b6cb0", "section inherited along the line / footing typed by size"),
          ("#b7791f", "width or size conflict, resolved by a named convention"),
          ("#c53030", "unbound band / type not in schedule (unresolved)"),
          ("#81c7b8", "slab panel, thickness printed in the panel"),
          ("#b2dfd6", "slab panel, sheet-uniform thickness (provisional)"),
          ("#f4a259", "slab panel without thickness evidence (coverage risk)"),
          ("#cbd5e0", "opening (deducted)"),
          ("#e53e3e", "open boundary face / unenclosed band side (coverage risk)"),
          ("#d53f8c", "face end extended by a widened snap (coverage risk)")]


def _safe(t):
    t = str(t or "")
    return t if SAFE.match(t) else ""


def _pts(poly, tf):
    return " ".join(f"{tf(x, y)[0]:.1f},{tf(x, y)[1]:.1f}" for x, y in poly)


def _box_poly(b):
    return [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]


def sheet_svg(rec, width=1000):
    sh = rec["sheet"]
    pts = [p for b in rec.get("beams", []) for p in b["polygon"]]
    pts += [p for f in (rec.get("slab") or {}).get("faces", []) if f["class"] != "DETAIL" for p in f["polygon"]]
    pts += [p for f in rec.get("footings", []) if f.get("box") for p in _box_poly(f["box"])]
    if pts:                                   # the view is the detected content (with a margin), not the whole frame
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        m = 0.04 * max(max(xs) - min(xs), max(ys) - min(ys), 1e-9)
        x0, y0, x1, y1 = min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m
    else:
        x0, y0, x1, y1 = sh["box"]
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        return None
    k = width / w
    hh = h * k

    def tf(x, y):
        return ((x - x0) * k, (y1 - y) * k)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {hh:.0f}" width="100%" '
           f'role="img" aria-label="{H.escape(sh["sheet_id"])} {H.escape(sh["role"])}">',
           f'<rect x="0" y="0" width="{width:.0f}" height="{hh:.0f}" fill="#ffffff" stroke="#a0aec0"/>']
    slab = rec.get("slab") or {}
    for f in slab.get("faces", []):
        if f["class"] == "PANEL":
            fill = FACE_FILL.get(f.get("t_basis"), "#f4a259")
            stroke = "#e53e3e" if f.get("open_boundary") else "#4a5568"
        elif f["class"] == "OPENING":
            fill, stroke = "#cbd5e0", "#718096"
        elif f["class"] == "OPEN_BOUNDARY":
            fill, stroke = "#fed7d7", "#e53e3e"
        else:
            continue
        out.append(f'<polygon points="{_pts(f["polygon"], tf)}" fill="{fill}" fill-opacity="0.75" '
                   f'stroke="{stroke}" stroke-width="0.6"/>')
    for c in rec.get("column_boxes", []):
        out.append(f'<polygon points="{_pts(_box_poly(c), tf)}" fill="#2d3748" stroke="none"/>')
    for b in rec.get("beams", []):
        col = STATE_COLOUR.get(b.get("state"), "#c53030")
        if b.get("binding") == "INHERITED_ALONG_LINE" or str(b.get("state", "")).startswith("INHERIT"):
            col = STATE_COLOUR["INHERITED_ALONG_LINE"]
        out.append(f'<polygon points="{_pts(b["polygon"], tf)}" fill="{col}" fill-opacity="0.55" stroke="{col}" '
                   f'stroke-width="0.8"><title>{H.escape(str(b.get("band_id")))} {H.escape(_safe(b.get("mark")))} '
                   f'{H.escape(str(b.get("state")))}</title></polygon>')
        lab = _safe(b.get("mark"))
        if lab and b.get("polygon"):
            cx = sum(p[0] for p in b["polygon"]) / len(b["polygon"])
            cy = sum(p[1] for p in b["polygon"]) / len(b["polygon"])
            X, Y = tf(cx, cy)
            out.append(f'<text x="{X:.1f}" y="{Y:.1f}" font-size="10" font-family="Arial" fill="#1a202c" '
                       f'text-anchor="middle">{H.escape(lab)}</text>')
    for f in rec.get("footings", []):
        if not f.get("box"):
            continue
        col = FOOT.get(f["state"], "#c53030")
        out.append(f'<polygon points="{_pts(_box_poly(f["box"]), tf)}" fill="{col}" fill-opacity="0.25" '
                   f'stroke="{col}" stroke-width="1.2"><title>{H.escape(_safe(f.get("mark")))} '
                   f'{H.escape(f["state"])}</title></polygon>')
        lab = _safe(f.get("mark"))
        if lab:
            X, Y = tf((f["box"][0] + f["box"][2]) / 2, (f["box"][1] + f["box"][3]) / 2)
            out.append(f'<text x="{X:.1f}" y="{Y:.1f}" font-size="11" font-family="Arial" fill="#1a202c" '
                       f'text-anchor="middle">{H.escape(lab)}</text>')
    for x in slab.get("unenclosed_sides", []):
        X, Y = tf(*x["side_mid"])
        out.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="4" fill="#e53e3e"/>')
    for hrec in (rec.get("heal") or {}).get("extended_wide", []):
        if hrec.get("at"):
            X, Y = tf(*hrec["at"])
            out.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="2.5" fill="#d53f8c"/>')
    out.append("</svg>")
    return "\n".join(out)


def sheet_svgs(D):
    out = {}
    for sid, rec in D["sheets"].items():
        if not (rec.get("beams") or rec.get("footings") or (rec.get("slab") or {}).get("faces")):
            continue
        svg = sheet_svg(rec)
        if svg:
            out[f"{sid}_{rec['sheet']['role']}_{rec['sheet']['storey']}"] = svg
    return out


def _counts(rec):
    from collections import Counter
    c = {}
    if rec.get("beams"):
        c["bands"] = dict(Counter(b["state"] for b in rec["beams"]))
    if rec.get("footings"):
        c["footings"] = dict(Counter(f["state"] for f in rec["footings"]))
    if rec.get("slab"):
        c["faces"] = dict(rec["slab"].get("counts", {}))
        c["unenclosed_sides"] = len(rec["slab"].get("unenclosed_sides", []))
    if rec.get("heal"):
        c["heal"] = {"merged": rec["heal"]["merged"], "extended": rec["heal"]["extended"],
                     "extended_wide": len(rec["heal"]["extended_wide"])}
    return c


def html(D, banner=""):
    svgs = sheet_svgs(D)
    leg = "".join(f'<li><span class="sw" style="background:{c}"></span>{H.escape(t)}</li>' for c, t in LEGEND)
    pages = []
    for name, svg in svgs.items():
        sid = name.split("_")[0]
        rec = D["sheets"][sid]
        pages.append(f'<section><h2>{H.escape(name)}</h2><p class="m">{H.escape(str(_counts(rec)))}</p>{svg}'
                     f'</section>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Visual QA overlays</title>
<style>
:root{{--ink:#1a202c;--muted:#4a5568;--bg:#ffffff}}
body{{font-family:Arial,sans-serif;color:var(--ink);background:var(--bg);margin:16px}}
h1{{font-size:18px}} h2{{font-size:14px;margin:8px 0 2px}} .m{{font-size:9px;color:var(--muted);margin:0 0 4px}}
.b{{background:#fff5f5;border:1px solid #feb2b2;padding:6px;font-size:10px}}
ul{{list-style:none;padding:0;columns:2;font-size:10px}} li{{margin:2px 0}}
.sw{{display:inline-block;width:12px;height:10px;margin-right:6px;vertical-align:middle;border:1px solid #718096}}
section{{page-break-after:always;break-after:page}}
svg{{max-width:100%;height:auto}}
</style></head><body>
<h1>Visual QA - generic engine detections on the source geometry</h1>
<p class="b">{H.escape(banner)}</p>
<p class="m">Shapes are the detected objects at their source coordinates. Labels are engine marks only. A red dot is a
band side whose slab cell did not close; a pink dot is a face end the engine extended by a widened snap.</p>
<ul>{leg}</ul>
{''.join(pages)}
</body></html>"""
