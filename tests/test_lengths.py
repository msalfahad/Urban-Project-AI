"""E51 — a doorway is four facts, and they must never be one number."""

from __future__ import annotations

import pytest

from engine.lengths import (BASES, HOST_WALL_GROSS_LENGTH,
                            MATERIAL_PRESENT_LENGTH, OPENING_LENGTH,
                            RULE_REQUIRED, SKIRTING_ELIGIBLE_LENGTH,
                            SPACE_BOUNDARY_LENGTH, LengthBasisError, LengthSet,
                            basis_for, deducts_openings)


def door(width=1054.0):
    return LengthSet(space_boundary_mm=width, host_wall_gross_mm=width,
                     material_present_mm=0.0, opening_mm=width)


def wall(length=3000.0):
    return LengthSet(space_boundary_mm=length, host_wall_gross_mm=length,
                     material_present_mm=length, opening_mm=0.0)


def test_a_doorway_is_four_different_facts():
    """Zero actual material, a real opening, a valid space closure, and part of
    the gross host-wall line. Collapsing them makes at least three trades
    wrong."""
    d = door()
    assert d.of(MATERIAL_PRESENT_LENGTH) == 0.0
    assert d.of(OPENING_LENGTH) == 1054.0
    assert d.of(SPACE_BOUNDARY_LENGTH) == 1054.0
    assert d.of(HOST_WALL_GROSS_LENGTH) == 1054.0


def test_material_length_is_not_the_only_length_a_quantity_may_read():
    """The previous round said it was. 23010's own manual benchmark measures
    GROSS perimeter and deducts openings later, so the door span belongs to
    the gross line."""
    assert basis_for("GROSS_PLASTER") == HOST_WALL_GROSS_LENGTH
    assert basis_for("GROSS_CERAMIC_WALL") == HOST_WALL_GROSS_LENGTH
    assert basis_for("GROSS_PERIMETER") == SPACE_BOUNDARY_LENGTH
    assert basis_for("PHYSICAL_WALL_MATERIAL") == MATERIAL_PRESENT_LENGTH


def test_skirting_follows_neither_the_space_boundary_nor_the_material():
    """A doorway removes skirting; fixed joinery may too. It needs its own
    approved rule."""
    assert basis_for("SKIRTING") == SKIRTING_ELIGIBLE_LENGTH
    assert door().skirting_basis == RULE_REQUIRED
    assert door().of(SKIRTING_ELIGIBLE_LENGTH) is None


def test_an_unestablished_basis_is_never_reported_as_zero():
    """An unestablished basis and a measured zero are different facts, and a
    quantity built on the wrong one is wrong in a way nobody notices."""
    with pytest.raises(LengthBasisError, match="NOT zero"):
        door().require(SKIRTING_ELIGIBLE_LENGTH)
    # while a measured zero comes back as a number
    assert door().require(MATERIAL_PRESENT_LENGTH) == 0.0


def test_a_use_with_no_declared_basis_may_not_release_a_number():
    with pytest.raises(LengthBasisError, match="declared a measurement basis"):
        basis_for("VIBES")


def test_an_unknown_basis_is_refused():
    with pytest.raises(LengthBasisError, match="unknown length basis"):
        door().of("SOME_LENGTH")


def test_the_net_uses_are_the_ones_that_deduct_openings():
    assert deducts_openings("NET_CERAMIC_WALL")
    assert deducts_openings("SKIRTING")
    assert not deducts_openings("GROSS_PLASTER")
    assert not deducts_openings("FLOOR_AREA")


def test_every_basis_is_named_and_distinct():
    assert len(BASES) == 5
    assert len(set(BASES)) == 5


def test_a_wall_has_all_four_lengths_coinciding():
    w = wall()
    assert w.of(MATERIAL_PRESENT_LENGTH) == w.of(HOST_WALL_GROSS_LENGTH)
    assert w.of(OPENING_LENGTH) == 0.0
