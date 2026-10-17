"""R8.16: the freeze record (DOOR_OPENING_CLOSURE_POLICY_V2 + WALL_CONTACT_PATH_POLICY_V3 + the Qortuba method v2)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine.source import topology as T, topology_closures as TC, wall_bands as WB, wall_contact_path as WC

ROOT = Path(__file__).resolve().parents[2]
FZ = json.loads((ROOT / "tests/r8_16/registers/R8_16_FREEZE.json").read_text())


def sha(f):
    return hashlib.sha256((ROOT / f).read_bytes()).hexdigest()


def test_the_live_policies_are_the_frozen_ones_and_v5_closure_v1_and_path_v2_are_unchanged():
    assert (T.DOOR_CLOSURE_POLICY_ID, T.door_closure_policy_record()["digest"]) == tuple(FZ["door_closure_policy"].values())
    assert (WC.POLICY_ID_V3, WC.policy_record_v3()["digest"]) == tuple(FZ["wall_contact_path_policy"].values())
    u = FZ["unchanged"]
    assert u["wall_band_policy"] == [WB.POLICY_ID, WB.policy_record()["digest"]]
    assert u["topology_closure_policy"] == [TC.POLICY_ID, TC.policy_record()["digest"]]
    assert u["wall_contact_path_policy_v2"] == [WC.POLICY_ID_V2, WC.policy_record_v2()["digest"]]


def test_frozen_tests_blind_script_and_recommendation_unchanged():
    for f, h in FZ["synthetic_test_sha256"].items():
        assert sha(f) == h, f"frozen test edited after the R8.16 freeze: {f}"
    assert sha("research/external_engine_lab/r8_16_blind.py") == FZ["blind_script_sha256"]
    rec = FZ["recommendation_written_first"]
    assert sha(rec["file"]) == rec["sha256"]


def test_no_qortuba_v2_v3_output_before_the_freeze_and_the_method_has_authority():
    q = FZ["qortuba_before_freeze"]
    assert q["closure_v2_runs_on_qortuba"] == 0 and q["skirting_v3_measurements_on_qortuba"] == 0
    m = FZ["qortuba_method"]
    assert m["ref"] == "QORTUBA-NEW-SKIRTING-METHOD@v2" and m["authority"]["windows"].startswith("QORTUBA-NEW-SKIRTING-WINDOW")
    assert FZ["timestamp_metadata"]["in_digest"] is False
