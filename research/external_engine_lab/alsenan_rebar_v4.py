"""ALSENAN ROUND 4 - source exhaustion + carried rebar re-audit (builds on Round 3; Round-3 registers are never written).

What changes against Round 3 (alsenan_rebar_v3.Build):
  * every PDF-only authority is a VisualSourceClaim (alsenan_rebar_v4_sources) with a derived source state; only
    CROSS_VERIFIED / MACHINE_READ claims drive VERIFIED length parts, AI-only readings drive PROVISIONAL parts;
  * the nine carried V3b populations are rebuilt through REBAR_MODEL_V1 or made explicit BLOCKED populations:
    ground beams (interior + exterior, one register), lintels, column starters + necks, boundary wall, domes, pool,
    beam residue (unbound tags), F / F10 (retired: duplicate of the Round-3 blocked footing pair);
  * lift footing FF split into FF_FOOTING_MESH / LIFT_PIT_WALL_12MM / LIFT_PIT_WALL_16MM / LIFT_PIT_BASE_2D16 /
    OTHER_DETAIL_COMPONENTS with the pit outline machine-read from ST7757.dxf (S-BW) and the height BLOCKED;
  * slab bottom bars split by the p.15 rule (50 % continuous, 50 % stop 0.125 L from a continuous support) and
    drawn top bars measured from the plan, never the full panel;
  * D5 columns and the CB occurrence conflicts get a source-exhaustion search with scored candidates; only a match
    with no contradiction is accepted;
  * new explicit BLOCKED populations for sources the drawings require but do not detail (lift tie beams note 19,
    planted columns, parapets, temperature reinforcement).
Quantity authority: source bar definition x occurrence geometry x D^2/162; kg/m3 is never a quantity.
"""

from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path

from engine.source import rebar_model as RM
from engine.source import visual_source_claim as VS

import alsenan_rebar_v3 as R3
import alsenan_rebar_v4_sources as SV
import alsenan_structural_source_v2 as SRC

PDF = "ST7757.pdf"
C_SOIL, C_MEMBER = 0.07, 0.025
GB_LEN_BASIS_PAD_M = 0.25            # centreline-basis length >= clear span + two half supports (>= 0.125 each)
GB_DETAILS = {
    "GT5": {"claim": "P13-GB-GT5M", "rule": "> 5 m", "B": 0.30, "D": 0.60, "TOP": (3, 16),
            "LOWER_1": (3, 16), "LOWER_2": (3, 16), "STIR": (8, 150), "SIDE": None},
    "LT5": {"claim": "P13-GB-LT5M", "rule": "< 5 m", "B": 0.30, "D": 0.40, "TOP": (3, 14),
            "LOWER_1": (3, 14), "LOWER_2": (3, 14), "STIR": (8, 150), "SIDE": None},
    "LT2_5": {"claim": "P13-GB-LT2_5M-BARS", "section_claim": "P13-GB-LT2_5M-SECTION", "rule": "< 2.5 m", "B": 0.30,
              "D": 0.30, "TOP": (3, 14), "LOWER_1": (3, 14), "LOWER_2": (3, 14), "STIR": None, "SIDE": None},
    "EXT": {"claim": "P13-GB-EXTERIOR", "rule": "exterior wall", "B": 0.30, "D": None, "TOP": (3, 16),
            "LOWER_1": (3, 16), "LOWER_2": (3, 16), "STIR": (8, 150), "SIDE": (2, 12, 0.30)},
}
EXT_D_ASSUMED = 1.00                 # V3b provisional depth (ground +-0.00 to GF +1.00); never verified


def _cat(L):
    return "LT2_5" if L < 2.5 else ("LT5" if L < 5.0 else "GT5")


