"""T-242 Alsenan ledger (committed inputs only: ALSENAN_GROUND_INPUT.json from 'ST7757 dxf.dxf' sha 9f9d1179 and the
architectural DXF sha ab54dd55, T-230 / T-141 / T-138 records, the freelancer's committed cells). Re-runs the check
without writing and pins the engineering results."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t242"
sys.path.insert(0, str(HERE))
import t242_alsenan_check as C  # noqa: E402

ROWS, SUM = C.main(write=False)
INP = json.loads((HERE / "ALSENAN_GROUND_INPUT.json").read_text(encoding="utf-8"))
BY = {r["run"]: r for r in ROWS}


def test_input_is_values_only():
    txt = (HERE / "ALSENAN_GROUND_INPUT.json").read_text(encoding="utf-8")
    assert INP["source"]["structural_sha256"].startswith("9f9d1179")
    assert INP["source"]["architectural_sha256"].startswith("ab54dd55")
    assert not re.search(r"\d{5,}\.\d", txt)           # no sheet coordinates


def test_alignment_of_the_two_sheets():
    a = INP["alignment"]
    assert a["architectural_columns"] == 30 and a["level_texts_paired"] == a["level_texts_same_value"] == 14
    assert a["level_text_residual_mm"] <= 1.0 and a["column_centroid_residual_mm_max"] <= 75.0


def test_every_run_once_and_partition_conserves():
    p = INP["partition"]
    named = sum(x["plan_m2"] for x in p["unbilled_pieces"])
    assert p["spans_m2"] + p["columns_in_strips_m2"] + p["arcs_net_m2"] + named == pytest.approx(
        p["drawn_band_strips_m2"], abs=0.001)
    assert all(d["plan_m2"] == 0.0 for d in p["span_span_doubles"] + p["span_column_overlaps"])
    ids = [r["run"] for r in ROWS]
    assert len(ids) == len(set(ids)) == 59 + 2 + 1 + 29          # straight + curved + boundary + slab panels
    assert INP["slab_panels_solid_m2"] + sum(p["plan_m2"] for p in INP["slab_panels"]) == pytest.approx(290.464, abs=0.01)


def test_classification_counts():
    assert SUM["classification"] == {"INTERIOR": 32, "EXTERIOR": 26, "COURT": 3, "CANDIDATES": 0}
    assert BY["10A+7C9#1"]["component"] == "GB-EXTERIOR"          # +0.15 passage beside it (S1), S2 overruled
    assert BY["109+7CB#1"]["component"] == "GB-INTERIOR"          # rooms on both sides (S4), no outside side
    assert BY["178+7DB#1"]["component"] == "GB-COURT"             # stair court one side, a room-less panel the other
    assert BY["1811+1812#1"]["component"] == "GB-COURT"


def test_components_pinned():
    c = SUM["components"]
    assert c["interior"]["calculated_m3"] == pytest.approx(2.2684, abs=1e-4)
    assert c["interior"]["calculated_runs"] == 5
    assert (c["interior"]["held_low_m3"], c["interior"]["held_high_m3"]) == pytest.approx((9.7673, 10.7365), abs=1e-3)
    e = SUM["exterior_split"]
    main = [v for k, v in e.items() if k.startswith("HELD")][0]
    annex = [v for k, v in e.items() if k.startswith("CONFLICT")][0]
    assert (main["runs"], main["low_m3"], main["high_m3"]) == (17, pytest.approx(13.440, abs=1e-3),
                                                               pytest.approx(15.960, abs=1e-3))
    assert annex["runs"] == 9
    assert c["boundary_gb"]["held_high_m3"] == pytest.approx(3.5256, abs=1e-4)
    assert c["boundary_gb"]["held_low_m3"] is None
    g = c["ground_slab"]
    assert g["calculated_m3"] == pytest.approx(20.4328, abs=1e-4) and g["calculated_runs"] == 27
    assert (g["held_low_m3"], g["held_high_m3"]) == pytest.approx((0.0, 1.2304), abs=1e-4)
    assert SUM["line_closable"] is False
    assert any("exterior" in w for w in SUM["line_not_closable_because"])


def test_lift_ends_and_corner_piece():
    assert BY["15D+7C8#1"]["L_m"] == 2.9 and BY["17C+7E3#1"]["L_m"] == 3.228
    assert BY["17C+7E3#1"]["value_m3"] == "0.3874"                  # 0.30 x 0.40 x 3.228
    assert BY["109+7CB#1"]["value_m3"] == "0.5280"                  # 0.30 x 0.40 x 4.400
    assert "corner square" in BY["7D4+F8#2"]["end_notes"]


def test_no_exterior_run_released():
    for r in ROWS:
        if "EXTERIOR" in r["component"]:
            assert r["status"] in ("HELD", "CONFLICT") and r["value_m3"] == ""


def test_freelancer_cells():
    f = SUM["freelancer"]
    assert f["total_m3"] == pytest.approx(75.09) and f["summary_row_18"] == pytest.approx(75.09)
    assert f["longitudinal_m3"] + f["transverse_m3"] == pytest.approx(37.98)
    assert f["boundary_m3"] == pytest.approx(7.56) and f["slab_m3"] == pytest.approx(29.55)


def test_freelancer_reconciled_to_named_causes():
    r = SUM["freelancer_reconciliation_building_beams"]
    assert r["length_effect_m3"] == pytest.approx(3.558, abs=1e-3)
    assert abs(r["residual_low_m3"]) < 1e-3 and abs(r["residual_high_m3"]) < 1e-3
    b = SUM["freelancer_reconciliation_boundary"]
    assert b["his_m3"] - b["drawn_m3"] == pytest.approx(b["section_effect_m3"] + b["length_effect_m3"], abs=1e-3)
