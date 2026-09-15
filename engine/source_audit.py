"""E65 — what a drawing is MADE OF, before anyone measures anything with it.

Two jobs, both about not fooling ourselves.

FIRST, the CAD oracle. A DXF/DWG of the same sheet answers the question every
failure so far has been ambiguous about: is the PDF reconstruction wrong, or
does the drawing genuinely look like that? The oracle runs AFTER the PDF output
is generated and frozen, and it is FORBIDDEN from feeding back into the same
run. It is a test fixture, not a product path — clients send PDFs.

SECOND, the source representation audit. Every tolerance in this engine was
chosen while looking at AR-00, and the wall-band abstraction assumes two-line
walls. Before a second project can be a generalisation test, we have to know
whether it is even the same KIND of drawing. This audit answers that using no
benchmark at all: it counts representations, not errors.

    A SOURCE AUDIT MAY RUN ON PROJECT 2 NOW. A measurement may not.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# How walls appear on a sheet. The engine currently handles the first well.
DOUBLE_LINE_WALL = "DOUBLE_LINE_WALL"
SINGLE_LINE_WALL = "SINGLE_LINE_WALL"
# The unclassified population. A wall-pen stroke that did not pair is a
# stroke drawn with the wall pen — not a wall — until evidence says more.
UNPAIRED_WALL_STYLE_STROKE = "UNPAIRED_WALL_STYLE_STROKE"
FILLED_POCHE_WALL = "FILLED_OR_POCHE_WALL"
HATCHED_WALL = "HATCHED_WALL"
REPRESENTATION_UNKNOWN = "REPRESENTATION_UNKNOWN"

WALL_REPRESENTATIONS = (DOUBLE_LINE_WALL, SINGLE_LINE_WALL,
                        FILLED_POCHE_WALL, HATCHED_WALL,
                        UNPAIRED_WALL_STYLE_STROKE,
                        REPRESENTATION_UNKNOWN)

SUPPORTED_REPRESENTATIONS = (DOUBLE_LINE_WALL,)

# What the audit concludes about whether this engine can read the drawing at
# all. Stated before any measurement is attempted.
SUPPORTABLE = "SUPPORTABLE_BY_THE_CURRENT_ENGINE"
PARTIALLY_SUPPORTABLE = "PARTIALLY_SUPPORTABLE"
UNSUPPORTED = "UNSUPPORTED_REPRESENTATION"


class SourceAuditError(RuntimeError):
    """An oracle or audit was asked to influence the run it is judging."""


@dataclass(frozen=True)
class SourceAudit:
    """What one drawing is made of. No areas, no errors, no benchmark."""

    drawing_id: str
    revision: str
    source_hash: str
    paths: int = 0
    segments: int = 0
    curves: int = 0
    axis_aligned: int = 0
    diagonal: int = 0
    text_objects: int = 0
    glyph_outline_paths: int = 0
    stroke_width_histogram: dict = field(default_factory=dict)
    heavy_pen_pt: float | None = None
    paired_face_length_m: float | None = None
    # NOT "single line wall length". The stroke weight says a mark was drawn
    # with the wall pen and nothing more, so this is the length of the
    # population and the classification of it is separate.
    unpaired_wall_style_stroke_length_m: float | None = None
    unpaired_stroke_classification: dict = field(default_factory=dict)
    wall_representation_mix: dict = field(default_factory=dict)
    dimension_representation: str = ""
    block_or_symbol_paths: int = 0
    verdict: str = REPRESENTATION_UNKNOWN
    why: str = ""

    def _coverage_claim(self) -> dict:
        """What share of the DRAWING's wall reached the accepted band set.

        This is the figure a reader will want and the one most easily
        overclaimed. It is only meaningful once the unpaired wall-style
        stroke population has been classified, because until then the
        denominator is unknown: an unpaired stroke may be a missing wall or
        a fixture outline that was never a wall at all.
        """
        cls = self.unpaired_stroke_classification
        if not cls or self.paired_face_length_m is None:
            return {"status": "NOT_ESTABLISHED",
                    "why": ("the unpaired wall-style stroke population is "
                            "not classified, so the denominator is unknown. "
                            "No percentage here may be read as walls "
                            "captured")}
        wall_like = cls.get("wall_like_length_m")
        if wall_like is None:
            return {"status": "NOT_ESTABLISHED",
                    "why": "the classification reports no wall-like length"}
        denom = self.paired_face_length_m + wall_like
        return {
            "status": "ESTABLISHED_AGAINST_A_CLASSIFIED_POPULATION",
            "paired_into_bands_m": round(self.paired_face_length_m, 1),
            "wall_like_but_unpaired_m": round(wall_like, 1),
            "pct": (None if not denom
                    else round(100 * self.paired_face_length_m / denom, 1)),
            "why": ("the denominator counts only the unpaired strokes that "
                    "evidence says could be wall. Strokes classified as "
                    "fixture, duplicate, annotation or non-wall geometry are "
                    "excluded, because counting them would understate "
                    "capture by blaming the engine for marks that are not "
                    "walls"),
            "still_not_a_claim_that": (
                "this share of the ARCHITECTURAL walls is captured. It is a "
                "share of wall-pen stroke length, and a wall drawn in a "
                "representation this engine does not read at all would not "
                "appear in either term"),
        }

    def record(self) -> dict:
        return {"drawing_id": self.drawing_id, "revision": self.revision,
                "source_hash": self.source_hash,
                "paths": self.paths, "segments": self.segments,
                "curves": self.curves,
                "axis_aligned_segments": self.axis_aligned,
                "diagonal_segments": self.diagonal,
                "text_objects": self.text_objects,
                "glyph_outline_paths": self.glyph_outline_paths,
                "stroke_width_histogram": dict(self.stroke_width_histogram),
                "heavy_pen_pt": self.heavy_pen_pt,
                "paired_face_length_m": self.paired_face_length_m,
                "unpaired_wall_style_stroke_length_m":
                    self.unpaired_wall_style_stroke_length_m,
                "unpaired_stroke_classification": dict(
                    self.unpaired_stroke_classification),
                "wall_representation_mix": dict(self.wall_representation_mix),
                "drawing_wall_representation_coverage": (
                    self._coverage_claim()),
                "dimension_representation": self.dimension_representation,
                "block_or_symbol_paths": self.block_or_symbol_paths,
                "verdict": self.verdict, "why": self.why,
                "contains_no_measurement": True,
                "note": ("representation counts only. This audit may run on "
                         "an unseen project without spending its benchmark")}


def audit_drawing(drawing, *, drawing_id: str, revision: str,
                  source_hash: str, bands=None, rejections=None,
                  unpaired_strokes=None) -> SourceAudit:
    """Count what the sheet is made of. Nothing here measures a room."""
    segs = drawing.segments
    axis = [s for s in segs if s.is_axis_aligned]
    diag = [s for s in segs if not s.is_axis_aligned]
    widths = Counter(round(s.stroke_width_pt, 2) for s in axis)
    # The pen carrying the most axis-aligned LENGTH, not the most marks — and
    # STROKED marks only. A filled rectangle reports width 0.0 and would win
    # on length alone while telling us nothing about the drawing's pen.
    stroked = [s for s in axis if s.stroke_width_pt > 0]
    heavy = None
    if stroked:
        by_len: dict = {}
        for s in stroked:
            by_len[round(s.stroke_width_pt, 2)] = (
                by_len.get(round(s.stroke_width_pt, 2), 0.0) + s.length_mm)
        heavy = max(by_len, key=by_len.get)

    paired = single = None
    mix: dict = {}
    if bands is not None:
        paired = sum(abs(b.end_mm - b.start_mm) for b in bands
                     if b.wall_face_separation_mm is not None) / 1000
        mix[DOUBLE_LINE_WALL] = round(paired, 1)
    stroke_cls: dict = {}
    if rejections is not None:
        single = sum(getattr(r, "length_mm", 0.0) for r in rejections) / 1000
        # The population, named for what is known about it. Calling this
        # length SINGLE_LINE_WALL was a guess dressed as a measurement.
        mix[UNPAIRED_WALL_STYLE_STROKE] = round(single, 1)
    if unpaired_strokes is not None:
        from engine.unpaired_strokes import (CONFIRMED_SINGLE_LINE_WALL,
                                              summary as stroke_summary)
        stroke_cls = dict(stroke_summary(unpaired_strokes))
        per = stroke_cls.get("by_class", {})
        # Only the class evidence actually confirmed enters the
        # representation mix as single-line wall. The rest of the population
        # stays in UNPAIRED_WALL_STYLE_STROKE, which is what is known.
        mix[SINGLE_LINE_WALL] = per.get(
            CONFIRMED_SINGLE_LINE_WALL, {}).get("length_m", 0.0)

    # The support share is judged against WALL-LIKE unpaired length when the
    # population has been classified, and against the whole population when
    # it has not — a drawing whose unpaired strokes turn out to be fixtures
    # is not a drawing this engine cannot read.
    unpaired_term = (stroke_cls.get("wall_like_length_m")
                     if stroke_cls else single)
    total = (paired or 0.0) + (unpaired_term or 0.0)
    share = (paired or 0.0) / total if total else 0.0
    if bands is None or rejections is None:
        verdict, why = REPRESENTATION_UNKNOWN, (
            "no wall extraction was run, so the representation mix is not "
            "established. The counts above still say what the sheet contains")
    elif share >= 0.7:
        verdict, why = SUPPORTABLE, (
            f"{share * 100:.0f}% of wall-pen face length pairs into two-face "
            "bands, which is the representation this engine reads")
    elif share >= 0.3:
        if stroke_cls:
            per = stroke_cls.get("by_class", {})
            named = ", ".join(
                f"{k} {v['length_m']:.0f} m"
                for k, v in list(per.items())[:4])
            why = (f"{share * 100:.0f}% of WALL-LIKE wall-pen face length "
                   "pairs into a two-face band. The unpaired remainder has "
                   f"been classified — {named} — so the shortfall is not a "
                   "mystery: it is mostly wall that IS drawn and did not "
                   "pair, which is a different repair from wall that is not "
                   "drawn at all")
        else:
            why = (f"only {share * 100:.0f}% of wall-pen face length pairs "
                   "into a two-face band. The unpaired remainder is either "
                   "single-line wall, filled wall, or wall-pen marks that "
                   "are not walls — and the three need telling apart before "
                   "more measurement is built on the paired population "
                   "alone")
        verdict = PARTIALLY_SUPPORTABLE
    else:
        verdict, why = UNSUPPORTED, (
            f"{share * 100:.0f}% pairs into two-face bands. This drawing is "
            "probably not double-line, and measuring it with the current "
            "engine would produce confident nonsense")

    return SourceAudit(
        drawing_id=drawing_id, revision=revision, source_hash=source_hash,
        paths=len(drawing.paths), segments=len(segs),
        curves=len(getattr(drawing, "curves", ())),
        axis_aligned=len(axis), diagonal=len(diag),
        text_objects=0,
        glyph_outline_paths=len({c.path_id for c in
                                 getattr(drawing, "curves", ())}),
        stroke_width_histogram={str(k): v for k, v in widths.most_common(10)},
        heavy_pen_pt=heavy,
        paired_face_length_m=(None if paired is None else round(paired, 1)),
        unpaired_wall_style_stroke_length_m=(
            None if single is None else round(single, 1)),
        unpaired_stroke_classification=stroke_cls,
        wall_representation_mix=mix,
        dimension_representation=("NOT_EXTRACTED — see "
                                  "engine.document_observations"),
        block_or_symbol_paths=len({c.path_id for c in
                                   getattr(drawing, "curves", ())}),
        verdict=verdict, why=why)


# ------------------------------------------------------------- the CAD oracle

ORACLE_ABSENT = "CAD_SOURCE_NOT_AVAILABLE"
ORACLE_READY = "CAD_ORACLE_READY"

PDF_ADAPTER_WRONG = "PDF_ADAPTER_WRONG"
DRAWING_REALLY_IS_LIKE_THAT = "DRAWING_REALLY_IS_LIKE_THAT"
ORACLE_UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class CadOracleCompare:
    """A comparison against CAD, run AFTER the PDF result is frozen.

    The direction is the whole discipline. The oracle answers *which* of two
    explanations a PDF failure has — the adapter is wrong, or the drawing
    genuinely contains that — and it may never be consulted while the PDF
    result is still being produced.
    """

    status: str = ORACLE_ABSENT
    pdf_run_hash: str = ""
    cad_source_hash: str = ""
    wall_presence: dict = field(default_factory=dict)
    wall_face_location: dict = field(default_factory=dict)
    wall_thickness: dict = field(default_factory=dict)
    openings: dict = field(default_factory=dict)
    space_boundaries: dict = field(default_factory=dict)
    verdict: str = ORACLE_UNRESOLVED
    why: str = ""

    def record(self) -> dict:
        return {"status": self.status, "pdf_run_hash": self.pdf_run_hash,
                "cad_source_hash": self.cad_source_hash,
                "wall_presence": dict(self.wall_presence),
                "wall_face_location": dict(self.wall_face_location),
                "wall_thickness": dict(self.wall_thickness),
                "openings": dict(self.openings),
                "space_boundaries": dict(self.space_boundaries),
                "verdict": self.verdict,
                "fed_back_into_the_pdf_run": False,
                "why": self.why}


def cad_oracle(*, cad_path: str | None, pdf_run_hash: str) -> CadOracleCompare:
    """Hook only. Returns ORACLE_ABSENT until a CAD source exists.

    Deliberately inert rather than absent: the shape of the comparison is
    fixed now, so when the DXF arrives it cannot quietly become an input.
    """
    if not cad_path:
        return CadOracleCompare(
            status=ORACLE_ABSENT, pdf_run_hash=pdf_run_hash,
            verdict=ORACLE_UNRESOLVED,
            why=("no DXF/DWG of this sheet is available, so every PDF failure "
                 "remains ambiguous between 'the adapter is wrong' and 'the "
                 "drawing really is like that'. Obtaining it is the cheapest "
                 "way to remove that ambiguity, and it stays a TEST FIXTURE: "
                 "clients send PDFs"))
    raise SourceAuditError(
        "CAD ingestion is not implemented. It is deliberately a hook: adding "
        "it must be a separate, explicit step so it cannot become an input to "
        "the PDF run it is meant to judge")
