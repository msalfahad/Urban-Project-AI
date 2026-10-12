"""SYNTHETIC ARCHITECTURAL PLANS (M9 S2) - DXF plans whose every quantity is known by construction, for the regression
fixtures of the architectural route (ezdxf; synthetic geometry only - no client drawing, no product data).

    villa(path, *, dx=0.0, dy=0.0, mirror=False, quarter_turns=0)  -> {"path", "truth"}
    hatch_islands(path)                                             -> {"path", "truth"}

The villa has two plan sheets (GROUND FLOOR PLAN, FIRST FLOOR PLAN) in mm. Walls are the faces of the rooms and the
outer face of the exterior wall (double lines, 200 mm apart), cut at every opening and closed by jambs; doors are
INSERTs of one door block (a leaf + a 90-degree swing), one of them MIRRORED; windows are glazing lines inside their
wall gap; columns are solid-hatched 400 x 400 squares standing free inside rooms; a straight stair is drawn as tread
lines; room words (one Arabic) and level texts sit inside the rooms. `truth` is written by hand from the coordinates
below (rectangle and L areas, perimeters, door widths): it never comes from the engine.

Metamorphic variants move (dx, dy), mirror (x -> -x) or turn (90-degree steps) the plan CONTENTS inside fixed sheet
frames; the truth does not change.
"""

from __future__ import annotations

import math

T = 200.0                              # wall thickness (mm)

# ---- ground floor (mm): exterior outer face 0..12400 x 0..9400; room faces below
GF_ROOMS = {
    "LIVING": [(200, 200), (9200, 200), (9200, 4200), (6200, 4200), (6200, 9200), (200, 9200)],
    "BEDROOM": [(6400, 4400), (9200, 4400), (9200, 9200), (6400, 9200)],
    "BATH": [(9400, 200), (12200, 200), (12200, 2600), (9400, 2600)],
    "KITCHEN": [(9400, 2800), (12200, 2800), (12200, 9200), (9400, 9200)],
}
GF_OUTER = [(0, 0), (12400, 0), (12400, 9400), (0, 9400)]
GF_LABELS = {"LIVING": (3000, 3000), "BEDROOM": (7800, 8200), "BATH": (10800, 1800), "KITCHEN": (10800, 7000)}
GF_WORDS = {"LIVING": "LIVING", "BEDROOM": "غرفة نوم", "BATH": "BATH", "KITCHEN": "KITCHEN"}
# openings: (kind, axis, wall band low, wall band high, s0, s1, door insert or None)
#   axis "x": a vertical wall occupying x in [lo, hi], gap y in [s0, s1]; axis "y": a horizontal wall
#   door insert: (hinge x, hinge y, rotation deg, xscale sign, yscale sign) for a block whose leaf runs along +x and
#   whose swing closes at +y (90 degrees)
GF_OPENINGS = [
    ("DOOR", "x", 6200, 6400, 5000, 5900, (6400, 5000, 0, 1, 1)),           # LIVING | BEDROOM 0.90
    ("DOOR", "x", 9200, 9400, 800, 1600, (9400, 800, 0, 1, 1)),             # LIVING | BATH 0.80
    ("DOOR", "x", 9200, 9400, 3100, 4000, (9400, 4000, 0, 1, -1)),          # LIVING | KITCHEN 0.90, MIRRORED insert
    ("DOOR", "y", 0, 200, 2000, 3000, (3000, 200, 90, 1, 1)),               # entrance into LIVING 1.00
    ("WINDOW", "x", 0, 200, 6000, 7500, None),                              # LIVING west 1.50
    ("WINDOW", "y", 9200, 9400, 7000, 8500, None),                          # BEDROOM north 1.50
    ("WINDOW", "x", 12200, 12400, 5000, 6500, None),                        # KITCHEN east 1.50
    ("WINDOW", "x", 12200, 12400, 1000, 1600, None),                        # BATH east 0.60
]
GF_COLUMNS = [(2000, 6000), (5000, 2000), (7600, 6600)]                     # lower-left corners, 400 x 400

