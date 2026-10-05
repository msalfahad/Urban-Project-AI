"""ALSENAN ROUND 3 - structural rebar truth engine (source -> typed bar set -> occurrence -> geometry -> count -> length
-> D^2/162 -> net kg -> completeness -> BBS). Builds on engine.source.rebar_model; V3b and Round 2 are not touched.

Authorities (ST7757, read in round 3):
  p.8  note 9   development / lap length of starter bars >= 70 D (tension), >= 40 D (compression)
  p.8  note 21  side bars 2 / 3 / 4 Ø12 in beams deeper than 60 cm "according to beam width" (mapping not printed)
  p.8  note 22  cover >= 2.5 cm columns / slabs / beams; >= 7 cm concrete in contact with soil
  p.13 typical isolated footing: bottom long / short bars straight; a separate BOXED-bar cage
  p.14 lift with isolated footing (FF): footing bars drawn as a closed perimeter loop; pit walls 20 cm with
       6Ø12/m + 6Ø16/m, height "as per lift manufacturer recommendations"
  p.16 typical stair steel layout (N.T.S., 0.00 / +2.00 / +4.00, one landing)
  DXF  C-BEAM2 / C-BEAM3 schedule frames: attributes + S-REIN.D bar graphics + split top-bar callouts + '/m'
       stirrup-zone dimensions (one identical TEMPLATE graphic in every frame, spans drawn equal)
Quantity authority is always the source bar definition x the occurrence geometry; kg/m3 is QA only.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

from engine.source import bbs_optimiser as BB
from engine.source import rebar_model as RM

import alsenan_structural_source_v2 as SRC

DRAWING = "ST7757.dxf"
COVER = {
    "COVER-SOIL-70": {"value_mm": 70.0, "kind": "MINIMUM", "applies_to": ["FOOTING", "FOOTING_2_LAYER", "FOOTING_LIFT",
                                                                         "STRAP_BEAM", "GROUND_BEAM", "GROUND_SLAB"],
                      "source": "ST7757.pdf p.8 note 22: concrete in contact with soil >= 7 cm"},
    "COVER-MEMBER-25": {"value_mm": 25.0, "kind": "MINIMUM", "applies_to": ["COLUMN", "BEAM", "CONTINUOUS_BEAM", "SLAB",
                                                                           "LINTEL"],
                        "source": "ST7757.pdf p.8 note 22: columns, slabs and beams >= 2.5 cm"},
    "COVER-STAIR-NOT-SPECIFIED": {"value_mm": None, "kind": "NOT_SPECIFIED", "applies_to": ["STAIR"],
                                  "source": "note 22 names columns, slabs, beams and soil contact only"},
}
LAP = {
    "LAP-TENSION-70D": {"factor": 70, "source": "ST7757.pdf p.8 note 9 (starter bars, tension zones)"},
    "LAP-COMPRESSION-40D": {"factor": 40, "source": "ST7757.pdf p.8 note 9 (starter bars, compression zones)"},
    "STOCK-12M": {"stock_m": BB.STOCK_M, "source": "Urban procurement stock length (OD-V3B-12) - procurement, not "
                                                    "engineering"},
}
SNAP_FRAC = 0.025                 # a drawn bar end within 2.5 % of a drawn span from a support line is AT the support
CB_TEXT_ROW_DY = 250.0            # a schedule label sits at most 250 units above the bar it labels


def _c(rule):
    return COVER[rule]["value_mm"] / 1000.0


def _src(sha, locator, raw, normalised, page=None, **kw):
    return {"drawing": DRAWING, "drawing_sha256": sha, "page": page, "locator": locator, "raw": raw,
            "normalised": normalised, **kw}


def _cnt_abs(n, basis):
    return RM.bar_count("ABSOLUTE_COUNT", int(n), basis=basis)


def _loop(B, H, c):
    return 2 * (B - 2 * c) + 2 * (H - 2 * c)


def _hook135(d):
    return 2 * BB.hook_addition(d, "135_TIE")["addition_m"]


# ===================================================================================================== CB graphics
def cb_graphics(path=SRC.DXF) -> dict:
    """Per C-BEAM insert: support lines, every S-REIN.D bar with its bound label, normalised span coordinates, legs
    (drawn hooks) and the '/m' stirrup-zone dimensions. Units are the frame's drawing units (spans drawn equal)."""
    import ezdxf
    from ezdxf import bbox as BBX
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    ents = [e for e in msp if e.dxftype() in ("LINE", "LWPOLYLINE", "TEXT", "DIMENSION")]
    out = {}
    for bn in ("C-BEAM2", "C-BEAM3"):
        n_sp = int(bn[-1])
        blk = doc.blocks.get(bn)
        wmax = max(e.dxf.insert.x for e in blk if e.dxftype() == "ATTDEF") + 1200.0
        for ins in msp.query(f'INSERT[name=="{bn}"]'):
            x0, y0 = ins.dxf.insert.x, ins.dxf.insert.y
            at = {a.dxf.tag: (a.dxf.text, a.dxf.insert.x - x0, a.dxf.insert.y - y0) for a in ins.attribs}
            name = at["BEAM-NAME"][0]
            inside = []
            for e in ents:
                try:
                    b = BBX.extents([e])
                except Exception:
                    continue
                if b.has_data and x0 - 100 <= b.extmin.x and b.extmax.x <= x0 + wmax and y0 - 150 <= b.extmin.y \
                        and b.extmax.y <= y0 + 4190:
                    inside.append(e)
            sup = sorted({round(e.dxf.start.x - x0, 1) for e in inside if e.dxftype() == "LINE"
                          and e.dxf.layer == "S-LINE.SCH" and abs(e.dxf.start.x - e.dxf.end.x) < 1
                          and min(e.dxf.start.y, e.dxf.end.y) - y0 < 600 and max(e.dxf.start.y, e.dxf.end.y) - y0 > 3500})
            # split bar callouts: count / '%%C' / diameter TEXT fragments on one row (top row and support row)
            frag = sorted([(e.dxf.insert.x - x0, e.dxf.insert.y - y0, e.dxf.text.strip(), e.dxf.handle) for e in inside
                           if e.dxftype() == "TEXT" and e.dxf.layer == "S-TEXT.SCH" and 1700 < e.dxf.insert.y - y0 < 3300],
                          key=lambda f: (round(f[1] / 100), f[0]))
            callouts, cur = [], []
            for f in frag:
                if cur and (f[0] - cur[-1][0] > 1300 or abs(f[1] - cur[-1][1]) > 60):
                    callouts.append(cur)
                    cur = []
                cur.append(f)
            if cur:
                callouts.append(cur)
            labels = []
            for i in range(1, n_sp + 1):
                t = at.get(f"BOT{i}-B")
                if t:
                    labels.append({"tag": f"BOT{i}", "x": t[1], "y": t[2], "count": at[f"BOT{i}-B"][0],
                                   "dia": at[f"BOT{i}-D"][0], "kind": "ATTRIBUTE", "role_hint": "BOTTOM", "span": i})
            for k in (["MID"] if n_sp == 2 else ["MID1", "MID2"]):
                t = at.get(f"{k}-B")
                labels.append({"tag": k, "x": t[1], "y": t[2], "count": t[0], "dia": at[f"{k}-D"][0],
                               "kind": "ATTRIBUTE", "role_hint": "SUPPORT_TOP",
                               "support": 1 if k in ("MID", "MID1") else 2})
            for c in callouts:
                toks = [f[2] for f in sorted(c)]
                if len(toks) == 3 and toks[1].upper() == "%%C" and toks[0].isdigit() and toks[2].isdigit():
                    labels.append({"tag": f"CALLOUT@{round(min(f[0] for f in c))}", "x": min(f[0] for f in c),
                                   "y": min(f[1] for f in c), "count": toks[0], "dia": toks[2], "kind": "LOOSE_CALLOUT",
                                   "role_hint": "TOP", "handles": [f[3] for f in sorted(c)]})
            spans_drawn = [sup[i + 1] - sup[i] for i in range(len(sup) - 1)]

            def u_of(x):
                if len(sup) < 2:
                    return None, False
                j = 0 if x <= sup[0] else len(sup) - 2 if x >= sup[-1] else \
                    max(i for i in range(len(sup) - 1) if sup[i] <= x)
                u = j + (x - sup[j]) / spans_drawn[j]
                k = min(max(int(round(u)), 0), len(sup) - 1)
                adj = [spans_drawn[i] for i in (k - 1, k) if 0 <= i < len(spans_drawn)]
                if abs(x - sup[k]) <= SNAP_FRAC * min(adj):
                    return float(k), True
                return u, False
            bars = []
            for e in inside:
                if e.dxf.layer != "S-REIN.D":
                    continue
                pts = ([(e.dxf.start.x - x0, e.dxf.start.y - y0), (e.dxf.end.x - x0, e.dxf.end.y - y0)]
                       if e.dxftype() == "LINE" else [(p[0] - x0, p[1] - y0) for p in e.get_points()])
                segs = list(zip(pts, pts[1:]))
                horiz = [s for s in segs if abs(s[0][1] - s[1][1]) < 1.0]
                legs = [s for s in segs if abs(s[0][0] - s[1][0]) < 1.0]
                if not horiz:
                    continue
                h = max(horiz, key=lambda s: abs(s[1][0] - s[0][0]))
                xa, xb, yb = min(h[0][0], h[1][0]), max(h[0][0], h[1][0]), h[0][1]
                ua, sa = u_of(xa)
                ub, sb = u_of(xb)
                straddle = [k for k in range(1, len(sup) - 1) if ua < k - 1e-9 and ub > k + 1e-9]
                row = "BOTTOM" if yb < 1700 else ("SUPPORT_ROW" if yb < 2500 else "TOP_ROW")
                geo_role = ("BOTTOM" if row == "BOTTOM" else "SUPPORT_TOP" if straddle else
                            "CONTINUOUS_TOP" if row == "TOP_ROW" else "SPAN_TOP")
                bar = {"handle": e.dxf.handle, "entity": e.dxftype(), "drawn": [round(xa, 1), round(xb, 1), round(yb, 1)],
                       "u_start": ua, "u_end": ub, "start_at_support": sa, "end_at_support": sb, "row": row,
                       "straddles_supports": straddle, "role": geo_role,
                       "legs": [{"x": round(s[0][0], 1), "drawn_length": round(abs(s[1][1] - s[0][1]), 1)} for s in legs],
                       "_cand": [lb for lb in labels if 0.0 <= lb["y"] - yb <= CB_TEXT_ROW_DY and xa - 50 <= lb["x"] <= xb + 50
                                 and (lb["role_hint"] != "SUPPORT_TOP" or lb["support"] in straddle)
                                 and (lb["role_hint"] != "BOTTOM" or geo_role == "BOTTOM")
                                 and (lb["role_hint"] != "TOP" or geo_role != "BOTTOM")]}
                bars.append(bar)
            pairs = sorted(((0 if lb["count"] else 1, abs(lb["x"] - (bar["drawn"][0] + bar["drawn"][1]) / 2), bi, li)
                            for bi, bar in enumerate(bars) for li, lb in enumerate(labels) if lb in bar["_cand"]))
            used_b, used_l = set(), set()
            for _, _, bi, li in pairs:
                if bi in used_b or li in used_l:
                    continue
                used_b.add(bi)
                used_l.add(li)
                lb = labels[li]
                bars[bi].update(label=lb, binding=("ONE_TO_ONE_PRINTED" if lb["count"] else "EMPTY_SCHEDULE_CELL"))
            for bar in bars:
                n_c = len(bar.pop("_cand"))
                if "label" not in bar:
                    bar.update(label=None, binding=f"UNBOUND ({n_c} candidate label(s) taken or none)")
            unbound_labels = [lb for li, lb in enumerate(labels) if li not in used_l and lb["count"]]
            dims = []
            for e in inside:
                if e.dxftype() == "DIMENSION" and "/m" in (e.dxf.text or ""):
                    a_, b_ = e.dxf.defpoint2.x - x0, e.dxf.defpoint3.x - x0
                    dims.append({"handle": e.dxf.handle, "u": sorted([u_of(a_)[0], u_of(b_)[0]])})
            out[name] = {"block": bn, "insert_handle": ins.dxf.handle, "support_lines": sup,
                         "unbound_printed_labels": unbound_labels,
                         "spans_drawn": [round(s, 2) for s in spans_drawn], "bars": sorted(bars, key=lambda b: b["handle"]),
                         "stirrup_zone_dims": sorted(dims, key=lambda d: d["handle"]),
                         "labels": [{k: v for k, v in lb.items()} for lb in labels]}
    sig = {n: tuple((round(b["drawn"][0]), round(b["drawn"][1]), round(b["drawn"][2])) for b in g["bars"])
           for n, g in out.items()}
    fam = defaultdict(list)
    for n, g in out.items():
        fam[(g["block"], sig[n])].append(n)
    return {"frames": out, "template_variants": [sorted(v, key=lambda t: int(t[2:])) for v in fam.values()],
            "finding": "spans are drawn equal in every frame (N.T.S. template, scaled here per real span); most frames "
                       "of one block share one graphic, edited frames (bars moved / added, loose callouts) are bound "
                       "frame by frame"}


