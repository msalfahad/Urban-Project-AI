"""An opening with nothing in it.

A gap in a wall with no door leaf in it is still a gap: it interrupts the skirting, the profile and every wall-area
trade exactly as a doorway does.  What it does not do is cost anything to buy, so it must never reach a door or window
schedule.  And it has no assumed height at all - a passage is either open to the ceiling or it has a head above it, and
only the owner knows which, so the door default is barred from it while the width deduction proceeds without waiting.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.boq import opening_source_search as OS

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
PASSAGES = ("OS-77f8fed2eb15", "OS-85cb2192ebc0")


def reg(name):
    return json.loads((OUT / f"{name}.json").read_text("utf-8"))


def by_id():
    return {x["QUANTITY_ID"]: x for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]}


def opens():
    return {r["OPENING_ID"]: r for r in reg("QORTUBA_OPENING_REGISTER_COMPLETED")["ROWS"]}


# ------------------------------------------------------------------ the type exists and is used
def test_open_passage_is_a_permanent_opening_type():
    assert "OPEN_PASSAGE" in OS.OPENING_TYPES
    assert set(OS.OPEN_PASSAGE_SUBTYPES) == {"OPEN_PASSAGE_FULL_HEIGHT", "OPEN_PASSAGE_WITH_HEAD"}
    us = {x["TITLE"] for x in reg("URBAN_OWNER_RULES_V1")["URBAN_STANDARDS"]}
    assert "AN_OPEN_PASSAGE_IS_AN_OPENING_WITH_NOTHING_IN_IT" in us
    assert "AN_OPEN_PASSAGE_HAS_NO_ASSUMED_HEIGHT" in us


def test_both_confirmed_gaps_are_open_passages_of_1200_mm():
    o = opens()
    for sid in PASSAGES:
        r = o[sid]
        assert r["TYPE"] == "OPEN_PASSAGE"
        assert r["WIDTH_M"] == 1.2
        assert r["TYPE_SOURCE"] and "owner" in r["TYPE_SOURCE"]


# ------------------------------------------------------------------ no assumed height
def test_a_passage_height_is_an_owner_input_and_never_the_door_default():
    o = opens()
    full, head = o["OS-77f8fed2eb15"], o["OS-85cb2192ebc0"]
    assert full["OPEN_PASSAGE_SUBTYPE"] == "OPEN_PASSAGE_FULL_HEIGHT"
    assert full["HEIGHT_M"] == 3.0 == OS.QORTUBA_WALL_HEIGHT_M, "full height IS the wall height"
    assert full["REVEAL_SIDES"] == ["LEFT", "RIGHT"], "there is no head, so there is no top to finish"
    assert head["OPEN_PASSAGE_SUBTYPE"] == "OPEN_PASSAGE_WITH_HEAD"
    assert head["HEIGHT_M"] == 2.2
    assert head["REVEAL_SIDES"] == ["LEFT", "RIGHT", "TOP"]
    # 2.200 m also happens to be TD-02.  A coincidence of figures is not a provenance: this one is an owner input,
    # and if TD-02 ever moves, this does not.
    assert "not the generic TD-02" in head["HEIGHT_SOURCE"]
    rules = {r["PARAMETER"]: r for r in reg("URBAN_OWNER_RULES_V1")["QORTUBA_PROJECT_RULES"]}
    assert rules["QORTUBA_OPEN_PASSAGE_WITH_HEAD_HEIGHT"]["VALUE"] == 2.2
    for sid in PASSAGES:
        assert o[sid]["HEIGHT_STATUS"] == "ANSWERED_BY_OWNER"
        assert o[sid]["STATUS"] == "USABLE"


def test_each_passage_area_is_deducted_from_both_rooms_it_joins():
    rooms = {r["ROOM_NAME"]: r for r in reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]}
    got = {}
    for r in reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]:
        for o in r["OPENINGS_DEDUCTED"]:
            if o["OPENING_ID"] in PASSAGES:
                got.setdefault(o["OPENING_ID"], []).append((r["ROOM_NAME"], o["AREA_M2"]))
    assert set(got) == set(PASSAGES)
    assert sorted(got["OS-77f8fed2eb15"]) == [("HALL", 3.6), ("UNLABELLED_INTERNAL_SPACE", 3.6)]
    assert sorted(got["OS-85cb2192ebc0"]) == [("DRESS", 2.64), ("M.B.ROOM", 2.64)]
    # and nothing still waits on them
    waiting = {o.get("OPENING_ID") for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]
               for o in x["RESIDUAL_OPENINGS"]}
    assert not (set(PASSAGES) & waiting)


# ------------------------------------------------------------------ never procured
def test_a_passage_never_reaches_a_door_or_window_schedule():
    o = opens()
    for sid in PASSAGES:
        assert o[sid]["TYPE"] != "DOOR"
    q = by_id()
    for qid in ("Q-15", "Q-16", "Q-17"):
        ids = {r["OPENING_ID"] for r in q[qid]["SCHEDULE"]}
        assert not (ids & set(PASSAGES)), f"{qid} is a procurement schedule and must not carry an open passage"
    assert q["Q-16"]["COUNT"] == 7, "the PVC door count is unchanged by the passages"
    assert abs(q["Q-16"]["PHYSICAL_OPENING_AREA_M2"]["VALUE"] - 16.665) < 1e-9
    hum = {h["OPENING_ID"]: h for h in OS.human_register()}
    for sid in PASSAGES:
        assert hum[sid]["MATERIAL_TRADE"] == "OPEN_PASSAGE_NO_PROCUREMENT"


# ------------------------------------------------------------------ the linear deduction
def test_each_passage_leaves_the_path_of_both_rooms_it_joins():
    PASSAGES_ONLY = PASSAGES
    rooms = {r["ROOM_ID"]: r for r in reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]}
    got = {}
    for r in rooms.values():
        for p in r["OPEN_PASSAGES_DEDUCTED"]:
            got.setdefault(p["OPENING_ID"], []).append((r["ROOM_NAME"], p["WIDTH_M"]))
    assert set(PASSAGES_ONLY) <= set(got)
    for sid in PASSAGES_ONLY:
        hits = got[sid]
        assert len(hits) == 2, f"{sid} must interrupt the path of both rooms it joins"
        assert all(w == 1.2 for _, w in hits)
    assert {n for sid in PASSAGES_ONLY for n, _ in got[sid]} == {
        "HALL", "UNLABELLED_INTERNAL_SPACE", "M.B.ROOM", "DRESS"}


def test_the_skirting_and_profile_total_moved_by_exactly_the_widths_that_interrupt_it():
    q = by_id()
    for qid in ("Q-01", "Q-02"):
        x = q[qid]
        # two passages at 1.200 m and the 2.700 m full-height opening, each leaving both room paths it joins;
        # the two 1.100 m bedroom gaps interrupt no measured apartment path and take nothing off
        assert x["MEASURED_NET_QUANTITY"] == 76.389
        assert x["VALUE_BEFORE_THE_OPEN_PASSAGE_CORRECTION"] == 86.589
        assert x["OPEN_PASSAGE_DEDUCTION_LM"] == 10.2
        assert round(86.589 - 10.2, 3) == x["MEASURED_NET_QUANTITY"]
        assert len(x["OPEN_PASSAGES_DEDUCTED"]) == 6
        assert round(sum(d["WIDTH_M"] for d in x["OPEN_PASSAGES_DEDUCTED"]), 3) == 10.2
        assert x["STATUS"] == "FINAL_QUANTITY_AVAILABLE", "a linear deduction never waits for a height"
        assert x["RESIDUAL_OPENINGS"] == []


def test_the_project_rules_record_the_correction_and_the_open_question():
    rules = {r["PARAMETER"]: r for r in reg("URBAN_OWNER_RULES_V1")["QORTUBA_PROJECT_RULES"]}
    assert rules["QORTUBA_OPEN_PASSAGES"]["VALUE"] == "2 x 1.200 m"
    assert rules["QORTUBA_OPEN_PASSAGE_VERTICAL_CONDITION"]["VALUE"] == "ANSWERED"
    ledger = reg("QORTUBA_QUESTION_LEDGER")
    closed = {x["DECISION_ID"] for x in ledger["CLOSED"]}
    assert {"OP-01", "OP-02", "OP-03", "OP-04"} <= closed, "an answer the owner has given is never asked again"
    assert "O-11" not in {x["ID"] for x in ledger["STILL_OPEN"]}


def test_the_three_other_gaps_are_closed_by_the_owner_for_measurement():
    """They were UNRESOLVED; the owner closed them without naming an architectural type, and none was inferred."""
    o = opens()
    for sid in ("OS-b1e147c89482", "OS-3144b5fbb149", "OS-045efd7810a7"):
        r = o[sid]
        assert r["TYPE"] == "FULL_HEIGHT_OPENING_FOR_MEASUREMENT"
        assert r["HEIGHT_M"] == 3.0
        assert r["REVEAL_SIDES"] == ["LEFT", "RIGHT"], "full height, so there is no head to finish"
        assert r["STATUS"] == "USABLE"
    hum = {h["OPENING_ID"]: h for h in OS.human_register()}
    for sid in ("OS-b1e147c89482", "OS-3144b5fbb149", "OS-045efd7810a7"):
        assert hum[sid]["MATERIAL_TRADE"] == "OPEN_PASSAGE_NO_PROCUREMENT"
