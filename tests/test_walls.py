"""E25 — wall segments, dimension ownership, and proven openings.

These run on small hand-built masks where the right answer is known by
construction, so a regression shows up as an arithmetic failure rather than a
judgement call about a drawing.
"""

from __future__ import annotations

from decimal import Decimal as D

import numpy as np
import pytest

from engine.walls import (OPEN, OPENING, WALL, SpaceWalls, WallError,
                          bridge_openings, duplicate_walls, orientation,
                          run_length, space_walls)

PX = D("1000")          # 1 px = 1 m, so every expected number is readable


def room(h=9, w=9, box=(2, 6, 2, 6)):
    """A rectangular room: wall ring + interior label."""
    y0, y1, x0, x1 = box
    wall = np.zeros((h, w), bool)
    wall[y0, x0:x1 + 1] = wall[y1, x0:x1 + 1] = True
    wall[y0:y1 + 1, x0] = wall[y0:y1 + 1, x1] = True
    lab = np.zeros((h, w), np.int32)
    lab[y0 + 1:y1, x0 + 1:x1] = 7
    return wall, lab


# ------------------------------------------------------------------- helpers
def test_run_length_measures_the_whole_run():
    m = np.array([[True, True, True, False, True]])
    assert run_length(m, 1).tolist() == [[3, 3, 3, 0, 1]]


def test_orientation_splits_vertical_from_horizontal_wall():
    wall = np.zeros((7, 7), bool)
    wall[1:6, 3] = True          # a vertical wall
    vert, horiz = orientation(wall)
    assert vert[3, 3] and not horiz[3, 3]


# ------------------------------------------------------------------ openings
def test_a_door_gap_between_jambs_is_bridged_and_measured():
    wall, lab = room()
    wall[6, 4] = False                                  # doorway in the south wall
    closed, bridges = bridge_openings(wall, 2)
    assert bridges.sum() == 1 and closed[6, 4]
    sw = space_walls('RM', lab, 7, wall, bridges, PX, outside_id=0, max_opening_mm=2000)
    assert [o.width_mm for o in sw.openings] == [1000]
    assert 'jamb pair' in sw.openings[0].provenance


def test_a_gap_wider_than_a_door_is_left_open():
    wall, lab = room()
    wall[6, 3:6] = False                                # 3 m hole: not a door
    _, bridges = bridge_openings(wall, 2)
    assert bridges.sum() == 0


def test_the_empty_middle_of_a_room_is_never_bridged():
    """Wall above and wall below also describes a room. Only jambs count."""
    wall = np.zeros((9, 9), bool)
    wall[2, 1:8] = True
    wall[6, 1:8] = True                                 # two horizontal walls, 3 apart
    _, bridges = bridge_openings(wall, 5)
    assert bridges.sum() == 0, "bridging sealed a room that was never connected"


# ------------------------------------------------------------------ segments
def test_a_closed_room_reports_its_true_perimeter():
    wall, lab = room()
    sw = space_walls('RM', lab, 7, wall, np.zeros_like(wall), PX, outside_id=0)
    assert sw.perimeter_m == D('12')                    # 3 m x 3 m interior
    assert sw.wall_length_m == D('12')
    assert sw.is_closed and sw.status == 'VALIDATED'


def test_a_doorway_still_counts_toward_wall_length():
    """Ceramic runs across a doorway; the opening is a separate deduction."""
    wall, lab = room()
    wall[6, 4] = False
    _, bridges = bridge_openings(wall, 2)
    sw = space_walls('RM', lab, 7, wall, bridges, PX, outside_id=0, max_opening_mm=2000)
    assert sw.wall_length_m == D('12')
    assert sw.opening_deduction_m == D('1')


def test_an_open_side_is_flagged_not_counted_as_wall():
    wall, lab = room()
    wall[6, 3:6] = False                                # open-plan transition
    sw = space_walls('RM', lab, 7, wall, np.zeros_like(wall), PX, outside_id=0)
    assert sw.open_length_m == D('3')
    assert sw.wall_length_m == D('9')
    assert not sw.is_closed and sw.status == 'UNRESOLVED'
    assert any(s.far_side == OPEN and s.validation == 'UNRESOLVED' for s in sw.segments)


def test_every_segment_carries_provenance():
    wall, lab = room()
    sw = space_walls('RM', lab, 7, wall, np.zeros_like(wall), PX, outside_id=0,
                     drawing='AR-00', revision='Rev C')
    assert sw.segments
    for s in sw.segments:
        assert s.space_id == 'RM' and s.wall_id.startswith('RM-')
        assert s.source_drawing == 'AR-00' and s.source_revision == 'Rev C'
        assert s.side in ('N', 'S', 'E', 'W')
        assert s.length_mm > 0 and s.start_px != s.end_px
        assert s.classification in ('INTERNAL', 'EXTERNAL')


