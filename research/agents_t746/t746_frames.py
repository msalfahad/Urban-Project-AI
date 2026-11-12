"""T-746 door frame census from the plan DXF (research; reads a private drawing passed as an argument, writes only
handles, block names and sizes in m: no coordinate, text or client data).

Per door / gate / arch of the T-249 census (research/agents_t249/OPENINGS_T249.csv, PLAN_SYMBOL handle): when the
handle is an INSERT, its block's frame posts are read: a closed rectangle at each jamb whose sides run from the wall
line y = 0 to y = D (the block's wall depth). Opening width = the block's extreme x (jamb to jamb, block units mm,
scale +-1 only: a mirrored insert (x scale -1) has the same sizes). The drawn masonry jambs are then found on both wall faces (the wall lines that stop at the opening, in block
coordinates); only when both posts' outer edges sit at the masonry jambs (within 5 mm) does the plan draw the frame
over the whole jamb reveal (frame_at_jambs True -> FRAME_COVERS_RETURN_DRAWN for the jambs); a block whose posts sit
off the wall gap is a POSITION CONFLICT, never read as cover. The head
member is not on a plan: nothing is read for it.

    python3 -I research/agents_t746/t746_frames.py <P7757.dxf> > research/agents_t746/DOOR_FRAMES_T746.csv
"""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CENSUS = ROOT / "research/agents_t249/OPENINGS_T249.csv"
COLS = ("opening", "kind", "handle", "entity", "block", "mirrored", "opening_w_m", "wall_depth_m", "post_w_m",
        "posts_closed", "masonry_w_m", "jamb_offsets_mm", "frame_at_jambs", "evidence")
TOL_MM = 5.0          # a post edge within 5 mm of the drawn wall end is at the jamb


def _masonry(msp, e, w, depth):
    """masonry jamb ends on both wall faces in block coordinates: the drawn wall lines (any LINE parallel to the
    opening on y = 0 or y = depth, within 1.5 m) that stop at the opening. -> (left, right) per face or None."""
    import math  # noqa: PLC0415
    ins, a = e.dxf.insert, math.radians(e.dxf.rotation)
    ca, sa, sx, sy = math.cos(a), math.sin(a), e.dxf.xscale, e.dxf.yscale

    def loc(p):
        dx, dy = p.x - ins.x, p.y - ins.y
        return ((dx * ca + dy * sa) / sx, (-dx * sa + dy * ca) / sy)

    faces = {}
    for face in (0.0, depth):
        left, right = None, None
        for ln in msp.query("LINE"):
            p0, p1 = loc(ln.dxf.start), loc(ln.dxf.end)
            if abs(p0[1] - face) > 2 or abs(p1[1] - face) > 2:
                continue
            x0, x1 = sorted((p0[0], p1[0]))
            if x1 < -1500 or x0 > w + 1500 or x1 - x0 < 1:
                continue
            if x0 < -TOL_MM and x1 <= w / 2:
                left = x1 if left is None else max(left, x1)
            elif x1 > w + TOL_MM and x0 >= w / 2:
                right = x0 if right is None else min(right, x0)
        faces[face] = (left, right)
    return faces


def _rects(segs, depth):
    """x ranges [x0, x1] closed as rectangles 0 .. depth: two verticals over the full depth and, at y = 0 and at
    y = depth, a horizontal line covering x0 .. x1 (a top line may run on into the leaf, so it may be longer)."""
    vert = {s[0] for s in segs if s[0] == s[2] and {s[1], s[3]} == {0.0, depth}}
    hor = [(min(s[0], s[2]), max(s[0], s[2]), s[1]) for s in segs if s[1] == s[3]]

    def covered(x0, x1, y):
        return any(a <= x0 and x1 <= b and yy == y for a, b, yy in hor)

    out = []
    for x0 in sorted(vert):
        x1 = min((x for x in vert if x > x0), default=None)
        if x1 is not None and covered(x0, x1, 0.0) and covered(x0, x1, depth):
            out.append((x0, x1))
    return out


