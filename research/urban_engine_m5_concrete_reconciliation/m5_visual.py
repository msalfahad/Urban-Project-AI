"""M5 visual QA: ten figures (SVG) and one HTML page printed to PDF.

Every figure says what each mark is: SOURCE GEOMETRY (CAD entities of the M4 model), SOURCE TEXT (a printed value),
CONDITIONAL or UNRESOLVED. Nothing is drawn that the drawings or the registers do not hold; schematic figures say so."""

from __future__ import annotations

import html as H
import math
import subprocess
from pathlib import Path

from shapely.geometry import Polygon

import m5_reconcile as M
import m5_tables as T

INK, MUTED, GRID = "#1a202c", "#4a5568", "#e2e8f0"
C_MEAS, C_COND, C_UNRES, C_EXCL, C_FL, C_GEO, C_TEXT = ("#2b6cb0", "#d69e2e", "#c53030", "#805ad5", "#4a5568",
                                                        "#a0aec0", "#2f855a")
STYLE = f"font-family:Arial,Helvetica,sans-serif;font-size:11px;fill:{INK}"


class Canvas:
    def __init__(self, bounds, width=980, pad=40, title="", subtitle=""):
        x0, y0, x1, y1 = bounds
        self.x0, self.y0 = x0, y0
        self.s = (width - 2 * pad) / max(x1 - x0, 1e-9)
        self.w, self.h = width, (y1 - y0) * self.s + 2 * pad + 60
        self.pad, self.top = pad, 60
        self.y1 = y1
        self.out = [f'<rect x="0" y="0" width="{width}" height="{self.h:.0f}" fill="#ffffff"/>',
                    f'<text x="{pad}" y="24" style="{STYLE};font-size:15px;font-weight:bold">{H.escape(title)}</text>',
                    f'<text x="{pad}" y="42" style="{STYLE};fill:{MUTED}">{H.escape(subtitle)}</text>']

    def tf(self, x, y):
        return self.pad + (x - self.x0) * self.s, self.top + self.pad / 2 + (self.y1 - y) * self.s

    def poly(self, pts, fill, stroke="none", op=0.55, sw=0.6, title="", dash=""):
        d = " ".join(f"{a:.1f},{b:.1f}" for a, b in (self.tf(x, y) for x, y in pts))
        t = f"<title>{H.escape(title)}</title>" if title else ""
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.out.append(f'<polygon points="{d}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" '
                        f'stroke-width="{sw}"{da}>{t}</polygon>')

    def line(self, a, b, col, sw=1.0, dash=""):
        (x1, y1), (x2, y2) = self.tf(*a), self.tf(*b)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" '
                        f'stroke-width="{sw}"{da}/>')

    def text(self, x, y, s, size=9, col=INK, anchor="middle", bold=False):
        X, Y = self.tf(x, y)
        fw = "bold" if bold else "normal"
        self.out.append(f'<text x="{X:.1f}" y="{Y:.1f}" text-anchor="{anchor}" style="{STYLE};font-size:{size}px;'
                        f'fill:{col};font-weight:{fw}">{H.escape(str(s))}</text>')

    def legend(self, items, y=None):
        y = y or self.h - 18
        x = self.pad
        for col, lab, op in items:
            if x + 26 + 6.2 * len(lab) > self.w - 10:
                x, y = self.pad, y + 16
                self.h += 16
            self.out.append(f'<rect x="{x}" y="{y - 9}" width="14" height="10" fill="{col}" fill-opacity="{op}" '
                            f'stroke="{col}" stroke-width="0.6"/>')
            self.out.append(f'<text x="{x + 18}" y="{y}" style="{STYLE};font-size:10px">{H.escape(lab)}</text>')
            x += 26 + 6.2 * len(lab)

    def svg(self):
        self.out[0] = f'<rect x="0" y="0" width="{self.w}" height="{self.h:.0f}" fill="#ffffff"/>'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h:.0f}" '
                f'viewBox="0 0 {self.w} {self.h:.0f}">' + "".join(self.out) + "</svg>\n")


def _bounds(polys, margin=600):
    xs = [p[0] for P in polys for p in P]
    ys = [p[1] for P in polys for p in P]
    return min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin


def _box(b):
    return [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]


def _uid_state(P):
    return {u["UID"]: T.contrib(u)["STATE"] for u in P["U"]}


def _state_col(st):
    if st == "MEASURED":
        return C_MEAS
    if st == "CONDITIONAL":
        return C_COND
    if st.startswith("EXCLUDED"):
        return C_EXCL
    return C_UNRES