def span_split(ua, ub, spans):
    """Physical length of a normalised run [ua, ub]: whole spans covered = CORE (source span attributes); fractional
    pieces = EXTENSION (schematic template proportion x real span)."""
    core = ext = 0.0
    pieces = []
    j = int(math.floor(ua + 1e-9))
    while j < len(spans) and j < ub - 1e-9:
        f = min(ub, j + 1) - max(ua, j)
        if f > 1e-9:
            L = f * spans[j]
            if abs(f - 1.0) < 1e-9:
                core += L
                pieces.append({"span": j + 1, "fraction": 1.0, "kind": "CORE", "m": L})
            else:
                ext += L
                pieces.append({"span": j + 1, "fraction": round(f, 6), "kind": "EXTENSION", "m": L})
        j += 1
    return core, ext, pieces


# ===================================================================================================== builders
class Build:
    def __init__(self, ctx, src=None, defs=None, cbg=None):
        self.ctx = ctx
        self.src = src or SRC.read()
        self.defs = defs or SRC.definitions(self.src)
        self.cbg = cbg or cb_graphics()
        self.sha = self.src["sha256"]
        self.comps, self.pops, self.rc_occ = [], [], []
        self.registers = defaultdict(list)
        d = defaultdict(list)
        for x in self.defs["definitions"]:
            d[(x["element"], x["type"])].append(x)
        self.dmap = d

    def add(self, pop, comps):
        self.comps += comps
        self.pops.append(pop)
        return pop

    def defsrc(self, df, tags, normalised=None):
        raw = {t: df["raw_attributes"].get(t) for t in tags}
        return _src(self.sha, f"{df['block']}:{df['insert_handle']}:{'+'.join(tags)}", raw, normalised or raw,
                    page=df["page"], definition=f"{df['element']} {df['type']}")

    # ------------------------------------------------------------------------------------------- footings
    def footings(self):
        rows = self.ctx["a3"]["footings"]["rows"]
        for i, f in enumerate(rows):
            occ = f"FOOTING:{f['type']}#{i + 1}"
            self.rc_occ.append(occ)
            ft = self.dmap.get(("FOOTING", f["type"]))
            ftb = self.dmap.get(("FOOTING_2_LAYER", f["type"]))
            est = str(f.get("status", "")).startswith("COMPUTED")
            pid = f"POP:{occ}"
            comps = []
            df = (ft or ftb or [None])[0]
            if df is None:
                comps.append(RM.blocked_component(comp_id=f"{pid}|NO_DEFINITION", population_id=pid,
                                                  element_type="FOOTING", occurrence_id=occ, level="FOUNDATION",
                                                  bar_role="ALL", why="no schedule definition",
                                                  source=_src(self.sha, f"plan mark {f.get('mark_key')}", f["type"],
                                                              "NO_DEFINITION")))
                self.add(RM.population(pop_id=pid, element_type="FOOTING", occurrence_id=occ, level="FOUNDATION",
                                       occurrence_state="BLOCKED", components=comps, occurrence_why="NO_DEFINITION"),
                         comps)
                continue
            L, W, D = df["fields"]["L_cm"] / 100, df["fields"]["W_cm"] / 100, df["fields"]["D_cm"] / 100
            c = _c("COVER-SOIL-70")
            occ_src = {"plan_mark": f.get("mark_key"), "status": f.get("status")}
            if ft:
                comps += self._ft(pid, occ, ft[0], L, W, c)
                et = "FOOTING"
            else:
                comps += self._ftb(pid, occ, ftb[0], L, W, D, c, lift=f["type"] == "FF")
                et = "FOOTING_LIFT" if f["type"] == "FF" else "FOOTING_2_LAYER"
            self.add(RM.population(pop_id=pid, element_type=et, occurrence_id=occ, level="FOUNDATION",
                                   occurrence_state="ESTABLISHED" if est else "BLOCKED", components=comps,
                                   source=occ_src, occurrence_why=None if est else
                                   f"REBAR_BLOCKED_CONCRETE_NOT_ESTABLISHED (footing concrete {f.get('status')})"),
                     comps)

    def _ft(self, pid, occ, df, L, W, c):
        out = []
        F = df["fields"]
        for key, role, run, tags in (("short_bars", "BOTTOM_SHORT", W, ("SH-B", "SH-D")),
                                     ("long_bars", "BOTTOM_LONG", L, ("LO-B", "LO-D"))):
            b = F[key]
            out.append(RM.component(
                comp_id=f"{pid}|{role}", population_id=pid, element_type="FOOTING", occurrence_id=occ,
                level="FOUNDATION", bar_role=role, layer="BOTTOM", direction=role.split("_")[1], dia_mm=b["dia_mm"],
                count=_cnt_abs(b["count"], "printed count (FT schedule)"),
                parts=[RM.part("CORE", run - 2 * c, RM.COMPLETE, "straight bar = side - 2 x cover (p.13: bottom "
                                                                  "bars straight)")],
                cover_rule_id="COVER-SOIL-70", source=self.defsrc(df, tags, b),
                formula=f"{b['count']} x ({run:.2f} - 2 x {c:.3f}) m x {b['dia_mm']}^2/162"))
        bx = F["boxed"]["raw_boxed_value"]
        if bx:
            out.append(RM.blocked_component(
                comp_id=f"{pid}|BOXED", population_id=pid, element_type="FOOTING", occurrence_id=occ,
                level="FOUNDATION", bar_role="BOXED_COMPONENT_UNKNOWN_SEMANTICS",
                why=f"BOXED '{bx}' printed; p.13 draws a boxed-bar cage but the meaning of '{bx}' (bars per face / "
                    f"direction / diameter) is not established", source=self.defsrc(df, ("BOXED",), {"raw": bx})))
        else:
            out.append(RM.not_required(comp_id=f"{pid}|BOXED", population_id=pid, element_type="FOOTING",
                                       occurrence_id=occ, level="FOUNDATION", bar_role="BOXED",
                                       why="BOXED cell empty in the schedule row",
                                       source=self.defsrc(df, ("BOXED",), {"raw": ""})))
        return out

    def _ftb(self, pid, occ, df, L, W, D, c, lift=False):
        out = []
        F = df["fields"]
        et = "FOOTING_LIFT" if lift else "FOOTING_2_LAYER"
        top_counts = {}
        for key, layer, dirn, tags in (("TOP_short", "TOP", "SHORT", ("SH-T-B", "SH-T-D")),
                                       ("TOP_long", "TOP", "LONG", ("LO-T-B", "LO-T-D")),
                                       ("BOTTOM_short", "BOTTOM", "SHORT", ("SH-B-B", "SH-B-D")),
                                       ("BOTTOM_long", "BOTTOM", "LONG", ("LO-B-B", "LO-B-D"))):
            b = F[key]
            run = (W if dirn == "SHORT" else L) - 2 * c                # bar length
            dist = (L if dirn == "SHORT" else W) - 2 * c               # distribution width across the bars
            cnt = RM.bar_count("BARS_PER_METRE", b["count"], dist, basis="FTB schedule: bars per metre")
            parts = [RM.part("CORE", run, RM.COMPLETE, "straight bar = side - 2 x cover")]
            out.append(RM.component(
                comp_id=f"{pid}|{layer}_{dirn}", population_id=pid, element_type=et, occurrence_id=occ,
                level="FOUNDATION", bar_role=f"{layer}_{dirn}", layer=layer, direction=dirn, dia_mm=b["dia_mm"],
                count=cnt, parts=parts, cover_rule_id="COVER-SOIL-70", source=self.defsrc(df, tags, b),
                formula=f"n = {cnt['formula']}; length {run:.3f} m; x {b['dia_mm']}^2/162"))
            if layer == "TOP":
                top_counts[dirn] = (cnt, b["dia_mm"], run)
        if lift:
            n = sum(v[0]["verified"] for v in top_counts.values())
            nc = sum(v[0]["convention"] for v in top_counts.values())
            leg = D - 2 * c
            out.append(RM.component(
                comp_id=f"{pid}|TOP_LEGS", population_id=pid, element_type=et, occurrence_id=occ, level="FOUNDATION",
                bar_role="PERIMETER_CLOSURE_LEGS", layer="TOP", direction="BOTH", dia_mm=top_counts["SHORT"][1],
                count={"mode": "ABSOLUTE_COUNT", "verified": n, "convention": nc, "rule_id": "TOP_BAR_COUNT",
                       "formula": "one bar end pair per top bar (both directions)"},
                parts=[RM.part("LEG", 2 * leg, RM.PROVISIONAL, "p.14 draws the footing bars as a closed perimeter "
                                                              "loop: 2 legs x (D - 2 x cover) per top bar - shape from "
                                                              "the typical detail, not dimensioned")],
                cover_rule_id="COVER-SOIL-70", source=_src(self.sha, "ST7757.pdf p.14 DETAIL OF LIFT WITH ISOLATED "
                                                           "FOOTING", "closed loop drawn", "LEG = D - 2c", page=14),
                formula=f"{n} bars x 2 x ({D:.2f} - 2 x {c:.3f}) m"))
            for role, why in (("LIFT_PIT_WALLS", "pit walls 20 cm, 6Ø12/m + 6Ø16/m vertical: wall height 'as per lift "
                                                  "manufacturer recommendations' - not in the source"),
                              ("PIT_WALL_BASE_BARS_2D16", "2Ø16 at each wall base: length follows the pit walls")):
                out.append(RM.blocked_component(comp_id=f"{pid}|{role}", population_id=pid, element_type=et,
                                                occurrence_id=occ, level="FOUNDATION", bar_role=role, why=why,
                                                source=_src(self.sha, "ST7757.pdf p.14", "drawn", "BLOCKED", page=14)))
        else:
            out.append(RM.blocked_component(
                comp_id=f"{pid}|TOP_END_DETAIL", population_id=pid, element_type=et, occurrence_id=occ,
                level="FOUNDATION", bar_role="TOP_LAYER_END_DETAIL",
                why="two-layer footing top mesh: end legs / bends not detailed (p.13 shows a boxed cage for the "
                    "typical footing only)", source=self.defsrc(df, ("BOXED-T",), {"raw": "TOP"})))
        return out

    # ------------------------------------------------------------------------------------------- straps
    def straps(self):
        for s in self.ctx["a3"]["straps"]["rows"]:
            occ = f"STRAP:{s['type']}:{s['mark_key'].split('|')[1]}"
            self.rc_occ.append(occ)
            pid = f"POP:{occ}"
            defs = self.dmap.get(("STRAP_BEAM", s["type"])) or []
            Lc = s.get("length_m")
            c = _c("COVER-SOIL-70")
            if len(defs) != 1:
                cands = []
                for df in defs:
                    F = df["fields"]
                    kg = sum(F[k]["count"] * Lc * RM.kgm(F[k]["dia_mm"]) for k in ("bottom", "top")) if Lc else None
                    cands.append({"insert_handle": df["insert_handle"], "B_cm": F["B_cm"], "H_cm": F["H_cm"],
                                  "raw": df["raw_attributes"], "longitudinal_audit_kg": kg})
                self.registers["STRAP_CONFLICTS"].append({"occurrence": occ, "state":
                                                          "SOURCE_CONFLICT_DUPLICATE_SCHEDULE_KEY", "candidates": cands,
                                                          "selected": None})
                comps = [RM.blocked_component(comp_id=f"{pid}|ALL", population_id=pid, element_type="STRAP_BEAM",
                                              occurrence_id=occ, level="FOUNDATION", bar_role="ALL",
                                              why="SOURCE_CONFLICT_DUPLICATE_SCHEDULE_KEY: two SB2 rows (80x50 / 100x50); "
                                                  "no row is selected", audit_kg=0.0,
                                              source=_src(self.sha, "SBT:" + "/".join(d["insert_handle"] for d in defs),
                                                          [d["raw_attributes"] for d in defs], "CONFLICT", page=10))]
                self.add(RM.population(pop_id=pid, element_type="STRAP_BEAM", occurrence_id=occ, level="FOUNDATION",
                                       occurrence_state="BLOCKED", components=comps,
                                       occurrence_why="SOURCE_CONFLICT_DUPLICATE_SCHEDULE_KEY"), comps)
                continue
            df = defs[0]
            F = df["fields"]
            B, H = F["B_cm"] / 100, F["H_cm"] / 100
            comps = []
            for key, role, tags in (("bottom", "BOTTOM", ("BOT-B", "BOT-D")), ("top", "TOP", ("TOP-B", "TOP-D"))):
                b = F[key]
                comps.append(RM.component(
                    comp_id=f"{pid}|{role}", population_id=pid, element_type="STRAP_BEAM", occurrence_id=occ,
                    level="FOUNDATION", bar_role=role, layer=role, dia_mm=b["dia_mm"],
                    count=_cnt_abs(b["count"], "printed count (SBT)"),
                    parts=[RM.part("CORE", Lc, RM.COMPLETE, "measured clear length between footing faces"),
                           RM.part("ANCHORAGE", None, RM.BLOCKED, "anchorage into the footings",
                                   why="not detailed in the source")],
                    cover_rule_id="COVER-SOIL-70", source=self.defsrc(df, tags, b),
                    formula=f"{b['count']} x {Lc:.3f} m (clear) x {b['dia_mm']}^2/162; anchorage BLOCKED"))
            st = F["stirrups_per_m"]
            cnt = RM.bar_count("BARS_PER_METRE", st["count"], Lc, basis="SBT header STIRRUPS/m")
            comps.append(RM.component(
                comp_id=f"{pid}|STIRRUPS", population_id=pid, element_type="STRAP_BEAM", occurrence_id=occ,
                level="FOUNDATION", bar_role="STIRRUPS", dia_mm=st["dia_mm"], count=cnt, bar_shape="CLOSED_LINK",
                parts=[RM.part("CORE", _loop(B, H, c), RM.COMPLETE, "closed loop 2(B-2c)+2(H-2c), outside dims"),
                       RM.part("HOOK", _hook135(st["dia_mm"]), RM.PROVISIONAL,
                               "PROVISIONAL_HOOK_ALLOWANCE: 2 x 135° (ACI 318-19 Table 25.3.2, edition unverified)")],
                cover_rule_id="COVER-SOIL-70", source=self.defsrc(df, ("STI-B", "D"), st),
                formula=f"{cnt['formula']}; loop {_loop(B, H, c):.3f} m"))
            comps.append(RM.not_required(comp_id=f"{pid}|SIDE_BARS", population_id=pid, element_type="STRAP_BEAM",
                                         occurrence_id=occ, level="FOUNDATION", bar_role="SIDE_BARS",
                                         why=f"depth {F['H_cm']:.0f} cm <= 60 (note 21)"))
            dep = s.get("support_outline_conflicts")
            self.add(RM.population(pop_id=pid, element_type="STRAP_BEAM", occurrence_id=occ, level="FOUNDATION",
                                   occurrence_state="PROVISIONAL" if dep else "ESTABLISHED", components=comps,
                                   source={"plan_mark": s["mark_key"], "length_m": Lc},
                                   occurrence_why=("clear length measured to the face of a footing outline whose size is "
                                                   "a SOURCE_CONFLICT (F / F10)") if dep else None), comps)

    # ------------------------------------------------------------------------------------------- simple beams
    def simple_beams(self):
        for fl, sh in self.ctx["b2a"]["sheets"].items():
            for o in sh["occurrences"]:
                if o["type"].startswith("CB"):
                    continue
                tag = o["tags"][0].split("|")[1] if o["tags"] else "NOTAG"
                occ = f"BEAM:{fl}:{o['type']}:{tag}"
                self.rc_occ.append(occ)
                pid = f"POP:{occ}"
                df = (self.dmap.get(("SIMPLE_BEAM", o["type"])) or [None])[0]
                Ls = (o.get("lengths") or {}).get("SUPPORT_CENTRELINE_LENGTH")
                Lc = (o.get("lengths") or {}).get("CLEAR_FACE_TO_FACE_LENGTH")
                why = None
                if df is None:
                    why = "REBAR_BLOCKED_NO_DEFINITION"
                elif o["state"] != "MEASURED":
                    why = f"REBAR_BLOCKED_OCCURRENCE_NOT_MEASURED ({o['state']})"
                elif not Ls or not Lc:
                    why = "REBAR_BLOCKED_LENGTH_MISSING"
                if why:
                    comps = [RM.blocked_component(comp_id=f"{pid}|ALL", population_id=pid, element_type="BEAM",
                                                  occurrence_id=occ, level=fl, bar_role="ALL", why=why,
                                                  source=_src(self.sha, f"plan tag {o['tags'][:1]}", o["state"], why))]
                    self.add(RM.population(pop_id=pid, element_type="BEAM", occurrence_id=occ, level=fl,
                                           occurrence_state="BLOCKED", components=comps, occurrence_why=why), comps)
                    continue
                F = df["fields"]
                B, H = F["B_cm"] / 100, F["H_cm"] / 100
                c = _c("COVER-MEMBER-25")
                comps = []
                for key, role, tags in (("bottom", "BOTTOM", ("BOT-B", "BOT-D")), ("top", "TOP", ("TOP-B", "TOP-D"))):
                    b = F[key]
                    comps.append(RM.component(
                        comp_id=f"{pid}|{role}", population_id=pid, element_type="BEAM", occurrence_id=occ, level=fl,
                        bar_role=role, layer=role, dia_mm=b["dia_mm"], count=_cnt_abs(b["count"], "printed count (SBT)"),
                        parts=[RM.part("CORE", Lc, RM.COMPLETE, "clear span face to face (measured)"),
                               RM.part("EXTENSION", Ls - Lc, RM.PROVISIONAL, "embedment from the faces to the support "
                                                                             "centrelines (V3a basis, not detailed)"),
                               RM.part("ANCHORAGE", None, RM.BLOCKED, "end anchorage / hooks", why="not detailed")],
                        cover_rule_id="COVER-MEMBER-25", source=self.defsrc(df, tags, b),
                        formula=f"{b['count']} x ({Lc:.3f} verified + {Ls - Lc:.3f} provisional) m x {b['dia_mm']}^2/162"))
                st = F["stirrups_per_m"]
                cnt = RM.bar_count("BARS_PER_METRE", st["count"], Lc, basis="SBT header STIRRUPS/m over the clear span")
                comps.append(RM.component(
                    comp_id=f"{pid}|STIRRUPS", population_id=pid, element_type="BEAM", occurrence_id=occ, level=fl,
                    bar_role="STIRRUPS", dia_mm=st["dia_mm"], count=cnt, bar_shape="CLOSED_LINK",
                    parts=[RM.part("CORE", _loop(B, H, c), RM.COMPLETE, "closed loop 2(B-2c)+2(H-2c)"),
                           RM.part("HOOK", _hook135(st["dia_mm"]), RM.PROVISIONAL, "PROVISIONAL_HOOK_ALLOWANCE 2 x 135°")],
                    cover_rule_id="COVER-MEMBER-25", source=self.defsrc(df, ("STI-B", "D"), st),
                    formula=f"{cnt['formula']}; loop {_loop(B, H, c):.3f} m"))
                rm = F.get("remarks_side_bars")
                if F["H_cm"] > 60:
                    comps.append(RM.blocked_component(
                        comp_id=f"{pid}|SIDE_BARS", population_id=pid, element_type="BEAM", occurrence_id=occ, level=fl,
                        bar_role="SIDE_BARS", why=("REMARKS token '" + rm["raw"] + "' captured; count per face / "
                                                   "levels need the typical detail") if rm else
                        "note 21: depth > 60 cm needs 2/3/4 Ø12 by beam width - mapping not printed",
                        source=_src(self.sha, f"TEXT:{rm['text_handle']}" if rm else "ST7757.pdf p.8 note 21",
                                    rm["raw"] if rm else "note 21", rm.get("grammar") if rm else "RANGE 2..4 Ø12",
                                    page=10 if rm else 8)))
                else:
                    comps.append(RM.not_required(comp_id=f"{pid}|SIDE_BARS", population_id=pid, element_type="BEAM",
                                                 occurrence_id=occ, level=fl, bar_role="SIDE_BARS",
                                                 why=f"depth {F['H_cm']:.0f} cm <= 60 (note 21)"))
                self.add(RM.population(pop_id=pid, element_type="BEAM", occurrence_id=occ, level=fl,
                                       occurrence_state="ESTABLISHED", components=comps,
                                       source={"plan_tags": o["tags"], "Ls_m": Ls, "Lc_m": Lc}), comps)

    # ------------------------------------------------------------------------------------------- continuous beams
    def continuous_beams(self):
        frames = self.cbg["frames"]
        occs = defaultdict(list)
        for fl, sh in self.ctx["b2a"]["sheets"].items():
            for o in sh["occurrences"]:
                if o["type"].startswith("CB"):
                    occs[o["type"]].append((fl, o))
        for df in sorted(self.dmap_all("CONTINUOUS_BEAM"), key=lambda d: int(d["type"][2:])):
            name = df["type"]
            g = frames[name]
            geo = self._cb_geometry(df, g)
            self.registers["CB_GEOMETRY"].append(geo)
            if not occs.get(name):
                self.registers["CB_DEFINITIONS_WITHOUT_OCCURRENCE"].append(
                    {"type": name, "state": "NO_PLAN_OCCURRENCE", "why": "definition read; no tag of this type on the "
                                                                          "GF / 1F / 2F beam plans"})
                continue
            for fl, o in occs[name]:
                self._cb_occurrence(df, geo, fl, o)

    def dmap_all(self, el):
        return [x for (e, _), v in self.dmap.items() if e == el for x in v]

    def _cb_geometry(self, df, g):
        F = df["fields"]
        spans = F["spans_m"]
        rows = []
        for b in g["bars"]:
            lab = b["label"] or {}
            core, ext, pieces = span_split(b["u_start"], b["u_end"], spans)
            rows.append({"handle": b["handle"], "role": b["role"], "row": b["row"],
                         "straddles_supports": b["straddles_supports"], "label_tag": lab.get("tag", "UNBOUND"),
                         "label_kind": lab.get("kind"), "count": lab.get("count", ""), "dia": lab.get("dia", ""),
                         "u_start": round(b["u_start"], 6), "u_end": round(b["u_end"], 6),
                         "start_at_support": b["start_at_support"], "end_at_support": b["end_at_support"],
                         "legs": b["legs"], "pieces": pieces, "core_m": core, "extension_m": ext,
                         "rule": "whole spans between support lines = source span attributes (CORE); fractional "
                                 "template pieces x real span (EXTENSION, schematic)",
                         "confidence": "HIGH (core) / MEDIUM (extension: N.T.S. template, spans drawn equal)",
                         "label_binding": b["binding"], "label_handles": lab.get("handles")})
        return {"type": df["type"], "block": g["block"], "insert_handle": g["insert_handle"],
                "support_lines_drawn": g["support_lines"], "spans_drawn": g["spans_drawn"], "spans_m": spans,
                "bars": rows, "stirrup_zones": g["stirrup_zone_dims"],
                "unbound_printed_labels": g["unbound_printed_labels"]}

    def _cb_occurrence(self, df, geo, fl, o):
        F = df["fields"]
        name = df["type"]
        tag = o["tags"][0].split("|")[1] if o["tags"] else "NOTAG"
        occ = f"CB:{fl}:{name}:{tag}"
        self.rc_occ.append(occ)
        pid = f"POP:{occ}"
        spans = F["spans_m"]
        L = o.get("lengths") or {}
        Ls, Lc = L.get("SUPPORT_CENTRELINE_LENGTH"), L.get("CLEAR_FACE_TO_FACE_LENGTH")
        sched = sum(spans)
        if o["state"] == "MEASURED" and Ls and abs(Ls - sched) / sched <= 0.05:
            ost, why = "ESTABLISHED", f"plan centreline {Ls:.3f} m vs schedule spans {sched:.2f} m (<= 5 %)"
        elif o["state"] == "MEASURED":
            ost, why = "PROVISIONAL", (f"plan length does not confirm the schedule spans (centreline {Ls}, clear {Lc}, "
                                       f"schedule {sched:.2f})")
        else:
            ost, why = "BLOCKED", f"REBAR_BLOCKED_OCCURRENCE_CONFLICT ({o['state']}: {o.get('tags_vs_spans')})"
        B, H = F["B_cm"] / 100, F["H_cm"] / 100
        c = _c("COVER-MEMBER-25")
        support_deduction = (Ls - Lc) if (Ls and Lc) else None
        comps = []
        base = dict(population_id=pid, element_type="CONTINUOUS_BEAM", occurrence_id=occ, level=fl,
                    cover_rule_id="COVER-MEMBER-25")
        for b in geo["bars"]:
            role = b["role"]
            n, d = b["count"], b["dia"]
            span = (int(b["label_tag"][3]) if role == "BOTTOM" and b["label_tag"].startswith("BOT") else
                    "S" + ",".join(map(str, b["straddles_supports"])) if role == "SUPPORT_TOP" else
                    int(math.floor(b["u_start"] + 1e-9)) + 1)
            if b["label_kind"] == "ATTRIBUTE":
                srcd = self.defsrc(df, (f"{b['label_tag']}-B", f"{b['label_tag']}-D"), {"count": n, "dia_mm": d})
            elif b["label_kind"] == "LOOSE_CALLOUT":
                srcd = _src(self.sha, f"{df['block']}:{df['insert_handle']}:TEXT:{'+'.join(b['label_handles'])}",
                            f"{n} %%C {d} (split TEXT fragments)", {"count": n, "dia_mm": d}, page=df["page"],
                            binding="count / Ø / diameter fragments on one row directly above the drawn bar")
            else:
                srcd = _src(self.sha, f"{df['block']}:{df['insert_handle']}:GEOM:{b['handle']}", "drawn bar, no label",
                            "UNBOUND", page=df["page"])
            srcd["geometry_handle"] = b["handle"]
            cid = f"{pid}|{role}|{span}|{b['handle']}"
            if not (str(n).isdigit() and str(d).isdigit()):
                comps.append(RM.blocked_component(comp_id=cid, bar_role=role,
                                                  why=f"bar drawn ({role}); count / diameter not printed "
                                                      f"({b['label_binding']}: {b['label_tag']})", source=srcd,
                                                  **{k: v for k, v in base.items() if k != "cover_rule_id"}))
                comps[-1].update(span=span, layer="TOP" if role != "BOTTOM" else "BOTTOM")
                continue
            n, d = int(n), int(d)
            parts = []
            if b["core_m"] > 0:
                parts.append(RM.part("CORE", b["core_m"], RM.COMPLETE, "whole spans between support lines (schedule "
                                                                      "span attributes)"))
            if b["extension_m"] > 0:
                parts.append(RM.part("EXTENSION", b["extension_m"], RM.PROVISIONAL,
                                     "schedule-graphic template proportion x real span (N.T.S.)"))
            if b["legs"]:
                parts.append(RM.part("HOOK", None, RM.BLOCKED, "drawn hook / leg at the end support",
                                     why=f"{len(b['legs'])} leg(s) drawn, length not dimensioned"))
            if role == "BOTTOM" and (b["u_start"] == 0.0 or b["u_end"] == float(len(spans))):
                parts.append(RM.part("ANCHORAGE", None, RM.BLOCKED, "end anchorage into the end support",
                                     why="drawn to the support line only; anchorage not detailed"))
            comps.append(RM.component(
                comp_id=cid, bar_role=role, layer="BOTTOM" if role == "BOTTOM" else "TOP", span=span, dia_mm=d,
                count=_cnt_abs(n, "printed count"), parts=parts, source=srcd, interpretation_state="GRAPHIC_BOUND",
                laps=RM.lap_parts(b["core_m"] + b["extension_m"], d),
                formula=f"{n} x ({b['core_m']:.3f} core + {b['extension_m']:.3f} template) m x {d}^2/162", **base))
        for i, st in enumerate(F["stirrups_per_span"]):
            Lj = spans[i]
            zone_lb = max(Lj - support_deduction, 0.0) if support_deduction is not None else None
            cnt = RM.bar_count("BARS_PER_METRE", st["count"], zone_lb if zone_lb is not None else Lj,
                               basis="'/m' dimension spans support line to support line")
            if zone_lb is not None:
                conv = RM.bar_count("BARS_PER_METRE", st["count"], Lj)["convention"]
                cnt = dict(cnt, convention=conv, formula=cnt["formula"] + f"; convention over the dimensioned span "
                                                                            f"{Lj:.2f} m = {conv}")
            comps.append(RM.component(
                comp_id=f"{pid}|STIRRUPS|S{i + 1}", bar_role="STIRRUPS", span=i + 1, dia_mm=st["dia_mm"], count=cnt,
                bar_shape="CLOSED_LINK", parts=[RM.part("CORE", _loop(B, H, c), RM.COMPLETE, "closed loop"),
                                                RM.part("HOOK", _hook135(st["dia_mm"]), RM.PROVISIONAL,
                                                        "PROVISIONAL_HOOK_ALLOWANCE 2 x 135°")],
                source=self.defsrc(df, (f"STR{i + 1}-B", f"STR{i + 1}-D"), st),
                formula=f"{cnt['formula']}; verified zone = span {Lj:.2f} - all support widths "
                        f"({support_deduction if support_deduction is not None else 'n/a'}) m", **base))
        if F["H_cm"] > 60:
            comps.append(RM.blocked_component(comp_id=f"{pid}|SIDE_BARS", bar_role="SIDE_BARS",
                                              why="note 21 (depth > 60): 2/3/4 Ø12 by width - mapping not printed",
                                              source=_src(self.sha, "ST7757.pdf p.8 note 21", "note 21", "RANGE",
                                                          page=8),
                                              **{k: v for k, v in base.items() if k != "cover_rule_id"}))
        else:
            comps.append(RM.not_required(comp_id=f"{pid}|SIDE_BARS", bar_role="SIDE_BARS",
                                         why=f"depth {F['H_cm']:.0f} cm <= 60",
                                         **{k: v for k, v in base.items() if k != "cover_rule_id"}))
        self.add(RM.population(pop_id=pid, element_type="CONTINUOUS_BEAM", occurrence_id=occ, level=fl,
                               occurrence_state=ost, components=comps, occurrence_why=why,
                               source={"plan_tags": o["tags"], "plan_state": o["state"], "lengths": L}), comps)

    # ------------------------------------------------------------------------------------------- columns
    BAND = {"GROUND FLOOR": "GR", "1ST FLOOR": "1ST", "2ND FLOOR & TOP": "2ND"}

    def columns(self):
        ties_src = next((t for t in self.src["loose"] if "ST. OF COLUMN" in t["raw"].upper()), None)
        for r in self.ctx["b2a"]["columns"]["rows"]:
            occ = f"COLUMN:{r['floor']}:{r['type']}:{r['tag_key'].split('|')[1]}"
            pid = f"POP:{occ}"
            self.rc_occ.append(occ)
            df = (self.dmap.get(("COLUMN", r["type"])) or [None])[0]
            band = (df or {}).get("fields", {}).get("bands", {}).get(self.BAND.get(r["storey_band"], ""))
            base = dict(population_id=pid, element_type="COLUMN", occurrence_id=occ, level=r["floor"])
            if r.get("state") == "NOT_IN_STOREY" or band is None:
                comps = [RM.not_required(comp_id=f"{pid}|ALL", bar_role="ALL", why="type has no section in this storey",
                                         **base)]
                self.add(RM.population(pop_id=pid, occurrence_state="NOT_REQUIRED", components=comps,
                                       occurrence_why="NOT_IN_STOREY", **{k: v for k, v in base.items()
                                                                          if k != "population_id"}), comps)
                continue
            h = next(iv["interval_m"] for iv in self.ctx["b2a"]["intervals"] if iv["from"] == r["floor"])
            clear = r.get("height_m") or h
            B, D = band["B_cm"] / 100, band["H_cm"] / 100
            c = _c("COVER-MEMBER-25")
            bars = band["bars"]
            lap = LAP["LAP-COMPRESSION-40D"]["factor"] * bars["dia_mm"] / 1000.0
            comps = [RM.component(
                comp_id=f"{pid}|VERTICAL", bar_role="VERTICAL", dia_mm=bars["dia_mm"],
                count=_cnt_abs(bars["count"], "CGT schedule"), cover_rule_id="COVER-MEMBER-25",
                parts=[RM.part("CORE", h, RM.COMPLETE, "storey interval (STRUCTURAL_INTERVAL_FROM_FFL_EQUAL_BUILDUP)")],
                source=self.defsrc(df, tuple(bars["tags"]), bars), bbs_addition_m=lap,
                bbs_addition_rule="LAP-COMPRESSION-40D at the storey splice (procurement only)",
                formula=f"{bars['count']} x {h:.2f} m x {bars['dia_mm']}^2/162", **base)]
            cnt = RM.bar_count("BARS_PER_METRE", 6, clear, basis="'ST. OF COLUMN 6Ø8/m' over the column height")
            comps.append(RM.component(
                comp_id=f"{pid}|TIES", bar_role="TIES", dia_mm=8, count=cnt, bar_shape="CLOSED_LINK",
                cover_rule_id="COVER-MEMBER-25",
                parts=[RM.part("CORE", _loop(B, D, c), RM.COMPLETE, "closed loop 2(B-2c)+2(D-2c)"),
                       RM.part("HOOK", _hook135(8), RM.PROVISIONAL, "PROVISIONAL_HOOK_ALLOWANCE 2 x 135°")],
                source=_src(self.sha, f"TEXT:{ties_src['handle']}" if ties_src else "ST. OF COLUMN",
                            ties_src["raw"] if ties_src else "6Ø8/m", "6 Ø8 per metre"),
                formula=f"{cnt['formula']}; loop {_loop(B, D, c):.3f} m", **base))
            est = r.get("volume_m3") is not None
            pop = RM.population(pop_id=pid, occurrence_state="ESTABLISHED" if est else "BLOCKED", components=comps,
                                occurrence_why=None if est else
                                f"REBAR_BLOCKED_OCCURRENCE_NOT_ESTABLISHED ({r.get('state')})",
                                source={"plan_tag": r["tag_key"], "state": r.get("state"), "volume_m3": r.get("volume_m3")},
                                **{k: v for k, v in base.items() if k != "population_id"})
            self.add(pop, comps)
            self.registers["COLUMN_RECONCILIATION"].append({
                "occurrence": occ, "concrete_state": r.get("state"), "volume_m3": r.get("volume_m3"),
                "rebar_source_state": "CGT " + r["type"] + " " + self.BAND[r["storey_band"]],
                "kg_if_geometry_accepted": sum(x["verified_kg"] + x["provisional_kg"] + x["audit_kg"] for x in comps),
                "release_state": pop["release_state"]})

    # ------------------------------------------------------------------------------------------- slab audit
    def slabs(self):
        rows = self.ctx["v3b"]["struct"]["slab"]["rows"]
        tb = self._tb_binding()
        for fl in ("GF", "1F", "2F"):
            occ = f"SLAB:{fl}"
            pid = f"POP:{occ}"
            self.rc_occ.append(occ)
            base = dict(population_id=pid, element_type="SLAB", occurrence_id=occ, level=fl,
                        cover_rule_id="COVER-MEMBER-25")
            comps = []
            for r in [x for x in rows if x["floor"] == fl]:
                cid = f"{pid}|{r.get('annotation') or r.get('text')}"
                st = r["state"]
                srcd = _src(self.sha, f"TEXT:{r.get('annotation')}", r.get("text"),
                            {"n_per_m": r.get("n"), "dia_mm": r.get("dia_mm"), "top": r.get("top")},
                            binding=r.get("binding"))
                nb = dict(base, cover_rule_id=None)
                if st in ("DUPLICATE_LABEL", "BOUND_TO_DETAIL"):
                    comps.append(RM.not_required(comp_id=cid, bar_role="SLAB_BAR", why=f"{st}: counted once / with the "
                                                 f"dome detail ({r.get('duplicate_of') or r.get('detail')})",
                                                 source=srcd, **{k: v for k, v in nb.items() if k != "cover_rule_id"}))
                    continue
                if r.get("count") is None or not r.get("length_mm"):
                    comps.append(RM.blocked_component(comp_id=cid, bar_role="SLAB_BAR", why=f"slab bar {st}",
                                                      source=srcd, **{k: v for k, v in nb.items()
                                                                      if k != "cover_rule_id"}))
                    continue
                for layer in (["BOTTOM", "TOP"] if r.get("annotation") in tb["bound"] else
                              ["TOP" if r.get("top") else "BOTTOM"]):
                    comps.append(self._slab_comp(r, cid + ("|T&B_TOP" if layer == "TOP" and not r.get("top") else ""),
                                                 layer, srcd, base, tb))
            if not comps:
                comps.append(RM.blocked_component(comp_id=f"{pid}|NO_ANNOTATION", bar_role="SLAB_BAR",
                                                  why="no slab reinforcement annotation bound on this floor",
                                                  source=_src(self.sha, f"slab sheet {fl}", "none", "NO_ANNOTATION"),
                                                  **{k: v for k, v in base.items() if k != "cover_rule_id"}))
            self.add(RM.population(pop_id=pid, occurrence_state="ESTABLISHED", components=comps,
                                   occurrence_why="slab panel coverage (every panel annotated) is not proven - the "
                                                  "slab population stays a lower bound",
                                   release_override=None, **{k: v for k, v in base.items()
                                                             if k not in ("population_id", "cover_rule_id")}), comps)
            # a slab is never VERIFIED_COMPLETE here: coverage of all panels unproven
            if self.pops[-1]["release_state"] == RM.VC:
                self.pops[-1] = RM.population(pop_id=pid, occurrence_state="ESTABLISHED", components=comps,
                                              release_override=RM.LB,
                                              occurrence_why="panel coverage unproven",
                                              **{k: v for k, v in base.items()
                                                 if k not in ("population_id", "cover_rule_id")})
                p = self.pops[-1]
                p["lower_bound_kg"], p["verified_complete_kg"] = sum(x["verified_kg"] for x in comps), 0.0
        self.registers["SLAB_TB"] = tb

    def _slab_comp(self, r, cid, layer, srcd, base, tb):
        L = r["length_mm"] / 1000.0
        rate, w = r.get("n"), (r.get("width_mm") or 0) / 1000.0
        n_bind = r["count"]
        if r.get("kind") == "PER_M" or (rate and w):
            lb = RM.bar_count("BARS_PER_METRE", rate, w)["verified"] if rate and w else n_bind
            lb = min(lb, n_bind)
            cnt = {"mode": "BARS_PER_METRE", "value": rate, "verified": lb, "convention": n_bind,
                   "rule_id": "SLAB_BINDER_COUNT_SPLIT", "rate_per_m": rate,
                   "formula": f"binder n = floor(w/s)+1 = {n_bind}; verified = ceil(rate x w) = {lb}"}
        else:
            cnt = _cnt_abs(n_bind, "binder count")
        st = r["state"]
        if st in ("BOUND", "BOUND_TEXT_ONLY"):
            parts = [RM.part("CORE", L, RM.COMPLETE, "clear span + measured embedment at both supports (binder)")]
        elif st == "PARTIAL":
            c = r.get("commercial") or {}
            extra = (c.get("net_m", 0) / n_bind - L) if c.get("net_m") else 0.0
            parts = [RM.part("CORE", L, RM.COMPLETE, "measured part"),
                     RM.part("EXTENSION", max(extra, 0.0), RM.PROVISIONAL, "open-support embedment (median width)")]
        else:
            parts = [RM.part("CORE", L, RM.PROVISIONAL, f"{st}: drawn extent")]
        why = None
        if layer == "TOP" and not r.get("top"):
            why = f"(T&B) qualifier {tb['bound'][r['annotation']]['qualifier']} bound by position"
        return RM.component(comp_id=cid, bar_role="SLAB_BAR", layer=layer, direction=r.get("annotation"),
                            dia_mm=r["dia_mm"], count=cnt, parts=parts, source=srcd, why=why,
                            formula=f"{cnt['formula']} x {L:.3f} m x {r['dia_mm']}^2/162", **base)

    def _tb_binding(self):
        """(T&B) qualifier -> the slab annotation it modifies: same rotation, nearest within 600 mm, and the next
        same-rotation annotation at least twice as far. Otherwise BLOCKED_QUALIFIER_BINDING."""
        import ezdxf
        doc = ezdxf.readfile(str(SRC.DXF))
        msp = doc.modelspace()
        tx = [e for e in msp.query("TEXT") if e.dxf.layer in ("S-TEXT-SLAB", "S-TEXT-CORNER")]
        ann = [e for e in tx if re.search(r"%%c\d+/m", e.dxf.text, re.I)]
        rows = {r.get("annotation"): r for r in self.ctx["v3b"]["struct"]["slab"]["rows"]}
        out = {"bound": {}, "rows": []}
        for q in [e for e in tx if e.dxf.text.strip() == "(T&B)"]:
            rot = round(float(q.dxf.get("rotation", 0.0)) % 180)
            same = sorted([(math.hypot(e.dxf.insert.x - q.dxf.insert.x, e.dxf.insert.y - q.dxf.insert.y), e) for e in ann
                           if round(float(e.dxf.get("rotation", 0.0)) % 180) == rot], key=lambda t: t[0])
            d1, e1 = same[0] if same else (None, None)
            d2 = same[1][0] if len(same) > 1 else None
            strong = d1 is not None and d1 <= 600 and (d2 is None or d2 >= 2 * d1)
            row = rows.get(e1.dxf.handle) if e1 is not None else None
            rec = {"qualifier": q.dxf.handle, "rotation": rot, "nearest_annotation": e1.dxf.handle if e1 else None,
                   "nearest_text": e1.dxf.text if e1 else None, "d1_mm": round(d1, 1) if d1 else None,
                   "d2_mm": round(d2, 1) if d2 else None, "annotation_state": row["state"] if row else None,
                   "annotation_bound_as_top": row.get("top") if row else None,
                   "top_record_exists": bool(row and row.get("top")),
                   "binding": "STRONG_POSITIONAL" if strong and row else "BLOCKED_QUALIFIER_BINDING"}
            out["rows"].append(rec)
            if rec["binding"] == "STRONG_POSITIONAL" and not rec["top_record_exists"]:
                out["bound"][e1.dxf.handle] = rec
        out["dedupe_audit"] = [{k: r.get(k) for k in ("floor", "annotation", "text", "state", "duplicate_of", "top",
                                                      "count", "length_mm")}
                               for r in self.ctx["v3b"]["struct"]["slab"]["rows"] if r["state"] == "DUPLICATE_LABEL"]
        return out

    # ------------------------------------------------------------------------------------------- ground slab, stairs
    def ground_slab(self, r1_gzb):
        fps = r1_gzb["footprints"]
        for z in self.ctx["v3b"]["struct"]["ground_zones"]["zones"]:
            occ = f"GROUND_SLAB:{z['id']}"
            pid = f"POP:{occ}"
            self.rc_occ.append(occ)
            area = z.get("slab_m2")
            outer = z.get("outer_m2") or r1_gzb["v3a_zone_1"]["outer_m2"]
            fp_match = [f for f in fps if abs(f["area_m2"] - outer) < 0.01]
            scope = ("ESTABLISHED_SOLE_CANDIDATE" if fp_match else "AMBIGUOUS_NESTED_CANDIDATES")
            self.registers["GROUND_SLAB_SCOPE"].append({
                "zone": z["id"], "note": "T=10cm, 5Ø10/m E.W.", "bound_cell_outer_m2": outer, "slab_m2": area,
                "footprints": fps, "scope": scope,
                "positive_evidence_checked": ["slab note position", "closed cell / footprint outlines",
                                              "structural layer (1 / 2)", "drawing title"],
                "evidence_found": ("the note's smallest closed cell IS a whole ground-beam footprint" if fp_match else
                                   "the note lies inside nested closed cells; no boundary, callout or hatch selects one"),
                "decision": ("scope = the footprint" if fp_match else
                             "BLOCKED_SCOPE (Q-S4): the bound smallest cell is kept as a LOWER BOUND; min -> max is "
                             "not used")})
            comps = []
            for d in ("X", "Y"):
                comps.append(RM.component(
                    comp_id=f"{pid}|MESH_{d}", population_id=pid, element_type="GROUND_SLAB", occurrence_id=occ,
                    level="GF", bar_role="MESH", direction=d, dia_mm=10,
                    count={"mode": "BARS_PER_METRE", "value": 5, "verified": 1, "convention": 1,
                           "rule_id": "MESH_AREA_X_RATE", "formula": "run = area x 5 m/m2 (5Ø10/m E.W.)"},
                    parts=[RM.part("CORE", area * 5.0, RM.PROVISIONAL,
                                   "mesh run = slab area x rate; cover / edge bars not deducted / added")],
                    cover_rule_id="COVER-SOIL-70", source=_src(self.sha, "ground-beam sheet note", "5%%c10/m E.W.",
                                                              "5 Ø10 per metre each way", page=3),
                    formula=f"{area:.3f} m2 x 5 x 10^2/162"))
            if scope != "ESTABLISHED_SOLE_CANDIDATE":
                comps.append(RM.blocked_component(comp_id=f"{pid}|SCOPE_REMAINDER", population_id=pid,
                                                  element_type="GROUND_SLAB", occurrence_id=occ, level="GF",
                                                  bar_role="MESH_SCOPE_REMAINDER",
                                                  why="BLOCKED_SCOPE Q-S4: rest of the footprint not established",
                                                  source=_src(self.sha, "R1 ground_zone_binding", "nested cells",
                                                              "AMBIGUOUS")))
            self.add(RM.population(pop_id=pid, element_type="GROUND_SLAB", occurrence_id=occ, level="GF",
                                   occurrence_state="ESTABLISHED", components=comps,
                                   occurrence_why=scope), comps)

    def stairs(self):
        occ = "STAIRS:GF-1F+1F-2F"
        pid = f"POP:{occ}"
        self.rc_occ.append(occ)
        fl = self.ctx["v3b"]["struct"]["stairs"]["flights"]
        reasons = [
            "p.16 TYPICAL STEEL LAYOUT is N.T.S. with levels 0.00 / +2.00 (one landing) / +4.00",
            f"Alsenan GF->1F rise {fl[0]['H_m']} m with two turns (plan tread runs {fl[0]['plan_tread_lines_check']})",
            f"Alsenan 1F->2F rise {fl[1]['H_m']} m",
            "waist thickness printed only as 'THICK' (no value); riser count not printed",
            "no stair callout on the plans binds the typical layout to a flight"]
        self.registers["STAIR_APPLICABILITY"].append({"detail": "ST7757.pdf p.16 TYPICAL STEEL LAYOUT-STAIR SECTION",
                                                      "bars_printed": ["8Ø16/m", "6Ø14/m", "6Ø12/m", "Ø12/20cm",
                                                                       "Ø8/15", "1Ø12", "6Ø16/m"],
                                                      "state": "BLOCKED_DETAIL_APPLICABILITY", "reasons": reasons})
        comps = [RM.blocked_component(comp_id=f"{pid}|ALL", population_id=pid, element_type="STAIR",
                                      occurrence_id=occ, level="GF", bar_role="ALL",
                                      why="BLOCKED_DETAIL_APPLICABILITY: " + "; ".join(reasons),
                                      source=_src(self.sha, "ST7757.pdf p.16", "typical", "BLOCKED", page=16))]
        self.add(RM.population(pop_id=pid, element_type="STAIR", occurrence_id=occ, level="GF",
                               occurrence_state="BLOCKED", components=comps,
                               occurrence_why="BLOCKED_DETAIL_APPLICABILITY"), comps)

    # ------------------------------------------------------------------------------------------- carried
    CARRIED = ("GROUND", "LINTELS", "GROUND_BEAM_EXT", "DOME", "POOL", "BEAM_RESIDUE", "BOUNDARY_WALL",
               "FOOTING_F_F10", "COLUMN_STARTERS")
    DROPPED = {"BEAM_SIDE_BARS": "replaced by R3 SIDE_BARS components (BLOCKED: note 21 / REMARKS semantics)",
               "FOOTINGS": "re-engineered (R3 footings)", "COLUMNS": "re-engineered (R3 columns)",
               "BEAMS": "re-engineered (R3 simple beams / straps)", "SLAB": "re-engineered (R3 slab audit)",
               "GROUND_SLAB": "re-engineered (R3 ground-slab scope)", "STAIRS": "re-engineered (R3 stairs)"}

    def carried(self):
        """Populations Round 3 does not re-engineer: carried from V3b with an honest release (never VERIFIED_COMPLETE:
        not re-audited this round)."""
        ws = self.ctx["v3b"]["rebar"]["weighed"]
        groups = defaultdict(list)
        for s in ws:
            if s["population"] == "GROUND" and s.get("element") == "GROUND_SLAB":
                continue                                          # ground slab zone 1 is re-engineered
            groups[s["population"]].append(s)
        for popn in self.CARRIED:
            occ = f"CARRIED:{popn}"
            pid = f"POP:{occ}"
            self.rc_occ.append(occ)
            comps = []
            for i, s in enumerate(groups.get(popn, [])):
                cid = f"{pid}|{i:04d}|{s['ref']}"
                srcd = _src(self.sha, f"V3b set {s['ref']}", s.get("basis") or s.get("why") or "V3b set",
                            s.get("commercial") or s.get("technical") or s.get("state") or "BLOCKED",
                            carried_from="ctx.v3b.rebar.weighed")
                b = dict(population_id=pid, element_type=popn, occurrence_id=occ, level=s.get("level"))
                if s.get("net_kg") is None:
                    comps.append(RM.blocked_component(comp_id=cid, bar_role=s["ref"], why=s.get("why") or "BLOCKED",
                                                      source=srcd, **b))
                    continue
                if s.get("state") == "WEIGHT_ONLY":
                    c = RM.component(comp_id=cid, bar_role=s["ref"], dia_mm=None, count=None, parts=[], source=srcd,
                                     forced_state=None, **b)
                    c.update(state=RM.PROVISIONAL, provisional_kg=s["net_kg"], net_kg=s["net_kg"],
                             formula=s.get("basis"), cover_rule_id="CARRIED")
                    comps.append(c)
                    continue
                tech = s.get("tech_kg") or 0.0
                c = RM.component(comp_id=cid, bar_role=s["ref"], dia_mm=s["dia_mm"], layer=f"V3B_SET_{i}",
                                 count=_cnt_abs(s["count"], "V3b set"), source=srcd, cover_rule_id="CARRIED_V3B",
                                 parts=[RM.part("CORE", s["straight_m"], RM.COMPLETE if s.get("technical") in
                                                ("DERIVED", "PARTIAL") else RM.PROVISIONAL, "V3b straight length"),
                                        RM.part("HOOK", s.get("hook_m") or 0.0, RM.PROVISIONAL, "V3b code-method hooks")],
                                 formula=f"V3b: {s['count']} x {s.get('bar_m', 0):.3f} m x {s['dia_mm']}^2/162", **b)
                comps.append(c)
            override = RM.BUDGET if popn == "BEAM_RESIDUE" else None
            pop = RM.population(pop_id=pid, element_type=popn, occurrence_id=occ, level="ALL",
                                occurrence_state="ESTABLISHED", components=comps, release_override=override,
                                occurrence_why="CARRIED_FROM_V3B_NOT_REAUDITED_R3")
            if pop["release_state"] == RM.VC:                    # not re-audited -> never claimed complete
                pop = RM.population(pop_id=pid, element_type=popn, occurrence_id=occ, level="ALL",
                                    occurrence_state="ESTABLISHED", components=comps, release_override=RM.LB,
                                    occurrence_why="CARRIED_FROM_V3B_NOT_REAUDITED_R3")
                pop["lower_bound_kg"], pop["verified_complete_kg"] = sum(x["verified_kg"] for x in comps), 0.0
            self.add(pop, comps)
        dropped = defaultdict(float)
        for s in ws:
            if s["population"] in self.DROPPED:
                dropped[s["population"]] += s.get("net_kg") or 0.0
        self.registers["V3B_REPLACED"] = [{"population": k, "v3b_net_kg": v, "why": self.DROPPED[k]}
                                          for k, v in sorted(dropped.items())]

    # ------------------------------------------------------------------------------------------- run
    def run(self, r1_gzb):
        self.footings()
        self.straps()
        self.simple_beams()
        self.continuous_beams()
        self.columns()
        self.slabs()
        self.ground_slab(r1_gzb)
        self.stairs()
        self.carried()
        return self


