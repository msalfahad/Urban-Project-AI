"""T-357 hand fixture, Villa P (synthetic, not Alsenan): a plot with TWO printed ground levels, a printed clearance
note, coverage percentages, EG-shift coefficients; adverse cases.

Villa P by hand (drawing units mm):
- plot boundary 20.00 x 30.00 m, corners P1 (street-left), P2 (street-right), P3 (rear-right), P4 (rear-left):
  area 600.000 m2. Mirrored / reversed vertex order: same 600.000 m2. An L-shaped plot 20 x 30 minus a 5 x 10 notch:
  600 - 50 = 550.000 m2.
- printed ground marks: +0.00 at P1 and P2 (street), +0.60 at P3 and P4 (rear): two printed values -> SLOPING, no
  single EG value (a mean 0.30 is never produced); per corner 0.00 / 0.00 / 0.60 / 0.60.
- coverage: GF 330.00 m2 printed '55.00 %' (330 / 600 = 55.000 %), 1F 247.50 printed '41.25 %': CONSISTENT;
  a printed '58.00 %' for 330.00 is a CONFLICT (implies a 568.97 m2 plot).
- clearance: sheet S-1 note 3 prints site clearance -> PRINTED_SCOPE (S-1 note 3), area from that note, not computed.
- EG-shift coefficients per metre of EG rise: a 12.00 m2 pit to an absolute printed formation +12.000; a 12.00 m2 pit
  bounded 'not less than 1.5 m below existing ground' 0.000; fill above EG to an absolute slab soffit, plan 80.00 m2:
  -80.000; a held zone: None.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t357"))
import ground_reference_v1 as G  # noqa: E402

CORNERS = ["P1", "P2", "P3", "P4"]


def mark(kind, value, corner=None, unit="m", handle="h", **kw):
    return dict(kind=kind, value=value, unit=unit, sheet="A-1", handle=handle, corner=corner, **kw)


def test_plot_area_rectangle_mirror_and_l_shape():
    rect = [(0, 0), (20000, 0), (20000, 30000), (0, 30000)]
    assert G.polygon_area(rect, "mm") == pytest.approx(600.0, abs=1e-9)
    assert G.polygon_area(list(reversed(rect)), "mm") == pytest.approx(600.0, abs=1e-9)
    mirrored = [(-x, y) for x, y in rect]
    assert G.polygon_area(mirrored, "mm") == pytest.approx(600.0, abs=1e-9)
    ell = [(0, 0), (20, 0), (20, 20), (15, 20), (15, 30), (0, 30)]
    assert G.polygon_area(ell, "m") == pytest.approx(550.0, abs=1e-9)


def test_two_printed_ground_levels_are_sloping_never_averaged():
    marks = [mark("PLOT_EDGE_GROUND", 0.0, "P1"), mark("PLOT_EDGE_GROUND", 0.0, "P2"),
             mark("PLOT_EDGE_GROUND", 600, "P3", unit="mm"), mark("PLOT_EDGE_GROUND", 0.6, "P4")]
    r = G.existing_ground_reference(marks, CORNERS)
    assert r["status"] == "SLOPING" and r["value_m"] is None
    assert r["per_corner"] == {"P1": 0.0, "P2": 0.0, "P3": 0.6, "P4": 0.6}


def test_flat_plot_all_corners_derived_and_spot_level_printed():
    marks = [mark("PLOT_EDGE_GROUND", 0.0, c) for c in CORNERS]
    assert G.existing_ground_reference(marks, CORNERS)["status"] == "DERIVED"
    spot = marks + [mark("EXISTING_GROUND_SPOT", 0.0, None)]
    assert G.existing_ground_reference(spot, CORNERS)["status"] == "PRINTED"


def test_adverse_unprinted_ground_is_held_not_zero():
    marks = [mark("NAMED_NO_VALUE", None), mark("FINISHED_GROUND", 0.15), mark("FINISHED_FLOOR", 1.0)]
    r = G.existing_ground_reference(marks, CORNERS)
    assert r["status"] == "HELD" and r["value_m"] is None


def test_adverse_corner_missing_is_held():
    marks = [mark("PLOT_EDGE_GROUND", 0.0, c) for c in CORNERS[:3]] + [mark("CUT_GROUND_LINE", 0.0)]
    r = G.existing_ground_reference(marks, CORNERS)
    assert r["status"] == "HELD" and r["value_m"] is None and r["per_corner"]["P4"] is None


def test_adverse_finished_level_offered_as_ground_refused():
    with pytest.raises(G.RefusedInput):
        G.existing_ground_reference([mark("FINISHED_GROUND", 0.15, "P1", offered_as_ground=True)], CORNERS)


def test_adverse_undeclared_unit_refused():
    with pytest.raises(G.RefusedInput):
        G.existing_ground_reference([mark("PLOT_EDGE_GROUND", 0.0, "P1", unit=None)], CORNERS)
    with pytest.raises(G.RefusedInput):
        G.polygon_area([(0, 0), (1, 0), (1, 1)], "ft")


def test_coverage_consistent_and_conflict():
    ok = G.check_coverage_percentages(600.0, [{"name": "GF", "area_m2": 330.0, "pct": 55.0},
                                              {"name": "1F", "area_m2": 247.5, "pct": 41.25}])
    assert ok["status"] == "CONSISTENT"
    bad = G.check_coverage_percentages(600.0, [{"name": "GF", "area_m2": 330.0, "pct": 58.0}])
    assert bad["status"] == "CONFLICT" and bad["rows"][0]["implied_plot_m2"] == pytest.approx(568.966, abs=1e-3)


def test_clearance_printed_scope_absent_unknown_and_convention_refused():
    sheets = ["S-1", "S-2", "A-1"]
    printed = G.clearance_scope([{"sheet": "S-1", "searched": True, "clearance_notes": ["3"]},
                                 {"sheet": "S-2", "searched": True, "clearance_notes": []},
                                 {"sheet": "A-1", "searched": True, "clearance_notes": []}], sheets)
    assert printed["status"] == "PRINTED_SCOPE" and printed["refs"] == ["S-1 note 3"] and printed["area_m2"] is None
    none = [{"sheet": s, "searched": True, "clearance_notes": []} for s in sheets]
    assert G.clearance_scope(none, sheets)["status"] == "NOT_IN_DRAWN_SCOPE"
    assert G.clearance_scope(none[:2], sheets)["status"] == "UNKNOWN"
    with pytest.raises(G.RefusedInput):  # plot 600 - footprint 330 = 270 m2 is a convention, not a scope
        G.clearance_scope(none, sheets, convention_area_m2=270.0)


def test_eg_shift_coefficients():
    c = G.eg_shift_coefficients([
        {"id": "pit abs", "plan_m2": 12.0, "side": "BELOW_EG", "reference": "ABSOLUTE"},
        {"id": "pit rel", "plan_m2": 12.0, "side": "BELOW_EG", "reference": "RELATIVE_TO_EG"},
        {"id": "fill", "plan_m2": 80.0, "side": "ABOVE_EG", "reference": "ABSOLUTE"},
        {"id": "held", "plan_m2": None, "side": "ABOVE_EG", "reference": "ABSOLUTE"},
        {"id": "held2", "plan_m2": 5.0, "side": "BELOW_EG", "reference": "HELD"}])
    assert [x["coef_m3_per_m"] for x in c] == [12.0, 0.0, -80.0, None, None]
