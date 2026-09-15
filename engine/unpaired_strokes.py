"""E67 — 851 m of wall-pen stroke that did not pair is not 851 m of wall.

Round 1's source audit reported it as `SINGLE_LINE_WALL`. That was a guess
dressed as a measurement. The stroke weight says a mark was drawn with the
wall pen; it says nothing about whether the mark is a wall, and an architect
uses one pen for more than one thing.

So the population is named for what is actually known about it —

    UNPAIRED_WALL_STYLE_STROKE

— and then classified on evidence. NEVER FROM PEN WEIGHT ALONE.

This matters beyond nomenclature. The 46 wall-solid components and the 738 m2
merged free-space blob are probably the same missing-wall problem seen from
opposite ends, and the classes below are what tell a genuinely missing wall
apart from a fixture outline that was never a wall at all.
"""

from __future__ import annotations

from dataclasses import dataclass

POPULATION = "UNPAIRED_WALL_STYLE_STROKE"

# RENAMED. "CONFIRMED_SINGLE_LINE_WALL" claimed more than the evidence
# carries: a single vector stroke cannot establish a wall's THICKNESS, the
# location of either finish face, or a material polygon. What the evidence
# does support is that a separator EXISTS along that line.
#
#     SINGLE_LINE_WALL_EXISTENCE_SUPPORTED
#         a lone wall-pen run, solid in the raster, with no mate anywhere
#         on its line. Something is drawn there and it is probably a wall.
#         It may become a TOPOLOGY_SEPARATOR_HYPOTHESIS.
#
#     SINGLE_LINE_WALL_GEOMETRY_COMPLETE
#         the above PLUS an independently established thickness and both
#         face positions. Only this may create material geometry, and
#         nothing in this engine produces it yet.
#
# NEVER INVENT THE MISSING HALF.
SINGLE_LINE_EXISTENCE_SUPPORTED = "SINGLE_LINE_WALL_EXISTENCE_SUPPORTED"
SINGLE_LINE_GEOMETRY_COMPLETE = "SINGLE_LINE_WALL_GEOMETRY_COMPLETE"
# The old name, kept as an alias so no caller silently reads a different
# population, and deliberately equal to the EXISTENCE class so that any
# code still using it gets the weaker, correct claim.
CONFIRMED_SINGLE_LINE_WALL = SINGLE_LINE_EXISTENCE_SUPPORTED

# What a supported single line may be used FOR.
TOPOLOGY_SEPARATOR_HYPOTHESIS = "TOPOLOGY_SEPARATOR_HYPOTHESIS"
FRAGMENTED_MATE = "FRAGMENTED_MATE"
DIFFERENT_WALL_REPRESENTATION = "DIFFERENT_WALL_REPRESENTATION"
FIXTURE_OR_SYMBOL = "FIXTURE_OR_SYMBOL"
ANNOTATION_OR_DETAIL = "ANNOTATION_OR_DETAIL"
DUPLICATE = "DUPLICATE"
NON_WALL_GEOMETRY = "NON_WALL_GEOMETRY"
STROKE_UNRESOLVED = "UNRESOLVED"

CLASSES = (SINGLE_LINE_EXISTENCE_SUPPORTED, FRAGMENTED_MATE,
           DIFFERENT_WALL_REPRESENTATION, FIXTURE_OR_SYMBOL,
           ANNOTATION_OR_DETAIL, DUPLICATE, NON_WALL_GEOMETRY,
           STROKE_UNRESOLVED)

# Only these classes are candidates for a missing wall worth recovering.
WALL_LIKE_CLASSES = (SINGLE_LINE_EXISTENCE_SUPPORTED, FRAGMENTED_MATE,
                     DIFFERENT_WALL_REPRESENTATION)

# Classes that support a separator's EXISTENCE without establishing its
# geometry. These may generate a topology hypothesis and may never become
# material.
EXISTENCE_ONLY_CLASSES = (SINGLE_LINE_EXISTENCE_SUPPORTED,)

# What it takes to move from existence to geometry. None of these is
# produced by this engine yet, which is why the geometry class is empty.
GEOMETRY_REQUIREMENTS = (
    "an independently established wall THICKNESS for this line — from a "
    "printed dimension, a CAD entity, a wall schedule or a human decision",
    "the position of BOTH finish faces, not one face and an assumption",
    "a stated measurement basis for the resulting polygon",
)

