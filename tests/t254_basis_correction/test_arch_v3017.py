"""T-254: ARCH_TAKEOFF_V3.0.17 (engine.source.arch_v3017): candidate lines on an unprinted depth / height corrected line
id by line id from a checker-merged basis ledger.

Hand-made synthetic villa K254 (not the development villa), computed by hand before running the code:
  printed: exterior ground-beam section top 'ground floor slab level' +0.90, underside 'outer natural ground' +-0.00
           -> D = 0.90 m for EXTERIOR runs; interior class 30 x 40 printed for interior beams only; columns 0.30 x 0.30;
           2F roof prints only the FINISHED +10.20 (no slab level).
  candidate (V3.0.16-like) lines, width 0.30 everywhere:
    GB-E1 typed EXTERIOR, run E1 5.40 m face to face, engine depth 0.40 (interior class) -> 5.40 x 0.30 x 0.40 = 0.6480
          drawing: 5.40 x 0.30 x 0.90 = 1.4580 m3 (REBASE, +0.8100)
    GB-I2 typed INTERIOR, holds the EXTERIOR run E2 2.25 m, engine depth 0.30 -> 2.25 x 0.30 x 0.30 = 0.2025
          drawing: 2.25 x 0.30 x 0.90 = 0.6075 m3 (REBASE, +0.4050)
    GB-I3 typed INTERIOR, interior run I3 4.00 m x 0.30 x 0.40 = 0.4800 (untouched, byte-identical)
    GB-C4 typed EXTERIOR, court run C4 3.00 m, engine 3.00 x 0.30 x 0.40 = 0.3600: no printed section -> HELD blank,
          readings 0.30 / 0.40 depth: 0.2700 / 0.3600 in the scenario only
    COL-2F 0.30 x 0.30 x 4.20 (FFL to the FINISHED roof) = 0.3780 -> HELD blank (roof datum)
  group GB_EXT: lines 3 (E1, I2, C4) before 0.6480 + 0.2025 + 0.3600 = 1.2105, released after 1.4580 + 0.6075 =
  2.0655, held 1; group COL: 1 line before 0.3780, after 0, held 1.
  Totals STR.CONC.GROUND_BEAM m3: before 0.6480 + 0.2025 + 0.4800 + 0.3600 = 1.6905 -> after 1.4580 + 0.6075 + 0.4800 =
  2.5455 released + 1 blocked line.
"""

from __future__ import annotations

import copy
import json

import pytest

from engine.source import arch_v30 as A30
from engine.source import arch_v304 as A304
from engine.source import arch_v3017 as A
from engine.source import boq_line as BL

PID = "villa-k254"
REV = "c" * 64
ROUTE = {"project_id": "K254 structural set", "revision_set_sha256": "d" * 64}
DOCS = [{"file": "K254-ST.dxf", "sha256": "e" * 64}]
SRC = {"file": "research/k254/BASIS.csv", "sha256": "f" * 64, "task": "T-K1", "merge_commit": "1" * 40,
       "checker_run": "Verifier 2026-10-25 09:33"}


def line(eid, code, qty, floor="GROUND"):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit="m3", evidence_state="SOURCE_DERIVED",
                      measured_net=qty, element_id=eid, floor=floor, physical_element="BEAM", formula="engine",
                      inputs={"engine": {"depth": 0.4}}, documents=DOCS, rule_id="R-ENG", rule_version="1",
                      item_en="x", item_ar="x", trade="CONCRETE")
    ln["project"] = {"project_id": PID, "revision_set_sha256": REV, "route": dict(ROUTE)}
    return BL.validate(ln)


GB = "STR.CONC.GROUND_BEAM"
COL = "STR.CONC.COLUMN"


