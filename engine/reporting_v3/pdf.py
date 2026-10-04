"""REPORTING V3 - PDF documents (HTML -> Chromium), same style family as Reporting V2.

doc = {"title", "title_ar", "subtitle", "pages": [{"title_en", "title_ar", "blocks": [...]}]}
block: {"p": text} | {"ul": [text]} | {"kv": [[k, v]]} |
       {"table": {"head": [...], "rows": [[...]], "num": [col idx], "status": col idx, "ar": [col idx], "group": bool}}
Rows starting with {"group": text} render as a group band; {"total": True} rows are bold with a navy top rule.
"""

from __future__ import annotations

import base64
import hashlib
import html
from pathlib import Path

from engine.reporting_v2.pdf import _pin, find_chromium

NAVY, NAVY2 = "#1F3A5F", "#2C4E78"
ST = {"COMPUTED": ("#C6EFCE", "#006100"), "PARTIAL": ("#FFEB9C", "#7F6000"), "REVIEW": ("#FFEB9C", "#7F6000"),
      "BLOCKED": ("#FFC7CE", "#9C0006"), "NOT_IN_SOURCE": ("#EDEDED", "#555555"), "PASS": ("#C6EFCE", "#006100"),
      "FAIL": ("#FFC7CE", "#9C0006"), "UNCHANGED": ("#C6EFCE", "#006100")}

CSS = """
@font-face { font-family: Cairo; src: url('%(cairo)s'); }
@page { size: A4 landscape; margin: 11mm 9mm 13mm 9mm; }
body { font-family: Cairo, 'DejaVu Sans', sans-serif; font-size: 8pt; color: #222; margin: 0; }
.page { page-break-before: always; }
.page:first-of-type { page-break-before: auto; }
.top { display: flex; align-items: center; gap: 10px; border-bottom: 1.5pt solid #fbad46; padding-bottom: 3px; }
.top img { height: 36px; }
.top .t1 { font-size: 12pt; font-weight: 700; color: %(navy)s; }
.top .t2 { font-size: 7.5pt; color: #6B7280; }
.band { background: %(navy)s; color: #fff; display: flex; justify-content: space-between; align-items: center;
        padding: 6px 12px; margin: 6px 0 6px; font-size: 14pt; font-weight: 700; }
.ar { direction: rtl; text-align: right; }
p { margin: 3px 0 5px; line-height: 1.35; }
ul { margin: 2px 0 6px 16px; padding: 0; } li { margin: 1px 0; }
table { border-collapse: collapse; width: 100%%; margin: 4px 0 8px; }
th { background: #DCE3EC; color: %(navy)s; font-size: 7.2pt; border: 0.5pt solid #C3CBD5; padding: 2px 3px; text-align: left; }
td { border: 0.5pt solid #C3CBD5; padding: 1.5px 3px; vertical-align: top; font-size: 7.4pt; }
thead { display: table-header-group; } tr { break-inside: avoid; }
td.num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
td.st { text-align: center; font-weight: 700; font-size: 7pt; white-space: nowrap; }
tr.grp td { background: #548235; color: #fff; font-weight: 700; }
tr.tot td { background: #DDEBF7; font-weight: 700; border-top: 1.2pt solid %(navy)s; }
table.kv th { width: 28%%; }
.cover { text-align: center; margin-top: 30mm; }
.cover .h1 { font-size: 26pt; font-weight: 700; color: %(navy)s; }
.cover .h2 { font-size: 16pt; color: %(navy2)s; margin-top: 6mm; }
.cover .h3 { font-size: 10pt; color: #555; margin-top: 10mm; }
"""


def _e(v):
    return html.escape("" if v is None else str(v))


def _num(v):
    if v is None or v == "":
        return ""
    if isinstance(v, (int, float)):
        return f"{v:,.3f}" if isinstance(v, float) else f"{v:,}"
    return _e(v)


