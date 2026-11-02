"""T-350: summary_t350.json from a finished research/agents_t350/v3043_run.py run (values, states, engine ids and file
hashes only; no coordinate, no name, no drawing text).

    python3 -I research/agents_t350/t350_summary.py <run>/v3043 [--write]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "summary_t350.json"


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build(run):
    run = Path(run)
    led = json.loads((run / "V3_0_43_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    r = json.loads((run / "V3_0_43_RUN.json").read_text(encoding="utf-8"))
    rows = []
    for x in led["rows"]:
        rec = x["record"]
        rows.append({"line_id": x["line_id"], "item_code": x["item_code"], "element_id": x["element_id"],
                     "action": x["action"], "v3_0_42": x["before_v3_0_42"], "v3_0_43": x["after_v3_0_43"],
                     "evidence_status": x["evidence_status"],
                     "bound": rec.get("bound"), "at_least_m3": rec.get("at_least_m3"),
                     "upper_m3": rec.get("upper_m3"), "coef_m3_per_m_depth": rec.get("coef_m3_per_m_depth"),
                     "bound_lines": len(rec.get("bound_lines") or ()), "range_was": rec.get("was"),
                     "tasks": rec.get("tasks")})
    i = r["identity"]
    return {"method": r["method"], "extends": r["extends"], "released_default": r["released_default"],
            "files_sha256": {p.name: _sha(p) for p in sorted(run.glob("V3_0_4[23]_BOQ_LINES.json"))},
            "identity": {k: i[k] for k in ("v3_0_42_lines", "v3_0_43_lines", "added", "replaced",
                                           "outside_rows_identical_to_v3_0_42", "outside_rows_sha256", "diff",
                                           "earthworks")},
            "totals_moved_by_code": r["totals_moved_by_code"], "rows": rows,
            "waiting_pieces": sorted(k for k in r["waiting_pieces"] if k.startswith("T350"))}


if __name__ == "__main__":
    s = build(sys.argv[1])
    if "--write" in sys.argv:
        OUT.write_text(json.dumps(s, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print("written", OUT.relative_to(ROOT))
    print(json.dumps({k: s[k] for k in ("files_sha256", "identity")}, indent=1))
