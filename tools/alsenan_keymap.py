"""ALSENAN KEY MAP (task T-001b) - turns one engine run (canonical BOQ_LINES.json + BOQ_RELEASE_REPORT.json) and the
freelancer's normalised rows into the scorer's rows through an explicit key map, then scores them with
tools/alsenan_scoreboard.py. Reads only; writes only the files named by --out / --markdown.

Release class of a canonical line (the rule the engine's own release report applies, UP-QTY-STATUS-001,
tools/urban_boq_m9.py `_release_report`):
- evidence_state in QUANTITY_STATES (MEASURED / SOURCE_DERIVED / PROVISIONAL) with a measured_net -> RELEASED, qty;
- NOT_APPLICABLE_WITH_EVIDENCE / EXCLUDED_WITH_REASON -> not an answer (the engine states the item has no scope in
  that place); counted per key in "excluded", never turned into a quantity;
- anything else (BLOCKED_RFI, BOUNDED_EXPOSURE, a quantity state without measured_net, an unknown state) -> HELD with
  qty None: a range or a missing number never becomes a released quantity, and missing never becomes 0.
- every CONDITIONAL scenario set of the release report that carries a keyed item answers that key once as HELD
  (qty None): the quantity of a space under review sits in no line, so comparing the lines alone would understate.

Key map (URBAN_ALSENAN_KEY_MAP_V1, tests/alsenan/T001B_KEY_MAP.json): keys -> {trade, reference_id, item_codes,
conditional_items?, reference_unit?}. An item code in two keys, a key without its reference row, or a reference id
used twice is an error. Lines whose item code no key names stay UNMAPPED (listed, never false positives).

CLI: python3 -I tools/alsenan_keymap.py --run RUN_DIR --reference BENCHMARK_NORMALISED.json --key-map KEY_MAP.json
     --out OUT.json [--markdown OUT.md]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import alsenan_scoreboard as S  # noqa: E402

QUANTITY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")   # engine/source/boq_line.py QUANTITY_STATES
EXCLUDED_STATES = ("NOT_APPLICABLE_WITH_EVIDENCE", "EXCLUDED_WITH_REASON")


def load_key_map(doc):
    """Validated key map: {item_code: key entry}, {key: entry}."""
    by_item, by_key, refs = {}, {}, set()
    for k in doc["keys"]:
        key = k["key"]
        if key in by_key:
            raise ValueError(f"key {key!r} repeated")
        if k["reference_id"] in refs:
            raise ValueError(f"reference {k['reference_id']!r} used by two keys")
        refs.add(k["reference_id"])
        by_key[key] = k
        for code in k["item_codes"]:
            if code in by_item:
                raise ValueError(f"item code {code!r} answers two keys")
            by_item[code] = k
    return by_item, by_key


def line_status(ln):
    """(status for the scorer, qty) of one canonical line, or None when the line is an exclusion."""
    ev = ln.get("evidence_state")
    if ev in EXCLUDED_STATES:
        return None
    if ev in QUANTITY_STATES and ln.get("measured_net") is not None:
        return "RELEASED", float(ln["measured_net"])
    return "HELD", None


def engine_rows(lines, release_report, key_map_doc):
    """Scorer engine rows + an adapter report (excluded / unmapped counts per item code)."""
    by_item, by_key = load_key_map(key_map_doc)
    rows, excluded, unmapped = [], {}, {}
    for ln in lines:
        code = ln["item_code"]
        k = by_item.get(code)
        st = line_status(ln)
        if st is None:
            if k is not None:
                excluded[k["key"]] = excluded.get(k["key"], 0) + 1
            continue
        status, qty = st
        loc = ln.get("location") or {}
        rows.append({"id": ln["line_id"], "trade": k["trade"] if k else ln.get("trade"), "unit": ln["unit"],
                     "qty": qty, "status": status, "key": k["key"] if k else None,
                     "surface": loc.get("element_id")})
        if k is None:
            unmapped[(code, ln["unit"])] = unmapped.get((code, ln["unit"]), 0) + 1
    conditional = {}
    for key, k in by_key.items():
        items = set(k.get("conditional_items") or ())
        if not items:
            continue
        for s in (release_report or {}).get("categories", {}).get("CONDITIONAL", {}).get("scenario_sets", []):
            hit = any(items & set(v) for v in (s.get("by_scenario") or {}).values())
            if hit:
                unit = S.norm_unit(sorted(items)[0].rsplit("[", 1)[1].rstrip("]"))
                rows.append({"id": f"COND:{s['set_id']}:{key}", "trade": k["trade"], "unit": unit, "qty": None,
                             "status": "HELD", "key": key, "surface": f"COND:{s['set_id']}"})
                conditional[key] = conditional.get(key, 0) + 1
    report = {"excluded_lines_by_key": excluded, "conditional_sets_by_key": conditional,
              "unmapped_by_item": [{"item_code": c, "unit": u, "lines": n} for (c, u), n in sorted(unmapped.items())]}
    return rows, report


def reference_rows(normalised_doc, key_map_doc):
    """One scorer reference row per key from the normalised freelancer records (any row kind the map names)."""
    _, by_key = load_key_map(key_map_doc)
    recs = {r["id"]: r for r in normalised_doc["records"]}
    kinds = set(key_map_doc.get("reference_row_kinds") or ())
    rows = []
    for key, k in by_key.items():
        rec = recs.get(k["reference_id"])
        if rec is None:
            raise ValueError(f"key {key!r}: reference {k['reference_id']!r} not found")
        if kinds and rec.get("row_kind") not in kinds:
            raise ValueError(f"key {key!r}: reference {k['reference_id']!r} is a {rec.get('row_kind')} row")
        unit = rec.get("unit")
        if not str(unit or "").strip() and k.get("reference_unit"):
            if not str(k.get("reference_unit_source") or "").strip():
                raise ValueError(f"key {key!r}: a reference unit needs its source")
            unit = k["reference_unit"]
        rows.append({"id": rec["id"], "trade": k["trade"], "unit": unit, "qty": rec.get("qty"), "key": key})
    return rows


def run(run_dir, normalised_doc, key_map_doc):
    run_dir = Path(run_dir)
    lines = json.loads((run_dir / "BOQ_LINES.json").read_text(encoding="utf-8"))
    rel_path = run_dir / "BOQ_RELEASE_REPORT.json"
    rel = json.loads(rel_path.read_text(encoding="utf-8")) if rel_path.exists() else None
    eng, report = engine_rows(lines, rel, key_map_doc)
    ref = reference_rows(normalised_doc, key_map_doc)
    result = S.score(eng, ref)
    result["adapter"] = dict(report, release_report_present=rel is not None, boq_lines=len(lines))
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--key-map", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown")
    # T-177 opt-in: the SCOREBOARD v2 table (tools/scoreboard_v2.py) in the same call; without --v2-out nothing below
    # runs and the outputs above stay byte-identical
    ap.add_argument("--v2-out", help="SCOREBOARD v2 JSON (tools/scoreboard_v2.py)")
    ap.add_argument("--v2-markdown")
    ap.add_argument("--v2-label", help="Baseline cell of the --run side")
    ap.add_argument("--v2-verdicts", help="checker verdict file URBAN_SCOREBOARD_CHECKER_VERDICTS_V1")
    ap.add_argument("--v2-candidate-lines", help="a candidate's V3_0_x_BOQ_LINES.json, scored beside --run's "
                                                 "release report")
    ap.add_argument("--v2-candidate-label")
    ap.add_argument("--v2-heading", help="UTC date time for the '## SCOREBOARD v2' heading")
    # T-182 opt-in: the five-measures table (## SCOREBOARD v2.1); without it the v2 output is unchanged
    ap.add_argument("--v2-five-measures", action="store_true", help="T-182 five-measures layout")
    ap.add_argument("--v2-min-accuracy-scope", type=float, help="minimum scope share for the accuracy column")
    a = ap.parse_args(argv)
    v2 = [a.v2_markdown, a.v2_label, a.v2_verdicts, a.v2_candidate_lines, a.v2_candidate_label, a.v2_heading,
          a.v2_five_measures or None, a.v2_min_accuracy_scope]
    if a.v2_min_accuracy_scope is not None and not a.v2_five_measures:
        ap.error("--v2-min-accuracy-scope needs --v2-five-measures")
    if a.v2_out is None and any(x is not None for x in v2):
        ap.error("the --v2-* options need --v2-out")
    if a.v2_out is not None and (a.v2_label is None or a.v2_verdicts is None):
        ap.error("--v2-out needs --v2-label and --v2-verdicts")
    result = run(a.run, json.loads(Path(a.reference).read_text(encoding="utf-8")),
                 json.loads(Path(a.key_map).read_text(encoding="utf-8")))
    Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    md = S.markdown(result)
    if a.markdown:
        Path(a.markdown).write_text(md, encoding="utf-8")
    print(md, end="")
    if a.v2_out is not None:
        from tools import scoreboard_v2 as V2
        five = {} if not a.v2_five_measures else {"layout": V2.LAYOUT_FIVE, "min_scope": (
            V2.MIN_ACCURACY_SCOPE if a.v2_min_accuracy_scope is None else a.v2_min_accuracy_scope)}
        res2 = V2.build(a.run, a.v2_label, json.loads(Path(a.reference).read_text(encoding="utf-8")),
                        json.loads(Path(a.key_map).read_text(encoding="utf-8")),
                        json.loads(Path(a.v2_verdicts).read_text(encoding="utf-8")),
                        a.v2_candidate_lines, a.v2_candidate_label, **five)
        print(V2.write(res2, a.v2_out, a.v2_markdown, a.v2_heading), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
