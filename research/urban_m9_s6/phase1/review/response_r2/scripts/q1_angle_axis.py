"""Q1 follow-up: the 0.5-degree angle bin of opening_census.face_lines measures along the BIN axis, not the faces'
own direction; across a wall of thickness t the second face's along-positions shift by t * sin(dtheta), dtheta <= 0.25
deg. Variant MEAN_AXIS keeps the bin for grouping only and measures along the length-weighted mean direction of the
segments in the bin (doubled-angle mean). Run the q1_threshold_sites cases at random angles, frozen axis vs mean axis.
usage: python3 -I q1_angle_axis.py SRC [N] [JSON_OUT]"""
import json, math, random, sys
from collections import defaultdict
SRC = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 400
sys.path.insert(0, SRC)
from engine.source import opening_census as OC
from engine.source import opening_gaps as OG
FROZEN = OC.face_lines


def face_lines_mean_axis(segments, ang_res_deg=0.1, off_tol=2.0, join_tol=1.0, min_len=1.0):
    bins = defaultdict(list)
    for sid, a, b in segments:
        L = math.dist(a, b)
        if L < min_len:
            continue
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0
        key = round(round(ang / ang_res_deg) * ang_res_deg, 6) % 180.0
        bins[key].append((sid, a, b, L, ang))
    lines = []
    for key in sorted(bins):
        mem = bins[key]
        cx = sum(L * math.cos(math.radians(2 * ang)) for *_x, L, ang in mem)
        cy = sum(L * math.sin(math.radians(2 * ang)) for *_x, L, ang in mem)
        th = math.degrees(math.atan2(cy, cx)) / 2.0
        u, n = OC.frame_of(th)
        items = sorted((OC.along(a, n), *sorted((OC.along(a, u), OC.along(b, u))), sid) for sid, a, b, L, ang in mem)
        cur = None
        for off, t0, t1, sid in items:
            if cur is not None and off - cur["_last"] <= off_tol:
                cur["_iv"].append((t0, t1, [sid])); cur["_offs"].append(off); cur["_last"] = off
            else:
                cur = {"ang": key, "u": u, "n": n, "_iv": [(t0, t1, [sid])], "_offs": [off], "_last": off}
                lines.append(cur)
    for ln in lines:
        ln["off"] = sum(ln["_offs"]) / len(ln["_offs"])
        ln["cover"] = OC._union(ln.pop("_iv"), join_tol)
        ln["lo"], ln["hi"] = ln["cover"][0][0], ln["cover"][-1][1]
        del ln["_offs"], ln["_last"]
    for i, ln in enumerate(lines):
        ln["line_id"] = f"FL{i + 1:04d}"
    return lines


ns = {}
exec(open(sys.argv[0].replace("q1_angle_axis.py", "q1_threshold_sites.py")).read().split("ERR = []\nres = {}")[0]
     .replace("SRC = sys.argv[1]", "SRC = %r" % SRC).replace("N = int(sys.argv[2]) if len(sys.argv) > 2 else 500", "N = %d" % N), ns)
rng = random.Random(11)
res = {}
for axis, fn in (("BIN_AXIS (frozen)", FROZEN), ("MEAN_AXIS", face_lines_mean_axis)):
    OC.face_lines = fn
    for kind in ("PIECE", "OVERLAP", "GAP"):
        for unit, unit_m in (("mm", 1e-3), ("m", 1.0)):
            for off in (0.0, 1e6, 3.3e9):
                ns["ERR"] = []
                ok = 0
                for _ in range(N):
                    r = rng.uniform(0, 360)
                    at = (round(rng.uniform(-1, 1) * (off + 1000), 3), round(rng.uniform(-1, 1) * (off + 1000), 3))
                    ok += ns["run"](kind, unit_m, r, at, True)
                res[f"{axis}|{kind}|{unit}|rot=random|off={off:g}mm"] = {"found_robust": ok / N,
                    "max_measured_error_mm": max(ns["ERR"]) if ns["ERR"] else None}
OC.face_lines = FROZEN
w = max(map(len, res))
for c, v in res.items():
    e = v["max_measured_error_mm"]
    print(f"{c:{w}s} {v['found_robust']:7.3f} {('%.3e' % e) if e is not None else '-':>12s}")
if len(sys.argv) > 3:
    json.dump({"n_per_case": N, "results": res}, open(sys.argv[3], "w"), indent=1)