class Build4(R3.Build):
    def __init__(self, ctx, capture=None, **kw):
        super().__init__(ctx, **kw)
        self.capture = capture or SV.load_capture()
        self.pit = self._lift_pit()
        tags = {fl: (ctx["b2a"]["sheets"][fl]["slab"]["sheet_thickness_tags_cm"] or [None])[0] for fl in ("GF", "1F", "2F")}
        self.slab_tags_cm = tags
        self.claims = {c["claim_id"]: c for c in SV.build_claims(self.capture, dxf_lift_pit=self.pit, slab_tags_cm=tags)}
        self.pdf_sha = self.capture["drawing_sha256"]
        self.reaudit = []

    # ------------------------------------------------------------------------------------------- claims
    def auth(self, cid):
        return VS.quantity_authority(self.claims[cid])

    def st(self, cid):
        """length-part state a claim can support: COMPLETE only with VERIFIED quantity authority"""
        return RM.COMPLETE if self.auth(cid) == VS.VERIFIED_AUTHORITY else RM.PROVISIONAL

    def vsrc(self, cid, normalised=None, **kw):
        c = self.claims[cid]
        return {"drawing": PDF, "drawing_sha256": self.pdf_sha, "page": c["page"],
                "locator": f"{PDF} p.{c['page']} crop {c['crop_id']} {c['crop_bbox']} (crop sha256 {c['crop_hash'][:16]})",
                "raw": c["raw_visual_transcription"], "normalised": normalised or c["normalised_interpretation"],
                "claim_id": cid, "claim_state": c["source_state"], **kw}

    # ------------------------------------------------------------------------------------------- lift pit (DXF)
    def _lift_pit(self):
        import ezdxf
        doc = ezdxf.readfile(str(SRC.DXF))
        msp = doc.modelspace()
        ff = next((e for e in msp.query("TEXT") if e.dxf.text.strip() == "FF"), None)
        if ff is None:
            return None
        x, y = ff.dxf.insert.x, ff.dxf.insert.y
        rect = []
        for e in msp.query("LWPOLYLINE"):
            if e.dxf.layer != "S-BW" or not e.closed:
                continue
            pts = [(p[0], p[1]) for p in e.get_points()]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            if min(xs) <= x <= max(xs) and min(ys) <= y <= max(ys):
                rect.append((max(xs) - min(xs), max(ys) - min(ys), e.dxf.handle))
        if len(rect) != 2:
            return {"state": "NOT_FOUND", "rects": rect}
        inner, outer = sorted(rect)
        wall = ((outer[0] - inner[0]) / 2.0, (outer[1] - inner[1]) / 2.0)
        return {"state": "MACHINE_READ", "inner_m": [round(inner[0] / 1000, 3), round(inner[1] / 1000, 3)],
                "outer_m": [round(outer[0] / 1000, 3), round(outer[1] / 1000, 3)],
                "wall_mm": round((wall[0] + wall[1]) / 2.0, 1),
                "centreline_perimeter_m": round(2 * ((inner[0] + outer[0]) / 2 + (inner[1] + outer[1]) / 2) / 1000, 3),
                "inner_perimeter_m": round(2 * (inner[0] + inner[1]) / 1000, 3),
                "handles": [inner[2], outer[2]], "source": "ST7757.dxf S-BW closed outlines around the FF footing mark"}

    # ------------------------------------------------------------------------------------------- footings (FF split)
    MESH_ROLES = ("TOP_SHORT", "TOP_LONG", "BOTTOM_SHORT", "BOTTOM_LONG")

    def footings(self):
        super().footings()
        i = next((k for k, p in enumerate(self.pops) if p["element_type"] == "FOOTING_LIFT"), None)
        if i is None:
            return
        p = self.pops[i]
        pid, occ = p["pop_id"], p["occurrence_id"]
        old = [c for c in self.comps if c["population_id"] == pid]
        keep = [c for c in old if c["bar_role"] not in ("LIFT_PIT_WALLS", "PIT_WALL_BASE_BARS_2D16")]
        for c in keep:
            c["component_group"] = "FF_FOOTING_MESH" if c["bar_role"] in self.MESH_ROLES else "OTHER_DETAIL_COMPONENTS"
        base = dict(population_id=pid, element_type="FOOTING_LIFT", occurrence_id=occ, level="FOUNDATION")
        new = []
        pit = self.pit or {}
        per, per_in = pit.get("centreline_perimeter_m"), pit.get("inner_perimeter_m")
        cid = "P14-LIFT-VALUES"
        h_why = "wall height = pit depth 'As Per Lift Manufactures recommendations' - not in the source"
        cnt16 = RM.bar_count("BARS_PER_METRE", 6, per, basis="6Ø16/m along the pit-wall centreline (one face)") \
            if per else None
        new.append(RM.component(
            comp_id=f"{pid}|LIFT_PIT_WALL_16MM", bar_role="LIFT_PIT_WALL_16MM", dia_mm=16, count=cnt16,
            parts=[RM.part("CORE", None, RM.BLOCKED, "vertical bar length = pit-wall height", why=h_why)],
            source=self.vsrc(cid, {"rate": "6Ø16/m", "orientation": "vertical (AI reading)",
                                   "per_face": "not printed"}, pit=pit),
            cover_rule_id="COVER-SOIL-70", interpretation_state="BLOCKED_DIMENSION", why=f"BLOCKED_DIMENSION: {h_why}",
            formula=f"n >= 6/m x {per} m (one face); length = pit height (BLOCKED)", **base))
        cnt12 = RM.bar_count("BARS_PER_METRE", 6, None, basis="6Ø12/m over the pit-wall height (BLOCKED)")
        new.append(RM.component(
            comp_id=f"{pid}|LIFT_PIT_WALL_12MM", bar_role="LIFT_PIT_WALL_12MM", dia_mm=12, count=cnt12,
            parts=[RM.part("CORE", per or 0.0, RM.COMPLETE if per else RM.BLOCKED,
                           "horizontal bar = pit-wall centreline loop (DXF S-BW)")],
            source=self.vsrc(cid, {"rate": "6Ø12/m", "orientation": "horizontal (AI reading)"}, pit=pit),
            cover_rule_id="COVER-SOIL-70", interpretation_state="BLOCKED_DIMENSION",
            why=f"BLOCKED_DIMENSION: bar count = 6/m x wall height; {h_why}",
            formula=f"n = 6/m x height (BLOCKED); length {per} m", **base))
        base_cnt = {"mode": "ABSOLUTE_COUNT", "verified": 2, "convention": 4, "rule_id": "TWO_LABELLED_PAIRS",
                    "formula": "2Ø16 printed twice at the wall base: 2 certain, 2 more if both labels are distinct bars"}
        new.append(RM.component(
            comp_id=f"{pid}|LIFT_PIT_BASE_2D16", bar_role="LIFT_PIT_BASE_2D16", dia_mm=16, count=base_cnt,
            parts=[RM.part("CORE", per_in or 0.0, self.st(cid), "loop >= inner pit perimeter (DXF S-BW inner outline)"),
                   RM.part("EXTENSION", max((per or 0) - (per_in or 0), 0.0), RM.PROVISIONAL,
                           "inner perimeter -> wall centreline loop"),
                   RM.part("ANCHORAGE", None, RM.BLOCKED, "corner continuity / laps", why="not detailed")],
            source=self.vsrc(cid, {"bars": "2Ø16 x 2 labels"}, pit=pit), cover_rule_id="COVER-SOIL-70",
            formula=f"2 (+2) x {per_in} m (+ {round((per or 0) - (per_in or 0), 3)} m) x 16^2/162", **base))
        new.append(RM.component(
            comp_id=f"{pid}|PIT_WALL_TOP_2D12", bar_role="OTHER_DETAIL_COMPONENTS", layer="WALL_TOP", dia_mm=12,
            count=R3._cnt_abs(2, "2Ø12 printed at the wall top"),
            parts=[RM.part("CORE", per or 0.0, RM.PROVISIONAL, "wall-top loop (2Ø12 is OCR-read but not in the "
                                                                "independent review: AI + OCR only)")],
            source=self.vsrc(cid, {"bars": "2Ø12 wall top"}, pit=pit), cover_rule_id="COVER-SOIL-70",
            formula=f"2 x {per} m x 12^2/162", **base))
        for c in new:
            c["component_group"] = c["bar_role"] if c["bar_role"] != "OTHER_DETAIL_COMPONENTS" else \
                "OTHER_DETAIL_COMPONENTS"
        self.comps = [c for c in self.comps if c["population_id"] != pid] + keep + new
        self.pops[i] = RM.population(pop_id=pid, element_type="FOOTING_LIFT", occurrence_id=occ, level="FOUNDATION",
                                     occurrence_state=p["occurrence_state"], components=keep + new, source=p["source"],
                                     occurrence_why=p["occurrence_why"])
        self.registers["LIFT"] = {"pit": pit, "population": pid,
                                  "components": [{"comp_id": c["comp_id"], "group": c.get("component_group"),
                                                  "state": c["state"], "verified_kg": c["verified_kg"],
                                                  "provisional_kg": c["provisional_kg"], "why": c["why"]}
                                                 for c in keep + new]}

    # ------------------------------------------------------------------------------------------- CB occurrences
    def continuous_beams(self):
        self.cb_candidates = cb_candidates(self.ctx, self.dmap)
        super().continuous_beams()

    def _cb_occurrence(self, df, geo, fl, o):
        super()._cb_occurrence(df, geo, fl, o)
        tag = o["tags"][0].split("|")[1] if o["tags"] else "NOTAG"
        occ = f"CB:{fl}:{df['type']}:{tag}"
        dec = next((r for r in self.cb_candidates if r["occurrence"] == occ), None)
        if dec and dec["decision"] == "ACCEPTED_STRONG" and self.pops[-1]["occurrence_state"] != "ESTABLISHED":
            p = self.pops[-1]
            comps = [c for c in self.comps if c["population_id"] == p["pop_id"]]
            self.pops[-1] = RM.population(pop_id=p["pop_id"], element_type=p["element_type"], occurrence_id=occ,
                                          level=fl, occurrence_state="ESTABLISHED", components=comps,
                                          source=p["source"], occurrence_why="SOURCE_EXHAUSTION: " + dec["why"])

    # ------------------------------------------------------------------------------------------- columns (D5)
    def columns(self):
        super().columns()
        self.d5 = d5_reconciliation(self.ctx)
        beam_d = [d["fields"].get("H_cm") for (e, _), v in self.dmap.items() if e in ("SIMPLE_BEAM", "CONTINUOUS_BEAM")
                  for d in v if d["fields"].get("H_cm")]
        dmax = max(beam_d) / 100.0 if beam_d else None
        for row in self.d5:
            k = next((i for i, p in enumerate(self.pops) if p["occurrence_id"] == row["occurrence"]), None)
            if k is None:
                continue
            p = self.pops[k]
            comps = [c for c in self.comps if c["population_id"] == p["pop_id"]]
            cls = row["classification"]
            if cls == "REAL_COLUMN_UPPER_MEMBER_UNBOUND" and dmax:
                h = row["storey_interval_m"]
                ties = next(c for c in comps if c["bar_role"] == "TIES")
                cnt = RM.bar_count("BARS_PER_METRE", 6, max(h - dmax, 0.0),
                                   basis=f"clear height >= storey {h:.2f} - deepest scheduled beam {dmax:.2f} m")
                cnt = dict(cnt, convention=RM.bar_count("BARS_PER_METRE", 6, h)["convention"])
                new_t = RM.component(
                    comp_id=ties["comp_id"], population_id=p["pop_id"], element_type="COLUMN",
                    occurrence_id=p["occurrence_id"], level=p["level"], bar_role="TIES", dia_mm=8, count=cnt,
                    bar_shape="CLOSED_LINK", cover_rule_id="COVER-MEMBER-25", parts=ties["parts"],
                    source=ties["source"], formula=f"{cnt['formula']} (upper member unbound: lower bound)")
                comps = [new_t if c is ties else c for c in comps]
                self.comps = [new_t if c is ties else c for c in self.comps]
                st, why = "ESTABLISHED", "D5 SOURCE_EXHAUSTION: " + row["evidence"]
            elif cls == "REAL_COLUMN_SEVERAL_OUTLINES":
                st, why = "PROVISIONAL", "D5 SOURCE_EXHAUSTION: " + row["evidence"]
            elif cls == "OFF_STOREY_COLUMN":
                st, why = "NOT_REQUIRED", "D5 SOURCE_EXHAUSTION: OFF_STOREY_COLUMN - " + row["evidence"]
            else:
                continue
            self.pops[k] = RM.population(pop_id=p["pop_id"], element_type="COLUMN", occurrence_id=p["occurrence_id"],
                                         level=p["level"], occurrence_state=st, components=comps, source=p["source"],
                                         occurrence_why=why)
            row["r4_release_state"] = self.pops[k]["release_state"]
            row["r4_verified_kg"] = self.pops[k]["lower_bound_kg"] + self.pops[k]["verified_complete_kg"]
            row["r4_provisional_kg"] = self.pops[k]["provisional_kg"]
            row["r4_audit_kg"] = self.pops[k]["audit_kg"]

    # ------------------------------------------------------------------------------------------- slabs (p.15 rules)
    def slabs(self):
        rows = self.ctx["v3b"]["struct"]["slab"]["rows"]
        tb = self._tb_binding()
        self.registers["SLAB_TB"] = tb
        self.slab_rule_rows = []
        for fl in ("GF", "1F", "2F"):
            occ = f"SLAB:{fl}"
            pid = f"POP:{occ}"
            self.rc_occ.append(occ)
            base = dict(population_id=pid, element_type="SLAB", occurrence_id=occ, level=fl,
                        cover_rule_id="COVER-MEMBER-25")
            nb = {k: v for k, v in base.items() if k != "cover_rule_id"}
            comps = []
            for r in [x for x in rows if x["floor"] == fl]:
                cid = f"{pid}|{r.get('annotation') or r.get('text')}"
                st = r["state"]
                srcd = R3._src(self.sha, f"TEXT:{r.get('annotation')}", r.get("text"),
                               {"n_per_m": r.get("n"), "dia_mm": r.get("dia_mm"), "top": r.get("top")},
                               binding=r.get("binding"))
                if st in ("DUPLICATE_LABEL", "BOUND_TO_DETAIL"):
                    comps.append(RM.not_required(comp_id=cid, bar_role="SLAB_BAR", why=f"{st}: counted once / with "
                                                 f"the dome detail ({r.get('duplicate_of') or r.get('detail')})",
                                                 source=srcd, **nb))
                    continue
                if r.get("count") is None or not r.get("length_mm"):
                    comps.append(RM.blocked_component(comp_id=cid, bar_role="SLAB_BAR", why=f"slab bar {st}",
                                                      source=srcd, **nb))
                    continue
                layers = ["BOTTOM", "TOP"] if r.get("annotation") in tb["bound"] else ["TOP" if r.get("top") else
                                                                                          "BOTTOM"]
                for layer in layers:
                    c0 = self._slab_comp(r, cid + ("|T&B_TOP" if layer == "TOP" and not r.get("top") else ""), layer,
                                         srcd, base, tb)
                    comps += self._p15_split(r, c0, layer, srcd, base)
            if not comps:
                comps.append(RM.blocked_component(comp_id=f"{pid}|NO_ANNOTATION", bar_role="SLAB_BAR",
                                                  why="no slab reinforcement annotation bound on this floor",
                                                  source=R3._src(self.sha, f"slab sheet {fl}", "none", "NO_ANNOTATION"),
                                                  **nb))
            pop = RM.population(pop_id=pid, occurrence_state="ESTABLISHED", components=comps,
                                occurrence_why="slab panel coverage (every panel annotated) is not proven - the slab "
                                               "population stays a lower bound",
                                **{k: v for k, v in base.items() if k not in ("population_id", "cover_rule_id")})
            if pop["release_state"] == RM.VC:
                pop = RM.population(pop_id=pid, occurrence_state="ESTABLISHED", components=comps,
                                    release_override=RM.LB, occurrence_why="panel coverage unproven",
                                    **{k: v for k, v in base.items() if k not in ("population_id", "cover_rule_id")})
                pop["lower_bound_kg"], pop["verified_complete_kg"] = sum(x["verified_kg"] for x in comps), 0.0
            self.add(pop, comps)

    def _p15_split(self, r, c0, layer, srcd, base):
        """Apply the p.15 TYP. SLAB ON BEAMS rules to one R3 slab component (bottom per-metre bars and drawn top
        bars); everything else is returned unchanged with its rule classification."""
        span = (r.get("clear_span_mm") or 0) / 1000.0
        L = (r.get("length_mm") or 0) / 1000.0
        row = {"floor": r["floor"], "annotation": r.get("annotation"), "text": r.get("text"), "layer": layer,
               "binder_length_m": L, "clear_span_m": span or None, "drawn_length_m":
               (r.get("drawn_length_mm") or 0) / 1000.0 or None}
        tb_top = c0["comp_id"].endswith("|T&B_TOP")
        stop_ok = self.auth("P15-SLAB-BOTTOM-STOP") == VS.VERIFIED_AUTHORITY
        if (layer == "BOTTOM" and r.get("kind") == "PER_M" or layer == "BOTTOM" and r.get("n") and r.get("width_mm")) \
                and span > 0 and c0["state"] in (RM.COMPLETE, RM.PARTIAL) and stop_ok:
            nv, nc = c0["count"]["verified"], c0["count"]["convention"]
            sv, sc = math.ceil(nv / 2), math.ceil(nc / 2)
            stop_core = max(span * (1 - 2 * 0.125), 0.0)
            core_L = c0["verified_length_m"]
            out = []
            cnt_c = dict(c0["count"], verified=nv - sv, convention=nc - sc,
                         formula=c0["count"]["formula"] + f"; 50 % continue: {nv - sv} (+{(nc - sc) - (nv - sv)})")
            cnt_s = dict(c0["count"], verified=sv, convention=sc,
                         formula=c0["count"]["formula"] + f"; 50 % stop: {sv} (+{sc - sv})")
            for tag, cnt, parts in (
                    ("CONT50", cnt_c, [p for p in c0["parts"]]),
                    ("STOP50", cnt_s, [RM.part("CORE", min(stop_core, core_L), RM.COMPLETE,
                                               "p.15: stops 0.125 L before a continuous support face (worst case "
                                               "both supports continuous) - CROSS_VERIFIED rule"),
                                       RM.part("EXTENSION", max(core_L - min(stop_core, core_L), 0.0) +
                                               c0["provisional_length_m"], RM.PROVISIONAL,
                                               "support continuity not classified: up to the R3 binder length")])):
                out.append(RM.component(
                    comp_id=f"{c0['comp_id']}|{tag}", bar_role="SLAB_BAR", layer=layer,
                    direction=f"{r.get('annotation')}:{tag}", dia_mm=c0["dia_mm"], count=cnt, parts=parts,
                    source=dict(srcd, rule_claim="P15-SLAB-BOTTOM-STOP"), why=c0["why"],
                    formula=f"{cnt['formula']} x {sum(p['length_m'] for p in parts if p['length_m']):.3f} m x "
                            f"{c0['dia_mm']}^2/162", **base))
            row.update(rule="BOTTOM_50PCT_STOP_0.125L", r3_verified_kg=c0["verified_kg"],
                       r4_verified_kg=sum(x["verified_kg"] for x in out),
                       r4_provisional_kg=sum(x["provisional_kg"] for x in out),
                       classification="OVERCOUNT" if sum(x["verified_kg"] for x in out) < c0["verified_kg"] - 1e-6
                       else "MATCH_SOURCE",
                       why="R3 gave every bottom bar span + embedment; p.15 stops half of them 0.125 L short of each "
                           "continuous support - the difference is no longer verified")
            self.slab_rule_rows.append(row)
            return out
        if layer == "TOP" and r.get("top") and r.get("binding") == "DRAWN_BAR" and r.get("drawn_length_mm") and \
                span > 0 and c0["state"] in (RM.COMPLETE, RM.PARTIAL):
            dl = r["drawn_length_mm"] / 1000.0
            rule_len = 2 * 0.25 * span + 0.20
            c1 = RM.component(
                comp_id=c0["comp_id"], bar_role="SLAB_BAR", layer=layer, direction=r.get("annotation"),
                dia_mm=c0["dia_mm"], count=c0["count"],
                parts=[RM.part("CORE", dl, RM.COMPLETE, "drawn top bar on the slab plan (DXF line length)"),
                       RM.part("ANCHORAGE", None, RM.BLOCKED, "anchorage / hook at the bar ends", why="not detailed")],
                source=dict(srcd, rule_claim="P15-SLAB-TOP-NONCONTINUOUS"), why=c0["why"],
                formula=f"{c0['count']['formula']} x {dl:.3f} m (drawn) x {c0['dia_mm']}^2/162", **base)
            row.update(rule="TOP_BARS_DRAWN_EXTENT_VS_0.25L", r3_verified_kg=c0["verified_kg"],
                       r4_verified_kg=c1["verified_kg"], r4_provisional_kg=c1["provisional_kg"],
                       rule_length_m=round(rule_len, 3), drawn_vs_rule=round(dl / rule_len, 3),
                       classification="OVERCOUNT" if c1["verified_kg"] < c0["verified_kg"] - 1e-6 else "MATCH_SOURCE",
                       why="R3 gave this top bar the whole panel (span + embedment); the plan draws it "
                           f"{dl:.3f} m, consistent with 2 x 0.25 L + support ({rule_len:.3f} m)")
            self.slab_rule_rows.append(row)
            return [c1]
        row.update(rule="NOT_GOVERNED" if tb_top else ("PROVISIONAL_ALREADY" if c0["state"] == RM.PROVISIONAL else
                                                       "NO_SPAN"),
                   r3_verified_kg=c0["verified_kg"], r4_verified_kg=c0["verified_kg"],
                   r4_provisional_kg=c0["provisional_kg"],
                   classification="MATCH_SOURCE" if tb_top else "BLOCKED" if c0["state"] == RM.BLOCKED else
                   "UNCHANGED",
                   why="explicit (T&B) mesh: the project annotation governs the top layer" if tb_top else
                   "rule not applicable / not measurable for this row")
        self.slab_rule_rows.append(row)
        return [c0]

    # ------------------------------------------------------------------------------------------- run
    def carried(self):
        """Round 4 replaces the carried V3b populations; nothing is carried as opaque kg."""
        self.ground_beams()
        self.lintels()
        self.column_starters()
        self.boundary_wall()
        self.domes()
        self.pool()
        self.beam_residue()
        self.f_f10_retired()
        self.new_required_blocked()

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

    # ------------------------------------------------------------------------------------------- ground beams
    def ground_beams(self):
        import alsenan_v3_structure as V3S
        import alsenan_v3b_struct as V3BS
        gr = V3S.ground(self.ctx, self.ctx["_work"])
        fps = V3BS.ground_zones(self.ctx)["_fp"]
        rows = []
        for s in gr["spans"]:
            L = s["length_m"]
            occ = f"GB:{s['id']}"
            pid = f"POP:{occ}"
            self.rc_occ.append(occ)
            fp_ext = min(f.exterior.distance(s["_poly"]) for f in fps) < 5.0
            v3_ext = bool(s["exterior"])
            cats = {_cat(L), _cat(L + GB_LEN_BASIS_PAD_M)}
            if fp_ext and v3_ext:
                cand = {"EXT"}
            elif not fp_ext and not v3_ext:
                cand = set(cats)
            else:
                cand = {"EXT"} | cats
            primary = "EXT" if fp_ext else _cat(L)
            claims_ok = all(self.auth(GB_DETAILS[k]["claim"]) == VS.VERIFIED_AUTHORITY for k in cand)
            base = dict(population_id=pid, element_type="GROUND_BEAM", occurrence_id=occ, level="FOUNDATION",
                        cover_rule_id="COVER-SOIL-70")
            P = GB_DETAILS[primary]
            comps = []
            for role in ("TOP", "LOWER_1", "LOWER_2"):
                specs = {GB_DETAILS[k][role] for k in cand}
                n, d = P[role]
                agree = len(specs) == 1 and claims_ok
                core = RM.part("CORE", L, RM.COMPLETE if agree else RM.PROVISIONAL,
                               "clear span between columns (GBP bands, DXF)" if agree else
                               f"governing detail not established among {sorted(cand)}: {sorted(specs)}")
                comps.append(RM.component(
                    comp_id=f"{pid}|{role}", bar_role=role, layer="TOP" if role == "TOP" else role, dia_mm=d,
                    count=R3._cnt_abs(n, f"p.13 {P['rule']} section"),
                    parts=[core, RM.part("ANCHORAGE", None, RM.BLOCKED, "continuity / anchorage at the columns",
                                         why="not detailed")],
                    source=self.vsrc(P["claim"], {"count": n, "dia_mm": d, "row": role}, plan_span=s["id"],
                                     plan_band=s["band"]),
                    formula=f"{n} x {L:.3f} m x {d}^2/162", **base))
            st_specs = {GB_DETAILS[k]["STIR"] for k in cand}
            Ds = {GB_DETAILS[k]["D"] for k in cand}
            if P["STIR"] is None or None in st_specs:
                std, sp = 8, 150
                cnt = RM.bar_count("SPACING_MM", sp, L, basis="Ø8/15 inherited from the sibling sections - NOT printed "
                                                               "for the < 2.5 m section")
                loop = R3._loop(0.30, (P["D"] or EXT_D_ASSUMED), C_SOIL)
                parts = [RM.part("CORE", loop, RM.PROVISIONAL, "stirrup not printed for this section: sibling Ø8/15")]
                comps.append(RM.component(comp_id=f"{pid}|STIRRUPS", bar_role="STIRRUPS", dia_mm=std, count=cnt,
                                          bar_shape="CLOSED_LINK", parts=parts, forced_state=RM.PROVISIONAL,
                                          source=self.vsrc(P.get("section_claim") or P["claim"]),
                                          why="STIRRUP_SPEC_NOT_PRINTED (drawn, no callout)",
                                          formula=f"{cnt['formula']}; loop {loop:.3f} m (provisional)", **base))
            else:
                std, sp = P["STIR"]
                cnt = RM.bar_count("SPACING_MM", sp, L, basis=f"Ø{std}/{sp / 10:.0f}cm along the clear span")
                agree_s = len(st_specs) == 1 and claims_ok
                legs_h = 2 * (0.30 - 2 * C_SOIL)
                if len(Ds) == 1 and None not in Ds and agree_s:
                    parts = [RM.part("CORE", R3._loop(0.30, P["D"], C_SOIL), RM.COMPLETE, "closed loop at 70 mm cover")]
                else:
                    Dp = P["D"] or EXT_D_ASSUMED
                    parts = [RM.part("CORE", legs_h, RM.COMPLETE if agree_s else RM.PROVISIONAL,
                                     "two horizontal legs 2 (B - 2c)"),
                             RM.part("LEG", 2 * (Dp - 2 * C_SOIL), RM.PROVISIONAL,
                                     "vertical legs: depth " + ("FOLLOW ARCH. (assumed 1.00, V3b)" if P["D"] is None
                                                                else f"{Dp} - candidates disagree {sorted(map(str, Ds))}"))]
                parts.append(RM.part("HOOK", R3._hook135(std), RM.PROVISIONAL, "PROVISIONAL_HOOK_ALLOWANCE 2 x 135°"))
                comps.append(RM.component(comp_id=f"{pid}|STIRRUPS", bar_role="STIRRUPS", dia_mm=std, count=cnt,
                                          bar_shape="CLOSED_LINK", parts=parts, source=self.vsrc(P["claim"]),
                                          formula=f"{cnt['formula']}", **base))
            if primary == "EXT":
                n_side = 2 * max(0, math.floor((EXT_D_ASSUMED - 0.30) / 0.30))
                comps.append(RM.component(
                    comp_id=f"{pid}|SIDE_BARS", bar_role="SIDE_BARS", dia_mm=12,
                    count=R3._cnt_abs(n_side, "2Ø12/30cm over an ASSUMED 1.00 m depth"),
                    parts=[RM.part("CORE", L, RM.PROVISIONAL, "count depends on the FOLLOW ARCH. depth (not printed)")],
                    forced_state=RM.PROVISIONAL, source=self.vsrc("P13-GB-EXTERIOR"),
                    why="BLOCKED_DIMENSION depth -> provisional count", formula=f"{n_side} x {L:.3f} m x 12^2/162",
                    **base))
            else:
                comps.append(RM.not_required(comp_id=f"{pid}|SIDE_BARS", bar_role="SIDE_BARS",
                                             why="interior p.13 sections carry no side bars",
                                             **{k: v for k, v in base.items() if k != "cover_rule_id"}))
            pop = RM.population(pop_id=pid, element_type="GROUND_BEAM", occurrence_id=occ, level="FOUNDATION",
                                occurrence_state="ESTABLISHED", components=comps,
                                source={"plan_span": s["id"], "band": s["band"], "length_m": L},
                                occurrence_why="paired 300 mm GBP bands between columns (ST7757.dxf)")
            self.add(pop, comps)
            rows.append({"span": s["id"], "band": s["band"], "length_m": L, "v3_exterior_flag": v3_ext,
                         "footprint_edge": fp_ext, "length_categories": sorted(cats), "candidates": sorted(cand),
                         "primary_detail": primary,
                         "applicability": ("ESTABLISHED" if len(cand) == 1 else "AMBIGUOUS_GOVERNING_DETAIL"),
                         "release_state": pop["release_state"], "verified_kg": pop["lower_bound_kg"],
                         "provisional_kg": pop["provisional_kg"],
                         "components": [{"role": c["bar_role"], "state": c["state"], "dia_mm": c["dia_mm"],
                                         "count": (c["count"] or {}).get("verified"), "verified_kg": c["verified_kg"],
                                         "provisional_kg": c["provisional_kg"]} for c in comps]})
        self.registers["GROUND_BEAMS"] = rows

    # ------------------------------------------------------------------------------------------- lintels
    def lintels(self):
        sched = self.claims["P13-LINTEL-SCHEDULE"]["value"]
        bear_st = self.st("P13-LINTEL-BEARING")
        sch_st = self.st("P13-LINTEL-SCHEDULE")
        opn = {o["id"]: o for o in self.ctx["v3"]["openings"]["rows"]}
        rows = []
        for r in self.ctx["v3"]["openings"]["lintels"]:
            occ = f"LINTEL:{r['opening']}"
            pid = f"POP:{occ}"
            self.rc_occ.append(occ)
            base = dict(population_id=pid, element_type="LINTEL", occurrence_id=occ, level=r["floor"],
                        cover_rule_id="COVER-MEMBER-25")
            W = r.get("opening_width_m")
            row = next((x for x in sched if W and W * 100 <= x["max_cm"] + 1e-6), None) if W else None
            if r.get("status") != "COMPUTED" or row is None:
                comps = [RM.blocked_component(comp_id=f"{pid}|ALL", bar_role="ALL",
                                              why=f"opening width not established or outside the schedule "
                                                  f"({r.get('status')}: {r.get('why')})",
                                              source=self.vsrc("P13-LINTEL-SCHEDULE"),
                                              **{k: v for k, v in base.items() if k != "cover_rule_id"})]
                self.add(RM.population(pop_id=pid, element_type="LINTEL", occurrence_id=occ, level=r["floor"],
                                       occurrence_state="BLOCKED", components=comps,
                                       occurrence_why=r.get("why") or "opening width BLOCKED"), comps)
                rows.append({"opening": r["opening"], "state": "BLOCKED"})
                continue
            B = (opn.get(r["opening"]) or {}).get("wall_t_m") or r.get("B_m")
            D = row["D_cm"] / 100.0
            ext = max(2 * 0.40 - 2 * C_MEMBER, 0.0)
            comps = []
            for role, (n, d) in (("BOTTOM", row["bottom"]), ("TOP", row["top"])):
                comps.append(RM.component(
                    comp_id=f"{pid}|{role}", bar_role=role, layer=role, dia_mm=d,
                    count=R3._cnt_abs(n, f"lintel schedule row <= {row['max_cm']} cm"),
                    parts=[RM.part("CORE", W, sch_st, "bars span at least the opening width"),
                           RM.part("EXTENSION", ext, bear_st, "MIN.40cm bearing each side less end cover"),
                           RM.part("HOOK", None, RM.BLOCKED, "bar ends drawn bent", why="hook length not dimensioned")],
                    source=self.vsrc("P13-LINTEL-SCHEDULE", {"row_max_cm": row["max_cm"], "bars": [n, d]},
                                     opening=r["opening"], bearing_claim="P13-LINTEL-BEARING"),
                    formula=f"{n} x ({W:.3f} + {ext:.3f}) m x {d}^2/162", **base))
            sn, sd = row["stir_per_m"]
            cnt = RM.bar_count("BARS_PER_METRE", sn, W, basis="5Ø8/M over the opening width (verified)")
            cnt = dict(cnt, convention=RM.bar_count("BARS_PER_METRE", sn, W + 2 * 0.40)["convention"],
                       formula=cnt["formula"] + f"; convention over the lintel length {W + 0.8:.2f} m")
            comps.append(RM.component(
                comp_id=f"{pid}|STIRRUPS", bar_role="STIRRUPS", dia_mm=sd, count=cnt, bar_shape="CLOSED_LINK",
                parts=[RM.part("CORE", R3._loop(B, D, C_MEMBER), sch_st, f"loop B {B} (wall) x D {D}"),
                       RM.part("HOOK", R3._hook135(sd), RM.PROVISIONAL, "PROVISIONAL_HOOK_ALLOWANCE 2 x 135°")],
                source=self.vsrc("P13-LINTEL-SCHEDULE", {"stirrups": "5Ø8/M"}, opening=r["opening"]),
                formula=cnt["formula"], **base))
            pop = RM.population(pop_id=pid, element_type="LINTEL", occurrence_id=occ, level=r["floor"],
                                occurrence_state="ESTABLISHED", components=comps,
                                source={"opening": r["opening"], "kind": r.get("kind"), "width_m": W},
                                occurrence_why="opening in a block wall with a measured width (lintel schedule note: "
                                               "B = width of the block wall)")
            self.add(pop, comps)
            rows.append({"opening": r["opening"], "width_m": W, "row_max_cm": row["max_cm"], "B_m": B, "D_m": D,
                         "release_state": pop["release_state"], "verified_kg": pop["lower_bound_kg"],
                         "provisional_kg": pop["provisional_kg"]})
        self.registers["LINTELS"] = rows

    # ------------------------------------------------------------------------------------------- starters + necks
    def column_starters(self):
        defs = {d["type"]: d for d in self.ctx["a3"]["rebar"]["definitions"] if d["element"] == "COLUMN"}
        hs = []
        for f in self.ctx["a3"]["footings"]["rows"]:
            if str(f.get("status", "")).startswith("COMPUTED"):
                hs.append(f["dims"]["H"]["m"])
        hmin = min(hs) if hs else None
        proj_st = self.st("P13-STARTER-PROJECTION-40D")
        foot_st = self.st("P13-STARTER-FOOT-MIN30")
        rows = []
        for p in [p for p in list(self.pops) if p["element_type"] == "COLUMN" and p["level"] == "GF"
                  and p["release_state"] not in (RM.NIS,)]:
            typ = p["occurrence_id"].split(":")[2]
            fb = ((defs.get(typ) or {}).get("bars") or {}).get("FOUNDATION") or []
            occ = f"STARTERS:{p['occurrence_id']}"
            pid = f"POP:{occ}"
            self.rc_occ.append(occ)
            base = dict(population_id=pid, element_type="COLUMN_STARTERS", occurrence_id=occ, level="FOUNDATION",
                        cover_rule_id="COVER-SOIL-70")
            comps = []
            if not fb or hmin is None:
                comps.append(RM.blocked_component(comp_id=f"{pid}|STARTERS", bar_role="STARTERS",
                                                  why="no FOUNDATION bars for this column type / no footing depth",
                                                  source=R3._src(self.sha, f"CGT {typ} FOUNDATION", None, None),
                                                  **{k: v for k, v in base.items() if k != "cover_rule_id"}))
            for b in fb:
                n, d = b["count"], b["dia_mm"]
                comps.append(RM.component(
                    comp_id=f"{pid}|STARTERS|{d}", bar_role="STARTERS", dia_mm=d,
                    count=R3._cnt_abs(n, f"CGT {typ} FOUNDATION band"),
                    parts=[RM.part("CORE", hmin - C_SOIL, RM.COMPLETE,
                                   f"embedment to the bottom mesh: smallest established footing depth {hmin} - 70 mm"),
                           RM.part("LEG", 0.30, foot_st, "p.13 horizontal foot Min. 30cm"),
                           RM.part("EXTENSION", 40 * d / 1000.0, proj_st, "p.13 '40 ø' projection above the footing top "
                                                                         "(+ p.8 note 9 compression 40Ø)")],
                    source=R3._src(self.sha, f"CGT {typ} FOUNDATION", f"{n} Ø {d}", {"count": n, "dia_mm": d},
                                   detail_claims=["P13-STARTER-PROJECTION-40D", "P13-STARTER-FOOT-MIN30"]),
                    formula=f"{n} x ({hmin - C_SOIL:.3f} + 0.30 + {40 * d / 1000:.3f}) m x {d}^2/162", **base))
                comps.append(RM.blocked_component(
                    comp_id=f"{pid}|NECK_VERTICALS|{d}", bar_role="NECK_VERTICALS", dia_mm=d,
                    why="BLOCKED_DIMENSION: column bars from the footing top to the GF level - founding level is a site "
                        "decision (p.8 note 12) and no neck height is printed",
                    source=R3._src(self.sha, f"CGT {typ} FOUNDATION", f"{n} Ø {d}", "neck height BLOCKED"),
                    **{k: v for k, v in base.items() if k != "cover_rule_id"}))
            ost = p["occurrence_state"] if p["occurrence_state"] in ("ESTABLISHED", "PROVISIONAL") else "BLOCKED"
            pop = RM.population(pop_id=pid, element_type="COLUMN_STARTERS", occurrence_id=occ, level="FOUNDATION",
                                occurrence_state=ost, components=comps, source={"column": p["occurrence_id"]},
                                occurrence_why=f"one starter set per GF column ({p['release_state']})")
            self.add(pop, comps)
            rows.append({"column": p["occurrence_id"], "type": typ, "foundation_bars": [[b["count"], b["dia_mm"]]
                                                                                       for b in fb],
                         "release_state": pop["release_state"], "verified_kg": pop["lower_bound_kg"],
                         "provisional_kg": pop["provisional_kg"], "audit_kg": pop["audit_kg"]})
        self.registers["STARTERS"] = {"footing_depth_min_m": hmin, "rows": rows}

    # ------------------------------------------------------------------------------------------- boundary wall
    def boundary_wall(self):
        bw = self.ctx["v3b"]["struct"]["boundary_wall"]
        occ = "BOUNDARY_WALL:S-BOUN"
        pid = f"POP:{occ}"
        self.rc_occ.append(occ)
        L = bw["length_m"]
        sch = next((d for d in self.dmap.get(("SIMPLE_BEAM", "B.W"), [])), None)
        base = dict(population_id=pid, element_type="BOUNDARY_WALL", occurrence_id=occ, level="EXTERNAL")
        F = (sch or {}).get("fields", {})
        k = RM.kgm
        cand_sched = ((F.get("bottom", {}).get("count", 0) * k(F.get("bottom", {}).get("dia_mm", 0)) +
                       F.get("top", {}).get("count", 0) * k(F.get("top", {}).get("dia_mm", 0))) * L) if F else None
        cand_typ = (2 * 2 * k(14) + 2 * 3 * k(16)) * L
        comps = [
            RM.blocked_component(comp_id=f"{pid}|BEAM", bar_role="BW_BEAM",
                                 why="SOURCE_CONFLICT: schedule row B.W (20 x 60, 4Ø16 / 2Ø14, 7Ø8/m) vs p.14 typical "
                                     "boundary wall (ground beam 20 x 40, 2Ø14 (T&B) / 3Ø16 (T&B), Ø8/20) - neither "
                                     "selected", source=self.vsrc("P14-BOUNDARY-WALL-TYPICAL", schedule_row="B.W"),
                                 **base),
            RM.blocked_component(comp_id=f"{pid}|COLUMNS", bar_role="BW_COLUMNS",
                                 why="20 x 30 columns 4Ø14 at 'SEE ARCH PLAN' spacing - count / height not printed",
                                 source=self.vsrc("P14-BOUNDARY-WALL-TYPICAL"), **base),
            RM.blocked_component(comp_id=f"{pid}|PADS", bar_role="BW_PADS",
                                 why="130 x 80 x 30 pads (7Ø12 / 4Ø12 B.W) - one per column; count not printed",
                                 source=self.vsrc("P14-BOUNDARY-WALL-TYPICAL"), **base),
            RM.blocked_component(comp_id=f"{pid}|LOWER_BEAM", bar_role="BW_LOWER_BEAM",
                                 why="second (lower) beam at the pad level: depth 'AS PER EXCAVATION DEPTH'",
                                 source=self.vsrc("P14-BOUNDARY-WALL-TYPICAL"), **base)]
        pop = RM.population(pop_id=pid, element_type="BOUNDARY_WALL", occurrence_id=occ, level="EXTERNAL",
                            occurrence_state="ESTABLISHED", components=comps, source={"run_m": L, "runs": bw["runs"]},
                            occurrence_why="S-BOUN outline on the GBP sheet (DXF)")
        self.add(pop, comps)
        self.registers["BOUNDARY_WALL"] = {
            "run_m": L, "release_state": pop["release_state"],
            "candidates_longitudinal_kg_audit_only": {"schedule_B.W": cand_sched,
                                                      "typical_p14_as_read": cand_typ},
            "decision": "SOURCE_CONFLICT - no candidate selected (as SB2)"}

    # ------------------------------------------------------------------------------------------- domes
    def domes(self):
        rows = []
        for r in self.ctx["v3b"]["struct"]["domes"]["rows"]:
            occ = f"DOME:{r['id']}"
            pid = f"POP:{occ}"
            self.rc_occ.append(occ)
            rb = r.get("ring_beam") or {}
            span, cl, B, D = r["span_m"], float(rb.get("centreline_diameter_m") or 0), float(rb.get("B_m") or 0), \
                float(rb.get("D_drawn_m") or 0)
            base = dict(population_id=pid, element_type="DOME", occurrence_id=occ, level=r["location"],
                        cover_rule_id="COVER-MEMBER-25")
            srcd = lambda raw, norm: R3._src(self.sha, "ST7757.dxf DETAIL OF DOME (S-TEXT.D)", raw, norm,
                                             plan_circle=r["plan_circle"], detail_factor=r.get("detail_factor"))
            inner = math.pi * max(cl - B + 2 * C_MEMBER, 0.0)
            ring = math.pi * cl
            comps = []
            for role, n, d, raw in (("RING_TOP", 3, 16, "3%%c16"), ("RING_BOTTOM", 3, 18, "3%%c18")):
                comps.append(RM.component(
                    comp_id=f"{pid}|{role}", bar_role=role, dia_mm=d, count=R3._cnt_abs(n, "DXF text"),
                    parts=[RM.part("CORE", inner, RM.COMPLETE, "innermost bar circle (detail scaled by the printed 442)"),
                           RM.part("EXTENSION", ring - inner, RM.PROVISIONAL, "to the ring-beam centreline circle")],
                    source=srcd(raw, {"count": n, "dia_mm": d}), laps=RM.lap_parts(ring, d),
                    formula=f"{n} x pi x {cl:.3f} m x {d}^2/162", **base))
            comps.append(RM.component(
                comp_id=f"{pid}|RING_SIDE", bar_role="RING_SIDE", dia_mm=14,
                count=R3._cnt_abs(4, "2Ø14/20cm over the drawn depth (AS PER ARCH)"),
                parts=[RM.part("CORE", ring, RM.PROVISIONAL, "count depends on the ring depth 'AS PER ARCH'")],
                forced_state=RM.PROVISIONAL, source=srcd("2%%c14/20cm", "2 per 20 cm of depth"),
                formula=f"4 x {ring:.3f} m x 14^2/162", **base))
            cnt = RM.bar_count("BARS_PER_METRE", 8, ring, basis="8Ø8/m along the ring")
            comps.append(RM.component(
                comp_id=f"{pid}|RING_LINKS", bar_role="RING_LINKS", dia_mm=8, count=cnt, bar_shape="CLOSED_LINK",
                parts=[RM.part("CORE", 2 * (B - 2 * C_MEMBER), RM.COMPLETE, "horizontal legs 2 (B - 2c)"),
                       RM.part("LEG", 2 * (D - 2 * C_MEMBER), RM.PROVISIONAL, "vertical legs: depth AS PER ARCH (drawn)"),
                       RM.part("HOOK", R3._hook135(8), RM.PROVISIONAL, "PROVISIONAL_HOOK_ALLOWANCE 2 x 135°")],
                source=srcd("8%%c8/m", "8 links per metre"), formula=cnt["formula"], **base))
            r_pl = span / 2.0 - C_MEMBER
            mer = RM.bar_count("SPACING_MM", 150, math.pi * span, basis="Ø12/15cm round the springing circle")
            arc = None
            if r.get("R_m") and r.get("rise_m"):
                Rm = r["R_m"]
                arc = Rm * math.asin(min(span / 2.0 / Rm, 1.0)) if r["rise_m"] <= Rm else Rm * (
                    math.pi - math.asin(min(span / 2.0 / Rm, 1.0)))
            comps.append(RM.component(
                comp_id=f"{pid}|SHELL_MERIDIONAL", bar_role="SHELL_MERIDIONAL", dia_mm=12, count=mer,
                parts=[RM.part("CORE", r_pl, RM.COMPLETE, "springing -> crown >= plan radius"),
                       RM.part("EXTENSION", max((arc or r_pl) - r_pl, 0.0), RM.PROVISIONAL,
                               f"meridian arc from the elevation rise {r.get('rise_m')} m (raster claim "
                               f"{r.get('rise_source')}; the N.I.S. detail prints 190)")],
                source=srcd("%%C12MM/15cm", "meridional Ø12 @ 150"), formula=mer["formula"], **base))
            plan_a = math.pi * (span / 2.0) ** 2
            comps.append(RM.component(
                comp_id=f"{pid}|SHELL_HOOPS", bar_role="SHELL_HOOPS", dia_mm=12,
                count=R3._cnt_abs(1, "hoop set as total length"),
                parts=[RM.part("CORE", plan_a / 0.15, RM.COMPLETE, "plan-projected area / 0.15 (surface >= plan)"),
                       RM.part("EXTENSION", max((r.get("mid_area_m2") or 0) - plan_a, 0.0) / 0.15, RM.PROVISIONAL,
                               "mid-surface area (elevation rise) / 0.15")],
                source=srcd("%%C12MM/15cm", "hoops Ø12 @ 150"), formula=f"{plan_a:.3f} m2 / 0.15 x 12^2/162", **base))
            pop = RM.population(pop_id=pid, element_type="DOME", occurrence_id=occ, level=r["location"],
                                occurrence_state="ESTABLISHED", components=comps,
                                source={"plan_circle": r["plan_circle"], "span_m": span},
                                occurrence_why="P7757 plan dome circle matched to the single DETAIL OF DOME (span "
                                               "4.42 printed)")
            self.add(pop, comps)
            rows.append({"dome": r["id"], "span_m": span, "rise_m": r.get("rise_m"), "rise_source": r.get("rise_source"),
                         "release_state": pop["release_state"], "verified_kg": pop["lower_bound_kg"],
                         "provisional_kg": pop["provisional_kg"]})
        self.registers["DOMES"] = rows

    # ------------------------------------------------------------------------------------------- pool
    def pool(self):
        pl = self.ctx["v3b"]["struct"]["pool"]
        occ = "POOL:SWIM"
        pid = f"POP:{occ}"
        self.rc_occ.append(occ)
        base = dict(population_id=pid, element_type="POOL", occurrence_id=occ, level="EXTERNAL",
                    cover_rule_id="COVER-SOIL-70")
        comps = []
        if pl.get("state") != "DERIVED":
            comps.append(RM.blocked_component(comp_id=f"{pid}|ALL", bar_role="ALL", why=f"pool {pl.get('state')}",
                                              source=R3._src(self.sha, "DETAIL OF SWIMMING POOL", None, None),
                                              **{k: v for k, v in base.items() if k != "cover_rule_id"}))
        else:
            L, W = pl["inner_m"]
            wall, Dp, bt = pl["wall_t_m"], pl["depth_m"], pl["base_t_m"]
            per = 2 * ((L + wall) + (W + wall))
            Lo, Wo = L + 2 * wall, W + 2 * wall
            why = ("label -> member mapping of the N.I.S. pool detail is an AI reading; the detail's sloped floor (deep "
                   "7Ø14/m, slope 6Ø14/m, shallow 6Ø12/m) is not on the 1.55 x 3.10 plan; depth from a raster claim")
            src = lambda raw: R3._src(self.sha, "ST7757.dxf DETAIL OF SWIMMING POOL (S-TEXT.D)", raw, "AI mapping",
                                      depth_source=pl.get("depth_source"))
            sets = [("BASE_LONG_TB", 14, RM.bar_count("BARS_PER_METRE", 7, Wo), Lo, 2, "7%%c14/m"),
                    ("BASE_SHORT_TB", 14, RM.bar_count("BARS_PER_METRE", 7, Lo), Wo, 2, "7%%c14/m"),
                    ("WALL_VERTICAL_OUTER", 14, RM.bar_count("BARS_PER_METRE", 7, per), Dp + bt - 0.05, 1, "7%%c14/m"),
                    ("WALL_VERTICAL_INNER", 12, RM.bar_count("BARS_PER_METRE", 6, per), Dp + bt - 0.05, 1, "6%%c12/m"),
                    ("WALL_HORIZONTAL", 12, RM.bar_count("SPACING_MM", 200, Dp), per, 2, "%%c12/20cm")]
            for role, d, cnt, Lb, mult, raw in sets:
                cnt = dict(cnt, verified=cnt["verified"] * mult, convention=cnt["convention"] * mult)
                comps.append(RM.component(comp_id=f"{pid}|{role}", bar_role=role, dia_mm=d, count=cnt,
                                          parts=[RM.part("CORE", Lb, RM.PROVISIONAL, why)], forced_state=RM.PROVISIONAL,
                                          source=src(raw), why=why, formula=f"{cnt['verified']} x {Lb:.3f} m x {d}^2/162",
                                          **base))
        pop = RM.population(pop_id=pid, element_type="POOL", occurrence_id=occ, level="EXTERNAL",
                            occurrence_state="ESTABLISHED", components=comps, source={"pool": pl.get("swim_block")},
                            occurrence_why="SWIM block + S-BW outlines on the GBP sheet (DXF)")
        self.add(pop, comps)

    # ------------------------------------------------------------------------------------------- residue
    def beam_residue(self):
        for s in [s for s in self.ctx["v3b"]["rebar"]["weighed"] if s["population"] == "BEAM_RESIDUE"]:
            occ = f"UNBOUND_TAG:{s['ref'].split('|')[0]}|{s['ref'].split('|')[1]}"
            pid = f"POP:{occ}"
            self.rc_occ.append(occ)
            comps = [RM.blocked_component(
                comp_id=f"{pid}|ALL", population_id=pid, element_type="BEAM_UNBOUND_TAG", occurrence_id=occ,
                level=s.get("level"), bar_role="ALL", audit_kg=s.get("net_kg") or 0.0,
                why="unbound beam tag (no adjacent band): occurrence not established and may repeat a measured beam - "
                    "V3b BUDGET weight kept as audit only",
                source=R3._src(self.sha, f"TEXT {s['ref']}", s["ref"], s.get("basis")))]
            self.add(RM.population(pop_id=pid, element_type="BEAM_UNBOUND_TAG", occurrence_id=occ, level=s.get("level"),
                                   occurrence_state="BLOCKED", components=comps,
                                   occurrence_why="REBAR_BLOCKED_OCCURRENCE_NOT_ESTABLISHED (unbound tag)"), comps)

    def f_f10_retired(self):
        """V3b carried 'F10 selected' as provisional: selecting one side of the F / F10 source conflict is not allowed
        (as SB2). The Round-3 footing populations F#n / F10#n already carry the pair as BLOCKED with audit kg."""
        self.registers["F_F10"] = {"v3b_population": "FOOTING_F_F10", "state": "RETIRED_DUPLICATE",
                                   "why": "the conflict pair is already the BLOCKED Round-3 footing populations; no "
                                          "side is selected"}

    # ------------------------------------------------------------------------------------------- new blocked
    def new_required_blocked(self):
        ivs = {iv["from"]: iv["interval_m"] for iv in self.ctx["b2a"]["intervals"]}
        th = self.claims["P8-N19-LIFT-TIE-BEAMS"]["value"]["storey_threshold_m"]
        self.registers["LIFT_TIE_BEAMS"] = []
        for fl, h in sorted(ivs.items()):
            need = h is not None and h > th
            self.registers["LIFT_TIE_BEAMS"].append({"storey": fl, "interval_m": h, "required": need})
            if need:
                self._blocked_pop(f"LIFT_TIE_BEAMS:{fl}", "LIFT_TIE_BEAM", fl,
                                  f"p.8 note 19: storey {h} m > {th} m -> tie beams round the lift shaft at 3.00 m; "
                                  "section, bars and plan position not printed", "P8-N19-LIFT-TIE-BEAMS")
        for t in [x for x in self.src["loose"] if x["raw"].upper().startswith("P.C")]:
            self._blocked_pop(f"PLANTED_COLUMN:{t['handle']}", "PLANTED_COLUMN", "SLAB_SHEET",
                              f"'{t['raw']}' on a slab sheet: planted-column bars not in the column schedule; the p.15 "
                              "beam detail adds 4Ø16 + stirrups over 'DEPTH' (lengths not printed)", "P15-PLANTED-COLUMN")
        self._blocked_pop("PARAPET_RC:ROOF", "PARAPET_RC", "ROOF",
                          "p.14 parapet details read; none is bound to an Alsenan roof edge (BLOCKED_DETAIL_APPLICABILITY)",
                          "P14-PARAPETS")
        tr = self.temperature_register()
        for row in tr["floors"]:
            self._blocked_pop(f"TEMPERATURE:{row['floor']}", "TEMPERATURE_REINFORCEMENT", row["floor"],
                              f"{row['state']}: slab {row['thickness_mm']} mm is not a printed row "
                              f"({row['bracket']}); candidate top mid-span regions in {row['candidate_panels']} panels",
                              "P15-TEMPERATURE-SCHEDULE")

    def _blocked_pop(self, occ, et, level, why, cid):
        pid = f"POP:{occ}"
        self.rc_occ.append(occ)
        comps = [RM.blocked_component(comp_id=f"{pid}|ALL", population_id=pid, element_type=et, occurrence_id=occ,
                                      level=level, bar_role="ALL", why=why, source=self.vsrc(cid))]
        self.add(RM.population(pop_id=pid, element_type=et, occurrence_id=occ, level=level,
                               occurrence_state="ESTABLISHED", components=comps, occurrence_why=why), comps)

    # ------------------------------------------------------------------------------------------- temperature
    def temperature_register(self):
        rows = self.claims["P15-TEMPERATURE-SCHEDULE"]["value"]
        table = {t: (d, s) for t, d, s in rows}
        slab_rows = self.ctx["v3b"]["struct"]["slab"]["rows"]
        tb = self.registers.get("SLAB_TB", {}).get("bound", {})
        out = []
        for fl in ("GF", "1F", "2F"):
            t = (self.slab_tags_cm.get(fl) or 0) * 10
            below = max([x for x in table if x < t], default=None)
            above = min([x for x in table if x > t], default=None)
            exact = t in table
            br = (f"between {below} ({'Y%d@%d' % table[below]}) and {above} ({'Y%d@%d' % table[above]})"
                  if below and above else "outside the table")
            panels = [r for r in slab_rows if r["floor"] == fl and not r.get("top") and r.get("annotation") not in tb
                      and r["state"] in ("BOUND", "BOUND_TEXT_ONLY", "PARTIAL")]
            area = sum((r.get("clear_span_mm") or 0) * (r.get("width_mm") or 0) for r in panels) / 1e6
            out.append({"floor": fl, "thickness_mm": t, "thickness_source": "slab-sheet thickness tag (DXF)",
                        "exact_row": exact, "state": "EXACT_MATCH" if exact else "SOURCE_RULE_NOT_EXACT_MATCH",
                        "bracket": br, "bracket_consistent": bool(below and above and table[below] == table[above]),
                        "candidate_panels": len(panels), "candidate_panel_area_m2_upper_bound": round(area, 3),
                        "region_rule": "top of slab in mid-span where no top bars (p.15 detail) + 2000 mm across beams "
                                       "parallel to the main bars (note 2)",
                        "quantity": "BLOCKED (no rounding to a neighbouring row)"})
        reg = {"table": rows, "notes_claim": "P15-TEMPERATURE-NOTES", "lap_rule": "40 x Ø (note 1)", "floors": out,
               "slab_thickness_default_claim": "P8-N18-SLAB-THICKNESS (160 mm)"}
        self.registers["TEMPERATURE"] = reg
        return reg


