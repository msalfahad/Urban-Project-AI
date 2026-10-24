"""T-267: the owner's 15 tests (OWNER_RULE_STAIRS_2026-10-24.md, task row) and the extra cases, on synthetic stairs.
Expected values are hand calculations (written beside each assertion), never read back from the module."""
from __future__ import annotations

import copy
import math

import pytest

from engine.source import stair_finish_levels_v1 as M
from engine.source import stair_geometry as SG

from .fixtures import MARBLE, dog_leg, rect, straight


def risers(rec):
    return [r["structural_riser_mm"] for r in M.levels(rec)["risers"]]


def line(res, comp, part):
    (ln,) = [x for x in res["lines"] if x["component"] == comp and x["part"] == part]
    return ln


def codes(res):
    return [f["code"] for f in res["findings"]]


# 1 / 2: the owner's examples (F0 = F1 = 100, stair finish omitted)
@pytest.mark.parametrize("r,first,last", [(150.0, 250.0, 50.0), (160.0, 260.0, 60.0)])
def test_owner_examples_25_15_5_and_26_16_6(r, first, last):
    got = risers(straight(10, r, s=0.0))
    assert got == pytest.approx([first] + [r] * 8 + [last])
    lv = M.levels(straight(10, r, s=0.0))
    assert lv["closed_form"]["agrees"]                       # the frozen stair_riser_schedule.first_last agrees


def test_values_are_not_hardcoded():
    assert risers(straight(10, 155.0, s=0.0, f0=80.0, f1=120.0)) == pytest.approx([235.0] + [155.0] * 8 + [35.0])


# 3: F0 != F1 (R 160, F0 100, F1 60, S 30): first 160 + 100 - 30 = 230, last 160 + 30 - 60 = 130
def test_f0_differs_from_f1():
    rec = straight(10, 160.0, s=30.0, f0=100.0, f1=60.0)
    assert risers(rec) == pytest.approx([230.0] + [160.0] * 8 + [130.0])
    c = M.levels(rec)["closure"]
    assert c["sum_structural_risers_mm"] == pytest.approx(230 + 8 * 160 + 130)      # 1640
    assert c["slab_to_slab_mm"] == pytest.approx((1600 - 60) - (0 - 100))           # 1640
    assert c["closes"]


# 4: nonzero marble + bed (S = 20 + 30 = 50): first 210, last 110; visible riser 160 - 50 = 110 mm
def test_nonzero_marble_and_bed():
    rec = straight(10, 160.0, s=50.0)
    assert risers(rec) == pytest.approx([210.0] + [160.0] * 8 + [110.0])
    res = M.check_stair(rec)
    assert line(res, "MARBLE_RISER", "riser 1")["quantity"] == pytest.approx(0.110 * 1.2)      # 0.132 m2
    assert line(res, "MARBLE_RISER", "riser 10")["quantity"] == pytest.approx(0.140 * 1.2)     # 160 - 20 (arrival)


# 5: the finish changes at a landing and between flights (A 30, landing 50, B 20), R 160, F0 = F1 = 100
def test_finish_changes_between_flights_and_at_the_landing():
    got = risers(dog_leg(6, 6, 160.0))
    # 1: 160+100-30=230; 2-5: 160; 6 onto the landing: 160+30-50=140; 7 off it: 160+50-20=190; 8-11: 160; 12: 160+20-100=80
    assert got == pytest.approx([230.0, 160, 160, 160, 160, 140.0, 190.0, 160, 160, 160, 160, 80.0])
    assert sum(got) == pytest.approx(12 * 160.0)


# 6: a rise that no whole count of 160 fits, and one with no count inside 150 - 170
def test_rise_not_divisible():
    rep = M.alternatives(4500.0, None, M.UNKNOWN)
    assert [a["risers"] for a in rep["alternatives"]] == [27, 28, 29, 30]   # 166.67 / 160.71 / 155.17 / 150.00
    assert [round(a["finished_riser_mm"], 2) for a in rep["alternatives"]] == [166.67, 160.71, 155.17, 150.0]
    assert M.riser_count_exact(4.5, 0.16) is None                          # 28.125: never rounded
    assert M.alternatives(250.0, 1000.0, M.FIXED)["status"] == "NO_COUNT_IN_RANGE"   # 125 / 250 only


