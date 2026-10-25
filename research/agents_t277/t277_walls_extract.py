"""T-277 blockwork consequence extractor: which block walls lie under each CONFLICT band, and how much of each wall's
centreline changes cover (beam soffit vs slab soffit) between the drawn width and the scheduled width.

    .work/venv/bin/python -I research/agents_t277/t277_walls_extract.py <scratch>/t125_inputs.pkl \
        <scratch>/t277_geometry.json [--write]

Inputs (both outside the repository): the T-125 wall bands of Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip
(P7757.dxf, sha ab54dd55; `research/agents_t125/alsenan_v2_dump.py`, unchanged) and this task's geometry capture of
'ST7757 dxf.dxf' (t277_extract.py). Frames: the architectural plan is laid on the roof-slab plan of the same storey by a
pure translation found here from the column outlines (arch columns of the wall stage vs S-COL.BON centres; T-108 /
T-143 method, re-derived, residual printed). Output ALSENAN_T277_WALLS.json: per CONFLICT band and per wall (V2 run
id), the centreline length inside the band at the drawn width and at the scheduled width with either drawn face kept
(the census never decides which face would move), its crossing angle; lengths only, no coordinates.
"""
from __future__ import annotations

import json
import math
import pickle
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLAB_OF = {"GF": "GF", "1F": "1F", "2F": "2F"}   # walls of storey X sit under the roof slab of storey X (T-213)
# CONFLICT labels of the census (sheet, label handle) -> the run they name (register member / component); the band is
# the drawn edge pair the census bound at the run centre
CONFLICT_RUNS = [
    ("GF", "BM-GF-054", "BEAMS:GF:BAND0008", "B29"),
    ("GF", "BM-GF-055", "BEAMS:GF:BAND0036.1", "CB2"),
    ("GF", "BM-GF-055", "BEAMS:GF:BAND0036.2", "CB2"),
    ("GF", "BM-GF-056", "BEAMS:GF:BAND0042", "B21"),
    ("1F", "BM-1F-030", "BEAMS:1F:BAND0009", "B6"),
    ("1F", "BM-1F-031", "BEAMS:1F:BAND0026.1", "CB10"),
    ("1F", "BM-1F-031", "BEAMS:1F:BAND0026.2", "CB10"),
]


def align(arch_cols, st_cols):
    """pure translation arch -> ST from column centres (best count within 0.06 m, then the mean of the matches)."""
    ac = [(sum(p[0] for p in q) / len(q), sum(p[1] for p in q) / len(q)) for q in arch_cols if len(q) >= 3]
    best = None
    for a in ac:
        for s in st_cols:
            t = (s[0] - a[0], s[1] - a[1])
            n = sum(1 for x in ac if min(math.hypot(x[0] + t[0] - y[0], x[1] + t[1] - y[1]) for y in st_cols) < 0.06)
            if best is None or n > best[0]:
                best = (n, t)
    n, t = best
    pairs = []
    for x in ac:
        y = min(st_cols, key=lambda y: math.hypot(x[0] + t[0] - y[0], x[1] + t[1] - y[1]))
        if math.hypot(x[0] + t[0] - y[0], x[1] + t[1] - y[1]) < 0.06:
            pairs.append((x, y))
    t = (sum(y[0] - x[0] for x, y in pairs) / len(pairs), sum(y[1] - x[1] for x, y in pairs) / len(pairs))
    res = max(math.hypot(x[0] + t[0] - y[0], x[1] + t[1] - y[1]) for x, y in pairs)
    return t, len(pairs), len(ac), res


def inside_len(c, base, u, n, o_lo, o_hi, s_lo, s_hi, step=0.002, where=None):
    """length of polyline c inside the strip o_lo <= o <= o_hi, s_lo <= s <= s_hi (frame: base, u, n), by 2 mm
    sampling (adequate: the strips are >= 0.05 m and the answer is reported to 1 mm)."""
    tot = 0.0
    acc = 0.0
    for a, b in zip(c, c[1:]):
        L = math.dist(a, b)
        k = max(1, int(L / step))
        for i in range(k):
            t = (i + 0.5) / k
            x, y = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
            s = (x - base[0]) * u[0] + (y - base[1]) * u[1]
            o = (x - base[0]) * n[0] + (y - base[1]) * n[1]
            if s_lo <= s <= s_hi and o_lo <= o <= o_hi:
                tot += L / k
                if where is not None:
                    where.append(acc + t * L)
        acc += L
    return tot


