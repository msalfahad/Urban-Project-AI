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
