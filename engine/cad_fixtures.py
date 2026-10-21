"""Synthetic CAD drawings with known answers, for freezing the adapter.

The enclosure algorithm was frozen on synthetic fixtures before AR-00 was
measured, for a reason that applies twice over here: an adapter validated
against the drawing it will be judged on has been tuned, not tested. So
every case below is built by hand, its answer is arithmetic, and none of it
came from looking at P7757.

Each fixture is a LibreDWG-JSON-shaped decode — the same shape the real
decoder emits — so the adapter under test is the production path and not a
stand-in for it.

WHAT THE HARD CASES ARE

  * A ROTATED, SCALED, NESTED BLOCK. Composition order is the whole
    content: AutoCAD scales in the block's axes, then rotates, then
    translates, and any other order puts the geometry somewhere plausible
    but wrong. The fixtures state the expected coordinates to four
    decimals so a transposed composition cannot pass.

  * A BULGED POLYLINE SPAN. It is an ARC. A chord would be a straight line
    nobody drew, and a straight line is exactly what a wall detector would
    happily consume.

  * A BLOCK DEFINITION'S OWN ENTITIES. They live at the definition's local
    origin. Emitting them as drawing geometry puts a phantom door at 0,0 —
    and on a real sheet 0,0 is usually inside a room.

  * DIMLFAC. The dimension spans 3000 mm and prints "300". Both are true.
    A fixture asserts all three values separately and that none equals
    another.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# Handle numbering. These are ARBITRARY ids inside a fixture and carry no
# meaning; the adapter must derive identity from them rather than from the
# order entities happen to appear in, so the fixtures deliberately place
# entities out of handle order.
H_LAYER = 10
H_BLOCK = 100
H_ENTITY = 1000


@dataclass
class Builder:
    """Assembles a LibreDWG-shaped decode. No geometry decisions here."""

    insunits: int = 4
    dimlfac: float = 1.0
    objects: list = field(default_factory=list)
    _layers: dict = field(default_factory=dict)
    _blocks: dict = field(default_factory=dict)
    _next: int = H_ENTITY

    def layer(self, name: str) -> list:
        if name not in self._layers:
            h = H_LAYER + len(self._layers)
            self._layers[name] = h
            self.objects.append(
                {"object": "LAYER", "handle": [0, 1, h], "name": name})
        return [5, 1, self._layers[name], self._layers[name]]

    def _handle(self) -> int:
        self._next += 1
        return self._next

    def block(self, name: str, entities: list) -> int:
        """Define a block from already-created entity handles.

        This reproduces the REAL decoder's shape, defect and all. On
        project 7757 a BLOCK_HEADER's `entities` list names the block's own
        BEGIN and END delimiters rather than its contents, while each
        entity's `ownerhandle` points back at the header correctly. So the
        fixture writes the misleading list AND the correct ownership — an
        adapter that trusts the list fails here rather than on the client's
        drawing.
        """
        h = H_BLOCK + len(self._blocks)
        self._blocks[name] = h
        for e in entities:
            for row in self.objects:
                if row.get("handle") == [0, 1, e]:
                    row["ownerhandle"] = [12, 1, h, h]
        begin = self._add({"type": 4, "layer": self.layer("0"),
                           "ownerhandle": [12, 1, h, h], "name": name})
        end = self._add({"type": 5, "layer": self.layer("0"),
                         "ownerhandle": [12, 1, h, h]})
        self.objects.append({
            "object": "BLOCK_HEADER", "handle": [0, 1, h], "name": name,
            "entities": [[3, 1, begin, begin], [3, 1, end, end]]})
        return h

    def _add(self, row: dict) -> int:
        h = self._handle()
        row["handle"] = [0, 1, h]
        row.setdefault("entity", "")
        self.objects.append(row)
        return h

    def line(self, x1, y1, x2, y2, layer="0") -> int:
        return self._add({"type": 19, "layer": self.layer(layer),
                          "start": [x1, y1, 0.0], "end": [x2, y2, 0.0]})

    def lwpolyline(self, points, layer="0", *, closed=False, bulges=None
                   ) -> int:
        return self._add({"type": 77, "layer": self.layer(layer),
                          "points": [list(p) for p in points],
                          "bulges": list(bulges or []),
                          "flag": 0x200 if closed else 0})

    def arc(self, cx, cy, r, a0, a1, layer="0") -> int:
        return self._add({"type": 17, "layer": self.layer(layer),
                          "center": [cx, cy, 0.0], "radius": r,
                          "start_angle": a0, "end_angle": a1})

    def circle(self, cx, cy, r, layer="0") -> int:
        return self._add({"type": 18, "layer": self.layer(layer),
                          "center": [cx, cy, 0.0], "radius": r})

    def hatch(self, layer="0") -> int:
        return self._add({"type": 78, "layer": self.layer(layer)})

    def text(self, value, x, y, height=300.0, layer="0") -> int:
        return self._add({"type": 1, "layer": self.layer(layer),
                          "ins_pt": [x, y, 0.0], "height": height,
                          "text_value": value})

    def mtext(self, value, x, y, height=220.0, layer="0") -> int:
        return self._add({"type": 44, "layer": self.layer(layer),
                          "ins_pt": [x, y, 0.0], "text_height": height,
                          "text": value})

    def dimension(self, x1, y1, x2, y2, *, display=None, user_text="",
                  layer="0") -> int:
        span = math.hypot(x2 - x1, y2 - y1)
        act = span * self.dimlfac if display is None else display
        return self._add({"type": 21, "layer": self.layer(layer),
                          "xline1_pt": [x1, y1, 0.0],
                          "xline2_pt": [x2, y2, 0.0],
                          "act_measurement": act, "user_text": user_text})

    def point(self, x, y, layer="0") -> int:
        return self._add({"type": 27, "layer": self.layer(layer),
                          "x": x, "y": y, "z": 0.0})

    def insert(self, block_name, x, y, *, scale=(1.0, 1.0), rotation=0.0,
               layer="0") -> int:
        bh = self._blocks[block_name]
        return self._add({"type": 7, "layer": self.layer(layer),
                          "ins_pt": [x, y, 0.0],
                          "scale": [scale[0], scale[1], 1.0],
                          "rotation": rotation,
                          "block_header": [5, 1, bh, bh]})

    def build(self) -> dict:
        hdr = {"INSUNITS": self.insunits, "LUNITS": 2, "TILEMODE": 1}
        if self.dimlfac != 1.0:
            hdr["DIMLFAC"] = self.dimlfac
        # Model space, so the adapter's definition-skipping has a real
        # owner to distinguish from a block.
        # The real file's model-space header lists no entities either, so
        # top-level membership is "owner does not resolve to a block".
        objs = [{"object": "BLOCK_HEADER", "handle": [0, 1, 2],
                 "name": "*MODEL_SPACE", "entities": []}] + self.objects
        return {"FILEHEADER": {"version": "AC1018"}, "HEADER": hdr,
                "OBJECTS": objs}


@dataclass(frozen=True)
class Fixture:
    """One synthetic drawing and what the adapter must return for it."""

    name: str
    what_it_tests: str
    decode: dict
    expect: dict


def _wall_pair(b, x0, y0, x1, y1, thickness, layer="WALLS"):
    """Two parallel lines — a wall drawn as its two faces."""
    if abs(y1 - y0) < abs(x1 - x0):          # horizontal run
        b.line(x0, y0, x1, y0, layer)
        b.line(x0, y0 + thickness, x1, y0 + thickness, layer)
    else:
        b.line(x0, y0, x0, y1, layer)
        b.line(x0 + thickness, y0, x0 + thickness, y1, layer)


# --------------------------------------------------------------- the cases

def _f_line():
    b = Builder()
    b.line(0, 0, 3000, 0, "A")
    return Fixture(
        "LINE", "a single drawn line survives with its length and axis",
        b.build(), {"primitives": 1, "segments": 1, "length_mm": 3000.0,
                    "axis": "H", "layers": ["A"]})


def _f_lwpolyline_open():
    b = Builder()
    b.lwpolyline([(0, 0), (1000, 0), (1000, 2000)], "A")
    return Fixture(
        "LWPOLYLINE_OPEN",
        "an open polyline becomes its spans, not one object and not a ring",
        b.build(), {"primitives": 2, "segments": 2, "total_length_mm": 3000.0})


def _f_lwpolyline_closed():
    b = Builder()
    b.lwpolyline([(0, 0), (1000, 0), (1000, 1000), (0, 1000)], "A",
                 closed=True)
    return Fixture(
        "LWPOLYLINE_CLOSED",
        "a closed polyline emits the closing span too — four sides, not three",
        b.build(), {"primitives": 4, "segments": 4, "total_length_mm": 4000.0})


def _f_lwpolyline_bulge():
    b = Builder()
    b.lwpolyline([(0, 0), (1000, 0)], "A", bulges=[1.0, 0.0])
    return Fixture(
        "LWPOLYLINE_BULGE_IS_AN_ARC",
        "a bulged span is an ARC. A chord would invent a straight wall line",
        b.build(), {"primitives": 1, "segments": 0, "arcs": 1})


def _f_arc():
    b = Builder()
    b.arc(500, 500, 900, 0.0, math.pi / 2, "D")
    return Fixture(
        "ARC", "an arc stays an arc and is never a segment",
        b.build(), {"primitives": 1, "segments": 0, "arcs": 1,
                    "length_mm": round(900 * math.pi / 2, 6)})


def _f_circle():
    b = Builder()
    b.circle(0, 0, 250, "COL")
    return Fixture(
        "CIRCLE", "a circle stays a circle",
        b.build(), {"primitives": 1, "segments": 0, "circles": 1,
                    "length_mm": round(2 * math.pi * 250, 6)})


def _f_hatch():
    b = Builder()
    b.hatch("COL")
    b.line(0, 0, 100, 0, "COL")
    return Fixture(
        "HATCH", "a hatch is carried as a hatch, never as boundary segments",
        b.build(), {"primitives": 2, "segments": 1, "hatches": 1})


def _f_text():
    b = Builder()
    b.text("SALOON", 1500, 1500, 300.0, "TEXT")
    return Fixture(
        "TEXT", "typed text becomes an observation with its position",
        b.build(), {"texts": 1, "text_value": "SALOON",
                    "text_at": (1500.0, 1500.0), "primitives": 0})


def _f_mtext():
    b = Builder()
    b.mtext("MASTER BEDROOM", 2000, 800, 220.0, "TEXT")
    return Fixture(
        "MTEXT", "mtext is read from its own field, not the TEXT field",
        b.build(), {"texts": 1, "text_value": "MASTER BEDROOM"})


def _f_dimension_plain():
    b = Builder(dimlfac=1.0)
    b.dimension(0, 0, 0, 3000, layer="DIM")
    return Fixture(
        "DIMENSION_LINEAR",
        "with DIMLFAC 1 the three values agree, and are still three values",
        b.build(), {"dimensions": 1, "geometry_mm": 3000.0,
                    "display_value": 3000.0, "normalized_mm": 3000.0})


def _f_dimension_dimlfac():
    b = Builder(dimlfac=0.1)
    b.dimension(0, 0, 0, 3000, layer="DIM")
    return Fixture(
        "DIMENSION_WITH_DIMLFAC",
        "the dimension spans 3000 mm and PRINTS 300. Both are true, and the "
        "printed number is not a millimetre value",
        b.build(), {"dimensions": 1, "geometry_mm": 3000.0,
                    "display_value": 300.0, "normalized_mm": 3000.0,
                    "display_is_not_geometry": True})


def _f_dimension_overridden():
    b = Builder(dimlfac=0.1)
    b.dimension(0, 0, 0, 3000, display=300.0, user_text="VARIES",
                layer="DIM")
    return Fixture(
        "DIMENSION_TEXT_OVERRIDDEN",
        "the author typed over the measurement, so the printed text is not a "
        "reading of the geometry and must be flagged",
        b.build(), {"dimensions": 1, "overridden": True})


def _f_units_unitless():
    b = Builder(insunits=0)
    b.line(0, 0, 1000, 0, "A")
    return Fixture(
        "UNITS_UNITLESS",
        "INSUNITS 0 declares NO unit. It is not a declaration of millimetres",
        b.build(), {"drawing_unit": "NOT_ESTABLISHED", "insunits_code": 0})


def _f_units_mm():
    b = Builder(insunits=4)
    b.line(0, 0, 1000, 0, "A")
    return Fixture(
        "UNITS_MILLIMETRE", "INSUNITS 4 is millimetres",
        b.build(), {"drawing_unit": "millimetre", "insunits_code": 4})


def _f_insert_plain():
    b = Builder()
    e = b.line(0, 0, 1000, 0, "SYM")
    b.block("MARK", [e])
    b.insert("MARK", 0, 0)
    return Fixture(
        "INSERT",
        "an instance produces geometry; the definition's own copy does not "
        "appear twice",
        b.build(), {"segments": 1, "instances": 1,
                    "segment_endpoints": ((0.0, 0.0), (1000.0, 0.0))})


def _f_insert_translated():
    b = Builder()
    e = b.line(0, 0, 1000, 0, "SYM")
    b.block("MARK", [e])
    b.insert("MARK", 5000, 7000)
    return Fixture(
        "INSERT_TRANSLATED", "the instance geometry moves to the insert point",
        b.build(), {"segments": 1, "instances": 1,
                    "segment_endpoints": ((5000.0, 7000.0),
                                          (6000.0, 7000.0))})


def _f_insert_rotated():
    b = Builder()
    e = b.line(0, 0, 1000, 0, "SYM")
    b.block("MARK", [e])
    b.insert("MARK", 0, 0, rotation=math.pi / 2)
    return Fixture(
        "INSERT_ROTATED",
        "rotated 90 degrees a horizontal line becomes vertical, and its "
        "axis must read V rather than a near-miss SKEW",
        b.build(), {"segments": 1, "axis": "V",
                    "segment_endpoints": ((0.0, 0.0), (0.0, 1000.0))})


def _f_insert_scaled():
    b = Builder()
    e = b.line(0, 0, 1000, 0, "SYM")
    b.block("MARK", [e])
    b.insert("MARK", 0, 0, scale=(2.0, 3.0))
    return Fixture(
        "INSERT_SCALED", "non-uniform scale applies per axis",
        b.build(), {"segments": 1, "length_mm": 2000.0,
                    "segment_endpoints": ((0.0, 0.0), (2000.0, 0.0))})


def _f_insert_rotated_and_scaled():
    b = Builder()
    e = b.line(0, 0, 1000, 0, "SYM")
    b.block("MARK", [e])
    b.insert("MARK", 1000, 2000, scale=(2.0, 2.0), rotation=math.pi / 2)
    return Fixture(
        "INSERT_SCALED_THEN_ROTATED_THEN_MOVED",
        "the composition order IS the content: scale in block axes, then "
        "rotate, then translate. Any other order lands somewhere plausible "
        "and wrong",
        b.build(), {"segments": 1,
                    "segment_endpoints": ((1000.0, 2000.0),
                                          (1000.0, 4000.0))})


def _f_insert_nested():
    b = Builder()
    leaf = b.line(0, 0, 100, 0, "SYM")
    b.block("LEAF", [leaf])
    mid = b.insert("LEAF", 10, 0)
    b.block("MID", [mid])
    b.insert("MID", 1000, 500, scale=(2.0, 2.0))
    return Fixture(
        "INSERT_NESTED",
        "a block inside a block composes both transforms: the leaf's 10 mm "
        "offset is scaled by the outer 2x before the outer translation",
        b.build(), {"segments": 1, "instances": 2, "max_depth": 1,
                    "segment_endpoints": ((1020.0, 500.0), (1220.0, 500.0))})


def _f_definition_not_emitted():
    b = Builder()
    e = b.line(0, 0, 900, 0, "DOORS")
    b.block("D090", [e])
    # Defined but NEVER inserted.
    return Fixture(
        "BLOCK_DEFINED_BUT_NEVER_PLACED",
        "a definition with no instance contributes NO geometry. Emitting it "
        "would put a phantom door at the definition origin, which on a real "
        "sheet is usually inside a room",
        b.build(), {"segments": 0, "instances": 0, "definitions": 1})


def _f_door_block():
    b = Builder()
    leaf = b.line(0, 0, 0, 900, "DOORS")
    swing = b.arc(0, 0, 900, 0.0, math.pi / 2, "DOORS")
    b.block("D090", [leaf, swing])
    b.insert("D090", 4000, 0)
    b.insert("D090", 8000, 0, rotation=math.pi)
    return Fixture(
        "DOOR_BLOCK_TWO_PLACEMENTS",
        "one definition, two doors. The count of doors is the count of "
        "INSTANCES, never of definitions",
        b.build(), {"instances": 2, "definitions": 1, "segments": 2,
                    "arcs": 2, "block_name": "D090"})


def _f_room_name_block():
    b = Builder()
    t = b.text("SAL", 0, 0, 300.0, "TEXT")
    b.block("SAL", [t])
    b.insert("SAL", 2500, 1800)
    return Fixture(
        "ROOM_NAME_BLOCK",
        "a room stamp is a block whose text rides its instance transform, so "
        "the label lands in the room rather than at the block origin",
        b.build(), {"texts": 1, "text_value": "SAL",
                    "text_at": (2500.0, 1800.0), "instances": 1})


def _f_wall_two_lines():
    b = Builder()
    _wall_pair(b, 0, 0, 5000, 0, 200)
    return Fixture(
        "WALL_AS_TWO_LINES",
        "a wall drawn as two faces is two segments 200 mm apart — the "
        "adapter reports both and calls neither a wall",
        b.build(), {"segments": 2, "parallel_gap_mm": 200.0,
                    "no_wall_is_named": True})


def _f_mixed_thickness():
    b = Builder()
    _wall_pair(b, 0, 0, 5000, 0, 200)
    _wall_pair(b, 0, 3000, 5000, 3000, 300)
    return Fixture(
        "MIXED_WALL_THICKNESS",
        "two walls of different thickness in one drawing: 200 and 300. "
        "Neither is normalised to the other",
        b.build(), {"segments": 4, "distinct_gaps_mm": [200.0, 300.0]})


def _f_doorway_interruption():
    b = Builder()
    # A room whose south wall is interrupted by a 900 mm doorway.
    b.line(0, 0, 2000, 0, "WALLS")
    b.line(2900, 0, 5000, 0, "WALLS")
    b.line(0, 3000, 5000, 3000, "WALLS")
    b.line(0, 0, 0, 3000, "WALLS")
    b.line(5000, 0, 5000, 3000, "WALLS")
    return Fixture(
        "DOORWAY_INTERRUPTION",
        "the south wall stops at 2000 and resumes at 2900. The gap is 900 "
        "and the adapter must not bridge it — bridging is what turns a "
        "doorway into a wall nobody drew",
        b.build(), {"segments": 5, "collinear_gap_mm": 900.0,
                    "nothing_bridged": True})


def _f_column_in_room():
    b = Builder()
    b.line(0, 0, 5000, 0, "WALLS")
    b.line(0, 3000, 5000, 3000, "WALLS")
    b.line(0, 0, 0, 3000, "WALLS")
    b.line(5000, 0, 5000, 3000, "WALLS")
    b.lwpolyline([(2400, 1400), (2600, 1400), (2600, 1600), (2400, 1600)],
                 "COLS", closed=True)
    b.hatch("COLS")
    return Fixture(
        "COLUMN_INSIDE_ROOM",
        "a column sits inside the room on its own layer. It is geometry and "
        "it is not a room boundary — the distinction is the profile's, and "
        "the adapter must keep them separable by layer and kind",
        b.build(), {"segments": 8, "hatches": 1,
                    "layers_present": ["COLS", "WALLS"]})


def _f_unrelated_annotation():
    b = Builder(dimlfac=0.1)
    b.line(0, 0, 5000, 0, "WALLS")
    b.dimension(0, -500, 5000, -500, layer="DIM")
    b.text("GROUND FLOOR PLAN 1:100", 2000, -1500, 500.0, "TITLE")
    b.line(-1000, -2000, 6000, -2000, "TITLE")
    b.point(100, 100, "MARKERS")
    return Fixture(
        "UNRELATED_ANNOTATION_GEOMETRY",
        "dimension lines, a title and a title-block rule are geometry on "
        "their own layers. A POINT is a marker and is dropped outright — it "
        "can never be a boundary",
        b.build(), {"segments": 2, "dimensions": 1, "texts": 1,
                    "points_dropped": True,
                    "layers_present": ["DIM", "MARKERS", "TITLE", "WALLS"]})


def _f_two_drawing_areas():
    b = Builder()
    # Two room outlines 40 m apart in one model space, as sheets laid side
    # by side. Each is closed; the gap between them is far larger than
    # either.
    for ox in (0, 40000):
        b.line(ox, 0, ox + 5000, 0, "WALLS")
        b.line(ox, 3000, ox + 5000, 3000, "WALLS")
        b.line(ox, 0, ox, 3000, "WALLS")
        b.line(ox + 5000, 0, ox + 5000, 3000, "WALLS")
        b.text("PLAN", ox + 2500, -800, 500.0, "TITLE")
    return Fixture(
        "TWO_DRAWING_AREAS_IN_ONE_MODEL_SPACE",
        "two separate drawings share one model space, 40 m apart. The "
        "adapter reports one extent spanning both; separating them is "
        "localisation's job and must be possible from the coordinates alone",
        b.build(), {"segments": 8, "texts": 2,
                    "extent_width_mm": 45000.0,
                    "two_clusters_at_x": (0.0, 40000.0)})


def cases() -> list:
    """Every fixture, in a fixed order that is not their identity."""
    return [
        _f_line(), _f_lwpolyline_open(), _f_lwpolyline_closed(),
        _f_lwpolyline_bulge(), _f_arc(), _f_circle(), _f_hatch(),
        _f_text(), _f_mtext(),
        _f_dimension_plain(), _f_dimension_dimlfac(),
        _f_dimension_overridden(),
        _f_units_unitless(), _f_units_mm(),
        _f_insert_plain(), _f_insert_translated(), _f_insert_rotated(),
        _f_insert_scaled(), _f_insert_rotated_and_scaled(),
        _f_insert_nested(), _f_definition_not_emitted(),
        _f_door_block(), _f_room_name_block(),
        _f_wall_two_lines(), _f_mixed_thickness(),
        _f_doorway_interruption(), _f_column_in_room(),
        _f_unrelated_annotation(), _f_two_drawing_areas(),
    ]
