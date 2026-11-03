"""T-350 r4: summary_t350r4.json from a finished v3048_run.py directory (ids, states, quantities, hashes only).

    .work/venv/bin/python -I research/agents_t350r4/t350r4_summary.py <run dir>/v3048 [--write]
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build(d):
    d = Path(d)
    led = json.loads((d / "V3_0_48_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    run = json.loads((d / "V3_0_48_RUN.json").read_text(encoding="utf-8"))
    sha = {n: hashlib.sha256((d / n).read_bytes()).hexdigest() for n in ("V3_0_47_BOQ_LINES.json",
                                                                          "V3_0_48_BOQ_LINES.json")}
    rows = [{"line_id": r["line_id"], "item_code": r["item_code"], "element_id": r["element_id"],
             "action": r["action"], "change": r["change"], "before_v2_9": r["before_released_v2_9"],
             "before": r["before_base"], "after": r["after_v3_0_48"], "evidence_status": r["evidence_status"],
             "still_held": [h["what"] + ": " + h["why"][:160] for h in r["still_held"] or ()]} for r in led["rows"]]
    diff = list(csv.DictReader(io.StringIO((d / "V3_0_48_DIFF.csv").read_text(encoding="utf-8"))))
    moved = [{k: x[k] for k in ("line_id", "item_code", "element_id", "vs_base", "vs_released_v2_9", "base",
                                "v3_0_48")} for x in diff if x["vs_base"] != "SAME"]
    ident = run["identity"]
    return {"task": "T-350 r4", "method": run["method"], "extends": run["extends"],
            "base_sha256": sha["V3_0_47_BOQ_LINES.json"], "candidate_sha256": sha["V3_0_48_BOQ_LINES.json"],
            "lines": {"base": ident["base_lines"], "v3_0_48": ident["v3_0_48_lines"], "added": ident["added"],
                      "replaced": ident["replaced"], "outside_identical": ident["outside_rows_identical_to_base"],
                      "outside_rows_sha256": ident["outside_rows_sha256"]},
            "diff": ident["diff"], "earthworks": ident["earthworks"],
            "totals_moved_by_code": run["totals_moved_by_code"], "rows": rows, "line_diff_vs_v3_0_47": moved}


if __name__ == "__main__":
    s = build(sys.argv[1])
    text = json.dumps(s, ensure_ascii=False, indent=1) + "\n"
    if "--write" in sys.argv:
        (HERE / "summary_t350r4.json").write_text(text, encoding="utf-8")
    print(text)
