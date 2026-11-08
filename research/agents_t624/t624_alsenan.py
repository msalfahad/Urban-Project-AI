"""T-624 development-villa closure (research, unwired; lane S): the four beam-band items T-614 r2 / T-619 left open.

    .work/venv/bin/python -I research/agents_t624/t624_alsenan.py <structural.dxf> [--write | --check]

(a) GF CB4 BAND0021.1.r2 +0.01355 m3 'inside a neighbour rectangle' (T-614 r2 open item);
(b) the 5 model-only pairs UNRESOLVED on the T-229 add placement (GF B28 / B26 at C27, GF B26 at C25, GF B27 at C8,
    1F B19 at C15);
(c) F-T619-1: the GF B27 tip 0.001524 m2 carried as a HELD companion 0 .. 0.001295 m3;
(d) F-T619-2: FR-T614-H1 (GF CB8 at col 2, 0.00454 m2 HELD) has no owning BOQ line.

Inputs (read only): Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179..; decoded to .work/private
only); the T-610 member / line model and the T-614 census helpers (unchanged); the T-229 census re-run with its own
code (research/agents_t229/t229_census.py, unchanged) to rebuild the region behind each named T-229 add. Tracked
output: band ids, marks, line ids, DXF handles, areas, depths, volumes, verdicts; no coordinate.
"""
from __future__ import annotations

import csv
import hashlib
import json
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT / "research" / "agents_t614", ROOT / "research" / "agents_t610",
          ROOT / "research" / "agents_t229", ROOT / "research" / "agents_t217", ROOT):
    sys.path.insert(0, str(p))

import t624_rules as R  # noqa: E402
import t614_rules as R614  # noqa: E402  (read only)
import t614_alsenan as T614  # noqa: E402  (read only)
import t610_alsenan as T610  # noqa: E402  (read only)

OUT = HERE / "out"
JSON_OUT = OUT / "T624_BEAM_END_OPEN_ITEMS.json"
MD_OUT = OUT / "T624_BEAM_END_OPEN_ITEMS.md"
DXF_SHA = T610.DXF_SHA
LEDGER = ROOT / "research/agents_t252/LEDGER_T252.csv"
T229_CENSUS = ROOT / "research/agents_t229/CENSUS.csv"
T229_SUMMARY = ROOT / "research/agents_t229/summary.json"
RG = ROOT / "research/urban_engine_m4_correctness/st7757_route_g"
# V14 B10 STR.CONC.BEAM after-total (T-619 MERGED e8709e09, Verifier re-add 08:01): low .. high (high = low + the B27
# tip companion 0.001524 x 0.85); his (freelancer) total from the V10 statement (T-623 row)
V14_B10_LOW, V14_B10_HIGH, HIS_B10 = 66.392081, 66.393376, 66.093875

# the five T-614 r2 model-only pairs (census column index -> DXF outline handle, read from T-229 / T-614 records)
PAIRS = [
    {"storey": "GF", "parent": "BAND0035", "column": "C27", "mark": "B28", "end": ("GF:BAND0035.1", 0),
     "column_handles": "support + carried 31B (S-COL.HAT ANSI35)"},
    {"storey": "GF", "parent": "BAND0047", "column": "C27", "mark": "B26", "end": ("GF:BAND0047.2", 1),
     "column_handles": "support + carried 31B (S-COL.HAT ANSI35)"},
    {"storey": "GF", "parent": "BAND0047", "column": "C25", "mark": "B26", "end": ("GF:BAND0047.1", 0),
     "column_handles": "371"},
    {"storey": "GF", "parent": "BAND0048", "column": "C8", "mark": "B27", "end": ("GF:BAND0048.1", 0),
     "column_handles": "35C"},
    {"storey": "1F", "parent": "BAND0030", "column": "C15", "mark": "B19", "end": ("1F:BAND0030.1", 1),
     "column_handles": "667"},
]


def r6(x):
    return None if x is None else round(float(x), 6)


def handle(seg_id):
    return seg_id.split(":")[1]


