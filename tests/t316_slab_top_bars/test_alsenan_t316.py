"""T-316 Alsenan pins (development villa; research ledger only). Reads the committed top-end detail (numbers and T-139
face ids only, built from the private faces by `t316_alsenan.py --geometry`) and the merged T-306 / T-152 research
files; no drawing is read here, no candidate or released kg is changed."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t316"
sys.path.insert(0, str(HERE))
import t316_alsenan as A  # noqa: E402


@pytest.fixture(scope="module")
def built():
    return A.build()


def test_committed_files_reproduce():
    assert A.run(False) == 0


def test_every_top_line_and_end_once(built):
    line_rows, group_rows, _c, _r, counts, groups, _x = built
    assert len(line_rows) == 98 and len({r["line_id"] for r in line_rows}) == 98
    det = list(csv.DictReader(open(HERE / "TOP_END_DETAIL_T316.csv", encoding="utf-8")))
    assert len(det) == 5914 == len(group_rows)
    assert all(d["support"] in A.tb.CLASSES for d in det)
    assert {k: [counts["A"][k], counts["B"][k]] for k in counts["A"]} == {
        "CONTINUOUS": [1362, 1457], "EDGE_BEAM": [882, 919], "STEP_EDGE": [376, 401],
        "IRREGULAR_SUPPORT": [234, 269], "OPENING_EDGE": [2, 12]}
    assert all(len(v) <= 2 for v in groups.values()) and len(groups) == 283


def test_t306_top_causes_close_by_class():
    s = json.load(open(HERE / "TOP_SUMMARY_T316.json"))
    assert s["t306_top_causes_kg"] == {"TOP_NOTE2_WORDING": 781.385, "TOP_NOTE2_VS_P15": 185.612,
                                       "TOP_CROSSING": 146.686, "COUNT_CONVENTION": 107.27}
    assert all(abs(v) < 0.01 for v in s["residual_kg"].values())        # 3 dp storage of 98 lines
    by = s["the_1113_683_by_class_kg"]
    assert by == {"CONTINUOUS": 694.418, "EDGE_BEAM": 232.661, "IRREGULAR_SUPPORT": 53.319, "OPENING_EDGE": 0.898,
                  "STEP_EDGE": 132.394}
    assert s["the_1113_683_total_kg"] == pytest.approx(1113.683, abs=0.01)
    assert s["by_class_kg"]["TOP_CROSSING"]["EDGE_BEAM"] == 0.0           # T-152 books no crossing at an edge


def test_findings_pinned():
    s = json.load(open(HERE / "TOP_SUMMARY_T316.json"))
    assert s["across_edge_beam_kg"] == {"A": [122.574, 144.352], "B": [127.586, 150.278]}
    assert s["t152_p15_beyond_span_in_candidate_high_kg"] == 81.746 and s["lines_high_reading_p15"] == 40
    assert s["ends_facing_TB_panel_A_B"] == [37, 40]
    assert s["statuses"]["UNRESOLVED_TB_PANEL"] == 4 and s["statuses"]["HELD"] == 8


def test_held_stays_blank_never_zero():
    rows = list(csv.DictReader(open(HERE / "TOP_LINE_LEDGER_T316.csv", encoding="utf-8")))
    for r in rows:
        if r["proposed_status"] in ("HELD", "UNRESOLVED_TB_PANEL"):
            assert r["p15_valued_low_kg"] == "" and r["p15_valued_high_kg"] == ""
        else:
            assert float(r["p15_valued_low_kg"]) <= float(r["p15_valued_high_kg"])


def test_worked_example_2f047_y():
    rows = {r["line_id"]: r for r in csv.DictReader(open(HERE / "TOP_LINE_LEDGER_T316.csv", encoding="utf-8"))}
    r = rows["L-4651c36c7b73eab9cb77"]
    # 1.20 m span: continuous side 0.30 x 5.00 = 1.50 + edge side 0.25 x 1.20 = 0.30 > 1.20 -> R316-10 bound
    # A: 15 x (1.20 + 0.10 + 0.16) x 100/162 = 13.519; B: 15 x (1.50 + 0.10 + 0.20) + (0.36 + 0.10 + 0.30 + 0.20)
    #    = 27.96 m x 100/162 = 17.259
    assert (r["p15_valued_low_kg"], r["p15_valued_high_kg"]) == ("13.519", "17.259")
