"""T-402 held beam lines resolved one by one: hand NON-Alsenan fixture 'Villa Q' (normal + adverse) and checks on the
committed Alsenan table. Hand values (metres, m3):

  B5 schedule 0.25 x 0.60, drawn 0.30, face to face 4.20 between two 0.30 columns (axis span 4.50):
      drawn 0.30 x 0.60 x 4.20 = 0.756 ; schedule 0.25 x 0.60 x 4.20 = 0.630  -> BOUNDED 0.630 .. 0.756
      slab t 0.15: strip 0.05 x 4.20 x 0.15 = 0.0315 (GAP at 0.25, OVERLAP the other way); total shift 0.05 x 4.20 x 0.45 = 0.0945
  B5 drawn 0.25 = schedule 0.25: VALUE 0.630
  unlabelled 1.20 m piece past the column, drawn 0.20, set depths 0.40 .. 0.90: HELD, bound 0.096 .. 0.216, no value
  two marks on one 2.00 m span, 0.20 wide, rows 0.40 / 0.75: BOUNDED 0.160 .. 0.300
  edge projection 0.20 x 3.00: HELD, plan area 0.600 m2, no m3 bound
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t402"))
import t402_rules as R  # noqa: E402

RD = R.Reading


def b5(drawn=0.30, length=RD(4.20, "FACE_TO_FACE")):
    return R.HeldPiece("Q-B5", "B5", widths=[RD(0.25, "SCHEDULE_ROW", "B5"), RD(drawn, "DRAWN_EDGES", "h1 h2")],
                       depths=[RD(0.60, "SCHEDULE_ROW", "B5")], length=length)


# ---------------------------------------------------------------- normal cases
def test_width_conflict_is_bounded_by_the_two_readings_only():
    r = R.resolve(b5())
    assert r["result"] == R.BOUNDED and r["m3"] is None
    assert r["low"] == pytest.approx(0.630, abs=1e-9) and r["high"] == pytest.approx(0.756, abs=1e-9)


def test_agreeing_schedule_and_drawing_give_a_value():
    r = R.resolve(b5(drawn=0.25))
    assert r["result"] == R.VALUE and r["m3"] == pytest.approx(0.630, abs=1e-9)


def test_two_marks_bounded():
    p = R.HeldPiece("Q-CB1", "CB1|B2", widths=[RD(0.20, "SCHEDULE_ROW", "CB1"), RD(0.20, "DRAWN_EDGES")],
                    depths=[RD(0.40, "SCHEDULE_ROW", "B2"), RD(0.75, "SCHEDULE_ROW", "CB1")], length=RD(2.0, "FACE_TO_FACE"))
    r = R.resolve(p)
    assert r["result"] == R.BOUNDED and (r["low"], r["high"]) == (pytest.approx(0.16), pytest.approx(0.30))


def test_unlabelled_piece_held_with_labelled_envelope_bound():
    p = R.HeldPiece("Q-U1", None, widths=[RD(0.20, "DRAWN_EDGES")],
                    depths=[RD(0.40, "SCHEDULE_ENVELOPE"), RD(0.90, "SCHEDULE_ENVELOPE")], length=RD(1.20, "FACE_TO_FACE"))
    r = R.resolve(p)
    assert r["result"] == R.HELD and r["m3"] is None
    assert (r["low"], r["high"]) == (pytest.approx(0.096), pytest.approx(0.216))
    assert "SCHEDULE_ENVELOPE" in r["basis"]


def test_projection_plan_area_only():
    p = R.HeldPiece("Q-P1", None, widths=[RD(0.20, "DRAWN_EDGES")],
                    depths=[RD(0.40, "SCHEDULE_ENVELOPE"), RD(1.20, "SCHEDULE_ENVELOPE")],
                    length=RD(3.0, "FACE_TO_FACE"), projection=True, plan_area_m2=0.60)
    r = R.resolve(p)
    assert r["result"] == R.HELD and r["m3"] is None and r["low"] is None and r["high"] is None
    assert r["plan_area_m2"] == pytest.approx(0.60)


def test_slab_pairing_both_directions():
    g = R.slab_pairing(0.30, 0.25, 4.20, 0.15)
    o = R.slab_pairing(0.25, 0.30, 4.20, 0.15)
    assert g == {"kind": "GAP", "slab_m3": pytest.approx(0.0315)}
    assert o == {"kind": "OVERLAP", "slab_m3": pytest.approx(0.0315)}
    # total concrete moves by db x L x (D - t) only: beam bound difference minus the slab strip
    r = R.resolve(b5())
    assert (r["high"] - r["low"]) - g["slab_m3"] == pytest.approx(0.05 * 4.20 * (0.60 - 0.15))


# ---------------------------------------------------------------- adverse cases
def test_centre_line_span_refused():
    with pytest.raises(R.RefusedReading):
        R.resolve(b5(length=RD(4.50, "CENTRE_LINE")))


def test_section_borrowed_from_neighbour_refused():
    p = R.HeldPiece("Q-U1", None, widths=[RD(0.20, "DRAWN_EDGES")], depths=[RD(0.60, "NEIGHBOUR_MARK", "B5")],
                    length=RD(1.20, "FACE_TO_FACE"))
    with pytest.raises(R.RefusedReading):
        R.resolve(p)


def test_schedule_row_on_an_unlabelled_piece_refused():
    p = R.HeldPiece("Q-U1", None, widths=[RD(0.25, "SCHEDULE_ROW", "B5")], depths=[RD(0.60, "SCHEDULE_ROW", "B5")],
                    length=RD(1.20, "FACE_TO_FACE"))
    with pytest.raises(R.RefusedReading):
        R.resolve(p)


def test_scaled_section_is_never_a_value():
    p = R.HeldPiece("Q-U2", None, widths=[RD(0.50, "DRAWN_EDGES")], depths=[RD(0.75, "SCALED_SECTION", "D-D")],
                    length=RD(1.50, "FACE_TO_FACE"))
    r = R.resolve(p)
    assert r["result"] == R.HELD and r["m3"] is None and r["low"] is None
    assert r["indication"] == [(0.75, "D-D")]


@pytest.mark.parametrize("bad", [0.0, -0.2])
def test_held_as_zero_refused(bad):
    with pytest.raises(R.RefusedReading):
        R.refuse_zero(0)
    with pytest.raises(R.RefusedReading):
        R.resolve(R.HeldPiece("Q", "B5", widths=[RD(bad, "DRAWN_EDGES")], depths=[RD(0.6, "SCHEDULE_ROW")],
                              length=RD(4.2, "FACE_TO_FACE")))
    R.refuse_zero(None)


def test_missing_length_is_held_never_zero():
    with pytest.raises(R.RefusedReading):
        R.resolve(b5(length=None))


# ---------------------------------------------------------------- reader geometry: rotation, mirror, off-parallel
def _rot(p, a, mirror=False):
    x, y = p
    if mirror:
        x = -x
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


@pytest.mark.parametrize("deg,mirror", [(0, False), (30, False), (98.5, True), (-45, True)])
def test_reader_width_under_rotation_and_mirror(deg, mirror):
    pytest.importorskip("shapely")
    import t402_read as RR
    a = math.radians(deg)
    band = {"pts": [_rot(p, a, mirror) for p in [(0, 0), (4.2, 0), (4.2, 0.30), (0, 0.30)]], "title": "B5 BOUND"}
    lines = [("E1", "1", _rot((-0.3, 0.0), a, mirror), _rot((4.5, 0.0), a, mirror)),
             ("E2", "1", _rot((-0.3, 0.30), a, mirror), _rot((4.5, 0.30), a, mirror)),
             ("SKEW", "1", _rot((0, 0.15), a, mirror), _rot((4.2, 0.15 + 4.2 * math.tan(math.radians(0.6))), a, mirror)),
             ("FAR", "1", _rot((0, 0.60), a, mirror), _rot((4.2, 0.60), a, mirror))]
    r = RR.measure(band, lines, [], [], [])
    assert r["drawn_width_m"] == pytest.approx(0.30, abs=1e-4)
    hs = {f["handle"] for f in r["faces"]}
    assert hs == {"E1", "E2"}                       # 0.6 deg off-parallel and the far line are not faces
    assert all(f["clipped_m"] == pytest.approx(4.2, abs=1e-4) for f in r["faces"])


# ---------------------------------------------------------------- committed Alsenan table (no private input)
def _rows():
    return list(csv.DictReader((ROOT / "research" / "agents_t402" / "HELD_LINES_T402.csv").open(encoding="utf-8")))


def test_alsenan_table_one_row_per_held_line():
    rows = _rows()
    assert len(rows) == 27 and len({r["line_id"] for r in rows}) == 27
    fl = {}
    for r in rows:
        fl[r["floor"]] = fl.get(r["floor"], 0) + 1
    assert fl == {"GF": 10, "1F": 12, "2F": 5}


def test_alsenan_table_held_stays_blank_and_never_zero():
    for r in _rows():
        assert r["result"] in ("BOUNDED", "HELD")
        assert r["value_m3"] == ""                   # nothing valued: no held line settled by the drawings
        for k in ("low_m3", "high_m3"):
            assert r[k] == "" or float(r[k]) > 0
        if r["cls"] in ("PROJECTION", "RING"):
            assert r["low_m3"] == "" and r["high_m3"] == "" and float(r["plan_area_m2"]) > 0
        if r["result"] == "BOUNDED":
            assert float(r["low_m3"]) < float(r["high_m3"])
        assert r["missing_fact"]


def test_alsenan_width_bounds_rederive_by_hand():
    w = {r["line_id"]: r for r in _rows() if r["cls"] == "WIDTH"}
    cb2 = w["L-2c7b0b1e1a439d9ffd1e"]            # CB2 span 1: schedule 0.20 / drawn 0.2502, D 0.50, L 3.4692
    assert float(cb2["low_m3"]) == pytest.approx(0.20 * 0.50 * float(cb2["f2f_length_m"]), abs=1e-6)
    assert float(cb2["high_m3"]) == pytest.approx(float(cb2["drawn_width_m"]) * 0.50 * float(cb2["f2f_length_m"]), abs=1e-6)
    for r in w.values():                          # agrees with the candidate's bound within 1 mm of width / length
        assert abs(float(r["low_m3"]) - float(r["cand_low"])) < 0.001
        assert abs(float(r["high_m3"]) - float(r["cand_high"])) < 0.001