# ------------------------------------------------------------------ 1 ground zone footprint
def fig_ground(P):
    D = P["D"]
    rec = D["sheets"]["SH08"]
    st = _uid_state(P)
    faces = [f for f in rec["slab"]["faces"] if len(f["polygon"]) >= 3]
    x0, y0, x1, y1 = P["plot"]["bounds_sh08"]
    c = Canvas((x0 - 500, y0 - 500, x1 + 500, y1 + 500), title="1  Ground beams + ground slab: drawn footprint, "
               "Urban state, freelancer plate", subtitle="SH08 ground-beam plan. Plot 31.37 x 15.00 m (printed). "
               "The freelancer's 295.5 m2 plate is a typed area with no outline: it cannot be drawn.")
    c.poly(_box((x0, y0, x1, y1)), "#ffffff", stroke=C_GEO, op=0.0, sw=0.8, dash="6,4", title="plot (S-BOUN)")
    for f in faces:
        sid = None
        for pre in ("P-C:GROUND_SLAB:GROUND:", "U-C:GROUND_SLAB:GROUND:"):
            if pre + f["face_id"] in st:
                sid = st[pre + f["face_id"]]
        if f["class"] == "PANEL":
            col = _state_col(sid or "UNRESOLVED")
            c.poly(f["polygon"], col, stroke=col, op=0.16 if col == C_MEAS else 0.32,
                   title=f"{f['face_id']} {f['area_m2']:.2f} m2 {sid}")
    for b in rec["bands"]:
        cid = "P-C:GROUND_BEAMS:GROUND:" + b["band_id"]
        u = next((x for x in P["U"] if x["UID"] == cid), None)
        ext = u and (u["DIMS"] or {}).get("arch_class") == "EXTERIOR_WALL"
        c.poly(b["polygon"], "#2c5282" if ext else "#3182ce", stroke="#1a365d", op=0.85 if ext else 0.7, sw=0.3,
               title=f"{b['band_id']} {'exterior' if ext else 'interior'} {b['length'] / 1000:.2f} m")
    for cb in rec.get("column_boxes", []):
        c.poly(_box(cb), INK, op=0.9)
    for r in P["runs"]:
        c.poly(r["points"], C_TEXT, stroke=C_TEXT, op=0.7, title=f"boundary wall {r['handle']} {r['centreline_m']:.2f} m")
    for u, f, parts in P["ctx"]["decomposition"]:
        Pp = Polygon(f["polygon"])
        c.text(Pp.centroid.x, Pp.centroid.y, "lift / lobby cell: CONDITIONAL", 9, C_UNRES, bold=True)
    gs = P["gs"]
    c.text(x0, y1 + 250, f"drawn plate {gs['footprint_m2']:.1f} m2 = measured cells {gs['measured_m2']:.1f} + "
           f"held cells {gs['unresolved_m2']:.1f} + beams / columns {gs['members_inside_m2']:.1f};  freelancer "
           f"{gs['fl_area_m2']:.1f} m2", 10, INK, anchor="start")
    c.legend([(C_MEAS, "GS cell measured (CAD)", 0.16), ("#3182ce", "interior GB (CAD)", 0.7),
              ("#2c5282", "exterior GB (CAD + arch)", 0.85),
              (C_COND, "GS cell conditional", 0.4), (C_UNRES, "GS cell unresolved", 0.4),
              (C_TEXT, "boundary wall run (CAD, S-BOUN)", 0.7), (INK, "column", 0.9)])
    return c.svg()


# ------------------------------------------------------------------ 2 foundations
def fig_foundations(P):
    D = P["D"]
    rec = D["sheets"]["SH10"]
    boxes = [f["box"] for f in rec["footings"] if f.get("box")]
    c = Canvas(_bounds([_box(b) for b in boxes]), title="2  Footings: drawn outlines by mark, freelancer count vs "
               "Urban", subtitle="SH10 foundation plan (CAD outlines). Red label = mark whose count or volume "
               "differs between the freelancer and Urban.")
    diff = {e["MARK_OR_PART"]: e for e in P["elements"] if e["FAMILY"] == "FOOTINGS"}
    for f in rec["footings"]:
        if not f.get("box"):
            continue
        mk = f.get("mark")
        key = "F+F10" if mk in ("F", "F10") else mk
        e = diff.get(key)
        bad = e and e["CLASS"] != "MATCHED_WITHIN_TOLERANCE"
        c.poly(_box(f["box"]), C_UNRES if bad else C_MEAS, stroke=INK, op=0.35, sw=0.5,
               title=f"{mk} {f.get('drawn_m')}")
        cx, cy = (f["box"][0] + f["box"][2]) / 2, (f["box"][1] + f["box"][3]) / 2
        c.text(cx, cy, mk, 9, C_UNRES if bad else INK, bold=bool(bad))
    y = c.h - 40
    rows = sorted(diff.values(), key=lambda e: e["MARK_OR_PART"])
    txt = "  ".join(f"{e['MARK_OR_PART']}: FL {e['FREELANCER_M3']:.2f} / U {e['URBAN_MEASURED_BASE_M3']:.2f}"
                    for e in rows if e["CLASS"] != "MATCHED_WITHIN_TOLERANCE")
    c.out.append(f'<text x="{c.pad}" y="{y}" style="{STYLE};font-size:10px">Differences: {H.escape(txt)}</text>')
    c.legend([(C_MEAS, "footing outline, same count and size (CAD)", 0.35),
              (C_UNRES, "mark with a count / overlap difference", 0.35)])
    return c.svg()


