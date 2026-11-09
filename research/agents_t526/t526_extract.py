"""T-526 drawing reader (research only, NOT engine code): the full Alsenan END census of every masonry census run on
COLUMN_END_CENSUS_V2 (end_census_v2.py), with the structural identity of every column found beyond a run end.

For every MASONRY_CENTRELINE_V2 run (t274_runs.json, both black and white walls, all storeys) and each of its two ends:
  - V2 class from the architectural column outlines (P7757.dxf, the wall stage's own capture, t125_inputs.pkl);
  - the V1 census state: is the junction listed by T-355 (SHARMAT_T355.csv) and T-317 (JOINTS_T317.csv, V rows)?
    Both key a junction by the column piece station on the run, so an end junction is listed only when the run's own
    end piece is a column (T274_RUN_PIECES.csv);
  - the masonry beyond the end (T-516 storey masonry M) for the non-column ends;
  - for a column beyond an end: the structural column on ST7757 (S-COL.BON outline handle) after the T-274 translation
    of the architectural plan onto the structural sheet (column outlines matched, residual printed), and its T-119 ledger
    id / schedule mark (research/agents_t119/COLUMNS_TO_CONTROLLING_MEMBER.csv, nearest centre within 0.06 m).
Inputs (outside the repository, never committed): <scratch>/t125_inputs.pkl, <scratch>/t125_v2.json, <scratch>/t274_runs.json
(research/agents_t125 + research/agents_t274/t274_runs.py on Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip ->
P7757.dxf) and Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'. Output: research/agents_t526/out/END_CENSUS_V2_T526.csv
(ids, classes, gaps in mm, covers; no drawing coordinate) and out/ALIGN_T526.json.

    python3 -I research/agents_t526/t526_extract.py <scratch> <ST7757.dxf>
"""
import csv
import json
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import ezdxf
import numpy as np
from shapely.affinity import translate
from shapely.geometry import Polygon

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "research"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RES / "agents_t516"))
sys.path.insert(0, str(RES / "agents_t317"))
import end_census_v2 as E  # noqa: E402
import t516_extract as T516  # noqa: E402
import t317_alsenan as T317  # noqa: E402

OUT = HERE / "out" / "END_CENSUS_V2_T526.csv"
OUT_ALIGN = HERE / "out" / "ALIGN_T526.json"
JOINT = 0.010                   # owner session 2026-10-29: 10 mm mortar joint (ASSUMED - OWNER-APPROVED)
SHEETS = {"GF": (40500, 74500, 35500, 51000), "1F": (11500, 36000, 35500, 51000), "2F": (-27000, -2000, 35500, 51000)}


def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def st_columns(st_dxf):
    doc = ezdxf.readfile(st_dxf)
    out = {st: [] for st in SHEETS}
    for e in doc.modelspace().query('LWPOLYLINE[layer=="S-COL.BON"]'):
        p = [(x / 1000, y / 1000) for x, y, *_ in e.get_points()]
        if len(p) < 3:
            continue
        a = np.array(p)
        c = a.mean(0)
        for st, (x0, x1, y0, y1) in SHEETS.items():
            if x0 / 1000 <= c[0] <= x1 / 1000 and y0 / 1000 <= c[1] <= y1 / 1000 and (a.max(0) - a.min(0)).max() < 1.3:
                out[st].append((c, e.dxf.handle, Polygon(p).buffer(0)))
    return out


def align(acs, scs):
    """one translation arch -> structural sheet (T-274 t274_geom.py method): the shift matching most column centres."""
    sc = []
    for c, h, _P in scs:
        if all(np.linalg.norm(c - u) > 0.05 for u, _ in sc):
            sc.append((c, h))
    best = None
    for a in acs:
        for s, _ in sc:
            t = s - a
            n = sum(min(np.linalg.norm(x + t - y) for y, _ in sc) < 0.06 for x in acs)
            if best is None or n > best[0]:
                best = (n, t)
    t = best[1]
    pairs = [(x, min(sc, key=lambda y: np.linalg.norm(x + t - y[0]))) for x in acs]
    pairs = [(x, y) for x, y in pairs if np.linalg.norm(x + t - y[0]) < 0.06]
    t = np.mean([y[0] - x for x, y in pairs], 0)
    res = max(np.linalg.norm(x + t - y[0]) for x, y in pairs)
    return t, sc, len(pairs), float(res)


