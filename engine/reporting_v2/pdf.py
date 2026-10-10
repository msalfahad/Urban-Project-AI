"""REPORTING V2 - PDF renderer: the same REPORTING_MODEL_V2 as the workbook, printed through Chromium.

One section per workbook sheet, same order, same tables, same formatted values and status colours; each sheet starts
on a new page with its navy title band. TECH sheets print a short appendix page (first rows + row count) - the full
tables stay in the workbook. The PDF metadata dates are pinned so the same model gives the same bytes.
"""

from __future__ import annotations

import base64
import glob
import hashlib
import html
import os
import re
from pathlib import Path

from . import terms as T
from .model import is_f, is_in, is_q
from .xlsx import QTY_FMT, SUMMARY_FMT, qty_text

NAVY, NAVY_2 = "#1F3A5F", "#2C4E78"
STATUS_CSS = {"COMPUTED": "#E2EFDA", "PARTIAL": "#FFF2CC", "REVIEW": "#FFF2CC", "BLOCKED": "#F8D7DA", "INFO": "#EDEDED"}
BAR = {"COMPUTED": "#5B9A3C", "PARTIAL": "#D9822B", "REVIEW": "#C9A227", "BLOCKED": "#C0504D"}
RSTATUS_CSS = {"MATCH": ("#C6EFCE", "#006100"), "CLOSE": ("#FFEB9C", "#7F6000"), "REVIEW": ("#FFC7CE", "#9C0006")}
INPUT_BG, FORMULA_BG = "#FFF9C4", "#DDEBF7"
TECH_ROWS = 25
FIXED_DATE = b"D:20261003000000+00'00'"


def fmt_num(v, fmt):
    """Python rendering of the workbook number format (#,##0.000 / #,##0.00 / #,##0 / 0% / 0.000 / General)."""
    if fmt == "0%":
        return f"{v * 100:.0f}%"
    if fmt == "General":
        return f"{v:g}"
    m = re.match(r"#?,?#*0(?:\.(0+))?", fmt.replace("#,##", "#,"))
    dec = len(m.group(1)) if m and m.group(1) else 0
    return f"{v:,.{dec}f}" if "," in fmt else f"{v:.{dec}f}"


def _cell_fmt(c, colspec, role):
    u = (c.get("unit") if isinstance(c, dict) else None) or colspec.get("unit")
    k = colspec["kind"]
    if k == "count":
        return "#,##0"
    if k == "pct":
        return "0%"
    if k == "dim":
        return "0.000"
    if k == "num":
        return "General"
    if role == "SUMMARY" and u in SUMMARY_FMT and not (isinstance(c, dict) and c.get("unit")):
        return SUMMARY_FMT[u]
    return QTY_FMT.get(u, "#,##0.000")


def _esc(v):
    return html.escape(str(v))


def _plain(c):
    """The value shown for a cell: a formula's evaluated value, an input's pre-fill, otherwise the cell itself."""
    return c["v"] if is_f(c) else (c["input"] if is_in(c) else c)


def _bar(rows):
    rows = [dict(r, cells=[_plain(c) for c in r["cells"]]) for r in rows if r["status"] in BAR]
    n = sum(r["cells"][2] for r in rows) or 1
    x, out = 0.0, []
    for r in rows:
        w = 560.0 * r["cells"][2] / n
        if w <= 0:
            continue
        out.append(f'<rect x="{x + 1:.1f}" y="4" width="{max(w - 2, 1):.1f}" height="26" rx="3" fill="{BAR[r["status"]]}">'
                   f'<title>{_esc(T.STATUS_LABEL[r["status"]][0])}: {r["cells"][2]}</title></rect>')
        if w > 40:
            out.append(f'<text x="{x + w / 2:.1f}" y="22" text-anchor="middle" fill="#fff" font-size="11" font-weight="700">'
                       f'{_esc(T.STATUS_LABEL[r["status"]][0])} {r["cells"][2]}</text>')
        x += w
    return f'<svg class="bar" viewBox="0 0 562 34" width="562" height="34" role="img" aria-label="coverage by status">{"".join(out)}</svg>'


