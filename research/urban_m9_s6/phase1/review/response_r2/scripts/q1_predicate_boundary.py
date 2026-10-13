"""Q1: does a tolerance-aware "at least T" predicate keep every drafted-T piece AND drop every genuinely undersized one?
Pure stdlib, deterministic.

A segment drafted at T + delta (T = 100 mm) is placed through a chain of block inserts (rotation + translation at each
level, the last one to a site offset) in a drawing unit. Five decision procedures:

  FROZEN       keep when not (L < T)                                   (the committed code)
  EPS_FIXED    keep when L >= T - 1e-6 mm                              (the review's first proposal)
  EPS_DRAFT    keep when L >= T - 1e-3 mm                              (a drafting-precision tolerance)
  FP_BOUND     keep when L >= T - eps_fp, eps_fp = K * u * M * (depth + 1), M = the largest |coordinate| of the
               segment in drawing units, u = 2**-53, K = 16: a floating-point error bound, no floor
  HYBRID       eps = max(1e-6 mm, eps_fp); and if eps_fp > 1e-3 mm the decision is UNDECIDABLE (reported, never guessed)

Truth: drafted delta >= 0 must be KEPT; delta <= -1e-6 mm is a genuinely undersized piece and must be DROPPED;
-1e-6 < delta < 0 is below any drafting precision (a "same drafted value" band): either decision is reported, and is
counted separately.

usage: python3 -I q1_predicate_boundary.py [N_PER_CASE] [JSON_OUT]
"""
import json, math, random, sys

N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
rng = random.Random(20261014)
T_MM = 100.0
U = 2.0 ** -53
UNITS = {"mm": 1e-3, "cm": 1e-2, "m": 1.0, "in": 0.0254}
DELTAS_MM = [-1e-2, -1e-3, -1e-4, -1e-5, -3e-6, -1.5e-6, -1e-6, -5e-7, -1e-7, -1e-9, 0.0, 1e-9, 1e-7, 1e-6, 1e-5, 1e-3]
OFFSETS_MM = [0.0, 1e5, 1e6, 1e7, 3.3e9]      # origin, 100 m, 1 km, 10 km, national-grid northing in mm (~3 300 km)
ROTS = [0.0, 90.0, 30.0, 45.0, None]
DEPTHS = [1, 3]


def place(p, chain):
    x, y = p
    for rot, tx, ty in chain:
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        x, y = x * c - y * s + tx, x * s + y * c + ty
    return x, y


def decide(L, M, depth, k, method):
    """L, M in drawing units; k = drawing units per mm."""
    T = T_MM * k
    fp = 16.0 * U * M * (depth + 1)
    if method == "FROZEN":
        return "KEEP" if not L < T else "DROP"
    if method == "EPS_FIXED":
        return "KEEP" if L >= T - 1e-6 * k else "DROP"
    if method == "EPS_DRAFT":
        return "KEEP" if L >= T - 1e-3 * k else "DROP"
    if method == "FP_BOUND":
        return "KEEP" if L >= T - fp else "DROP"
    if method == "HYBRID":
        if fp > 1e-3 * k:
            return "UNDECIDABLE"
        return "KEEP" if L >= T - max(1e-6 * k, fp) else "DROP"
    raise ValueError(method)


