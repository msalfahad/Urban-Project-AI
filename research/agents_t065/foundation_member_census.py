"""T-065: foundation member census around a plot-edge band (read only, stdlib only).

Usage:
    python3 -I research/agents_t065/foundation_member_census.py <structural.dxf> --outer 1658 --inner 1659

Finds the closed outer / inner band polylines by handle, takes the outer one's box as the plot, and lists every
footing outline inside it: INSERTs of a block whose geometry is a unit square on the footing layer (scaled by the
insert's X / Y scale), closed AND open LWPOLYLINEs on the footing layer, and closed 4-LINE rectangles on the footing
layer. For each footing it reports the length of the band centre line (mid-way between the outer and inner
polylines) that lies inside it, and per band side: drawn length, length inside footings, inside columns, free length.
Prints no drawing coordinates; sizes in metres, lengths of the band centre line in metres.
No engine code is imported. Development reference only.
"""
import argparse
import json
import sys


def pairs(path):
    with open(path, "r", encoding="cp1252", errors="replace") as f:
        lines = f.read().splitlines()
    for i in range(0, len(lines) - 1, 2):
        yield int(lines[i].strip()), lines[i + 1].strip()


class Ent:
    def __init__(self, kind):
        self.type = kind
        self.tags = []

    def g(self, code, default=None):
        for k, v in self.tags:
            if k == code:
                return v
        return default


def load(path):
    section = None
    cur = None
    ents, blocks, blk = [], {}, None
    for c, v in pairs(path):
        if c == 0:
            if cur is not None:
                if section == "ENTITIES":
                    ents.append(cur)
                elif section == "BLOCKS" and blk is not None and cur.type not in ("BLOCK", "ENDBLK"):
                    blocks[blk].append(cur)
                cur = None
            if v == "SECTION":
                section = "?"
                continue
            if v == "ENDSEC":
                section = None
                continue
            if section in ("ENTITIES", "BLOCKS"):
                cur = Ent(v)
                if v == "ENDBLK":
                    blk = None
            continue
        if section == "?" and c == 2:
            section = v
            continue
        if cur is not None:
            cur.tags.append((c, v))
            if cur.type == "BLOCK" and c == 2:
                blk = v
                blocks.setdefault(v, [])
    return ents, blocks


def lw_points(e):
    xs = [float(v) for k, v in e.tags if k == 10]
    ys = [float(v) for k, v in e.tags if k == 20]
    closed = (int(e.g(70, "0")) & 1) == 1
    return list(zip(xs, ys)), closed


