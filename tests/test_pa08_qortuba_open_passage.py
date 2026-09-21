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
def test_a_passage_takes_no_height_from_the_door_default():
    o = opens()
    for sid in PASSAGES:
        r = o[sid]
        assert r["HEIGHT_M"] is None, "TD-02 is barred from an open passage"
        assert r["HEIGHT_SOURCE"] is None
        assert r["HEIGHT_STATUS"] == "OWNER_INPUT_REQUIRED"
        assert r["OPEN_PASSAGE_SUBTYPE"] is None
        assert r["STATUS"] == "PARTIAL_HEIGHT_REQUIRED"


def test_no_wall_area_is_deducted_for_a_passage_before_its_height_arrives():
    """The width deduction is taken; the AREA deduction is not, and the rows that wait say which openings they wait on."""
    rooms = {r["ROOM_ID"]: r for r in reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]}
    for r in rooms.values():
        for o in r["OPENINGS_DEDUCTED"]:
            assert o["OPENING_ID"] not in PASSAGES, "no area may be taken for a passage with no height"
    waiting = {o.get("OPENING_ID") for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]
               for o in x["RESIDUAL_OPENINGS"]}
    assert set(PASSAGES) <= waiting, "the wall-area rows must say they are waiting on these two"


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
    rooms = {r["ROOM_ID"]: r for r in reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]}
    got = {}
    for r in rooms.values():
        for p in r["OPEN_PASSAGES_DEDUCTED"]:
            got.setdefault(p["OPENING_ID"], []).append((r["ROOM_NAME"], p["WIDTH_M"]))
    assert set(got) == set(PASSAGES)
    for sid, hits in got.items():
        assert len(hits) == 2, f"{sid} must interrupt the path of both rooms it joins"
        assert all(w == 1.2 for _, w in hits)
    assert {n for hits in got.values() for n, _ in hits} == {
        "HALL", "UNLABELLED_INTERNAL_SPACE", "M.B.ROOM", "DRESS"}


def test_the_skirting_and_profile_total_moved_by_exactly_the_four_widths():
    q = by_id()
    for qid in ("Q-01", "Q-02"):
        x = q[qid]
        assert x["MEASURED_NET_QUANTITY"] == 81.789
        assert x["VALUE_BEFORE_THE_OPEN_PASSAGE_CORRECTION"] == 86.589
        assert x["OPEN_PASSAGE_DEDUCTION_LM"] == 4.8
        assert round(86.589 - 4.8, 3) == x["MEASURED_NET_QUANTITY"]
        assert len(x["OPEN_PASSAGES_DEDUCTED"]) == 4
        for d in x["OPEN_PASSAGES_DEDUCTED"]:
            assert round(d["PATH_BEFORE_LM"] - d["PATH_AFTER_LM"], 3) == 1.2, d["ROOM"]
        assert x["STATUS"] == "FINAL_QUANTITY_AVAILABLE", "a linear deduction never waits for a height"
        assert x["RESIDUAL_OPENINGS"] == []


def test_the_project_rules_record_the_correction_and_the_open_question():
    rules = {r["PARAMETER"]: r for r in reg("URBAN_OWNER_RULES_V1")["QORTUBA_PROJECT_RULES"]}
    assert rules["QORTUBA_OPEN_PASSAGES"]["VALUE"] == "2 x 1.200 m"
    assert rules["QORTUBA_OPEN_PASSAGE_VERTICAL_CONDITION"]["VALUE"] is None
    ledger = reg("QORTUBA_QUESTION_LEDGER")
    closed = {x["DECISION_ID"] for x in ledger["CLOSED"]}
    assert {"OP-01", "OP-02"} <= closed, "a type the owner has given is never asked again"
    assert "O-11" in {x["ID"] for x in ledger["STILL_OPEN"]}


def test_the_three_other_gaps_are_still_unresolved_and_uninferred():
    o = opens()
    for sid in ("OS-b1e147c89482", "OS-3144b5fbb149", "OS-045efd7810a7"):
        assert o[sid]["TYPE"] == "UNRESOLVED"
        assert o[sid]["HEIGHT_M"] is None
        assert o[sid]["STATUS"] == "OWNER_INPUT_REQUIRED"
