"""Contract for A9 — Orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ROUTES = {
    "engineer_review", "approval_queue", "client_agent",
    "schedule", "archive", "owner",
}
PRIORITIES = {"urgent", "normal", "low"}


@dataclass
class Event:
    type: str
    record: dict
    state: str = ""


@dataclass
class Routing:
    route_to: str
    priority: str = "normal"
    reason: str = ""
    escalate: bool = False
    summary: str = ""

    def validate(self) -> None:
        if self.route_to not in ROUTES:
            raise ValueError(f"route_to {self.route_to!r} invalid")
        if self.priority not in PRIORITIES:
            raise ValueError(f"priority {self.priority!r} invalid")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Routing":
        out = cls(
            route_to=data.get("route_to", ""),
            priority=data.get("priority", "normal"),
            reason=data.get("reason", ""),
            escalate=bool(data.get("escalate", False)),
            summary=data.get("summary", ""),
        )
        out.validate()
        return out
