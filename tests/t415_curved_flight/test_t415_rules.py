"""T-415 curved-flight concrete rules (research/agents_t415/t415_rules.py) on a hand NON-Alsenan fixture.

Villa H (hypothetical): a 90-degree curved flight, structural lane between opening edges r_in 1.000 / r_out 2.200 m,
7 DRAWN riser lines at 0, 15, ..., 90 deg (6 treads), riser 0.170 m (printed on its own section), waist not printed.
Hand figures (independent of the module's closed form):
  tread area   = 1/2 (2.2^2 - 1.0^2) x pi/12 = 1/2 x 3.84 x 0.261799 = 0.502655 m2; 6 treads = 3.015929 m2
  steps        = 1/2 x 0.170 x 3.015929 = 0.256354 m3
  waist coeff. K per tread = integral sqrt(1 + (0.17 / (r pi/12))^2) r pi/12 dr, midpoint rule 200,000 strips
               = 0.544115 m2 (x 6 = 3.264692); waist = t x K, HELD while t is not printed
  developed centreline at r 1.6 = 1.6 x pi/2 = 2.513274 m; chord = 2 x 1.6 x sin 45 = 2.262742 m (refused)
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t415"))
import t415_rules as R  # noqa: E402

RI, RO, RISE = 1.0, 2.2, 0.17
ANGLES = [0, 15, 30, 45, 60, 75, 90]


def _midpoint_k(ri, ro, d, rise, n=200000):
    h = (ro - ri) / n
    return sum(math.sqrt(1 + (rise / ((ri + (i + .5) * h) * d)) ** 2) * (ri + (i + .5) * h) * d * h for i in range(n))


def _flight(angles=ANGLES):
    fp = R.FlightPieces(rise=RISE, rise_status="DRAWING-CONFIRMED")
    for t in R.treads_from_riser_angles(angles, RI, RO, RISE, "CURVED"):
        fp.add(t)
    return fp


# ---------------------------------------------------------------------------------------------------- normal case

def test_tread_areas_and_steps_hand():
    fp = _flight()
    assert len(fp.treads) == 6
    for t in fp.treads:
        assert t.area == pytest.approx(0.502655, abs=1e-6)
    assert fp.area() == pytest.approx(3.015929, abs=1e-6)
    assert fp.steps_m3() == pytest.approx(0.256354, abs=1e-6)


def test_waist_coefficient_closed_form_matches_independent_integration():
    k = R.annular_waist_coefficient(RI, RO, math.pi / 12, RISE)
    assert k == pytest.approx(0.544115, abs=1e-6)
    assert k == pytest.approx(_midpoint_k(RI, RO, math.pi / 12, RISE), abs=1e-8)
    assert _flight().k_waist() == pytest.approx(3.264692, abs=1e-5)
    # the slope differs with the radius: one secant at the centreline is NOT the waist coefficient
    g_mid = 1.6 * math.pi / 12
    one_secant = 0.502655 * math.sqrt(1 + (RISE / g_mid) ** 2)
    assert abs(one_secant - k) > 1e-3


def test_developed_length_not_chord():
    assert R.resolve_curved_length(2.513274, 1.6, math.pi / 2) == pytest.approx(2.513274, abs=1e-6)


def test_rotation_and_mirror_invariant():
    base = _flight()
    rot = _flight([a + 37.0 for a in ANGLES])
    mir = _flight(sorted(-a for a in ANGLES))  # clockwise flight, walked in ascending angle order
    for f in (rot, mir):
        assert f.area() == pytest.approx(base.area(), abs=1e-9)
        assert f.steps_m3() == pytest.approx(base.steps_m3(), abs=1e-9)
        assert f.k_waist() == pytest.approx(base.k_waist(), abs=1e-9)


def test_bound_at_least_steps_when_reinforcement_printed():
    b = R.curved_flight_bound(0.256354, reinforcement_printed=True)
    assert b == dict(kind="AT_LEAST", low=0.256354, high=None)
    assert R.curved_flight_bound(0.256354, reinforcement_printed=False)["kind"] == "UNBOUNDED"


def test_plate_row_decomposition_closes_and_keeps_held_held():
    pieces = [dict(id="straight", area=3.6, m3=0.94), dict(id="landing", area=1.44, m3=0.2304),
              dict(id="curved", area=3.015929, m3=None)]
    rec = R.decompose_plate_row(1.2, 10.0, 0.28, pieces)
    kinds = {t["id"]: t["kind"] for t in rec["terms"]}
    assert kinds["curved"] == "HELD_BINDING" and kinds["landing"] == "THICKNESS_BASIS"
    assert rec["residual"] == pytest.approx(0.94 + 0.2304 - 1.2 * 10.0 * 0.28, abs=1e-12)
    assert sum(t["m3"] for t in rec["terms"]) == pytest.approx(rec["residual"], abs=1e-12)
    beyond = [t for t in rec["terms"] if t["kind"] == "AREA_BEYOND_DRAWN"][0]
    assert beyond["area"] == pytest.approx(12.0 - 3.6 - 1.44 - 3.015929, abs=1e-9)


# ---------------------------------------------------------------------------------------------------- adverse cases

def test_chord_length_refused():
    with pytest.raises(R.CurvedLengthError):
        R.resolve_curved_length(2.262742, 1.6, math.pi / 2)


def test_steps_counted_twice_refused():
    fp = _flight()
    junction = R.Tread("L6", "S1", 0.36, 0.40, "STRAIGHT")
    fp.add(junction)
    with pytest.raises(R.StepsTwiceError):
        fp.add(R.Tread("L6", "S1", 0.36, 0.40, "CURVED"))  # the junction tread offered to the curve too
    with pytest.raises(R.StepsTwiceError):
        fp.add(R.Tread("S1", "L6", 0.36, 0.40, "CURVED"))  # same tread, ids reversed
    with pytest.raises(R.StepsTwiceError):
        R.plate_equivalent_check(steps_separately=True, plate_thickness_includes_steps=True)


def test_undrawn_winder_refused():
    with pytest.raises(R.UndrawnWinderError):
        R.subdivide_undrawn(90.0, 6)
    fp = _flight()
    with pytest.raises(R.UndrawnWinderError):
        fp.add(R.Tread("A", "B", 0.5, 0.55, "CURVED", drawn=False))
    with pytest.raises(R.UndrawnWinderError):
        R.treads_from_riser_angles([0.0], RI, RO, RISE, "CURVED")


def test_waist_held_never_zero_and_never_borrowed():
    v, st = R.waist_m3(3.264692, None, None, "VILLA-H-CURVED")
    assert v is None and st == "HELD"
    with pytest.raises(R.BorrowedThicknessError):
        R.waist_m3(3.264692, 0.16, "VILLA-H-STRAIGHT", "VILLA-H-CURVED")
    v, st = R.waist_m3(3.264692, 0.15, "VILLA-H-CURVED", "VILLA-H-CURVED")
    assert st == "CALCULATED" and v == pytest.approx(0.489704, abs=1e-6)


def test_units_and_missing_riser():
    with pytest.raises(ValueError):
        R.annular_area(1000.0, 2200.0, math.pi / 12)  # millimetres read as metres
    with pytest.raises(ValueError):
        R.treads_from_riser_angles(ANGLES, RI, RO, None, "CURVED")
    with pytest.raises(ValueError):
        R.treads_from_riser_angles(list(reversed(ANGLES)), RI, RO, RISE, "CURVED")
