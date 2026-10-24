"""T-272 Alsenan stirrup ledger (committed inputs only: the merged T-265 ledger and the T-242 ring radii). Re-runs the
check without writing and pins the engineering results; the committed LEDGER_T272.csv / summary.json equal a fresh run."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t272"
sys.path.insert(0, str(HERE))
import t272_alsenan_check as C  # noqa: E402
import t272_stirrups as S  # noqa: E402

ROWS, SUM = C.main(write=False)


def test_scope_is_the_t265_runs():
    assert SUM["exterior"]["runs"] == 17 and SUM["exterior"]["length_m"] == pytest.approx(55.9912, abs=1e-4)
    assert SUM["boundary"]["runs"] == 5 and SUM["boundary"]["length_m"] == pytest.approx(44.07, abs=1e-4)


def test_exterior_count_envelope_and_t265_reading():
    e = SUM["exterior"]
    assert e["count_envelope"] == [361, 400]
    assert e["half_spacing_reading"] == 380 == e["t265_range"][0]     # T-265 A = the half-spacing reading
    assert e["t265_range"] == [380, 397]
    assert e["count_status"].startswith("HELD")


def test_one_run_by_hand():
    r = [x for x in ROWS if x["run"] == "7D0+FC#2"][0]                  # 5.745 / 0.15 = 38.3
    assert (r["count_low"], r["count_half_spacing_reading"], r["count_high"]) == (38, 39, 40)
    assert r["qa_sharp_perimeter_m"] == pytest.approx(2 * (0.242 + 0.892), abs=1e-9)


def test_ring_counted_on_face_arcs():
    r = [x for x in ROWS if x["run"] == C.RING][0]
    assert (r["count_low"], r["count_high"]) == (38, 45)                 # 5.7068 / 0.15 -> 39 - 1; 6.4678 -> 44 + 1
    assert SUM["ring"]["inner_arc_m"] == pytest.approx(5.7068, abs=1e-4)


def test_every_mass_is_held_never_zero():
    for r in ROWS:
        assert r["kg"] is None and r["kg_status"] == S.HELD and r["cut_length_m"] is None
        assert r["count"] is None
    assert SUM["exterior"]["kg"] is None and SUM["boundary"]["kg"] is None


def test_boundary_link_has_no_drawn_closure_and_no_count():
    b = SUM["boundary"]
    assert any("closure" in h for h in b["cut_length_held"])
    assert SUM["design_flags"]["BOUNDARY_GB"] and not SUM["design_flags"]["GB_EXTERIOR"]
    assert all("M4" in r["count_basis"] for r in ROWS if r["family"] == "BOUNDARY_GB")


def test_qa_reading_is_labelled_and_separate():
    assert SUM["exterior"]["qa_kg_at_high_count_no_hooks"] == pytest.approx(358.4, abs=0.01)
    assert all(r["qa_status"] == S.QA_ONLY for r in ROWS)


def test_committed_files_equal_a_fresh_run():
    committed = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert committed == json.loads(json.dumps(SUM, ensure_ascii=False))
    rows = list(csv.DictReader((HERE / "LEDGER_T272.csv").open(encoding="utf-8")))
    assert len(rows) == len(ROWS) == 22
    for got, want in zip(rows, ROWS):
        assert got["run"] == want["run"] and int(got["count_low"]) == want["count_low"]
        assert int(got["count_high"]) == want["count_high"] and got["kg"] == ""
