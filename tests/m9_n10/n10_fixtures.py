"""Phase N10 synthetic fixtures (no private drawing): curved wall openings, drawn in millimetres on the Phase 2B-6
layers (A-WALL / A-DOOR / A-GLAZ / A-COL), with the Phase 2B-9 height evidence (opening tags, a door / window
schedule, a section). Every truth in n10_truth.py is derived by hand from the coordinates below, never from the engine.

    curved_room(path, opening="WINDOW", evidence=FULL, extra=())
        the quarter-disc BEDROOM of Phase 2B-9 example 4: straight walls along x and y (0.20 m), a 90-degree curved
        wall centred on the inner corner (200, 200), inner radius 3.00 m, outer 3.20 m; door D1 1.00 m in the south
        wall (x 1200..2200); and ONE opening in the curved wall:
          WINDOW         W4 from STUB_DEG to 90 - STUB_DEG (a 0.20 m curved stub on the inner face at each end), radial
                         jamb lines across the wall on A-WALL, glazing an arc r 3.10 m on A-GLAZ; schedule row W4
                         4312 x 1200, sill 1000; its tag outside the wall at r 3.60 m, 45 degrees
          FLOOR_GLAZING  the same opening, W5 4312 x 3000, sill 0 (floor to ceiling)
          DOOR           D2: a gap of 1.00 m on the inner face (1/3 rad) centred on 45 degrees, radial jamb lines, its
                         leaf (0.90 m) hinged on the inner face 50 mm inside the first jamb, swinging into the room
          PASSAGE        the D2 gap with nothing drawn in it
          NO_JAMB        the W4 gap with its glazing and no jamb lines
          SPLAYED        the W4 opening whose outer face stops 20 mm further along the arc at each end (the jamb
                         lines join the inner face ends to the outer ones: a jamb not quite radial)
        extra:
          FURNITURE      a concentric arc r 2.50 m (10..80 degrees) on A-FURN inside the room
          DECOR          arcs r 3.10 m on A-DECO inside the wall body beside the gap (0..STUB_DEG, 90 - STUB_DEG..90)
          WALL_ARC_IN_GAP  an arc r 3.10 m on A-WALL across the gap (a wall line inside it: not an opening)
    nested(path)   the WINDOW room drawn inside a block inserted at (5000, 2000), turned 30 degrees, with the
                   walls, glazing and door in the block (the evidence texts stay in model space, moved with it)
    masonry_room(path, section="TOS", partition=False)
        Phase 2B-9 example 1 (a 4.00 x 3.00 m BEDROOM, 0.20 m walls, door D1 1.00 x 2.20 in the south wall x
        1000..2000, window W1 1.50 x 1.20 sill 1.00 in the north wall x 1250..2750, glazing at mid wall), its tags and
        schedule, and its own SECTION A-A on the GROUND FLOOR band:
          section="TOS"     F.F.L. +-0.00, T.O.S. -0.10, F.C.L. +3.00, U/S SLAB +3.10 (panel 3.20 m, build-up 0.10)
          section="BOB"     the same with B.O.B. +2.60 (a beam bottom: beam depth 0.50 m below the soffit)
          section="NO_TOS"  F.F.L., F.C.L., U/S SLAB only (no structural slab top: the masonry height is not given)
          section="TWO"     SECTION A-A (T.O.S. -0.10) and SECTION B-B (T.O.S. -0.15): the sections disagree
          section="FACADE"  the TOS section plus F.F.L. +3.50 named FIRST FLOOR (floor-to-floor 3.50 m)
          section=None      no section at all
        partition=True adds a 0.15 m partition x 3000..3150 from the south to the north wall's inner faces;
        column / enclosure / annex: a free-standing column inside the room, a closed boundary-wall box 2.00 m around
        the room, a closed 2.00 x 2.00 m wall box 3.00 m east of it (masonry_room's docstring)
Every plan has the sheet frame and title the admission needs."""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "m9_p2b9"))
sys.path.insert(0, str(HERE.parent / "m9_p2b6"))
sys.path.insert(0, str(HERE.parents[1]))

