"""R8.19 lab: write the freeze record (policies, unchanged R8.18 / V4 policies, file hashes, the synthetic test list,
QORTUBA-NEW-WALL-FACE-METHOD@v3) BEFORE the blind Qortuba run. Run once on the committed code; never rewritten.

    python3 research/external_engine_lab/r8_19_freeze.py <code_commit>
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import boq_report as BR, exposed_finish as EF, reveal_finish as RF, reveal_physicality as RP  # noqa
from engine.source import wall_contact_path as WC, wall_faces as V1, wall_faces_v2 as WF, wall_height as WH    # noqa
from engine.source import waterproofing as WP                                                              # noqa: E402

OUT = ROOT / "tests/r8_19/registers/R8_19_FREEZE.json"
TESTS = ["tests/r8_19/test_r8_19_exposed_finish.py", "tests/r8_19/test_r8_19_reveal_physicality.py",
         "tests/r8_19/test_r8_19_boq_report.py", "tests/r8_19/test_r8_19_freeze.py"]
ENGINE = ["engine/source/exposed_finish.py", "engine/source/reveal_physicality.py", "engine/source/boq_report.py"]
FACTS = ["data/registry/OWNER_METHOD_FACTS.json", "data/registry/URBAN_OWNER_METHOD_RULES.json",
         "data/registry/OWNER_PHYSICAL_FACTS.json"]
WET = ["WET_SERVICE_ROOM", "SERVICE_ROOM"]
DRY = "DRY_INTERNAL_ROOM"


def sha(f):
    return hashlib.sha256((ROOT / f).read_bytes()).hexdigest()


def method():
    fz18 = json.loads((ROOT / "tests/r8_18/registers/R8_18_FREEZE.json").read_text())
    v2 = fz18["qortuba_wall_face_method"]
    m = {"method_id": "QORTUBA-NEW-WALL-FACE-METHOD", "version": 3, "supersedes": v2["ref"],
         "scope": v2["scope"], "surface_model": f"{v2['ref']} via the frozen R8.18 run (heights, wall-plane surfaces, "
                                                "reveal geometry / ownership / finish, waterproofing) - unchanged",
         "object_face_rules": {
             EF.COLUMN_FACE: {"rule_id": "URBAN-EXPOSED-COLUMN-FINISH-METHOD@v1", "face_class": EF.COLUMN_FACE,
                              "requires": ["PHYSICAL_EXPOSURE"], "room_classes": [DRY] + WET,
                              "follows": "ROOM_WALL_TRADES"},
             EF.OBSTACLE_FACE: {"rule_id": "URBAN-EXPOSED-INTERIOR-DUCT-FINISH-METHOD@v1",
                                "face_class": EF.OBSTACLE_FACE,
                                "requires": ["PHYSICAL_EXPOSURE", "OWNER_PHYSICAL_AUTHORITY"], "room_classes": [DRY],
                                "follows": "ROOM_WALL_TRADES",
                                "project_statement": "QORTUBA-NEW-BED-ROOM-DUCT-FINISH-OWNER-001@v1"}},
         "object_identity": {EF.COLUMN_FACE: "every SEGMENT part whose geometry role is STRUCTURAL_OBSTACLE (all "
                                             "segments of each column entity, exposed or not)",
                             EF.OBSTACLE_FACE: "every SEGMENT part of an entity with an obstacle state "
                                               "(OWNER_PHYSICAL_OBSTACLE = owner physical authority)"},
         "exposure": "certified site-boundary spans of the class, attributed to the object's own segments",
         "reveal_physicality": {"policy": RP.POLICY_ID, "replaces": "the R8.18 blind / rebuild reveal-face check",
                                "evidence": "admitted wall / structural parts (roles TOPOLOGY_BOUNDARY / "
                                            "STRUCTURAL_OBSTACLE) or an ESTABLISHED band OPENING_JAMB end of the same "
                                            "opening"},
         "rows": {"DRY_WALL_PLASTER": {"trade": "PLASTER", "classes": [DRY]},
                  "DRY_WALL_PAINT": {"trade": "PAINT", "classes": [DRY]},
                  "WET_SERVICE_WALL_TILE": {"trade": "WALL_TILE", "classes": WET},
                  "WET_WALL_TILE_PREP": {"trade": "WET_WALL_TILE_PREP", "classes": WET},
                  "WET_SERVICE_REVEAL_PLASTER": {"trade": "PLASTER", "classes": WET, "reveals_only": True}},
         "row_states": {"COMPUTED_SHADOW_COMPLETE": "every contributor resolved: COMPLETE = AUTHORISED_SUBTOTAL",
                        "AUTHORISED_SUBTOTAL": "an unresolved contributor exists: COMPLETE null (BLOCKED_PARTIAL)",
                        "BLOCKED": "a room's surface model is not COMPUTED", "FINAL": "never in this round"},
         "never": ["the R8.18 diagnostic areas added to a total", "a finish on a hidden / embedded / internal face",
                   "an obstacle finish without owner physical authority", "new skirting", "paint in a wet room",
                   "a fixture line as a reveal surface", "plaster as proof of a surface",
                   "PLASTER == PAINT asserted without surface-set identity"]}
    m["ref"] = "QORTUBA-NEW-WALL-FACE-METHOD@v3"
    m["digest"] = hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest()
    return m


def main(commit):
    full = subprocess.run(["git", "rev-parse", commit], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    rec = {"SCHEMA": "URBAN_R8_19_FREEZE_V1",
           "recommendation_written_first": {"file": "research/external_engine_lab/r8_19_recommendation.json",
                                            "sha256": sha("research/external_engine_lab/r8_19_recommendation.json"),
                                            "commit": "6910087"},
           "frozen_commit": full,
           "policies": {"exposed_finish": [EF.POLICY_ID, EF.policy_record()["digest"]],
                        "reveal_physicality": [RP.POLICY_ID, RP.policy_record()["digest"]],
                        "boq_report": [BR.POLICY_ID, BR.policy_record()["digest"]]},
           "unchanged": {"wall_face_v1": [V1.POLICY_ID, V1.policy_record()["digest"]],
                         "wall_face_v2": [WF.POLICY_ID, WF.policy_record()["digest"]],
                         "wall_height": [WH.POLICY_ID, WH.policy_record()["digest"]],
                         "reveal_finish": [RF.POLICY_ID, RF.policy_record()["digest"]],
                         "waterproofing": [WP.POLICY_ID, WP.policy_record()["digest"]],
                         "wall_contact_path_v4": [WC.POLICY_ID_V4, WC.policy_record_v4()["digest"]],
                         "r8_18_freeze_sha256": sha("tests/r8_18/registers/R8_18_FREEZE.json"),
                         "r8_18_blind_script_sha256": sha("research/external_engine_lab/r8_18_blind.py")},
           "engine_file_sha256": {f: sha(f) for f in ENGINE}, "facts_sha256": {f: sha(f) for f in FACTS},
           "blind_script_sha256": sha("research/external_engine_lab/r8_19_blind.py"),
           "synthetic_test_sha256": {f: sha(f) for f in TESTS[:3]},
           "qortuba_wall_face_method": method(),
           "qortuba_before_freeze": {"r8_19_runs_on_qortuba": 0,
                                     "inspection_only": "column / duct span sources, part roles, the sliding-door "
                                                        "south jamb parts and band ends (recorded in the "
                                                        "recommendation) - no trade quantity computed"},
           "order": ["recommendation (6910087)", "engines + rules + facts + tests + blind script (frozen commit)",
                     "THIS freeze", "commit", "THEN the blind Qortuba run", "THEN rebuild / registers / BOQ"],
           "rule": "no engine, test, rule, fact or blind-script change after this record without a disclosed amendment",
           "amendments": []}
    import importlib.util
    tests = []
    for f in TESTS[:3]:
        spec = importlib.util.spec_from_file_location("m", ROOT / f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        tests += [f"{Path(f).stem}::{n}" for n in dir(mod) if n.startswith("test_")]
    rec["synthetic_tests"], rec["synthetic_test_count"] = tests, len(tests)
    OUT.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    print(OUT, rec["synthetic_test_count"], rec["qortuba_wall_face_method"]["digest"][:12])


if __name__ == "__main__":
    main(sys.argv[1])
