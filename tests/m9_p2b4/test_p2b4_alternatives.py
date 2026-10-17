"""Phase 2B-4 constructability audit: the planners of the construction calculator reproduce the hand-derived plans
and the hand-verified points of the junction-flange sweep (where the roll count and the selected layout change)."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import construct_cases as CC                                  # noqa: E402
import construct_reference as CR                              # noqa: E402


def _close(a, b):
    return abs(a - b) < 0.0005


def test_the_sweep_at_the_hand_verified_flange_widths():
    rows = {r["j_mm"]: r for r in CR.sweep(CC.ROOM_B, CR.URBAN, [100, 110, 150, 160])}
    for key, want in CC.SWEEP_HAND.items():
        j = int(round(float(key.split("_")[1]) * 1000))
        for reading in ("V25", "RULE"):
            along, rolls, m2, seams = rows[j][reading]
            w = want[reading]
            assert (along, rolls, seams) == (w[0], w[1], w[3]) and _close(m2, w[2]), (key, reading, rows[j][reading])


def test_the_planners_find_the_hand_plans():
    for case, along, obj, j in ((CC.WPB_A1, "Y", CR.LEAST_MEMBRANE, 100), (CC.WPB_A1_FJ, "Y", CR.FEWEST_JOINTS, 100),
                                (CC.WPB_A2_LM, "X", CR.LEAST_MEMBRANE, 150), (CC.WPB_A2_FJ, "X", CR.FEWEST_JOINTS, 150),
                                (CC.WPD_A1, "X", CR.LEAST_MEMBRANE, 100), (CC.WPD_FJ, "X", CR.FEWEST_JOINTS, 100)):
        key, plan, _ = CR.plan_A(CC.ROOMS[case["room"]], CR.URBAN, along, obj, j)
        q = CR.summary(CR.verify(CC.ROOMS[case["room"]], CR.URBAN, plan))
        e = case["expected"]
        assert (q["rolls"], q["seams"]) == (e["rolls"], e["seams"]) and _close(q["consumed_m2"], e["consumed_m2"]), \
            (case["id"], q["rolls"], q["seams"], q["consumed_m2"])
    for case in (CC.WPB_B, CC.WPE_B):
        _, plan = CR.plan_B(CC.ROOMS[case["room"]], CR.URBAN, "X", CR.FEWEST_JOINTS)
        q = CR.summary(CR.verify(CC.ROOMS[case["room"]], CR.URBAN, plan))
        e = case["expected"]
        assert (q["rolls"], q["seams"]) == (e["rolls"], e["seams"]) and _close(q["consumed_m2"], e["consumed_m2"])


def test_fold_up_along_y_needs_a_splice_or_a_third_roll():
    """3.40 m strips: two per roll; five strips need three rolls, or two with one end-lapped splice (one more seam)."""
    k1, _ = CR.plan_B(CC.ROOM_B, CR.URBAN, "Y", CR.FEWEST_JOINTS, splice=False)
    k2, p2 = CR.plan_B(CC.ROOM_B, CR.URBAN, "Y", CR.FEWEST_JOINTS, splice=True)
    assert k1 == (3, 4, 17000) and k2 == (2, 5, 17100)
    q = CR.summary(CR.verify(CC.ROOM_B, CR.URBAN, p2))
    assert q["floor_end_laps"] == 1 and q["rolls"] == 2


def test_the_doorway_jambs_and_corners_are_never_complete_without_a_detail():
    """method A: every jamb is an open butt joint between the doorway piece and the band end; method B: every jamb
    a slit. Corners: pleats (internal) and gaps (external) are reported, never treated."""
    for case in CC.PLANS:
        res = CR.verify(CC.ROOMS[case["room"]], CR.URBAN, case["plan"])
        doors = len(CC.ROOMS[case["room"]]["doors"])
        if res["method"] == "A":
            assert len(res["jambs"]) == 2 * doors and all(x["state"] == "BUTT_JOINT_OPEN" for x in res["jambs"])
            assert all(c["kind"] in (CR.INTERNAL, CR.EXTERNAL) for c in res["corners"])
        else:
            assert res["jamb_slits"] == 2 * doors and res["corner_excess"] > 0
