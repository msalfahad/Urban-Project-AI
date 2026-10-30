"""T-354 hand fixture villa K354 (not Alsenan): soil treatment scope and quantity rules SOIL_TREATMENT_V1.

Villa K354 (invented): an L-shaped slab on grade, fill top at +0.85, outline 12.00 x 9.00 minus a 5.00 x 3.00 notch
= 108.000 - 15.000 = 93.000 m2; footing pit A 2.00 x 2.00 = 4.000 m2 and pit B 1.50 x 1.50 = 2.250 m2, bottoms at
-1.70, both inside the slab plan; one trench 6.00 x 0.70 = 4.200 m2, bottom -1.00, inside the slab plan; pit sides HELD
(formation depth a bound). Specification clause 02-361 line 3.1 (invented) requires treatment.
  PLAN basis      : 93.000 m2 (pits and trench inside the plan are not added)
  SURFACES basis  : 93.000 + 4.000 + 2.250 + 4.200 = 103.450 m2 determinate + pit sides HELD by name
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t354"))
import soil_treatment_v1 as S  # noqa: E402

SHEETS = ["S-1", "S-2", "A-1"]
SEARCH = [{"sheet": s, "searched": True, "requires": []} for s in SHEETS]
SLAB = [(0, 0), (12, 0), (12, 9), (5, 9), (5, 6), (0, 6)]


def spec(basis):
    return {"kind": "SPECIFICATION", "document": "K354 specification", "clause": "02-361", "ref": "line 3.1",
            "basis": basis}


def zones(slab=None, unit="m"):
    return [
        {"id": "ZS", "surface": "SLAB_ON_GRADE_FILL_TOP", "level_m": 0.85, "outline": slab or SLAB, "unit": unit},
        {"id": "PA", "surface": "PIT_BOTTOM", "level_m": -1.70, "area_m2": 4.0, "inside_plan_of": "ZS"},
        {"id": "PB", "surface": "PIT_BOTTOM", "level_m": -1.70, "area_m2": 2.25, "inside_plan_of": "ZS"},
        {"id": "T1", "surface": "TRENCH_BOTTOM", "level_m": -1.00, "area_m2": 4.2, "inside_plan_of": "ZS"},
    ]


def required(basis):
    return S.scope_status(SEARCH, SHEETS, sources=[spec(basis)])


# ---- normal cases -------------------------------------------------------------------------------------------------

def test_plan_basis_counts_the_plan_once():
    q = S.zones_quantity(required("PLAN"), zones(), "PLAN")
    assert q["determinate_m2"] == pytest.approx(93.0, abs=1e-6) and q["status"] == "DETERMINATE"
    assert [r["state"] for r in q["rows"]] == ["DETERMINATE"] + ["INSIDE_PLAN_NOT_ADDED"] * 3


def test_surfaces_basis_each_surface_once_with_held_sides():
    zs = zones() + [{"id": "PA-S", "surface": "PIT_SIDE", "level_m": None, "area_m2": None,
                     "held_reason": "formation AT_MOST bound, depth not printed"}]
    q = S.zones_quantity(required("SURFACES"), zs, "SURFACES")
    assert q["determinate_m2"] == pytest.approx(103.45, abs=1e-6)
    assert q["status"] == "HELD" and q["held"] == ["PA-S"]
    assert next(r for r in q["rows"] if r["id"] == "PA-S")["m2"] is None


def test_mirror_rotation_and_mm_give_the_same_area():
    mirrored = [(-x, y) for x, y in SLAB]
    rotated = [(-y, x) for x, y in SLAB]
    in_mm = [(x * 1000, y * 1000) for x, y in SLAB]
    for outline, unit in ((mirrored, "m"), (rotated, "m"), (in_mm, "mm")):
        q = S.zones_quantity(required("PLAN"), zones(outline, unit), "PLAN")
        assert q["determinate_m2"] == pytest.approx(93.0, abs=1e-6)


def test_overlap_deduction_between_zones_at_one_level():
    zs = [{"id": "Z1", "surface": "SLAB_ON_GRADE_FILL_TOP", "level_m": 0.85, "area_m2": 20.0},
          {"id": "Z2", "surface": "SLAB_ON_GRADE_FILL_TOP", "level_m": 0.85, "area_m2": 6.0}]
    q = S.zones_quantity(required("SURFACES"), zs, "SURFACES", deductions=[{"from": "Z1", "of": "Z2", "area_m2": 1.5}])
    assert q["determinate_m2"] == pytest.approx(24.5, abs=1e-6)


def test_no_source_all_sheets_searched_is_not_in_drawn_scope_never_zero():
    r = S.scope_status(SEARCH, SHEETS)
    assert r["status"] == "NOT_IN_DRAWN_SCOPE" and r["area_m2"] is None


# ---- adverse cases ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["USUAL_PRACTICE", "TYPICAL_SPEC_OTHER_PROJECT", "REFERENCE_BOOK", "FREELANCER_ROW",
                                  "ASSUMED"])
def test_treatment_assumed_without_a_source_is_refused(kind):
    with pytest.raises(S.RefusedInput):
        S.scope_status(SEARCH, SHEETS, sources=[dict(spec("PLAN"), kind=kind)])


def test_source_without_note_or_clause_reference_is_refused():
    with pytest.raises(S.RefusedInput):
        S.scope_status(SEARCH, SHEETS, sources=[dict(spec("PLAN"), ref="")])


def test_convention_area_without_source_is_refused():
    with pytest.raises(S.RefusedInput):
        S.scope_status(SEARCH, SHEETS, convention_area_m2=470.55)


def test_quantity_under_not_in_scope_is_refused():
    with pytest.raises(S.RefusedInput):
        S.zones_quantity(S.scope_status(SEARCH, SHEETS), zones(), "PLAN")


def test_unsearched_sheet_leaves_unknown():
    r = S.scope_status(SEARCH[:2], SHEETS)
    assert r["status"] == "UNKNOWN" and r["unsearched"] == ["A-1"] and r["area_m2"] is None


def test_requiring_note_without_source_record_is_refused():
    srch = [dict(SEARCH[0], requires=["7"])] + SEARCH[1:]
    with pytest.raises(S.RefusedInput):
        S.scope_status(srch, SHEETS)


def test_pit_bottom_counted_again_with_the_slab_plan_is_refused():
    zs = zones()
    zs[1] = {k: v for k, v in zs[1].items() if k != "inside_plan_of"}
    with pytest.raises(S.RefusedInput):
        S.zones_quantity(required("PLAN"), zs, "PLAN")


def test_vertical_face_under_plan_basis_is_refused():
    zs = zones() + [{"id": "PA-S", "surface": "PIT_SIDE", "level_m": None, "area_m2": 9.0}]
    with pytest.raises(S.RefusedInput):
        S.zones_quantity(required("PLAN"), zs, "PLAN")


def test_basis_not_stated_by_the_source_is_refused():
    with pytest.raises(S.RefusedInput):
        S.zones_quantity(required("PLAN"), zones(), "SURFACES")


def test_held_zone_written_as_zero_is_refused():
    zs = zones() + [{"id": "PA-S", "surface": "PIT_SIDE", "level_m": -1.0, "area_m2": 0.0, "held_reason": "depth"}]
    with pytest.raises(S.RefusedInput):
        S.zones_quantity(required("SURFACES"), zs, "SURFACES")


def test_zone_twice_is_refused():
    with pytest.raises(S.RefusedInput):
        S.zones_quantity(required("SURFACES"), zones() + [zones()[1]], "SURFACES")


def test_overlap_deducted_between_different_levels_is_refused():
    with pytest.raises(S.RefusedInput):
        S.zones_quantity(required("SURFACES"), zones(), "SURFACES",
                         deductions=[{"from": "ZS", "of": "PA", "area_m2": 4.0}])


def test_non_treatment_layer_is_refused():
    zs = zones() + [{"id": "WP", "surface": "EARTH_CONTACT_WATERPROOFING", "level_m": 0.0, "area_m2": 50.0}]
    with pytest.raises(S.RefusedInput):
        S.zones_quantity(required("SURFACES"), zs, "SURFACES")


def test_unstated_unit_is_refused():
    with pytest.raises(S.RefusedInput):
        S.polygon_area(SLAB, "ft")
