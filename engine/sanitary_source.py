"""A second DESIGN representation: the sanitary set, aligned or refused.

The architectural drawing says where the walls are. The sanitary drawing
says where the water and the drainage are. They are two representations
of one building, and neither replaces the other — so this module reads
the sanitary set into its own source, and then tries to put it on the
architectural plan.

    DESIGN_SANITARY       its own source, its own hash, its own
                          coordinates. Never written over the
                          architectural decode

ALIGNMENT IS A CLAIM, AND IT IS TESTED. A sheet plotted "to fit" has no
round scale, so the scale is SEARCHED for, and the search has to produce
a WINNER rather than a preference: the long walls of the architectural
plan must match the long lines of the sanitary sheet on both axes, and
the winning scale must beat the field. Where it does not, the alignment
is NOT ESTABLISHED and everything resting on it stays a question — an
alignment that is nearly right puts a floor drain in the wrong room.

AND A SYMBOL IS NOT A RULE. A drainage point near a pantry says water
arrives there. It does not say which wall is tiled, how high, or that the
pantry has a sink at all: those are the drawing's business and the
owner's, and this module reports what it found, not what it implies.
"""

from __future__ import annotations

import bisect
import hashlib
import math
from dataclasses import dataclass, field
from pathlib import Path

MODEL = "A_SANITARY_SET_IS_ITS_OWN_SOURCE_AND_ITS_ALIGNMENT_IS_TESTED_V1"

DESIGN_SANITARY = "DESIGN_SANITARY"
DESIGN_ARCHITECTURAL = "DESIGN_ARCHITECTURAL"

# --- how the alignment is judged ----------------------------------------
ESTABLISHED = "ALIGNMENT_ESTABLISHED"
AMBIGUOUS = "ALIGNMENT_AMBIGUOUS_NO_SCALE_WINS"
NOT_ESTABLISHED = "ALIGNMENT_NOT_ESTABLISHED"
NO_GEOMETRY = "THE_SANITARY_SET_CARRIES_NO_READABLE_GEOMETRY"

# A wall line of one drawing sits on the other's within this. A drawn
# wall is 200 mm thick in this project and a single-line wall sits on
# its centre, so 40 mm is a fifth of a wall: tight enough that a
# neighbouring wall cannot stand in for the right one.
ALIGN_TOL_MM = 40.0

# Enough of the long walls, on BOTH axes, or it is not an alignment.
ALIGN_MIN_SHARE = 0.6

# And the winning scale must beat the next distinct one by this much of
# the long walls, or the sheet is telling us nothing in particular.
ALIGN_MARGIN = 0.15

# What counts as a LONG wall — the ones a sanitary underlay shows.
LONG_WALL_MM = 3000.0
# and the page lines that could be one, in points of the sheet
LONG_LINE_PT = 80.0

# A fixture symbol is a small closed figure: a floor drain, a trap, a
# cleanout. In millimetres of building, once the scale is known.
FIXTURE_MIN_MM = 40.0
FIXTURE_MAX_MM = 600.0

ROT_NONE = "PAGE_X_IS_PLAN_X"
ROT_QUARTER = "PAGE_Y_IS_PLAN_X"
ORIENTATIONS = (ROT_NONE, ROT_QUARTER)


def model_hash() -> str:
    parts = ([MODEL, DESIGN_SANITARY, ESTABLISHED, AMBIGUOUS,
              NOT_ESTABLISHED, NO_GEOMETRY] + list(ORIENTATIONS)
             + [DRAINAGE_EVIDENCE, NO_DIRECTION]
             + [str(v) for v in (ALIGN_TOL_MM, ALIGN_MIN_SHARE,
                                 ARCH_SAME_LINE_MM, MIN_RUN_MM,
                                 ALIGN_MARGIN, LONG_WALL_MM,
                                 LONG_LINE_PT, FIXTURE_MIN_MM,
                                 FIXTURE_MAX_MM)])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "ALIGN_TOL_MM": ALIGN_TOL_MM,
        "ALIGN_MIN_SHARE": ALIGN_MIN_SHARE,
        "ALIGN_MARGIN": ALIGN_MARGIN,
        "LONG_WALL_MM": LONG_WALL_MM,
        "LONG_LINE_PT": LONG_LINE_PT,
        "FIXTURE_MIN_MM": FIXTURE_MIN_MM,
        "FIXTURE_MAX_MM": FIXTURE_MAX_MM,
        "why": {
            "the_scale_is_searched_not_assumed": (
                "a sheet plotted to fit has no round scale. 1:100 "
                "reduced by 8% is 1:108, and assuming 1:100 would put "
                "every fixture two metres out"),
            "a_winner_or_nothing": (
                "the best scale must beat the field. A best guess among "
                "equals is not an alignment, and an alignment that is "
                "nearly right puts a floor drain in the wrong room"),
            "a_symbol_is_not_a_rule": (
                "a drainage point near a pantry says water arrives "
                "there. It does not say which wall is tiled"),
        },
    }


