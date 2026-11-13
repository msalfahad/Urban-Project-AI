"""T-753 read-only: render a window of an architectural DXF to a PNG outside the repository, one colour per layer, so a
person can read the joinery linework (kitchen runs, wardrobes, vanities). Usage:
  run research/agents_t753/t753_render.py <arch.dxf> <out.png> [x0 y0 x1 y1 (metres)] [--layers a,b] [--handles]"""
from __future__ import annotations
import sys


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("out")
    ap.add_argument("win", nargs="*", type=float)
    ap.add_argument("--layers", default="")
    ap.add_argument("--handles", action="store_true", help="print the handle of every LINE/LWPOLYLINE/ARC in the window")
    ap.add_argument("--dpi", type=int, default=150)
    a = ap.parse_args(argv)
    import ezdxf
    from ezdxf import bbox
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    doc = ezdxf.readfile(a.dxf)
    msp = doc.modelspace()
    keep = set(a.layers.split(",")) if a.layers else None
    if a.win:
        x0, y0, x1, y1 = [v * 1000 for v in a.win]
    else:
        e = bbox.extents(msp)
        x0, y0, x1, y1 = e.extmin.x, e.extmin.y, e.extmax.x, e.extmax.y
        print("extents m", [round(v / 1000, 2) for v in (x0, y0, x1, y1)])

    def flt(ent):
        if keep is not None and (not ent.dxf.is_supported("layer") or ent.dxf.layer not in keep):
            return False
        try:
            b = bbox.extents([ent], fast=True)
        except Exception:
            return False
        if not b.has_data:
            return False
        return not (b.extmax.x < x0 or b.extmin.x > x1 or b.extmax.y < y0 or b.extmin.y > y1)
    fig = plt.figure(figsize=(max(4, (x1 - x0) / 1000 * 0.9), max(4, (y1 - y0) / 1000 * 0.9)))
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    ctx.set_current_layout(msp)
    Frontend(ctx, MatplotlibBackend(ax)).draw_entities(e for e in msp if flt(e))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    # a 1 m grid so the reader can locate items (labels in metres)
    import math
    for gx in range(math.floor(x0 / 1000), math.ceil(x1 / 1000) + 1):
        ax.axvline(gx * 1000, color="#cccccc", lw=0.2, zorder=-1)
        if gx % 2 == 0:
            ax.text(gx * 1000, y0, str(gx), fontsize=5, color="blue")
    for gy in range(math.floor(y0 / 1000), math.ceil(y1 / 1000) + 1):
        ax.axhline(gy * 1000, color="#cccccc", lw=0.2, zorder=-1)
        if gy % 2 == 0:
            ax.text(x0, gy * 1000, str(gy), fontsize=5, color="blue")
    fig.savefig(a.out, dpi=a.dpi, facecolor="white")
    if a.handles:
        for e in msp:
            if e.dxftype() in ("LINE", "LWPOLYLINE", "ARC", "CIRCLE", "INSERT") and flt(e):
                b = bbox.extents([e])
                print(e.dxftype(), e.dxf.handle, e.dxf.layer, getattr(e.dxf, "name", ""),
                      [round(v / 1000, 3) for v in (b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
