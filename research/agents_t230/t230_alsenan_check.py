"""T-230 on the development villa: every strap / ground-beam (tie-beam) end, its intersection volume and its owner.

Inputs (values, ids and DXF handles only; no drawing content): ALSENAN_END_INPUT.json (t230_extract.py on 'ST7757
dxf.dxf' this run), research/agents_t174/T174_STRAPS.json (T-174 MERGED 984ebbe1, Checker 14:52: strap plan areas in
the footings), research/agents_t141/T141_SPANS.csv (GROUND_SYSTEM_SPANS_V2 spans and p.13 depth classes),
research/agents_t138/T138_MEMBERS.csv (exterior-wall beams, "FOLLOW ARCH." depth). Outputs: LEDGER_T230.csv,
summary.json. Run: python3 -I research/agents_t230/t230_alsenan_check.py [--write]
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import end_ownership as EO  # noqa: E402

# p.13 typical ground-beam sections (depth by span length) and the exterior-wall beam "FOLLOW ARCH." from the GF slab
# level +0.95 (T-214, DRAWING-CONFIRMED) to the outer ground: +-0.00 or the court +0.15 (bottom HELD, D-35)
DEPTH = {"P13-GB-GT5M": 0.60, "P13-GB-LT5M": 0.40, "P13-GB-LT2_5M": 0.30, "GT5M": 0.60, "LT5M": 0.40,
         "LT2_5M": 0.30, "EXT": (0.80, 0.95)}
# level chain (T-206 / T-214, merged; values only)
FORMATION_AT_MOST = -1.50      # p.9 boxed note 1 (a limit)
FOOTING_SOFFIT_ABOVE_FORMATION = 0.17   # p.13 stack 0.10 blinding + 0.02 membrane + 0.05 screed (T-206)
GB_TOP_MAIN, GB_TOP_ANNEX = 0.95, 0.25  # GF structural slab tops (T-214); exterior GB top = GF slab level (p.13)
H_MAX = 0.70                   # thickest footing (F12, p.9)


def depths_of(span, t141, t138):
    r = t141.get(span)
    det = t138.get(r["hand_occurrence"]) if r else None
    out = set()
    if det:
        for c in det.replace("CONC/", "").split("/"):
            v = DEPTH.get(c.strip())
            if isinstance(v, tuple):
                out |= set(v)
            elif v:
                out.add(v)
    if not out and r:
        for c in r["v2_class"].split("+"):
            if c in DEPTH:
                out.add(DEPTH[c])
    return sorted(out)


def class_of(L):
    return 0.60 if L > 5.0 else (0.40 if L > 2.5 else 0.30)


def main(write=False):
    inp = json.loads((HERE / "ALSENAN_END_INPUT.json").read_text(encoding="utf-8"))
    straps = json.loads((ROOT / "research/agents_t174/T174_STRAPS.json").read_text(encoding="utf-8"))
    t141 = {r["span_id"]: r for r in csv.DictReader(open(ROOT / "research/agents_t141/T141_SPANS.csv",
                                                          encoding="utf-8"))}
    t138 = {}
    for r in csv.DictReader(open(ROOT / "research/agents_t138/T138_MEMBERS.csv", encoding="utf-8")):
        if r["component"] == "TOP":
            t138[r["member"]] = r["detail"]
    ledger, summ = [], {"policy": EO.policy_record()}

    # ---------------------------------------------------------------- A. strap ends (T-174 plan areas)
    sep_strap = []
    for s in straps:
        D = s["D_m"]
        ends = []
        for f in s["concrete_in_footings"]:
            H = f.get("H_m")
            A_net = f.get("A_in_m2")
            A_col = f.get("column_area_removed_m2", 0.0)
            r0 = EO.strap_end(D, H, A_net, A_col, 0.0)
            ends.append({"end": f["footing"], "H": H, "A_net": A_net, "A_col": A_col})
            if r0["status"] == EO.HELD:
                ledger.append({"element": f"STRAP {s['mark']}", "end": f["footing"], "pair": "STRAP / FOOTING",
                               "owner": "UNDETERMINED", "volume_m3": "", "range_m3": "",
                               "status": EO.HELD, "basis": f"{r0['missing']} not printed (Q-31 C, F10 + F)"})
                continue
            ledger.append({"element": f"STRAP {s['mark']}", "end": f["footing"], "pair": "STRAP / FOOTING",
                           "owner": "FOOTING", "volume_m3": round(r0["footing_m3"], 4), "range_m3": "",
                           "status": "DRAWING-CONFIRMED at e = 0 (strap soffit = footing soffit)",
                           "basis": f"A_net {A_net} m2 x min(D {D}, H {H}); strap excess {round(r0['strap_excess_m3'], 4)}"})
            ledger.append({"element": f"STRAP {s['mark']}", "end": f["footing"], "pair": "STRAP / NECK",
                           "owner": "NECK", "volume_m3": round(r0["neck_m3"], 4), "range_m3": "",
                           "status": "DRAWING-CONFIRMED at e = 0",
                           "basis": f"column footprint in the strap {A_col} m2 x (e + D - H)+"})
        if all(x["H"] is not None and x["A_net"] is not None for x in ends):
            rng = EO.strap_level_range(D, ends)
            nonneg = EO.strap_level_range(D, ends, e_min=0.0)
            summ.setdefault("strap_level", {})[s["mark"]] = {
                "D": D, "ends": [(x["end"], x["H"], x["A_net"], x["A_col"]) for x in ends],
                "excess_at_e0_m3": round(rng["excess_at_e0_m3"], 4), "neck_at_e0_m3": round(rng["neck_at_e0_m3"], 4),
                "excess_min_m3": round(rng["excess_min_m3"], 4), "e_at_min_m": rng["e_at_min_m"],
                "excess_sup_monolithic_m3": round(rng["excess_sup_m3"], 4), "e_range_m": rng["e_range_m"],
                "excess_sup_soffit_not_below_m3": round(nonneg["excess_sup_m3"], 4),
                "exposure_per_0_10_m_of_e_m3": round(sum(x["A_net"] for x in ends) * 0.10, 4)}
        # strap top vs any ground-beam soffit (3-D separation)
        Hs = [x["H"] for x in ends if x["H"] is not None]
        if Hs:
            top_e0 = FORMATION_AT_MOST + FOOTING_SOFFIT_ABOVE_FORMATION + D
            top_mono = FORMATION_AT_MOST + FOOTING_SOFFIT_ABOVE_FORMATION + min(Hs) + D
            sep_strap.append({"strap": s["mark"], "strap_top_at_e0_at_most_m": round(top_e0, 3),
                              "strap_top_monolithic_bound_m": round(top_mono, 3)})
    summ["strap_top"] = sep_strap

    # ---------------------------------------------------------------- B. ground-beam ends at necks
    jl = []
    per_end = {}
    for e in inp["column_ends"]:
        per_end.setdefault(e["column"], []).append(e)
    for j in inp["junctions"]:
        spans = sorted({e.split(":")[0] for e in j["ends"]})
        ds = sorted({d for sp in spans for d in depths_of(sp, t141, t138)})
        dbl, gap = j["double_plan_m2_per_reading"], j["gap_plan_m2_per_reading"]
        if not ds:
            continue
        # DOUBLE: each end's plan overlap x THAT span's depth; GAP (a region shared by the bands at the junction):
        # plan x the depths of the spans meeting there
        nread = len(dbl)
        lo_k, hi_k = [], []
        for k in range(nread):
            lo_s = hi_s = 0.0
            for e in per_end.get(j["column"], []):
                d_e = depths_of(e["span_id"], t141, t138) or ds
                lo_s += e["double_plan_m2_per_reading"][k] * min(d_e)
                hi_s += e["double_plan_m2_per_reading"][k] * max(d_e)
            lo_k.append(lo_s)
            hi_k.append(hi_s)
        lo_d, hi_d = min(lo_k), max(hi_k)
        dbl_spans = sorted({e["span_id"] for e in per_end.get(j["column"], [])
                            if max(e["double_plan_m2_per_reading"]) > 0})
        if dbl_spans:
            ds_d = sorted({d for sp in dbl_spans for d in depths_of(sp, t141, t138)})
        else:
            ds_d = []
        lo_g, hi_g = min(gap) * ds[0], max(gap) * ds[-1]
        if max(dbl) > 0 and max(gap) == 0:
            ds = ds_d or ds
        if max(dbl) == 0 and max(gap) == 0:
            st = "DRAWING-CONFIRMED (0 in every reading)"
        elif j["neck_status"] == EO.DRAWING_CONFIRMED and len(ds) == 1:
            st = EO.DRAWING_CONFIRMED
        elif j["neck_status"] == EO.CONFLICT:
            st = "CONFLICT (T-217 section)" + (" + depth candidates" if len(ds) > 1 else "")
        else:
            st = EO.HELD + (" (depth candidates / exterior bottom D-35)" if len(ds) > 1 else "")
        row = {"column": j["column"], "ends": j["ends"], "neck": j["neck_note"], "depths_m": ds,
               "double_plan_m2": (min(dbl), max(dbl)), "gap_plan_m2": (min(gap), max(gap)),
               "double_m3": (round(lo_d, 4), round(hi_d, 4)), "gap_m3": (round(lo_g, 4), round(hi_g, 4)),
               "status": st}
        jl.append(row)
        if max(dbl) > 0 or max(gap) > 0:
            ledger.append({"element": f"GB at {j['column']}", "end": " ".join(j["ends"]),
                           "pair": "GROUND BEAM / NECK",
                           "owner": "NECK owns the DOUBLE (beam measured net)" if max(dbl) > 0 and max(gap) == 0 else
                           ("GROUND BEAM keeps the GAP (no other line contains it)" if max(dbl) == 0 else
                            "NECK owns the DOUBLE; GROUND BEAM keeps the GAP"),
                           "volume_m3": round(hi_d, 4) if lo_d == hi_d and max(dbl) > 0 else "",
                           "range_m3": f"DOUBLE {round(lo_d, 4)}..{round(hi_d, 4)}; GAP {round(lo_g, 4)}..{round(hi_g, 4)}",
                           "status": st, "basis": f"{j['neck_note']}; depths {ds}"})
    summ["junctions_total"] = len(jl)
    summ["junctions_zero"] = sum(1 for r in jl if r["status"].startswith("DRAWING-CONFIRMED (0"))
    summ["junctions_nonzero"] = [r for r in jl if not r["status"].startswith("DRAWING-CONFIRMED (0")]
    conf = [r for r in jl if r["status"] == EO.DRAWING_CONFIRMED]
    summ["gb_double_confirmed_m3"] = (round(sum(r["double_m3"][0] for r in conf), 4),
                                      round(sum(r["double_m3"][1] for r in conf), 4))
    summ["gb_double_confirmed_plan_m2"] = round(sum(r["double_plan_m2"][1] for r in conf), 4)
    ext = [r for r in jl if r["double_plan_m2"][1] > 0 and r["status"].startswith("HELD")]
    summ["gb_double_exterior_m3"] = (round(sum(r["double_m3"][0] for r in ext), 4),
                                     round(sum(r["double_m3"][1] for r in ext), 4))

    # ---------------------------------------------------------------- C. ground-beam ends at the lift ring
    fr = []
    for f in inp["free_ends"]:
        r = t141.get(f["span_id"], {})
        old_ds = sorted({DEPTH[c] for c in r.get("v2_class", "").split("+") if c in DEPTH})
        L_old = f["v2_face_to_face_m"]
        L_new = f["length_to_support_m"]
        row = {"span_id": f["span_id"], "end": f["end"], "v2_node": f["v2_node"], "v2_refs": f["v2_refs"],
               "v2_status": r.get("v2_status"), "support": f["support"], "status": f["status"],
               "refused": f["refused"], "L_v2_m": L_old, "L_to_support_m": L_new}
        if L_new is not None:
            Dn = class_of(L_new)
            row.update({"D_new_m": Dn, "m3_v2": [round(L_old * 0.30 * d, 4) for d in old_ds],
                        "m3_new": round(L_new * 0.30 * Dn, 4),
                        "delta_m3": [round(L_new * 0.30 * Dn - L_old * 0.30 * d, 4) for d in old_ds]})
            ledger.append({"element": f"GB {f['span_id']}", "end": f["end"], "pair": "GROUND BEAM / LIFT RING",
                           "owner": "GROUND BEAM to the ring face (ring owns its own wall)",
                           "volume_m3": round(L_new * 0.30 * Dn, 4), "range_m3": "",
                           "status": EO.DRAWING_CONFIRMED,
                           "basis": f"band drawn to {f['support']} (T-204 ring outer face); {L_new} m x 0.30 x {Dn}"
                                    f" (p.13 class); V2 {f['v2_node']} {f['v2_refs']} {L_old} m: "
                                    + ("the footing outline is no support (no 3-D contact)" if f["refused"] else
                                       "the column is beside the band (not in its path); the ring face is the end")})
        fr.append(row)
    summ["ring_ends"] = fr

    # ---------------------------------------------------------------- D. plan overlaps that are not intersections
    ov = inp["gb_footing_plan_overlaps"]
    soffit_min = min(GB_TOP_ANNEX - 0.60, 0.00)
    ftop_max = FORMATION_AT_MOST + FOOTING_SOFFIT_ABOVE_FORMATION + H_MAX
    summ["gb_footing"] = {"plan_overlaps": len(ov), "spans": len({o["span_id"] for o in ov}),
                          "plan_overlap_m2": round(sum(o["plan_overlap_m2"] for o in ov), 4),
                          "gb_soffit_at_least_m": round(soffit_min, 3), "footing_top_at_most_m": round(ftop_max, 3),
                          "vertical_gap_at_least_m": round(soffit_min - ftop_max, 3), "intersection_m3": 0.0}
    ledger.append({"element": "GB over footings (51 spans)", "end": "-", "pair": "GROUND BEAM / FOOTING",
                   "owner": "none (no 3-D intersection)", "volume_m3": 0.0, "range_m3": "",
                   "status": EO.DRAWING_CONFIRMED,
                   "basis": f"plan overlap {summ['gb_footing']['plan_overlap_m2']} m2; GB soffit >= {round(soffit_min, 2)}"
                            f" vs footing top <= {round(ftop_max, 2)} (gap >= {round(soffit_min - ftop_max, 2)} m)"})
    so = inp["strap_gb_plan_overlaps"]
    summ["strap_gb"] = {"plan_overlaps": so, "plan_overlap_m2": round(sum(o["plan_overlap_m2"] for o in so), 4)}

    if write:
        with open(HERE / "LEDGER_T230.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["element", "end", "pair", "owner", "volume_m3", "range_m3", "status",
                                              "basis"])
            w.writeheader()
            w.writerows(ledger)
        (HERE / "summary.json").write_text(json.dumps(summ, indent=1, sort_keys=True, default=list) + "\n",
                                           encoding="utf-8")
    return ledger, summ


if __name__ == "__main__":
    led, s = main(write="--write" in sys.argv)
    for r in led:
        print(r)
    print(json.dumps({k: v for k, v in s.items() if k != "policy"}, indent=1, default=list)[:6000])
