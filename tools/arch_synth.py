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
                # x -> -x mirrors the insert: Mx R(r) S(sx, sy) = R(-r) S(-sx, sy) (P2B2: was 180 - r, which turned
                # every mirrored leaf half a turn about its hinge - closing outside its gap, swinging the other way)
                sx, r = -sx, (-r) % 360
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


# ---- M9 S4: physical vs functional floor - plan ENTITIES built directly (mm, no DXF read), with hand truth ----
S4_ROLES = {"A-WALL": "WALL", "A-DOOR": "DOOR", "A-GLAZ": "WINDOW", "A-COL": "COLUMN"}


def _s4_ents(rooms, outer, openings, *, texts=(), extra_segments=(), swings=(), columns=()):
    """walls from the room rectangles' faces and the outer outline (cut at every opening, jambs drawn), door swings
    as door-layer arcs with their leaf lines, extra segments (id, layer, a, b, path) as given."""
    segs, arcs = [], []

    def seg(a, b, layer, path=None, sid=None):
        segs.append({"id": sid or f"S{len(segs) + 1}", "layer": layer, "a": tuple(map(float, a)),
                     "b": tuple(map(float, b)), **({"path": [path]} if path else {})})
    for poly in list(rooms.values()) + [outer]:
        for i in range(len(poly)):
            for a, b in _cut(poly[i], poly[(i + 1) % len(poly)], openings):
                seg(a, b, "A-WALL")
    for kind, axis, lo, hi, s0, s1, _ in openings:
        if kind == "NO_JAMBS":
            continue
        for s in (s0, s1):
            seg((lo, s), (hi, s), "A-WALL") if axis == "x" else seg((s, lo), (s, hi), "A-WALL")
    for k, (hinge, r, a0, a1) in enumerate(swings, 1):
        occ = f"DOOR:{k}"
        c = tuple(map(float, hinge))
        s = (c[0] + r * math.cos(math.radians(a0)), c[1] + r * math.sin(math.radians(a0)))
        e = (c[0] + r * math.cos(math.radians(a1)), c[1] + r * math.sin(math.radians(a1)))
        arcs.append({"id": f"A{k}", "layer": "A-DOOR", "c": c, "r": float(r), "s": s, "e": e, "dir": "CCW",
                     "path": [occ]})
        seg(c, s, "A-DOOR", occ)                                       # the open leaf
    for k, (x, y) in enumerate(columns, 1):                            # one closed polyline per column
        for i, (a, b) in enumerate((((x, y), (x + 400, y)), ((x + 400, y), (x + 400, y + 400)),
                                    ((x + 400, y + 400), (x, y + 400)), ((x, y + 400), (x, y)))):
            seg(a, b, "A-COL", sid=f"COL{k}:{i}")
    for a, b, layer, path in extra_segments:
        seg(a, b, layer, path)
    tx = [{"id": f"T{k}", "x": float(p[0]), "y": float(p[1]), "value": v, "layer": "A-TEXT"}
          for k, (v, p) in enumerate(texts, 1)]
    return {"segments": segs, "arcs": arcs, "texts": tx, "inserts": [], "hatches": []}


S4_OUTER = [(0, 0), (10600, 0), (10600, 8600), (0, 8600)]
S4_ROOMS = {"MASTER": [(200, 200), (5200, 200), (5200, 4200), (200, 4200)],
            "KITCHEN": [(5400, 200), (9000, 200), (9000, 3000), (5400, 3000)],
            "LOBBY": [(5400, 3200), (9000, 3200), (9000, 4200), (5400, 4200)],
            "CORRIDOR": [(9200, 200), (10400, 200), (10400, 8400), (9200, 8400)],
            "VEST": [(200, 4400), (2200, 4400), (2200, 6200), (200, 6200)],
            "BATH": [(2400, 4400), (4400, 4400), (4400, 6200), (2400, 6200)],
            "BEDROOM": [(4600, 4400), (9000, 4400), (9000, 8400), (4600, 8400)],
            "CLOSET": [(2400, 6400), (4400, 6400), (4400, 8400), (2400, 8400)],
            "ACCESS": [(200, 6400), (2200, 6400), (2200, 8400), (200, 8400)]}
