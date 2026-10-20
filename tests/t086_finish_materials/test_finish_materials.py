"""T-086 FINISH_MATERIALS_TABLE_V1 on a hand fixture that is not any client villa (owner Q-45 values).

Hand calculations (written out; waste 5 % on mortar; 1:4 mortar = 8 bags of 50 kg and 1.1 m3 loose sand per m3;
adhesive 20 kg per 5 m2 for ceramic / porcelain):
  B  bathroom 4.00 x 3.00 = 12.00 m2 wet floor, bed 0.04 - 0.06:
       mortar 12 x 0.04 x 1.05 = 0.504, 12 x 0.06 x 1.05 = 0.756 m3; cement 4.032 - 6.048 bags; sand 0.5544 - 0.8316 m3;
       adhesive 12 / 5 = 2.40 bags
  BW bathroom walls: perimeter 14.00 - door 0.80 = 13.20 m x 3.35 = 44.22 m2 - window 0.60 x 0.60 = 0.36 -> 43.86 m2,
       mortar 43.86 x 0.02 x 1.05 = 0.92106 m3; cement 7.36848; sand 1.013166; adhesive 8.772 bags
  R  bedroom 5.00 x 4.00 m given in mm = 20.00 m2 dry floor, bed 0.03 - 0.04:
       mortar 0.63 - 0.84 m3; cement 5.04 - 6.72; sand 0.693 - 0.924; adhesive 4.00
  S  stair flight 10 steps, riser 0.165, tread 0.30, width 1.20 (owner Q-19 step = tread + riser):
       treads 3.60 + risers 1.98 = 5.58 m2; mortar 5.58 x 0.03 x 1.05 = 0.17577 m3; cement and sand HELD (1:3 not
       given), adhesive HELD (marble)
  L  landing 1.20 x 1.25 = 1.50 m2; mortar 0.04725 m3
  Project released: 82.94 m2; mortar 2.27808 - 2.74008 m3; cement 16.44048 - 20.13648 bags (buy 17 - 21);
       adhesive 15.172 bags (buy 16)."""

import math

import pytest

from engine.source import finish_materials_table as F


def rot(points, deg, mirror=False):
    a = math.radians(deg)
    out = []
    for x, y in points:
        if mirror:
            x = -x
        out.append((x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)))
    return out


BATH = [(0, 0), (4, 0), (4, 3), (0, 3)]
BED_MM = [(0, 0), (5000, 0), (5000, 4000), (0, 4000)]


def fixture():
    return [
        {"id": "B", "floor": "GF", "kind": F.WET_FLOOR, "polygon": BATH},
        {"id": "BW", "floor": "GF", "kind": F.WET_WALL, "wall_length": 14.0, "door_widths": [0.80], "height": 3.35,
         "openings": [{"id": "W1", "width": 0.60, "height": 0.60}]},
        {"id": "R", "floor": "1F", "kind": F.DRY_FLOOR, "polygon": BED_MM, "unit_m": 0.001},
        {"id": "S", "floor": "GF", "kind": F.STAIR_FLIGHT, "steps": 10, "riser": 0.165, "tread": 0.30, "width": 1.20},
        {"id": "L", "floor": "GF", "kind": F.STAIR_LANDING, "length": 1.20, "width": 1.25},
        {"id": "X", "floor": "1F", "kind": F.DRY_FLOOR, "name": "store, no outline drawn"},
    ]


def by_id(t):
    return {r["id"]: r for r in t["rows"]}


def test_bathroom_floor_by_hand():
    r = by_id(F.table(fixture()))["B"]
    assert r["status"] == "RELEASED" and r["area_m2"] == pytest.approx(12.0)
    assert (r["bed_low_m"], r["bed_high_m"], r["mix"]) == (0.04, 0.06, "1:4")
    assert r["mortar_m3_low"] == pytest.approx(0.504) and r["mortar_m3_high"] == pytest.approx(0.756)
    assert r["cement_bags_low"] == pytest.approx(4.03, abs=0.005) and r["cement_bags_high"] == pytest.approx(6.05, abs=0.005)
    assert r["sand_m3_low"] == pytest.approx(0.5544) and r["sand_m3_high"] == pytest.approx(0.8316)
    assert r["adhesive_bags"] == pytest.approx(2.40)
    assert r["mortar_status"] == r["cement_sand_status"] == r["adhesive_status"] == "PROVISIONAL"


