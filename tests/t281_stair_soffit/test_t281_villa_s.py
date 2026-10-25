"""T-281 STAIR_SOFFIT_V1 on a hand-calculated fixture that is NOT the development villa (Villa S), plus adverse cases.

Villa S (synthetic): riser 0.16 m, going 0.30 m (hypot = 0.34 exactly, sec = 1.133333), waist 0.15 m.
  L-stair: F1 8 riser lines from the ground slab, lane 1.10 -> quarter landing QL 1.10 x 1.10 (t 0.15, a 0.20 x 0.20
  column in its far corner) -> F2 12 riser lines, head on a 0.60 deep beam whose face is 0.15 before the last riser line.
  Dog-leg: F3 10 riser lines from the ground slab -> half landing HL 1.20 x 2.30 (two lanes 1.10 + well 0.10) -> F4.
Hand calculation (method O = riser line to riser line; method D = physical soffit planes):
  F1  O plan 7 x 0.30 x 1.10 = 2.31, true 2.31 x 1.133333 = 2.618
      D ground kink (0.30 / 0.16) x 0.15 x 1.133333 = 0.31875 -> slab-borne 0.350625, sloped 1.78125 x 1.10 = 1.959375,
        true 2.220625; head kink 0.30 + 1.875 x (0.17 - 0.15) = 0.3375 -> 0.37125 m2 inside QL, true 0.42075
  QL  O 1.21 - 0.04 = 1.17; D 1.17 - 0.37125 = 0.79875
  F2  O plan (3.30 - 0.15) x 1.10 = 3.465, true 3.927; D foot kink 1.875 x 0.02 = 0.0375 flat 0.04125 + sloped
        3.1125 x 1.10 = 3.42375 x 1.133333 = 3.88025 -> 3.9215; beam check 1.92 - 0.533333 x 3.15 + 0.17 = 0.41 <= 0.60
  totals plan 6.945 both; true O 7.715, true D 7.361625 (+ 0.350625 slab-borne, no soffit)
  HL  O 2.76; D 2.76 - F3's kink 0.37125 = 2.38875 (F4's foot kink stays inside F4)."""

import importlib.util
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("t281_stair_soffit", ROOT / "research" / "agents_t281" / "t281_stair_soffit.py")
S = importlib.util.module_from_spec(_s)
sys.modules.setdefault("t281_stair_soffit", S)
_s.loader.exec_module(S)

PR = "PRINTED"
SEC = 0.34 / 0.30


def flight(id_, n, foot, head, w=1.10, r=0.16, rs=PR, t=0.15, ts="PRINTED waist 150"):
    return {"id": id_, "n": n, "g": 0.30, "w": w, "r": r, "r_source": rs, "t": t, "t_source": ts, "foot": foot,
            "head": head, "status": "DRAWING-CONFIRMED", "below": "hall", "src": "fixture"}


F1 = flight("F1", 8, {"type": "ground"}, {"type": "plate", "t": 0.15, "room": 1.10})
F2 = flight("F2", 12, {"type": "plate", "t": 0.15}, {"type": "beam_face", "offset_before_last": 0.15, "depth": 0.60})
QL = {"id": "QL", "length": 1.10, "width": 1.10, "subs": [("column", "NO_SOFFIT", (0.90, 1.10, 0.90, 1.10))],
      "status": "DRAWING-CONFIRMED", "below": "hall", "src": "fixture"}


def lstair():
    r1, l1 = S.flight_rows(F1)
    k1, kd = S.kink_rows(F1, l1, QL["length"], QL["width"], QL["subs"])
    q = S.landing_rows(QL, [kd])
    r2, l2 = S.flight_rows(F2)
    return {r["id"]: r for r in r1 + k1 + q + r2}