S4_OPENINGS = [
    ("PASSAGE", "y", 4200, 4400, 800, 2100, None),       # O1 MASTER | VEST archway 1.30, nothing drawn in it
    ("PASSAGE", "y", 3000, 3200, 6000, 7000, None),      # O2 KITCHEN | LOBBY 1.00, nothing drawn in it
    ("DOOR", "x", 9000, 9200, 3300, 4100, None),         # O3 LOBBY | CORRIDOR door 0.80
    ("DOOR", "x", 2200, 2400, 4500, 5300, None),         # O4 VEST | BATH door 0.80: its hinge stands 0.14 m from O1
    ("PASSAGE", "x", 4400, 4600, 7000, 8000, None),      # O5 CLOSET | BEDROOM 1.00 with an arch symbol block in it
    ("PASSAGE", "y", 6200, 6400, 500, 1500, None),       # O6 ACCESS | VEST 1.00 with four lines along it
    ("PASSAGE", "y", 6200, 6400, 2800, 3800, None)]      # O7 BATH | CLOSET 1.00, nothing drawn in it
S4_WORDS = (("MASTER BEDROOM", (2600, 2000)), ("KITCHEN", (7000, 1500)), ("CORRIDOR", (9800, 6000)),
            ("BATH", (3400, 5400)), ("BEDROOM", (6800, 6500)))
S4_SWINGS = (((9000, 3300), 800, 0, 90),                  # O3: leaf open along +x, closed along +y up the opening
             ((2200, 4500), 800, 0, 90))                  # O4
S4_MARKS = ((((4400, 7000), (4400, 8000)), "A-THIN", "ARCH:1"), (((4600, 7000), (4600, 8000)), "A-THIN", "ARCH:1"),
            (((500, 6200), (1500, 6200)), "A-THIN", None), (((500, 6250), (1500, 6250)), "A-THIN", None),
            (((500, 6350), (1500, 6350)), "A-THIN", None), (((500, 6400), (1500, 6400)), "A-THIN", None))
S4_TRUTH = {
    # hand-derived from the rectangles: a room takes in an unlabelled cell reached ONLY through a clear passage from it
    "MASTER_BEDROOM": 5.0 * 4.0 + 1.3 * 0.2 + 2.0 * 1.8,   # + the archway's doorway piece + the vestibule
    "KITCHEN": 3.6 * 2.8 + 1.0 * 0.2 + 3.6 * 1.0,          # + the passage piece + the lobby (up to the lobby door)
    "BATHROOM": 2.0 * 1.8,                                 # the closet behind O7 is larger than half the bath: apart
    "BEDROOM": 4.4 * 4.0,                                  # O5 holds an arch symbol: a drawn boundary
    "CORRIDOR": 1.2 * 8.2,
    "UNLABELLED": sorted([2.0 * 2.0, 2.0 * 2.0]),          # the closet (not attached) and the access (O6 marked)
    "attached_m2": {"MASTER_BEDROOM": 2.0 * 1.8, "KITCHEN": 3.6 * 1.0},
}


def s4_floor():
    """-> (ents, roles, truth) of the S4 physical / functional floor (one plan, mm)."""
    marks = [(a, b, layer, path) for (a, b), layer, path in S4_MARKS]
    ents = _s4_ents(S4_ROOMS, S4_OUTER, S4_OPENINGS, texts=S4_WORDS, swings=S4_SWINGS, extra_segments=marks)
    return ents, dict(S4_ROLES, **{"A-THIN": "OTHER"}), S4_TRUTH


S4W_THETA_DEG = 30.3                 # an island partition at an angle off the 0.5-degree band grid ...
S4W_STUB = ((1500.0, 1200.0), 1500.0, 150.0)   # ... from this point, 1.5 m long, 0.15 m thick, both ends left open


