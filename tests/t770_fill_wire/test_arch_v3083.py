"""T-770 r6: ARCH_TAKEOFF_V3.0.83 (FILL_WIRE_V3, R-T770-4) on a synthetic index and synthetic BOQ lines (no project
data): sets named by the package, carried rows, NOT_APPLICABLE rows -> EXCLUDED with evidence (never 0), the one safety
line restated, a basis correction that never touches the figure; adverse cases stop the run. Plus the committed r6
outputs equal their builder."""
from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3081 as B  # noqa: E402
from engine.source import arch_v3083 as A  # noqa: E402

V79, V81 = "ARCH_TAKEOFF_V3.0.79", "ARCH_TAKEOFF_V3.0.81"


def _ln(lid, code, unit, cls="HELD", net=None, label=None, lo=None, hi=None):
    d = {"binding": None, "class": cls, "element_id": f"E:{lid}", "held_high": hi, "held_low": lo,
         "item_code": code, "line_id": lid, "measured_net": net, "unbound_records": [], "unit": unit}
    if label:
        d["method_label"] = label
    return d


def _index():
    return {"schema": B.INDEX_SCHEMA, "candidate_version": A.EXTENDS, "lines": [
        _ln("L-beam", "STR.CONC.BEAM", "m3", lo=0.44, hi=0.55),
        _ln("L-wall", "STR.CONC.BOUNDARY_WALL", "m3", lo=5.6, hi=11.0),
        _ln("L-safe", "STR.CONC.SAFETY", "m3", "RELEASED", 1.0, "SAFETY"),
        _ln("L-plas", "FIN.PLASTER", "m2", lo=13.7, hi=21.6),
        _ln("L-glue", "MAS.GLUE.AAC", "kg"),
        _ln("L-blk", "MAS.BLOCK", "m2"),
        _ln("L-done", "STR.EARTH.EXCAVATION", "m3", "RELEASED", 46.3, "ESTIMATE"),
        _ln("L-out", "FIN.PAINT", "m2", "RELEASED", 10.0)]}


def _r(lid, code, unit, before, after, label, basis):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": f"E:{lid}", "before": before,
            "after": after, "label": label, "basis": basis}


def _held(lo, hi):
    return {"class": "HELD", "net": None, "low": lo, "high": hi}


def _pkg():
    conc = {"schema": "T757_FIX_ROWS_V1", "task": "T-1", "candidate_version": V79, "rows": [
        _r("L-beam", "STR.CONC.BEAM", "m3", _held(0.44, 0.55), {"class": "RELEASED", "net": 0.44}, "DRAWING-READ",
           "0.2 x 4.4 x 0.5"),
        _r("L-wall", "STR.CONC.BOUNDARY_WALL", "m3", _held(5.6, 11.0), {"class": "RELEASED", "net": 8.4588},
           "DEFAULT", "band 0.20 x 0.60")],
        "ignored_small": {"t1_sum_m3": 0.43, "t2_width_sum_m3": 0.77, "total_m3": 1.2},
        "safety_line": {"line_id": "NEW:STR.CONC.SAFETY", "item_code": "STR.CONC.SAFETY", "unit": "m3",
                        "label": "SAFETY", "before": 1.0, "after": 1.2, "basis": "ONE safety line restated"}}
    plas = {"candidate_version": V81, "rows": [   # no schema, no task: named by the package (k)
        dict(_r("L-plas", "FIN.PLASTER", "m2", _held(13.7, 21.6), {"class": "RELEASED", "net": 17.64}, "DEFAULT",
                "run 7.2 x 3.00 - 3.96; part A 16.5255 (4.0927 x 4.04)"), set="PLASTER_WET")]}
    mas = {"candidate_version": V81, "rows": [
        _r("L-glue", "MAS.GLUE.AAC", "kg", _held(None, None),
           {"class": "EXCLUDED", "net": None, "reason": A.NA_STATE}, "NOT_APPLICABLE", "no white wall in this host"),
        _r("L-blk", "MAS.BLOCK", "m2", _held(None, None), {"class": "RELEASED", "net": 101.0}, "DEFAULT",
           "sum of components")]}
    earlier = {"schema": "DELIVERY_FIX_ROWS_V1", "task": "T-4", "candidate_version": V79, "rows": [
        _r("L-done", "STR.EARTH.EXCAVATION", "m3", {"index_class": "HELD", "fix_row": "T-0", "net": 47.0,
                                                     "label": "ESTIMATE"},
           {"class": "RELEASED", "net": 46.3}, "ESTIMATE", "wired in an earlier round"),
        _r("L-wall", "STR.CONC.BOUNDARY_WALL", "m3", {"index_class": "HELD", "fix_row": "T-1", "net": 8.4588,
                                                       "label": "DEFAULT"},
           {"class": "RELEASED", "net": 9.0958}, "DEFAULT", "+0.637 above the footing tops")],
        "new_lines": [{"proposed_id": "NEW:X", "item_code": "STR.CONC.BLINDING", "unit": "m3", "net": 2.1,
                       "label": "ESTIMATE", "basis": "added in an earlier round"}]}
    return {"schema": A.PACKAGE_SCHEMA, "method": A.METHOD, "base": A.EXTENDS, "row_bases": [V79, V81],
            "set_names": ["T-1", "T-2", "T-3", "T-4"], "carry": {"T-4": ["L-wall"]},
            "basis_corrections": {"L-plas": {"old": "16.5255 (4.0927", "new": "16.5345 (4.0927",
                                             "source": "Checker F-1"}},
            "sets": [conc, plas, mas, earlier]}


