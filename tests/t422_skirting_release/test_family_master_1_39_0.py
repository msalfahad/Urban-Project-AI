"""T-422: rules/coverage/BOQ_FAMILY_MASTER_1.39.0.json = 1.38.0 + the pending ARCH_TAKEOFF_V3.0.44 package + the one
family whose lines it moves (B3-06 ordinary skirting: evidence, opt-in reader, missing text); no item code,
capability or candidate state changes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3044 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.38.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.39.0.json"


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_b3_06_and_the_pending_entry_change(docs):
    old, new = docs
    assert new["version"] == "1.39.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert sorted(c for c in nb if nb[c] != ob[c]) == ["B3-06"]
    f0, f1 = ob["B3-06"], nb["B3-06"]
    for k in ("capability", "capability_change", "item_codes", "candidate", "in_v3_0_candidate"):
        assert f1[k] == f0[k]
    assert f1["item_codes"] == ["FIN.SKIRTING"] and "ARCH_TAKEOFF_V3.0.44" in f1["opt_in_readers"]
    assert f1["evidence"][:-1] == f0["evidence"] and "check_skirting" in f1["evidence"][-1]
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-422", A.METHOD, "engine/source/arch_v3044.py")
    assert p["changes_families_by_item_code"] == ["FIN.SKIRTING"] and "merge_commit" not in p
    for k in ("capability_counts", "candidate_state_counts", "in_v3_0_candidate_counts"):
        assert new[k] == old[k]


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []
