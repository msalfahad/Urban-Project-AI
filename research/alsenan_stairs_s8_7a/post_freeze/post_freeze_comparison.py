"""S8.7A post-freeze comparison: the frozen riser / finish correction layer against the earlier figures, after the
freeze.

    python3 -I research/alsenan_stairs_s8_7a/post_freeze/post_freeze_comparison.py

Reads the frozen S8.7A layer and the frozen S8.7 package (both verified before and after; never written), then the
earlier figures that S8.7A did not read before its freeze:
  * the old Urban V3b stair lines (C-STAIR, R-STAIRS-GF, S-GOING, S-RAIL, S-TREAD, S-RISER, S-NOSING) and its
    STAIRS bar population; V3b's code method is reproduced here from its stated inputs so that the riser count it
    assumed can be set against the drawn counts;
  * the PRE-S8 stair columns (02 CONCRETE_QUANTITY_STATE, 03 / 04 coverage, 06 CONCRETE_STATES, 07 interface);
  * the R5 architectural stair register (its riser method);
  * the S8.7 post-freeze sensitivity totals.
Every difference is classified (NO_DIFFERENCE, AUTHORITY, SCOPE, METHOD, MISSED_OBJECT, NOT_COMPARABLE) and
explained. Nothing here changes a frozen quantity, selects a riser count or releases anything.
"""

from __future__ import annotations

import csv
import io
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import delta_release as DR  # noqa: E402

R = ROOT / "research"
V3B_LINES = ROOT / "tests/alsenan/registers_v3b/BOQ_LINES_V3B.json"
V3B_POP = ROOT / "tests/alsenan/registers_v3b/REBAR_POPULATION_REGISTER.json"
R5_STAIRS = R / "alsenan_arch_truth_05/registers/STAIR_ARCHITECTURAL_REGISTER.json"
PRE_S8 = R / "pre_s8_structural_completeness"
S87 = R / "alsenan_stairs_s8_7"
S87_PF = S87 / "post_freeze/02_S8_7_CONDITIONAL_TOTALS.csv"
MANIFEST = PKG / "15_S8_7A_CORRECTION_MANIFEST.json"
S87_MANIFEST = S87 / "17_S8_7_FREEZE_MANIFEST.json"
OUT = ["01_POST_FREEZE_COMPARISON.csv", "02_V3B_METHOD_REPRODUCTION.csv", "03_POST_FREEZE_SUMMARY.json",
       "00_POST_FREEZE_README.md"]
STAIR_CODES = re.compile(r"STAIR|TREAD|RISER|NOSING|GOING|S-RAIL")

# V3b B03 stair method, as stated on its C-STAIR line and in its builder (re-derived here, not imported)
V3B_RISE_M = {"A1": 4.50, "A2": 4.20}
V3B_R_MAX, V3B_R_MIN, V3B_G, V3B_W, V3B_T = 0.175, 0.15, 0.30, 1.15, 0.16
V3B_LANDINGS = {"A1": 2, "A2": 1}


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _r(v, nd=6):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        s = f"{v:.6f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(name, rows):
    buf = io.StringIO()
    keys = list(dict.fromkeys(k for r in rows for k in r))
    w = csv.DictWriter(buf, fieldnames=keys, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in keys})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def v3b_method():
    """V3b's code method per storey: n = ceil(H / 0.175), one continuous slope of (n - 1) goings, W 1.15, waist
    0.16, W x W landings (two on GF -> 1F, one on 1F -> 2F)."""
    out = []
    for run, H in V3B_RISE_M.items():
        n = math.ceil(H / V3B_R_MAX - 1e-9)
        n_hi = math.floor(H / V3B_R_MIN)
        R_ = H / n
        slope = math.hypot((n - 1) * V3B_G, H)
        waist = slope * V3B_W * V3B_T
        steps = n * R_ * V3B_G / 2 * V3B_W
        land = V3B_W * V3B_W * V3B_LANDINGS[run] * V3B_T
        out.append({"STOREY_RUN": run, "H_M": H, "V3B_RISERS": n, "V3B_RISERS_HIGH": n_hi, "V3B_RISER_MM": _r(R_ * 1000),
                    "V3B_TREADS": n - 1, "V3B_SLOPE_M": _r(slope), "V3B_WAIST_M3": _r(waist), "V3B_STEPS_M3": _r(steps),
                    "V3B_LANDINGS": V3B_LANDINGS[run], "V3B_LANDING_M3": _r(land),
                    "V3B_CONCRETE_M3": _r(waist + steps + land, 4),
                    "V3B_RISER_FINISH_M2": _r(n * R_ * V3B_W, 3), "V3B_NOSING_LM": _r((n - 1) * V3B_W, 3),
                    "V3B_HANDRAIL_LM": _r(slope + V3B_W, 3)})
    return out


