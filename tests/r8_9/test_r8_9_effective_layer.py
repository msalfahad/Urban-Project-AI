"""R8.9 §2-§3, §18: canonical effective layer (layer-0 inheritance through the whole insert chain) on BOTH routes,
role admission reading it, and the numeric tolerance taken from the full geometry extent."""

from __future__ import annotations

import math

import ezdxf
import pytest

from engine.source import canonical_build as CB, canonical_input as CI, geometry_role as GR, observations as O
from engine.source import room_topology as RT, topology_policy as TP
from engine.source.cad import kernel, kernel_ezdxf as K2R
from tests.r8_8 import helpers as H

ANCHOR = O.SourceRevisionAnchor(None, "T", "T")
LAYERS = ("0", "WALL", "FURNITURE", "FROZEN_ONE", "OFF_ONE")
STATES = {n: {"frozen": n == "FROZEN_ONE", "off": n == "OFF_ONE"} for n in LAYERS}


def _line(h, layer):
    return O.SourceEntityObservation(f"D1:{h}", str(h), "T:LINE", O.LINE, O.LineGeom((0.0, 0.0), (100.0, 0.0)), layer)


def _ins(h, block, layer):
    return O.SourceEntityObservation(f"D1:{h}", str(h), "T:INSERT", O.INSERT,
                                     O.InsertGeom(block, (0.0, 0.0), (1.0, 1.0, 1.0), 0.0), layer)


def k1_parts(entities, blocks=None, unknown_insert=()):
    doc = O.SourceDocument(ANCHOR, tuple(entities), blocks or {})
    obs = {o.obs_id: o for o in doc.entities}
    for b in doc.blocks.values():
        for o in b.entities:
            obs[o.obs_id] = o
    real = kernel.realise(doc)
    il = lambda p: None if p.split("[")[0] in unknown_insert else (obs[p.split("[")[0]].layer if p.split("[")[0] in obs else None)
    vis = CB.VisibilityAuthority(STATES, il)
    steps = lambda path: tuple(CI.LineageStep(p.split(":", 1)[1], "B", "BLK") for p in path)
    return CB.parts_from_realised(H.REV, real, steps, vis)


def k2_parts(build):
    doc = ezdxf.new()
    for n in LAYERS[1:]:
        doc.layers.add(n)
    doc.layers.get("FROZEN_ONE").freeze()
    doc.layers.get("OFF_ONE").off()
    build(doc)
    rg = K2R.realise(doc)
    return CB.K2(H.REV, doc, rg).parts()


def one(parts):
    (p,) = parts
    return p.layer, p.effective_layer, p.effective_layer_authority, p.visibility


# ------------------------------------------------------------------------------------------- K1 route
def test_A_model_space_line_on_wall_is_effective_wall_k1():
    assert one(k1_parts([_line(1, "WALL")])) == ("WALL", "WALL", CI.EFFECTIVE_SOURCE_LAYER, CI.VISIBLE)


def test_B_layer0_child_takes_the_insert_layer_k1():
    blk = O.BlockDefinition("HB", "SOFA_X", (0.0, 0.0), (_line(10, "0"),))
    assert one(k1_parts([_ins(20, "HB", "FURNITURE")], {"HB": blk})) == \
        ("0", "FURNITURE", CI.EFFECTIVE_BYLAYER_INSERT_CHAIN, CI.VISIBLE)


def test_C_nested_layer0_resolves_through_the_whole_chain_k1():
    inner = O.BlockDefinition("HI", "I", (0.0, 0.0), (_line(10, "0"),))
    mid = O.BlockDefinition("HM", "M", (0.0, 0.0), (_ins(11, "HI", "0"),))
    assert one(k1_parts([_ins(20, "HM", "WALL")], {"HI": inner, "HM": mid})) == \
        ("0", "WALL", CI.EFFECTIVE_BYLAYER_INSERT_CHAIN, CI.VISIBLE)


def test_D_explicit_child_layer_is_not_overridden_k1():
    blk = O.BlockDefinition("HB", "B", (0.0, 0.0), (_line(10, "FURNITURE"),))
    assert one(k1_parts([_ins(20, "HB", "WALL")], {"HB": blk})) == \
        ("FURNITURE", "FURNITURE", CI.EFFECTIVE_SOURCE_LAYER, CI.VISIBLE)


def test_E_frozen_or_off_parent_insert_layer_keeps_visibility_hidden_k1():
    blk = O.BlockDefinition("HB", "B", (0.0, 0.0), (_line(10, "0"),))
    assert one(k1_parts([_ins(20, "HB", "FROZEN_ONE")], {"HB": blk}))[3] == CI.HIDDEN_SOURCE
    assert one(k1_parts([_ins(21, "HB", "OFF_ONE")], {"HB": blk}))[3] == CI.HIDDEN_SOURCE     # layer-0 child: ByLayer


