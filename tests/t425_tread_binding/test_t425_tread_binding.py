"""T-425 one flight occurrence, one tread line (R-T425-1 .. 3) on a NON-Alsenan hand fixture, Villa K425.

Villa K425 (hand-drawn, invented): a U stair GF +0.00 -> 1F +3.36 -> 2F +6.72.
  A   GF -> turn: 8 drawn front edges a1 .. a8, 1.000 wide, goings 0.280 drawn (8 treads)
  T   winder turn: drawn winders with conflicting counts (plan 3, section 4): HELD by the owner rule (S-9 type)
  B   turn -> 1F: 9 front edges b1 .. b9, 1.000 wide; goings of b1 .. b8 drawn 0.280, b9's rear edge (the 1F floor
      edge) not drawn on any sheet
  C   1F -> 2F: 10 front edges c1 .. c10, 0.950 wide, goings 0.290 drawn (10 treads)
Candidate readings (as a take-off engine would produce them):
  GF-1  A, OWN, 6 treads (two hidden treads above the cut missed)          valued 6 x 0.28 x 1.0
  1F-1  C, OWN, 10 treads                                                  valued
  2F-1  C, SEEN_THROUGH from 2F, 9 treads                                   valued  (the double count)
  1F-2  B, OWN, 8 treads                                                    valued
  1F-3  T seen from 1F, 3 wedges                                            valued  (held flight)
  2F-2  nothing drawn there (a ghost reading)                               valued  (UNBOUND)
  GF-2  B seen from GF, BOUNDED (not valued)
Hand results (independent of the code):
  A: 8 x 0.280 x 1.000 = 2.240 m2 (was 1.680, +0.560); step 8.000 lm (was 6.000, +2.000)
  B: drawn 9 treads; m2 = 8 x 0.280 x 1.000 = 2.240 (was 2.240, the 9th HELD beside 0.280); step 9.000 (was 8.000)
  C: 10 x 0.290 x 0.950 = 2.755 m2 kept; step 9.500 lm kept; 2F-1 2.4795 m2 / 8.550 lm DOUBLE_COUNT removed
  T: 0.700 m2 / 3.000 lm HELD;  ghost: 0.500 m2 / 2.000 lm HELD (UNBOUND)
"""

import importlib.util
import itertools
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("t425_tb", ROOT / "research" / "agents_t425" / "tread_binding.py")
TB = importlib.util.module_from_spec(spec)
sys.modules["t425_tb"] = TB
spec.loader.exec_module(TB)


def tr(prefix, n, width, going, src="K425 plan GF", undrawn=()):
    return tuple(TB.Tread(f"{prefix}{i}", width, None if f"{prefix}{i}" in undrawn else going,
                          "" if f"{prefix}{i}" in undrawn else src) for i in range(1, n + 1))


def flights():
    return [TB.Flight("A", tr("a", 8, 1.0, 0.28)),
            TB.Flight("T", tr("t", 3, 1.0, 0.28), held_cause="winder counts conflict (plan 3 vs section 4): S-9 HELD"),
            TB.Flight("B", tr("b", 9, 1.0, 0.28, undrawn=("b9",))),
            TB.Flight("C", tr("c", 10, 0.95, 0.29))]


def readings():
    R = TB.Reading
    return [R("GF-1", "A", "OWN", "LT-GF1", "LS-GF1", "PROVISIONAL", 6, 1.68, 6.0),
            R("1F-1", "C", "OWN", "LT-1F1", "LS-1F1", "PROVISIONAL", 10, 2.755, 9.5),
            R("2F-1", "C", "SEEN_THROUGH", "LT-2F1", "LS-2F1", "PROVISIONAL", 9, 2.4795, 8.55),
            R("1F-2", "B", "OWN", "LT-1F2", "LS-1F2", "PROVISIONAL", 8, 2.24, 8.0),
            R("1F-3", "T", "SEEN_THROUGH", "LT-1F3", "LS-1F3", "PROVISIONAL", 3, 0.7, 3.0),
            R("2F-2", None, "UNBOUND", "LT-2F2", "LS-2F2", "PROVISIONAL", 2, 0.5, 2.0),
            R("GF-2", "B", "PARTIAL", "LT-GF2", "LS-GF2", "BOUNDED_EXPOSURE", 4, None, None)]


def by_line(rows):
    return {r.line_id: r for r in rows}


def test_normal_hand_values():
    b = by_line(TB.bind(flights(), readings()))
    assert b["LT-GF1"].action == TB.CORRECT and b["LT-GF1"].after == pytest.approx(2.24) \
        and b["LT-GF1"].delta == pytest.approx(0.56)
    assert b["LS-GF1"].after == pytest.approx(8.0) and b["LS-GF1"].delta == pytest.approx(2.0)
    assert b["LT-1F2"].after == pytest.approx(2.24) and b["LT-1F2"].beside == pytest.approx(0.28) \
        and b["LT-1F2"].action == TB.CORRECT and "b9" in b["LT-1F2"].cause
    assert b["LS-1F2"].after == pytest.approx(9.0)
    assert b["LT-1F1"].action == TB.KEEP and b["LS-1F1"].action == TB.KEEP
    assert b["LT-GF2"].action == TB.KEEP and b["LT-GF2"].after is None