def main(argv):
    ins = pickle.load(open(argv[0], "rb"))
    g = json.load(open(argv[1], encoding="utf-8"))
    v2 = json.load(open(argv[2], encoding="utf-8"))
    cen = json.load(open(HERE / "ALSENAN_T277_INPUT.json", encoding="utf-8"))
    import csv
    reg = {(r["member_id"], r["component"]): r for r in
           csv.DictReader(open(HERE.parent / "agents_t110" / "BEAM_MEMBER_REGISTER.csv", encoding="utf-8"))}
    runs = {(r["member"], r["component"]): r for r in cen["run_centres"]}
    sched = {s["mark"]: float(s["W"]) / 100.0 for s in cen["schedule"]}
    lines = {sh: {l[0]: (tuple(l[1]), tuple(l[2])) for l in g["lines"][sh]} for sh in g["lines"]}
    out = dict(schema="T277_WALLS_V1", arch_sha256_prefix="ab54dd55", st_sha256_prefix="9f9d1179", align={}, bands=[])
    cols_st = {sh: g["columns"][sh] for sh in ("GF", "1F", "2F")}
    for sh in ("GF", "1F"):
        f = ins["floors"][sh]
        t, n, na, res = align(f["columns_m"], [tuple(c) for c in cols_st[sh]])
        out["align"][sh] = dict(matched=n, arch_columns=na, resid_m=round(res, 4))
        walls = []
        for w in f["walls"]:
            cl = [(x * f["unit_m"] + t[0], y * f["unit_m"] + t[1]) for x, y in (w.get("centreline") or [])]
            if len(cl) >= 2:
                walls.append((w["wall_id"], w.get("t_m"), cl))
        for st_, mem, comp, mark in CONFLICT_RUNS:
            if st_ != sh:
                continue
            rc = runs[(mem, comp)]
            rd = rc["stations"][0]["readings"][0]
            h1, h2 = rd["edges"][0][0], rd["edges"][1][0]
            e1, e2 = lines[sh][h1], lines[sh][h2]
            r = reg[(mem, comp)]
            cx, cy, L = float(r["x"]), float(r["y"]), float(r["length_m"])
            p, q = e1
            Le = math.dist(p, q)
            u = ((q[0] - p[0]) / Le, (q[1] - p[1]) / Le)
            nn = (-u[1], u[0])
            o2 = (e2[0][0] - p[0]) * nn[0] + (e2[0][1] - p[1]) * nn[1]
            sc = (cx - p[0]) * u[0] + (cy - p[1]) * u[1]
            s_lo, s_hi = sc - L / 2.0, sc + L / 2.0
            lo, hi = min(0.0, o2), max(0.0, o2)
            wd = hi - lo
            ws = sched[mark]
            dw = ws - wd
            variants = {"drawn": (lo, hi), "schedule_keep_face_%s" % (h1 if o2 > 0 else h2): (lo, lo + ws),
                        "schedule_keep_face_%s" % (h2 if o2 > 0 else h1): (hi - ws, hi)}
            rows = []
            split = {}
            for x in v2["floors"][sh]["v2"]["stretches"]:
                if not x.get("in_run", True):
                    split.setdefault(x["wall_id"], []).append((x["from_m"], x["to_m"]))
            for wid, tw, cl in walls:
                where = []
                lens = {k: inside_len(cl, p, u, nn, a, b, s_lo, s_hi, where=where if k == "drawn" else None)
                        for k, (a, b) in variants.items()}
                if max(lens.values()) < 0.001:
                    continue
                wh = []
                inside_len(cl, p, u, nn, min(v[0] for v in variants.values()), max(v[1] for v in variants.values()),
                           s_lo, s_hi, where=wh)
                sp = sorted(split.get(wid, ()))
                pieces = sorted({1 + sum(1 for a_, b_ in sp if b_ < s_) for s_ in wh})
                in_split = any(any(a_ <= s_ <= b_ for a_, b_ in sp) for s_ in wh)
                # crossing angle between the wall centreline piece and the band axis
                ang = None
                for a_, b_ in zip(cl, cl[1:]):
                    d = (b_[0] - a_[0], b_[1] - a_[1])
                    if math.hypot(*d) > 1e-6:
                        ang = round(math.degrees(math.acos(min(1.0, abs(d[0] * u[0] + d[1] * u[1]) / math.hypot(*d)))), 2)
                        break
                rows.append(dict(wall_run=wid, v2_pieces=["%s#%d" % (wid, k) for k in pieces] if sp else [wid],
                                 at_centreline_m=[round(min(wh), 3), round(max(wh), 3)], in_split_stretch=in_split,
                                 t_m=tw, angle_to_band_deg=ang,
                                 len_m={k: round(v, 3) for k, v in lens.items()}))
            out["bands"].append(dict(storey=sh, member=mem, component=comp, mark=mark, edges=[h1, h2],
                                     drawn_m=round(wd, 4), schedule_m=ws, delta_b_m=round(dw, 4), run_len_m=L,
                                     walls=rows))
    print(json.dumps(out["align"]))
    for b in out["bands"]:
        print(b["storey"], b["component"], b["mark"], b["drawn_m"], b["schedule_m"],
              [(w["v2_pieces"], w["in_split_stretch"], w["t_m"], w["angle_to_band_deg"], w["len_m"]) for w in b["walls"]])
    if "--write" in argv:
        (HERE / "ALSENAN_T277_WALLS.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
