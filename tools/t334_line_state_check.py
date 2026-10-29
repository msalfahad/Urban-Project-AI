"""LINE-STATE CONSISTENCY CHECK (task T-334) - a read-only export-integrity check beside tools/boq_export_v1.py. It
computes, changes and approves no engine quantity, edits no line and no frozen file, and nothing in engine/ imports it.
General: no project name, item code or element id is written in this module.

Why. A canonical line (engine/source/boq_line.py) states its state FOUR times: the evidence_state word, the
measured_net figure, the bounded_range and the human-readable calculation.formula (which the export prints). The
schema validator (boq_line.validate) ties the state word to the presence of measured_net only. Nothing ties the formula
text or the range cause to the state, so a released quantity can print 'held: ' as its formula, and a line taken off
(NOT_APPLICABLE) can keep its old gross figure: a reader of BOQ.csv sees two different states on one row. This check
makes every such disagreement visible, line by line, and lets the export refuse it.

Kinds (every one that applies is listed in 'issues'; a line's category is the first, most severe first):

  REFUSED  UNKNOWN_STATE          the evidence_state is not a canonical word (boq_line.EVIDENCE)
  REFUSED  HELD_AS_ZERO           a hold shown as 0: a valued line with measured_net 0 whose formula opens with a hold
                                  word, or a bounded line whose range is 0 .. 0
  REFUSED  HELD_WITH_FIGURE       a line without a quantity state (BLOCKED_RFI / BOUNDED_EXPOSURE / EXCLUDED /
                                  NOT_APPLICABLE) carries a measured_net or a numeric gross, or a terminal line
                                  (BLOCKED_RFI / EXCLUDED / NOT_APPLICABLE) carries a bounded_range
  REFUSED  VALUED_WITH_HELD_TEXT  a quantity line (MEASURED / SOURCE_DERIVED / PROVISIONAL with a measured_net) whose
                                  formula opens with a hold word (HOLD_WORDS: 'held:', 'unresolved:', 'blocked', ...)
  REFUSED  RANGE_WITHOUT_CAUSE    a bounded_range without a named basis, a BOUNDED_EXPOSURE line without a range or
                                  without the question that unlocks it (rfi.question), or a range with low > high
  REFUSED  RANGE_EXCLUDES_NET     a quantity line whose own range does not contain its measured_net
  REFUSED  SOURCE_NOT_NAMED       a SOURCE_DERIVED / MEASURED line names no source document (a file with its sha256)
  FLAG     FORMULA_FIGURE_DISAGREES  the formula's concluding figure in the line's own unit (the last '= x <unit>' or
                                  'net x <unit>') is not the measured_net (quantity line, to the figure's printed
                                  decimals) or lies outside the line's range (bounded line); on a line without a
                                  quantity and without a range any concluding figure in the line's unit disagrees
A diagnostic that never fails a line: NOTE_OPEN_RFI_ON_VALUED (a quantity line that also carries an rfi: an owner rule
such as 'quantity without material' publishes the quantity and holds the material; listed, never refused).

    python3 -I tools/t334_line_state_check.py check --lines V3_0_x_BOQ_LINES.json [--json OUT.json] [--csv OUT.csv]
        exit 0 clean, 1 FLAG only, 2 any REFUSED
    python3 -I tools/t334_line_state_check.py export --lines ... --candidate-version ... --out DIR [any
        tools/boq_export_v1.py option]
        the GUARDED export: the check runs first; on any finding NOTHING is written (exit 2, the findings printed),
        else tools/boq_export_v1.main runs unchanged with the same arguments
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

DEFAULT_GUARD_CLASS = "TOOLING"        # T-212: a read-only check; it produces no quantity

SCHEMA = "URBAN_LINE_STATE_CHECK_V1"
TOL = 0.0005                           # tools/boq_export_v1.QTY_MATCH_TOL: the export's own quantity tolerance
DEC = 6

from engine.source import boq_line as BL       # noqa: E402
from tools import boq_export_v1 as E           # noqa: E402  (its main: the guarded export runs it unchanged)

QUANTITY = BL.QUANTITY_STATES                  # MEASURED, SOURCE_DERIVED, PROVISIONAL
TERMINAL = BL.TERMINAL_NO_QUANTITY             # BLOCKED_RFI, EXCLUDED_WITH_REASON, NOT_APPLICABLE_WITH_EVIDENCE
SOURCED = ("MEASURED", "SOURCE_DERIVED")
# a formula that OPENS with one of these words states a hold (case-insensitive, whole word)
HOLD_WORDS = ("held", "hold", "unresolved", "blocked", "conflict", "not measured", "not quantified", "unquantified")
HOLD_RE = re.compile(r"^\s*(?:" + "|".join(re.escape(w) for w in HOLD_WORDS) + r")\b", re.IGNORECASE)

REFUSED, FLAG = "REFUSED", "FLAG"
CATEGORIES = (  # (code, severity), most severe first: a line's category is the first that applies
    ("UNKNOWN_STATE", REFUSED), ("HELD_AS_ZERO", REFUSED), ("HELD_WITH_FIGURE", REFUSED),
    ("VALUED_WITH_HELD_TEXT", REFUSED), ("RANGE_WITHOUT_CAUSE", REFUSED), ("RANGE_EXCLUDES_NET", REFUSED),
    ("SOURCE_NOT_NAMED", REFUSED), ("FORMULA_FIGURE_DISAGREES", FLAG))
SEVERITY = dict(CATEGORIES)
OK = "OK"
NOTE_OPEN_RFI = "NOTE_OPEN_RFI_ON_VALUED"
CSV_COLUMNS = ("line_id", "trade", "item_code", "floor", "element_id", "unit", "evidence_state", "category", "severity",
               "issues", "measured_net", "gross", "range_low", "range_high", "formula_head", "formula_figure", "detail")


class LineStateError(ValueError):
    pass


def _isnum(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _r(x):
    return None if x is None else round(float(x), DEC)


def formula_figure(formula, unit):
    """the formula's CONCLUDING figure in the line's own unit: the last '= x <unit>' or 'net x <unit>' -> (value, printed
    decimals) or (None, None). A figure in another unit (a length on a kg line, an area on an m3 line) is a reading,
    not the line's quantity, and is ignored."""
    if not formula or not unit:
        return None, None
    pat = r"(?:=|\bnet)\s*(-?\d+(?:\.\d+)?)\s*" + re.escape(unit) + r"(?![A-Za-z0-9])"
    ms = list(re.finditer(pat, str(formula)))
    if not ms:
        return None, None
    x = ms[-1].group(1)
    return float(x), (len(x.split(".")[1]) if "." in x else 0)