def _table(sec, role, tech=False):
    cols = sec["columns"]
    rows = sec["rows"][:TECH_ROWS] if tech else sec["rows"]
    h = []
    if sec["kind"] == "notes":
        h.append('<ul class="notes">' + "".join(f"<li>{_esc(r['cells'][0])}</li>" for r in rows) + "</ul>")
        return "".join(h)
    if sec["kind"] == "info":
        h.append('<table class="info">' + "".join(f"<tr><th>{_esc(r['cells'][0])}</th><td>{_esc(r['cells'][1])}</td></tr>"
                                                  for r in rows) + "</table>")
        return "".join(h)
    if role == "RECON":                                   # working sheet: fixed column widths as in the workbook grid
        ws_ = [c.get("width") or 12 for c in cols]
        h.append('<table class="grid recon"><colgroup>' + "".join(f'<col style="width:{100 * w / sum(ws_):.2f}%">' for w in ws_) +
                 "</colgroup><thead><tr>")
    else:
        h.append('<table class="grid"><thead><tr>')
    for c in cols:
        lab = _esc(c["en"]) + (f" ({_esc(c['unit'])})" if c.get("unit") and c["kind"] == "qty" and c["en"] != "QTY" else "")
        ar = f'<br><span class="ar">{_esc(c["ar"])}</span>' if c.get("ar") else ""
        h.append(f"<th>{lab}{ar}</th>")
    h.append("</tr></thead><tbody>")
    for r in rows:
        group = r["role"] == "NOTE" and r.get("note") == "GROUP"
        cls = "group" if group else ("tot" if r["role"] in ("SUBTOTAL", "TOTAL") else "")
        h.append(f'<tr class="{cls}">')
        for j, c in enumerate(cols):
            v = r["cells"][j] if j < len(r["cells"]) else ""
            k = c["kind"]
            if is_f(v) or is_in(v):
                x, bg = _plain(v), (FORMULA_BG if is_f(v) else INPUT_BG)
                if k == "rstatus" and x in RSTATUS_CSS:
                    bg, fg = RSTATUS_CSS[x]
                    h.append(f'<td class="st" style="background:{bg};color:{fg}">{_esc(x)}</td>')
                elif k == "rstatus":
                    h.append(f'<td class="st" style="background:#EDEDED;color:#555">{_esc(x or "")}</td>')
                elif isinstance(x, (int, float)) and not isinstance(x, bool):
                    if k == "pct" or (is_in(v) and v["itype"] == "pct"):
                        t = f"{x * 100:+.1f}%" if is_f(v) and c["key"] == "pct" else f"{x * 100:.1f}%"
                    elif c["key"] == "diff":
                        t = f"{x:+,.3f}" if abs(x) >= 0.0005 else "0.000"
                    elif k == "count":
                        t = f"{x:,.0f}"
                    else:
                        t = fmt_num(x, _cell_fmt({}, dict(c, unit=(v.get("fmt") if is_f(v) else None) or c.get("unit")), role) if k == "qty"
                                    else "0.000" if k == "dim" else "General")
                    h.append(f'<td class="num" style="background:{bg}">{t}</td>')
                else:
                    h.append(f'<td style="background:{bg}">{_esc("" if x is None else x)}</td>')
            elif is_q(v):
                if v["q"] is None:
                    t = qty_text(v)
                    h.append(f'<td class="num {"blk" if t == "BLOCKED" else "na"}">{_esc(t)}</td>')
                else:
                    h.append(f'<td class="num">{fmt_num(v["q"], _cell_fmt(v, c, role))}</td>')
            elif k == "status" and v in T.STATUS_LABEL:
                h.append(f'<td class="st" style="background:{STATUS_CSS[v]}">{_esc(T.STATUS_LABEL[v][0])}</td>')
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                h.append(f'<td class="num">{fmt_num(v, _cell_fmt(v, c, role))}</td>')
            elif k == "ar":
                h.append(f'<td class="ar" dir="rtl">{_esc(v or "")}</td>')
            else:
                nw = " nw" if k == "code" and isinstance(v, str) and len(v) <= 18 else ""      # short ids never break
                h.append(f'<td class="{(k if k in ("code", "cls") else "") + nw}">{_esc("" if v is None else v)}</td>')
        h.append("</tr>")
    h.append("</tbody></table>")
    if tech and len(sec["rows"]) > TECH_ROWS:
        h.append(f'<p class="secnote">First {TECH_ROWS} of {len(sec["rows"])} rows - the full table is in the workbook tab of the same name.</p>')
    return "".join(h)


