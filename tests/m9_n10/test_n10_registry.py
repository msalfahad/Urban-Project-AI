"""Phase N10 - knowledge registry 1.5.0 (tools/kb_build_1_5.py): the frozen 1.4.0 registry plus the N10 delta, read
only by ARCH_TAKEOFF_V2.9. Every new rule is REQUIRES_CONFIRMATION (the engine's reading of the owner program)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import knowledge as K                     # noqa: E402

NEW = {"UP-OPEN-CURVED-001", "UP-MAS-HEIGHT-001", "UP-FACADE-001", "UP-FW-001", "UP-EXC-001"}


def _reg(v):
    with K.using(v):
        return K.registry()


def test_registry_1_5_is_the_builder_output():
    p = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "kb_build_1_5.py"), "--check"],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def test_registry_1_5_validates_with_every_code_and_test_link():
    assert K.validate(_reg("1.5.0"), links=True) == []


def test_registry_1_5_is_1_4_plus_the_n10_delta_only():
    r14, r15 = _reg("1.4.0"), _reg("1.5.0")
    assert r15["base"] == {"version": "1.4.0", "sha256": hashlib.sha256(
        (ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.4.0.json").read_bytes()).hexdigest()}
    old = {r["rule_id"]: r for r in r14["rules"]}
    new = {r["rule_id"]: r for r in r15["rules"]}
    assert set(new) - set(old) == NEW
    assert all(new[k] == v for k, v in old.items())                     # no 1.4.0 rule changed
    assert all(new[k]["status"] == "REQUIRES_CONFIRMATION" for k in NEW)  # no interpretation promoted
    assert r15["owner_questions"][:len(r14["owner_questions"])] == r14["owner_questions"]


def test_v2_9_reads_1_5_and_v2_8_still_reads_1_4():
    sys.path.insert(0, str(ROOT / "tools"))
    import urban_boq_m9 as M
    assert M.V29_KNOWLEDGE == "1.5.0" and M.V28_KNOWLEDGE == "1.4.0"
    assert K.version() == "1.0.0"                                       # the default is unchanged
    json.dumps(_reg("1.5.0"))
