"""T-127 pool-court soffit from the printed dimensions and the drawn arc parameters (no CAD face, no engine call).
Local frame (metres): X = 0 at the court face of the 0.20 m west wall pier / glazing-band ends, X = 2.00 at the outer face
of the east boundary wall; Y = 0 at the court face of the south wall, Y = 5.40 at the court face of the north wall.
Every value below is a printed dimension of the GF plan (sheet 03) or a sum of them, except where marked CAD."""
import math
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union

N = 2000  # points per full circle

def arc(c, r, a0, a1):
    if a1 < a0:
        a1 += 360
    n = max(8, int(N * (a1 - a0) / 360))
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

def disk(c, r):
    return Point(c).buffer(r, resolution=N // 4)

# ---- printed GF-plan values (sheet 03) ----
W_OUT = 2.000          # 2000: court face of the west pier line to the OUTER face of the east boundary wall
T_BND = 0.200          # 20 / 200: east boundary wall
H = 0.750 + 3.500 + 1.150   # vertical chain 750 + 3500 + 1150 between the north and south wall faces = 5.400
POOL_D = 3.500         # 3500: pool west edge to the outer face of the boundary wall (pool radius 1.750)
GAP = 0.500            # 500: pool edge to the court face of the curved glazing band
BAND = 0.200           # 20 / 200: the curved glazing band
YC = 1.150 + 3.500 / 2 # pool centre level: 1150 + 3500 / 2 = 2.900
XC = W_OUT - POOL_D / 2  # 0.250
R_FACE = POOL_D / 2 + GAP   # 2.250: court face of the curved band = the printed 657 line
W_CLEAR = W_OUT - T_BND     # 1.800

def court_clear():
    # west boundary: X = 0 line, the r 2.25 arc where it bulges west of X = 0
    rect = box(0, 0, W_CLEAR, H)
    seg = disk((XC, YC), R_FACE).intersection(box(-5, 0, 0, H))
    return unary_union([rect, seg])

def void_and_ring():
    # GF roof slab sheet (structural set): B7 ring drawn as two circles, CAD radii (not printed on the slab sheet):
    A, B = (XC, YC), (XC + 1.435, YC)      # B centre 1.435 east of the pool centre (1F plan: r 1.935 window arc centre)
    rAi, rAo, rBi, rBo = 1.550, 1.750, 1.735, 1.935
    ft_c, ft_r = (XC + 0.5694, YC + 0.8699), 0.5104      # top fillet (CAD)
    fb_c, fb_r = (XC + 0.5916, YC - 0.6304), 0.6899      # bottom fillet (CAD)
    x_cb1 = 1.650           # CB1 inner face (CAD, 0.350 beam: 1.650 .. 2.000)
    y_b17, y_b7, x_b8 = 1.5798, 4.2803, -0.050           # B17 north face, B7 straight-leg south face, B8 east face (CAD)
    pts = [(x_cb1, YC - math.sqrt(rAi**2 - (x_cb1 - XC)**2))]
    pts += arc(A, rAi, 25.415, 57.355)
    pts += arc(ft_c, ft_r, 58.498, 127.921)
    pts += arc(B, rBi, 132.821, 221.158)
    pts += arc(fb_c, fb_r, 227.857, 304.539)
    pts += arc(A, rAi, 309.349, 334.585)
    void = Polygon(pts).buffer(0)
    bay = box(x_b8, y_b17, x_cb1, y_b7)
    outer = disk(A, rAo).intersection(disk(B, rBo)).intersection(bay)
    ring = outer.difference(void)
    corners = bay.difference(outer)
    return void, ring, corners, bay

if __name__ == "__main__":
    c = court_clear()
    rect = W_CLEAR * H
    seg = c.area - rect
    d = XC; th = math.acos(d / R_FACE)
    seg_formula = R_FACE**2 * th - d * math.sqrt(R_FACE**2 - d**2)
    arc_len = R_FACE * 2 * math.acos(d / R_FACE)
    col = 0.500 * 0.050     # NW GF column proud of the north wall face (CAD 0.05: T-123 anchor N)
    print(f"clear rectangle {W_CLEAR:.3f} x {H:.3f} = {rect:.4f} m2")
    print(f"west segment r {R_FACE:.3f}, chord at {d:.3f} from the centre: formula {seg_formula:.4f}, polygon {seg:.4f} m2;"
          f" court-face arc length {arc_len:.4f} m (printed 657)")
    print(f"court clear gross {c.area:.4f} - column proud {col:.4f} = {c.area - col:.4f} m2")
    v, ring, corners, bay = void_and_ring()
    print(f"bay {bay.area:.4f} = void {v.area:.4f} + ring band {ring.area:.4f} + slab corners {corners.area:.4f}"
          f" (check {v.area + ring.area + corners.area:.4f}); void inside court: {c.contains(v.buffer(-1e-6))}")
    print(f"void extents X {v.bounds[0]:.4f}..{v.bounds[2]:.4f}, Y {v.bounds[1]:.4f}..{v.bounds[3]:.4f}")
    net = c.area - col - v.area
    print(f"NET soffit = {c.area - col:.4f} - {v.area:.4f} = {net:.4f} m2")
    # what the net soffit is made of (GF roof slab sheet, CAD beam faces; beam widths are not printed on the slab sheet)
    soff = c.difference(box(0, 5.35, 0.5, 5.40)).difference(v)
    beams = {"B24 (north, Y 5.10..5.60)": box(-5, 5.10, 2.0, 5.60), "CB1 (east, X 1.65..2.00)": box(1.65, -1, 2.0, 6),
             "B7 straight leg (Y 4.280..4.480)": box(-0.05, 4.2803, 1.65, 4.4803),
             "B17 (Y 1.130..1.580)": box(-5, 1.1298, 1.65, 1.5798), "B8 (X -0.25..-0.05)": box(-0.25, 1.5798, -0.05, 5.10),
             "B28 (X 0.25..0.50, Y 0..1.130)": box(0.25, 0, 0.50, 1.1298), "B7 ring band (inner to outer face)": ring,
             "bay corners outside the ring faces (no slab bars drawn)": corners}
    used = None; tot = 0
    for k, g in beams.items():
        a = soff.intersection(g if used is None else g.difference(used)).area
        used = g if used is None else used.union(g); tot += a
        print(f"   {k:55s} {a:.4f}")
    print(f"   {'slab panels (remainder)':55s} {soff.area - tot:.4f}   (sum {soff.area:.4f})")
