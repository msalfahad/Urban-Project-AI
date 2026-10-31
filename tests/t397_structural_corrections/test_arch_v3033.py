"""T-397: ARCH_TAKEOFF_V3.0.33 (structural corrections of Checker-verified reconciliations, line id by line id) on a
hand-calculated NON-Alsenan villa (V397), normal and adverse.

Villa V397, by hand (every value an own hand figure; nothing from the development villa):
  GS  ground-slab cell HELD, BOUNDED_EXPOSURE 2.40 .. 2.40 m3 = its gross 24.00 m2 x 0.10; inside it a 1.50 x 1.50 shaft
      (2.25 m2) and strips 0.75 m2 are not slab: own slab panels 21.00 m2 x 0.10 = 2.10 -> held bound 0 .. 2.10 m3
  B1  beam 0.30 x 0.60 x 4.00 = 0.720 m3 drawn; the candidate deducted a fitted 'overlap' 0.003 m2 x 0.60 = 0.0018 ->
      line 0.7182; restored 0.720 (GAP 0.0018)
  B2  beam 0.20 x 0.50 to an oblique carrier face: drawn net 0.20 x 0.50 x 3.00 = 0.300; the square band ran 0.002 m3
      past the face (DOUBLE with the carrier) and stopped 0.003 m3 short at the other edge (GAP) -> line 0.299;
      restored 0.300 (GAP 0.003 - DOUBLE 0.002 = +0.001, both named apart)
  C1  column schedule 25 x 50 x 3.00 = 0.375 (line), drawn 200 x 500 mm x 3.00 = 0.300 -> range 0.300 .. 0.375
  C2  column schedule 20 x 60 x 3.00 = 0.360 (line), drawn 250 x 600 mm x 3.00 = 0.450 -> range 0.360 .. 0.450
  LP  lift pit walls: outer 2.00 x 2.00 - inner 1.60 x 1.60 = 1.44 m2 gross - 4 column pieces 0.40 = 1.04 m2 net;
      depth not printed -> NEW line HELD BLANK, 1.04 m2 beside
  S   suspended slab 10.000 m3 SOURCE_DERIVED and a FIN.PAINT line 30.000 m2: unchanged
  valued concrete 0.7182 + 0.299 + 0.375 + 0.360 + 10.000 = 11.7522 -> 0.720 + 0.300 + 10.000 = 11.020 m3;
  ranges 0.660 .. 0.825 (C1 + C2); GS held 0 .. 2.10; lift pit BLANK.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3033 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-v397", "f" * 64
DOCS = [{"file": "v397_structure.dxf", "sha256": "d" * 64}]
SRC = [{"task": "T-391", "file": "research/v397/gs.json", "sha256": "1" * 64, "merge_commit": "a" * 40,
        "checker_run": "checker run 51 (Gate A PASS)"},
       {"task": "T-392", "file": "research/v397/beams.json", "sha256": "2" * 64, "merge_commit": "b" * 40,
        "checker_run": "checker run 51 (Gate A PASS)"},
       {"task": "T-394", "file": "research/v397/cols.json", "sha256": "3" * 64, "merge_commit": "c" * 40,
        "checker_run": "checker run 52 (Gate A PASS)"},
       {"task": "T-256", "file": "research/v397/t256.csv", "sha256": "4" * 64, "merge_commit": "e" * 40,
        "checker_run": "checker run 30 (Gate A PASS)"}]


def _line(code, eid, ev, net=None, floor="GF", unit="m3", br=None):
    kw = {"rfi": {"question": "held"}} if ev == "BLOCKED_RFI" else {}
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=eid, floor=floor, physical_element=eid, gross=net,
                        bounded_range=br, formula=f"{eid} {net}", documents=DOCS, rule_id="R", rule_version="1",
                        notes="v397", **kw)


def lines_3032():
    return [_line("STR.CONC.GROUND_SLAB", "GS:CELL-A", "BOUNDED_EXPOSURE", floor="GROUND",
                  br={"low": 2.4, "high": 2.4, "basis": "unresolved cell"}),
            _line("STR.CONC.BEAM", "B1", "PROVISIONAL", 0.7182),
            _line("STR.CONC.BEAM", "B2", "PROVISIONAL", 0.299),
            _line("STR.CONC.COLUMN", "C1", "PROVISIONAL", 0.375),
            _line("STR.CONC.COLUMN", "C2", "PROVISIONAL", 0.36, floor="1F"),
            _line("STR.CONC.SLAB", "S1", "SOURCE_DERIVED", 10.0),
            _line("FIN.PAINT", "GF-H:wall paint", "PROVISIONAL", 30.0, unit="m2")]


def _id(lines, eid):
    return next(x["line_id"] for x in lines if x["location"]["element_id"] == eid)


def _exp(lines, eid, **kw):
    ln = next(x for x in lines if x["location"]["element_id"] == eid)
    return dict({"item_code": ln["item_code"], "element_id": eid, "floor": ln["location"]["floor"],
                 "evidence_state": ln["evidence_state"]}, **kw)


def doc(lines=None):
    lines = lines or lines_3032()
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": copy.deepcopy(SRC), "rows": [
        {"action": "HELD_BOUND", "line_id": _id(lines, "GS:CELL-A"), "expect": _exp(lines, "GS:CELL-A", high=2.4),
         "low": 0.0, "high": 2.1, "source_tasks": ["T-391"], "evidence_status": "HELD",
         "cause": "own slab panels 21.00 m2 x 0.10; shaft 2.25 + strips 0.75 m2 are not slab"},
        {"action": "GAP_RESTORE", "line_id": _id(lines, "B1"), "expect": _exp(lines, "B1", measured_net=0.7182),
         "value": 0.72, "named_terms": [{"kind": "GAP", "m3": 0.0018, "name": "fitted overlap deduction"}],
         "source_tasks": ["T-392"], "evidence_status": "VERIFIED", "cause": "B1 drawn cell 1.20 m2 x 0.60"},
        {"action": "GAP_RESTORE", "line_id": _id(lines, "B2"), "expect": _exp(lines, "B2", measured_net=0.299),
         "value": 0.3, "named_terms": [{"kind": "GAP", "m3": 0.003, "name": "short of the carrier face"},
                                       {"kind": "DOUBLE", "m3": 0.002, "name": "past the carrier face"}],
         "source_tasks": ["T-392"], "evidence_status": "VERIFIED", "cause": "B2 drawn net to the carrier face"},
        {"action": "CONFLICT_RANGE", "line_id": _id(lines, "C1"), "expect": _exp(lines, "C1", measured_net=0.375),
         "readings": {"SCHEDULE": 0.375, "DRAWN": 0.3}, "designer_item": "column-band item",
         "schedule_print": "GR 25x50", "drawn_print": "200x500 mm", "height_m": 3.0, "source_tasks": ["T-394", "T-256"],
         "evidence_status": "HELD", "cause": "schedule vs drawn"},
        {"action": "CONFLICT_RANGE", "line_id": _id(lines, "C2"), "expect": _exp(lines, "C2", measured_net=0.36),
         "readings": {"SCHEDULE": 0.36, "DRAWN": 0.45}, "designer_item": "column-band item",
         "schedule_print": "1ST 20x60", "drawn_print": "250x600 mm", "height_m": 3.0, "source_tasks": ["T-394", "T-256"],
         "evidence_status": "HELD", "cause": "schedule vs drawn"},
        {"action": "MISSING_HELD", "item_code": "STR.CONC.LIFT", "element_id": "LIFT_PIT:WALLS", "floor": "FOUNDATION",
         "physical_element": "lift pit walls", "beside": 1.04, "beside_unit": "m2 plan ring net",
         "held_reason": "pit depth as per lift manufacturer", "source_tasks": ["T-394"], "evidence_status": "HELD",
         "cause": "1.44 gross - 0.40 column pieces"}]}


def run(d=None, lines=None):
    lines = lines or lines_3032()
    inp = A.load_inputs(d or doc(lines), PID)
    ch, log = A.changes_for(inp, lines)
    out, ident = A.integrate(lines, ch)
    return lines, ch, log, out, ident


def _valued(out, prefix="STR.CONC."):
    return round(sum(x["measured_net"] for x in out if x["item_code"].startswith(prefix) and
                     x["evidence_state"] in A.VALUED_STATES), 6)


def _by(out):
    return {x["location"]["element_id"]: x for x in out}


# ------------------------------------------------------------------------------------------------ normal
def test_hand_totals():
    lines, ch, log, out, ident = run()
    assert _valued(lines) == 11.7522
    assert _valued(out) == 11.02
    c = ident["corrections"]
    assert (c["range_low_m3"], c["range_high_m3"]) == (0.66, 0.825)
    assert c["by_action"] == {"CONFLICT_RANGE": 2, "GAP_RESTORE": 2, "HELD_BOUND": 1, "MISSING_HELD": 1}
    assert ident["replaced"] == 5 and ident["added"] == 1 and ident["outside_rows"] == 2


def test_held_bound_is_a_range_never_a_value():
    lines, ch, log, out, ident = run()
    gs = _by(out)["GS:CELL-A"]
    assert gs["evidence_state"] == "BOUNDED_EXPOSURE" and gs["measured_net"] is None
    assert (gs["bounded_range"]["low"], gs["bounded_range"]["high"]) == (0.0, 2.1)
    assert log["m3_moved"]["held_high"] == -0.3


def test_gap_restore_names_double_and_gap_apart():
    lines, ch, log, out, ident = run()
    b2 = _by(out)["B2"]
    assert b2["measured_net"] == 0.3 and b2["evidence_state"] == "PROVISIONAL"
    rec = b2["calculation"]["inputs"][A.REC_KEY]
    assert {t["kind"] for t in rec["named_terms"]} == {"GAP", "DOUBLE"}
    assert "DOUBLE 0.002" in b2["calculation"]["formula"] and "GAP 0.003" in b2["calculation"]["formula"]
    assert _by(out)["B1"]["measured_net"] == 0.72


def test_conflict_range_both_readings_never_one_end():
    lines, ch, log, out, ident = run()
    for eid, lo, hi in (("C1", 0.3, 0.375), ("C2", 0.36, 0.45)):
        c = _by(out)[eid]
        assert c["evidence_state"] == "BOUNDED_EXPOSURE" and c["measured_net"] is None and c["gross"] is None
        assert (c["bounded_range"]["low"], c["bounded_range"]["high"]) == (lo, hi)
        assert c["rfi"]["question"]


def test_missing_element_held_blank_never_zero():
    lines, ch, log, out, ident = run()
    lp = _by(out)["LIFT_PIT:WALLS"]
    assert lp["evidence_state"] == "BLOCKED_RFI" and lp["measured_net"] is None and not lp.get("bounded_range")
    assert lp["item_code"] == "STR.CONC.LIFT" and lp["unit"] == "m3"
    assert "1.04" in lp["rfi"]["question"] and " = " not in lp["calculation"]["formula"]


def test_outside_lines_byte_identical_and_totals_move_only_in_named_codes(tmp_path):
    lines = lines_3032()
    inp = A.load_inputs(doc(lines), PID)
    ch, log = A.changes_for(inp, lines)
    names, ident, led = A.write(tmp_path, lines, ch, log, inp)
    old = {x["line_id"]: x for x in lines}
    out = A.integrate(lines, ch)[0]
    for x in out:
        if x["location"]["element_id"] in ("S1", "GF-H:wall paint"):
            assert A30.line_sha(x) == A30.line_sha(old[x["line_id"]])
    t0, t1 = A304.code_totals(lines), A304.code_totals(out)
    moved = {k.split("|")[0] for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    assert moved <= {"STR.CONC.GROUND_SLAB", "STR.CONC.BEAM", "STR.CONC.COLUMN", "STR.CONC.LIFT"}
    d = (tmp_path / "V3_0_33_DIFF.csv").read_text(encoding="utf-8")
    assert d.count("ADDED") == 1 and d.count(",SAME,") == 2 and d.count(",CHANGED,") == 5
    assert led["integration_package"] is True and "V3_0_33_INTEGRATION_LEDGER.csv" in names


def test_restated_line_changes_only_quantity_state_range():
    lines, ch, log, out, ident = run()
    old = {x["line_id"]: x for x in lines}
    for c in ch:
        if c["action"] == "REPLACE":
            a, b = copy.deepcopy(old[c["before"]["line_id"]]), copy.deepcopy(c["after"])
            for x in (a, b):
                for k in A.ROW_KEYS:
                    x.pop(k, None)
            assert a == b


def test_mirrored_order_same_result():
    lines = lines_3032()
    d = doc(lines)
    d["rows"] = list(reversed(d["rows"]))
    out1 = run(lines=lines)[3]
    out2 = run(d=d, lines=lines)[3]
    assert {x["line_id"]: A30._qty(x) for x in out1} == {x["line_id"]: A30._qty(x) for x in out2}


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut, msg, stage="changes"):
    lines = lines_3032()
    d = doc(lines)
    mut(d, lines)
    with pytest.raises((A.InputsError, ValueError), match=msg):
        A.changes_for(A.load_inputs(d, PID), lines)


def test_stale_binding_refused():
    def m(d, lines):
        lines[1]["measured_net"] = 0.7
    _bad(m, "stale binding")


def test_wrong_element_refused():
    _bad(lambda d, l: d["rows"][1]["expect"].update(element_id="B9"), "stale binding")


def test_held_bound_raised_refused():
    _bad(lambda d, l: d["rows"][0].update(high=2.5), "never adds")


def test_held_bound_zero_high_refused():
    _bad(lambda d, l: d["rows"][0].update(high=0.0), "never 0")


def test_gap_terms_not_closing_refused():
    _bad(lambda d, l: d["rows"][2]["named_terms"].pop(), "named terms")


def test_gap_without_named_cause_refused():
    _bad(lambda d, l: d["rows"][1].update(named_terms=[]), "never 'rounding'")


def test_conflict_candidate_at_neither_reading_refused():
    _bad(lambda d, l: d["rows"][3].update(readings={"SCHEDULE": 0.4, "DRAWN": 0.3}), "neither reading")


def test_conflict_one_reading_refused():
    _bad(lambda d, l: d["rows"][3].update(readings={"SCHEDULE": 0.375}), "both readings")


def test_conflict_mm3_reading_refused():
    # a reading in the wrong unit (mm x mm x m) is not its print x height: refused, never ranged
    _bad(lambda d, l: d["rows"][3].update(readings={"SCHEDULE": 0.375, "DRAWN": 300000.0}), "not its print")


def test_conflict_reading_not_its_print_refused():
    # a drawn reading that is not the drawn outline x height (e.g. the schedule area re-used) is refused
    _bad(lambda d, l: d["rows"][4].update(drawn_print="200x600 mm"), "not its print")


def test_missing_element_with_value_refused():
    _bad(lambda d, l: d["rows"][5].update(value=1.5), "never with a value")


def test_missing_element_zero_beside_refused():
    _bad(lambda d, l: d["rows"][5].update(beside=0.0), "never 0")


def test_non_structural_code_refused():
    _bad(lambda d, l: d["rows"][5].update(item_code="MAS.BLOCK"), "not a structural concrete code")


def test_unmerged_source_refused():
    _bad(lambda d, l: d["rows"][1].update(source_tasks=["T-999"]), "no merged source")


def test_line_in_two_rows_refused():
    def m(d, lines):
        d["rows"].append(copy.deepcopy(d["rows"][1]))
    _bad(m, "two rows")


def test_applied_twice_refused():
    lines, ch, log, out, ident = run()
    d = doc(lines)
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(d, PID), out)


def test_valued_conflict_line_refused_by_guard():
    lines, ch, log, out, ident = run()
    bad = copy.deepcopy(out)
    c1 = next(x for x in bad if x["location"]["element_id"] == "C1")
    c1.update(evidence_state="PROVISIONAL", measured_net=0.3375, bounded_range=None)
    with pytest.raises(ValueError, match="carries a value"):
        A.check_corrections(bad)


def test_change_outside_rows_refused():
    lines, ch, log, out, ident = run()
    ch2 = copy.deepcopy(ch)
    paint = next(x for x in lines if x["item_code"] == "FIN.PAINT")
    after = copy.deepcopy(paint)
    after["measured_net"] = 31.0
    ch2.append({"piece": A.PIECE, "action": "REPLACE", "before": paint, "after": after})
    with pytest.raises(ValueError, match="structural concrete"):
        A.integrate(lines, ch2)