# ---- first floor (mm): exterior 0..9400 x 0..8000
F1_ROOMS = {
    "MASTER": [(200, 200), (6200, 200), (6200, 5200), (200, 5200)],
    "STAIR": [(6400, 200), (9200, 200), (9200, 5200), (6400, 5200)],
    "BATH2": [(200, 5400), (3000, 5400), (3000, 7800), (200, 7800)],
    "LOBBY": [(3200, 5400), (9200, 5400), (9200, 7800), (3200, 7800)],
}
F1_OUTER = [(0, 0), (9400, 0), (9400, 8000), (0, 8000)]
F1_LABELS = {"MASTER": (3000, 2500), "STAIR": (7000, 4600), "BATH2": (1500, 6600), "LOBBY": (6000, 6800)}
F1_WORDS = {"MASTER": "MASTER BEDROOM", "STAIR": "STAIR", "BATH2": "BATH", "LOBBY": "LOBBY"}
F1_OPENINGS = [
    ("DOOR", "y", 5200, 5400, 4000, 4900, (4000, 5200, 270, 1, -1)),        # MASTER | LOBBY 0.90 (mirrored, turned)
    ("DOOR", "x", 3000, 3200, 6000, 6800, (3000, 6000, 180, 1, -1)),        # BATH2 | LOBBY 0.80 (mirrored, turned)
    ("PASSAGE", "y", 5200, 5400, 7000, 8000, None),                         # STAIR | LOBBY 1.00, no door
    ("WINDOW", "x", 0, 200, 2000, 3500, None),                              # MASTER west 1.50
    ("WINDOW", "y", 7800, 8000, 5000, 6500, None),                          # LOBBY north 1.50
    ("WINDOW", "x", 0, 200, 6400, 7000, None),                              # BATH2 west 0.60
]
F1_TREADS = [((7300, 1000 + 300 * i), (8300, 1000 + 300 * i)) for i in range(10)]   # 10 tread lines, going 0.30, 1.0 wide

# sheet frames (fixed; metamorphic moves only their contents) and the plan origin inside each frame
FRAMES = {"GF": ((-6000, -8000), (24000, 18000), (0, 0), "GROUND FLOOR PLAN"),
          "1F": ((34000, -8000), (64000, 18000), (40000, 0), "FIRST FLOOR PLAN")}


def _area(p):
    return abs(sum(p[i - 1][0] * p[i][1] - p[i][0] * p[i - 1][1] for i in range(len(p)))) / 2e6


def _per(p):
    return sum(math.dist(p[i - 1], p[i]) for i in range(len(p))) / 1e3


