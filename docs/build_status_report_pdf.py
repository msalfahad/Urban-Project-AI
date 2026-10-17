"""Build a standalone HTML and a PDF from the artifact-format status report.

The report in docs/ is written the way an Artifact wants it - no <html> wrapper, fonts pulled from Google - so it
cannot be opened offline or printed as it stands.  This turns it into one self-contained file: the font subsets
that the page actually uses are inlined as data URIs, a print stylesheet is added, and headless Chromium prints
it.  Nothing about the report's content is changed.

    python docs/build_status_report_pdf.py
"""

from __future__ import annotations

import base64
import pathlib
import re
import subprocess
import tempfile

SRC = pathlib.Path("docs/URBAN_ENGINE_STATUS_REPORT.html")
OUT = pathlib.Path("data/reports")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
FONT_CSS = ("https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700"
            "&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600"
            "&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Arabic:wght@400;600&display=swap")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
PRINT_CSS = """
<style media="print">
@page { size: A4; margin: 15mm 13mm 16mm; }
html, body { background:#fff !important; }
body { font-size: 10.8pt; }
header.bar { position: static !important; }
header.bar nav { display: none; }
main { padding-block: 16px 0 !important; }
.wrap { padding-inline: 0 !important; max-width: 100% !important; }
.scroll { overflow: visible !important; }
table { min-width: 0 !important; font-size: 9.2pt; }
th, td { padding: 4px 6px; }
h1 { font-size: 24pt; }
h2 { font-size: 15pt; margin-top: 22px; break-after: avoid; page-break-after: avoid; }
h3 { break-after: avoid; page-break-after: avoid; }
.case, .q, .tile, .flow .step, tr, .scroll { break-inside: avoid; page-break-inside: avoid; }
#status, #how, #rules, #right, #wrong, #limits, #ask, #app, #files { break-before: page; page-break-before: always; }
p, li { max-width: none; }
a { color: inherit; text-decoration: none; }
</style>
"""


def _curl(url, dest):
    subprocess.run(["curl", "-sS", "-m", "60", "-A", UA, "-o", str(dest), url], check=True)


def inline_fonts(tmp):
    """Only the latin and arabic faces the page uses - the other 28 subsets would triple the file."""
    css = tmp / "fonts.css"
    _curl(FONT_CSS, css)
    kept, seen = [], {}
    for block in re.findall(r"@font-face\s*\{[^}]*\}", css.read_text()):
        rng = re.search(r"unicode-range:\s*([^;]+);", block)
        if not rng or not ("U+0000-00FF" in rng.group(1) or "U+0600" in rng.group(1)):
            continue
        url = re.search(r"url\((https://[^)]+)\)", block).group(1)
        if url not in seen:
            f = tmp / f"f{len(seen)}.woff2"
            _curl(url, f)
            seen[url] = base64.b64encode(f.read_bytes()).decode()
        kept.append(block.replace(url, "data:font/woff2;base64," + seen[url]))
    return "<style>\n" + "\n".join(kept) + "\n</style>"


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    src = SRC.read_text("utf-8")
    head, body = src[:src.index("<header")], src[src.index("<header"):]
    with tempfile.TemporaryDirectory() as td:
        head = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>',
                      inline_fonts(pathlib.Path(td)), head)
    doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
           + head + "<style>html,body{margin:0}body{padding-block:0}</style>" + PRINT_CSS
           + "</head>\n<body>\n" + body + "\n</body>\n</html>\n")
    html = OUT / "URBAN_ENGINE_STATUS_REPORT_standalone.html"
    html.write_text(doc, "utf-8")
    pdf = OUT / "URBAN_ENGINE_STATUS_REPORT.pdf"
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
                    "--virtual-time-budget=15000", f"--print-to-pdf={pdf}", html.resolve().as_uri()],
                   check=True, capture_output=True)
    return html, pdf


if __name__ == "__main__":
    h, p = build()
    print(f"{h}  {h.stat().st_size // 1024} KB")
    print(f"{p}  {p.stat().st_size // 1024} KB")
