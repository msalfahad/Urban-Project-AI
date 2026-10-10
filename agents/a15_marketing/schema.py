"""Contract for A15 — Marketing Strategist."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MarketingInput:
    date_range: str
    goal: str = ""
    analysis: dict = field(default_factory=dict)   # A14's output


@dataclass
class MarketingPlan:
    goal: str
    themes: list[str] = field(default_factory=list)
    calendar: list[dict] = field(default_factory=list)
    cadence: str = ""
    notes: str = ""

    def validate(self) -> None:
        if not self.calendar:
            raise ValueError("a marketing plan needs at least one planned post")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MarketingPlan":
        out = cls(
            goal=data.get("goal", ""),
            themes=list(data.get("themes", [])),
            calendar=list(data.get("calendar", [])),
            cadence=data.get("cadence", ""),
            notes=data.get("notes", ""),
        )
        out.validate()
        return out