# ---- the truth, by hand (m, m2), independent of the engine
COL_A, COL_P = 0.16, 1.6                         # one 400 x 400 column: area, perimeter
TRUTH = {
    "GF": {
        "plate_m2": 12.4 * 9.4,
        "rooms": {
            # L-shape: 9.0 x 4.0 + 6.0 x 5.0 = 66.0 gross; two columns inside
            "LIVING": {"kind": "DRY", "gross_m2": 66.0, "net_m2": 66.0 - 2 * COL_A, "boundary_lm": 36.0 + 2 * COL_P,
                       "doors_lm": 0.9 + 0.8 + 0.9 + 1.0, "passages_lm": 0.0, "sill_windows_lm": 1.5, "holes": 2},
            "BEDROOM": {"kind": "DRY", "gross_m2": 2.8 * 4.8, "net_m2": 2.8 * 4.8 - COL_A, "boundary_lm": 15.2 + COL_P,
                        "doors_lm": 0.9, "passages_lm": 0.0, "sill_windows_lm": 1.5, "holes": 1},
            "BATH": {"kind": "WET", "gross_m2": 2.8 * 2.4, "net_m2": 2.8 * 2.4, "boundary_lm": 10.4, "doors_lm": 0.8,
                     "passages_lm": 0.0, "sill_windows_lm": 0.6, "holes": 0, "doorways": [(0.8, 0.2)]},
            "KITCHEN": {"kind": "DRY", "gross_m2": 2.8 * 6.4, "net_m2": 2.8 * 6.4, "boundary_lm": 18.4,
                        "doors_lm": 0.9, "passages_lm": 0.0, "sill_windows_lm": 1.5, "holes": 0},
        },
        "openings": {"DOOR": 4, "WINDOW": 4, "PASSAGE": 0},
        "door_widths_m": sorted([0.9, 0.8, 0.9, 1.0]),
    },
    "1F": {
        "plate_m2": 9.4 * 8.0,
        "rooms": {
            "MASTER_BEDROOM": {"kind": "DRY", "gross_m2": 30.0, "net_m2": 30.0, "boundary_lm": 22.0, "doors_lm": 0.9,
                               "passages_lm": 0.0, "sill_windows_lm": 1.5, "holes": 0},
            "STAIR": {"kind": "STAIR", "gross_m2": 14.0, "net_m2": 14.0, "boundary_lm": 15.6, "doors_lm": 0.0,
                      "passages_lm": 1.0, "sill_windows_lm": 0.0, "holes": 0},
            "BATHROOM": {"kind": "WET", "gross_m2": 6.72, "net_m2": 6.72, "boundary_lm": 10.4, "doors_lm": 0.8,
                         "passages_lm": 0.0, "sill_windows_lm": 0.6, "holes": 0, "doorways": [(0.8, 0.2)]},
            "CORRIDOR": {"kind": "CIRCULATION", "gross_m2": 14.4, "net_m2": 14.4, "boundary_lm": 16.8,
                         "doors_lm": 0.9 + 0.8, "passages_lm": 1.0, "sill_windows_lm": 1.5, "holes": 0},
        },
        "openings": {"DOOR": 2, "WINDOW": 3, "PASSAGE": 1},
        "door_widths_m": sorted([0.9, 0.8]),
        "stair": {"tread_lines": 10, "going_m": 0.30, "width_m": 1.0, "run_m": 2.7},
    },
    "levels": {"GF": 0.0, "1F": 3.5},
}
# the GF rooms keyed by the lexicon code the engine reads from the words
TRUTH["GF"]["rooms"] = {{"LIVING": "LIVING", "BEDROOM": "BEDROOM", "BATH": "BATHROOM", "KITCHEN": "KITCHEN"}[k]: v
                        for k, v in TRUTH["GF"]["rooms"].items()}
assert abs(_area(GF_ROOMS["LIVING"]) - 66.0) < 1e-9 and abs(_per(GF_ROOMS["LIVING"]) - 36.0) < 1e-9


def _xf(p, origin, dx, dy, mirror, quarter_turns, centre):
    x, y = p[0] - centre[0], p[1] - centre[1]
    if mirror:
        x = -x
    for _ in range(quarter_turns % 4):
        x, y = -y, x
    return (x + centre[0] + origin[0] + dx, y + centre[1] + origin[1] + dy)


def _cut(a, b, openings):
    """the face line a-b with every gap of an opening on it removed (axis-aligned faces)."""
    (x1, y1), (x2, y2) = a, b
    gaps = []
    for kind, axis, lo, hi, s0, s1, _ in openings:
        if axis == "x" and x1 == x2 and x1 in (lo, hi) and min(y1, y2) <= s0 and s1 <= max(y1, y2):
            gaps.append((s0, s1))
        if axis == "y" and y1 == y2 and y1 in (lo, hi) and min(x1, x2) <= s0 and s1 <= max(x1, x2):
            gaps.append((s0, s1))
    if not gaps:
        return [(a, b)]
    vert = x1 == x2
    t0, t1 = (min(y1, y2), max(y1, y2)) if vert else (min(x1, x2), max(x1, x2))
    pieces, pos = [], t0
    for s0, s1 in sorted(gaps):
        if s0 > pos:
            pieces.append((pos, s0))
        pos = max(pos, s1)
    if t1 > pos:
        pieces.append((pos, t1))
    return [(((x1, p), (x1, q)) if vert else ((p, y1), (q, y1))) for p, q in pieces]


