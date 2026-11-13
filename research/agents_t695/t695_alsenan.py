"""T-695 on the development villa: B1 earthworks census of the candidate of record and the zones the drawings
measure now (values only; no drawing content). Inputs, each pinned by sha256:

  research/agents_t672/out/LINE_INDEX_V3_0_68.json  candidate of record ARCH_TAKEOFF_V3.0.68 (lines d1de50cb)
  research/agents_t695/STRAP_TRENCH_INPUT_T695.json own read of 'ST7757 dxf.dxf' (t695_extract.py)
  research/agents_t350r2/BEAM_OVER_PITS_T350R2.csv  merged T-350 r2 (piece -> run, class)
  research/agents_t242/LEDGER_T242.csv              merged T-242 (interior runs: titles, D-33)
  research/agents_t350r2/FILL_T350R2.csv            merged T-350 r2 (footprints / layers of the valued zones)

    python3 -I research/agents_t695/t695_alsenan.py   -> CENSUS_T695.csv, ZONES_T695.json, summary_t695.json
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
import earthworks_census_v1 as E  # noqa: E402

PINS = {
    "agents_t672/out/LINE_INDEX_V3_0_68.json": None,
    "agents_t695/STRAP_TRENCH_INPUT_T695.json": None,
    "agents_t350r2/BEAM_OVER_PITS_T350R2.csv": None,
    "agents_t242/LEDGER_T242.csv": None,
    "agents_t350r2/FILL_T350R2.csv": None,
}
CANDIDATE = "ARCH_TAKEOFF_V3.0.68"
LINES_SHA = "d1de50cb0a58919e0860ca46cbd5170baf55ac9b66f55978b988214aef95bf94"

EG = 0.0
S01_UNDERSIDE = 1.50          # S01 ESTIMATED (owner-accepted RFI re-review 2026-11-02): footing underside -1.50
UNDERLAY, BLINDING = 0.07, 0.10
SENS = 0.10                   # S01 sensitivity
LIFT = 0.15                   # owner 2026-11-02 18:00, OWNER-PROVISIONAL
# p.10 strap schedule (T-356 s.1, merged): breadth x depth; soffit flush with the footing soffits (T-230, 5 / 5 ends)
STRAP_D = {"SB1": 0.50, "SB2": 0.50, "SB3": 0.40}
MAIN_TOP, ANNEX_TOP = 0.95, 0.25   # p.13 'Ground Floor slab level' (T-214 b 0.05 under +1.00); annex (T-230 / T-320)
DEPTH_BY_TITLE = {"GB-LT2_5M": 0.30, "GB-LT5M": 0.40, "GB-GT5M": 0.60}


def sha(rel):
    return hashlib.sha256((RES / rel).read_bytes()).hexdigest()


def _csv(rel):
    with open(RES / rel, newline="") as f:
        return list(csv.DictReader(f))


# ------------------------------------------------------------------------------------------------ the zones ----

def piece_classes():
    """route-G piece -> (category, D range) by the merged T-350 r2 binding and the T-242 ledger"""
    t242 = {r["run"]: r for r in _csv("agents_t242/LEDGER_T242.csv")}
    out = {}
    for r in _csv("agents_t350r2/BEAM_OVER_PITS_T350R2.csv"):
        comp, run = r["component"], r["run"]
        if not comp:
            out[r["piece"]] = ("UNBOUND", None, None)
            continue
        led = t242.get(run, {})
        titles = [t for t in (led.get("titles") or r["titles"] or "").split("+") if t in DEPTH_BY_TITLE]
        ds = sorted({DEPTH_BY_TITLE[t] for t in titles}) or None
        d33 = "D-33" in (led.get("reasons") or r["reasons"] or "")
        if comp.startswith("GB-EXTERIOR MAIN"):
            cat = "MAIN_EXT"
        elif comp.startswith("GB-EXTERIOR ANNEX"):
            cat = "ANNEX_EXT_D35"
        elif comp.startswith("GB-INTERIOR MAIN"):
            cat = "MAIN_INT_D33" if d33 else "MAIN_INT_D"
        elif comp.startswith("GB-INTERIOR ANNEX"):
            cat = "ANNEX_INT_D33" if d33 else "ANNEX_INT_D"
        else:
            cat = "OTHER"
        dL = float(r["dL_m"]) if r["dL_m"] not in ("", None) else None
        out[r["piece"]] = (cat, ds, dL)
    return out


def interior_main_zero():
    """Z1-TRENCH-INT-GB-MAIN-ZERO: the 13 main interior runs with a printed class (T-242, no D-33)."""
    runs = [r for r in _csv("agents_t242/LEDGER_T242.csv")
            if r["component"] == "GB-INTERIOR" and r["part"] == "MAIN" and "D-33" not in r["reasons"]]
    dmax = max(DEPTH_BY_TITLE[t] for r in runs for t in r["titles"].split("+") if t in DEPTH_BY_TITLE)
    z, bottom, thr = E.zero_by_geometry(MAIN_TOP, dmax, BLINDING, EG)
    ev = json.loads((RES / "agents_t695/STRAP_TRENCH_INPUT_T695.json").read_text())["gf_drop_evidence"]
    sunken_on_gb = sum(v for k, v in ev["hatches"].items() if k.startswith("GROUND_BEAMS_PLAN|S-HAT.BAT|ANSI31"))
    sunken_else = sum(v for k, v in ev["hatches"].items() if k.startswith("OTHER_SHEETS|S-HAT.BAT|ANSI31"))
    return {"runs": len(runs), "D_max_m": dmax, "top_m": MAIN_TOP, "lowest_blinding_bottom_m": bottom,
            "wet_drop_margin_m": round(bottom - EG, 6), "zero": z, "d_star_m": thr,
            "evidence": {"sunken_hatches_on_ground_beam_plan": sunken_on_gb,
                         "sunken_hatches_on_other_sheets": sunken_else,
                         "ground_beam_plan_level_marks": ev["ground_beam_plan_level_marks"]}}


def strap_zone():
    """Z1-TRENCH-STRAPS: excavation / backfill per admissible scenario (S02 end at F10 / F x D-15 reading x the
    D-33 / D-34 sections of the annex beams over SB3), each computed alone; the envelope is the zone's range."""
    X = json.loads((RES / "agents_t695/STRAP_TRENCH_INPUT_T695.json").read_text())
    st = X["straps"]
    cls = piece_classes()
    plans = {
        "BOX": {m: (st[m]["concrete_plan_outside_zones_m2"], st[m]["side_strip_plan_outside_zones_m2"]) for m in st},
        "DRAWN": {m: (st[m]["concrete_plan_outside_zones_f10_drawn_m2"],
                      st[m]["side_strip_plan_outside_zones_f10_drawn_m2"]) for m in st},
    }
    # readings of D-15 (blinding under a strap printed nowhere) and of the strap's own formation
    readings = {
        "R1_NONE": {"wide": False, "blind": 0.0, "under": 0.0},          # as drawn: no blinding, soffit -1.50
        "R2_BLINDING": {"wide": True, "blind": BLINDING, "under": 0.0},  # T-356 'own layer': 0.10 at +-0.10
        "R3_FOOTING_CHAIN": {"wide": True, "blind": BLINDING, "under": UNDERLAY},  # footing chain continued
    }
    scen, detail = [], []
    for end, P in plans.items():
        for rn, R in readings.items():
            for dread in ("LOW", "HIGH"):
                per = {}
                exc_tot = disp_tot = net_tot = 0.0
                for m, (pb, pbp) in P.items():
                    plan = pbp if R["wide"] else pb
                    depth = S01_UNDERSIDE + R["blind"] + R["under"]
                    solids = {"strap": pb * STRAP_D[m], "blinding": (pbp if R["blind"] else 0.0) * R["blind"],
                              "underlay": pb * R["under"]}
                    netted = 0.0
                    stop_top = S01_UNDERSIDE - STRAP_D[m]           # EG -> strap top
                    for r in X["gb_pieces"]:
                        v = r["by_strap"].get(f"{m}|{end}")
                        if not v:
                            continue
                        so_b, so_bp, bo_b, bo_bp = v
                        so = so_bp if R["wide"] else so_b
                        bo = bo_bp if R["wide"] else bo_b
                        cat, ds, dL = cls[r["piece"]]
                        if cat == "MAIN_EXT":              # beam on N.G.: only its blinding cut (-0.10 .. 0) is shared
                            netted += so * BLINDING        # already carried by the valued EXT-GB-MAIN trench line
                        elif cat in ("MAIN_INT_D",):
                            assert E.zero_by_geometry(MAIN_TOP, max(ds), BLINDING)[0]
                        elif cat == "MAIN_INT_D33":
                            # loaded span, section not printed: wholly above EG while D <= 0.85; above the strap trench
                            # it can reach EG only for D > 0.85 (D-33): solid below EG 0 .. not bounded -> the
                            # HIGH end below caps it at the strap top (a deeper beam would rest on the strap)
                            if dread == "HIGH":
                                solids[f"gb {r['piece']}"] = so * BLINDING + bo * (stop_top - BLINDING)
                        elif cat == "ANNEX_INT_D":
                            d = min(ds) if dread == "LOW" else max(ds)
                            solids[f"gb {r['piece']}"] = so * BLINDING + bo * (d - ANNEX_TOP)
                        elif cat in ("ANNEX_INT_D33", "ANNEX_EXT_D35"):
                            solids[f"gb {r['piece']}"] = so * BLINDING + (bo * (stop_top - BLINDING)
                                                                          if dread == "HIGH" else 0.0)
                        else:
                            raise SystemExit(f"unclassified piece over a strap: {r['piece']} {cat}")
                    fill_depth = (S01_UNDERSIDE if R["wide"] else stop_top)   # deepest fill column in the zone
                    s = E.trench_scenario(f"{end}|{rn}|{dread}|{m}", plan, depth, solids, netted, fill_depth, LIFT)
                    per[m] = s
                    exc_tot += s["excavation_m3"]
                    disp_tot += s["displacement_m3"]
                    net_tot += netted
                tot = {"scenario": f"{end}|{rn}|{dread}", "excavation_m3": round(exc_tot, 6),
                       "backfill_m3": round(exc_tot - disp_tot, 6),
                       "compaction_footprint_m2": round(sum(s["plan_m2"] for s in per.values()), 6),
                       "layers": max(s["layers"] for s in per.values()), "netted_cut_m3": round(net_tot, 6)}
                scen.append(tot)
                detail.append({"scenario": tot["scenario"], "by_strap": per, "total": tot})
    # the sensitivity of S01 (+-0.10 on the footing underside) moves every scenario's cut by plan x 0.10
    env = E.envelope(scen)
    sens = {}
    for sgn, name in ((-1, "-0.10"), (1, "+0.10")):
        lo = min(s["excavation_m3"] + sgn * SENS * s["compaction_footprint_m2"] for s in scen)
        hi = max(s["excavation_m3"] + sgn * SENS * s["compaction_footprint_m2"] for s in scen)
        sens[name] = [round(lo, 6), round(hi, 6)]
    return {"scenarios": scen, "detail": detail, "envelope": env, "s01_sensitivity_excavation_m3": sens,
            "plans_m2": plans, "trench_union_BP_box_m2": X["trench_union_BP_m2"]}