@dataclass
class Page:
    """One sheet of the sanitary set, as geometry in page points."""

    index: int = 0
    width_pt: float = 0.0
    height_pt: float = 0.0
    rotation: int = 0
    v_lines: tuple = ()        # (x, y0, y1)
    h_lines: tuple = ()        # (y, x0, x1)
    blobs: tuple = ()          # (cx, cy, w, h) closed figures
    items: int = 0

    def record(self) -> dict:
        return {
            "page": self.index,
            "width_pt": round(self.width_pt, 1),
            "height_pt": round(self.height_pt, 1),
            "rotation": self.rotation,
            "vertical_lines": len(self.v_lines),
            "horizontal_lines": len(self.h_lines),
            "closed_figures": len(self.blobs),
            "vector_items": self.items,
        }


@dataclass
class Source:
    path: str = ""
    name: str = ""
    kind: str = DESIGN_SANITARY
    sha256: str = ""
    pages: list = field(default_factory=list)
    status: str = ""

    def record(self) -> dict:
        return {
            "source": self.name,
            "representation": self.kind,
            "path": self.path,
            "RAW_FILE_SHA256": self.sha256,
            "pages": [p.record() for p in self.pages],
            "status": self.status,
            "never_replaces": DESIGN_ARCHITECTURAL,
        }


@dataclass
class Alignment:
    """A transform from one sheet's points to the building's millimetres."""

    page: int = 0
    orientation: str = ROT_QUARTER
    scale_mm_per_pt: float = 0.0
    offset_x_mm: float = 0.0
    offset_y_mm: float = 0.0
    matched_x: float = 0.0
    matched_y: float = 0.0
    walls_x: int = 0
    walls_y: int = 0
    residual_mm: float | None = None
    runner_up: float = 0.0
    status: str = NOT_ESTABLISHED
    why: str = ""

    def to_model(self, px: float, py: float) -> tuple:
        """A point on the sheet, in the building's own coordinates."""
        if self.orientation == ROT_QUARTER:
            return (py * self.scale_mm_per_pt + self.offset_x_mm,
                    px * self.scale_mm_per_pt + self.offset_y_mm)
        return (px * self.scale_mm_per_pt + self.offset_x_mm,
                py * self.scale_mm_per_pt + self.offset_y_mm)

    def record(self) -> dict:
        return {
            "page": self.page,
            "orientation": self.orientation,
            "scale_mm_per_pt": round(self.scale_mm_per_pt, 3),
            "plot_scale_1_to": (round(self.scale_mm_per_pt / 0.352778)
                                if self.scale_mm_per_pt else None),
            "offset_x_mm": round(self.offset_x_mm, 1),
            "offset_y_mm": round(self.offset_y_mm, 1),
            "long_walls_matched_x": f"{self.matched_x:.0%} of {self.walls_x}",
            "long_walls_matched_y": f"{self.matched_y:.0%} of {self.walls_y}",
            "mean_residual_mm": (None if self.residual_mm is None
                                 else round(self.residual_mm, 1)),
            "runner_up_score": round(self.runner_up, 3),
            "status": self.status,
            "why": self.why,
            "tolerance_mm": ALIGN_TOL_MM,
        }


