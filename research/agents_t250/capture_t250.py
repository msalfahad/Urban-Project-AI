"""T-250 capture (research only, read-only on the drawing): the two geometric inputs of the face crosswalk, written to a
pickle OUTSIDE the repository (the drawing's coordinates never enter a tracked file).

  1. ROOM FACES: the T-128 r3 walk (research/agents_t128/scripts/walk_r2.py, merged a6ac2c66, unchanged) is executed
     as it is; its own `classify` call is wrapped so every 5 mm sample of every walked ring is kept with its class
     (WALL / COLUMN / WINDOW / DOOR / GAP / VIRTUAL), its position and its length. The walk's own result is
     re-checked against the committed walk_r3.json (contour and paintable metres of all 32 rooms) before anything is
     used: a walk that does not reproduce is refused.
  2. WALL RUNS: the T-125 capture of MASONRY_CENTRELINE_V2 inputs (alsenan_v2_dump.py pickle) is measured again with
     the engine module, and the span [s0, s1] of every split run (`<band>#k`) is recorded by wrapping the module's own
     `_sub_record` (read-only; the module is not changed).

Usage (project venv, Python 3.11):
    python -I research/agents_t250/capture_t250.py <P7757.dxf> <t125_inputs.pkl> --out <scratch>/t250_capture.pkl
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import pickle
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WALK = ROOT / "research/agents_t128/scripts/walk_r2.py"
ROOMS_PY = ROOT / "research/agents_t147/scripts/rooms.py"
WALK_R3 = ROOT / "research/agents_t128/walk_r3.json"
HOOK = "t1, r1 = classify(F, pp)"


def capture_rooms(dxf: str, scratch_json: str):
    src = WALK.read_text(encoding="utf-8")
    if src.count(HOOK) != 1:
        raise SystemExit("walk_r2.py changed: the classify call to wrap is not found exactly once (refused)")
    src = src.replace(HOOK, "t1, r1 = _T250_CAPTURE(rid, F, pp)")
    samples = {}
    polys = {}

    def cap(rid, F, pp):
        polys.setdefault(rid, []).append({"ext": [tuple(c) for c in pp.exterior.coords],
                                          "holes": [[tuple(c) for c in r.coords] for r in pp.interiors]})
        tot, runs = ns["classify"](F, pp)
        rec = samples.setdefault(rid, [])
        for ri, cls, ln, pr in runs:
            if not pr:
                continue
            seg = ln / len(pr)
            for p in pr:
                rec.append((cls, round(p.x, 6), round(p.y, 6), seg, ri))
        return tot, runs

    ns = {"__name__": "__main__", "_T250_CAPTURE": cap}
    old = sys.argv
    sys.argv = [str(WALK), str(ROOMS_PY), dxf, scratch_json]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(src, str(WALK), "exec"), ns)
    except SystemExit as e:
        if e.code not in (0, None):
            raise SystemExit(f"walk exited {e.code}: refused")
    finally:
        sys.argv = old
    got = json.load(open(scratch_json))["rooms"]
    ref = json.load(open(WALK_R3))["rooms"]
    bad = [k for k in ref if abs(got[k]["contour_m"] - ref[k]["contour_m"]) > 0.002
           or abs(got[k]["paintable_m"] - ref[k]["paintable_m"]) > 0.002]
    if bad or set(got) != set(ref):
        raise SystemExit(f"walk does not reproduce walk_r3.json on {bad}: refused")
    floors = {}
    for rid in samples:
        floors[rid] = rid.split("-")[0] if not rid.startswith("ST-") else rid.split("-")[1]
    return samples, floors, len(ref), polys


def sample_handles(dxf: str, samples):
    """the drawn entity (layer 1 wall, S-COL.BON column, W window; door blocks are closures, not entities) each walked
    sample lies on, within TOUCH_M: {room: [handle | None per sample]} in sample order. Handles are what the Checker
    opens on the Drive drawing; nothing else about the entity leaves the capture."""
    import ezdxf
    import numpy as np
    import shapely
    from shapely.geometry import LineString
    doc = ezdxf.readfile(dxf)
    geoms, hs = [], []
    for e in doc.modelspace():
        if e.dxftype() not in ("LINE", "LWPOLYLINE", "ARC", "POLYLINE"):
            continue
        if e.dxf.layer not in ("1", "S-COL.BON", "W"):
            continue
        for kind, L, pts, circ in _segments(e) if e.dxftype() != "POLYLINE" else []:
            if len(pts) > 1:
                geoms.append(LineString(pts))
                hs.append(e.dxf.handle)
    tree = shapely.STRtree(geoms)
    out = {}
    for room, v in samples.items():
        P = shapely.points(np.array([[q[1], q[2]] for q in v]))
        idx_in, idx_tree = tree.query_nearest(P, max_distance=TOUCH_M)
        hv = [None] * len(v)
        for i, j in zip(idx_in, idx_tree):
            if hv[i] is None:
                hv[i] = hs[j]
        out[room] = hv
    return out


def capture_runs(pkl: str):
    sys.path.insert(0, str(ROOT))
    from engine.source import masonry_centreline_v2 as V2
    d = pickle.load(open(pkl, "rb"))
    spans = []
    orig = V2._sub_record

    def sub(w, k, s0, s1, band, idx):
        r = orig(w, k, s0, s1, band, idx)
        spans.append({"run_id": r["wall_id"], "parent": w.get("wall_id"), "s0": s0, "s1": s1})
        return r

    V2._sub_record = sub
    out = {}
    try:
        for fl, f in d["floors"].items():
            spans.clear()
            r2 = V2.measure_floors({fl: f})[fl]
            u = f["unit_m"]
            bands = [{"band": w["wall_id"], "t_m": w["t_m"], "family": w["family"], "kind": w.get("kind"),
                      "sides": w.get("sides"), "a": tuple(c * u for c in w["centreline"][0]),
                      "b": tuple(c * u for c in w["centreline"][-1])} for w in f["walls"] if w.get("centreline")]
            out[fl] = {"bands": bands, "spans": list(spans),
                       "runs": [{k: r.get(k) for k in ("run_id", "members", "family", "t_m", "ends", "arch_run_lm",
                                                       "physical_blockwork_lm", "openings_in_run")}
                                for r in r2["runs"]],
                       "junctions": (r2.get("v1") or {}).get("junctions", []),
                       "columns": [[tuple(p) for p in q] for q in f["columns_m"]],
                       "stretches": r2.get("stretches", [])}
    finally:
        V2._sub_record = orig
    return out


T249 = ROOT / "research/agents_t249/OPENINGS_T249.csv"
TOUCH_M = 0.006          # a walked sample lies on a drawn line within 6 mm (walk step 5 mm, BUF grow-back exact)


def _segments(e):
    """(kind, length_m, points) pieces of one entity: ARC parts (bulge or ARC) and straight parts, metres."""
    from ezdxf import path as P
    t = e.dxftype()
    if t == "LINE":
        a, b = (e.dxf.start.x / 1000, e.dxf.start.y / 1000), (e.dxf.end.x / 1000, e.dxf.end.y / 1000)
        return [("LINE", math.dist(a, b), [a, b], None)]
    if t == "ARC":
        r = e.dxf.radius / 1000
        sw = math.radians((e.dxf.end_angle - e.dxf.start_angle) % 360)
        c = (e.dxf.center.x / 1000, e.dxf.center.y / 1000)
        return [("ARC", r * sw, [(q.x / 1000, q.y / 1000) for q in e.flattening(0.2)], (c, r))]
    if t == "LWPOLYLINE":
        pts = list(e.get_points())
        out = []
        n = len(pts) if e.closed else len(pts) - 1
        for i in range(n):
            x0, y0, _, _, bu = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)][:2]
            a, b = (x0 / 1000, y0 / 1000), (x1 / 1000, y1 / 1000)
            ch = math.dist(a, b)
            if abs(bu) > 1e-9 and ch > 0:
                th = 4 * math.atan(abs(bu))
                r = ch / (2 * math.sin(th / 2))
                # centre and polyline of the arc
                mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                h = r * math.cos(th / 2) * (1 if bu > 0 else -1)
                ux, uy = (b[0] - a[0]) / ch, (b[1] - a[1]) / ch
                cx, cy = mx - uy * h, my + ux * h
                a0 = math.atan2(a[1] - cy, a[0] - cx)
                sgn = 1 if bu > 0 else -1
                poly = [(cx + r * math.cos(a0 + sgn * th * k / 400), cy + r * math.sin(a0 + sgn * th * k / 400))
                        for k in range(401)]
                out.append(("ARC", r * th, poly, ((cx, cy), r)))
            elif ch > 0:
                out.append(("LINE", ch, [a, b], None))
        return out
    return []


def capture_openings(dxf: str, samples, runs, room_floor):
    """per T-249 opening with plan handles: every piece of its glazing entities (arc / line, length) and the walked
    room metres lying on each piece; for curved ones also every ARC concentric with the glass (band faces) and the
    metres the rooms touch on it."""
    import csv
    import ezdxf
    from shapely.geometry import LineString, Point
    doc = ezdxf.readfile(dxf)
    import numpy as np
    import shapely
    arr = {r: (np.array([q[1] for q in v]), np.array([q[2] for q in v]), np.array([q[3] for q in v]))
           for r, v in samples.items()}

    def touch(line):
        out = {}
        env = line.buffer(TOUCH_M)
        for r, (xs, ys, ss) in arr.items():
            m = float(ss[shapely.contains_xy(env, xs, ys)].sum())
            if m > 0:
                out[r] = m
        return out

    rows = list(csv.DictReader(open(T249, encoding="utf-8")))
    res = {}
    arcs = [e for e in doc.modelspace().query("ARC")]
    wall1 = []
    for e in doc.modelspace().query('LINE LWPOLYLINE ARC[layer=="1"]'):
        for kind, L, pts, circ in _segments(e):
            if len(pts) > 1:
                wall1.append((LineString(pts), e.dxf.handle))
    for r in rows:
        hs = (r["HANDLES"] or "").split()
        if not hs or r["KIND"] != "WINDOW":
            continue
        pieces = []
        for h in hs:
            e = doc.entitydb.get(h)
            if e is None:
                raise SystemExit(f"{r['ID']}: handle {h} not in the drawing (wrong file?): refused")
            for k, (kind, L, pts, circ) in enumerate(_segments(e)):
                pieces.append({"handle": h, "layer": e.dxf.layer, "piece": k, "kind": kind, "len_m": L,
                               "radius_m": circ[1] if circ else None, "centre": circ[0] if circ else None,
                               "touch": touch(LineString(pts))})
        rec = {"id": r["ID"], "floor": r["FLOOR"], "pieces": pieces, "concentric": []}
        # metres of each ARC piece lying inside a straight wall band of its floor (a partition stopping on the glass)
        sys.path.insert(0, str(HERE))
        import face_crosswalk as X
        bands = X.prepare([b for b in runs[r["FLOOR"]]["bands"] if b["kind"] in ("INTERNAL", "EXTERNAL")
                           and "|" not in b["band"]])
        for h in hs:
            e = doc.entitydb.get(h)
            for k, (kind, L, pts, circ) in enumerate(_segments(e)):
                if kind != "ARC":
                    continue
                ib = {}
                for i in range(len(pts) - 1):
                    mid = ((pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2)
                    seg = math.dist(pts[i], pts[i + 1]) * L / LineString(pts).length
                    for b in bands:
                        if X.in_band(mid, b):
                            ib[b["band"]] = ib.get(b["band"], 0.0) + seg
                            break
                # untouched part of the arc: sub-segments with no walked sample of any room within TOUCH_M, and the
                # wall-layer (1) entities lying on that part (what stops on the glass there)
                fl_rooms = [rr for rr in arr if room_floor[rr] == r["FLOOR"]]
                AX = np.concatenate([arr[rr][0] for rr in fl_rooms])
                AY = np.concatenate([arr[rr][1] for rr in fl_rooms])
                un, near = 0.0, set()
                for i in range(len(pts) - 1):
                    mid = ((pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2)
                    seg = math.dist(pts[i], pts[i + 1]) * L / LineString(pts).length
                    if float(np.min((AX - mid[0]) ** 2 + (AY - mid[1]) ** 2)) > TOUCH_M ** 2:
                        un += seg
                        for g, ge in wall1:
                            if g.distance(Point(mid)) < 0.01:
                                near.add(ge)
                for p in pieces:
                    if p["handle"] == h and p["piece"] == k:
                        p["in_bands"] = ib
                        p["untouched_m"] = un
                        p["untouched_on_layer1"] = sorted(near)
        cs = [p for p in pieces if p["kind"] == "ARC"]
        if cs:
            c0 = cs[0]["centre"]
            rr = [p["radius_m"] for p in cs]
            for e in arcs:
                c = (e.dxf.center.x / 1000, e.dxf.center.y / 1000)
                rad = e.dxf.radius / 1000
                if math.dist(c, c0) < 0.05 and min(rr) - 0.30 <= rad <= max(rr) + 0.30:
                    kind, L, pts, circ = _segments(e)[0]
                    rec["concentric"].append({"handle": e.dxf.handle, "layer": e.dxf.layer, "len_m": L,
                                              "radius_m": rad, "touch": touch(LineString(pts))})
            for p in pieces:
                p["centre"] = None          # no coordinates leave the capture as data
        res[r["ID"]] = rec
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("t125_pkl")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if Path(a.out).resolve().is_relative_to(ROOT):
        raise SystemExit("--out must be outside the repository")
    samples, floors, n, polys = capture_rooms(a.dxf, str(Path(a.out).with_suffix(".walk.json")))
    runs = capture_runs(a.t125_pkl)
    openings = capture_openings(a.dxf, samples, runs, floors)
    handles = sample_handles(a.dxf, samples)
    pickle.dump({"samples": samples, "room_floor": floors, "runs": runs, "openings": openings, "handles": handles,
                 "polys": polys},
                open(a.out, "wb"))
    print(f"rooms {len(samples)} (walk reproduces walk_r3.json on {n} / {n}); floors", {fl: len(v['bands']) for fl, v in runs.items()})


if __name__ == "__main__":
    main()
