"""T-040 read-only diagnostic: door symbol blocks and elevation dimensions of a plan DXF against one engine run.

Not imported by any engine, tool or method file; reproduces the counts of T-040_DOORS_WINDOWS.md. Writes nothing.

    python3 -I research/agents_t040/opening_census.py DRAWING.dxf RUN_DIR

RUN_DIR is the output folder of `tools/urban_boq_m9.py arch` (ARCH_PLAN.json, DOOR_SCHEDULE.json). Prints:
1. per plan region: every block insert whose block holds a swing ARC (a door symbol), its leaf radius x |scale|, and
   the nearest engine door element (DOOR_SCHEDULE.json) of the same floor, then the engine elements no block is
   nearest to;
2. per non-plan frame (elevations, sections): every DIMENSION with its measured value, angle and end points, so
   printed opening heights can be read against the elevation drawing;
3. the text count per plan region (door / window marks would appear here).
General: no layer, block or project name is coded; units are the drawing's own.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

import ezdxf


def _in(b, x, y):
    return b[0] <= x <= b[2] and b[1] <= y <= b[3]


def main(dxf, run):
    run = Path(run)
    plan = json.loads((run / "ARCH_PLAN.json").read_text(encoding="utf-8"))
    regs = [(r["floor"], r["box"]) for r in plan["regions"]]
    others = [(o["sheet_id"], o["box"]) for o in plan.get("other_frames") or ()]
    els = json.loads((run / "DOOR_SCHEDULE.json").read_text(encoding="utf-8"))["doors"]["elements"]
    doc = ezdxf.readfile(dxf)
    msp = doc.modelspace()

    def floor_of(x, y):
        return next((f for f, b in regs if _in(b, x, y)), None)

    swing_r = {}
    for blk in doc.blocks:
        r = [e.dxf.radius for e in blk if e.dxftype() == "ARC"]
        lines = sum(1 for e in blk if e.dxftype() == "LINE")
        texts = sum(1 for e in blk if e.dxftype() in ("TEXT", "MTEXT"))
        if r and lines and not texts and len(r) <= 2:
            swing_r[blk.name] = r
    print("== door symbol blocks (block with 1-2 swing arcs, lines, no text)")
    used = set()
    for e in msp.query("INSERT"):
        if e.dxf.name not in swing_r:
            continue
        x, y = e.dxf.insert.x, e.dxf.insert.y
        fl = floor_of(x, y)
        if fl is None:
            continue
        best = min(((math.hypot(el["centre"][0] - x, el["centre"][1] - y), el) for el in els
                    if el["floor"] == fl and el.get("centre")), key=lambda t: t[0], default=None)
        leaf = [round(r * abs(e.dxf.xscale), 1) for r in swing_r[e.dxf.name]]
        el = best[1] if best else None
        if el:
            used.add(el["element_id"])
        print(fl, e.dxf.handle, "leaf", leaf, "->", el and el["element_id"], el and el["section"],
              el and el["boq_class"], el and el["structural_opening_width_m"], "dist", best and round(best[0], 1))
    print("engine door elements no block is nearest to:",
          [(el["floor"], el["element_id"], el["section"], el["structural_opening_width_m"]) for el in els
           if el["element_id"] not in used])
    print("== dimensions in non-plan frames")
    for d in msp.query("DIMENSION"):
        p1, p2 = d.dxf.get("defpoint2"), d.dxf.get("defpoint3")
        if p1 is None:
            continue
        sh = next((k for k, b in others if _in(b, p1.x, p1.y)), None)
        if sh is None:
            continue
        m = d.get_measurement()
        print(sh, "angle", round(d.dxf.get("angle", 0)), "value", round(m, 1) if isinstance(m, float) else m,
              "p1", (round(p1.x), round(p1.y)), "p2", (round(p2.x), round(p2.y)))
    print("== texts per plan region (TEXT / MTEXT at top level)")
    print(dict(Counter(floor_of(t.dxf.insert.x, t.dxf.insert.y) for t in msp.query("TEXT MTEXT"))))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
