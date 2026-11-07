"""T-578 handrails / balustrades / guards and stair nosing vs a reference takeoff (R-T578-1): a non-Alsenan hand
fixture, adverse cases, and the development-villa build pinned (byte-identical rebuild, closures, units)."""
from __future__ import annotations

import importlib
import importlib.util
import json
import math
import re
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t578"
sys.path.insert(0, str(HERE))
R = importlib.import_module("t578_rules")
_spec = importlib.util.spec_from_file_location("t578_alsenan", HERE / "t578_alsenan.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

D = Decimal


# ---- hand fixture (not Alsenan): Villa F, one dog-leg stair, flight going 3.00 m, rise 1.80 m ----------------------
# Pitch length sqrt(3.00^2 + 1.80^2) = sqrt(12.24) = 3.498571 lm; plan 3.00 lm kept apart.
def test_fixture_flight_pitch_length_vs_plan():
    assert R.rail_length("INCLINED", "3.00", "1.80") == D("3.498571")
    assert R.rail_length("HORIZONTAL", "3.00") == D("3.000000")
    assert R.check_billed("INCLINED", "3.00", "1.80", "3.498571") == D("3.498571")


def test_fixture_in_millimetres():
    assert R.rail_length("INCLINED", "3000", "1800", unit="mm") == D("3.498571")
    assert R.nosing_lm("1200", "50", unit="mm") == D("1.150")


@pytest.mark.parametrize("deg", [0, 37, 90, 180, 211])
@pytest.mark.parametrize("mirror", [False, True])
def test_fixture_plan_length_rotation_and_mirror(deg, mirror):
    a = math.radians(deg)
    p, q = (0.0, 0.0), (3.00, 0.0)
    if mirror:
        q = (-q[0], q[1])
    rot = lambda x: (x[0] * math.cos(a) - x[1] * math.sin(a) + 7.0, x[0] * math.sin(a) + x[1] * math.cos(a) - 2.0)  # noqa
    plan = R.plan_from_points(rot(p), rot(q))
    assert plan == D("3.000000")
    assert R.rail_length("INCLINED", plan, "1.80") == D("3.498571")


def _villa_f():
    pcs = [R.rail_piece("F1", "BALUSTRADE", "INCLINED", "DRAWING-CONFIRMED", "3.00", "1.80", "3.498571", run="R1"),
           R.rail_piece("LD", "BALUSTRADE", "HORIZONTAL", "DRAWING-CONFIRMED", "1.20", None, "1.20", run="R1"),
           R.rail_piece("F2", "BALUSTRADE", "INCLINED", "DRAWING-CONFIRMED", "3.00", "1.80", "3.498571", run="R1"),
           R.rail_piece("WT", "BALUSTRADE", "TURN", "HELD", bound=R.turn_bound("0.20", "0.30"), run="R1"),
           R.rail_piece("G1", "GUARD", "HORIZONTAL", "DRAWING-CONFIRMED", "4.00", None, "4.00", run="R2"),
           R.rail_piece("W1", "WALL_HANDRAIL", "INCLINED", "NOT_APPLICABLE")]
    return pcs


def test_fixture_villa_f_closes_against_a_reference():
    pcs = _villa_f()
    ours = R.ours_total(pcs)
    assert ours == D("12.197142")          # 3.498571 x 2 + 1.20 + 4.00
    lo, hi = R.held_bound(pcs)
    assert lo == D("0.360555") and hi is None   # chord sqrt(0.2^2 + 0.3^2)
    his = D("7.20")                         # reference: plan length of both flights (6.00) + landing 1.20, no guard
    causes = [R.cause("guard in our list only", D("-4.00"), "ENGINE_RIGHT", "SCOPE", "fixture"),
              R.cause("pitch vs plan", D("6.00") - D("6.997142"), "ENGINE_RIGHT", "MEASURE", "fixture"),
              R.cause("held turn", 0, "HELD", "HELD", "fixture", bound=(lo, hi))]
    assert R.close(his, ours, causes) == D("-4.997142")
    assert R.pct(his, ours, causes) is None


def test_fixture_nosing_one_per_riser_and_his_count_by_width():
    ns = [R.nosing_piece(f"N{i}", "S", "TREAD", "DRAWING-CONFIRMED", "1.150") for i in range(10)]
    ns.append(R.nosing_piece("N10", "S", "LANDING_EDGE", "DRAWING-CONFIRMED", "1.150", notch="0.050"))
    ns.append(R.nosing_piece("N11", "S", "WINDER", "HELD", beside="1.259"))
    assert R.ours_total(ns) == D("12.600")
    assert R.held_bound(ns) == (D(0), D("1.259"))
    his = R.his_row_lm(12, "1.20")
    assert his == D("14.40")
    causes = [R.cause("held winder", D("1.20"), "HELD", "HELD", "f", bound=R.held_bound(ns)),
              R.cause("width", 11 * D("0.05"), "ENGINE_RIGHT", "MEASURE", "f"),
              R.cause("notch", D("0.050"), "ENGINE_RIGHT", "MEASURE", "f")]
    assert R.close(his, R.ours_total(ns), causes) == D("1.800")


def test_fixture_curved_flight_per_going_bounded():
    pitch = R.rail_length("INCLINED", "2.587274", "1.928568")
    assert R.check_billed("INCLINED", "2.587274", "1.928568", "3.228281", curved=True) == D("3.228281")
    assert pitch < D("3.228281")
    with pytest.raises(R.RuleError):
        R.check_billed("INCLINED", "2.587274", "1.928568", "4.60", curved=True)      # beyond plan + rise
    with pytest.raises(R.RuleError):
        R.check_billed("INCLINED", "2.587274", "1.928568", "3.10", curved=True)      # below the pitch line


# ---- adverse --------------------------------------------------------------------------------------------------------
def test_adverse_plan_length_for_a_flight_rail_refused():
    with pytest.raises(R.RuleError, match="plan length billed for an inclined rail"):
        R.check_billed("INCLINED", "3.00", "1.80", "3.00")
    with pytest.raises(R.RuleError, match="plan length billed"):
        R.rail_piece("F1", "BALUSTRADE", "INCLINED", "DRAWING-CONFIRMED", "3.00", "1.80", "3.00")


def test_adverse_held_winder_edge_counted_as_zero_refused():
    with pytest.raises(R.RuleError, match="never 0"):
        R.nosing_piece("W", "S", "WINDER", "HELD", edge="0")
    with pytest.raises(R.RuleError, match="never 0"):
        R.rail_piece("WT", "BALUSTRADE", "TURN", "HELD", billed="0", bound=(D(0), None))
    with pytest.raises(R.RuleError, match="HELD / UNKNOWN is never 0"):
        R.D(None)
    with pytest.raises(R.RuleError, match="HELD piece with a value"):
        R.ours_total([{"id": "x", "status": "HELD", "value": D(0), "bound": (D(0), None)}])


def test_adverse_kinds_and_units():
    with pytest.raises(R.RuleError, match="without a rise"):
        R.rail_length("INCLINED", "3.00", None)
    with pytest.raises(R.RuleError, match="it is INCLINED"):
        R.rail_length("HORIZONTAL", "3.00", "0.20")
    with pytest.raises(R.RuleError, match="TURN"):
        R.rail_length("TURN", "0.20", "0.30")
    with pytest.raises(R.RuleError, match="unit"):
        R.rail_length("INCLINED", "3", "1.8", unit="cm")
    with pytest.raises(R.RuleError):
        R.rail_piece("X", "HANDRAIL?", "INCLINED", "DRAWING-CONFIRMED", "3", "1.8", "3.498571")
    with pytest.raises(R.RuleError, match="needs a bound"):
        R.rail_piece("X", "BALUSTRADE", "TURN", "HELD")


def test_adverse_verified_and_unnamed_residual_refused():
    with pytest.raises(R.RuleError, match="Checker"):
        R.rail_piece("X", "BALUSTRADE", "INCLINED", "VERIFIED", "3", "1.8", "3.498571")
    with pytest.raises(R.RuleError, match="residual"):
        R.close("18.95", "18.724", [R.cause("a", "0.2", "UNRESOLVED", "RESIDUAL", "x")])
    with pytest.raises(R.RuleError, match="needs the bound"):
        R.cause("h", 0, "HELD", "HELD", "x")


def test_adverse_reference_count():
    with pytest.raises(R.RuleError, match="whole number"):
        R.his_row_lm("63.5", "1.20")
    with pytest.raises(R.RuleError):
        R.his_row_lm(None, "1.20")
    with pytest.raises(R.RuleError, match="notch longer"):
        R.nosing_lm("0.05", "0.10")


# ---- development villa, pinned ---------------------------------------------------------------------------------------
OUT = HERE / "out" / "T578_RAIL_NOSING_RECONCILE.json"


def test_alsenan_rebuild_byte_identical():
    assert OUT.read_text(encoding="utf-8") == A.dump(A.build())


def test_alsenan_rail_totals_and_closure():
    d = json.loads(OUT.read_text(encoding="utf-8"))
    r = d["rails_lm"]
    assert r["ours"]["by_family"] == {"WALL_HANDRAIL": "0", "BALUSTRADE": "33.319174", "GUARD": "21.550"}
    assert r["his"]["value"] == "18.95" and r["gap"] == "-35.919174" and r["pct"] is None
    assert sum(D(c["amount"]) for c in r["causes"]) == D(r["gap"])
    assert all(x["value"] is None for x in r["runs"] if x["status"] in ("HELD", "UNKNOWN"))
    assert all(x["bound"] is not None for x in r["runs"] if x["status"] == "HELD")
    assert d["code_closure"]["FIN.RAILING"]["by_class"] == {"EXCLUDED": 14, "HELD": 5, "RELEASED": 3}


def test_alsenan_nosing_totals_and_closure():
    d = json.loads(OUT.read_text(encoding="utf-8"))
    t = d["nosing_lm"]["totals"]
    assert (D(t["his"]), D(t["ours"]), D(t["gap"]), t["held_n"]) == (D("123.2"), D("87.35"), D("35.85"), 20)
    for g in d["nosing_lm"]["groups"]:
        assert sum(D(c["amount"]) for c in g["causes"]) == D(g["gap"])
    n = d["nosing_nr"]["totals"]
    assert (n["his"], n["ours"], n["gap"]) == ("96", 69, "27")
    assert d["code_closure"]["nosing_lines_in_candidate"] == 0


def test_alsenan_no_workbook_text_or_coordinates():
    s = OUT.read_text(encoding="utf-8")
    assert not re.search("[؀-ۿ]", s)
    src = (HERE / "t578_alsenan.py").read_text(encoding="utf-8") + (HERE / "t578_rules.py").read_text(encoding="utf-8")
    assert not re.search("[؀-ۿ]", src)


def test_alsenan_edited_input_stops_the_build(monkeypatch):
    monkeypatch.setitem(A.PINS, A.CENSUS, "0000000000000000")
    with pytest.raises(R.RuleError, match="restate the inputs"):
        A.build()
