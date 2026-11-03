"""T-484 on the development villa: own re-measure of the four displacement components of the pits backfill that the
T-350 r2 verdict left unverified (29 necks, strap ends, C8, ground-beam solids over the pits) plus the external GB
trench and the F10 + F scenarios, read from the structural DXF itself (Drive 'Alsenan chalet project' /
'ST7757 dxf.dxf', decoded into .work/private; sha256 prefix 9f9d1179 checked).

Own reads (by layer and handle, no engine route): foundation plan frame (S-COL.BON outlines, S-FOOTINGS polylines /
LINE squares, S-DIM 'F' inserts, column and footing TEXT labels), the schedules (INSERT CGT FOU.W / FOU.H, FT / FTB
DEPHT, SBT strap rows), the ground-beam plan (layer '1' line pairs and arcs by the T-253 / T-242 run handles; frame
translation +38 724.4 mm checked on the 36 columns), the plot rectangle 1658 and the upper boundary G.B 7FC / 7FE / 810.
Merged inputs reused (Checker-verified): the T-189 pool frame (via t350r2_alsenan.pool envelope), the run categories
of the T-350 r2 BEAM_OVER_PITS table (T-253 / T-242 ledgers), the S01 level basis (owner-accepted).

    .work/venv/bin/python -I research/agents_t484/t484_alsenan.py .work/private/ST7757.dxf
      -> summary_t484.json, NECKS_T484.csv, BEAM_PIECES_T484.csv beside this file (handles and values only)
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RES / "agents_t350r2"))

from shapely.geometry import LineString, Point, Polygon, box  # noqa: E402
from shapely.ops import polygonize, unary_union  # noqa: E402

import displacement_remeasure_v1 as R  # noqa: E402

SHA_PREFIX = "9f9d1179"
FP_FRAME = (115000, 155000, 33000, 53000)          # foundation plan frame (raw mm)
GB_FRAME = (78930, 114124, 29036, 57066)           # ground-beam plan frame (raw mm)
GB_TO_FP = 38724.4                                 # GB sheet -> foundation sheet (x only), checked on 36 columns
EG, LIMIT, UNDERLAY, BLINDING, P = 0.0, -1.50, 0.07, 0.10, 0.10
D_S01 = UNDERLAY + BLINDING                        # S01: footing underside at -1.50, formation -1.67
PLOT_H = "1658"
UPPER_GB = ("7FC", "7FE", "810")
STRAPS = {  # drawn edge handles, the two footing outlines it joins, schedule row handle (on sheet)
    "SB1": ("1689", "1B1C", ("1B24", "1B1B"), "1FB0"),
    "SB2": ("1B08", "1B09", ("1B07", "1B19"), "2ABA"),   # 1FBB (80 x 50) lies off the sheet (D-38 / RFI-099)
    "SB3": ("1B26", "1B27", ("1B2A", "166B"), "2B06"),
}
ARCS = {"157+158": ("157", "158"), "139+13A": ("139", "13A")}
RULE = {"MAIN_EXT": "BLINDING_ONLY", "MAIN_INT_D": "ZERO", "MAIN_INT_D33": "OPEN_LOW_ZERO",
        "ANNEX_INT_D33": "OPEN_LOW_BLINDING", "ANNEX_EXT_D35": "OPEN_LOW_BLINDING"}
PRI_HIGH = ["ANNEX_EXT_D35", "MAIN_INT_D33", "ANNEX_INT_D33", "MAIN_EXT", "MAIN_INT_D"]
PRI_LOW = ["MAIN_EXT", "ANNEX_EXT_D35", "ANNEX_INT_D33", "MAIN_INT_D33", "MAIN_INT_D"]


def _in(fr, x, y):
    return fr[0] <= x <= fr[1] and fr[2] <= y <= fr[3]


def read(dxf):
    import ezdxf
    from ezdxf import bbox
    sha = hashlib.sha256(Path(dxf).read_bytes()).hexdigest()
    assert sha.startswith(SHA_PREFIX), sha[:8]
    doc = ezdxf.readfile(dxf)
    msp = doc.modelspace()
    d = {"sha8": sha[:8], "texts": [], "cols": {}, "ftg": {}, "ftg_lines": [], "gb_lines": {}, "ins_texts": [],
         "sched_col": {}, "sched_ftg": {}, "sched_sb": {}, "ent": doc.entitydb}
    for e in msp.query("TEXT"):
        p = e.dxf.insert
        if _in(FP_FRAME, p.x, p.y):
            d["texts"].append((e.dxf.handle, e.dxf.text.strip(), p.x / 1000, p.y / 1000))
    for e in msp.query("LWPOLYLINE"):
        pts = [(x / 1000, y / 1000) for x, y in e.get_points("xy")]
        cx, cy = sum(p[0] for p in pts) / len(pts) * 1000, sum(p[1] for p in pts) / len(pts) * 1000
        if not _in(FP_FRAME, cx, cy):
            continue
        if e.dxf.layer == "S-COL.BON":
            d["cols"][e.dxf.handle] = Polygon(pts)
        elif e.dxf.layer == "S-FOOTINGS":
            d["ftg"][e.dxf.handle] = Polygon(pts)
    for e in msp.query("LINE"):
        s, t = e.dxf.start, e.dxf.end
        mx, my = (s.x + t.x) / 2, (s.y + t.y) / 2
        if e.dxf.layer == "S-FOOTINGS" and _in(FP_FRAME, mx, my):
            d["ftg_lines"].append((e.dxf.handle, (s.x / 1000, s.y / 1000), (t.x / 1000, t.y / 1000)))
        if _in(GB_FRAME, mx, my):
            d["gb_lines"][e.dxf.handle] = ((s.x + GB_TO_FP) / 1000, s.y / 1000), ((t.x + GB_TO_FP) / 1000, t.y / 1000)
    for e in msp.query("INSERT"):
        at = {a.dxf.tag: a.dxf.text for a in e.attribs}
        if e.dxf.name == "CGT":
            d["sched_col"][at["COL-T"]] = (float(at["FOU.W"]) / 100, float(at["FOU.H"]) / 100, e.dxf.handle)
        elif e.dxf.name in ("FT", "FTB"):
            d["sched_ftg"][at["FO-TY"]] = (float(at["W"]) / 100, float(at["H"]) / 100, float(at["DEPHT"]) / 100,
                                          e.dxf.handle)
        elif e.dxf.name == "SBT" and at.get("BEAM", "").startswith("SB"):
            d["sched_sb"][e.dxf.handle] = (at["BEAM"], float(at["W"]) / 100, float(at["H"]) / 100)
        elif e.dxf.layer == "S-DIM" and e.dxf.name in ("F", "CF", "F11"):
            b = bbox.extents([e])
            if not _in(FP_FRAME, b.center.x, b.center.y):
                continue
            if e.dxf.name == "F":
                d["ftg"][e.dxf.handle] = box(b.extmin.x / 1000, b.extmin.y / 1000, b.extmax.x / 1000,
                                             b.extmax.y / 1000)
            for v in e.virtual_entities():
                if v.dxftype() == "TEXT":
                    p = v.dxf.insert
                    d["ins_texts"].append((e.dxf.handle, v.dxf.text.strip(), p.x / 1000, p.y / 1000))
    L = [LineString([a, b]) for _, a, b in d["ftg_lines"]]
    for pg in polygonize(unary_union(L)):
        if abs(pg.area - 1.0) < 1e-6:                  # the 1.00 x 1.00 FN squares drawn as four LINEs
            d["ftg"]["LINESQ@%.3f,%.3f" % pg.bounds[:2]] = pg
    pl = doc.entitydb.get(PLOT_H)
    d["plot"] = Polygon([(x / 1000, y / 1000) for x, y in pl.get_points("xy")])
    return d


def footing_types(d):
    """Footing type per outline: the footing label inside it (F.., C../F.., C/F), else the nearest label outside."""
    labs = []
    for h, t, x, y in d["texts"] + [(h, t, x, y) for h, t, x, y in d["ins_texts"]]:
        m = re.match(r"^(?:C\d*|CN)?/?(F\d*|FN|FF)$", t)
        if m:
            labs.append((m.group(1), Point(x, y)))
    out = {}
    for h, pg in d["ftg"].items():
        inside = sorted({t for t, p in labs if pg.buffer(0.001).contains(p)})
        if not inside:
            inside = [min(labs, key=lambda tp: pg.distance(tp[1]))[0]]
            out[h] = (inside, "NEAREST_LABEL")
        else:
            out[h] = (inside, "LABEL_INSIDE")
    return out


def neck_marks(d, sched):
    """Column mark per S-COL.BON outline: greedy on distance + a size term (drawn plan vs the mark's schedule
    section), so a label between two outlines goes to the outline of its own size."""
    labs = []
    for h, t, x, y in d["texts"] + d["ins_texts"]:
        m = re.match(r"^(C\d*|CN)(?:/F\w*)?$", t)
        if m:
            labs.append((h, m.group(1), Point(x, y)))
    cn = sched.get("CN", (0.30, 0.30))
    cost = []
    for lh, mk, p in labs:
        w, dd = sched[mk][:2] if mk in sched else cn
        for ch, pg in d["cols"].items():
            cost.append((pg.distance(p) + 10.0 * abs(pg.area - w * dd), lh, mk, ch))
    used_l, used_c, out = set(), set(), {}
    for c, lh, mk, ch in sorted(cost):
        if lh in used_l or ch in used_c:
            continue
        used_l.add(lh)
        used_c.add(ch)
        out[ch] = (mk, lh)
    return out


def pits_and_zone(d, ftype):
    import t350r2_alsenan as T
    pits = {h: pg for h, pg in d["ftg"].items() if ftype[h][0] not in (["FF"], ["F", "F10"])}
    union = unary_union([pg.buffer(P, join_style=2) for pg in pits.values()])
    # the pool envelope in the same raw frame (T-189 frame placed by F8's corner; t350r2 construction)
    _, _, _, _, pool, ftg = T.inputs()
    f8 = next(f for f in ftg.values() if f["type"] == "F8")
    cx, cy = f8["x0_mm"] / 1000 - pool["F8"]["x"][0], f8["y0_mm"] / 1000 - pool["F8"]["y"][0]
    r, bx = pool["outline"]["r_outer"], pool["outline"]["back_x"]
    outer = Point(cx, cy).buffer(r, quad_segs=256).intersection(box(cx - r, cy - r, cx, cy + r)).union(
        box(cx, cy - r, cx + bx, cy + r))
    env = outer.buffer(0.10, quad_segs=256)
    zone = union.intersection(d["plot"]).difference(env)
    return pits, union, env, zone


def necks(d, ftype, sched_c, sched_f, env, d_below=D_S01):
    marks = neck_marks(d, sched_c)
    rows, total, coef = [], 0.0, 0.0
    for ch, pg in sorted(d["cols"].items()):
        mk, lh = marks[ch]
        host = [h for h, f in d["ftg"].items() if f.intersection(pg).area > 0.5 * pg.area]
        assert len(host) == 1, (ch, host)
        ft = ftype[host[0]][0]
        drawn = pg.area
        w, dd = sched_c[mk][:2] if mk in sched_c else (0.30, 0.30)     # CN: text row 30 x 30 (T-075)
        row = {"outline": ch, "label": lh, "mark": mk, "footing_outline": host[0], "footing": "|".join(ft),
               "schedule_m2": round(w * dd, 6), "drawn_m2": round(drawn, 6)}
        if ft == ["FF"]:
            row.update(status="OTHER_ZONE", reason="lift pit raft FF: pit depth not printed")
        elif ft == ["F", "F10"]:
            row.update(status="OTHER_ZONE", reason="F10 + F outline (S02 scenarios): own zone, Q-31 C")
        elif mk == "C8" and ft == ["F14"]:
            row.update(status="CONFLICT", reason="mark C8 (schedule 0.30 x 0.90) vs plan text 30X80, drawn 0.80 and "
                                                 "the ground-beam plan label C7 (0.30 x 0.80)")
        else:
            H = sched_f[ft[0]][2]
            top = LIMIT - d_below + UNDERLAY + BLINDING + H          # S01: -1.50 + H
            ie = pg.intersection(env).area / drawn * (w * dd)
            r = R.neck_below_eg(w * dd, top, EG, ie)
            row.update(status="CALCULATED", H=H, footing_top=round(top, 4), h=round(r.parts["h_m"], 4),
                       in_env_m2=round(ie, 6), m3=round(r.value, 6),
                       env_clearance_m=round(pg.distance(env), 4))
            total += r.value
            coef += w * dd
        rows.append(row)
    c8 = next(r for r in rows if r["status"] == "CONFLICT")
    H = sched_f["F14"][2]
    h = EG - (LIMIT - d_below + UNDERLAY + BLINDING + H)
    c8_range = (round(0.30 * 0.80 * h, 6), round(0.30 * 0.90 * h, 6))
    return rows, round(total, 6), round(coef, 6), c8_range


def _perp(a, b):
    """Mean perpendicular distance of edge b's two ends from the infinite line through edge a (drawn width)."""
    (x0, y0), (x1, y1) = a
    n = math.hypot(x1 - x0, y1 - y0)
    return sum(abs((x1 - x0) * (y0 - py) - (x0 - px) * (y1 - y0)) / n for px, py in b) / 2


