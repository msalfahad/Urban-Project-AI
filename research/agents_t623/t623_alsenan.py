"""T-623 development-villa re-measure (research, unwired): the 18 UNKNOWN rows of statement V10 T-545/beams@V10 (12)
and T-551/columns@V10 (6), each measured again from the structural drawing and the freelancer's rows (R-T623-1 .. 3).

    .work/venv/bin/python -I research/agents_t623/t623_alsenan.py <structural.dxf> <concrete workbook> [--write|--check]

Inputs (read only; decoded into .work/private only, never tracked): Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'
(sha256 9f9d1179..) and the concrete + rebar workbook (his beam sheet and his columns sheet). Own read: every length,
area, radius and count below comes from the raw DXF entities (ezdxf, hex handles); route G (tools/urban_boq_m2, as
T-610 runs it) is used ONLY as a locator (which two face handles form a band, which sheet frame is which storey, the
printed schedule depth bound to a band's mark). Engine values: research/agents_t507/out/LINE_INDEX_V3_0_57.json through
the T-252 ledger (beams) and research/agents_t394/summary_t394.json (column members). Statement:
research/agents_t609/out/RECONCILED_STATEMENT_T609.json (sections_v10 [2], [3]).
Tracked output (out/): handles, m3, m2, depths and classes only; no coordinate, no row or length of his.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(ROOT / "research" / "agents_t610"))

import t623_rules as R  # noqa: E402

DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
STATEMENT = ROOT / "research/agents_t609/out/RECONCILED_STATEMENT_T609.json"
SCORECARD = ROOT / "research/agents_t613/out/SCORECARD_T613.json"
LINE_INDEX = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
LEDGER = ROOT / "research/agents_t252/LEDGER_T252.csv"
T394 = ROOT / "research/agents_t394/summary_t394.json"
OUT = HERE / "out"
JSON_OUT = OUT / "T623_UNKNOWN_ROWS.json"
SHEET = {"GF": "SH06", "1F": "SH04"}
BEAM_SHEET = "كمرات"
COLUMN_SHEET = "الحوائط + الأعمدة"
HIS_COL_DEPTH = Decimal("0.75")                     # his columns stop 0.75 below the slab top on GF and 1F (T-394)
TOUCH_M = 0.01                                      # a support within 1 cm of a band end is that end's support
OVERLAP_M2 = 0.001                                  # a band covering >= 10 cm2 of an outline frames into the column
D = Decimal


def hx(rid):
    """route G id 'D2:1064:0' -> raw DXF handle '428' (decimal id -> hex handle)."""
    return "%X" % int(rid.split(":")[1])


# ------------------------------------------------------------------------------------------------ inputs
class Drawing:
    def __init__(self, dxf):
        import ezdxf
        sha = hashlib.sha256(Path(dxf).read_bytes()).hexdigest()
        if sha != DXF_SHA:
            raise R.Refused(f"drawing sha256 {sha[:8]} is not the ST7757 file of record")
        self.doc = ezdxf.readfile(str(dxf))
        import t610_alsenan as T610                                         # locator only (route G as V3.0.x)
        self.G = T610.route_g(dxf)["generic"]
        lo = self.G["intake"]["local_origin"]
        self.lo = (lo["x"], lo["y"])
        self.um = self.G["D"]["unit_m"]

    def sheet(self, st):
        return self.G["D"]["sheets"][SHEET[st]]

    def to_m(self, st, p):
        ox, oy = self.sheet(st)["sheet"]["origin"]
        return ((p[0] - self.lo[0] - ox) * self.um, (p[1] - self.lo[1] - oy) * self.um)

    def ent(self, h):
        e = self.doc.entitydb.get(h)
        if e is None:
            raise R.Refused(f"handle {h} not in the drawing")
        return e

    def seg(self, st, h):
        e = self.ent(h)
        if e.dxftype() != "LINE":
            raise R.Refused(f"{h} is {e.dxftype()}, not a face LINE")
        return self.to_m(st, e.dxf.start), self.to_m(st, e.dxf.end)

    def outline(self, st, h):
        from shapely.geometry import Polygon
        e = self.ent(h)
        if e.dxftype() != "LWPOLYLINE" or e.dxf.layer != "S-COL.BON":
            raise R.Refused(f"{h} is not an S-COL.BON outline")
        return Polygon([self.to_m(st, p) for p in e.get_points("xy")]).buffer(0)

    def outlines(self, st):
        """Every S-COL.BON closed outline inside the storey's slab-plan frame: {handle: polygon}."""
        from shapely.geometry import box
        x0, y0, x1, y1 = self.sheet(st)["sheet"]["box"]
        fr = box(x0 + self.lo[0], y0 + self.lo[1], x1 + self.lo[0], y1 + self.lo[1])
        out = {}
        for e in self.doc.modelspace().query('LWPOLYLINE[layer=="S-COL.BON"]'):
            pts = [tuple(p) for p in e.get_points("xy")]
            if len(pts) >= 4 and all(fr.contains(__import__("shapely.geometry", fromlist=["Point"]).Point(p))
                                     for p in pts):
                out[e.dxf.handle] = self.outline(st, e.dxf.handle)
        return out

    def texts(self, st, layer="S-TEXT"):
        x0, y0, x1, y1 = self.sheet(st)["sheet"]["box"]
        out = []
        for e in self.doc.modelspace().query(f'TEXT[layer=="{layer}"]'):
            p = e.dxf.insert
            if x0 <= p[0] - self.lo[0] <= x1 and y0 <= p[1] - self.lo[1] <= y1:
                out.append((e.dxf.handle, e.dxf.text.strip(), self.to_m(st, p)))
        return out

    def bands(self, st):
        """Locator: route G bands of the storey keyed by band id (face handles, mark, schedule depth, piece range)."""
        rec = self.sheet(st)
        beams = {b["band_id"]: b for b in rec["beams"]}
        out = {}
        for b in rec["bands"]:
            m = beams.get(b["band_id"], {})
            out[b["band_id"]] = {"kind": b["kind"], "faces": [hx(h) for h in b["handles"]], "mark": m.get("mark"),
                                 "depth": m.get("depth_m"), "parent": b.get("parent") or b["band_id"],
                                 "polygon": [self.to_m(st, (p[0] + self.lo[0], p[1] + self.lo[1]))
                                             for p in b["polygon"]]}
        return out


