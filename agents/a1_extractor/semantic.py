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
labelled كوي / IRON is the same physical space the old qiyal calls مطبخ. A label
is one signal among several, never the mapping itself — so `label_source` and
`confidence_basis` are required, and confidence must name the evidence that
supports it rather than expressing a feeling.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

SEMANTIC_LABELS = {
    "BEDROOM", "MASTER_BEDROOM", "SALON", "DINING", "KITCHEN", "BATHROOM",
    "WASHROOM", "DRESS", "IRON_ROOM", "STORE", "CORRIDOR", "LOBBY", "ENTRANCE",
    "STAIR", "STAIR_LANDING", "LIFT_SHAFT", "SHAFT", "VOID", "TERRACE",
    "BALCONY", "MAID_ROOM", "DRIVER_ROOM", "LAUNDRY", "SERVICE_ROOM",
    "ROOF_ROOM", "EXTERNAL_AREA", "OPEN_PLAN", "UNKNOWN",
}

# Spaces a takeoff loses most often. A1 is asked to account for these by name so
# that "we did not see one" is a statement rather than an omission.
COMMONLY_MISSED = {
    "STORE", "SHAFT", "TERRACE", "BALCONY", "STAIR_LANDING", "VOID", "CORRIDOR",
    "SERVICE_ROOM", "MAID_ROOM", "LAUNDRY", "IRON_ROOM", "ROOF_ROOM",
    "LIFT_SHAFT", "EXTERNAL_AREA", "OPEN_PLAN",
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

    def validate(self) -> None:
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


@dataclass
class SemanticOutput:
    spaces: list[SpaceSemantics] = field(default_factory=list)
    not_a_space: list[str] = field(default_factory=list)
    notes: str = ""

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
                )
                for r in raw
            ],
            not_a_space=list(data.get("not_a_space", [])),
            notes=data.get("notes", ""),
        )
        out.validate()
        return out
