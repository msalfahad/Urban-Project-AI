"""T-770 r11: ARCH_TAKEOFF_V3.0.88 (FILL_WIRE_V7 unchanged, one version step) on a synthetic index and synthetic BOQ
lines (no project data): two worker sets built on the older base V3.0.86 apply by line id to a V3.0.87 base; a
released run is re-measured, a HELD range becomes a RELEASED point (inside and outside the range it replaces, the
figure is the set's, never the range's end), a low = high range is carried as a point; every other line is
untouched. Adverse: the wrong schema / base / index version, a stale before, a row on a base the package does not
accept, one line bound by two sets, a HELD row widened to low > high, a row naming no base line.
Plus the committed r11 outputs equal their builder."""
from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3081 as B  # noqa: E402
from engine.source import arch_v3088 as A  # noqa: E402

V86 = "ARCH_TAKEOFF_V3.0.86"
LC = "L-" + "a" * 20          # a decor-ceiling cornice run (released, re-measured)
LE = "L-" + "b" * 20          # door-jamb tile edges (HELD 0 .. 7.0 -> point 9.6 outside the range)
LF = "L-" + "c" * 20          # a stair-corner floor strip (HELD 0 .. 0.4 -> point 0.4)
LS = "L-" + "d" * 20          # a space with low = high (carried as a point)


def _ln(lid, code, unit, cls="RELEASED", net=None, lo=None, hi=None, label=None, basis=None):
    d = {"binding": None, "class": cls, "element_id": f"E:{lid}", "held_high": hi, "held_low": lo,
         "item_code": code, "line_id": lid, "measured_net": net, "unbound_records": [], "unit": unit}
    if label:
        d["method_label"], d["fill_basis"] = label, basis
    return d


def _index():
    return {"schema": B.INDEX_SCHEMA, "candidate_version": A.EXTENDS, "lines": [
        _ln(LC, "FIN.CEILING.CORNICE", "lm", net=20.0, label="ESTIMATE", basis="closed rooms 20.0"),
        _ln(LE, "FIN.WALL.TILE.EDGE", "lm", cls="HELD", lo=0.0, hi=7.0, label="ESTIMATE", basis="0 where a frame covers"),
        _ln(LF, "FIN.FLOOR.FINISH_HELD", "m2", cls="HELD", lo=0.0, hi=0.4),
        _ln(LS, "ARCH.SPACE", "m2", cls="HELD", lo=1.25, hi=1.25),
        _ln("L-out", "FIN.PAINT", "m2", net=10.0, label="DEFAULT", basis="x")]}


def _row(lid, code, unit, before, after, label, basis):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": f"E:{lid}", "before": before,
            "after": after, "label": label, "basis": basis}


def _pkg():
    cornice = {"schema": "URBAN_FIX_ROWS_V1", "task": "T-1", "candidate_version": V86, "rows": [
        _row(LC, "FIN.CEILING.CORNICE", "lm", {"class": "RELEASED", "net": 20.0, "label": "ESTIMATE"},
             {"class": "RELEASED", "net": 26.5}, "ESTIMATE", "closed rooms 20.0 + open zone 4.0 x 2 - 1.5 opening")]}
    held = {"schema": "URBAN_FIX_ROWS_V1", "task": "T-2", "candidate_version": V86, "rows": [
        _row(LE, "FIN.WALL.TILE.EDGE", "lm", {"class": "HELD", "low": 0.0, "high": 7.0, "label": "ESTIMATE"},
             {"class": "RELEASED", "net": 9.6}, "DEFAULT", "2 faces x (2 x 2.20 + 0.40)"),
        _row(LF, "FIN.FLOOR.FINISH_HELD", "m2", {"class": "HELD", "low": 0.0, "high": 0.4},
             {"class": "RELEASED", "net": 0.4}, "DRAWING-READ", "0.20 x 2.00 strip"),
        _row(LS, "ARCH.SPACE", "m2", {"class": "HELD", "low": 1.25, "high": 1.25},
             {"class": "RELEASED", "net": 1.25}, "MEASURED", "low = high: 1.25 carried as a point")]}
    return {"schema": A.PACKAGE_SCHEMA, "method": A.METHOD, "base": A.EXTENDS, "row_bases": [V86],
            "set_names": ["T-1", "T-2"], "sets": [cornice, held]}


