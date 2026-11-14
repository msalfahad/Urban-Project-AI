"""T-770 r5: ARCH_TAKEOFF_V3.0.82 (FILL_WIRE_V2, R-T770-3) on a synthetic index (no project data): stacked rows compose
with the row they restate or bind a base line that already carries it; a deferred row is never applied; an added
NOT_APPLICABLE entry is recorded, never 0; adverse cases stop the run. Plus the committed r5 outputs equal their builder."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3081 as B  # noqa: E402
from engine.source import arch_v3082 as A  # noqa: E402

V78 = "ARCH_TAKEOFF_V3.0.78"


def _ln(lid, code, unit, cls="HELD", net=None, label=None, eid=None):
    d = {"binding": None, "class": cls, "element_id": eid or f"E:{lid}", "held_high": None, "held_low": None,
         "item_code": code, "line_id": lid, "measured_net": net, "unbound_records": [], "unit": unit}
    if label:
        d["method_label"] = label
    return d


def _index():
    return {"schema": B.INDEX_SCHEMA, "candidate_version": A.EXTENDS, "lines": [
        _ln("L-a", "STR.EARTH.EXCAVATION", "m3", eid="X:A"),
        _ln("L-b", "STR.CONC.BOUNDARY_PAD", "m3", "RELEASED", 3.12, "SAFETY", eid="X:B"),
        _ln("L-c", "STR.CONC.BOUNDARY_WALL", "m3", eid="X:C"),
        _ln("L-d", "FIN.PAINT", "m2", "RELEASED", 10.0, eid="X:D"),
        _ln("L-e", "STR.CONC.BLINDING", "m3", "RELEASED", 1.0, "SAFETY", eid="X:E")]}


def _blank():
    return {"class": "HELD", "net": None, "low": None, "high": None}


def _pkg():
    first = {"schema": "DELIVERY_FIX_ROWS_V1", "task": "T-1", "candidate_version": V78, "rows": [
        {"line_id": "L-a", "item_code": "STR.EARTH.EXCAVATION", "unit": "m3", "element_id": "X:A",
         "before": _blank(), "after": {"class": "RELEASED", "net": 47.0}, "label": "ESTIMATE", "basis": "70 x 0.4 x 1.67"}],
        "new_lines": [{"family": "B1-06", "item_code": "SITE.DEWATERING", "unit": "item", "net": None,
                       "label": "NOT_APPLICABLE", "basis": "groundwater below formation"},
                      {"family": "B1-01", "item_code": "SITE.CLEARANCE", "unit": "m2", "net": 470.55,
                       "label": "DRAWING-READ", "basis": "plot 15.00 x 31.37"}]}
    second = {"schema": "DELIVERY_FIX_ROWS_V1", "task": "T-2", "candidate_version": "ARCH_TAKEOFF_V3.0.79", "rows": [
        {"line_id": "L-a", "item_code": "STR.EARTH.EXCAVATION", "unit": "m3", "element_id": "X:A",
         "before": {"index_class": "HELD", "fix_row": "T-1", "net": 47.0, "label": "ESTIMATE"},
         "after": {"class": "RELEASED", "net": 46.3}, "label": "ESTIMATE", "basis": "per run type"},
        {"line_id": "L-b", "item_code": "STR.CONC.BOUNDARY_PAD", "unit": "m3", "element_id": "X:B",
         "before": {"index_class": "HELD", "fix_row": "T-9", "net": 3.12, "label": "SAFETY"},
         "after": {"class": "RELEASED", "net": 2.34}, "label": "SAFETY", "basis": "10 x 1.30 x 0.60 x 0.30"},
        {"line_id": "L-c", "item_code": "STR.CONC.BOUNDARY_WALL", "unit": "m3", "element_id": "X:C",
         "before": {"index_class": "HELD", "fix_row": "T-8", "net": 8.4588, "label": "DEFAULT"},
         "after": {"class": "RELEASED", "net": 9.0958}, "label": "DEFAULT", "basis": "band + above footings"}],
        "new_lines": [{"proposed_id": "NEW:STR.CONC.BLINDING:BAND", "item_code": "STR.CONC.BLINDING", "unit": "m3",
                       "net": 2.1147, "label": "ESTIMATE", "basis": "70.49 x 0.30 x 0.10"}]}
    return {"schema": A.PACKAGE_SCHEMA, "base": A.EXTENDS, "row_bases": [V78, "ARCH_TAKEOFF_V3.0.79"],
            "defer": {"L-c": "restates T-8, wired in a later round"}, "sets": [first, second]}


def test_stack_compose_base_bind_defer_and_not_applicable():
    idx = _index()
    new, applied, rep = A.apply_index(idx, _pkg())
    by = {ln["line_id"]: ln for ln in new["lines"]}
    assert by["L-a"]["measured_net"] == 46.3 and "restates T-1 47.0" in by["L-a"]["fill_basis"]
    assert by["L-b"]["measured_net"] == 2.34                          # bound to the base figure T-9 already put there
    assert by["L-c"] == idx["lines"][2]                               # deferred: exactly as the base
    assert by["L-d"] == idx["lines"][3] and by["L-e"] == idx["lines"][4]
    assert len(applied) == 2 and len(new["lines"]) == 7               # two added lines, dewatering NOT a line
    added = new["lines"][5:]
    assert sorted(x["item_code"] for x in added) == ["SITE.CLEARANCE", "STR.CONC.BLINDING"]
    assert not any(x["item_code"] == "SITE.DEWATERING" for x in new["lines"])
    assert [d["line_id"] for d in rep["deferred"]] == ["L-c"] and len(rep["not_applicable"]) == 1
    assert len(rep["stacked_on_row"]) == 1 and len(rep["stacked_on_base"]) == 1
    assert new["candidate_version"] == A.METHOD and new["fill"]["rule"] == A.RULES


def test_adverse_stacked_row_on_a_different_figure_stops():
    p = _pkg()
    p["sets"][1]["rows"][0]["before"]["net"] = 47.5               # T-1 wrote 47.0
    with pytest.raises(A.FillError, match="stale"):
        A.apply_index(_index(), p)


def test_adverse_stacked_row_on_an_absent_task_stops_unless_deferred():
    p = _pkg()
    p["defer"] = {}
    with pytest.raises(A.FillError, match="neither in the package nor in the base"):
        A.apply_index(_index(), p)


def test_adverse_base_carries_another_label_stops():
    idx = _index()
    idx["lines"][1]["method_label"] = "ESTIMATE"                  # the row restates a SAFETY figure
    with pytest.raises(A.FillError, match="neither in the package nor in the base"):
        A.apply_index(idx, _pkg())


def test_adverse_added_line_without_figure_and_not_na_stops():
    p = _pkg()
    p["sets"][0]["new_lines"][0]["label"] = "ESTIMATE"
    with pytest.raises(A.FillError, match="without a figure"):
        A.apply_index(_index(), p)


def test_adverse_deferred_line_no_row_names_and_empty_reason():
    p = _pkg()
    p["defer"]["L-zz"] = "nothing"
    with pytest.raises(A.FillError, match="no row names"):
        A.apply_index(_index(), p)
    p = _pkg()
    p["defer"]["L-c"] = " "
    with pytest.raises(A.FillError, match="needs a reason"):
        A.apply_index(_index(), p)


def test_adverse_wrong_base_and_v1_schema_refused():
    p = _pkg()
    p["base"] = "ARCH_TAKEOFF_V3.0.79"
    with pytest.raises(A.FillError, match="base is"):
        A.apply_index(_index(), p)
    p = _pkg()
    p["schema"] = B.PACKAGE_SCHEMA
    with pytest.raises(A.FillError, match="schema"):
        A.apply_index(_index(), p)


def test_index_composed_row_never_applied_twice():
    new, applied, _ = A.apply_index(_index(), _pkg())
    assert [r["line_id"] for r in applied].count("L-a") == 1
    assert {r["set"] for r in applied if r["line_id"] == "L-a"} == {"T-2"}


def _boq_line(lid, code, unit, state, net, label=None, eid="X"):
    ln = {"line_id": lid, "item_code": code, "unit": unit, "evidence_state": state, "measured_net": net,
          "bounded_range": None, "gross": None, "deductions": [], "additions": [], "item_en": code + " text",
          "location": {"element_id": eid, "room_id": "R1", "room_name_en": "r", "room_name_ar": "r"},
          "calculation": {"formula": "f", "inputs": {"a": 1}}, "rule": {"rule_id": "R", "version": "V"},
          "notes": ""}
    if label:
        ln["method_label"] = label
    return ln


def test_boq_view_added_line_takes_a_base_shape_and_outside_lines_stay():
    lines = [_boq_line("L-a", "STR.EARTH.EXCAVATION", "m3", "BLOCKED_PRECONDITION", None, eid="X:A"),
             _boq_line("L-b", "STR.CONC.BOUNDARY_PAD", "m3", "PROVISIONAL", 3.12, "SAFETY", eid="X:B"),
             _boq_line("L-c", "STR.CONC.BOUNDARY_WALL", "m3", "BLOCKED_PRECONDITION", None, eid="X:C"),
             _boq_line("L-d", "FIN.PAINT", "m2", "MEASURED", 10.0, eid="X:D"),
             _boq_line("L-e", "STR.CONC.BLINDING", "m3", "PROVISIONAL", 1.0, "SAFETY", eid="X:E")]
    new, applied, added, rep = A.apply_boq_lines(copy.deepcopy(lines), _pkg())
    assert new[2] == lines[2] and new[3] == lines[3] and new[4] == lines[4]
    assert new[0]["evidence_state"] == "PROVISIONAL" and new[0]["measured_net"] == 46.3
    extra = {x["item_code"]: x for x in new[5:]}
    assert set(extra) == {"SITE.CLEARANCE", "STR.CONC.BLINDING"}
    assert extra["STR.CONC.BLINDING"]["item_en"] == "STR.CONC.BLINDING text"     # shaped on the blinding line
    assert extra["SITE.CLEARANCE"]["location"]["room_id"] is None
    assert extra["SITE.CLEARANCE"]["calculation"]["inputs"] == {}
    assert extra["SITE.CLEARANCE"]["rule"]["rule_id"] == A.RULE_STACK


def test_committed_r5_outputs_equal_their_builder():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t770/v3082_index.py"), "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0 and "check: OK" in r.stdout, r.stdout + r.stderr


def test_committed_r5_index_named_check_and_families():
    s = json.loads((ROOT / "research/agents_t770/out/V3_0_82_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["blank_in_package_families_after"] == 0
    assert s["named_check"]["finding"] == "F-V776-1" and s["named_check"]["overlap_bound_m3"] <= 0.7506 + 1e-9
    assert s["named_check"]["share_of_b1_excavation"] < 0.01
    assert [d["line_id"] for d in s["stack_report"]["deferred"]] == ["L-6290a9f3d93f38cd46d6"]
    assert s["lines"] == s["lines_before"] + len(s["added"])
