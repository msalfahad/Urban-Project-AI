"""T-356 development-villa ledger: three buried-concrete range findings of T-347 (F-T347-2 / -3 / -4) settled to a
proposal per candidate line. Reads only committed, values-only inputs:

  research/agents_t356/ALSENAN_T356_INPUT.json      (own DXF read, t356_extract.py)
  research/agents_t347/CANDIDATE_V3024_BURIED_LINES.json, BINDING_T347.csv   (V3.0.24 of record, T-347 binding)
  research/agents_t242/LEDGER_T242.csv              (interior ground-beam runs, D-33 / D-34)

    python3 -I research/agents_t356/t356_alsenan.py --write

Outputs: FINDINGS_T356.csv, FILL_T350_T356.csv, DOWNGRADE_PROPOSALS_T356.json, summary_t356.json.
Nothing here changes a candidate or released line; the proposals are for the Checker / lane I (T-350).
"""

import csv
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import t356_rules as R  # noqa: E402

CANDIDATE = "ARCH_TAKEOFF_V3.0.24"
T = 0.10                                   # blinding thickness, p.13 '10cm Plain con.'
STRAP_LINE = "L-35382b18e2e362df3ae6"
BAND_LINE = "L-6290a9f3d93f38cd46d6"
BAND_ENGINE_LENGTH_M = 60.17               # T-037: 30.97 + 14.60 + 14.60, the neighbour side (31.17 m) not in the group
BAND_WIDTH = 0.20
BAND_DEPTHS = (0.40, 0.60)                 # p.14 plan 'GROUND BEAM (20x40)'; p.10 schedule row B.W 20 x 60
STRAP_B = {"SB1": 0.70, "SB2": 1.00, "SB3": 0.50}   # p.10 schedule of simple beams, B (breadth)
PAD = (1.30, 0.80, 0.30)                   # p.14 '(130x80x30)'; A-A: the 80 includes the 20 G.B, G.B and pad share a soffit
GB_TITLES = [("GT5M", ">", 5.0, 0.60), ("LT5M", "<", 5.0, 0.40), ("LT2_5M", "<", 2.5, 0.30)]   # p.13 titles


def _load():
    inp = json.load(open(os.path.join(HERE, "ALSENAN_T356_INPUT.json"), encoding="utf-8"))
    cand = json.load(open(os.path.join(ROOT, "research/agents_t347/CANDIDATE_V3024_BURIED_LINES.json"), encoding="utf-8"))
    lines = cand["lines"]
    lines = {l["line_id"]: l for l in (lines.values() if isinstance(lines, dict) else lines)}
    bind = list(csv.DictReader(open(os.path.join(ROOT, "research/agents_t347/BINDING_T347.csv"), encoding="utf-8")))
    t242 = list(csv.DictReader(open(os.path.join(ROOT, "research/agents_t242/LEDGER_T242.csv"), encoding="utf-8")))
    return inp, cand, lines, bind, t242


def _f(x):
    return "" if x is None else f"{x:.6f}"


