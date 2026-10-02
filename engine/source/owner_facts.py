"""OWNER PHYSICAL FACTS (R8.12) - a generic authority type, kept apart from owner CLAIMS (owner_claims).

A physical fact is an owner statement about what is BUILT, bound to source identity like a claim:
fact id + version, authority, revision + anchor + region + frame scope, part bindings (key + fingerprint + physical
reading), a statement, the DOMAINS it may affect, and supersession. It is data, never project logic in code.

A fact never edits a source record, never creates geometry and never carries a quantity. Per domain it has one
OUTCOME:
  OFFERED             recorded, not (yet) used in this domain
  APPLIED             it is the authority this domain used
  CORROBORATING_ONLY  the engine established the same reading independently; the fact adds confidence, not authority
  REJECTED_SCOPE      another revision / anchor / region / frame
  STALE               a bound part changed (fingerprint) or is missing
  CONFLICT            the engine's own reading contradicts it: review required, neither side overwrites the other

ENGINE vs OWNER (per bound part):
  ENGINE_ESTABLISHED_OWNER_AGREES      -> CORROBORATING_ONLY (engine authority stands)
  ENGINE_ESTABLISHED_OWNER_DISAGREES   -> CONFLICT (review)
  ENGINE_UNRESOLVED_OWNER_ESTABLISHES  -> the fact MAY be applied as reviewed OWNER_ROLE_AUTHORITY (part-scoped,
                                          always labelled as human authority, never as engine-derived)
  ENGINE_DISAGREES_OWNER_ESTABLISHES   -> CONFLICT (the source contradicts the owner reading; never silently applied)

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from . import owner_claims as OC

POLICY_ID = "OWNER_PHYSICAL_FACT_POLICY_V2"      # V2 (R8.15): + obstacle authority / threshold treatment domains
OFFERED, APPLIED, CORROBORATING_ONLY = "OFFERED", "APPLIED", "CORROBORATING_ONLY"
REJECTED_SCOPE, STALE, CONFLICT = "REJECTED_SCOPE", "STALE", "CONFLICT"
OUTCOMES = (OFFERED, APPLIED, CORROBORATING_ONLY, REJECTED_SCOPE, STALE, CONFLICT)

TOPOLOGY_ROLE = "TOPOLOGY_ROLE"                         # only through an explicit, reviewed part-scoped role claim
TOPOLOGY_CLOSURE_REVIEW = "TOPOLOGY_CLOSURE_REVIEW"
BLOCKER_CLASSIFICATION = "BLOCKER_CLASSIFICATION"
PASSAGE_ATTRIBUTES = "PASSAGE_ATTRIBUTES"
OBSTACLE_AUTHORITY = "OBSTACLE_AUTHORITY"             # V2: a built obstacle the engine geometry already realises
THRESHOLD_TREATMENT = "THRESHOLD_TREATMENT"           # V2: what is built in one door threshold (e.g. marble)
DOMAINS = (TOPOLOGY_ROLE, TOPOLOGY_CLOSURE_REVIEW, BLOCKER_CLASSIFICATION, PASSAGE_ATTRIBUTES, OBSTACLE_AUTHORITY,
           THRESHOLD_TREATMENT)
KIND_DOMAINS = {"OPEN_PASSAGE_CONSTRUCTION": (TOPOLOGY_CLOSURE_REVIEW, BLOCKER_CLASSIFICATION, PASSAGE_ATTRIBUTES),
                "BUILT_OBSTACLE": (OBSTACLE_AUTHORITY, BLOCKER_CLASSIFICATION),
                "PASSAGE_HEAD_CONDITION": (PASSAGE_ATTRIBUTES, BLOCKER_CLASSIFICATION),
                "THRESHOLD_FINISH_CONSTRUCTION": (THRESHOLD_TREATMENT, BLOCKER_CLASSIFICATION)}

AGREES = "ENGINE_ESTABLISHED_OWNER_AGREES"
DISAGREES = "ENGINE_ESTABLISHED_OWNER_DISAGREES"
OWNER_ONLY = "ENGINE_UNRESOLVED_OWNER_ESTABLISHES"
CONTRADICTED = "ENGINE_DISAGREES_OWNER_ESTABLISHES"
MATRIX = {AGREES: CORROBORATING_ONLY, DISAGREES: CONFLICT, OWNER_ONLY: "MAY_APPLY_AS_OWNER_ROLE_AUTHORITY",
          CONTRADICTED: CONFLICT}
ENGINE_ESTABLISHED, ENGINE_UNRESOLVED, ENGINE_CONTRARY = "ESTABLISHED", "UNRESOLVED", "CONTRARY"


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


@dataclass(frozen=True)
class PhysicalFact:
    fact_id: str
    version: int
    kind: str
    authority: tuple
    scope: dict
    parts: tuple                      # ((key, fingerprint, physical_reading), ...)
    statement: dict = field(default_factory=dict)
    allowed_domains: tuple = ()
    supersedes: tuple = ()

    @property
    def ref(self):
        return f"{self.fact_id}@v{self.version}"


def from_record(rec: dict) -> PhysicalFact:
    return PhysicalFact(rec["fact_id"], int(rec["version"]), rec["kind"], tuple(rec["authority"]), dict(rec["scope"]),
                        tuple((p["key"], p["fingerprint"], p["physical_reading"]) for p in rec["parts"]),
                        dict(rec.get("statement", {})),
                        tuple(rec.get("allowed_domains") or KIND_DOMAINS.get(rec["kind"], ())),
                        tuple(rec.get("supersedes", ())))


def bind(fact: PhysicalFact, inp) -> dict:
    """The fact's binding to THIS input: APPLIES, REJECTED_SCOPE or STALE (all parts or nothing)."""
    rev, sc = inp.revision, fact.scope
    base = {"fact": fact.ref, "parts": []}
    if rev is None or rev.revision_id != sc.get("source_revision_id") or \
            rev.anchor_sha256 != sc.get("source_anchor_sha256") or inp.region_id != sc.get("region_id") or \
            inp.frame_id != sc.get("frame_id"):
        return dict(base, binding=REJECTED_SCOPE)
    by_key = {p.identity.key: p for p in inp.parts}
    per = []
    for key, fp, reading in fact.parts:
        p = by_key.get(key)
        st = OC.PART_NOT_IN_SOURCE if p is None else (OC.APPLIES if OC.part_fingerprint(p) == fp else
                                                       OC.STALE_PART_FINGERPRINT)
        per.append({"key": key, "state": st, "physical_reading": reading})
    return dict(base, binding=OC.APPLIES if all(x["state"] == OC.APPLIES for x in per) else STALE, parts=per)