def test_an_external_wall_is_classified_from_what_lies_beyond_it():
    wall, lab = room()
    sw = space_walls('RM', lab, 7, wall, np.zeros_like(wall), PX, outside_id=0)
    assert all(s.classification == 'EXTERNAL' for s in sw.segments if s.far_side == WALL)


def test_an_internal_wall_names_the_space_on_the_other_side():
    """Two rooms sharing one wall: the segment must point at the neighbour."""
    wall = np.zeros((9, 13), bool)
    wall[2, 2:11] = wall[6, 2:11] = True
    wall[2:7, 2] = wall[2:7, 6] = wall[2:7, 10] = True
    lab = np.zeros((9, 13), np.int32)
    lab[3:6, 3:6] = 7
    lab[3:6, 7:10] = 8
    sw = space_walls('LEFT', lab, 7, wall, np.zeros_like(wall), PX, outside_id=0,
                     id_to_space={8: 'RIGHT'})
    east = [s for s in sw.segments if s.side == 'E']
    assert east and east[0].adjoining_space == 'RIGHT'
    assert east[0].classification == 'INTERNAL'


def test_a_missing_region_raises_rather_than_returning_nothing():
    wall, lab = room()
    with pytest.raises(WallError, match="not in the label map"):
        space_walls('GHOST', lab, 999, wall, np.zeros_like(wall), PX)


def test_a_shared_wall_is_reported_not_silently_merged():
    wall = np.zeros((9, 13), bool)
    wall[2, 2:11] = wall[6, 2:11] = True
    wall[2:7, 2] = wall[2:7, 6] = wall[2:7, 10] = True
    lab = np.zeros((9, 13), np.int32)
    lab[3:6, 3:6] = 7
    lab[3:6, 7:10] = 8
    a = space_walls('LEFT', lab, 7, wall, np.zeros_like(wall), PX, outside_id=0)
    b = space_walls('RIGHT', lab, 8, wall, np.zeros_like(wall), PX, outside_id=0)
    # 1 px = 1 m here, so the two faces of the 1 px wall sit 2 m apart
    pairs = duplicate_walls([a, b], PX, max_wall_mm=2000)
    assert pairs, 'the shared wall between LEFT and RIGHT was not reported'
    assert any('LEFT' in x and 'RIGHT' in y or 'RIGHT' in x and 'LEFT' in y
               for x, y, _ in pairs)


def test_unrelated_walls_far_apart_are_not_called_duplicates():
    wall, lab = room()
    a = space_walls('RM', lab, 7, wall, np.zeros_like(wall), PX, outside_id=0)
    # opposite faces of the SAME room are 3 m apart — a room, not a shared wall
    assert duplicate_walls([a], PX, max_wall_mm=2000) == []


def test_wall_length_excludes_open_but_perimeter_does_not():
    sw = SpaceWalls('X')
    from engine.walls import WallSegment
    sw.segments = [
        WallSegment('w1', 'X', 'N', (0, 0), (3, 0), 3000, WALL, None, 'INTERNAL'),
        WallSegment('w2', 'X', 'S', (0, 3), (3, 3), 2000, OPEN, 'Y', 'INTERNAL'),
    ]
    assert sw.perimeter_m == D('5') and sw.wall_length_m == D('3')
    assert sw.open_length_m == D('2') and not sw.is_closed


# ------------------------------------------------------- hole filling matters
def test_a_fixture_inside_a_room_does_not_become_wall():
    """A WC drawn inside a bathroom must not be traced as part of its boundary."""
    wall, lab = room(11, 11, (1, 9, 1, 9))
    fixture = (5, 5)
    lab[fixture] = 0                       # a fixture punches a hole in the region
    sw_filled = space_walls('RM', lab, 7, wall, np.zeros_like(wall), PX, outside_id=0)
    sw_raw = space_walls('RM', lab, 7, wall, np.zeros_like(wall), PX,
                         outside_id=0, fill_region=False)
    assert sw_filled.perimeter_m == D('28')          # 7 m x 7 m interior
    assert sw_raw.perimeter_m > sw_filled.perimeter_m


# --------------------------------- topology / gross / net kept separate
def test_a_doorway_closure_is_not_a_physical_wall():
    from engine.walls import (PHYSICAL_WALL, VIRTUAL_OPENING_CLOSURE,
                              OPEN_TRANSITION, WallSegment)
    wall, lab = room()
    wall[6, 4] = False
    _, bridges = bridge_openings(wall, 2)
    sw = space_walls('RM', lab, 7, wall, bridges, PX, outside_id=0, max_opening_mm=2000)
    v = [s for s in sw.segments if s.segment_type == VIRTUAL_OPENING_CLOSURE]
    assert len(v) == 1
    assert not v[0].physical_wall
    assert v[0].counts_for_gross_perimeter and v[0].counts_for_gross_wall
    assert v[0].deductible_from_net_finish


