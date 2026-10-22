"""T-160: does a drawn ring band stop at the faces of its bay? (the drawing's own answer to the full-annulus question)

For every ARC (layer filter) whose centre lies inside the window, print both endpoints and the bay face each one lies on
(within 3 mm), or 'joins another arc' (an endpoint shared with another arc of the window). A ring whose outer arcs all end
on bay faces is drawn in-bay: no part of it lies inside the framing members.
Usage: python -I arc_ends.py <dxf> x0,y0,x1,y1 W=<x>,E=<x>,S=<y>,N=<y> [--layers 1]
"""
import math
import sys

import ezdxf

MM = 0.001


def main(dxf, win, faces, layers=("1",), tol=0.003):
    x0, y0, x1, y1 = win
    msp = ezdxf.readfile(dxf).modelspace()
    arcs = []
    for e in msp:
        if e.dxftype() == "ARC" and e.dxf.layer in layers:
            c = e.dxf.center
            if x0 <= c.x * MM <= x1 and y0 <= c.y * MM <= y1:
                arcs.append((c.x * MM, c.y * MM, e.dxf.radius * MM, e.dxf.start_angle, e.dxf.end_angle))
    ends = []
    for cx, cy, r, a0, a1 in arcs:
        for a in (a0, a1):
            ends.append((cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)), (cx, cy, r, a)))
    bad = 0
    for x, y, (cx, cy, r, a) in ends:
        on = [k for k, v in faces.items() if abs((x if k in "WE" else y) - v) <= tol]
        joins = sum(1 for x2, y2, _ in ends if math.hypot(x2 - x, y2 - y) <= tol) > 1
        what = f"on face {','.join(on)}" if on else ("joins another arc" if joins else "FREE END (not on a face)")
        bad += what.startswith("FREE")
        print(f"arc c=({cx:.4f},{cy:.4f}) r={r:.4f} at {a:7.2f} deg -> ({x:.4f},{y:.4f}) {what}")
    print("ALL ENDS ON A FACE OR JOINED" if not bad else f"{bad} FREE END(S)")
    return bad


if __name__ == "__main__":
    a = sys.argv[1:]
    lay = tuple(a[a.index("--layers") + 1].split(",")) if "--layers" in a else ("1",)
    f = {kv.split("=")[0]: float(kv.split("=")[1]) for kv in a[2].split(",")}
    sys.exit(1 if main(a[0], tuple(map(float, a[1].split(","))), f, lay) else 0)
