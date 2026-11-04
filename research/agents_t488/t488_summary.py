"""T-488: write research/agents_t488/summary_t488.json from a finished v3055_run.py run (its --out folder, outside the
repository). Only engine ids, item codes, units, states and quantities are copied (no names, no coordinates).

    python3 -I research/agents_t488/t488_summary.py <run out>/v3050
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEYS = ("V3_0_47", "V3_0_48", "V3_0_50", "V3_0_51", "V3_0_53", "V3_0_55")


def main(d):
    d = Path(d)
    chain = {k: hashlib.sha256((d / f"{k}_BOQ_LINES.json").read_bytes()).hexdigest()[:8]
             for k in KEYS if (d / f"{k}_BOQ_LINES.json").exists()}
    run = json.loads((d / "V3_0_55_RUN.json").read_text(encoding="utf-8"))
    led = json.loads((d / "V3_0_55_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    rows = []
    for r in led["rows"]:
        rec = r.get("record") or {}
        rows.append({"action": r["action"], "line_id": r["line_id"], "item_code": r["item_code"], "unit": r["unit"],
                     "floor": r["floor"], "element_id": r["element_id"], "parent_line_id": r.get("parent_line_id"),
                     "before": r["before_base"], "after": r["after_v3_0_55"], "v2_9": r["before_released_v2_9"],
                     "removed": rec.get("removed"), "kept": rec.get("kept"), "terms": rec.get("removed_terms"),
                     "added_held": [{k: h.get(k) for k in ("wall", "kind", "item", "terms", "upper", "length", "range")}
                                    for h in rec.get("added_held") or ()],
                     "drop_upper": rec.get("drop_upper"),
                     "retired_increments": [h.get("wall") for h in rec.get("retired_increments") or ()],
                     "parapet": {k: rec.get(k) for k in ("run", "before_m2", "after_m2")} if rec.get("run") else None})
    out = {"task": "T-488", "method": run["method"], "extends": run["extends"],
           "drawings": {"plan": "training-villa Drive folder / P7757_DXF_COMPRESSED.zip -> P7757.dxf sha256 ab54dd55",
                        "structural": "training-villa Drive folder / ST7757 dxf.dxf sha256 9f9d1179"},
           "chain": chain,
           "identity": {k: ident[k] for k in ("base_lines", "v3_0_55_lines", "replaced", "added", "outside_rows",
                                              "outside_rows_identical_to_base", "outside_rows_sha256", "wiring",
                                              "diff")},
           "totals_moved_by_code": run["totals_moved_by_code"], "rows": rows}
    (HERE / "summary_t488.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                           encoding="utf-8")
    print(json.dumps({"chain": chain, "replaced": ident["replaced"], "moved": sorted(run["totals_moved_by_code"])}))


if __name__ == "__main__":
    main(sys.argv[1])
