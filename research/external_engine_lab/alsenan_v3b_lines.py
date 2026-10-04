"""ALSENAN V3b - BOQ lines with two release views (TECHNICAL_QTO / COMMERCIAL_BOQ), waste / procurement, concrete
attributes and V3a supersession.

Every line keeps the V3a contract read by the workbooks (trade, level, group, code, desc, unit, qty = technical qty,
status = technical status, formula, authority, sumrow) and adds:
    release   {"technical": {class, qty, in_total}, "commercial": {class, qty, method, assumption, confidence, low,
               high, procurement_eligible, ...}}           engine.source.release_model
    waste     {NET, WASTE_METHOD, WASTE_PCT, WASTE_QTY, PROCUREMENT, STATE}   engine.source.waste_procurement
    concrete  {CONCRETE_STRENGTH, CEMENT_TYPE, SOIL_CONTACT, SULFATE_REQUIREMENT, SOURCE}   (concrete lines)
    supersedes [V3a codes]
"""

from __future__ import annotations

from collections import defaultdict

import alsenan_v3_registers as REGS
from engine.source import release_model as RM
from engine.source import waste_procurement as WP

TECH_STATUS = {"MEASURED": "COMPUTED", "DERIVED": "COMPUTED", "RASTER_DERIVED": "COMPUTED", "SOURCE_RULE": "COMPUTED",
               "CODE_METHOD": "COMPUTED", "OWNER_PROJECT_FACT": "COMPUTED", "URBAN_STANDARD": "COMPUTED",
               "PARTIAL": "PARTIAL", "REVIEW": "REVIEW", "BLOCKED": "BLOCKED", "BLOCKED_SOURCE_CONFLICT": "BLOCKED",
               "NOT_IN_SOURCE": "NOT_IN_SOURCE", "PENDING": "REVIEW"}
FL2LV = {"GF": "GF", "1F": "1F", "2F": "2F_ROOF", "FOUNDATION": "GF"}
WASTE_RULES = []                     # no approved waste rule (OD-V3B-12): every non-rebar line is PENDING


def _r(v, n=6):
    return None if v is None else round(float(v), n)


def tech_of(ln):
    st, au = ln["status"], ln.get("authority") or ""
    if st == "COMPUTED":
        if "URBAN_FALLBACK" in au or "URBAN-" in au:
            return "URBAN_STANDARD"
        if "OWNER" in au:
            return "OWNER_PROJECT_FACT"
        return "DERIVED"
    return {"PARTIAL": "PARTIAL", "REVIEW": "REVIEW", "BLOCKED": "BLOCKED", "NOT_IN_SOURCE": "NOT_IN_SOURCE"}[st]


def prov(cls, qty, lo, hi, conf, method, assumption, source=None):
    return {"class": cls, "qty": _r(qty), "low": _r(lo), "high": _r(hi), "confidence": conf, "method": method,
            "assumption": assumption, "source": source}


def conf_by_range(q, lo, hi):
    """Confidence of a measured quantity whose only uncertainty is a bounded deduction: range width / quantity
    <= 5 % = H, <= 15 % = M, else L."""
    if not q:
        return "L"
    w = (hi - lo) / abs(q)
    return "H" if w <= 0.05 else "M" if w <= 0.15 else "L"


def mk(trade, level, group, code, en, ar, unit, tclass, tqty, formula, authority, commercial=None, trace="",
       details=None, supersedes=(), sumrow=None, concrete=None, no_total=False):
    st = TECH_STATUS[tclass]
    rel = RM.release(tclass, _r(tqty) if tclass in RM.TECH_IN_TOTAL else None, commercial)
    ln = REGS.line(trade, level, group, code, en, ar, unit, tqty if tclass in RM.TECH_IN_TOTAL else None, st,
                   formula, authority, trace, details)
    ln["release"] = rel
    ln["supersedes"] = list(supersedes)
    ln["sumrow"], ln["sumrow_ar"] = sumrow if sumrow else (None, None)
    if concrete:
        ln["concrete"] = concrete
    if no_total:
        ln["no_total"] = no_total
    return ln


def from_v3a(ln, commercial=None, **over):
    t = over.pop("tclass", tech_of(ln))
    out = mk(ln["trade"], ln["level"], ln["group"], ln["code"], ln["desc_en"], ln["desc_ar"], ln["unit"], t,
             over.pop("tqty", ln["qty"]), over.pop("formula", ln["formula"]), over.pop("authority", ln["authority"]),
             commercial, ln.get("trace", ""), ln.get("details"), over.pop("supersedes", ()),
             concrete=over.pop("concrete", None))
    out["v3a_line"] = ln["line_id"]
    out["sumrow"], out["sumrow_ar"] = ln.get("sumrow"), ln.get("sumrow_ar")
    out.update(over)
    return out


# ------------------------------------------------------------------ concrete attributes (OD-V3B-2)
def conc_attr(code):
    plain = code.startswith("C-BLD") or code.startswith("C-POOL-BLD")
    soil = any(code.startswith(p) for p in ("C-FTG", "C-BLD", "C-NECK", "C-GB", "C-GSLAB", "C-STR", "C-POOL", "C-BWALL"))
    return {"CONCRETE_STRENGTH": "f'c >= 150 kg/cm2 (plain)" if plain else "f'c >= 300 kg/cm2 (reinforced)",
            "CEMENT_TYPE": "SULFATE- AND SALT-RESISTING" if soil else "BY_SPEC (not soil-contact; note 13 silent)",
            "SOIL_CONTACT": soil, "SULFATE_REQUIREMENT": "YES (note 13)" if soil else "NOT STATED",
            "SOURCE": "ST7757.pdf p.8 notes 6 and 13"}