# ------------------------------------------------------------------ 3 slab maps
def fig_slabs(P):
    out = []
    st = _uid_state(P)
    for sh, floor in (("SH06", "GF"), ("SH04", "1F"), ("SH02", "2F")):
        rec = P["D"]["sheets"][sh]
        faces = [f for f in rec["slab"]["faces"] if len(f["polygon"]) >= 3]
        polys = [f["polygon"] for f in faces]
        c = Canvas(_bounds(polys), width=980, title=f"3{'abc'[len(out)]}  Suspended slab {floor} ({sh}): panels by "
                   "thickness basis and Urban state", subtitle="CAD faces of the M4 model. Panels stop at the beam "
                   "faces (beams measured full depth).")
        for f in faces:
            key = None
            for pre in (f"P-C:SLABS:{floor}:", f"U-C:SLABS:{floor}:"):
                if pre + f["face_id"] in st:
                    key = pre + f["face_id"]
            if f["class"] == "PANEL":
                s_ = st.get(key, "UNRESOLVED") if key else "NOT_SLAB"
                u = next((x for x in P["U"] if x["UID"] == key), None) if key else None
                t = (u["DIMS"] or {}).get("t_m") if u else None
                basis = (u["DIMS"] or {}).get("t_basis") if u else ""
                col = C_MEAS if s_ == "MEASURED" and basis == "PROJECT_DEFAULT" else \
                    (C_TEXT if s_ == "MEASURED" else (C_EXCL if s_.startswith("EXCLUDED") else C_UNRES))
                c.poly(f["polygon"], col, stroke=col, op=0.3, title=f"{f['face_id']} {f['area_m2']:.2f} m2 t {t} "
                       f"{basis} {s_}")
                if t and f["area_m2"] > 6 and s_ == "MEASURED":
                    Pp = Polygon(f["polygon"]).buffer(0)
                    c.text(Pp.representative_point().x, Pp.representative_point().y, f"{t * 100:.0f}", 8, MUTED)
            elif f["class"] == "BEAM":
                c.poly(f["polygon"], C_GEO, op=0.5)
        if floor == "1F":
            for dm in P["ctx"]["domes"]:
                x, y = dm["sh04"]
                pts = [(x + dm["r_mm"] * math.cos(a / 24 * 2 * math.pi), y + dm["r_mm"] * math.sin(a / 24 * 2 * math.pi))
                       for a in range(24)]
                c.poly(pts, "none", stroke=C_EXCL, op=0.0, sw=1.2, dash="4,3", title="dome circle (S-BOUN)")
                c.text(x, y, "dome", 9, C_EXCL, bold=True)
        c.legend([(C_MEAS, "16 cm project default (2 printed notes, machine-read)", 0.3),
                  (C_TEXT, "thickness printed in the panel", 0.3), (C_EXCL, "not slab (dome opening)", 0.3),
                  (C_UNRES, "unresolved", 0.3), (C_GEO, "beam strip", 0.5)])
        out.append(c.svg())
    return out


