"""T-231: BOQ_FAMILY_MASTER 1.3.0 (1.2.0 + the pending ARCH_TAKEOFF_V3.0.8 package) and rule r3 of
tools/family_master_candidate.py (pending packages; a superseded registry version is not the registry of record).

Normal: 1.3.0 equals its builder, carries every 1.2.0 family unchanged, checks clean on this head; 1.2.0 checks clean
because 1.3.0 accounts for the newer module. Adverse, on a synthetic tree (no repository file): a newer candidate
module nobody declares (stale), a pending package naming another module or a version not above the candidate, carrying a
verdict, also merged, or named by a family state, and a newer registry that does not account for the module."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t231"))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.2.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.3.0.json"


@pytest.fixture(scope="module")
def docs():
    return (json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8")))


# ------------------------------------------------------------------------------------------------ the merged files
def test_1_3_0_equals_its_builder_and_copies_1_2_0(docs):
    import build_master_1_3_0 as B
    old, new = docs
    tc = new["pending_packages"][0]["task_commit"]
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(tc))
    assert new["version"] == "1.3.0" and old["version"] == "1.2.0"
    for k in old:
        if k not in ("version", "supersedes", "source"):
            assert new[k] == old[k], k                      # every family, count and released field unchanged
    assert set(new) - set(old) == {"pending_packages"}


def test_1_3_0_checks_clean_and_v308_is_pending_not_merged(docs):
    _, new = docs
    assert FMC.check(new, is_ancestor=FMC.git_is_ancestor) == []
    p = new["pending_packages"][0]
    assert (p["task"], p["method_version"], p["module"], p["status"]) == (
        "T-231", "ARCH_TAKEOFF_V3.0.8", "engine/source/arch_v308.py", "READY_FOR_GATE_B")
    assert "merge_commit" not in p and "verdict" not in p
    assert new["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.7"      # the candidate of record is unchanged
    assert all("T-231" not in (f["candidate"].get("packages") or []) for f in new["families"])


def test_superseded_1_2_0_is_accounted_for_by_1_3_0(docs):
    old, _ = docs
    # T-211: the newest version that accounts for arch_v308 is the newest registry on the tree carrying the T-231
    # entry (1.4.0 copies it); 1.3.0 itself must still declare it (asserted on 1.3.0's own content)
    acc = FMC.newer_registry_modules(old, ROOT).get("engine/source/arch_v308.py")
    assert acc is not None and FMC._semver(acc) >= FMC._semver("1.3.0")
    assert any(p["module"] == "engine/source/arch_v308.py" for p in docs[1]["pending_packages"])
    assert FMC.check(old, is_ancestor=FMC.git_is_ancestor) == []
    assert FMC.DEFAULT == NEW


# ------------------------------------------------------------------------------------------------ synthetic tree
SHA = "a" * 40


def tree(tmp_path, modules=(7, 8)):
    for n in modules:
        f = tmp_path / f"engine/source/arch_v30{n}.py"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("X = 1\n", encoding="utf-8")
    (tmp_path / "tests/tx").mkdir(parents=True, exist_ok=True)
    (tmp_path / "rules/coverage").mkdir(parents=True, exist_ok=True)
    return tmp_path


def registry(version="9.0.0", pending=None):
    fam = {"code": "F-01", "in_v3_0_candidate": "no",
           "candidate": {"state": "NOT_IN_CANDIDATE", "method_version": "ARCH_TAKEOFF_V3.0.7", "as_of_package": "T-100",
                         "packages": []}}
    d = {"version": version, "candidate_states": list(FMC.STATES),
         "candidate_state_definitions": {s: "x" for s in FMC.STATES},
         "candidate": {"method_version": "ARCH_TAKEOFF_V3.0.7", "as_of_package": "T-100"},
         "candidate_packages": [{"task": "T-100", "method_version": "ARCH_TAKEOFF_V3.0.7",
                                 "module": "engine/source/arch_v307.py", "merge_commit": SHA,
                                 "verdict": "MERGED (Verifier 2026-10-23 10:00 UTC)", "integrates": ["T-001"],
                                 "tests": ["tests/tx"]}],
         "families": [fam],
         "candidate_state_counts": {"INTEGRATED_IN_CANDIDATE_AND_TESTED": 0, "HELD_IN_CANDIDATE": 0,
                                    "IN_CANDIDATE_BASE_LINES": 0, "NOT_IN_CANDIDATE": 1},
         "in_v3_0_candidate_counts": {"yes": 0, "no": 1}}
    if pending is not None:
        d["pending_packages"] = pending
    return d


def pend(**kw):
    p = {"task": "T-200", "method_version": "ARCH_TAKEOFF_V3.0.8", "module": "engine/source/arch_v308.py",
         "task_commit": "b" * 40, "status": "READY_FOR_GATE_B", "integrates": ["T-002"], "tests": ["tests/tx"]}
    p.update(kw)
    return p


def test_synthetic_pending_declared_is_clean(tmp_path):
    root = tree(tmp_path)
    assert FMC.check(registry(pending=[pend()]), root=root) == []


def test_adverse_newer_module_nobody_declares_is_stale(tmp_path):
    root = tree(tmp_path)
    bad = FMC.check(registry(), root=root)
    assert any("arch_v308.py" in b and "stale" in b for b in bad), bad


@pytest.mark.parametrize("kw, words", [
    ({"module": "engine/source/arch_v307.py"}, "is not the module of ARCH_TAKEOFF_V3.0.8"),
    ({"method_version": "ARCH_TAKEOFF_V3.0.7", "module": "engine/source/arch_v307.py"}, "is not above the candidate"),
    ({"verdict": "MERGED (Verifier 2026-10-23 11:00 UTC)"}, "carries a verdict"),
    ({"status": "MERGED"}, "status must be READY_FOR_GATE_B"),
    ({"task_commit": "abc1234"}, "not a full 40-hex sha"),
    ({"tests": ["tests/none"]}, "does not exist"),
    ({"integrates": []}, "'integrates' must list"),
    ({"task": "T-100"}, "also a merged package"),
])
def test_adverse_pending_package_rules(tmp_path, kw, words):
    root = tree(tmp_path)
    bad = FMC.check(registry(pending=[pend(**kw)]), root=root)
    assert any(words in b for b in bad), bad


def test_adverse_module_of_another_version(tmp_path):
    root = tree(tmp_path, modules=(7, 8, 9))
    bad = FMC.check(registry(pending=[pend(module="engine/source/arch_v309.py")]), root=root)
    assert any("is not the module of ARCH_TAKEOFF_V3.0.8" in b for b in bad), bad
    assert any("arch_v308.py" in b and "stale" in b for b in bad), bad            # V3.0.8 itself is then undeclared


def test_adverse_family_naming_a_pending_package(tmp_path):
    root = tree(tmp_path)
    d = registry(pending=[pend()])
    d["families"][0]["candidate"]["packages"] = ["T-200"]
    bad = FMC.check(d, root=root)
    assert any("names the pending package T-200" in b for b in bad), bad


def test_adverse_task_commit_not_on_the_head(tmp_path):
    root = tree(tmp_path)
    bad = FMC.check(registry(pending=[pend()]), root=root, is_ancestor=lambda c: c != "b" * 40)
    assert any("task_commit bbbbbbbbbb is not on the checked head" in b for b in bad), bad


def test_superseded_version_accounted_only_by_a_newer_registry_that_names_the_module(tmp_path):
    root = tree(tmp_path)
    old = registry(version="9.0.0")
    newer = registry(version="9.1.0", pending=[pend()])
    (root / "rules/coverage/BOQ_FAMILY_MASTER_9.1.0.json").write_text(json.dumps(newer), encoding="utf-8")
    assert FMC.check(old, root=root) == []                      # 9.1.0 accounts for arch_v308
    other = copy.deepcopy(newer)
    other["pending_packages"] = []
    (root / "rules/coverage/BOQ_FAMILY_MASTER_9.1.0.json").write_text(json.dumps(other), encoding="utf-8")
    assert any("stale" in b for b in FMC.check(old, root=root))  # a newer version that does not name it: still stale
    lower = registry(version="8.9.0", pending=[pend()])
    (root / "rules/coverage/BOQ_FAMILY_MASTER_9.1.0.json").unlink()
    (root / "rules/coverage/BOQ_FAMILY_MASTER_8.9.0.json").write_text(json.dumps(lower), encoding="utf-8")
    assert any("stale" in b for b in FMC.check(old, root=root))  # an OLDER version never accounts for a newer module
