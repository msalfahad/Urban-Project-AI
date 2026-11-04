"""T-460 item 2: SKIRTING_LINE_CLOSURE_V1 on a non-training hand fixture (villa K bedroom, 4.00 x 3.50 m).

Hand calculation: boundary walk 2 x (4.00 + 3.50) = 15.000 lm; door 0.900 lm deducted; floor glazing 1.200 lm deducted;
a sill window threshold 1.500 lm restored as an addition -> net 15.000 - 0.900 - 1.200 + 1.500 = 14.400 lm (CLOSES).
Adverse: the same net written without the addition listed (net 14.400 vs walk 12.900 -> UNLISTED_ADDITION 1.500);
a net 12.400 with only the door listed (UNLISTED_DEDUCTION 1.700, never plugged); a net without a gross; a HELD line
without a net is NO_QUANTITY, never 0; a deduction with no length is not summed as 0.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t460"))

import skirting_closure_v1 as SK  # noqa: E402

DOOR = {"what": "door / passage openings", "lm": 0.9}
GLZ = {"what": "glazing edge (floor-level windows)", "lm": 1.2}
THR = {"what": "sill window threshold W1", "lm": 1.5}


def test_normal_line_closes():
    r = SK.close({"line_id": "K1", "gross": 15.0, "net": 14.4, "deductions": [DOOR, GLZ], "additions": [THR]})
    assert r["state"] == "CLOSES" and r["residual_lm"] == pytest.approx(0.0, abs=1e-9)
    assert r["listed_ded"] == pytest.approx(2.1) and r["listed_add"] == pytest.approx(1.5)


def test_adverse_unlisted_addition_and_deduction():
    a = SK.close({"line_id": "K2", "gross": 15.0, "net": 14.4, "deductions": [DOOR, GLZ]})
    assert a["state"] == "UNLISTED_ADDITION" and a["residual_lm"] == pytest.approx(-1.5)
    b = SK.close({"line_id": "K3", "gross": 15.0, "net": 12.4, "deductions": [DOOR]})
    assert b["state"] == "UNLISTED_DEDUCTION" and b["residual_lm"] == pytest.approx(1.7)


def test_adverse_no_gross_no_quantity_and_missing_length():
    assert SK.close({"line_id": "K4", "gross": None, "net": 14.4})["state"] == "NO_GROSS"
    held = SK.close({"line_id": "K5", "gross": None, "net": None, "evidence_state": "BLOCKED_RFI"})
    assert held["state"] == "NO_QUANTITY" and held["residual_lm"] is None
    r = SK.close({"line_id": "K6", "gross": 15.0, "net": 14.1, "deductions": [{"what": "door", "lm": None}]})
    assert r["state"] == "NO_GROSS" and r["listed_ded"] is None


def test_candidate_ledger_rows_qty_unit_lm():
    # the candidate's ledger rows carry {"id", "qty", "unit": "lm"}; a row in another unit is not an lm deduction
    r = SK.close({"line_id": "K7", "gross": 15.0, "net": 14.1,
                  "deductions": [{"id": "OP-1", "qty": 0.9, "unit": "lm"}], "additions": []})
    assert r["state"] == "CLOSES" and r["listed_ded"] == pytest.approx(0.9)
    m = SK.close({"line_id": "K8", "gross": 15.0, "net": 14.1, "deductions": [{"id": "OP-1", "qty": 1.0, "unit": "pcs"}]})
    assert m["state"] == "NO_GROSS" and m["listed_ded"] is None


def test_ledger_summary():
    L = SK.ledger([{"line_id": "K1", "gross": 15.0, "net": 14.4, "deductions": [DOOR, GLZ], "additions": [THR]},
                   {"line_id": "K3", "gross": 15.0, "net": 12.4, "deductions": [DOOR]},
                   {"line_id": "K5", "gross": None, "net": None},
                   {"line_id": "X", "item_code": "FIN.PLASTER", "gross": 1.0, "net": 1.0}])
    s = L["summary"]
    assert s["lines"] == 3 and s["by_state"] == {"CLOSES": 1, "NO_QUANTITY": 1, "UNLISTED_DEDUCTION": 1}
    assert s["unlisted_ded_lm"] == pytest.approx(1.7) and s["net_sum_lm"] == pytest.approx(26.8)
