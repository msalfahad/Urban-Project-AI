"""ALSENAN V3b - rebar completion: population inventory, hooks / bends by a recorded code method, BBS cutting on 12 m
stock with offcut reuse, net / lap / hook / purchased / offcut / waste, technical vs commercial.

Every bar set is one record:
    population, element, ref, level, dia_mm, count, straight_m (per bar), hooks [(kind, n)] per bar, lap_m (one lap),
    technical (class the technical view may use: DERIVED / CODE_METHOD... or None), commercial class, confidence
Weights are never kg/m3; a bar set without a count or a length is BLOCKED (listed, never estimated here).
"""

from __future__ import annotations

import math
from collections import defaultdict

from engine.source import bbs_optimiser as BB

LAP_T, LAP_C = 70, 40                                          # p.8 note 9 (x Ø)
LEVEL = {"FOUNDATION": "GF", "GF": "GF", "1F": "1F", "2F": "2F_ROOF"}


def kgm(d):
    return d * d / 162.0


def _set(pop, element, ref, level, dia, count, straight_m, hooks=(), lap="T", technical="DERIVED",
         commercial=None, conf="H", basis="", low_f=1.0, high_f=1.0):
    return {"population": pop, "element": element, "ref": ref, "level": level, "dia_mm": dia, "count": int(count),
            "straight_m": straight_m, "hooks": list(hooks), "lap_m": (LAP_T if lap == "T" else LAP_C) * dia / 1000.0,
            "technical": technical, "commercial": commercial or technical, "confidence": conf, "basis": basis,
            "low_f": low_f, "high_f": high_f}


def _hook_m(dia, hooks):
    out, cls = 0.0, None
    for kind, n in hooks:
        h = BB.hook_addition(dia, kind)
        out += n * h["addition_m"]
        cls = h["class"]
    return out, cls


def inventory(ctx, st) -> list:
    """All bar sets: V3a sets (complete ones as they are; partial ones completed with code-method hooks), slab
    binding, ground-slab zone 2, domes, pool, exterior ground beams, necks / starters, residue beams / columns,
    side bars, F / F10, boundary wall beam."""
    rb = ctx["v3"]["rebar"]
    out = []
    for key in ("footings", "columns", "beams", "ground", "lintels"):
        for b in rb[key]:
            lv = LEVEL.get(b["floor"], "GF")
            if b.get("status") == "BLOCKED" and "side bars" in b["ref"]:
                continue                                     # completed in extra_sets (note 21 range)
            if b.get("status") == "BLOCKED":
                out.append({"population": key.upper(), "element": b["element"], "ref": b["ref"], "level": lv,
                            "state": "BLOCKED", "why": b.get("why")})
                continue
            lap = "C" if b["element"] == "COLUMN" and b["shape"] == "STRAIGHT" else "T"
            if b["hook_bend_addition_m"] == "BLOCKED_DETAILING":
                if b["shape"] == "CLOSED_LINK":
                    out.append(_set(key.upper(), b["element"], b["ref"], lv, b["dia_mm"], b["count"],
                                    b["straight_length_m"], hooks=[("135_TIE", 2)], technical="PARTIAL",
                                    commercial="PROVISIONAL_CODE_METHOD", conf="M",
                                    basis="closed link: 2 x 135° tie hooks (ACI 318-19 Table 25.3.2, edition unverified)"))
                else:
                    out.append(_set(key.upper(), b["element"], b["ref"], lv, b["dia_mm"], b["count"],
                                    b["straight_length_m"], hooks=[("90", 2)], technical="PARTIAL",
                                    commercial="PROVISIONAL_CODE_METHOD", conf="M", low_f=None,
                                    basis="end anchorage: 2 x 90° standard hooks (ACI 318-19 Table 25.3.1, edition "
                                          "unverified); low = no hook (bars continuous through supports)"))
            else:
                r = _set(key.upper(), b["element"], b["ref"], lv, b["dia_mm"], b["count"], b["straight_length_m"],
                         lap=lap, basis=b.get("basis", ""))
                if b["element"] == "COLUMN":
                    r["column_splice"] = True                        # one 40Ø lap per storey splice (V3a)
                out.append(r)
    return out


