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
    # a section with NO dimension entity (Villa Q section X-X): its scaled depth stays an indication (R-T402-3). r2: this
    # is no longer the Alsenan D-D reading, which prints its depth by dimensions (see the R-T402-6 tests below)
    p = R.HeldPiece("Q-U2", None, widths=[RD(0.50, "DRAWN_EDGES")], depths=[RD(0.75, "SCALED_SECTION", "X-X")],
                    length=RD(1.50, "FACE_TO_FACE"))
    r = R.resolve(p)
    assert r["result"] == R.HELD and r["m3"] is None and r["low"] is None
    assert r["indication"] == [(0.75, "X-X")]


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
        if r["line_id"] == "L-8ea71184fff91b4357b7":  # r2: the only line settled by the drawings (section D-D printed)
            assert r["result"] == "VALUE" and float(r["value_m3"]) > 0 and r["low_m3"] == "" and r["high_m3"] == ""
            continue
        assert r["result"] in ("BOUNDED", "HELD")
        assert r["value_m3"] == ""                   # no other held line is settled by the drawings
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


# ---------------------------------------------------------------- r2: R-T402-6 dimensioned section (Villa Q section Y-Y)
#   Y-Y outline 0.30 (undimensioned, scaled) x 0.70: vertical chain 50 + 20 = 0.70 closes the outline; rounded top corner
#   printed 20 (H) and 20 (V) on a drawn arc; the plan draws the piece 0.40 wide, 2.00 m face to face:
#   round = 0.2^2 (1 - pi/4) = 0.0085841 m2 ; 0.40 x 0.70 - 0.0085841 = 0.2714159 m2 ; x 2.00 = 0.542832 m3
def test_depth_printed_by_a_dimension_chain_is_a_dimensioned_section():
    D = R.depth_from_chain([0.50, 0.20], 0.70)
    ded = R.corner_round_m2(0.20, 0.20, arc_drawn=True)
    assert D == pytest.approx(0.70) and ded == pytest.approx(0.2 ** 2 * (1 - math.pi / 4), abs=1e-8)
    p = R.HeldPiece("Q-U3", None, widths=[RD(0.40, "DRAWN_EDGES", "p1 p2")], depths=[RD(D, "DIMENSIONED_SECTION", "Y-Y")],
                    length=RD(2.00, "FACE_TO_FACE"), section_deduct_m2=ded)
    r = R.resolve(p)
    assert r["result"] == R.VALUE and r["m3"] == pytest.approx(0.542832, abs=1e-6)


def test_scaled_width_of_a_dimensioned_section_stays_inadmissible():
    # the section's scaled width 0.30 is an indication: it neither binds the width nor makes a bound with the drawn 0.40
    p = R.HeldPiece("Q-U3", None, widths=[RD(0.40, "DRAWN_EDGES"), RD(0.30, "SCALED_SECTION", "Y-Y")],
                    depths=[RD(0.70, "DIMENSIONED_SECTION", "Y-Y")], length=RD(2.00, "FACE_TO_FACE"))
    r = R.resolve(p)
    assert r["result"] == R.VALUE and r["m3"] == pytest.approx(0.40 * 0.70 * 2.00)


def test_as_per_schedule_on_a_bar_leader_is_not_no_dimension():
    assert R.is_size_note("AS PER SCH.", on_bar_leader=True) is False
    # adverse: calling the section undimensioned while its vertical dimensions are listed is refused by the chain check
    with pytest.raises(R.RefusedReading):
        R.depth_from_chain([], 0.70)                 # 'no dimension' only after listing: an empty list proves nothing
    with pytest.raises(R.RefusedReading):
        R.depth_from_chain([0.50], 0.70)             # a chain that does not close the outline is not a printed depth


@pytest.mark.parametrize("rh,rv,arc", [(None, 0.20, True), (0.20, 0.20, False), (0.20, 0.10, True), (0.0, 0.0, True)])
def test_corner_round_needs_both_printed_extents_and_a_drawn_arc(rh, rv, arc):
    with pytest.raises(R.RefusedReading):
        R.corner_round_m2(rh, rv, arc)


# ---------------------------------------------------------------- r2: R-T402-5 slab pairing as a bound
#   B5 drawn 0.30 -> schedule 0.25 (GAP), L 4.20, D 0.60, t 0.15; face A sees slab 4.20, face B an opening (0 .. 0):
#   slab strip 0.05 x 0.15 x [0, 4.20] = 0 .. 0.0315 ; net shift -0.05 x (4.20 x 0.60 - Ls x 0.15) = -0.126 .. -0.0945
def test_slab_pairing_is_a_bound_when_the_faces_differ():
    sp = R.slab_pairing_bound(0.30, 0.25, 4.20, 0.60, 0.15, [(4.20, 4.20), (0.0, 0.0)])
    assert sp["kind"] == "GAP" and not sp["point"]
    assert sp["slab_m3_low"] == pytest.approx(0.0) and sp["slab_m3_high"] == pytest.approx(0.0315)
    assert sp["total_shift_low"] == pytest.approx(-0.126) and sp["total_shift_high"] == pytest.approx(-0.0945)


