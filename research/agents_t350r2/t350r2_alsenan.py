"""T-350 r2 on the development villa: CALCULATED earthworks quantities per zone (owner sessions 2026-11-02 17:20 /
17:45 / 18:00) from merged, Checker-gated research ledgers only (values, DXF handles, coordinates; no drawing content):

  T-170 / T-347 pits (neat plans, overlaps, beyond-plot strips), T-320 displacement ledger (per component, value at the
  printed limit and m3 per metre below it), T-183 r2 / T-320 pool envelope, T-189 pool frame (F8 and its necks),
  T-174 / T-230 / T-350 straps (volume, drawn length, slope), T-253 main exterior ground-beam blinding,
  T-445 / T-478 F10 + F scenario blinding plans (S02 interpretations, S06 clip).

Level basis: RFI RE-REVIEW 2026-11-02 'S01 ESTIMATED: founding level = the p.9 note 1 minimum (1.5 m below the existing
plot level, existing ground +-0.00 derived) with blinding under it; ... excavation / backfill from it, labelled
ESTIMATED with +-0.10 m sensitivity'. Founding level = footing UNDERSIDE (Q-21 vocabulary) = -1.50; the printed chain
under it (underlay 0.07 + blinding 0.10, T-206 VERIFIED) puts the excavation formation at -1.67 = the T-320 limit
model at d = 0.17 m below the printed -1.50. The printed minimum itself (formation -1.50, the reading 'the 1.50 m is
the formation') stays the hard lower bound beside every pit figure.

Run: python3 -I research/agents_t350r2/t350r2_alsenan.py -> FILL_T350R2.csv, summary_t350r2.json beside this file.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import earthworks_qty_v1 as E  # noqa: E402

EG = 0.0
LIMIT = -1.50                 # ST p.9 note 1 'not less than 1.5 m below the existing plot level'
UNDERLAY, BLINDING = 0.07, 0.10
D_S01 = UNDERLAY + BLINDING   # formation below the printed limit under the S01 reading (footing underside at -1.50)
SENS = 0.10                   # S01 sensitivity, owner 2026-11-02
LIFT = E.fact(0.15, E.EST, "owner 2026-11-02 18:00: maximum 150 mm finished compacted lift, OWNER-PROVISIONAL "
              "(project drawings / geotechnical spec govern where they differ)")
S01_SRC = ("RFI RE-REVIEW 2026-11-02 S01 ESTIMATED (owner-accepted): footing underside at the p.9 note 1 minimum "
           "-1.50, underlay 0.07 + blinding 0.10 under it (T-206)")


def _csv(p):
    with open(RES / p, newline="") as f:
        return list(csv.DictReader(f))


def _json(p):
    return json.loads((RES / p).read_text())


def _f(x):
    return float(x) if x not in (None, "") else None


def inputs():
    pits = [p for p in _csv("agents_t347/PITS_T347.csv") if p["neat_status"] == "DRAWING-CONFIRMED"]
    ov = _csv("agents_t347/OVERLAPS_T347.csv")
    led = _csv("agents_t320/LEDGER_T320.csv")
    s320 = _json("agents_t320/summary.json")
    pool = _json("agents_t189/ALSENAN_OVERLAP_INPUT.json")["pool"]
    ftg = {f["id"]: f for f in _json("agents_t170/ALSENAN_EXCAVATION_INPUT.json")["footings"]}
    return pits, ov, led, s320, pool, ftg


def pool_interfaces():
    """Every pit and neck against the pool, in one frame (shapely; T-170 outlines in the raw foundation-sheet frame,
    T-189 pool frame placed by F8's corner, the plot rectangle of the foundation sheet from ZONE_INPUT_T350R2.json).
    -> per pit: neat plan in the envelope (outer r + 0.10 p.7 layers), of it beyond the plot line, footprint in the
    envelope and in the outer shell plan; per neck on those pits: its section square in the envelope / outer plan.
    The neck point is the T-205 id point (taken as the section centre; recorded, not re-read)."""
    from shapely.geometry import Point, box
    from shapely.ops import unary_union
    _, _, led, _, pool, ftg = inputs()
    zin = _json("agents_t350r2/ZONE_INPUT_T350R2.json")
    x0, y0, x1, y1 = (v / 1000 for v in zin["plot_rect_raw_mm"])
    plot = box(x0, y0, x1, y1)
    f8 = next(f for f in ftg.values() if f["type"] == "F8")
    cx, cy = f8["x0_mm"] / 1000 - pool["F8"]["x"][0], f8["y0_mm"] / 1000 - pool["F8"]["y"][0]
    r, bx = pool["outline"]["r_outer"], pool["outline"]["back_x"]
    outer = Point(cx, cy).buffer(r, quad_segs=256).intersection(box(cx - r, cy - r, cx, cy + r)).union(
        box(cx, cy - r, cx + bx, cy + r))
    env = outer.buffer(0.10, quad_segs=256)
    pits = {}
    for f in ftg.values():
        if f["type"] in ("FF", "F10/F") or f.get("detail") != "ISOLATED_P13":
            continue
        a0, b0 = f["x0_mm"] / 1000, f["y0_mm"] / 1000
        fp = box(a0, b0, a0 + f["dx_mm"] / 1000, b0 + f["dy_mm"] / 1000)
        pits[f["id"]] = {"type": f["type"], "H": f["schedule_L_W_H_m"][2], "fp": fp, "neat": fp.buffer(0.10, join_style=2)}
    U = unary_union([p["neat"] for p in pits.values()])
    Z = U.intersection(plot).difference(env)
    per = {}
    for k, p in pits.items():
        ne, fe, fo = p["neat"].intersection(env), p["fp"].intersection(env), p["fp"].intersection(outer)
        if ne.area > 1e-9:
            per[k] = {"type": p["type"], "H": p["H"], "neat_in_env_m2": round(ne.area, 6),
                      "neat_in_env_beyond_plot_m2": round(ne.difference(plot).area, 6),
                      "footprint_in_env_m2": round(fe.area, 6), "footprint_in_outer_shell_plan_m2": round(fo.area, 6)}
    necks = {}
    for c in led:
        if c["kind"] != "NECK" or c["group"][4:] not in per or not c["plan_m2"]:
            continue
        x, y = (float(v) / 1000 for v in c["id"].rsplit("@", 1)[1].split(","))
        h = math.sqrt(float(c["plan_m2"])) / 2 if c["plan_m2"] else 0.0
        nid = "NECK:COL:" + c["id"].split(":", 1)[1]
        sec = next((s_ for n in _json("agents_t205/ALSENAN_NECK_INPUT.json")["necks"] if n["id"] == nid
                    for s_ in n["sections"] if s_["printed"]), None)
        w, d_ = ((sec["W"] / 200, sec["D"] / 200) if sec else (h, h))
        sq = box(x - w, y - d_, x + w, y + d_)
        necks[c["id"]] = {"pit": per[c["group"][4:]]["type"], "plan_m2": float(c["plan_m2"]),
                          "in_env_m2": round(sq.intersection(env).area, 6),
                          "in_outer_m2": round(sq.intersection(outer).area, 6),
                          "clearance_to_env_m": round(sq.distance(env) if not sq.intersects(env) else
                                                      -sq.intersection(env).area, 4)}
    return {"zone_plan_m2": round(Z.area, 6), "union_m2": round(U.area, 6),
            "beyond_plot_m2": round(U.difference(plot).area, 6), "env_m2": round(env.area, 6),
            "pits_in_env": per, "necks_on_those_pits": necks, "route_g_zone_plan_m2": zin["zone_plan_m2"]}


def pits_zone(d=D_S01):
    pits, ov, led, s320, pool, ftg = inputs()
    ids = {p["id"] for p in pits}
    assert len(ids) == 24
    neat = sum(float(p["neat_plan_m2"]) for p in pits)
    overl = sum(float(o["neat_overlap_m2"]) for o in ov if o["a"] in ids and o["b"] in ids)
    union = neat - overl
    beyond = sum(float(p["beyond_plot_plan_m2"]) for p in pits)
    f8 = s320["f8_pool"]
    plan_t347 = union - beyond - f8["neat_in_env_m2"]     # the V3.0.43 bound's plan (F8 only, beyond counted twice)
    PI = pool_interfaces()
    env_pits = PI["pits_in_env"]
    plan = PI["zone_plan_m2"]
    fp_env = sum(v["footprint_in_env_m2"] for v in env_pits.values())
    ftg_env = sum(v["footprint_in_env_m2"] * v["H"] for v in env_pits.values())
    D = -LIMIT + d
    exc = plan * D
    # displacement inside the zone (EG -> formation), each component once
    rows = [c for c in led if c["group"].startswith("PIT:FTG") and c["group"][4:] in ids]
    val = lambda k: sum(float(c["value_m3"]) for c in rows if c["kind"] == k and c["value_m3"])  # noqa: E731
    netted = {}
    for x in s320["shared"]:
        if x["status"] == "NETTED":
            k = x["a"].rsplit(":", 1)[1]
            netted[k] = netted.get(k, 0.0) + x["value_m3"]
    blind = plan * BLINDING                                  # one layer over the zone plan (T-445 rule)
    blind_check = val("BLINDING") - netted.get("BLINDING", 0) - beyond * BLINDING - sum(
        v["neat_in_env_m2"] - v["neat_in_env_beyond_plot_m2"] for v in env_pits.values()) * BLINDING
    under = val("UNDERLAY") - netted.get("UNDERLAY", 0) - fp_env * UNDERLAY
    footing = val("FOOTING") - netted.get("FOOTING", 0) - ftg_env
    necks_b = [c for c in rows if c["kind"] == "NECK" and c["value_m3"]]
    nenv = PI["necks_on_those_pits"]
    necks = sum((float(c["value_m3"]) + float(c["coef_m3_per_m"]) * d) *
                (1 - nenv.get(c["id"], {}).get("in_env_m2", 0.0) / float(c["plan_m2"])) for c in necks_b)
    necks_coef = sum(float(c["coef_m3_per_m"]) for c in necks_b)
    c8 = next(c for c in rows if c["kind"] == "NECK" and c["status"] == "CONFLICT")
    lo, hi = (float(v) for v in c8["range_m3"].split(".."))
    h0 = -LIMIT - (UNDERLAY + BLINDING) - 0.50          # its footing F14 H 0.50 (p.9); range at d = 0 / h0 = A
    c8_lo, c8_hi = lo / h0 * (h0 + d), hi / h0 * (h0 + d)
    # strap ends inside the pits' 0.10 blinding-projection strip: section (merged volume / drawn length) x 0.10 x slope
    # (volume m3, drawn length m between the footing faces, slope factor, ends on the 24 pits): SB1's other end is on
    # the F10 + F outline (its own zone), SB2 F11 / F6, SB3 F15 / F3 (T-350 Gate B own re-measure of the 3 straps)
    straps = {"SB1": (1.5925, 4.5500, 1.0, 1), "SB2": (1.1464, 2.2927, 1.01898, 2), "SB3": (0.6516, 3.2580, 1.06818, 2)}
    strap_ends = sum(v / L * 0.10 * k * n for v, L, k, n in straps.values())
    disp_lo = blind + under + footing + necks + strap_ends + c8_lo
    disp_hi = disp_lo - c8_lo + c8_hi
    # backfill depth beside the footings: from the blinding top (formation + 0.10) to EG
    zdepth = D - BLINDING
    fp_zone = val("UNDERLAY") / UNDERLAY - netted.get("UNDERLAY", 0) / UNDERLAY - fp_env
    neck_area = sum(float(c["plan_m2"]) for c in necks_b)
    return {
        "d_below_limit_m": d, "formation_m": round(LIMIT - d, 4), "depth_m": round(D, 4),
        "plan": {"neat_sum_m2": round(neat, 6), "overlaps_once_m2": round(overl, 6), "union_m2": round(union, 6),
                 "beyond_plot_m2": round(beyond, 6), "f8_in_pool_envelope_m2": f8["neat_in_env_m2"],
                 "v3043_bound_plan_m2": round(plan_t347, 6), "zone_plan_m2": round(plan, 6),
                 "zone_plan_route_g_m2": PI["route_g_zone_plan_m2"],
                 "correction_m2": round(plan - plan_t347, 6)},
        "pool_interfaces": {k: PI[k] for k in ("pits_in_env", "necks_on_those_pits", "env_m2", "beyond_plot_m2")},
        "excavation_insitu_m3": round(exc, 6),
        "displacement": {"blinding_check_from_ledger": round(blind_check, 6), "blinding": round(blind, 6), "underlay": round(under, 6), "footings": round(footing, 6),
                         "necks_29": round(necks, 6), "necks_coef_m3_per_m": round(necks_coef, 6),
                         "neck_C8_conflict": [round(c8_lo, 6), round(c8_hi, 6)],
                         "strap_ends_in_projection_strip": round(strap_ends, 6),
                         "total": [round(disp_lo, 6), round(disp_hi, 6)]},
        "backfill_compacted_m3": [round(exc - disp_hi, 6), round(exc - disp_lo, 6)],
        "backfill_zone_depth_m": round(zdepth, 4),
        "layers": E.layers(E.fact(zdepth, E.EST, S01_SRC), LIFT)["value"],
        "formation_compaction_m2": round(plan, 6),
        "fill_plan_beside_footings_m2": round(plan - fp_zone, 6),
        "fill_plan_above_footings_m2": [round(plan - neck_area - c8_hi / (h0 + d), 6),
                                        round(plan - neck_area - c8_lo / (h0 + d), 6)],
        "beyond_plot_held": {"excavation_m3": round(beyond * D, 6), "blinding_m3": round(beyond * BLINDING, 6)},
        "under_pool_band": {"excavation_m3": round(sum(v["neat_in_env_m2"] - v["neat_in_env_beyond_plot_m2"]
                                                        for v in env_pits.values()) * d, 6),
                            "why": "the pit chains below the pool formation -1.50 under S01 inside the envelope plan; "
                                   "footing vs pool CONFLICT (F8: T-183 interface 1 / T-320; F4 / FN: this run): HELD"},
    }


DEPTH_BY_TITLE = {"GB-LT2_5M": 0.30, "GB-LT5M": 0.40, "GB-GT5M": 0.60}   # p.13 interior classes (T-242 / T-320)
MAIN_TOP, ANNEX_TOP = 0.95, 0.25


def _ledger_runs():
    """Every ground-beam run of the merged ledgers with its category: T-253 (main exterior at the N.G. datum, annex
    exterior D-35, court) and T-242 (interior main / annex: CALCULATED, D-34 title ranges, D-33)."""
    runs = []
    t253 = _csv("agents_t253/LEDGER_T253.csv")
    have = set()
    for r in t253:
        c = r["component"]
        if c.startswith("GB-EXTERIOR MAIN"):
            runs.append({"run": r["item"], "cat": "MAIN_EXT", "L": float(r["L_m"])})
        elif c.startswith("GB-EXTERIOR ANNEX"):
            runs.append({"run": r["item"], "cat": "ANNEX_EXT_D35", "L": float(r["L_m"])})
        else:
            continue
        have.add(r["item"])
    for r in _csv("agents_t242/LEDGER_T242.csv"):
        if r["component"] != "GB-INTERIOR" or r["run"] in have:
            continue
        titles = [t for t in r["titles"].split("+") if t in DEPTH_BY_TITLE]
        ds = sorted({DEPTH_BY_TITLE[t] for t in titles})
        d33 = "D-33" in r["reasons"]
        cat = ("MAIN" if r["part"] == "MAIN" else "ANNEX") + "_INT_" + ("D33" if d33 else "D")
        runs.append({"run": r["run"], "cat": cat, "L": float(r["L_m"]), "D": ds})
    return runs


def beam_deductions(d=D_S01):
    """Vo / Va / Vb: ground-beam solids below EG that lie inside the pits zone plan (own route-G read of the strips
    against the zone plan, BEAM_OVER_PITS_T350R2.csv; boundary bands ZONE_INPUT_T350R2.json). Each run is bound to
    its route-G piece(s) by handle pair (order when the counts agree, else the pair's pieces together). A run's
    below-EG solid inside the zone: blinding strip x 0.10 + beam plan x (bottom below EG). Bounds:
      MAIN_EXT   beam bottom on N.G. (T-253 Gate A): blinding only, exact; a route-G piece longer than the ledger run
                 (a column inside) -> low = overlap - dL x (b + 0.20), high = overlap.
      MAIN_INT_D top +0.95, D <= 0.60: wholly above EG (ZERO_BY_BOUND, T-242 condition) -> 0.
      MAIN_INT_D33 / ANNEX_INT_D33 / ANNEX_EXT_D35: depth not printed -> low = the blinding layer at the shallowest
                 reading (bottom at N.G. for D-35 reading L; D >= top for D-33), high = the run's own blinding layer
                 (strip x 0.10) resting on the pit's blinding top with the beam (its own plan) above it up to EG: over
                 the footing the solid would stop at the footing top, over the 0.10 projection margin only the pit's
                 blinding stops it, so the blinding top is the bound valid everywhere.
      ANNEX_INT_D top +0.25, D from the printed title class range (D-34)."""
    rows = [r for r in _csv("agents_t350r2/BEAM_OVER_PITS_T350R2.csv")]
    pieces = {}
    for r in rows:
        k = r["piece"].rsplit("#", 1)[0]
        pieces.setdefault(k, []).append(r)
    runs = _ledger_runs()
    groups = {}
    for x in runs:
        k = x["run"].split(":", 1)[1] if x["run"].startswith("ARC:") else x["run"].split("#")[0]
        k = {"114+115+7DF": "114+7DF"}.get(k, k)
        groups.setdefault(k, []).append(x)
    btop = -(LIMIT - d + BLINDING)            # EG - blinding top (formation + 0.10) under S01 (+d)
    out = {"MAIN_EXT": [0.0, 0.0], "MAIN_INT_D": [0.0, 0.0], "MAIN_INT_D33": [0.0, 0.0], "ANNEX_EXT_D35": [0.0, 0.0],
           "ANNEX_INT_D": [0.0, 0.0], "ANNEX_INT_D33": [0.0, 0.0]}
    detail = []

    def contrib(cat, strip_ov, beam_ov, per, dL, Ds):
        if cat == "MAIN_INT_D":
            return 0.0, 0.0
        if cat == "MAIN_EXT":
            return max(0.0, strip_ov - max(0.0, dL) * 0.50) * BLINDING, strip_ov * BLINDING
        if cat == "ANNEX_INT_D":
            lo = max(0.0, strip_ov - max(0.0, dL) * 0.50) * BLINDING + beam_ov * (min(Ds) - ANNEX_TOP)
            return lo, strip_ov * BLINDING + beam_ov * (max(Ds) - ANNEX_TOP)
        lo = 0.0 if cat == "MAIN_INT_D33" else max(0.0, strip_ov - max(0.0, dL) * 0.50) * BLINDING
        return lo, strip_ov * BLINDING + beam_ov * (btop - BLINDING)   # blinding layer + the beam above it

    for k, rs in groups.items():
        ps = pieces.get(k, [])
        if not ps:
            continue
        ps = sorted(ps, key=lambda r: int(r["piece"].rsplit("#", 1)[1]))
        rs = sorted(rs, key=lambda x: x["run"])
        pairs = list(zip(rs, [[p] for p in ps])) if len(ps) == len(rs) else [(None, ps)]
        for x, pl in pairs:
            members = [x] if x else rs
            cats = {m["cat"] for m in members}
            L_led = sum(m["L"] for m in members)
            L_rg = sum(float(p["L_routeG_m"]) for p in pl)
            so = sum(float(p["over_pits_m2"] or 0) for p in pl)
            bo = sum(float(p["beam_over_pits_m2"] or 0) for p in pl)
            per = [(t, float(H), float(a), float(b)) for p in pl for t, H, a, b in
                   (q.split(":") for q in p["pits"].split()) ] if any(p["pits"] for p in pl) else []
            if so <= 0:
                continue
            if len(cats) > 1:
                # mixed categories on one route-G piece set: bound by the widest member rules
                Dm = next((m.get("D") for m in members if m.get("D")), [0.30, 0.60])
                lo = min(contrib(c, so, bo, per, L_rg - L_led, Dm)[0] for c in cats)
                cat = max(cats, key=lambda c: contrib(c, so, bo, per, L_rg - L_led, Dm)[1])
                hi = contrib(cat, so, bo, per, L_rg - L_led, Dm)[1]
            else:
                cat = cats.pop()
                lo, hi = contrib(cat, so, bo, per, L_rg - L_led, members[0].get("D") or [0.30, 0.60])
            out[cat][0] += lo
            out[cat][1] += hi
            detail.append({"runs": [m["run"] for m in members], "cat": cat, "L_ledger": round(L_led, 4),
                           "L_routeG": round(L_rg, 4), "strip_over_zone_m2": round(so, 6),
                           "beam_over_zone_m2": round(bo, 6), "m3": [round(lo, 6), round(hi, 6)]})
    # information only (NOT adopted): the printed class titles read as the D-33 sections and reading L for D-35
    info = sum(r["m3"][0] for r in detail)
    for r in detail:
        if r["cat"] == "ANNEX_INT_D33":
            ds = [DEPTH_BY_TITLE[t] for x in runs if x["run"] in r["runs"] for t in [] ] or \
                 [v for x in runs if x["run"] in r["runs"] for v in (x.get("D") or [])]
            if ds:
                info += r["beam_over_zone_m2"] * (min(ds) - ANNEX_TOP)
    zin = _json("agents_t350r2/ZONE_INPUT_T350R2.json")
    vb_plan = sum(b["over_pits_m2"] for b in zin["boundary_upper"])
    res = {k: [round(v[0], 6), round(v[1], 6)] for k, v in out.items()}
    res["UPPER_BOUNDARY_GB"] = [round(vb_plan * 0.40, 6)] * 2   # p.14 A-A 20 x 40, top at N.G.: wholly -0.40 .. 0
    res["total"] = [round(sum(v[0] for v in res.values()), 6), round(sum(v[1] for v in res.values()), 6)]
    return {"by_category_m3": res, "runs": detail, "upper_boundary_plan_over_zone_m2": round(vb_plan, 6),
            "printed_class_reading_m3_information": round(info + vb_plan * 0.40, 6)}


def f10f_zone(d=D_S01):
    """S02: three interpretations, each one consistent scenario (owner 2026-11-02); in-plot plan = blinding / 0.10
    (T-478 own read, clipped low / clipped high / unclipped m3 of blinding)."""
    D = -LIMIT + d
    sc = {"F10 alone": ((0.435, 0.450, 0.480), 2.80 * 1.40 * 0.50, 2.80 * 1.40),
          "F10 + F rows": ((0.525, 0.560, 0.590), 2.80 * 1.40 * 0.50 + 0.90 * 0.80 * 0.30, 2.80 * 1.40 + 0.90 * 0.80),
          "drawn outline": ((0.5025, 0.5025, 0.552), 3.25 * 1.40 * 0.50, 3.25 * 1.40)}
    out = {}
    for k, ((bl, bh, bu), ftg, fp) in sc.items():
        out[k] = {"in_plot_plan_m2": [round(bl / BLINDING, 4), round(bh / BLINDING, 4)],
                  "excavation_in_plot_m3": [round(bl / BLINDING * D, 6), round(bh / BLINDING * D, 6)],
                  "beyond_plot_excavation_m3": [round((bu - bh) / BLINDING * D, 6), round((bu - bl) / BLINDING * D, 6)],
                  "footing_m3": round(ftg, 6), "underlay_m3": round(fp * UNDERLAY, 6),
                  "backfill_before_necks_m3": [round(bl / BLINDING * D - bl - fp * UNDERLAY - ftg, 6),
                                               round(bh / BLINDING * D - bh - fp * UNDERLAY - ftg, 6)]}
    return out


def run():
    base = pits_zone(D_S01)
    lo, hi = pits_zone(D_S01 - SENS), pits_zone(D_S01 + SENS)
    for z, dd in ((base, D_S01), (lo, D_S01 - SENS), (hi, D_S01 + SENS)):
        bd = beam_deductions(dd)
        z["beam_solids_in_zone"] = bd
        g = z["backfill_compacted_m3"]
        z["backfill_before_beam_solids_m3"] = list(g)
        z["backfill_compacted_m3"] = [round(g[0] - bd["by_category_m3"]["total"][1], 6),
                                      round(g[1] - bd["by_category_m3"]["total"][0], 6)]
    minimum = pits_zone(0.0)
    s320 = _json("agents_t320/summary.json")
    pool_in = round(s320["pool_envelope_m3"] - s320["pool_layers_beyond_plot_line_m3"], 6)
    gb_ext = s320["z1_by_family_m3"]["main-house exterior ground-beam blinding (17 runs)"]
    res = {"method": E.METHOD_ID, "rule": E.RULE_ID, "level_basis": S01_SRC, "eg_m": EG,
           "pits24": base, "pits24_sensitivity": {
               "-0.10": {"excavation_insitu_m3": lo["excavation_insitu_m3"], "backfill": lo["backfill_compacted_m3"],
                         "layers": lo["layers"]},
               "+0.10": {"excavation_insitu_m3": hi["excavation_insitu_m3"], "backfill": hi["backfill_compacted_m3"],
                         "layers": hi["layers"]}},
           "pits24_printed_minimum_bound_m3": minimum["excavation_insitu_m3"],
           "pool": {"excavation_insitu_m3": pool_in, "status": E.DC, "formation_m": -1.50,
                    "plan_m2": round(pool_in / 1.50, 6), "backfill_compacted_m3": 0.0,
                    "why_zero": "inside the neat envelope everything is shell, p.7 layers or water space (T-320 "
                                "decomposition closes); backfill only in the blinding projection beyond the membrane "
                                "(not printed) and the working space: HELD by name"},
           "gb_ext_main": {"excavation_insitu_m3": gb_ext, "status": E.DC, "formation_m": -0.10,
                           "plan_m2": round(gb_ext / 0.10, 6), "backfill_compacted_m3": 0.0,
                           "held": "the run ends over the pits (Vo): counted in both the trench and the pit plan "
                                   "until the run-end positions are netted (HELD by name, at most the trench itself)"},
           "f10f": f10f_zone(D_S01),
           "lower_gb_row": {"rule": "p.13 two-beam detail exists iff GB top - footing underside > 2.50 m (T-205 / T-042 B3)",
                            "gb_top_minus_footing_underside_m": {k: round(0.95 - LIMIT + dd, 4) for k, dd in
                                                                 (("S01", 0.0), ("S01 -0.10", -SENS), ("S01 +0.10", SENS))},
                            "required": {k: (0.95 - LIMIT + dd) > 2.50 + 1e-9 for k, dd in
                                         (("S01", 0.0), ("S01 -0.10", -SENS), ("S01 +0.10", SENS))}}}
    vo = base["beam_solids_in_zone"]["by_category_m3"]["MAIN_EXT"]
    trench = [round(gb_ext - vo[1], 6), round(gb_ext - vo[0], 6)]       # the trench outside the pit plan
    res["gb_ext_main"]["excavation_outside_pits_m3"] = trench
    res["gb_ext_main"]["inside_pits_m3"] = vo
    ex_lo = base["excavation_insitu_m3"] + pool_in + trench[0]
    ex_hi = base["excavation_insitu_m3"] + pool_in + trench[1]
    bf = base["backfill_compacted_m3"]
    res["computed_zones"] = {
        "excavation_insitu_m3": [round(ex_lo, 6), round(ex_hi, 6)],
        "backfill_compacted_m3": bf,
        "displacement_below_EG_m3": [round(ex_lo - bf[1], 6), round(ex_hi - bf[0], 6)],
        "note": "pits (S01) + pool (printed) + main exterior GB trench outside the pit plan (its run ends over the "
                "pits are inside the pit excavation); every other zone HELD by name"}
    return res


FIELDS = ["row_id", "proposed_state", "value_m3", "lo_m3", "hi_m3", "status", "basis", "sensitivity", "held_beside",
          "unit_extra"]


def fill_rows(res):
    """One row per V3.0.43 earthworks zone line (row ids of FILL_T350_T347.csv) + the coverage-gap rows."""
    p, s, f = res["pits24"], res["pits24_sensitivity"], res["f10f"]
    fl = [v for sc in f.values() for v in sc["excavation_in_plot_m3"]]
    bf = p["backfill_compacted_m3"]
    R = []
    add = lambda *a: R.append(dict(zip(FIELDS, a)))  # noqa: E731
    X, B, Dd = "B1-02 EXCAVATION|", "B1-03 BACKFILL|", "B1-04 DISPOSAL|"
    add(X + "Z1-PITS-24 (24 neat footing pits)", "VALUED", p["excavation_insitu_m3"], "", "", E.EST,
        f"in situ, EG +-0.00 to formation {p['formation_m']} over the neat union plan {p['plan']['zone_plan_m2']} m2 "
        f"(inside the plot line, minus every pit part inside the pool envelope: F8, F4, FN, owned by the pool zone to "
        f"-1.50) x {p['depth_m']}; {S01_SRC}",
        f"-0.10: {s['-0.10']['excavation_insitu_m3']}; +0.10: {s['+0.10']['excavation_insitu_m3']}; printed-minimum "
        f"bound (formation -1.50) {res['pits24_printed_minimum_bound_m3']} (V3.0.43 printed 188.017207 on a plan "
        f"{p['plan']['correction_m2']} m2 off)",
        f"working space HELD (not printed, no documented method; pits vs bulk dig OQ-13); beyond the plot line "
        f"{p['beyond_plot_held']['excavation_m3']} HELD (S06 / D-14); pit chains under the pool formation (F8, F4, FN) "
        f"{p['under_pool_band']['excavation_m3']} HELD (CONFLICT)",
        f"formation compaction {p['formation_compaction_m2']} m2")
    add(X + "Z1-PIT-FF (lift raft and pit)", "HELD", "", "", "", E.HELD, "lift pit floor 'as per lift manufacturer' "
        "(p.14): S01 does not reach it", "", "pit depth, blinding projection, working space", "raft plan 20.700 m2")
    add(X + "Z1-PIT-F10F (open outline 1B1B)", "RANGE", "", round(min(fl), 6), round(max(fl), 6), E.EST,
        "S02 three interpretations, each one scenario (F10 alone / F10 + F rows / drawn outline), S06 clip, S01 depth "
        + "; ".join(f"{k} {v['excavation_in_plot_m3'][0]}..{v['excavation_in_plot_m3'][1]}" for k, v in f.items()),
        "+-0.10 m: +-plan x 0.10", "beyond the plot line per scenario HELD; working space", "")
    add(X + "Z1-POOL (pool envelope to the printed -1.50)", "VALUED", res["pool"]["excavation_insitu_m3"], "", "", E.DC,
        "neat envelope inside the plot x printed formation -1.50 (T-183 r2 chain from the rim)", "none (printed)",
        "blinding projection beyond the membrane line, working space, envelope beyond the plot line 0.5486 HELD",
        f"formation compaction {res['pool']['plan_m2']} m2")
    tr = res["gb_ext_main"]["excavation_outside_pits_m3"]
    add(X + "Z1-TRENCH-EXT-GB-MAIN (17 runs, cut for the blinding only)", "RANGE", "", tr[0], tr[1], E.DC,
        f"neat cut L 55.99 x 0.50 x 0.10 = {res['gb_ext_main']['excavation_insitu_m3']} less the run ends inside the "
        f"pit plan {res['gb_ext_main']['inside_pits_m3'][0]}..{res['gb_ext_main']['inside_pits_m3'][1]} (own route-G "
        f"read per run; those are dug with the pits)", "none (printed)", "working space HELD",
        f"formation compaction {round(tr[0] / 0.10, 4)}..{round(tr[1] / 0.10, 4)} m2 outside the pits ('COMPACTED SOIL', p.13)")
    for z in ("Z1-TRENCH-INT-GB-MAIN-ZERO (13 runs wholly above EG)", "Z1-TRENCH-INT-GB-MAIN-D33 (sections not printed)",
              "Z1-TRENCH-ANNEX (interior D-34 / D-33, exterior D-35)", "Z1-TRENCH-COURT (3 runs)",
              "Z1-TRENCH-STRAPS (SB1 / SB2 / SB3)", "Z1-TRENCH-BOUNDARY (p.14 typical boundary wall)"):
        add(X + z, "UNCHANGED", "", "", "", "as V3.0.43", "S01 does not settle this zone's open dimension", "", "", "")
    lg = res["lower_gb_row"]
    add(X + "Z1-LOWER-GB-ROW (p.13 two-beam detail)", "NOT_REQUIRED_UNDER_S01", "", "", "", E.EST,
        f"{lg['rule']}: S01 {lg['gb_top_minus_footing_underside_m']['S01']} m -> not required",
        f"+0.10: {lg['gb_top_minus_footing_underside_m']['S01 +0.10']} m -> REQUIRED (flips)", "no plan draws it", "")
    add(B + "Z1-PITS-24", "RANGE", "", bf[0], bf[1], E.EST,
        "excavated - displacement below EG at actual positions, once: blinding / underlay / footings net + 29 necks "
        "at S01 height + C8 conflict range + strap ends in the projection strip + ground-beam solids over the pits "
        f"(per run, own route-G read): {json.dumps(p['beam_solids_in_zone']['by_category_m3'])}",
        f"-0.10: {s['-0.10']['backfill']}; +0.10: {s['+0.10']['backfill']}",
        "the range is the D-33 / D-35 beam sections (designer items): high end = shallowest reading, low end = the "
        "solid down to the pit blinding; information, not adopted: printed class titles as sections -> "
        f"{round(p['backfill_before_beam_solids_m3'][1] - p['beam_solids_in_zone']['printed_class_reading_m3_information'], 6)}",
        f"{p['layers']} layers at 0.15 (zone depth {p['backfill_zone_depth_m']} m, OWNER-PROVISIONAL lift); fill plan "
        f"beside footings {p['fill_plan_beside_footings_m2']} m2, above footings {p['fill_plan_above_footings_m2'][0]}"
        f"..{p['fill_plan_above_footings_m2'][1]} m2")
    add(B + "Z1-POOL", "HELD", "", "", "", E.HELD, "neat envelope part calculated 0.000 (all shell / layers / water "
        "space): the zone's backfill lies wholly in held geometry", "", "blinding projection, working space", "")
    add(B + "Z1-TRENCH-EXT-GB-MAIN", "HELD", "", "", "", E.HELD, "neat cut part calculated 0.000 (filled by the "
        "blinding): the zone's backfill lies wholly in the working space", "", "working space", "")
    add(B + "Z1-OTHER-TRENCHES (annex, court, straps, boundary, D-33)", "UNCHANGED", "", "", "", "as V3.0.43", "", "", "", "")
    add(B + "Z2 (fill above EG under the GF ground slab, from excavated soil)", "UNCHANGED", "", "", "", "as V3.0.43",
        "enclosed plan, wet-floor b, D-33 / D-34 not established", "", "", "")
    add(Dd + "ALL ZONES", "HELD", "", "", "", E.HELD,
        "dry-mass balance (EARTHWORKS_QTY_V1.dry_mass_balance): in-situ dry density, placement target density, "
        "suitable share (geotechnical), loose densities and the Z2 draw all HELD; payable basis in situ",
        "", f"displacement below EG in the computed zones {res['computed_zones']['displacement_below_EG_m3'][0]}.."
        f"{res['computed_zones']['displacement_below_EG_m3'][1]} m3 = the geometric surplus only if compacted and "
        f"in-situ dry densities were equal and no soil went to Z2 (neither is established)", "")
    for sc, v in f.items():
        add(B + f"GAP Z1-PIT-F10F [{sc}]", "PROPOSED_NEW_LINE_HELD", "", v["backfill_before_necks_m3"][0],
            v["backfill_before_necks_m3"][1], E.HELD, "coverage gap: B1-02 has the zone, B1-03 has no line; value "
            "before the C10 / C necks (HELD, Q-31 C)", "", "necks C10 / C; SB1 in F10 + F", "")
    add(B + "GAP Z1-PIT-FF", "PROPOSED_NEW_LINE_HELD", "", "", "", E.HELD, "coverage gap: B1-02 has the zone, B1-03 "
        "has no line", "", "lift pit depth", "")
    return R


def write(res):
    (HERE / "summary_t350r2.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    with open(HERE / "FILL_T350R2.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(fill_rows(res))


if __name__ == "__main__":
    r = run()
    write(r)
    print(json.dumps(r, indent=1, sort_keys=True))
