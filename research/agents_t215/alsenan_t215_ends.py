"""T-215 part 1: the GF 45 deg / column wall-end bounds of T-108 r2 closed from the drawn faces (development villa).

Reads at run time (outside the repository): the T-125 capture of P7757.dxf (Drive "Alsenan chalet project" /
P7757_DXF_COMPRESSED.zip) made by research/agents_t125/alsenan_v2_dump.py, and the V2 run made by alsenan_v2_run.py.
Every face is named by its DXF handle; no coordinate is written. Writes research/agents_t215/T215_ENDS.csv (numbers and
ids only). `--check` recomputes and compares with the committed file.

Usage (Python 3.11):
    python3 -I research/agents_t215/alsenan_t215_ends.py <scratch>/t125_inputs.pkl <scratch>/t125_v2.json [--check]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import pickle
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import junction_close as J  # noqa: E402

OUT = HERE / "T215_ENDS.csv"
OUT_ROWS = HERE / "T215_ROW_EFFECT.csv"
ROOT = HERE.parents[1]
K = 0.001                     # drawing unit = mm (capture unit_m)

# ledger row id (T-108) <- V2 run id; the band FL0063-FL0064 is split by V2 into #1 (GF-W21) and #2 (GF-W20)
ROW = {"WB-FL0070-FL0072": "GF-W22", "WB-FL0102-FL0103": "GF-W34", "WB-FL0063-FL0064#1": "GF-W21",
       "WB-FL0063-FL0064#2": "GF-W20", "WB-FL0046-FL0047": "GF-W33", "WB-FL0100-FL0101": "GF-W31",
       "WB-FL0048-FL0049": "GF-W32", "WB-FL0068-FL0069": "GF-W13"}
# T-108 r2 HELD bound per row (m, 0 .. max, never added) - the value this task closes
BOUND = {"GF-W13": 0.200, "GF-W20": 0.137, "GF-W21": 0.137, "GF-W31": 0.137, "GF-W32": 0.278, "GF-W33": 0.217,
         "GF-W34": 0.256, "GF-W22": 0.0}

# Junction clusters. Each arm: (run id, which end of its band is at the junction (0 / 1), window from the counted end
# (m), through?). Faces: wall-layer and column-outline handles that bound the junction masonry.
CLUSTERS = [
    {"id": "J-A", "what": "GF-W22 stem + GF-W34 45 deg stem under the north wall face (G-T108-1 junction piece)",
     "arms": [("WB-FL0070-FL0072", 1, 0.5, False), ("WB-FL0102-FL0103", 1, 0.5, False)],
     "faces": ["D2:528:0", "D2:545:0", "D2:806:0", "D2:807:0"],
     "closing": [("D2:625:0", "D2:691:0")]},      # the north wall's near face, drawn with a gap where the stems join
    {"id": "J-B", "what": "GF-W21 vertical turning 45 deg into GF-W33 (one bent wall, no through wall)",
     "arms": [("WB-FL0063-FL0064#1", 1, 0.5, False), ("WB-FL0046-FL0047", 0, 0.5, False)],
     "faces": ["D2:190:0", "D2:736:0", "D2:792:0", "D2:793:0"], "closing": []},
    {"id": "J-C", "what": "Y node: GF-W20 vertical splitting into GF-W31 (SE) and GF-W32 (SW, door OP-018 next to it)",
     "arms": [("WB-FL0063-FL0064#2", 0, 0.5, False), ("WB-FL0100-FL0101", 1, 0.5, False),
              ("WB-FL0048-FL0049", 1, "OP-018", False)],
     "faces": ["D2:189:0", "D2:735:0", "D2:804:0", "D2:805:0", "D2:796:0", "D2:791:0"], "closing": []},
    {"id": "J-D", "what": "GF-W32 45 deg end and GF-W13 top end at the column on the GF-W13 line",
     "arms": [("WB-FL0048-FL0049", 0, 0.5, False), ("WB-FL0068-FL0069", 1, 0.5, False)],
     "faces": ["D2:795:0", "D2:799:0", "D2:530:0", "D2:546:0"], "closing": [], "column_faces": True},
]


def _seg(index, h):
    s = index[h]
    return ((s["a"][0] * K, s["a"][1] * K), (s["b"][0] * K, s["b"][1] * K))


def run_extent(v2, fl, run_id, rec):
    """(s0, s1) of the run along its band, metres from centreline[0]. Whole band unless V2 split it (stretches) or a
    column cut it (arch run shorter than the band: the cut is at the end the column sits on)."""
    base = run_id.split("#")[0]
    L = float(rec["gross_lm"])
    gaps = sorted((float(s["from_m"]), float(s["to_m"])) for s in v2["stretches"]
                  if s["wall_id"] == base and not s.get("in_run"))
    pieces, a = [], 0.0
    for g0, g1 in gaps:
        pieces.append((a, g0))
        a = g1
    pieces.append((a, L))
    k = int(run_id.split("#")[1]) - 1 if "#" in run_id else 0
    s0, s1 = pieces[k]
    run = next(r for r in v2["runs"] if r["run_id"] == run_id)
    return s0, s1, float(run["arch_run_lm"])


def cut_by_columns(p0, d, s0, s1, cols, arch):
    """The run's own piece of [s0, s1] once the column outlines are cut out (V1 / V2 cut columns from the run):
    the remaining piece whose length is the V2 run length (within 1 mm), else ValueError."""
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union
    seg = LineString([(p0[0] + d[0] * s0, p0[1] + d[1] * s0), (p0[0] + d[0] * s1, p0[1] + d[1] * s1)])
    rest = seg.difference(unary_union([Polygon(q) for q in cols])) if cols else seg
    parts = list(getattr(rest, "geoms", [rest]))
    tot = sum(g.length for g in parts)
    if abs(tot - arch) > 1e-3:
        raise ValueError(f"run length {arch} not reproduced by the band less columns ({tot:.4f})")
    a = min(math.dist(p0, c) for g in parts for c in g.coords)
    b = max(math.dist(p0, c) for g in parts for c in g.coords)
    if len(parts) > 1:
        raise ValueError("a column splits the run: not a single piece")
    return a, b


def build(pkl, v2json):
    cap = pickle.load(open(pkl, "rb"))["floors"]["GF"]
    v2 = json.load(open(v2json))["floors"]["GF"]["v2"]
    assert abs(cap["unit_m"] - K) < 1e-12
    index = {s["id"]: s for s in cap["ents"]["segments"]}
    recs = {w["wall_id"]: w for w in cap["walls"]}
    cols = [[(x, y) for x, y in q] for q in cap["columns_m"]]
    rows = []
    for c in CLUSTERS:
        walls, meta = [], {}
        for run_id, end, win, thr in c["arms"]:
            rec = recs[run_id.split("#")[0]]
            p0 = (rec["centreline"][0][0] * K, rec["centreline"][0][1] * K)
            p1 = (rec["centreline"][-1][0] * K, rec["centreline"][-1][1] * K)
            Lb = math.dist(p0, p1)
            d = ((p1[0] - p0[0]) / Lb, (p1[1] - p0[1]) / Lb)
            s0, s1, arch = run_extent(v2, "GF", run_id, rec)
            s0, s1 = cut_by_columns(p0, d, s0, s1, cols, arch)
            sN = s1 if end == 1 else s0
            node = (p0[0] + d[0] * sN, p0[1] + d[1] * sN)
            u = (-d[0], -d[1]) if end == 1 else d
            if isinstance(win, str):            # window at the jamb of the named opening in the run
                st = next(s for s in v2["stretches"] if s.get("ref") == win and s["wall_id"] == run_id.split("#")[0])
                win = (sN - float(st["to_m"])) if end == 1 else (float(st["from_m"]) - sN)
            walls.append(J.Wall(ROW[run_id], float(rec["t_m"]), node, u, float(win), 0.0, thr, reach_m=0.45))
            meta[ROW[run_id]] = run_id
        faces = [_seg(index, h) for h in c["faces"]]
        closing = []
        for ha, hb in c["closing"]:
            a, b = _seg(index, ha), _seg(index, hb)
            closing.append((a[1], b[0]))                       # the gap between the two drawn pieces of one face
        colp = []
        if c.get("column_faces"):
            from shapely.geometry import Polygon
            band = J.strip(walls[0]).union(J.strip(walls[1])).buffer(0.3)
            for q in cols:
                if Polygon(q).intersects(band):
                    colp.append(q)
                    faces += [(q[i], q[(i + 1) % len(q)]) for i in range(len(q))]
        M = J.masonry_from_faces(faces, walls, closing, columns=colp)
        r = J.close_junction(M, walls)
        for wid, v in r["walls"].items():
            run = next(x for x in v2["runs"] if x["run_id"] == meta[wid])
            rows.append({"cluster": c["id"], "row_id": wid, "v2_run": meta[wid], "t_m": f"{v['t_m']:.2f}",
                         "v2_physical_m": f"{float(run['arch_run_lm']):.4f}",
                         "t108_bound_max_m": f"{BOUND[wid]:.3f}",
                         "window_counted_m": f"{v['counted_len_m']:.4f}", "window_share_m2": f"{v['share_m2']:.6f}",
                         "delta_m": f"{v['delta_m']:+.4f}",
                         "closed_length_m": f"{float(run['arch_run_lm']) + v['delta_m']:.4f}",
                         "cluster_masonry_m2": f"{r['masonry_m2']:.6f}",
                         "cluster_residual_m2": f"{r['residual_m2']:.6f}",
                         "cluster_unassigned_m2": f"{r['unassigned_m2']:.6f}", "status": r["status"],
                         "what": c["what"]})
    return rows


def _in(q, p):
    from shapely.geometry import Point, Polygon
    return Polygon(q).buffer(1e-6).contains(Point(p))


def row_effect(rows):
    """Per T-108 row: the closed length change, and the gross m2 change at the member above the end piece. The member
    over the end piece was not sampled by T-143 (it sampled the band only): a row with ONE member height along its run
    gets that height (EXACT); a row with several gets the range of its own members (BOUNDED, never the weighted mean)."""
    import re
    t143 = {r["row_id"]: r for r in csv.DictReader(open(ROOT / "research/agents_t143/T143_BLOCK_BY_WALL_RUN.csv",
                                                       encoding="utf-8"))}
    t108 = {r["row_id"]: r for r in csv.DictReader(open(ROOT / "research/agents_t108/T108_BY_WALL.csv",
                                                       encoding="utf-8"))}
    acc = {}
    for r in rows:
        acc.setdefault(r["row_id"], 0.0)
        acc[r["row_id"]] += float(r["delta_m"])
    out = []
    for rid in sorted(acc):
        hs = sorted({float(h) for h in re.findall(r"-> h ([0-9.]+)", t143[rid]["members_above"])})
        d = acc[rid]
        lo, hi = sorted((d * hs[0], d * hs[-1]))
        b = t108[rid]
        out.append({"row_id": rid, "t_m": b["t_m"], "block_type": b["block_type"],
                    "t108_physical_m": b["physical_length_m"], "t108_held_end_max_m": BOUND[rid] and f"{BOUND[rid]:.3f}" or "",
                    "delta_m": f"{d:+.4f}", "closed_length_m": f"{float(b['physical_length_m']) + d:.4f}",
                    "length_status": "DRAWING-CONFIRMED (plan faces; held bound closed)",
                    "member_heights_m": " / ".join(f"{h:.2f}" for h in hs),
                    "d_gross_m2_min": f"{lo:+.4f}", "d_gross_m2_max": f"{hi:+.4f}",
                    "m2_status": "EXACT (one member along the run)" if len(hs) == 1 else
                                 "BOUNDED (member over the end piece not sampled)",
                    "d_m3_min": f"{lo * float(b['t_m']):+.4f}", "d_m3_max": f"{hi * float(b['t_m']):+.4f}",
                    "t108_net_status": b["net_status"]})
    return out


def render(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pkl")
    ap.add_argument("v2json")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    rows = build(a.pkl, a.v2json)
    txt, txt2 = render(rows), render(row_effect(rows))
    if a.check:
        ok = OUT.read_text(encoding="utf-8") == txt and OUT_ROWS.read_text(encoding="utf-8") == txt2
        print("CHECK", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    OUT.write_text(txt, encoding="utf-8")
    OUT_ROWS.write_text(txt2, encoding="utf-8")
    print(txt)
    print(txt2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