# ================================================================== builder
def build(ctx, v3a_lines, V) -> list:
    by = {x["code"]: x for x in v3a_lines}
    out = []
    used = set()

    def take(code):
        used.add(code)
        return by[code]
    S, F, RB = V["struct"], V["finish"], V["rebar"]
    # ---------------------------------------------------------------- CONCRETE
    T = "CONCRETE"
    RC = ("Reinforced concrete", "خرسانة مسلحة")
    PC = ("Plain concrete (blinding)", "خرسانة عادية")
    for ln in v3a_lines:
        if ln["trade"] != T:
            continue
        c = ln["code"]
        if c in ("C-BLD-F", "C-BLD-GB"):
            used.add(c)
            out.append(from_v3a(ln, tclass="REVIEW", concrete=conc_attr(c), no_total="ALTERNATIVE",
                                desc_en=ln["desc_en"] + " - SOURCE_DETAIL_LOCAL_BLINDING (alternative, same layer)",
                                authority="SOURCE (p.13) - double-count guard: superseded by the owner full-footprint method"))
            continue
        if c == "C-NECK":
            used.add(c)
            k = S["necks"]["concrete"]
            out.append(from_v3a(ln, prov(k["class"], k["qty"], k["low"], k["high"], k["confidence"], k["method"],
                                         k["assumption"]), concrete=conc_attr(c)))
            continue
        if c == "C-GB-EXT":
            used.add(c)
            k = S["ext_gb"]["concrete"]
            out.append(from_v3a(ln, prov(k["class"], k["qty"], k["low"], k["high"], k["confidence"], k["method"],
                                         k["assumption"]), concrete=conc_attr(c)))
            continue
        if c == "C-GSLAB-ZONE-2":
            used.add(c)
            z = next(z for z in S["ground_zones"]["zones"] if z["id"] == "ZONE-2")
            if z["state"] == "CLOSED_CROSS_LAYER":
                out.append(from_v3a(ln, tclass="DERIVED", tqty=z["volume_m3"], concrete=conc_attr(c),
                                    formula=f"{z['slab_m2']:.3f} m2 (zone outer {z['outer_m2']:.3f} closed across layers) "
                                            f"x 0.10", authority="SOURCE (p.3 'T=10cm') - zone closed across layers (B10)"))
            else:
                out.append(from_v3a(ln, concrete=conc_attr(c)))
            continue
        if c == "C-STAIR":
            used.add(c)
            fl = S["stairs"]["flights"]
            q = sum(x["concrete_m3"] for x in fl)
            hi = sum(x["concrete_hi_m3"] for x in fl)
            out.append(from_v3a(ln, prov("PROVISIONAL_CODE_METHOD", q, q * 0.9, hi * 1.1, "M",
                                         "risers ceil(H / 0.175) (2R + G, G = 0.30 printed); waist 16 cm; W 1.15 m; "
                                         "landings W x W per turn",
                                         "waist 0.16 = note 18 slab default (not a waist proof); landings labelled"),
                                concrete=conc_attr(c)))
            continue
        if c == "C-DOME":
            used.add(c)
            for d in S["domes"]["rows"]:
                lv = "2F_ROOF" if "TOWER" in d["id"] else "1F"
                out.append(mk(T, lv, "OTHER", f"C-DOME-SHELL-{d['plan_circle']}", f"Dome shell 10 cm - {d['location']}",
                              "قشرة القبة", "m3", "DERIVED", d["shell_m3"],
                              f"2 pi Rm hm x t; span {d['span_m']} (plan circle) / {d['span_route_c_m']} (route C), "
                              f"rise {d['rise_m']} ({d['rise_source']}), t {d['shell_t_m']}",
                              "SOURCE (P7757 plan circle + elevation rise + DETAIL OF DOME, factor proved)",
                              supersedes=["C-DOME"], sumrow=RC, concrete=conc_attr("C-DOME")))
                rb = d["ring_beam"]
                out.append(mk(T, lv, "OTHER", f"C-DOME-RING-{d['plan_circle']}", f"Dome ring beam - {d['location']}",
                              "حزام القبة", "m3", "BLOCKED", None,
                              f"pi x {rb['centreline_diameter_m']} x {rb['B_m']} x D; D 'AS PER ARCH' (drawn {rb['D_drawn_m']})",
                              "DETAIL OF DOME (N.I.S.)",
                              prov("PROVISIONAL_SOURCE_DERIVED", rb["volume_m3"], rb["volume_m3"] * 0.6,
                                   rb["volume_m3"] * 1.2, "M", "ring beam B x drawn depth at the proved detail factor",
                                   "depth 'AS PER ARCH' not printed: drawn 0.75 m (range 0.45 .. 0.90)"),
                              supersedes=["C-DOME"], sumrow=RC, concrete=conc_attr("C-DOME")))
            continue
        if c == "C-POOL":
            used.add(c)
            p = S["pool"]
            if p.get("concrete_m3"):
                out.append(from_v3a(ln, tclass="DERIVED", tqty=p["concrete_m3"], formula=p["formula"],
                                    authority=f"SOURCE (S-BW outline + SWIM block, depth {p['depth_m']} printed "
                                              f"{p['depth_source']}, DETAIL OF SWIMMING POOL)", concrete=conc_attr(c)))
                out.append(mk(T, "OTHER_EXTERNAL", "OTHER", "C-POOL-BLD", "Pool blinding 10 cm plain concrete",
                              "خرسانة عادية تحت المسبح", "m3", "DERIVED", p["blinding_m3"], "(outer + 0.20)^2 x 0.10",
                              "SOURCE (detail: 10cm PLAIN CONCRETE)", sumrow=PC, concrete=conc_attr("C-POOL-BLD")))
            else:
                out.append(from_v3a(ln, concrete=conc_attr(c)))
            continue
        if c == "C-BWALL":
            used.add(c)
            bw = S["boundary_wall"]
            out.append(from_v3a(ln, prov("PROVISIONAL_SOURCE_DERIVED", bw["beam_m3"], bw["beam_m3"] * 0.9,
                                         bw["beam_m3"] * 1.35, "M", "B.W 20 x 60 x S-BOUN run (ground-beam sheet)",
                                         "footings of the p.14 typical detail not spaced on a plan (PENDING); the front "
                                         "fence run is drawn on the fence sheet only (high +35 %)"), concrete=conc_attr(c)))
            continue
        if c == "C-FTG":
            used.add(c)
            out.append(from_v3a(ln, concrete=conc_attr(c)))
            ff = S["f_f10"]
            k = ff["commercial"]
            out.append(mk(T, "GF", "SUBSTRUCTURE", "C-FTG-FF10", "Footing F / F10 (one drawn outline, two definitions)",
                          "قاعدة F / F10", "m3", "BLOCKED_SOURCE_CONFLICT", None,
                          f"F_SCENARIO 2 x F = {ff['F_SCENARIO']['concrete_m3']:.3f}; F10_SCENARIO 1 x F10 = "
                          f"{ff['F10_SCENARIO']['concrete_m3']:.3f}; DIFFERENCE {ff['DIFFERENCE']:.3f}",
                          "SOURCE CONFLICT (OQ3-S1)", prov(k["class"], k["qty"], k["low"], k["high"], k["confidence"],
                                                         k["method"], k["assumption"]),
                          sumrow=RC, concrete=conc_attr("C-FTG")))
            continue
        if c.startswith("C-COL-") or c.startswith("C-BEAM-"):
            used.add(c)
            out.append(from_v3a(ln, concrete=conc_attr(c)))
            fl = c.rsplit("-", 1)[1]
            res = S["residue"]["columns" if c.startswith("C-COL") else "beams"]
            xs = [x for x in res if x["floor"] == fl and x.get("commercial")]
            if xs:
                q = sum(x["commercial"]["qty"] for x in xs)
                lo = sum(x["commercial"]["low"] for x in xs)
                hi = sum(x["commercial"]["high"] for x in xs)
                worst = "BUDGET_ESTIMATE" if any(x["commercial"]["class"] == "BUDGET_ESTIMATE" for x in xs) else \
                    "PROVISIONAL_GEOMETRIC_INFERENCE"
                conf = "L" if worst == "BUDGET_ESTIMATE" else "M"
                out.append(mk(T, ln["level"], "SUPERSTRUCTURE", c + "-RES", ln["desc_en"] + " - residue (not bound)",
                              ln["desc_ar"] + " (متبقي)", "m3", "BLOCKED", None,
                              f"{len(xs)} occurrence(s) / tag(s) V3a could not measure",
                              "B07 residue", prov(worst, q, lo, hi, conf,
                                                  "drawn band or same-type median length x scheduled section",
                                                  "see SUBSTRUCTURE / residue records; unbound tags may repeat a "
                                                  "measured beam (low 0)"),
                              details=[{"ref": x["id"], "formula": x.get("length_basis") or x.get("why_v3a"),
                                        "qty": x["commercial"]["qty"], "status": x["commercial"]["class"]} for x in xs],
                              sumrow=RC, concrete=conc_attr(c)))
            continue
        used.add(c)
        out.append(from_v3a(ln, concrete=conc_attr(c)))
    bl = S["blinding"]["OWNER_FULL_FOOTPRINT_BLINDING"]
    out.append(mk(T, "GF", "SUBSTRUCTURE", "C-BLD-FULL", "Plain concrete blinding - full founded footprint (owner method)",
                  "صبة نظافة كامل المسقط", "m3", "OWNER_PROJECT_FACT", bl["volume_m3"],
                  f"{bl['area_m2']:.3f} m2 ({' + '.join(str(f['area_m2']) for f in bl['footprints'])}) x {bl['thickness_m']}",
                  "OD-V3B-1 FULL_FOOTPRINT_BLINDING_METHOD; t SOURCE p.13; footprint = ground-beam system outline",
                  supersedes=["C-BLD-F", "C-BLD-GB"], sumrow=PC, concrete=conc_attr("C-BLD-FULL")))
    # ---------------------------------------------------------------- REBAR (population x level; bases never summed)
    out += rebar_lines(RB)
    # ---------------------------------------------------------------- BLOCKWORK
    out += blockwork_lines(ctx, v3a_lines, V, used)
    # ---------------------------------------------------------------- PLASTER / PAINT (net, sequences, beads, facades)
    out += plaster_lines(ctx, v3a_lines, V, used)
    # ---------------------------------------------------------------- FLOORING, CEILINGS, TILE / WP, OPENINGS, STAIRS
    out += flooring_lines(ctx, v3a_lines, V, used)
    out += ceiling_lines(v3a_lines, used)
    out += tile_wp_lines(ctx, v3a_lines, V, used)
    out += opening_lines(ctx, v3a_lines, V, used)
    out += stair_lines(v3a_lines, V, used)
    out += external_lines(V)
    for i, ln in enumerate(out):
        ln["line_id"] = f"B{i + 1:04d}"
        if "sumrow" not in ln or ln.get("sumrow") is None and "v3a_line" in ln:
            pass
        ln["waste"] = waste_of(ln, RB)
    return out


