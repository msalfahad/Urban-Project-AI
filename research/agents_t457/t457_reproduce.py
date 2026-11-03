"""T-457 step 1 (owner directive 2026-11-02 C2, re-scoped by the owner's site practice): does the engine charge a
SECOND mortar fixing bed on a wet wall (a 2 cm 1:4 bed AND adhesive as two fixing layers, or the same layer twice)?

  1. hand case through FINISH_MATERIALS_TABLE_V1 / V2 / V3: the cement layers and fixing materials one wet wall gets;
  2. candidate path (ARCH_TAKEOFF_V3.0.44 + tools/urban_boq_m9.py, static import closure): is the materials table
     reachable, and which item codes can sit on a wet-wall face (every item-code literal of the closure);
  3. the one-plaster-line-per-room refusal of the wet backing (arch_v3022.py) that keeps one coat per face.

Synthetic only: no drawing, no client data. Run from the tree root:
    python3 -I research/agents_t457/t457_reproduce.py [--out research/agents_t457/out/T457_REPRODUCTION.json]
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t456"))

import t456_reproduce as T456                                   # noqa: E402  (closure helpers, unchanged)
from engine.source import finish_materials_table as V1          # noqa: E402
from engine.source import finish_materials_table_v2 as V2       # noqa: E402
from engine.source import finish_materials_table_v3 as V3       # noqa: E402

CANDIDATE_ENTRIES = ["engine/source/arch_v3044.py", "tools/urban_boq_m9.py"]
TABLES = ["engine/source/finish_materials_table.py", "engine/source/finish_materials_table_v2.py",
          "engine/source/finish_materials_table_v3.py"]
CODE = re.compile(r"^(FIN|WP|MAS|ARCH)\.[A-Z0-9_.]+$")
WALL_LAYER = re.compile(r"BED|MORTAR|ADHESIVE|RENDER|SPATTER|PLASTER|WALL")

# hand fixture (not any project): a 2.40 x 1.80 m bathroom, one 0.80 m door, tile to 2.70 m, one 0.60 x 0.60 window
#   run = 2 x (2.40 + 1.80) - 0.80 = 7.60 m; gross = 7.60 x 2.70 = 20.52 m2; net = 20.52 - 0.36 = 20.16 m2
#   V1 / V2 layer 20.16 x 0.02 x 1.05 = 0.42336 m3 -> x 8 = 3.38688 bags, x 1.1 = 0.465696 m3 sand
#   adhesive 20.16 / 5 = 4.032 bags
HAND = {"id": "WW-1", "floor": "GF", "kind": V1.WET_WALL, "wall_length": 8.40, "door_widths": [0.80], "height": 2.70,
        "openings": [{"id": "W-1", "width": 0.60, "height": 0.60}]}


def _layers(r):
    """cement-based layers and fixing materials one wet-wall row charges on its m2."""
    cem = []
    if r.get("mortar_m3_low") is not None:
        cem.append({"layer": "tile bed (V1 label 'bed', mix " + str(r.get("mix")) + ")", "thickness_m": r["bed_low_m"],
                    "mortar_m3": r["mortar_m3_low"], "cement_bags": r["cement_bags_low"], "sand_m3": r["sand_m3_low"],
                    "status": r["mortar_status"]})
    for o in r.get("operations") or ():
        if o["op"] != "ADHESIVE_AND_PORCELAIN":
            cem.append({"layer": o["op"], "thickness_m": o["thickness_m"], "mortar_m3": o["mortar_m3"],
                        "status": o["mortar_status"], "reason": o["mortar_reason"]})
    fixing = ["ADHESIVE"] if r.get("adhesive_bags") is not None else []
    if r.get("fixing_material") is None and r.get("mortar_m3_low") is not None:
        fixing.append("MORTAR_BED (by its V1 label)")
    return {"area_m2": r["area_m2"], "cement_layers": cem, "fixing_materials": fixing,
            "adhesive_bags": r["adhesive_bags"]}


def hand_case():
    out = {}
    for name, mod in (("V1", V1), ("V2", V2), ("V3", V3)):
        out[name] = _layers(mod.row(dict(HAND)))
    floor = {"id": "DF-1", "floor": "GF", "kind": V1.DRY_FLOOR, "area_m2": 20.0}
    t2, t3 = V2.table([dict(HAND), dict(floor)]), V3.table([dict(HAND), dict(floor)])
    out["project_totals"] = {
        "V2": {k: t2["project"][k] for k in ("mortar_m3_low", "mortar_m3_high", "cement_bags_low", "cement_bags_high")},
        "V3": {k: t3["project"][k] for k in ("mortar_m3_low", "mortar_m3_high", "cement_bags_low", "cement_bags_high")},
        "note": "V2 adds the wet-wall layer (0.42336 m3) to the floor-bed total (0.63 .. 0.84 m3); V3 keeps floor beds only"}
    return out


def _codes(path):
    try:
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    return {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and CODE.match(n.value)}


def candidate_path():
    cl = T456.closure(CANDIDATE_ENTRIES)
    codes = {}
    for p in sorted(cl):
        for c in _codes(p):
            codes.setdefault(c, []).append(p)
    wall = {c: sorted(v)[:3] for c, v in sorted(codes.items()) if WALL_LAYER.search(c)}
    a3022 = (ROOT / "engine/source/arch_v3022.py").read_text(encoding="utf-8")
    return {
        "entries": CANDIDATE_ENTRIES,
        "closure_modules": len(cl),
        "tables_in_closure": {t: t in cl for t in TABLES},
        "item_codes_in_closure": len(codes),
        "wall_layer_codes": wall,
        "bed_codes": sorted(c for c in codes if "BED" in c),
        "adhesive_codes": sorted(c for c in codes if "ADHESIVE" in c),
        "render_or_spatter_codes": sorted(c for c in codes if "RENDER" in c or "SPATTER" in c),
        "one_plaster_line_per_room_refusal": "room in two records (one plaster line per room)" in a3022,
        "one_backing_per_tile_line_refusal": "tile line bound twice (one backing line per tile line)" in a3022,
        "runtime_loaders": T456.dynamic_refs(cl),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    res = {"task": "T-457", "question": "second mortar fixing bed on a wet wall (C2)", "hand": HAND,
           "cases": hand_case(), "candidate": candidate_path()}
    txt = json.dumps(res, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