def his_rows(path):
    """His beam rows per storey and mark (b, D, L, n -> m3) and his column rows per storey and mark (b, c, h, n)."""
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    beams = {"GF": {}, "1F": {}, "2F": {}}
    st = None
    ws = wb[BEAM_SHEET]
    mark = None
    for r in ws.iter_rows(values_only=True):
        a = r[0]
        if isinstance(a, str) and "كمرات" in a:
            st = "GF" if "الأرضي" in a else "1F" if "الأول" in a else "2F" if "السطح" in a else st
            continue
        b, dd, ll, n = r[1], r[2], r[3], r[5]
        if isinstance(a, str) and a.strip() and isinstance(b, (int, float)):
            mark = a.strip()
            for p in ("BCB", "GCB"):
                if mark.startswith(p):
                    mark = mark[1:]
        if st and isinstance(b, (int, float)) and isinstance(ll, (int, float)) and mark:
            n = n if isinstance(n, (int, float)) else 1
            beams[st].setdefault(mark, []).append((D(str(b)), D(str(dd)), D(str(ll)), int(n)))
    cols = {"NECK": {}, "GF": {}, "1F": {}, "2F": {}}
    fam = None
    for r in wb[COLUMN_SHEET].iter_rows(values_only=True):
        a = r[0]
        if isinstance(a, str):
            if "رقاب" in a:
                fam = "NECK"
            elif "الأرضي" in a:
                fam = "GF"
            elif "الأول" in a:
                fam = "1F"
            elif "السطح" in a:
                fam = "2F"
            elif "السرداب" in a:
                fam = None
        b, c, h, n = r[1], r[2], r[3], r[5]
        if fam and isinstance(a, str) and all(isinstance(v, (int, float)) for v in (b, c, h, n)):
            cols[fam][a.strip()] = (D(str(b)), D(str(c)), D(str(h)), int(n))
    return beams, cols


def his_beam_m3(rows):
    return R.d6(sum((b * dd * ll * n for b, dd, ll, n in rows), D(0)))


def his_beam_len(rows):
    return sum((ll * n for _, _, ll, n in rows), D(0))


def statement_rows():
    st = json.loads(STATEMENT.read_text(encoding="utf-8"))
    sc = json.loads(SCORECARD.read_text(encoding="utf-8"))
    out = {}
    for si, li in ((2, 32), (3, 33)):
        sec = st["sections_v10"][si]
        line = sc["reference_lines"][li]
        assert line["section_id"] == sec["section_id"]
        out[sec["section_id"]] = [(i, srow, line["rows"][i]["status"]) for i, srow in enumerate(sec["rows"])]
    return out


def engine_lines():
    """Engine m3 per storey and band: the RELEASED STR.CONC.BEAM line of V3.0.57 that bills the band (a T-252 ledger
    line 'HL:BEAM_LEDGER:<st>:<run>#<band>' or a route G line 'P-C:BEAMS:<st>:<band>')."""
    lines = [x for x in json.loads(LINE_INDEX.read_text(encoding="utf-8"))["lines"] if x["item_code"] == "STR.CONC.BEAM"]
    out = {}
    for x in lines:
        e = x["element_id"]
        if x["class"] != "RELEASED":
            continue
        if e.startswith("HL:BEAM_LEDGER:"):
            st, rest = e.split(":")[2], e.split(":", 3)[3]
            key = rest.split("#")[1] if "#" in rest else rest
        elif e.startswith("P-C:BEAMS:"):
            st, key = e.split(":")[2], e.split(":")[3]
        else:
            continue
        out.setdefault((st, key), []).append((x["line_id"], x["measured_net"]))
    return out


# ------------------------------------------------------------------------------------------------ own measures
def _axis(dw, st, b):
    a0, a1 = dw.seg(st, b["faces"][0])
    ux, uy = a1[0] - a0[0], a1[1] - a0[1]
    ln = (ux * ux + uy * uy) ** 0.5
    return (ux / ln, uy / ln)


def band_plan(dw, st, bands, bid, cols, net=True):
    """Own drawn plan of one band piece: the face quadrilateral from the two raw face LINEs (R.quad_plan), for a band
    split by a column cut between its pieces at the mid point of each cut (piece order and ranges from the locator),
    net of every column outline when net (the column owns its footprint, UP-CONC-JOINT-001)."""
    from shapely.ops import unary_union
    b = bands[bid]
    fa, fb = b["faces"]
    q = R.quad_plan(dw.seg(st, fa), dw.seg(st, fb))
    sib = sorted([k for k, v in bands.items() if v["parent"] == b["parent"]],
                 key=lambda k: min(p[0] * _axis(dw, st, b)[0] + p[1] * _axis(dw, st, b)[1]
                                   for p in bands[k]["polygon"]))
    if len(sib) > 1:
        u = _axis(dw, st, b)
        rng = {k: (min(p[0] * u[0] + p[1] * u[1] for p in bands[k]["polygon"]),
                   max(p[0] * u[0] + p[1] * u[1] for p in bands[k]["polygon"])) for k in sib}
        i = sib.index(bid)
        lo = None if i == 0 else (rng[sib[i - 1]][1] + rng[bid][0]) / 2
        hi = None if i == len(sib) - 1 else (rng[bid][1] + rng[sib[i + 1]][0]) / 2
        q = q.intersection(R.axis_strip(u, lo, hi))
    if net:
        q = q.difference(unary_union(list(cols.values())))
    return q


