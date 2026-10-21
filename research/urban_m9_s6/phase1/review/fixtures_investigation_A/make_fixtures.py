"""S6 review, Investigation A: minimal synthetic DXF fixtures for the float-boundary drop of a drafted 100 mm wall-face
piece (S6P1-NEW-05). Generic geometry only (no project data).

One wall 200 mm thick, drawn as two face lines, with a 1000 mm opening. Below the opening, one face continues
for 2000 mm; the other is only a drafted 100 mm return piece. That is the case where a column or a cross wall
takes over the face. Above the opening, both faces continue for 2000 mm. Jamb lines close both ends.

The opening exists only if the 100 mm piece survives `face_lines(min_len = 100 mm)`. Without the piece, the
second face starts above the opening, the band's common extent excludes the opening, and no gap is found.

usage: python3 -I make_fixtures.py OUT_DIR
"""
import sys
from pathlib import Path
import ezdxf

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
WALL = "A-WALL"
LOCAL = [  # (x0, y0, x1, y1) in mm, wall along +y, faces at x = 0 and x = 200
    (0, -2000, 0, 0), (200, -100, 200, 0),          # below the opening: long face, and the 100 mm return piece
    (0, 1000, 0, 3000), (200, 1000, 200, 3000),     # above the opening
    (0, 0, 200, 0), (0, 1000, 200, 1000),           # jamb lines
    (200, -100, 1200, -100),                        # the cross wall the short piece returns into
]


def doc_mm():
    d = ezdxf.new("R2010"); d.header["$INSUNITS"] = 4; d.layers.add(WALL); return d


def direct(name, scale=1.0, units=4, dx=0.0, dy=0.0):
    d = ezdxf.new("R2010"); d.header["$INSUNITS"] = units; d.layers.add(WALL)
    m = d.modelspace()
    for x0, y0, x1, y1 in LOCAL:
        m.add_line((dx + x0 * scale, dy + y0 * scale), (dx + x1 * scale, dy + y1 * scale), dxfattribs={"layer": WALL})
    d.saveas(OUT / name)


def inserted(name, at, rot, scale=1.0, units=4):
    d = ezdxf.new("R2010"); d.header["$INSUNITS"] = units; d.layers.add(WALL)
    b = d.blocks.new("WALL_UNIT")
    for x0, y0, x1, y1 in LOCAL:
        b.add_line((x0 * scale, y0 * scale), (x1 * scale, y1 * scale), dxfattribs={"layer": "0"})
    d.modelspace().add_blockref("WALL_UNIT", at, dxfattribs={"layer": WALL, "rotation": rot})
    d.saveas(OUT / name)


direct("A0_control_mm_origin.dxf")                                            # exact: the opening is found
inserted("A1_mm_block_rotated_offset.dxf", (-351234.567, -702468.135), 90.0)  # mm, rotated block at a site offset
direct("A2_m_direct_offset.dxf", scale=0.001, units=6, dy=250.00035)     # metres, typed coordinates
inserted("A3_m_block_rotated_offset.dxf", (-351.234567, -702.468135), 90.0, scale=0.001, units=6)
direct("A4_mm_direct_offset.dxf", dy=250000.35)                              # mm, typed coordinates (exact here)
inserted("A5_mm_block_rot30_offset.dxf", (64587.608, -241759.95), 30.0)        # mm, a 30 degree wing at a site offset
inserted("A6_m_block_rot30_offset.dxf", (-795.601935, 13.38432), 30.0, scale=0.001, units=6)  # metres, 30 degrees
print(sorted(p.name for p in OUT.glob("*.dxf")))
