"""T-361: read the private architectural DXF by handle -> values-only ALSENAN_FENCE_GATE_INPUT.json (research only).

    python3 -I research/agents_t361/t361_extract.py <P7757.dxf> [--write]

Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55...), kept in .work/private and
never committed. The output holds lengths (m), counts and DXF handles only: no coordinates, no text content, no client
data. Every handle is asserted (type, layer, length) so a drawing revision fails loudly instead of drifting.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "ALSENAN_FENCE_GATE_INPUT.json"
SHA_PREFIX = "ab54dd55"
MM = 0.001


def _line(db, h, layer=None):
    e = db[h]
    if e.dxftype() != "LINE":
        raise SystemExit(f"{h}: {e.dxftype()} (expected LINE)")
    if layer is not None and e.dxf.layer != layer:
        raise SystemExit(f"{h}: layer {e.dxf.layer} (expected {layer})")
    a, b = e.dxf.start, e.dxf.end
    return a, b, math.hypot(b.x - a.x, b.y - a.y) * MM


def _poly_len(db, h, layer):
    e = db[h]
    if e.dxftype() != "LWPOLYLINE" or e.dxf.layer != layer:
        raise SystemExit(f"{h}: {e.dxftype()} on {e.dxf.layer}")
    p = [(q[0], q[1]) for q in e.get_points()]
    return sum(math.hypot(x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in zip(p, p[1:])) * MM, p


def extract(path):
    import ezdxf
    sha = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if not sha.startswith(SHA_PREFIX):
        raise SystemExit(f"unexpected DXF sha256 {sha[:8]} (expected {SHA_PREFIX})")
    doc = ezdxf.readfile(path)
    db = doc.entitydb
    if doc.layers.get("2").dxf.linetype.upper() != "HIDDEN":
        raise SystemExit("layer 2 is not HIDDEN in this revision")

    # ---- street side (GF plan): fence line 10F = gap 110 (HIDDEN) + solid; the solid's free end is cap 10B
    _, _, fence_outer = _line(db, "10F", "5")
    gap_len, gap_pts = _poly_len(db, "110", "2")
    _, _, cap = _line(db, "10B", "5")
    inner_len, inner_pts = _poly_len(db, "13A", "5")
    street_inner = math.hypot(inner_pts[1][0] - inner_pts[0][0], inner_pts[1][1] - inner_pts[0][1]) * MM
    upper_inner = math.hypot(inner_pts[2][0] - inner_pts[1][0], inner_pts[2][1] - inner_pts[1][1]) * MM
    solid_street = fence_outer - gap_len
    # the gap's two ends are the dewaneya corner (fence end 10F) and the solid's end cap 10B
    a10b, _, _ = _line(db, "10B", "5")
    if abs(abs(gap_pts[1][1] - a10b.y)) > 1.0:
        raise SystemExit("gap 110 does not end on the fence end cap 10B")
    # leaf symbols inside the street gap: none of layer D / door blocks may lie in it
    y0, y1 = sorted([gap_pts[0][1], gap_pts[1][1]])
    x_line = gap_pts[0][0]
    # a leaf symbol belongs to the gap when its extents overlap the gap's span (not merely touch an end) within 1.2 m
    # of the gap line; a door of the building wall that only meets the gap's end point (dewaneya door 15E) does not
    from ezdxf import bbox
    leaves_in_gap, near_but_outside = [], []
    for e in doc.modelspace():
        is_leaf = (e.dxftype() == "INSERT" and e.dxf.name.upper().startswith("D")) or \
                  (e.dxftype() in ("LINE", "ARC", "LWPOLYLINE") and e.dxf.layer == "D")
        if not is_leaf:
            continue
        bb = bbox.extents([e])
        if not bb.has_data or bb.extmax.x < x_line - 1200 or bb.extmin.x > x_line + 1200:
            continue
        overlap = min(bb.extmax.y, y1) - max(bb.extmin.y, y0)
        if overlap > 50:
            leaves_in_gap.append(e.dxf.handle)
        elif overlap > -100:
            near_but_outside.append(e.dxf.handle)

    # ---- upper neighbour side (outer lines 99 + 98, inner 13A second leg)
    _, _, up99 = _line(db, "99", "5")
    _, _, up98 = _line(db, "98", "5")

    # ---- lower neighbour short fence between the annex and the main house (outer 86, inner 106)
    _, _, low86 = _line(db, "86", "5")
    _, _, low106 = _line(db, "106", "5")

    # ---- sea side: gate block 2D8 (D120), zone 8E, wall 8D, column 2F94 face, leaf-symbol polylines 39D / 39E
    g = db["2D8"]
    if g.dxftype() != "INSERT" or g.dxf.name != "D120":
        raise SystemExit("2D8 is not the D120 door block")
    blk = doc.blocks.get("D120")
    jambs = [e for e in blk if e.dxftype() == "LINE" and e.dxf.layer == "D"]
    xs = sorted({round(v, 1) for e in jambs for v in (e.dxf.start.x, e.dxf.end.x)})
    block_width = (xs[-1] - xs[0]) * MM
    arc = next(e for e in blk if e.dxftype() == "ARC")
    leaf_r = arc.dxf.radius * MM
    _, _, sea8e = _line(db, "8E", "5")
    _, _, sea8d = _line(db, "8D", "5")
    a8d, b8d, _ = _line(db, "8D", "5")
    # element from the column face 2F94 (top) to the upper plot corner (98 end)
    col = db["2F96"]
    col_y = max(q[1] for q in col.get_points())
    corner_y = db["98"].dxf.start.y
    sea_element = abs(corner_y - col_y) * MM

    # ---- SE elevation: the sea gate seen through the side passage (leaf 23F1 / 23F2 + knob 23F6, frame 23F4 / 23F3,
    # head 23F8, court line 23E5)
    _, _, se_leaf_h = _line(db, "23F1", "5")
    _, _, se_leaf_h2 = _line(db, "23F2", "5")
    a1, _, _ = _line(db, "23F1", "5")
    a2, _, _ = _line(db, "23F2", "5")
    se_leaf_w = abs(a2.x - a1.x) * MM
    f1, _, _ = _line(db, "23F4", "5")
    f2, _, _ = _line(db, "23F3", "5")
    se_frame_w = abs(f2.x - f1.x) * MM
    hd, _, _ = _line(db, "23F8", "5")
    court, _, _ = _line(db, "23E5", "5")
    se_head_h = (hd.y - court.y) * MM
    jt, jb, se_wall_h = _line(db, "23F4", "5")
    knob = db["23F6"].dxftype()

    # ---- NW elevation: pier 2880 / 2881, panel top 27FA, panel end 27EA / 27EB, ground 27F1
    p1, _, _ = _line(db, "2880", "5")
    p2, _, _ = _line(db, "2881", "5")
    nw_pier = abs(p2.x - p1.x) * MM
    t1, t2, nw_panel_w = _line(db, "27FA", "5")
    gr, _, _ = _line(db, "27F1", "5")
    nw_panel_h = (t1.y - gr.y) * MM
    e1, _, _ = _line(db, "27EA", "1")
    e2, _, _ = _line(db, "27EB", "1")
    nw_end = abs(e2.x - e1.x) * MM

    # ---- entrance stair ST-03 open side (layer 5 edge 368 = flight side, 367 = top strip) vs wall side 15A / 158
    _, _, st3_side = _line(db, "368", "5")
    _, _, st3_top = _line(db, "367", "5")
    w1, _, _ = _line(db, "15A", "1")
    w2, _, _ = _line(db, "158", "1")
    st3_wall_t = abs(w1.y - w2.y) * MM

    # ---- elevation railing posts (two close vertical lines each) under the NW and SE top rails
    def post_lines(top_h):
        t = db[top_h]
        y = t.dxf.start.y
        xa, xb = sorted([t.dxf.start.x, t.dxf.end.x])
        xs_ = []
        for e in doc.modelspace().query("LINE"):
            a, b = e.dxf.start, e.dxf.end
            if abs(a.x - b.x) < 1 and xa - 10 <= a.x <= xb + 10 and y - 150 <= max(a.y, b.y) <= y + 5 \
                    and abs(a.y - b.y) >= 150:
                xs_.append((a.x - xa, e.dxf.handle))
        return sorted(xs_), (xb - xa) * MM

    nw_posts, nw_rail = post_lines("279F")
    se_posts, se_rail = post_lines("223C")

    # ---- glass: hatch pattern census (no glass pattern) + window layer W only in openings
    from collections import Counter
    hatch = Counter(e.dxf.pattern_name for e in doc.modelspace().query("HATCH"))

    r = lambda v: round(v, 4)  # noqa: E731
    return {
        "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf sha256 " + sha[:16] + "...",
        "unit": "m",
        "street": {"fence_line_outer_10F": r(fence_outer), "gap_110_hidden": r(gap_len), "solid": r(solid_street),
                   "end_cap_10B": r(cap), "inner_face_13A_street_leg": r(street_inner),
                   "leaf_symbols_in_gap": leaves_in_gap, "leaf_symbols_at_gap_end_outside": near_but_outside},
        "upper_neighbour": {"outer_99_98": r(up99 + up98), "inner_13A_leg": r(upper_inner)},
        "lower_neighbour_short": {"outer_86": r(low86), "inner_106": r(low106)},
        "sea": {"gate_block_2D8": "D120", "gate_block_width": r(block_width), "gate_leaf_swing_radius": r(leaf_r),
                "zone_8E": r(sea8e), "solid_8D": r(sea8d), "element_column_face_to_corner": r(sea_element)},
        "se_elevation_sea_gate": {"leaf_w_23F1_23F2": r(se_leaf_w), "leaf_h": r(se_leaf_h),
                                  "leaf_h_check": r(se_leaf_h2), "knob_23F6": knob, "frame_w_23F4_23F3": r(se_frame_w),
                                  "head_23F8_above_court_23E5": r(se_head_h), "frame_line_h_23F4": r(se_wall_h)},
        "nw_elevation_sea_gate_zone": {"pier_2880_2881": r(nw_pier), "panel_27FA": r(nw_panel_w),
                                       "panel_h_above_27F1": r(nw_panel_h), "end_27EA_27EB": r(nw_end)},
        "st03": {"open_side_368": r(st3_side), "top_strip_367": r(st3_top), "wall_side_15A_158_thickness": r(st3_wall_t)},
        "posts": {"nw_top_rail_279F": r(nw_rail), "nw_vertical_lines": [[round(x * MM, 3), h] for x, h in nw_posts],
                  "se_top_rail_223C": r(se_rail), "se_vertical_lines": [[round(x * MM, 3), h] for x, h in se_posts]},
        "hatch_patterns": dict(sorted(hatch.items())),
    }


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    data = extract(argv[1])
    text = json.dumps(data, indent=1, ensure_ascii=True) + "\n"
    if "--write" in argv:
        OUT.write_text(text)
        print(f"wrote {OUT.name}")
    else:
        same = OUT.exists() and OUT.read_text() == text
        print("committed input reproduces" if same else "DIFFERS from the committed input")
        print(text)
        return 0 if same else 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
