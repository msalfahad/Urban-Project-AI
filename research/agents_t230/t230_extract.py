"""T-230 extraction on the structural DXF (Drive "Alsenan chalet project", "ST7757 dxf.dxf", sha 9f9d1179).

    .work/venv/bin/python -I research/agents_t230/t230_extract.py <structural.dxf> [--out <dir>]

Reads, by layer and handle (nothing typed): the ground-beam bands and columns of the GROUND BEAMS PLAN and the footing
and column outlines of the FOUNDATION PLAN exactly as T-141 does (its runner's `outlines`, the frozen sheet frames, the
S5 band pairing incl. arcs, GROUND_SYSTEM_SPANS_V2 spans); the lift ring S-BW (T-204: 7C2 outer / 7BE inner); the
neck readings of T-217 (LEDGER_T217.csv, FOUNDATION rows). Writes ALSENAN_END_INPUT.json: per ground-beam span end
the plan areas (m2) of DOUBLE / GAP per neck reading, per free / footing end the drawn support, per span the plan
overlap with every footing; values, ids and handles only, no coordinates.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import end_ownership as EO  # noqa: E402

spec = importlib.util.spec_from_file_location("r141", os.path.join(ROOT, "research/agents_t141/run_t141_alsenan.py"))
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)
T217 = os.path.join(ROOT, "research/agents_t217/LEDGER_T217.csv")
TOL_MM = 5.0


def dims(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return max(xs) - min(xs), max(ys) - min(ys)


def same_size(poly, ab, tol=TOL_MM):
    w, h = dims(poly)
    return abs(sorted((w, h))[0] - sorted(ab)[0]) <= tol and abs(sorted((w, h))[1] - sorted(ab)[1]) <= tol


def printed_sizes(cands):
    """[(a_mm, b_mm, printed?)] from a T-217 candidates cell: '0.30x0.50 [SCHEDULE:..., TEXT:...] | 0.30x0.40 [...]'."""
    out = []
    for part in cands.split(" | "):
        m = re.match(r"([0-9.]+)x([0-9.]+) \[(.*)\]", part.strip())
        if not m:
            continue
        a, b, src = float(m.group(1)) * 1000, float(m.group(2)) * 1000, m.group(3)
        out.append((a, b, ("SCHEDULE" in src or "TEXT" in src or "DIM" in src), src))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("--out", default=HERE)
    a = ap.parse_args()
    import ezdxf
    if R.sha(a.dxf) != R.DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    doc = ezdxf.readfile(a.dxf)
    msp = doc.modelspace()
    GBP, FP = R.GBP, R.FP
    shift = FP[0] - GBP[0]

    faces = [{"handle": e.dxf.handle, "layer": e.dxf.layer, "p0": tuple(e.dxf.start)[:2], "p1": tuple(e.dxf.end)[:2]}
             for e in msp.query("LINE[layer=='1']") if R.inb(*tuple(e.dxf.start)[:2], GBP)]
    res = R.GN.pair_straight(faces, width=300.0, tol=12.0, admitted_layers={"1"})
    bands = [{"band_id": "+".join(b["handles"]), "u": b["u"], "lo_off": b["lo_off"], "hi_off": b["hi_off"],
              "t0": b["t0"], "t1": b["t1"], "handles": b["handles"]} for b in res["bands"]]
    arcs = [{"handle": e.dxf.handle, "layer": "1", "cx": e.dxf.center[0], "cy": e.dxf.center[1], "r": e.dxf.radius,
             "a0": e.dxf.start_angle, "a1": e.dxf.end_angle} for e in msp.query("ARC[layer=='1']")
            if R.inb(e.dxf.center[0], e.dxf.center[1], GBP)]
    ares = R.GN.pair_arcs(arcs, width=300.0, tol=12.0, admitted_layers={"1"})
    for k, b in enumerate(ares["bands"], start=1):
        bands.append({"band_id": f"ARC:{'+'.join(b['handles'])}/{k}", "u": (1.0, 0.0), "lo_off": 0, "hi_off": 1,
                      "t0": 0, "t1": 1, "handles": b["handles"], "kind": "ARC",
                      "polygon": [tuple(p) for p in b["polygon"]]})
    cols = R.outlines(msp, "S-COL.BON", GBP)
    cols_fp = [(i, [(x - shift, y) for x, y in p]) for i, p, _ in R.outlines(msp, "S-COL.BON", FP)]
    feet_fp = R.outlines(msp, "S-FOOTINGS", FP, blocks=("F",))
    feet_gb = [(i, [(x - shift, y) for x, y in p], h) for i, p, h in feet_fp]
    supports = [{"support_id": "COL:" + i, "kind": "COLUMN", "polygon": p, "handles": h} for i, p, h in cols] + \
               [{"support_id": "FTG:" + i, "kind": "FOOTING", "polygon": p, "handles": h} for i, p, h in feet_gb]
    out = R.V2.split_ground_beams(bands, supports, units="mm", classes=R.CLASSES)
    S = {s["support_id"]: s for s in supports}
    B = {b["band_id"]: b for b in bands}

    # lift ring (T-204): S-BW closed polylines on the ground-beam sheet
    ring = []
    for e in msp.query("LWPOLYLINE[layer=='S-BW']"):
        pts = [tuple(p[:2]) for p in e.get_points()]
        if R.inb(*pts[0], GBP):
            ring.append((e.dxf.handle, pts))

    # T-217 neck readings (FOUNDATION rows), keyed by the ground-beam-plan handle
    t217 = {}
    for r in csv.DictReader(open(T217, encoding="utf-8")):
        if r["storey"] != "FOUNDATION":
            continue
        m = re.search(r"DRAWN:GBP ([0-9A-F]+)", r["candidates"])
        if m:
            t217[m.group(1)] = r

    def necks(cid):
        """Neck plan candidates for a ground-beam-plan column: (status, [polys], note)."""
        h = cid.split(":", 1)[1]
        P = S[cid]["polygon"]
        r = t217.get(h)
        if r is None:
            return "NO_T217_RECORD", [P], "drawn outline (no T-217 FOUNDATION row names this handle)"
        sizes = printed_sizes(r["candidates"])
        printed = [(x, y) for x, y, p, _ in sizes if p]
        if r["status"] == "AGREE":
            return EO.DRAWING_CONFIRMED, [P], f"T-217 AGREE ({r['member']} {r['mark']})"
        if r["status"] == "DRAFTING_NOTE":
            ab = printed[0]
            if same_size(P, ab):
                return EO.DRAWING_CONFIRMED, [P], f"T-217 DRAFTING_NOTE: the ground-beam plan draws the printed {ab}"
            fp = [q for i, q in cols_fp if EO.overlap_area(q, P) > 0.5 * EO.area(P) and same_size(q, ab)]
            if len(fp) == 1:
                shared = sum(1 for k in range(4) for v in (0, 1)
                             if abs(sorted(c[v] for c in fp[0])[k] - sorted(c[v] for c in P)[k]) <= TOL_MM) // 2
                return EO.DRAWING_CONFIRMED, fp, (f"T-217 DRAFTING_NOTE: printed {ab} drawn on the foundation plan at "
                                                  f"the same place ({shared} of 4 edge pairs coincide)")
            w, h_ = dims(P)
            axis = 0 if abs(w - sorted(ab)[0]) > TOL_MM and abs(w - sorted(ab)[1]) > TOL_MM else 1
            target = [v for v in ab if abs(v - (h_ if axis == 0 else w)) > TOL_MM] or list(ab)
            delta = max(target) - (w if axis == 0 else h_)
            return EO.HELD, EO.widened(P, axis, delta), f"T-217 DRAFTING_NOTE: printed {ab}, position not drawn"
        # CONFLICT: the drawn reading plus every other printed size, its extra at an unprinted position
        polys = [P]
        w, h_ = dims(P)
        for ab in printed:
            if same_size(P, ab):
                continue
            if abs(min(ab) - min(w, h_)) > TOL_MM:
                axis = 0 if w <= h_ else 1
                polys += EO.widened(P, axis, min(ab) - min(w, h_))
            else:
                axis = 0 if w >= h_ else 1
                polys += EO.widened(P, axis, max(ab) - max(w, h_))
        return EO.CONFLICT, polys, f"T-217 CONFLICT {r['member']} {r['mark']}: {sorted(set(printed))}"

    rows, free, overl, junction = [], [], [], {}
    for sp in out["spans"]:
        b = B[sp["band_id"]]
        u = tuple(b["u"])
        lo, hi = sorted((b["lo_off"], b["hi_off"]))
        ta = sp["start"]["face_station_m"] * 1000.0
        tb = sp["end"]["face_station_m"] * 1000.0
        rect = EO.band_slab(u, lo, hi, ta, tb)
        for i, fpoly, _ in feet_gb:
            a_ = EO.overlap_area(rect, fpoly) if len(fpoly) == 4 else None
            if a_ is None:
                from shapely.geometry import Polygon
                a_ = Polygon(rect).intersection(Polygon(fpoly)).area
            if a_ > 1.0:
                overl.append({"span_id": sp["span_id"], "footing": i, "plan_overlap_m2": round(a_ / 1e6, 4)})
        for end, t_face, side in (("start", ta, +1), ("end", tb, -1)):
            nd = sp[end]
            if nd["kind"] == "COLUMN":
                for cid in nd["refs"]:
                    st, polys, note = necks(cid)
                    g = EO.gb_end(u, lo, hi, t_face, side, polys, S[cid]["polygon"], depths=[1.0],
                                  t_drawn_end=b["t0"] if side > 0 else b["t1"])
                    rows.append({"span_id": sp["span_id"], "end": end, "column": cid, "neck_status": st,
                                 "neck_note": note, "n_readings": len(polys),
                                 "double_plan_m2_per_reading": [round(d / 1e6, 4) for d, _ in g["per_reading"]],
                                 "band_width_m": round((hi - lo) / 1000.0, 4)})
                    J = junction.setdefault(cid, {"status": st, "note": note, "polys": polys, "ends": [],
                                                  "double": [0.0] * len(polys), "regions": [[] for _ in polys]})
                    J["ends"].append(f"{sp['span_id']}:{end}")
                    for k, ((d, _), reg) in enumerate(zip(g["per_reading"], g["gap_regions"])):
                        J["double"][k] += d
                        if reg:
                            J["regions"][k].append(reg)
            elif nd["kind"] in ("FOOTING_FACE", "GAP_TO_COLUMN", "FREE_END"):
                t_drawn = b["t0"] if end == "start" else b["t1"]
                cands = []
                win = EO.band_slab(u, lo, hi, t_drawn - 600, t_drawn + 600)
                for rh, pts in ring:          # lift ring faces in the band strip near the drawn end (T-204)
                    ts = sorted({round(p[0] * u[0] + p[1] * u[1], 3) for p in EO.clip_convex(pts, win)})
                    if ts:
                        tt = min(ts, key=lambda v: abs(v - t_drawn))
                        cands.append({"id": f"S-BW {rh}", "kind": "WALL", "t_face": tt, "separation_m": 0.0})
                for r_ in nd["refs"]:
                    if r_.startswith("FTG:"):
                        # vertical gap >= 0.28 m: GB soffit >= +0.25 - 0.60 vs footing top <= -1.50 + 0.17 + 0.70
                        cands.append({"id": r_, "kind": "FOOTING", "t_face": t_face, "separation_m": 0.28})
                    elif r_.startswith("COL:"):
                        cin = EO.clip_convex(S[r_]["polygon"], EO.band_slab(u, lo, hi, -1e9, 1e9))
                        if len(cin) >= 3 and EO.area(cin) > 1.0:     # only a column IN the band's path
                            ts = [p[0] * u[0] + p[1] * u[1] for p in cin]
                            cands.append({"id": r_, "kind": "COLUMN", "t_face": max(ts) if end == "start" else
                                          min(ts), "separation_m": 0.0})
                fs = EO.free_end_support(t_drawn, cands, tol=TOL_MM)
                free.append({"span_id": sp["span_id"], "end": end, "v2_node": nd["kind"], "v2_refs": nd["refs"],
                             "v2_face_to_face_m": sp["lengths"]["face_to_face_m"],
                             "drawn_end_minus_v2_face_m": round(abs(t_drawn - t_face) / 1000.0, 4),
                             "support": fs.get("support"), "support_kind": fs.get("kind"), "status": fs["status"],
                             "refused": fs.get("refused"),
                             "length_to_support_m": None if fs.get("t_face") is None else
                             round(abs((tb if end == "start" else ta) - fs["t_face"]) / 1000.0, 4)})
    # strap strips (T-174 edge handles, foundation plan) moved onto the ground-beam sheet: plan overlap with spans
    from shapely.geometry import MultiPoint
    strap_ov = []
    for mark, hs in (("SB1", ("1689", "1B1C")), ("SB2", ("1B08", "1B09")), ("SB3", ("1B26", "1B27"))):
        pts = []
        for h in hs:
            e = doc.entitydb.get(h)
            pts += [(e.dxf.start[0] - shift, e.dxf.start[1]), (e.dxf.end[0] - shift, e.dxf.end[1])]
        hull = MultiPoint(pts).convex_hull
        for sp in out["spans"]:
            b = B[sp["band_id"]]
            lo, hi = sorted((b["lo_off"], b["hi_off"]))
            rect = EO.band_slab(tuple(b["u"]), lo, hi, sp["start"]["face_station_m"] * 1000.0,
                                sp["end"]["face_station_m"] * 1000.0)
            from shapely.geometry import Polygon as _P
            a_ = _P(rect).intersection(hull).area
            if a_ > 1.0:
                strap_ov.append({"strap": mark, "span_id": sp["span_id"], "plan_overlap_m2": round(a_ / 1e6, 4)})
    # one junction = one neck: DOUBLE summed over its ends, GAP = union of the beam regions not inside the neck
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    jrows = []
    for cid, J in sorted(junction.items()):
        gaps = []
        for k, P in enumerate(J["polys"]):
            regs = [Polygon(r) for r in J["regions"][k]]
            g = unary_union(regs).difference(Polygon(P)).area if regs else 0.0
            gaps.append(round(g / 1e6, 4))
        jrows.append({"column": cid, "neck_status": J["status"], "neck_note": J["note"], "ends": J["ends"],
                      "n_readings": len(J["polys"]),
                      "double_plan_m2_per_reading": [round(d / 1e6, 4) for d in J["double"]],
                      "gap_plan_m2_per_reading": gaps})
    data = {"source": {"drive": "Alsenan chalet project / ST7757 dxf.dxf", "sha256": R.DXF_SHA,
                       "sheets": "GROUND BEAMS PLAN (bands, columns, S-BW ring); FOUNDATION PLAN (footings, columns)"},
            "spans": len(out["spans"]), "column_ends": rows, "junctions": jrows, "free_ends": free,
            "gb_footing_plan_overlaps": overl, "strap_gb_plan_overlaps": strap_ov}
    with open(os.path.join(a.out, "ALSENAN_END_INPUT.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    print(len(out["spans"]), "spans;", len(rows), "column ends;", len(free), "free ends;", len(overl), "plan overlaps;", strap_ov)
    for r in jrows:
        if max(r["double_plan_m2_per_reading"]) > 0 or max(r["gap_plan_m2_per_reading"]) > 0 or \
                r["neck_status"] != EO.DRAWING_CONFIRMED:
            print(" ", r)
    for r in free:
        print(" FREE", r)


if __name__ == "__main__":
    main()
