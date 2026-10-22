"""T-143 hand helper (research only): what sits on each wall band of the architectural plans.

Samples every wall band centreline (V2 inputs, T-125) every 0.02 m, drops samples inside a column outline or inside a
stretch MASONRY_CENTRELINE_V2 splits out (not wall), moves each sample onto the structural roof-slab plan of the same
floor (pure translation found from the column outlines, align.json), and records what is directly above it:
a beam band of the route G overlay (T-110 member register: mark, b x h, status), else a slab face of T-139 (class,
thickness), else nothing drawn. Output: per band, the stretches by member with their length (m).
Usage: python3 -I heights.py <scratch>
"""
import csv
import json
import math
import pickle
import sys
from collections import defaultdict

from shapely.geometry import Point, Polygon
from shapely import wkt as W

S = sys.argv[1]
STEP = 0.02
TOL = 0.03          # a centreline point within 3 cm of a beam band is under that beam

ins = pickle.load(open(f"{S}/t125_inputs.pkl", "rb"))
v2 = json.load(open(f"{S}/t125_v2.json"))
bands = json.load(open(f"{S}/bands.json"))
align = json.load(open(f"{S}/align.json"))
reg = list(csv.DictReader(open(f"{S}/wb/research/agents_t110/BEAM_MEMBER_REGISTER.csv")))
faces = json.load(open(f"{S}/faces.json"))
panels = {r["id"]: r for r in csv.DictReader(open(f"{S}/panels.csv"))}

# register rows by band key
REG = {}
for r in reg:
    c = r["component"].split(":")
    if c[0] == "BEAMS":
        k = c[2]
        if "+" in k:                                  # BAND0047.1+.2 -> both halves
            base = k.split(".")[0]
            for s in (".1", ".2"):
                REG[f"{base}{s}@{c[1]}"] = r
        else:
            REG[f"{k}@{c[1]}"] = r
    elif c[0] == "RING" and "BAND0033-0036" in c[2]:
        for n in range(33, 37):
            REG[f"BAND{n:04d}@{c[1]}"] = r

BP = {st: [] for st in ("GF", "1F", "2F")}
for k, v in bands.items():
    st = k.split("@")[1]
    P = Polygon(v["pts"]).buffer(0)
    BP[st].append((k, v["title"], P))
FP = {st: [(f["id"], W.loads(f["wkt"])) for f in fl] for st, fl in faces.items()}


def above(st, x, y):
    p = Point(x, y)
    hits = []
    for k, title, P in BP[st]:
        if P.distance(p) <= TOL:
            r = REG.get(k)
            hits.append((k, title, r))
    if hits:
        return ("BEAM", hits)
    for fid, F in FP[st]:
        if F.contains(p):
            pr = panels.get(fid) or {}
            return ("FACE", [(fid, pr.get("cls", "?"), pr.get("t", ""), (pr.get("evidence") or "")[:120])])
    return ("NONE", [])


def poly_len(c):
    return sum(math.dist(c[i], c[i + 1]) for i in range(len(c) - 1))


def at(c, s):
    for i in range(len(c) - 1):
        L = math.dist(c[i], c[i + 1])
        if s <= L or i == len(c) - 2:
            t = 0 if L == 0 else min(max(s / L, 0), 1)
            return (c[i][0] + t * (c[i + 1][0] - c[i][0]), c[i][1] + t * (c[i + 1][1] - c[i][1]))
        s -= L


ANNEX_X_MAX = -148.90
LIFT_BOX = (-142.60, -140.30, -797.25, -794.95)
SAMPLES = {}
out = {}
for fl, f in ins["floors"].items():
    u = f["unit_m"]
    sh = align[fl]["shift"]
    cols = [Polygon(q) for q in f["columns_m"] if len(q) >= 3]
    split = defaultdict(list)
    for st in v2["floors"][fl]["v2"]["stretches"]:
        if not st.get("in_run", True):
            split[st["wall_id"]].append((st["from_m"], st["to_m"]))
    for w in f["walls"]:
        c = [(x * u, y * u) for x, y in (w.get("centreline") or [])]
        if len(c) < 2:
            continue
        L = poly_len(c)
        n = max(1, int(L / STEP))
        segs = defaultdict(float)
        detail = {}
        dropped = defaultdict(float)
        spl = sorted(split.get(w["wall_id"], ()))
        smp = []
        for i in range(n):
            s = (i + 0.5) * L / n
            ds = L / n
            if any(a <= s <= b for a, b in split.get(w["wall_id"], ())):
                dropped["SPLIT_OUT_NOT_WALL"] += ds
                continue
            x, y = at(c, s)
            if any(P.contains(Point(x, y)) for P in cols):
                dropped["COLUMN"] += ds
                continue
            kind, hits = above(fl, x + sh[0], y + sh[1])
            if kind == "BEAM":
                # the lowest underside wins (deepest member) when two bands meet over the wall
                def dep(h):
                    r = h[2]
                    try:
                        return float(r["depth_m"])
                    except Exception:
                        return 9.0              # unknown depth sorts first -> HELD
                h = max(hits, key=dep)
                r = h[2]
                key = ("BEAM", h[0], r["member_id"] if r else "NO_REGISTER_ROW", r["mark"] if r else h[1],
                       r["status"] if r else "UNKNOWN", r["width_m"] if r else "", r["depth_m"] if r else "")
                if len(hits) > 1:
                    detail[key] = "junction of " + ", ".join(sorted({x[0] for x in hits}))
            elif kind == "FACE":
                fid, cls, t, ev = hits[0]
                key = ("FACE", fid, cls, t)
                detail.setdefault(key, ev)
            else:
                key = ("NONE",)
            segs[key] += ds
            ix = 1 + sum(1 for a, b in spl if b < s)
            zone = "annex" if (fl == "GF" and x < ANNEX_X_MAX) else "main"
            lift = fl == "GF" and LIFT_BOX[0] <= x <= LIFT_BOX[1] and LIFT_BOX[2] <= y <= LIFT_BOX[3]
            smp.append((ix, zone, lift, list(key), ds))
        SAMPLES[f"{fl}|{w['wall_id']}"] = smp
        out[f"{fl}|{w['wall_id']}"] = {
            "floor": fl, "wall_id": w["wall_id"], "t_m": w.get("t_m"), "band_len_m": round(L, 4),
            "x0": round(c[0][0], 3), "y0": round(c[0][1], 3), "x1": round(c[-1][0], 3), "y1": round(c[-1][1], 3),
            "dropped": {k: round(v, 3) for k, v in dropped.items()},
            "above": [{"key": list(k), "len_m": round(v, 3), "note": detail.get(k, "")} for k, v in
                      sorted(segs.items(), key=lambda kv: -kv[1])]}
json.dump(out, open(f"{S}/above.json", "w"), indent=1)
json.dump(SAMPLES, open(f"{S}/samples.json", "w"))
for k, v in out.items():
    print(k, v["t_m"], v["band_len_m"], v["dropped"], [(a["key"][:4] if a["key"][0] == "FACE" else
          (a["key"][3], a["key"][4], a["key"][6]), a["len_m"]) for a in v["above"]])
