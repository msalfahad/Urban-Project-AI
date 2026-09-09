"""Contract for A13 — Contract Reader."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContractInput:
    text: str


@dataclass
class Milestone:
    trigger: str
    percent: float | None = None
    amount_kwd: float | None = None
    due: str = ""


@dataclass
class ContractOutput:
    payment_milestones: list[Milestone] = field(default_factory=list)
    retention: dict = field(default_factory=dict)
    delay_penalty: dict = field(default_factory=dict)
    notice_periods: list[dict] = field(default_factory=list)
    variation_procedure: str = ""
    unclear: list[str] = field(default_factory=list)

    def validate(self) -> None:
        for m in self.payment_milestones:
            if not m.trigger.strip():
                raise ValueError("each milestone needs a trigger")
            if m.percent is not None and not (0 <= m.percent <= 100):
                raise ValueError(f"milestone percent {m.percent} out of range")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContractOutput":
        out = cls(
            payment_milestones=[
                Milestone(
                    trigger=m.get("trigger", ""),
                    percent=m.get("percent"),
                    amount_kwd=m.get("amount_kwd"),
                    due=m.get("due", ""),
                )
                for m in data.get("payment_milestones", [])
            ],
            retention=dict(data.get("retention", {})),
            delay_penalty=dict(data.get("delay_penalty", {})),
            notice_periods=list(data.get("notice_periods", [])),
            variation_procedure=data.get("variation_procedure", ""),
            unclear=list(data.get("unclear", [])),
        )
        out.validate()
        return out
