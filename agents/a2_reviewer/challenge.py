"""A2 challenger schema.

By this point the answer already exists. A2's job is to attack it.

The schema is built so that attacking is the only thing it CAN do: a challenge
carries an issue, evidence and a recommended route, and there is nowhere to put
a replacement number. "My quantity is 5.2 and the engine says 5.0, so use 5.1"
is not a thing this type can express. A challenged quantity goes back to E23/E25
or to a human; it is never averaged with an opinion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

PASS = "PASS"
CHALLENGE_LOW = "CHALLENGE_LOW"
CHALLENGE_MEDIUM = "CHALLENGE_MEDIUM"
CHALLENGE_HIGH = "CHALLENGE_HIGH"
BLOCK = "BLOCK"

SEVERITIES = (PASS, CHALLENGE_LOW, CHALLENGE_MEDIUM, CHALLENGE_HIGH, BLOCK)
BLOCKING = {CHALLENGE_HIGH, BLOCK}

CHALLENGE_TYPES = {
    "MISSING_SPACE", "DUPLICATE_SPACE", "WRONG_ROOM_TYPE", "WRONG_APARTMENT",
    "WRONG_FLOOR", "WRONG_SCOPE", "WRONG_TRADE", "WRONG_HEIGHT",
    "WRONG_FINISH_RULE", "WRONG_REVISION", "MISSING_DRAWING",
    "SCHEDULE_CONFLICT", "NOTE_CONFLICT", "SHAFT_COUNTED_AS_FLOOR",
    "VOID_COUNTED_AS_FLOOR", "TERRACE_INCORRECTLY_INCLUDED",
    "STAIR_OPENING_COUNTED", "OPEN_PLAN_ARTIFICIALLY_CLOSED",
    "BATHROOM_DRESS_CONFUSION", "IRON_KITCHEN_CONFUSION",
    "DOOR_WINDOW_DOUBLE_COUNT", "WEAK_SOURCE_OVER_STRONG",
    "DESIGN_SITE_QUANTITY_MIXED", "UNSUPPORTED_ASSUMPTION",
}

ROUTES = {"E23_GEOMETRY", "E25_BOUNDARY", "E27_TRADE_RULE", "A1_SEMANTIC",
          "HUMAN_REVIEW", "DRAWING_CONTROL", "NO_ACTION"}

_NUMERIC_KEY = re.compile(
    r"corrected|revised|proposed|suggested_value|new_value|should_be|instead_of",
    re.IGNORECASE)


class ChallengeError(ValueError):
    """A2 tried to do something other than challenge."""


@dataclass
class Challenge:
    challenge_id: str
    project_id: str
    space_id: str
    challenge_type: str
    severity: str
    evidence: str
    reason: str
    recommended_route: str
    quantity_id: str = ""
    source_refs: list[str] = field(default_factory=list)
    status: str = "OPEN"

    def validate(self) -> None:
        if self.challenge_type not in CHALLENGE_TYPES:
            raise ChallengeError(
                f"{self.challenge_id}: challenge_type {self.challenge_type!r} is not "
                f"one of {sorted(CHALLENGE_TYPES)}")
        if self.severity not in SEVERITIES:
            raise ChallengeError(
                f"{self.challenge_id}: severity {self.severity!r} is invalid")
        if self.recommended_route not in ROUTES:
            raise ChallengeError(
                f"{self.challenge_id}: recommended_route {self.recommended_route!r} "
                f"is not one of {sorted(ROUTES)}")
        if not self.evidence.strip():
            raise ChallengeError(
                f"{self.challenge_id}: a challenge without evidence is an opinion")
        if self.severity != PASS and not self.reason.strip():
            raise ChallengeError(f"{self.challenge_id}: a challenge must say why")

    @property
    def blocks_release(self) -> bool:
        return self.severity in BLOCKING


@dataclass
class ChallengeOutput:
    verdict: str = PASS
    challenges: list[Challenge] = field(default_factory=list)
    notes: str = ""

    def validate(self) -> None:
        for c in self.challenges:
            c.validate()
        if self.verdict not in SEVERITIES:
            raise ChallengeError(f"verdict {self.verdict!r} is invalid")
        worst = max((SEVERITIES.index(c.severity) for c in self.challenges), default=0)
        if SEVERITIES.index(self.verdict) < worst:
            raise ChallengeError(
                f"verdict {self.verdict} is softer than the worst challenge "
                f"{SEVERITIES[worst]} — the summary cannot understate the findings")

    @property
    def blocking(self) -> list[Challenge]:
        return [c for c in self.challenges if c.blocks_release]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChallengeOutput":
        raw = data.get("challenges", [])
        for r in raw:
            bad = [k for k in r if _NUMERIC_KEY.search(k)]
            if bad:
                raise ChallengeError(
                    f"{r.get('challenge_id', '?')}: A2 offered a replacement value in "
                    f"{bad}. A challenger routes a quantity back to E23/E25 or to a "
                    "human; it never proposes a number to average with.")
        out = cls(
            verdict=data.get("verdict", PASS),
            challenges=[
                Challenge(
                    challenge_id=r.get("challenge_id", ""),
                    project_id=r.get("project_id", ""),
                    space_id=r.get("space_id", ""),
                    challenge_type=r.get("challenge_type", ""),
                    severity=r.get("severity", CHALLENGE_LOW),
                    evidence=r.get("evidence", ""),
                    reason=r.get("reason", ""),
                    recommended_route=r.get("recommended_route", "HUMAN_REVIEW"),
                    quantity_id=r.get("quantity_id", ""),
                    source_refs=list(r.get("source_refs", [])),
                )
                for r in raw
            ],
            notes=data.get("notes", ""),
        )
        out.validate()
        return out