def _band(a, b):
    pg = Polygon([a[0], a[1], b[1], b[0]]).buffer(0)
    if pg.area < 1e-9 or not pg.is_valid:
        pg = Polygon([a[0], a[1], b[0], b[1]]).buffer(0)
    return pg


def straps(d, ftype, pits, sched_sb):
    feet = unary_union(list(d["ftg"].values()))
    pit_plan = unary_union([pg.buffer(P, join_style=2) for pg in pits.values()])
    rows, total = [], 0.0
    lines = {h: (a, b) for h, a, b in d["ftg_lines"]}
    for k, (e1, e2, (fa, fb), sh) in STRAPS.items():
        mark, W, H = sched_sb[sh]
        assert mark.replace(".", "") == k
        (a0, a1), (b0, b1) = lines[e1], lines[e2]
        width = _perp((a0, a1), (b0, b1))
        band = _band((a0, a1), (b0, b1))
        rest = band.difference(feet)
        comp = [g for g in getattr(rest, "geoms", [rest]) if g.distance(d["ftg"][fa]) < 1e-3
                and g.distance(d["ftg"][fb]) < 1e-3]
        assert len(comp) == 1, k
        between = comp[0]
        for f in (fa, fb):
            in_pits = f in pits
            near = between.intersection(d["ftg"][f].buffer(P, join_style=2))
            r = R.strap_end_volume(near, pit_plan if in_pits else d["ftg"][f].buffer(P, join_style=2), feet, H,
                                   width, W)
            rows.append({"strap": k, "schedule": f"{W:.2f} x {H:.2f} (row {sh})", "drawn_width_m": round(width, 4),
                         "axis_length_between_faces_m": round(between.area / width, 4), "end_on": "|".join(ftype[f][0]),
                         "zone": "PITS24" if in_pits else "OWN_ZONE (F10 + F)", "plan_m2": round(r.parts["plan_m2"], 6),
                         "m3": round(r.value, 6)})
            if in_pits:
                total += r.value
    return rows, round(total, 6)


