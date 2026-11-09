"""T-642 probe (exploration only; stdout): the content of a block definition and every INSERT of it.
Usage: t642_block.py <dxf> <block name>"""
from __future__ import annotations

import sys

import ezdxf


def main(argv):
    doc = ezdxf.readfile(argv[0])
    b = doc.blocks.get(argv[1])
    print("block", argv[1], "base", tuple(b.base_point))
    for e in b:
        t = e.dxftype()
        d = {"h": e.dxf.handle, "t": t}
        if e.dxf.is_supported("layer"):
            d["layer"] = e.dxf.layer
        if t in ("TEXT", "MTEXT", "ATTDEF"):
            d["txt"] = e.plain_text() if t == "MTEXT" else e.dxf.text
            d["at"] = (round(e.dxf.insert.x, 2), round(e.dxf.insert.y, 2))
            d["height"] = e.dxf.get("height") or e.dxf.get("char_height")
        elif t == "LINE":
            d["a"] = (round(e.dxf.start.x, 2), round(e.dxf.start.y, 2))
            d["b"] = (round(e.dxf.end.x, 2), round(e.dxf.end.y, 2))
        print(d)
    for ins in doc.modelspace().query("INSERT"):
        if ins.dxf.name.lower() == argv[1].lower():
            v = [(a.dxf.tag, a.dxf.text) for a in ins.attribs]
            print("INSERT", ins.dxf.handle, ins.dxf.layer, round(ins.dxf.insert.x / 1000, 4), round(ins.dxf.insert.y / 1000, 4),
                  "rot", round(ins.dxf.rotation, 3), "scale", ins.dxf.xscale, v)
    # every insert whose block holds a text equal to the block name (mark blocks)
    names = {}
    for ins in doc.modelspace().query("INSERT"):
        names.setdefault(ins.dxf.name, 0)
        names[ins.dxf.name] += 1
    print("insert names", sorted(names.items()))


if __name__ == "__main__":
    main(sys.argv[1:])