def main(scratch, st_dxf):
    S = Path(scratch)
    d = pickle.load(open(S / "t125_inputs.pkl", "rb"))
    v = json.load(open(S / "t125_v2.json"))
    runs = json.load(open(S / "t274_runs.json"))
    pieces = defaultdict(list)
    for x in rd(RES / "agents_t274/T274_RUN_PIECES.csv"):
        pieces[x["run_key"]].append(x)
    sharmat = defaultdict(set)
    for x in rd(RES / "agents_t355/SHARMAT_T355.csv"):
        rk, st = x["column_at"].rsplit("@", 1)
        sharmat[rk].add(round(float(st), 3))
    vj = defaultdict(set)
    for x in rd(RES / "agents_t317/JOINTS_T317.csv"):
        if x["dir"] == "V" and "@" in x["at"]:
            rk, st = x["at"].rsplit("@", 1)
            vj[rk].add(round(float(st), 3))
    wall_of = {}
    walls, _unknown, _t261, _gaps = T317.build()
    reg = {r["wall_id"]: r for r in rd(RES / "agents_t288/BLOCKWORK_WALL_REGISTER_V4.csv")}
    for r, rk, _w, _n, _s in walls:
        wall_of[rk] = r["wall_id"]
    t119 = defaultdict(list)
    for x in rd(RES / "agents_t119/COLUMNS_TO_CONTROLLING_MEMBER.csv"):
        t119[x["storey"]].append((np.array([float(x["x"]), float(x["y"])]), x["id"], x["mark"], x["drawn"]))
    stc = st_columns(st_dxf)
    rows, al, cache = [], {}, {}
    for rk in sorted(runs):
        R = runs[rk]
        fl = R["floor"]
        if R["segment"] is None:
            rows.append({"floor": fl, "run": rk, "wall_id": wall_of.get(rk, ""), "end": "", "class_v2": "NO_STRAIGHT_RUN",
                         "junction_v2": "", "held": "curved / bay run: no straight V1 band (T-274), not probed"})
            continue
        if fl not in cache:
            W, ax, M, cols, gaps, _r = T516.storey(d["floors"][fl], v["floors"][fl]["v2"])
            acs = [np.array(c.centroid.coords[0]) for c in cols]
            t, sc, n, res = align(acs, stc[fl])
            al[fl] = {"arch_columns": len(cols), "matched": n, "max_residual_m": round(res, 4)}
            # columns drawn ONLY on the structural sheet (no architectural outline within 0.06 m), in the arch frame
            sto = []
            for c, h, P in stc[fl]:
                if min(np.linalg.norm(c - (x + t)) for x in acs) > 0.06 and all(h2 != h for h2, _ in sto):
                    sto.append((h, translate(P, -t[0], -t[1])))
            al[fl]["structural_only_columns"] = [h for h, _ in sto]
            cache[fl] = (M, cols, acs, t, sc, sto)
        M, cols, acs, t, sc, sto = cache[fl]
        (a, b), L, th = R["segment"], R["seg_len"], float(R["t_m"])
        ps = pieces.get(rk, [])
        for end in (0, 1):
            inner = (ps[0] if end == 0 else ps[-1]) if ps else None
            res = E.classify_end(a, b, th, end, cols, JOINT, own_piece_is_column=bool(inner and inner["kind"] == "COLUMN"))
            if res.cls == "COLUMN_PIECE_IN_RUN":
                st = 0.0 if end == 0 else round(float(inner["from_m"]), 3)
            else:
                st = None
            # V1 listed? (the census keys a column by its piece station on this run)
            l355 = st is not None and st in sharmat.get(rk, set())
            l317 = st is not None and st in vj.get(rk, set())
            # masonry beyond the end (T-516 M), for the class the end has when no column is there
            dx, dy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            ux, uy = (-dx, -dy) if end == 0 else (dx, dy)
            e = a if end == 0 else b
            P = E._strip(e, (ux, uy), 0.0, E.PROBE, th / 2 - E.INSET)
            mm = P.intersection(M).area / P.area
            sid = hid = mark = drawn = ""
            depth = ""
            if res.column is not None and res.cls != "COLUMN_PIECE_IN_RUN":
                Z = E._strip(e, (ux, uy), res.gap_m, 1.5, th / 2 - E.INSET).intersection(cols[res.column])
                depth = f"{(max((x - e[0]) * ux + (y - e[1]) * uy for g in getattr(Z, 'geoms', [Z]) for x, y in g.exterior.coords) - res.gap_m) * 1000:.1f}"
            if res.column is not None:
                c = acs[res.column] + t
                h = min(sc, key=lambda y: np.linalg.norm(c - y[0]))
                if np.linalg.norm(c - h[0]) < 0.06:
                    hid = h[1]
                g = min(t119[fl], key=lambda y: np.linalg.norm(c - y[0]))
                if np.linalg.norm(c - g[0]) < 0.06:
                    sid, mark, drawn = g[1], g[2], g[3]
            # the same end against the structural-only outlines, and the run axis crossing one (no T-274 piece then)
            so = E.classify_end(a, b, th, end, [P for _, P in sto], JOINT)
            st_only = "" if so.cls == "NO_COLUMN" else f"{so.cls} {sto[so.column][0]}"
            if end == 1:
                band = E._strip(a, (dx, dy), 0.0, L, th / 2 - E.INSET)
                colr = [(float(x["from_m"]), float(x["to_m"])) for x in ps if x["kind"] == "COLUMN"]
                for h, P in sto:
                    Z = band.intersection(P)
                    if Z.is_empty or Z.area <= E.AREA_EPS:
                        continue
                    ss = [(x - a[0]) * dx + (y - a[1]) * dy for g in getattr(Z, "geoms", [Z]) for x, y in g.exterior.coords]
                    s0, s1 = min(ss), max(ss)
                    inside = any(c0 - 1e-6 <= s0 and s1 <= c1 + 1e-6 for c0, c1 in colr)
                    tag = ("INSIDE_ARCH_COLUMN_PIECE" if inside else "CROSSES_MASONRY") + f" {h} {s0:.3f}..{s1:.3f}"
                    st_only = (st_only + "; " if st_only else "") + tag
            v1_listed = l355 and l317
            rows.append({"floor": fl, "run": rk, "wall_id": wall_of.get(rk, ""),
                         "block_type": reg.get(wall_of.get(rk, ""), {}).get("block_type", ""),
                         "t_m": f"{th:.2f}", "end": end, "run_end_type": R["ends"][end],
                         "inner_piece": inner["kind"] if inner else "", "class_v2": res.cls,
                         "gap_mm": "" if res.gap_m is None else f"{res.gap_m * 1000:.1f}",
                         "cover": f"{res.cover:.4f}", "column_depth_mm": depth, "masonry_cover": f"{mm:.4f}",
                         "junction_v2": {True: "YES", False: "NO", None: "HELD"}[res.junction],
                         "listed_t355": "YES" if l355 else "NO", "listed_t317": "YES" if l317 else "NO",
                         "missed_by_v1": "YES" if res.junction and not v1_listed else ("HELD" if res.junction is None
                                                                                      else "NO"),
                         "arch_column": "" if res.column is None else f"{fl}-C{res.column:02d}",
                         "st_handle": hid, "structural_only": st_only, "t119_id": sid, "mark": mark, "drawn": drawn, "held": res.held})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    keys = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator="\n", restval="")
        w.writeheader()
        w.writerows(rows)
    json.dump(al, open(OUT_ALIGN, "w"), indent=1, sort_keys=True)
    print(json.dumps(al))
    for r in rows:
        if r.get("missed_by_v1") in ("YES", "HELD") or r["class_v2"] not in ("NO_COLUMN", "COLUMN_PIECE_IN_RUN"):
            print({k: r.get(k) for k in ("run", "wall_id", "end", "run_end_type", "inner_piece", "class_v2", "gap_mm",
                                         "cover", "listed_t355", "listed_t317", "missed_by_v1", "t119_id", "mark",
                                         "st_handle")})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
