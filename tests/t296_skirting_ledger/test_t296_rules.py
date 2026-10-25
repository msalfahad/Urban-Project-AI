"""T-296: skirting opening-to-line rules on a hand NON-Alsenan fixture (villa K296, synthetic, hand-calculated).

Room K296-B1 (dry bedroom 4.00 x 3.50 m, boundary 15.00 m), pieces walked anticlockwise:
  wall A 4.00 m with door D-1 0.90 m  -> WALL 3.10 + DOOR 0.90
  wall B 3.50 m wall-tiled to the floor (another finish owns the base) -> TILED_WALL 3.50
  wall C 4.00 m with window W-1 1.20 m, sill 0.90 m (printed)          -> WALL 2.80 + WINDOW 1.20 (skirted under the sill)
  wall D 3.50 m with door D-2 0.80 m  -> WALL 2.70 + DOOR 0.80
  skirting = 3.10 + 2.80 + 1.20 + 2.70 = 9.80 lm = 15.00 - doors 1.70 - tiled base 3.50
Variants: W-1 sill not established -> HELD range 8.60 .. 9.80 lm; W-1 sill 0.00 (floor glazing) -> 8.60 lm.
Line trail: candidate line gross 15.00, listed doors 1.70, net 8.60 -> unlisted 1.20 (W-1) + tiled base 3.50 ... named.
"""
from __future__ import annotations

import copy
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t296"))

import skirting_opening_rules as R  # noqa: E402


def room(sill_state="ESTABLISHED", sill_m=0.90):
    return {"room_id": "K296-B1", "finish_class": "DRY", "pieces": [
        {"piece_id": "A1", "kind": "WALL", "length_m": 3.10},
        {"piece_id": "A2", "kind": "DOOR", "opening_id": "D-1", "length_m": 0.90},
        {"piece_id": "B", "kind": "TILED_WALL", "length_m": 3.50},
        {"piece_id": "C1", "kind": "WALL", "length_m": 2.80},
        {"piece_id": "C2", "kind": "WINDOW", "opening_id": "W-1", "length_m": 1.20, "sill_state": sill_state,
         "sill_m": sill_m},
        {"piece_id": "D1", "kind": "WALL", "length_m": 2.70},
        {"piece_id": "D2", "kind": "DOOR", "opening_id": "D-2", "length_m": 0.80}]}


def test_normal_two_doors_one_tiled_wall():
    out = R.room_ledger(room())
    assert out["status"] == "DETERMINATE"
    assert out["certain_lm"] == pytest.approx(9.80, abs=1e-9)
    assert out["boundary_lm"] == pytest.approx(15.00, abs=1e-9)
    assert [(d["opening_id"], d["length_m"]) for d in out["deductions"]] == [("D-1", 0.90), ("D-2", 0.80)]
    assert out["boundary_lm"] - sum(d["length_m"] for d in out["deductions"]) - 3.50 == pytest.approx(9.80, abs=1e-9)


def test_sill_not_established_is_a_range_never_certain():
    out = R.room_ledger(room("HELD", None))
    assert out["status"] == "HELD"
    assert out["certain_lm"] == pytest.approx(8.60, abs=1e-9)
    assert out["range_lm"] == (pytest.approx(8.60, abs=1e-9), pytest.approx(9.80, abs=1e-9))
    assert {d["opening_id"]: d["basis"] for d in out["deductions"]}["W-1"] == "HELD_RANGE"


def test_floor_glazing_is_deducted():
    out = R.room_ledger(room("ESTABLISHED", 0.0))
    assert out["status"] == "DETERMINATE" and out["certain_lm"] == pytest.approx(8.60, abs=1e-9)


def test_order_and_mirror_invariant():
    base = R.room_ledger(room())["certain_lm"]
    rr = room()
    for seed in range(5):
        r2 = copy.deepcopy(rr)
        random.Random(seed).shuffle(r2["pieces"])
        assert R.room_ledger(r2)["certain_lm"] == base
    r3 = copy.deepcopy(rr)
    r3["pieces"].reverse()                       # mirrored walk (clockwise)
    assert R.room_ledger(r3)["certain_lm"] == base


def test_wet_full_height_room_is_not_applicable_not_zero():
    r = room()
    r["finish_class"] = "WET_FULL_HEIGHT_TILE"
    out = R.room_ledger(r)
    assert out["status"] == "NOT_APPLICABLE" and out["certain_lm"] is None


# ---------------------------------------------------------------- adverse
def test_door_deducted_twice_refused():
    r = room()
    r["pieces"].append({"piece_id": "A3", "kind": "DOOR", "opening_id": "D-1", "length_m": 0.90})
    with pytest.raises(ValueError, match="deducted twice"):
        R.room_ledger(r)


def test_sill_window_deducted_refused():
    r = room()
    r["pieces"][4]["deduct"] = True
    with pytest.raises(ValueError, match="established sill above the floor"):
        R.room_ledger(r)


def test_tiled_wall_carrying_skirting_refused():
    r = room()
    r["pieces"][2]["skirted"] = True
    with pytest.raises(ValueError, match="another finish owns"):
        R.room_ledger(r)


def test_held_run_as_zero_refused():
    r = room()
    r["finish_class"] = "UNKNOWN"
    r["reported_lm"] = 0
    with pytest.raises(ValueError, match="reported as 0"):
        R.room_ledger(r)
    with pytest.raises(ValueError, match="reported as 0"):
        R.check_report("HELD", 0)
    assert R.check_report("HELD", None) is None


def test_missing_length_refused_never_zero():
    r = room()
    r["pieces"][0]["length_m"] = None
    with pytest.raises(ValueError, match="missing is never 0"):
        R.room_ledger(r)


def test_line_trail_names_the_unlisted_part():
    line = {"line_id": "L-K296", "gross": 15.00, "net": 8.60}
    deds = [{"opening_id": "D-1", "length_m": 0.90, "listed": True},
            {"opening_id": "D-2", "length_m": 0.80, "listed": True},
            {"cause": "tiled base B", "length_m": 3.50, "listed": True},
            {"opening_id": "W-1", "length_m": 1.20, "listed": False}]
    t = R.line_trail(line, deds)
    assert not t["readds_as_listed"] and t["readds_with_named"]
    assert t["unlisted_lm"] == pytest.approx(1.20) and t["residual_lm"] == pytest.approx(0.0, abs=1e-9)


def test_line_trail_threshold_twice_refused():
    line = {"line_id": "L-K296", "gross": 15.00, "net": 8.60}
    deds = [{"opening_id": "W-1", "length_m": 1.20, "listed": False},
            {"opening_id": "W-1", "length_m": 1.20, "listed": True}]
    with pytest.raises(ValueError, match="listed twice"):
        R.line_trail(line, deds)


def test_line_trail_unlisted_residual_is_reported_not_absorbed():
    line = {"line_id": "L-K296", "gross": 15.00, "net": 8.60}
    deds = [{"opening_id": "D-1", "length_m": 0.90, "listed": True}]
    t = R.line_trail(line, deds)
    assert not t["readds_with_named"] and t["residual_lm"] == pytest.approx(5.50)


def test_line_trail_missing_net_refused():
    with pytest.raises(ValueError, match="missing is never 0"):
        R.line_trail({"line_id": "x", "gross": 15.0, "net": None}, [])
