"""The owner rule addendum of 2026-09-17, as tests.

Stairs, the open American pantry and the elevator marble standard — with
the one rule that governs all three: an owner rule says WHICH answer
applies and never supplies geometry. Where the geometry a rule needs is
not established, the answer is the rule's own refusal or a question for
the owner, never the default.
"""

from __future__ import annotations

import io
import json
import tokenize
from pathlib import Path

import pytest

from engine import elevator_marble as elev
from engine import functional_zone as fz
from engine import rule_library as rlib
from engine import stair_assembly as stair


def _code(module):
    out = []
    for tok in tokenize.generate_tokens(
            io.StringIO(open(module.__file__, encoding="utf-8").read())
            .readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        out.append(tok.string)
    return " ".join(out)


@pytest.fixture(scope="module")
def library():
    return rlib.load()


# ------------------------------------------------------ §M the library

def test_every_rule_carries_what_a_rule_must_carry(library):
    assert len(library.rules) >= 14
    for rule in library.rules.values():
        rec = rule.record()
        for field in rlib.REQUIRED_FIELDS:
            assert field in rec, f"{rule.rule_id} has no {field}"
        assert rule.version and rule.effective_date and rule.source
        assert rule.owner_confirmed is True
        assert rule.unknown_behavior


def test_a_record_missing_a_field_is_refused():
    with pytest.raises(rlib.RuleRefused):
        rlib.build([{"rule_id": "X", "rule_name": "a habit somebody typed"}])


def test_the_priority_order_is_drawing_project_standard_unknown(library):
    # the standard applies when nothing else says
    assert rlib.resolve(library, "UP-ELEV-002").source == rlib.SRC_STANDARD
    # the owner's project note outranks it
    assert rlib.resolve(library, "UP-ELEV-002",
                        project=400.0).source == rlib.SRC_PROJECT
    # and the drawing outranks them both
    got = rlib.resolve(library, "UP-ELEV-002", drawing=350.0,
                       project=400.0)
    assert got.source == rlib.SRC_DRAWING and got.value == 350.0


def test_a_mandatory_rule_takes_no_project_override_but_takes_the_drawing(
        library):
    got = rlib.resolve(library, "UP-PANTRY-004", project=3.0)
    assert got.source == rlib.SRC_STANDARD and not got.established
    assert rlib.resolve(library, "UP-PANTRY-004",
                        drawing=2.4).source == rlib.SRC_DRAWING


def test_a_default_is_never_applied_to_geometry_nobody_established(library):
    got = rlib.resolve(library, "UP-ELEV-002", geometry_established=False,
                       missing=("door_clear_width",))
    assert not got.established and got.value is None
    assert "door_clear_width" in got.what_is_missing


def test_an_unknown_rule_is_a_question_with_an_address(library):
    got = rlib.resolve(library, "UP-NOTHING-999")
    assert got.source == rlib.SRC_UNKNOWN
    assert rlib.NO_SUCH_RULE in got.what_is_missing
    assert got.question_for_the_owner
    req = rlib.owner_rule_request("كيال", where="GROUND FLOOR PLAN",
                                  question="what does this term mean?")
    assert req["exception"] == rlib.OWNER_RULE_REQUEST
    assert req["exact_term"] == "كيال" and req["where_in_the_drawing"]


def test_the_library_on_disk_is_the_one_that_loads(library):
    data = json.loads(Path(rlib.LIBRARY_PATH).read_text(encoding="utf-8"))
    assert len(data["rules"]) == len(library.rules)
    assert library.library_hash()


# --------------------------------------------- §A, §B the open pantry

def test_the_owner_settles_the_openness_and_supplies_no_geometry():
    rows = [{"space_id": "PS-1", "region_id": "DR-001",
             "area_m2": 12.0, "boundary_faces": []}]

    class _L:
        text, x, y, space_id, region_id = "PANTRY", 0.0, 0.0, "PS-1", "DR-001"

    rep = fz.assess(rows, [_L()],
                    owner_openness=fz.OPEN_AMERICAN_PANTRY)
    p = rep.pantries[0]
    assert p.openness == fz.OPEN_AMERICAN_PANTRY
    assert fz.EV_OWNER_CONFIRMED in p.openness_evidence
    # and NOT one millimetre of tile from it
    assert p.wall_tile_length_m == 0.0
    assert p.wall_tile_shape == fz.SHAPE_NOT_ESTABLISHED
    assert fz.TILE_WALLS_NEED_REVIEW in p.exceptions
    assert p.wall_tile_height_m is None


def test_an_open_pantry_never_borrows_the_perimeter_of_its_space():
    """UP-PANTRY-003: never tile the perimeter of an imaginary pantry."""
    rows = [{"space_id": "PS-1", "region_id": "DR-001", "area_m2": 30.0,
             "boundary_faces": [
                 {"axis": "H", "fixed_mm": 0.0, "length_mm": 6000.0,
                  "basis": "CLEAR_INTERNAL_FACE_TO_FACE",
                  "wall_band_id": "PW-1", "face_id": "F1"},
                 {"axis": "V", "fixed_mm": 0.0, "length_mm": 5000.0,
                  "basis": "CLEAR_INTERNAL_FACE_TO_FACE",
                  "wall_band_id": "PW-2", "face_id": "F2"}]}]

    class _L:
        text, x, y, space_id, region_id = "PANTRY", 0.0, 0.0, "PS-1", "DR-001"

    rep = fz.assess(rows, [_L()], owner_openness=fz.OPEN_AMERICAN_PANTRY)
    p = rep.pantries[0]
    assert p.openness == fz.OPEN_AMERICAN_PANTRY
    assert p.wall_tile_length_m == 0.0          # 11 m of wall is there
    assert fz.TILE_WALLS_NEED_REVIEW in p.exceptions


def test_no_tile_height_is_assumed_anywhere():
    body = _code(fz)
    for habit in ("2.40", "2.70", "3.00", "3.20"):
        assert habit not in body


def test_the_tiled_arrangement_has_a_word_for_what_is_drawn():
    assert fz._shape_of(1) == fz.ONE_WALL
    assert fz._shape_of(2) == fz.L_SHAPE
    assert fz._shape_of(3) == fz.U_SHAPE
    assert fz._shape_of(4) == fz.CLOSED_ON_FOUR_SIDES
    assert fz._shape_of(5) == fz.OTHER_DRAWN_CONFIGURATION
    assert fz._shape_of(0) == fz.SHAPE_NOT_ESTABLISHED


# ------------------------------------------------ §C–§G the stairs

def test_the_finish_rule_reaches_every_stair_not_only_the_main_one():
    reports, made = [], []
    for role in (stair.MAIN_INTERIOR_STAIR, stair.SECONDARY_INTERIOR_STAIR,
                 stair.EXTERIOR_STEPS, stair.STAIR_ROLE_UNKNOWN):
        a = stair.Assembly(stair_id=f"SA-{role}", region_id="DR-001")
        a.stair_role = role
        made.append(a)
    rep = stair.StairReport(region_id="DR-001")
    rep.assemblies = made
    reports.append(rep)
    out = stair.reconcile(
        reports, finish_rules={"ALL": {"finish": "MARBLE",
                                       "rule_id": "UP-STAIR-001@1.0.0"}})
    assert out["physical_stairs"]
    for x in out["physical_stairs"]:
        assert x.finish == "MARBLE"
        assert x.finish_source == "UP-STAIR-001@1.0.0"


def test_a_stair_with_no_rule_is_not_marble_because_it_is_a_stair():
    rep = stair.StairReport(region_id="DR-001")
    rep.assemblies = [stair.Assembly(stair_id="SA-1", region_id="DR-001")]
    out = stair.reconcile([rep])
    assert out["physical_stairs"][0].finish == stair.FINISH_NOT_CONFIRMED


def test_the_visible_riser_is_the_rise_less_the_tread_build_up():
    """The owner's worked example, as arithmetic and not as a constant."""
    visible, source = stair._visible_riser(160.0, 30.0)
    assert visible == 130.0 and "BUILD_UP" in source
    width_mm = 1200.0
    assert round(width_mm * 300.0 / 1e6, 4) == 0.36        # TREAD_M2
    assert round(width_mm * visible / 1e6, 4) == 0.156     # RISER_VISIBLE
    assert round(0.36 + 0.156, 4) == 0.516                 # per step


def test_the_visible_riser_is_never_invented():
    assert stair._visible_riser(160.0, None) == (
        None, stair.BUILD_UP_NOT_ESTABLISHED)
    assert stair._visible_riser(None, 30.0) == (
        None, stair.VISIBLE_RISER_NOT_ESTABLISHED)
    body = _code(stair)
    for habit in ("130.0", "0.13", "160.0", "30.0 ", "120.0"):
        assert f"= {habit}" not in body


def test_a_riser_with_no_visible_height_reports_none_not_zero():
    r = stair.Riser(riser_id="SR-1", width_mm=1200.0, height_mm=160.0,
                    area_m2=0.192)
    rec = r.record()
    assert rec["RISER_VISIBLE_M2"] is None
    assert rec["visible_source"] == stair.VISIBLE_RISER_NOT_ESTABLISHED


def test_a_measurement_basis_is_not_a_pricing_basis():
    q = stair.quantities([], [])
    assert q[stair.COMMERCIAL_BASIS] == stair.COMMERCIAL_NOT_ESTABLISHED
    q2 = stair.quantities([], [], commercial_basis="PER_STEP")
    assert q2[stair.COMMERCIAL_BASIS] == "PER_STEP"
    assert q2[stair.GEOMETRIC_UNIT]["TREAD_AREA"] == stair.UNIT_M2
    assert q2[stair.GEOMETRIC_UNIT]["RAILING_PATH"] == stair.UNIT_LM


# ------------------------------------------- §H–§L the elevator marble

def test_a_station_is_a_landing_door_and_not_a_shaft():
    out = elev.stations({"elevators": [
        {"elevator_id": "ELV-01", "floors_served": ["GF", "FF", "SF", "RF"]}]})
    assert out["station_count"] == 4
    ids = [s["elevator_station_id"] for s in out["stations"]]
    assert ids == ["ELV-01-GF", "ELV-01-FF", "ELV-01-SF", "ELV-01-RF"]


def test_two_doors_on_one_floor_are_two_assemblies():
    out = elev.stations({"elevators": [
        {"elevator_id": "ELV-02", "floors_served": ["GF"],
         "doors_per_floor": {"GF": 2}}]})
    assert out["station_count"] == 2
    assert [s["elevator_station_id"] for s in out["stations"]] == [
        "ELV-02-GF-1", "ELV-02-GF-2"]


def test_the_surround_is_the_union_area_and_neither_naive_answer():
    s = elev.measure_surround("ELV-01-GF", door_width_mm=1000.0,
                              door_height_mm=2100.0, left_mm=500.0,
                              top_mm=500.0, right_mm=500.0)
    assert s.status == elev.MEASURED
    assert round(s.area_m2, 4) == 3.1
    # along the door edge, three sides x 0.50: misses both top corners
    assert round((2.1 + 1.0 + 2.1) * 0.5, 4) == 2.6
    # three full bands added: counts both top corners twice
    assert round((2.1 + 0.5) * 0.5 * 2 + 2.0 * 0.5, 4) == 3.6
    assert s.area_m2 not in (2.6, 3.6)


def test_the_surround_takes_three_different_widths():
    s = elev.measure_surround("ELV-01-FF", door_width_mm=900.0,
                              door_height_mm=2200.0, left_mm=400.0,
                              top_mm=600.0, right_mm=500.0)
    expect = (0.4 * 2.2) + (0.5 * 2.2) + ((0.4 + 0.9 + 0.5) * 0.6)
    assert round(s.area_m2, 4) == round(expect, 4)


def test_an_area_and_an_edge_length_are_kept_apart():
    s = elev.measure_surround("ELV-01-GF", door_width_mm=1000.0,
                              door_height_mm=2100.0, left_mm=500.0,
                              top_mm=500.0, right_mm=500.0)
    rec = s.record()
    assert rec["ELEVATOR_SURROUND_AREA_M2"] == 3.1
    assert rec["ELEVATOR_SURROUND_EDGE_LM"] == 7.2
    assert rec["measurement_basis"] == elev.FROM_A_POLYGON


def test_a_station_with_no_door_geometry_measures_nothing():
    s = elev.measure_surround("ELV-01-SF", left_mm=500.0, top_mm=500.0,
                              right_mm=500.0)
    assert s.status == elev.SURROUND_NOT_ESTABLISHED
    assert s.area_m2 is None
    assert "door_clear_width" in s.what_is_missing


def test_the_threshold_is_its_own_object_and_its_depth_is_asked_for():
    t = elev.measure_threshold("ELV-01-GF", width_mm=1000.0)
    assert t.status == elev.THRESHOLD_DEPTH_NOT_ESTABLISHED
    assert t.area_m2 is None
    out = elev.stations({"elevators": [
        {"elevator_id": "ELV-01", "floors_served": ["GF"],
         "doors": {"ELV-01-GF": {"door_clear_width_mm": 1000.0,
                                 "door_clear_height_mm": 2100.0}}}]})
    asked = [x for x in out["exceptions"]
             if x["kind"] == "ELEVATOR_THRESHOLD"]
    assert asked and "depth" in asked[0]["question_for_the_owner"]
    station = out["stations"][0]
    assert station["threshold"]["ELEVATOR_THRESHOLD_AREA_M2"] is None
    # and the threshold never becomes part of the vertical surround
    assert station["surround"]["ELEVATOR_SURROUND_AREA_M2"] == 3.1


def test_the_drawing_beats_the_half_metre_default(library):
    out = elev.stations({"elevators": [
        {"elevator_id": "ELV-03", "floors_served": ["GF"],
         "doors": {"ELV-03-GF": {"door_clear_width_mm": 1000.0,
                                 "door_clear_height_mm": 2100.0,
                                 "surround_width_mm_drawn": 300.0}}}]},
        library=library)
    s = out["stations"][0]["surround"]
    assert s["left_surround_width_mm"] == 300.0
    assert s["surround_width_source"] == rlib.SRC_DRAWING


def test_no_elevator_geometry_is_invented_for_this_project():
    project = json.loads(
        Path("data/registry/P7757_PROJECT_RULES.json").read_text(
            encoding="utf-8"))
    out = elev.stations(project.get("elevator") or {})
    assert out["station_count"] == 0
    assert out["status"] == elev.STATIONS_NOT_ESTABLISHED
