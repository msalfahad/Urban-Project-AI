"""T-419: rules/coverage/BOQ_FAMILY_MASTER_1.42.0.json = 1.41.0 + the pending ARCH_TAKEOFF_V3.0.46 package + the text of
the five families its lines touch (B10-10, B10-13, B11-01, B9-01, B8-08); no owner, capability or candidate state
changes; the candidate census of 1.41.0 carried unchanged."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3046 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.41.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.42.0.json"
TOUCHED = ["B8-08", "B9-01", "B10-10", "B10-13", "B11-01"]


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_touched_families_and_pending_entry_change(docs):
    old, new = docs
    assert new["version"] == "1.42.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert sorted(c for c in nb if nb[c] != ob[c]) == sorted(TOUCHED)
    for c in TOUCHED:
        for k in ("candidate", "in_v3_0_candidate", "capability", "item_codes"):
            assert nb[c][k] == ob[c][k]
        assert A.METHOD in nb[c]["opt_in_readers"] and "V3.0.46" in nb[c]["missing"]
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-419", A.METHOD, "engine/source/arch_v3046.py")
    assert "merge_commit" not in p
    for k in ("candidate_state_counts", "in_v3_0_candidate_counts", "capability_counts", "candidate_census",
              "not_a_boq_line_codes", "item_codes_without_family"):
        assert new[k] == old[k]


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs, monkeypatch):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3046" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_family_naming_the_pending_package_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B10-10")
    b["candidate"]["packages"] = list(b["candidate"]["packages"]) + ["T-419"]
    assert any("pending package T-419" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
