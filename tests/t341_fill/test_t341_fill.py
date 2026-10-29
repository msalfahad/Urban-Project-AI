"""T-341 fill table: synthetic villa VG-341 (hand-calculated; not the development villa). Normal and adverse cases."""

import copy
import csv
import importlib.util
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t341_fill", ROOT / "research" / "agents_t341" / "t341_fill.py")
F = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(F)
from tools import t330_deductions_check as C  # noqa: E402


def line(lid, code, unit, gross, net, ded=(), add=(), inputs=None, eid="VG-R1:x", floor="GF"):
    return {"line_id": lid, "trade": "FIN", "item_code": code, "unit": unit, "gross": gross, "measured_net": net,
            "deductions": list(ded), "additions": list(add), "location": {"floor": floor, "element_id": eid},
            "calculation": {"formula": "", "inputs": inputs or {}}, "evidence_state": "PROVISIONAL"}


# hand: room 4.00 x 3.00, height 3.00 -> 14.00 x 3.00 = 42.000 m2; door 0.90 x 2.20 = 1.980; window 1.20 x 1.00 = 1.200
PLASTER = line("L-P1", "FIN.PLASTER", "m2", 42.0, 38.82, inputs={"owner_manual_method": {"deductions": [
    {"opening": "D-01", "face": "R1|W1", "m2": 1.98}, {"opening": "W-01", "face": "R1|W3", "m2": 1.2}]}})


def ledger(tmp_path, rows):
    p = tmp_path / "ledger.csv"
    cols = ["line_id", "opening_id", "census_id", "kind", "length_m", "listed", "listed_as", "source", "cause"]
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({**{c: "" for c in cols}, **r})
    return F.load_ledger(p)


def test_shadow_list_fills_and_closes():
    rec, rows = F.fill_line(PLASTER)
    assert rec["status"] == "RECONCILED" and abs(rec["residual"]) <= F.TOL
    assert [(r["opening_id"], r["face"], r["amount"]) for r in rows] == [("D-01", "R1|W1", 1.98), ("W-01", "R1|W3", 1.2)]
    after = C.check_lines(F.apply_fill([PLASTER], [rec], rows))
    assert after["flagged"] == 0 and after["refused"] == 0


def test_skirting_ledger_split_addition_and_unlisted(tmp_path):
    # hand: perimeter 14.00; door 0.90; band passage 3.00 of which only 2.50 on this boundary (+0.50 back);
    # window edge 1.20 split 0.60 listed glazing + 0.60 unlisted threshold -> net 14 - 0.9 - 3.0 + 0.5 - 0.6 - 0.6 = 9.40
    ln = line("L-S1", "FIN.SKIRTING", "lm", 14.0, 9.4,
              ded=[{"lm": 3.4, "what": "door / passage openings"}, {"lm": 0.6, "what": "glazing edge"}])
    led = ledger(tmp_path, [
        {"line_id": "L-S1", "opening_id": "OP-1", "kind": "DOOR", "length_m": "0.9", "listed": "True",
         "listed_as": "door / passage openings"},
        {"line_id": "L-S1", "opening_id": "OP-2", "kind": "PASSAGE", "length_m": "3.0", "listed": "True",
         "listed_as": "door / passage openings"},
        {"line_id": "L-S1", "opening_id": "", "kind": "PASSAGE_RUN_RESIDUAL", "length_m": "-0.5", "listed": "True",
         "listed_as": "door / passage openings"},
        {"line_id": "L-S1", "opening_id": "OP-3#glazing-half", "kind": "WINDOW_EDGE_HALF", "length_m": "0.6",
         "listed": "True", "listed_as": "glazing edge"},
        {"line_id": "L-S1", "opening_id": "OP-3#threshold-half", "kind": "WINDOW_EDGE_HALF", "length_m": "0.6",
         "listed": "False", "listed_as": ""}])
    assert C.check_line(ln)["category"] == "NOT_SUMMING"
    rec, rows = F.fill_line(ln, led["L-S1"])
    assert rec["status"] == "RECONCILED", rec
    assert rec["additions_sum"] == 0.5 and all(r["amount"] >= 0 for r in rows)
    assert math.isclose(rec["deductions_sum"], 5.1, abs_tol=1e-9)
    assert C.check_lines(F.apply_fill([ln], [rec], rows))["flagged"] == 0