def test_l_stair_hand_calculation_method_o():
    r = lstair()
    assert r["F1"]["plan_O"] == pytest.approx(2.31, abs=1e-9)
    assert r["F1"]["true_O"] == pytest.approx(2.618, abs=1e-9)
    assert r["QL"]["plan_O"] == pytest.approx(1.17, abs=1e-9) and r["QL"]["true_O"] == pytest.approx(1.17, abs=1e-9)
    assert r["F2"]["plan_O"] == pytest.approx(3.465, abs=1e-9)
    assert r["F2"]["true_O"] == pytest.approx(3.927, abs=1e-9)
    assert sum(x["true_O"] for x in r.values() if x["cls"] == "STAIR_SOFFIT") == pytest.approx(7.715, abs=1e-9)


def test_l_stair_hand_calculation_method_d():
    r = lstair()
    assert r["F1"]["ground_kink_m"] == pytest.approx(0.31875, abs=1e-12)
    assert r["F1/slab-borne foot"]["plan_D"] == pytest.approx(0.350625, abs=1e-9)
    assert r["F1"]["plan_D"] == pytest.approx(1.959375, abs=1e-9)
    assert r["F1"]["true_D"] == pytest.approx(2.220625, abs=1e-9)
    assert r["F1/head kink"]["plan_D"] == pytest.approx(0.37125, abs=1e-9)
    assert r["F1/head kink"]["true_D"] == pytest.approx(0.42075, abs=1e-9)
    assert r["QL"]["plan_D"] == pytest.approx(0.79875, abs=1e-9)
    assert r["F2"]["true_D"] == pytest.approx(3.9215, abs=1e-9)
    soffit = [x for x in r.values() if x["cls"] == "STAIR_SOFFIT"]
    assert sum(x["true_D"] for x in soffit) == pytest.approx(7.361625, abs=1e-9)
    # the plan is a partition: method O and method D only move strips between rows
    assert sum(x["plan_O"] for x in r.values()) == pytest.approx(6.945 + 0.04, abs=1e-9)
    assert sum(x["plan_D"] for x in r.values()) == pytest.approx(6.945 + 0.04, abs=1e-9)


def test_dog_leg_half_landing_takes_only_the_arriving_flights_kink():
    f3 = flight("F3", 10, {"type": "ground"}, {"type": "plate", "t": 0.15, "room": 1.20})
    f4 = flight("F4", 10, {"type": "plate", "t": 0.15}, {"type": "plate", "t": 0.15, "room": 1.95})
    hl = {"id": "HL", "length": 1.20, "width": 2.30, "subs": [], "status": "DRAWING-CONFIRMED", "below": "hall",
          "src": "fixture"}
    _, l3 = S.flight_rows(f3)
    k3, kd3 = S.kink_rows(f3, l3, 1.20, 2.30, (), 0.0)
    rows4, l4 = S.flight_rows(f4)
    h = S.landing_rows(hl, [kd3])[0]
    assert h["plan_O"] == pytest.approx(2.76, abs=1e-9)
    assert h["plan_D"] == pytest.approx(2.38875, abs=1e-9)
    assert rows4[0]["foot_kink_m"] == pytest.approx(0.0375, abs=1e-12)     # F4's flat strip stays inside F4
    assert rows4[0]["plan_D"] == pytest.approx(rows4[0]["plan_O"], abs=1e-12)


def test_adverse_two_flights_claiming_one_landing_strip_refused():
    _, l1 = S.flight_rows(F1)
    _, kd = S.kink_rows(F1, l1, 1.10, 1.10)
    with pytest.raises(S.SoffitError):
        S.landing_rows(QL, [kd, dict(kd)])


def test_adverse_riser_unprinted_is_held_never_a_convention_riser():
    f = flight("Fx", 8, {"type": "ground"}, {"type": "plate", "t": 0.15}, r=None, rs=None)
    rows, lim = S.flight_rows(f)
    assert lim["sec"] is None
    assert rows[0]["true_O"] is None and rows[0]["true_D"] is None and rows[0]["plan_D"] is None
    assert rows[0]["status"] == "HELD"
    assert rows[0]["plan_O"] == pytest.approx(2.31, abs=1e-9)     # the drawn riser lines still give the plan
    t = S.totals(rows)
    assert t["true_O_held_rows"] == 1 and t["true_O_measured"] == 0.0 and t["held_plan_m2"] == pytest.approx(2.31)
    with pytest.raises(S.SoffitError):
        S.flight_rows(flight("Fc", 8, {"type": "ground"}, {"type": "plate", "t": 0.15}, r=0.165,
                             rs="CONVENTION 0.165"))


