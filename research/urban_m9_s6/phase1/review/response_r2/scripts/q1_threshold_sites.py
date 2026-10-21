"""Q1, threshold by threshold: does each band-path threshold lose a drafted-exact value under rotation / site offset?
Uses the engine's own frozen functions (opening_census.face_lines / wall_bands / band_gaps) on placed segments.

  OVERLAP  two faces 200 mm apart overlapping by exactly 300 mm (the min_overlap): the band must exist
  GAP      a band with a drafted 500 mm opening between masonry jambs (the min_gap used by layer_roles): the gap must
           be found (400 mm and 500 mm are both used; 500 is tested)
  PIECE    the 100 mm face piece (Investigation A), for comparison

Each case: the frozen comparison vs the same comparison with the margin max(1e-6 mm, fp bound) applied (by passing a
threshold lowered by the margin, i.e. the robust "at least" predicate).
usage: python3 -I q1_threshold_sites.py SRC [N] [JSON_OUT]"""
import json, math, random, sys
SRC = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 500
sys.path.insert(0, SRC)
from engine.source import opening_census as OC
from engine.source import opening_gaps as OG
U = 2.0 ** -53
rng = random.Random(7)


def place(p, rot, at):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return (p[0] * c - p[1] * s + at[0], p[0] * s + p[1] * c + at[1])


def margin(segs, k, depth=1):
    M = max(abs(v) for _, a, b in segs for v in (*a, *b))
    return max(1e-6 * k, 16 * U * M * (depth + 1))


def run(kind, unit_m, rot, at, robust):
    k = 1e-3 / unit_m
    P = lambda x, y: place((x * k, y * k), rot, (at[0] * k, at[1] * k))
    if kind == "OVERLAP":       # face A from 0..1000, face B from 700..1700: overlap exactly 300 mm
        local = [("A", (0, 0), (1000, 0)), ("B", (700, 200), (1700, 200))]
    elif kind == "GAP":         # both faces with a 500 mm gap (1000..1500) and jamb lines
        local = [("A1", (0, 0), (1000, 0)), ("A2", (1500, 0), (3000, 0)), ("B1", (0, 200), (1000, 200)),
                 ("B2", (1500, 200), (3000, 200))]
    else:                       # PIECE: one face continues, the other is a 100 mm piece below a 1000 mm gap
        local = [("A1", (0, 0), (2000, 0)), ("A2", (3000, 0), (5000, 0)), ("B1", (1900, 200), (2000, 200)),
                 ("B2", (3000, 200), (5000, 200))]
    segs = [(i, P(*a), P(*b)) for i, a, b in local]
    m = margin(segs, k) if robust else 0.0
    fl = OC.face_lines(segs, ang_res_deg=0.5, off_tol=2.0 * k, join_tol=5.0 * k, min_len=100.0 * k - m)
    bands = OC.wall_bands(fl, 0.10 / unit_m, 0.45 / unit_m, min_overlap=0.3 / unit_m - m)
    if kind == "OVERLAP":
        if bands:
            ERR.append(abs((bands[0]["hi"] - bands[0]["lo"]) / k - 300.0))
        return len(bands) == 1
    # V2's unit-relative merge (1 mm in the unit); the frozen 1.0-unit merge would close every gap in metres
    gaps = [g for b in bands for g in OG.band_gaps(b, min_gap=0.5 / unit_m - m if kind == "GAP" else 0.5 / unit_m,
                                                   jamb_tol=0.03 / unit_m, merge_tol=1e-3 / unit_m)]
    want = 500.0 if kind == "GAP" else 1000.0
    hit = [g for g in gaps if abs(g["width"] / k - want) < 0.05]
    if hit:
        ERR.append(abs(hit[0]["width"] / k - want))
    return bool(hit)


ERR = []
res = {}
for kind in ("PIECE", "OVERLAP", "GAP"):
    for unit, unit_m in (("mm", 1e-3), ("m", 1.0)):
        for rot in (0.0, 90.0, 30.0, 45.0, None):
            for off in (0.0, 1e6, 3.3e9):
                ok_f = ok_r = 0
                ERR.clear()
                for _ in range(N):
                    r = rot if rot is not None else rng.uniform(0, 360)
                    at = (round(rng.uniform(-1, 1) * (off + 1000), 3), round(rng.uniform(-1, 1) * (off + 1000), 3))
                    ok_f += run(kind, unit_m, r, at, False)
                    ok_r += run(kind, unit_m, r, at, True)
                res[f"{kind}|{unit}|rot={'rand' if rot is None else int(rot)}|off={off:g}mm"] = {
                    "frozen": ok_f / N, "robust": ok_r / N, "max_measured_error_mm": max(ERR) if ERR else None}
w = max(map(len, res))
print(f"{'case':{w}s} {'frozen':>8s} {'robust':>8s} {'max |measured - drafted| mm':>28s}")
for c, v in res.items():
    e = v['max_measured_error_mm']
    print(f"{c:{w}s} {v['frozen']:8.3f} {v['robust']:8.3f} {('%.3e' % e) if e is not None else '-':>28s}")
if len(sys.argv) > 3:
    json.dump({"n_per_case": N, "found_fraction": res}, open(sys.argv[3], "w"), indent=1)