def extra_sets(ctx, struct) -> list:
    out = []
    # slab binding (B09)
    for r in struct["slab"]["rows"]:
        lv = LEVEL[r["floor"]]
        if r.get("technical") == "DERIVED" and r.get("length_mm"):
            out.append(_set("SLAB", "SLAB", f"{r['floor']} {r['text']} [{r['annotation']}]", lv, r["dia_mm"], r["count"],
                            r["length_mm"] / 1000.0, basis="bound annotation: clear span + embedment, count per panel"))
        elif r.get("commercial"):
            c = r["commercial"]
            L = c["net_m"] / r["count"]
            out.append(_set("SLAB", "SLAB", f"{r['floor']} {r['text']} [{r['annotation']}]", lv, r["dia_mm"], r["count"],
                            L, technical="PARTIAL" if r["state"] == "PARTIAL" else None, commercial=c["class"],
                            conf=c["confidence"], basis=c["method"] + "; " + c["assumption"],
                            low_f=c["low_m"] / c["net_m"], high_f=c["high_m"] / c["net_m"]))
            if r["state"] == "PARTIAL":
                out[-1]["technical_straight_m"] = r["length_mm"] / 1000.0
    # ground slab zone 2 (B10): 5Ø10/m E.W. over the closed zone
    for z in struct["ground_zones"]["zones"]:
        if z["state"] == "CLOSED_CROSS_LAYER":
            a = z["slab_m2"]
            side = math.sqrt(a)
            n = math.floor(side / 0.2) + 1
            for d in ("X", "Y"):
                out.append(_set("GROUND_SLAB", "GROUND_SLAB", f"{z['id']} 5Ø10/m {d}", "GF", 10, n, a / ((n - 1) * 0.2),
                                basis="zone area / bar spacing (5Ø10/m E.W., p.3); equivalent square bar run"))
    # domes (B05)
    for d in struct["domes"]["rows"]:
        lv = "2F_ROOF" if "TOWER" in d["id"] else "1F"
        rr = d.get("ring_rebar")
        if rr:
            for ring in rr["rings"]:
                out.append(_set("DOME", "DOME_RING_BEAM", f"{d['id']} {ring['what']}", lv, ring["dia"], ring["n"],
                                ring["length_m"], basis="DETAIL OF DOME (N.I.S., factor proved by the 442 dimension)"))
            out.append(_set("DOME", "DOME_RING_BEAM", f"{d['id']} links 8Ø8/m", lv, 8, rr["links"], rr["link_length_m"],
                            hooks=[("135_TIE", 2)], technical="PARTIAL", commercial="PROVISIONAL_CODE_METHOD", conf="M",
                            basis="ring-beam links 8Ø8/m; 135° hooks code method"))
        if d.get("mid_area_m2"):
            R, h = d["R_m"] - d["shell_t_m"] / 2, d["rise_m"] - d["shell_t_m"] / 2
            th = math.acos(max(-1.0, min(1.0, (R - h) / R)))
            mer = R * th
            n_mer = math.ceil(math.pi * d["span_m"] / 0.15)
            n_hoop = math.ceil(mer / 0.15)
            out.append(_set("DOME", "DOME_SHELL", f"{d['id']} meridional Ø12/15", lv, 12, n_mer, mer,
                            basis="shell mesh Ø12 / 15 cm (detail): meridional bars springing -> crown"))
            out.append(_set("DOME", "DOME_SHELL", f"{d['id']} hoops Ø12/15", lv, 12, n_hoop, d["mid_area_m2"] / mer,
                            basis="hoops: mid-surface area / meridian = mean hoop length"))
    # pool (B04)
    p = struct["pool"]
    if p.get("depth_m"):
        L, W = p["inner_m"]
        w, D, bt = p["wall_t_m"], p["depth_m"], p["base_t_m"]
        per = 2 * ((L + w) + (W + w))
        Lo, Wo = L + 2 * w, W + 2 * w
        vh = D + bt - 0.05
        out += [_set("POOL", "POOL_WALL", "vertical 7Ø14/m outer", "OTHER_EXTERNAL", 14, math.ceil(per * 7), vh,
                     basis="DETAIL OF SWIMMING POOL"),
                _set("POOL", "POOL_WALL", "vertical 7Ø12/m inner", "OTHER_EXTERNAL", 12, math.ceil(per * 7), vh,
                     basis="DETAIL OF SWIMMING POOL"),
                _set("POOL", "POOL_WALL", "horizontal Ø12/20 both faces", "OTHER_EXTERNAL", 12, 2 * math.ceil(D / 0.2 + 1),
                     per, basis="DETAIL OF SWIMMING POOL"),
                _set("POOL", "POOL_BASE", "base 7Ø14/m top+bottom long", "OTHER_EXTERNAL", 14, 2 * math.ceil(Wo * 7), Lo,
                     basis="DETAIL OF SWIMMING POOL (deep-end values)"),
                _set("POOL", "POOL_BASE", "base 7Ø14/m top+bottom short", "OTHER_EXTERNAL", 14, 2 * math.ceil(Lo * 7), Wo,
                     basis="DETAIL OF SWIMMING POOL (deep-end values)")]
    # exterior ground beams (B01) - provisional depth
    e = struct["ext_gb"]
    for x in ctx["v3"]["ground_items"]["beams"]:
        if x["kind"] != "EXTERIOR":
            continue
        Lx, D = x["length_m"], 1.00
        base = dict(technical=None, commercial="PROVISIONAL_SOURCE_DERIVED", conf="M",
                    basis="p.13 exterior GB bars; D = 1.00 provisional (ground to GF level)")
        out += [_set("GROUND_BEAM_EXT", "GROUND_BEAM", f"{x['id']} top 3Ø16", "GF", 16, 3, Lx, hooks=[("90", 2)], **base),
                _set("GROUND_BEAM_EXT", "GROUND_BEAM", f"{x['id']} bottom 6Ø16", "GF", 16, 6, Lx, hooks=[("90", 2)], **base),
                _set("GROUND_BEAM_EXT", "GROUND_BEAM", f"{x['id']} side 2Ø12 @30", "GF", 12, 2 * 2, Lx, **base),
                _set("GROUND_BEAM_EXT", "GROUND_BEAM", f"{x['id']} links Ø8/15", "GF", 8, math.ceil(Lx / 0.15),
                     2 * (0.30 - 0.14) + 2 * (D - 0.14), hooks=[("135_TIE", 2)], **base)]
    # necks / starters (B02)
    nk = struct["necks"]["starter_rebar_kg"]
    out.append({"population": "COLUMN_STARTERS", "element": "COLUMN", "ref": "necks / starters (all footings)",
                "level": "GF", "state": "WEIGHT_ONLY", "commercial": "PROVISIONAL_URBAN_FALLBACK", "confidence": "L",
                "kg": nk["qty"], "low_kg": nk["low"], "high_kg": nk["high"], "basis": nk["basis"], "dia_mm": 16})
    # residue beams / columns (B07): the same type's measured kg per m
    per_m = _kg_per_m_by_type(ctx)
    for b in struct["residue"]["beams"]:
        c = b.get("commercial")
        if not c or not b.get("length_m"):
            continue
        k = per_m.get(b["type"])
        if k is None:
            continue
        lv = LEVEL[b["floor"]]
        out.append({"population": "BEAM_RESIDUE", "element": "BEAM", "ref": b["id"], "level": lv, "state": "WEIGHT_ONLY",
                    "commercial": c["class"], "confidence": c["confidence"], "kg": k * b["length_m"],
                    "low_kg": k * b["length_m"] * (c["low"] / c["qty"] if c["qty"] else 0),
                    "high_kg": k * b["length_m"] * (c["high"] / c["qty"] if c["qty"] else 1), "dia_mm": None,
                    "basis": f"measured {b['type']} straight + hook weight per m ({k:.2f} kg/m) x residue length"})
    # side bars (note 21) - range 2..4 Ø12 per beam deeper than 60
    for b in ctx["v3"]["rebar"]["beams"]:
        if b.get("status") == "BLOCKED" and "side bars" in b["ref"]:
            Ls = _beam_len(ctx, b["ref"])
            if Ls:
                out.append(_set("BEAM_SIDE_BARS", "BEAM", b["ref"], LEVEL.get(b["floor"], "GF"), 12, 3, Ls, technical=None,
                                commercial="PROVISIONAL_SOURCE_RANGE", conf="M", low_f=2 / 3, high_f=4 / 3,
                                basis="p.8 note 21: 2 / 3 / 4 Ø12 by beam width - mapping not printed; 3 (mid), range 2..4"))
    # F / F10 (B06) - selected commercial basis F10
    ff = struct["f_f10"]
    lib = ctx["a3"]["footings"]["library"]["F10"]
    out += [_set("FOOTING_F_F10", "FOOTING", "F10 long 10Ø14 (selected basis)", "GF", 14, 10, lib["L_cm"] / 100 - 0.14,
                 technical=None, commercial="PROVISIONAL_SOURCE_RANGE", conf="M",
                 low_f=ff["F_SCENARIO"]["rebar_kg"] / ff["F10_SCENARIO"]["rebar_kg"], basis="F / F10 conflict, F10 selected"),
            _set("FOOTING_F_F10", "FOOTING", "F10 short 20Ø14 (selected basis)", "GF", 14, 20, lib["W_cm"] / 100 - 0.14,
                 technical=None, commercial="PROVISIONAL_SOURCE_RANGE", conf="M",
                 low_f=ff["F_SCENARIO"]["rebar_kg"] / ff["F10_SCENARIO"]["rebar_kg"], basis="F / F10 conflict, F10 selected")]
    # boundary wall beam B.W (schedule) along the S-BOUN runs
    bw = struct["boundary_wall"]
    if bw.get("length_m"):
        Lb = bw["length_m"]
        base = dict(technical=None, commercial="PROVISIONAL_SOURCE_DERIVED", conf="M",
                    basis="schedule B.W 20x60: bottom 4Ø16, top 2Ø14, 7Ø8/m; run = S-BOUN outline")
        for n, d, nm in ((4, 16, "bottom 4Ø16"), (2, 14, "top 2Ø14")):
            out.append(_set("BOUNDARY_WALL", "BEAM", f"B.W {nm}", "OTHER_EXTERNAL", d, n, Lb, **base))
        out.append(_set("BOUNDARY_WALL", "BEAM", "B.W links 7Ø8/m", "OTHER_EXTERNAL", 8, math.ceil(7 * Lb),
                        2 * (0.20 - 0.10) + 2 * (0.60 - 0.10), hooks=[("135_TIE", 2)], **base))
    # stairs: no reinforcement detail bound this round
    out.append({"population": "STAIRS", "element": "STAIR", "ref": "stair flights", "level": "GF", "state": "BLOCKED",
                "why": "no stair reinforcement callout bound (p.16 section gives the going only)"})
    return out


