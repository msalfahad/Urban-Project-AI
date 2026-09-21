"""OPENING COMPLETION: the search that proves a height is not there, and the gap that is not a doorway.

An exhaustive search that finds nothing is a result, and it has to be recorded as carefully as one that finds something,
because the alternative is searching again next month and guessing in the meantime.  These tests hold that the search
was actually made, that its emptiness is stated rather than implied, and that the two things it DID resolve - a gap
through one face is not an opening, and a window with a sill is still an opening in the wall area - reach the quantities
they should and no others.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.boq import opening_source_search as OS

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
R1 = Path(PR.OUT_DIR) / "pa08_qortuba_r1"


def reg(name, folder=OUT):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


def opens():
    return reg("QORTUBA_OPENING_REGISTER_COMPLETED")


def by_id():
    return {x["QUANTITY_ID"]: x for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]}


# ------------------------------------------------------------------ §1 the search
def test_the_search_names_what_it_looked_for_and_what_was_there():
    s = opens()["SOURCE_SEARCH"]
    looked = {c["LOOKED_FOR"] for c in s["CHECKS"]}
    assert {"BLOCK_ATTRIBUTES", "AUTHORED_DIMENSIONS", "WINDOW_OR_DOOR_BLOCKS", "OPENING_SCHEDULE",
            "ANNOTATIONS_CARRYING_A_HEIGHT", "EMBEDDED_ELEVATIONS_OR_SECTIONS",
            "REPEATED_IDENTICAL_BLOCK_DEFINITIONS", "PDF_COMPANION"} <= looked
    for c in s["CHECKS"]:
        assert len(c["WHAT_WAS_THERE"]) > 40, c["LOOKED_FOR"]


def test_the_search_really_read_the_decode_and_not_a_summary():
    s = opens()["SOURCE_SEARCH"]
    assert s["ENTITY_CENSUS"]["DIMENSION_LINEAR"] == 101
    assert s["ENTITY_CENSUS"].get("ATTRIB", 0) == 0 and s["ENTITY_CENSUS"].get("ATTDEF", 0) == 0
    assert "WALL" in s["LAYERS"] and "WINDOW" in s["LAYERS"] and "arrow2" in s["LAYERS"]
    assert "SECOND FLOOR PLAN" in s["PROSE_STRINGS"]
    assert s["DIMENSION_VALUE_OVERRIDES"] >= 49, "the plan dimension text overrides were read"


def test_the_drawing_set_contains_no_opening_height_and_says_so():
    s = opens()["SOURCE_SEARCH"]
    assert s["OPENING_HEIGHTS_FOUND"] == 0 and s["OPENING_TYPE_MARKS_FOUND"] == 0
    assert "no opening height of any kind" in s["CONCLUSION"]
    assert s["WHAT_WOULD_SUPPLY_ONE"]
    assert opens()["HEIGHTS_FROM_THE_DRAWING"] == 0


def test_no_named_block_is_a_door_or_window_type():
    s = opens()["SOURCE_SEARCH"]
    for b in s["NAMED_BLOCK_DEFINITIONS"]:
        assert not b.startswith("*"), b
    assert "FRAM" in s["NAMED_BLOCK_DEFINITIONS"], "the fixture needs the frame block that exists"


# ------------------------------------------------------------------ §1 the register
def test_every_opening_carries_the_eight_required_fields():
    for r in opens()["ROWS"]:
        for k in ("OPENING_ID", "ROOM", "TYPE", "WIDTH_M", "HEIGHT_M", "WIDTH_SOURCE", "HEIGHT_SOURCE", "STATUS"):
            assert k in r, (r["OPENING_ID"], k)
        assert r["TYPE"] in OS.OPENING_TYPES
        assert r["WIDTH_M"] > 0 and r["WIDTH_SOURCE"]
        assert r["STATUS"] in ("USABLE", "OWNER_INPUT_REQUIRED", "NOT_AN_OPENING", "PARTIAL_HEIGHT_REQUIRED")


def test_a_height_exists_only_where_the_owner_default_may_reach():
    owner = OS.OWNER_SUPPLIED_HEIGHTS
    for r in opens()["ROWS"]:
        if r["HEIGHT_M"] is None:
            assert r["HEIGHT_SOURCE"] is None
            continue
        if r["OPENING_ID"] in owner:
            # an owner override is a real dimension and may reach any type
            assert r["HEIGHT_M"] == owner[r["OPENING_ID"]][0] and "OWNER" in r["HEIGHT_SOURCE"]
            continue
        assert r["TYPE"] == "DOOR" and r["HEIGHT_M"] == OS.DEFAULT_DOOR_HEIGHT_M
        assert "TD-02" in r["HEIGHT_SOURCE"]
    assert opens()["DEFAULT_APPLIED_ONLY_TO_ORDINARY_DOORS"] is True


def test_the_default_width_is_never_used_because_every_width_is_measured():
    for r in opens()["ROWS"]:
        assert "DWG" in r["WIDTH_SOURCE"], r["OPENING_ID"]
        assert r["WIDTH_M"] != OS.DEFAULT_DOOR_WIDTH_M or "DWG" in r["WIDTH_SOURCE"]


def test_a_gap_through_one_face_is_not_a_doorway():
    sites = {r["SITE_ID"]: r for r in reg("PA08_QORTUBA_R1_OPENING_REGISTER", R1)["ROWS"]}
    single = {s for s, r in sites.items() if r["STATUS"] == "SINGLE_FACE_GAP"}
    assert len(single) == 5
    rows = {r["OPENING_ID"]: r for r in opens()["ROWS"]}
    for s in single:
        assert rows[s]["IS_AN_OPENING_THROUGH_THE_WALL"] is False, s
        assert rows[s]["STATUS"] == "NOT_AN_OPENING"
        assert "interrupts both" in rows[s]["WHY_NOT_AN_OPENING"]


def test_a_cad_junction_is_not_an_opening_either():
    rows = {r["OPENING_ID"]: r for r in opens()["ROWS"]}
    junc = [r for r in rows.values() if r["SITE_CLASS"] == "CAD_JUNCTION"]
    assert len(junc) == 4
    for r in junc:
        assert r["IS_AN_OPENING_THROUGH_THE_WALL"] is False and r["STATUS"] == "NOT_AN_OPENING"


def test_a_window_with_a_sill_is_still_an_opening_in_the_wall_area():
    rows = {r["OPENING_ID"]: r for r in opens()["ROWS"]}
    sills = opens()["DOES_NOT_REACH_THE_FLOOR"]
    assert len(sills) == 6
    for s in sills:
        assert rows[s]["IS_AN_OPENING_THROUGH_THE_WALL"] is True, s
        assert rows[s]["INTERRUPTS_AT_FLOOR_LEVEL"] is False
        assert rows[s]["STATUS"] == "OWNER_INPUT_REQUIRED"


def test_the_pdf_reading_is_recorded_as_evidence_and_not_as_a_dimension():
    rows = {r["OPENING_ID"]: r for r in opens()["ROWS"]}
    quoted = [r for r in rows.values() if r["PDF_READER"]]
    assert len(quoted) == 3
    for r in quoted:
        if r["OPENING_ID"] in OS.OWNER_SUPPLIED_HEIGHTS:
            assert "OWNER" in r["HEIGHT_SOURCE"], "the height came from the owner, never from the reader"
            continue
        assert r["HEIGHT_M"] is None, "a reader may speak to type, never to a dimension"


# ------------------------------------------------------------------ §2 one opening, one wall
def test_an_opening_blocks_only_its_own_rooms():
    ops = {o["OPENING_ID"]: o for o in reg("QORTUBA_OPENING_REGISTER")["ROWS"]}
    rooms = {r["ROOM"]: r for r in reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]}
    for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]:
        if not x["ROOMS"]:
            continue
        alias = set(x["ROOMS"]) | {r.split(" /")[0] for r in x["ROOMS"]}
        alias |= {rooms[r]["ROOM"] for r in rooms if rooms[r]["ROOM_NAME"] in alias}
        for o in x["RESIDUAL_OPENINGS"]:
            oid = o.get("OPENING_ID")
            if oid and ops.get(oid, {}).get("ROOMS"):
                assert set(ops[oid]["ROOMS"]) & alias, (x["QUANTITY_ID"], oid)


def test_a_non_opening_blocks_nothing_at_all():
    dead = set(opens()["NOT_AN_OPENING"])
    assert len(dead) == 9
    for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]:
        named = {o.get("OPENING_ID") for o in x["RESIDUAL_OPENINGS"]}
        assert not (named & dead), (x["QUANTITY_ID"], named & dead)


# ------------------------------------------------------------------ the owner's confirmed skirting
def test_the_skirting_and_profile_are_the_owner_s_fixed_figure():
    q = by_id()
    for qid in ("Q-01", "Q-02"):
        # 86.589 was the figure before the owner identified the two open passages; each interrupts the path of BOTH
        # rooms it joins, so 4 x 1.200 lm left it.  The window rule QP-09 that fixed 86.589 is unchanged.
        assert q[qid]["MEASURED_NET_QUANTITY"] == 81.789, qid
        assert q[qid]["VALUE_BEFORE_THE_OPEN_PASSAGE_CORRECTION"] == 86.589, qid
        assert q[qid]["OPEN_PASSAGE_DEDUCTION_LM"] == 4.8, qid
        assert q[qid]["STATUS"] == "FINAL_QUANTITY_AVAILABLE"
        assert "QP-09" in q[qid]["RULE_ID"]
    assert q["Q-01"]["MEASURED_NET_QUANTITY"] == q["Q-02"]["MEASURED_NET_QUANTITY"]
    rules = {r["PARAMETER"]: r for r in reg("URBAN_OWNER_RULES_V1")["QORTUBA_PROJECT_RULES"]}
    assert rules["QORTUBA_HIDDEN_SKIRTING_PATH"]["VALUE"] == 81.789
    assert rules["QORTUBA_HIDDEN_PROFILE_PATH"]["VALUE"] == 81.789
    assert rules["QORTUBA_SKIRTING_WINDOW_DEDUCTION"]["RULE_LEVEL"] == "QORTUBA_PROJECT_RULE"


def test_the_superseded_reading_is_kept_as_an_audit_trail_not_as_a_quantity():
    q = by_id()["Q-01"]
    assert q["VALUE_UNDER_THE_SUPERSEDED_READING"] == 91.675
    assert q["SUPERSEDED_READING_CLOSED_BY"].startswith("QP-09")
    assert q["MEASURED_NET_QUANTITY"] != q["VALUE_UNDER_THE_SUPERSEDED_READING"]


# ------------------------------------------------------------------ §7 aluminium
def test_the_aluminium_rows_are_schedules_and_never_bare_counts():
    q = by_id()
    for qid in ("Q-15", "Q-16", "Q-17"):
        x = q[qid]
        assert x["UNIT"] == "M2", qid
        assert x["SCHEDULE"] and x["OPENINGS"] == len(x["SCHEDULE"])
        assert x["COUNT_IS_NOT_THE_QUANTITY"]
        for row in x["SCHEDULE"]:
            assert row["WIDTH_M"] > 0 and row["OPENING_ID"]
            if row["HEIGHT_M"] is None:
                assert row["AREA_M2"] is None and row["STATUS"] == "OWNER_INPUT_REQUIRED" and row["WHY"]
            else:
                assert abs(row["AREA_M2"] - round(row["WIDTH_M"] * row["HEIGHT_M"], 4)) < 1e-9


def test_a_window_without_a_height_stays_owner_input_required():
    x = by_id()["Q-15"]
    assert x["STATUS"] == "OWNER_INPUT_REQUIRED" and x["MEASURED_NET_QUANTITY"] is None
    assert x["RESOLVED"] == 0 and x["OPENINGS"] > 0
    assert "forbids a default" in x["PARAMETER_SOURCE"]
    assert x["BOQ_ITEM"] == "ALUMINIUM_EXTERNAL_WINDOWS"


def test_the_door_areas_sum_to_the_schedule():
    x = by_id()["Q-16"]
    assert abs(x["MEASURED_NET_QUANTITY"] - round(sum(r["AREA_M2"] for r in x["SCHEDULE"]), 4)) < 1e-9
    assert x["USES_TEMPORARY_DEFAULT"] is True
    assert x["BOQ_ITEM"] == "PVC_INTERNAL_DOORS", "US-13: an interior door is never an aluminium item"
    assert all(r["MATERIAL_TRADE"] == "PVC" for r in x["SCHEDULE"])


# ------------------------------------------------------------------ nothing moved
def test_no_geometry_was_touched_by_the_completion():
    q = reg("QORTUBA_RECALCULATED_QUANTITIES_V1")
    assert q["GEOMETRY_STAGES_RERUN"] == 0 and q["WASTE_APPLIED_ANYWHERE"] is False
    fz = reg("FREEZE_URBAN_OWNER_RULES_V1")
    assert fz["QORTUBA_GEOMETRY_CHANGED"] == "NONE" and fz["NEW_TAKEOFF_PHASES_CREATED"] == 0
    ident = reg("QORTUBA_WALL_OBJECT_IDENTITY")
    assert ident["BLOCKWORK_CONFIRMED_LENGTH_M"] == 128.38