def _has_source(ln):
    docs = (ln.get("source") or {}).get("documents") or []
    return any(isinstance(d, dict) and d.get("file") and d.get("sha256") for d in docs)


def check_line(ln, tol=TOL):
    """-> one result dict: category OK or the first finding code in CATEGORIES order; 'issues' = every code that
    applies; 'notes' = diagnostics that never fail a line."""
    ev = ln.get("evidence_state")
    unit = ln.get("unit")
    loc = ln.get("location") or {}
    net, gross = ln.get("measured_net"), ln.get("gross")
    br = ln.get("bounded_range")
    f = str(((ln.get("calculation") or {}).get("formula")) or "")
    held_text = bool(HOLD_RE.match(f))
    fig, fdec = formula_figure(f, unit)
    res = {"line_id": ln.get("line_id"), "trade": ln.get("trade"), "item_code": ln.get("item_code"),
           "floor": loc.get("floor"), "element_id": loc.get("element_id"), "unit": unit, "evidence_state": ev,
           "category": OK, "severity": "", "issues": "", "notes": "",
           "measured_net": _r(net) if _isnum(net) else None, "gross": _r(gross) if _isnum(gross) else None,
           "range_low": None, "range_high": None, "formula_head": f[:80], "formula_figure": fig, "detail": ""}
    issues = {}
    lo = hi = None
    if br is not None:
        if not isinstance(br, dict):
            issues["RANGE_WITHOUT_CAUSE"] = "bounded_range is not a {low, high, basis} record"
        else:
            lo, hi = br.get("low"), br.get("high")
            res["range_low"], res["range_high"] = (_r(lo) if _isnum(lo) else None), (_r(hi) if _isnum(hi) else None)
    if ev not in BL.EVIDENCE:
        issues["UNKNOWN_STATE"] = f"evidence_state {ev!r} is not one of {list(BL.EVIDENCE)}"
    valued = ev in QUANTITY and _isnum(net)
    # ---- a hold shown as 0
    if valued and abs(net) <= 1e-12 and held_text:
        issues["HELD_AS_ZERO"] = "measured_net 0 on a line whose formula states a hold"
    if ev == "BOUNDED_EXPOSURE" and _isnum(lo) and _isnum(hi) and abs(lo) <= 1e-12 and abs(hi) <= 1e-12:
        issues["HELD_AS_ZERO"] = "a held range of 0 .. 0"
    # ---- a line without a quantity carries a figure
    if ev in BL.EVIDENCE and ev not in QUANTITY:
        figs = []
        if net is not None:
            figs.append(f"measured_net {net}")
        if _isnum(gross):
            figs.append(f"gross {gross} {unit}")
        if ev in TERMINAL and br is not None:
            figs.append("a bounded_range")
        if figs:
            issues["HELD_WITH_FIGURE"] = f"a {ev} line carries " + " and ".join(figs)
    if ev in QUANTITY and not _isnum(net):
        issues["HELD_WITH_FIGURE"] = f"a {ev} line without a numeric measured_net (state word and quantity disagree)"
    # ---- a quantity printed under a hold text
    if valued and held_text and "HELD_AS_ZERO" not in issues:
        issues["VALUED_WITH_HELD_TEXT"] = f"{ev} {net} {unit} with a formula that opens {f[:40]!r}"
    # ---- a range needs its cause
    if isinstance(br, dict):
        if not str(br.get("basis") or "").strip():
            issues["RANGE_WITHOUT_CAUSE"] = "a bounded_range without its basis (the named cause)"
        elif _isnum(lo) and _isnum(hi) and lo > hi + tol:
            issues["RANGE_WITHOUT_CAUSE"] = f"range low {lo} > high {hi}"
        elif not (_isnum(lo) and _isnum(hi)):
            issues["RANGE_WITHOUT_CAUSE"] = "a bounded_range without numeric low and high"
    if ev == "BOUNDED_EXPOSURE":
        if br is None:
            issues["RANGE_WITHOUT_CAUSE"] = "a BOUNDED_EXPOSURE line without its range"
        elif not str(((ln.get("rfi") or {}).get("question")) or "").strip():
            issues.setdefault("RANGE_WITHOUT_CAUSE", "a BOUNDED_EXPOSURE line without the question that unlocks it")
    if valued and isinstance(br, dict) and _isnum(lo) and _isnum(hi) and not (lo - tol <= net <= hi + tol):
        issues["RANGE_EXCLUDES_NET"] = f"measured_net {net} outside its own range {lo} .. {hi} {unit}"
    # ---- SOURCE_DERIVED / MEASURED names its source
    if ev in SOURCED and not _has_source(ln):
        issues["SOURCE_NOT_NAMED"] = f"a {ev} line names no source document (file + sha256)"
    # ---- the formula's concluding figure agrees with the state
    if fig is not None:
        ftol = max(0.5 * 10 ** -fdec, tol) + 1e-9
        if valued and abs(fig - net) > ftol:
            issues["FORMULA_FIGURE_DISAGREES"] = (f"formula concludes {fig} {unit}, measured_net {net} {unit}"
                                                  + (f" (= gross {gross})" if _isnum(gross) and abs(fig - gross) <= ftol
                                                     else ""))
        elif ev not in QUANTITY and _isnum(lo) and _isnum(hi) and not (lo - ftol <= fig <= hi + ftol):
            issues["FORMULA_FIGURE_DISAGREES"] = (f"formula concludes {fig} {unit}, outside the line's range "
                                                  f"{lo} .. {hi} {unit}"
                                                  + (f" (= gross {gross})" if _isnum(gross) and abs(fig - gross) <= ftol
                                                     else ""))
        elif ev not in QUANTITY and br is None:
            issues["FORMULA_FIGURE_DISAGREES"] = f"formula concludes {fig} {unit} on a {ev} line without a quantity"
    if valued and ln.get("rfi"):
        res["notes"] = NOTE_OPEN_RFI
    if issues:
        codes = [c for c, _s in CATEGORIES if c in issues]
        res["category"], res["severity"] = codes[0], SEVERITY[codes[0]]
        res["issues"] = " ".join(codes)
        res["detail"] = "; ".join(f"{c}: {issues[c]}" for c in codes)
    return res


