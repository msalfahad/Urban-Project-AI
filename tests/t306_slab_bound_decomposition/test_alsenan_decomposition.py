"""T-306 Alsenan pins: the 294 BOUND suspended-slab reinforcement lines of the candidate (T-297 r2 basis ledger)
decompose by cause with residual 0.000 kg; merged research files only (numbers, no drawing content)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t306"))
import t306_alsenan as A  # noqa: E402


@pytest.fixture(scope="module")
def run():
    return A.run()


def test_every_bound_line_once_and_closure(run):
    dec, s = run
    assert s["lines"] == 294 and len({r["line_id"] for r in dec}) == 294
    assert s["bound_low_kg"] == pytest.approx(4643.766, abs=1e-6)
    assert s["bound_high_kg"] == pytest.approx(6832.326, abs=1e-6)
    assert s["spread_kg"] == pytest.approx(2188.560, abs=1e-6)
    assert abs(s["residual_kg"]) < 1e-6
    assert abs(s["causes_kg"]["STORAGE_ROUNDING"]) < 0.02


def test_cause_totals(run):
    c = run[1]["causes_kg"]
    assert c["ANCHORAGE_LENGTH"] == pytest.approx(746.560, abs=1e-3)
    assert c["TOP_NOTE2_WORDING"] == pytest.approx(781.385, abs=1e-3)
    assert c["TOP_NOTE2_VS_P15"] == pytest.approx(185.612, abs=1e-3)
    assert c["TOP_CROSSING"] == pytest.approx(146.686, abs=1e-3)
    assert c["COUNT_CONVENTION"] == pytest.approx(318.227, abs=1e-3)
    assert c["LABEL_MEANING"] == pytest.approx(10.081, abs=1e-3)


def test_findings_pinned(run):
    s = run[1]
    out = {(o["line"], o["reading"]) for o in s["readings_outside_bound"]}
    assert len(out) == 9
    assert sum(1 for _, r in out if r == "no_note2_bars_over_TB_mesh") == 4
    assert sum(1 for _, r in out if r == "label_n_in_all_40d") == 3
    assert ("L-b10f318a155d5ee1b289", "i_B") in out and ("L-b10f318a155d5ee1b289", "ii_A+cross") in out
    assert s["tb_top_low_kg"] == pytest.approx(28.663, abs=1e-3)
    assert s["skew_B_below_A"] == ["L-4a2be75de3f9e0f69614"]
    assert s["drawing_confirmed_components"] == 0


def test_development_end_census_p15(run):
    e = run[1]["dev_end_census"]
    # the census re-derives the candidate's own development figures from the merged T-152 input (2 ends per bar)
    assert e["model_low"] == pytest.approx(939.794, abs=0.02) and e["model_high"] == pytest.approx(1741.976, abs=0.02)
    # p.15: no development at continuous ends (50 % stop 0.125 L short, 50 % continue = the crossing half)
    assert e["cont_low"] == pytest.approx(556.205, abs=1e-3) and e["cont_high"] == pytest.approx(1027.310, abs=1e-3)
    assert e["noncont_low"] == pytest.approx(384.089, abs=1e-3) and e["noncont_high"] == pytest.approx(718.120, abs=1e-3)
    assert (e["extra_segment_ends_A"], e["extra_segment_ends_B"]) == (2, 8)
    assert len(e["lines_with_opening_segment_ends"]) == 4
