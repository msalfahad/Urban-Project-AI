"""Board task T-011 - knowledge registry 1.6.0 (tools/kb_build_1_6.py): the frozen 1.5.0 registry plus the owner's
answer to the door-minimum question (Q-04 / OQ-05). Only UP-DOOR-OPEN-002 and UP-DOOR-OPEN-003 change; 1.5.0 and every
method's registry stay as they were."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import knowledge as K                     # noqa: E402

AMENDED = {"UP-DOOR-OPEN-002", "UP-DOOR-OPEN-003"}


def _reg(v):
    with K.using(v):
        return K.registry()


def test_registry_1_6_is_the_builder_output():
    p = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "kb_build_1_6.py"), "--check"],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def test_registry_1_6_validates_with_every_code_and_test_link():
    assert K.validate(_reg("1.6.0"), links=True) == []


def test_registry_1_6_is_1_5_plus_the_door_answer_only():
    r15, r16 = _reg("1.5.0"), _reg("1.6.0")
    assert r16["base"] == {"version": "1.5.0", "sha256": hashlib.sha256(
        (ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.5.0.json").read_bytes()).hexdigest()}
    old = {r["rule_id"]: r for r in r15["rules"]}
    new = {r["rule_id"]: r for r in r16["rules"]}
    assert set(new) == set(old)
    assert {k for k in old if new[k] != old[k]} == AMENDED
    assert new["UP-DOOR-OPEN-002"]["status"] == "OWNER_APPROVED"
    assert new["UP-DOOR-OPEN-002"]["authority"]["source"].startswith("owner answer 2026-10-18 to Q-04")
    oq15 = {q["id"]: q for q in r15["owner_questions"]}
    oq16 = {q["id"]: q for q in r16["owner_questions"]}
    assert set(oq15) == set(oq16) and {k for k in oq15 if oq15[k] != oq16[k]} == {"OQ-05"}
    assert oq16["OQ-05"]["state"] == "ANSWERED"
    assert {k: v for k, v in oq16["OQ-05"].items() if k in oq15["OQ-05"]} == oq15["OQ-05"]   # the record is kept


def test_the_door_table_under_1_6():
    with K.using("1.6.0"):
        t = {c: K.door_standard(c) for c in ("INTERNAL_PVC", "BATHROOM_PVC", "EXTERNAL_ALUMINIUM", "MAIN_ENTRANCE")}
    assert t["INTERNAL_PVC"] == {"required_nominal_door_m": 1.0, "required_wall_opening_m": 1.1, "allowance_m": 0.1}
    assert t["BATHROOM_PVC"] == {"required_nominal_door_m": 0.9, "required_wall_opening_m": 1.0, "allowance_m": 0.1}
    assert t["EXTERNAL_ALUMINIUM"]["required_wall_opening_m"] == 1.1 and t["MAIN_ENTRANCE"] is None


def test_no_method_reads_1_6_and_the_default_is_unchanged():
    sys.path.insert(0, str(ROOT / "tools"))
    import urban_boq_m9 as M
    assert M.V29_KNOWLEDGE == "1.5.0" and M.V28_KNOWLEDGE == "1.4.0"
    assert K.version() == "1.0.0"
    with K.using("1.5.0"):                                          # V2.9's registry still holds OQ-05 open
        assert K.rule("UP-DOOR-OPEN-002")["status"] == "REQUIRES_CONFIRMATION"