# ===================================================================================================== D5
def d5_reconciliation(ctx) -> list:
    """Classify every column occurrence Round 3 kept BLOCKED (the 26 'D5' rows) from the storey evidence only:
       OFF_STOREY_COLUMN               not drawn on this storey's framing sheet nor any above, drawn below;
       REAL_COLUMN_UPPER_MEMBER_UNBOUND one outline on this storey, tag bound; only the framing member is unbound;
       REAL_COLUMN_SEVERAL_OUTLINES    tag bound, several outlines at the location (which outline is ambiguous);
       UNRESOLVED                      tag not bound to any outline of its printed size.
    Only the first two change the release; a candidate never restores kg by itself."""
    rows = ctx["b2a"]["columns"]["rows"]
    by_tag = defaultdict(dict)
    for r in rows:
        by_tag[r["tag_key"]][r["floor"]] = r
    ivs = {iv["from"]: iv["interval_m"] for iv in ctx["b2a"]["intervals"]}
    order = ["GF", "1F", "2F"]
    out = []
    for r in rows:
        if r.get("volume_m3") is not None or r["state"] == "NOT_IN_STOREY":
            continue
        fl = r["floor"]
        seq = by_tag[r["tag_key"]]
        lower = [seq.get(f, {}).get("state") for f in order[:order.index(fl)]]
        upper = [seq.get(f, {}).get("state") for f in order[order.index(fl) + 1:]]
        lower_drawn = any(s and s not in ("NOT_DRAWN_ON_STOREY_SHEET", "NOT_IN_STOREY") and
                          seq[f].get("volume_m3") is not None for f, s in zip(order, lower))
        if r["state"] == "NOT_DRAWN_ON_STOREY_SHEET" and lower_drawn and all(
                s in (None, "NOT_DRAWN_ON_STOREY_SHEET", "NOT_IN_STOREY") for s in upper):
            cls = "OFF_STOREY_COLUMN"
            ev = (f"no outline on the {fl} framing sheet nor above ({upper or 'top storey'}); drawn and measured below "
                  f"({[f for f in order[:order.index(fl)] if seq.get(f, {}).get('volume_m3') is not None]})")
        elif r["state"] == "BLOCKED_UPPER_MEMBER_UNBOUND":
            cls = "REAL_COLUMN_UPPER_MEMBER_UNBOUND"
            ev = (f"tag bound; one outline {r.get('storey_outline_mm')} at {r.get('storey_outline_centre')} on the {fl} "
                  "sheet; only the framing member above is unbound (clear height lower bound = storey - deepest beam)")
        elif r["state"] == "BLOCKED_SEVERAL_OUTLINES_ON_STOREY_SHEET":
            cls = "REAL_COLUMN_SEVERAL_OUTLINES"
            ev = f"tag bound; several outlines at the location on the {fl} sheet - which outline carries it is ambiguous"
        elif r["state"] == "NOT_DRAWN_ON_STOREY_SHEET":
            cls = "UNRESOLVED"
            ev = f"not drawn on {fl}; storeys above {upper} - not a clean off-storey pattern"
        else:
            cls = "UNRESOLVED"
            ev = f"{r['state']} ({r.get('tag_binding')}): no outline of the printed size beside the tag"
        out.append({"occurrence": f"COLUMN:{fl}:{r['type']}:{r['tag_key'].split('|')[1]}", "floor": fl,
                    "type": r["type"], "r3_state": r["state"], "tag_binding": r.get("tag_binding"),
                    "storeys": {f: seq.get(f, {}).get("state") for f in order}, "storey_interval_m": ivs.get(fl),
                    "classification": cls, "evidence": ev,
                    "kg_restored": cls in ("REAL_COLUMN_UPPER_MEMBER_UNBOUND", "REAL_COLUMN_SEVERAL_OUTLINES")})
    return out


