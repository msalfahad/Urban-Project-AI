"""T-699 development-villa census: the 21 blank STR.CONC.LINTEL lines of the candidate of record (V3.0.69 index), each
classed with the one-sided bound the drawings support (R-T699-1) or its exact missing datum. Research only, unwired:
no candidate line moves; a bound sits BESIDE its blank line.

Committed inputs only (merged, Checker-verified ledgers; no drawing is opened by this script):
  V3.0.69 index    research/agents_t687/out/LINE_INDEX_V3_0_69.json (the 21 blank lines, ids / classes asserted)
  payable form     research/agents_t650/out/T650_PAYABLE_FORM.json (B = wall thickness, D = ST p.13 schedule depth,
                   width, 60 / 60 RC cast)
  jamb evidence    research/agents_t644/out/JAMB_EVIDENCE_T644.csv (stopper and available bearing per end, 6 dp)
  extended search  research/agents_t544/out/EXTENDED_SEARCH_T544.csv
  T-673 / T-678    research/agents_t673/out/T673_LEDGER.json, research/agents_t678/out/T678_LEDGER.json (existence,
                   designer causes, thresholds; D-GF-04 / D-1F-06 REQUIRED on the owner door-height fallback Q-55 C)
  run geometry     research/agents_t274/T274_RUN_PIECES.csv (D-GF-04 host run length, for the named END datum)

    python3 -I research/agents_t699/t699_alsenan.py [--write]
"""
from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal as X
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t699_rules as R  # noqa: E402

RES = ROOT / "research"
INDEX = RES / "agents_t687" / "out" / "LINE_INDEX_V3_0_69.json"
T650 = RES / "agents_t650" / "out" / "T650_PAYABLE_FORM.json"
JAMBS = RES / "agents_t644" / "out" / "JAMB_EVIDENCE_T644.csv"
EXT = RES / "agents_t544" / "out" / "EXTENDED_SEARCH_T544.csv"
T673 = RES / "agents_t673" / "out" / "T673_LEDGER.json"
T678 = RES / "agents_t678" / "out" / "T678_LEDGER.json"
PIECES = RES / "agents_t274" / "T274_RUN_PIECES.csv"
OUT = HERE / "out" / "T699_LEDGER.json"
OUT_MD = HERE / "out" / "T699_CENSUS.md"
B_MIN = R.b_min_of("0.40")      # ST p.13 schedule bearing (printed): governs over the owner 0.15 minimum (R-T699-1 (d))
OWNER_PRECAST = [X("1.20"), X("1.50"), X("2.50"), X("3.00"), X("4.00")]

# neighbours of the piers met by these 21 lines, from the candidate state (index asserted below)
NEIGHBOURS = {
    "D-GF-03": "MIN_BEARING",   # bounded 0.052 .. 0.058, MIN_BEARING (T-678 ledger: pier 0.15 to W04 taken whole)
    "D-1F-08": "RELEASED",      # released 0.051 (V3.0.69 index)
    "W11": "HELD", "W12": "HELD",   # both blank in this set: full pier as each one's ceiling, counted once in the family
}

