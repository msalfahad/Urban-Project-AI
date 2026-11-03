"""T-455: the B3 TILE PURCHASE LEDGER (adhesive bags, tile boxes) beside the candidate ARCH_TAKEOFF_V3.0.45, NOT in it.

Reader tool (stdlib + engine.source.finish_materials_table_v4). It measures nothing: each row traces
    candidate tiled line id -> item code -> line m2 (measured_net, unchanged) -> tile size (sourced or HELD) ->
    UPC-ADHESIVE-001 bags (fractional) -> purchasing group -> tile product -> layout count -> boxes.
No candidate module, no released (V2.9 + route G) line and no BOQ_FAMILY_MASTER family changes here.

Input (committed, sha256-pinned; no drawing content):
  research/agents_t479/out/LINE_INDEX_V3_0_45.json   candidate V3.0.45 line index (the pin T-454 uses)

Rules of this ledger (project-independent):
  R-T455-1 SCOPE   tiled porcelain / ceramic lines: FIN.FLOOR.PORCELAIN (dry floor), FIN.FLOOR.WET_TILE (wet floor),
           FIN.WALL.TILE (wet wall), EXT.FLOOR.PORCELAIN (outdoor floor), FIN.FLOOR.FINISH_HELD (floor whose finish
           is not established: finish None). EXCLUDED lines carry no material (listed). Stone (FIN.MARBLE.*) is out of
           this ledger: Q-45 stone adhesive coverage not given, no packaging rule.
  R-T455-2 AREA    the line's measured_net; a HELD line is HELD (never 0). Evidence VERIFIED only for a line bound
           VERIFIED_WHOLE by a Checker verdict, else UNKNOWN (the rate never upgrades the area).
  R-T455-3 SIZE    a tile size only from a printed note, a project document or an owner project decision, with its
           source (TILE_SIZE map below, empty for this villa: the architectural DXF census read 276 texts and found 0
           tile size notes (research/agents_t087/alsenan_tile_summary.json, T-087), and the ground-floor PDF sheet has
           no text layer and shows room names, dimensions and levels only (T-455 visual read)). A drafted hatch grid is
           a pattern, never a size (never scaled from a drawing).
  R-T455-4 GROUP   one adhesive purchasing group 'PROJECT' (one adhesive product named for the villa, UPC-ADHESIVE-001);
           tile products are not named on any drawing: boxes HELD (product_not_named).

    python3 -I research/agents_t455/t455_tile_purchase.py [OUT_DIR]     # writes the ledger (default: ./out)
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import finish_materials_table_v4 as V4  # noqa: E402

SCHEMA = "URBAN_T455_TILE_PURCHASE_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.45"
LINE_INDEX = ROOT / "research/agents_t479/out/LINE_INDEX_V3_0_45.json"
PIN = "16920d3c682399541f8fa84d31f39bca171e3d4e7f362bcb1eb0b05b3f4269f4"
SCOPE = {"FIN.FLOOR.PORCELAIN": (V4.DRY_FLOOR, V4.PORCELAIN_CERAMIC),
         "FIN.FLOOR.WET_TILE": (V4.WET_FLOOR, V4.PORCELAIN_CERAMIC),
         "FIN.WALL.TILE": (V4.WET_WALL, V4.PORCELAIN_CERAMIC),
         "EXT.FLOOR.PORCELAIN": (V4.DRY_FLOOR, V4.PORCELAIN_CERAMIC),
         "FIN.FLOOR.FINISH_HELD": (V4.DRY_FLOOR, None)}
TILE_SIZE = {}          # line_id -> {"tile_cm": "60x60", "source": "..."}; none printed for this villa (R-T455-3)


class LedgerError(ValueError):
    pass


def _load(path=None):
    p = Path(path) if path else LINE_INDEX
    raw = p.read_bytes()
    if path is None and hashlib.sha256(raw).hexdigest() != PIN:
        raise LedgerError(f"{p.relative_to(ROOT)}: sha256 is not the pinned {PIN[:8]}")
    return json.loads(raw.decode("utf-8"))


def _floor(element_id):
    for tok in element_id.replace(":", "-").replace("#", "-").split("-"):
        if tok in ("GF", "1F", "2F", "RF"):
            return tok
    return None


def build(line_index=None):
    d = _load(line_index)
    lines, excluded = [], []
    for ln in d["lines"]:
        if ln["item_code"] not in SCOPE:
            continue
        if ln["class"] == "EXCLUDED":
            excluded.append(ln["line_id"])
            continue
        if ln["unit"] != "m2":
            raise LedgerError(f"{ln['line_id']}: unit {ln['unit']!r} is not m2")
        kind, finish = SCOPE[ln["item_code"]]
        held = ln["class"] == "HELD" or ln["measured_net"] is None
        b = ln.get("binding") or {}
        sz = TILE_SIZE.get(ln["line_id"]) or {}
        lines.append({"id": ln["line_id"], "item_code": ln["item_code"], "floor": _floor(ln["element_id"]),
                      "kind": kind, "finish": finish, "area_m2": None if held else float(ln["measured_net"]),
                      "area_reason": (f"candidate line HELD (range {ln.get('held_low')} .. {ln.get('held_high')})"
                                      if held else None),
                      "tile_cm": sz.get("tile_cm"), "tile_size_source": sz.get("source"),
                      "evidence_status": "VERIFIED" if b.get("binding") == "VERIFIED_WHOLE" else "UNKNOWN"})
    res = V4.purchase_from_lines([{k: v for k, v in x.items() if k != "item_code"} for x in lines])
    code = {x["id"]: x["item_code"] for x in lines}
    by_code = {}
    for r in res["rows"]:
        c = by_code.setdefault(code[r["id"]], {"lines": 0, "released": 0, "held": 0, "area_m2": 0.0,
                                               "v3_flat_bags": 0.0, "v4_bags_known": 0.0, "v4_bags_held_lines": 0,
                                               "bound_low": 0.0, "bound_high": 0.0})
        c["lines"] += 1
        if r["area_m2"] is None:
            c["held"] += 1
        else:
            c["released"] += 1
            c["area_m2"] += r["area_m2"]
        c["v3_flat_bags"] += r["adhesive_v3_flat_bags"] or 0.0
        if r["adhesive_bags"] is None:
            c["v4_bags_held_lines"] += 1
        else:
            c["v4_bags_known"] += r["adhesive_bags"]
        if r.get("adhesive_bound_bags"):
            c["bound_low"] += r["adhesive_bound_bags"]["low"]
            c["bound_high"] += r["adhesive_bound_bags"]["high"]
    for c in by_code.values():
        for k in ("area_m2", "v3_flat_bags", "v4_bags_known", "bound_low", "bound_high"):
            c[k] = round(c[k], 6)
    return {"schema": SCHEMA, "candidate": CANDIDATE, "method": V4.METHOD_ID, "input_sha256": PIN,
            "excluded_lines": excluded, "by_item_code": by_code, "purchase": {"adhesive": res["adhesive"],
                                                                            "tiles": res["tiles"]},
            "rows": res["rows"]}


def write(out_dir=None):
    out = Path(out_dir) if out_dir else HERE / "out"
    out.mkdir(parents=True, exist_ok=True)
    led = build()
    (out / "TILE_PURCHASE_T455.json").write_text(json.dumps(led, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
                                                 encoding="utf-8")
    buf = io.StringIO()
    cols = ("id", "kind", "finish", "area_m2", "evidence_status", "adhesive_v3_flat_bags", "adhesive_bags",
            "adhesive_status", "adhesive_reason", "bound_low", "bound_high", "tile_product", "tiles_reason")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(cols)
    for r in led["rows"]:
        b = r.get("adhesive_bound_bags") or {}
        w.writerow([r.get(c) if c not in ("bound_low", "bound_high") else b.get(c.split("_")[1]) for c in cols])
    (out / "TILE_PURCHASE_T455.csv").write_text(buf.getvalue(), encoding="utf-8")
    return led


if __name__ == "__main__":
    led = write(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({"by_item_code": led["by_item_code"], "adhesive": led["purchase"]["adhesive"],
                      "tiles_not_named": len(led["purchase"]["tiles"]["product_not_named"])}, indent=1))
