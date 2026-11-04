"""T-508: write research/agents_t508/summary_t508.json from a finished v3056_run.py run (its --out folder, outside the
repository). Only engine ids, item codes, units, states and quantities are copied (no names, no coordinates).

    python3 -I research/agents_t508/t508_summary.py <run out>/v3050
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEYS = ("V3_0_47", "V3_0_48", "V3_0_50", "V3_0_51", "V3_0_53", "V3_0_54", "V3_0_55", "V3_0_56")


def main(d):
    d = Path(d)
    chain = {k: hashlib.sha256((d / f"{k}_BOQ_LINES.json").read_bytes()).hexdigest()[:8]
             for k in KEYS if (d / f"{k}_BOQ_LINES.json").exists()}
    run = json.loads((d / "V3_0_56_RUN.json").read_text(encoding="utf-8"))
    led = json.loads((d / "V3_0_56_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    rows = []
    for r in led["rows"]:
        rec = r.get("record") or {}
        p = rec.get("stair_piece") or {}
        rows.append({"action": r["action"], "line_id": r["line_id"], "item_code": r["item_code"], "unit": r["unit"],
                     "floor": r["floor"], "element_id": r["element_id"], "before": r["before_base"],
                     "after": r["after_v3_0_56"], "evidence_status": r["evidence_status"],
                     "piece": p.get("pid") or rec.get("element"), "kind": p.get("kind"), "cls": p.get("cls"),
                     "plan_lm": p.get("plan_lm"), "risers": p.get("risers"), "returns_lm": p.get("returns_lm"),
                     "figure_beside_lm": rec.get("figure_beside_lm"), "family": rec.get("family"),
                     "pair_line": rec.get("pair_line"),
                     "landing_pieces": [{k: x.get(k) for k in ("pid", "plan_lm", "returns_lm")}
                                        for x in rec.get("pieces") or ()],
                     "retired_lm": rec.get("retired_lm"), "closed_lm": rec.get("closed_lm"),
                     "stretches": [{k: x.get(k) for k in ("segment", "lm", "carried_by")}
                                   for x in rec.get("stretches") or ()]})
    out = {"task": "T-508", "method": run["method"], "extends": run["extends"],
           "drawings": {"plan": "training-villa Drive folder / P7757_DXF_COMPRESSED.zip -> P7757.dxf sha256 ab54dd55",
                        "structural": "training-villa Drive folder / ST7757 dxf.dxf sha256 9f9d1179"},
           "chain": chain,
           "identity": {k: ident[k] for k in ("base_lines", "v3_0_56_lines", "replaced", "added", "outside_rows",
                                              "outside_rows_identical_to_base", "outside_rows_sha256",
                                              "stair_skirting", "diff")},
           "summary": led["summary"], "totals_moved_by_code": run["totals_moved_by_code"], "rows": rows}
    (HERE / "summary_t508.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                           encoding="utf-8")
    print(json.dumps({"chain": chain, "replaced": ident["replaced"], "added": ident["added"],
                      "moved": sorted(run["totals_moved_by_code"])}))


if __name__ == "__main__":
    main(sys.argv[1])