# 7: 25 goings 300 -> 280 = 0.50 m shorter; 25 risers with 24 goings = 0.48 m
def test_going_change_counts_goings_not_risers():
    with_tread = M.check_stair(dog_leg(25, 4, 160.0, top_tread_drawn=True))
    on_landing = M.check_stair(dog_leg(25, 4, 160.0, top_tread_drawn=False))
    ga = {g["flight"]: g for g in with_tread["goings"]}["A"]
    gb = {g["flight"]: g for g in on_landing["goings"]}["A"]
    assert (ga["risers"], ga["goings"]) == (25, 25)
    assert (gb["risers"], gb["goings"]) == (25, 24)
    assert ga["alternatives"]["run_change_mm"][0] == pytest.approx(-500.0)      # 25 x (280 - 300)
    assert gb["alternatives"]["run_change_mm"][0] == pytest.approx(-480.0)      # 24 x (280 - 300)


# 8: projection beyond the wall: last riser line 9 x 300 = 2700, alignment 2600 -> 100 beyond
def test_projection_beyond_a_wall():
    rec = straight(10, 160.0)
    rec["flights"]["A"]["end_limit_mm"] = 2600.0
    (f,) = [x for x in M.check_stair(rec)["findings"] if x["code"] == "PROJECTION"]
    assert f["values"]["beyond_mm"] == pytest.approx(100.0)
    rec["flights"]["A"]["end_limit_mm"] = 2700.0
    assert "PROJECTION" not in codes(M.check_stair(rec))


# 9: architectural / structural disagreement is a conflict, never resolved
def test_arch_struct_disagreement():
    rec = straight(10, 160.0)
    rec["cross_readings"] = [{"item": "going T1", "arch": 300.0, "struct": 280.0}]
    (f,) = [x for x in M.check_stair(rec)["findings"] if x["code"] == "ARCH_STRUCT_DISAGREE"]
    assert f["kind"] == "CONFLICT" and f["changes_geometry"] is False


# 10: extra / missing upper step (plan 10, section 11) and the arrival riser off the slab edge (2700 vs 2400)
def test_extra_or_missing_step_and_misaligned_top():
    rec = straight(10, 160.0)
    rec["riser_counts"] = {"PLAN": 10, "SECTION": 11}
    rec["flights"]["A"]["top_edge_mm"] = 2400.0
    res = M.check_stair(rec)
    (f,) = [x for x in res["findings"] if x["code"] == "EXTRA_OR_MISSING_STEP"]
    assert f["kind"] == "CONFLICT" and f["values"] == {"PLAN": 10, "SECTION": 11, "record": 10}
    (m,) = [x for x in res["findings"] if x["code"] == "MISALIGNED_TOP"]
    assert m["values"]["offset_mm"] == pytest.approx(300.0)
    # never picked: every level, riser and riser-dependent quantity HELD, blank
    assert res["levels"]["riser_mm"] is None
    assert all(r["structural_riser_mm"] is None and r["status"] == M.HELD for r in res["levels"]["risers"])
    assert line(res, "CONCRETE", "flight A")["quantity"] is None
    assert line(res, "HANDRAIL", "flight A")["quantity"] is None
    assert line(res, "MARBLE_RISER", "riser 1")["quantity"] is None
    assert line(res, "MARBLE_TREAD", "T1")["status"] == M.MEASURED            # plan geometry, not count-dependent
    # an owner decision naming the governing reading: levels on it, the conflict still listed
    rec["riser_count_governs"] = "PLAN"
    res = M.check_stair(rec)
    assert res["levels"]["riser_mm"] == pytest.approx(160.0) and "EXTRA_OR_MISSING_STEP" in codes(res)
    rec["riser_count_governs"] = "SECTION"                                     # names a reading the record does not use
    assert M.check_stair(rec)["levels"]["riser_mm"] is None


