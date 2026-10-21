"""R8.18: the freeze record (wall-face V2, wall-height authority, reveal finish, waterproofing, Qortuba method v2)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine.source import reveal_finish as RF, wall_contact_path as WC, wall_faces as V1, wall_faces_v2 as WF
from engine.source import wall_height as WH, waterproofing as WP

ROOT = Path(__file__).resolve().parents[2]
FZ = json.loads((ROOT / "tests/r8_18/registers/R8_18_FREEZE.json").read_text())


def sha(f):
    return hashlib.sha256((ROOT / f).read_bytes()).hexdigest()


def test_live_policies_are_the_frozen_ones_and_v1_v4_are_unchanged():
    p = FZ["policies"]
    for mod, key in ((WF, "wall_face_v2"), (WH, "wall_height"), (RF, "reveal_finish"), (WP, "waterproofing")):
        assert [mod.POLICY_ID, mod.policy_record()["digest"]] == p[key]
    u = FZ["unchanged"]
    assert u["wall_face_v1"] == [V1.POLICY_ID, V1.policy_record()["digest"]]
    assert u["wall_contact_path_v4"] == [WC.POLICY_ID_V4, WC.policy_record_v4()["digest"]]


def test_frozen_tests_blind_script_and_recommendation_unchanged():
    for f, h in FZ["synthetic_test_sha256"].items():
        assert sha(f) == h, f"frozen test edited after the R8.18 freeze: {f}"
    assert sha("research/external_engine_lab/r8_18_blind.py") == FZ["blind_script_sha256"]
    rec = FZ["recommendation_written_first"]
    assert sha(rec["file"]) == rec["sha256"]


def test_the_method_scopes_heights_per_trade_and_never_globalises():
    m = FZ["qortuba_wall_face_method"]
    hs = m["height_scopes"]
    assert [c["value_m"] for c in hs["DRY_INTERNAL_ROOM|PLASTER"] if c["kind"] == "OWNER_PROJECT_FACT"] == [3.15]
    assert [c["value_m"] for c in hs["WET_SERVICE_ROOM|WALL_TILE"]] == [3.2]
    assert set(m["column_faces"].values()) == {"UNRESOLVED"} and set(m["obstacle_faces"].values()) == {"UNRESOLVED"}
    assert FZ["qortuba_before_freeze"]["wall_face_v2_runs_on_qortuba"] == 0
