"""T-299: read-only route G reinforcement extract (values and drawing handles only, no coordinates, no client data).

    .work/venv/bin/python -I research/agents_t299/t299_route_g_extract.py <structural DXF> research/agents_t299/ROUTE_G_ITEMS_T299.csv

compute(route='G', URBAN_M8_GENERIC_CONVENTIONS_V6, no profile), as owner 2026-10-25 10:33 (2) names it. Writes one row
per reinforcement item (unit kg) and one row per COLUMNS / GROUND_BEAMS concrete component (to show which members route
G carries with no steel at all). Nothing in engine/ or tools/ is changed; the result object is only read.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FIELDS = ["item_id", "component_id", "family", "storey", "unit", "category", "low", "base", "high", "dia_mm", "support",
          "blocker", "formula", "source", "assumptions"]


def main(dxf: str, out: str) -> None:
    from tools import urban_boq_m2 as M2
    R = M2.compute([dxf], conventions=str(ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"), route="G")
    rows = []
    for it in R["items"]:
        keep = it.get("unit") == "kg" or (it.get("unit") == "m3" and it.get("family") in ("COLUMNS", "GROUND_BEAMS"))
        if not keep:
            continue
        src = str(it.get("source") or "").replace(Path(dxf).name, "<structural DXF>")
        rows.append({
            "item_id": it["item_id"], "component_id": it.get("component_id"), "family": it.get("family"),
            "storey": it.get("storey"), "unit": it.get("unit"), "category": it.get("category"),
            "low": "" if it.get("low") is None else repr(float(it["low"])),
            "base": "" if it.get("base") is None else repr(float(it["base"])),
            "high": "" if it.get("high") is None else repr(float(it["high"])),
            "dia_mm": it.get("dia_mm") or "", "support": it.get("support"), "blocker": it.get("blocker"),
            "formula": it.get("formula") or "", "source": src, "assumptions": ";".join(it.get("assumptions") or []),
        })
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    steel = R["summary"]["steel_t"]
    sha = hashlib.sha256(Path(dxf).read_bytes()).hexdigest()[:8]
    kg = sum(float(r["base"] or 0) for r in rows if r["unit"] == "kg")
    meta = {"dxf_sha256_8": sha, "rows": len(rows), "kg_items": sum(1 for r in rows if r["unit"] == "kg"),
            "summary_steel_t": {k: repr(float(v)) for k, v in steel.items()},
            "rebar_completeness": R["summary"].get("rebar_completeness")}
    Path(out).with_name("ROUTE_G_SUMMARY_T299.json").write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n",
                                                                encoding="utf-8")
    print(f"dxf sha {sha}; {len(rows)} rows; kg items base {kg:.6f} kg; summary PLANNING_BASE {steel['PLANNING_BASE']:.9f} t")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