# per line: existence, cause class, cause reference, deciding datum / threshold, conditional exclusion member
CLASS = {
    "W04": ("CONDITIONAL_EXCLUSION", "DESIGNER ITEM", "D-39 / Q-54 B (annex roof slab top)",
            "lintel only if the annex slab top >= +3.829 (2.80 drawn head + 0.019 tol + 0.20 + 0.06 bed + CB6 0.75); "
            "drawn bound today 3.544 .. 4.30 (R-T678-2)", "CB6 BM-GF-030 (20x75) over the drawn head +2.80"),
    "W08": ("CONDITIONAL_EXCLUSION", "DESIGNER ITEM", "D-39 / Q-54 B (annex roof slab top)",
            "lintel only if the annex slab top >= +3.816 (2.80 + 0.006 + 0.20 + 0.06 + 0.75)",
            "CB6 BM-GF-030 (20x75) over the drawn head +2.80"),
    "W11": ("CONDITIONAL_EXCLUSION", "DESIGNER ITEM", "T-207 sill / head level not drawn (height 2.20 DRAWING-CONFIRMED)",
            "REQUIRED only if the head <= 2.234 above FFL +0.30 under B9 0.75 (sill <= 0.034); a higher head leaves "
            "less than D + bed under B9", "B9 (0.75) over GF-W18"),
    "W12": ("CONDITIONAL_EXCLUSION", "DESIGNER ITEM", "T-207 sill / head level not drawn (as W11)",
            "as W11", "B9 (0.75) over GF-W18"),
    "W25": ("OPEN", "DESIGNER ITEM", "R-T228-3 F3 (1F stair-shaft landing member over W25, 'about +7.6', not printed)",
            "the landing member level and depth over W25", None),
    "W26": ("CONDITIONAL_EXCLUSION", "DESIGNER ITEM", "D-39 (2F stair-roof structural top / build-up)",
            "printed head 2.80 under the single 3.00 piece: gap 0.20 = D exactly (spare -0.06 with the bed): REQUIRED "
            "only if the structural soffit is >= 3.06; below 3.00 the piece serves the opening; between, HELD by name", "the 2F stair-roof piece over W26 (soffit 3.00)"),
    "W27": ("OPEN", "DESIGNER ITEM", "R-T228-3 F4 (2F stair-shaft member at +9.70 not printed on the shaft line)",
            "the 2F stair-shaft member level and depth over W27", None),
    "D-GF-04": (R.REQUIRED, "METHOD GAP", "R-T678-3 (END: no stopper inside the 3.00 m search)",
                "END stopper: the host run WB-FL0089-FL0090 ends 3.2703 m past the jamb at a T-junction (T-274); no "
                "merged rule gives a junction end a ceiling (Lead / Checker ruling, not an owner question)", None),
    "D-GF-05": ("OPEN", "DESIGNER ITEM", "Q-67 side-passage FFL (not printed) + START stopper WB-FL0001-FL0002:NOT_WALL "
                "not recorded", "REQUIRED if the side-passage FFL <= +0.30 (CB7 bound c_lo 2.494, spare 0.034); the "
                "START stopper (what lies 0.30 past the jamb) for the AT_MOST", None),
    "D-GF-08": ("CONDITIONAL_EXCLUSION", "DESIGNER ITEM", "D-43 (ST p.8 n.19 unsized lift tie beam over GF-W08)",
                "the lift tie beam depth and level: at the door head it serves the opening (no lintel)",
                "the lift tie beam of ST p.8 n.19 (unsized)"),
    "D-GF-09": ("OPEN", "DESIGNER ITEM", "T-581 DRAWING CONFLICT (D120 1.00 frame in a 0.90 gap) + host GF-W10 held piece",
                "the opening width (0.90 or 1.00) and the soffit over GF-W10's held piece", None),
    "D-GF-14": ("OPEN", "MEASURABLE NOW", "host GF-W30: no drawn wall piece in the T-274 run geometry, no T-644 jamb row",
                "a read of the GF-W30 run (band, pieces, both jamb stoppers) from the architectural DXF", None),
    "D-1F-01": ("OPEN", "DESIGNER ITEM", "T-227 (dome opening ring 1F-073 over 1F-W11: soffit not printed)",
                "the dome-ring soffit over 1F-W11", None),
    "D-1F-06": (R.REQUIRED, "METHOD GAP", "R-T678-3 (END on the crossing wall WB-FL0027-FL0028, 0.0733 m)",
                "END: the lintel may bear into / through the crossing wall; its far face is not a recorded stopper and "
                "no merged rule caps a junction end (Lead / Checker ruling, not an owner question)", None),
    "D-1F-09": ("OPEN", "DESIGNER ITEM", "T-227 (D-1F-09 wholly inside the east dome opening 1F-077: wall top not drawn)",
                "the top of 1F-W13 over D-1F-09", None),
    "D-2F-02": ("CONDITIONAL_EXCLUSION", "DESIGNER ITEM", "D-04 / Q-61 C(4) (BM-2F-017 unlabelled, depth not printed)",
                "REQUIRED for any BM-2F-017 depth <= 0.52 m on the drawn 2F slab-top bound 12.68 (12.68 - 9.70 - d >= "
                "2.20 + 0.20 + 0.06); the beam serves the door if d > 0.58 on that bound", "BM-2F-017 (unsized)"),
    "A-GF-01": ("OPEN", "DESIGNER ITEM", "T-238 (arched head: crown level printed nowhere, arch not dimensioned)",
                "the crown level and the arch detail; a curved head is never a straight-lintel m3 (R-T673-3)", None),
    "L-GF-01": ("OPEN", "DESIGNER ITEM", "D-45 / register LIFT LANDING DOOR LINTEL (head not printed; shaft wall RC or "
                "masonry not printed)", "the lift landing door head and the shaft wall material", None),
    "L-1F-01": ("OPEN", "DESIGNER ITEM", "D-45 / register LIFT LANDING DOOR LINTEL", "as L-GF-01", None),
    "L-2F-01": ("OPEN", "DESIGNER ITEM", "D-45 / register LIFT LANDING DOOR LINTEL", "as L-GF-01", None),
    "P-GF-01": ("OPEN", "DESIGNER ITEM", "D-45 (head drawn on no sheet, T-207 re-check)", "the P-GF-01 head level", None),
}
FORM = {"A-GF-01": "CURVED"}
WIDTH_RANGE = {"D-GF-09": ["0.90", "1.00"]}     # T-581 conflict: 0.90 gap (drawn) .. 1.00 (frame text)


