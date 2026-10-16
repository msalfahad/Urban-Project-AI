"""PROOF DRAWINGS - Phase 2B-3: synthetic DXF plans that put proof cases through the whole architectural route
(DXF -> rooms -> openings -> lines -> waterproofing / doors -> outputs), drawn with tools/arch_synth's plan writer
(synthetic geometry only). Every room's expected values are those of its proof case: the drawing adds the route, not
new arithmetic.

    bathrooms(path)   PD-1: two 4.00 x 3.00 m bathrooms (WP-B geometry: each with one 1.00 m door) side by side, a
                      dry corridor along their north walls; the scope test of a ROOM project rule (RS-02)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import arch_synth as AS                            # noqa: E402

PD1_ROOMS = {"BATH1": [(200, 200), (4200, 200), (4200, 3200), (200, 3200)],
             "BATH2": [(4400, 200), (8400, 200), (8400, 3200), (4400, 3200)],
             "CORRIDOR": [(200, 3400), (8400, 3400), (8400, 4800), (200, 4800)]}
PD1_OUTER = [(0, 0), (8600, 0), (8600, 5000), (0, 5000)]
PD1_LABELS = {"BATH1": (2200, 1600), "BATH2": (6400, 1600), "CORRIDOR": (4300, 4100)}
PD1_WORDS = {"BATH1": "BATH", "BATH2": "BATH", "CORRIDOR": "CORRIDOR"}
# doors: north wall of each bath (y 3200..3400), 1.00 m, hinge on the corridor face, swinging into the corridor
PD1_OPENINGS = [("DOOR", "y", 3200, 3400, 1700, 2700, (2700, 3400, 90, 1, 1)),
                ("DOOR", "y", 3200, 3400, 5900, 6900, (6900, 3400, 90, 1, 1))]
BATH1_POINT_M = (2.2, 1.6)                     # a point inside BATH1 (metres) for a ROOM-scoped project rule


def bathrooms(path):
    import ezdxf
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    blk = doc.blocks.new("DOOR1000")
    blk.add_line((0, 0), (1000, 0), dxfattribs={"layer": "0"})
    blk.add_arc((0, 0), 1000, 0, 90, dxfattribs={"layer": "0"})
    msp = doc.modelspace()
    (x0, y0), (x1, y1), org, title = AS.FRAMES["GF"]
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": "A-FRAME"})
    msp.add_text(title, dxfattribs={"layer": "A-TITLE", "height": 500}).set_placement((x0 + 2000, y0 + 1500))
    AS._plan(msp, rooms=PD1_ROOMS, outer=PD1_OUTER, labels=PD1_LABELS, words=PD1_WORDS, openings=PD1_OPENINGS,
             columns=(), level="+0.00", treads=(), origin=org, dx=0.0, dy=0.0, mirror=False, quarter_turns=0)
    doc.saveas(str(path))
    return str(path)