def beams_measure(dw, his, eng):
    out = {}
    cols = {st: dw.outlines(st) for st in ("GF", "1F")}
    B = {st: dw.bands(st) for st in ("GF", "1F")}

    def piece(st, bid):
        p = band_plan(dw, st, B[st], bid, cols[st])
        depth = D(str(B[st][bid]["depth"]))
        return {"band": bid, "faces": B[st][bid]["faces"], "plan_m2": str(R.d6(p.area)), "depth_m": str(depth),
                "own_m3": str(R.beam_volume(p.area, depth)), "_poly": p}

    def eng_for(st, bid):
        hit = eng.get((st, bid), [])
        if len(hit) != 1:
            return None
        return hit[0][1]

    # GF B1: every drawn B1 piece (RUN_COUNT row)
    ps = [piece("GF", b) for b, v in sorted(B["GF"].items()) if v["mark"] == "B1"]
    own = sum((D(p["own_m3"]) for p in ps), D(0))
    his_m3 = his_beam_m3(his["GF"]["B1"])
    out["GF: RUN_COUNT"] = {"storey": "GF", "mark": "B1", "pieces": [p["band"] for p in ps], "detail": ps,
                            "own_m3": str(own), "ref_m3": str(his_m3), "own_delta": str(R.d6(his_m3 - own)),
                            "engine_m3": str(R.d6(sum((D(str(eng_for("GF", p["band"]) or 0)) for p in ps), D(0)))),
                            "cause": "drawn B1 runs (faces + tag) beyond his four rows: his B1 length is shorter than "
                                     "the drawn face-to-face length of the mark, so no part can be support run-through"}
    # single-band rows (drawing precision / beyond extent)
    for name, st, bid, mark in (("GF: UNTRACED -> GF B11 DRAWING_PRECISION", "GF", "BAND0001", "B11"),
                                ("GF: UNTRACED -> GF B8 DRAWING_PRECISION", "GF", "BAND0003", "B8"),
                                ("1F: UNTRACED -> 1F B11 DRAWING_PRECISION", "1F", "BAND0004", "B11"),
                                ("1F: UNTRACED -> 1F B6 DRAWING_PRECISION", "1F", "BAND0021", "B6")):
        p = piece(st, bid)
        rows = his[st][mark]
        if mark == "B6":
            rows = rows[:1]                                   # his one 1F B6 row bound to BAND0021 (T-395 binding)
        hm = his_beam_m3(rows)
        out[name] = {"storey": st, "mark": mark, "pieces": [bid], "detail": [p], "own_m3": p["own_m3"],
                     "ref_m3": str(hm), "own_delta": str(R.d6(hm - D(p["own_m3"]))),
                     "engine_m3": str(eng_for(st, bid)),
                     "cause": "one row of his against one drawn run; his length rounded (< 0.05 m)"}
    # GF B2 MARK_BOUNDARY: his B2 length vs drawn B2 pieces + their support extents (row = beyond the allowance)
    ps = [piece("GF", b) for b, v in sorted(B["GF"].items()) if v["mark"] == "B2"]
    supp = b2_supports(dw, B["GF"], cols["GF"], [p["band"] for p in ps])
    own_f2f = sum((D(p["own_m3"]) for p in ps), D(0))
    inner_cols = []                                           # columns inside a piece (not at its ends)
    for p in ps:
        g = band_plan(dw, "GF", B["GF"], p["band"], cols["GF"], net=False)
        u = _axis(dw, "GF", B["GF"][p["band"]])
        ts = [q[0] * u[0] + q[1] * u[1] for q in g.exterior.coords]
        for h, c in cols["GF"].items():
            if g.intersection(c).area > OVERLAP_M2:
                cs = [q[0] * u[0] + q[1] * u[1] for q in c.exterior.coords]
                if min(cs) > min(ts) + 0.02 and max(cs) < max(ts) - 0.02:
                    inner_cols.append({"piece": p["band"], "column": h, "extent_m": str(R.d6(max(cs) - min(cs)))})
    inner = R.d6(sum((D(c["extent_m"]) for c in inner_cols), D(0)) * D("0.2") * D("0.4"))
    sec = D("0.2") * D("0.4")
    col_ext = sum((D(s["extent_m"]) for s in supp if s["support"].startswith("column")), D(0))
    car_drawn = sum((D(s["extent_m"]) for s in supp if s["support"].startswith("carrier")), D(0))
    car_perp = sum((D(s["carrier_width_m"]) for s in supp if s["support"].startswith("carrier")), D(0))
    allow_perp = R.d6((col_ext + car_perp) * sec + inner)       # carrier at its own width (T-395 / T-545 allowance)
    allow_drawn = R.d6((col_ext + car_drawn) * sec + inner)     # carrier crossed on the B2 axis (R-T600-1 r2)
    hm = his_beam_m3(his["GF"]["B2"])
    beyond_perp = R.d6(hm - own_f2f - allow_perp)
    beyond_drawn = R.d6(hm - own_f2f - allow_drawn)
    b1_piece = piece("GF", "BAND0020.1")
    out["GF: UNTRACED -> GF B2 MARK_BOUNDARY"] = {
        "storey": "GF", "mark": "B2", "pieces": [p["band"] for p in ps], "detail": ps, "supports": supp,
        "own_m3": str(own_f2f), "inside_piece_columns": inner_cols, "inside_piece_columns_m3": str(inner),
        "ref_m3": str(hm), "excess_over_face_to_face_m3": str(R.d6(hm - own_f2f)),
        "allowance_carrier_at_width_m3": str(allow_perp), "allowance_carrier_crossed_m3": str(allow_drawn),
        "own_delta": str(beyond_perp), "beyond_if_carrier_crossed_m3": str(beyond_drawn),
        "capacity_B1_piece_m3": b1_piece["own_m3"],
        "capacity_carrier_crossing_beyond_width_m3": str(R.d6((car_drawn - car_perp) * sec)),
        "cause": "his B2 length beyond the drawn B2 pieces and their supports (carrier B7 at its width): it fits "
                 "BOTH in the collinear piece the drawing labels B1 (BAND0020.1, billed once under B1) AND in the "
                 "oblique crossing of the curved carrier B7 on the B2 axis; his rows carry no location"}
    # 1F CB12 BEYOND_EXTENT: his length beyond the drawn outer-face extent of the mark
    ps = [piece("1F", b) for b in ("BAND0018.1", "BAND0018.2")]
    ext, ends = cb12_extent(dw, B["1F"], cols["1F"])
    rows = his["1F"]["CB12"]
    b_, d_ = rows[0][0], rows[0][1]
    beyond = R.d6((his_beam_len(rows) - D(str(ext))) * b_ * d_)
    out["1F: UNTRACED -> 1F CB12 BEYOND_EXTENT"] = {
        "storey": "1F", "mark": "CB12", "pieces": [p["band"] for p in ps], "detail": ps, "end_supports": ends,
        "outer_face_extent_m": str(R.d6(ext)), "own_delta": str(beyond), "own_m3": str(R.d6(D(str(ext)) * b_ * d_)),
        "engine_m3": str(R.d6(sum((D(str(eng_for("1F", p["band"]))) for p in ps), D(0)))),
        "extent_minus_engine_m3": str(R.d6(R.d6(D(str(ext)) * b_ * d_) -
                                           sum((D(str(eng_for("1F", p["band"]))) for p in ps), D(0)))),
        "ref_m3": str(his_beam_m3(rows)),
        "cause": "his CB12 row is longer than the drawn member between the outer faces of its two end supports"}
    # UPSTANDS: section A-A (B20, GF) and B-B (B23, 1F): L-outline area / scale^2 - schedule b x D, x the west span
    for name, st, sec, bid, mark in (("GF: UPSTAND", "GF", "560", "BAND0043.1", "B20"),
                                     ("1F: UPSTAND", "1F", "16BF", "BAND0031.1", "B23")):
        up = upstand(dw, st, sec, B[st], bid, cols[st])
        out[name] = {"storey": st, "mark": mark + " upstand", "pieces": [f"{bid} upstand"], "detail": [up],
                     "own_m3": up["own_m3"], "ref_m3": "0", "own_delta": str(-D(up["own_m3"])),
                     "cause": f"0.20 x 0.20 upstand drawn on the {mark} section, no row of his"}
    # 1F DOME_RING: west ring B4 (annulus from the raw arcs) inside the bay of the four framing beam faces
    ring = dome_ring(dw)
    out["1F: DOME_RING"] = {"storey": "1F", "mark": "B4 ring", "pieces": ["RING:1F:WEST"], "detail": [ring],
                            "own_m3": ring["own_m3"], "ref_m3": "0", "own_delta": str(-D(ring["own_m3"])),
                            "cause": "ring beam B4 0.20 x 0.50 drawn round the west dome opening (two B4 tags); his "
                                     "dome row is a 0.10 shell plate (T-398), no ring row"}
    for v in out.values():
        for p in v.get("detail", []):
            p.pop("_poly", None)
    return out


