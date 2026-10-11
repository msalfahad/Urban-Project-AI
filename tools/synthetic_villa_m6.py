"""SYNTHETIC VILLA M6 - completeness cases drawn onto the M2 synthetic villa, with the truth of what was drawn.

    python3 -I tools/synthetic_villa_m6.py OUT_DIR SEED [SEED ...] [--defects]

tools/synthetic_villa.py draws the frame of a villa (foundation plan, two roof-slab plans, schedules) and stays
unchanged. This generator re-opens that drawing and adds, from a separate random stream, the elements a takeoff
silently misses and the drafting that must NOT be reported:

ELEMENTS (each in the truth file with its sheet, its box in sheet-local metres and the finding kinds that detect it)
  PLANTED_COLUMN   a planted-column label on a beam of a roof-slab plan, in one of several spellings, sometimes with
                   the column's outline on the plan above
  BOUNDARY_WALL    a wall strip along one to three sides of the plot (the plot line drawn on every plan)
  POOL             a pool shell (outer and inner outline) in the plot margin
  LIFT_PIT         a lift pit (double-walled square) inside a foundation-plan bay
  WATER_TANK       a tank (double outline) on the top roof slab
  DOME             a dome ring (two circles) on the top roof slab, with or without ribs
  STAIR            a stair flight (outline and treads) in a ground-floor roof bay
  SUNKEN_SLAB      a sunken-slab outline inside a panel
  UNKNOWN_OUTLINE  a closed outline with no text on a numbered layer (an equipment base / planter)
  SCHEDULE_ORPHAN  a beam schedule row no plan uses
  SCHEDULE_UNREAD  a schedule row whose key is not a mark the reader knows ('B.W', 'R.W'), with its sizes
  LABEL_ORPHAN     a beam mark in a bay far from any beam, or a strap mark with no strap
  DEPENDENCY_NOTE  'as per arch' / 'see detail' beside a beam
  COLUMN_GAP       one column left off the ground-floor roof plan
  MISSING_STOREY   the first-floor roof plan left out of the set (its height and schedule bands remain)
  EXTRA_STOREY     the first-floor roof plan drawn again as a second-floor plan (no schedule band for it)
DISTRACTORS (must not become findings): level marks, section marks, a north arrow, a general-notes block naming
  families in prose, the plot line repeated on every plan.

Layer names, label spellings, note words (English / Arabic), sizes and positions vary by seed. The truth is the list
above as drawn; it never reads the engine. Synthetic drawings share the generator author's drafting assumptions:
they test that the detectors generalise across arrangements, names and sizes, not real-drawing accuracy.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import synthetic_villa as SV          # noqa: E402

LAYERS = {
    "BOUNDARY_WALL": ["S-BOUN", "BOUNDARY", "FENCE WALL", "S-FENCE", "8"],
    "POOL": ["S-POOL", "POOL", "SWIMMING POOL", "S-SPECIAL", "9"],
    "LIFT_PIT": ["S-LIFT", "LIFT", "S-SHAFT", "3"],
    "WATER_TANK": ["S-TANK", "TANK", "WATER-TANK", "4"],
    "DOME": ["S-DOME", "DOME", "6", "S-ROOF-DOME"],
    "STAIR": ["ST", "S-STAIR", "STAIRS", "5"],
    "SUNKEN_SLAB": ["S-SUNK", "SUNKEN", "S-SLAB-STEP", "12"],
    "UNKNOWN_OUTLINE": ["10", "11", "Layer1", "X-MISC"],
    "LEVEL": ["LEVEL", "S-LVL", "LEVELS"],
    "SECTION": ["S-SEC", "SECTION", "S-SECT-MARK"],
    "NORTH": ["N-ARROW", "NORTH", "S-SYMBOL"],
}
FAMILY = {"BOUNDARY_WALL": "BOUNDARY_WALL", "POOL": "POOL", "LIFT_PIT": "LIFT", "WATER_TANK": "WATER_TANK",
          "DOME": "DOMES", "STAIR": "STAIRS", "SUNKEN_SLAB": "SLAB_STEP", "UNKNOWN_OUTLINE": "UNKNOWN",
          "PLANTED_COLUMN": "PLANTED_COLUMN", "SCHEDULE_ORPHAN": "BEAMS", "LABEL_ORPHAN": "BEAMS",
          "DEPENDENCY_NOTE": None, "COLUMN_GAP": "COLUMNS", "MISSING_STOREY": None, "EXTRA_STOREY": "COLUMNS",
          "SCHEDULE_UNREAD": None}
EXPECT = {
    "BOUNDARY_WALL": ("DRAWN_NOT_MEASURED",), "POOL": ("DRAWN_NOT_MEASURED",), "LIFT_PIT": ("DRAWN_NOT_MEASURED",),
    "WATER_TANK": ("DRAWN_NOT_MEASURED",), "DOME": ("DRAWN_NOT_MEASURED",),
    "STAIR": ("STAIR_NOT_MEASURED", "DRAWN_NOT_MEASURED", "REGION_EXCLUDED"),
    "SUNKEN_SLAB": ("DRAWN_NOT_MEASURED", "OPENING_NOT_DEDUCTED"), "UNKNOWN_OUTLINE": ("DRAWN_NOT_MEASURED",),
    "PLANTED_COLUMN": ("LABEL_NOT_CONSUMED", "COLUMN_PRESENCE_NOT_ITEMIZED", "MEASURED"),
    "SCHEDULE_ORPHAN": ("SCHEDULED_NOT_PLACED",), "LABEL_ORPHAN": ("LABEL_NOT_CONSUMED", "PLACED_NOT_SCHEDULED"),
    "DEPENDENCY_NOTE": ("DEPENDENCY",), "COLUMN_GAP": ("COLUMN_BAND_NOT_ON_PLAN", "COLUMN_ITEM_WITHOUT_PRESENCE"),
    "MISSING_STOREY": ("STOREY_PLAN_MISSING",),
    "EXTRA_STOREY": ("STOREY_COLUMN_BANDS_MISSING", "COLUMN_PRESENCE_NOT_ITEMIZED"),
    "SCHEDULE_UNREAD": ("SCHEDULE_ROW_UNREAD",),
}
# held-out vocabulary: layer names and spellings the development seeds never draw (generalisation of the names)
LAYERS_HELDOUT = {
    "BOUNDARY_WALL": ["WALL-BOUNDARY", "S-COMPOUND-WALL", "21"], "POOL": ["S-SWIMMING-POOL", "POOL-SHELL", "22"],
    "LIFT_PIT": ["S-ELEVATOR-PIT", "LIFT-SHAFT", "23"], "WATER_TANK": ["S-WATER-TANK", "RESERVOIR", "24"],
    "DOME": ["CUPOLA", "S-DOMES", "25"], "STAIR": ["S-STAIRCASE", "STEPS", "26"],
    "SUNKEN_SLAB": ["S-DROP-SLAB", "RECESS", "27"], "UNKNOWN_OUTLINE": ["28", "29", "MISC-2"],
    "LEVEL": ["S-LEVEL-MARK", "LVL-SYM"], "SECTION": ["S-SECTION-LINE", "SECT"], "NORTH": ["NORTH-ARROW", "SYMBOLS"],
}
NOTE_HELDOUT = {"BOUNDARY_WALL": ["COMPOUND WALL", "PLOT BOUNDARY WALL", None], "POOL": ["SWIMMING-POOL", None],
                "LIFT_PIT": ["ELEVATOR PIT", "LIFT SHAFT", None], "WATER_TANK": ["RESERVOIR", "W. TANK", None],
                "DOME": ["CUPOLA", None], "STAIR": ["STAIRCASE", None], "SUNKEN_SLAB": ["DROPPED SLAB", "RECESSED", None]}
PLANTED_HELDOUT = ["P.C {a}*{b}", "PLANTED COLUMN {a}x{b}", "P.C {a} X {b}"]
PLANTED_SPELLINGS = ["P.C {a}x{b}", "PC {a}X{b}", "P.C. {a} x {b}", "PLANTED COL. {a}x{b}", "PC ({a}x{b})"]
PLANTED_SECTIONS = [(20, 40), (20, 50), (25, 50), (20, 60), (30, 30)]
DEPENDENCY_NOTES = ["AS PER ARCH.", "LEVEL AS PER ARCH", "SEE DETAIL 3", "FOLLOW ARCH.", "BY OTHERS"]
NOTE = {"BOUNDARY_WALL": ["BOUNDARY WALL", "FENCE WALL", None, None], "POOL": ["SWIMMING POOL", "POOL", None],
        "LIFT_PIT": ["LIFT PIT", "LIFT", "ELEVATOR", None], "WATER_TANK": ["WATER TANK", "TANK", None],
        "DOME": ["DOME", None], "STAIR": ["UP", "STAIR", None], "SUNKEN_SLAB": ["SUNKEN SLAB -0.30", "SUNK", None]}
ALL_KINDS = ("PLANTED_COLUMN", "BOUNDARY_WALL", "POOL", "LIFT_PIT", "WATER_TANK", "DOME", "STAIR", "SUNKEN_SLAB",
             "UNKNOWN_OUTLINE", "SCHEDULE_ORPHAN", "LABEL_ORPHAN", "DEPENDENCY_NOTE", "COLUMN_GAP", "SCHEDULE_UNREAD")


def _arabic_note(kind):
    """an Arabic note word for the family, taken from the engine's own bilingual vocabulary (never typed here)."""
    from engine.source import generic_route as GR
    key = {"BOUNDARY_WALL": "WALLS", "POOL": "POOL", "LIFT_PIT": "LIFT", "WATER_TANK": "WATER_TANK",
           "DOME": "DOMES", "STAIR": "STAIRS"}.get(kind)
    words = [w for w in GR.SCOPE_WORDS.get(key, ()) if not w.isascii()]
    return words[0] if words else None


