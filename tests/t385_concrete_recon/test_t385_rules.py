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
    assert s["engine_valued_m3"] == AP(4.2) and s["residual_m3"] == AP(-0.45) and s["bookkeeping_closes"]
    assert s["named_causes_m3"] == AP(-0.45) and s["unexplained_m3"] == AP(0.0) and s["cause_closes"]
    assert rows[0]["contribution_m3"] == AP(-0.45) and rows[1]["contribution_m3"] == AP(0.0)
    rows, s = R.family("COL", _col(), ["LC1", "LC2"], LINES, FL, 1.8)
    assert s["residual_m3"] == AP(-0.6) and s["bookkeeping_closes"] and s["unexplained_m3"] == AP(0.0)
    assert s["held_named_m3"] == AP(-0.6) and s["named_causes_m3"] == AP(0.0) and s["cause_closes"]
    n1 = rows[1]
    assert n1["engine_valued_m3"] == 0.0 and n1["held_low_m3"] == AP(0.32) and n1["held_high_m3"] == AP(0.48)
    assert n1["verdict"] == "HELD" and n1["contribution_m3"] == AP(-0.6)


def test_unexplained_remainder_is_named_not_hidden():
    # freelancer family total printed 0.128 above his own rows: without the arithmetic cause the family does not close
    rows, s = R.family("FOOT", _foot(), ["LF1", "LF2"], LINES, FL, 4.778)
    assert not s["bookkeeping_closes"] and s["bookkeeping_remainder_m3"] == AP(-0.128)
    assert s["unexplained_m3"] == AP(-0.128) and not s["cause_closes"]
    comps = _foot()
    comps.append({"id": "FA-ARITH", "family": "FOOT", "engine_lines": [], "freelancer_rows": [],
                  "freelancer_arithmetic_m3": 0.128, "cause_class": "FREELANCER_ARITHMETIC",
                  "cause": "printed total exceeds the sum of his own rows", "verdict": "ENGINE_RIGHT"})
    rows, s = R.family("FOOT", comps, ["LF1", "LF2"], LINES, FL, 4.778)
    assert s["bookkeeping_closes"] and s["cause_closes"] and s["named_causes_m3"] == AP(-0.578)


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
    assert s["engine_valued_m3"] == AP(1.8) and rows[1]["held_audit_engine_m3"] == AP(2.4) and s["bookkeeping_closes"]
    assert s["held_named_m3"] == AP(-2.4) and s["named_causes_m3"] == AP(-0.45) and s["cause_closes"]


# ---- r2: cause closure (R-T385-6). Fixture: a pool-like wall population, hand calculated.
#   engine: wall band mean length 10.00 m x 0.20 x height 1.00 (rim to base top) = 2.000 m3 (LW1, valued)
#   freelancer: 10.50 x 0.20 x 1.60 = 3.360 m3; contribution -1.360 m3 =
#     base thickness 0.30 counted again in the wall: 10.00 x 0.20 x 0.30 = 0.600 (DEPTH)
#     plan length 0.50 m longer, at his height:      0.50 x 0.20 x 1.60 = 0.160 (DIMENSION)
#     a further 0.30 m of his height no cause traces: 10.00 x 0.20 x 0.30 = 0.600 (untraced)
LW = {"LW1": _line("LW1", 10.0 * 0.2 * 1.0), "LU1": _line("LU1", 1.0)}
FLW = {"W:1": 10.5 * 0.2 * 1.6, "W:2": 1.25}


def _walls(split):
    c = {"id": "W", "family": "POOL", "engine_lines": ["LW1"], "freelancer_rows": ["W:1"], "cause_class": "DEPTH",
         "cause": "wall height from the base bottom (base counted again) and plan length", "verdict": "ENGINE_RIGHT"}
    if split is not None:
        c["cause_split"] = split
    return c


SPLIT_BASE = {"cause_class": "DEPTH", "cause": "base thickness 0.30 counted again in the wall height", "m3": -0.6}
SPLIT_PLAN = {"cause_class": "DIMENSION", "cause": "wall length 0.50 m over the drawn band", "m3": -0.16}