# ================================================================== rebar
REB = "REBAR"
SUM_NET = ("Rebar - net design weight (straight + hooks)", "التسليح - الوزن الصافي")


def rebar_lines(RB) -> list:
    out = []
    agg = defaultdict(lambda: {"tech": 0.0, "net": 0.0, "lo": 0.0, "hi": 0.0, "hook": 0.0, "lap": 0.0, "sets": 0,
                               "blocked": 0, "classes": set(), "conf": set()})
    for s in RB["weighed"]:
        k = (s["population"], s["level"])
        a = agg[k]
        a["sets"] += 1
        if s.get("net_kg") is None:
            a["blocked"] += 1
            a["why"] = s.get("why")
            continue
        a["net"] += s["net_kg"]
        a["tech"] += s.get("tech_kg") or 0.0
        a["lo"] += s.get("low_kg") if s.get("low_kg") is not None else s["net_kg"]
        a["hi"] += s.get("high_kg") if s.get("high_kg") is not None else s["net_kg"]
        a["hook"] += s.get("hook_kg") or 0.0
        a["lap"] += s.get("lap_kg") or 0.0
        a["classes"].add(s.get("commercial") or s.get("technical"))
        a["conf"].add(s.get("confidence") or "H")
    for (pop, lv), a in sorted(agg.items()):
        code = f"R-{pop}-{lv}"
        if a["net"] == 0 and a["blocked"]:
            out.append(mk(REB, lv, pop, code, f"Rebar {pop.lower().replace('_', ' ')} - not computable",
                          "تسليح غير قابل للحساب", "kg", "BLOCKED", None, a.get("why") or "", "BLOCKED",
                          sumrow=("Bar sets / members not computable", "تسليح غير قابل للحساب"), supersedes=["R-"]))
            continue
        prov_cls = sorted(c for c in a["classes"] if c and c.startswith(("PROVISIONAL", "BUDGET")))
        tcls = "DERIVED" if not prov_cls and a["tech"] >= a["net"] - 1e-6 else ("PARTIAL" if a["tech"] > 0 else "BLOCKED")
        conf = "L" if "L" in a["conf"] else "M" if "M" in a["conf"] else "H"
        com = None
        if tcls != "DERIVED":
            cls = "BUDGET_ESTIMATE" if "BUDGET_ESTIMATE" in prov_cls else (prov_cls[0] if prov_cls else "PROVISIONAL_CODE_METHOD")
            if "PROVISIONAL_URBAN_FALLBACK" in prov_cls:
                cls = "PROVISIONAL_URBAN_FALLBACK"
            com = prov(cls, a["net"], min(a["lo"], a["net"]), max(a["hi"], a["net"]), conf,
                       "bar sets: straight + hooks (" + ("code method" if a["hook"] else "none") + ")",
                       f"{len(prov_cls)} provisional class(es): {', '.join(prov_cls)}")
        out.append(mk(REB, lv, pop, code, f"Rebar {pop.lower().replace('_', ' ')} - net design weight",
                      "تسليح - الوزن الصافي", "kg", tcls, a["tech"] if tcls != "BLOCKED" else None,
                      f"{a['sets']} bar sets ({a['blocked']} blocked); hooks {a['hook']:.1f} kg; laps {a['lap']:.1f} kg "
                      f"(procurement, not in net)", "SOURCE schedules / plans + ACI 318-19 hook tables (unverified)",
                      com, sumrow=SUM_NET, supersedes=["R-"]))
        out[-1]["rebar"] = {"net_kg": a["net"], "technical_kg": a["tech"], "hook_kg": a["hook"], "lap_kg": a["lap"]}
    cut = RB["cutting"]
    for view, key in (("technical", "TECH"), ("commercial", "COMM")):
        t = cut[view]["total"]
        out.append(mk(REB, "GF", "PROCUREMENT", f"R-BBS-PURCHASED-{key}",
                      f"Rebar purchased from 12 m stock (BBS cut, {view} population)", "وزن التوريد (قص)", "kg",
                      "CODE_METHOD" if view == "technical" else "BLOCKED", t["purchased_kg"] if view == "technical" else None,
                      f"used {t['used_kg']:.1f} kg (incl. laps) + unused offcut {t['unused_kg']:.1f} kg; reused offcut "
                      f"{t['reused_kg']:.1f} kg; effective waste {t['effective_waste_pct']:.2f} %",
                      "BBS_OPTIMISER_V1 first-fit decreasing, 12.00 m stock (OD-V3B-12)",
                      None if view == "technical" else prov("PROVISIONAL_CODE_METHOD", t["purchased_kg"],
                                                            t["purchased_kg"] * 0.97, t["purchased_kg"] * 1.05, "M",
                                                            "BBS cut of the commercial population",
                                                            "weight-only sets (starters, residue beams) not cut"),
                      sumrow=(f"Rebar - purchased from 12 m stock ({view} population)", "حديد التوريد"),
                      no_total="ALTERNATIVE_BASIS"))
    return out


