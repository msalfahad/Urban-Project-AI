"""E72 — a reference may only be opened where it maps to ONE space.

After a control is frozen, other references may be compared against it. The
temptation at that moment is to take a row labelled "Bedroom" from a
schedule, find a bedroom, and call the two a match. On this project that row
could be any of six bedrooms, and a comparison built on a forced mapping
produces a number that looks like evidence and is not.

So each reference row is resolved, and a row that does not resolve is
reported as REFERENCE_MAPPING_UNRESOLVED with the reason. A row with an
unresolved mapping is never compared, never averaged, and never counted as
agreement.

Two things have to be unambiguous before a comparison is allowed:

    THE MAPPING   this row is about exactly one space, and no other row
                  claims that space
    THE BASIS     the reference measures the same thing the engine does.
                  A LENGTH WITHOUT A BASIS IS NOT A LENGTH, and neither is
                  an area: a structural-opening area and a clear internal
                  finish-face area are different quantities of the same room

The sealed site benchmark is NOT a reference this module may open. It is
refused by name, in code, so that no future caller can reach it by passing a
path.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

RESOLVED = "REFERENCE_MAPPED_TO_ONE_SPACE"
UNRESOLVED = "REFERENCE_MAPPING_UNRESOLVED"

# Why a row did not resolve.
AMBIGUOUS_NAME = "NAME_MATCHES_MORE_THAN_ONE_SPACE"
NO_MATCH = "NAME_MATCHES_NO_SPACE"
DUPLICATE_CLAIM = "MORE_THAN_ONE_ROW_CLAIMS_THIS_SPACE"
BASIS_NOT_STATED = "REFERENCE_BASIS_NOT_STATED"
BASIS_INCOMPATIBLE = "REFERENCE_BASIS_IS_A_DIFFERENT_QUANTITY"
NO_VALUE = "ROW_CARRIES_NO_VALUE_TO_COMPARE"

REASONS = (AMBIGUOUS_NAME, NO_MATCH, DUPLICATE_CLAIM, BASIS_NOT_STATED,
           BASIS_INCOMPATIBLE, NO_VALUE)

# Files this module refuses to open, whatever it is asked.
#
# A sealed file is one that carries a KNOWN TOTAL for a project the engine
# is being tested on: a site benchmark, a manual qiyal, a previous BOQ, or
# an architect's own printed area take-off. Each is the only independent
# check its project has, and a check that has been read is spent. The seal
# is BY NAME because a rule kept in memory is not a rule.
SEALED = ("site_benchmark.json",
          "P7757_area_takeoff_benchmark.pdf")


class SealedReferenceError(RuntimeError):
    """Something tried to open a reference that must never reach an agent."""


def refuse_if_sealed(path: str) -> None:
    """The one guard that matters, enforced by name rather than by memory."""
    name = str(path).replace("\\\\", "/").rsplit("/", 1)[-1]
    if name in SEALED:
        raise SealedReferenceError(
            f"{name} is the sealed site benchmark. It is the only honest "
            "test this project has of whether the engine measures a real "
            "building, and reading it here would spend it. It is never "
            "opened by the engine, by an agent, or by a comparison")


@dataclass(frozen=True)
class ReferenceRow:
    """One row of some external document, as read, before any matching."""

    row_id: str
    label: str
    value: float | None = None
    unit: str = ""
    basis: str = ""
    source: str = ""


@dataclass(frozen=True)
class Resolution:
    row_id: str
    label: str
    status: str
    space_id: str = ""
    reason: str = ""
    candidates: tuple[str, ...] = ()
    value: float | None = None
    basis: str = ""
    why: str = ""

    @property
    def may_be_compared(self) -> bool:
        return self.status == RESOLVED

    def record(self) -> dict:
        return {"row_id": self.row_id, "label": self.label,
                "status": self.status, "space_id": self.space_id,
                "reason": self.reason,
                "candidate_space_ids": list(self.candidates),
                "value": self.value, "basis": self.basis,
                "may_be_compared": self.may_be_compared,
                "why": self.why}


@dataclass
class Report:
    resolutions: list = field(default_factory=list)
    compatible_bases: tuple = ()
    notes: dict = field(default_factory=dict)

    def record(self) -> dict:
        ok = [r for r in self.resolutions if r.may_be_compared]
        return {
            "rows": len(self.resolutions),
            "mapped_to_one_space": len(ok),
            "unresolved": len(self.resolutions) - len(ok),
            "by_reason": dict(Counter(
                r.reason for r in self.resolutions if r.reason)),
            "compatible_bases": list(self.compatible_bases),
            "resolutions": [r.record() for r in self.resolutions][:60],
            "rule": ("a row is compared only where it maps to exactly one "
                     "space AND states a basis the engine can be compared "
                     "against. An unresolved row is not compared, not "
                     "averaged and not counted as agreement"),
            "why_a_generic_row_is_refused": (
                "a schedule row labelled 'Bedroom' on a floor with six "
                "bedrooms is not evidence about any of them. Forcing it onto "
                "the nearest bedroom produces a number that looks like "
                "validation and is not"),
            "notes": dict(self.notes),
        }


def resolve(rows, spaces, *, compatible_bases=(), aliases=None) -> Report:
    """Map reference rows onto space ids, refusing anything ambiguous.

    `spaces` maps space_id -> a dict of names the space is known by
    (for example {"name_en": "Bedroom 1", "room_type": "BEDROOM"}). A row
    matches a space if its label equals the space id, or equals one of those
    names, case- and space-insensitively. A ROOM TYPE IS NOT A NAME: matching
    "Bedroom" against room_type BEDROOM is what produces the ambiguity this
    module exists to refuse, so type matches are collected as candidates and
    never as a resolution.
    """
    rep = Report(compatible_bases=tuple(compatible_bases))
    exact: dict = {}
    by_type: dict = {}
    for sid, names in (spaces or {}).items():
        exact.setdefault(_key(sid), []).append(sid)
        for field_name, val in (names or {}).items():
            if not val:
                continue
            if field_name == "room_type":
                by_type.setdefault(_key(val), []).append(sid)
            else:
                exact.setdefault(_key(val), []).append(sid)
    for k, v in (aliases or {}).items():
        exact.setdefault(_key(k), []).append(v)

    claims: dict = {}
    staged = []
    for row in rows:
        key = _key(row.label)
        hits = sorted(set(exact.get(key, ())))
        types = sorted(set(by_type.get(key, ())))
        staged.append((row, hits, types))
        if len(hits) == 1:
            claims[hits[0]] = claims.get(hits[0], 0) + 1

    for row, hits, types in staged:
        res = _resolve_one(row, hits, types, claims, rep.compatible_bases)
        rep.resolutions.append(res)
    return rep


def _resolve_one(row, hits, types, claims, bases) -> Resolution:
    common = dict(row_id=row.row_id, label=row.label, value=row.value,
                  basis=row.basis)
    if not hits and not types:
        return Resolution(status=UNRESOLVED, reason=NO_MATCH, why=(
            f"nothing on this floor is called {row.label!r}. A row that "
            "matches no space is not evidence about any space"), **common)
    if not hits and types:
        return Resolution(
            status=UNRESOLVED, reason=AMBIGUOUS_NAME, candidates=tuple(types),
            why=(f"{row.label!r} is a ROOM TYPE, and {len(types)} spaces on "
                 f"this floor are of that type ({', '.join(types[:6])}"
                 f"{'…' if len(types) > 6 else ''}). Picking one would "
                 "manufacture a comparison"), **common)
    if len(hits) > 1:
        return Resolution(
            status=UNRESOLVED, reason=AMBIGUOUS_NAME, candidates=tuple(hits),
            why=(f"{row.label!r} matches {len(hits)} spaces "
                 f"({', '.join(hits[:6])}). The reference does not say which "
                 "one it measured"), **common)
    sid = hits[0]
    if claims.get(sid, 0) > 1:
        return Resolution(
            status=UNRESOLVED, reason=DUPLICATE_CLAIM, candidates=(sid,),
            why=(f"{claims[sid]} rows resolve to {sid}. Either the reference "
                 "measured it more than once or two different rooms share a "
                 "name, and neither is settled here"), **common)
    if row.value is None:
        return Resolution(
            status=UNRESOLVED, reason=NO_VALUE, space_id=sid,
            why=(f"the row maps cleanly to {sid} and carries no value, so "
                 "there is nothing to compare. The mapping is recorded; the "
                 "comparison is not"), **common)
    if not row.basis:
        return Resolution(
            status=UNRESOLVED, reason=BASIS_NOT_STATED, space_id=sid,
            why=(f"the row maps cleanly to {sid} but does not say WHAT it "
                 "measured. A clear internal area and a structural-opening "
                 "area are different quantities of the same room, and a "
                 "number without its basis cannot be compared to one"),
            **common)
    if bases and row.basis not in bases:
        return Resolution(
            status=UNRESOLVED, reason=BASIS_INCOMPATIBLE, space_id=sid,
            why=(f"the row measures {row.basis}, and the engine measures "
                 f"{' or '.join(bases)}. Comparing them would report the "
                 "difference between two bases as an error"), **common)
    return Resolution(
        status=RESOLVED, space_id=sid,
        why=(f"{row.label!r} names exactly one space ({sid}), no other row "
             f"claims it, and the row states basis {row.basis}"), **common)


def _key(s) -> str:
    return " ".join(str(s or "").strip().lower().replace("_", " ").split())
