"""T-770 r8: ARCH_TAKEOFF_V3.0.85 (FILL_WIRE_V5, R-T770-6) on a synthetic index and synthetic BOQ lines (no project
data): a row labelled NOT_APPLICABLE_WITH_EVIDENCE with 0 becomes EXCLUDED (never a RELEASED 0); a recalled deferred
added line of an already-wired set is recomputed from its carrier that this package fills, keeps the id it would have
had, and no row of the recalled set is applied again; adverse cases stop the run. Plus the committed r8 outputs equal
their builder."""
from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3081 as B  # noqa: E402
from engine.source import arch_v3085 as A  # noqa: E402

V79, V81 = "ARCH_TAKEOFF_V3.0.79", "ARCH_TAKEOFF_V3.0.81"


def _ln(lid, code, unit, cls="HELD", net=None, lo=None, hi=None):
    return {"binding": None, "class": cls, "element_id": f"E:{lid}", "held_high": hi, "held_low": lo,
            "item_code": code, "line_id": lid, "measured_net": net, "unbound_records": [], "unit": unit}


def _index():
    return {"schema": B.INDEX_SCHEMA, "candidate_version": A.EXTENDS, "lines": [
        _ln("L-r1", "FIN.EXT.FINISH", "m2", lo=40.0, hi=45.0),
        _ln("L-r2", "FIN.EXT.FINISH", "m2"),
        _ln("L-run", "ARCH.FACADE_RUN", "lm"),
        _ln("L-roof", "FIN.ROOF.FINISH", "m2", "RELEASED", 60.0),
        _ln("L-sp", "FIN.SPATTER_DASH", "m2", "RELEASED", 300.0),           # an earlier round's spatter line
        _ln("L-out", "FIN.PAINT", "m2", "RELEASED", 10.0)]}


def _held(lo=None, hi=None):
    return {"class": "HELD", "net": None, "low": lo, "high": hi}


def _r(lid, code, unit, before, after, label, basis):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": f"E:{lid}", "before": before,
            "after": after, "label": label, "basis": basis}


def _recalled():
    """an already-wired set: its row and its first added line were applied earlier; the second was deferred"""
    return {"schema": "URBAN_FIX_ROWS_V1", "task": "T-9", "candidate_version": V81, "rows": [
        _r("L-sp", "FIN.SPATTER_DASH", "m2", _held(), {"class": "RELEASED", "net": 300.0}, "ESTIMATE", "earlier")],
        "new_lines": [
            {"item_code": "FIN.SPATTER_DASH", "unit": "m2", "element_id": "SP:IN", "label": "ESTIMATE", "net": 300.0,
             "basis": "= carrier FIN.PLASTER"},
            {"item_code": "FIN.SPATTER_DASH", "unit": "m2", "element_id": "SP:EX", "label": "ESTIMATE", "net": 99.0,
             "basis": "= carrier FIN.EXT.FINISH; recompute at wiring"}]}


def _pkg():
    ext = {"schema": "T1_FIX_ROWS_V1", "task": "T-1", "candidate_version": V79, "rows": [
        _r("L-r1", "FIN.EXT.FINISH", "m2", _held(40.0, 45.0), {"class": "RELEASED", "net": 42.0}, "MEASURED", "6 x 7"),
        _r("L-r2", "FIN.EXT.FINISH", "m2", _held(), {"class": "RELEASED", "net": 8.5}, "DEFAULT", "parapet 1.20"),
        _r("L-run", "ARCH.FACADE_RUN", "lm", _held(), {"class": "RELEASED", "net": 0.0},
           "NOT_APPLICABLE_WITH_EVIDENCE", "a drawing outline, no face")]}
    roof = {"schema": "DELIVERY_FIX_ROWS_V1", "task": "T-2", "candidate_version": "ARCH_TAKEOFF_V3.0.82", "rows": [
        _r("L-roof", "FIN.ROOF.FINISH", "m2", {"class": "RELEASED", "net": 60.0, "low": None, "high": None},
           {"class": "RELEASED", "net": 55.0}, "DRAWING-READ", "face less dome base")]}
    return {"schema": A.PACKAGE_SCHEMA, "method": A.METHOD, "base": A.EXTENDS,
            "row_bases": [V79, V81, "ARCH_TAKEOFF_V3.0.82"], "set_names": ["T-1", "T-2"],
            "carriers": {"SP:EX": {"carrier": ["FIN.EXT.FINISH", "m2"]}},
            "recall": {"T-9": {"element_ids": ["SP:EX"], "reason": "deferred until its carrier was wired"}},
            "recall_sets": {"T-9": _recalled()}, "sets": [ext, roof]}