def test_floor_gross_restated_from_face():
    # hand: face 30.00; stair treads 2.00 (listed); part moved to the wet floor 5.00 -> net 23.00; gross written = net
    ln = line("L-F1", "FIN.FLOOR.PORCELAIN", "m2", 23.0, 23.0, ded=[{"m2": 2.0, "what": "stair treads"}],
              inputs={"floor_scope_v3014": {"kind": "TO_WET", "area_m2": 5.0, "record": "VG-PART"}}, eid="VG-R2:floor")
    ceil = line("L-C1", "FIN.CEILING", "m2", 30.0, 30.0, eid="VG-R2:ceiling")
    rep, recs, rows = F.build([ln, ceil], {})
    assert [r["status"] for r in recs] == ["RECONCILED_GROSS_RESTATED"]
    assert recs[0]["gross_used"] == 30.0 and abs(recs[0]["residual"]) <= F.TOL
    out = F.apply_fill([ln, ceil], recs, rows)
    assert out[0]["gross"] == 30.0 and ln["gross"] == 23.0          # copies only; input untouched
    assert C.check_lines(out)["flagged"] == 0


def test_adverse_opening_listed_twice_refused():
    bad = copy.deepcopy(PLASTER)
    bad["calculation"]["inputs"]["owner_manual_method"]["deductions"].append(
        {"opening": "D-01", "face": "R1|W1", "m2": 1.98})
    bad["measured_net"] = 42.0 - 1.98 * 2 - 1.2          # even when the arithmetic closes
    rec, _rows = F.fill_line(bad)
    assert rec["status"] == "REFUSED" and "listed twice" in rec["cause"]


def test_adverse_list_in_another_unit_refused():
    bad = copy.deepcopy(PLASTER)
    bad["calculation"]["inputs"]["owner_manual_method"]["deductions"][1] = {"opening": "W-01", "face": "R1|W3",
                                                                              "lm": 1.2}
    rec, _rows = F.fill_line(bad)
    assert rec["status"] == "REFUSED" and "another unit" in rec["cause"]


def test_adverse_net_no_list_explains_stays_unexplained():
    bad = copy.deepcopy(PLASTER)
    bad["measured_net"] = 37.82                          # 1.000 m2 more removed than the openings explain
    rec, rows = F.fill_line(bad)
    assert rec["status"] == "UNEXPLAINED" and math.isclose(rec["residual"], 1.0, abs_tol=1e-9)
    out = F.apply_fill([bad], [rec], rows)
    assert out[0] is bad and out[0]["deductions"] == []  # never forced to fit
    assert C.check_lines(out)["flagged"] == 1


def test_adverse_floor_gross_equal_net_without_face_is_unexplained():
    ln = line("L-F2", "FIN.FLOOR.PORCELAIN", "m2", 23.0, 23.0, ded=[{"m2": 2.0, "what": "stair treads"}],
              inputs={"floor_scope_v3014": {"kind": "TO_WET", "area_m2": 5.0, "record": "VG-PART"}}, eid="VG-R3:floor")
    rec, _rows = F.fill_line(ln, (), None)
    assert rec["status"] == "UNEXPLAINED" and rec["residual"] is None


def test_ledger_that_does_not_close_aggregate_falls_back_to_element(tmp_path):
    ln = line("L-S2", "FIN.SKIRTING", "lm", 10.0, 9.0, ded=[{"lm": 1.0, "what": "door / passage openings"}])
    led = ledger(tmp_path, [{"line_id": "L-S2", "opening_id": "OP-9", "length_m": "0.8", "listed": "True",
                             "listed_as": "door / passage openings"}])
    rec, rows = F.fill_line(ln, led["L-S2"])
    assert rec["status"] == "RECONCILED_BY_ELEMENT" and rows[0]["source"].startswith("ELEMENT")
