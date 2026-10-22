"""T-159 hand fixture (NOT the development villa): an L-shaped two-storey house with a setback first floor and one
curved side, computed by hand below and checked against t159_sides.

    python3 -I research/agents_t159/check_t159.py --check

Ground floor (metres, plan frame shared by both floors): L-shape (0,0) (12,0) (12,4) (7,4) (7,9) (0,9), the west side
a half-circle bay from (0,9) round to (0,0), centre (0,4.5), radius 4.5 (bulging to -x). First floor (setback):
the rectangle (0,0) (7,0) (7,9) (0,9). Axes: +x E, -x W, +y N, -y S. Levels: outside ground 0.00, GF floor +0.50,
1F floor and GF roof +4.00, GF parapet top +4.60, 1F roof +7.50, 1F parapet top +8.50.

By hand:
  GF sides  S-1 12.000 (FLUSH 7 under the 1F face, EDGE 5)   E-1 4.000 EDGE   N-1 5.000 EDGE   E-2 5.000 FLUSH
            N-2 7.000 FLUSH   W-1 arc pi x 4.5 = 14.137167 (EDGE: the bay has its own roof)       run 47.137167
  GF areas  S-1 7 x 4.00 + 5 x 4.60 = 51.000; E-1 4 x 4.60 = 18.400; N-1 5 x 4.60 = 23.000; E-2 5 x 4.00 = 20.000;
            N-2 7 x 4.00 = 28.000; W-1 4.5 pi x 4.60 = 20.7 pi = 65.030968                      GF 205.430968 m2
  1F sides  S-1 7 (on the GF face: FLUSH below)   E-1 9 (FLUSH 5 over GF E-2, COVERED 4 over the GF roof)
            N-1 7 FLUSH   W-1 9 COVERED (over the bay roof); every 1F side is a roof edge (no 2F)    run 32.000
  1F areas  every side from +4.00 to +8.50 = 4.50: 7 x 4.5 + 9 x 4.5 + 7 x 4.5 + 9 x 4.5 = 144.000      1F 144.000 m2
  House     349.430968 m2
Adversarial: the same house rotated 30 deg and -121 deg, mirrored (facing names swap E <-> W), in millimetres (scaled
in and out), started at another vertex, walked clockwise; mirrored + clockwise + millimetres together; a porch variant (the 1F runs 1.5 m further south over the GF
S side: GF S-1 COVERED 7 + EDGE 5 = 51.000 as before, the 1F S side over open air EDGE below 7 m, its bottom +4.00,
the 1F E side 10.5 m); a missing level -> no area (HELD), never 0; a top below its bottom raises; an empty outline ->
no sides."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import t159_sides as S                                                       # noqa: E402

AX = {"+x": "E", "-x": "W", "+y": "N", "-y": "S"}


def seg(a, b):
    return {"a": list(a), "b": list(b), "len_m": math.hypot(b[0] - a[0], b[1] - a[1]), "straight": True,
            "opening": None}


def arc(a, b, c, r, sweep):
    return {"a": list(a), "b": list(b), "c": list(c), "r": r, "len_m": r * sweep, "straight": False, "opening": None}


def gf():
    p = [(0, 0), (12, 0), (12, 4), (7, 4), (7, 9), (0, 9)]
    es = [seg(p[i], p[i + 1]) for i in range(5)]
    # bay: from (0,9) round to (0,0) through (-4.5,4.5): split in two arcs (as a CAD arc often is)
    es.append(arc((0, 9), (-4.5, 4.5), (0, 4.5), 4.5, math.pi / 2))
    es.append(arc((-4.5, 4.5), (0, 0), (0, 4.5), 4.5, math.pi / 2))
    return es


def f1(porch=False):
    y0 = -1.5 if porch else 0.0
    p = [(0, y0), (7, y0), (7, 9), (0, 9), (0, y0)]
    return [seg(p[i], p[i + 1]) for i in range(4)]


def xform(edges, ang_deg=0.0, mirror=False, scale=1.0, start=0, reverse=False):
    t = math.radians(ang_deg)

    def T(q):
        x, y = q
        if mirror:
            x = -x
        x, y = x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t)
        return [x * scale, y * scale]
    out = []
    for e in edges:
        g = dict(e)
        g["a"], g["b"] = T(e["a"]), T(e["b"])
        g["len_m"] = e["len_m"] * scale
        if not e["straight"]:
            g["c"], g["r"] = T(e["c"]), e["r"] * scale
        out.append(g)
    out = out[start:] + out[:start]
    if reverse:
        out = [dict(e, a=e["b"], b=e["a"]) for e in reversed(out)]
    return out


def floors(g, f, porch=False):
    return [{"name": "GF", "edges": g, "outside": 0.0, "floor": 0.5, "edge_top": 4.6, "next_floor": 4.0},
            {"name": "1F", "edges": f, "outside": None, "floor": 4.0, "edge_top": 8.5, "next_floor": None}]


FAILS = []


def ok(cond, msg):
    if not cond:
        FAILS.append(msg)
    return cond


def near(a, b, tol=1e-6):
    return a is not None and b is not None and abs(a - b) <= tol


def run_case(label, g, f, ax, scale=1.0, porch=False, mirrored=False):
    k = 1.0 / scale
    gm = xform(g, scale=k) if scale != 1.0 else g      # millimetres in -> metres for the tolerances
    fm = xform(f, scale=k) if scale != 1.0 else f
    sg = S.name_sides(S.split_sides(gm, ax))
    sf = S.name_sides(S.split_sides(fm, ax))
    ok(len(sg) == 6, f"{label}: GF {len(sg)} sides, expected 6")
    ok(len(sf) == 4, f"{label}: 1F {len(sf)} sides, expected 4")
    ok(near(sum(s["len_m"] for s in sg), 47.137167), f"{label}: GF run {sum(s['len_m'] for s in sg)}")
    ok(near(sum(s["len_m"] for s in sf), 35.0 if porch else 32.0), f"{label}: 1F run")
    arcs = [s for s in sg if s["kind"] == "ARC"]
    ok(len(arcs) == 1 and near(arcs[0]["len_m"], 4.5 * math.pi), f"{label}: one arc side of pi x 4.5")
    bay = ax["+x"] if mirrored else ax["-x"]          # mirrored: the bay is on the other side, facing the other way
    ok(arcs and arcs[0]["facing"] == bay, f"{label}: arc faces {arcs[0]['facing'] if arcs else None}")
    lens = sorted(round(s["len_m"], 6) for s in sg)
    ok(lens == sorted([12.0, 4.0, 5.0, 5.0, 7.0, round(4.5 * math.pi, 6)]), f"{label}: GF lengths {lens}")
    rows = S.house_facade(floors(gm, fm, porch), ax)
    tot = {fl: sum(r["area_m2"] for r in rows if r["floor"] == fl) for fl in ("GF", "1F")}
    ok(near(tot["GF"], 205.430968), f"{label}: GF area {tot['GF']}")
    ok(near(tot["1F"], 157.5 if porch else 144.0), f"{label}: 1F area {tot['1F']}")
    # the long south side splits 7 / 5 (FLUSH or COVERED / EDGE)
    south = [r for r in rows if r["floor"] == "GF" and near(r["len_m"], 12.0)][0]
    want = "COVERED" if porch else "FLUSH"
    got = {p[0]: round(p[1], 6) for p in south["portions"]}
    ok(got == {want: 7.0, "EDGE": 5.0}, f"{label}: GF south portions {got}")
    if porch:
        s1 = [r for r in rows if r["floor"] == "1F" and near(r["len_m"], 7.0) and r["facing"] == ax["-y"]][0]
        ok(s1["portions"] == [("EDGE/EDGE", 7.0, 4.0, 8.5)] or
           [(p[0], round(p[1], 6), p[2], p[3]) for p in s1["portions"]] == [("EDGE/EDGE", 7.0, 4.0, 8.5)],
           f"{label}: 1F south over open air {s1['portions']}")
    else:
        e1 = [r for r in rows if r["floor"] == "1F" and near(r["len_m"], 9.0) and r["facing"] == (ax["-x"] if mirrored else ax["+x"])][0]
        got = sorted((p[0], round(p[1], 6)) for p in e1["portions"])
        ok(got == [("EDGE/COVERED", 4.0), ("EDGE/FLUSH", 5.0)], f"{label}: 1F east portions {got}")
    return rows


def main():
    g, f = gf(), f1()
    run_case("base", g, f, AX)
    for ang in (30.0, -121.0, 90.0):
        # a rotated plan keeps lengths and areas; facing names follow the rotated axes, so only checked unrotated
        sg = S.split_sides(xform(g, ang), AX)
        ok(near(sum(s["len_m"] for s in sg), 47.137167) and len(sg) == 6, f"rotated {ang}: sides / run")
        rows = S.house_facade(floors(xform(g, ang), xform(f, ang)), AX)
        ok(near(sum(r["area_m2"] for r in rows), 349.430968), f"rotated {ang}: house area")
    run_case("mirrored", xform(g, mirror=True), xform(f, mirror=True), AX, mirrored=True)
    run_case("millimetres", xform(g, scale=1000.0), xform(f, scale=1000.0), AX, scale=1000.0)
    run_case("other start", xform(g, start=3), xform(f, start=2), AX)
    run_case("clockwise", xform(g, reverse=True), xform(f, reverse=True), AX)
    run_case("mirrored + clockwise + millimetres", xform(g, mirror=True, reverse=True, scale=1000.0),
             xform(f, mirror=True, reverse=True, scale=1000.0), AX, scale=1000.0, mirrored=True)
    run_case("porch", g, f1(porch=True), AX, porch=True)
    # missing data
    fl = floors(g, f)
    fl[0]["outside"] = None
    rows = S.house_facade(fl, AX)
    ok(all(r["area_m2"] is None for r in rows if r["floor"] == "GF"), "missing ground level: GF areas must be HELD")
    ok(all(r["area_m2"] is not None for r in rows if r["floor"] == "1F"), "missing ground level: 1F unaffected")
    ok(S.band_area(5.0, [{"bottom": 0.0, "top": None}]) is None, "band with no top -> None, never 0")
    ok(near(S.band_area(5.0, [{"bottom": 0.0, "top": 1.0}, {"bottom": 1.0, "top": 3.5}]), 17.5), "band sum")
    try:
        S.band_area(1.0, [{"bottom": 2.0, "top": 1.0}])
        ok(False, "a top below its bottom must raise")
    except ValueError:
        pass
    ok(S.split_sides([], AX) == [], "empty outline -> no sides")
    # a 0.05 m jog stays a RETURN side of its own (never merged, never dropped)
    p = [(0, 0), (10, 0), (10, 4), (5.05, 4), (5.05, 4.05), (0, 4.05)]
    es = [seg(p[i], p[(i + 1) % len(p)]) for i in range(len(p))]
    sd = S.split_sides(es, AX)
    ok(sum(1 for s in sd if s["kind"] == "RETURN") == 1 and near(sum(s["len_m"] for s in sd), 28.1),
       "jog: one RETURN, run 28.10")
    # an opening on a side stays in the side's length (the run includes openings, UP-FACADE-001)
    es2 = [seg((0, 0), (4, 0)), dict(seg((4, 0), (5.5, 0)), opening="W1|0"), seg((5.5, 0), (10, 0)),
           seg((10, 0), (10, 4)), seg((10, 4), (0, 4)), seg((0, 4), (0, 0))]
    sd2 = S.split_sides(es2, AX)
    ok(len(sd2) == 4 and near(sd2[0]["len_m"] if near(sd2[0]["len_m"], 10.0) else
                              [s for s in sd2 if s["facing"] == "S"][0]["len_m"], 10.0)
       and [s for s in sd2 if s["facing"] == "S"][0]["openings"] == [("W1|0", 1.5)], "opening kept in the side")
    if FAILS:
        print("FAIL")
        for m in FAILS:
            print("  -", m)
        sys.exit(1)
    print("PASS: hand fixture (L-shaped two-storey house, setback, curved bay, porch variant) - rotated, mirrored, "
          "millimetres, re-started, clockwise, missing data")


if __name__ == "__main__":
    if "--check" not in sys.argv:
        print(__doc__)
    main()