# ===================================================================================================== invariants
def check_cb_accounting(b) -> list:
    """Every drawn bar of every CB frame ends in exactly one component of each occurrence of that type."""
    v = []
    geo = {g["type"]: g for g in b.registers["CB_GEOMETRY"]}
    for p in [p for p in b.pops if p["element_type"] == "CONTINUOUS_BEAM"]:
        typ = p["occurrence_id"].split(":")[2]
        handles = [c["comp_id"].rsplit("|", 1)[1] for c in b.comps if c["population_id"] == p["pop_id"]
                   and c["bar_role"] not in ("STIRRUPS", "SIDE_BARS")]
        for bar in geo[typ]["bars"]:
            n = handles.count(bar["handle"])
            if n != 1:
                v.append(("CB_BAR_NOT_ACCOUNTED_ONCE", p["pop_id"], bar["handle"], n))
        n_st = sum(1 for c in b.comps if c["population_id"] == p["pop_id"] and c["bar_role"] == "STIRRUPS")
        if n_st != len(geo[typ]["spans_m"]):
            v.append(("CB_STIRRUP_SPAN_MISSING", p["pop_id"]))
    return v


def check_cb_span_cores(b) -> list:
    """A bottom bar's verified core must equal the source spans it covers (whole spans only)."""
    v = []
    geo = {g["type"]: g for g in b.registers["CB_GEOMETRY"]}
    for c in b.comps:
        if c["element_type"] != "CONTINUOUS_BEAM" or c["bar_role"] != "BOTTOM" or c["state"] == RM.BLOCKED:
            continue
        typ = c["occurrence_id"].split(":")[2]
        bar = next(x for x in geo[typ]["bars"] if x["handle"] == c["comp_id"].rsplit("|", 1)[1])
        want = sum(pc["m"] for pc in bar["pieces"] if pc["kind"] == "CORE")
        if abs(c["verified_length_m"] - want) > 1e-6:
            v.append(("CB_CORE_DIFFERS_FROM_SPANS", c["comp_id"]))
    return v


