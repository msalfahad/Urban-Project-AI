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

from collections import Counter
from dataclasses import dataclass

POPULATION = "UNPAIRED_WALL_STYLE_STROKE"

CONFIRMED_SINGLE_LINE_WALL = "CONFIRMED_SINGLE_LINE_WALL"
FRAGMENTED_MATE = "FRAGMENTED_MATE"
DIFFERENT_WALL_REPRESENTATION = "DIFFERENT_WALL_REPRESENTATION"
FIXTURE_OR_SYMBOL = "FIXTURE_OR_SYMBOL"
ANNOTATION_OR_DETAIL = "ANNOTATION_OR_DETAIL"
DUPLICATE = "DUPLICATE"
NON_WALL_GEOMETRY = "NON_WALL_GEOMETRY"
STROKE_UNRESOLVED = "UNRESOLVED"

CLASSES = (CONFIRMED_SINGLE_LINE_WALL, FRAGMENTED_MATE,
           DIFFERENT_WALL_REPRESENTATION, FIXTURE_OR_SYMBOL,
           ANNOTATION_OR_DETAIL, DUPLICATE, NON_WALL_GEOMETRY,
           STROKE_UNRESOLVED)

# Only these classes are candidates for a missing wall worth recovering.
WALL_LIKE_CLASSES = (CONFIRMED_SINGLE_LINE_WALL, FRAGMENTED_MATE,
                     DIFFERENT_WALL_REPRESENTATION)

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

        cls, why = _classify_one(
            length=length, dup=dup, near_gap=near_gap, support=support,
            peers=len(peers))
        out.append(UnpairedStroke(
            stroke_id=getattr(f, "segment_id", "") or getattr(f, "face_id", ""),
            axis=f.axis, fixed_mm=f.fixed_mm, start_mm=lo, end_mm=hi,
            stroke_class=cls, stroke_width_pt=f.stroke_width_pt,
            raster_support=(None if support is None else round(support, 3)),
            nearest_band_id=near_id,
            nearest_band_gap_mm=near_gap, collinear_neighbours=len(peers),
            evidence=tuple(ev), why=why))
    return out


def _classify_one(*, length: float, dup: bool, near_gap, support, peers: int
                  ) -> tuple[str, str]:
    """The decision, in the order the evidence actually settles it."""
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
    if support is not None and support >= MIN_RASTER_SUPPORT and peers == 0:
        return CONFIRMED_SINGLE_LINE_WALL, (
            f"a lone run of {length:.0f} mm with raster support "
            f"{support:.2f} and no mate anywhere on its line: drawn as ONE "
            "line and solid on the sheet. This is the class the band engine "
            "cannot express")
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
        "note": ("classified on evidence. Pen weight alone says a mark was "
                 "drawn with the wall pen and nothing about whether it is a "
                 "wall — and only the wall-like classes are candidates for "
                 "recovery"),
    }
