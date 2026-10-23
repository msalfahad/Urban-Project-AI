"""T-215 part 1: the GF 45 deg / column wall-end bounds of T-108 r2 closed from the drawn faces (development villa).

Reads at run time (outside the repository): the T-125 capture of P7757.dxf (Drive "Alsenan chalet project" /
P7757_DXF_COMPRESSED.zip) made by research/agents_t125/alsenan_v2_dump.py, and the V2 run made by alsenan_v2_run.py.
Every face is named by its DXF handle; no coordinate is written. Writes research/agents_t215/T215_ENDS.csv (numbers and
ids only). `--check` recomputes and compares with the committed file.

Also reads ST7757 dxf.dxf (Drive "Alsenan chalet project") for the member above each closed piece: the GROUND FLOOR
ROOF SLAB plan is placed on the architectural plan by one translation found from the column outlines (S-COL.BON, every
architectural GF column matched, residual printed); beam faces by handle, sizes from the T-110 member register.

Usage (Python 3.11):
    python3 -I research/agents_t215/alsenan_t215_ends.py <scratch>/t125_inputs.pkl <scratch>/t125_v2.json <ST7757.dxf>
        [--check]
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


# Owner Q-60 A: block height = storey height - depth of the member above. GF storey 4.50 (T-108 / T-143); the GF roof
# slab over these junctions is 0.16 (ST p.8 note 18; T-139 panels GF-015 / 016 / 027 / 039 / 052, T-143 rows).
GF_STOREY, GF_SLAB = 4.50, 0.16
# Members above, per cluster: (label, ST face handles (two parallel faces), extent handles or None, depth m, cases).
# CB2 (BM-GF-055) is a T-110 CONFLICT: schedule width 0.20 vs drawn 0.25 (owner Q-61 C(1): never pick). Case
# "drawn" uses both drawn faces; case "schedule-flush-out" a 0.20 band on the drawn outer face, which leaves the
# 0.05 m strip under the slab. Any other placement of a 0.20 band lies between the two.
MEMBERS = {
    "J-A": [("CB2 BM-GF-055 0.5 deep", ("278", "274"), 0.50, "CB2"),
            ("B3 BM-GF-024 0.20 x 0.40", ("291", "28E"), 0.40, None)],
    "J-D": [("B1 / B3 band on the GF-W13 line 0.40 deep", ("291", "28E"), 0.40, None)],
}


def st_translation(st_doc, cols_arch_m):
    """One translation ST -> architectural plan from the column outlines: every architectural column matched to an
    ST column of the same size; returns (dx, dy) in metres and the worst residual (m)."""
    import numpy as np
    from collections import Counter
    sc = []
    for e in st_doc.modelspace().query('LWPOLYLINE[layer=="S-COL.BON"]'):
        p = np.array([(x * K, y * K) for x, y, *_ in e.get_points()])
        if len(p) >= 3:
            sc.append((p.mean(0), tuple(np.round(p.max(0) - p.min(0), 3))))
    ac = [(np.array(q).mean(0), tuple(np.round(np.array(q).max(0) - np.array(q).min(0), 3))) for q in cols_arch_m]
    votes = Counter()
    for a, sa in ac:
        for c, ss in sc:
            if sa == ss or sa == ss[::-1]:
                votes[tuple(np.round(c - a, 3))] += 1
    (tx, ty), n = votes.most_common(1)[0]
    t = np.array((tx, ty))
    res = max(min(np.linalg.norm(c - (a + t)) for c, _ in sc) for a, _ in ac)
    if n != len(ac) or res > 0.005:
        raise ValueError(f"column match {n} / {len(ac)}, residual {res:.4f} m: no single translation")
    return t, res


def member_polys(st_doc, cid, t, case):
    """Member bands of a cluster in architectural metres for one CB2 case."""
    from shapely.geometry import Polygon
    out = []
    for label, (h1, h2), depth, flag in MEMBERS.get(cid, ()):
        e1, e2 = st_doc.entitydb[h1], st_doc.entitydb[h2]
        a1, b1 = e1.dxf.start, e1.dxf.end
        a2, b2 = e2.dxf.start, e2.dxf.end
        pts = [(a1.x, a1.y), (b1.x, b1.y), (b2.x, b2.y), (a2.x, a2.y)]
        if abs(a1.y - b1.y) < 1 and abs(a2.y - b2.y) < 1:          # horizontal band: overlap of the two faces in x
            x0 = max(min(a1.x, b1.x), min(a2.x, b2.x))
            x1 = min(max(a1.x, b1.x), max(a2.x, b2.x))
            y1f, y2f = a1.y, a2.y
            if flag == "CB2" and case == "schedule-flush-out":
                y1f = y2f - 200.0 if y2f > y1f else y2f + 200.0
            pts = [(x0, y1f), (x1, y1f), (x1, y2f), (x0, y2f)]
        elif abs(a1.x - b1.x) < 1 and abs(a2.x - b2.x) < 1:        # vertical band: overlap in y
            y0 = max(min(a1.y, b1.y), min(a2.y, b2.y))
            y1 = min(max(a1.y, b1.y), max(a2.y, b2.y))
            pts = [(a1.x, y0), (a1.x, y1), (a2.x, y1), (a2.x, y0)]
        else:
            raise ValueError(f"{label}: faces not axis-parallel; give the band explicitly")
        out.append((Polygon([(x * K - t[0], y * K - t[1]) for x, y in pts]), GF_STOREY - depth))
    return out


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


def build(pkl, v2json, stdxf):
    import ezdxf
    st_doc = ezdxf.readfile(stdxf)
    cap = pickle.load(open(pkl, "rb"))["floors"]["GF"]
    v2 = json.load(open(v2json))["floors"]["GF"]["v2"]
    assert abs(cap["unit_m"] - K) < 1e-12
    index = {s["id"]: s for s in cap["ents"]["segments"]}
    recs = {w["wall_id"]: w for w in cap["walls"]}
    cols = [[(x, y) for x, y in q] for q in cap["columns_m"]]
    t, res = st_translation(st_doc, cols)
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
        dm2 = {}
        for case in ("drawn", "schedule-flush-out"):
            g = J.gross_change(walls, r, member_polys(st_doc, c["id"], t, case), GF_STOREY - GF_SLAB)
            for k, v in g.items():
                dm2.setdefault(k, []).append(v)
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
                         "d_gross_m2_lo": f"{min(dm2[wid]):+.4f}", "d_gross_m2_hi": f"{max(dm2[wid]):+.4f}",
                         "members_above": "; ".join(m[0] for m in MEMBERS.get(c["id"], ())) or "slab 0.16 only",
                         "st_fit_residual_mm": f"{res * 1000:.1f}",
                         "what": c["what"]})
    return rows


def _in(q, p):
    from shapely.geometry import Point, Polygon
    return Polygon(q).buffer(1e-6).contains(Point(p))


def row_effect(rows):
    """Per T-108 row: the closed length change and the gross m2 change, both from the drawings: the closed piece's area
    from the plan faces, its height from the member drawn above it on the ST GF roof-slab plan (owner Q-60 A). EXACT
    when every case agrees; BOUNDED only by a named member CONFLICT (CB2 width, Q-61 C(1)); never a weighted mean."""
    t108 = {r["row_id"]: r for r in csv.DictReader(open(ROOT / "research/agents_t108/T108_BY_WALL.csv",
                                                       encoding="utf-8"))}
    acc = {}
    for r in rows:
        a = acc.setdefault(r["row_id"], [0.0, 0.0, 0.0])
        a[0] += float(r["delta_m"])
        a[1] += float(r["d_gross_m2_lo"])
        a[2] += float(r["d_gross_m2_hi"])
    out = []
    for rid in sorted(acc):
        d, lo, hi = acc[rid]
        b = t108[rid]
        exact = abs(hi - lo) < 5e-5
        out.append({"row_id": rid, "t_m": b["t_m"], "block_type": b["block_type"],
                    "t108_physical_m": b["physical_length_m"],
                    "t108_held_end_max_m": f"{BOUND[rid]:.3f}" if BOUND[rid] else "",
                    "delta_m": f"{d:+.4f}", "closed_length_m": f"{float(b['physical_length_m']) + d:.4f}",
                    "length_status": "DRAWING-CONFIRMED (plan faces; held bound closed)",
                    "d_gross_m2_min": f"{lo:+.4f}", "d_gross_m2_max": f"{hi:+.4f}",
                    "m2_status": "DRAWING-CONFIRMED (member above read on the ST slab plan)" if exact else
                                 "BOUNDED (CB2 width CONFLICT 0.20 schedule / 0.25 drawn, Q-61 C(1))",
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
    ap.add_argument("stdxf")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    rows = build(a.pkl, a.v2json, a.stdxf)
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
