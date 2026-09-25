"""E1 — general regressions on the physical-geometry layer.

None of these is a P7757 target. They are a square room, a room with one
curved wall, two rooms with a doorway between them, and an open-plan pair,
because a rule that only holds on the drawing it was written against is
not a rule.

What they guard, in order: a curve survives; an open edge stays open; a
doorway closure is never wall material; a dimension witness cannot close a
room; a label inside a small face does not own it; a bounding box cannot
become measurement geometry; a junction repair is distinguishable from
drawn CAD; agreement between two representations of one design is named as
such; and an unresolved region is withheld rather than forced closed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from engine import cad_geometry as cg
from engine import e1_region as er


# ------------------------------------------------------------- fixtures

@dataclass(frozen=True)
class Prov:
    handle: int
    entity_type: str
    layer: str
    block_path: tuple = ()
    instance_path: tuple = ()
    sub_id: str = ""

    @property
    def object_id(self) -> str:
        return f"CAD-{self.handle}"


@dataclass(frozen=True)
class Prim:
    kind: str
    provenance: Prov
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


def line(h, x1, y1, x2, y2, layer="W"):
    return Prim("SEGMENT", Prov(h, "19", layer), x1=x1, y1=y1, x2=x2, y2=y2)


def arc(h, cx, cy, r, a1, a2, layer="W"):
    return Prim("ARC", Prov(h, "17", layer), cx=cx, cy=cy, radius=r,
                start_angle=a1, end_angle=a2)


def square_room(h0=1, x=0.0, y=0.0, w=4000.0, d=3000.0, layer="W"):
    return [line(h0, x, y, x + w, y, layer),
            line(h0 + 1, x + w, y, x + w, y + d, layer),
            line(h0 + 2, x + w, y + d, x, y + d, layer),
            line(h0 + 3, x, y + d, x, y, layer)]


WALL = {"W"}
ROLE = {"W": cg.MATERIAL_WALL_FACE}


# ------------------------------------------------------------ 1. curves

def test_an_arc_survives_cad_to_boundary_unchanged():
    # three straight sides and one quarter-round side
    r = 2000.0
    prims = [line(1, 0, 0, 2000, 0),
             line(2, 2000, 0, 2000, 2000),
             line(3, 0, 2000, 0, 0),
             arc(4, 0, 0, r, 0.0, math.pi / 2)]
    out = cg.trace((400, 400), prims, wall_layers=WALL, role_of=ROLE)
    assert out["candidates"], out.get("why")
    b = out["candidates"][0]["boundary"]
    curved = [s for s in b.segments if s.kind == cg.ARC]
    assert curved, "the arc did not survive into the boundary"
    got = curved[0]
    assert got.radius == r
    assert abs(got.sweep - math.pi / 2) < 1e-6
    assert got.object_id == "CAD-4"
    rec = got.record()
    assert rec["exact_parameters_retained"] is True
    assert rec["analytical_geometry"] == "THE_ORIGINAL_CURVE"
    assert rec["tessellation"] == cg.RENDERING_ONLY
    assert b.kind == cg.COMPOSITE_CURVE


def test_a_chord_never_becomes_the_stored_geometry():
    a = cg.BoundarySegment(kind=cg.ARC, cx=0, cy=0, radius=1000,
                           start_angle=0, end_angle=math.pi,
                           object_id="CAD-9", layer="W")
    # the tessellation is many points; the geometry is still one arc
    assert len(a.points(tol_mm=0.1)) > 20
    assert a.record()["kind"] == cg.ARC
    assert "points" not in a.record()
    assert abs(a.length_mm - 1000 * math.pi) < 1e-6


# -------------------------------------------------------- 2. open edges

def test_an_open_plan_region_may_remain_open():
    # three sides only: nothing closes the fourth
    prims = [line(1, 0, 0, 4000, 0), line(2, 4000, 0, 4000, 3000),
             line(3, 4000, 3000, 0, 3000)]
    out = cg.trace((2000, 1500), prims, wall_layers=WALL, role_of=ROLE)
    assert out["candidates"] == []
    reg = er.assess(cad_geometry_id="G1", a18_candidate_id="A1",
                    drawing_id="D", floor="GROUND", label="LOUNGE",
                    trace_result=out)
    assert reg.outcome == er.OPEN_PHYSICAL_REGION
    assert reg.boundary is None
    assert reg.record()["no_polygon"] == er.NO_CLOSED_PHYSICAL_POLYGON_FROM_CAD


# ------------------------------------------- 3. doorways are not material

def test_a_doorway_closure_never_becomes_wall_material():
    prims = square_room()
    # a 900 mm doorway in the south wall
    prims[0] = line(1, 0, 0, 1500, 0)
    prims.append(line(5, 2400, 0, 4000, 0))
    closed = cg.close_openings(prims, wall_layers=WALL, door_layers=set())
    assert closed["gaps_closed"] == 1
    row = closed["rows"][0]
    assert row["boundary_role"] == cg.VIRTUAL_PORTAL_BOUNDARY
    assert row["material_present"] is False
    assert row["wall_length_contribution_mm"] == 0.0
    assert row["opening_width_mm"] == 900.0
    assert row["host_wall_faces"]
    assert row["jamb_endpoints_mm"]

    bar = closed["barriers"][0]
    assert bar.length_mm == 900.0
    assert bar.wall_length_contribution_mm == 0.0
    assert bar.material_present is False

    out = cg.trace((2000, 1500), prims, wall_layers=WALL, role_of=ROLE,
                   extra_segments=closed["barriers"])
    b = out["candidates"][0]["boundary"]
    assert b.contains_artificial_topology is True
    # the ring is 14 m of built wall plus 0.9 m of nothing
    assert abs(b.perimeter_mm - 14000.0) < 1.0
    assert abs(b.material_length_mm - 13100.0) < 1.0
    assert abs(b.topology_only_length_mm - 900.0) < 1.0
    assert b.record()["length_by_boundary_role"][
        cg.VIRTUAL_PORTAL_BOUNDARY] == 900.0


# --------------------------------------- 4. annotation cannot close a room

def test_a_dimension_witness_line_cannot_close_a_physical_room():
    prims = square_room()
    prims[0] = line(1, 0, 0, 1500, 0)
    prims.append(line(5, 2400, 0, 4000, 0))
    # a witness line lying exactly across the gap, on a dimension layer
    prims.append(line(6, 1500, 0, 2400, 0, layer="DIM"))
    out = cg.trace((2000, 1500), prims, wall_layers=WALL, role_of=ROLE)
    assert out["candidates"] == [], (
        "a dimension witness line closed a room, which it must never do")

    # and if one reaches a ring by any route, validation fails it
    ring = cg.CompositeBoundary(segments=(
        cg.BoundarySegment(kind=cg.LINE, x1=0, y1=0, x2=1000, y2=0,
                           role=cg.MATERIAL_WALL_FACE, object_id="CAD-1"),
        cg.BoundarySegment(kind=cg.LINE, x1=1000, y1=0, x2=1000, y2=1000,
                           role=cg.DIMENSION_WITNESS, object_id="CAD-6"),
    ), closed=True)
    reg = er.Region(outcome=er.CLOSED_PHYSICAL_REGION, boundary=ring)
    reg = er.validate(reg)
    assert reg.validation["checks"][er.V_NO_ANNOTATION_WALL]["result"] == er.FAIL
    assert reg.released is False


# ------------------------------------------------- 5. labels do not own

def test_a_label_inside_a_small_unrelated_polygon_does_not_own_it():
    # a cupboard inside a room; the room's stamp happens to fall in it
    prims = square_room() + square_room(h0=10, x=200, y=200, w=600, d=600)
    out = cg.trace((400, 400), prims, wall_layers=WALL, role_of=ROLE)
    reg = er.assess(cad_geometry_id="G1", a18_candidate_id="A1",
                    drawing_id="D", floor="GROUND", label="BEDROOM",
                    trace_result=out, labels_in_face=("BEDROOM", "CUPBOARD"))
    assert er.LABEL_POLYGON_OWNERSHIP_CONFLICT in reg.conflicts
    assert reg.outcome == er.MULTI_FUNCTION_PHYSICAL_REGION
    reg = er.validate(reg)
    assert reg.validation["checks"][er.V_LABEL_OWNERSHIP]["result"] == er.FAIL
    assert reg.released is False


def test_a_floor_plate_is_not_the_labelled_room():
    prims = square_room(w=30000.0, d=20000.0)      # 600 m2
    out = cg.trace((15000, 10000), prims, wall_layers=WALL, role_of=ROLE)
    reg = er.assess(cad_geometry_id="G1", a18_candidate_id="A1",
                    drawing_id="D", floor="GROUND", label="PANTRY",
                    trace_result=out)
    assert reg.outcome == er.NO_UNIQUE_PHYSICAL_REGION
    assert reg.boundary is None


# ------------------------------------------------- 6. bounding boxes

def test_a_bounding_box_cannot_become_measurement_geometry():
    prims = [line(1, 0, 0, 2000, 0), line(2, 2000, 0, 2000, 2000),
             line(3, 0, 2000, 0, 0), arc(4, 0, 0, 2000, 0.0, math.pi / 2)]
    out = cg.trace((400, 400), prims, wall_layers=WALL, role_of=ROLE)
    b = out["candidates"][0]["boundary"]
    box = b.bbox_for_indexing_only()
    assert box["BOUNDING_BOX_IS_NOT_MEASUREMENT_GEOMETRY"] is True
    assert "why" in box
    rec = b.record()
    assert rec["bounding_box"]["BOUNDING_BOX_IS_NOT_MEASUREMENT_GEOMETRY"]
    # the boundary itself is segments, not a box
    assert rec["BOUNDARY_SEGMENTS"]
    assert rec["representation"] in (cg.COMPOSITE_CURVE, cg.POLYLINE)


# ----------------------------------------- 7. repairs versus drawn CAD

def test_a_junction_repair_is_distinguishable_from_drawn_cad():
    prims = square_room()
    # the south wall stops 3 mm short of the corner
    prims[0] = line(1, 0, 0, 3997, 0)
    closed = cg.close_openings(prims, wall_layers=WALL, door_layers=set())
    assert closed["junction_repairs"] == 1
    assert closed["openings"] == 0
    row = closed["rows"][0]
    assert row["class"] == cg.CAD_JUNCTION_REPAIR
    assert row["original_vs_repaired"] == "REPAIRED_TOPOLOGY"
    bar = closed["barriers"][0]
    assert bar.role == cg.CAD_JUNCTION_REPAIR
    assert bar.entity_type == "CAD_JUNCTION_REPAIR_NOT_AN_ORIGINAL_CAD_ENTITY"
    assert bar.object_id == ""              # it is not a drawn entity
    assert bar.wall_length_contribution_mm == 0.0


# ------------------------------------------- 8. corroboration language

def test_raster_and_cad_agreement_is_cross_representation():
    got = er.corroboration(source_families=["DESIGN", "DESIGN"])
    assert got["kind"] == er.CROSS_REPRESENTATION_CORROBORATION
    assert "same" in got["why"].lower() or "one design" in got["why"].lower()
    two = er.corroboration(source_families=["DESIGN", "SITE_MEASUREMENT"])
    assert two["kind"] == er.INDEPENDENT_SOURCE_FAMILY_CORROBORATION


# ------------------------------------------------ 9. withhold, not force

def test_an_unresolved_region_is_withheld_rather_than_force_closed():
    ring = cg.CompositeBoundary(segments=(
        cg.BoundarySegment(kind=cg.LINE, x1=0, y1=0, x2=1000, y2=0,
                           role=cg.MATERIAL_WALL_FACE, object_id="CAD-1"),
        cg.BoundarySegment(kind=cg.LINE, x1=1000, y1=0, x2=1000, y2=1000,
                           role=cg.VIRTUAL_PORTAL_BOUNDARY),
    ), closed=True)
    reg = er.Region(outcome=er.CLOSED_PHYSICAL_REGION, boundary=ring)
    reg = er.validate(reg)
    assert reg.validation["checks"][
        er.V_NO_UNEXPLAINED_CLOSURE]["result"] == er.FAIL
    assert reg.validation["verdict"] == er.WITHHELD
    assert reg.released is False
    assert "repair" in reg.validation["rule"].lower()


def test_material_share_gates_a_closed_physical_region():
    # a ring that is mostly inserted topology is not a physical room
    prims = square_room()
    prims[0] = line(1, 0, 0, 800, 0)
    prims[1] = line(2, 4000, 0, 4000, 600)
    out = cg.trace((2000, 1500), prims, wall_layers=WALL, role_of=ROLE)
    assert out["candidates"] == []


def test_every_outcome_and_check_name_is_declared():
    assert len(er.OUTCOMES) == 6
    assert len(er.CHECKS) == 12
    assert len(cg.ROLES) == 13
    assert set(cg.MATERIAL_ROLES) <= set(cg.ROLES)
    assert set(cg.TOPOLOGY_ONLY_ROLES) <= set(cg.ROLES)
    assert not set(cg.MATERIAL_ROLES) & set(cg.TOPOLOGY_ONLY_ROLES)
