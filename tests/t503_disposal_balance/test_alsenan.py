"""T-503 on the candidate of record V3.0.48 (lines sha 33a81c53): the B1-04 balance from the pinned merged summaries.
Re-runs without writing and pins the engineering results."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t503"
sys.path.insert(0, str(HERE))
import disposal_balance_v1 as B  # noqa: E402
import t503_alsenan as A  # noqa: E402

R = A.main(write=False)
TERMS = {t["line_id"]: t for t in R["terms"]}


def test_every_term_is_a_candidate_earthworks_line():
    assert len(TERMS) == 19 and R["disposal_line"] == "L-78d7c8a989ab34527a1c"
    assert sum(1 for t in TERMS.values() if t["role"] == B.EXC) == 12
    assert sum(1 for t in TERMS.values() if t["role"] == B.FILL) == 7


def test_excavation_sum_from_the_valued_and_ranged_lines():
    e = R["excavation"]
    assert e["low"] == pytest.approx(208.164757 + 17.776576 + 7.2645)
    assert e["high"] == pytest.approx(208.164757 + 17.776576 + 8.39175)
    assert e["open"] and len(e["held_lines"]) == 9


def test_trench_never_uses_the_held_defective_bound():
    t = TERMS[A.TRENCH_PENDING]
    assert t["low"] is None and t["high"] is None and t["status"] == B.HELD
    assert A.TRENCH_PENDING in R["excavation"]["held_lines"]


def test_fill_demand_pits_backfill_and_six_held_lines():
    d = R["fill_demand"]
    assert d["low"] == pytest.approx(119.963335) and d["high"] == pytest.approx(128.643547)
    assert "L-eac006402d3035da007b" in d["held_lines"] and len(d["held_lines"]) == 6   # Z2 raised fill HELD


def test_disposal_is_a_held_range_never_a_number_never_zero():
    d = R["disposal_insitu_m3"]
    assert d["high"]["value"] == pytest.approx(234.333083) and d["high"]["qualifier"] == B.AT_LEAST
    assert d["low"]["value"] is None
    miss = " ".join(d["low"]["missing"])
    for need in ("in-situ dry density", "placement target", "geotechnical", "L-eac006402d3035da007b"):
        assert need in miss
    assert R["state"] == "HELD_RANGE" and not R["single_number"]
    i = R["import_compacted_m3"]
    assert i["high"]["value"] == pytest.approx(128.643547) and i["high"]["qualifier"] == B.AT_LEAST
    assert i["low"]["value"] is None
    assert R["payable"]["basis"] == B.IN_SITU and R["disposal_loose_m3"]["low"] is None


def test_committed_summary_matches_the_run():
    s = json.loads((HERE / "summary_t503.json").read_text(encoding="utf-8"))
    assert s == json.loads(json.dumps(R, sort_keys=True))