def test_adverse_flight_valued_twice_is_caught():
    b = by_line(TB.bind(flights(), readings()))
    assert b["LT-2F1"].action == TB.DOUBLE and b["LT-2F1"].after is None and b["LT-2F1"].delta == pytest.approx(-2.4795)
    assert b["LS-2F1"].action == TB.DOUBLE
    t = TB.totals(TB.bind(flights(), readings()))
    assert t["B7-02"]["double_count_removed"] == pytest.approx(2.4795)
    # the wrong logic (sum every valued reading) would give C 2.755 + 2.4795; the rule keeps C once
    vals = [r.after for r in TB.bind(flights(), readings()) if r.flight == "C" and r.code == "B7-02" and r.after]
    assert vals == [pytest.approx(2.755)]


def test_held_flight_and_unbound_never_zero():
    b = by_line(TB.bind(flights(), readings()))
    for lid, q in (("LT-1F3", 0.7), ("LS-1F3", 3.0), ("LT-2F2", 0.5), ("LS-2F2", 2.0)):
        assert b[lid].action == TB.HOLD and b[lid].after is None and b[lid].beside == pytest.approx(q)
    assert "S-9" in b["LT-1F3"].cause and "UNBOUND" in b["LT-2F2"].cause


def test_totals_hand():
    t = TB.totals(TB.bind(flights(), readings()))
    # after: A 2.240 + C 2.755 + B 2.240 = 7.235 m2; 8 + 9.5 + 9 = 26.5 lm
    assert t["B7-02"]["valued_after"] == pytest.approx(7.235)
    assert t["B7-06"]["valued_after"] == pytest.approx(26.5)
    assert t["B7-02"]["valued_before"] == pytest.approx(1.68 + 2.755 + 2.4795 + 2.24 + 0.7 + 0.5)
    assert t["B7-02"]["held_by_name"] == pytest.approx(1.2)


def test_partial_readings_fold_not_double():
    R = TB.Reading
    rs = [R("G1", "A", "PARTIAL", "T1", "S1", "PROVISIONAL", 5, 1.4, 5.0),
          R("G2", "A", "PARTIAL", "T2", "S2", "PROVISIONAL", 2, 0.56, 2.0)]
    b = by_line(TB.bind([TB.Flight("A", tr("a", 8, 1.0, 0.28))], rs))
    assert b["T1"].after == pytest.approx(2.24) and b["T2"].action == TB.FOLD and b["T2"].after is None
    assert any("engine reads 7 treads, drawn 8" in n for n in b["T1"].notes)


def test_order_invariance():
    base = {(r.line_id, r.action, r.after) for r in TB.bind(flights(), readings())}
    for perm in itertools.islice(itertools.permutations(readings()), 0, 40, 7):
        assert {(r.line_id, r.action, r.after) for r in TB.bind(flights(), list(perm))} == base


def test_mirror_rotation_invariance():
    # the check works on drawn lengths and counts only: a mirrored / rotated plan gives the same front-edge lengths and
    # goings, so the same rows (coordinates never enter)
    m = [TB.Flight(f.fid, tuple(reversed(f.treads)), f.held_cause) for f in flights()]
    assert {(r.line_id, r.after) for r in TB.bind(m, readings())} == \
        {(r.line_id, r.after) for r in TB.bind(flights(), readings())}


@pytest.mark.parametrize("bad", [
    lambda F, R: ([TB.Flight("A", tr("a", 8, 1000.0, 0.28))] + F[1:], R),            # mm passed as m
    lambda F, R: ([TB.Flight("A", tr("a", 8, 1.0, 280.0))] + F[1:], R),              # mm going
    lambda F, R: ([TB.Flight("A", tr("a", 8, 1.0, 0.0))] + F[1:], R),                # zero going
    lambda F, R: ([TB.Flight("A", tr("a", 8, 1.0, 0.28) + (TB.Tread("a1", 1.0, 0.28, "x"),))] + F[1:], R),  # twice
    lambda F, R: ([TB.Flight("A", (TB.Tread("a1", 1.0, 0.28, ""),))] + F[1:], R),     # going without source
    lambda F, R: (F, R + [TB.Reading("X", "C", "OWN", "LX", "SX", "PROVISIONAL", 1, 0.1, 1.0)]),  # two OWN
    lambda F, R: (F, R + [TB.Reading("Y", "Z", "OWN", "LY", "SY", "PROVISIONAL", 1, 0.1, 1.0)]),  # unknown flight
    lambda F, R: (F, R + [TB.Reading("W", None, "OWN", "LW", "SW", "PROVISIONAL", 1, 0.1, 1.0)]),  # unbound as OWN
    lambda F, R: (F, R + [TB.Reading("V", "A", "PARTIAL", "LV", "SV", "PROVISIONAL", 1, None, 1.0)]),  # valued, None
    lambda F, R: (F, R + [R[0]]),                                                      # reading twice
])
def test_refused_inputs(bad):
    F, R = bad(flights(), readings())
    with pytest.raises(TB.BindingInputError):
        TB.bind(F, R)
