"""T-694 development-villa run: concrete reconciliation statement ROUND 3 on the candidate of record V3.0.68
(concrete = V3.0.67, T-682) + the PROPOSED 'after T-693' column from the T-689 ledger + the T-689 register gaps.

Reads committed files only: the V3.0.68 line index (T-672), master 1.69.0, the T-683 statement (V3.0.66 causes,
Checker-passed), the integration packages that wired concrete lines (T-668 / T-671 / T-677 / T-682), the T-689 ledger,
the key map T001B, the normalised reference cover totals, the merged scorecard V12 and T-683's reference arithmetic,
and this task's out/T694_OWN_READ.json (values only, read from the private DXF copy by t694_extract.py).

    python3 -I research/agents_t694/t694_alsenan.py [--write] [--check]

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
sys.path.insert(0, str(ROOT / "research" / "agents_t683"))
import t679_alsenan as A  # noqa: E402
import t679_rules as R  # noqa: E402
import t683_rules as S  # noqa: E402
import t683_alsenan as P  # noqa: E402
import t694_rules as T  # noqa: E402

INDEX = "research/agents_t672/out/LINE_INDEX_V3_0_68.json"
INDEX_67 = "research/agents_t682/out/LINE_INDEX_V3_0_67.json"
MASTER = "rules/coverage/BOQ_FAMILY_MASTER_1.69.0.json"
T683 = "research/agents_t683/out/T683_STATEMENT.json"
T689 = "research/agents_t689/out/T689_HELD_RANGES.json"
OWN = "research/agents_t694/out/T694_OWN_READ.json"
PACKAGES = P.PACKAGES + [("T-682", "research/agents_t682/summary_t682.json")]
OUT_JSON, OUT_MD = HERE / "out" / "T694_STATEMENT.json", HERE / "out" / "T694_STATEMENT.md"
PREFIX, UNIT, TRADE = "STR.CONC", "m3", "CONCRETE"
CAUSE_VERSION = "ARCH_TAKEOFF_V3.0.66"  # the T-683 statement read V3.0.66

# R-T683-1 restatements of the 11 lines T-682 wired (their T-683 class was MEASURABLE NOW = 'wire it'); residual
# causes quoted from T-682 s.0 / s.3 and T-678 (merged), the D-numbers from DESIGNER_CLARIFICATIONS.
_LB = ("bound wired by T-682 (R-T678-1 / -3, T-678 ledger): low = opening + 0.40 bearing at each end with >= 0.40 drawn, "
       "high = the drawn ceilings; the cast length between them and the end connection are not printed (T-516 RFI)")
_LA = "; existence on the owner door-height fallback 2.20 (Q-55 C, ASSUMED - OWNER-APPROVED, re-run trigger in the line)"
_LO = ("LOWER_ONLY wired by T-682: one end has no recorded stopper within the search limit (R-T678-3), so its high end "
       "is OPEN; the floor beside is the existence-required minimum")
LINTEL_682 = {
    "L-a7b8b292503ae1bf6c77": ("D-1F-05", "DESIGNER ITEM", _LB + _LA),
    "L-9ec762c0bd529b924f33": ("D-1F-06", "OPEN BOUND", _LO + _LA),
    "L-1a07849115af938b4a72": ("D-GF-01", "DESIGNER ITEM", _LB + _LA),
    "L-71998da6340be871d0af": ("D-GF-02", "DESIGNER ITEM", _LB + _LA),
    "L-a7848a35fb4329e09d10": ("D-GF-03", "DESIGNER ITEM", _LB + _LA),
    "L-274b112580029084b80e": ("D-GF-04", "OPEN BOUND", _LO + _LA),
    "L-fd68db051119ea0266ee": ("D-GF-07", "DESIGNER ITEM", _LB),
    "L-3af715c6e83364208ad0": ("W01", "DESIGNER ITEM", _LB),
    "L-47882fa3a0d9cdcc122e": ("W13", "DESIGNER ITEM", _LB),
}
RESTATE = {lid: {"cause_class": c, "named": f"lintel {m}: {n}",
                 "source": "T-694 restatement of T-682 s.0 / s.3 (MEASURABLE NOW = 'wire it', done in V3.0.67)"}
           for lid, (m, c, n) in LINTEL_682.items()}
RESTATE["L-541c7e565bb93ecdb78b"] = {
    "cause_class": "DESIGNER ITEM",
    "named": "PC-2F: section drawn 0.20 x 0.40 (FFRS 77B, SFRS 778) vs its own leader text FFRS 77C 'P.C 20x50' "
             "(T-694 own read: the leader reaches 77B) -> proposed D-66 addition; top datum D-39 (2F roof slab top not "
             "printed). Bound 0.20 x 0.40 x 2.28 .. 0.20 x 0.50 x 3.50 wired by T-682",
    "source": "T-694 restatement of T-682 s.2 + T-689 s.3 (register gap F-T689-2)"}
RESTATE["L-fad18af6e7139a5e99d1"] = {
    "cause_class": "DESIGNER ITEM",
    "named": "annex C3 (GFRS 353 drawn 0.25 x 0.50 = schedule C3 GR 25 x 50, AGREE): top datum only, the annex roof "
             "slab top is not printed (D-39 / Q-54 B); low from R-T678-2 s_lo 3.544, high finished +4.30. No section "
             "cause (T-694 F-T694-2)",
    "source": "T-694 restatement of T-682 s.2 + T-678 s.1 + T-566 registration"}

# R-T694-4 inputs: designer register lists (DESIGNER_CLARIFICATIONS D-66 as registered) and the cause rows of the
# T-689 ledger with the readings of each SECTION cause (outline vs print, m2).
D66 = {"GFRS 347", "GFRS 359", "GFRS 344", "FFRS 691", "FFRS 676", "FFRS 697", "FFRS 673", "FFRS 694", "FFRS 685",
       "FFRS 688", "FFRS 68E", "FFRS 679", "FFRS 667"}
MEMBER_REF = {  # line -> drawn outline (T-689 table / T-566 registration / T-220)
    "L-9f5a647014bbf83359f9": ("GFRS 34A", ["0.08", "0.10"]), "L-c0b3340a906c2c7650f8": ("GFRS 34D", ["0.08", "0.10"]),
    "L-e6c1c9a7feec10f64975": ("GFRS 356", ["0.08", "0.10"]), "L-694a75c84dd6e4bb4491": ("GFRS 350", ["0.08", "0.125"]),
    "L-bc01297b1c4a4c45a15f": ("SFRS 415", ["0.12", "0.10"]), "L-541c7e565bb93ecdb78b": ("FFRS 77B", ["0.08", "0.10"]),
    "L-fad18af6e7139a5e99d1": ("GFRS 353", ["0.125", "0.125"]),
}

# Checker re-measure list: three lines no Checker has re-measured before (statement work only checked by totals)
CHECKER_LIST = [
    ("L-541c7e565bb93ecdb78b", "PC-2F section association: text FFRS 77C 'P.C 20x50' with leader 77F; the leader far end "
     "is 298 mm from outline 77B (0.20 x 0.40) and 2,652 mm from the next outline; the text itself is 348 mm from 67C "
     "(0.20 x 0.50, the 1F C2); compare 544 / 545 -> 329 and 548 / 549 -> 386 (311 mm each)"),
    ("L-bc01297b1c4a4c45a15f", "SFRS 415 drawn 0.60 x 0.20 (schedule C5 2ND 20 x 50): no size text and no dimension "
     "within 0.60 m (only 79F '4ø16/Top', a slab bar text, 434 mm)"),
    ("L-694a75c84dd6e4bb4491", "GFRS 350 drawn 0.40 x 0.20 (schedule C3 GR 25 x 50): no text and no dimension within 0.60 m"),
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


def view(agg_acc) -> dict:
    return R.scope_view(agg_acc)


def statement(lines, master, cz):
    agg = R.aggregate(lines, master["families"], cz, prefix=PREFIX, unit=UNIT)
    fam_meta = {f["code"]: f for f in master["families"]}
    fams = OrderedDict()
    for code, acc in agg["families"].items():
        v = view(acc)
        v["item"] = fam_meta[code]["item_en"]
        fams[code] = v
    return agg, fams


def build() -> dict:
    idx, idx67, master = load(INDEX), load(INDEX_67), load(MASTER)
    index_sha = A.sha(ROOT / INDEX)
    lines = [ln for ln in idx["lines"] if ln["item_code"].startswith(PREFIX)]
    l67 = [ln for ln in idx67["lines"] if ln["item_code"].startswith(PREFIX)]
    if lines != l67:
        raise T.Refused("V3.0.68 STR.CONC lines differ from V3.0.67 (the statement says concrete = V3.0.67)")
    parts = T.partition(idx["lines"], prefix=PREFIX, unit=UNIT)  # R-T694-1 on the whole index
    t683 = load(T683)
    cz0 = {h["line_id"]: {"cause_class": h["cause_class"], "named": h["cause"], "source": h["cause_source"]}
           for h in t683["held_lines"]}
    by_id = {ln["line_id"]: ln for ln in lines}
    held = {k: v for k, v in by_id.items() if v["class"] == R.HELD}
    cv = {lid: CAUSE_VERSION for lid in cz0}
    cz, restated, floors = S.restate(cz0, cv, held, packages(), RESTATE)
    agg, families = statement(lines, master, cz)
    census_rows = A.check_census(agg["families"], master, index_sha)
    trade = view(agg["total"])
    pt = T.totals(parts)
    for k in ("released", "held_bounded"):
        for f in pt[k]:
            if f != "lines" and pt[k][f] != trade[k][f if f != "m3" else "m3"]:
                raise T.Refused(f"R-T694-1 totals {k}.{f} {pt[k][f]} != R-T679-1 {trade[k][f]}")
        if pt[k]["lines"] != trade[k]["lines"]:
            raise T.Refused(f"R-T694-1 {k} line count differs")
    # before (V3.0.66, T-683) -> after (V3.0.68) by line id
    before = t683["trade_total"]
    l66 = {ln["line_id"]: ln for ln in load(P.INDEX)["lines"] if ln["item_code"].startswith(PREFIX)}
    moved = []
    dlo = dhi = Decimal(0)
    for lid, ln in by_id.items():
        o = l66[lid]
        if (o["class"], o["held_low"], o["held_high"], o["measured_net"]) != (
                ln["class"], ln["held_low"], ln["held_high"], ln["measured_net"]):
            if o["class"] != ln["class"] or o["measured_net"] != ln["measured_net"]:
                raise T.Refused(f"{lid}: class / released number moved V3.0.66 -> V3.0.68")
            moved.append(OrderedDict(line_id=lid, element_id=ln["element_id"], code=ln["item_code"],
                                     before="blank" if o["held_low"] is None else [o["held_low"], o["held_high"]],
                                     after=[ln["held_low"], ln["held_high"]], cause_class=cz[lid]["cause_class"]))
            dlo += R.D(ln["held_low"]) - (R.D(o["held_low"]) if o["held_low"] is not None else 0)
            dhi += R.D(ln["held_high"]) - (R.D(o["held_high"]) if o["held_high"] is not None else 0)
    if set(l66) != set(by_id):
        raise T.Refused("line set changed V3.0.66 -> V3.0.68")
    chk = OrderedDict(
        released=f"{before['released']['m3']} -> {trade['released']['m3']}",
        bounded=f"{before['held_bounded']['lines']} {before['held_bounded']['low']} .. {before['held_bounded']['high']} "
                f"-> {trade['held_bounded']['lines']} {trade['held_bounded']['low']} .. {trade['held_bounded']['high']}",
        delta_low=T.s6(dlo), delta_high=T.s6(dhi),
        blank=f"{before['held_blank']['lines']} -> {trade['held_blank']['lines']}")
    if R.D(before["held_bounded"]["low"]) + dlo != R.D(trade["held_bounded"]["low"]) or \
            R.D(before["held_bounded"]["high"]) + dhi != R.D(trade["held_bounded"]["high"]):
        raise T.Refused("before + line moves != after")
    # PROPOSED column 'after T-693' from the T-689 ledger (R-T694-2)
    t689 = load(T689)
    mv = []
    for r in t689["lines"]:
        if r["before"] != r["after"]:
            mv.append({"line_id": r["line_id"], "before": r["before"], "after": r["after"],
                       "source": "T-689 R-T689-1 (B8 joint, merged 66ffd421)"})
    for r in t689["blank_to_bounded"]["lines"]:
        mv.append({"line_id": r["line_id"], "before": None, "after": r["after"],
                   "source": "T-689 conflict_bound (merged 66ffd421)"})
    plines, applied = T.overlay(lines, mv)
    pagg, pfams = statement(plines, master, cz)
    proposed = OrderedDict(
        label="PROPOSED until wired (T-693, lane I, Checker Gate B); never the candidate, never released",
        moves=applied, trade_total=view(pagg["total"]),
        families=OrderedDict((k, v) for k, v in pfams.items() if v != families[k]))
    fam689 = t689["blank_to_bounded"]
    col = pfams["B10-06"] if "B10-06" in pfams else None
    # reference comparison, apart
    km = load(A.KEYMAP)
    keys = [k for k in km["keys"] if k["trade"] == TRADE]
    refs = {r["id"]: r for r in load(A.BENCH)["records"] if r.get("row_kind") == "COVER_TOTAL"}
    cmp_rows = R.compare(keys, refs, agg["codes"], unit=UNIT)
    pcmp = R.compare(keys, refs, pagg["codes"], unit=UNIT)
    for r, p in zip(cmp_rows, pcmp):
        r["after_t693_proposed"] = OrderedDict(range=p["engine"]["engine_range"],
                                               held=f"{p['engine']['held_bounded']['lines']} + "
                                                    f"{p['engine']['held_blank']['lines']}")
    t683keys = {r["key"]: r for r in t683["reference_apart"]["keys"]}
    for r in cmp_rows:
        o = t683keys[r["key"]]
        r["vs_t683"] = "released unchanged" if o["engine"]["released"] == r["engine"]["released"] else "released moved"
    ar = load(P.ARITH)["keys"]["CONC.BEAM"]["arithmetic"]
    beam = next(r for r in cmp_rows if r["key"] == "CONC.BEAM")
    slab = next(r for r in cmp_rows if r["key"] == "CONC.SLAB")
    rel_b = R.D(beam["engine"]["released"]["m3"])
    notes = OrderedDict(
        slab=OrderedDict(
            difference=A.d6(slab["difference_ref_minus_released"]), pct=slab["pct_of_reference"],
            status="UNRESOLVED (ambiguous scope), residual named",
            split=("T-683 storey bridge: GF +0.050478, 1F -0.556333, 2F +0.043100 (re-add exactly). T-688 (merged "
                   "a62b3024) 1F: engine geometry = own re-measure (ENGINE_RIGHT on every drawn panel, noise "
                   "+0.000263); his typed 120 m2 rounding -0.080 .. +0.080; scope 2.977 .. 3.977 m2 of drawn panels not "
                   "in his 120 = -0.636333 .. -0.476333 m3 UNRESOLVED (62 panel subsets fit; none named). 2F: a "
                   "thickness-zone split (0.16: 31.25 vs 31.84 m2; 0.18: 13.635 vs 13.35 m2), not investigated")),
        beam=OrderedDict(
            cover=ar["cover_total"], his_rows=ar["row_sum"], omitted_row="0.128 (0.20 x 0.40 x 1.60, first 1F row "
            "outside his 1F sub-total; R-T683-3)", engine_released=R.s(rel_b),
            cover_minus_released=R.s(R.sub(R.D(ar["cover_total"]), rel_b)),
            rows_minus_released=R.s(R.sub(R.D(ar["row_sum"]), rel_b)),
            status="REFERENCE ARITHMETIC (his rows), % suppressed: the key holds HELD lines"))
    # R-T694-3 / -4: PC-2F association and the register gaps
    own = load(OWN)
    assoc = []
    for cs in own["cases"]:
        a = T.associate(cs, {h: tuple(b) for h, b in cs["outlines"].items()}, own["tol_mm"])
        a["text_value"] = cs["text"]
        a["nearest_to_text"] = T.nearest(cs["at"], {h: tuple(b) for h, b in cs["outlines"].items()})
        assoc.append(a)
    if [a["outline"] for a in assoc] != ["329", "386", "77B"]:
        raise T.Refused(f"R-T694-3 association changed: {[a['outline'] for a in assoc]}")
    gap_read = own["gap_outlines"]
    for h, g in gap_read.items():
        if g["size_texts_within_600"] or g["dimensions_within_600"]:
            raise T.Refused(f"{h}: a size text / dimension within 0.60 m exists; not a designer item until read")
    cause_rows = []
    for r in t689["lines"] + fam689["lines"]:
        lid = r["line_id"]
        if lid not in MEMBER_REF:
            continue
        cs = r.get("causes") or [{"item": r.get("section_item") or "D-66", "kind": "SECTION"},
                                 {"item": "D-39" if "2F" in r["element_id"] else "D-39", "kind": "TOP DATUM"}]
        cause_rows.append({"line_id": lid, "member_ref": MEMBER_REF[lid][0], "causes": cs,
                           "readings": MEMBER_REF[lid][1]})
    seen = set()
    cause_rows = [c for c in cause_rows if not (c["line_id"] in seen or seen.add(c["line_id"]))]
    spurious, gaps = T.check_causes(cause_rows, {"D-66": D66})
    st = OrderedDict()
    st["schema"] = "URBAN_T694_CONCRETE_STATEMENT_V1"
    st["task"] = "T-694"
    st["rules"] = ["R-T679-1 1.0.0 / R-T683-1 1.0.0 (unchanged)", "R-T694-1 .. -4 1.0.0 (research/agents_t694/t694_rules.py)"]
    st["not_claimed"] = ("development villa; not an accuracy claim; nothing released (the released default V2.9 + route "
                         "G is unchanged); no quantity changed; the reference is never a quantity")
    st["candidate"] = OrderedDict(version=idx["candidate_version"], index=INDEX, index_sha256=index_sha,
                                  lines_sha256=idx["inputs"]["lines"], concrete_equals=INDEX_67, master=MASTER,
                                  master_census_agrees=len(census_rows))
    st["inputs_sha256"] = OrderedDict((p, A.sha(ROOT / p)) for p in
                                      [T683, T689, OWN, A.KEYMAP, A.BENCH, A.SCORECARD, P.ARITH]
                                      + [rel_ for _, rel_ in PACKAGES])
    st["partition"] = OrderedDict((b, len(v)) for b, v in parts.items())
    st["trade_total"] = trade
    st["families"] = families
    st["item_codes"] = OrderedDict((c, view(a)) for c, a in agg["codes"].items())
    st["before_after_v3_0_66"] = OrderedDict(reconcile=chk, lines=moved)
    st["stale_classes_restated"] = restated
    st["floors_beside"] = OrderedDict(rule="R-T683-1 (e): AT_LEAST of blank lines, never in the range", lines=floors,
                                      sum_at_least=R.s(sum((R.D(f["at_least"]) for f in floors), Decimal(0))))
    st["after_t693_proposed"] = proposed
    st["reference_apart"] = OrderedDict(
        rule="difference = reference - engine released; % only where the key holds no HELD line",
        keys=cmp_rows, notes=notes, not_keyed_item_codes=R.not_keyed(agg["codes"], keys))
    st["pc_2f"] = OrderedDict(
        own_read=(f"Own read this run of {own['source']} ({own['bytes']} B, sha256 {own['sha256'][:8]}; decoded into "
                  f".work/private only): every 'P.C' text in the file = {own['pc_texts_in_file']} (handles 544, 548, "
                  "77C), each with a 3-vertex leader on S-TEXT-SLAB; outlines and leader ends relative to the text"),
        association=assoc,
        gap_outlines=gap_read,
        searched=("this run: every TEXT / MTEXT / DIMENSION of the ST DXF (no 'PLANT' / 'CARRYING' text, no size text or "
                  "dimension within 0.60 m of 77B / 778); merged: T-220 (ST p.15 'beam carrying planted col.' detail, "
                  "generic, no size; legend p.3-p.6; no schedule row for P.C), T-217 / T-256 (Checker-verified: p.9 "
                  "schedule, slab plans, sections A-A .. D-D, PDF plot = copy of the DXF)"),
        result=("no section, detail, dimension or schedule row fixes the PC-2F section: the only print is its own leader "
                "text 77C 'P.C 20x50' (leader to 77B, R-T694-3), against the outline 0.20 x 0.40 drawn on both FFRS 77B "
                "and SFRS 778; the p.15 'beam carrying planted col.' detail is generic (no size; T-220). DESIGNER ITEM: "
                "proposed addition to D-66 (which section is built), quantity 0.08 .. 0.10 m2 x 2.28 .. 3.50 m, already "
                "inside L-541c7e56 0.1824 .. 0.35"))
    st["cause_register"] = OrderedDict(spurious=spurious, gaps=gaps)
    st["checker_list"] = [OrderedDict(line_id=a, what=b) for a, b in CHECKER_LIST]
    held_rows = []
    for ln in lines:
        if ln["class"] != R.HELD:
            continue
        c = cz[ln["line_id"]]
        held_rows.append(OrderedDict(family=agg["owner"][ln["item_code"]], line_id=ln["line_id"],
                                     item_code=ln["item_code"], element_id=ln["element_id"],
                                     bound=[R.s(R.D(ln["held_low"])), R.s(R.D(ln["held_high"]))]
                                     if ln["held_low"] is not None else None, cause_class=c["cause_class"],
                                     cause=c["named"], cause_source=c["source"]))
    held_rows.sort(key=lambda r: (r["family"], r["item_code"], r["line_id"]))
    st["held_lines"] = held_rows
    return st


def md(st: dict) -> str:
    L = []
    c = st["candidate"]
    L.append("# T-694 Concrete reconciliation statement round 3 (V3.0.68; concrete = V3.0.67)\n")
    L.append(f"Candidate {c['version']}: `{c['index']}` sha256 {c['index_sha256'][:12]}, lines {c['lines_sha256'][:8]}; "
             f"master `{c['master']}` census agrees on {c['master_census_agrees']} families. {st['not_claimed']}.\n")
    L.append(f"Partition (R-T694-1, whole STR.CONC): {dict(st['partition'])}.\n")
    L.append("## Family subtotal -> trade total (m3; buckets never summed together)\n")
    L.append("| Family | Item | Lines | Released n / m3 | Bounded n / low .. high | Blank n (DESIGNER / OPEN BOUND / "
             "MEASURABLE NOW) | Excl | Engine range |")
    L.append("|---|---|---|---|---|---|---|---|")

    def row(name, item, v):
        bb = v["held_blank"]["by_cause"]
        return (f"| {name} | {item} | {v['lines']} | {v['released']['lines']} / {v['released']['m3']} | "
                f"{v['held_bounded']['lines']} / {v['held_bounded']['low']} .. {v['held_bounded']['high']} | "
                f"{v['held_blank']['lines']} ({bb['DESIGNER ITEM']} / {bb['OPEN BOUND']} / {bb['MEASURABLE NOW']}) | "
                f"{v['excluded']['lines']} | {v['engine_range'][0]} .. {v['engine_range'][1]} |")
    for code, v in st["families"].items():
        L.append(row(code, v["item"], v))
    L.append(row("**TRADE**", "all STR.CONC", st["trade_total"]))
    fb = st["floors_beside"]
    L.append("\nFloors beside (blank lines, never in the range): " + "; ".join(
        f"{f['line_id'][:10]} >= {f['at_least']}" for f in fb["lines"]) + f"; sum {fb['sum_at_least']} m3.\n")
    ba = st["before_after_v3_0_66"]
    r = ba["reconcile"]
    L.append(f"## Before (V3.0.66, T-683) -> after (V3.0.68)\n\nreleased {r['released']}; bounded {r['bounded']} "
             f"(line moves: low +{r['delta_low']}, high +{r['delta_high']}, exact); blank {r['blank']}.\n")
    L.append("| Line | Element | Before | After | Cause class |")
    L.append("|---|---|---|---|---|")
    for m in ba["lines"]:
        L.append(f"| {m['line_id'][:10]} | {m['element_id']} | {m['before']} | {m['after'][0]} .. {m['after'][1]} | "
                 f"{m['cause_class']} |")
    L.append(f"\nRestated (R-T683-1): {len(st['stale_classes_restated'])} lines, MEASURABLE NOW -> "
             + ", ".join(f"{x['line_id'][:10]} {x['class_after']}" for x in st["stale_classes_restated"]) + ".\n")
    p = st["after_t693_proposed"]
    L.append(f"## After T-693 ({p['label']})\n")
    L.append("| Line | Element | Before | After | Source |")
    L.append("|---|---|---|---|---|")
    for m in p["moves"]:
        L.append(f"| {m['line_id'][:10]} | {m['element_id']} | {m['before']} | {m['after'][0]} .. {m['after'][1]} | "
                 f"{m['source']} |")
    for code, v in p["families"].items():
        L.append(row(code + " PROPOSED", v["item"], v))
    L.append(row("**TRADE PROPOSED**", "all STR.CONC", p["trade_total"]))
    L.append("\n## Reference comparison, apart (key map T001B)\n")
    L.append("| Key | Reference | Engine released | Engine range | Held | Ref - released | % | After T-693 range (PROPOSED) |")
    L.append("|---|---|---|---|---|---|---|---|")
    for x in st["reference_apart"]["keys"]:
        e = x["engine"]
        L.append(f"| {x['key']} | {A.d6(x['reference'])} | {e['released']['m3']} | {e['engine_range'][0]} .. "
                 f"{e['engine_range'][1]} | {e['held_bounded']['lines']} + {e['held_blank']['lines']} | "
                 f"{A.d6(x['difference_ref_minus_released'])} | {x['pct_of_reference'] or 'suppressed'} | "
                 f"{x['after_t693_proposed']['range'][0]} .. {x['after_t693_proposed']['range'][1]} |")
    n = st["reference_apart"]["notes"]
    L.append(f"\n- CONC.SLAB {n['slab']['difference']} m3 ({n['slab']['pct']} %): {n['slab']['status']}. {n['slab']['split']}.")
    b = n["beam"]
    L.append(f"- CONC.BEAM cover {b['cover']} vs his rows {b['his_rows']}: omitted {b['omitted_row']}; engine released "
             f"{b['engine_released']}: cover - released {b['cover_minus_released']}, rows - released "
             f"{b['rows_minus_released']}; {b['status']}.\n")
    pc = st["pc_2f"]
    L.append("## PC-2F section (R-T694-3)\n")
    L.append(f"{pc['own_read']}\n")
    for a in pc["association"]:
        L.append(f"- text {a['text']}: {a['status']} -> {a['outline']} ({a['basis']}; gap {a.get('gap_mm')} mm, next "
                 f"{a.get('next_mm')} mm; outline nearest the text itself: {a['nearest_to_text']}{'; ' + a['why'] if a.get('why') else ''})")
    L.append(f"\nSearched: {pc['searched']}\n\nResult: {pc['result']}.\n")
    cr = st["cause_register"]
    L.append("## Cause register (R-T694-4)\n")
    for g in cr["gaps"]:
        L.append(f"- GAP {g['line_id'][:10]} {g['member']} {g['kind']}: {g['why']} ({g['item']})")
    for g in cr["spurious"]:
        L.append(f"- SPURIOUS {g['line_id'][:10]} {g['item']} readings {g['readings']}: {g['why']}")
    L.append("\n## Checker re-measure list (not re-measured before)\n")
    for i, x in enumerate(st["checker_list"], 1):
        L.append(f"{i}. {x['line_id'][:10]}: {x['what']}")
    L.append(f"\n## HELD lines ({len(st['held_lines'])})\n")
    L.append("| Family | Line | Code | Bound m3 | Cause class | Cause | Source |")
    L.append("|---|---|---|---|---|---|---|")
    for h in st["held_lines"]:
        bd = f"{h['bound'][0]} .. {h['bound'][1]}" if h["bound"] else "blank"
        L.append(f"| {h['family']} | {h['line_id'][:10]} | {h['item_code'][9:]} | {bd} | {h['cause_class']} | "
                 f"{str(h['cause']).replace('|', '/')[:160]} | {h['cause_source']} |")
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
        print("T694 check", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    t, p = st["trade_total"], st["after_t693_proposed"]["trade_total"]
    print(f"{st['candidate']['version']}: released {t['released']['lines']} / {t['released']['m3']}; bounded "
          f"{t['held_bounded']['lines']} {t['held_bounded']['low']} .. {t['held_bounded']['high']} "
          f"{t['held_bounded']['by_cause']}; blank {t['held_blank']['lines']} {t['held_blank']['by_cause']}; excluded "
          f"{t['excluded']['lines']}; PROPOSED bounded {p['held_bounded']['lines']} {p['held_bounded']['low']} .. "
          f"{p['held_bounded']['high']}, blank {p['held_blank']['lines']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
