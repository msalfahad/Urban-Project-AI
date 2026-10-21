"""Phase 2B-7 synthetic fixtures (no private drawing): the Phase 2B-6 plans (tests/m9_p2b6/p2b6_fixtures) plus the
adversarial drawings of the ARCH_TAKEOFF_V2.7 acceptance tests. Millimetres; every truth below is derived by hand
from the coordinates, never from the engine.

    door_plan(path, variant)    p2b6 variants (PLAIN, CROSSING, OPEN_SIDE, COLUMN, DOUBLE) and
        SIDE_PANEL   the 1.027 m wall gap of CROSSING: the 0.80 m door, then a fixed glazed side panel (two glazing
                     lines on A-GLAZ across 1800 .. 2027) and a wall jamb at 2027 - a door in a WIDER opening
        ONE_FACE     CROSSING whose partition stops at the wall: the inner face of the remainder is the 77 mm return and
                     the partition's mouth, the outer face is open - a remainder proven wall on one face only
        TEE          a 150 mm partition meets the wall from the room side only (1800 .. 1950); the outer face of the
                     wall runs on unbroken - a remainder that is a junction mouth on one face, wall on the other
        MIXED        PLAIN with its door symbol AND its window glazing drawn on one layer A-OPEN
        COLUMN_JAMB  a hatched full-thickness column is the far jamb of the gap; a 77 mm strip with nothing drawn
                     lies between the door frame and the column (the p2b6 COLUMN plan - a column narrower than its
                     wall, leaving 25 - 27 mm slots - is a V2.6 fixture only)
    lookalike(path, kind)       p2b6 kinds (WARDROBE, DRAIN, THREE_DRAINS, THRESHOLD, COLUMN) and
        DRAIN_AT_WALL a hatched 0.15 m drain square touching the inner face of the south wall
        FOUR_LINE_COLUMNS three hatched 0.40 m columns of four LINEs each, two against walls, one free
        TURNED_COLUMNS the same three columns drawn as closed polylines turned 30 degrees about their centres
    wc_plan(path, kind)         a W.C. and an unlabelled lobby holding a basin and, by kind, a water closet drawn as
                                loose lines / inside an anonymous block / alone, or an adversary (an oval table, a
                                vanity counter), or the Arabic room word (WC_TRUTH: the lobby's expected scope)
    arc_room(path)              the benchmark B10 bathroom (one curved wall, an inner ARC and an outer bulge) with its
                                door block; transforms through variant()
    column_villa(path, kind)    the synthetic villa with its three 0.40 m columns redrawn: "FOUR_LINES" (each four
                                LINEs, same layer), "TURNED" (closed polylines turned 30 degrees about their centres)
    variant(src, dst, kind)     p2b6 transforms (rot30 / rot90 / mirror / rot37_metres / translate / metres / reorder /
                                nest)

Every plan has the sheet frame and title the admission needs."""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "m9_p2b6"))
sys.path.insert(0, str(HERE.parent / "m9_p2b5_bench"))
sys.path.insert(0, str(HERE.parents[1]))

import p2b6_fixtures as F6                                    # noqa: E402

W, DOOR, GLAZ, COL = F6.W, F6.DOOR, F6.GLAZ, F6.COL
ROLES = F6.ROLES
_ref6 = F6._ref


def _ref(e):
    """p2b6_fixtures._ref, plus the centre of an ELLIPSE (a water-closet bowl) for the frame grouping of variant()."""
    return e.dxf.center if e.dxftype() == "ELLIPSE" else _ref6(e)


F6._ref = _ref
variant = F6.variant
lookalike_p2b6 = F6.lookalike

# hand truth of the door plans (m, m2). door_m: the door's own opening (jamb lines of its symbol); structural_m: the
# wall's structural opening after V2.7 (the jamb span where the rest of the gap is proven wall on both faces, else
# the whole wall gap); remainder: what the rest of the gap is
TRUTH = {
    "PLAIN": {"door_m": 0.80, "structural_m": 0.80, "remainder": None},
    "CROSSING": {"door_m": 0.80, "structural_m": 0.80, "remainder": "WALL_BOTH_FACES"},
    "TEE": {"door_m": 0.80, "structural_m": 0.80, "remainder": "WALL_BOTH_FACES"},
    "OPEN_SIDE": {"door_m": 0.80, "structural_m": 1.027, "remainder": "OPEN"},
    "COLUMN_JAMB": {"door_m": 0.80, "structural_m": 0.877, "remainder": "OPEN"},
    "SIDE_PANEL": {"door_m": 0.80, "structural_m": 1.027, "remainder": "GLAZED_SIDE_PANEL"},
    "ONE_FACE": {"door_m": 0.80, "structural_m": 1.027, "remainder": "WALL_ONE_FACE"},
    "DOUBLE": {"door_m": 1.60, "structural_m": 1.60, "remainder": None},
}


