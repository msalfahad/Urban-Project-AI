"""The whole-floor challenge overlay: candidate geometry, and what was challenged.

    python -m tools.a18_pass_d_overlay --run-dir <dir> --parent <page image>

Two things are drawn, keyed by the same stable candidate ids that appear
in the register and in the local overlays:

    the FROZEN PASS geometry      every candidate box, as that pass stated
                                  it or as the union of its members
    the CHALLENGE OUTCOME         the colour of that box

What is NOT drawn is the challenging pass's own proposed geometry. It
exists in prose and in 37 local overlays, and turning prose into polygons
here would be the harness inventing boundaries and then presenting them as
a reading. The ids connect the two: a box on this sheet, a local overlay
of the same name, and a row in the register.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

from engine import export_provenance as prov

COLOUR = {
    "CONFIRMED": (30, 140, 60),
    "CHALLENGED": (215, 40, 40),
    "UNRESOLVED": (200, 140, 20),
}
KIND_WIDTH = {"PHYSICAL_SPACE": 7, "FUNCTIONAL_ZONE": 4,
              "FLOOR_FINISH_TRADE_ZONE": 4}
DASH = 40


def _dashed(draw, box, colour, width):
    left, top, right, bottom = box
    for x in range(int(left), int(right), DASH * 2):
        draw.line([x, top, min(x + DASH, right), top], colour, width)
        draw.line([x, bottom, min(x + DASH, right), bottom], colour, width)
    for y in range(int(top), int(bottom), DASH * 2):
        draw.line([left, y, left, min(y + DASH, bottom)], colour, width)
        draw.line([right, y, right, min(y + DASH, bottom)], colour, width)


def build(run_dir, parent) -> dict:
    root = Path(run_dir)
    reg = json.loads(
        (root / "A18_PASS_D_FALSE_CONFIDENCE_REGISTER.json").read_text())
    cand = {c["candidate_id"]: c for c in json.loads(
        (root / "A18_PASS_D_CANDIDATES.json").read_text())["candidates"]}
    img = Image.open(parent).convert("RGB")
    draw = ImageDraw.Draw(img)

    drawn = []
    for row in reg["rows"]:
        cid = row["candidate_id"]
        box = cand[cid]["box"]
        colour = COLOUR.get(row["outcome"], (90, 90, 90))
        width = KIND_WIDTH.get(row["hypothesis_kind"], 4)
        if row["hypothesis_kind"] == "PHYSICAL_SPACE":
            draw.rectangle(box, outline=colour, width=width)
        else:
            _dashed(draw, box, colour, width)
        draw.text((box[0] + 12, box[1] + 12), cid, fill=colour)
        drawn.append({"candidate_id": cid, "box": box,
                      "outcome": row["outcome"],
                      "hypothesis_kind": row["hypothesis_kind"],
                      "local_overlay": row["overlay"]})

    out = root / "A18_PASS_D_WHOLE_FLOOR_OVERLAY.png"
    img.save(out)
    rec = {
        "MODEL": "A_WHOLE_FLOOR_CHALLENGE_OVERLAY_V1",
        "file": out.name,
        "pixels": list(img.size),
        "candidates_drawn": len(drawn),
        "legend": {
            "solid rectangle": "a PHYSICAL_SPACE candidate",
            "dashed rectangle": "a FUNCTIONAL_ZONE or FLOOR_FINISH_TRADE_ZONE candidate",
            "green": "the challenge CONFIRMED every question",
            "red": "at least one question was CHALLENGED",
            "amber": "UNRESOLVED and not challenged",
            "text": "the stable candidate id, which is also the name of its "
                    "local overlay and its row in the register",
        },
        "geometry_drawn_is": ("the FROZEN pass's own stated extent, its "
                             "stated label point box, or the union of a "
                             "zone's members - nothing else"),
        "geometry_deliberately_not_drawn": (
            "the challenging pass's proposed boundaries. Those are prose "
            "and 37 local overlays; turning prose into polygons here would "
            "be the harness inventing geometry and presenting it as a "
            "reading"),
        "rows": drawn,
        prov.RAW: prov.raw_sha256(out),
    }
    (root / "A18_PASS_D_WHOLE_FLOOR_OVERLAY.json").write_text(
        json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--parent", required=True)
    a = ap.parse_args(argv)
    rec = build(a.run_dir, a.parent)
    print(json.dumps({"file": rec["file"], "pixels": rec["pixels"],
                      "candidates_drawn": rec["candidates_drawn"],
                      "sha256": rec[prov.RAW][:16]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
