"""T-263 development-villa ledger (Alsenan; not an accuracy claim) from committed merged inputs only (T-242, T-253,
T-233, T-205). Re-runs without writing and pins the engineering results; the committed LEDGER_T263.csv must match."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t263"
sys.path.insert(0, str(HERE))
import buried_wp_v1 as W  # noqa: E402
import t263_alsenan_check as C  # noqa: E402

ROWS, SUM = C.main(write=False)
BY = {(r.element, r.face): r for r in ROWS}


def test_sources_pinned():
    assert SUM["sources"]["structural_sha_prefix"] == "9f9d1179"
    assert SUM["runs"] == 59


def test_ground_beam_faces_drawing_confirmed():
    g = SUM["gb_faces_drawing_confirmed"]
    # interior 5 single-title runs: 2 x 0.30 x (4.400 + 3.228 + 3.525 + 3.525 + 4.225 = 18.903) = 11.3418
    assert g["by_class"]["INTERIOR MAIN"] == [10, pytest.approx(11.3418)]
    # main exterior inner faces on fill: 0.85 x 28.3089 m (11 runs) = 24.0626
    assert g["by_class"]["EXTERIOR MAIN"] == [11, pytest.approx(24.062565)]
    assert g["m2"] == pytest.approx(35.404365) and SUM["measured_total_m2"] == g["m2"]


def test_main_exterior_outer_faces_above_natural_ground():
    assert SUM["gb_faces_excluded_above_ground"] == 14
    r = BY[("7E0+FD#2", "side A (OUTSIDE)")]
    assert r.status == W.EXCLUDED and r.readings["face_m2"] == pytest.approx(3.25 * 0.95)


def test_held_faces_never_zero():
    held = [r for r in ROWS if r.status == W.HELD]
    assert held and all(r.qty is None for r in held)
    assert SUM["gb_faces_held"] == 85
    assert BY[("109+7CB#2", "side B (PANEL: HELD)")].held_why.startswith("PANEL_HELD")          # GS-16
    assert BY[("170+7C3#1", "side A (PANEL: SPLIT_LEVEL)")].held_why.startswith("PANEL_SPLIT")  # GS-08
    assert BY[("136+7D5#1", "side B (OUTSIDE)")].held_why.startswith("DEPTH_HELD")              # annex CONFLICT


def test_footing_tops_and_necks():
    f = SUM["footing_tops"]
    # 23 exact outlines: 104.72 .. 104.75 single reading in all; 109.85 membrane outlines - necks 5.10 .. 5.13
    assert f["single_reading_m2_exact"] == pytest.approx(92.60)
    assert f["single_reading_conflict"] == {"FTG:1B1A": {"SINGLE_high": 12.15, "SINGLE_low": 12.12}}
    assert f["two_tag_held"] == ["FTG:1B1B"] and f["outlines_held_detail"] == 24
    assert BY[("FTG:1B2B", "top outside the necks")].status == W.EXCLUDED
    n = SUM["necks"]
    assert n["held"] == 32 and n["excluded_lift"] == 4
    assert n["m2_per_m_height"] == [pytest.approx(55.6), pytest.approx(55.8)]


def test_committed_ledger_matches_the_rerun():
    with open(HERE / "LEDGER_T263.csv", encoding="utf-8") as fh:
        led = list(csv.DictReader(fh))
    assert len(led) == len(ROWS)
    for a, r in zip(led, ROWS):
        d = r.as_dict()
        assert (a["element"], a["face"], a["status"]) == (d["element"], d["face"], d["status"])
        assert (a["qty"] or None) == (None if d["qty"] is None else str(d["qty"]))
    committed = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert committed == json.loads(json.dumps(SUM, sort_keys=True))
