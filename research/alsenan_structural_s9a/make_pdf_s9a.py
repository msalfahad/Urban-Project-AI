"""Print visual/S9A_VISUAL_QA.html to visual/S9A_VISUAL_QA.pdf (A4 landscape) with the pre-installed Chromium.

    python3 -I research/alsenan_structural_s9a/make_pdf_s9a.py

The PDF is a rendering of the HTML the builder froze, not a frozen output itself. It is git-ignored like the other
review PDFs, because it embeds plan geometry from the client drawings. The HTML's SHA-256 goes into the PDF's metadata,
so a reader can tie the PDF to 18_S9A_CORRECTION_MANIFEST.json. The creation dates are dropped, so printing the same
HTML again gives the same file.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTML = HERE / "visual" / "S9A_VISUAL_QA.html"
PDF = HERE / "visual" / "S9A_VISUAL_QA.pdf"
MANIFEST = HERE / "18_S9A_CORRECTION_MANIFEST.json"
CHROMIUM = "/opt/pw-browsers/chromium"

SCRIPT = r"""
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: process.env.S9A_CHROMIUM });
  const p = await b.newPage();
  await p.emulateMedia({ media: 'print', colorScheme: 'light' });
  await p.goto('file://' + process.env.S9A_HTML, { waitUntil: 'load' });
  await p.pdf({ path: process.env.S9A_PDF, format: 'A4', landscape: true, printBackground: true,
    displayHeaderFooter: true, headerTemplate: '<div></div>',
    footerTemplate: '<div style="font:7px system-ui,Inter,sans-serif;color:#898781;width:100%;padding:0 10mm;' +
      'display:flex;justify-content:space-between"><span>S9A visual QA · ST7757 structural · correction ' +
      'layer over S9 (frozen) · nothing on these pages is released unless it says released</span>' +
      '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
    margin: { top: '9mm', bottom: '12mm', left: '10mm', right: '10mm' } });
  await b.close();
})();
"""


def main():
    sha = hashlib.sha256(HTML.read_bytes()).hexdigest()
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if m["outputs"].get("visual/S9A_VISUAL_QA.html") != sha:
        sys.exit("the HTML differs from the manifest: rebuild with build_s9a.py first")
    env = dict(os.environ, S9A_HTML=str(HTML), S9A_PDF=str(PDF), S9A_CHROMIUM=CHROMIUM)
    subprocess.run(["node", "-"], input=SCRIPT.encode(), env=env, check=True, cwd=HERE)
    from pypdf import PdfReader, PdfWriter
    r = PdfReader(str(PDF))
    w = PdfWriter(clone_from=r)
    w._info = None
    w.add_metadata({"/Title": "S9A visual QA (ST7757 structural)", "/Producer": "Chromium via make_pdf_s9a.py",
                    "/Subject": f"rendering of visual/S9A_VISUAL_QA.html sha256 {sha}"})
    with open(PDF, "wb") as fh:
        w.write(fh)
    print(json.dumps({"pdf": str(PDF.relative_to(HERE.parents[1])), "pages": len(r.pages), "html_sha256": sha}))


if __name__ == "__main__":
    main()
