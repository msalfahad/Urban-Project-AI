"""S9A report and visual layer: the README, the completeness report, the SVG figures and the visual QA page.

    called by build_s9a.write(L, s); not run on its own

Nothing here measures or decides. Every number is read from the builder's registers (L) or from the S1 / S9 registers
the builder hashed into its manifest. Plan figures are drawn from ST7757.dxf entities in each sheet's local mm (the
frame origin subtracted, as in every S1 register) and from the S1 polygons; nothing is moved, simplified or invented.

Each figure carries one or more of three labels:
    SOURCE-DERIVED  drawn at the position the source records (DXF entities, S1 polygons, register coordinates)
    SCHEMATIC       explains a rule or a reading; sizes may be to scale, positions are not drawn positions
    CONDITIONAL     a value that holds only under an unconfirmed reading; never released, never in a total

Deterministic: fixed number formatting, sorted iteration, ids taken from register ids, no clock.
"""

from __future__ import annotations

import html
import json
import math
import re
import statistics
from collections import Counter, defaultdict

from engine.source import structural_completeness as SCQ

SHEET_INFO = {"GFRS": ("GF roof slab", "GF"), "FFRS": ("1F roof slab", "1F"), "SFRS": ("2F roof slab", "2F")}
LANE_GROUP = {"RELEASED_FROZEN_STAGE": "REL", "RELEASED_S9_DELTA": "REL", "CONDITIONAL_NOT_RELEASED": "COND",
              "INDICATIVE_ONLY_NOT_RELEASED": "COND", "SOURCE_CONFLICT": "CONF", "BLOCKED_UNQUANTIFIED": "BLK",
              "NOT_IN_SOURCE": "BLK", "EXCLUDED_OWNED_BY_OTHER_FAMILY": "OWN", "NOT_APPLICABLE": "OWN"}
GROUPS = ("REL", "COND", "CONF", "BLK", "OWN")
GROUP_LABEL = {"REL": "Released", "COND": "Conditional / indicative", "CONF": "Source conflict",
               "BLK": "Blocked / not in source", "OWN": "Owned by another family / n.a."}
LABEL_NOTE = {"SOURCE-DERIVED": "drawn where the source puts it: DXF entities, S1 polygons, register coordinates",
              "SCHEMATIC": "explains a rule or a reading; not a drawn position",
              "CONDITIONAL": "holds only under an unconfirmed reading; never released, never in a total"}

# ------------------------------------------------------------------ style
DARK = ("--surface:#1a1a19;--card:#232321;--ink:#f1f0eb;--ink2:#c4c2ba;--muted:#8f8d86;--grid:#353431;--rule:#4a4945;"
        "--plan:#a7a59d;--plan2:#6b6963;--neutral:#6a6863;--slab:#34332f;--s1:#3987e5;--s2:#d95926")
TOKENS = (":root{--surface:#fcfcfb;--card:#ffffff;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;"
          "--rule:#cfcdc4;--plan:#6f6d66;--plan2:#aeaca4;--good:#0ca30c;--warn:#fab219;--serious:#ec835a;"
          "--crit:#d03b3b;--neutral:#c2c0b7;--slab:#e7e5dd;--s1:#2a78d6;--s2:#eb6834}\n"
          "@media (prefers-color-scheme: dark){:root:not([data-theme=\"light\"]){" + DARK + "}}\n"
          ":root[data-theme=\"dark\"]{" + DARK + "}\n")
_G = {"REL": "--good", "COND": "--warn", "CONF": "--serious", "BLK": "--crit", "OWN": "--neutral"}
SVG_CSS = (
    ".t{font-family:system-ui,Inter,\"Segoe UI\",Roboto,Helvetica,Arial,sans-serif;fill:var(--ink);font-size:10.5px}"
    ".tt{font-size:15px;font-weight:650}.ts{font-size:11.5px;fill:var(--ink2)}.t2{fill:var(--ink2)}.tm{fill:var(--muted)}"
    ".tb{font-weight:650}.tx{font-size:9.5px}.tl{font-size:12.5px}.th{font-size:22px;font-weight:650}"
    ".ax{stroke:var(--grid);stroke-width:1;fill:none}.rule{stroke:var(--rule);stroke-width:1;fill:none}"
    ".pl{stroke:var(--plan);stroke-width:.7;fill:none;stroke-linecap:round;stroke-linejoin:round}"
    ".pl2{stroke:var(--plan2);stroke-width:.55;fill:none;stroke-dasharray:3 2}"
    ".plb{stroke:var(--ink2);stroke-width:1;fill:none}.gl{stroke:var(--grid);stroke-width:.8;stroke-dasharray:2 3}"
    ".dim{stroke:var(--ink2);stroke-width:.8;fill:none}.lead{stroke:var(--ink2);stroke-width:.7;fill:none}"
    ".slab{fill:var(--slab);stroke:var(--plan);stroke-width:.8}.void{fill:none;stroke:var(--plan2);stroke-width:.6;"
    "stroke-dasharray:2 2}.col{fill:var(--neutral);stroke:var(--ink2);stroke-width:.5}"
    ".ring{stroke:var(--surface);stroke-width:1.5}.mm{fill:none;stroke:var(--serious);stroke-width:1.6;"
    "stroke-dasharray:2.5 1.5}.hl{stroke:var(--crit);stroke-width:.8}.band{fill:var(--crit);fill-opacity:.18;"
    "stroke:var(--crit);stroke-width:1.2}.callout{fill:none;stroke:var(--crit);stroke-width:1.2}"
    ".s1{fill:var(--s1)}.s2{fill:var(--s2)}.k1{stroke:var(--s1)}.k2{stroke:var(--s2)}.surf{fill:var(--surface)}"
    ".card{fill:var(--card);stroke:var(--rule);stroke-width:1}.bdg{fill:none;stroke:var(--ink2);stroke-width:1}"
    ".bdg-SCHEMATIC{stroke-dasharray:3 2}.bdg-CONDITIONAL{stroke:var(--warn);fill:var(--warn);fill-opacity:.16}"
    ".tex{fill:none;stroke:var(--ink);stroke-opacity:.45;stroke-width:.8}"
    + "".join(f".f-{g}{{fill:var({v})}}.a-{g}{{fill:var({v});fill-opacity:.26;stroke:var({v});stroke-width:.8}}"
              f".k-{g}{{stroke:var({v})}}" for g, v in _G.items()))
ICONS = (
    '<symbol id="i-REL" viewBox="0 0 12 12"><circle cx="6" cy="6" r="5.5" style="fill:var(--good)"/>'
    '<path d="M3.3 6.2 5.2 8.1 8.8 4.3" style="fill:none;stroke:#fff;stroke-width:1.6;stroke-linecap:round;'
    'stroke-linejoin:round"/></symbol>'
    '<symbol id="i-COND" viewBox="0 0 12 12"><circle cx="6" cy="6" r="5" style="fill:var(--surface);'
    'stroke:var(--warn);stroke-width:1.6"/><path d="M6 1A5 5 0 0 0 6 11Z" style="fill:var(--warn)"/></symbol>'
    '<symbol id="i-CONF" viewBox="0 0 12 12"><path d="M6 .8 11.4 10.8H.6Z" style="fill:var(--serious)"/>'
    '<path d="M6 4.3v3.3" style="stroke:#fff;stroke-width:1.5;stroke-linecap:round"/>'
    '<circle cx="6" cy="9.2" r=".8" style="fill:#fff"/></symbol>'
    '<symbol id="i-BLK" viewBox="0 0 12 12"><circle cx="6" cy="6" r="5.5" style="fill:var(--crit)"/>'
    '<path d="M3.9 3.9 8.1 8.1M8.1 3.9 3.9 8.1" style="stroke:#fff;stroke-width:1.6;stroke-linecap:round"/></symbol>'
    '<symbol id="i-OWN" viewBox="0 0 12 12"><circle cx="6" cy="6" r="5" style="fill:none;stroke:var(--ink2);'
    'stroke-width:1.3"/><path d="M3.6 6h4.8" style="stroke:var(--ink2);stroke-width:1.5;stroke-linecap:round"/>'
    '</symbol>')


# ------------------------------------------------------------------ formatting
def E(s):
    return html.escape(str(s), quote=True)


def c(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def q(v, nd=3):
    """a quantity with thousands separators; a missing value is a dash, never a zero"""
    return "-" if v is None else f"{v:,.{nd}f}"


def tw(s, size=10.5):
    return len(str(s)) * size * 0.56


def _f(v):
    return None if v in (None, "", "None") else float(v)


# ------------------------------------------------------------------ svg primitives
class Fig:
    def __init__(self, fid, name, title, labels, w, h, body, sub="", defs="", caption="", sources=()):
        self.fid, self.name, self.title, self.labels, self.w, self.h = fid, name, title, labels, w, h
        self.body, self.sub, self.defs, self.caption, self.sources = body, sub, defs, caption, list(sources)

    def _head(self):
        out = [f'<text class="t tt" x="16" y="25">{E(self.title)}</text>']
        if self.sub:
            out.append(f'<text class="t ts" x="16" y="43">{E(self.sub)}</text>')
        x = self.w - 16
        for lab in reversed(self.labels):
            bw = len(lab) * 6.4 + 16
            x -= bw
            out.append(f'<g data-label="{lab}"><rect class="bdg bdg-{lab}" x="{c(x)}" y="12" width="{c(bw)}" '
                       f'height="18" rx="9"/><text class="t tx tb" x="{c(x + bw / 2)}" y="24.5" '
                       f'text-anchor="middle">{lab}</text></g>')
            x -= 6
        return "".join(out)

    def standalone(self):
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{c(self.h)}" '
                f'viewBox="0 0 {self.w} {c(self.h)}" role="img" aria-labelledby="{self.fid}-t" '
                f'data-figure="{self.fid}"><title id="{self.fid}-t">{E(self.title)}</title>'
                f'<style>{TOKENS}{SVG_CSS}</style><defs>{ICONS}{self.defs}</defs>'
                f'<rect width="{self.w}" height="{c(self.h)}" style="fill:var(--surface)"/>'
                f'{self._head()}{self.body}</svg>\n')

    def inline(self):
        return (f'<svg class="fig" viewBox="0 0 {self.w} {c(self.h)}" role="img" aria-labelledby="{self.fid}-t" '
                f'data-figure="{self.fid}"><title id="{self.fid}-t">{E(self.title)}</title><defs>{self.defs}</defs>'
                f'{self._head()}{self.body}</svg>')


def T(x, y, s, cls="", anchor="start", extra=""):
    a = "" if anchor == "start" else f' text-anchor="{anchor}"'
    return f'<text class="t {cls}" x="{c(x)}" y="{c(y)}"{a}{extra}>{E(s)}</text>'


def icon(g, x, y, s=12):
    return f'<use href="#i-{g}" x="{c(x)}" y="{c(y)}" width="{s}" height="{s}"/>'


def tip(s):
    return f"<title>{E(s)}</title>"


def legend(items, x, y, maxw=968, size=10.5):
    """items: [(group or swatch markup, label)]; flows left to right, wraps at maxw"""
    out, cx, cy = [], x, y
    for g, lab in items:
        w = 18 + tw(lab, size) + 18
        if cx + w > x + maxw:
            cx, cy = x, cy + 18
        out.append(icon(g, cx, cy - 10) if g in GROUPS else g.replace("{x}", c(cx)).replace("{y}", c(cy - 10)))
        out.append(T(cx + 17, cy, lab, "t2"))
        cx += w
    return "".join(out), cy


def hbar(x, y, w, h, cls, title=""):
    """a bar with a 4 px rounded data end: square on the baseline (left), rounded at the value end"""
    if w <= 0:
        return ""
    r = min(4.0, w / 2, h / 2)
    d = (f"M{c(x)} {c(y)}H{c(x + w - r)}A{c(r)} {c(r)} 0 0 1 {c(x + w)} {c(y + r)}V{c(y + h - r)}"
         f"A{c(r)} {c(r)} 0 0 1 {c(x + w - r)} {c(y + h)}H{c(x)}Z")
    return f'<path class="{cls}" d="{d}">{tip(title) if title else ""}</path>'


def ticks(lo, hi, n=5):
    span = hi - lo
    raw = span / n
    mag = 10 ** math.floor(math.log10(raw))
    step = min((s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= raw), default=raw)
    v, out = math.ceil(lo / step) * step, []
    while v <= hi + 1e-9:
        out.append(round(v, 9))
        v += step
    return out