def _slab(o, u, a, b):
    n = (-u[1], u[0])
    return Polygon([(o[0] + u[0] * a + n[0] * 1e3, o[1] + u[1] * a + n[1] * 1e3),
                    (o[0] + u[0] * b + n[0] * 1e3, o[1] + u[1] * b + n[1] * 1e3),
                    (o[0] + u[0] * b - n[0] * 1e3, o[1] + u[1] * b - n[1] * 1e3),
                    (o[0] + u[0] * a - n[0] * 1e3, o[1] + u[1] * a - n[1] * 1e3)])


def gb_pieces(d, cols):
    """Straight runs: band between the two drawn faces, cut at every column standing in it (the neck owns that
    footprint); strip = the piece grown 0.10 at its sides only. Arcs: annulus between the two arcs over their common
    span, cut at the columns; strip grown 0.10 radially."""
    def straight(k):
        h1, h2 = k.split("+")[0], k.split("+")[-1]
        a, b = d["gb_lines"][h1], d["gb_lines"][h2]
        band = _band(a, b)
        o = a[0]
        L = math.dist(a[0], a[1])
        u = ((a[1][0] - a[0][0]) / L, (a[1][1] - a[0][1]) / L)
        w = _perp(a, b)
        pr = lambda g: [(x - o[0]) * u[0] + (y - o[1]) * u[1] for x, y in g.exterior.coords]  # noqa: E731
        lo, hi = min(pr(band)), max(pr(band))
        cuts = sorted((min(pr(c)), max(pr(c))) for c in getattr(cols, 'geoms', [cols]) if c.intersection(band).area > 0.25 * min(c.area, w * w))
        iv, s = [], lo
        for c0, c1 in cuts:
            if c0 > s + 1e-3:
                iv.append((s, min(c0, hi)))
            s = max(s, c1)
        if hi > s + 1e-3:
            iv.append((s, hi))
        out = []
        for s0, s1 in iv:
            sl = _slab(o, u, s0, s1)
            pc = band.intersection(sl)
            out.append({"L": s1 - s0, "beam": pc, "strip": pc.buffer(P, cap_style=2, join_style=2).intersection(sl)})
        return out

    def arc(k):
        e1, e2 = (d["ent"].get(h) for h in ARCS[k])
        c = ((e1.dxf.center.x + GB_TO_FP) / 1000, e1.dxf.center.y / 1000)
        r0, r1 = sorted((e1.dxf.radius / 1000, e2.dxf.radius / 1000))
        s = max(e1.dxf.start_angle, e2.dxf.start_angle)
        t = min(e1.dxf.end_angle, e2.dxf.end_angle)
        if t <= s:
            t += 360
        ang = [math.radians(s + (t - s) * i / 256) for i in range(257)]
        sector = Polygon([c] + [(c[0] + 10 * math.cos(q), c[1] + 10 * math.sin(q)) for q in ang])
        ring = Point(c).buffer(r1, quad_segs=256).difference(Point(c).buffer(r0, quad_segs=256))
        sring = Point(c).buffer(r1 + P, quad_segs=256).difference(Point(c).buffer(r0 - P, quad_segs=256))
        beam = ring.intersection(sector).difference(cols)
        strip = sring.intersection(sector).difference(cols)
        return [{"L": beam.area / (r1 - r0), "beam": beam, "strip": strip}]
    return straight, arc


