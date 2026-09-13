"""Each quantity declares what it needs. One global geometry flag is not enough.

"Openings unresolved, so no wall quantity" is both too strict and too loose. Too
strict: a GROSS ceramic wall area does not need the openings — whether to deduct
them is the trade rule's decision, and a gross figure with the deduction pending
is a useful, honest number. Too loose: blockwork needs the openings AND the
physical-wall split AND a thickness, and one flag would wave all three through.
"""

from __future__ import annotations

import pytest

from engine.release_matrix import (CLOSED_BOUNDARY, EXTERNAL_SPLIT, FLOOR_AREA,
                                   HEIGHT, NOT_READY, OPENING_RULE, OPENINGS,
                                   PHYSICAL_WALL_SPLIT, READY, REGION_IDENTITY,
                                   SCOPE, TRADE_RULE, USES, WALL_THICKNESS,
                                   ReleaseMatrixError, assess,
                                   gross_alternatives, matrix)

GEOMETRY_ONLY = {SCOPE: True, REGION_IDENTITY: True, CLOSED_BOUNDARY: True,
                 HEIGHT: True, TRADE_RULE: True}


def test_a_gross_wall_area_does_not_need_the_openings():
    """The point of a gross figure."""
    assert assess("GROSS_CERAMIC_WALL", GEOMETRY_ONLY).ready


def test_the_net_form_of_the_same_quantity_does_need_them():
    r = assess("NET_CERAMIC_WALL", GEOMETRY_ONLY)
    assert not r.ready
    assert set(r.missing) == {OPENINGS, OPENING_RULE}


def test_a_blocked_net_quantity_names_the_gross_one_that_could_ship_now():
    assert gross_alternatives("NET_CERAMIC_WALL") == ["GROSS_CERAMIC_WALL"]
    assert gross_alternatives("NET_PLASTER") == ["GROSS_PLASTER"]


def test_gross_and_net_are_different_uses_so_one_cannot_be_read_as_the_other():
    assert USES["GROSS_PLASTER"].is_gross and not USES["NET_PLASTER"].is_gross
    assert USES["GROSS_PLASTER"].gross_of == "NET_PLASTER"


def test_blockwork_needs_far_more_than_a_closed_boundary():
    r = assess("BLOCKWORK", GEOMETRY_ONLY)
    assert not r.ready
    assert set(r.missing) == {PHYSICAL_WALL_SPLIT, EXTERNAL_SPLIT, OPENINGS,
                              OPENING_RULE, WALL_THICKNESS}


def test_paint_is_not_derived_from_plaster_and_carries_its_own_dependencies():
    """Ceramic, stone or cladding may cover what plaster covered."""
    assert set(USES["PAINT"].requires) == set(USES["NET_PLASTER"].requires)
    assert "plaster" in USES["PAINT"].description


def test_skirting_depends_on_boundary_and_openings_never_on_floor_area():
    assert FLOOR_AREA not in USES["SKIRTING"].requires
    assert OPENINGS in USES["SKIRTING"].requires
    assert "never derived from floor area" in USES["SKIRTING"].description


def test_an_external_finish_needs_the_internal_external_split():
    assert EXTERNAL_SPLIT in USES["EXTERNAL_FINISH"].requires


def test_waterproofing_splits_horizontal_from_vertical():
    assert FLOOR_AREA in USES["WATERPROOFING_HORIZONTAL"].requires
    assert HEIGHT in USES["WATERPROOFING_VERTICAL"].requires
    assert HEIGHT not in USES["WATERPROOFING_HORIZONTAL"].requires


def test_a_ceiling_is_not_assumed_equal_to_the_floor():
    assert "never assumed equal to floor area" in USES["CEILING"].description


# --- nothing defaults ---------------------------------------------------------

def test_a_dependency_nobody_mentioned_counts_as_missing():
    """Silence is the commonest way a default sneaks in."""
    r = assess("GROSS_PERIMETER", {SCOPE: True})
    assert not r.ready
    assert set(r.missing) == {REGION_IDENTITY, CLOSED_BOUNDARY}
    assert "never established" in r.reasons[REGION_IDENTITY]


def test_an_explicitly_false_dependency_blocks_and_keeps_its_reason():
    r = assess("GROSS_PERIMETER",
               {SCOPE: True, REGION_IDENTITY: False, CLOSED_BOUNDARY: True},
               reasons={REGION_IDENTITY: "WSH-01 may be the shaft, not the washroom"})
    assert r.missing == [REGION_IDENTITY]
    assert "shaft" in r.explain()


def test_an_unknown_use_raises_rather_than_being_allowed():
    with pytest.raises(ReleaseMatrixError, match="unknown use"):
        assess("CEILING_PAINT_MAYBE", GEOMETRY_ONLY)


def test_region_identity_gates_every_single_use():
    """Attach a trade to the wrong polygon and every number after it is wrong."""
    for name, use in USES.items():
        assert REGION_IDENTITY in use.requires, name


def test_scope_gates_every_single_use():
    for name, use in USES.items():
        assert SCOPE in use.requires, name


def test_the_matrix_assesses_every_use_against_one_set_of_facts():
    m = matrix(GEOMETRY_ONLY)
    assert set(m) == set(USES)
    ready = sorted(n for n, r in m.items() if r.ready)
    assert "GROSS_CERAMIC_WALL" in ready and "BLOCKWORK" not in ready
