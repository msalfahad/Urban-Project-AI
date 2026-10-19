"""T-010 synthetic plans (NOT a client drawing): one small room drawn in mm, built with ezdxf and read back through the
architectural route's own reader composition (tools/urban_boq_m9._arch_compute: urban_intake.read + arch_intake.
read_arch + ellipse chords). Layer names are deliberately unlike any project's: WALLS-150 (wall), M-FURNITURE
(furniture), P-SANIT (sanitary), ROOM-NAMES (labels).

Local geometry (mm, before any transform): the room's inside face 0 .. 2600 x 0 .. 2200; 150 mm walls; a 0.80 m door
gap in the south wall (x 300 .. 1100). Hand truth of the wet scope (computed by hand, not by the engine):
    floor                2.60 x 2.20                     = 5.72 m2
    boundary (one-sided) 2 x (2.60 + 2.20)               = 9.60 m  (doorway included, UP-WP-002 'no door deduction')
    upturn               9.60 x 0.20                     = 1.92 m2
    doorway piece        0.80 x 0.15                     = 0.12 m2
    membrane             5.72 + 1.92 + 0.12              = 7.76 m2
    wall porcelain       9.60 x 3.00 - 0.80 x 2.20 (door) - 0.60 x 0.80 (window) = 28.80 - 1.76 - 0.48 = 26.56 m2
"""

from __future__ import annotations

import math

import ezdxf
from ezdxf.math import Matrix44

WALL, FURN, SAN, NAMES = "WALLS-150", "M-FURNITURE", "P-SANIT", "ROOM-NAMES"
ROLES = {WALL: "WALL", FURN: "OTHER", SAN: "OTHER", NAMES: "OTHER", "0": "OTHER", "DOORS": "DOOR"}
INSIDE = [(0, 0), (2600, 0), (2600, 2200), (0, 2200)]


def _rect(msp, x0, y0, x1, y1, layer):
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": layer})


def _walls(msp):
    L = lambda a, b: msp.add_line(a, b, dxfattribs={"layer": WALL})       # noqa: E731
    # inside faces (the door gap x 300 .. 1100 in the south wall) and outside faces
    L((0, 0), (300, 0)), L((1100, 0), (2600, 0)), L((2600, 0), (2600, 2200)), L((2600, 2200), (0, 2200))
    L((0, 2200), (0, 0))
    L((-150, -150), (300, -150)), L((1100, -150), (2750, -150)), L((2750, -150), (2750, 2350))
    L((2750, 2350), (-150, 2350)), L((-150, 2350), (-150, -150))
    L((300, 0), (300, -150)), L((1100, 0), (1100, -150))                  # jambs
    msp.add_arc((300, 0), 800, 0, 90, dxfattribs={"layer": "DOORS"})       # door swing into the room
    msp.add_line((300, 0), (300, 800), dxfattribs={"layer": "DOORS"})


def _blocks(doc):
    b = doc.blocks.new("LAVATORY-01")                     # a wash basin: deck 500 x 400, bowl r 150 (origin = deck SW)
    _rect(b, 0, 0, 500, 400, "0")
    b.add_circle((250, 180), 150, dxfattribs={"layer": "0"})
    b = doc.blocks.new("WC-WALLHUNG")                     # a WC block: cistern on the wall, elliptical pan
    _rect(b, -250, 0, 250, 200, "0")
    b.add_ellipse((0, -300), major_axis=(0, 300), ratio=200 / 300, dxfattribs={"layer": "0"})
    b = doc.blocks.new("SHOWER-TRAY-900")
    _rect(b, 0, 0, 900, 900, "0")
    b = doc.blocks.new("FLOOR_DRAIN_100")
    b.add_circle((0, 0), 50, dxfattribs={"layer": "0"})
    b = doc.blocks.new("COOKER-4")
    _rect(b, 0, 0, 600, 600, "0")


def _exploded_wc(msp, layer):
    """a water closet drawn as loose lines: cistern 0.50 x 0.20 on the north wall face, bowl 0.40 x 0.60."""
    _rect(msp, 1000, 2000, 1500, 2200, layer)
    msp.add_ellipse((1250, 1700), major_axis=(0, 300), ratio=200 / 300, dxfattribs={"layer": layer})


