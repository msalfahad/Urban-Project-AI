"""TEXT STYLE FONTS (V3) - {text source handle: font file of its text style}, read from a DXF.

The canonical text record (canonical_input.PlacedText) carries no style, so a legacy Arabic SHX text cannot be told
from Latin text without the drawing. This reader walks every TEXT / MTEXT / ATTRIB / ATTDEF in model space, paper
spaces and block definitions and returns the font file of each one's text style, keyed by the decimal handle the
canonical identity uses (source_handle). A style without a font file, or a missing style, maps to "".

Project-agnostic; ezdxf only.
"""

from __future__ import annotations

import ezdxf

POLICY_ID = "TEXT_STYLE_FONT_MAP_V1"
TEXT_TYPES = ("TEXT", "MTEXT", "ATTRIB", "ATTDEF")


def font_of_handle(dxf_path) -> dict:
    doc = ezdxf.readfile(str(dxf_path))
    fonts = {}
    for st in doc.styles:
        f = st.dxf.get("font", "") or ""
        fonts[st.dxf.name.upper()] = f
    out = {}

    def visit(e):
        if e.dxftype() in TEXT_TYPES:
            out[str(int(e.dxf.handle, 16))] = fonts.get((e.dxf.get("style", "") or "").upper(), "")
        if e.dxftype() == "INSERT":
            for a in e.attribs:
                visit(a)

    for layout in doc.layouts:
        for e in layout:
            visit(e)
    for blk in doc.blocks:
        for e in blk:
            visit(e)
    return dict(sorted(out.items(), key=lambda kv: int(kv[0])))
