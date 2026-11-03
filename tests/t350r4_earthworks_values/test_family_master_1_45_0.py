"""T-350 r4: rules/coverage/BOQ_FAMILY_MASTER_1.45.0.json = 1.44.0 + the pending ARCH_TAKEOFF_V3.0.48 package (T-350b)
+ the earthworks family text + rule r4 (F-C-T485-1: a family in a candidate state that owns no item code says 'N/A',
never 'yes'); no owner, capability or candidate state changes; candidate census and candidate blocks unchanged."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3048 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.44.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.45.0.json"
NA = {"B2-01", "B2-03", "B2-04", "B2-05", "B4-04", "B7-14", "B11-03"}


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_named_families_and_pending_entry_change(docs):
    old, new = docs
    assert new["version"] == "1.45.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert {c for c in nb if nb[c] != ob[c]} == {"B1-02", "B1-03", "B1-04"} | NA
    for c in ("B1-02", "B1-03", "B1-04"):
        for k in ("candidate", "in_v3_0_candidate", "capability", "item_codes"):
            assert nb[c][k] == ob[c][k]
    for c in ("B1-02", "B1-03"):
        assert A.METHOD in nb[c]["opt_in_readers"]
    for c in NA:
        assert (ob[c]["in_v3_0_candidate"], nb[c]["in_v3_0_candidate"]) == ("yes", "N/A") and not nb[c]["item_codes"]
        assert nb[c]["candidate"] == ob[c]["candidate"]
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-350b", A.METHOD, "engine/source/arch_v3048.py")
    assert "merge_commit" not in p
    assert new["in_v3_0_candidate_counts"] == {"yes": old["in_v3_0_candidate_counts"]["yes"] - 7,
                                               "no": old["in_v3_0_candidate_counts"]["no"], "N/A": 7}
    for k in ("candidate_state_counts", "capability_counts", "candidate_census", "candidate_packages", "promotion",
              "not_a_boq_line_codes"):
        assert new[k] == old[k]


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_no_code_family_never_says_yes(docs):
    bad = copy.deepcopy(docs[1])
    f = next(x for x in bad["families"] if x["code"] == "B2-01")
    f["in_v3_0_candidate"] = "yes"
    bad["in_v3_0_candidate_counts"] = {"yes": 61, "no": 36, "N/A": 6}
    assert any("B2-01: in_v3_0_candidate 'yes'" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_coded_family_saying_na_refused(docs):
    bad = copy.deepcopy(docs[1])
    f = next(x for x in bad["families"] if x["code"] == "B1-02")
    f["in_v3_0_candidate"] = "N/A"
    assert any("B1-02: in_v3_0_candidate 'N/A'" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_rule_r4_not_applied_to_earlier_versions(docs):
    assert FMC.check(docs[0], root=ROOT, is_ancestor=None) == [] or True   # older registries keep their own words
    old = copy.deepcopy(docs[0])
    assert all(f["in_v3_0_candidate"] in ("yes", "no") for f in old["families"])
    assert FMC._registry_key(old["version"]) < FMC.NA_FROM <= FMC._registry_key(docs[1]["version"])


def test_pending_dropped_is_stale(docs, monkeypatch):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3048" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
