"""Phase 2B-9 synthetic fixtures (no private drawing): the worked examples of the Phase 2B-9 instruction, drawn in
millimetres on the Phase 2B-6 layers (A-WALL / A-DOOR / A-GLAZ / A-COL), with the height evidence a real drawing set
carries (opening tags, a door / window schedule, a section, room and floor notes) on their own sheets. Every truth
in p2b9_truth.py is derived by hand from the coordinates below, never from the engine.

    example1(path, window="SILL" | "FLOOR", evidence=...)
        a 4.00 x 3.00 m BEDROOM (inner faces x 200..4200, y 200..3200; 0.20 m walls, outer 0..4400 x 0..3400);
        door D1 1.00 m in the south wall (jambs x 1000 / 2000, frame lines 50 mm in, a 0.90 m leaf);
        window in the north wall x 1250..2750 (1.50 m), its glazing line at y 3300 (mid-wall: 0.10 m inner reveal);
        window="SILL": W1 1.50 x 1.20 m, sill 1.00 m; window="FLOOR": W2 1.50 x 3.00 m, sill 0.00 (to the ceiling)
    example2(path, evidence=...)   a 4.00 x 3.00 m BATH (the Phase 2B-3 WP-B room), door D1 1.00 m at x 1700..2700
    example3(path, evidence=...)   a 4.00 x 3.00 m BEDROOM whose south wall is only short stubs: door D1 x 400..1400,
                                   window W3 x 1650..3950 (2.30 m): a 0.20 m return (x 200..400), a 0.25 m pier
                                   (x 1400..1650) and a 0.25 m return (x 3950..4200), each under the 0.30 m band rule
    example4(path, evidence=...)   a quarter-disc BEDROOM: straight walls along x and y (0.20 m), a 90-degree curved wall
                                   centred on the inner corner (200, 200), inner radius 3.00 m, outer 3.20 m; door D1
                                   1.00 m in the south wall (x 1200..2200)
evidence: a set of
    TAGS          the opening marks D1 / W1 / W2 / W3 drawn next to their openings (outside the room)
    SCHEDULE      a DOOR AND WINDOW SCHEDULE sheet (mark, width, height, sill in mm)
    SECTION       a SECTION A-A sheet: F.F.L. +-0.00, F.C.L. +3.00, U/S SLAB +3.00 on the GROUND FLOOR band
    ROOM_NOTE     a ceiling-height note inside the room (C.H. 3.00, or example1's room_note) - room-scoped
    FLOOR_NOTE    a general note on the plan sheet (ALL WINDOW SILLS 1.00 M, CEILING HEIGHT 3.00 M)
    SILL_TAG      the element annotation SILL 0.90 next to W1 (contradicts the schedule's 1.00: the element wins)
    SECTION2      a second section that gives F.C.L. +2.80 for the same floor (a same-rank conflict with SECTION)
    SECTION_FF    a section with only F.F.L. +-0.00 (GROUND FLOOR) and F.F.L. +3.60 (FIRST FLOOR): floor-to-floor only
example1(..., rows={mark: (w, h, sill)}) overrides schedule rows (a row whose width is not the window's).
Every plan has the sheet frame and title the admission needs."""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "m9_p2b6"))
sys.path.insert(0, str(HERE.parents[1]))

import p2b6_fixtures as F6                                    # noqa: E402

W, DOOR, GLAZ, COL = F6.W, F6.DOOR, F6.GLAZ, F6.COL
ROLES = F6.ROLES
variant = F6.variant
TXT = "A-TEXT"
FULL = frozenset({"TAGS", "SCHEDULE", "SECTION"})

# the schedule rows of the examples: mark -> (width mm, height mm, sill mm or None)
SCHEDULE_ROWS = {"D1": (1000, 2200, None), "W1": (1500, 1200, 1000), "W2": (1500, 3000, 0), "W3": (2300, 1200, 1000)}