# ------------------------------------------------------------------ 4 beam depth readings (schematic)
def fig_beam_section(P):
    fam = P["fam"]
    w, h = 980, 360
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
         f'<rect width="{w}" height="{h}" fill="#fff"/>',
         f'<text x="30" y="24" style="{STYLE};font-size:15px;font-weight:bold">4  Beam depth readings and the '
         'beam / slab overlap (SCHEMATIC)</text>',
         f'<text x="30" y="42" style="{STYLE};fill:{MUTED}">Not to scale. The four sources split the same concrete '
         'differently; only the frame per floor is allocation-free.</text>']
    cases = [("Freelancer", "beam gross depth H (slab inside), slab net", True, False),
             ("Urban base (reading A)", "H overall incl. slab; panels stop at faces", True, False),
             ("Urban high (reading B)", "H below the slab: + t over every beam", True, True),
             ("MCP (U-C4N, christiannp)", "downstand only; slab full depth over beams", False, False)]
    for k, (name, why, gross, extra) in enumerate(cases):
        x = 40 + k * 235
        y0 = 90
        o.append(f'<rect x="{x}" y="{y0}" width="200" height="22" fill="{C_GEO}" fill-opacity="0.5"/>')
        if gross:
            o.append(f'<rect x="{x + 75}" y="{y0}" width="50" height="{110 if extra else 88}" fill="{C_MEAS}" '
                     'fill-opacity="0.6"/>')
            o.append(f'<rect x="{x}" y="{y0}" width="75" height="22" fill="{C_TEXT}" fill-opacity="0.45"/>')
            o.append(f'<rect x="{x + 125}" y="{y0}" width="75" height="22" fill="{C_TEXT}" fill-opacity="0.45"/>')
        else:
            o.append(f'<rect x="{x}" y="{y0}" width="200" height="22" fill="{C_TEXT}" fill-opacity="0.45"/>')
            o.append(f'<rect x="{x + 75}" y="{y0 + 22}" width="50" height="66" fill="{C_MEAS}" fill-opacity="0.6"/>')
        o.append(f'<text x="{x}" y="{y0 + 140}" style="{STYLE};font-weight:bold">{H.escape(name)}</text>')
        o.append(f'<text x="{x}" y="{y0 + 156}" style="{STYLE};font-size:10px;fill:{MUTED}">{H.escape(why)}</text>')
    rows = [("Freelancer beams + slabs", sum(r["FL_BEAMS"] + r["FL_SLABS"] for r in P["frame"])),
            ("Urban beams + slabs (base)", fam["BEAMS"]["MEAS_BASE"] + fam["SLABS"]["MEAS_BASE"]),
            ("Urban beams (reading B) + slabs", fam["BEAMS"]["MEAS_HIGH"] + fam["SLABS"]["MEAS_BASE"])]
    mc = {r["FAMILY"]: r for r in P["fam_rows"]}
    for s in ("UC4N", "CHRISTIANNP"):
        b, sl = mc["BEAMS"][s + "_M3"], mc["SLABS"][s + "_M3"]
        if isinstance(b, float) and isinstance(sl, float):
            rows.append((("U-C4N" if s == "UC4N" else "christiannp") + " beams + slabs", b + sl))
    y = 290
    for k, (lab, v) in enumerate(rows):
        o.append(f'<text x="{40 + (k % 3) * 310}" y="{y + (k // 3) * 18}" style="{STYLE}">{H.escape(lab)}: '
                 f'{v:.2f} m3</text>')
    o.append(f'<rect x="40" y="{h - 22}" width="14" height="10" fill="{C_MEAS}" fill-opacity="0.6"/><text x="60" '
             f'y="{h - 13}" style="{STYLE};font-size:10px">beam concrete</text><rect x="170" y="{h - 22}" width="14" '
             f'height="10" fill="{C_TEXT}" fill-opacity="0.45"/><text x="190" y="{h - 13}" style="{STYLE};'
             f'font-size:10px">slab concrete</text></svg>')
    return "".join(o) + "\n"


