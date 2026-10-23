"""T-222 (blockwork resolution, part 2 of the HELD bounds): the 1F bay basis, P-GF-05 and P-1F-01 on the development
villa (Alsenan). Development evidence only, not an accuracy claim.

Reads at run time (outside the repository; nothing from them is written except numbers and ids):
  <cap>    the T-125 capture of P7757.dxf (research/agents_t125/alsenan_v2_dump.py), Drive "Alsenan chalet project" /
           P7757_DXF_COMPRESSED.zip
  <st>     ST7757 dxf.dxf (Drive "Alsenan chalet project")
The run re-measures the V2 plan run with engine/source/masonry_centreline_v2.py on the capture to get the strips it
counts (read-only use of the module). Faces, caps and members are named by DXF handle; levels read from the
architect's DWF (vector) are in READINGS_T222.csv with their view and how they were read.

Usage (Python 3.11):  python3 -I research/agents_t222/alsenan_t222.py <cap.pkl> <ST7757.dxf> [--check]
Writes research/agents_t222/T222_RESULTS.csv; --check compares with the committed file instead.
"""
from __future__ import annotations

import argparse
import csv
import io
import math
import pickle
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
import bay_and_heads as B  # noqa: E402

OUT = HERE / "T222_RESULTS.csv"
K = 0.001

# ---- 1F bay (W17 concave glazed bay in 1F-W00 / 1F-W01 / 1F-W25), P7757.dxf 1F plan, wall layer '1' and 'W'
BAY_ARCS = {"outer_face_r": ("D2:3021:0", "D2:3022:0", "D2:3024:0"),     # r 1.935 (towards the bay's centre)
            "inner_face_r": ("D2:3025:0", "D2:3026:0", "D2:3030:0")}     # r 2.135 (room side)
CAP_FULL = {"bottom": "D2:3031:0", "top": "D2:3033:0"}                   # layer 1, full band thickness
CAP_FRAME = {"bottom": "D2:3032:0", "top": "D2:3034:0"}                  # layer W, 0.12 frame line (not the end)
STRAIGHT = "WB-FL0041-FL0042"                                            # 1F-W00 (#1) / 1F-W01 (#2), t 0.20
CROSS = "WB-FL0022-FL0023"                                               # 1F-W14 + W15 (P-1F-01), t 0.15
CROSS_FACES = ("D2:3082:0", "D2:3084:0")                                 # its two faces at the bay end
# ST7757 dxf.dxf FIRST FLOOR ROOF SLAB: CB12 band faces (T-110 BM-1F-017, CB12 25x75), placed by the T-108 1F
# translation (every one of the 20 1F columns, S-COL.BON, one vote)
CB12_FACES = ("5DE", "5DF")
STOREY_1F, CB12_D, SLAB_1F = 4.20, 0.75, 0.16            # T-143 / T-108; T-110 register; ST p.8 note 18 (T-143)
WINDOW_PAD = 0.30                                        # window: the bay's extent +- this along the straight wall

# ---- P-GF-05 (court-wall passage mouth, engine GF OP-007): member over it on the GROUND FLOOR ROOF SLAB
B1_FACES = ("2AE", "2AF")                                # B1 band (T-110 B1 20x40) over the opening, continuous
PGF05 = {"width": 1.20, "floor": 0.15, "head": 2.65, "lintel_d": 0.20, "struct_top_1F": 5.45, "B1_d": 0.40}


def st_translation(st, cols_m):
    """ST -> architectural plan (metres), one translation voted by the column outlines; all must match."""
    import numpy as np
    from collections import Counter
    sc = []
    for e in st.modelspace().query('LWPOLYLINE[layer=="S-COL.BON"]'):
        p = np.array([(x * K, y * K) for x, y, *_ in e.get_points()])
        if len(p) >= 3:
            sc.append((p.mean(0), tuple(np.round(p.max(0) - p.min(0), 3))))
    ac = [(np.array(q).mean(0), tuple(np.round(np.array(q).max(0) - np.array(q).min(0), 3))) for q in cols_m]
    votes = Counter()
    for a, sa in ac:
        for c, ss in sc:
            if sa == ss or sa == ss[::-1]:
                votes[tuple(np.round(c - a, 3))] += 1
    (tx, ty), n = votes.most_common(1)[0]
    if n != len(ac):
        raise ValueError(f"column match {n} / {len(ac)}: no single translation")
    return tx, ty, n