def _beam_len(ctx, ref):
    fl, typ = ref.split()[0], ref.split()[1]
    for o in ctx["b2a"]["sheets"].get(fl, {}).get("occurrences", []):
        if o["type"] == typ and o["state"] == "MEASURED":
            L = (o.get("lengths") or {}).get("SUPPORT_CENTRELINE_LENGTH")
            if L:
                return L
    return None


def _kg_per_m_by_type(ctx):
    acc = defaultdict(lambda: [0.0, 0.0])
    seen = set()
    for b in ctx["v3"]["rebar"]["beams"]:
        if b.get("status") == "BLOCKED":
            continue
        typ = b["ref"].split()[1]
        h, _ = _hook_m(b["dia_mm"], [("135_TIE", 2)] if b["shape"] == "CLOSED_LINK" else [("90", 2)])
        acc[typ][0] += b["count"] * (b["straight_length_m"] + h) * kgm(b["dia_mm"])
        key = b["ref"].rsplit(" ", 1)[0]
        if key not in seen and b["shape"] == "STRAIGHT":
            seen.add(key)
            acc[typ][1] += b["straight_length_m"]
    return {t: (w / L if L else None) for t, (w, L) in acc.items()}


def weigh(sets) -> list:
    """Per set: net (straight + hooks), lap addition, technical / commercial weights with ranges."""
    out = []
    for s in sets:
        if s.get("state") == "BLOCKED":
            out.append(dict(s, net_kg=None))
            continue
        if s.get("state") == "WEIGHT_ONLY":
            out.append(dict(s, net_kg=s["kg"], lap_kg=0.0, tech_kg=None))
            continue
        d = s["dia_mm"]
        k = kgm(d)
        h, hcls = _hook_m(d, s["hooks"])
        bar = s["straight_m"] + h
        pieces = BB.split_run(bar, s["lap_m"])
        laps = len(pieces) - 1
        lap_add = laps * s["lap_m"]
        if s.get("column_splice"):
            lap_add += s["lap_m"]                            # the storey splice (V3a procurement rule)
        net = s["count"] * bar * k
        tech = None
        if s["technical"] in ("DERIVED", "CODE_METHOD"):
            tech = net
        elif s["technical"] == "PARTIAL":
            tech = s["count"] * s.get("technical_straight_m", s["straight_m"]) * k   # measured straight part only
        lo_f = s["low_f"] if s["low_f"] is not None else (s["straight_m"] / bar)
        out.append(dict(s, hook_m=h, hook_class=hcls, bar_m=bar, pieces=pieces, laps_per_bar=laps,
                        net_kg=net, lap_kg=s["count"] * lap_add * k, hook_kg=s["count"] * h * k, tech_kg=tech,
                        low_kg=net * lo_f, high_kg=net * s["high_f"]))
    return out