def beams(d, cols, zone, pits, ftype, sched_f, d_below=D_S01, union=None):
    rows_rg = list(csv.DictReader(open(RES / "agents_t350r2/BEAM_OVER_PITS_T350R2.csv")))
    S = json.loads((RES / "agents_t350r2/summary_t350r2.json").read_text())
    cat_of_piece = {}
    for r in S["pits24"]["beam_solids_in_zone"]["runs"]:
        for x in r["runs"]:
            cat_of_piece[x] = r["cat"]
    groups = {}
    for r in rows_rg:
        key = r["run"] or r["piece"]
        k = key.split(":", 1)[1] if key.startswith("ARC:") else r["piece"].rsplit("#", 1)[0]
        groups.setdefault(k, {})[r["piece"]] = (r["run"], float(r["L_routeG_m"] or 0), float(r["L_t253_m"] or 0),
                                                sorted(q.split(":")[0] for q in r["pits"].split()))
    straight, arc = gb_pieces(d, cols)
    pieces, table = [], []
    for k, rg in sorted(groups.items()):
        cats = {}
        for piece, (run, Lrg, Lled, ptypes) in rg.items():
            c = cat_of_piece.get(run) or cat_of_piece.get(run.replace("114+7DF", "114+115+7DF"))
            if c:
                cats[piece] = (c, Lled or Lrg, ptypes)
        if not cats:
            continue                                    # runs with no part over the pits in the merged table
        ps = arc(k) if k in ARCS else straight(k)
        kinds = {cl[0] for cl in cats.values()}
        for i, p in enumerate(ps):
            if len(kinds) == 1:
                c = next(iter(kinds))
            else:                                        # mixed run: the piece over the same pits, then length
                mine = sorted(ftype[h][0][0] for h, pg in pits.items()
                              if p["strip"].intersection(pg.buffer(P, join_style=2)).area > 1e-4)
                c = min(cats.values(), key=lambda cl: (-len(set(cl[2]) & set(mine)) + len(set(cl[2]) ^ set(mine)),
                                                       abs(cl[1] - p["L"])))[0]
            pieces.append({"id": f"{k}#{i + 1}", "cat": c, "rule": RULE[c], "beam": p["beam"], "strip": p["strip"]})
            table.append({"pair": k, "piece": i + 1, "cat": c, "L_m": round(p["L"], 4),
                          "beam_over_zone_m2": round(p["beam"].intersection(zone).area, 6),
                          "strip_over_zone_m2": round(p["strip"].intersection(zone).area, 6)})
    footprints = []
    for h, pg in pits.items():
        H = sched_f[ftype[h][0][0]][2]
        footprints.append((pg, LIMIT - d_below + UNDERLAY + BLINDING + H))
    floor = LIMIT - d_below + BLINDING
    hi = R.beam_solid_bounds(pieces, cols, zone, footprints, floor, EG, BLINDING, PRI_HIGH)
    lo = R.beam_solid_bounds(pieces, cols, zone, footprints, floor, EG, BLINDING, PRI_LOW)
    # upper boundary G.B (p.14 A-A 20 x 40, top at N.G.): wholly -0.40 .. 0 where it lies over the zone
    ub = unary_union([Polygon([((x + GB_TO_FP) / 1000, y / 1000) for x, y in d["ent"].get(h).get_points("xy")])
                      for h in UPPER_GB])
    ub_plan = ub.difference(cols).intersection(zone).area
    bycat = {c: [round(lo.parts.get(c, {}).get("low", 0.0), 6), round(hi.parts.get(c, {}).get("high", 0.0), 6)]
             for c in PRI_HIGH}
    bycat["UPPER_BOUNDARY_GB"] = [round(ub_plan * 0.40, 6)] * 2
    total = [round(sum(v[0] for v in bycat.values()), 6), round(sum(v[1] for v in bycat.values()), 6)]
    # reconciliation with T-350 r2 (route-G method): the same pieces, one correction at a time (high end)
    from shapely.geometry import GeometryCollection
    none = GeometryCollection()
    steps = {}
    if union is not None:
        v0 = R.beam_solid_bounds(pieces, none, union, [], floor, EG, BLINDING, PRI_HIGH)
        v1 = R.beam_solid_bounds(pieces, none, zone, [], floor, EG, BLINDING, PRI_HIGH)
        v2 = R.beam_solid_bounds(pieces, cols, zone, [], floor, EG, BLINDING, PRI_HIGH)
        l0 = R.beam_solid_bounds(pieces, none, union, [], floor, EG, BLINDING, PRI_LOW)
        l1 = R.beam_solid_bounds(pieces, none, zone, [], floor, EG, BLINDING, PRI_LOW)
        steps = {"V0 own pieces, unclipped pit union, columns kept, no footing stop": [l0.low, v0.high],
                 "V1 + zone plan (plot line, pool envelope) as the excavation": [l1.low, v1.high],
                 "V2 + column footprints to the necks": [lo.low, v2.high],
                 "V3 + high end stopped on the footing + underlay top (final)": [lo.low, hi.high]}
        steps = {k: [round(a, 6), round(b, 6)] for k, (a, b) in steps.items()}
    # main exterior trench: its whole strip (ledger basis L x 0.50) and the part inside the pits zone, owned by it
    main_ext_strip_zone = lo.parts.get("MAIN_EXT", {}).get("strip_m2", 0.0)
    ext = unary_union([p["strip"] for p in pieces if p["cat"] == "MAIN_EXT"]).difference(cols)
    ext_own = {"strip_total_m2": round(ext.area, 6), "beyond_plot_m2": round(ext.difference(d["plot"]).area, 6),
               "in_pool_envelope_m2": round(ext.intersection(union).difference(zone).intersection(d["plot"]).area, 6)
               if union is not None else None,
               "in_zone_m2": round(main_ext_strip_zone, 6)}
    return {"by_category_m3": bycat, "total_m3": total, "pieces": table,
            "high_parts": {c: {k: round(v, 6) for k, v in x.items() if k != "rule"} for c, x in hi.parts.items()},
            "low_parts": {c: {k: round(v, 6) for k, v in x.items() if k != "rule"} for c, x in lo.parts.items()},
            "upper_boundary_plan_over_zone_m2": round(ub_plan, 6), "reconciliation_without_upper_gb_m3": steps,
            "main_ext_strip_in_zone_m2": round(main_ext_strip_zone, 6), "main_ext_own": ext_own}


