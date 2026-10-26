"""T-255: BOQ_FAMILY_MASTER 1.14.0 = 1.13.0 + the pending ARCH_TAKEOFF_V3.0.19 package (rule r3 of
tools/family_master_candidate.py). Normal: 1.14.0 equals its builder, copies every 1.13.0 field (the T-231 .. T-266
pending entries included), checks clean on this head; 1.13.0 still checks clean because 1.14.0 accounts for
the newer module. Adverse: a 1.14.0 that drops the V3.0.19 entry leaves the module unaccounted (stale); a pending entry
that names a family is refused."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t255"))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.13.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.14.0.json"


@pytest.fixture(scope="module")
def docs():
    return (json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8")))


def test_1_14_0_equals_its_builder_and_copies_1_13_0(docs):
    import build_master_1_14_0 as B
    old, new = docs
    tc = new["pending_packages"][-1]["task_commit"]
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(tc))
    assert new["version"] == "1.14.0" and old["version"] == "1.13.0"
    for k in old:
        if k not in ("version", "supersedes", "source", "pending_packages"):
            assert new[k] == old[k], k
    assert new["pending_packages"][:-1] == old["pending_packages"]      # T-231 .. T-266 kept as they were
    assert set(new) == set(old)


def test_1_14_0_checks_clean_and_v3019_is_pending_not_merged(docs):
    _, new = docs
    assert FMC.check(new, is_ancestor=FMC.git_is_ancestor) == []
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"], p["status"]) == (
        "T-255", "ARCH_TAKEOFF_V3.0.19", "engine/source/arch_v3019.py", "READY_FOR_GATE_B")
    assert p["integrates"] == ["T-254", "T-232", "T-249", "T-250", "T-285", "T-292"] and p["changes_families_by_item_code"] == []
    assert "merge_commit" not in p and "verdict" not in p
    assert all("T-255" not in (f["candidate"].get("packages") or []) for f in new["families"])


def test_1_13_0_is_accounted_for_by_1_14_0(docs):
    old, _ = docs
    # the newest version that accounts for arch_v3019 is the newest registry on the tree carrying the T-255 entry (a
    # later version copies it); 1.14.0 itself must still declare it (asserted on 1.14.0's own content)
    acc = FMC.newer_registry_modules(old, ROOT).get("engine/source/arch_v3019.py")
    assert acc is not None and FMC._semver(acc) >= FMC._semver("1.14.0")
    assert any(p["module"] == "engine/source/arch_v3019.py" for p in docs[1]["pending_packages"])
    assert FMC.check(old, is_ancestor=FMC.git_is_ancestor) == []


def test_adverse_dropping_the_v3019_entry_is_stale(docs, monkeypatch):
    _, new = docs
    bad = copy.deepcopy(new)
    bad["pending_packages"] = bad["pending_packages"][:-1]
    # a newer registry on the tree copies the T-255 entry and so accounts for arch_v3019; the adverse
    # case is judged as on the head this file was written for (no newer registry version), where the drop must be stale
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    probs = FMC.check(bad, root=ROOT, is_ancestor=FMC.git_is_ancestor)
    assert probs and any("arch_v3019" in p for p in probs)


def test_adverse_a_family_naming_the_pending_package_is_refused(docs):
    _, new = docs
    bad = copy.deepcopy(new)
    bad["families"][0]["candidate"]["packages"] = list(bad["families"][0]["candidate"].get("packages") or []) + ["T-255"]
    assert any("T-255" in p for p in FMC.check(bad, root=ROOT, is_ancestor=FMC.git_is_ancestor))
