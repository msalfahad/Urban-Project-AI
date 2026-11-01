"""T-417 rules on a hand fixture that is NOT Alsenan: Villa D417, a dog-leg stair, storey A 20 risers x 0.17
(two flights of 10), storey B 10 risers x 0.16 per flight, going 0.28, lane 1.10, printed waist 0.15, run 9 x 0.28
= 2.52 m (first to last riser line). Hand figures (independent of the rules module):
  sec = hypot(0.17, 0.28) / 0.28 = 1.169881; steps 10 x 1/2 x 0.17 x 0.28 x 1.10 = 0.261800 m3;
  waist 2.52 x 1.169881 x 0.15 x 1.10 = 0.486437 m3; developed profile 2.52 + 10 x 0.17 = 4.22 m (B: 4.12 m);
  a freelancer row 1.10 x 4.22 x 0.25: RISE_IN_LENGTH -1.70 x 1.10 x 0.25 = -0.467500 (A);
  on B: -1.60 x 0.275 = -0.440000 + ONE_LENGTH -(4.22 - 4.12) x 0.275 = -0.027500;
  column 0.05 proud over s 0.50 .. 1.00 of flight A: 0.05 x (0.5 x 0.15 x 1.169881 + 0.044321) = 0.006603 m3
  (saw-tooth by a 200 000-point midpoint sum, 0.044321).
"""

import importlib.util
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t417_rules", ROOT / "research" / "agents_t417" / "t417_rules.py")
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)

SIB = [{"id": "A1", "row": "flights", "run": 2.52, "n": 10, "riser": 0.17},
       {"id": "B1", "row": "flights", "run": 2.52, "n": 10, "riser": 0.16}]


def test_flight_hand_figures():
    f = R.flight(10, 0.17, 0.28, 1.10, 2.52, 0.15)
    assert f["steps_m3"] == pytest.approx(0.261800, abs=1e-6)
    assert f["waist_m3"] == pytest.approx(0.486437, abs=1e-6)
    assert f["sec"] == pytest.approx(1.169881, abs=1e-6)
    assert f["inclined_m"] == pytest.approx(2.52 * 1.169881, abs=1e-5)
    assert f["profile_m"] == pytest.approx(4.22, abs=1e-9)


def test_waist_never_on_plan_or_developed_length():
    for basis in ("PLAN", "DEVELOPED"):
        with pytest.raises(R.Refused):
            R.flight(10, 0.17, 0.28, 1.10, 2.52, 0.15, length_basis=basis)


def test_unprinted_waist_is_held_not_zero():
    f = R.flight(10, 0.17, 0.28, 1.10, 2.52, None)
    assert f["state"] == "HELD" and f["waist_m3"] is None and f["gross_m3"] is None
    assert f["steps_m3"] == pytest.approx(0.2618, abs=1e-6)


def test_slab_plus_steps_on_developed_profile_refused():
    with pytest.raises(R.Refused):
        R.engine_plate(True, "DEVELOPED", 2.52, 10, 0.17, 1.10, 0.25)
    assert R.engine_plate(True, "PLAN", 2.52, 10, 0.17, 1.10, 0.25) == pytest.approx(0.693, abs=1e-9)


def test_length_split_own_profile():
    t = R.length_terms("A1", "flights", 4.22, 1.10, 0.25, 2.52, 10, 0.17, SIB)
    d = {x["term"]: x for x in t}
    assert d["RISE_IN_LENGTH"]["m3"] == pytest.approx(-0.4675, abs=1e-6) and d["RISE_IN_LENGTH"]["traced"]
    assert d["ONE_LENGTH"]["m3"] == pytest.approx(0.0, abs=1e-9)
    assert sum(x["m3"] for x in t) == pytest.approx(-(4.22 - 2.52) * 1.10 * 0.25, abs=1e-6)


def test_length_split_one_length_for_two_flights():
    t = R.length_terms("B1", "flights", 4.22, 1.10, 0.25, 2.52, 10, 0.16, SIB)
    d = {x["term"]: x for x in t}
    assert d["RISE_IN_LENGTH"]["m3"] == pytest.approx(-0.44, abs=1e-6)
    assert d["ONE_LENGTH"]["m3"] == pytest.approx(-0.0275, abs=1e-6) and d["ONE_LENGTH"]["traced"]
    # sibling order does not matter
    t2 = R.length_terms("B1", "flights", 4.22, 1.10, 0.25, 2.52, 10, 0.16, list(reversed(SIB)))
    assert [x["m3"] for x in t2] == [x["m3"] for x in t]


