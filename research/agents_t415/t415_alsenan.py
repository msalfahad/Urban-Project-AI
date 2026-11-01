"""T-415 development villa (Alsenan is one sample): ST-02 round-stair curved flight RS-C concrete, read BY HANDLE.

Build (needs the PRIVATE structural DXF 'ST7757 dxf.dxf' from Drive folder 'Alsenan chalet project', decoded into
.work/private only, sha256 9f9d1179...):
    python3 -I research/agents_t415/t415_alsenan.py --dxf <ST7757 dxf.dxf> --write
asserts every layer / handle it relies on, builds the structural lane polygon of the curved flight and the transition
tread on ST p.4 (GF roof slab plan), splits it by the DRAWN riser lines, and writes summary_t415.json beside this file
(radii, angles, lengths, areas and m3 only: no coordinates, no drawing content, no freelancer row text).
Check (no private input):
    python3 -I research/agents_t415/t415_alsenan.py --check
recomputes the closed-form treads, the steps, the waist coefficients and the reconciliation from the committed summary
and prints REPRODUCED when every figure matches.

Freelancer side: his ST-02 row as cited on the board / T-398 (1.2 x 16.4 x 0.28 = 5.5104 m3); its row text stays in
the private workbook. Engine side: the merged T-258 r2 ledger values of RS-S / RS-A / RS-LD (cited, not re-derived).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t415_rules as R  # noqa: E402

SUMMARY = HERE / "summary_t415.json"
MM = 0.001
RISE = 4.50 / 28  # Q-50 A cond: plan count 28, 'reconstructed, no section' (ASSUMED — OWNER-APPROVED)
RISER_IDS = ["2EA", "2E9", "2E8", "2E7", "2E6", "2E5", "2E4", "2E3", "2E2", "2E1", "2E0", "2DF"]  # walking order
STRAIGHT_FIRST = "2BA"  # RS-S first riser line (T-258 RS-S: 11 lines 2BA .. 2C4)
# merged T-258 r2 ledger (research/agents_t258/LEDGER_T258.csv), m3, and their drawn plan areas (m2, from the same rows)
ENGINE = {
    "ST02-RS-S": dict(m3=0.942732, area=3.000 * 1.200, src="T-258 r2: 3.000 run x lane 1.200 (B3 face 283 -> 2D0)"),
    "ST02-RS-LD": dict(m3=0.216400, area=1.3525, src="T-258 r2: 1.150 x 1.200 - column 374 0.0275"),
    "ST02-RS-A": dict(m3=0.377093, area=1.200 * 1.200, src="T-258 r2: run 1.200 x lane 1.200 (2CF -> 289)"),
}
HIS = dict(w=1.2, l=16.4, t=0.28)  # board T-415 / T-398 (his ST-02 row, his own printed figures)
RS_S_T = 0.16  # 'T 16' block 5B6, printed inside the RS-S panel only (Q-47 A)


# ------------------------------------------------------------------------------------------- build (private input)

def build(dxf_path: str, inset_mm: float = 0.0) -> dict:
    """inset_mm > 0: the retired tread-line lane (lines 1.150 inset 0.050 from each opening edge), for comparison."""
    import ezdxf
    from shapely.geometry import LineString, Point, Polygon, box
    from shapely.ops import split, unary_union

    db = ezdxf.readfile(dxf_path).entitydb

    def ent(h, typ, layer):
        e = db[h]
        assert e.dxftype() == typ, (h, e.dxftype(), typ)
        assert e.dxf.layer == layer, (h, e.dxf.layer, layer)
        return e

    inner, outer = ent("2DE", "ARC", "S-OPENING"), ent("2DD", "ARC", "S-OPENING")
    c = (inner.dxf.center[0], inner.dxf.center[1])
    for h in ("2DD", "2DB", "2DC"):
        cc = db[h].dxf.center
        assert math.hypot(cc[0] - c[0], cc[1] - c[1]) < 1e-3, h
    r_in, r_out = inner.dxf.radius, outer.dxf.radius
    void_edge = ent("2D0", "LINE", "S-OPENING")  # straight-flight void edge, starts at the inner arc end
    b3 = ent("283", "LINE", "1")  # 'B3 (With Stair)' band face (stair side)
    s1 = ent("2BA", "LINE", "2")
    y_void, y_b3 = void_edge.dxf.start[1], b3.dxf.start[1]
    assert abs(void_edge.dxf.end[1] - y_void) < 1e-6 and abs(b3.dxf.end[1] - y_b3) < 1e-6
    x_s1 = s1.dxf.start[0]
    r_in, r_out, y_void = r_in + inset_mm, r_out - inset_mm, y_void - inset_mm
    assert abs(s1.dxf.end[0] - x_s1) < 1e-6
    # the inner arc ends where the void edge starts; the straight lane edges are the same radii seen at 270 deg
    p_end = inner.end_point
    assert inset_mm or math.hypot(p_end[0] - void_edge.dxf.end[0], p_end[1] - void_edge.dxf.end[1]) < 1e-3

    def pol(r, a):
        return (c[0] + r * math.cos(a), c[1] + r * math.sin(a))

    a0 = math.radians(min(inner.dxf.start_angle, outer.dxf.start_angle)) - 0.01
    n = 20000
    arc_out = [pol(r_out, a0 + (math.radians(270.0) - a0) * i / n) for i in range(n + 1)]
    arc_in = [pol(r_in, a0 + (math.radians(270.0) - a0) * i / n) for i in range(n + 1)]
    sector = Polygon(arc_out + arc_in[::-1])
    straight = box(c[0], y_b3, x_s1, y_void)
    # lane: annulus sector (both S-OPENING arcs) + the transition up to 2BA, clipped by the B3 band face (stair side)
    lane_raw = unary_union([sector, straight])
    lane = lane_raw.intersection(box(c[0] - 10 * r_out, y_b3, x_s1, c[1] + 10 * r_out))
    b3_clip = (lane_raw.area - lane.area) * MM * MM  # outer-arc strip beyond the B3 band face (beam side)
    # lane start edge: the line between the two arc start points (the flight's foot outline)
    st_in = inner.start_point
    st_out = outer.start_point
    foot_cut = LineString([(st_in[0] + (st_in[0] - st_out[0]) * 5, st_in[1] + (st_in[1] - st_out[1]) * 5),
                           (st_out[0] - (st_in[0] - st_out[0]) * 5, st_out[1] - (st_in[1] - st_out[1]) * 5)])
    pieces = split(lane, foot_cut)
    lane = max(pieces.geoms, key=lambda g: g.area)

    risers = {}
    for h in RISER_IDS:
        e = ent(h, "LINE", "2")
        p, q = e.dxf.start, e.dxf.end
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        # perpendicular distance of the riser line from the stair centre (radial offset)
        off = (p[0] - c[0]) * (-uy) + (p[1] - c[1]) * ux
        risers[h] = dict(p=(p[0], p[1]), u=(ux, uy), L=L * MM, off=off * MM,
                         r0=math.hypot(p[0] - c[0], p[1] - c[1]) * MM, r1=math.hypot(q[0] - c[0], q[1] - c[1]) * MM,
                         ang=math.degrees(math.atan2(p[1] - c[1], p[0] - c[0])) % 360)
        # radial base angle phi: the line is at angle phi + asin(off / r) at radius r (same off for every riser line,
        # so the angular step between two lines is the same at every radius)
        risers[h]["phi"] = (risers[h]["ang"] - math.degrees(math.asin(risers[h]["off"] / risers[h]["r0"]))) % 360

    def long_line(h, ext=10000.0):
        d = risers[h]
        p, (ux, uy) = d["p"], d["u"]
        return LineString([(p[0] - ux * ext, p[1] - uy * ext), (p[0] + ux * ext, p[1] + uy * ext)])

    cut_lines = [long_line(h) for h in RISER_IDS] + [LineString([(x_s1, y_b3 - 10), (x_s1, y_void + 10)])]
    regions = [lane]
    for cl in cut_lines:
        nxt = []
        for g in regions:
            nxt.extend(split(g, cl).geoms)
        regions = nxt

    # classify each region by the two riser lines that bound it (point-in-between test on the walking direction)
    def side(h, pt):
        d = risers[h]
        p, (ux, uy) = d["p"], d["u"]
        # walking direction is +angle (counter-clockwise); a point uphill of the line has positive cross with u
        return (pt[0] - p[0]) * uy - (pt[1] - p[1]) * ux

    seq = RISER_IDS + [STRAIGHT_FIRST]
    treads = []
    for g in regions:
        pt = g.representative_point().coords[0]
        if pt[0] >= x_s1 - 1e-6:
            raise AssertionError("region beyond 2BA inside the curved lane")
        ups = [side(h, pt) for h in RISER_IDS]
        # count lines that the point lies uphill of
        k = sum(1 for v in ups if v < 0)
        treads.append((k, g))
    # sanity: walking direction sign: the region nearest the foot must lie downhill of all lines (k = 0)
    ks = sorted(k for k, _ in treads)
    assert ks == list(range(0, 13)), ks

    def sec_alpha_k(k, x, y):
        """local going on the walking path through (x, y) for tread k (1 .. 12)."""
        r = math.hypot(x - c[0], y - c[1]) if x <= c[0] else (c[1] - y)
        if k <= 11:
            lo, hi = seq[k - 1], seq[k]
            dth = math.radians(risers[hi]["phi"] - risers[lo]["phi"])
            g = r * dth  # parallel-offset lines: the angular step is the same at every radius
        else:
            d = risers["2DF"]
            th = math.atan2(d["p"][1] - c[1], d["p"][0] - c[0]) % (2 * math.pi)
            th_r = th + math.asin(max(-1.0, min(1.0, d["off"] / (r * MM)))) - math.asin(d["off"] / d["r0"])
            g = r * (math.radians(270.0) - th_r) + (x_s1 - c[0])
        return math.sqrt(1.0 + (RISE / (g * MM)) ** 2)

    def k_numeric(k, g, step=1.5):
        minx, miny, maxx, maxy = g.bounds
        tot = 0.0
        y = miny + step / 2
        from shapely import contains_xy
        import numpy as np
        xs = np.arange(minx + step / 2, maxx, step)
        while y < maxy:
            ys = np.full_like(xs, y)
            inside = contains_xy(g, xs, ys)
            for x in xs[inside]:
                tot += sec_alpha_k(k, float(x), y)
            y += step
        return tot * (step * MM) ** 2

    # curtail at the foot: arcs 2EB / 2EC (layer 2) bulging into the well beyond the inner S-OPENING arc
    def arc_poly(h):
        e = ent(h, "ARC", "2")
        cc, rr = e.dxf.center, e.dxf.radius
        s, t = math.radians(e.dxf.start_angle), math.radians(e.dxf.end_angle)
        if t < s:
            t += 2 * math.pi
        pts = [(cc[0] + rr * math.cos(s + (t - s) * i / 4000), cc[1] + rr * math.sin(s + (t - s) * i / 4000))
               for i in range(4001)]
        return Polygon(pts), pts[0], pts[-1]

    well = Point(c).buffer(r_in, 4000)
    curtail = {}
    for h in ("2EB", "2EC"):
        P, a, b = arc_poly(h)
        ends = []
        for pt in (a, b):
            best = min(risers, key=lambda k_: math.hypot(pt[0] - risers[k_]["p"][0], pt[1] - risers[k_]["p"][1]))
            ends.append((best, round(math.hypot(pt[0] - risers[best]["p"][0], pt[1] - risers[best]["p"][1]) * MM, 4)))
        curtail[h] = dict(radius=round(db[h].dxf.radius * MM, 6), ends=ends,
                          area_beyond_lane_m2=round(P.intersection(well).area * MM * MM, 6),
                          min_r=round((math.hypot(db[h].dxf.center[0] - c[0], db[h].dxf.center[1] - c[1])
                                       - db[h].dxf.radius) * MM, 6))

    rows = []
    for k, g in sorted(treads, key=lambda t: t[0]):
        area = g.area * MM * MM
        if k == 0:
            rows.append(dict(k=0, lower="lane start", upper=seq[0], area=round(area, 6), piece="FOOT (floor +1.00)"))
            continue
        lo, hi = seq[k - 1], seq[k]
        dth = risers[hi]["phi"] - risers[lo]["phi"] if k <= 11 else None
        clipped = abs(area - (R.annular_area(r_in * MM, r_out * MM, math.radians(dth)) if dth else -1)) > 2e-5
        if k <= 11 and not clipped:
            kw = R.annular_waist_coefficient(r_in * MM, r_out * MM, math.radians(dth), RISE)
            method = "closed form"
        else:
            kw = k_numeric(k, g)
            method = "numeric 1.5 mm grid"
        rows.append(dict(k=k, lower=lo, upper=hi, dtheta_deg=round(dth, 6) if dth else None, area=round(area, 6),
                         k_waist=round(kw, 6), k_method=method, clipped_by_B3=bool(k <= 11 and clipped),
                         piece="RS-C" if k <= 11 else "RS-C transition (2DF -> 2BA)"))

    # numeric-integration self-check on an unclipped tread (closed form available): recorded, must be < 2e-4 m2
    t3 = next(g for k, g in treads if k == 3)
    d3 = math.radians(risers[seq[3]]["phi"] - risers[seq[2]]["phi"])
    k_err = abs(k_numeric(3, t3) - R.annular_waist_coefficient(r_in * MM, r_out * MM, d3, RISE))
    assert k_err < 2e-4, k_err
    # column census (S-COL.BON closed outlines) against the curved lane: R-CONC-OWN-1 column corollary
    cols = []
    for e in db.values():
        if e.dxftype() == "LWPOLYLINE" and e.dxf.get("layer") == "S-COL.BON" and e.closed:
            P = Polygon([p_[:2] for p_ in e.get_points()])
            if P.is_valid and P.distance(lane) < 1.0:
                cols.append(dict(handle=e.dxf.handle, overlap_m2=round(P.intersection(lane).area * MM * MM, 6)))
    dths = [risers[seq[i + 1]]["phi"] - risers[seq[i]]["phi"] for i in range(11)]
    out = dict(
        schema="T415_ALSENAN_RS_C",
        drawing="'ST7757 dxf.dxf' sha256 9f9d1179 (Drive 'Alsenan chalet project'), ST p.4 GF roof slab plan",
        lane=dict(r_in=round(r_in * MM, 6), r_out=round(r_out * MM, 6), width=round((r_out - r_in) * MM, 6),
                  src="S-OPENING arcs 2DE (inner) / 2DD (outer), concentric with the layer-5 pair 2DB / 2DC; "
                      "R-STAIR-LANE-1 (structural lane = opening edge to opening edge)",
                  straight_lane_outer_r=round((c[1] - y_b3) * MM, 6), straight_lane_inner_r=round((c[1] - y_void) * MM, 6),
                  outer_arc_end_deg=round(outer.dxf.end_angle, 3), inner_arc_end_deg=round(inner.dxf.end_angle, 3),
                  transition_straight_part=round((x_s1 - c[0]) * MM, 6)),
        risers=[dict(id=h, ang=round(risers[h]["ang"], 4), phi=round(risers[h]["phi"], 4), drawn_len=round(risers[h]["L"], 4),
                     radial_offset=round(risers[h]["off"], 4), r_from=round(risers[h]["r0"], 4),
                     r_to=round(risers[h]["r1"], 4)) for h in RISER_IDS],
        dtheta_deg=dict(min=round(min(dths), 6), max=round(max(dths), 6)),
        rise=RISE, rise_status="ASSUMED — OWNER-APPROVED (Q-50 A cond, plan count 28, no section)",
        treads=rows, curtail=curtail,
        columns_touching_lane=cols, b3_clip_m2=round(b3_clip, 6),
        lane_area=round(lane.area * MM * MM, 6), k_numeric_check_err_m2=round(k_err, 6), inset_mm=inset_mm,
    )
    return out


# ------------------------------------------------------------------------------------------- derive (no private input)

def derive(s: dict) -> dict:
    treads = [t for t in s["treads"] if t["k"] >= 1]
    fp = R.FlightPieces(rise=s["rise"], rise_status=s["rise_status"])
    for t in treads:
        fp.add(R.Tread(t["lower"], t["upper"], t["area"], t["k_waist"], "RS-C"))
    steps = fp.steps_m3()
    area = fp.area()
    kw = fp.k_waist()
    waist, wstat = R.waist_m3(kw, None, None, "ST02-RS-C")  # no thickness printed in the curved panel
    bound = R.curved_flight_bound(steps, reinforcement_printed=True)  # '8 d16/m' 5BC printed in the curved panel
    # scenario only (labelled; never a quantity): if the RS-S 'T 16' governed the curved flight too
    scen_t = RS_S_T
    scenario = dict(label="ILLUSTRATIVE SCENARIO, not a quantity: waist t = 0.16 (RS-S panel value, NOT printed for "
                          "RS-C)", waist=round(scen_t * kw, 6), total=round(steps + scen_t * kw, 6))
    pieces = [dict(id=k, area=v["area"], m3=v["m3"]) for k, v in ENGINE.items()]
    pieces.append(dict(id="ST02-RS-C (12 treads incl. transition)", area=area, m3=None))
    rec = R.decompose_plate_row(HIS["w"], HIS["l"], HIS["t"], pieces)
    lane_w = s["lane"]["width"]
    lengths = dict(
        curve_centreline_risers_1_12=round(sum(math.radians(t["dtheta_deg"]) for t in treads if t["dtheta_deg"])
                                           * (s["lane"]["r_in"] + s["lane"]["r_out"]) / 2, 6),
        whole_stair_plan_area=round(area + sum(v["area"] for v in ENGINE.values()), 6),
        his_area_over_drawn=round(rec["his_area"] / (area + sum(v["area"] for v in ENGINE.values())), 6),
    )
    # drawn candidates for his one length (his width 1.2): a candidate is TRACED only with evidence beyond the figure
    drawn_len = rec["drawn_area"] / HIS["w"]
    tread = treads[2]["area"]
    cands = {
        "whole drawn plan on his width": drawn_len,
        "whole drawn plan counted on two plans (GF + 1F)": 2 * drawn_len,
        "whole plan + the 9 lower treads again (also drawn on ST p.3)": drawn_len + 9 * tread / HIS["w"],
    }
    lengths["his_length_candidates"] = {k: round(v, 4) for k, v in cands.items()}
    lengths["his_length_traced"] = any(abs(v - HIS["l"]) <= 0.10 for v in cands.values())
    return dict(steps_m3=round(steps, 6), area_m2=round(area, 6), k_waist_m2=round(kw, 6), waist=waist,
                waist_status=wstat, bound=dict(kind=bound["kind"], low=round(bound["low"], 6), high=None),
                scenario=scenario, lane_w=lane_w, reconciliation=dict(
                    his_m3=round(rec["his_m3"], 6), his_area=round(rec["his_area"], 6),
                    drawn_area=round(rec["drawn_area"], 6), engine_valued=round(rec["engine_valued"], 6),
                    residual=round(rec["residual"], 6),
                    terms=[dict(t, m3=round(t["m3"], 6), **({"area": round(t["area"], 6)} if "area" in t else {}))
                           for t in rec["terms"]]), lengths=lengths)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.check:
        s = json.loads(SUMMARY.read_text(encoding="utf-8"))
        d = derive(s["geometry"])
        alt = derive(s["retired_tread_line_lane"]["geometry"])
        if (json.dumps(d, sort_keys=True) == json.dumps(s["derived"], sort_keys=True)
                and json.dumps(alt, sort_keys=True) == json.dumps(s["retired_tread_line_lane"]["derived"],
                                                                  sort_keys=True)):
            print("REPRODUCED")
            return 0
        print("DIFFERS")
        print(json.dumps(d, indent=1))
        return 1
    g = build(a.dxf)
    d = derive(g)
    g_alt = build(a.dxf, inset_mm=50.0)
    s = dict(geometry=g, derived=d, retired_tread_line_lane=dict(geometry=g_alt, derived=derive(g_alt)))
    txt = json.dumps(s, indent=1, ensure_ascii=False)
    if a.write:
        SUMMARY.write_text(txt + "\n", encoding="utf-8")
    print(json.dumps(d, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
