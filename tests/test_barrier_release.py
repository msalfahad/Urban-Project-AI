"""A probable portal may produce a hypothesis. It may not release a quantity.

A barrier is accepted geometrically long before the opening it plugs is
proven to exist. If the portal is not really there, the space is not really
there — and a released quantity carries no memory of which portal it rested
on. So acceptance and releasability are two different questions.
"""

import pytest

from engine.free_space import (BARRIER_ACCEPTED, BARRIER_REJECTED,
                               BARRIER_RELEASE_UNRESOLVED,
                               DIAGNOSTIC_PARTITION_BARRIER,
                               NOT_CONSTRAINED_BY_A_BARRIER,
                               RELEASABLE_PARTITION_BARRIER,
                               PortalPartitionBarrier, release_policy)
from engine.space_boundary import (EXISTENCE_PROBABLE, EXISTENCE_VALIDATED,
                                   GEOMETRY_PROBABLE, GEOMETRY_UNRESOLVED,
                                   GEOMETRY_VALIDATED)


def _bar(pid="PT-1", existence=EXISTENCE_VALIDATED,
         geometry=GEOMETRY_VALIDATED, status=BARRIER_ACCEPTED, ev=("A", "B")):
    return PortalPartitionBarrier(
        portal_id=pid, ring=((0, 0), (900, 0), (900, 200), (0, 200), (0, 0)),
        host_wall_band_id="WB-1", jamb_a_mm=0.0, jamb_b_mm=900.0, axis="H",
        closure_basis="HOST_WALL_THICKNESS", existence_status=existence,
        geometry_status=geometry, existence_evidence=ev, status=status)


class _Cand:
    def __init__(self, i, ports=()):
        self.space_geometry_id = i
        self.bounding_portal_ids = tuple(ports)


# --- the barrier's own class ---------------------------------------------

def test_a_validated_portal_with_established_geometry_may_release():
    b = _bar()
    assert b.release_class == RELEASABLE_PARTITION_BARRIER
    assert b.release_blocker == ""
    assert b.record()["may_release_a_space"]


def test_a_probable_portal_gives_a_diagnostic_barrier_only():
    b = _bar(existence=EXISTENCE_PROBABLE)
    assert b.release_class == DIAGNOSTIC_PARTITION_BARRIER
    assert not b.record()["may_release_a_space"]


def test_four_geometric_observations_of_one_gap_are_one_family():
    # This is the actual AR-00 case: SPAN_IN_THE_DOOR_RANGE,
    # PAIRED_BANDS_TERMINATE_FACING_EACH_OTHER, END_CAPS_AT_BOTH_JAMBS and
    # GAP_CLOSES_AN_OTHERWISE_COMPLETE_BOUNDARY. Four items, all looking at
    # the same gap in the same way.
    b = _bar(existence=EXISTENCE_PROBABLE,
             ev=("SPAN_IN_THE_DOOR_RANGE",
                 "PAIRED_BANDS_TERMINATE_FACING_EACH_OTHER",
                 "END_CAPS_AT_BOTH_JAMBS",
                 "GAP_CLOSES_AN_OTHERWISE_COMPLETE_BOUNDARY"))
    assert b.release_class == DIAGNOSTIC_PARTITION_BARRIER
    assert "SECOND INDEPENDENT FAMILY" in b.release_blocker
    assert "one family, not four proofs" in b.release_blocker


def test_geometry_being_probable_is_enough_geometry():
    # Geometry only has to be established; existence is the hard gate.
    assert _bar(geometry=GEOMETRY_PROBABLE).release_class == \
        RELEASABLE_PARTITION_BARRIER


def test_unresolved_geometry_blocks_even_a_validated_portal():
    b = _bar(geometry=GEOMETRY_UNRESOLVED)
    assert b.release_class == DIAGNOSTIC_PARTITION_BARRIER
    assert "the barrier's own extent is a hypothesis" in b.release_blocker


def test_a_barrier_that_was_not_accepted_releases_nothing():
    b = _bar(status=BARRIER_REJECTED)
    assert b.release_class == BARRIER_RELEASE_UNRESOLVED
    assert "the barrier itself is" in b.release_blocker


# --- the policy over whole components ------------------------------------

def test_one_unproven_barrier_blocks_the_whole_component():
    # A component's shape is wrong if ANY opening it depends on is wrong.
    bars = [_bar("PT-1"), _bar("PT-2", existence=EXISTENCE_PROBABLE)]
    got = release_policy(bars, [_Cand("SG-1", ("PT-1", "PT-2"))])
    row = got["space_geometries"][0]
    assert row["release_class"] == DIAGNOSTIC_PARTITION_BARRIER
    assert row["barriers_that_cannot_release"] == ["PT-2"]
    assert row["barriers_depended_on"] == 2


def test_a_component_whose_every_barrier_is_validated_may_release():
    bars = [_bar("PT-1"), _bar("PT-2")]
    got = release_policy(bars, [_Cand("SG-1", ("PT-1", "PT-2"))])
    assert got["space_geometries"][0]["release_class"] == \
        RELEASABLE_PARTITION_BARRIER
    assert got["releasable_space_geometries"] == 1


def test_a_component_no_barrier_bounds_is_not_thereby_cleared():
    # Most of AR-00's components are merged blobs that no barrier touches.
    # Calling them releasable would turn silence into a clearance.
    got = release_policy([_bar()], [_Cand("SG-1", ())])
    row = got["space_geometries"][0]
    assert row["release_class"] == NOT_CONSTRAINED_BY_A_BARRIER
    assert "NOT a clearance" in row["why"]
    assert got["releasable_space_geometries"] == 0
    assert got["space_geometries_no_barrier_bounds"] == 1


def test_the_counts_separate_the_three_outcomes():
    bars = [_bar("PT-1"), _bar("PT-2", existence=EXISTENCE_PROBABLE)]
    cands = [_Cand("SG-1", ("PT-1",)), _Cand("SG-2", ("PT-2",)),
             _Cand("SG-3", ())]
    got = release_policy(bars, cands)
    assert got["releasable_space_geometries"] == 1
    assert got["space_geometries_blocked_by_a_barrier"] == 1
    assert got["space_geometries_no_barrier_bounds"] == 1
    assert got["releasable_barriers"] == 1
    assert got["diagnostic_barriers"] == 1


def test_the_policy_states_what_a_probable_portal_may_and_may_not_do():
    got = release_policy([], [])
    assert "may generate a space HYPOTHESIS" in got["policy"]
    assert "may NOT make the resulting space releasable" in got["policy"]


def test_a_rejected_barrier_is_not_counted_as_a_dependency():
    bars = [_bar("PT-1", status=BARRIER_REJECTED)]
    got = release_policy(bars, [_Cand("SG-1", ("PT-1",))])
    assert got["accepted_barriers"] == 0
    assert got["space_geometries"][0]["barriers_depended_on"] == 0


def test_a_barrier_never_becomes_material_whatever_its_release_class():
    from engine.free_space import TOPOLOGY_ONLY_NOT_MATERIAL
    for b in (_bar(), _bar(existence=EXISTENCE_PROBABLE)):
        assert b.record()["material_role"] == TOPOLOGY_ONLY_NOT_MATERIAL