# A stroke this short is a detail mark, whatever pen drew it: no wall in a
# villa is 150 mm long.
MIN_WALL_RUN_MM = 300.0
# Two strokes closer than this on the same line are the same mark twice.
DUPLICATE_TOL_MM = 2.0
# A run this close to an accepted band, on the same line, is that band's
# own face or a fragment of its mate.
FRAGMENT_REACH_MM = 60.0
# Raster support below this means nothing solid is drawn there at all.
MIN_RASTER_SUPPORT = 0.5
# A parallel face closer than this on a nearby line is a candidate MATE, so
# the run is not single-line at all — whatever the band engine did with the
# pair. The old test asked only for collinear neighbours on the SAME line
# and so never looked for the mate a single-line wall is defined by not
# having.
PARALLEL_FACE_REACH_MM = 500.0
# A single vector run this long is not a room's wall on a villa floor: it is
# a grid line, a section marker or a sheet border. The blind sample found a
# 50 m stroke classified as a single-line wall.
MAX_WALL_RUN_MM = 30_000.0
# A WALL IS PART OF A WALL NETWORK. A partition runs between other walls and
# something meets it at each end; a sheet border, a grid line and a section
# marker meet nothing. This is what finally separated the two 29 m frame
# lines at the top and bottom of the sheet from the building's geometry —
# and it is evidence about the drawing, not a length chosen to exclude them.
NETWORK_REACH_MM = 300.0


@dataclass(frozen=True)
class UnpairedStroke:
    """One wall-pen face that never became a band, and what it turned out to be."""

    stroke_id: str
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    stroke_class: str
    stroke_width_pt: float | None = None
    raster_support: float | None = None
    nearest_band_id: str = ""
    nearest_band_gap_mm: float | None = None
    collinear_neighbours: int = 0
    evidence: tuple[str, ...] = ()
    why: str = ""

    @property
    def length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    @property
    def is_wall_like(self) -> bool:
        return self.stroke_class in WALL_LIKE_CLASSES

    def record(self) -> dict:
        return {"stroke_id": self.stroke_id, "population": POPULATION,
                "stroke_class": self.stroke_class,
                "axis": self.axis, "fixed_mm": round(self.fixed_mm, 1),
                "start_mm": round(self.start_mm, 1),
                "end_mm": round(self.end_mm, 1),
                "length_mm": round(self.length_mm, 1),
                "stroke_width_pt": self.stroke_width_pt,
                "raster_support": self.raster_support,
                "nearest_band_id": self.nearest_band_id,
                "nearest_band_gap_mm": (
                    None if self.nearest_band_gap_mm is None
                    else round(self.nearest_band_gap_mm, 1)),
                "collinear_neighbours": self.collinear_neighbours,
                "is_wall_like": self.is_wall_like,
                "evidence": list(self.evidence), "why": self.why}


