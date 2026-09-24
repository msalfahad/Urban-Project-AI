"""The three entities the engine keeps apart, and the vocabulary of statuses and evidence they carry.

A geometry component is what the drawing yields.  A semantic space is what a person would call a room.  A
measurement object is what a trade is measured on.  Confusing any two of them is how a wall sliver becomes floor
finish and how a room label ends up describing only the fragment that happened to contain its text.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from engine.qs_core import geom

NAMESPACE = uuid.UUID("6f3f1f8e-0c5a-5d2a-9a2b-1f1c2d3e4f50")

# ---------------------------------------------------------------- what a geometry component is made of
KIND_FLOOR_REGION = "FLOOR_REGION"          # usable floor: a candidate for room membership
KIND_WALL_BAND = "WALL_BAND"                # wall material: never floor finish
KIND_COLUMN = "COLUMN"                      # structure inside or beside a space
KIND_SLIVER = "SLIVER"                      # a drafting artefact too small or too thin to be a space
KIND_EXTERNAL = "EXTERNAL_OPEN"             # outside the enclosure
NON_ROOM_KINDS = (KIND_WALL_BAND, KIND_COLUMN, KIND_SLIVER)

# ---------------------------------------------------------------- statuses
ASSIGNED_TO_SPACE = "ASSIGNED_TO_SPACE"
NON_ROOM_GEOMETRY = "NON_ROOM_GEOMETRY"
EXTERNAL_OPEN_AREA = "EXTERNAL_OPEN_AREA"
UNRESOLVED = "UNRESOLVED"

HOST_ASSIGNED = "HOST_ASSIGNED"
HOST_WALL_UNRESOLVED = "HOST_WALL_UNRESOLVED"

SPACE_NAMED = "NAMED"
SPACE_UNNAMED = "UNNAMED_ON_DRAWING"
SPACE_LABEL_CONFLICT = "CONFLICTING_LABELS"

# ---------------------------------------------------------------- lineage across revisions
LINEAGE_UNCHANGED = "UNCHANGED"
LINEAGE_MODIFIED = "MODIFIED"
LINEAGE_NEW = "NEW"
LINEAGE_REMOVED = "REMOVED"
LINEAGE_SPLIT = "SPLIT"
LINEAGE_MERGED = "MERGED"
LINEAGE_REVIEW = "REVIEW_REQUIRED"

# ---------------------------------------------------------------- confidence, as a word rather than a number
CONFIDENCE_PROVEN = "PROVEN"                # the drawing settles it
CONFIDENCE_STRONG = "STRONG"                # one interpretation survives, others are excluded by evidence
CONFIDENCE_WEAK = "WEAK"                    # one interpretation leads but rivals remain
CONFIDENCE_NONE = "NONE"                    # nothing decides


@dataclass(frozen=True)
class Evidence:
    """Why the engine believes something.  Every classification carries these, and a reader can disagree."""
    rule: str
    detail: dict = field(default_factory=dict)

    def as_dict(self):
        return {"RULE": self.rule, "DETAIL": self.detail}


@dataclass
class Label:
    """A piece of text the drawing places at a point."""
    text: str
    x: float
    y: float
    source: str = "DRAWING_TEXT"


@dataclass
class GeometryComponent:
    """A connected piece of the drawing: floor cells, a wall band, a column, a sliver."""
    component_ref: str
    kind: str
    rects: list
    floor: str
    source_revision: str
    thickness: float = None          # wall bands only, in metres
    axis: str = None                 # wall bands only
    material_length: float = None    # wall lines only: the run that actually has material in it
    layer: str = None
    uid: str = None
    persistent_id: str = None
    status: str = None
    room_id: str = None
    evidence: list = field(default_factory=list)
    confidence: str = None

    @property
    def area(self):
        return geom.total_area(self.rects)

    @property
    def centroid(self):
        return geom.centroid(self.rects)

    @property
    def bbox(self):
        return geom.bbox(self.rects)

    @property
    def length(self):
        """A wall band's run, along its own axis.  Meaningless for a floor region, which is why it is a wall
        band's property and not a component's measurement."""
        b = self.bbox
        if self.axis == geom.AXIS_X:
            return b.width
        if self.axis == geom.AXIS_Y:
            return b.height
        return max(b.width, b.height)

    def as_dict(self):
        return {"COMPONENT_REF": self.component_ref, "UID": self.uid, "PERSISTENT_ID": self.persistent_id,
                "KIND": self.kind, "FLOOR": self.floor, "SOURCE_REVISION": self.source_revision,
                "AREA_M2": round(self.area, 6), "RECTANGLES": len(self.rects),
                "THICKNESS_M": self.thickness, "AXIS": self.axis, "LAYER": self.layer,
                "ROOM_ID": self.room_id, "STATUS": self.status, "CONFIDENCE": self.confidence,
                "EVIDENCE": [e.as_dict() for e in self.evidence]}


@dataclass
class Opening:
    """A door, window or other hole, with the geometry that decides which wall it belongs to."""
    opening_ref: str
    rect: geom.Rect                  # the clear opening, as drawn through the wall
    floor: str
    source_revision: str
    opening_type: str = "UNKNOWN"
    width: float = None
    height: float = None
    width_source: str = None
    height_source: str = None
    axis: str = None                 # the axis the opening runs along
    layer: str = None
    uid: str = None
    persistent_id: str = None
    host_component_ref: str = None
    host_thickness: float = None
    host_candidates: list = field(default_factory=list)
    host_evidence: list = field(default_factory=list)
    host_confidence: str = CONFIDENCE_NONE
    host_status: str = HOST_WALL_UNRESOLVED

    @property
    def area(self):
        if self.width is None or self.height is None:
            return None
        return self.width * self.height

    def as_dict(self):
        return {"OPENING_REF": self.opening_ref, "UID": self.uid, "PERSISTENT_ID": self.persistent_id,
                "FLOOR": self.floor, "SOURCE_REVISION": self.source_revision, "TYPE": self.opening_type,
                "GEOMETRY": self.rect.as_tuple(), "AXIS": self.axis,
                "WIDTH_M": self.width, "WIDTH_SOURCE": self.width_source,
                "HEIGHT_M": self.height, "HEIGHT_SOURCE": self.height_source,
                "AREA_M2": None if self.area is None else round(self.area, 6),
                "HOST_COMPONENT_REF": self.host_component_ref, "HOST_THICKNESS_M": self.host_thickness,
                "HOST_CANDIDATES": self.host_candidates,
                "HOST_ASSIGNMENT_CONFIDENCE": self.host_confidence,
                "HOST_ASSIGNMENT_STATUS": self.host_status,
                "HOST_EVIDENCE": [e.as_dict() for e in self.host_evidence]}


@dataclass
class SemanticSpace:
    """What a person would call a room: one or more floor components that continue into one another."""
    room_id: str
    floor: str
    source_revision: str
    component_refs: list
    rects: list = field(default_factory=list)
    label: str = None
    label_status: str = SPACE_UNNAMED
    labels_seen: list = field(default_factory=list)
    area: float = 0.0
    uid: str = None
    persistent_id: str = None
    status: str = ASSIGNED_TO_SPACE
    confidence: str = CONFIDENCE_PROVEN
    evidence: list = field(default_factory=list)

    def as_dict(self):
        return {"ROOM_ID": self.room_id, "UID": self.uid, "PERSISTENT_ID": self.persistent_id,
                "FLOOR": self.floor, "SOURCE_REVISION": self.source_revision,
                "LABEL": self.label, "LABEL_STATUS": self.label_status, "LABELS_SEEN": self.labels_seen,
                "COMPONENT_REFS": sorted(self.component_refs), "COMPONENTS": len(self.component_refs),
                "AREA_M2": round(self.area, 6), "STATUS": self.status, "CONFIDENCE": self.confidence,
                "EVIDENCE": [e.as_dict() for e in self.evidence]}


@dataclass
class MeasurementObject:
    """What a trade is measured on.  It references a space or a component; it is never the same object."""
    measurement_object_id: str
    trade: str
    unit: str
    quantity: float
    floor: str
    source_revision: str
    room_id: str = None
    component_ref: str = None
    basis: str = None
    status: str = None
    confidence: str = CONFIDENCE_PROVEN
    evidence: list = field(default_factory=list)

    def as_dict(self):
        return {"MEASUREMENT_OBJECT_ID": self.measurement_object_id, "TRADE": self.trade,
                "ROOM_ID": self.room_id, "COMPONENT_REF": self.component_ref, "FLOOR": self.floor,
                "SOURCE_REVISION": self.source_revision, "MEASURED_QUANTITY": self.quantity,
                "MEASURED_UNIT": self.unit, "MEASUREMENT_BASIS": self.basis, "STATUS": self.status,
                "CONFIDENCE": self.confidence, "EVIDENCE": [e.as_dict() for e in self.evidence],
                "WASTE_PERCENT": None, "PROCUREMENT_QUANTITY": None, "UNIT_RATE": None, "AMOUNT": None}
