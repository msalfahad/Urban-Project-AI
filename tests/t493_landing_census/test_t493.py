"""T-493 / LANDING_CENSUS_V1 (R-T493-1): every landing of a stair classed, measured once, one owner trade.

Hand villa K493 (not Alsenan). Storey levels 0.00 (GF) and 3.20 (1F). Dog-leg stair, two lanes 1.10 m with a 0.10 m
gap, flights of 10 risers x 0.160 m; the half landing at +1.60 is DIMENSIONED: depth 1.20 m printed, width 1.10 + 0.10 +
1.10 = 2.30 m -> 2.30 x 1.20 = 2.760 m2 (hand). A column 0.30 x 0.05 stands proud into it -> 2.760 - 0.015 = 2.745 m2.
The 1F arrival (owner answer, condition met) 2.30 x 1.50 = 3.450 m2. A lower lobby at +0.00 under the landing
(1.10 x 1.20 = 1.320 m2) is a STACKED surface, never a double count.
Adverse: a quarter area at the GF foot of the flight, bounded as its own zone, depth printed nowhere -> FLOOR_OR_LANDING,
area kept (1.21 m2), material HELD, never 0; no polygon -> area HELD (None), never 0.
"""
import json
import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "research" / "agents_t493"
sys.path.insert(0, str(RES))
import landing_census_v1 as L  # noqa: E402

LEVELS = [0.0, 3.20]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def tf(points, unit_f=1.0, rot_deg=0.0, mirror=False, shift=(0.0, 0.0)):
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    out = []
    for x, y in points:
        if mirror:
            x = -x
        out.append((((x * c - y * s) + shift[0]) * unit_f, ((x * s + y * c) + shift[1]) * unit_f))
    return out


def half_landing(**kw):
    p = {"id": "K-HL", "stair": "K-ST1", "level": 1.60, "arriving": ["F1"], "departing": ["F2"],
         "polygon": rect(0, 3.0, 2.30, 4.20), "claimed_by": ["B7-04"]}
    p.update(kw)
    return p


def arrival(**kw):
    p = {"id": "K-ARR", "stair": "K-ST1", "level": 3.20, "arriving": ["F2"],
         "owner_answer": {"id": "OWNER-K (arrival marble)", "condition_met": True},
         "polygon": rect(0, -1.50, 2.30, 0.0), "claimed_by": ["B7-04"]}
    p.update(kw)
    return p


def lobby(**kw):
    p = {"id": "K-LOBBY", "stair": "K-ST1", "level": 0.0, "departing": ["F1"],
         "polygon": rect(1.20, 3.0, 2.30, 4.20), "claimed_by": ["B3-01"], "in_room_floor_line": True}
    p.update(kw)
    return p


def row(res, pid):
    return next(r for r in res["rows"] if r["id"] == pid)


# ---------------------------------------------------------------------------------------------------- normal
def test_normal_dimensioned_half_landing():
    res = L.census([half_landing()], LEVELS)
    r = row(res, "K-HL")
    assert r["element"] == "STAIR_LANDING" and r["trade"] == "B7-04"
    assert r["area_m2"] == pytest.approx(2.30 * 1.20, abs=1e-9) == pytest.approx(2.760)
    assert r["material"] == "MARBLE" and "UP-STAIR-005" in r["material_basis"]
    assert r["status"] == "MEASURED"


def test_column_notch_is_the_drawn_polygon_not_a_rectangle():
    col = rect(2.00, 4.15, 2.30, 4.25)     # 0.30 x 0.10 column, 0.05 of it inside the landing
    r = row(L.census([half_landing(solids=[col])], LEVELS), "K-HL")
    assert r["area_m2"] == pytest.approx(2.760 - 0.30 * 0.05)
    assert r["solid_cut_m2"] == pytest.approx(0.015)


