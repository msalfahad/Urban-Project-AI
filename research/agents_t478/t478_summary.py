"""T-478: summary_t478.json from a finished v3045_run.py output (codes, ids, states, quantities; no drawing content).

    .work/venv/bin/python -I research/agents_t478/t478_summary.py <out of v3045_run.py> [--write]
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(argv):
    src = Path(argv[1])
    run = json.loads((src / "V3_0_45_RUN.json").read_text(encoding="utf-8"))
    led = json.loads((src / "V3_0_45_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    rows = [{"line_id": r["line_id"], "action": r["action"], "element_id": r["element_id"],
             "v2_9": r["before_released_v2_9"], "v3_0_44": r["before_base"], "v3_0_45": r["after_v3_0_45"],
             "evidence_status": r["evidence_status"], "still_held": r["still_held"]} for r in led["rows"]]
    lines = (src / "V3_0_45_BOQ_LINES.json").read_bytes()
    base = (src / "V3_0_44_BOQ_LINES.json").read_bytes()
    out = {"method": run["method"], "extends": run["extends"], "released_default": run["released_default"],
           "base_v3_0_44_lines_sha256": hashlib.sha256(base).hexdigest(),
           "v3_0_45_lines_sha256": hashlib.sha256(lines).hexdigest(),
           "identity": {k: run["identity"][k] for k in ("base_lines", "v3_0_45_lines", "replaced", "added",
                                                        "outside_rows", "outside_rows_identical_to_base",
                                                        "outside_rows_sha256", "blinding", "earthworks", "skirting",
                                                        "diff")},
           "totals_moved_by_code": run["totals_moved_by_code"], "rows": rows, "plate": run["plate"],
           "waiting": {k: v for k, v in run["waiting_pieces"].items() if k.startswith("T478_")}}
    text = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        (HERE / "summary_t478.json").write_text(text, encoding="utf-8")
        print("written summary_t478.json")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