# ---------------------------------------------------------------- T-229 regions rebuilt with T-229's own code
def t229_regions(dxf):
    """Re-run the T-229 census (unchanged code) and keep the polygon of every end region it measured (its `_beyond`
    construction) and the carried-column outlines; returns {(piece, end): {...}} in T-229 frame (drawing metres)."""
    import t229_census as C
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union
    store = {}
    orig = C._beyond

    def wrap(p, end, touch, M, P, gpolys, rings, B, segs, out_edges):
        r = orig(p, end, touch, M, P, gpolys, rings, B, segs, out_edges)
        reach = 2.0 if touch == "CARRIED" else 0.8      # as C._beyond (read only)
        strip = Polygon(C._box(p, end, reach))
        stops = [Polygon(m.plan) for m in M if m.kind != "CARRIED_COLUMN"]
        stops += [Polygon(q.plan()) for q in P if q is not p and q.beam != p.beam]
        stops += [Polygon(gp) for gid, gp in gpolys if p.id.split(":")[1] not in gid]
        for rk in rings:
            st, band = rk.split(":")
            stops.append(Polygon(B[band + "@" + st]["pts"]).buffer(0))
        free = strip.difference(unary_union(stops).buffer(0))
        c = p.p0 if end == 0 else p.p1
        d = (-p.u[0], -p.u[1]) if end == 0 else p.u
        n = (-d[1] * p.width / 2, d[0] * p.width / 2)
        face = LineString([(c[0] - n[0], c[1] - n[1]), (c[0] + n[0], c[1] + n[1])]).buffer(0.002)
        comps = [g for g in getattr(free, "geoms", [free]) if not g.is_empty and g.intersects(face)]
        g = unary_union(comps) if comps else None
        if (g.area if g is not None else 0.0) != (r.get("beyond_area_m2") or 0.0) and \
                abs((g.area if g is not None else 0.0) - r["beyond_area_m2"]) > 1e-5:
            raise AssertionError(f"T-229 region rebuild differs at {p.id} {end}")
        store[(p.id, end)] = {"region": g, "area_t229": r.get("beyond_area_m2"), "touch": touch,
                              "carried": [Polygon(m.plan) for m in M if m.kind == "CARRIED_COLUMN"],
                              "plan": Polygon(p.plan())}
        return r
    C._beyond = wrap
    try:
        with tempfile.TemporaryDirectory() as td:
            bands = Path(td) / "bands.json"
            subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t110/scripts/bands.py"), str(RG),
                            str(bands)], check=True, capture_output=True)
            C.extract(Path(dxf), bands)
    finally:
        C._beyond = orig
    return store


def frame_shift(store, members, st):
    """T-229 frame (drawing metres) -> route G sheet metres: median centroid offset of the same pieces."""
    dd = [(members[k.split(":")[1]]["rect"].centroid.x - v["plan"].centroid.x,
           members[k.split(":")[1]]["rect"].centroid.y - v["plan"].centroid.y)
          for (k, e), v in store.items() if k.startswith(st + ":") and e == 0 and k.split(":")[1] in members]
    sx, sy = statistics.median(x for x, _ in dd), statistics.median(y for _, y in dd)
    spread = max(max(abs(x - sx), abs(y - sy)) for x, y in dd)
    return sx, sy, spread, len(dd)


# ---------------------------------------------------------------- drawing helpers
def seg_lines(G, sid):
    from shapely.geometry import LineString
    rec = G["D"]["sheets"][sid]
    u_m = G["D"]["unit_m"]
    ox, oy = rec["sheet"]["origin"]
    return {s["id"]: (s["layer"], LineString([((s["a"][0] - ox) * u_m, (s["a"][1] - oy) * u_m),
                                              ((s["b"][0] - ox) * u_m, (s["b"][1] - oy) * u_m)]))
            for s in G["intake"]["segments"]}


def on_lines(geom, segs, buf=R.LINE_BUF_M, min_len=0.005):
    """Handles of drawn lines that run along a boundary part of geom (>= 5 mm of it within 2 mm)."""
    b = geom.boundary
    out = []
    for sid, (layer, ln) in segs.items():
        if ln.distance(geom) > buf:
            continue
        if b.intersection(ln.buffer(buf)).length >= min_len:
            out.append(f"{handle(sid)} ({layer})")
    return sorted(out)