def _lines(msp, segs, layer=W):
    F6._lines(msp, segs, layer)


def door_plan(path, variant_):
    if variant_ in ("PLAIN", "CROSSING", "OPEN_SIDE", "COLUMN", "DOUBLE"):
        return F6.door_plan(path, variant_)
    if variant_ == "COLUMN_JAMB":
        return _column_jamb(path)
    doc, msp = F6._doc()
    for name in ("A-OPEN", "P-SANITARY"):
        doc.layers.add(name)
    F6._shell(msp) if variant_ != "MIXED" else _shell_mixed(msp)
    if variant_ in ("SIDE_PANEL", "ONE_FACE"):
        g0, g1 = 1000, 2027
        _lines(msp, [((0, 0), (g0, 0)), ((200, 200), (g0, 200)), ((g0, 0), (g0, 200)),
                     ((g1, 0), (4400, 0)), ((g1, 200), (4200, 200))])
        if variant_ == "SIDE_PANEL":
            _lines(msp, [((g1, 0), (g1, 200))])
            _lines(msp, [((1800, 75), (g1, 75)), ((1800, 125), (g1, 125))], GLAZ)
            msp.add_text("BATH", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((2000, 1700))
        else:
            # CROSSING on the room side only: the 77 mm return and the partition's mouth on the inner face; the
            # partition does not cross the wall, the outer face (y = 0) stays open between 1800 and 2027
            _lines(msp, [((1800, 200), (1877, 200)), ((1877, 200), (1877, 3200)), ((g1, 200), (g1, 3200))])
            msp.add_text("BATH", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((900, 1700))
            msp.add_text("BEDROOM", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((2900, 1700))
        F6._door(msp, 1000, 1800)
    elif variant_ == "TEE":
        # south wall: outer face continuous 1800 .. 4400; inner face 1950 .. 4200; the partition 1800 .. 1950 runs
        # north from the inner face to the north wall (y 200 .. 3200)
        _lines(msp, [((0, 0), (1000, 0)), ((200, 200), (1000, 200)), ((1000, 0), (1000, 200)),
                     ((1800, 0), (4400, 0)), ((1950, 200), (4200, 200)),
                     ((1800, 200), (1800, 3200)), ((1950, 200), (1950, 3200))])
        F6._door(msp, 1000, 1800)
        msp.add_text("BATH", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((900, 1700))
        msp.add_text("BEDROOM", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((3000, 1700))
    elif variant_ == "MIXED":
        F6._south_plain(msp)
        for x in (1000, 1800, 1050, 1750):
            msp.add_line((x, 0), (x, 200), dxfattribs={"layer": "A-OPEN"})
        msp.add_line((1750, 200), (1750, 900), dxfattribs={"layer": "A-OPEN"})
        msp.add_arc((1750, 200), 700, 90, 180, dxfattribs={"layer": "A-OPEN"})
        msp.add_text("BEDROOM", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((2000, 1700))
    else:
        raise ValueError(variant_)
    doc.saveas(str(path))
    return path


def _column_jamb(path):
    """a hatched full-thickness 0.15 m column (closed polyline on A-COL) at x 1877 .. 2027 is the far jamb of the wall
    gap; the door's jamb lines at 1000 and 1800; between the door frame and the column a 77 mm strip with nothing
    drawn on either face."""
    doc, msp = F6._doc()
    F6._shell(msp)
    _lines(msp, [((0, 0), (1000, 0)), ((200, 200), (1000, 200)), ((1000, 0), (1000, 200)),
                 ((2027, 0), (4400, 0)), ((2027, 200), (4200, 200))])
    _square_rect(msp, 1877, 0, 2027, 200, COL)
    F6._door(msp, 1000, 1800)
    msp.add_text("BATH", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((2000, 1700))
    doc.saveas(str(path))
    return path


def _square_rect(msp, x0, y0, x1, y1, layer):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
    msp.add_hatch(dxfattribs={"layer": layer}).paths.add_polyline_path(pts, is_closed=True)


def _shell_mixed(msp):
    """F6._shell with its 0.60 m east window's glazing on A-OPEN (the door symbol's layer)."""
    _lines(msp, [((4400, 0), (4400, 1000)), ((4400, 1600), (4400, 3400)), ((4400, 3400), (0, 3400)), ((0, 3400), (0, 0)),
                 ((4200, 200), (4200, 1000)), ((4200, 1600), (4200, 3200)), ((4200, 3200), (200, 3200)),
                 ((200, 3200), (200, 200)), ((4200, 1000), (4400, 1000)), ((4200, 1600), (4400, 1600))])
    msp.add_line((4300, 1000), (4300, 1600), dxfattribs={"layer": "A-OPEN"})


def _square(msp, x0, y0, side, layer, *, lines=True, turn_deg=0.0, hatch=True):
    c = (x0 + side / 2, y0 + side / 2)
    t = math.radians(turn_deg)
    pts = []
    for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = dx * side / 2, dy * side / 2
        pts.append((c[0] + x * math.cos(t) - y * math.sin(t), c[1] + x * math.sin(t) + y * math.cos(t)))
    if lines:
        _lines(msp, list(zip(pts, pts[1:] + pts[:1])), layer)
    else:
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
    if hatch:
        msp.add_hatch(dxfattribs={"layer": layer}).paths.add_polyline_path(pts, is_closed=True)
    return pts


# hand truth of the lookalikes (the PLAIN room 4.00 x 3.00, BEDROOM): (area m2, perimeter m, the layer's V2.7 role)
LOOK_TRUTH = {
    "DRAIN": (12.0, 14.0, "OTHER"),
    "THREE_DRAINS": (12.0, 14.0, "OTHER"),
    "DRAIN_AT_WALL": (12.0, 14.0, "OTHER"),
    "WARDROBE": (12.0, 14.0, "OTHER"),
    "THRESHOLD": (12.0, 14.0, "OTHER"),
    # one 0.30 m column against the south wall's inner face: 12 - 0.09; the boundary goes round its two sides
    "COLUMN": (round(12.0 - 0.09, 6), 14.6, "COLUMN"),
    # three 0.40 m columns: (3500, 200) against the south wall, (200, 1500) against the west wall, (2000, 1400) free:
    # 12 - 3 x 0.16 = 11.52; boundary 14 + 2 x 0.40 (south one) + 2 x 0.40 (west one) + 1.60 (the free one, a hole)
    "FOUR_LINE_COLUMNS": (round(12.0 - 3 * 0.16, 6), round(14.0 + 4 * 0.40 + 1.6, 6), "COLUMN"),
    # three turned 0.40 m columns, all free (holes): 12 - 3 x 0.16; boundary 14 + 3 x 1.60
    "TURNED_COLUMNS": (round(12.0 - 3 * 0.16, 6), round(14.0 + 3 * 1.6, 6), "COLUMN"),
}


def lookalike(path, kind):
    if kind in ("WARDROBE", "DRAIN", "THREE_DRAINS", "THRESHOLD", "COLUMN"):
        return F6.lookalike(path, kind)
    doc, msp = F6._doc()
    F6._shell(msp)
    F6._south_plain(msp)
    F6._door(msp, 1000, 1800)
    msp.add_text("BEDROOM", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((2600, 2600))
    if kind == "DRAIN_AT_WALL":
        _square(msp, 2500, 200, 150, "P-DRAIN")
    elif kind == "FOUR_LINE_COLUMNS":
        for x0, y0 in ((3500, 200), (200, 1500), (2000, 1400)):
            _square(msp, x0, y0, 400, "S-COL")
    elif kind == "TURNED_COLUMNS":
        # turned columns cannot stand flush against an axis-aligned wall face: all three stand free, centres as
        # above shifted 0.40 m into the room
        for x0, y0 in ((3300, 700), (700, 1500), (2000, 1400)):
            _square(msp, x0, y0, 400, "S-COL", lines=False, turn_deg=30.0)
    else:
        raise ValueError(kind)
    doc.saveas(str(path))
    return path


def wc_plan(path, kind="BASIN"):
    """a W.C. (room word W.C.) x 200..2200 and an unlabelled LOBBY x 2400..5800, y 200..3200 (inner faces), 0.20 m
    walls; a 0.80 m door W.C. -> lobby in the partition (y 600..1400, swinging into the W.C.), a 1.00 m external door
    in the lobby's south wall (x 4600..5600, swinging out). The lobby holds, by kind:
        BASIN          a WASH block (basin) against the north wall only
        EXPLODED       the basin + a water closet drawn as loose lines on P-SANITARY: cistern 0.50 x 0.20 against
                       the north wall (x 4000..4500, y 3000..3200) and its bowl, an ellipse 0.40 x 0.60 whose rear
                       end touches the cistern (centre (4250, 2700))
        EXPLODED_FURN  the same water closet on A-FURN (no sanitary layer name: the shape is the only evidence)
        ANON_BLOCK     the same water closet inside an anonymously named block A$C51 (inserted on A-FURN)
        ALONE          the EXPLODED_FURN water closet and NO basin
        OVAL_TABLE     the basin + an ellipse 1.20 x 0.80 (a table) and a 0.50 x 0.20 bench apart from it
        BASIN_COUNTER  the basin + a 1.20 x 0.60 counter against the north wall with a 0.50 x 0.35 ellipse INSIDE it
        ARABIC         the basin + the Arabic room word for a W.C. inside the lobby
        BASIN_FITTINGS the basin + its own fittings drawn loose on P-SANITARY beside the block (two tap circles, a
                       waste circle, two spout lines, the counter's rear edge 0.50 m): the basin's linework, not a
                       second piece of evidence (found on the reference plan)
        BIDET          the basin + a bowl (ellipse 0.40 x 0.60) with no cistern
        CHAIR          the basin + a chair: a seat 0.45 x 0.45 with rounded corners and a 0.45 x 0.08 back
        DETACHED       the basin + the EXPLODED_FURN bowl and cistern with 0.25 m between them (not touching)
        ROUND_BOWL     the basin + a water closet whose bowl is drawn as a circle r 0.20 m touching the cistern
        SEAT_LOOKALIKE the basin + an armchair drawn with a WC's outline: an elliptical seat 0.45 x 0.55 whose rear
                       touches a 0.45 x 0.15 back rectangle set across it"""
    doc, msp = F6._doc()
    for name in ("P-SANITARY",):
        doc.layers.add(name)
    blk = doc.blocks.new("WASH")
    blk.add_lwpolyline([(0, 0), (500, 0), (500, 400), (0, 400)], close=True, dxfattribs={"layer": "0"})
    blk.add_circle((250, 220), 150, dxfattribs={"layer": "0"})
    # outer 0..6000 x 0..3400; the partition x 2200..2400 with its gap y 600..1400; the external gap x 4600..5600
    _lines(msp, [((0, 0), (0, 3400)), ((0, 3400), (6000, 3400)), ((6000, 3400), (6000, 0)),
                 ((0, 0), (4600, 0)), ((5600, 0), (6000, 0)), ((4600, 0), (4600, 200)), ((5600, 0), (5600, 200)),
                 ((200, 200), (2200, 200)), ((2400, 200), (4600, 200)), ((5600, 200), (5800, 200)),
                 ((200, 200), (200, 3200)), ((200, 3200), (2200, 3200)), ((2400, 3200), (5800, 3200)),
                 ((5800, 3200), (5800, 200)),
                 ((2200, 200), (2200, 600)), ((2200, 1400), (2200, 3200)), ((2400, 200), (2400, 600)),
                 ((2400, 1400), (2400, 3200)), ((2200, 600), (2400, 600)), ((2200, 1400), (2400, 1400))])
    # the partition door: jamb lines, leaf from the hinge (2200, 650) into the W.C., 90-degree swing
    for y in (600, 1400):
        msp.add_line((2200, y), (2400, y), dxfattribs={"layer": DOOR})
    msp.add_line((2200, 650), (1500, 650), dxfattribs={"layer": DOOR})
    msp.add_arc((2200, 650), 700, 90, 180, dxfattribs={"layer": DOOR})
    # the external door: jamb lines, leaf from the hinge (5550, 0) out of the building, 90-degree swing
    for x in (4600, 5600):
        msp.add_line((x, 0), (x, 200), dxfattribs={"layer": DOOR})
    msp.add_line((5550, 0), (5550, -900), dxfattribs={"layer": DOOR})
    msp.add_arc((5550, 0), 900, 180, 270, dxfattribs={"layer": DOOR})
    msp.add_text("W.C.", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((900, 2000))
    if kind != "ALONE":
        msp.add_blockref("WASH", (2600, 2600), dxfattribs={"layer": "A-FURN"})
    if kind in ("EXPLODED", "EXPLODED_FURN", "ALONE", "ANON_BLOCK"):
        target, ox, oy, lay = msp, 0.0, 0.0, ("P-SANITARY" if kind == "EXPLODED" else "A-FURN")
        if kind == "ANON_BLOCK":
            target, ox, oy, lay = doc.blocks.new("A$C51"), -4250.0, -2700.0, "0"
        target.add_lwpolyline([(4000 + ox, 3000 + oy), (4500 + ox, 3000 + oy), (4500 + ox, 3200 + oy),
                               (4000 + ox, 3200 + oy)], close=True, dxfattribs={"layer": lay})
        target.add_ellipse((4250 + ox, 2700 + oy), major_axis=(0, 300), ratio=200 / 300, dxfattribs={"layer": lay})
        if kind == "ANON_BLOCK":
            msp.add_blockref("A$C51", (4250, 2700), dxfattribs={"layer": "A-FURN"})
    elif kind == "OVAL_TABLE":
        msp.add_ellipse((4000, 1700), major_axis=(600, 0), ratio=400 / 600, dxfattribs={"layer": "A-FURN"})
        msp.add_lwpolyline([(2800, 900), (3300, 900), (3300, 1100), (2800, 1100)], close=True,
                           dxfattribs={"layer": "A-FURN"})
    elif kind == "BASIN_COUNTER":
        msp.add_lwpolyline([(3800, 2600), (5000, 2600), (5000, 3200), (3800, 3200)], close=True,
                           dxfattribs={"layer": "A-FURN"})
        msp.add_ellipse((4400, 2900), major_axis=(250, 0), ratio=175 / 250, dxfattribs={"layer": "A-FURN"})
    elif kind == "BASIN_FITTINGS":
        # the WASH block sits at (2600, 2600), 500 x 400; its fittings within 0.10 m of it
        for c, r in (((2780, 2960), 25), ((2920, 2960), 25), ((2850, 2820), 30)):
            msp.add_circle(c, r, dxfattribs={"layer": "P-SANITARY"})
        _lines(msp, [((2780, 2960), (2800, 2900)), ((2920, 2960), (2900, 2900)), ((2600, 3050), (3100, 3050))],
               "P-SANITARY")
    elif kind == "BIDET":
        msp.add_ellipse((4250, 2700), major_axis=(0, 300), ratio=200 / 300, dxfattribs={"layer": "A-FURN"})
    elif kind == "DETACHED":
        # the bowl's rear end at y 2750, the cistern from y 3000: 0.25 m apart
        msp.add_ellipse((4250, 2450), major_axis=(0, 300), ratio=200 / 300, dxfattribs={"layer": "A-FURN"})
        msp.add_lwpolyline([(4000, 3000), (4500, 3000), (4500, 3200), (4000, 3200)], close=True,
                           dxfattribs={"layer": "A-FURN"})
    elif kind == "CHAIR":
        r = 60
        msp.add_lwpolyline([(3800 + r, 1500, 0, 0, 0), (4250 - r, 1500, 0, 0, 0.4142), (4250, 1500 + r, 0, 0, 0),
                            (4250, 1950 - r, 0, 0, 0.4142), (4250 - r, 1950, 0, 0, 0), (3800 + r, 1950, 0, 0, 0.4142),
                            (3800, 1950 - r, 0, 0, 0), (3800, 1500 + r, 0, 0, 0.4142)], format="xyseb", close=True,
                           dxfattribs={"layer": "A-FURN"})
        msp.add_lwpolyline([(3800, 1950), (4250, 1950), (4250, 2030), (3800, 2030)], close=True,
                           dxfattribs={"layer": "A-FURN"})
    elif kind == "ROUND_BOWL":
        msp.add_lwpolyline([(4000, 3000), (4500, 3000), (4500, 3200), (4000, 3200)], close=True,
                           dxfattribs={"layer": "A-FURN"})
        msp.add_circle((4250, 2800), 200, dxfattribs={"layer": "A-FURN"})
    elif kind == "SEAT_LOOKALIKE":
        msp.add_ellipse((4000, 1600), major_axis=(0, 275), ratio=225 / 275, dxfattribs={"layer": "A-FURN"})
        msp.add_lwpolyline([(3775, 1875), (4225, 1875), (4225, 2025), (3775, 2025)], close=True,
                           dxfattribs={"layer": "A-FURN"})
    elif kind == "ARABIC":
        msp.add_text("\u062f\u0648\u0631\u0629 \u0645\u064a\u0627\u0647", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((3800, 1600))
    elif kind != "BASIN":
        raise ValueError(kind)
    doc.saveas(str(path))
    return path


# the lobby: 3.40 x 3.00 m (x 2400..5800, y 200..3200); the W.C. 2.00 x 3.00 m
WC_TRUTH = {"lobby_m2": 10.2, "wc_m2": 6.0,
            "BASIN": "REVIEW", "EXPLODED": "WET", "EXPLODED_FURN": "WET", "ANON_BLOCK": "WET", "ALONE": "REVIEW",
            "OVAL_TABLE": "REVIEW", "BASIN_COUNTER": "REVIEW", "ARABIC": "WET",
            "BASIN_FITTINGS": "REVIEW", "BIDET": "REVIEW", "CHAIR": "REVIEW", "DETACHED": "REVIEW",
            # the desired readings of two cases the shape rule gets wrong (tests/m9_p2b7/test_p2b7_unproven: xfail)
            "ROUND_BOWL": "WET", "SEAT_LOOKALIKE": "REVIEW"}


def arc_room(path):
    import bench_cases as BC
    import bench_drawings as BD
    BD.dxf(BC.BY_ID["B10"], Path(path))
    return path


# B10 hand truth (bench_cases B10; the curved band from the coordinates): the inner face an arc r 2.50 m about
# (2200, 1700) over +-asin(0.6) = +-36.86989765 deg; the outer face an arc r 2.70 m about the same centre
B10_SWEEP = 2 * math.asin(0.6)                                # 1.287002218 rad, the inner arc's sweep
B10 = {"area_m2": 13.021881929958028, "perimeter_m": 14.217505543966421,
       "arc_inner_m": 2.5 * B10_SWEEP, "arc_mid_m": 2.6 * B10_SWEEP, "arc_outer_m": 2.7 * B10_SWEEP,
       "strip_m2": B10_SWEEP * (2.7 ** 2 - 2.5 ** 2) / 2, "t_m": 0.20}


def column_villa(path, kind):
    """the synthetic villa (tools/arch_synth.villa) with the three GF columns redrawn: FOUR_LINES or TURNED."""
    import ezdxf
    from tools import arch_synth as AS
    base = Path(str(path) + ".base.dxf")
    AS.villa(base)
    doc = ezdxf.readfile(str(base))
    msp = doc.modelspace()
    for e in list(msp):
        if e.dxf.layer == "A-COL":
            msp.delete_entity(e)
    for x0, y0 in AS.GF_COLUMNS:
        _square(msp, x0, y0, 400, "A-COL", lines=(kind == "FOUR_LINES"), turn_deg=30.0 if kind == "TURNED" else 0.0)
    doc.saveas(str(path))
    return path


def framed_door_plan(path, kind):
    """the PLAIN bathroom with a door BLOCK DOORF (jamb lines at 0 / 800 and frame lines at 50 / 750 across the wall,
    the 0.70 m leaf and its swing from the hinge (750, 200)) inserted at (1000, 0), and a 0.60 m window in the south
    wall (x 2800 .. 3400, two glazing lines). kind:
        FLAT        the door insert and the glazing lines in model space
        GROUP       both inside one group block GRP (inserted at the origin): the group's glazing lies in the same
                    wall strip as the door's frame lines
        NEST / GROUP_NEST   FLAT / GROUP with the whole plan inside two levels of blocks (variant "nest")
    Hand truth (FRAMED_TRUTH): door 0.80 m, frame 0.80 m (the block's lines 0 .. 800 in the wall strip), leaf 0.70 m,
    the bath 4.00 x 3.00 = 12.00 m2, two windows of 0.60 m."""
    if kind in ("NEST", "GROUP_NEST"):
        base = Path(str(path) + ".flat.dxf")
        framed_door_plan(base, "FLAT" if kind == "NEST" else "GROUP")
        return variant(base, path, "nest")
    doc, msp = F6._doc()
    F6._shell(msp)
    _lines(msp, [((0, 0), (1000, 0)), ((200, 200), (1000, 200)), ((1000, 0), (1000, 200)),
                 ((1800, 0), (2800, 0)), ((1800, 200), (2800, 200)), ((1800, 0), (1800, 200)),
                 ((2800, 0), (2800, 200)), ((3400, 0), (3400, 200)),
                 ((3400, 0), (4400, 0)), ((3400, 200), (4200, 200))])
    blk = doc.blocks.new("DOORF")
    for x in (0, 800, 50, 750):
        blk.add_line((x, 0), (x, 200), dxfattribs={"layer": "0"})
    blk.add_line((750, 200), (750, 900), dxfattribs={"layer": "0"})
    blk.add_arc((750, 200), 700, 90, 180, dxfattribs={"layer": "0"})
    host = msp
    if kind == "GROUP":
        host = doc.blocks.new("GRP")
        msp.add_blockref("GRP", (0, 0), dxfattribs={"layer": "0"})
    elif kind != "FLAT":
        raise ValueError(kind)
    host.add_blockref("DOORF", (1000, 0), dxfattribs={"layer": DOOR})
    for y in (75, 125):
        host.add_line((2800, y), (3400, y), dxfattribs={"layer": GLAZ})
    msp.add_text("BATH", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((2000, 1700))
    doc.saveas(str(path))
    return path


FRAMED_TRUTH = {"door_m": 0.80, "frame_m": 0.80, "leaf_m": 0.70, "bath_m2": 12.0, "windows_m": [0.6, 0.6]}


def column_row(path, kind):
    """a hall 12.00 x 4.00 m (inner faces x 200 .. 12200, y 200 .. 4200; 0.20 m walls), a 0.80 m door in the south
    wall (x 1000 .. 1800), and hatched 0.40 x 0.40 m columns (closed polylines) on A-COL in one row (their faces on two
    lines 0.40 m apart that span the row - one long "band" of the column layer that is not a wall):
        AT_WALL   four columns against the north wall's inner face at x 1000 / 4500 / 8000 / 11400 (y 3800 .. 4200)
        FREE_ROW  three columns standing free at x 2000 / 5800 / 9600 (y 2000 .. 2400)
    COLUMN_ROW_TRUTH: the hall's area and perimeter (holes included in the perimeter, as the engine reports it)."""
    doc, msp = F6._doc()
    _lines(msp, [((0, 0), (1000, 0)), ((1800, 0), (12400, 0)), ((12400, 0), (12400, 4400)), ((12400, 4400), (0, 4400)),
                 ((0, 4400), (0, 0)), ((200, 200), (1000, 200)), ((1800, 200), (12200, 200)),
                 ((12200, 200), (12200, 4200)), ((12200, 4200), (200, 4200)), ((200, 4200), (200, 200)),
                 ((1000, 0), (1000, 200)), ((1800, 0), (1800, 200))])
    F6._door(msp, 1000, 1800)
    xs, y0 = ((1000, 4500, 8000, 11400), 3800) if kind == "AT_WALL" else ((2000, 5800, 9600), 2000)
    if kind not in ("AT_WALL", "FREE_ROW"):
        raise ValueError(kind)
    for x0 in xs:
        _square(msp, x0, y0, 400, COL, lines=False)
    msp.add_text("BEDROOM", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((6000, 1000))
    doc.saveas(str(path))
    return path


COLUMN_ROW_TRUTH = {"AT_WALL": {"area_m2": 12.0 * 4.0 - 4 * 0.16, "perimeter_m": 2 * (12.0 + 4.0) + 4 * 2 * 0.4},
                    "FREE_ROW": {"area_m2": 12.0 * 4.0 - 3 * 0.16, "perimeter_m": 2 * (12.0 + 4.0) + 3 * 4 * 0.4}}
