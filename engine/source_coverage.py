"""E73 — coverage measured in ONE primitive, because the last one was not.

The previous figure was:

    DRAWING_WALL_REPRESENTATION_COVERAGE = 45.9%
      = 615.1 m paired WALL-BAND length
      / (615.1 m band + 723.8 m wall-like SOURCE-STROKE length)

Those two terms count different things. A two-face wall contributes roughly
TWO source-face lengths and ONE band length, so the numerator was
deduplicated and the denominator was not. The ratio is not a coverage: it
understates capture by about a factor of two on exactly the population it
claims to measure.

So every term here is SOURCE STROKE LENGTH — the length of marks as the
drawing contains them, before any pairing, deduplication or interpretation.
The parts must add up to the total, and the residual is reported rather than
absorbed, because an accounting identity that nobody checks is where a
missing population hides.

A physical-wall length is reported SEPARATELY and only where deduplication
is reliable: an accepted two-face band is two strokes describing one wall,
so its band length is a physical length. No physical-wall length is derived
for the unpaired population at all — a single stroke does not establish a
wall, and NEVER INVENT THE MISSING HALF applies to length as much as to
thickness.
"""

from __future__ import annotations

from dataclasses import dataclass, field

PRIMITIVE = "SOURCE_WALL_STYLE_STROKE_LENGTH_MM"

# The metric names, spelled out so a reader can grep for them and find this
# module rather than a percentage with no denominator.
TOTAL = "SOURCE_WALL_STYLE_STROKE_LENGTH_TOTAL"
USED_IN_BANDS = "SOURCE_STROKE_LENGTH_USED_IN_ACCEPTED_BANDS"
SINGLE_LINE = "SOURCE_STROKE_LENGTH_CLASSIFIED_SINGLE_LINE"
FRAGMENTED = "SOURCE_STROKE_LENGTH_FRAGMENTED_MATE"
OTHER_REPRESENTATION = "SOURCE_STROKE_LENGTH_DIFFERENT_REPRESENTATION"
NON_WALL = "SOURCE_STROKE_LENGTH_NON_WALL"
DUPLICATE = "SOURCE_STROKE_LENGTH_DUPLICATE"
UNRESOLVED = "SOURCE_STROKE_LENGTH_UNRESOLVED"
UNACCOUNTED = "SOURCE_STROKE_LENGTH_UNACCOUNTED"

# The accounting identity must close to within this. ABSOLUTE, in mm: a
# percentage would let a whole class of strokes go missing on a long sheet.
IDENTITY_TOLERANCE_MM = 1.0


class SourceCoverageError(RuntimeError):
    """A coverage figure was asked for that mixes primitives."""


@dataclass
class SourceCoverage:
    """Every length in source-stroke millimetres, and nothing else."""

    total_mm: float = 0.0
    used_in_bands_mm: float = 0.0
    single_line_mm: float = 0.0
    fragmented_mate_mm: float = 0.0
    different_representation_mm: float = 0.0
    non_wall_mm: float = 0.0
    duplicate_mm: float = 0.0
    unresolved_mm: float = 0.0
    # Physical wall length, deduplicated, reported separately.
    accepted_band_length_mm: float = 0.0
    accepted_bands: int = 0
    notes: dict = field(default_factory=dict)

    @property
    def accounted_mm(self) -> float:
        return (self.used_in_bands_mm + self.single_line_mm
                + self.fragmented_mate_mm
                + self.different_representation_mm + self.non_wall_mm
                + self.duplicate_mm + self.unresolved_mm)

    @property
    def unaccounted_mm(self) -> float:
        return self.total_mm - self.accounted_mm

    @property
    def identity_closes(self) -> bool:
        return abs(self.unaccounted_mm) <= IDENTITY_TOLERANCE_MM

    def _pct(self, value: float) -> float | None:
        if self.total_mm <= 0.0:
            return None
        return round(100.0 * value / self.total_mm, 2)

    @property
    def wall_like_mm(self) -> float:
        """Strokes evidence says could be wall, INCLUDING the paired ones."""
        return (self.used_in_bands_mm + self.single_line_mm
                + self.fragmented_mate_mm
                + self.different_representation_mm)

    def record(self) -> dict:
        return {
            "primitive": PRIMITIVE,
            "why_one_primitive": (
                "a two-face wall contributes about two source-face lengths "
                "and one band length. Dividing a band length by a source "
                "length is not a coverage figure: it understates capture by "
                "roughly a factor of two on the very population it claims "
                "to measure"),
            "lengths_m": {
                TOTAL: round(self.total_mm / 1000, 1),
                USED_IN_BANDS: round(self.used_in_bands_mm / 1000, 1),
                SINGLE_LINE: round(self.single_line_mm / 1000, 1),
                FRAGMENTED: round(self.fragmented_mate_mm / 1000, 1),
                OTHER_REPRESENTATION: round(
                    self.different_representation_mm / 1000, 1),
                NON_WALL: round(self.non_wall_mm / 1000, 1),
                DUPLICATE: round(self.duplicate_mm / 1000, 1),
                UNRESOLVED: round(self.unresolved_mm / 1000, 1),
                UNACCOUNTED: round(self.unaccounted_mm / 1000, 1),
            },
            "share_of_source_stroke_length_pct": {
                USED_IN_BANDS: self._pct(self.used_in_bands_mm),
                SINGLE_LINE: self._pct(self.single_line_mm),
                FRAGMENTED: self._pct(self.fragmented_mate_mm),
                OTHER_REPRESENTATION: self._pct(
                    self.different_representation_mm),
                NON_WALL: self._pct(self.non_wall_mm),
                DUPLICATE: self._pct(self.duplicate_mm),
                UNRESOLVED: self._pct(self.unresolved_mm),
                UNACCOUNTED: self._pct(self.unaccounted_mm),
            },
            "source_stroke_capture": {
                "used_in_accepted_bands_pct": self._pct(
                    self.used_in_bands_mm),
                "of_wall_like_source_stroke_pct": (
                    None if self.wall_like_mm <= 0.0 else
                    round(100.0 * self.used_in_bands_mm / self.wall_like_mm,
                          2)),
                "wall_like_source_stroke_m": round(
                    self.wall_like_mm / 1000, 1),
                "basis": ("both terms are SOURCE STROKE LENGTH. The second "
                          "figure excludes strokes evidence says were never "
                          "wall, and leaves UNRESOLVED out of both terms "
                          "rather than choosing a side for it"),
            },
            "accounting_identity": {
                "closes": self.identity_closes,
                "total_mm": round(self.total_mm, 1),
                "accounted_mm": round(self.accounted_mm, 1),
                "unaccounted_mm": round(self.unaccounted_mm, 1),
                "tolerance_mm": IDENTITY_TOLERANCE_MM,
                "why": ("the parts must add to the total. An identity nobody "
                        "checks is where a missing population hides"),
            },
            "physical_wall_length": {
                "metric": "PHYSICAL_WALL_LENGTH_FROM_ACCEPTED_BANDS",
                "length_m": round(self.accepted_band_length_mm / 1000, 1),
                "bands": self.accepted_bands,
                "deduplication_basis": "TWO_DRAWN_FACES_ARE_ONE_WALL",
                "why_this_is_separate": (
                    "this is a deduplicated PHYSICAL length and the figures "
                    "above are SOURCE STROKE lengths. They may never be "
                    "divided into one another"),
                "not_derived_for": (
                    "the unpaired population. A single stroke does not "
                    "establish a wall's thickness or its faces, so it has no "
                    "physical length here — NEVER INVENT THE MISSING HALF "
                    "applies to length as much as to thickness"),
            },
            "notes": dict(self.notes),
        }