CSS = """
@font-face { font-family: Cairo; src: url('%(cairo)s'); }
@page { size: A4 landscape; margin: 11mm 9mm 13mm 9mm; }
body { font-family: Cairo, 'DejaVu Sans', sans-serif; font-size: 7.9pt; color: #222; margin: 0; }
.sheet { page-break-before: always; }
.sheet:first-of-type { page-break-before: auto; }
.top { display: flex; align-items: center; gap: 10px; border-bottom: 1.5pt solid #fbad46; padding-bottom: 3px; }
.top img { height: 38px; }
.top .t1 { font-size: 13pt; font-weight: 700; color: %(navy)s; }
.top .t2 { font-size: 7.5pt; color: #6B7280; }
.top .rs { margin-left: auto; font-size: 7.5pt; font-weight: 700; color: #9C2B2B; text-align: right; }
.band { background: %(navy)s; color: #fff; display: flex; justify-content: space-between; align-items: center;
        padding: 6px 12px; margin: 6px 0 2px; font-size: 15pt; font-weight: 700; }
.band .ar { font-size: 15pt; }
.note { color: #9C2B2B; font-style: italic; font-size: 7.5pt; margin: 1px 0 4px; }
.sec { break-inside: auto; margin-top: 8px; }
.sechead { background: %(navy2)s; color: #fff; display: flex; justify-content: space-between; padding: 3px 8px;
           font-weight: 700; font-size: 9.5pt; break-after: avoid; }
table { border-collapse: collapse; width: 100%%; }
table.grid th { background: #DCE3EC; color: %(navy)s; font-size: 7.2pt; border: 0.5pt solid #C3CBD5; padding: 2px 3px; }
table.grid td { border: 0.5pt solid #C3CBD5; padding: 1.5px 3px; vertical-align: top; }
table.grid thead { display: table-header-group; }
table.grid tr { break-inside: avoid; }
td.num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
td.blk { color: #9C2B2B; text-align: center; font-weight: 700; font-size: 7.4pt; }
td.na { color: #6B7280; text-align: center; }
td.st { text-align: center; font-weight: 700; font-size: 7.4pt; white-space: nowrap; }
td.ar, .ar { direction: rtl; text-align: right; }
td.code { font-family: 'DejaVu Sans Mono', monospace; font-size: 6.4pt; color: #444; word-break: break-all; }
td.nw { white-space: nowrap; word-break: normal; }
table.recon { table-layout: fixed; font-size: 6.9pt; }
table.recon th { font-size: 6.4pt; }
table.recon td { overflow-wrap: anywhere; }
td.cls { font-family: 'DejaVu Sans Mono', monospace; font-size: 6.2pt; color: #444; white-space: nowrap; }
tr.group td { background: #E9EEF4; font-weight: 700; color: %(navy)s; }
tr.tot td { background: #F2F4F7; font-weight: 700; border-top: 1.2pt solid %(navy)s; }
table.info th { text-align: left; width: 26%%; color: %(navy)s; padding: 1px 4px; }
table.info td { padding: 1px 4px; }
.secnote { color: #6B7280; font-style: italic; font-size: 7pt; margin: 2px 0 0; }
ul.notes { margin: 3px 0 0 16px; padding: 0; }
.bar { display: block; margin: 6px 0 2px; }
"""


