"""T-642 development-villa fix rows (research, unwired; lane S): the Checker T-180 P02 / P04 findings and the four
B10-12 STR.CONC.PARAPET HELD-blank lines.

    bash scripts/agent_env.sh run --tree task-T-642 research/agents_t642/t642_alsenan.py <structural.dxf> [--write]

(a) F-C-P04-1  1F CB12 strip beside column 664 ('billed by no line', Checker +0.024375 .. 0.0275 m3);
(b) F-C-P02-14 GF strip north of column 353 ('in no band', Checker HELD 0.040 .. 0.075 m3);
(c) GF B11 BAND0001 oblique end (Checker ENGINE_WRONG -0.003159 m3);
(d) F-C-P02-13 GF BAND0049 annex corner arc (depth 'unsourced', Checker UNRESOLVED 0.150796 .. 0.282743 m3);
(e) the 4 STR.CONC.PARAPET lines HELD blank in the T-630 table: a named cause each, with the drawn bound beside.

Every geometric value is measured from the DXF entities by handle (ezdxf, own construction) BEFORE the engine figure
is read; the engine side is the candidate LINE (route G rectangle + named T-229 terms, LEDGER_T252 'adds'), never the
band rectangle alone. Inputs (read only): Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179..,
decoded to .work/private only); route G (T-610 helpers, unchanged); LINE_INDEX_V3_0_57; LEDGER_T252; T-229
summary.json (gap / end records); T-610 fix rows; T-319 parapet run ledger; T-328 parapet line binding. Tracked output:
handles, line ids, marks, areas, depths, volumes, verdicts; no coordinate.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT / "research" / "agents_t610", ROOT):
    sys.path.insert(0, str(p))

import t642_rules as R  # noqa: E402
import t610_alsenan as T610  # noqa: E402  (read only)

OUT = HERE / "out"
JSON_OUT = OUT / "T642_FIX_ROWS.json"
MD_OUT = OUT / "T642_FIX_ROWS.md"
DXF_SHA = T610.DXF_SHA
LEDGER = ROOT / "research/agents_t252/LEDGER_T252.csv"
T229 = ROOT / "research/agents_t229/summary.json"
T610_OUT = ROOT / "research/agents_t610/out/T610_BEAM_OVERLAP_CENSUS.json"
T319_RUNS = ROOT / "research/agents_t319/V3_0_23_RUNS_T319.csv"
T328_LINES = ROOT / "research/agents_t328/PARAPET_LINES_V3030.json"
U = 1000.0                       # drawing units per metre
EPS = 1e-9


def r6(x):
    return None if x is None else round(float(x), 6)


# ---------------------------------------------------------------- DXF by handle (drawing metres)
class Dwg:
    def __init__(self, path):
        import ezdxf
        self.doc = ezdxf.readfile(path)

    def e(self, h):
        x = self.doc.entitydb.get(h)
        if x is None:
            raise R.Refused(f"handle {h} absent")
        return x

    def line(self, h):
        x = self.e(h)
        assert x.dxftype() == "LINE", (h, x.dxftype())
        return (x.dxf.start.x / U, x.dxf.start.y / U), (x.dxf.end.x / U, x.dxf.end.y / U)

    def box(self, h):
        x = self.e(h)
        pts = [(p[0] / U, p[1] / U) for p in x.get_points("xy")]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)

    def arc(self, h):
        x = self.e(h)
        return (x.dxf.center.x / U, x.dxf.center.y / U), x.dxf.radius / U, x.dxf.start_angle, x.dxf.end_angle

    def schedule(self, mark):
        for ins in self.doc.modelspace().query("INSERT"):
            if ins.dxf.name == "SBT":
                a = {t.dxf.tag: t.dxf.text for t in ins.attribs}
                if a.get("BEAM") == mark:
                    return ins.dxf.handle, float(a["W"]) / 100.0, float(a["H"]) / 100.0
        raise R.Refused(f"no schedule row for {mark}")

    def block_text(self, insert_h):
        """world position, direction and string of the TEXT inside a mark block INSERT (mark labels drawn as blocks)."""
        ins = self.e(insert_h)
        blk = self.doc.blocks.get(ins.dxf.name)
        texts = [t for t in blk if t.dxftype() == "TEXT"]
        assert len(texts) == 1, insert_h
        t = texts[0]
        th = math.radians(ins.dxf.rotation)
        lx, ly = t.dxf.insert.x * ins.dxf.xscale, t.dxf.insert.y * ins.dxf.yscale
        wx = ins.dxf.insert.x + lx * math.cos(th) - ly * math.sin(th)
        wy = ins.dxf.insert.y + lx * math.sin(th) + ly * math.cos(th)
        return {"block": ins.dxf.name, "text_handle": t.dxf.handle, "text": t.dxf.text, "layer": t.dxf.layer,
                "height_m": t.dxf.height / U, "at": (wx / U, wy / U), "dir_deg": (ins.dxf.rotation + t.dxf.rotation) % 360}


def ys(seg):
    return sorted((seg[0][1], seg[1][1]))


def xs(seg):
    return sorted((seg[0][0], seg[1][0]))


# ---------------------------------------------------------------- route G (engine side)
def engine(dxf):
    G = T610.route_g(dxf)["generic"]
    lines, ledger = T610.load_lines(), T610.load_ledger()
    S = {}
    for st, sid in T610.SHEETS.items():
        members, cols, _ = T610.storey_members(G, sid, st)
        recs, pl = T610.line_members(lines, ledger, members, st)
        S[st] = {"members": members, "cols": cols, "recs": recs, "pl": pl, "slab": T610.slab_panels(G, sid)}
    return S


def shift_from(member_rect, abs_minx, abs_miny):
    """route G sheet frame -> drawing metres: translation fixed by one member's billed rectangle against the drawn
    faces that bound it (asserted again on a second member per storey)."""
    b = member_rect.bounds
    return abs_minx - b[0], abs_miny - b[1]


def to_abs(g, sh):
    from shapely.affinity import translate
    return translate(g, sh[0], sh[1])


def covers(S, st, sh, strip):
    """{line_id: m2 of the strip inside the line's billed plan} (RELEASED lines) and HELD lines' drawn plan."""
    out = {}
    for lid, r in S[st]["recs"].items():
        g = r.get("billed") if r["class"] == "RELEASED" else (r.get("drawn") if r["class"] == "HELD" else None)
        if g is None:
            continue
        a = to_abs(g, sh).intersection(strip).area
        if a > R.EPS_M2:
            out[lid] = a
    return out


def ledger_rows():
    return {r["run"]: r for r in csv.DictReader(LEDGER.open(encoding="utf-8")) if r["status"] != "SUPERSEDED_R2"}


def line_value(S, st, lid):
    return S[st]["recs"][lid]["value_m3"]


# ---------------------------------------------------------------- build
def build(dxf):
    from shapely.geometry import Point, box
    sha = hashlib.sha256(Path(dxf).read_bytes()).hexdigest()
    assert sha == DXF_SHA, sha
    D = Dwg(dxf)
    S = engine(dxf)
    led = ledger_rows()
    t229 = json.loads(T229.read_text(encoding="utf-8"))
    t610 = json.loads(T610_OUT.read_text(encoding="utf-8"))
    out = {"schema": "T642_FIX_ROWS_V1", "rules_applied": list(R.RULES), "new_rule": None,
           "candidate": "ARCH_TAKEOFF_V3.0.57 line index (= V3.0.58 for STR.CONC.BEAM / STR.CONC.PARAPET)",
           "source": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179..)", "items": {}}

    # ---- frames (route G sheet metres -> drawing metres), each fixed by one member and checked on a second
    f1 = D.line("5DF")
    c664 = D.box("664")
    sh1 = shift_from(S["1F"]["members"]["BAND0018.1"]["rect"], xs(f1)[0], D.box("69D")[3])
    chk1 = to_abs(S["1F"]["members"]["BAND0018.2"]["rect"], sh1).bounds
    assert abs(chk1[1] - c664[3]) < 1e-4 and abs(chk1[3] - D.box("676")[1]) < 1e-4, chk1
    f28f, f428 = D.line("28F"), D.line("428")
    sh0 = shift_from(S["GF"]["members"]["BAND0030.1"]["rect"], xs(D.line("2B2"))[0], 0.0)
    b30 = S["GF"]["members"]["BAND0030.1"]["rect"].bounds
    sh0 = (sh0[0], D.box("353")[1] - b30[3])
    chk0 = to_abs(S["GF"]["members"]["BAND0001"]["rect"], sh0).bounds
    assert abs(chk0[0] - xs(f28f)[0]) < 1e-4 and abs(chk0[3] - ys(f428)[1]) < 1e-4, chk0
    out["frames"] = {"1F": "route G SH04 fixed on CB12 BAND0018.1 (5DF / 69D), checked on BAND0018.2 (664 / 676)",
                     "GF": "route G SH06 fixed on B4 BAND0030.1 (2B2 / 353), checked on B11 BAND0001 (28F / 428)"}

    # ================================================================ (a) 1F CB12 strip beside column 664
    e1, f6d2, f6d3 = D.line("5DE"), D.line("6D2"), D.line("6D3")
    assert ys(f1)[0] < c664[1] and ys(f1)[1] > c664[3], "5DF must run on past column 664"
    width = abs(xs(e1)[0] - xs(f1)[0])
    proj = c664[0] - xs(f1)[0]                              # beam face to column face: the projecting strip width
    gap = box(xs(f1)[0], c664[1], c664[0], c664[3])          # beside the column, inside the drawn beam width
    b6 = box(xs(f1)[0], min(f6d2[0][1], f6d3[0][1]), c664[0], max(f6d2[0][1], f6d3[0][1]))
    assert abs(max(f6d2[0][0], f6d2[1][0]) - c664[0]) < 1e-6, "B6 face 6D2 ends on the column face"
    strip = gap.difference(b6)
    cv = covers(S, "1F", sh1, strip)
    cv_sq = covers(S, "1F", sh1, b6)
    lid_a = S["1F"]["pl"]["BAND0018.1"]
    row = led["BM-1F-017#BAND0018.1"]
    gap229 = next(g for g in t229["gaps"] if g.get("a") == "1F:BAND0018.1" and g.get("b") == "1F:BAND0018.2")
    rect_m3 = float(row["released_m3"])
    term = {"T-229 SUPPORT_CUT_BESIDE (gap 1F:BAND0018.1|BAND0018.2, column 664)": gap229["short_m3"]}
    # the T-229 term region rebuilt: the gap between the two CB12 pieces inside the band width (route G rectangles),
    # net of the column and of every other band's rectangle; the strip must lie in it (R-T624-1 (a))
    r1 = to_abs(S["1F"]["members"]["BAND0018.1"]["rect"], sh1).bounds
    r2 = to_abs(S["1F"]["members"]["BAND0018.2"]["rect"], sh1).bounds
    others = [to_abs(m["rect"], sh1) for k, m in S["1F"]["members"].items() if not k.startswith("BAND0018")]
    from shapely.ops import unary_union
    region = box(r1[0], r1[3], r1[2], r2[1]).difference(box(*c664)).difference(unary_union(others))
    in_region = region.intersection(strip).area
    cv[lid_a] = cv.get(lid_a, 0.0) + in_region
    state, owners = R.owners_of(strip.area, cv)
    d_cb12 = float(row["depth_m"])
    own_m3 = strip.area * d_cb12
    cmp_ = R.compare_with_line(own_m3, line_value(S, "1F", lid_a), rect_m3, term, piece_term=list(term)[0])
    fr4 = next(f for f in t610["fix_rows"] if f["id"] == "FR-T610-4")
    out["items"]["a"] = {
        "finding": "F-C-P04-1 CB12 0.25 wide over column 664 0.20 wide: west 0.05 strip 'billed by no line'",
        "drawn": {"beam_faces": "5DE / 5DF", "beam_width_m": r6(width), "column": "664", "column_width_m": r6(c664[2] - c664[0]),
                  "projecting_strip_width_m": r6(proj), "strip_length_m": r6(c664[3] - c664[1]),
                  "face_5DF_runs_on_past_column": True, "b6_faces": "6D2 / 6D3 end on the column face",
                  "strip_m2": r6(strip.area), "b6_crossing_square_m2": r6(b6.area), "depth_m": d_cb12,
                  "own_m3": r6(own_m3)},
        "engine": {"line_id": lid_a, "run": row["run"], "line_value_m3": line_value(S, "1F", lid_a),
                   "rectangle_m3": rect_m3, "named_terms_m3": {k: r6(v) for k, v in term.items()},
                   "t229_gap_record": {k: gap229[k] for k in ("length_m", "width_m", "area_m2", "support_share",
                                                              "other_beam_share", "beside_m2", "short_m3", "edges_continuous")},
                   "t229_term_region_rebuilt_m2": r6(region.area), "strip_in_term_region_m2": r6(in_region),
                   "decomposition_residual_m3": r6(cmp_["decomposition_residual_m3"]),
                   "other_lines_billing_strip_m2": {k: r6(v) for k, v in cv.items() if k != lid_a},
                   "crossing_square_billed_by": {k: r6(v) for k, v in cv_sq.items()},
                   "crossing_square_depth_fix": f"{fr4['id']} {fr4['pair']} {fr4['engine_minus_physical_m3']} m3 "
                                                f"(MERGED T-610; not again)",
                   "strip_in_slab_panel_m2": r6(to_abs(S["1F"]["slab"], sh1).intersection(strip).area)},
        "owners": owners, "state": state,
        "delta_own_minus_term_m3": r6(cmp_["delta_vs_term_m3"]),
        "checker_view_m3": r6(cmp_["checker_band_view_m3"]),
        "residual_cause": "T-229 gap fitted on the T-110 band plan (width 0.2511 / length 0.8994 / B6 share 0.0573 vs "
                          "drawn 0.250 / 0.900 / 0.0125 m2): beside 0.033018 vs drawn 0.0325 m2 -> +0.000388 m3 in the "
                          "line; within the R-T624-1 named-add tolerance 0.001 m3",
        "verdict": "ENGINE_RIGHT (BILLED_ONCE by the T-229 term in the CB12 run line); F-C-P04-1 not an omission: the "
                   "Checker compared the band rectangle (5.625 m clear) and not the line value 1.079463",
        "fix_row": {"id": "FR-T642-1", "line_id": lid_a, "change_m3": 0.0, "status": "NO_CHANGE (residual named)"}}

    # ================================================================ (b) GF strip north of column 353 (B4 faces run on)
    c353, f2b2, f2b3, f484, f2af = D.box("353"), D.line("2B2"), D.line("2B3"), D.line("484"), D.line("2AF")
    assert abs(ys(f2b2)[1] - f484[0][1]) < 1e-6 and abs(ys(f2b3)[1] - f484[0][1]) < 1e-6, "B4 faces end on 484"
    assert ys(f2b2)[0] < c353[1] and abs(f2af[0][1] - c353[3]) < 1e-6
    strip_b = box(xs(f2b2)[0], c353[3], xs(f2b3)[0], f484[0][1])
    cvb = covers(S, "GF", sh0, strip_b)
    stateb, ownb = R.owners_of(strip_b.area, cvb)
    sch_b4, sch_b7 = D.schedule("B4"), D.schedule("B7")
    assert abs(sch_b4[1] - (xs(f2b3)[0] - xs(f2b2)[0])) < 1e-6
    end229 = [e for e in t229["ends"] if e.get("piece") == "GF:BAND0030.1" and e.get("end") == 1]
    val = R.value_omission(strip_b.area, [
        {"mark": "B4", "depth_m": sch_b4[2], "source": f"faces 2B2 / 2B3 are the B4 run's own LINE entities (CB7 face to "
         f"closing line 484, through column 353); B4 label 508 on that run; schedule SBT {sch_b4[0]}"},
        {"mark": "B7", "depth_m": sch_b7[2], "source": f"the strip is the straight lead-in of the B7 arc (ring width "
         f"0.20 = arc radii 1.30 - 1.10 on the same x as 2B2 / 2B3); arc label INSERT 47D; schedule SBT {sch_b7[0]}"}])
    assert stateb == "BILLED_ONCE" and len(ownb) == 1, (stateb, ownb)
    lid_b = ownb[0]
    rb = S["GF"]["recs"][lid_b]
    idx = {ln["line_id"]: ln for ln in T610.load_lines()}
    lb = idx[lid_b]
    assert lb["class"] == "HELD" and lb["measured_net"] is None
    mb = S["GF"]["members"][rb["own_pieces"][0]]
    out["items"]["b"] = {
        "finding": "F-C-P02-14 strip north of column 353 'in no band' (Checker HELD 0.040 .. 0.075 m3)",
        "drawn": {"faces": "2B2 / 2B3 (single LINE entities through column 353), closing line 484, CB6 north face 2AF / "
                           "column 353 north side", "width_m": r6(xs(f2b3)[0] - xs(f2b2)[0]),
                  "length_m": r6(f484[0][1] - c353[3]), "strip_m2": r6(strip_b.area),
                  "depths_allowed_by_the_drawing": {"B4": sch_b4[2], "B7": sch_b7[2]}},
        "engine": {"lines_carrying_strip_m2": {k: r6(v) for k, v in cvb.items()},
                   "line": {"line_id": lid_b, "element_id": lb["element_id"], "class": lb["class"],
                            "held_low_m3": lb["held_low"], "held_high_m3": lb["held_high"],
                            "route_g_piece": rb["own_pieces"], "route_g_mark": mb["mark"], "route_g_state": mb["state"],
                            "piece_drawn_m2": r6(to_abs(mb["drawn"], sh0).area),
                            "held_range_reads_m": [r6(lb["held_low"] / strip_b.area), r6(lb["held_high"] / strip_b.area)]},
                   "t229_B4_end_at_353": [{k: e.get(k) for k in ("cls", "status", "short_m3")} for e in end229],
                   "strip_in_slab_panel_m2": r6(to_abs(S["GF"]["slab"], sh0).intersection(strip_b).area)},
        "owners": ownb, "state": "CARRIED_ONCE_AS_HELD (unbound route G piece)",
        "value": {k: r6(v) for k, v in val.items() if k != "state"}, "value_state": val["state"],
        "verdict": "NOT an omission: the strip is the unbound route G piece BAND0030.2, carried once by HELD line "
                   f"{lid_b} (range {lb['held_low']} .. {lb['held_high']} m3 = any W20 schedule depth 0.40 .. 1.20); the "
                   "drawing narrows it to B4 0.50 (its faces) .. B7 0.75 (arc lead-in): R-T619-1 low end SET + companion",
        "fix_row": {"id": "FR-T642-2", "line_id": lid_b, "change": f"HELD {lb['held_low']} .. {lb['held_high']} -> SET "
                    f"{r6(val['set_m3'])} m3", "change_m3": r6(val["set_m3"]), "status": "SET (low end, B4 0.50)",
                    "companion": {"element": lb["element_id"] + "~T642_DEPTH_B4_B7",
                                  "held_m3": [0.0, r6(val["companion_high_m3"])],
                                  "cause": "strip depth B4 0.50 (its face entities) vs B7 0.75 (arc lead-in): no mark "
                                           "printed on the strip"}}}

    # ================================================================ (c) GF B11 BAND0001 oblique end
    f427 = D.line("427")

    def y_on(seg, x):
        (x0, y0), (x1, y1) = seg
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    top = ys(f28f)[1]
    e_a = top - y_on(f427, xs(f28f)[0])
    e_b = top - y_on(f427, xs(f428)[0])
    w11 = xs(f428)[0] - xs(f28f)[0]
    sch_b11 = D.schedule("B11")
    trap = w11 * (e_a + e_b) / 2
    own_c = trap * sch_b11[2]
    lid_c = S["GF"]["pl"]["BAND0001"]
    row_c = led["BM-GF-001#BAND0001"]
    end_c = next(e for e in t229["ends"] if e.get("piece") == "GF:BAND0001" and e.get("end") == 0)
    term_c = {"T-229 END_SHORT_OBLIQUE (GF:BAND0001 end 0, B13 face)": end_c["short_m3"]}
    cmp_c = R.compare_with_line(own_c, line_value(S, "GF", lid_c), float(row_c["released_m3"]), term_c)
    out["items"]["c"] = {
        "finding": "GF B11 ENGINE_WRONG -0.003159 m3 (short edge at the oblique end, Verifier 2026-11-08 20:04)",
        "drawn": {"faces": "28F / 428 from column 332 to oblique B13 face 427", "edges_m": [r6(e_a), r6(e_b)],
                  "width_m": r6(w11), "schedule": f"SBT {sch_b11[0]} B11 W {sch_b11[1]} H {sch_b11[2]}",
                  "plan_m2": r6(trap), "own_m3": r6(own_c)},
        "engine": {"line_id": lid_c, "run": row_c["run"], "line_value_m3": line_value(S, "GF", lid_c),
                   "rectangle_m3": float(row_c["released_m3"]), "named_terms_m3": {k: r6(v) for k, v in term_c.items()},
                   "t229_end_record": {k: end_c[k] for k in ("cls", "status", "beyond_area_m2", "beyond_side_t_m", "short_m3")}},
        "delta_own_minus_line_m3": r6(cmp_c["delta_vs_line_m3"]),
        "delta_own_minus_band_rect_m3": r6(cmp_c["delta_vs_band_m3"]),
        "residual_cause": "T-229 end region 0.0046 m2 (side stations 0.0439 / 0.0022 m on the fitted plan) vs drawn "
                          "triangle w x (edge_a - edge_b) / 2; within the 0.001 m3 named-add tolerance",
        "verdict": "ENGINE_RIGHT on the candidate line (the oblique end is billed by the T-229 term); the Checker's "
                   "-0.003159 is against the route G rectangle 0.683110, which is not the line value",
        "fix_row": {"id": "FR-T642-3", "line_id": lid_c, "change_m3": 0.0, "status": "NO_CHANGE (residual named)"}}

    # ================================================================ (d) GF BAND0049 annex corner arc: its printed mark
    (cx, cy), r_out, a0, a1 = D.arc("29F")
    (cx2, cy2), r_in, b0, b1 = D.arc("2A0")
    assert abs(cx - cx2) < 1e-9 and abs(cy - cy2) < 1e-9 and (a0, a1) == (b0, b1)
    sweep = math.radians((a1 - a0) % 360)
    plan_d = sweep / 2 * (r_out ** 2 - r_in ** 2)
    lab = D.block_text("47D")
    lx, ly = lab["at"]
    rho = math.hypot(lx - cx, ly - cy)
    ang = math.degrees(math.atan2(ly - cy, lx - cx)) % 360
    tangent = (ang - 90) % 180
    text_dir = lab["dir_deg"] % 180
    ring = Point(cx, cy).buffer(r_out, 256).difference(Point(cx, cy).buffer(r_in, 256))
    c356 = D.box("356")
    b2_face = D.line("2B9")
    d_ring = Point(lx, ly).distance(ring)
    d_b2 = Point(lx, ly).distance(box(xs(b2_face)[0], b2_face[0][1], c356[0], c356[3]))
    d_cb6 = abs(ly - f2af[0][1])
    sch = D.schedule(lab["text"])
    lid_d = S["GF"]["pl"]["BAND0049"]
    row_d = led["BM-GF-049#BAND0049"]
    own_d = plan_d * sch[2]
    out["items"]["d"] = {
        "finding": "F-C-P02-13 BAND0049 annex NE corner arc: 'no mark printed', B7 0.75 depth unsourced",
        "drawn": {"arcs": "29F / 2A0, sweep %.1f deg" % math.degrees(sweep), "r_out_m": r6(r_out), "r_in_m": r6(r_in),
                  "ring_width_m": r6(r_out - r_in), "plan_m2": r6(plan_d)},
        "printed_mark": {"insert": "47D", **{k: lab[k] for k in ("block", "text_handle", "text", "layer", "height_m")},
                         "angle_on_arc_deg": round(ang, 1), "radius_of_label_m": r6(rho),
                         "outside_outer_face_m": r6(rho - r_out), "text_vs_tangent_deg": round(abs(text_dir - tangent), 1),
                         "distance_to_ring_m": r6(d_ring), "distance_to_B2_band_m": r6(d_b2),
                         "distance_to_CB6_face_m": r6(d_cb6),
                         "why_missed": "the label is TEXT 482 inside block 'b7' (INSERT 47D), not a model-space TEXT"},
        "schedule": f"SBT {sch[0]} {lab['text']} W {sch[1]} H {sch[2]} (W = ring width)",
        "own_m3": r6(own_d),
        "engine": {"line_id": lid_d, "run": row_d["run"], "line_value_m3": line_value(S, "GF", lid_d),
                   "rectangle_or_ring_m3": float(row_d["released_m3"]), "mark": row_d["mark"]},
        "delta_own_minus_line_m3": r6(own_d - float(row_d["released_m3"])),
        "verdict": "ENGINE_RIGHT, depth DRAWING-CONFIRMED (the arc's own printed B7 label); UNRESOLVED closes at 0.282743",
        "fix_row": {"id": "FR-T642-4", "line_id": lid_d, "change_m3": 0.0, "status": "NO_CHANGE (depth source named)"}}
    assert sch[1] == round(r_out - r_in, 6)

    # ================================================================ (e) 4 STR.CONC.PARAPET HELD-blank lines
    pl = json.loads(T328_LINES.read_text(encoding="utf-8"))["lines"]
    runs = list(csv.DictReader(T319_RUNS.open(encoding="utf-8")))

    def rng(s):
        a = [float(v) for v in s.split("..")]
        return a[0], a[-1]
    cause = ("PARAPET_RC_MATERIAL: which printed detail governs each run (ST p.14 P1 brick on a 0.30 RC upstand with an "
             "RC cap 'AS PER ARC.', vs the architect's sections drawn cast concrete) is not keyed: designer item, owner "
             "Q-65 C, material HELD; + PARAPET_RC_B_EDGE: roof build-up depth at the edge (D-39) HELD; cap profile "
             "unprinted in the structural set")
    rows_e = []
    for ln in pl:
        rr = [r for r in runs if r["line_id"] == ln["line_id"]]
        floor = sum(float(r["floor_at_least_m3"]) for r in rr)
        allrc = [sum(rng(r["all_rc_printed_part_m3"])[i] for r in rr) for i in (0, 1)]
        inc = sum(float(r["held_increment_m3_per_m_b_edge"]) for r in rr)
        cl = sum(rng(r["centreline_m"])[0] for r in rr), sum(rng(r["centreline_m"])[1] for r in rr)
        held_geom = [r["run"] for r in rr if r["geometry_status"] != "DRAWING-CONFIRMED" or r["h_status"] != "PRINTED"]
        rec = R.class_held_line({"line_id": ln["line_id"], "measured_net": ln["measured_net"]}, cause,
                                {"at_least_m3": r6(floor), "all_rc_printed_part_m3": [r6(allrc[0]), r6(allrc[1])],
                                 "plus_m3_per_m_b_edge": r6(inc)})
        rec.update({"element_id": ln["element_id"], "runs": len(rr), "centreline_m": [r6(cl[0]), r6(cl[1])],
                    "runs_with_held_geometry_or_height": held_geom,
                    "trial_boq_text": f"HELD — {ln['element_id'].split('#')[0]}: material per run (Q-65 C) and edge "
                                      f"build-up (D-39); at least {floor:.3f} m3 RC in every printed alternative"})
        rows_e.append(rec)
    out["items"]["e"] = {"finding": "4 STR.CONC.PARAPET lines HELD blank with no cause in the T-630 table",
                         "classed": f"{len(rows_e)} / 4 HELD_WITH_CAUSE (class B: a named cause; no drawn single figure "
                                    f"exists while the material per run is HELD)",
                         "lines": rows_e,
                         "total_at_least_m3": r6(sum(x["bound_beside"]["at_least_m3"] for x in rows_e)),
                         "note": "the bound is shown beside the blank line, never summed into B10 (UP-QTY-STATUS-001); "
                                 "owner manual method: no parapet concrete row (blockwork 1.00 / 1.80 / 1.00 m) - shown "
                                 "beside, never used"}
    assert len(rows_e) == 4

    # ---- summary of fix rows
    out["fix_rows"] = [out["items"][k]["fix_row"] for k in "abcd"]
    out["b10_effect_m3"] = {"set": r6(val["set_m3"]), "held_companion": [0.0, r6(val["companion_high_m3"])],
                            "replaces_held_range": [lb["held_low"], lb["held_high"]],
                            "checker_items_closed_no_change": ["F-C-P04-1", "GF B11 -0.003159", "F-C-P02-13"]}
    return out


def render_md(d):
    I = d["items"]
    L = ["# T-642 fix rows (generated; research, unwired)", "",
         f"Candidate {d['candidate']}. Source {d['source']}. Rules applied {', '.join(d['rules_applied'])}; no new rule.", "",
         "| item | own (drawing) | candidate line | delta own - line m3 | verdict | fix row |", "|---|---|---|---|---|---|"]
    a, b, c, dd = I["a"], I["b"], I["c"], I["d"]
    L.append(f"| (a) F-C-P04-1 CB12 @ 664 | {a['drawn']['strip_m2']} m2 x {a['drawn']['depth_m']} = {a['drawn']['own_m3']} | "
             f"{a['engine']['line_id']} {a['engine']['line_value_m3']} = {a['engine']['rectangle_m3']} + T-229 "
             f"{list(a['engine']['named_terms_m3'].values())[0]} | {a['delta_own_minus_term_m3']} (vs the term) | {a['verdict'].split(' (')[0]} | "
             f"{a['fix_row']['id']} {a['fix_row']['status']} |")
    L.append(f"| (b) F-C-P02-14 strip N of 353 | {b['drawn']['strip_m2']} m2; B4 0.50 / B7 0.75 | "
             f"{b['engine']['line']['line_id']} HELD {b['engine']['line']['held_low_m3']} .. {b['engine']['line']['held_high_m3']} "
             f"(route G piece {b['engine']['line']['route_g_piece'][0]}) | SET {b['value']['set_m3']} + HELD 0 .. "
             f"{b['value']['companion_high_m3']} | carried once as HELD; range narrowed | {b['fix_row']['id']} |")
    L.append(f"| (c) GF B11 oblique end | {c['drawn']['plan_m2']} m2 x 0.75 = {c['drawn']['own_m3']} | {c['engine']['line_id']} "
             f"{c['engine']['line_value_m3']} = {c['engine']['rectangle_m3']} + T-229 {list(c['engine']['named_terms_m3'].values())[0]} | "
             f"{c['delta_own_minus_line_m3']} | ENGINE_RIGHT | {c['fix_row']['id']} {c['fix_row']['status']} |")
    L.append(f"| (d) F-C-P02-13 BAND0049 arc | {dd['drawn']['plan_m2']} m2 x 0.75 = {dd['own_m3']} | {dd['engine']['line_id']} "
             f"{dd['engine']['rectangle_or_ring_m3']} | {dd['delta_own_minus_line_m3']} | ENGINE_RIGHT (B7 printed: INSERT 47D / "
             f"TEXT 482, {dd['printed_mark']['outside_outer_face_m']} m outside the arc at {dd['printed_mark']['angle_on_arc_deg']} deg) | "
             f"{dd['fix_row']['id']} {dd['fix_row']['status']} |")
    L += ["", "## (e) STR.CONC.PARAPET", "", "| line | element | runs | at least m3 | all-RC printed part m3 | + m3 per m b_edge |",
          "|---|---|---|---|---|---|"]
    for x in I["e"]["lines"]:
        bb = x["bound_beside"]
        L.append(f"| {x['line_id']} | {x['element_id']} | {x['runs']} | {bb['at_least_m3']} | {bb['all_rc_printed_part_m3']} | "
                 f"{bb['plus_m3_per_m_b_edge']} |")
    L += ["", f"Cause (each line): {I['e']['lines'][0]['cause']}", "",
          f"B10 effect: HELD line {d['b10_effect_m3']['replaces_held_range']} -> +{d['b10_effect_m3']['set']} m3 SET (FR-T642-2) + HELD companion 0 .. "
          f"{d['b10_effect_m3']['held_companion'][1]}; closed with no change: "
          f"{', '.join(d['b10_effect_m3']['checker_items_closed_no_change'])}."]
    return "\n".join(L) + "\n"


def main(argv):
    d = build(argv[0])
    s = json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False)
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(s + "\n", encoding="utf-8")
        MD_OUT.write_text(render_md(d), encoding="utf-8")
    print(render_md(d))


if __name__ == "__main__":
    main(sys.argv[1:])
