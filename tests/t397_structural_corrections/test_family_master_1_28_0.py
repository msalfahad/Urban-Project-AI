"""T-397: BOQ_FAMILY_MASTER 1.28.0 = 1.27.0 + the pending ARCH_TAKEOFF_V3.0.33 package (rule r3 of
tools/family_master_candidate.py); no new code, no family changes.

Normal: 1.28.0 equals its builder, copies every 1.27.0 field it does not name, checks clean on the head; every code the
V3.0.33 module writes is owned by a 1.28.0 family (STR.CONC.LIFT by B10-10). Adverse: the pending entry dropped (the
head's arch_v3033.py becomes unaccounted: stale), a pending entry carrying a merge commit, and a family naming the
pending package are each refused."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3033 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.27.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.28.0.json"
_spec = importlib.util.spec_from_file_location("b128", ROOT / "research/agents_t397/build_master_1_28_0.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)
NAMED = {"version", "supersedes", "source", "pending_packages", "item_code_scan"}


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_equals_builder(docs):
    old, new = docs
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(new["pending_packages"][-1]["task_commit"]))


def test_copies_every_other_field(docs):
    old, new = docs
    assert set(old) == set(new)
    for k in set(old) - NAMED:
        assert old[k] == new[k], k
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-397", A.METHOD, "engine/source/arch_v3033.py")


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_written_codes_owned(docs):
    owned = {c for f in docs[1]["families"] for c in f.get("item_codes") or ()}
    assert set(A.CONCRETE) <= owned
    assert "STR.CONC.LIFT" in next(f for f in docs[1]["families"] if f["code"] == "B10-10")["item_codes"]


def test_pending_dropped_is_stale(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    probs = FMC.check(bad, root=ROOT, is_ancestor=None)
    assert any("arch_v3033" in p for p in probs)


def test_pending_with_merge_commit_refused(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"][-1]["merge_commit"] = "0" * 40
    assert any("merge commit" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_family_naming_pending_refused(docs):
    bad = copy.deepcopy(docs[1])
    f = next(f for f in bad["families"] if f["code"] == "B10-10")
    f["candidate"]["packages"] = list(f["candidate"].get("packages") or []) + ["T-397"]
    assert any("pending package T-397" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
