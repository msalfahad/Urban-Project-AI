"""T-487: rules/coverage/BOQ_FAMILY_MASTER_1.50.0.json = 1.48.0 + T-483 (merged ea7d375f) PROMOTED by R-T485-1 + the
pending ARCH_TAKEOFF_V3.0.53 package (T-487) + the B9-02 text; no owner, capability or candidate state changes; the file
equals its builder; checks clean on the head."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3053 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.48.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.50.0.json"


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_b9_02_text_and_the_promotion_change(docs):
    old, new = docs
    assert new["version"] == "1.50.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    # outside the candidate blocks only B9-02 changes; no candidate state moves
    assert {c for c in nb if {k: v for k, v in nb[c].items() if k != "candidate"}
            != {k: v for k, v in ob[c].items() if k != "candidate"}} == {"B9-02"}
    assert all(nb[c]["candidate"]["state"] == ob[c]["candidate"]["state"] for c in nb)
    for k in ("candidate", "in_v3_0_candidate", "capability", "item_codes", "v3_0_planned_tasks"):
        if k != "candidate":
            assert nb["B9-02"][k] == ob["B9-02"][k]
    assert nb["B9-02"]["candidate"]["state"] == "NOT_IN_CANDIDATE"
    assert A.METHOD in nb["B9-02"]["opt_in_readers"] and "1.016 m3" in nb["B9-02"]["missing"]
    # T-483 promoted with its merge and verdict; T-487 the only pending package
    assert [p["task"] for p in old["pending_packages"]] == ["T-483"]
    promoted = new["candidate_packages"][-1]
    assert new["candidate_packages"][:-1] == old["candidate_packages"]
    assert (promoted["task"], promoted["merge_commit"][:8], promoted["gate"]) == ("T-483", "ea7d375f", "GATE_B")
    assert promoted["families_changed_by_line_diff"] == ["B3-06"]
    assert [p["task"] for p in new["pending_packages"]] == ["T-487"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-487", A.METHOD, "engine/source/arch_v3053.py")
    assert p["changes_families_by_item_code"] == [A.CODE]
    assert "merge_commit" not in p and FMC.SHA40.match(p["task_commit"])
    # the census at V3.0.51: B3-06 re-derived, every other family identical to 1.48.0's
    cen, ocen = new["candidate_census"], old["candidate_census"]
    assert cen["method_version"] == "ARCH_TAKEOFF_V3.0.51" and cen["lines"] == 4876 and cen["issue_counts"] == {}
    assert cen["lines_sha256"].startswith("c0b6d664")
    assert {c for c in cen["families"] if cen["families"][c] != ocen["families"][c]} <= {"B3-06"}
    for k in ("candidate_state_counts", "capability_counts", "not_a_boq_line_codes", "in_v3_0_candidate_counts"):
        assert new.get(k) == old.get(k)


def test_equals_its_builder(docs):
    sys.path.insert(0, str(ROOT / "research" / "agents_t487"))
    import build_master_1_50_0 as B
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(docs[1]["pending_packages"][-1]["task_commit"]))


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs, monkeypatch):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3053" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
