"""T-460 item 2: SKIRTING_LINE_CLOSURE_V1 on a candidate's FIN.SKIRTING lines.

usage: python3 -I research/agents_t460/t460_skirting.py <lines.json> <label> [--write]
    <lines.json>  a candidate BOQ lines file (a list of lines, or {"lines": [...]}) or the merged T-296 extract
                  research/agents_t296/CANDIDATE_V3017_SKIRTING.json ({"skirting_lines": [...]})
Writes SKIRTING_CLOSURE_<label>.csv and summary_skirting_<label>.json beside this file: line ids, states, lm only.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import skirting_closure_v1 as SK  # noqa: E402

COLS = ["line_id", "evidence_state", "state", "gross", "listed_ded", "listed_add", "net", "residual_lm"]


def load(path):
    d = json.loads(Path(path).read_text())
    if isinstance(d, dict) and "skirting_lines" in d:
        return d["skirting_lines"]
    lines = d["lines"] if isinstance(d, dict) else d
    out = []
    for ln in lines:
        if ln.get("item_code") != "FIN.SKIRTING":
            continue
        out.append({"line_id": ln["line_id"], "evidence_state": ln.get("evidence_state"), "gross": ln.get("gross"),
                    "net": ln.get("measured_net"), "deductions": ln.get("deductions") or [],
                    "additions": ln.get("additions") or []})
    return out


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    L = SK.ledger(load(a[0]))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    w.writerows(L["rows"])
    txt = json.dumps(L["summary"], indent=1, sort_keys=True) + "\n"
    if "--write" in a:
        (HERE / f"SKIRTING_CLOSURE_{a[1]}.csv").write_text(buf.getvalue())
        (HERE / f"summary_skirting_{a[1]}.json").write_text(txt)
    print(buf.getvalue())
    print(txt)


if __name__ == "__main__":
    main()
