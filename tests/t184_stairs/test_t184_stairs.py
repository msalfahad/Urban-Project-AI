"""T-184: staircase inventory, continuity, landing ownership, drawing conflicts and stair concrete.

Synthetic 'Villa Q' (not the development villa), metres unless stated:
  ST-A dog-leg core, storeys 0.00 / 3.60 / 7.20, two flights per storey in one place (stacked):
    A1 box (2.0, 0, 3.2, 3.0) 0.00 -> 1.80     A2 box (3.3, 0, 4.5, 3.0) 1.80 -> 3.60   (GF roof slab plan)
    A3 = A1 place 3.60 -> 5.40                  A4 = A2 place 5.40 -> 7.20                (1F roof slab plan)
  ST-B straight stair box (8.0, 0, 9.2, 4.0) 0.00 -> 3.60, drawn on the GF plan and again (seen) on the 1F plan.
Hand calculations:
  flight 10 risers x 0.175, going 0.28, 9 goings, width 1.10, waist 0.15:
    steps 10 x 1/2 x 0.175 x 0.28 x 1.10 = 0.2695 m3
    waist 1.10 x 0.15 x hypot(9 x 0.28, 9 x 0.175) = 0.165 x hypot(2.52, 1.575) = 0.165 x 2.971704 = 0.490331 m3
  landing 1.20 x 2.40 x 0.15 = 0.432 m3; with 0.05 m2 column corner deducted (2.88 - 0.05) x 0.15 = 0.4245 m3
  owner stair rule (OWNER_RULE_STAIRS): 4.48 m -> 28 risers (not 29 from 28.000000000000004); 3.20 -> 20 x 0.160 no
  flag; 4.50 m drawn 27 -> 0.16667 > 0.16 FLAG, drawn governs.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_P = ROOT / "research" / "agents_t184"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _P / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, mod)
    spec.loader.exec_module(mod)
    return sys.modules[name]


SI = _load("t184_stair_inventory")
LG = _load("t184_alsenan_ledger")
FD = SI.FlightDrawing


def villa_q(transform=lambda b: b):
    t = transform
    return [
        FD("S-GF", "SLAB_PLAN", t((2.0, 0.0, 3.2, 3.0)), 0.00, 1.80, 12, 0.28, 1.20),
        FD("S-GF", "SLAB_PLAN", t((3.3, 0.0, 4.5, 3.0)), 1.80, 3.60, 12, 0.28, 1.20),
        FD("S-1F", "SLAB_PLAN", t((2.0, 0.0, 3.2, 3.0)), 3.60, 5.40, 12, 0.28, 1.20),
        FD("S-1F", "SLAB_PLAN", t((3.3, 0.0, 4.5, 3.0)), 5.40, 7.20, 12, 0.28, 1.20),
        FD("A-GF", "ARCH_PLAN", t((8.0, 0.0, 9.2, 4.0)), 0.00, 3.60, 22, 0.28, 1.20),
        FD("A-1F", "ARCH_PLAN", t((8.0, 0.0, 9.2, 4.0)), 0.00, 3.60, 22, 0.28, 1.20),   # seen from above
    ]


FLOORS = [0.00, 3.60, 7.20]


def _rot(b):                     # 90 degrees: (x, y) -> (-y, x), box normalised
    return (-b[3], b[0], -b[1], b[2])


def _mir(b):                     # mirror about x = 0
    return (-b[2], b[1], -b[0], b[3])


# ---------------------------------------------------------------- stacked flights (D-T184-1)
@pytest.mark.parametrize("tf", [lambda b: b, _rot, _mir])
def test_stacked_flights_are_separate_and_seen_flight_is_once(tf):
    fl = SI.physical_flights(villa_q(tf))
    assert len(fl) == 5                                   # A1..A4 + one straight flight (drawn twice, same levels)
    st = [f for f in fl if len(f.drawings) == 2]
    assert len(st) == 1 and st[0].z_from == 0.0 and st[0].z_to == 3.60
    assert all(f.status == "ESTABLISHED" for f in fl)


def test_adverse_released_twin_rule_loses_the_upper_storey_flights():
    """the released 'drawn again on' rule (levels ignored) keeps 3 of the 5 physical flights: A3 and A4 vanish."""
    old = SI.released_twin_rule(villa_q())
    new = SI.physical_flights(villa_q())
    assert len(old) == 3 and len(new) == 5
    lost = {(f.z_from, f.z_to) for f in new} - {(f.z_from, f.z_to) for f in old}
    assert lost == {(3.60, 5.40), (5.40, 7.20)}


def test_unknown_levels_on_a_stacked_pair_are_undetermined_never_merged():
    d = villa_q()
    d[2] = FD("S-1F", "SLAB_PLAN", (2.0, 0.0, 3.2, 3.0), None, None)
    fl = SI.physical_flights(d)
    assert len(fl) == 5
    und = [f for f in fl if f.status == "UNDETERMINED"]
    assert len(und) == 2 and {f.z_from for f in und} == {0.0, None}


# ---------------------------------------------------------------- two staircases, one omitted
def test_two_staircases_identified_and_none_omitted():
    drawn = villa_q()
    stairs = SI.assemble_stairs(SI.physical_flights(drawn))
    assert [s["stair_id"] for s in stairs] == ["ST-01", "ST-02"]
    assert len(stairs[0]["flights"]) == 4 and stairs[0]["levels"] == [0.0, 1.8, 3.6, 5.4, 7.2]
    assert len(stairs[1]["flights"]) == 1
    assert SI.unassigned(drawn, stairs) == []


def test_adverse_second_staircase_omitted_is_reported():
    drawn = villa_q()
    stairs = SI.assemble_stairs(SI.physical_flights(drawn[:4]))        # inventory built without the straight stair
    miss = SI.unassigned(drawn, stairs)
    assert len(miss) == 2 and {m.sheet for m in miss} == {"A-GF", "A-1F"}


# ---------------------------------------------------------------- continuity: ends at one floor vs continues
def test_stair_ending_at_one_floor_vs_continuing():
    stairs = SI.assemble_stairs(SI.physical_flights(villa_q()))
    core, straight = stairs
    assert SI.continues_above(core, 3.60) is True
    assert SI.floors_served(core, FLOORS) == dict(floors=[0.0, 3.6, 7.2], ends_at=7.2, continues_above_top=False)
    assert SI.continues_above(straight, 3.60) is False
    assert SI.floors_served(straight, FLOORS)["ends_at"] == 3.6


def test_adverse_continuation_never_inferred_from_a_lower_plan():
    """only the GF slab plan read: the core must END at 3.60, not be extended to 7.20 by analogy."""
    stairs = SI.assemble_stairs(SI.physical_flights(villa_q()[:2]))
    assert SI.floors_served(stairs[0], FLOORS) == dict(floors=[0.0, 3.6], ends_at=3.6, continues_above_top=False)


# ---------------------------------------------------------------- landing vs floor slab
def test_landing_at_floor_inside_slab_is_floor_slab_intermediate_is_stair():
    floor_l = SI.Landing("L-1F", 3.60, (2.0, 3.0, 4.5, 4.2), 0.15, inside_floor_slab=True)
    mid_l = SI.Landing("L-MID", 1.80, (2.0, 3.0, 4.5, 4.2), 0.15)
    assert SI.landing_owner(floor_l, FLOORS) == "FLOOR_SLAB"
    assert SI.landing_owner(mid_l, FLOORS) == "STAIR"


def test_adverse_floor_level_landing_outside_any_slab_panel_stays_stair():
    l = SI.Landing("L-1F", 3.60, (2.0, 3.0, 4.5, 4.2), 0.15, inside_floor_slab=False)
    assert SI.landing_owner(l, FLOORS) == "STAIR"


def test_alsenan_floor_arrival_landings_not_counted_twice():
    data = LG.load()
    st1 = LG.stair_ledger(data["stairs"][0], [1.00, 5.50, 9.70])
    owners = {r["part"]: r.get("owner") for r in st1["rows"] if "owner" in r}
    assert owners["1F-ARRIVAL landing"] == owners["2F-ARRIVAL landing"] == "FLOOR_SLAB"
    assert owners["MS1-LD landing"] == owners["MS2-LD landing"] == "STAIR"
    # the floor-arrival landings (2 x 1.95 x 2.50 x 0.16 = 1.560 m3) are NOT in the stair total
    assert st1["measured_m3"] == pytest.approx(4.8364, abs=1e-4)


# ---------------------------------------------------------------- architectural vs structural conflict
def test_arch_vs_struct_dimension_conflict_keeps_both_values():
    a = FD("A-1F", "ARCH_PLAN", (0, 0, 1, 1), 5.50, 9.70, 11, 0.30, 1.20)
    s = FD("SEC", "SECTION", (0, 0, 1, 1), 5.50, 9.70, 12, 0.30, 1.15)
    c = SI.compare_readings(a, s)
    assert {x["field"] for x in c} == {"risers", "width"}
    r = [x for x in c if x["field"] == "risers"][0]
    assert (r["architectural"], r["structural"], r["status"]) == (11, 12, "CONFLICT")


def test_matching_readings_raise_no_conflict():
    a = FD("A", "ARCH_PLAN", (0, 0, 1, 1), 1.0, 5.5, 12, 0.30, 1.20)
    assert SI.compare_readings(a, FD("S", "SLAB_PLAN", (0, 0, 1, 1), 1.0, 5.5, 12, 0.30, 1.205)) == []


# ---------------------------------------------------------------- concrete, units, missing data
def test_flight_and_landing_concrete_hand_calc():
    c = SI.flight_concrete(10, 0.175, 0.28, 9, 1.10, 0.15)
    assert c["steps"] == pytest.approx(0.2695, abs=1e-9)
    assert c["waist"] == pytest.approx(0.165 * math.hypot(2.52, 1.575), abs=1e-9)
    assert c["waist"] == pytest.approx(0.490331, abs=1e-6)
    assert SI.landing_concrete(1.20, 2.40, 0.15) == pytest.approx(0.432)
    assert SI.landing_concrete(1.20, 2.40, 0.15, 0.05) == pytest.approx(0.4245)


def test_adverse_missing_waist_is_held_never_zero():
    c = SI.flight_concrete(10, 0.175, 0.28, 9, 1.10, None)
    assert c["waist"] is None
    t = SI.stair_total([("F steps", c["steps"]), ("F waist", c["waist"])])
    assert t == dict(measured_m3=pytest.approx(0.2695), held=["F waist"])
    assert SI.landing_concrete(None, 2.4, 0.15) is None


def test_units_mm_cm_m_and_refused_unit():
    assert SI.to_m(1200, "mm") == pytest.approx(1.2)
    assert SI.to_m(120, "cm") == pytest.approx(1.2)
    assert SI.to_m(1.2, "m") == 1.2
    with pytest.raises(ValueError):
        SI.to_m(1.2, "ft")


def test_owner_stair_rule_is_a_check_and_avoids_the_float_trap():
    assert SI.owner_rule_check(4.48, 28)["rule_risers"] == 28
    ok = SI.owner_rule_check(3.20, 20)
    assert ok["flag"] is False and ok["governs"] == "DRAWN"
    bad = SI.owner_rule_check(4.50, 27)
    assert bad["rule_risers"] == 29 and bad["flag"] is True and bad["drawn_risers"] == 27


# ---------------------------------------------------------------- development villa ledger (re-derivation of T-111)
def test_alsenan_ledger_rederives_t111_and_keeps_every_storey():
    data = LG.load()
    led = {s["stair_id"]: s for s in (LG.stair_ledger(s, [1.00, 5.50, 9.70]) for s in data["stairs"])}
    t111 = json.loads((ROOT / "research" / "agents_t111" / "ledger_summary.json").read_text())["summary"]
    assert led["ST-01"]["net_m3"] == pytest.approx(t111["main_drawn_after_ledger_m3"], abs=1e-4)      # 4.746
    assert led["ST-02"]["net_m3"] == pytest.approx(t111["round_calculated_m3"] - t111["round_ledger_deducted_m3"],
                                                   abs=1e-4)                                              # 1.561
    assert led["ST-03"]["net_m3"] == pytest.approx(t111["entrance_m3"], abs=1e-4)                       # 0.357
    assert led["ST-01b"]["net_m3"] == pytest.approx(t111["lobby_m3"], abs=1e-4)                         # 0.126
    parts = {r["part"].split()[0] for r in led["ST-01"]["rows"]}
    assert {"MS2-L", "MS2-U", "MS2-LD"} <= parts                         # the 1F -> 2F storey is in the ledger
    held = {h["id"] for h in led["ST-02"]["held"]}
    assert {"RS-C", "RS-C-SOFFIT"} <= held                               # curved part held (Q-50 / Q-51), not 0
    assert led["ST-03"]["held"] and led["ST-03"]["held"][0]["candidate_m3"] is None


def test_alsenan_freelancer_reconciliation_closes_to_zero():
    data = LG.load()
    led = [LG.stair_ledger(s, [1.00, 5.50, 9.70]) for s in data["stairs"]]
    rec = LG.reconcile(data, led)["ST01"]
    f, l = rec["his_flights_minus_own"], rec["his_landings_minus_own"]
    assert abs(f["residual"]) < 1e-9 and abs(l["residual"]) < 1e-9
    assert rec["freelancer"] - rec["own_net"] == pytest.approx(
        f["length_5_3_vs_drawn"] + f["thickness_0_28_vs_drawn"] + l["area_5_04_vs_4_44"] + l["thickness_0_20_vs_0_16"],
        abs=1e-9)
