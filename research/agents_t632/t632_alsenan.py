"""T-632 development-villa census (research, unwired): every beam upstand / level-change strip drawn on the GF / 1F / 2F
slab plans of ST7757, drawn extent vs billed extent (R-T632-1 .. 3), and the B20 settlement (Checker F-C-P02-12).

    .work/venv/bin/python -I research/agents_t632/t632_alsenan.py <structural.dxf> [--write|--check]

Input (read only, `.work/private` only, never tracked): Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256
9f9d1179..). Every length is read from raw DXF entities by hex handle (hatch boundaries on S-HAT.BAT, LINEs on the
HIDDEN layer '2', section cut lines and arrows on S-SEC.LINE, section outlines on layer '1', DIMENSION texts). Route G
(as T-610 / T-623 run it) is used only as a locator: band polygons, faces, marks, schedule depth, sheet frames, and the
slab-engine face class of a strip. Tracked output: handles, lengths (m), m3 and classes only; no coordinate.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(ROOT / "research" / "agents_t623"))
sys.path.insert(2, str(ROOT))

import t632_rules as R  # noqa: E402

DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
OUT = HERE / "out" / "T632_UPSTAND_CENSUS.json"
SHEETS = {"GF": "SH06", "1F": "SH04", "2F": "SH02", "GROUND": "SH08"}
HIDDEN_LAYER = "2"           # linetype HIDDEN in the layer table (checked at run time)
HATCH_LAYER = "S-HAT.BAT"
HATCH_ON_BAND = 0.90         # a hatch is ON a band when >= 90 % of its area lies inside the band polygon
# engine / statement billing of upstands (statement V11 rows 'GF: UPSTAND' / '1F: UPSTAND', T-545 R-T545-1; T-623
# re-measured both as 0.20 x 0.20 x 3.000 = 0.120 m3). No other upstand is billed by any line.
BILLED = {("GF", "B20"): {"length_m": "3.000000", "m3": "0.120000", "row": "statement V11 'GF: UPSTAND'"},
          ("1F", "B23"): {"length_m": "3.000000", "m3": "0.120000", "row": "statement V11 '1F: UPSTAND'"}}
D = Decimal


class Drawing:
    def __init__(self, dxf):
        import ezdxf
        sha = hashlib.sha256(Path(dxf).read_bytes()).hexdigest()
        if sha != DXF_SHA:
            raise R.Refused(f"drawing sha256 {sha[:8]} is not the ST7757 file of record")
        import t623_alsenan as T623
        T623.SHEET.update(SHEETS)
        self.T = T623.Drawing(dxf)
        self.doc = self.T.doc
        lt = self.doc.layers.get(HIDDEN_LAYER).dxf.linetype.upper()
        if not lt.startswith("HIDDEN"):
            raise R.Refused(f"layer {HIDDEN_LAYER} is {lt}, not HIDDEN: the above-slab convention is not this one")

    def m(self, st, p):
        return self.T.to_m(st, p)

    def in_sheet(self, st, p):
        x0, y0, x1, y1 = self.T.sheet(st)["sheet"]["box"]
        return x0 <= p[0] - self.T.lo[0] <= x1 and y0 <= p[1] - self.T.lo[1] <= y1


def _axis(poly_pts):
    (x0, y0), (x1, y1) = poly_pts[0], poly_pts[1]
    L = math.hypot(x1 - x0, y1 - y0)
    u = ((x1 - x0) / L, (y1 - y0) / L)
    if u[0] < -1e-9 or (abs(u[0]) < 1e-9 and u[1] < 0):
        u = (-u[0], -u[1])
    return u, (-u[1], u[0])


def _proj(u, pts):
    ts = [p[0] * u[0] + p[1] * u[1] for p in pts]
    return min(ts), max(ts)


def hatch_polys(dw, st):
    from shapely.geometry import Polygon
    out = {}
    for e in dw.doc.modelspace().query(f'HATCH[layer=="{HATCH_LAYER}"]'):
        pts = []
        for p in e.paths:
            if hasattr(p, "vertices"):
                pts += [v[:2] for v in p.vertices]
            else:
                pts += [ed.start for ed in p.edges if hasattr(ed, "start")]
        if len(pts) >= 3 and dw.in_sheet(st, pts[0]):
            out[e.dxf.handle] = Polygon([dw.m(st, p) for p in pts]).buffer(0)
    return out


def hidden_lines(dw, st):
    from shapely.geometry import LineString
    out = {}
    for e in dw.doc.modelspace().query(f'LINE[layer=="{HIDDEN_LAYER}"]'):
        if e.dxf.linetype.upper() not in ("BYLAYER",) and not e.dxf.linetype.upper().startswith("HIDDEN"):
            continue
        if dw.in_sheet(st, e.dxf.start):
            out[e.dxf.handle] = LineString([dw.m(st, e.dxf.start), dw.m(st, e.dxf.end)])
    return out


def cuts(dw, st):
    """Section cut lines (S-SEC.LINE, linetype CENTER) with their letter and view direction (arrow tip)."""
    from shapely.geometry import LineString, Point
    msp = dw.doc.modelspace()
    lines, arrows, letters = {}, [], []
    for e in msp.query('LWPOLYLINE[layer=="S-SEC.LINE"]'):
        pts = list(e.get_points("xyseb"))
        if not dw.in_sheet(st, pts[0]):
            continue
        if e.dxf.linetype.upper() == "CENTER" and len(pts) == 2:
            lines[e.dxf.handle] = LineString([dw.m(st, p[:2]) for p in pts])
        elif len(pts) >= 2:
            tip = min(range(len(pts)), key=lambda i: pts[i][2])            # start width ~0 at the arrow tip
            far = max(range(len(pts)), key=lambda i: math.dist(pts[i][:2], pts[tip][:2]))
            arrows.append((e.dxf.handle, dw.m(st, pts[tip][:2]), dw.m(st, pts[far][:2])))
    for e in msp.query('TEXT[layer=="S-SEC-TEXT"]'):
        if dw.in_sheet(st, e.dxf.insert):
            letters.append((e.dxf.text.strip(), dw.m(st, e.dxf.insert)))
    out = {}
    for h, ln in lines.items():
        near = [a for a in arrows if ln.distance(Point(a[1])) < 0.6 or ln.distance(Point(a[2])) < 0.6]
        views = set()
        for _, tip, far in near:
            v = (tip[0] - far[0], tip[1] - far[1])
            n = math.hypot(*v)
            views.add((round(v[0] / n, 3), round(v[1] / n, 3)))
        ends = [Point(c) for c in ln.coords]
        letter = sorted(letters, key=lambda t: min(Point(t[1]).distance(p) for p in ends))[0][0] if letters else None
        out[h] = {"line": ln, "views": sorted(views), "arrows": sorted(a[0] for a in near), "letter": letter}
    return out


def section_outline(dw, letter):
    """The printed section of 'SECTION X-X': the layer-1 outline nearest above its title; outline in cm by the printed
    dimensions (drawing units per cm = measurement / printed text of every dimension inside the outline's box)."""
    msp = dw.doc.modelspace()
    title = next((e for e in msp.query('TEXT') if e.dxf.text.replace("%%U", "").strip().upper() == f"SECTION {letter}-{letter}"),
                 None)
    if title is None:
        return None
    tx, ty = title.dxf.insert[0], title.dxf.insert[1]
    best = None
    for e in msp.query('LWPOLYLINE[layer=="1"]'):
        pts = [p[:2] for p in e.get_points("xy")]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if min(ys) > ty and min(ys) - ty < 2500 and min(xs) - 1500 < tx < max(xs) + 3000 and len(pts) >= 6:
            d = math.hypot((min(xs) + max(xs)) / 2 - tx, min(ys) - ty)
            if best is None or d < best[0]:
                best = (d, e, pts)
    if best is None:
        return None
    _, e, pts = best
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    dims = []
    for dm in msp.query("DIMENSION"):
        dp = dm.dxf.defpoint
        if min(xs) - 1500 <= dp[0] <= max(xs) + 3500 and min(ys) - 1500 <= dp[1] <= max(ys) + 1500:
            blk = dw.doc.blocks.get(dm.dxf.geometry)
            txt = [v.plain_text() for v in blk if v.dxftype() == "MTEXT"] if blk else []
            if txt and txt[0].strip().replace(".", "").isdigit():
                dims.append((dm.get_measurement(), float(txt[0])))
    # scale from the longest printed dimension; every other printed value must be its measure rounded to the cm
    if not dims:
        raise R.Refused(f"section {letter}-{letter}: no printed dimension")
    meas, val = max(dims)
    k = round(meas / val, 1)
    bad = [(round(m_ / k, 2), v) for m_, v in dims if abs(m_ / k - v) > 0.5]
    if bad:
        raise R.Refused(f"section {letter}-{letter}: printed dimensions disagree with the drawn ones {bad}")
    x0, y0 = min(xs), min(ys)
    return {"handle": e.dxf.handle, "title": title.dxf.handle, "units_per_cm": k,
            "outline_cm": [(round((x - x0) / k, 1), round((y - y0) / k, 1)) for x, y in pts]}


def census(dxf):
    from shapely.geometry import Point, Polygon
    dw = Drawing(dxf)
    out = {"drawing_sha256": DXF_SHA[:8], "rules": R.RULE_ID, "storeys": {}}
    sections = {}
    for st in ("GF", "1F", "2F", "GROUND"):
        B = dw.T.bands(st)
        P = {k: Polygon(v["polygon"]).buffer(0) for k, v in B.items()}
        H, L, C = hatch_polys(dw, st), hidden_lines(dw, st), cuts(dw, st)
        rows = []
        # hidden lines per band, stair series removed
        for bid, b in B.items():
            u, n = _axis(b["polygon"])
            t0b, t1b = _proj(u, b["polygon"])
            par = []
            for h, ln in L.items():
                c = list(ln.coords)
                du = (c[1][0] - c[0][0], c[1][1] - c[0][1])
                if abs(du[0] * n[0] + du[1] * n[1]) > 1e-3 * ln.length:
                    continue
                a, z = _proj(u, c)
                par.append((h, a, z, c[0][0] * n[0] + c[0][1] * n[1]))
            stair = R.tread_series(par)
            ev = []
            for h, hp in H.items():
                ov = hp.intersection(P[bid]).area
                if hp.area > 0 and ov / hp.area >= HATCH_ON_BAND:
                    ev.append({"kind": "HATCH", "handle": h, "interval": _proj(u, list(hp.exterior.coords))})
            for h, a, z, off in par:
                if h in stair or z - a < 0.3:
                    continue
                if P[bid].buffer(0.002).contains(L[h]):
                    ev.append({"kind": "TOP_EDGE", "handle": h, "interval": (a, z), "_off": off})
            crossing = [(h, c) for h, c in C.items() if c["line"].intersects(P[bid])]
            if not ev and not crossing:
                continue
            if st == "GROUND":
                if ev:
                    rows.append({"storey": st, "band": bid, "mark": b["mark"], "class": "OUT_OF_SCOPE",
                                 "evidence": [f"{e['kind']} {e['handle']} {R.d6(e['interval'][1] - e['interval'][0])} m"
                                              for e in ev],
                                 "why": "ground-beam plan: hidden lines inside ground-beam bands, no section prints an "
                                        "upstand; not a slab-level upstand"})
                continue
            ext = R.drawn_extent([{k: v for k, v in e.items() if k != "_off"} for e in ev])
            row = {"storey": st, "band": bid, "mark": b["mark"], "faces": b["faces"], "depth_m": b["depth"],
                   "band_piece_m": str(R.d6(t1b - t0b)), "extent": {k: (str(v) if isinstance(v, D) else v)
                                                                    for k, v in ext.items() if k not in ("t0", "t1")},
                   "stair_series_excluded": sorted(h for h in stair
                                                   if P[bid].buffer(0.002).contains(L[h]))}
            if ext.get("state") == "MEASURED":
                row["extent"]["starts_at_band_end"] = abs(ext["t0"] - R.d6(t0b)) <= R.TOL_M
                row["extent"]["ends_at_band_end"] = abs(ext["t1"] - R.d6(t1b)) <= R.TOL_M
            sec = []
            for h, c in crossing:
                letter = c["letter"]
                if letter not in sections:
                    sections[letter] = section_outline(dw, letter)
                so = sections[letter]
                a = c["line"].intersection(P[bid])
                ct = sum(_proj(u, list(a.coords))) / 2 if not a.is_empty else None
                rec = {"cut": h, "letter": letter, "arrows": c["arrows"], "outline": so and so["handle"],
                       "cut_t_from_band_start_m": str(R.d6(ct - t0b)) if ct is not None else None}
                if so:
                    sw = (max(x for x, _ in so["outline_cm"]) - min(x for x, _ in so["outline_cm"])) / 100
                    rec["section_base_m"] = str(R.d6(sw))
                    from shapely.geometry import Polygon as _Pg
                    rec["section_area_m2"] = str(R.d6(_Pg(so["outline_cm"]).area / 10000))
                    # width of the band in plan
                    bw = P[bid].area / (t1b - t0b)
                    try:
                        up = R.section_take_upstand(so["outline_cm"], bw, b["depth"] or 0)
                    except R.Refused as x:
                        up = {"state": "NOT_THIS_BAND", "why": str(x)}
                    up = {k: (str(v) if isinstance(v, D) else v) for k, v in up.items()}
                    if up.get("state") == "PRESENT" and len(c["views"]) == 1:
                        up["plan_side"] = R.plan_side(up["side"], c["views"][0], n)
                    rec["upstand"] = up
                sec.append(rec)
            row["sections"] = sec
            # where the hidden top edge sits: the upstand lies between it and the face on the printed side
            for e in ev:
                if e["kind"] == "TOP_EDGE":
                    lo_off = min(p[0] * n[0] + p[1] * n[1] for p in b["polygon"])
                    hi_off = max(p[0] * n[0] + p[1] * n[1] for p in b["polygon"])
                    row.setdefault("top_edge_offsets_m", []).append(
                        {"handle": e["handle"], "from_minus_n_face": str(R.d6(e["_off"] - lo_off)),
                         "to_plus_n_face": str(R.d6(hi_off - e["_off"]))})
            # classify
            billed = BILLED.get((st, b["mark"]))
            ups = [s["upstand"] for s in sec if s.get("upstand", {}).get("state") == "PRESENT"]
            if ext.get("state") == "MEASURED" and ups:
                cut_t = next(D(s["cut_t_from_band_start_m"]) + R.d6(t0b) for s in sec
                             if s.get("upstand", {}).get("state") == "PRESENT")
                q = R.upstand_quantity(D(ups[0]["w_m"]), D(ups[0]["h_m"]), ext, cut_t=cut_t,
                                       section_span=(t0b, t1b))
                row["own"] = {k: str(v) for k, v in q.items()}
                if billed:
                    delta = R.d6(D(billed["m3"]) - q["volume_m3"])
                    row["billed"] = billed
                    row["class"] = "ENGINE_RIGHT" if abs(delta) <= R.D("0.001") else "ENGINE_WRONG"
                    row["engine_minus_own_m3"] = str(delta)
                else:
                    row["class"] = "MISSING_LINE"
            elif ev:
                row["class"] = "HELD"
                row["held_why"] = ("level-change hatch on the band; no section printed through this band shows an "
                                   "upstand (cross-section and direction not printed): upstand or dropped band "
                                   "unresolved; billed by no line")
                row["drawn_length_m"] = row["extent"].get("length_m")
            else:
                row["class"] = "NO_UPSTAND_EVIDENCE"
            rows.append(row)
        out["storeys"][st] = rows
    from shapely.geometry import Polygon as _Pg
    out["sections"] = {k: {"outline": v["handle"], "title": v["title"], "units_per_cm": v["units_per_cm"],
                           "area_m2": str(R.d6(_Pg(v["outline_cm"]).area / 10000)),
                           "base_m": str(R.d6((max(x for x, _ in v["outline_cm"]) - min(x for x, _ in v["outline_cm"])) / 100)),
                           "height_m": str(R.d6(max(y for _, y in v["outline_cm"]) / 100))}
                       for k, v in sections.items() if v}
    out["b20_strip"] = strip_record(dw)
    return out


def strip_record(dw):
    """F-C-P02-12: the 0.20 strip drawn north of B20 (GF, faces 2C6 / 2C7) and its 1F twin (faces 5E1 / 5E6)."""
    from shapely.geometry import Point, Polygon
    rec = {}
    for st, bid, cut, arcs in (("GF", "BAND0031", "55A", ("316",)), ("1F", "BAND0013", "76E", ("647",))):
        B = dw.T.bands(st)
        b = B[bid]
        P = Polygon(b["polygon"]).buffer(0)
        u, _n = _axis(b["polygon"])
        t0, t1 = _proj(u, b["polygon"])
        C = cuts(dw, st)
        crossed = cut in C and C[cut]["line"].intersects(P)
        hatched = any(hp.intersection(P).area > 0.01 for hp in hatch_polys(dw, st).values())
        faces = [dw.T.ent(h) for h in b["faces"]]
        above = any(f.dxf.layer == HIDDEN_LAYER for f in faces)
        letter = C[cut]["letter"] if cut in C else None
        so = section_outline(dw, letter) if letter else None
        base = (max(x for x, _ in so["outline_cm"]) - min(x for x, _ in so["outline_cm"])) / 100 if so else None
        slab = dw.T.sheet(st)["slab"]
        face_cls = None
        mid = P.centroid
        for f in slab["faces"]:
            if len(f["polygon"]) < 3:
                continue
            fp = Polygon([dw.T.to_m(st, (p[0] + dw.T.lo[0], p[1] + dw.T.lo[1])) for p in f["polygon"]]).buffer(0)
            if fp.contains(mid):
                face_cls = f"{f['class']} / {f.get('region')}"
        ident = R.strip_identity(above_convention=above, hatched=hatched, crossed_by_section=crossed,
                                 printed_on_section=False if base is not None and base <= 0.45 else None,
                                 outline_continues=bool(arcs))
        rec[st] = {"band": bid, "faces": b["faces"], "face_layers": sorted({f.dxf.layer for f in faces}),
                   "length_m": str(R.d6(t1 - t0)), "width_m": str(R.d6(P.area / (t1 - t0))),
                   "plan_m2": str(R.d6(P.area)), "hatched": hatched, "crossed_by_cut": cut if crossed else None,
                   "section_base_m": str(R.d6(base)) if base is not None else None,
                   "outline_corner_arcs": list(arcs), "slab_engine_face": face_cls, "identity": ident,
                   "billed_by": "no line (slab engine: inside a beam band; beam binder: UNBOUND)",
                   "status": "HELD (thickness of the strip not printed; not an upstand)"}
    return rec


def _json(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str, ensure_ascii=False)


def main(argv):
    dxf = argv[1]
    res = census(dxf)
    txt = _json(res)
    if "--write" in argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(txt + "\n", encoding="utf-8")
    if "--check" in argv:
        if OUT.read_text(encoding="utf-8") != txt + "\n":
            raise SystemExit("committed census differs from the rebuild")
        print("check: rebuild equals committed")
    if "--write" not in argv and "--check" not in argv:
        print(txt)


if __name__ == "__main__":
    main(sys.argv)
