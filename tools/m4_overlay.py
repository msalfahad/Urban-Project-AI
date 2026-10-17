"""M4 OVERLAYS - visual QA of the M4 rules on the drawing's own geometry (engine ids and marks only; no source text).

    exceptions_svg(rec, rows, extra)   one sheet: every unresolved concrete item numbered at its location (the
                                       number is the NO column of UNRESOLVED_CONCRETE_EXCEPTIONS)
    cb_svg(rec)                        continuous-beam lines: pieces by span-matching state, span numbers, the pieces
                                       that took their section through the printed span sequence
    gb_exterior_svg(rec, arch, items)  ground beams by architectural class and exterior case
    slab_svg(rec)                      slab panels by thickness basis; panels whose member overlap was deducted
    blinding_svg(D, overlap)           footing blinding (footing + projection) and the beam strips on it
    lintel_svg(rec, openings, reg)     architectural openings on the slab plan above them, by lintel outcome
    stair_svg(rec)                     stair zones with their drawn tread lines
    html(sections, banner)             one printable page per section
"""

from __future__ import annotations

import html as H
import re

SAFE = re.compile(r"^[A-Z]{1,4}\d{0,3}[A-Z]?$")
GREY, INK = "#cbd5e0", "#1a202c"
CB_STATE = {"MATCH_FORWARD": "#1b7f4c", "MATCH_REVERSED": "#2b6cb0", "MATCH_SYMMETRIC": "#319795",
            "AMBIGUOUS_DIRECTION": "#b7791f", "AMBIGUOUS_SPANS": "#c05621", "SPAN_COUNT_CONFLICT": "#c53030",
            "SPAN_LENGTH_CONFLICT": "#c53030", "NO_PRINTED_SPANS": "#718096"}
GB_CLASS = {"EXTERIOR_WALL": "#2b6cb0", "INTERIOR_WALL": "#718096", "PERIMETER_NO_WALL": "#c05621",
            "NOT_PERIMETER": GREY, "NOT_REGISTERED": "#e53e3e"}
GB_CASE = {"GB_EXTERIOR_DEPTH": "#2b6cb0", "GB_EXTERIOR_LEVEL_CONFLICT": "#d69e2e",
           "GB_EXTERIOR_NOT_EVIDENCED": "#e53e3e"}
T_BASIS = {"PRINTED_IN_PANEL": "#81c7b8", "PROJECT_DEFAULT": "#9ae6b4", "SHEET_UNIFORM": "#b2dfd6",
           "CONVENTION_DEFAULT": "#f6d58e", "NO_THICKNESS": "#f4a259", "CONFLICTING_TAGS": "#f4a259"}
LINTEL = {"PROVISIONAL": "#1b7f4c", "UNRESOLVED": "#d69e2e", "REPORTED": "#c53030"}


def _box(b):
    return [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]


class _View:
    def __init__(self, pts, width=1000):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        m = 0.04 * max(max(xs) - min(xs), max(ys) - min(ys), 1e-9)
        self.x0, self.y0, self.x1, self.y1 = min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m
        self.k = width / (self.x1 - self.x0)
        self.w, self.h = width, (self.y1 - self.y0) * self.k
        self.out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w:.0f} {self.h:.0f}" width="100%">',
                    f'<rect x="0" y="0" width="{self.w:.0f}" height="{self.h:.0f}" fill="#ffffff" stroke="#a0aec0"/>']

    def tf(self, x, y):
        return (x - self.x0) * self.k, (self.y1 - y) * self.k

    def poly(self, pts, fill, stroke="none", op=0.6, sw=0.6, title=""):
        p = " ".join("%.1f,%.1f" % self.tf(x, y) for x, y in pts)
        t = f"<title>{H.escape(title)}</title>" if title else ""
        self.out.append(f'<polygon points="{p}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" '
                        f'stroke-width="{sw}">{t}</polygon>')

    def line(self, a, b, col, sw=0.8):
        (x0, y0), (x1, y1) = self.tf(*a), self.tf(*b)
        self.out.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{col}" '
                        f'stroke-width="{sw}"/>')

    def text(self, x, y, s, size=10, col=INK, bold=False):
        X, Y = self.tf(x, y)
        w = ' font-weight="bold"' if bold else ""
        self.out.append(f'<text x="{X:.1f}" y="{Y:.1f}" font-size="{size}" font-family="Arial" fill="{col}"{w} '
                        f'text-anchor="middle" dominant-baseline="middle">{H.escape(s)}</text>')

    def badge(self, x, y, s, col="#c53030"):
        X, Y = self.tf(x, y)
        self.out.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="8" fill="#ffffff" stroke="{col}" stroke-width="1.6"/>')
        self.out.append(f'<text x="{X:.1f}" y="{Y + 0.5:.1f}" font-size="8" font-family="Arial" fill="{col}" '
                        f'font-weight="bold" text-anchor="middle" dominant-baseline="middle">{H.escape(s)}</text>')

    def svg(self):
        return "\n".join(self.out + ["</svg>"])


