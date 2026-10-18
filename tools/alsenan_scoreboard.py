"""ALSENAN SCOREBOARD (task T-001a) - engine BOQ rows vs reference (freelancer) rows, scored per trade and unit as
docs/agents/MISSION.md "How accuracy is scored" defines it. Pure arithmetic over two row lists: no engine module is
imported, no quantity is changed, nothing is written except the file named by --out.

Normalised rows (the scorer's only input; the adapters below build them from committed registers):
    reference row  {"id", "trade", "unit", "qty", "key"}
    engine row     {"id", "trade", "unit", "qty", "status", "key", "surface"?}
    verdicts       {reference id: {"verdict": ENGINE_RIGHT | FREELANCER_RIGHT | RULE_DIFFERENCE | UNRESOLVED,
                                   "hand_calc": "<hand calculation from the drawing>", "note": ...}}
An engine row answers the reference row with the same "key" (several engine rows may split one reference line; their
quantities are summed). The key map is explicit input: this module never guesses a match from a description.

Rules (each is a test in tests/scoreboard/test_alsenan_scoreboard.py):
- Units are never mixed or converted: aliases of one unit are folded (m2 / m² / م2), nothing else (kg vs t, m2 vs nr,
  mm vs m are different units). A reference row whose engine answer is in another unit is UNIT_MISMATCH: refused, not
  compared, not covered. A reference row without a unit goes to its own "(missing)" bucket and is never compared.
- Missing never becomes 0: a qty of None stays None. A RELEASED engine row without a quantity is HELD
  (RELEASED_WITHOUT_QTY); a reference row without a quantity is covered but never enters WAPE.
- Release class of an engine row: RELEASED (COMPUTED / RELEASED), HELD (PARTIAL / REVIEW / BLOCKED* / HELD) or
  UNSUPPORTED (NOT_IN_SOURCE / NOT_IMPLEMENTED / UNSUPPORTED). An unknown status is an error, never a guess.
  A reference line is compared only when every same-unit engine row answering it is RELEASED (a partly held answer
  would understate); otherwise it is HELD, or UNSUPPORTED when every answer is UNSUPPORTED.
- Coverage = reference lines answered RELEASED / HELD / UNSUPPORTED in their own unit / all reference lines.
  Silent omission = a reference line with no engine row at all.
- WAPE = sum |engine - reference| / sum reference over compared lines (None when that sum is 0, never 0 %).
  Signed error = sum (engine - reference) / sum reference (diagnostic). Adjudicated WAPE keeps the same denominator
  but counts the error only of lines whose verdict is FREELANCER_RIGHT or UNRESOLVED, or that have no verdict
  (MISSION.md "Who is right": only those count against the engine). ENGINE_RIGHT without a hand calculation is
  downgraded to UNRESOLVED.
- Duplicate = an engine row repeating the "surface" (provenance of the measured thing) of an earlier engine row on the
  same key and unit: one surface counted twice. Its quantity stays in the compared sum (the BOQ total carries it).
  False positive = an engine row whose key matches no reference line. An engine row without a key is UNMAPPED
  (listed; a key-map gap, not a false positive).

CLI: python3 -I tools/alsenan_scoreboard.py --engine E.json --reference R.json [--verdicts V.json] --out OUT.json
     [--markdown OUT.md]; each input is a JSON list of normalised rows or {"rows": [...]}.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

SCHEMA = "URBAN_ALSENAN_SCOREBOARD_V1"
MISSING_UNIT = "(missing)"

UNIT_ALIASES = {
    "m2": "m2", "m²": "m2", "sqm": "m2", "م2": "m2", "م²": "m2",
    "m3": "m3", "m³": "m3", "cum": "m3", "م3": "m3", "م³": "m3",
    "lm": "lm", "m": "lm", "rm": "lm", "ml": "lm", "م.ط": "lm", "م ط": "lm", "مط": "lm",
    "nr": "nr", "no": "nr", "no.": "nr", "each": "nr", "pcs": "nr", "عدد": "nr",
    "kg": "kg", "كجم": "kg", "كغ": "kg",
    "t": "t", "ton": "t", "tonne": "t", "طن": "t",
    "mm": "mm",
}

RELEASED, HELD, UNSUPPORTED = "RELEASED", "HELD", "UNSUPPORTED"
STATUS_CLASS = {
    "COMPUTED": RELEASED, "RELEASED": RELEASED,
    "PARTIAL": HELD, "REVIEW": HELD, "BLOCKED": HELD, "BLOCKED_SOURCE_CONFLICT": HELD, "HELD": HELD,
    "NOT_IN_SOURCE": UNSUPPORTED, "NOT_IMPLEMENTED": UNSUPPORTED, "UNSUPPORTED": UNSUPPORTED,
}

VERDICTS = ("ENGINE_RIGHT", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "UNRESOLVED")
COUNTS_AGAINST_ENGINE = {"FREELANCER_RIGHT", "UNRESOLVED", None}

# reference-line outcomes
OUT_COMPARED = "COMPARED"
OUT_HELD = "HELD"
OUT_UNSUPPORTED = "UNSUPPORTED"
OUT_SILENT = "SILENT_OMISSION"
OUT_UNIT_MISMATCH = "UNIT_MISMATCH"
OUT_REF_UNIT_MISSING = "REFERENCE_UNIT_MISSING"
OUT_REF_QTY_MISSING = "REFERENCE_QTY_MISSING"
COVERED = {OUT_COMPARED, OUT_HELD, OUT_UNSUPPORTED, OUT_REF_QTY_MISSING}


def norm_unit(unit):
    """Folded unit, or None when absent. An unknown non-empty unit is an error (never silently mixed)."""
    if unit is None:
        return None
    u = str(unit).strip().lower()
    if not u:
        return None
    if u not in UNIT_ALIASES:
        raise ValueError(f"unknown unit {unit!r}")
    return UNIT_ALIASES[u]


def _qty(value, where):
    """A finite float, or None for a missing quantity. Never turns missing into 0."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{where}: quantity {value!r} is not a number")
    if not math.isfinite(value):
        raise ValueError(f"{where}: quantity {value!r} is not finite")
    return float(value)


