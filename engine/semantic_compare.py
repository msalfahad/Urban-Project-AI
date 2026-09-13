"""E32 — Deterministic A1/A2 semantic comparison.

No model decides whether two models agree. This is arithmetic on fields.

The rule that matters most here is that AGREEMENT IS NOT PROOF. The first blind
test on this project had A1 and A2 agree on all 30 dimensions they both read
while between them missing about a third of the floor. Two readers can share a
blind spot, and two readers who agree against a third source are not right — they
are outvoted. So:

- agreement at LOW confidence is AGREE_LOW_CONFIDENCE, which is not a pass
- agreement that contradicts a schedule is SOURCE_CONFLICT, not agreement
- a disagreement is never resolved by whichever model sounded more certain

Materiality is attached to prioritise review, and ONLY to prioritise review. A
wrong answer stays wrong when it is cheap; materiality changes the queue order,
never the verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Comparison verdicts.
AGREE_HIGH_CONFIDENCE = "AGREE_HIGH_CONFIDENCE"
AGREE_LOW_CONFIDENCE = "AGREE_LOW_CONFIDENCE"
DISAGREE = "DISAGREE"
MISSING_A1 = "MISSING_A1"
MISSING_A2 = "MISSING_A2"
SOURCE_CONFLICT = "SOURCE_CONFLICT"
HUMAN_REVIEW = "HUMAN_REVIEW"

# Materiality — routing priority, never truth.
LOW, MEDIUM, HIGH, CRITICAL = "LOW", "MEDIUM", "HIGH", "CRITICAL"
_RANK = {LOW: 0, MEDIUM: 1, HIGH: 2, CRITICAL: 3}

# Confidence strong enough that agreement carries weight.
STRONG_CONFIDENCE = {"HIGH", "MEDIUM"}

# Fields compared, and how much a difference in each one can cost.
# Scope, apartment and floor are CRITICAL because they move whole rooms into or
# out of a bill; a label difference is judged by its trade consequences instead.
FIELD_MATERIALITY = {
    "scope_status": CRITICAL,
    "apartment_id": CRITICAL,
    "floor_id": CRITICAL,
    "zone_id": HIGH,
    "semantic_label": None,          # decided by trade consequence
    "trade_relevance": HIGH,
}


@dataclass
class FieldDiff:
    field_name: str
    a1: object
    a2: object
    materiality: str
    note: str = ""


@dataclass
class SpaceComparison:
    space_id: str
    verdict: str
    materiality: str = LOW
    diffs: list[FieldDiff] = field(default_factory=list)
    source_conflict: str = ""
    a1_confidence: str = ""
    a2_confidence: str = ""

    @property
    def agreed(self) -> bool:
        return self.verdict in (AGREE_HIGH_CONFIDENCE, AGREE_LOW_CONFIDENCE)

    @property
    def is_pass_candidate(self) -> bool:
        """Only strong, unconflicted agreement is even eligible for auto-pass."""
        return self.verdict == AGREE_HIGH_CONFIDENCE


def _trade_consequence(label: str, rules) -> tuple | None:
    """What the trade rules actually DO to this label, or None if unknown."""
    if rules is None:
        return None
    try:
        r = rules.rule_for(label)
    except Exception:
        return None
    return (r.floor_finish, r.wall_finish)


def label_materiality(a1_label: str, a2_label: str, rules=None) -> tuple[str, str]:
    """How much a label disagreement costs, judged by trade consequences.

    BEDROOM vs MASTER_BEDROOM changes nothing a trade does, so it is LOW.
    BEDROOM vs BATHROOM changes floor and wall finish, so it is HIGH.
    SHAFT vs WASHROOM turns a void into a tiled room, so it is CRITICAL.
    """
    if a1_label == a2_label:
        return LOW, ""
    ca, cb = _trade_consequence(a1_label, rules), _trade_consequence(a2_label, rules)
    # A space that is not a space at all being called a room is the worst case.
    non_spaces = {"SHAFT", "VOID", "LIFT_SHAFT", "STAIR"}
    if (a1_label in non_spaces) != (a2_label in non_spaces):
        return CRITICAL, "one agent says this is not usable floor at all"
    if ca is None or cb is None:
        return HIGH, "no trade rule for one of the labels — consequence unknown"
    if ca == cb:
        return LOW, "different words, identical trade consequences"
    return HIGH, f"trade consequences differ: {ca} vs {cb}"


def compare_space(a1, a2, *, rules=None, schedule_label: str | None = None) -> SpaceComparison:
    """Compare one space's semantics field by field."""
    if a1 is None and a2 is None:
        raise ValueError("nothing to compare")
    if a1 is None:
        return SpaceComparison(a2.space_id, MISSING_A1, CRITICAL,
                               a2_confidence=a2.label_confidence)
    if a2 is None:
        return SpaceComparison(a1.space_id, MISSING_A2, CRITICAL,
                               a1_confidence=a1.label_confidence)

    diffs: list[FieldDiff] = []
    for name, mat in FIELD_MATERIALITY.items():
        va, vb = getattr(a1, name), getattr(a2, name)
        if isinstance(va, list):
            va, vb = sorted(va), sorted(vb)
        if va == vb:
            continue
        if name == "semantic_label":
            mat, note = label_materiality(va, vb, rules)
        else:
            note = ""
        diffs.append(FieldDiff(name, va, vb, mat, note))

    cmp = SpaceComparison(a1.space_id, DISAGREE, LOW, diffs,
                          a1_confidence=a1.label_confidence,
                          a2_confidence=a2.label_confidence)

    # A schedule is a third source. Two agents agreeing against it are outvoted,
    # not corroborated — this is exactly the BATHROOM/BATHROOM/STORE case.
    if schedule_label and a1.semantic_label == a2.semantic_label \
            and schedule_label != a1.semantic_label:
        cmp.verdict = SOURCE_CONFLICT
        cmp.materiality = HIGH
        cmp.source_conflict = (
            f"A1 and A2 both say {a1.semantic_label}, but the schedule says "
            f"{schedule_label}. Agreement against a third source is not proof.")
        return cmp

    if diffs:
        cmp.verdict = DISAGREE
        cmp.materiality = max((d.materiality for d in diffs), key=lambda m: _RANK[m])
        return cmp

    # Identical. Whether that is worth anything depends on the evidence behind it.
    strong = (a1.label_confidence in STRONG_CONFIDENCE
              and a2.label_confidence in STRONG_CONFIDENCE)
    unresolved = bool(a1.semantic_conflicts or a2.semantic_conflicts)
    if strong and not unresolved:
        cmp.verdict = AGREE_HIGH_CONFIDENCE
    else:
        cmp.verdict = AGREE_LOW_CONFIDENCE
        cmp.materiality = MEDIUM
        cmp.source_conflict = (
            "agreement rests on weak evidence" if not strong
            else "agreement carries an unresolved semantic conflict")
    return cmp