# ------------------------------------------------------------------ bar charts
def bars(title, subtitle, rows, unit="m3", width=980):
    """rows: (label, freelancer, urban_low, urban_base, urban_high, cond_high)"""
    n = len(rows)
    h = 90 + n * 26 + 50
    vmax = max([max(r[1] or 0, (r[4] or 0) + (r[5] or 0)) for r in rows] + [1e-9])
    x0, x1 = 300, width - 170
    sc = (x1 - x0) / vmax
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" viewBox="0 0 {width} {h}">',
         f'<rect width="{width}" height="{h}" fill="#fff"/>',
         f'<text x="30" y="24" style="{STYLE};font-size:15px;font-weight:bold">{H.escape(title)}</text>',
         f'<text x="30" y="42" style="{STYLE};fill:{MUTED}">{H.escape(subtitle)}</text>']
    for k, (lab, fl, lo, ba, hi, ch) in enumerate(rows):
        y = 70 + k * 26
        o.append(f'<text x="{x0 - 8}" y="{y + 14}" text-anchor="end" style="{STYLE}">{H.escape(lab)}</text>')
        o.append(f'<rect x="{x0}" y="{y}" width="{max((fl or 0) * sc, 0):.1f}" height="8" fill="{C_FL}" '
                 f'fill-opacity="0.75" rx="2"><title>freelancer {fl or 0:.3f}</title></rect>')
        o.append(f'<rect x="{x0}" y="{y + 10}" width="{max((ba or 0) * sc, 0):.1f}" height="8" fill="{C_MEAS}" '
                 f'fill-opacity="0.8" rx="2"><title>Urban base {ba or 0:.3f}</title></rect>')
        if hi and lo is not None:
            o.append(f'<line x1="{x0 + lo * sc:.1f}" y1="{y + 14}" x2="{x0 + hi * sc:.1f}" y2="{y + 14}" '
                     f'stroke="{INK}" stroke-width="1.2"/>')
        if ch:
            o.append(f'<rect x="{x0 + (ba or 0) * sc:.1f}" y="{y + 10}" width="{ch * sc:.1f}" height="8" '
                     f'fill="{C_COND}" fill-opacity="0.55" rx="2"><title>conditional up to {ch:.3f}</title></rect>')
        lab = f"FL {fl or 0:.2f} | U {ba or 0:.2f}" + (f" (cond. to {ch:.2f})" if ch else "")
        if not (fl or ba or ch or hi):
            lab = "in neither base: not drawn / unresolved"
        o.append(f'<text x="{x0 + max(fl or 0, (ba or 0) + (ch or 0), hi or 0) * sc + 6:.1f}" y="{y + 14}" '
                 f'style="{STYLE};font-size:9px;fill:{MUTED}">{H.escape(lab)}</text>')
    y = h - 20
    o.append(f'<rect x="30" y="{y - 9}" width="14" height="8" fill="{C_FL}" fill-opacity="0.75"/><text x="50" y="{y}" '
             f'style="{STYLE};font-size:10px">freelancer</text><rect x="130" y="{y - 9}" width="14" height="8" '
             f'fill="{C_MEAS}"/><text x="150" y="{y}" style="{STYLE};font-size:10px">Urban measured base (line: '
             f'low - high)</text><rect x="400" y="{y - 9}" width="14" height="8" fill="{C_COND}" fill-opacity="0.55"/>'
             f'<text x="420" y="{y}" style="{STYLE};font-size:10px">Urban conditional (up to high)</text></svg>')
    return "".join(o) + "\n"


def fig_stairs_domes(P):
    rows = []
    for e in P["elements"]:
        if e["FAMILY"] in ("STAIRS", "DOMES"):
            rows.append((f"{e['FAMILY'].title()} {e['MARK_OR_PART']}", e["FREELANCER_M3"], e["URBAN_MEASURED_LOW_M3"],
                         e["URBAN_MEASURED_BASE_M3"], e["URBAN_MEASURED_HIGH_M3"], e["URBAN_CONDITIONAL_HIGH_M3"]))
    return bars("5  Stairs and domes by element", "ST-A main, ST-B lobby steps, ST-C light-well, ST-D entrance; dome "
                "shells, rings, tower, drums. Riser scenarios are research only (never approved).", rows)


def fig_specials(P):
    rows = []
    for e in P["elements"]:
        if e["FAMILY"] in ("POOL", "POOL_PUMP_ROOM", "LIFT", "BOUNDARY_WALL", "GB_PERIMETER", "WATER_TANK",
                           "PARAPETS", "CANTILEVER_PORTIONS", "LINTELS"):
            rows.append((f"{e['FAMILY'].replace('_', ' ').title()} {e['MARK_OR_PART']}"[:42], e["FREELANCER_M3"],
                         e["URBAN_MEASURED_LOW_M3"], e["URBAN_MEASURED_BASE_M3"], e["URBAN_MEASURED_HIGH_M3"],
                         e["URBAN_CONDITIONAL_HIGH_M3"]))
    return bars("6  Pool and special scope", "Zero Urban bars with a conditional band = drawn but not "
                "measurable without an answer; zero everywhere = not drawn (UNRESOLVED, never assumed absent).", rows)


