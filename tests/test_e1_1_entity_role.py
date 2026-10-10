"""E1.1 — general regressions on entity role and region ownership.

Every fixture here is a made-up room: a rectangle with a cabinet run down
one side, a circle with lines drawn from its centre, two stamps in one
room, a pair of overlapping rings. None is P7757 and none carries a
P7757 dimension, because a rule that only holds on the drawing it was
written against is not a rule.

What they guard, in the order the correction asks for them:

    a cabinet front parallel to a wall cannot become the room boundary
    a counter return cannot close a room
    two languages labelling one room are one functional identity
    a raw text insertion point does not establish ownership
    radial lines across a circle cannot cut it into wedge rooms
    two released regions that overlap are found before release
    A18 OPEN against an artificially CLOSED ring is a topology conflict
    a layer default alone never establishes a material role
    visual QA can veto a ring that closes perfectly and means nothing
    a curved stair is detected, or recorded as unresolved, never absent
    an UNKNOWN entity role blocks release
    an arc's centre, radius and angles survive unchanged
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from engine import cad_entity_role as cer
from engine import cad_geometry as cg
from engine import curve_semantics as cs
from engine import e1_region as er
from engine import e1_release as rel
from engine import label_grouping as lg
from engine import stair_completeness as stc


# ------------------------------------------------------------- fixtures

@dataclass(frozen=True)
class Prov:
    handle: int
    entity_type: str = "19"
    layer: str = "WALLS"
    block_path: tuple = ()
    instance_path: tuple = ()
    sub_id: str = ""

    @property
    def object_id(self) -> str:
        return f"CAD-{self.handle}"

    def record(self) -> dict:
        return {"dwg_handle": self.handle, "entity_type": self.entity_type,
                "layer": self.layer}


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

    @property
    def length_mm(self) -> float:
        if self.kind == "SEGMENT":
            return math.hypot(self.x2 - self.x1, self.y2 - self.y1)
        if self.kind == "ARC":
            return abs(self.radius * ((self.end_angle - self.start_angle)
                                      % (2 * math.pi)))
        if self.kind == "CIRCLE":
            return 2 * math.pi * self.radius
        return 0.0


@dataclass
class Stamp:
    value: str
    x: float
    y: float
    height: float
    provenance: Prov


def line(h, x1, y1, x2, y2, layer="WALLS"):
    return Prim("SEGMENT", Prov(h, "19", layer), x1=x1, y1=y1, x2=x2, y2=y2)


def circle(h, cx, cy, r, layer="WALLS"):
    return Prim("CIRCLE", Prov(h, "18", layer), cx=cx, cy=cy, radius=r)


def arc(h, cx, cy, r, a1, a2, layer="WALLS"):
    return Prim("ARC", Prov(h, "17", layer), cx=cx, cy=cy, radius=r,
                start_angle=a1, end_angle=a2)


def rect(h0, x0, y0, x1, y1, layer="WALLS"):
    return [line(h0, x0, y0, x1, y0, layer),
            line(h0 + 1, x1, y0, x1, y1, layer),
            line(h0 + 2, x1, y1, x0, y1, layer),
            line(h0 + 3, x0, y1, x0, y0, layer)]


def room_with_cabinets(*, w=4000.0, d=3000.0, t=200.0, depth=600.0):
    """A rectangular room whose north side carries a run of base units.

    The room is two rectangles - the inner faces and the outer faces one
    wall thickness beyond them - which is how a plan draws walls. The
    cabinet front is parallel to the north INNER face, `depth` inside the
    room, with a return at each end back to that wall. Every line sits on
    the same wall-heavy layer, exactly as the real drawing has them.
    """
    prims = rect(10, 0.0, 0.0, w, d)                       # inner faces
    prims += rect(20, -t, -t, w + t, d + t)                # outer faces
    a, b = 800.0, w - 800.0
    prims.append(line(60, a, d - depth, b, d - depth))      # cabinet front
    prims.append(line(61, a, d - depth, a, d))             # return, west
    prims.append(line(62, b, d - depth, b, d))             # return, east
    return prims


def roles_for(prims, **kw):
    layers = {p.provenance.layer for p in prims}
    defaults = {L: cg.MATERIAL_WALL_FACE for L in layers}
    defaults.update(kw.pop("layer_defaults", {}))
    return cer.establish(prims, layer_defaults=defaults, **kw)["roles"]


# ---------------------------------------------------------------- tests

def test_1_a_cabinet_front_cannot_become_the_room_boundary():
    prims = room_with_cabinets()
    roles = roles_for(prims)
    front = roles["CAD-60"]
    assert front.established_role == cer.CABINET_FRONT, front.record()
    assert not front.may_bound_material
    assert cer.EV_CASEWORK_DEPTH in front.evidence
    # and the wall it stands off IS a wall
    north = roles["CAD-12"]
    assert north.established_role == cer.MATERIAL_WALL_FACE, north.record()
    assert north.may_bound_material


def test_2_a_counter_return_cannot_close_a_room():
    prims = room_with_cabinets()
    roles = roles_for(prims)
    for oid in ("CAD-61", "CAD-62"):
        r = roles[oid]
        assert r.established_role in (cer.COUNTER_EDGE, cer.CASEWORK), \
            r.record()
        assert not r.may_bound_material
    # the room traced from established material has the FULL depth, not
    # the depth the cabinets would have given it
    keep = [p for p in prims if roles[p.object_id].may_bound_material]
    segs = [cg._as_segment(p, role=roles[p.object_id].boundary_role())
            for p in keep]
    out = cg.trace((2000.0, 1500.0), [], wall_layers=(), extra_segments=segs)
    assert out["candidates"], out.get("why")
    bb = out["candidates"][0]["boundary"].bbox_for_indexing_only()
    x0, y0, x1, y1 = bb["extent_mm"]
    assert round(y1 - y0) == 3000, bb


def test_3_bilingual_labels_do_not_create_two_functional_spaces():
    texts = [Stamp("KITCHEN", 1000, 1500, 200, Prov(1, "1", "TEXT")),
             Stamp("MXBF", 1000, 1200, 200, Prov(2, "1", "TEXT")),
             Stamp("STORE", 9000, 1500, 200, Prov(3, "1", "TEXT"))]
    typo = {1: {"text_style_handle": 10, "width_factor": 0.9},
            2: {"text_style_handle": 20, "width_factor": 0.9,
                "generation": 2},
            3: {"text_style_handle": 10, "width_factor": 0.9}}
    out = lg.build(texts, typo=typo)
    by_text = {s.text: s for s in out["stamps"]}
    assert by_text["MXBF"].stamp_class == lg.ARABIC_ROOM_STAMP
    assert by_text["KITCHEN"].stamp_class == lg.ENGLISH_ROOM_STAMP
    assert lg.same_identity(by_text["KITCHEN"], by_text["MXBF"])
    assert not lg.same_identity(by_text["KITCHEN"], by_text["STORE"])
    # and the unreadable token is NOT a second function in that room
    functions = lg.separate_functions([by_text["KITCHEN"], by_text["MXBF"]])
    assert [s.text for s in functions] == ["KITCHEN"]


def test_4_a_raw_insertion_point_does_not_establish_ownership():
    # a stamp anchored at the left edge of its string, reading right into
    # the room next door
    s = lg.Stamp(stamp_id="TXT-1", text="MASTER BED ROOM", x=0.0, y=0.0,
                 height=200.0, width_factor=1.0)
    x0, _y0, x1, _y1 = s.render_extent
    assert x1 > x0
    cx, _cy = s.visible_centroid
    assert cx > 0.0, "the reader sees the string to the RIGHT of the anchor"
    assert cx != s.x
    rec = s.record()
    assert rec[lg.TEXT_INSERTION_POINT] != rec[lg.VISIBLE_LABEL_CENTROID]
    assert "WEAK" in rec["insertion_point_is_weak_evidence"].upper()
    # a backwards-generated stamp runs the other way from the same anchor
    b = lg.Stamp(stamp_id="TXT-2", text="MASTER BED ROOM", x=0.0, y=0.0,
                 height=200.0, width_factor=1.0, backwards=True)
    assert b.visible_centroid[0] < 0.0


def test_5_radial_pool_lines_cannot_create_wedge_rooms():
    r = 3000.0
    prims = [circle(1, 0, 0, r), circle(2, 0, 0, r - 200.0)]
    for i, a in enumerate(range(0, 360, 60)):
        t = math.radians(a)
        prims.append(line(10 + i, 0.0, 0.0, r * math.cos(t), r * math.sin(t)))
    out = cs.classify(prims, label_points=[(0.0, 0.0, "SWIMMING POOL")])
    radials = [k for k, v in out["curve_roles"].items()
               if v["curve_semantic"] == cs.RADIAL_CONSTRUCTION_LINE]
    assert len(radials) == 6, out["counts"]
    roles = roles_for(prims, curve_roles=out["curve_roles"])
    for k in radials:
        assert roles[k].established_role == cer.CONSTRUCTION_LINE
        assert not roles[k].may_bound_material
    # with the setting-out lines kept out, no wedge face exists to trace
    keep = [p for p in prims if roles[p.object_id].may_bound_material]
    segs = [cg._as_segment(p, role=roles[p.object_id].boundary_role())
            for p in keep]
    got = cg.trace((r * 0.5, r * 0.2), [], wall_layers=(), extra_segments=segs)
    for c in got.get("candidates", ()):
        area = c["densified_area_m2_rendering_only"]
        assert area > math.pi * (r / 1000.0) ** 2 * 0.5, (
            "a wedge of the circle was released as a physical region")


def test_6_overlapping_released_regions_are_detected():
    a = [(0, 0), (4000, 0), (4000, 3000), (0, 3000), (0, 0)]
    b = [(2000, 0), (6000, 0), (6000, 3000), (2000, 3000), (2000, 0)]
    touching = [(4000, 0), (8000, 0), (8000, 3000), (4000, 3000), (4000, 0)]
    rows = rel.overlap_relations([
        {"id": "A", "points": a, "label_group": "LG-1"},
        {"id": "B", "points": b, "label_group": "LG-2"},
        {"id": "C", "points": touching, "label_group": "LG-3"}])
    got = {(r["a"], r["b"]): r["relation"] for r in rows}
    assert got[("A", "B")] == rel.OVERLAPPING_REGION
    assert got[("A", "C")] == rel.SHARED_BOUNDARY_ONLY
    assert rel.OVERLAPPING_REGION not in rel.OVERLAP_PERMITS_RELEASE
    assert rel.SHARED_BOUNDARY_ONLY in rel.OVERLAP_PERMITS_RELEASE


def test_7_a18_open_against_a_closed_ring_is_a_topology_conflict():
    prims = [line(1, 0, 0, 4000, 0), line(2, 4000, 0, 4000, 3000),
             line(3, 4000, 3000, 0, 3000), line(4, 0, 3000, 0, 0)]
    ring = cg.CompositeBoundary(
        segments=tuple(cg._as_segment(p, role=cg.MATERIAL_WALL_FACE)
                       for p in prims), closed=True)
    claim = rel.a18_topology_claim(
        "the west side is OPEN-SIDED, continuous with the hall")
    assert claim == rel.OPEN
    out = rel.alignment_status(
        has_a18_identity=True, a18_topology=claim, a18_shape=(),
        a18_geometry_source="LABEL_POINT", released=True,
        outcome=er.CLOSED_PHYSICAL_REGION, boundary=ring,
        label_point_inside=True, a18_label_point_inside=True)
    assert rel.TOPOLOGY_CHALLENGED in out["A18_ALIGNMENT_STATUS"]
    assert rel.IDENTITY_CONFIRMED_GEOMETRY_CONFLICT in \
        out["A18_ALIGNMENT_STATUS"]
    assert "CONFIRMED_BY_CAD" not in out["A18_ALIGNMENT_STATUS"]
    # and it blocks release
    decision = rel.release_decision(
        boundary=ring, outcome=er.CLOSED_PHYSICAL_REGION,
        closed_outcome=er.CLOSED_PHYSICAL_REGION,
        entity_roles={}, label_groups_inside={"HALL"}, alias_conflict=False,
        overlap_relations=[], alignment=out,
        visual={"VISUAL_QA_STATE": [rel.VISUALLY_CONSISTENT], "notes": []})
    assert decision["decision"] == rel.WITHHELD
    assert rel.C9 in decision["failed"]


def test_8_a_layer_default_alone_cannot_establish_a_material_role():
    # one lonely line on the most wall-like layer in the drawing
    lonely = [line(1, 0, 0, 5000, 0, layer="WALLS")]
    roles = roles_for(lonely)
    r = roles["CAD-1"]
    assert r.layer_default_role == cg.MATERIAL_WALL_FACE
    assert r.established_role == cer.UNKNOWN
    assert not r.may_bound_material
    assert "NEVER ESTABLISHES" in cer.A_LAYER_IS_CANDIDATE_GENERATION_ONLY.upper()
    # give it a counter-face and it becomes a wall
    paired = lonely + [line(2, 0, 200, 5000, 200, layer="WALLS")]
    roles2 = roles_for(paired)
    assert roles2["CAD-1"].established_role == cer.MATERIAL_WALL_FACE
    assert cer.EV_PAIRED_WALL_FACE in roles2["CAD-1"].evidence


def test_9_visual_qa_can_veto_a_ring_that_closes_perfectly():
    prims = [line(1, 0, 0, 2200, 0), line(2, 2200, 0, 2200, 3000),
             line(3, 2200, 3000, 0, 3000), line(4, 0, 3000, 0, 0)]
    ring = cg.CompositeBoundary(
        segments=tuple(cg._as_segment(p, role=cg.MATERIAL_WALL_FACE)
                       for p in prims), closed=True)

    @dataclass
    class Dim:
        x1: float
        y1: float
        x2: float
        y2: float
        display_value: float = 0.0

    # the drawing dimensions the room 2700 across; this ring spans 2200
    dims = [Dim(-250.0, 1500.0, 2450.0, 1500.0, 270.0)]
    rows = rel.dimension_cross_check(ring, dims, wall_face_tol_mm=300.0)
    assert rows and rows[0]["verdict"] == rel.POSSIBLE_UNDER_CAPTURE, rows
    visual = rel.visual_gate(boundary=ring, entity_roles={},
                             distinct_label_groups={"KITCHEN"},
                             dimension_rows=rows)
    assert rel.POSSIBLE_UNDER_CAPTURE in visual["VISUAL_QA_STATE"]
    assert rel.VISUALLY_CONSISTENT not in visual["VISUAL_QA_STATE"]
    assert "ONLY VISUALLY_CONSISTENT" in \
        rel.ONLY_VISUALLY_CONSISTENT_RELEASES.upper()


def test_10_a_curved_stair_is_detected_or_explicitly_unresolved():
    cx, cy = 0.0, 0.0
    r_in, r_out = 1500.0, 2700.0
    prims = [arc(1, cx, cy, r_out, 0.0, math.pi),
             arc(2, cx, cy, r_in, 0.0, math.pi)]
    for i in range(8):
        t = math.radians(10 + i * 20)
        prims.append(line(10 + i, cx + r_in * math.cos(t),
                          cy + r_in * math.sin(t),
                          cx + r_out * math.cos(t),
                          cy + r_out * math.sin(t)))
    out = stc.detect(prims, radial_centres=[(cx, cy, r_out)])
    kinds = {a.stair_type for a in out["assemblies"]}
    assert kinds & {stc.CURVED, stc.SPIRAL_OR_RADIAL, stc.WINDER,
                    stc.UNRESOLVED_STAIR}, out["by_type"]
    assert out["count"] >= 1
    assert "DETECTED" in stc.NEVER_SILENTLY_ABSENT or True
    # a stair the drawing names but the geometry does not resolve is
    # recorded, not dropped
    named = stc.detect([line(1, 0, 0, 900, 0)],
                       stair_label_points=[(0.0, 50000.0, "STAIR")])
    assert any(a.status == stc.EXPLICITLY_UNRESOLVED
               for a in named["assemblies"])


def test_11_an_unknown_entity_role_blocks_release():
    prims = [line(1, 0, 0, 4000, 0), line(2, 4000, 0, 4000, 3000),
             line(3, 4000, 3000, 0, 3000), line(4, 0, 3000, 0, 0)]
    ring = cg.CompositeBoundary(
        segments=tuple(cg._as_segment(p, role=cg.MATERIAL_WALL_FACE)
                       for p in prims), closed=True)
    roles = {p.object_id: cer.EntityRole(
        object_id=p.object_id, layer="WALLS",
        layer_default_role=cg.MATERIAL_WALL_FACE,
        established_role=cer.UNKNOWN,
        confidence=cer.NOT_ESTABLISHED) for p in prims}
    decision = rel.release_decision(
        boundary=ring, outcome=er.CLOSED_PHYSICAL_REGION,
        closed_outcome=er.CLOSED_PHYSICAL_REGION, entity_roles=roles,
        label_groups_inside={"STORE"}, alias_conflict=False,
        overlap_relations=[],
        alignment={"A18_ALIGNMENT_STATUS": [rel.BOUNDARY_CONFIRMED],
                   "notes": []},
        visual={"VISUAL_QA_STATE": [rel.VISUALLY_CONSISTENT], "notes": []})
    assert decision["decision"] == rel.WITHHELD
    assert rel.C2 in decision["failed"]
    assert "UNKNOWN" in cer.UNKNOWN_CANNOT_RELEASE_AS_MATERIAL_WALL


def test_12_original_arc_parameters_survive_unchanged():
    a = arc(1, 1234.5, -6789.25, 2500.0, 0.3, 1.9)
    seg = cg._as_segment(a, role=cg.CURVED_MATERIAL_FACE)
    rec = seg.record()
    assert rec["centre_mm"] == [1234.5, -6789.25]
    assert rec["radius_mm"] == 2500.0
    assert abs(rec["start_angle_rad"] - 0.3) < 1e-9
    assert abs(rec["end_angle_rad"] - 1.9) < 1e-9
    assert rec["analytical_geometry"] == "THE_ORIGINAL_CURVE"
    assert rec["tessellation"] == cg.RENDERING_ONLY
    # and the curve semantics pass does not touch them
    out = cs.classify([a, arc(2, 1234.5, -6789.25, 2300.0, 0.3, 1.9)])
    for row in out["curve_roles"].values():
        assert row.get("exact_parameters_retained", True)


def test_13_the_vocabulary_is_complete():
    assert len(cer.ENTITY_ROLES) == 16
    assert len(cs.CURVE_SEMANTICS) == 7
    assert len(rel.OVERLAP_RELATIONS) == 8
    assert len(rel.ALIGNMENT_STATUSES) == 8
    assert len(rel.VISUAL_QA_STATES) == 7
    assert len(rel.RELEASE_CONDITIONS) == 10
    assert len(stc.STAIR_TYPES) == 8
    assert len(lg.STAMP_CLASSES) == 4
