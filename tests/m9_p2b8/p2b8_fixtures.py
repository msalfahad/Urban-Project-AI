"""Phase 2B-8 synthetic fixtures (no private drawing): the Phase 2B-7 plans (tests/m9_p2b7/p2b7_fixtures) plus the
drawings of the V2.7 acceptance-hardening tests. Millimetres; every truth below is derived by hand from the
coordinates, never from the engine.

    wc_plan(path, kind)         p2b7 kinds, and
        PLAIN_LOBBY     the BASIN plan with its basin block deleted: an unlabelled lobby with nothing drawn inside
        ARMCHAIR_AT_WALL the basin + an armchair against the north wall: an elliptical seat 0.45 x 0.55 whose rear
                        touches a 0.45 x 0.15 back rectangle standing on the wall face (a seat wider than a WC bowl)
        WC_SIZED_CHAIR  the basin + a seat 0.40 x 0.55 touching a 0.45 x 0.15 back on the wall face: the outline of a
                        close-coupled water closet at a water closet's size (geometry cannot tell them apart)
        ROUND_TABLE_SHELF the basin + a round table (circle d 0.60) touching a 0.50 x 0.20 shelf on the wall face
        OFFSET_ROUND    the basin + a circle d 0.40 touching the cistern 0.15 m off the cistern's centre line
        BASIN_OWN_WC_LIKE the basin drawn as a block WASH3 whose OWN linework is a bowl-like ellipse 0.38 x 0.55
                        touching a 0.45 x 0.15 rectangle on the wall face (a pedestal basin and its tap deck): the
                        basin's linework, never a second piece of evidence
    bath_corridor_door(path)    a bathroom (BATH) whose 0.80 m door, in a 1.027 m wall gap (the reference plan's
                                pattern: 77 mm return + 150 mm crossing partition, drawn on both faces), opens into an
                                internal CORRIDOR; a STORE east of the partition (DOOR_TRUTH)
Every plan has the sheet frame and title the admission needs."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "m9_p2b7"))
sys.path.insert(0, str(HERE.parents[1]))

import p2b7_fixtures as F7                                    # noqa: E402

F6 = F7.F6
W, DOOR, GLAZ, COL = F7.W, F7.DOOR, F7.GLAZ, F7.COL
ROLES = F7.ROLES
variant = F7.variant
door_plan = F7.door_plan

# the lobby (p2b7_fixtures.wc_plan): x 2400 .. 5800, y 200 .. 3200 (inner faces), 0.20 m walls; its doors: 0.80 m
# (the W.C. door, in the partition x 2200 .. 2400, y 600 .. 1400) and 1.00 m (the external door, x 4600 .. 5600 in the
# south wall); the W.C. x 200 .. 2200. The synthetic S2 heights (tests/m9_p2b6/p2b6_run.FACTS): plaster 3.00, paint
# 3.00, wall tile 2.40, door 2.10.
LOBBY = {"area_m2": 3.40 * 3.00, "perimeter_lm": 2 * (3.40 + 3.00), "doors_m": (0.80, 1.00), "door_h_m": 2.10,
         "plaster_h_m": 3.00, "paint_h_m": 3.00, "tile_h_m": 2.40, "wall_t_m": 0.20}
_DED = sum(LOBBY["doors_m"]) * LOBBY["door_h_m"]                     # 1.80 x 2.10 = 3.78 m2 of door openings
LOBBY_TRUTH = {
    # released: the ceiling is the plan area of the face in every plausible type (UP-CEIL-001; no void, no stair)
    "ceiling_m2": LOBBY["area_m2"],                                  # 10.20
    # conditional, both scenarios: wall run x plaster height - door openings
    "plaster_m2": LOBBY["perimeter_lm"] * LOBBY["plaster_h_m"] - _DED,  # 12.80 x 3.00 - 3.78 = 34.62
    # DRY_SCOPE (lobby / wash area): porcelain floor, paint over the plaster, skirting = boundary - door openings
    "dry_floor_m2": LOBBY["area_m2"],
    "dry_paint_m2": LOBBY["perimeter_lm"] * LOBBY["paint_h_m"] - _DED,  # 34.62
    "skirting_lm": LOBBY["perimeter_lm"] - sum(LOBBY["doors_m"]),    # 12.80 - 1.80 = 11.00
    "dry_external_strip_m2": 1.00 * LOBBY["wall_t_m"],               # 0.20 (floor porcelain through the doorway)
    # WET_SCOPE (UP-WET-001, as a W.C.): wet floor tile, wall tile to 2.40 m (the facts' height, below the owner full
    # height: the skirting remains), membrane floor, upturn on the eligible walls (boundary - doors) x 0.20 m
    "wet_floor_m2": LOBBY["area_m2"],
    "wet_tile_m2": LOBBY["perimeter_lm"] * LOBBY["tile_h_m"] - _DED,    # 30.72 - 3.78 = 26.94
    "wet_wp_floor_m2": LOBBY["area_m2"],
    "wet_wall_upturn_m2": (LOBBY["perimeter_lm"] - sum(LOBBY["doors_m"])) * 0.20,   # 11.00 x 0.20 = 2.20
    "wet_external_threshold_m2": 1.00 * LOBBY["wall_t_m"],           # 0.20 marble at the external door
    "wet_new_doorway_wp_m2": 1.00 * LOBBY["wall_t_m"],               # 0.20: the external door's piece (the W.C.
                                                                     # door's 0.16 m2 is the W.C.'s or the lobby's,
                                                                     # never both)
}

# the bath / corridor door (bath_corridor_door): the wall gap x 1000 .. 2027 in the wall y 0 .. 200; the door's jamb
# lines at 1000 and 1800, its frame lines 50 mm in (1050, 1750), its leaf 0.70 m (swing radius) hinged at (1750, 200);
# the remainder 1800 .. 2027 is the 77 mm return (1800 .. 1877) and the 150 mm partition (1877 .. 2027), drawn on both
# faces
DOOR_TRUTH = {"as_drawn_wall_opening_m": 1.027, "jamb_span_m": 0.80, "leaf_m": 0.70, "owner_minimum_m": 0.90,
              "category": "BATHROOM_PVC", "symbol_difference_m": 0.80 - 0.70,          # 0.10: CAD symbol geometry
              "structural_shortfall_m": 0.90 - 0.80,                                   # 0.10
              "leaf_shortfall_m": 0.90 - 0.70,                                         # 0.20
              "remainder_m": 1.027 - 0.80,                                             # 0.227 wall on both faces
              "remainder_after_m": 1.027 - 0.90,                                       # 0.127 if widened to 0.90
              "door_h_m": 2.10}


def wc_plan(path, kind="BASIN"):
    if kind in ("PLAIN_LOBBY", "ARMCHAIR_AT_WALL", "WC_SIZED_CHAIR", "ROUND_TABLE_SHELF", "OFFSET_ROUND",
                "BASIN_OWN_WC_LIKE"):
        return _wc_more(path, kind)
    return F7.wc_plan(path, kind)


def _wc_more(path, kind):
    import ezdxf
    tmp = Path(str(path) + ".base.dxf")
    F7.wc_plan(tmp, "BASIN")
    doc = ezdxf.readfile(str(tmp))
    tmp.unlink()
    msp = doc.modelspace()
    if kind in ("PLAIN_LOBBY", "BASIN_OWN_WC_LIKE"):
        for e in list(msp.query("INSERT")):
            if e.dxf.name == "WASH":
                msp.delete_entity(e)
    furn = {"layer": "A-FURN"}
    if kind == "ARMCHAIR_AT_WALL":
        # the back 0.45 x 0.15 on the north wall face (y 3200), the seat 0.45 wide x 0.55 deep in front of it
        msp.add_lwpolyline([(3775, 3050), (4225, 3050), (4225, 3200), (3775, 3200)], close=True, dxfattribs=furn)
        msp.add_ellipse((4000, 3050 - 275), major_axis=(0, 275), ratio=225 / 275, dxfattribs=furn)
    elif kind == "WC_SIZED_CHAIR":
        msp.add_lwpolyline([(3775, 3050), (4225, 3050), (4225, 3200), (3775, 3200)], close=True, dxfattribs=furn)
        msp.add_ellipse((4000, 3050 - 275), major_axis=(0, 275), ratio=200 / 275, dxfattribs=furn)
    elif kind == "ROUND_TABLE_SHELF":
        msp.add_lwpolyline([(4000, 3000), (4500, 3000), (4500, 3200), (4000, 3200)], close=True, dxfattribs=furn)
        msp.add_circle((4250, 2700), 300, dxfattribs=furn)
    elif kind == "OFFSET_ROUND":
        msp.add_lwpolyline([(4000, 3000), (4500, 3000), (4500, 3200), (4000, 3200)], close=True, dxfattribs=furn)
        msp.add_circle((4400, 2800), 200, dxfattribs=furn)
    elif kind == "BASIN_OWN_WC_LIKE":
        blk = doc.blocks.new("WASH3")
        blk.add_lwpolyline([(-225, 0), (225, 0), (225, 150), (-225, 150)], close=True, dxfattribs={"layer": "0"})
        blk.add_ellipse((0, -275), major_axis=(0, 275), ratio=190 / 275, dxfattribs={"layer": "0"})
        # the block's origin on the wall face: its deck (0 .. 150 above it) stands against the wall
        msp.add_blockref("WASH3", (4000, 3050), dxfattribs=furn)
    doc.saveas(str(path))
    return path


def bath_corridor_door(path):
    """the p2b6 shell (north / east / west walls of 0 .. 4400 x 0 .. 3400, inner 200 .. 4200 x 200 .. 3200, a 0.60 m
    east window); the wall y 0 .. 200 with the CROSSING gap x 1000 .. 2027; the partition x 1877 .. 2027 north to the
    north wall (BATH west, BEDROOM east) and south to the corridor's south wall; below the wall a corridor y -1500 .. 0
    (outer face y -1700, side walls continuing the shell's) split by the partition: CORRIDOR west, STORE east."""
    doc, msp = F6._doc()
    F6._shell(msp)
    L = F6._lines
    # the wall y 0 .. 200: both faces stop at the side walls' inner faces (x 200 / 4200), the gap 1000 .. 2027
    L(msp, [((200, 0), (1000, 0)), ((200, 200), (1000, 200)), ((1000, 0), (1000, 200)),
            ((2027, 0), (4200, 0)), ((2027, 200), (4200, 200))])
    # the 77 mm return and the partition crossing the wall (on both faces)
    L(msp, [((1800, 0), (1877, 0)), ((1800, 200), (1877, 200)),
            ((1877, 200), (1877, 3200)), ((2027, 200), (2027, 3200)),
            ((1877, 0), (1877, -1500)), ((2027, 0), (2027, -1500))])
    # the corridor: side walls continue down, the south wall y -1700 .. -1500
    L(msp, [((0, 0), (0, -1700)), ((200, 0), (200, -1500)), ((4400, 0), (4400, -1700)), ((4200, 0), (4200, -1500)),
            ((0, -1700), (4400, -1700)), ((200, -1500), (1877, -1500)), ((2027, -1500), (4200, -1500))])
    F6._door(msp, 1000, 1800)
    for txt, xy in (("BATH", (900, 1700)), ("BEDROOM", (2900, 1700)), ("CORRIDOR", (700, -800)),
                    ("STORE", (2900, -800))):
        msp.add_text(txt, dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement(xy)
    doc.saveas(str(path))
    return path


def column_in_wall(path, through=False):
    """the p2b6 PLAIN bathroom (4.00 x 3.00 m, its 0.80 m door in the south wall) whose north wall (y 3200 .. 3400) is
    interrupted by a 0.30 m column standing across its whole thickness (x 2000 .. 2300, a closed polyline on A-COL):
    the wall faces stop at the column's sides (through=True: the wall's face lines run on through the column, the
    column drawn over them). Turned with the plan (variant rot30) the column is no longer axis-aligned; every
    quantity must stay the same."""
    doc, msp = F6._doc()
    L = F6._lines
    # east / west walls and the east window as in the p2b6 shell; the north wall split at the column
    L(msp, [((4400, 0), (4400, 1000)), ((4400, 1600), (4400, 3400)), ((0, 3400), (0, 0)),
            ((4200, 200), (4200, 1000)), ((4200, 1600), (4200, 3200)), ((200, 3200), (200, 200)),
            ((4200, 1000), (4400, 1000)), ((4200, 1600), (4400, 1600)),
            *((((0, 3400), (4400, 3400)), ((200, 3200), (4200, 3200))) if through else
              (((0, 3400), (2000, 3400)), ((2300, 3400), (4400, 3400)), ((200, 3200), (2000, 3200)),
               ((2300, 3200), (4200, 3200))))])
    msp.add_line((4300, 1000), (4300, 1600), dxfattribs={"layer": GLAZ})
    msp.add_lwpolyline([(2000, 3200), (2300, 3200), (2300, 3400), (2000, 3400)], close=True,
                       dxfattribs={"layer": COL})
    F6._south_plain(msp)
    F6._door(msp, 1000, 1800)
    msp.add_text("BATH", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((2000, 1700))
    doc.saveas(str(path))
    return path


def wide_door_plan(path):
    """the p2b6 PLAIN bathroom with a 1.10 m door (gap and jamb lines 1000 .. 2100, frame lines 50 mm in, the 1.00 m
    leaf hinged at (2050, 200)) to the outside: an ordinary external door above the 1.00 m minimum on every reading."""
    doc, msp = F6._doc()
    F6._shell(msp)
    F6._south_plain(msp, 1000, 2100)
    F6._door(msp, 1000, 2100)
    msp.add_text("BATH", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((2000, 1700))
    doc.saveas(str(path))
    return path