def b2_supports(dw, bands, cols, bids):
    """Supports met by the GF B2 pieces: at each piece end, the column outline or carrier band it stops at, its
    extent along the piece axis (own read)."""
    from shapely.geometry import LineString, Point
    out = []
    for bid in bids:
        fa, fb = bands[bid]["faces"]
        a0, a1 = dw.seg("GF", fa)
        b0, b1 = dw.seg("GF", fb)
        q = band_plan(dw, "GF", bands, bid, cols, net=False)
        ux, uy = a1[0] - a0[0], a1[1] - a0[1]
        L = (ux * ux + uy * uy) ** 0.5
        ux, uy = ux / L, uy / L
        ts = [p[0] * ux + p[1] * uy for p in q.exterior.coords]
        t0, t1 = min(ts), max(ts)
        mid_n = sum(p[0] * -uy + p[1] * ux for p in q.exterior.coords) / len(q.exterior.coords)
        for t_end, sgn in ((t0, -1), (t1, 1)):
            probe = Point(ux * (t_end + sgn * 0.02) - uy * mid_n, uy * (t_end + sgn * 0.02) + ux * mid_n)
            hit = [(h, c) for h, c in cols.items() if c.distance(probe) < TOUCH_M]
            if not hit:                               # the band's faces run over a column at this end
                endzone = q.intersection(R.axis_strip((ux, uy), t_end - 0.02, t_end + 0.02))
                hit = [(h, c) for h, c in cols.items() if c.intersection(endzone).area > 1e-6]
            if hit:
                h, c = hit[0]
                cs = [p[0] * ux + p[1] * uy for p in c.exterior.coords]
                out.append({"piece": bid, "end": "start" if sgn < 0 else "end", "support": f"column {h}",
                            "extent_m": str(R.d6(max(cs) - min(cs)))})
                continue
            carrier = [k for k, v in bands.items() if k != bid and v["parent"] != bands[bid]["parent"] and
                       __import__("shapely.geometry", fromlist=["Polygon"]).Polygon(v["polygon"]).buffer(0)
                       .distance(probe) < TOUCH_M]
            if carrier:
                cp = __import__("shapely.geometry", fromlist=["Polygon"]).Polygon(bands[carrier[0]]["polygon"])
                seg = LineString([(ux * (t_end - 5 * sgn * -1) - uy * mid_n, uy * (t_end - 5 * sgn * -1) + ux * mid_n),
                                  (ux * t_end - uy * mid_n, uy * t_end + ux * mid_n)])
                w = seg.intersection(cp.buffer(0)).length
                out.append({"piece": bid, "end": "start" if sgn < 0 else "end",
                            "support": f"carrier {carrier[0]} ({bands[carrier[0]]['mark']})", "extent_m": str(R.d6(w)),
                            "carrier_width_m": str(R.d6(carrier_w(dw, bands[carrier[0]])))})
            else:
                out.append({"piece": bid, "end": "start" if sgn < 0 else "end", "support": "none (open end)",
                            "extent_m": "0"})
    return out


