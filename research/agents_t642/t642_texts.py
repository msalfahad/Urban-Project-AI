"""T-642 probe (exploration only; stdout): every TEXT / MTEXT (model space and blocks) matching a word, with position.
Usage: t642_texts.py <dxf> <regex>"""
from __future__ import annotations

import re
import sys

import ezdxf


def main(argv):
    doc = ezdxf.readfile(argv[0])
    rx = re.compile(argv[1], re.I)
    for sp in [doc.modelspace()] + list(doc.blocks):
        for e in sp:
            t = e.dxftype()
            if t not in ("TEXT", "MTEXT", "ATTDEF"):
                continue
            s = e.plain_text() if t == "MTEXT" else e.dxf.text
            if rx.search(s or ""):
                print(sp.name, e.dxf.handle, t, e.dxf.layer, round(e.dxf.insert.x / 1000, 3), round(e.dxf.insert.y / 1000, 3),
                      repr(s[:200]))


if __name__ == "__main__":
    main(sys.argv[1:])