def v2_strips(cap_floor):
    """The strips the V2 run counts (its own identity union), captured from the module without changing it."""
    import shapely.ops as so
    from engine.source import masonry_centreline_v2 as V2
    calls, orig = [], so.unary_union

    def spy(g, *a, **k):
        g = list(g)
        calls.append(g)
        return orig(g, *a, **k)
    so.unary_union = spy
    try:
        rec = V2.measure_floors({"1F": cap_floor})["1F"]
    finally:
        so.unary_union = orig
    total = rec["identity"]["sum_run_x_t_m2"]
    cols = [orig(h) for h in calls if len(h) == len(cap_floor["columns_m"])]
    for g in calls:
        if len(g) != rec["identity"]["pieces"]:
            continue
        u = orig(g)
        for c in cols or [None]:
            uc = u.difference(c) if c is not None else u
            if abs(uc.area - total) < 0.005:          # = the module's own identity (strip union less columns)
                return uc, rec
    raise ValueError("V2 strip union not found")


def bay(cap, st):
    from shapely.geometry import box
    f = cap["floors"]["1F"]
    segs = {s["id"]: s for s in f["ents"]["segments"]}
    arcs = {a["id"]: a for a in f["ents"]["arcs"]}
    walls = {w["wall_id"]: w for w in f["walls"]}
    c0 = arcs[BAY_ARCS["outer_face_r"][1]]
    centre = (c0["c"][0] * K, c0["c"][1] * K)
    r_in = round(arcs[BAY_ARCS["outer_face_r"][1]]["r"] * K, 4)
    r_out = round(arcs[BAY_ARCS["inner_face_r"][1]]["r"] * K, 4)
    for grp in BAY_ARCS.values():                      # every face piece on the same circle
        for h in grp:
            a = arcs[h]
            if math.dist((a["c"][0] * K, a["c"][1] * K), centre) > 1e-6:
                raise ValueError(f"{h} not concentric")
    arc = B.ArcBand("1F-W25", centre, r_in, r_out, through=True)
    cap_pts = {k: ((segs[h]["a"][0] * K, segs[h]["a"][1] * K), (segs[h]["b"][0] * K, segs[h]["b"][1] * K))
               for k, h in CAP_FULL.items()}
    for k, h in CAP_FRAME.items():                     # the frame line must be refused as a glazing end
        p = ((segs[h]["a"][0] * K, segs[h]["a"][1] * K), (segs[h]["b"][0] * K, segs[h]["b"][1] * K))
        try:
            B.glazing_sector(arc, p, cap_pts["top" if k == "bottom" else "bottom"])
            raise AssertionError("frame line accepted as a cap")
        except ValueError:
            pass
    sw = walls[STRAIGHT]
    a = (sw["centreline"][0][0] * K, sw["centreline"][0][1] * K)
    b = (sw["centreline"][-1][0] * K, sw["centreline"][-1][1] * K)
    if abs(a[0] - b[0]) > 1e-6:
        raise ValueError("this reading expects the straight wall vertical on the plan; rotate the frame first")
    # the glazing sector is the one on the room side of the straight wall (away from the bay's centre)
    side = -1.0 if centre[0] > a[0] else 1.0
    glz, span = B.glazing_sector(arc, cap_pts["bottom"], cap_pts["top"], through=(centre[0] + side, centre[1]))
    straight = B.StraightBand("1F-W00/W01", a, b, float(sw["t_m"]), through=True)
    cw = walls[CROSS]
    ca = (cw["centreline"][0][0] * K, cw["centreline"][0][1] * K)
    cb = (cw["centreline"][-1][0] * K, cw["centreline"][-1][1] * K)
    # the stem's band reaches the face it stops on (the straight wall's room face): a T stem stops ON the face
    half_face = a[0] - float(sw["t_m"]) / 2 if centre[0] > a[0] else a[0] + float(sw["t_m"]) / 2
    if abs(cb[1] - ca[1]) > 1e-6:
        raise ValueError("the cross wall is expected horizontal on the plan")
    far = max(ca, cb, key=lambda q: q[0]) if centre[0] > a[0] else min(ca, cb, key=lambda q: q[0])
    near = ca if far is cb else cb
    cross = B.StraightBand("1F-W14+W15", near, (half_face, far[1]), float(cw["t_m"]))
    # window: the arc band's reach (+ 0.05 m) into the room x the bay's extent +- WINDOW_PAD along the straight wall
    half_t = float(sw["t_m"]) / 2
    win = box(min(a[0], centre[0] - r_out) - 0.05 if side < 0 else a[0] - half_t,
              centre[1] - r_out - WINDOW_PAD,
              a[0] + half_t if side < 0 else max(a[0], centre[0] + r_out) + 0.05,
              centre[1] + r_out + WINDOW_PAD)
    for c in f["columns_m"]:                           # the window must hold no column (concrete is not masonry)
        from shapely.geometry import Polygon as _P
        if _P(c).intersects(win) and _P(c).intersection(win).area > 1e-9:
            raise ValueError("a column lies in the bay window: narrow WINDOW_PAD")
    # the cross wall's end region up to the main band face (its faces stop on the arc / the main wall)
    f1, f2 = (segs[h] for h in CROSS_FACES)
    yb = sorted([f1["a"][1] * K, f2["a"][1] * K])
    x_end = max(max(f1["a"][0], f1["b"][0]), max(f2["a"][0], f2["b"][0])) * K
    extra = [box(min(f1["a"][0], f1["b"][0], f2["a"][0], f2["b"][0]) * K, yb[0], x_end, yb[1])]
    mas = B.bay_masonry(arc, [straight], glz, win, extra=extra)
    counted, v2rec = v2_strips(f)
    stub = next(r for r in v2rec["runs"] if r["run_id"].startswith("BAY|"))
    stub_m = float(stub["physical_blockwork_lm"])
    # height zones from the ST 1F roof slab plan
    tx, ty, nvote = st_translation(st, f["columns_m"])
    e1, e2 = (st.entitydb[h] for h in CB12_FACES)
    xb = sorted([e1.dxf.start.x * K - tx, e2.dxf.start.x * K - tx])
    yr = sorted([e1.dxf.start.y * K - ty, e1.dxf.end.y * K - ty, e2.dxf.start.y * K - ty, e2.dxf.end.y * K - ty])
    cb12 = box(xb[0], yr[0], xb[1], yr[-1])
    zones = [B.Zone("slab 0.16", win, round(STOREY_1F - SLAB_1F, 3)),
             B.Zone("CB12 25x75", cb12, round(STOREY_1F - CB12_D, 3))]
    al = B.allocate(mas, [straight, arc, cross], counted=counted, zones=zones)
    # the stub V2 already counts (1F-STUB-001) lies inside the bay's share: T-108 booked it at 3.45 m
    w25 = al.by_wall["1F-W25"]
    rows = [("bay", "V2 counted strips in the window (m2)", round(counted.intersection(mas).area, 4)),
            ("bay", "drawn masonry in the window (m2)", round(mas.area, 4)),
            ("bay", "glazing sector sweep between the full caps (rad)", round(span, 5)),
            ("bay", "glazing on the band mid circle between the caps (m)", round(arc.r_mid * span, 4)),
            ("bay", "ST translation votes (1F columns)", nvote),
            ("bay", "CB12 band width (m)", round(xb[1] - xb[0], 3)),
            ("bay", "unassigned masonry (m2)", round(al.unassigned_m2, 5)),
            ("bay", "1F-W25 physical length incl. stub (m)", round(w25["length_m"], 4)),
            ("bay", "1F-W25 gross (m2)", round(w25["gross_m2"], 3)),
            ("bay", "1F-W25 stub already established (m)", round(stub_m, 4)),
            ("bay", "1F-W25 gross established by T-108 (m2)", round(stub_m * (STOREY_1F - CB12_D), 3)),
            ("bay", "1F-W25 change (m)", round(w25["length_m"] - stub_m, 4)),
            ("bay", "1F-W25 change (m2)", round(w25["gross_m2"] - stub_m * (STOREY_1F - CB12_D), 3)),
            ("bay", "1F-W00/W01 change (m)", round(al.by_wall["1F-W00/W01"]["length_m"], 4)),
            ("bay", "1F-W00/W01 change (m2)", round(al.by_wall["1F-W00/W01"]["gross_m2"], 3)),
            ("bay", "1F-W14+W15 junction piece (m)", round(al.by_wall["1F-W14+W15"]["length_m"], 4)),
            ("bay", "1F-W14+W15 junction piece (m2)", round(al.by_wall["1F-W14+W15"]["gross_m2"], 3))]
    return rows


