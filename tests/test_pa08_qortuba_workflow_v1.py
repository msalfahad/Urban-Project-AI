"""The workflow, not the engine.

Three claims are tested here, and none of them is about geometry.  A question number is a name the owner holds, so it
is issued once and never reused.  An opening belongs to the two rooms it joins, not to every room its host band runs
past, so a dry-room gap does not hold up bathroom ceramic.  And a quantity that leaves the workpaper carries its whole
provenance with it - and leaves as DRAFT, because approval is the owner's act and not the engine's.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.boq import (approved_quantities as AQ, opening_source_search as OS,
                                                            owner_questions as OQ)

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
CERAMIC_ROWS = ("Q-05", "Q-06", "Q-10")
DRY_GAPS = ("OS-77f8fed2eb15", "OS-85cb2192ebc0")


def reg(name):
    return json.loads((OUT / f"{name}.json").read_text("utf-8"))


def by_id():
    return {x["QUANTITY_ID"]: x for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]}


# ------------------------------------------------------------------ §D the whole vocabulary
def test_the_case_vocabulary_is_eight_cases_and_no_more():
    assert set(OS.OPENING_CASES) == {
        "DOOR", "WINDOW", "SLIDING_DOOR", "GLAZED_OPENING",
        "OPEN_PASSAGE_FULL_HEIGHT", "OPEN_PASSAGE_WITH_HEAD",
        "FULL_HEIGHT_OPENING_FOR_MEASUREMENT", "NOT_AN_OPENING", "UNKNOWN"}
    r = reg("QORTUBA_OPENING_REGISTER_COMPLETED")
    assert set(r["BY_CASE"]) <= set(OS.OPENING_CASES)
    assert r["BY_CASE"]["OPEN_PASSAGE_FULL_HEIGHT"] == 1
    assert r["BY_CASE"]["OPEN_PASSAGE_WITH_HEAD"] == 1
    assert r["BY_CASE"]["FULL_HEIGHT_OPENING_FOR_MEASUREMENT"] == 3
    # every gap is now classified, so nothing is left UNKNOWN and no type question remains
    assert "UNKNOWN" not in r["BY_CASE"]
    assert not [q for q in reg("QORTUBA_OWNER_QUESTIONS")["ROWS"] if q["ASKS_FOR"] == "TYPE"]


# ------------------------------------------------------------------ §B attribution
def test_a_dry_room_gap_does_not_block_a_ceramic_quantity():
    q = by_id()
    for qid in CERAMIC_ROWS:
        named = {o.get("OPENING_ID") for o in q[qid]["RESIDUAL_OPENINGS"]}
        assert not (named & set(DRY_GAPS)), f"{qid} was blocked by an opening that is not in any ceramic face"


def test_an_opening_is_attributed_to_the_rooms_it_joins_not_to_the_band_s_whole_list():
    hum = {h["OPENING_ID"]: h for h in OS.human_register()}
    h = hum["OS-77f8fed2eb15"]
    band = {r["OPENING_ID"]: r for r in reg("QORTUBA_OPENING_REGISTER_COMPLETED")["ROWS"]}["OS-77f8fed2eb15"]
    # the host band runs past a bathroom and the pantry, and the opening joins neither of them
    assert {"BATH", "PAINTRY"} <= {x.strip() for x in band["ROOM"].split(",")}
    assert set(h["ROOMS_FOR_DEDUCTION"]) == {"HALL / whgm", "UNLABELLED_INTERNAL_SPACE"}
    rules = {r["PARAMETER"]: r for r in reg("URBAN_OWNER_RULES_V1")["QORTUBA_PROJECT_RULES"]}
    assert rules["QORTUBA_OPENING_ROOM_ATTRIBUTION"]["VALUE"] == "THE_TWO_ROOMS_IT_JOINS"


def test_the_pantry_window_still_blocks_the_pantry_because_it_really_is_there():
    """Removing false dependencies must not remove true ones."""
    q = by_id()
    for qid in ("Q-06", "Q-10"):
        named = {o.get("OPENING_ID") for o in q[qid]["RESIDUAL_OPENINGS"]}
        assert "BE-02" in named, f"{qid} genuinely waits on the pantry window height"


# ------------------------------------------------------------------ a number is a name
def test_a_question_number_is_issued_once_and_never_reused():
    oq = reg("QORTUBA_OWNER_QUESTIONS")
    live = {q["#"] for q in oq["ROWS"]}
    issued = set(OQ.ISSUED_NUMBERS.values())
    assert live <= issued
    assert oq["RETIRED_NUMBERS"] == sorted(issued - live)
    assert set(oq["RETIRED_NUMBERS"]) == {7, 8, 9, 10, 11}, "every answered opening keeps its number retired"
    # and the numbers that remain still name the same openings they always named
    by_n = {q["#"]: q["AUDIT_OPENING_ID"] for q in oq["ROWS"]}
    for oid, n in OQ.ISSUED_NUMBERS.items():
        if n in by_n:
            assert by_n[n] == oid, f"#{n} has changed what it points at"


# ------------------------------------------------------------------ §J and §L the handover shape
def test_every_exported_record_carries_the_whole_schema():
    e = reg("APPROVED_QUANTITIES")
    assert set(e["SCHEMA_FIELDS"]) == set(AQ.FIELDS)
    assert e["COUNT"] == len(reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"])
    for r in e["ROWS"]:
        for k in AQ.FIELDS:
            assert k in r, (r["SUBITEM"], k)
        assert r["PROJECT_ID"] and r["DRAWING_REVISION"] and r["FLOOR"] and r["TRADE"] and r["ITEM"]
        assert r["STATUS"] in e["STATUSES"]
        assert r["APPROVAL_STATUS"] in AQ.APPROVAL_STATES


def test_nothing_leaves_the_engine_approved():
    e = reg("APPROVED_QUANTITIES")
    assert e["APPROVED_COUNT"] == 0
    assert all(r["APPROVAL_STATUS"] == "DRAFT" for r in e["ROWS"])
    assert e["BY_APPROVAL"] == {"DRAFT": e["COUNT"]}


def test_only_a_final_row_carries_a_payable_quantity():
    for r in reg("APPROVED_QUANTITIES")["ROWS"]:
        if r["STATUS"] == "FINAL":
            assert r["FINAL_BOQ_QUANTITY"] is not None and r["FINAL_BOQ_QUANTITY"] == r["MEASURED_QUANTITY"]
        else:
            assert r["FINAL_BOQ_QUANTITY"] is None, r["SUBITEM"]


# ------------------------------------------------------------------ FINISHING MODE §1 and §2
def test_the_door_height_is_a_confirmed_parameter_not_a_placeholder():
    rules = {r["PARAMETER"]: r for r in reg("URBAN_OWNER_RULES_V1")["QORTUBA_PROJECT_RULES"]}
    p = rules["OWNER_CONFIRMED_INTERNAL_DOOR_HEIGHT"]
    assert p["VALUE"] == 2.20 and p["UNIT"] == "M"
    assert p["RULE_LEVEL"] == "QORTUBA_PROJECT_RULE", "a confirmed parameter is not a temporary default"
    # the generic placeholder survives for other projects, and says it is superseded here
    td = {r["RULE_ID"]: r for r in reg("URBAN_OWNER_RULES_V1")["TEMPORARY_DEFAULTS"]}
    assert "SUPERSEDED by QP-21" in td["TD-02"]["WHY"]


def test_no_quantity_is_held_partial_merely_for_using_the_confirmed_door_height():
    for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]:
        assert x["USES_TEMPORARY_DEFAULT"] is False
        assert x["TEMPORARY_DEFAULT_WARNING"] is None
        if x["STATUS"] == "PARTIALLY_CALCULATED":
            assert x["RESIDUAL_OPENINGS"], f"{x['QUANTITY_ID']} is partial with nothing outstanding"
        if x["USES_OWNER_CONFIRMED_PARAMETER"]:
            assert "QP-21" in x["OWNER_CONFIRMED_PARAMETER_NOTE"], x["QUANTITY_ID"]


def test_bathroom_wall_ceramic_is_final():
    x = by_id()["Q-05"]
    assert x["STATUS"] == "FINAL_QUANTITY_AVAILABLE"
    assert x["MEASURED_NET_QUANTITY"] == 84.9
    assert x["RESIDUAL_OPENINGS"] == []
    assert "QP-21" in x["RULE_ID"] and "QP-01" in x["RULE_ID"]
    assert "OWNER_CONFIRMED_PROJECT_PARAMETER" in x["PARAMETER_SOURCE"]


def test_a_measured_quantity_is_not_a_pricing_basis():
    """§3: the PVC physical data is established; what a door costs per unit of anything is a separate question."""
    x = by_id()["Q-16"]
    assert x["COUNT"] == 7
    assert x["PHYSICAL_OPENING_AREA_M2"]["STATE"] == "ESTABLISHED"
    assert abs(x["PHYSICAL_OPENING_AREA_M2"]["VALUE"] - 16.665) < 1e-9
    assert x["FINAL_PRICING_QUANTITY"]["VALUE"] is None
    assert x["FINAL_PRICING_QUANTITY"]["STATE"] == "PROJECT_RULE_REQUIRED"
    assert x["STATUS"] == "PROJECT_RULE_REQUIRED", "a settled measurement does not settle a pricing unit"


def test_the_bedroom_lobby_door_attribution_stays_corrected():
    """§4: the 1.125 m door joins two dry rooms, whatever else its host band runs past."""
    hum = {h["OPENING_ID"]: h for h in OS.human_register()}
    d = [h for h in hum.values() if h["TYPE"] == "DOOR" and abs(h["WIDTH_M"] - 1.125) < 1e-9][0]
    assert set(d["ROOMS_FOR_DEDUCTION"]) == {"BED.ROOM", "UNLABELLED_INTERNAL_SPACE"}
    assert "BATH" not in d["ROOMS_FOR_DEDUCTION"]
    q = by_id()
    assert q["Q-08"]["MEASURED_NET_QUANTITY"] == 283.0025 == q["Q-09"]["MEASURED_NET_QUANTITY"]


# ------------------------------------------------------------------ FINISHING MODE §5 the final batch
def test_the_final_batch_asks_for_everything_still_needed_and_nothing_else():
    oq = reg("QORTUBA_OWNER_QUESTIONS")
    by_kind = {}
    for q in oq["ROWS"]:
        by_kind.setdefault(q["ASKS_FOR"], []).append(q["#"])
    assert sorted(by_kind["HEIGHT"]) == [1, 2, 3, 4, 5, 6], "the six window heights"
    assert "TYPE" not in by_kind, "every gap is closed; no architectural type is still being asked"
    assert by_kind["TRADE"] == [12], "the internal glazing trade"
    assert by_kind["PRICING_BASIS"] == [13], "the PVC pricing basis"
    assert len(oq["ROWS"]) == 8


def test_a_pricing_question_is_marked_as_one_and_holds_up_no_measurement():
    oq = reg("QORTUBA_OWNER_QUESTIONS")
    pricing = [q for q in oq["ROWS"] if q["INPUT_KIND"] == "PRICING_INPUT"]
    assert len(pricing) == 1 and pricing[0]["ASKS_FOR"] == "PRICING_BASIS"
    assert oq["PRICING_INPUTS"] == 1
    assert oq["TRADE_CLASSIFICATION_INPUTS"] == 1
    assert oq["QUANTITY_MEASUREMENT_INPUTS"] == 6
    assert "NOT a measurement question" in pricing[0]["WHY_IT_MATTERS"]
    # and nothing in the takeoff names it as an outstanding opening
    waiting = {o.get("OPENING_ID") for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]
               for o in x["RESIDUAL_OPENINGS"]}
    assert "Q-16" not in waiting


def test_only_openings_that_still_block_a_quantity_are_asked_about():
    """Every measurement question must be one some row is actually waiting on, and every such row must be asked."""
    oq = reg("QORTUBA_OWNER_QUESTIONS")
    asked = {q["AUDIT_OPENING_ID"] for q in oq["ROWS"] if q["INPUT_KIND"] == "QUANTITY_MEASUREMENT_INPUT"}
    waiting = {o.get("OPENING_ID") for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]
               for o in x["RESIDUAL_OPENINGS"]}
    assert asked == {w for w in waiting if w}, "a question nothing waits on is not worth the owner's time"


# ------------------------------------------------------------------ FINAL COMPLETION: the end-gap correction
def test_a_gap_beyond_the_band_is_not_deducted_from_it_twice():
    """A band's length stops at its end jambs, so an end gap is already excluded from the measured material."""
    reg_c = reg("QORTUBA_OPENING_REGISTER_COMPLETED")
    ends = [r for r in reg_c["ROWS"] if not r["INTERIOR_TO_HOST_BAND"]]
    assert ends, "Qortuba has end gaps; if this empties, the detection broke"
    for r in ends:
        lo, hi = r["GAP_MM"]
        e0, e1 = r["BAND_EXTENT_MM"]
        assert hi <= e0 + 1 or lo >= e1 - 1, r["OPENING_ID"]
        assert "not deducted a second time" in r["WHY_NOT_DEDUCTED_FROM_THE_BAND"]