def waste_of(ln, RB):
    if ln["trade"] == REB and ln["code"].startswith("R-BBS"):
        view = "technical" if ln["code"].endswith("TECH") else "commercial"
        t = RB["cutting"][view]["total"]
        return WP.apply(t["used_kg"], "kg", {"method": "CUTTING_OPTIMISATION", "waste_qty": t["unused_kg"],
                                              "procurement": t["purchased_kg"], "scope": "ITEM",
                                              "source": "BBS_OPTIMISER_V1"})
    q = ln["release"]["commercial"]["qty"]
    if ln["trade"] == "CONCRETE":
        w = WP.apply(q, ln["unit"], None)
        w["WASTE_METHOD"] = "POUR / ORDER ALLOWANCE - PENDING (net volume is the BOQ)"
        return w
    if ln["trade"] == REB:
        w = WP.apply(q, ln["unit"], None)
        w["WASTE_METHOD"] = "see R-BBS-PURCHASED (cutting optimisation on the whole population)"
        return w
    return WP.apply(q, ln["unit"], WP.resolve(ln["code"], ln["trade"], None, WASTE_RULES))


# ================================================================== blockwork
def blockwork_lines(ctx, v3a, V, used) -> list:
    out = []
    F, S = V["finish"], V["struct"]
    for ln in v3a:
        if ln["trade"] != "BLOCKWORK":
            continue
        c = ln["code"]
        used.add(c)
        if c == "B-OVER-OPEN":
            ov = F["over_openings"]
            out.append(from_v3a(ln, prov(ov["class"], ov["qty"], ov["low"], ov["high"], ov["confidence"], ov["method"],
                                         ov["assumption"]), tclass="PARTIAL" if ov["technical"] else "BLOCKED",
                                tqty=ov["technical"] or None,
                                formula=ov["formula"]))
        elif c == "B-BWALL":
            bw = S["boundary_wall"]
            q = bw["blockwork_m2"]
            fr = (bw["front_run_printed_m"] or 0) * bw["height_m"]
            out.append(from_v3a(ln, prov("PROVISIONAL_SOURCE_DERIVED", q + fr, q, q + fr, "M",
                                         "S-BOUN run (ground-beam sheet) + printed front fence run, x 2.65 printed",
                                         f"run {bw['length_m']} m + front {bw['front_run_printed_m']} m (gates not "
                                         f"deducted); the two runs are assumed distinct"),
                                formula=f"({bw['length_m']} + {bw['front_run_printed_m']}) x {bw['height_m']}"))
        else:
            out.append(from_v3a(ln))
    return out