def check_lines(lines, tol=TOL):
    """-> report dict: every finding by line; per (trade, item code, unit, state) the counts and the quantity the
    findings carry (released net, held range)."""
    if not isinstance(lines, list):
        raise LineStateError("lines must be a list of canonical lines")
    ids = [ln.get("line_id") for ln in lines]
    if len(set(ids)) != len(ids):
        raise LineStateError("two lines with one line id (refused: a finding could not be bound to its line)")
    results = [check_line(ln, tol) for ln in lines]
    fam = defaultdict(lambda: {"lines": 0, "ok": 0, "flagged": 0, "refused": 0, "by_issue": defaultdict(int),
                               "findings_net": 0.0, "findings_range_low": 0.0, "findings_range_high": 0.0,
                               "notes": 0})
    for r in results:
        f = fam[(str(r["trade"] or ""), str(r["item_code"] or ""), str(r["unit"] or ""), str(r["evidence_state"] or ""))]
        f["lines"] += 1
        f["notes"] += 1 if r["notes"] else 0
        if r["category"] == OK:
            f["ok"] += 1
            continue
        f["flagged" if r["severity"] == FLAG else "refused"] += 1
        for c in r["issues"].split():
            f["by_issue"][c] += 1
        f["findings_net"] += r["measured_net"] or 0.0
        f["findings_range_low"] += r["range_low"] or 0.0
        f["findings_range_high"] += r["range_high"] or 0.0
    families = []
    for (t, c, u, s), f in sorted(fam.items()):
        bad = f["flagged"] + f["refused"]
        families.append({"trade": t, "item_code": c, "unit": u, "evidence_state": s, "lines": f["lines"],
                         "ok": f["ok"], "flagged": f["flagged"], "refused": f["refused"],
                         "by_issue": dict(sorted(f["by_issue"].items())),
                         "findings_net": _r(f["findings_net"]) if bad else None,
                         "findings_range_low": _r(f["findings_range_low"]) if bad else None,
                         "findings_range_high": _r(f["findings_range_high"]) if bad else None,
                         "notes_open_rfi_on_valued": f["notes"]})
    findings = [r for r in results if r["severity"]]
    findings.sort(key=lambda r: (str(r["trade"] or ""), str(r["item_code"] or ""), str(r["floor"] or ""),
                                 str(r["element_id"] or ""), str(r["line_id"] or "")))
    by_kind = defaultdict(int)
    for r in findings:
        for c in r["issues"].split():
            by_kind[c] += 1
    states = defaultdict(int)
    for r in results:
        states[r["category"]] += 1
    return {"schema": SCHEMA, "tolerance": tol, "lines": len(lines), "categories": dict(sorted(states.items())),
            "by_kind": dict(sorted(by_kind.items())),
            "flagged": sum(1 for r in findings if r["severity"] == FLAG),
            "refused": sum(1 for r in findings if r["severity"] == REFUSED),
            "notes": {NOTE_OPEN_RFI: sum(1 for r in results if r["notes"])},
            "note_lines": sorted(r["line_id"] for r in results if r["notes"]),
            "families": families, "findings": findings}


