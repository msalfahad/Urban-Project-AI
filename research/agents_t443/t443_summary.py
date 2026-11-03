"""T-443: summary_t443.json from a finished v3046_run.py directory (ids, states, quantities, hashes only).

    .work/venv/bin/python -I research/agents_t443/t443_summary.py <run dir>/v3046 [--write]
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build(d):
    d = Path(d)
    led = json.loads((d / "V3_0_46_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    run = json.loads((d / "V3_0_46_RUN.json").read_text(encoding="utf-8"))
    sha = {n: hashlib.sha256((d / n).read_bytes()).hexdigest() for n in ("V3_0_45_BOQ_LINES.json",
                                                                          "V3_0_46_BOQ_LINES.json")}
    rows = [{"line_id": r["line_id"], "element_id": r["element_id"], "floor": r["floor"], "room_id": r["room_id"],
             "action": r["action"], "change": r["change"], "before": r["before_base"], "after": r["after_v3_0_46"],
             "evidence_status": r["evidence_status"]} for r in led["rows"]]
    ident = run["identity"]
    return {"task": "T-443", "method": run["method"], "extends": run["extends"],
            "base_sha256": sha["V3_0_45_BOQ_LINES.json"], "candidate_sha256": sha["V3_0_46_BOQ_LINES.json"],
            "lines": {"base": ident["base_lines"], "v3_0_46": ident["v3_0_46_lines"], "added": ident["added"],
                      "replaced": ident["replaced"], "outside_identical": ident["outside_rows_identical_to_base"]},
            "stair_rooms": ident["stair_rooms"], "totals_moved_by_code": run["totals_moved_by_code"],
            "parents": run["piece_logs"][0]["parents"], "rows": rows}


if __name__ == "__main__":
    s = build(sys.argv[1])
    text = json.dumps(s, ensure_ascii=False, indent=1) + "\n"
    if "--write" in sys.argv:
        (HERE / "summary_t443.json").write_text(text, encoding="utf-8")
    print(text)