def test_no_wall_deducts_more_material_than_it_contains():
    for w in reg("QORTUBA_BLOCKWORK_RECALC")["ROWS"]:
        if w["GROSS_AREA_M2"] is None:
            continue
        assert w["OPENING_DEDUCTION_M2"] <= w["GROSS_AREA_M2"] + 1e-9, w["WALL_ID"]
        if w["NET_AREA_M2"] is not None:
            assert w["NET_AREA_M2"] >= 0, f"{w['WALL_ID']} has a negative area"


def test_the_two_bedroom_gaps_interrupt_no_measured_apartment_path():
    """Their host band belongs to two unlabelled spaces, so no room finish run passes along it."""
    hum = {h["OPENING_ID"]: h for h in OS.human_register()}
    for sid in ("OS-3144b5fbb149", "OS-045efd7810a7"):
        assert hum[sid]["ROOM_IDS_FOR_DEDUCTION"] == []
    rooms = reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]
    charged = {o["OPENING_ID"] for r in rooms for o in r["OPENINGS_DEDUCTED"]}
    charged |= {p["OPENING_ID"] for r in rooms for p in r["OPEN_PASSAGES_DEDUCTED"]}
    assert not (charged & {"OS-3144b5fbb149", "OS-045efd7810a7"})
    # but they ARE holes in a confirmed masonry band, and that band's own arithmetic accounts for them
    w = [x for x in reg("QORTUBA_BLOCKWORK_RECALC")["ROWS"] if x["WALL_ID"] == "W-62147653"][0]
    assert {g["OPENING_ID"] for g in w["END_GAPS_NOT_DEDUCTED"]} == {"OS-3144b5fbb149", "OS-045efd7810a7"}


def test_a_reveal_follows_a_deduction_and_never_leads_it():
    q = by_id()["Q-08"]
    assert "7 dry-to-dry opening reveals" in q["FORMULA"]
    # the two bedroom gaps deduct from no room, so they add no reveal either
    assert q["MEASURED_NET_QUANTITY"] == 283.0025
