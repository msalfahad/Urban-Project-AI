"""T-414 on the development villa (committed table only; the private candidate run is not needed): B3-05 per room from
ARCH_TAKEOFF_V3.0.34 (json 4c7f581c), dry beds bounded by the T-214 drawn build-up, wet beds HELD on the drawing basis,
owner Q-45 ranges beside, NOT_APPLICABLE finish rows carry no bed, nothing held as 0, no double count."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t414"))
import t414_alsenan as A  # noqa: E402

HERE = ROOT / "research" / "agents_t414"


@pytest.fixture(scope="module")
def summ():
    return A.check()


@pytest.fixture(scope="module")
def rows():
    return list(csv.DictReader((HERE / "ROOM_TABLE_T414.csv").open()))


def test_bound_to_the_candidate_of_record(summ):
    assert summ["candidate"] == "ARCH_TAKEOFF_V3.0.34"
    assert summ["candidate_json_sha256"].startswith("4c7f581c") and summ["candidate_lines"] == 4690


def test_totals_pinned(summ):
    d, w = summ["totals"]["DRY"], summ["totals"]["WET"]
    assert (d["rooms_area_valued"], d["m2"], d["m3_owner_low"], d["m3_owner_high"]) == (19, 288.1458, 8.6443, 11.5258)
    assert d["m3_drawing_bound_high"] == 14.3001 and len(d["rows_not_applicable"]) == 13
    assert (w["rooms_area_valued"], w["m2"], w["m3_owner_low"], w["m3_owner_high"]) == (21, 85.5756, 3.4229, 5.1347)
    assert w["m3_drawing_bound_high"] is None and w["m3_drawing_bound_rooms"] == 0


def test_wet_rooms_held_on_the_drawing_basis_never_zero(rows):
    for r in rows:
        if r["kind"] == "WET":
            assert r["m3_drawing_status"] == "HELD" and r["m3_drawing_high"] == "" and r["build_up_b"] == ""


def test_dry_rooms_bounded_by_the_drawn_build_up(rows):
    for r in rows:
        if r["kind"] == "DRY" and r["m2_status"] != "NOT_APPLICABLE":
            b = float(r["build_up_b"])
            assert b in (0.049, 0.05) and r["owner_check"] == "CONSISTENT"
            assert float(r["m3_drawing_high"]) == pytest.approx(float(r["area_m2"]) * b, abs=1e-4)


def test_not_applicable_rows_carry_nothing(rows):
    na = [r for r in rows if r["m2_status"] == "NOT_APPLICABLE"]
    assert na and all(r["area_m2"] == "" and r["m3_owner_low"] == "" for r in na)


def test_kitchen_is_a_wet_bed_and_the_open_room_stays_dry(rows):
    by = {r["element_id"]: r for r in rows}
    assert by["GF-RA3AD49:floor"]["kind"] == "WET" and by["GF-RA3AD49:floor"]["membrane_in_room"] == "WHOLE"
    assert by["GF-RC99C2A:floor"]["kind"] == "DRY" and by["GF-RC99C2A:floor"]["membrane_in_room"].startswith("PART")


def test_one_layer_one_item(summ):
    assert summ["double_counted"] == []
    assert all(fam.startswith("B8-0") for fam, _ in summ["other_layer_lines_on_b3_05_rooms"])
    assert set(summ["owned_elsewhere_lines"]) <= {"ROOF", "STAIR", "OUTDOOR_GROUND", "POOL", "FOUNDATION"}


def test_freelancer_has_no_bed_row(summ):
    assert summ["freelancer"]["screed_or_bed_rows"] == 0
    assert summ["totals"]["WET"]["m2"] - summ["freelancer"]["tiled_floor_rows_m2"]["wet_areas"] == pytest.approx(
        13.4550 + 0.1106, abs=1e-3)   # pantry (Q-37 A, no freelancer row) + T-074 wet rooms (+0.16 %)


def test_summary_is_json_stable():
    s = (HERE / "summary.json").read_text()
    assert json.loads(s)["rows"] == 53
