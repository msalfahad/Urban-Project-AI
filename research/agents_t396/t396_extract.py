"""T-396: read the private architectural DXF by handle -> values-only ALSENAN_FENCE_INPUT.json (research only).

    python3 -I research/agents_t396/t396_extract.py <P7757.dxf> [--write]

Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55...), kept in .work/private and
never committed. The output holds lengths / heights (m), counts and DXF handles only: no coordinates, no text content,
no client data. Every handle is asserted (type, layer, length) so a drawing revision fails loudly.

What it reads (built on merged T-361 / T-253 handles, re-read here, not copied):
  GF plan, plot-line bands on layer 5: north 99 + 98, street 10F (gate gap 110 on HIDDEN layer 2, end cap 10B),
  inner polyline 13A (street and north inner legs), lower-neighbour passage closure 86 / 106, sea line 8D + 8E,
  sea column S-COL.BON 2F96 and the wall end 39F.
  Elevations (NW / SE): the 0.20 fence-end lines 27EA / 27EB and 23DD / 23DF, their top lines 27F3 / 23E6, the
  '+-0.00' level blocks 2A43 / 2439 and the court lines 27F1 / 23E5: the drawn top of the fence end above +-0.00.
  Cross-trade guard: every layer-1 (wall) LINE parallel to a fence band face within 0.25 m and overlapping it.
  Column census: structural columns (S-COL.BON) and layer-D rectangles lying inside each 0.20 fence band.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "ALSENAN_FENCE_INPUT.json"
SHA_PREFIX = "ab54dd55"
MM = 0.001


def _line(db, h, layer=None):
    e = db[h]
    if e.dxftype() != "LINE":
        raise SystemExit(f"{h}: {e.dxftype()} (expected LINE)")
    if layer is not None and e.dxf.layer != layer:
        raise SystemExit(f"{h}: layer {e.dxf.layer} (expected {layer})")
    a, b = e.dxf.start, e.dxf.end
    return (a.x, a.y), (b.x, b.y), math.hypot(b.x - a.x, b.y - a.y) * MM


def _poly(db, h, layer):
    e = db[h]
    if e.dxftype() != "LWPOLYLINE" or e.dxf.layer != layer:
        raise SystemExit(f"{h}: {e.dxftype()} on {e.dxf.layer}")
    return [(q[0], q[1]) for q in e.get_points()]


def _seg_len(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1]) * MM


def _level_y(db, h):
    e = db[h]
    if e.dxftype() != "INSERT" or e.dxf.name != "level":
        raise SystemExit(f"{h}: not a 'level' block")
    texts = [x.dxf.text for x in e.doc.blocks[e.dxf.name] if x.dxftype() == "TEXT"]
    if texts != ["%%p0.00"]:
        raise SystemExit(f"{h}: level block text {texts} (expected +-0.00)")
    return e.dxf.insert.y


def _wall_overlaps(msp, a, b, tol=250.0, min_overlap=50.0):
    """layer-1 LINEs parallel to segment a-b, within tol (mm) of its line, overlapping it by more than min_overlap."""
    ax, ay = a
    bx, by = b
    L = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / L, (by - ay) / L
    hits = []
    for e in msp.query("LINE[layer=='1']"):
        s, t = e.dxf.start, e.dxf.end
        vx, vy = t.x - s.x, t.y - s.y
        lv = math.hypot(vx, vy)
        if lv < 1:
            continue
        if abs(vx / lv * uy - vy / lv * ux) > 0.01:      # not parallel
            continue
        d = abs((s.x - ax) * uy - (s.y - ay) * ux)
        if d > tol:
            continue
        p0 = (s.x - ax) * ux + (s.y - ay) * uy
        p1 = (t.x - ax) * ux + (t.y - ay) * uy
        ov = min(max(p0, p1), L) - max(min(p0, p1), 0.0)
        if ov > min_overlap:
            hits.append((e.dxf.handle, round(ov * MM, 4), round(d * MM, 4)))
    return hits


def extract(path):
    import ezdxf
    sha = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if not sha.startswith(SHA_PREFIX):
        raise SystemExit(f"unexpected DXF sha256 {sha[:8]} (expected {SHA_PREFIX})")
    doc = ezdxf.readfile(path)
    db = doc.entitydb
    msp = doc.modelspace()
    if doc.layers.get("2").dxf.linetype.upper() != "HIDDEN":
        raise SystemExit("layer 2 is not HIDDEN in this revision")

    # ---- north (upper neighbour): outer 99 + 98 collinear, inner leg of 13A
    a99, b99, l99 = _line(db, "99", "5")
    a98, b98, l98 = _line(db, "98", "5")
    if abs(a99[1] - a98[1]) > 0.5 or abs(b98[0] - a99[0]) > 0.5:
        raise SystemExit("99 / 98 not one collinear outer line")
    p13a = _poly(db, "13A", "5")
    if len(p13a) != 3:
        raise SystemExit("13A: expected 3 vertices")
    street_inner = _seg_len(p13a[0], p13a[1])
    north_inner = _seg_len(p13a[1], p13a[2])
    # ---- street: outer 10F = HIDDEN gap 110 + solid; cap 10B ends the solid
    a10f, b10f, l10f = _line(db, "10F", "5")
    p110 = _poly(db, "110", "2")
    gap = _seg_len(p110[0], p110[-1])
    _, _, cap = _line(db, "10B", "5")
    # ---- lower neighbour: passage closure 86 / 106 (two faces 0.20 apart)
    a86, b86, l86 = _line(db, "86", "5")
    a106, b106, l106 = _line(db, "106", "5")
    t_lower = abs(a86[1] - a106[1]) * MM
    # ---- sea: 8D + 8E on one outer line; column 2F96 face to the 8D start; 39F at the 8D start
    a8d, b8d, l8d = _line(db, "8D", "5")
    a8e, b8e, l8e = _line(db, "8E", "5")
    if abs(a8d[0] - a8e[0]) > 0.5 or abs(b8d[1] - a8e[1]) > 0.5:
        raise SystemExit("8D / 8E not one collinear line")
    col = _poly(db, "2F96", "S-COL.BON")
    col_face_y = max(p[1] for p in col)
    a39f, _, _ = _line(db, "39F", "D")
    end_piece = (a8d[1] - col_face_y) * MM
    if abs(a39f[1] - a8d[1]) > 0.5:
        raise SystemExit("39F is not at the 8D start")
    # sea and north outer lines meet at the plot corner
    if abs(b8e[1] - a98[1]) > 0.5 or abs(a8d[0] - a98[0]) > 0.5:
        raise SystemExit("sea line and north line do not meet at one corner")

    # ---- elevations: fence end 0.20 wide, top above the +-0.00 level block and above the court line
    def end_view(left, right, top, level, court):
        al, bl, ll = _line(db, left, "1")
        ar, br, lr = _line(db, right, "1")
        at, bt, lt = _line(db, top, "1")
        y0 = _level_y(db, level)
        ac, _, _ = _line(db, court, "5")
        ytop = max(bl[1], al[1])
        if abs(max(br[1], ar[1]) - ytop) > 0.5 or abs(at[1] - ytop) > 0.5:
            raise SystemExit(f"{left}/{right}/{top}: tops disagree")
        return {"handles": [left, right, top, level, court], "width_m": round(lt, 4),
                "top_above_pm000_m": round((ytop - y0) * MM, 4),
                "top_above_court_m": round((ytop - ac[1]) * MM, 4),
                "court_above_pm000_m": round((ac[1] - y0) * MM, 4),
                "lines_below_pm000_m": [round((y0 - min(al[1], bl[1])) * MM, 4), round((y0 - min(ar[1], br[1])) * MM, 4)]}

    nw = end_view("27EA", "27EB", "27F3", "2A43", "27F1")
    se = end_view("23DD", "23DF", "23E6", "2439", "23E5")

    # ---- cross-trade guard: layer-1 wall lines on the fence bands
    guards = {
        "north_outer_99_98": _wall_overlaps(msp, a99, b98),
        "north_inner_13A": _wall_overlaps(msp, p13a[1], p13a[2]),
        "street_outer_10F": _wall_overlaps(msp, a10f, b10f),
        "street_inner_13A": _wall_overlaps(msp, p13a[0], p13a[1]),
        "lower_86": _wall_overlaps(msp, a86, b86),
        "lower_106": _wall_overlaps(msp, a106, b106),
        "sea_8D": _wall_overlaps(msp, a8d, b8d),
        "sea_8E": _wall_overlaps(msp, a8e, b8e),
    }
    # ---- columns drawn in the bands: structural columns (S-COL.BON) and layer-D rectangles, by band
    from ezdxf import bbox as _bbox
    bands = {
        "north": (b99[0], a98[0], p13a[1][1], a99[1]),
        "street": (a10f[0], p13a[0][0], p13a[0][1], b10f[1]),
        "sea": (a8d[0] - 200.0, a8d[0], col_face_y, b8e[1]),        # 0.20 band inward of the outer line
        "lower": (a86[0], b86[0], a86[1], a106[1]),
    }
    inside = {}
    for name, (x0, x1, y0, y1) in bands.items():
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        found = {"S-COL.BON": [], "D_rectangles": []}
        for lay, key in (("S-COL.BON", "S-COL.BON"), ("D", "D_rectangles")):
            for e in msp.query(f"LWPOLYLINE[layer=='{lay}']"):
                bb = _bbox.extents([e])
                if (bb.extmin.x >= x0 - 5 and bb.extmax.x <= x1 + 5 and bb.extmin.y >= y0 - 5 and bb.extmax.y <= y1 + 5):
                    sz = sorted([(bb.extmax.x - bb.extmin.x) * MM, (bb.extmax.y - bb.extmin.y) * MM])
                    if sz[0] > 0.01:
                        found[key].append([e.dxf.handle, round(sz[0], 4), round(sz[1], 4)])
        inside[name] = found
    r = lambda x: round(x, 4)  # noqa: E731
    return {
        "source": f"Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf sha256 {sha[:16]}...",
        "unit": "m",
        "north": {"outer_99_98": r(l99 + l98), "inner_13A_leg": r(north_inner)},
        "street": {"outer_10F": r(l10f), "gate_gap_110": r(gap), "end_cap_10B": r(cap), "inner_13A_leg": r(street_inner)},
        "lower_passage_closure": {"outer_86": r(l86), "inner_106": r(l106), "thickness": r(t_lower)},
        "sea": {"col_face_2F96_to_8D": r(end_piece), "solid_8D": r(l8d), "zone_8E": r(l8e)},
        "elevation_fence_end_nw": nw,
        "elevation_fence_end_se": se,
        "layer1_wall_lines_on_fence_bands": guards,
        "columns_drawn_in_fence_bands": inside,
    }


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    got = extract(argv[0])
    if "--write" in argv:
        OUT.write_text(json.dumps(got, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {OUT.name}")
        return 0
    want = json.loads(OUT.read_text(encoding="utf-8"))
    if got != want:
        print("DIFFERS from the committed input")
        return 1
    print("committed input reproduced")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