def test_flight_conflict_holds_that_flight_only():
    rec = dog_leg(6, 6, 160.0)
    rec["flights"]["A"]["conflict"] = "plan vs structural riser lines (designer item)"
    res = M.check_stair(rec)
    assert line(res, "CONCRETE", "flight A")["status"] == M.HELD
    assert line(res, "MARBLE_TREAD", "A1")["status"] == M.HELD and line(res, "HANDRAIL", "flight A")["status"] == M.HELD
    assert line(res, "CONCRETE", "flight B")["status"] == M.MEASURED
    assert line(res, "MARBLE_TREAD", "B1")["status"] == M.MEASURED


# 11: plausible structural risers (all 160) give unequal finished ones: 160+30-100 = 90 first, 160+100-30 = 230 last
def test_unequal_finished_risers_from_plausible_structural_ones():
    rec = straight(10, 160.0, s=30.0)
    rec["structural_risers_mm"] = [160.0] * 10
    (f,) = [x for x in M.check_stair(rec)["findings"] if x["code"] == "UNEQUAL_FINISHED_RISERS"]
    assert f["values"]["finished_mm"] == pytest.approx([90.0] + [160.0] * 8 + [230.0])
    rec["floor_top_finish_mm"] = 60.0
    rec["structural_risers_mm"] = [230.0] + [160.0] * 8 + [130.0]   # the owner method for F1 = 60: finished all 160
    assert "UNEQUAL_FINISHED_RISERS" not in codes(M.check_stair(rec))


# 12: short landing and headroom, each against a stated, verified limit
def test_short_landing_and_headroom():
    rec = dog_leg(6, 6, 160.0)
    rec["limits"] = {"landing_depth_min_mm": {"value": 1300.0, "source": "synthetic verified clause", "verified": True},
                     "headroom_min_mm": {"value": 2000.0, "source": "synthetic verified clause", "verified": True}}
    # B1 is level 7 (5 risers on A, 1 onto the landing, 1 onto B1): FFL 1120; B2 1280; member soffit 3020 over 0 .. 600
    rec["overhead"] = [{"id": "BM", "flight": "B", "s_from_mm": 0.0, "s_to_mm": 600.0, "soffit_mm": 3020.0}]
    res = M.check_stair(rec)
    assert "LANDING_DEPTH" in codes(res)
    (h,) = res["headroom"]
    assert h["clear_mm"] == pytest.approx(3020.0 - 1280.0) and h["check"] == "BELOW_LIMIT"       # 1740
    assert "HEADROOM" in codes(res)
    rec["limits"]["headroom_min_mm"]["verified"] = False
    res = M.check_stair(rec)
    assert res["headroom"][0]["check"] == M.CODE_NOT_VERIFIED and "HEADROOM" not in codes(res)


# 13: drawn dimensions outside the owner preference: findings only, the drawn quantities stay
def test_outside_owner_preference_is_a_finding_only():
    res = M.check_stair(straight(10, 180.0, going=260.0))
    assert codes(res).count("OUTSIDE_OWNER_PREFERENCE") == 1 + 9          # the riser + every drawn going
    assert line(res, "MARBLE_TREAD", "T1")["quantity"] == pytest.approx(0.260 * 1.2)
    assert all(f["changes_geometry"] is False for f in res["findings"])