def blocked(eid, code, floor):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit="m3", evidence_state="BLOCKED_RFI",
                      element_id=eid, floor=floor, physical_element="COLUMN", formula="held", documents=DOCS,
                      rule_id="R-ENG", rule_version="1", rfi={"question": "member not drawn", "unlocks": eid},
                      item_en="x", item_ar="x", trade="CONCRETE")
    ln["project"] = {"project_id": PID, "revision_set_sha256": REV, "route": dict(ROUTE)}
    return BL.validate(ln)


def candidate():
    return [line("K:GB:E1", GB, 0.648), line("K:GB:I2", GB, 0.2025), line("K:GB:I3", GB, 0.48),
            line("K:GB:C4", GB, 0.36), line("K:COL:2F:C1", COL, 0.378, "2F"), blocked("K:COL:2F:X9", COL, "2F")]


def ids():
    return {ln["location"]["element_id"]: ln["line_id"] for ln in candidate()}


EXT_SUPPORT = {"kind": "TWO_PRINTED_LEVELS", "printed": "exterior section: top GF slab +0.90, underside N.G. +-0.00",
               "sheets": "K254 ST p.9"}


def inputs():
    i = ids()
    return {"schema": A.INPUTS_SCHEMA, "project": PID, "sources": [dict(SRC)],
            "records": [
                {"line_id": i["K:GB:E1"], "item_code": GB, "element_id": "K:GB:E1", "group": "GB_EXT", "task": "T-K1",
                 "physical_element": "GROUND_BEAM exterior", "before": {"evidence_state": "SOURCE_DERIVED",
                                                                       "measured_net": 0.648},
                 "action": "REBASE", "value": 1.458, "runs": [{"id": "E1", "value": 1.458}],
                 "support": dict(EXT_SUPPORT), "status": "DRAWING-CONFIRMED"},
                {"line_id": i["K:GB:I2"], "item_code": GB, "element_id": "K:GB:I2", "group": "GB_EXT", "task": "T-K1",
                 "physical_element": "GROUND_BEAM exterior in a line typed interior",
                 "before": {"evidence_state": "SOURCE_DERIVED", "measured_net": 0.2025},
                 "action": "REBASE", "value": 0.6075, "runs": [{"id": "E2", "value": 0.6075}],
                 "support": dict(EXT_SUPPORT), "status": "DRAWING-CONFIRMED"},
                {"line_id": i["K:GB:C4"], "item_code": GB, "element_id": "K:GB:C4", "group": "GB_EXT", "task": "T-K1",
                 "physical_element": "GROUND_BEAM court", "before": {"evidence_state": "SOURCE_DERIVED",
                                                                    "measured_net": 0.36},
                 "action": "HOLD", "held_item": "court section not printed", "reasons": ["no section"],
                 "scenario": {"readings": {"d030": 0.27, "d040": 0.36}, "basis": "depth candidates"}},
                {"line_id": i["K:COL:2F:C1"], "item_code": COL, "element_id": "K:COL:2F:C1", "group": "COL",
                 "task": "T-K1", "physical_element": "COLUMN 2F", "before": {"evidence_state": "SOURCE_DERIVED",
                                                                             "measured_net": 0.378},
                 "action": "HOLD", "held_item": "roof datum", "reasons": ["only the finished +10.20 printed"]}],
            "groups": {"GB_EXT": {"lines": 3, "before": 1.2105, "released_after": 2.0655, "held_lines": 1},
                       "COL": {"lines": 1, "before": 0.378, "released_after": 0.0, "held_lines": 1}}}


def run(doc=None, cand=None):
    cand = cand or candidate()
    doc = A.load_inputs(doc if doc is not None else inputs(), PID)
    ch, log = A.changes_for(doc, cand)
    return A.integrate(cand, ch), ch, log