def carrier_w(dw, b):
    """Drawn width of a carrier band: face separation (straight) or ring width (arc faces, radius difference)."""
    if b["kind"] == "STRAIGHT":
        (a0, a1), (b0, _) = dw.seg("GF", b["faces"][0]), dw.seg("GF", b["faces"][1])
        ux, uy = a1[0] - a0[0], a1[1] - a0[1]
        ln = (ux * ux + uy * uy) ** 0.5
        return abs((b0[0] - a0[0]) * -uy / ln + (b0[1] - a0[1]) * ux / ln)
    r = [dw.ent(h).dxf.radius * dw.um for h in b["faces"]]
    return abs(r[0] - r[1])


def cb12_extent(dw, bands, cols):
    """1F CB12 outer-face extent: from the far face of the support at one end to the far face of the support at
    the other, along the axis of faces 5DE / 5DF (own read)."""
    from shapely.geometry import Point
    fa, fb = bands["BAND0018.1"]["faces"]
    a0, a1 = dw.seg("1F", fa)
    ux, uy = a1[0] - a0[0], a1[1] - a0[1]
    L = (ux * ux + uy * uy) ** 0.5
    ux, uy = ux / L, uy / L
    ts, ns = [], []
    for bid in ("BAND0018.1", "BAND0018.2"):
        for h in bands[bid]["faces"]:
            for p in dw.seg("1F", h):
                ts.append(p[0] * ux + p[1] * uy)
                ns.append(p[0] * -uy + p[1] * ux)
    n_mid = sum(ns) / len(ns)
    t0, t1 = min(ts), max(ts)
    ends, lo, hi = [], t0, t1
    from shapely.geometry import LineString
    axis = LineString([(ux * t0 - uy * n_mid, uy * t0 + ux * n_mid), (ux * t1 - uy * n_mid, uy * t1 + ux * n_mid)])
    for t_end, sgn in ((t0, -1), (t1, 1)):
        # the support at a drawn end: an outline the band axis reaches within 0.5 m of the face extreme
        probe = Point(ux * t_end - uy * n_mid, uy * t_end + ux * n_mid)
        hit = [(h, c) for h, c in cols.items() if c.distance(axis) < TOUCH_M and c.distance(probe) < 0.5]
        if not hit:
            raise R.Refused("CB12 end support not found")
        h, c = min(hit, key=lambda kv: kv[1].distance(probe))
        cs = [p[0] * ux + p[1] * uy for p in c.exterior.coords]
        ends.append({"end": "start" if sgn < 0 else "end", "support": f"column {h}",
                     "extent_m": str(R.d6(max(cs) - min(cs)))})
        if sgn < 0:
            lo = min(lo, min(cs))
        else:
            hi = max(hi, max(cs))
    return hi - lo, ends


def upstand(dw, st, sec_handle, bands, bid, cols):
    """Upstand on a section: the section outline (raw LWPOLYLINE) area at the section scale (base width = the
    schedule width b) minus the schedule b x D; length = the drawn span of the band piece the section cuts."""
    from shapely.geometry import Polygon
    e = dw.ent(sec_handle)
    pts = [tuple(p) for p in e.get_points("xy")]
    poly = Polygon(pts).buffer(0)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    base_w_units = max(xs) - min(xs)
    b = {"B20": D("0.40"), "B23": D("0.45")}[bands[bid]["mark"]]
    depth = D(str(bands[bid]["depth"]))
    scale = D(str(base_w_units)) / b                                  # drawing units per metre on the section
    area = R.d6(D(str(poly.area)) / (scale * scale))
    up_area = R.d6(area - b * depth)
    height = R.d6(D(str(max(ys) - min(ys))) / scale - depth)
    top_w = sorted({round(x, 3) for x in xs})
    span = band_plan(dw, st, bands, bid, cols, net=False)
    u = _axis(dw, st, bands[bid])
    for h, c in cols.items():
        if span.intersection(c).area > OVERLAP_M2:                # the clear span stops at every column face
            cs = [q[0] * u[0] + q[1] * u[1] for q in c.exterior.coords]
            span = span.difference(R.axis_strip(u, min(cs), max(cs)))
    if span.geom_type != "Polygon":
        span = max(span.geoms, key=lambda g: g.area)
    ts = [q[0] * u[0] + q[1] * u[1] for q in span.exterior.coords]
    length = R.d6(max(ts) - min(ts))
    return {"section_outline": sec_handle, "band": bid, "section_area_m2": str(area), "upstand_area_m2": str(up_area),
            "upstand_height_m": str(height), "distinct_x_on_section": len(top_w), "span_m": str(length),
            "own_m3": str(R.d6(up_area * length))}


