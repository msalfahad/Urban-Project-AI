"""T-700 on the development villa: the zones T-695 left open, measured, and the B1 census restated for wiring
(values only; no drawing content). Inputs, each pinned by sha256:

  research/agents_t687/out/LINE_INDEX_V3_0_69.json   newest candidate line index (ground-slab + earthworks lines; the
                                                      20 STR.EARTH lines are checked equal to V3.0.68, T-695's record)
  research/agents_t672/out/LINE_INDEX_V3_0_68.json   T-695's candidate of record
  research/agents_t700/ZONE_INPUT_T700.json          own read of 'ST7757 dxf.dxf' (t700_extract.py)
  research/agents_t242/LEDGER_T242.csv               merged T-242 (ground-beam runs: L, b, titles, D-33 / D-34 / D-35,
                                                      court; ground-slab panels: printed level S1, room)
  research/agents_t695/*                             merged T-695 (census, zones, piece classes, free strips)

    python3 -I research/agents_t700/t700_alsenan.py   -> WIRING_T700.csv, ZONES_T700.json, summary_t700.json
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RES / "agents_t695"))
import earthworks_round2_v1 as R2  # noqa: E402
import earthworks_census_v1 as E  # noqa: E402
import t695_alsenan as T695  # noqa: E402

IDX69, IDX68 = "agents_t687/out/LINE_INDEX_V3_0_69.json", "agents_t672/out/LINE_INDEX_V3_0_68.json"
PINS = {IDX69: None, IDX68: None, "agents_t700/ZONE_INPUT_T700.json": None, "agents_t242/LEDGER_T242.csv": None,
        "agents_t695/CENSUS_T695.csv": None, "agents_t695/ZONES_T695.json": None,
        "agents_t695/STRAP_TRENCH_INPUT_T695.json": None}

EG = 0.0                    # existing ground +-0.00 DRAWING-CONFIRMED (T-170 / T-253)
SENS = 0.10                 # EG / S01 sensitivity shown beside, never mixed
LIFT = 0.15                 # owner 2026-11-02 18:00, OWNER-PROVISIONAL
B_FLOOR, T_SLAB = 0.05, 0.10  # T-214 floor build-up 0.05 DRAWING-CONFIRMED on the dry chains; 'T=10cm' (T-206)
BLINDING, PROJ = 0.10, 0.10   # p.13 GB sections on a 10 cm base '10 / 30 / 10'
MAIN_TOP, ANNEX_TOP = 0.95, 0.25
DEPTH_BY_TITLE = {"GB-LT2_5M": 0.30, "GB-LT5M": 0.40, "GB-GT5M": 0.60}
FFL_MAIN, FFL_ANNEX, FFL_COURT = 1.00, 0.30, 0.15   # GB-plan LEVEL marks; courts +0.15 = paving ON N.G. (T-320)
# S01 (owner-accepted RFI re-review, ESTIMATED): footing underside -1.50; footing chain R3 underlay 0.07 + blinding 0.10
S01_UNDERSIDE, UNDERLAY = 1.50, 0.07
# lift pit FF (T-322 merged, p.9 / p.14): raft 4.60 x 4.50 x 0.55, '5cm Screed', '10cm Plain con.', ring 2.20 / 1.80;
# p.9 note 1: foundation level 'not less than 1.50 m below the existing plot level' (Q-21 C: a minimum)
FF_T, FF_SCREED, FF_BLIND, FOUND_MIN = 0.55, 0.05, 0.10, 1.50
# c1089bdb (L-41cfb82e, 35.6054 m2): T-391 / T-444 merged own panels; OWN-009 carries +1.00 (1C2) and +0.30 (1C9)
C1089 = {"OWN-007": (11.9237, [FFL_MAIN]), "OWN-010": (10.9742, [FFL_MAIN]), "OWN-047": (1.1875, [FFL_MAIN]),
         "OWN-009": (11.52, [FFL_ANNEX, FFL_MAIN])}
NO_LEVEL = {"SITE-c26e93b649f5066b": "GS-12 'Garden / yard / court' (floored or open: not printed, T-242)",
            "SITE-67b20a045d91a15c": "GS-16 in no GF room, no level mark (T-242)"}
GS28 = "SITE-2870ca7b6a82bfa0"   # T-242 GS-28 kitchen, printed +0.30 (S1); not a route-G SH08 face


def sha(rel):
    return hashlib.sha256((RES / rel).read_bytes()).hexdigest()


def _csv(rel):
    with open(RES / rel, newline="") as f:
        return list(csv.DictReader(f))


def _gs_lines(idx):
    return {x["element_id"].split(":")[-1]: x for x in idx["lines"] if x["item_code"] == "STR.CONC.GROUND_SLAB"}


# ------------------------------------------------------------------------------------------------------- Z2 ----

def z2_terms(gs, gsheet, eg):
    """panel terms (one per candidate GS line; c1089bdb by its four own panels) and beam terms (T-242 runs)"""
    panels, basis = [], {}
    blocks = {b["block"]: b for b in gsheet["blocks"]}
    annex_block = [b["block"] for b in gsheet["blocks"] if set(b["level_marks_inside"]) == {"+0.30"}]
    main_block = [b["block"] for b in gsheet["blocks"] if "+1.00" in b["level_marks_inside"]]
    assert len(annex_block) == 1 and len(main_block) == 1, gsheet["blocks"]
    for cell, ln in sorted(gs.items()):
        a = round(ln["measured_net"] / T_SLAB, 6)
        if cell == "SITE-c1089bdb4cfcdc4a":
            assert abs(sum(v[0] for v in C1089.values()) - a) < 1e-4, a
            for own, (ar, ffl) in C1089.items():
                panels.append(R2.panel_term(f"{cell}/{own}", ar, ffl, B_FLOOR, T_SLAB, eg))
                basis[f"{cell}/{own}"] = ("SPLIT +0.30 / +1.00 (1C9 / 1C2), extent of each zone not printed"
                                          if len(ffl) > 1 else "main block, GF +1.00 (T-391 / T-444 own panel)")
            continue
        if cell == GS28:
            ffl, why = [FFL_ANNEX], "T-242 GS-28 printed +0.30 (S1)"
        elif cell in NO_LEVEL:
            ffl, why = [FFL_COURT, FFL_MAIN], NO_LEVEL[cell] + ": court on N.G. (0) .. floored +1.00"
        else:
            p = gsheet["panels"][cell]
            if p["block"] == annex_block[0]:
                ffl, why = [FFL_ANNEX], "annex block (marks +0.30 only)"
            elif p["block"] == main_block[0]:
                assert "+0.30" not in p["level_marks_inside"], cell
                ffl, why = [FFL_MAIN], "main block, GF +1.00 (T-214); the block's lobby mark 1C9 lies in c1089bdb"
            else:
                raise SystemExit(f"{cell}: block not established")
            assert abs(p["area_m2"] - a) < 0.005 or cell in ("SITE-49a7dae5c139aebb", "SITE-3f7728a83b30ec14",
                                                             "SITE-c1b4b440fb6ecf4c"), (cell, p["area_m2"], a)
        panels.append(R2.panel_term(cell, a, ffl, B_FLOOR, T_SLAB, eg))
        basis[cell] = why
    beams = []
    for r in _csv("agents_t242/LEDGER_T242.csv"):
        comp, part = r["component"], r["part"]
        if not comp.startswith("GB-") or part not in ("MAIN", "ANNEX"):
            continue
        L, b = float(r["L_m"]), float(r["b_m"])
        ds = sorted({DEPTH_BY_TITLE[t] for t in r["titles"].split("+") if t in DEPTH_BY_TITLE})
        rs = r["reasons"]
        top = MAIN_TOP if part == "MAIN" else ANNEX_TOP
        if comp.startswith("GB-EXTERIOR"):
            if part == "MAIN":     # D-35 FOLLOW ARCH. to the outer ground: 0.80 (court +0.15) .. 0.95 (N.G.)
                t = R2.beam_term(r["run"], L, b, top, BLINDING, eg, PROJ, [0.80, 0.95], outer_proj=True)
            else:                  # D-35 annex: literal 0.10 .. 0.25 against the printed sections (source conflict)
                t = R2.beam_term(r["run"], L, b, top, BLINDING, eg, PROJ, [0.10, 0.25] + (ds or []),
                                 outer_proj=True)
            t["class"] = f"{part}_EXT_D35"
        elif comp == "GB-COURT":   # section and top not established: court top (+0.15 - 0.05) .. GF +0.95
            cand = sorted({float(x) for x in rs.split("candidates")[1].split("|")[0].replace("/", " ").split()
                           if x.replace(".", "").isdigit()})
            ts = [R2.beam_term(r["run"], L, b, tp, BLINDING, eg, PROJ, cand, outer_proj=True)
                  for tp in (FFL_COURT - B_FLOOR, MAIN_TOP)]
            t = dict(ts[1], fill_m3=[min(x["fill_m3"][0] for x in ts), max(x["fill_m3"][1] for x in ts)])
            t["class"] = "COURT"
        else:
            d33 = "D-33" in rs
            t = R2.beam_term(r["run"], L, b, top, BLINDING, eg, PROJ, ds, open_above=d33)
            t["class"] = f"{part}_INT" + ("_D33" if d33 else "_D34" if len(ds) > 1 else "")
        beams.append(t)
    return panels, beams, basis


def z2(gs, gsheet):
    out = {}
    for tag, eg in (("EG", EG), ("EG-0.10", EG - SENS), ("EG+0.10", EG + SENS)):
        panels, beams, basis = z2_terms(gs, gsheet, eg)
        zone = R2.z2_zone(panels, beams, LIFT)
        by = {}
        for t in panels:
            w = basis[t["cell"]]
            k = "PANEL_" + ("HELD_LEVEL" if t["depth_m"][0] != t["depth_m"][1] else
                            "ANNEX_030" if "+0.30" in w else "MAIN_100")
            v = by.setdefault(k, {"n": 0, "area_m2": 0.0, "fill_m3": [0.0, 0.0]})
            v["n"] += 1
            v["area_m2"] += t["area_m2"]
            v["fill_m3"] = [v["fill_m3"][0] + t["fill_m3"][0], v["fill_m3"][1] + t["fill_m3"][1]]
        for t in beams:
            v = by.setdefault("BEAM_" + t["class"], {"n": 0, "L_m": 0.0, "fill_m3": [0.0, 0.0]})
            v["n"] += 1
            v["L_m"] += t["L_m"]
            v["fill_m3"] = [v["fill_m3"][0] + t["fill_m3"][0], v["fill_m3"][1] + t["fill_m3"][1]]
        for v in by.values():
            v["fill_m3"] = [round(x, 6) for x in v["fill_m3"]]
            for k in ("area_m2", "L_m"):
                if k in v:
                    v[k] = round(v[k], 6)
        out[tag] = {"zone": zone, "by_class": dict(sorted(by.items()))}
        if tag == "EG":
            out["panels"] = panels
            out["beams"] = beams
            out["panel_basis"] = basis
            # layer counts per class at EG (the OWNER-PROVISIONAL 0.15 lift): main 0.85, annex 0.15, under-beam <= 0.55
            out["layers"] = {"main_panels": R2.layers(FFL_MAIN - B_FLOOR - T_SLAB - EG, LIFT),
                             "annex_panels": R2.layers(FFL_ANNEX - B_FLOOR - T_SLAB - EG, LIFT),
                             "under_main_interior_beam_max": R2.layers(MAIN_TOP - 0.30 - BLINDING - EG, LIFT)}
    return out


# ------------------------------------------------------------------------------------------------- lift pit ----

def lift_pit(lp):
    raw = lp["raw"]
    assert raw["plan_m2"] == 20.7 and lp["ring_outer_inside_ff_raw_m2"] == lp["ring_outer_plan_m2"] == 4.84
    others = {"pits zone Z": raw["in_pits_zone_m2"], "F10 / F drawn": raw["in_f10_drawn_m2"],
              "pool envelope": raw["in_pool_envelope_m2"], "beyond plot": raw["beyond_plot_m2"],
              **{f"strap {k}": v["in_ff_raw_m2"] for k, v in lp["straps"].items()}}
    a = R2.own_plan(raw["plan_m2"], others)
    lit = R2.supplier_pit_at_least(a, lp["ring_outer_plan_m2"], FOUND_MIN - FF_SCREED - FF_BLIND, FF_T,
                                   {"screed": FF_SCREED, "blinding": FF_BLIND}, EG)
    s01 = R2.supplier_pit_at_least(a, lp["ring_outer_plan_m2"], S01_UNDERSIDE, FF_T,
                                   {"screed": FF_SCREED, "blinding": FF_BLIND}, EG)
    return {"plan_own_m2": a, "overlaps_m2": others, "ring_outer_m2": lp["ring_outer_plan_m2"],
            "AT_LEAST": lit, "reading": "p.9 note 1 minimum read as the FORMATION (blinding bottom) -1.50: the "
            "smallest admissible reading; the AT_LEAST holds for every reading of what the 1.50 measures",
            "S01_beside": s01, "upper": None,
            "missing": "lift pit depth 'as per lift manufacturer' (ST p.14; S14 / D-43 -> LIFT SUPPLIER)"}


# ---------------------------------------------------------------------------------------------------- annex ----

def annex():
    X = json.loads((RES / "agents_t695/STRAP_TRENCH_INPUT_T695.json").read_text())
    Z = json.loads((RES / "agents_t695/ZONES_T695.json").read_text())["annex"]
    cls = T695.piece_classes()
    led = {r["run"]: r for r in _csv("agents_t242/LEDGER_T242.csv")}
    annex_keys = {k.split("#")[0].replace("ARC:", "") for k, v in led.items() if v["part"] == "ANNEX"}
    parts_hi, rg_L, led_L, unbound = [], 0.0, 0.0, []
    for r in X["gb_pieces"]:
        cat, ds, dL = cls.get(r["piece"], ("UNKNOWN", None, None))
        if not cat.startswith("ANNEX"):
            if r["piece"].split("#")[0] not in annex_keys:
                continue
            unbound.append(r["piece"])      # an annex run's piece the T-350 r2 binding left UNBOUND: open, datum
            cat = "ANNEX_UNBOUND"
        rg_L += r["L_routeG_m"]
        a = r["strip_free_m2"]
        if cat == "ANNEX_INT_D":
            parts_hi.append((r["piece"], a, 0.0, max(ds) + BLINDING - ANNEX_TOP))
        else:
            parts_hi.append((r["piece"], a, 0.0, None))
    led_L = sum(float(v["L_m"]) for v in led.values() if v["part"] == "ANNEX" and v["component"].startswith("GB-"))
    assert rg_L >= led_L - 1e-6, (rg_L, led_L)
    out = {"low_m3": Z["at_least_m3"], "route_g_L_m": round(rg_L, 4), "ledger_L_m": round(led_L, 4),
           "unbound_pieces_taken": unbound}
    for tag, datum in (("R3_S01", S01_UNDERSIDE + UNDERLAY + BLINDING),
                       ("R3_S01-0.10", S01_UNDERSIDE + UNDERLAY + BLINDING - SENS),
                       ("R3_S01+0.10", S01_UNDERSIDE + UNDERLAY + BLINDING + SENS)):
        b = R2.trench_bounds(parts_hi, datum)
        out[tag] = {"datum_depth_m": round(datum, 6), "high_m3": b["high_m3"]}
    out["no_datum"] = R2.trench_bounds(parts_hi, None)["kind"]
    out["parts_high"] = [{"piece": p, "free_strip_m2": a, "max_depth_m": d} for p, a, _, d in parts_hi]
    return out


# --------------------------------------------------------------------------------------------------- wiring ----

def wiring(idx, zz, ff, ax):
    cen = {r["element_id"]: r for r in _csv("agents_t695/CENSUS_T695.csv")}
    lines = {x["element_id"]: x for x in idx["lines"] if x["item_code"].startswith("STR.EARTH.")}
    assert set(cen) == set(lines) and len(lines) == 20
    for k, x in lines.items():
        assert cen[k]["line_id"] == x["line_id"]
    m = lambda s: None if s in ("", None) else float(s)  # noqa: E731
    lo, hi = zz["EG"]["zone"]["fill_m3"]
    upd = {
        "EW-T350:B1-02:Z1-TRENCH-STRAPS": ("RANGE", None, 9.950299, 16.121241, "T-695 (Gate A MERGED): D-15 x S02",
                                           "D-15 blinding under straps; S02 F10 / F end"),
        "EW-T350:B1-02:Z1-TRENCH-INT-GB-MAIN-ZERO": ("ZERO_BY_GEOMETRY", 0.0, None, None,
                                                     "T-695: 13 runs, blinding bottom >= +0.45 > EG", ""),
        "EW-T350:B1-03:Z1-POOL": ("ZERO_BY_GEOMETRY", 0.0, None, None,
                                  "T-695: shell, layers and water space fill the neat cut; working space OQ-13 beside",
                                  ""),
        "EW-T350:B1-03:Z1-TRENCH-EXT-GB-MAIN": ("ZERO_BY_GEOMETRY", 0.0, None, None,
                                                "T-695: the neat cut is the blinding; working space OQ-13 beside", ""),
        "EW-T350:B1-02:Z1-TRENCH-ANNEX": ("RANGE", None, ax["low_m3"], ax["R3_S01"]["high_m3"],
                                          "T-700: low free strip x min depth (T-695); high free strip x the "
                                          "foundation formation datum R3 under S01 (ESTIMATED)",
                                          "D-33 / D-35 annex sections (S8); S01 founding level"),
        "EW-T350:B1-02:Z1-PIT-FF": ("AT_LEAST", None, ff["AT_LEAST"]["excavation_m3"], None,
                                    "T-700: own plan 20.70 m2 x formation >= 1.50 (p.9 note 1)", ff["missing"]),
        "EW-T350:B1-03:Z1-PIT-FF": ("AT_LEAST", None, ff["AT_LEAST"]["backfill_m3"], None,
                                    "T-700: (20.70 - ring 4.84) x raft-top depth >= 0.80", ff["missing"]),
        "EW-T350:B1-03:Z2": ("RANGE", None, lo, hi,
                             "T-700: panels x (underside - EG) + under-beam columns - blinding projections",
                             "GS-08 lobby extent (+0.30 / +1.00), GS-12 / GS-16 floored or open, D-33 / D-34 / D-35 "
                             "and court sections"),
        "EW-T350:B1-04:ALL": ("BLANK", None, None, None,
                              f"Z2 now bounded {lo} .. {hi} m3 compacted (T-700); the balance is R-T505-1 by dry mass",
                              " | ".join(E.MATERIAL_TESTS.values())),
    }
    rows = []
    for k in sorted(lines, key=lambda e: (e.split(":")[1], e)):
        c, x = cen[k], lines[k]
        fam = k.split(":")[1]
        state = "HELD" if x["class"] != "RELEASED" else "RELEASED"
        if k in upd:
            bound, val, l, h, basis, miss = upd[k]
            if bound != "BLANK" and not (bound == "RANGE" and x["held_low"] is not None):
                state = "PROPOSED_" + bound
        else:
            bound = c["bound"]
            val, l, h = m(c["value_m3"]), m(c["low_m3"]), m(c["high_m3"])
            basis, miss = (c["proposal"], "" if bound == "VALUE" else c["gap"])
        rows.append(R2.wiring_row(fam, x["line_id"], k, state, bound, val, l, h, basis, miss))
    # the strap backfill split T-695 proposed (a new line id is lane I's to mint)
    rows.append(R2.wiring_row("B1-03", "NEW (split of L-89b8e6beaea55fc0e4c9)", "EW-T350:B1-03:Z1-TRENCH-STRAPS",
                              "PROPOSED_RANGE", "RANGE", None, 6.437519, 10.952471,
                              "T-695 (Gate A MERGED): cut - strap concrete - blinding / underlay - GB below EG",
                              "D-15 blinding under straps; S02 F10 / F end"))
    return rows


def run(write=True):
    for rel in PINS:
        PINS[rel] = sha(rel)
    i69 = json.loads((RES / IDX69).read_text())
    i68 = json.loads((RES / IDX68).read_text())
    ew = lambda i: sorted((x["element_id"], x["line_id"], x["class"], x["measured_net"], x["held_low"],  # noqa: E731
                           x["held_high"]) for x in i["lines"] if x["item_code"].startswith("STR.EARTH."))
    assert ew(i69) == ew(i68), "earthworks lines moved between V3.0.68 and V3.0.69"
    gs = _gs_lines(i69)
    assert len(gs) == 26 and all(x["class"] == "RELEASED" for x in gs.values())
    gs_m3 = round(sum(x["measured_net"] for x in gs.values()), 6)
    inp = json.loads((RES / "agents_t700/ZONE_INPUT_T700.json").read_text())
    zz = z2(gs, inp["ground_sheet"])
    ff = lift_pit(inp["lift_pit"])
    ax = annex()
    rows = wiring(i69, zz, ff, ax)
    mat = E.material_account({"z2_fill_compacted_low": zz["EG"]["zone"]["fill_m3"][0],
                              "z2_fill_compacted_high": zz["EG"]["zone"]["fill_m3"][1]},
                             {k: None for k in E.MATERIAL_TESTS})
    summary = {"task": "T-700", "method": R2.VERSION, "candidate": i69["candidate_version"],
               "inputs_sha256": dict(PINS), "ground_slab_lines": len(gs), "ground_slab_m3": gs_m3,
               "z2": {k: zz[k] for k in ("EG", "EG-0.10", "EG+0.10", "layers")}, "lift_pit": ff, "annex": {
                   k: v for k, v in ax.items() if k != "parts_high"}, "material": mat,
               "wiring_counts": {c: sum(1 for r in rows if r["report_class"] == c) for c in ("CONFIRMED", "HELD")},
               "wiring_rows": len(rows)}
    if write:
        with open(HERE / "WIRING_T700.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(R2.WIRING_FIELDS), lineterminator="\n")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        (HERE / "ZONES_T700.json").write_text(json.dumps({"z2": zz, "lift_pit": ff, "annex": ax}, indent=1,
                                                         sort_keys=True) + "\n")
        (HERE / "summary_t700.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    return rows, summary


if __name__ == "__main__":
    rows, s = run()
    print(json.dumps({k: s[k] for k in ("ground_slab_m3", "z2", "lift_pit", "annex", "wiring_counts")}, indent=1))
