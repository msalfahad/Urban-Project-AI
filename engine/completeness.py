"""E28 — Completeness Auditor.

The Test 1 failure was not a misread dimension. Both surveyors read every
dimension they looked at correctly, and between them they still left about a
third of the floor unmeasured — because a room nobody mentions produces no
error, no warning and no variance. Agreement between two readers says nothing
about the rooms neither one opened.

So this module refuses to let a detected region simply not appear. Every region
the geometry engine found must be dispositioned:

    DETECTED = IN_SCOPE + OUT_OF_SCOPE + AMBIGUOUS + NOT_A_SPACE

An unlisted region is an audit failure, not a rounding difference. Excluding a
space is fine — the terrace is excluded on the owner's instruction — but it has
to be excluded *out loud*, with its geometry still stored.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

SCOPES = ("IN_SCOPE", "OUT_OF_SCOPE", "AMBIGUOUS")


class CompletenessError(RuntimeError):
    """A detected space went missing — never downgraded to a warning."""


@dataclass
class AuditResult:
    detected: int
    in_scope: list[int] = field(default_factory=list)
    out_of_scope: list[int] = field(default_factory=list)
    ambiguous: list[int] = field(default_factory=list)
    not_a_space: list[int] = field(default_factory=list)
    unaccounted: list[int] = field(default_factory=list)
    double_counted: list[int] = field(default_factory=list)

    @property
    def accounted(self) -> int:
        return (len(self.in_scope) + len(self.out_of_scope)
                + len(self.ambiguous) + len(self.not_a_space))

    @property
    def ok(self) -> bool:
        return not self.unaccounted and not self.double_counted

    def raise_if_incomplete(self) -> None:
        if self.double_counted:
            raise CompletenessError(
                f"regions dispositioned more than once: {sorted(self.double_counted)}")
        if self.unaccounted:
            raise CompletenessError(
                f"{len(self.unaccounted)} detected region(s) have no disposition: "
                f"{sorted(self.unaccounted)} — a space may be excluded, but never "
                "silently omitted"
            )


def audit(detected_ids: list[int], spaces: list[dict], not_a_space: list[int]) -> AuditResult:
    """Prove every detected region was dealt with."""
    res = AuditResult(detected=len(detected_ids))
    seen: dict[int, int] = {}
    for sp in spaces:
        rid, scope = sp["region"], sp["scope"]
        if scope not in SCOPES:
            raise CompletenessError(f"region {rid}: scope {scope!r} not one of {SCOPES}")
        seen[rid] = seen.get(rid, 0) + 1
        {"IN_SCOPE": res.in_scope, "OUT_OF_SCOPE": res.out_of_scope,
         "AMBIGUOUS": res.ambiguous}[scope].append(rid)
    for rid in not_a_space:
        seen[rid] = seen.get(rid, 0) + 1
        res.not_a_space.append(rid)
    res.double_counted = [r for r, n in seen.items() if n > 1]
    res.unaccounted = [r for r in detected_ids if r not in seen]
    return res


def totals_by_scope(regions: dict[int, Decimal], spaces: list[dict]) -> dict[str, Decimal]:
    """Sum measured area per scope bucket. Code adds up, nobody else."""
    out = {s: Decimal(0) for s in SCOPES}
    for sp in spaces:
        a = regions.get(sp["region"])
        if a is not None:
            out[sp["scope"]] += a
    return out
