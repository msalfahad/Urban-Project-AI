"""T-733 DRAWING READ (research, unwired): (a) the ST-02 F1 / F4 junction read on each step-line set, (b) the V-07
third-dome position on the structural slab plan of the 2F roof.

Inputs (Drive "Alsenan chalet project", decoded by `bash scripts/agent_env.sh decode` into .work/private only):
P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55) and "ST7757 dxf.dxf" (sha256 9f9d1179).
Writes T733_DRAWN.json: handles, layers, lengths, areas and counts only (no coordinate, no drawing text, no client name).

    .work/venv/bin/python -I research/agents_t733/t733_extract.py --dxf <P7757.dxf> --st <ST7757.dxf> --write
    .work/venv/bin/python -I research/agents_t733/t733_extract.py --dxf <P7757.dxf> --st <ST7757.dxf>   (re-read, compare)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "T733_DRAWN.json"
ND = 6
U = 0.001                                          # millimetres
M2 = U * U

# ST-02 on the 1F plan (T-727 handles): radial flight F1 lines, highest first, and the straight flight F4 lines
F1_L5 = ["BB9", "BB7", "BB5", "BB3", "BB1", "BAF", "BAD", "BAB", "BA9", "BA7", "BA5", "BA3"]
F1_L2 = ["BBA", "BB8", "BB6", "BB4", "BB2", "BB0", "BAE", "BAC", "BAA", "BA8", "BA6", "BA4"]
F4_L5 = ["B43", "B4A", "B49", "B48", "B47", "B46", "B45", "B44", "B4B", "B4C", "B4D"]
F4_L2 = ["B4E", "B55", "B54", "B53", "B52", "B51", "B50", "B4F", "B56", "B57", "B58"]
ARC_INNER = "B9C"                                  # radial flight centre
OUTLINE = {"inner_stringer": "B76", "void_edge_east": "B75", "arrival_edge": "D24"}
GF_PAIR = ("22F", "234")                           # the same junction pair on the GF plan (T-727)
DOME_2F = "1300"                                   # V-07: 2F plan circle drawn 'above'


def _q(x):
    return round(float(x), ND)


def read(dxf, st):
    import ezdxf
    from shapely.geometry import LineString, Point, Polygon, box
    from shapely.ops import unary_union

    doc = ezdxf.readfile(dxf)
    E = doc.entitydb
    out = {"unit_m": U}

    def seg(h):
        e = E[h]
        assert e.dxftype() == "LINE", (h, e.dxftype())
        return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]

    c = (E[ARC_INNER].dxf.center.x, E[ARC_INNER].dxf.center.y)

    def radial(lines, junction):
        qs = []
        for a, b in zip(lines, lines[1:] + [junction]):
            A = sorted(seg(a), key=lambda p: math.dist(p, c))
            B = sorted(seg(b), key=lambda p: math.dist(p, c))
            qs.append(Polygon([A[0], A[1], B[1], B[0]]))
        return unary_union(qs), qs

    def straight(lines):
        pts = [p for h in lines for p in seg(h)]
        return box(min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))

    readings = {}
    for name, (r, j, s) in {"mixed_engine": (F1_L2, F4_L2[0], F4_L5), "set_layer2": (F1_L2, F4_L2[0], F4_L2),
                            "set_layer5": (F1_L5, F4_L5[0], F4_L5)}.items():
        f1, qs = radial(r, j)
        f4 = straight(s)
        readings[name] = {"F1_m2": _q(f1.area * M2), "F4_m2": _q(f4.area * M2),
                          "overlap_m2": _q(f1.intersection(f4).area * M2), "union_m2": _q(f1.union(f4).area * M2),
                          "sum_m2": _q((f1.area + f4.area) * M2), "F1_first_quad_m2": _q(qs[0].area * M2),
                          "F1_last_quad_m2": _q(qs[-1].area * M2), "F1_quads": len(qs)}
    # pair offsets and layers
    off_straight = sorted({_q(abs(seg(a)[0][0] - seg(b)[0][0]) * U) for a, b in zip(F4_L5, F4_L2)})
    rad_len = {h: _q(math.dist(*seg(h)) * U) for h in (F1_L5[0], F1_L2[0], F1_L5[-1], F1_L2[-1])}
    radii = {h: [_q(math.dist(p, c) * U) for p in sorted(seg(h), key=lambda p: math.dist(p, c))]
             for h in (F1_L5[0], F1_L2[0])}
    # which set ends on the drawn outline (R-T733-2): the far end of F4 against the stringer end / void edge
    stringer, edge = seg(OUTLINE["inner_stringer"]), seg(OUTLINE["void_edge_east"])
    far = {"set_layer2": seg(F4_L2[-1])[0][0], "set_layer5": seg(F4_L5[-1])[0][0]}
    stringer_end_x = max(p[0] for p in stringer)
    edge_x = edge[0][0]
    coincide = {k: abs(x - stringer_end_x) < 1.0 and abs(x - edge_x) < 1.0 for k, x in far.items()}
    gap = {k: _q(abs(x - edge_x) * U) for k, x in far.items()}
    # the same pair drawn on the GF plan
    gf = {h: (E[h].dxf.layer, _q(math.dist(*seg(h)) * U)) for h in GF_PAIR}
    gf_offset = _q(abs(seg(GF_PAIR[0])[0][0] - seg(GF_PAIR[1])[0][0]) * U)
    out["junction"] = {
        "handles": {"F1_layer5": F1_L5, "F1_layer2": F1_L2, "F4_layer5": F4_L5, "F4_layer2": F4_L2,
                    "outline": OUTLINE},
        "layers": {"F1_layer5": sorted({E[h].dxf.layer for h in F1_L5}), "F1_layer2": sorted({E[h].dxf.layer for h in F1_L2}),
                   "F4_layer5": sorted({E[h].dxf.layer for h in F4_L5}), "F4_layer2": sorted({E[h].dxf.layer for h in F4_L2})},
        "pair_offset_straight_m": off_straight,
        "radial_line_lengths_m": rad_len, "radial_top_line_radii_m": radii,
        "readings": readings,
        "far_end_on_outline": coincide, "far_end_gap_to_void_edge_m": gap,
        "gf_plan_pair": gf, "gf_plan_pair_offset_m": gf_offset,
    }

    # ---- (b) V-07 on the structural 2F roof slab plan --------------------------------------------------------------
    sdoc = ezdxf.readfile(st)
    dome = E[DOME_2F]
    cx, cy, r = dome.dxf.center.x, dome.dxf.center.y, dome.dxf.radius

    def cols(d, win=None):
        rs = []
        for e in d.modelspace().query("LWPOLYLINE"):
            try:
                lay = e.dxf.layer
            except Exception:
                continue
            if lay != "S-COL.BON":
                continue
            p = [(a[0], a[1]) for a in e.get_points()]
            if len(p) < 4:
                continue
            b = (min(x for x, _ in p), min(y for _, y in p), max(x for x, _ in p), max(y for _, y in p))
            if win and not (win[0] < b[0] < win[2] and win[1] < b[1] < win[3]):
                continue
            rs.append(b)
        return rs

    A = cols(doc, (cx - 15000, cy - 15000, cx + 15000, cy + 15000))
    S = cols(sdoc)
    votes = Counter()
    for a in A:
        for s in S:
            if round(s[2] - s[0]) == round(a[2] - a[0]) and round(s[3] - s[1]) == round(a[3] - a[1]):
                votes[(round(s[0] - a[0]), round(s[1] - a[1]))] += 1
    (dx, dy), n = votes.most_common(1)[0]
    worst = 0.0
    for a in A:
        best = min(max(abs(s[i] - (a[i] + (dx if i % 2 == 0 else dy))) for i in range(4)) for s in S)
        worst = max(worst, best)
    X, Y = cx + dx, cy + dy
    sheet_cols = [s for s in S if abs(s[0] - X) < 12000 and abs(s[1] - Y) < 12000]
    disc = Point(X, Y).buffer(r, 256)
    inside = Counter()
    beams = []
    outline_pts = []
    for e in sdoc.modelspace():
        try:
            lay = e.dxf.layer
        except Exception:
            continue
        t = e.dxftype()
        try:
            if t == "LINE":
                g = LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
            elif t == "LWPOLYLINE":
                pts = [(a[0], a[1]) for a in e.get_points()]
                g = LineString(pts) if len(pts) > 1 else Point(pts[0])
            elif t in ("CIRCLE", "ARC"):
                g = Point(e.dxf.center.x, e.dxf.center.y).buffer(e.dxf.radius).exterior
            elif t == "HATCH":
                from ezdxf import bbox as _bb
                bb = _bb.extents([e])
                if not bb.has_data:
                    continue
                g = box(bb.extmin.x, bb.extmin.y, bb.extmax.x, bb.extmax.y)
            else:
                continue
        except Exception:
            continue
        if g.distance(Point(X, Y)) > 12000:
            continue
        if lay == "1" and t == "LINE":
            outline_pts.extend(g.coords)
        if g.intersects(disc):
            inside[(t, lay)] += 1
            if lay == "1" and t == "LINE":
                beams.append(_q(g.intersection(disc).length * U))
    sheet = box(min(p[0] for p in outline_pts), min(p[1] for p in outline_pts),
                max(p[0] for p in outline_pts), max(p[1] for p in outline_pts))
    openings_on_sheet = sum(1 for e in sdoc.modelspace() if e.dxftype() in ("LINE", "LWPOLYLINE", "HATCH")
                            and getattr(e.dxf, "layer", None) == "S-OPENING"
                            and _near(e, X, Y, 12000))
    hatches = Counter()
    for e in sdoc.modelspace().query("HATCH"):
        from ezdxf import bbox as _bb
        bb = _bb.extents([e])
        if bb.has_data and abs(bb.center.x - X) < 12000 and abs(bb.center.y - Y) < 12000:
            hatches[e.dxf.layer] += 1
    out["v07"] = {
        "dome_handle": DOME_2F, "dome_layer": dome.dxf.layer, "dome_radius_m": _q(r * U),
        "dome_disc_m2": _q(math.pi * r * r * M2),
        "overlay": {"arch_2F_block_columns": len(A), "matched_st": n, "worst_corner_residual_mm": _q(worst)},
        "st_sheet_columns": len(sheet_cols),
        "st_sheet_beam_line_extent_m": [_q((sheet.bounds[2] - sheet.bounds[0]) * U), _q((sheet.bounds[3] - sheet.bounds[1]) * U)],
        "st_sheet_beam_line_extent_m2": _q(sheet.area * M2),
        "inside_dome_footprint_by_type_layer": {f"{k[0]}/{k[1]}": v for k, v in sorted(inside.items()) if v},
        "beam_lines_crossing_dome": len(beams), "beam_line_lengths_inside_dome_m": sorted(beams),
        "s_opening_entities_on_sheet": openings_on_sheet,
        "hatches_on_sheet_by_layer": dict(sorted(hatches.items())),
        # an opening is an S-OPENING entity, a circle / arc, or a hatch other than a column fill inside the footprint
        "opening_drawn": any(k[1] == "S-OPENING" or k[0] in ("CIRCLE", "ARC")
                             or (k[0] == "HATCH" and k[1] != "S-COL.HAT") for k, v in inside.items() if v),
    }
    return out


def _near(e, X, Y, d):
    try:
        if e.dxftype() == "LINE":
            p = [e.dxf.start, e.dxf.end]
        elif e.dxftype() == "LWPOLYLINE":
            p = [type("P", (), {"x": a[0], "y": a[1]}) for a in e.get_points()]
        else:
            return False
    except Exception:
        return False
    return any(abs(q.x - X) < d and abs(q.y - Y) < d for q in p)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--st", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    got = json.dumps(read(a.dxf, a.st), indent=1, sort_keys=True) + "\n"
    if a.write:
        OUT.write_text(got)
        print(f"wrote {OUT.name}")
        return 0
    same = OUT.read_text() == got
    print("T733_DRAWN.json", "SAME" if same else "DIFFERS")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