import p2b6_fixtures as F6                                    # noqa: E402
import p2b9_fixtures as F9                                    # noqa: E402

W, DOOR, GLAZ = F6.W, F6.DOOR, F6.GLAZ
ROLES = F6.ROLES
FULL = F9.FULL
variant = F6.variant
C = (200.0, 200.0)
R_IN, R_OUT, R_GLAZ = 3000.0, 3200.0, 3100.0
STUB_DEG = math.degrees(200.0 / R_IN)                         # 3.819719 deg: a 0.20 m stub on the inner arc
DOOR_DEG = math.degrees(1000.0 / R_IN)                        # 19.098593 deg: 1.00 m on the inner arc
SPLAY_MM = 20.0                                               # the outer face's extra run at each end (SPLAYED)
ROWS = {"W4": (4312, 1200, 1000), "W5": (4312, 3000, 0)}


def _pt(r, deg, c=C):
    return c[0] + r * math.cos(math.radians(deg)), c[1] + r * math.sin(math.radians(deg))


def _straight(msp):
    """the south wall (y 0..200) with the door D1 gap x 1200..2200 and the west wall (x 0..200), as example 4."""
    F6._lines(msp, [((0, 0), (1200, 0)), ((2200, 0), (3400, 0)), ((3400, 0), (3400, 200)),
                    ((200, 200), (1200, 200)), ((2200, 200), (3200, 200)),
                    ((1200, 0), (1200, 200)), ((2200, 0), (2200, 200)),
                    ((0, 0), (0, 3400)), ((0, 3400), (200, 3400)), ((200, 200), (200, 3200))])
    F6._door(msp, 1200, 2200)


def _gap(opening):
    if opening in ("DOOR", "PASSAGE"):
        return 45.0 - DOOR_DEG / 2, 45.0 + DOOR_DEG / 2
    return STUB_DEG, 90.0 - STUB_DEG


def _curved_wall(msp, a, b, opening):
    """the two faces with the gap a..b (deg) and the radial jamb lines (none for NO_JAMB)."""
    da = db = 0.0
    if opening == "SPLAYED":                                  # the outer face stops SPLAY_MM further along
        da = db = math.degrees(SPLAY_MM / R_OUT)
    msp.add_arc(C, R_IN, 0, a, dxfattribs={"layer": W})
    msp.add_arc(C, R_IN, b, 90, dxfattribs={"layer": W})
    msp.add_arc(C, R_OUT, 0, a - da, dxfattribs={"layer": W})
    msp.add_arc(C, R_OUT, b + db, 90, dxfattribs={"layer": W})
    if opening != "NO_JAMB":
        msp.add_line(_pt(R_IN, a), _pt(R_OUT, a - da), dxfattribs={"layer": W})
        msp.add_line(_pt(R_IN, b), _pt(R_OUT, b + db), dxfattribs={"layer": W})


def _curved_door(msp, a, b):
    """the leaf hinged on the inner face 50 mm inside the jamb at a, closed toward the jamb at b, open into the room."""
    hinge_deg = a + math.degrees(50.0 / R_IN)
    h = _pt(R_IN, hinge_deg)
    leaf = 900.0
    to_b = math.degrees(math.atan2(_pt(R_IN, b)[1] - h[1], _pt(R_IN, b)[0] - h[0]))
    # open: 90 degrees from the closed direction, toward the centre (into the room)
    cands = [to_b + 90, to_b - 90]
    op_deg = min(cands, key=lambda d: math.dist((h[0] + leaf * math.cos(math.radians(d)),
                                                 h[1] + leaf * math.sin(math.radians(d))), C))
    msp.add_line(h, (h[0] + leaf * math.cos(math.radians(op_deg)), h[1] + leaf * math.sin(math.radians(op_deg))),
                 dxfattribs={"layer": DOOR})
    lo, hi = sorted((to_b, op_deg))
    msp.add_arc(h, leaf, lo, hi, dxfattribs={"layer": DOOR})