def _unres():
    return {"id": "U", "family": "POOL", "engine_lines": ["LU1"], "freelancer_rows": ["W:2"], "cause_class": "SCOPE",
            "cause": "lump row over several runs, not split by run", "verdict": "UNRESOLVED"}


def test_r2_split_short_of_its_contribution_prints_the_remainder():
    rows, s = R.family("POOL", [_walls([SPLIT_BASE, SPLIT_PLAN])], ["LW1"], LW, FLW, 3.36)
    w = rows[0]
    assert w["contribution_m3"] == AP(-1.36) and w["traced_m3"] == AP(-0.76) and w["unexplained_m3"] == AP(-0.6)
    assert "DEPTH -0.600000" in w["cause_split"] and "DIMENSION -0.160000" in w["cause_split"]
    assert s["bookkeeping_closes"] and not s["cause_closes"]
    assert s["named_causes_m3"] == AP(-0.76) and s["unexplained_m3"] == AP(-0.6) and s["untraced_remainder_m3"] == AP(-0.6)
    # normal: a split that covers the whole contribution closes the cause
    full = [SPLIT_BASE, SPLIT_PLAN, {"cause_class": "DEPTH", "cause": "rim drawn 0.30 m higher in his section", "m3": -0.6}]
    _, s = R.family("POOL", [_walls(full)], ["LW1"], LW, FLW, 3.36)
    assert s["cause_closes"] and s["unexplained_m3"] == AP(0.0)
    # one stated cause, no split: it covers the whole contribution
    _, s = R.family("POOL", [_walls(None)], ["LW1"], LW, FLW, 3.36)
    assert s["named_causes_m3"] == AP(-1.36) and s["cause_closes"]


def test_r2_unresolved_is_unexplained_never_a_named_cause():
    # bookkeeping closes (every line and row bound) but the UNRESOLVED -0.250 stays unexplained (F-T385-1)
    rows, s = R.family("POOL", [_walls(None), _unres()], ["LW1", "LU1"], LW, FLW, 4.61)
    assert s["bookkeeping_closes"] and s["bookkeeping_remainder_m3"] == AP(0.0)
    assert s["named_causes_m3"] == AP(-1.36) and s["unresolved_m3"] == AP(-0.25) and s["unexplained_m3"] == AP(-0.25)
    assert not s["cause_closes"]


def test_r2_adverse_unresolved_counted_as_named_cause_refused():
    u = _unres()
    u["cause_split"] = [{"cause_class": "SCOPE", "cause": "lump row", "m3": -0.25}]
    with pytest.raises(R.Refused):
        R.family("POOL", [_walls(None), u], ["LW1", "LU1"], LW, FLW, 4.61)
    held = _col()
    held[1]["cause_split"] = [{"cause_class": "DEPTH", "cause": "neck height", "m3": -0.6}]
    with pytest.raises(R.Refused):
        R.family("COL", held, ["LC1", "LC2"], LINES, FL, 1.8)
    for k in ("traced_m3", "unexplained_m3", "named_causes_m3"):
        u = _unres()
        u[k] = -0.25
        with pytest.raises(R.Refused):
            R.family("POOL", [_walls(None), u], ["LW1", "LU1"], LW, FLW, 4.61)


def test_r2_adverse_split_without_physical_cause_refused():
    with pytest.raises(R.Refused):
        R.family("POOL", [_walls([])], ["LW1"], LW, FLW, 3.36)
    with pytest.raises(R.Refused):
        R.family("POOL", [_walls([SPLIT_BASE, {"cause_class": "DIMENSION", "cause": "40 % of the rest", "m3": -0.16}])],
                 ["LW1"], LW, FLW, 3.36)
    with pytest.raises(R.Refused):
        R.family("POOL", [_walls([{"cause_class": "DEPTH", "cause": "base again"}])], ["LW1"], LW, FLW, 3.36)
