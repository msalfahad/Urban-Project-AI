"""E1.2 — general regressions on interval roles and the cold challenge.

Every fixture is invented: a long line half of which has a partner, a
free-standing band in the middle of a room, a wardrobe-sized loop beside
a column-sized one, a level mark lying in line with a wall. None is
P7757 and none carries a P7757 dimension.

What they guard, in the order the correction asks for them:

    one entity may hold a WALL interval and an UNKNOWN one
    partial support cannot promote the unsupported remainder
    every supporting fragment stays in provenance
    two parallel lines joined to nothing are not automatically a wall
    a furniture loop in the old column size range is not a column
    a loop with structural evidence is
    a level mark never inherits a wall role by being in line with one
    collinear continuation needs the band to continue
    a site-context note never becomes a physical space
    the deterministic layer cannot claim anything was seen
    the cold challenge can veto a ring that closes perfectly
    the cold challenge cannot edit CAD geometry
    a disagreement can be resolved AGAINST the frozen reading
    a conflict nothing settles withholds
    an arc's parameters survive unchanged
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from engine import arbitration as arb
from engine import atomic_interval as ai
from engine import cad_geometry as cg
from engine import deterministic_qa as dqa
from engine import interval_role as ir
from engine import label_grouping as lg
from engine import label_ontology as lo
from engine import visual_challenger as vc


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


def line(h, x1, y1, x2, y2, layer="WALLS"):
    return Prim("SEGMENT", Prov(h, "19", layer), x1=x1, y1=y1, x2=x2, y2=y2)


def arc(h, cx, cy, r, a1, a2, layer="WALLS"):
    return Prim("ARC", Prov(h, "17", layer), cx=cx, cy=cy, radius=r,
                start_angle=a1, end_angle=a2)


def loop(h, x, y, w, d, layer="WALLS"):
    return [line(h, x, y, x + w, y, layer),
            line(h + 1, x + w, y, x + w, y + d, layer),
            line(h + 2, x + w, y + d, x, y + d, layer),
            line(h + 3, x, y + d, x, y, layer)]


def roles_for(prims, **kw):
    layers = {p.provenance.layer for p in prims}
    defaults = {L: cg.MATERIAL_WALL_FACE for L in layers}
    defaults.update(kw.pop("layer_defaults", {}))
    return ir.establish(prims, layer_defaults=defaults, **kw)


def ivs(out, oid):
    return out["intervals"][oid]


# ---------------------------------------------------------------- tests

def test_1_one_entity_may_hold_two_roles():
    # a 6 m line with a counter-face along its first 2.5 m only
    prims = [line(1, 0, 0, 6000, 0),
             line(2, 0, 200, 2500, 200),
             # a perpendicular wall PAIR for the band to join at one end
             line(3, 0, 0, 0, 3000), line(4, 200, 0, 200, 3000)]
    out = roles_for(prims)
    rows = ivs(out, "CAD-1")
    roles = {iv.role for iv in rows}
    assert len(rows) >= 2, [iv.record() for iv in rows]
    assert ir.MATERIAL_WALL_FACE in roles, roles
    assert ir.UNKNOWN in roles, roles
    wall = [iv for iv in rows if iv.role == ir.MATERIAL_WALL_FACE]
    unknown = [iv for iv in rows if iv.role == ir.UNKNOWN]
    assert all(iv.may_bound_material for iv in wall)
    assert not any(iv.may_bound_material for iv in unknown)


def test_2_partial_overlap_cannot_promote_the_remainder():
    prims = [line(1, 0, 0, 6000, 0),
             line(2, 0, 200, 2500, 200),
             line(3, 0, 0, 0, 3000), line(4, 200, 0, 200, 3000)]
    out = roles_for(prims)
    rows = ivs(out, "CAD-1")
    far = max(rows, key=lambda iv: iv.start_mm[0])
    assert far.role == ir.UNKNOWN, far.record()
    assert ir.EV_UNSUPPORTED_REMAINDER in far.evidence
    supported = sum(iv.length_mm for iv in rows if iv.may_bound_material)
    # the supported stretch may reach its own end by at most a wall
    # thickness, and no further
    assert supported <= 2500.0 + ir.CORNER_REACH_MM + 1.0, supported


def test_3_every_supporting_fragment_stays_in_provenance():
    # one face, a counter-face broken into three pieces by two openings
    prims = [line(1, 0, 0, 6000, 0),
             line(2, 0, 200, 1500, 200),
             line(3, 2500, 200, 4000, 200),
             line(4, 5000, 200, 6000, 200),
             line(5, 0, 0, 0, 3000), line(6, 200, 0, 200, 3000)]
    out = roles_for(prims)
    partners = set()
    saw_union = False
    for iv in ivs(out, "CAD-1"):
        for x in iv.supporting_partner_intervals:
            partners.add(x["object_id"])
        if ir.EV_SUPPORT_UNION in iv.evidence:
            saw_union = True
    assert {"CAD-2", "CAD-3", "CAD-4"} <= partners, partners
    assert saw_union
    for iv in ivs(out, "CAD-1"):
        for x in iv.supporting_partner_intervals:
            assert "supports_t_start" in x and "supports_t_end" in x
            assert "dwg_handle" in x


def test_4_a_free_standing_paired_band_is_not_automatically_a_wall():
    # a room, and a counter drawn as two parallel lines standing in it,
    # touching nothing at either end
    prims = loop(10, 0, 0, 6000, 5000) + loop(20, -200, -200, 6400, 5400)
    prims += [line(60, 1500, 2000, 4500, 2000),
              line(61, 1500, 2150, 4500, 2150)]
    out = roles_for(prims)
    band = ivs(out, "CAD-60") + ivs(out, "CAD-61")
    assert any(iv.role == ir.AMBIGUOUS_PAIRED_BAND for iv in band), \
        [iv.record() for iv in band]
    for iv in band:
        assert not iv.may_bound_material
        if iv.role == ir.AMBIGUOUS_PAIRED_BAND:
            assert ir.EV_BAND_JOINS_NOTHING in iv.evidence
            assert set(iv.conflicting_evidence) == set(
                ir.PAIRED_BAND_READINGS)
    assert "COUNTER" in ir.PAIRED_BAND_READINGS
    assert "BAR" in ir.PAIRED_BAND_READINGS


def test_5_a_furniture_loop_in_the_column_size_range_is_not_a_column():
    # one wardrobe-sized loop on the room's own layer, alone
    prims = loop(10, 0, 0, 6000, 5000) + loop(20, -200, -200, 6400, 5400)
    prims += loop(60, 1000, 1000, 600, 600)
    out = roles_for(prims)
    rows = [iv for oid in ("CAD-60", "CAD-61", "CAD-62", "CAD-63")
            for iv in ivs(out, oid)]
    assert rows
    for iv in rows:
        assert iv.role != ir.COLUMN, iv.record()
        assert not iv.may_bound_material
    loops = out["columns"]["loops"]
    mine = [L for L in loops if "CAD-60" in L["member_object_ids"]]
    assert mine and mine[0]["ROLE"] == ir.COLUMN_CANDIDATE_UNRESOLVED
    assert mine[0]["evidence_that_is_structural_in_kind"] == []


def test_6_a_loop_with_structural_evidence_is_a_column():
    # a family of identical loops on a layer that holds nothing else
    prims = loop(10, 0, 0, 12000, 6000) + loop(20, -200, -200, 12400, 6400)
    for i in range(4):
        prims += loop(100 + i * 10, 2000 + i * 2500, 2000, 400, 400,
                      layer="STRUCT")
    out = roles_for(prims)
    loops = out["columns"]["loops"]
    struct = [L for L in loops if "STRUCT" in L["layers"]]
    assert struct, loops
    assert all(L["ROLE"] == ir.COLUMN for L in struct), struct
    assert all(ir.EV_COL_LAYER_IS_STRUCTURAL
               in L["evidence_that_is_structural_in_kind"] for L in struct)
    assert all(ir.EV_COL_FAMILY in L["STRUCTURAL_EVIDENCE"] for L in struct)
    first = ivs(out, "CAD-100")
    assert any(iv.may_bound_material for iv in first), \
        [iv.record() for iv in first]
    assert all(L["MAY_BOUND_MATERIAL"] for L in struct)


def test_7_a_level_entity_cannot_inherit_a_wall_role():
    prims = [line(1, 0, 0, 4000, 0), line(2, 0, 200, 4000, 200),
             line(3, 0, 0, 0, 3000), line(4, 200, 0, 200, 3000),
             # a level mark's leader, exactly in line with the wall face
             line(50, 5000, 0, 6000, 0, layer="LEVEL")]
    out = roles_for(prims, level_layers={"LEVEL"})
    rows = ivs(out, "CAD-50")
    for iv in rows:
        assert iv.role == ir.LEVEL_OR_GRID_ANNOTATION, iv.record()
        assert not iv.may_bound_material
    assert ir.LEVEL_OR_GRID_ANNOTATION in ir.NOT_MATERIAL_CANDIDATE


def test_8_collinear_continuation_needs_the_band_to_continue():
    # a wall, then across a doorway a lone line on the same infinite line
    # with NO counter-face of its own
    prims = [line(1, 0, 0, 3000, 0), line(2, 0, 200, 3000, 200),
             line(3, 0, 0, 0, 3000), line(4, 200, 0, 200, 3000),
             line(50, 4000, 0, 6000, 0)]
    out = roles_for(prims)
    lone = ivs(out, "CAD-50")
    for iv in lone:
        assert iv.role != ir.MATERIAL_WALL_FACE, iv.record()
        assert not iv.may_bound_material
        if ir.EV_COLLINEAR_GEOMETRIC in iv.evidence:
            assert ir.EV_MATERIAL_CONTINUATION not in iv.evidence
    # now give it a counter-face: the band continues, and so does the wall
    prims2 = prims + [line(51, 4000, 200, 6000, 200)]
    out2 = roles_for(prims2)
    assert any(iv.role == ir.MATERIAL_WALL_FACE
               for iv in ivs(out2, "CAD-50"))
    assert "SAME INFINITE LINE" in ir.COLLINEARITY_IS_NOT_MATERIAL.upper()


def test_9_site_context_labels_never_become_physical_spaces():
    inside = lg.Stamp(stamp_id="TXT-1", text="STORE", x=2000, y=2000,
                      height=200, stamp_class=lg.ENGLISH_ROOM_STAMP)
    outside = lg.Stamp(stamp_id="TXT-2", text="NEXT PLOT", x=20000, y=20000,
                       height=400, stamp_class=lg.ENGLISH_ROOM_STAMP)
    groups = [lg.Group(group_id="LG-1", members=(inside,),
                       english_token="STORE"),
              lg.Group(group_id="LG-2", members=(outside,),
                       english_token="NEXT PLOT")]
    prims = loop(10, 0, 0, 6000, 5000)
    segs = [cg._as_segment(p, role=cg.MATERIAL_WALL_FACE) for p in prims]
    out = lo.classify(groups, material_segments=segs)
    by_text = {r.text: r for r in out["rows"]}
    assert by_text["STORE"].label_class == lo.PHYSICAL_SPACE_LABEL
    assert by_text["STORE"].in_denominator
    assert by_text["NEXT PLOT"].label_class == lo.SITE_CONTEXT_ANNOTATION
    assert not by_text["NEXT PLOT"].in_denominator
    assert lo.SITE_CONTEXT_ANNOTATION not in \
        lo.IN_THE_COMPLETENESS_DENOMINATOR
    assert out["physical_and_functional_candidates"] == 1


def test_10_the_deterministic_layer_cannot_claim_it_looked():
    assert dqa.BANNED_STATE == "VISUALLY_CONSISTENT"
    assert dqa.BANNED_STATE not in dqa.QA_STATES
    prims = loop(10, 0, 0, 4000, 3000)
    ring = cg.CompositeBoundary(
        segments=tuple(cg._as_segment(p, role=cg.MATERIAL_WALL_FACE)
                       for p in prims), closed=True)
    roles = {p.object_id: {"role": ir.MATERIAL_WALL_FACE,
                           "may_bound_material": True} for p in prims}
    out = dqa.check(boundary=ring, interval_roles=roles,
                    distinct_label_groups={"STORE"}, dimension_rows=[])
    assert out["DETERMINISTIC_QA_STATE"] == [dqa.DETERMINISTICALLY_CONSISTENT]
    assert dqa.BANNED_STATE not in out["DETERMINISTIC_QA_STATE"]
    assert "never looked" in dqa.MODEL.lower().replace("_", " ") or \
        "NEVER_LOOKS" in dqa.MODEL


def test_11_the_cold_challenge_can_veto_a_ring_that_closes():
    assert vc.V2_PERMITS_RELEASE == (vc.VISUALLY_CONSISTENT,)
    for bad in (vc.COUNTER_OR_BAR_USED_AS_WALL,
                vc.INTERNAL_CASEWORK_USED_AS_BOUNDARY,
                vc.OPEN_SIDE_FALSELY_CLOSED):
        assert bad in vc.V2_STATUSES
        assert bad not in vc.V2_PERMITS_RELEASE


def test_12_the_challenge_cannot_edit_cad_geometry():
    assert vc.screen_return("the north line reads as a counter, not a wall") \
        == []
    assert "A_COORDINATE_PAIR" in vc.screen_return(
        "move the boundary to -151238, -802612")
    assert "A_MEASURED_QUANTITY" in vc.screen_return(
        "the room is 2700 mm across")
    assert "A_MEASURED_QUANTITY" in vc.screen_return("about 9.6 m2")
    assert "may not move a CAD coordinate" in \
        vc.THE_CHALLENGER_MAY_NOT_MOVE_A_COORDINATE


def test_13_a_disagreement_can_be_resolved_against_the_frozen_reading():
    out = arb.arbitrate(a18_says_open=True, cad_open=False,
                        cad_has_portal=True,
                        portal_evidence=("A_DOOR_ENTITY_STANDS_IN_THE_GAP",),
                        ambiguous_band_on_ring=(),
                        v1_open_sides=[],
                        v2_statuses=(vc.VISUALLY_CONSISTENT,))
    assert out["ARBITRATION_STATE"] == arb.A18_CHALLENGED
    assert not out["blocks_release"]
    # and the other way round, when the visual pass agrees with A18
    other = arb.arbitrate(a18_says_open=True, cad_open=False,
                          cad_has_portal=True, portal_evidence=(),
                          ambiguous_band_on_ring=(),
                          v1_open_sides=["the east side has no wall"],
                          v2_statuses=(vc.OPEN_SIDE_FALSELY_CLOSED,))
    assert other["ARBITRATION_STATE"] == arb.CAD_CHALLENGED
    assert not other["blocks_release"]


def test_14_a_conflict_nothing_settles_withholds():
    out = arb.arbitrate(a18_says_open=True, cad_open=False,
                        cad_has_portal=False, portal_evidence=(),
                        ambiguous_band_on_ring=(), v1_open_sides=None,
                        v2_statuses=())
    assert out["ARBITRATION_STATE"] == arb.UNRESOLVED
    assert out["blocks_release"]
    # an ambiguous band on the ring is itself a reason not to believe CAD
    band = arb.arbitrate(a18_says_open=True, cad_open=False,
                         cad_has_portal=True, portal_evidence=(),
                         ambiguous_band_on_ring=("E1_2:CAD-60#01",),
                         v1_open_sides=None, v2_statuses=())
    assert band["ARBITRATION_STATE"] == arb.CAD_CHALLENGED


def test_15_arc_parameters_survive_the_interval_layer():
    a = arc(1, 1234.5, -6789.25, 2500.0, 0.3, 1.9)
    rows = ai.cut(a, [(0.5, ai.CUT_INTERSECTION)])
    assert len(rows) == 2
    total = sum(iv.length_mm for iv in rows)
    assert abs(total - a.length_mm) < 1e-6
    for iv in rows:
        p = ai.point_at(a, iv.t_start)
        assert abs(math.hypot(p[0] - a.cx, p[1] - a.cy) - a.radius) < 1e-6
    seg = cg._as_segment(a, role=cg.CURVED_MATERIAL_FACE)
    rec = seg.record()
    assert rec["centre_mm"] == [1234.5, -6789.25]
    assert rec["radius_mm"] == 2500.0
    assert abs(rec["start_angle_rad"] - 0.3) < 1e-9
    assert rec["analytical_geometry"] == "THE_ORIGINAL_CURVE"


def test_16_the_vocabulary_is_complete():
    assert len(ir.ROLES) == 20
    assert len(ir.PAIRED_BAND_READINGS) == 8
    assert len(lo.LABEL_CLASSES) == 8
    assert len(dqa.QA_STATES) == 7
    assert len(vc.V1_OBSERVATIONS) == 13
    assert len(vc.V2_STATUSES) == 11
    assert len(arb.STATES) == 5
    assert len(ai.CUT_REASONS) == 10
