"""OWNER INPUTS V2: the rules that keep a question answerable and a trade honest.

Two of these matter more than the arithmetic they govern.  A question an owner cannot answer is not a question, so no
row put to the owner may carry an internal identifier where the room name belongs.  And a PVC door is not an aluminium
item however similar the area calculation looks, so the schedules are separated by material and not by convenience.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.boq import opening_source_search as OS, owner_questions as OQ

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"


def reg(name, folder=OUT):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


def by_id():
    return {x["QUANTITY_ID"]: x for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]}


def rules():
    return reg("URBAN_OWNER_RULES_V1")


# ------------------------------------------------------------------ §1 no default window height
def test_there_is_no_default_window_height_anywhere():
    us = {x["TITLE"] for x in rules()["URBAN_STANDARDS"]}
    assert "THERE_IS_NO_DEFAULT_WINDOW_HEIGHT" in us
    for r in reg("QORTUBA_OPENING_REGISTER_COMPLETED")["ROWS"]:
        if r["TYPE"] in ("WINDOW", "SLIDING_DOOR") and r["HEIGHT_M"] is not None:
            raise AssertionError(f"{r['OPENING_ID']} was given a window height")
    # the aluminium schedule shows an unanswered height as a question, never as a number
    alu = by_id()["Q-15"]
    assert "height?" in alu["FORMULA"] and alu["MEASURED_NET_QUANTITY"] is None
    for r in alu["SCHEDULE"]:
        assert r["HEIGHT_M"] is None and r["AREA_M2"] is None


def test_a_window_without_a_height_is_owner_input_required_not_source_required():
    assert by_id()["Q-15"]["STATUS"] == "OWNER_INPUT_REQUIRED"
    for r in reg("QORTUBA_OPENING_REGISTER_COMPLETED")["ROWS"]:
        if r["TYPE"] == "WINDOW":
            assert r["STATUS"] == "OWNER_INPUT_REQUIRED", r["OPENING_ID"]


# ------------------------------------------------------------------ §1/§8/§9 how the owner is asked
def test_no_question_put_to_the_owner_carries_an_opaque_id():
    oq = reg("QORTUBA_OWNER_QUESTIONS")
    assert oq["AUDIT_COLUMNS"] == ["AUDIT_OPENING_ID"]
    for q in oq["ROWS"]:
        visible = " ".join(str(q[c]) for c in oq["TABLE_COLUMNS"]) + " " + str(q["LOCATION"])
        assert "OS-" not in visible and "BE-" not in visible, q["#"]
        assert q["AUDIT_OPENING_ID"], "the id is kept, in the audit column"


def test_every_question_names_a_room_an_opening_and_a_width():
    for q in reg("QORTUBA_OWNER_QUESTIONS")["ROWS"]:
        assert q["ROOM"] and q["OPENING"] and q["QUESTION"]
        # a pricing question is about a unit, not a dimension, so it is the one row with no width to give
        if q["INPUT_KIND"] == "QUANTITY_MEASUREMENT_INPUT":
            assert q["WIDTH_M"] > 0, q["#"]
        else:
            assert q["ASKS_FOR"] in ("PRICING_BASIS", "TRADE")
        assert q["LOCATION"] and len(q["LOCATION"]) > 10
        assert q["WHY_IT_MATTERS"]


def test_the_questions_are_numbered_and_the_plan_is_numbered_the_same_way():
    oq = reg("QORTUBA_OWNER_QUESTIONS")
    nums = [q["#"] for q in oq["ROWS"]]
    # numbers are issued once and never reused, so an answered question leaves a gap rather than renumbering the rest
    assert nums == sorted(nums) and len(set(nums)) == len(nums)
    assert set(nums) <= set(OQ.ISSUED_NUMBERS.values())
    assert oq["RETIRED_NUMBERS"] == [8, 9], "the two answered passages keep their numbers out of circulation"
    assert Path(oq["MARKED_PLAN"]).exists()
    assert OQ.PLAN.stat().st_size > 5000, "the marked plan is drawn, not a stub"


def test_each_window_is_asked_on_its_own_row():
    oq = reg("QORTUBA_OWNER_QUESTIONS")
    wins = [q for q in oq["ROWS"] if q["ASKS_FOR"] == "HEIGHT"]
    assert len(wins) == 6 and len({q["AUDIT_OPENING_ID"] for q in wins}) == 6
    assert oq["WINDOWS_ARE_NOT_GROUPED"]
    assert oq["NO_HEIGHT_IS_ASSUMED_FOR_ANY_OF_THEM"] is True


def test_an_unresolved_gap_is_asked_in_words_not_as_a_hash():
    oq = reg("QORTUBA_OWNER_QUESTIONS")
    kinds = [q for q in oq["ROWS"] if q["ASKS_FOR"] == "TYPE"]
    # five gaps were asked; the owner has answered two of them, so three type questions remain
    assert len(kinds) == 3
    for q in kinds:
        assert "door, an open passage, a window" in q["QUESTION"]
        assert "OS-" not in q["LOCATION"]
    # and nothing the owner has answered is asked again, in any form
    assert not [q for q in oq["ROWS"] if q["ASKS_FOR"] == "PASSAGE_HEIGHT"]
    asked = {q["AUDIT_OPENING_ID"] for q in oq["ROWS"]}
    assert not (asked & set(OS.OWNER_SUPPLIED_PASSAGE_SUBTYPES))


# ------------------------------------------------------------------ §2 the glazed opening
def test_the_hall_pantry_opening_is_2750_by_2200():
    r = [x for x in reg("QORTUBA_OPENING_REGISTER_COMPLETED")["ROWS"]
         if x["OPENING_ID"] == "OS-b5a0fbb335d4"][0]
    assert r["WIDTH_M"] == 2.750 and r["HEIGHT_M"] == 2.200
    assert "OWNER" in r["HEIGHT_SOURCE"] and r["STATUS"] == "USABLE"
    rooms = {x["ROOM"]: x for x in reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]}
    for room in ("HALL / whgm", "PAINTRY"):
        ids = [o["OPENING_ID"] for o in rooms[room]["OPENINGS_DEDUCTED"]]
        assert "OS-b5a0fbb335d4" in ids, room
    assert abs(by_id()["Q-17"]["MEASURED_NET_QUANTITY"] - 6.05) < 1e-9


def test_both_sides_of_a_shared_opening_lose_the_area():
    rooms = {x["ROOM"]: x for x in reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]}
    assert abs(rooms["PAINTRY"]["OPENING_DEDUCTION_M2"] - 6.05) < 1e-9
    # the Hall also loses the 3.600 m2 full-height passage to the Lobby, so its deduction is 14.025 + 3.600
    assert abs(rooms["HALL / whgm"]["OPENING_DEDUCTION_M2"] - 17.625) < 1e-9


# ------------------------------------------------------------------ §3 PVC is not aluminium
def test_interior_doors_are_pvc_and_never_appear_under_aluminium():
    q = by_id()
    assert q["Q-16"]["BOQ_ITEM"] == "PVC_INTERNAL_DOORS"
    assert q["Q-15"]["BOQ_ITEM"] == "ALUMINIUM_EXTERNAL_WINDOWS"
    pvc = {r["OPENING_ID"] for r in q["Q-16"]["SCHEDULE"]}
    alu = {r["OPENING_ID"] for r in q["Q-15"]["SCHEDULE"]}
    assert pvc and alu and not (pvc & alu)
    for r in q["Q-15"]["SCHEDULE"]:
        assert r["MATERIAL_TRADE"] == "ALUMINIUM" and r["TYPE"] in ("WINDOW", "SLIDING_DOOR")
    assert q["Q-16"]["TRADE"] != q["Q-15"]["TRADE"]


def test_an_internal_glazed_opening_is_neither_pvc_nor_aluminium():
    q = by_id()["Q-17"]
    assert q["BOQ_ITEM"] == "INTERNAL_GLAZED_OPENING"
    assert all(r["MATERIAL_TRADE"] == "INTERNAL_GLAZED_OPENING" for r in q["SCHEDULE"])


def test_every_opening_schedule_carries_count_width_height_and_area():
    q = by_id()
    for qid in ("Q-15", "Q-16", "Q-17"):
        x = q[qid]
        assert x["COUNT"] == len(x["SCHEDULE"])
        for r in x["SCHEDULE"]:
            assert r["COUNT"] == 1 and r["WIDTH_M"] > 0
            assert ("HEIGHT_M" in r) and ("AREA_M2" in r)


# ------------------------------------------------------------------ §4 waterproofing
def test_the_pantry_is_waterproofed_by_area_and_gross_perimeter():
    q = by_id()
    assert q["Q-03P"]["MEASURED_NET_QUANTITY"] == 11.685 and q["Q-03P"]["UNIT"] == "M2"
    assert q["Q-04P"]["MEASURED_NET_QUANTITY"] == 11.150 and q["Q-04P"]["UNIT"] == "LM"
    sk = {x["ROOM"]: x for x in reg("QORTUBA_QS01_SKIRTING_TAKEOFF", QS)["ROWS"]}
    assert q["Q-04P"]["MEASURED_NET_QUANTITY"] == sk["PAINTRY"]["GROSS_WALL_LINE_PERIMETER_LM"]
    rooms = {x["ROOM"]: x for x in reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]}
    assert rooms["PAINTRY"]["SKIRTING_LM"] == 0.0
    assert q["Q-04P"]["MEASURED_NET_QUANTITY"] != rooms["PAINTRY"]["SKIRTING_LM"], "not the skirting path"
    assert abs(q["Q-04PR"]["MEASURED_NET_QUANTITY"] - round(11.150 * 0.15, 4)) < 1e-9


def test_the_waterproofing_room_types_are_enumerated_in_the_standard():
    us = [x for x in rules()["URBAN_STANDARDS"] if x["TITLE"] == "WATERPROOFING_ROOM_TYPES_ARE_ENUMERATED"][0]
    for room in ("bathroom", "kitchen", "pantry", "iron room", "washing room", "laundry"):
        assert room in us["STATEMENT"].lower(), room
    assert "doorways not" in us["STATEMENT"].lower()


# ------------------------------------------------------------------ §6 porcelain
def test_the_porcelain_area_was_re_totalled_and_not_inherited():
    x = by_id()["Q-13"]
    assert x["BOQ_ITEM"] == "PORCELAIN_FLOOR_DRY_ROOMS" and x["STATUS"] == "FINAL_QUANTITY_AVAILABLE"
    assert x["SUBTOTAL_VERIFIED_AGAINST_THE_FROZEN_REGISTER"] is True
    floors = reg("QORTUBA_QS01_FLOOR_CALCULATIONS", QS)["ROWS"]
    dry = [f for f in floors if f["ROOM"].split(" /")[0] not in ("BATH", "PAINTRY")]
    assert abs(x["MEASURED_NET_QUANTITY"] - round(sum(f["METHOD_A_CAD_POLYGON_AREA_M2"] for f in dry), 4)) < 1e-9
    assert len(x["ROOM_BREAKDOWN"]) == len(dry)
    assert x["PANTRY_EXCLUDED_M2"] == 11.685


def test_the_three_floor_items_still_sum_to_the_apartment():
    q = by_id()
    s = reg("QORTUBA_QS01_SUMMARY_TOTALS", QS)
    total = sum(q[k]["MEASURED_NET_QUANTITY"] for k in ("Q-11", "Q-12", "Q-13"))
    assert abs(total - s["C_TOTAL_INTERNAL_APARTMENT_FLOOR_AREA_M2"]["VALUE"]) < 1e-6


# ------------------------------------------------------------------ §7 ceiling
def test_the_ceiling_is_one_area_line_and_carries_no_decor_length():
    x = by_id()["Q-14"]
    assert x["BOQ_ITEM"] == "CEILING_BY_AREA" and x["UNIT"] == "M2"
    assert x["MEASURED_NET_QUANTITY"] == 138.510
    assert x["CEILING_PERIMETER_NOT_A_PAYABLE_ITEM_LM"] == 153.125
    for banned in ("cornice", "cove lighting", "bulkhead", "shadow gap", "decorative perimeter"):
        assert banned in x["DECOR_LENGTHS_NOT_CARRIED"]
    for y in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]:
        if y["UNIT"] == "LM":
            assert "cornice" not in y["BOQ_ITEM"].lower(), y["QUANTITY_ID"]


def test_no_cornice_run_survives_in_the_bill():
    from research.qs_wall_treatment_01.pa08.qortuba.boq import workbook_boq as WB
    for cm in ("CM-CL1", "CM-CL2", "CM-CL3"):
        assert cm in WB.CLOSED_BY_RULE, cm
        assert "US-15" in WB.CLOSED_BY_RULE[cm][0]


# ------------------------------------------------------------------ nothing moved
def test_the_new_rules_are_stored_at_the_right_levels():
    R = rules()
    titles = {x["TITLE"] for x in R["URBAN_STANDARDS"]}
    assert {"THERE_IS_NO_DEFAULT_WINDOW_HEIGHT", "ASK_IN_WORDS_A_PERSON_CAN_ACT_ON",
            "INTERIOR_DOORS_ARE_PVC_EXTERIOR_OPENINGS_ARE_ALUMINIUM",
            "WATERPROOFING_ROOM_TYPES_ARE_ENUMERATED",
            "A_CEILING_IS_PRICED_BY_AREA_UNTIL_A_CEILING_DRAWING_EXISTS"} <= titles
    params = {x["PARAMETER"]: x for x in R["QORTUBA_PROJECT_RULES"]}
    assert params["QORTUBA_HALL_PANTRY_GLAZED_OPENING_HEIGHT"]["VALUE"] == 2.200
    assert params["QORTUBA_DRY_FLOOR_FINISH"]["VALUE"] == "PORCELAIN"
    assert params["QORTUBA_INTERIOR_DOORS"]["VALUE"] == "PVC"
    for x in R["QORTUBA_PROJECT_RULES"]:
        assert x["APPLIES_TO_OTHER_PROJECTS"] is False


def test_no_geometry_was_touched_by_owner_inputs_v2():
    fz = reg("FREEZE_URBAN_OWNER_RULES_V1")
    assert fz["QORTUBA_GEOMETRY_CHANGED"] == "NONE" and fz["NEW_TAKEOFF_PHASES_CREATED"] == 0
    assert reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["GEOMETRY_STAGES_RERUN"] == 0
    ident = reg("QORTUBA_WALL_OBJECT_IDENTITY")
    assert ident["BLOCKWORK_CONFIRMED_LENGTH_M"] == 128.38
    rooms = reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]
    sk = {x["ROOM_ID"]: x for x in reg("QORTUBA_QS01_SKIRTING_TAKEOFF", QS)["ROWS"]}
    for r in rooms:
        assert r["GROSS_WALL_LINE_LM"] == sk[r["ROOM_ID"]]["GROSS_WALL_LINE_PERIMETER_LM"]


def test_the_answered_questions_are_closed_and_the_open_ones_are_new():
    ql = reg("QORTUBA_QUESTION_LEDGER")
    closed = {c["DECISION_ID"] for c in ql["CLOSED"]}
    assert {"O-03", "O-04", "V2-01", "V2-02", "V2-03"} <= closed
    open_ids = {x["ID"] for x in ql["STILL_OPEN"]}
    assert not (open_ids & closed)
    blob = " ".join(x["QUESTION"].lower() for x in ql["STILL_OPEN"])
    for answered in ("pantry takes waterproofing", "ceiling paint scope", "dry floor finish"):
        assert answered not in blob, answered