def measure(faces, bands, strokes) -> SourceCoverage:
    """Source-stroke lengths, by what became of each stroke.

    `faces` is every wall-style source face considered. `bands` are the
    accepted bands, which name the faces they consumed. `strokes` are the
    classified unpaired strokes.
    """
    from engine.unpaired_strokes import (ANNOTATION_OR_DETAIL,
                                         CONFIRMED_SINGLE_LINE_WALL,
                                         DIFFERENT_WALL_REPRESENTATION,
                                         DUPLICATE as CLS_DUPLICATE,
                                         FIXTURE_OR_SYMBOL,
                                         FRAGMENTED_MATE, NON_WALL_GEOMETRY,
                                         STROKE_UNRESOLVED)

    def _len(face) -> float:
        lo = min(face.start_mm, face.end_mm)
        hi = max(face.start_mm, face.end_mm)
        return hi - lo

    by_id = {}
    for f in faces:
        fid = getattr(f, "segment_id", "") or getattr(f, "face_id", "")
        if fid:
            by_id[fid] = _len(f)

    cov = SourceCoverage(total_mm=sum(by_id.values()))

    consumed = set()
    for b in bands:
        for fid in tuple(b.face_a_ids) + tuple(b.face_b_ids):
            consumed.add(fid)
    cov.used_in_bands_mm = sum(by_id.get(i, 0.0) for i in consumed)
    cov.accepted_bands = len(list(bands))
    cov.accepted_band_length_mm = sum(
        abs(b.end_mm - b.start_mm) for b in bands)

    buckets = {
        CONFIRMED_SINGLE_LINE_WALL: "single_line_mm",
        FRAGMENTED_MATE: "fragmented_mate_mm",
        DIFFERENT_WALL_REPRESENTATION: "different_representation_mm",
        FIXTURE_OR_SYMBOL: "non_wall_mm",
        ANNOTATION_OR_DETAIL: "non_wall_mm",
        NON_WALL_GEOMETRY: "non_wall_mm",
        CLS_DUPLICATE: "duplicate_mm",
        STROKE_UNRESOLVED: "unresolved_mm",
    }
    for s in strokes:
        # A stroke that ALSO reached a band is already counted there; the
        # classified population is the unpaired one, so this is a guard
        # against double counting rather than an expected case.
        if s.stroke_id in consumed:
            continue
        attr = buckets.get(s.stroke_class)
        if attr is None:
            continue
        setattr(cov, attr, getattr(cov, attr) + (s.end_mm - s.start_mm))

    cov.notes["classified_strokes"] = len(list(strokes))
    cov.notes["source_faces"] = len(by_id)
    cov.notes["faces_consumed_by_bands"] = len(consumed & set(by_id))
    if not cov.identity_closes:
        cov.notes["identity_warning"] = (
            f"{cov.unaccounted_mm / 1000:.1f} m of source stroke length is "
            "in neither an accepted band nor a classified stroke. That "
            "population exists and is unnamed")
    return cov