def f10f(d, ftype, sched_f, d_below=D_S01):
    h = next(h for h, t in ftype.items() if t[0] == ["F", "F10"])
    x0, y0, x1, y1 = d["ftg"][h].bounds
    W10, L10 = sched_f["F10"][:2]
    WF, LF = sched_f["F"][:2]
    g = lambda b: b.buffer(P, join_style=2)  # noqa: E731
    D = -LIMIT + d_below
    f10s = {"F10 at the west end": box(x0, y0, x0 + W10, y0 + L10), "F10 at the east end": box(x1 - W10, y0, x1,
                                                                                                  y0 + L10)}
    fs = {"F south-west": box(x0, y0, x0 + WF, y0 + LF), "F south-east": box(x1 - WF, y0, x1, y0 + LF),
          "F north-west": box(x0, y1 - LF, x0 + WF, y1), "F north-east": box(x1 - WF, y1 - LF, x1, y1)}
    alone = [g(b).intersection(d["plot"]).area for b in f10s.values()]
    union, summ, overlap = [], [], []
    for b in f10s.values():
        for f in fs.values():
            union.append(R.union_plan([g(b), g(f)], d["plot"]))
            summ.append(g(b).intersection(d["plot"]).area + g(f).intersection(d["plot"]).area)
            overlap.append(b.intersection(f).area)
    outline = g(d["ftg"][h]).intersection(d["plot"]).area
    return {"outline_m": [round(x1 - x0, 4), round(y1 - y0, 4)], "depth_m": round(D, 4),
            "F10_alone_plan_m2": [round(min(alone), 6), round(max(alone), 6)],
            "F10_plus_F_union_plan_m2": [round(min(union), 6), round(max(union), 6)],
            "F10_plus_F_sum_plan_m2_T478": [round(min(summ), 6), round(max(summ), 6)],
            "F10_F_footing_plan_overlap_m2": [round(min(overlap), 6), round(max(overlap), 6)],
            "outline_plan_m2": round(outline, 6),
            "excavation_m3": {"F10 alone": [round(min(alone) * D, 6), round(max(alone) * D, 6)],
                              "F10 + F (union)": [round(min(union) * D, 6), round(max(union) * D, 6)],
                              "drawn outline": [round(outline * D, 6)] * 2,
                              "all scenarios": [round(min(alone + union + [outline]) * D, 6),
                                                round(max(alone + union + [outline]) * D, 6)]}}