def check_ftb_layers(b) -> list:
    need = {"TOP_SHORT", "TOP_LONG", "BOTTOM_SHORT", "BOTTOM_LONG"}
    v = []
    for p in [p for p in b.pops if p["element_type"] in ("FOOTING_2_LAYER", "FOOTING_LIFT")]:
        have = {c["bar_role"] for c in b.comps if c["population_id"] == p["pop_id"]}
        if not need <= have:
            v.append(("FTB_LAYER_MISSING", p["pop_id"], sorted(need - have)))
    return v


def check_layer_tags(b) -> list:
    """FTB layer from the source tag: SH-T / LO-T = TOP, SH-B-B / LO-B-B = BOTTOM."""
    v = []
    for c in b.comps:
        loc = (c["source"] or {}).get("locator", "")
        if c["element_type"] in ("FOOTING_2_LAYER", "FOOTING_LIFT") and c["layer"] in ("TOP", "BOTTOM") and \
                c["bar_role"] in ("TOP_SHORT", "TOP_LONG", "BOTTOM_SHORT", "BOTTOM_LONG"):
            want = "TOP" if ("-T-B" in loc) else "BOTTOM"
            if c["layer"] != want or not c["bar_role"].startswith(want):
                v.append(("FTB_LAYER_DIFFERS_FROM_SOURCE_TAG", c["comp_id"]))
    return v


