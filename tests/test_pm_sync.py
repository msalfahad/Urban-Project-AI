"""Tests for E14 — PM Sync.

Prove that a document we write is shaped exactly like the app's BoqItemModel and
that the app will compute the quantity we intended.
"""

import pytest

from engine.pm_sync import (
    ApprovedBoqLine,
    BOQ_ITEM_FIELDS,
    measurement_to_formula,
    to_boq_item_doc,
    expected_quantity,
    sync_boq,
)


def _line(**kw):
    base = dict(
        project_id="p1",
        group_id="g1",
        package_id="pkg1",
        package_name="Blockwork",
        name="Plaster to wall W1",
        unit="m2",
        count=1,
        dimensions_m=[6.0, 3.0],
        cost_rate=2.0,
        selling_rate=2.5,
    )
    base.update(kw)
    return ApprovedBoqLine(**base)


def test_document_has_exactly_the_apps_fields():
    doc = to_boq_item_doc(_line())
    assert set(doc.keys()) == BOQ_ITEM_FIELDS


def test_area_maps_to_area_formula():
    ft, m = measurement_to_formula(1, [6.0, 3.0])
    assert ft == "area"
    assert m == {"length": 6.0, "width": 3.0}


def test_volume_maps_to_volume_formula():
    ft, m = measurement_to_formula(1, [2.0, 3.0, 4.0])
    assert ft == "volume"
    assert m == {"length": 2.0, "width": 3.0, "height": 4.0}


def test_count_only_maps_to_simple():
    ft, m = measurement_to_formula(5, [])
    assert ft == "simple"
    assert m == {"qty": 5.0}


def test_multiple_instances_precompute_qty_as_simple():
    # 3 identical panels, each 2.0 x 1.5 = 3.0 m2 -> total 9.0 m2.
    ft, m = measurement_to_formula(3, [2.0, 1.5])
    assert ft == "simple"
    assert m["qty"] == pytest.approx(9.0)


def test_expected_quantity_matches_app_computation():
    # The app will recompute from the doc; it must equal count*product(dims).
    assert expected_quantity(_line(count=1, dimensions_m=[6.0, 3.0])) == 18.0
    assert expected_quantity(_line(count=5, dimensions_m=[4.0])) == pytest.approx(20.0)


def test_sync_writes_to_the_project_boqitems_subcollection():
    captured = []

    def writer(path, doc):
        captured.append((path, doc))
        return f"id{len(captured)}"

    result = sync_boq([_line(), _line(name="Skirting", count=5, dimensions_m=[4.0], unit="m")], writer)
    assert result.written == ["id1", "id2"]
    assert captured[0][0] == "projects/p1/boqItems"      # exact app path
    assert captured[1][1]["formulaType"] == "simple"     # linear run -> simple
    assert captured[1][1]["measurements"]["qty"] == pytest.approx(20.0)