# ===================================================================================================== CB candidates
def _support_t(sheet, o):
    """Position (along the band) and kind of every support Round 2 used for one CB occurrence."""
    br = o["band_record"]
    u = br["u"]
    cols = {c["id"]: c for c in sheet["columns"]}
    lines = {}
    for ln in sheet["_lines"]:
        for k in ln["keys"]:
            lines[k] = ln
    out = []
    for s in o.get("supports_used") or []:
        t = None
        for k in s["keys"]:
            if k in cols:
                cx, cy = cols[k]["centre"]
                t = cx * u[0] + cy * u[1]
            elif k in lines:
                ln = lines[k]
                if abs(ln["u"][0] * u[0] + ln["u"][1] * u[1]) < 0.1:           # perpendicular line: offset = position
                    t = ln["offset"] * (1 if (ln["n"][0] * u[0] + ln["n"][1] * u[1]) > 0 else -1)
            if t is not None:
                break
        out.append({"kind": s["kind"], "t": t})
    return out


def _collinear_extension(sheet, br, gap=1200.0):
    """Extend a band along its axis through lines of the same two edges (same offsets) separated by <= gap."""
    u = br["u"]
    lo, hi = br["lo"], br["hi"]
    segs = []
    for ln in sheet["_lines"]:
        if abs(ln["u"][0] * u[1] - ln["u"][1] * u[0]) > 0.01:
            continue
        sgn = 1 if (ln["n"][0] * br["n"][0] + ln["n"][1] * br["n"][1]) > 0 else -1
        off = ln["offset"] * sgn
        if abs(off - lo) <= 5 or abs(off - hi) <= 5:
            a, b = sorted((ln["t0"] * (1 if ln["u"][0] * u[0] + ln["u"][1] * u[1] > 0 else -1),
                           ln["t1"] * (1 if ln["u"][0] * u[0] + ln["u"][1] * u[1] > 0 else -1)))
            segs.append((a, b))
    t0, t1 = br["t0"], br["t1"]
    changed = True
    while changed:
        changed = False
        for a, b in segs:
            if b >= t0 - gap and a < t0 - 1:
                t0, changed = a, True
            if a <= t1 + gap and b > t1 + 1:
                t1, changed = b, True
    return t0, t1