def _plan(msp, *, rooms, outer, labels, words, openings, columns, level, treads, origin, dx, dy, mirror, quarter_turns,
          variant=None):
    xs, ys = [p[0] for p in outer], [p[1] for p in outer]
    centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    X = lambda p: _xf(p, origin, dx, dy, mirror, quarter_turns, centre)          # noqa: E731
    rot = (90 * quarter_turns) % 360

    def line(a, b, layer):
        msp.add_line(X(a), X(b), dxfattribs={"layer": layer})
    for poly in list(rooms.values()) + [outer]:
        for i in range(len(poly)):
            for a, b in _cut(poly[i], poly[(i + 1) % len(poly)], openings):
                line(a, b, "A-WALL")
    for kind, axis, lo, hi, s0, s1, door in openings:
        for s in (s0, s1):                                                     # jambs
            line((lo, s), (hi, s), "A-WALL") if axis == "x" else line((s, lo), (s, hi), "A-WALL")
        if kind == "WINDOW":
            for f in (1 / 3, 2 / 3):
                o = lo + (hi - lo) * f
                line((o, s0), (o, s1), "A-GLAZ") if axis == "x" else line((s0, o), (s1, o), "A-GLAZ")
        if door:
            hx, hy, r, sx, sy = door
            w = (s1 - s0) / 1000.0
            if mirror:
                sx, r = -sx, (180 - r) % 360                                     # x -> -x mirrors the insert
            if variant == "NESTED_MIRRORED_DOORS":
                # the door block mirrored inside a wrapper block that is mirrored back: the same WCS geometry
                msp.add_blockref("DOORWRAP", X((hx, hy)), dxfattribs={
                    "layer": "A-DOOR", "xscale": -sx * w, "yscale": sy * w, "rotation": (r + rot) % 360})
            else:
                msp.add_blockref("DOOR1000", X((hx, hy)), dxfattribs={
                    "layer": "A-DOOR", "xscale": sx * w, "yscale": sy * w, "rotation": (r + rot) % 360})
    for cx, cy in columns:
        sq = [X(p) for p in ((cx, cy), (cx + 400, cy), (cx + 400, cy + 400), (cx, cy + 400))]
        msp.add_lwpolyline(sq, close=True, dxfattribs={"layer": "A-COL"})
        h = msp.add_hatch(dxfattribs={"layer": "A-COL"})
        h.set_solid_fill()
        h.paths.add_polyline_path(sq, is_closed=True)
    for a, b in treads:
        line(a, b, "A-STAIR")
    for name, p in labels.items():
        word = words[name]
        if variant == "ATTRIB_LABELS":
            # the room word is the NAME attribute of a room-tag block (its block name is not a room word)
            msp.add_blockref("RTAG", X(p), dxfattribs={"layer": "A-TEXT"}).add_auto_attribs({"NAME": word})
        elif variant == "SHX_ARABIC" and word in SHX_KEYBOARD_WORDS:
            # the Arabic word typed on the Arabic (101) keyboard in an Arabic SHX font: the DXF holds Latin letters
            msp.add_text(SHX_KEYBOARD_WORDS[word], dxfattribs={"layer": "A-TEXT", "height": 200,
                                                               "style": "AR-SHX"}).set_placement(X(p))
        else:
            msp.add_text(word, dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement(X(p))
        msp.add_text(level, dxfattribs={"layer": "A-TEXT", "height": 150}).set_placement(X((p[0], p[1] - 500)))


# the Arabic room word typed on the Arabic (101) keyboard, by hand, letter by letter: ghain=y reh=v feh=t
# teh-marbuta=m (space) noon=k waw=, meem=l
SHX_KEYBOARD_WORDS = {"غرفة نوم": "yvtm k,l"}
VARIANTS = (None, "NESTED_MIRRORED_DOORS", "ATTRIB_LABELS", "SHX_ARABIC")


def villa(path, *, dx=0.0, dy=0.0, mirror=False, quarter_turns=0, variant=None):
    """variant (S3, the truth does not change): NESTED_MIRRORED_DOORS - every door is a mirrored door block inside a
    wrapper block inserted mirrored; ATTRIB_LABELS - the room words are ATTRIBs of a room-tag block; SHX_ARABIC - the
    Arabic room word is typed in an Arabic SHX keyboard font (xarb.shx)."""
    import ezdxf
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {VARIANTS}")
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    blk = doc.blocks.new("DOOR1000")
    blk.add_line((0, 0), (1000, 0), dxfattribs={"layer": "0"})               # the open leaf
    blk.add_arc((0, 0), 1000, 0, 90, dxfattribs={"layer": "0"})              # the swing, closing at +y
    wrap = doc.blocks.new("DOORWRAP")
    wrap.add_blockref("DOOR1000", (0, 0), dxfattribs={"layer": "0", "xscale": -1})
    tag = doc.blocks.new("RTAG")
    tag.add_attdef("NAME", (0, 0), dxfattribs={"height": 200, "layer": "0"})
    doc.styles.add("AR-SHX", font="xarb.shx")
    msp = doc.modelspace()
    for fl, ((x0, y0), (x1, y1), org, title) in FRAMES.items():
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": "A-FRAME"})
        msp.add_text(title, dxfattribs={"layer": "A-TITLE", "height": 500}).set_placement((x0 + 2000, y0 + 1500))
    common = {"dx": dx, "dy": dy, "mirror": mirror, "quarter_turns": quarter_turns, "variant": variant}
    _plan(msp, rooms=GF_ROOMS, outer=GF_OUTER, labels=GF_LABELS, words=GF_WORDS, openings=GF_OPENINGS,
          columns=GF_COLUMNS, level="+0.00", treads=(), origin=FRAMES["GF"][2], **common)
    _plan(msp, rooms=F1_ROOMS, outer=F1_OUTER, labels=F1_LABELS, words=F1_WORDS, openings=F1_OPENINGS, columns=(),
          level="+3.50", treads=F1_TREADS, origin=FRAMES["1F"][2], **common)
    doc.saveas(str(path))
    return {"path": str(path), "truth": TRUTH}


def hatch_islands(path):
    """a 4 x 3 m hatch with a 1 x 1 m island, a mirrored (extrusion 0,0,-1) 2 x 2 m hatch, and a block holding a
    1 x 2 m hatch inserted twice (once mirrored). Truth: areas 11.0, 4.0, 2.0, 2.0 m2 at their drawn places."""
    import ezdxf
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    h = msp.add_hatch(dxfattribs={"layer": "H-ISLAND"})
    h.set_solid_fill()
    h.paths.add_polyline_path([(0, 0), (4000, 0), (4000, 3000), (0, 3000)], is_closed=True)
    h.paths.add_polyline_path([(1000, 1000), (2000, 1000), (2000, 2000), (1000, 2000)], is_closed=True)
    m = msp.add_hatch(dxfattribs={"layer": "H-MIRROR", "extrusion": (0, 0, -1)})
    m.set_solid_fill()
    # OCS of extrusion (0,0,-1) maps x -> -x: this square is drawn at WCS x 10000..12000
    m.paths.add_polyline_path([(-10000, 0), (-12000, 0), (-12000, 2000), (-10000, 2000)], is_closed=True)
    b = doc.blocks.new("HB")
    hb = b.add_hatch(dxfattribs={"layer": "H-BLOCK"})
    hb.set_solid_fill()
    hb.paths.add_polyline_path([(0, 0), (1000, 0), (1000, 2000), (0, 2000)], is_closed=True)
    msp.add_blockref("HB", (20000, 0))
    msp.add_blockref("HB", (30000, 0), dxfattribs={"xscale": -1})
    doc.saveas(str(path))
    truth = [{"layer": "H-ISLAND", "area_m2": 11.0, "islands": 1, "box_mm": (0, 0, 4000, 3000)},
             {"layer": "H-MIRROR", "area_m2": 4.0, "islands": 0, "box_mm": (10000, 0, 12000, 2000)},
             {"layer": "H-BLOCK", "area_m2": 2.0, "islands": 0, "box_mm": (20000, 0, 21000, 2000)},
             {"layer": "H-BLOCK", "area_m2": 2.0, "islands": 0, "box_mm": (29000, 0, 30000, 2000)}]
    return {"path": str(path), "truth": truth}


# ---- M9 S3: stairs (straight, curved, a dog-leg drawn on one layer) on two plans, with a void at the curved stair
ST_ROOMS = {"LIVING": [(200, 200), (8200, 200), (8200, 6200), (200, 6200)],
            "STAIR": [(8400, 200), (14200, 200), (14200, 6200), (8400, 6200)]}
ST_OUTER = [(0, 0), (14400, 0), (14400, 6400), (0, 6400)]
ST_LABELS = {"LIVING": (2000, 5300), "STAIR": (13300, 5800)}
ST_WORDS = {"LIVING": "LIVING", "STAIR": "STAIR"}
ST_OPENINGS = [("PASSAGE", "x", 8200, 8400, 2000, 3200, None),                  # LIVING | STAIR 1.20, no door
               ("DOOR", "y", 0, 200, 1000, 2000, (2000, 200, 90, 1, 1))]         # entrance 1.00
ST_COLUMNS = [(1000, 4500), (6500, 4500), (7000, 800)]                          # 400 x 400, the grid of both plans
LIVING_FLIGHT = [((4000 + 300 * i, 1000), (4000 + 300 * i, 2200)) for i in range(6)]       # 6 lines, 1.2 wide
FAN_C, FAN_R0, FAN_R1, FAN_N, FAN_STEP = (11300, 3200), 500.0, 1700.0, 9, 15.0            # 9 radial lines, 15 deg
FAN = [((FAN_C[0] + FAN_R0 * math.cos(math.radians(FAN_STEP * k)), FAN_C[1] + FAN_R0 * math.sin(math.radians(FAN_STEP * k))),
        (FAN_C[0] + FAN_R1 * math.cos(math.radians(FAN_STEP * k)), FAN_C[1] + FAN_R1 * math.sin(math.radians(FAN_STEP * k))))
       for k in range(FAN_N)]
# two legs side by side on ONE layer, their lines interleaved 50 mm apart in the going direction
LEG_A = [((8700, 600 + 300 * k), (9700, 600 + 300 * k)) for k in range(7)]
LEG_B = [((9800, 650 + 300 * k), (10800, 650 + 300 * k)) for k in range(7)]
ST_FRAMES = {"GF": ((-6000, -8000), (24000, 18000), (0, 0), "GROUND FLOOR PLAN"),
             "1F": ((34000, -8000), (64000, 18000), (40000, 0), "FIRST FLOOR PLAN")}
_q = 0.5 * math.sin(math.radians(FAN_STEP)) * ((FAN_R1 / 1000) ** 2 - (FAN_R0 / 1000) ** 2)
ST_TRUTH = {
    # each tread its own polygon (hand-derived): the n lines of a flight bound n - 1 treads
    "living_flight": {"lines": 6, "tread_m2": 5 * 0.30 * 1.2, "step_lm": 5 * 1.2},
    "fan": {"lines": FAN_N, "tread_m2": (FAN_N - 1) * _q, "step_lm": (FAN_N - 1) * (FAN_R1 - FAN_R0) / 1000,
            "sweep_deg": (FAN_N - 1) * FAN_STEP},
    "leg": {"lines": 7, "tread_m2": 6 * 0.30 * 1.0, "step_lm": 6 * 1.0},
    "living_gross_m2": 48.0, "living_floor_m2": 48.0 - 3 * COL_A - 5 * 0.30 * 1.2,    # columns + the drawn treads out
    "stair_room_m2": 5.8 * 6.0,
}


def stairs(path):
    """two plans (GROUND / FIRST FLOOR) of a living room and a stair room on one column grid. GF: a straight flight
    stands in the living room (its treads leave the porcelain), and the stair room holds a curved fan and a dog-leg
    whose two legs are drawn on one layer. 1F: the same stair room, with a VOID word at the fan (the fan is the GF stair
    seen through the void: counted once) and the dog-leg legs repeated (a stacked flight: counted, flagged)."""
    import ezdxf
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    blk = doc.blocks.new("DOOR1000")
    blk.add_line((0, 0), (1000, 0), dxfattribs={"layer": "0"})
    blk.add_arc((0, 0), 1000, 0, 90, dxfattribs={"layer": "0"})
    msp = doc.modelspace()
    for fl, ((x0, y0), (x1, y1), org, title) in ST_FRAMES.items():
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": "A-FRAME"})
        msp.add_text(title, dxfattribs={"layer": "A-TITLE", "height": 500}).set_placement((x0 + 2000, y0 + 1500))
        treads = (LIVING_FLIGHT if fl == "GF" else []) + FAN + LEG_A + LEG_B
        _plan(msp, rooms=ST_ROOMS, outer=ST_OUTER, labels=ST_LABELS, words=ST_WORDS, openings=ST_OPENINGS,
              columns=ST_COLUMNS, level="+0.00" if fl == "GF" else "+3.50", treads=treads, origin=org, dx=0.0, dy=0.0,
              mirror=False, quarter_turns=0)
        if fl == "1F":
            msp.add_text("VOID", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((org[0] + 11300, 4000))
    doc.saveas(str(path))
    return {"path": str(path), "truth": ST_TRUTH}


def entities(path):
    """one drawing of the entity kinds the readers must normalise, with analytic truth (mm):
    ELLIPSE 2000 x 1000 (full) | an ARC r 1000 / 90 deg in a block inserted at x-scale 2 (an elliptical quarter) |
    SPLINE through 4 points | a closed 2D POLYLINE 3000 x 2000 | an MLINE 4000 + 3000 at scale 200 | a 2 x 3 MINSERT of a
    400 x 400 column block at 2000 / 3000 spacing | a block with an ATTDEF inserted with its ATTRIB | an MTEXT."""
    import ezdxf
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    msp.add_ellipse((0, 0), major_axis=(2000, 0), ratio=0.5, dxfattribs={"layer": "E"})
    msp.add_spline([(0, 10000), (1000, 11000), (2000, 10000), (3000, 11000)], dxfattribs={"layer": "S"})
    msp.add_polyline2d([(0, 5000), (3000, 5000), (3000, 7000), (0, 7000)], close=True, dxfattribs={"layer": "P"})
    m = msp.add_mline([(10000, 0), (14000, 0), (14000, 3000)], dxfattribs={"layer": "M"})
    m.dxf.scale_factor = 200
    col = doc.blocks.new("COL")
    col.add_lwpolyline([(0, 0), (400, 0), (400, 400), (0, 400)], close=True)
    mi = msp.add_blockref("COL", (20000, 0), dxfattribs={"layer": "C"})
    mi.grid(size=(2, 3), spacing=(2000, 3000))
    arc = doc.blocks.new("ARCB")
    arc.add_arc((0, 0), 1000, 0, 90)
    msp.add_blockref("ARCB", (30000, 0), dxfattribs={"xscale": 2, "yscale": 1, "layer": "A"})
    tag = doc.blocks.new("TAG")
    tag.add_attdef("NAME", (0, 0), dxfattribs={"height": 200})
    msp.add_blockref("TAG", (40000, 0), dxfattribs={"layer": "T"}).add_auto_attribs({"NAME": "KITCHEN"})
    msp.add_mtext("BATH", dxfattribs={"layer": "T", "char_height": 200}).set_location((40000, 2000))
    doc.saveas(str(path))
    return {"path": str(path), "truth": {
        "ellipse_full_mm": math.pi * (3 * (2000 + 1000) - math.sqrt((3 * 2000 + 1000) * (2000 + 3 * 1000))),  # Ramanujan
        "stretched_quarter": {"a": 2000, "b": 1000},
        "polyline_perimeter_mm": 10000.0, "minsert_columns": 6, "attrib": "KITCHEN", "mtext": "BATH"}}