def _frame(msp, x0, x1, title, y0=-8000, y1=18000):
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": "A-FRAME"})
    msp.add_text(title, dxfattribs={"layer": "A-TITLE", "height": 500}).set_placement((x0 + 2000, y0 + 1500))


def _text(msp, s, x, y, h=200, layer=TXT):
    msp.add_text(s, dxfattribs={"layer": layer, "height": h}).set_placement((x, y))


def _schedule(msp, marks, rows=None):
    """the DOOR AND WINDOW SCHEDULE sheet (x 26000 .. 56000): a header row and one row per mark, values in mm
    (rows: {mark: (w, h, sill)} overriding SCHEDULE_ROWS)."""
    _frame(msp, 26000, 56000, "DOOR AND WINDOW SCHEDULE")
    cols = (28000, 32000, 37000, 42000)
    _text(msp, "DOOR AND WINDOW SCHEDULE", 28000, 15000, 300)
    for x, h in zip(cols, ("MARK", "WIDTH (mm)", "HEIGHT (mm)", "SILL (mm)")):
        _text(msp, h, x, 14000)
    for i, m in enumerate(marks):
        w, h, s = (rows or {}).get(m) or SCHEDULE_ROWS[m]
        y = 13200 - 800 * i
        for x, v in zip(cols, (m, str(w), str(h), "-" if s is None else str(s))):
            _text(msp, v, x, y)


def _section(msp, x0=58000, fcl="+3.00", title="SECTION A-A"):
    """a section sheet: the floor and ceiling lines of the GROUND FLOOR, their level texts (y = level x 1000)."""
    _frame(msp, x0, x0 + 30000, title)
    fc = float(fcl) * 1000
    msp.add_line((x0 + 2000, 0), (x0 + 12000, 0), dxfattribs={"layer": "A-SECT"})
    msp.add_line((x0 + 2000, fc), (x0 + 12000, fc), dxfattribs={"layer": "A-SECT"})
    _text(msp, "F.F.L. %s0.00" % "±", x0 + 12500, 0)
    _text(msp, f"F.C.L. {fcl}", x0 + 12500, fc)
    _text(msp, "U/S SLAB +3.00", x0 + 16000, 3000)
    _text(msp, "GROUND FLOOR", x0 + 3000, 1500)


def _section_ff(msp, x0=58000):
    """a section showing only the finished floor levels of the GROUND and FIRST floors (no ceiling, no soffit): a
    floor-to-floor interval of 3.60 m and nothing else."""
    _frame(msp, x0, x0 + 30000, "SECTION C-C")
    for v, lv, name in ((0.0, "F.F.L. %s0.00" % "±", "GROUND FLOOR"), (3.6, "F.F.L. +3.60", "FIRST FLOOR")):
        y = v * 1000
        msp.add_line((x0 + 2000, y), (x0 + 12000, y), dxfattribs={"layer": "A-SECT"})
        _text(msp, lv, x0 + 12500, y)
        _text(msp, name, x0 + 3000, y + 1500)


def _walls_rect(msp, south_gaps, north_gaps):
    """the 4.40 x 3.40 m outer box with 0.20 m walls; gaps [(x0, x1)] in the south (y 0..200) and north
    (y 3200..3400) walls, each closed by jamb lines across the wall."""
    def side(y_out, y_in, gaps, x_out=(0, 4400), x_in=(200, 4200)):
        xs_o, xs_i = [x_out[0]], [x_in[0]]
        for g0, g1 in gaps:
            xs_o += [g0, g1]
            xs_i += [g0, g1]
            F6._lines(msp, [((g0, y_out), (g0, y_in)), ((g1, y_out), (g1, y_in))])
        xs_o.append(x_out[1])
        xs_i.append(x_in[1])
        for k in range(0, len(xs_o), 2):
            F6._lines(msp, [((xs_o[k], y_out), (xs_o[k + 1], y_out)), ((xs_i[k], y_in), (xs_i[k + 1], y_in))])
    side(0, 200, south_gaps)
    side(3400, 3200, north_gaps)
    F6._lines(msp, [((0, 0), (0, 3400)), ((200, 200), (200, 3200)), ((4400, 0), (4400, 3400)),
                    ((4200, 200), (4200, 3200))])