def compare(engine_state: str, owner_reading: str | None, engine_reading: str | None = None) -> str:
    """ENGINE vs OWNER matrix state for one bound part."""
    if owner_reading is None:
        return None
    if engine_state == ENGINE_ESTABLISHED:
        return AGREES if engine_reading in (None, owner_reading) else DISAGREES
    if engine_state == ENGINE_CONTRARY:
        return CONTRADICTED
    return OWNER_ONLY


def outcome(binding: dict, domain: str, *, used: bool, comparisons=()) -> str:
    """The fact's outcome in one domain."""
    if binding["binding"] == REJECTED_SCOPE:
        return REJECTED_SCOPE
    if binding["binding"] != OC.APPLIES:
        return STALE
    if any(c in (DISAGREES, CONTRADICTED) for c in comparisons):
        return CONFLICT
    if comparisons and all(c == AGREES for c in comparisons) and not used:
        return CORROBORATING_ONLY
    return APPLIED if used else OFFERED


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "outcomes": list(OUTCOMES), "domains": list(DOMAINS),
           "kind_domains": {k: list(v) for k, v in KIND_DOMAINS.items()}, "matrix": MATRIX,
           "binding": "revision + anchor + region + frame + every bound part's fingerprint (all or nothing)",
           "history": ["V1 (R8.12): topology role / closure review / blocker classification / passage attributes",
                       "V2 (R8.15): + OBSTACLE_AUTHORITY (BUILT_OBSTACLE) and THRESHOLD_TREATMENT "
                       "(THRESHOLD_FINISH_CONSTRUCTION) and PASSAGE_HEAD_CONDITION kinds - none reaches TOPOLOGY_ROLE"],
           "never": ["edits a source record", "creates geometry", "carries a quantity", "overwrites contradictory "
                     "geometry (CONFLICT -> review)", "enters a domain not allowed by its kind", "is project logic in "
                     "code"]}
    rec["digest"] = _digest(rec)
    return rec
