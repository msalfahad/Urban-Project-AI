"""T-620: scorecard V11 = the T-613 scorecard tool (R-T613-1, read only, imported unchanged) re-run on statement V11
(T-620, sha256 pinned), with the V11 supersession level added, the F-T613-5 fix (one HELD-blank count per line, its
NOT_COMPARABLE part named) and the change from scorecard V10 (T-613 committed output, pinned) named per line.

Research, unwired: reads committed JSON only; computes no quantity, moves no total, releases nothing.

  python3 -I research/agents_t620/t620_scorecard.py           # build out/SCORECARD_T620.json and .md
  python3 -I research/agents_t620/t620_scorecard.py --check   # rebuild and compare with out/ (exit 1 on a difference)
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
T613 = ROOT / "research/agents_t613"
if str(T613) not in sys.path:
    sys.path.insert(0, str(T613))
import t613_scorecard as S  # noqa: E402  (T-613, read only; its module constants are never reassigned here)

D = Decimal
ScorecardError = S.ScorecardError
STATEMENT = HERE / "out/RECONCILED_STATEMENT_T620.json"
STATEMENT_SHA256 = "db5f7bceb8b6b44b1d9f87c40e83022cdd1123789e4e3be81fe43e9bad298e69"
V10_SCORECARD = T613 / "out/SCORECARD_T613.json"
V10_SCORECARD_SHA256 = "62b5402a74919dff76da49c8787f892f88ead2d9bc8960c353f2f213a95dd936"
OUT_JSON = HERE / "out/SCORECARD_T620.json"
OUT_MD = HERE / "out/SCORECARD_T620.md"
SCHEMA = "URBAN_T620_SCORECARD_V11"
LEVELS = S.LEVELS + ("sections_v11",)
SUPERSEDES = S.SUPERSEDES + ("supersedes_v11",)

PENDING_NOT_IN_V11 = (
    {"task": "T-622", "state": "READY (not merged at the T-620 claim)",
     "effect": "B4 wall tile 47 UNKNOWN rows to evidence: T-547/wall-tile stays UNKNOWN 0 / 53 here; not folded in"},
    {"task": "T-623 .. T-628", "state": "TODO at the claim",
     "effect": "B10 beams / columns / footing rows, beam-end open items, B3 carry-forward, B8, B12 m2: not folded in"},
)


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


def held_blank_of_record(st: dict, cards: list[dict]) -> None:
    """F-T613-5: one HELD-blank count per line, read from the statement's reconciliation; the rows' count must agree."""
    rec = {h["section_id"]: h for h in st.get("held_blank_reconciliation_v11", [])}
    for c in cards:
        h = rec.get(c["section_id"])
        rows = c["held_inside_rows"]["blank_lines"]
        if h is None:
            c["held_blank_lines_of_record"] = None
            continue
        if h["in_compared_rows"] != rows:
            raise ScorecardError(f"{c['section_id']}: rows count {rows} != statement {h['in_compared_rows']}")
        if h["in_compared_rows"] + sum(h["in_not_comparable_blocks"].values()) != h["held_blank_lines"]:
            raise ScorecardError(f"{c['section_id']}: HELD-blank count does not re-add (F-T613-5)")
        c["held_blank_lines_of_record"] = {"count": h["held_blank_lines"], "in_rows": rows,
                                           "in_not_comparable": h["in_not_comparable_blocks"], "cause": h["cause"]}


def _base(sid: str) -> str:
    return sid.split("@")[0]


def changes_from_v10(cards: list[dict], apart: list[dict], v10: dict, st: dict) -> list[dict]:
    old = {_base(c["section_id"]): c for c in v10["reference_lines"]}
    old_ap = {_base(a["section_id"]): a for a in v10["apart"]}
    sup11 = st.get("supersedes_v11", {})
    restated = {_base(v): v for v in sup11.values()}
    out = []
    for c in cards + apart:
        b = _base(c["section_id"])
        o = old.get(b) or old_ap.get(b)
        if o is None:
            raise ScorecardError(f"{c['section_id']}: no V10 line to compare (a new line needs its own row)")
        ch = {k: [o.get(k), c.get(k)] for k in ("line_status", "status_count", "by_class", "reference_total",
                                                   "engine_valued", "difference") if o.get(k) != c.get(k)}
        if b in restated or ch:
            out.append({"line": b, "v10_section": o["section_id"], "v11_section": c["section_id"],
                        "apart": c in apart, "changed": ch or "none (annotations only: bounds / ranges / causes)",
                        "cause": all_sections(st)[c["section_id"]].get("fold_v11", "none"),
                        "note": all_sections(st)[c["section_id"]].get("change_note_v11")})
    for r in out:
        if r["v11_section"] == r["v10_section"] and r["changed"] != "none (annotations only: bounds / ranges / causes)":
            raise ScorecardError(f"{r['line']}: changed without a V11 restatement")
    return out


def build(st: dict, v10: dict) -> dict:
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
    held_blank_of_record(st, cards)
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
    lines: dict = {}
    for c in cards:
        k = c["line_status"].split(" ")[0] if not c["line_status"].startswith("PARTIALLY") else "PARTIALLY VERIFIED"
        lines[k] = lines.get(k, 0) + 1
    rows = {s: sum(c["status_count"][s] for c in cards) for s in S.STATUSES}
    rows10 = {s: sum(c["status_count"][s] for c in v10["reference_lines"]) for s in S.STATUSES}
    lines10: dict = {}
    for c in v10["reference_lines"]:
        k = c["line_status"].split(" ")[0] if not c["line_status"].startswith("PARTIALLY") else "PARTIALLY VERIFIED"
        lines10[k] = lines10.get(k, 0) + 1
    return {
        "schema": SCHEMA, "rule": S.RULE + " (T-613 tool, unchanged) + R-T620-1 (d)",
        "statement": {"path": str(STATEMENT.relative_to(ROOT)), "sha256": STATEMENT_SHA256,
                      "schema": st.get("schema_v11"), "released_quantities_changed": st.get("released_quantities_changed")},
        "scorecard_v10": {"path": str(V10_SCORECARD.relative_to(ROOT)), "sha256": V10_SCORECARD_SHA256},
        "not_claimed": "development villa; not an accuracy claim; no product accuracy figure; freelancer agreement is "
                       "never proof; nothing released (V3.0.58 NOT RELEASED; V2.9 + route G unchanged)",
        "sections_in_statement": len(all_sections(st)), "sections_of_record": len(record),
        "scored_sections": len(cards), "apart_sections": len(apart),
        "headline": {"lines_by_status_v11": dict(sorted(lines.items())), "lines_by_status_v10": dict(sorted(lines10.items())),
                     "rows_by_status_v11": rows, "rows_by_status_v10": rows10},
        "changes_from_v10": changes_from_v10(cards, apart, v10, st),
        "trade_tables": tables, "reference_lines": cards, "apart": apart,
        "residual_by_unit_reference_kind_and_class": {u: {k: str(v) for k, v in m.items()} for u, m in sorted(by_unit_class.items())},
        "statement_totals_check": check_statement_totals(st, record),
        "not_comparable": [{k: n.get(k) for k in ("report", "trade", "unit")} for n in st.get("not_comparable", [])],
        "pending_not_in_v11": list(PENDING_NOT_IN_V11) + [{"task": "statement V11 pending", "state": "as listed by T-620",
                                                          "effect": p} for p in st.get("reports_pending", [])],
    }


def markdown(sc: dict) -> str:
    h = sc["headline"]
    L = ["# T-620 scorecard V11 from statement V11 (generated; reference - engine, + = in the reference only)", "",
         f"Statement of record: `{sc['statement']['path']}` sha256 {sc['statement']['sha256'][:16]}... "
         f"({sc['statement']['schema']}); tool: {sc['rule']}. {sc['not_claimed']}.", "",
         f"Sections {sc['sections_in_statement']}; of record {sc['sections_of_record']}; scored {sc['scored_sections']}, "
         f"apart {sc['apart_sections']}. HELD and UNKNOWN never count as 0 or as correct; no % beside HELD.", "",
         "## Headline: lines and rows by status, V10 -> V11", "",
         "| Status | Lines V10 | Lines V11 | Rows V10 | Rows V11 |", "|---|---|---|---|---|"]
    for s in sorted(set(h["lines_by_status_v10"]) | set(h["lines_by_status_v11"]) | set(S.STATUSES)):
        L.append(f"| {s} | {h['lines_by_status_v10'].get(s, 0)} | {h['lines_by_status_v11'].get(s, 0)} | "
                 f"{h['rows_by_status_v10'].get(s, '-')} | {h['rows_by_status_v11'].get(s, '-')} |")
    L += ["", "## Change from scorecard V10, per line", "", "| Line | V10 section | V11 section | Change | Fold |",
          "|---|---|---|---|---|"]
    for c in sc["changes_from_v10"]:
        ch = c["changed"] if isinstance(c["changed"], str) else "; ".join(
            f"{k}: {v[0]} -> {v[1]}" if k == "line_status" else f"{k} " + ", ".join(
                f"{s} {v[0].get(s)}->{v[1].get(s)}" for s in v[1] if v[0].get(s) != v[1].get(s))
            for k, v in c["changed"].items())
        L.append(f"| {c['line']}{' (apart)' if c['apart'] else ''} | {c['v10_section']} | {c['v11_section']} | {ch} | "
                 f"{c['cause']}{': ' + c['note'] if c.get('note') else ''} |")
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
    L += ["", "## HELD-blank lines, one count (F-T613-5)", ""]
    for c in sc["reference_lines"]:
        if c.get("held_blank_lines_of_record"):
            L.append(f"- {c['section_id']}: {c['held_blank_lines_of_record']['cause']}")
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
    L += ["", "## Apart (never added)", "", "| Section | Kind | Unit | Difference | By class | Line status |",
          "|---|---|---|---|---|---|"]
    for a in sc["apart"]:
        bc = "; ".join(f"{k} {v}" for k, v in (a.get("by_class") or {}).items() if D(v))
        L.append(f"| {a['section_id']} | {a['kind']} | {a['unit']} | {a.get('difference', '-')} | {bc or '-'} | "
                 f"{a.get('line_status', '-')} |")
    L += ["", "## Residual by unit, reference kind and class (scored lines; never mixed)", "",
          "| Unit / ref. kind | " + " | ".join(S.CLASSES) + " |", "|---|" + "---|" * len(S.CLASSES)]
    for u, m in sc["residual_by_unit_reference_kind_and_class"].items():
        L.append(f"| {u} | " + " | ".join(m[k] for k in S.CLASSES) + " |")
    L += ["", "## Pending, not in V11 (never folded in)", ""]
    L += [f"- {p['task']} ({p['state']}): {p['effect']}" for p in sc["pending_not_in_v11"]]
    return "\n".join(L) + "\n"


def dumps(sc: dict) -> str:
    return json.dumps(sc, indent=1, ensure_ascii=True, sort_keys=False) + "\n"


def main(argv: list[str]) -> int:
    sc = build(load(STATEMENT, STATEMENT_SHA256), load(V10_SCORECARD, V10_SCORECARD_SHA256))
    js, md = dumps(sc), markdown(sc)
    if "--check" in argv:
        ok = OUT_JSON.read_text() == js and OUT_MD.read_text() == md
        print("T-620 scorecard --check:", "IDENTICAL" if ok else "DIFFERS")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(js)
    OUT_MD.write_text(md)
    print(f"T-620 scorecard written: {len(sc['trade_tables'])} trade tables, {sc['scored_sections']} lines scored")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