def backfill(res):
    """Pits backfill with the four re-measured components; the Checker-verified ones (excavation, blinding, underlay,
    footings: T-350 r2 verdict) are taken from the merged summary unchanged."""
    S = json.loads((RES / "agents_t350r2/summary_t350r2.json").read_text())["pits24"]
    exc = S["excavation_insitu_m3"]
    dp = S["displacement"]
    verified = dp["blinding"] + dp["underlay"] + dp["footings"]
    mine_lo = res["necks"]["m3"] + res["strap_ends"]["m3"] + res["c8_conflict_m3"][0] + res["beam_solids"]["total_m3"][0]
    mine_hi = res["necks"]["m3"] + res["strap_ends"]["m3"] + res["c8_conflict_m3"][1] + res["beam_solids"]["total_m3"][1]
    old = S["backfill_compacted_m3"]
    new = [round(exc - verified - mine_hi, 6), round(exc - verified - mine_lo, 6)]
    return {"excavation_m3": exc, "verified_displacement_m3": round(verified, 6),
            "remeasured_displacement_m3": [round(mine_lo, 6), round(mine_hi, 6)],
            "backfill_t350r2_m3": old, "backfill_t484_m3": new,
            "width_m3": [round(old[1] - old[0], 6), round(new[1] - new[0], 6)],
            "named_residual_range": {"C8 mark conflict (drawing conflict, stays)": round(res["c8_conflict_m3"][1] -
                                                                                         res["c8_conflict_m3"][0], 6),
                                     "D-33 / D-35 beam sections (designer items, stay)":
                                         round(res["beam_solids"]["total_m3"][1] - res["beam_solids"]["total_m3"][0], 6)}}


