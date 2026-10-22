"""Synthetic, non-Alsenan fixture for walk_r2.classify (hand-calculated). Villa K bed room: 4.00 x 3.00 m; the east
side is a curved glazing face (arc of radius 2.00 m through the two east corners, bulging out); a 0.80 m door gap in
the south wall closed by a gap line; a 1.00 m open side (no drawn line) in the west wall. Run in the project venv:
python -I check_walk_r2.py   ->  'check_walk PASS'. Adversarial: mirrored, rotated 37 degrees, shifted 1 km.
Hand values: arc chord 3.00, r 2.00 -> half angle asin(0.75) = 0.848062 rad, arc length 2 x 2.00 x 0.848062 = 3.392248;
walls = north 4.00 + south 4.00 - door 0.80 + west 3.00 - open 1.00 = 9.20; contour = 4 + 4 + 3 + 3.392248 = 14.392248."""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union
from shapely import affinity
import walk_r2 as W

def arc(cx, cy, r, a0, a1, n=400):
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]

def fixture(tf):
    half = math.asin(0.75); cx = 4.0 - 2.0 * math.cos(half); cy = 1.5          # centre west of the east side
    east = arc(cx, cy, 2.0, -half, half)                                          # from (4,0) to (4,3), bulging east
    room = Polygon([(0, 0)] + east + [(0, 3)])
    walls = [LineString([(0, 3), (4, 3)]), LineString([(0, 0), (1.0, 0)]), LineString([(1.8, 0), (4, 0)]),
             LineString([(0, 0), (0, 1.0)]), LineString([(0, 2.0), (0, 3)])]
    wins = [LineString(east)]; gaps = [LineString([(1.0, 0), (1.8, 0)])]
    g = lambda geoms: unary_union([tf(x) for x in geoms])
    F = dict(walls=g(walls), cols=LineString([(-50, -50), (-50, -49)]), wins=g(wins), doors=LineString([(-60, -60), (-60, -59)]),
             gaps=g(gaps))
    return F, tf(room)

def run(tf, name):
    F, poly = fixture(tf)
    tot, runs = W.classify(F, poly, step=0.002)
    arc_len = 2 * 2.0 * math.asin(0.75)
    # the walk's documented bias (calc_r2 SAMPLE_LOSS): an opening run that meets a wall line loses about 0.005 m at
    # each wall end to the wall (a point within 5 mm of the jamb line reads WALL); the curved window meets no gap
    L = 0.01
    want = {'WALL': 9.20 + 2 * L, 'WINDOW': arc_len, 'GAP': 0.80 - L, 'VIRTUAL': 1.00 - L}
    ok = all(abs(tot.get(k, 0) - v) < 0.004 for k, v in want.items()) and abs(poly.exterior.length - (11 + arc_len)) < 0.005
    print(name, {k: round(v, 3) for k, v in tot.items()}, 'contour', round(poly.exterior.length, 4), 'OK' if ok else 'FAIL')
    return ok

# r3 adverse case (checker 2026-10-22 16:11, Alsenan 1F-11 at the W17 jambs): the region leaks into a glazing-frame
# cavity at the jamb. Same villa K room; at the north-east jamb the walked ring dips into a 0.03 m wide, 0.075 m deep
# cavity between two frame lines (x = 3.995 and 3.935, layer W) whose sides sit 0.015 m (BUF) off them: by hand the
# ring is 0.15 m too long (two sides 0.075; the 0.03 bottom replaces 0.03 of north wall). Drawn face length = 11 + arc.
# After trim_notches: contour = drawn face length, spike scan empty, VIRTUAL only the 1.00 open side.
# Second adverse case: the same 0.03 x 0.075 recess drawn on all three sides (a real face, like the acute corner where
# the GF-15 glazing band meets its wall): it must NOT be reported or trimmed (contour keeps its 0.15 m).
def notch_fixture(tf, drawn_recess):
    half = math.asin(0.75); cx = 4.0 - 2.0 * math.cos(half); cy = 1.5
    east = arc(cx, cy, 2.0, -half, half)
    ring = [(0, 0)] + east + [(3.98, 3.0), (3.98, 3.075), (3.95, 3.075), (3.95, 3.0), (0, 3)]
    room = Polygon(ring)
    walls = [LineString([(0, 3), (4, 3)]), LineString([(0, 0), (1.0, 0)]), LineString([(1.8, 0), (4, 0)]),
             LineString([(0, 0), (0, 1.0)]), LineString([(0, 2.0), (0, 3)])]
    wins = [LineString(east), LineString([(3.995, 3.0), (3.995, 3.2)]), LineString([(3.935, 3.0), (3.935, 3.2)])]
    if drawn_recess:
        wins += [LineString([(3.98, 3.0), (3.98, 3.075), (3.95, 3.075), (3.95, 3.0)])]
    gaps = [LineString([(1.0, 0), (1.8, 0)])]
    g = lambda geoms: unary_union([tf(x) for x in geoms])
    F = dict(walls=g(walls), cols=LineString([(-50, -50), (-50, -49)]), wins=g(wins), doors=LineString([(-60, -60), (-60, -59)]),
             gaps=g(gaps))
    F['drawn'] = unary_union([F['walls'], F['wins'], F['gaps']])
    return F, tf(room)

def run_notch(tf, name):
    # tolerance 1e-5 m: the 400-chord arc polyline is 2.5e-6 m shorter than the true arc
    arc_len = 2 * 2.0 * math.asin(0.75); face = 11 + arc_len
    F, poly = notch_fixture(tf, False)
    before = W.spikes(list(poly.exterior.coords), F['drawn'])
    q, trims = W.trim_notches(poly, F['drawn'])
    after = W.spikes(list(q.exterior.coords), F['drawn'])
    tot, _ = W.classify(F, q, step=0.002)
    ok1 = (abs(poly.exterior.length - (face + 0.15)) < 1e-5 and len(before) == 1 and before[0][1] == 'U'
           and abs(q.exterior.length - face) < 1e-5 and not after and len(trims) == 1
           and abs(trims[0]['removed_m'] - 0.15) < 1e-4 and abs(tot.get('VIRTUAL', 0) - (1.00 - 0.01)) < 0.004)
    F2, poly2 = notch_fixture(tf, True)
    sp2 = W.spikes(list(poly2.exterior.coords), F2['drawn'])
    q2, trims2 = W.trim_notches(poly2, F2['drawn'])
    ok2 = not sp2 and not trims2 and abs(q2.exterior.length - (face + 0.15)) < 1e-5
    print(name, 'cavity notch: contour', round(poly.exterior.length, 4), '->', round(q.exterior.length, 4), 'drawn face',
          round(face, 4), 'scan', before, '->', after, '| drawn recess kept', round(q2.exterior.length, 4), sp2,
          'OK' if ok1 and ok2 else 'FAIL')
    return ok1 and ok2

ident = lambda g: g
mirror = lambda g: affinity.scale(g, xfact=-1, yfact=1, origin=(0, 0))
rot = lambda g: affinity.translate(affinity.rotate(g, 37, origin=(0, 0)), 1000.0, -800.0)
res = [run(ident, 'plain'), run(mirror, 'mirrored'), run(rot, 'rotated 37 deg + 1 km shift')]
res += [run_notch(ident, 'plain'), run_notch(mirror, 'mirrored'), run_notch(rot, 'rotated 37 deg + 1 km shift')]
print('check_walk', 'PASS' if all(res) else 'FAIL')
sys.exit(0 if all(res) else 1)
