"""T-731 development-villa build (research, unwired): ST-01 GF -> 1F (MS1-L / MS1-T / MS1-U) readings defined by count x
riser = printed rise segment by segment (R-T731-1), the MS1-L concrete and formwork bounds and their T-711 / T-725
children restated on ARCH_TAKEOFF_V3.0.73 (R-T731-2), and the ST-01 flights / landings re-measured by handle for the
Checker.

Reads only merged repository files (sha256-pinned in PINS.json) plus the drawing facts below, re-read this run from
Drive "Alsenan chalet project" / "ST7757 dxf.dxf" (sha256 9f9d1179..., by handle, relative lengths only) and
"p7757_arch_sheet10.pdf" (section A-A: level marks and the landing dimension), both decoded by the wrapper into
.work/private only. No candidate, released (V2.9 + route G), rule / knowledge version or registry file is touched;
nothing is wired, released or VERIFIED.

    python3 -I research/agents_t731/t731_alsenan.py [--write | --check]
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t731_rules as R  # noqa: E402

R725 = R.R725
SCHEMA = "URBAN_T731_STAIR_COHERENT_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.73"
INDEX = "research/agents_t722/out/LINE_INDEX_V3_0_73.json"
T725 = "research/agents_t725/out/T725_LEDGER.json"
T711 = "research/agents_t711/out/T711_LEDGER.json"
T258 = "research/agents_t258/LEDGER_T258.csv"
INPUTS = (INDEX, T725, T711, T258)
PIN_FILE = HERE / "PINS.json"
OUT_JSON = HERE / "out" / "T731_LEDGER.json"
OUT_MD = HERE / "out" / "T731_REMEASURE.md"

# ---- drawing facts, own read this run, relative lengths in m
ST = {
    "dxf_sha256_16": "9f9d1179a5d2a663",
    "g": 0.300, "t": 0.16, "lane": 1.200,
    # p.4 MS1-L riser lines, distance from 45A (all 1.150 long, layer 2); B20 face 2C6 lies 0.150 from 45A
    "ms1l_lines": {"45A": 0.0, "271": 0.3, "26C": 0.6, "26D": 0.9, "26E": 1.2, "26F": 1.5, "268": 1.8, "269": 2.1,
                   "26A": 2.4, "26B": 2.7, "25D": 3.0, "25E": 3.3},
    "ms1l_A_first": "26C",           # reading A: 10 lines 26C .. 25E (T-258 / T-281, C-ST-4)
    "ms1l_col36B_m2": 0.025,
    "turn_region": (1.300, 1.150),   # 284 -> 2F3 1.300; 25E -> 279 1.150
    "winder_lines_B": {"2F6": 1.2587, "2F4": 1.6263, "2F5": 1.2587, "2F3": 1.1500},
    "ms1ld": (1.200, 1.200),         # 25A -> 296; 25B -> 279
    "ms1u_lines": {"459": 0.0, "270": 0.3, "264": 0.6, "265": 0.9, "266": 1.2, "267": 1.5, "260": 1.8, "262": 2.1,
                   "263": 2.4, "261": 2.7, "25C": 3.0, "25B": 3.3},  # 2C6 at 0.200 from 459 (head inside B20)
    # p.5
    "ms2l_lines": {"646": 0.0, "645": 0.3, "640": 0.6, "641": 0.9, "642": 1.2, "643": 1.5, "63C": 1.8, "63D": 2.1,
                   "63E": 2.4, "63F": 2.7, "631": 3.0, "632": 3.3},  # B20 face 5E1 at 0.150 from 646
    "ms2u_lines": {"644": 0.0, "638": 0.3, "639": 0.6, "63A": 0.9, "63B": 1.2, "634": 1.5, "636": 1.8, "637": 2.1,
                   "635": 2.4, "630": 2.7, "62F": 3.0},              # 11 drawn; 62F -> B23 face 5E1 3.100
    "ms2ld_w": (1.300, 1.150),       # 5E3 -> 5E2; 632 -> 5C0
    "ms2ld_e": (1.200, 1.200),       # 5E2 -> 5D4; 62F -> 5C0
    # p.3 ST-01b D1
    "d1_lines": {"1C7": 0.0, "1C6": 0.3, "1C5": 0.6, "1C4": 0.9},  # each 1.150 long
    "d1_lane": 1.200,                # layer-5 edge 1C3 -> band face 15F
    "st_levels_at_st01": "none: no level text within 5 m of 45A (p.4) or 646 (p.5); the ST plans print no stair level",
}
ARCH = {
    "sheet": "p7757_arch_sheet10.pdf (section A-A, 1:100, page rotated)",
    "GF": ("+1.00", 1.00, "level mark on the GF stair-hall floor"),
    "LOBBY": ("+0.30", 0.30, "level mark on the court-door lobby floor under the landing"),
    "LD": ("+3.50", 3.50, "vertical dimension 320 from the +0.30 mark to the top (finish) line of the half landing: "
                          "0.30 + 3.20"),
    "1F": ("+5.50", 5.50, "level mark; storey dimension 450 from +1.00"),
}
LEVELS = [R.PrintedLevel("GF", 1.00, ARCH["GF"][2]), R.PrintedLevel("LD", 3.50, ARCH["LD"][2]),
          R.PrintedLevel("1F", 5.50, ARCH["1F"][2])]
BREAKS = {"MS1-T": "LD"}
DRAWN_EVERY_SOURCE = {"MS1-U": 12}  # ST p.4 25B .. 459 12 lines and section A-A 12 cut risers (VERIFIED, T-189)
READ_SRC = {
    "A": ((("MS1-L", 10), ("MS1-T", 5), ("MS1-U", 12)), "section A-A sheet 10 (owner Q-46 A: the section counts)"),
    "B": ((("MS1-L", 12), ("MS1-T", 4), ("MS1-U", 12)),
          "ST p.4: 12 straight lines 45A .. 25E + winders 2F6 / 2F4 / 2F5 + closing 2F3 + 12 lines 25B .. 459"),
    "P": ((("MS1-L", 10), ("MS1-T", 4), ("MS1-U", 11)), "architectural GF plan 10 + 4 + 11 (Q-46: a check only)"),
}


def sha16(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def check_pins():
    pins = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    if set(pins) != set(INPUTS):
        raise R.Refused(f"pin set differs: {sorted(set(pins) ^ set(INPUTS))}")
    bad = {p: (sha16(p), v) for p, v in pins.items() if sha16(p) != v}
    if bad:
        raise R.Refused(f"input drift (sha256[:16] now, pinned): {bad}")
    return pins


def r6(x):
    return None if x is None else round(x, 6) + 0.0


BR = R725.BR


def lo6(x):
    """a floor printed by R-T696-1 (toward minus infinity) from the exact float"""
    return str(BR.round_low(BR.D(repr(x))))


def hi6(x):
    """a high / cap printed by R-T696-1 (toward plus infinity)"""
    return str(BR.round_high(BR.D(repr(x))))


def spacing_ok(lines: dict, g: float):
    v = sorted(lines.values())
    return all(abs((b - a) - g) < 1e-9 for a, b in zip(v, v[1:]))


def ms1l_profile(r, n, *, clip):
    g, t = ST["g"], ST["t"]
    e = (n - 1) * g
    whole = R725.side_profile(r, g, t, n, 0.0, e, clip_floor=clip)
    strip = R725.side_profile(r, g, t, n, e - 0.05, e, clip_floor=False)
    return whole, strip


def build():
    pins = check_pins()
    idx = json.loads((ROOT / INDEX).read_text(encoding="utf-8"))
    if idx["candidate_version"] != CANDIDATE:
        raise R.Refused("line index is not the candidate of record")
    lines73 = {x["line_id"]: x for x in idx["lines"]}
    t725 = {x["line_id"]: x for x in json.loads((ROOT / T725).read_text(encoding="utf-8"))["lines"]}
    t711 = {x["line_id"]: x for x in json.loads((ROOT / T711).read_text(encoding="utf-8"))["lines"]}
    with open(ROOT / T258, encoding="utf-8", newline="") as fh:
        t258 = {}
        for row in csv.DictReader(fh):
            t258.setdefault(row["id"], row)

    # ------------------------------------------------------------ (a) readings, R-T731-1
    g, t, w = ST["g"], ST["t"], ST["lane"]
    if not all(spacing_ok(ST[k], g) for k in ("ms1l_lines", "ms1u_lines", "ms2l_lines", "ms2u_lines", "d1_lines")):
        raise R.Refused("a riser-line spacing differs from the going")
    readings, refused = {}, {}
    for name, (pieces, src) in READ_SRC.items():
        try:
            R.check_drawn_counts(name, pieces, DRAWN_EVERY_SOURCE)
            segs = R.segments(name, pieces, src, LEVELS, BREAKS)
            readings[name] = {"source": src, "pieces": pieces,
                              "segments": [{"pieces": s.pieces, "n": s.n, "rise_m": s.rise_m, "r": round(s.r, 9),
                                            "from": s.lo, "to": s.hi} for s in segs],
                              "r_by_piece": {p: s.r for s in segs for p in s.pieces}}
        except R.Refused as exc:
            refused[name] = {"source": src, "pieces": pieces, "why": str(exc)}
    # the uniform carriers recorded by earlier pieces
    misses_b28 = R.uniform_misses("B28-uniform", READ_SRC["B"][0], LEVELS, BREAKS)
    refused["B28-uniform"] = {
        "source": "T-725 'coherent B': ST p.4 count 28 at 4.50 / 28 over the storey",
        "why": "R-T731-1 (c): one rise 0.160714 over a printed half landing: reaches "
               f"+{misses_b28[0][2]:.6f} at the landing printed {ARCH['LD'][0]} (miss {misses_b28[0][3]:+.6f} m), and "
               "carries MS1-U at 0.160714 against its VERIFIED 2.00 / 12", "misses": misses_b28}
    try:
        R725.Reading("B27-as-recorded", 4.50, READ_SRC["B"][0], "ST p.4", "section A-A 27", total_declared=27)
    except R725.Refused as exc:
        refused["B27-as-recorded"] = {"source": "T-258 / T-281 / T-352 / T-711 MS1-L part", "why": str(exc)}
    if set(readings) != {"A", "B"}:
        raise R.Refused(f"coherent readings differ from A / B: {sorted(readings)}")
    rA, rB = readings["A"]["r_by_piece"], readings["B"]["r_by_piece"]
    if abs(rA["MS1-U"] - rB["MS1-U"]) > 1e-12 or abs(rA["MS1-U"] - 4.50 / 27) > 1e-12:
        raise R.Refused("MS1-U rise differs between coherent readings or from its VERIFIED basis")

    # ------------------------------------------------------------ (b) MS1-L concrete and formwork, restated
    nA = sum(1 for k, v in ST["ms1l_lines"].items() if v >= ST["ms1l_lines"][ST["ms1l_A_first"]])
    nB = len(ST["ms1l_lines"])
    if (nA, nB) != (READ_SRC["A"][0][0][1], READ_SRC["B"][0][0][1]):
        raise R.Refused("MS1-L drawn line counts differ from the readings")
    rd = {"A": (rA["MS1-L"], nA), "B": (rB["MS1-L"], nB)}
    prof = {k: {m: ms1l_profile(r, n, clip=(m == "D")) for m in ("O", "D")} for k, (r, n) in rd.items()}
    conc = {k: prof[k]["O"][0] * w for k in rd}
    if abs(conc["A"] - float(t258["ST01-MS1-L"]["low_m3"])) > 1e-6:
        raise R.Refused("MS1-L reading A concrete differs from T-258")
    turn = ST["turn_region"][0] * ST["turn_region"][1]
    floor_plate = 1.44 * t
    sums = {k: conc[k] + 0.5 * rd[k][0] * 1.44 + floor_plate for k in rd}
    old711 = t711["L-7863355dfcb68a681d2d"]
    if abs(sums["A"] - float(old711["at_least_m3"])) > 1e-6:
        raise R.Refused("T-711 reading A sum not reproduced")
    re711 = R.restate(float(old711["at_least_m3"]), None, {k: (v, None) for k, v in sums.items()}, tol=2e-6)
    comp_min = min(conc.values()) + 0.5 * min(r for r, _ in rd.values()) * 1.44 + floor_plate

    # formwork: L-9c3643da (well side), L-d9790e45 (cap), L-ffd491ad (risers + soffit + turn)
    side = {f"{k}{m}": prof[k][m][0] - prof[k][m][1] for k in rd for m in ("O", "D")}
    old9c = t725["L-9c3643da524267bf47f6"]
    re9c = R.restate(float(old9c["low"]), float(old9c["high"]), {k: (v, v) for k, v in side.items()}, tol=2e-6)
    cap_d9 = {k: prof[k]["O"][0] + prof[k]["O"][1] for k in rd}
    oldd9 = t725["L-d9790e457fd530487553"]
    ffd = {}
    for k, (r, n) in rd.items():
        run = (n - 1) * g
        plan = run * w - ST["ms1l_col36B_m2"]
        risers = R725.riser_forms([w] * n, r, drawn=True)
        if k == "A":
            wind = R725.winder_floor(READ_SRC["A"][0][1][1], min(ST["turn_region"]), r, region_drawn=True)
        else:
            wind = R725.riser_forms(ST["winder_lines_B"].values(), r, drawn=True)
        for m in ("O", "D"):
            soff = R725.soffit_true(plan, r, g) if m == "O" else R725.soffit_d(plan, w, r, g, t, foot_on_slab=True)
            ffd[k + m] = {"risers": risers, "soffit": soff, "turn_floor": R725.warped_floor(turn, region_drawn=True),
                          "winders": wind, "sum": risers + soff + turn + wind}
    oldff = t725["L-ffd491ad529ee2251982"]
    # T-725 recorded AD 7.678895 floored to 7.678894 by its directed rounding (R-T696-1): equal within 2e-6, kept
    reff = R.restate(float(oldff["low"]), None, {k: (v["sum"], None) for k, v in ffd.items()}, tol=2e-6)
    if reff["flag"] or abs(ffd["AD"]["sum"] - float(oldff["low"])) > 2e-6:
        raise R.Refused("L-ffd491ad reading A method D not reproduced")
    soffit_hi = {"O": ffd["BO"]["soffit"], "D": ffd["BD"]["soffit"]}

    for lid in ("L-7863355dfcb68a681d2d", "L-9c3643da524267bf47f6", "L-d9790e457fd530487553", "L-ffd491ad529ee2251982"):
        x = lines73[lid]
        if x["class"] != "HELD" or x["measured_net"] is not None or x["held_low"] is not None:
            raise R.Refused(f"{lid}: not a blank HELD line on {CANDIDATE}")

    restated = [
        {"line_id": "L-7863355dfcb68a681d2d", "item": "STR.CONC.STAIR", "unit": "m3", "piece": "MS1-L + winders + turn",
         "class_on_V3_0_73": "HELD blank", "class_proposed": "AT_LEAST (T-711, unchanged)",
         "low_old": old711["at_least_m3"], "low_new": lo6(re711["low"]), "high_old": None, "high_new": None,
         "reading_sums_old": old711["reading_sums"],
         "reading_sums_new": {"A": lo6(sums["A"]), "B": lo6(sums["B"])},
         "reading_sums_exact": {k: repr(v) for k, v in sums.items()},
         "t725_B_sum_beside": "1.383119",
         "note": "floor from reading A; B (16 risers to +3.50 at 2.50 / 16 = 0.15625) is above it; no AT_MOST "
                 "(warped turn soffit, C-ST-3); componentwise min mixes readings (refused, information only) "
                 f"{old711['componentwise_min']} -> {lo6(comp_min)}. T-711 printed 1.213429 half-up; the exact "
                 f"reading A sum {sums['A']:.9f} floors to {lo6(sums['A'])} (R-T696-1): -0.000001 m3, rounding only"},
        {"line_id": "L-9c3643da524267bf47f6", "item": "STR.FORMWORK.STAIR", "unit": "m2", "piece": "MS1-L well side",
         "class_on_V3_0_73": "HELD blank", "class_proposed": "BOUNDED (T-725)",
         "low_old": old9c["low"], "low_new": lo6(re9c["low"]), "high_old": old9c["high"],
         "high_new": hi6(re9c["high"]), "readings_new": {k: r6(v) for k, v in side.items()},
         "note": "high = reading B method O on the coherent 0.15625 (T-725 0.854426 used 4.50 / 28 uniform)"},
        {"line_id": "L-d9790e457fd530487553", "item": "STR.FORMWORK.STAIR", "unit": "m2",
         "piece": "MS1-L west wall + well-end junction", "class_on_V3_0_73": "HELD blank",
         "class_proposed": "BLANK_NAMED (T-725, SEQ)", "cap_old": oldd9["cap"],
         "cap_new": hi6(max(cap_d9.values())), "readings_new": {k: r6(v) for k, v in cap_d9.items()},
         "note": "cap = reading B method O on the coherent 0.15625; low stays blank (sequence not printed)"},
        {"line_id": "L-ffd491ad529ee2251982", "item": "STR.FORMWORK.STAIR", "unit": "m2",
         "piece": "MS1-L risers + soffit + winder turn", "class_on_V3_0_73": "HELD blank",
         "class_proposed": "AT_LEAST (T-725, unchanged)", "low_old": oldff["low"], "low_new": lo6(reff["low"]),
         "readings_old": oldff["readings"],
         "readings_new": {k: {kk: r6(vv) for kk, vv in v.items()} for k, v in ffd.items()},
         "note": "low = reading A method D (unchanged); the B readings move with the coherent rise but stay above"},
    ]
    effects_beside = {
        "MS1-L concrete high m3 (side O x 1.20)": {"T-258 recorded (refused B27)": "1.054813",
                                                   "T-725 (refused B28-uniform)": "1.037005",
                                                   "T-731 coherent B": hi6(conc["B"])},
        "MS1-L soffit true O high m2 (lane A input, T-715 / T-718)": {"T-725": "4.464083",
                                                                       "T-731": hi6(soffit_hi["O"])},
        "MS1-L soffit true D high m2": {"T-725": "4.002826", "T-731": hi6(soffit_hi["D"])},
        "floors moved": 0,
    }

    # ------------------------------------------------------------ (c) re-measure of ST-01 flights / landings
    v = lambda k: ST[k][0] * ST[k][1] * t
    d1_r = (1.00 - 0.30) / len(ST["d1_lines"])
    d1_steps = len(ST["d1_lines"]) * 0.5 * d1_r * g * ST["d1_lane"]
    d1_arr = 0.5 * d1_r * g * ST["d1_lane"] * (1 - ((d1_r - 0.10) / d1_r) ** 2)
    rem = []

    def row(piece, own, ledger_id, released_line=None, status_ledger=None, basis=""):
        lv = t258[ledger_id]["value_m3"] if ledger_id else None
        res = None if (own is None or not lv) else round(own - float(lv), 6) + 0.0
        rem.append({"piece": piece, "own_m3": r6(own), "ledger": ledger_id, "ledger_m3": lv,
                    "residual_m3": res, "status_ledger": status_ledger or (t258[ledger_id]["evidence"] if ledger_id else None),
                    "released_line": released_line, "basis": basis})

    row("MS2-LD-W half landing +7.516", v("ms2ld_w"), "ST01-MS2-LD-W", "L-2416e65f (0.4696 with MS2-LD-E)",
        basis="p.5 5E3 -> 5E2 1.300 x 632 -> 5C0 1.150 x T 0.16 (Q-47 A); level 5.50 + 12 x 4.20 / 25")
    row("MS2-LD-E half landing +7.684", v("ms2ld_e"), "ST01-MS2-LD-E", "L-2416e65f (0.4696 with MS2-LD-W)",
        basis="p.5 5E2 -> 5D4 1.200 x 62F -> 5C0 1.200 x 0.16; level 9.70 - 12 x 0.168")
    row("MS1-LD half landing +3.50", v("ms1ld"), "ST01-MS1-LD", "L-e37d81a8 (1.227952 with MS1-U)",
        basis="p.4 25A -> 296 1.200 x 25B -> 279 1.200 x 0.16; level printed by section A-A (320 above +0.30)")
    row("D1 steps (ST-01b) +0.30 -> +1.00", d1_steps - d1_arr, "ST01b-D1-STEPS", "L-85f64587 (0.100286)",
        basis=f"p.3 1C7 / 1C6 / 1C5 / 1C4 at 0.300, 1.150 long, lane 1C3 -> 15F 1.200; r = 0.70 / 4 = {d1_r:.3f} "
              f"(section A-A +0.30 / +1.00); 4 x 1/2 x r x 0.30 x 1.20 = {d1_steps:.6f} - arrival wedge in GS-08 "
              f"{d1_arr:.6f} (Q-62 A cond)")
    row("MS1-U flight geometry", None, "ST01-MS1-U", "L-e37d81a8", basis="p.4 12 lines 459 .. 25B at 0.300 (handles "
        "in the ledger), 459 0.200 inside B20 (2C6); r 2.00 / 12 on both coherent readings = the VERIFIED basis")
    row("MS2-L flight geometry", None, "ST01-MS2-L", "L-67e4b048", basis="p.5 12 lines 646 .. 632 at 0.300, 646 "
        "0.150 inside B20 (5E1); 3.300 = T-258 basis")
    row("MS2-U flight geometry", None, "ST01-MS2-U", "L-bb0e57b1", basis="p.5 11 drawn lines 644 .. 62F at 0.300, "
        "62F -> 5E1 3.100; arrival line from p.4 459 (T-258)")
    row("MS1-L flight geometry (HELD)", None, "ST01-MS1-L", None, basis="p.4 12 lines 45A .. 25E at 0.300 (B), "
        "10 lines 26C .. 25E (A, from 0.600), 45A 0.150 short of B20 face 2C6, lane 284 -> 256 1.200, head 25E 0.050 "
        "short of the well end")
    row("MS1-T turn region (HELD)", None, "ST01-MS1-T-SLAB", None, basis="p.4 284 -> 2F3 1.300 x 25E -> 279 1.150 = "
        "1.495 m2; winder lines 2F6 1.2587 / 2F4 1.6263 / 2F5 1.2587, closing 2F3 1.1500; soffit not drawn (C-ST-3)")
    for x in rem:
        if x["residual_m3"] is not None and abs(x["residual_m3"]) > 1e-6:
            raise R.Refused(f"re-measure residual {x['piece']}: {x['residual_m3']}")

    out = {
        "schema": SCHEMA, "task": "T-731", "candidate": CANDIDATE, "rules": R.RULES, "inputs": pins,
        "drawn_st": ST, "drawn_arch": ARCH,
        "levels": [vars(lv) for lv in LEVELS],
        "readings_coherent": {k: {kk: vv for kk, vv in x.items() if kk != "r_by_piece"} for k, x in readings.items()},
        "readings_refused": refused,
        "restated": restated, "effects_beside": effects_beside, "remeasure": rem,
        "findings": {
            "F-T731-1": "T-725's 'coherent B' (4.50 / 28 uniform) is itself incoherent: section A-A prints the half "
                        "landing at +3.50 (dimension 320 above +0.30), which 16 risers at 0.160714 miss by +0.0714 m, "
                        "and it would carry the VERIFIED MS1-U at 0.160714 instead of 2.00 / 12. The coherent "
                        "structural reading is 16 risers over 2.50 m (0.15625) then 12 over 2.00 m (0.166667). "
                        "Highs only move: MS1-L concrete hi 1.037005 -> %s m3, well side hi 0.854426 -> %s m2."
                        % (hi6(conc["B"]), hi6(re9c["high"])),
            "F-T731-2": "The architectural GF plan reading (10 + 4 + 11) is refused twice: Q-46 A makes it a check, "
                        "and its 11 MS1-U risers contradict the 12 drawn on ST p.4 and cut in section A-A.",
            "F-T731-3": "The ST plans print no level at ST-01 (own read p.4 / p.5): every reading's rise rests on the "
                        "architectural section's levels; reading B's count is structural, its levels architectural "
                        "(levels are physical facts, R-T731-1 (a)).",
        },
    }
    return out


def report_md(out):
    L = [f"# T-731 ST-01 re-measure and restated MS1-L bounds on {out['candidate']} (research, unwired)", "",
         "## Readings (R-T731-1)", "", "| reading | source | segments (n x r = rise) | state |", "|---|---|---|---|"]
    for k, x in out["readings_coherent"].items():
        seg = "; ".join(f"{s['from']}->{s['to']} {s['n']} x {s['r']:.6f} = {s['rise_m']:.2f}" for s in x["segments"])
        L.append(f"| {k} | {x['source']} | {seg} | COHERENT |")
    for k, x in out["readings_refused"].items():
        L.append(f"| {k} | {x['source']} | - | REFUSED: {x['why']} |")
    L += ["", "## Restated lines", "", "| line | item | piece | old | new | note |", "|---|---|---|---|---|---|"]
    for x in out["restated"]:
        old = x.get("low_old") or "", x.get("high_old") or "", x.get("cap_old") or ""
        new = x.get("low_new") or "", x.get("high_new") or "", x.get("cap_new") or ""
        L.append(f"| {x['line_id']} | {x['item']} {x['unit']} | {x['piece']} | lo {old[0]} hi {old[1]} cap {old[2]} | "
                 f"lo {new[0]} hi {new[1]} cap {new[2]} | {x['note']} |")
    L += ["", "## Re-measure of ST-01 pieces (own read, ST7757 dxf by handle + section A-A)", "",
          "| piece | own m3 | ledger | ledger m3 | residual | ledger state | released line | basis |",
          "|---|---|---|---|---|---|---|---|"]
    for x in out["remeasure"]:
        L.append(f"| {x['piece']} | {'' if x['own_m3'] is None else format(x['own_m3'], '.6f')} | "
                 f"{x['ledger']} | {x['ledger_m3'] or ''} | {'' if x['residual_m3'] is None else x['residual_m3']} | "
                 f"{x['status_ledger']} | {x['released_line'] or ''} | {x['basis']} |")
    return "\n".join(L) + "\n"


def main(argv):
    out = build()
    js = json.dumps(out, indent=1, sort_keys=True, default=str) + "\n"
    md = report_md(out)
    if "--write" in argv:
        OUT_JSON.parent.mkdir(exist_ok=True)
        OUT_JSON.write_text(js, encoding="utf-8")
        OUT_MD.write_text(md, encoding="utf-8")
    elif "--check" in argv:
        if OUT_JSON.read_text(encoding="utf-8") != js or OUT_MD.read_text(encoding="utf-8") != md:
            print("T731 outputs differ from a fresh build")
            return 1
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