def read(path: str) -> Source:
    """The sanitary set as vector geometry, or an honest empty source."""
    p = Path(path)
    src = Source(path=str(p), name=p.name,
                 sha256=hashlib.sha256(p.read_bytes()).hexdigest()
                 if p.exists() else "",
                 status=NO_GEOMETRY)
    if not p.exists():
        src.status = "THE_FILE_IS_NOT_HERE"
        return src
    try:
        import pymupdf
    except ImportError:      # noqa: BLE001
        src.status = "NO_PDF_READER"
        return src
    doc = pymupdf.open(str(p))
    for i, page in enumerate(doc, 1):
        v, h, blobs, items = [], [], [], 0
        for path_obj in page.get_drawings():
            xs, ys = [], []
            for it in path_obj["items"]:
                items += 1
                if it[0] == "l":
                    a, b = it[1], it[2]
                    xs += [a.x, b.x]
                    ys += [a.y, b.y]
                    if abs(a.x - b.x) < 0.05 and abs(a.y - b.y) > 1.0:
                        v.append((a.x, min(a.y, b.y), max(a.y, b.y)))
                    elif abs(a.y - b.y) < 0.05 and abs(a.x - b.x) > 1.0:
                        h.append((a.y, min(a.x, b.x), max(a.x, b.x)))
                elif it[0] == "c":
                    for pt in it[1:]:
                        xs.append(pt.x)
                        ys.append(pt.y)
                elif it[0] == "re":
                    r = it[1]
                    xs += [r.x0, r.x1]
                    ys += [r.y0, r.y1]
            if xs and ys:
                w, ht = max(xs) - min(xs), max(ys) - min(ys)
                blobs.append(((min(xs) + max(xs)) / 2.0,
                              (min(ys) + max(ys)) / 2.0, w, ht))
        src.pages.append(Page(
            index=i, width_pt=page.rect.width, height_pt=page.rect.height,
            rotation=page.rotation, v_lines=tuple(v), h_lines=tuple(h),
            blobs=tuple(blobs), items=items))
        src.status = "READ"
    return src


def _long(values, cand, scale, tol=ALIGN_TOL_MM):
    """The share of `values` a scaled `cand` set covers, and the offset."""
    best, off_best, res_best = 0.0, None, None
    if not values or not cand:
        return 0.0, None, None
    for a in values:
        for q in cand:
            off = a - q * scale
            mapped = sorted(x * scale + off for x in cand)
            hit, res = 0, []
            for t in values:
                i = bisect.bisect_left(mapped, t)
                d = min((abs(mapped[j] - t) for j in (i - 1, i)
                         if 0 <= j < len(mapped)), default=1e9)
                if d <= tol:
                    hit += 1
                    res.append(d)
            share = hit / len(values)
            if share > best:
                best, off_best = share, off
                res_best = (sum(res) / len(res)) if res else None
    return best, off_best, res_best


def align(page: Page, *, wall_x, wall_y, scales=None) -> Alignment:
    """Put one sanitary sheet on the building, or say it does not go.

    `wall_x` and `wall_y` are the CENTRELINES of the architectural plan's
    long walls, in millimetres. A sanitary underlay draws a wall as one
    line, and one line sits on the centre of the two the architecture
    knows about.
    """
    pv = sorted({round(x, 2) for x, y0, y1 in page.v_lines
                 if y1 - y0 >= LONG_LINE_PT})
    ph = sorted({round(y, 2) for y, x0, x1 in page.h_lines
                 if x1 - x0 >= LONG_LINE_PT})
    out = Alignment(page=page.index, walls_x=len(wall_x),
                    walls_y=len(wall_y))
    if not pv or not ph or not wall_x or not wall_y:
        out.status = NO_GEOMETRY
        out.why = "one of the two drawings has no long lines to match"
        return out

    tried = []
    for orient in ORIENTATIONS:
        xs_cand = ph if orient == ROT_QUARTER else pv
        ys_cand = pv if orient == ROT_QUARTER else ph
        for scale in (scales or [round(v, 1) for v in
                                 _frange(20.0, 60.0, 0.5)]):
            fx, ox, rx = _long(wall_x, xs_cand, scale)
            fy, oy, ry = _long(wall_y, ys_cand, scale)
            tried.append((min(fx, fy), fx + fy, scale, orient, fx, fy,
                          ox, oy, rx, ry))
    tried.sort(reverse=True)
    top = tried[0]
    # the runner-up is the best result at a DIFFERENT scale, so that two
    # neighbouring scales of one peak are not read as two answers
    runner = next((t for t in tried[1:] if abs(t[2] - top[2]) > 1.0),
                  None)
    out.scale_mm_per_pt = top[2]
    out.orientation = top[3]
    out.matched_x, out.matched_y = top[4], top[5]
    out.offset_x_mm, out.offset_y_mm = (top[6] or 0.0), (top[7] or 0.0)
    res = [r for r in (top[8], top[9]) if r is not None]
    out.residual_mm = (sum(res) / len(res)) if res else None
    out.runner_up = (runner[0] if runner else 0.0)

    if min(out.matched_x, out.matched_y) < ALIGN_MIN_SHARE:
        out.status = NOT_ESTABLISHED
        out.why = (f"the best scale matches {out.matched_x:.0%} of the "
                   f"long walls on one axis and {out.matched_y:.0%} on "
                   f"the other, and {ALIGN_MIN_SHARE:.0%} is the least "
                   "this project calls an alignment")
        return out
    if top[0] - out.runner_up < ALIGN_MARGIN:
        out.status = AMBIGUOUS
        out.why = (f"scale {top[2]} matches {top[0]:.0%} and another "
                   f"scale matches {out.runner_up:.0%}. A best guess "
                   "among equals is not an alignment")
        return out
    out.status = ESTABLISHED
    out.why = (f"at {out.scale_mm_per_pt} mm per point the long walls of "
               f"the plan match on both axes — {out.matched_x:.0%} and "
               f"{out.matched_y:.0%} — and the next scale reaches only "
               f"{out.runner_up:.0%}")
    return out


