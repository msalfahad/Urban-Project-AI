"""Phase 2B-3 (ARCH_TAKEOFF_V2.5) waterproofing proofs - WP-2 / WP-3 of the program: every case's hand calculation
agrees with the independent reference calculator, then with the engine, in the case sequence (a case is compared
only when every simpler case before it passes); the 3.00 x 4.00 m bathroom's strip-by-strip cut inventory; the
installability of every cutting plan; the shared roll inventory; and the V2.4 results on the same cases, recorded as
FAILED_VALIDATION where the proof found its defects (V2.4 itself is frozen and not corrected)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import proof_cases as C                                       # noqa: E402
import proof_check as PC                                      # noqa: E402
import proof_engine as E                                      # noqa: E402

CASES = [c for c in sorted(C.WP_CASES, key=lambda c: c["sequence"]) if c["id"] != "WP-H"]
# the quantities on which V2.4 disagrees with the hand calculation, per case (the defects of DEFECT_REGISTER.md)
V24_FAILS = {
    "WP-A": {"band_pieces_m", "consumed_m2", "waste_m2", "cuts_m", "untouched_m2", "final_material_state"},
    "WP-B": {"band_pieces_m", "consumed_m2", "waste_m2", "cuts_m", "untouched_m2", "alt_rolls", "alt_seams",
             "alt_consumed_m2", "rolls_if_threshold_upturned", "final_material_state"},
    "WP-S": {"band_pieces_m", "consumed_m2", "waste_m2", "cuts_m", "untouched_m2", "final_material_state"},
    "WP-C": {"band_pieces_m", "consumed_m2", "waste_m2", "cuts_m", "final_material_state"},
    "WP-CX": {"direction", "floor_strips", "last_strip_w_m", "band_pieces_m", "band_joints", "laps_m2",
              "detailing_m2", "B_m2", "consumed_m2", "waste_m2", "cuts_m", "alt_rolls", "alt_seams", "alt_consumed_m2",
              "final_material_state"},
    "WP-BX": {"band_pieces_m", "band_joints", "laps_m2", "B_m2", "consumed_m2", "waste_m2"},
    "WP-LX": {"band_pieces_m", "consumed_m2", "waste_m2", "cuts_m", "alt_consumed_m2"},
    "WP-D": {"band_pieces_m", "consumed_m2", "waste_m2", "cuts_m", "final_material_state"},
    "WP-E": {"band_pieces_m", "consumed_m2", "waste_m2", "cuts_m", "alt_consumed_m2", "final_material_state"},
    "WP-F": {"band_pieces_m", "consumed_m2", "waste_m2", "final_material_state"},
    "WP-G": {"band_pieces_m", "consumed_m2", "waste_m2", "final_material_state"},
    "WP-W": {"band_pieces_m", "consumed_m2", "waste_m2", "cuts_m"},
}


@pytest.mark.parametrize("case", [c for c in C.WP_CASES if c.get("reference")], ids=lambda c: c["id"])
def test_the_hand_calculation_agrees_with_the_independent_reference(case):
    rows = PC.hand_vs_reference(case)
    assert len(rows) >= 10
    assert [r for r in rows if r["result"] != "AGREE"] == []


def test_the_cases_pass_in_sequence_simplest_first():
    """'Do not progress to a more complicated case until the simpler case passes': the cases are compared in their
    sequence and the comparison stops at the first failure (the assertion names it)."""
    assert [c["id"] for c in CASES] == [x for x in C.SEQUENCE if x != "WP-H"]
    passed = []
    for c in CASES:
        rows = E.compare(c["expected"], E.wp_quantities(E.wp_area(c, E.V25)))
        bad = [(r["quantity"], r["expected"], r["engine"]) for r in rows if r["result"] == "FAIL"]
        assert not bad, (c["id"], "after", passed, bad)
        passed.append(c["id"])
    assert passed[:2] == ["WP-A", "WP-B"]


def test_v2_4_fails_exactly_where_the_proof_found_its_defects():
    for c in CASES:
        rows = E.compare(c["expected"], E.wp_quantities(E.wp_area(c, E.V24)))
        assert {r["quantity"] for r in rows if r["result"] == "FAIL"} == V24_FAILS[c["id"]], c["id"]


def test_the_3x4_bathroom_cut_inventory_strip_by_strip():
    """WP-2: the exact cutting plan of the 3.00 x 4.00 m bathroom and the two figures the owner asked to prove -
    17.80 m2 consumed and 2 rolls - from the engine's own roll records."""
    a = E.wp_area(C.WP_B, E.V25)
    lay = a["layout"]["layout"]
    rolls = [[(s["length_m"], s["for"]) for s in r["segments"]] for r in lay["rolls"]]
    assert rolls == [[(3.0, "floor strip 1"), (3.0, "floor strip 2"), (3.0, "floor strip 3")],
                     [(3.0, "floor strip 4"), (3.0, "floor strip 5"), (2.8, "upturn lanes")]]
    assert [r["untouched_tail_m"] for r in lay["rolls"]] == [1.0, 1.2]
    assert sum(s["length_m"] for r in lay["rolls"] for s in r["segments"]) == pytest.approx(17.8)
    assert (a["row"]["consumed_m2"], a["row"]["rolls_if_installed_alone"]) == (17.8, 2)
    assert lay["band_planner"]["segments"] == [{"length_m": 2.8, "basis": "SHORTEST_FINISHING_SEGMENT"}]
    assert lay["roll_packing"]["proven"] is True and lay["roll_packing"]["lower_bound"] == 2
    # laps: 4 side seams of 3.00 m, the band lap onto the floor 13.00 m, 4 band joints, the doorway piece lap
    s = lay["seams"]
    assert (s["longitudinal"]["count"], s["upturn_end_laps"]["count"], s["upturn_to_floor_lap"]["running_lm"],
            s["doorway_to_floor_lap"]["running_lm"]) == (4, 4, 13.0, 1.0)
    # offcuts: the 0.60 x 3.00 trim of strip 5 became two lanes (no scrap); scrap = the band segment residue
    assert [x[:2] for x in lay["scrap"]] == [[0.1, 2.8]] and lay["offcuts_retained"] == []
    # the proven subtotal is kept apart from the provisional final material requirement
    assert a["row"]["proven_subtotal"]["total_m2"] == 14.8 and a["row"]["final_material_state"] == \
        "PROVISIONAL_DETAILS_OPEN"
    assert a["row"]["roll_sensitivity"]["rolls_if_every_open_doorway_is_upturned"] == 2
    assert any(w["what"].startswith("DOOR_THRESHOLD_TRANSITION") for w in a["row"]["withheld"])


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_every_cutting_plan_is_installable(case):
    """no optimisation beyond what can be installed: every cut fits a roll; a roll's cuts never exceed its length;
    every lapped band piece covers something past its 0.10 m lap; the material balances (consumed = installed +
    waste + retained offcuts; gross = consumed + untouched roll remainders); every lane comes from a whole lane
    width (no narrow offcut is used as a band)."""
    a = E.wp_area(case, E.V25)
    lay = a["layout"]
    L = lay["layout"]
    lap = next((r["value"] for r in case["scenario"]["rules"] if r["parameter"] == "lap_m"), 0.1)
    for r in L["rolls"]:
        assert all(0 < s["length_m"] <= 10.0 + 1e-9 for s in r["segments"])
        assert sum(s["length_m"] for s in r["segments"]) <= 10.0 + 1e-9
    assert all(p > lap + 1e-9 for p in L["band_pieces_m"][1:])
    assert lay["consumed_m2"] == pytest.approx(lay["placed_m2"] + lay["overlap_m2"] + lay["cutting_waste_m2"] +
                                               lay["reusable_offcuts_m2"], abs=1e-6)
    assert lay["packaging"]["pack_total_m2"] == pytest.approx(lay["consumed_m2"] +
                                                              lay["packaging"]["packaging_surplus_m2"], abs=1e-6)
    assert all(w < L["band_width_m"] - 1e-9 or why.endswith("unused lane") for w, ln, why in L["scrap"])


