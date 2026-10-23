"""Trade completeness runner (T-236): engine/source/trade_completeness_v1.check() on one project's input file.

    python3 -I tools/trade_completeness.py <input.json> --out <dir>      writes TRADE_COMPLETENESS.json,
                                                                         TRADE_COMPLETENESS_TRADES.csv (one row per
                                                                         trade), TRADE_COMPLETENESS_ELEMENTS.csv,
                                                                         REFERENCE_LINE_ROWS.json (T-235 part (3))
    python3 -I tools/trade_completeness.py <input.json> --print          the per-trade table only

<input.json>: {"project_id", "inventories", "register", "lines" (canonical BOQ lines, or "lines_file": a path to a
BOQ_LINES.json list / {"lines": [...]}), "line_links", "verdicts", "exclusions", "opening_census", "levels",
"accuracy"} as documented in the module. The runner reads and writes nothing else; it changes no line and no
quantity. Exit 0 always when the check ran (a gap is a finding, not a failure); exit 2 on a refused input.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.source import trade_completeness_v1 as TC  # noqa: E402

DEFAULT_GUARD_CLASS = "CHECK_ONLY"      # T-212 property P1: a runner of a check module; writes no BOQ quantity

TRADE_COLUMNS = ("trade", "principal", "status", "lines", "unlinked_lines", "found", "measured", "held", "verified",
                 "missing", "duplicated", "unresolved", "geometry_only", "conflict", "agreement_conflict", "excluded",
                 "register_only", "out_of_inventory_scope", "completeness_n_d", "verified_n_d", "inventory_sources")
ELEMENT_COLUMNS = ("trade", "key", "status", "measurement", "duplicated", "inventory_agreement", "sources", "refs",
                   "lines", "reason")


def load(path):
    p = Path(path)
    d = json.loads(p.read_text(encoding="utf-8"))
    if "lines_file" in d:
        lf = Path(d.pop("lines_file"))
        lf = lf if lf.is_absolute() else (p.parent / lf)
        raw = json.loads(lf.read_text(encoding="utf-8"))
        d["lines"] = raw["lines"] if isinstance(raw, dict) else raw
    return d


def run(d):
    kw = {k: d[k] for k in ("inventories", "register", "lines", "line_links", "verdicts", "exclusions",
                            "opening_census", "levels", "accuracy") if k in d}
    return TC.check(**kw)


def trade_rows(rep):
    comp = {r["trade"]: r for r in rep["completeness_table"]}
    ver = {r["trade"]: r for r in rep["verified_table"]}
    for t in rep["trades"]:
        row = dict(t)
        row["completeness_n_d"] = f"{comp[t['trade']]['n']} / {comp[t['trade']]['d']}"
        row["verified_n_d"] = f"{ver[t['trade']]['n']} / {ver[t['trade']]['d']}"
        row["inventory_sources"] = " ; ".join(t["inventory_sources"])
        yield {k: row[k] for k in TRADE_COLUMNS}


def _csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: (" | ".join(r[k]) if isinstance(r.get(k), list) else r.get(k)) for k in cols})


def write(rep, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "TRADE_COMPLETENESS.json").write_text(TC.dumps(rep), encoding="utf-8")
    _csv(out / "TRADE_COMPLETENESS_TRADES.csv", TRADE_COLUMNS, trade_rows(rep))
    _csv(out / "TRADE_COMPLETENESS_ELEMENTS.csv", ELEMENT_COLUMNS, rep["elements"])
    (out / "REFERENCE_LINE_ROWS.json").write_text(json.dumps(TC.reference_line_rows(rep), indent=1, sort_keys=True,
                                                             ensure_ascii=False), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--out")
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args(argv)
    try:
        rep = run(load(a.input))
    except TC.CompletenessError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    if a.out:
        write(rep, a.out)
    if a.print or not a.out:
        for r in trade_rows(rep):
            print(f"{r['trade']:<24} {r['status']:<27} found {r['found']:>4}  completeness {r['completeness_n_d']:>9}  "
                  f"verified {r['verified_n_d']:>9}  missing {r['missing']:>3}  dup {r['duplicated']:>3}  "
                  f"held {r['held']:>3}  lines {r['lines']:>4}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
