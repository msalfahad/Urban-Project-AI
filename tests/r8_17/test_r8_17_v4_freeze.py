"""R8.17: the V4 freeze record (WALL_CONTACT_PATH_POLICY_V4 + QORTUBA-NEW-SKIRTING-METHOD@v3)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine.source import opening_facts as OPF, topology as T, topology_closures as TC, wall_bands as WB
from engine.source import wall_contact_path as WC

ROOT = Path(__file__).resolve().parents[2]
FZ = json.loads((ROOT / "tests/r8_17/registers/R8_17_V4_FREEZE.json").read_text())


def sha(f):
    return hashlib.sha256((ROOT / f).read_bytes()).hexdigest()


def test_the_live_v4_is_the_frozen_one_and_everything_below_is_unchanged():
    assert (WC.POLICY_ID_V4, WC.policy_record_v4()["digest"]) == tuple(FZ["wall_contact_path_policy"].values())
    assert (OPF.POLICY_ID, OPF.policy_record()["digest"]) == tuple(FZ["opening_physical_class_policy"].values())
    u = FZ["unchanged"]
    assert u["wall_contact_path_policy_v3"] == [WC.POLICY_ID_V3, WC.policy_record_v3()["digest"]]
    assert u["door_opening_closure_policy"] == [T.DOOR_CLOSURE_POLICY_ID, T.door_closure_policy_record()["digest"]]
    assert u["wall_band_policy"] == [WB.POLICY_ID, WB.policy_record()["digest"]]
    assert u["topology_closure_policy"] == [TC.POLICY_ID, TC.policy_record()["digest"]]


def test_frozen_tests_blind_script_and_recommendation_unchanged():
    for f, h in FZ["synthetic_test_sha256"].items():
        assert sha(f) == h, f"frozen test edited after the R8.17 V4 freeze: {f}"
    assert sha("research/external_engine_lab/r8_17_blind.py") == FZ["blind_script_sha256"]
    rec = FZ["recommendation_written_first"]
    assert sha(rec["file"]) == rec["sha256"]


def test_no_qortuba_v4_output_before_the_freeze_and_the_method_has_authority():
    assert FZ["qortuba_before_freeze"]["skirting_v4_measurements_on_qortuba"] == 0
    m = FZ["qortuba_method"]
    assert m["ref"] == "QORTUBA-NEW-SKIRTING-METHOD@v3" and m["authority"]["path_policy"] == WC.POLICY_ID_V4
    assert m["authority"]["sliding_glazed_door"].startswith("QORTUBA-NEW-HALL-PAINTRY-SLIDING-GLASS-DOOR")