def release_class(status):
    s = str(status or "").strip().upper()
    if s not in STATUS_CLASS:
        raise ValueError(f"unknown engine status {status!r}")
    return STATUS_CLASS[s]


def _unique_ids(rows, side):
    seen = set()
    for r in rows:
        rid = r.get("id")
        if rid is None or rid in seen:
            raise ValueError(f"{side} row id {rid!r} is missing or repeated")
        seen.add(rid)


def _ratio(num, den):
    return None if not den else num / den


def score(engine_rows, reference_rows, verdicts=None):
    """Score engine rows against reference rows; returns a JSON-ready dict (see the module docstring)."""
    verdicts = verdicts or {}
    _unique_ids(engine_rows, "engine")
    _unique_ids(reference_rows, "reference")

    refs = []
    by_ref_key = {}
    for r in reference_rows:
        key = r.get("key")
        if key is None:
            raise ValueError(f"reference row {r['id']!r} has no key")
        if key in by_ref_key:
            raise ValueError(f"reference key {key!r} is used by more than one reference row")
        ref = {"id": r["id"], "trade": r.get("trade"), "unit": norm_unit(r.get("unit")),
               "qty": _qty(r.get("qty"), f"reference {r['id']}"), "key": key}
        by_ref_key[key] = ref
        refs.append(ref)

    engines = []
    unmapped = []
    by_eng_key = {}
    for e in engine_rows:
        cls = release_class(e.get("status"))
        qty = _qty(e.get("qty"), f"engine {e['id']}")
        note = None
        if cls == RELEASED and qty is None:
            cls, note = HELD, "RELEASED_WITHOUT_QTY"
        row = {"id": e["id"], "trade": e.get("trade"), "unit": norm_unit(e.get("unit")), "qty": qty,
               "class": cls, "key": e.get("key"), "surface": e.get("surface"), "note": note}
        engines.append(row)
        if row["key"] is None:
            unmapped.append(row)
        else:
            by_eng_key.setdefault(row["key"], []).append(row)

    warnings = []
    lines = []
    duplicates = []
    for ref in refs:
        answers = by_eng_key.get(ref["key"], [])
        v = verdicts.get(ref["id"]) or {}
        verdict = v.get("verdict")
        if verdict is not None and verdict not in VERDICTS:
            raise ValueError(f"reference {ref['id']!r}: unknown verdict {verdict!r}")
        downgraded = False
        if verdict == "ENGINE_RIGHT" and not str(v.get("hand_calc") or "").strip():
            verdict, downgraded = "UNRESOLVED", True
            warnings.append(f"{ref['id']}: ENGINE_RIGHT without a hand calculation counted as UNRESOLVED")
        line = {"ref_id": ref["id"], "trade": ref["trade"], "unit": ref["unit"] or MISSING_UNIT, "key": ref["key"],
                "reference_qty": ref["qty"], "engine_ids": [a["id"] for a in answers], "engine_qty": None,
                "refused_engine_ids": [], "duplicate_engine_ids": [], "verdict": verdict,
                "verdict_downgraded": downgraded, "abs_error": None, "signed_error": None}
        if not answers:
            line["outcome"] = OUT_SILENT
        elif ref["unit"] is None:
            line["outcome"] = OUT_REF_UNIT_MISSING
        else:
            same = [a for a in answers if a["unit"] == ref["unit"]]
            line["refused_engine_ids"] = [a["id"] for a in answers if a["unit"] != ref["unit"]]
            line["engine_ids"] = [a["id"] for a in same]
            seen_surface = set()
            for a in same:
                s = a["surface"]
                if s is not None and s in seen_surface:
                    line["duplicate_engine_ids"].append(a["id"])
                    duplicates.append({"engine_id": a["id"], "trade": a["trade"], "unit": a["unit"],
                                       "key": a["key"], "surface": s, "qty": a["qty"]})
                elif s is not None:
                    seen_surface.add(s)
            if not same:
                line["outcome"] = OUT_UNIT_MISMATCH
            elif all(a["class"] == UNSUPPORTED for a in same):
                line["outcome"] = OUT_UNSUPPORTED
            elif any(a["class"] != RELEASED for a in same):
                line["outcome"] = OUT_HELD
            elif ref["qty"] is None:
                line["outcome"] = OUT_REF_QTY_MISSING
                line["engine_qty"] = sum(a["qty"] for a in same)
            else:
                line["outcome"] = OUT_COMPARED
                eq = sum(a["qty"] for a in same)
                line["engine_qty"] = eq
                line["signed_error"] = eq - ref["qty"]
                line["abs_error"] = abs(eq - ref["qty"])
        lines.append(line)

    false_positives = [{"engine_id": e["id"], "trade": e["trade"], "unit": e["unit"] or MISSING_UNIT,
                        "key": e["key"], "qty": e["qty"], "class": e["class"]}
                       for e in engines if e["key"] is not None and e["key"] not in by_ref_key]

    buckets = {}

    def bucket(trade, unit):
        return buckets.setdefault((trade, unit), {
            "trade": trade, "unit": unit, "reference_lines": 0, "covered": 0, "released": 0, "held": 0,
            "unsupported": 0, "silent_omissions": 0, "unit_mismatch": 0, "reference_qty_missing": 0,
            "compared": 0, "sum_reference": 0.0, "sum_abs_error": 0.0, "sum_signed_error": 0.0,
            "sum_abs_error_counted": 0.0, "false_positives": 0, "false_positive_qty": 0.0,
            "false_positive_qty_missing": 0, "duplicates": 0})

    for ln in lines:
        b = bucket(ln["trade"], ln["unit"])
        b["reference_lines"] += 1
        out = ln["outcome"]
        b["covered"] += out in COVERED
        b["released"] += out in (OUT_COMPARED, OUT_REF_QTY_MISSING)
        b["held"] += out == OUT_HELD
        b["unsupported"] += out == OUT_UNSUPPORTED
        b["silent_omissions"] += out == OUT_SILENT
        b["unit_mismatch"] += out == OUT_UNIT_MISMATCH
        b["reference_qty_missing"] += out == OUT_REF_QTY_MISSING
        if out == OUT_COMPARED:
            b["compared"] += 1
            b["sum_reference"] += ln["reference_qty"]
            b["sum_abs_error"] += ln["abs_error"]
            b["sum_signed_error"] += ln["signed_error"]
            if ln["verdict"] in COUNTS_AGAINST_ENGINE:
                b["sum_abs_error_counted"] += ln["abs_error"]
    for fp in false_positives:
        b = bucket(fp["trade"], fp["unit"])
        b["false_positives"] += 1
        if fp["qty"] is None:
            b["false_positive_qty_missing"] += 1
        else:
            b["false_positive_qty"] += fp["qty"]
    for d in duplicates:
        bucket(d["trade"], d["unit"])["duplicates"] += 1

    rows = []
    for key in sorted(buckets, key=lambda k: (str(k[0]), str(k[1]))):
        b = buckets[key]
        b["coverage"] = _ratio(b["covered"], b["reference_lines"])
        b["wape"] = _ratio(b["sum_abs_error"], b["sum_reference"])
        b["signed_error_ratio"] = _ratio(b["sum_signed_error"], b["sum_reference"])
        b["wape_adjudicated"] = _ratio(b["sum_abs_error_counted"], b["sum_reference"])
        rows.append(b)

    return {"SCHEMA": SCHEMA, "buckets": rows, "lines": lines, "false_positives": false_positives,
            "duplicates": duplicates,
            "unmapped_engine_rows": [{"engine_id": e["id"], "trade": e["trade"], "unit": e["unit"], "qty": e["qty"]}
                                     for e in unmapped],
            "warnings": warnings,
            "rule": "per trade and unit, never mixed; missing never becomes 0; MISSION.md scoring"}


