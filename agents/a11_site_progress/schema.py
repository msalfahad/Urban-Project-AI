"""Contract for A11 — Site Progress."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TRADE_STATES = {"in_progress", "stalled", "not_started", "done"}


@dataclass
class SiteInput:
    observation: str            # description of the photo/message
    timestamp: str = ""
    known_activities: list[str] = field(default_factory=list)


@dataclass
class Completed:
    activity: str
    detail: str = ""
    confidence: str = "medium"


@dataclass
class TradeStatus:
    trade: str
    status: str

    def validate(self) -> None:
        if self.status not in TRADE_STATES:
            raise ValueError(f"trade status {self.status!r} invalid")


@dataclass
class SiteOutput:
    completed: list[Completed] = field(default_factory=list)
    trade_status: list[TradeStatus] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    notes: str = ""

    def validate(self) -> None:
        for t in self.trade_status:
            t.validate()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SiteOutput":
        out = cls(
            completed=[
                Completed(c.get("activity", ""), c.get("detail", ""), c.get("confidence", "medium"))
                for c in data.get("completed", [])
            ],
            trade_status=[
                TradeStatus(t.get("trade", ""), t.get("status", "not_started"))
                for t in data.get("trade_status", [])
            ],
            flags=list(data.get("flags", [])),
            notes=data.get("notes", ""),
        )
        out.validate()
        return out
