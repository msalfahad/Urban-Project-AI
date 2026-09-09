"""Contract for A12 — Call Summariser."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CONTRACT_FORMS = {"black_structure", "finishing", "turnkey", "unknown"}
SENTIMENTS = {"positive", "neutral", "negative"}


@dataclass
class CallInput:
    transcript: str


@dataclass
class CallOutput:
    requirements: list[str] = field(default_factory=list)
    objections: list[str] = field(default_factory=list)
    contract_form: str = "unknown"
    next_action: str = ""
    sentiment: str = "neutral"
    summary_ar: str = ""

    def validate(self) -> None:
        if self.contract_form not in CONTRACT_FORMS:
            raise ValueError(f"contract_form {self.contract_form!r} invalid")
        if self.sentiment not in SENTIMENTS:
            raise ValueError(f"sentiment {self.sentiment!r} invalid")
        if not self.next_action.strip():
            raise ValueError("next_action must not be empty")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CallOutput":
        out = cls(
            requirements=list(data.get("requirements", [])),
            objections=list(data.get("objections", [])),
            contract_form=data.get("contract_form", "unknown"),
            next_action=data.get("next_action", ""),
            sentiment=data.get("sentiment", "neutral"),
            summary_ar=data.get("summary_ar", ""),
        )
        out.validate()
        return out
