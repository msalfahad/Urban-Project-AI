"""Normalize authored CAD into the model the rest of this engine already uses.

A CAD drawing is the first source this project has read that KNOWS WHAT IT
CONTAINS. A PDF gave marks and pen weights and left every meaning to be
inferred; a DWG gives an entity with a type, a layer, a block lineage and a
handle. The adapter's job is to carry that across without inventing
anything and without building a second, CAD-only world beside the existing
one.

    CAD COORDINATES ARE THE MEASUREMENT. There is no rendering step here,
    no pixel, and no manufactured pen weight. Millimetres come from the
    authored geometry.

FOUR RULES THIS MODULE IS BUILT AROUND

  1. NO SOURCE CONVENTION IS UNIVERSAL. Nothing here knows that a layer
     called W holds walls or that a block called SAL is a saloon. The
     adapter reports layers and block names as OBSERVATIONS; deciding what
     they mean is `engine.cad_profile`'s job, per source, with evidence.

  2. ORDER IS NEVER IDENTITY. Every normalized object's id is built from
     the DWG handle and its block lineage, never from a position in a list.
     A re-decode that returns the same entities in another order produces
     the same ids.

  3. A CURVE IS NOT A LINE. Arcs, circles and bulged polyline spans stay
     arcs. Flattening them into segments would manufacture straight wall
     candidates that nobody drew — the CAD version of promoting a proxy
     into geometry.

  4. A BLOCK DEFINITION IS NOT AN INSTANCE. A door block drawn once and
     placed eleven times is one definition and ELEVEN doors. Both are kept,
     and instance geometry is produced by composing transforms down the
     nesting, never by reading the definition's own coordinates as if they
     were in the drawing.

WHAT A DIMENSION IS, WHICH IS THREE THINGS

A DWG dimension carries the distance it spans AND the number it prints, and
they are not the same quantity when `DIMLFAC` is not 1. All three are kept
apart, and none is ever averaged with another:

    GEOMETRY_MEASURED_VALUE_MM     from xline1 to xline2, in drawing units
    DIMENSION_DISPLAY_VALUE        the number on the sheet, in its own unit
    DIMENSION_NORMALIZED_VALUE_MM  the display value converted back by
                                   DIMLFAC, for comparison with geometry
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from dataclasses import dataclass, field

ADAPTER = "DETERMINISTIC_CAD_ENTITY_NORMALISATION_V1"

# --- frozen parameters ----------------------------------------------------
# Each is a property of the CAD format or of arithmetic, not of any drawing.
# None may be changed because a real source scores better.

# How deep block nesting may go before the adapter refuses. AutoCAD permits
# arbitrary nesting; a cycle is impossible in a valid file but a corrupt one
# can present one, and an unbounded walk would hang rather than report.
MAX_NESTING_DEPTH = 16

# A segment shorter than this is a degenerate artefact of the authoring
# tool, not a drawn line. One micron: far below any drafting intent and far
# above float noise on coordinates of this magnitude.
MIN_SEGMENT_MM = 0.001

# How close a direction must be to an axis to be called axis-aligned. CAD
# coordinates are exact, so this catches only the float residue of a
# rotation by exactly 90 degrees, where sin/cos return 6.1e-17.
AXIS_EPSILON = 1e-9

# Entity kinds, named after what they ARE rather than after what they might
# mean. Nothing downstream may read a wall from this field alone.
SEGMENT = "SEGMENT"
ARC = "ARC"
CIRCLE = "CIRCLE"
HATCH = "HATCH"

AXIS_H = "H"
AXIS_V = "V"
AXIS_SKEW = "SKEW"

# DWG type codes the adapter understands. Anything else is counted and
# carried as UNHANDLED — visible, never silently dropped.
T_TEXT, T_ATTRIB, T_ATTDEF = 1, 2, 3
T_INSERT = 7
T_ARC, T_CIRCLE, T_LINE = 17, 18, 19
T_POINT = 27
T_MTEXT = 44
T_LWPOLYLINE, T_HATCH = 77, 78
T_DIMENSIONS = (20, 21, 22, 23, 24, 25, 26, 763)

# Block-definition delimiters. They mark where a definition starts and ends
# and are not drawing content. LibreDWG emits tens of thousands of spurious
# ones on some files (see invariant 45), so they are named and counted here
# rather than landing in `unhandled`, where a real surprise belongs.
T_BLOCK_DELIMITERS = (4, 5)

# A DWG type at or above 500 is an instance of a class from the CLASSES
# table rather than a fixed type. It is counted by type code — knowing that
# something custom is present is the point, and decoding it is not
# something to guess at.
CUSTOM_CLASS_FLOOR = 500

# Which layout a top-level entity belongs to. The drawing lives in one of
# them and paper space holds the sheet furniture in its OWN coordinate
# system, near the origin — so mixing the two inflates the extent by
# hundreds of metres and would put a title block inside a room.
MODEL_SPACE = "*MODEL_SPACE"


class CadAdapterError(RuntimeError):
    """The adapter was asked for something it must not guess at."""


# ---------------------------------------------------------------- transform

@dataclass(frozen=True)
class Transform2D:
    """A 2D affine map, as CAD composes them: scale, then rotate, then move.

    Kept explicit rather than as a matrix library call because the order is
    the whole content: AutoCAD applies an INSERT's scale in the block's own
    axes, THEN its rotation, THEN its insertion point, and composing those
    in any other order puts a rotated, scaled block in the wrong place.
    """

    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    e: float = 0.0
    f: float = 0.0

    @classmethod
    def identity(cls) -> "Transform2D":
        return cls()

    @classmethod
    def from_insert(cls, ins_pt, scale, rotation: float) -> "Transform2D":
        sx = float(scale[0]) if scale else 1.0
        sy = float(scale[1]) if scale and len(scale) > 1 else sx
        cos, sin = math.cos(rotation), math.sin(rotation)
        return cls(a=sx * cos, b=sx * sin, c=-sy * sin, d=sy * cos,
                   e=float(ins_pt[0]), f=float(ins_pt[1]))

    def then(self, outer: "Transform2D") -> "Transform2D":
        """This transform followed by `outer` — the nesting composition."""
        return Transform2D(
            a=outer.a * self.a + outer.c * self.b,
            b=outer.b * self.a + outer.d * self.b,
            c=outer.a * self.c + outer.c * self.d,
            d=outer.b * self.c + outer.d * self.d,
            e=outer.a * self.e + outer.c * self.f + outer.e,
            f=outer.b * self.e + outer.d * self.f + outer.f)

    def apply(self, x: float, y: float) -> tuple:
        return (self.a * x + self.c * y + self.e,
                self.b * x + self.d * y + self.f)

    @property
    def scale_x(self) -> float:
        return math.hypot(self.a, self.b)

    @property
    def scale_y(self) -> float:
        return math.hypot(self.c, self.d)

    @property
    def is_uniform(self) -> bool:
        return abs(self.scale_x - self.scale_y) < 1e-9

    @property
    def rotation(self) -> float:
        return math.atan2(self.b, self.a)

    @property
    def is_mirrored(self) -> bool:
        return (self.a * self.d - self.b * self.c) < 0


# --------------------------------------------------------------- provenance

@dataclass(frozen=True)
class Provenance:
    """Where a normalized object came from, all the way back to the file."""

    handle: int
    entity_type: str
    layer: str
    source_hash: str = ""
    block_path: tuple = ()          # outermost block name first
    instance_path: tuple = ()       # the INSERT handles that placed it
    sub_id: str = ""                # which part of a multi-part entity

    @property
    def object_id(self) -> str:
        """Identity from handle and lineage — never from list position.

        One DWG entity can produce several primitives: a polyline is one
        handle and four sides. Those sides need distinct ids or a wall face
        on one is indistinguishable from a wall face on another — and the
        self-test caught exactly that before any real drawing was measured.

        `sub_id` is derived from the span's OWN LOCAL COORDINATES, not from
        its position in the vertex list. A decoder that returned the
        vertices in another order would still produce the same ids, which
        is what ORDER IS NEVER IDENTITY requires of a part as much as of a
        whole.
        """
        lineage = "/".join(str(h) for h in self.instance_path)
        out = f"CAD-{self.handle}"
        if self.sub_id:
            out += f".{self.sub_id}"
        return out + (f"@{lineage}" if lineage else "")

    def record(self) -> dict:
        return {"dwg_handle": self.handle, "entity_type": self.entity_type,
                "layer": self.layer, "source_sha256_16": self.source_hash,
                "block_path": list(self.block_path),
                "instance_path": list(self.instance_path),
                "part": self.sub_id, "object_id": self.object_id}


def _part_id(x1: float, y1: float, x2: float, y2: float) -> str:
    """A stable name for one span of a multi-part entity, from its own ends.

    Intrinsic to the geometry, so it survives a reordering of the vertex
    list; short, so an id stays readable in a report.
    """
    key = f"{x1:.4f},{y1:.4f}->{x2:.4f},{y2:.4f}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]


# ---------------------------------------------------------------- primitives

@dataclass(frozen=True)
class Primitive:
    """One piece of authored geometry, in drawing units, with its lineage."""

    kind: str
    provenance: Provenance
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    cx: float = 0.0
    cy: float = 0.0
    radius: float = 0.0
    start_angle: float = 0.0
    end_angle: float = 0.0

    @property
    def object_id(self) -> str:
        return self.provenance.object_id

    @property
    def length_mm(self) -> float:
        if self.kind == SEGMENT:
            return math.hypot(self.x2 - self.x1, self.y2 - self.y1)
        if self.kind == ARC:
            sweep = (self.end_angle - self.start_angle) % (2 * math.pi)
            return abs(self.radius * sweep)
        if self.kind == CIRCLE:
            return 2 * math.pi * self.radius
        return 0.0

    @property
    def axis(self) -> str:
        if self.kind != SEGMENT:
            return AXIS_SKEW
        dx, dy = abs(self.x2 - self.x1), abs(self.y2 - self.y1)
        if dy <= AXIS_EPSILON * max(1.0, dx):
            return AXIS_H
        if dx <= AXIS_EPSILON * max(1.0, dy):
            return AXIS_V
        return AXIS_SKEW

    def record(self) -> dict:
        out = {"kind": self.kind, "axis": self.axis,
               "length_mm": round(self.length_mm, 3),
               "provenance": self.provenance.record()}
        if self.kind == SEGMENT:
            out["start_mm"] = [round(self.x1, 4), round(self.y1, 4)]
            out["end_mm"] = [round(self.x2, 4), round(self.y2, 4)]
        else:
            out["centre_mm"] = [round(self.cx, 4), round(self.cy, 4)]
            out["radius_mm"] = round(self.radius, 4)
        return out


@dataclass(frozen=True)
class TextObservation:
    """Text the author typed. An observation, never an identity."""

    value: str
    x: float
    y: float
    height: float
    provenance: Provenance

    def record(self) -> dict:
        return {"text": self.value, "at_mm": [round(self.x, 2),
                                              round(self.y, 2)],
                "text_height_mm": round(self.height, 2),
                "provenance": self.provenance.record(),
                "this_is": ("what the author typed. It is evidence of "
                            "identity and is not identity")}


@dataclass(frozen=True)
class DimensionObservation:
    """An authored dimension: what it spans, and what it prints.

    Three values, deliberately not reconciled here. `geometry_mm` is the
    distance between the extension-line origins in DRAWING units;
    `display_value` is the number on the sheet in whatever unit the
    dimension style prints; `normalized_mm` is that number converted back
    through DIMLFAC so it can be compared with geometry.
    """

    geometry_mm: float
    display_value: float | None
    dimlfac: float
    user_text: str
    x1: float
    y1: float
    x2: float
    y2: float
    provenance: Provenance

    @property
    def normalized_mm(self):
        if self.display_value is None or not self.dimlfac:
            return None
        return self.display_value / self.dimlfac

    @property
    def is_overridden(self) -> bool:
        """The author replaced the measurement with typed text."""
        return bool(self.user_text.strip())

    def record(self) -> dict:
        return {
            "GEOMETRY_MEASURED_VALUE_MM": round(self.geometry_mm, 3),
            "DIMENSION_DISPLAY_VALUE": self.display_value,
            "DIMENSION_NORMALIZED_VALUE_MM": (
                None if self.normalized_mm is None
                else round(self.normalized_mm, 3)),
            "dimlfac_applied": self.dimlfac,
            "text_overridden_by_author": self.is_overridden,
            "user_text": self.user_text,
            "extension_origins_mm": [[round(self.x1, 3), round(self.y1, 3)],
                                     [round(self.x2, 3), round(self.y2, 3)]],
            "provenance": self.provenance.record(),
            "never": ("these three values are never averaged. They are "
                      "different quantities that happen to be close"),
        }


@dataclass(frozen=True)
class BlockInstance:
    """One placement of one block definition, with its resolved transform."""

    block_name: str
    provenance: Provenance
    transform: Transform2D
    depth: int = 0

    @property
    def insertion_mm(self) -> tuple:
        return (self.transform.e, self.transform.f)

    def record(self) -> dict:
        return {"block_definition": self.block_name,
                "insertion_mm": [round(self.transform.e, 2),
                                 round(self.transform.f, 2)],
                "scale": [round(self.transform.scale_x, 6),
                          round(self.transform.scale_y, 6)],
                "rotation_deg": round(math.degrees(self.transform.rotation), 6),
                "mirrored": self.transform.is_mirrored,
                "nesting_depth": self.depth,
                "provenance": self.provenance.record()}


# -------------------------------------------------------------- the drawing

@dataclass
class NormalizedDrawing:
    """The source-independent result. Nothing here is named a wall."""

    source_file: str = ""
    source_hash: str = ""
    drawing_unit: str = ""
    insunits_code: int | None = None
    dimlfac: float = 1.0
    space: str = ""
    primitives: list = field(default_factory=list)
    texts: list = field(default_factory=list)
    dimensions: list = field(default_factory=list)
    instances: list = field(default_factory=list)
    block_definitions: dict = field(default_factory=dict)
    layers: list = field(default_factory=list)
    unhandled: dict = field(default_factory=dict)
    notes: dict = field(default_factory=dict)

    def segments(self) -> list:
        return [p for p in self.primitives if p.kind == SEGMENT]

    def extent(self) -> tuple:
        xs, ys = [], []
        for p in self.primitives:
            if p.kind == SEGMENT:
                xs += [p.x1, p.x2]
                ys += [p.y1, p.y2]
            else:
                xs += [p.cx - p.radius, p.cx + p.radius]
                ys += [p.cy - p.radius, p.cy + p.radius]
        if not xs:
            return (0.0, 0.0, 0.0, 0.0)
        return (min(xs), min(ys), max(xs), max(ys))

    def normalization_hash(self) -> str:
        """A hash of the normalized geometry, order-independent.

        Sorted before hashing so a decoder that returns entities in a
        different order produces the SAME hash — ORDER IS NEVER IDENTITY
        applies to the freeze as much as to the ids.
        """
        rows = sorted(
            f"{p.kind}|{p.object_id}|{p.x1:.4f},{p.y1:.4f},"
            f"{p.x2:.4f},{p.y2:.4f},{p.cx:.4f},{p.cy:.4f},{p.radius:.4f}"
            for p in self.primitives)
        rows += sorted(f"T|{t.provenance.object_id}|{t.value}"
                       for t in self.texts)
        rows += sorted(f"D|{d.provenance.object_id}|{d.geometry_mm:.4f}|"
                       f"{d.display_value}" for d in self.dimensions)
        h = hashlib.sha256("\n".join(rows).encode("utf-8"))
        return h.hexdigest()[:24]

    def record(self) -> dict:
        return {
            "adapter": ADAPTER,
            "adapter_hash": adapter_hash(),
            "normalization_hash": self.normalization_hash(),
            "source_file": self.source_file,
            "source_sha256_16": self.source_hash,
            "layout_normalized": self.space,
            "drawing_unit": self.drawing_unit,
            "insunits_code": self.insunits_code,
            "dimlfac": self.dimlfac,
            "primitives": len(self.primitives),
            "primitives_by_kind": dict(
                Counter(p.kind for p in self.primitives).most_common()),
            "segments_by_axis": dict(
                Counter(p.axis for p in self.segments()).most_common()),
            "texts": len(self.texts),
            "dimensions": len(self.dimensions),
            "block_instances": len(self.instances),
            "block_definitions": len(self.block_definitions),
            "max_nesting_depth_seen": max(
                [i.depth for i in self.instances], default=0),
            "layers": sorted(self.layers),
            "unhandled_entity_types": dict(self.unhandled),
            "extent_mm": [round(v, 2) for v in self.extent()],
            "notes": dict(self.notes),
            "what_this_is_not": (
                "nothing here is a wall, an opening, a room or a quantity. "
                "These are authored primitives with their lineage. Meaning "
                "is assigned per source by the profile, on evidence"),
        }


def frozen_parameters() -> dict:
    return {
        "ADAPTER": ADAPTER,
        "MAX_NESTING_DEPTH": MAX_NESTING_DEPTH,
        "MIN_SEGMENT_MM": MIN_SEGMENT_MM,
        "AXIS_EPSILON": AXIS_EPSILON,
        "why_each": {
            "MAX_NESTING_DEPTH": (
                "a valid file cannot contain a block cycle, a corrupt one "
                "can, and an unbounded walk would hang instead of report"),
            "MIN_SEGMENT_MM": (
                "one micron — below any drafting intent, above float noise "
                "on coordinates of this magnitude"),
            "AXIS_EPSILON": (
                "CAD coordinates are exact, so this catches only the float "
                "residue of an exact 90-degree rotation (sin = 6.1e-17)"),
        },
    }


def adapter_hash() -> str:
    """Freeze hash over the adapter's name and every frozen parameter."""
    parts = [ADAPTER, f"depth={MAX_NESTING_DEPTH}",
             f"min_seg={MIN_SEGMENT_MM}", f"axis_eps={AXIS_EPSILON}"]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------------- normalisation

