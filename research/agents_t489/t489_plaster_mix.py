"""T-489: the MIX stage of the B2 plaster material ledger beside the candidate (ARCH_TAKEOFF_V3.0.45), NOT in it.

Reader tool (stdlib + engine.source.plaster_materials_table_v2). It measures nothing: it takes the merged T-454 ledger
(candidate line -> class -> area -> layer -> thickness -> mortar m3, PLASTER_MATERIALS_TABLE_V1, rebuilt from the same
sha256-pinned inputs) and adds, per coat, the cement : sand ratio with its source, the Q-53 C conversion, cement bags /
sand m3, the WORKFLOW_CONTROLS s.5 status and the 1:3 / 1:4 / 1:5 sensitivity (NOT A QUANTITY).
No candidate module, no released (V2.9 + route G) line and no BOQ_FAMILY_MASTER family changes here.

    python3 -I research/agents_t489/t489_plaster_mix.py [OUT_DIR]     # writes the mix ledger (default: ./out)
"""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import plaster_materials_table_v2 as V2  # noqa: E402

SCHEMA = "URBAN_T489_PLASTER_MIX_V1"
_spec = importlib.util.spec_from_file_location("t454_reader", ROOT / "research/agents_t454/t454_plaster_materials.py")
T454 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T454)


def build(mix=None, line_index=None, binding=None):
    led = T454.build(line_index, binding)
    t = V2.apply(led["table"], mix=mix)
    return {"schema": SCHEMA, "candidate": led["candidate"], "method": V2.METHOD_ID, "reads": led["schema"],
            "inputs": led["inputs"], "census": led["census"], "table": t}


CSV_COLS = ("line_id", "element_id", "class", "layer", "area_m2", "area_label", "thickness_m", "thickness_kind",
            "status", "mortar_m3", "mortar_m3_at_least", "mix_ratio", "mix_label", "cement_bags", "sand_m3",
            "cement_bags_at_least", "sand_m3_at_least", "materials_status", "s5_status", "sens_1_3_bags",
            "sens_1_4_bags", "sens_1_5_bags", "materials_reason")


def to_csv(led):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_COLS)
    for r in led["table"]["rows"]:
        for x in r["layers"]:
            s = x.get("sensitivity_not_a_quantity") or {}
            v = {"line_id": r["id"], "element_id": r.get("element_id"), "class": r["class"] or "CLASS_NOT_ESTABLISHED",
                 **x, "mix_ratio": (x.get("mix") or {}).get("ratio"),
                 **{f"sens_1_{n}_bags": (s.get(f"1:{n}") or {}).get("cement_bags") for n in (3, 4, 5)}}
            w.writerow(["" if v.get(c) is None else v.get(c) for c in CSV_COLS])
    return buf.getvalue()


def write(led, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "PLASTER_MIX_T489.json").write_text(json.dumps(led, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
                                               encoding="utf-8")
    (out / "PLASTER_MIX_T489.csv").write_text(to_csv(led), encoding="utf-8")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    led = build()
    write(led, argv[0] if argv else HERE / "out")
    print(json.dumps({"census": led["census"], "sums": led["table"]["sums"]}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
