"""S6 review, Investigation A: which fix makes "a drafted 100 mm piece is at least 100 mm" hold under translation,
rotation and unit change? Pure stdlib, deterministic.

A 100 mm segment is placed by a block insert (rotate about the origin, then translate to a site offset), the way
an INSERT reaches the intake. Then six decision procedures are applied to it, with the threshold 100 mm:
  FROZEN       float length in drawing units, keep when not (L < 100 mm), with 100 mm expressed in the unit
  CANON_MM     convert the coordinates to mm first, then FROZEN
  QUANT_1UM    round each coordinate to 0.001 mm, then FROZEN
  INT_UM       integer micrometre coordinates, exact comparison of the squared length with (100 000 um)^2
  ROBUST_EPS   float, keep when L >= 100 mm - eps, eps = 1e-6 mm (in the unit)
  LOCAL_ORIGIN translate to a local origin (the insert point) before measuring, then FROZEN
The kept fraction should be 1.0 for every sample; anything less is a silent drop.

usage: python3 -I a_method_comparison.py [N] [JSON_OUT]"""
import json, math, random, sys

N = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
rng = random.Random(20261013)
ROTS = [0.0, 90.0, 180.0, 270.0, 30.0, 45.0, 60.0, None]       # None: a random angle


def place(p, rot, at):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return (p[0] * c - p[1] * s + at[0], p[0] * s + p[1] * c + at[1])


def decide(a, b, unit_m, method, at):
    thr = 100.0 * (1e-3 / unit_m)
    if method == "FROZEN":
        return not math.dist(a, b) < thr
    if method == "CANON_MM":
        f = unit_m * 1000.0
        return not math.dist((a[0] * f, a[1] * f), (b[0] * f, b[1] * f)) < 100.0
    if method == "QUANT_1UM":
        f = unit_m * 1000.0
        q = lambda p: (round(p[0] * f, 3), round(p[1] * f, 3))
        return not math.dist(q(a), q(b)) < 100.0
    if method == "INT_UM":
        f = unit_m * 1e6
        qa, qb = (round(a[0] * f), round(a[1] * f)), (round(b[0] * f), round(b[1] * f))
        return (qa[0] - qb[0]) ** 2 + (qa[1] - qb[1]) ** 2 >= 100000 ** 2
    if method == "ROBUST_EPS":
        return math.dist(a, b) >= thr - 1e-9 / unit_m
    if method == "LOCAL_ORIGIN":
        return not math.dist((a[0] - at[0], a[1] - at[1]), (b[0] - at[0], b[1] - at[1])) < thr
    raise ValueError(method)


METHODS = ["FROZEN", "CANON_MM", "QUANT_1UM", "INT_UM", "ROBUST_EPS", "LOCAL_ORIGIN"]
res = {}
for unit_m, label in ((0.001, "mm"), (1.0, "m")):
    k = 1e-3 / unit_m
    local = ((200.0 * k, -100.0 * k), (200.0 * k, 0.0))           # the drafted 100 mm piece in the block
    for rot in ROTS:
        kept = {m: 0 for m in METHODS}
        for _ in range(N):
            r = rot if rot is not None else rng.uniform(0, 360)
            at = (round(rng.uniform(-900000, 900000), 3) * k, round(rng.uniform(-900000, 900000), 3) * k)
            a, b = place(local[0], r, at), place(local[1], r, at)
            for m in METHODS:
                kept[m] += decide(a, b, unit_m, m, at)
        res[f"{label}/rot={'random' if rot is None else int(rot)}"] = {m: round(v / N, 4) for m, v in kept.items()}
w = max(len(k) for k in res)
print(f"{'case':{w}s} " + " ".join(f"{m:>12s}" for m in METHODS))
for case, v in res.items():
    print(f"{case:{w}s} " + " ".join(f"{v[m]:12.4f}" for m in METHODS))
if len(sys.argv) > 2:
    json.dump({"n_per_case": N, "kept_fraction": res}, open(sys.argv[2], "w"), indent=1)
