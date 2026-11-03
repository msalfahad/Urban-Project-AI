"""T-490 / STONE_FLOOR_CENSUS_V1 (R-T490-1): B3-03 stone floor applicability, measure and overlap.

Hand villa K490 (not Alsenan). Entrance hall 4.00 x 3.00 m with a 0.90 m door in a 0.20 m wall:
  floor 4.00 x 3.00 = 12.00 m2 (the door changes nothing in the floor: its strip 0.90 x 0.20 = 0.18 m2 lies in the wall,
  listed to B3-04 by opening id, never added to the hall). A plan note names the hall marble -> B3-03 APPLICABLE 12.00.
  Column 0.30 x 0.30 inside the hall -> 12.00 - 0.09 = 11.91.
"""
import json
import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "research" / "agents_t490"
sys.path.insert(0, str(RES))
import stone_floor_census_v1 as S  # noqa: E402

NOTE_MARBLE = {"kind": "PLAN_NOTE", "material": "MARBLE", "rule": "plan note 'marble floor'"}
DEFAULT_PORC = {"kind": "DEFAULT_RULE", "material": "PORCELAIN", "rule": "URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1"}


def rect(w, h, unit_f=1.0, rot_deg=0.0, mirror=False, shift=(0.0, 0.0)):
    pts = [(0, 0), (w, 0), (w, h), (0, h)]
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    out = []
    for x, y in pts:
        if mirror:
            x = -x
        xr, yr = x * c - y * s, x * s + y * c
        out.append(((xr + shift[0]) * unit_f, (yr + shift[1]) * unit_f))
    return out


def hall(**kw):
    sp = {"id": "K-ENT", "name": "entrance hall", "floor": "GF", "element": "ROOM_FLOOR",
          "polygon": rect(4.0, 3.0), "unit": "m", "material_evidence": [NOTE_MARBLE],
          "openings": [{"id": "D-K1", "width": 0.90, "depth": 0.20}], "carriers": []}
    sp.update(kw)
    return sp


def test_normal_entrance_hall_marble_note():
    r = S.census_space(hall())
    assert r["area_m2"] == pytest.approx(12.00, abs=1e-9)
    assert r["family"] == "B3-03" and r["status"] == "APPLICABLE"
    assert r["b3_03_new_m2"] == pytest.approx(12.00)
    assert r["thresholds"] == [{"opening_id": "D-K1", "family": "B3-04", "strip_m2": pytest.approx(0.18)}]


@pytest.mark.parametrize("unit,f", [("m", 1.0), ("mm", 1000.0)])
@pytest.mark.parametrize("rot", [0.0, 37.0, 90.0, 211.0])
@pytest.mark.parametrize("mirror", [False, True])
def test_units_rotation_mirror(unit, f, rot, mirror):
    r = S.census_space(hall(polygon=rect(4.0, 3.0, f, rot, mirror, (1234.5, -77.0)), unit=unit))
    assert r["area_m2"] == pytest.approx(12.00, abs=1e-6)
    assert r["b3_03_new_m2"] == pytest.approx(12.00, abs=1e-6)


def test_fixed_column_deducted():
    r = S.census_space(hall(fixed=[{"id": "C1", "polygon": rect(0.3, 0.3)}]))
    assert r["area_m2"] == pytest.approx(11.91)


def test_adverse_already_porcelain_not_added_again():
    sp = hall(material_evidence=[DEFAULT_PORC],
              carriers=[{"line_id": "L-K-PORC", "family": "B3-01", "material": "PORCELAIN", "area_m2": 12.0}])
    r = S.census_space(sp)
    assert r["status"] == "NOT_APPLICABLE" and r["family"] == "B3-01"
    assert r["b3_03_new_m2"] == 0.0 and r["b3_03_move_m2"] == 0.0
    out = S.census([sp])
    assert out["totals"]["b3_03_new_m2"] == 0.0 and out["totals"]["b3_03_applicability"] == "NOT_APPLICABLE"


def test_adverse_stone_note_over_porcelain_line_is_a_move_not_an_addition():
    sp = hall(material_evidence=[NOTE_MARBLE, DEFAULT_PORC],
              carriers=[{"line_id": "L-K-PORC", "family": "B3-01", "material": "PORCELAIN", "area_m2": 12.0}])
    r = S.census_space(sp)
    assert r["status"] == "APPLICABLE_MOVE"
    assert r["b3_03_new_m2"] == 0.0 and r["b3_03_move_m2"] == pytest.approx(12.0)