def fig_blinding(P):
    D = P["D"]
    fp = D["sheets"]["SH10"]
    shift = D["blinding_overlap"]["shift"].get("SH08", (0.0, 0.0))
    boxes = [f["box"] for f in fp["footings"] if f.get("box")]
    p = 100.0
    polys = [_box((b[0] - p, b[1] - p, b[2] + p, b[3] + p)) for b in boxes]
    o10, o8 = M.sheet_origin(D, "SH10"), M.sheet_origin(D, "SH08")
    x0, y0, x1, y1 = P["plot"]["bounds_sh08"]
    plot10 = _box((x0 - o8[0] + o10[0], y0 - o8[1] + o10[1], x1 - o8[0] + o10[0], y1 - o8[1] + o10[1]))
    c = Canvas(_bounds([plot10]), title="7  Blinding: drawn layer (footings + ground beams) vs the freelancer's "
               "full-plot plate", subtitle="Plain concrete, kept apart from RC. Footing outlines + 100 mm "
               "projection (SH10); ground-beam strips registered from SH08; dashed: plot plate (freelancer).")
    c.poly(plot10, C_FL, stroke=C_FL, op=0.07, sw=1.0, dash="6,4", title="full plot 31.37 x 15.00 (freelancer)")
    for b in D["sheets"]["SH08"]["bands"]:
        pts = [(x + shift[0], y + shift[1]) for x, y in b["polygon"]]
        P_ = Polygon(pts).buffer(p, join_style=2)
        c.poly(list(P_.exterior.coords), C_COND, op=0.35)
    for q in polys:
        c.poly(q, C_MEAS, stroke=C_MEAS, op=0.4)
    bo = P["blind_overlap"]
    c.text(plot10[0][0], plot10[2][1] + 300, f"footing layer {bo['footings_m2']:.1f} m2, beam strips "
           f"{bo['beams_m2']:.1f} m2, counted once {bo['placed_union_m2']:.1f} m2; plot plate "
           f"{P['blind_rows'][3]['AREA_M2']:.1f} m2", 10, INK, anchor="start")
    c.legend([(C_MEAS, "footing + projection (CAD + p.13 text)", 0.4), (C_COND, "ground-beam strip (CAD)", 0.35),
              (C_FL, "freelancer full plot (not drawn as a layer)", 0.1)])
    return c.svg()


def fig_top20(P):
    rate = P["rate"]
    rows = sorted([e for e in P["elements"] if e["FAMILY"] != "BLINDING"],
                  key=lambda e: -abs(e["DIFF_FREELANCER_MINUS_URBAN_BASE_M3"] or 0))[:20]
    width, h = 980, 90 + 20 * 24 + 40
    vmax = max(abs(e["DIFF_FREELANCER_MINUS_URBAN_BASE_M3"]) for e in rows) * rate
    mid = 560
    sc = (width - mid - 150) / vmax
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" viewBox="0 0 {width} {h}">',
         f'<rect width="{width}" height="{h}" fill="#fff"/>',
         f'<text x="30" y="24" style="{STYLE};font-size:15px;font-weight:bold">8  Top 20 discrepancies by KWD '
         f'(freelancer - Urban measured base, {rate} KWD/m3)</text>',
         f'<text x="30" y="42" style="{STYLE};fill:{MUTED}">Right = the freelancer prices more; left = Urban measures '
         'more. Class in brackets.</text>', f'<line x1="{mid}" y1="60" x2="{mid}" y2="{h - 30}" stroke="{GRID}"/>']
    for k, e in enumerate(rows):
        y = 64 + k * 24
        v = e["DIFF_FREELANCER_MINUS_URBAN_BASE_M3"] * rate
        x = mid if v >= 0 else mid + v * sc
        col = C_FL if v >= 0 else C_MEAS
        o.append(f'<text x="{min(mid, x) - 8 if v >= 0 else x - 8}" y="{y + 12}" text-anchor="end" '
                 f'style="{STYLE};font-size:10px">{H.escape(e["FAMILY"].title() + " " + e["FLOOR"] + " " + e["MARK_OR_PART"])}'
                 f' ({H.escape(e["CLASS"].split(" ")[0][:28])})</text>')
        o.append(f'<rect x="{x:.1f}" y="{y + 3}" width="{abs(v) * sc:.1f}" height="12" fill="{col}" '
                 f'fill-opacity="0.75" rx="2"/>')
        o.append(f'<text x="{(mid + v * sc + 6) if v >= 0 else mid + 6}" y="{y + 13}" style="{STYLE};font-size:9px;'
                 f'fill:{MUTED}">{v:+.0f} KWD ({e["DIFF_FREELANCER_MINUS_URBAN_BASE_M3"]:+.2f} m3)</text>')
    o.append("</svg>")
    return "".join(o) + "\n"


