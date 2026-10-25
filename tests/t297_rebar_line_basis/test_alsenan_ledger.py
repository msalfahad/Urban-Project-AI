"""T-297 Alsenan rebar line-to-member basis ledger, rebuilt from committed inputs only (own ARCH_TAKEOFF_V3.0.16 run on
the Drive copies, extracted by research/agents_t297/t297_extract.py; merged hand ledgers T-148 / T-138 / T-149 / T-152,
T-280 core datums). Re-builds without writing and compares with the committed outputs; checks the ledger invariants
(development villa; not an accuracy claim)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t297"
sys.path.insert(0, str(HERE))
import pytest  # noqa: E402

import t297_ledger as L  # noqa: E402


@pytest.fixture(scope="module")
def built():
    import t297_alsenan as A
    cand, rows, summary = A.build()
    return A, cand, rows, summary


def test_rebuild_equals_committed_outputs(built):
    A, CAND, ROWS, SUMMARY = built
    assert A.csv_text(ROWS) == (HERE / "LINE_BASIS_T297.csv").read_text(encoding="utf-8")
    assert json.loads((HERE / "LINE_BASIS_SUMMARY_T297.json").read_text(encoding="utf-8")) == SUMMARY


def test_every_reinforcement_line_of_the_candidate_once(built):
    A, CAND, ROWS, SUMMARY = built
    ids = [r.line_id for r in ROWS]
    assert len(ids) == len(set(ids)) == CAND["rebar_lines"] == len(CAND["lines"])
    assert SUMMARY["candidate"]["candidate_lines_csv_sha256"] == CAND["candidate_lines_csv_sha256"]


def test_no_bound_or_held_carries_a_quantity_and_every_bound_has_a_datum(built):
    A, CAND, ROWS, SUMMARY = built
    for r in ROWS:
        L.check_row(r)
        if r.status == "BOUND":
            assert r.quantity_kg is None and r.datum and r.datum_status
        if r.status in L.NO_QUANTITY:
            assert r.quantity_kg is None and r.bound_low_kg is None


def test_residuals_against_the_candidate_and_the_source_ledgers_are_zero(built):
    A, CAND, ROWS, SUMMARY = built
    for k, v in SUMMARY["residuals_vs_candidate_kg"].items():
        assert abs(v) <= 5e-6, k
    for k, v in SUMMARY["residuals_vs_sources_kg"].items():
        assert abs(v["residual_kg"]) <= v["tolerance_kg"], k


def test_line_state_and_basis_agree(built):
    A, CAND, ROWS, SUMMARY = built
    for r in ROWS:
        if r.line_state == "NOT_APPLICABLE_WITH_EVIDENCE":
            assert r.status == "NOT_APPLICABLE"
        if r.line_state in ("BLOCKED_RFI", "EXCLUDED_WITH_REASON"):
            assert r.status in ("HELD", "BOUND")
        if r.status in ("DRAWING_CONFIRMED", "VERIFIED", "CONVENTION", "ASSUMED_OWNER_APPROVED"):
            assert r.line_state in ("SOURCE_DERIVED", "MEASURED", "PROVISIONAL")
            assert abs(r.quantity_kg - r.line_kg) <= 5e-7


def test_alsenan_pins(built):
    """engineering results of the candidate of record (csv a4dc01dd), per family and basis status"""
    A, CAND, ROWS, SUMMARY = built
    t = SUMMARY["totals_by_family_status"]
    assert CAND["candidate_lines_csv_sha256"].startswith("a4dc01dd") and len(ROWS) == 2505
    assert t["COLUMNS|DRAWING_CONFIRMED"] == {"lines": 32, "kg": 1887.128, "t": 1.887128}
    assert t["BEAMS|DRAWING_CONFIRMED"]["kg"] == 5171.031
    assert t["GROUND_BEAMS|DRAWING_CONFIRMED"]["kg"] == 1252.907
    assert t["FOOTINGS|CONVENTION"]["kg"] == 874.862227 and "FOOTINGS|DRAWING_CONFIRMED" not in t
    assert t["GROUND_SLAB|CONVENTION"]["kg"] == 1064.239762
    assert t["BEAMS|BOUND"]["high_kg"] is None and t["BEAMS|BOUND"]["high_open_lines"] == 51
    assert not any(k.endswith(("|VERIFIED", "|ASSUMED_OWNER_APPROVED")) for k in t)
    f = SUMMARY["coverage_findings"][0]["foundation_column_lines_by_bar_group"]
    assert f == {"MAIN": {"BLOCKED_RFI -> HELD": 28}, "TIES": {"BLOCKED_RFI -> HELD": 28}}
    by = {r.line_id: r for r in ROWS}
    lap = [r for r in ROWS if r.family == "COLUMNS" and r.bar_group.startswith("LAP")]
    assert len(lap) == 56 and all(r.status == "BOUND" and r.lap_basis == "NOTE_READING" for r in lap)
    assert by["L-03062228b230a7fff3bd"].quantity_kg == 53.096     # COL-1F-35 C2: 8 x 4.20 x 256 / 162
    assert round(by["L-00fbbdf4ad454311231c"].quantity_kg, 6) == 40.177778 and \
        by["L-00fbbdf4ad454311231c"].status == "CONVENTION"      # F5 bottom long: 20 x 2.26 x 0.888889


def test_the_ledger_holds_for_the_v3017_candidate_too():
    """T-254 (V3.0.17, csv 429008af) merged during this task: its 2,505 reinforcement lines equal V3.0.16's line by
    line (ids, states, quantities, ranges, locations), so every row of this ledger applies to V3.0.17 unchanged"""
    eq = json.loads((HERE / "REBAR_EQUIVALENCE_T297.json").read_text(encoding="utf-8"))
    assert eq["later_csv_sha256"].startswith("429008af") and eq["later_json_sha256"].startswith("366be2f8")
    assert eq["same_line_ids"] and eq["differing"] == [] and eq["rebar_lines_later"] == eq["rebar_lines_base"] == 2505