def columns_of(cols):
    cl = sorted(getattr(cols, "geoms", [cols]), key=lambda c: (round(c.centroid.x, 3), round(c.centroid.y, 3)))
    return [c for c in cl if c.area > R614.EPS_M2]


def load_t229_census():
    rows = {}
    for r in csv.DictReader(open(T229_CENSUS, encoding="utf-8")):
        if r["where"].startswith("end "):
            rows[(r["piece"], int(r["where"].split()[1]))] = r
    return rows


def other_t229_regions(store, shift, st, exclude, billed_only=None):
    """T-229 end regions of this storey in the route G frame, eroded by the frame spread (a 1-2 mm fit offset is not
    an overlap); billed_only: the T-229 census rows, keeping only ends whose class bills a term (status BEAM_SHORT)."""
    from shapely.affinity import translate
    out = {}
    for k, v in store.items():
        if not k[0].startswith(st + ":") or v["region"] is None or k in exclude:
            continue
        if billed_only is not None and (billed_only.get(k) or {}).get("status") != "BEAM_SHORT":
            continue
        out[k] = translate(v["region"], shift[0], shift[1]).buffer(-shift[2])
    return out


# ---------------------------------------------------------------- the four items
def build(dxf):
    from shapely.affinity import translate
    from shapely.geometry import Polygon, LineString
    sha = hashlib.sha256(Path(dxf).read_bytes()).hexdigest()
    assert sha == DXF_SHA, sha
    G = T610.route_g(dxf)["generic"]
    lines, ledger = T610.load_lines(), T610.load_ledger()
    store = t229_regions(dxf)
    census229 = load_t229_census()
    summ = json.loads(T229_SUMMARY.read_text(encoding="utf-8"))
    led = {r["run"]: r for r in csv.DictReader(open(LEDGER, encoding="utf-8"))}
    S = {}
    for st, sid in T610.SHEETS.items():
        members, cols, _ = T610.storey_members(G, sid, st)
        recs, pl = T610.line_members(lines, ledger, members, st)
        live = {k: v for k, v in recs.items() if v.get("drawn") is not None}
        S[st] = {"sid": sid, "members": members, "cols": cols, "col_list": columns_of(cols), "recs": recs,
                 "pl": pl, "live": live, "hulls": T614.parent_hulls(G, sid), "segs": seg_lines(G, sid),
                 "shift": frame_shift(store, members, st), "slab": T610.slab_panels(G, sid)}
    out = {"schema": "T624_BEAM_END_OPEN_ITEMS_V1", "rule": R.RULE_ID,
           "candidate": "ARCH_TAKEOFF_V3.0.57 (= V3.0.58 for STR.CONC.BEAM)",
           "source": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179..)",
           "t229_frame": {st: {"pieces": s["shift"][3], "spread_m": r6(s["shift"][2])} for st, s in S.items()}}

    def all_billed(st, skip_lines=()):
        s = S[st]
        return {lid: r["billed"] for lid, r in s["live"].items() if r.get("billed") is not None and lid not in skip_lines}

    # ---- (a) GF CB4 BAND0021.1.r2: the oblique end triangle
    s = S["GF"]
    h = s["hulls"]["BAND0021"]
    u = h["u"]
    nvec = (-u[1], u[0])

    def P(t, o):
        return (t * u[0] + o * nvec[0], t * u[1] + o * nvec[1])
    (fa, fb) = sorted(h["faces"], key=lambda f: f["intervals"][0][0])     # fa: the longer face (starts first)
    t_long, t_short = fa["intervals"][0][0], fb["intervals"][0][0]
    tri = Polygon([P(t_long, fa["off_m"]), P(t_short, fa["off_m"]), P(t_short, fb["off_m"])])
    shared = LineString([P(t_short, fa["off_m"]), P(t_short, fb["off_m"])])
    cover = R.drawn_cover(tri, [ln for _, ln in s["segs"].values()], shared=shared)
    lid_a = s["pl"]["BAND0021.1"]
    billed_other = {k: v.intersection(tri).area for k, v in all_billed("GF", [lid_a]).items()}
    t229o = other_t229_regions(store, s["shift"], "GF", exclude={("GF:BAND0021.1", 0)}, billed_only=census229)
    t229_other = {f"{k[0]} end {k[1]}": g.intersection(tri).area for k, g in t229o.items()}
    own229 = translate(store[("GF:BAND0021.1", 0)]["region"], s["shift"][0], s["shift"][1])
    row = led["BM-GF-021#BAND0021.1.r2"]
    L, b, d = float(row["length_m"]), float(row["b_drawn_m"]), float(row["depth_m"])
    rect = s["members"]["BAND0021.1"]["rect"].area
    excess = L * b - rect
    out["a_CB4"] = {
        "line_id": lid_a, "run": row["run"], "printed": f"{L} x {b} x {d} = {row['m3']}", "rect_m2": r6(rect),
        "excess_m2": r6(excess), "excess_m3": r6(excess * d),
        "triangle_m2": r6(tri.area), "triangle_x_depth_m3": r6(tri.area * d),
        "edge_lengths_m": [r6(fa["intervals"][0][1] - t_long), r6(fb["intervals"][0][1] - t_short)],
        "triangle_sides_on": on_lines(tri, s["segs"]), "boundary_drawn_share": r6(cover),
        "in_support_columns_m2": r6(tri.intersection(s["cols"]).area),
        "billed_by_other_lines_m2": r6(sum(billed_other.values())),
        "in_other_t229_regions_m2": r6(sum(t229_other.values())),
        "in_own_t229_end_region_m2": r6(tri.intersection(own229).area), "own_t229_end_region_m2": r6(own229.area),
        "in_slab_panel_m2": r6(tri.intersection(s["slab"]).area),
        "excess_minus_triangle_m3": r6((excess - tri.area) * d)}
    a = out["a_CB4"]
    a["verdict"] = ("ENGINE_RIGHT" if a["billed_by_other_lines_m2"] <= R.EPS_M2 and a["in_other_t229_regions_m2"]
                    <= R.EPS_M2 and abs(a["excess_minus_triangle_m3"]) <= R.ADD_TOL_M3 and cover >= R.DRAWN_COVER_MIN
                    else "UNRESOLVED")
    a["basis"] = ("the r2 mean-length excess is the drawn triangle between CB4's two faces and B27's face: inside "
                  "no other member's rectangle, billed by no other line and in no other T-229 region; billed once")

    # ---- (b) the five model-only pairs
    out["b_pairs"] = []
    for spec in PAIRS:
        st = spec["storey"]
        s = S[st]
        h = s["hulls"][spec["parent"]]
        ci = int(spec["column"][1:])
        c = s["col_list"][ci]
        rest = [x for j, x in enumerate(s["col_list"]) if j != ci]
        _, E = R614.piece(h["hull"], h["u"], c, rest)
        piece_key = spec["end"][0]
        band = piece_key.split(":")[1]
        lid = s["pl"][band]
        line = s["live"][lid]
        depth = line["depth_m"]
        others_drawn = R614.union([r["drawn"] for k, r in s["live"].items() if k != lid])
        owned = R614.minus(E, others_drawn)
        own_rects = R614.union([s["members"][k]["rect"] for k in h["kids"]])
        in_rect = R614.inter(owned, own_rects)
        reg = store[spec["end"]]["region"]
        regm = translate(reg, s["shift"][0], s["shift"][1]) if reg is not None else None
        cen = census229[spec["end"]]
        add_m3 = float(cen["m3_effect"] or 0)
        end_cls = cen["class"]
        rec = {"storey": st, "mark": spec["mark"], "column": spec["column"], "column_outline": spec["column_handles"],
               "line_id": lid, "depth_m": depth, "piece_m2": r6(E.area), "in_other_band_m2": r6(E.area - owned.area),
               "owned_m2": r6(owned.area), "in_own_rectangle_m2": r6(in_rect.area),
               "t229_end": f"{piece_key} end {spec['end'][1]}", "t229_class": end_cls, "t229_add_m3": add_m3,
               "in_slab_panel_m2": r6(owned.intersection(s["slab"]).area)}
        rest_owned = R614.minus(owned, own_rects)
        if end_cls.startswith("END_SHORT") and regm is not None:
            pl_ = R.place_in_add(rest_owned, regm, add_m3, depth)
            # the drawn content of the region: band part + carried-column footprint inside the drawn hull
            car = R614.union([translate(x, s["shift"][0], s["shift"][1]) for x in store[spec["end"]]["carried"]])
            drawn_content = R614.union([rest_owned, R614.inter(R614.inter(regm, car), h["hull"])])
            rec.update({"region_m2": r6(pl_["region_m2"]), "region_x_depth_m3": r6(pl_["region_m3"]),
                        "region_vs_add_m3": r6(pl_["region_vs_add_m3"]), "piece_in_region_m2": r6(pl_["in_add_m2"]),
                        "piece_outside_region_m2": r6(pl_["outside_m2"]),
                        "region_carried_column_m2": r6(R614.inter(regm, car).area),
                        "region_minus_drawn_content_m2": r6(regm.area - drawn_content.area),
                        "region_minus_drawn_content_m3": r6((regm.area - drawn_content.area) * depth),
                        "placement": pl_["verdict"]})
            unbilled = max(pl_["outside_m2"], 0.0)
            # the drawn content read a second way (R-T624-1 (c)): the band-width strip over the region's span, net
            # of solid support columns (carried outlines excluded), other drawn bands and the own rectangles, valid
            # when its boundary is drawn all round except the side it shares with the rectangle
            uu, nn = h["u"], (-h["u"][1], h["u"][0])
            nlo_, nhi_ = R614.span(h["hull"], nn)
            t0_, t1_ = R614.span(regm, uu)
            solid = R614.minus(s["cols"], car)
            strip_c = R614.minus(R614.minus(R614.minus(R614.band_strip(uu, nlo_, nhi_, t0_, t1_), solid),
                                            others_drawn), own_rects)
            cov = R.drawn_cover(strip_c, [ln for _, ln in s["segs"].values()], shared=own_rects.boundary,
                                buf=max(R.LINE_BUF_M, s["shift"][2]))
            rec.update({"strip_content_m2": r6(strip_c.area), "strip_content_drawn_share": r6(cov),
                        "region_minus_strip_content_m3": r6((regm.area - strip_c.area) * depth),
                        "region_outline_on": on_lines(strip_c, s["segs"], buf=max(R.LINE_BUF_M, s["shift"][2]))})
            agree_hull = abs((regm.area - drawn_content.area) * depth) <= R.tol_m3(add_m3)
            agree_strip = cov >= R.DRAWN_COVER_MIN and abs((regm.area - strip_c.area) * depth) <= R.tol_m3(add_m3)
            rec["region_content_agrees"] = "HULL" if agree_hull else "STRIP" if agree_strip else "NO"
            ok = pl_["verdict"] == "BILLED_BY_ADD" and (agree_hull or agree_strip)
            rec["verdict"] = "ENGINE_RIGHT" if ok else "UNRESOLVED"
            rec["residual_m3"] = r6(unbilled * depth)
        else:
            # no named add at this end (T-229 class PASS): the piece beyond the rectangle is billed by nobody unless
            # it is a fit residual; the drawn faces decide (R-T624-1 (d))
            ends = []
            for f in h["faces"]:
                t = f["intervals"][0][0] if spec["end"][1] == 0 else f["intervals"][-1][1]
                uu, nn = h["u"], (-h["u"][1], h["u"][0])
                ends.append((t * uu[0] + f["off_m"] * nn[0], t * uu[1] + f["off_m"] * nn[1]))
            reach = R.faces_reach_column(ends, c)
            wedge = rest_owned.area
            billed_any = sum(v.intersection(rest_owned).area for v in all_billed(st, [lid]).values())
            t229o = other_t229_regions(store, s["shift"], st, exclude=set(), billed_only=census229)
            in229 = sum(g.intersection(rest_owned).area for g in t229o.values())
            cl = R.classify_wedge(wedge - billed_any - in229, reach, depth)
            sk = abs(__import__("math").degrees(__import__("math").atan2(h["u"][1], h["u"][0])) % 90.0)
            rec.update({"faces_end_on_column": reach, "band_skew_deg": r6(min(sk, 90.0 - sk)),
                        "face_end_distance_to_column_m": [r6(c.exterior.distance(R._pt(p))) for p in ends],
                        "wedge_m2": r6(wedge), "wedge_billed_by_any_line_m2": r6(billed_any),
                        "wedge_in_any_t229_region_m2": r6(in229), "wedge_class": cl["class"],
                        "t229_square_threshold_would_drop_it": cl.get("t229_would_call_square"),
                        "wedge_sides_on": on_lines(rest_owned, s["segs"])})
            rec["verdict"] = "ENGINE_WRONG_OMISSION" if cl["class"] == "DRAWN_WEDGE" else "UNRESOLVED"
            rec["omission_m3"] = r6(cl["m3"]) if cl["m3"] is not None else None
        out["b_pairs"].append(rec)
    # run decompositions (R-T624-1 (b)): each run value = rectangles + named T-229 terms
    runs = []
    for b_ in summ["beams"]:
        name = b_["beam"]
        if not any(x in name for x in ("GF B26", "GF B27", "GF B28", "1F B19")):
            continue
        terms = {"released_rectangles": b_["released_m3"], "route_g_held_rectangles": b_["route_g_held_m3"] or 0.0}
        for cz in b_["causes"]:
            k, v = cz.split()
            terms[f"{k} {v}"] = float(v)
        runs.append({"beam": name, "drawing_derived_m3": b_["drawing_derived_m3"], "terms_m3": terms,
                     "residual_m3": r6(R.decompose_run(b_["drawing_derived_m3"], terms))})
    out["b_run_decomposition"] = runs

    # ---- (c) the GF B27 tip (F-T619-1)
    s = S["GF"]
    lid1, lid27 = s["pl"]["BAND0029.4"], s["pl"]["BAND0048.1"]
    zone = R614.minus(R614.inter(s["live"][lid1]["drawn"], s["live"][lid27]["drawn"]), s["cols"])
    r27 = s["members"]["BAND0048.1"]["rect"]
    tip = R614.inter(zone, r27)
    jd = [b_.get("junction_deductions") for b_ in G["D"]["sheets"][s["sid"]]["beams"] if b_["band_id"] == "BAND0029.4"][0]
    released27 = float(led["BM-GF-048#BAND0048.1"]["m3"])   # the run value
    b27 = next(b_ for b_ in summ["beams"] if b_["beam"] == "GF B27 (BAND0048)")
    rect27_term = b27["released_m3"]                         # piece .1 rectangle term inside the run (2.5025)
    jt = R.junction_tip(tip, r27, released27, rect27_term, s["members"]["BAND0029.4"]["billed"], 0.85)
    in229 = sum(g.intersection(tip).area for g in other_t229_regions(store, s["shift"], "GF", set(),
                                                                   billed_only=census229).values())
    b1row = led["BM-GF-031#BAND0029.4"]
    out["c_B27_tip"] = {
        "zone_m2": r6(zone.area), "tip_m2": r6(tip.area), "tip_in_B27_rectangle_m2": r6(jt["in_owner_rect_m2"]),
        "tip_in_B1_billed_m2": r6(jt["in_other_billed_m2"]), "tip_in_any_t229_region_m2": r6(in229),
        "route_g_junction_deduction_on_B1": [{"owner": x["owner"], "area_m2": r6(x["area_m2"])} for x in jd],
        "B27_rectangle_m2": r6(r27.area), "B27_rectangle_x_0.85_m3": r6(r27.area * 0.85),
        "B27_run_rectangle_term_m3": rect27_term, "B27_line_id": lid27,
        "B1_line_id": lid1, "B1_value_m3": b1row["m3"],
        "B1_rebuilt_m3": r6((float(b1row["length_m"]) * float(b1row["b_drawn_m"]) - tip.area) * 0.4),
        "state": jt["state"], "companion_m3": jt["companion_m3"]}
    out["c_B27_tip"]["verdict"] = ("ENGINE_RIGHT" if jt["state"] == "BILLED_ONCE_BY_OWNER" and in229 <= R.EPS_M2
                                   else "UNRESOLVED")

    # ---- (d) FR-T614-H1: GF CB8 at col 2 (C13), west of the column
    s = S["GF"]
    h = s["hulls"]["BAND0039"]
    u = h["u"]
    nvec = (-u[1], u[0])
    nlo, nhi = R614.span(h["hull"], nvec)
    b0, b1 = R614.span(h["hull"], u)
    c13 = s["col_list"][13]
    c0, _ = R614.span(c13, u)
    strip = R614.band_strip(u, nlo, nhi, b1, c0)
    lid39 = s["pl"]["BAND0039"]
    others = [r["drawn"] for k, r in s["live"].items() if k != lid39]
    reg = R.end_gap_region(strip, others, s["col_list"])
    shared = LineString([(b1 * u[0] + nlo * nvec[0], b1 * u[1] + nlo * nvec[1]),
                         (b1 * u[0] + nhi * nvec[0], b1 * u[1] + nhi * nvec[1])])
    cover = R.drawn_cover(reg, [ln for _, ln in s["segs"].values()], shared=shared)
    depth39 = s["live"][lid39]["depth_m"]
    cls = R.classify_end_gap(reg, cover, depth39)
    billed_any = sum(v.intersection(reg).area for v in all_billed("GF").values())
    in229 = sum(g.intersection(reg).area for g in other_t229_regions(store, s["shift"], "GF", set(),
                                                                   billed_only=census229).values())
    row39 = led["BM-GF-040#BAND0039"]
    face_ends = sorted((r6(f["off_m"] - nlo), r6(f["intervals"][-1][1] - b0)) for f in h["faces"])
    out["d_H1"] = {
        "held_row": "FR-T614-H1", "column": "C13 (col 2, outline 37D)", "band": "GF BAND0039 (CB8)",
        "line_id": lid39, "run": row39["run"], "run_printed_length_m": float(row39["length_m"]),
        "hull_length_m": r6(b1 - b0), "end_gap_m": r6(c0 - b1),
        "faces_offset_and_drawn_length_m": face_ends,
        "region_m2": r6(reg.area), "boundary_drawn_share": r6(cover), "boundary_on": on_lines(reg, s["segs"]),
        "billed_by_any_line_m2": r6(billed_any), "in_any_t229_region_m2": r6(in229),
        "in_slab_panel_m2": r6(reg.intersection(s["slab"]).area), "depth_m": depth39,
        "state": cls["state"], "m3": r6(cls.get("m3")), "t614_held_m2": 0.00454}
    out["d_H1"]["verdict"] = ("ENGINE_WRONG_OMISSION" if cls["state"] == "MEASURED" and billed_any <= R.EPS_M2 and
                              in229 <= R.EPS_M2 else "HELD")

    # ---- fix rows and the B10 effect (research, unwired)
    fixes = []
    n = 0
    for p in out["b_pairs"]:
        if p["verdict"] == "ENGINE_WRONG_OMISSION":
            n += 1
            fixes.append({"id": f"FR-T624-{n}", "storey": p["storey"], "mark": p["mark"], "line_id": p["line_id"],
                          "at": f"{p['column']} ({p['column_outline']})", "piece_m2": p["wedge_m2"],
                          "depth_m": p["depth_m"], "change_m3": p["omission_m3"], "cause": "DRAWN_WEDGE (d)"})
    if out["d_H1"]["verdict"] == "ENGINE_WRONG_OMISSION":
        n += 1
        fixes.append({"id": f"FR-T624-{n}", "storey": "GF", "mark": "CB8", "line_id": lid39,
                      "at": "C13 west end gap (col 2, 37D)", "piece_m2": out["d_H1"]["region_m2"],
                      "depth_m": depth39, "change_m3": out["d_H1"]["m3"], "cause": "END_GAP (c); supersedes FR-T614-H1"})
    total = sum(f["change_m3"] for f in fixes)
    low = V14_B10_LOW if out["c_B27_tip"]["verdict"] == "ENGINE_RIGHT" else None
    out["fix_rows"] = fixes
    out["b10_effect"] = {
        "v14_after_total_m3": [V14_B10_LOW, V14_B10_HIGH],
        "after_c_m3": low, "fix_rows_m3": r6(total),
        "after_t624_m3": r6(low + total) if low is not None else None,
        "his_m3": HIS_B10, "gap_to_his_m3": r6(low + total - HIS_B10) if low is not None else None,
        "gap_to_his_pct": r6((low + total - HIS_B10) / HIS_B10 * 100) if low is not None else None,
        "note": "research, unwired: no candidate line moved; for the next wiring manifest"}
    out["note"] = ("areas m2, volumes m3, depths m (schedule, full depth to the slab top as the candidate bills); no "
                   "coordinate; handles are DXF entity handles of ST7757.")
    return out


