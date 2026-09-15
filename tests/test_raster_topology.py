"""§4, §5: the automatic topology pipeline finds spaces and measures nothing.

Every test here builds a synthetic render whose right answer is known by
construction, so a passing test means the pipeline found the rooms someone
drew — not that it agreed with a benchmark.
"""

import numpy as np
import pytest
from shapely.geometry import box

from engine import raster_topology as rt
from engine.frames import IDENTITY, Frame


class _Seg:
    """The fields raster_topology reads off a Segmentation."""

    def __init__(self, wall_mask, px_mm=10.0):
        self.wall_mask = wall_mask
        self.px_mm = px_mm
        self.dpi = 300
        self.ink_threshold = 200
        self.source_path = "synthetic"
        self.source_sha256 = "0" * 64


class _Barrier:
    def __init__(self, polygon):
        self.polygon = polygon


def _sheet(h=120, w=160):
    """An empty sheet: all free.

    No ink border — a real render has white paper at the sheet edge, and
    that is what makes the paper identifiable as the OUTSIDE (it touches
    the border; an enclosed courtyard never does).
    """
    return np.zeros((h, w), bool)


def _frame(seg):
    h, w = seg.wall_mask.shape
    return Frame(IDENTITY, raster_w_mm=w * seg.px_mm,
                 raster_h_mm=h * seg.px_mm, fit=1.0)


def _two_rooms(gap_at=None, gap_width=0):
    """Two rooms either side of one vertical wall, optionally with a door."""
    ink = _sheet()
    ink[10:110, 79:82] = True              # the dividing wall
    if gap_at is not None:
        ink[gap_at:gap_at + gap_width, 79:82] = False
    # Outer walls of the building.
    ink[9:11, 9:151] = True
    ink[109:111, 9:151] = True
    ink[9:111, 9:11] = True
    ink[9:111, 149:151] = True
    return _Seg(ink)


# --- it finds the rooms ---------------------------------------------------

def test_one_wall_between_two_rooms_gives_two_regions():
    seg = _two_rooms()
    topo = rt.build(seg, _frame(seg), min_region_m2=0.5)
    assert len(topo.regions) == 2
    for r in topo.regions:
        assert r.approximate_area_m2 > 0.5


def test_a_door_in_the_wall_merges_the_two_rooms():
    """The image is honest about connectivity: a gap is a connection."""
    seg = _two_rooms(gap_at=50, gap_width=9)
    topo = rt.build(seg, _frame(seg), min_region_m2=0.5)
    assert len(topo.regions) == 1


def test_the_outside_is_not_a_region():
    """The paper is not a space, however much of the sheet it covers.

    Asserted on identity rather than on area: in this fixture the interior
    legitimately occupies most of the sheet, so an area ratio would prove
    nothing. The test is that the component containing the sheet corner
    never became a region.
    """
    seg = _two_rooms()
    topo = rt.build(seg, _frame(seg), min_region_m2=0.5)
    corner_label = int(np.asarray(topo.labels)[0, 0])
    assert corner_label not in topo.region_label_of.values()
    assert topo.notes["outside_components"] >= 1
    # And no region's bounding box spans the whole sheet.
    h, w = seg.wall_mask.shape
    for r in topo.regions:
        x0, y0, x1, y1 = r.bbox_mm
        assert (x1 - x0) < w * seg.px_mm - seg.px_mm


def test_slivers_below_the_minimum_area_are_dropped_and_counted():
    seg = _two_rooms()
    seg.wall_mask[40:43, 20:24] = True     # a tiny enclosed nick
    topo = rt.build(seg, _frame(seg), min_region_m2=20.0)
    assert topo.regions == [] or all(
        r.approximate_area_m2 >= 20.0 for r in topo.regions)
    assert topo.notes["regions_below_min_area_dropped"] >= 1


# --- §5 vector walls reinforce the separation ----------------------------

def test_an_established_wall_separates_rooms_the_render_leaves_joined():
    """The point of the fusion: ink misses a hairline, the solid does not."""
    seg = _two_rooms(gap_at=50, gap_width=9)
    frame = _frame(seg)
    before = rt.build(seg, frame, min_region_m2=0.5)
    assert len(before.regions) == 1

    # A wall rectangle over the gap, in vector mm (IDENTITY frame).
    px = seg.px_mm
    solid = box(79 * px, 50 * px, 82 * px, 59 * px)
    after = rt.build(seg, frame, established_solid=solid, min_region_m2=0.5)
    assert len(after.regions) == 2
    assert after.provenance["established_solid_barrier_px"] > 0