def pgf05(cap, st):
    f = cap["floors"]["GF"]
    tx, ty, nvote = st_translation(st, f["columns_m"])
    op = next(o for o in f["openings"] if o["opening_id"] == "OP-007")
    cx, cy = op["position"]["centre_m"]
    e1, e2 = (st.entitydb[h] for h in B1_FACES)
    ys = sorted([e1.dxf.start.y * K - ty, e2.dxf.start.y * K - ty])
    xr = sorted([e1.dxf.start.x * K - tx, e1.dxf.end.x * K - tx])
    on_band = ys[0] - 1e-6 <= cy <= ys[1] + 1e-6 and xr[0] <= cx - 0.6 and cx + 0.6 <= xr[1]
    if not on_band:
        raise ValueError("B1 band does not run over the whole opening")
    P = PGF05
    soffit = P["struct_top_1F"] - P["B1_d"]
    st_, val = B.masonry_above(P["width"], soffit - P["floor"], head_level_m=P["head"] - P["floor"],
                               lintel_depth_m=P["lintel_d"])
    if st_ != "VALUE":
        raise ValueError(st_)
    return [("P-GF-05", "ST translation votes (GF columns)", nvote),
            ("P-GF-05", "B1 band width over the opening (m)", round(ys[1] - ys[0], 3)),
            ("P-GF-05", "opening centre offset from the B1 band axis (m)", round(abs(cy - (ys[0] + ys[1]) / 2), 3)),
            ("P-GF-05", "B1 soffit (m)", round(soffit, 3)),
            ("P-GF-05", "masonry above the lintel (m2)", val),
            ("P-GF-05", "masonry above the lintel (m3 at 0.20)", round(val * 0.20, 4))]