def test_index_normal_case():
    base = _index()
    new, applied, late, rep = A.apply_index(base, _pkg())
    by = {ln["line_id"]: ln for ln in new["lines"]}
    assert by[LC]["measured_net"] == 26.5 and by[LC]["class"] == "RELEASED"
    assert by[LE]["class"] == "RELEASED" and by[LE]["measured_net"] == 9.6 and by[LE]["method_label"] == "DEFAULT"
    assert by[LE]["held_low"] is None and by[LE]["held_high"] is None     # the range is gone, not kept beside it
    assert by[LF]["measured_net"] == 0.4 and by[LF]["method_label"] == "DRAWING-READ"
    assert by[LS]["measured_net"] == 1.25 and by[LS]["method_label"] == "MEASURED"
    assert by["L-out"] == base["lines"][4]
    assert len(new["lines"]) == 5 and not late
    assert new["candidate_version"] == A.METHOD and new["extends"] == A.EXTENDS and new["fill"]["rule"] == A.RULES
    assert new["fill"]["policy"] == A.POLICY_ID
    assert not any(ln["class"] == "RELEASED" and ln["measured_net"] == 0 for ln in new["lines"])
    assert {r["line_id"] for r in applied} == {LC, LE, LF, LS}


def _boq(ln):
    br = None if ln["held_low"] is None else {"low": ln["held_low"], "high": ln["held_high"]}
    return {"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln["unit"],
            "evidence_state": "PROVISIONAL" if ln["class"] == "RELEASED" else (B.BOUNDED if br else "HELD"),
            "measured_net": ln["measured_net"], "bounded_range": br,
            "location": {"element_id": ln["element_id"]}, "gross": None,
            "method_label": ln.get("method_label"), "fill_basis": ln.get("fill_basis")}


def test_boq_view_matches_the_index_view():
    lines = [_boq(ln) for ln in _index()["lines"]]
    new, applied, added, late, rep = A.apply_boq_lines(lines, _pkg())
    by = {ln["line_id"]: ln for ln in new}
    idx = {ln["line_id"]: ln for ln in A.apply_index(_index(), _pkg())[0]["lines"]}
    assert set(by) == set(idx) and len(new) == len(lines) and not added and not late
    for lid, ln in by.items():
        assert B.line_class(ln) == idx[lid]["class"] and ln["measured_net"] == idx[lid]["measured_net"], lid
    assert by["L-out"] == lines[4]


def _h(p):
    return p["sets"][1]


@pytest.mark.parametrize("break_it, msg", [
    (lambda p: p.update(schema="URBAN_FILL_PACKAGE_V7"), "is not URBAN_FILL_PACKAGE_V8"),
    (lambda p: p.update(base=V86), "built for"),
    (lambda p: [s.update(candidate_version="ARCH_TAKEOFF_V3.0.70") for s in p["sets"]], "base accepts"),
    (lambda p: _h(p)["rows"].append(copy.deepcopy(p["sets"][0]["rows"][0])), "bound by T-1 and T-2"),
    (lambda p: _h(p)["rows"][0]["after"].update({"class": "HELD", "low": 9.6, "high": 7.0}), "0 <= low <= high"),
    (lambda p: _h(p)["rows"][0].update(line_id="L-" + "z" * 20), "name no base line"),
    (lambda p: _h(p)["rows"][0]["after"].update(net=None), "needs a figure"),
])
def test_adverse_cases_stop_the_run(break_it, msg):
    p = copy.deepcopy(_pkg())
    break_it(p)
    with pytest.raises(B.FillError, match=msg):
        A.apply_index(_index(), p)


def test_row_on_a_stale_before_stops():
    """adverse: the base moved under the set (the range the row read is no longer the base line)"""
    base = _index()
    base["lines"][1]["held_high"] = 8.0
    with pytest.raises(B.FillError, match="row read"):
        A.apply_index(base, _pkg())


def test_index_of_another_version_refused():
    base = _index()
    base["candidate_version"] = V86
    with pytest.raises(B.FillError, match="base is"):
        A.apply_index(base, _pkg())


def test_committed_r11_outputs_equal_their_builder():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t770/v3088_index.py"), "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0 and "check: OK" in r.stdout, r.stdout + r.stderr
