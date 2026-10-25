"""T-274 hand-reading helper (research only, NOT engine code): what is drawn over every metre of every wall band.

Exact version of the T-143 2 cm sampler (research/agents_t143/scripts/heights.py), written because that sampler is the
root cause of the non-closing height pieces (Checker T-180 slot 15:59 / 16:04): it sampled every 0.02 m of the BAND (not
of the census run), counted a sample as 'under a beam' within 3 cm OUTSIDE the band edge (TOL 0.03 widens every beam
crossing by up to 0.06 m), and the register then spread a weighted mean of those pieces over the census length.

Here every census RUN segment (MASONRY_CENTRELINE_V2 end points after L extensions, t274_runs.py) is cut EXACTLY at every boundary of
  - a column outline of the architectural plan (the census never includes a column),
  - a beam band of the route G overlay (T-110 member register: mark, b x h), no tolerance,
  - a face of the structural roof-slab plan (T-139 slab_faces: slab panel, opening, stair, ...),
after one translation per storey from the architectural frame to the structural sheet frame (column outlines matched,
as T-143 align.py, residual printed). Between two consecutive cut points the midpoint decides what is above: the
deepest beam band containing it (block stops under the lowest underside), else the slab face containing it, else
NOTHING DRAWN. Output (scratch only, outside the repository): per band, the ordered pieces with their station along
the band (from, to, m), the member and its depth.

Usage: python3 -I t274_geom.py <scratch> <st.dxf>
  <scratch> holds t125_inputs.pkl (T-125), t274_runs.json (t274_runs.py), bands.json (T-110 bands.py on the committed route G
  overlays), faces.json (T-139 slab_faces.py); writes <scratch>/t274_pieces.json and <scratch>/t274_align.json."""
import csv
import json
import math
import pickle
import sys
from pathlib import Path

import ezdxf
import numpy as np
from shapely import wkt as W
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
S = Path(sys.argv[1])
ST_DXF = sys.argv[2]
SHEETS = {"GF": (40500, 74500, 35500, 51000), "1F": (11500, 36000, 35500, 51000), "2F": (-27000, -2000, 35500, 51000)}

ins = pickle.load(open(S / "t125_inputs.pkl", "rb"))
runs = json.load(open(S / "t274_runs.json"))
bands = json.load(open(S / "bands.json"))
faces = json.load(open(S / "faces.json"))
panels = {r["id"]: r for r in csv.DictReader(open(ROOT / "research/agents_t139/PANELS.csv"))}
reg = list(csv.DictReader(open(ROOT / "research/agents_t110/BEAM_MEMBER_REGISTER.csv")))

REG = {}
for r in reg:
    c = r["component"].split(":")
    if c[0] == "BEAMS":
        k = c[2]
        if "+" in k:
            base = k.split(".")[0]
            for s in (".1", ".2"):
                REG[f"{base}{s}@{c[1]}"] = r
        else:
            REG[f"{k}@{c[1]}"] = r
    elif c[0] == "RING" and "BAND0033-0036" in c[2]:
        for n in range(33, 37):
            REG[f"BAND{n:04d}@{c[1]}"] = r

# structural column outlines per sheet
doc = ezdxf.readfile(ST_DXF)
stcols = {st: [] for st in SHEETS}
for e in doc.modelspace().query('LWPOLYLINE[layer=="S-COL.BON"]'):
    p = [(x / 1000, y / 1000) for x, y, *_ in e.get_points()]
    if len(p) < 3:
        continue
    a = np.array(p)
    c = a.mean(0)
    for st, (x0, x1, y0, y1) in SHEETS.items():
        if x0 / 1000 <= c[0] <= x1 / 1000 and y0 / 1000 <= c[1] <= y1 / 1000 and (a.max(0) - a.min(0)).max() < 1.3:
            stcols[st].append((c, Polygon(p).buffer(0), e.dxf.handle))

align = {}
for st in SHEETS:
    f = ins["floors"][st]
    ac = [np.array(q).mean(0) for q in f["columns_m"] if len(q) >= 3]
    sc = []
    for c, _P, _h in stcols[st]:
        if all(np.linalg.norm(c - u) > 0.05 for u in sc):
            sc.append(c)
    best = None
    for a in ac:
        for s in sc:
            t = s - a
            n = sum(min(np.linalg.norm(x + t - y) for y in sc) < 0.06 for x in ac)
            if best is None or n > best[0]:
                best = (n, t)
    t = best[1]
    pairs = [(x, min(sc, key=lambda y: np.linalg.norm(x + t - y))) for x in ac]
    pairs = [(x, y) for x, y in pairs if np.linalg.norm(x + t - y) < 0.06]
    t = np.mean([y - x for x, y in pairs], 0)
    res = max(np.linalg.norm(x + t - y) for x, y in pairs)
    align[st] = dict(shift=t.tolist(), matched=len(pairs), arch_cols=len(ac), struct_cols=len(sc), resid=float(res))
    print(st, "columns matched", len(pairs), "/", len(ac), "max residual m", round(res, 4))
json.dump(align, open(S / "t274_align.json", "w"), indent=1)


