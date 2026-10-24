"""T-262 capture (research only, read-only on the drawing): the two geometric inputs of the opening-to-room join,
written to a pickle OUTSIDE the repository (the drawing's coordinates never enter a tracked file).

  1. ROOM REGIONS: the merged T-128 r3 walk (research/agents_t128/scripts/walk_r2.py, a6ac2c66, unchanged) is executed
     as it is; its own `classify` call is wrapped only to keep each walked polygon (exterior + holes) per room. The
     walk's result is re-checked against the committed walk_r3.json (contour and paintable metres of all 32 rooms)
     before anything is used: a walk that does not reproduce is refused.
  2. OPENINGS: every row of the merged engine-independent inventory (research/agents_t249/OPENINGS_T249.csv,
     2a2d15af) is looked up on the drawing BY ITS HANDLES (never by a name, never by an engine id) and turned into
     probe stations (point on the opening line + its unit normal):
       - door / gate (door block or loose swing arc): the hinge (arc centre) to the closed-leaf point (the arc end the
         drawn open leaf does not touch; with no leaf drawn, the arc end nearest a layer-1 wall line); stations every
         5 cm along that line; side A = the swing side (towards the arc's mid point), side B = the other side;
       - window: the longest drawn glazing entity of the symbol, flattened; stations every 5 cm along it with the
         local normal (so a curved glazing band is probed square to its own arc);
       - leafless arch (arch block): the block's drawn geometry, minimum rotated rectangle, long axis = opening line.
  3. WALL STRIPS: pairs of parallel layer-1 LINEs 0.08 .. 0.32 m apart that overlap along their length by > 0.20 m
     (the two faces of one wall); the quadrilateral between them is the strip, kept with both handles.

Usage (project venv, Python 3.11):
    python -I research/agents_t262/capture_t262.py <P7757.dxf> --out <scratch>/t262_capture.pkl
"""
from __future__ import annotations

import argparse
import contextlib
import csv
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
INVENTORY = ROOT / "research/agents_t249/OPENINGS_T249.csv"
HOOK = "t1, r1 = classify(F, pp)"
LEAF_ARC_MIN_M = 0.40          # a door swing (rooms.py uses the same 400 mm floor)
STRIP_T = (0.08, 0.32)         # wall thickness band for a face pair (Alsenan 0.10 .. 0.30 incl. finishes)
STRIP_MIN_OVERLAP_M = 0.20
PLAN_BOXES = []                # the walk's own storey boxes (walk_r2.BOXES), filled by capture_rooms


def capture_rooms(dxf: str, scratch_json: str):
    src = WALK.read_text(encoding="utf-8")
    if src.count(HOOK) != 1:
        raise SystemExit("walk_r2.py changed: the classify call to wrap is not found exactly once (refused)")
    src = src.replace(HOOK, "t1, r1 = _T262_CAPTURE(rid, F, pp)")
    polys = {}

    def cap(rid, F, pp):
        polys.setdefault(rid, []).append({"ext": [tuple(c) for c in pp.exterior.coords],
                                          "holes": [[tuple(c) for c in r.coords] for r in pp.interiors]})
        return ns["classify"](F, pp)

    ns = {"__name__": "__main__", "_T262_CAPTURE": cap}
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
    PLAN_BOXES[:] = list(ns["BOXES"].values())
    floor = {rid: (rid.split("-")[1] if rid.startswith("ST-") else rid.split("-")[0]) for rid in polys}
    return polys, floor, {k: got[k]["walked_area_m2"] for k in got}


def _flat(e):
    from ezdxf import path as zpath
    try:
        p = zpath.make_path(e)
    except Exception:
        return []
    return [(q.x / 1000.0, q.y / 1000.0) for q in p.flattening(2)]


STATION_SPACING_M = 0.05      # one probe station per 5 cm of opening line (at least 3), at the middle of each piece