def test_bathroom_wall_by_hand():
    r = by_id(F.table(fixture()))["BW"]
    assert r["gross_m2"] == pytest.approx(44.22) and r["openings_m2"] == pytest.approx(0.36)
    assert r["area_m2"] == pytest.approx(43.86)
    assert r["mortar_m3_low"] == r["mortar_m3_high"] == pytest.approx(0.92106)
    assert r["cement_bags_low"] == pytest.approx(7.37, abs=0.005)
    assert r["sand_m3_low"] == pytest.approx(1.0132, abs=1e-4)
    assert r["adhesive_bags"] == pytest.approx(8.77, abs=0.005)


def test_bedroom_in_mm_by_hand():
    r = by_id(F.table(fixture()))["R"]
    assert r["area_m2"] == pytest.approx(20.0)
    assert r["mortar_m3_low"] == pytest.approx(0.63) and r["mortar_m3_high"] == pytest.approx(0.84)
    assert r["cement_bags_low"] == pytest.approx(5.04) and r["cement_bags_high"] == pytest.approx(6.72)
    assert r["sand_m3_low"] == pytest.approx(0.693) and r["sand_m3_high"] == pytest.approx(0.924)
    assert r["adhesive_bags"] == pytest.approx(4.0)


def test_stair_flight_and_landing_by_hand():
    t = by_id(F.table(fixture()))
    s, l = t["S"], t["L"]
    assert s["treads_m2"] == pytest.approx(3.60) and s["risers_m2"] == pytest.approx(1.98)
    assert s["area_m2"] == pytest.approx(5.58) and s["mix"] == "1:3"
    assert s["mortar_m3_low"] == s["mortar_m3_high"] == pytest.approx(0.17577)
    # 1:3 bags / sand and marble adhesive are not owner values: HELD, never a typical figure, never 0
    assert s["cement_bags_low"] is None and s["sand_m3_low"] is None and s["cement_sand_status"] == "HELD"
    assert "1:3" in s["cement_sand_reason"]
    assert s["adhesive_bags"] is None and "MARBLE" in s["adhesive_reason"]
    assert l["area_m2"] == pytest.approx(1.50) and l["mortar_m3_low"] == pytest.approx(0.04725)


def test_room_without_outline_is_held_not_zero():
    r = by_id(F.table(fixture()))["X"]
    assert r["status"] == "HELD" and r["area_m2"] is None and r["reason"].startswith("NO_AREA")
    for k in ("mortar_m3_low", "cement_bags_low", "sand_m3_low", "adhesive_bags"):
        assert r[k] is None


def test_project_and_floor_sums_by_hand():
    t = F.table(fixture())
    p = t["project"]
    assert p["area_m2"] == pytest.approx(82.94)
    assert p["mortar_m3_low"] == pytest.approx(2.27808) and p["mortar_m3_high"] == pytest.approx(2.74008)
    assert p["cement_bags_low"] == pytest.approx(16.44, abs=0.01) and p["cement_bags_high"] == pytest.approx(20.14, abs=0.01)
    assert (p["cement_bags_to_buy_low"], p["cement_bags_to_buy_high"], p["adhesive_bags_to_buy"]) == (17, 21, 16)
    assert p["held_rows"] == ["X"]
    assert set(p["not_in_sum"]["cement_bags_low"]) == {"S", "L", "X"}
    gf = t["per_floor"]["GF"]
    assert gf["area_m2"] == pytest.approx(12 + 43.86 + 5.58 + 1.5)
    assert t["per_kind"][F.DRY_FLOOR]["area_m2"] == pytest.approx(20.0)


@pytest.mark.parametrize("deg,mirror", [(30, False), (30, True), (137.5, True), (-90, False)])
def test_rotation_and_mirror_do_not_change_quantities(deg, mirror):
    base = by_id(F.table(fixture()))["B"]
    e = {"id": "B", "floor": "GF", "kind": F.WET_FLOOR, "polygon": [(x * 1000, y * 1000) for x, y in rot(BATH, deg, mirror)],
         "unit_m": 0.001}
    r = F.row(e)
    for k in ("area_m2", "mortar_m3_low", "mortar_m3_high", "adhesive_bags", "sand_m3_high"):
        assert r[k] == pytest.approx(base[k], abs=1e-6)


def test_l_shaped_room_and_hole():
    # L: 5 x 4 less a 2 x 1.5 notch = 17.00 m2; a 0.5 x 0.5 shaft hole -> 16.75 m2
    L = [(0, 0), (5, 0), (5, 2.5), (3, 2.5), (3, 4), (0, 4)]
    r = F.row({"id": "L1", "floor": "GF", "kind": F.DRY_FLOOR, "polygon": L,
               "holes": [[(1, 1), (1.5, 1), (1.5, 1.5), (1, 1.5)]]})
    assert r["area_m2"] == pytest.approx(16.75)
    assert r["mortar_m3_low"] == pytest.approx(16.75 * 0.03 * 1.05)


