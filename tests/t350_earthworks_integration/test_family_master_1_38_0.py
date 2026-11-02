"""T-350: rules/coverage/BOQ_FAMILY_MASTER_1.38.0.json = 1.37.0 + the pending ARCH_TAKEOFF_V3.0.43 package + the
families whose lines it adds or re-ranges (B1-02 / B1-03 / B1-04 own the three new earthworks codes; B1-01 note only;
B10-01 / B10-04 text); no owner, capability or candidate state changes."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3043 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.37.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.38.0.json"
FAMS = ["B1-01", "B1-02", "B1-03", "B1-04", "B10-01", "B10-04"]


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_the_touched_families_and_the_pending_entry_change(docs):
    old, new = docs
    assert new["version"] == "1.38.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert sorted(c for c in nb if nb[c] != ob[c]) == sorted(FAMS)
    for c in FAMS:
        for k in ("capability", "candidate", "in_v3_0_candidate"):
            assert nb[c][k] == ob[c][k]
    for c, code in (("B1-02", A.EXC), ("B1-03", A.BKF), ("B1-04", A.DSP)):
        assert nb[c]["item_codes"] == ob[c]["item_codes"] + [code]
        assert "ARCH_TAKEOFF_V3.0.43" in nb[c]["opt_in_readers"] and "HELD BLANK" in nb[c]["missing"]
    assert "NOT IN DRAWN SCOPE" in nb["B1-01"]["note"] and nb["B1-01"]["item_codes"] == []
    for c in ("B10-01", "B10-04"):
        assert nb[c]["item_codes"] == ob[c]["item_codes"]
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-350", A.METHOD, "engine/source/arch_v3043.py")
    assert p["integrates"][:3] == ["T-347", "T-356", "T-357"] and "merge_commit" not in p
    for k in ("candidate_state_counts", "in_v3_0_candidate_counts", "capability_counts"):
        assert new[k] == old[k]


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    probs = FMC.check(bad, root=ROOT, is_ancestor=None)
    acc = FMC.newer_registry_modules(docs[1], ROOT).get("engine/source/arch_v3043.py")
    if acc is None:
        assert any("arch_v3043" in p for p in probs)
    else:
        gov = json.loads((ROOT / f"rules/coverage/BOQ_FAMILY_MASTER_{acc}.json").read_text(encoding="utf-8"))
        assert docs[1]["pending_packages"][-1] in gov["pending_packages"]


def test_family_naming_the_pending_package_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B1-02")
    b["candidate"]["packages"] = ["T-350"]
    assert any("pending package T-350" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_earthworks_codes_owned_once(docs):
    own = {}
    for f in docs[1]["families"]:
        for c in f["item_codes"]:
            assert c not in own, f"{c} owned twice"
            own[c] = f["code"]
    assert {own[c] for c in A.EW_CODES} == {"B1-02", "B1-03", "B1-04"}
    assert set(A.RANGE_CODES) <= set(own)
