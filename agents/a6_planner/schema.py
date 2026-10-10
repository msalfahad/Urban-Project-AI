"""Contract for A6 — Planner. Activities and dependencies only; no durations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlanInput:
    contract_form: str
    area_m2: float | None = None
    floors: int | None = None
    pool: bool = False
    lift: bool = False
    notes: str = ""


@dataclass
class Activity:
    id: str
    name: str
    stage: str = ""
    trade: str = ""
    depends_on: list[str] = field(default_factory=list)
    can_overlap_with: list[str] = field(default_factory=list)
    quantity_driver: str = ""
    crew_assumption: str = ""
    provisional: bool = True
    notes: str = ""

    def validate(self) -> None:
        if not self.id.strip():
            raise ValueError("activity id required")
        if not self.name.strip():
            raise ValueError("activity name required")


@dataclass
class PlanOutput:
    activities: list[Activity] = field(default_factory=list)

    def validate(self) -> None:
        ids = set()
        for a in self.activities:
            a.validate()
            if a.id in ids:
                raise ValueError(f"duplicate activity id {a.id!r}")
            ids.add(a.id)
        # Dependencies must reference real activities.
        for a in self.activities:
            for dep in a.depends_on:
                if dep not in ids:
                    raise ValueError(f"{a.id} depends on unknown activity {dep!r}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlanOutput":
        acts = [
            Activity(
                id=a.get("id", ""),
                name=a.get("name", ""),
                stage=a.get("stage", ""),
                trade=a.get("trade", ""),
                depends_on=list(a.get("depends_on", [])),
                can_overlap_with=list(a.get("can_overlap_with", [])),
                quantity_driver=a.get("quantity_driver", ""),
                crew_assumption=a.get("crew_assumption", ""),
                provisional=bool(a.get("provisional", True)),
                notes=a.get("notes", ""),
            )
            for a in data.get("activities", [])
        ]
        out = cls(activities=acts)
        out.validate()
        return out
