"""Phase 2B-4 constructability audit: every cutting plan of the audit, rebuilt piece by piece by the construction
calculator, is physically complete (each piece fits the material it is cut from, every floor / upturn / doorway
surface is covered on a 10 mm grid, every joint laps, the material balances) and gives exactly the quantities of its
hand derivation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import construct_cases as CC                                  # noqa: E402
import construct_reference as CR                              # noqa: E402

TOL = 0.0005


@pytest.mark.parametrize("case", CC.PLANS, ids=[p["id"] for p in CC.PLANS])
def test_the_plan_is_buildable_and_matches_its_hand_derivation(case):
    res = CR.verify(CC.ROOMS[case["room"]], CR.URBAN, case["plan"])
    got = CR.summary(res)
    for k, v in case["expected"].items():
        assert k in got, (case["id"], k)
        if isinstance(v, float):
            assert got[k] is not None and abs(got[k] - v) <= TOL, (case["id"], k, v, got[k])
        else:
            assert got[k] == v, (case["id"], k, v, got[k])


def test_material_is_conserved_and_classified_in_every_plan():
    for case in CC.PLANS:
        q = CR.summary(CR.verify(CC.ROOMS[case["room"]], CR.URBAN, case["plan"]))
        assert abs(q["consumed_m2"] - q["installed_m2"] - q["true_waste_m2"] - q["reusable_m2"]) < 1e-6, case["id"]


def test_a_plan_with_a_gap_or_a_short_joint_is_rejected():
    """the calculator is not a formula: a band one piece short, a piece cut from too little material, or a floor
    strip of the wrong width fails."""
    room, plan = CC.ROOMS["WP-B"], CC.WPB_A1["plan"]
    short = dict(plan, runs=[["B1", "B2", "B3", "B4"]])
    with pytest.raises(AssertionError):
        CR.verify(room, CR.URBAN, short)
    over = dict(plan, cross=dict(plan["cross"], L1=[("DW", 1000), ("B2", 2100)]))
    with pytest.raises(AssertionError):
        CR.verify(room, CR.URBAN, over)
    narrow = dict(plan, rip=dict(plan["rip"], C5=[("S5", 300), ("L1", 300), ("L2", 300)]))
    with pytest.raises(AssertionError):
        CR.verify(room, CR.URBAN, narrow)
    no_door = dict(plan, doorways={})
    with pytest.raises(AssertionError):
        CR.verify(room, CR.URBAN, no_door)


def test_the_3x4_inventory_strip_by_strip():
    """WP-2 of the program: every piece of the as-planned 3 x 4 m bathroom, its source roll, size and destination."""
    res = CR.verify(CC.ROOM_B, CR.URBAN, CC.WPB_A1["plan"])
    rows = {r["id"]: r for r in res["pieces"]}
    want = {"S1": (1000, 3000, 1, "floor strip 1"), "S2": (1000, 3000, 1, "floor strip 2"),
            "S3": (1000, 3000, 1, "floor strip 3"), "S4": (1000, 3000, 2, "floor strip 4"),
            "S5": (400, 3000, 2, "floor strip 5"), "DW": (300, 1000, 2, "doorway D1"), "B1": (300, 3000, 2, "run 1"),
            "B2": (300, 2000, 2, "run 1"), "B3": (300, 2800, 2, "run 1"), "B4": (300, 2800, 2, "run 1"),
            "B5": (300, 2800, 2, "run 1"), "G~w": (100, 2800, 2, "offcut")}
    for pid, (w, ln, roll, dest) in want.items():
        assert (rows[pid]["w"], rows[pid]["l"], rows[pid]["roll"]) == (w, ln, roll), pid
        assert rows[pid]["to"].startswith(dest), (pid, rows[pid]["to"])
    assert res["tails"] == [1000, 1200]
