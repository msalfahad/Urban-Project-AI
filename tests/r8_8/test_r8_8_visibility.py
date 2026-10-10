"""R8.8 §9-§10: visibility AUTHORITY for parts, texts and dimensions alike. Nothing is VISIBLE by default."""

from __future__ import annotations

import pytest

from engine.source import canonical_build as CB, canonical_input as CI, room_topology as RT
from tests.r8_8 import helpers as H

ezdxf = pytest.importorskip("ezdxf")


@pytest.fixture(scope="module")
def k2():
    from engine.source.cad import kernel_ezdxf as K2R
    d = ezdxf.new()
    d.layers.add("VIS")
    d.layers.add("FROZ").freeze()
    d.layers.add("OFF").off()
    msp = d.modelspace()
    msp.add_text("ROOM_A", dxfattribs={"layer": "VIS", "insert": (10, 10)})
    msp.add_text("ROOM_F", dxfattribs={"layer": "FROZ", "insert": (20, 10)})
    t_flag = msp.add_text("ROOM_H", dxfattribs={"layer": "VIS", "insert": (30, 10)})
    t_flag.dxf.invisible = 1
    dm_vis = msp.add_linear_dim(base=(0, 50), p1=(0, 40), p2=(100, 40), dxfattribs={"layer": "VIS"})
    dm_vis.render()
    dm_off = msp.add_linear_dim(base=(0, 80), p1=(0, 70), p2=(100, 70), dxfattribs={"layer": "OFF"})
    dm_off.render()
    blk = d.blocks.new_anonymous_block(type_char="U")
    blk.add_text("ROOM_U", dxfattribs={"layer": "VIS", "insert": (0, 0)})
    blk.add_linear_dim(base=(0, 5), p1=(0, 0), p2=(10, 0), dxfattribs={"layer": "VIS"}).render()
    msp.add_blockref(blk.name, (200, 200), dxfattribs={"layer": "VIS"})
    real = K2R.realise(d)
    b = CB.K2("R", d, real)
    texts = {t.value: t for t in b.texts()}
    dims = b.dimensions()
    return {"texts": texts, "dims": dims, "doc": d, "dm_vis": dm_vis, "dm_off": dm_off}


def test_visible_ordinary_text_and_dimension(k2):
    assert k2["texts"]["ROOM_A"].visibility == CI.VISIBLE
    vis = [x for x in k2["dims"] if x.identity.source_handle == str(int(k2["dm_vis"].dimension.dxf.handle, 16))]
    assert vis and vis[0].visibility == CI.VISIBLE


def test_hidden_source_text_and_dimension(k2):
    assert k2["texts"]["ROOM_F"].visibility == CI.HIDDEN_SOURCE          # frozen layer
    assert k2["texts"]["ROOM_H"].visibility == CI.HIDDEN_SOURCE          # entity invisibility flag
    off = [x for x in k2["dims"] if x.identity.source_handle == str(int(k2["dm_off"].dimension.dxf.handle, 16))]
    assert off and off[0].visibility == CI.HIDDEN_SOURCE                 # layer off


def test_text_and_dimension_in_unresolved_dynamic_block(k2):
    assert k2["texts"]["ROOM_U"].visibility == CI.VISIBILITY_UNRESOLVED
    inside = [x for x in k2["dims"] if x.identity.instance_handles]
    assert inside and all(x.visibility == CI.VISIBILITY_UNRESOLVED for x in inside)


def test_layer_state_not_read_means_unresolved_never_visible():
    va = CB.VisibilityAuthority(None, lambda p: "0")
    assert va("WALL", ()) == CI.VISIBILITY_UNRESOLVED
    va = CB.VisibilityAuthority({"WALL": {"frozen": False, "off": False}}, lambda p: "MISSING")
    assert va("WALL", ()) == CI.VISIBLE
    assert va("WALL", ("D1:9",)) == CI.VISIBILITY_UNRESOLVED                 # insert layer not in the table
    st = {"A": {"frozen": True, "off": False}, "B": {"frozen": False, "off": True}, "0": {"frozen": False, "off": False},
          "W": {"frozen": False, "off": False}}
    va = CB.VisibilityAuthority(st, lambda p: {"D1:1": "A", "D1:2": "B"}[p])
    assert va("W", ("D1:1",)) == CI.HIDDEN_SOURCE                           # frozen insert layer hides all
    assert va("W", ("D1:2",)) == CI.VISIBLE                                 # off insert layer: own-layer child shows
    assert va("0", ("D1:2",)) == CI.HIDDEN_SOURCE                           # ByLayer child of an off insert


def test_unresolved_text_fails_closed_and_hidden_text_cannot_label_a_room():
    room = H.box(1, 0, 0, 500, 400)
    unresolved = H.inp(room, texts=[H.text(50, "ROOM_U", 250, 200, vis=CI.VISIBILITY_UNRESOLVED)])
    r = RT.run(unresolved, frame_insert=None)
    assert r["state"] == CI.METHOD_INPUT_INCOMPLETE and r["sites"] is None
    hidden = H.inp(room, texts=[H.text(51, "ROOM_H", 250, 200, vis=CI.HIDDEN_SOURCE)])
    r = RT.run(hidden, frame_insert=None)
    assert r["state"] == "BUILT" and [s["labels"] for s in r["sites"]] == [[]]
    shown = H.inp(room, texts=[H.text(52, "ROOM_A", 250, 200)])
    assert [s["labels"] for s in RT.run(shown, frame_insert=None)["sites"]] == [["E52"]]


def test_hidden_or_unresolved_dimension_fails_closed_when_the_method_requires_it():
    c = CI.MethodContract("NEEDS_DIMS", "1", dimension_fields=("dimension_identity", "measurement", "visibility"))
    assert CI.validate(H.inp(dims=[H.dim(1)]), c)["state"] == CI.COMPLETE
    assert CI.validate(H.inp(dims=[H.dim(1, vis=CI.VISIBILITY_UNRESOLVED)]), c)["state"] == CI.METHOD_INPUT_INCOMPLETE
    assert CI.validate(H.inp(dims=[H.dim(1, vis=CI.HIDDEN_SOURCE)]), c)["state"] == CI.METHOD_INPUT_INCOMPLETE
    from dataclasses import replace
    v = CI.validate(H.inp(dims=[H.dim(1, vis=CI.HIDDEN_SOURCE)]), replace(c, hidden_excluded=True))
    assert v["state"] == CI.COMPLETE and v["hidden_excluded"] == {"dimensions": 1}
    v = CI.validate(H.inp(dims=[H.dim(1, vis=CI.VISIBILITY_UNRESOLVED)]), replace(c, hidden_excluded=True))
    assert v["state"] == CI.METHOD_INPUT_INCOMPLETE                        # unresolved is never "hidden"