def cutting(weighed, stock=BB.STOCK_M) -> dict:
    """BBS per diameter: technical population (sets whose technical class is complete) and the commercial
    population (all sets with geometry). Weight-only sets (no bar geometry) are reported beside the cut."""
    def run(sel):
        by = defaultdict(list)
        for s in weighed:
            if s.get("net_kg") is None or "pieces" not in s or not sel(s):
                continue
            extra = [s["lap_m"]] if s.get("column_splice") else []
            for i, p in enumerate(s["pieces"]):
                L = p + (extra[0] if (extra and i == len(s["pieces"]) - 1 and p + extra[0] <= stock) else 0.0)
                by[s["dia_mm"]].append((f"{s['ref']}#{i}", L, s["count"]))
        res = {}
        for d, pcs in sorted(by.items()):
            c = BB.cut(pcs, stock)
            k = kgm(d)
            res[d] = dict(c, kg_per_m=round(k, 4), used_kg=round(c["used_m"] * k, 3),
                          purchased_kg=round(c["purchased_m"] * k, 3), unused_kg=round(c["unused_offcut_m"] * k, 3),
                          reused_kg=round(c["reused_offcut_m"] * k, 3))
        tot = {k: round(sum(v[k] for v in res.values()), 3) for k in ("used_kg", "purchased_kg", "unused_kg", "reused_kg")}
        tot["effective_waste_pct"] = round(100 * tot["unused_kg"] / tot["purchased_kg"], 3) if tot["purchased_kg"] else 0
        return {"by_dia": res, "total": tot}
    return {"technical": run(lambda s: s["technical"] in ("DERIVED", "CODE_METHOD")),
            "commercial": run(lambda s: True), "stock_m": stock, "policy": BB.policy_record()}


