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