def s4_walls():
    """-> (ents, roles, truth): two rooms on one plan, mm.
    LIVING 4.0 x 2.8 holds a free-standing partition (two parallel wall lines at 30.3 degrees, ends not drawn): its body
    is wall, never floor (the caps must meet the drawn lines exactly). BATH 1.2 x 1.2 is entered by a door hung in a
    gap with no jamb lines and wall stubs too short for a wall band: the door closes on the bath face (its leaf) and
    the wall's other face closes the doorway piece (closure B), so neither room takes the 0.8 x 0.2 doorway piece."""
    t = math.radians(S4W_THETA_DEG)
    (x0, y0), L, w = S4W_STUB
    d, n = (math.cos(t), math.sin(t)), (-math.sin(t), math.cos(t))
    a1, b1 = (x0, y0), (x0 + L * d[0], y0 + L * d[1])
    a2, b2 = (x0 + w * n[0], y0 + w * n[1]), (x0 + L * d[0] + w * n[0], y0 + L * d[1] + w * n[1])
    rooms = {"LIVING": [(200, 200), (4200, 200), (4200, 3000), (200, 3000)],
             "BATH": [(1400, 3200), (2600, 3200), (2600, 4400), (1400, 4400)]}
    outer = [(0, 0), (4400, 0), (4400, 4600), (0, 4600)]
    # the wall between them (y 3000..3200): the LIVING face runs on except the door gap; the bath face is two stubs
    openings = [("NO_JAMBS", "y", 3000, 3200, 1600, 2400, None)]
    ents = _s4_ents(rooms, outer, openings, texts=(("LIVING", (800, 800)), ("BATH", (2000, 4000))),
                    swings=(((1600, 3200), 800, 270, 360),),
                    extra_segments=((a1, b1, "A-WALL", None), (a2, b2, "A-WALL", None),
                                    # the space between the bath and the outer wall is closed by these wall faces
                                    ((200, 3200), (1400, 3200), "A-WALL", None), ((2600, 3200), (4200, 3200), "A-WALL", None),
                                    ((200, 3200), (200, 4400), "A-WALL", None), ((4200, 3200), (4200, 4400), "A-WALL", None),
                                    ((200, 4400), (1400, 4400), "A-WALL", None), ((2600, 4400), (4200, 4400), "A-WALL", None)))
    truth = {"LIVING": 4.0 * 2.8 - L * w / 1e6, "BATH": 1.2 * 1.2, "doorway_m2": 0.8 * 0.2,
             "stub_m2": L * w / 1e6}
    return ents, S4_ROLES, truth


def _rot(p, c, deg):
    t = math.radians(deg)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(t) - y * math.sin(t), c[1] + x * math.sin(t) + y * math.cos(t))


S4V_ROOM = {"LIVING": [(200, 200), (8200, 200), (8200, 6200), (200, 6200)]}
S4V_OUTER = [(0, 0), (8400, 0), (8400, 6400), (0, 6400)]


def s4_voids():
    """-> {case: (ents, roles, truth)}, mm. One living room 8.0 x 6.0 per case:
    X_RECT_HAND_DRAWN  a VOID word inside a 4.0 x 3.0 rectangle marked by one full diagonal and a second line drawn
                       by hand from the third corner (3 degrees off the other diagonal, 60 % of its length): the void
                       is 12.0 m2 and leaves the floor finish
    SYMBOL_NO_WORD     a rectangle with all four sides and both diagonals but no VOID word: recorded, never deducted
    WORD_NO_OUTLINE    a VOID word and nothing around it: VOID_EXTENT_UNRESOLVED, nothing deducted"""
    P, Q, C = (3000, 2000), (7000, 5000), (7000, 2000)
    far = (3000, 5000)
    second = _rot((C[0] + 0.6 * (far[0] - C[0]), C[1] + 0.6 * (far[1] - C[1])), C, 3.0)
    out = {}
    words = (("LIVING", (1000, 1000)),)
    ents = _s4_ents(S4V_ROOM, S4V_OUTER, [], texts=words + (("VOID", (5000, 3600)),),
                    extra_segments=((P, Q, "A-THIN", None), (C, second, "A-THIN", None)))
    out["X_RECT_HAND_DRAWN"] = (ents, dict(S4_ROLES, **{"A-THIN": "OTHER"}),
                                {"void_m2": 4.0 * 3.0, "floor_m2": 8.0 * 6.0 - 4.0 * 3.0, "codes": ["LIVING"]})
    sq = [(3000, 2000), (7000, 2000), (7000, 5000), (3000, 5000)]
    sides = [(sq[i], sq[(i + 1) % 4], "A-THIN", None) for i in range(4)] + [(sq[0], sq[2], "A-THIN", None),
                                                                           (sq[1], sq[3], "A-THIN", None)]
    ents = _s4_ents(S4V_ROOM, S4V_OUTER, [], texts=words, extra_segments=sides)
    out["SYMBOL_NO_WORD"] = (ents, dict(S4_ROLES, **{"A-THIN": "OTHER"}),
                             {"void_m2": 0.0, "floor_m2": 48.0, "codes": ["LIVING"]})
    ents = _s4_ents(S4V_ROOM, S4V_OUTER, [], texts=words + (("VOID", (5000, 3600)),))
    out["WORD_NO_OUTLINE"] = (ents, dict(S4_ROLES, **{"A-THIN": "OTHER"}),
                              {"void_m2": 0.0, "floor_m2": None, "codes": ["LIVING", "VOID"]})
    return out


S4S_COLUMNS = [(600, 600), (4800, 600), (600, 5200), (4800, 5200)]      # inside the living room, 400 x 400


