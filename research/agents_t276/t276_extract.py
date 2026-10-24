"""T-276 face trace on the development villa's structural DXF (values, ids and DXF handles only; no coordinates).

    .work/venv/bin/python -I research/agents_t276/t276_extract.py <structural.dxf> [--out <dir>]

Input (Drive "Alsenan chalet project"): "ST7757 dxf.dxf" (sha 9f9d1179), the route G input. Nothing typed: the bands,
spans, columns, arcs, lift ring and slab panels are rebuilt EXACTLY as T-242 (MERGED 9455a63d) builds them
(research/agents_t242/t242_extract.py, structural part only), and the panel ids GS-nn are checked against the merged
ALSENAN_GROUND_INPUT.json (same area and same bordering runs, else the run stops).

What it adds: every vertical face of the buried ground-beam system is traced ONCE. The plan union of the drawn concrete
(band strips + curved bands + columns on the ground-beam plan + lift ring) is the solid; its boundary is every face that
can have earth against it: the boundary of each slab-panel hole (faces against the fill under a panel) and the outer
boundary (faces outside the building). Each boundary is walked in 5 mm steps and each step is given to the ONE drawn
member nearest to it: a span (and its side A / B and the drawn face LINE handle of that side), a column (neck), a
curved band (and its convex / concave face), the lift ring, or a band piece in no span (junction / GAP piece, T-242
partition). Lengths per owner per panel are written in metres (0.1 mm); the steps sum to the boundary length exactly.
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
sys.path.insert(0, os.path.join(ROOT, "research", "agents_t230"))
import end_ownership as EO  # noqa: E402
sys.path.insert(0, HERE)
import face_trace as FT  # noqa: E402

spec = importlib.util.spec_from_file_location("r141", os.path.join(ROOT, "research/agents_t141/run_t141_alsenan.py"))
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)

STEP_MM = 5.0


def r4(v):
    return round(float(v), 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("structural")
    ap.add_argument("--out", default=HERE)
    a = ap.parse_args()
    import ezdxf
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import unary_union
    from shapely.strtree import STRtree

    if R.sha(a.structural) != R.DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    doc = ezdxf.readfile(a.structural)
    msp = doc.modelspace()
    GBP, FP = R.GBP, R.FP
    shift = FP[0] - GBP[0]

    # ---- T-242 geometry, structural part, unchanged
    lines1 = {e.dxf.handle: e for e in msp.query("LINE[layer=='1']") if R.inb(*tuple(e.dxf.start)[:2], GBP)}
    faces = [{"handle": h, "layer": e.dxf.layer, "p0": tuple(e.dxf.start)[:2], "p1": tuple(e.dxf.end)[:2]}
             for h, e in lines1.items()]
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
    out = R.V2.split_ground_beams(bands, supports, units="mm", classes=R.CLASSES)
    B = {b["band_id"]: b for b in bands if b.get("kind") != "ARC"}

    def arc_pts(e, n=64):
        cx, cy, r = e.dxf.center[0], e.dxf.center[1], e.dxf.radius
        a0, a1 = e.dxf.start_angle, e.dxf.end_angle
        if a1 < a0:
            a1 += 360.0
        return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                 cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
    arc_polys = {}
    for h_out, h_in in (("139", "13A"), ("157", "158")):
        eo, ei = arcs[h_out], arcs[h_in]
        if eo.dxf.radius < ei.dxf.radius:
            eo, ei = ei, eo
        P = Polygon(arc_pts(eo) + list(reversed(arc_pts(ei)))).buffer(0)
        arc_polys[f"ARC:{h_out}+{h_in}"] = {"poly": P, "outer": eo, "inner": ei}
    strip_full = {}
    for bid, b in B.items():
        lo, hi = sorted((b["lo_off"], b["hi_off"]))
        strip_full[bid] = Polygon(EO.band_slab(tuple(b["u"]), lo, hi, b["t0"], b["t1"]))
    span_poly, span_meta = {}, {}
    for sp in out["spans"]:
        b = B[sp["band_id"]]
        lo, hi = sorted((b["lo_off"], b["hi_off"]))
        ta, tb = sp["start"]["face_station_m"] * 1000.0, sp["end"]["face_station_m"] * 1000.0
        span_poly[sp["span_id"]] = Polygon(EO.band_slab(tuple(b["u"]), lo, hi, ta, tb))
        span_meta[sp["span_id"]] = {"band": sp["band_id"], "lo": lo, "hi": hi, "ta": min(ta, tb), "tb": max(ta, tb),
                                    "L": sp["lengths"]["face_to_face_m"]}
    col_poly = {"COL:" + i: Polygon(p).buffer(0) for i, p, _ in cols}
    ring = []
    for e in msp.query("LWPOLYLINE[layer=='S-BW']"):
        pts = [tuple(p[:2]) for p in e.get_points()]
        if R.inb(*pts[0], GBP):
            ring.append((e.dxf.handle, Polygon(pts).buffer(0)))
    cols_u = unary_union(list(col_poly.values()))
    arcs_net = {k: v["poly"].difference(unary_union(list(strip_full.values()))).difference(cols_u)
                for k, v in arc_polys.items()}
    drawn = unary_union(list(strip_full.values()) + [v["poly"] for v in arc_polys.values()])
    spans_u = unary_union(list(span_poly.values()))
    ring_u = unary_union([P for _, P in ring])
    rest = drawn.difference(spans_u).difference(cols_u).difference(unary_union(list(arcs_net.values()))) \
        .difference(ring_u)
    pieces = {}
    for g in getattr(rest, "geoms", [rest]):
        if g.is_empty or g.area < 1.0:
            continue
        in_bands = sorted(bid for bid, P in strip_full.items() if P.intersection(g).area > 0.5 * g.area)
        near_c = sorted(c for c, Q in col_poly.items() if Q.distance(g) < 1.0)
        near_s = sorted(s for s, P in span_poly.items() if P.distance(g) < 1.0)
        key = f"PIECE:{'+'.join(in_bands) or 'none'}@{'+'.join(near_c + near_s)}"
        k2, n = key, 2
        while k2 in pieces:
            k2, n = f"{key}#{n}", n + 1
        pieces[k2] = {"poly": g, "in_bands": in_bands, "touches_columns": near_c, "touches_spans": near_s,
                      "plan_m2": r4(g.area / 1e6)}

    # ---- slab panels (T-242: holes of the solid >= 0.05 m2, ids by area, then bordering runs)
    solid = unary_union(list(strip_full.values()) + [v["poly"] for v in arc_polys.values()] +
                        list(col_poly.values()) + [P for _, P in ring]).buffer(5).buffer(-5)
    panels, small_holes = [], []
    for g in getattr(solid, "geoms", [solid]):
        for rr in g.interiors:
            P = Polygon(rr)
            if P.area < 0.05e6:
                small_holes.append(r4(P.area / 1e6))
                continue
            border = sorted(sid for sid, Q in span_poly.items() if Q.distance(P) < 2.0) + \
                sorted(k for k, v in arc_polys.items() if v["poly"].distance(P) < 2.0)
            panels.append({"plan_m2": r4(P.area / 1e6), "bordering_runs": border, "poly": P})
    panels.sort(key=lambda d: (-d["plan_m2"], d["bordering_runs"]))
    for k, pnl in enumerate(panels, start=1):
        pnl["panel_id"] = f"GS-{k:02d}"
    merged = json.load(open(os.path.join(ROOT, "research/agents_t242/ALSENAN_GROUND_INPUT.json"), encoding="utf-8"))
    mp = {p["panel_id"]: p for p in merged["slab_panels"]}
    for pnl in panels:
        m = mp.get(pnl["panel_id"])
        if not m or abs(m["plan_m2"] - pnl["plan_m2"]) > 1e-4 or m["bordering_runs"] != pnl["bordering_runs"]:
            raise SystemExit(f"panel {pnl['panel_id']} does not reproduce the merged T-242 panel")

    # ---- owners: every drawn member a face step can belong to
    owners = []
    for sid, P in span_poly.items():
        owners.append(("SPAN", sid, P))
    for cid, Q in col_poly.items():
        owners.append(("COLUMN", cid, Q))
    for k, P in arcs_net.items():
        owners.append(("ARC", k, arc_polys[k]["poly"]))
    for k, d in pieces.items():
        owners.append(("PIECE", k, d["poly"]))
    for h, P in ring:
        owners.append(("LIFT_RING", "S-BW:" + h, P))
    tree = STRtree([o[2] for o in owners])

    # which drawn LINE is the face of each side of each band (by its offset from the band axis frame)
    def face_handle(bid, side):
        b = B[bid]
        u, n = EO.band_frame(tuple(b["u"]))
        lo, hi = sorted((b["lo_off"], b["hi_off"]))
        want = lo if side == "A" else hi
        best = None
        for h in b["handles"]:
            e = lines1.get(h)
            if e is None:
                continue
            p = tuple(e.dxf.start)[:2]
            off = p[0] * n[0] + p[1] * n[1]
            if best is None or abs(off - want) < best[0]:
                best = (abs(off - want), h)
        return best[1] if best and best[0] < 15.0 else None

    def meta(kind, oid):
        if kind == "SPAN":
            m = span_meta[oid]
            u, n = EO.band_frame(tuple(B[m["band"]]["u"]))
            return {"u": u, "n": n, "lo": m["lo"], "hi": m["hi"], "ta": m["ta"], "tb": m["tb"]}
        if kind == "ARC":
            v = arc_polys[oid]
            return {"centre": (v["outer"].dxf.center[0], v["outer"].dxf.center[1]), "r_out": v["outer"].dxf.radius,
                    "r_in": v["inner"].dxf.radius}
        return {}
    owners4 = [(k, i, P, meta(k, i)) for k, i, P in owners]
    outers = sorted(getattr(solid, "geoms", [solid]), key=lambda g: -g.area)
    rings = [(pnl["panel_id"], list(pnl["poly"].exterior.coords)) for pnl in panels] + \
        [(f"OUTER-{k}", list(g.exterior.coords)) for k, g in enumerate(outers, start=1)]
    traced = FT.trace(owners4, rings, step=STEP_MM)
    boundaries = []
    for bid, _ in rings:
        t = traced[bid]
        bd = {"boundary": bid, "kind": "OUTER" if bid.startswith("OUTER-") else "PANEL", "length_m": r4(t["length"] / 1000.0),
              "max_step_to_member_mm": round(t["max_dist"], 1), "acc": t["pieces"]}
        if bd["kind"] == "OUTER":
            bd["solid_m2"] = r4(outers[int(bid[6:]) - 1].area / 1e6)
        boundaries.append(bd)

    # ---- every column outline on the ground-beam plan: which drawn member covers each part of its perimeter (a beam
    # framing into the column face: concrete against concrete) and which part is free (on a panel / outer boundary)
    col_contacts = {}
    fp_cols = [(i, Polygon(p).buffer(0)) for i, p, _ in R.outlines(msp, "S-COL.BON", FP)]
    for cid, Q in sorted(col_poly.items()):
        ls = LineString(list(Q.exterior.coords))
        L = ls.length
        nstep = max(1, int(math.ceil(L / STEP_MM)))
        acc = {}
        for k in range(nstep):
            s0, s1 = L * k / nstep, L * (k + 1) / nstep
            pt = ls.interpolate((s0 + s1) / 2.0)
            best = None
            for i in tree.query(pt.buffer(3.0)):
                kind, oid, P = owners[i]
                if kind == "COLUMN" and oid == cid:
                    continue
                d = P.distance(pt)
                if d <= 2.0 and (best is None or d < best[0]):
                    best = (d, kind, oid)
            if best is None:
                inside_panel = next((p["panel_id"] for p in panels if p["poly"].buffer(3.0).contains(pt)), None)
                key = ("FREE", inside_panel or "OUTER")
            else:
                key = (best[1], best[2])
            acc[key] = acc.get(key, 0.0) + (s1 - s0)
        c = Q.centroid
        fp_hit = [i for i, P in fp_cols if P.contains(Point(c.x + shift, c.y))]
        col_contacts[cid] = {"perimeter_m": r4(L / 1000.0), "plan_m2": r4(Q.area / 1e6),
                             "foundation_plan_outline": fp_hit[0] if len(fp_hit) == 1 else None,
                             "parts": [{"kind": k[0], "with": k[1], "length_m": r4(v / 1000.0)}
                                       for k, v in sorted(acc.items())]}

    # ---- every span side face line between its two face stations: what stands just beyond it (3 mm out): a panel
    # hole, the outside, or another drawn member (a beam framing in, a column): the evidence for each covered length
    panel_tree = STRtree([p["poly"] for p in panels])
    side_cover = {}
    for sid, m in sorted(span_meta.items()):
        u, n = EO.band_frame(tuple(B[m["band"]]["u"]))
        for side, off, sgn in (("A", m["lo"], -1.0), ("B", m["hi"], 1.0)):
            L = m["tb"] - m["ta"]
            nstep = max(1, int(math.ceil(L / STEP_MM)))
            acc = {}
            for k in range(nstep):
                t = m["ta"] + L * (k + 0.5) / nstep
                o = off + sgn * 3.0
                pt = Point(t * u[0] + o * n[0], t * u[1] + o * n[1])
                hit = None
                for i in tree.query(pt):
                    kind, oid, P = owners[i]
                    if (kind, oid) != ("SPAN", sid) and P.contains(pt):
                        hit = f"{kind}:{oid}" if not oid.startswith(("COL:", "PIECE:", "ARC:")) else oid
                        break
                if hit is None:
                    pi = [panels[i]["panel_id"] for i in panel_tree.query(pt) if panels[i]["poly"].contains(pt)]
                    hit = f"PANEL:{pi[0]}" if pi else ("OUTER" if not solid.contains(pt) else "SMALL_HOLE")
                acc[hit] = acc.get(hit, 0.0) + L / nstep
            side_cover[f"{sid}|{side}"] = {k: r4(v / 1000.0) for k, v in sorted(acc.items())}

    rows = []
    for bd in boundaries:
        for (kind, oid, sub), L in sorted(bd.pop("acc").items(), key=lambda t: (t[0][0], t[0][1], str(t[0][2]))):
            row = {"boundary": bd["boundary"], "member_kind": kind, "member": oid, "face": sub, "length_m": r4(L / 1000.0)}
            if kind == "SPAN" and sub in ("A", "B"):
                row["face_line_handle"] = face_handle(span_meta[oid]["band"], sub)
                row["span_face_to_face_m"] = span_meta[oid]["L"]
            if kind == "ARC":
                v = arc_polys[oid]
                row["arc_handle"] = (v["outer"] if sub == "CONVEX" else v["inner"]).dxf.handle
            rows.append(row)
    data = {"source": {"drive": "Alsenan chalet project / ST7757 dxf.dxf", "structural_sha256": R.DXF_SHA,
                       "t242_panels_reproduced": len(panels), "step_mm": STEP_MM},
            "small_holes_m2": small_holes,
            "pieces": {k: {kk: vv for kk, vv in d.items() if kk != "poly"} for k, d in sorted(pieces.items())},
            "boundaries": boundaries, "faces": rows, "column_contacts": col_contacts, "span_side_cover": side_cover,
            "spans": {sid: {"band": m["band"], "face_to_face_m": m["L"]} for sid, m in sorted(span_meta.items())}}
    with open(os.path.join(a.out, "ALSENAN_FACE_TRACE.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    print(len(panels), "panels reproduced;", len(outers), "outer boundaries;", len(rows), "face rows;",
          "small holes", small_holes)
    for bd in boundaries:
        print(" ", bd)


if __name__ == "__main__":
    main()
