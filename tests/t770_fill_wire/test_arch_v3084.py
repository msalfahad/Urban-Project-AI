"""T-770 r7: ARCH_TAKEOFF_V3.0.84 (FILL_WIRE_V4, R-T770-5) on a synthetic index and synthetic BOQ lines (no project
data): a rows_detail set with an ADD entry, a form alternative EXCLUDED_WITH_REASON (never 0), a ranged OPTIONAL added
line kept HELD, carrier-derived lines recomputed on the wired candidate (a carrier the same package fills counts with
its new figure), a deferred added line never written; adverse cases stop the run. Plus the committed r7 outputs equal
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
from engine.source import arch_v3084 as A  # noqa: E402

V81 = "ARCH_TAKEOFF_V3.0.81"


def _ln(lid, code, unit, cls="HELD", net=None, label=None, lo=None, hi=None):
    d = {"binding": None, "class": cls, "element_id": f"E:{lid}", "held_high": hi, "held_low": lo,
         "item_code": code, "line_id": lid, "measured_net": net, "unbound_records": [], "unit": unit}
    if label:
        d["method_label"] = label
    return d


def _index():
    return {"schema": B.INDEX_SCHEMA, "candidate_version": A.EXTENDS, "lines": [
        _ln("L-tread", "FIN.MARBLE.TREAD", "m2"),
        _ln("L-slope", "FIN.STAIR.SKIRTING.SLOPED", "lm"),
        _ln("L-open", "FIN.STAIR.SKIRTING.ZIGZAG", "lm"),
        _ln("L-step", "FIN.STAIR.STEP_LM", "lm", lo=2.0, hi=3.0),
        _ln("L-step2", "FIN.STAIR.STEP_LM", "lm", "RELEASED", 10.0, "DRAWING-READ"),
        _ln("L-plas", "FIN.PLASTER", "m2", "RELEASED", 100.0, "DEFAULT"),
        _ln("L-ext", "FIN.EXT.FINISH", "m2", lo=5.0, hi=6.0),
        _ln("L-ceil", "FIN.CEILING", "m2"),
        _ln("L-out", "FIN.PAINT", "m2", "RELEASED", 10.0),
        _ln("L-door", "DOOR.INTERNAL.PVC", "pcs", "RELEASED", 3.0)]}


def _held(lo=None, hi=None):
    return {"class": "HELD", "net": None, "low": lo, "high": hi}


def _r(lid, code, unit, before, after, label, basis, **kw):
    return dict({"line_id": lid, "item_code": code, "unit": unit, "element_id": f"E:{lid}", "before": before,
                 "after": after, "label": label, "basis": basis, "set": "STAIR"}, **kw)


def _pkg():
    stair = {"task": "T-1", "candidate_version": V81, "rows": 5, "rows_detail": [   # no schema: rows_detail (p)
        _r("L-tread", "FIN.MARBLE.TREAD", "m2", _held(), {"class": "RELEASED", "net": 3.0}, "DRAWING-READ", "10 x 0.30"),
        _r("L-slope", "FIN.STAIR.SKIRTING.SLOPED", "lm", _held(),
           {"class": "EXCLUDED", "net": None, "reason": "FORM_ALTERNATIVE_X"}, "NOT_APPLICABLE",
           "the zigzag form carries the strip; never additive"),
        _r("L-open", "FIN.STAIR.SKIRTING.ZIGZAG", "lm", _held(),
           {"class": "EXCLUDED", "net": None, "reason": A.NA_STATE}, "NOT_APPLICABLE", "open side, no wall"),
        _r("L-step", "FIN.STAIR.STEP_LM", "lm", _held(2.0, 3.0), {"class": "RELEASED", "net": 2.5}, "ESTIMATE",
           "inside the range"),
        {"action": "ADD", "line_id": None, "before": None, "item_code": "FIN.MARBLE.LANDING", "unit": "m2",
         "element_id": "LD:1", "after": {"class": "RELEASED", "net": 1.4375}, "label": "MEASURED",
         "basis": "1.25 x 1.15", "set": "STAIR"}]}
    ceil = {"schema": "URBAN_FIX_ROWS_V1", "task": "T-2", "candidate_version": V81, "rows": [
        _r("L-ceil", "FIN.CEILING", "m2", _held(), {"class": "RELEASED", "net": 40.0}, "DEFAULT", "room 5 x 8")]}
    miss = {"schema": "URBAN_FIX_ROWS_V1", "task": "T-3", "candidate_version": V81, "rows": [], "new_lines": [
        {"item_code": "FIN.SPATTER_DASH", "unit": "m2", "element_id": "SP:IN", "label": "ESTIMATE", "net": 99.0,
         "basis": "= carrier FIN.PLASTER"},
        {"item_code": "FIN.SPATTER_DASH", "unit": "m2", "element_id": "SP:EX", "label": "ESTIMATE", "net": 50.0,
         "basis": "= carrier FIN.EXT.FINISH"},
        {"item_code": "FIN.CEILING.GYPSUM", "unit": "m2", "element_id": "GY", "label": "ESTIMATE", "net": 0.0,
         "basis": "= FIN.CEILING (board item, not additive)"},
        {"item_code": "FIN.STAIR.NOSING", "unit": "lm", "element_id": "NO", "label": "ESTIMATE", "net": 11.0,
         "basis": "= STEP_LM + landing edges"},
        {"item_code": "MAS.MESH_STRIP", "unit": "lm", "element_id": "MESH", "label": "ESTIMATE", "low": 8.0,
         "high": 11.0, "optional": True, "basis": "every 3rd course"},
        {"item_code": "MEP.SAN.WC", "unit": "pcs", "element_id": "WC", "label": "MEASURED", "net": 2.0,
         "basis": "counted"}]}
    return {"schema": A.PACKAGE_SCHEMA, "method": A.METHOD, "base": A.EXTENDS, "row_bases": [V81],
            "set_names": ["T-1", "T-2", "T-3"],
            "carriers": {"SP:IN": {"carrier": ["FIN.PLASTER", "m2"]}, "GY": {"carrier": ["FIN.CEILING", "m2"]},
                         "NO": {"carrier": ["FIN.STAIR.STEP_LM", "lm"], "plus": 1.0, "plus_source": "landing edges"}},
            "defer_added": {"SP:EX": "carrier still HELD"},
            "sets": [stair, ceil, miss]}


def _added(new, base):
    return {ln["item_code"] + ":" + ln["element_id"].split(":", 1)[1]: ln for ln in new["lines"][len(base["lines"]):]}


def test_index_normal_case():
    base = _index()
    new, applied, late, rep = A.apply_index(base, _pkg())
    by = {ln["line_id"]: ln for ln in new["lines"]}
    assert by["L-tread"]["measured_net"] == 3.0 and by["L-step"]["measured_net"] == 2.5
    assert by["L-slope"]["class"] == "EXCLUDED" and by["L-slope"]["measured_net"] is None
    assert by["L-slope"]["excluded_reason"].startswith("EXCLUDED_WITH_REASON (FORM_ALTERNATIVE_X")
    assert by["L-open"]["excluded_reason"].startswith(A.NA_STATE)
    assert by["L-ext"] == base["lines"][6] and by["L-out"] == base["lines"][8]       # outside lines untouched
    add = _added(new, base)
    assert add["FIN.MARBLE.LANDING:NEW:LD:1"]["measured_net"] == 1.4375
    assert add["FIN.SPATTER_DASH:NEW:SP:IN"]["measured_net"] == 100.0           # recomputed, not the set's 99
    assert add["FIN.CEILING.GYPSUM:NEW:GY"]["measured_net"] == 40.0             # carrier filled in this package
    assert add["FIN.STAIR.NOSING:NEW:NO"]["measured_net"] == 13.5               # 2.5 + 10.0 + 1.0
    mesh = add["MAS.MESH_STRIP:NEW:MESH"]
    assert mesh["class"] == "HELD" and (mesh["held_low"], mesh["held_high"]) == (8.0, 11.0)
    assert mesh["measured_net"] is None and "OPTIONAL" in mesh["fill_basis"]
    assert not any(k.startswith("FIN.SPATTER_DASH:NEW:SP:EX") for k in add)   # deferred: never written, never 0
    assert len(new["lines"]) == len(base["lines"]) + 6
    assert len(rep["deferred_added"]) == 1 and len(rep["excluded_with_reason"]) == 1
    assert len(applied) == 5 and new["candidate_version"] == A.METHOD and new["extends"] == A.EXTENDS
    ids = [ln["line_id"] for ln in new["lines"]]
    assert len(set(ids)) == len(ids)


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
    new, applied, added, late, rep = A.apply_boq_lines(lines, _pkg())
    by = {ln["line_id"]: ln for ln in new}
    assert by["L-slope"]["evidence_state"] == A.EXCLUDED_STATE and by["L-slope"]["measured_net"] is None
    assert by["L-out"] == lines[8]
    idx = {ln["line_id"]: ln for ln in A.apply_index(_index(), _pkg())[0]["lines"]}
    assert set(by) == set(idx)
    for lid, ln in by.items():
        assert B.line_class(ln) == idx[lid]["class"], lid
        if idx[lid]["class"] == "RELEASED":
            assert ln["measured_net"] == idx[lid]["measured_net"], lid
        if idx[lid]["class"] == "HELD" and idx[lid]["held_low"] is not None:
            assert (ln["bounded_range"]["low"], ln["bounded_range"]["high"]) == (idx[lid]["held_low"],
                                                                                 idx[lid]["held_high"])


def _no_defer(p):
    p["defer_added"] = {}


@pytest.mark.parametrize("break_it, msg", [
    (lambda p: p["sets"][0].update(rows=4), "rows count"),
    (lambda p: p["sets"][0]["rows_detail"][1]["after"].update(reason=""), "a reason and a basis"),
    (lambda p: p["sets"][0]["rows_detail"][1].update(label="DEFAULT"), "label NOT_APPLICABLE"),
    (lambda p: p["sets"][0]["rows_detail"][1].update(before=_held(1.0, 2.0)), "stale"),
    (lambda p: p["sets"][0]["rows_detail"][4].update(before=_held()), "reads a before"),
    (lambda p: p["sets"][0]["rows_detail"][4].update(action="MOVE"), "is not ADD"),
    (lambda p: (_no_defer(p), p["carriers"].update({"SP:EX": {"carrier": ["FIN.EXT.FINISH", "m2"]}})), "not closed"),
    (lambda p: p["sets"][1].update(rows=[]), "not closed"),        # FIN.CEILING left HELD: the gypsum carrier is open
    (lambda p: p["carriers"].update({"NOPE": {"carrier": ["FIN.PLASTER", "m2"]}}), "carrier"),
    (lambda p: p["carriers"]["SP:IN"].update(carrier=["FIN.PLASTER", "lm"]), "is not \\[item code"),
    (lambda p: p["carriers"]["NO"].update(plus_source=""), "addition needs"),
    (lambda p: p["defer_added"].update({"SP:EX": " "}), "needs a reason"),
    (lambda p: p["sets"][2]["new_lines"][4].update(low=12.0), "0 <= low <= high"),
    (lambda p: [n.pop("element_id") for n in p["sets"][2]["new_lines"][5:]], "needs an element id"),
    (lambda p: p.update(base="ARCH_TAKEOFF_V3.0.82"), "built for"),
    (lambda p: p.update(schema="URBAN_FILL_PACKAGE_V3"), "is not URBAN_FILL_PACKAGE_V4"),
])
def test_adverse_cases_stop_the_run(break_it, msg):
    p = copy.deepcopy(_pkg())
    break_it(p)
    with pytest.raises(B.FillError, match=msg):
        A.apply_index(_index(), p)


def test_excluded_with_reason_never_drops_a_figure():
    base = _index()
    base["lines"][1] = _ln("L-slope", "FIN.STAIR.SKIRTING.SLOPED", "lm", "RELEASED", 4.0)
    p = _pkg()
    p["sets"][0]["rows_detail"][1]["before"] = {"class": "RELEASED", "net": 4.0, "low": None, "high": None}
    with pytest.raises(B.FillError, match="only on a HELD line"):
        A.apply_index(base, p)


def test_committed_r7_outputs_equal_their_builder():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t770/v3084_index.py"), "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0 and "check: OK" in r.stdout, r.stdout + r.stderr
