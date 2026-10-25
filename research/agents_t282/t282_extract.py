"""T-282 extraction (research only): each ground-beam span's two side faces traced on its OWN drawn edge lines to the
carrier face that edge meets, on the development villa's structural DXF. Values, ids and DXF handles only (no
coordinates, no client text).

    .work/venv/bin/python -I research/agents_t282/t282_extract.py <structural.dxf> [--out <dir>]

Input (Drive "Alsenan chalet project" / "ST7757 dxf.dxf", sha 9f9d1179 = T-141 DXF_SHA). The bands, arcs, columns,
footings and spans are built exactly as T-242 builds them (T-141 runner, GROUND_SYSTEM_SPANS_V2); the spans are
checked against the committed T-242 input (span ids, face stations, face-to-face lengths) before anything is written.

What is added per span (the physical question of T-282): V2 cuts a span square at ONE station per end (the outermost
station of the support's footprint across the band width). A side face is cast on one edge line; it ends where THAT
edge line meets the carrier named at that end:
  COLUMN          the column outline crossed by the edge line (offset within SNAP of the outline counts as on it)
  BEAM_JUNCTION   the carrier band strip (straight) or the curved band region between its two drawn arcs
  FOOTING_FACE / GAP_TO_COLUMN / FREE_END   no carrier face on the edge: the V2 station is kept (stated, HELD where
                  V2 holds the end)
An edge line the named carrier does not reach is reported NOT_REACHED (never closed square, never 0).
Also written: every column face parallel to a band edge within SLIVER_MM of it (a column 0.05 mm inside a band edge is
the column's face, not a beam face; SNAP_MM is the stated tolerance)."""
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

SNAP_MM = 1.0        # stated snap tolerance: an offset thinner than 1 mm between two outlines is not a member
SLIVER_MM = 5.0      # census window for near-coincident column faces / band edges (V2 contact tolerance)