def run(dxf):
    d = read(dxf)
    ftype = footing_types(d)
    sched_c, sched_f = d["sched_col"], d["sched_ftg"]
    pits, union, env, zone = pits_and_zone(d, ftype)
    assert len(pits) == 24, len(pits)
    cols = unary_union(list(d["cols"].values()))
    nrows, ntot, ncoef, c8 = necks(d, ftype, sched_c, sched_f, env)
    srows, stot = straps(d, ftype, pits, d["sched_sb"])
    bm = beams(d, cols, zone, pits, ftype, sched_f, union=union)
    ext_total_plan = None
    t253 = [r for r in csv.DictReader(open(RES / "agents_t253/LEDGER_T253.csv"))
            if r["component"].startswith("GB-EXTERIOR MAIN")]
    ext_total_plan = sum(float(r["L_m"]) for r in t253) * (0.30 + 2 * P)
    inside = bm["main_ext_strip_in_zone_m2"]
    out = {
        "method": "DISPLACEMENT_REMEASURE_V1", "dxf_sha8": d["sha8"], "level_basis": "S01 ESTIMATED (owner-accepted): "
        "footing underside -1.50, underlay 0.07 + blinding 0.10 under it; EG +-0.00 (T-357 DERIVED)",
        "zone_plan_m2": round(zone.area, 6), "pit_union_m2": round(union.area, 6),
        "footing_types": {h: t for h, t in ftype.items()},
        "necks": {"count_calculated": sum(1 for r in nrows if r["status"] == "CALCULATED"), "m3": ntot,
                  "coef_m3_per_m": ncoef, "rows": nrows},
        "c8_conflict_m3": list(c8),
        "strap_ends": {"m3": stot, "rows": srows},
        "beam_solids": bm,
        "ext_gb_trench": {"own_strip": bm["main_ext_own"],
                          "own_outside_pits_m3": round((bm["main_ext_own"]["strip_total_m2"] - inside) * 0.10, 6),
                          "plan_m2": round(ext_total_plan, 6), "excavation_m3": round(ext_total_plan * 0.10, 6),
                          "inside_pits_m3": round(inside * 0.10, 6),
                          "outside_pits_m3": round((ext_total_plan - inside) * 0.10, 6)},
        "f10f": f10f(d, ftype, sched_f),
    }
    out["pits_backfill"] = backfill(out)
    return out


