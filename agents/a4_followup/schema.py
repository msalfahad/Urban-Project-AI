"""Contract for A4 — Follow-up Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

STEPS = {"day2", "day5", "day10", "stop"}


@dataclass
class FollowupInput:
    days_silent: int
    last_stage: str = ""            # where A3 left the lead
    lead_summary: str = ""          # short human description of the lead
    client_replied_since: bool = False


@dataclass
class FollowupOutput:
    should_send: bool
    message_ar: str
    step: str
    reason: str = ""

    def validate(self) -> None:
        if self.step not in STEPS:
            raise ValueError(f"step {self.step!r} invalid")
        if self.should_send and not self.message_ar.strip():
            raise ValueError("message_ar required when should_send is true")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FollowupOutput":
        out = cls(
            should_send=bool(data.get("should_send", False)),
            message_ar=data.get("message_ar", ""),
            step=data.get("step", "stop"),
            reason=data.get("reason", ""),
        )
        out.validate()
        return out