def check_column_occurrences(b) -> list:
    """D5: a column occurrence without established concrete never carries verified / lower-bound kg."""
    vol = {r["occurrence"]: r["volume_m3"] for r in b.registers["COLUMN_RECONCILIATION"]}
    return [("D5_COLUMN_RELEASED_WITHOUT_CONCRETE", p["pop_id"]) for p in b.pops
            if p["element_type"] == "COLUMN" and p["occurrence_id"] in vol and vol[p["occurrence_id"]] is None
            and (p["verified_complete_kg"] + p["lower_bound_kg"] + p["provisional_kg"]) > 0]


def check_tb(b) -> list:
    v = []
    for ann in b.registers["SLAB_TB"]["bound"]:
        layers = {c["layer"] for c in b.comps if c["element_type"] == "SLAB" and
                  (c["source"] or {}).get("locator") == f"TEXT:{ann}" and c["state"] != RM.NOT_REQUIRED}
        if layers != {"TOP", "BOTTOM"}:
            v.append(("T_AND_B_LAYER_COLLAPSED", ann, sorted(layers)))
    return v


def check_strap_conflicts(b) -> list:
    keys = {c["key"] for c in b.defs["conflicts"]}
    return RM.check_conflicts([p for p in b.pops if p["element_type"] == "STRAP_BEAM"], keys,
                              lambda p: p["occurrence_id"].split(":")[1])


def project_invariants(b) -> dict:
    return {"cb_accounting": check_cb_accounting(b), "cb_span_cores": check_cb_span_cores(b),
            "ftb_layers": check_ftb_layers(b), "layer_tags": check_layer_tags(b),
            "column_d5": check_column_occurrences(b), "t_and_b": check_tb(b), "strap_conflicts": check_strap_conflicts(b),
            "source_consistency": RM.check_source_consistency(b.comps)}


def build(ctx, r1_gzb, src=None, defs=None, cbg=None) -> Build:
    return Build(ctx, src, defs, cbg).run(r1_gzb)
