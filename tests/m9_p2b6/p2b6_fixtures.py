"""Phase 2B-6 synthetic fixtures (no private drawing): small plans in millimetres with hand-derived truth.

    door_plan(path, variant)   a 4.00 x 3.00 m interior, 0.20 m walls (layers A-WALL / A-DOOR / A-GLAZ / A-COL),
                               a door whose symbol (jamb lines, 50 mm frame lines, leaf, 90-degree swing) is drawn
                               exploded on A-DOOR. Variants (TRUTH below):
        PLAIN       the wall gap is the door's own 0.80 m
        CROSSING    the wall gap is 1.027 m: the 0.80 m door, a 77 mm return and a 150 mm partition crossing the wall
                    (the reference plan's pattern of D-V26-06); rooms BATH (west) and BEDROOM (east)
        OPEN_SIDE   the same 1.027 m gap, its east part open on both faces
        COLUMN      the same gap with a 150 mm column standing in it
        DOUBLE      a 1.60 m pair of 0.75 m leaves, no jamb lines between them
    lookalike(path, kind)      the PLAIN plan (room BEDROOM) plus one object that looks like a role but is not:
        WARDROBE    a 0.60 m wardrobe leaf and swing on A-FURN, hinged 50 mm off a wall face
        DRAIN       a hatched 0.15 m floor-drain square on P-DRAIN, free in the room
        THREE_DRAINS three hatched 0.15 m drain squares (closed polylines) on P-DRAIN
        THRESHOLD   the doorway's marble threshold drawn as one line across the door gap on A-THR
        COLUMN      a TRUE column: a hatched 0.30 m square of four LINEs on S-COL against the south wall
    basin_plan(path)           a W.C. (room word) and, through a 0.80 m door, an unlabelled lobby holding a WASH
                               basin block; the lobby opens to the outside through a 1.00 m door
    variant(src, dst, kind)    the plan moved inside its axis-aligned sheet frame: rot30 / rot90 / mirror (each
                               frame's contents about their own centre), rot37_metres (a 4.40 x 3.40 m plan turned about
                               its centre, then metres), translate, metres, reorder, nest (the whole plan inside two
                               levels of blocks)
Every plan has the sheet frame and title the admission needs (tools/arch_synth.FRAMES["GF"])."""

from __future__ import annotations

import math

W, DOOR, GLAZ, COL = "A-WALL", "A-DOOR", "A-GLAZ", "A-COL"
SHEET = ("A-FRAME", "A-TITLE")
ROLES = ("A-WALL=WALL", "A-COL=COLUMN", "A-GLAZ=WINDOW", "A-DOOR=DOOR")

# hand truth (m, m2): the door width, the doorway strip (width x 0.20 m wall), the BATH floor (None: no claim)
TRUTH = {
    "PLAIN": {"door_m": 0.80, "strip_m2": 0.16, "bath_m2": 12.0},
    "CROSSING": {"door_m": 0.80, "strip_m2": 0.16, "bath_m2": round((1.877 - 0.200) * 3.0, 6)},
    "OPEN_SIDE": {"door_m": 0.80, "strip_m2": None, "bath_m2": 12.0},
    "COLUMN": {"door_m": 0.80, "strip_m2": None, "bath_m2": None},
    "DOUBLE": {"door_m": 1.60, "strip_m2": 0.32, "bath_m2": 12.0},
}


def _doc():
    import ezdxf
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    for name in (W, DOOR, GLAZ, COL, "A-TEXT", "A-FURN", "P-DRAIN", "A-THR", "S-COL") + SHEET:
        doc.layers.add(name)
    msp.add_lwpolyline([(-6000, -8000), (24000, -8000), (24000, 18000), (-6000, 18000)], close=True,
                       dxfattribs={"layer": "A-FRAME"})
    msp.add_text("GROUND FLOOR PLAN", dxfattribs={"layer": "A-TITLE", "height": 500}).set_placement((-4000, -6500))
    return doc, msp


def _lines(msp, segs, layer=W):
    for a, b in segs:
        msp.add_line(a, b, dxfattribs={"layer": layer})