def test_index_normal_case():
    base = _index()
    new, applied, rep = A.apply_index(base, _pkg())
    by = {ln["line_id"]: ln for ln in new["lines"]}
    assert len(new["lines"]) == len(base["lines"])           # carried set adds nothing again
    assert by["L-beam"]["measured_net"] == 0.44 and by["L-beam"]["method_label"] == "DRAWING-READ"
    assert by["L-wall"]["measured_net"] == 9.0958             # composed with the T-1 point (R-T770-3 h1)
    assert by["L-safe"]["measured_net"] == 1.2 and by["L-safe"]["method_label"] == "SAFETY"
    assert by["L-glue"]["class"] == "EXCLUDED" and by["L-glue"]["measured_net"] is None
    assert by["L-glue"]["excluded_reason"].startswith(A.NA_STATE)
    assert by["L-plas"]["measured_net"] == 17.64 and "16.5345 (4.0927" in by["L-plas"]["fill_basis"]
    assert "16.5255" not in by["L-plas"]["fill_basis"]
    assert by["L-done"] == base["lines"][6] and by["L-out"] == base["lines"][7]   # outside lines untouched
    assert rep["carried"] == {"T-4": ["L-wall"]} and len(rep["restated_safety"]) == 1
    assert rep["source_schemas"]["T-2"] is None and new["candidate_version"] == A.METHOD
    assert len(applied) == 6


def _boq(ln):
    st = {"RELEASED": "PROVISIONAL", "HELD": "BOUNDED_EXPOSURE" if ln["held_low"] is not None else "BLOCKED"}
    d = {"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln["unit"],
         "evidence_state": st[ln["class"]], "measured_net": ln["measured_net"],
         "bounded_range": {"low": ln["held_low"], "high": ln["held_high"]} if ln["held_low"] is not None else None,
         "location": {"element_id": ln["element_id"]}, "gross": None}
    if ln.get("method_label"):
        d["method_label"] = ln["method_label"]
    return d


def test_boq_view_matches_the_index_view():
    lines = [_boq(ln) for ln in _index()["lines"]]
    new, applied, added, rep = A.apply_boq_lines(lines, _pkg())
    by = {ln["line_id"]: ln for ln in new}
    assert not added and len(new) == len(lines)
    assert by["L-glue"]["evidence_state"] == A.NA_STATE and by["L-glue"]["measured_net"] is None
    assert by["L-safe"]["measured_net"] == 1.2 and by["L-wall"]["measured_net"] == 9.0958
    assert by["L-blk"]["evidence_state"] == "PROVISIONAL" and by["L-out"] == lines[7]
    idx = {ln["line_id"]: ln for ln in A.apply_index(_index(), _pkg())[0]["lines"]}
    for lid, ln in by.items():
        assert B.line_class(ln) == idx[lid]["class"]
        if idx[lid]["class"] == "RELEASED":
            assert ln["measured_net"] == idx[lid]["measured_net"]


@pytest.mark.parametrize("break_it, msg", [
    (lambda p: p["sets"][2]["rows"][0]["after"].update(reason="OTHER"), "only NOT_APPLICABLE"),
    (lambda p: p["sets"][2]["rows"][0].update(before=_held(1.0, 2.0)), "stale"),
    (lambda p: p.update(carry={"T-4": ["L-nope"]}), "carried line"),
    (lambda p: p["sets"][0]["safety_line"].update(after=1.5), "is not max"),
    (lambda p: p["sets"][0]["safety_line"].update(before=2.0), "binds 1 base safety line"),
    (lambda p: p["sets"][0]["ignored_small"].update(total_m3=1.5), "equal to its parts"),
    (lambda p: p["basis_corrections"]["L-plas"].update(old="99.9"), "basis correction"),
    (lambda p: p["sets"][1].update(schema="SOMETHING_ELSE"), "not of the fix-row shape"),
    (lambda p: p["sets"][1].update(task="T-9"), "package names it"),
    (lambda p: p.update(set_names=["T-1", "T-2", "T-3"]), "set_names"),
    (lambda p: p.update(base="ARCH_TAKEOFF_V3.0.81"), "built for"),
    (lambda p: p.update(carry={}), "neither in the package nor in the base"),   # without the carry T-4 rows wired earlier apply again
])
def test_adverse_cases_stop_the_run(break_it, msg):
    p = copy.deepcopy(_pkg())
    break_it(p)
    with pytest.raises(B.FillError, match=msg):
        A.apply_index(_index(), p)


def test_not_applicable_never_drops_a_figure():
    base = _index()
    base["lines"][4] = _ln("L-glue", "MAS.GLUE.AAC", "kg", "RELEASED", 43.6)
    p = _pkg()
    p["sets"][2]["rows"][0]["before"] = {"class": "RELEASED", "net": 43.6, "low": None, "high": None}
    with pytest.raises(B.FillError, match="only on a HELD line"):
        A.apply_index(base, p)


def test_committed_r6_outputs_equal_their_builder():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t770/v3083_index.py"), "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0 and "check: OK" in r.stdout, r.stdout + r.stderr
