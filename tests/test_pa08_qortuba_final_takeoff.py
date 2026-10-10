"""The quantity set as it stands before anybody writes a rate against it, and the contractor sheet beside it.

Two claims. The takeoff is complete and sealed: every measurement that can be made from the frozen drawing has been
made, nothing is approved, and no rate exists. And the contractor comparison is validation rather than correction -
his sheet and ours were produced independently, so where they agree the agreement means something, and where they
differ our figure stays put and the difference is named.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.boq import final_takeoff as FT, opening_source_search as OS

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"


def reg(name):
    return json.loads((OUT / f"{name}.json").read_text("utf-8"))


def by_id():
    return {x["QUANTITY_ID"]: x for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]}


# ------------------------------------------------------------------ the window heights
def test_the_window_height_is_a_project_input_and_not_an_urban_default():
    assert OS.QORTUBA_WINDOW_HEIGHT_M == 1.500
    rules = {r["PARAMETER"]: r for r in reg("URBAN_OWNER_RULES_V1")["QORTUBA_PROJECT_RULES"]}
    w = rules["QORTUBA_WINDOW_HEIGHT"]
    assert w["VALUE"] == 1.500 and w["RULE_LEVEL"] == "QORTUBA_PROJECT_RULE"
    assert "this project only" in w["WHY"]
    # the Urban standard that forbids assuming a window height is untouched
    us = {x["TITLE"] for x in reg("URBAN_OWNER_RULES_V1")["URBAN_STANDARDS"]}
    assert "THERE_IS_NO_DEFAULT_WINDOW_HEIGHT" in us


def test_a_sliding_door_height_is_stored_but_no_opening_is_invented_for_it():
    """The owner gave heights for sliding doors this storey does not contain.  None is conjured up to use them."""
    c = reg("QORTUBA_OPENING_REGISTER_COMPLETED")
    assert c["SLIDING_DOORS_IN_THIS_SCOPE"] == 0
    for k, v in c["SLIDING_DOOR_INPUTS"].items():
        assert v["HEIGHT_M"] == 2.200
        assert v["PRESENT_IN_THIS_SCOPE"] is False and v["WHY"]
    assert not [r for r in c["ROWS"] if r["TYPE"] == "SLIDING_DOOR"]


# ------------------------------------------------------------------ the aluminium package
def test_the_aluminium_takeoff_comes_from_the_plan_and_totals_its_own_schedule():
    a = by_id()["Q-15"]
    p = a["PRE_CONTRACT_ALUMINIUM"]
    assert p["WINDOW_COUNT"] == 6
    assert abs(p["WINDOW_AREA_M2"] - sum(r["AREA_M2"] for r in a["SCHEDULE"])) < 1e-9
    assert p["TOTAL_PRE_CONTRACT_AREA_M2"] == a["MEASURED_NET_QUANTITY"] == 17.2459
    assert p["SLIDING_DOOR_COUNT"] == 0 and p["OTHER_EXTERNAL_COUNT"] == 0
    for r in a["SCHEDULE"]:
        assert abs(r["AREA_M2"] - round(r["WIDTH_M"] * r["HEIGHT_M"], 4)) < 1e-9
        assert r["HEIGHT_M"] == 1.5 and r["WIDTH_M"] > 0


# ------------------------------------------------------------------ §18 and §26 statuses
def test_a_complete_measurement_is_not_called_partial_for_a_missing_rate():
    q = by_id()
    assert q["Q-16"]["STATUS"] == "PRICING_BASIS_REQUIRED"
    assert q["Q-17"]["STATUS"] == "TRADE_CLASSIFICATION_PENDING"
    for qid in ("Q-16", "Q-17"):
        assert q[qid]["MEASURED_NET_QUANTITY"] is not None
        assert q[qid]["RESIDUAL_OPENINGS"] == [], "nothing physical is missing from either"


def test_the_blockwork_rows_separate_the_physical_state_from_the_commercial_one():
    for qid in ("Q-07-150", "Q-07-200"):
        x = by_id()[qid]
        assert x["COMMERCIAL_ITEM_MAPPING"] == "COMMERCIAL_ITEM_MAPPING_REVIEW"
        assert x["AMBIGUOUS_THICKNESS_ITEM_LENGTH_M"] > 0
        # the remaining physical uncertainty is bounded and stated, not open-ended
        assert x["MAXIMUM_REMAINING_MOVEMENT_M2"] > 0
        assert x["LOWER_BOUND_M2"] == round(x["MEASURED_NET_QUANTITY"] - x["MAXIMUM_REMAINING_MOVEMENT_M2"], 4)
        assert x["MAXIMUM_REMAINING_MOVEMENT_M2"] / x["MEASURED_NET_QUANTITY"] < 0.02


# ------------------------------------------------------------------ the sealed takeoff
def test_the_pre_pricing_takeoff_carries_no_rate_and_no_waste():
    t = reg("QORTUBA_FINAL_PRE_PRICING_TAKEOFF")
    assert t["RATES_SUPPLIED"] == 0 and t["WASTE_APPLIED"] is False
    assert t["COUNT"] == len([x for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]
                              if x["STATUS"] != "NOT_APPLICABLE"])
    for r in t["ROWS"]:
        assert r["QUANTITY_ID"] and r["TRADE"] and r["ITEM"] and r["UNIT"] and r["FORMULA"]
    assert t["DIGEST"] and len(t["DIGEST"]) == 16


def test_nothing_in_the_export_is_approved():
    e = reg("APPROVED_QUANTITIES")
    assert e["APPROVED_COUNT"] == 0
    assert all(r["APPROVAL_STATUS"] == "DRAFT" for r in e["ROWS"])


# ------------------------------------------------------------------ the contractor sheet
def test_the_contractor_comparison_never_moves_our_quantity():
    t = reg("QORTUBA_FINAL_PRE_PRICING_TAKEOFF")
    ours = by_id()
    for c in t["CONTRACTOR_COMPARISON"]:
        assert c["STATUS"] in ("CLOSE_AGREEMENT", "DIFFERENT_BASIS_OR_SCOPE", "NOT_COMPARABLE")
        assert c["LIKELY_BASIS_OR_SCOPE_DIFFERENCE"]
        if not c["OUR_QUANTITY_IDS"]:
            assert c["STATUS"] == "NOT_COMPARABLE" and c["OUR_QUANTITY"] is None
            continue
        # the figure beside his is exactly the one in our own takeoff, unrounded and unadjusted
        mine = round(sum(ours[q]["MEASURED_NET_QUANTITY"] for q in c["OUR_QUANTITY_IDS"]), 4)
        assert c["OUR_QUANTITY"] == mine
        assert c["DELTA"] == round(mine - c["CONTRACTOR_QUANTITY"], 4)


def test_the_skirting_agrees_with_the_contractor_within_one_percent():
    """Two independent measurements of the same path: his tape, our frozen registers."""
    t = {c["CONTRACTOR_ROW"]: c for c in reg("QORTUBA_FINAL_PRE_PRICING_TAKEOFF")["CONTRACTOR_COMPARISON"]}
    for cid in ("CC-02", "CC-03"):
        assert t[cid]["OUR_QUANTITY"] == 76.389 and t[cid]["CONTRACTOR_QUANTITY"] == 76.9
        assert abs(t[cid]["DELTA_PCT"]) < 1.0
        assert t[cid]["STATUS"] == "CLOSE_AGREEMENT"


def test_a_trim_item_we_never_measured_is_said_to_be_not_comparable():
    t = {c["CONTRACTOR_ROW"]: c for c in reg("QORTUBA_FINAL_PRE_PRICING_TAKEOFF")["CONTRACTOR_COMPARISON"]}
    for cid in ("CC-05", "CC-06"):
        assert t[cid]["STATUS"] == "NOT_COMPARABLE"
        assert t[cid]["OUR_QUANTITY"] is None, "no length is invented to match a contractor's sheet"
