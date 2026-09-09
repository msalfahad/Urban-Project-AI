"""Tests for E6 Alerts, E8 Waste, E9 Cooling, E17 Preliminaries."""

from datetime import date

import pytest

from engine.alerts import Thresholds, check_variance, check_rate_age
from engine.waste import waste_factor, gross_quantity, family_of
from engine.cooling import tons_for_area, select_units, floor_load
from engine.preliminaries import preliminaries


# ---- E6 Alerts ----
def test_variance_within_limit_is_ok():
    assert check_variance(105, 100) is None       # 5% < 10%


def test_variance_beyond_limit_flags():
    a = check_variance(120, 100)
    assert a and a.kind == "variance" and a.severity == "review"


def test_stale_rate_blocks():
    a = check_rate_age(date(2026, 1, 1), as_of=date(2026, 6, 1))
    assert a and a.severity == "block"


def test_fresh_rate_ok():
    assert check_rate_age(date(2026, 5, 20), as_of=date(2026, 6, 1)) is None


# ---- E8 Waste ----
def test_marble_waste_higher_than_block():
    assert waste_factor("marble") > waste_factor("block")


def test_gross_quantity_applies_waste():
    assert gross_quantity(100, "ceramic") == pytest.approx(110.0)   # 10%


def test_gross_rounds_up_to_pack():
    # 100 * 1.10 = 110, round up to 25 -> 125
    assert gross_quantity(100, "ceramic", round_up_to=25) == 125


def test_family_from_arabic():
    assert family_of("رخام درج") == "marble"
    assert family_of("طابوق ابيض") == "block"


# ---- E9 Cooling ----
def test_cooling_tons_scales_with_area():
    t = tons_for_area(100, "living")   # 100 * 600 / 12000 = 5 tons
    assert round(t, 2) == 5.0


def test_select_units_covers_load():
    units = select_units(5.0)
    assert sum(units) >= 5.0


def test_floor_load_picks_units():
    fl = floor_load("Ground", 120, "living")
    assert fl.tons > 0 and fl.units and sum(fl.units) >= fl.tons


# ---- E17 Preliminaries ----
def test_preliminaries_scale_with_duration():
    p32 = preliminaries(duration_weeks=32)
    p64 = preliminaries(duration_weeks=64)
    # longer programme costs more preliminaries (time-based items)
    assert p64.total > p32.total


def test_preliminaries_include_lump_and_time():
    p = preliminaries(duration_weeks=10)
    bases = {i.basis for i in p.items}
    assert "per_week" in bases and "lump" in bases
    assert p.total > 0