def dome_ring(dw):
    """West ring B4: radii and centre from the raw arcs (long pair 5FE / 5FF, short arcs 600 .. 603), the bay box from the
    nearest beam-band face on each side of the centre (raw face LINEs of the 1F bands, longer than 1 m), annulus inside the box x
    the B4 schedule depth 0.50."""
    import math
    outer = [dw.ent(h) for h in ("5FE", "5FF")]
    inner = [dw.ent(h) for h in ("600", "601", "602", "603")]
    for a in outer + inner:
        if a.dxftype() != "ARC":
            raise R.Refused("ring arcs")
    c = dw.to_m("1F", outer[0].dxf.center)
    ra, rb = outer[0].dxf.radius * dw.um, inner[0].dxf.radius * dw.um
    r_in, r_out = min(ra, rb), max(ra, rb)
    for a in outer + inner:
        cc = dw.to_m("1F", a.dxf.center)
        assert math.dist(cc, c) < 1e-6
    assert all(abs(a.dxf.radius * dw.um - ra) < 1e-6 for a in outer)
    assert all(abs(a.dxf.radius * dw.um - rb) < 1e-6 for a in inner)
    best = {"W": None, "E": None, "S": None, "N": None}
    faces = {h for b in dw.bands("1F").values() if b["kind"] == "STRAIGHT" for h in b["faces"]}
    for h in sorted(faces):
        e = dw.ent(h)
        p, q = dw.to_m("1F", e.dxf.start), dw.to_m("1F", e.dxf.end)
        if math.dist(p, q) < 1.0:
            continue
        if abs(p[0] - q[0]) < 1e-6 and min(p[1], q[1]) <= c[1] <= max(p[1], q[1]):
            d = p[0] - c[0]
            k = "E" if d > 0 else "W"
            if abs(d) > 1.0 and (best[k] is None or abs(d) < abs(best[k][0])):
                best[k] = (d, e.dxf.handle)
        if abs(p[1] - q[1]) < 1e-6 and min(p[0], q[0]) <= c[0] <= max(p[0], q[0]):
            d = p[1] - c[1]
            k = "N" if d > 0 else "S"
            if abs(d) > 1.0 and (best[k] is None or abs(d) < abs(best[k][0])):
                best[k] = (d, e.dxf.handle)
    box = (c[0] + best["W"][0], c[1] + best["S"][0], c[0] + best["E"][0], c[1] + best["N"][0])
    area = R.annulus_in_box(c, r_in, r_out, box)
    return {"arcs_long": ["5FE", "5FF"], "arcs_short": ["600", "601", "602", "603"], "r_inner_m": str(R.d6(r_in)),
            "r_outer_m": str(R.d6(r_out)), "bay_faces": {k: v[1] for k, v in best.items()},
            "bay_box_m": [str(R.d6(box[2] - box[0])), str(R.d6(box[3] - box[1]))], "ring_plan_m2": str(R.d6(area)),
            "depth_m": "0.5", "own_m3": str(R.beam_volume(area, "0.5"))}