def s87a_whole(conc):
    tot = {}
    for r in conc:
        if r["ELEMENT_ID"].startswith("TOTAL (whole stair"):
            tot[r["SCENARIO"]] = float(r["CONCRETE_M3"])
    return tot


def compare():
    pre = DR.verify_frozen(MANIFEST, ROOT)
    pre87 = DR.verify_frozen(S87_MANIFEST, ROOT)
    s = json.loads((PKG / "12_RELEASE_SUMMARY.json").read_text(encoding="utf-8"))
    conc = _rows(PKG / "06_CONCRETE_QUANTITY_SCENARIOS.csv")
    s87_rel = json.loads((S87 / "16_S8_7_SUMMARY.json").read_text(encoding="utf-8"))["released"]
    whole = s87a_whole(conc)
    winder = {r["SCENARIO"]: float(r["CONCRETE_M3"]) for r in conc
              if r["KIND"] == "WINDER TURN" and r["CONCRETE_M3"]}
    counts = s["counts"]
    v3 = v3b_method()
    lines = [l for l in json.loads(V3B_LINES.read_text(encoding="utf-8"))["lines"] if STAIR_CODES.search(l["code"])]
    by = {l["code"]: l for l in lines}
    v3b_c = by["C-STAIR"]["release"]["commercial"]
    v3b_sum = _r(math.fsum(x["V3B_CONCRETE_M3"] for x in v3), 4)

    rep = []
    drawn = {"A1": {"GFRS": counts["A1:STRUCTURAL GF roof sheet (GFRS)"], "ARCH-GF": counts["A1:ARCHITECTURAL GF plan"]},
             "A2": {"FFRS": counts["A2:STRUCTURAL 1F roof sheet (FFRS)"], "ARCH-1F": counts["A2:ARCHITECTURAL 1F plan"],
                    "ARCH-2F": counts["A2:ARCHITECTURAL 2F plan (repeated view)"]}}
    owner = {"A1": {"A": counts["A1:OWNER SCENARIO A"], "B": counts["A1:OWNER SCENARIO B"]},
             "A2": {"A": counts["A2:OWNER SCENARIO A"], "B": counts["A2:OWNER SCENARIO B"]}}
    sc = {"A1": ("A1-ARCH_GF-25", "A1-OWNER_A-28"), "A2": ("A2-FFRS-24", "A2-OWNER_A-27")}
    for x in v3:
        run = x["STOREY_RUN"]
        lo, hi = sorted(whole[k] for k in sc[run])
        rep.append({**x, "DRAWN_COUNTS": drawn[run], "OWNER_SCENARIOS": owner[run],
                    "V3B_COUNT_DRAWN_ON_ANY_VIEW": x["V3B_RISERS"] in drawn[run].values(),
                    "S8_7A_WIDTH_M": 1.20, "S8_7A_WHOLE_STAIR_M3_RANGE": [_r(lo), _r(hi)],
                    "S8_7A_SCENARIOS": list(sc[run])})
    _csv(OUT[1], rep)

    rows = []
    main_lo = _r(sum(min(whole[k] for k in sc[r]) for r in sc))
    main_hi = _r(sum(max(whole[k] for k in sc[r]) for r in sc))
    c_whole = _r(whole["C-DRAWN-28"])
    c = by["C-STAIR"]
    rows.append({"REFERENCE": f"V3b {c['line_id']} C-STAIR ({c['level']})", "UNIT": "m3",
                 "REFERENCE_VALUE": f"technical {c['release']['technical']['class']}; commercial {v3b_c['class']} "
                                    f"{v3b_c['qty']} ({v3b_c['low']} - {v3b_c['high']})",
                 "REFERENCE_METHOD": v3b_c["method"],
                 "S8_7A": f"method reproduced here: {v3b_sum} m3 (= {' + '.join(str(x['V3B_CONCRETE_M3']) for x in v3)}); "
                          f"S8.7A main stair whole-stair scenarios {main_lo} - {main_hi} m3 (waist 160 sensitivity, "
                          f"never released); light-well stair {c_whole} m3",
                 "CLASS": "METHOD + SCOPE",
                 "EXPLANATION": "V3b's figure falls inside the S8.7A main-stair range, but by compensating errors: "
                                "(a) one continuous slope per storey instead of two flights and a winder turn; "
                                "(b) width 1.15 m (drawn 1.20); (c) the half-turn as flat W x W quarters, two on "
                                "GF -> 1F (drawn: one flat quarter and one winder quarter) and one on 1F -> 2F "
                                "(drawn: two quarters); (d) a riser count from ceil(H / 0.175), not "
                                "from a drawing. It also leaves out the light-well (round) stair entirely. Agreement "
                                "of the total is not agreement of the method."})
    for x in rep:
        run = x["STOREY_RUN"]
        rows.append({"REFERENCE": f"V3b C-STAIR riser count {run} (H {x['H_M']} m)", "UNIT": "risers",
                     "REFERENCE_VALUE": f"{x['V3B_RISERS']} ({x['V3B_RISER_MM']} mm); band high {x['V3B_RISERS_HIGH']}",
                     "REFERENCE_METHOD": "ceil(H / 0.175): the 2R + G comfort band, section A-A not machine-counted",
                     "S8_7A": f"drawn {x['DRAWN_COUNTS']}; owner scenarios {x['OWNER_SCENARIOS']}",
                     "CLASS": "NO_DIFFERENCE (count only)" if x["V3B_COUNT_DRAWN_ON_ANY_VIEW"] else "METHOD",
                     "EXPLANATION": ("24 equals the structural 1F roof sheet and the repeated 2F view, which omit the "
                                     "three radial winder risers; the match is the 175 mm cap meeting 4.20 m exactly "
                                     "(4.20 / 0.175 = 24), not a count. The architectural 1F plan draws 27.")
                     if x["V3B_COUNT_DRAWN_ON_ANY_VIEW"] else
                     ("26 is drawn on no view (structural 28, architectural 25) and is neither owner scenario. "
                      "It is the smallest count under the 175 mm cap.")})
    for code in ("S-RISER", "S-TREAD", "S-NOSING", "S-RAIL"):
        l = by[code]
        com = l["release"]["commercial"]
        if code == "S-RISER":
            s87a = ("uniform finished risers make n x h = H for any count, so the riser face area of the straight "
                    "flights does not depend on which scenario is confirmed; the radial winder risers are longer than "
                    "the flight width and V3b does not see them")
            cls = "METHOD"
        elif code == "S-NOSING":
            s87a = (f"V3b treads {sum(x['V3B_TREADS'] for x in v3)} (= 25 + 23). S8.7A tread counts follow the "
                    f"confirmed riser count; every scenario changes this line")
            cls = "METHOD"
        else:
            s87a = "finish areas and handrail lengths are not S8.7A scope; they follow the confirmed count"
            cls = "NOT_COMPARABLE"
        rows.append({"REFERENCE": f"V3b {l['line_id']} {code} ({l['level']})", "UNIT": l["unit"],
                     "REFERENCE_VALUE": f"technical {l['release']['technical']['class']}; commercial {com['class']} "
                                        f"{com['qty']}",
                     "REFERENCE_METHOD": com.get("method") or l.get("formula"), "S8_7A": s87a, "CLASS": cls,
                     "EXPLANATION": "V3b's finish lines rest on the same ceil(H / 0.175) count, width 1.15 and one "
                                    "slope per storey; reproduced exactly in 02"})
    g = by["S-GOING"]
    rows.append({"REFERENCE": f"V3b {g['line_id']} S-GOING", "UNIT": "m", "REFERENCE_VALUE": g["qty"],
                 "REFERENCE_METHOD": g["formula"],
                 "S8_7A": "300 mm on every flight of the primary views; the architectural GF plan's upper treads of "
                          "the first flight are irregular (325 / 250 / 316.7) and reported, not corrected",
                 "CLASS": "NO_DIFFERENCE", "EXPLANATION": "same going; the irregular goings are a drawing fact"})
    rb = by["R-STAIRS-GF"]
    pop = [r for r in json.loads(V3B_POP.read_text(encoding="utf-8"))["rows"] if r.get("population") == "STAIRS"]
    rows.append({"REFERENCE": f"V3b {rb['line_id']} R-STAIRS-GF + STAIRS population", "UNIT": "kg",
                 "REFERENCE_VALUE": f"{rb['release']['technical']['class']}; population "
                                    f"{[(r['classes'], r['technical_kg']) for r in pop]}",
                 "REFERENCE_METHOD": rb["formula"],
                 "S8_7A": f"no new bars; S8.7's {s87_rel['kg']} kg reproduced exactly; only 8Ø16/m is explicit, every "
                          f"other p.16 family typical-only and blocked",
                 "CLASS": "AUTHORITY", "EXPLANATION": "V3b bound no stair callout; S8.7 bound the plan callouts and "
                                                      "S8.7A releases nothing further"})
    census = [r for r in _rows(PRE_S8 / "02_STRUCTURAL_ELEMENT_CENSUS.csv")
              if r["ELEMENT_FAMILY"].startswith("STAIR") or r["ELEMENT_ID"].startswith("SPC-STAIR-SP")]
    miss = sorted({r["MISSING_INFORMATION"] for r in census if r["ELEMENT_ID"].startswith("SPC-STAIR-SP")})
    rows.append({"REFERENCE": f"PRE-S8 02 CONCRETE_QUANTITY_STATE + MISSING_INFORMATION ({len(census)} stair rows)",
                 "UNIT": "m3", "REFERENCE_VALUE": {st[:90]: sum(1 for r in census if r["CONCRETE_QUANTITY_STATE"] == st)
                                            for st in sorted({r["CONCRETE_QUANTITY_STATE"] for r in census})},
                 "REFERENCE_METHOD": f"missing: {miss}",
                 "S8_7A": "riser height: in source conflict per storey (counts recorded per view); landing levels: "
                          "scheduled per scenario; waist: still not established",
                 "CLASS": "AUTHORITY", "EXPLANATION": "the three missing items are the three S8.7A questions; one is "
                                                      "narrowed to a choice between drawn counts, none is closed"})
    cov = [r for r in _rows(PRE_S8 / "03_CONCRETE_COVERAGE_MATRIX.csv") if r["FAMILY"] == "STAIR_AND_LANDING"]
    rows.append({"REFERENCE": "PRE-S8 03 concrete coverage (STAIR_AND_LANDING)", "UNIT": "m3",
                 "REFERENCE_VALUE": {"URBAN_LINES": sorted({r["URBAN_LINES"] for r in cov}),
                                     "V3B_COMMERCIAL_SHARED": sorted({r["V3B_LINE_COMMERCIAL_PROVISIONAL_M3_SHARED"]
                                                                      for r in cov}),
                                     "CR": sorted({r["CR_VERIFIED_LOWER_BEST_M3"] for r in cov})},
                 "REFERENCE_METHOD": "one V3b line shared by every stair floor row; contractor register empty",
                 "S8_7A": "no contractor-register stair figure exists to compare", "CLASS": "AUTHORITY",
                 "EXPLANATION": "the only earlier figure is V3b's code-method one"})
    rc = [r for r in _rows(PRE_S8 / "04_REBAR_COVERAGE_MATRIX.csv") if r["FAMILY"].startswith("STAIR")]
    rows.append({"REFERENCE": "PRE-S8 04 rebar coverage (stair families)", "UNIT": "kg",
                 "REFERENCE_VALUE": {r["COMPONENT"]: r["COVERAGE"] for r in rc},
                 "REFERENCE_METHOD": "P16 stair bars unquantified; rule P16-STAIR a rule reference only",
                 "S8_7A": "p.16 families typical-only and blocked; the stair-beam rows stay with S6.1",
                 "CLASS": "NO_DIFFERENCE", "EXPLANATION": "same state: a typical detail is not a project quantity"})
    cand = [r for r in _rows(PRE_S8 / "06_S8_CANDIDATE_REGISTER.csv") if r["S8_FAMILY"] == "STAIR_AND_LANDING"]
    rows.append({"REFERENCE": "PRE-S8 06 CONCRETE_STATES (stair family)", "UNIT": "m3",
                 "REFERENCE_VALUE": cand[0]["CONCRETE_STATES"], "REFERENCE_METHOD": cand[0]["READINESS"],
                 "S8_7A": "not read before the freeze", "CLASS": "AUTHORITY", "EXPLANATION": "same V3b figure"})
    itf = next(r for r in _rows(PRE_S8 / "07_INTERFACE_DOUBLE_COUNT_AUDIT.csv") if r["INTERFACE"] == "SLAB -> STAIR")
    s7row = next(r for r in _rows(PKG / "08_BEAM_AND_S6_S7_OWNERSHIP_RECONCILIATION.csv")
                 if r["ELEMENT_ID"] == "S7 stair-adjacent supports")
    m = re.search(r"([\d.]+) kg", itf["BARS_OWNED"])
    m2 = re.search(r"([\d.]+) kg", s7row["S8_7A"])
    same = bool(m and m2 and abs(float(m.group(1)) - float(m2.group(1))) < 0.05)
    rows.append({"REFERENCE": "PRE-S8 07 SLAB -> STAIR interface", "UNIT": "kg",
                 "REFERENCE_VALUE": f"CONCRETE: {itf['CONCRETE']}; BARS_OWNED: {itf['BARS_OWNED']}",
                 "REFERENCE_METHOD": itf["STATE"], "S8_7A": s7row["S8_7A"][:160],
                 "CLASS": "NO_DIFFERENCE" if same else "METHOD",
                 "EXPLANATION": "the S7 top extensions at the stair-adjacent supports agree (PRE-S8 rounds to 0.1 kg); "
                                "S8.7A releases no top bar, so nothing repeats S7's extension"})
    r5 = json.loads(R5_STAIRS.read_text(encoding="utf-8"))
    d_runs = [x for x in r5["runs"] if x["flight_width_m"] == 2.8]
    rows.append({"REFERENCE": "R5 stair register riser method", "UNIT": "risers",
                 "REFERENCE_VALUE": f"{len(r5['runs'])} runs; risers = tread lines + 1; riser height "
                                    f"{r5['riser_height']['state']} ({r5['riser_height']['why']})",
                 "REFERENCE_METHOD": "tread lines counted per drafting run; cut / overhead linetypes not summed",
                 "S8_7A": f"a drawn line is a riser (nosing + riser face pair = one); example: the 2.80 m wide run of "
                          f"{d_runs[0]['tread_lines']} lines is the entrance steps D-F1, R5 "
                          f"{d_runs[0]['riser_count_candidate']} risers, S8.7A {counts['D:ARCH-GF']} "
                          f"({_r(850 / counts['D:ARCH-GF'])} mm over 0.85 m)",
                 "CLASS": "METHOD",
                 "EXPLANATION": "R5's + 1 assumes the arrival riser is undrawn; on these plans the landing-edge "
                                "lines are drawn and are risers. R5 never closes a storey total."})
    rows.append({"REFERENCE": "R5 radial lines", "UNIT": "risers", "REFERENCE_VALUE": "none found",
                 "REFERENCE_METHOD": "straight sets only",
                 "S8_7A": "three radial winder risers per main-stair turn (GFRS, ARCH-GF, ARCH-1F) and 12 curved "
                          "light-well risers",
                 "CLASS": "MISSED_OBJECT",
                 "EXPLANATION": "the same omission separates 24 from 27 on 1F -> 2F: the structural 1F roof sheet "
                                "and the 2F view do not draw the radial lines"})
    pf = {r["STAIR_ID"]: r for r in _rows(S87_PF)}
    a_no_w_lo = _r(sum(min(whole[k] - winder.get(k, 0.0) for k in sc[r]) for r in sc))
    a_no_w_hi = _r(sum(max(whole[k] - winder.get(k, 0.0) for k in sc[r]) for r in sc))
    rows.append({"REFERENCE": "S8.7 post-freeze ST-A released + sensitivity", "UNIT": "m3",
                 "REFERENCE_VALUE": f"{pf['ST-A']['RELEASED_PLUS_SENSITIVITY_LOW']} - "
                                    f"{pf['ST-A']['RELEASED_PLUS_SENSITIVITY_HIGH']} (not computed "
                                    f"{pf['ST-A']['NOT_COMPUTED']})",
                 "REFERENCE_METHOD": "S8.7 sensitivity over the computable flights; winder turns not computed",
                 "S8_7A": f"whole stair {main_lo} - {main_hi}; without the winder turns {a_no_w_lo} - {a_no_w_hi}",
                 "CLASS": "METHOD",
                 "EXPLANATION": f"without the turns the lower ends agree within "
                                f"{_r(abs(a_no_w_lo - float(pf['ST-A']['RELEASED_PLUS_SENSITIVITY_LOW'])))} m3; "
                                f"S8.7A adds the winder turns (plane-equivalent approximation) and evaluates every "
                                f"drawn count per view, so its upper end is the 28-riser GF -> 1F arrangement. Both "
                                f"are context, neither is a quantity"})
    rows.append({"REFERENCE": "S8.7 post-freeze ST-C released + sensitivity", "UNIT": "m3",
                 "REFERENCE_VALUE": f"{pf['ST-C']['RELEASED_PLUS_SENSITIVITY_LOW']} (not computed "
                                    f"{pf['ST-C']['NOT_COMPUTED']})",
                 "REFERENCE_METHOD": "S8.7 left the curved flight uncomputed",
                 "S8_7A": f"whole stair {c_whole} with the curved flight C-F1 "
                          f"{_r(next(float(r['CONCRETE_M3']) for r in conc if r['ELEMENT_ID'] == 'C-F1'))}",
                 "CLASS": "METHOD", "EXPLANATION": "S8.7A computes the curved flight as a sensitivity; not released"})
    _csv(OUT[0], rows)
    summ = {"round": "S8_7A_POST_FREEZE", "frozen_manifest_sha256": pre["manifest_sha256"],
            "s8_7_manifest_sha256": pre87["manifest_sha256"], "rows": len(rows),
            "classes": {k: sum(1 for r in rows if r["CLASS"] == k) for k in sorted({r["CLASS"] for r in rows})},
            "v3b_c_stair_commercial_m3": v3b_c["qty"], "v3b_method_reproduced_m3": v3b_sum,
            "v3b_reproduced_exactly": abs(v3b_sum - v3b_c["qty"]) < 5e-5,
            "v3b_risers": {x["STOREY_RUN"]: x["V3B_RISERS"] for x in v3},
            "s8_7a_main_stair_whole_m3_range": [main_lo, main_hi], "s8_7a_light_well_whole_m3": c_whole,
            "released_by_s8_7a": None,
            "rule": "explains differences only; no frozen quantity is changed, no riser count is chosen, nothing is "
                    "released"}
    (HERE / OUT[2]).write_text(json.dumps(summ, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (HERE / OUT[3]).write_text(readme(summ, rep), encoding="utf-8")
    post = DR.verify_frozen(MANIFEST, ROOT)
    post87 = DR.verify_frozen(S87_MANIFEST, ROOT)
    assert post["manifest_sha256"] == pre["manifest_sha256"]
    assert post87["manifest_sha256"] == pre87["manifest_sha256"]
    return summ


def readme(s, rep):
    t = "\n".join(f"| {x['STOREY_RUN']} | {x['V3B_RISERS']} ({_cell(x['V3B_RISER_MM'])} mm) | "
                  f"{', '.join(f'{k} {v}' for k, v in x['DRAWN_COUNTS'].items())} | "
                  f"{x['OWNER_SCENARIOS']['A']} / {x['OWNER_SCENARIOS']['B']} | {_cell(x['V3B_CONCRETE_M3'])} | "
                  f"{_cell(x['S8_7A_WHOLE_STAIR_M3_RANGE'][0])} - {_cell(x['S8_7A_WHOLE_STAIR_M3_RANGE'][1])} |"
                  for x in rep)
    return f"""# S8.7A post-freeze comparison

This comparison ran after the freeze. The frozen S8.7A layer and the S8.7 package were verified before and after,
and neither was written. Classes: {json.dumps(s['classes'])}.

## V3b C-STAIR

V3b released no technical quantity. Its commercial provisional figure was {s['v3b_c_stair_commercial_m3']} m3, and
the post-freeze module reproduces it from V3b's own stated method as {s['v3b_method_reproduced_m3']} m3 (`02`). The
method:

- risers from ceil(H / 0.175);
- one continuous slope per storey;
- width 1.15 m and waist 0.16;
- W x W landings, two on GF -> 1F and one on 1F -> 2F.

| Run | V3b risers | Drawn risers | Owner A / B | V3b m3 | S8.7A whole stair m3 (sensitivity) |
|---|---|---|---|---|---|
{t}

- **GF -> 1F:** V3b's 26 is drawn on no view and is neither owner scenario.
- **1F -> 2F:** V3b's 24 equals the structural 1F roof sheet only because 4.20 / 0.175 = 24. That sheet omits the
  three radial winder risers.
- **Total:** the V3b figure sits inside the S8.7A main-stair range, {s['s8_7a_main_stair_whole_m3_range'][0]} -
  {s['s8_7a_main_stair_whole_m3_range'][1]} m3, but only through compensating errors:
  - a single slope instead of two flights and a winder turn;
  - 1.15 m width where the drawings give 1.20;
  - the half-turn as flat W x W quarters: two on GF -> 1F, where one quarter is drawn as winders, and one on
    1F -> 2F, where two quarters are drawn.
- **Scope:** V3b leaves out the light-well (round) stair, which is {s['s8_7a_light_well_whole_m3']} m3 in S8.7A.

## Other references

- **Riser finish:** with uniform finished risers the area is H x W for any count, so the confirmed scenario changes
  the nosing and tread lines but not the riser face area of the straight flights.
- **PRE-S8:** the stair rows carry the same V3b line. Their three missing items (waist, riser height, landing levels)
  are the S8.7A questions:
  - riser height is narrowed to a choice between drawn counts;
  - landing levels are scheduled per scenario;
  - the waist stays open.
- **S7 interface:** the S7 stair-side top extensions agree with S8.7A's record, 75 strip ends and 71.9 kg.
- **R5:** the register counts risers = lines + 1 and finds no radial line. On these plans the landing-edge lines are
  drawn risers, so R5 over-counts by one each run whose landing edge is drawn. It also misses the winder risers.

Nothing here or in S8.7A is released. The owner decides before any production BOQ change.
"""


if __name__ == "__main__":
    print(json.dumps(compare(), indent=1))
