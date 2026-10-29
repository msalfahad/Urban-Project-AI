"""T-348 rules on villa C (not the development villa). Hand calculation:

Villa C: a 1F light-well screen 2.40 m wide between two piers stands from the 1F floor +4.00 to its parapet top +7.60; the
1F roof +7.00 covers the recess behind it; the recessed wall behind is an arc r 2.00 m on the 2.40 m chord. The screen
has a rectangular opening 1.60 x 2.00 (3.200 m2), intrados 0.25 m deep along 2.00 + 1.60 + 2.00 = 5.60 m.
  screen front storey  2.40 x (7.00 - 4.00) = 7.200 gross - 3.200 = 4.000 net
  screen front parapet 2.40 x (7.60 - 7.00) = 1.440
  screen back storey   7.200 - 3.200 = 4.000 (the hole goes through both faces)
  intrados             0.25 x 5.60 = 1.400 (a reveal, not a facade face)
  recess soffit        segment r 2.00 / chord 2.40: d = sqrt(4 - 1.44) = 1.60; 4 acos(0.8) - 1.60 x 1.20 = 0.654004
  recessed wall arc    2 x 2.00 x asin(0.60) = 2.574004 m; x 3.00 = 7.722012 m2
Freelancer-style rows (one plane each, 2.50 x 3.60 = 9.000, three of them = 27.000):
  row a (front plane): drawn 7.200 + 1.440 = 8.640 + width term 0.10 x 3.60 = 0.360 -> 9.000
  row b (back plane):  drawn 7.200 + 7.722012 = 14.922012 + above-roof term 2.50 x 0.60 = 1.500
                       + width term 2.50 x 3.00 - 14.922012 = -7.422012 -> 9.000
  row c: no exterior face (9.000)                                   total 27.000, residual 0.000000
"""
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t348"))

import t348_void_faces as R  # noqa: E402

HOLE = [(0.0, 0.0), (0.0, 2.0), (1.6, 2.0), (1.6, 0.0)]


def screen():
    a = R.poly_area(HOLE)
    p = R.path_length(HOLE)
    return R.screen_faces(2.40, 4.00, 7.00, 7.60, a, a, 0.25, p, p)


def get(faces, face, band):
    return [f for f in faces if f["face"] == face and f["band"] == band][0]


def test_screen_faces_by_hand():
    f = screen()
    assert get(f, "SCREEN-FRONT", "storey")["gross"] == pytest.approx(7.2)
    assert get(f, "SCREEN-FRONT", "storey")["net_lo"] == pytest.approx(4.0)
    assert get(f, "SCREEN-BACK", "storey")["net_hi"] == pytest.approx(4.0)
    assert get(f, "SCREEN-FRONT", "parapet")["net_lo"] == pytest.approx(1.44)
    assert get(f, "SCREEN-INTRADOS", "reveal")["net_lo"] == pytest.approx(1.40)


def test_recess_soffit_and_arc_by_hand():
    assert R.segment_area(2.0, 2.4) == pytest.approx(4 * math.acos(0.8) - 1.92, abs=1e-12)
    assert R.segment_area(2.0, 2.4) == pytest.approx(0.654004, abs=1e-6)
    assert R.arc_length(2.0, 2.4) == pytest.approx(2.574004, abs=1e-6)


def test_mirror_rotation_and_units_do_not_change_the_hole():
    a = R.poly_area(HOLE)
    mirrored = [(-x, y) for x, y in HOLE]
    rot = [(-y, x) for x, y in HOLE]
    mm = [(x * 1000, y * 1000) for x, y in HOLE]
    assert R.poly_area(mirrored) == pytest.approx(a)
    assert R.poly_area(rot) == pytest.approx(a)
    assert R.poly_area(mm) / 1e6 == pytest.approx(a)


