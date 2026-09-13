"""A1 — Semantic / Scope schema.

A1's job changed twice. It no longer measures: E23 and E25 do that, from the
drawing's own vector geometry, which no model can beat. And since Run 0 it no
longer decides trades either: E27 does that, from the project's rule library.
A1 now attaches MEANING to geometry that already exists — what a space is,
whose apartment it belongs to, whether it is in scope.

Three hard rules are enforced here rather than requested in the prompt.

1. A semantic record carries NO geometry. If the model returns an area, a
   perimeter or a dimension, the record is rejected. A1 cannot silently edit
   E23/E25 because the schema gives it nowhere to put a number. When A1 believes
   the geometry is wrong it raises a GEOMETRY_CHALLENGE, which is a message to
   the engine, not an edit.

2. Identifiers are chosen from a registry, never written. Run 0 asked for
   `apartment_id` as free text; A1 answered APT-EAST and A2 answered APT-01 and
   the comparator scored 0% agreement on what may well have been the same
   apartment. The same schema hole let both invent a zone hierarchy for a
   project that has no approved zone ontology at all. Now the canonical ids
   exist before either agent runs, and UNKNOWN and AMBIGUOUS are real answers.

3. Confidence is per field. "No finish schedule exists, therefore nothing can be
   HIGH" conflated two different questions: a drawing text entity reading حمام
   inside a valid room polygon is strong evidence about what the room IS, and
   says nothing at all about what finish it takes. Those now live in separate
   fields and neither can drag the other down.

One lesson from this project stays baked into the label handling: on AR-00 the
room labelled كوي / IRON is the same physical space the MEASURER calls مطبخ. A
label is one signal among several, never the mapping itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from engine.group_registry import APARTMENT, ZONE, GroupRegistry, GroupRegistryError

# The vocabulary will change — SERVICE_ROOM will one day split into
# MECHANICAL_ROOM, ELECTRICAL_ROOM and PUMP_ROOM. Every record carries the
# version it was written under so an old project stays interpretable instead of
# silently depending on an enum that moved underneath it.
#
# 3.0: canonical apartment/zone ids, per-field confidence, trade relevance
#      removed (it belongs to E27).
SEMANTIC_SCHEMA_VERSION = "3.0"

# FROZEN canonical taxonomy v2.0, approved by the owner 13 Sep 2026. The label
# vocabulary did not change in schema 3.0 — only what surrounds it.
# Space FUNCTION only. A label never implies a finish and never implies scope:
# BATHROOM does not mean wall ceramic (E27 decides), TERRACE does not mean
# excluded (scope_status decides). Synonyms live in the alias registry, which is
# large on purpose so this list can stay small.
SEMANTIC_LABELS = {
    "BEDROOM", "MASTER_BEDROOM",
    "SALON", "LIVING_ROOM", "DINING", "OPEN_PLAN_LIVING",
    "KITCHEN",
    "BATHROOM", "WC", "WASHROOM",
    "DRESSING_ROOM", "IRON_ROOM", "LAUNDRY_ROOM", "STORE",
    "CORRIDOR", "LOBBY", "ENTRANCE",
    "MAID_ROOM", "DRIVER_ROOM", "SERVICE_ROOM",
    "STAIR", "STAIR_LANDING", "STAIR_VOID",
    "ELEVATOR_SHAFT", "SHAFT", "SERVICE_SHAFT",
    "VOID", "DOUBLE_HEIGHT_VOID",
    "BALCONY", "TERRACE",
    "ROOF_ROOM", "ROOF_AREA",
    "GARAGE", "PARKING",
    "EXTERNAL_AREA",
    "UNKNOWN", "AMBIGUOUS", "NOT_A_SPACE",
}

# Spaces a takeoff loses most often. A1 is asked to account for these by name so
# that "we did not see one" is a statement rather than an omission.
COMMONLY_MISSED = {
    "STORE", "SHAFT", "SERVICE_SHAFT", "TERRACE", "BALCONY", "STAIR_LANDING",
    "STAIR_VOID", "VOID", "DOUBLE_HEIGHT_VOID", "CORRIDOR", "SERVICE_ROOM",
    "MAID_ROOM", "LAUNDRY_ROOM", "IRON_ROOM", "ROOF_ROOM", "ROOF_AREA",
    "ELEVATOR_SHAFT", "EXTERNAL_AREA", "OPEN_PLAN_LIVING",
}

LABEL_SOURCES = {"DWG_TEXT_ENTITY", "PDF_TEXT", "VISION_MODEL", "HUMAN_VERIFIED", "UNKNOWN"}
SCOPES = {"IN_SCOPE", "OUT_OF_SCOPE", "AMBIGUOUS"}

# NOT_ESTABLISHED is not a low confidence. It means the evidence for this
# particular question was never supplied, which is a different fact from weak
# evidence and routes differently: one is a question for the owner, the other is
# a question for a surveyor.
NOT_ESTABLISHED = "NOT_ESTABLISHED"
CONFIDENCE = {"HIGH", "MEDIUM", "LOW", "VERY_LOW", NOT_ESTABLISHED}

# Confidence is derived from which independent signals agree, per question.
# These are deliberately NOT the same ladder: what makes a LABEL certain has
# nothing to do with what makes SCOPE certain.
LABEL_EVIDENCE = {
    "HIGH": "a drawing text entity inside this space's polygon, unambiguous in the alias registry",
    "MEDIUM": "text plus geometry/adjacency agree, or the label resolved through an alias",
    "LOW": "no legible label — read from fixtures, proportions or adjacency",
    "VERY_LOW": "inferred from position alone",
    NOT_ESTABLISHED: "no evidence of any kind was available",
}
SCOPE_EVIDENCE = {
    "HIGH": "the owner's brief names this space or the block containing it",
    "MEDIUM": "the brief states a criterion that clearly covers this space",
    "LOW": "scope inferred from the brief by extension",
    "VERY_LOW": "scope guessed from context",
    NOT_ESTABLISHED: "the brief does not reach this space — a question for the owner",
}
APARTMENT_EVIDENCE = {
    "HIGH": "access and enclosure on the drawing place this space in one unit only",
    "MEDIUM": "adjacency and position place it in one unit, with no contradicting access",
    "LOW": "position only",
    "VERY_LOW": "no better than a guess",
    NOT_ESTABLISHED: "no topological evidence was available",
}

# Anything that smells like a measurement. A1 has no business returning one.
_GEOMETRY_KEY = re.compile(
    r"area|perimeter|length|width|height|dimension|_m2|_mm\b|polygon|coordinate",
    re.IGNORECASE)

# Fields from schema 2.0 that no longer exist, and why. A stale prompt or a
# cached model habit must fail loudly rather than have its answer dropped on the
# floor — a silently ignored trade decision is worse than a rejected record.
RETIRED_FIELDS = {
    "trade_relevance": "E27 decides trade relevance from the project rule library. "
                       "Raise a trade_challenge instead of listing trades.",
    "trade_notes": "use trade_challenges[].note",
    "missing_rule_id": "E27 generates missing rule ids. Raise a trade_challenge.",
    "missing_rule_description": "use trade_challenges[].note",
    "label_confidence": "renamed to semantic_label_confidence — confidence is now "
                        "per field, so the unqualified name is ambiguous.",
}

# What A1 is allowed to push back WITH. Both are messages, never quantities.
TRADE_RULE_CHALLENGE = "TRADE_RULE_CHALLENGE"
DRAWING_NOTE_CONFLICT = "DRAWING_NOTE_CONFLICT"
CHALLENGE_KINDS = {TRADE_RULE_CHALLENGE, DRAWING_NOTE_CONFLICT}


class SemanticError(ValueError):
    """A1 returned something outside its remit — usually a number or an id."""


@dataclass
class SemanticInput:
    """What A1 is given: geometry that already exists, and the project's scope."""

    project_id: str
    drawing_id: str
    drawing_revision: str
    floor_id: str
    scope_brief: str = ""
    # space_id -> whatever E23/E25 established. Passed through untouched.
    geometry: dict[str, dict[str, Any]] = field(default_factory=dict)
    # The canonical groups an agent may assign to. Required before a run.
    groups: GroupRegistry | None = None


