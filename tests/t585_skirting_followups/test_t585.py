"""T-585 skirting follow-ups (R-T585-1): non-Alsenan hand fixtures, adverse cases, and the development-villa build
pinned (byte-identical rebuild, closures, no coordinate committed)."""
from __future__ import annotations

import importlib.util
import json
import math
import re
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t585"
sys.path.insert(0, str(HERE))
R = importlib.import_module("t585_rules")
_spec = importlib.util.spec_from_file_location("t585_alsenan", HERE / "t585_alsenan.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
D = Decimal


# ---- stairs: hand fixture (not Alsenan) -------------------------------------------------------------------------------
def test_flight_one_wall_side_pitch():
    lines = R.flight_sides("3.00", "1.80", ("WALL", "OPEN"))
    assert len(lines) == 1
    assert lines[0]["pitch"].quantize(D("0.001")) == D("3.499")            # hypot(3.00, 1.80) = 3.49857
    assert lines[0]["zigzag"] == D("4.80")                                  # other form, beside, never added


def test_flight_both_sides_only_when_both_walls_and_mm_mirror():
    two = R.flight_sides("3000", "1800", ("WALL", "WALL"), unit="mm")
    assert [x["pitch"].quantize(D("0.001")) for x in two] == [D("3.499"), D("3.499")]
    assert R.flight_sides("3.00", "1.80", ("OPEN", "WALL"))[0]["pitch"] == R.flight_sides("3.00", "1.80", ("WALL",))[0]["pitch"]
    assert R.flight_sides("3.00", "1.80", ("OPEN", "OPEN")) == []


def test_winder_bound_is_convex_end_point():
    lo, hi = R.winder_bound("1.00", "1.00", "1.00")
    assert lo == D("2.00")
    assert abs(hi - D(math.sqrt(2) + 1)) < D("1e-12")


def test_flights_total_two_forms_never_added_held_bounded():
    t = R.flights_total([{"pid": "A", "status": "HELD-FORM", "pitch": "3.498571", "zigzag": "4.80"},
                         {"pid": "B", "status": "HELD", "pitch": "1.00", "cause": "window"},
                         {"pid": "C", "status": "UNKNOWN", "pitch": None, "cause": "no wall"}])
    assert t["pitch_lm"] == D("3.498571") and t["zigzag_lm"] == D("4.80")
    assert t["lo"] == D("3.498571") and t["hi"] is None                     # unknown stays unbounded, never 0


# ---- yard: hand fixture (not Alsenan) ---------------------------------------------------------------------------------
def test_yard_printed_base_and_not_in_drawing():
    faces = [{"id": "Y1", "length": "10.00", "host": "WALL", "finish": "ESTABLISHED", "base_note": "sheet A-5 note 3"},
             {"id": "Y2", "length": "10.00", "host": "FENCE", "finish": "ESTABLISHED", "base_note": None}]
    t = R.yard_totals(faces)
    assert t["drawing_confirmed_lm"] == D("10.00")
    y2 = t["rows"][1]
    assert y2["class"] == "NOT_IN_DRAWING" and y2["measured"] == 0 and y2["physical"] == D("10.00")
    assert t["not_in_drawing_physical_lm"] == D("10.00")


def test_yard_held_finish_is_unresolved_not_zero():
    t = R.yard_totals([{"id": "P1", "length": "2.80", "host": "WALL", "finish": "HELD"}])
    r = t["rows"][0]
    assert r["class"] == "UNRESOLVED" and r["measured"] is None and r["hi"] == D("2.80")
    with pytest.raises(R.RuleError):
        R.D(r["measured"])                                                   # HELD never becomes a number


def test_yard_openings_and_glazing_have_no_face():
    for host in ("DOOR", "GATE", "OPEN_EDGE", "FLOOR_GLAZING"):
        r = R.classify_face({"id": host, "length": "1.0", "host": host, "finish": "ESTABLISHED"})
        assert r["class"] == "NO_FACE" and r["measured"] == 0


def test_yard_sill_window_with_note_is_a_range():
    r = R.classify_face({"id": "S", "length": "1.50", "host": "SILL_WINDOW", "finish": "ESTABLISHED", "base_note": "n"})
    assert r["class"] == "DRAWING-CONFIRMED" and r["measured"] is None and (r["lo"], r["hi"]) == (0, D("1.50"))


# ---- adverse ------------------------------------------------------------------------------------------------------------
def test_adverse_face_without_a_finished_floor_refused():
    with pytest.raises(R.RuleError, match="no finished floor"):
        R.classify_face({"id": "X", "length": "5.0", "host": "FENCE", "finish": "NONE", "base_note": "note"})


def test_adverse_pieces_to_lm_without_printed_length_refused():
    with pytest.raises(R.RuleError, match="printed piece length"):
        R.pieces_to_lm(96)
    assert R.pieces_to_lm(5, "300", unit="mm") == D("1.5")
    with pytest.raises(R.RuleError):
        R.pieces_to_lm("2.5", "0.30")


@pytest.mark.parametrize("face,msg", [
    ({"id": "a", "length": "1", "host": "DOOR", "finish": "ESTABLISHED", "claimed": "DRAWING-CONFIRMED"}, "never skirted"),
    ({"id": "b", "length": "1", "host": "WALL", "finish": "ESTABLISHED", "claimed": "DRAWING-CONFIRMED"}, "no base"),
    ({"id": "c", "length": "1", "host": "WALL", "finish": "HELD", "claimed": "DRAWING-CONFIRMED"}, "HELD"),
    ({"id": "d", "length": "1", "host": "WALL", "finish": "ESTABLISHED", "claimed": "VERIFIED"}, "Checker"),
    ({"id": "e", "length": "-1", "host": "WALL", "finish": "ESTABLISHED"}, "negative"),
    ({"id": "f", "length": "1", "host": "ROOF", "finish": "ESTABLISHED"}, "unknown"),
])
def test_adverse_face_claims(face, msg):
    with pytest.raises(R.RuleError, match=msg):
        R.classify_face(face)


def test_adverse_duplicate_face_and_pitch_over_zigzag():
    f = {"id": "Y", "length": "1", "host": "WALL", "finish": "ESTABLISHED"}
    with pytest.raises(R.RuleError, match="twice"):
        R.yard_totals([f, dict(f)])
    with pytest.raises(R.RuleError, match="exceeds"):
        R.flight_line({"pid": "Z", "status": "HELD-FORM", "pitch": "5", "zigzag": "4"})
    with pytest.raises(R.RuleError):
        R.pitch("0", "1")


# ---- development villa (pinned) ---------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def built():
    return A.build()


def test_build_byte_identical(built):
    assert A.OUT.read_text() == A.dump(built)


def test_yard_closes_and_classes(built):
    y = built["yard"]
    assert y["closure"]["yard_face_perimeter_lm"] == "98.629"
    t = y["totals_lm"]
    assert t["DRAWING-CONFIRMED"] == "0"
    assert t["NOT_IN_DRAWING_physical_wall_foot"] == "59.582"
    assert t["NOT_IN_DRAWING_under_unprinted_sills_range_hi"] == "6"
    assert t["UNRESOLVED_bound"] == ["0", "11.61"]
    assert y["reconcile"]["gap"] == "-81.32" and y["reconcile"]["pct"] is None
    assert {f["class"] for f in y["faces"] if f["zone"] in ("PO", "PC") and f["host"] in ("WALL", "FENCE")} == {"UNRESOLVED"}


def test_stairs_restated(built):
    s = built["stairs"]
    assert (s["two_form_pitch_lm"], s["two_form_zigzag_lm"]) == ("17.009049", "23.300481")
    assert s["flight_lo"] == "19.359049" and s["flight_hi"] is None          # RS-C outer band stays unbounded
    assert built["e1_landing"]["landing_lm"] == "3.5"
    assert built["e1_landing"]["flight_check"]["pitch"] == "1.470544"


def test_no_coordinate_or_workbook_text_committed():
    pat = re.compile(r"-(1[2-9]\d|2\d\d|3\d\d|7\d\d|8\d\d)\.\d{2,}")
    for p in HERE.rglob("*"):
        if p.is_file() and p.suffix in (".json", ".md", ".py", ".csv"):
            assert not pat.search(p.read_text()), p
