"""T-392 rules on a hand-made villa T392-K (not Alsenan; every figure calculated by hand below).

(1) R-T392-1, ring tangent to a beam: ring inner R 1.00, outer R 1.20 about the origin, closed on the west by the east
    face of beam BW (0.20 wide, x -1.20 .. -1.00, y -2 .. 2): the beam's cell touches the ring only at the tangent
    point, drawn overlap 0. A ledger that deducted 0.0015 m2 x 0.75 from BW = GAP 0.001125 m3 (named). Normal case: a
    beam BX whose east face is at x -0.95 overlaps the ring's inner disc boundary; its drawn overlap with the ring is
    measured, a deduction of exactly that area is COUNTED_ONCE.
(2) R-T392-2, band end across an oblique face: band 0.30 wide (y 0 .. 0.30), x 0 .. 3.00, depth 0.75; carrier face
    through (3.15, 0) and (2.95, 0.30): it crosses x 3.00 at y 0.225. Cell to the face = 0.30 x (3.15 + 2.95) / 2 =
    0.915 m2; band 0.900; beyond the face (y 0.225 .. 0.30) 0.075 x 0.05 / 2 = 0.001875; short of the face (y 0 ..
    0.225) 0.225 x 0.15 / 2 = 0.016875; 0.900 - 0.001875 + 0.016875 = 0.915. A column holds 0.010 of the short part:
    DOUBLE 0.001875 x 0.75 = 0.00140625, GAP 0.006875 x 0.75 = 0.00515625, never netted.
(3) R-T392-3: line pair 6.00 m along a tank side 4.00 m, 1.10 m before and 0.90 m after: outside 2.00 m, owner the
    boundary wall (one HELD concrete line, masonry MISSING).
(4) R-T392-4: member 1.000 m2 in pieces 0.600 (0.200 uncovered) and 0.400 (0.100 uncovered), depth 0.75: located
    0.150 + 0.075 = 0.225 m3.
"""

import math
import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import Point, box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t392"))
import t392_rules as R  # noqa: E402


def ring_and_beam(east_face):
    ring = Point(0, 0).buffer(1.20, 4096).difference(Point(0, 0).buffer(1.00, 4096))
    ring = ring.intersection(box(-1.00, -2, 2, 2))            # closed by the BW face x = -1.00
    beam = box(east_face - 0.20, -2, east_face, 2)
    return ring, beam


def test_tangent_beam_deduction_is_a_named_gap():
    ring, beam = ring_and_beam(-1.00)
    ov = ring.intersection(beam).area
    assert ov == pytest.approx(0.0, abs=1e-9)
    res = R.overlap_deduction(0.0015, ov, 0.75, "ledger Z: sliver against ring")
    assert res == {"status": "GAP", "m3": pytest.approx(0.001125), "name": "ledger Z: sliver against ring"}


def test_real_overlap_deducted_once_and_invariant_under_mirror_and_rotation():
    ring = Point(0, 0).buffer(1.20, 4096).difference(Point(0, 0).buffer(1.00, 4096))
    beam = box(-1.15, -2, -0.95, 2)                          # crosses the ring's west part
    ov = ring.intersection(beam).area
    # hand bound: the strip x -1.15 .. -0.95 cuts the annulus in two lens-like pieces, about 2 x 0.20 x 0.60
    assert 0.15 < ov < 0.35
    assert R.overlap_deduction(ov, ov, 0.75, "ledger Z")["status"] == "COUNTED_ONCE"
    for f in (lambda g: affinity.scale(g, -1, 1, origin=(0, 0)), lambda g: affinity.rotate(g, 90, origin=(0, 0))):
        assert f(ring).intersection(f(beam)).area == pytest.approx(ov, rel=1e-6)   # mirror / rotation invariant
    # deducting less than the drawn overlap leaves a DOUBLE of the difference
    assert R.overlap_deduction(ov - 0.01, ov, 0.75, "ledger Z") == {"status": "DOUBLE", "m3": pytest.approx(0.0075),
                                                                  "name": "ledger Z"}