def _pts(rec, extra=()):
    pts = [p for b in rec.get("beams", []) for p in b["polygon"]]
    pts += [p for f in (rec.get("slab") or {}).get("faces", []) if f["class"] != "DETAIL" for p in f["polygon"]]
    pts += [p for f in rec.get("footings", []) if f.get("box") for p in _box(f["box"])]
    return pts + list(extra)


def _base(v, rec):
    for f in (rec.get("slab") or {}).get("faces", []):
        if f["class"] == "PANEL":
            v.poly(f["polygon"], "#f7fafc", "#e2e8f0", 1.0, 0.4)
    for c in rec.get("column_boxes", []):
        v.poly(_box(c), "#4a5568", op=0.9)
    for b in rec.get("beams", []):
        v.poly(b["polygon"], GREY, op=0.8)
    for f in rec.get("footings", []):
        if f.get("box"):
            v.poly(_box(f["box"]), "none", "#a0aec0", 1.0, 0.8)


def _centre(poly):
    return sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly)


def exceptions_svg(rec, rows, polys):
    """rows: UNRESOLVED_CONCRETE_EXCEPTIONS rows of this sheet; polys: component id -> polygon (drawing units)."""
    pts = _pts(rec, [p for r in rows for p in polys.get(r["COMPONENT_ID"], [])])
    if not pts:
        return None
    v = _View(pts)
    _base(v, rec)
    for r in rows:
        poly = polys.get(r["COMPONENT_ID"]) or []
        if len(poly) >= 3:
            v.poly(poly, "#feb2b2", "#c53030", 0.8, 1.2, r["NO"])
    for r in rows:
        poly = polys.get(r["COMPONENT_ID"]) or []
        if poly:
            x, y = _centre(poly)
            v.badge(x, y, r["NO"].split("-")[-1], "#c53030" if r["CLASS"] != "NEED_UNRESOLVED" else "#b7791f")
    return v.svg()


def cb_svg(rec):
    lines = rec.get("cb_lines") or []
    if not lines:
        return None
    v = _View(_pts(rec))
    _base(v, rec)
    poly = {b["band_id"]: b["polygon"] for b in rec.get("beams", [])}
    for ln in lines:
        col = CB_STATE.get(ln["state"], "#c53030")
        inh = set(ln.get("inherited") or [])
        for pid in ln["pieces"]:
            if pid in poly:
                v.poly(poly[pid], "#2b6cb0" if pid in inh else col, col, 0.75, 1.0,
                       f"{ln['mark']} {ln['state']}" + (" inherited by span sequence" if pid in inh else ""))
        for s in ln["spans"]:
            ps = [poly[p] for p in s["pieces"] if p in poly]
            if ps:
                x, y = _centre([q for p in ps for q in p])
                v.text(x, y, f"{ln['mark'] if SAFE.match(ln['mark']) else ''}.{s['index']}", 8, INK, True)
        if not ln["spans"] and ln["pieces"] and ln["pieces"][0] in poly:
            x, y = _centre(poly[ln["pieces"][0]])
            v.text(x, y, (ln["mark"] if SAFE.match(ln["mark"]) else "") + " ?", 8, "#c53030", True)
    return v.svg()


def gb_exterior_svg(rec, arch, items):
    bands = (arch or {}).get("bands") or {}
    case = {i["component_id"].split(":")[-1]: i["blocker"] for i in items
            if i["trade"] == "CONCRETE" and i["family"] == "GROUND_BEAMS" and i["storey"] == rec["sheet"]["storey"]}
    v = _View(_pts(rec))
    _base(v, rec)
    for b in rec.get("beams", []):
        a = bands.get(b["band_id"], {})
        cls = a.get("class", "NOT_REGISTERED")
        col = GB_CASE.get(case.get(b["band_id"]), GB_CLASS.get(cls, GREY))
        v.poly(b["polygon"], col, col, 0.8, 0.8, f"{b['band_id']} {cls} {case.get(b['band_id'], '')}")
        if a.get("floor_level_m") is not None and "OUTSIDE" in rec.get("band_sides", {}).get(b["band_id"], []):
            x, y = _centre(b["polygon"])
            v.text(x, y, f"+{a['floor_level_m']:.2f}", 7)
    return v.svg()


def slab_svg(rec):
    faces = (rec.get("slab") or {}).get("faces", [])
    if not faces:
        return None
    v = _View(_pts(rec))
    for f in faces:
        if f["class"] != "PANEL":
            continue
        col = T_BASIS.get(f.get("t_basis"), "#f4a259")
        stroke = "#d53f8c" if f.get("member_overlap_m2") else "#4a5568"
        v.poly(f["polygon"], col, stroke, 0.85, 1.2 if f.get("member_overlap_m2") else 0.4,
               f"{f['face_id']} t {f.get('t_m')} {f.get('t_basis')}")
        if f.get("t_m") and f["area_m2"] > 2.0:
            x, y = _centre(f["polygon"])
            v.text(x, y, f"{f['t_m'] * 100:.0f}", 8)
    for c in rec.get("column_boxes", []):
        v.poly(_box(c), "#4a5568", op=0.9)
    for b in rec.get("beams", []):
        v.poly(b["polygon"], GREY, op=0.8)
    return v.svg()