def splay_glazing_deg(deg, sense):
    """the angle (deg) where the SPLAYED jamb line from (R_IN, deg) to (R_OUT, deg + sense * splay) crosses R_GLAZ."""
    p, q = _pt(R_IN, deg), _pt(R_OUT, deg + sense * math.degrees(SPLAY_MM / R_OUT))
    dx, dy = q[0] - p[0], q[1] - p[1]
    fx, fy = p[0] - C[0], p[1] - C[1]
    A, B, Cq = dx * dx + dy * dy, 2 * (fx * dx + fy * dy), fx * fx + fy * fy - R_GLAZ ** 2
    t = (-B + math.sqrt(B * B - 4 * A * Cq)) / (2 * A)
    x, y = p[0] + t * dx, p[1] + t * dy
    return math.degrees(math.atan2(y - C[1], x - C[0]))


def _draw(msp, opening, extra):
    a, b = _gap(opening)
    _curved_wall(msp, a, b, opening)
    _straight(msp)
    if opening in ("WINDOW", "FLOOR_GLAZING", "NO_JAMB"):
        msp.add_arc(C, R_GLAZ, a, b, dxfattribs={"layer": GLAZ})
    if opening == "SPLAYED":                                  # the glazing ends on the slanted jamb lines
        msp.add_arc(C, R_GLAZ, splay_glazing_deg(a, -1), splay_glazing_deg(b, 1), dxfattribs={"layer": GLAZ})
    if opening == "DOOR":
        _curved_door(msp, a, b)
    if "FURNITURE" in extra:
        msp.add_arc(C, 2500.0, 10, 80, dxfattribs={"layer": "A-FURN"})
    if "DECOR" in extra:
        msp.add_arc(C, R_GLAZ, 0, a, dxfattribs={"layer": "A-DECO"})
        msp.add_arc(C, R_GLAZ, b, 90, dxfattribs={"layer": "A-DECO"})
    if "WALL_ARC_IN_GAP" in extra:
        msp.add_arc(C, R_GLAZ, a, b, dxfattribs={"layer": W})
    F9._text(msp, "BEDROOM", 1300, 1500)


def _marks(opening):
    m = {"WINDOW": "W4", "SPLAYED": "W4", "NO_JAMB": "W4", "FLOOR_GLAZING": "W5"}.get(opening)
    tags = {"D1": (1600, -500)}
    if m:
        tags[m] = _pt(3600.0, 45.0)
    return (["D1"] + ([m] if m else [])), tags


def curved_room(path, opening="WINDOW", evidence=FULL, extra=()):
    doc, msp = F6._doc()
    for lay in ("A-SECT", "A-DECO"):
        doc.layers.add(lay)
    _draw(msp, opening, extra)
    marks, tags = _marks(opening)
    F9._evidence(msp, evidence, marks, tags, (1300, 1500), rows=ROWS)
    doc.saveas(str(path))
    return Path(path)


def nested(path, evidence=FULL):
    """the WINDOW room inside a block inserted at (5000, 2000) and turned 30 degrees."""
    import ezdxf  # noqa: F401
    doc, msp = F6._doc()
    for lay in ("A-SECT", "A-DECO"):
        doc.layers.add(lay)
    blk = doc.blocks.new("CURVED_ROOM")
    _draw(blk, "WINDOW", ())
    for e in list(blk):                                       # the room word stays in model space (moved below)
        if e.dxftype() == "TEXT":
            blk.delete_entity(e)
    ins, rot = (5000.0, 2000.0), 30.0
    msp.add_blockref("CURVED_ROOM", ins, dxfattribs={"rotation": rot, "layer": "0"})

    def mv(p):
        x, y = p
        cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        return ins[0] + x * cr - y * sr, ins[1] + x * sr + y * cr
    F9._text(msp, "BEDROOM", *mv((1300, 1500)))
    F9._text(msp, "D1", *mv((1600, -500)))
    F9._text(msp, "W4", *mv(_pt(3600.0, 45.0)))
    if "SCHEDULE" in evidence:
        F9._schedule(msp, ["D1", "W4"], ROWS)
    if "SECTION" in evidence:
        F9._section(msp)
    doc.saveas(str(path))
    return Path(path)


