"""T-242 extraction on the development villa's Drive drawings (values, ids and DXF handles only; no coordinates).

    .work/venv/bin/python -I research/agents_t242/t242_extract.py <structural.dxf> <architectural.dxf> \
        <ARCH_WALLS.json of the released baseline run> [--out <dir>]

Inputs (Drive "Alsenan chalet project"): "ST7757 dxf.dxf" (sha 9f9d1179), the architectural DXF from
P7757_DXF_COMPRESSED.zip (sha ab54dd55), and the ARCH_WALLS.json that `tools/release_baseline.py run
research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json` writes for those two files (REPRODUCED b96185d4).

What it reads, by layer and handle (nothing typed):
- GROUND BEAMS PLAN frame (T-141 runner: frames, band pairing, GROUND_SYSTEM_SPANS_V2 spans, S-COL.BON columns,
  foundation-plan footings moved by the frame pitch), the layer-1 arcs (curved bands), the S-BW lift ring, the
  S-BOUN bands (boundary wall at natural-ground level, ST p.14 "GROUND BEAM (20x40)"), the LEVEL texts of the sheet;
- the architectural GF plan placed on the ground-beam sheet by the translation that maps its LEVEL texts onto the
  14 copies on the structural sheet (same values), checked on the 30 architectural columns (residuals printed);
- ARCH_WALLS.json GF: the architectural wall over each beam and whether one of its sides is EXTERIOR.

Writes ALSENAN_GROUND_INPUT.json: per straight span its lengths, width, p.13 class on both length bases, ends,
mid-span tees, the three exterior / interior sources (S1 level-mark probe on the structural sheet, S2 architectural
wall kind, S3 is joined later from the T-138 record); per arc band its plan area net of supports and straight bands;
per S-BOUN band its area and width; the plan partition of the drawn band strips (each piece once). Areas in m2,
lengths in m, rounded to 0.1 mm / 0.0001 m2.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "research", "agents_t230"))
import end_ownership as EO  # noqa: E402

spec = importlib.util.spec_from_file_location("r141", os.path.join(ROOT, "research/agents_t141/run_t141_alsenan.py"))
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)

ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
PROBE_OFF_MM = 400.0       # S1 probe: 0.40 m outside each band face
WALL_ON_BEAM_MM = 200.0    # S2: wall centreline within 0.20 m of the beam axis, parallel, overlap > 0.10 m


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def r4(v):
    return round(float(v), 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("structural")
    ap.add_argument("architectural")
    ap.add_argument("arch_walls")
    ap.add_argument("--out", default=HERE)
    a = ap.parse_args()
    import ezdxf
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import polygonize, unary_union
    from shapely.strtree import STRtree

    if R.sha(a.structural) != R.DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    if sha(a.architectural) != ARCH_SHA:
        raise SystemExit("architectural DXF sha mismatch")
    doc = ezdxf.readfile(a.structural)
    msp = doc.modelspace()
    GBP, FP = R.GBP, R.FP
    shift = FP[0] - GBP[0]

    # ---- ground-beam bands and spans (exactly as T-141 / T-230)
    faces = [{"handle": e.dxf.handle, "layer": e.dxf.layer, "p0": tuple(e.dxf.start)[:2], "p1": tuple(e.dxf.end)[:2]}
             for e in msp.query("LINE[layer=='1']") if R.inb(*tuple(e.dxf.start)[:2], GBP)]
    res = R.GN.pair_straight(faces, width=300.0, tol=12.0, admitted_layers={"1"})
    bands = [{"band_id": "+".join(b["handles"]), "u": b["u"], "lo_off": b["lo_off"], "hi_off": b["hi_off"],
              "t0": b["t0"], "t1": b["t1"], "handles": b["handles"]} for b in res["bands"]]
    arcs = {e.dxf.handle: e for e in msp.query("ARC[layer=='1']") if R.inb(e.dxf.center[0], e.dxf.center[1], GBP)}
    # curved bands enter the span splitter as junction outlines (as T-141 / T-230: a straight band ending on a curved
    # one stops at its face); their own quantity is measured below from the two drawn arcs
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
    out = R.V2.split_ground_beams(bands, supports, units="mm", classes=R.CLASSES)
    B = {b["band_id"]: b for b in bands if b.get("kind") != "ARC"}
    unpaired = [{"handle": u["handle"], "piece_m": r4(u["length"] / 1000.0), "reason": u["reason"]}
                for u in res["unpaired"]]

    # ---- curved bands: the region between the two drawn arcs of one band (each arc over its own drawn range)
    def arc_pts(e, n=64):
        cx, cy, r = e.dxf.center[0], e.dxf.center[1], e.dxf.radius
        a0, a1 = e.dxf.start_angle, e.dxf.end_angle
        if a1 < a0:
            a1 += 360.0
        return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                 cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
    arc_pairs = [("139", "13A"), ("157", "158")]
    arc_polys = {}
    for h_out, h_in in arc_pairs:
        eo, ei = arcs[h_out], arcs[h_in]
        if eo.dxf.radius < ei.dxf.radius:
            eo, ei = ei, eo
        P = Polygon(arc_pts(eo) + list(reversed(arc_pts(ei)))).buffer(0)
        arc_polys[f"ARC:{h_out}+{h_in}"] = {"poly": P, "r_out_m": eo.dxf.radius / 1000.0, "r_in_m": ei.dxf.radius / 1000.0,
                                            "sweep_out_deg": r4((eo.dxf.end_angle - eo.dxf.start_angle) % 360),
                                            "sweep_in_deg": r4((ei.dxf.end_angle - ei.dxf.start_angle) % 360)}

    # ---- the drawn band strips (full drawn extent) and the span pieces (face to face)
    strip_full = {}
    for bid, b in B.items():
        lo, hi = sorted((b["lo_off"], b["hi_off"]))
        strip_full[bid] = Polygon(EO.band_slab(tuple(b["u"]), lo, hi, b["t0"], b["t1"]))
    span_poly = {}
    for sp in out["spans"]:
        b = B[sp["band_id"]]
        lo, hi = sorted((b["lo_off"], b["hi_off"]))
        span_poly[sp["span_id"]] = Polygon(EO.band_slab(tuple(b["u"]), lo, hi, sp["start"]["face_station_m"] * 1000.0,
                                                        sp["end"]["face_station_m"] * 1000.0))
    col_poly = {"COL:" + i: Polygon(p).buffer(0) for i, p, _ in cols}
    ring = []
    for e in msp.query("LWPOLYLINE[layer=='S-BW']"):
        pts = [tuple(p[:2]) for p in e.get_points()]
        if R.inb(*pts[0], GBP):
            ring.append((e.dxf.handle, Polygon(pts).buffer(0)))
    ring_outer = max(ring, key=lambda t: t[1].area)

    # ---- partition of the drawn beam strips: each piece in exactly one span / arc / column / named piece
    drawn = unary_union(list(strip_full.values()) + [v["poly"] for v in arc_polys.values()])
    spans_u = unary_union(list(span_poly.values()))
    cols_u = unary_union(list(col_poly.values()))
    arcs_net = {}
    for k, v in arc_polys.items():
        net = v["poly"].difference(unary_union(list(strip_full.values()))).difference(cols_u)
        arcs_net[k] = net
    arcs_u = unary_union(list(arcs_net.values()))
    pairs_double = []
    ids = sorted(span_poly)
    for i, s1 in enumerate(ids):
        for s2 in ids[i + 1:]:
            ov = span_poly[s1].intersection(span_poly[s2]).area
            if ov > 1.0:
                pairs_double.append({"a": s1, "b": s2, "plan_m2": r4(ov / 1e6)})
    span_col = []
    for s, P in span_poly.items():
        for c, Q in col_poly.items():
            ov = P.intersection(Q).area
            if ov > 1.0:
                span_col.append({"span_id": s, "column": c, "plan_m2": r4(ov / 1e6)})
    rest = drawn.difference(spans_u).difference(cols_u).difference(arcs_u).difference(ring_outer[1])
    pieces = []
    for g in getattr(rest, "geoms", [rest]):
        if g.is_empty or g.area < 1.0:
            continue
        near_c = sorted(c for c, Q in col_poly.items() if Q.distance(g) < 1.0)
        near_s = sorted(s for s, P in span_poly.items() if P.distance(g) < 1.0)
        in_bands = sorted(bid for bid, P in strip_full.items() if P.intersection(g).area > 0.5 * g.area)
        pieces.append({"plan_m2": r4(g.area / 1e6), "in_bands": in_bands, "touches_columns": near_c,
                       "touches_spans": near_s})
    pieces.sort(key=lambda d: -d["plan_m2"])

    # ---- S1: level-mark probe on the structural sheet (faces of the band edges, columns, ring, boundary bands
    # and the architectural walls / windows / doors placed on the sheet)
    ad = ezdxf.readfile(a.architectural)
    amsp = ad.modelspace()

    # placement of the architectural GF plan on the ground-beam sheet: the ground-beam sheet carries copies of the
    # architect's GF level marks; the translation that maps the most architectural LEVEL texts onto a structural one
    # of the SAME value is the placement (no frame typed in); it is then checked on the 30 architectural columns
    from collections import Counter
    slv = [(e.dxf.insert[0], e.dxf.insert[1], e.dxf.text) for e in msp.query("TEXT[layer=='LEVEL']")
           if R.inb(e.dxf.insert[0], e.dxf.insert[1], GBP)]
    alv_all = [(e.dxf.insert[0], e.dxf.insert[1], e.dxf.text) for e in amsp.query("TEXT[layer=='LEVEL']")]
    votes = Counter()
    for ax_, ay_, at in alv_all:
        for sx, sy, st_ in slv:
            if at == st_:
                votes[(round(sx - ax_), round(sy - ay_))] += 1
    (dx0, dy0), nv = votes.most_common(1)[0]
    if nv != len(slv):
        raise SystemExit(f"architectural GF plan not placed: {nv} of {len(slv)} level marks agree")

    def in_arch(x, y):
        return R.inb(x + dx0, y + dy0, GBP)
    alv = [t for t in alv_all if in_arch(t[0], t[1])]
    pairs = []
    for x, y, t in alv:
        best = min(slv, key=lambda s_: (s_[0] - x - dx0) ** 2 + (s_[1] - y - dy0) ** 2)
        pairs.append((best[0] - x, best[1] - y, best[2] == t))
    DX = sum(p[0] for p in pairs) / len(pairs)
    DY = sum(p[1] for p in pairs) / len(pairs)
    lv_resid = max(math.hypot(p[0] - DX, p[1] - DY) for p in pairs)
    acols = []
    for e in amsp.query("LWPOLYLINE[layer=='S-COL.BON']"):
        p = [tuple(q[:2]) for q in e.get_points()]
        cx, cy = sum(x for x, _ in p) / len(p), sum(y for _, y in p) / len(p)
        if in_arch(cx, cy):
            acols.append((cx, cy))
    scols = [(Q.centroid.x, Q.centroid.y) for Q in col_poly.values()]
    col_resid = sorted(min(math.hypot(sx - ax_ - DX, sy - ay_ - DY) for sx, sy in scols) for ax_, ay_ in acols)

    lines = []
    for e in msp.query("LINE[layer=='1']"):
        s0, s1 = e.dxf.start, e.dxf.end
        if R.inb(s0[0], s0[1], GBP):
            lines.append([(s0[0], s0[1]), (s1[0], s1[1])])
    for e in arcs.values():
        lines.append([(p[0], p[1]) for p in e.flattening(10)])
    boun = []
    for e in msp.query("LWPOLYLINE[layer=='S-BOUN']"):
        pts = [tuple(p[:2]) for p in e.get_points()]
        if R.inb(*pts[0], GBP):
            boun.append((e.dxf.handle, pts))
            lines.append(pts + [pts[0]])
    for _, P in ring:
        lines.append(list(P.exterior.coords))
    for Q in col_poly.values():
        lines.append(list(Q.exterior.coords))
    for lay in ("1", "W", "D"):
        for e in amsp.query(f"LINE[layer=='{lay}']"):
            s0, s1 = e.dxf.start, e.dxf.end
            if in_arch(s0[0], s0[1]):
                lines.append([(s0[0] + DX, s0[1] + DY), (s1[0] + DX, s1[1] + DY)])
        for e in amsp.query(f"LWPOLYLINE[layer=='{lay}']"):
            p = [(q[0] + DX, q[1] + DY) for q in e.get_points()]
            if len(p) > 1 and in_arch(p[0][0] - DX, p[0][1] - DY):
                lines.append(p + ([p[0]] if e.closed else []))
        for e in amsp.query(f"ARC[layer=='{lay}']"):
            if in_arch(e.dxf.center[0], e.dxf.center[1]):
                lines.append([(p[0] + DX, p[1] + DY) for p in e.flattening(20)])
    ext = []
    for cs in lines:
        if len(cs) == 2:
            (x0, y0), (x1, y1) = cs
            L = math.hypot(x1 - x0, y1 - y0)
            if L > 0:
                ux, uy = (x1 - x0) / L, (y1 - y0) / L
                cs = [(x0 - 30 * ux, y0 - 30 * uy), (x1 + 30 * ux, y1 + 30 * uy)]   # close 30 mm drafting gaps
        ext.append(LineString(cs))
    zfaces = list(polygonize(unary_union(ext)))
    tree = STRtree(zfaces)
    marks = [(Point(x, y), t) for x, y, t in slv]

    def level_at(x, y):
        pt = Point(x, y)
        c = [zfaces[i] for i in tree.query(pt) if zfaces[i].contains(pt)]
        if not c:
            return "BEYOND"          # outside every closed face of the sheet (beyond the plot line)
        f = min(c, key=lambda g: g.area)
        ls = sorted({t for q, t in marks if f.contains(q)})
        return "/".join(ls) if ls else "NO_MARK"

    W = json.load(open(a.arch_walls, encoding="utf-8"))
    gfw = [f for f in W["floors"] if f["floor"] == "GF"][0]["walls"]
    walls = []
    for w in gfw:
        (x0, y0), (x1, y1) = w["centreline"][0], w["centreline"][-1]
        walls.append((w["wall_id"], (x0 + DX, y0 + DY), (x1 + DX, y1 + DY), w["kind"], "EXTERIOR" in w["sides"]))

    def proj(u, p):
        return p[0] * u[0] + p[1] * u[1]
    # the two building parts: the annex lies west of the +0.15 passage between bands 10B+7D1 (annex east wall) and
    # 10A+7C9 (main-house west wall); the passage axis is midway between the two band axes
    def axis_x(bid):
        b = B[bid]
        lo_, hi_ = sorted((b["lo_off"], b["hi_off"]))
        n_ = (-b["u"][1], b["u"][0])
        return (lo_ + hi_) / 2.0 * n_[0]
    x_passage = (axis_x("10B+7D1") + axis_x("10A+7C9")) / 2.0
    span_rows = []
    for sp in out["spans"]:
        b = B[sp["band_id"]]
        u = tuple(b["u"])
        n = (-u[1], u[0])
        lo, hi = sorted((b["lo_off"], b["hi_off"]))
        mid = (lo + hi) / 2.0
        ta = sp["start"]["face_station_m"] * 1000.0
        tb = sp["end"]["face_station_m"] * 1000.0
        probes = []
        for frac in (0.25, 0.5, 0.75):
            t = ta + (tb - ta) * frac
            for side, off in (("A", lo - PROBE_OFF_MM), ("B", hi + PROBE_OFF_MM)):
                probes.append({"side": side, "at": frac,
                               "level": level_at(t * u[0] + off * n[0], t * u[1] + off * n[1])})
        over = []
        for wid, p0, p1, kind, has_ext in walls:
            L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            if L < 1.0 or abs(((p1[0] - p0[0]) * u[0] + (p1[1] - p0[1]) * u[1]) / L) < 0.995:
                continue
            if abs(proj(n, p0) - mid) > WALL_ON_BEAM_MM or abs(proj(n, p1) - mid) > WALL_ON_BEAM_MM:
                continue
            s0, s1 = sorted((proj(u, p0), proj(u, p1)))
            ov = min(s1, tb) - max(s0, ta)
            if ov > 100.0:
                over.append({"wall": wid, "kind": kind, "exterior_side": has_ext, "overlap_m": r4(ov / 1000.0)})
        tm = (ta + tb) / 2.0
        xm = tm * u[0] + mid * n[0]
        part = "ANNEX" if xm < x_passage else "MAIN"
        direction = "X" if abs(u[0]) > 0.999 else ("Y" if abs(u[1]) > 0.999 else "OBLIQUE")
        span_rows.append({
            "span_id": sp["span_id"], "band_id": sp["band_id"], "handles": sp["handles"], "direction": direction,
            "part": part, "width_m": sp["width_m"], "face_to_face_m": sp["lengths"]["face_to_face_m"],
            "centreline_m": sp["lengths"]["centreline_m"], "end_candidates": sp["lengths"]["end_candidates"],
            "class_face_to_face": sp["class_face_to_face"], "class_centreline": sp["class_centreline"],
            "class_state": sp["class_state"], "v2_status": sp["status"], "v2_held": sp["held_reasons"],
            "v2_flags": sp["flags"],
            "start": {"kind": sp["start"]["kind"], "refs": sp["start"]["refs"]},
            "end": {"kind": sp["end"]["kind"], "refs": sp["end"]["refs"]},
            # a tee or crossing is on THIS span only when its station lies between the span's two faces (V2 lists
            # the junctions of the whole band on every span of it)
            "tees_mid_span": [{"band_id": t["band_id"], "station_m": t["station_m"]} for t in sp["intermediate"]
                              if (ta - b["t0"]) / 1000.0 < t["station_m"] < (tb - b["t0"]) / 1000.0],
            "span_from_m": r4((ta - b["t0"]) / 1000.0), "span_to_m": r4((tb - b["t0"]) / 1000.0),
            "band_drawn_m": r4((b["t1"] - b["t0"]) / 1000.0),
            "S1_probes": probes, "S2_walls": over})

    arc_rows = []
    for k, v in arc_polys.items():
        net = arcs_net[k]
        touches = sorted(c for c, Q in col_poly.items() if Q.distance(v["poly"]) < 1.0) + \
            sorted(s for s, P in span_poly.items() if P.distance(v["poly"]) < 1.0)
        cpt = v["poly"].representative_point()
        # sides of the curved band: probe 0.40 m inside the inner arc and outside the outer arc at the mid angle
        e_out = [arcs[h] for h in k[4:].split("+") if arcs[h].dxf.radius / 1000.0 == v["r_out_m"]][0]
        cx, cy = e_out.dxf.center[0], e_out.dxf.center[1]
        a0, a1 = e_out.dxf.start_angle, e_out.dxf.end_angle
        if a1 < a0:
            a1 += 360.0
        side_levels = []
        for frac in (0.25, 0.5, 0.75):
            th = math.radians(a0 + (a1 - a0) * frac)
            for side, rr in (("inside", v["r_in_m"] * 1000.0 - PROBE_OFF_MM), ("outside", v["r_out_m"] * 1000.0 + PROBE_OFF_MM)):
                side_levels.append({"side": side, "at": frac, "level": level_at(cx + rr * math.cos(th), cy + rr * math.sin(th))})
        arc_rows.append({"arc_band": k, "part": "ANNEX" if v["poly"].centroid.x < x_passage else "MAIN", "r_out_m": r4(v["r_out_m"]), "r_in_m": r4(v["r_in_m"]),
                         "width_m": r4(v["r_out_m"] - v["r_in_m"]),
                         "sweep_out_deg": v["sweep_out_deg"], "sweep_in_deg": v["sweep_in_deg"],
                         "drawn_plan_m2": r4(v["poly"].area / 1e6), "net_plan_m2": r4(net.area / 1e6),
                         "deducted_straight_and_columns_m2": r4((v["poly"].area - net.area) / 1e6),
                         "touches": touches, "S1_probes": side_levels})
    del cpt

    boun_rows = []
    for h, pts in boun:
        P = Polygon(pts).buffer(0)
        mrr = P.minimum_rotated_rectangle
        xs = list(mrr.exterior.coords)
        e1 = math.hypot(xs[1][0] - xs[0][0], xs[1][1] - xs[0][1])
        e2 = math.hypot(xs[2][0] - xs[1][0], xs[2][1] - xs[1][1])
        ov_span = sum(P.intersection(Q).area for Q in span_poly.values())
        ov_col = sum(P.intersection(Q).area for Q in col_poly.values())
        ov_full = sum(P.intersection(Q).area for Q in strip_full.values())
        # width read from the polygon: twice the area over the perimeter for a thin band (exact for a rectangle)
        width = 2.0 * P.area / P.length if len(pts) > 4 else min(e1, e2)
        boun_rows.append({"handle": h, "vertices": len(pts), "plan_m2": r4(P.area / 1e6),
                          "width_m": r4(width / 1000.0), "rect_sides_m": sorted([r4(e1 / 1000.0), r4(e2 / 1000.0)]),
                          "overlap_spans_m2": r4(ov_span / 1e6), "overlap_columns_m2": r4(ov_col / 1e6),
                          "overlap_band_strips_m2": r4(ov_full / 1e6)})

    data = {"source": {"drive": "Alsenan chalet project / ST7757 dxf.dxf + P7757_DXF_COMPRESSED.zip (P7757.dxf)",
                       "structural_sha256": R.DXF_SHA, "architectural_sha256": ARCH_SHA,
                       "arch_walls": "ARCH_WALLS.json of release_baseline V29_ROUTEG_NO_PROFILE (REPRODUCED b96185d4)"},
            "alignment": {"architectural_columns": len(acols), "level_texts_paired": len(pairs),
                          "level_texts_same_value": sum(1 for p in pairs if p[2]),
                          "level_text_residual_mm": round(lv_resid, 1),
                          "column_centroid_residual_mm_max": round(col_resid[-1], 1),
                          "column_centroid_residual_note": "architectural columns are drawn 0.20 / 0.25 wide inside "
                                                            "the wall, the structural ones 0.30: centroids differ by "
                                                            "half the width difference (<= 0.05 m in each axis)"},
            "spans": span_rows, "arc_bands": arc_rows, "boundary_bands": boun_rows,
            "partition": {"drawn_band_strips_m2": r4(drawn.area / 1e6), "spans_m2": r4(spans_u.area / 1e6),
                          "span_sum_m2": r4(sum(P.area for P in span_poly.values()) / 1e6),
                          "columns_in_strips_m2": r4(drawn.intersection(cols_u).area / 1e6),
                          "arcs_net_m2": r4(arcs_u.area / 1e6),
                          "lift_ring_in_strips_m2": r4(drawn.intersection(ring_outer[1]).area / 1e6),
                          "span_span_doubles": pairs_double, "span_column_overlaps": span_col,
                          "unbilled_pieces": pieces, "unpaired_face_pieces": unpaired}}
    with open(os.path.join(a.out, "ALSENAN_GROUND_INPUT.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    print(len(span_rows), "spans;", len(arc_rows), "arc bands;", len(boun_rows), "boundary bands;",
          "alignment", data["alignment"])
    print("partition", {k: v for k, v in data["partition"].items() if not isinstance(v, list)})
    print("doubles", pairs_double, "span/column", span_col)
    for p in pieces:
        print(" piece", p)


if __name__ == "__main__":
    main()
