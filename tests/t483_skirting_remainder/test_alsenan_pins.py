"""T-483: pins of the development-villa run (research/agents_t483/summary_t483.json, from v3049_apply.py on the
candidate of record's V3_0_48 lines of a v3049_run.py chain on the Drive copies): the base is V3.0.48 e86a53a8, five
FIN.SKIRTING lines change, nothing is added, certain skirting rises by the W11 / W12 bases and the dressing walk only,
and the inputs builder reproduces the merged T-481 hand figures without private data."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "agents_t483")]

from engine.source import arch_v3049 as A  # noqa: E402
import t483_inputs as I  # noqa: E402

S = json.loads((ROOT / "research/agents_t483/summary_t483.json").read_text(encoding="utf-8"))


def test_base_is_candidate_of_record_and_only_skirting_moves():
    assert S["base_sha256"].startswith("e86a53a8")
    assert (S["lines"]["added"], S["lines"]["replaced"]) == (0, 5)
    assert S["lines"]["outside_identical"] == S["lines"]["base"] - 5
    t = S["totals_moved_by_code"]
    assert list(t) == ["FIN.SKIRTING|lm"]
    b, a = t["FIN.SKIRTING|lm"]["base"], t["FIN.SKIRTING|lm"]["v3_0_49"]
    assert a["released"] - b["released"] == pytest.approx(3.90984 + 5.1, abs=2e-6)
    assert (b["held_high"], a["held_high"]) == (pytest.approx(15.730915), pytest.approx(2.2))


def test_rows_by_hand():
    by = {r["line_id"]: r for r in S["rows"]}
    assert by["L-d32414916cfbd04c27be"]["after"]["value"] == pytest.approx(20.127876 - 2.0, abs=2e-6)
    assert by["L-4a85470b3a822d6fb7bb"]["after"]["value"] == pytest.approx(6.9 - 0.8 - 1.0)
    for lid in ("L-836720153cd9a3578f63", "L-e7dcdc69e1a2b24f8616", "L-fbba0e0db25f6b481eaa"):
        assert by[lid]["after"]["state"] == "NOT_APPLICABLE_WITH_EVIDENCE"
    assert "L-079bc7669b2c68d5d11b" not in by       # W13 / W25 stay held: B7-07 / B7-08 not in the candidate


def test_inputs_reproduce_t481_hand_figures():
    d = A.load_inputs(I.build("pin"))
    assert [w["sill_m"] for r in d["_releases"] for w in r["_windows"]] == [0.699, 0.699]
    assert [r["_released"] for r in d["_releases"]] == [pytest.approx(3.909839)]
    assert [w["sill_m"] for r in d["_closes"] for w in r["_windows"]] == [0.0, 0.0]
    m = d["_walks"][0]["_m"]
    assert (m["gross"], m["net"], m["deducted"]) == (pytest.approx(6.9), pytest.approx(5.1), pytest.approx(1.8))