def _stations_along(pts, fracs=None):
    """points at the given fractions of a polyline's length (default: one per STATION_SPACING_M, centred in its
    piece), each with its unit normal (left of travel)."""
    seg = [(pts[i], pts[i + 1], math.dist(pts[i], pts[i + 1])) for i in range(len(pts) - 1)]
    seg = [s for s in seg if s[2] > 1e-9]
    L = sum(s[2] for s in seg)
    if fracs is None:
        n = max(3, int(math.ceil(L / STATION_SPACING_M)))
        fracs = [(k + 0.5) / n for k in range(n)]
    out = []
    for f in fracs:
        t, acc = f * L, 0.0
        for a, b, ln in seg:
            if acc + ln >= t:
                u = ((b[0] - a[0]) / ln, (b[1] - a[1]) / ln)
                k = (t - acc) / ln
                out.append({"p": (a[0] + u[0] * k * ln, a[1] + u[1] * k * ln), "n": (-u[1], u[0])})
                break
            acc += ln
    return out, L


def door_geometry(doc, handle, wall_lines):
    from shapely.geometry import LineString, Point
    e = doc.entitydb[handle]
    if e.dxftype() == "INSERT":
        ves = list(e.virtual_entities())
    else:
        ves = [e]
    arcs = [v for v in ves if v.dxftype() == "ARC" and v.dxf.radius / 1000.0 > LEAF_ARC_MIN_M]
    if not arcs:
        raise ValueError(f"{handle}: no swing arc")
    a = max(arcs, key=lambda v: v.dxf.radius)
    c3 = a.ocs().to_wcs(a.dxf.center)
    c = (c3.x / 1000.0, c3.y / 1000.0)
    r = a.dxf.radius / 1000.0
    v = _flat(a)
    ends = [v[0], v[-1]]
    mid = v[len(v) // 2]
    leaves = [LineString(_flat(x)) for x in ves if x.dxftype() in ("LINE", "LWPOLYLINE") and len(_flat(x)) >= 2]
    if e.dxftype() == "ARC":                                  # loose swing: leaf lines on the arc's own layer nearby
        for x in doc.modelspace().query(f'LINE LWPOLYLINE[layer=="{e.dxf.layer}"]'):
            q = _flat(x)
            if len(q) >= 2 and LineString(q).distance(Point(c)) < 0.05:
                leaves.append(LineString(q))
    touched = lambda p: min((ln.distance(Point(p)) for ln in leaves), default=9.0)
    tq = sorted(ends, key=touched)
    if touched(tq[0]) < 0.02 and touched(tq[1]) >= 0.02:
        closed, basis = tq[1], "the arc end the drawn open leaf does not touch"
    else:
        closed = min(ends, key=lambda p: min(w.distance(Point(p)) for w in wall_lines))
        basis = "no single open leaf drawn: the arc end nearest a layer-1 wall line"
    st, L = _stations_along([c, closed])
    # orient every normal to the swing side (towards the arc mid point) -> side A = swing side
    for s in st:
        if (mid[0] - s["p"][0]) * s["n"][0] + (mid[1] - s["p"][1]) * s["n"][1] < 0:
            s["n"] = (-s["n"][0], -s["n"][1])
    return {"stations": st, "line_m": round(L, 4), "leaf_r_m": round(r, 4), "basis": basis,
            "side_a_is": "swing side"}


def window_geometry(doc, handles):
    ents = [doc.entitydb[h] for h in handles]
    flats = [(h, _flat(x)) for h, x in zip(handles, ents)]
    flats = [(h, f) for h, f in flats if len(f) >= 2]
    length = lambda f: sum(math.dist(f[i], f[i + 1]) for i in range(len(f) - 1))
    h, f = max(flats, key=lambda hf: length(hf[1]))
    st, L = _stations_along(f)
    chord = math.dist(f[0], f[-1])
    return {"stations": st, "line_m": round(L, 4), "probe_entity": h, "curved": (L - chord) > 0.02,
            "basis": "longest glazing entity of the symbol, probed square to itself", "side_a_is": "left of the entity"}


def arch_geometry(doc, handle):
    from shapely.geometry import MultiPoint
    e = doc.entitydb[handle]
    pts = [p for x in e.virtual_entities() for p in _flat(x)]
    mrr = MultiPoint(pts).minimum_rotated_rectangle
    c = list(mrr.exterior.coords)
    e1, e2 = math.dist(c[0], c[1]), math.dist(c[1], c[2])
    a, b = (c[0], c[1]) if e1 >= e2 else (c[1], c[2])
    k = (c[2][0] - c[1][0], c[2][1] - c[1][1]) if e1 >= e2 else (c[0][0] - c[1][0], c[0][1] - c[1][1])
    # the long axis through the middle of the short side
    off = (k[0] / 2.0, k[1] / 2.0)
    line = [(a[0] + off[0], a[1] + off[1]), (b[0] + off[0], b[1] + off[1])]
    st, L = _stations_along(line)
    return {"stations": st, "line_m": round(L, 4), "basis": "arch block outline, long axis of its minimum rectangle",
            "side_a_is": "left of the long axis"}


def wall_strips(doc):
    """pairs of parallel layer-1 LINEs 0.08 .. 0.32 m apart overlapping > 0.20 m along their length."""
    lines = []
    for e in doc.modelspace().query('LINE[layer=="1"]'):
        a = (e.dxf.start.x / 1000.0, e.dxf.start.y / 1000.0)
        b = (e.dxf.end.x / 1000.0, e.dxf.end.y / 1000.0)
        m = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        if math.dist(a, b) > 0.2 and any(x0 <= m[0] <= x1 and y0 <= m[1] <= y1 for x0, x1, y0, y1 in PLAN_BOXES):
            lines.append((e.dxf.handle, a, b))
    out = []
    for i, (h1, a1, b1) in enumerate(lines):
        L1 = math.dist(a1, b1)
        u = ((b1[0] - a1[0]) / L1, (b1[1] - a1[1]) / L1)
        n = (-u[1], u[0])
        for h2, a2, b2 in lines[i + 1:]:
            L2 = math.dist(a2, b2)
            v = ((b2[0] - a2[0]) / L2, (b2[1] - a2[1]) / L2)
            if abs(u[0] * v[1] - u[1] * v[0]) > 0.005:
                continue
            d = (a2[0] - a1[0]) * n[0] + (a2[1] - a1[1]) * n[1]
            if not (STRIP_T[0] <= abs(d) <= STRIP_T[1]):
                continue
            t2 = sorted(((p[0] - a1[0]) * u[0] + (p[1] - a1[1]) * u[1]) for p in (a2, b2))
            lo, hi = max(0.0, t2[0]), min(L1, t2[1])
            if hi - lo <= STRIP_MIN_OVERLAP_M:
                continue
            P = lambda t, s: (a1[0] + u[0] * t + n[0] * s, a1[1] + u[1] * t + n[1] * s)
            out.append({"handles": (h1, h2), "t_m": round(abs(d), 4), "overlap_m": round(hi - lo, 4),
                        "quad": [P(lo, 0), P(hi, 0), P(hi, d), P(lo, d)]})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    import ezdxf
    out = Path(a.out)
    polys, floor, areas = capture_rooms(a.dxf, str(out.with_suffix(".walk.json")))
    doc = ezdxf.readfile(a.dxf)
    from shapely.geometry import LineString
    wall_lines = [LineString(_flat(e)) for e in doc.modelspace().query('LINE[layer=="1"]') if len(_flat(e)) >= 2]
    ops = []
    for r in csv.DictReader(open(INVENTORY, encoding="utf-8")):
        hs = r["HANDLES"].split()
        if r["KIND"] in ("DOOR", "GATE"):
            g = door_geometry(doc, hs[0], wall_lines)
        elif r["KIND"] == "WINDOW":
            g = window_geometry(doc, hs)
        else:
            g = arch_geometry(doc, hs[0])
        g.update(id=r["ID"], kind=r["KIND"], floor=r["FLOOR"], handles=hs)
        ops.append(g)
    strips = wall_strips(doc)
    pickle.dump({"rooms": polys, "room_floor": floor, "walked_area_m2": areas, "openings": ops, "strips": strips},
                open(out, "wb"))
    print(f"T-262 capture: {len(polys)} rooms (walk reproduces walk_r3.json), {len(ops)} openings, "
          f"{len(strips)} wall strips -> {out}")


if __name__ == "__main__":
    main()