@dataclass
class ComparisonReport:
    rows: list[SpaceComparison] = field(default_factory=list)

    def by_verdict(self, verdict: str) -> list[SpaceComparison]:
        return [r for r in self.rows if r.verdict == verdict]

    @property
    def disagreement_rate(self) -> float:
        if not self.rows:
            return 0.0
        bad = sum(1 for r in self.rows if not r.agreed)
        return bad / len(self.rows)

    @property
    def pass_candidates(self) -> list[SpaceComparison]:
        return [r for r in self.rows if r.is_pass_candidate]

    def queue(self) -> list[SpaceComparison]:
        """Everything needing a human, worst first."""
        need = [r for r in self.rows if not r.is_pass_candidate]
        return sorted(need, key=lambda r: -_RANK[r.materiality])


def compare(a1_out, a2_out, *, rules=None, schedule: dict[str, str] | None = None
            ) -> ComparisonReport:
    """Compare two semantic passes over the same spaces."""
    schedule = schedule or {}
    a1_map = {s.space_id: s for s in a1_out.spaces}
    a2_map = {s.space_id: s for s in a2_out.spaces}
    rows = [
        compare_space(a1_map.get(sid), a2_map.get(sid), rules=rules,
                      schedule_label=schedule.get(sid))
        for sid in sorted(set(a1_map) | set(a2_map))
    ]
    return ComparisonReport(rows)