def population_register(weighed) -> dict:
    pops = defaultdict(lambda: {"sets": 0, "blocked": 0, "technical_kg": 0.0, "net_kg": 0.0, "lap_kg": 0.0,
                                "hook_kg": 0.0, "low_kg": 0.0, "high_kg": 0.0, "classes": set()})
    for s in weighed:
        p = pops[s["population"]]
        p["sets"] += 1
        if s.get("net_kg") is None:
            p["blocked"] += 1
            p["classes"].add("BLOCKED")
            continue
        p["classes"].add(s.get("commercial") or s.get("technical"))
        p["net_kg"] += s["net_kg"]
        p["technical_kg"] += s.get("tech_kg") or 0.0
        p["lap_kg"] += s.get("lap_kg") or 0.0
        p["hook_kg"] += s.get("hook_kg") or 0.0
        p["low_kg"] += s.get("low_kg") or 0.0
        p["high_kg"] += s.get("high_kg") or 0.0
    rows = []
    for k, v in sorted(pops.items()):
        rows.append({"population": k, **{kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items()
                                         if kk != "classes"}, "classes": sorted(c for c in v["classes"] if c)})
    tn = sum(r["net_kg"] for r in rows)
    tt = sum(r["technical_kg"] for r in rows)
    for r in rows:
        r["weight_share_pct"] = round(100 * r["net_kg"] / tn, 2) if tn else 0
    return {"rows": rows, "net_kg": round(tn, 3), "technical_kg": round(tt, 3),
            "coverage": {"ITEM_pct": round(100 * sum(1 for r in rows if r["blocked"] < r["sets"]) / len(rows), 2),
                         "BAR_SET_pct": round(100 * sum(r["sets"] - r["blocked"] for r in rows) /
                                              sum(r["sets"] for r in rows), 2),
                         "POPULATION_pct": round(100 * sum(1 for r in rows if r["blocked"] == 0) / len(rows), 2),
                         "WEIGHT_TECHNICAL_OF_COMMERCIAL_pct": round(100 * tt / tn, 2) if tn else 0,
                         "WEIGHT_COVERAGE_ESTIMATE_note": "commercial net weight over the populations with geometry; "
                                                          "blocked populations (stairs, boxed footing bars) have no "
                                                          "weight and are listed"}}