@dataclass
class TradeChallenge:
    """A1 disagreeing with, or missing, a trade rule. Not a trade decision."""

    kind: str
    note: str
    trade: str = ""

    def validate(self, space_id: str) -> None:
        if self.kind not in CHALLENGE_KINDS:
            raise SemanticError(
                f"{space_id}: trade challenge kind {self.kind!r} is not one of "
                f"{sorted(CHALLENGE_KINDS)}")
        if not self.note.strip():
            raise SemanticError(
                f"{space_id}: a {self.kind} with no note is not actionable")
        # Naming a trade is optional; naming one that does not exist is not. A
        # challenge has to reach a queue, and a queue is keyed on the registry.
        if self.trade:
            from engine.trades import TradeError, validate_all
            try:
                validate_all([self.trade])
            except TradeError as exc:
                raise SemanticError(f"{space_id}: {exc}") from exc


@dataclass
class SpaceSemantics:
    """What one space MEANS. No geometry and no trade decision live here."""

    space_id: str
    semantic_label: str
    label_source: str
    semantic_label_confidence: str
    confidence_basis: str
    scope_status: str
    scope_confidence: str = NOT_ESTABLISHED
    scope_basis: str = ""
    original_drawing_label: str = ""
    floor_id: str = ""
    # Canonical ids only — validated against the project's group registry.
    apartment_id: str = "UNKNOWN"
    apartment_membership_confidence: str = NOT_ESTABLISHED
    apartment_basis: str = ""
    apartment_description: str = ""       # free text ABOUT the unit, never an id
    zone_id: str = "UNKNOWN"
    zone_membership_confidence: str = NOT_ESTABLISHED
    zone_description: str = ""            # free text ABOUT the zone, never an id
    schedule_confidence: str = NOT_ESTABLISHED
    space_function: str = ""
    drawing_notes: str = ""
    schedule_references: list[str] = field(default_factory=list)
    special_conditions: str = ""
    semantic_conflicts: list[str] = field(default_factory=list)
    geometry_challenge: str = ""          # a message to the engine, not an edit
    trade_challenges: list[TradeChallenge] = field(default_factory=list)
    semantic_schema_version: str = SEMANTIC_SCHEMA_VERSION

    def validate(self, registry: GroupRegistry | None = None) -> None:
        if self.space_function.strip().upper().replace(" ", "_") == self.semantic_label:
            raise SemanticError(
                f"{self.space_id}: space_function repeats semantic_label. The label "
                "is the functional CLASS; space_function is an optional human "
                "subtype such as 'Guest Bedroom' or 'Water pump room'.")
        if not self.space_id.strip():
            raise SemanticError("space_id must not be empty")
        if self.semantic_label not in SEMANTIC_LABELS:
            raise SemanticError(
                f"{self.space_id}: semantic_label {self.semantic_label!r} is not one of "
                f"{sorted(SEMANTIC_LABELS)}")
        if self.label_source not in LABEL_SOURCES:
            raise SemanticError(
                f"{self.space_id}: label_source {self.label_source!r} is invalid")
        for name in ("semantic_label_confidence", "scope_confidence",
                     "apartment_membership_confidence", "zone_membership_confidence",
                     "schedule_confidence"):
            if getattr(self, name) not in CONFIDENCE:
                raise SemanticError(
                    f"{self.space_id}: {name} {getattr(self, name)!r} is invalid — "
                    f"one of {sorted(CONFIDENCE)}")
        if self.scope_status not in SCOPES:
            raise SemanticError(
                f"{self.space_id}: scope_status {self.scope_status!r} is invalid")

        # --- each confidence names its own evidence -------------------------
        if not self.confidence_basis.strip():
            raise SemanticError(
                f"{self.space_id}: semantic_label_confidence must name the evidence "
                f"behind it — for {self.semantic_label_confidence} that is "
                f"{LABEL_EVIDENCE[self.semantic_label_confidence]!r}")
        if self.scope_confidence != NOT_ESTABLISHED and not self.scope_basis.strip():
            raise SemanticError(
                f"{self.space_id}: scope_confidence is {self.scope_confidence} but "
                f"scope_basis is empty — for that level the evidence is "
                f"{SCOPE_EVIDENCE[self.scope_confidence]!r}")
        if self.apartment_membership_confidence != NOT_ESTABLISHED \
                and not self.apartment_basis.strip():
            raise SemanticError(
                f"{self.space_id}: apartment_membership_confidence is "
                f"{self.apartment_membership_confidence} but apartment_basis is empty — "
                f"for that level the evidence is "
                f"{APARTMENT_EVIDENCE[self.apartment_membership_confidence]!r}")

        # A HIGH label read only by a vision model is a contradiction: the whole
        # point of the scale is which independent signals agreed.
        if self.semantic_label_confidence == "HIGH" and self.label_source == "VISION_MODEL":
            raise SemanticError(
                f"{self.space_id}: HIGH confidence cannot rest on VISION_MODEL alone — "
                "that is LOW by definition")
        if self.label_source == "UNKNOWN" and self.semantic_label_confidence in (
                "HIGH", "MEDIUM"):
            raise SemanticError(
                f"{self.space_id}: no label source, so semantic_label_confidence "
                f"cannot be {self.semantic_label_confidence}")

        # --- confidence and answer must not contradict each other -----------
        # Fail closed: no scope evidence means the scope question is open, and an
        # open question is AMBIGUOUS. It is never IN_SCOPE by default.
        if self.scope_confidence == NOT_ESTABLISHED and self.scope_status != "AMBIGUOUS":
            raise SemanticError(
                f"{self.space_id}: scope_status {self.scope_status} with no scope "
                "evidence. A scope decision nobody can trace is an assumption — "
                "answer AMBIGUOUS and let a human settle it.")
        if self.apartment_id in ("UNKNOWN", "AMBIGUOUS") \
                and self.apartment_membership_confidence in ("HIGH", "MEDIUM"):
            raise SemanticError(
                f"{self.space_id}: apartment_id is {self.apartment_id} but membership "
                f"confidence is {self.apartment_membership_confidence} — a confident "
                "non-answer is a contradiction.")

        for c in self.trade_challenges:
            c.validate(self.space_id)

        # --- identifiers come from the registry ------------------------------
        if registry is None:
            raise SemanticError(
                f"{self.space_id}: no group registry supplied, so apartment_id and "
                "zone_id cannot be validated. Run 0 shipped without one and the "
                "comparison was meaningless; validation is not optional now.")
        for kind, value in ((APARTMENT, self.apartment_id), (ZONE, self.zone_id)):
            try:
                registry.validate_assignment(kind, value, space_id=self.space_id)
            except GroupRegistryError as exc:
                raise SemanticError(str(exc)) from exc
        # With no ontology, zone_id is forced to UNKNOWN; claiming confidence
        # about a hierarchy that does not exist is the invention we removed.
        if not registry.zone_ontology_defined \
                and self.zone_membership_confidence != NOT_ESTABLISHED:
            raise SemanticError(
                f"{self.space_id}: project {registry.project} has no zone ontology, so "
                f"zone_membership_confidence must be {NOT_ESTABLISHED}, not "
                f"{self.zone_membership_confidence}.")


