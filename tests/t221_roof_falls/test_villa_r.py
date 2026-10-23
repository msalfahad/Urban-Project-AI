"""T-221 ROOF_FALLS_V1 on the hand fixture villa T221-R (not the development villa). Hand truth (metres, fall 1 %):

    R1  roof 12.00 x 5.00, outlets at both south corners (0,0) and (12,0)
        far point (6, 5): EIKONAL 0.01 x sqrt(6^2 + 5^2) = 0.0781; AXIS 0.01 x (6 + 5) = 0.110
        mean rise AXIS 0.01 x (3 + 2.5) = 0.055; EIKONAL from the closed form of the mean corner distance of a 6 x 5
        rectangle; catchments 30 / 30 m2
    R2  L-shaped roof (0,0)-(6,0)-(6,2)-(2,2)-(2,6)-(0,6), one outlet (6,0): the path from (0,6) bends at the reflex
        corner (2,2): EIKONAL 0.01 x (sqrt(20) + sqrt(20)) = 0.0894; AXIS 0.01 x 12 = 0.120
    R3  terrace strip 20.00 x 1.30, one outlet (20,0): EIKONAL 0.01 x sqrt(400 + 1.69) = 0.2004; AXIS 0.213
    Parapet upstand 0.30: R3 with t0 0.05 and membrane 0.01 -> NOT PROVEN while a layer is unknown; PROVEN with all
    layers printed (0.30 - 0.213 - 0.06 = 0.027 margin); VIOLATED with t0 0.10 + 0.213 >= 0.30 ... (0.2004 + 0.10 + 0.01)

Adverse: no outlet drawn; zero fall (a constant layer); an outlet outside the roof; mirror / rotation / mm input give
the same rise; a constant drawn layer offered as the roof build-up; a dry-floor layer carried to a wet zone; a finished
level offered as the structural top; an owner allowance used as a datum; a roof with falls and no t0 stays HELD (never 0).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t221"))
import roof_falls_v1 as R  # noqa: E402

RECT = [(0, 0), (12, 0), (12, 5), (0, 5)]
LSHAPE = [(0, 0), (6, 0), (6, 2), (2, 2), (2, 6), (0, 6)]
STRIP = [(0, 0), (20, 0), (20, 1.3), (0, 1.3)]


def _mean_corner(a, b):
    d = math.hypot(a, b)
    return (2 * a * b * d + a ** 3 * math.log((b + d) / a) + b ** 3 * math.log((a + d) / b)) / 6 / (a * b)


def test_r1_two_outlets_hand_values():
    r = R.falls_field(RECT, [(0, 0), (12, 0)], 0.01)
    ek, ax = r["models"]["EIKONAL"], r["models"]["AXIS"]
    assert ek["rise_max_m"] == pytest.approx(0.01 * math.hypot(6, 5), abs=5e-4)
    assert ax["rise_max_m"] == pytest.approx(0.110, abs=5e-4)
    assert ax["rise_mean_m"] == pytest.approx(0.055, abs=5e-4)
    assert ek["rise_mean_m"] == pytest.approx(0.01 * _mean_corner(6, 5), abs=5e-4)
    assert ek["catchment_m2"] == pytest.approx([30.0, 30.0], abs=0.2)
    assert ax["volume_above_t0_m3"] == pytest.approx(0.055 * 60, abs=0.02)


def test_r2_reflex_corner_bends_the_path():
    r = R.falls_field(LSHAPE, [(6, 0)], 0.01)
    assert r["models"]["EIKONAL"]["rise_max_m"] == pytest.approx(0.01 * 2 * math.sqrt(20), abs=5e-4)
    assert r["models"]["AXIS"]["rise_max_m"] == pytest.approx(0.120, abs=5e-4)
    assert r["models"]["EIKONAL"]["far_point"] == pytest.approx([0.0, 6.0], abs=0.06)


def test_r3_strip_bounds_nearly_coincide():
    r = R.falls_field(STRIP, [(20, 0)], 0.01)
    lo, hi = r["models"]["EIKONAL"]["rise_max_m"], r["models"]["AXIS"]["rise_max_m"]
    assert lo == pytest.approx(0.2004, abs=5e-4) and hi == pytest.approx(0.213, abs=5e-4)
    assert lo <= hi


def test_bounds_are_ordered_on_every_fixture():
    for o, d in ((RECT, [(0, 0), (12, 0)]), (LSHAPE, [(6, 0)]), (STRIP, [(20, 0)])):
        m = R.falls_field(o, d, 0.01)["models"]
        assert m["EIKONAL"]["rise_max_m"] <= m["AXIS"]["rise_max_m"]
        assert m["EIKONAL"]["rise_mean_m"] <= m["AXIS"]["rise_mean_m"]


def test_mirror_rotation_and_units_do_not_change_the_rise():
    base = R.falls_field(LSHAPE, [(6, 0)], 0.01)["models"]
    mir = R.falls_field([(-x, y) for x, y in LSHAPE], [(-6, 0)], 0.01)["models"]
    rot = R.falls_field([(-y, x) for x, y in LSHAPE], [(0, 6)], 0.01)["models"]
    mm = R.falls_field([(x * 1000, y * 1000) for x, y in LSHAPE], [(6000, 0)], 0.01, units="mm")["models"]
    for other in (mir, rot, mm):
        for m in R.MODELS:
            assert other[m]["rise_max_m"] == pytest.approx(base[m]["rise_max_m"], abs=5e-4)


def test_owner_fallback_half_percent_halves_the_rise():
    a = R.falls_field(RECT, [(0, 0), (12, 0)], 0.01)["models"]["AXIS"]["rise_max_m"]
    b = R.falls_field(RECT, [(0, 0), (12, 0)], 0.005)["models"]["AXIS"]["rise_max_m"]
    assert b == pytest.approx(a / 2, abs=5e-4)


@pytest.mark.parametrize("drains,slope,msg", [([], 0.01, "DRAINS_NOT_DRAWN"), ([(0, 0)], 0.0, "CONSTANT_LAYER_VS_FALLS"),
                                              ([(30, 30)], 0.01, "outside")])
def test_adverse_falls_inputs_refused(drains, slope, msg):
    with pytest.raises(ValueError, match=msg):
        R.falls_field(RECT, drains, slope)


def test_unknown_units_refused():
    with pytest.raises(ValueError, match="units"):
        R.falls_field(RECT, [(0, 0)], 0.01, units="cm")


def test_parapet_bound_three_outcomes():
    rise = (0.2004, 0.213)
    assert R.evaluate_parapet(rise, 0.30, t0=0.05, layers={"membrane": None})["status"] == "NOT PROVEN"
    p = R.evaluate_parapet(rise, 0.30, t0=0.05, layers={"membrane": 0.01})
    assert p["status"] == "PROVEN" and p["margin_m"] == pytest.approx(0.027, abs=1e-4)
    assert R.evaluate_parapet(rise, 0.30, t0=0.10, layers={"membrane": 0.01})["status"] == "VIOLATED"
    held = R.evaluate_parapet(rise, 0.30, t0=None)
    assert held["status"] == "NOT PROVEN" and "t0 (screed at the outlet)" in held["unknown"]


def _zone(**kw):
    z = {"zone_id": "Z", "kind": "ROOF", "ffl": {"value": 7.45, "kind": "FINISHED_ROOF"}, "evidence": [], "owner": []}
    z.update(kw)
    return z


def test_roof_with_falls_and_no_t0_is_held_never_zero():
    f = R.falls_field(RECT, [(0, 0), (12, 0)], 0.01)
    s = R.zone_status(_zone(falls=f, t0=None))
    assert s["status"] == "HELD" and s["b"] is None and s["structural_top"] is None
    assert s["falls_rise_max_m"] == [f["models"]["EIKONAL"]["rise_max_m"], f["models"]["AXIS"]["rise_max_m"]]
    assert any("t0" in m for m in s["missing"]) and any("reference point" in m for m in s["missing"])


def test_printed_structural_top_confirms_the_zone():
    s = R.zone_status(_zone(evidence=[{"source": "PRINTED_TOP", "kind": "SLAB_TOP", "value": 7.30}]))
    assert s["status"] == "DRAWING-CONFIRMED" and s["b"] == pytest.approx(0.15)


@pytest.mark.parametrize("zone,msg", [
    (_zone(evidence=[{"source": "DRAWN_LAYER", "cut_zone_kind": "ROOF", "thickness": 0.05}]), "CONSTANT_LAYER_VS_FALLS"),
    (_zone(kind="WET", ffl={"value": 3.95, "kind": "FFL"},
           evidence=[{"source": "DRAWN_LAYER", "cut_zone_kind": "DRY", "thickness": 0.05}]), "DRY_LAYER_TO_WET"),
    (_zone(kind="SUNKEN", ffl={"value": 3.95, "kind": "FFL"},
           evidence=[{"source": "DRAWN_LAYER", "cut_zone_kind": "DRY", "thickness": 0.05}]), "DRY_LAYER_TO_WET"),
    (_zone(evidence=[{"source": "PRINTED_TOP", "kind": "FINISHED_ROOF", "value": 7.45}]), "FINISHED_AS_STRUCTURAL"),
    (_zone(owner=[{"rule": "Q-43", "scope": "WALL_HEIGHT_ALLOWANCE", "used_as": "LEVEL_DATUM"}]), "ALLOWANCE_AS_DATUM"),
    (_zone(ffl={"value": 7.30, "kind": "SLAB_TOP"}), "finished level"),
])
def test_adverse_zone_refusals(zone, msg):
    with pytest.raises(ValueError, match=msg):
        R.zone_status(zone)


def test_wet_and_sunken_without_evidence_held():
    w = R.zone_status(_zone(kind="WET", ffl={"value": 3.95, "kind": "FFL"}))
    s = R.zone_status(_zone(kind="SUNKEN", ffl={"value": 3.95, "kind": "FFL"}, drop=None))
    assert w["status"] == s["status"] == "HELD" and w["b"] is None and s["b"] is None
    assert "the printed drop of the sunken panel" in s["missing"]
