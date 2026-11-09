"""R-T533-1 on a non-Alsenan fixture: a 0.15 m black wall 4.00 x 3.00 m, units and joint mortar by hand; the module of
another thickness is never borrowed; missing / millimetre / unsourced inputs are HELD or refused, never 0."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t533"))
import block_module_v1 as BM  # noqa: E402

MIX = ("fixture mix: 8 bags + 1.1 m3 per m3", 8.0, 1.1)
E15 = BM.ModuleEntry("BLACK", 0.15, 0.39, 0.19, 0.010, 0.010, "fixture supplier sheet, 15 cm block", "SUPPLIER_RECORD")
E15_25 = BM.ModuleEntry("BLACK", 0.15, 0.39, 0.24, 0.010, 0.010, "fixture supplier sheet B", "SUPPLIER_RECORD")
E20 = BM.ModuleEntry("BLACK", 0.20, 0.39, 0.19, 0.010, 0.010, "fixture owner rule, 20 cm block", "OWNER_CONFIRMED")


def q(area, reg, t=0.15):
    return BM.quantities(area, reg, "BLACK", t, MIX[1], MIX[2], MIX[0])


def test_wall_4x3_by_hand():
    # 12.00 m2; module 0.40 x 0.20 -> 10 units per course x 15 courses = 150 units
    # mortar = 4.00 x 3.00 x 0.15 - 150 x 0.39 x 0.19 x 0.15 = 1.800 - 1.66725 = 0.13275 m3
    r = q(12.0, [E15, E20])
    assert r["status"] == "RESOLVED" and r["citation"] == E15.citation
    assert r["units_nr"] == pytest.approx(150.0, abs=1e-9)
    assert r["mortar_m3"] == pytest.approx(0.13275, abs=1e-12)
    assert r["cement_bags"] == pytest.approx(1.062, abs=1e-12)      # 0.13275 x 8
    assert r["sand_m3"] == pytest.approx(0.146025, abs=1e-12)       # 0.13275 x 1.1
    lay = BM.course_layout(4.00, 3.00, E15)
    assert lay["units_nr"] == 150 and lay["mortar_m3"] == pytest.approx(r["mortar_m3"], abs=1e-12)


def test_other_module_by_hand():
    # 0.39 x 0.24 + 10 mm -> 0.40 x 0.25: 10 x 12 courses = 120 units; 1.800 - 120 x 0.39 x 0.24 x 0.15 = 0.1152 m3
    r = q(12.0, [E15_25])
    assert r["units_nr"] == pytest.approx(120.0, abs=1e-9)
    assert r["mortar_m3"] == pytest.approx(0.1152, abs=1e-12)
    assert BM.course_layout(4.00, 3.00, E15_25)["units_nr"] == 120


def test_rotated_wall_same_area_same_count():
    # 3.20 long x 4.00 high (12.80 m2): 8 per course x 20 courses = 160 = 12.80 x 12.5
    assert BM.course_layout(3.20, 4.00, E15)["units_nr"] == 160
    assert q(12.8, [E15])["units_nr"] == pytest.approx(160.0, abs=1e-9)


def test_adverse_020_module_never_borrowed():
    r = q(12.0, [E20])
    assert r["status"] == "HELD"
    assert r["units_nr"] is None and r["mortar_m3"] is None and r["cement_bags"] is None and r["sand_m3"] is None
    assert "0.15 m black" in r["held"]
    assert r["units_nr"] != 150.0                       # the 0.20 module would have given 150


def test_adverse_missing_area_held_not_zero():
    r = q(None, [E15])
    assert r["status"] == "HELD" and r["units_nr"] is None and "laid area missing" in r["held"]


def test_adverse_millimetres_refused():
    with pytest.raises(BM.ModuleError):
        q(12.0, [E15], t=150)
    bad = BM.ModuleEntry("BLACK", 0.15, 390, 190, 0.010, 0.010, "mm sheet", "SUPPLIER_RECORD")
    with pytest.raises(BM.ModuleError):
        q(12.0, [bad])


def test_adverse_unsourced_entry_refused():
    for e in (BM.ModuleEntry("BLACK", 0.15, 0.39, 0.19, 0.01, 0.01, "", "SUPPLIER_RECORD"),
              BM.ModuleEntry("BLACK", 0.15, 0.39, 0.19, 0.01, 0.01, "analogy with 0.20", "ESTIMATED")):
        with pytest.raises(BM.ModuleError):
            q(12.0, [e])


def test_adverse_two_sources_disagree_conflict():
    r = q(12.0, [E15, E15_25])
    assert r["status"] == "CONFLICT" and r["units_nr"] is None


def test_adverse_mix_without_source_refused():
    with pytest.raises(BM.ModuleError):
        BM.quantities(12.0, [E15], "BLACK", 0.15, 8.0, 1.1, "")


def test_negative_area_refused():
    with pytest.raises(BM.ModuleError):
        q(-1.0, [E15])