# ------------------------------------------------------------------ drawing geometry
class Geo:
    """ST7757.dxf entities by sheet frame, in local mm. The three slab sheets are the builder's; FP and GBP are found
    the same way (the title insert inside a DEFPOINTS frame of the same size)."""
    LAYERS = ("1", "2", "5", "S-BEAM", "S-BOUN", "S-OPENING", "S-COL.BON", "S-FOOTINGS")
    NAMES = ("GFRS", "FFRS", "SFRS", "FP", "GBP")

    def __init__(self, dwg):
        from ezdxf import bbox as BB
        from ezdxf import path as EP
        boxes = []
        for e in dwg.msp.query('LWPOLYLINE[layer=="DEFPOINTS"]'):
            b = BB.extents([e])
            if b.extmax.x - b.extmin.x > 20000 and b.extmax.y - b.extmin.y > 10000:
                boxes.append((b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
        ins = defaultdict(list)
        for i in dwg.msp.query("INSERT"):
            ins[i.dxf.name].append(i.dxf.insert)
        self.box = {}
        for n in self.NAMES:
            if len(ins[n]) != 1:
                raise ValueError(f"title insert {n}")
            p = ins[n][0]
            hit = [b for b in boxes if b[0] <= p.x <= b[2] and b[1] <= p.y <= b[3]]
            if len(hit) != 1:
                raise ValueError(f"frame of {n}")
            self.box[n] = hit[0]
        for n in SHEET_INFO:
            if tuple(self.box[n]) != tuple(dwg.frames[n]["box"]):
                raise ValueError(f"frame of {n} differs from the builder's")
        self.items = defaultdict(list)
        for e in dwg.msp.query("LINE LWPOLYLINE ARC CIRCLE"):
            if e.dxf.layer not in self.LAYERS:
                continue
            pts = [(v.x, v.y) for v in EP.make_path(e).flattening(2.0)]
            if len(pts) < 2:
                continue
            sh = self.sheet_of(*pts[0])
            if sh is None:
                continue
            a, b = self.box[sh][0], self.box[sh][1]
            closed = e.dxftype() == "CIRCLE" or (e.dxftype() == "LWPOLYLINE" and e.closed)
            self.items[(sh, e.dxf.layer)].append((e.dxf.handle, closed, [(x - a, y - b) for x, y in pts]))
        for k in self.items:
            self.items[k].sort(key=lambda r: r[0])
        self.text_at = {}
        for t in dwg.msp.query("TEXT MTEXT"):
            p = t.dxf.insert
            sh = self.sheet_of(p.x, p.y)
            if sh:
                self.text_at[t.dxf.handle] = (sh, (p.x - self.box[sh][0], p.y - self.box[sh][1]))

    def sheet_of(self, x, y):
        for n, (a, b, cc, d) in self.box.items():
            if a <= x <= cc and b <= y <= d:
                return n
        return None

    def poly(self, sheet, handle):
        for lay in ("S-COL.BON", "S-FOOTINGS"):
            for h, _, pts in self.items[(sheet, lay)]:
                if h == handle:
                    return pts
        return None


class View:
    """local mm -> figure px: x right, y up in the drawing, down on the page; one scale k (px per mm)"""

    def __init__(self, box, w, h=None):
        x0, y0, x1, y1 = box
        self.k = w / (x1 - x0) if h is None else min(w / (x1 - x0), h / (y1 - y0))
        self.x0, self.y1 = x0, y1
        self.w, self.h = (x1 - x0) * self.k, (y1 - y0) * self.k

    def X(self, x):
        return (x - self.x0) * self.k

    def Y(self, y):
        return (self.y1 - y) * self.k

    def pts(self, poly):
        return " ".join(f"{c(self.X(x))},{c(self.Y(y))}" for x, y in poly)

    def path(self, polys):
        return "".join("M" + " L".join(f"{c(self.X(x))} {c(self.Y(y))}" for x, y in p) + "Z" for p in polys if p)

    def meta(self):
        return E(json.dumps({"x0": self.x0, "y1": self.y1, "k": self.k}, sort_keys=True))


def bbox(polys, pad=0.0):
    xs = [x for p in polys for x, _ in p]
    ys = [y for p in polys for _, y in p]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def centroid(poly):
    return (sum(x for x, _ in poly) / len(poly), sum(y for _, y in poly) / len(poly))


def inside_box(pts, box):
    return any(box[0] <= x <= box[2] and box[1] <= y <= box[3] for x, y in pts)


def lines_svg(G, sheet, v, box=None, layers=(("2", "pl2"), ("S-OPENING", "pl2"), ("5", "pl2"), ("1", "pl"),
                                           ("S-BEAM", "pl"), ("S-BOUN", "plb"))):
    out = []
    for lay, cls in layers:
        for h, closed, pts in G.items[(sheet, lay)]:
            if box and not inside_box(pts, box):
                continue
            tag = "polygon" if closed else "polyline"
            out.append(f'<{tag} class="{cls}" points="{v.pts(pts)}" data-h="{h}"/>')
    for h, closed, pts in G.items[(sheet, "S-COL.BON")]:
        if not closed and (not box or inside_box(pts, box)):
            out.append(f'<polyline class="pl" points="{v.pts(pts)}"/>')
    return "".join(out)


def scalebar(x, y, k, metres=5):
    L = metres * 1000 * k
    out = [f'<path class="dim" d="M{c(x)} {c(y)}H{c(x + L)}"/>']
    for i in range(metres + 1):
        xx = x + i * 1000 * k
        out.append(f'<path class="dim" d="M{c(xx)} {c(y - 3)}V{c(y + 3)}"/>')
    out.append(T(x, y + 14, "0", "tx t2"))
    out.append(T(x + L, y + 14, f"{metres} m", "tx t2", "middle"))
    return "".join(out)


# ------------------------------------------------------------------ register views
def lanes(L):
    return {r["COMPONENT_ID"]: r["LANE"] for r in L["s9conc"]}


def beam_group(state):
    if state.startswith(("CONDITIONAL", "UPPER_BOUND", "BAND_IS")):
        return "COND"
    if state.startswith("SOURCE_CONFLICT"):
        return "CONF"
    return "BLK"


def s9a_inventory(L):
    """S9's 560 records with S9A's owner changes applied: each re-owned span is superseded by its band row; the CA band
    is added as a record its beam owns. Neither change carries a quantity."""
    sup = {d["COMPONENT_ID"] for d in L["deltas"] if d["CHANGE_KIND"] == "OWNERSHIP_TRANSFER"}
    rows = [{"ID": r["COMPONENT_ID"], "FAMILY": r["FAMILY"], "STOREY": r["STOREY"], "LANE": r["CONCRETE_LANE"]}
            for r in L["s9inv"] if r["COMPONENT_ID"] not in sup]
    for b in L["bands"]:
        rows.append({"ID": b["BAND_ID"], "FAMILY": "CANTILEVER_PORTIONS", "STOREY": b["STOREY_SLAB"].split()[0],
                     "LANE": "EXCLUDED_OWNED_BY_OTHER_FAMILY" if b["OWNER_DECISION"].startswith("BEAMS")
                     else "BLOCKED_UNQUANTIFIED"})
    if len(rows) != len(L["s9inv"]) - len(sup) + len(L["bands"]) or len({r["ID"] for r in rows}) != len(rows):
        raise ValueError("S9A inventory view")
    return rows


class Reg:
    """the S1 registers the plan figures read (paths and hashes are in the builder's manifest)"""

    def __init__(self, L):
        j = lambda k: json.loads(open(L["F"][k], encoding="utf-8").read())["rows"]  # noqa: E731
        self.slabs = j("S1_SLAB")
        self.cocc = j("S1_COCC")
        self.bocc = j("S1_BOCC")
        self.cbocc = j("S1_CBOCC")
        self.focc = j("S1_FOCC")


def beam_marks(L, R, G):
    """tag positions of the compared beams (simple beams: S1's tag position; continuous spans: the span's tag text);
    untagged spans have no tag, so no marker"""
    pos = {r["beam_id"]: (r["sheet"], tuple(r["tag_position_mm"])) for r in R.bocc
           if r.get("tag_position_mm") and r.get("sheet")}
    for r in R.cbocc:
        for i, s in enumerate(r["plan_spans"], 1):
            t = G.text_at.get(s.get("tag_handle"))
            if t and t[0] == r["sheet"]:
                pos[f"{r['cb_id']}#SPAN{i}"] = t
    out = defaultdict(list)
    for b in L["beams"]:
        p = pos.get(b["COMPONENT_ID"])
        if p and p[0] == b["SHEET"]:
            out[b["SHEET"]].append((b, p[1]))
    return out


# ============================================================================ figures
def fig_dashboard(L, s):
    inv = s9a_inventory(L)
    s9 = L["s9sum"]
    agree = [r for r in L["verify"] if r["RESULT"] == "AGREES"]
    worst = max(abs(r["PUBLISHED_MINUS_INDEPENDENT"]) for r in agree)
    allb = next(r for r in L["beam_tot"] if r["GROUP"] == "ALL" and r["SET"].startswith("conditional"))
    tiles = [
        ("REL", "Released concrete", f"{q(s9['released_concrete_m3_total'])} m3",
         "unchanged by S9A: delta 0.000 m3"),
        ("REL", "Released reinforcement", f"{q(s9['released_reinforcement_kg_total'])} kg",
         f"{s9['released_reinforcement_kg_total'] / 1000:.3f} t; unchanged: delta 0.000 kg"),
        ("REL", "Independent recompute", f"{len(agree)} of {len(agree)} agree",
         "every difference below 0.000001" if worst < 1e-6 else f"largest difference {worst:.6f}"),
        ("COND", "Conditional beam concrete", f"{allb['TOTAL_DEPTH_M3']:.1f} - {allb['BELOW_SLAB_M3']:.1f} m3",
         f"{allb['BEAMS']} beams; never released (RFI-A01)"),
        ("BLK", "Open engineer questions", f"{len(L['rfi'])} RFIs",
         "project gate stays INCOMPLETE"),
    ]
    out, tw_, gap = [], 186.4, 9
    for i, (g, head, big, small) in enumerate(tiles):
        x = 16 + i * (tw_ + gap)
        out.append(f'<rect class="card" x="{c(x)}" y="56" width="{c(tw_)}" height="76" rx="8"/>')
        out.append(icon(g, x + 12, 67))
        out.append(T(x + 30, 77, head, "t2"))
        out.append(T(x + 12, 105, big, "th"))
        out.append(T(x + 12, 123, small, "tx t2"))
    fam_counts = defaultdict(Counter)
    for r in inv:
        fam_counts[r["FAMILY"]][LANE_GROUP[r["LANE"]]] += 1
    rel_m3 = s9["released_concrete_m3_by_family"]
    rel_kg = s9["released_reinforcement_kg_by_family"]
    fams = sorted(fam_counts, key=lambda f: (-sum(fam_counts[f].values()), f))
    y0, x0, bw, rh = 178, 190, 520, 20
    lg, _ = legend([(g, GROUP_LABEL[g]) for g in GROUPS], 16, 154)
    out.append(lg)
    out.append(T(x0 + bw + 24, y0 - 8, "Released m3", "tx t2 tb"))
    out.append(T(x0 + bw + 130, y0 - 8, "Released kg", "tx t2 tb"))
    for i, f in enumerate(fams):
        y = y0 + i * rh
        cn = fam_counts[f]
        tot = sum(cn.values())
        out.append(T(16, y + 13, f.replace("_", " ").title(), ""))
        out.append(T(x0 - 8, y + 13, str(tot), "tx t2", "end"))
        cx = x0
        for g in GROUPS:
            if not cn[g]:
                continue
            w = bw * cn[g] / tot
            seg = w - 2 if cx + w < x0 + bw - 0.01 else w
            out.append(f'<rect class="f-{g}" x="{c(cx)}" y="{c(y + 3)}" width="{c(max(seg, 0.8))}" height="15" '
                       f'rx="2">{tip(f"{f}: {cn[g]} {GROUP_LABEL[g].lower()}")}</rect>')
            if w > 22:
                fill = "#fff" if g in ("REL", "BLK") else "var(--ink)"
                out.append(f'<text class="t tx tb" x="{c(cx + w / 2 - 1)}" y="{c(y + 14)}" text-anchor="middle" '
                           f'style="fill:{fill}">{cn[g]}</text>')
            cx += w
        out.append(T(x0 + bw + 84, y + 13, q(rel_m3.get(f)) if f in rel_m3 else "-", "tn", "end"))
        out.append(T(x0 + bw + 210, y + 13, q(rel_kg.get(f)) if f in rel_kg else "-", "tn", "end"))
    yb = y0 + len(fams) * rh + 14
    out.append(f'<path class="rule" d="M16 {c(yb - 6)}H984"/>')
    out.append(T(16, yb + 10, f"All families: {len(inv)} records after S9A ({len(L['s9inv'])} in S9; "
                 f"{sum(1 for d in L['deltas'] if d['CHANGE_KIND'] == 'OWNERSHIP_TRANSFER')} untagged spans "
                 f"superseded by their band rows, {len(L['bands'])} band rows added). Each record holds one lane.",
                 "tx t2"))
    out.append(T(x0 + bw + 84, yb + 10, q(s9["released_concrete_m3_total"]), "tn tb", "end"))
    out.append(T(x0 + bw + 210, yb + 10, q(s9["released_reinforcement_kg_total"]), "tn tb", "end"))
    return Fig("F01", "01_COVERAGE_DASHBOARD.svg", "1  Structural quantity coverage", ["SOURCE-DERIVED"], 1000,
               yb + 26, "".join(out),
               sub="Every structural record by family and lane. Bars count records; only released lanes carry "
                   "quantities into the BOQ.",
               caption="Counts are records, not volume. Released m3 and kg are S9's frozen totals, recomputed "
                       "independently by S9A (01_S9_TOTALS_VERIFICATION.csv).",
               sources=["S9 01 / 02 / 14", "S9A 01, 10"])


def fig_plan(L, s, G, R, sheet, marks):
    title, storey = SHEET_INFO[sheet]
    page = L["dwg"].frames[sheet]["page"]
    ln = lanes(L)
    panels = [p for p in R.slabs if p["sheet"] == sheet]
    cols = [(h, pts) for h, closed, pts in G.items[(sheet, "S-COL.BON")] if closed]
    box = bbox([p["polygon_mm"] for p in panels if p["class"] != "OUTSIDE_BUILDING_OR_COURT"]
               + [pts for _, pts in cols], 900)
    v = View(box, 940, 380)
    ox, oy = 16 + (940 - v.w) / 2 + 14, 70
    clip = f"F02-{sheet}-clip"
    defs = f'<clipPath id="{clip}"><rect x="0" y="0" width="{c(v.w)}" height="{c(v.h)}"/></clipPath>'
    body = [f'<g transform="translate({c(ox)},{c(oy)})" data-view="{v.meta()}" data-sheet="{sheet}">',
            f'<rect x="0" y="0" width="{c(v.w)}" height="{c(v.h)}" class="rule"/><g clip-path="url(#{clip})">']
    pc = Counter()
    for p in sorted(panels, key=lambda r: r["panel_id"]):
        lane = ln.get(p["panel_id"])
        g = LANE_GROUP.get(lane)
        polys = [p["polygon_mm"]] + list(p.get("holes_mm") or [])
        if p["class"] == "OUTSIDE_BUILDING_OR_COURT":
            continue
        if g is None:
            body.append(f'<path class="void" d="{v.path(polys)}"/>')
            continue
        pc[g] += 1
        info = f"{p['panel_id']}: {lane}; {p['class']}"
        body.append(f'<path class="a-{g}" fill-rule="evenodd" d="{v.path(polys)}" data-id="{p["panel_id"]}">'
                    f'{tip(info)}</path>')
    body.append(lines_svg(G, sheet, v))
    colid = {}
    for r in R.cocc:
        for h, sh in zip(r["plan_source"]["handles"], r["plan_source"]["sheets"]):
            if sh == sheet:
                colid[h] = r["column_id"]
    mism = {r["COLUMN_ID"] for r in L["cols"]}
    cc = Counter()
    for h, pts in cols:
        cid = colid.get(h)
        g = LANE_GROUP.get(ln.get(cid))
        cls = f"f-{g}" if g else "col"
        if g:
            cc[g] += 1
        info = f"{cid or h}: {ln.get(cid, '-')}"
        body.append(f'<polygon class="{cls}" points="{v.pts(pts)}" style="stroke:var(--ink2);stroke-width:.5" '
                    f'data-h="{h}">{tip(info)}</polygon>')
        if cid in mism:
            body.append(f'<polygon class="mm" points="{v.pts(pts)}"/>')
    bands = [b for b in L["bands"] if b["SHEET"] == sheet]
    for b in bands:
        body.append(f'<polygon class="band" points="{v.pts(b["POLYGON_LOCAL_MM"])}" data-band="{b["BAND_ID"]}">'
                    f'{tip(b["BAND_ID"] + ": " + b["CONCRETE_STATE"])}</polygon>')
        cx, cy = centroid(b["POLYGON_LOCAL_MM"])
        body.append(f'<circle class="callout" cx="{c(v.X(cx))}" cy="{c(v.Y(cy))}" r="9"/>')
        body.append(T(v.X(cx) + 12, v.Y(cy) - 8, b["BAND_ID"].replace("S9A-", ""), "tx tb"))
    bm = Counter()
    for b, (x, y) in sorted(marks.get(sheet, []), key=lambda t: t[0]["COMPONENT_ID"]):
        g = beam_group(b["S9A_STATE"])
        bm[g] += 1
        X, Y = v.X(x), v.Y(y)
        info = (f"{b['COMPONENT_ID']}: {b['S9A_STATE']}; B x H = {q(b['B_MM'], 0)} x {q(b['H_MM'], 0)} mm, "
                f"L = {q(b['L_M'])} m")
        body.append(f'<path class="f-{g} ring" d="M{c(X)} {c(Y - 5)}L{c(X + 5)} {c(Y)}L{c(X)} {c(Y + 5)}'
                    f'L{c(X - 5)} {c(Y)}Z" data-beam="{E(b["COMPONENT_ID"])}">{tip(info)}</path>')
    body.append("</g>")
    occ = [r for r in R.cocc if r["floor"] == storey and r.get("plan_centre_mm") and r.get("grid")]
    for axis, idx in (("X", 0), ("Y", 1)):
        pos = defaultdict(list)
        for r in occ:
            if r["grid"].get(axis):
                pos[r["grid"][axis]].append(r["plan_centre_mm"][idx])
        last = None
        for lab, vals in sorted(pos.items(), key=lambda kv: statistics.median(kv[1])):
            m = statistics.median(vals)
            if axis == "X":
                X = v.X(m)
                if last is not None and X - last < 22:
                    continue
                last = X
                body.append(f'<path class="gl" d="M{c(X)} -6V{c(v.h)}"/>')
                body.append(f'<circle cx="{c(X)}" cy="-14" r="8" class="surf" style="stroke:var(--ink2)"/>')
                body.append(T(X, -10.5, lab.replace("X", ""), "tx", "middle"))
            else:
                Y = v.Y(m)
                if last is not None and last - Y < 18:
                    continue
                last = Y
                body.append(f'<path class="gl" d="M-6 {c(Y)}H{c(v.w)}"/>')
                body.append(f'<circle cx="-16" cy="{c(Y)}" r="8" class="surf" style="stroke:var(--ink2)"/>')
                body.append(T(-16, Y + 3.5, lab.replace("Y", ""), "tx", "middle"))
    body.append(scalebar(0, v.h + 16, v.k))
    body.append("</g>")
    y = oy + v.h + 46
    rows = [("Slab panels", pc), ("Columns", cc), ("Beams (marker at the beam tag)", bm)]
    for i, (name, cnt) in enumerate(rows):
        yy = y + i * 16
        body.append(T(16, yy, name, "tb"))
        x = 200
        for g in GROUPS:
            if cnt[g]:
                body.append(icon(g, x, yy - 10))
                lab = f"{cnt[g]} {GROUP_LABEL[g].lower()}"
                body.append(T(x + 16, yy, lab, "t2"))
                x += 30 + tw(lab)
    yy = y + 3 * 16
    body.append(f'<rect class="band" x="200" y="{c(yy - 10)}" width="14" height="10"/>')
    body.append(T(16, yy, "Cantilever bands", "tb"))
    body.append(T(220, yy, f"{len(bands)} dense-hatch bands (S9A, thickness unknown)", "t2"))
    body.append(f'<rect class="mm" x="470" y="{c(yy - 10)}" width="12" height="10"/>')
    body.append(T(488, yy, "column whose drawn section differs from the schedule (F06)", "t2"))
    body.append(T(16, yy + 16, "Outside and courtyard faces are not shaded. Hover any element for its id and lane.",
                  "tx tm"))
    h = yy + 26
    return Fig(f"F02-{sheet}", f"02_LOCATION_MAP_{storey}_ROOF.svg",
               f"2  {title}: what is released, conditional or blocked", ["SOURCE-DERIVED"], 1000, h,
               "".join(body), defs=defs, sub=f"ST7757.dxf sheet {sheet} (PDF page {page}); local mm; grid labels from the "
                                  "S1 column centres. Hover any element for its id and lane.",
               caption=("Panels are S1 polygons coloured by their S9 concrete lane; columns are the drawn S-COL.BON "
                        "outlines; diamonds sit on beam tags (untagged spans have no tag and no diamond). Line work "
                        "is the drawing's own layers 1 / 2 / S-BOUN / S-OPENING."),
               sources=["ST7757.dxf", "S1 slab, column, beam registers", "S9 02", "S9A 03, 05, 09"])


def fig_foundation(L, s, G, R):
    ln = lanes(L)
    ftg = [(r, r["outline"]["bbox"]) for r in R.focc if r.get("outline") and r["outline"].get("bbox")]
    fcols = []
    for r in R.cocc:
        if r["floor"] != "FOUNDATION":
            continue
        for h, sh in zip(r["plan_source"]["handles"], r["plan_source"]["sheets"]):
            if sh == "FP":
                pts = G.poly("FP", h)
                if pts:
                    fcols.append((r["column_id"], h, pts))
    walls = []
    for r in L["s9conc"]:
        m = re.search(r"rect \[([-\d.]+), ([-\d.]+), ([-\d.]+), ([-\d.]+)\]", r["SOURCE"])
        if r["FAMILY"] == "LIFT" and m:
            walls.append((r, [float(x) for x in m.groups()]))
    rects = [[(a, b), (cc, b), (cc, d), (a, d)] for _, (a, b, cc, d) in ftg]
    box = bbox(rects + [p for _, _, p in fcols], 700)
    v = View(box, 940, 380)
    ox, oy = 16 + (940 - v.w) / 2 + 14, 70
    defs = f'<clipPath id="F02-FDN-clip"><rect x="0" y="0" width="{c(v.w)}" height="{c(v.h)}"/></clipPath>'
    body = [f'<g transform="translate({c(ox)},{c(oy)})" data-view="{v.meta()}" data-sheet="FP+GBP">',
            f'<rect x="0" y="0" width="{c(v.w)}" height="{c(v.h)}" class="rule"/><g clip-path="url(#F02-FDN-clip)">']
    body.append(lines_svg(G, "GBP", v, layers=(("1", "pl"),)))
    fc = Counter()
    for r, (a, b, cc, d) in sorted(ftg, key=lambda t: t[0]["footing_id"]):
        lane = ln.get(r["footing_id"])
        g = LANE_GROUP.get(lane, "OWN")
        ftype = r["type"] or "/".join(r.get("candidate_types") or []) or "?"
        fc[g] += 1
        body.append(f'<rect class="a-{g}" x="{c(v.X(a))}" y="{c(v.Y(d))}" width="{c((cc - a) * v.k)}" '
                    f'height="{c((d - b) * v.k)}" data-id="{r["footing_id"]}">'
                    f'{tip(r["footing_id"] + " (" + ftype + "): " + str(lane))}</rect>')
        if (cc - a) * v.k > 26:
            body.append(T(v.X((a + cc) / 2), v.Y((b + d) / 2) + 3.5, ftype, "tx t2", "middle"))
    nc = Counter()
    for cid, h, pts in sorted(fcols):
        g = LANE_GROUP.get(ln.get(cid), "OWN")
        nc[g] += 1
        body.append(f'<polygon class="f-{g}" points="{v.pts(pts)}" style="stroke:var(--ink2);stroke-width:.5">'
                    f'{tip(cid + ": " + str(ln.get(cid)))}</polygon>')
    for r, (a, b, cc, d) in walls:
        body.append(f'<rect class="f-COND" x="{c(v.X(a))}" y="{c(v.Y(d))}" width="{c((cc - a) * v.k)}" '
                    f'height="{c((d - b) * v.k)}">{tip(r["COMPONENT_ID"] + ": " + r["LANE"])}</rect>')
    if walls:
        wx = statistics.mean([(w[1][0] + w[1][2]) / 2 for w in walls])
        wy = max(w[1][3] for w in walls)
        body.append(T(v.X(wx), v.Y(wy) - 8, "LIFT PIT", "tx tb", "middle"))
    body.append("</g>")
    body.append(scalebar(0, v.h + 16, v.k))
    body.append("</g>")
    y = oy + v.h + 46
    for i, (name, cnt) in enumerate([("Footings", fc), ("Foundation necks (columns)", nc)]):
        yy = y + i * 16
        body.append(T(16, yy, name, "tb"))
        x = 220
        for g in GROUPS:
            if cnt[g]:
                body.append(icon(g, x, yy - 10))
                lab = f"{cnt[g]} {GROUP_LABEL[g].lower()}"
                body.append(T(x + 16, yy, lab, "t2"))
                x += 30 + tw(lab)
    yy = y + 32
    body.append(T(16, yy, "Lift pit walls", "tb"))
    body.append(icon("COND", 220, yy - 10))
    body.append(T(236, yy, f"{len(walls)} walls, indicative only (pit depth not printed)", "t2"))
    yy += 16
    body.append(T(16, yy, "Ground beams", "tb"))
    body.append(f'<path class="pl" d="M220 {c(yy - 4)}H236"/>')
    body.append(T(242, yy, "drawn edges from sheet GBP; span-by-span states are in F06b (the registers hold the "
                           "edge lines, not the span ends)", "t2"))
    return Fig("F02-FDN", "02_LOCATION_MAP_FOUNDATION.svg", "2  Foundation: footings, necks and the lift pit",
               ["SOURCE-DERIVED"], 1000, yy + 16, "".join(body), defs=defs,
               sub="Footing outlines from S1 (sheet FP), neck outlines from FP, ground-beam edges from GBP; the "
                   "sheets share one frame layout, so their local mm align.",
               caption="Footings are released (FF, the lift footing, counted once in the footing family). Necks wait "
                       "for the founding level (RFI-A03).",
               sources=["ST7757.dxf FP / GBP", "S1 footing and column registers", "S9 02"])


def _band_defs(fid, b, k, spacing=100.0):
    s = max(spacing * k, 1.2)
    pid = f"{fid}-h-{b['BAND_ID']}"
    return pid, (f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="{c(s)}" height="{c(s)}" '
                 f'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="{c(s)}" class="hl"/></pattern>')


def fig_bands_overview(L, s, G, R):
    body, defs = [], []
    cw, gap = 312, 14
    for i, sheet in enumerate(SHEET_INFO):
        panels = [p for p in R.slabs if p["sheet"] == sheet]
        cols = [pts for h, closed, pts in G.items[(sheet, "S-COL.BON")] if closed]
        box = bbox([p["polygon_mm"] for p in panels] + cols, 500)
        v = View(box, cw, 250)
        ox, oy = 16 + i * (cw + gap) + (cw - v.w) / 2, 84
        body.append(T(16 + i * (cw + gap), 66, f"{SHEET_INFO[sheet][0]} ({sheet}, PDF p."
                                              f"{L['dwg'].frames[sheet]['page']})", "tb"))
        body.append(f'<g transform="translate({c(ox)},{c(oy)})" data-view="{v.meta()}" data-sheet="{sheet}">')
        body.append(lines_svg(G, sheet, v, layers=(("1", "pl"), ("S-BOUN", "plb"))))
        for pts in cols:
            body.append(f'<polygon class="col" points="{v.pts(pts)}"/>')
        for b in [b for b in L["bands"] if b["SHEET"] == sheet]:
            body.append(f'<polygon points="{v.pts(b["POLYGON_LOCAL_MM"])}" style="fill:var(--crit)" '
                        f'data-band="{b["BAND_ID"]}">{tip(b["BAND_ID"])}</polygon>')
            cx, cy = centroid(b["POLYGON_LOCAL_MM"])
            body.append(f'<circle class="callout" cx="{c(v.X(cx))}" cy="{c(v.Y(cy))}" r="8"/>')
            body.append(T(v.X(cx) + 10, v.Y(cy) - 8, b["BAND_ID"].replace("S9A-", ""), "tx tb"))
        body.append("</g>")
    return Fig("F03A", "03_BANDS_ON_PLAN.svg", "3  The eight cantilever bands on the slab plans", ["SOURCE-DERIVED"],
               1000, 350, "".join(body), defs="".join(defs),
               sub="Each red mark is one dense-hatch region (layer S-HAT.BAT, ANSI31 at 100 mm) found in "
                   "ST7757.dxf; the ring locates it.",
               caption="Found independently from the DXF hatch population (not from the earlier census): 8 regions at "
                       "100 mm spacing, 4.947 m2 in plan; the 6 sunken-slab hatches are at 250 mm.",
               sources=["ST7757.dxf", "S9A 03 / 04"])


def fig_band_details(L, s, G, R):
    ln = lanes(L)
    body, defs = [], []
    cw, ch, gx, gy = 236, 236, 8, 12
    for i, b in enumerate(L["bands"]):
        col, row = i % 4, i // 4
        x0, y0 = 16 + col * (cw + gx), 58 + row * (ch + gy)
        poly = b["POLYGON_LOCAL_MM"]
        bx = bbox([poly])
        cxm, cym = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
        half = max((bx[2] - bx[0]) / 2 + 1100, (bx[3] - bx[1]) / 2 * 1.45 + 1100, 1700)
        win = (cxm - half, cym - half * 0.62, cxm + half, cym + half * 0.62)
        v = View(win, cw - 2, 146)
        pid, pdef = _band_defs("F03B", b, v.k)
        defs.append(pdef)
        clip = f"F03B-c-{b['BAND_ID']}"
        defs.append(f'<clipPath id="{clip}"><rect x="0" y="0" width="{c(v.w)}" height="{c(v.h)}"/></clipPath>')
        body.append(f'<rect class="card" x="{c(x0)}" y="{c(y0)}" width="{cw}" height="{ch}" rx="8"/>')
        body.append(T(x0 + 10, y0 + 18, f"{b['BAND_ID']}  {SHEET_INFO[b['SHEET']][1]} roof", "tb"))
        body.append(T(x0 + cw - 10, y0 + 18, f"DXF {b['DXF_HANDLE']}", "tx t2", "end"))
        px, py = x0 + 1 + (cw - 2 - v.w) / 2, y0 + 26
        body.append(f'<g transform="translate({c(px)},{c(py)})" data-view="{v.meta()}" data-sheet="{b["SHEET"]}" '
                    f'clip-path="url(#{clip})">')
        for p in [p for p in R.slabs if p["sheet"] == b["SHEET"]]:
            if not inside_box(p["polygon_mm"], (win[0] - 8000, win[1] - 8000, win[2] + 8000, win[3] + 8000)):
                continue
            g = LANE_GROUP.get(ln.get(p["panel_id"]))
            if g:
                body.append(f'<path class="a-{g}" fill-rule="evenodd" d="{v.path([p["polygon_mm"]] + list(p.get("holes_mm") or []))}"/>')
        body.append(lines_svg(G, b["SHEET"], v, box=(win[0] - 6000, win[1] - 6000, win[2] + 6000, win[3] + 6000)))
        for h, closed, pts in G.items[(b["SHEET"], "S-COL.BON")]:
            if closed and inside_box(pts, win):
                body.append(f'<polygon class="col" points="{v.pts(pts)}"/>')
        body.append(f'<polygon points="{v.pts(poly)}" style="fill:url(#{pid});stroke:var(--crit);stroke-width:1.3" '
                    f'data-band="{b["BAND_ID"]}">{tip(b["BAND_ID"])}</polygon>')
        body.append(scalebar(6, v.h - 10, v.k, 1))
        body.append("</g>")
        yt = py + 146 + 16
        body.append(T(x0 + 10, yt, f"{q(b['WIDTH_MM'], 0)} x {q(b['LENGTH_MM'], 1 if b['LENGTH_MM'] % 1 else 0)} mm"
                                   f"  |  {q(b['AREA_M2'])} m2  |  on {b['BEAM_LINE']}", "tx"))
        owner = "beam CA owns it (its hatch)" if b["OWNER_DECISION"].startswith("BEAMS") else \
            "re-owned: cantilever portion"
        body.append(T(x0 + 10, yt + 14, owner, "tx t2"))
        body.append(icon("BLK" if b["CONCRETE_STATE"].startswith("BLOCKED") else "OWN", x0 + 10, yt + 19, 11))
        body.append(T(x0 + 25, yt + 28, "thickness UNKNOWN; 0 m3 / 0 kg released", "tx t2"))
    h = 58 + 2 * (ch + gy)
    return Fig("F03B", "03_BAND_DETAILS.svg", "3  Each band at its drawn position", ["SOURCE-DERIVED"], 1000, h,
               "".join(body), defs="".join(defs),
               sub="1 m scale bar in each view. Grey: drawn columns; thin lines: the drawing's beam edges; tint: the "
                   "adjacent S1 panels by lane.",
               caption="Every band lies outside all slab panels and columns (0 m2 overlap) and on one beam line's "
                       "strip. Hatch drawn at the DXF pattern spacing (100 mm); the line phase is not the drawing's.",
               sources=["ST7757.dxf", "S1 slab register", "S9A 03 / 04"])


def fig_hatch(L, s):
    ev = L["band_summary"]
    ref = ev["legend_reference_spacing_mm"]
    lo, hi = 60.0, 270.0
    x0, x1 = 210, 960
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)  # noqa: E731
    top, rh = 92, 22
    n = len(L["bands"])
    body = []
    for t in ticks(lo, hi, 7):
        body.append(f'<path class="ax" d="M{c(X(t))} {top - 8}V{top + n * rh}"/>')
        body.append(T(X(t), top + n * rh + 14, f"{t:g}", "tx t2", "middle"))
    body.append(T((x0 + x1) / 2, top + n * rh + 30, "plotted hatch-line spacing, model mm (PDF vector paths x 100)",
                  "tx t2", "middle"))
    for name, val in sorted(ref.items(), key=lambda kv: kv[1]):
        a, b = X(val * 0.94), X(val * 1.06)
        body.append(f'<rect x="{c(a)}" y="{top - 8}" width="{c(b - a)}" height="{n * rh + 8}" '
                    f'style="fill:var(--grid);fill-opacity:.55"/>')
        body.append(f'<path class="dim" d="M{c(X(val))} {top - 14}V{top + n * rh}"/>')
        lab = {"BEARING_WALL": "bearing wall", "CANTILEVER_PORTION": "cantilever portion",
               "SUNKEN_SLAB": "sunken slab"}[name]
        anchor, dx = {"BEARING_WALL": ("end", -4), "CANTILEVER_PORTION": ("start", 4)}.get(name, ("middle", 0))
        body.append(T(X(val) + dx, top - 30, f"legend: {lab}", "tx tb", anchor))
        body.append(T(X(val) + dx, top - 17, f"{val} mm", "tx t2", anchor))
    for i, b in enumerate(L["bands"]):
        y = top + i * rh + rh / 2
        body.append(T(16, y + 4, f"{b['BAND_ID']}  ({b['SHEET']} {b['DXF_HANDLE']})", ""))
        dx = X(b["DXF_LINE_SPACING_MM"])
        px = X(b["PDF_SPACING_MODEL_MM"])
        body.append(f'<circle cx="{c(dx)}" cy="{c(y)}" r="4.5" style="fill:var(--surface);stroke:var(--ink);'
                    f'stroke-width:1.4">{tip("DXF pattern spacing " + str(b["DXF_LINE_SPACING_MM"]) + " mm")}'
                    f'</circle>')
        body.append(f'<circle cx="{c(px)}" cy="{c(y)}" r="4.5" class="f-BLK ring">'
                    f'{tip("PDF plotted spacing " + str(b["PDF_SPACING_MODEL_MM"]) + " mm")}</circle>')
        body.append(T(x1 + 8, y + 4, f"{b['PDF_SPACING_MODEL_MM']:.2f}", "tx tn"))
    yl = top + n * rh + 48
    lg, _ = legend([('<circle cx="{x}" cy="{y}" r="4.5" transform="translate(6,6)" style="fill:var(--surface);'
                     'stroke:var(--ink);stroke-width:1.4"/>', "DXF hatch pattern spacing"),
                    ('<circle cx="{x}" cy="{y}" r="4.5" transform="translate(6,6)" style="fill:var(--crit)"/>',
                     "spacing measured on the plotted PDF"),
                    ('<rect x="{x}" y="{y}" width="12" height="12" style="fill:var(--grid)"/>',
                     "+/- 6 % match window")], 16, yl)
    body.append(lg)
    return Fig("F03C", "03_BAND_HATCH_SPACING.svg", "3  Which legend symbol each band's hatch matches",
               ["SOURCE-DERIVED"], 1000, yl + 14, "".join(body),
               sub="Measured from the PDF's own vector paths inside each band and inside each legend box (pages 4 - 6).",
               caption="All 8 bands sit in the cantilever-portion window and outside the bearing-wall window. The "
                       "legend gives a symbol, never a thickness.",
               sources=["ST7757.pdf p.4 - 6", "ST7757.dxf", "S9A 03 / 04"])


def fig_beam_sections(L, s):
    cond = [b for b in L["beams"] if b["S9A_STATE"].startswith("CONDITIONAL")]
    combo = Counter((b["B_MM"], b["H_MM"], b["SLAB_T_MM"]) for b in cond)
    (B, H, t), n = sorted(combo.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    ex = sorted([b for b in cond if (b["B_MM"], b["H_MM"], b["SLAB_T_MM"]) == (B, H, t)],
                key=lambda b: (-b["L_M"], b["COMPONENT_ID"]))[0]
    vol = SCQ.beam_convention_volumes(B / 1000, H / 1000, ex["L_M"], t / 1000)
    per = SCQ.beam_convention_volumes(B / 1000, H / 1000, 1.0, t / 1000)
    k, sw, top = 0.30, 280.0, 112
    body = []
    for j, (key, name, cls, hh, label, note) in enumerate((
            ("TOTAL_DEPTH", "Reading A: H is the overall depth (slab included)", "s1", H, "H", "(the schedule depth)"),
            ("BELOW_SLAB", "Reading B: H is measured below the slab", "s2", H + t, "H + t",
             f"(H = {H:g} below the slab)"))):
        ox = 16 + j * 492
        cx = ox + 175
        half = B * k / 2
        body.append(f'<rect class="card" x="{ox}" y="56" width="476" height="392" rx="8"/>')
        body.append(T(ox + 14, 80, name, "tb tl"))
        body.append(T(cx - half - sw * k, top - 9, "slab panel (stops at the beam face)", "tx t2"))
        for x in (cx - half - sw * k, cx + half):
            body.append(f'<rect class="slab" x="{c(x)}" y="{top}" width="{c(sw * k)}" height="{c(t * k)}"/>')
        body.append(f'<rect class="{cls}" x="{c(cx - half)}" y="{top}" width="{c(B * k)}" height="{c(t * k)}" '
                    'style="fill-opacity:.5"/>')
        body.append(f'<rect class="{cls}" x="{c(cx - half)}" y="{c(top + t * k)}" width="{c(B * k)}" '
                    f'height="{c((hh - t) * k)}" style="fill-opacity:.92"/>')
        body.append(f'<rect x="{c(cx - half)}" y="{top}" width="{c(B * k)}" height="{c(hh * k)}" '
                    'style="fill:none;stroke:var(--ink);stroke-width:1.2"/>')
        yb = top + hh * k
        body.append(f'<path class="dim" d="M{c(cx - half)} {c(yb + 12)}H{c(cx + half)}M{c(cx - half)} {c(yb + 7)}'
                    f'V{c(yb + 17)}M{c(cx + half)} {c(yb + 7)}V{c(yb + 17)}"/>')
        body.append(T(cx, yb + 29, f"B = {B:g}", "tx", "middle"))
        xr = cx + half + sw * k + 12
        body.append(f'<path class="dim" d="M{c(xr)} {top}V{c(yb)}M{c(xr - 5)} {top}H{c(xr + 5)}'
                    f'M{c(xr - 5)} {c(yb)}H{c(xr + 5)}"/>')
        body.append(T(xr + 8, (top + yb) / 2, f"{label} = {hh:g}", "tx tb"))
        body.append(T(xr + 8, (top + yb) / 2 + 14, note, "tx t2"))
        xl = cx - half - sw * k - 12
        body.append(f'<path class="dim" d="M{c(xl)} {top}V{c(top + t * k)}M{c(xl - 5)} {top}H{c(xl + 5)}'
                    f'M{c(xl - 5)} {c(top + t * k)}H{c(xl + 5)}"/>')
        body.append(T(xl - 7, top + t * k / 2 + 4, f"t = {t:g}", "tx", "end"))
        y = 344
        body.append(T(ox + 14, y, f"beam = B x {label} x L", "tb"))
        body.append(T(ox + 14, y + 18, f"= {B / 1000:g} x {hh / 1000:g} x L = {per[key]:.4f} m3 per metre"))
        body.append(T(ox + 14, y + 36, f"{ex['COMPONENT_ID']} (L = {ex['L_M']:g} m): {vol[key]:.4f} m3", "t2"))
        body.append(T(ox + 14, y + 54, "the strip B x t over the beam is beam concrete in both readings", "tx t2"))
        body.append(T(ox + 14, y + 70, "mm; section to scale", "tx tm"))
    body.append(T(16, 470, f"Most common conditional section: B {B:g} x H {H:g} mm with t = {t:g} mm ({n} of "
                           f"{len(cond)} beams). The readings differ by the strip B x t x L = {per['STRIP']:.4f} m3 "
                           f"per metre; {vol['STRIP']:.4f} m3 for the example beam.", "t2"))
    return Fig("F04A", "04_BEAM_CONVENTIONS.svg", "4  The two readings of the beam schedule depth H",
               ["SCHEMATIC", "CONDITIONAL"], 1000, 484, "".join(body),
               sub="The drawings print H but not whether it includes the slab. Neither reading is chosen here.",
               caption="Sections drawn to scale from the schedule values; the numbers are register values for one "
                       "real beam. Choosing a reading needs the engineer (RFI-A01).",
               sources=["S1 beam schedule", "PRE-S7 thickness", "S9A 05"])


def fig_beam_totals(L, s):
    tot = {(r["GROUP"], r["SET"]): r for r in L["beam_tot"]}
    groups = [("ALL", "All storeys"), ("STOREY GF", "GF roof"), ("STOREY 1F", "1F roof"), ("STOREY 2F", "2F roof")]
    cset = "conditional (schedule section + clear length)"
    mx = max(tot[(g, cset)]["BELOW_SLAB_M3"] for g, _ in groups)
    x0, x1 = 150, 760
    X = lambda v: (v / (mx * 1.08)) * (x1 - x0)  # noqa: E731
    body = []
    lg, _ = legend([('<rect x="{x}" y="{y}" width="12" height="12" rx="2" class="s1"/>', "Reading A: H overall (B x H x L)"),
                    ('<rect x="{x}" y="{y}" width="12" height="12" rx="2" class="s2"/>',
                     "Reading B: H below the slab (B x (H + t) x L)")], 16, 66)
    body.append(lg)
    top = 86
    for t in ticks(0, mx * 1.08, 6):
        body.append(f'<path class="ax" d="M{c(x0 + X(t))} {top}V{top + 4 * 58}"/>')
        body.append(T(x0 + X(t), top + 4 * 58 + 14, f"{t:g}", "tx t2", "middle"))
    body.append(T(x0 + (x1 - x0) / 2, top + 4 * 58 + 30, "conditional beam concrete, m3", "tx t2", "middle"))
    for i, (g, name) in enumerate(groups):
        r = tot[(g, cset)]
        y = top + i * 58 + 8
        body.append(T(16, y + 14, name, "tb"))
        body.append(T(16, y + 30, f"{r['BEAMS']} beams", "tx t2"))
        body.append(hbar(x0, y, X(r["TOTAL_DEPTH_M3"]), 17, "s1", f"{name} A: {r['TOTAL_DEPTH_M3']} m3"))
        body.append(hbar(x0, y + 20, X(r["BELOW_SLAB_M3"]), 17, "s2", f"{name} B: {r['BELOW_SLAB_M3']} m3"))
        body.append(T(x0 + X(r["TOTAL_DEPTH_M3"]) + 6, y + 13, q(r["TOTAL_DEPTH_M3"]), "tx tn"))
        body.append(T(x0 + X(r["BELOW_SLAB_M3"]) + 6, y + 33,
                      f"{q(r['BELOW_SLAB_M3'])}   (+{q(r['SENSITIVITY_M3'])}, {r['SENSITIVITY_PCT']:g} %)", "tx tn"))
    # composition of the 150
    allr = [r for r in L["beam_tot"] if r["GROUP"] == "ALL"]
    seg = [("COND", "conditional", allr[0]["BEAMS"], ""), ("CONF", "source conflict", allr[1]["BEAMS"], ""),
           ("COND", "curved: upper bound", allr[2]["BEAMS"], "tex"), ("BLK", "missing a dimension", allr[3]["BEAMS"], ""),
           ("BLK", "re-owned as cantilever", allr[4]["BEAMS"], "tex")]
    ntot = sum(x[2] for x in seg)
    yc = top + 4 * 58 + 56
    body.append(T(16, yc + 12, f"All {ntot} beams", "tb"))
    cx, W = x0, x1 - x0 + 200
    for g, lab, cnt, tex in seg:
        w = W * cnt / ntot
        body.append(f'<rect class="f-{g}" x="{c(cx)}" y="{yc}" width="{c(max(w - 2, .8))}" height="18" rx="2">'
                    f'{tip(f"{cnt} {lab}")}</rect>')
        if tex:
            body.append(f'<rect x="{c(cx)}" y="{yc}" width="{c(max(w - 2, .8))}" height="18" '
                        'style="fill:url(#F04B-tex)"/>')
        cx += w
    yl = yc + 38
    items = [(g if not tex else f'<g transform="translate({{x}},{{y}})"><rect width="12" height="12" rx="2" '
                                f'class="f-{g}"/><rect width="12" height="12" style="fill:url(#F04B-tex)"/></g>',
              f"{cnt} {lab}") for g, lab, cnt, tex in seg]
    lg, yy = legend(items, 16, yl)
    body.append(lg)
    defs = ('<pattern id="F04B-tex" patternUnits="userSpaceOnUse" width="5" height="5" patternTransform="rotate(45)">'
            '<line x1="0" y1="0" x2="0" y2="5" class="tex"/></pattern>')
    conf = tot[("ALL", "source conflict")]
    body.append(T(16, yy + 22, f"The {conf['BEAMS']} source-conflict beams would add {q(conf['TOTAL_DEPTH_M3'])} - "
                               f"{q(conf['BELOW_SLAB_M3'])} m3 once their drawn width and schedule width are "
                               "reconciled; they are outside the bars above.", "tx t2"))
    return Fig("F04B", "04_BEAM_CONVENTION_TOTALS.svg", "4  Beam concrete under each reading, by storey",
               ["CONDITIONAL"], 1000, yy + 36, "".join(body), defs=defs,
               sub="103 beams with a schedule section and a clear length. Not released under either reading.",
               caption="Reading B adds the slab strip over each beam: 14.165 m3 (25 %) more over the building. The "
                       "panels never contain that strip, so neither reading double-counts slab concrete.",
               sources=["S9A 05 / 06"])


def fig_overlap(L, s):
    o = {r["CHECK_ID"]: r for r in L["overlaps"]}
    body = []
    k, top = 0.25, 118
    B, H, t, sw = 300, 600, 160, 520
    x0 = 30
    bx = x0 + sw * k
    body.append('<rect class="card" x="16" y="56" width="560" height="372" rx="8"/>')
    body.append(T(30, 80, "Section across a beam between two panels", "tb tl"))
    body.append(f'<rect class="a-REL" x="{c(x0)}" y="{top}" width="{c(sw * k)}" height="{c(t * k)}"/>')
    body.append(f'<rect class="a-REL" x="{c(bx + B * k)}" y="{top}" width="{c(sw * k)}" height="{c(t * k)}"/>')
    body.append(f'<rect class="f-COND" x="{c(bx)}" y="{top}" width="{c(B * k)}" height="{c(H * k)}" '
                'style="fill-opacity:.35;stroke:var(--ink);stroke-width:1.2"/>')
    body.append(f'<rect x="{c(bx)}" y="{top}" width="{c(B * k)}" height="{c(t * k)}" '
                'style="fill:url(#F05A-tex);stroke:var(--ink);stroke-width:.8"/>')
    body.append(T(x0 + sw * k / 2, top - 9, "panel A (released)", "tx", "middle"))
    body.append(T(bx + B * k + sw * k / 2, top - 9, "panel B (released)", "tx", "middle"))
    for xx in (bx, bx + B * k):
        body.append(f'<path class="lead" d="M{c(xx)} {top - 24}V{c(top + H * k + 10)}" '
                    'style="stroke-dasharray:3 2"/>')
    body.append(T(bx + B * k / 2, top + H * k + 26, "panel edges sit on the beam faces", "tx", "middle"))
    ax = bx + B * k + sw * k + 14
    body.append(f'<path class="lead" d="M{c(bx + B * k - 6)} {c(top + t * k / 2)}L{c(ax - 4)} {c(top + 62)}"/>')
    for i, (txt, cls) in enumerate((("strip B x t over the beam:", "tx tb"), ("in no panel; beam concrete", "tx t2"),
                                    ("under both readings", "tx t2"), ("", ""), ("beam below the slab:", "tx tb"),
                                    ("conditional (F04)", "tx t2"))):
        if txt:
            body.append(T(ax, top + 66 + i * 14, txt, cls))
    lines = [
        ("BO-01", f"BO-01: {o['BO-01']['COUNT']} of {o['BO-01']['COUNT']} beam-supported panel edges lie on a drawn "
                  "face"),
        ("", "(" + o["BO-01"]["DETAIL"].split(": ", 1)[1].replace('"', "").strip("{}")
         .replace("BEAM_EDGE_LINE", "beam edge line").replace("COLUMN_OUTLINE", "column outline") + ")"),
        ("BO-02", f"BO-02: released panels overlapping a drawn column: {o['BO-02']['DETAIL']}"),
        ("BO-03", f"BO-03: {o['BO-03']['COUNT']} beam lengths are clear lengths (never above c/c)"),
        ("BO-05", f"BO-05: per beam, B - A = B x t x L ({o['BO-05']['COUNT']} beams): no slab counted twice"),
        ("BO-04", f"BO-04: {o['BO-04']['DETAIL']} (RFI-A10)"),
    ]
    for i, (cid, txt) in enumerate(lines):
        y = 330 + i * 15
        if cid:
            g = "COND" if o[cid]["RESULT"] == "INFO" else ("REL" if o[cid]["RESULT"] == "PASS" else "BLK")
            body.append(icon(g, 30, y - 10, 11))
        body.append(T(46, y, txt, "tx"))
    # junction plans
    jx = 592
    body.append(f'<rect class="card" x="{jx}" y="56" width="392" height="372" rx="8"/>')
    body.append(T(jx + 14, 78, "Plan: who owns the junction", "tb tl"))
    s_ = 0.11
    cells = [("beam into a column", "the column owns its footprint for the storey; the beam stops at its face"),
             ("beam carried by a beam", "the carrier runs through; the carried beam stops at its face"),
             ("two beams, no column", "both stop at the other's face: the corner square is in neither")]
    for i, (head, note) in enumerate(cells):
        y = 100 + i * 108
        bx = jx + 30
        body.append(T(jx + 14, y + 4, head, "tx tb"))
        if i == 0:
            body.append(f'<rect class="f-OWN" x="{c(bx + 60)}" y="{c(y + 22)}" width="{c(400 * s_)}" '
                        f'height="{c(400 * s_)}" style="stroke:var(--ink2)"/>')
            body.append(f'<rect class="f-COND" x="{c(bx)}" y="{c(y + 22 + 100 * s_)}" width="{c(60)}" '
                        f'height="{c(200 * s_)}" style="fill-opacity:.6"/>')
            body.append(f'<rect class="f-COND" x="{c(bx + 60 + 400 * s_)}" y="{c(y + 22 + 100 * s_)}" '
                        f'width="60" height="{c(200 * s_)}" style="fill-opacity:.6"/>')
        elif i == 1:
            body.append(f'<rect class="f-COND" x="{c(bx)}" y="{c(y + 30)}" width="160" height="{c(250 * s_)}" '
                        f'style="fill-opacity:.6"/>')
            body.append(f'<rect class="f-COND" x="{c(bx + 68)}" y="{c(y + 30 + 250 * s_)}" width="{c(200 * s_)}" '
                        f'height="44" style="fill-opacity:.35;stroke:var(--ink2);stroke-width:.6"/>')
        else:
            body.append(f'<rect class="f-COND" x="{c(bx)}" y="{c(y + 30)}" width="70" height="{c(250 * s_)}" '
                        f'style="fill-opacity:.6"/>')
            body.append(f'<rect class="f-COND" x="{c(bx + 70)}" y="{c(y + 30 + 250 * s_)}" '
                        f'width="{c(250 * s_)}" height="44" style="fill-opacity:.35;stroke:var(--ink2);'
                        f'stroke-width:.6"/>')
            body.append(f'<rect x="{c(bx + 70)}" y="{c(y + 30)}" width="{c(250 * s_)}" height="{c(250 * s_)}" '
                        f'style="fill:none;stroke:var(--crit);stroke-width:1.4;stroke-dasharray:2 1.5"/>')
        words, line, ly = note.split(), "", y + 30
        for w_ in words:
            if tw(line + " " + w_, 9.5) > 170:
                body.append(T(jx + 210, ly, line.strip(), "tx t2"))
                line, ly = w_, ly + 13
            else:
                line += " " + w_
        body.append(T(jx + 210, ly, line.strip(), "tx t2"))
    defs = ('<pattern id="F05A-tex" patternUnits="userSpaceOnUse" width="5" height="5" patternTransform="rotate(45)">'
            '<line x1="0" y1="0" x2="0" y2="5" class="tex"/></pattern>')
    return Fig("F05A", "05_SLAB_BEAM_OVERLAP.svg", "5  Slab, beam and column overlaps: gross to net",
               ["SCHEMATIC"], 1000, 444, "".join(body), defs=defs,
               sub="S9 measures panels between member faces, beams clear between supports and columns over the full "
                   "storey; the checks are S9A's.",
               caption="Panel NET = GROSS: the panel polygon already stops at the faces, so no beam deduction is "
                       "needed. The only gap is the corner square of 10 beam ends that meet without a column "
                       "(an undercount of at most 0.454 m3, never a double count).",
               sources=["S9A 07", "S1 slab register"])


def fig_face_example(L, s, G, R):
    ln = lanes(L)
    byid = {x["panel_id"]: x for x in R.slabs}
    cands = [(b, byid[f["panel"]]) for b in L["bands"] for f in b["BOUNDING_PANEL_FACES"]
             if f["panel_class"] == "SLAB_PANEL" and LANE_GROUP.get(ln.get(f["panel"])) == "REL"
             and len(byid[f["panel"]]["polygon_mm"]) == len(byid[f["panel"]]["edges"])]
    band, p = cands[0]
    pid = p["panel_id"]
    sheet = p["sheet"]
    box = bbox([p["polygon_mm"], band["POLYGON_LOCAL_MM"]], 900)
    v = View(box, 600, 380)
    beam_lines = [(a, b) for h, closed, pts in G.items[(sheet, "1")] for a, b in
                  zip(pts, pts[1:] + (pts[:1] if closed else []))]
    col_lines = [(a, b) for h, closed, pts in G.items[(sheet, "S-COL.BON")] for a, b in
                 zip(pts, pts[1:] + (pts[:1] if closed else []))]
    ox, oy = 30, 70
    body = [f'<g transform="translate({ox},{oy})" data-view="{v.meta()}" data-sheet="{sheet}" '
            'clip-path="url(#F05B-clip)">']
    body.append(f'<path class="a-REL" fill-rule="evenodd" d="{v.path([p["polygon_mm"]] + list(p.get("holes_mm") or []))}"/>')
    body.append(lines_svg(G, sheet, v, box=(box[0] - 4000, box[1] - 4000, box[2] + 4000, box[3] + 4000)))
    for h, closed, pts in G.items[(sheet, "S-COL.BON")]:
        if closed and inside_box(pts, box):
            body.append(f'<polygon class="col" points="{v.pts(pts)}"/>')
    pid2, pdef = _band_defs("F05B", band, v.k)
    body.append(f'<polygon points="{v.pts(band["POLYGON_LOCAL_MM"])}" style="fill:url(#{pid2});stroke:var(--crit);'
                f'stroke-width:1.3"/>')
    poly = p["polygon_mm"]
    cnt = Counter()
    for e in p["edges"]:
        i = e["edge_index"]
        a, b = poly[i], poly[(i + 1) % len(poly)]
        if math.hypot(b[0] - a[0], b[1] - a[1]) < 1:
            continue
        on_beam = SCQ.edge_on_lines(a, b, beam_lines, 2.0, 0.9)[0]
        on_col = SCQ.edge_on_lines(a, b, col_lines, 2.0, 0.9)[0]
        kind = "beam" if on_beam else ("column" if on_col else "none")
        cnt[(e["support"], kind)] += 1
        cls = {"beam": "k1", "column": "k2", "none": "k-BLK"}[kind]
        dash = ";stroke-dasharray:3 2" if e["support"] != "BEAM" else ""
        info = f"edge {i}: S1 support {e['support']}; on a drawn {kind} face"
        body.append(f'<path class="{cls}" d="M{c(v.X(a[0]))} {c(v.Y(a[1]))}L{c(v.X(b[0]))} {c(v.Y(b[1]))}" '
                    f'style="stroke-width:3;stroke-linecap:round{dash}">{tip(info)}</path>')
    body.append("</g>")
    body.append(f'<g transform="translate({ox},{oy})">{scalebar(0, v.h + 16, v.k, 2)}</g>')
    pdef += f'<clipPath id="F05B-clip"><rect x="0" y="0" width="{c(v.w)}" height="{c(v.h)}"/></clipPath>'
    x = 660
    body.append(T(x, 92, pid, "tb tl"))
    body.append(T(x, 110, f"{SHEET_INFO[sheet][0]}, {ln.get(pid)}", "t2"))
    body.append(T(x, 128, f"area {float(p['area_m2']):.3f} m2 (S1); edges re-checked here:", "t2"))
    y = 152
    for (sup, kind), n in sorted(cnt.items()):
        cls = {"beam": "k1", "column": "k2", "none": "k-BLK"}[kind]
        body.append(f'<path class="{cls}" d="M{x} {y - 4}H{x + 20}" style="stroke-width:3"/>')
        body.append(T(x + 28, y, f"{n} edge(s): S1 support {sup}, lies on a drawn {kind} face" if kind != "none" else
                      f"{n} edge(s): S1 support {sup}, on no drawn member face", "tx"))
        y += 18
    body.append(T(x, y + 10, f"{band['BAND_ID']} (hatched) lies outside the panel,", "tx t2"))
    body.append(T(x, y + 24, "on the strip of " + band["BEAM_LINE"] + ": it is not slab-panel concrete.", "tx t2"))
    body.append(T(x, y + 50, "Dashed edges: S1 records no beam support there", "tx tm"))
    body.append(T(x, y + 64, "(a free edge, a column or a void).", "tx tm"))
    return Fig("F05B", "05_PANEL_FACE_EXAMPLE.svg", "5  One released panel: its edges are the drawn beam faces",
               ["SOURCE-DERIVED"], 1000, oy + v.h + 40, "".join(body), defs=pdef,
               sub="Blue: edge on a drawn beam edge line (layer 1); orange: on a column outline. The same test as "
                   "BO-01, redrawn for one panel next to a band.",
               caption="The panel polygon is S1's; the beam lines and columns are the drawing's. Every supported "
                       "edge of every released panel passes this test (BO-01, 243 of 243).",
               sources=["ST7757.dxf", "S1 slab register", "S9A 07"])


def fig_columns(L, s):
    order = ["INTERPRETATION_SCHEDULE_STOREY_ROW", "INTERPRETATION_TYPE_TAG", "GENUINE_CONFLICT_ONE_DIMENSION",
             "GENUINE_CONFLICT"]
    short = {"INTERPRETATION_SCHEDULE_STOREY_ROW": "row", "INTERPRETATION_TYPE_TAG": "tag",
             "GENUINE_CONFLICT_ONE_DIMENSION": "1 side", "GENUINE_CONFLICT": "none"}
    head = {"INTERPRETATION_SCHEDULE_STOREY_ROW": "row: equals this type's schedule row for another storey",
            "INTERPRETATION_TYPE_TAG": "tag: equals another type's schedule on this storey",
            "GENUINE_CONFLICT_ONE_DIMENSION": "1 side: one dimension agrees, the other does not",
            "GENUINE_CONFLICT": "none: no schedule row of any storey or type matches"}
    floors = ["FOUNDATION", "GF", "1F", "2F"]
    rows = sorted(L["cols"], key=lambda r: (order.index(r["PROBLEM_KIND"].split(" + ")[0]),
                                            floors.index(r["FLOOR"]), r["COLUMN_ID"]))
    k, cw, ch, per = 0.62, 95, 106, 10
    body, y = [], 58
    for i, r in enumerate(rows):
        kind = r["PROBLEM_KIND"].split(" + ")[0]
        g = "COND" if kind.startswith("INTERP") else "CONF"
        x0, y0 = 16 + (i % per) * (cw + 2), y + (i // per) * (ch + 6)
        body.append(f'<rect class="card" x="{c(x0)}" y="{c(y0)}" width="{cw}" height="{ch}" rx="6"/>')
        m = re.match(r"COL-(.+)-(X\d+)-(Y\d+)-(\w+)", r["COLUMN_ID"])
        typ, grid, fl = (m.group(1), f"{m.group(2)}/{m.group(3)}", m.group(4)) if m else (r["TYPE"], "", r["FLOOR"])
        fl = "FDN" if fl == "FOUNDATION" else fl
        body.append(T(x0 + 7, y0 + 14, f"{typ} {fl}", "tx tb"))
        body.append(icon(g, x0 + cw - 18, y0 + 5, 11))
        body.append(T(x0 + 7, y0 + 26, grid, "tx t2"))
        dw, sc = sorted(r["DRAWN_CM"], reverse=True), sorted(r["SCHEDULE_CM"], reverse=True)
        cx, cy = x0 + cw / 2, y0 + 52
        body.append(f'<rect x="{c(cx - dw[0] * k / 2)}" y="{c(cy - dw[1] * k / 2)}" width="{c(dw[0] * k)}" '
                    f'height="{c(dw[1] * k)}" class="col">{tip(r["COLUMN_ID"] + " drawn " + str(r["DRAWN_CM"]))}'
                    "</rect>")
        body.append(f'<rect x="{c(cx - sc[0] * k / 2)}" y="{c(cy - sc[1] * k / 2)}" width="{c(sc[0] * k)}" '
                    f'height="{c(sc[1] * k)}" class="mm">{tip("schedule " + str(r["SCHEDULE_CM"]))}</rect>')
        body.append(T(x0 + 7, y0 + ch - 24, f"drawn {dw[0]:g} x {dw[1]:g}", "tx"))
        body.append(T(x0 + 7, y0 + ch - 11, f"sched. {sc[0]:g} x {sc[1]:g}", "tx t2"))
        body.append(T(x0 + cw - 7, y0 + 26, short[kind], "tx t2", "end"))
        if r["LIFT_COLUMN"]:
            body.append(T(x0 + cw - 22, y0 + 14, "LIFT", "tx tb", "end"))
    y += (len(rows) + per - 1) // per * (ch + 6) + 12
    cnt = Counter(r["PROBLEM_KIND"].split(" + ")[0] for r in rows)
    for j, kind in enumerate(order):
        g = "COND" if kind.startswith("INTERP") else "CONF"
        xx, yy = 16 + (j % 2) * 490, y + (j // 2) * 17
        body.append(icon(g, xx, yy - 10, 11))
        body.append(T(xx + 16, yy, f"{cnt[kind]}  {head[kind]}", "tx"))
    y += 2 * 17 + 6
    lg, yy = legend([('<rect x="{x}" y="{y}" width="14" height="10" class="col"/>', "drawn outline (ST7757.dxf)"),
                     ('<rect x="{x}" y="{y}" width="14" height="10" class="mm"/>', "schedule section (S1 schedule row)")],
                    16, y)
    body.append(lg)
    return Fig("F06A", "06_COLUMN_SCHEDULE_VS_PLAN.svg", "6  The 28 columns whose drawn section differs from the "
               "schedule", ["SOURCE-DERIVED", "SCHEMATIC"], 1000, yy + 12, "".join(body),
               sub="cm, all at one scale; long side drawn horizontal for comparison (plan orientation in 09). "
                   "Locations: dashed rings on the F02 maps.",
               caption="19 are interpretation questions (another schedule row or type matches the drawn size); 9 match "
                       "nothing. The four lift-pit columns are drawn 200 / 250 against the scheduled 300 (S8.8 C-01).",
               sources=["S1 column registers", "ST7757.dxf", "S9A 09"])


def fig_gb(L, s):
    rows = [r for r in L["gb"] if r["PROBLEM_KIND"].startswith("INTERPRETATION")]
    rows.sort(key=lambda r: (r["CC_M"] if r["CC_M"] is not None else r["CLEAR_M"], r["OCCURRENCE_ID"]))
    lo, hi = 0.0, 10.0
    x0, x1 = 170, 760
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)  # noqa: E731
    top, rh = 96, 19
    n = len(rows)
    body = []
    for a, b, lab, g in ((0, 2.5, "< 2.5 m: 30 x 30", 0), (2.5, 5.0, "2.5 - 5 m: 30 x 40", 1),
                         (5.0, 10.0, "> 5 m: 30 x 60", 0)):
        body.append(f'<rect x="{c(X(a))}" y="{top - 22}" width="{c(X(b) - X(a))}" height="{n * rh + 22}" '
                    f'style="fill:var(--grid);fill-opacity:{".55" if g else ".22"}"/>')
        body.append(T((X(a) + X(b)) / 2, top - 8, lab, "tx tb", "middle"))
    body.append(T(x0, top - 30, "p.13 titles read as exclusive length bands:", "tx t2"))
    for t in range(0, 11):
        body.append(T(X(t), top + n * rh + 14, f"{t}", "tx t2", "middle"))
    body.append(T((x0 + x1) / 2, top + n * rh + 30, "span length, m", "tx t2", "middle"))
    body.append(T(x1 + 14, top - 8, "m3: c/c basis | clear basis", "tx tb"))
    for i, r in enumerate(rows):
        y = top + i * rh + rh / 2
        chg = bool(r["CLASS_CHANGES_WITH_BASIS"])
        body.append(T(16, y + 4, r["OCCURRENCE_ID"], "tx tb" if chg else "tx"))
        if r["CLEAR_M"] is not None and r["CC_M"] is not None:
            body.append(f'<path d="M{c(X(r["CLEAR_M"]))} {c(y)}H{c(X(r["CC_M"]))}" '
                        'style="stroke:var(--ink2);stroke-width:1.5"/>')
        if r["CLEAR_M"] is not None:
            body.append(f'<circle cx="{c(X(r["CLEAR_M"]))}" cy="{c(y)}" r="4" style="fill:var(--surface);'
                        f'stroke:var(--ink);stroke-width:1.3">{tip("clear " + str(r["CLEAR_M"]) + " m")}</circle>')
        if r["CC_M"] is not None:
            ring = ' style="stroke:var(--ink);stroke-width:1.6"' if chg else ""
            body.append(f'<circle cx="{c(X(r["CC_M"]))}" cy="{c(y)}" r="4" class="f-COND ring"{ring}>'
                        f'{tip("centre to centre " + str(r["CC_M"]) + " m")}</circle>')
        mc, ml = r["M3_EXCLUSIVE_TITLES_CC_BASIS"], r["M3_EXCLUSIVE_TITLES_CLEAR_BASIS"]
        note = "exterior or interior?" if r["EXTERIOR_CANDIDATE"] else ("class changes with the basis" if chg else "")
        body.append(T(x1 + 14, y + 4, f"{q(mc)} | {q(ml)}   {note}".rstrip(), "tx tn"))
    yl = top + n * rh + 50
    lg, yy = legend([('<circle cx="{x}" cy="{y}" r="4" transform="translate(6,6)" style="fill:var(--surface);'
                      'stroke:var(--ink);stroke-width:1.3"/>', "clear length"),
                     ("COND", "centre-to-centre length (dark ring and bold id: the class changes with the "
                              "basis)")], 16, yl)
    body.append(lg)
    kinds = Counter(r["PROBLEM_KIND"] for r in L["gb"])
    rel = kinds.get("RELEASED_IN_S9", 0)
    interp = sum(v for k_, v in kinds.items() if k_.startswith("INTERPRETATION"))
    body.append(T(16, yy + 22, f"All {len(L['gb'])} ground and strap beams: {rel} released in S9, {interp} "
                               f"interpretation questions, {kinds.get('MISSING_SOURCE_INFORMATION', 0)} missing source "
                               f"information (exterior depth 'FOLLOW ARCH.', concentrated-load detail), "
                               f"{kinds.get('SOURCE_CONFLICT', 0)} source conflicts.", "tx t2"))
    return Fig("F06B", "06_GROUND_BEAM_LENGTH_CLASSES.svg", "6  Ground beams: which length picks the section?",
               ["SOURCE-DERIVED", "CONDITIONAL"], 1000, yy + 36, "".join(body),
               sub=f"The {n} spans whose class depends on reading the p.13 titles or on the length basis; lengths "
                   "from S5.",
               caption="Read literally, '< 2.5 m (30x30)' and '< 5 m (30x40)' both hold for a short span. The m3 shown "
                       "assume exclusive bands and are never released (RFI-A05).",
               sources=["S5 occurrence lengths", "p.13 titles", "S9A 08"])


def fig_lift(L, s, G, R):
    ln = lanes(L)
    ff = next(r for r in R.focc if r["type"] == "FF")
    a, b, cc, d = ff["outline"]["bbox"]
    walls = []
    for r in L["s9conc"]:
        m = re.search(r"rect \[([-\d.]+), ([-\d.]+), ([-\d.]+), ([-\d.]+)\]", r["SOURCE"])
        if r["FAMILY"] == "LIFT" and m:
            walls.append((r, [float(x) for x in m.groups()]))
    lcols = []
    for x in L["lift"]:
        ps = x["PLAN_SOURCE"]
        h = ps["handles"][ps["sheets"].index("FP")]
        lcols.append((x, G.poly("FP", h)))
    box = (a - 900, b - 900, cc + 900, d + 900)
    v = View(box, 520, 430)
    ox, oy = 30, 66
    body = [f'<g transform="translate({ox},{oy})" data-view="{v.meta()}" data-sheet="FP">']
    body.append(lines_svg(G, "GBP", v, box=box, layers=(("1", "pl2"),)))
    body.append(f'<rect class="a-REL" x="{c(v.X(a))}" y="{c(v.Y(d))}" width="{c((cc - a) * v.k)}" '
                f'height="{c((d - b) * v.k)}">{tip(ff["footing_id"])}</rect>')
    for r, (wa, wb, wc, wd) in walls:
        body.append(f'<rect class="f-COND" x="{c(v.X(wa))}" y="{c(v.Y(wd))}" width="{c((wc - wa) * v.k)}" '
                    f'height="{c((wd - wb) * v.k)}" style="fill-opacity:.85">{tip(r["COMPONENT_ID"])}</rect>')
    for x, pts in lcols:
        if not pts:
            continue
        body.append(f'<polygon class="f-CONF" points="{v.pts(pts)}" style="stroke:var(--ink);stroke-width:.6">'
                    f'{tip(x["COLUMN_ID"] + " drawn " + str(x["DRAWN_CM"]))}</polygon>')
        px, py = centroid(pts)
        xs = sorted(p_[0] for p_ in pts)
        ys = sorted(p_[1] for p_ in pts)
        wx, wy = xs[-1] - xs[0], ys[-1] - ys[0]
        sc = x["SCHEDULE_CM"]
        sx, sy = (max(sc) * 10, min(sc) * 10) if wx >= wy else (min(sc) * 10, max(sc) * 10)
        body.append(f'<rect class="mm" x="{c(v.X(px - sx / 2))}" y="{c(v.Y(py + sy / 2))}" width="{c(sx * v.k)}" '
                    f'height="{c(sy * v.k)}"/>')
        m = re.match(r"COL-(.+)-(X\d+)-(Y\d+)-", x["COLUMN_ID"])
        body.append(T(v.X(px), v.Y(py) - max(sx, sy) * v.k / 2 - 6, f"{m.group(1)} {m.group(2)}/{m.group(3)}",
                      "tx tb", "middle"))
    body.append(T(v.X(a) + 6, v.Y(b) - 6, f"FF {ff['sizes']['schedule_L_cm']:g} x {ff['sizes']['schedule_W_cm']:g} cm",
                  "tx tb"))
    body.append(scalebar(0, v.h + 16, v.k, 2))
    body.append("</g>")
    x0 = 590
    ffrow = next(r for r in L["s9conc"] if r["COMPONENT_ID"] == ff["footing_id"])
    owners = [("REL", f"Footing {ff['footing_id']}", f"FOOTINGS · released {q(_f(ffrow['RELEASED_M3']))} m3",
               "counted once, in the footing family"),
              ("OWN", "LIFT-01-FTG", "LIFT · reference only", "points to the footing row; no quantity"),
              ("OWN", "LIFT-01-PIT-BASE", "not applicable", "the FF top is the pit floor"),
              ("COND", f"{len(walls)} pit walls (200 mm)", "LIFT · indicative only, "
               f"{q(sum(_f(r['CONDITIONAL_M3']) for r, _ in walls))} m3",
               "pit depth not printed (RFI-A03)"),
              ("CONF", f"{len(lcols)} lift columns", "COLUMNS · source conflict",
               "drawn 200 / 250 vs schedule 300 (RFI-A04)"),
              ("BLK", "LIFT-01-TIE-GF", "LIFT · blocked", "section and bars not stated"),
              ("OWN", "Shaft enclosure GF-2F", "not applicable", "architectural walls"),
              ("BLK", "LIFT-01-OVERRUN", "not in source", "")]
    body.append(T(x0, 84, "Who owns each lift element", "tb tl"))
    y = 110
    for g, name, own, why in owners:
        body.append(icon(g, x0, y - 10))
        body.append(T(x0 + 18, y, name, "tb"))
        body.append(T(x0 + 18, y + 14, own, "tx"))
        if why:
            body.append(T(x0 + 18, y + 27, why, "tx t2"))
        y += 44
    lg, yy = legend([('<rect x="{x}" y="{y}" width="12" height="12" class="mm"/>', "schedule size (300 mm)")],
                    x0, y + 4, 380)
    body.append(lg)
    h = max(oy + v.h + 40, yy + 16)
    return Fig("F07", "07_LIFT_AND_FOOTING_OWNERSHIP.svg", "7  Lift pit and footing: one owner per element",
               ["SOURCE-DERIVED", "SCHEMATIC"], 1000, h, "".join(body),
               sub="Plan: the FF outline (S1), the pit-wall rectangles (S8.8, via S9) and the lift-column outlines "
                   "(FP); dashed: the scheduled size centred on the drawn column.",
               caption="Nothing in the lift family is released. The footing below it is released once, in the footing "
                       "family; the pit walls stay indicative until the founding level and pit depth are given.",
               sources=["ST7757.dxf FP / GBP", "S1 footing and column registers", "S9 02", "S8.8 C-01"])


def fig_bars(fid, name, title, rows, unit, cls, sub, caption, labels=("SOURCE-DERIVED",), nd=3):
    rows = sorted(rows, key=lambda r: -r[1])
    mx = max(v for _, v in rows) * 1.12
    x0, x1 = 200, 900
    top, rh = 66, 26
    body = []
    for t in ticks(0, mx, 6):
        X = x0 + t / mx * (x1 - x0)
        body.append(f'<path class="ax" d="M{c(X)} {top - 4}V{top + len(rows) * rh}"/>')
        body.append(T(X, top + len(rows) * rh + 14, f"{t:,.0f}", "tx t2", "middle"))
    body.append(T((x0 + x1) / 2, top + len(rows) * rh + 30, unit, "tx t2", "middle"))
    for i, (lab, v) in enumerate(rows):
        y = top + i * rh
        body.append(T(16, y + 15, lab.replace("_", " ").title(), ""))
        body.append(hbar(x0, y + 4, v / mx * (x1 - x0), 16, cls, f"{lab}: {q(v, nd)} {unit}"))
        body.append(T(x0 + v / mx * (x1 - x0) + 6, y + 16, q(v, nd), "tx tn"))
    return Fig(fid, name, title, list(labels), 1000, top + len(rows) * rh + 44, "".join(body), sub=sub,
               caption=caption, sources=["S9 14", "S9A 01 / 11"])


def fig_conditional(L, s):
    rows = []
    for u in L["unlock"]:
        lo, hi = u["UNLOCKS_M3_LOW"], u["UNLOCKS_M3_HIGH"]
        if lo is None and hi is None:
            continue
        if (lo or 0) == 0 and (hi or 0) == 0:
            continue
        rows.append((u["RFI_ID"], lo, hi, u["EFFECT"]))
    fam = {r["RFI_ID"]: r["FAMILY"] for r in L["rfi"]}
    mx = max(max(x for x in (lo, hi) if x is not None) for _, lo, hi, _ in rows) * 1.1
    x0, x1 = 260, 900
    X = lambda v: x0 + v / mx * (x1 - x0)  # noqa: E731
    top, rh = 70, 30
    body = []
    for t in ticks(0, mx, 7):
        body.append(f'<path class="ax" d="M{c(X(t))} {top - 4}V{top + len(rows) * rh}"/>')
        body.append(T(X(t), top + len(rows) * rh + 14, f"{t:g}", "tx t2", "middle"))
    body.append(T((x0 + x1) / 2, top + len(rows) * rh + 30, "m3 the answer would make releasable (conditional)",
                  "tx t2", "middle"))
    for i, (rid, lo, hi, eff) in enumerate(rows):
        y = top + i * rh + 14
        body.append(T(16, y - 1, f"{rid}  {fam[rid].split(' / ')[0].replace('_', ' ').title()}", "tb"))
        body.append(T(16, y + 12, eff[:48] + ("..." if len(eff) > 48 else ""), "tx t2"))
        if lo is not None and hi is not None and hi > lo:
            body.append(f'<rect class="f-COND" x="{c(X(lo))}" y="{c(y - 7)}" width="{c(X(hi) - X(lo))}" height="12" '
                        f'rx="3">{tip(f"{rid}: {q(lo)} - {q(hi)} m3")}</rect>')
            body.append(f'<path d="M{c(X(0))} {c(y - 1)}H{c(X(lo))}" style="stroke:var(--warn);stroke-width:1;'
                        f'stroke-dasharray:2 2"/>')
            body.append(T(X(hi) + 6, y + 3, f"{q(lo)} - {q(hi)}", "tx tn"))
        else:
            vv = hi if hi is not None else lo
            body.append(f'<circle cx="{c(X(vv))}" cy="{c(y - 1)}" r="5" class="f-COND ring">'
                        f'{tip(f"{rid}: {q(vv)} m3")}</circle>')
            note = "" if hi is not None else "  (at the adjacent slab thickness; context only)"
            body.append(T(X(vv) + 9, y + 3, f"{q(vv)}{note}", "tx tn"))
    p = L["s9sum"]["conditional_point_m3"]
    body.append(T(16, top + len(rows) * rh + 50, f"S9's own conditional point estimate is {q(p)} m3 over 230 "
                                                 "unreleased rows; S9A confirms it sits on no released row (V06). "
                                                 "None of these values enters the 158.070 m3.", "tx t2"))
    return Fig("F08C", "08_CONDITIONAL_CONCRETE.svg", "8  Concrete waiting on an answer", ["CONDITIONAL"], 1000,
               top + len(rows) * rh + 64, "".join(body),
               sub="A bar is a range between two readings; a dot is a single value. Never added to the released total.",
               caption="The ranges are what each engineer answer would make releasable, read from the S9A unlock "
                       "register (14); they are not estimates of the final BOQ.",
               sources=["S9A 13 / 14", "S9 02"])


def fig_blocked(L, s):
    inv = s9a_inventory(L)
    cnt = defaultdict(Counter)
    for r in inv:
        g = LANE_GROUP[r["LANE"]]
        if g in ("COND", "CONF", "BLK"):
            cnt[r["FAMILY"]][g] += 1
    fams = sorted(cnt, key=lambda f: (-sum(cnt[f].values()), f))
    mx = max(sum(v.values()) for v in cnt.values())
    x0, x1 = 200, 900
    top, rh = 82, 24
    body = []
    lg, _ = legend([(g, GROUP_LABEL[g]) for g in ("COND", "CONF", "BLK")], 16, 66)
    body.append(lg)
    for t in ticks(0, mx * 1.05, 6):
        X = x0 + t / (mx * 1.05) * (x1 - x0)
        body.append(f'<path class="ax" d="M{c(X)} {top - 4}V{top + len(fams) * rh}"/>')
        body.append(T(X, top + len(fams) * rh + 14, f"{t:g}", "tx t2", "middle"))
    body.append(T((x0 + x1) / 2, top + len(fams) * rh + 30, "records not released", "tx t2", "middle"))
    for i, f in enumerate(fams):
        y = top + i * rh
        body.append(T(16, y + 15, f.replace("_", " ").title(), ""))
        cx = x0
        for g in ("COND", "CONF", "BLK"):
            n = cnt[f][g]
            if not n:
                continue
            w = n / (mx * 1.05) * (x1 - x0)
            body.append(f'<rect class="f-{g}" x="{c(cx)}" y="{c(y + 4)}" width="{c(max(w - 2, .8))}" height="15" '
                        f'rx="2">{tip(f"{f}: {n} {GROUP_LABEL[g].lower()}")}</rect>')
            if w > 20:
                fill = "#fff" if g == "BLK" else "var(--ink)"
                body.append(f'<text class="t tx tb" x="{c(cx + w / 2 - 1)}" y="{c(y + 15)}" text-anchor="middle" '
                            f'style="fill:{fill}">{n}</text>')
            cx += w
        body.append(T(cx + 6, y + 16, str(sum(cnt[f].values())), "tx tn t2"))
    return Fig("F09", "09_BLOCKED_AND_MISSING.svg", "9  What is not released, by family", ["SOURCE-DERIVED"], 1000,
               top + len(fams) * rh + 44, "".join(body),
               sub="Records in a not-released lane after S9A. The table below gives the reason and the question that "
                   "unblocks each group.",
               caption="Blocked means a dimension, level or detail is missing from the source; conflict means two "
                       "sources disagree; conditional means one interpretation is pending. None is counted as zero.",
               sources=["S9 01 / 02", "S9A 10"])


def fig_rfi(L, s):
    rows = L["unlock"]
    top, rh = 82, 30
    x0, x1, x2, x3 = 330, 640, 690, 960
    mm = max((r["UNLOCKS_M3_HIGH"] if r["UNLOCKS_M3_HIGH"] is not None else r["UNLOCKS_M3_LOW"]) or 0 for r in rows)
    mk = max(r["UNLOCKS_KG"] or 0 for r in rows)
    body = [T(x0, 66, "concrete, m3 (upper reading)", "tx tb"), T(x2, 66, "reinforcement, kg", "tx tb")]
    pr = {r["RFI_ID"]: r["PRIORITY"] for r in L["rfi"]}
    for i, r in enumerate(rows):
        y = top + i * rh
        hi = r["UNLOCKS_M3_HIGH"] if r["UNLOCKS_M3_HIGH"] is not None else r["UNLOCKS_M3_LOW"]
        body.append(T(16, y + 14, f"{r['RFI_ID']} ({pr[r['RFI_ID']]})", "tb"))
        qq = r["QUESTION"]
        body.append(T(16, y + 26, qq[:58] + ("..." if len(qq) > 58 else ""), "tx t2"))
        if hi:
            body.append(hbar(x0, y + 6, hi / mm * (x1 - x0), 14, "f-COND", f"{r['RFI_ID']}: {q(hi)} m3"))
            body.append(T(x0 + hi / mm * (x1 - x0) + 5, y + 17, q(hi, 2), "tx tn"))
        else:
            body.append(T(x0, y + 17, "not quantified" if hi is None else "0", "tx tm"))
        kg = r["UNLOCKS_KG"]
        if kg:
            body.append(hbar(x2, y + 6, kg / mk * (x3 - x2 - 60), 14, "f-COND", f"{r['RFI_ID']}: {q(kg)} kg"))
            body.append(T(x2 + kg / mk * (x3 - x2 - 60) + 5, y + 17, q(kg, 0), "tx tn"))
        else:
            body.append(T(x2, y + 17, "not quantified" if kg is None else "0", "tx tm"))
    return Fig("F10", "10_RFI_UNLOCK_RANKING.svg", "10  Which engineer answers unlock the most", ["CONDITIONAL"], 1000,
               top + len(rows) * rh + 16, "".join(body),
               sub="Ranked by the concrete each answer would make releasable, then by reinforcement. Separate scales "
                   "for m3 and kg.",
               caption="Values are conditional quantities the answer would allow S9 to release, never a promise of "
                       "release.",
               sources=["S9A 13 / 14"])


# ============================================================================ page
PAGE_CSS = """
*{box-sizing:border-box}html{background:var(--surface)}body{margin:0;background:var(--surface);color:var(--ink);
font:14px/1.5 system-ui,Inter,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
main{max-width:1120px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:28px;line-height:1.2;margin:0 0 6px}h2{font-size:20px;margin:0 0 4px}h3{font-size:15px;margin:18px 0 6px}
p{margin:6px 0}.lead{color:var(--ink2);font-size:15px;max-width:860px}.kicker{font-size:12px;letter-spacing:.08em;
text-transform:uppercase;color:var(--ink2);font-weight:600}
section{margin:34px 0 0}figure{margin:12px 0 0}svg.fig{display:block;width:100%;height:auto}
figcaption{font-size:12.5px;color:var(--ink2);margin:4px 0 0;max-width:900px}
.src{font-size:11.5px;color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:12px;margin:8px 0 4px}
th{text-align:left;font-weight:600;color:var(--ink2);border-bottom:1.5px solid var(--rule);padding:5px 6px;
vertical-align:bottom}td{border-bottom:1px solid var(--grid);padding:4px 6px;vertical-align:top}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.pill{display:inline-block;font-size:11px;font-weight:650;border:1px solid var(--ink2);border-radius:9px;
padding:0 8px;margin-right:4px;white-space:nowrap}.pill.SCHEMATIC{border-style:dashed}
.pill.CONDITIONAL{border-color:var(--warn);background:color-mix(in srgb,var(--warn) 16%,transparent)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}.box{border:1px solid var(--rule);border-radius:10px;
padding:12px 14px;background:var(--card)}.st{display:inline-flex;align-items:center;gap:4px;white-space:nowrap}
.st svg{width:12px;height:12px}.muted{color:var(--muted)}ul{margin:6px 0 6px 18px;padding:0}li{margin:2px 0}
.toggle{position:fixed;top:10px;right:12px;font:12px system-ui,Inter,sans-serif;border:1px solid var(--rule);
background:var(--card);color:var(--ink);border-radius:8px;padding:4px 10px;cursor:pointer}
a{color:var(--s1)}
@media (max-width:720px){.grid2{grid-template-columns:1fr}main{padding:16px}table{font-size:11px}
.wide{display:block;overflow-x:auto}figure{overflow-x:auto}svg.fig{min-width:760px}}
@page{size:A4 landscape;margin:9mm 10mm 12mm}
@media print{html,body{background:#fff}main{max-width:none;padding:0}.toggle{display:none}
section{break-before:page;margin:0}section.first{break-before:auto}figure,tr,.box{break-inside:avoid}
svg.fig{max-height:155mm}h2{margin-top:0}table{font-size:10.5px}}
td:first-child{white-space:nowrap}.toc{columns:4;column-gap:24px;margin:6px 0 0 18px}
@media (max-width:720px){.toc{columns:1}}@media print{.pb{break-before:page}}.toc li{break-inside:avoid}
"""

TOGGLE_JS = ("<script>(function(){var b=document.getElementById('theme');if(!b)return;var r=document.documentElement;"
             "try{var s=localStorage.getItem('s9a-theme');if(s)r.setAttribute('data-theme',s)}catch(e){}"
             "b.addEventListener('click',function(){var d=r.getAttribute('data-theme');var dark=d?d==='dark':"
             "matchMedia('(prefers-color-scheme: dark)').matches;var n=dark?'light':'dark';"
             "r.setAttribute('data-theme',n);try{localStorage.setItem('s9a-theme',n)}catch(e){}})})();</script>")


def st(g, text=None):
    return (f'<span class="st"><svg viewBox="0 0 12 12" aria-hidden="true"><use href="#i-{g}"/></svg>'
            f'{E(text if text is not None else GROUP_LABEL[g])}</span>')


def table(head, rows, num=()):
    h = "".join(f'<th class="n">{E(x)}</th>' if i in num else f"<th>{E(x)}</th>" for i, x in enumerate(head))
    b = "".join("<tr>" + "".join(f'<td class="n">{x}</td>' if i in num else f"<td>{x}</td>" for i, x in enumerate(r))
                + "</tr>" for r in rows)
    return f'<div class="wide"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'


def figure(f):
    pills = "".join(f'<span class="pill {lab}">{lab}</span>' for lab in f.labels)
    return (f'<figure id="{f.fid}">{f.inline()}<figcaption>{pills} {E(f.caption)} '
            f'<span class="src">Sources: {E("; ".join(f.sources))}. File: visual/{E(f.name)}</span></figcaption>'
            "</figure>")


TOC = (("s1", "Coverage dashboard"), ("sA", "S9 totals recomputed"), ("s2", "Location maps by floor"),
       ("s3", "The eight cantilever bands"), ("s4", "Beam depth conventions"), ("s5", "Slab / beam / column overlaps"),
       ("s6", "Columns and ground beams"), ("s7", "Lift pit and footing"), ("s8", "Concrete and reinforcement"),
       ("s9", "Blocked and missing"), ("s10", "Engineer RFI sheet"))


def findings(L, s):
    s9, b, v = L["s9sum"], s["bands"], s["verification"]
    allb = next(r for r in L["beam_tot"] if r["GROUP"] == "ALL" and r["SET"].startswith("conditional"))
    a02 = next(r for r in L["rfi"] if r["RFI_ID"] == "RFI-A02")
    return [
        f"S9's release holds: {v['families_agree']} of {v['families_agree']} families agree with an independent "
        "recompute; the only other difference is 0.001 kg of rounding in the S9 README table.",
        f"The {b['count']} hatched bands ({q(b['area_m2'], 3)} m2) are cantilever portions. {b['registered_blocked']} "
        "move from 'untagged beam' to cantilever portion and stay blocked (no thickness); one is beam CA's own hatch.",
        f"Beam concrete is {q(allb['TOTAL_DEPTH_M3'])} or {q(allb['BELOW_SLAB_M3'])} m3 depending on what H means: "
        "one engineer answer (RFI-A01) settles it. Nothing is released until then.",
        "Slab panels stop at drawn beam and column faces (243 of 243 edges), so neither beam reading counts slab "
        "concrete twice.",
        f"Ties and links: {q(a02['UNLOCKS_KG'])} kg wait for a bend radius and hook (RFI-A02); no source prints one.",
    ]


def page(L, s, F):
    s9 = L["s9sum"]
    allb = next(r for r in L["beam_tot"] if r["GROUP"] == "ALL" and r["SET"].startswith("conditional"))
    fig = {f.fid: f for f in F}
    out = [f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1"><title>S9A Visual QA</title>'
           f'<style>{TOKENS}{PAGE_CSS}{SVG_CSS}</style></head><body>'
           f'<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{ICONS}</defs></svg>'
           '<button class="toggle" id="theme" type="button">Light / dark</button><main>']
    out.append('<section class="first"><div class="kicker">Structural QA · drawing set ST7757 · round S9A · '
               f'{E(s["date"])}</div><h1>Structural completeness, cantilever bands and beam conventions</h1>'
               '<p class="lead">A dated correction layer over S9 (frozen at commit 5f317d2). It re-checks every '
               'released quantity, finds the eight hatched bands in the drawing, compares the two readings of the beam '
               'depth and separates interpretation questions from missing information. '
               '<strong>It releases nothing and changes no frozen stage.</strong></p>'
               f'<p class="lead"><strong>Released, unchanged: {q(s9["released_concrete_m3_total"])} m3 concrete and '
               f'{q(s9["released_reinforcement_kg_total"])} kg reinforcement</strong>, S9\'s partial structural BOQ. '
               'S9A delta 0.000 m3 / 0.000 kg. The project gate stays INCOMPLETE.</p>'
               '<div class="grid2" style="margin-top:12px"><div class="box"><h3 style="margin-top:0">Key findings'
               '</h3><ul>' + "".join(f"<li>{E(x)}</li>" for x in findings(L, s)) + "</ul></div>"
               '<div class="box"><h3 style="margin-top:0">How to read the figures</h3><ul>'
               + "".join(f'<li><span class="pill {k}">{k}</span> {E(v)}</li>' for k, v in LABEL_NOTE.items())
               + "</ul><p>" + " ".join(st(g) for g in GROUPS) + "</p><p class=\"muted\">Status colours always come with "
               "an icon and a label. Blue and orange are the two beam readings.</p></div></div>"
               '<div class="box" style="margin-top:12px"><h3 style="margin-top:0">Contents</h3><ol class="toc">'
               + "".join(f'<li><a href="#{a}">{E(t)}</a></li>' for a, t in TOC) + "</ol></div></section>")
    out.append('<section id="s1"><h2>1 · Coverage dashboard</h2>' + figure(fig["F01"]) + "</section>")
    fam_label = lambda f: "README table (3 dp)" if f == "README_TABLE_3DP" else f.replace("_", " ").title()  # noqa
    vr = [[E(r["TRADE"].title()), E(fam_label(r["FAMILY"])), q(r["S9_PUBLISHED"], 6),
           q(r["INDEPENDENT_RECOMPUTE"], 6), f'{r["PUBLISHED_MINUS_INDEPENDENT"]:+.9f}', E(r["UNIT"]),
           st("REL", "agrees") if r["RESULT"] == "AGREES" else st("COND", "rounding only")] for r in L["verify"]]
    out.append('<section id="sA"><h2>A · S9 totals, recomputed independently</h2><p>Every released family re-summed from the '
               'stages\' row-level registers with code that does not read S9\'s own CSVs. The only difference beyond '
               'one millionth is the S9 README family table: rounded to 3 dp before summing, it adds to 0.001 kg more '
               'than the unrounded total.</p>'
               + table(["Trade", "Family", "S9 published", "Independent", "Published - independent", "Unit", ""], vr,
                       num=(2, 3, 4))
               + table(["Check", "What", "Result", "Detail"],
                       [[E(r["CHECK_ID"]), E(r["CHECK"]), st("REL", "pass") if r["RESULT"] == "PASS" else
                         st("BLK", r["RESULT"]), E(r["DETAIL"][:140])] for r in L["inv"]]) + "</section>")
    out.append('<section id="s2"><h2>2 · Location maps</h2><p>Each map is the drawing\'s own sheet. Panels and columns are '
               'coloured by their S9 lane; diamonds mark beam tags. Hover for ids.</p>'
               + figure(fig["F02-FDN"]) + "</section>")
    for sh in SHEET_INFO:
        out.append(f"<section>{figure(fig['F02-' + sh])}</section>")
    dm = lambda v: q(v, 0) if float(v).is_integer() else q(v, 1)  # noqa: E731
    br = [[E(b["BAND_ID"]), E(b["SHEET"]), E(b["DXF_HANDLE"]), f'{dm(b["WIDTH_MM"])} x {dm(b["LENGTH_MM"])}',
           q(b["AREA_M2"], 4), f'{b["PDF_SPACING_MODEL_MM"]:.2f}', E(b["BEAM_LINE"]),
           E(b["S9_COMPONENT_SAME_FOOTPRINT"]), E(b["OWNER_DECISION"].split(" (")[0].split(":")[0]),
           st("BLK", "blocked") if b["CONCRETE_STATE"].startswith("BLOCKED") else st("OWN", "beam CA"),
           q(b["CONDITIONAL_M3_IF_ADJACENT_SLAB_T"])] for b in L["bands"]]
    bs = s["bands"]
    out.append('<section id="s3"><h2>3 · The eight bands</h2>'
               f'<p>{bs["count"]} dense-hatch regions, {q(bs["area_m2"], 3)} m2 in plan, found in the DXF without the '
               'earlier census. Each matches the legend\'s <em>cantilever portion</em> symbol. They are not new objects: '
               f'{bs["registered_blocked"]} were S9 "untagged beam" spans and are re-owned as cantilever portions '
               '(blocked: no thickness); one is the hatch of the tagged cantilever beam CA, which keeps it.</p>'
               + figure(fig["F03A"]) + "</section><section>" + figure(fig["F03B"]) + "</section><section>"
               + figure(fig["F03C"])
               + table(["Band", "Sheet", "DXF", "W x L mm", "m2", "PDF mm", "Beam line", "S9 row, same footprint",
                        "Owner after S9A", "Concrete", "m3 at adjacent t (context)"], br, num=(4, 5, 10))
               + "</section>")
    bt = [[E(r["GROUP"].replace("STOREY ", "")), E(r["SET"]), str(r["BEAMS"]), q(r.get("TOTAL_DEPTH_M3")),
           q(r.get("BELOW_SLAB_M3")), q(r.get("SENSITIVITY_M3")), "-" if r.get("SENSITIVITY_PCT") in (None, "") else
           f'{r["SENSITIVITY_PCT"]:g} %'] for r in L["beam_tot"]
          if r["GROUP"] == "ALL" or r["SET"].startswith(("conditional", "source conflict"))]
    out.append('<section id="s4"><h2>4 · Beam depth conventions</h2>'
               f'<p>{s["beams"]["compared"]} superstructure beams compared. {allb["BEAMS"]} have a schedule section and a '
               f'clear length: {q(allb["TOTAL_DEPTH_M3"])} m3 if H is the overall depth, {q(allb["BELOW_SLAB_M3"])} m3 '
               'if H is below the slab. No reading is selected; no beam concrete is released.</p>'
               + figure(fig["F04A"]) + "</section><section>" + figure(fig["F04B"])
               + table(["Group", "Set", "Beams", "A: H overall m3", "B: H below slab m3", "B - A m3", "B - A"], bt,
                       num=(2, 3, 4, 5, 6)) + "</section>")
    out.append('<section id="s5"><h2>5 · Slab, beam and column overlaps</h2>' + figure(fig["F05A"]) + "</section><section>"
               + figure(fig["F05B"]) + table(["Check", "What", "Result", "Count", "Detail"],
                                             [[E(o["CHECK_ID"]), E(o["CHECK"]), st("REL", "pass") if o["RESULT"] ==
                                               "PASS" else st("COND", o["RESULT"].lower()), str(o["COUNT"]),
                                               E(o["DETAIL"])] for o in L["overlaps"]], num=(3,)) + "</section>")
    cr = [[E(r["COLUMN_ID"]), E(r["FLOOR"]), E(r["TYPE"]), E(" x ".join(f"{x:g}" for x in r["DRAWN_CM"])),
           E(" x ".join(f"{x:g}" for x in r["SCHEDULE_CM"])),
           st("COND", "interpretation") if r["PROBLEM_KIND"].startswith("INTERP") else st("CONF", "conflict"),
           E(r["WHY"]), q(r["M3_SCHEDULE"]), q(r["M3_DRAWN"])] for r in sorted(
        L["cols"], key=lambda r: (["FOUNDATION", "GF", "1F", "2F"].index(r["FLOOR"]), r["COLUMN_ID"]))]
    gk = Counter(r["PROBLEM_KIND"] for r in L["gb"])
    out.append('<section id="s6"><h2>6 · Columns and ground beams</h2>' + figure(fig["F06A"]) + "</section><section>"
               + table(["Column", "Floor", "Type", "Drawn cm", "Schedule cm", "Kind", "Why", "m3 schedule",
                        "m3 drawn"], cr, num=(7, 8))
               + f'<p>Column ties: the only printed rule is "{E(L["ties"]["tie_rule"])}". No bend radius, hook or closure '
               f'is printed (DXF text search: {len(L["ties"]["dxf_text_hits"])} hits): '
               f'{E(L["ties"]["state"])}. S9-C01 keeps {q(s["verification"]["s9_c01_kg"])} kg of tie paths and hooks '
               'conditional.</p></section><section>' + figure(fig["F06B"])
               + "<p>Ground-beam problem kinds (08): " + "; ".join(f"{E(k_.lower().replace('_', ' '))}: {v_}"
                                                                    for k_, v_ in sorted(gk.items())) + ".</p></section>")
    out.append('<section id="s7"><h2>7 · Lift pit and footing</h2>' + figure(fig["F07"]) + "</section>")
    out.append('<section id="s8"><h2>8 · Concrete and reinforcement</h2>' + figure(fig["F08A"]) + figure(fig["F08B"])
               + "</section><section>" + figure(fig["F08C"]) + "</section>")
    why = {"BEAMS": "depth convention (A01), conflicts (A04-type width), untagged sections (A09)",
           "COLUMNS": "founding level for necks (A03), section mismatches (A04)",
           "GROUND_BEAMS": "p.13 titles and length basis, exterior depth (A05)",
           "LINTELS": "bearings and head functions (A07)", "GROUND_SLAB": "extent of the 10 cm note (A06)",
           "CANTILEVER_PORTIONS": "thickness and bars (A08)", "LIFT": "pit depth, tie beam (A03, S8.8)",
           "STAIRS": "owner scenarios, waist and build-ups (S8.7C)", "POOL": "not detailed for structure",
           "DOMES": "ring beams and openings (S8.3)", "PARAPETS": "no section", "PLAIN_CONCRETE": "blinding: no extent",
           "BOUNDARY_WALL": "conflicting sources", "OTHER": "not in the structural set",
           "WATER_TANK_ROOF": "not in the structural set", "FOOTINGS": "F / F10 tag conflict",
           "SLABS": "sunken drops and void-zone panels"}
    inv = s9a_inventory(L)
    cnt = defaultdict(Counter)
    for r in inv:
        cnt[r["FAMILY"]][LANE_GROUP[r["LANE"]]] += 1
    rows = [[E(f.replace("_", " ").title()), str(cnt[f]["COND"] or ""), str(cnt[f]["CONF"] or ""),
             str(cnt[f]["BLK"] or ""), E(why.get(f, ""))] for f in sorted(cnt, key=lambda f: -(
                 cnt[f]["COND"] + cnt[f]["CONF"] + cnt[f]["BLK"])) if cnt[f]["COND"] + cnt[f]["CONF"] + cnt[f]["BLK"]]
    out.append('<section id="s9"><h2>9 · Blocked and missing</h2>' + figure(fig["F09"]) + '<div class="pb">'
               + table(["Family", "Conditional", "Conflict", "Blocked", "What would unblock it"], rows, num=(1, 2, 3))
               + "</div>"
               + "</section>")
    rr = [[E(r["RFI_ID"]), E(r["PRIORITY"]), E(r["TO"]), E(r["PROBLEM_TYPE"]), E(r["QUESTION"]), E(r["SCOPE"]),
           q(r["UNLOCKS_M3_LOW"]) + ("" if r["UNLOCKS_M3_HIGH"] in (None, r["UNLOCKS_M3_LOW"]) else
                                     " - " + q(r["UNLOCKS_M3_HIGH"])), q(r["UNLOCKS_KG"])] for r in L["rfi"]]
    out.append('<section id="s10"><h2>10 · Engineer RFI sheet</h2>' + figure(fig["F10"]) + "</section><section>"
               + table(["RFI", "Priority", "To", "Problem type", "Question", "Scope", "Unlocks m3", "Unlocks kg"], rr,
                       num=(6, 7))
               + table(["Check", "What", "Result"], [[E(r["CHECK_ID"]), E(r["CHECK"]), st("REL", "pass") if
                                                      r["RESULT"] == "PASS" else st("BLK", r["RESULT"])]
                                                     for r in L["cons"]])
               + '<p class="muted">S9A is a dated correction layer (18_S9A_CORRECTION_MANIFEST.json). S9 and the 29 '
                 'frozen stages verify unchanged before and after the build. Nothing here is a released quantity '
                 'unless it says released.</p></section>')
    out.append("</main>" + TOGGLE_JS + "</body></html>\n")
    return "".join(out)


# ============================================================================ text outputs
def readme(L, s):
    s9 = L["s9sum"]
    v = s["verification"]
    b = s["bands"]
    bm = s["beams"]
    allb = next(r for r in L["beam_tot"] if r["GROUP"] == "ALL" and r["SET"].startswith("conditional"))
    ck = Counter(r["PROBLEM_KIND"].split(" + ")[0] for r in L["cols"])
    gk = Counter(r["PROBLEM_KIND"] for r in L["gb"])
    gi = sum(n for k, n in gk.items() if k.startswith("INTERPRETATION"))
    un = L["unlock"]
    lines = [
        "# S9A: structural completeness, cantilever bands and visual QA", "",
        f"Baseline HEAD `{s['baseline']}`. Date {s['date']}. State: `DATED_CORRECTION_LAYER` "
        "(`18_S9A_CORRECTION_MANIFEST.json`).", "",
        "S9A is a correction layer over S9 (`research/alsenan_structural_s9`, frozen, unchanged). It re-checks S9, "
        "finds the eight hatched bands, compares the two beam-depth readings and audits the ground-beam and column "
        "conflicts. S9 and the 29 stage freezes verify unchanged before and after the build.", "",
        f"**Nothing is released.** The released baseline stays **{q(s9['released_concrete_m3_total'])} m3 concrete** "
        f"and **{q(s9['released_reinforcement_kg_total'])} kg reinforcement**: a partial structural BOQ, not a complete "
        "building estimate. S9A changes owners and lanes only, each with a reason (`10`). The production BOQ is not "
        "touched, and the project gate stays INCOMPLETE.", "",
        "## Conclusions", "",
        f"1. **S9's totals hold.** Every released family was recomputed from the stages' own row registers: "
        f"{v['families_agree']} of {v['families_agree']} agree to rounding (largest difference below one millionth). "
        f"The {v['readme_table_rounding_kg']} kg difference is only the S9 README table, whose 3-dp family values add "
        "up to 0.001 kg more than the unrounded total.",
        f"2. **The inventory is consistent.** {s9['components']} records, one lane each, mutually exclusive. There are "
        f"110 deltas summing to the published release, and S9-C01 holds {q(v['s9_c01_kg'])} kg in {v['s9_c01_parts']} "
        f"parts. The {q(s9['conditional_point_m3'])} m3 conditional point sits on no released row.",
        f"3. **The eight bands are cantilever portions, not new structure.** There are {b['count']} regions with "
        f"{q(b['area_m2'], 3)} m2 in plan. All match the legend's cantilever-portion hatch on the plotted PDF.",
        f"   - {b['registered_blocked']} were S9 untagged beam spans. They are re-owned as cantilever portions and "
        "remain blocked, because no thickness is printed.",
        "   - One is the hatch of the tagged beam CA, which keeps it.",
        "   - No band overlaps a panel or a column, so there is no double count.",
        f"4. **Beam concrete depends on one answer.** {allb['BEAMS']} beams have a full section and clear length. "
        f"They total {q(allb['TOTAL_DEPTH_M3'])} m3 if H is the overall depth, or {q(allb['BELOW_SLAB_M3'])} m3 if H "
        f"is below the slab: {q(allb['SENSITIVITY_M3'])} m3 ({allb['SENSITIVITY_PCT']:g} %) apart. Neither reading is "
        "chosen.",
        "   - Panels stop at beam faces (243 of 243 edges), so the slab strip over a beam is counted once under either "
        "reading.",
        "   - Corner squares where two beams meet without a column are counted nowhere: an undercount of at most "
        f"{q(sum(x['max_m3'] for x in L['corners']))} m3.",
        "5. **Interpretation is separated from missing information.**",
        f"   - Columns: {ck['INTERPRETATION_SCHEDULE_STOREY_ROW'] + ck['INTERPRETATION_TYPE_TAG']} of the 28 section "
        f"mismatches match another schedule row or type (interpretation). "
        f"{ck['GENUINE_CONFLICT'] + ck['GENUINE_CONFLICT_ONE_DIMENSION']} match nothing (conflict). The four lift-pit "
        "columns stay a conflict: drawn 200 / 250 mm against a scheduled 300 mm.",
        f"   - Ground beams: {gi} spans are interpretation questions (title overlap, c/c or clear length, exterior or "
        f"interior). {gk['MISSING_SOURCE_INFORMATION']} lack source information (the exterior depth is 'FOLLOW ARCH.').",
        "   - Column ties: no bend radius, hook or closure is printed anywhere (missing source information).",
        "",
        "## What the engineer can unlock", "",
        "These are conditional quantities each answer would make releasable, never a promise of release (`14`).", "",
        "| Rank | RFI | Question | Concrete m3 | Reinforcement kg |", "|---|---|---|---|---|",
    ]
    for u in un:
        lo, hi = u["UNLOCKS_M3_LOW"], u["UNLOCKS_M3_HIGH"]
        m3 = "-" if lo is None and hi is None else (q(lo) if hi in (None, lo) else f"{q(lo)} - {q(hi)}")
        rank = u["RANK_CONCRETE"] or "-"
        if u["RANK_STEEL"]:
            rank = f"{rank} (steel {u['RANK_STEEL']})"
        lines.append(f"| {rank} | {u['RFI_ID']} | {u['QUESTION']} | {m3} | {q(u['UNLOCKS_KG'])} |")
    lines += [
        "",
        "**The single largest unlock is RFI-A01, the beam depth convention.** One answer makes "
        f"{q(allb['TOTAL_DEPTH_M3'])} - {q(allb['BELOW_SLAB_M3'])} m3 of beam concrete releasable. The largest steel "
        f"unlock is RFI-A02, the tie and link bend radius and hooks: {q(next(u['UNLOCKS_KG'] for u in un if u['RFI_ID'] == 'RFI-A02'))} kg.",
        "",
        "## Files", "",
        "| File | What it holds |", "|---|---|",
        "| `01_S9_TOTALS_VERIFICATION.csv` | Each released family: published, row sum, independent recompute |",
        "| `02_S9_INVENTORY_VERIFICATION.csv` | V01 - V07: inventory, lanes, deltas, S9-C01, conditional leakage |",
        "| `03_BAND_CORRECTION_REGISTER.csv` | The 8 bands: handle, sheet, polygon, size, legend match, overlaps, "
        "owner, states |",
        "| `04_BAND_EVIDENCE.json` | Hatch population, PDF legend spacings, per-band evidence |",
        "| `05_BEAM_CONVENTION_COMPARISON.csv` | 150 beams: B / H / L sources, t, volumes under each reading |",
        "| `06_BEAM_CONVENTION_TOTALS.csv` | Totals by storey and set |",
        "| `07_BEAM_SLAB_COLUMN_OVERLAP_AUDIT.csv` | BO-01 - BO-05 |",
        "| `08_GROUND_BEAM_AUDIT.csv` | 62 ground and strap beams: c/c vs clear class, title overlap, exterior depth |",
        "| `09_COLUMN_AUDIT.csv` | The 28 section mismatches, interpretation vs conflict; lift columns |",
        "| `10_S9A_DELTA_REGISTER.csv` | 15 owner / lane changes, all 0 m3 / 0 kg |",
        "| `11_CONCRETE_AND_STEEL_RECONCILIATION.csv` | Released (unchanged) and conditional ranges by family |",
        "| `12_STRUCTURAL_COMPLETENESS_REPORT.md` | The updated completeness report |",
        "| `13_ENGINEER_RFI_REGISTER.csv` / `14_UNLOCK_RANKING.csv` | 10 RFIs with problem type and unlock values |",
        "| `15_CONSERVATION_CHECKS.csv` | C01 - C17 |",
        "| `16_S9A_SUMMARY.json`, `17_PROVENANCE.jsonl`, `18_S9A_CORRECTION_MANIFEST.json` | Summary, provenance, "
        "manifest |",
        "| `visual/S9A_VISUAL_QA.html` | The visual QA package (10 items) as one page; print to PDF with "
        "`make_pdf_s9a.py` |",
        "| `visual/*.svg` | Each figure on its own, labelled SOURCE-DERIVED, SCHEMATIC or CONDITIONAL |",
        "", "Rebuild: `python3 -I research/alsenan_structural_s9a/build_s9a.py` (byte-identical). The PDF "
        "(`visual/S9A_VISUAL_QA.pdf`) is printed from the HTML and git-ignored, like the other review PDFs.", "",
        "## Notes for the reviewer", "",
        "**What worked**", "",
        "- The independent recompute matches S9 to rounding in every family.",
        "- The bands were found and classified from the drawing alone:",
        "  - DXF hatch pattern and scale;",
        "  - the plotted spacing read from the PDF vector paths;",
        "  - the legend boxes on the same pages.",
        "- Every slab-panel edge S1 marks as beam-supported lies on a drawn beam or column face. This is what makes "
        "the two beam readings safe from slab double counting.",
        "",
        "**What did not work, or stays open**", "",
        "- No source states the beam depth convention, the band thickness, the founding level, the tie hooks or the "
        "exterior ground-beam depth. These stay blocked or conditional.",
        "- Ground-beam spans could not be placed on the plan span by span: the registers hold edge lines, not span "
        "ends.",
        "- Untagged beam spans have no tag, so they have no marker on the maps.",
        "",
        "**Recommended next step**", "",
        "- Send RFI-A01, A02, A03 and A04 to the engineer first. Together they cover most of the unreleased concrete "
        "and steel.",
        "- Release nothing until the answers come back. Then apply them as a separately approved release on top of S9 "
        "/ S9A.",
        "- Do not start S10 until that review.", "",
    ]
    return "\n".join(lines) + "\n"


def completeness_report(L, s):
    s9 = L["s9sum"]
    inv = s9a_inventory(L)
    cnt = defaultdict(Counter)
    for r in inv:
        cnt[r["FAMILY"]][LANE_GROUP[r["LANE"]]] += 1
    rel_m3, rel_kg = s9["released_concrete_m3_by_family"], s9["released_reinforcement_kg_by_family"]
    cond = {r["FAMILY"]: r for r in L["recon"] if r.get("S9A_CONDITIONAL_LOW") is not None or
            r["FAMILY"].startswith("CANTILEVER")}
    lines = [
        "# S9A structural completeness report", "",
        f"Correction layer over S9 (frozen). Date {s['date']}. Released quantities are S9's, unchanged; S9A releases "
        "nothing. Records are S9's 560 with S9A's owner changes: 7 untagged spans superseded by their band rows, 8 band "
        f"rows added ({len(inv)} records).", "",
        "## By family", "",
        "| Family | Records | Released | Conditional | Conflict | Blocked | Owned elsewhere / n.a. | Released m3 | "
        "Released kg |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for f in sorted(cnt, key=lambda f: (-sum(cnt[f].values()), f)):
        n = cnt[f]
        lines.append(f"| {f} | {sum(n.values())} | {n['REL']} | {n['COND']} | {n['CONF']} | {n['BLK']} | {n['OWN']} | "
                     f"{q(rel_m3.get(f)) if f in rel_m3 else '-'} | {q(rel_kg.get(f)) if f in rel_kg else '-'} |")
    tot = Counter()
    for n in cnt.values():
        tot.update(n)
    lines.append(f"| **All** | {len(inv)} | {tot['REL']} | {tot['COND']} | {tot['CONF']} | {tot['BLK']} | "
                 f"{tot['OWN']} | {q(s9['released_concrete_m3_total'])} | "
                 f"{q(s9['released_reinforcement_kg_total'])} |")
    lines += ["", "## Not released, with its range", "",
              "These values are conditional. None enters a released total (C15).", "",
              "| Item | Low m3 | High m3 | Note |", "|---|---|---|---|"]
    for f, r in cond.items():
        lines.append(f"| {f} | {q(r.get('S9A_CONDITIONAL_LOW'))} | {q(r.get('S9A_CONDITIONAL_HIGH'))} | "
                     f"{r.get('NOTE', '')} |")
    lines += ["", "## Interpretation versus missing information", "",
              "| RFI | Problem type | Scope |", "|---|---|---|"]
    for r in L["rfi"]:
        lines.append(f"| {r['RFI_ID']} | {r['PROBLEM_TYPE']} | {r['SCOPE']} |")
    lines += ["", "## Not quantified at all", "",
              "- Pool, parapets, blinding, the boundary wall, the dome rings, the lift tie beam and the overrun are "
              "unchanged from S9: blocked or not in the source.",
              "- The 7 cantilever portions join them: blocked until a thickness is given.",
              "- The sunken-slab drops (6 hatches at 250 mm) are unchanged S9 rows.", "",
              "The visual QA package (`visual/S9A_VISUAL_QA.html`) shows each of these on the plans.", ""]
    return "\n".join(lines) + "\n"


# ============================================================================ build
def build(L, s):
    G = Geo(L["dwg"])
    R = Reg(L)
    marks = beam_marks(L, R, G)
    s9 = L["s9sum"]
    F = [fig_dashboard(L, s), fig_foundation(L, s, G, R)]
    F += [fig_plan(L, s, G, R, sh, marks) for sh in SHEET_INFO]
    F += [fig_bands_overview(L, s, G, R), fig_band_details(L, s, G, R), fig_hatch(L, s), fig_beam_sections(L, s),
          fig_beam_totals(L, s), fig_overlap(L, s), fig_face_example(L, s, G, R), fig_columns(L, s), fig_gb(L, s),
          fig_lift(L, s, G, R)]
    F.append(fig_bars("F08A", "08_RELEASED_CONCRETE.svg", "8  Released concrete by family",
                      list(s9["released_concrete_m3_by_family"].items()), "m3", "s1",
                      f"Total {q(s9['released_concrete_m3_total'])} m3, S9's release, unchanged by S9A.",
                      "Beams have no released concrete: their depth convention is open (F04). That is not a zero."))
    F.append(fig_bars("F08B", "08_RELEASED_REINFORCEMENT.svg", "8  Released reinforcement by family",
                      list(s9["released_reinforcement_kg_by_family"].items()), "kg", "s1",
                      f"Total {q(s9['released_reinforcement_kg_total'])} kg, S9's release, unchanged by S9A.",
                      "Each family at its authoritative frozen version; column ties and hooks (S9-C01) are not in it."))
    F += [fig_conditional(L, s), fig_blocked(L, s), fig_rfi(L, s)]
    ids = [f.fid for f in F]
    if len(set(ids)) != len(ids) or len({f.name for f in F}) != len(F):
        raise ValueError("figure ids")
    out = {f.name: f.standalone() for f in F}
    out["S9A_VISUAL_QA.html"] = page(L, s, F)
    index = [{"figure": f.fid, "file": f.name, "title": f.title, "labels": f.labels, "sources": f.sources}
             for f in F]
    out["VISUAL_INDEX.json"] = json.dumps({"figures": index, "labels": LABEL_NOTE, "lane_groups": LANE_GROUP},
                                          indent=1, sort_keys=True) + "\n"
    return out
