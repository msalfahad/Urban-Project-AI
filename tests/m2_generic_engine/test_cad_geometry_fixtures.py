"""M2 CAD geometry hardening: hand-made DXFs with HAND-DERIVED truth through the generic intake (tools/urban_intake).

Each fixture states its truth from plane geometry, not from a run of the engine:
    bulge 1 between (0,0) and (2,0)            -> semicircle, centre (1,0), r 1, length pi
    block arc 0-90 deg r 1 at (1,0), INSERT xscale -1 at the origin -> centre (-1,0), sweep reversed, length pi/2
    ARC centre (2,0) r 1 with extrusion (0,0,-1)  -> WCS centre (-2,0) (OCS x flips under -Z)
    line (0,0)-(1,0) in block A, A in block B, B inserted at (10,0) rotated 90 -> WCS (10,0)-(10,1)
    MINSERT 2 columns x 3 rows, spacing 5 / 7    -> 6 copies, 6 distinct source ids
    ELLIPSE major (2,0) ratio 0.5                -> axis u (2,0), |v| = 1
    layer-0 block child inserted on S-COL        -> segments on S-COL (inherited), keyed by the kernel's decimal id
"""

from __future__ import annotations

import math

import pytest

ezdxf = pytest.importorskip("ezdxf")

from tools import urban_intake as UI          # noqa: E402


def _save(doc, tmp_path, name):
    p = tmp_path / f"{name}.dxf"
    doc.saveas(p)
    return UI.read(p)


def _arc_len(a):
    return UI.arc_length(a)


def test_bulge_semicircle(tmp_path):
    doc = ezdxf.new("R2018")
    doc.modelspace().add_lwpolyline([(0, 0, 0, 0, 1.0), (2, 0)], format="xyseb", dxfattribs={"layer": "L"})
    I = _save(doc, tmp_path, "bulge")
    assert len(I["arcs"]) == 1
    a = I["arcs"][0]
    assert a["c"][0] == pytest.approx(1.0, abs=1e-9) and a["c"][1] == pytest.approx(0.0, abs=1e-9)
    assert a["r"] == pytest.approx(1.0, abs=1e-9)
    assert _arc_len(a) == pytest.approx(math.pi, rel=1e-9)


def test_mirrored_insert_arc(tmp_path):
    doc = ezdxf.new("R2018")
    blk = doc.blocks.new("ARCBLK")
    blk.add_arc((1, 0), 1.0, 0, 90, dxfattribs={"layer": "0"})
    ins = doc.modelspace().add_blockref("ARCBLK", (0, 0), dxfattribs={"layer": "S-BEAM"})
    ins.dxf.xscale = -1.0
    I = _save(doc, tmp_path, "mirror")
    assert len(I["arcs"]) == 1
    a = I["arcs"][0]
    assert a["c"][0] == pytest.approx(-1.0, abs=1e-9) and a["c"][1] == pytest.approx(0.0, abs=1e-9)
    assert _arc_len(a) == pytest.approx(math.pi / 2, rel=1e-9)
    # block arc runs (2,0) -> (1,1) counter-clockwise; mirrored it runs (-2,0) -> (-1,1), now clockwise
    pts = {tuple(round(v, 9) for v in a["s"]), tuple(round(v, 9) for v in a["e"])}
    assert pts == {(-2.0, 0.0), (-1.0, 1.0)}
    assert a["layer"] == "S-BEAM"                                       # layer-0 child inherits the insert's layer


def test_ocs_extrusion_arc(tmp_path):
    doc = ezdxf.new("R2018")
    doc.modelspace().add_arc((2, 0), 1.0, 0, 180, dxfattribs={"layer": "L", "extrusion": (0, 0, -1)})
    I = _save(doc, tmp_path, "ocs")
    a = I["arcs"][0]
    assert a["c"][0] == pytest.approx(-2.0, abs=1e-9) and a["c"][1] == pytest.approx(0.0, abs=1e-9)
    assert _arc_len(a) == pytest.approx(math.pi, rel=1e-9)


def test_nested_rotated_blocks(tmp_path):
    doc = ezdxf.new("R2018")
    A = doc.blocks.new("A")
    A.add_line((0, 0), (1, 0), dxfattribs={"layer": "0"})
    B = doc.blocks.new("B")
    B.add_blockref("A", (0, 0), dxfattribs={"layer": "0"})
    doc.modelspace().add_blockref("B", (10, 0), dxfattribs={"layer": "S-COL", "rotation": 90})
    I = _save(doc, tmp_path, "nested")
    assert len(I["segments"]) == 1
    s = I["segments"][0]
    got = {tuple(round(v, 9) for v in s["a"]), tuple(round(v, 9) for v in s["b"])}
    assert got == {(10.0, 0.0), (10.0, 1.0)}
    assert s["layer"] == "S-COL" and len(s["path"]) == 2


def test_minsert_copies_are_distinct(tmp_path):
    doc = ezdxf.new("R2018")
    blk = doc.blocks.new("SQ")
    blk.add_lwpolyline([(0, 0), (1, 0), (1, 1), (0, 1)], close=True, dxfattribs={"layer": "0"})
    m = doc.modelspace().add_blockref("SQ", (0, 0), dxfattribs={"layer": "S-COL"})
    m.grid(size=(3, 2), spacing=(7, 5))                                  # 3 rows x 2 columns
    I = _save(doc, tmp_path, "minsert")
    assert len(I["segments"]) == 6 * 4
    assert len({s["id"] for s in I["segments"]}) == 24
    xs = sorted({round(min(s["a"][0], s["b"][0]), 6) for s in I["segments"]})
    ys = sorted({round(min(s["a"][1], s["b"][1]), 6) for s in I["segments"]})
    assert xs[0] == 0.0 and 5.0 in xs and ys[0] == 0.0 and 7.0 in ys and 14.0 in ys


def test_ellipse_axes(tmp_path):
    doc = ezdxf.new("R2018")
    doc.modelspace().add_ellipse((0, 0), major_axis=(2, 0), ratio=0.5, dxfattribs={"layer": "L"})
    I = _save(doc, tmp_path, "ellipse")
    e = I["ellipses"][0]
    assert tuple(round(v, 9) for v in e["u"][:2]) == (2.0, 0.0)
    assert math.hypot(*e["v"][:2]) == pytest.approx(1.0, abs=1e-9)


def test_layer_inheritance_uses_decimal_ids(tmp_path):
    """Regression (M2 defect set): the kernel's instance-path ids are DECIMAL; keying the insert layers by the hex
    handle looked up an unrelated entity once a hex handle read as another entity's decimal id."""
    doc = ezdxf.new("R2018")
    blk = doc.blocks.new("COL")
    blk.add_lwpolyline([(0, 0), (1, 0), (1, 1), (0, 1)], close=True, dxfattribs={"layer": "0"})
    msp = doc.modelspace()
    for k in range(40):                                                  # enough handles for hex / decimal overlap
        msp.add_blockref("COL", (k * 3, 0), dxfattribs={"layer": "S-COL"})
        msp.add_line((k * 3, 10), (k * 3 + 1, 10), dxfattribs={"layer": "S-DIM"})
        msp.add_blockref("COL", (k * 3, 20), dxfattribs={"layer": "S-DIM"}).dxf.xscale = 0.5
    I = _save(doc, tmp_path, "inherit")
    col = [s for s in I["segments"] if s["path"] and s["a"][1] < 5]
    assert col and all(s["layer"] == "S-COL" for s in col)
    keys = UI._insert_layers(ezdxf.readfile(tmp_path / "inherit.dxf"))
    assert all(k.split(":")[1].isdigit() for k in keys)