class _Sheet:
    """drawing-unit placement of design metres on one sheet, as tools/synthetic_villa places them."""

    def __init__(self, D, key, slot=None):
        self.s = 1.0 if D["var"]["units"] == "m" else 1000.0
        n = SV.SHEET_ORDER.index(key) if slot is None else slot
        self.ox = n * 45.0

    def P(self, x, y):
        return ((self.ox + 4.0 + x) * self.s, (4.0 + y) * self.s)

    def local(self, x, y):                      # sheet-local metres (world - frame origin)
        return (4.0 + x, 4.0 + y)


def _box_local(sh, x0, y0, x1, y1):
    a, b = sh.local(x0, y0), sh.local(x1, y1)
    return (round(min(a[0], b[0]), 3), round(min(a[1], b[1]), 3), round(max(a[0], b[0]), 3), round(max(a[1], b[1]), 3))


def generate(out_dir, seed, defects=False, vocabulary="dev", hard=False):
    """vocabulary "heldout": layer names, note words and planted-column spellings the development seeds never use;
    hard: rebar symbols and section marks drawn on numbered layers inside the plans (distractors)."""
    import ezdxf
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    R = random.Random(seed * 2654435761 % 2 ** 32 + 17)            # M6 stream: never touches the M2 design draw
    D = SV.design(seed)
    D["var"].update(defects=bool(defects), m3=False, m4=False)
    path = out / f"villa_m6_{seed}.dxf"
    SV.write_dxf(D, path)
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    s = 1.0 if D["var"]["units"] == "m" else 1000.0
    th = 0.2 * s
    xs, ys = D["xs"], D["ys"]
    X, Y = xs[-1], ys[-1]
    text_layer = D["var"]["layers"]["text"]
    col_layer = D["var"]["layers"]["col"]
    truth, distract = [], []
    LAY = LAYERS_HELDOUT if vocabulary == "heldout" else LAYERS
    NOTES_ = NOTE_HELDOUT if vocabulary == "heldout" else NOTE
    SPELL = PLANTED_HELDOUT if vocabulary == "heldout" else PLANTED_SPELLINGS
    variant = {"missing_storey": seed % 7 == 5, "extra_storey": seed % 7 == 3 and not defects}
    kinds = [k for k in ALL_KINDS if R.random() < 0.6]
    for must in R.sample(ALL_KINDS, 3):
        if must not in kinds:
            kinds.append(must)
    if variant["missing_storey"]:
        kinds = [k for k in kinds if k not in ("WATER_TANK", "DOME")]
    top = "GF" if variant["missing_storey"] else "1F"

    def layer(name):
        if name not in doc.layers:
            doc.layers.add(name)
        return name

    def line(sh, a, b, lay):
        msp.add_line(sh.P(*a), sh.P(*b), dxfattribs={"layer": layer(lay)})

    def rect(sh, x0, y0, x1, y1, lay):
        pts = [sh.P(x0, y0), sh.P(x1, y0), sh.P(x1, y1), sh.P(x0, y1)]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer(lay)})

    def text(sh, val, x, y, lay=None, h=None):
        if not val:
            return
        t = msp.add_text(val, dxfattribs={"layer": lay or text_layer, "height": h or th})
        t.set_placement(sh.P(x, y))

    def note(kind):
        opts = list(NOTES_.get(kind, [None]))
        ar = _arabic_note(kind)
        if ar and R.random() < 0.25:
            return ar
        return R.choice(opts)

    def add(kind, sheet, box, **kw):
        rec = {"id": f"T{len(truth) + 1:02d}", "kind": kind, "family": FAMILY[kind], "sheet": sheet, "box": box,
               "expect": list(EXPECT[kind])}
        rec.update(kw)
        truth.append(rec)

    def bay(i, j):
        return xs[i], ys[j], xs[i + 1], ys[j + 1]

    nbx, nby = len(xs) - 1, len(ys) - 1
    bays = [(i, j) for i in range(nbx) for j in range(nby) if (i, j) != (0, 0)]   # bay (0, 0) holds the opening
    R.shuffle(bays)
    used_bays = {}

    def take_bay(sheet):
        for b in bays:
            if b not in used_bays.get(sheet, set()):
                used_bays.setdefault(sheet, set()).add(b)
                return b
        return None

    F = _Sheet(D, "FOUNDATION")
    # ---------------------------------------------------------------- plot line (every plan) + boundary wall
    mx0, my0 = 3.6, R.uniform(2.5, 3.2)                          # south margin clear of the footings
    mx1, my1 = R.uniform(1.6, 2.4), R.uniform(1.6, 2.4)
    if D["var"]["curved"]:
        mx1 = 7.6                                   # the curved beam B9 stands right of the building
    plot = (-mx0, -my0, X + mx1, Y + my1)
    plot_layer = R.choice(LAY["BOUNDARY_WALL"])
    for key in ("FOUNDATION", "GF", "1F"):
        sh = _Sheet(D, key)
        rect(sh, *plot, plot_layer)
    if "BOUNDARY_WALL" in kinds:
        w = R.choice([0.2, 0.25, 0.3])
        sides = R.sample(["S", "N", "W"], R.choice([1, 2, 3]))
        boxes, length = [], 0.0
        for side in sides:
            if side == "S":
                a, b, off = (plot[0], plot[1]), (plot[2], plot[1]), (0.0, w)
            elif side == "N":
                a, b, off = (plot[0], plot[3]), (plot[2], plot[3]), (0.0, -w)
            else:
                a, b, off = (plot[0], plot[1]), (plot[0], plot[3]), (w, 0.0)
            line(F, (a[0] + off[0], a[1] + off[1]), (b[0] + off[0], b[1] + off[1]), plot_layer)
            boxes.append((min(a[0], a[0] + off[0]), min(a[1], a[1] + off[1]), max(b[0], b[0] + off[0]),
                          max(b[1], b[1] + off[1])))
            length += math.dist(a, b)
        nt = note("BOUNDARY_WALL")
        if nt:                                     # beside the first wall side drawn
            side = sides[0]
            if side == "S":
                text(F, nt, plot[0] + 1.0, plot[1] + w + 0.25)
            elif side == "N":
                text(F, nt, plot[0] + 1.0, plot[3] - w - 0.45)
            else:
                text(F, nt, plot[0] + w + 0.25, plot[1] + 1.0)
        bx = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
        add("BOUNDARY_WALL", "FOUNDATION", _box_local(F, *bx), layer=plot_layer, note=bool(nt),
            magnitude={"strip_length_m": round(length, 3), "strip_width_m": w})
    # ---------------------------------------------------------------- pool in the left plot margin
    if "POOL" in kinds:
        lay = R.choice(LAY["POOL"])
        L, W, t = R.uniform(3.0, min(6.0, Y - 0.5)), R.uniform(1.6, 2.0), R.choice([0.2, 0.25, 0.3])
        x0, y0 = -mx0 + 0.25, R.uniform(0.2, max(0.3, Y - L - 0.2))
        rect(F, x0, y0, x0 + W, y0 + L, lay)
        rect(F, x0 + t, y0 + t, x0 + W - t, y0 + L - t, lay)
        nt = note("POOL")
        if nt:
            text(F, nt, x0 + 0.3, y0 + L / 2)
        add("POOL", "FOUNDATION", _box_local(F, x0, y0, x0 + W, y0 + L), layer=lay, note=bool(nt),
            magnitude={"outer_area_m2": round(L * W, 3), "ring_area_m2": round(L * W - (L - 2 * t) * (W - 2 * t), 3)})
    # ---------------------------------------------------------------- lift pit in a foundation bay
    if "LIFT_PIT" in kinds:
        b = take_bay("FOUNDATION")
        if b:
            bx0, by0, bx1, by1 = bay(*b)
            a = R.uniform(1.6, 2.0)
            cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
            lay = R.choice(LAY["LIFT_PIT"])
            rect(F, cx - a / 2, cy - a / 2, cx + a / 2, cy + a / 2, lay)
            rect(F, cx - a / 2 + 0.2, cy - a / 2 + 0.2, cx + a / 2 - 0.2, cy + a / 2 - 0.2, lay)
            nt = note("LIFT_PIT")
            if nt:
                text(F, nt, cx - 0.4, cy)
            add("LIFT_PIT", "FOUNDATION", _box_local(F, cx - a / 2, cy - a / 2, cx + a / 2, cy + a / 2), layer=lay,
                note=bool(nt), magnitude={"outer_area_m2": round(a * a, 3)})
    # ---------------------------------------------------------------- unknown outline in the plot margin (south)
    if "UNKNOWN_OUTLINE" in kinds:
        lay = R.choice(LAY["UNKNOWN_OUTLINE"])
        y0 = -my0 + 0.35
        w_, h_ = R.uniform(1.0, 2.5), R.uniform(0.5, min(0.9, -1.25 - y0))     # clear of the footings (>= 1.25 m)
        x0 = R.uniform(0.5, max(0.6, X - w_ - 0.5))
        rect(F, x0, y0, x0 + w_, y0 + h_, lay)
        add("UNKNOWN_OUTLINE", "FOUNDATION", _box_local(F, x0, y0, x0 + w_, y0 + h_), layer=lay, note=False,
            magnitude={"area_m2": round(w_ * h_, 3)})
    # ---------------------------------------------------------------- label orphan (foundation strap mark / bay mark)
    if "LABEL_ORPHAN" in kinds:
        G = _Sheet(D, "GF")
        b = take_bay("GF")
        if b and R.random() < 0.5:
            bx0, by0, bx1, by1 = bay(*b)
            mk = D["btypes"][0]
            cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
            text(G, mk, cx, cy, h=0.15 * s)
            add("LABEL_ORPHAN", "GF", _box_local(G, cx - 0.2, cy - 0.2, cx + 0.4, cy + 0.2), token=mk)
        else:
            cx, cy = (xs[0] + xs[1]) / 2, ys[0] + 0.15
            text(F, "SB1", cx, cy, h=0.15 * s)
            add("LABEL_ORPHAN", "FOUNDATION", _box_local(F, cx - 0.2, cy - 0.2, cx + 0.4, cy + 0.2), token="SB1",
                family="GROUND_BEAMS")
    # ---------------------------------------------------------------- slab-plan elements
    G = _Sheet(D, "GF")
    T = _Sheet(D, top)
    beams = SV.beams_of(D)
    interior = [bm for bm in beams if bm["tagged"] and 0 < (bm["line"]) < (len(ys) - 1 if bm["axis"] == "x" else
                                                                             len(xs) - 1)]
    if "PLANTED_COLUMN" in kinds and interior:
        bm = R.choice(interior)
        a_, b_ = R.choice(PLANTED_SECTIONS)
        spelling = R.choice(SPELL)
        lab = spelling.format(a=a_, b=b_)
        mx, my = bm["mid_design"]
        tx, ty = (mx + 0.35, my + 0.3) if bm["axis"] == "x" else (mx + 0.3, my + 0.35)
        text(G, lab, tx, ty, h=0.15 * s)
        box_above = (not variant["missing_storey"]) and R.random() < 0.5
        also = []
        if box_above:
            U = _Sheet(D, "1F")
            rect(U, mx - a_ / 200, my - b_ / 200, mx + a_ / 200, my + b_ / 200, col_layer)
            also.append({"storey": "1F", "box": _box_local(U, mx - a_ / 200, my - b_ / 200, mx + a_ / 200,
                                                         my + b_ / 200)})
        add("PLANTED_COLUMN", "GF", _box_local(G, mx - 0.3, my - 0.3, tx + 0.8, ty + 0.3), label=lab,
            section_cm=(a_, b_), box_above=box_above, at_beam=bm["type"], also=also)
    if "DEPENDENCY_NOTE" in kinds and beams:
        bm = R.choice([b for b in beams if b["tagged"]] or beams)
        mx, my = bm["mid_design"]
        nt = R.choice(DEPENDENCY_NOTES)
        tx, ty = (mx - 0.5, my - 0.45) if bm["axis"] == "x" else (mx + 0.2, my - 0.6)
        text(G, nt, tx, ty, h=0.15 * s)
        add("DEPENDENCY_NOTE", "GF", _box_local(G, tx - 0.1, ty - 0.1, tx + 1.5, ty + 0.3), note_text=nt)
    if "STAIR" in kinds:
        b = take_bay("GF")
        if b:
            bx0, by0, bx1, by1 = bay(*b)
            lay = R.choice(LAY["STAIR"])
            wf = R.uniform(1.0, 1.2)
            go = R.choice([0.28, 0.29, 0.30])
            n = int(min(14, (by1 - by0 - 0.8) / go))
            x0 = bx0 + 0.4
            y0 = by0 + 0.4
            rect(G, x0, y0, x0 + wf, y0 + n * go, lay)
            for k in range(1, n):
                line(G, (x0, y0 + k * go), (x0 + wf, y0 + k * go), lay)
            nt = note("STAIR")
            if nt:
                text(G, nt, x0 + 0.2, y0 + n * go / 2, h=0.15 * s)
            add("STAIR", "GF", _box_local(G, x0, y0, x0 + wf, y0 + n * go), layer=lay, note=bool(nt),
                magnitude={"n_treads": n, "going_m": go})
    if "SUNKEN_SLAB" in kinds:
        b = take_bay("GF")
        if b:
            bx0, by0, bx1, by1 = bay(*b)
            lay = R.choice(LAY["SUNKEN_SLAB"])
            w_, h_ = R.uniform(1.4, min(2.4, bx1 - bx0 - 1.0)), R.uniform(1.4, min(2.0, by1 - by0 - 1.0))
            x0, y0 = bx0 + 0.5, by0 + 0.5
            rect(G, x0, y0, x0 + w_, y0 + h_, lay)
            nt = note("SUNKEN_SLAB")
            if nt:
                text(G, nt, x0 + 0.2, y0 + h_ / 2, h=0.15 * s)
            add("SUNKEN_SLAB", "GF", _box_local(G, x0, y0, x0 + w_, y0 + h_), layer=lay, note=bool(nt),
                magnitude={"area_m2": round(w_ * h_, 3)})
    if "WATER_TANK" in kinds:
        b = take_bay(top)
        if b:
            bx0, by0, bx1, by1 = bay(*b)
            lay = R.choice(LAY["WATER_TANK"])
            w_, h_ = R.uniform(1.5, min(2.5, bx1 - bx0 - 1.0)), R.uniform(1.2, min(2.0, by1 - by0 - 1.0))
            x0, y0 = bx0 + 0.5, by0 + 0.5
            rect(T, x0, y0, x0 + w_, y0 + h_, lay)
            rect(T, x0 + 0.2, y0 + 0.2, x0 + w_ - 0.2, y0 + h_ - 0.2, lay)
            nt = note("WATER_TANK")
            if nt:
                text(T, nt, x0 + 0.3, y0 + h_ / 2, h=0.15 * s)
            add("WATER_TANK", top, _box_local(T, x0, y0, x0 + w_, y0 + h_), layer=lay, note=bool(nt),
                magnitude={"outer_area_m2": round(w_ * h_, 3)})
    if "DOME" in kinds:
        b = take_bay(top)
        if b:
            bx0, by0, bx1, by1 = bay(*b)
            r = min(R.uniform(1.0, 1.6), (bx1 - bx0) / 2 - 0.4, (by1 - by0) / 2 - 0.4)
            cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
            lay = R.choice(LAY["DOME"])
            msp.add_circle(T.P(cx, cy), r * s, dxfattribs={"layer": layer(lay)})
            msp.add_circle(T.P(cx, cy), (r - 0.2) * s, dxfattribs={"layer": layer(lay)})
            ribs = R.random() < 0.5
            if ribs:
                for k in range(12):
                    a = 2 * math.pi * k / 12
                    line(T, (cx, cy), (cx + (r - 0.2) * math.cos(a), cy + (r - 0.2) * math.sin(a)), lay)
            nt = note("DOME")
            if nt:
                text(T, nt, cx - 0.3, cy + r + 0.15, h=0.15 * s)
            add("DOME", top, _box_local(T, cx - r, cy - r, cx + r, cy + r), layer=lay, note=bool(nt), ribs=ribs,
                magnitude={"radius_m": round(r, 3)})
    # ---------------------------------------------------------------- column left off the GF roof plan
    if "COLUMN_GAP" in kinds:
        inner = [c for c in D["cols"] if 0 < c["i"] < len(xs) - 1 or 0 < c["j"] < len(ys) - 1] or D["cols"]
        c = R.choice(inner)
        x0, y0 = G.P(c["x"] - 0.4, c["y"] - 0.4)
        x1, y1 = G.P(c["x"] + 0.8, c["y"] + 0.8)
        gone = 0
        for e in list(msp):
            if e.dxftype() in ("LWPOLYLINE", "INSERT", "HATCH", "TEXT") and e.dxf.layer in (col_layer, text_layer):
                if e.dxftype() == "LWPOLYLINE":
                    pts = [p[:2] for p in e.get_points("xy")]
                    cxp, cyp = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
                elif e.dxftype() == "HATCH":
                    p0 = _entity_point(e)
                    if p0 is None:
                        continue
                    cxp, cyp = p0[0], p0[1]
                else:
                    cxp, cyp = e.dxf.insert[0], e.dxf.insert[1]
                if x0 <= cxp <= x1 and y0 <= cyp <= y1 and (e.dxftype() != "TEXT" or e.dxf.text == c["type"]):
                    msp.delete_entity(e)
                    gone += 1
        add("COLUMN_GAP", "GF", _box_local(G, c["x"] - 0.4, c["y"] - 0.4, c["x"] + 0.4, c["y"] + 0.4),
            storey="GF", column=c["type"], removed=gone)
    # ---------------------------------------------------------------- schedule orphan
    if "SCHEDULE_ORPHAN" in kinds:
        tags = D["var"]["tags"]["beam"]
        u = 100.0 if D["var"]["tags"]["unit"] == "cm" else 1000.0
        mk = "B6"
        rows = SV.schedule_rows(D)
        nrows = sum(len(v) for v in rows.values())
        ins = msp.add_blockref("BEAM_ROW", _Sheet(D, "SCHED").P(1.0, 20.0 - 0.6 * nrows),
                               dxfattribs={"layer": D["var"]["layers"]["sched"]})
        ins.add_auto_attribs(dict(zip(tags, [mk, f"{0.2 * u:g}", f"{0.45 * u:g}", "3", "14", "2", "12", "5", "8"])))
        add("SCHEDULE_ORPHAN", "SCHED", None, token=mk)
    if "SCHEDULE_UNREAD" in kinds:
        tags = D["var"]["tags"]["beam"]
        u = 100.0 if D["var"]["tags"]["unit"] == "cm" else 1000.0
        key = R.choice(["B.W", "R.W", "P.W", "T.B"])
        rows = SV.schedule_rows(D)
        nrows = sum(len(v) for v in rows.values()) + (1 if "SCHEDULE_ORPHAN" in kinds else 0)
        ins = msp.add_blockref("BEAM_ROW", _Sheet(D, "SCHED").P(1.0, 20.0 - 0.6 * nrows),
                               dxfattribs={"layer": D["var"]["layers"]["sched"]})
        ins.add_auto_attribs(dict(zip(tags, [key, f"{0.2 * u:g}", f"{0.6 * u:g}", "4", "16", "2", "14", "7", "8"])))
        add("SCHEDULE_UNREAD", "SCHED", None, token=key)
    # ---------------------------------------------------------------- distractors
    for key in ("GF", "1F"):
        if variant["missing_storey"] and key == "1F":
            continue
        sh = _Sheet(D, key)
        lay = R.choice(LAY["LEVEL"])
        px, py = X * R.uniform(0.2, 0.8), Y * R.uniform(0.2, 0.8)
        msp.add_lwpolyline([sh.P(px, py), sh.P(px + 0.25, py + 0.25), sh.P(px - 0.25, py + 0.25)], close=True,
                           dxfattribs={"layer": layer(lay)})
        text(sh, "+3.50", px + 0.3, py + 0.1, lay=text_layer, h=0.15 * s)
        distract.append({"kind": "LEVEL_MARK", "sheet": key, "box": _box_local(sh, px - 0.3, py, px + 0.3, py + 0.3)})
        lay = R.choice(LAY["SECTION"])
        sx_ = R.uniform(0.3, 0.7) * X
        line(sh, (sx_, -1.2), (sx_, Y + 1.2), lay)
        for yy in (-1.6, Y + 1.6):
            msp.add_circle(sh.P(sx_, yy), 0.35 * s, dxfattribs={"layer": layer(lay)})
            text(sh, "A", sx_ - 0.1, yy - 0.1, lay=text_layer, h=0.2 * s)
        distract.append({"kind": "SECTION_MARK", "sheet": key, "box": _box_local(sh, sx_ - 0.4, -2.0, sx_ + 0.4,
                                                                                  Y + 2.0)})
    if hard:                                       # rebar symbols and section marks on numbered layers
        for key in ("GF", "1F"):
            if variant["missing_storey"] and key == "1F":
                continue
            sh = _Sheet(D, key)
            b = take_bay(key) or (1, 0) if nbx > 1 else (0, 1)
            bx0, by0, bx1, by1 = bay(*b)
            lay = R.choice(["1", "2", "7"])
            yb = by0 + (by1 - by0) * R.uniform(0.3, 0.7)
            line(sh, (bx0 + 0.3, yb), (bx1 - 0.3, yb), lay)
            line(sh, (bx0 + 0.3, yb), (bx0 + 0.3, yb + 0.15), lay)
            line(sh, (bx1 - 0.3, yb), (bx1 - 0.3, yb + 0.15), lay)
            text(sh, R.choice(["Ø10@200", "T12-150", "5Ø10/M", "Y10 @ 150"]), (bx0 + bx1) / 2 - 0.4, yb + 0.1,
                 h=0.12 * s)
            distract.append({"kind": "REBAR_SYMBOL", "sheet": key, "box": _box_local(sh, bx0, yb - 0.2, bx1, yb + 0.4)})
            lay = R.choice(["3", "8", "9"])
            sy_ = R.uniform(0.3, 0.7) * Y
            line(sh, (-1.2, sy_), (X + 1.2, sy_), lay)
            for xx in (-1.6, X + 1.6):
                msp.add_circle(sh.P(xx, sy_), 0.35 * s, dxfattribs={"layer": layer(lay)})
                text(sh, "B", xx - 0.1, sy_ - 0.1, lay=text_layer, h=0.2 * s)
            distract.append({"kind": "SECTION_MARK", "sheet": key, "box": _box_local(sh, -2.0, sy_ - 0.4, X + 2.0,
                                                                                      sy_ + 0.4)})
    sh = _Sheet(D, "FOUNDATION")
    lay = R.choice(LAY["NORTH"])
    nx_, ny_ = -mx0 - 0.0, Y + my1 + 1.2
    msp.add_lwpolyline([sh.P(nx_, ny_), sh.P(nx_ + 0.2, ny_ + 0.6), sh.P(nx_ + 0.4, ny_)], close=True,
                       dxfattribs={"layer": layer(lay)})
    text(sh, "N", nx_ + 0.12, ny_ + 0.7, h=0.2 * s)
    gx, gy = X + mx1 + 0.8, Y + my1 - 0.5
    for k, ln in enumerate(["GENERAL NOTES:", "1. ALL DIMENSIONS ARE IN MM UNLESS NOTED.",
                            "2. CONCRETE FOR THE WATER TANK AND THE POOL SHALL BE SULPHATE RESISTING.",
                            "3. LIFT PIT WATERPROOFING BY SPECIALIST."]):
        if gx + 2 < 39.0:
            text(sh, ln, gx, gy - 0.4 * k, h=0.15 * s)
    distract.append({"kind": "GENERAL_NOTES", "sheet": "FOUNDATION", "box": None})
    # ---------------------------------------------------------------- storey variants
    if variant["missing_storey"]:
        sh = _Sheet(D, "1F")
        lo, hi = sh.ox * s, (sh.ox + 40.0) * s
        for e in list(msp):
            try:
                p0 = _entity_point(e)
            except Exception:
                continue
            if p0 is not None and lo - 1e-6 <= p0[0] <= hi + 1e-6:
                msp.delete_entity(e)
        add("MISSING_STOREY", "1F", None, storey="1F")
    elif variant["extra_storey"]:
        sh = _Sheet(D, "1F")
        lo, hi = sh.ox * s, (sh.ox + 40.0) * s
        dx = (4 * 45.0 - sh.ox) * s
        for e in list(msp):
            if e.dxftype() in ("DIMENSION",):
                continue
            p0 = _entity_point(e)
            if p0 is None or not (lo - 1e-6 <= p0[0] <= hi + 1e-6):
                continue
            c = e.copy()
            c.translate(dx, 0, 0)
            if c.dxftype() == "TEXT" and c.dxf.text == SV.TITLES[D["var"]["lang"]]["1F"]:
                c.dxf.text = "SECOND FLOOR ROOF SLAB"
            msp.add_entity(c)
        add("EXTRA_STOREY", "2F", None, storey="2F")
    doc.saveas(str(path))
    T_ = SV.truth(D)
    heights = dict(D["heights"])
    if variant["extra_storey"]:
        heights["2F"] = 3.4
    prof = SV.profile(D)
    if variant["extra_storey"]:
        prof["conventions"].append({"id": "STOREY_HEIGHT_2F", "title": "Storey height 2F", "kind": "number",
                                    "unit": "m", "base": 3.4, "low": 3.4, "high": 3.4, "provenance": "PRINTED_VALUE",
                                    "source": "synthetic section", "rationale": "printed floor to floor"})
    base_known = []
    if D["var"]["missing_type"]:
        base_known.append({"kind": "MISSING_TYPE", "token": D["btypes"][2],
                           "expect": ["PLACED_NOT_SCHEDULED", "LABEL_NOT_CONSUMED"]})
    if D["var"]["curved"]:
        cx, cy = X + 5.0, Y / 2.0
        for key in ("GF", top):
            sh = _Sheet(D, key)
            base_known.append({"kind": "CURVED_BEAM_B9", "sheet": key,
                               "box": _box_local(sh, cx - 2.2, cy - 0.2, cx + 2.2, cy + 2.2),
                               "expect": ["DRAWN_NOT_MEASURED", "MEASURED"]})
    gone = next((e.get("column") and (e["box"]) for e in truth if e["kind"] == "COLUMN_GAP"), None)
    design_columns = [{"type": c["type"], "local": (round(4 + c["x"], 3), round(4 + c["y"], 3)),
                       "storeys": [st for st in ("GF", "1F") if st in heights and
                                   not (st == "1F" and variant["missing_storey"])]} for c in D["cols"]]
    m6 = {"seed": seed, "defects": bool(defects), "vocabulary": vocabulary, "hard": bool(hard), "variant": variant,
          "elements": truth, "distractors": distract,
          "design_columns": design_columns, "column_gap_box": gone,
          "base_known": base_known, "plot_local": {k: _box_local(_Sheet(D, k), *plot) for k in ("FOUNDATION", "GF",
                                                                                                "1F")},
          "rule": "the truth is what this generator drew; it never reads the engine"}
    T_["m6"] = m6
    (out / f"villa_m6_{seed}.truth.json").write_text(json.dumps(T_, indent=1, ensure_ascii=False, default=str))
    (out / f"villa_m6_{seed}.profile.json").write_text(json.dumps(prof, indent=1))
    return path


def _entity_point(e):
    t = e.dxftype()
    if t == "LINE":
        return e.dxf.start
    if t in ("TEXT", "MTEXT", "INSERT"):
        return e.dxf.insert
    if t == "LWPOLYLINE":
        p = next(iter(e.get_points("xy")), None)
        return p
    if t in ("CIRCLE", "ARC"):
        return e.dxf.center
    if t == "HATCH":
        for path in e.paths:
            v = getattr(path, "vertices", None)
            if v:
                return v[0]
        return None
    if t == "DIMENSION":
        return e.dxf.defpoint
    return None


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--defects"]
    for sd in args[1:]:
        print(generate(args[0], int(sd), defects="--defects" in sys.argv))