def s4_shaft_plans(offset=(40000.0, 0.0)):
    """-> [(floor, ents)] two plans of one storey stack, the upper drawn `offset` away, on one column grid: a LIVING
    5.8 x 6.0 (four 0.4 x 0.4 columns inside), a 1.8 x 1.8 doorless unlabelled space at the same place on both plans
    (a shaft) and a 1.8 x 1.8 STORE that has a door on the lower plan only (so it never stacks as a doorless
    footprint). Truth: the two 3.24 m2 faces at the shaft are SHAFT; the stores are not."""
    rooms = {"LIVING": [(200, 200), (6000, 200), (6000, 6200), (200, 6200)],
             "SHAFT": [(6200, 200), (8000, 200), (8000, 2000), (6200, 2000)],
             "STORE": [(6200, 2200), (8000, 2200), (8000, 4000), (6200, 4000)],
             "SPARE": [(6200, 4200), (8000, 4200), (8000, 6200), (6200, 6200)]}
    outer = [(0, 0), (8200, 0), (8200, 6400), (0, 6400)]
    plans = []
    for k, fl in enumerate(("GF", "1F")):
        dx, dy = offset[0] * k, offset[1] * k
        mv = {n: [(x + dx, y + dy) for x, y in p] for n, p in rooms.items()}
        ops = [("DOOR", "x", 6000 + dx, 6200 + dx, 2600 + dy, 3400 + dy, None)] if fl == "GF" else []
        sw = (((6200 + dx, 2600 + dy), 800, 0, 90),) if fl == "GF" else ()
        ents = _s4_ents(mv, [(x + dx, y + dy) for x, y in outer], ops,
                        texts=(("LIVING", (2000 + dx, 2000 + dy)), ("STORE", (7100 + dx, 5200 + dy))),
                        swings=sw, columns=[(x + dx, y + dy) for x, y in S4S_COLUMNS])
        plans.append((fl, ents))
    return plans


# S5 - an open space split only along lines DRAWN inside it (arch_rooms.zone_partition). One hall (inner face
# 11.8 x 7.8 m) holds LIVING and DINING words (dry), a GARDEN word in a strip closed by three drawn lines on a floor
# layer, and a wash corner (a basin block, no word) closed by two drawn lines. Things that must NOT split it: an
# X-marked rectangle round the DINING word (the slab opening above), a section-cut line running through the walls, a
# table drawn as a closed rectangle. A small word-less pocket touches both the garden and the hall: it stays
# unallocated (no nearest-label choice).
S5_OUTER = [(0, 0), (12200, 0), (12200, 8200), (0, 8200)]
S5_HALL = {"HALL": [(200, 200), (12000, 200), (12000, 8000), (200, 8000)]}
S5_WORDS = (("LIVING", (3000, 5000)), ("DINING", (8250, 5250)), ("GARDEN", (6000, 800)))
S5_LINES = (                                                        # (a, b, layer)
    ((4000, 1500), (9000, 1500), "A-FLOR"), ((4000, 200), (4000, 1500), "A-FLOR"),      # the garden strip
    ((9000, 200), (9000, 1500), "A-FLOR"),
    ((9000, 1500), (10500, 1500), "A-FLOR"), ((10500, 200), (10500, 1500), "A-FLOR"),  # the pocket beside it
    ((10000, 6000), (10000, 8000), "A-FLOR"), ((10000, 6000), (12000, 6000), "A-FLOR"),  # the wash corner
    ((7000, 4000), (9500, 4000), "A-FLOR"), ((9500, 4000), (9500, 6500), "A-FLOR"),      # X-marked rectangle
    ((9500, 6500), (7000, 6500), "A-FLOR"), ((7000, 6500), (7000, 4000), "A-FLOR"),
    ((7000, 4000), (9500, 6500), "A-FLOR"), ((9500, 4000), (7000, 6500), "A-FLOR"),
    ((5000, -2000), (5000, 10000), "A-SECT"),                                          # section cut (through walls)
    ((2000, 3000), (3000, 3000), "A-FURN"), ((3000, 3000), (3000, 4000), "A-FURN"),    # a table
    ((3000, 4000), (2000, 4000), "A-FURN"), ((2000, 4000), (2000, 3000), "A-FURN"))
S5_INSERTS = (("WASH", (11000, 7000)),)
S5_TRUTH = {
    "face_m2": 11.8 * 7.8,
    "GARDEN": 5.0 * 1.3,                      # EXTERNAL: no floor finish
    "WASH_CORNER": 2.0 * 2.0,                 # named from the basin (wet: wet-room tile + waterproofing, flagged)
    "POCKET": 1.5 * 1.3,                      # touches the garden and the hall: unallocated
    "OPEN_PLAN": 11.8 * 7.8 - 5.0 * 1.3 - 2.0 * 2.0 - 1.5 * 1.3,   # LIVING + DINING, one dry finish
}


