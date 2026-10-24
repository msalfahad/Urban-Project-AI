"""T-272 r2 extraction: drawn clear spans of every ground-beam run between supporting faces, INCLUDING the faces of
crossing / tee ground beams, and the drawn inner / outer face arcs of the curved ring split at its columns.
Values, ids and DXF handles only; no coordinates are written.

    .work/venv/bin/python -I research/agents_t272/t272_r2_extract.py <"ST7757 dxf.dxf" decoded> [--out <dir>]

Input: Drive "Alsenan chalet project" / "ST7757 dxf.dxf" (sha 9f9d1179, the same file T-141 / T-230 / T-242 read).
Bands, columns, footings and spans exactly as T-242 (T-141 runner, GROUND_SYSTEM_SPANS_V2). For each span the
footprint of every other ground band that the V2 splitter listed as 'CROSSING_OR_TEE (no split)' is taken from the
same engine function (_junction_interval: the interval along the run covered by the other band's strip), so a link of
this run (a section perpendicular to its axis across its full width) is clear of the other beam only outside that
interval (Checker 2026-10-24 17:04: no link continues through a crossing ground beam unless a print shows it).
Relation per tee: THROUGH (the other strip covers this band's whole width) or STOPS_AT_FACE (only a sliver within the
contact tolerance: the other beam ends on this beam's near face).

Ring ARC:157+158: the two drawn arcs (inner r 2.25 / outer r 2.55 m); each arc's drawn range minus the angular
ranges covered by the S-COL.BON column outlines that touch it, giving the drawn face pieces per arc.
Writes CLEAR_SPANS_T272R2.json next to this file (or --out).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
spec = importlib.util.spec_from_file_location("r141", os.path.join(ROOT, "research/agents_t141/run_t141_alsenan.py"))
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)
V2 = R.V2

RUNS = ["107+7CE#1", "109+7CB#2", "109+7CB#3", "10A+7C9#1", "114+115+7DF#2", "145+7CA#1", "170+7C3#1",
        "170+7C3#2", "170+7C3#3", "170+7C3#4", "7D0+FC#1", "7D0+FC#2", "7D0+FC#3", "7D0+FC#4", "7E0+FD#1",
        "7E0+FD#2"]                     # the 16 straight T-265 exterior runs (the 17th is the ring)


def r4(v):
    return round(float(v), 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("structural")
    ap.add_argument("--out", default=HERE)
    a = ap.parse_args()
    import ezdxf
    from shapely.geometry import Polygon

    if R.sha(a.structural) != R.DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    doc = ezdxf.readfile(a.structural)
    msp = doc.modelspace()
    GBP, FP = R.GBP, R.FP
    shift = FP[0] - GBP[0]
    faces = [{"handle": e.dxf.handle, "layer": e.dxf.layer, "p0": tuple(e.dxf.start)[:2], "p1": tuple(e.dxf.end)[:2]}
             for e in msp.query("LINE[layer=='1']") if R.inb(*tuple(e.dxf.start)[:2], GBP)]
    res = R.GN.pair_straight(faces, width=300.0, tol=12.0, admitted_layers={"1"})
    bands = [{"band_id": "+".join(b["handles"]), "u": b["u"], "lo_off": b["lo_off"], "hi_off": b["hi_off"],
              "t0": b["t0"], "t1": b["t1"], "handles": b["handles"]} for b in res["bands"]]
    arcs = {e.dxf.handle: e for e in msp.query("ARC[layer=='1']") if R.inb(e.dxf.center[0], e.dxf.center[1], GBP)}
    arc_in = [{"handle": h, "layer": "1", "cx": e.dxf.center[0], "cy": e.dxf.center[1], "r": e.dxf.radius,
               "a0": e.dxf.start_angle, "a1": e.dxf.end_angle} for h, e in arcs.items()]
    ares = R.GN.pair_arcs(arc_in, width=300.0, tol=12.0, admitted_layers={"1"})
    for k, ab in enumerate(ares["bands"], start=1):
        bands.append({"band_id": f"ARC:{'+'.join(ab['handles'])}/{k}", "u": (1.0, 0.0), "lo_off": 0, "hi_off": 1,
                      "t0": 0, "t1": 1, "handles": ab["handles"], "kind": "ARC",
                      "polygon": [tuple(p) for p in ab["polygon"]]})
    cols = R.outlines(msp, "S-COL.BON", GBP)
    feet_fp = R.outlines(msp, "S-FOOTINGS", FP, blocks=("F",))
    feet_gb = [(i, [(x - shift, y) for x, y in p], h) for i, p, h in feet_fp]
    supports = [{"support_id": "COL:" + i, "kind": "COLUMN", "polygon": p, "handles": h} for i, p, h in cols] + \
               [{"support_id": "FTG:" + i, "kind": "FOOTING", "polygon": p, "handles": h} for i, p, h in feet_gb]
    out = V2.split_ground_beams(bands, supports, units="mm", classes=R.CLASSES)
    tol = V2.TOL_M * 1000.0
    BB = {b["band_id"]: V2._band(b) for b in bands if b.get("kind") != "ARC"}

    spans = {}
    for sp in out["spans"]:
        if sp["span_id"] not in RUNS:
            continue
        b = BB[sp["band_id"]]
        ta = sp["start"]["face_station_m"] * 1000.0
        tb = sp["end"]["face_station_m"] * 1000.0
        width = b["hi"] - b["lo"]
        tees = []
        for t in sp["intermediate"]:
            o = BB[t["band_id"]]
            iv = V2._junction_interval(b, o, tol)
            if not iv or not (ta < (iv[0] + iv[1]) / 2 < tb):
                continue
            g = V2._clip_strip(V2._rect(b), o["u"], o["n"], o["t0"] - tol, o["t1"] + tol, o["lo"], o["hi"])
            ns = [V2._dot(p, b["n"]) for p in g]
            depth = max(ns) - min(ns)
            sin = abs(b["u"][0] * o["u"][1] - b["u"][1] * o["u"][0])
            # the paired band of an oblique beam is cut square at the shorter face line; its drawn face lines may
            # run on to this beam's face (or to a neighbouring tee's face): every face-line end within the oblique
            # reach (width / sin) of this band's strip widens the footprint to the drawn ends
            lo_t, hi_t, ends_used = iv[0], iv[1], []
            reach = (o["hi"] - o["lo"]) / max(sin, 1e-9)
            strip_b = Polygon(V2._rect(b))
            for h in o["handles"]:
                e = doc.entitydb.get(h)
                if e is None or e.dxftype() != "LINE":
                    continue
                for p in (tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]):
                    from shapely.geometry import Point as _P
                    dist = strip_b.distance(_P(p))
                    if dist <= reach + tol:
                        tp = V2._dot(p, b["u"])
                        if tp < lo_t or tp > hi_t:
                            ends_used.append({"handle": h, "off_face_m": r4(dist / 1000.0),
                                              "at_m": r4((tp - ta) / 1000.0)})
                        lo_t, hi_t = min(lo_t, tp), max(hi_t, tp)
            iv = (lo_t, hi_t)
            tees.append({"band_id": t["band_id"], "from_face_m": r4((iv[0] - ta) / 1000.0),
                         "to_face_m": r4((iv[1] - ta) / 1000.0), "footprint_m": r4((iv[1] - iv[0]) / 1000.0),
                         "face_line_ends_widening": ends_used,
                         "sin_angle": round(sin, 4),
                         "relation": "THROUGH" if depth >= width - 2 * tol else "STOPS_AT_FACE",
                         "depth_into_band_m": r4(depth / 1000.0)})
        tees.sort(key=lambda x: x["from_face_m"])
        L = (tb - ta) / 1000.0
        pieces, cur = [], 0.0
        for t in tees:
            if t["from_face_m"] > cur + 1e-6:
                pieces.append(r4(t["from_face_m"] - cur))
            cur = max(cur, t["to_face_m"])
        if L > cur + 1e-6:
            pieces.append(r4(L - cur))
        spans[sp["span_id"]] = {"face_to_face_m": r4(L), "width_m": r4(width / 1000.0), "tees": tees,
                                "clear_pieces_m": pieces,
                                "start": sp["start"]["refs"], "end": sp["end"]["refs"]}
    missing = sorted(set(RUNS) - set(spans))

    # ---- ring, reading B: the angular range where a RADIAL link section (inner arc to outer arc) lies inside both
    # drawn arcs' ranges and crosses no column outline and no straight band strip (no link through a support)
    from shapely.geometry import LineString, Point as _Pt
    ei, eo = arcs["158"], arcs["157"]
    if ei.dxf.radius > eo.dxf.radius:
        ei, eo = eo, ei
    cx, cy = ei.dxf.center[0], ei.dxf.center[1]
    ox, oy = eo.dxf.center[0], eo.dxf.center[1]

    def in_sweep(e, ang):
        a0, a1 = e.dxf.start_angle, e.dxf.end_angle
        return (ang - a0) % 360.0 <= ((a1 - a0) % 360.0) + 1e-9

    zone = _Pt(cx, cy).buffer(eo.dxf.radius + 50.0)
    near_cols = {k: P for k, P in {"COL:" + i: Polygon(p).buffer(0) for i, p, _ in cols}.items() if P.intersects(zone)}
    near_bands = {k: Polygon(V2._rect(bb)) for k, bb in BB.items() if Polygon(V2._rect(bb)).intersects(zone)}
    steps, free, prev, blocked = 36000, [], False, {}
    for k in range(steps):
        ang = k * 360.0 / steps
        ok = in_sweep(ei, ang)
        if ok:
            # the ray from the inner centre meets the outer arc (own centre) at angle phi about the outer centre
            dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            fx, fy = cx - ox, cy - oy
            bq = fx * dx + fy * dy
            tt = -bq + math.sqrt(bq * bq - (fx * fx + fy * fy - eo.dxf.radius ** 2))
            px, py = cx + tt * dx, cy + tt * dy
            phi = math.degrees(math.atan2(py - oy, px - ox)) % 360.0
            ok = in_sweep(eo, phi)
            if ok:
                seg = LineString([(cx + ei.dxf.radius * dx, cy + ei.dxf.radius * dy), (px, py)])
                hit = [c for c, P in near_cols.items() if P.intersects(seg)] + \
                      [s for s, P in near_bands.items() if P.intersection(seg).length > 1.0]
                for c in hit:
                    blocked.setdefault(c, [ang, ang])[1] = ang
                ok = not hit
            if ok:
                if not prev:
                    free.append({"a0": ang, "a1": ang, "phi0": phi, "phi1": phi})
                else:
                    free[-1].update(a1=ang, phi1=phi)
        prev = ok
    step = 360.0 / steps
    radial = [{"sweep_deg": r4(f["a1"] - f["a0"] + step),
               "inner_arc_m": r4(math.radians(f["a1"] - f["a0"] + step) * ei.dxf.radius / 1000.0),
               "outer_arc_m": r4(math.radians(((f["phi1"] - f["phi0"]) % 360.0) + step) * eo.dxf.radius / 1000.0)}
              for f in free]
    ring_radial = {"pieces": radial, "blocked_by": sorted(blocked),
                   "centre_offset_m": r4(math.hypot(cx - ox, cy - oy) / 1000.0)}

    # ---- ring ARC:157+158, reading A: drawn face arcs net of the column outlines on them
    col_poly = {"COL:" + i: Polygon(p).buffer(0) for i, p, _ in cols}
    ring = {}
    for h in ("157", "158"):
        e = arcs[h]
        cx, cy, r = e.dxf.center[0], e.dxf.center[1], e.dxf.radius
        a0, a1 = e.dxf.start_angle, e.dxf.end_angle
        if a1 < a0:
            a1 += 360.0
        n = 20000
        from shapely.geometry import Point
        free, cov = [], {}
        prev = None
        for k in range(n + 1):
            ang = a0 + (a1 - a0) * k / n
            p = Point(cx + r * math.cos(math.radians(ang)), cy + r * math.sin(math.radians(ang)))
            hit = [cid for cid, P in col_poly.items() if P.buffer(1.0).contains(p)]
            for cid in hit:
                cov.setdefault(cid, [ang, ang])[1] = ang
            state = bool(hit)
            if not state:
                if prev is None or prev:
                    free.append([ang, ang])
                else:
                    free[-1][1] = ang
            prev = state
        pieces = [r4(math.radians(f[1] - f[0]) * r / 1000.0) for f in free if f[1] > f[0]]
        ring[h] = {"r_m": r4(r / 1000.0), "sweep_deg": r4(a1 - a0), "drawn_arc_m": r4(math.radians(a1 - a0) * r / 1000.0),
                   "columns_on_arc": {cid: {"deg": r4(v[1] - v[0]), "arc_m": r4(math.radians(v[1] - v[0]) * r / 1000.0)}
                                      for cid, v in sorted(cov.items())},
                   "face_pieces_m": pieces, "face_total_m": r4(sum(pieces))}
    res = {"source": {"drive": "Alsenan chalet project / ST7757 dxf.dxf", "sha256": R.DXF_SHA,
                      "method": "T-141 bands + GROUND_SYSTEM_SPANS_V2 spans; tee footprints by V2._junction_interval; "
                                "ring arcs sampled 20000 steps against S-COL.BON outlines (+1 mm)"},
           "spans": spans, "missing_runs": missing, "ring": ring, "ring_radial": ring_radial}
    path = os.path.join(a.out, "CLEAR_SPANS_T272R2.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