@dataclass
class SemanticOutput:
    spaces: list[SpaceSemantics] = field(default_factory=list)
    not_a_space: list[str] = field(default_factory=list)
    notes: str = ""
    semantic_schema_version: str = SEMANTIC_SCHEMA_VERSION

    def validate(self, registry: GroupRegistry | None = None) -> None:
        seen: set[str] = set()
        for s in self.spaces:
            s.validate(registry)
            if s.space_id in seen:
                raise SemanticError(f"{s.space_id} classified twice")
            seen.add(s.space_id)
        for sid in self.not_a_space:
            if sid in seen:
                raise SemanticError(f"{sid} is both classified and marked not-a-space")
        # NOT_A_SPACE exists in the taxonomy AND as a list. Using both for one
        # space is the duplication that creates two sources of truth, so a
        # NOT_A_SPACE record must live in the list instead.
        for s in self.spaces:
            if s.semantic_label == "NOT_A_SPACE":
                raise SemanticError(
                    f"{s.space_id}: use the not_a_space[] list rather than the "
                    "NOT_A_SPACE label, so there is one place to look.")

    def covers(self, detected: list[str]) -> list[str]:
        """Detected spaces A1 left semantically invisible."""
        accounted = {s.space_id for s in self.spaces} | set(self.not_a_space)
        return [d for d in detected if d not in accounted]

    @classmethod
    def from_dict(cls, data: dict[str, Any], *,
                  registry: GroupRegistry | None = None) -> "SemanticOutput":
        raw = data.get("spaces", [])
        for r in raw:
            sid = r.get("space_id", "?")
            bad = [k for k in r if _GEOMETRY_KEY.search(k)]
            if bad:
                raise SemanticError(
                    f"{sid}: A1 returned geometry field(s) {bad} — measurement belongs "
                    "to E23/E25. Raise a geometry_challenge instead.")
            retired = [k for k in r if k in RETIRED_FIELDS]
            if retired:
                raise SemanticError(
                    f"{sid}: field(s) {retired} were removed in schema "
                    f"{SEMANTIC_SCHEMA_VERSION}. "
                    + " ".join(f"{k}: {RETIRED_FIELDS[k]}" for k in retired))
        out = cls(
            spaces=[
                SpaceSemantics(
                    space_id=r.get("space_id", ""),
                    semantic_label=r.get("semantic_label", ""),
                    label_source=r.get("label_source", "UNKNOWN"),
                    semantic_label_confidence=r.get("semantic_label_confidence",
                                                    NOT_ESTABLISHED),
                    confidence_basis=r.get("confidence_basis", ""),
                    scope_status=r.get("scope_status", "AMBIGUOUS"),
                    scope_confidence=r.get("scope_confidence", NOT_ESTABLISHED),
                    scope_basis=r.get("scope_basis", ""),
                    original_drawing_label=r.get("original_drawing_label", ""),
                    floor_id=r.get("floor_id", ""),
                    apartment_id=r.get("apartment_id", "UNKNOWN"),
                    apartment_membership_confidence=r.get(
                        "apartment_membership_confidence", NOT_ESTABLISHED),
                    apartment_basis=r.get("apartment_basis", ""),
                    apartment_description=r.get("apartment_description", ""),
                    zone_id=r.get("zone_id", "UNKNOWN"),
                    zone_membership_confidence=r.get("zone_membership_confidence",
                                                     NOT_ESTABLISHED),
                    zone_description=r.get("zone_description", ""),
                    schedule_confidence=r.get("schedule_confidence", NOT_ESTABLISHED),
                    space_function=r.get("space_function", ""),
                    drawing_notes=r.get("drawing_notes", ""),
                    schedule_references=list(r.get("schedule_references", [])),
                    special_conditions=r.get("special_conditions", ""),
                    semantic_conflicts=list(r.get("semantic_conflicts", [])),
                    geometry_challenge=r.get("geometry_challenge", ""),
                    trade_challenges=[
                        TradeChallenge(kind=c.get("kind", ""), note=c.get("note", ""),
                                       trade=c.get("trade", ""))
                        for c in r.get("trade_challenges", [])
                    ],
                    semantic_schema_version=r.get("semantic_schema_version",
                                                  SEMANTIC_SCHEMA_VERSION),
                )
                for r in raw
            ],
            not_a_space=list(data.get("not_a_space", [])),
            notes=data.get("notes", ""),
            semantic_schema_version=data.get("semantic_schema_version",
                                             SEMANTIC_SCHEMA_VERSION),
        )
        out.validate(registry)
        return out