def annex_at_least():
    """Z1-TRENCH-ANNEX: interior D-34 runs bounded, D-33 / D-35 only from below; parts over deeper zones excluded
    (pits, F10 / F, FF, pool, strap trench at its widest, boundary band)."""
    X = json.loads((RES / "agents_t695/STRAP_TRENCH_INPUT_T695.json").read_text())
    cls = piece_classes()
    lo_parts, hi_parts, unbounded, skipped = [], [], [], []
    for r in X["gb_pieces"]:
        cat, ds, dL = cls.get(r["piece"], ("UNKNOWN", None, None))
        if not cat.startswith("ANNEX"):
            continue
        if dL is None or abs(dL) > 0.001:
            skipped.append({"piece": r["piece"], "dL_m": dL, "why": "route-G piece and ledger run disagree: left out "
                            "of the lower bound (a smaller AT_LEAST stays valid)"})
            continue
        a = r["strip_free_m2"]
        if cat == "ANNEX_INT_D":
            lo_parts.append((r["piece"], a, min(ds) + BLINDING - ANNEX_TOP))
            hi_parts.append((r["piece"], a, max(ds) + BLINDING - ANNEX_TOP))
        else:      # D-33 / D-35: shallowest admissible reading = beam bottom at N.G., its 0.10 blinding below EG
            lo_parts.append((r["piece"], a, BLINDING))
            unbounded.append(r["piece"])
    lo = E.at_least_trench(lo_parts)
    return {"at_least_m3": lo["m3"], "upper": None if unbounded else E.at_least_trench(hi_parts)["m3"],
            "parts": [{"piece": p, "free_strip_m2": a, "min_depth_m": round(d, 6)} for p, a, d in lo_parts],
            "unbounded_pieces": unbounded, "skipped": skipped}