def classify(faces, bands, *, raster_support=None, wall_pen: float | None = None
             ) -> list:
    """Classify each unpaired wall-pen face. Evidence, never pen weight alone.

    `faces` are the wall-pen face candidates that did NOT become a band.
    `raster_support(axis, fixed, lo, hi) -> ratio | None` is optional.
    """
    by_line: dict = {}
    for f in faces:
        by_line.setdefault((f.axis, round(f.fixed_mm)), []).append(f)

    band_lines: dict = {}
    for b in bands:
        if b.wall_face_separation_mm is None:
            continue
        for at in (b.face_a_mm, b.face_b_mm):
            if at is not None:
                band_lines.setdefault(b.axis, []).append((at, b))

    out = []
    for f in faces:
        lo, hi = min(f.start_mm, f.end_mm), max(f.start_mm, f.end_mm)
        length = hi - lo
        ev = []
        if wall_pen is not None and abs(
                (f.stroke_width_pt or 0.0) - wall_pen) < 1e-6:
            ev.append("DRAWN_WITH_THE_WALL_PEN")

        # Nearest accepted band FACE on the same axis.
        near_id, near_gap = "", None
        for at, b in band_lines.get(f.axis, ()):
            d = abs(at - f.fixed_mm)
            if near_gap is None or d < near_gap:
                near_id, near_gap = b.wall_band_id, d

        peers = [g for g in by_line.get((f.axis, round(f.fixed_mm)), ())
                 if g is not f]
        dup = any(abs(min(g.start_mm, g.end_mm) - lo) < DUPLICATE_TOL_MM
                  and abs(max(g.start_mm, g.end_mm) - hi) < DUPLICATE_TOL_MM
                  for g in peers)
        support = (raster_support(f.axis, f.fixed_mm, lo, hi)
                   if raster_support is not None else None)
        if support is not None and support >= MIN_RASTER_SUPPORT:
            ev.append("RASTER_SHOWS_SOLID_HERE")
        if peers:
            ev.append("COLLINEAR_NEIGHBOURS_ON_THIS_LINE")

        # The nearest PARALLEL face on a different line whose run overlaps
        # this one: the mate a single-line wall is defined by not having.
        par = None
        for g in faces:
            if g is f or g.axis != f.axis:
                continue
            d = abs(g.fixed_mm - f.fixed_mm)
            if d < 1e-6:
                continue
            g_lo = min(g.start_mm, g.end_mm)
            g_hi = max(g.start_mm, g.end_mm)
            if g_hi < lo or g_lo > hi:
                continue
            if par is None or d < par:
                par = d
        if par is not None and par <= PARALLEL_FACE_REACH_MM:
            ev.append(f"A_PARALLEL_FACE_LIES_{par:.0f}_MM_AWAY")
        pen_match = (None if wall_pen is None else
                     abs((f.stroke_width_pt or 0.0) - wall_pen) < 1e-6)
        # Does anything MEET this run? A perpendicular face crossing it, or
        # a band ending at it. A wall is part of a wall network.
        meets = 0
        for g in faces:
            if g is f:
                continue
            if g.axis == f.axis:
                continue
            g_lo = min(g.start_mm, g.end_mm)
            g_hi = max(g.start_mm, g.end_mm)
            if (g_lo - NETWORK_REACH_MM <= f.fixed_mm
                    <= g_hi + NETWORK_REACH_MM
                    and lo - NETWORK_REACH_MM <= g.fixed_mm
                    <= hi + NETWORK_REACH_MM):
                meets += 1
                if meets >= 2:
                    break
        if meets:
            ev.append(f"{meets}_PERPENDICULAR_FACE_S_MEET_THIS_RUN")

        cls, why = _classify_one(
            length=length, dup=dup, near_gap=near_gap, support=support,
            peers=len(peers), pen_match=pen_match,
            pen_pt=f.stroke_width_pt, parallel_mm=par, meets=meets)
        out.append(UnpairedStroke(
            stroke_id=getattr(f, "segment_id", "") or getattr(f, "face_id", ""),
            axis=f.axis, fixed_mm=f.fixed_mm, start_mm=lo, end_mm=hi,
            stroke_class=cls, stroke_width_pt=f.stroke_width_pt,
            raster_support=(None if support is None else round(support, 3)),
            nearest_band_id=near_id,
            nearest_band_gap_mm=near_gap, collinear_neighbours=len(peers),
            evidence=tuple(ev), why=why))
    return out


