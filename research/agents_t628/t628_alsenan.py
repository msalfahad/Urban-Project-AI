"""T-628 development-villa re-measure (research, unwired): the 5 rows of statement V11 T-551/footing-line and the 2 rows
of T-551/lift-walls, each measured again from the structural drawing (R-T628-1 .. 5).

    .work/venv/bin/python -I research/agents_t628/t628_alsenan.py <structural.dxf> <concrete workbook> [--write|--check]

Inputs (read only; decoded into .work/private only, never tracked): Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'
(sha256 9f9d1179..) and the concrete + rebar workbook (his footings sheet and his walls + columns sheet). Own read: every
outline, face, ring and schedule value comes from the raw DXF entities (ezdxf, hex handles) of the FOUNDATION PLAN frame
(the plot polyline 1658 +/- 3 m) and the FT / FTB / SBT schedule inserts; no route G, no engine module. Engine values:
research/agents_t620/out/RECONCILED_STATEMENT_T620.json (sections T-551/footing-line, T-551/lift-walls) and the held
lines of research/agents_t507/out/LINE_INDEX_V3_0_57.json; downgrade record: research/agents_t374/T374_BOUND_DOWNGRADES_V2.json.
Tracked output (out/): handles, m2, m3, depths and classes only; no coordinate, no row, length or count of his.
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import t628_rules as R  # noqa: E402

DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
STATEMENT = ROOT / "research/agents_t620/out/RECONCILED_STATEMENT_T620.json"
LINE_INDEX = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
DOWNGRADES = ROOT / "research/agents_t374/T374_BOUND_DOWNGRADES_V2.json"
OUT = HERE / "out"
JSON_OUT = OUT / "T628_FOOTING_LIFT_ROWS.json"
FOOTING_SHEET, COLUMN_SHEET = "القواعد", "الحوائط + الأعمدة"
HIS_LABEL = {"F.F": "FF", "F.N": "FN", "STB1": "SB1", "STB2": "SB2", "STB3": "SB3", "الشناج المحيط": "BAND"}
PLOT, PLOT_IN = "1658", "1659"                       # S-BOUN outer / inner face of the 0.20 m band (T-065 E1)
PIT_OUT, PIT_IN = "10EB", "10EA"                     # S-BW pit outline / shaft outline
FOUR_LINE = {"10F0": "10F0 10F1 10F2 10F3", "10F8": "10F8 10F9 10FA 10FB", "1100": "1100 1101 1102 1103"}
STRAP_FACES = {"SB1": ("1689", "1B1C"), "SB2": ("1B08", "1B09"), "SB3": ("1B26", "1B27")}
BAND_LINE, F10_LINE, PIT_LINE = "L-6290a9f3d93f38cd46d6", "L-164ae9d338976be9e582", "L-684fcad323adc0c8a267"
D = Decimal


# ------------------------------------------------------------------------------------------------ drawing
class Drawing:
    def __init__(self, dxf):
        import ezdxf
        sha = hashlib.sha256(Path(dxf).read_bytes()).hexdigest()
        if sha != DXF_SHA:
            raise R.Refused(f"drawing sha256 {sha[:8]} is not the ST7757 file of record")
        self.doc = ezdxf.readfile(str(dxf))
        self.msp = self.doc.modelspace()
        pts = list(self.doc.entitydb[PLOT].get_points("xy"))
        self.x0, self.y0 = min(p[0] for p in pts), min(p[1] for p in pts)
        from shapely.geometry import box
        self.frame = box(-3.0, -3.0, (max(p[0] for p in pts) - self.x0) / 1000 + 3.0,
                         (max(p[1] for p in pts) - self.y0) / 1000 + 3.0)

    def m(self, p):
        return ((p[0] - self.x0) / 1000.0, (p[1] - self.y0) / 1000.0)

    def poly(self, h):
        from shapely.geometry import Polygon
        return Polygon([self.m(p) for p in self.doc.entitydb[h].get_points("xy")])

    def seg(self, h):
        e = self.doc.entitydb[h]
        return self.m(e.dxf.start), self.m(e.dxf.end)

    def schedule(self):
        out = {}
        for e in self.msp.query("INSERT"):
            if e.dxf.name in ("FT", "FTB"):
                a = {t.dxf.tag: t.dxf.text for t in e.attribs}
                out[a["FO-TY"]] = {"L": float(a["W"]) / 100, "W": float(a["H"]) / 100, "H": D(a["DEPHT"]) / 100,
                                   "insert": e.dxf.handle}
        return out

    def strap_rows(self):
        out = {}
        for e in self.msp.query("INSERT[name=='SBT']"):
            a = {t.dxf.tag: t.dxf.text for t in e.attribs}
            out.setdefault(a["BEAM"], []).append((float(a["W"]) / 100, float(a["H"]) / 100, e.dxf.handle))
        return out

    def outlines(self):
        """{handle: polygon} of every footing outline in the frame: unit-square F inserts scaled to size, S-FOOTINGS
        polylines (closed, or open where a strap enters: closed across the gap), four-LINE squares."""
        from shapely.geometry import Point, Polygon, box
        out = {}
        for e in self.msp.query("INSERT[name=='F']"):
            c = self.m(e.dxf.insert)
            if self.frame.contains(Point(c)):
                if e.dxf.rotation % 90:
                    raise R.Refused(f"rotated footing insert {e.dxf.handle}")
                sx, sy = abs(e.dxf.xscale) / 2, abs(e.dxf.yscale) / 2      # block F = 1000 x 1000 mm square
                if e.dxf.rotation % 180:
                    sx, sy = sy, sx
                out[e.dxf.handle] = box(c[0] - sx, c[1] - sy, c[0] + sx, c[1] + sy)
        for e in self.msp.query("LWPOLYLINE[layer=='S-FOOTINGS']"):
            pts = [self.m(p) for p in e.get_points("xy")]
            if self.frame.contains(Point(pts[0])):
                out[e.dxf.handle] = Polygon(pts)
        for k, hs in FOUR_LINE.items():
            out[k] = Polygon([self.m(self.doc.entitydb[h].dxf.start) for h in hs.split()])
        for h, g in out.items():
            if not g.is_valid or g.area <= 0:
                raise R.Refused(f"outline {h} invalid")
        return out

    def tags(self):
        from shapely.geometry import Point
        out = []
        for e in self.msp:
            t = e.dxftype()
            if t == "TEXT" and e.dxf.layer == "S-TEXT":
                s = e.dxf.text.strip()
            elif t == "INSERT" and e.dxf.name in ("CF", "F11"):
                s = {"CF": "C/F", "F11": "C11/F11"}[e.dxf.name]
            else:
                continue
            p = self.m(e.dxf.insert)
            if not self.frame.contains(Point(p)):
                continue
            lab = s.split("/")[-1].strip()
            if lab in ("F", "FF", "FN") or (lab.startswith("F") and lab[1:].isdigit()):
                out.append((lab, Point(p), e.dxf.handle))
        return out


def bind(outl, tags, sched):
    """Each tag to one outline: inside it, else the nearest outline within 1.0 m whose drawn size is the tag's row."""
    bound = {h: [] for h in outl}
    for lab, pt, th in tags:
        ins = [h for h, g in outl.items() if g.contains(pt)]
        if len(ins) == 1:
            bound[ins[0]].append((lab, th))
            continue
        row = sched.get(lab)
        cand = sorted((g.distance(pt), h) for h, g in outl.items()
                      if row and g.distance(pt) <= 1.0 and R.size_agrees(g.bounds, row["L"], row["W"]))
        if not cand or (len(cand) > 1 and cand[1][0] - cand[0][0] < 0.1):
            raise R.Refused(f"tag {lab} {th} binds to no single outline")
        bound[cand[0][1]].append((lab, th))
    return bound


