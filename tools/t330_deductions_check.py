"""CANONICAL DEDUCTIONS CHECK (task T-330) - a read-only export-integrity check beside tools/boq_export_v1.py. It
computes, changes and approves no engine quantity, edits no line and no frozen file, and nothing in engine/ imports it.
General: no project name, item code or element id is written in this module.

Why. A canonical line (engine/source/boq_line.py) carries gross, measured_net and a 'deductions' list. When the list is
empty while gross != net, the deductions exist only somewhere a consumer does not read (for example in
calculation.inputs), and a consumer that computes gross - sum(deductions) gets the GROSS: a silent over-measure in the
contractual export (deductions_n 0, deductions_total blank, net below gross). This check makes that visible and lets
the export refuse it.

The identity every quantity line with a numeric gross must satisfy (same unit, tolerance TOL):

    gross - sum(deductions) + sum(additions) = measured_net

and every deduction is CANONICAL: it names the element / opening it deducts (one of ID_KEYS) and carries its own
non-negative quantity in the line's unit, under a key the export reads (QTY_KEYS, the keys
tools/boq_export_v1._deductions reads) or under a key named after a unit ('m2', 'lm', ...: it then states that unit).

Findings (every one that applies is listed in 'issues'; the line's category is the first, most severe first):
  REFUSED  MIXED_UNITS        a deduction / addition states a unit other than the line's
  REFUSED  NEGATIVE_DEDUCTION a deduction / addition quantity below 0 (a sign carried twice)
  REFUSED  EXCEEDS_GROSS      the deductions sum to more than the gross (a negative remainder)
  FLAG     NON_NUMERIC        a deduction / addition without one numeric quantity (a range, a text)
  FLAG     EMPTY_DEDUCTIONS   gross != net and the canonical list is empty (the consumer reads gross as net)
  FLAG     NOT_SUMMING        gross - deductions + additions != net (a residual, in the line's unit)
  FLAG     EXPORT_TOTAL_BLANK the export's own reader (boq_export_v1._deductions) finds no total in the list, or
                              another total: BOQ.csv would show deductions_n > 0 with a blank / different total
  FLAG     MISSING_ID         a deduction without the id of what it deducts
A line whose gross is not a number, or that carries no measured_net (HELD / EXCLUDED), has no arithmetic to check and
is counted as NOT_APPLICABLE; it is never treated as passing a quantity.

    python3 -I tools/t330_deductions_check.py check --lines V3_0_x_BOQ_LINES.json [--json OUT.json] [--csv OUT.csv]
        exit 0 clean, 1 FLAG only, 2 any REFUSED
    python3 -I tools/t330_deductions_check.py export --lines ... --candidate-version ... --out DIR [any
        tools/boq_export_v1.py option]
        the GUARDED export: the check runs first; on any finding NOTHING is written (exit 2, the findings printed),
        else tools/boq_export_v1.main runs unchanged with the same arguments
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

DEFAULT_GUARD_CLASS = "TOOLING"        # T-212: a read-only check; it produces no quantity

SCHEMA = "URBAN_DEDUCTIONS_CHECK_V1"
TOL = 0.0005                           # tools/boq_export_v1.QTY_MATCH_TOL: the export's own quantity tolerance
QTY_KEYS = ("area", "qty", "quantity", "value", "net")          # the keys tools/boq_export_v1._deductions reads
ID_KEYS = ("element_id", "opening_id", "opening", "id", "line_id", "ref")
UNIT_KEYS = ("unit",)

REFUSED, FLAG = "REFUSED", "FLAG"
CATEGORIES = (  # (code, severity), most severe first: a line's category is the first that applies
    ("MIXED_UNITS", REFUSED), ("NEGATIVE_DEDUCTION", REFUSED), ("EXCEEDS_GROSS", REFUSED),
    ("NON_NUMERIC", FLAG), ("EMPTY_DEDUCTIONS", FLAG), ("NOT_SUMMING", FLAG), ("EXPORT_TOTAL_BLANK", FLAG),
    ("MISSING_ID", FLAG))
SEVERITY = dict(CATEGORIES)
NOT_APPLICABLE, OK = "NOT_APPLICABLE", "OK"
CSV_COLUMNS = ("line_id", "trade", "item_code", "floor", "element_id", "unit", "category", "severity", "issues",
               "gross", "deductions_n", "deductions_sum", "additions_sum", "measured_net", "gross_minus_net", "residual",
               "export_deductions_total", "detail", "shadow_path", "shadow_n", "shadow_sum", "shadow_open", "shadow_explains_gap")
DEC = 6

from engine.source import boq_line as BL       # noqa: E402
from tools import boq_export_v1 as E           # noqa: E402  (read only: its own deduction reader)

UNIT_QTY_KEYS = tuple(BL.UNITS)                # a deduction key named after a unit carries that unit


class DeductionsError(ValueError):
    pass


def _isnum(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _item(d):
    """one deduction / addition -> (quantity or None, id or None, units it states). A key named after a unit
    (engine/source/boq_line.UNITS: 'm2', 'lm', ...) is a quantity that states its own unit; 'unit' states it too."""
    if _isnum(d):
        return float(d), None, set()
    if isinstance(d, dict):
        units = {str(d[k]) for k in UNIT_KEYS if d.get(k) not in (None, "")}
        q = next((float(d[k]) for k in QTY_KEYS if _isnum(d.get(k))), None)
        for k in UNIT_QTY_KEYS:
            if k in d:
                units.add(k)
                if q is None and _isnum(d[k]):
                    q = float(d[k])
        i = next((d[k] for k in ID_KEYS if d.get(k) not in (None, "")), None)
        return q, i, units
    return None, None, set()


def _r(x):
    return None if x is None else round(float(x), DEC)


SHADOW_QTY_KEYS = QTY_KEYS + ("m2", "m3", "lm", "m")


def _shadow(ln):
    """DIAGNOSTIC ONLY (never used to pass a line): deductions a line states outside the canonical field, i.e. any
    'deductions' list nested under calculation.inputs. -> (path, n, numeric sum, n without one number (a range or
    no quantity)); (None, 0, None, 0) when there is none. It tells the next fill package where the list lives."""
    found = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "deductions" and isinstance(v, list) and v:
                    found.append((path + "." + k, v))
                else:
                    walk(v, path + "." + str(k))
    walk(((ln.get("calculation") or {}).get("inputs")) or {}, "calculation.inputs")
    if not found:
        return None, 0, None, 0
    path, ds = found[0]
    s, n_open = 0.0, 0
    for d in ds:
        q = None
        if _isnum(d):
            q = float(d)
        elif isinstance(d, dict):
            q = next((float(d[k]) for k in SHADOW_QTY_KEYS if _isnum(d.get(k))), None)
        if q is None:
            n_open += 1
        else:
            s += q
    return path, len(ds), _r(s), n_open


def check_line(ln, tol=TOL):
    """-> one result dict for a canonical line: category OK, NOT_APPLICABLE or the first finding code in CATEGORIES
    order, and 'issues' = every finding code that applies (a line can be short of its net AND name no opening)."""
    unit = ln.get("unit")
    loc = ln.get("location") or {}
    gross, net = ln.get("gross"), ln.get("measured_net")
    ded = ln.get("deductions") or []
    add = ln.get("additions") or []
    res = {"line_id": ln.get("line_id"), "trade": ln.get("trade"), "item_code": ln.get("item_code"),
           "floor": loc.get("floor"), "element_id": loc.get("element_id"), "unit": unit, "category": OK,
           "severity": "", "issues": "", "gross": _r(gross) if _isnum(gross) else None, "deductions_n": len(ded),
           "deductions_sum": None, "additions_sum": None, "measured_net": _r(net) if _isnum(net) else None,
           "gross_minus_net": None, "residual": None, "export_deductions_total": None, "detail": "",
           "shadow_explains_gap": None}
    sp, sn, ss, so = _shadow(ln)
    res.update({"shadow_path": sp, "shadow_n": sn, "shadow_sum": ss, "shadow_open": so})
    if not isinstance(ded, list) or not isinstance(add, list):
        raise DeductionsError(f"{ln.get('line_id')}: deductions / additions must be lists")
    if not _isnum(gross) or not _isnum(net):
        res["category"] = NOT_APPLICABLE
        res["detail"] = "no numeric gross" if not _isnum(gross) else "no measured_net (held / excluded / blocked)"
        return res
    d_items = [_item(d) for d in ded]
    a_items = [_item(a) for a in add]
    res["gross_minus_net"] = _r(gross - net)
    res["shadow_explains_gap"] = bool(ss is not None and so == 0 and abs(ss - (gross - net)) <= tol)
    issues = {}

    bad_u = sorted({u for _q, _i, us in d_items + a_items for u in us if u != unit})
    if bad_u:
        issues["MIXED_UNITS"] = f"line in {unit}, a deduction / addition in {bad_u}"
    dq = [q for q, _i, _u in d_items]
    aq = [q for q, _i, _u in a_items]
    if any(q is not None and q < -1e-12 for q in dq + aq):
        issues["NEGATIVE_DEDUCTION"] = "a deduction / addition below 0"
    dsum = sum(q for q in dq if q is not None)
    asum = sum(q for q in aq if q is not None)
    res["deductions_sum"] = _r(dsum) if ded else None
    res["additions_sum"] = _r(asum) if add else None
    if ded and dsum > gross + tol:
        issues["EXCEEDS_GROSS"] = f"deductions {dsum:.6f} > gross {gross:.6f} {unit}"
    n_open = sum(1 for q in dq + aq if q is None)
    if n_open:
        issues["NON_NUMERIC"] = f"{n_open} deduction / addition(s) without one numeric quantity"
    else:
        residual = gross - dsum + asum - net
        res["residual"] = _r(residual)
        if abs(residual) > tol:
            if not ded and not add:
                issues["EMPTY_DEDUCTIONS"] = f"gross - net = {gross - net:.6f} {unit} with an empty canonical list"
            else:
                issues["NOT_SUMMING"] = f"gross - deductions + additions - net = {residual:.6f} {unit}"
    if ded:
        _n, etot = E._deductions(ln)          # the export's own reader: what BOQ.csv deductions_total will show
        res["export_deductions_total"] = _r(etot)
        if etot is None:
            issues["EXPORT_TOTAL_BLANK"] = ("tools/boq_export_v1 reads no quantity from this list: BOQ.csv shows "
                                            f"deductions_n {len(ded)} with a blank deductions_total")
        elif not n_open and abs(etot - dsum) > tol:
            issues["EXPORT_TOTAL_BLANK"] = f"the export reads {etot:.6f}, the list sums {dsum:.6f} {unit}"
    n_noid = sum(1 for _q, i, _u in d_items if i is None)
    if n_noid:
        issues["MISSING_ID"] = f"{n_noid} deduction(s) without the id of what they deduct"
    if issues:
        codes = [c for c, _s in CATEGORIES if c in issues]
        res["category"], res["severity"] = codes[0], SEVERITY[codes[0]]
        res["issues"] = " ".join(codes)
        res["detail"] = "; ".join(f"{c}: {issues[c]}" for c in codes)
    return res


def check_lines(lines, tol=TOL):
    """-> report dict: every finding by line, and per (trade, item code, unit) the counts and quantities."""
    if not isinstance(lines, list):
        raise DeductionsError("lines must be a list of canonical lines")
    ids = [ln.get("line_id") for ln in lines]
    if len(set(ids)) != len(ids):
        raise DeductionsError("two lines with one line id (refused: a finding could not be bound to its line)")
    results = [check_line(ln, tol) for ln in lines]
    fam = defaultdict(lambda: {"lines": 0, "checked": 0, "not_applicable": 0, "ok": 0, "flagged": 0, "refused": 0,
                               "by_category": defaultdict(int), "by_issue": defaultdict(int), "flagged_gross": 0.0, "flagged_net": 0.0,
                               "flagged_gross_minus_net": 0.0, "shadow_explains_gap": 0, "shadow_present": 0})
    for r in results:
        f = fam[(str(r["trade"] or ""), str(r["item_code"] or ""), str(r["unit"] or ""))]
        f["lines"] += 1
        if r["category"] == NOT_APPLICABLE:
            f["not_applicable"] += 1
            continue
        f["checked"] += 1
        if r["category"] == OK:
            f["ok"] += 1
            continue
        f["flagged" if r["severity"] == FLAG else "refused"] += 1
        f["by_category"][r["category"]] += 1
        for c in r["issues"].split():
            f["by_issue"][c] += 1
        f["flagged_gross"] += r["gross"]
        f["flagged_net"] += r["measured_net"]
        f["flagged_gross_minus_net"] += r["gross_minus_net"]
        f["shadow_explains_gap"] += 1 if r["shadow_explains_gap"] else 0
        f["shadow_present"] += 1 if r["shadow_n"] else 0
    families = []
    for (t, c, u), f in sorted(fam.items()):
        bad = f["flagged"] + f["refused"]
        families.append({"trade": t, "item_code": c, "unit": u, "lines": f["lines"], "checked": f["checked"],
                         "not_applicable": f["not_applicable"], "ok": f["ok"], "flagged": f["flagged"],
                         "refused": f["refused"], "by_category": dict(sorted(f["by_category"].items())),
                         "by_issue": dict(sorted(f["by_issue"].items())),
                         "flagged_gross": _r(f["flagged_gross"]) if bad else None,
                         "flagged_net": _r(f["flagged_net"]) if bad else None,
                         "flagged_gross_minus_net": _r(f["flagged_gross_minus_net"]) if bad else None,
                         "findings_with_shadow_list": f["shadow_present"],
                         "findings_shadow_explains_gap": f["shadow_explains_gap"]})
    findings = [r for r in results if r["severity"]]
    findings.sort(key=lambda r: (str(r["trade"] or ""), str(r["item_code"] or ""), str(r["floor"] or ""),
                                 str(r["element_id"] or ""), str(r["line_id"] or "")))
    totals = defaultdict(int)
    for r in results:
        totals[r["category"]] += 1
    return {"schema": SCHEMA, "tolerance": tol, "lines": len(lines),
            "categories": dict(sorted(totals.items())),
            "flagged": sum(1 for r in findings if r["severity"] == FLAG),
            "refused": sum(1 for r in findings if r["severity"] == REFUSED),
            "families": families, "findings": findings}


def exit_code(report):
    return 2 if report["refused"] else (1 if report["flagged"] else 0)


def assert_exportable(lines, tol=TOL):
    """the export guard: raise DeductionsError naming every finding; nothing may be written from such lines."""
    rep = check_lines(lines, tol)
    if rep["findings"]:
        head = "; ".join(f"{r['line_id']} {r['category']}" for r in rep["findings"][:10])
        more = f" (+{len(rep['findings']) - 10} more)" if len(rep["findings"]) > 10 else ""
        raise DeductionsError(f"{len(rep['findings'])} line(s) whose canonical deductions do not reconcile gross to "
                              f"net (missing, incomplete, unreadable or inconsistent; export refused, never a silent "
                              f"gross): "
                              f"{head}{more}")
    return rep


def findings_csv(report):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in report["findings"]:
        w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.{DEC}f}" if isinstance(r[k], float) else r[k]))
                    for k in CSV_COLUMNS})
    return buf.getvalue()


def _load(path):
    from engine.reference_mapping import refuse_if_sealed
    refuse_if_sealed(str(path))
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main_check(argv):
    ap = argparse.ArgumentParser(prog="t330_deductions_check.py check")
    ap.add_argument("--lines", required=True)
    ap.add_argument("--json", help="write the full report here")
    ap.add_argument("--csv", help="write one row per finding here")
    a = ap.parse_args(argv)
    rep = check_lines(_load(a.lines))
    if a.json:
        Path(a.json).write_text(json.dumps(rep, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    if a.csv:
        Path(a.csv).write_text(findings_csv(rep), encoding="utf-8")
    print(json.dumps({"lines": rep["lines"], "categories": rep["categories"], "flagged": rep["flagged"],
                      "refused": rep["refused"],
                      "families_with_findings": [f for f in rep["families"] if f["flagged"] or f["refused"]]},
                     indent=1, sort_keys=True, ensure_ascii=False))
    return exit_code(rep)


def main_export(argv):
    ap = argparse.ArgumentParser(prog="t330_deductions_check.py export", add_help=False)
    ap.add_argument("--lines", required=True)
    a, _rest = ap.parse_known_args(argv)
    try:
        assert_exportable(_load(a.lines))
    except DeductionsError as e:
        print(f"T-330 DEDUCTIONS GUARD: {e}", file=sys.stderr)
        return 2
    return E.main(list(argv))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "check":
        return main_check(argv[1:])
    if argv and argv[0] == "export":
        return main_export(argv[1:])
    print("usage: t330_deductions_check.py check|export --lines FILE ...", file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
