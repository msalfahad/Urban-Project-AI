"""Tests pinning our formula mirror to the web app's BoqFormulaEngine.

If any of these fail, our Python engine has drifted from the Dart engine in
Urban Projects Manager and BOQ quantities would disagree — re-sync before
writing anything to the app's Firestore.
"""

import pytest

from engine.boq_formula import compute_quantity, FIELDS_FOR


def test_simple_takes_qty_directly():
    assert compute_quantity("simple", {"qty": 7.0}) == 7.0


def test_area_is_length_times_width():
    assert compute_quantity("area", {"length": 6.0, "width": 3.0}) == 18.0


def test_volume_is_length_times_width_times_height():
    assert compute_quantity("volume", {"length": 2.0, "width": 3.0, "height": 4.0}) == 24.0


def test_perimeter_is_perimeter_times_height():
    assert compute_quantity("perimeter", {"perimeter": 20.0, "height": 3.0}) == 60.0


def test_missing_field_reads_as_zero():
    # Matches the app's `values['width'] ?? 0`.
    assert compute_quantity("area", {"length": 6.0}) == 0.0


def test_unknown_type_falls_through_to_simple():
    assert compute_quantity("mystery", {"qty": 5.0}) == 5.0


def test_field_lists_match_the_app():
    assert FIELDS_FOR["area"] == ["length", "width"]
    assert FIELDS_FOR["volume"] == ["length", "width", "height"]
    assert FIELDS_FOR["perimeter"] == ["perimeter", "height"]
    assert FIELDS_FOR["simple"] == ["qty"]