# ================================================================== plaster / paint
PP = "PLASTER_PAINT"


def plaster_lines(ctx, v3a, V, used) -> list:
    out = []
    F = V["finish"]
    for ln in v3a:
        if ln["trade"] == PP:
            used.add(ln["code"])
    rooms = F["net"]["rooms"]
    for r in rooms:
        lv = FL2LV[r["floor"]]
        nm = r["name"] or r["room"]
        n = r["net"]
        sup = [f"P-PL-{r['room']}", f"P-PA-{r['room']}", f"P-SD-{r['room']}"]
        partial = r["faces_blocked_length_m"] and r["faces_blocked_length_m"] > 0
        if r["wet"]:
            continue                                         # tiled faces: 07 (spatter + tile prep + tile)
        p = n.get("PLASTER")
        if p:
            tcls = "DERIVED" if not r["provisional"] and not partial else "BLOCKED"
            com = None if tcls == "DERIVED" else prov(
                "PROVISIONAL_SOURCE_DERIVED", p["net"], p["net_low"], p["net_high"],
                conf_by_range(p["net"], p["net_low"], p["net_high"]) if not partial else "M",
                "NET = gross - openings (raster heights) + reveals; confidence from the deduction range",
                f"{len(r['openings'])} opening(s) on the faces; reveal depth URBAN_FALLBACK"
                + ("; part of the faces blocked (V3a)" if partial else ""))
            for code, en, ar in (("SD", "Spatter dash (internal)", "طرطشة داخلية"),
                                 ("RP", "Rough plaster (internal)", "مساح خشن"),
                                 ("SP", "Smooth plaster (internal)", "مساح ناعم")):
                out.append(mk(PP, lv, "INTERNAL PLASTER" if code != "SD" else "SPATTER DASH", f"P-{code}-{r['room']}",
                              f"{en} - {nm}", f"{ar} - {nm}", "m2", tcls, p["net"] if tcls == "DERIVED" else None,
                              f"gross {p['gross']:.3f} - openings {p['openings']:.3f} + reveals {p['reveals']:.3f}",
                              "NET_COMMERCIAL_MEASUREMENT (OD-V3B-3) / DRY_INTERNAL_SPATTER_ROUGH_SMOOTH (OD-V3B-5)",
                              dict(com) if com else None, trace=r["room"], supersedes=sup,
                              sumrow={"SD": ("Spatter dash (internal)", "طرطشة"), "RP": ("Rough plaster", "مساح خشن"),
                                      "SP": ("Smooth plaster", "مساح ناعم")}[code]))
        a = n.get("PAINT")
        pb = F["paint_blocked"].get(r["room"])
        if a or pb:
            if a and not pb:
                tcls = "DERIVED" if not r["provisional"] and not partial else "BLOCKED"
                com = None if tcls == "DERIVED" else prov("PROVISIONAL_SOURCE_DERIVED", a["net"], a["net_low"],
                                                          a["net_high"], conf_by_range(a["net"], a["net_low"], a["net_high"])
                                                          if not partial else "M",
                                                          "NET paint = gross - openings + reveals",
                                                          "opening heights provisional (range from their height ranges)")
                q = a["net"]
                f_ = f"gross {a['gross']:.3f} - openings {a['openings']:.3f} + reveals {a['reveals']:.3f}"
            else:
                tcls = "BLOCKED"
                com = prov("PROVISIONAL_GEOMETRIC_INFERENCE", pb["net"], pb["low"], pb["high"], "M", pb["method"],
                           pb["assumption"])
                q = None
                f_ = pb["formula"]
            out.append(mk(PP, lv, "PAINT", f"P-PA-{r['room']}", f"Internal paint (net) - {nm}", f"دهان داخلي - {nm}", "m2",
                          tcls, q if tcls == "DERIVED" else None, f_,
                          "NET_COMMERCIAL_MEASUREMENT + URBAN_FALLBACK build-up (OD-V3-1)", com, trace=r["room"],
                          supersedes=sup, sumrow=("Internal paint (net)", "دهان داخلي")))
    # reveals (components, included in the net lines)
    rv = defaultdict(float)
    for r in rooms:
        for k, v in r["reveals"].items():
            rv[(FL2LV[r["floor"]], k)] += v or 0.0
    for (lv, k), v in sorted(rv.items()):
        if k == "WINDOW_SILL_LM":
            continue
        out.append(mk(PP, lv, "REVEALS", f"P-{k}-{lv}", f"{k.replace('_', ' ').title()} (component, inside the net)",
                      "شرشوب", "m2", "BLOCKED", None, "jambs + head x half the wall thickness per face",
                      "OD-V3B-9 REVEALS_MEASURED; depth URBAN_FALLBACK",
                      prov("PROVISIONAL_URBAN_FALLBACK", v, v * 0.6, v * 1.4, "M", "reveal = (2 h + w) x t / 2 per face",
                           "frame position unknown: depth half the wall (range 60 .. 140 %)"),
                      sumrow=None, no_total="COMPONENT_INSIDE_NET", supersedes=["P-REVEAL"]))
    # angle beads (OD-V3B-8): per floor, technical part = beads of raster-derived openings + corners
    bd = defaultdict(lambda: [0.0, 0.0])
    for s in F["net"]["beads"]:
        if s["status"] != "MEASURED":
            continue
        lv = FL2LV[s["floor"]]
        tech = s.get("source") in ("PRINTED", "RASTER_TYPE_MATCH") or s["edge_type"] == "EXTERNAL_CORNER"
        bd[lv][0] += s["length_m"] if tech else 0.0
        bd[lv][1] += s["length_m"]
    for lv, (t, c) in sorted(bd.items()):
        out.append(mk(PP, lv, "ANGLE BEADS", f"P-BEAD-{lv}", "Steel plaster angle beads (exposed plaster edges)",
                      "زوايا المساح", "lm", "PARTIAL" if t < c else "DERIVED", t,
                      "corner_bead segments: door / window jambs + heads + sills on plastered faces, projecting corners",
                      "STEEL_PLASTER_ANGLE_BEADS (OD-V3B-8); V3a 15.7 lm superseded",
                      None if t >= c else prov("PROVISIONAL_SOURCE_DERIVED", c, t + 0.8 * (c - t), t + 1.2 * (c - t), "M",
                                               "segments of openings with provisional heights", "heights +- 20 %"),
                      supersedes=["P-CB"], sumrow=("Angle beads", "زوايا")))
    # facades (B14) - Sigma sequence
    for f in F["facades"]["floors"]:
        lv = FL2LV[f["floor"]]
        q = f["net_m2"]
        for code, en, ar in (("EXT-SD", "External spatter dash", "طرطشة خارجية"),
                             ("EXT-RP", "External rough plaster", "مساح خشن خارجي"),
                             ("EXT-SP", "External smooth plaster", "مساح ناعم خارجي"),
                             ("EXT-SIGMA", "External Sigma finish (final)", "سيجما")):
            out.append(mk(PP, lv, "EXTERNAL", f"P-{code}-{f['floor']}", f"{en} - {f['floor']} facades", ar, "m2", "BLOCKED",
                          None, f"perimeter {f['outline_perimeter_m']} x band {f['band_m']:.2f} - openings "
                                f"{f['openings_m2']} + reveals {f['external_reveals_m2']}",
                          "SIGMA_EXTERNAL_SPATTER_ROUGH_SMOOTH_SIGMA (OD-V3B-7); elevations draw rendered plaster",
                          prov("PROVISIONAL_GEOMETRIC_INFERENCE", q, q * 0.9, q * 1.1, "M",
                               "floor outline (rooms closed across walls) x printed level band - openings + reveals",
                               "outline method; no Route C on the raster facade silhouettes this round (+-10 %)"),
                          supersedes=["P-EXT"], sumrow=(en, ar)))
    for p in F["facades"].get("parapets") or []:
        pass
    pr = F["parapet_faces"]
    for lv, q, frm in pr:
        out.append(mk(PP, lv, "EXTERNAL", f"P-EXT-PAR-{lv}", "Parapet plaster (both faces + coping)", "لياسة الدروة",
                      "m2", "DERIVED", q, frm, "V3a parapet lengths x 0.50 (sections) x 2 faces + 0.20 coping",
                      sumrow=("Parapet plaster", "لياسة الدروة")))
    return out


