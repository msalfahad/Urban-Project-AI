"""Neutral source observations — the ONE shape K1 reads.

A decoder route (LibreDWG JSON today, ezdxf in R8.2) maps its own raw
representation into these records. K1 never sees a decoder's field names,
so an unverified raw field cannot leak into the geometry kernel.

Conventions:
  * coordinates are NATIVE drawing units, exactly as authored; no unit is
    inferred or applied here;
  * ARC/CIRCLE/LWPOLYLINE/INSERT/TEXT/ATTRIB geometry is in the entity's
    OCS; LINE and ELLIPSE positions are WCS-native (ELLIPSE uses its normal
    only to orient the minor axis);
  * angles are radians, counter-clockwise about the entity's normal;
  * `extrusion` is carried RAW: validating it is K1's job (kernel_ocs), so a
    malformed value is a visible finding, never a silently repaired default;
  * `visible` is the source's own invisibility flag. Anonymous (*U) blocks
    of dynamic blocks carry every visibility state; the non-current ones are
    flagged invisible (R8.1 dynamic-block review).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# entity kinds
LINE = "LINE"
ARC = "ARC"
CIRCLE = "CIRCLE"
LWPOLYLINE = "LWPOLYLINE"
ELLIPSE = "ELLIPSE"
INSERT = "INSERT"
TEXT = "TEXT"
MTEXT = "MTEXT"
DIMENSION = "DIMENSION"
HATCH = "HATCH"
POINT = "POINT"
SOLID = "SOLID"
ATTDEF = "ATTDEF"
UNSUPPORTED_KIND = "UNSUPPORTED"

# observed and retained, not realised by K1 as measurement geometry (R8.2 capability register)
CARRIED_KINDS = frozenset({TEXT, MTEXT, DIMENSION, HATCH, POINT, SOLID, ATTDEF})

DEFAULT_EXTRUSION = (0.0, 0.0, 1.0)


@dataclass(frozen=True)
class SourceRevisionAnchor:
    """Which bytes, decoded by which route, this observation is valid for."""

    source_sha256: str | None
    route: str
    decoder: str
    decoder_version: str | None = None
    decoder_binary_sha256: str | None = None   # DECODER_BINARY_PIN; None = not established for THESE bytes
    parser_lineage: str | None = None          # who parsed the DWG bytes (e.g. LIBREDWG), for independence claims
    conversion_chain: tuple = ()               # ordered steps from the original source to this representation
    pin_status: str = "NOT_ESTABLISHED"        # decoder_pins.status(): REGISTERED / UNREGISTERED_BUILD / NOT_ESTABLISHED


@dataclass(frozen=True)
class GridSpec:
    """MINSERT array. Spacing is in the insert's OCS units: rotated with the
    insert, never scaled by it."""

    columns: int
    rows: int
    column_spacing: float
    row_spacing: float


@dataclass(frozen=True)
class LineGeom:
    start: tuple
    end: tuple


@dataclass(frozen=True)
class ArcGeom:
    center: tuple
    radius: float
    start_angle: float
    end_angle: float


@dataclass(frozen=True)
class CircleGeom:
    center: tuple
    radius: float


@dataclass(frozen=True)
class PolylineGeom:
    vertices: tuple
    bulges: tuple
    closed: bool


@dataclass(frozen=True)
class EllipseGeom:
    center: tuple
    major_axis: tuple
    ratio: float
    start_param: float
    end_param: float


@dataclass(frozen=True)
class AttributeGeom:
    handle: str
    tag: str
    value: str
    insertion: tuple
    extrusion: Any = DEFAULT_EXTRUSION


@dataclass(frozen=True)
class InsertGeom:
    block_key: str
    insertion: tuple
    scale: tuple
    rotation: float
    grid: GridSpec | None = None
    attributes: tuple = ()


@dataclass(frozen=True)
class TextGeom:
    insertion: tuple
    value: str


@dataclass(frozen=True)
class CarriedGeom:
    """A carried kind's own anchor points, in its frame, so nothing about it is lost."""

    anchor: tuple | None
    points: tuple = ()
    value: str = ""


@dataclass(frozen=True)
class UnsupportedGeom:
    category: str          # findings.ENTITY_CATEGORIES
    reason: str
    impacts: tuple | None = None       # capability-register impacts for this kind (None: code default)


@dataclass(frozen=True)
class SourceEntityObservation:
    obs_id: str
    source_handle: str
    source_type: str       # the route's own designation, e.g. "LIBREDWG:17:ARC"
    kind: str
    geometry: Any
    layer: str | None = None
    extrusion: Any = DEFAULT_EXTRUSION
    visible: bool = True
    provenance: tuple = ()  # (field, raw path / status) pairs from the route


@dataclass(frozen=True)
class XrefInfo:
    path: str
    attachment: str        # ATTACH / OVERLAY / UNKNOWN
    resolved: bool | None
    unloaded: bool | None
    mapping_status: str    # VERIFIED / SOURCE_MAPPING_UNVERIFIED


@dataclass(frozen=True)
class BlockDefinition:
    key: str
    name: str
    base_point: tuple
    entities: tuple
    xref: XrefInfo | None = None
    name_readable: bool = True
    anonymous: bool = False             # *U / *D style name: the name is not an identity
    parent_ref: tuple | None = None     # route's evidence of a dynamic parent: ("BLOCK_HEADER", key, name) /
                                        # ("NON_BLOCK", kind) / None (no reference); mapping UNVERIFIED


@dataclass(frozen=True)
class UnplacedObservation:
    """An observation whose ownership / placement the source does not establish.

    Kept whole (handle, type, layer, raw geometry) so it stays auditable, and
    NEVER realised in model space: its coordinates may be block-local."""

    observation: SourceEntityObservation
    raw_owner: Any                      # the route's raw owner reference, verbatim
    reason: str                         # OWNER_HANDLE_UNKNOWN / OWNER_AMBIGUOUS / OWNER_EVIDENCE_CONFLICT / OWNER_IS_INSERT / NO_OWNER_EVIDENCE
    evidence: tuple = ()                # what each ownership source said


@dataclass(frozen=True)
class SourceDocument:
    anchor: SourceRevisionAnchor
    entities: tuple                     # model space
    blocks: dict = field(default_factory=dict)
    header: dict = field(default_factory=dict)   # recorded raw, never interpreted here
    findings: tuple = ()                # route-level findings
    notes: dict = field(default_factory=dict)
    unplaced: tuple = ()                # UnplacedObservation: ownership not established (R8.2 Phase 0)
    other_layouts: tuple = ()           # (layout name, observation): paper-space content, retained, not realised