def cb_candidates(ctx, dmap) -> list:
    """CB_OCCURRENCE_CANDIDATE_REGISTER: every CB occurrence Round 3 did not establish and every unbound CB tag,
    scored on breadth, length vs the schedule span sum, column-support span count, tag position, collinear extension.
    ACCEPTED_STRONG only when every factor agrees and nothing contradicts; otherwise the evidence is listed."""
    out = []
    for fl, sh in ctx["b2a"]["sheets"].items():
        for o in [o for o in sh["occurrences"] if o["type"].startswith("CB")]:
            df = (dmap.get(("CONTINUOUS_BEAM", o["type"])) or [None])[0]
            if df is None:
                continue
            spans = df["fields"]["spans_m"]
            sched = sum(spans)
            L = o.get("lengths") or {}
            Ls, Lc = L.get("SUPPORT_CENTRELINE_LENGTH"), L.get("CLEAR_FACE_TO_FACE_LENGTH")
            tag = o["tags"][0].split("|")[1] if o["tags"] else "NOTAG"
            occ = f"CB:{fl}:{o['type']}:{tag}"
            if o["state"] == "MEASURED" and Ls and abs(Ls - sched) / sched <= 0.05:
                continue                                                    # already ESTABLISHED in Round 3
            ev, contra, factors = [], [], {}
            factors["breadth_mm"] = {"drawn": o.get("drawn_breadth_mm"), "schedule": df["fields"]["B_cm"] * 10,
                                     "agree": o.get("drawn_breadth_mm") == df["fields"]["B_cm"] * 10}
            if o["state"] == "BAND_TYPE_CONFLICT":
                contra.append(f"band also claimed by {o.get('conflict_with')} (two types, one band)")
            br = o["band_record"]
            Lb = (br["t1"] - br["t0"]) / 1000.0
            factors["length"] = {"centreline_m": Ls, "clear_m": Lc, "drawn_band_m": round(Lb, 3),
                                 "schedule_sum_m": sched}
            if abs(Lb - sched) / sched <= 0.05:
                ev.append(f"drawn band {Lb:.3f} m within 5 % of the schedule {sched:.2f} m (but support-to-support "
                          "length not measured)")
            if Ls and abs(Ls - sched) / sched <= 0.05:
                ev.append(f"centreline {Ls:.3f} m within 5 % of the schedule {sched:.2f} m")
                factors["length"]["agree"] = True
            else:
                t0, t1 = _collinear_extension(sh, br)
                ext = (t1 - t0) / 1000.0
                factors["collinear_extension_m"] = round(ext, 3)
                if ext > Lb + 0.5 and abs(ext - sched) / sched <= 0.08:
                    ev.append(f"collinear band continues to {ext:.2f} m (schedule {sched:.2f} m)")
                    contra.append("the extension crosses another member's support zone - continuity not proven")
                else:
                    contra.append(f"plan length {Ls or Lc or round(Lb, 3)} m vs schedule {sched:.2f} m")
                factors["length"]["agree"] = False
            sup = _support_t(sh, o)
            if sup and all(s["t"] is not None for s in sup):
                ts = sorted(s["t"] for s in sup)
                ends = (ts[0], ts[-1])
                interior_cols = [s for s in sup if s["kind"] == "COLUMN" and ends[0] + 1 < s["t"] < ends[1] - 1]
                interior_all = [s for s in sup if ends[0] + 1 < s["t"] < ends[1] - 1]
                factors["supports"] = {"interior_all": len(interior_all), "interior_columns": len(interior_cols),
                                       "kinds": [s["kind"] for s in sup], "schedule_spans": len(spans)}
                if len(interior_cols) + 1 == len(spans):
                    extra = [s['kind'] for s in interior_all if s['kind'] != 'COLUMN']
                    ev.append(f"column-supported span count {len(interior_cols) + 1} = schedule spans {len(spans)}"
                              + (f" (Round 2 also cut the band at a non-column {extra} line - not a schedule support)"
                                 if extra else ""))
                    factors["supports"]["agree"] = True
                else:
                    contra.append(f"column-supported spans {len(interior_cols) + 1} vs schedule {len(spans)}")
                    factors["supports"]["agree"] = False
            else:
                contra.append("support positions not resolvable")
            ok = (not contra and factors["breadth_mm"]["agree"] and factors["length"].get("agree") and
                  factors.get("supports", {}).get("agree"))
            out.append({"occurrence": occ, "type": o["type"], "floor": fl, "r3_state": o["state"],
                        "candidate": f"band {br['edge_keys']}", "evidence": ev, "contradictions": contra,
                        "score_factors": factors, "decision": "ACCEPTED_STRONG" if ok else "NOT_ACCEPTED",
                        "why": "; ".join(ev) if ok else "; ".join(contra)})
        # unbound CB tags
        for r in [r for r in sh["binding"] if r["namespace"] == "CONTINUOUS" and r["state"] != "BOUND"]:
            df = (dmap.get(("CONTINUOUS_BEAM", r["type"])) or [None])[0]
            sched = sum(df["fields"]["spans_m"]) if df else None
            x, y = r["mark_xy"]
            rot = math.radians(r.get("rotation_deg") or 0.0)
            ux, uy = math.cos(rot), math.sin(rot)
            B = (r.get("B_cm") or 0) * 10
            cands = []
            par = [ln for ln in sh["_lines"] if abs(ln["u"][0] * uy - ln["u"][1] * ux) < 0.01]
            for i, a in enumerate(par):
                for b in par[i + 1:]:
                    sa = 1 if a["n"][0] * b["n"][0] + a["n"][1] * b["n"][1] > 0 else -1
                    w = abs(a["offset"] - sa * b["offset"])
                    if abs(w - B) > 15:
                        continue
                    ta = sorted((a["t0"], a["t1"]))
                    tb_ = sorted((b["t0"], b["t1"]) if a["u"][0] * b["u"][0] + a["u"][1] * b["u"][1] > 0 else
                                 (-b["t1"], -b["t0"]))
                    ov = (max(ta[0], tb_[0]), min(ta[1], tb_[1]))
                    if ov[1] - ov[0] < 300:
                        continue
                    mid_off = (a["offset"] + sa * b["offset"]) / 2.0
                    d_perp = abs((-a["n"][0] * 0 + 0) + (x * a["n"][0] + y * a["n"][1]) - mid_off)
                    t_tag = x * a["u"][0] + y * a["u"][1]
                    inside = ov[0] - 300 <= t_tag <= ov[1] + 300
                    Lb = (ov[1] - ov[0]) / 1000.0
                    cands.append({"edges": [a["keys"], b["keys"]], "breadth_mm": round(w, 1),
                                  "length_m": round(Lb, 3), "tag_offset_mm": round(d_perp, 1), "tag_within_span": inside,
                                  "length_vs_schedule": round(Lb / sched, 3) if sched else None})
            cands.sort(key=lambda c: (not c["tag_within_span"], c["tag_offset_mm"]))
            best = cands[0] if cands else None
            ok = bool(best and best["tag_within_span"] and best["tag_offset_mm"] <= 2 * (r.get("text_height") or 300)
                      and sched and abs(best["length_m"] - sched) / sched <= 0.05)
            contra = []
            if not cands:
                contra.append(f"no {B:.0f} mm band parallel to the tag on the sheet")
            elif not ok:
                contra.append(f"nearest band {best['tag_offset_mm']} mm from the tag, length {best['length_m']} m vs "
                              f"schedule {sched} m")
            near = bool(best and best["tag_offset_mm"] <= 5 * (r.get("text_height") or 300))
            ev = []
            if best and sched and abs(best["length_m"] - sched) / sched <= 0.05:
                ev.append(f"a {best['breadth_mm']:.0f} mm band of length {best['length_m']} m (schedule {sched} m) lies "
                          f"{best['tag_offset_mm']} mm from the tag")
            out.append({"occurrence": f"TAG:{fl}:{r['type']}:{r['mark_key'].split('|')[1]}", "type": r["type"],
                        "floor": fl, "r3_state": r["state"], "candidate": best, "candidates_considered": len(cands),
                        "evidence": ev if not ok else ["band at scheduled breadth under the tag, length within 5 %"],
                        "contradictions": contra, "score_factors": {"top_candidates": cands[:3]},
                        "decision": "ACCEPTED_STRONG" if ok else ("NOT_ACCEPTED" if near else "UNRESOLVED"),
                        "why": "; ".join(contra) or "strong match"})
    return out