def s5_zones(transform=None):
    """-> (ents, roles, truth) of the S5 drawn-line zones fixture; `transform` maps every point (metamorphic tests)."""
    T = transform or (lambda p: (float(p[0]), float(p[1])))
    ents = _s4_ents(S5_HALL, S5_OUTER, [], texts=S5_WORDS,
                    extra_segments=[(a, b, layer, None) for a, b, layer in S5_LINES])
    ents["inserts"] = [{"id": f"I:{k}", "name": n, "layer": "A-FIXT", "x": float(p[0]), "y": float(p[1]),
                        "box": None, "path": [], "depth": 0, "attribs": {}} for k, (n, p) in enumerate(S5_INSERTS, 1)]
    if transform:
        for s in ents["segments"]:
            s["a"], s["b"] = T(s["a"]), T(s["b"])
        for t in ents["texts"]:
            t["x"], t["y"] = T((t["x"], t["y"]))
        for i in ents["inserts"]:
            i["x"], i["y"] = T((i["x"], i["y"]))
    roles = dict(S4_ROLES, **{"A-FLOR": "OTHER", "A-SECT": "OTHER", "A-FURN": "OTHER", "A-TEXT": "OTHER"})
    return ents, roles, S5_TRUTH


# S5 - double height: the same 8 x 6 m room on two plans (four 0.4 m columns inside it, the column grid that aligns
# the plans); the upper plan marks a 2 x 3 m VOID (word inside an X-marked rectangle), the lower plan draws the same
# X-marked slab opening without the word. The upper plan is drawn 40 m to the right.
S5D_ROOM = {"LIVING": [(200, 200), (8200, 200), (8200, 6200), (200, 6200)]}
S5D_OUTER = [(0, 0), (8400, 0), (8400, 6400), (0, 6400)]
S5D_COLUMNS = [(600, 600), (7200, 600), (600, 5200), (7200, 5200)]
S5D_VOID = [(3000, 2000), (5000, 2000), (5000, 5000), (3000, 5000)]
S5D_TRUTH = {"room_m2": 8.0 * 6.0 - 4 * 0.4 * 0.4, "void_m2": 2.0 * 3.0}


def s5_double_height(dx=40000.0):
    """-> ((ents_lower, ents_upper), roles, truth)."""
    def plan(off, words):
        sh = lambda p: (p[0] + off, p[1])                                   # noqa: E731
        x = [((sh(S5D_VOID[i]), sh(S5D_VOID[(i + 1) % 4])), "A-FLOR") for i in range(4)] + \
            [((sh(S5D_VOID[0]), sh(S5D_VOID[2])), "A-FLOR"), ((sh(S5D_VOID[1]), sh(S5D_VOID[3])), "A-FLOR")]
        return _s4_ents({k: [sh(p) for p in v] for k, v in S5D_ROOM.items()}, [sh(p) for p in S5D_OUTER], [],
                        texts=[(w, sh(p)) for w, p in words], columns=[sh(c) for c in S5D_COLUMNS],
                        extra_segments=[(a, b, layer, None) for (a, b), layer in x])
    lower = plan(0.0, (("LIVING", (1500, 3000)),))
    upper = plan(dx, (("LIVING", (1500, 3000)), ("VOID", (4000, 3500))))
    return (lower, upper), dict(S4_ROLES, **{"A-FLOR": "OTHER", "A-TEXT": "OTHER"}), S5D_TRUTH


# S5 - two wet rooms sharing one door (0.80 m in a 0.20 m wall): ONE doorway piece (UP-WP-003)
S5W_ROOMS = {"BATH1": [(200, 200), (2200, 200), (2200, 2200), (200, 2200)],
             "BATH2": [(2400, 200), (4400, 200), (4400, 2200), (2400, 2200)]}
S5W_OUTER = [(0, 0), (4600, 0), (4600, 2400), (0, 2400)]
S5W_OPENINGS = [("DOOR", "x", 2200, 2400, 800, 1600, None)]
S5W_SWINGS = (((2400, 800), 800, 0, 90),)


def s5_wet_pair():
    ents = _s4_ents(S5W_ROOMS, S5W_OUTER, S5W_OPENINGS, texts=(("BATH", (1200, 1200)), ("W.C.", (3400, 1200))),
                    swings=S5W_SWINGS)
    return ents, dict(S4_ROLES), {"doorway_m2": 0.8 * 0.2, "room_m2": 2.0 * 2.0}