if __name__ == "__main__":
    res = run(sys.argv[1])
    out = HERE / "summary_t484.json"
    keep = {k: v for k, v in res.items() if k != "footing_types"}
    out.write_text(json.dumps(keep, indent=1, sort_keys=True) + "\n")
    with open(HERE / "NECKS_T484.csv", "w", newline="") as f:
        cols = ["outline", "label", "mark", "footing_outline", "footing", "schedule_m2", "drawn_m2", "status", "H",
                "footing_top", "h", "in_env_m2", "env_clearance_m", "m3", "reason"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in res["necks"]["rows"]:
            w.writerow({k: r.get(k, "") for k in cols})
    with open(HERE / "BEAM_PIECES_T484.csv", "w", newline="") as f:
        cols = ["pair", "piece", "cat", "L_m", "beam_over_zone_m2", "strip_over_zone_m2"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in res["beam_solids"]["pieces"]:
            w.writerow(r)
    print(json.dumps({k: keep[k] for k in ("zone_plan_m2", "c8_conflict_m3", "ext_gb_trench", "f10f")}, indent=1))
    print("backfill", json.dumps(res["pits_backfill"]))
    print("necks", res["necks"]["count_calculated"], res["necks"]["m3"], "straps", res["strap_ends"]["m3"])
    print("beams", json.dumps(res["beam_solids"]["by_category_m3"]), res["beam_solids"]["total_m3"])