def r4(v):
    return None if v is None else round(float(v), 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("structural")
    ap.add_argument("--out", default=HERE)
    a = ap.parse_args()
    import ezdxf
    from shapely.geometry import LineString, Point, Polygon, box

    if R.sha(a.structural) != R.DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    doc = ezdxf.readfile(a.structural)
    msp = doc.modelspace()
    GBP, FP = R.GBP, R.FP
    shift = FP[0] - GBP[0]

    lines = {e.dxf.handle: (tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2])
             for e in msp.query("LINE[layer=='1']") if R.inb(*tuple(e.dxf.start)[:2], GBP)}
    faces = [{"handle": h, "layer": "1", "p0": p0, "p1": p1} for h, (p0, p1) in lines.items()]
    res = R.GN.pair_straight(faces, width=300.0, tol=12.0, admitted_layers={"1"})
    bands = [{"band_id": "+".join(b["handles"]), "u": b["u"], "lo_off": b["lo_off"], "hi_off": b["hi_off"],
              "t0": b["t0"], "t1": b["t1"], "handles": b["handles"]} for b in res["bands"]]
    arcs = {e.dxf.handle: e for e in msp.query("ARC[layer=='1']") if R.inb(e.dxf.center[0], e.dxf.center[1], GBP)}
    arc_in = [{"handle": h, "layer": "1", "cx": e.dxf.center[0], "cy": e.dxf.center[1], "r": e.dxf.radius,
               "a0": e.dxf.start_angle, "a1": e.dxf.end_angle} for h, e in arcs.items()]
    ares = R.GN.pair_arcs(arc_in, width=300.0, tol=12.0, admitted_layers={"1"})
    arc_bands = {}
    for k, ab in enumerate(ares["bands"], start=1):
        bid = f"ARC:{'+'.join(ab['handles'])}/{k}"
        bands.append({"band_id": bid, "u": (1.0, 0.0), "lo_off": 0, "hi_off": 1, "t0": 0, "t1": 1,
                      "handles": ab["handles"], "kind": "ARC", "polygon": [tuple(p) for p in ab["polygon"]]})
        hs = ab["handles"]
        es = [arcs[h] for h in hs]
        c = es[0].dxf.center
        arc_bands[bid] = {"handles": hs, "cx": c[0], "cy": c[1],
                          "radii": {h: arcs[h].dxf.radius for h in hs},
                          "ranges": {h: (arcs[h].dxf.start_angle, arcs[h].dxf.end_angle) for h in hs}}
    cols = R.outlines(msp, "S-COL.BON", GBP)
    feet_fp = R.outlines(msp, "S-FOOTINGS", FP, blocks=("F",))
    feet_gb = [(i, [(x - shift, y) for x, y in p], h) for i, p, h in feet_fp]
    supports = [{"support_id": "COL:" + i, "kind": "COLUMN", "polygon": p, "handles": h} for i, p, h in cols] + \
               [{"support_id": "FTG:" + i, "kind": "FOOTING", "polygon": p, "handles": h} for i, p, h in feet_gb]
    out = R.V2.split_ground_beams(bands, supports, units="mm", classes=R.CLASSES)
    B = {b["band_id"]: b for b in bands if b.get("kind") != "ARC"}

    # ---- identity check against the committed T-242 input (same spans, same face stations)
    with open(os.path.join(ROOT, "research/agents_t242/ALSENAN_GROUND_INPUT.json"), encoding="utf-8") as fh:
        g242 = {s["span_id"]: s for s in json.load(fh)["spans"]}
    mine = {s["span_id"]: s for s in out["spans"]}
    if set(mine) != set(g242):
        raise SystemExit("span set differs from T-242: %s" % sorted(set(mine) ^ set(g242)))
    for sid, s in mine.items():
        if abs(s["lengths"]["face_to_face_m"] - g242[sid]["face_to_face_m"]) > 1e-4:
            raise SystemExit("span %s face to face differs from T-242" % sid)

    col_poly = {"COL:" + i: Polygon(p).buffer(0) for i, p, _ in cols}
    ftg_poly = {"FTG:" + i: Polygon(p).buffer(0) for i, p, _ in feet_gb}
    arc_poly = {b["band_id"]: Polygon(b["polygon"]).buffer(0) for b in bands if b.get("kind") == "ARC"}

    def strip(b):
        """a carrier band as DRAWN: the region between its own two edge lines over each line's own extent (a band
        whose edges end at different stations is not cut square at either; the paired overlap t0 .. t1 would be)."""
        from shapely.geometry import MultiPoint
        pts = [p for h in b["handles"] for p in lines[h]]
        return MultiPoint(pts).convex_hull
    strip_poly = {bid: strip(b) for bid, b in B.items()}

    def dot(p, v):
        return p[0] * v[0] + p[1] * v[1]

    def edge_handle(b, off):
        """the drawn LINE of band b that lies on offset `off` (its station range)."""
        u = b["u"]
        n = (-u[1], u[0])
        best = None
        for h in b["handles"]:
            p0, p1 = lines[h]
            o = (dot(p0, n) + dot(p1, n)) / 2.0
            if best is None or abs(o - off) < abs(best[1] - off):
                best = (h, o, sorted((dot(p0, u), dot(p1, u))))
        return best

    def carrier_geoms(kind, refs):
        gs = []
        for r in refs:
            if r.startswith("COL:"):
                gs.append(("COLUMN", r, col_poly[r]))
            elif r.startswith("FTG:"):
                gs.append(("FOOTING", r, ftg_poly[r]))
            elif r.startswith("ARC:"):
                gs.append(("ARC_BAND", r, arc_poly[r]))
            elif r in strip_poly:
                gs.append(("BAND", r, strip_poly[r]))
            else:
                raise SystemExit("unknown carrier ref %s" % r)
        return gs

    def local(b, G):
        """G in the band's own (station t, offset o) frame: the edge lines are exactly o = lo / o = hi there, so a
        face drawn 0.04 mm off a band edge stays parallel to it (a world-frame line 20 m long would cross it)."""
        u = b["u"]
        n = (-u[1], u[0])
        return Polygon([(dot(p, u), dot(p, n)) for p in G.exterior.coords]).buffer(0)

    def hit(b, off, t_from, sign, geoms):
        """station where the edge line o = off, walked from t_from in direction sign, first meets a carrier outline,
        read on the strip off +- SNAP_MM (a sub-mm drafting offset between two outlines is not a member: a column face
        0.05 mm off the band edge is on it; a face drawn a hair out of parallel is not read as a crossing). On a face
        oblique to the edge the strip moves the station by at most SNAP_MM / tan(angle). -> (station, ref, how)."""
        far = 30000.0
        lo_t, hi_t = sorted((t_from, t_from + sign * far))
        S = box(lo_t, off - SNAP_MM, hi_t, off + SNAP_MM)
        best = None
        for kind, ref, G in geoms:
            X = S.intersection(local(b, G))
            if X.is_empty or X.area <= 0:
                continue
            ts = [c[0] for geom in getattr(X, "geoms", [X]) if geom.geom_type == "Polygon"
                  for c in geom.exterior.coords]
            t = min(ts) if sign == 1 else max(ts)
            if best is None or (t - best[0]) * sign < -1e-6:
                best = (t, ref, kind)
        return best

    every = [("COLUMN", k, v) for k, v in col_poly.items()] + [("BAND", k, v) for k, v in strip_poly.items()] + \
        [("ARC_BAND", k, v) for k, v in arc_poly.items()] + [("FOOTING", k, v) for k, v in ftg_poly.items()]

    def at_drawn_end(b, off, t_end, own):
        """what element the drawn edge line's own end point touches (within SNAP_MM), other than its own band."""
        pt = Point(t_end, off)
        return sorted(ref for kind, ref, G in every if ref != own and local(b, G).distance(pt) <= SNAP_MM)

    rows = []
    for s in out["spans"]:
        b = B[s["band_id"]]
        lo, hi = sorted((b["lo_off"], b["hi_off"]))
        ta = s["start"]["face_station_m"] * 1000.0
        tb = s["end"]["face_station_m"] * 1000.0
        tm = (ta + tb) / 2.0
        edges = {}
        for side, off in (("A", lo), ("B", hi)):
            h, o_line, (l0, l1) = edge_handle(b, off)
            ends = {}
            for end, t_sq, sign in (("start", ta, -1), ("end", tb, 1)):
                kind = s[end]["kind"]
                refs = s[end]["refs"]
                if kind in ("COLUMN", "BEAM_JUNCTION"):
                    hh = hit(b, off, tm, sign, carrier_geoms(kind, refs))
                    if hh is None:
                        t_dr = l0 if sign == -1 else l1
                        ends[end] = {"status": "NOT_REACHED", "station_m": None, "square_m": r4((t_sq - b["t0"]) / 1000.0),
                                     "carrier": "+".join(refs), "how": "the named carrier does not reach this edge",
                                     "drawn_end_m": r4((t_dr - b["t0"]) / 1000.0),
                                     "drawn_end_touches": at_drawn_end(b, off, t_dr, s["band_id"])}
                    else:
                        t_dr = l0 if sign == -1 else l1
                        ends[end] = {"status": "CARRIER_FACE", "station_m": r4((hh[0] - b["t0"]) / 1000.0),
                                     "square_m": r4((t_sq - b["t0"]) / 1000.0), "carrier": hh[1], "how": hh[2],
                                     "beyond_square_m": r4(sign * (hh[0] - t_sq) / 1000.0),
                                     "drawn_end_m": r4((t_dr - b["t0"]) / 1000.0),
                                     "drawn_minus_face_mm": round(sign * (t_dr - hh[0]), 1)}
                else:
                    ends[end] = {"status": "V2_STATION_" + kind, "station_m": r4((t_sq - b["t0"]) / 1000.0),
                                 "square_m": r4((t_sq - b["t0"]) / 1000.0), "carrier": "+".join(refs), "how": kind,
                                 "beyond_square_m": 0.0}
            st, en = ends["start"]["station_m"], ends["end"]["station_m"]
            L = None if st is None or en is None else r4((en - st))
            edges[side] = {"edge_handle": h, "offset_dev_mm": r4(o_line - off), "drawn_line_m": r4((l1 - l0) / 1000.0),
                           "drawn_from_m": r4((l0 - b["t0"]) / 1000.0), "drawn_to_m": r4((l1 - b["t0"]) / 1000.0),
                           "ends": ends, "length_m": L}
        rows.append({"span_id": s["span_id"], "band_id": s["band_id"], "width_m": s["width_m"],
                     "face_to_face_m": s["lengths"]["face_to_face_m"],
                     "start": {"kind": s["start"]["kind"], "refs": s["start"]["refs"]},
                     "end": {"kind": s["end"]["kind"], "refs": s["end"]["refs"]},
                     "edges": edges})

    # ---- arc carriers: the arc length a framing band's two edge lines cut out of the carrier arc it frames into
    framing = []
    for r in rows:
        for end in ("start", "end"):
            ref = [x for x in r[end]["refs"] if x.startswith("ARC:")]
            if not ref:
                continue
            ab = arc_bands[ref[0]]
            angs = {}
            for side in ("A", "B"):
                e = r["edges"][side]["ends"][end]
                b = B[r["band_id"]]
                u = b["u"]
                n = (-u[1], u[0])
                off = sorted((b["lo_off"], b["hi_off"]))[0 if side == "A" else 1]
                t = e["station_m"] * 1000.0 + b["t0"]
                x, y = t * u[0] + off * n[0], t * u[1] + off * n[1]
                rr = math.hypot(x - ab["cx"], y - ab["cy"])
                angs[side] = (math.degrees(math.atan2(y - ab["cy"], x - ab["cx"])) % 360.0, rr)
            # the carrier arc whose radius the two hit points lie on
            hcar = min(ab["radii"], key=lambda h: abs(ab["radii"][h] - sum(v[1] for v in angs.values()) / 2.0))
            Rm = ab["radii"][hcar]
            d = abs(angs["A"][0] - angs["B"][0])
            d = min(d, 360.0 - d)
            framing.append({"span_id": r["span_id"], "end": end, "carrier": ref[0], "carrier_arc": hcar,
                            "R_m": r4(Rm / 1000.0), "r_hit_A_m": r4(angs["A"][1] / 1000.0),
                            "r_hit_B_m": r4(angs["B"][1] / 1000.0), "deg_A": round(angs["A"][0], 3),
                            "deg_B": round(angs["B"][0], 3), "arc_between_m": r4(Rm * math.radians(d) / 1000.0),
                            "chord_between_m": r4(2 * Rm * math.sin(math.radians(d) / 2) / 1000.0)})

    # ---- sliver census: column faces parallel to a band edge within SLIVER_MM, over the band's drawn range
    slivers = []
    for bid, b in B.items():
        u = b["u"]
        n = (-u[1], u[0])
        lo, hi = sorted((b["lo_off"], b["hi_off"]))
        for cid, P in col_poly.items():
            cs = list(local(b, P).exterior.coords)
            for (t0_, o0_), (t1_, o1_) in zip(cs, cs[1:]):
                if abs(t1_ - t0_) < 50.0 or abs(o1_ - o0_) > 1e-3 * abs(t1_ - t0_):
                    continue                             # only column faces parallel to the band
                oc = (o0_ + o1_) / 2.0
                s0, s1 = sorted((t0_, t1_))
                ov = min(s1, b["t1"]) - max(s0, b["t0"])
                if ov <= 1.0:
                    continue
                for side, off in (("A", lo), ("B", hi)):
                    dmm = oc - off
                    if 1e-3 <= abs(dmm) <= SLIVER_MM:   # below 1 micron: the same line (coincident faces)
                        slivers.append({"band_id": bid, "side": side, "column": cid, "offset_mm": round(dmm, 3),
                                        "column_face_inside_band": bool(lo < oc < hi), "along_m": r4(ov / 1000.0),
                                        "below_snap": abs(dmm) < SNAP_MM})
    slivers.sort(key=lambda d: (d["band_id"], d["column"], d["side"]))

    # ---- METHOD T (traced faces, face_trace.trace): the boundary of the union of every drawn ground-beam member
    # (straight bands between their own edge lines, each edge closed on its named carrier; curved bands between their
    # own arcs), the columns and the lift ring, each boundary piece given to one owner (R-FACE-OWN-1, R-FACE-SNAP-1).
    sys.path.insert(0, HERE)
    fspec = importlib.util.spec_from_file_location("t282_face_trace", os.path.join(HERE, "face_trace.py"))
    FT = importlib.util.module_from_spec(fspec)
    fspec.loader.exec_module(FT)
    ring_polys = []
    for e in msp.query("LWPOLYLINE[layer=='S-BW']"):
        pts = [tuple(p[:2]) for p in e.get_points()]
        if R.inb(*pts[0], GBP):
            ring_polys.append((e.dxf.handle, Polygon(pts).buffer(0)))
    lift = max(ring_polys, key=lambda t: t[1].area)
    members = {}
    by_band = {}
    for s_ in out["spans"]:
        by_band.setdefault(s_["band_id"], []).append(s_)
    for bid, sps in by_band.items():
        b = B[bid]
        u = b["u"]
        n = (-u[1], u[0])
        lo, hi = sorted((b["lo_off"], b["hi_off"]))
        edges = {}
        for side, off in (("A", lo), ("B", hi)):
            ts = []
            for h in b["handles"]:
                p0, p1 = lines[h]
                if abs((dot(p0, n) + dot(p1, n)) / 2.0 - off) < 12.0:
                    ts += [dot(p0, u), dot(p1, u)]
            t0, t1 = min(ts), max(ts)
            edges[side] = ((t0 * u[0] + off * n[0], t0 * u[1] + off * n[1]), (t1 * u[0] + off * n[0], t1 * u[1] + off * n[1]))
        sps = sorted(sps, key=lambda z: z["start"]["face_station_m"])
        members[bid] = {"edges": edges, "width": hi - lo,
                        "spans": [(z["start"]["face_station_m"], z["end"]["face_station_m"], z["span_id"]) for z in sps],
                        "ends": {"start": {"kind": sps[0]["start"]["kind"], "carriers": sps[0]["start"]["refs"]},
                                 "end": {"kind": sps[-1]["end"]["kind"], "carriers": sps[-1]["end"]["refs"]}}}
    arcs_in = {bid: {"cx": ab["cx"], "cy": ab["cy"], "radii": ab["radii"], "ranges": ab["ranges"]}
               for bid, ab in arc_bands.items()}
    T = FT.trace(members, {k: list(v.exterior.coords) for k, v in col_poly.items()}, arcs_in,
                 {"LIFT:" + lift[0]: list(lift[1].exterior.coords)})
    traced_doc = {
        "sides": [{"span_id": k[0], "side": k[1], "length_m": v} for k, v in sorted(T["sides"].items())],
        "ends": [{"span_id": k[0], "end_kind": k[1], "length_m": v} for k, v in sorted(T["ends"].items())],
        "end_artefacts_m": T.get("end_artefacts_m", []),
        "columns": [{"column": k, "length_m": v} for k, v in sorted(T["columns"].items())],
        "others": [{"owner": k, "length_m": v} for k, v in sorted(T["others"].items())],
        "arcs": [{"arc_band": k[0], "arc": k[1], "R_m": r4(arcs_in[k[0]]["radii"][k[1]] / 1000.0), "length_m": v,
                  "deg_pieces": T["arc_pieces"][k]} for k, v in sorted(T["arcs"].items())],
        "closed_on_carrier": T["closed"], "held": T["held"], "gaps": T["gaps"],
        "pieces_beyond": [pc for pc in T["pieces"] if pc["where"] != "IN_SPAN" and pc["m"] > 0],
        "unattributed": T["unattributed"],
        "extended_between_edge_ends": T["extended"],
        "boundary_total_m": r4(sum(T["sides"].values()) + sum(T["ends"].values()) + sum(T["columns"].values()) +
                               sum(T["others"].values()) + sum(T["arcs"].values()) + sum(T["unattributed"]))}
    for pc in traced_doc["pieces_beyond"]:
        pc.pop("f0", None)
        pc.pop("f1", None)
    unattributed = T["unattributed"]
    os.makedirs(a.out, exist_ok=True)
    doc_out = {"schema": "T282_EDGE_INPUT", "source": {"drive": "Alsenan chalet project / ST7757 dxf.dxf",
                                                       "structural_sha256": R.DXF_SHA},
               "snap_mm": SNAP_MM, "sliver_window_mm": SLIVER_MM, "spans": rows, "arc_framing": framing,
               "slivers": slivers, "traced": traced_doc}
    with open(os.path.join(a.out, "ALSENAN_EDGE_INPUT.json"), "w", encoding="utf-8") as fh:
        json.dump(doc_out, fh, indent=1, sort_keys=True)
    print("spans %d, arc framings %d, slivers %d, traced boundary %.4f m, unattributed %d" % (
        len(rows), len(framing), len(slivers), traced_doc["boundary_total_m"], len(unattributed)))


if __name__ == "__main__":
    main()