def int_main_d33():
    z, bottom, thr = E.zero_by_geometry(MAIN_TOP, 0.85, BLINDING, EG)
    return {"zero_if_D_at_most_m": round(MAIN_TOP - BLINDING - EG, 6), "check": z}


# ------------------------------------------------------------------------------------------------ the census ----

def register(zero, strap, annex):
    se = strap["envelope"]
    reg = {
        "EW-T350:B1-02:Z1-PITS-24": ("MEASURABLE_NOW", [], "", [],
            "keep VALUED 208.164757 (S01 ESTIMATED, T-350 r4); working space OQ-13 beside"),
        "EW-T350:B1-02:Z1-POOL": ("MEASURABLE_NOW", [], "", [], "keep VALUED 17.776576 (printed -1.50)"),
        "EW-T350:B1-02:Z1-TRENCH-EXT-GB-MAIN": ("MEASURABLE_NOW", ["DESIGNER"],
            "S06 / D-14 plot-line clip names the range 1.069269 .. 1.176467 (T-497 restated)", [],
            "keep BOUNDED; the strap trench nets its shared blinding cut (<= 0.003002 m3) so this line is unchanged"),
        "EW-T350:B1-02:Z1-PIT-F10F": ("DESIGNER", ["MEASURABLE_NOW"],
            "Q-31 C: F10 drawn outline vs schedule, RFI to the designer (S02 three scenarios 7.2645 .. 8.39175)", [],
            "keep BOUNDED"),
        "EW-T350:B1-02:Z1-PIT-FF": ("DESIGNER", [],
            "lift pit depth 'as per lift manufacturer' (ST p.14; S14 / D-43 -> LIFT SUPPLIER); raft plan 20.700 m2", [],
            "keep HELD BLANK"),
        "EW-T350:B1-02:Z1-TRENCH-INT-GB-MAIN-ZERO": ("MEASURABLE_NOW", [],
            "", [], (f"CALCULATED 0.000 (ZERO_BY_GEOMETRY): {zero['runs']} runs, top +{MAIN_TOP} (p.13 GF slab level), "
                     f"D <= {zero['D_max_m']} printed class, blinding bottom >= +{zero['lowest_blinding_bottom_m']}; "
                     f"the T-214 wet condition is discharged: the GB plan draws {zero['evidence']['sunken_hatches_on_ground_beam_plan']} "
                     f"sunken hatches ({zero['evidence']['sunken_hatches_on_other_sheets']} on the slab sheets) and "
                     f"prints only {', '.join(zero['evidence']['ground_beam_plan_level_marks'])}")),
        "EW-T350:B1-02:Z1-TRENCH-INT-GB-MAIN-D33": ("DESIGNER", [],
            "D-33 (S8): loaded spans have no section; the cut is 0 while D <= 0.85 m, not bounded above", [],
            "keep HELD BLANK; ZERO_IF D <= 0.85 beside"),
        "EW-T350:B1-02:Z1-TRENCH-ANNEX": ("DESIGNER", ["MEASURABLE_NOW"],
            "D-33 / D-35 (S8) annex sections: only a lower bound; interior D-34 runs bounded", [],
            f"keep HELD; AT_LEAST {annex['at_least_m3']} m3 beside (free strips x minimum depth)"),
        "EW-T350:B1-02:Z1-TRENCH-COURT": ("DESIGNER", [],
            "court ground beams: no court section (T-253 candidates 0.30 / 0.40 / 0.95; S8)", [], "keep HELD BLANK"),
        "EW-T350:B1-02:Z1-TRENCH-STRAPS": ("MEASURABLE_NOW", ["DESIGNER"],
            "D-15 (S15) blinding under straps and S02 (F10 / F end) name the range", [],
            (f"BOUNDED {se['excavation_m3'][0]} .. {se['excavation_m3'][1]} m3 (S01 ESTIMATED)")),
        "EW-T350:B1-02:Z1-TRENCH-BOUNDARY": ("DESIGNER", ["OWNER_RULE"],
            "S2 / Q-28 A PROVISIONAL: the band's section and its depth to the foundation level are not printed", [],
            "keep HELD BLANK"),
        "EW-T350:B1-02:Z1-LOWER-GB-ROW": ("DESIGNER", ["MEASURABLE_NOW"],
            "S1 / Q-21 C founding level fixed on site: under S01 not required (2.45 <= 2.50 m), at +0.10 required "
            "and drawn on no plan (unbounded)", [], "keep HELD BLANK; S01 reading 0.000 beside (not a value)"),
        "EW-T350:B1-03:Z1-PITS-24": ("MEASURABLE_NOW", ["DESIGNER"],
            "D-33 / D-35 sections over the pits name the range (T-484, 6 / 8 verified)", [], "keep BOUNDED"),
        "EW-T350:B1-03:Z1-POOL": ("MEASURABLE_NOW", ["OWNER_RULE"],
            "neat backfill 0.000 calculated (shell, layers, water space fill the envelope); the blinding projection "
            "(S23-like, not printed) and working space (OQ-13, no method) are the only fill", [],
            "propose CALCULATED 0.000 neat, consistent with the VALUED neat excavation; working space beside"),
        "EW-T350:B1-03:Z1-TRENCH-EXT-GB-MAIN": ("MEASURABLE_NOW", ["OWNER_RULE"],
            "neat backfill 0.000 calculated (the cut is the blinding); working space OQ-13", [],
            "propose CALCULATED 0.000 neat, consistent with the BOUNDED neat excavation"),
        "EW-T350:B1-03:Z1-OTHER-TRENCHES": ("DESIGNER", ["MEASURABLE_NOW"],
            "annex D-33 / D-35, court section, boundary (S8, S2); the strap part is now bounded (split proposed)", [],
            f"split: a B1-03 STRAPS line BOUNDED {se['backfill_m3'][0]} .. {se['backfill_m3'][1]} m3; the rest HELD"),
        "EW-T350:B1-03:Z1-PIT-F10F": ("DESIGNER", ["MEASURABLE_NOW"],
            "Q-31 C (S02 scenarios 4.5951 .. 6.2912 before the C10 / C necks)", [], "keep HELD"),
        "EW-T350:B1-03:Z1-PIT-FF": ("DESIGNER", [], "lift pit depth (S14 / D-43 LIFT SUPPLIER)", [], "keep HELD"),
        "EW-T350:B1-03:Z2": ("DESIGNER", ["MEASURABLE_NOW"],
            "D-33 / D-34 beam solids above EG and the GF slab soffit; the wet-floor condition is discharged by the "
            "same GB-plan evidence as the ZERO zone (no GF drop drawn); the enclosed plan is measurable (not done here)",
            [], "keep HELD; next row: Z2 enclosed plan x (soffit - EG) - solids, D-33 bounded"),
        "EW-T350:B1-04:ALL": ("NEEDS_TEST", ["DESIGNER"],
            "dry-mass balance R-T505-1: no measured density; Z2 draw; held zones", [
                E.MATERIAL_TESTS[k] for k in E.MATERIAL_TESTS], "keep HELD"),
    }
    return {k: {"cause": c, "secondary": s, "gap": g, "tests": t, "proposal": p} for k, (c, s, g, t, p) in reg.items()}