def exit_code(report):
    return 2 if report["refused"] else (1 if report["flagged"] else 0)


def assert_exportable(lines, tol=TOL):
    """the export guard: raise LineStateError naming the findings; nothing may be written from such lines."""
    rep = check_lines(lines, tol)
    if rep["findings"]:
        head = "; ".join(f"{r['line_id']} {r['category']}" for r in rep["findings"][:10])
        more = f" (+{len(rep['findings']) - 10} more)" if len(rep["findings"]) > 10 else ""
        raise LineStateError(f"{len(rep['findings'])} line(s) whose state word, quantity, range and formula disagree "
                             f"(export refused: one row would show two states): {head}{more}")
    return rep


def findings_csv(report):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n", extrasaction="ignore")
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
    ap = argparse.ArgumentParser(prog="t334_line_state_check.py check")
    ap.add_argument("--lines", required=True)
    ap.add_argument("--json", help="write the full report here")
    ap.add_argument("--csv", help="write one row per finding here")
    a = ap.parse_args(argv)
    rep = check_lines(_load(a.lines))
    if a.json:
        Path(a.json).write_text(json.dumps(rep, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    if a.csv:
        Path(a.csv).write_text(findings_csv(rep), encoding="utf-8")
    print(json.dumps({"lines": rep["lines"], "categories": rep["categories"], "by_kind": rep["by_kind"],
                      "flagged": rep["flagged"], "refused": rep["refused"], "notes": rep["notes"],
                      "families_with_findings": [f for f in rep["families"] if f["flagged"] or f["refused"]]},
                     indent=1, sort_keys=True, ensure_ascii=False))
    return exit_code(rep)


def main_export(argv):
    ap = argparse.ArgumentParser(prog="t334_line_state_check.py export", add_help=False)
    ap.add_argument("--lines", required=True)
    a, _rest = ap.parse_known_args(argv)
    try:
        assert_exportable(_load(a.lines))
    except LineStateError as e:
        print(f"T-334 LINE-STATE GUARD: {e}", file=sys.stderr)
        return 2
    return E.main(list(argv))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "check":
        return main_check(argv[1:])
    if argv and argv[0] == "export":
        return main_export(argv[1:])
    print("usage: t334_line_state_check.py check|export --lines FILE ...", file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