def test_adverse_waist_unprinted_holds_only_method_d():
    f = flight("Fw", 8, {"type": "ground"}, {"type": "plate", "t": 0.15}, t=None, ts=None)
    rows, lim = S.flight_rows(f)
    assert rows[0]["true_O"] == pytest.approx(2.618, abs=1e-9)      # method O needs only riser and going
    assert rows[0]["true_D"] is None and "waist" in rows[0]["held_D"]
    with pytest.raises(S.SoffitError):
        S.flight_rows(flight("Fw2", 8, {"type": "ground"}, {"type": "plate", "t": 0.15}, t=0.175,
                             ts="CONVENTION 0.175"))


def test_adverse_beam_too_shallow_and_kink_past_the_plate_are_held():
    shallow = dict(F2, head={"type": "beam_face", "offset_before_last": 0.15, "depth": 0.35})
    assert S.flight_rows(shallow)[1]["D"] is None
    short = dict(F1, head={"type": "plate", "t": 0.15, "room": 0.30})
    lim = S.flight_rows(short)[1]
    assert lim["D"] is None and "far edge" in lim["D_held"]
    _, kd = S.kink_rows(F1, S.flight_rows(F1)[1], 0.30, 1.10)
    assert kd["held"] and S.landing_rows(QL, [kd])[0]["true_D"] is None


def test_adverse_winder_and_curved_flight_true_area_held():
    assert S.winder_true_area(drawn_polygons=None, soffit_drawn=False) is None
    assert S.winder_true_area(drawn_polygons=[[(0, 0), (1, 0), (0, 1)]], soffit_drawn=False) is None
    r = S.held_surface("W", "winder", 1.495, "hall", "fixture", "warped soffit not drawn")
    assert r["true_O"] is None and r["true_D"] is None and r["plan_O"] == 1.495
    with pytest.raises(S.SoffitError):
        S.held_surface("W", "winder", 1.495, "hall", "fixture", "")


def test_adverse_sub_piece_outside_its_flight_refused():
    with pytest.raises(S.SoffitError):
        S.flight_rows(F1, [("column", "NO_SOFFIT", (1.9, 2.4, 0.0, 0.05))])


def test_mirror_and_units():
    a = S.flight_rows(F1, [("column", "NO_SOFFIT", (0.5, 1.0, 0.0, 0.05))])[0][0]
    b = S.flight_rows(F1, [("column", "NO_SOFFIT", (0.5, 1.0, 1.05, 1.10))])[0][0]   # same column, mirrored lane
    for k in ("plan_O", "true_O", "plan_D", "true_D"):
        assert a[k] == pytest.approx(b[k], abs=1e-12)
    assert a["plan_O"] == pytest.approx(2.31 - 0.025, abs=1e-12)
    assert S.to_m(1100, "mm") == pytest.approx(1.10) and S.to_m(15, "cm") == pytest.approx(0.15)
    with pytest.raises(S.SoffitError):
        S.to_m(3, "ft")
    # a rotation of the stair changes nothing: the method works in the flight's own frame (s along, u across)
    assert math.isclose(S.pitch(0.16, 0.30, PR), SEC, abs_tol=1e-12)


def test_partition_and_ceiling_rules():
    assert S.partition_check(3.0, {"a": 1.0, "b": 2.0}) == pytest.approx(0.0)
    with pytest.raises(S.SoffitError):
        S.partition_check(3.0, {"a": 1.0, "b": 1.9})
    assert S.partition_check(3.0, {"a": 1.0, "b": 1.9}, residual_named="named cause") == pytest.approx(0.1)
    assert S.exclude_from_ceiling(10.0, 2.5) == pytest.approx(7.5)
    with pytest.raises(S.SoffitError):
        S.exclude_from_ceiling(1.0, 2.5)
