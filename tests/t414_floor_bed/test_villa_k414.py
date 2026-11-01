"""T-414 FLOOR_BED_V1 on a hand-calculated villa that is NOT Alsenan (villa K414, two storeys, invented dimensions).

Hand calculation (metres):
  GF living 6.00 x 5.00 = 30.000 m2 DRY, FFL +0.60, slab top +0.52 printed in a section -> b = 0.080
      finish not printed -> drawing: 0 < t <= 0.080, m3 bound 0 .. 2.400; owner Q-45 0.03 .. 0.04 -> 0.900 .. 1.200 m3,
      check 0.04 + 0 <= 0.08 CONSISTENT, finish slot 0.080 - 0.040 - 0.003 = 0.037 .. 0.080 - 0.030 = 0.050
  GF bedroom 4.20 x 3.50 = 14.700 m2 DRY, same zone, tile 0.010 printed in the finish schedule
      drawing: t = 0.080 - 0.010 - (0 .. 0.003) = 0.067 .. 0.070 -> 0.9849 .. 1.0290 m3 DRAWING-CONFIRMED range
  1F bath 2.40 x 2.00 = 4.800 m2 WET, sunken panel, drop printed 0.10, its own zone b = 0.05 + 0.10 = 0.150
      finish not printed -> bound 0 .. 0.720 m3; owner 0.04 .. 0.06 -> 0.192 .. 0.288 m3 CONSISTENT
  1F store (area HELD by the finish line) -> every quantity HELD, never 0
  1F balcony 3.00 x 1.50 = 4.500 m2 BALCONY, b HELD (constant layer vs falls) -> SCREED, m3 HELD on both methods
  roof terrace -> owned by B13-01, excluded, 0 rows
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t414"))
import floor_bed_v1 as FB  # noqa: E402

BU_GF = {"zone_type": "DRY", "b": 0.08, "status": "DRAWING-CONFIRMED", "ref": "K414 section 1-1 slab top +0.52"}


def villa():
    return {"units": "m", "rooms": [
        {"element_id": "K-GF-LIV", "floor": "GF", "kind": "DRY", "area_m2": 30.0, "area_status": "DRAWING-CONFIRMED",
         "finish_line": "L-k1", "finish_code": "FIN.FLOOR.PORCELAIN", "ffl": 0.60, "build_up": dict(BU_GF)},
        {"element_id": "K-GF-BED", "floor": "GF", "kind": "DRY", "area_m2": 14.7, "area_status": "DRAWING-CONFIRMED",
         "finish_line": "L-k2", "finish_code": "FIN.FLOOR.PORCELAIN", "ffl": 0.60, "build_up": dict(BU_GF),
         "finish_thickness": {"value": 0.010, "ref": "K414 finish schedule: porcelain 10 mm"}},
        {"element_id": "K-1F-BATH", "floor": "1F", "kind": "WET", "sunken": True, "area_m2": 4.8,
         "area_status": "DRAWING-CONFIRMED", "finish_line": "L-k3", "finish_code": "FIN.FLOOR.WET_TILE", "ffl": 3.60,
         "build_up": {"zone_type": "SUNKEN", "b": 0.15, "status": "DRAWING-CONFIRMED",
                      "ref": "K414 section 2-2: 0.05 + printed drop 0.10"}},
        {"element_id": "K-1F-STORE", "floor": "1F", "kind": "DRY", "area_m2": None, "area_status": "HELD",
         "finish_line": "L-k4", "ffl": 3.60,
         "build_up": {"zone_type": "DRY", "b": 0.05, "status": "DRAWING-CONFIRMED", "ref": "K414 section 1-1"}},
        {"element_id": "K-1F-BALC", "floor": "1F", "kind": "BALCONY", "area_m2": 4.5, "area_status": "DRAWING-CONFIRMED",
         "finish_line": "L-k5", "ffl": 3.58, "build_up": {"zone_type": "OUTDOOR", "b": None,
                                                          "missing": "CONSTANT_LAYER_VS_FALLS"}},
        {"element_id": "K-ROOF-T", "floor": "1F", "kind": "TERRACE"},
    ]}


@pytest.fixture(scope="module")
def res():
    return FB.evaluate(villa())


def _row(res, rid):
    return next(r for r in res["rows"] if r["element_id"] == rid)


def test_dry_room_bound_and_owner_range(res):
    r = _row(res, "K-GF-LIV")
    assert r["layer"] == "MORTAR_BED" and r["m2_status"] == "DRAWING-CONFIRMED" and r["area_m2"] == 30.0
    assert r["m3_drawing"]["status"] == "HELD" and r["m3_drawing"]["bound"] == [0.0, 2.4]
    assert r["m3_owner"] == {"status": FB.STATUS_OWNER, "low": 0.9, "high": 1.2}
    assert r["owner_manual"]["check"] == "CONSISTENT"
    assert r["owner_manual"]["finish_slot_m"] == [0.037, 0.05]


def test_printed_finish_gives_a_drawing_range_in_mm_units(res):
    r = _row(res, "K-GF-BED")
    assert r["m3_drawing"]["status"] == "DRAWING-CONFIRMED"
    assert r["m3_drawing"]["range"] == [pytest.approx(0.9849), pytest.approx(1.029)]


def test_sunken_wet_room_on_its_own_level(res):
    r = _row(res, "K-1F-BATH")
    assert r["drawing"]["b"] == 0.15 and r["m3_drawing"]["bound"] == [0.0, 0.72]
    assert r["m3_owner"]["low"] == pytest.approx(0.192) and r["m3_owner"]["high"] == pytest.approx(0.288)


def test_held_area_stays_held_never_zero(res):
    r = _row(res, "K-1F-STORE")
    assert r["area_m2"] is None and r["m3_drawing"]["status"] == "HELD" and r["m3_owner"]["status"] == "HELD"
    t = res["totals"]["DRY"]
    assert t["rooms_area_held"] == ["K-1F-STORE"] and t["m2"] == 44.7


def test_balcony_is_screed_with_thickness_held(res):
    r = _row(res, "K-1F-BALC")
    assert r["layer"] == "SCREED" and r["area_m2"] == 4.5
    assert r["m3_owner"]["status"] == "HELD" and r["m3_drawing"]["status"] == "HELD" and r["m3_drawing"]["bound"] is None


def test_terrace_excluded_owned_by_roof(res):
    assert [e["element_id"] for e in res["excluded"]] == ["K-ROOF-T"]
    assert all(r["element_id"] != "K-ROOF-T" for r in res["rows"])


def test_totals(res):
    t = res["totals"]
    assert t["DRY"]["m3_owner_low"] == pytest.approx(0.9 + 0.441) and t["DRY"]["m3_owner_high"] == pytest.approx(1.788)
    assert t["WET"]["m2"] == 4.8 and t["BALCONY"]["m3_owner_rooms"] == 0


# ---- adverse cases -------------------------------------------------------------------------------------------------

def _with(idx, **kw):
    v = villa()
    v["rooms"][idx].update(kw)
    return v


def test_thickness_defaulted_refused():
    with pytest.raises(ValueError, match="DEFAULTED_THICKNESS"):
        FB.evaluate(_with(1, finish_thickness={"value": 0.01, "ref": ""}))
    v = villa()
    v["rooms"][0]["build_up"]["ref"] = None
    with pytest.raises(ValueError, match="DEFAULTED_THICKNESS"):
        FB.evaluate(v)


def test_roof_counted_twice_refused():
    with pytest.raises(ValueError, match="OWNED_ELSEWHERE"):
        FB.evaluate(_with(5, as_b3_05=True))


def test_overlap_with_roof_ledger_is_a_double_count():
    v = villa()
    v["rooms"][4]["element_id"] = "K-ROOF-T2"
    res = FB.evaluate(v)
    chk = FB.overlap_check(res["rows"], [{"element_id": "K-ROOF-T2", "family": "B13-01", "layer": "FALLS_SCREED"},
                                         {"element_id": "K-1F-BATH", "family": "B8-01", "layer": "MEMBRANE"}])
    assert chk["double_counted"] == [{"element_id": "K-ROOF-T2", "family": "B13-01", "layer": "FALLS_SCREED"}]
    assert chk["different_layer_same_room"][0]["family"] == "B8-01"


def test_held_as_zero_refused():
    with pytest.raises(ValueError, match="HELD_AS_ZERO"):
        FB.evaluate(_with(3, area_m2=0.0))


def test_sunken_room_given_the_dry_build_up_refused():
    with pytest.raises(ValueError, match="STEPPED_SLAB_NOT_OWN_LEVEL"):
        FB.evaluate(_with(2, build_up=dict(BU_GF)))


def test_wet_room_given_the_dry_build_up_refused():
    with pytest.raises(ValueError, match="STEPPED_SLAB_NOT_OWN_LEVEL"):
        FB.evaluate(_with(2, sunken=False, build_up=dict(BU_GF)))


def test_same_room_twice_refused():
    v = villa()
    v["rooms"].append(copy.deepcopy(v["rooms"][0]))
    with pytest.raises(ValueError, match="counted twice"):
        FB.evaluate(v)


def test_owner_bed_that_cannot_fit_is_a_conflict():
    res = FB.evaluate(_with(0, build_up={"zone_type": "DRY", "b": 0.025, "status": "DRAWING-CONFIRMED", "ref": "x"}))
    assert _row(res, "K-GF-LIV")["owner_manual"]["check"] == "CONFLICT"


def test_mm_units():
    v = villa()
    v["units"] = "mm"
    for r in v["rooms"]:
        bu = r.get("build_up")
        if bu and bu.get("b") is not None:
            bu["b"] = bu["b"] * 1000
    v["rooms"][1]["finish_thickness"]["value"] = 10
    res = FB.evaluate(v)
    assert _row(res, "K-GF-LIV")["m3_drawing"]["bound"] == [0.0, 2.4]
    with pytest.raises(ValueError, match="unknown units"):
        FB.evaluate({"units": "ft", "rooms": []})


def test_not_applicable_finish_row_carries_no_bed():
    v = villa()
    v["rooms"].append({"element_id": "K-GF-STRIP", "floor": "GF", "kind": "DRY", "area_status": "NOT_APPLICABLE",
                       "finish_line": "L-k6"})
    res = FB.evaluate(v)
    r = _row(res, "K-GF-STRIP")
    assert r["m3_owner"]["status"] == "NOT_APPLICABLE" and r["area_m2"] is None
    assert res["totals"]["DRY"]["rows_not_applicable"] == ["K-GF-STRIP"] and res["totals"]["DRY"]["m2"] == 44.7
