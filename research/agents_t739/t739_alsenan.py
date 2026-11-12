"""T-739 ALL-TRADE AGGREGATION STATEMENT on the candidate of record ARCH_TAKEOFF_V3.0.73 (R-T739-1; lane I, research).

Reads only committed, sha-pinned JSON (no drawing, no workbook beyond the committed normalised benchmark the key map
already reads); writes only research/agents_t739/out/. No quantity, class or candidate file changes; nothing released
(V3.0.73 NOT RELEASED; released V2.9 + route G untouched).

  python3 -I research/agents_t739/t739_alsenan.py --write   # write out/
  python3 -I research/agents_t739/t739_alsenan.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import glob
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t739_rules as R  # noqa: E402

OUT = HERE / "out"
JSON_OUT, MD_OUT = OUT / "T739_AGGREGATION.json", OUT / "T739_AGGREGATION.md"
PIN = {
    "index73": ("research/agents_t722/out/LINE_INDEX_V3_0_73.json",
                "af8d567d8a8ae8288ddf3c4c8207d2cbfcf2f322513af84e63a4448898ad7b23"),
    "index72": ("research/agents_t703/out/LINE_INDEX_V3_0_72.json",
                "8e753204d90ebf75d8fa5fe3de120f235bdb16e06a7d677e6aeb615e84ef5d2b"),
    "t722": ("research/agents_t722/out/T722_SUMMARY.json",
             "e6d8906cbb5343bdc47f0d389cab2d47880013750fbc668bfb740e3a42178216"),
    "master": ("rules/coverage/BOQ_FAMILY_MASTER_1.74.0.json",
               "edf5e4646f087a453c3a4202ea862d946b766351cf91053f3cf9632be5a6ae0e"),
    "t469": ("research/agents_t469/out/T469_SCOREBOARD_V3_0_41.json",
             "0c9c9be01dc35cd7b025e09527ea7d945bdf7297dac346013f924d00982b6bba"),
    "t692": ("research/agents_t692/out/T692_CENSUS.json",
             "4603d478296a24a33475d3a1aa74033e8b2650521b3d4e1fbe094840d9c7e369"),
    "keymap": ("tests/alsenan/T001C_KEY_MAP.json",
               "d304446e32a540757e620e6517681fdffd34bb7114727b57f7219768bcebcdb9"),
    "bench": ("tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json",
              "959a8eeb67e3129a3ead75851ef17651dcd005acfc6d6b34add936477fabe613"),
    "t726": ("research/agents_t726/out/T726_SHAFT_RESIDUAL.json",
             "30ea2e2385b25677ccffd1db5d07aeafb987675a21c937ecb1a4cf2bb0a4a9ca"),
    "downgrades": ("research/agents_t469/DOWNGRADES_SNAPSHOT.json",
                   "817326399e5b9ffff1d727b9599dff46d1f917c930e759c37e1d5721f0f85766"),
    "t716": ("research/agents_t716/out/T716_CENSUS.json",
             "af27f1d5f389b438b02eb7316611c96256bc3239f9ca8c8d3e2c0211ccd87255"),
    "t654": ("research/agents_t654/out/TRIAL_BOQ_R4_T654.json",
             "9e032726257c4961972bd7fd8de2620a3f7e2adc1f32a78802764a5289e91733"),
}
# cause-bearing keys, in the order a record's cause is read (first non-empty wins)
CAUSE_KEYS = ("cause", "causes", "why", "why_no_low", "why_no_bound", "why_no_at_most", "at_most_why_none",
              "hold_text", "hold", "cause_named", "cause_t676", "reason", "m3_cause_proposed", "form_why",
              "cause_class")
ID_IN_TEXT = re.compile(r"\b(D-\d+|Q-\d+|OQ-\d+|C-ST-\d+|F-T\d+-\d+)\b")
TASK_DIR = re.compile(r"research/agents_t(\d{3})/")
ADDED_SINCE_T654 = 654   # T-654 trial BOQ r4 is the base cause register; records of later tasks overrule it
HAND_CELLS = (("B7 Stairs", "m3"), ("B9 Masonry", "m2"), ("B4 Walls", "lm"))
# outputs whose per-line 'cause' field states something other than why the line is held (read, never used as a cause)
NOT_A_HOLD_CAUSE = {662: "T-662 rebar ratio: its 'cause' is the ratio route taken (detailed kept / no calibration), "
                         "not the reason the line is held"}


def load(key):
    rel, want = PIN[key]
    b = (ROOT / rel).read_bytes()
    got = hashlib.sha256(b).hexdigest()
    if got != want:
        raise R.AggregationError(f"{rel}: sha256 {got[:8]} != pinned {want[:8]}")
    return json.loads(b.decode("utf-8"))


def trade_map(master):
    own = {}
    for f in master["families"]:
        for c in f.get("item_codes") or []:
            if c in own:
                raise R.AggregationError(f"{c}: owned by two families")
            own[c] = (f["group"], f["code"])
    reg = set(master.get("not_a_boq_line_codes") or {})
    return own, reg


def _cause_text(o):
    for k in CAUSE_KEYS:
        v = o.get(k)
        if v in (None, "", [], {}):
            continue
        if isinstance(v, list):
            parts = []
            for x in v:
                parts.append(" ".join(f"{a}={b}" for a, b in x.items()) if isinstance(x, dict) else str(x))
            return f"{k}: " + "; ".join(parts)
        if isinstance(v, dict):
            return f"{k}: " + json.dumps(v, ensure_ascii=False, sort_keys=True)
        return str(v) if k == "cause" else f"{k}: {v}"
    faces = o.get("faces")
    if isinstance(faces, list):
        fc = sorted({x.get("cause") for x in faces if isinstance(x, dict) and x.get("cause")})
        if fc:
            return "faces: " + " | ".join(fc)
    item = o.get("item")
    if isinstance(item, str) and ID_IN_TEXT.search(item):
        return f"item: {item}" + (f" ({o['action']})" if o.get("action") else "")
    return None


def _walk(o, acc):
    if isinstance(o, dict):
        lid = next((o[k] for k in ("line_id", "line") if isinstance(o.get(k), str) and o[k].startswith("L-")), None)
        if lid:
            acc.append((lid, _cause_text(o)))
        for v in o.values():
            _walk(v, acc)
    elif isinstance(o, list):
        for v in o:
            _walk(v, acc)


def cause_records(index_ids):
    """(e) every committed per-line cause record of T-654 and of later tasks' research outputs, resolved to full ids."""
    by_prefix = defaultdict(list)
    for i in index_ids:
        by_prefix[i[:10]].append(i)
    files = sorted(glob.glob(str(ROOT / "research/agents_t[6-9][0-9][0-9]/out/*.json")))
    recs, used = [], Counter()
    for f in files:
        rel = str(Path(f).relative_to(ROOT))
        m = TASK_DIR.search(rel)
        tn = int(m.group(1))
        if tn < ADDED_SINCE_T654 or tn in (716, 739) or tn in NOT_A_HOLD_CAUSE or "LINE_INDEX" in rel:
            continue
        if tn == 654:
            d = load("t654")
            if rel != PIN["t654"][0]:
                continue
            acc = [(x["line_id"], x.get("cause")) for x in d["per_line"]]
        else:
            try:
                d = json.loads(Path(f).read_text(encoding="utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            acc = []
            _walk(d, acc)
        for lid, text in acc:
            full = R.resolve_prefix(lid, index_ids, by_prefix)
            if full and text:
                recs.append((tn, f"T-{tn:03d} {Path(rel).name}", full, text))
                used[f"T-{tn:03d}"] += 1
    return recs, used


def downgrade_causes(index, snap):
    applied = {x["downgrade_id"] for x in index["downgrades"] if x["status"] == "APPLIED"}
    out = {}
    for r in snap["downgrades"]:
        if r["downgrade_id"] in applied:
            for lid in r["line_ids"]:
                out[lid] = f"{r['downgrade_id']} APPLIED: {r['reason']}"
    return out, sorted(applied)


def chain_readd(i72, i73, t722):
    """(d) V3.0.72 + the T-722 package rows = V3.0.73; every other line byte-equal."""
    a = {l["line_id"]: l for l in i72["lines"]}
    b = {l["line_id"]: l for l in i73["lines"]}
    if set(a) != set(b):
        raise R.AggregationError("V3.0.72 and V3.0.73 indexes carry different line ids")
    rows = {r["line_id"]: r for r in t722["rows"]}

    def st(ln):
        return {"low": ln["held_low"], "high": ln["held_high"], "value": ln["measured_net"]}
    checked, changed = 0, []
    for lid, l73 in b.items():
        l72 = a[lid]
        if lid in rows:
            r = rows[lid]
            for side, ln in (("before", l72), ("after", l73)):
                want = {k: r[side].get(k) for k in ("low", "high", "value")}
                if st(ln) != want:
                    raise R.AggregationError(f"{lid}: index {side} {st(ln)} != T-722 record {want}")
            checked += 1
            if l72 != l73:
                changed.append(lid)
        elif l72 != l73:
            raise R.AggregationError(f"{lid}: changed V3.0.72 -> V3.0.73 with no package row")
    return {"package_rows": len(rows), "rows_checked_before_after": checked, "lines_changed": len(changed),
            "other_lines_byte_equal": len(b) - len(rows)}


def build():
    i73, i72, t722 = load("index73"), load("index72"), load("t722")
    master, t469, t692 = load("master"), load("t469"), load("t692")
    keymap, bench, t726, snap = load("keymap"), load("bench"), load("t726"), load("downgrades")
    if i73["candidate_version"] != "ARCH_TAKEOFF_V3.0.73":
        raise R.AggregationError("not the candidate of record")
    own, reg = trade_map(master)
    lines = i73["lines"]

    def trade_of(code):
        if code in reg:
            return "REGISTER (not a BOQ line)"
        if code not in own:
            raise R.AggregationError(f"{code}: no family owns it (NO_FAMILY)")
        return own[code][0]
    agg = R.aggregate(lines, trade_of)

    # trade x unit table
    trades = []
    for (t, unit), cells in sorted(agg["trade_unit"].items()):
        rt = R.range_text(cells, unit)
        trades.append({
            "trade": t, "unit": unit,
            "counts": {s: cells[s]["n"] for s in R.STATES},
            "released": R.fmt(cells[R.RELEASED]["released"]),
            "bounded_low": R.fmt(cells[R.BOUNDED]["low"]), "bounded_high": R.fmt(cells[R.BOUNDED]["high"]),
            "at_least_low": R.fmt(cells[R.AT_LEAST]["low"]), "at_most_high": R.fmt(cells[R.AT_MOST]["high"]),
            "total": rt["total"], "statement": rt["text"]})
    codes = []
    for (t, code, unit), cells in sorted(agg["code_unit"].items()):
        codes.append({"trade": t, "family": own.get(code, ("", "REGISTER"))[1], "item_code": code, "unit": unit,
                      "counts": {s: cells[s]["n"] for s in R.STATES},
                      "released": R.fmt(cells[R.RELEASED]["released"]),
                      "bounded_low": R.fmt(cells[R.BOUNDED]["low"]), "bounded_high": R.fmt(cells[R.BOUNDED]["high"]),
                      "statement": R.range_text(cells, unit)["text"],
                      "line_ids": {s: sorted(cells[s]["lines"]) for s in R.STATES if cells[s]["lines"]}})

    # (d) chain re-add + component coverage
    chain = chain_readd(i72, i73, t722)
    comp = Counter(trade_of(r["item_code"]) for r in t722["rows"])
    comp_cover = {t: {"lines": n, "with_committed_component_record": comp.get(t, 0),
                      "without": n - comp.get(t, 0)}
                  for t, n in sorted(Counter(trade_of(l["item_code"]) for l in lines).items())}
    # T-722 concrete census cross-check (its own after figures)
    cc = []
    for code, v in sorted(t722["conc_census_after"].items()):
        cells = {s: R._cell() for s in R.STATES}
        for ln in lines:
            if ln["item_code"] == code and ln["unit"] == "m3":  # noqa: SIM102
                R._add(cells[R.state_of(ln)], ln, R.state_of(ln))
        zl = [ln for ln in lines if ln["item_code"] == code and ln["unit"] == "m3" and R.state_of(ln) == R.BOUNDED
              and R.D(ln["held_low"]) == 0]
        mine = {"released": cells[R.RELEASED]["released"], "low": cells[R.BOUNDED]["low"],
                "high": cells[R.BOUNDED]["high"], "blank": cells[R.BLANK]["n"], "bounded": cells[R.BOUNDED]["n"]}
        theirs = {"released": R.D(v["released_m3"]), "low": R.D(v["bounded_low_m3"]),
                  "high": R.D(v["bounded_high_m3"]), "blank": v["blank"], "bounded": v["bounded"]}
        # T-722 prints float sums rounded to 6 decimals: agreement is |exact - printed| <= 1e-6; any other difference
        # is reported (never forced), with the index's 0 .. cap lines of the code named as the candidate explanation
        tol = Decimal("0.000001")
        ok = all((abs(mine[k] - theirs[k]) <= tol) if isinstance(mine[k], Decimal) else mine[k] == theirs[k]
                 for k in mine)
        diffs = {k: (R.fmt(mine[k] - theirs[k]) if isinstance(mine[k], Decimal) else mine[k] - theirs[k])
                 for k in mine if mine[k] != theirs[k]}
        cc.append({"item_code": code, "agree": ok, "t722_printed": {k: (R.fmt(v) if isinstance(v, Decimal) else v) for k, v in theirs.items()}, "exact_minus_t722_printed": diffs,
                   "zero_low_caps": [f"{ln['line_id']} 0 .. {ln['held_high']}" for ln in zl], "released_m3": R.fmt(mine["released"]),
                   "bounded": f"{R.fmt(mine['low'])} .. {R.fmt(mine['high'])} ({mine['bounded']})",
                   "blank": mine["blank"],
                   "beside_run_record_only": v.get("beside_sum_m3_run_record_only") or {}})

    # (e) causes
    held = [l["line_id"] for l in lines if l["class"] == "HELD"]
    recs, used = cause_records({l["line_id"] for l in lines})
    dg, applied = downgrade_causes(i73, snap)
    t716 = load("t716")
    cls716 = {}
    for lid, a in t716["assignment"].items():
        txt = f"{a['kind']}: {a['bucket']}" + (f" (dependent on host {a['host']})" if a.get("host") else "")
        cls716[lid] = ("T-716 cause-class census (V3.0.70, merged 17aaab4b)", txt)
    causes, findings = R.resolve_causes(held, recs, dg, cls716)
    src_count = Counter(c["source"].split(" ")[0] if c["source"].startswith("T-") else c["source"]
                        for c in causes.values())
    meta = {l["line_id"]: l for l in lines}
    held_rows = []
    for lid in sorted(held):
        ln = meta[lid]
        c = causes.get(lid)
        held_rows.append({"line_id": lid, "trade": trade_of(ln["item_code"]), "item_code": ln["item_code"],
                          "unit": ln["unit"], "state": R.state_of(ln), "held_low": ln["held_low"],
                          "held_high": ln["held_high"],
                          "cause": c["cause"] if c else None, "cause_source": c["source"] if c else "F-T739-1",
                          "also_stated_by": c["also_stated_by"] if c else [],
                          "cause_class_t716": cls716[lid][1] if lid in cls716 else "NOT IN T-716 (held after V3.0.70)"})
    f_by = defaultdict(list)
    for lid in findings:
        f_by[f"{trade_of(meta[lid]['item_code'])} {meta[lid]['item_code']} ({meta[lid]['unit']})"].append(lid)

    # (f) released V2.9 + route G beside (T-469 committed side A, by item code)
    side = next(s for s in t469["sides"] if "V29" in (s.get("label") or "") or "released" in (s.get("label") or "").lower())
    v29 = defaultdict(lambda: {"released": Decimal(0), "released_lines": 0, "held_lines": 0, "excluded_lines": 0})
    for r in side["by_item_code"]:
        try:
            t = trade_of(r["item_code"])
        except R.AggregationError:
            t = "NO_FAMILY in master 1.74.0"
        c = v29[(t, r["unit"])]
        c["released"] += R.D(r["released_qty"])
        c["released_lines"] += r["released_lines"]
        c["held_lines"] += r["held_lines"]
        c["excluded_lines"] += r["excluded_lines"]
    v29_rows = [{"trade": t, "unit": u, "released": R.fmt(c["released"]), "released_lines": c["released_lines"],
                 "held_lines": c["held_lines"], "excluded_lines": c["excluded_lines"]}
                for (t, u), c in sorted(v29.items())]

    # (f) freelancer through the key map
    sys.path.insert(0, str(ROOT))
    from tools import alsenan_keymap as K          # read only: reference rows of the declared keys
    from tools import alsenan_scoreboard as S      # unit aliases only
    refs = {r["key"]: r for r in K.reference_rows(bench, keymap)}
    keyed = []
    for k in keymap["keys"]:
        ref = refs[k["key"]]
        ru = S.UNIT_ALIASES.get(str(ref["unit"]).strip().lower(), ref["unit"]) if ref["unit"] else None
        cells = {s: R._cell() for s in R.STATES}
        other_unit = Counter()
        for ln in lines:
            if ln["item_code"] in k["item_codes"]:
                u = S.UNIT_ALIASES.get(ln["unit"], ln["unit"])
                if u != ru:
                    other_unit[ln["unit"]] += 1
                    continue
                st = R.state_of(ln)
                R._add(cells[st], ln, st)
        refq = R.D(ref["qty"])
        n_eng = sum(cells[s]["n"] for s in R.STATES if s != R.EXCLUDED)
        row = {"key": k["key"], "freelancer": f"{R.fmt(refq.quantize(Decimal('0.001')))} {ru}",
               "released": R.fmt(cells[R.RELEASED]["released"]), "released_n": cells[R.RELEASED]["n"],
               "bounded": f"{R.fmt(cells[R.BOUNDED]['low'])} .. {R.fmt(cells[R.BOUNDED]['high'])}",
               "bounded_n": cells[R.BOUNDED]["n"], "at_least_n": cells[R.AT_LEAST]["n"],
               "blank_n": cells[R.BLANK]["n"], "excluded_n": cells[R.EXCLUDED]["n"],
               "other_unit_lines_not_compared": dict(other_unit)}
        if k["key"] == "PLASTER.INTERNAL":
            rc = t726["reconciliation"]
            row["compare"] = ("LIKE FOR LIKE only (Lead 2026-11-11 12:25; ruling 2026-11-12 04:17): "
                              f"{' .. '.join(rc['like_for_like_plaster_pct_row_named_apart'])} % with his 13.50 m2 "
                              "shaft row APART (NO_FACE / UNRESOLVED on his side), his full total beside "
                              f"{' .. '.join(rc['like_for_like_plaster_pct'])} % (T-726, quoted, not re-derived); "
                              "the key-level blended figure is never printed as a %")
        elif "typed_lines" in json.dumps(k) or k["key"] == "FLOOR.INTERNAL":
            row["compare"] = "TYPED_KEY (tools/alsenan_keymap.py typed selectors only; not run here)"
        elif n_eng == 0:
            row["compare"] = "NO ANSWER in the reference unit (unit refused, never converted)"
        else:
            open_up = cells[R.BLANK]["n"] + cells[R.AT_LEAST]["n"] > 0
            row["compare"] = R.pct_range(cells[R.RELEASED]["released"], cells[R.BOUNDED]["low"],
                                         cells[R.BOUNDED]["high"], refq, open_up)
        keyed.append(row)

    # missing families (no line in V3.0.73), with the T-692 class where it has one
    t692c = {r["code"]: r for r in t692["rows"]}
    present = {own[l["item_code"]][1] for l in lines if l["item_code"] in own}
    missing, since = [], []
    for f in master["families"]:
        if f["code"] in present:
            if f["code"] in t692c:
                since.append({"family": f["code"], "item": f["item_en"], "t692_class": t692c[f["code"]]["class"]})
            continue
        r = t692c.get(f["code"])
        missing.append({"family": f["code"], "group": f["group"], "item": f["item_en"], "unit": f.get("unit"),
                        "t692_class": r["class"] if r else "NOT IN T-692 PRIMARY SET",
                        "t692_band": r["band"] if r else None})
    # three trade x unit cells listed line by line for a hand re-add (one m3, one m2, one lm)
    hand = []
    for t, u in HAND_CELLS:
        rows = [{"line_id": l["line_id"], "item_code": l["item_code"], "state": R.state_of(l),
                 "measured_net": l["measured_net"], "held_low": l["held_low"], "held_high": l["held_high"]}
                for l in sorted(lines, key=lambda x: (x["item_code"], x["line_id"]))
                if l["unit"] == u and trade_of(l["item_code"]) == t]
        hand.append({"trade": t, "unit": u, "lines": rows,
                     "statement": next(x["statement"] for x in trades if (x["trade"], x["unit"]) == (t, u))})
    return {
        "schema": "URBAN_T739_AGGREGATION_V1", "hand_readd_cells": hand, "task": "T-739", "rule": f"{R.RULE_ID} {R.RULE_VERSION}",
        "candidate": "ARCH_TAKEOFF_V3.0.73 (NOT RELEASED), lines sha c5a0b128",
        "inputs": {k: {"path": v[0], "sha256": v[1]} for k, v in PIN.items()},
        "line_count": len(lines), "state_count": dict(Counter(R.state_of(l) for l in lines)),
        "trades": trades, "item_codes": codes, "chain_readd_v3_0_72_to_v3_0_73": chain,
        "component_coverage": comp_cover, "concrete_census_crosscheck_t722": cc,
        "held": {"lines": len(held), "with_cause": len(causes), "findings_F_T739_1": len(findings),
                 "cause_source_counts": dict(sorted(src_count.items())), "records_read_by_task": dict(sorted(used.items())),
                 "applied_downgrades_on_index": applied,
                 "not_used_as_cause": {f"T-{k:03d}": v for k, v in NOT_A_HOLD_CAUSE.items()}, "F_T739_1_by_code": {k: sorted(v) for k, v in sorted(f_by.items())},
                 "rows": held_rows},
        "released_v2_9_route_g_beside": {"source": "T-469 committed side A (BOQ lines 1eff0920, 1,455 lines)",
                                         "rows": v29_rows},
        "freelancer_keyed": keyed,
        "missing_families": {"master": "1.74.0", "families": len(master["families"]), "no_line": len(missing),
                             "rows": missing, "t692_rows_now_with_lines": since},
        "not_claimed": "development villa statement; nothing wired or released; no accuracy figure; freelancer "
                       "agreement is never proof",
    }


def render_md(b):
    L = [f"# T-739 all-trade aggregation statement, {b['candidate']}", "",
         f"Rule {b['rule']}. {b['line_count']} lines; states: " +
         ", ".join(f"{k} {v}" for k, v in sorted(b["state_count"].items())) + ". " + b["not_claimed"] + ".", "",
         "## Per trade and unit (never summed across states or units)", "",
         "| Trade | Unit | Rel n | Released | Bounded n | Bounded low .. high | AT_LEAST n | AT_MOST n | Blank n | Excl n | Statement |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in b["trades"]:
        c = t["counts"]
        L.append(f"| {t['trade']} | {t['unit']} | {c['RELEASED']} | {t['released']} | {c['BOUNDED']} | "
                 f"{t['bounded_low']} .. {t['bounded_high']} | {c['AT_LEAST']} | {c['AT_MOST']} | {c['BLANK']} | "
                 f"{c['EXCLUDED']} | {t['statement']} |")
    L += ["", "## Per item code (line ids in the JSON)", "", "| Trade | Family | Item code | Unit | Statement | Excl n |",
          "|---|---|---|---|---|---|"]
    for c in b["item_codes"]:
        L.append(f"| {c['trade']} | {c['family']} | {c['item_code']} | {c['unit']} | {c['statement']} | "
                 f"{c['counts']['EXCLUDED']} |")
    ch = b["chain_readd_v3_0_72_to_v3_0_73"]
    L += ["", "## Re-add checks", "",
          f"- Every subtotal computed twice (lines direct, item-code subtotals) in Decimal: equal.",
          f"- Chain V3.0.72 -> V3.0.73: {ch['package_rows']} T-722 package rows, before / after checked "
          f"{ch['rows_checked_before_after']} (index fields moved on {ch['lines_changed']}: the AT_LEAST / NAMED rows move "
          f"no index field); {ch['other_lines_byte_equal']} other lines byte-equal.",
          "- T-722 concrete census (its own after figures, rounded float sums) against this exact re-add: " +
          "; ".join(f"{x['item_code']} {'AGREE' if x['agree'] else 'DIFFERS ' + json.dumps(x['exact_minus_t722_printed'], sort_keys=True) + ' (index 0 .. cap lines: ' + (', '.join(x['zero_low_caps']) or 'none') + '; F-T739-2)'}"
                    f" released {x['released_m3']} m3, bounded {x['bounded']}, blank {x['blank']}"
                    + (f", beside (run record only, not in the index) {x['beside_run_record_only']}"
                       if x['beside_run_record_only'] else "") for x in b["concrete_census_crosscheck_t722"]),
          "- Component layer: only the T-722 package rows carry a committed per-line component record (before / after);"
          " every other line's gross / deductions / additions live in the private run output (V3_0_73_BOQ_LINES "
          "c5a0b128), NOT re-added here:", "",
          "| Trade | Lines | With committed component record | Without |", "|---|---|---|---|"]
    for t, v in b["component_coverage"].items():
        L.append(f"| {t} | {v['lines']} | {v['with_committed_component_record']} | {v['without']} |")
    h = b["held"]
    L += ["", "## HELD lines and their causes (never 0, never summed into a released figure)", "",
          f"{h['lines']} HELD lines: {h['with_cause']} with a committed cause, {h['findings_F_T739_1']} without "
          "(F-T739-1, listed by id in the JSON). Cause source (latest task wins): " +
          ", ".join(f"{k} {v}" for k, v in h["cause_source_counts"].items()) + ".", "",
          "F-T739-1 by item code: " + ("; ".join(f"{k} {len(v)}" for k, v in h["F_T739_1_by_code"].items()) or "none"),
          "", "## Released V2.9 + route G beside (not mixed)", "",
          f"Source: {b['released_v2_9_route_g_beside']['source']}.", "",
          "| Trade | Unit | Released | Released n | Held n | Excl n |", "|---|---|---|---|---|---|"]
    for r in b["released_v2_9_route_g_beside"]["rows"]:
        L.append(f"| {r['trade']} | {r['unit']} | {r['released']} | {r['released_lines']} | {r['held_lines']} | "
                 f"{r['excluded_lines']} |")
    L += ["", "## Freelancer, keyed lines only (T001C key map; diagnostic range, not an accuracy claim)", "",
          "| Key | Freelancer | Released (n) | Bounded (n) | Blank n | Compare |", "|---|---|---|---|---|---|"]
    for k in b["freelancer_keyed"]:
        L.append(f"| {k['key']} | {k['freelancer']} | {k['released']} ({k['released_n']}) | {k['bounded']} "
                 f"({k['bounded_n']}) | {k['blank_n']} | {k['compare']} |")
    L += ["", "## Hand re-add cells (Checker Gate A: one m3, one m2, one lm)", ""]
    for c in b["hand_readd_cells"]:
        L += [f"### {c['trade']} {c['unit']}: {c['statement']}", "", "| Line | Item code | State | Net | Low | High |",
              "|---|---|---|---|---|---|"]
        for r in c["lines"]:
            L.append(f"| {r['line_id']} | {r['item_code']} | {r['state']} | {r['measured_net']} | {r['held_low']} | "
                     f"{r['held_high']} |")
        L.append("")
    m = b["missing_families"]
    L += ["", f"## Families with no line in V3.0.73 ({m['no_line']} of {m['families']}, master {m['master']})", "",
          "| Family | Group | Item | Unit | T-692 class |", "|---|---|---|---|---|"]
    for r in m["rows"]:
        L.append(f"| {r['family']} | {r['group']} | {r['item']} | {r['unit']} | {r['t692_class']} |")
    if m["t692_rows_now_with_lines"]:
        L += ["", "T-692 rows that now have a line: " + "; ".join(
            f"{x['family']} {x['item']}" for x in m["t692_rows_now_with_lines"])]
    return "\n".join(L) + "\n"


def dumps(b):
    return json.dumps(b, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main(argv):
    b = build()
    j, md = dumps(b), render_md(b)
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(j, encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
        print("written", JSON_OUT.name, MD_OUT.name)
        return 0
    if "--check" in argv:
        ok = JSON_OUT.read_text(encoding="utf-8") == j and MD_OUT.read_text(encoding="utf-8") == md
        print("check", "OK" if ok else "DIFFERS")
        return 0 if ok else 1
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
