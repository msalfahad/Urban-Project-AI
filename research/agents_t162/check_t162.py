"""T-162 hand fixture (NOT the development villa): `python3 -I research/agents_t162/check_t162.py --check`.

Two-storey box with a set-back, a parapet, 3 openings and 8 external corners, calculated by hand:
  GF 10.00 x 8.00 m, outside ground +-0.00, GF roof (= 1F floor) +4.00, GF parapet top +4.60.
  1F 6.00 x 8.00 m on the west part of the GF: flush on the west, south and north faces, set back 4.00 m on the east;
  1F parapet top +8.50.
  Openings: a door 1.00 x 2.20 (no sill), a window 1.50 x 1.20 (sill), a window 2.00 wide whose height no sheet prints.
By hand:
  GF corners: (0,0) and (0,8) under the 1F (flush): +0.00 -> +4.00 = 4.00 m each; (10,0) and (10,8) roof edge:
  +0.00 -> +4.60 = 4.60 m each.  1F corners: 4 x (+4.00 -> +8.50) = 4 x 4.50.  8 convex corners = 35.20 m.l.
  Parapet outer top edge: GF east 8.00 + the GF roof edge on the south and north 2 x 4.00 = 16.00; 1F 28.00 -> 44.00.
  Reveals: door 1.00 + 2 x 2.20 = 5.40; window 2 x 1.50 + 2 x 1.20 = 5.40; window 3: head + sill 4.00, jambs HELD.
  Measured 35.20 + 44.00 + 5.40 + 5.40 + 4.00 = 94.00 m.l, jambs HELD.
r2 (rework of the Checker's 2026-10-22 rejection): corners are ONE m.l line with four separate figures, never m2:
  physical 94.00 m.l; payable under the freelancer's half convention 47.00 m.l (a payment figure, the physical length
  stays 94.00); amount at the Urban PDF rate 94.00 x 1.25 = 117.50 KWD (= 47.00 x 2.50). Adverse: adding a corner m.l
  line to a plaster m2 total must raise; a HELD length stays None in every figure.
  1F parapet (closed ring 6 x 8, t 0.20, 0.50 high above its roof slab): outer top arris 28.00, inner top arris
  28.00 - 8 x 0.20 = 26.40 m.l, top (28.00 + 26.40) / 2 x 0.20 = 5.44 m2, inner face 26.40 x 0.50 = 13.20 m2;
  54.40 m.l of top arrises = 1.943 per metre of outer run, never 3 (the freelancer's 3 lines per metre).
  Opening arrises composed once over a list: door 1.00 x 2.20 ASSUMED 5.40; window 1.50 x 1.20 5.40; window 2.00 with
  no printed height 4.00 + jambs HELD -> measured 9.40, assumed 5.40; adverse: a 1.20 x 2.00 window with a sill is
  6.40 m.l, never 10.40 (r1's caller added the jambs twice).
Adversarial: rotated 30 / -121 deg, mirrored, millimetres, clockwise walk, a re-started ring, a collinear extra
vertex, an L-shaped ring (one concave corner), a tangent arc fillet (no corner), a non-tangent arc (two corners), a
dropped passage-mouth edge (two MOUTH_END), a missing level (HELD None, never 0), an inconsistent band (raises)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import t162_corners as C                                                     # noqa: E402

TOL = 1e-6


def ring(pts):
    n = len(pts)
    return [{"a": list(pts[i]), "b": list(pts[(i + 1) % n]), "straight": True,
             "len_m": math.dist(pts[i], pts[(i + 1) % n])} for i in range(n)]


def xf(pts, deg=0.0, mirror=False, scale=1.0, reverse=False, start=0):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    out = []
    for x, y in pts:
        if mirror:
            x = -x
        out.append(((x * c - y * s) * scale, (x * s + y * c) * scale))
    if reverse:
        out = out[::-1]
    return out[start:] + out[:start]


def inside(p, poly):
    x, y = p
    r = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            r = not r
    return r


def box_corners(gf, f1, scale, levels):
    """the fixture's corner m.l from the two rings (any frame), with its own band rule: a GF corner under the 1F
    plate ends at the 1F floor, else at the GF parapet top; 1F corners run floor -> parapet top."""
    tot, held, n = 0.0, False, 0
    for fl, pts, up in (("GF", gf, f1), ("1F", f1, None)):
        E = ring(pts)
        for c in C.ring_corners(E):
            assert c["kind"] == "CONVEX", c
            n += 1
            if fl == "GF":
                # probe a little inside the GF, diagonally from the corner
                cx = sum(p[0] for p in pts) / len(pts)
                cy = sum(p[1] for p in pts) / len(pts)
                q = (c["at"][0] + (cx - c["at"][0]) * 0.01, c["at"][1] + (cy - c["at"][1]) * 0.01)
                top = levels["f1"] if inside(q, up) else levels["gf_par"]
                b = (levels["ground"], top)
            else:
                b = (levels["f1"], levels["f1_par"])
            h = C.corner_height(b, b)
            if h is None:
                held = True
            else:
                tot += h
    return n, (None if held else tot)


def check():
    fails = []

    def eq(name, got, want, tol=TOL):
        if got is None or want is None:
            ok = got is None and want is None
        else:
            ok = abs(got - want) <= tol
        print(("PASS " if ok else "FAIL ") + f"{name}: got {got} want {want}")
        if not ok:
            fails.append(name)

    gf = [(0, 0), (10, 0), (10, 8), (0, 8)]
    f1 = [(0, 0), (6, 0), (6, 8), (0, 8)]
    lv = {"ground": 0.00, "f1": 4.00, "gf_par": 4.60, "f1_par": 8.50}
    variants = [dict(), dict(deg=30), dict(deg=-121, mirror=True), dict(scale=1000.0), dict(reverse=True),
                dict(start=2), dict(deg=90, mirror=True, reverse=True, start=1)]
    for v in variants:
        n, ml = box_corners(xf(gf, **v), xf(f1, **v), v.get("scale", 1.0), lv)
        eq(f"8 corners {v}", float(n), 8.0)
        eq(f"vertical corners m.l {v}", ml, 35.20)
    # collinear extra vertex on the GF south face: still 4 corners
    eq("collinear vertex is not a corner", float(len(C.ring_corners(ring([(0, 0), (5, 0), (10, 0), (10, 8), (0, 8)])))),
       4.0)
    # L shape: 5 convex + 1 concave, both walking directions and mirrored
    L = [(0, 0), (12, 0), (12, 4), (7, 4), (7, 9), (0, 9)]
    for v in (dict(), dict(reverse=True), dict(mirror=True, deg=45)):
        k = [c["kind"] for c in C.ring_corners(ring(xf(L, **v)))]
        eq(f"L convex {v}", float(k.count("CONVEX")), 5.0)
        eq(f"L concave {v}", float(k.count("CONCAVE")), 1.0)
    # tangent arc fillet r 1.0 at the (10,0) corner of the GF box: no corner at either arc end
    fil = [{"a": [0, 0], "b": [9, 0], "straight": True, "len_m": 9.0},
           {"a": [9, 0], "b": [10, 1], "straight": False, "c": [9, 1], "r": 1.0, "len_m": math.pi / 2},
           {"a": [10, 1], "b": [10, 8], "straight": True, "len_m": 7.0},
           {"a": [10, 8], "b": [0, 8], "straight": True, "len_m": 10.0},
           {"a": [0, 8], "b": [0, 0], "straight": True, "len_m": 8.0}]
    eq("tangent fillet: 3 corners", float(len(C.ring_corners(fil))), 3.0)
    # non-tangent arc (a bay bulging out of the east face, chord 4, r 2.5): two convex corners at its ends
    sag = 2.5 - math.sqrt(2.5 ** 2 - 2 ** 2)
    half = math.asin(2 / 2.5)
    bay = [{"a": [0, 0], "b": [10, 0], "straight": True, "len_m": 10.0},
           {"a": [10, 0], "b": [10, 2], "straight": True, "len_m": 2.0},
           {"a": [10, 2], "b": [10, 6], "straight": False, "c": [10 - (2.5 - sag), 4], "r": 2.5, "len_m": 2.5 * 2 * half},
           {"a": [10, 6], "b": [10, 8], "straight": True, "len_m": 2.0},
           {"a": [10, 8], "b": [0, 8], "straight": True, "len_m": 10.0},
           {"a": [0, 8], "b": [0, 0], "straight": True, "len_m": 8.0}]
    k = C.ring_corners(bay)
    eq("bay: 6 corners", float(len(k)), 6.0)
    eq("bay end turn (deg)", abs(k[1]["turn_deg"]), math.degrees(half), 1e-4)
    # passage mouth dropped: its two ends are MOUTH_END, no corner across it
    m = C.ring_corners(ring([(0, 0), (4, 0), (5.2, 0), (10, 0), (10, 8), (0, 8)]), drop=(1,))
    eq("mouth ends", float(sum(1 for c in m if c["kind"] == "MOUTH_END")), 2.0)
    # missing level -> HELD, never 0; inconsistent band raises
    n, ml = box_corners(gf, f1, 1.0, dict(lv, ground=None))
    eq("missing ground level -> HELD", ml, None)
    try:
        C.corner_height((0.0, 1.0), (2.0, 3.0))
        fails.append("disjoint bands must raise")
        print("FAIL disjoint bands must raise")
    except ValueError:
        print("PASS disjoint bands raise")
    # parapet outer top edge: GF edges not under the 1F + the whole 1F outline
    par = 8.0 + 2 * 4.0 + 28.0
    eq("parapet top outer m.l", par, 44.0)
    # reveals
    d = C.opening_reveal_ml(1.00, 2.20, False)
    w = C.opening_reveal_ml(1.50, 1.20, True)
    h = C.opening_reveal_ml(2.00, None, True)
    eq("door reveal", d[0], 5.40)
    eq("window reveal", w[0], 5.40)
    eq("window HELD height: head + sill known", h[0], 4.00)
    eq("window HELD height: jambs", h[1], None)
    tot = 35.20 + par + d[0] + w[0] + h[0]
    eq("measured m.l", tot, 94.00)
    # r2 (a): four separate figures, never m2
    ff = C.four_figures(tot)
    eq("physical m.l (unchanged by the half convention)", ff["physical_ml"], 94.00)
    eq("contract m.l (default = physical)", ff["contract_ml"], 94.00)
    eq("payable m.l under the half convention", ff["payable_ml_half_convention"], 47.00)
    eq("amount at 1.25 KWD/m.l", ff["amount_kwd"], 117.50)
    eq("amount = payable x 2.50 KWD/m2 rate", ff["payable_ml_half_convention"] * C.URBAN_PDF_EXT_PLASTER_RATE_KWD_PER_M2,
       ff["amount_kwd"])
    eq("no m2 figure in a corner line", float(sum(1 for k in ff if "m2" in k)), 0.0)
    eq("unit m.l", 1.0 if ff["unit"] == "m.l" else 0.0, 1.0)
    fh = C.four_figures(None)
    eq("HELD corner: payable stays HELD", fh["payable_ml_half_convention"], None)
    eq("HELD corner: amount stays HELD", fh["amount_kwd"], None)
    eq("his contract basis passed explicitly: payable", C.four_figures(None, 1297.35)["payable_ml_half_convention"],
       648.675)
    try:
        C.add_area_m2((100.0, "m2"), (tot, "m.l"))
        fails.append("corners added to m2 must raise")
        print("FAIL corners added to m2 must raise")
    except ValueError:
        print("PASS corners added to m2 raise (adverse)")
    eq("plaster m2 sum", C.add_area_m2((100.0, "m2"), (20.5, "m2")), 120.5)
    eq("plaster m2 sum with a HELD face -> HELD, never 0", C.add_area_m2((100.0, "m2"), (None, "m2")), None)
    # r2 (b): parapet as physical items
    pc = C.parapet_components(28.00, 28.00 - 8 * 0.20, 0.20, 0.50)
    eq("parapet outer top arris", pc["outer_top_arris_ml"], 28.00)
    eq("parapet inner top arris", pc["inner_top_arris_ml"], 26.40)
    eq("parapet top m2", pc["top_m2"], 5.44)
    eq("parapet inner face m2", pc["inner_face_m2"], 13.20)
    eq("top arrises per metre of outer run (never 3)", (pc["outer_top_arris_ml"] + pc["inner_top_arris_ml"]) / 28.00,
       54.40 / 28.00)
    eq("adverse: 3 lines per metre is not the physical count", 1.0 if abs(54.40 / 28.00 - 3.0) > 0.5 else 0.0, 1.0)
    rng = C.parapet_components(10.0, 9.6, 0.20, (0.40, 1.60))["inner_face_m2"]
    eq("held height range: face lo", rng[0], 3.84)
    eq("held height range: face hi", rng[1], 15.36)
    eq("unknown height -> HELD None", C.parapet_components(10.0, 9.6, 0.20, None)["inner_face_m2"], None)
    try:
        C.parapet_components(10.0, 9.6, None, 0.5)
        fails.append("missing thickness must raise")
        print("FAIL missing thickness must raise")
    except ValueError:
        print("PASS missing thickness raises (never 0)")
    # r2: opening arrises composed once (the r1 caller defect)
    ag = C.opening_arrises([("d", 1.00, 2.20, "ASSUMED", False), ("w", 1.50, 1.20, "PRINTED", True),
                            ("w3", 2.00, None, "HELD", True)])
    eq("openings measured", ag["measured"], 9.40)
    eq("openings assumed", ag["assumed"], 5.40)
    eq("openings held ids", float(len(ag["held_ids"])), 1.0)
    eq("adverse: 1.20 x 2.00 window with sill is 6.40, never 10.40",
       C.opening_arrises([("x", 1.20, 2.00, "PRINTED", True)])["measured"], 6.40)
    print(f"\n{'ALL PASS' if not fails else 'FAILED: ' + ', '.join(fails)}")
    return not fails


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(0 if check() else 1)
    print(__doc__)