def _level_section(msp, x0, title, levels, names=(("GROUND FLOOR", 1500),)):
    """a section sheet on the GROUND FLOOR band: each (label, value_m) text at its level line (y = value x 1000);
    names: the floor names written inside their bands (y in mm)."""
    F9._frame(msp, x0, x0 + 30000, title)
    for label, v in levels:
        y = v * 1000
        msp.add_line((x0 + 2000, y), (x0 + 12000, y), dxfattribs={"layer": "A-SECT"})
        F9._text(msp, f"{label} {'+' if v > 0 else ('-' if v < 0 else '%s' % chr(177))}{abs(v):.2f}", x0 + 12500, y)
    for name, y in names:
        F9._text(msp, name, x0 + 3000, y)


TOS_LEVELS = [("F.F.L.", 0.0), ("T.O.S.", -0.10), ("F.C.L.", 3.00), ("U/S SLAB", 3.10)]
FACADE_LEVELS = TOS_LEVELS + [("F.F.L.", 3.50)]
FACADE_NAMES = (("GROUND FLOOR", 1500), ("FIRST FLOOR", 5000))


def _box(msp, x0, y0, x1, y1, t, layer=W):
    """a closed box: outer x0..x1 / y0..y1 and, when t is given, the inner face offset t (drawing units); no gap."""
    sq = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    if t:
        sq += [((x0 + t, y0 + t), (x1 - t, y0 + t)), ((x1 - t, y0 + t), (x1 - t, y1 - t)),
               ((x1 - t, y1 - t), (x0 + t, y1 - t)), ((x0 + t, y1 - t), (x0 + t, y0 + t))]
    for a, b in sq:
        msp.add_line(a, b, dxfattribs={"layer": layer})


def masonry_room(path, section="TOS", partition=False, column=False, enclosure=False, annex=False):
    """column: a free-standing 0.30 m column (A-COL) inside the room (an island: never a facade); enclosure: a closed
    0.20 m wall box 2.00 m outside the room on the wall layer (a boundary wall around the building); annex: a closed
    2.00 x 2.00 m wall box (0.20 m) 3.00 m east of the room, raised 0.60 m so no face is collinear with the room's
    walls (a second outline on the floor; collinear faces with jambs at both ends would read as an opening)."""
    doc, msp = F6._doc()
    doc.layers.add("A-SECT")
    F9._walls_rect(msp, [(1000, 2000)], [(1250, 2750)])
    F6._door(msp, 1000, 2000)
    msp.add_line((1250, 3300), (2750, 3300), dxfattribs={"layer": GLAZ})
    if partition:
        F6._lines(msp, [((3000, 200), (3000, 3200)), ((3150, 200), (3150, 3200))])
    if column:
        _box(msp, 3300, 2400, 3600, 2700, None, layer=F6.COL)
    if enclosure:
        _box(msp, -2000, -2000, 6400, 5400, 200)
    if annex:
        _box(msp, 7400, 600, 9400, 2600, 200)
    F9._text(msp, "BEDROOM", 2000, 1700)
    F9._evidence(msp, frozenset({"TAGS", "SCHEDULE"}), ["D1", "W1"], {"D1": (1400, -500), "W1": (1900, 3700)},
                 (2000, 1700))
    if section == "TOS":
        _level_section(msp, 58000, "SECTION A-A", TOS_LEVELS)
    elif section == "BOB":
        _level_section(msp, 58000, "SECTION A-A", TOS_LEVELS + [("B.O.B.", 2.60)])
    elif section == "NO_TOS":
        _level_section(msp, 58000, "SECTION A-A", [x for x in TOS_LEVELS if x[0] != "T.O.S."])
    elif section == "TWO":
        _level_section(msp, 58000, "SECTION A-A", TOS_LEVELS)
        _level_section(msp, 90000, "SECTION B-B", [x if x[0] != "T.O.S." else ("T.O.S.", -0.15) for x in TOS_LEVELS])
    elif section == "FACADE":
        _level_section(msp, 58000, "SECTION A-A", FACADE_LEVELS, FACADE_NAMES)
    doc.saveas(str(path))
    return Path(path)
