"""The visual zone register, transcribed from a frozen pass, and drawn.

    python -m tools.a18_zone_register --run-dir <dir> --parent <page image>

Three things are kept apart here, and the register refuses to collapse
them:

    PHYSICAL_SPACE            what walls and openings define it
    FUNCTIONAL_ZONE           what the region is for
    FLOOR_FINISH_TRADE_ZONE   how far one finish actually runs

and so are three relations between zones:

    SAME_TRADE_CATEGORY       the same trade does the work
    SAME_FINISH               the same material and specification
    SAME_MEASUREMENT_ZONE     one zone, measured as one quantity

TWO ROOMS USING CERAMIC ARE NOT THEREBY ONE MEASUREMENT ZONE. A bathroom,
a kitchen, a washing room or a pantry may carry its own room-level
quantity while sharing a trade category with half the floor, so a
relation that a pass did not asserted is recorded as NOT_STATED rather
than inferred from the material.

The overlay draws the register's own boxes on the sheet. It adds no
geometry: a box that a pass did not state is not drawn.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

from engine import export_provenance as prov

NOT_STATED = "NOT_STATED_BY_THE_PASS"
RELATIONS = ("SAME_TRADE_CATEGORY", "SAME_FINISH", "SAME_MEASUREMENT_ZONE")


def register(zones, functional, trade, source) -> dict:
    doc = {
        "MODEL": "A_VISUAL_ZONE_REGISTER_KEEPS_THREE_THINGS_APART_V1",
        "run_id": source.get("run_id", ""),
        "transcribed_from": source,
        "three_readings_are_separate": {
            "PHYSICAL_SPACE": "what physical walls and openings define it",
            "FUNCTIONAL_ZONE": "what the region is for",
            "FLOOR_FINISH_TRADE_ZONE": "how far one finish actually runs",
            "rule": "these three are not forced to agree"},
        "three_relations_are_separate": {
            "SAME_TRADE_CATEGORY": "the same trade does the work in both",
            "SAME_FINISH": "the same material and specification",
            "SAME_MEASUREMENT_ZONE": "one zone, measured as one quantity",
            "rule": ("two rooms using ceramic are NOT thereby one "
                     "measurement zone. A relation the pass did not assert "
                     "is NOT_STATED, never inferred from the material")},
        "physical_spaces": zones,
        "functional_zones": functional,
        "floor_finish_trade_zones": trade,
        "counts": {"physical_spaces": len(zones),
                   "functional_zones": len(functional),
                   "trade_zones": len(trade)},
    }
    doc["VISUAL_ZONE_REGISTER_HASH"] = prov.canonical_sha256(doc)
    return doc


def overlay(parent, doc, out_path, *, width=6) -> dict:
    img = Image.open(parent).convert("RGB")
    draw = ImageDraw.Draw(img)
    drawn = 0
    for zone in doc["physical_spaces"]:
        box = zone.get("box_as_stated")
        if not box:
            continue
        draw.rectangle(box, outline=(220, 30, 30), width=width)
        drawn += 1
    for zone in doc["physical_spaces"]:
        point = zone.get("label_point")
        if not point:
            continue
        x, y = point
        r = 26
        draw.ellipse([x - r, y - r, x + r, y + r], outline=(20, 90, 220),
                     width=width)
    img.save(out_path)
    return {"file": Path(out_path).name,
            "boxes_drawn": drawn,
            "label_points_drawn": sum(
                1 for z in doc["physical_spaces"] if z.get("label_point")),
            "legend": {"red rectangle": "an extent the pass stated",
                       "blue circle": "a label position the pass stated"},
            "nothing_added": ("a space for which the pass stated no extent "
                              "is not drawn. The overlay carries no "
                              "geometry the register does not hold"),
            prov.RAW: prov.raw_sha256(out_path)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--parent", required=True)
    ap.add_argument("--zones", required=True,
                    help="the transcription of the frozen pass, as JSON")
    a = ap.parse_args(argv)
    run_dir = Path(a.run_dir)
    src = json.loads(Path(a.zones).read_text(encoding="utf-8"))
    doc = register(src["physical_spaces"], src["functional_zones"],
                   src["floor_finish_trade_zones"], src["transcribed_from"])
    out = run_dir / "A18_VISUAL_ZONE_REGISTER.json"
    png = run_dir / "A18_GROUND_FLOOR_INTERPRETATION_OVERLAY.png"
    doc["overlay"] = overlay(a.parent, doc, png)
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(json.dumps({"register": str(out), "overlay": str(png),
                      "counts": doc["counts"],
                      "boxes_drawn": doc["overlay"]["boxes_drawn"],
                      "VISUAL_ZONE_REGISTER_HASH":
                          doc["VISUAL_ZONE_REGISTER_HASH"][:16]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