METHODS = ["FROZEN", "EPS_FIXED", "EPS_DRAFT", "FP_BOUND", "HYBRID"]
res = {}
noise = {}
for unit, unit_m in UNITS.items():
    k = 1e-3 / unit_m
    for off in OFFSETS_MM:
        for rot in ROTS:
            for depth in DEPTHS:
                case = f"{unit}|off={off:g}mm|rot={'rand' if rot is None else int(rot)}|depth={depth}"
                tally = {m: {"false_drop": 0, "false_keep": 0, "band_keep": 0, "band_drop": 0, "undecidable": 0, "n": 0,
                             "keep_by_delta": {f"{d:g}": 0 for d in DELTAS_MM}} for m in METHODS}
                worst = 0.0
                for _ in range(N):
                    chain = []
                    for d in range(depth):
                        r = rot if rot is not None else rng.uniform(0, 360)
                        if d < depth - 1:      # inner inserts: small local offsets, arbitrary angles for random rot
                            chain.append((r if rot is not None else rng.uniform(0, 360), rng.uniform(-5000, 5000) * k,
                                          rng.uniform(-5000, 5000) * k))
                        else:
                            ox = (off + rng.uniform(0, 1000)) * k * (1 if rng.random() < 0.5 else -1)
                            oy = (off + rng.uniform(0, 1000)) * k * (1 if rng.random() < 0.5 else -1)
                            chain.append((r, round(ox, 3), round(oy, 3)))
                    base = (rng.uniform(-3000, 3000) * k, rng.uniform(-3000, 3000) * k)
                    for dmm in DELTAS_MM:
                        Ld = (T_MM + dmm) * k
                        a = place(base, chain)
                        b = place((base[0], base[1] + Ld), chain)
                        L = math.dist(a, b)
                        M = max(abs(a[0]), abs(a[1]), abs(b[0]), abs(b[1]))
                        if dmm == 0.0:
                            worst = max(worst, abs(L - Ld) / k)
                        for m in METHODS:
                            t = tally[m]; t["n"] += 1
                            dec = decide(L, M, depth, k, m)
                            t["keep_by_delta"][f"{dmm:g}"] += dec == "KEEP"
                            if dec == "UNDECIDABLE":
                                t["undecidable"] += 1
                            elif dmm >= 0 and dec == "DROP":
                                t["false_drop"] += 1
                            elif dmm <= -1e-6 and dec == "KEEP":
                                t["false_keep"] += 1
                            elif -1e-6 < dmm < 0:
                                t["band_keep" if dec == "KEEP" else "band_drop"] += 1
                res[case] = tally
                noise[case] = worst
# summarise by offset (the dominant factor) and unit
summary = {}
for case, tally in res.items():
    unit, off = case.split("|")[0], case.split("|")[1]
    key = f"{unit}|{off}"
    s = summary.setdefault(key, {m: {"false_drop": 0, "false_keep": 0, "band_keep": 0, "band_drop": 0, "undecidable": 0, "n": 0,
                                     "keep_by_delta": {f"{d:g}": 0 for d in DELTAS_MM}} for m in METHODS})
    for m in METHODS:
        for f in s[m]:
            if f == "keep_by_delta":
                for d, v in tally[m][f].items():
                    s[m][f][d] += v
            else:
                s[m][f] += tally[m][f]
    s.setdefault("max_noise_mm", 0.0)
    s["max_noise_mm"] = max(s["max_noise_mm"], noise[case])
print(f"{'unit|offset':22s} {'max |L-Ld| mm':>14s}  " + "  ".join(f"{m:>26s}" for m in METHODS))
print(f"{'':22s} {'':>14s}  " + "  ".join(f"{'fdrop/fkeep/undec/band':>26s}" for m in METHODS))
for key, s in summary.items():
    print(f"{key:22s} {s['max_noise_mm']:14.3e}  " + "  ".join(
        f"{s[m]['false_drop']:>8d}/{s[m]['false_keep']:>6d}/{s[m]['undecidable']:>5d}/{s[m]['band_keep']:>4d}k" for m in METHODS))
if len(sys.argv) > 2:
    json.dump({"n_per_case": N, "deltas_mm": DELTAS_MM, "offsets_mm": OFFSETS_MM, "summary": summary, "cases": res,
               "max_noise_mm_by_case": noise}, open(sys.argv[2], "w"), indent=1)

per = len(ROTS) * len(DEPTHS) * N
print()
print("keep rate per drafted delta (mm), pooled over units, rotations and depths")
offs = sorted({k.split("|")[1] for k in summary}, key=lambda x: float(x.split("=")[1][:-2]))
for m in ("FROZEN", "EPS_FIXED", "FP_BOUND", "HYBRID"):
    print(m)
    print(f"  {'delta_mm':>9s} " + " ".join(f"{o:>16s}" for o in offs))
    for d in DELTAS_MM:
        row = []
        for o in offs:
            kept = sum(summary[f"{u}|{o}"][m]["keep_by_delta"][f"{d:g}"] for u in UNITS)
            row.append(f"{kept / (per * len(UNITS)):16.3f}")
        print(f"  {d:9.0e} " + " ".join(row))
