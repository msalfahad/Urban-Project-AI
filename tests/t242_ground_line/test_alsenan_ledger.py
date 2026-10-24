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
    assert len(ids) == len(set(ids)) == 59 + 2 + 1


def test_classification_counts():
    assert SUM["classification"] == {"INTERIOR": 29, "EXTERIOR": 27, "COURT": 1, "CANDIDATES": 4}
    assert BY["10A+7C9#1"]["component"] == "GB-EXTERIOR"          # +0.15 passage beside it (S1), S2 overruled
    assert BY["109+7CB#1"]["component"] == "GB-CANDIDATES"
    assert BY["1811+1812#1"]["component"] == "GB-COURT"


def test_components_pinned():
    c = SUM["components"]
    assert c["interior"]["calculated_m3"] == pytest.approx(1.7404, abs=1e-4)
    assert c["interior"]["calculated_runs"] == 4
    assert (c["interior"]["held_low_m3"], c["interior"]["held_high_m3"]) == pytest.approx((9.3690, 10.2055), abs=1e-3)
    e = SUM["exterior_split"]
    main = [v for k, v in e.items() if k.startswith("HELD")][0]
    annex = [v for k, v in e.items() if k.startswith("CONFLICT")][0]
    assert (main["runs"], main["low_m3"], main["high_m3"]) == (18, pytest.approx(13.584, abs=1e-3),
                                                               pytest.approx(16.131, abs=1e-3))
    assert annex["runs"] == 9
    assert c["boundary_gb"]["held_high_m3"] == pytest.approx(3.5256, abs=1e-4)
    assert c["boundary_gb"]["held_low_m3"] is None
    assert SUM["line_closable"] is False
    assert any("ground_slab" in w for w in SUM["line_not_closable_because"])


def test_lift_ends_and_corner_piece():
    assert BY["15D+7C8#1"]["L_m"] == 2.9 and BY["17C+7E3#1"]["L_m"] == 3.228
    assert BY["17C+7E3#1"]["value_m3"] == "0.3874"                  # 0.30 x 0.40 x 3.228
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