def test_adverse_missing_area_is_held_never_zero():
    sp = hall()
    del sp["polygon"]
    r = S.census_space(sp)
    assert r["area_m2"] is None and r["status"] == "APPLICABLE_AREA_HELD"
    assert r["b3_03_held"] == [0.0, None]
    assert S.census([sp])["totals"]["b3_03_held_unbounded"] == 1


def test_stair_arrival_is_b7_not_b303():
    sp = {"id": "K-ARR", "element": "STAIR_ARRIVAL", "area_m2": 2.4 * 1.8, "area_source": "printed",
          "material_evidence": [{"kind": "OWNER_RULE", "material": "MARBLE", "rule": "UP-STAIR-005"}, DEFAULT_PORC]}
    r = S.census_space(sp)
    assert r["family"] == "B7" and r["status"] == "CARRIED_ELSEWHERE" and r["b3_03_new_m2"] == 0.0
    assert r["material_basis"] == "OWNER_RULE"  # the porcelain default never applies to a stair part
    assert r["line_state"] == "NO_LINE"


def test_floor_or_landing_without_printed_depth_is_held():
    sp = {"id": "K-FOOT", "element": "FLOOR_OR_LANDING", "area_m2": 3.0, "area_source": "drawn",
          "material_evidence": [DEFAULT_PORC, {"kind": "OWNER_RULE", "material": "MARBLE", "condition_met": False}]}
    r = S.census_space(sp)
    assert r["status"] == "HELD" and r["candidate_families"] == ["B3-01", "B7"]
    assert r["material"] is None and r["area_m2"] == 3.0
    sp["material_evidence"][1]["condition_met"] = True
    assert S.census_space(sp)["family"] == "B7"
    sp["material_evidence"].append(NOTE_MARBLE)
    assert S.census_space(sp)["family"] == "B3-03"


def test_conflict_same_level_is_held():
    sp = hall(material_evidence=[NOTE_MARBLE, {"kind": "PROJECT_SCHEDULE", "material": "PORCELAIN"}])
    r = S.census_space(sp)
    assert r["status"] == "HELD" and r["material_basis"] == "CONFLICT"
    assert r["b3_03_held"] == [0.0, pytest.approx(12.0)]


def test_threshold_goes_to_b304():
    sp = {"id": "K-TH", "element": "THRESHOLD", "area_m2": 0.18, "area_source": "printed", "material_evidence": []}
    r = S.census_space(sp)
    assert r["family"] == "B3-04" and r["b3_03_new_m2"] == 0.0


@pytest.mark.parametrize("bad,msg", [
    ({"unit": "ft"}, "unit"),
    ({"element": "BALCONY"}, "element"),
    ({"fixed": [{"id": "X", "polygon": rect(5, 5)}]}, "exceed"),
    ({"polygon": None, "area_m2": 12.0}, "source"),
    ({"material_evidence": [{"kind": "RUMOUR", "material": "MARBLE"}]}, "evidence"),
    ({"material_evidence": [{"kind": "PLAN_NOTE", "material": "WOOD"}]}, "material"),
])
def test_refusals(bad, msg):
    with pytest.raises(S.CensusError, match=msg):
        S.census_space(hall(**bad))


def test_duplicate_id_refused():
    with pytest.raises(S.CensusError, match="duplicate"):
        S.census([hall(), hall()])


def test_training_villa_census_reproduces():
    import t490_alsenan as A
    out = A.run()
    committed = json.loads((RES / "summary.json").read_text(encoding="utf-8"))
    assert committed == json.loads(json.dumps(out))
    rows = {r["id"]: r for r in out["rows"]}
    assert out["totals"]["b3_03_applicability"] == "NOT_APPLICABLE"
    assert out["totals"]["b3_03_new_m2"] == 0.0 and out["totals"]["b3_03_move_m2"] == 0.0
    assert rows["GF-ST-HALL"]["status"] == "HELD" and rows["GF-ST-HALL"]["area_m2"] == pytest.approx(4.805)
    assert rows["GF-ST-LOBBY030"]["area_m2"] == pytest.approx(1.3225)
    assert rows["GF-E1-LANDING"]["area_m2"] == pytest.approx(5.18)
    assert rows["1F-MAIN-ARRIVAL"]["carrier_minus_measure_m2"] == pytest.approx(0.0475)
    assert rows["2F-ST-ARRIVAL"]["line_state"] == "HELD_ONLY"
    assert rows["1F-ROUND-QUARTER-LANDING"]["line_state"] == "NO_LINE"
    assert rows["GF-ST-CN"]["area_m2"] is None  # held, never 0
    assert out["totals"]["by_family_m2"]["HELD"] == pytest.approx(6.1275)