def _csv(p):
    return list(csv.DictReader(Path(p).open(encoding="utf-8", newline="")))


def _f(v):
    return None if v is None else format(X(v).quantize(X("0.000001")), "f")


def owner_piece(w):
    if w is None:
        return "width not drawn: piece not chosen"
    need = X(str(w)) + 2 * R.OWNER_B_MIN
    for L in OWNER_PRECAST:
        if L >= need:
            return f"{L} m precast ({w} + 2 x 0.15 = {need})"
    return f"FLAGGED (> 4.00 m: {need})"


def blank_lintels():
    ix = json.loads(INDEX.read_text(encoding="utf-8"))
    assert ix["candidate_version"].endswith("3.0.69"), ix["candidate_version"]
    lines = ix["lines"]
    lin = [l for l in lines if l["item_code"] == "STR.CONC.LINTEL"]
    blank = [l for l in lin if l["measured_net"] is None and l["held_low"] is None and l["held_high"] is None]
    assert all(l["class"] == "HELD" for l in blank)
    by_el = {l["element_id"]: l for l in lin}
    # the neighbours' states named above are the candidate's
    assert by_el["LINTEL:D-GF-03"]["held_low"] == 0.052 and by_el["LINTEL:D-GF-03"]["held_high"] == 0.058
    assert by_el["LINTEL:D-1F-08"]["class"] == "RELEASED"
    census = {"lines": len(lin), "released": sum(1 for l in lin if l["class"] == "RELEASED"),
              "bounded": sum(1 for l in lin if l["held_low"] is not None), "blank": len(blank)}
    return blank, census


def build():
    blank, census = blank_lintels()
    assert census["blank"] == 21, census
    pf = json.loads(T650.read_text(encoding="utf-8"))["per_opening"]
    jam = {}
    for r in _csv(JAMBS):
        jam.setdefault(r["opening_id"], []).append(r)
    ext = {(r["opening_id"], r["side"]): r for r in _csv(EXT)}
    t78 = {r["opening"]: r for r in json.loads(T678.read_text(encoding="utf-8"))["lintels"]}
    t73 = {r["opening"]: r for r in json.loads(T673.read_text(encoding="utf-8"))["lintels"]}
    rows = []
    for l in sorted(blank, key=lambda x: x["element_id"]):
        oid = l["element_id"].split(":", 1)[1]
        assert oid in CLASS, oid
        assert t73[oid]["line_id"] == l["line_id"]
        p = pf[oid]
        existence, cause, ref, datum, excl = CLASS[oid]
        if existence == R.REQUIRED:      # only the two T-678 REQUIRED lines (owner door-height fallback Q-55 C)
            assert t78[oid]["existence"].startswith("REQUIRED"), oid
        ends = []
        for j in jam.get(oid, []):
            e = {"side": j["side"], "a": j["v3_available_6dp_m"], "stopper": j["stopper"],
                 "stopper_id": j["stopper_id"] or None}
            if j["stopper"] == "SEARCH_LIMIT" and (oid, j["side"]) in ext:
                x = ext[(oid, j["side"])]
                e.update(extended=x["available_6dp_m"], extended_stopper=x["stopper"])
            if j["stopper"] == "OPENING" and "CROSSING" in (j["stopper_id"] or ""):
                e["stopper"] = "CROSSING_WALL"          # not a stopper (R-T678-3): OPEN end
            if j["stopper"] == "OPENING" and (j["stopper_id"] or "").endswith(":NOT_WALL"):
                e["stopper"] = "UNRECORDED"             # T-678: START stopper not recorded
            ends.append(e)
        lintel = {"id": oid, "width_m": p["width_m"], "width_range": WIDTH_RANGE.get(oid), "B": p["B_m"],
                  "D": p["D_m"], "form": FORM.get(oid, "STRAIGHT"), "ends": ends}
        st = R.one_sided(existence=existence, lintel=lintel, neighbours=NEIGHBOURS, b_min=B_MIN, excluded_by=excl)
        rows.append({
            "opening": oid, "line_id": l["line_id"], "storey": p["storey"], "block": p["block_type"],
            "B_m": p["B_m"], "D_m": p["D_m"], "width_m": p["width_m"] if oid not in WIDTH_RANGE else WIDTH_RANGE[oid],
            "ends": [(e["side"], e["stopper"], e["stopper_id"], e["a"]) for e in ends],
            "existence": existence, "cause_class": cause, "cause_ref": ref, "deciding_datum": datum,
            "conditional_exclusion_member": excl,
            "at_least_m3": _f(st["at_least"]), "at_most_m3": _f(st["at_most"]),
            "conditional_lo_m3": _f(st["conditional_lo"]), "convention": st.get("convention"),
            "length_hi_m": _f(st.get("length_hi")), "why_no_at_most": st.get("why_no_at_most"),
            "line_after": "HELD blank (unchanged; bound beside)", "owner_manual": owner_piece(p["width_m"])})
    # family: W11 / W12 both take the full shared pier 1.1451 (ceil 1.146) as their ceiling: count it once
    w11 = next(r for r in rows if r["opening"] == "W11")
    pier_dbl = R.BR.mul(w11["B_m"], w11["D_m"], R.R73.ceil_mm("1.145100"))
    exact = [{"id": r["opening"], "at_most_exact": R.BR.mul(r["B_m"], r["D_m"], X(r["length_hi_m"]))}
             for r in rows if r["at_most_m3"]]
    fam = R.family_at_most(exact, [("W11", "W12", pier_dbl)])
    al = [r for r in rows if r["at_least_m3"]]
    counts = {}
    for r in rows:
        k = ("AT_MOST" if r["at_most_m3"] else "") + ("+AT_LEAST" if r["at_least_m3"] else "")
        counts[k or "NONE (datum named)"] = counts.get(k or "NONE (datum named)", 0) + 1
    by_cause = {}
    for r in rows:
        by_cause[r["cause_class"]] = by_cause.get(r["cause_class"], 0) + 1
    return {
        "task": "T-699", "candidate_index": "ARCH_TAKEOFF_V3.0.69 (research/agents_t687/out/LINE_INDEX_V3_0_69.json)",
        "rules": ["R-T699-1 1.0.0", "R-T673-3", "R-T678-1", "R-T678-3", "R-T696-1"], "b_min_m": str(B_MIN),
        "lintel_census_before": census, "lines": rows, "counts": counts, "by_cause": by_cause,
        "family": {"at_most_lines": len(exact), "at_most_sum_m3": _f(fam),
                   "pier_counted_once": {"W11/W12": _f(pier_dbl)},
                   "at_least_lines": [r["opening"] for r in al],
                   "at_least_sum_m3": _f(sum(X(r["at_least_m3"]) for r in al)),
                   "never_summed_with": "the candidate's released / bounded LINTEL totals (beside, not added)"},
    }


