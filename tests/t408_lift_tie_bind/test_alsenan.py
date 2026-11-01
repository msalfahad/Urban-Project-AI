"""T-408 on the development villa: committed outputs of research/agents_t408/t408_alsenan.py run on the Drive copies
against the candidate of record ARCH_TAKEOFF_V3.0.34 (V3_0_34_BOQ_LINES.json 4c7f581c, own reproduction). Private
inputs are not needed: the committed CSV / JSON are pinned. Hand values: GF storey 1.00 -> 5.50 = 4.50 > 4.30 (tie),
1F / 2F 4.20 (none); clear runs S 1.80 + N 1.80 + W 1.20 + E 0.70 = 5.50 m on the GF columns (0.20 x 0.50 x 3, 0.25 x
1.00); 5.50 x 0.20 + 0.50 = 1.60 = 2.20^2 - 1.80^2; ring beams 0.650 + 0.650 + 0.464 = 1.764 m3; cap 1.80^2 x 0.16."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t408"
S = json.loads((D / "summary_t408.json").read_text(encoding="utf-8"))


def test_tie_length_same_on_every_plan_that_draws_the_gf_columns():
    for plan in ("GF_ROOF_SLAB_PLAN (columns under the GF roof)", "P1_COLUMNS_PLAN", "GROUND_BEAMS_PLAN (pit ring, T-401)"):
        p = S["plans"][plan]
        assert p["runs_m"] == pytest.approx({"S": 1.80, "N": 1.80, "W": 1.20, "E": 0.70})
        assert p["run_total_m"] == pytest.approx(5.50)
        assert p["band_m"] == pytest.approx({"W": 0.2, "E": 0.2, "S": 0.2, "N": 0.2})
    assert S["gf_band_closure"]["closes"] is True


def test_tie_only_in_the_gf_and_held_missing_never_zero():
    st = {s["storey"]: s for s in S["storeys"]}
    assert st["GF"]["tie_required"] and st["GF"]["height_m"] == pytest.approx(4.50)
    assert not st["1F"]["tie_required"] and not st["2F"]["tie_required"]
    for c in st["GF"]["components"]:
        assert c["value"] is None and c["status"] == "MISSING" and c["missing"]
        assert c["length_m"] == pytest.approx(5.50)
    assert st["GF"]["clash"]["state"] == "OPEN"
    assert S["tie_lines_v3034"] == []


def test_ring_beams_and_cap_bound_unchanged_in_v3034():
    assert S["ring_beam_lines"] == 12 and S["ring_all_bound"] is True
    assert S["ring_beams_m3"] == pytest.approx(1.764)
    assert S["cap_bound"] is True and S["cap_m3"] == pytest.approx(1.80 * 1.80 * 0.16)


def test_only_drift_is_the_t397_column_range():
    rows = list(csv.DictReader((D / "BINDING_T408.csv").open(encoding="utf-8")))
    bad = [r for r in rows if r["result"] != "BOUND"]
    assert [r["line_id"] for r in bad] == ["L-755eb56b55e86301b488"]
    assert [d["line_id"] for d in S["drift_v3032_v3034"]] == ["L-755eb56b55e86301b488"]
    assert S["drift_v3032_v3034"][0]["v34"][2] == pytest.approx([0.756, 1.05])   # 0.20 x 0.90 .. 0.25 x 1.00 x 4.20


def test_pit_wall_line_names_only_one_of_its_two_facts():
    by = {r["line_id"]: r for r in S["lift_lines_v3034"]}
    assert by["L-684fcad323adc0c8a267"]["facts_not_named"] == ["GF build-up F.F.L. -> slab-on-grade top"]
    for lid in ("L-e3eb00574a3c1c605077", "L-6d72f51dfe7ec1097f00"):
        assert len(by[lid]["facts_not_named"]) == 2


def test_gf_lift_block_walls_held_with_the_tie():
    blk = S["gf_lift_block_lines"]
    assert len(blk) == 3
    for v in blk.values():
        assert v["state"] == "BLOCKED_RFI" and v["value"] is None
        assert v["walls"] == ["GF-W08", "GF-W09", "GF-W13", "GF-W14"]