@pytest.mark.parametrize("unit,f", [("m", 1.0), ("mm", 1000.0)])
@pytest.mark.parametrize("rot", [0.0, 37.0, 90.0, 211.0])
@pytest.mark.parametrize("mirror", [False, True])
def test_units_rotation_mirror(unit, f, rot, mirror):
    poly = tf(rect(0, 3.0, 2.30, 4.20), f, rot, mirror, (512.25, -38.5))
    col = tf(rect(2.00, 4.15, 2.30, 4.25), f, rot, mirror, (512.25, -38.5))
    r = row(L.census([half_landing(polygon=poly, unit=unit, solids=[col])], LEVELS), "K-HL")
    assert r["area_m2"] == pytest.approx(2.745, abs=1e-6)


def test_arrival_with_owner_condition_met_is_stair_marble():
    r = row(L.census([arrival()], LEVELS), "K-ARR")
    assert r["element"] == "STAIR_ARRIVAL" and r["trade"] == "B7-04" and r["material"] == "MARBLE"
    assert r["area_m2"] == pytest.approx(3.450)


def test_stacked_landing_over_lobby_is_not_a_double_count():
    res = L.census([half_landing(), lobby()], LEVELS)
    assert res["stacked"] == [{"a": "K-HL", "b": "K-LOBBY", "plan_overlap_m2": pytest.approx(1.320),
                               "surface_overlap_m2": 0.0, "levels": [1.60, 0.0]}]
    assert row(res, "K-LOBBY")["element"] == "FLOOR" and row(res, "K-LOBBY")["trade"] == "B3-01"
    assert res["b3_b7_shared_m2"] == 0.0


def test_split_level_landing_total_and_surfaces():
    s = L.split_level([{"id": "W", "level": 1.60, "polygon": rect(0, 3.0, 1.15, 4.20)},
                       {"id": "E", "level": 1.76, "polygon": rect(1.15, 3.0, 2.30, 4.20)}], rect(0, 3.0, 2.30, 4.20))
    assert s["total_m2"] == pytest.approx(2.760)
    assert [x["area_m2"] for x in s["surfaces"]] == [pytest.approx(1.38), pytest.approx(1.38)]


def test_split_not_established_keeps_total():
    s = L.split_level([{"id": "W", "level": 1.60, "polygon": None}, {"id": "E", "level": 1.76, "polygon": None}],
                      rect(0, 3.0, 2.30, 4.20))
    assert s["total_m2"] == pytest.approx(2.760)
    assert all(x["area_m2"] is None for x in s["surfaces"])


def test_bound_with_landings_leaves_them_as_lines():
    b = L.bound_check(5.0, [{"id": "arr", "m2": 3.45, "kind": "LANDING"}, {"id": "void", "m2": 1.55, "kind": "VOID"}])
    assert b["verdict"] == "LANDINGS_LEAVE_AS_OWN_LINES" and b["landing_m2"] == pytest.approx(3.45)


# ---------------------------------------------------------------------------------------------------- adverse
def test_adverse_quarter_area_at_floor_foot_without_printed_depth_is_floor_or_landing_held():
    q = {"id": "K-QF", "stair": "K-ST1", "level": 0.0, "departing": ["F1"], "polygon": rect(0, 0, 1.10, 1.10)}
    r = row(L.census([q], LEVELS), "K-QF")
    assert r["element"] == "FLOOR_OR_LANDING"
    assert r["material"] is None and r["status"] == "MATERIAL_HELD"
    assert r["area_m2"] == pytest.approx(1.21)          # area kept, never 0
    assert r["trade"].startswith("HELD")


def test_adverse_owner_answer_condition_not_met_stays_held():
    r = row(L.census([arrival(owner_answer={"id": "OWNER-K", "condition_met": False})], LEVELS), "K-ARR")
    assert r["element"] == "FLOOR_OR_LANDING" and r["material"] is None


def test_adverse_no_polygon_is_area_held_never_zero():
    r = row(L.census([half_landing(polygon=None)], LEVELS), "K-HL")
    assert r["area_m2"] is None and r["status"] == "AREA_HELD"


def test_adverse_winder_is_never_a_landing():
    r = row(L.census([{"id": "K-W", "kind_hint": "WINDER", "polygon": None}], LEVELS), "K-W")
    assert r["element"] == "WINDER" and r["trade"] == "B7-02" and r["status"] == "TREAD_FAMILY"


