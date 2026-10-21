"""R8.19: the freeze record (exposed object finish, reveal physicality, BOQ report layer, Qortuba method v3) and the
unchanged R8.18 / V4 policies."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine.source import boq_report as BR, exposed_finish as EF, reveal_finish as RF, reveal_physicality as RP
from engine.source import wall_contact_path as WC, wall_faces as V1, wall_faces_v2 as WF, wall_height as WH
from engine.source import waterproofing as WP

ROOT = Path(__file__).resolve().parents[2]
FZ = json.loads((ROOT / "tests/r8_19/registers/R8_19_FREEZE.json").read_text())


def sha(f):
    return hashlib.sha256((ROOT / f).read_bytes()).hexdigest()


def test_live_policies_are_the_frozen_ones_and_r8_18_v4_are_unchanged():
    p = FZ["policies"]
    for mod, key in ((EF, "exposed_finish"), (RP, "reveal_physicality"), (BR, "boq_report")):
        assert [mod.POLICY_ID, mod.policy_record()["digest"]] == p[key]
    u = FZ["unchanged"]
    for mod, key in ((V1, "wall_face_v1"), (WF, "wall_face_v2"), (WH, "wall_height"), (RF, "reveal_finish"),
                     (WP, "waterproofing")):
        assert u[key] == [mod.POLICY_ID, mod.policy_record()["digest"]]
    assert u["wall_contact_path_v4"] == [WC.POLICY_ID_V4, WC.policy_record_v4()["digest"]]
    assert sha("tests/r8_18/registers/R8_18_FREEZE.json") == u["r8_18_freeze_sha256"]
    assert sha("research/external_engine_lab/r8_18_blind.py") == u["r8_18_blind_script_sha256"]


def test_frozen_tests_engines_blind_script_and_recommendation_unchanged():
    for f, h in {**FZ["synthetic_test_sha256"], **FZ["engine_file_sha256"]}.items():
        assert sha(f) == h, f"edited after the R8.19 freeze: {f}"
    assert sha("research/external_engine_lab/r8_19_blind.py") == FZ["blind_script_sha256"]
    rec = FZ["recommendation_written_first"]
    assert sha(rec["file"]) == rec["sha256"]


def test_the_method_requires_exposure_and_owner_authority_and_keeps_rows_separate():
    m = FZ["qortuba_wall_face_method"]
    r = m["object_face_rules"]
    assert "PHYSICAL_EXPOSURE" in r[EF.COLUMN_FACE]["requires"]
    assert {"PHYSICAL_EXPOSURE", "OWNER_PHYSICAL_AUTHORITY"} <= set(r[EF.OBSTACLE_FACE]["requires"])
    assert r[EF.OBSTACLE_FACE]["room_classes"] == ["DRY_INTERNAL_ROOM"]
    assert set(m["rows"]) == {"DRY_WALL_PLASTER", "DRY_WALL_PAINT", "WET_SERVICE_WALL_TILE", "WET_WALL_TILE_PREP",
                              "WET_SERVICE_REVEAL_PLASTER"}
    assert FZ["qortuba_before_freeze"]["r8_19_runs_on_qortuba"] == 0 and FZ["synthetic_test_count"] == 29
