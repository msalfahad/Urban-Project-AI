"""T-744 synthetic villa N744 (NOT a client drawing): two bathrooms side by side, mirror images about x = 2,750 mm,
built with ezdxf and read back through the architectural route's reader composition (tests/t010 plan_fixtures.
read_plan). Layer and block names are deliberately unlike any project's.

Room L (west): inside 0 .. 2600 x 0 .. 2200 mm. Room R (east): its mirror, inside 2900 .. 5500 x 0 .. 2200.
Blocks:
    TAG-WC      text only: TEXT '03' (a room number) - a room tag NAMED like a WC, never a fixture
    TAG-WASH    text only: TEXT '04'                 - a room tag NAMED like a basin
    WC-PAN      a WC drawn: cistern 500 x 200 + pan circle r 180 (geometry)
    WC-WRAP     no own entity: one nested INSERT of WC-PAN (geometry through nesting)
    WC-EMPTY    no entity at all
Hand truth (owner Q-13 B: the room label decides; a name alone is not a fixture; L-T743-1 content decides):
    a TAG-WC in a space is 0 WC; a WC-PAN or WC-WRAP is 1 WC; a WC-EMPTY is nothing drawn.
"""

from __future__ import annotations

import ezdxf
from ezdxf.math import Matrix44

WALL, FURN, NAMES = "PARTITION-X", "FITTINGS-Y", "TAGS-Z"
ROLES = {WALL: "WALL", FURN: "OTHER", NAMES: "OTHER", "0": "OTHER"}
ROOM_L = [(0, 0), (2600, 0), (2600, 2200), (0, 2200)]
MIRROR_X = 2750.0


def mirror_pt(p):
    return (2 * MIRROR_X - p[0], p[1])


def _box(msp, x0, y0, x1, y1):
    L = lambda a, b: msp.add_line(a, b, dxfattribs={"layer": WALL})       # noqa: E731
    L((x0, y0), (x1, y0)), L((x1, y0), (x1, y1)), L((x1, y1), (x0, y1)), L((x0, y1), (x0, y0))


def _blocks(doc):
    b = doc.blocks.new("TAG-WC")
    b.add_text("03", dxfattribs={"layer": "0", "height": 120})
    b = doc.blocks.new("TAG-WASH")
    b.add_text("04", dxfattribs={"layer": "0", "height": 120})
    b = doc.blocks.new("WC-PAN")
    b.add_lwpolyline([(-250, 0), (250, 0), (250, 200), (-250, 200)], close=True, dxfattribs={"layer": "0"})
    b.add_circle((0, -250), 180, dxfattribs={"layer": "0"})
    b = doc.blocks.new("WC-WRAP")
    b.add_blockref("WC-PAN", (0, 0))
    doc.blocks.new("WC-EMPTY")


def villa(path, *, left=(), right=(), label_left=None, label_right=None, mirror_drawing=False):
    """write N744; left / right: [(block name, (x, y) in room-L local mm)]; the right room's items are mirrored.
    mirror_drawing mirrors the whole sheet about x = 0 afterwards (an adverse transform). -> (poly L, poly R)."""
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    for n in (WALL, FURN, NAMES):
        doc.layers.add(n)
    _blocks(doc)
    msp = doc.modelspace()
    _box(msp, 0, 0, 2600, 2200)
    _box(msp, 2900, 0, 5500, 2200)
    _box(msp, -150, -150, 5650, 2350)
    for name, p in left:
        msp.add_blockref(name, p, dxfattribs={"layer": FURN})
    for name, p in right:
        q = mirror_pt(p)
        msp.add_blockref(name, q, dxfattribs={"layer": FURN, "xscale": -1})
    if label_left:
        msp.add_text(label_left, dxfattribs={"layer": NAMES, "height": 150}).set_placement((600, 1000))
    if label_right:
        msp.add_text(label_right, dxfattribs={"layer": NAMES, "height": 150}).set_placement(mirror_pt((1600, 1000)))
    m = Matrix44.scale(-1, 1, 1) if mirror_drawing else Matrix44()
    m = m @ Matrix44.translate(61_000, -24_000, 0)
    for e in list(msp):
        e.transform(m)
    doc.saveas(str(path))
    pl = [tuple(m.transform((x, y, 0)))[:2] for x, y in ROOM_L]
    pr = [tuple(m.transform((*mirror_pt((x, y)), 0)))[:2] for x, y in ROOM_L]
    return pl, pr