def columns_measure(dw, his):
    rec = json.loads(T394.read_text(encoding="utf-8"))["per_line_engine"]
    out = {}
    cols = {st: dw.outlines(st) for st in ("GF", "1F")}
    B = {st: dw.bands(st) for st in ("GF", "1F")}
    plans = {}
    for st in ("GF", "1F"):
        P = {}
        for bid, b in B[st].items():
            if b["depth"] is None:
                continue
            if b["kind"] == "STRAIGHT":
                try:
                    g = band_plan(dw, st, B[st], bid, cols[st], net=False)
                except R.Refused:
                    continue
                u = _axis(dw, st, b)
                ts = [p[0] * u[0] + p[1] * u[1] for p in g.exterior.coords]
                ends = [g.intersection(R.axis_strip(u, min(ts), min(ts) + 0.02)),
                        g.intersection(R.axis_strip(u, max(ts) - 0.02, max(ts)))]
            else:
                from shapely.geometry import Polygon
                g = Polygon(b["polygon"]).buffer(0)
                ends = [g]
            P[bid] = (g, ends, D(str(b["depth"])), b["mark"])
        plans[st] = P

    def member(st, h):
        c = dw.outline(st, h)
        # a beam frames INTO the column where one of its drawn ends stops on the outline (within 1 cm) or its band runs
        # over the outline (covers >= 10 cm2 of it); a band that only runs alongside a face passes beside it
        fr = sorted({(str(dep), mk) for g, ends, dep, mk in plans[st].values()
                     if g.intersection(c).area > OVERLAP_M2 or any(e.distance(c) < TOUCH_M for e in ends)})
        dmax = max((D(x[0]) for x in fr), default=None)
        return {"handle": h, "A_m2": str(R.d6(c.area)), "framing": [f"{mk} {dp}" for dp, mk in fr],
                "D_ctrl_own_m": None if dmax is None else str(dmax)}

    # COUNT rows: the drawn members of the mark (T-248 / T-394 binding by handle, Checker T-566 34 / 36 REGISTERED),
    # each outline re-read (sides, area, hatch); GF also counted from the tags on the GF column plan (SH12, own read)
    def tags(sheet, mark):
        x0, y0, x1, y1 = dw.G["D"]["sheets"][sheet]["sheet"]["box"]
        out = []
        for e in dw.doc.modelspace().query('TEXT[layer=="S-TEXT"]'):
            p = e.dxf.insert
            if e.dxf.text.strip() == mark and x0 <= p[0] - dw.lo[0] <= x1 and y0 <= p[1] - dw.lo[1] <= y1:
                out.append(e.dxf.handle)
        return sorted(out)

    for name, st, mark in (("columns GF: COUNT C1", "GF", "C1"), ("columns GF: COUNT C2", "GF", "C2"),
                           ("columns 1F: COUNT C3", "1F", "C3")):
        bound = [r["member"].split(":")[1] for r in rec if r["storey"] == st and r["mark"] == mark and ":" in r["member"]]
        ms = []
        for h in bound:
            c = dw.outline(st, h)
            bx = c.bounds
            ms.append({"handle": h, "sides_m": sorted([str(R.d6(bx[2] - bx[0])), str(R.d6(bx[3] - bx[1]))]),
                       "A_m2": str(R.d6(c.area))})
        drawn = len(ms)
        tg = tags("SH12", mark) if st == "GF" else []
        b, c_, h_, n = his["cols"][st][mark]
        unit = R.d6(b * c_ * h_)
        dl = R.count_delta(n, drawn, unit)
        neck = his["cols"]["NECK"].get(mark)
        out[name] = {"storey": st, "mark": mark, "pieces": [m["handle"] for m in ms], "members": ms,
                     "drawn_count": drawn, "column_plan_tags": tg if st == "GF" else "not read (no 1F tag sheet)",
                     "tags_equal_members": (len(tg) == drawn) if st == "GF" else None,
                     "own_m3": str(R.d6(drawn * unit)), "ref_m3": str(R.d6(n * unit)), "own_delta": str(dl),
                     "his_neck_rows_equal_drawn_count": None if neck is None else neck[3] == drawn,
                     "cause": f"his {mark} count on {st} exceeds the drawn {mark} members"}
    # BASE: the two CB5-line columns start at +0.25 (T-287 G1, annex FFL +0.30 - 0.05) not +0.95
    ms = [member("GF", h) for h in ("365", "35F")]
    base = R.d6(sum((D(m["A_m2"]) * (D("0.25") - D("0.95")) for m in ms), D(0)))
    out["columns GF: BASE"] = {"storey": "GF", "mark": "C3 365 / C5 35F", "pieces": ["365 base", "35F base"],
                               "members": ms, "base_m": "0.25 (T-287 G1, cited)", "own_delta": str(base),
                               "own_m3": str(-base), "ref_m3": "0",
                               "cause": "the two CB5-line columns stand on the annex ground beam (base +0.25), 0.70 m "
                                        "below the +0.95 base his uniform height assumes"}
    # GLOBAL_DEPTH: valued, non-CONFLICT members with a settled D_ctrl (the compared set of T-551 / J)
    for st, name in (("GF", "columns GF: GLOBAL_DEPTH"), ("1F", "columns 1F: GLOBAL_DEPTH")):
        mem = [r for r in rec if r["storey"] == st and r["state"] == "VALUED" and r["section_status"] ==
               "DRAWING-CONFIRMED" and r["d_ctrl"] is not None and ":" in r["member"]]
        rows, pairs, agree = [], [], 0
        for r in mem:
            h = r["member"].split(":")[1]
            m = member(st, h)
            m["mark"] = r["mark"]
            m["D_ctrl_record_m"] = str(r["d_ctrl"])
            m["A_record_m2"] = str(R.d6(D(str(r["engine_m3"])) / D(str(r["engine_h"]))))
            ok = m["D_ctrl_own_m"] is not None and D(m["D_ctrl_own_m"]) == D(str(r["d_ctrl"])) and \
                D(m["A_m2"]) == D(m["A_record_m2"])
            agree += ok
            m["agrees"] = ok
            rows.append(m)
            if m["D_ctrl_own_m"] is not None:
                pairs.append((D(m["A_m2"]), D(m["D_ctrl_own_m"])))
        gd = R.global_depth_delta(pairs, HIS_COL_DEPTH)             # sum A x (D - 0.75)  = reference - engine
        out[name] = {"storey": st, "mark": "compared set", "pieces": [f"{m['handle']} depth" for m in rows],
                     "members": rows, "members_agreeing": f"{agree} / {len(rows)}", "own_delta": str(gd),
                     "joint_head_own_m3": str(R.joint_head(pairs)), "own_m3": None, "ref_m3": None,
                     "cause": "his one 0.75 soffit depth against each member's own controlling depth (the deepest "
                              "beam framing in): A x (D_ctrl - 0.75) per member"}
    return out


# ------------------------------------------------------------------------------------------------ build
CLASS = {   # class after the re-measure (proposal for the Checker), by statement row name prefix
    "GF: RUN_COUNT": "ENGINE_RIGHT", "GF: UPSTAND": "ENGINE_RIGHT", "1F: UPSTAND": "ENGINE_RIGHT",
    "1F: DOME_RING": "ENGINE_RIGHT", "columns GF: COUNT C1": "ENGINE_RIGHT", "columns GF: COUNT C2": "ENGINE_RIGHT",
    "columns 1F: COUNT C3": "ENGINE_RIGHT", "columns GF: BASE": "ENGINE_RIGHT",
    "columns GF: GLOBAL_DEPTH": "ENGINE_RIGHT", "columns 1F: GLOBAL_DEPTH": "ENGINE_RIGHT",
}


