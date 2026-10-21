"""Tests for the unit-algebra core."""

import pytest

from engine.units import Quantity, Unit, UnitError


def test_length_times_length_is_area():
    result = Quantity(3.0, Unit.LENGTH) * Quantity(4.0, Unit.LENGTH)
    assert result.unit is Unit.AREA
    assert result.value == 12.0


def test_area_times_length_is_volume():
    result = Quantity(12.0, Unit.AREA) * Quantity(2.0, Unit.LENGTH)
    assert result.unit is Unit.VOLUME
    assert result.value == 24.0


def test_count_times_length_stays_length():
    result = Quantity(5.0, Unit.COUNT) * Quantity(2.0, Unit.LENGTH)
    assert result.unit is Unit.LENGTH
    assert result.value == 10.0


def test_scalar_multiplication_preserves_unit():
    result = Quantity(10.0, Unit.AREA) * 1.1  # e.g. a waste factor
    assert result.unit is Unit.AREA
    assert result.value == pytest.approx(11.0)


def test_adding_like_units_works():
    total = Quantity(10.0, Unit.AREA) + Quantity(5.5, Unit.AREA)
    assert total == Quantity(15.5, Unit.AREA)


def test_adding_unlike_units_is_refused():
    with pytest.raises(UnitError):
        Quantity(10.0, Unit.AREA) + Quantity(5.0, Unit.LENGTH)


def test_area_times_area_is_illegal():
    with pytest.raises(UnitError):
        Quantity(2.0, Unit.AREA) * Quantity(2.0, Unit.AREA)
