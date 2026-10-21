"""T-119 r2 hand-reading helper (research only, NOT engine code): second, independent framing search from the DXF
beam edges, to catch members the route G band search (column_ledger.py, band polygon within 3 cm) misses, such as
oblique beams whose overlay band is drawn short of the column face (verifier 2026-10-21 18:40: B19 at 1F C9).

For every column row of COLUMNS_TO_CONTROLLING_MEMBER.csv it collects the beam-edge segments of that storey's
roof-slab plan (layers 1 / 2 / S-BOUN / S-BEAM / 5, blocks exploded) that END on the column outline (an end point
within 3 cm of it, the other end outside the outline grown by 3 cm), groups them by the face they leave from and their
direction, and maps each group to the route G band / T-110 member that lies 0.30 .. 0.60 m out along the edge.
Every group whose member is not already in the row's framing list is printed as NEW for a reading by eye on the sheet;
it decides nothing.  Usage: python -I framing_recheck.py <ST.dxf> <bands.json> <t110 register csv> <ledger csv> <out json>
       python -I framing_recheck.py --selftest   (synthetic, non-Alsenan hand cases; no input files)"""
import csv, json, math, sys
from shapely.geometry import Polygon, LineString, Point, box


def arriving(x, y, dx, dy, seg_list, tol=0.03, min_len=0.25):
    """Edge segments that END on the outline of the column box (centre x, y; size dx x dy), grouped by
    (face, direction rounded to 5 deg). A segment passing the column, or lying inside it, is not arriving."""
    col = box(x - dx / 2, y - dy / 2, x + dx / 2, y + dy / 2); grown = col.buffer(tol, join_style=2)
    groups = {}
    for p, q in seg_list:
        for a, b in ((p, q), (q, p)):
            if col.exterior.distance(Point(a)) <= tol and not grown.contains(Point(b)) and math.dist(a, b) > min_len:
                ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360
                face = min((abs(a[0] - (x - dx / 2)), 'W'), (abs(a[0] - (x + dx / 2)), 'E'),
                           (abs(a[1] - (y - dy / 2)), 'S'), (abs(a[1] - (y + dy / 2)), 'N'))[1]
                groups.setdefault((face, round(ang / 5) * 5 % 360), []).append((a, b))
    return groups


def selftest():
    """Hand cases on an invented 0.20 x 0.50 column at (10, 20) (not Alsenan): an oblique 0.40 beam leaving the east
    face at atan(0.1) = 5.7 deg (both edges end on the face: one group, 2 edges), a beam passing the column (no
    group), a single tread line ending on the west face (one group, 1 edge: the pair test is the reader's), a 0.10 m
    stub (shorter than 0.25: ignored); then the same scene mirrored in x and rotated 90 deg."""
    def scene(tf):
        S = [((10.10, 20.05), (15.10, 20.55)), ((10.10, 19.80), (15.10, 20.30)),    # oblique beam edges, E face
             ((5.0, 19.70), (15.0, 19.70)),                                             # passing line, below the column
             ((9.90, 20.10), (7.00, 20.10)),                                            # one tread line, W face
             ((10.0, 20.25), (10.0, 20.35))]                                            # 0.10 stub on the N face
        return [(tf(a), tf(b)) for a, b in S]
    g = arriving(10, 20, 0.20, 0.50, scene(lambda p: p))
    assert sorted((k, len(v)) for k, v in g.items()) == [(('E', 5), 2), (('W', 180), 1)], g
    gm = arriving(-10, 20, 0.20, 0.50, scene(lambda p: (-p[0], p[1])))                   # mirror x
    assert sorted((k, len(v)) for k, v in gm.items()) == [(('E', 0), 1), (('W', 175), 2)], gm
    gr = arriving(-20, 10, 0.50, 0.20, scene(lambda p: (-p[1], p[0])))                   # rotate +90 deg
    assert sorted((k, len(v)) for k, v in gr.items()) == [(('N', 95), 2), (('S', 270), 1)], gr
    assert arriving(10, 20, 0.20, 0.50, []) == {}                                       # missing data: nothing, never a member
    print('selftest: 4 cases PASS')


