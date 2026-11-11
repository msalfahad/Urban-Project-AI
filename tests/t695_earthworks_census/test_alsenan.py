"""T-695 on the candidate of record ARCH_TAKEOFF_V3.0.68 (lines d1de50cb): the B1 census and the zones the drawings
measure now, from the committed values-only inputs (no drawing needed). Re-runs without writing; pins the results."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t695"
sys.path.insert(0, str(HERE))
import t695_alsenan as A  # noqa: E402

ROWS, S = A.run(write=False)


def test_census_covers_every_b1_line_once():
    assert S["b1_lines"] == 20 and len({r["line_id"] for r in ROWS}) == 20
    assert S["census_counts"] == {"B1-02|DESIGNER": 7, "B1-02|MEASURABLE_NOW": 5, "B1-03|DESIGNER": 4,
                                  "B1-03|MEASURABLE_NOW": 3, "B1-04|NEEDS_TEST": 1}
    assert all(r["gap"] for r in ROWS if r["cause"] != "MEASURABLE_NOW")


def test_committed_outputs_match_a_fresh_run():
    with open(HERE / "CENSUS_T695.csv", newline="") as f:
        com = list(csv.DictReader(f))
    assert [r["line_id"] for r in com] == [r["line_id"] for r in ROWS]
    assert [r["cause"] for r in com] == [r["cause"] for r in ROWS]
    assert json.loads((HERE / "summary_t695.json").read_text())["straps"]["excavation_m3"] == S["straps"]["excavation_m3"]


def test_interior_main_zero_by_geometry():
    z = S["zero_zone"]
    assert z["zero"] and z["runs"] == 13 and z["D_max_m"] == 0.4 and z["lowest_blinding_bottom_m"] == 0.45
    assert z["evidence"]["sunken_hatches_on_ground_beam_plan"] == 0
    assert z["evidence"]["sunken_hatches_on_other_sheets"] > 0


def test_strap_trench_range():
    s = S["straps"]
    # low: drawn F10 / F outline, no blinding: 6.633533 m2 x 1.50; high: route-G box end, footing chain: 9.655236 x
    # 1.67 less the main exterior GB blinding cut it shares (0.030019 m2 x 0.10)
    assert s["excavation_m3"] == [9.950299, 16.121241]
    assert abs(6.633533 * 1.50 - s["excavation_m3"][0]) < 2e-6
    assert abs(9.655236 * 1.67 - 0.030019 * 0.10 - s["excavation_m3"][1]) < 2e-6
    assert s["backfill_m3"] == [6.437519, 10.952471]
    assert s["layers"] == [8, 10] and s["compaction_footprint_m2"] == [6.633533, 9.655236]
    assert len(s["scenarios"]) == 12


def test_annex_lower_bound_only():
    a = S["annex"]
    assert a["at_least_m3"] == 0.877899 and a["upper"] is None and len(a["skipped"]) == 5


def test_disposal_held_names_the_tests():
    m = S["material"]
    assert m["state"] == "HELD" and any("ASTM D1557" in t for t in m["missing_tests"])