def _pct(x):
    return "-" if x is None else f"{100.0 * x:.2f} %"


def markdown(result):
    """SCOREBOARD.md rows: one per trade and unit."""
    head = ("| Trade | Unit | Ref lines | Coverage | Silent omissions | Unit refused | Compared | WAPE | "
            "WAPE (adjudicated) | Signed | False pos. | Duplicates |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
    out = [head]
    for b in result["buckets"]:
        out.append(f"| {b['trade']} | {b['unit']} | {b['reference_lines']} | {_pct(b['coverage'])} | "
                   f"{b['silent_omissions']} | {b['unit_mismatch']} | {b['compared']} | {_pct(b['wape'])} | "
                   f"{_pct(b['wape_adjudicated'])} | {_pct(b['signed_error_ratio'])} | {b['false_positives']} | "
                   f"{b['duplicates']} |")
    return "\n".join(out) + "\n"


# ---- adapters from committed registers (the key map is explicit input; T-001b supplies the real one) ----

def engine_rows_from_boq_lines(doc, key_map, surface_map=None):
    """Rows of a BOQ_LINES*.json register (registers_v3 / registers_v3b): line_id, trade, unit, qty, status.
    key_map / surface_map: {line_id: key / surface}; a line absent from key_map gets key None (UNMAPPED)."""
    surface_map = surface_map or {}
    return [{"id": ln["line_id"], "trade": ln.get("trade"), "unit": ln.get("unit"), "qty": ln.get("qty"),
             "status": ln.get("status"), "key": key_map.get(ln["line_id"]),
             "surface": surface_map.get(ln["line_id"])} for ln in doc["lines"]]


def reference_rows_from_normalised(doc, key_map, row_kinds=("DETAIL",)):
    """Records of registers_b1/BENCHMARK_NORMALISED.json (derived, unchanged, from FREELANCER_RAW_ROWS.json) of
    the given row kinds that key_map maps; unmapped records are returned apart so none disappears silently."""
    rows, unmapped = [], []
    for rec in doc["records"]:
        if rec.get("row_kind") not in row_kinds:
            continue
        if rec["id"] not in key_map:
            unmapped.append(rec["id"])
            continue
        rows.append({"id": rec["id"], "trade": rec.get("trade"), "unit": rec.get("unit"), "qty": rec.get("qty"),
                     "key": key_map[rec["id"]]})
    return rows, unmapped


def _load_rows(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["rows"] if isinstance(data, dict) else data


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--engine", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--verdicts")
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown")
    a = ap.parse_args(argv)
    verdicts = json.loads(Path(a.verdicts).read_text(encoding="utf-8")) if a.verdicts else {}
    result = score(_load_rows(a.engine), _load_rows(a.reference), verdicts)
    Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.markdown:
        Path(a.markdown).write_text(markdown(result), encoding="utf-8")
    for w in result["warnings"]:
        print("warning:", w, file=sys.stderr)
    print(markdown(result), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
