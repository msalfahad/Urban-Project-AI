"""T-074 hand-table helper: membrane strips of a 1.00 m roll laid as in the owner's worked kitchen example (Q-30 answer,
2026-10-19) on any floor outline. Not engine code and read by no method: it states the hand method the T-074 table used so
the engine's cutting plan (waterproofing_system.cutting_plan, UP-WP-LAY-001) can be compared with it.

Method (owner's words in short, Q-30): roll 1.00 m x 10.00 m; 0.10 m side lap; 0.20 m wall upturn folded from the same
strip. Across the span: the first strip covers 1.00 - 0.20 = 0.80 m of floor, each next full strip 1.00 - 0.10 = 0.90 m,
the last strip is cut to (remaining floor + 0.10 lap + 0.20 upturn); a span of 0.60 m or less takes one strip of
span + 0.40 m. Each strip is as long as the outline inside its band + 0.20 + 0.20 (upturn at both ends). Cut membrane =
sum of strip width x length; rolls if alone = ceil(cut / 10.00 m2) (the owner's count); offcut = rolls x 10 - cut.
The strips run along the room's longest wall (x) or across it (y); no rule fixes which, so both are reported (Lead
2026-10-19 14:55). Corner reinforcement, drain detailing and manufacturer laps are not included (owner's note).

Usage: python3 -I research/agents_t074/strip_layout.py   (runs the self-test: the owner's example and the edge cases)
"""
import math

from shapely import affinity
from shapely.geometry import Polygon, box

ROLL_W, ROLL_L, LAP, UP = 1.00, 10.00, 0.10, 0.20


def strips(poly, axis="x"):
    cs = list(poly.exterior.coords)
    best = max(range(len(cs) - 1), key=lambda i: math.dist(cs[i], cs[i + 1]))
    ang = math.degrees(math.atan2(cs[best + 1][1] - cs[best][1], cs[best + 1][0] - cs[best][0]))
    p = affinity.rotate(poly, -ang, origin=(0, 0))
    if axis == "y":
        p = affinity.rotate(p, 90, origin=(0, 0))
    x0, y0, x1, y1 = p.bounds
    span = y1 - y0
    if span + 2 * UP <= ROLL_W + 1e-9:
        bands = [(0.0, span, span + 2 * UP)]
    else:
        covered = ROLL_W - UP
        bands = [(0.0, covered, ROLL_W)]
        while True:
            need = span - covered
            if need + LAP + UP <= ROLL_W + 1e-9:
                bands.append((covered, span, need + LAP + UP))
                break
            bands.append((covered, covered + ROLL_W - LAP, ROLL_W))
            covered += ROLL_W - LAP
    rows = []
    for a, b, w in bands:
        piece = p.intersection(box(x0 - 1, y0 + a, x1 + 1, y0 + b))
        length = 0.0 if piece.is_empty else piece.bounds[2] - piece.bounds[0]
        rows.append({"width_m": round(w, 3), "floor_cover_m": round(max(b - a, 0), 3), "length_m": round(length + 2 * UP, 3)})
    cut = sum(r["width_m"] * r["length_m"] for r in rows)
    rolls = math.ceil(round(cut, 6) / ROLL_L)
    return {"span_across_m": round(span, 3), "n": len(rows), "strips": rows, "cut_m2": round(cut, 3),
            "rolls_by_area": rolls, "offcut_m2": round(rolls * ROLL_L - cut, 3)}


def _key(r):
    return (r["n"], r["cut_m2"], r["rolls_by_area"], tuple((q["width_m"], q["length_m"]) for q in r["strips"]))


def selftest():
    k = strips(box(0, 0, 4, 3), "x")                       # owner's kitchen 3 x 4 m
    assert [q["width_m"] for q in k["strips"]] == [1.0, 1.0, 1.0, 0.7]
    assert [q["floor_cover_m"] for q in k["strips"]] == [0.8, 0.9, 0.9, 0.4]
    assert all(q["length_m"] == 4.4 for q in k["strips"])
    assert (k["cut_m2"], k["rolls_by_area"], k["offcut_m2"]) == (16.28, 2, 3.72)
    k2 = strips(box(0, 0, 4, 3), "y")                      # the other direction: 5 strips x 3.40 m = 16.32 m2
    assert (k2["n"], k2["cut_m2"], k2["rolls_by_area"]) == (5, 16.32, 2)
    for g in (affinity.rotate(box(0, 0, 4, 3), 37, origin=(0, 0)),           # rotated, mirrored, mm scaled to m
              affinity.scale(box(0, 0, 4, 3), -1, 1, origin=(0, 0)),
              affinity.scale(affinity.rotate(box(0, 0, 4000, 3000), 37, origin=(0, 0)), 0.001, 0.001, origin=(0, 0))):
        assert {_key(strips(g, "x")), _key(strips(g, "y"))} == {_key(k), _key(k2)}
    b = strips(box(0, 0, 3, 3), "x")                       # owner's 3 x 3 bathroom picture
    assert (b["n"], b["cut_m2"], b["rolls_by_area"]) == (4, 12.58, 2)
    L = strips(Polygon([(0, 0), (3, 0), (3, 1.5), (1.5, 1.5), (1.5, 3), (0, 3)]), "x")   # L-shape: shorter strips
    assert L["cut_m2"] < b["cut_m2"]
    n = strips(box(0, 0, 2, 0.5), "x")                     # 0.50 m wide: one 0.90 m strip
    assert n["n"] == 1 and n["strips"][0]["width_m"] == 0.9
    return "strip layout self-test OK"


if __name__ == "__main__":
    print(selftest())