# ================================================================== flooring (room by room) and ceilings
def flooring_lines(ctx, v3a, V, used) -> list:
    out = []
    dual = {d["room"]: d for d in V["dual"]["rooms"]}
    for ln in v3a:
        if ln["trade"] != "FLOORING_PORCELAIN":
            continue
        used.add(ln["code"])
        if ln["code"] == "F-STAIR":
            out.append(from_v3a(ln, tclass="REVIEW", formula="superseded by S-TREAD / S-RISER (09) - never twice",
                                no_total="SUPERSEDED"))
            continue
        if ln["code"] == "F-COURT":
            c = V["external"]["courtyard"]
            out.append(from_v3a(ln, prov(c["class"], c["qty"], c["low"], c["high"], c["confidence"], c["method"],
                                         c["assumption"]) if c.get("qty") else None, formula=c["formula"]))
            continue
        x = from_v3a(ln)
        rid = ln.get("trace") or ln["code"].split("-", 2)[-1]
        d = dual.get(rid)
        if d:
            x["dual"] = d
        out.append(x)
    return out


def ceiling_lines(v3a, used) -> list:
    out = []
    for ln in v3a:
        if ln["trade"] != "CEILINGS":
            continue
        used.add(ln["code"])
        if ln["group"] == "CORNICE":
            out.append(from_v3a(ln, formula=ln["formula"] + " - CORNICE_ONLY_WHERE_ESTABLISHED (OD-V3B-10): PENDING",
                                no_total="PENDING_REVIEW"))
        else:
            out.append(from_v3a(ln))
    return out


