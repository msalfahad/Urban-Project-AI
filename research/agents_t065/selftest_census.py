"""Self-test of foundation_member_census.py on a hand-calculated synthetic DXF (not Alsenan). Writes only to a temp dir.

Plot 10.00 x 6.00 m in mm, band 0.20 m: centre line 2 x (9.80 + 5.80) = 31.20 m.
Footings: unit-square block scaled 1.0 x 0.8 at the corner (centre line inside 0.90 + 0.70 = 1.60 m); open polyline
2.0 x 1.0 on side 1 (2.00 m); a 4-LINE 1.0 x 1.0 square on side 2 (1.00 m); an inner footing off the band (0).
Expected: in footings 4.60 m, free 26.60 m. Second case: the same plot shifted by (-50000, +20000) and
mirrored in x (handled by boxes, axis-aligned only): same totals.
"""
import io, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def dxf(shift=(0.0, 0.0), mirror=False):
    def P(x, y):
        x = -x if mirror else x
        return x + shift[0], y + shift[1]
    out = ["0", "SECTION", "2", "BLOCKS",
           "0", "BLOCK", "2", "FT", "0", "LWPOLYLINE", "5", "B1", "8", "S-FOOTINGS", "70", "1",
           "10", "-500", "20", "-500", "10", "500", "20", "-500", "10", "500", "20", "500", "10", "-500", "20", "500",
           "0", "ENDBLK", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
    def lw(h, pts, closed, layer):
        out.extend(["0", "LWPOLYLINE", "5", h, "8", layer, "70", "1" if closed else "0"])
        for x, y in pts:
            X, Y = P(x, y)
            out.extend(["10", repr(X), "20", repr(Y)])
    lw("A1", [(0, 0), (10000, 0), (10000, 6000), (0, 6000)], True, "S-BOUN")
    lw("A2", [(200, 200), (9800, 200), (9800, 5800), (200, 5800)], True, "S-BOUN")
    X, Y = P(500, 400)
    out.extend(["0", "INSERT", "5", "A3", "8", "S-DIM", "2", "FT", "10", repr(X), "20", repr(Y),
                "41", "-1.0" if mirror else "1.0", "42", "0.8"])
    lw("A4", [(4600, 1000), (4000, 1000), (4000, 0), (6000, 0), (6000, 1000), (5400, 1000)], False, "S-FOOTINGS")
    lw("A5", [(3000, 3000), (4000, 3000), (4000, 4000), (3000, 4000)], True, "S-FOOTINGS")
    sq = [(9000, 3000), (10000, 3000), (10000, 4000), (9000, 4000), (9000, 3000)]
    for i in range(4):
        (ax, ay), (bx, by) = P(*sq[i]), P(*sq[i + 1])
        out.extend(["0", "LINE", "5", "L%d" % i, "8", "S-FOOTINGS", "10", repr(ax), "20", repr(ay),
                    "11", repr(bx), "21", repr(by)])
    out.extend(["0", "ENDSEC", "0", "EOF"])
    return "\n".join(out) + "\n"


def run(text):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "synthetic.dxf")
        open(p, "w").write(text)
        r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "foundation_member_census.py"), p,
                            "--outer", "A1", "--inner", "A2"], capture_output=True, text=True, check=True)
        return json.loads(r.stdout)


def main():
    for case, text in (("plain", dxf()), ("shifted+mirrored", dxf((-50000.0, 20000.0), True))):
        t = run(text)["totals_m"]
        assert t["drawn"] == 31.2, (case, t)
        assert t["footings"] == 4.6, (case, t)
        assert t["free"] == 26.6, (case, t)
        print(case, "OK", t)


if __name__ == "__main__":
    main()
