"""Where the sampled neighbourhoods are. One whole-floor picture.

This is a map of the sample, not evidence about anything. It exists so
that a reviewer can see at a glance that the mechanical strata did not
quietly cluster in one corner of the drawing.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.semantic_edge_experiment_01 import protocol as P
from tools import run_e1_2 as r12
from tools import run_e1_3 as r13
from research.semantic_edge_experiment_01.build import Args

OUT = Path("data/experiments/SEMANTIC_EDGE_EXPERIMENT_01")

COLOUR = {
    P.STRATUM_A: (220, 20, 60), P.STRATUM_B: (255, 140, 0),
    P.STRATUM_C: (30, 144, 255), P.STRATUM_D: (34, 139, 34),
    P.STRATUM_E: (148, 0, 211), P.STRATUM_F: (139, 69, 19),
    P.STRATUM_G: (0, 178, 178), P.STRATUM_H: (255, 0, 255),
    P.STRATUM_I: (0, 0, 0), P.STRATUM_J: (128, 128, 128),
}


def main() -> int:
    from PIL import ImageDraw
    a = Args()
    prep = r12.prepare(a.decode)
    gf = r12.ground_floor(prep)
    reg, sheet = r13._registered_sheet(a, gf)
    if sheet is None or not getattr(sheet, "ok", False):
        raise SystemExit("the source sheet did not register")

    groups = json.loads((OUT / "02_FEATURE_GROUP_REGISTER.json")
                        .read_text(encoding="utf-8"))["GROUPS"]
    xs = [v for g in groups for v in (g["LOCAL_TOPOLOGY"]["bounding_box_mm"][0],
                                      g["LOCAL_TOPOLOGY"]["bounding_box_mm"][2])]
    ys = [v for g in groups for v in (g["LOCAL_TOPOLOGY"]["bounding_box_mm"][1],
                                      g["LOCAL_TOPOLOGY"]["bounding_box_mm"][3])]
    centre = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
    half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2.0 + 3000.0
    got = r12._frame(sheet, reg, centre, half, (2400, 2400))
    if got is None:
        raise SystemExit("the whole-floor frame could not be made")
    img, to_px, _box = got
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)
    for g in groups:
        b = g["LOCAL_TOPOLOGY"]["bounding_box_mm"]
        p0, p1 = to_px(b[0], b[1]), to_px(b[2], b[3])
        x0, x1 = sorted((p0[0], p1[0]))
        y0, y1 = sorted((p0[1], p1[1]))
        col = COLOUR.get(g["STRATUM"], (0, 0, 0))
        draw.rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], outline=col, width=3)
        draw.text((x0 + 3, y0 + 3), g["STRATUM"][0], fill=col)

    d = OUT / "overlays"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "WHERE_THE_SAMPLE_IS.png"
    img.save(p)
    legend = {"WHAT_THIS_IS": ("a map of where the mechanically selected "
                              "feature neighbourhoods fall on the floor. "
                              "It is not evidence about any of them"),
              "LETTER_IS_THE_STRATUM": {s[0]: s for s in P.STRATA},
              "groups": len(groups),
              "PNG_SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}
    (d / "WHERE_THE_SAMPLE_IS.json").write_text(
        json.dumps(legend, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(json.dumps(legend, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
