"""T-310: rules/coverage/BOQ_FAMILY_MASTER_1.49.0.json = 1.47.0 + the pending ARCH_TAKEOFF_V3.0.52 package (T-310) +
the waterproofing family text (B8-01 / B8-02 / B8-03 / B8-09) + B8-09 owning the two pool layer codes; no owner,
capability or candidate state changes; candidate census and candidate blocks unchanged."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3052 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.47.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.49.0.json"
FAMS = {"B8-01", "B8-02", "B8-03", "B8-09"}


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_named_families_and_pending_entry_change(docs):
    old, new = docs
    assert new["version"] == "1.49.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert {c for c in nb if nb[c] != ob[c]} == FAMS
    for c in FAMS:
        for k in ("candidate", "in_v3_0_candidate", "capability"):
            assert nb[c][k] == ob[c][k]
        assert A.METHOD in nb[c]["opt_in_readers"]
    for c in FAMS - {"B8-09"}:
        assert nb[c]["item_codes"] == ob[c]["item_codes"]
    assert (ob["B8-09"]["item_codes"], nb["B8-09"]["item_codes"]) == ([], ["WP.POOL.MEMBRANE",
                                                                         "WP.POOL.PROTECTION_SCREED"])
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-310", A.METHOD, "engine/source/arch_v3052.py")
    assert "merge_commit" not in p
    for k in ("candidate_state_counts", "capability_counts", "candidate_census", "candidate_packages", "promotion",
              "not_a_boq_line_codes", "in_v3_0_candidate_counts"):
        assert new[k] == old[k]


def test_every_new_code_has_one_family(docs):
    new = docs[1]
    for code in (A.POOL_MEMBRANE, A.POOL_SCREED):
        assert [f["code"] for f in new["families"] if code in f["item_codes"]] == ["B8-09"]


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_package_with_a_verdict_refused(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"][-1]["merge_commit"] = "a" * 40
    assert any("pending package T-310" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
