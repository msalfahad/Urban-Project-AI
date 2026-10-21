"""Input/output contract for A1 — Extractor.

Dependency-free dataclasses. The Output validates itself so a malformed model
response fails before it can reach the engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

VALID_UNITS = {"count", "m", "m2", "m3", "kg"}
VALID_CONFIDENCE = {"high", "medium", "low"}

# How many dimensions each unit must have (kg comes from steel schedules, not
# from multiplying lengths, so it is exempt from the dimension-count check).
_DIMS_FOR_UNIT = {"count": 0, "m": 1, "m2": 2, "m3": 3}


@dataclass
class ExtractInput:
    """One drawing/schedule to read."""

    drawing_number: str
    sheet: str = ""
    revision: str = ""
    trade: str = ""
    # The actual image/text is supplied to the model by the runner; this record
    # is the metadata that travels with every extracted record.


@dataclass
class Measurement:
    description: str
    trade: str
    count: float
    dimensions_m: list[float]
    unit: str
    source_drawing: str = ""
    source_sheet: str = ""
    source_revision: str = ""
    confidence: str = "medium"
    notes: str = ""

    def validate(self) -> None:
        if not self.description.strip():
            raise ValueError("measurement description must not be empty")
        if self.unit not in VALID_UNITS:
            raise ValueError(f"unit {self.unit!r} not one of {sorted(VALID_UNITS)}")
        if self.confidence not in VALID_CONFIDENCE:
            raise ValueError(f"confidence {self.confidence!r} is invalid")
        if self.count is None or self.count < 0:
            raise ValueError(f"count must be >= 0, got {self.count!r}")
        for d in self.dimensions_m:
            if not isinstance(d, (int, float)) or d < 0:
                raise ValueError(f"dimension {d!r} must be a non-negative number")
        # Dimension count must match the claimed unit (except kg).
        expected = _DIMS_FOR_UNIT.get(self.unit)
        if expected is not None and len(self.dimensions_m) != expected:
            raise ValueError(
                f"unit {self.unit} needs {expected} dimension(s), "
                f"got {len(self.dimensions_m)} — this is exactly what the "
                "Unit Guard exists to catch"
            )


@dataclass
class ExtractOutput:
    records: list[Measurement] = field(default_factory=list)

    def validate(self) -> None:
        for r in self.records:
            r.validate()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExtractOutput":
        raw = data.get("records", [])
        records = [
            Measurement(
                description=r.get("description", ""),
                trade=r.get("trade", ""),
                count=r.get("count", 0),
                dimensions_m=list(r.get("dimensions_m", [])),
                unit=r.get("unit", ""),
                source_drawing=r.get("source_drawing", ""),
                source_sheet=r.get("source_sheet", ""),
                source_revision=r.get("source_revision", ""),
                confidence=r.get("confidence", "medium"),
                notes=r.get("notes", ""),
            )
            for r in raw
        ]
        out = cls(records=records)
        out.validate()
        return out