def box(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def union_length(intervals):
    total, cur = 0.0, None
    for a, b in sorted(intervals):
        if cur and a <= cur[1]:
            cur[1] = max(cur[1], b)
        else:
            if cur:
                total += cur[1] - cur[0]
            cur = [a, b]
    if cur:
        total += cur[1] - cur[0]
    return total


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("--outer", required=True)
    ap.add_argument("--inner", required=True)
    ap.add_argument("--footing-layer", default="S-FOOTINGS")
    ap.add_argument("--column-layer", default="S-COL.BON")
    ap.add_argument("--unit-m", type=float, default=0.001)
    a = ap.parse_args(argv)
    ents, blocks = load(a.dxf)
    by_handle = {e.g(5): e for e in ents}
    ob = box(lw_points(by_handle[a.outer])[0])
    ib = box(lw_points(by_handle[a.inner])[0])
    width = ib[0] - ob[0]
    off = width / 2.0
    ring = (ob[0] + off, ob[1] + off, ob[2] - off, ob[3] - off)

    def inside_plot(x, y):
        return ob[0] - 1 <= x <= ob[2] + 1 and ob[1] - 1 <= y <= ob[3] + 1

    unit_square_blocks = set()
    for name, items in blocks.items():
        polys = [i for i in items if i.type == "LWPOLYLINE" and i.g(8) == a.footing_layer]
        if len(items) == 1 and len(polys) == 1:
            bx = box(lw_points(polys[0])[0])
            unit_square_blocks.add((name, bx))
    footings = []
    for e in ents:
        if e.type == "INSERT":
            for name, bx in unit_square_blocks:
                if e.g(2) == name:
                    cx, cy = float(e.g(10)), float(e.g(20))
                    if not inside_plot(cx, cy):
                        continue
                    sx, sy = float(e.g(41, "1")), float(e.g(42, "1"))
                    # a mirrored insert has a negative scale: normalise the box (T-065 self-test case 2)
                    xa, xb = sorted((cx + bx[0] * sx, cx + bx[2] * sx))
                    ya, yb = sorted((cy + bx[1] * sy, cy + bx[3] * sy))
                    footings.append((e.g(5), "block %s on layer %s" % (name, e.g(8)), (xa, ya, xb, yb)))
        elif e.type == "LWPOLYLINE" and e.g(8) == a.footing_layer:
            pts, closed = lw_points(e)
            if pts and all(inside_plot(x, y) for x, y in pts):
                footings.append((e.g(5), "polyline %s" % ("closed" if closed else "open"), box(pts)))
    # closed 4-LINE rectangles on the footing layer
    lines = [e for e in ents if e.type == "LINE" and e.g(8) == a.footing_layer]
    segs = {}
    for e in lines:
        p = (round(float(e.g(10))), round(float(e.g(20))))
        q = (round(float(e.g(11))), round(float(e.g(21))))
        if inside_plot(*p) and inside_plot(*q):
            segs[e.g(5)] = (p, q)
    used = set()
    for h, (p, q) in segs.items():
        if h in used:
            continue
        chain, pts, end = [h], [p, q], q
        for _ in range(3):
            nxt = [k for k, (r, s) in segs.items() if k not in chain and r == end]
            if not nxt:
                break
            chain.append(nxt[0])
            end = segs[nxt[0]][1]
            pts.append(end)
        if len(chain) == 4 and end == p:
            used.update(chain)
            footings.append((chain[0], "4 lines %s-%s" % (chain[0], chain[-1]), box(pts)))
    columns = []
    for e in ents:
        if e.type == "LWPOLYLINE" and e.g(8) == a.column_layer:
            pts, closed = lw_points(e)
            if pts and all(inside_plot(x, y) for x, y in pts):
                columns.append(box(pts))
    x0, y0, x1, y1 = ring
    sides = [("side 1 (y = min)", "h", y0, x0, x1), ("side 2 (x = max)", "v", x1, y0, y1),
             ("side 3 (y = max)", "h", y1, x0, x1), ("side 4 (x = min)", "v", x0, y0, y1)]

    def cover(bx, side):
        _, o, c, lo, hi = side
        if o == "h" and bx[1] <= c <= bx[3]:
            s, t = max(lo, bx[0]), min(hi, bx[2])
        elif o == "v" and bx[0] <= c <= bx[2]:
            s, t = max(lo, bx[1]), min(hi, bx[3])
        else:
            return None
        return (s, t) if t > s else None

    u = a.unit_m
    out = {"band_width_m": round(width * u, 3), "centre_line_m": round(2 * ((x1 - x0) + (y1 - y0)) * u, 3),
           "band_area_m2": round(((ob[2] - ob[0]) * (ob[3] - ob[1]) - (ib[2] - ib[0]) * (ib[3] - ib[1])) * u * u, 3),
           "footings": [], "sides": []}
    for h, kind, bx in footings:
        on = [c for c in (cover(bx, s) for s in sides) if c]
        out["footings"].append({"handle": h, "kind": kind, "size_m": [round((bx[2] - bx[0]) * u, 3),
                                round((bx[3] - bx[1]) * u, 3)],
                                "centre_line_inside_m": round(sum(t - s for s, t in on) * u, 3)})
    tot = {"drawn": 0.0, "footings": 0.0, "columns": 0.0, "either": 0.0}
    for s in sides:
        fi = [c for c in (cover(bx, s) for _, _, bx in footings) if c]
        ci = [c for c in (cover(bx, s) for bx in columns) if c]
        row = {"side": s[0], "drawn_m": (s[4] - s[3]) * u, "in_footings_m": union_length(fi) * u,
               "in_columns_m": union_length(ci) * u, "in_either_m": union_length(fi + ci) * u}
        row["free_m"] = row["drawn_m"] - row["in_either_m"]
        for k in tot:
            tot[k] += row["drawn_m" if k == "drawn" else "in_%s_m" % k]
        out["sides"].append({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()})
    out["totals_m"] = {k: round(v, 3) for k, v in tot.items()}
    out["totals_m"]["free"] = round(tot["drawn"] - tot["either"], 3)
    json.dump(out, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
