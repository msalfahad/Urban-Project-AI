"""Stage 2 evidence (synthetic, read-only): the robust predicate "keep when value >= T - m" is obtained EXACTLY by
calling the frozen opening_census functions with the threshold T - m, because each of the three thresholds is used
in exactly one strict comparison (`L < min_len` in face_lines, `hi - lo < min_overlap` in wall_bands, `g < min_gap`
in band_gaps). So ARCH_TAKEOFF_V2.1 can use robust thresholds without any change to the pinned file.

For each site, drafted values T + delta are placed at several rotations and site offsets; the set the frozen function
keeps with threshold T - m is compared with the reference predicate value >= T - m computed on the same values.
m = max(1e-6 mm, 16 u M (d + 1)) in drawing units (round 2, Q1). Exit 1 on any difference.
usage: python3 -I research/freeze_integrity/stage2_threshold_shift_check.py [OUT_JSON]"""
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.source import opening_census as OC          # noqa: E402

U = 2.0 ** -53
DELTAS = [-1e-2, -1e-5, -3e-6, -1e-6, -1e-9, 0.0, 1e-9, 1e-6, 1e-3]
ROTS = [0.0, 90.0, 30.0, 45.0]
OFFS = [0.0, 1e6, 1e7]
rng = random.Random(20261013)


def place(p, rot, at):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return (p[0] * c - p[1] * s + at[0], p[0] * s + p[1] * c + at[1])


def margin(segs, k):
    M = max(abs(v) for _, a, b in segs for v in (*a, *b))
    return max(1e-6 * k, 16 * U * M * 2)


res, bad = {}, 0
for unit, unit_m in (("mm", 1e-3), ("m", 1.0)):
    k = 1e-3 / unit_m
    for rot in ROTS:
        for off in OFFS:
            at = (off * k + rng.uniform(0, 1000) * k, -off * k + rng.uniform(0, 1000) * k)
            P = lambda x, y: place((x * k, y * k), rot, at)
            n = agree = 0
            for d in DELTAS:
                # PIECE: one 100 mm + d piece; the frozen face_lines with min_len = T - m keeps it iff L >= T - m
                segs = [("P", P(0, 0), P(100 + d, 0))]
                m = margin(segs, k)
                T = 100.0 * k - m
                kept = any("P" in ids for ln in OC.face_lines(segs, ang_res_deg=0.5, off_tol=2 * k, join_tol=5 * k, min_len=T)
                           for *_, ids in ln["cover"])
                L = math.dist(segs[0][1], segs[0][2])
                n += 1; agree += kept == (L >= T)
                # OVERLAP: two faces 200 mm apart overlapping by 300 + d mm
                segs = [("A", P(0, 0), P(1000, 0)), ("B", P(700 - d, 200), P(1700, 200))]
                m = margin(segs, k)
                fl = OC.face_lines(segs, ang_res_deg=0.5, off_tol=2 * k, join_tol=5 * k, min_len=100 * k - m)
                T = 0.3 / unit_m - m
                bands = OC.wall_bands(fl, 0.10 / unit_m, 0.45 / unit_m, min_overlap=T)
                lo = max(l["lo"] for l in fl) if len(fl) == 2 else None
                hi = min(l["hi"] for l in fl) if len(fl) == 2 else None
                if lo is not None:
                    n += 1; agree += bool(bands) == (hi - lo >= T)
                # GAP: a band with a 500 + d mm gap
                segs = [("A1", P(0, 0), P(1000, 0)), ("A2", P(1500 + d, 0), P(3000, 0)),
                        ("B1", P(0, 200), P(1000, 200)), ("B2", P(1500 + d, 200), P(3000, 200))]
                m = margin(segs, k)
                fl = OC.face_lines(segs, ang_res_deg=0.5, off_tol=2 * k, join_tol=5 * k, min_len=100 * k - m)
                bands = OC.wall_bands(fl, 0.10 / unit_m, 0.45 / unit_m, min_overlap=0.3 / unit_m - m)
                T = 0.5 / unit_m - m
                for b in bands:
                    gaps = OC.band_gaps(b, min_gap=T, jamb_tol=0.03 / unit_m)
                    cov = OC._union([(x, y, i) for x, y, i in OC._covers(b["A"]["cover"], b["lo"], b["hi"]) +
                                     OC._covers(b["B"]["cover"], b["lo"], b["hi"])], 1.0)
                    want = sum(1 for (_, e0, _), (s1, _, _) in zip(cov, cov[1:]) if s1 - e0 >= T)
                    n += 1; agree += len(gaps) == want
            res[f"{unit}|rot={int(rot)}|off={off:g}mm"] = {"checks": n, "agree": agree}
            bad += n - agree
out = {"equivalent": bad == 0, "disagreements": bad, "cases": res,
       "claim": "frozen function(threshold = T - m) keeps exactly the values >= T - m, at all three sites"}
print(json.dumps({"equivalent": out["equivalent"], "disagreements": bad, "checks": sum(v["checks"] for v in res.values())}))
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
sys.exit(0 if bad == 0 else 1)