def run(write=True):
    for rel in PINS:
        PINS[rel] = sha(rel)
    idx = json.loads((RES / "agents_t672/out/LINE_INDEX_V3_0_68.json").read_text())
    assert idx["candidate_version"] == CANDIDATE and idx["inputs"]["lines"] == LINES_SHA
    zero = interior_main_zero()
    assert zero["zero"]
    strap = strap_zone()
    annex = annex_at_least()
    d33 = int_main_d33()
    reg = register(zero, strap, annex)
    rows = E.census(idx["lines"], reg)
    mat = E.material_account({"excavation_in_situ_valued": 208.164757 + 17.776576},
                             {k: None for k in E.MATERIAL_TESTS})
    fill = {r["row_id"]: r for r in _csv("agents_t350r2/FILL_T350R2.csv")}
    summary = {
        "task": "T-695", "method": E.VERSION, "candidate": CANDIDATE, "lines_sha256": LINES_SHA,
        "inputs_sha256": dict(PINS), "b1_lines": len(rows), "census_counts": E.census_counts(rows),
        "zero_zone": zero, "int_main_d33": d33,
        "straps": {"excavation_m3": strap["envelope"]["excavation_m3"],
                   "excavation_by": strap["envelope"]["excavation_m3_by"],
                   "backfill_m3": strap["envelope"]["backfill_m3"], "backfill_by": strap["envelope"]["backfill_m3_by"],
                   "compaction_footprint_m2": strap["envelope"]["compaction_footprint_m2"],
                   "layers": strap["envelope"]["layers"], "s01_sensitivity_excavation_m3":
                       strap["s01_sensitivity_excavation_m3"], "scenarios": strap["scenarios"]},
        "annex": annex, "material": mat,
        "footprints_layers_merged": {
            "pits": "compaction 124.649555 m2, 11 layers (T-350 r2)",
            "pool": fill["B1-02 EXCAVATION|Z1-POOL (pool envelope to the printed -1.50)"]["unit_extra"],
            "ext_gb_trench": fill["B1-02 EXCAVATION|Z1-TRENCH-EXT-GB-MAIN (17 runs, cut for the blinding only)"][
                "unit_extra"]},
    }
    if write:
        with open(HERE / "CENSUS_T695.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["family", "code", "line_id", "element_id", "zone", "state", "bound",
                                              "value_m3", "low_m3", "high_m3", "cause", "secondary", "gap", "tests",
                                              "proposal"], lineterminator="\n")
            w.writeheader()
            for r in rows:
                w.writerow({**r, "secondary": " ".join(r["secondary"]), "tests": " | ".join(r["tests"])})
        (HERE / "ZONES_T695.json").write_text(json.dumps({"straps": strap, "annex": annex, "zero": zero},
                                                         indent=1, sort_keys=True) + "\n")
        (HERE / "summary_t695.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    return rows, summary


if __name__ == "__main__":
    rows, s = run()
    print(json.dumps({k: s[k] for k in ("b1_lines", "census_counts", "zero_zone", "straps", "annex")}, indent=1)[:6000])