def _classify_one(*, length: float, dup: bool, near_gap, support, peers: int,
                  pen_match: bool | None = None, pen_pt=None,
                  parallel_mm=None, meets: int | None = None
                  ) -> tuple[str, str]:
    """The decision, in the order the evidence actually settles it.

    Two requirements were missing and a blind sample of the population
    exposed both. Of 434.8 m once called CONFIRMED_SINGLE_LINE_WALL, only
    155.6 m was drawn with this drawing's wall pen, and several members had
    a parallel face 40-250 mm away — which is the one thing a single-line
    wall is defined by not having.
    """
    if dup:
        return DUPLICATE, (
            "another stroke on this line has the same extent: one mark found "
            "twice, not two walls")
    if length < MIN_WALL_RUN_MM:
        return ANNOTATION_OR_DETAIL, (
            f"{length:.0f} mm long. No wall in a villa is that short, "
            "whatever pen drew it")
    if near_gap is not None and near_gap < FRAGMENT_REACH_MM:
        return FRAGMENTED_MATE, (
            f"{near_gap:.1f} mm from an accepted band's own face: this is a "
            "fragment of that wall's mate, not a separate wall. Recovering it "
            "would extend an existing band rather than add a new one")
    if support is not None and support < MIN_RASTER_SUPPORT:
        return NON_WALL_GEOMETRY, (
            f"raster support {support:.2f}: nothing solid is drawn along this "
            "line, so the stroke outlines something other than masonry")
    if length > MAX_WALL_RUN_MM:
        return ANNOTATION_OR_DETAIL, (
            f"{length / 1000:.1f} m as ONE unbroken run. No wall on a villa "
            "floor is drawn that way: this is a grid line, a section marker "
            "or a sheet border")
    if parallel_mm is not None and parallel_mm <= PARALLEL_FACE_REACH_MM:
        return STROKE_UNRESOLVED, (
            f"a parallel face lies {parallel_mm:.0f} mm away along this run, "
            "so this is not a single-line wall — it is one side of a "
            "candidate PAIR the band engine did not accept. Why it did not "
            "is a pairing question, and guessing the answer here would put "
            "the stroke in the wrong population")
    if pen_match is False:
        return STROKE_UNRESOLVED, (
            f"drawn at {pen_pt} pt, and this drawing's wall pen is not that. "
            "A mark in a different pen may still be a wall in some "
            "conventions, so this is UNRESOLVED and not non-wall — but it "
            "does not support the EXISTENCE of a wall on its own")
    if meets == 0:
        return NON_WALL_GEOMETRY, (
            f"a {length / 1000:.1f} m run that NOTHING meets: no wall face "
            "and no accepted band terminates at it or crosses it anywhere "
            "along its length. A wall is part of a wall network — a "
            "partition runs between other walls. This is a sheet border, a "
            "grid line or a section marker")
    if support is not None and support >= MIN_RASTER_SUPPORT and peers == 0:
        return SINGLE_LINE_EXISTENCE_SUPPORTED, (
            f"a lone run of {length:.0f} mm with raster support "
            f"{support:.2f} and no mate anywhere on its line: drawn as ONE "
            "line and solid on the sheet. That supports the EXISTENCE of a "
            "separator along this line and nothing more — a single stroke "
            "establishes no thickness and no finish-face position, so this "
            "may become a TOPOLOGY_SEPARATOR_HYPOTHESIS and may NOT create "
            "material geometry")
    if peers >= 2:
        return FIXTURE_OR_SYMBOL, (
            f"{peers} other strokes share this line: a fixture outline, a "
            "hatch or a block, rather than a wall face")
    return STROKE_UNRESOLVED, (
        f"{length:.0f} mm, nearest band face "
        f"{'unknown' if near_gap is None else format(near_gap, '.0f') + ' mm'}"
        f", raster support {'unmeasured' if support is None else support}. "
        "Not enough to classify, and a guess here would become a wall")


def summary(strokes) -> dict:
    """The population, by class and by LENGTH — length is what matters."""
    by_class: dict = {}
    for s in strokes:
        d = by_class.setdefault(s.stroke_class, {"count": 0, "length_m": 0.0})
        d["count"] += 1
        d["length_m"] += s.length_mm / 1000
    for d in by_class.values():
        d["length_m"] = round(d["length_m"], 1)
    wall_like = [s for s in strokes if s.is_wall_like]
    return {
        "population": POPULATION,
        "strokes": len(strokes),
        "total_length_m": round(
            sum(s.length_mm for s in strokes) / 1000, 1),
        "by_class": dict(sorted(by_class.items(),
                                key=lambda kv: -kv[1]["length_m"])),
        "wall_like_strokes": len(wall_like),
        "wall_like_length_m": round(
            sum(s.length_mm for s in wall_like) / 1000, 1),
        "unresolved": sum(1 for s in strokes
                          if s.stroke_class == STROKE_UNRESOLVED),
        # THREE groups, kept apart. An earlier report added them together
        # and called the sum "never a wall", which silently converted
        # UNRESOLVED from unknown into false. Unknown is not a verdict.
        "not_wall_like_length_m": {
            "classified_non_wall": round(sum(
                s.length_mm for s in strokes
                if s.stroke_class in (FIXTURE_OR_SYMBOL,
                                      ANNOTATION_OR_DETAIL,
                                      NON_WALL_GEOMETRY)) / 1000, 1),
            "duplicate": round(sum(
                s.length_mm for s in strokes
                if s.stroke_class == DUPLICATE) / 1000, 1),
            "unresolved": round(sum(
                s.length_mm for s in strokes
                if s.stroke_class == STROKE_UNRESOLVED) / 1000, 1),
        },
        "what_each_group_means": {
            "classified_non_wall": (
                "evidence says this mark outlines something that is not "
                "masonry"),
            "duplicate": (
                "one mark found twice. NOT a statement that it is not a "
                "wall — it is a statement that it is not an ADDITIONAL "
                "wall"),
            "unresolved": (
                "not enough evidence to classify. This length is NOT proven "
                "non-wall and must never be added to the non-wall total. It "
                "sits in neither the wall-like nor the non-wall figure on "
                "purpose"),
        },
        "note": ("classified on evidence. Pen weight alone says a mark was "
                 "drawn with the wall pen and nothing about whether it is a "
                 "wall — and only the wall-like classes are candidates for "
                 "recovery"),
    }