def _abs_handle(h):
    return h[-1] if isinstance(h, list) and h else None


def _pt(v, idx=0):
    return float(v[idx]) if isinstance(v, (list, tuple)) and len(v) > idx else 0.0


def normalize(decoded: dict, *, source_file: str = "", source_hash: str = "",
              space: str = MODEL_SPACE,
              max_depth: int = MAX_NESTING_DEPTH) -> NormalizedDrawing:
    """Turn a decoded CAD file into source-independent primitives.

    `decoded` is LibreDWG's JSON shape. Nothing about layer or block NAMES
    influences anything here.
    """
    objs = decoded.get("OBJECTS") or []
    if not objs:
        raise CadAdapterError(
            "the decode carries no objects, so there is nothing to "
            "normalize. That is not a finding that the drawing is empty")

    hdr = decoded.get("HEADER") or {}
    insunits = hdr.get("INSUNITS")
    dimlfac = float(hdr.get("DIMLFAC", 1.0) or 1.0)

    layer_name, block_header, by_handle = {}, {}, {}
    for o in objs:
        kind = o.get("object")
        h = _abs_handle(o.get("handle"))
        if h is not None:
            by_handle[h] = o
        if kind == "LAYER":
            layer_name[h] = o.get("name", "")
        elif kind == "BLOCK_HEADER":
            block_header[h] = o

    # WHICH BLOCK OWNS WHICH ENTITY.
    #
    # A BLOCK_HEADER carries an `entities` list, and on this decoder that
    # list is WRONG: for block SAL it names the block's own BEGIN and END
    # delimiters instead of the two text entities inside it. Trusting it
    # emitted three text observations from a drawing carrying thirty-nine,
    # and every room-name stamp vanished.
    #
    # The ownership runs the other way and is reliable: each entity names
    # its owner. Inverting that gives 152 entities across 31 definitions,
    # and SAL comes back holding exactly its two labels.
    owned_by: dict = {}
    for o in objs:
        if "entity" not in o or o.get("type") in T_BLOCK_DELIMITERS:
            continue
        oh = _abs_handle(o.get("ownerhandle"))
        if oh in block_header:
            owned_by.setdefault(oh, []).append(o)

    out = NormalizedDrawing(
        source_file=source_file, source_hash=source_hash,
        insunits_code=insunits,
        drawing_unit=("millimetre" if insunits == 4 else
                      "NOT_ESTABLISHED" if insunits in (None, 0)
                      else f"insunits_code_{insunits}"),
        dimlfac=dimlfac,
        layers=[v for v in layer_name.values() if v],
        block_definitions={
            _abs_handle(b.get("handle")): b.get("name", "")
            for b in block_header.values()
            if not str(b.get("name", "")).startswith("*")},
    )
    unhandled: Counter = Counter()
    dropped: Counter = Counter()
    custom: Counter = Counter()

    # A definition's own entities live at its local origin and must never be
    # emitted as if they stood in the drawing — that is a phantom door at
    # 0,0. They reach the sheet only through an INSERT.
    in_definition = set()
    for h, rows in owned_by.items():
        if str(block_header[h].get("name", "")).startswith("*"):
            continue
        for o in rows:
            in_definition.add(_abs_handle(o.get("handle")))

    def layer_of(o):
        return layer_name.get(_abs_handle(o.get("layer")),
                              "UNRESOLVED_LAYER_REFERENCE")

    def emit(o, xf: Transform2D, block_path: tuple, inst_path: tuple,
             depth: int):
        t = o.get("type")
        prov = Provenance(
            handle=_abs_handle(o.get("handle")) or -1,
            entity_type=str(t), layer=layer_of(o), source_hash=source_hash,
            block_path=block_path, instance_path=inst_path)

        if t == T_LINE:
            x1, y1 = xf.apply(_pt(o.get("start"), 0), _pt(o.get("start"), 1))
            x2, y2 = xf.apply(_pt(o.get("end"), 0), _pt(o.get("end"), 1))
            if math.hypot(x2 - x1, y2 - y1) >= MIN_SEGMENT_MM:
                out.primitives.append(Primitive(
                    SEGMENT, prov, x1=x1, y1=y1, x2=x2, y2=y2))
            return

        if t == T_LWPOLYLINE:
            pts = o.get("points") or []
            bulges = o.get("bulges") or []
            closed = bool(int(o.get("flag", 0)) & 0x200)
            n = len(pts)
            span = range(n) if closed and n > 2 else range(n - 1)
            for i in span:
                p, q = pts[i], pts[(i + 1) % n]
                x1, y1 = xf.apply(_pt(p, 0), _pt(p, 1))
                x2, y2 = xf.apply(_pt(q, 0), _pt(q, 1))
                # From the LOCAL vertices, so the id is the same however the
                # instance is placed and however the vertices are ordered.
                part = _part_id(_pt(p, 0), _pt(p, 1), _pt(q, 0), _pt(q, 1))
                prov_i = Provenance(
                    handle=prov.handle, entity_type=prov.entity_type,
                    layer=prov.layer, source_hash=prov.source_hash,
                    block_path=prov.block_path,
                    instance_path=prov.instance_path, sub_id=part)
                bulge = float(bulges[i]) if i < len(bulges) else 0.0
                if abs(bulge) > 1e-12:
                    # A bulged span is an ARC. Emitting it as a chord would
                    # invent a straight line the author did not draw.
                    chord = math.hypot(x2 - x1, y2 - y1)
                    if chord < MIN_SEGMENT_MM:
                        continue
                    theta = 4 * math.atan(abs(bulge))
                    radius = chord / (2 * math.sin(theta / 2))
                    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                    out.primitives.append(Primitive(
                        ARC, prov_i, cx=mx, cy=my, radius=radius,
                        start_angle=0.0, end_angle=theta,
                        x1=x1, y1=y1, x2=x2, y2=y2))
                elif math.hypot(x2 - x1, y2 - y1) >= MIN_SEGMENT_MM:
                    out.primitives.append(Primitive(
                        SEGMENT, prov_i, x1=x1, y1=y1, x2=x2, y2=y2))
            return

        if t == T_ARC:
            cx, cy = xf.apply(_pt(o.get("center"), 0), _pt(o.get("center"), 1))
            out.primitives.append(Primitive(
                ARC, prov, cx=cx, cy=cy,
                radius=float(o.get("radius", 0.0)) * xf.scale_x,
                start_angle=float(o.get("start_angle", 0.0)) + xf.rotation,
                end_angle=float(o.get("end_angle", 0.0)) + xf.rotation))
            return

        if t == T_CIRCLE:
            cx, cy = xf.apply(_pt(o.get("center"), 0), _pt(o.get("center"), 1))
            out.primitives.append(Primitive(
                CIRCLE, prov, cx=cx, cy=cy,
                radius=float(o.get("radius", 0.0)) * xf.scale_x))
            return

        if t in (T_TEXT, T_ATTRIB, T_ATTDEF, T_MTEXT):
            value = o.get("text_value") or o.get("text") or ""
            x, y = xf.apply(_pt(o.get("ins_pt"), 0), _pt(o.get("ins_pt"), 1))
            height = float(o.get("height") or o.get("text_height") or 0.0)
            if value.strip():
                out.texts.append(TextObservation(
                    value=value.strip(), x=x, y=y,
                    height=height * xf.scale_y, provenance=prov))
            return

        if t in T_DIMENSIONS:
            a = o.get("xline1_pt") or o.get("def_pt") or [0, 0, 0]
            b = o.get("xline2_pt") or o.get("def_pt") or [0, 0, 0]
            x1, y1 = xf.apply(_pt(a, 0), _pt(a, 1))
            x2, y2 = xf.apply(_pt(b, 0), _pt(b, 1))
            geom = math.hypot(x2 - x1, y2 - y1)
            act = o.get("act_measurement")
            out.dimensions.append(DimensionObservation(
                geometry_mm=geom,
                display_value=(None if act is None else float(act)),
                dimlfac=dimlfac, user_text=str(o.get("user_text") or ""),
                x1=x1, y1=y1, x2=x2, y2=y2, provenance=prov))
            return

        if t == T_INSERT:
            bh = block_header.get(_abs_handle(o.get("block_header")))
            name = bh.get("name", "") if bh else ""
            local = Transform2D.from_insert(
                o.get("ins_pt") or [0, 0, 0], o.get("scale") or [1, 1, 1],
                float(o.get("rotation", 0.0) or 0.0))
            placed = local.then(xf)
            out.instances.append(BlockInstance(
                block_name=name, provenance=prov, transform=placed,
                depth=depth))
            if depth >= max_depth:
                out.notes.setdefault("nesting_depth_reached", []).append(
                    prov.object_id)
                return
            bh_handle = _abs_handle(o.get("block_header"))
            for child in owned_by.get(bh_handle, ()):
                emit(child, placed, block_path + (name,),
                     inst_path + (prov.handle,), depth + 1)
            return

        if t == T_HATCH:
            out.primitives.append(Primitive(HATCH, prov))
            return
        if t == T_POINT:
            dropped["POINT"] += 1    # a marker, never a boundary
            return
        if t in T_BLOCK_DELIMITERS:
            dropped["BLOCK_DELIMITER"] += 1
            return
        if isinstance(t, int) and t >= CUSTOM_CLASS_FLOOR:
            custom[str(t)] += 1
            return
        unhandled[str(t)] += 1

    other_space = Counter()
    for o in objs:
        if "entity" not in o:
            continue
        h = _abs_handle(o.get("handle"))
        if h in in_definition:
            continue          # reached through its INSERT, not on its own
        oh = _abs_handle(o.get("ownerhandle"))
        where = (str(block_header[oh].get("name", ""))
                 if oh in block_header else None)
        if where is not None and where.startswith("*") and where != space:
            other_space[where] += 1
            continue
        emit(o, Transform2D.identity(), (), (), 0)

    out.unhandled = dict(unhandled)
    out.space = space
    out.notes["block_definition_entities_skipped_at_top_level"] = len(
        in_definition)
    out.notes["entities_dropped_by_kind"] = dict(dropped)
    out.notes["custom_class_entities_by_type_code"] = dict(custom)
    out.notes["entities_in_other_layouts"] = dict(other_space)
    if other_space:
        out.notes["why_other_layouts_excluded"] = (
            "paper space holds the sheet frame and title block in its OWN "
            "coordinate system, near the origin. Normalizing it together "
            "with model space inflates the extent by hundreds of metres and "
            "puts a title block inside a room")
    out.notes["geometry_authority"] = (
        "CAD coordinates. Nothing here was rasterised and no pen weight was "
        "read or manufactured")
    return out