def _door(msp, x0, x1, hinge_right=True):
    """a single door between x0 and x1 in the south wall (y 0..200): jamb lines across the wall, frame lines 50 mm
    in, the leaf (open, up into the room) and its 90-degree swing."""
    for x in (x0, x1, x0 + 50, x1 - 50):
        msp.add_line((x, 0), (x, 200), dxfattribs={"layer": DOOR})
    leaf = x1 - x0 - 100
    h = (x1 - 50, 200) if hinge_right else (x0 + 50, 200)
    msp.add_line(h, (h[0], 200 + leaf), dxfattribs={"layer": DOOR})
    msp.add_arc(h, leaf, 90 if hinge_right else 0, 180 if hinge_right else 90, dxfattribs={"layer": DOOR})


def _shell(msp):
    """the north, east and west walls (outer 0..4400 x 0..3400, inner 200..4200 x 200..3200) and a 0.60 m window in
    the east wall."""
    _lines(msp, [((4400, 0), (4400, 1000)), ((4400, 1600), (4400, 3400)), ((4400, 3400), (0, 3400)), ((0, 3400), (0, 0)),
                 ((4200, 200), (4200, 1000)), ((4200, 1600), (4200, 3200)), ((4200, 3200), (200, 3200)),
                 ((200, 3200), (200, 200)), ((4200, 1000), (4400, 1000)), ((4200, 1600), (4400, 1600))])
    msp.add_line((4300, 1000), (4300, 1600), dxfattribs={"layer": GLAZ})


def _south_plain(msp, g0=1000, g1=1800):
    _lines(msp, [((0, 0), (g0, 0)), ((200, 200), (g0, 200)), ((g0, 0), (g0, 200)),
                 ((g1, 0), (4400, 0)), ((g1, 200), (4200, 200)), ((g1, 0), (g1, 200))])


