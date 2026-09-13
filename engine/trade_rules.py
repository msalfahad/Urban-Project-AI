"""E27 — Trade Rule Library.

Geometry is one thing; what a trade does to that geometry is another. A bedroom
and a bathroom can have identical floors and completely different scopes of
work, and no amount of general construction knowledge tells you which — only
the project's own rules do.

So nothing here is hard-coded globally. A `TradeRuleSet` is loaded per project,
and a room type with no rule raises rather than defaulting, because a silent
default is exactly how a bathroom ends up priced as a bedroom.

Heights are per trade, never per room. The Test 1 takeoff used one 3.30 m height
for everything; the real project uses 3.00 m for ceramic and 3.20 m for plaster.
One generic `roomHeight` field cannot express that, so there isn't one.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path


class TradeRuleError(RuntimeError):
    """No rule covers this — an engineer decides, the engine does not guess."""


@dataclass(frozen=True)
class RoomRule:
    room_type: str
    floor_finish: str | None          # None = no floor finish in this trade
    wall_finish: str | None
    notes: str = ""

    # Provenance. A trade decision without a traceable rule is an assumption
    # wearing a number's clothes, so every applied rule can name itself.
    rule_id: str = ""
    source: str = ""                  # where the decision comes from
    measurement_basis: str = ""       # which physical face the quantity follows

    def applied(self, rule_set: "TradeRuleSet", decision: str) -> dict:
        """A record of this rule being applied — what an audit can read back."""
        return {
            "rule_id": self.rule_id or f"{rule_set.trade}:{self.room_type}",
            "project_id": rule_set.project,
            "rule_set_version": rule_set.version,
            "effective_from": rule_set.effective_from,
            "source": self.source or rule_set.source,
            "space_type": self.room_type,
            "trade": rule_set.trade,
            "decision": decision,
            "measurement_basis": self.measurement_basis or rule_set.measurement_basis,
            "height_m": str(rule_set.height_m),
        }


@dataclass
class TradeRuleSet:
    """One trade's rules for one project."""

    trade: str
    height_m: Decimal
    rules: dict[str, RoomRule] = field(default_factory=dict)
    project: str = ""
    version: str = "1.0"
    effective_from: str = ""
    source: str = ""
    measurement_basis: str = ""
    height_source: str = ""           # never a default; always says where it came from

    def rule_for(self, room_type: str) -> RoomRule:
        key = room_type.strip().upper()
        if key not in self.rules:
            raise TradeRuleError(
                f"{self.trade}: no rule for room type {room_type!r} in project "
                f"{self.project or '<unnamed>'} — add one rather than assuming"
            )
        return self.rules[key]

    def has_wall_finish(self, room_type: str) -> bool:
        return self.rule_for(room_type).wall_finish is not None

    def has_floor_finish(self, room_type: str) -> bool:
        return self.rule_for(room_type).floor_finish is not None

    def wall_area_m2(self, room_type: str, wall_length_m: Decimal) -> Decimal:
        """Wall length x this trade's height. Never a generic room height."""
        if not self.has_wall_finish(room_type):
            raise TradeRuleError(
                f"{self.trade}: {room_type} has no wall finish — asking for its "
                "wall area means the caller believes a rule that does not exist"
            )
        if wall_length_m < 0:
            raise TradeRuleError(f"negative wall length {wall_length_m}")
        return wall_length_m * self.height_m

    @classmethod
    def from_dict(cls, data: dict) -> "TradeRuleSet":
        rs = {
            k.upper(): RoomRule(
                room_type=k.upper(),
                floor_finish=v.get("floor_finish"),
                wall_finish=v.get("wall_finish"),
                notes=v.get("notes", ""),
                rule_id=v.get("rule_id", ""),
                source=v.get("source", ""),
                measurement_basis=v.get("measurement_basis", ""),
            )
            for k, v in data.get("rules", {}).items()
        }
        # A rule keyed on a word that is not a semantic label can never fire —
        # it would sit in the file looking authoritative while every lookup for
        # that space type raised "no rule". SALOON vs SALON cost exactly this.
        from agents.a1_extractor.semantic import SEMANTIC_LABELS
        unknown = sorted(set(rs) - SEMANTIC_LABELS)
        if unknown:
            raise TradeRuleError(
                f"{data.get('trade')}: rule(s) for {unknown} are not semantic labels. "
                "Trade rules are keyed on the canonical vocabulary so a spelling "
                "difference cannot silently change a quantity.")
        if not data.get("_height_source") and not data.get("height_source"):
            raise TradeRuleError(
                f"{data.get('trade')}: height {data.get('height_m')} has no stated "
                "source. A trade height is a project decision, never a default — "
                "the Test 1 takeoff applied 3.30 m to everything for exactly this "
                "reason.")
        return cls(
            trade=data["trade"],
            height_m=Decimal(str(data["height_m"])),
            rules=rs,
            project=data.get("project", ""),
            version=data.get("version", "1.0"),
            effective_from=data.get("effective_from", ""),
            source=data.get("source", ""),
            measurement_basis=data.get("measurement_basis", ""),
            height_source=data.get("_height_source", data.get("height_source", "")),
        )

    @classmethod
    def load(cls, path: str | Path) -> "TradeRuleSet":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
