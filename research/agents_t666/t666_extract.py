"""T-666 own drawing read (private input; prints only derived member geometry in m, relative to each member).

Usage (from the checkout root, on the decoded private copy only):
    python3 -I research/agents_t666/t666_extract.py .work/private/<ST dxf>

Reads 'ST7757 dxf.dxf' (Drive 'Alsenan chalet project', read-only, decoded into .work/private) and prints, as JSON:
  (a) for each of the five R-T660-2 unlabelled beam pieces: the drawn edge pair, where each edge starts / ends along the
      piece axis, the faces of the members met at each end (column outline, crossing-band face lines, the outer line),
      and which neighbour line's span covers each 0.20 x 0.20 junction square;
  (b) the foundation-level boundary band (FOUNDATION PLAN closed S-BOUN pair + its hatch) and the building's 0.30 m
      exterior ground beams on the plot line (GROUND BEAMS PLAN, shifted onto the foundation plan by the measured
      frame translation), per stretch: band centre-line length under a building G.B, of it inside footing outlines.
Nothing is written into the repository; the committed READS in t666_alsenan.py are the printed values (m), checked
against this output by the Checker. No absolute coordinates are printed (positions are relative to the member).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t065"))
import foundation_member_census as C  # noqa: E402  (T-065 merged raw DXF reader: load, lw_points, box, union_length)

U = 0.001  # drawing unit mm -> m
GBP_TO_FP_DX = 38724.0  # GROUND BEAMS PLAN -> FOUNDATION PLAN frame translation in x (T-566 measured; checked below)


def _line(e):
    return (float(e.g(10)), float(e.g(20))), (float(e.g(11)), float(e.g(21)))


def pieces(by):
    """(a) the five unlabelled pieces: edges, ends and junction-square owners."""
    def vx(h):  # a vertical edge: x, ymin, ymax
        (x1, y1), (x2, y2) = _line(by[h])
        assert abs(x1 - x2) < 0.5, h
        return x1, min(y1, y2), max(y1, y2)

    def hz(h):  # a horizontal line: y, xmin, xmax
        (x1, y1), (x2, y2) = _line(by[h])
        assert abs(y1 - y2) < 0.5, h
        return y1, min(x1, x2), max(x1, x2)

    def col(h):
        return C.box(C.lw_points(by[h])[0])

    out = {}
    # 2F vertical pieces BAND0008.1 (399 / 39C, column 418), BAND0011.1 (39E / 3A1, column 41E),
    # BAND0006.1 (397 / 3AD, column 424): south end on the outer line 392, south band inner-face lines interrupted.
    south_outer = hz("392")
    south_inner = [hz(h) for h in ("393", "394", "395")]
    for name, (ea, eb, c) in {"BAND0008.1": ("39C", "399", "418"), "BAND0011.1": ("3A1", "39E", "41E"),
                              "BAND0006.1": ("397", "3AD", "424")}.items():
        xa, ya0, _ = vx(ea)
        xb, yb0, _ = vx(eb)
        cb = col(c)
        width = abs(xb - xa)
        start = max(ya0, yb0)
        inner_y = south_inner[0][0]
        covered = [s for s in south_inner if s[1] < (xa + xb) / 2 < s[2]]
        out[name] = {
            "edges": [ea, eb], "drawn_width_m": round(width * U, 4),
            "edges_start_on_outer_line_392": abs(start - south_outer[0]) < 0.5,
            "south_band_inner_face_crosses_piece": bool(covered),
            "south_band_depth_zone_m": round((inner_y - south_outer[0]) * U, 4),
            "column": c, "column_size_m": [round((cb[2] - cb[0]) * U, 3), round((cb[3] - cb[1]) * U, 3)],
            "piece_inside_column_width": cb[0] - 0.5 <= min(xa, xb) and max(xa, xb) <= cb[2] + 0.5,
            "drawn_length_outer_line_to_column_face_m": round((cb[1] - south_outer[0]) * U, 4),
            "near_face_length_inner_face_to_column_face_m": round((cb[1] - inner_y) * U, 4),
        }
    # crossing bands at the column squares: their face lines and where they stop (column faces)
    cross = {}
    for pair, cols in {("398", "3A2"): ("418", "41E"), ("772", "773"): ("424",)}.items():
        ya, xa0, xa1 = hz(pair[0])
        yb, xb0, xb1 = hz(pair[1])
        cross["/".join(pair)] = {"width_m": round(abs(yb - ya) * U, 4),
                                 "square_inside_column": {c: (col(c)[1] - 0.5 <= min(ya, yb) and max(ya, yb)
                                                              <= col(c)[3] + 0.5) for c in cols}}
    out["crossing_bands"] = cross
    # 2F BAND0001.3: north band 38D / 38E past column 415 to the east outer line 39A; east band inner face 39B stops
    # at the north band's inner face 38E (the corner square is drawn inside the north band).
    y_out, x0o, x1o = hz("38D")
    y_in, x0i, x1i = hz("38E")
    xe, ye0, ye1 = vx("39A")
    xei, yei0, yei1 = vx("39B")
    c415 = col("415")
    out["BAND0001.3"] = {
        "edges": ["38D", "38E"], "drawn_width_m": round(abs(y_out - y_in) * U, 4),
        "both_edges_end_on_outer_line_39A": abs(x1o - xe) < 0.5 and abs(x1i - xe) < 0.5,
        "east_band_inner_face_39B_stops_at_38E": abs(yei1 - y_in) < 0.5,
        "drawn_length_column_415_face_to_outer_line_m": round((xe - c415[2]) * U, 4),
        "near_face_length_to_39B_m": round((xei - c415[2]) * U, 4),
        "east_band_drawn_length_outer_south_to_38E_m": round((yei1 - yei0) * U, 4),
    }
    # 1F BAND0005.1: 5C6 / 5E3 from B23's north face 5E1 (B23 5E4 / 5E1 runs through) to column 691
    x6, y60, y61 = vx("5C6")
    x3, y30, y31 = vx("5E3")
    b23n = hz("5E1")
    b23s = hz("5E4")
    c691 = col("691")
    out["BAND0005.1"] = {
        "edges": ["5C6", "5E3"], "drawn_width_m": round(abs(x3 - x6) * U, 4),
        "edges_start_on_B23_face_5E1": abs(min(y60, y30) - b23n[0]) < 0.5,
        "B23_faces_run_through": b23n[1] < min(x6, x3) and max(x6, x3) < b23n[2] and b23s[1] < x6 < b23s[2],
        "B23_width_m": round(abs(b23n[0] - b23s[0]) * U, 4),
        "drawn_length_B23_face_to_column_691_face_m": round((c691[1] - b23n[0]) * U, 4),
    }
    return out


def stretches(ents, blocks, by):
    """(b) foundation band vs building exterior G.B on the plot line."""
    ob = C.box(C.lw_points(by["1658"])[0])
    ib = C.box(C.lw_points(by["1659"])[0])
    half = (ib[0] - ob[0]) / 2
    x0, y0, x1, y1 = ob[0] + half, ob[1] + half, ob[2] - half, ob[3] - half
    # GBP plot outline (7FE outer corner run) must equal the FP outline shifted by GBP_TO_FP_DX
    gbp = C.box(C.lw_points(by["7FE"])[0])
    assert abs(gbp[0] + GBP_TO_FP_DX - ob[0]) < 0.5 and abs(gbp[3] - ob[3]) < 0.5, "frame translation"
    # footing outlines on the foundation plan (the T-065 census logic: unit-square block inserts, closed or open
    # polylines, 4-line rectangles on S-FOOTINGS)
    feet = []
    unit = {n: C.box(C.lw_points(i[0])[0]) for n, i in blocks.items()
            if len(i) == 1 and i[0].type == "LWPOLYLINE" and i[0].g(8) == "S-FOOTINGS"}

    def inplot(x, y):
        return ob[0] - 1 <= x <= ob[2] + 1 and ob[1] - 1 <= y <= ob[3] + 1
    for e in ents:
        if e.type == "INSERT" and e.g(2) in unit:
            cx, cy = float(e.g(10)), float(e.g(20))
            if inplot(cx, cy):
                bx = unit[e.g(2)]
                sx, sy = float(e.g(41, "1")), float(e.g(42, "1"))
                xa, xb = sorted((cx + bx[0] * sx, cx + bx[2] * sx))
                ya, yb = sorted((cy + bx[1] * sy, cy + bx[3] * sy))
                feet.append((xa, ya, xb, yb))
        elif e.type == "LWPOLYLINE" and e.g(8) == "S-FOOTINGS":
            pts, _ = C.lw_points(e)
            if pts and all(inplot(*p) for p in pts):
                feet.append(C.box(pts))
    segs = {}
    for e in ents:
        if e.type == "LINE" and e.g(8) == "S-FOOTINGS":
            p, q = _line(e)
            p, q = (round(p[0]), round(p[1])), (round(q[0]), round(q[1]))
            if inplot(*p) and inplot(*q):
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
            feet.append(C.box(pts))

    def gb_v(ha, hb):  # building G.B along a vertical plot side: (y from, y to) on the FP frame
        (_, a0), (_, a1) = _line(by[ha])
        return min(a0, a1), max(a0, a1)

    def gb_h(ha):
        (b0, _), (b1, _) = _line(by[ha])
        return min(b0, b1) + GBP_TO_FP_DX, max(b0, b1) + GBP_TO_FP_DX
    runs = {  # side, orientation, fixed coordinate of the band centre line, interval along it under the building G.B
        "side 1 lower neighbour, G.B F8 / 7D4": ("h", y0, gb_h("F8")),
        "side 1 lower neighbour, G.B FC / 7D0": ("h", y0, gb_h("FC")),
        "street lower, G.B 136 / 7D5": ("v", x0, gb_v("136", "7D5")),
        "sea lower, G.B FD / 7E0": ("v", x1, gb_v("FD", "7E0")),
    }
    res = {"band_width_m": round(2 * half * U, 3), "centre_line_m": round(2 * ((x1 - x0) + (y1 - y0)) * U, 3),
           "band_hatch_1657": [by["1657"].type, by["1657"].g(8), by["1657"].g(2), by["1657"].g(91)], "runs": {}}
    for k, (o, c, (s, t)) in runs.items():
        lo, hi = (x0, x1) if o == "h" else (y0, y1)
        s, t = max(s, lo), min(t, hi)
        on = []
        for bx in feet:
            if o == "h" and bx[1] <= c <= bx[3]:
                a, b = max(s, bx[0]), min(t, bx[2])
            elif o == "v" and bx[0] <= c <= bx[2]:
                a, b = max(s, bx[1]), min(t, bx[3])
            else:
                continue
            if b > a:
                on.append((a, b))
        inside = C.union_length(on)
        res["runs"][k] = {"centre_line_m": round((t - s) * U, 3), "inside_footings_m": round(inside * U, 3),
                          "free_m": round((t - s - inside) * U, 3)}
    return res


def main(argv=None):
    argv = argv or sys.argv[1:]
    ents, blocks = C.load(argv[0])
    by = {e.g(5): e for e in ents}
    print(json.dumps({"pieces": pieces(by), "band": stretches(ents, blocks, by)}, indent=1))


if __name__ == "__main__":
    main()