def test_F_unreadable_insert_layer_gives_no_authoritative_role_k1():
    blk = O.BlockDefinition("HB", "B", (0.0, 0.0), (_line(10, "0"),))
    parts = k1_parts([_ins(20, "HB", "WALL")], {"HB": blk}, unknown_insert=("D1:20",))
    (p,) = parts
    assert (p.effective_layer, p.effective_layer_authority) == (None, CI.EFFECTIVE_UNRESOLVED)
    assert p.visibility == CI.VISIBILITY_UNRESOLVED                  # the same unknown fails visibility closed
    assert RT.run(H.inp(parts), frame_insert=None)["sites"] is None   # TS01: METHOD_INPUT_INCOMPLETE
    from dataclasses import replace
    q = replace(p, visibility=CI.VISIBLE)                            # even if visible: no layer-based role
    a = GR.admit(H.inp([q]), frame_insert=None, eps=1e-9)["roles"][q.identity.key]
    assert a.role == GR.UNKNOWN_PHYSICAL and a.evidence["LAYER_ROLE"] is None
    assert a.evidence["effective_layer_authority"] == CI.EFFECTIVE_UNRESOLVED


# ------------------------------------------------------------------------------------------- K2 route
def test_A_to_D_on_the_ezdxf_route():
    def b(doc):
        doc.modelspace().add_line((0, 0), (100, 0), dxfattribs={"layer": "WALL"})
    assert one(k2_parts(b))[:3] == ("WALL", "WALL", CI.EFFECTIVE_SOURCE_LAYER)

    def b(doc):
        blk = doc.blocks.new("SOFA_X")
        blk.add_line((0, 0), (100, 0), dxfattribs={"layer": "0"})
        doc.modelspace().add_blockref("SOFA_X", (0, 0), dxfattribs={"layer": "FURNITURE"})
    assert one(k2_parts(b))[:3] == ("0", "FURNITURE", CI.EFFECTIVE_BYLAYER_INSERT_CHAIN)

    def b(doc):
        inner = doc.blocks.new("I")
        inner.add_line((0, 0), (100, 0), dxfattribs={"layer": "0"})
        mid = doc.blocks.new("M")
        mid.add_blockref("I", (0, 0), dxfattribs={"layer": "0"})
        doc.modelspace().add_blockref("M", (0, 0), dxfattribs={"layer": "WALL"})
    assert one(k2_parts(b))[:3] == ("0", "WALL", CI.EFFECTIVE_BYLAYER_INSERT_CHAIN)

    def b(doc):
        blk = doc.blocks.new("B")
        blk.add_line((0, 0), (100, 0), dxfattribs={"layer": "FURNITURE"})
        doc.modelspace().add_blockref("B", (0, 0), dxfattribs={"layer": "WALL"})
    assert one(k2_parts(b))[:3] == ("FURNITURE", "FURNITURE", CI.EFFECTIVE_SOURCE_LAYER)


def test_E_frozen_parent_on_the_ezdxf_route():
    def b(doc):
        blk = doc.blocks.new("B")
        blk.add_line((0, 0), (100, 0), dxfattribs={"layer": "0"})
        doc.modelspace().add_blockref("B", (0, 0), dxfattribs={"layer": "FROZEN_ONE"})
    assert one(k2_parts(b))[3] == CI.HIDDEN_SOURCE


def test_role_reads_the_effective_layer_not_the_source_layer():
    blk = O.BlockDefinition("HB", "B", (0.0, 0.0), (_line(10, "0"),))
    parts = k1_parts([_ins(20, "HB", "FURNITURE")], {"HB": blk})
    a = GR.admit(H.inp(parts), frame_insert=None, eps=1e-9)["roles"][parts[0].identity.key]
    assert a.evidence["layer"] == "FURNITURE" and a.evidence["source_layer"] == "0"
    assert a.role == GR.FURNITURE                                    # GR-03: symbol + no boundary layer + FURNITURE


def test_a_record_built_without_derivation_never_guesses_for_a_layer0_child():
    p = H.part(1, "SEGMENT", (0, 0, 1, 0), layer="0", path=("9",))
    assert CI.effective_layer(p) == (None, CI.EFFECTIVE_NOT_DERIVED)
    q = H.part(2, "SEGMENT", (0, 0, 1, 0), layer="0")
    assert CI.effective_layer(q) == ("0", CI.EFFECTIVE_SOURCE_LAYER)


# ------------------------------------------------------------------------------------------- §18
def test_eps_n_uses_the_full_extent_of_every_part():
    far = 7.5e5
    parts = [H.seg(1, 0.0, 0.0, far, 0.0)]                 # endpoint 1 at the origin, endpoint 2 far away
    assert RT.max_abs_coordinate(parts) == far
    r = RT.run(H.inp(parts), frame_insert=None)
    assert r["tolerances"]["eps_n"] == TP.eps_noise(far)
    arc = [H.part(2, "ARC", (10.0, 10.0, 1.0e5, 0.0, math.pi))]   # the extremum, not the centre
    assert RT.max_abs_coordinate(arc) == pytest.approx(1.0e5 + 10.0)
