"""E63 — the data model for what a drawing SAYS, kept apart from what it shows.

Prepared now, extracted later. The point of writing the model before the
multimodal extraction exists is to fix the EVIDENCE ROLES first, because that
is where the temptation lies:

    PRINTED DIMENSION      ->  GEOMETRY / DOCUMENT evidence about SIZE
    ROOM LABEL / TAG       ->  SEMANTIC evidence about IDENTITY
    ROOM SCHEDULE ENTRY    ->  DOCUMENT evidence about IDENTITY
    DOOR / WINDOW SCHEDULE ->  DOCUMENT evidence about OPENINGS

A printed 3.50 that matches a measured 3497 mm is strong evidence the SIZE is
right. It says nothing whatever about which room it is: a bedroom and a
bathroom can both be 3.50 m wide. Letting a dimension match lift a room's
IDENTITY would be the WSH-01 error in a new costume — geometry agreeing, and
the name still wrong.

Nothing in this module reads a drawing. It defines what an observation is, what
it may be used for, and what it may not.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# What kind of thing was read off the sheet.
PRINTED_DIMENSION = "PRINTED_DIMENSION"
ROOM_LABEL = "ROOM_LABEL"
ROOM_SCHEDULE_ENTRY = "ROOM_SCHEDULE_ENTRY"
DOOR_SCHEDULE_ENTRY = "DOOR_SCHEDULE_ENTRY"
WINDOW_SCHEDULE_ENTRY = "WINDOW_SCHEDULE_ENTRY"
LEVEL_ANNOTATION = "LEVEL_ANNOTATION"

OBSERVATION_KINDS = (PRINTED_DIMENSION, ROOM_LABEL, ROOM_SCHEDULE_ENTRY,
                     DOOR_SCHEDULE_ENTRY, WINDOW_SCHEDULE_ENTRY,
                     LEVEL_ANNOTATION)

# What an observation may be used AS. This is the whole reason the module
# exists ahead of the extraction.
USE_FOR_SIZE = "SIZE_EVIDENCE"
USE_FOR_IDENTITY = "IDENTITY_EVIDENCE"
USE_FOR_OPENINGS = "OPENING_EVIDENCE"
USE_FOR_LEVELS = "LEVEL_EVIDENCE"

EVIDENCE_ROLE = {
    PRINTED_DIMENSION: (USE_FOR_SIZE,),
    ROOM_LABEL: (USE_FOR_IDENTITY,),
    ROOM_SCHEDULE_ENTRY: (USE_FOR_IDENTITY,),
    DOOR_SCHEDULE_ENTRY: (USE_FOR_OPENINGS,),
    WINDOW_SCHEDULE_ENTRY: (USE_FOR_OPENINGS,),
    LEVEL_ANNOTATION: (USE_FOR_LEVELS,),
}

# How the text reached us. Glyph outlines are the case a naive text extractor
# misses entirely — a drawing whose room names are vector outlines is not a
# drawing without room names.
TEXT_OBJECT = "PDF_TEXT_OBJECT"
GLYPH_OUTLINE = "VECTOR_GLYPH_OUTLINE"
RASTER_OCR = "RASTER_OCR"
CAD_ATTRIBUTE = "CAD_TEXT_ATTRIBUTE"
HUMAN_TRANSCRIPTION = "HUMAN_TRANSCRIPTION"

TEXT_SOURCES = (CAD_ATTRIBUTE, TEXT_OBJECT, GLYPH_OUTLINE, RASTER_OCR,
                HUMAN_TRANSCRIPTION)

UNPARSED = "UNPARSED"


class ObservationError(RuntimeError):
    """An observation was used as evidence for something it cannot support."""


@dataclass(frozen=True)
class PrintedDimensionObservation:
    """A dimension as PRINTED, not as measured.

    `parsed_value_mm` is None until somebody parses it, and None is not zero:
    an unparsed dimension is an observation whose value is unknown, which is a
    different thing from a dimension of zero.
    """

    observation_id: str
    raw_text: str
    parsed_value_mm: float | None = None
    unit_as_printed: str = ""
    orientation: str = ""                 # H, V, or a bearing
    anchor_mm: tuple | None = None        # where on the sheet it sits
    extent_mm: tuple | None = None        # what it dimensions, if known
    text_source: str = UNPARSED
    drawing_id: str = ""
    drawing_revision: str = ""
    confidence: float | None = None
    parse_note: str = ""

    @property
    def kind(self) -> str:
        return PRINTED_DIMENSION

    @property
    def is_parsed(self) -> bool:
        return self.parsed_value_mm is not None

    def may_be_used_for(self, use: str) -> bool:
        return use in EVIDENCE_ROLE[PRINTED_DIMENSION]

    def require_use(self, use: str) -> None:
        """Refuse the WSH-01 error in a new costume."""
        if not self.may_be_used_for(use):
            raise ObservationError(
                f"a printed dimension is {'/'.join(EVIDENCE_ROLE[PRINTED_DIMENSION])} "
                f"and may not be used as {use}. A printed 3.50 that matches a "
                "measured 3497 mm proves the SIZE is right and says nothing "
                "about WHICH ROOM it is: a bedroom and a bathroom can both be "
                "3.50 m wide")

    def record(self) -> dict:
        return {"observation_id": self.observation_id, "kind": self.kind,
                "raw_text": self.raw_text,
                "parsed_value_mm": self.parsed_value_mm,
                "unit_as_printed": self.unit_as_printed,
                "orientation": self.orientation,
                "anchor_mm": (None if self.anchor_mm is None
                              else [round(v, 1) for v in self.anchor_mm]),
                "extent_mm": (None if self.extent_mm is None
                              else [round(v, 1) for v in self.extent_mm]),
                "text_source": self.text_source,
                "drawing_id": self.drawing_id,
                "drawing_revision": self.drawing_revision,
                "confidence": self.confidence,
                "is_parsed": self.is_parsed,
                "evidence_roles": list(EVIDENCE_ROLE[PRINTED_DIMENSION]),
                "parse_note": self.parse_note}


@dataclass(frozen=True)
class TextObservation:
    """A label, tag or schedule row. Identity or opening evidence, never size."""

    observation_id: str
    kind: str
    raw_text: str
    anchor_mm: tuple | None = None
    text_source: str = UNPARSED
    drawing_id: str = ""
    drawing_revision: str = ""
    confidence: float | None = None
    fields: dict = field(default_factory=dict)

    def may_be_used_for(self, use: str) -> bool:
        return use in EVIDENCE_ROLE.get(self.kind, ())

    def require_use(self, use: str) -> None:
        if not self.may_be_used_for(use):
            raise ObservationError(
                f"a {self.kind} is {'/'.join(EVIDENCE_ROLE.get(self.kind, ()))} "
                f"and may not be used as {use}")

    def record(self) -> dict:
        return {"observation_id": self.observation_id, "kind": self.kind,
                "raw_text": self.raw_text,
                "anchor_mm": (None if self.anchor_mm is None
                              else [round(v, 1) for v in self.anchor_mm]),
                "text_source": self.text_source,
                "drawing_id": self.drawing_id,
                "drawing_revision": self.drawing_revision,
                "confidence": self.confidence,
                "evidence_roles": list(EVIDENCE_ROLE.get(self.kind, ())),
                "fields": dict(self.fields)}


def readiness(observations) -> dict:
    """What exists so far. Currently: the model, and no extraction."""
    obs = list(observations)
    return {
        "observations": len(obs),
        "by_kind": dict(Counter(getattr(o, "kind", "") for o in obs)),
        "by_text_source": dict(Counter(o.text_source for o in obs)),
        "parsed": sum(1 for o in obs if getattr(o, "is_parsed", False)),
        "evidence_roles": {k: list(v) for k, v in EVIDENCE_ROLE.items()},
        "extraction_status": ("MODEL_ONLY_NO_EXTRACTION_BUILT"
                             if not obs else "OBSERVATIONS_PRESENT"),
        "note": ("the roles are fixed before the extraction exists, because "
                 "that is where the temptation lies: a dimension match must "
                 "never lift a room's IDENTITY"),
    }
