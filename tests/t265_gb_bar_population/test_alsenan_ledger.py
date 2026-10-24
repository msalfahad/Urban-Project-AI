"""T-265 Alsenan ledger (committed inputs only: the merged T-253 ledger). Re-runs the check without writing and pins
the engineering results; the committed LEDGER_T265.csv / summary.json must equal a fresh run."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t265"
sys.path.insert(0, str(HERE))
import t265_alsenan_check as C  # noqa: E402
import t265_gb_bars as G  # noqa: E402

ROWS, SUM = C.main(write=False)


def test_lengths_are_the_merged_geometry():
    assert SUM["lengths_m"] == {"boundary_band": 44.07, "main_exterior": 55.9912, "annex_conflict": 29.7063}


def test_boundary_band_tb_read_per_layer():
    assert SUM["tb_reading"]["reading"] == "PER_LAYER_BY_LEADER"
    b = SUM["families"]["BOUNDARY_GB"]
    assert b["by_component_kg"] == {"TOP": pytest.approx(106.639, abs=1e-3),
                                    "BOTTOM_ROW_1": pytest.approx(208.925, abs=1e-3)}
    assert b["released_lower_bound_kg"] == pytest.approx(315.564, abs=1e-3)
    assert SUM["literal_tb_both_layers_kg_rejected"] == pytest.approx(631.126, abs=1e-3)
    assert SUM["boundary_bottom_fits"]["cover_0.07_soil"] is False


def test_main_exterior_population():
    e = SUM["families"]["GB_EXTERIOR"]
    assert e["by_component_kg"]["SIDE"] == pytest.approx(199.082, abs=1e-3)       # 2 levels x 2 d12 at D 0.95
    assert e["released_lower_bound_kg"] == pytest.approx(995.396, abs=1e-3)
    sides = [r for r in ROWS if r["component"] == "SIDE" and r["status"] == G.RELEASED_LB]
    assert len(sides) == 17 and all(r["n_bars"] == 4 for r in sides)


def test_stirrup_counts_match_ceil_rule_on_the_south_strip():
    st = {r["member"]: r["n_bars"] for r in ROWS if r["component"] == "STIRRUP_COUNT" and r["family"] == "GB_EXTERIOR"}
    assert [st[k] for k in ("7D0+FC#1", "7D0+FC#2", "7D0+FC#3", "7D0+FC#4")] == ["20..21", "39..40", "43..44", "8..9"]


def test_annex_court_held_and_paving_no_rebar():
    annex = [r for r in ROWS if r["family"] == "GB_EXTERIOR" and r["component"] == "ALL"]
    assert len(annex) == 9 and all(r["status"] == G.HELD and r["kg"] is None for r in annex)
    court = [r for r in ROWS if r["family"] == "GB_COURT"]
    assert len(court) == 3 and all(r["kg"] is None for r in court)
    assert SUM["families"]["GB_COURT"]["released_lower_bound_kg"] is None
    pav = [r for r in ROWS if r["family"] == "PAVING"]
    assert pav[0]["status"] == G.NO_REBAR and pav[0]["kg"] is None


def test_committed_outputs_equal_a_fresh_run():
    committed = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert committed == json.loads(json.dumps(SUM, ensure_ascii=False))
    with (HERE / "LEDGER_T265.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(ROWS)
    for a, b in zip(rows, ROWS):
        assert a["member"] == b["member"] and a["component"] == b["component"]
        assert a["kg"] == ("" if b["kg"] is None else str(b["kg"]))
