"""T-770 r10: ARCH_TAKEOFF_V3.0.87 (FILL_WIRE_V7, R-T770-8) on a synthetic index and synthetic BOQ lines (no project
data): a CHECKER_FINDING set whose rows carry the finding id in the basis and hand factors whose product is the after
figure is applied by line id like any other set; a worker set built on the older base applies beside it; a set's
added lines are written; every other line is untouched. Adverse: a hand product that differs, a factor <= 0, a basis
that does not name the finding, a finding set without its verdict, one line bound by two sets, the wrong schema / base.
Plus the committed r10 outputs equal their builder."""
from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3081 as B  # noqa: E402
from engine.source import arch_v3087 as A  # noqa: E402

V85 = "ARCH_TAKEOFF_V3.0.85"
LB = "L-" + "a" * 20          # a beam band carried at a default depth (worker set)
LS = "L-" + "b" * 20          # a strip in the same band (Checker finding)
LU = "L-" + "c" * 20          # an upturn run that loses a doorway


def _ln(lid, code, unit, cls="RELEASED", net=None, label=None, basis=None):
    d = {"binding": None, "class": cls, "element_id": f"E:{lid}", "held_high": None, "held_low": None,
         "item_code": code, "line_id": lid, "measured_net": net, "unbound_records": [], "unit": unit}
    if label:
        d["method_label"], d["fill_basis"] = label, basis
    return d


def _index():
    return {"schema": B.INDEX_SCHEMA, "candidate_version": A.EXTENDS, "lines": [
        _ln(LB, "STR.CONC.BEAM", "m3", net=0.36, label="DEFAULT", basis="0.60 m2 x 0.60 default"),
        _ln(LS, "STR.CONC.BEAM", "m3", net=0.096, label="DEFAULT", basis="0.16 m2 x 0.60 default"),
        _ln(LU, "FIN.WP.ROOF_UPTURN", "lm", net=10.0, label="ESTIMATE", basis="inner boundary 10.0"),
        _ln("L-out", "FIN.PAINT", "m2", net=10.0, label="DEFAULT", basis="x")]}


def _r(lid, code, unit, b, a, label, basis, **kw):
    d = {"line_id": lid, "item_code": code, "unit": unit, "element_id": f"E:{lid}",
         "before": {"class": "RELEASED", "net": b, "label": label}, "after": {"class": "RELEASED", "net": a},
         "label": label, "basis": basis}
    d.update(kw)
    return d


def _pkg():
    worker = {"schema": "URBAN_FIX_ROWS_V1", "task": "T-1", "candidate_version": V85, "rows": [
        _r(LB, "STR.CONC.BEAM", "m3", 0.36, 0.096, "DEFAULT", "0.60 m2 x 0.16 printed slab")]}
    upturn = {"schema": "DELIVERY_FIX_ROWS_V1", "task": "T-2", "candidate_version": V85, "rows": [
        _r(LU, "FIN.WP.ROOF_UPTURN", "lm", 10.0, 9.0, "DRAWING-READ", "10.0 less the door 1.0")], "new_lines": [
        {"line_id": "NEW:E:door", "item_code": "FIN.WP.DOORWAY_TRANSITION", "unit": "m2", "element_id": "E:door",
         "label": "DRAWING-READ", "net": 0.2, "basis": "1.00 x 0.20"}]}
    finding = {"schema": "URBAN_FIX_ROWS_V1", "task": "F-X-1", "kind": A.CHECKER_FINDING, "finding": "F-X-1",
               "verdict": {"task": "T-1", "gate": "A", "utc": "2026-01-01T00:00Z"}, "candidate_version": A.EXTENDS,
               "rows": [_r(LS, "STR.CONC.BEAM", "m3", 0.096, 0.0256, "DEFAULT",
                           "Checker F-X-1: same band, 0.16 m2 x 0.16 = 0.0256", hand=[0.16, 0.16])]}
    return {"schema": A.PACKAGE_SCHEMA, "method": A.METHOD, "base": A.EXTENDS, "row_bases": [V85],
            "set_names": ["T-1", "T-2", "F-X-1"], "sets": [worker, upturn, finding]}