def p1f01(cap):
    """B-B looks north from its cut; the wall carrying D-1F-08 / D-1F-09 stands between the cut and P-1F-01."""
    f = cap["floors"]["1F"]
    ops = {o["opening_id"]: o for o in f["openings"]}
    walls = {w["wall_id"]: w for w in f["walls"]}
    p = ops["OP-009"]
    dwall = walls["WB-FL0013-FL0014"]
    px, py = p["position"]["centre_m"]
    near_y = dwall["centreline"][0][1] * K
    xs = sorted([dwall["centreline"][0][0] * K, dwall["centreline"][-1][0] * K])
    gap = abs(py - near_y)
    drawn = [B.Drawn("FACE", xs[0], xs[1], 1.0, ref="WB-FL0013-FL0014 face")]
    for oid in ("OP-005", "OP-006"):
        o = ops[oid]
        ox = o["position"]["centre_m"][0]
        drawn.append(B.Drawn("LEAFED_DOOR", ox - o["width_m"] / 2, ox + o["width_m"] / 2, 1.0, ref=oid))
    kind, det = B.view_evidence(px - 0.65, px + 0.65, 1.0 + gap, drawn)
    held = B.masonry_above(1.30, STOREY_1F - SLAB_1F, head_level_m=None, lintel_depth_m=0.20)
    return [("P-1F-01", "plan gap between P-1F-01's wall and the B-B door wall (m)", round(gap, 3)),
            ("P-1F-01", "B-B evidence for P-1F-01", kind),
            ("P-1F-01", "B-B elements in front", ";".join(det)),
            ("P-1F-01", "masonry above the lintel", f"{held[0]} {held[1][0]} .. {held[1][1]}")]


def run(cap_p, st_p):
    import ezdxf
    cap = pickle.load(open(cap_p, "rb"))
    st = ezdxf.readfile(st_p)
    rows = bay(cap, st) + pgf05(cap, st) + p1f01(cap)
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["item", "quantity", "value"])
    w.writerows(rows)
    return s.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cap")
    ap.add_argument("st")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    txt = run(a.cap, a.st)
    if a.check:
        ok = OUT.read_text() == txt
        print("T222_RESULTS.csv", "PASS" if ok else "DIFFERS")
        if not ok:
            print(txt)
        return 0 if ok else 1
    OUT.write_text(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