def _wc_sized_chair(msp, layer):
    """L-P8-01: a seat 0.40 x 0.55 touching a back 0.45 x 0.15 on the north wall face (a WC's outline)."""
    _rect(msp, 1025, 2050, 1475, 2200, layer)
    msp.add_ellipse((1250, 2050 - 275), major_axis=(0, 275), ratio=200 / 275, dxfattribs={"layer": layer})


ITEMS = {
    "BASIN": lambda doc, msp: msp.add_blockref("LAVATORY-01", (1900, 1750), dxfattribs={"layer": FURN}),
    "BASIN_ON_SANITARY": lambda doc, msp: msp.add_blockref("LAVATORY-01", (1900, 1750), dxfattribs={"layer": SAN}),
    "WC_BLOCK": lambda doc, msp: msp.add_blockref("WC-WALLHUNG", (1250, 2000), dxfattribs={"layer": FURN}),
    "SHOWER_BLOCK": lambda doc, msp: msp.add_blockref("SHOWER-TRAY-900", (1650, 50), dxfattribs={"layer": FURN}),
    "DRAIN_BLOCK": lambda doc, msp: msp.add_blockref("FLOOR_DRAIN_100", (2000, 600), dxfattribs={"layer": FURN}),
    "DRAIN_TEXT": lambda doc, msp: msp.add_text("F.D", dxfattribs={"layer": NAMES, "height": 80}).set_placement(
        (2000, 600)),
    "COOKER": lambda doc, msp: msp.add_blockref("COOKER-4", (100, 1500), dxfattribs={"layer": FURN}),
    "EXPLODED_WC_FURN": lambda doc, msp: _exploded_wc(msp, FURN),
    "EXPLODED_WC_SAN": lambda doc, msp: _exploded_wc(msp, SAN),
    "WC_SIZED_CHAIR": lambda doc, msp: _wc_sized_chair(msp, FURN),
}


def transform_matrix(transform):
    """'none' | 'rot37' | 'mirror' | 'metres' | 'rot37_mirror_metres' -> (Matrix44 in mm, unit scale)."""
    m = Matrix44()
    if "mirror" in transform:
        m = m @ Matrix44.scale(-1, 1, 1)
    if "rot37" in transform:
        m = m @ Matrix44.z_rotate(math.radians(37))
    m = m @ Matrix44.translate(52_000, -31_000, 0)       # far from the origin, as real sheets are
    scale = 0.001 if "metres" in transform else 1.0
    if scale != 1.0:
        m = m @ Matrix44.scale(scale, scale, scale)
    return m, scale


def room_dxf(path, *, label=None, items=(), transform="none"):
    """write the synthetic room; -> the room's inside polygon in drawing units."""
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6 if "metres" in transform else 4
    for name in (WALL, FURN, SAN, NAMES, "DOORS"):
        doc.layers.add(name)
    _blocks(doc)
    msp = doc.modelspace()
    _walls(msp)
    if label:
        msp.add_text(label, dxfattribs={"layer": NAMES, "height": 150}).set_placement((700, 1100))
    for it in items:
        ITEMS[it](doc, msp)
    m, _ = transform_matrix(transform)
    for e in list(msp):
        e.transform(m)
    doc.saveas(str(path))
    poly = [tuple(m.transform((x, y, 0)))[:2] for x, y in INSIDE]
    return poly


def read_plan(path):
    """the architectural route's entities of one drawing, composed exactly as tools/urban_boq_m9._arch_compute does
    (intake segments + arch_intake extra geometry + ellipse chords; arch_intake texts and inserts)."""
    from tools import arch_intake as AI
    from tools import urban_intake as UI
    E = UI.read(str(path))
    A = AI.read_arch(path, unit_m=E.get("unit_m"))
    chords = AI.ellipse_chords(E.get("ellipses") or [], E["unit_m"])
    return dict(E, texts=A["texts"], inserts=A["inserts"], segments=E["segments"] + A["extra_segments"] + chords,
                arcs=E["arcs"] + A["extra_arcs"])


def to_m(poly, transform):
    _, s = transform_matrix(transform)
    u = 1.0 if s != 1.0 else 0.001
    return [(x * u, y * u) for x, y in poly]
