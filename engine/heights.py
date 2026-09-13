"""E38 — Height registry.

A trade height is a project decision, never a number the engine knows. The Test 1
takeoff applied one 3.30 m height to an entire floor and every wall quantity on
that job was wrong by a constant; this module exists so that cannot be expressed.

Eight heights, independently sourced. Plaster runs to 3.20 m on project 23010 and
ceramic to 3.00 m, so a single `roomHeight` field cannot state the truth and is
not offered. Ceiling height and clear height are different questions again.

Every height carries where it came from, and `ASSUMED` is a first-class source
type precisely so that an assumption can be written down and then refused: an
assumed height may be recorded, may be reviewed, may be discussed — and can never
produce a releasable quantity. The alternative, which every estimating system
falls into eventually, is that a plausible number with no provenance becomes
indistinguishable from a measured one.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

# The eight heights, kept apart because they answer different questions.
STRUCTURAL_WALL = "structural_wall_height"
BLOCKWORK = "blockwork_height"
PLASTER = "plaster_height"
PAINT = "paint_height"
CERAMIC = "ceramic_height"
WATERPROOFING = "waterproofing_height"
CLEAR = "clear_height"
CEILING = "ceiling_height"

HEIGHT_NAMES = (STRUCTURAL_WALL, BLOCKWORK, PLASTER, PAINT, CERAMIC,
                WATERPROOFING, CLEAR, CEILING)

# Where a height may come from, strongest first. The order is the source
# hierarchy: a weaker source never overrides a stronger one silently.
SECTION_DRAWING = "SECTION_DRAWING"
SPECIFICATION = "SPECIFICATION"
OWNER_RULE = "OWNER_RULE"
SITE_MEASURED = "SITE_MEASURED"
ASSUMED = "ASSUMED"

SOURCE_TYPES = (SECTION_DRAWING, SPECIFICATION, OWNER_RULE, SITE_MEASURED, ASSUMED)
SOURCE_RANK = {t: i for i, t in enumerate(SOURCE_TYPES)}

# ASSUMED is deliberately absent. It is a source type so an assumption can be
# recorded honestly; it is not a source that may produce money.
RELEASABLE_SOURCES = frozenset({SECTION_DRAWING, SPECIFICATION, OWNER_RULE,
                                SITE_MEASURED})

VALIDATED = "VALIDATED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
REJECTED = "REJECTED"
VALIDATION_STATES = (VALIDATED, REVIEW_REQUIRED, REJECTED)

# Why a height cannot be used, in a form a router can act on.
HEIGHT_REQUIRED = "HEIGHT_REQUIRED"


class HeightError(RuntimeError):
    """A height was asked for and no defensible one exists."""


@dataclass(frozen=True)
class Height:
    """One named height for one project, with its whole provenance."""

    height_id: str
    name: str
    value_m: Decimal
    source_type: str
    source: str                       # the human-readable citation
    drawing_id: str = ""
    revision: str = ""
    validation_status: str = REVIEW_REQUIRED
    unit: str = "m"
    note: str = ""

    def __post_init__(self) -> None:
        if self.name not in HEIGHT_NAMES:
            raise HeightError(
                f"{self.height_id}: {self.name!r} is not one of the eight named "
                f"heights {HEIGHT_NAMES}. A generic room height is the mistake "
                "this registry exists to prevent.")
        if self.source_type not in SOURCE_TYPES:
            raise HeightError(
                f"{self.height_id}: source_type {self.source_type!r} is not one of "
                f"{SOURCE_TYPES}")
        if self.validation_status not in VALIDATION_STATES:
            raise HeightError(
                f"{self.height_id}: validation_status {self.validation_status!r} "
                f"is not one of {VALIDATION_STATES}")
        if self.unit != "m":
            raise HeightError(
                f"{self.height_id}: heights are stored in metres, not {self.unit!r}")
        if self.value_m <= 0:
            raise HeightError(f"{self.height_id}: non-physical height {self.value_m}")
        if not self.source.strip():
            raise HeightError(
                f"{self.height_id}: a height with no citation is an assumption "
                "wearing a measurement's clothes — say where it came from.")
        if self.source_type in (SECTION_DRAWING,) and not self.drawing_id.strip():
            raise HeightError(
                f"{self.height_id}: source_type {SECTION_DRAWING} must name the "
                "drawing it was read from.")
        if self.source_type == ASSUMED and self.validation_status == VALIDATED:
            raise HeightError(
                f"{self.height_id}: an ASSUMED height cannot be VALIDATED. "
                "Recording the assumption is right; blessing it is not.")

    @property
    def releasable(self) -> bool:
        """May a quantity built on this height be released without a human?"""
        return (self.source_type in RELEASABLE_SOURCES
                and self.validation_status == VALIDATED)

    @property
    def block_reason(self) -> str:
        if self.releasable:
            return ""
        if self.source_type == ASSUMED:
            return (f"{self.height_id} is ASSUMED ({self.value_m} m, {self.source}). "
                    "An assumed height may be recorded and reviewed; it may never "
                    "produce a released quantity.")
        return (f"{self.height_id} is {self.validation_status} — "
                f"{self.value_m} m from {self.source_type}. An engineer validates "
                "it before it can carry a quantity.")

    def provenance(self) -> dict:
        return {
            "height_id": self.height_id, "name": self.name,
            "value_m": str(self.value_m), "unit": self.unit,
            "source_type": self.source_type, "source": self.source,
            "drawing_id": self.drawing_id, "revision": self.revision,
            "validation_status": self.validation_status,
            "releasable": self.releasable, "note": self.note,
        }


@dataclass
class HeightRegistry:
    """Every named height for one project. Silence is not a default."""

    project: str
    heights: dict[str, Height]
    version: str = "1.0"
    effective_from: str = ""

    def __post_init__(self) -> None:
        for name, h in self.heights.items():
            if name != h.name:
                raise HeightError(f"{name} is filed under the wrong name ({h.name})")

    @property
    def missing(self) -> list[str]:
        return [n for n in HEIGHT_NAMES if n not in self.heights]

    def get(self, name: str) -> Height:
        """The height, or a named refusal. Never 3.0, 3.2 or 3.3."""
        if name not in HEIGHT_NAMES:
            raise HeightError(f"{name!r} is not one of the eight named heights")
        if name not in self.heights:
            raise HeightError(
                f"{HEIGHT_REQUIRED}: project {self.project} has no {name}. "
                "No generic height is substituted — the Test 1 takeoff applied "
                "3.30 m to a whole floor for exactly this reason.")
        return self.heights[name]

    def for_release(self, name: str) -> Height:
        """The height, only if a quantity may actually be released on it."""
        h = self.get(name)
        if not h.releasable:
            raise HeightError(h.block_reason)
        return h

    def status(self) -> dict[str, str]:
        """What every trade would find if it asked right now."""
        out = {}
        for n in HEIGHT_NAMES:
            if n not in self.heights:
                out[n] = HEIGHT_REQUIRED
            else:
                h = self.heights[n]
                out[n] = "RELEASABLE" if h.releasable else h.validation_status
        return out

    @classmethod
    def from_dict(cls, data: dict) -> "HeightRegistry":
        heights = {}
        for name, h in data.get("heights", {}).items():
            heights[name] = Height(
                height_id=h.get("height_id", f"{data['project']}:{name}"),
                name=name,
                value_m=Decimal(str(h["value_m"])),
                source_type=h.get("source_type", ASSUMED),
                source=h.get("source", ""),
                drawing_id=h.get("drawing_id", ""),
                revision=h.get("revision", ""),
                validation_status=h.get("validation_status", REVIEW_REQUIRED),
                unit=h.get("unit", "m"),
                note=h.get("note", ""),
            )
        return cls(project=data["project"], heights=heights,
                   version=data.get("version", "1.0"),
                   effective_from=data.get("effective_from", ""))

    @classmethod
    def load(cls, path: str | Path) -> "HeightRegistry":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
