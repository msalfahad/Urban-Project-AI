"""T-127: why T-121's CAD gross for the pool court (18.393 m2, plate inside the slab sheet less the V2.9 facade outline)
is larger than the soffit measured face to face from the printed dimensions (16.525 m2). Same local frame as
pool_court_hand.py. The pieces added back are slab over the court's bounding facade walls (with their opening heads) and the 0.08 m recess between the
curved frame (CAD line, 0.080 m off the printed band face) and the printed 657 line. Run: python3 -I reconcile_t121_basis.py"""
import math, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from pool_court_hand import court_clear, arc, box, Polygon, unary_union
def bulge_arc(p0, p1, b, n=400):
    th = 4 * math.atan(b); c = math.dist(p0, p1); r = c / (2 * math.sin(th / 2))
    mx, my = (p0[0]+p1[0])/2, (p0[1]+p1[1])/2; dx, dy = (p1[0]-p0[0])/c, (p1[1]-p0[1])/c
    h = r * math.cos(th / 2); cx, cy = mx - dy * h, my + dx * h   # centre left of chord for b>0
    a0 = math.atan2(p0[1]-cy, p0[0]-cx); a1 = math.atan2(p1[1]-cy, p1[0]-cx)
    if a1 < a0: a1 += 2*math.pi
    return [(cx + r*math.cos(a0+(a1-a0)*i/n), cy + r*math.sin(a0+(a1-a0)*i/n)) for i in range(n+1)], r, r*th
# frame line W 280 (CAD): X -0.080, Y 5.400 -> 5.2065, bulge 0.867 to 0.5934, -> 0.450 (mm values from the plan / 1000)
pts, r, L = bulge_arc((-0.080, 5.2065), (-0.080, 0.5934), 0.867)
frame_region = Polygon([(-0.080, 5.400)] + pts + [(-0.080, 0.450), (0, 0.450), (0, 0), (2, 0), (2, 5.4), (0, 5.4)]).buffer(0)
clear = court_clear()
pocket = frame_region.difference(clear).difference(box(1.8, 0, 2, 5.4))
east = box(1.8, 0, 2.0, 5.4)
north = box(-0.08, 5.4, 2.0, 5.6).difference(box(0, 5.35, 0.5, 5.6))
south = box(-0.2, -0.2, 2.0, 0).difference(box(-0.2, -0.25, 0.7, 0)).difference(box(1.8, -0.5, 2.0, 0))
colproud = box(0, 5.35, 0.5, 5.4).area
print(f"frame arc r {r:.4f} length {L:.4f}; clear {clear.area:.4f}; pocket {pocket.area:.4f}; east wall strip {east.area:.4f};"
      f" north wall strip {north.area:.4f}; south wall strip {south.area:.4f}; column proud {colproud:.4f}")
base = clear.area - colproud
for name, v in [("clear", base), ("+pocket", base + pocket.area), ("+pocket+east", base + pocket.area + east.area),
                ("+pocket+east+north", base + pocket.area + east.area + north.area),
                ("+pocket+east+north+south", base + pocket.area + east.area + north.area + south.area),
                ("+east+north", base + east.area + north.area)]:
    print(f"{name:28s} {v:.4f}  (T-121 CAD gross 18.393: {v-18.393:+.4f})")
