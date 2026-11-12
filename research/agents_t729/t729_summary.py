"""T-729: the run-of-record summary (item codes, units, states, quantities, line ids and hashes only) from a finished
research/agents_t729/v3075_run.py output directory -> out/T729_SUMMARY.json. Reads only the V3_0_74 / V3_0_75 files.

    python3 -I research/agents_t729/t729_summary.py --run <dir with V3_0_74/75_*> --out research/agents_t729/out/T729_SUMMARY.json
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    d = Path(a.run)
    run = json.loads((d / "V3_0_75_RUN.json").read_text(encoding="utf-8"))
    led = json.loads((d / "V3_0_75_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    diff = list(csv.DictReader(io.StringIO((d / "V3_0_75_DIFF.csv").read_text(encoding="utf-8"))))
    rows = [{k: r.get(k) for k in ("piece", "action", "change", "line_id", "item_code", "unit", "before_base",
                                   "after_v3_0_75", "beside", "companion", "restates", "rule", "fix", "class",
                                   "evidence_status")} for r in led["rows"]]
    doc = {"schema": "URBAN_T729_SUMMARY_V1", "method": run["method"], "extends": run["extends"],
           "lines_sha256": {v: hashlib.sha256((d / f"V3_0_{v}_BOQ_LINES.json").read_bytes()).hexdigest()
                            for v in ("74", "75")},
           "identity": {k: ident[k] for k in ("base_lines", "v3_0_75_lines", "replaced", "added", "outside_rows",
                                              "outside_rows_identical_to_base", "outside_rows_sha256",
                                              "formwork_concrete", "diff")},
           "totals_moved_by_code": run["totals_moved_by_code"], "census_before": ident["census_before"],
           "census_after": ident["census_after"],
           "diff_changed": sorted(r["line_id"] for r in diff if r["vs_base"] != "SAME"),
           "rows": rows, "waiting_pieces": sorted(run["waiting_pieces"])}
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print("summary:", doc["lines_sha256"]["74"][:8], "->", doc["lines_sha256"]["75"][:8], doc["identity"]["diff"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
