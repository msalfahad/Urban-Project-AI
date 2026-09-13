"""A1 — Semantic / Scope schema.

A1's job changed. It no longer measures: E23 and E25 do that, and they do it
from the drawing's own vector geometry, which no model can beat. A1 now attaches
MEANING to geometry that already exists — what a space is, whose apartment it
belongs to, whether it is in scope, which trades care about it.

The hard rule is enforced here rather than requested in the prompt: a semantic
record carries NO geometry. If the model returns an area, a perimeter or a
dimension, the record is rejected. A1 cannot silently edit E23/E25 because the
schema gives it nowhere to put a number.

When A1 believes the geometry is wrong it raises a GEOMETRY_CHALLENGE, which is
a message to the engine, not an edit.

One lesson from this project is baked into the label handling: on AR-00 the room
labelled كوي / IRON is the same physical space the old MEASURER calls مطبخ. A label
is one signal among several, never the mapping itself — so `label_source` and
`confidence_basis` are required, and confidence must name the evidence that
supports it rather than expressing a feeling.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from engine.trades import RULE_REQUIRED, TradeError, validate_all

# The vocabulary will change — SERVICE_ROOM will one day split into
# MECHANICAL_ROOM, ELECTRICAL_ROOM and PUMP_ROOM. Every record carries the
# version it was written under so an old project stays interpretable instead of
# silently depending on a enum that moved underneath it.
SEMANTIC_SCHEMA_VERSION = "2.0"

# FROZEN canonical taxonomy v2.0, approved by the owner 13 Sep 2026.
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
CONFIDENCE = {"HIGH", "MEDIUM", "LOW", "VERY_LOW"}
SCOPES = {"IN_SCOPE", "OUT_OF_SCOPE", "AMBIGUOUS"}

# Confidence is derived from which independent signals agree, not asserted.
CONFIDENCE_EVIDENCE = {
    "HIGH": "drawing text entity + room polygon + schedule agree",
    "MEDIUM": "vision label + geometry + adjacency agree",
    "LOW": "vision label only",
    "VERY_LOW": "inferred from context, no label present",
}

# Anything that smells like a measurement. A1 has no business returning one.
_GEOMETRY_KEY = re.compile(
    r"area|perimeter|length|width|height|dimension|_m2|_mm\b|polygon|coordinate",
    re.IGNORECASE)


class SemanticError(ValueError):
    """A1 returned something outside its remit — usually a number."""


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


@dataclass
class SpaceSemantics:
    """What one space MEANS. No geometry lives here, by design."""

    space_id: str
    semantic_label: str
    label_source: str
    label_confidence: str
    confidence_basis: str
    scope_status: str
    original_drawing_label: str = ""
    floor_id: str = ""
    zone_id: str = ""
    apartment_id: str = ""
    space_function: str = ""
    trade_relevance: list[str] = field(default_factory=list)
    drawing_notes: str = ""
    schedule_references: list[str] = field(default_factory=list)
    special_conditions: str = ""
    semantic_conflicts: list[str] = field(default_factory=list)
    geometry_challenge: str = ""          # a message to the engine, not an edit
    trade_notes: str = ""                 # free text ABOUT trades, never a trade id
    # When a trade cannot be decided, name the rule that is missing in a form a
    # router can act on. Prose alone cannot be grouped, counted or assigned.
    missing_rule_id: str = ""
    missing_rule_description: str = ""
    missing_required_fields: list[str] = field(default_factory=list)
    semantic_schema_version: str = SEMANTIC_SCHEMA_VERSION

    def validate(self) -> None:
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
        if self.label_confidence not in CONFIDENCE:
            raise SemanticError(
                f"{self.space_id}: label_confidence {self.label_confidence!r} is invalid")
        if self.scope_status not in SCOPES:
            raise SemanticError(
                f"{self.space_id}: scope_status {self.scope_status!r} is invalid")
        if not self.confidence_basis.strip():
            raise SemanticError(
                f"{self.space_id}: confidence must name the evidence behind it — "
                f"for {self.label_confidence} that is "
                f"{CONFIDENCE_EVIDENCE[self.label_confidence]!r}")
        # A HIGH label read only by a vision model is a contradiction: the whole
        # point of the scale is which independent signals agreed.
        if self.label_confidence == "HIGH" and self.label_source == "VISION_MODEL":
            raise SemanticError(
                f"{self.space_id}: HIGH confidence cannot rest on VISION_MODEL alone — "
                "that is LOW by definition")
        if self.label_source == "UNKNOWN" and self.label_confidence in ("HIGH", "MEDIUM"):
            raise SemanticError(
                f"{self.space_id}: no label source, so confidence cannot be "
                f"{self.label_confidence}")
        # Trades are a registry, not prose: they feed rules, quantities and a
        # BOQ, so an invented string breaks the chain at the money end.
        try:
            validate_all(self.trade_relevance)
        except TradeError as exc:
            raise SemanticError(f"{self.space_id}: {exc}") from exc
        # Applicability that depends on a finish schedule nobody supplied is a
        # routed question. Generic construction knowledge is not project scope.
        if RULE_REQUIRED in self.trade_relevance and not self.missing_rule_id.strip():
            raise SemanticError(
                f"{self.space_id}: RULE_REQUIRED needs a machine-readable "
                "missing_rule_id (e.g. CERAMIC_WALL_FINISH_IRON_ROOM). Free text in "
                "trade_notes cannot be grouped, counted or routed.")
        if self.missing_rule_id and RULE_REQUIRED not in self.trade_relevance:
            raise SemanticError(
                f"{self.space_id}: missing_rule_id is set but the trade is not marked "
                "RULE_REQUIRED — the record would claim a decision it does not have.")


@dataclass
class SemanticOutput:
    spaces: list[SpaceSemantics] = field(default_factory=list)
    not_a_space: list[str] = field(default_factory=list)
    notes: str = ""
    semantic_schema_version: str = SEMANTIC_SCHEMA_VERSION

    def validate(self) -> None:
        seen: set[str] = set()
        for s in self.spaces:
            s.validate()
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
    def from_dict(cls, data: dict[str, Any]) -> "SemanticOutput":
        raw = data.get("spaces", [])
        for r in raw:
            bad = [k for k in r if _GEOMETRY_KEY.search(k)]
            if bad:
                raise SemanticError(
                    f"{r.get('space_id', '?')}: A1 returned geometry field(s) {bad} — "
                    "measurement belongs to E23/E25. Raise a geometry_challenge instead.")
        out = cls(
            spaces=[
                SpaceSemantics(
                    space_id=r.get("space_id", ""),
                    semantic_label=r.get("semantic_label", ""),
                    label_source=r.get("label_source", "UNKNOWN"),
                    label_confidence=r.get("label_confidence", "VERY_LOW"),
                    confidence_basis=r.get("confidence_basis", ""),
                    scope_status=r.get("scope_status", "AMBIGUOUS"),
                    original_drawing_label=r.get("original_drawing_label", ""),
                    floor_id=r.get("floor_id", ""),
                    zone_id=r.get("zone_id", ""),
                    apartment_id=r.get("apartment_id", ""),
                    space_function=r.get("space_function", ""),
                    trade_relevance=list(r.get("trade_relevance", [])),
                    drawing_notes=r.get("drawing_notes", ""),
                    schedule_references=list(r.get("schedule_references", [])),
                    special_conditions=r.get("special_conditions", ""),
                    semantic_conflicts=list(r.get("semantic_conflicts", [])),
                    geometry_challenge=r.get("geometry_challenge", ""),
                    trade_notes=r.get("trade_notes", ""),
                    missing_rule_id=r.get("missing_rule_id", ""),
                    missing_rule_description=r.get("missing_rule_description", ""),
                    missing_required_fields=list(r.get("missing_required_fields", [])),
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
        out.validate()
        return out