def door_plan(path, variant):
    doc, msp = _doc()
    _shell(msp)
    if variant in ("CROSSING", "OPEN_SIDE", "COLUMN"):
        g0, g1 = 1000, 2027
        _lines(msp, [((0, 0), (g0, 0)), ((200, 200), (g0, 200)), ((g0, 0), (g0, 200)),
                     ((g1, 0), (4400, 0)), ((g1, 200), (4200, 200))])
        if variant == "CROSSING":
            _lines(msp, [((1800, 0), (1877, 0)), ((1800, 200), (1877, 200)),
                         ((1877, 200), (1877, 3200)), ((2027, 200), (2027, 3200)),
                         ((1877, 0), (1877, -2450)), ((2027, 0), (2027, -2450)), ((1877, -2450), (2027, -2450))])
        elif variant == "OPEN_SIDE":
            _lines(msp, [((g1, 0), (g1, 200))])
        else:
            _lines(msp, [((g1, 0), (g1, 200))])
            _lines(msp, [((1850, 25), (2000, 25)), ((2000, 25), (2000, 175)), ((2000, 175), (1850, 175)),
                         ((1850, 175), (1850, 25))], COL)
        _door(msp, 1000, 1800)
    elif variant == "DOUBLE":
        _south_plain(msp, 1000, 2600)
        for x in (1000, 2600):
            msp.add_line((x, 0), (x, 200), dxfattribs={"layer": DOOR})
        for h, a0 in (((1050, 200), 0), ((2550, 200), 90)):
            msp.add_line(h, (h[0], 950), dxfattribs={"layer": DOOR})
            msp.add_arc(h, 750, a0, a0 + 90, dxfattribs={"layer": DOOR})
    elif variant == "PLAIN":
        _south_plain(msp)
        _door(msp, 1000, 1800)
    else:
        raise ValueError(variant)
    if variant == "CROSSING":
        msp.add_text("BATH", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((900, 1700))
        msp.add_text("BEDROOM", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((2900, 1700))
    else:
        msp.add_text("BATH", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((2000, 1700))
    doc.saveas(str(path))
    return path


def lookalike(path, kind):
    doc, msp = _doc()
    _shell(msp)
    _south_plain(msp)
    _door(msp, 1000, 1800)
    msp.add_text("BEDROOM", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((2000, 1700))
    if kind == "WARDROBE":
        h = (4150, 2400)
        msp.add_line(h, (h[0] - 600, h[1]), dxfattribs={"layer": "A-FURN"})
        msp.add_arc(h, 600, 180, 270, dxfattribs={"layer": "A-FURN"})
    elif kind in ("DRAIN", "COLUMN"):
        side, (x0, y0), lay = (150, (2500, 1200), "P-DRAIN") if kind == "DRAIN" else (300, (3500, 200), "S-COL")
        sq = [(x0, y0), (x0 + side, y0), (x0 + side, y0 + side), (x0, y0 + side)]
        _lines(msp, list(zip(sq, sq[1:] + sq[:1])), lay)
        msp.add_hatch(dxfattribs={"layer": lay}).paths.add_polyline_path(sq, is_closed=True)
    elif kind == "THREE_DRAINS":
        for x0, y0 in ((1500, 1000), (2500, 1000), (3200, 2400)):
            sq = [(x0, y0), (x0 + 150, y0), (x0 + 150, y0 + 150), (x0, y0 + 150)]
            msp.add_lwpolyline(sq, close=True, dxfattribs={"layer": "P-DRAIN"})
            msp.add_hatch(dxfattribs={"layer": "P-DRAIN"}).paths.add_polyline_path(sq, is_closed=True)
    elif kind == "THRESHOLD":
        _lines(msp, [((1000, 100), (1800, 100))], "A-THR")
    else:
        raise ValueError(kind)
    doc.saveas(str(path))
    return path


def basin_plan(path):
    """W.C. 2.00 x 1.80 m (x 200..2200, y 200..2000) and lobby 2.00 x 1.80 m (x 2400..4400) side by side, 0.20 m walls;
    a 0.80 m door W.C. -> lobby in the 0.20 m partition, a 1.00 m door lobby -> outside in the lobby's south wall;
    the room word W.C. in the first, a WASH block (a basin) and no word in the second."""
    doc, msp = _doc()
    blk = doc.blocks.new("WASH")
    blk.add_lwpolyline([(0, 0), (500, 0), (500, 400), (0, 400)], close=True, dxfattribs={"layer": "0"})
    blk.add_circle((250, 220), 150, dxfattribs={"layer": "0"})
    # outer 0..4600 x 0..2200; inner faces: W.C. 200..2200, lobby 2400..4400, y 200..2000
    _lines(msp, [((0, 0), (0, 2200)), ((0, 2200), (4600, 2200)), ((4600, 2200), (4600, 0)),
                 ((200, 200), (200, 2000)), ((200, 2000), (2200, 2000)), ((2400, 2000), (4400, 2000)),
                 ((4400, 2000), (4400, 200)),
                 ((0, 0), (2900, 0)), ((3900, 0), (4600, 0)),                         # south outer, gap 2900..3900
                 ((200, 200), (2200, 200)), ((2400, 200), (2900, 200)), ((3900, 200), (4400, 200)),
                 ((2900, 0), (2900, 200)), ((3900, 0), (3900, 200)),
                 ((2200, 200), (2200, 600)), ((2200, 1400), (2200, 2000)),            # partition, gap y 600..1400
                 ((2400, 200), (2400, 600)), ((2400, 1400), (2400, 2000)),
                 ((2200, 600), (2400, 600)), ((2200, 1400), (2400, 1400))])
    # the partition door (0.80 m between frame lines at 650 / 1350 - jamb to jamb 0.80 m: y 600..1400)
    for y in (600, 1400):
        msp.add_line((2200, y), (2400, y), dxfattribs={"layer": DOOR})
    msp.add_line((2400, 650), (3100, 650), dxfattribs={"layer": DOOR})
    msp.add_arc((2400, 650), 700, 0, 90, dxfattribs={"layer": DOOR})
    # the external door (1.00 m, y 0..200 at x 2900..3900)
    for x in (2900, 3900):
        msp.add_line((x, 0), (x, 200), dxfattribs={"layer": DOOR})
    msp.add_line((3850, 200), (3850, 1100), dxfattribs={"layer": DOOR})
    msp.add_arc((3850, 200), 900, 90, 180, dxfattribs={"layer": DOOR})
    msp.add_text("W.C.", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((900, 1100))
    msp.add_blockref("WASH", (3700, 1500), dxfattribs={"layer": "A-FURN"})
    doc.saveas(str(path))
    return path


def _ref(e):
    t = e.dxftype()
    if t == "LINE":
        return e.dxf.start
    if t in ("ARC", "CIRCLE"):
        return e.dxf.center
    if t in ("INSERT", "TEXT", "MTEXT"):
        return e.dxf.insert
    if t == "LWPOLYLINE":
        return list(e.get_points("xy"))[0]
    if t == "HATCH":
        p = e.paths[0]
        return p.vertices[0] if hasattr(p, "vertices") else p.edges[0].start
    return None


def variant(src, dst, kind):
    """the same drawing with its plan moved; the frame and title stay axis-aligned (a turned sheet frame is refused
    at admission: PLAN_TITLES_OUTSIDE_ANY_FRAME)."""
    import ezdxf
    from ezdxf.math import Matrix44
    doc = ezdxf.readfile(str(src))
    msp = doc.modelspace()
    if kind in ("rot30", "rot90", "mirror"):
        rot = {"rot30": Matrix44.z_rotate(math.radians(30)), "rot90": Matrix44.z_rotate(math.radians(90)),
               "mirror": Matrix44.scale(-1, 1, 1)}[kind]
        boxes = []
        for e in msp:
            if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "A-FRAME":
                f = [(p[0], p[1]) for p in e.get_points("xy")]
                boxes.append((min(x for x, _ in f), min(y for _, y in f), max(x for x, _ in f), max(y for _, y in f)))
        groups = {}
        for e in msp:
            if e.dxf.layer in SHEET:
                continue
            p = _ref(e)
            k = next((i for i, b in enumerate(boxes) if p is not None and b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]),
                     -1)
            groups.setdefault(k, []).append(e)
        for es in groups.values():
            ps = [_ref(e) for e in es if _ref(e) is not None]
            c = ((min(p[0] for p in ps) + max(p[0] for p in ps)) / 2, (min(p[1] for p in ps) + max(p[1] for p in ps)) / 2)
            m = Matrix44.chain(Matrix44.translate(-c[0], -c[1], 0), rot, Matrix44.translate(c[0], c[1], 0))
            for e in es:
                e.transform(m)
    elif kind == "rot37_metres":
        c = (2200.0, 1700.0)
        m = Matrix44.chain(Matrix44.translate(-c[0], -c[1], 0), Matrix44.z_rotate(math.radians(37)),
                           Matrix44.translate(c[0], c[1], 0))
        for e in msp:
            if e.dxf.layer not in SHEET:
                e.transform(m)
        for e in msp:
            e.transform(Matrix44.scale(0.001, 0.001, 0.001))
        doc.header["$INSUNITS"] = 6
    elif kind == "translate":
        for e in msp:
            e.transform(Matrix44.translate(1.0e6, -5.0e5, 0))
    elif kind == "metres":
        for e in msp:
            e.transform(Matrix44.scale(0.001, 0.001, 0.001))
        doc.header["$INSUNITS"] = 6
    elif kind == "reorder":
        ents = list(msp)
        for e in ents:
            msp.unlink_entity(e)
        for e in reversed(ents):
            msp.add_entity(e)
    elif kind == "nest":
        inner, outer = doc.blocks.new("PLAN_IN"), doc.blocks.new("PLAN_OUT")
        for e in list(msp):
            if e.dxf.layer in SHEET:
                continue
            inner.add_entity(e.copy())
            msp.delete_entity(e)
        outer.add_blockref("PLAN_IN", (0, 0), dxfattribs={"layer": "0"})
        msp.add_blockref("PLAN_OUT", (0, 0), dxfattribs={"layer": "0"})
    else:
        raise ValueError(kind)
    doc.saveas(str(dst))
    return dst