def test_gross_wall_includes_the_doorway_and_net_deducts_it():
    """The qiyal measures gross; only a trade rule may take the opening off."""
    wall, lab = room()
    wall[6, 4] = False
    _, bridges = bridge_openings(wall, 2)
    sw = space_walls('RM', lab, 7, wall, bridges, PX, outside_id=0, max_opening_mm=2000)
    assert sw.gross_wall_perimeter_m == D('12')
    assert sw.physical_wall_m == D('11')          # masonry only
    assert sw.net_wall_perimeter_m() == D('11')   # gross minus the 1 m opening
    assert sw.net_wall_perimeter_m(deduct_openings=False) == D('12')


def test_an_open_side_is_in_the_room_outline_but_not_in_gross_wall():
    from engine.walls import OPEN_TRANSITION
    wall, lab = room()
    wall[6, 3:6] = False
    sw = space_walls('RM', lab, 7, wall, np.zeros_like(wall), PX, outside_id=0)
    assert sw.gross_room_perimeter_m == D('12')   # the closed outline
    assert sw.gross_wall_perimeter_m == D('9')    # no wall on the open side
    assert any(s.segment_type == OPEN_TRANSITION for s in sw.segments)


# ------------------------------------------------------------ dashed lines
def test_a_dashed_line_is_rebuilt_as_one_boundary():
    """The مغاسل case: a threshold drawn as dashes is a boundary, not a gap."""
    from engine.walls import dashed_runs
    px = D("10")                       # 1 px = 10 mm
    dashes = [("H", 100.0, float(x), float(x + 20)) for x in range(0, 120, 30)]
    runs = dashed_runs(dashes, px, max_dash_mm=350, max_gap_mm=200, min_run_mm=600)
    assert len(runs) == 1
    ori, fixed, a, b = runs[0]
    assert ori == "H" and fixed == 100.0
    assert D(str(b - a)) * px >= D("600")


def test_two_ordinary_walls_are_not_joined_into_a_dashed_run():
    """Long collinear pieces are walls with a door between them, not dashes."""
    from engine.walls import dashed_runs
    px = D("10")
    walls = [("H", 50.0, 0.0, 200.0), ("H", 50.0, 300.0, 500.0)]   # 2 m pieces
    assert dashed_runs(walls, px) == []


def test_a_short_dashed_run_is_not_a_boundary():
    from engine.walls import dashed_runs
    px = D("10")
    dashes = [("H", 10.0, float(x), float(x + 10)) for x in range(0, 40, 20)]
    assert dashed_runs(dashes, px) == []


# --------------------------------------------- walls versus fixtures
def test_a_single_line_is_not_a_wall():
    """The BTH-07 defect: a lone fixture line got a doorway inserted in it."""
    from engine.walls import paired_wall_faces
    px = D("10")                                   # 1 px = 10 mm
    wall_a = ("V", 100.0, 0.0, 300.0)
    wall_b = ("V", 110.0, 0.0, 300.0)              # its other face, 100 mm away
    fixture = ("V", 200.0, 50.0, 140.0)            # a lone shower line
    kept = paired_wall_faces([wall_a, wall_b, fixture], px)
    assert wall_a in kept and wall_b in kept
    assert fixture not in kept


def test_faces_too_far_apart_are_not_one_wall():
    from engine.walls import paired_wall_faces
    px = D("10")
    far = [("V", 0.0, 0.0, 300.0), ("V", 100.0, 0.0, 300.0)]   # 1 m apart
    assert paired_wall_faces(far, px) == []


def test_parallel_lines_that_do_not_overlap_are_not_one_wall():
    from engine.walls import paired_wall_faces
    px = D("10")
    offset = [("V", 100.0, 0.0, 20.0), ("V", 110.0, 200.0, 300.0)]
    assert paired_wall_faces(offset, px) == []


def test_a_reconstructed_run_must_land_on_walls_at_both_ends():
    """A threshold spans an opening; tub hatching ends in mid-air."""
    from engine.walls import anchored_runs
    px = D("10")
    walls = [("V", 0.0, 0.0, 200.0), ("V", 100.0, 0.0, 200.0)]
    threshold = ("H", 100.0, 0.0, 100.0)        # wall to wall
    hatching = ("H", 50.0, 30.0, 70.0)          # floating inside the room
    kept = anchored_runs([threshold, hatching], walls, px)
    assert threshold in kept and hatching not in kept


def test_a_fixture_near_a_real_wall_does_not_borrow_its_partner():
    """x=2580 sat 227 mm from the BTH-06 partition and pretended to be a wall."""
    from engine.walls import paired_wall_faces
    px = D("10")
    face_a = ("V", 260.0, 0.0, 300.0)          # partition face
    face_b = ("V", 275.0, 0.0, 300.0)          # its other face, 150 mm away
    fixture = ("V", 237.0, 10.0, 100.0)        # 230 mm from face_a — plausible, but
    kept = paired_wall_faces([face_a, face_b, fixture], px)
    assert face_a in kept and face_b in kept
    assert fixture not in kept, "fixture borrowed the partition as its partner"
