"""T-246: ARCH_TAKEOFF_V3.0.36 (DEDUCTION_LISTING: canonical deduction lists by opening / element id; no quantity
moves) on a hand-calculated NON-Alsenan villa (V246).

Villa V246, by hand (own figures; nothing from the development villa):
  R1 skirting   perimeter 20.00 lm; door D1 0.90, door D2 0.80; window W1 1.20 wide at the floor: glazing half 0.60
                (listed) + threshold half 0.60 (deducted by the net, NOT listed): net 20.00 - 0.90 - 0.80 - 0.60 - 0.60
                = 17.10 lm. The candidate lists 1.70 + 0.60 = 2.30 only: 20.00 - 2.30 = 17.70 != 17.10 (short 0.60).
                W1 reading: sill 1.00 above the floor (SKIRTED) -> both halves listed with physical_check UNRESOLVED.
  R2 plaster    wall face 46.00 m2; door D3 0.90 x 2.20 = 1.98; window W2 1.20 x 1.50 = 1.80: net 42.22 m2; the
                candidate's list is empty (the openings only in calculation.inputs).
  R3 porcelain  face 30.00 m2; stair treads 4.50; landing split out 2.25: net 23.25; the candidate writes gross = net
                23.25 beside a list of 4.50 -> gross restated to the face 30.00.
  R4 skirting   gross 12.00, a band passage P1 3.00 wider than its stretch on the boundary (2.40): signed ledger row
                -0.60 kept as an ADDITION: 12.00 - 3.00 + 0.60 = 9.60 = net.
  Footing F1    untouched (byte-identical).
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3036 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402
from tools import t330_deductions_check as C  # noqa: E402

PID, REV = "villa-v246", "e" * 64
DOCS = [{"file": "v246_plan.dxf", "sha256": "d" * 64}]
SRC = [{"task": t, "file": f"research/v246/{t}.csv", "sha256": str(i) * 64, "merge_commit": chr(97 + i) * 40,
        "checker_run": f"checker run {70 + i} (Gate A PASS)"} for i, t in enumerate(("T-341", "T-345", "T-296"), 1)]


def _line(code, eid, unit, gross, net, ded, trade, ev="MEASURED"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=eid, floor="GF", physical_element=eid, gross=gross,
                        deductions=ded, formula=f"{eid}", documents=DOCS, rule_id="R", rule_version="1",
                        notes="v246", item_en=eid, item_ar=eid, trade=trade)


def lines_3035():
    return [_line("FIN.SKIRTING", "R1:skirting", "lm", 20.0, 17.1,
                  [{"lm": 1.7, "what": "door / passage openings"}, {"lm": 0.6, "what": "glazing edge"}], "FLOOR_FINISH"),
            _line("FIN.PLASTER", "R2:plaster", "m2", 46.0, 42.22, [], "PLASTER"),
            _line("FIN.FLOOR.PORCELAIN", "R3:floor", "m2", 23.25, 23.25, [{"m2": 4.5, "what": "stair treads"}],
                  "FLOOR_FINISH"),
            _line("FIN.SKIRTING", "R4:skirting", "lm", 12.0, 9.6, [{"lm": 2.4, "what": "door / passage openings"}],
                  "FLOOR_FINISH"),
            _line("STR.CONC.FOOTING", "F1", "m3", 3.0, 3.0, [], "CONCRETE")]


def _id(lines, eid):
    return next(x["line_id"] for x in lines if x["location"]["element_id"] == eid)


def _it(i, q, role="DEDUCTION", **kw):
    return dict({"role": role, "id": i, "qty": q, "source": "hand"}, **kw)


def _row(lines, eid, items, action="LIST_FILL", after=None, tasks=("T-341",)):
    b = next(x for x in lines if x["location"]["element_id"] == eid)
    r = {"action": action, "line_id": b["line_id"], "status": "RECONCILED", "source_tasks": list(tasks),
         "expect": {"item_code": b["item_code"], "element_id": eid, "unit": b["unit"],
                    "evidence_state": b["evidence_state"], "gross": b["gross"], "measured_net": b["measured_net"]},
         "items": items}
    if after is not None:
        r["gross_after"] = after
    return r


W1 = dict(census_id="W1", physical_check="UNRESOLVED", physical_why="sill 1.00 above the floor (SKIRTED)")


def inputs(lines):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": SRC, "lines": [
        _row(lines, "R1:skirting", [_it("OP-1", 0.9, census_id="D1"), _it("OP-2", 0.8, census_id="D2"),
                                    _it("OP-3#glazing-half", 0.6, **W1), _it("OP-3#threshold-half", 0.6, **W1)],
             tasks=("T-341", "T-296")),
        _row(lines, "R2:plaster", [_it("D3", 1.98), _it("W2", 1.8)]),
        _row(lines, "R3:floor", [_it("STAIR:F1", 4.5), _it("LANDING", 2.25)], "GROSS_RESTATE", 30.0, ("T-345",)),
        _row(lines, "R4:skirting", [_it("P1", 3.0), _it("PASSAGE_RUN_RESIDUAL:R4", 0.6, role="ADDITION")])]}


def run(lines=None, doc=None):
    lines = lines or lines_3035()
    d = A.load_inputs(doc or inputs(lines), PID)
    ch, log = A.changes_for(d, lines)
    out, ident = A.integrate(lines, ch)
    return lines, out, ident, ch, log


# ------------------------------------------------------------------------------------------------ normal
def test_every_listed_line_closes_and_nothing_moves():
    l35, l36, ident, ch, log = run()
    by = {x["location"]["element_id"]: x for x in l36}
    assert ident["replaced"] == 4 and ident["outside_rows"] == 1 and ident["lists"] == {"lines": 4, "items": 10}
    for eid, gross, n in (("R1:skirting", 20.0, 4), ("R2:plaster", 46.0, 2), ("R3:floor", 30.0, 2),
                          ("R4:skirting", 12.0, 2)):
        ln = by[eid]
        assert ln["gross"] == gross and len(ln["deductions"]) + len(ln["additions"]) == n
        d = sum(x["qty"] for x in ln["deductions"]) - sum(x["qty"] for x in ln["additions"])
        assert abs(ln["gross"] - d - ln["measured_net"]) < 1e-9
    # hand: R1 20.00 - (0.90 + 0.80 + 0.60 + 0.60) = 17.10; R3 30.00 - 4.50 - 2.25 = 23.25; R4 12.00 - 3.00 + 0.60
    assert by["R1:skirting"]["measured_net"] == 17.1 and by["R3:floor"]["measured_net"] == 23.25
    assert A304.code_totals(l35) == A304.code_totals(l36)
    assert [A30._qty(x) for x in l35] == [A30._qty(x) for x in l36]
    assert A30.line_sha(l35[4]) == A30.line_sha(l36[4])


def test_t330_check_reads_every_list_ok():
    l35, l36, *_ = run()
    before = C.check_lines(l35)
    after = C.check_lines(l36)
    assert before["flagged"] == 4 and after["flagged"] == 0 and after["refused"] == 0
    assert after["categories"]["OK"] == 5


def test_window_halves_carry_the_physical_reading_and_are_not_applied():
    _l35, l36, _i, ch, log = run()
    r1 = next(x for x in l36 if x["location"]["element_id"] == "R1:skirting")
    flagged = [x["id"] for x in r1["deductions"] if x.get("physical_check") == "UNRESOLVED"]
    assert flagged == ["OP-3#glazing-half", "OP-3#threshold-half"] and r1["measured_net"] == 17.1
    assert log["physical"] == {"UNRESOLVED": 2}
    led = A.ledger_rows(ch)
    assert next(r for r in led if r["element_id"] == "R1:skirting")["unresolved_items"] == flagged


def test_write_files_and_diff_text_only(tmp_path):
    l35 = lines_3035()
    d = A.load_inputs(inputs(l35), PID)
    ch, log = A.changes_for(d, l35)
    names, ident, led = A.write(tmp_path, l35, ch, log)
    assert "V3_0_36_BOQ_LINES.json" in names and led["integration_package"] is True
    diff = (tmp_path / "V3_0_36_DIFF.csv").read_text(encoding="utf-8")
    assert diff.count("CHANGED_TEXT_ONLY") == 4 and ",CHANGED," not in diff
    run_ = json.loads((tmp_path / "V3_0_36_RUN.json").read_text(encoding="utf-8"))
    assert run_["totals_moved_by_code"] == {} and run_["released_default"] is False


# ------------------------------------------------------------------------------------------------ adverse
def test_unlisted_deduction_refused():
    l35 = lines_3035()
    doc = inputs(l35)
    doc["lines"][0]["items"] = doc["lines"][0]["items"][:3]          # the threshold half left out
    with pytest.raises(A.InputsError, match="unlisted deduction is refused"):
        A.load_inputs(doc)


def test_threshold_deducted_twice_refused():
    l35 = lines_3035()
    doc = inputs(l35)
    doc["lines"][0]["items"].append(_it("OP-3#threshold-half", 0.6, **W1))
    with pytest.raises(A.InputsError, match="listed twice"):
        A.load_inputs(doc)


def test_negative_deduction_refused():
    l35 = lines_3035()
    doc = inputs(l35)
    doc["lines"][3]["items"][1] = _it("PASSAGE_RUN_RESIDUAL:R4", -0.6)
    with pytest.raises(A.InputsError, match="ADDITION"):
        A.load_inputs(doc)


def test_stale_binding_stops():
    l35 = lines_3035()
    doc = inputs(l35)
    l35[1] = _line("FIN.PLASTER", "R2:plaster", "m2", 46.0, 41.0, [], "PLASTER")     # re-netted since the ledger
    d = A.load_inputs(doc)
    with pytest.raises(A.InputsError, match="stale binding"):
        A.changes_for(d, l35)


def test_restated_gross_below_the_field_refused():
    l35 = lines_3035()
    doc = inputs(l35)
    doc["lines"][2]["gross_after"] = 20.0
    with pytest.raises(A.InputsError, match="never shrinks"):
        A.load_inputs(doc)


def test_held_line_not_listed():
    l35 = lines_3035()
    doc = inputs(l35)
    doc["lines"][1]["expect"]["evidence_state"] = "BLOCKED_RFI"
    with pytest.raises(A.InputsError, match="held / excluded"):
        A.load_inputs(doc)


def test_unit_slip_cannot_close():
    l35 = lines_3035()
    doc = inputs(l35)
    doc["lines"][0]["items"][0]["qty"] = 900.0                       # mm read as m
    with pytest.raises(A.InputsError, match="above the gross|not the net"):
        A.load_inputs(doc)


def test_applied_once_and_no_merged_source():
    l35, l36, *_ = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(inputs(l35)), l36)
    doc = inputs(l35)
    doc["lines"][0]["source_tasks"] = ["T-999"]
    with pytest.raises(A.InputsError, match="no merged source"):
        A.load_inputs(doc)


def test_integrate_refuses_a_moved_quantity():
    l35 = lines_3035()
    d = A.load_inputs(inputs(l35), PID)
    ch, _log = A.changes_for(d, l35)
    bad = copy.deepcopy(ch)
    bad[1]["after"]["measured_net"] = 40.0
    with pytest.raises(ValueError, match="a quantity moved|not the net"):
        A.integrate(l35, bad)


def test_mirrored_order_same_result():
    l35 = lines_3035()
    doc = inputs(l35)
    rev = copy.deepcopy(doc)
    rev["lines"] = list(reversed(rev["lines"]))
    for r in rev["lines"]:
        r["items"] = list(reversed(r["items"]))
    _a, out1, *_ = run(l35, doc)
    _b, out2, *_ = run(lines_3035(), rev)
    s1 = {x["line_id"]: (x["gross"], sorted(i["id"] for i in x["deductions"])) for x in out1}
    s2 = {x["line_id"]: (x["gross"], sorted(i["id"] for i in x["deductions"])) for x in out2}
    assert s1 == s2
