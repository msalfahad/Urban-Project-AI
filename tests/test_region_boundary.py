"""§9: a pixel blob becomes an ORDERED rectilinear ring, in drawing axes."""

import numpy as np

from engine.frames import IDENTITY, SWAP_FLIP_Y, Frame
from engine.region_boundary import BoundaryRun, simplify, trace


def _frame(name=IDENTITY, w=400.0, h=300.0):
    return Frame(name, raster_w_mm=w, raster_h_mm=h, fit=1.0)


def _rect(h=30, w=40, r0=5, r1=15, c0=8, c1=28, label=5):
    lab = np.zeros((h, w), np.int32)
    lab[r0:r1, c0:c1] = label
    return lab


def test_a_rectangle_traces_to_four_runs():
    runs = trace(_rect(), 5, _frame(), 10.0)
    assert len(runs) == 4
    assert [r.axis for r in runs] == ["H", "V", "H", "V"]


def test_the_ring_alternates_axes():
    """The polygon rebuild depends on it: run i gives one corner ordinate."""
    lab = np.zeros((40, 40), np.int32)
    lab[5:35, 5:20] = 3
    lab[5:15, 20:35] = 3
    runs = simplify(trace(lab, 3, _frame(w=400.0, h=400.0), 10.0))
    for a, b in zip(runs, runs[1:] + runs[:1]):
        assert a.axis != b.axis


def test_an_l_shape_traces_to_six_runs():
    lab = np.zeros((40, 40), np.int32)
    lab[5:35, 5:20] = 3
    lab[5:15, 20:35] = 3
    runs = simplify(trace(lab, 3, _frame(w=400.0, h=400.0), 10.0))
    assert len(runs) == 6


def test_the_axis_is_read_in_DRAWING_space_not_pixel_space():
    """SWAP_FLIP_Y: vector-x follows pixel-y, so the axes swap.

    Assuming the pixel direction is the drawing direction is the mistake
    that made an earlier leak map report 27 of 30 frontiers as having no
    vector separator.
    """
    lab = _rect()
    ident = trace(lab, 5, _frame(IDENTITY), 10.0)
    swapped = trace(lab, 5, _frame(SWAP_FLIP_Y), 10.0)
    assert [r.axis for r in ident] == ["H", "V", "H", "V"]
    assert [r.axis for r in swapped] == ["V", "H", "V", "H"]
    # The long pixel side (20 px) is 200 mm either way — but on a
    # different drawing axis.
    assert max(r.length_mm for r in ident) == 200.0
    assert max(r.length_mm for r in swapped) == 200.0


def test_coordinates_are_named_approximate_and_forbidden_for_release():
    rec = trace(_rect(), 5, _frame(), 10.0)[0].record()
    assert "APPROXIMATE_fixed_mm" in rec
    assert "fixed_mm" not in rec
    assert "SEARCH GUIDE" in rec["this_is"]
    assert "may be released" in rec["this_is"]


def test_an_empty_label_traces_to_nothing():
    assert trace(_rect(), 99, _frame(), 10.0) == []


# --- simplification -------------------------------------------------------

def test_a_staircase_jag_is_removed():
    """A one-pixel jag is a rendering artefact, not a feature."""
    lab = _rect()
    lab[7:9, 27] = 0                      # a two-pixel bite out of the side
    raw = trace(lab, 5, _frame(), 10.0, min_run_px=1)
    assert len(raw) > 4
    got = simplify(raw, min_run_mm=100.0)
    assert len(got) == 4, [r.record() for r in got]


def test_simplification_keeps_a_real_feature():
    """A 900 mm doorway-sized step survives; a 20 mm jag does not."""
    lab = np.zeros((40, 60), np.int32)
    lab[5:35, 5:50] = 4
    lab[5:14, 40:50] = 0                  # a 9 x 10 px (90 x 100 mm) notch
    runs = simplify(trace(lab, 4, _frame(w=600.0, h=400.0), 100.0,
                          min_run_px=1), min_run_mm=100.0)
    assert len(runs) == 6, [r.record() for r in runs]


def test_the_dominant_line_survives_a_merge():
    """Merging keeps the longer neighbour's coordinate, not an average."""
    runs = [BoundaryRun(1, "H", 100.0, 0.0, 5000.0, 50),
            BoundaryRun(2, "V", 5000.0, 100.0, 120.0, 2),
            BoundaryRun(3, "H", 120.0, 5000.0, 5200.0, 2),
            BoundaryRun(4, "V", 5200.0, 120.0, 3000.0, 30),
            BoundaryRun(5, "H", 3000.0, 0.0, 5200.0, 52),
            BoundaryRun(6, "V", 0.0, 100.0, 3000.0, 30)]
    got = simplify(runs, min_run_mm=300.0)
    h_at_top = [r for r in got if r.axis == "H" and r.fixed_mm < 1000.0]
    assert h_at_top, [r.record() for r in got]
    # 100.0 was the long run's line; 120.0 was the jag's.
    assert h_at_top[0].fixed_mm == 100.0
