"""Scoped owner / project claims (R8.7): an owner answer applies exactly where it was given, never further.

A claim names its scope (project, source revision, region, spaces, items) and the purposes it may serve. `applies`
compares a use against that scope field by field; any mismatch is OWNER_SCOPE_MISMATCH with the fields named.
A claim scoped to a revision whose exact source is still pending may serve SHADOW / DIAGNOSTIC work only; a
release use is refused until a claim anchored to the exact source supersedes it.

No claim is ever generalised: a field the claim leaves unrestricted must be listed in `unrestricted` explicitly,
so "not mentioned" never means "applies everywhere". Project-agnostic; stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

APPLIES = "APPLIES"
OWNER_SCOPE_MISMATCH = "OWNER_SCOPE_MISMATCH"
PURPOSE_NOT_AUTHORISED = "PURPOSE_NOT_AUTHORISED"
CLAIM_NOT_ACTIVE = "CLAIM_NOT_ACTIVE"

SHADOW_DIAGNOSTIC = "SHADOW_DIAGNOSTIC"
RELEASE = "RELEASE"

ACTIVE = "ACTIVE"
SUPERSEDED = "SUPERSEDED"
SCOPE_FIELDS = ("project", "revision_id", "region_id", "space_ids", "items")


@dataclass(frozen=True)
class ScopedClaim:
    claim_id: str
    kind: str                                    # e.g. NATIVE_UNIT, PLAN_SELECTION, CEILING_FOOTPRINT_RULE
    value: dict
    project: str
    revision_id: str
    region_id: str | None = None
    space_ids: frozenset = frozenset()
    items: frozenset = frozenset()
    unrestricted: frozenset = frozenset()        # scope fields deliberately NOT restricted (stated, never implied)
    purposes: tuple = (SHADOW_DIAGNOSTIC,)
    authority: str = ""
    anchor_state: str = ""
    status: str = ACTIVE
    supersedes: str | None = None
    evidence: dict = field(default_factory=dict)


def applies(claim: ScopedClaim, *, project: str, revision_id: str, purpose: str, region_id: str | None = None,
            space_id: str | None = None, item: str | None = None) -> dict:
    if claim.status != ACTIVE:
        return {"state": CLAIM_NOT_ACTIVE, "claim_id": claim.claim_id, "mismatched": ["status"]}
    mismatched = []
    if claim.project != project:
        mismatched.append("project")
    if claim.revision_id != revision_id:
        mismatched.append("revision_id")
    if "region_id" not in claim.unrestricted and claim.region_id != region_id:
        mismatched.append("region_id")
    if "space_ids" not in claim.unrestricted and space_id not in claim.space_ids:
        mismatched.append("space_ids")
    if "items" not in claim.unrestricted and item not in claim.items:
        mismatched.append("items")
    if mismatched:
        return {"state": OWNER_SCOPE_MISMATCH, "claim_id": claim.claim_id, "mismatched": mismatched}
    if purpose not in claim.purposes:
        return {"state": PURPOSE_NOT_AUTHORISED, "claim_id": claim.claim_id, "mismatched": ["purpose"],
                "allowed_purposes": list(claim.purposes)}
    return {"state": APPLIES, "claim_id": claim.claim_id, "mismatched": [], "value": dict(claim.value)}


def from_record(r: dict) -> ScopedClaim:
    s = r["scope"]
    return ScopedClaim(r["claim_id"], r["kind"], dict(r["value"]), s["project"], s["revision_id"], s.get("region_id"),
                       frozenset(s.get("space_ids") or ()), frozenset(s.get("items") or ()),
                       frozenset(s.get("unrestricted") or ()), tuple(r["purposes"]), r.get("authority", ""),
                       r.get("anchor_state", ""), r.get("status", ACTIVE), r.get("supersedes"), dict(r.get("evidence") or {}))
