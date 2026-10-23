"""T-214 on the development villa (research/agents_t214: metres measured on the architect's sections, Drive titles and
views only). What the drawings establish: every dry floor band cut by SECTION A-A / B-B draws an unhatched 0.05 m layer
between the FFL marker line and the hatched slab (vector DWF and both current-issue scans agree within 3 mm), so
b = 0.05 DRAWING-CONFIRMED on GF, annex, 1F and 2F dry zones; wet, sunken and roof / terrace zones stay HELD; the T-189
B20 / B23 condition is PROVEN on the drawing basis and NOT PROVEN on the owner's allowances (never a datum); the
summary reproduces byte for byte."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t214"))
import t214_alsenan_check as A  # noqa: E402


@pytest.fixture(scope="module")
def res():
    return A.build()


def _z(res, zid):
    return next(z for z in res["zones"] if z["zone"] == zid)


@pytest.mark.parametrize("zid,top", [("GF-DRY", 0.95), ("ANNEX-DRY", 0.25), ("1F-DRY", 5.45), ("2F-DRY", 9.65)])
def test_dry_floors_drawing_confirmed(res, zid, top):
    z = _z(res, zid)
    assert z["drawing_status"] == "DRAWING-CONFIRMED"
    assert z["drawing_b_m"] == pytest.approx(0.05, abs=res["plot_resolution_m"])
    assert z["slab_top_drawing"] == pytest.approx(top, abs=res["plot_resolution_m"])


@pytest.mark.parametrize("zid", ["GF-WET", "1F-SUNKEN", "2F-SUNKEN", "1F-TERRACE-ROOF", "2F-TERRACE-ROOF",
                                 "MAIN-ROOF", "ANNEX-ROOF"])
def test_other_zones_held_never_zero(res, zid):
    z = _z(res, zid)
    assert z["drawing_status"] == "HELD" and z["drawing_b_m"] is None and z["slab_top_drawing"] is None


def test_roof_constant_layer_refused(res):
    for zid in ("MAIN-ROOF", "ANNEX-ROOF", "2F-TERRACE-ROOF"):
        assert any(n.startswith("CONSTANT_LAYER_VS_FALLS") for n in _z(res, zid)["drawing_notes"])


def test_t189_condition(res):
    for c in res["conditions"]:
        assert c["DRAWING"].startswith("PROVEN")
        assert c["OWNER_MANUAL"].startswith("NOT PROVEN (ALLOWANCE_AS_DATUM")


def test_q43_is_an_allowance_beside_never_a_datum(res):
    q43 = next(o for o in _z(res, "1F-DRY")["owner_manual"] if o["rule"] == "Q-43")
    assert q43["scope"] == "WALL_HEIGHT_ALLOWANCE" and q43["usable_as_datum"] is False
    assert q43["residual_drawn_minus_owner_m"][0] == pytest.approx(-0.05, abs=0.002)


def test_level_chain_r3_effects(res):
    lc = res["level_chain"]
    assert lc["uses_changed"]["A4-STAIR-B20"]["R3"]["sensitivity"].startswith("difference inside the stated margin")
    assert lc["uses_changed"]["A4-STAIR-B23"]["R3"]["sensitivity"].startswith("difference inside the stated margin")
    # the neck top at the FFL stays a finished-as-structural use; the ground-beam top is now +0.95
    assert lc["uses_changed"]["A3-NECK-TOP"]["R3"]["code"] == "FINISHED_AS_STRUCTURAL"
    assert lc["datums_changed"]["GF-EXT-F8/GB_TOP"]["R3"] == [0.95, "DRAWING-CONFIRMED"]
    assert not any(k.startswith(("1F-WET", "2F-WET")) for k in lc["datums_changed"])


def test_summary_reproduces():
    assert A.main(["--check"]) == 0
