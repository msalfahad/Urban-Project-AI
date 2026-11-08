"""T-642 probe (exploration only; stdout): DXF entities by handle, or near a point (drawing units / 1000 = m).
Usage: t642_handles.py <dxf> h <handle> ... | t642_handles.py <dxf> near <x_m> <y_m> <r_m> [block]"""
from __future__ import annotations

import sys

import ezdxf


def desc(e):
    t = e.dxftype()
    if not e.dxf.is_supported("layer"):
        return {"h": e.dxf.handle, "t": t}
    d = {"h": e.dxf.handle, "t": t, "layer": e.dxf.get("layer"), "owner": e.dxf.get("owner")}
    try:
        if t == "LINE":
            d["a"] = (round(e.dxf.start.x / 1000, 4), round(e.dxf.start.y / 1000, 4))
            d["b"] = (round(e.dxf.end.x / 1000, 4), round(e.dxf.end.y / 1000, 4))
        elif t in ("LWPOLYLINE",):
            d["pts"] = [(round(float(p[0]) / 1000, 4), round(float(p[1]) / 1000, 4)) for p in e.get_points("xy")]
            d["bulge"] = [round(float(p[4]), 4) for p in e.get_points("xyseb")]
            d["closed"] = e.closed
        elif t in ("ARC", "CIRCLE"):
            d["c"] = (round(e.dxf.center.x / 1000, 4), round(e.dxf.center.y / 1000, 4))
            d["r"] = round(e.dxf.radius / 1000, 4)
            if t == "ARC":
                d["ang"] = (round(e.dxf.start_angle, 3), round(e.dxf.end_angle, 3))
        elif t in ("TEXT", "MTEXT"):
            d["txt"] = e.plain_text() if t == "MTEXT" else e.dxf.text
            d["at"] = (round(e.dxf.insert.x / 1000, 4), round(e.dxf.insert.y / 1000, 4))
        elif t == "INSERT":
            d["name"] = e.dxf.name
            d["at"] = (round(e.dxf.insert.x / 1000, 4), round(e.dxf.insert.y / 1000, 4))
            d["scale"] = (e.dxf.xscale, e.dxf.yscale)
            d["rot"] = e.dxf.rotation
        elif t == "HATCH":
            d["pattern"] = e.dxf.pattern_name
    except Exception as x:  # noqa: BLE001
        d["err"] = str(x)
    return d


def pts(d):
    if "a" in d:
        return [d["a"], d["b"]]
    if "pts" in d:
        return d["pts"]
    if "c" in d:
        return [d["c"]]
    if "at" in d:
        return [d["at"]]
    return []


def main(argv):
    doc = ezdxf.readfile(argv[0])
    if argv[1] == "h":
        for h in argv[2:]:
            e = doc.entitydb.get(h.upper())
            if e is None:
                print(h, "absent")
                continue
            d = desc(e)
            own = doc.entitydb.get(e.dxf.owner)
            d["owner_t"] = own.dxftype() if own is not None else None
            if own is not None and own.dxftype() == "BLOCK_RECORD":
                d["block"] = own.dxf.name
            print(d)
        return
    x, y, r = float(argv[2]), float(argv[3]), float(argv[4])
    blk = argv[5] if len(argv) > 5 else None
    spaces = [doc.blocks.get(blk)] if blk else [doc.modelspace()] + [b for b in doc.blocks]
    for sp in spaces:
        for e in sp:
            d = desc(e)
            P = pts(d)
            if "pts" in d and len(P) > 1:
                hit = any(min(p[0], q[0]) - r <= x <= max(p[0], q[0]) + r and min(p[1], q[1]) - r <= y <= max(p[1], q[1]) + r
                          for p, q in zip(P, P[1:] + ([P[0]] if d.get("closed") else [])))
            elif "a" in d:
                p, q = P
                hit = min(p[0], q[0]) - r <= x <= max(p[0], q[0]) + r and min(p[1], q[1]) - r <= y <= max(p[1], q[1]) + r
            else:
                hit = any(abs(p[0] - x) <= r and abs(p[1] - y) <= r for p in P)
            if hit:
                d["space"] = sp.name
                print(d)


if __name__ == "__main__":
    main(sys.argv[1:])
