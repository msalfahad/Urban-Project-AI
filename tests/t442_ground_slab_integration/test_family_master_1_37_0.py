"""T-442: rules/coverage/BOQ_FAMILY_MASTER_1.37.0.json = 1.36.0 + the pending ARCH_TAKEOFF_V3.0.42 package + the
families whose lines it adds, values or re-texts (evidence, opt-in reader, missing / note text); no owner, capability or
candidate state changes."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3042 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.36.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.37.0.json"
FAMS = ["B10-05", "B10-06", "B10-10"]


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_the_touched_families_and_the_pending_entry_change(docs):
    old, new = docs
    assert new["version"] == "1.37.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert sorted(c for c in nb if nb[c] != ob[c]) == FAMS
    for c in FAMS:
        for k in ("item_codes", "capability", "candidate", "in_v3_0_candidate"):
            assert nb[c][k] == ob[c][k]
        assert "ARCH_TAKEOFF_V3.0.42" in nb[c]["opt_in_readers"]
    assert "UNRESOLVED" in nb["B10-05"]["missing"]
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-442", A.METHOD, "engine/source/arch_v3042.py")
    assert p["integrates"] == ["T-444", "T-436", "T-433", "T-401"] and "merge_commit" not in p
    for k in ("candidate_state_counts", "in_v3_0_candidate_counts", "capability_counts"):
        assert new[k] == old[k]


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    probs = FMC.check(bad, root=ROOT, is_ancestor=None)
    acc = FMC.newer_registry_modules(docs[1], ROOT).get("engine/source/arch_v3042.py")
    if acc is None:
        assert any("arch_v3042" in p for p in probs)
    else:
        gov = json.loads((ROOT / f"rules/coverage/BOQ_FAMILY_MASTER_{acc}.json").read_text(encoding="utf-8"))
        assert docs[1]["pending_packages"][-1] in gov["pending_packages"]


def test_family_naming_the_pending_package_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B10-05")
    b["candidate"]["packages"] = ["T-442"]
    assert any("pending package T-442" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_ground_slab_code_owned_by_b10_05(docs):
    own = {c: f["code"] for f in docs[1]["families"] for c in f["item_codes"]}
    assert own[A.GS] == "B10-05"
    assert set(A.TEXT_CODES) <= set(own)