def test_wall_with_unprinted_window_is_held_with_candidate():
    r = F.row({"id": "W", "floor": "GF", "kind": F.WET_WALL, "wall_length": 10.0, "door_widths": [0.8], "height": 3.0,
               "openings": [{"id": "OP-7", "width": 0.6, "height": None}]})
    assert r["status"] == "HELD" and "OP-7" in r["reason"] and r["candidate_m2"] == pytest.approx(27.6)
    assert r["adhesive_bags"] is None


def test_wall_with_held_height_carries_the_candidate():
    r = F.row({"id": "W", "floor": "1F", "kind": F.WET_WALL, "wall_length": 9.0, "door_widths": [0.8],
               "height_status": "HELD", "height_reason": "BEAM_NOT_0.60", "candidate_height": 3.35})
    assert r["status"] == "HELD" and r["reason"] == "BEAM_NOT_0.60"
    assert r["candidate_m2"] == pytest.approx(8.2 * 3.35) and r["area_m2"] is None


@pytest.mark.parametrize("e,reason", [
    ({"kind": F.WET_WALL, "wall_length": 1.0, "door_widths": [0.9, 0.9], "height": 3}, "WALL_RUN_INVALID"),
    ({"kind": F.WET_WALL, "door_widths": [0.9], "height": 3}, "WALL_LENGTH_NOT_GIVEN"),
    ({"kind": F.DRY_FLOOR, "area_m2": 0}, "AREA_INVALID"),
    ({"kind": F.DRY_FLOOR, "area_m2": -4}, "AREA_INVALID"),
    ({"kind": F.DRY_FLOOR, "polygon": [(0, 0), (1, 1)]}, "OUTLINE_INVALID"),
    ({"kind": F.DRY_FLOOR, "polygon": [(0, 0), (1, 1), (2, 2)]}, "OUTLINE_INVALID"),
    ({"kind": F.DRY_FLOOR, "area_m2": 10, "unit_m": 0}, "UNIT_NOT_GIVEN"),
    ({"kind": F.STAIR_FLIGHT, "steps": 0, "riser": 0.16, "tread": 0.3, "width": 1.2}, "STEP_COUNT_NOT_GIVEN"),
    ({"kind": F.STAIR_FLIGHT, "steps": 10, "riser": None, "tread": 0.3, "width": 1.2}, "STEP_SIZE_NOT_GIVEN"),
    ({"kind": F.STAIR_FLIGHT, "area_status": "HELD", "area_reason": "RISER_COUNT_CONFLICT"}, "RISER_COUNT_CONFLICT"),
    ({"kind": "SKIRTING", "area_m2": 3}, "UNKNOWN_KIND"),
])
def test_bad_or_missing_data_is_held(e, reason):
    r = F.row(dict(e, id="E", floor="GF"))
    assert r["status"] == "HELD" and r["area_m2"] is None and r["reason"].startswith(reason)


def test_roof_screed_and_finish_are_held_area_released():
    r = F.row({"id": "RF", "floor": "ROOF", "kind": F.ROOF, "area_m2": 100.0})
    assert r["status"] == "RELEASED" and r["area_m2"] == 100.0
    assert r["mortar_m3_low"] is None and "Q-41" in r["mortar_reason"]
    assert r["adhesive_bags"] is None and r["adhesive_reason"].startswith("FINISH_NOT_GIVEN")


def test_closing_riser_and_sum_of_all_held_is_none():
    s = F.row({"id": "S2", "floor": "1F", "kind": F.STAIR_FLIGHT, "steps": 12, "risers": 13, "riser": 0.168,
               "tread": 0.30, "width": 1.20})
    assert s["treads_m2"] == pytest.approx(4.32) and s["risers_m2"] == pytest.approx(13 * 0.168 * 1.2)
    t = F.table([{"id": "a", "floor": "2F", "kind": F.DRY_FLOOR}, {"id": "b", "floor": "2F", "kind": F.WET_FLOOR}])
    p = t["project"]
    assert p["area_m2"] is None and p["cement_bags_to_buy_low"] is None and p["adhesive_bags_to_buy"] is None


def test_duplicate_surface_is_refused():
    with pytest.raises(ValueError):
        F.table([{"id": "a", "kind": F.DRY_FLOOR, "area_m2": 1}, {"id": "a", "kind": F.DRY_FLOOR, "area_m2": 1}])


def test_module_holds_no_project_constants():
    import inspect
    src = inspect.getsource(F).lower()
    for word in ("alsenan", "p7757", "st7757", "dewaneya"):
        assert word not in src
