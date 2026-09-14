"""E52 — a bounding box is an index, never a room."""

from __future__ import annotations

import pytest

from engine.bbox import (RECTANGULAR_BY_PRINTED_DIMENSIONS,
                         RECTANGULARITY_UNPROVEN, ROOM_AREA, ROOM_PERIMETER,
                         ROOM_SIDES, BoundingBox, BoundingBoxError,
                         prove_rectangular, raster_outline_refusal)


def box(sid="STR-01", fill=0.676):
    return BoundingBox(sid, 0.0, 0.0, 4000.0, 3000.0, fill_ratio=fill)


def test_indexing_is_always_allowed():
    assert box().index_extent() == (0.0, 0.0, 4000.0, 3000.0)


@pytest.mark.parametrize("use", [ROOM_SIDES, ROOM_PERIMETER, ROOM_AREA])
def test_an_unproven_box_may_not_supply_physical_geometry(use):
    """STR-01's 2606 mm 'missing wall' was the east edge of this box."""
    with pytest.raises(BoundingBoxError, match="NEVER PHYSICAL GEOMETRY"):
        box().physical(use)


def test_the_refusal_states_how_far_the_room_is_from_its_box():
    with pytest.raises(BoundingBoxError, match="fills 68%"):
        box().physical(ROOM_SIDES)


def test_a_fill_ratio_is_not_a_rectangularity_proof():
    """The missing few percent is exactly where a notch or stub wall lives."""
    b = BoundingBox("X", 0.0, 0.0, 1000.0, 1000.0, fill_ratio=0.98)
    assert not b.is_proven_rectangular
    with pytest.raises(BoundingBoxError):
        b.physical(ROOM_AREA)


def test_an_independent_proof_grants_exactly_one_box():
    b = prove_rectangular(box("BTH-05", 0.894),
                          basis=RECTANGULAR_BY_PRINTED_DIMENSIONS,
                          proof="printed 2336 x 1460 on AR-00")
    assert b.is_proven_rectangular
    assert b.physical(ROOM_SIDES) == (0.0, 0.0, 4000.0, 3000.0)
    # and no other box is affected
    assert box().rectangularity == RECTANGULARITY_UNPROVEN


def test_a_proof_must_say_what_proved_it():
    with pytest.raises(BoundingBoxError, match="better manners"):
        prove_rectangular(box(), basis=RECTANGULAR_BY_PRINTED_DIMENSIONS,
                          proof="")


def test_a_fill_ratio_is_refused_as_a_basis_outright():
    with pytest.raises(BoundingBoxError, match="not an accepted"):
        prove_rectangular(box(), basis="FILL_RATIO_ABOVE_0_9", proof="0.94")


def test_the_raster_outline_is_not_the_replacement():
    """WSH-01 proves a raster region can carry the wrong physical identity."""
    why = raster_outline_refusal("STR-01")
    assert "may not construct" in why
    assert "WSH-01" in why
    assert "WALL BANDS" in why
