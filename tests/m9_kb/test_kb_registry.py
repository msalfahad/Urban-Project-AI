"""Phase 2B-1 WP-1: the engineering knowledge registry (knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json) - every
approved door, wet-area, skirting and elevator rule is a machine-readable record traceable to its authority, linked
to the code that applies it and the test that proves it; the rule store rules/ is untouched."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import knowledge as K          # noqa: E402

REG = K.registry()
IDS = {r["rule_id"]: r for r in REG["rules"]}
IDENTITY = re.compile("YEARS" + " 2013|7757-[A-Z]|(?i:als[ey]?n[ya]?an)|(?i:" + "qor" + "tuba|al-?rash" + "ed|adai"
                      + "liya)")


def test_every_record_is_complete_and_valid():
    assert K.validate(REG, links=False) == []


def test_every_code_and_test_link_exists():
    """a rule that names a function or a test that does not exist is not traceable."""
    assert K.validate(REG, links=True) == []


def test_the_required_rule_families_are_present_and_approved():
    need = {"UP-DOOR-CLS-001", "UP-DOOR-CLS-002", "UP-DOOR-CLS-003", "UP-DOOR-CLS-004", "UP-DOOR-CLS-005",
            "UP-DOOR-OPEN-002", "UP-DOOR-HGT-001", "UP-DOOR-AREA-001", "UP-ELEV-SCHED-001", "UP-WET-001",
            "UP-FIN-WALL-001", "UP-FIN-PAINT-001", "UP-SKIRT-001", "UP-THR-001", "UP-SPACE-001"}
    assert need <= set(IDS)
    for i in need:
        assert IDS[i]["status"] == "OWNER_APPROVED" and IDS[i]["authority"]["source"], i
        assert IDS[i]["tests"] and IDS[i]["code"], i


def test_the_superseded_dimension_reading_points_to_the_owner_correction():
    old, new = IDS["UP-DOOR-MIN-001"], IDS["UP-DOOR-OPEN-002"]
    assert old["status"] == "DEPRECATED" and old["superseded_by"] == "UP-DOOR-OPEN-002"
    assert "UP-DOOR-MIN-001" in new["supersedes"]
    assert "owner correction" in new["authority"]["source"].lower()


def test_the_owner_correction_values_live_in_data_not_code():
    t = IDS["UP-DOOR-OPEN-002"]["logic"]["table"]
    assert t == {"INTERNAL_PVC": {"required_nominal_door_m": 1.00, "required_wall_opening_m": 1.10},
                 "BATHROOM_PVC": {"required_nominal_door_m": 0.90, "required_wall_opening_m": 1.00},
                 "EXTERNAL_ALUMINIUM": {"required_nominal_door_m": 1.00, "required_wall_opening_m": 1.10}}
    assert K.door_standard("MAIN_ENTRANCE") is None and K.door_standard("ELEVATOR") is None
    for ex in IDS["UP-DOOR-OPEN-002"]["examples"]:
        s = K.door_standard(ex["category"])
        req = max(ex["cad_m"], s["required_wall_opening_m"])
        assert abs(req - ex["required_wall_opening_m"]) < 1e-9 and abs(req - ex["cad_m"] - ex["enlargement_m"]) < 1e-9


def test_precedence_puts_drawing_evidence_above_owner_rules():
    assert K.precedence_rank("APPROVED_DRAWING") < K.precedence_rank("APPROVED_SPECIFICATION") < \
        K.precedence_rank("VERIFIED_GEOMETRY") < K.precedence_rank("PROJECT_DECISION") < \
        K.precedence_rank("OWNER_RULE") < K.precedence_rank("ASSUMPTION") < K.precedence_rank("UNRESOLVED")
    assert IDS["UP-KB-PREC-001"]["logic"]["physical_fact_hierarchy"][0].startswith("1 approved drawing")


def test_project_decisions_are_never_general():
    ps = [r for r in REG["rules"] if r["status"] == "PROJECT_SPECIFIC"]
    assert ps and all(r["kind"] == "PROJECT_DECISION" and "project" in r["scope"].lower() for r in ps)


def test_conflicts_name_a_resolution_and_open_ones_name_a_question():
    for c in REG["conflicts"]:
        assert c["resolution"]
        if c["state"] in ("OPEN", "CONFLICTED"):
            assert re.search(r"OQ-\d\d", c["resolution"]), c["id"]


def test_the_wet_area_list_is_the_owner_list():
    assert set(K.wet_codes()) == {"BATHROOM", "KITCHEN", "PANTRY", "IRONING", "LAUNDRY"}
    assert K.confirm_codes() == ("LAUNDRY",)


def test_the_source_index_is_current_and_carries_no_identity():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools/kb_index.py"), "--check"], capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stdout
    for p in (ROOT / "knowledge").glob("*.json"):
        hit = IDENTITY.search(p.read_text(encoding="utf-8"))
        assert hit is None, (p.name, hit.group(0))


def test_the_rule_store_gains_no_file():
    """rules/ is read by V1 .. V2.2 (its digest is in their RUN_RULES); the registry lives outside it."""
    manifest = json.loads((ROOT / "rules/RULES_MANIFEST.json").read_text(encoding="utf-8"))
    on_disk = {p.relative_to(ROOT / "rules").as_posix() for p in (ROOT / "rules").rglob("*.json")
               if p.name != "RULES_MANIFEST.json"}
    assert on_disk == set(manifest["files"])


def test_every_line_reference_names_the_registry_and_its_digest():
    r = K.ref("UP-WET-001")
    assert r["rule_set"] == K.RULE_SET and r["rule_set_digest"] == K.digest() and r["status"] == "OWNER_APPROVED"


def test_the_registry_is_the_builder_output():
    """the committed registry is exactly what tools/kb_build.py writes (no hand edit drifts from its builder)."""
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools/kb_build.py"), "--check"], capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stdout