def test_a_diagnostic_hypothesis_never_creates_a_separation():
    """§5: diagnostic walls are soft proposals, not barriers."""
    seg = _two_rooms(gap_at=50, gap_width=9)
    frame = _frame(seg)
    px = seg.px_mm
    hypothesis = box(79 * px, 50 * px, 82 * px, 59 * px)
    topo = rt.build(seg, frame, established_solid=None,
                    diagnostic_solid=hypothesis, min_region_m2=0.5)
    assert len(topo.regions) == 1, "a hypothesis manufactured a room"
    assert topo.soft_barrier_proposals
    prop = topo.soft_barrier_proposals[0]
    assert prop["used_as_a_barrier"] is False
    assert "may not manufacture a room" in prop["why"]


def test_a_portal_barrier_is_reopened_so_a_doorway_still_connects():
    """§5: portals stay passable, or we manufacture the separation."""
    seg = _two_rooms(gap_at=50, gap_width=9)
    frame = _frame(seg)
    px = seg.px_mm
    solid = box(79 * px, 10 * px, 82 * px, 110 * px)      # the whole wall
    portal = _Barrier(box(78 * px, 50 * px, 83 * px, 59 * px))

    closed = rt.build(seg, frame, established_solid=solid, min_region_m2=0.5)
    assert len(closed.regions) == 2

    passable = rt.build(seg, frame, established_solid=solid,
                        portal_barriers=[portal], min_region_m2=0.5)
    assert len(passable.regions) == 1
    assert passable.provenance["portal_pixels_reopened"] > 0


# --- adjacency and candidate openings ------------------------------------

def test_two_regions_across_a_thin_wall_are_adjacent():
    seg = _two_rooms()
    topo = rt.build(seg, _frame(seg), min_region_m2=0.5)
    assert len(topo.adjacencies) == 1
    adj = topo.adjacencies[0]
    assert adj.contact_px > 0
    assert adj.min_barrier_px == 3          # the wall is three pixels wide


def test_one_doorway_is_one_candidate_opening_not_hundreds():
    """The clustering bug: a door found once per scan line became many."""
    seg = _two_rooms()
    # A near-door: the wall thins to one pixel over a short run, leaving the
    # regions separate but only just.
    seg.wall_mask[50:59, 80:82] = False
    topo = rt.build(seg, _frame(seg), min_region_m2=0.5)
    assert len(topo.regions) == 2
    assert 1 <= len(topo.openings) <= 2, (
        f"{len(topo.openings)} candidates for one thin place")


def test_regions_carry_their_adjacency_and_opening_ids():
    seg = _two_rooms()
    seg.wall_mask[50:59, 80:82] = False
    topo = rt.build(seg, _frame(seg), min_region_m2=0.5)
    for r in topo.regions:
        assert r.adjacent_region_ids
        assert r.candidate_opening_ids


def test_a_candidate_opening_may_not_supply_a_width():
    """§3: raster may not be the authoritative source of opening width."""
    seg = _two_rooms()
    seg.wall_mask[50:59, 80:82] = False
    topo = rt.build(seg, _frame(seg), min_region_m2=0.5)
    rec = topo.openings[0].record()
    assert "APPROXIMATE_width_mm" in rec
    assert "opening_width_mm" not in rec
    assert rec["may_not_supply"].startswith("an opening width")
    assert "SEARCH_WINDOW_centroid_mm" in rec


# --- §3, §4 what it refuses ----------------------------------------------

def test_no_released_millimetre_leaves_this_module():
    seg = _two_rooms()
    rec = rt.build(seg, _frame(seg), min_region_m2=0.5).record()
    forbidden = ("wall coordinate", "wall thickness", "opening width",
                 "released area", "released perimeter")
    for phrase in forbidden:
        assert phrase in rec["what_this_may_not_supply"]
    for row in rec["region_rows"]:
        assert "APPROXIMATE_area_m2" in row
        assert "area_m2" not in row