def build(dxf, workbook):
    dw = Drawing(dxf)
    hb, hc = his_rows(workbook)
    eng = engine_lines()
    meas = beams_measure(dw, hb, eng)
    meas.update(columns_measure(dw, {"cols": hc}))
    st_rows = statement_rows()
    lines = {}
    for sid, rows in st_rows.items():
        unk = [(i, s) for i, s, status in rows if status == "UNKNOWN"]
        out_rows = []
        for i, s in unk:
            name = s["name"]
            key = next((k for k in meas if name.startswith(k) or name == k), None)
            if key is None and "THROUGH_SUPPORT residual" in name:
                out_rows.append(through_support_row(i, s, meas))
                continue
            m = meas[key]
            stmt = D(s["delta"])
            own = D(m["own_delta"])
            drift = R.d6(own - stmt)
            cause = drift_cause(key, m, drift)
            status, _ = R.row_status(own, stmt, drift_cause=cause)
            cls = CLASS.get(key, s["class"])
            if key.startswith(("GF: UNTRACED", "1F: UNTRACED")):
                cls = s["class"]
            out_rows.append({"row": i, "name": name, "statement_class": s["class"], "statement_delta": str(stmt),
                             "own_delta": str(own), "drift": str(drift), "drift_cause": cause,
                             "class": R.check_class(cls), "status": status, "storey": m["storey"],
                             "pieces": m["pieces"], "evidence": {k: v for k, v in m.items()
                                                                  if k not in ("pieces", "storey", "ref_m3")}})
        R.pieces_once(out_rows)
        line_unknown = R.d6(sum((D(s["delta"]) for _, s in unk), D(0)))
        own_total = R.d6(sum((D(r["own_delta"]) for r in out_rows), D(0)))
        causes = {}
        for r in out_rows:
            causes[r["name"]] = (r["class"], r["own_delta"])
        drift_total = R.d6(own_total - line_unknown)
        if drift_total:
            causes_drift = {f"DRIFT (re-measure vs statement) {r['name']}": (r["class"], r["drift"])
                            for r in out_rows if D(r["drift"])}
        else:
            causes_drift = {}
        # the statement's UNKNOWN delta = own deltas - drifts, by named row: re-adds exactly (R-T623-2)
        neg = {k: (c, str(-D(v))) for k, (c, v) in causes_drift.items()}
        R.split_line(line_unknown, {**causes, **neg})
        lines[sid] = {"unknown_rows": len(unk), "statement_unknown_delta_m3": str(line_unknown),
                      "own_unknown_delta_m3": str(own_total), "drift_m3": str(drift_total),
                      "by_class_own": by_class(out_rows), "rows": out_rows}
    return {"schema": "T623_UNKNOWN_ROWS_V1", "rule": R.RULE_ID,
            "candidate": "ARCH_TAKEOFF_V3.0.58 (beam lines = V3.0.57 LINE_INDEX); NOT RELEASED",
            "statement": "T-609 V10 sections_v10 [2] T-545/beams@V10, [3] T-551/columns@V10 (scorecard T-613 rows "
                         "UNKNOWN)",
            "source": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179..) + concrete workbook",
            "sign": "reference - engine (statement sign); own_delta = his rows - own drawn measure",
            "lines": lines,
            "note": "m3 / m2 / m only; handles are raw DXF handles; no coordinate, no row or length of his"}


def by_class(rows):
    out = {}
    for r in rows:
        out[r["class"]] = str(R.d6(D(out.get(r["class"], "0")) + D(r["own_delta"])))
    return out


def drift_cause(key, m, drift):
    if abs(drift) <= R.TOL_M3:
        return None
    if key.startswith("1F: UNTRACED -> 1F CB12"):
        return ("EXTENT_VS_ALLOWANCE: the statement row is his - engine less T-545's THROUGH_SUPPORT allowance; the "
                "own row is his length beyond the drawn outer-face extent; the difference is the part of the "
                "allowance T-545 took beyond the outer faces (engine CB12 line bills a T-229 beyond strip)")
    if key == "GF: RUN_COUNT":
        return "JUNCTION: own face plans vs the ledger runs' junction deductions (R-T610-1 owner by length)"
    return None


def through_support_row(i, s, meas):
    """THROUGH_SUPPORT residual (UNRESOLVED): J re-measured member by member (own A x own D_ctrl); T and the zone
    split are T-545 / T-600 (cited); the row stays UNRESOLVED with T-600's capacity terms, never relabelled."""
    st = "GF" if s["name"].startswith("GF") else "1F"
    gd = meas[f"columns {st}: GLOBAL_DEPTH"]
    j_own = D(gd["joint_head_own_m3"])
    j_stmt = {"GF": D("2.281250"), "1F": D("0.385000")}[st]
    drift = R.d6(j_own - j_stmt)
    status, _ = R.row_status(D(s["delta"]) - drift, D(s["delta"]),
                             drift_cause="J_MEMBER" if abs(drift) > R.TOL_M3 else None)
    return {"row": i, "name": s["name"], "statement_class": s["class"], "statement_delta": s["delta"],
            "own_delta": str(R.d6(D(s["delta"]) - drift)), "drift": str(-drift),
            "drift_cause": None if not drift else "J re-measured differs", "class": "UNRESOLVED",
            "status": "RE-MEASURED (PARTS)", "storey": st, "pieces": [f"J {st}"],
            "evidence": {"J_own_m3": str(j_own), "J_statement_m3": str(j_stmt),
                         "J_members_agreeing": gd["members_agreeing"],
                         "T_m3": {"GF": "2.901714", "1F": "1.593362"}[st],
                         "T_source": "T-545 per-mark THROUGH_SUPPORT (his lengths, private) - cited",
                         "capacity_terms": "T-600 r2 s.2 (zones at HELD / D_ctrl-open columns, OVERLAP, BESIDE, "
                                           "CARRIER_NODE, UNCOVERED, BEYOND) - cited; SHORT stays UNRESOLVED by group",
                         "why_open": "his rows carry no location: which zones his lengths reach is not printed"}}


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    d = build(argv[1], argv[2])
    txt = json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(txt, encoding="utf-8")
    elif "--check" in argv:
        assert JSON_OUT.read_text(encoding="utf-8") == txt, "committed output differs from the rebuild"
    for sid, ln in d["lines"].items():
        print(sid, ln["unknown_rows"], "rows; statement", ln["statement_unknown_delta_m3"], "own",
              ln["own_unknown_delta_m3"], "drift", ln["drift_m3"])
        for r in ln["rows"]:
            print("  ", r["row"], r["status"], r["class"], "stmt", r["statement_delta"], "own", r["own_delta"],
                  "drift", r["drift"], "|", r["name"][:60])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
