"""T-476: handrails / guardrails along the slope, flight by flight (R-T476-1 slope vs level, R-T476-2 one home per
physical flight for the plan reader's per-flight lines, R-T476-3 family of a horizontal guard).

Synthetic 'Villa E' (not the development villa), hand calculation in research/agents_t476/t476_handrail_runs.py:
dog-leg, 2 flights x 9 risers 0.175 / going 0.280 -> 8 goings: plan 2.240, rise 1.400,
sqrt(2.240^2 + 1.400^2) = sqrt(5.0176 + 1.9600) = 2.641515 lm per flight; level turn 0.250; top floor-edge guard
continuous with flight B's band 1.100 (B7-09); separate floor-edge band 0.900 (B13-08).
B7-09 = 2 x 2.641515 + 0.250 + 1.100 = 6.633030 lm.
Adverse: plan length billed for an inclined run refused; inclined without rise refused; mm read as m refused; open side
with no drawn rail HELD (None); guard on a walled side refused; a per-flight line carrying a figure refused; two primary
readings of one flight refused; an unbound reader line refused; reader side kinds that differ from the census named;
mirrored flight (sides swapped) gives the same length and the same side check.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_DIR = ROOT / "research" / "agents_t476"


def _mod():
    spec = importlib.util.spec_from_file_location("t476_handrail_runs", _DIR / "t476_handrail_runs.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("t476_handrail_runs", mod)
    spec.loader.exec_module(mod)
    return mod


H = _mod()


def test_villa_e_hand_calculation():
    A, B, segs = H.villa_e()
    assert A.goings == 8 and A.plan == pytest.approx(2.240) and A.rise == pytest.approx(1.400)
    assert A.pitch_length == pytest.approx(math.sqrt(5.0176 + 1.96), abs=1e-9)
    assert A.pitch_length == pytest.approx(2.641515, abs=5e-7)
    t = H.family_totals(segs)
    assert t[H.FAM_STAIR]["confirmed_lm"] == pytest.approx(6.633030, abs=5e-6)
    assert t[H.FAM_GUARD]["confirmed_lm"] == pytest.approx(0.900)
    assert H.FAM_WALL not in t


def test_plan_length_for_inclined_run_refused():
    with pytest.raises(H.RailInputError, match="plan length"):
        H.segment_length(H.INCLINED, 2.240, 1.400, length_m=2.240)
    with pytest.raises(H.RailInputError, match="without its rise"):
        H.segment_length(H.INCLINED, 2.240, None)
    with pytest.raises(H.RailInputError, match="HORIZONTAL segment with rise"):
        H.segment_length(H.HORIZONTAL, 2.240, 1.400)
    L = H.segment_length(H.INCLINED, 2.240, 1.400)
    assert H.segment_length(H.INCLINED, 2.240, 1.400, length_m=L) == pytest.approx(2.641515, abs=5e-7)


def test_units_mm_refused():
    with pytest.raises(H.RailInputError):
        H.Flight("X", 9, 175.0, 280.0)
    with pytest.raises(H.RailInputError):
        H.segment_length(H.HORIZONTAL, 1100.0, 0.0)


def test_side_classification():
    assert H.classify_side(H.OPEN, rail_drawn=True) == (H.FAM_STAIR, H.CONFIRMED)
    assert H.classify_side(H.OPEN, rail_drawn=False) == (H.FAM_STAIR, H.HELD)
    assert H.classify_side(H.OPEN, rail_drawn=True, floor_level_band=True) == (H.FAM_GUARD, H.CONFIRMED)
    assert H.classify_side(H.WALL, rail_drawn=False) == (None, H.NOT_APPLICABLE)
    assert H.classify_side(H.WALL, rail_drawn=True, wall_rail_drawn=True) == (H.FAM_WALL, H.CONFIRMED)
    with pytest.raises(H.RailInputError, match="walled side"):
        H.classify_side(H.WALL, rail_drawn=True)


def test_held_is_blank_never_zero():
    with pytest.raises(H.RailInputError, match="carries a figure"):
        H.family_totals([{"id": "x", "family": H.FAM_STAIR, "status": H.HELD, "length": 0.0}])
    t = H.family_totals([{"id": "x", "family": H.FAM_STAIR, "status": H.HELD, "length": None}])
    assert t[H.FAM_STAIR]["held_n"] == 1 and t[H.FAM_STAIR]["confirmed_lm"] == 0.0


def _readers():
    return [H.ReaderLine("L-1", "GF", "F1", (("side_a", H.WALL, 2.24), ("side_b", H.OPEN, 2.24))),
            H.ReaderLine("L-2", "1F", "F1", (("side_a", H.WALL, 2.24), ("side_b", H.OPEN, 2.24))),
            H.ReaderLine("L-3", "1F", "F2", (("side_a", H.OPEN, 2.24), ("side_b", H.WALL, 2.24)))]


def test_reader_lines_bound_once_and_retired():
    census = {"E-A": (H.OPEN, H.WALL), "E-B": (H.WALL, H.OPEN)}
    homes = {"E-A": ["RUN E-A inner"], "E-B": ["RUN E-B inner"]}
    b = H.bind_reader_lines(_readers(), {"L-1": ("E-A", "PRIMARY"), "L-2": ("E-A", "SEEN_THROUGH_OPENING"),
                                         "L-3": ("E-B", "PRIMARY")}, census, homes)
    assert [x["action"] for x in b] == ["RETIRE"] * 3
    assert all(x["side_check"] == "AGREE" for x in b)        # mirrored side names, same multiset of kinds


def test_reader_adverse():
    census = {"E-A": (H.OPEN, H.WALL), "E-B": (H.OPEN, H.WALL)}
    homes = {"E-A": ["r"], "E-B": ["r"]}
    with pytest.raises(H.RailInputError, match="two primary"):
        H.bind_reader_lines(_readers(), {"L-1": ("E-A", "PRIMARY"), "L-2": ("E-A", "PRIMARY"),
                                         "L-3": ("E-B", "PRIMARY")}, census, homes)
    with pytest.raises(H.RailInputError, match="bound to no physical flight"):
        H.bind_reader_lines(_readers(), {"L-1": ("E-A", "PRIMARY")}, census, homes)
    fig = [H.ReaderLine("L-9", "GF", "F1", (("side_a", H.OPEN, 1.0),), measured=2.5)]
    with pytest.raises(H.RailInputError, match="same guard twice"):
        H.bind_reader_lines(fig, {"L-9": ("E-A", "PRIMARY")}, census, homes)
    both_open = [H.ReaderLine("L-5", "GF", "F1", (("side_a", H.OPEN, 1.2), ("side_b", H.OPEN, 1.2)))]
    b = H.bind_reader_lines(both_open, {"L-5": ("E-A", "PRIMARY")}, census, homes)
    assert b[0]["side_check"].startswith("SIDE_DIFFERS")
    b = H.bind_reader_lines(both_open, {"L-5": ("E-A", "PRIMARY")}, census, {})
    assert b[0]["action"] == "HOLD_OPEN"


def test_committed_development_villa_outputs_close():
    """The committed run outputs (python3 -I research/agents_t476/t476_alsenan.py <dxf> <V2.9 lines> --write) are
    internally consistent: confirmed lengths re-derived from plan / rise, held rows blank, 14 reader lines retired."""
    rows = list(csv.DictReader((_DIR / "FLIGHT_CENSUS_T476.csv").open()))
    b709 = 0.0
    for r in rows:
        if r["STATUS"] == H.CONFIRMED:
            L, plan = float(r["LENGTH_LM"]), float(r["PLAN_M"])
            rise = float(r["RISE_M"]) if r["RISE_M"] else 0.0
            if r["KIND"] == H.INCLINED and r["FLIGHT"] != "RS-C":       # RS-C is per going (variable pitch)
                assert L == pytest.approx(math.hypot(plan, rise), abs=2e-6)
                assert L > plan
            if r["KIND"] == H.HORIZONTAL:
                assert L == pytest.approx(plan) and rise == 0.0
            if r["FAMILY"] == H.FAM_STAIR:
                b709 += L
        else:
            assert r["LENGTH_LM"] == ""
    assert round(b709, 3) == 33.319
    s = json.loads((_DIR / "summary.json").read_text())
    assert s["reader_binding"]["retire"] == 14 and s["reader_binding"]["side_differs"] == []
    assert s["proposal"]["B7-09 FIN.RAILING"]["proposed_valued_lm"] == 33.319
    assert s["proposal"]["B13-08 MET.RAILING.GUARD"]["proposed_valued_lm"] == 21.55
    binds = list(csv.DictReader((_DIR / "READER_BINDING_T476.csv").open()))
    prim = [r["PHYSICAL_FLIGHT"] for r in binds if r["READING"] in ("PRIMARY", "PARTIAL_PRIMARY")]
    assert len(prim) == len(set(prim)) == 9
