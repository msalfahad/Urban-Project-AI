"""T-456 (owner directive 2026-11-02 C1): FINISH_MATERIALS_TABLE_V1 multiplies a GIVEN area (already m2) by the
drawing unit squared (finish_materials_table.py:112); FINISH_MATERIALS_TABLE_V2 keeps it. Synthetic hand cases only.

Hand values (owner Q-45 values of V1, PROVISIONAL): 20 m2 dry porcelain floor, bed 0.03 .. 0.04 m, mortar waste 5 %:
    mortar 20 x 0.03 x 1.05 = 0.63 m3 .. 20 x 0.04 x 1.05 = 0.84 m3
    cement 0.63 x 8 = 5.04 .. 0.84 x 8 = 6.72 bags of 50 kg; sand 0.63 x 1.1 = 0.693 .. 0.84 x 1.1 = 0.924 m3
    adhesive 20 / 5 = 4 bags of 20 kg"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t456"))

from engine.source import finish_materials_table as V1      # noqa: E402
from engine.source import finish_materials_table_v2 as V2   # noqa: E402

MM, M = 0.001, 1.0
KEYS = ("area_m2", "status", "reason", "mortar_m3_low", "mortar_m3_high", "cement_bags_low", "cement_bags_high",
        "sand_m3_low", "sand_m3_high", "adhesive_bags", "candidate_m2")
HAND_20 = {"area_m2": 20.0, "mortar_m3_low": 0.63, "mortar_m3_high": 0.84, "cement_bags_low": 5.04,
           "cement_bags_high": 6.72, "sand_m3_low": 0.693, "sand_m3_high": 0.924, "adhesive_bags": 4.0}


def area_el(u, a=20.0, **kw):
    return dict({"id": "A", "floor": "GF", "kind": V1.DRY_FLOOR, "area_m2": a, "unit_m": u}, **kw)


# ------------------------------------------------------------------ step 1: the defect, reproduced on V1
def test_v1_defect_reproduced_20_m2_in_mm_becomes_0_00002():
    r = V1.row(area_el(MM))
    assert r["area_m2"] == pytest.approx(20.0e-6, rel=1e-9)          # 20 x 0.001 x 0.001
    # the materials collapse to the 6-decimal round-off: mortar 20e-6 x 0.04 x 1.05 = 8.4e-7 prints 1e-06 m3, so the
    # cement is 8e-06 bags (not even the 6.72e-06 a clean 10^6 shrink gives) against the hand 6.72 bags
    assert r["mortar_m3_high"] == 1e-06 and r["cement_bags_high"] == 8e-06
    assert r["mortar_m3_low"] == 1e-06 and r["adhesive_bags"] == 4e-06
    assert V1.row(area_el(M))["area_m2"] == 20.0                      # metres hide the defect


# ------------------------------------------------------------------ the fix: 20 m2 stays 20 m2 in both units
@pytest.mark.parametrize("u", [M, MM, 0.01, 0.0254])
def test_v2_given_area_is_never_scaled(u):
    r = V2.row(area_el(u))
    assert r["status"] == "RELEASED"
    for k, v in HAND_20.items():
        assert r[k] == pytest.approx(v, abs=1e-9), k


def test_v2_equals_v1_in_metres_to_the_last_digit():
    for a in (20.0, 0.37, 137.5, 1e-3, 12345.678901):
        r1, r2 = V1.row(area_el(M, a)), V2.row(area_el(M, a))
        assert {k: r1[k] for k in KEYS} == {k: r2[k] for k in KEYS}


@pytest.mark.parametrize("kind", [V1.DRY_FLOOR, V1.WET_FLOOR, V1.STAIR_LANDING, V1.ROOF, V1.BALCONY])
def test_every_floor_like_kind_takes_the_fix(kind):
    r = V2.row(area_el(MM, 7.5, kind=kind))
    assert r["area_m2"] == pytest.approx(7.5)


# ------------------------------------------------------------------ every other branch: V2 == V1 (mm and m)
def _others(u):
    s = 1.0 / u
    return [
        {"id": "P", "floor": "GF", "kind": V1.DRY_FLOOR, "polygon": [(0, 0), (4 * s, 0), (4 * s, 5 * s), (0, 5 * s)],
         "holes": [[(s, s), (1.5 * s, s), (1.5 * s, 1.5 * s), (s, 1.5 * s)]], "unit_m": u},
        {"id": "LW", "floor": "GF", "kind": V1.WET_FLOOR, "length": 2.5 * s, "width": 1.8 * s, "unit_m": u},
        {"id": "WW", "floor": "1F", "kind": V1.WET_WALL, "wall_length": 9.0 * s, "door_widths": [0.8 * s],
         "height": 3.0 * s, "openings": [{"id": "W1", "width": 0.6 * s, "height": 0.6 * s}], "unit_m": u},
        {"id": "WWH", "floor": "1F", "kind": V1.WET_WALL, "wall_length": 9.0 * s, "door_widths": [0.8 * s],
         "height_status": "HELD", "candidate_height": 3.0 * s, "unit_m": u},
        {"id": "ST", "floor": "GF", "kind": V1.STAIR_FLIGHT, "steps": 10, "risers": 11, "riser": 0.17 * s,
         "tread": 0.30 * s, "width": 1.2 * s, "unit_m": u},
        {"id": "H", "floor": "GF", "kind": V1.DRY_FLOOR, "area_status": "HELD", "area_reason": "SRC", "candidate_m2": 9.0,
         "unit_m": u},
        {"id": "N", "floor": "GF", "kind": V1.DRY_FLOOR, "unit_m": u},
    ]


@pytest.mark.parametrize("u", [M, MM])
def test_v2_is_v1_on_every_branch_but_the_given_area(u):
    for e in _others(u):
        r1, r2 = V1.row(e), V2.row(e)
        assert {k: r1[k] for k in KEYS} == {k: r2[k] for k in KEYS}, e["id"]


def test_hand_values_of_the_other_branches_in_mm():
    rows = {r["id"]: r for r in V2.table(_others(MM))["rows"]}
    assert rows["P"]["area_m2"] == pytest.approx(20.0 - 0.25)                   # 4 x 5 less a 0.5 x 0.5 hole
    assert rows["LW"]["area_m2"] == pytest.approx(4.5)                          # 2.5 x 1.8
    assert rows["WW"]["area_m2"] == pytest.approx((9.0 - 0.8) * 3.0 - 0.36)     # 24.24
    assert rows["WWH"]["area_m2"] is None and rows["WWH"]["candidate_m2"] == pytest.approx(8.2 * 3.0)
    assert rows["ST"]["area_m2"] == pytest.approx(10 * 0.30 * 1.2 + 11 * 0.17 * 1.2)   # 3.60 + 2.244
    assert rows["H"]["area_m2"] is None and rows["H"]["candidate_m2"] == 9.0    # a candidate m2 is not scaled either
    assert rows["N"]["status"] == "HELD" and rows["N"]["reason"].startswith("NO_AREA")


# ------------------------------------------------------------------ adverse cases
@pytest.mark.parametrize("bad", [0, -4, "abc", True, float("nan"), float("inf")])
def test_broken_given_area_is_held_never_0(bad):
    r = V2.row(area_el(MM, bad))
    assert r["status"] == "HELD" and r["area_m2"] is None and r["reason"].startswith("AREA_INVALID")
    assert r["mortar_m3_low"] is None and r["adhesive_bags"] is None


@pytest.mark.parametrize("u", [0, None, "x", -1.0])
def test_broken_unit_is_held_as_v1(u):
    e = area_el(u)
    assert V2.row(e)["reason"] == V1.row(e)["reason"] == "UNIT_NOT_GIVEN"


def test_area_given_as_text_is_read_as_m2():
    assert V2.row(area_el(MM, "20"))["area_m2"] == pytest.approx(20.0)


def test_given_area_wins_over_a_polygon_as_in_v1():
    e = area_el(MM, 20.0, polygon=[(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
    assert V2.row(e)["area_m2"] == pytest.approx(20.0)        # not the 1 m2 polygon, not 2e-05


def test_mixed_table_in_mm_sums_and_holds():
    els = [area_el(MM, 20.0, id="A"),
           {"id": "P", "floor": "GF", "kind": V1.DRY_FLOOR, "polygon": [(0, 0), (3000, 0), (3000, 4000), (0, 4000)],
            "unit_m": MM},
           area_el(MM, 0, id="Z", floor="1F")]
    t1, t2 = V1.table(els), V2.table(els)
    assert t2["method"] == "FINISH_MATERIALS_TABLE_V2" and t2["supersedes"] == V1.METHOD_ID
    assert t2["project"]["area_m2"] == pytest.approx(32.0)                 # 20 + 12; Z held, not added as 0
    assert t1["project"]["area_m2"] == pytest.approx(12.00002)             # V1: the given room vanished
    assert t2["project"]["held_rows"] == ["Z"] and t2["project"]["not_in_sum"]["area_m2"] == ["Z"]
    assert t2["per_floor"]["1F"]["area_m2"] is None                       # a floor with only held rows is HELD
    assert t2["project"]["adhesive_bags_to_buy"] == math.ceil(32.0 / 5.0)  # 6.4 -> 7 whole bags on the sum


def test_duplicate_ids_refused():
    with pytest.raises(ValueError):
        V2.table([area_el(MM, id="a"), area_el(MM, id="a")])


# ------------------------------------------------------------------ reachability guard (step 1 evidence)
def test_v1_is_on_neither_the_released_nor_the_candidate_path():
    import t456_reproduce as R
    rep = R.reachability()
    assert rep["closure_method_check"]["pass"], rep["closure_method_check"]
    assert rep["target_in_released_path"] is False
    assert rep["target_in_candidate_closure"] is False
    assert rep["target_in_runtime_loaded_closure"] is False
    assert all(not x["names_target"] for x in rep["runtime_loaders_in_candidate_closure"])


def test_v2_declares_itself_an_unwired_producer():
    assert V2.DEFAULT_GUARD_CLASS == "UNWIRED_PRODUCER"
    src = (ROOT / "engine/source/finish_materials_table_v2.py").read_text(encoding="utf-8")
    assert 'DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"' in src
