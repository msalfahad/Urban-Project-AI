"""Contract for A8 — Briefer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BriefInput:
    period: str = "daily"       # "daily" or "weekly"
    snapshot: dict = field(default_factory=dict)  # engine-assembled figures


@dataclass
class BriefOutput:
    headline: str
    leads: str = ""
    quotes: str = ""
    projects: str = ""
    decisions_needed: list[str] = field(default_factory=list)
    brief_ar: str = ""

    def validate(self) -> None:
        if not self.headline.strip():
            raise ValueError("headline must not be empty")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BriefOutput":
        out = cls(
            headline=data.get("headline", ""),
            leads=data.get("leads", ""),
            quotes=data.get("quotes", ""),
            projects=data.get("projects", ""),
            decisions_needed=list(data.get("decisions_needed", [])),
            brief_ar=data.get("brief_ar", ""),
        )
        out.validate()
        return out
