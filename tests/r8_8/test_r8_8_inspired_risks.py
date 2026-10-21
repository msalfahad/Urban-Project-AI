"""R8.8 §29: synthetic cases inspired by other projects' known risks (no project data, no pipeline change):
mirrored / negative-extrusion geometry, nested blocks, custom entities, closed polylines."""

from __future__ import annotations

import math

from engine.source import canonical_build as CB, canonical_input as CI, observations as O, room_topology as RT
from engine.source import topology as T
from engine.source.cad import kernel
from tests.r8_8 import helpers as H

ANCHOR = O.SourceRevisionAnchor(None, "T", "T")
STATES = {"WALL": {"frozen": False, "off": False}, "0": {"frozen": False, "off": False}}


def k1_parts(entities, blocks=None):
    doc = O.SourceDocument(ANCHOR, tuple(entities), blocks or {})
    real = kernel.realise(doc)
    obs = {o.obs_id: o for o in doc.entities}
    vis = CB.VisibilityAuthority(STATES, lambda p: obs[p.split("[")[0]].layer if p.split("[")[0] in obs else "0")
    steps = lambda path: tuple(CI.LineageStep(p.split(":", 1)[1], "B" + p.split(":", 1)[1], "BLK") for p in path)
    return CB.parts_from_realised(H.REV, real, steps, vis), real


def closed_room(h, x0, y0, x1, y1, extrusion=(0.0, 0.0, 1.0)):
    verts = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    if extrusion[2] < 0:                                         # OCS x is mirrored for a -Z extrusion
        verts = tuple((-x, y) for x, y in verts)
    return O.SourceEntityObservation(f"D1:{h}", str(h), "T:LWPOLYLINE", O.LWPOLYLINE,
                                     O.PolylineGeom(verts, (0.0,) * 4, True), "WALL", extrusion)


def test_closed_polyline_room_keeps_span_identity_and_exact_area():
    parts, _ = k1_parts([closed_room(1, 0, 0, 500, 400)])
    assert sorted(p.identity.part_index for p in parts) == [0, 1, 2, 3]       # the closing span is span 3
    r = RT.run(H.inp(parts, texts=[H.text(5, "R", 100, 100)]), frame_insert=None)
    assert [round(s["area_m2"], 6) for s in r["sites"]] == [20.0] and r["sites"][0]["status"] == T.CERTIFIED


def test_negative_extrusion_room_is_measured_in_world_coordinates():
    parts, _ = k1_parts([closed_room(1, 0, 0, 500, 400, extrusion=(0.0, 0.0, -1.0))])
    xs = sorted({round(v, 9) for p in parts for v in (p.geometry[0], p.geometry[2])})
    assert xs == [0.0, 500.0]                                               # mirrored back by the OCS
    r = RT.run(H.inp(parts, texts=[H.text(5, "R", 100, 100)]), frame_insert=None)
    assert [round(s["area_m2"], 6) for s in r["sites"]] == [20.0]


def test_mirrored_nested_block_rooms_keep_identity_and_area():
    inner = O.BlockDefinition("HI", "ROOMS", (0.0, 0.0), (closed_room(10, 0, 0, 500, 400),))
    mid_ins = O.SourceEntityObservation("D1:20", "20", "T:INSERT", O.INSERT, O.InsertGeom("HI", (0.0, 0.0), (-1.0, 1.0, 1.0), 0.0), "0")
    outer = O.BlockDefinition("HO", "FLOOR", (0.0, 0.0), (mid_ins,))
    top = O.SourceEntityObservation("D1:30", "30", "T:INSERT", O.INSERT, O.InsertGeom("HO", (1000.0, 0.0), (1.0, 1.0, 1.0),
                                                                                  math.pi / 2), "0")
    parts, _ = k1_parts([top], {"HI": inner, "HO": outer})
    assert {p.identity.instance_handles for p in parts} == {("30", "20")}
    # walls inside a symbol occurrence are not admitted by GR-05 (model space only): fail closed, never measured
    r = RT.run(H.inp(parts), frame_insert=None)
    assert all(s["status"] != T.CERTIFIED or not s["labels"] for s in r["sites"]) and \
        {a.role for a in r["roles"]["roles"].values()} == {"UNKNOWN_PHYSICAL"}


def test_custom_entity_on_a_wall_layer_blocks_the_whole_input():
    room = H.box(1, 0, 0, 500, 400)
    i = H.inp(room, texts=[H.text(5, "R", 100, 100)])
    ok = RT.run(i, frame_insert=None, unrealised=[])
    assert ok["sites"][0]["status"] == T.CERTIFIED
    custom = [{"code": "CUSTOM_CLASS", "obs_id": "D1:99", "layer": "A-WALL", "path": []}]
    r = RT.run(i, frame_insert=None, unrealised=custom)
    assert r["unrealised"]["blocking_input"] and all(s["status"] == T.REVIEW_REQUIRED for s in r["sites"])
    nolayer = [{"code": "PROXY", "obs_id": "D1:98", "layer": None, "path": []}]
    assert RT.run(i, frame_insert=None, unrealised=nolayer)["unrealised"]["blocking_input"]


def test_custom_entity_on_a_layer_inside_a_room_blocks_that_room_only():
    # SUPERSEDED by R8.9 §9 (R89-D05): R8.8 localised an unrealised entity by its layer's REALISED peers, which
    # proves nothing about where the unrealised entity is. Without positive placement it now blocks the region;
    # with its own placement (e.g. an ACIS body extent) it blocks exactly the rooms it meets.
    parts = H.two_rooms() + [H.seg(60, 100, 100, 200, 100, layer="MISC")]
    i = H.inp(parts, texts=[H.text(5, "A", 250, 200), H.text(6, "B", 750, 200)])
    u = {"code": "UNHANDLED", "obs_id": "D1:97", "layer": "MISC", "path": []}
    r = RT.run(i, frame_insert=None, unrealised=[u])
    assert all("REGION_REVIEW_REQUIRED" in s["issues"] for s in r["sites"])
    r = RT.run(i, frame_insert=None, unrealised=[dict(u, extent=[100.0, 100.0, 200.0, 150.0], extent_basis="TEST")])
    by = {tuple(s["labels"]): s for s in r["sites"]}
    assert "UNREALISED_ENTITY_POSSIBLY_IN_SITE" in by[("E5",)]["issues"]
    assert "UNREALISED_ENTITY_POSSIBLY_IN_SITE" not in by[("E6",)]["issues"]


def test_unaccounted_unrealised_entities_are_stated_not_assumed_absent():
    r = RT.run(H.inp(H.box(1, 0, 0, 500, 400)), frame_insert=None)
    assert r["unrealised"]["state"].startswith("NOT_SUPPLIED")
