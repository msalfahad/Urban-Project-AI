"""T-700 on the development villa (Drive 'Alsenan chalet project', 'ST7757 dxf.dxf' 9f9d1179) from the committed
values-only inputs (no drawing needed): Z2, the lift pit FF, the annex bound and the wiring form. Re-runs without
writing; pins the results (development villa, not an accuracy claim)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t700"
sys.path.insert(0, str(HERE))
import t700_alsenan as A  # noqa: E402

ROWS, S = A.run(write=False)


def test_ground_slab_family_is_the_z2_plan():
    assert S["ground_slab_lines"] == 26 and S["ground_slab_m3"] == 21.640885
    by = S["z2"]["EG"]["by_class"]
    area = by["PANEL_MAIN_100"]["area_m2"] + by["PANEL_ANNEX_030"]["area_m2"] + by["PANEL_HELD_LEVEL"]["area_m2"]
    assert abs(area - 216.40885) < 1e-6
    assert by["PANEL_MAIN_100"]["fill_m3"] == [125.37453, 125.37453]          # 147.49945 x 0.85
    assert by["PANEL_ANNEX_030"]["fill_m3"] == [6.76281, 6.76281]             # 45.0854 x 0.15
    assert by["PANEL_HELD_LEVEL"]["fill_m3"] == [1.728, 20.2504]              # GS-08 lobby, GS-12, GS-16


def test_z2_range_and_eg_sensitivity():
    assert S["z2"]["EG"]["zone"]["fill_m3"] == [136.900995, 163.479489]
    assert S["z2"]["EG"]["zone"]["layers_max"] == 6
    assert S["z2"]["EG-0.10"]["zone"]["fill_m3"][0] > S["z2"]["EG"]["zone"]["fill_m3"][0]
    assert S["z2"]["EG+0.10"]["zone"]["fill_m3"][1] < S["z2"]["EG"]["zone"]["fill_m3"][1]
    assert S["z2"]["layers"] == {"main_panels": 6, "annex_panels": 1, "under_main_interior_beam_max": 4}
    # the 13 interior runs T-695 calculated as 0 cut: 7 fixed D 0.40 (+0.115 m3/m) and 6 D-34 0.30 / 0.40
    assert S["z2"]["EG"]["by_class"]["BEAM_MAIN_INT"] == {"L_m": 24.573, "fill_m3": [2.825895, 2.825895], "n": 7}


def test_lift_pit_at_least_only():
    f = S["lift_pit"]
    assert f["plan_own_m2"] == 20.7 and all(v == 0.0 for v in f["overlaps_m2"].values())
    assert f["AT_LEAST"]["excavation_m3"] == 31.05 and f["AT_LEAST"]["backfill_m3"] == 12.688
    assert f["S01_beside"]["excavation_m3"] == 34.155 and f["S01_beside"]["backfill_m3"] == 15.067
    assert f["upper"] is None


def test_annex_bounded_by_the_foundation_datum():
    a = S["annex"]
    assert a["low_m3"] == 0.877899 and a["R3_S01"]["high_m3"] == 21.407259
    assert a["route_g_L_m"] >= a["ledger_L_m"] and a["no_datum"] == "AT_LEAST"


def test_wiring_form_every_b1_line_once_and_material_held():
    ids = [r["element_id"] for r in ROWS]
    assert len(ROWS) == 21 and len(set(ids)) == 21      # 20 lines + the T-695 strap-backfill split (new B1-03 element)
    assert sum(1 for r in ROWS if r["line_id"].startswith("L-")) == 20
    z2 = next(r for r in ROWS if r["element_id"] == "EW-T350:B1-03:Z2")
    assert (z2["bound"], z2["low_m3"], z2["high_m3"]) == ("RANGE", 136.900995, 163.479489)
    assert all(r["missing_input"] for r in ROWS if r["report_class"] == "HELD")
    assert S["material"]["state"] == "HELD" and len(S["material"]["missing_tests"]) == 5


def test_committed_outputs_match_a_fresh_run():
    with open(HERE / "WIRING_T700.csv", newline="") as f:
        com = list(csv.DictReader(f))
    assert [r["element_id"] for r in com] == [r["element_id"] for r in ROWS]
    assert json.loads((HERE / "summary_t700.json").read_text())["z2"]["EG"]["zone"] == S["z2"]["EG"]["zone"]