def blinding_svg(D, p_m):
    """footing blinding (footing + p) on the foundation plan with the ground-beam strips registered onto it."""
    fp = next((r for r in D["sheets"].values() if r["sheet"]["role"] == "FOUNDATION_PLAN"), None)
    ov = D.get("blinding_overlap") or {}
    if fp is None:
        return None
    u = D["unit_m"]
    pn = p_m / u
    boxes = [f["box"] for f in fp.get("footings", []) if f.get("box")]
    shift = ov.get("shift") or {}
    strips = []
    for sid, rec in D["sheets"].items():
        if sid not in shift:
            continue
        dx, dy = shift[sid]
        bands = rec.get("bands", []) if rec["sheet"]["role"] == "GROUND_BEAM_PLAN" else \
            (rec.get("straps") or {}).get("bands", [])
        for b in bands:
            if b.get("kind", "STRAIGHT") != "STRAIGHT" or not b.get("u"):
                continue
            uu, nn = b["u"], (-b["u"][1], b["u"][0])
            strips.append([(uu[0] * t + nn[0] * o + dx, uu[1] * t + nn[1] * o + dy)
                           for t, o in ((b["t0"], b["lo_off"] - pn), (b["t1"], b["lo_off"] - pn),
                                        (b["t1"], b["hi_off"] + pn), (b["t0"], b["hi_off"] + pn))])
    pts = [p for b in boxes for p in _box(b)] + [p for s in strips for p in s]
    if not pts:
        return None
    v = _View(pts)
    for s in strips:
        v.poly(s, "#bee3f8", "#2b6cb0", 0.6, 0.5)
    for b in boxes:
        v.poly(_box((b[0] - pn, b[1] - pn, b[2] + pn, b[3] + pn)), "#fbd38d", "#c05621", 0.55, 0.8)
        v.poly(_box(b), "none", "#7b341e", 1.0, 0.6)
    return v.svg()


def lintel_svg(rec, openings, reg, items, storey):
    if not openings or (reg or {}).get("state") != "REGISTERED":
        return None
    cat = {i["component_id"]: i["category"] for i in items if i["family"] == "LINTELS" and i["trade"] == "CONCRETE"}
    pts = []
    marks = []
    for op in openings:
        u, n = op["u"], op["n"]
        q = [(u[0] * s + n[0] * o + reg["dx"], u[1] * s + n[1] * o + reg["dy"])
             for s, o in ((op["s0"], op["o0"]), (op["s1"], op["o0"]), (op["s1"], op["o1"]), (op["s0"], op["o1"]))]
        pts += q
        marks.append((op, q, cat.get(f"LINTELS:{storey}:{op['opening_id']}", "REPORTED")))
    v = _View(_pts(rec, pts))
    _base(v, rec)
    for op, q, c in marks:
        v.poly(q, LINTEL[c], LINTEL[c], 0.9, 2.0, f"{op['opening_id']} {op['width_m']:.2f} m {op.get('beam_over')}")
        x, y = _centre(q)
        v.text(x, y, op["opening_id"].split("-")[-1].lstrip("0"), 7, INK, True)
    return v.svg()


def stair_svg(rec):
    faces = [f for f in (rec.get("slab") or {}).get("faces", []) if f.get("region") == "STAIR_ZONE"]
    if not faces:
        return None
    pts = [p for f in faces for p in f["polygon"]]
    v = _View(pts, width=700)
    for f in faces:
        v.poly(f["polygon"], "#e9d8fd", "#6b46c1", 0.7, 1.0, f["face_id"])
        for a, b in (f.get("treads") or {}).get("lines", []):
            v.line(a, b, "#553c9a", 1.0)
    return v.svg()


def html(sections, banner=""):
    body = []
    for title, note, svgs in sections:
        figs = "".join(f"<figure>{s}<figcaption>{H.escape(c)}</figcaption></figure>" for c, s in svgs if s)
        body.append(f"<section><h2>{H.escape(title)}</h2><p class='m'>{note}</p>{figs or '<p>(none)</p>'}</section>")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>M4 visual QA</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{{--ink:#1a202c;--muted:#4a5568;--bg:#ffffff}}
body{{font-family:Arial,sans-serif;color:var(--ink);background:var(--bg);margin:16px}}
h1{{font-size:18px}} h2{{font-size:15px;margin:10px 0 4px}} .m{{font-size:10px;color:var(--muted);margin:0 0 6px}}
.b{{background:#fff5f5;border:1px solid #feb2b2;padding:6px;font-size:10px}}
figure{{margin:0 0 10px}} figcaption{{font-size:10px;color:var(--muted)}} svg{{max-width:100%;height:auto}}
table{{border-collapse:collapse;font-size:10px}} td,th{{border:1px solid #cbd5e0;padding:2px 5px}}
img{{max-width:240px;border:1px solid #cbd5e0}}
section{{break-after:page}}
</style></head><body>
<h1>M4 visual QA - source-evidence rules on the drawing geometry</h1>
<p class="b">{H.escape(banner)}</p>
{''.join(body)}
</body></html>"""