def test_overlap_deduction_adverse_inputs_refused():
    with pytest.raises(R.Refused, match="UNNAMED"):
        R.overlap_deduction(0.0015, 0.0, 0.75, "")
    with pytest.raises(R.Refused, match="UNITS"):
        R.overlap_deduction(1500.0, 0.0, 0.75, "x")            # mm2 given as m2
    with pytest.raises(R.Refused, match="UNITS"):
        R.overlap_deduction(0.0015, 0.0, 750, "x")             # depth in mm
    with pytest.raises(R.Refused, match="MISSING"):
        R.overlap_deduction(0.0015, None, 0.75, "x")            # unknown overlap is never 0


def test_band_end_across_oblique_face_double_and_gap_apart():
    face = [(3.15, 0.0), (2.95, 0.30)]
    from shapely.geometry import Polygon
    cell = Polygon([(0, 0), face[0], face[1], (0, 0.30)])
    band = box(0, 0, 3.00, 0.30)
    beyond, short = band.difference(cell).area, cell.difference(band).area
    assert cell.area == pytest.approx(0.915) and beyond == pytest.approx(0.001875) and short == pytest.approx(0.016875)
    res = R.band_end_vs_face(band.area, cell.area, beyond, short, 0.010, 0.75)
    assert res["double_m3"] == pytest.approx(0.00140625, abs=1e-6)       # rule reports m3 to 6 dp
    assert res["gap_m3"] == pytest.approx(0.00515625, abs=1e-6)
    assert res["status"] == "BOTH"
    # mirrored member (carrier on the west end) gives the same figures
    m = affinity.scale(cell, -1, 1, origin=(0, 0))
    mb = affinity.scale(band, -1, 1, origin=(0, 0))
    assert mb.difference(m).area == pytest.approx(beyond) and m.difference(mb).area == pytest.approx(short)


def test_band_end_adverse_refused():
    with pytest.raises(R.Refused, match="NOT_CLOSED"):
        R.band_end_vs_face(0.900, 0.915, 0.001875, 0.010, 0.0, 0.75)
    with pytest.raises(R.Refused, match="OWNED_EXCEEDS_SHORT"):
        R.band_end_vs_face(0.900, 0.915, 0.001875, 0.016875, 0.02, 0.75)
    with pytest.raises(R.Refused, match="MISSING"):
        R.band_end_vs_face(0.900, None, 0.001875, 0.016875, 0.0, 0.75)


def test_split_side_outside_part_owned_by_the_boundary_wall():
    owner = {"element": "boundary wall", "lines": [{"sheet": "ground-beam plan", "line_id": "L-x", "status": "HELD"},
                                                   {"sheet": "plan above ground", "line_id": None}]}
    res = R.split_side(6.00, 4.00, 1.10, 0.90, owner)
    assert res["outside_m"] == pytest.approx(2.00) and res["inside_m"] == 4.00
    assert [x["state"] for x in res["lines"]] == ["HELD", "MISSING"]


def test_split_side_adverse_refused():
    owner = {"element": "boundary wall", "lines": [{"sheet": "s", "line_id": "L-x"}]}
    with pytest.raises(R.Refused, match="TANK_OWNS_OUTSIDE"):
        R.split_side(6.00, 4.00, 1.10, 0.90, {"element": "pool wall", "lines": [{"sheet": "s", "line_id": "L-p"}]})
    with pytest.raises(R.Refused, match="NOT_CLOSED"):
        R.split_side(6.00, 4.00, 1.10, 0.80, owner)
    with pytest.raises(R.Refused, match="NO_LINE_STATED"):
        R.split_side(6.00, 4.00, 1.10, 0.90, {"element": "boundary wall", "lines": []})
    with pytest.raises(R.Refused, match="UNITS"):
        R.split_side(6000, 4000, 1100, 900, owner)


def test_locate_residual_per_piece_and_recheck():
    res = R.locate_residual(1.000, [(0.600, 0.200), (0.400, 0.100)], 0.75)
    assert res["status"] == "LOCATED" and res["located_m3"] == pytest.approx(0.225)
    assert R.locate_residual(1.000, [(0.600, 0.200), (0.400, 0.100)], 0.75, 0.001)["status"] == "RECHECK"
    with pytest.raises(R.Refused, match="PIECES_NOT_MEMBER"):
        R.locate_residual(1.000, [(0.600, 0.200)], 0.75)
