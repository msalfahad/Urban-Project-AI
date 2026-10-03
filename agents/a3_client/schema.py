"""Input/output contract for A3 — Client Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CONTRACT_FORMS = {"black_structure", "finishing", "turnkey", "unknown"}
PROJECT_TYPES = {"house", "chalet", "commercial", "renovation", "unknown"}
STAGES = {"qualifying", "awaiting_drawings", "ready_for_takeoff", "needs_human"}


@dataclass
class Message:
    """One inbound WhatsApp turn plus the conversation so far."""

    text: str
    history: list[dict] = field(default_factory=list)  # [{"role","text"}]


@dataclass
class Lead:
    contract_form: str = "unknown"
    project_type: str = "unknown"
    area_m2: float | None = None
    floors: int | None = None
    pool: bool | None = None
    lift: bool | None = None
    budget_kwd: float | None = None
    timing: str = ""
    drawings_requested: bool = False
    drawings_received: bool = False

    def validate(self) -> None:
        if self.contract_form not in CONTRACT_FORMS:
            raise ValueError(f"contract_form {self.contract_form!r} invalid")
        if self.project_type not in PROJECT_TYPES:
            raise ValueError(f"project_type {self.project_type!r} invalid")


@dataclass
class ClientReply:
    reply_ar: str
    lead: Lead
    stage: str = "qualifying"
    handoff_reason: str = ""

    def validate(self) -> None:
        if not self.reply_ar.strip():
            raise ValueError("reply_ar must not be empty")
        if self.stage not in STAGES:
            raise ValueError(f"stage {self.stage!r} invalid")
        self.lead.validate()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClientReply":
        ld = data.get("lead", {}) or {}
        reply = cls(
            reply_ar=data.get("reply_ar", ""),
            lead=Lead(
                contract_form=ld.get("contract_form", "unknown"),
                project_type=ld.get("project_type", "unknown"),
                area_m2=ld.get("area_m2"),
                floors=ld.get("floors"),
                pool=ld.get("pool"),
                lift=ld.get("lift"),
                budget_kwd=ld.get("budget_kwd"),
                timing=ld.get("timing", ""),
                drawings_requested=bool(ld.get("drawings_requested", False)),
                drawings_received=bool(ld.get("drawings_received", False)),
            ),
            stage=data.get("stage", "qualifying"),
            handoff_reason=data.get("handoff_reason", ""),
        )
        reply.validate()
        return reply