def build_html(model, logo=None, cairo=None) -> str:
    proj = model["project"]
    logo_tag = ""
    if logo and Path(logo).exists():
        logo_tag = f'<img src="data:image/png;base64,{base64.b64encode(Path(logo).read_bytes()).decode()}" alt="Urban Projects">'
    css = CSS % {"navy": NAVY, "navy2": NAVY_2, "cairo": Path(cairo).resolve().as_uri() if cairo else ""}
    out = [f"<!doctype html><html><head><meta charset='utf-8'><title>{_esc(proj['name_en'])} - QTO REPORT</title>"
           f"<style>{css}</style></head><body>"]
    for s in model["sheets"]:
        tech = s["role"] == "TECH"
        out.append(f'<div class="sheet" data-sheet="{_esc(s["name"])}">')
        out.append(f'<div class="top">{logo_tag}<div><div class="t1">{_esc(proj["name_en"])} — QTO REPORT — {_esc(proj["phase"])}</div>'
                   f'<div class="t2">{_esc(proj["subtitle"])}</div></div><div class="rs">{_esc(proj["release_state"])}'
                   f'<br><span class="ar">{_esc(proj.get("name_ar", ""))}</span></div></div>')
        out.append(f'<div class="band"><span>{_esc(s["name"][:2])}. {_esc(s["title_en"])}</span><span class="ar">{_esc(s["title_ar"])}</span></div>')
        if s.get("note"):
            out.append(f'<div class="note">{_esc(s["note"])}</div>')
        if tech:
            out.append('<div class="note">Technical appendix (TRACE) - not additive.</div>')
        for sec in s["sections"]:
            out.append(f'<div class="sec"><div class="sechead"><span>{_esc(sec["title_en"])}</span><span class="ar">{_esc(sec["title_ar"])}</span></div>')
            if sec["kind"] == "coverage":
                out.append(_bar(sec["rows"]))
            out.append(_table(sec, s["role"], tech))
            if sec.get("note"):
                out.append(f'<p class="secnote">{_esc(sec["note"])}</p>')
            out.append("</div>")
        out.append("</div>")
    out.append("</body></html>")
    return "".join(out)


def find_chromium():
    exe = os.environ.get("URBAN_CHROMIUM")
    if exe:
        return exe
    hits = sorted(glob.glob(f"{os.environ.get('PLAYWRIGHT_BROWSERS_PATH', '/opt/pw-browsers')}/chromium-*/chrome-linux/chrome"))
    return hits[-1] if hits else None


def _pin(data: bytes) -> bytes:
    """Same-length replacement of the creation / modification dates so the bytes are stable (offsets unchanged)."""
    def fix(m):
        n = len(m.group(0)) - 2
        return b"(" + FIXED_DATE[:n].ljust(n, b" ") + b")"
    return re.sub(rb"\(D:\d{14}[^)]*\)", fix, data)


def render(model, path, logo=None, cairo=None) -> dict:
    from playwright.sync_api import sync_playwright
    path = Path(path)
    page_html = build_html(model, logo, cairo)
    html_path = path.with_suffix(".html")
    html_path.write_text(page_html, encoding="utf-8")
    proj = model["project"]
    footer = ('<div style="font-family:Cairo,sans-serif;font-size:7pt;width:100%;color:#555;display:flex;justify-content:space-between;'
              f'padding:0 9mm"><span>{_esc(proj["name_en"])} — QTO REPORT — {_esc(proj["phase"])}</span>'
              '<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span><span>Urban Projects</span></div>')
    launch = {"executable_path": find_chromium()} if find_chromium() else {}
    with sync_playwright() as p:
        b = p.chromium.launch(**launch)
        pg = b.new_page()
        pg.goto(html_path.resolve().as_uri())
        pg.wait_for_timeout(300)
        pg.pdf(path=str(path), format="A4", landscape=True, print_background=True, prefer_css_page_size=True,
               display_header_footer=True, header_template="<div></div>", footer_template=footer)
        b.close()
    data = _pin(path.read_bytes())
    path.write_bytes(data)
    html_path.unlink()
    return {"file_sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "html_sha256": hashlib.sha256(page_html.encode()).hexdigest()}
