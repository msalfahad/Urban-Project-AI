"""T-478: rules/coverage/BOQ_FAMILY_MASTER_1.40.0.json = 1.38.0 + the pending ARCH_TAKEOFF_V3.0.45 package + the B10-01
blinding family text; no owner, capability or candidate state changes."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3045 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.38.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.40.0.json"


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_blinding_family_and_pending_entry_change(docs):
    old, new = docs
    assert new["version"] == "1.40.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert [c for c in nb if nb[c] != ob[c]] == ["B10-01"]
    for k in ("candidate", "in_v3_0_candidate", "capability", "item_codes"):
        assert nb["B10-01"][k] == ob["B10-01"][k]
    assert A.METHOD in nb["B10-01"]["opt_in_readers"] and "HELD BLANK" in nb["B10-01"]["missing"]
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-478", A.METHOD, "engine/source/arch_v3045.py")
    assert "merge_commit" not in p
    for k in ("candidate_state_counts", "in_v3_0_candidate_counts", "capability_counts"):
        assert new[k] == old[k]


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    assert any("arch_v3045" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_family_naming_the_pending_package_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B10-01")
    b["candidate"]["packages"] = list(b["candidate"]["packages"]) + ["T-478"]
    assert any("pending package T-478" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
