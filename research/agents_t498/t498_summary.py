"""T-498: write research/agents_t498/summary_t498.json from a finished v3057_run.py run (its hub out folder, outside the
repository). Only engine ids, item codes, units, states and quantities are copied (no names, no coordinates).

    python3 -I research/agents_t498/t498_summary.py <run out>/v3050
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEYS = ("V3_0_47", "V3_0_48", "V3_0_50", "V3_0_51", "V3_0_53", "V3_0_54", "V3_0_55", "V3_0_56", "V3_0_57")


def main(d):
    d = Path(d)
    chain = {k: hashlib.sha256((d / f"{k}_BOQ_LINES.json").read_bytes()).hexdigest()[:8]
             for k in KEYS if (d / f"{k}_BOQ_LINES.json").exists()}
    run = json.loads((d / "V3_0_57_RUN.json").read_text(encoding="utf-8"))
    led = json.loads((d / "V3_0_57_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    rows = []
    for r in led["rows"]:
        rec = r.get("record") or {}
        b = rec.get("base") or {}
        rows.append({"line_id": r["line_id"], "item_code": r["item_code"], "family": r["family"], "unit": r["unit"],
                     "floor": r["floor"], "element_id": r["element_id"], "source_line_id": r["source_line_id"],
                     "after": r["after_v3_0_57"], "evidence_status": r["evidence_status"],
                     "contract_net_m2": b.get("contract_net_m2"), "lintel_deduction_m2": b.get("lintel_deduction_m2"),
                     "material_base_m2": b.get("material_base_m2"), "base_state": b.get("base_state"),
                     "range_m2": b.get("range_m2"),
                     "lintels": [{k: x.get(k) for k in ("opening_id", "kind", "lintel_line_id", "face_m2", "face_max_m2")}
                                 for x in b.get("lintels") or ()],
                     "beside": rec.get("figure_beside") or rec.get("beside_materials"), "why": rec.get("why")})
    out = {"task": "T-498", "method": run["method"], "extends": run["extends"],
           "drawings": {"plan": "training-villa Drive folder / P7757_DXF_COMPRESSED.zip -> P7757.dxf sha256 ab54dd55",
                        "structural": "training-villa Drive folder / ST7757 dxf.dxf sha256 9f9d1179"},
           "chain": chain,
           "identity": {k: ident[k] for k in ("base_lines", "v3_0_57_lines", "replaced", "added", "outside_rows",
                                              "outside_rows_identical_to_base", "outside_rows_sha256", "materials",
                                              "diff")},
           "summary": led["summary"], "totals_moved_by_code": run["totals_moved_by_code"], "rows": rows}
    (HERE / "summary_t498.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                           encoding="utf-8")
    print(json.dumps({"chain": chain, "added": ident["added"], "moved": run["totals_moved_by_code"],
                      "log": led["summary"]}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