def test_the_pipeline_cannot_see_the_golden_regions():
    """§4: the human overlay may score this output and may not build it."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(rt))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    params = set(inspect.signature(rt.build).parameters)
    for forbidden in ("golden", "overlay", "benchmark", "space_map",
                      "labels_inside", "expected", "room_names"):
        assert forbidden not in params
        assert forbidden not in names
    assert "golden" not in inspect.getsource(rt).lower().replace(
        "golden regions", "").replace("golden region", "")


def test_the_record_states_what_built_it():
    seg = _two_rooms()
    rec = rt.build(seg, _frame(seg), min_region_m2=0.5).record()
    assert "No golden region" in rec["built_from"]
    assert "may SCORE it" in rec["built_from"]
    assert rec["algorithm"] == rt.ALGORITHM
    prov = rec["provenance"]
    for key in ("algorithm", "dpi", "ink_threshold", "px_mm", "frame",
                "min_region_m2"):
        assert key in prov


# --- the freeze -----------------------------------------------------------

def test_the_output_hash_is_stable_for_the_same_input():
    seg = _two_rooms()
    frame = _frame(seg)
    a = rt.build(seg, frame, min_region_m2=0.5)
    b = rt.build(seg, frame, min_region_m2=0.5)
    assert a.output_hash == b.output_hash


def test_the_output_hash_covers_the_openings_too():
    """A frozen automatic result must not be able to change its openings."""
    seg = _two_rooms()
    frame = _frame(seg)
    a = rt.build(seg, frame, min_region_m2=0.5)
    seg2 = _two_rooms()
    seg2.wall_mask[50:59, 80:82] = False         # adds a thin place
    b = rt.build(seg2, frame, min_region_m2=0.5)
    assert a.output_hash != b.output_hash


# --- §9 a graded portal closes; a hypothesis stays passable --------------

def test_a_supported_portal_closes_the_partition():
    """A partition barrier exists to separate the spaces it connects.

    Reopening EVERY portal merged rooms through their doorways. A portal
    whose existence is supported is evidence, not a hypothesis, so it may
    close — while an unvalidated one must still stay passable.
    """
    seg = _two_rooms(gap_at=50, gap_width=9)
    frame = _frame(seg)
    px = seg.px_mm
    door = _Barrier(box(78 * px, 50 * px, 83 * px, 59 * px))

    merged = rt.build(seg, frame, min_region_m2=0.5)
    assert len(merged.regions) == 1

    closed = rt.build(seg, frame, closing_barriers=[door],
                      min_region_m2=0.5)
    assert len(closed.regions) == 2
    assert closed.provenance["validated_portal_pixels_closed"] > 0


def test_a_hypothesis_portal_still_may_not_manufacture_a_separation():
    seg = _two_rooms(gap_at=50, gap_width=9)
    frame = _frame(seg)
    px = seg.px_mm
    door = _Barrier(box(78 * px, 50 * px, 83 * px, 59 * px))
    got = rt.build(seg, frame, portal_barriers=[door], min_region_m2=0.5)
    assert len(got.regions) == 1
    assert got.provenance["validated_portal_pixels_closed"] == 0


def test_the_record_explains_the_two_portal_treatments():
    seg = _two_rooms()
    rec = rt.build(seg, _frame(seg), min_region_m2=0.5).record()
    assert "evidence grade" in rec["portals_were"]
    assert "only a hypothesis is left PASSABLE" in rec["portals_were"]


def test_declining_to_close_is_not_the_same_as_reopening():
    """Three distinct treatments, and the difference matters.

    Carving a barrier out of the mask DELETES ink the drawing contains — a
    door leaf, a threshold. Declining to ADD an unsupported barrier does
    not. So an unvalidated portal is left alone by default, and reopening
    is a separate act a caller must ask for explicitly.
    """
    seg = _two_rooms()                      # a solid wall, no gap in the ink
    frame = _frame(seg)
    px = seg.px_mm
    door = _Barrier(box(78 * px, 40 * px, 83 * px, 70 * px))

    left_alone = rt.build(seg, frame, min_region_m2=0.5)
    assert len(left_alone.regions) == 2
    assert left_alone.provenance["portal_pixels_reopened"] == 0

    reopened = rt.build(seg, frame, portal_barriers=[door],
                        min_region_m2=0.5)
    assert reopened.provenance["portal_pixels_reopened"] > 0
    assert len(reopened.regions) == 1, (
        "reopening must actually delete the ink when asked")