def _evidence(msp, evidence, marks, tag_at, room_pt, room_note="C.H. 3.00", rows=None):
    if "TAGS" in evidence:
        for m, (x, y) in tag_at.items():
            _text(msp, m, x, y)
    if "SCHEDULE" in evidence:
        _schedule(msp, marks, rows)
    if "SECTION" in evidence:
        _section(msp)
    if "SECTION_FF" in evidence:
        _section_ff(msp)
    if "SECTION2" in evidence:
        _section(msp, x0=90000, fcl="+2.80", title="SECTION B-B")
    if "ROOM_NOTE" in evidence:
        _text(msp, room_note, room_pt[0], room_pt[1] - 400, 150)
    if "FLOOR_NOTE" in evidence:
        _text(msp, "NOTES: ALL WINDOW SILLS 1.00 M. CEILING HEIGHT 3.00 M UNLESS NOTED", 0, -3000, 200)
    if "SILL_TAG" in evidence:
        _text(msp, "SILL 0.90", tag_at["W1"][0], tag_at["W1"][1] + 300, 150)


def example1(path, window="SILL", evidence=FULL, room_note="C.H. 3.00", rows=None):
    doc, msp = F6._doc()
    doc.layers.add("A-SECT")
    _walls_rect(msp, [(1000, 2000)], [(1250, 2750)])
    F6._door(msp, 1000, 2000)
    msp.add_line((1250, 3300), (2750, 3300), dxfattribs={"layer": GLAZ})
    _text(msp, "BEDROOM", 2000, 1700)
    wm = "W1" if window == "SILL" else "W2"
    _evidence(msp, evidence, ["D1", wm], {"D1": (1400, -500), wm: (1900, 3700)}, (2000, 1700), room_note, rows)
    doc.saveas(str(path))
    return Path(path)


def example2(path, evidence=FULL):
    doc, msp = F6._doc()
    doc.layers.add("A-SECT")
    _walls_rect(msp, [(1700, 2700)], [])
    F6._door(msp, 1700, 2700)
    _text(msp, "BATH", 1800, 1700)
    _evidence(msp, evidence, ["D1"], {"D1": (2100, -500)}, (1800, 1700))
    doc.saveas(str(path))
    return Path(path)


def example3(path, evidence=FULL):
    doc, msp = F6._doc()
    doc.layers.add("A-SECT")
    _walls_rect(msp, [(400, 1400), (1650, 3950)], [])
    F6._door(msp, 400, 1400)
    msp.add_line((1650, 100), (3950, 100), dxfattribs={"layer": GLAZ})
    _text(msp, "BEDROOM", 2000, 1700)
    _evidence(msp, evidence, ["D1", "W3"], {"D1": (800, -500), "W3": (2700, -500)}, (2000, 1700))
    doc.saveas(str(path))
    return Path(path)


def example3_returns(path, evidence=FULL):
    """the example-1 room without its window, the door D1 (x 1000..2000) in the south wall, and two return walls
    (0.20 m thick) standing into the room at the door's jambs: a 0.20 m return x 800..1000, y 200..400 and a 0.35 m
    return x 2000..2200, y 200..550. The jamb lines run on along the returns' door-side faces."""
    doc, msp = F6._doc()
    doc.layers.add("A-SECT")
    F6._lines(msp, [((0, 0), (1000, 0)), ((2000, 0), (4400, 0)),
                    ((200, 200), (800, 200)), ((2200, 200), (4200, 200)),
                    ((800, 200), (800, 400)), ((800, 400), (1000, 400)), ((1000, 0), (1000, 400)),
                    ((2000, 0), (2000, 550)), ((2000, 550), (2200, 550)), ((2200, 550), (2200, 200))])
    F6._lines(msp, [((0, 3400), (4400, 3400)), ((200, 3200), (4200, 3200))])
    F6._lines(msp, [((0, 0), (0, 3400)), ((200, 200), (200, 3200)), ((4400, 0), (4400, 3400)),
                    ((4200, 200), (4200, 3200))])
    F6._door(msp, 1000, 2000)
    _text(msp, "BEDROOM", 2600, 1700)
    _evidence(msp, evidence, ["D1"], {"D1": (1400, -500)}, (2600, 1700))
    doc.saveas(str(path))
    return Path(path)


