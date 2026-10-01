"""R8.13 §32: the V4 freeze record - the live engine is the frozen V4, the frozen tests are unchanged, the
recommendation was committed with the freeze and no V4 Qortuba output existed before it."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine.source import topology_closures as TC, wall_bands as WB

ROOT = Path(__file__).resolve().parents[2]
FZ = json.loads((ROOT / "tests/r8_13/registers/R8_13_V4_FREEZE.json").read_text())


def sha(f):
    return hashlib.sha256((ROOT / f).read_bytes()).hexdigest()


def test_the_live_engine_is_the_frozen_v4():
    assert (WB.POLICY_ID, WB.policy_record()["digest"]) == (FZ["wall_band_policy"]["id"], FZ["wall_band_policy"]["digest"])
    assert (TC.POLICY_ID, TC.policy_record()["digest"]) == (FZ["closure_policy"]["id"], FZ["closure_policy"]["digest"])
    assert FZ["closure_policy"]["changed"] is False


def test_the_frozen_tests_and_the_recommendation_are_unchanged():
    for f, h in FZ["synthetic_test_sha256"].items():
        assert sha(f) == h, f"frozen test edited after the V4 freeze: {f}"
    rec = FZ["recommendation_written_first"]
    assert sha(rec["file"]) == rec["sha256"] and rec["committed_in"] == FZ["frozen_commit"]


def test_no_v4_qortuba_output_and_no_floor_fact_before_the_freeze():
    q = FZ["qortuba_before_freeze"]
    assert q["new_revision_v4_runs"] == 0 and q["v4_qortuba_outputs_inspected"] == 0
    assert FZ["floor_fact_available_to_v4"] is False and FZ["timestamp_metadata"]["in_digest"] is False
    assert FZ["v4_synthetic_test_count"] == len(FZ["v4_synthetic_tests"]) >= 20


def test_only_policy_id_lines_superseded_in_earlier_frozen_tests():
    assert set(FZ["superseded_frozen_tests"]) == {"tests/r8_12/test_r8_12_fragment_bands.py",
                                                  "tests/r8_11/test_r8_11_amendment_a1.py"}
    assert all(v["change"].startswith("ONE line: the policy-id assertion") for v in FZ["superseded_frozen_tests"].values())
