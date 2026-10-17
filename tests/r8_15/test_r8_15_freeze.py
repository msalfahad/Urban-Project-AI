"""R8.15: the skirting freeze record (WALL_CONTACT_PATH_POLICY_V2 + the frozen Qortuba method)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine.source import topology_closures as TC, wall_bands as WB, wall_contact_path as WC

ROOT = Path(__file__).resolve().parents[2]
FZ = json.loads((ROOT / "tests/r8_15/registers/R8_15_SKIRTING_FREEZE.json").read_text())


def sha(f):
    return hashlib.sha256((ROOT / f).read_bytes()).hexdigest()


def test_the_live_path_policy_is_the_frozen_v2_and_topology_policies_are_unchanged():
    assert (WC.POLICY_ID_V2, WC.policy_record_v2()["digest"]) == (FZ["wall_contact_path_policy"]["id"],
                                                                   FZ["wall_contact_path_policy"]["digest"])
    assert WB.policy_record()["digest"] == FZ["wall_band_policy_unchanged"]["digest"] and WB.POLICY_ID == \
        "WALL_BAND_POLICY_V5"
    assert TC.policy_record()["digest"] == FZ["closure_policy_unchanged"]["digest"]


def test_frozen_tests_and_recommendation_unchanged():
    for f, h in FZ["synthetic_test_sha256"].items():
        assert sha(f) == h, f"frozen test edited after the skirting freeze: {f}"
    rec = FZ["recommendation_written_first"]
    assert sha(rec["file"]) == rec["sha256"]


def test_the_frozen_method_takes_its_parameters_from_the_rule_store_and_no_qortuba_total_came_first():
    m = FZ["qortuba_method"]
    assert m["parameters"]["window_treatment"] == WC.DEDUCT_WINDOWS and m["authority"]["window_treatment"].startswith("QP-09")
    assert m["parameters"]["jamb_return"] == WC.NO_RETURN and "counterfactual" in m["authority"]["jamb_return"]
    assert FZ["qortuba_before_freeze"]["v2_skirting_measurements_on_qortuba"] == 0
    assert FZ["timestamp_metadata"]["in_digest"] is False