def test_shared_roll_inventory_with_its_conditions():
    """WP-H: the wet-area rooms share rolls (3 instead of 4 bought per room); the exterior system never joins them;
    the exact packing finds the 3-roll plan that first fit decreasing misses (V2.4: 4); every shared roll carries
    whole full-width pieces only."""
    plans, built = E.wp_shared([C.WP_B, C.WP_A, C.WP_W, C.WP_G], E.V25)
    wet = next(p for p in plans if p["system_id"] == "URBAN_DEFAULT_WET_AREA")
    ext = next(p for p in plans if p["system_id"] == "URBAN_DEFAULT_EXTERIOR")
    exp = C.WP_H["expected"]
    assert (wet["rolls"], wet["rolls_if_each_area_alone"], ext["rolls"], len(plans)) == (
        exp["wet_rolls"], exp["wet_rolls_alone"], exp["exterior_rolls"], exp["systems"])
    assert sum(p["length_m"] for r in wet["cutting_plan"] for p in r["pieces"]) == pytest.approx(exp["wet_cut_m"])
    assert wet["packing"]["proven"] and wet["packing"]["lower_bound"] == 3 and \
        wet["packing"]["first_fit_decreasing"] == exp["v24_first_fit_rolls"]
    assert set(wet["areas"]) == {"WP-B", "WP-A", "WP-W"} and ext["areas"] == ["WP-G"]
    assert all(r["sharing"]["review"] is None for r in wet["cutting_plan"])            # one floor
    assert any("narrow offcuts stay with the area" in x for x in wet["sharing_conditions"])
    v24, _ = E.wp_shared([C.WP_B, C.WP_A, C.WP_W, C.WP_G], E.V24)
    assert next(p for p in v24 if p["system_id"] == "URBAN_DEFAULT_WET_AREA")["rolls"] == 4
    assert "packing" not in v24[0]


def test_a_roll_carried_between_floors_is_flagged():
    a = E.wp_area(C.WP_B, E.V25, room_id="GF-B", floor="GF")
    b = E.wp_area(C.WP_W, E.V25, room_id="1F-W", floor="1F")
    with E.K.using("1.1.0"):
        p = E.WS.cutting_plan([a, b], exact=True)[0]
    shared = [r for r in p["cutting_plan"] if len(r["sharing"]["floors"]) > 1]
    assert shared and all(r["sharing"]["review"].startswith("ROLL_CARRIED_BETWEEN_FLOORS") for r in shared)