def _frange(lo, hi, step):
    v = lo
    while v < hi:
        yield v
        v += step


def fixtures(page: Page, alignment: Alignment) -> list:
    """The small closed figures of a sheet, in the building's own mm.

    A floor drain, a trap, a cleanout and a fitting are all drawn as a
    small closed figure. WHICH of them this one is, the sheet's legend
    says and this module does not: it reports a drainage-plan symbol at
    a place, with its size, and nothing more.
    """
    if alignment.status != ESTABLISHED or not alignment.scale_mm_per_pt:
        return []
    out = []
    for n, (cx, cy, w, h) in enumerate(page.blobs, 1):
        wm = w * alignment.scale_mm_per_pt
        hm = h * alignment.scale_mm_per_pt
        if not (FIXTURE_MIN_MM <= max(wm, hm) <= FIXTURE_MAX_MM):
            continue
        x, y = alignment.to_model(cx, cy)
        out.append({
            "symbol_id": f"SAN-P{page.index}-{n:04d}",
            "at_mm": [round(x, 1), round(y, 1)],
            "size_mm": [round(wm, 1), round(hm, 1)],
            "representation": DESIGN_SANITARY,
            "what_it_is": "A_DRAWING_SYMBOL_ON_THE_SANITARY_SHEET",
            "what_it_is_not": (
                "a fixture schedule, a pipe size, or a reason to tile a "
                "wall"),
        })
    return out


# A sanitary sheet draws the architecture too, as a background. A line
# that sits on an architectural wall line is that wall, redrawn — not
# drainage — and counting it as drainage makes every room look plumbed.
ARCH_SAME_LINE_MM = 120.0
# Below this a segment is a piece of a letter or a hatch tick, not a run.
MIN_RUN_MM = 150.0

DRAINAGE_EVIDENCE = "SANITARY_LINEWORK_AFTER_THE_ARCHITECTURE_IS_TAKEN_OUT"
NO_DIRECTION = "THE_SANITARY_LINEWORK_NAMES_NO_HOST_WALL"


def _sanitary_only(page: Page, alignment: Alignment, arch_v, arch_h):
    """The sheet's linework with the architecture it redraws taken out."""
    from shapely.geometry import LineString

    av, ah = sorted(arch_v), sorted(arch_h)

    def _on_arch(pos, arr):
        if not arr:
            return False
        i = bisect.bisect_left(arr, pos)
        return any(abs(arr[j] - pos) <= ARCH_SAME_LINE_MM
                   for j in (i - 1, i) if 0 <= j < len(arr))

    kept, dropped = [], 0
    runs = ([(x, y0, x, y1) for x, y0, y1 in page.v_lines]
            + [(x0, y, x1, y) for y, x0, x1 in page.h_lines])
    for ax, ay, bx, by in runs:
        p1 = alignment.to_model(ax, ay)
        p2 = alignment.to_model(bx, by)
        if math.dist(p1, p2) < MIN_RUN_MM:
            continue
        mx = (p1[0] + p2[0]) / 2.0
        my = (p1[1] + p2[1]) / 2.0
        if abs(p1[0] - p2[0]) < ARCH_SAME_LINE_MM and _on_arch(mx, av):
            dropped += 1
            continue
        if abs(p1[1] - p2[1]) < ARCH_SAME_LINE_MM and _on_arch(my, ah):
            dropped += 1
            continue
        kept.append(LineString([p1, p2]))
    return kept, dropped


