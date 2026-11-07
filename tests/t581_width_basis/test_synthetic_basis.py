"""T-581 R-T581-1 on a non-training villa (villa Z, hand-calculated) plus adverse cases."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_p = ROOT / "research" / "agents_t581" / "t581_width_basis.py"
_s = importlib.util.spec_from_file_location("t581_width_basis", _p)
W = importlib.util.module_from_spec(_s)
sys.modules["t581_width_basis"] = W
_s.loader.exec_module(W)
L = W.L

# villa Z door block 'DZ': 1000 mm overall, 50 mm frames each end, 200 mm wall, leaf from y = 200
DZ = [((0, 0), (50, 0)), ((50, 0), (50, 200)), ((0, 200), (0, 0)), ((950, 0), (1000, 0)), ((1000, 0), (1000, 200)),
      ((950, 200), (950, 0)), ((60, 200), (0, 200)), ((60, 200), (60, 1090)), ((100, 1090), (100, 200))]
FR = W.block_frame(DZ)


def faces(left, right, t=200, left_b=None, right_b=None):
    """wall-face lines on both faces stopping at left / right (block coordinates, mm)."""
    lb = left if left_b is None else left_b
    rb = right if right_b is None else right_b
    return [((-1500, 0), (left, 0), "a1"), ((right, 0), (2500, 0), "a2"),
            ((-1500, t), (lb, t), "b1"), ((rb, t), (2500, t), "b2")]


def test_block_frame_overall_and_clear():
    assert FR["overall_mm"] == 1000 and FR["frame_clear_mm"] == 900 and FR["t_mm"] == 200


def test_task_fixture_masonry_basis_gives_the_150_piece():
    # by hand: masonry 1.00 + 2 x 0.15 = 1.30 -> 1.50 piece; frame-clear 0.90 + 0.30 = 1.20 -> 1.20 piece
    e = W.wall_ends(faces(0, 1000), FR)
    assert e["state"] == W.CONFIRMED and e["gap_mm"] == 1000
    w = W.masonry_width({"id": "Z-D1", "basis": W.MASONRY, "gap_mm": e["gap_mm"], "state": e["state"]})
    assert w == 1.0
    assert L.piece(w)["piece_m"] == 1.5
    assert L.piece(FR["frame_clear_mm"] / 1000)["piece_m"] == 1.2      # the refused basis would give 1.20
    assert W.classify(FR, e) == "AT_BLOCK_EDGES"


def test_shifted_symbol_masonry_is_the_wall_ends_not_the_block():
    # block drawn 47 mm into the masonry: wall ends at 47 / 947 on both faces -> 0.90 (-> 1.20), never the 1.00 block
    e = W.wall_ends(faces(47, 947), FR)
    assert e["gap_mm"] == 900 and W.classify(FR, e) == "AT_FRAME_LINE"
    assert L.piece(e["gap_mm"] / 1000)["piece_m"] == 1.2


def test_shifted_beyond_frame_is_shifted():
    e = W.wall_ends(faces(-120, 880), FR)
    assert e["gap_mm"] == 1000 and W.classify(FR, e) == "SHIFTED"


def test_faces_disagree_unresolved_never_block_width():
    e = W.wall_ends(faces(0, 1000, left_b=100), FR)
    assert e["state"] == W.UNRESOLVED and e["gap_mm"] is None
    assert W.masonry_width({"id": "Z", "basis": W.MASONRY, "gap_mm": None, "state": e["state"]}) is None
    assert L.piece(None)["status"] == L.HELD          # held, never 0


def test_no_wall_end_within_reach_unresolved():
    segs = [((-3000, 0), (-2000, 0), "a"), ((0, 200), (-500, 200), "b"), ((1000, 200), (1800, 200), "c")]
    assert W.wall_ends(segs, FR)["state"] == W.UNRESOLVED


def test_face_line_through_the_opening_unresolved():
    segs = faces(0, 1000) + [((-200, 0), (1200, 0), "x")]
    assert W.wall_ends(segs, FR)["state"] == W.UNRESOLVED


def test_mixed_basis_refused():
    with pytest.raises(W.BasisError, match="mixed"):
        W.check_single_basis([{"basis": W.MASONRY}, {"basis": "FRAME_CLEAR"}])


@pytest.mark.parametrize("basis", ["FRAME_CLEAR", "BLOCK_OVERALL", "LEAF_RADIUS"])
def test_other_bases_refused(basis):
    with pytest.raises(W.BasisError):
        W.masonry_width({"id": "Z", "basis": basis, "gap_mm": 890.0, "state": W.CONFIRMED})


def test_width_in_metres_refused_as_mm():
    with pytest.raises(W.BasisError, match="units"):
        W.masonry_width({"id": "Z", "basis": W.MASONRY, "gap_mm": 1.0, "state": W.CONFIRMED})


def _census():
    return [{"id": "Z-D1", "storey": "GF", "wall_class": "EXT", "width_m": 0.90, "state": L.REQUIRED},
            {"id": "Z-D2", "storey": "GF", "wall_class": "INT", "width_m": 0.80, "state": L.HELD},
            {"id": "Z-D3", "storey": "1F", "wall_class": "INT", "width_m": 1.00, "state": L.REQUIRED},
            {"id": "Z-W1", "storey": "1F", "wall_class": "EXT", "width_m": 2.40, "state": L.REQUIRED}]


def test_restate_attributes_each_change_to_an_opening():
    # Z-D1 was read frame-clear 0.90 (1.20) but its wall ends are 1.00 -> 1.50: GF 1.20 -1, 1.50 +1, +0.30 lm;
    # Z-D3 faces disagree -> UNRESOLVED: width held by name (at most drops by its 1.50, never a 0-width piece)
    meas = {"Z-D1": {"basis": W.MASONRY, "gap_mm": 1000.0, "state": W.CONFIRMED},
            "Z-D2": {"basis": W.MASONRY, "gap_mm": 800.0, "state": W.CONFIRMED},
            "Z-D3": {"basis": W.MASONRY, "gap_mm": None, "state": W.UNRESOLVED}}
    r = W.restate(_census(), meas, ["GF", "1F"])
    assert r["diff_nr"][1.2]["GF"] == -1 and r["diff_nr"][1.5]["GF"] == +1
    assert r["diff_nr"][1.5]["1F"] == -1
    assert {c["id"] for c in r["changes"]} == {"Z-D1", "Z-D3"}
    d3 = next(c for c in r["changes"] if c["id"] == "Z-D3")
    assert d3["w_new"] is None and d3["state"] == W.UNRESOLVED
    assert "Z-D3" in r["after"]["no_width"]
    assert r["diff_lm"] == pytest.approx(0.30 - 1.50)
    # Z-W1 (no frame block) is untouched: 2.40 + 0.30 = 2.70 -> 3.00
    assert r["after"]["at_most"][3.0]["1F"] == 1


def test_restate_refuses_mixed_measurements():
    meas = {"Z-D1": {"basis": W.MASONRY, "gap_mm": 1000.0, "state": W.CONFIRMED},
            "Z-D2": {"basis": "FRAME_CLEAR", "gap_mm": 700.0, "state": W.CONFIRMED}}
    with pytest.raises(W.BasisError, match="mixed"):
        W.restate(_census(), meas, ["GF", "1F"])


def _dxf(tmp_path, scale=1.0, mirrored=False, rot=90.0, shift=0.0):
    ezdxf = pytest.importorskip("ezdxf")
    from ezdxf.math import Matrix44, Vec3
    doc = ezdxf.new()
    blk = doc.blocks.new("DZ")
    for a, b in DZ:
        blk.add_line((a[0] * scale, a[1] * scale), (b[0] * scale, b[1] * scale), dxfattribs={"layer": "D"})
    msp = doc.modelspace()
    ins = msp.add_blockref("DZ", (5000, 7000), dxfattribs={"rotation": rot, "xscale": -1 if mirrored else 1})
    m = ins.matrix44() if scale == 1.0 else Matrix44()
    for (a, b, _) in faces(shift, 900 + shift if shift else 1000):
        pa, pb = m.transform(Vec3(a[0], a[1], 0)), m.transform(Vec3(b[0], b[1], 0))
        msp.add_line(pa, pb, dxfattribs={"layer": "WALL"})
    p = tmp_path / "z.dxf"
    doc.saveas(p)
    return p


@pytest.mark.parametrize("mirrored,rot", [(False, 0.0), (False, 90.0), (True, 90.0), (True, 225.0)])
def test_dxf_reader_rotation_and_mirror(tmp_path, mirrored, rot):
    out = W.measure_dxf(_dxf(tmp_path, mirrored=mirrored, rot=rot, shift=47.0), "WALL")
    assert len(out) == 1
    o = out[0]
    assert o["overall_mm"] == 1000 and o["frame_clear_mm"] == 900 and o["mirrored"] == mirrored
    assert o["wall_ends"]["gap_mm"] == pytest.approx(900.0, abs=0.2)


def test_dxf_block_in_metres_refused(tmp_path):
    with pytest.raises(W.BasisError, match="units"):
        W.measure_dxf(_dxf(tmp_path, scale=0.001), "WALL")