def _table(t):
    out = ["<table><thead><tr>" + "".join(f"<th>{_e(h)}</th>" for h in t["head"]) + "</tr></thead><tbody>"]
    num, ar, stc = set(t.get("num", [])), set(t.get("ar", [])), t.get("status")
    for r in t["rows"]:
        if isinstance(r, dict) and "group" in r:
            out.append(f'<tr class="grp"><td colspan="{len(t["head"])}">{_e(r["group"])}</td></tr>')
            continue
        cls = ""
        if isinstance(r, dict) and r.get("total"):
            cls, r = ' class="tot"', r["cells"]
        cells = []
        for i, v in enumerate(r):
            if i == stc and v in ST:
                bg, fg = ST[v]
                cells.append(f'<td class="st" style="background:{bg};color:{fg}">{_e(v)}</td>')
            elif i in num:
                cells.append(f'<td class="num">{_num(v)}</td>')
            elif i in ar:
                cells.append(f'<td class="ar">{_e(v)}</td>')
            else:
                cells.append(f"<td>{_e(v)}</td>")
        out.append(f"<tr{cls}>" + "".join(cells) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def build_html(doc, logo=None, cairo=None) -> str:
    logo_tag = ""
    if logo and Path(logo).exists():
        logo_tag = f'<img src="data:image/png;base64,{base64.b64encode(Path(logo).read_bytes()).decode()}" alt="Urban Projects">'
    css = CSS % {"navy": NAVY, "navy2": NAVY2, "cairo": Path(cairo).resolve().as_uri() if cairo else ""}
    out = [f"<!doctype html><html><head><meta charset='utf-8'><title>{_e(doc['title'])}</title><style>{css}</style></head><body>"]
    for i, pg in enumerate(doc["pages"]):
        out.append('<div class="page">')
        if pg.get("cover"):
            out.append(f'<div class="top">{logo_tag}</div><div class="cover"><div class="h1">{_e(doc["title"])}</div>'
                       f'<div class="h2 ar" style="text-align:center">{_e(doc["title_ar"])}</div>'
                       f'<div class="h3">{_e(doc["subtitle"])}</div>')
            for b in pg.get("blocks", []):
                out.append(_block(b))
            out.append("</div></div>")
            continue
        out.append(f'<div class="top">{logo_tag}<div><div class="t1">{_e(doc["title"])}</div>'
                   f'<div class="t2">{_e(doc["subtitle"])}</div></div></div>')
        out.append(f'<div class="band"><span>{_e(pg["title_en"])}</span><span class="ar">{_e(pg.get("title_ar", ""))}</span></div>')
        for b in pg.get("blocks", []):
            out.append(_block(b))
        out.append("</div>")
    out.append("</body></html>")
    return "".join(out)


def _block(b):
    if "p" in b:
        return f"<p>{_e(b['p'])}</p>"
    if "h" in b:
        return f'<p style="font-weight:700;color:{NAVY};font-size:9.5pt;margin-top:8px">{_e(b["h"])}</p>'
    if "ul" in b:
        return "<ul>" + "".join(f"<li>{_e(x)}</li>" for x in b["ul"]) + "</ul>"
    if "kv" in b:
        return '<table class="kv"><tbody>' + "".join(f"<tr><th>{_e(k)}</th><td>{_e(v)}</td></tr>" for k, v in b["kv"]) + \
            "</tbody></table>"
    if "table" in b:
        return _table(b["table"])
    return ""


def render(doc, path, logo=None, cairo=None) -> dict:
    from playwright.sync_api import sync_playwright
    path = Path(path)
    page_html = build_html(doc, logo, cairo)
    html_path = path.with_suffix(".html")
    html_path.write_text(page_html, encoding="utf-8")
    footer = ('<div style="font-family:Cairo,sans-serif;font-size:7pt;width:100%;color:#555;display:flex;'
              'justify-content:space-between;padding:0 9mm"><span>' + _e(doc["title"]) + '</span>'
              '<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span><span>Urban Projects</span></div>')
    launch = {"executable_path": find_chromium()} if find_chromium() else {}
    with sync_playwright() as p:
        br = p.chromium.launch(**launch)
        pg = br.new_page()
        pg.goto(html_path.resolve().as_uri())
        pg.wait_for_timeout(300)
        pg.pdf(path=str(path), format="A4", landscape=True, print_background=True, prefer_css_page_size=True,
               display_header_footer=True, header_template="<div></div>", footer_template=footer)
        br.close()
    data = _pin(path.read_bytes())
    path.write_bytes(data)
    html_path.unlink()
    return {"file": path.name, "file_sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            "html_sha256": hashlib.sha256(page_html.encode()).hexdigest()}