def test_adverse_same_level_overlap_refused():
    other = half_landing(id="K-HL2", polygon=rect(2.0, 3.0, 3.0, 4.2))
    with pytest.raises(L.CensusError, match="double count"):
        L.census([half_landing(), other], LEVELS)


def test_adverse_one_surface_claimed_by_b3_and_b7_refused():
    with pytest.raises(L.CensusError, match="B3 and B7"):
        L.census([half_landing(claimed_by=["B3-01", "B7-04"])], LEVELS)


def test_adverse_bound_holding_no_landing_is_not_applicable():
    b = L.bound_check(2.9, [{"id": "winders", "m2": 1.3, "kind": "WINDER"}, {"id": "div", "m2": 0.7, "kind": "SOLID"},
                            {"id": "treads", "m2": 0.9, "kind": "TREAD"}])
    assert b["verdict"] == "NOT_APPLICABLE_AS_LANDING_BOUND" and b["landing_m2"] == 0


def test_adverse_bound_content_must_re_add():
    with pytest.raises(L.CensusError, match="re-add"):
        L.bound_check(3.0, [{"id": "x", "m2": 1.0, "kind": "VOID"}])


@pytest.mark.parametrize("bad,msg", [
    ({"unit": "ft"}, "unit"),
    ({"level": None}, "level missing"),
    ({"departing": []}, "arriving and a departing"),
    ({"polygon": [(0, 0), (1, 0)]}, "at least 3"),
    ({"project_material": "GOLD"}, "unknown material"),
    ({"solids": [rect(10, 10, 11, 11)]}, "does not touch"),
])
def test_refusals(bad, msg):
    with pytest.raises(L.CensusError, match=msg):
        L.census([half_landing(**bad)], LEVELS)


def test_refuses_duplicate_id():
    with pytest.raises(L.CensusError, match="duplicate"):
        L.census([half_landing(), half_landing()], LEVELS)


def test_split_surfaces_must_re_add():
    with pytest.raises(L.CensusError, match="re-add"):
        L.split_level([{"id": "W", "level": 1.6, "polygon": rect(0, 3.0, 1.0, 4.2)},
                       {"id": "E", "level": 1.76, "polygon": rect(1.15, 3.0, 2.30, 4.2)}], rect(0, 3.0, 2.30, 4.2))


def test_project_material_overrides_rule():
    r = row(L.census([half_landing(project_material="GRANITE")], LEVELS), "K-HL")
    assert r["material"] == "GRANITE" and r["material_basis"] == "PROJECT_SOURCE"


def test_module_has_no_training_villa_constant():
    src = (RES / "landing_census_v1.py").read_text(encoding="utf-8")
    for token in ("1.3525", "2.9325", "4.865", "1.4375", "P7757", "ST-01", "MS2-LD", "L-5d2be30d"):
        assert token not in src


# ---------------------------------------------------------------------------------------------------- pin
def test_training_villa_pin():
    s = json.loads((RES / "summary.json").read_text(encoding="utf-8"))
    by = {r["id"]: r for r in s["rows"]}
    assert by["ST02-RS-LD"]["area_m2"] == pytest.approx(1.3525)
    assert by["ST01-2F-ARRIVAL"]["area_m2"] == pytest.approx(4.865)
    assert by["ST01-MS1-LD"]["area_m2"] == pytest.approx(1.4375)
    assert by["ST01-MS2-LD"]["area_m2"] == pytest.approx(2.9325)
    assert s["proposed_new_b7_04_m2"] == pytest.approx(10.5875)
    assert s["b3_b7_shared_m2"] == 0.0
    assert by["ST01-GF-HALL"]["status"] == "MATERIAL_HELD" and by["ST01-GF-HALL"]["area_m2"] == pytest.approx(4.805)


def test_training_villa_rebuild_from_extract_is_byte_identical():
    sys.path.insert(0, str(RES))
    import t493_alsenan as A
    x = json.loads(A.EXTRACT.read_text(encoding="utf-8"))
    c, j = A.write_outputs(A.build(x))
    assert c == A.CENSUS.read_text(encoding="utf-8") and j == A.SUMMARY.read_text(encoding="utf-8")