# ================================================================== wall tile / waterproofing
def tile_wp_lines(ctx, v3a, V, used) -> list:
    from engine.source import waterproofing_policy as WPP
    out = []
    F = V["finish"]
    net = {r["room"]: r for r in F["net"]["rooms"]}
    fin = {r["room"]: r for r in ctx["v3"]["finishes"]["rows"]}
    rooms = {r["id"]: r for r in ctx["v3"]["rooms"]["rows"]}
    T = "WALL_TILE_WATERPROOFING"
    for ln in v3a:
        if ln["trade"] != T:
            continue
        c = ln["code"]
        used.add(c)
        if c.startswith("T-WT-"):
            rid = c[len("T-WT-"):]
            r = net.get(rid)
            t = r and r["net"].get("TILE")
            if not t:
                out.append(from_v3a(ln))
                continue
            tcls = "DERIVED" if not r["provisional"] else "BLOCKED"
            com = None if tcls == "DERIVED" else prov("PROVISIONAL_SOURCE_DERIVED", t["net"], t["net_low"], t["net_high"],
                                                      conf_by_range(t["net"], t["net_low"], t["net_high"]),
                                                      "NET wall tile = gross - openings + tiled reveals",
                                                      "opening heights provisional (range from their height ranges)")
            for code, en, ar, g in (("T-SD-", "Spatter dash (wet / tiled faces)", "طرطشة", "WALL TILE PREP"),
                                    ("T-TP-", "Tile preparation (wet / tiled faces)", "تجهيز للسيراميك", "WALL TILE PREP"),
                                    ("T-WT-", "Wall tile (net)", "سيراميك جدران", "WALL TILE")):
                out.append(mk(T, ln["level"], g, code + rid, f"{en} - {ln['desc_en'].split(' - ')[-1]}", ar, "m2", tcls,
                              t["net"] if tcls == "DERIVED" else None,
                              f"gross {t['gross']:.3f} - openings {t['openings']:.3f} + reveals {t['reveals']:.3f}",
                              "WET_ROOM_SPATTER_ONLY_BEFORE_TILE (OD-V3B-4) + NET (OD-V3B-3)", dict(com) if com else None,
                              trace=rid, supersedes=[c, f"P-PL-{rid}", f"P-SD-{rid}", f"P-PA-{rid}"],
                              sumrow={"T-SD-": ("Spatter dash (tiled faces)", "طرطشة"),
                                                                 "T-TP-": ("Tile preparation", "تجهيز"),
                                                                 "T-WT-": ("Wall tile (net)", "سيراميك جدران")}[code]))
            continue
        if c.startswith("T-WP-"):
            rid = c[len("T-WP-"):]
            f = fin[rid]
            w = WPP.wet(floor_m2=f["floor_area_m2"], perimeter_m=rooms[rid]["perimeter_m"],
                        door_widths_m=[f["opening_widths_m"]] if f["opening_widths_m"] else None, room=rid)
            parts = (("FLOOR", "Wet-room floor waterproofing", "m2", w.get("floor_m2")),
                     ("UPTURN-LM", "Waterproofing upturn - length", "lm", w.get("upturn_length_m")),
                     ("UPTURN-H", "Waterproofing upturn - height", "m", w.get("upturn_m")),
                     ("UPTURN-M2", "Waterproofing upturn - area (length x height)", "m2",
                      (w.get("upturn_length_m") or 0) * (w.get("upturn_m") or 0)))
            for k, en, u, q in parts:
                out.append(mk(T, ln["level"], "WET ROOM WATERPROOFING", f"T-WP-{k}-{rid}", f"{en} - {rid}",
                              "عزل مائي", u, "URBAN_STANDARD" if q is not None else "BLOCKED", q,
                              ln["formula"], "URBAN-WET-ROOM-WP (waterproofing_policy) - component split (V3b)",
                              supersedes=[c],
                              sumrow={"FLOOR": ("WP floor", "عزل أرضية"), "UPTURN-LM": ("WP upturn length", "طول القلبة"),
                                      "UPTURN-H": None, "UPTURN-M2": ("WP upturn area", "مساحة القلبة")}[k],
                              no_total="DIMENSION" if k == "UPTURN-H" else False))
            continue
        out.append(from_v3a(ln))
    S = V["struct"]
    p = S["pool"]
    if p.get("external_wp_m2"):
        out.append(mk(T, "OTHER_EXTERNAL", "POOL", "T-POOL-WP-EXT", "Pool external insulation membrane (5 cm)",
                      "عزل خارجي للمسبح", "m2", "DERIVED", p["external_wp_m2"], "outer base + outer walls x (D + base)",
                      "DETAIL OF SWIMMING POOL", sumrow=("Pool waterproofing / finish", "المسبح")))
        out.append(mk(T, "OTHER_EXTERNAL", "POOL", "T-POOL-FIN", "Pool internal finish (tile / mosaic BY_SPEC)",
                      "تكسية المسبح", "m2", "DERIVED", p["internal_finish_m2"], "inner base + inner walls x D",
                      "S-BW outline + printed depth", sumrow=("Pool waterproofing / finish", "المسبح")))
    e = S["ext_gb"]
    L_ = e["length_m"]
    out.append(mk(T, "GF", "FOUNDATION WATERPROOFING", "T-FWP-GB-EXT", "Liquid waterproofing 2 layers - exterior ground beams",
                  "عزل الميد الخارجية", "m2", "BLOCKED", None, f"2 x D x {L_:.2f} m", "SOURCE (p.13 earth-contact rule)",
                  prov("PROVISIONAL_SOURCE_DERIVED", 2 * 1.00 * L_, 2 * 0.90 * L_, 2 * 1.30 * L_, "M",
                       "2 faces x D x length", "D provisional (B01)"),
                  sumrow=("Foundation waterproofing / membrane", "عزل الأساسات")))
    return out