def depth_of(r):
    try:
        return float(r["depth_m"])
    except Exception:
        return None


out = {}
for st in SHEETS:
    f = ins["floors"][st]
    u = f["unit_m"]
    sh = np.array(align[st]["shift"])
    acols = [Polygon([(x + sh[0], y + sh[1]) for x, y in q]).buffer(0) for q in f["columns_m"] if len(q) >= 3]
    BP = []
    for k, v in bands.items():
        if k.endswith("@" + st):
            BP.append((k, v["title"], Polygon(v["pts"]).buffer(0)))
    FP = [(fc["id"], W.loads(fc["wkt"])) for fc in faces[st]]
    FPD = dict(FP)
    geoms = [P for _k, _t, P in BP] + [P for _i, P in FP] + acols
    for rk, rv in runs.items():
        if rv["floor"] != st or rv["segment"] is None:
            continue
        c = [(x + sh[0], y + sh[1]) for x, y in rv["segment"]]
        line = LineString(c)
        L = line.length
        cuts = {0.0, L}
        for G in geoms:
            if not G.intersects(line):
                continue
            x = G.boundary.intersection(line)
            for g in getattr(x, "geoms", [x]):
                if g.is_empty:
                    continue
                for p in (g.coords if g.geom_type in ("Point", "LineString") else []):
                    cuts.add(round(line.project(Point(p)), 6))
        cuts = sorted(cuts)
        pieces = []
        for a, b in zip(cuts, cuts[1:]):
            if b - a < 1e-6:
                continue
            m = line.interpolate((a + b) / 2)
            if any(P.contains(m) for P in acols):
                key = {"kind": "COLUMN"}
            else:
                hits = [(k, t, REG.get(k)) for k, t, P in BP if P.contains(m)]
                via = None
                fid = None
                if not hits:
                    fid = next((i for i, P in FP if P.contains(m)), None)
                    pr = panels.get(fid) or {}
                    if fid is not None and pr.get("cls") == "BEAM_OR_COLUMN":
                        # a drawn beam / junction face the route G band polygon does not reach (band ends cut at a
                        # column face, junction corners): the member is the band whose polygon shares area with
                        # this drawn face; a structural column outline over the wall is named, never a beam
                        Fp = FPD[fid]
                        if any(P.contains(m) for _c, P, _h in stcols[st]):
                            hits = []
                            via = "ST_COLUMN"
                        else:
                            near = [(P.distance(m), k, t) for k, t, P in BP if P.intersection(Fp).area > 1e-6]
                            # a merged junction face (band + column, or two bands) belongs, at this point, to the
                            # band nearest to it (within 1 mm of the nearest), never to every band touching the face
                            dmin = min((d for d, _k, _t in near), default=None)
                            hits = [(k, t, REG.get(k)) for d, k, t in near if d <= dmin + 0.001]
                            via = "FACE " + fid if hits else None
                if via == "ST_COLUMN":
                    key = {"kind": "ST_COLUMN", "face": fid}
                elif hits:
                    known = [h for h in hits if h[2] and depth_of(h[2]) is not None]
                    if len(known) < len(hits):          # an unregistered / undepthed band over the wall: HELD by name
                        h = [h for h in hits if not (h[2] and depth_of(h[2]) is not None)][0]
                        key = {"kind": "BEAM", "band": h[0], "member": h[2]["member_id"] if h[2] else "NO_REGISTER_ROW",
                               "mark": h[2]["mark"] if h[2] else h[1], "depth_m": None,
                               "status": h[2]["status"] if h[2] else "UNKNOWN"}
                    else:
                        h = max(known, key=lambda z: depth_of(z[2]))
                        key = {"kind": "BEAM", "band": h[0], "member": h[2]["member_id"], "mark": h[2]["mark"],
                               "depth_m": depth_of(h[2]), "status": h[2]["status"]}
                    if len(hits) > 1:
                        key["junction"] = sorted(z[0] for z in hits)
                    if via:
                        key["via"] = via
                else:
                    if fid is None:
                        fid = next((i for i, P in FP if P.contains(m)), None)
                    if fid is None:
                        key = {"kind": "NONE"}
                    else:
                        pr = panels.get(fid) or {}
                        key = {"kind": "FACE", "face": fid, "cls": pr.get("cls", "?"), "t": pr.get("t", "")}
            if pieces and pieces[-1]["key"] == key and abs(pieces[-1]["to"] - a) < 1e-6:
                pieces[-1]["to"] = b
            else:
                pieces.append({"from": a, "to": b, "key": key})
        for p in pieces:
            p["len"] = round(p["to"] - p["from"], 6)
            p["from"], p["to"] = round(p["from"], 6), round(p["to"], 6)
        out[rk] = {"floor": st, "run_id": rv["run_id"], "t_m": rv["t_m"], "ends": rv["ends"], "ext": rv["ext"],
                   "arch_run_lm": rv["arch_run_lm"], "segment_len_m": round(L, 6), "pieces": pieces}
json.dump(out, open(S / "t274_pieces.json", "w"), indent=1)
print(len(out), "runs")
