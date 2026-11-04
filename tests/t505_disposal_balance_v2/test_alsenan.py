"""T-505 on the candidate ARCH_TAKEOFF_V3.0.50 (T-497 MERGED 5f8814e8): the B1-04 balance with the loss accounts
from the pinned merged summaries. Re-runs without writing and pins the engineering results."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t505"
sys.path.insert(0, str(HERE))
import disposal_balance_v2 as B  # noqa: E402
import t505_alsenan as A  # noqa: E402

R = A.main(write=False)
TERMS = {t["line_id"]: t for t in R["terms"]}


def test_terms_are_the_v3050_earthworks_lines():
    assert len(TERMS) == 19 and R["candidate"]["method"] == "ARCH_TAKEOFF_V3.0.50"
    assert R["candidate"]["restated_m3"] == [1.069269, 1.176467]


def test_held_trench_bound_beside_never_summed():
    t = TERMS[A.TRENCH]
    assert t["low"] is None and t["status"] == B.HELD and A.TRENCH in R["excavation"]["held_lines"]
    assert R["held_bounds_beside"]["if_taken_s0_end_m3"] == [235.402352, 235.50955]


def test_s0_end_is_pure_geometry_and_unchanged_from_v1():
    d, i = R["disposal_insitu_m3"], R["import_compacted_m3"]
    assert d["high"]["value"] == pytest.approx(234.333083) and d["high"]["qualifier"] == B.AT_LEAST
    assert i["high"]["value"] == pytest.approx(128.643547) and i["high"]["qualifier"] == B.AT_LEAST
    assert R["v1_comparison"]["s0_unchanged"] is True


def test_reuse_end_held_names_the_loss():
    lo = R["disposal_insitu_m3"]["low"]
    assert lo["value"] is None and B.MISSING_LR in lo["missing"]
    assert R["losses"]["reuse"]["status"] == B.HELD and R["losses"]["import"]["status"] == B.HELD
    assert R["state"] == "HELD_RANGE" and not R["single_number"]
    assert R["import_procurement"]["high"]["procured_dry_t"] is None


def test_committed_summary_matches_the_run():
    s = json.loads((HERE / "summary_t505.json").read_text(encoding="utf-8"))
    assert s == json.loads(json.dumps(R, sort_keys=True))
