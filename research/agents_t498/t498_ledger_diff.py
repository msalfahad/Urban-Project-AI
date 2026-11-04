"""T-498 (read-only): the blockwork material figures per MAS.BLOCK line, T-453 r2 on V3.0.45 (out/BLOCK_MATERIALS_T453.csv,
merged; MATERIAL_LEDGER_T453.json) vs the same machinery on V3.0.55 = V3.0.56 masonry lines (t498_inputs.ledger), with the cause per change.

    python3 -I research/agents_t498/t498_ledger_diff.py [OUT.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t498_inputs as L  # noqa: E402

OLD = ROOT / "research/agents_t453/out/MATERIAL_LEDGER_T453.json"


def fig(m):
    for k in ("theoretical_count", "consumption_kg", "mortar_installed_m3"):
        if m.get(k) not in (None, ""):
            return float(m[k])
    for k in ("theoretical_count_range", "consumption_kg_range", "mortar_installed_m3_range"):
        v = m.get(k)
        if v not in (None, ""):
            return json.loads(v) if isinstance(v, str) else v
    return "HELD"


def main(argv):
    old = {(r["line_id"], r["item"]): r
           for r in json.loads(OLD.read_text(encoding="utf-8"))["block_materials"]}
    led, notes = L.ledger()
    rows = []
    for m in led["block_materials"]:
        k = (m["line_id"], m["item"])
        o = old.get(k)
        before = "NOT IN T-453 r2" if o is None else fig(o)
        after = fig(m)
        if before != after:
            rows.append({"line_id": m["line_id"], "element_id": m["element_id"], "item": m["item"],
                         "material": m.get("material"), "material_type": m.get("material_type"),
                         "t453_r2_v3_0_45": before, "v3_0_56": after,
                         "net_before": None if o is None else o.get("net_m2"),
                         "net_now": m.get("net_m2"), "status_now": m["status"]})
    out = {"changed_rows": rows, "unchanged_rows": len(led["block_materials"]) - len(rows),
           "totals_now": {"black_0_20": led["block_totals"]["black_0_20_by_label"],
                          "glue": led["glue_groups"]["known_part_by_label"], "mortar": led["mortar"]},
           "held_walls_carried_held": notes["held_walls_carried_held"]}
    text = json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    if len(argv) > 1:
        Path(argv[1]).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main(sys.argv)