def fig_unresolved(P):
    out = []
    st = _uid_state(P)
    for sh, floor, fams in (("SH06", "GF", ("BEAMS", "SLABS", "LINTELS")), ("SH04", "1F", ("BEAMS", "SLABS", "LINTELS")),
                            ("SH02", "2F", ("BEAMS", "SLABS", "LINTELS")), ("SH08", "GROUND", ("GROUND_SLAB",))):
        rec = P["D"]["sheets"][sh]
        polys = [b["polygon"] for b in rec["bands"]] + [f["polygon"] for f in rec["slab"]["faces"]
                                                         if len(f["polygon"]) >= 3]
        c = Canvas(_bounds(polys), title=f"9{'abcd'[len(out)]}  Missing / unresolved / reallocated concrete on {sh} "
                   f"({floor})", subtitle="Each mark is an Urban item that is not in the measured base (conditional, "
                   "unresolved or moved by an M5 decision); hover for the item id.")
        for b in rec["bands"]:
            c.poly(b["polygon"], C_GEO, op=0.35)
        n = 0
        keys = []
        for u in P["U"]:
            if u["ORIGIN"] != "M4" or u["FAMILY"] not in fams:
                continue
            s_ = st[u["UID"]]
            if s_ == "MEASURED":
                continue
            part = u["UID"].split(":")[-1]
            poly = None
            if u["FAMILY"] in ("BEAMS", "GROUND_BEAMS"):
                pp = M.band_polygon(P["D"], sh, part)
                poly = list(pp.exterior.coords) if pp is not None else None
            elif u["FAMILY"] in ("SLABS", "GROUND_SLAB"):
                f = next((f for f in rec["slab"]["faces"] if f["face_id"] == part), None)
                poly = f["polygon"] if f else None
            if not poly:
                continue
            n += 1
            keys.append((u["UID"], s_.split(" ")[0], f" ({u['EXP_HIGH']:.2f} m3 high)" if u.get("EXP_HIGH") else ""))
            col = _state_col(s_)
            c.poly(poly, col, stroke=col, op=0.6, sw=1.0, title=f"{u['UID']} {s_} {u.get('M5_NOTE', '')}")
            Pp = Polygon(poly).buffer(0)
            c.text(Pp.representative_point().x, Pp.representative_point().y, str(n), 8, INK, bold=True)
        c.legend([(C_COND, "conditional (drawn, needs an answer)", 0.6), (C_UNRES, "unresolved", 0.6),
                  (C_EXCL, "excluded / reallocated by an M5 decision", 0.6), (C_GEO, "other bands (context)", 0.35)])
        y = c.h + 4
        for k_, (uid, s_, ex) in enumerate(keys):
            col_x = c.pad + (k_ % 2) * 470
            if k_ % 2 == 0:
                y += 14
            c.out.append(f'<text x="{col_x}" y="{y}" style="{STYLE};font-size:9px">{k_ + 1}: '
                         f'{H.escape(uid.split(":", 1)[-1])} - {H.escape(s_)}{H.escape(ex)}</text>')
        c.h = y + 16
        c.out[0] = f'<rect x="0" y="0" width="{c.w}" height="{c.h:.0f}" fill="#ffffff"/>'
        out.append(c.svg())
    return out


def fig_waterfall(P):
    b = P["bridge"]
    steps = b["steps"]
    width, h = 980, 640
    vals = [b["start"]]
    run = b["start"]
    for s in steps:
        run += s["M3"]
        vals.append(run)
    lo, hi = min(vals) - 10, max(vals) + 5
    x0 = 60
    bw = (width - 2 * x0) / (len(steps) + 2)
    sy = (h - 260) / (hi - lo)

    def Y(v):
        return 70 + (hi - v) * sy
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" viewBox="0 0 {width} {h}">',
         f'<rect width="{width}" height="{h}" fill="#fff"/>',
         f'<text x="30" y="24" style="{STYLE};font-size:15px;font-weight:bold">10  Freelancer RC -> Urban measured '
         'base (waterfall, m3)</text>',
         f'<text x="30" y="42" style="{STYLE};fill:{MUTED}">Each step = Urban - freelancer for one cause (04). The '
         'axis starts at {:.0f} m3.</text>'.format(lo)]
    o.append(f'<rect x="{x0}" y="{Y(b["start"]):.1f}" width="{bw * 0.8:.1f}" height="{Y(lo) - Y(b["start"]):.1f}" '
             f'fill="{C_FL}" fill-opacity="0.8"/><text x="{x0 + bw * 0.4:.1f}" y="{Y(b["start"]) - 4:.1f}" '
             f'text-anchor="middle" style="{STYLE};font-size:9px">{b["start"]:.1f}</text>')
    run = b["start"]
    for k, s in enumerate(steps, 1):
        a, z = run, run + s["M3"]
        x = x0 + k * bw
        col = C_UNRES if s["M3"] < 0 else C_MEAS
        o.append(f'<rect x="{x:.1f}" y="{Y(max(a, z)):.1f}" width="{bw * 0.8:.1f}" height="{max(abs(Y(a) - Y(z)), 0.8):.1f}" '
                 f'fill="{col}" fill-opacity="0.75"><title>{H.escape(s["STEP"])}: {s["M3"]:+.3f} m3</title></rect>')
        o.append(f'<text x="{x + bw * 0.4:.1f}" y="{Y(max(a, z)) - 3:.1f}" text-anchor="middle" style="{STYLE};'
                 f'font-size:8px;fill:{MUTED}">{s["M3"]:+.1f}</text>')
        o.append(f'<text transform="translate({x + bw * 0.45:.1f},{Y(lo) + 12:.1f}) rotate(60)" '
                 f'style="{STYLE};font-size:8px">{H.escape(s["STEP_ID"] + " " + s["STEP"][:34])}</text>')
        run = z
    x = x0 + (len(steps) + 1) * bw
    o.append(f'<rect x="{x:.1f}" y="{Y(b["end"]):.1f}" width="{bw * 0.8:.1f}" height="{Y(lo) - Y(b["end"]):.1f}" '
             f'fill="{C_MEAS}" fill-opacity="0.9"/><text x="{x + bw * 0.4:.1f}" y="{Y(b["end"]) - 4:.1f}" '
             f'text-anchor="middle" style="{STYLE};font-size:9px">{b["end"]:.1f}</text>')
    o.append("</svg>")
    return "".join(o) + "\n"


