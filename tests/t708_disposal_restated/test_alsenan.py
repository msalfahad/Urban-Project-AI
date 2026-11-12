"""T-708 on the development villa (Drive 'Alsenan chalet project', 'ST7757 dxf.dxf' 9f9d1179) from the committed
values-only inputs (no drawing needed). Re-runs without writing; pins the results (not an accuracy claim)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t708"
sys.path.insert(0, str(HERE))
import t708_alsenan as A  # noqa: E402

S, REC, RA, RB = A.run(write=False)


def test_z2_owner_plan_x_depth_closes_to_named_causes():
    z = S["z2_reconciliation"]
    assert z["owner_plan_m2"] == 216.40885 and z["owner_depth_m"] == 0.85 and z["terms"] == 29 + 61
    lo, hi = z["ends"]["low"], z["ends"]["high"]
    assert lo["engine_m3"] == 136.900995 and hi["engine_m3"] == 163.479489
    assert lo["delta_by_cause_m3"]["PANEL_ANNEX_030"] == hi["delta_by_cause_m3"]["PANEL_ANNEX_030"] == -31.55978
    assert lo["delta_by_cause_m3"]["PANEL_MAIN_100"] == 0.0           # 147.49945 m2: engine depth = owner depth
    assert lo["delta_by_cause_m3"]["PANEL_HELD_LEVEL"] == -18.5224 and hi["delta_by_cause_m3"]["PANEL_HELD_LEVEL"] == 0
    beams = lambda e: round(sum(v for k, v in e["delta_by_cause_m3"].items() if k.startswith("BEAM_")), 6)  # noqa
    assert beams(lo) == 3.035655 and beams(hi) == 11.091749
    assert abs(lo["residual_m3"]) <= 3e-6 and abs(hi["residual_m3"]) <= 3e-6


def test_every_panel_term_is_a_candidate_ground_slab_line():
    ids = {t["id"].split()[0] for t in REC["terms"] if t["kind"] == "PANEL"}
    assert len(ids) == 26 and all(i.startswith("L-") for i in ids)


def test_candidate_of_record_balance_is_t505():
    a = S["balance"]["A_candidate_of_record"]["closure"]
    assert a["disposal_s0_m3"] == 234.333083 and a["import_s0_m3"] == 128.643547
    assert a["residual_disposal_m3"] == 0 and a["residual_import_m3"] == 0


def test_restated_on_t695_t700_geometry():
    b = S["balance"]["B_t695_t700_geometry"]
    assert b["closure"]["disposal_s0_m3"] == 271.861583 and b["closure"]["import_s0_m3"] == 292.123036
    assert b["E"] == [244.034031, 271.861583, 6] and b["D"] == [256.86433, 292.123036, 3]
    assert S["balance"]["s0_change_m3"] == {"disposal": 37.5285, "import": 163.479489}
    assert RB["disposal_insitu_m3"]["low"]["value"] is None and RB["import_compacted_m3"]["low"]["value"] is None
    assert [x["at_least_m3"] for x in b["beside"]["at_least"]] == [31.05, 12.688]
    assert S["break_even_yield_closed_parts"]["B"]["k_star"] == [0.835381, 1.058386]


def test_every_density_held_never_a_mass():
    for r in S["dry_mass_inputs"]:
        assert r["dry_t"] is None and r["state"] == "HELD"
    assert {r["zone"] for r in S["dry_mass_inputs"] if r["t700_zone"]} == {"Z1-PIT-FF", "Z1-TRENCH-ANNEX", "Z2"}


def test_committed_outputs_match_a_fresh_run():
    com = json.loads((HERE / "summary_t708.json").read_text())
    assert com == json.loads(json.dumps(S, sort_keys=True))
    with open(HERE / "WIRING_T708.csv", newline="") as f:
        w = list(csv.DictReader(f))
    assert [r["high_end_m3"] for r in w[:4]] == ["234.333083", "128.643547", "271.861583", "292.123036"]