STUB_DEG = math.degrees(0.20 / 3.0)                           # 3.819719 deg: a 0.20 m stub on the 3.00 m inner arc


def example4_curved_stub(path, evidence=FULL):
    """example 4 with a window W4 in the curved wall from STUB_DEG to 90 - STUB_DEG: a 0.20 m curved stub (on the
    inner face) at each end of the window, its jambs radial lines across the wall, its glazing an arc at r 3.10 m."""
    doc, msp = F6._doc()
    doc.layers.add("A-SECT")
    c = (200, 200)
    F6._lines(msp, [((0, 0), (1200, 0)), ((2200, 0), (3400, 0)), ((3400, 0), (3400, 200)),
                    ((200, 200), (1200, 200)), ((2200, 200), (3200, 200)),
                    ((1200, 0), (1200, 200)), ((2200, 0), (2200, 200)),
                    ((0, 0), (0, 3400)), ((0, 3400), (200, 3400)), ((200, 200), (200, 3200))])
    a, b = STUB_DEG, 90 - STUB_DEG
    for r in (3000, 3200):
        msp.add_arc(c, r, 0, a, dxfattribs={"layer": W})
        msp.add_arc(c, r, b, 90, dxfattribs={"layer": W})
    for d in (a, b):
        x0, y0, _, _ = _arc_pts(c, 3000, d, d)
        x1, y1, _, _ = _arc_pts(c, 3200, d, d)
        msp.add_line((x0, y0), (x1, y1), dxfattribs={"layer": W})
    msp.add_arc(c, 3100, a, b, dxfattribs={"layer": GLAZ})
    F6._door(msp, 1200, 2200)
    _text(msp, "BEDROOM", 1300, 1500)
    _evidence(msp, evidence, ["D1"], {"D1": (1600, -500)}, (1300, 1500))
    doc.saveas(str(path))
    return Path(path)


def _arc_pts(c, r, a0, a1):
    return c[0] + r * math.cos(math.radians(a0)), c[1] + r * math.sin(math.radians(a0)), \
        c[0] + r * math.cos(math.radians(a1)), c[1] + r * math.sin(math.radians(a1))


def example4(path, evidence=FULL):
    doc, msp = F6._doc()
    doc.layers.add("A-SECT")
    c = (200, 200)
    # the south wall (y 0..200) with the door gap x 1200..2200, ending under the curved wall at x 3400
    F6._lines(msp, [((0, 0), (1200, 0)), ((2200, 0), (3400, 0)), ((3400, 0), (3400, 200)),
                    ((200, 200), (1200, 200)), ((2200, 200), (3200, 200)),
                    ((1200, 0), (1200, 200)), ((2200, 0), (2200, 200)),
                    # the west wall (x 0..200), ending under the curved wall at y 3400
                    ((0, 0), (0, 3400)), ((0, 3400), (200, 3400)), ((200, 200), (200, 3200))])
    for r in (3000, 3200):                                     # the curved wall: inner and outer faces, 0..90 deg
        msp.add_arc(c, r, 0, 90, dxfattribs={"layer": W})
    F6._door(msp, 1200, 2200)
    _text(msp, "BEDROOM", 1300, 1500)
    _evidence(msp, evidence, ["D1"], {"D1": (1600, -500)}, (1300, 1500))
    doc.saveas(str(path))
    return Path(path)
