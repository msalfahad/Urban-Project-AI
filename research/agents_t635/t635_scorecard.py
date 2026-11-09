"""T-635: scorecard V12 = the T-613 scorecard tool (R-T613-1, read only, imported unchanged) re-run on statement V12
(T-635, sha256 pinned), with the V12 supersession level added, the one HELD-blank count of record carried from V11
(R-T620-1 (d); no rebar section is restated in V12) and the change from scorecard V11 (T-620 committed output, pinned)
named per line, with the evidence move per line (rows by status V11 -> V12).

Research, unwired: reads committed JSON only; computes no quantity, moves no total, releases nothing.

  python3 -I research/agents_t635/t635_scorecard.py           # build out/SCORECARD_T635.json and .md
  python3 -I research/agents_t635/t635_scorecard.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT / "research/agents_t613", ROOT / "research/agents_t620"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import t613_scorecard as S  # noqa: E402  (T-613, read only; its module constants are never reassigned here)
import t620_scorecard as S11  # noqa: E402  (T-620, read only)

D = Decimal
ScorecardError = S.ScorecardError
STATEMENT = HERE / "out/RECONCILED_STATEMENT_T635.json"
STATEMENT_SHA256 = "7820d46acf2507629bcf0d96379a7abb681fcfb8e7eed832dacc4447d06b2965"
V11_SCORECARD = ROOT / "research/agents_t620/out/SCORECARD_T620.json"
V11_SCORECARD_SHA256 = "4e26155f2ae48c3a442b3678f928b11c7609e67a18b601597978d159652a81e3"
OUT_JSON = HERE / "out/SCORECARD_T635.json"
OUT_MD = HERE / "out/SCORECARD_T635.md"
SCHEMA = "URBAN_T635_SCORECARD_V12"
LEVELS = S11.LEVELS + ("sections_v12",)
SUPERSEDES = S11.SUPERSEDES + ("supersedes_v12",)


def load(path: Path, sha: str | None) -> dict:
    raw = path.read_bytes()
    if sha is not None and hashlib.sha256(raw).hexdigest() != sha:
        raise ScorecardError(f"{path.name}: sha256 differs from the pin (re-pin in a new version)")
    return json.loads(raw)


def all_sections(st: dict) -> dict:
    out = {}
    for lv in LEVELS:
        for c in st.get(lv, []):
            if c["section_id"] in out:
                raise ScorecardError(f"{c['section_id']}: section id twice in the statement")
            out[c["section_id"]] = dict(c, _level=lv)
    return out


def supersession(st: dict) -> dict:
    sup = {}
    for k in SUPERSEDES:
        sup.update({a: b for a, b in st.get(k, {}).items() if not a.startswith("beside")})
    return sup


def sections_of_record(st: dict) -> OrderedDict:
    secs, sup = all_sections(st), supersession(st)
    for a, b in sup.items():
        if b not in secs:
            raise ScorecardError(f"{a} -> {b}: superseding section absent")
    return OrderedDict((k, v) for k, v in secs.items() if k not in sup)


def check_statement_totals(st: dict, record: dict) -> list[dict]:
    sup = supersession(st)
    out = []
    for t in st["totals"]:
        sid = t["sections"][0]
        cur = S.of_record(sid, sup)
        sec = record[cur]
        for k in ("reference_total", "engine_valued", "difference"):
            if D(t[k]) != D(sec[k]):
                raise ScorecardError(f"totals {sid}: {k} {t[k]} != section of record {cur} {sec[k]}")
        moved = {c: [t["by_class"][c], sec["by_class"].get(c, "0")] for c in S.CLASSES
                 if D(t["by_class"][c]) != D(sec["by_class"].get(c, "0"))}
        if cur == sid and moved:
            raise ScorecardError(f"totals {sid}: by class differs from its own section ({moved})")
        out.append({"totals_section": sid, "section_of_record": cur, "reference_engine_difference": "EQUAL",
                    "by_class": "EQUAL" if not moved else "SUPERSEDED (statement totals entry predates the restatement)"})
    return out


def _base(sid: str) -> str:
    return sid.split("@")[0]


def changes_from_v11(cards: list[dict], apart: list[dict], v11: dict, st: dict) -> list[dict]:
    old = {_base(c["section_id"]): c for c in v11["reference_lines"]}
    old_ap = {_base(a["section_id"]): a for a in v11["apart"]}
    restated = {_base(v): v for v in st.get("supersedes_v12", {}).values()}
    secs = all_sections(st)
    out = []
    for c in cards + apart:
        b = _base(c["section_id"])
        o = old.get(b) or old_ap.get(b)
        if o is None:
            raise ScorecardError(f"{c['section_id']}: no V11 line to compare (a new line needs its own row)")
        for k in ("reference_total", "engine_valued", "difference", "by_class"):
            if o.get(k) != c.get(k):
                raise ScorecardError(f"{b}: {k} moved V11 -> V12 (an evidence fold moves no quantity and no class)")
        ch = {k: [o.get(k), c.get(k)] for k in ("line_status", "status_count") if o.get(k) != c.get(k)}
        if b in restated or ch:
            out.append({"line": b, "v11_section": o["section_id"], "v12_section": c["section_id"],
                        "apart": c in apart, "changed": ch or "none (stamps confirmed or annotations only)",
                        "cause": secs[c["section_id"]].get("fold_v12", "none"),
                        "note": secs[c["section_id"]].get("change_note_v12")})
    for r in out:
        if r["v12_section"] == r["v11_section"] and not isinstance(r["changed"], str):
            raise ScorecardError(f"{r['line']}: changed without a V12 restatement")
    return out


def build(st: dict, v11: dict) -> dict:
    record = sections_of_record(st)
    cards, apart = [], []
    for sid, sec in record.items():
        if sec.get("kind") in S.SCORED_KINDS:
            cards.append(S.section_card(sid, sec))
        else:
            ap = {"section_id": sid, "kind": sec.get("kind"), "trade": sec.get("trade"), "unit": sec.get("unit"),
                  "why_apart": "nested / reading / implied / cross-reference / bounds: never added (R-T613-1 (c))"}
            if "rows" in sec and "reference_total" in sec:
                c = S.section_card(sid, sec)
                ap.update({k: c[k] for k in ("reference_total", "engine_valued", "difference", "line_status",
                                             "status_count", "pct_of_reference", "pct_note", "by_class")})
            apart.append(ap)
    S11.held_blank_of_record(st, cards)     # V11 reconciliation, carried unchanged (no rebar section restated)
    tables = S.trade_tables(cards)
    for tb in tables:
        mine = [c for c in cards if c["section_id"] in tb["sections"]]
        if str(sum((D(c["difference"]) for c in mine), D(0))) != tb["difference"]:
            raise ScorecardError(f"{tb['trade_code']}: table difference not the sum of its sections")
        hb = [c["held_blank_lines_of_record"] for c in mine if c.get("held_blank_lines_of_record")]
        tb["held_blank_lines_of_record"] = (sum(h["count"] for h in hb) if hb else None)
    for c in cards:
        if c["pct_of_reference"] is not None and c["held_rows"]:
            raise ScorecardError(f"{c['section_id']}: a % beside a HELD row")
    by_unit_class: dict = {}
    for c in cards:
        u = by_unit_class.setdefault(f"{c['unit']} / {c['reference_kind']}", {k: D(0) for k in S.CLASSES})
        for k in S.CLASSES:
            u[k] += D(c["by_class"][k])

    def lines_by(cs):
        out: dict = {}
        for c in cs:
            k = c["line_status"].split(" ")[0] if not c["line_status"].startswith("PARTIALLY") else "PARTIALLY VERIFIED"
            out[k] = out.get(k, 0) + 1
        return dict(sorted(out.items()))
    rows = {s: sum(c["status_count"][s] for c in cards) for s in S.STATUSES}
    rows11 = {s: sum(c["status_count"][s] for c in v11["reference_lines"]) for s in S.STATUSES}
    if sum(rows.values()) != sum(rows11.values()):
        raise ScorecardError("scored row count changed V11 -> V12 (a fold neither adds nor drops a row)")
    by_trade = {}
    for t, t11 in zip(tables, v11["trade_tables"]):
        if (t["trade_code"], t["unit"], t["reference_kind"]) != (t11["trade_code"], t11["unit"], t11["reference_kind"]):
            raise ScorecardError("trade tables differ in key V11 -> V12")
        if t["status_count"] != t11["status_count"]:
            by_trade[f"{t['trade_code']} {t['unit']} {t['reference_kind']}"] = {
                s: [t11["status_count"][s], t["status_count"][s]] for s in S.STATUSES
                if t11["status_count"][s] != t["status_count"][s]}
    return {
        "schema": SCHEMA, "rule": S.RULE + " (T-613 tool, unchanged) + R-T620-1 (d) + R-T635-1",
        "statement": {"path": str(STATEMENT.relative_to(ROOT)), "sha256": STATEMENT_SHA256,
                      "schema": st.get("schema_v12"), "released_quantities_changed": st.get("released_quantities_changed")},
        "scorecard_v11": {"path": str(V11_SCORECARD.relative_to(ROOT)), "sha256": V11_SCORECARD_SHA256},
        "not_claimed": "development villa; not an accuracy claim; no product accuracy figure; freelancer agreement is "
                       "never proof; nothing released (V3.0.59 NOT RELEASED; V2.9 + route G unchanged)",
        "sections_in_statement": len(all_sections(st)), "sections_of_record": len(record),
        "scored_sections": len(cards), "apart_sections": len(apart),
        "headline": {"lines_by_status_v12": lines_by(cards), "lines_by_status_v11": lines_by(v11["reference_lines"]),
                     "rows_by_status_v12": rows, "rows_by_status_v11": rows11},
        "status_moves_by_trade_table": by_trade,
        "changes_from_v11": changes_from_v11(cards, apart, v11, st),
        "trade_tables": tables, "reference_lines": cards, "apart": apart,
        "residual_by_unit_reference_kind_and_class": {u: {k: str(v) for k, v in m.items()} for u, m in sorted(by_unit_class.items())},
        "statement_totals_check": check_statement_totals(st, record),
        "not_comparable": [{k: n.get(k) for k in ("report", "trade", "unit")} for n in st.get("not_comparable", [])],
        "beside_not_scored": [{k: b[k] for k in ("task", "merge", "what")} for b in st.get("beside_v12", [])],
        "pending_not_in_v12": [{"task": "statement V12 pending", "state": "as listed by T-635", "effect": p}
                               for p in st.get("reports_pending", [])],
    }


def markdown(sc: dict) -> str:
    h = sc["headline"]
    L = ["# T-635 scorecard V12 from statement V12 (generated; reference - engine, + = in the reference only)", "",
         f"Statement of record: `{sc['statement']['path']}` sha256 {sc['statement']['sha256'][:16]}... "
         f"({sc['statement']['schema']}); tool: {sc['rule']}. {sc['not_claimed']}.", "",
         f"Sections {sc['sections_in_statement']}; of record {sc['sections_of_record']}; scored {sc['scored_sections']}, "
         f"apart {sc['apart_sections']}. HELD and UNKNOWN never count as 0 or as correct; no % beside HELD.", "",
         "## Headline: lines and rows by status, V11 -> V12", "",
         "| Status | Lines V11 | Lines V12 | Rows V11 | Rows V12 |", "|---|---|---|---|---|"]
    for s in sorted(set(h["lines_by_status_v11"]) | set(h["lines_by_status_v12"]) | set(S.STATUSES)):
        L.append(f"| {s} | {h['lines_by_status_v11'].get(s, 0)} | {h['lines_by_status_v12'].get(s, 0)} | "
                 f"{h['rows_by_status_v11'].get(s, '-')} | {h['rows_by_status_v12'].get(s, '-')} |")
    L += ["", "## Row status moves per trade table (V11 -> V12)", "", "| Table | Moves |", "|---|---|"]
    for k, v in sc["status_moves_by_trade_table"].items():
        L.append(f"| {k} | " + "; ".join(f"{s} {a} -> {b}" for s, (a, b) in v.items()) + " |")
    L += ["", "## Change from scorecard V11, per line (quantities and classes unchanged by construction)", "",
          "| Line | V11 section | V12 section | Change | Fold |", "|---|---|---|---|---|"]
    for c in sc["changes_from_v11"]:
        ch = c["changed"] if isinstance(c["changed"], str) else "; ".join(
            f"{k}: {v[0]} -> {v[1]}" if k == "line_status" else f"{k} " + ", ".join(
                f"{s} {v[0].get(s)}->{v[1].get(s)}" for s in v[1] if v[0].get(s) != v[1].get(s))
            for k, v in c["changed"].items())
        L.append(f"| {c['line']}{' (apart)' if c['apart'] else ''} | {c['v11_section']} | {c['v12_section']} | {ch} | "
                 f"{c['cause']} |")
    L += ["", "## Trade tables (one unit and one reference kind each)", "",
          "| Trade | Unit | Ref. kind | Lines | Reference | Engine valued | Difference | ENGINE_RIGHT | ENGINE_WRONG | "
          "RULE_DIFFERENCE | HELD | TOLERANCE | UNRESOLVED | Lines by status | HELD rows at delta 0: bound | "
          "HELD-blank lines (one count) |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in sc["trade_tables"]:
        b = t["by_class"]
        L.append(f"| {t['trade_code']} | {t['unit']} | {t['reference_kind']} | {len(t['sections'])} | "
                 f"{t['reference_total']} | {t['engine_valued']} | {t['difference']} | {b['ENGINE_RIGHT']} | "
                 f"{b['ENGINE_WRONG']} | {b['RULE_DIFFERENCE']} | {b['HELD']} | {b['TOLERANCE']} | {b['UNRESOLVED']} | "
                 f"{', '.join(f'{k} {v}' for k, v in t['lines_by_status'].items())} | "
                 f"{t['held_bound_add'][0]} .. {t['held_bound_add'][1]} | {t['held_blank_lines_of_record'] or '-'} |")
    L += ["", "## Residual rows by evidence status per trade table: count / signed / gross |delta|", "",
          "| Trade | Unit | Ref. kind | " + " | ".join(S.STATUSES) + " |", "|---|---|---|" + "---|" * len(S.STATUSES)]
    for t in sc["trade_tables"]:
        L.append(f"| {t['trade_code']} | {t['unit']} | {t['reference_kind']} | " + " | ".join(
            f"{t['status_count'][s]} / {t['status_signed'][s]} / {t['status_gross'][s]}" for s in S.STATUSES) + " |")
    L += ["", "## Engine vs freelancer per reference line", "",
          "| Section | Trade | Unit | Reference | Engine valued | Difference | % of ref. | Line status | Rows by status |",
          "|---|---|---|---|---|---|---|---|---|"]
    for c in sc["reference_lines"]:
        pct = c["pct_of_reference"] if c["pct_of_reference"] is not None else "none"
        L.append(f"| {c['section_id']} | {c['trade_code']} | {c['unit']} | {c['reference_total']} | "
                 f"{c['engine_valued']} | {c['difference']} | {pct} ({c['pct_note'][:70]}) | {c['line_status']} | "
                 f"{S._sc(c)} |")
    L += ["", "## Apart (never added)", "", "| Section | Kind | Unit | Difference | Line status |", "|---|---|---|---|---|"]
    for a in sc["apart"]:
        L.append(f"| {a['section_id']} | {a['kind']} | {a['unit']} | {a.get('difference', '-')} | "
                 f"{a.get('line_status', '-')} |")
    L += ["", "## Residual by unit, reference kind and class (scored lines; never mixed)", "",
          "| Unit / ref. kind | " + " | ".join(S.CLASSES) + " |", "|---|" + "---|" * len(S.CLASSES)]
    for u, m in sc["residual_by_unit_reference_kind_and_class"].items():
        L.append(f"| {u} | " + " | ".join(m[k] for k in S.CLASSES) + " |")
    L += ["", "## Beside, not scored (merged work with no statement section)", ""]
    L += [f"- {b['task']} ({b['merge']}): {b['what']}" for b in sc["beside_not_scored"]]
    L += ["", "## Pending, not in V12 (never folded in)", ""]
    L += [f"- {p['effect']}" for p in sc["pending_not_in_v12"]]
    return "\n".join(L) + "\n"


def dumps(sc: dict) -> str:
    return json.dumps(sc, indent=1, ensure_ascii=True, sort_keys=False) + "\n"


def main(argv: list[str]) -> int:
    sc = build(load(STATEMENT, STATEMENT_SHA256), load(V11_SCORECARD, V11_SCORECARD_SHA256))
    js, md = dumps(sc), markdown(sc)
    if "--check" in argv:
        ok = OUT_JSON.read_text() == js and OUT_MD.read_text() == md
        print("T-635 scorecard --check:", "IDENTICAL" if ok else "DIFFERS")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(js)
    OUT_MD.write_text(md)
    print(f"T-635 scorecard written: {len(sc['trade_tables'])} trade tables, {sc['scored_sections']} lines scored")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