# ------------------------------------------------------------------------------------------------ normal
def test_rebase_and_hold_by_hand():
    (out, ident), ch, log = run()
    by = {ln["location"]["element_id"]: ln for ln in out}
    assert by["K:GB:E1"]["measured_net"] == pytest.approx(1.458, abs=1e-9)
    assert by["K:GB:I2"]["measured_net"] == pytest.approx(0.6075, abs=1e-9)
    for k in ("K:GB:C4", "K:COL:2F:C1"):
        assert by[k]["evidence_state"] == "BLOCKED_RFI"
        assert by[k]["measured_net"] is None and by[k]["bounded_range"] is None   # blank, never 0
    t = A304.code_totals(out)[f"{GB}|m3"]
    assert t["released"] == pytest.approx(2.5455, abs=1e-9)
    assert t["blocked_lines"] == 1
    assert log["groups"]["GB_EXT"]["released_after"] == pytest.approx(2.0655)
    assert ident["replaced"] == 4 and ident["outside_rows"] == 2


def test_line_ids_and_everything_else_kept():
    cand = candidate()
    (out, _), _, _ = run(cand=copy.deepcopy(cand))
    assert [x["line_id"] for x in out] == [x["line_id"] for x in cand]
    assert A30.line_sha(out[2]) == A30.line_sha(cand[2])          # GB-I3 untouched byte-identical
    for a, b in zip(cand, out):
        assert a["project"] == b["project"] and a["location"] == b["location"] and a["source"] == b["source"]


def test_scenario_holds_readings_only():
    sc = A.scenarios(inputs())
    assert [s["readings"] for s in sc] == [{"d030": 0.27, "d040": 0.36}]
    assert all(s["status"].startswith("HELD - SCENARIO ONLY") for s in sc)


def test_added_held_line_is_blank_and_stamped_like_its_sibling():
    d = inputs()
    i = ids()
    d["adds"] = [{"id": "BGB", "item_code": GB, "unit": "m3", "floor": "GROUND", "element": "BOUNDARY_GB",
                  "physical_element": "GROUND_BEAM boundary", "task": "T-K1", "item_en": "Boundary ground beam",
                  "item_ar": "x", "trade": "CONCRETE", "like_line_id": i["K:GB:E1"], "state": "HELD",
                  "held_item": "boundary column count", "reasons": ["columns not drawn"],
                  "scenario": {"readings": {"band": 1.2}}}]
    (out, ident), ch, _ = run(d)
    add = out[-1]
    assert ident["added"] == 1 and add["evidence_state"] == "BLOCKED_RFI" and add["measured_net"] is None
    assert add["project"] == candidate()[0]["project"]
    assert add["source"]["documents"] == DOCS


# ------------------------------------------------------------------------------------------------ generic regression
# pair (lessons 2026-10-25, T-289): the correction list is built from the DRAWN runs bound by geometry
RUNS = [{"id": "E1", "cls": "EXTERIOR", "axis": "X", "at": 0.0, "a": 0.0, "b": 5.4},
        {"id": "E2", "cls": "EXTERIOR", "axis": "Y", "at": 5.4, "a": 0.0, "b": 2.25},
        {"id": "I3", "cls": "INTERIOR", "axis": "X", "at": 3.0, "a": 0.0, "b": 4.0}]
GLINES = [{"line_id": "GB-E1", "typed": "EXTERIOR", "axis": "X", "at": 0.0, "a": 0.0, "b": 5.4},
          {"line_id": "GB-I2", "typed": "INTERIOR", "axis": "Y", "at": 5.4, "a": 0.0, "b": 2.25},
          {"line_id": "GB-I3", "typed": "INTERIOR", "axis": "X", "at": 3.0, "a": 0.0, "b": 4.0}]


def test_normal_exterior_run_in_an_interior_typed_line_is_found_by_geometry():
    b = A.bind_runs(RUNS, GLINES)
    assert b["typed_mismatch"] == [("GB-I2", "INTERIOR", "EXTERIOR", "E2")]
    assert A.check_correction_list(b, "EXTERIOR", ["GB-E1", "GB-I2"]) == ["GB-I2"]


def test_normal_binding_is_mirror_and_order_invariant():
    mir = [dict(r, a=-r["b"], b=-r["a"]) for r in RUNS]
    ml = [dict(x, a=-x["b"], b=-x["a"]) for x in GLINES]
    assert A.bind_runs(list(reversed(mir)), list(reversed(ml))) == A.bind_runs(RUNS, GLINES)


