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


def test_adverse_frame_drawn_over_masonry_is_unresolved_with_a_bound():
    # R-T581-1 (2) 1.1.0: the 1.00 frame drawn 47 mm into the masonry on the left and 53 mm on the right (wall ends
    # 47 / 947 on both faces): a 1.00 frame cannot sit in a 0.90 gap. Neither 0.90 (wall ends) nor 1.00 (symbol) is
    # chosen: UNRESOLVED, width held (never 0), bound 0.90 .. 1.00 -> lintel 1.20 .. 1.50 (0.90 + 0.30 = 1.20 -> 1.20;
    # 1.00 + 0.30 = 1.30 -> 1.50)
    e = W.wall_ends(faces(47, 947), FR)
    assert e["state"] == W.UNRESOLVED and e["gap_mm"] is None and e["conflict"] == W.CONFLICT
    assert e["drawn_gap_mm"] == 900 and e["bound_mm"] == [900, 1000]
    assert W.classify(FR, e) == "INSIDE_FOOTPRINT"
    assert W.masonry_width({"id": "Z", "basis": W.MASONRY, "gap_mm": e["gap_mm"], "state": e["state"]}) is None
    assert [L.piece(x / 1000)["piece_m"] for x in e["bound_mm"]] == [1.2, 1.5]


def test_one_end_inside_the_footprint_is_unresolved_too():
    # the block overlaps the masonry by 120 mm on the right only: gap 1.00 = frame, but the frame is not in the gap
    e = W.wall_ends(faces(-120, 880), FR)
    assert e["state"] == W.UNRESOLVED and e["drawn_gap_mm"] == 1000 and W.classify(FR, e) == "INSIDE_FOOTPRINT"


def test_wall_end_within_tolerance_of_the_edge_is_not_a_conflict():
    # 3 mm inside the edge (draughting tolerance 5 mm): DRAWING-CONFIRMED 0.997 (cf. a 0.797 D315 read)
    e = W.wall_ends(faces(3, 1000), FR)
    assert e["state"] == W.CONFIRMED and e["gap_mm"] == 997 and W.classify(FR, e) == "AT_BLOCK_EDGES"


def test_wall_ends_outside_the_block_are_the_opening():
    # the masonry gap 1.10 is wider than the 1.00 symbol (the frame fits inside it): the wall ends are the opening
    e = W.wall_ends(faces(-50, 1050), FR)
    assert e["state"] == W.CONFIRMED and e["gap_mm"] == 1100 and W.classify(FR, e) == "SHIFTED"


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


def test_restate_holds_a_conflict_by_name_with_low_and_high_tables():
    # Z-D1 frame drawn over masonry: bound 0.90 .. 1.00 -> 1.20 .. 1.50. Held table: Z-D1 named in no_width;
    # low table = old (Z-D1 1.20), high table Z-D1 1.50: GF 1.20 -1, 1.50 +1, +0.30 lm; the census AT_MOST
    # (0.90 -> 1.20, 0.80 -> 1.20, 1.00 -> 1.50, 2.40 -> 3.00 = 6.90 lm) is no longer an upper bound (7.20 > 6.90)
    meas = {"Z-D1": {"basis": W.MASONRY, "gap_mm": None, "state": W.UNRESOLVED, "bound_mm": [900.0, 1000.0]},
            "Z-D2": {"basis": W.MASONRY, "gap_mm": 800.0, "state": W.CONFIRMED}}
    r = W.restate(_census(), meas, ["GF", "1F"])
    assert r["after"]["no_width"] == ["Z-D1"] and r["after"]["total_at_most_nr"] == 3
    assert r["held_bound"]["Z-D1"] == {"bound_m": [0.9, 1.0], "lintel_bound_m": [1.2, 1.5]}
    assert r["table_low"]["total_at_most_nr"] == r["table_high"]["total_at_most_nr"] == 4
    assert r["table_low"]["at_most"][1.2]["GF"] == 2 and r["table_high"]["at_most"][1.2]["GF"] == 1
    assert r["table_high"]["at_most"][1.5]["GF"] == 1
    assert r["census_at_most_lm"] == pytest.approx(6.9)
    assert r["lm_low"] == pytest.approx(6.9) and r["lm_high"] == pytest.approx(7.2)
    assert r["census_at_most_is_upper_bound"] is False


def test_restate_bound_in_metres_refused():
    meas = {"Z-D1": {"basis": W.MASONRY, "gap_mm": None, "state": W.UNRESOLVED, "bound_mm": [0.9, 1.0]}}
    with pytest.raises(W.BasisError, match="units"):
        W.restate(_census(), meas, ["GF", "1F"])


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
    assert o["frame_x0_mm"] == 0 and o["frame_x1_mm"] == 1000
    assert o["wall_ends"]["drawn_gap_mm"] == pytest.approx(900.0, abs=0.2)
    assert o["wall_ends"]["state"] == W.UNRESOLVED and o["ends_sit"] == "INSIDE_FOOTPRINT"


@pytest.mark.parametrize("mirrored,rot", [(False, 0.0), (True, 225.0)])
def test_dxf_reader_ends_at_block_edges_confirmed(tmp_path, mirrored, rot):
    o = W.measure_dxf(_dxf(tmp_path, mirrored=mirrored, rot=rot), "WALL")[0]
    assert o["wall_ends"]["state"] == W.CONFIRMED and o["wall_ends"]["gap_mm"] == pytest.approx(1000.0, abs=0.2)


def test_dxf_block_in_metres_refused(tmp_path):
    with pytest.raises(W.BasisError, match="units"):
        W.measure_dxf(_dxf(tmp_path, scale=0.001), "WALL")