def visuals(P):
    svgs = {"01_GROUND_ZONE_FOOTPRINT.svg": fig_ground(P), "02_FOOTINGS_BY_MARK.svg": fig_foundations(P)}
    for k, s in enumerate(fig_slabs(P)):
        svgs[f"03{'abc'[k]}_SLAB_MAP_{('GF', '1F', '2F')[k]}.svg"] = s
    svgs["04_BEAM_DEPTH_READINGS_SCHEMATIC.svg"] = fig_beam_section(P)
    svgs["05_STAIRS_DOMES.svg"] = fig_stairs_domes(P)
    svgs["06_POOL_SPECIAL_SCOPE.svg"] = fig_specials(P)
    svgs["07_BLINDING_OVERLAP.svg"] = fig_blinding(P)
    svgs["08_TOP20_DISCREPANCIES.svg"] = fig_top20(P)
    for k, s in enumerate(fig_unresolved(P)):
        svgs[f"09{'abcd'[k]}_UNRESOLVED_{('SH06', 'SH04', 'SH02', 'SH08')[k]}.svg"] = s
    svgs["10_WATERFALL.svg"] = fig_waterfall(P)
    body = "".join(f'<section><div class="fig">{s}</div><p class="cap">{H.escape(n)}</p></section>'
                   for n, s in svgs.items())
    n = P["numbers"]
    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>M5 Visual Concrete QA</title>
<style>body{{font-family:Arial,Helvetica,sans-serif;color:{INK};background:#fff;margin:24px}}
h1{{font-size:20px}} .note{{color:{MUTED};font-size:12px;max-width:980px}}
section{{page-break-inside:avoid;margin:18px 0}} .fig svg{{max-width:100%;height:auto;border:1px solid {GRID}}}
.cap{{font-size:10px;color:{MUTED}}} @media print{{section{{page-break-after:always}}}}</style></head><body>
<h1>M5 - Visual concrete QA (ST7757)</h1>
<p class="note">Planning reconciliation, not engineering-approved. Urban measured RC base {n['urban_m5']['MEAS_BASE']:.2f} m3
(low {n['urban_m5']['MEAS_LOW']:.2f}, high {n['urban_m5']['MEAS_HIGH']:.2f}); conditional {n['urban_m5']['COND_LOW']:.2f} -
{n['urban_m5']['COND_HIGH']:.2f} m3; blinding kept apart. Marks: SOURCE GEOMETRY = CAD entities of the M4 model;
SOURCE TEXT = printed value; CONDITIONAL; UNRESOLVED. Schematic figures are labelled so.</p>{body}</body></html>"""
    return svgs, page


def to_pdf(html_path, pdf_path):
    chrome = "/opt/pw-browsers/chromium"
    if not Path(chrome).exists():
        return {"pdf": None, "why": "chromium not found"}
    r = subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu", f"--print-to-pdf={pdf_path}",
                        "--no-pdf-header-footer", f"file://{Path(html_path).resolve()}"], capture_output=True,
                       text=True, timeout=180)
    ok = Path(pdf_path).exists()
    return {"pdf": str(Path(pdf_path).name) if ok else None, "returncode": r.returncode,
            "bytes": Path(pdf_path).stat().st_size if ok else 0}