def test_adverse_list_from_the_engine_flag_misses_the_interior_typed_line():
    b = A.bind_runs(RUNS, GLINES)
    engine_flag = [x["line_id"] for x in GLINES if x["typed"] == "EXTERIOR"]
    with pytest.raises(A.InputsError, match="GB-I2"):
        A.check_correction_list(b, "EXTERIOR", engine_flag)


def test_adverse_drawn_exterior_run_matched_to_no_line_is_reported_never_dropped():
    runs = RUNS + [{"id": "E9", "cls": "EXTERIOR", "axis": "X", "at": 9.0, "a": 0.0, "b": 1.2}]
    b = A.bind_runs(runs, GLINES)
    assert b["unmatched_runs"] == ["E9"]
    with pytest.raises(A.InputsError, match="E9"):
        A.check_correction_list(b, "EXTERIOR", ["GB-E1", "GB-I2"])


def test_adverse_binding_named_in_inputs_but_line_not_corrected():
    d = inputs()
    d["binding"] = {"cls": "EXTERIOR", "source": "bind_runs", "holding_line_ids": ["GB-I2-elsewhere"]}
    with pytest.raises(A.InputsError, match="not corrected"):
        A.load_inputs(d, PID)


# ------------------------------------------------------------------------------------------------ adverse inputs
def _mut(fn):
    d = inputs()
    fn(d)
    return d


@pytest.mark.parametrize("fn, msg", [
    (lambda d: (d["records"][0].update(before={"evidence_state": "SOURCE_DERIVED", "measured_net": 0.7}),
                d["groups"]["GB_EXT"].update(before=1.2625)), "stale"),
    (lambda d: d["records"][0]["support"].update(kind="BORROWED_CLASS_DEPTH"), "borrowed"),
    (lambda d: d["records"][3].update(action="REBASE", value=0.378, support={"kind": "FINISHED_LEVEL", "printed": "x",
                                                                             "sheets": "y"}, status="DRAWING-CONFIRMED",
                                      held_item=None), "finished"),
    (lambda d: d["records"][0]["support"].update(kind="PENDING"), "unmerged"),
    (lambda d: d["records"][2].update(value=0), "no figure"),
    (lambda d: d["records"][2].update(action="CONFLICT"), "both readings"),
    (lambda d: d["records"][2]["scenario"]["readings"].update(d030=0), "0 is no reading"),
    (lambda d: d["records"][0].update(task="T-UNMERGED"), "merged sources"),
    (lambda d: d["records"].append(dict(d["records"][0])), "named twice"),
    (lambda d: d["groups"]["GB_EXT"].update(before=1.3), "sum to"),
    (lambda d: d["records"][0].update(runs=[{"id": "E1", "value": 1.40}]), "sum of its runs"),
    (lambda d: d["records"][0].update(value=0.0), "value > 0"),
    (lambda d: d["records"][0].update(status="VERIFIED"), "checker run"),
    (lambda d: d["records"][3].update(held_item=None), "names the item"),
])
def test_adverse_inputs_refused(fn, msg):
    with pytest.raises(A.InputsError, match=msg):
        run(_mut(fn))


def test_adverse_unit_slip_is_a_stale_before():
    d = inputs()
    d["records"][0]["before"]["measured_net"] = 648.0        # litres / mm slip: never the line's figure
    d["groups"]["GB_EXT"]["before"] = 648.0 + 0.2025 + 0.36
    with pytest.raises(A.InputsError, match="stale"):
        run(d)


def test_adverse_record_of_a_line_the_candidate_lacks():
    d = inputs()
    d["records"][0]["line_id"] = "L-00000000000000000000"
    with pytest.raises(A.InputsError, match="does not carry"):
        run(d)


