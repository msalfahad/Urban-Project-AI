"""T-385 rules on a hand NON-Alsenan fixture (two families, one held part): normal + adverse cases.

Fixture villa (hand calculated):
  FOOTINGS: F-A 2 no. 1.50 x 1.50 x 0.40 = 0.900 each -> 1.800 m3 (engine line LF1, valued);
            F-B 1 no. 2.00 x 2.40 x 0.50 = 2.400 m3 (engine line LF2, valued);
            freelancer: F-A 2 x 1.50 x 1.50 x 0.50 = 2.250 (depth 0.50 instead of the printed 0.40: -0.450),
                        F-B 2.400 (agrees). Residual 4.200 - 4.650 = -0.450 m3 = DEPTH cause -0.450.
  COLUMNS:  C-1 4 no. 0.20 x 0.50 x 3.00 = 0.300 each -> 1.200 m3 (LC1 valued);
            neck N-1 4 no. 0.20 x 0.50 x h, h HELD (formation level open) bound 0.80 .. 1.20 m -> 0.320 .. 0.480 m3 (LC2);
            freelancer: C-1 1.200, N-1 4 x 0.20 x 0.50 x 1.50 = 0.600. Residual 1.200 - 1.800 = -0.600 m3
            = HELD named item (necks) -0.600, the agreement on C-1 0.000.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t385"))
import t385_rules as R  # noqa: E402

AP = pytest.approx


def _line(lid, net=None, ev="MEASURED", lo=None, hi=None):
    return {"line_id": lid, "evidence_state": ev if net is not None else "BOUNDED_EXPOSURE", "measured_net": net,
            "bounded_low": lo, "bounded_high": hi}


LINES = {l["line_id"]: l for l in (
    _line("LF1", 2 * 1.5 * 1.5 * 0.40), _line("LF2", 2.0 * 2.4 * 0.5), _line("LC1", 4 * 0.2 * 0.5 * 3.0),
    _line("LC2", None, lo=4 * 0.2 * 0.5 * 0.80, hi=4 * 0.2 * 0.5 * 1.20))}
FL = {"X:1": 2 * 1.5 * 1.5 * 0.5, "X:2": 2.4, "X:5": 1.2, "X:6": 4 * 0.2 * 0.5 * 1.5}


def _foot():
    return [
        {"id": "FA", "family": "FOOT", "engine_lines": ["LF1"], "freelancer_rows": ["X:1"], "cause_class": "DEPTH",
         "cause": "freelancer depth 0.50 m vs printed 0.40 m on 2 x 1.50 x 1.50", "verdict": "ENGINE_RIGHT"},
        {"id": "FB", "family": "FOOT", "engine_lines": ["LF2"], "freelancer_rows": ["X:2"], "cause_class": "AGREE",
         "cause": "same printed plan and depth", "verdict": "AGREE"}]


def _col():
    return [
        {"id": "C1", "family": "COL", "engine_lines": ["LC1"], "freelancer_rows": ["X:5"], "cause_class": "AGREE",
         "cause": "same section and storey height", "verdict": "AGREE"},
        {"id": "N1", "family": "COL", "engine_lines": ["LC2"], "freelancer_rows": ["X:6"], "cause_class": "HELD_ITEM",
         "cause": "neck height open: formation level not printed", "verdict": "HELD"}]


def test_normal_two_families_close():
    rows, s = R.family("FOOT", _foot(), ["LF1", "LF2"], LINES, FL, 4.65)
    assert s["engine_valued_m3"] == AP(4.2) and s["residual_m3"] == AP(-0.45) and s["closes"]
    assert rows[0]["contribution_m3"] == AP(-0.45) and rows[1]["contribution_m3"] == AP(0.0)
    rows, s = R.family("COL", _col(), ["LC1", "LC2"], LINES, FL, 1.8)
    assert s["residual_m3"] == AP(-0.6) and s["closes"] and s["unexplained_m3"] == AP(0.0)
    n1 = rows[1]
    assert n1["engine_valued_m3"] == 0.0 and n1["held_low_m3"] == AP(0.32) and n1["held_high_m3"] == AP(0.48)
    assert n1["verdict"] == "HELD" and n1["contribution_m3"] == AP(-0.6)


def test_unexplained_remainder_is_named_not_hidden():
    # freelancer family total printed 0.128 above his own rows: without the arithmetic cause the family does not close
    rows, s = R.family("FOOT", _foot(), ["LF1", "LF2"], LINES, FL, 4.778)
    assert not s["closes"] and s["unexplained_m3"] == AP(-0.128)
    comps = _foot()
    comps.append({"id": "FA-ARITH", "family": "FOOT", "engine_lines": [], "freelancer_rows": [],
                  "freelancer_arithmetic_m3": 0.128, "cause_class": "FREELANCER_ARITHMETIC",
                  "cause": "printed total exceeds the sum of his own rows", "verdict": "ENGINE_RIGHT"})
    rows, s = R.family("FOOT", comps, ["LF1", "LF2"], LINES, FL, 4.778)
    assert s["closes"]


def test_adverse_held_counted_as_zero_agreement_refused():
    comps = _col()
    comps[1]["verdict"] = "AGREE"
    with pytest.raises(R.Refused):
        R.family("COL", comps, ["LC1", "LC2"], LINES, FL, 1.8)


def test_adverse_held_component_with_another_verdict_refused():
    comps = _col()
    comps[1]["verdict"] = "FREELANCER_RIGHT"
    with pytest.raises(R.Refused):
        R.family("COL", comps, ["LC1", "LC2"], LINES, FL, 1.8)


def test_adverse_residual_closed_by_a_ratio_refused():
    comps = _foot()
    comps[0]["cause"] = "freelancer 25 % over on depth, scaled to the residual"
    with pytest.raises(R.Refused):
        R.family("FOOT", comps, ["LF1", "LF2"], LINES, FL, 4.65)


def test_adverse_typed_engine_figure_refused():
    comps = _foot()
    comps[0]["engine_m3"] = 2.25
    with pytest.raises(R.Refused):
        R.family("FOOT", comps, ["LF1", "LF2"], LINES, FL, 4.65)


def test_adverse_line_twice_or_missing_refused():
    comps = _foot()
    comps[1]["engine_lines"] = ["LF2", "LF1"]
    with pytest.raises(R.Refused):
        R.family("FOOT", comps, ["LF1", "LF2"], LINES, FL, 4.65)
    with pytest.raises(R.Refused):
        R.family("FOOT", _foot()[:1], ["LF1", "LF2"], LINES, FL, 4.65)
    comps = _foot()
    comps[1]["freelancer_rows"] = ["X:2", "X:1"]
    with pytest.raises(R.Refused):
        R.family("FOOT", comps, ["LF1", "LF2"], LINES, FL, 4.65)


def test_downgraded_line_is_held_in_the_contractual_view():
    # LF2 under a downgrade record: its 2.400 leaves the valued side, the component is HELD, never AGREE
    comps = _foot()
    with pytest.raises(R.Refused):
        R.family("FOOT", comps, ["LF1", "LF2"], LINES, FL, 4.65, downgraded_ids=["LF2"])
    comps[1].update(cause_class="HELD_ITEM", cause="wrong basis downgraded by the Checker", verdict="HELD")
    rows, s = R.family("FOOT", comps, ["LF1", "LF2"], LINES, FL, 4.65, downgraded_ids=["LF2"])
    assert s["engine_valued_m3"] == AP(1.8) and rows[1]["held_audit_engine_m3"] == AP(2.4) and s["closes"]
