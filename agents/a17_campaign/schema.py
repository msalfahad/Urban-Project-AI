"""Contract for A17 — Campaign Manager."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

STAGES = {
    "design", "permits", "foundations", "structure",
    "finishes", "handover", "complete",
}


@dataclass
class Project:
    """The project the campaign is about."""

    name: str
    type: str = ""                  # villa | chalet | apartment | fitout
    location: str = ""              # e.g. "Khairan"
    stage: str = ""                 # one of STAGES — drives what can be filmed
    usps: list[str] = field(default_factory=list)
    photo_refs: list[str] = field(default_factory=list)


@dataclass
class CampaignInput:
    project: Project
    window: str                     # e.g. "Oct-Dec 2026"
    objective: str = ""
    channels: list[str] = field(default_factory=list)   # instagram | whatsapp | tiktok | snapchat
    evidence: dict = field(default_factory=dict)        # A14's analysis
    progress: dict = field(default_factory=dict)        # review mode: what actually happened


@dataclass
class Campaign:
    objective: str
    audience: list[dict] = field(default_factory=list)   # {segment, where, message}
    phases: list[dict] = field(default_factory=list)     # {phase, milestone, weeks, focus}
    schedule: list[dict] = field(default_factory=list)   # {week, channel, type, topic, asset, cta}
    channel_weights: dict = field(default_factory=dict)  # engine turns these into KWD
    kpis: list[dict] = field(default_factory=list)       # {metric, target, how_measured}
    review: dict = field(default_factory=dict)           # {cadence, next_review, bring}
    adjustments: list[dict] = field(default_factory=list)  # {change, evidence} — review mode only
    notes: str = ""

    def validate(self) -> None:
        if not self.objective.strip():
            raise ValueError("objective must not be empty")
        if not self.schedule:
            raise ValueError("a campaign needs at least one scheduled action")
        if not self.channel_weights:
            raise ValueError("a campaign needs channel weights to split the budget")

        for channel, weight in self.channel_weights.items():
            if not isinstance(weight, (int, float)) or isinstance(weight, bool):
                raise ValueError(f"channel weight for {channel!r} must be a number")
            if weight <= 0:
                raise ValueError(f"channel weight for {channel!r} must be positive")

        for i, item in enumerate(self.schedule):
            for required in ("week", "channel", "topic"):
                if not str(item.get(required, "")).strip():
                    raise ValueError(f"schedule[{i}] is missing {required}")
            # Every channel it schedules must be one it budgeted for, or the
            # split would silently fund nothing for that work.
            if item["channel"] not in self.channel_weights:
                raise ValueError(
                    f"schedule[{i}] posts to {item['channel']!r}, which has no channel weight"
                )

        # A change without the number behind it is an opinion the owner can't check.
        for i, change in enumerate(self.adjustments):
            for required in ("change", "evidence"):
                if not str(change.get(required, "")).strip():
                    raise ValueError(f"adjustments[{i}] is missing {required}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Campaign":
        out = cls(
            objective=data.get("objective", ""),
            audience=list(data.get("audience", [])),
            phases=list(data.get("phases", [])),
            schedule=list(data.get("schedule", [])),
            channel_weights=dict(data.get("channel_weights", {})),
            kpis=list(data.get("kpis", [])),
            review=dict(data.get("review", {})),
            adjustments=list(data.get("adjustments", [])),
            notes=data.get("notes", ""),
        )
        out.validate()
        return out
