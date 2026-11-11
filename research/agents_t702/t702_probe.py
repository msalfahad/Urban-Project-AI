"""T-702 own probe (c): beam crossings on the GF-07 pantry and GF-14 wash-lobby contours, and the sunken wet panels
over them, read from the architectural plan with the structural first-floor slab plan overlaid.

    bash scripts/agent_env.sh run --tree task-T-702 research/agents_t702/t702_probe.py --arch <P7757.dxf> --st <ST7757.dxf>

Prints only RELATIVE geometry (metres in a room frame whose origin is a named face line's end point), entity handles,
lengths and areas; no absolute coordinate, no drawing text. Overlay: one translation fitted on one column pair (ST
S-COL.BON 35C -> arch S-COL.BON 2FAE, the pantry's north-west column, 1.10 x 0.25 on both) and checked on every other
column outline of the same sheet zone (count matched, worst corner residual).
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import ezdxf
from shapely.geometry import LineString, Polygon, box

ST_COL, AR_COL = "35C", "2FAE"
ST_RADIUS = 12000  # check window: column outlines within 12 m of the anchor column 35C (drawing units, mm)
B27 = ("325", "326")  # ST S-BEAM edge lines of B27 (90 x 85, T-110 BM-GF-048)
B11 = ("28F", "428")  # ST layer-1 edge lines of B11 (20 x 75, T-110 BM-GF-001), north part
PANELS = ("275", "276", "280", "287", "298")  # ST 'Sunken slab.' hatches under 1F wet rooms (T-213)


def corners(e):
    p = list(e.get_points("xy"))
    xs, ys = [q[0] for q in p], [q[1] for q in p]
    return min(xs), max(xs), min(ys), max(ys)


def line_pts(doc, h):
    e = doc.entitydb.get(h)
    return (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)


def fit(st, ar):
    a, c = corners(st.entitydb.get(ST_COL)), corners(ar.entitydb.get(AR_COL))
    dx, dy = c[0] - a[0], c[2] - a[2]
    arc = [corners(e) for e in ar.modelspace().query('LWPOLYLINE[layer=="S-COL.BON"]')]
    n = worst = 0
    for e in st.modelspace().query('LWPOLYLINE[layer=="S-COL.BON"]'):
        s = corners(e)
        if abs(s[0] - a[0]) > ST_RADIUS or abs(s[2] - a[2]) > ST_RADIUS:
            continue
        r = min(arc, key=lambda q: abs(q[0] - s[0] - dx) + abs(q[2] - s[2] - dy))
        err = max(abs(r[0] - s[0] - dx), abs(r[1] - s[1] - dx), abs(r[2] - s[2] - dy), abs(r[3] - s[3] - dy))
        if err <= 2.0:
            n, worst = n + 1, max(worst, err)
    return dx, dy, n, worst


def strip(p1, p2, q1, q2):
    """the beam footprint between two parallel edge lines, extended 1 m beyond the drawn ends on both sides"""
    import math
    ux, uy = p2[0] - p1[0], p2[1] - p1[1]
    L = math.hypot(ux, uy)
    ux, uy = ux / L, uy / L
    ext = lambda p, s: (p[0] + s * ux * 1000, p[1] + s * uy * 1000)  # noqa: E731
    return Polygon([ext(p1, -1), ext(p2, 1), ext(q2, 1), ext(q1, -1)])


def main(argv):
    arch, stp = argv[argv.index("--arch") + 1], argv[argv.index("--st") + 1]
    for name, p in (("arch", arch), ("st", stp)):
        print(name, "sha256", hashlib.sha256(Path(p).read_bytes()).hexdigest()[:8])
    ar, st = ezdxf.readfile(arch), ezdxf.readfile(stp)
    dx, dy, n, worst = fit(st, ar)
    print(f"overlay: {n} ST column outlines matched an arch S-COL.BON outline, worst corner residual {worst:.1f} mm")
    T = lambda p: (p[0] + dx, p[1] + dy)  # noqa: E731

    # ---- GF-07 pantry: frame origin = start of A6 (south face), x east, y north
    o = line_pts(ar, "A6")[0]
    loc = lambda p: (float(p[0] - o[0]) / 1000, float(p[1] - o[1]) / 1000)  # noqa: E731
    for h in ("A6", "AE", "158", "B3"):
        a, b = line_pts(ar, h)
        print(f"  pantry {h} layer {ar.entitydb.get(h).dxf.layer}: {tuple(round(v, 4) for v in loc(a))} -> "
              f"{tuple(round(v, 4) for v in loc(b))}")
    c = corners(ar.entitydb.get(AR_COL))
    col = tuple(round(float(v), 3) for v in ((c[0] - o[0]) / 1000, (c[1] - o[0]) / 1000, (c[2] - o[1]) / 1000,
                                             (c[3] - o[1]) / 1000))
    print("  column 2FAE x0 x1 y0 y1:", col)
    contour = {  # the pantry's full face walk (T-312 / T-128: 10.500 m of faces + the open east edge)
        "west face AE (0 .. column)": ((0, 0), (0, col[2])),
        "column 2FAE south face": ((0, col[2]), (col[1], col[2])),
        "column return": ((col[1], col[2]), (col[1], 4.5)),
        "north wall 158 + door D-GF-06 + wall to the east edge": ((col[1], 4.5), (3.0, 4.5)),
        "south face A6": ((0, 0), (3.0, 0)),
        "east edge B3 (open, layer 5)": ((3.0, 0), (3.0, 4.5)),
    }
    (p1, p2), (q1, q2) = (line_pts(st, B27[0]), line_pts(st, B27[1]))
    fp = strip(*(loc(T(p)) for p in (p1, p2, q1, q2)))
    print("  B27 edges (local):", [tuple(round(v, 4) for v in loc(T(p))) for p in (p1, p2, q1, q2)])
    tot = 0
    for k, (a, b) in contour.items():
        L = LineString([a, b]).intersection(fp).length
        tot += L if "open" not in k else 0
        print(f"    B27 footprint on {k}: {L:.4f} m")
    print(f"  B27 on the pantry's walls: {tot:.6f} m; face walk {sum(LineString([a, b]).length for k, (a, b) in contour.items() if 'open' not in k):.3f} m")
    beam_on = [LineString([a, b]).intersection(fp) for k, (a, b) in contour.items() if "open" not in k]
    room = box(0, 0, 3.0, 4.5)
    for h in PANELS:
        e = st.entitydb.get(h)
        pth = e.paths[0]
        vs = pth.vertices if hasattr(pth, "vertices") else [ed.start for ed in pth.edges]
        poly = Polygon([loc(T(v)) for v in vs])
        a = poly.intersection(room).area
        if a > 0.001:
            under = {k: round(LineString([a_, b_]).intersection(poly).length, 4) for k, (a_, b_) in contour.items()}
            under["(B27 stretch inside)"] = round(sum(g.intersection(poly).length for g in beam_on), 4)
            print(f"  sunken panel {h}: {a:.4f} m2 of the pantry plan; pantry faces under it "
                  f"{ {k: v for k, v in under.items() if v > 0.001} }")

    # ---- GF-14 wash lobby: frame origin = start of D2 (south face, east end), x east, y north
    o = line_pts(ar, "D2")[0]
    loc = lambda p: (float(p[0] - o[0]) / 1000, float(p[1] - o[1]) / 1000)  # noqa: E731
    P = {h: tuple(tuple(round(v, 4) for v in loc(p)) for p in line_pts(ar, h)) for h in
         ("D2", "BE", "318", "324", "317", "31A", "31B", "2DB")}
    for h, v in P.items():
        print(f"  GF-14 {h} layer {ar.entitydb.get(h).dxf.layer}: {v[0]} -> {v[1]}")
    faces = {
        "south face D2": P["D2"],
        "east face BE": P["BE"],
        "W_C 318": P["318"],
        "W_B 324": P["324"],
        "wall 317": P["317"],
        "door 320 (D315, head 2.20) over-door wall": (P["317"][1], P["31A"][0]),
        "wall 31A": P["31A"],
        "door 321 (D315, head 2.20) over-door wall": (P["31A"][1], P["31B"][0]),
        "wall 31B": P["31B"],
        "west face (x = 31B end)": (P["31B"][1], (P["31B"][1][0], P["2DB"][0][1])),
        "open south (layer 2, above)": P["2DB"],
    }
    (p1, p2), (q1, q2) = (line_pts(st, B11[0]), line_pts(st, B11[1]))
    fp = strip(*(loc(T(p)) for p in (p1, p2, q1, q2)))
    print("  B11 edges x (local):", round(loc(T(p1))[0], 4), round(loc(T(q1))[0], 4))
    tot = 0
    for k, (a, b) in faces.items():
        L = LineString([a, b]).intersection(fp).length
        if L > 0.0005:
            print(f"    B11 footprint on {k}: {L:.6f} m")
            tot += L if "open" not in k else 0
    print(f"  B11 on the lobby's faces: {tot:.6f} m; contour (walls + doors) "
          f"{sum(LineString([a, b]).length for k, (a, b) in faces.items() if 'open' not in k):.3f} m")
    for h in PANELS:
        e = st.entitydb.get(h)
        pth = e.paths[0]
        vs = pth.vertices if hasattr(pth, "vertices") else [ed.start for ed in pth.edges]
        poly = Polygon([loc(T(v)) for v in vs])
        hit = {k: LineString([a, b]).intersection(poly).length for k, (a, b) in faces.items()}
        hit = {k: round(v, 3) for k, v in hit.items() if v > 0.001}
        if hit:
            print(f"  sunken panel {h} over GF-14 faces: {hit}")


if __name__ == "__main__":
    main(sys.argv[1:])
