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

Run 0 added a fourth rule the hard way: A FIELD THAT CANNOT BE COMPARED MUST NOT
BE SCORED. `apartment_id` and `zone_id` were free text, compared by string
equality, and returned 0% agreement on 36 of 36 spaces — a number about the
schema, not about the agents. Identifiers now come from a canonical registry, and
where a registry cannot exist (Project 23010 has no approved zone ontology) the
field is excluded by name, with the reason recorded in the report rather than
quietly folded into an average.

`trade_relevance` left this comparison for the same reason. It was never A1's
decision to make: E27 owns it, and E27 is scored against the project rule set.
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
}

# Fields whose comparability depends on the project registry rather than on the
# answers. `kind` is what group_registry.scorable() is asked about.
REGISTRY_GATED = {"apartment_id": "APARTMENT", "zone_id": "ZONE"}


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
    excluded: dict[str, str] = field(default_factory=dict)

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


def comparable_fields(registry=None) -> tuple[dict[str, str], dict[str, str]]:
    """Which fields this project may be scored on, and why the rest may not.

    A field is excluded when the project cannot define what a correct answer
    would look like. That is a property of the project, not of the run, so it is
    decided once here and reported by name — never averaged away.
    """
    fields, excluded = {}, {}
    for name, mat in FIELD_MATERIALITY.items():
        kind = REGISTRY_GATED.get(name)
        if kind is None:
            fields[name] = mat
            continue
        if registry is None:
            excluded[name] = (
                "no canonical group registry was supplied, so this identifier "
                "would be free text compared by string equality — the Run 0 defect")
            continue
        ok, why = registry.scorable(kind)
        (fields if ok else excluded)[name] = mat if ok else why
    return fields, excluded


def compare_space(a1, a2, *, rules=None, schedule_label: str | None = None,
                  registry=None) -> SpaceComparison:
    """Compare one space's semantics field by field."""
    if a1 is None and a2 is None:
        raise ValueError("nothing to compare")
    if a1 is None:
        return SpaceComparison(a2.space_id, MISSING_A1, CRITICAL,
                               a2_confidence=a2.semantic_label_confidence)
    if a2 is None:
        return SpaceComparison(a1.space_id, MISSING_A2, CRITICAL,
                               a1_confidence=a1.semantic_label_confidence)

    fields, excluded = comparable_fields(registry)
    diffs: list[FieldDiff] = []
    for name, mat in fields.items():
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
                          a1_confidence=a1.semantic_label_confidence,
                          a2_confidence=a2.semantic_label_confidence,
                          excluded=dict(excluded))

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
    strong = (a1.semantic_label_confidence in STRONG_CONFIDENCE
              and a2.semantic_label_confidence in STRONG_CONFIDENCE)
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
class MembershipDiff:
    """Two groupings of the same spaces, compared as SETS rather than as names.

    This is the migration diagnostic. Run 0's A1 said APT-EAST and A2 said
    APT-01; had this existed then, identical member sets would have shown at a
    glance that the two agents agreed about the apartment and disagreed only
    about what to call it. Production compares canonical ids — but when a
    canonical id changes meaning, only the sets will say so.
    """

    kind: str
    identical_sets: list[tuple[str, str]] = field(default_factory=list)
    a1_only: dict[str, set[str]] = field(default_factory=dict)
    a2_only: dict[str, set[str]] = field(default_factory=dict)

    @property
    def same_partition(self) -> bool:
        """Do both agents carve the floor into the same groups of spaces?"""
        return not self.a1_only and not self.a2_only


def membership_diff(a1_out, a2_out, kind: str) -> MembershipDiff:
    """Compare group membership as sets of space ids, ignoring the names."""
    from engine.group_registry import membership
    m1, m2 = membership(a1_out.spaces, kind), membership(a2_out.spaces, kind)
    identical, used2 = [], set()
    for g1, s1 in sorted(m1.items()):
        for g2, s2 in sorted(m2.items()):
            if g2 not in used2 and s1 == s2:
                identical.append((g1, g2))
                used2.add(g2)
                break
    matched1 = {g for g, _ in identical}
    return MembershipDiff(
        kind=kind,
        identical_sets=identical,
        a1_only={g: s for g, s in m1.items() if g not in matched1},
        a2_only={g: s for g, s in m2.items() if g not in used2},
    )


@dataclass
class ComparisonReport:
    rows: list[SpaceComparison] = field(default_factory=list)
    excluded_fields: dict[str, str] = field(default_factory=dict)
    membership: dict[str, MembershipDiff] = field(default_factory=dict)

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


def compare(a1_out, a2_out, *, rules=None, schedule: dict[str, str] | None = None,
            registry=None) -> ComparisonReport:
    """Compare two semantic passes over the same spaces."""
    schedule = schedule or {}
    a1_map = {s.space_id: s for s in a1_out.spaces}
    a2_map = {s.space_id: s for s in a2_out.spaces}
    rows = [
        compare_space(a1_map.get(sid), a2_map.get(sid), rules=rules,
                      schedule_label=schedule.get(sid), registry=registry)
        for sid in sorted(set(a1_map) | set(a2_map))
    ]
    _, excluded = comparable_fields(registry)
    return ComparisonReport(
        rows,
        excluded_fields=excluded,
        membership={k: membership_diff(a1_out, a2_out, k)
                    for k in ("APARTMENT", "ZONE")},
    )
