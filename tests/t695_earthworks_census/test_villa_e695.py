"""T-695 EARTHWORKS_CENSUS_V1 on the hand villa E695 (not Alsenan): normal and adverse cases, numbers by hand.

Villa E695: one strap 0.60 x 0.50 joining two pits, 3.00 m clear between the two pit excavation plans; footing
underside 1.40 m below existing ground (EG +-0.00). Neat strap plan B = 0.60 x 3.00 = 1.80 m2; the strap grown 0.10 on
both sides BP = 0.80 x 3.00 = 2.40 m2.
  R1 (no blinding):  cut 1.80 x 1.40 = 2.52; strap 1.80 x 0.50 = 0.90; fill 1.62; fill depth 0.90 -> 6 layers @ 0.15
  R2 (blinding):     cut 2.40 x 1.50 = 3.60; strap 0.90 + blinding 0.24 = 1.14; fill 2.46; depth 1.40 -> 10 layers
  R3 (+ underlay):   cut 2.40 x 1.57 = 3.768; + underlay 1.80 x 0.07 = 0.126 -> solids 1.266; fill 2.502
  envelope: cut 2.52 .. 3.768; fill 1.62 .. 2.502; footprint 1.80 .. 2.40 m2; layers 6 .. 10
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t695"))
import earthworks_census_v1 as E  # noqa: E402

LIFT = 0.15


def _scen():
    return [
        E.trench_scenario("R1", 1.80, 1.40, {"strap": 0.90}, 0.0, 0.90, LIFT),
        E.trench_scenario("R2", 2.40, 1.50, {"strap": 0.90, "blinding": 0.24}, 0.0, 1.40, LIFT),
        E.trench_scenario("R3", 2.40, 1.57, {"strap": 0.90, "blinding": 0.24, "underlay": 0.126}, 0.0, 1.40, LIFT),
    ]


def test_strap_trench_by_hand():
    r1, r2, r3 = _scen()
    assert (r1["excavation_m3"], r1["backfill_m3"], r1["layers"]) == (2.52, 1.62, 6)
    assert (r2["excavation_m3"], r2["backfill_m3"], r2["layers"]) == (3.6, 2.46, 10)
    assert (r3["excavation_m3"], r3["backfill_m3"]) == (3.768, 2.502)
    env = E.envelope(_scen())
    assert env["excavation_m3"] == [2.52, 3.768] and env["backfill_m3"] == [1.62, 2.502]
    assert env["compaction_footprint_m2"] == [1.8, 2.4] and env["layers"] == [6, 10]
    assert env["excavation_m3_by"] == ["R1", "R3"]


def test_shared_cut_netted_once():
    # adverse: a ground beam on N.G. crosses the strap; its 0.10 blinding cut over 0.50 m2 is already on its own line
    r = E.trench_scenario("R2x", 2.40, 1.50, {"strap": 0.90, "blinding": 0.24}, 0.50 * 0.10, 1.40, LIFT)
    assert r["excavation_m3"] == 3.55 and r["netted_cut_m3"] == 0.05 and r["backfill_m3"] == 2.41


def test_mirror_and_rotation_do_not_matter():
    # the module takes plans and depths only: a mirrored / rotated strap gives the same numbers; scenario order is free
    a = E.envelope(_scen())
    b = E.envelope(list(reversed(_scen())))
    assert a["excavation_m3"] == b["excavation_m3"] and a["backfill_m3"] == b["backfill_m3"]


@pytest.mark.parametrize("args", [
    ("neg", -1.0, 1.4, {}),                    # negative plan
    ("mm", 1.80, 1400.0, {"strap": 0.9}),      # depth in mm read as m
    ("over", 1.80, 0.40, {"strap": 0.90}),     # solids exceed the cut
    ("nan", 1.80, float("nan"), {}),           # missing depth as NaN
    ("none", 1.80, None, {}),                  # missing depth -> refused, never 0
])
def test_adverse_trench(args):
    with pytest.raises(E.CensusError):
        E.trench_scenario(*args)


def test_envelope_refuses_empty_and_twice():
    with pytest.raises(E.CensusError):
        E.envelope([])
    s = _scen()
    with pytest.raises(E.CensusError):
        E.envelope([s[0], s[0]])


def test_layers():
    assert E.layers(0.90, 0.15) == 6 and E.layers(1.50, 0.15) == 10 and E.layers(1.10, 0.15) == 8
    assert E.layers(0.0, 0.15) == 0
    with pytest.raises(E.CensusError):
        E.layers(1.0, 0.0)


def test_zero_by_geometry():
    z, bottom, thr = E.zero_by_geometry(0.95, 0.40, 0.10)       # interior beam above EG: calculated 0
    assert z and bottom == 0.45 and thr == 0.85
    z, bottom, _ = E.zero_by_geometry(0.25, 0.40, 0.10)          # adverse: annex-like top +0.25 -> cut needed
    assert not z and bottom == -0.25
    z, _, _ = E.zero_by_geometry(0.95, 0.85, 0.10)               # exactly on EG: still 0
    assert z
    with pytest.raises(E.CensusError):
        E.zero_by_geometry(0.95, 0.0, 0.10)


def test_at_least():
    assert E.at_least_trench([("a", 2.0, 0.10), ("b", 1.0, 0.15)]) == {"kind": "AT_LEAST", "m3": 0.35}
    with pytest.raises(E.CensusError):
        E.at_least_trench([("a", -2.0, 0.10)])


def test_material_held_names_the_test():
    m = E.material_account({"excavation_in_situ": 10.0}, {"mdd": None, "insitu_dry_density": 1.70,
                                                          "loose_density": 1.40, "suitability": 1.0,
                                                          "target_density": 0.95})
    assert m["state"] == "HELD" and m["balance"] is None and m["geometry_m3"] == {"excavation_in_situ": 10.0}
    assert m["missing_tests"] == [E.MATERIAL_TESTS["mdd"]] and "ASTM D1557" in m["missing_tests"][0]
    full = E.material_account({"excavation_in_situ": 10.0}, {"mdd": 2.0, "insitu_dry_density": 1.7,
                                                             "loose_density": 1.4, "suitability": 1.0,
                                                             "target_density": 0.95})
    assert full["state"] == "INPUTS_COMPLETE" and "R-T505-1" in full["balance"]
    with pytest.raises(E.CensusError):
        E.material_account({"x": 1.0}, {"bulking": 1.25})          # a default factor is not a fact


# ---- census -----------------------------------------------------------------------------------------------------

def _idx():
    return [
        {"line_id": "L-1", "item_code": "STR.EARTH.EXCAVATION", "class": "RELEASED", "measured_net": 12.0,
         "held_low": None, "held_high": None, "unit": "m3", "element_id": "EW:B1-02:Z1-PITS"},
        {"line_id": "L-2", "item_code": "STR.EARTH.EXCAVATION", "class": "HELD", "measured_net": None,
         "held_low": 2.52, "held_high": 3.768, "unit": "m3", "element_id": "EW:B1-02:Z1-STRAP"},
        {"line_id": "L-3", "item_code": "STR.EARTH.BACKFILL", "class": "HELD", "measured_net": None,
         "held_low": None, "held_high": None, "unit": "m3", "element_id": "EW:B1-03:Z1-PITS"},
        {"line_id": "L-4", "item_code": "STR.EARTH.DISPOSAL", "class": "HELD", "measured_net": None,
         "held_low": None, "held_high": None, "unit": "m3", "element_id": "EW:B1-04:ALL"},
        {"line_id": "L-9", "item_code": "STR.CONC.FOOTING", "class": "RELEASED", "measured_net": 5.0,
         "held_low": None, "held_high": None, "unit": "m3", "element_id": "F1"},
    ]


def _reg():
    return {
        "EW:B1-02:Z1-PITS": {"cause": "MEASURABLE_NOW"},
        "EW:B1-02:Z1-STRAP": {"cause": "MEASURABLE_NOW", "secondary": ["DESIGNER"], "gap": "blinding under strap"},
        "EW:B1-03:Z1-PITS": {"cause": "DESIGNER", "gap": "beam section over the pits"},
        "EW:B1-04:ALL": {"cause": "NEEDS_TEST", "gap": "no density", "tests": [E.MATERIAL_TESTS["mdd"]]},
    }


def test_census_normal_and_mirror():
    rows = E.census(_idx(), _reg())
    assert [r["line_id"] for r in rows] == ["L-1", "L-2", "L-3", "L-4"]
    assert [r["bound"] for r in rows] == ["VALUE", "RANGE", "BLANK", "BLANK"]
    assert E.census_counts(rows) == {"B1-02|MEASURABLE_NOW": 2, "B1-03|DESIGNER": 1, "B1-04|NEEDS_TEST": 1}
    assert E.census(list(reversed(_idx())), _reg()) == rows


def _mut(fn):
    idx, reg = _idx(), _reg()
    fn(idx, reg)
    return idx, reg


@pytest.mark.parametrize("fn", [
    lambda i, r: r.pop("EW:B1-04:ALL"),                                         # index line with no census row
    lambda i, r: r.update({"EW:B1-03:Z9": {"cause": "DESIGNER", "gap": "x"}}),  # row naming no line
    lambda i, r: i[2].update({"measured_net": 0.0}),                           # HELD as 0
    lambda i, r: i[2].update({"measured_net": 4.0}),                           # HELD carrying a value
    lambda i, r: r["EW:B1-03:Z1-PITS"].update({"cause": "UNKNOWN"}),           # class not in the list
    lambda i, r: r["EW:B1-03:Z1-PITS"].update({"gap": ""}),                    # gap not named
    lambda i, r: r["EW:B1-04:ALL"].update({"tests": []}),                      # test not named
    lambda i, r: i[0].update({"item_code": "STR.EARTH.BACKFILL"}),             # code / zone family mismatch
    lambda i, r: i.append(dict(i[1], line_id="L-5")),                           # one zone on two lines
    lambda i, r: i.append(dict(i[1])),                                          # one line id twice
    lambda i, r: i[1].update({"held_high": None}),                             # half a bound
    lambda i, r: i[1].update({"held_low": 4.0}),                               # low > high
    lambda i, r: i[1].update({"unit": "mm3"}),                                 # unit
    lambda i, r: r["EW:B1-02:Z1-PITS"].update({"line_id": "L-7"}),             # stale line id in the register
])
def test_census_adverse(fn):
    idx, reg = _mut(fn)
    with pytest.raises(E.CensusError):
        E.census(idx, reg)
