"""The Al Rashed villa: a real blind project, and the two things that had to be settled before measuring it.

The drawing file says its unit is inches.  The building says otherwise, and the engine is not allowed to take
either on faith: the declared unit only overrules the file when the drawing's own wall pairs land inside the band
every masonry wall is inside under one reading and outside it under the other.

The DWG holds nine plan windows - three storeys times three revisions - and only three of them were plotted.  The
current row is identified by dimension containment against the PDF, not by position on the sheet.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import geometry as G, identity as ID, questions as Q

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"


def reg(name):
    return json.loads((OUT / f"{name}.json").read_text("utf-8"))


# ------------------------------------------------------------------ the unit
def test_the_engine_ran_on_the_villa_without_touching_anything_it_should_not():
    r = reg("ALRASHED_BLIND_RESULT")
    assert r["STATUS"] == "COMPLETED"
    assert r["VIOLATIONS"] == []


def test_a_wrong_insunits_is_overruled_only_on_wall_evidence():
    u = json.loads((OUT / "blind" / "PA06_SOURCE_UNIT_REGISTER.json").read_text("utf-8"))["ROWS"][0]
    assert u["RAW_INSUNITS"] == 1, "the file really does claim inches"
    assert u["UNIT_CANDIDATE"] == "m" and u["UNIT_SCALE_TO_MM"] == 1000.0
    assert u["PROVENANCE"] == "DECLARED_OVERRIDES_IMPLAUSIBLE_INSUNITS"
    o = u["INSUNITS_OVERRIDE"]
    assert o["OVERRULED_UNIT"] == "in"
    lo, hi = o["WALL_BAND_MM"]
    assert not (lo <= o["OVERRULED_WALL_THICKNESS_MODE_MM"] <= hi), "inches must fail the band"
    assert lo <= o["DECLARED_WALL_THICKNESS_MODE_MM"] <= hi, "metres must pass it"
    assert u["ACCEPTABLE_FOR_QUANTITIES"] is True


def test_a_declaration_without_evidence_cannot_overrule_the_file():
    """The override is not a back door: it needs the wall band to disagree, not just a declaration."""
    from engine.ingest import source_units as SU
    assert "WALL_THICKNESS_IN_BAND" in SU._secondary([], None, (), 1000.0)
    src = Path("engine/ingest/source_units.py").read_text("utf-8")
    assert 'sec_ins.get("WALL_THICKNESS_IN_BAND") is False' in src
    assert 'sec_dec.get("WALL_THICKNESS_IN_BAND") is True' in src


# ------------------------------------------------------------------ the plans
def test_only_three_of_the_nine_plan_windows_are_the_current_set():
    r = reg("ALRASHED_PROJECT_IDENTITY_AND_FLOOR_INVENTORY")
    rv = r["REVISION_SETS_IN_THE_DWG"]
    assert rv["PLAN_WINDOWS_FOUND"] == 9
    assert set(rv["WINDOWS"]) == {"BASEMENT", "GROUND", "FIRST"}
    assert "1.000" in rv["HOW_THE_CURRENT_ROW_WAS_IDENTIFIED"]


def test_every_floor_recovers_a_grid_walls_and_spaces():
    for f in reg("ALRASHED_PROJECT_IDENTITY_AND_FLOOR_INVENTORY")["FLOORS"]:
        assert f["WALL_SEGMENTS"] > 0 and f["SPACE_COMPONENTS_ABOVE_MIN"] > 0, f["FLOOR"]
        assert f["GRID_CELLS"][0] > 0 and f["GRID_CELLS"][1] > 0


def test_a_doorway_is_closed_for_room_bounding_but_is_not_wall_material():
    """A gap up to a door width is spanned; a genuinely open side is not."""
    walls = [("H", 0.0, 0.0, 3.0), ("H", 0.0, 4.0, 10.0),      # 1.00 m gap - a door
             ("V", 0.0, 0.0, 2.0), ("V", 0.0, 9.0, 10.0)]      # 7.00 m gap - an open side
    cl = G.closures(walls)
    assert len(cl) == 1 and cl[0][0] == "H"
    assert abs((cl[0][3] - cl[0][2]) - 1.0) < 1e-9
    assert all(c not in walls for c in cl), "a closure is never one of the wall segments"


def test_the_plot_arithmetic_on_the_sheet_agrees_with_itself():
    i = reg("ALRASHED_PROJECT_IDENTITY_AND_FLOOR_INVENTORY")["IDENTITY"]
    assert i["PLOT_AREA_M2"] == 600.00
    assert abs(22.00 * 27.28 - 600.16) < 1e-9


def test_the_area_schedule_is_recorded_as_read_not_assigned_to_floors():
    a = reg("ALRASHED_PROJECT_IDENTITY_AND_FLOOR_INVENTORY")["AREA_SCHEDULE_AS_DRAWN"]
    assert a["NOT_ESTABLISHED"]
    assert abs(sum([382.16, 69.66]) - 451.82) < 1e-9
    assert "not an input" in a["USE"]


# ------------------------------------------------------------------ what is missing
def test_the_missing_disciplines_say_what_they_cost():
    d = reg("ALRASHED_PROJECT_IDENTITY_AND_FLOOR_INVENTORY")["DISCIPLINES"]
    assert "sections" in d["ABSENT"] and "structural" in d["ABSENT"]
    for k, v in d["WHAT_THE_ABSENCE_COSTS"].items():
        assert v, k


def test_no_qortuba_dimension_is_inherited():
    src = (Path("research/qs_wall_treatment_01/pa09/alrashed/blind.py").read_text("utf-8")
           + Path("research/qs_wall_treatment_01/pa09/alrashed/identity.py").read_text("utf-8")
           + Path("research/qs_wall_treatment_01/pa09/alrashed/questions.py").read_text("utf-8"))
    for qortuba in ("3.000", "2.200", "1.500", "QORTUBA_WALL_HEIGHT", "QORTUBA_WINDOW_HEIGHT"):
        assert qortuba not in src, qortuba
    cfg = reg("ALRASHED_BLIND_CONFIG")
    for k, v in cfg["OWNER_PARAMETER_REGISTRY"].items():
        if isinstance(v, dict):
            assert v.get("VALUE") is None, k


# ------------------------------------------------------------------ the questions
def test_one_batch_of_questions_that_each_change_a_quantity():
    q = reg("ALRASHED_OWNER_QUESTIONS_BATCH_01")
    assert q["BATCH"] == 1 and q["COUNT"] == len(q["QUESTIONS"])
    assert all(x["NO"].startswith("AR-") for x in q["QUESTIONS"])
    for x in q["QUESTIONS"]:
        assert x["DRAWING_GIVES"] and x["DRAWING_DOES_NOT_GIVE"] and x["ASK"].endswith("?") is False or "?" in x["ASK"]
        assert x["WHY"]


def test_no_question_shows_the_owner_a_cad_hash_or_an_id():
    for x in Q.QUESTIONS:
        blob = x["ASK"] + x["DRAWING_GIVES"] + x["DRAWING_DOES_NOT_GIVE"]
        for bad in ("OS-", "PS-", "MB-", "PF-", "VW-", "SHA", "handle", "layer"):
            assert bad not in blob, (x["NO"], bad)


def test_nothing_the_drawing_answers_is_put_to_the_owner():
    q = reg("ALRASHED_OWNER_QUESTIONS_BATCH_01")
    subjects = " ".join(x["SUBJECT"].lower() for x in q["QUESTIONS"])
    for settled in ("drawing unit", "wall thickness", "which revision"):
        assert settled not in subjects, settled


# ------------------------------------------------------------------ the plan-area takeoff
def take():
    return json.loads((OUT / "ALRASHED_FIRST_PLAN_AREA_TAKEOFF.json").read_text("utf-8"))


def test_every_square_metre_of_each_plan_belongs_to_exactly_one_component():
    """The closure check: a residual other than zero would mean area was created or lost."""
    for f in take()["FLOORS"]:
        c = f["CLOSURE"]
        assert abs(c["RESIDUAL_M2"]) < 1e-3, (f["FLOOR"], c)
        assert c["PLAN_WINDOW_RECTANGLE_M2"] > 0


def test_room_names_are_placed_by_a_transform_that_is_checked_not_assumed():
    for f in take()["FLOORS"]:
        t = f["LABEL_TRANSFORM"]
        assert t["ESTABLISHED"] is True, f["FLOOR"]
        assert t["MAX_RESIDUAL_M"] <= 0.05, (f["FLOOR"], t["MAX_RESIDUAL_M"])
        assert abs(abs(t["ROT_DEG"]) - 90) < 0.1, "the plans are turned through a right angle on the sheet"
        assert t["INLIERS"] >= 8


def test_rooms_reproduce_the_dimensions_printed_beside_them():
    """The kitchen is dimensioned 820 x 500 on the sheet; the recovered room is 41.000 m2."""
    gr = next(f for f in take()["FLOORS"] if f["FLOOR"] == "GROUND")
    k = next(r for r in gr["ROOMS"] if r["NAME"] == "KITCHEN")
    assert abs(k["WIDTH_M"] - 8.20) < 0.01 and abs(k["DEPTH_M"] - 5.00) < 0.01
    assert abs(k["AREA_M2"] - 41.000) < 0.01


def test_a_space_the_drawing_does_not_name_keeps_its_area_and_loses_no_identity_it_never_had():
    rows = [r for f in take()["FLOORS"] for r in f["ROOMS"]]
    unnamed = [r for r in rows if r["ROLE"] == "UNNAMED_ON_DRAWING"]
    assert unnamed, "there are unlabelled spaces and they are reported, not hidden"
    for r in unnamed:
        assert r["NAME"] is None and r["AREA_M2"] > 0


def test_no_wall_height_is_assumed_anywhere_in_the_takeoff():
    t = take()
    assert "no clear height is assumed" in t["HEIGHT_RULE"]
    for o in t["OPENINGS_ALL"]:
        assert o["HEIGHT_M"] is None and o["AREA_M2"] is None
        assert o["HEIGHT_STATUS"] == "OWNER_INPUT_REQUIRED"
    blob = json.dumps(t)
    assert "3.80" not in blob, "the 4.00 m floor-to-floor is never turned into a clear height"


def test_openings_carry_a_clear_width_that_a_door_or_window_could_be():
    ops = take()["OPENINGS_ALL"]
    assert len(ops) > 100
    for o in ops:
        assert 0 < o["CLEAR_WIDTH_M"] <= 3.0


def test_the_stair_is_plan_geometry_only():
    for s in take()["STAIRS"]:
        assert s["STATUS"] == "PLAN_GEOMETRY_ONLY" and s["STAIR_LINES"] > 0


# ------------------------------------------------------------------ the schedule, as validation only
def test_the_first_floor_reproduces_the_sheets_own_area_figure():
    row = next(r for r in take()["AREA_SCHEDULE_RECONCILIATION"]["ROWS"] if r["SCHEDULE_FIGURE_M2"] == 69.66)
    assert row["AGREEMENT"] == "EXACT"
    assert abs(row["DELTA_PCT"]) < 0.05
    assert abs(8.10 * 8.60 - 69.66) < 1e-9


def test_a_schedule_figure_that_is_not_reproduced_is_left_unestablished():
    rows = take()["AREA_SCHEDULE_RECONCILIATION"]["ROWS"]
    assert any(r["AGREEMENT"] == "NOT_ESTABLISHED" for r in rows)
    assert "no schedule figure was used as a quantity" in take()["AREA_SCHEDULE_RECONCILIATION"]["RULE"]


def test_no_measured_area_was_moved_towards_the_schedule():
    """The ground floor is 5.48 m2 off the schedule and stays off it."""
    row = next(r for r in take()["AREA_SCHEDULE_RECONCILIATION"]["ROWS"] if r["SCHEDULE_FIGURE_M2"] == 382.16)
    assert row["DELTA_M2"] != 0 and row["AGREEMENT"] == "NOT_ESTABLISHED"
