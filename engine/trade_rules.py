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


# A rule set that has not been wired yet. NULL NEVER MEANS DEFAULT: a trade with
# no rules must fail closed, because "no rule" silently becoming "yes, at 3.0 m"
# is precisely how the first takeoff applied one height to the whole floor.
NOT_WIRED = "NOT_WIRED"
WIRED = "WIRED"


class TradeRuleError(RuntimeError):
    """No rule covers this — an engineer decides, the engine does not guess."""


class RuleEngineNotAvailable(TradeRuleError):
    """A quantity was requested from a trade whose rules are not wired yet."""


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
    trade_rule_status: str = WIRED

    def rule_for(self, room_type: str) -> RoomRule:
        if self.trade_rule_status != WIRED or not self.rules:
            raise RuleEngineNotAvailable(
                f"{self.trade}: rule set is {self.trade_rule_status} for project "
                f"{self.project or '<unnamed>'} — RULE_ENGINE_NOT_AVAILABLE. "
                "No default is applied; the quantity is not calculable yet.")
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
            trade_rule_status=data.get("trade_rule_status", WIRED),
            height_source=data.get("_height_source", data.get("height_source", "")),
        )

    @classmethod
    def load(cls, path: str | Path) -> "TradeRuleSet":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# E27 — who decides trade relevance
#
# Run 0 asked A1 and A2 for `trade_relevance` directly and they agreed on 12 of
# 36 spaces. That 33% was reported as a semantic failure, which put the blame in
# the wrong place: the architecture says A1/A2 classify WHAT A SPACE IS and E27
# decides WHAT TRADES APPLY. Two models improvising over a trade vocabulary are
# not disagreeing about the drawing, they are both guessing at a project rule
# neither was given.
#
# So the decision moves here, where it is a lookup with provenance. A1 may still
# push back — TRADE_RULE_CHALLENGE, DRAWING_NOTE_CONFLICT — but a challenge is a
# message, never a substitute quantity.
#
# Every branch below that cannot find a rule returns a status that stops work.
# None of them returns "yes, probably".

APPLIES = "APPLIES"
NOT_APPLICABLE = "NOT_APPLICABLE"
RULE_REQUIRED = "RULE_REQUIRED"
RULE_ENGINE_NOT_AVAILABLE = "RULE_ENGINE_NOT_AVAILABLE"
HELD_PENDING_SCOPE = "HELD_PENDING_SCOPE"
NOT_IN_SCOPE = "NOT_IN_SCOPE"

# Statuses that are a decision. Everything else is a question for a human.
_DECIDED = {APPLIES, NOT_APPLICABLE, NOT_IN_SCOPE}

FLOOR, WALL = "FLOOR", "WALL"

# Labels that name the absence of a classification. A trade rule keyed on one of
# these would be a rule about not knowing.
_NON_LABELS = {"UNKNOWN", "AMBIGUOUS", "NOT_A_SPACE", ""}


@dataclass(frozen=True)
class TradeDecision:
    """One trade x one element x one space: does this work happen here?"""

    trade: str
    element: str                      # FLOOR | WALL
    status: str
    applies: bool                     # False for every status except APPLIES
    space_label: str = ""
    finish: str | None = None
    rule_id: str = ""
    basis: str = ""                   # what the decision rests on, in words
    missing_rule_id: str = ""         # machine-readable, routable, groupable
    trade_rule_confidence: str = "NOT_ESTABLISHED"
    measurement_basis: str = ""

    @property
    def decided(self) -> bool:
        return self.status in _DECIDED

    @property
    def needs_human(self) -> bool:
        return not self.decided


def _missing_id(trade: str, element: str, label: str) -> str:
    return f"{trade}_{element}_{label or 'NO_LABEL'}".upper().replace(" ", "_")


def decide_trade(rule_set: "TradeRuleSet", label: str, element: str, *,
                 scope_status: str) -> TradeDecision:
    """One deterministic answer, or one named reason there isn't one."""
    if element not in (FLOOR, WALL):
        raise TradeRuleError(f"element {element!r} is not {FLOOR} or {WALL}")
    common = dict(trade=rule_set.trade, element=element, space_label=label)

    # Scope first: a trade question about a space that is not in the job is not
    # a trade question. AMBIGUOUS is held, never resolved by optimism.
    if scope_status == "OUT_OF_SCOPE":
        return TradeDecision(**common, status=NOT_IN_SCOPE, applies=False,
                             basis="space is out of the approved scope",
                             trade_rule_confidence="HIGH")
    if scope_status != "IN_SCOPE":
        return TradeDecision(**common, status=HELD_PENDING_SCOPE, applies=False,
                             basis=f"scope_status is {scope_status!r} — a trade cannot "
                                   "be applied to a space that may not be in the job",
                             missing_rule_id=_missing_id(rule_set.trade, element, "SCOPE"))
    if label in _NON_LABELS:
        return TradeDecision(**common, status=RULE_REQUIRED, applies=False,
                             basis=f"space label is {label!r} — there is nothing to look up",
                             missing_rule_id=_missing_id(rule_set.trade, element, label))
    try:
        rule = rule_set.rule_for(label)
    except RuleEngineNotAvailable as exc:
        return TradeDecision(**common, status=RULE_ENGINE_NOT_AVAILABLE, applies=False,
                             basis=str(exc),
                             missing_rule_id=_missing_id(rule_set.trade, element, label))
    except TradeRuleError as exc:
        return TradeDecision(**common, status=RULE_REQUIRED, applies=False,
                             basis=str(exc),
                             missing_rule_id=_missing_id(rule_set.trade, element, label))

    finish = rule.floor_finish if element == FLOOR else rule.wall_finish
    rule_id = rule.rule_id or f"{rule_set.trade}:{rule.room_type}"
    basis_src = rule.source or rule_set.source or "project rule set"
    if finish is None:
        return TradeDecision(**common, status=NOT_APPLICABLE, applies=False,
                             rule_id=rule_id, trade_rule_confidence="HIGH",
                             basis=f"{rule_set.trade} rule {rule_id} gives {label} no "
                                   f"{element.lower()} finish ({basis_src})")
    return TradeDecision(**common, status=APPLIES, applies=True, finish=finish,
                         rule_id=rule_id, trade_rule_confidence="HIGH",
                         measurement_basis=rule.measurement_basis or rule_set.measurement_basis,
                         basis=f"{rule_set.trade} rule {rule_id}: {label} takes "
                               f"{finish} ({basis_src})")


def trade_relevance(label: str, scope_status: str,
                    rule_sets: "dict[str, TradeRuleSet] | list[TradeRuleSet]"
                    ) -> list[TradeDecision]:
    """Every trade x element decision for one space. E27 owns this, not A1."""
    sets = rule_sets.values() if isinstance(rule_sets, dict) else rule_sets
    return [decide_trade(rs, label, el, scope_status=scope_status)
            for rs in sets for el in (FLOOR, WALL)]


def applied_trades(decisions: "list[TradeDecision]") -> list[str]:
    """The trades that actually apply — the list A1 used to be asked to invent."""
    return sorted({d.trade for d in decisions if d.applies})


def open_questions(decisions: "list[TradeDecision]") -> list[TradeDecision]:
    """Everything E27 refused to decide, for the human queue and the metric."""
    return [d for d in decisions if d.needs_human]