def test_untraced_length_stays_untraced_whole():
    t = R.length_terms("A1", "flights", 4.30, 1.10, 0.25, 2.52, 10, 0.17, SIB)
    assert len(t) == 1 and t[0]["term"] == "LENGTH" and not t[0]["traced"]
    assert t[0]["m3"] == pytest.approx(-(4.30 - 2.52) * 0.275, abs=1e-6)


def test_sibling_from_another_row_refused():
    sib = [{"id": "X", "row": "landings", "run": 2.62, "n": 10, "riser": 0.16}]
    with pytest.raises(R.Refused):
        R.length_terms("B1", "flights", 4.22, 1.10, 0.25, 2.52, 10, 0.16, sib)   # X: 2.62 + 1.60 = 4.22


def test_borrowed_riser_refused_and_mm_as_m_refused():
    with pytest.raises(R.Refused):
        R.borrowed_check("B1", "A1")
    assert R.borrowed_check("A1", "A1")
    with pytest.raises(R.Refused):
        R.flight(10, 0.17, 0.28, 1.10, 2520, 0.15)
    with pytest.raises(R.Refused):
        R.flight(10.0, 0.17, 0.28, 1.10, 2.52, 0.15)
    with pytest.raises(R.Refused):
        R.flight(10, None, 0.28, 1.10, 2.52, 0.15)


def test_landing_depth_band_is_the_beams():
    band = [{"id": "BB", "width": 0.20, "owner": "BEAM"}]
    t = R.landing_depth_terms("LD", 1.30, 1.10, 1.10, 1.10, 0.15, band)
    assert len(t) == 1 and t[0]["term"] == "OWNERSHIP" and t[0]["traced"]
    assert t[0]["m3"] == pytest.approx(-0.20 * 1.10 * 0.15, abs=1e-9)
    with pytest.raises(R.Refused):
        R.landing_depth_terms("LD", 1.30, 1.10, 1.10, 1.10, 0.15, [{"id": "BB", "width": 0.20, "owner": "STAIR"}])
    u = R.landing_depth_terms("LD", 1.25, 1.10, 1.10, 1.10, 0.15, band)
    assert len(u) == 1 and u[0]["term"] == "AREA" and not u[0]["traced"]
    c = R.unbound_plate_term("LD2", 1.21, 0.15)
    assert c["term"] == "COUNT" and c["m3"] == pytest.approx(0.1815, abs=1e-9)


def test_projection_exposure_hand():
    e = R.projection_exposure(0.05, 0.50, 1.00, 0.17, 0.28, 0.15, 10, 2.52)
    assert e == pytest.approx(0.006603, abs=1e-6)
    d = R.projection_deduction(e, "CONFLICT")
    assert d["state"] == "HELD" and d["low"] == 0.0 and d["high"] == e and d["in_flight_value"]
    assert R.projection_deduction(e, "DRAWN_CONFIRMED")["m3"] == e
    assert R.projection_deduction(0.0, "FLUSH")["m3"] == 0.0
    with pytest.raises(R.Refused):
        R.projection_exposure(0.05, 2.30, 2.80, 0.17, 0.28, 0.15, 10, 2.52)      # beyond the run
    with pytest.raises(R.Refused):
        R.projection_exposure(1.20, 0.50, 1.00, 0.17, 0.28, 0.15, 10, 2.52)      # across the lane
    with pytest.raises(R.Refused):
        R.projection_deduction(e, "GUESS")


def test_sawtooth_full_goings_equal_half_riser():
    # over whole goings the saw-tooth averages r / 2 (= the step triangles), at any start on a going boundary
    for k in range(4):
        s0 = k * 0.28
        assert R.sawtooth_integral(s0, s0 + 3 * 0.28, 0.17, 0.28) == pytest.approx(3 * 0.5 * 0.17 * 0.28, abs=1e-12)
    assert math.isclose(R.sawtooth_integral(0.1, 0.1, 0.17, 0.28), 0.0, abs_tol=1e-15)


def test_closure_refuses_a_gap():
    with pytest.raises(R.Refused):
        R.closure(-1.0, [{"term": "LENGTH", "m3": -0.9, "traced": False}])
    c = R.closure(-1.0, [{"term": "LENGTH", "m3": -0.9, "traced": False}, {"term": "WIDTH", "m3": -0.1,
                                                                          "traced": True}])
    assert c["untraced_m3"] == pytest.approx(-0.9) and c["traced_m3"] == pytest.approx(-0.1)