# 14: concrete, marble and rail reconcile to ONE geometry (the frozen straight_flight on the same inputs)
def test_concrete_marble_rail_from_one_geometry():
    res = M.check_stair(straight(10, 160.0, s=30.0, waist=150.0))
    ref = SG.straight_flight(10, 160.0, 300.0, 1200.0, 150.0)
    assert line(res, "CONCRETE", "flight A")["quantity"] == pytest.approx(ref["STAIR_CONCRETE_VOLUME"] / 1e9)
    trd = sum(x["quantity"] for x in res["lines"] if x["component"] == "MARBLE_TREAD")
    assert trd == pytest.approx(9 * 0.3 * 1.2) == pytest.approx(ref["FINISHING_TREAD_AREA"] / 1e6)    # 3.24 m2
    assert line(res, "HANDRAIL", "flight A")["quantity"] == pytest.approx(math.hypot(2700, 1440) / 1000)  # 3.06 m
    assert line(res, "HANDRAIL", "flight A")["quantity"] == pytest.approx(ref["HANDRAIL_PATH_LENGTH"] / 1000)


def test_concrete_by_hand_section():
    # hand: steps 9 x (0.5 x 300 x 160) above the root line; strip under it: length 2700 x vertical depth 150 / cos
    res = M.check_stair(straight(10, 160.0, waist=150.0))
    cos = 300.0 / math.hypot(300.0, 160.0)
    area = 9 * 0.5 * 300.0 * 160.0 + 2700.0 * 150.0 / cos
    assert line(res, "CONCRETE", "flight A")["quantity"] == pytest.approx(area * 1200.0 / 1e9)


# 15: an unresolved dimension stays HELD: blank, never 0
def test_unresolved_dimension_held_blank():
    res = M.check_stair(straight(10, 160.0, waist=None))
    ln = line(res, "CONCRETE", "flight A")
    assert ln["status"] == M.HELD and ln["quantity"] is None and "waist thickness" in ln["missing"]
    csv_text = M.export_csv(M.measured_rows(res))
    row = [r for r in csv_text.splitlines() if ",CONCRETE,flight A," in r][0]
    assert row.split(",")[5] == ""


# --- extras named in the task row
def test_integer_and_decimal_riser_count():
    assert M.riser_count_exact(4.48, 0.16) == 28
    assert math.ceil(4.48 / 0.16) == 29                                   # why binary division is never used
    assert M.riser_count_exact(4480, 160) == 28


def test_f0_given_f1_unknown():
    lv = M.levels(straight(10, 160.0, s=30.0, f0=100.0, f1=None))
    assert lv["risers"][0]["structural_riser_mm"] == pytest.approx(230.0)
    assert lv["risers"][-1]["structural_riser_mm"] is None and lv["risers"][-1]["status"] == M.HELD
    assert lv["closure"] is None


def test_last_riser_onto_a_landing_with_another_finish():
    lv = M.levels(dog_leg(6, 6, 160.0, s_a=30.0, s_land=10.0))
    assert lv["risers"][5]["onto"] == "L" and lv["risers"][5]["structural_riser_mm"] == pytest.approx(180.0)


def test_mirrored_stair_same_quantities():
    arc = [(0.0, 0.0), (2600.0, 0.0), (2600.0, 1200.0, 0.23), (0.0, 1200.0)]
    a = dog_leg(6, 6, 160.0, landing_poly=arc)
    b = copy.deepcopy(a)
    for s in b["surfaces"]:
        if s.get("polygon"):
            s["polygon"] = [(-p[0], p[1]) + ((-p[2],) if len(p) == 3 else ()) for p in s["polygon"]]
    qa = [(x["component"], x["part"], x["quantity"]) for x in M.check_stair(a)["lines"]]
    qb = [(x["component"], x["part"], x["quantity"]) for x in M.check_stair(b)["lines"]]
    assert [q[:2] for q in qa] == [q[:2] for q in qb]
    for (_, _, x), (_, _, y) in zip(qa, qb):
        assert (x is None and y is None) or x == pytest.approx(y)


def test_finish_material_unknown_holds_marble_not_levels():
    res = M.check_stair(straight(10, 160.0, finish=None))
    assert line(res, "MARBLE_TREAD", "T1")["status"] == M.HELD
    assert res["levels"]["risers"][0]["structural_riser_mm"] == pytest.approx(230.0)
    assert MARBLE["material"] == "MARBLE"


def test_rect_helper():
    assert SG.polygon_area(rect(0, 0, 3, 2)) == 6