# ================================================================== openings
def opening_lines(ctx, v3a, V, used) -> list:
    out = []
    F = V["finish"]
    areas = F["areas"]
    for ln in v3a:
        if ln["trade"] != "ALUMINIUM_OPENINGS":
            continue
        c = ln["code"]
        used.add(c)
        if c.endswith("-A") and c != "O-CURVED-A":
            fl = c.split("-")[2]
            kind = {"DOO": "DOOR", "DOU": "DOUBLE_LEAF_DOOR", "WIN": "WINDOW"}[c.split("-")[1]]
            xs = [a for a in areas if a["floor"] == fl and a["kind"] == kind]
            tech = sum(a["area_m2"] for a in xs if a.get("technical") == "RASTER_DERIVED")
            allq = sum(a["area_m2"] for a in xs if a.get("area_m2"))
            lo = sum(a["low_m2"] for a in xs if a.get("low_m2"))
            hi = sum(a["high_m2"] for a in xs if a.get("high_m2"))
            bud = any(a.get("commercial") == "BUDGET_ESTIMATE" for a in xs)
            n_t = sum(1 for a in xs if a.get("technical") == "RASTER_DERIVED")
            tcls = "RASTER_DERIVED" if n_t == len(xs) and xs else ("PARTIAL" if n_t else "BLOCKED")
            com = None if tcls == "RASTER_DERIVED" else prov(
                "BUDGET_ESTIMATE" if bud else "PROVISIONAL_SOURCE_DERIVED", allq, min(lo, allq), max(hi, allq),
                "L" if bud else "M", "width (DXF) x height (calibrated raster elevations / sections)",
                f"{n_t} of {len(xs)} heights raster-derived; the rest type-matched (range) or the floor population")
            out.append(from_v3a(ln, com, tclass=tcls, tqty=tech if tcls != "BLOCKED" else None,
                                formula=f"sum width x height; {n_t}/{len(xs)} raster-derived",
                                authority="RASTER_EVIDENCE_V1 (calibrated sheets) + DXF widths",
                                details=[{"ref": a["id"], "formula": f"{a.get('width_m')} x {a.get('height_m')}",
                                          "qty": a.get("area_m2"), "status": a.get("technical") or a.get("commercial")}
                                         for a in xs]))
            continue
        if c == "O-CURVED-A":
            L_ = by_code(v3a, "O-CURVED-L")["qty"]
            out.append(from_v3a(ln, tclass="RASTER_DERIVED", tqty=L_ * 4.30,
                                formula=f"{L_} lm x 4.30 (printed NW elevation, + 0.20 head)",
                                authority="RASTER PRINTED (H)"))
            continue
        out.append(from_v3a(ln))
    sills = defaultdict(float)
    for r in F["net"]["rooms"]:
        sills[FL2LV[r["floor"]]] += r["reveals"].get("WINDOW_SILL_LM") or 0.0
    for lv, v in sorted(sills.items()):
        out.append(mk("ALUMINIUM_OPENINGS", lv, "WINDOW", f"O-SILL-{lv}", "Window sills (internal face) - length",
                      "جلسات الشبابيك", "lm", "DERIVED", v, "sum of window widths on room faces", "DXF widths",
                      sumrow=("Window sill length", "جلسات")))
    return out


def by_code(lines, code):
    return next(x for x in lines if x["code"] == code)


# ================================================================== stairs
def stair_lines(v3a, V, used) -> list:
    out = []
    st = V["struct"]["stairs"]
    fl = st["flights"]
    for ln in v3a:
        if ln["trade"] != "STAIRS_RAILINGS":
            continue
        used.add(ln["code"])
        c = ln["code"]
        if c == "S-RAIL":
            q = sum(f["handrail_lm"] for f in fl)
            out.append(from_v3a(ln, prov("PROVISIONAL_CODE_METHOD", q, q * 0.95, q * 1.1, "M",
                                         "flight slope length + landing edge per flight",
                                         "risers by the 2R + G band (section A-A treads not machine-counted)")))
        elif c == "S-TREAD":
            q = sum(f["tread_m2"] for f in fl)
            out.append(from_v3a(ln, prov("PROVISIONAL_CODE_METHOD", q, q * 0.95, q * 1.1, "M",
                                         "treads (n - 1) x 0.30 x 1.15 + landings", "risers by the 2R + G band"),
                                desc_en="Stair treads + landings (marble)"))
            r = sum(f["riser_m2"] for f in fl)
            out.append(mk("STAIRS_RAILINGS", ln["level"], ln["group"], "S-RISER", "Stair risers (marble)", "قوائم الدرج", "m2",
                          "BLOCKED", None, "n x R x 1.15", "2R + G band",
                          prov("PROVISIONAL_CODE_METHOD", r, r * 0.97, r * 1.03, "M", "n x R x W = H x W per flight",
                               "riser area depends on H only (n R = H)"),
                          sumrow=("Stair risers", "قوائم")))
            no = sum(f["nosing_lm"] for f in fl)
            out.append(mk("STAIRS_RAILINGS", ln["level"], ln["group"], "S-NOSING", "Stair nosing", "حافة الدرج", "lm",
                          "BLOCKED", None, "(n - 1) x 1.15", "2R + G band",
                          prov("PROVISIONAL_CODE_METHOD", no, no * 0.95, no * 1.15, "M", "treads x width",
                               "risers by the 2R + G band"), sumrow=("Stair nosing", "حافة")))
        else:
            out.append(from_v3a(ln))
    return out


# ================================================================== external works
def external_lines(V) -> list:
    out = []
    S = V["struct"]
    bw = S["boundary_wall"]
    T = "BLOCKWORK"
    q = bw["plaster_both_faces_m2"] + 2 * (bw["front_run_printed_m"] or 0) * bw["height_m"]
    out.append(mk(PP, "OTHER_EXTERNAL", "EXTERNAL", "P-BWALL", "Boundary wall plaster both faces", "لياسة السور", "m2",
                  "BLOCKED", None, f"2 x ({bw['length_m']} + {bw['front_run_printed_m']}) x {bw['height_m']}",
                  "fence sheet height + S-BOUN run",
                  prov("PROVISIONAL_SOURCE_DERIVED", q, q * 0.75, q, "M", "both faces x printed height",
                       "front fence run assumed distinct from the S-BOUN run"),
                  sumrow=("Boundary wall plaster", "لياسة السور")))
    return out