def evidence_near(page: Page, alignment: Alignment, x: float, y: float,
                  *, radius_mm: float, arch_v=(), arch_h=()) -> dict:
    """The sanitary linework around a place the register cannot name.

    A pantry label that resolves to no physical space still stands
    somewhere, and the question "is there drainage here" is answerable
    about a place. WHICH WALL it belongs to is not, and this says so.
    """
    from shapely.geometry import Point

    if alignment.status != ESTABLISHED:
        return {"status": alignment.status, "sanitary_linework_lm": None}
    kept, _dropped = _sanitary_only(page, alignment, arch_v, arch_h)
    area = Point(x, y).buffer(radius_mm)
    quadrant = {"NE": 0.0, "NW": 0.0, "SE": 0.0, "SW": 0.0}
    lm = 0.0
    for g in kept:
        try:
            piece = g.intersection(area)
        except Exception:      # noqa: BLE001
            continue
        if piece.is_empty:
            continue
        lm += piece.length
        c = piece.centroid
        quadrant[("N" if c.y > y else "S") + ("E" if c.x > x else "W")] \
            += piece.length / 1000.0
    total = lm / 1000.0
    share = max(quadrant.values()) / total if total else 0.0
    return {
        "status": ESTABLISHED,
        "at_mm": [round(x, 1), round(y, 1)],
        "radius_mm": radius_mm,
        "sanitary_linework_lm": round(total, 2),
        "by_quadrant_lm": {k: round(v, 2) for k, v in quadrant.items()},
        "largest_quadrant_share": round(share, 3),
        # A HOST WALL WOULD SHOW AS A CONCENTRATION. Linework spread
        # evenly around a label names no wall, and saying which one it
        # is anyway is the guess this project does not make.
        "names_a_host_wall": bool(share >= 0.6),
        "what_it_is": DRAINAGE_EVIDENCE,
        "what_it_is_not": NO_DIRECTION if share < 0.6 else "",
    }


def drainage_evidence(page: Page, alignment: Alignment, *, polygons=(),
                      arch_v=(), arch_h=()) -> dict:
    """What the sanitary sheet draws inside each space, minus the walls.

    The architecture is subtracted first — a wall redrawn on the drainage
    sheet is a wall — and what remains is measured per space. It is
    reported as a LENGTH OF LINEWORK, which is evidence that something
    sanitary is drawn there, and never as a fixture, a pipe size or a
    reason to tile.
    """
    from shapely.geometry import LineString

    if alignment.status != ESTABLISHED:
        return {"status": alignment.status, "rows": [],
                "why": "nothing is measured through an alignment that "
                       "did not establish"}
    kept, dropped = _sanitary_only(page, alignment, arch_v, arch_h)

    rows = []
    for space_id, poly in polygons:
        if poly is None or poly.is_empty:
            continue
        lm = 0.0
        for g in kept:
            try:
                if g.intersects(poly):
                    lm += g.intersection(poly).length
            except Exception:      # noqa: BLE001
                continue
        area = poly.area / 1e6
        rows.append({
            "physical_space_id": space_id,
            "area_m2": round(area, 3),
            "sanitary_linework_lm": round(lm / 1000.0, 2),
            "per_m2": round((lm / 1000.0) / area, 3) if area else None,
            "what_it_is": DRAINAGE_EVIDENCE,
            "what_it_is_not": (
                "a fixture, a pipe size, a sink, or a tiled wall"),
        })
    rows.sort(key=lambda r: -(r["per_m2"] or 0))
    return {
        "status": ESTABLISHED,
        "rows": rows,
        "segments_kept": len(kept),
        "segments_dropped_as_architecture": dropped,
        "why": ("the sanitary sheet redraws the architecture as its "
                "background. Those lines are taken out first, or every "
                "room looks plumbed"),
    }


def near(symbols, x: float, y: float, radius_mm: float) -> list:
    """The symbols within a radius of a place, nearest first."""
    out = []
    for s in symbols:
        sx, sy = s["at_mm"]
        d = math.hypot(sx - x, sy - y)
        if d <= radius_mm:
            out.append(dict(s, distance_mm=round(d, 1)))
    return sorted(out, key=lambda s: s["distance_mm"])
