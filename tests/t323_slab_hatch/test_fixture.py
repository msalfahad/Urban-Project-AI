"""T-323 hand fixture (NOT Alsenan): villa T323-H, one 3.00 x 4.00 m roof-slab panel framed by 0.20 m beams on all
four sides, with a 'Sunken slab.' hatch that the drafter stopped at two annotations:

  - a slab-tag circle r 0.50 centred on the panel's north-east corner (3.00, 4.00): the hatch follows the quarter arc;
  - a bar-label text frame 0.80 x 0.30 (x 1.00 .. 1.80, y -0.10 .. 0.20) crossing the south edge: the hatch steps
    round it (a 0.80 x 0.20 notch).

Hand figures (by hand, before the code):
  panel (between beam faces)  A = 3.00 x 4.00 = 12.0000 m2, P = 2 x (3 + 4) = 14.0000 m
  hatch region                A = 12 - 0.80 x 0.20 - pi x 0.50^2 / 4 = 12 - 0.16 - 0.196350 = 11.643650 m2
                              P = 1.00 + (0.20 + 0.80 + 0.20) + 1.20 + 3.50 + pi x 0.50 / 2 + 2.50 + 4.00
                                = 13.400 + 0.785398 = 14.185398 m
  edge classes                MEMBER_FACE = 1.00 + 1.20 + 3.50 + 2.50 + 4.00 = 12.2000 m
                              ANNOTATION_CUT = 1.20 (frame) + 0.785398 (circle) = 1.985398 m
  residual panel - hatch      0.356350 m2 = 0.160000 under the frame + 0.196350 under the circle; other 0.0000
A panel quantity taken from the hatch would understate the slab by 0.3564 m2 (-2.97 %) and add 1.985 m of 'edge'.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest
from shapely.affinity import rotate, scale
from shapely.geometry import LineString, Point, Polygon, box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t323"))
import slab_hatch_edges as E  # noqa: E402

N_ARC = 512


def hatch_loop():
    arc = [(3 + 0.5 * math.cos(math.radians(270 - 90 * i / N_ARC)), 4 + 0.5 * math.sin(math.radians(270 - 90 * i / N_ARC)))
           for i in range(N_ARC + 1)]                         # (3, 3.5) -> (2.5, 4) round the corner, inside the panel
    return [(0, 0), (1.0, 0), (1.0, 0.2), (1.8, 0.2), (1.8, 0), (3, 0)] + arc + [(0, 4)]


PANEL = box(0, 0, 3, 4)
BEAMS = [box(-0.2, -0.2, 3.2, 0), box(-0.2, 4, 3.2, 4.2), box(-0.2, 0, 0, 4), box(3, 0, 3.2, 4)]
MEMBER_LINES = [list(PANEL.exterior.coords)] + [list(b.exterior.coords) for b in BEAMS]
CIRCLE = ("tag circle r 0.50", Point(3, 4).buffer(0.5, 256))
FRAME = ("bar label frame", box(1.0, -0.1, 1.8, 0.2))
ANNS = [CIRCLE, FRAME]
QUARTER = math.pi * 0.25 / 4


def classify(loop=None, members=MEMBER_LINES, anns=ANNS, frees=()):
    return E.classify_boundary([loop or hatch_loop()], member_lines=members, free_lines=frees, annotations=anns)


def test_hatch_region_and_edge_classes_by_hand():
    c = classify()
    assert c.region.area == pytest.approx(12 - 0.16 - QUARTER, abs=2e-5)
    assert c.perimeter == pytest.approx(13.4 + math.pi * 0.5 / 2, abs=1e-5)
    assert c.lengths["MEMBER_FACE"] == pytest.approx(12.2, abs=1e-6)
    assert c.lengths["ANNOTATION_CUT"] == pytest.approx(1.2 + math.pi * 0.5 / 2, abs=1e-5)
    assert c.lengths["FREE_EDGE"] == 0 and c.lengths["UNEXPLAINED"] == 0
    assert c.annotations_hit["bar label frame"] == pytest.approx(1.2, abs=1e-6)
    assert c.annotations_hit["tag circle r 0.50"] == pytest.approx(math.pi * 0.5 / 2, abs=1e-5)
    assert not c.is_panel_outline


def test_panel_rebuilt_from_member_faces_residual_named():
    c = classify()
    r = E.rebuild_panel(c, [PANEL] + BEAMS, annotations=ANNS)
    assert r["status"] == "DRAWING-CONFIRMED" and r["faces"] == 1
    assert r["area_m2"] == pytest.approx(12.0) and r["perimeter_m"] == pytest.approx(14.0)
    assert r["residual_m2"] == pytest.approx(0.16 + QUARTER, abs=2e-5)
    assert r["residual_annotation_m2"]["bar label frame"] == pytest.approx(0.16, abs=1e-9)
    assert r["residual_annotation_m2"]["tag circle r 0.50"] == pytest.approx(QUARTER, abs=2e-5)
    assert r["residual_annotation_net_m2"] == pytest.approx(0.16 + QUARTER, abs=2e-5)
    assert r["residual_other_m2"] == pytest.approx(0.0, abs=1e-9)
    assert r["outside_panel_m2"] == pytest.approx(0.0, abs=1e-9)


def test_hatch_equal_to_panel_is_a_panel_outline():
    c = classify(loop=list(PANEL.exterior.coords)[:-1])
    assert c.is_panel_outline and c.lengths["MEMBER_FACE"] == pytest.approx(14.0)
    r = E.rebuild_panel(c, [PANEL] + BEAMS, annotations=ANNS)
    assert r["residual_m2"] == pytest.approx(0.0, abs=1e-12)


def test_notch_redrawn_off_the_member_face_inside_an_annotation_is_named_both_ways():
    """The development-villa case in miniature: inside the tag circle the drafter redraws a column notch 0.05 m off
    the column outline. Panel (with the true 0.25 x 0.25 column notch at the NE corner) vs hatch notch shifted 0.05 m
    south: +0.25 x 0.05 not hatched, -0.25 x 0.05 hatched over the column, net 0, both inside the circle."""
    col = box(2.75, 3.75, 3.0, 4.0)
    panel = PANEL.difference(col)
    hatch = PANEL.difference(box(2.75, 3.70, 3.0, 3.95))          # notch drawn 0.05 m south of the column
    c = E.classify_boundary([list(hatch.exterior.coords)[:-1]], member_lines=MEMBER_LINES + [list(col.exterior.coords)],
                            annotations=[CIRCLE])
    r = E.rebuild_panel(c, [panel, col] + BEAMS, annotations=[CIRCLE])
    assert r["area_m2"] == pytest.approx(12 - 0.0625)
    assert r["residual_annotation_m2"]["tag circle r 0.50"] == pytest.approx(0.25 * 0.05, abs=1e-9)
    assert r["outside_annotation_m2"]["tag circle r 0.50"] == pytest.approx(0.25 * 0.05, abs=1e-9)
    assert r["residual_other_m2"] == pytest.approx(0.0, abs=1e-9)
    assert c.lengths["ANNOTATION_CUT"] > 0


# ------------------------------------------------------------------------------------------------- adverse cases
def test_annotation_edge_as_free_edge_refused():
    c = classify()
    with pytest.raises(E.HatchEdgeError, match="not slab edges"):
        E.free_edge_length(c, ["FREE_EDGE", "ANNOTATION_CUT"])
    with pytest.raises(E.HatchEdgeError, match="not slab edges"):
        E.free_edge_length(c, ["UNEXPLAINED"])
    with pytest.raises(E.HatchEdgeError, match="member faces carry no step concrete"):
        E.free_edge_length(c, ["MEMBER_FACE"])


def test_one_free_slab_edge_counts_only_its_drawn_length():
    """East beam removed: the east edge is a drawn free slab edge; the 0.50 m of it under the tag circle stays an
    annotation cut, so the free edge is 3.50 m, not 4.00 m and not the arc."""
    members = [list(b.exterior.coords) for b in BEAMS[:3]] + [[(0, 0), (3, 0)], [(3, 4), (0, 4)], [(0, 4), (0, 0)]]
    c = classify(members=members, frees=[[(3, 0), (3, 4)]])
    assert c.lengths["FREE_EDGE"] == pytest.approx(3.5, abs=1e-6)
    assert E.free_edge_length(c, ["FREE_EDGE"]) == pytest.approx(3.5, abs=1e-6)
    assert c.lengths["ANNOTATION_CUT"] == pytest.approx(1.2 + math.pi * 0.25, abs=1e-5)


def test_panel_left_open_is_held_never_the_hatch_area_never_zero():
    c = classify()
    r = E.rebuild_panel(c, BEAMS, annotations=ANNS)          # no face between the beams was polygonised
    assert r["status"] == "HELD" and r["area_m2"] is None and r["residual_m2"] is None
    assert "left open" in r["why"]


def test_hatch_marking_a_portion_of_a_face_is_held_as_a_portion():
    """A 'cantilever portion' hatch over the outer 1.50 m of a 0.50 x 5.75 m beam band: not a panel."""
    band = box(0, 0, 5.75, 0.5)
    c = E.classify_boundary([[(4.25, 0), (5.75, 0), (5.75, 0.5), (4.25, 0.5)]],
                            member_lines=[list(band.exterior.coords)], annotations=[("bar line", LineString(
                                [(4.25, -0.3), (4.25, 0.8)]).buffer(0.005))])
    assert c.lengths["ANNOTATION_CUT"] == pytest.approx(0.5, abs=1e-6)
    r = E.rebuild_panel(c, [band])
    assert r["status"] == "HELD" and "PORTION" in r["why"] and r["host_faces"][0][1] == pytest.approx(0.75)


def test_unexplained_edge_is_reported_not_absorbed():
    loop = [(0, 0), (3, 0), (3, 4), (0, 4), (0, 2.2), (0.3, 2.0), (0, 1.8)]     # a bite with nothing drawn there
    c = classify(loop=loop, anns=[])
    assert c.lengths["UNEXPLAINED"] > 0.5 and not c.is_panel_outline


def test_millimetres_refused():
    with pytest.raises(E.HatchEdgeError, match="not metres"):
        classify(loop=[(x * 1000, y * 1000) for x, y in hatch_loop()])


@pytest.mark.parametrize("how", ["mirror", "rotate90"])
def test_mirror_and_rotation_invariant(how):
    def tf(g):
        return scale(g, -1, 1, origin=(0, 0)) if how == "mirror" else rotate(g, 90, origin=(0, 0))
    loop = list(tf(Polygon(hatch_loop())).exterior.coords)[:-1]
    members = [list(tf(LineString(m)).coords) for m in MEMBER_LINES]
    anns = [(lab, tf(g)) for lab, g in ANNS]
    c = E.classify_boundary([loop], member_lines=members, annotations=anns)
    assert c.lengths["MEMBER_FACE"] == pytest.approx(12.2, abs=1e-6)
    assert c.lengths["ANNOTATION_CUT"] == pytest.approx(1.2 + math.pi * 0.25, abs=1e-5)
    r = E.rebuild_panel(c, [tf(PANEL)] + [tf(b) for b in BEAMS], annotations=anns)
    assert r["area_m2"] == pytest.approx(12.0) and r["residual_other_m2"] == pytest.approx(0.0, abs=1e-9)


def test_two_touching_region_loops_are_one_region():
    """A hatch split by an annotation arc into two touching loops (T-213 rule b): the region is their union."""
    a = [(0, 0), (3, 0), (3, 2), (0, 2)]
    b = [(0, 2), (3, 2), (3, 4), (0, 4)]
    c = E.classify_boundary([a, b], member_lines=MEMBER_LINES)
    assert c.region_loops == 2 and c.region.area == pytest.approx(12.0) and c.is_panel_outline