def test_slab_pairing_is_a_point_only_when_both_faces_see_slab():
    sp = R.slab_pairing_bound(0.25, 0.30, 4.20, 0.60, 0.15, [(4.20, 4.20), (4.20, 4.20)])
    assert sp["point"] and sp["kind"] == "OVERLAP" and sp["slab_m3_low"] == pytest.approx(0.0315)
    assert sp["total_shift_low"] == pytest.approx(0.05 * 4.20 * 0.45)


@pytest.mark.parametrize("faces", [[(4.2, 4.2)], [(1.0, 0.5), (0, 0)], [(0, 5.0), (0, 0)], [(None, 1.0), (0, 0)]])
def test_slab_pairing_refuses_one_face_or_bad_lengths(faces):
    with pytest.raises(R.RefusedReading):
        R.slab_pairing_bound(0.30, 0.25, 4.20, 0.60, 0.15, faces)


# ---------------------------------------------------------------- r2: committed Alsenan rows
def test_alsenan_bm_gf_059_value_from_section_d_d():
    r = {x["line_id"]: x for x in _rows()}["L-8ea71184fff91b4357b7"]
    b, L = float(r["drawn_width_m"]), float(r["f2f_length_m"])
    hand = (b * 0.75 - 0.20 ** 2 * (1 - math.pi / 4)) * L          # 0.55 + 0.20 printed; round 20 / 20 printed
    assert float(r["value_m3"]) == pytest.approx(hand, abs=1e-6)
    assert float(r["value_without_round_m3"]) == pytest.approx(b * 0.75 * L, abs=1e-6)
    assert "SCHEDULE_ENVELOPE" not in r["basis"]                    # P2 (envelope 0.40 .. 1.20) withdrawn


def test_alsenan_width_rows_carry_slab_pairing_bounds():
    w = [r for r in _rows() if r["cls"] == "WIDTH"]
    assert len(w) == 7
    for r in w:
        assert " .. " in r["slab_pairing"] and " .. " in r["total_shift_schedule_minus_drawn_m3"]
    b29 = {r["line_id"]: r for r in w}["L-9e4895663f76d7f03ac9"]
    lo, hi = (float(v) for v in b29["total_shift_schedule_minus_drawn_m3"].split(" .. "))
    L = float(b29["f2f_length_m"])
    assert hi <= 0.05 * L * 0.75 + 1e-6 and lo == pytest.approx(0.05 * L * (0.75 - 0.16), abs=1e-6)


@pytest.mark.parametrize("deg,mirror", [(0, False), (37, True)])
def test_sides_reader_slab_opening_and_undetermined(deg, mirror):
    # Villa Q beam 0.30 x 4.00 on the axis; face y=0 sees a slab bar 1.0 m away over the whole length; face y=0.30 sees
    # an opening cross over x 0 .. 2.0 and, beyond, a line 0.15 m away with nothing drawn (undetermined) over x 2.0 .. 4.0
    pytest.importorskip("shapely")
    from shapely.geometry import LineString, MultiLineString
    import t402_sides as S
    a = math.radians(deg)
    f = lambda p: _rot(p, a, mirror)  # noqa: E731
    band = {"pts": [f(p) for p in [(0, 0), (4.0, 0), (4.0, 0.30), (0, 0.30)]]}
    bounds = [("NEAR", LineString([f((2.0, 0.45)), f((5, 0.45))])),
              ("S1", LineString([f((-1, -2.0)), f((5, -2.0))]))]
    cross = MultiLineString([[f((0, 0.30)), f((2.0, 2.0))], [f((0, 2.0)), f((2.0, 0.30))]])
    hulls = [(["OP1"], cross.convex_hull)]
    evid = [("BAR", LineString([f((0, -1.0)), f((4.0, -1.0))]))]
    r = S.classify("Q-X", band, {}, bounds, hulls, evid)
    faces = {k: v["length_m"] for k, v in r.items() if k in ("w-", "w+")}
    slab_face = [v for v in faces.values() if v["SLAB"] > 3.9]
    other = [v for v in faces.values() if v["SLAB"] < 0.1]
    assert len(slab_face) == 1 and len(other) == 1
    assert other[0]["OPEN"] == pytest.approx(2.0, abs=0.06) and other[0]["UNDETERMINED"] == pytest.approx(2.0, abs=0.06)