def test_adverse_added_line_with_a_figure_refused():
    d = inputs()
    d["adds"] = [{"id": "BGB", "item_code": GB, "unit": "m3", "floor": "GROUND", "element": "B", "physical_element": "x",
                  "task": "T-K1", "item_en": "x", "item_ar": "x", "trade": "CONCRETE", "like_line_id": ids()["K:GB:E1"],
                  "state": "HELD", "held_item": "x", "reasons": ["y"], "value": 1.2}]
    with pytest.raises(A.InputsError, match="no figure"):
        run(d)


def test_adverse_change_outside_quantity_state_basis_refused():
    cand = candidate()
    doc = A.load_inputs(inputs(), PID)
    ch, _ = A.changes_for(doc, cand)
    ch[0]["after"]["location"] = dict(ch[0]["after"]["location"], floor="1F")
    with pytest.raises(ValueError, match="outside quantity"):
        A.integrate(cand, ch)


def test_adverse_two_project_identities_refused():
    cand = candidate()
    cand[2]["project"] = dict(cand[2]["project"], project_id="another villa")
    doc = A.load_inputs(inputs(), PID)
    ch, _ = A.changes_for(doc, cand)
    with pytest.raises(ValueError, match="project identities"):
        A.integrate(cand, ch)


def test_write_files(tmp_path):
    cand = candidate()
    doc = A.load_inputs(inputs(), PID)
    ch, log = A.changes_for(doc, cand)
    names, ident, led = A.write(tmp_path, cand, ch, log, doc)
    assert "V3_0_17_DIFF.csv" in names and led["integration_package"] is True
    diff = (tmp_path / "V3_0_17_DIFF.csv").read_text().splitlines()
    assert sum(1 for r in diff if ",CHANGED," in r) == 4 and sum(1 for r in diff if ",SAME," in r) == 2
    run_doc = json.loads((tmp_path / "V3_0_17_RUN.json").read_text())
    assert run_doc["released_default"] is False
    moved = run_doc["totals_moved_by_code"]
    assert set(moved) == {f"{GB}|m3", f"{COL}|m3"}
    again = tmp_path / "again"
    again.mkdir()
    A.write(again, cand, ch, log, doc)
    for n in names:
        assert (again / n).read_bytes() == (tmp_path / n).read_bytes()


# ------------------------------------------------------------------------------------------------ NOT_PRESENT
def _np(d):
    d["records"].append({"line_id": ids()["K:COL:2F:X9"], "item_code": COL, "element_id": "K:COL:2F:X9",
                         "group": "COL_NP", "task": "T-K1", "physical_element": "COLUMN 2F (type table only)",
                         "before": {"evidence_state": "BLOCKED_RFI", "measured_net": None}, "action": "NOT_PRESENT",
                         "absence_evidence": "no plan, plot or architectural plan draws it; no start symbol below",
                         "sheets_searched": "K254 ST p.4, p.5; arch 2F"})
    d["groups"]["COL_NP"] = {"lines": 1, "before": 0.0, "released_after": 0.0, "held_lines": 0}
    return d


def test_not_present_is_not_applicable_with_evidence_never_0():
    (out, ident), ch, log = run(_np(inputs()))
    x = [ln for ln in out if ln["location"]["element_id"] == "K:COL:2F:X9"][0]
    assert x["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and x["measured_net"] is None
    assert "NOT_PRESENT" in x["calculation"]["formula"] and x["notes"]
    assert ident["replaced"] == 5
    assert A304.code_totals(out)[f"{COL}|m3"]["lines"] == 1      # the absent member leaves the totals, never as 0


@pytest.mark.parametrize("k, v, msg", [("value", 0.0, "no figure"), ("absence_evidence", None, "absence evidence"),
                                       ("sheets_searched", None, "every sheet searched")])
def test_adverse_not_present_refused(k, v, msg):
    d = _np(inputs())
    d["records"][-1][k] = v
    with pytest.raises(A.InputsError, match=msg):
        run(d)
