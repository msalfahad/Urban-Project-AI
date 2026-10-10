"""The Al Rashed finishing takeoff: the owner's heights, the drawing's widths, and what neither supplies.

The owner gave four heights and one rule.  The tests hold the boundary between them and the drawing: a height the
owner gave is labelled as theirs, a width the drawing gives is never replaced by a default, and an opening whose
width no supplied file states carries no area at all rather than a plausible one.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import owner_inputs as OI, quantities as Q

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"


def rec():
    return json.loads((OUT / "ALRASHED_FINISHING_TAKEOFF.json").read_text("utf-8"))


# ------------------------------------------------------------------ whose number is whose
def test_the_owners_heights_are_recorded_as_the_owners_and_do_not_travel():
    for k, v in OI.PROJECT_INPUTS.items():
        assert v["KIND"] == "OWNER_CONFIRMED_PROJECT_INPUT"
        assert v["TRAVELS"] is False, k
    assert OI.AR01_WALL_HEIGHT_M == 3.600


def test_the_wet_room_rule_is_an_urban_standard_and_does_travel():
    r = OI.US_WET_ROOM_FINISH
    assert r["KIND"] == "URBAN_STANDARD" and r["TRAVELS"] is True and r["RULE_ID"] == "US-18"
    assert r["ON_A_FULLY_TILED_FACE"]["NORMAL_WALL_PAINT"] == 0
    assert r["ON_A_FULLY_TILED_FACE"]["NORMAL_SKIRTING"] == 0


def test_the_slab_thickness_is_still_not_assumed():
    """3.60 m came from the owner, not from 4.00 minus a guessed slab."""
    blob = json.dumps(rec())
    assert "3.80" not in blob
    for f in rec()["FLOORS"]:
        assert f["PLASTER_AND_PAINT"]["HEIGHT_M"] == 3.600
        assert "OWNER" in f["PLASTER_AND_PAINT"]["HEIGHT_SOURCE"]


# ------------------------------------------------------------------ widths
def test_a_drawn_width_is_never_replaced_by_the_default():
    assert OI.WIDTH_RULE["DEFAULT_DOOR_WIDTH_M"] == 1.000
    for f in rec()["FLOORS"]:
        for o in f["OPENINGS"]:
            if o["WIDTH_SOURCE"] == "DRAWING_JAMB_TO_JAMB":
                assert o["WIDTH_M"] and 0 < o["WIDTH_M"] <= 3.2
    widths = [o["WIDTH_M"] for f in rec()["FLOORS"] for o in f["OPENINGS"] if o["WIDTH_M"]]
    assert len(set(widths)) > 1, "widths are measured, not stamped from one default"


def test_a_window_with_no_readable_width_carries_no_area():
    wins = [o for f in rec()["FLOORS"] for o in f["OPENINGS"] if o["TYPE"] == "WINDOW"]
    assert wins, "the window symbols are located even though their widths are not readable"
    for w in wins:
        assert w["WIDTH_M"] is None and w["AREA_M2"] is None
        assert w["STATUS"] == "SOURCE_REQUIRED" and w["HEIGHT_M"] == OI.AR03_WINDOW_HEIGHT_M


def test_an_opening_of_unknown_type_is_not_quietly_called_a_door():
    for f in rec()["FLOORS"]:
        for o in f["OPENINGS"]:
            if o["TYPE"] == "UNKNOWN":
                assert o["AREA_M2"] is None and o["STATUS"] == "TYPE_CLASSIFICATION_PENDING"
            else:
                assert o["TYPE_SOURCE"] in ("CAD_SYMBOL_IN_THE_OPENING", "CAD_SYMBOL")


# ------------------------------------------------------------------ the trades
def test_blockwork_is_split_by_the_thickness_the_drawing_gives():
    for f in rec()["FLOORS"]:
        ts = {b["THICKNESS_MM"] for b in f["BLOCKWORK"]}
        assert 200 in ts, f["FLOOR"]
        for b in f["BLOCKWORK"]:
            assert b["NET_AREA_M2"] <= b["GROSS_AREA_M2"] + 1e-9
            assert b["NET_AREA_M2"] > 0, "no wall may deduct more than it contains"
            assert abs(b["GROSS_AREA_M2"] - b["LENGTH_M"] * 3.600) < 0.01


def test_a_tiled_face_takes_no_paint():
    for f in rec()["FLOORS"]:
        p = f["PLASTER_AND_PAINT"]
        assert abs(p["INTERNAL_PAINT_M2"]
                   - (p["INTERNAL_PLASTER_NET_M2"] - p["TILED_FACE_AREA_M2"])) < 0.01
        assert p["TILE_PREPARATION_M2"] == p["TILED_FACE_AREA_M2"]


def test_wet_rooms_are_tiled_by_the_rule_without_asking_again():
    wet = [w for f in rec()["FLOORS"] for w in f["WET_ROOMS"]]
    assert wet
    for w in wet:
        assert w["RULE"] == "US-18"
        assert w["SKIRTING_M"] == 0 and w["WALL_PAINT_M2"] == 0
        assert abs(w["WALL_TILE_AREA_M2"] - w["PERIMETER_M"] * 3.600) < 0.01


def test_the_roof_area_is_final_even_though_its_finish_is_not():
    rp = rec()["ROOF_AND_PARAPET"]
    assert rp["AREA_STATUS"] == "FINAL_QUANTITY_AVAILABLE"
    assert rp["ROOF_FINISH_MATERIAL"] is None and rp["ROOF_FINISH_STATUS"] == "FINISH_CLASSIFICATION_PENDING"
    assert rp["WATERPROOFING_AREA_M2"] == rp["ROOF_AREA_ENCLOSED_M2"]


def test_the_parapet_is_plastered_both_sides_and_built_once():
    rp = rec()["ROOF_AND_PARAPET"]
    assert rp["PARAPET_HEIGHT_M"] == 1.000
    assert abs(rp["PARAPET_PLASTER_M2"] - 2 * rp["PARAPET_BLOCKWORK_M2"]) < 0.01
    assert rp["PARAPET_PAINT_M2"] == rp["PARAPET_PLASTER_M2"]


def test_structural_and_mep_are_out_of_scope_not_missing():
    s = rec()["OUT_OF_SCOPE"]
    assert s["STATUS_FOR_THOSE_TRADES"] == "OUT_OF_SCOPE_FOR_CURRENT_VALIDATION"
    assert "STRUCTURAL" in s["OUT_OF_SCOPE"] and s["DO_NOT_REQUEST"] is True


# ------------------------------------------------------------------ the schedule, still validation only
def test_the_roof_explains_a_schedule_figure_that_was_previously_unmatched():
    row = next(r for r in rec()["AREA_SCHEDULE_RECONCILIATION_V2"]["ROWS"] if r["SCHEDULE_M2"] == 494.62)
    assert row["AGREEMENT"] == "CLOSE" and abs(row["DELTA_PCT"]) < 0.15


def test_the_one_figure_that_does_not_reproduce_stays_unestablished():
    row = next(r for r in rec()["AREA_SCHEDULE_RECONCILIATION_V2"]["ROWS"] if r["SCHEDULE_M2"] == 382.16)
    assert row["AGREEMENT"] == "NOT_ESTABLISHED" and row["DELTA_M2"] != 0
    assert "No measured area was moved towards it" in rec()["AREA_SCHEDULE_RECONCILIATION_V2"]["RULE"]
