"""T-683 development-villa run: concrete reconciliation statement ROUND 2 on candidate V3.0.66 (R-T679-1 unchanged +
R-T683-1 stale census classes, R-T683-2 scope bridge of CONC.COLUMN, R-T683-3 reference arithmetic of CONC.BEAM).

Reads committed files only (no drawing, no client data): the V3.0.66 line index (T-677), the family master 1.67.0 whose
candidate census was built on it, the merged censuses (T-669 / T-673 / T-678, via t679_alsenan.causes), the merged
integration packages that wired concrete lines after those censuses (T-668 V3.0.64, T-671 V3.0.65, T-677 V3.0.66), the
key map T001B, the normalised reference cover totals, the merged scorecard V12 (T-635) and this task's own
out/T683_REFERENCE_ARITH.json (numbers read from the private workbook copy by t683_reference_arith.py).

    python3 -I research/agents_t683/t683_alsenan.py [--write] [--check]

Development villa: not an accuracy claim; nothing released; no quantity changed; the reference is never a quantity.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t679"))
import t679_alsenan as A  # noqa: E402
import t679_rules as R  # noqa: E402
import t683_rules as S  # noqa: E402

INDEX = "research/agents_t677/out/LINE_INDEX_V3_0_66.json"
MASTER = "rules/coverage/BOQ_FAMILY_MASTER_1.67.0.json"
ARITH = "research/agents_t683/out/T683_REFERENCE_ARITH.json"
PACKAGES = [("T-668", "research/agents_t668/summary_t668.json"), ("T-671", "research/agents_t671/summary_t671.json"),
            ("T-677", "research/agents_t677/summary_t677.json")]
OUT_JSON, OUT_MD = HERE / "out" / "T683_STATEMENT.json", HERE / "out" / "T683_STATEMENT.md"
PREFIX, UNIT, TRADE = "STR.CONC", "m3", "CONCRETE"

# candidate each census read (t679_alsenan.causes 'source' prefix -> version)
CENSUS_VERSION = {"T-669": "ARCH_TAKEOFF_V3.0.63", "T-673": "ARCH_TAKEOFF_V3.0.64", "T-678": "ARCH_TAKEOFF_V3.0.65",
                  "T-667": "ARCH_TAKEOFF_V3.0.65", "T-642": "ARCH_TAKEOFF_V3.0.65"}

# R-T683-1 restatements: the residual cause that keeps each wired line HELD, quoted from the merged text of the census
# and of the package that wired it (T-673 s.3 status line; T-677 s.1 / s.3; T-669 census 'named'; Q-28).
_LINTEL = ("bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, "
           "high = the drawn jamb ceilings; the length actually cast between them and the end connection at a column / "
           "cross wall are not printed (T-516 RFI), heads drawn not printed (N09 'not to scale')")
LINTELS = {"L-4a12b89454e48ac510dc": "A-1F-01 (T-650 bound)", "L-2efe48097978cae5fc99": "P-1F-01 (T-650 bound)",
           "L-441ae5fe85351347aff0": "W05", "L-f269fabb74f505755492": "W06 (low = high: deficit end 0.000)",
           "L-ed7aadd01d9daa9559a9": "W07", "L-786344670c0002b31478": "W09",
           "L-882717b0c35a87e363ef": "W10 (START 0.100 deficit at a column)", "L-53ef44d8c490d1341b93": "W16",
           "L-6057028f3f666538a007": "W19 (pier side 0.40)", "L-6692d02cd6cd25120300": "W20 (pier side 0.40)",
           "L-dd5b41a7af885e96f797": "W21", "L-f68444edf483bc1d87d4": "W22 (low = high)", "L-bf76c17309c92605e174": "W23",
           "L-40e8c2597de12644e8e2": "W24", "L-005334b6998987164a5d": "W28", "L-aca2db3c2b29719328c7": "W29 (low = high)"}
RESTATE = {lid: {"cause_class": "DESIGNER ITEM", "named": f"lintel {m}: {_LINTEL}",
                 "source": "T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66)"}
           for lid, m in LINTELS.items()}
RESTATE["L-7d90a0feed2537221f16"] = {
    "cause_class": "DESIGNER ITEM",
    "named": "W19 / W20 pier remainder 0 .. 0.2 x 0.2 x (0.875 - 2 x 0.40) = 0.003: which of the two lintels runs over "
             "the 0.075 m is not drawn (owned once, never inside either high; T-677 s.1 ADD_SHARED, ends T-516 RFI)",
    "source": "T-683 from T-677 s.1 / s.3 (line added by T-677; no census row could exist)"}
RESTATE["L-061e18cf35a4b6b33d68"] = {
    "cause_class": "DESIGNER ITEM",
    "named": "ST-03 E1 waist slab not drawn (S-9); the steps part AT_LEAST 0.355017 is beside (T-677 LOWER_ONLY, "
             "T-258 DRAWING-CONFIRMED risers)",
    "source": "T-683 from T-673 stairs row + T-677 s.1 (the split was wired as a floor beside)"}
RESTATE["L-6290a9f3d93f38cd46d6"] = {
    "cause_class": "DESIGNER ITEM",
    "named": "boundary band 5.6392 .. 11.0328 wired by T-668: section B.W 20x60 vs typical 20x40 (designer RFI, Q-28; "
             "owner provisional A 8.4588 beside, not a released value) and band founding level 'AS PER EXCAVATION "
             "DEPTH' not printed",
    "source": "T-683 from the T-669 census row ('wire in T-668; then Q-28 keeps it bounded') + Q-28"}

# F-T679-1: the two V3.0.65 HELD lines with no census row: their census row (cause + the row that closes / wires it).
F_T679_1 = [
    OrderedDict(line_id="L-893c3db13b14dc38625e", element="pool blinding", state_v3_0_66="HELD blank; AT_LEAST "
                "0.915529 m3 beside (T-668 ADD_LOWER_ONLY: (11.851050 - 2.695761) x 0.10)", cause_class="DESIGNER ITEM",
                cause="C4 projection beyond the 0.10 wrap drawn, not dimensioned; C6 founding levels of F8 / F4 / FN vs "
                      "pool formation -1.50 not printed (one blinding layer or two) - T-667 s.2 designer list",
                wiring="already wired (T-668, V3.0.64) as a floor; nothing left to wire. Closes only on the designer "
                       "answer to C4 / C6, then a lane S re-measure row + a lane I row. No owner question (ERS 2.7: a "
                       "designer item, both items already on the designer list)"),
    OrderedDict(line_id="L-bef35462630d4b76596f", element="beam BAND0030.2 depth companion",
                state_v3_0_66="HELD bounded 0 .. 0.025 m3 (T-671 ADD_COMPANION: 0.100 x (0.75 - 0.50))",
                cause_class="DESIGNER ITEM",
                cause="no beam mark printed on the strip: depth B4 0.50 (released part 0.05) vs B7 0.75 (FR-T642-2, "
                      "T-642)", wiring="already wired (T-671, V3.0.65); closes on the designer mark for the strip. No "
                      "owner question (designer item)"),
]

# R-T683-2: CONC.COLUMN cover total 39.7515 split by the reference's own sub-totals (walls-and-columns sheet; numbers
# re-read this run from the private workbook copy, agree with T-551 / T-628).
COLUMN_COMPONENTS = [
    {"name": "lift pit walls (his 'walls' sub-total: ring 8 x 0.20 x 1.50)", "reference": "2.4",
     "engine": {"item_codes": ["STR.CONC.LIFT"], "element_ids": ["LIFT_PIT:WALLS"]},
     "note": "T-628 L0 / L1 (Checker RE-MEASURED): ring 1.600 m2 = net 1.100 (pit wall, this line, HELD D-43: pit depth "
             "'as per lift manufacturer') + 0.500 of four column pieces the engine NECK lines own (his neck rows carry "
             "them too: SCOPE_DOUBLE 0.75 ENGINE_RIGHT); 1.65 = 1.10 x his 1.50 HELD"},
    {"name": "necks (his neck sub-total)", "reference": "8.805",
     "engine": {"item_codes": ["STR.CONC.NECK"], "element_ids": None},
     "note": "T-551 necks: HELD 8.805 (36 lines; his share inside the engine bound on every line his rows carry)"},
    {"name": "columns GF + 1F + 2F (his three storey sub-totals 17.4375 + 7.728 + 3.381)", "reference": "28.5465",
     "engine": {"item_codes": ["STR.CONC.COLUMN"], "element_ids": None},
     "note": "T-551/columns@V12 class split quoted below (ENGINE_RIGHT 1.522, RULE_DIFFERENCE -2.66625, HELD 10.34925, "
             "UNRESOLVED -0.435)"},
]


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def packages() -> list[dict]:
    out = []
    for task, rel in PACKAGES:
        d = load(rel)
        out.append({"task": task, "base_version": d["extends"],
                    "rows": [r for r in d["rows"] if r["item_code"].startswith(PREFIX)], "file": rel})
    return out


def census_version(src: str) -> str:
    for k, v in CENSUS_VERSION.items():
        if src.startswith(k):
            return v
    raise R.Refused(f"census source {src!r} has no candidate version")


def build() -> dict:
    idx, master = load(INDEX), load(MASTER)
    index_sha = A.sha(ROOT / INDEX)
    cz0, supp = A.causes(idx["candidate_version"])
    lines = [ln for ln in idx["lines"] if ln["item_code"].startswith(PREFIX)]
    by_id = {ln["line_id"]: ln for ln in lines}
    held = {k: v for k, v in by_id.items() if v["class"] == R.HELD}
    cv = {lid: census_version(c["source"]) for lid, c in cz0.items()}
    pk = packages()
    cz, restated, floors = S.restate(cz0, cv, held, pk, RESTATE)
    agg = R.aggregate(lines, master["families"], cz, prefix=PREFIX, unit=UNIT)
    census_rows = A.check_census(agg["families"], master, index_sha)
    fam_meta = {f["code"]: f for f in master["families"]}
    families = OrderedDict()
    for code, acc in agg["families"].items():
        v = R.scope_view(acc)
        v["item"] = fam_meta[code]["item_en"]
        families[code] = v
    held_rows = []
    for ln in lines:
        if ln["class"] != R.HELD:
            continue
        c = cz[ln["line_id"]]
        held_rows.append(OrderedDict(
            family=agg["owner"][ln["item_code"]], line_id=ln["line_id"], item_code=ln["item_code"],
            element_id=ln["element_id"], bound=[R.s(R.D(ln["held_low"])), R.s(R.D(ln["held_high"]))]
            if ln["held_low"] is not None else None, cause_class=c["cause_class"], cause=c["named"],
            cause_source=c["source"]))
    held_rows.sort(key=lambda r: (r["family"], r["item_code"], r["line_id"]))
    km = load(A.KEYMAP)
    keys = [k for k in km["keys"] if k["trade"] == TRADE]
    refs = {r["id"]: r for r in load(A.BENCH)["records"] if r.get("row_kind") == "COVER_TOTAL"}
    cmp_rows = R.compare(keys, refs, agg["codes"], unit=UNIT)
    vc = A.verdict_causes(load(A.SCORECARD))
    for row in cmp_rows:
        row["causes_from_merged_verdicts"] = vc.get(row["key"]) or (
            "UNRESOLVED: no merged reconciliation section for this key (scorecard V12 has none); nothing classed here")
    # R-T683-2 bridge of CONC.COLUMN
    col_key = next(k for k in keys if k["key"] == "CONC.COLUMN")
    br = S.bridge("CONC.COLUMN", refs[col_key["reference_id"]]["qty"], COLUMN_COMPONENTS, lines)
    nc = S.not_comparable(lines, col_key["item_codes"], br, COLUMN_COMPONENTS)
    # R-T683-3 beam arithmetic (numbers from the private workbook, committed as numbers only)
    ar = load(ARITH)
    beam = next(r for r in cmp_rows if r["key"] == "CONC.BEAM")
    ba = ar["keys"]["CONC.BEAM"]["arithmetic"]
    rel = R.D(beam["engine"]["released"]["m3"])
    beam_ar = OrderedDict(
        cover_total=ba["cover_total"], his_row_sum=ba["row_sum"], cover_minus_rows=ba["cover_minus_rows"],
        cause=("his 1F sub-total sums its range from the SECOND 1F row: the first 1F row (0.20 x 0.40 x 1.60 = "
               "0.128 m3) is in his 1F carry-forward cell but not in the 1F sub-total the cover total adds "
               "(R-T683-3 OMITTED_ROW); every other row of the eight keyed concrete cover totals is reached exactly "
               "once (own audit of all eight chains)"),
        reproduces="T-545 'his rows sum to 66.093875' (T-545 s.1, BM-ARITH) reproduced from an own read of the "
                   "workbook formulas, not from the T-545 output",
        engine_released=R.s(rel), cover_minus_released=R.s(R.sub(R.D(ba["cover_total"]), rel)),
        rows_minus_released=R.s(R.sub(R.D(ba["row_sum"]), rel)),
        class_="REFERENCE ARITHMETIC: no engine verdict, no quantity moved; the cover total stays the keyed value; % "
               "stays suppressed (26 HELD beam lines)")
    st = OrderedDict()
    st["schema"] = "URBAN_T683_CONCRETE_STATEMENT_V1"
    st["task"] = "T-683"
    st["rules"] = ["R-T679-1 1.0.0 (research/agents_t679/t679_rules.py, unchanged)",
                   "R-T683-1 / -2 / -3 1.0.0 (research/agents_t683/t683_rules.py)"]
    st["not_claimed"] = ("development villa; not an accuracy claim; nothing released (the released default V2.9 + route "
                         "G is unchanged); no quantity changed; the reference is never a quantity and agreement is "
                         "never proof")
    st["candidate"] = OrderedDict(version=idx["candidate_version"], index=INDEX, index_sha256=index_sha,
                                  lines_sha256=idx["inputs"]["lines"], master=MASTER,
                                  master_census_agrees=len(census_rows))
    st["inputs_sha256"] = OrderedDict((p, A.sha(ROOT / p)) for p in
                                      [A.KEYMAP, A.BENCH, A.T669, A.T673, A.T678, A.SCORECARD, ARITH]
                                      + [rel_ for _, rel_ in PACKAGES])
    st["trade_total"] = R.scope_view(agg["total"])
    st["families"] = families
    st["item_codes"] = OrderedDict((c, R.scope_view(a)) for c, a in agg["codes"].items())
    st["stale_classes_restated"] = restated
    st["floors_beside"] = OrderedDict(
        rule="R-T683-1 (e): AT_LEAST values of blank lines, never in the bounded low or the engine range",
        lines=floors)
    tot = Decimal(0)
    for f in st["floors_beside"]["lines"]:
        tot = R.add(tot, R.D(f["at_least"]))
    st["floors_beside"]["sum_at_least"] = R.s(tot)
    st["f_t679_1_census_rows"] = F_T679_1
    st["held_lines"] = held_rows
    st["measurable_now_still_held"] = [OrderedDict(line_id=r["line_id"], element_id=r["element_id"],
                                                   wiring_row="T-682 (CLAIMED worker 3, lane I)")
                                       for r in held_rows if r["cause_class"] == "MEASURABLE NOW"]
    st["reference_apart"] = OrderedDict(
        rule="difference = reference - engine released; % only where the key holds no HELD line (R-T613-1 (g)); "
             "causes quoted from the merged scorecard V12 sections, scored on its own candidate (not re-classed)",
        keys=cmp_rows, not_keyed_item_codes=R.not_keyed(agg["codes"], keys),
        column_bridge=br, column_bridge_not_comparable=nc, beam_arithmetic=beam_ar,
        key_map_proposal=OrderedDict(
            status="PROPOSED, not applied (R-T683-2 (d)): a key-map version is a Lead / lane I decision",
            change="CONC.COLUMN answers STR.CONC.NECK + STR.CONC.COLUMN + STR.CONC.LIFT element LIFT_PIT:WALLS only; "
                   "STR.CONC.LIFT element LIFT_TIE_BEAM:GF stays not keyed (no row of his on any sheet, T-545 s.2)",
            needs="element-level key scope in tools/alsenan_keymap.py / alsenan_scoreboard.py (today item-code level: "
                  "keying the whole STR.CONC.LIFT code would put the tie beam into the column key)",
            effect_today="none on the numbers: both STR.CONC.LIFT lines are HELD blank, the key's % is already "
                         "suppressed; the scope of the key becomes like for like"))
    return st


def md(st: dict) -> str:
    L = []
    c = st["candidate"]
    L.append("# T-683 Concrete reconciliation statement round 2 (R-T679-1 + R-T683-1..3)\n")
    L.append(f"Candidate {c['version']}: `{c['index']}` sha256 {c['index_sha256'][:12]}..., lines sha "
             f"{c['lines_sha256'][:8]}; master `{c['master']}` census agrees on {c['master_census_agrees']} families. "
             f"{st['not_claimed']}.\n")
    L.append("## Engine side: family subtotal -> trade total (m3; buckets never summed together)\n")
    L.append("| Family | Item | Lines | Released n / m3 | Held bounded n / low .. high | Held blank n (DESIGNER / "
             "OPEN BOUND / MEASURABLE NOW) | Excluded n | Engine range | Verified whole / component |")
    L.append("|---|---|---|---|---|---|---|---|---|")

    def row(name, item, v):
        bb = v["held_blank"]["by_cause"]
        return (f"| {name} | {item} | {v['lines']} | {v['released']['lines']} / {v['released']['m3']} | "
                f"{v['held_bounded']['lines']} / {v['held_bounded']['low']} .. {v['held_bounded']['high']} | "
                f"{v['held_blank']['lines']} ({bb['DESIGNER ITEM']} / {bb['OPEN BOUND']} / {bb['MEASURABLE NOW']}) | "
                f"{v['excluded']['lines']} | {v['engine_range'][0]} .. {v['engine_range'][1]} | "
                f"{v['verified_share']['whole']} ({v['verified_share']['whole_m3']}) / "
                f"{v['verified_share']['component']} ({v['verified_share']['component_m3']}) |")
    for code, v in st["families"].items():
        L.append(row(code, v["item"], v))
    L.append(row("**TRADE**", "all STR.CONC", st["trade_total"]))
    fb = st["floors_beside"]
    L.append(f"\nFloors beside (blank lines, never in the range): "
             + "; ".join(f"{f['line_id'][:10]} >= {f['at_least']} ({f['source']})" for f in fb["lines"])
             + f"; sum {fb['sum_at_least']} m3.\n")
    L.append(f"## Stale census classes restated (R-T683-1): {len(st['stale_classes_restated'])} lines\n")
    L.append("| Line | Element | Wired by | Class before (source) | Class after | Residual |")
    L.append("|---|---|---|---|---|---|")
    for r in st["stale_classes_restated"]:
        L.append(f"| {r['line_id'][:10]} | {r['element_id']} | {r['wired_by']} | {r['class_before']} "
                 f"({r['source_before'][:22]}) | {r['class_after']} | {r['residual'][:150]} |")
    L.append("\n## F-T679-1: census rows of the two lines that had none\n")
    for r in st["f_t679_1_census_rows"]:
        L.append(f"- {r['line_id'][:10]} {r['element']}: {r['state_v3_0_66']}; {r['cause_class']}: {r['cause']}. "
                 f"Wiring: {r['wiring']}.")
    L.append("\n## Reference comparison, apart (freelancer cover totals, key map T001B)\n")
    L.append("| Key | Reference m3 | Engine released m3 | Engine range m3 | Held (bounded + blank) | Ref - released m3 "
             "| % | Verified whole |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in st["reference_apart"]["keys"]:
        e = r["engine"]
        L.append(f"| {r['key']} ({', '.join(r['item_codes'])}) | {A.d6(r['reference'])} | {e['released']['m3']} | "
                 f"{e['engine_range'][0]} .. {e['engine_range'][1]} | {e['held_bounded']['lines']} + "
                 f"{e['held_blank']['lines']} | {A.d6(r['difference_ref_minus_released'])} | "
                 f"{r['pct_of_reference'] if r['pct_of_reference'] is not None else 'suppressed'} | "
                 f"{e['verified_share']['whole']} |")
    L.append("\nCauses quoted from the merged scorecard V12 sections (m3 by class):\n")
    for r in st["reference_apart"]["keys"]:
        cz = r["causes_from_merged_verdicts"]
        if isinstance(cz, str):
            L.append(f"- {r['key']}: {cz}")
        else:
            for sct in cz:
                bc = ", ".join(f"{k} {v}" for k, v in sct["by_class"].items() if Decimal(v) != 0)
                L.append(f"- {r['key']} <- {sct['section_id']} (ref {sct['reference_total']}, engine "
                         f"{sct['engine_valued']}): {bc or 'all classes 0'}")
    br = st["reference_apart"]["column_bridge"]
    L.append(f"\n## F-T679-2: CONC.COLUMN scope bridge (R-T683-2), cover {br['reference']} m3\n")
    L.append("| Component | Ref m3 | Engine scope | Released n / m3 | Bounded n / low .. high | Blank n | Ref - released "
             "| Status |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in br["components"]:
        e, sc = r["engine"], r["engine_scope"]
        scope = ", ".join(sc["item_codes"]) + (f" [{', '.join(sc['element_ids'])}]" if sc.get("element_ids") else "")
        L.append(f"| {r['component']} | {r['reference']} | {scope} | {e['released']['lines']} / {e['released']['m3']} | "
                 f"{e['held_bounded']['lines']} / {e['held_bounded']['low']} .. {e['held_bounded']['high']} | "
                 f"{e['held_blank']['lines']} | {r['difference_ref_minus_released']} | {r['status']} |")
    for r in br["components"]:
        L.append(f"- {r['component']}: {r['note']}")
    nc = st["reference_apart"]["column_bridge_not_comparable"]
    L.append(f"- NOT_COMPARABLE (engine, no reference component): "
             + (", ".join(f"{x['line_id'][:10]} {x['element_id']} ({x['cls']})" for x in nc) or "none"))
    kp = st["reference_apart"]["key_map_proposal"]
    L.append(f"- Key map: {kp['status']}. {kp['change']}. Needs {kp['needs']}. Effect today: {kp['effect_today']}.")
    ba = st["reference_apart"]["beam_arithmetic"]
    L.append("\n## F-T679-3: CONC.BEAM reference arithmetic (R-T683-3)\n")
    L.append(f"Cover {ba['cover_total']} vs his rows {ba['his_row_sum']}: cover - rows = {ba['cover_minus_rows']} m3. "
             f"{ba['cause']}. {ba['reproduces']}. Engine released {ba['engine_released']}: cover - released "
             f"{ba['cover_minus_released']}, rows - released {ba['rows_minus_released']}. {ba['class_']}.\n")
    L.append(f"Not keyed (no reference row): {', '.join(st['reference_apart']['not_keyed_item_codes'])}.\n")
    L.append(f"MEASURABLE NOW still HELD (wiring row T-682): {len(st['measurable_now_still_held'])} lines.\n")
    L.append(f"## HELD lines ({len(st['held_lines'])}), each with its cause\n")
    L.append("| Family | Line | Code | Bound m3 | Cause class | Cause | Source |")
    L.append("|---|---|---|---|---|---|---|")
    for h in st["held_lines"]:
        b = f"{h['bound'][0]} .. {h['bound'][1]}" if h["bound"] else "blank"
        cause = str(h["cause"]).replace("|", "/")[:160]
        L.append(f"| {h['family']} | {h['line_id'][:10]} | {h['item_code'][9:]} | {b} | {h['cause_class']} | {cause} | "
                 f"{h['cause_source']} |")
    return "\n".join(L) + "\n"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    st = build()
    j, m = A.dumps(st), md(st)
    if a.write:
        OUT_JSON.write_text(j, encoding="utf-8")
        OUT_MD.write_text(m, encoding="utf-8")
    if a.check:
        ok = OUT_JSON.read_text(encoding="utf-8") == j and OUT_MD.read_text(encoding="utf-8") == m
        print("T683 check", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    t = st["trade_total"]
    print(f"{st['candidate']['version']}: released {t['released']['lines']} / {t['released']['m3']} m3; bounded "
          f"{t['held_bounded']['lines']} {t['held_bounded']['low']} .. {t['held_bounded']['high']}; blank "
          f"{t['held_blank']['lines']} {t['held_blank']['by_cause']}; bounded by cause {t['held_bounded']['by_cause']}; "
          f"excluded {t['excluded']['lines']}; restated {len(st['stale_classes_restated'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
