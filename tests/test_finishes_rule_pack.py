"""The QS Rule Pack (Finishes V1), as arithmetic that refuses to guess.

Nothing here measures a project. These are the owner's rules, executable
and tested, so that the measurement round that eventually uses them
starts from the pack rather than from somebody's memory of it.
"""

from __future__ import annotations

import math

import pytest

from engine import finishes_rules as fr
from engine import rule_library as rlib


@pytest.fixture(scope="module")
def library():
    return rlib.load()


PACK = ("UP-GEN-001", "UP-GEN-002", "UP-GEN-003", "UP-GEN-004",
        "UP-CER-001", "UP-CER-002", "UP-CER-003", "UP-CER-004",
        "UP-CER-005", "UP-CER-006", "UP-CER-007", "UP-CER-008",
        "UP-VOCAB-005", "UP-STAIR-010", "UP-STAIR-011", "UP-STAIR-012",
        "UP-WP-001", "UP-WP-002", "UP-WP-003", "UP-WP-004")


def test_every_rule_of_the_pack_is_in_the_library(library):
    for rule_id in PACK:
        rule = library.get(rule_id)
        assert rule is not None, rule_id
        assert rule.owner_confirmed and rule.version and rule.unit
        assert rule.unknown_behavior


def test_the_pack_is_recorded_as_truncated(library):
    note = " ".join(str(v) for v in library.notes.values())
    assert "TRUNCATED" in note.upper()


def test_the_open_questions_are_written_down():
    import json
    from pathlib import Path

    d = json.loads(Path("data/registry/OWNER_RULE_REQUESTS.json")
                   .read_text(encoding="utf-8"))
    ids = {q["id"] for q in d["open"]}
    assert {"ORR-001", "ORR-002", "ORR-003"} <= ids   # the three ellipses
    for q in d["open"]:
        assert q["question"] and q["why_it_matters"]


# ------------------------------------------------------------- ceramic

def test_skirting_is_a_run_less_its_doors():
    q = fr.skirting(24.0, door_widths_lm=[0.9, 0.8],
                    full_wall_ceramic=False)
    assert q.unit == fr.UNIT_LM
    assert q.value == pytest.approx(22.3)
    assert q.rule_id == "UP-CER-003"


def test_a_full_wall_ceramic_wet_room_takes_no_skirting():
    q = fr.skirting(24.0, door_widths_lm=[0.9], full_wall_ceramic=True)
    assert q.value == 0.0 and q.status == fr.MEASURED
    assert q.rule_id == "UP-CER-004"
    assert "RULE" in q.why


def test_a_zero_by_rule_is_not_a_zero_by_ignorance():
    known = fr.skirting(24.0, door_widths_lm=[], full_wall_ceramic=True)
    unknown = fr.skirting(24.0)
    assert known.value == 0.0 and known.status == fr.MEASURED
    assert unknown.value is None and unknown.status == fr.NOT_ESTABLISHED
    assert unknown.what_is_missing


def test_wall_ceramic_is_gross_less_openings():
    q = fr.wall_ceramic(31.5, openings_m2=4.2)
    assert q.value == pytest.approx(27.3) and q.unit == fr.UNIT_M2
    assert fr.wall_ceramic(31.5).status == fr.NOT_ESTABLISHED
    assert fr.wall_ceramic().status == fr.NOT_ESTABLISHED


def test_one_edge_takes_one_finish():
    clean = fr.edge_finish(6.4, 0.0)
    assert clean["status"] == "ONE_EDGE_ONE_FINISH"
    doubled = fr.edge_finish(6.4, 2.0, shared_lm=2.0)
    assert doubled["status"] == "DOUBLE_COUNTED_EDGE"
    assert "twice" in doubled["why"]


def test_a_floor_drain_is_counted_not_measured():
    q = fr.floor_drains(3)
    assert q.unit == fr.UNIT_PCS and q.value == 3.0


# -------------------------------------------------------------- stairs

def test_a_zigzag_skirting_follows_every_nose_and_riser():
    q = fr.zigzag_skirting([300.0] * 12, [160.0] * 12)
    assert q.value == pytest.approx((12 * 300 + 12 * 160) / 1000.0)
    # and it is LONGER than the plan run of the same flight
    assert q.value > (12 * 300) / 1000.0


def test_a_sloped_skirting_is_the_rake_not_its_shadow():
    q = fr.sloped_skirting(3600.0, 1920.0)
    assert q.value == pytest.approx(math.hypot(3600.0, 1920.0) / 1000.0)
    assert q.value > 3.6


def test_a_railing_follows_the_open_edge_only():
    q = fr.railing([4080.0])
    assert q.value == pytest.approx(4.08)
    assert "no railing" in q.why
    assert fr.railing().status == fr.NOT_ESTABLISHED


# ------------------------------------------------------- waterproofing

def test_the_upturn_is_fifteen_centimetres_of_the_run_less_its_openings():
    q = fr.upturn(12.0, openings_lm=0.9)
    assert q.value == pytest.approx((12.0 - 0.9) * 0.15)
    assert fr.UPTURN_M == 0.15


def test_the_membrane_carries_through_the_doorway():
    q = fr.wet_floor(5.4, doorway_m2=0.45)
    assert q.value == pytest.approx(5.85)
    assert q.rule_id == "UP-WP-003"
    assert "flood test" in q.why


def test_nothing_in_this_module_invents_a_dimension():
    for q in (fr.floor_ceramic(), fr.skirting(), fr.wall_ceramic(),
              fr.zigzag_skirting(), fr.sloped_skirting(), fr.railing(),
              fr.wet_floor(), fr.upturn(), fr.floor_drains()):
        assert q.status == fr.NOT_ESTABLISHED
        assert q.value is None
        assert q.what_is_missing


def test_no_quantity_here_is_a_price(library):
    for rule_id in PACK:
        rule = library.get(rule_id)
        assert "KWD" not in str(rule.value).upper()
        assert rule.rule_kind in rlib.KINDS
