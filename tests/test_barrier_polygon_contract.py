"""The bug that made three mechanisms silently inert.

`PortalPartitionBarrier` carries a `ring`. Three consumers asked for
`.polygon` via getattr and got None, so on the real drawing:

  * no opening jamb ever entered the boundary-candidate pool,
  * no portal was ever reopened in the segmentation mask,
  * every portal graded UNVALIDATED for "geometry not from source lines".

The synthetic fixtures each supplied a `.polygon` attribute, so every test
passed while the real path did nothing. These tests use the REAL class, so
the contract cannot drift again.
"""

import pytest

from engine import boundary_match as bm
from engine import raster_topology as rt
from engine.free_space import PortalPartitionBarrier
from engine.space_objects import SRC_VECTOR_OPENING_JAMB


def _barrier(axis="H", jamb_a=1000.0, jamb_b=1900.0, fixed=0.0,
             thickness=200.0):
    if axis == "H":
        ring = ((jamb_a, fixed), (jamb_b, fixed),
                (jamb_b, fixed + thickness), (jamb_a, fixed + thickness))
    else:
        ring = ((fixed, jamb_a), (fixed + thickness, jamb_a),
                (fixed + thickness, jamb_b), (fixed, jamb_b))
    return PortalPartitionBarrier(
        portal_id="PT-1", ring=ring, host_wall_band_id="WB-0001",
        jamb_a_mm=jamb_a, jamb_b_mm=jamb_b, axis=axis,
        closure_basis="CLEAR_INTERNAL_FINISH_FACE",
        existence_status="PORTAL_EXISTENCE_PROBABLE",
        geometry_status="GEOMETRY_CANDIDATE",
        existence_evidence=("OPENING_GAP", "END_CAP_AT_JAMB"))


def test_the_real_barrier_exposes_a_polygon():
    got = _barrier().polygon
    assert got is not None
    assert got.bounds == (1000.0, 0.0, 1900.0, 200.0)


def test_an_empty_ring_has_no_polygon():
    got = PortalPartitionBarrier(
        portal_id="PT-2", ring=(), host_wall_band_id="",
        jamb_a_mm=0.0, jamb_b_mm=0.0, axis="H", closure_basis="",
        existence_status="", geometry_status="")
    assert got.polygon is None


def test_the_real_barrier_yields_jamb_candidates():
    """The candidate class that was silently always empty."""
    got = bm.candidates_from_portals([_barrier()])
    assert len(got) == 2, "no jamb candidates from a real barrier"
    assert {c.source_type for c in got} == {SRC_VECTOR_OPENING_JAMB}
    assert {c.axis for c in got} == {"H"}
    assert {round(c.fixed_mm) for c in got} == {0, 200}


def test_a_vertical_barrier_yields_vertical_jambs():
    got = bm.candidates_from_portals([_barrier(axis="V")])
    assert {c.axis for c in got} == {"V"}
    assert {round(c.fixed_mm) for c in got} == {0, 200}


def test_the_real_barrier_reopens_pixels_in_the_mask():
    """"Portals stay passable" has to fire on the real object."""
    import numpy as np
    from shapely.geometry import box

    from engine.frames import IDENTITY, Frame

    class _Seg:
        def __init__(self, mask):
            self.wall_mask, self.px_mm = mask, 10.0
            self.dpi, self.ink_threshold = 300, 200
            self.source_path, self.source_sha256 = "synthetic", "0" * 64

    ink = np.zeros((120, 160), bool)
    ink[10:110, 79:82] = True          # one dividing wall, no door
    ink[9:11, 9:151] = True
    ink[109:111, 9:151] = True
    ink[9:111, 9:11] = True
    ink[9:111, 149:151] = True
    seg = _Seg(ink)
    frame = Frame(IDENTITY, raster_w_mm=160 * 10.0, raster_h_mm=120 * 10.0,
                  fit=1.0)

    closed = rt.build(seg, frame, min_region_m2=0.5)
    assert len(closed.regions) == 2

    door = PortalPartitionBarrier(
        portal_id="PT-D",
        ring=((780.0, 500.0), (830.0, 500.0), (830.0, 590.0),
              (780.0, 590.0)),
        host_wall_band_id="WB-1", jamb_a_mm=500.0, jamb_b_mm=590.0,
        axis="V", closure_basis="", existence_status="",
        geometry_status="")
    passable = rt.build(seg, frame, portal_barriers=[door],
                        min_region_m2=0.5)
    assert passable.provenance["portal_pixels_reopened"] > 0
    assert len(passable.regions) == 1, (
        "the doorway did not reopen: the two rooms stayed separate")