def test_index_normal_case():
    base = _index()
    new, applied, late, rep = A.apply_index(base, _pkg())
    by = {ln["line_id"]: ln for ln in new["lines"]}
    assert by[LB]["measured_net"] == 0.096 and by[LS]["measured_net"] == 0.0256
    assert by[LS]["method_label"] == "DEFAULT" and "F-X-1" in by[LS]["fill_basis"]
    assert by[LU]["measured_net"] == 9.0 and by[LU]["method_label"] == "DRAWING-READ"
    assert by["L-out"] == base["lines"][3]
    door = new["lines"][-1]
    assert door["item_code"] == "FIN.WP.DOORWAY_TRANSITION" and door["measured_net"] == 0.2 and len(new["lines"]) == 5
    assert rep["checker_finding_sets"][0]["finding"] == "F-X-1" and new["fill"]["checker_finding_sets"] == 1
    assert new["candidate_version"] == A.METHOD and new["extends"] == A.EXTENDS and A.RULE_V8 in new["fill"]["rule"]
    assert not any(ln["class"] == "RELEASED" and ln["measured_net"] == 0 for ln in new["lines"])
    assert {r["line_id"] for r in applied} == {LB, LS, LU}


def _boq(ln):
    return {"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln["unit"],
            "evidence_state": "PROVISIONAL", "measured_net": ln["measured_net"], "bounded_range": None,
            "location": {"element_id": ln["element_id"]}, "gross": None,
            "method_label": ln["method_label"], "fill_basis": ln["fill_basis"]}


def test_boq_view_matches_the_index_view():
    lines = [_boq(ln) for ln in _index()["lines"]]
    new, applied, added, late, rep = A.apply_boq_lines(lines, _pkg())
    by = {ln["line_id"]: ln for ln in new}
    idx = {ln["line_id"]: ln for ln in A.apply_index(_index(), _pkg())[0]["lines"]}
    assert set(by) == set(idx)
    for lid, ln in by.items():
        assert B.line_class(ln) == idx[lid]["class"] and ln["measured_net"] == idx[lid]["measured_net"], lid
    assert by["L-out"] == lines[3] and new[-1]["rule"]["version"] == A.METHOD


def _f(p):
    return p["sets"][2]


@pytest.mark.parametrize("break_it, msg", [
    (lambda p: _f(p)["rows"][0].update(hand=[0.16, 0.60]), "is not the after net"),               # adverse (ac)
    (lambda p: _f(p)["rows"][0].update(hand=[0.16, -0.16]), "positive factors"),
    (lambda p: _f(p)["rows"][0].pop("hand"), "positive factors"),
    (lambda p: _f(p)["rows"][0].update(basis="same band, 0.16 x 0.16"), "does not name the finding"),
    (lambda p: _f(p)["verdict"].pop("utc"), "verdict task / gate / utc"),
    (lambda p: _f(p).update(finding=""), "finding id"),
    (lambda p: _f(p)["rows"][0]["after"].update(net=None), "releases a figure"),
    (lambda p: _f(p)["rows"][0].update(line_id=LB), "bound by T-1 and F-X-1"),                    # adverse (ad)
    (lambda p: p.update(base=V85), "built for"),
    (lambda p: p.update(schema="URBAN_FILL_PACKAGE_V6"), "is not URBAN_FILL_PACKAGE_V7"),
])
def test_adverse_cases_stop_the_run(break_it, msg):
    p = copy.deepcopy(_pkg())
    break_it(p)
    with pytest.raises(B.FillError, match=msg):
        A.apply_index(_index(), p)


def test_finding_row_on_a_stale_before_stops():
    """adverse: the finding row's before must still be the base line (FILL_WIRE_V1 binding underneath)"""
    base = _index()
    base["lines"][1]["measured_net"] = 0.12
    with pytest.raises(B.FillError):
        A.apply_index(base, _pkg())


def test_index_of_another_version_refused():
    base = _index()
    base["candidate_version"] = V85
    with pytest.raises(B.FillError, match="base is"):
        A.apply_index(base, _pkg())


def test_committed_r10_outputs_equal_their_builder():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t770/v3087_index.py"), "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0 and "check: OK" in r.stdout, r.stdout + r.stderr
