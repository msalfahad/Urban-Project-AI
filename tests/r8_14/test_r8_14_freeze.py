"""R8.14 §22: the V5 freeze record."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine.source import topology_closures as TC, wall_bands as WB

ROOT = Path(__file__).resolve().parents[2]
FZ = json.loads((ROOT / "tests/r8_14/registers/R8_14_V5_FREEZE.json").read_text())


def sha(f):
    return hashlib.sha256((ROOT / f).read_bytes()).hexdigest()


def test_the_live_engine_is_the_frozen_v5_and_the_closure_policy_is_unchanged():
    assert (WB.POLICY_ID, WB.policy_record()["digest"]) == (FZ["wall_band_policy"]["id"], FZ["wall_band_policy"]["digest"])
    assert (TC.POLICY_ID, TC.policy_record()["digest"]) == (FZ["closure_policy"]["id"], FZ["closure_policy"]["digest"])
    assert FZ["supersedes"]["wall_band_policy"]["id"] == "WALL_BAND_POLICY_V4"


def test_frozen_tests_and_recommendation_unchanged():
    for f, h in FZ["synthetic_test_sha256"].items():
        assert sha(f) == h, f"frozen test edited after the V5 freeze: {f}"
    rec = FZ["recommendation_written_first"]
    assert sha(rec["file"]) == rec["sha256"] and rec["committed_in"] == FZ["frozen_commit"]


def test_no_v5_qortuba_output_and_no_owner_fact_before_the_freeze():
    q = FZ["qortuba_before_freeze"]
    assert q["new_revision_v5_runs"] == 0 and q["v5_qortuba_outputs_inspected"] == 0
    assert FZ["owner_facts_available_to_v5"] is False and FZ["timestamp_metadata"]["in_digest"] is False
    assert all(v["change"].startswith("policy-version assertion only") for v in FZ["superseded_frozen_tests"].values())