def census(dxf_path):
    import ezdxf  # noqa: PLC0415  (only this function reads the drawing)
    doc = ezdxf.readfile(dxf_path)
    rows = []
    with open(CENSUS, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["KIND"] not in ("DOOR", "GATE", "ARCH"):
                continue
            h = (r["HANDLES"] or "").split()
            if len(h) != 1:
                rows.append({"opening": r["ID"], "kind": r["KIND"], "handle": " ".join(h), "entity": "",
                             "evidence": "no single plan symbol handle"})
                continue
            e = doc.entitydb.get(h[0])
            if e is None:
                raise SystemExit(f"{r['ID']}: handle {h[0]} not in the drawing (wrong file?)")
            row = {"opening": r["ID"], "kind": r["KIND"], "handle": h[0], "entity": e.dxftype()}
            if e.dxftype() != "INSERT":
                rows.append(dict(row, evidence="not a door block: no frame drawn"))
                continue
            sx, sy = e.dxf.xscale, e.dxf.yscale
            if abs(abs(sx) - 1) > 1e-9 or abs(abs(sy) - 1) > 1e-9:
                raise SystemExit(f"{r['ID']}: block scale {sx} {sy} is not +-1")
            segs = [(round(b.dxf.start.x, 3), round(b.dxf.start.y, 3), round(b.dxf.end.x, 3), round(b.dxf.end.y, 3))
                    for b in doc.blocks[e.dxf.name] if b.dxftype() == "LINE"]
            w = max(max(s[0], s[2]) for s in segs)
            depths = sorted({abs(s[3] - s[1]) for s in segs if s[0] == s[2] and min(s[1], s[3]) == 0.0})
            depth = min(depths)                     # the wall depth: the shortest vertical from the wall line
            rects = _rects(segs, depth)
            ends = [x for x in rects if x[0] == 0.0 or x[1] == w]
            post_w = sorted({round(x[1] - x[0], 3) for x in ends})
            closed = len(ends) == 2 and ends[0][0] == 0.0 and ends[-1][1] == w
            m = _masonry(doc.modelspace(), e, w, depth)
            ok_faces = all(v[0] is not None and v[1] is not None for v in m.values())
            offs = [] if not ok_faces else [round(v[0] - 0.0, 1) for v in m.values()] + [round(v[1] - w, 1)
                                                                                        for v in m.values()]
            mw = sorted({round((v[1] - v[0]) / 1000, 3) for v in m.values()}) if ok_faces else []
            at = closed and ok_faces and all(abs(o) <= TOL_MM for o in offs)
            ev = ("block frame posts: closed rectangles over the full wall depth, their outer edges at the drawn masonry "
                  "jambs on both faces: the frame covers the whole jamb reveal" if at else
                  "frame posts not closed at both jambs" if not closed else
                  "masonry jamb not found on both faces" if not ok_faces else
                  "POSITION CONFLICT: the block's frame posts are not at the drawn masonry jambs (block width vs wall gap)")
            rows.append(dict(row, block=e.dxf.name, mirrored=str(sx < 0 or sy < 0), opening_w_m=f"{w / 1000:.3f}",
                             wall_depth_m=f"{depth / 1000:.3f}",
                             post_w_m=" ".join(f"{p / 1000:.3f}" for p in post_w), posts_closed=str(closed),
                             masonry_w_m=" ".join(f"{x + 0.0:.3f}" for x in mw),
                             jamb_offsets_mm=" ".join(f"{o + 0.0:.1f}" for o in offs), frame_at_jambs=str(at),
                             evidence=ev))
    return rows


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS, lineterminator="\n")
    w.writeheader()
    for r in census(argv[0]):
        w.writerow({k: r.get(k, "") for k in COLS})
    sys.stdout.write(buf.getvalue())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