if len(sys.argv) > 1 and sys.argv[1] == '--selftest':
    selftest(); sys.exit(0)
import ezdxf
DXF, BANDS, REG, LED, OUT = sys.argv[1:6]
EDGE_LAYERS = {'1', '2', 'S-BOUN', 'S-BEAM', '5'}
WIN = {'2F': (-27, -2), '1F': (11.5, 36), 'GF': (40.5, 74.5)}   # same sheet windows as prep_frames.py

doc = ezdxf.readfile(DXF); segs = {k: [] for k in WIN}
def add(p, q):
    for k, (a, b) in WIN.items():
        if a <= p[0] <= b and 35 < p[1] < 51.5 and a <= q[0] <= b:
            segs[k].append((p, q))
def walk(ents, d=0):
    for e in ents:
        t = e.dxftype()
        if t == 'INSERT' and d < 6:
            try: walk(list(e.virtual_entities()), d + 1)
            except Exception: pass
            continue
        try: L = e.dxf.layer
        except Exception: continue
        if L not in EDGE_LAYERS: continue
        if t == 'LINE':
            add((e.dxf.start.x / 1000, e.dxf.start.y / 1000), (e.dxf.end.x / 1000, e.dxf.end.y / 1000))
        elif t == 'LWPOLYLINE':
            p = [(q[0] / 1000, q[1] / 1000) for q in e.get_points()]
            if e.closed: p.append(p[0])
            for a, b in zip(p, p[1:]): add(a, b)
walk(doc.modelspace())

bands = json.load(open(BANDS))
reg = list(csv.DictReader(open(REG)))
def members(sh, bid):
    out = []
    for r in reg:
        c = r['component']
        if not c.startswith(f'BEAMS:{sh}:'): continue
        tail = c.split(':')[2]; parts = tail.split('+')
        base = parts[0].rsplit('.', 1)[0] if '.' in parts[0] else parts[0]
        if tail == bid or bid in [base + p if p.startswith('.') else p for p in parts] or (len(parts) > 1 and bid.startswith(base)):
            out.append(f"{r['member_id']} {r['mark']} D{r['depth_m']} {r['status']}")
    return out
BP = {}
for k, v in bands.items():
    bid, st = k.split('@'); P = Polygon(v['pts']); BP.setdefault(st, []).append((bid, P if P.is_valid else P.buffer(0)))

res = []
for r in csv.DictReader(open(LED)):
    sh = r['storey']; dx, dy = map(float, r['drawn'].split('x')); x, y = float(r['x']), float(r['y'])
    groups = arriving(x, y, dx, dy, segs[sh])
    found = []
    for (face, ang), L in sorted(groups.items()):
        a, b = L[0]; u = ((b[0] - a[0]) / math.dist(a, b), (b[1] - a[1]) / math.dist(a, b))
        probe = LineString([(a[0] + u[0] * 0.30, a[1] + u[1] * 0.30), (a[0] + u[0] * 0.60, a[1] + u[1] * 0.60)])
        near = sorted((P.distance(probe), bid) for bid, P in BP.get(sh, []))[:2]
        mem = [m for dd, bid in near if dd <= 0.25 for m in members(sh, bid)]
        inlist = any(m.split()[0] in r['framing'] for m in mem)
        found.append(dict(face=face, angle=ang, edges=len(L), oblique=ang % 90 != 0, probe_bands=[(bid, round(dd, 3)) for dd, bid in near], members=mem,
                          in_framing_list=inlist))
    new = [f for f in found if not f['in_framing_list']]
    res.append(dict(id=r['id'], storey=sh, mark=r['mark'], framing=r['framing'], D_ctrl=r['D_ctrl'], groups=found, new=new))
    for f in new:
        print(r['id'], r['mark'], 'D_ctrl', r['D_ctrl'], 'NEW', f['face'], f['angle'], 'edges', f['edges'], f['probe_bands'], f['members'])
json.dump(res, open(OUT, 'w'), indent=1)
print(len(res), 'columns;', sum(len(x['new']) for x in res), 'edge groups not in the framing list')
