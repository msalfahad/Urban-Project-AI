"""T-625 DRAWING READ (research, unwired): the GF round-stair footprint below the cut (row 0 of the T-621 floor tile
rows) and the boundary of the two open-plan floors GF-OPEN.full and 1F-LIV.floor_printed / floor_drawn, read by HANDLE on
the architectural DXF (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip -> P7757.dxf) with the structural DXF
(Drive "Alsenan chalet project" / "ST7757 dxf.dxf") as the second drawing, both decoded into .work/private only.
Writes T625_DRAWN.json: handles, layer classes, lengths, radii, angles swept and areas only (no coordinate, no drawing
text other than level marks, no client name). The builder t625_alsenan.py reads only that JSON.

    .work/venv/bin/python -I research/agents_t625/t625_extract.py --dxf <P7757.dxf> --st <ST7757 dxf.dxf> --write
    .work/venv/bin/python -I research/agents_t625/t625_extract.py --dxf <P7757.dxf> --st <ST7757 dxf.dxf>   (re-read)

Outline chains are the merged T-606 / T-612 chains (read only); everything else (segments, gaps, evidence, exact area,
printed checks, levels, footprint) is this run's own reading under R-T625-1.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
for _p in ("agents_t621", "agents_t606", "agents_t612"):
    sys.path.insert(0, str(ROOT / "research" / _p))
import t606_extract as X6  # noqa: E402  (storeys, chains; read only)
import t606_rules as R6  # noqa: E402  (vertex helpers + flattened outline = area route 2; read only)
import t612_extract as X12  # noqa: E402  (GF open-room chain; read only)
import t612_rules as R12  # noqa: E402  (gross outline route; read only)
import t621_extract as X21  # noqa: E402  (segment table; read only)
import t625_rules as R  # noqa: E402

OUT = HERE / "T625_DRAWN.json"
WALL_LAYERS = ("1", "W", "S-COL.BON")
DOOR_BLOCK = re.compile(r"^[Dd]\d{3}$")
# every non-wall line that lies on an outline edge, with its printed role (R-T625-1 (1)); an unnamed one is an error
PRINTED_ROLE = {"2DC": "MOUTH", "22B": "LIFT_SILL", "B9B": "LIFT_SILL", "AC0": "NOSING", "AC4": "NOSING",
                "ABE": "NOSING", "A8F": "VOID_EDGE", "B74": "VOID_EDGE", "B75": "VOID_EDGE", "AF5": "VOID_EDGE",
                "D24": "RISER"}
# undrawn gaps closed on a printed dimension: (outline, edge) -> dimension handle, corroborating ST line
DIM_GAPS = {("1F-LIV.floor_printed", "AC0"): ("10DF", "459"), ("1F-LIV.floor_drawn", "AC0"): ("10DF", "459")}
CHAINS = {
    "GF-OPEN.full": ("GF", "T612", X12.OUTLINES["GF-OPEN.full"][2]),
    "1F-LIV.floor_printed": ("1F", "T606", X6.OUTLINES["1F-LIV.floor_printed"][2]),
    "1F-LIV.floor_drawn": ("1F", "T606", X6.OUTLINES["1F-LIV.floor_drawn"][2]),
}
# printed checks of edge lengths: outline -> edge -> [(sign, DIMENSION handle)]
DIM_CHECKS = {
    "GF-OPEN.full": {"B5": [(1, "4E9")], "E0": [(1, "939")], "AE": [(1, "5E1")], "158": [(1, "5D5")],
                     "104": [(1, "5F9"), (1, "5D5")], "AB": [(1, "6AD"), (-1, "5E1")],
                     "222": [(1, "5ED"), (-1, "6AD")]},
    "1F-LIV.floor_printed": {"AEC": [(1, "105A")], "B68": [(1, "DE9")], "AFE": [(1, "1071"), (1, "DAA")],
                             "B16": [(1, "10DF"), (-1, "1042")], "AC0": [(1, "D25")], "C21": [(1, "10DF")],
                             "AEB": [(1, "FF1"), (1, "E56")], "AF7": [(1, "EC5"), (-1, "1042")],
                             "B74": [(1, "F34")]},
}
# the GF round stair ST-02 (row 0): tread band arcs, nosings (first .. last), straight run edges, cut, column
STAIR = {"inner_arc": "239", "outer_arc": "23D", "first_nosing": "256",
         "nosings": ["256", "254", "252", "250", "24E", "24C", "24A", "248", "246", "244", "242", "240"],
         "run_inner": "22E", "run_outer": "A7", "first_run_nosing": "22F", "cut": "13C", "column": "2FD2",
         "inner_string_arc": "23F", "run_inner_string": "22C", "outer_string_arc": "23E", "curb_line": "A8",
         "curtail_arc": "258", "dim_band_width": "955", "dim_first_step": "963"}
# 1F: landing nosing band at the top of the arriving round-stair flight (riser D24 L2, nosing D22 L5)
ARRIVAL_BAND = {"riser": "D24", "nosing": "D22"}
ST_FRAME = {"arch": ["2FE7", "3008"], "st": ["332", "374"]}       # column pair framing ST on the 1F plan (T-269)
ST_LINES = {"459": "east-lane top riser of ST-01 (12th)", "315": "top riser of the round-stair flight RS-A"}
SLAB_EDGE = {"st_north": "2D2", "st_east": "2CF", "arch_north": "B74", "arch_east": "B75", "arch_band_top": "D24"}


def _layers(msp):
    lay = {}
    for e in msp:
        if e.dxf.is_supported("layer"):
            lay[e.dxf.handle] = e.dxf.layer
    return lay


def _proj(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L, abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / L


def _verts(chain, geom):
    n, out = len(chain), []
    for i in range(n):
        ta, ga = geom[chain[i - 1][0]]
        tb, gb = geom[chain[i][0]]
        if ta == "LINE" and tb == "LINE":
            out.append(R6._line_line(ga, gb))
        elif ta == "LINE":
            out.append(R6._line_circle(ga, gb[0], gb[1]))
        else:
            out.append(R6._line_circle(gb, ga[0], ga[1]))
    return out


def _bb(doc, h):
    p = [q[:2] for q in doc.entitydb[h].get_points()]
    return min(x for x, _ in p), min(y for _, y in p)


def _edges(name, s, chain, geom, lines, lay, inserts, doc, st_doc, shift):
    verts = _verts(chain, geom)
    n, res, green = len(chain), [], []
    for i, (h, role) in enumerate(chain):
        p, q = verts[i], verts[(i + 1) % n]
        t, g = geom[h]
        if t == "ARC":
            c, r, s0, s1 = g
            green.append(("ARC", p, q, c, r, s0, s1))
            sw = R.arc_sweep(c, p, q, s0, s1)
            res.append({"handle": h, "role": role, "length": str(R.q6(abs(sw) * r / 1000)),
                        "segments": [{"length": str(R.q6(abs(sw) * r / 1000)), "drawn_by": [(h, "WALL")]}],
                        "kind": "ARC"})
            continue
        green.append(("LINE", p, q))
        L = math.dist(p, q)
        cov = []
        for hh, gg in lines:
            u1, d1 = _proj(gg[0], p, q)
            u2, d2 = _proj(gg[1], p, q)
            if d1 < R.LINE_TOL and d2 < R.LINE_TOL:
                lo, hi = max(0.0, min(u1, u2)), min(L, max(u1, u2))
                if hi - lo > R.LINE_TOL:
                    ly = lay.get(hh.split("#")[0], "?")
                    if ly in WALL_LAYERS:
                        cls = "WALL"
                    elif hh in PRINTED_ROLE:
                        cls = "PRINTED:" + PRINTED_ROLE[hh]
                    else:
                        raise R.RuleError(f"{name} {h}: printed line {hh} (layer {ly}) on the edge has no role")
                    cov.append((lo, hi, hh, cls))
        cov.sort()
        # sweep: cut the edge at every coverage end; each piece is drawn by the lines covering it, or a gap
        cuts = sorted({0.0, L} | {x for lo, hi, _, _ in cov for x in (lo, hi)})
        segs = []
        for a, b in zip(cuts, cuts[1:]):
            if b - a <= R.LINE_TOL / 2:
                continue
            by = [(hh, cls) for lo, hi, hh, cls in cov if lo <= a + 1e-6 and hi >= b - 1e-6]
            # a wall face governs where wall and printed lines coincide
            if any(c == "WALL" for _, c in by):
                by = [(hh, c) for hh, c in by if c == "WALL"]
            if by:
                if segs and segs[-1].get("drawn_by") and {c for _, c in segs[-1]["drawn_by"]} == {c for _, c in by}:
                    segs[-1]["length_mm"] += b - a
                    segs[-1]["drawn_by"] = sorted(set(segs[-1]["drawn_by"]) | set(by))
                else:
                    segs.append({"length_mm": b - a, "drawn_by": sorted(set(by))})
                continue
            mid = (p[0] + (q[0] - p[0]) * (a + b) / 2 / L, p[1] + (q[1] - p[1]) * (a + b) / 2 / L)
            ev = _gap_evidence(name, h, (a, b), mid, p, q, inserts, doc, st_doc, shift)
            segs.extend(ev)
        for sg in segs:
            sg["length"] = str(R.q6(sg.pop("length_mm") / 1000))
        # exact re-add: the last segment absorbs the q6 rounding of the others (reported)
        res.append({"handle": h, "role": role, "length": str(R.q6(L / 1000)), "segments": segs, "kind": "LINE"})
    return res, green


def _gap_evidence(name, h, ab, mid, p, q, inserts, doc, st_doc, shift):
    a, b = ab
    w = b - a
    doors = [(hd, nm) for hd, nm, ip in inserts if DOOR_BLOCK.match(nm) and math.dist(mid, ip) <= w / 2 + 600]
    if doors:
        hd, nm = min(doors, key=lambda d: math.dist(mid, [ip for x, _, ip in inserts if x == d[0]][0]))
        return [{"length_mm": w, "evidence": {"door": hd, "block": nm}}]
    key = (name, h)
    if key in DIM_GAPS:
        dh, sth = DIM_GAPS[key]
        dim = doc.entitydb[dh]
        ends = [(dim.dxf.defpoint2.x, dim.dxf.defpoint2.y), (dim.dxf.defpoint3.x, dim.dxf.defpoint3.y)]
        on = min(_proj(e, p, q)[1] for e in ends) < R.LINE_TOL
        corr_len = 0.0
        if st_doc is not None:
            ln = st_doc.entitydb[sth]
            sa = (ln.dxf.start.x - shift[0], ln.dxf.start.y - shift[1])
            sb = (ln.dxf.end.x - shift[0], ln.dxf.end.y - shift[1])
            u1, d1 = _proj(sa, p, q)
            u2, d2 = _proj(sb, p, q)
            if d1 < R.LINE_TOL and d2 < R.LINE_TOL:
                corr_len = max(0.0, min(b, max(u1, u2)) - max(a, min(u1, u2)))
        out = []
        if corr_len > R.LINE_TOL:
            out.append({"length_mm": corr_len, "evidence": {"dimension": dh, "on_line": on,
                                                            "corroboration": ["ST7757:" + sth]}})
        if w - corr_len > R.LINE_TOL / 2:
            out.append({"length_mm": w - corr_len, "evidence": {"dimension": dh, "on_line": on,
                                                                "corroboration": []}})
        return out
    return [{"length_mm": w, "evidence": {"kind": "NONE"}}]


def _levels(msp, poly, a0, b0):
    from shapely.geometry import Point
    out = []
    texts = [(t.dxf.text, (t.dxf.insert.x, t.dxf.insert.y)) for t in msp.query("TEXT")
             if re.match(r"^[+-]\d+\.\d\d$", t.dxf.text or "")]
    for e in msp.query("INSERT"):
        ip = (e.dxf.insert.x, e.dxf.insert.y)
        if e.dxf.name == "LE" and a0 < ip[0] < b0 and poly.contains(Point(ip)):
            near = sorted(texts, key=lambda t: math.dist(t[1], ip))
            if near and math.dist(near[0][1], ip) < 900:
                out.append({"mark": e.dxf.handle, "level": near[0][0]})
    return out


def _dim_check(doc, edges, checks):
    out = {}
    lens = {e["handle"]: e["length"] for e in edges}
    for h, terms in (checks or {}).items():
        v = sum(sg * doc.entitydb[d].get_measurement() / 1000 for sg, d in terms)
        out[h] = {"printed": str(R.q6(v)), "dims": [f"{'+' if sg > 0 else '-'}{d}" for sg, d in terms],
                  "edge": lens[h], "diff": str(R.q6(float(lens[h]) - v))}
    return out


def _stair(doc, lay):
    from shapely.geometry import Polygon
    db = doc.entitydb
    S = STAIR
    ai, ao = db[S["inner_arc"]], db[S["outer_arc"]]
    c = (ai.dxf.center.x, ai.dxf.center.y)
    for h in (S["outer_arc"], S["inner_string_arc"], S["outer_string_arc"]):
        cc = db[h].dxf.center
        if math.dist((cc.x, cc.y), c) > R.LINE_TOL:
            raise R.RuleError(f"arc {h} is not concentric with {S['inner_arc']}")
    ang = lambda p: math.degrees(math.atan2(p[1] - c[1], p[0] - c[0])) % 360.0  # noqa: E731
    ln = lambda h: ((db[h].dxf.start.x, db[h].dxf.start.y), (db[h].dxf.end.x, db[h].dxf.end.y))  # noqa: E731
    r0, r1 = ai.dxf.radius, ao.dxf.radius
    t0 = ang(ln(S["first_nosing"])[0])
    t1 = ai.dxf.end_angle
    if abs(ang(ln(S["first_nosing"])[1]) - t0) > 1e-6:
        raise R.RuleError("the first nosing is not radial")
    if abs(ao.dxf.end_angle - t1) > 1e-6 or abs(ai.dxf.start_angle - t0) > 1e-6:
        raise R.RuleError("inner / outer tread arcs do not share the flight's ends")
    sweep = (t1 - t0) % 360.0
    band_f1 = R.sector_band(r0, r1, sweep)
    noses = [ang(ln(h)[0]) for h in S["nosings"]] + [t1]
    steps = [round(b - a, 4) for a, b in zip(noses, noses[1:])]
    chord_f1 = R.chord_band(r0, r1, noses)
    rad = lambda r, t: (c[0] + r * math.cos(math.radians(t)), c[1] + r * math.sin(math.radians(t)))  # noqa: E731
    pi_, po = rad(r0, t1), rad(r1, t1)
    yi, yo, xc = ln(S["run_inner"])[0][1], ln(S["run_outer"])[0][1], ln(S["cut"])[0][0]
    run = Polygon([pi_, (xc, yi), (xc, yo), po])
    col = Polygon([p[:2] for p in db[S["column"]].get_points()])
    run_net = run.difference(col)
    x22f = ln(S["first_run_nosing"])[0][0]
    strip = Polygon([pi_, (x22f, yi), (x22f, yo), po])
    # beside pieces
    n = 4000
    def sector(ra, rb, ta, tb):
        ts = [math.radians(ta + (tb - ta) * k / n) for k in range(n + 1)]
        return Polygon([(c[0] + rb * math.cos(t), c[1] + rb * math.sin(t)) for t in ts] +
                       [(c[0] + ra * math.cos(t), c[1] + ra * math.sin(t)) for t in reversed(ts)])
    rs_in, rs_out = db[S["inner_string_arc"]].dxf.radius, db[S["outer_string_arc"]].dxf.radius
    inner_string = R.sector_band(rs_in, r0, sweep)
    y_str = ln(S["run_inner_string"])[0][1]
    run_string = abs(y_str - yi) * abs(xc - ln(S["run_inner_string"])[0][0]) / 1e6
    outer_string = sector(r1, rs_out, t0, t1)
    y_curb = ln(S["curb_line"])[0][1]
    from shapely.geometry import box
    face_side = box(c[0] - 1e5, y_curb, c[0] + 1e5, c[1] + 1e5)
    outer_in_face = outer_string.intersection(face_side).area / 1e6
    ca = db[S["curtail_arc"]]
    cs, ce = ca.dxf.start_angle, ca.dxf.end_angle
    ce = ce + 360 if ce < cs else ce
    cpts = [(ca.dxf.center.x + ca.dxf.radius * math.cos(math.radians(cs + (ce - cs) * k / n)),
             ca.dxf.center.y + ca.dxf.radius * math.sin(math.radians(cs + (ce - cs) * k / n))) for k in range(n + 1)]
    e0, e1 = ang(cpts[0]), ang(cpts[-1])
    if abs(math.dist(cpts[0], c) - r0) > R.LINE_TOL or abs(math.dist(cpts[-1], c) - r0) > R.LINE_TOL:
        raise R.RuleError("the curtail does not start and end on the inner tread arc")
    lo, hi = min(e0, e1), max(e0, e1)
    back = [rad(r0, lo + (hi - lo) * k / n) for k in range(n + 1)]
    if math.dist(back[0], cpts[-1]) > math.dist(back[-1], cpts[-1]):
        back = back[::-1]
    back = back if math.dist(back[0], cpts[-1]) < R.LINE_TOL else back[::-1]
    curtail = Polygon(cpts + back[1:-1])
    # printed checks
    d955 = db[S["dim_band_width"]].get_measurement() / 1000
    d963 = db[S["dim_first_step"]]
    p2, p3 = (d963.dxf.defpoint2.x, d963.dxf.defpoint2.y), (d963.dxf.defpoint3.x, d963.dxf.defpoint3.y)
    cc = (ca.dxf.center.x, ca.dxf.center.y)
    on_256 = min(math.dist(p, ln(S["first_nosing"])[1]) for p in (p2, p3))
    on_258 = min(abs(math.dist(p, cc) - ca.dxf.radius) for p in (p2, p3))
    return {
        "handles": S, "layers": {h: lay.get(h) for h in ("239", "23D", "256", "22E", "A7", "13C", "22F", "23F",
                                                         "22C", "23E", "258")},
        "inner_r": str(R.q6(r0 / 1000)), "outer_r": str(R.q6(r1 / 1000)), "width": str(R.q6((r1 - r0) / 1000)),
        "sweep_deg": str(R.q6(sweep)), "nosing_steps_deg": [str(s) for s in steps],
        "F1_band_exact": str(band_f1), "F1_chord": str(chord_f1),
        "F1_chord_loss": str(R.q6(float(band_f1) - float(chord_f1))),
        "F2_run_gross": str(R.q6(run.area / 1e6)), "F2_column_in_run": str(R.q6(run.intersection(col).area / 1e6)),
        "F2_run_net": str(R.q6(run_net.area / 1e6)),
        "F2_run_len_inner": str(R.q6((xc - pi_[0]) / 1000)), "F2_run_len_outer": str(R.q6((xc - po[0]) / 1000)),
        "F2_run_width": str(R.q6((yi - yo) / 1000)),
        "strip_arc_end_to_first_run_nosing": str(R.q6(strip.area / 1e6)),
        "F2_from_first_run_nosing_net": str(R.q6((Polygon([(x22f, yi), (xc, yi), (xc, yo), (x22f, yo)])
                                                  .difference(col)).area / 1e6)),
        "beside": {"inner_string_curve": str(inner_string),
                   "inner_string_curve_in_curtail": str(R.q6(sector(rs_in, r0, t0, t1).intersection(curtail).area
                                                           / 1e6)),
                   "inner_string_run": str(R.q6(run_string)),
                   "outer_string_curve": str(R.q6(outer_string.area / 1e6)),
                   "outer_string_curve_in_face": str(R.q6(outer_in_face)),
                   "curtail_first_step": str(R.q6(curtail.area / 1e6))},
        "printed": {"955_band_plus_string": str(R.q6(d955)), "drawn_band_plus_string": str(R.q6((yi - yo) / 1000 +
                                                                                              abs(y_str - yi) / 1000)),
                    "963_first_step": str(R.q6(d963.get_measurement() / 1000)),
                    "963_end_on_first_nosing_outer_end_mm": str(R.q6(on_256)),
                    "963_end_on_curtail_arc_mm": str(R.q6(on_258)),
                    "first_nosing_outer_r": str(R.q6(math.dist(ln(S["first_nosing"])[1], c) / 1000))},
    }


def _st(st_doc, doc):
    def bb(d, h):
        return _bb(d, h)
    a = [bb(doc, h) for h in ST_FRAME["arch"]]
    s = [bb(st_doc, h) for h in ST_FRAME["st"]]
    dx, dy = s[0][0] - a[0][0], s[0][1] - a[0][1]
    resid = max(abs(s[1][0] - a[1][0] - dx), abs(s[1][1] - a[1][1] - dy))
    return (dx, dy), resid


def _arrival_and_slab(doc, st_doc, shift):
    db = doc.entitydb
    ln = lambda d, h: ((d.entitydb[h].dxf.start.x, d.entitydb[h].dxf.start.y),  # noqa: E731
                       (d.entitydb[h].dxf.end.x, d.entitydb[h].dxf.end.y))
    r, nz = ln(doc, ARRIVAL_BAND["riser"]), ln(doc, ARRIVAL_BAND["nosing"])
    width = math.dist(*r) / 1000
    depth = abs(_proj(nz[0], *r)[1]) / 1000
    out = {"arrival_band": {"handles": [ARRIVAL_BAND["riser"], ARRIVAL_BAND["nosing"]],
                            "layers": [db[ARRIVAL_BAND["riser"]].dxf.layer, db[ARRIVAL_BAND["nosing"]].dxf.layer],
                            "width": str(R.q6(width)), "depth": str(R.q6(depth)), "area": str(R.q6(width * depth))}}
    if st_doc is None:
        return out
    st = {}
    for h, note in ST_LINES.items():
        a, b = ln(st_doc, h)
        a, b = (a[0] - shift[0], a[1] - shift[1]), (b[0] - shift[0], b[1] - shift[1])
        tgt = {"459": ln(doc, "AC0"), "315": ln(doc, "D24")}[h]
        st[h] = {"note": note, "layer": st_doc.entitydb[h].dxf.layer,
                 "offset_to_arch_line_mm": str(R.q6(max(_proj(a, *tgt)[1], _proj(b, *tgt)[1]))),
                 "length": str(R.q6(math.dist(a, b) / 1000)), "arch_line": {"459": "AC0", "315": "D24"}[h]}
    out["st_lines"] = st
    # slab edge vs the architectural void line (north / east of the 1F void); margin strips by bound
    n_st, e_st = ln(st_doc, SLAB_EDGE["st_north"]), ln(st_doc, SLAB_EDGE["st_east"])
    n_ar, e_ar = ln(doc, SLAB_EDGE["arch_north"]), ln(doc, SLAB_EDGE["arch_east"])
    y_st = n_st[0][1] - shift[1]
    x_st = max(e_st[0][0], e_st[1][0]) - shift[0]
    dn = abs(n_ar[0][1] - y_st) / 1000
    de = abs(e_ar[0][0] - x_st) / 1000
    north_len = abs(n_ar[0][0] - n_ar[1][0]) / 1000
    y_top = ln(doc, SLAB_EDGE["arch_band_top"])[0][1]
    east_len = abs(n_ar[0][1] - y_top) / 1000
    out["slab_edge_margin"] = {"handles": {"st": [SLAB_EDGE["st_north"], SLAB_EDGE["st_east"]],
                                           "arch": [SLAB_EDGE["arch_north"], SLAB_EDGE["arch_east"],
                                                    SLAB_EDGE["arch_band_top"]]},
                               "north_offset": str(R.q6(dn)), "east_offset": str(R.q6(de)),
                               "north_len": str(R.q6(north_len)), "east_len_to_band_top": str(R.q6(east_len)),
                               "bound_m2": str(R.q6(north_len * dn + (east_len + dn) * de))}
    return out


def read(path, st_path=None):
    import ezdxf
    from shapely.geometry import Polygon

    doc = ezdxf.readfile(path)
    if doc.header.get("$INSUNITS") != 4:
        raise R.RuleError("drawing units are not mm")
    msp = doc.modelspace()
    geom, mids = X21.segs(msp)
    st = X6._storeys(msp, mids)
    lay = _layers(msp)
    st_doc = ezdxf.readfile(st_path) if st_path else None
    shift, resid = _st(st_doc, doc) if st_doc is not None else ((0.0, 0.0), None)
    inserts = [(e.dxf.handle, e.dxf.name, (e.dxf.insert.x, e.dxf.insert.y)) for e in msp.query("INSERT")]
    cols = {k: [] for k in st}
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.layer == "S-COL.BON" and e.closed:
            p = [(q[0], q[1]) for q in e.get_points()]
            for k, (a0, b0) in st.items():
                if a0 < p[0][0] < b0:
                    cols[k].append((e.dxf.handle, p))
    out = {"schema": "T625_DRAWN_V1", "rule": R.RULE_ID,
           "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf); second drawing "
                     "'ST7757 dxf.dxf'", "units": "m / m2 / deg", "outlines": {}}
    for name, (s, src, chain) in CHAINS.items():
        a0, b0 = st[s]
        lines = [(h, g) for h, (t, g) in geom.items() if t == "LINE" and a0 < g[0][0] < b0]
        storey_ins = [i for i in inserts if a0 < i[2][0] < b0]
        edges, green = _edges(name, s, chain, geom, lines, lay, storey_ins, doc, st_doc, shift)
        acc = R.account(edges)
        g_area = R.green_area(green)
        if src == "T612":
            r2 = R12.outline_gross(geom, chain, cols[s])
            route2 = {"area": str(r2["area"]), "method": "R-T612-1 gross (T-612 tool, 0.5 deg flattening)"}
        else:
            r2 = R6.outline(geom, chain, [p for _, p in cols[s]])
            route2 = {"area": str(r2["area"]), "notch_m2": str(r2["notch_m2"]),
                      "method": "R-T606-1 (T-606 tool, 0.5 deg flattening, column notches)"}
        poly_pts = []
        for e in green:          # arcs sampled at 0.01 deg for the notch / level tests only (area: Green, exact)
            if e[0] == "LINE":
                poly_pts.append(e[1])
            else:
                c, r = e[3], e[4]
                sw = R.arc_sweep(c, e[1], e[2], e[5], e[6])
                t0 = math.atan2(e[1][1] - c[1], e[1][0] - c[0])
                k = max(2, int(abs(math.degrees(sw)) / 0.01))
                poly_pts.extend((c[0] + r * math.cos(t0 + sw * j / k), c[1] + r * math.sin(t0 + sw * j / k))
                                for j in range(k))
        poly = Polygon(poly_pts)
        notch = 0.0
        for _, cp in cols[s]:
            P = Polygon(cp)
            if P.intersects(poly) and not poly.contains(P):
                notch += P.intersection(poly).area
        inside = [h for h, cp in cols[s] if poly.contains(Polygon(cp))]
        notched = [h for h, cp in cols[s] if Polygon(cp).intersects(poly) and not poly.contains(Polygon(cp))
                   and Polygon(cp).intersection(poly).area > 1.0]
        out["outlines"][name] = {
            "storey": s, "chain_from": src, "handles": [h for h, _ in chain], "roles": [r for _, r in chain],
            "edges": edges, "account": acc, "area_exact_green": str(g_area),
            "column_notch_at_boundary": str(R.q6(notch / 1e6)), "columns_notched": notched,
            "columns_inside": inside, "area_exact_net": str(R.q6(float(g_area) - notch / 1e6)),
            "area_route2": route2, "dim_checks": _dim_check(doc, edges, DIM_CHECKS.get(name)),
            "levels": _levels(msp, poly, a0, b0)}
    out["stair_row0"] = _stair(doc, lay)
    out["st_frame"] = {"pair_arch": ST_FRAME["arch"], "pair_st": ST_FRAME["st"],
                       "residual_mm": None if resid is None else str(R.q6(resid))}
    out["first_floor"] = _arrival_and_slab(doc, st_doc, shift)
    return out


def dumps(d):
    return json.dumps(d, indent=1, sort_keys=True) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--st")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    d = read(a.dxf, a.st)
    txt = dumps(d)
    if a.write:
        OUT.write_text(txt, encoding="utf-8")
        print("written", OUT.name)
    else:
        print("re-read", "identical" if OUT.exists() and OUT.read_text(encoding="utf-8") == txt else "DIFFERS")
    for k, v in d["outlines"].items():
        print(k, "green", v["area_exact_green"], "route2", v["area_route2"]["area"], "notch",
              v["column_notch_at_boundary"], v["account"]["metres"])
        for o in v["account"]["open_sides"]:
            print("   ", o)
        print("   dims", v["dim_checks"])
        print("   levels", v["levels"])
    print(json.dumps(d["stair_row0"], indent=0)[:3000])
    print(json.dumps(d["first_floor"], indent=0), d["st_frame"])


if __name__ == "__main__":
    main()