def write_md(led):
    L = ["# T-699 census: the 21 blank STR.CONC.LINTEL lines of V3.0.69 with their one-sided drawn bounds (R-T699-1)", "",
         f"lintel lines before: {led['lintel_census_before']} ; bound kinds: {led['counts']} ; causes: {led['by_cause']}",
         f"; family AT_MOST {led['family']['at_most_sum_m3']} m3 on {led['family']['at_most_lines']} lines (W11 / W12 "
         f"pier once: -{led['family']['pier_counted_once']['W11/W12']}); AT_LEAST "
         f"{led['family']['at_least_sum_m3']} m3 on {', '.join(led['family']['at_least_lines'])}", "",
         "| # | line | opening | B x D | width | existence | AT_LEAST | AT_MOST | if REQUIRED (beside) | convention | "
         "cause | deciding datum | excluded if | owner manual |", "|" + "---|" * 14]
    for i, r in enumerate(led["lines"], 1):
        L.append(f"| {i} | {r['line_id']} | {r['opening']} | {r['B_m']} x {r['D_m']} | {r['width_m']} | "
                 f"{r['existence']} | {r['at_least_m3'] or '-'} | {r['at_most_m3'] or ('OPEN: ' + (r['why_no_at_most'] or ''))} | "
                 f"{r['conditional_lo_m3'] or '-'} | {r['convention'] or '-'} | {r['cause_class']}: {r['cause_ref']} | "
                 f"{r['deciding_datum']} | {r['conditional_exclusion_member'] or '-'} | {r['owner_manual']} |")
    return "\n".join(L) + "\n"


def main(argv):
    led = build()
    if "--write" in argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(led, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        OUT_MD.write_text(write_md(led), encoding="utf-8")
    print(json.dumps({k: led[k] for k in ("counts", "by_cause", "family")}, indent=1))
    for r in led["lines"]:
        print(r["opening"], r["existence"], r["at_least_m3"], r["at_most_m3"], r["conditional_lo_m3"], r["convention"],
              (r["why_no_at_most"] or "")[:90])


if __name__ == "__main__":
    main(sys.argv[1:])