def test_classification_of_faces_round_a_void():
    assert R.classify("OPEN_AIR", 7.00, 7.00) == "EXTERIOR"        # wall round the roofed part of the court
    assert R.classify("OPEN_AIR", 7.60) == "EXTERIOR"              # wall round the open part
    assert R.classify("ROOM", 7.00) == "INTERIOR"
    assert R.classify("ROOF", 7.60) == "PARAPET-INNER"
    assert R.split_at_roof(4.0, 7.6, 7.0) == [("STOREY", 4.0, 7.0), ("PARAPET", 7.0, 7.6)]


def test_adverse_face_above_a_roof_counted_as_facade():
    with pytest.raises(R.T348Error):
        R.classify("OPEN_AIR", 7.60, roof_level=7.00)


def test_reconciliation_by_hand():
    drawn_b = 7.2 + 2.0 * 2.0 * math.asin(0.6) * 3.0
    parts = [("front drawn", 8.64), ("front width", 0.36), ("back drawn", drawn_b), ("above roof", 1.5),
             ("back width", 7.5 - drawn_b), ("no face", 9.0)]
    assert R.reconcile(27.0, parts) == 0.0
    with pytest.raises(R.T348Error):
        R.reconcile(27.0, parts[:-1])                  # parts not adding up
    with pytest.raises(R.T348Error):
        R.reconcile(27.0, parts[:-1] + [("unresolved", None)])


def test_adverse_void_face_counted_inside_and_outside():
    with pytest.raises(R.T348Error):
        R.overlap_m2([{"key": "1F/W1"}], [{"key": "1F/W1"}])
    assert R.overlap_m2([{"key": "1F/W1-room"}], [{"key": "1F/W1-court"}]) == 0.0


def test_adverse_binding():
    ledger = {"1F/A/STOREY", "1F/B/STOREY"}
    assert R.bind([{"key": "1F/A/STOREY", "bound_to": "1F/A/STOREY"}, {"key": "1F/S/FRONT", "bound_to": None}], ledger)
    with pytest.raises(R.T348Error):                   # emitted twice
        R.bind([{"key": "1F/S/FRONT", "bound_to": None}, {"key": "1F/S/FRONT", "bound_to": None}], ledger)
    with pytest.raises(R.T348Error):                   # already in the ledger, emitted as NEW
        R.bind([{"key": "1F/A/STOREY", "bound_to": None}], ledger)
    with pytest.raises(R.T348Error):                   # one ledger key bound by two faces
        R.bind([{"key": "x", "bound_to": "1F/A/STOREY"}, {"key": "y", "bound_to": "1F/A/STOREY"}], ledger)
    with pytest.raises(R.T348Error):                   # bound to a key the ledger does not hold
        R.bind([{"key": "x", "bound_to": "1F/Z/STOREY"}], ledger)


def test_adverse_freelancer_row_as_quantity_and_held_never_zero():
    with pytest.raises(R.T348Error):
        R.his_row_as_quantity("b (2.50 x 3.60)")
    with pytest.raises(R.T348Error):
        R.fill_row("1F/S/FRONT", "DRAWING-CONFIRMED", m2=9.0, source="freelancer")
    with pytest.raises(R.T348Error):
        R.fill_row("1F/S/FRONT", "HELD", m2=0.0)
    with pytest.raises(R.T348Error):
        R.fill_row("1F/S/FRONT", "DRAWING-CONFIRMED", m2=0.0)
    with pytest.raises(R.T348Error):
        R.fill_row("1F/S/FRONT", "DRAWING-CONFIRMED")
    row = R.fill_row("1F/S/FRONT", "HELD", lo=3.9, hi=4.1)
    assert row["m2"] == "" and row["lo"] == "3.900000"


def test_adverse_hole_larger_than_face_and_levels():
    with pytest.raises(R.T348Error):
        R.screen_faces(1.0, 4.0, 7.0, 7.6, 3.5, 3.5, 0.25, 5.0, 5.0)
    with pytest.raises(R.T348Error):
        R.screen_faces(2.4, 7.0, 4.0, 7.6, 1.0, 1.0, 0.25, 5.0, 5.0)
    with pytest.raises(R.T348Error):
        R.segment_area(1.0, 2.5)
