"""T-260 Alsenan ledger (committed values-only input from P7757.dxf sha ab54dd55 and the sheet reads): re-runs the check
without writing and pins the engineering results for the Checker."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t260"
sys.path.insert(0, str(HERE))
import t260_alsenan_check as C  # noqa: E402

ROWS, SUM, OUT = C.main(write=False)
BY = {r["id"]: r for r in ROWS}


def test_outputs_are_reproduced_byte_for_byte():
    for k, v in OUT.items():
        assert (HERE / k).read_text(encoding="utf-8") == v


def test_input_is_values_only():
    txt = (HERE / "ALSENAN_T260_INPUT.json").read_text(encoding="utf-8")
    assert json.loads(txt)["source"]["architectural_dxf_sha256"].startswith("ab54dd55")
    assert not re.search(r"-?\d{5,}\.\d", txt)


def test_four_doors_settled_by_drawing_evidence():
    assert {k: (r["class"], r["width_m"], r["m2"]) for k, r in BY.items()} == {
        "D-GF-01": (C.E.ALU, 1.0, 2.2), "D-GF-05": (C.E.ALU, 1.0, 2.2),
        "D-GF-06": (C.E.ALU, 1.0, 2.2), "D-GF-09": (C.E.ALU, 0.9, 1.98)}
    assert all(r["width_status"] == C.E.DC and r["status"] == C.E.AS for r in ROWS)


def test_line_before_after_and_other_lines():
    a = SUM["aluminium_line_m2"]
    assert (a["before_released"], a["settled_here"], a["after_if_ruled"], a["pcs_after_if_ruled"]) == (4.18, 8.58,
                                                                                                        12.76, 6)
    assert a["before_held_range"][0] <= a["settled_here"] <= a["before_held_range"][1]
    o = SUM["other_lines_if_ruled"]
    assert o["PVC_GF_held_m2"] == [4.554, 5.28] and o["MAIN_ENTRANCE_held_m2"] == [5.0, 5.0]


def test_freelancer_reconciled_to_zero_residual():
    f = SUM["freelancer"]
    assert (f["pcs"], f["m2"], f["diff_m2"], f["diff_pct"]) == (5, 12.0, 0.76, 6.33)
    r = f["reconciliation_his_to_ours"]
    assert (r["heights_Q55C_2.20_vs_2.40"], r["widths_drawn_jambs"], r["count_drawn_5_GF_vs_his_4"],
            r["residual"]) == (-1.0, -0.44, 2.2, 0.0)


def test_d_gf_05_rests_on_the_q67_condition_on_two_sheets():
    inp = json.loads((HERE / "ALSENAN_T260_INPUT.json").read_text(encoding="utf-8"))
    d5 = next(d for d in inp["doors"] if d["id"] == "D-GF-05")
    mouth = d5["sides"][1]["mouths"][0]
    assert mouth["drawn_across_plan"] == [] and mouth["drawn_across_second_sheet"] == []
    assert "Q-67 A" in BY["D-GF-05"]["class_reason"]