def test_index_normal_case():
    base = _index()
    new, applied, late, rep = A.apply_index(base, _pkg())
    by = {ln["line_id"]: ln for ln in new["lines"]}
    assert by["L-r1"]["measured_net"] == 42.0 and by["L-r2"]["measured_net"] == 8.5
    assert by["L-roof"]["measured_net"] == 55.0
    run = by["L-run"]
    assert run["class"] == "EXCLUDED" and run["measured_net"] is None              # never a RELEASED 0
    assert run["excluded_reason"].startswith(A.NA_STATE) and run["method_label"] == A.NOT_APPLICABLE
    assert by["L-sp"] == base["lines"][4] and by["L-out"] == base["lines"][5]      # recalled set's row not re-applied
    assert len(new["lines"]) == len(base["lines"]) + 1
    sp = new["lines"][-1]
    assert sp["item_code"] == "FIN.SPATTER_DASH" and sp["measured_net"] == 50.5     # 42.0 + 8.5, not the set's 99
    assert sp["line_id"] == B.new_line_id("T-9", "NEW:SP:EX", "FIN.SPATTER_DASH", "m2")   # the id it would have had
    assert sp["added_by"] == A.RULE_V6 and "recalled from T-9" in sp["fill_basis"]
    assert rep["na_label_rows"] == {"T-1": 1} and len(rep["recalled"]) == 1
    assert len(applied) == 4 and new["candidate_version"] == A.METHOD and new["extends"] == A.EXTENDS
    assert not any(ln["item_code"] == "FIN.SPATTER_DASH" and "SP:IN" in ln["element_id"] for ln in new["lines"])


def _boq(ln):
    st = {"RELEASED": "PROVISIONAL", "HELD": "BOUNDED_EXPOSURE" if ln["held_low"] is not None else "BLOCKED"}
    return {"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln["unit"],
            "evidence_state": st[ln["class"]], "measured_net": ln["measured_net"],
            "bounded_range": {"low": ln["held_low"], "high": ln["held_high"]} if ln["held_low"] is not None else None,
            "location": {"element_id": ln["element_id"]}, "gross": None}


def test_boq_view_matches_the_index_view():
    lines = [_boq(ln) for ln in _index()["lines"]]
    new, applied, added, late, rep = A.apply_boq_lines(lines, _pkg())
    by = {ln["line_id"]: ln for ln in new}
    assert by["L-run"]["evidence_state"] == A.NA_STATE and by["L-run"]["measured_net"] is None
    assert by["L-out"] == lines[5] and by["L-sp"] == lines[4]
    idx = {ln["line_id"]: ln for ln in A.apply_index(_index(), _pkg())[0]["lines"]}
    assert set(by) == set(idx)
    for lid, ln in by.items():
        assert B.line_class(ln) == idx[lid]["class"], lid
        if idx[lid]["class"] == "RELEASED":
            assert ln["measured_net"] == idx[lid]["measured_net"], lid
    sp = new[-1]
    assert sp["rule"]["rule_id"] == A.RULE_V6 and sp["rule"]["version"] == A.METHOD


@pytest.mark.parametrize("break_it, msg", [
    (lambda p: p["sets"][0]["rows"][2]["after"].update(net=1.5), "only a RELEASED 0"),           # adverse (v)
    (lambda p: p["sets"][0]["rows"][2].update(basis=" "), "lacks basis|evidence basis"),
    (lambda p: p["sets"][0]["rows"][1].update(after={"class": "HELD", "low": 8.0, "high": 9.0}), "not closed"),
    (lambda p: p["recall"]["T-9"].update(element_ids=["SP:NOPE"]), "occurs 0 times"),             # adverse (w)
    (lambda p: p["recall"]["T-9"].update(element_ids=["SP:EX", "SP:EX"]), "named twice"),
    (lambda p: p["recall"]["T-9"].update(reason=""), "needs element ids and a reason"),
    (lambda p: p["recall_sets"].pop("T-9"), "differ"),
    (lambda p: (p["set_names"].append("T-9"), p["sets"].append(_recalled())), "also a set of this package"),
    (lambda p: p.update(base="ARCH_TAKEOFF_V3.0.83"), "built for"),
    (lambda p: p.update(schema="URBAN_FILL_PACKAGE_V4"), "is not URBAN_FILL_PACKAGE_V5"),
])
def test_adverse_cases_stop_the_run(break_it, msg):
    p = copy.deepcopy(_pkg())
    break_it(p)
    with pytest.raises(B.FillError, match=msg):
        A.apply_index(_index(), p)


def test_na_label_row_never_drops_a_figure():
    """adverse: the NOT_APPLICABLE reading binds a HELD line only; a RELEASED figure stops the run"""
    base = _index()
    base["lines"][2] = _ln("L-run", "ARCH.FACADE_RUN", "lm", "RELEASED", 7.0)
    p = _pkg()
    p["sets"][0]["rows"][2]["before"] = {"class": "RELEASED", "net": 7.0, "low": None, "high": None}
    with pytest.raises(B.FillError, match="only on a HELD line"):
        A.apply_index(base, p)


def test_index_of_another_version_refused():
    base = _index()
    base["candidate_version"] = "ARCH_TAKEOFF_V3.0.83"
    with pytest.raises(B.FillError, match="base is"):
        A.apply_index(base, _pkg())


def test_committed_r8_outputs_equal_their_builder():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t770/v3085_index.py"), "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0 and "check: OK" in r.stdout, r.stdout + r.stderr