def build():
    inp, cand, lines, bind, t242 = _load()
    if cand["candidate"] != CANDIDATE:
        raise R.Refused("candidate of record changed")
    rows, fill, dgs = [], [], []

    # ---- F-T347-2 strap blinding --------------------------------------------------------------------------------
    st = inp["straps_total"]
    # printed width (p.10) x drawn axis clear length: a parallelogram strip between two parallel faces is exactly
    # (B + 2p) x axis length; the drawn polygon is kept as the check (SB2 is drawn 0.987 wide for a printed 1.00)
    own_p, band_p = 0.0, 0.0
    for mark, s_ in inp["straps"].items():
        wd = sum(s_["drawn_width_m"]) / 2
        o = (STRAP_B[mark] + 2 * 0.10) * s_["axis_clear_m"]
        own_p += o
        band_p += s_["in_footing_blinding_band_m2"] * (STRAP_B[mark] + 0.20) / (wd + 0.20)
    sr = R.strap_blinding_range(own_p, T, False, merged_strip_m2=own_p - band_p)
    L = lines[STRAP_LINE]
    rep = inp["candidate_basis_reproduction_m2"]
    steps = {
        "own_strip_printed_width": own_p * T,
        "drawn_width_vs_printed": (st["own_strip_m2"] - own_p) * T,
        "merge_into_footing_band": -st["in_footing_blinding_band_m2"] * T,
        "f10f_outline_unseen": (rep["f10_outline_missing|no_gb"] - rep["all_outlines|no_gb"]) * T,
        "gb_blinding_plan_deduction": (rep["f10_outline_missing|gb_blinding_strips"] - rep["f10_outline_missing|no_gb"]) * T,
    }
    steps["residual_unexplained"] = L["bounded_high"] - sum(steps.values())
    t233_high = 0.913
    rows.append({
        "finding": "F-T347-2", "line_id": STRAP_LINE, "item_code": L["item_code"], "element": L["element_id"],
        "line_state": L["evidence_state"], "line_low": _f(L["bounded_low"]), "line_high": _f(L["bounded_high"]),
        "ledger_low": _f(sr["low"]), "ledger_high": _f(sr["high"]), "verdict": R.verdict(
            L["bounded_low"], L["bounded_high"], sr["low"], sr["high"]),
        "proposal": "CORRECT RANGE (held-range fix in lane I, T-350): 0 .. own strip; state stays HELD (D-15)",
        "cause_m3": "; ".join(f"{k} {v:+.6f}" for k, v in steps.items()),
        "evidence": "ST p.10 SB1 70x50 / SB2 100x50 / SB3 50x40 (size only); ST p.13 blinding drawn under footings and "
                    "ground beams, none under a strap (D-15); DXF strap edges 1689/1B1C, 1B08/1B09, 1B26/1B27; footing "
                    "outlines 1B24, 1B1B, 1B07, 1B19, 1B2A, 166B; T-230 strap top <= -0.33, ground-beam soffit >= -0.35 "
                    "main / annex gap >= 0.28 m (no shared level)",
        "open_items": "D-15 (blinding under straps, and the strap soffit level: merged reading "
                      f"{sr['merged']:.6f} m3 only if every strap soffit is flush with the footing soffits)",
    })
    fill.append({"line_id": STRAP_LINE, "family": "STR.CONC.BLINDING strap", "status": "HELD",
                 "value_m3": R.fill_value("HELD", None), "lo_m3": _f(sr["low"]), "lo_basis": "READING_NONE (D-15)",
                 "hi_m3": _f(sr["high"]), "hi_basis": f"own strip {own_p:.6f} m2 = printed (B + 0.20) x axis clear, x 0.10 (projection INHERITED "
                             "from p.13)",
                 "held_by": "D-15"})

    # ---- F-T347-3 boundary lower band -------------------------------------------------------------------------------
    b = inp["band"]
    br = R.band_range(b["centreline_m"], b["crossing_total_m"], BAND_WIDTH, BAND_DEPTHS)
    pad_split = BAND_WIDTH * PAD[0] * PAD[2]
    line_low = R.band_line_low(br["low"], pad_split, None)
    L = lines[BAND_LINE]
    free = b["centreline_m"] - b["crossing_total_m"]
    a_reading = free * BAND_WIDTH * max(BAND_DEPTHS)
    rows.append({
        "finding": "F-T347-3", "line_id": BAND_LINE, "item_code": L["item_code"], "element": L["element_id"],
        "line_state": L["evidence_state"], "line_low": _f(L["bounded_low"]), "line_high": _f(L["bounded_high"]),
        "ledger_low": _f(br["low"]), "ledger_high": _f(br["high"]),
        "verdict": R.verdict(L["bounded_low"], L["bounded_high"], br["low"], br["high"]),
        "proposal": "CORRECT RANGE by a downgrade-only record (UNSUPPORTED BASIS: length): line HELD blank; audit "
                    f"range {br['low']:.6f} .. {br['high']:.6f} m3 for the band solid; the LINE's low end NOT "
                    f"ESTABLISHED while the pad split ({pad_split:.6f} m3 per pad, count not printed) is open",
        "cause_m3": (f"length {BAND_ENGINE_LENGTH_M:.2f} m (one side lost) vs free {free:.2f} / drawn "
                     f"{b['centreline_m']:.2f} m: at B.W 20 x 60 {(BAND_ENGINE_LENGTH_M - free) * 0.12:+.6f} vs the "
                     f"owner's provisional A {a_reading:.6f}, {(BAND_ENGINE_LENGTH_M - b['centreline_m']) * 0.12:+.6f} "
                     "vs B; section: one of two printed readings"),
        "evidence": "DXF S-BOUN 1658 / 1659 (band 0.20, centreline 91.94 m, own); 21.45 m through 9 outlines "
                    "(1B1B 4.45, 1B07 3.50, 1B1A 3.80, 1B2A 1.80, 1B24 3.60, 1668 0.90, 1669 1.50, 166A 0.90, FN 1100 "
                    "1.00); ST p.10 B.W 20 x 60 (4 d16 B / 2 d14 T / 7 d8/m); ST p.14 plan 'GROUND BEAM (20x40)', "
                    "section A-A lower G.B 20 wide, depth not written, bars 2 d14 + 3 d16 T&B, d8/20 (not the B.W row), "
                    "pad 130x80x30 sharing the G.B soffit",
        "open_items": "Q-28 / RFI-S03 (section, crossing levels); M4 / RFI-S04 (pad and column count); pad vs band owner",
    })
    fill.append({"line_id": BAND_LINE, "family": "STR.CONC.BOUNDARY_WALL lower band", "status": "HELD",
                 "value_m3": R.fill_value("HELD", None), "lo_m3": "" if line_low is None else _f(line_low),
                 "lo_basis": f"NOT ESTABLISHED for the line (band solid >= {br['low']:.6f}; pad split n x "
                             f"{pad_split:.6f})", "hi_m3": _f(br["high"]), "hi_basis": "91.94 m x 0.20 x 0.60",
                 "held_by": "Q-28, M4"})
    dgs.append({"proposal_id": "DGP-T356-BAND", "basis_label": "UNSUPPORTED BASIS", "candidate_version": CANDIDATE,
                "line_ids": [BAND_LINE], "engine_qty": L["measured_net"], "proposed_state": "HELD",
                "audit_range_m3": [round(br["low"], 6), round(br["high"], 6)],
                "line_low_end": "NOT_ESTABLISHED (pad split, M4)",
                "evidence": [{"sheet": "ST7757 dxf.dxf FOUNDATION PLAN S-BOUN 1658/1659",
                              "printed_value": "band 0.20 closed round the plot, centreline 91.94 m"},
                             {"sheet": "ST7757.pdf p.10", "printed_value": "B.W 20 x 60"},
                             {"sheet": "ST7757.pdf p.14", "printed_value": "GROUND BEAM (20x40); A-A lower G.B depth not "
                                                                         "written; pads 130x80x30"}],
                "reason": "UNSUPPORTED BASIS: the line is 60.17 m x 0.20 x 0.60 SOURCE_DERIVED; 60.17 m is the band "
                          "with one plot side lost (T-037), neither the free 70.49 m nor the drawn 91.94 m, and 0.60 is "
                          "one of two printed sections (Q-28 A PROVISIONAL, not released)",
                "issued_by": "PROPOSAL (Worker 1, T-356): the Checker issues or refuses"})

    # ---- F-T347-4 interior ground beams, D-34 title precedence -----------------------------------------------------
    run2line = {r["id"][3:]: r["line_id"] for r in bind if r["id"].startswith("GB:")}
    gb_ids, gb_line, gb_lo, gb_hi = [], 0.0, 0.0, 0.0
    for x in t242:
        if "D-34" not in x["reasons"]:
            continue
        lid = run2line.get(x["run"])
        L = lines.get(lid)
        if L is None:
            raise R.Refused(f"run {x['run']} has no candidate line")
        # own range: titles holding literally on the face-to-face and the centreline basis (R-T356-5) x net plan
        cc = float(L["notes"].split("c/c ~")[1].split(" m")[0])
        held = R.class_titles([float(x["L_m"]), cc], GB_TITLES)
        names = sorted("GB-" + t[0] for t in held)
        if names != sorted(x["titles"].split("+")):
            raise R.Refused(f"run {x['run']}: titles {names} differ from T-242 {x['titles']}")
        adj = [float(a) for a in x["end_adjust_m2"].split("..")] if x["end_adjust_m2"] else [0.0, 0.0]
        # net plan of the line: its own value / its own class depth (the printed 'net_plan_m2' is rounded to 5 dp)
        h_line = float(L["notes"].split("-> H ")[1].split(";")[0])
        plan = L["bounded_low"] / h_line
        if abs(plan - L["dimensions"]["net_plan_m2"]) > 1e-5:
            raise R.Refused(f"run {x['run']}: line plan {plan} vs printed {L['dimensions']['net_plan_m2']}")
        lo = (plan + min(adj)) * min(t[3] for t in held)
        hi = (plan + max(adj)) * max(t[3] for t in held)
        if abs(lo - float(x["low_m3"])) > 1e-4 or abs(hi - float(x["high_m3"])) > 1e-4:
            raise R.Refused(f"run {x['run']}: own range {lo:.6f} .. {hi:.6f} differs from T-242")
        v = R.verdict(L["bounded_low"], L["bounded_high"], lo, hi)
        single = abs(L["bounded_low"] - L["bounded_high"]) < 1e-9
        d33 = bool(x["d33_tees"])
        if v == "CORRECT_RANGE" and single:
            gb_ids.append(lid)
            gb_line += L["bounded_low"]
            gb_lo += lo
            gb_hi += hi
            prop = "CORRECT RANGE by a downgrade-only record: single class depth shown as the value of an open title " \
                   "precedence (D-34" + (", and D-33: a beam lands on it, loaded section not printed" if d33 else "") + ")"
        elif v == "CORRECT_RANGE":
            prop = ("OTHER BASIS DIFFERENCE (not the D-34 title): the line omits the T-230 neck end adjustment "
                    f"{x['end_adjust_m2']} m2 of the run (T-242); a held-range fix for lane I, not a downgrade")
        else:
            prop = "LINE_RIGHT (the line already carries the D-34 range)"
        rows.append({
            "finding": "F-T347-4", "line_id": lid, "item_code": L["item_code"], "element": L["element_id"],
            "line_state": L["evidence_state"], "line_low": _f(L["bounded_low"]), "line_high": _f(L["bounded_high"]),
            "ledger_low": _f(lo), "ledger_high": _f(hi), "verdict": v, "proposal": prop,
            "cause_m3": f"run {x['run']} face {float(x['L_m']):.4f} / c-c {cc:.2f} m: titles holding literally "
                        + "+".join(n[3:] for n in names) + f"; low - line {lo - L['bounded_low']:+.6f}, "
                        f"high - line {hi - L['bounded_high']:+.6f}",
            "evidence": "ST p.13 titles 'More than 5m length without concentrated load' (60), 'Less than 5m length "
                        "without concentrated load' (40), 'Less than 2.5m length' (30); T-242 run ledger (face to face)",
            "open_items": "D-34" + (", D-33" if d33 else ""),
        })
        if v == "CORRECT_RANGE" and single:
            fill.append({"line_id": lid, "family": "STR.CONC.GROUND_BEAM interior", "status": "HELD",
                         "value_m3": R.fill_value("HELD", None), "lo_m3": _f(lo), "lo_basis": "narrowest printed title",
                         "hi_m3": _f(hi), "hi_basis": "widest printed title holding literally",
                         "held_by": "D-34" + (" + D-33 (no loaded section printed)" if d33 else "")})
    dgs.append({"proposal_id": "DGP-T356-GB-D34", "basis_label": "UNSUPPORTED BASIS", "candidate_version": CANDIDATE,
                "line_ids": sorted(gb_ids), "engine_qty": round(gb_line, 6), "proposed_state": "HELD",
                "audit_range_m3": [round(gb_lo, 6), round(gb_hi, 6)],
                "evidence": [{"sheet": "ST7757.pdf p.13", "printed_value": "three ground-beam sections titled by span "
                              "length (> 5 m: 30 x 60; < 5 m: 30 x 40; < 2.5 m: 30 x 30); no precedence printed"}],
                "reason": "UNSUPPORTED BASIS: each line shows the 'less than 2.5 m' depth 0.30 as its value although the "
                          "'less than 5 m' title also holds literally (D-34, designer item S8); the candidate's range "
                          "rule only varies the length basis (clear vs c/c), never the title",
                "issued_by": "PROPOSAL (Worker 1, T-356): the Checker issues or refuses"})

    summary = {
        "schema": "URBAN_T356_SUMMARY_V1", "candidate": CANDIDATE,
        "candidate_lines_json_sha256": cand["candidate_lines_json_sha256"],
        "strap_blinding": {"line": [lines[STRAP_LINE]["bounded_low"], lines[STRAP_LINE]["bounded_high"]],
                           "ledger": [sr["low"], round(sr["high"], 6)], "merged_reading": round(sr["merged"], 6),
                           "t233_high": t233_high, "t233_minus_ledger": round(t233_high - sr["high"], 6),
                           "drawn_polygon_high": round(st["own_strip_m2"] * T, 6),
                           "decomposition_m3": {k: round(v, 6) for k, v in steps.items()}},
        "boundary_band": {"line": lines[BAND_LINE]["measured_net"], "solid_range": [round(br["low"], 6),
                          round(br["high"], 6)], "drawn_m": b["centreline_m"], "crossing_m": b["crossing_total_m"],
                          "free_m": round(free, 4), "owner_A_provisional": round(a_reading, 6),
                          "pad_split_m3_each": round(pad_split, 6), "line_low_end": "NOT_ESTABLISHED"},
        "gb_d34": {"lines_single_value": len(gb_ids), "line_sum": round(gb_line, 6), "range": [round(gb_lo, 6),
                   round(gb_hi, 6)], "high_minus_line": round(gb_hi - gb_line, 6)},
        "rows": len(rows), "fill_rows": len(fill),
    }
    return rows, fill, dgs, summary


def _csv(rows):
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return s.getvalue()


def main(argv):
    rows, fill, dgs, summary = build()
    out = {"FINDINGS_T356.csv": _csv(rows), "FILL_T350_T356.csv": _csv(fill),
           "DOWNGRADE_PROPOSALS_T356.json": json.dumps({"schema": "URBAN_T356_DOWNGRADE_PROPOSALS_V1",
                                                         "proposals": dgs}, indent=1, sort_keys=True) + "\n",
           "summary_t356.json": json.dumps(summary, indent=1, sort_keys=True) + "\n"}
    if "--write" in argv:
        for k, v in out.items():
            with open(os.path.join(HERE, k), "w", encoding="utf-8") as f:
                f.write(v)
    return out


if __name__ == "__main__":
    o = main(sys.argv[1:])
    print(o["summary_t356.json"])
