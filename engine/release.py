"""E33 — Exception routing and release control.

The workflow does not end at "A2 found seven problems". Every quantity gets a
release status, and only released quantities may enter a BOQ. A BOQ is therefore
downstream of validation rather than a sum of whatever the pipeline produced.

Auto-validation is deliberately hard to earn. Each condition below exists
because this project has already seen it fail:

- semantics merely AGREED is not enough; two agents agreed through a third of a
  missing floor once already, so agreement has to be strong AND unconflicted
- a trade rule must exist, because a missing rule used to become a default
- geometry needs a known basis, because a clear-internal area compared against a
  printed-dimension area looks like an error and is not
- the revision must be right, because a beautiful quantity off an old sheet is
  just a confident mistake

Anything failing a condition is not deleted and not guessed at — it is routed,
with the reason attached, so the engineer sees the three that matter instead of
the hundred-and-fifty that do not.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.quantities import (APPROVED_BY_ENGINEER, AUTO_VALIDATED, BLOCKED,
                               REVIEW_REQUIRED, Quantity)
from engine.semantic_compare import AGREE_HIGH_CONFIDENCE, CRITICAL, HIGH, LOW, MEDIUM

_RANK = {LOW: 0, MEDIUM: 1, HIGH: 2, CRITICAL: 3}


@dataclass
class ReleaseDecision:
    quantity_id: str
    space_id: str
    status: str
    materiality: str = LOW
    reasons: list[str] = field(default_factory=list)

    @property
    def released(self) -> bool:
        return self.status in (AUTO_VALIDATED, APPROVED_BY_ENGINEER)


@dataclass
class ExceptionQueue:
    decisions: list[ReleaseDecision] = field(default_factory=list)

    @property
    def auto_validated(self) -> list[ReleaseDecision]:
        return [d for d in self.decisions if d.status == AUTO_VALIDATED]

    @property
    def review(self) -> list[ReleaseDecision]:
        return [d for d in self.decisions if d.status == REVIEW_REQUIRED]

    @property
    def blocked(self) -> list[ReleaseDecision]:
        return [d for d in self.decisions if d.status == BLOCKED]

    def ordered(self) -> list[ReleaseDecision]:
        """What a human should look at, worst first."""
        need = [d for d in self.decisions if not d.released]
        return sorted(need, key=lambda d: -_RANK[d.materiality])

    @property
    def human_review_rate(self) -> float:
        if not self.decisions:
            return 0.0
        return len([d for d in self.decisions if not d.released]) / len(self.decisions)


def decide(q: Quantity, *, comparison=None, challenges=(),
           rule_exists: bool | None = None,
           approved_revision: str | None = None) -> ReleaseDecision:
    """Decide one quantity's release status. Every refusal names itself."""
    reasons: list[str] = []
    materiality = LOW
    blocked = False

    if comparison is None:
        reasons.append("no semantic comparison exists for this space")
        materiality = CRITICAL
        blocked = True
    elif comparison.verdict != AGREE_HIGH_CONFIDENCE:
        reasons.append(
            f"semantics are {comparison.verdict}"
            + (f" — {comparison.source_conflict}" if comparison.source_conflict else ""))
        if _RANK[comparison.materiality] > _RANK[materiality]:
            materiality = comparison.materiality
        if comparison.materiality == CRITICAL:
            blocked = True

    # Tri-state on purpose. `None` is "nobody established whether a rule exists",
    # which used to default to True — a quantity could be released on a trade
    # rule that was never looked up. Not knowing is not the same as knowing yes.
    if rule_exists is None:
        reasons.append(
            f"whether a {q.trade} trade rule covers this space type was never "
            "established — E27 must answer before this is released")
        materiality = max(materiality, HIGH, key=lambda m: _RANK[m])
    elif not rule_exists:
        reasons.append(f"no {q.trade} trade rule covers this space type")
        materiality = max(materiality, HIGH, key=lambda m: _RANK[m])

    if not q.geometry_basis:
        reasons.append("geometry has no stated measurement basis")
        materiality = max(materiality, HIGH, key=lambda m: _RANK[m])

    if approved_revision is not None and q.drawing_revision != approved_revision:
        reasons.append(
            f"quantity is off revision {q.drawing_revision!r}, approved is "
            f"{approved_revision!r}")
        materiality = CRITICAL
        blocked = True

    for c in challenges:
        if c.blocks_release:
            reasons.append(f"{c.severity}: {c.challenge_type} — {c.reason}")
            materiality = max(materiality, HIGH, key=lambda m: _RANK[m])
            if c.severity == "BLOCK":
                blocked = True
        else:
            reasons.append(f"{c.severity}: {c.challenge_type}")
            materiality = max(materiality, MEDIUM, key=lambda m: _RANK[m])

    if not reasons:
        return ReleaseDecision(q.quantity_id, q.space_id, AUTO_VALIDATED, LOW,
                               ["all release conditions met"])
    return ReleaseDecision(q.quantity_id, q.space_id,
                           BLOCKED if blocked else REVIEW_REQUIRED,
                           materiality, reasons)


def route(quantities: list[Quantity], *, comparisons=None, challenges=None,
          rules_present=None, approved_revision: str | None = None) -> ExceptionQueue:
    """Route a whole project's quantities."""
    comparisons = comparisons or {}
    challenges = challenges or {}
    rules_present = rules_present or {}
    return ExceptionQueue([
        decide(q,
               comparison=comparisons.get(q.space_id),
               challenges=challenges.get(q.quantity_id, ()),
               rule_exists=rules_present.get(q.space_id),
               approved_revision=approved_revision)
        for q in quantities
    ])


def apply(quantities: list[Quantity], queue: ExceptionQueue) -> list[Quantity]:
    """Stamp each quantity with its decided status. Values are never touched."""
    by_id = {d.quantity_id: d for d in queue.decisions}
    out = []
    for q in quantities:
        d = by_id.get(q.quantity_id)
        out.append(Quantity(**{**q.__dict__, "status": d.status}) if d else q)
    return out