def render_md(d):
    L = ["# T-624 beam-end open items (R-T624-1, research, unwired)", "",
         f"Candidate {d['candidate']}; {d['source']}. T-229 regions rebuilt with T-229's own code; frame offset "
         "spread " + ", ".join(f"{k} {v['spread_m']} m ({v['pieces']} pieces)" for k, v in d["t229_frame"].items())
         + ".",
         "", "## (a) GF CB4 BAND0021.1.r2", "", "```", json.dumps(d["a_CB4"], indent=1, sort_keys=True), "```", "",
         "## (b) the five model-only pairs", "",
         "| storey | mark | column | line | depth | piece | owned | in rect | T-229 end (class, add m3) | region m2 "
         "| piece outside region | wedge m2 | verdict | m3 |", "|" + "---|" * 14]
    for p in d["b_pairs"]:
        L.append(f"| {p['storey']} | {p['mark']} | {p['column']} | {p['line_id']} | {p['depth_m']} | {p['piece_m2']} | "
                 f"{p['owned_m2']} | {p['in_own_rectangle_m2']} | {p['t229_end']} ({p['t229_class']}, "
                 f"{p['t229_add_m3']}) | {p.get('region_m2')} | {p.get('piece_outside_region_m2')} | "
                 f"{p.get('wedge_m2')} | {p['verdict']} | {p.get('omission_m3', p.get('residual_m3'))} |")
    L += ["", "```", json.dumps(d["b_pairs"], indent=1, sort_keys=True), "```", "", "### run decompositions", "",
          "```", json.dumps(d["b_run_decomposition"], indent=1, sort_keys=True), "```", "",
          "## (c) GF B27 tip (F-T619-1)", "", "```", json.dumps(d["c_B27_tip"], indent=1, sort_keys=True), "```", "",
          "## (d) FR-T614-H1 (F-T619-2)", "", "```", json.dumps(d["d_H1"], indent=1, sort_keys=True), "```", "",
          "## Fix rows", ""]
    for f in d["fix_rows"]:
        L.append(f"- {f['id']} {f['storey']} {f['mark']} {f['line_id']} at {f['at']}: {f['piece_m2']} m2 x "
                 f"{f['depth_m']} = +{f['change_m3']} m3 ({f['cause']})")
    L += ["", "## B10 STR.CONC.BEAM effect", "", "```", json.dumps(d["b10_effect"], indent=1, sort_keys=True), "```", ""]
    return "\n".join(L)


def main(argv):
    d = build(argv[0])
    js = json.dumps(d, indent=1, sort_keys=True) + "\n"
    md = render_md(d) + "\n"
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(js, encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
    elif "--check" in argv:
        if JSON_OUT.read_text(encoding="utf-8") != js or MD_OUT.read_text(encoding="utf-8") != md:
            print("T-624 differs from out/")
            return 1
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