# ===================================================================================================== ground slab
def ground_slab_scope_v2(ctx, r3_scope) -> dict:
    """Q-S4 second pass: the closed cells of the ground-beam network (layers 1 + 2, single lines as barriers) inside
    each footprint, the slab notes they hold and the other evidence on the sheet. Candidate regions are listed with
    their contradictions; the minimum (note cell) and the maximum (whole footprint) are never chosen by rule."""
    import alsenan_phase_a as AP
    import alsenan_phase_a3 as A3
    import alsenan_phase_b2a as B2A
    import alsenan_v3_structure as V3S
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import unary_union
    from engine.source import canonical_input as CI
    Sb = A3._blob(ctx, Path(ctx["_work"]), "ST7757.dxf")
    sb = ctx["structural_sheets"]["GROUND_BEAMS"]["bounds"]
    lay = lambda p: CI.effective_layer(p)[0]
    segs = [p for p in Sb["parts"] if p.kind == "SEGMENT" and lay(p) in ("1", "2") and
            AP.in_box(p.geometry[0], p.geometry[1], sb)]
    arcs = [p for p in Sb["parts"] if p.kind == "ARC" and lay(p) in ("1", "2") and AP.in_box(p.geometry[0], p.geometry[1], sb)]
    cols = [Polygon(B2A._rect_poly(r)) for r in B2A._col_rects(Sb, sb)]
    bands = V3S._pair_bands(segs, width=300.0, tol=12.0) + V3S._arc_bands(arcs, width=300.0, tol=12.0)
    thin = [LineString([(p.geometry[0], p.geometry[1]), (p.geometry[2], p.geometry[3])]).buffer(1.0) for p in segs]
    union = unary_union([b["poly"] for b in bands] + cols + thin)
    comps = sorted(getattr(union, "geoms", [union]), key=lambda g: -Polygon(g.exterior).area)
    texts = [t for t in Sb["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, sb)]
    notes = [t for t in texts if "T=" in t.value]
    kgm2 = 2 * 5 * RM.kgm(10)                                             # 5Ø10/m each way, audit only
    fps = []
    for i, g in enumerate([g for g in comps if Polygon(g.exterior).area >= 20e6]):
        cells = []
        for h in g.interiors:
            cp = Polygon(h)
            inside = [t.value.strip() for t in texts if cp.contains(Point(t.x, t.y))]
            cells.append({"area_m2": round(cp.area / 1e6, 3), "texts": inside,
                          "holds_slab_note": any("T=" in v for v in inside)})
        cells.sort(key=lambda c: -c["area_m2"])
        note_cells = [c for c in cells if c["holds_slab_note"]]
        tot = sum(c["area_m2"] for c in cells)
        other = [c for c in cells if not c["holds_slab_note"]]
        fps.append({"footprint": f"FP-{i + 1}", "outer_m2": round(Polygon(g.exterior).area / 1e6, 3),
                    "cells": cells, "cells_total_m2": round(tot, 3),
                    "note_cells_m2": round(sum(c["area_m2"] for c in note_cells), 3),
                    "candidates": [
                        {"id": "A_NOTE_CELL_ONLY", "area_m2": round(sum(c["area_m2"] for c in note_cells), 3),
                         "audit_kg": round(sum(c["area_m2"] for c in note_cells) * kgm2, 1),
                         "contradiction": f"{len(other)} other closed cells ({round(sum(c['area_m2'] for c in other), 2)} "
                                          "m2) have no slab note and no alternative floor construction printed"},
                        {"id": "B_ALL_CELLS", "area_m2": round(tot, 3), "audit_kg": round(tot * kgm2, 1),
                         "contradiction": "one note per footprint does not state 'typical'; cells may be voids / "
                                          "courtyards / pits"},
                        {"id": "C_ALL_CELLS_ABOVE_0.5M2", "area_m2": round(sum(c["area_m2"] for c in cells
                                                                             if c["area_m2"] >= 0.5), 3),
                         "audit_kg": round(sum(c["area_m2"] for c in cells if c["area_m2"] >= 0.5) * kgm2, 1),
                         "contradiction": "slivers dropped as drawing gaps; the other cells hold only column / footing "
                                          "tags and level marks (+1.00, and +0.30 in one cell) - no floor designation"}],
                    "level_marks_in_cells": sorted({v for c in cells for v in c["texts"] if v.startswith("+")}),
                    "decision": "ESTABLISHED_SOLE_CANDIDATE" if len(cells) == len(note_cells) else
                    "UNRESOLVED (Q-S4 narrowed)"})
    return {"rule": "candidate regions with contradictions; min -> max never used", "notes": [n.value for n in notes],
            "footprints": fps, "round3_scope": r3_scope,
            "g15": "XFAIL" if any(f["decision"].startswith("UNRESOLVED") for f in fps) else "PASS_CANDIDATE"}


# ===================================================================================================== build
def check_claim_authority(b) -> list:
    """No VERIFIED kg may rest on a claim without VERIFIED quantity authority."""
    v = []
    for c in b.comps:
        cid = (c["source"] or {}).get("claim_id")
        if cid and c["verified_kg"] > 0 and VS.quantity_authority(b.claims[cid]) != VS.VERIFIED_AUTHORITY:
            v.append(("VERIFIED_KG_ON_UNVERIFIED_CLAIM", c["comp_id"], cid))
    for cl in b.claims.values():
        v += [("CLAIM_INVALID",) + x for x in VS.validate(cl)]
    return v


def check_d5_no_candidate_restore(b) -> list:
    v = []
    for row in getattr(b, "d5", []):
        p = next((p for p in b.pops if p["occurrence_id"] == row["occurrence"]), None)
        if p is None:
            continue
        if row["classification"] in ("UNRESOLVED", "OFF_STOREY_COLUMN") and \
                p["lower_bound_kg"] + p["verified_complete_kg"] + p["provisional_kg"] > 0:
            v.append(("D5_KG_WITHOUT_ESTABLISHED_OCCURRENCE", row["occurrence"]))
    return v


def check_no_carried(b) -> list:
    return [("CARRIED_POPULATION_REMAINS", p["pop_id"]) for p in b.pops if p["occurrence_id"].startswith("CARRIED:")]


def project_invariants(b) -> dict:
    inv = R3.project_invariants(b)
    real = {f"POP:{r['occurrence']}" for r in getattr(b, "d5", []) if r["kg_restored"]}
    inv["column_d5"] = [v for v in inv["column_d5"] if v[1] not in real]   # physical occurrence established in R4
    inv["claim_authority"] = check_claim_authority(b)
    inv["d5_no_candidate_restore"] = check_d5_no_candidate_restore(b)
    inv["no_carried_population"] = check_no_carried(b)
    return inv


def build(ctx, r1_gzb, capture=None, **kw) -> Build4:
    return Build4(ctx, capture=capture, **kw).run(r1_gzb)
