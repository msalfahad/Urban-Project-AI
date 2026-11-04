"""T-483: summary_t483.json from a finished v3049_run.py / v3049_apply.py directory (ids, states, quantities, hashes).

    .work/venv/bin/python -I research/agents_t483/t483_summary.py <dir holding V3_0_48 + V3_0_49 files> [--write]
(the apply directory holds only V3_0_49_*: pass the base file with --base <V3_0_48_BOQ_LINES.json>)
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build(d, base=None):
    d = Path(d)
    led = json.loads((d / "V3_0_49_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    run = json.loads((d / "V3_0_49_RUN.json").read_text(encoding="utf-8"))
    b = Path(base) if base else d / "V3_0_48_BOQ_LINES.json"
    rows = [{"line_id": r["line_id"], "element_id": r["element_id"], "floor": r["floor"], "room_id": r["room_id"],
             "action": r["action"], "change": r["change"], "before": r["before_base"], "after": r["after_v3_0_49"],
             "evidence_status": r["evidence_status"]} for r in led["rows"]]
    ident = run["identity"]
    return {"task": "T-483", "method": run["method"], "extends": run["extends"],
            "base_sha256": hashlib.sha256(b.read_bytes()).hexdigest(),
            "candidate_sha256": hashlib.sha256((d / "V3_0_49_BOQ_LINES.json").read_bytes()).hexdigest(),
            "lines": {"base": ident["base_lines"], "v3_0_49": ident["v3_0_49_lines"], "added": ident["added"],
                      "replaced": ident["replaced"], "outside_identical": ident["outside_rows_identical_to_base"]},
            "remainder": ident["remainder"], "superseded_records": ident.get("superseded_records"),
            "totals_moved_by_code": run["totals_moved_by_code"], "rows": rows}


if __name__ == "__main__":
    base = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else None
    s = build(sys.argv[1], base)
    text = json.dumps(s, ensure_ascii=False, indent=1) + "\n"
    if "--write" in sys.argv:
        (HERE / "summary_t483.json").write_text(text, encoding="utf-8")
    print(text[:1500])