# ------------------------------------------------------------------------------------------------ his rows (private)
def his_rows(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    out = {}
    ws = wb[FOOTING_SHEET]
    for r in range(13, ws.max_row + 1):
        lab = ws.cell(r, 1).value
        if lab is None or ws.cell(r, 6).value is None:
            continue
        lab = HIS_LABEL.get(str(lab).strip(), str(lab).strip())
        b, c, h, n, tot = (ws.cell(r, k).value for k in (2, 3, 4, 6, 9))
        unit = R.d6(D(str(b)) * D(str(c)) * D(str(h)))
        if R.d6(unit * n) != R.d6(tot):
            raise R.Refused(f"his row {lab} does not re-add")
        out[lab] = {"dims": (D(str(b)), D(str(c)), D(str(h))), "n": int(n), "unit": unit, "m3": R.d6(tot)}
    ws = wb[COLUMN_SHEET]
    b, c, h, n, tot = (ws.cell(11, k).value for k in (2, 3, 4, 6, 9))
    out["LIFT_WALLS"] = {"dims": (D(str(b)), D(str(c)), D(str(h))), "n": int(n), "m3": R.d6(tot)}
    return out


# ------------------------------------------------------------------------------------------------ build
def build(dxf, workbook):
    from shapely.ops import unary_union
    dr = Drawing(dxf)
    sched, outl = dr.schedule(), dr.outlines()
    bound = bind(outl, dr.tags(), sched)
    his = his_rows(workbook)
    st = {s["section_id"]: s for s in json.loads(STATEMENT.read_text(encoding="utf-8"))["sections"]}
    lines = {ln["line_id"]: ln for ln in json.loads(LINE_INDEX.read_text(encoding="utf-8"))["lines"]}
    dgs = json.loads(DOWNGRADES.read_text(encoding="utf-8"))
    dgs = dgs if isinstance(dgs, list) else next(v for v in dgs.values() if isinstance(v, list))
    union = unary_union(list(outl.values()))

    # R-T628-2: every outline once (pairwise)
    pairs = R.plans_once(outl)
    if pairs:
        raise R.Refused(f"footing outlines overlap: {pairs}")

    # per mark (R-T628-1)
    marks, conflict = {}, []
    for h, tl in bound.items():
        labs = sorted({t for t, _ in tl})
        if len(labs) == 1:
            marks.setdefault(labs[0], []).append(h)
        elif len(labs) > 1:
            conflict.append((h, labs, [th for _, th in tl]))
        else:
            raise R.Refused(f"outline {h} carries no tag")
    pad = {}
    for mk, hs in sorted(marks.items()):
        row = sched[mk]
        stat = {}
        for h in hs:
            others = [g for k, g in outl.items() if k != h]
            stat[h] = R.outline_status(outl[h], others, row["L"], row["W"])
        pad[mk] = {"outlines": sorted(hs), "status": {h: s[0] for h, s in stat.items()},
                   "notch_m2": {h: str(R.d6(s[1])) for h, s in stat.items() if s[0] == "NOTCHED"},
                   "schedule": f"{mk} {row['L']:.2f} x {row['W']:.2f} x {row['H']:.2f} (insert {row['insert']})",
                   "m3": R.mark_volume([(h, outl[h].area) for h in hs], row["H"])}
    pads_total = sum((p["m3"] for p in pad.values()), D(0))

    rows_f = []
    sec = st["T-551/footing-line"]
    srow = {r["source_cause"] + (":" + r["name"].split("HELD ")[1].split(" (")[0] if r["source_cause"] == "HELD"
                                 else ""): r for r in sec["rows"]}

    # row 0 COUNT F3
    f3 = pad["F3"]
    d_cnt = R.count_delta(his["F3"]["n"], len(f3["outlines"]), his["F3"]["unit"])
    s = srow["COUNT"]
    status, drift = R.row_status(d_cnt, s["delta"])
    rows_f.append({"row": 0, "name": s["name"], "statement_class": s["class"], "statement_delta": s["delta"],
                   "own_delta": str(d_cnt), "drift": str(drift), "class": "ENGINE_RIGHT", "status": status,
                   "evidence": {"outlines": f3["outlines"], "tags": sorted(th for h in f3["outlines"]
                                                                          for _, th in bound[h]),
                                "schedule": f3["schedule"], "own_m3": str(f3["m3"]),
                                "drawn_count": len(f3["outlines"]),
                                "cause": "two drawn F3 outlines, each tag bound inside its outline; the reference "
                                         "counts one"}})

    # row 1 HELD F10 + F (CONFLICT)
    (ch, clabs, cth), = conflict
    a = outl[ch].area
    rd_a = R.d6(D(str(sched["F10"]["L"])) * D(str(sched["F10"]["W"])) * sched["F10"]["H"]
                + D(str(sched["F"]["L"])) * D(str(sched["F"]["W"])) * sched["F"]["H"])
    rd_b = R.d6(D(str(round(a, 6))) * max(sched[x]["H"] for x in clabs))
    lo, hi = R.conflict_bound([rd_a, rd_b])
    ln = lines[F10_LINE]
    if (R.d6(ln["held_low"]), R.d6(ln["held_high"])) != (lo, hi):
        raise R.Refused("F10 + F held line bound differs from the own two readings")
    s = srow["HELD:F10 + F outline"]
    own = his["F10"]["m3"]
    status, drift = R.row_status(own, s["delta"], held_by="Q-31 C (owner 2026-10-19: HOLD + RFI)")
    rows_f.append({"row": 1, "name": s["name"], "statement_class": s["class"], "statement_delta": s["delta"],
                   "own_delta": str(own), "drift": str(drift), "class": "HELD", "status": status,
                   "evidence": {"outline": ch, "outline_m2": str(R.d6(a)), "tags": sorted(cth), "labels": clabs,
                                "open_at": "S.B1 faces 1689 / 1B1C (0.70 m gap)",
                                "reading_A_schedule_rows_m3": str(rd_a), "reading_B_outline_deepest_m3": str(rd_b),
                                "held_line": F10_LINE, "held_bound_m3": [str(lo), str(hi)],
                                "reference_position": R.position(own, lo, hi),
                                "register": "ELEMENT_REGISTER footing F10-type CONFLICT (kept CONFLICT)"}})

    # row 2 HELD boundary band (R-T628-4)
    band = dr.poly(PLOT).difference(dr.poly(PLOT_IN))
    in_ftg = band.intersection(union).area
    cl = band.area / 0.20
    free = (band.area - in_ftg) / 0.20
    rng_lo = R.d6(D(str(round(free, 6))) * D("0.20") * D("0.40"))
    rng_hi = R.d6(D(str(round(cl, 6))) * D("0.20") * D("0.60"))
    prov_a = R.d6(D(str(round(free, 6))) * D("0.20") * D("0.60"))
    ln = lines[BAND_LINE]
    dg = [g for g in dgs if BAND_LINE in g.get("line_ids", [])]
    if len(dg) != 1:
        raise R.Refused("band downgrade record not single")
    hb = R.held_bound(ln["held_low"], dg[0]["basis_label"], (rng_lo, rng_hi),
                      "drawing range T-356 R-T356-3 re-measured: free length x 0.20 x 0.40 .. centre line x 0.20 x "
                      "0.60 (typical A-A 20 x 40 vs schedule B.W 20 x 60, Q-28 / RFI-S03)")
    s = srow["HELD:boundary band"]
    own = his["BAND"]["m3"]
    status, drift = R.row_status(own, s["delta"], held_by="Q-28 A PROVISIONAL (section + crossing levels unprinted)")
    rows_f.append({"row": 2, "name": s["name"], "statement_class": s["class"], "statement_delta": s["delta"],
                   "own_delta": str(own), "drift": str(drift), "class": "HELD", "status": status,
                   "evidence": {"faces": [PLOT, PLOT_IN], "band_m2": str(R.d6(band.area)),
                                "centre_line_m": str(R.d6(cl)), "inside_footings_m2": str(R.d6(in_ftg)),
                                "inside_footings_m": str(R.d6(in_ftg / 0.20)), "free_m": str(R.d6(free)),
                                "crossed_outlines": sorted(h for h, g in outl.items()
                                                           if g.intersection(band).area > 1e-9),
                                "owner_provisional_A_m3": str(prov_a), "held_line": BAND_LINE,
                                "held_line_bound_m3": str(R.d6(ln["held_low"])),
                                "downgrade": dg[0]["downgrade_id"] + " " + dg[0]["basis_label"],
                                "quoted_bound": hb, "reference_position": R.position(own, *hb["bound"]),
                                "reference_minus_A_m3": str(R.d6(own - prov_a)),
                                "crossings": "levels of band and footings not printed at the 9 crossings: overlap "
                                             "HELD by name (Q-28), never deducted silently (R-T628-2)"}})

    # row 3 OVERLAP FN notch
    fn = pad["FN"]
    (nh, nm2), = fn["notch_m2"].items()
    owner = [h for h, g in outl.items() if h != nh and g.intersection(
        __import__("shapely.geometry", fromlist=["box"]).box(*outl[nh].bounds).difference(outl[nh])).area > 1e-6]
    ref = his["FN"]["m3"]
    d_fn = R.d6(ref - fn["m3"])
    s = srow["OVERLAP"]
    status, drift = R.row_status(d_fn, s["delta"])
    rows_f.append({"row": 3, "name": s["name"], "statement_class": s["class"], "statement_delta": s["delta"],
                   "own_delta": str(d_fn), "drift": str(drift), "class": "ENGINE_RIGHT", "status": status,
                   "evidence": {"outlines": fn["outlines"], "notched": nh, "notch_m2": nm2,
                                "notch_owner": owner, "owner_mark": "F9", "own_FN_m3": str(fn["m3"]),
                                "notch_m3": str(R.d6(D(nm2) * sched["FN"]["H"])), "schedule": fn["schedule"]}})

    # row 4 LENGTH straps (R-T628-3)
    srows = dr.strap_rows()
    straps, own_s, ref_s = {}, D(0), D(0)
    for mk, (fa, fb) in STRAP_FACES.items():
        A, B = dr.seg(fa), dr.seg(fb)
        from shapely.geometry import LineString, Point
        w = (LineString(A).distance(Point(B[0])) + LineString(A).distance(Point(B[1]))) / 2
        sel = R.strap_section([r[:2] for r in srows[mk]], w)
        ins = [r[2] for r in srows[mk] if r[:2] == sel]
        ax = R.strap_axis(A, B)
        L = R.strap_clear_length(ax, union)
        v = R.strap_volume(sel[0], sel[1], L)
        joined = sorted(h for h, g in outl.items() if g.intersects(ax))
        straps[mk] = {"faces": [fa, fb], "drawn_width_m": str(R.d6(w)), "schedule_rows": len(srows[mk]),
                      "schedule_inserts": sorted(r[2] for r in srows[mk]), "selected": ins[0],
                      "section_m": [str(sel[0]), str(sel[1])], "clear_axis_m": str(R.d6(L)), "joins": joined,
                      "own_m3": str(v)}
        own_s += v
        ref_s += his[mk]["m3"]
    eng_s = R.d6(D(sec["engine_valued"]) - pads_total)
    s = srow["LENGTH"]
    d_len = R.d6(ref_s - own_s)
    rounding = R.d6(own_s - eng_s)
    status, drift = R.row_status(d_len, s["delta"])
    rows_f.append({"row": 4, "name": s["name"], "statement_class": s["class"], "statement_delta": s["delta"],
                   "own_delta": str(d_len), "drift": str(drift), "class": "ENGINE_RIGHT", "status": status,
                   "evidence": {"straps": straps, "own_straps_m3": str(own_s), "engine_straps_m3": str(eng_s),
                                "engine_line_rounding_m3": str(rounding)}})

    # beside (no row of his): SB1 piece inside the F10 + F outline, against its held line 0 .. high
    from shapely.geometry import Polygon as _P
    A, B = dr.seg("1689"), dr.seg("1B1C")
    piece = _P([A[0], A[1], B[1], B[0]]).buffer(0).intersection(outl[ch])
    colp = {}
    for e in dr.msp.query("LWPOLYLINE[layer=='S-COL.BON']"):
        g = dr.poly(e.dxf.handle)
        if g.is_valid and g.intersection(piece).area > 1e-9:
            colp[e.dxf.handle] = g.intersection(piece).area
    sb1_net = piece.area - sum(colp.values())
    sb1_hi = R.d6(D(str(round(sb1_net, 6))) * D(straps["SB1"]["section_m"][1]))
    sb1_line = next(ln for ln in lines.values() if ln["element_id"] == "HL:STRAP_CONCRETE:SB1:IN_FOOTING:F10_F")
    beside = {"SB1 in F10 + F": {"outline": ch, "piece_m2": str(R.d6(piece.area)),
                                 "column_pieces_m2": {h: str(R.d6(a)) for h, a in sorted(colp.items())},
                                 "net_m2": str(R.d6(sb1_net)), "own_high_m3": str(sb1_hi),
                                 "held_line": sb1_line["line_id"],
                                 "held_line_bound_m3": [str(R.d6(sb1_line["held_low"])),
                                                        str(R.d6(sb1_line["held_high"]))],
                                 "agree_high": abs(sb1_hi - R.d6(sb1_line["held_high"])) <= R.TOL_M3,
                                 "high_diff_m3": str(R.d6(sb1_hi - R.d6(sb1_line["held_high"]))),
                                 "diff_cause": "drawing precision of the strap face end points (0.0001 m order)",
                                 "note": "the column outline owns its plan; low end 0 (level of strap vs F10 + F not "
                                         "printed, HELD with the outline, Q-31 C)"},
              "SB3 in F3": "not re-measured: level model of T-230 (one straight strap, one level), held 0.0295 .. "
                           "0.2683 cited"}

    causes_f = {"COUNT F3 (two drawn outlines)":("ENGINE_RIGHT", rows_f[0]["own_delta"]),
                "HELD F10 + F outline (Q-31 C)": ("HELD", rows_f[1]["own_delta"]),
                "HELD boundary band (Q-28 A provisional)": ("HELD", rows_f[2]["own_delta"]),
                "OVERLAP FN notch owned by F9": ("ENGINE_RIGHT", rows_f[3]["own_delta"]),
                "LENGTH straps clear axis": ("ENGINE_RIGHT", rows_f[4]["own_delta"]),
                "ENGINE LENGTH PRECISION straps (T-231 axis lengths and the line at 4 dp)": ("TOLERANCE", str(rounding))}
    R.split_exact(sec["difference"], causes_f)

    # lift walls (R-T628-5)
    lsec = st["T-551/lift-walls"]
    outer, inner = dr.poly(PIT_OUT), dr.poly(PIT_IN)
    cols = {}
    for e in dr.msp.query("LWPOLYLINE[layer=='S-COL.BON']"):
        g = dr.poly(e.dxf.handle)
        if g.is_valid and g.intersection(outer.difference(inner)).area > 1e-9:
            cols[e.dxf.handle] = g
    gross, colm2, net = R.pit_ring(outer, inner, list(cols.values()))
    hl = his["LIFT_WALLS"]
    his_ring = R.d6(hl["dims"][0] * hl["dims"][1])
    if his_ring != R.d6(gross):
        raise R.Refused("his ring plan is not the drawn gross ring")
    sd = R.scope_double(colm2, hl["dims"][2])
    held = R.d6(hl["m3"] - sd)
    lrows = []
    s0, s1 = lsec["rows"]
    st0, dr0 = R.row_status(sd, s0["delta"])
    lrows.append({"row": 0, "name": s0["name"], "statement_class": s0["class"], "statement_delta": s0["delta"],
                  "own_delta": str(sd), "drift": str(dr0), "class": "ENGINE_RIGHT", "status": st0,
                  "evidence": {"pit_outline": PIT_OUT, "shaft_outline": PIT_IN, "gross_ring_m2": str(R.d6(gross)),
                               "column_outlines_in_ring": sorted(cols),
                               "column_pieces_m2": str(R.d6(colm2)),
                               "pieces_by_column_m2": {h: str(R.d6(g.intersection(outer.difference(inner)).area))
                                                       for h, g in sorted(cols.items())},
                               "owner": "lift necks / columns (R-T394-6); the reference neck rows carry the same "
                                        "four marks"}})
    st1, dr1 = R.row_status(held, s1["delta"], held_by="D-43 (pit depth 'as per lift manufacturer')")
    lrows.append({"row": 1, "name": s1["name"], "statement_class": s1["class"], "statement_delta": s1["delta"],
                  "own_delta": str(held), "drift": str(dr1), "class": "HELD", "status": st1,
                  "evidence": {"net_ring_m2": str(R.d6(net)), "held_line": PIT_LINE,
                               "held_line_bound": [lines[PIT_LINE]["held_low"], lines[PIT_LINE]["held_high"]],
                               "height": "not printed on the foundation plan or any pit section of ST7757 (D-43); "
                                         "the reference uses one uniform height, not a printed pit depth"}})
    causes_l = {"SCOPE_DOUBLE column pieces": ("ENGINE_RIGHT", str(sd)),
                "HELD net ring x height (D-43)": ("HELD", str(held))}
    R.split_exact(lsec["difference"], causes_l)

    # statement fix row (R-T628-4): engine_bounded with the drawing range in place of the unsupported band bound
    eb = sec["engine_bounded"]
    b_old = R.d6(lines[BAND_LINE]["held_low"])
    fix = {"id": "F-T628-1", "section": "T-551/footing-line", "row": rows_f[2]["name"],
           "statement_engine_bounded": [eb["low_at_least"], eb["high"]],
           "corrected_engine_bounded": [str(R.d6(D(eb["low_at_least"]) - b_old + rng_lo)),
                                        str(R.d6(D(eb["high"]) - b_old + rng_hi))],
           "corrected_row_note": "his share INSIDE the drawing range " + f"{rng_lo} .. {rng_hi}" +
                                 f"; {R.d6(own - prov_a)} above the owner's provisional A {prov_a} (Q-28)",
           "why": "the statement quotes the held band line's 7.2204 (60.17 m: one plot side lost, T-065 / T-356), a "
                  "bound the downgrade record marks UNSUPPORTED BASIS; class HELD and the line blank are unchanged; "
                  "low end NOT ESTABLISHED by the pad split (T-356 R-T356-4)"}
    return {
        "schema": "T628_FOOTING_LIFT_ROWS_V1", "rule": R.RULE_ID,
        "candidate": "ARCH_TAKEOFF_V3.0.58 (structural lines = V3.0.57 LINE_INDEX); NOT RELEASED; statement V11 T-620",
        "source": {"drawing": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'", "sha256": DXF_SHA,
                   "frame": "FOUNDATION PLAN (plot polyline 1658 +/- 3 m)",
                   "reference": "freelancer concrete + rebar workbook, footings and walls + columns sheets (private)"},
        "pads": {mk: {**{k: v for k, v in p.items() if k != "m3"}, "m3": str(p["m3"])} for mk, p in pad.items()},
        "pads_total_m3": str(R.d6(pads_total)), "outline_count": len(outl), "overlapping_outline_pairs": 0,
        "lines": {
            "T-551/footing-line": {"engine_m3": sec["engine_valued"], "statement_delta_m3": sec["difference"],
                                   "rows": rows_f, "split": {k: [c, str(R.d6(v))] for k, (c, v) in causes_f.items()},
                                   "beside_zero_components": beside},
            "T-551/lift-walls": {"engine_m3": lsec["engine_valued"], "statement_delta_m3": lsec["difference"],
                                 "rows": lrows, "split": {k: [c, str(R.d6(v))] for k, (c, v) in causes_l.items()}},
        },
        "fix_rows": [fix],
        "note": "own re-measure (worker 1); statuses for the Checker: RE-MEASURED rows DRAWING-CONFIRMED (worker), HELD "
                "rows HELD by name; no quantity of any candidate moved",
    }


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
        print(sid, "engine", ln["engine_m3"], "delta", ln["statement_delta_m3"])
        for r in ln["rows"]:
            print("  ", r["row"], r["status"], r["class"], "stmt", r["statement_delta"], "own", r["own_delta"],
                  "drift", r["drift"], "|", r["name"][:70])
    print("pads", d["pads_total_m3"], "outlines", d["outline_count"])
    print(json.dumps(d["fix_rows"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
