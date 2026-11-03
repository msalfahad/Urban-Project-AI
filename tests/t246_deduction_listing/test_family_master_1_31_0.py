"""T-246: rules/coverage/BOQ_FAMILY_MASTER_1.31.0.json = 1.30.0 + the pending ARCH_TAKEOFF_V3.0.36 package; no family,
code, capability or candidate state changes (V3.0.36 only re-lists deductions)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest
import sys as _sys_t485  # noqa: E402
_sys_t485.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t485"))
import t485_accounting as _T485  # noqa: E402  (T-485: a newer registry may hold the entry promoted, rule r3)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3036 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.30.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.31.0.json"


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_the_pending_entry_is_new(docs):
    old, new = docs
    assert new["version"] == "1.31.0" and new["families"] == old["families"]
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-246", A.METHOD, "engine/source/arch_v3036.py")
    assert p["changes_families_by_item_code"] == [] and "merge_commit" not in p
    for k in ("capability_counts", "candidate_state_counts", "in_v3_0_candidate_counts"):
        assert new[k] == old[k]


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    probs = FMC.check(bad, root=ROOT, is_ancestor=None)
    acc = FMC.newer_registry_modules(docs[1], ROOT).get("engine/source/arch_v3036.py")
    if acc is None:
        assert any("arch_v3036" in p for p in probs)
    else:
        gov = json.loads((ROOT / f"rules/coverage/BOQ_FAMILY_MASTER_{acc}.json").read_text(encoding="utf-8"))
        assert _T485.accounted(docs[1]["pending_packages"][-1], gov)


def test_pending_with_merge_commit_refused(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"][-1]["merge_commit"] = "0" * 40
    assert any("merge commit" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
