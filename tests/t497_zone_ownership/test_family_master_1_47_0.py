"""T-497: rules/coverage/BOQ_FAMILY_MASTER_1.47.0.json = 1.45.0 + the pending ARCH_TAKEOFF_V3.0.50 package (T-497) + the
B1-02 text; no owner, capability or candidate state changes; the file equals its builder; checks clean on the head."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3050 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.45.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.47.0.json"


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_b1_02_and_the_pending_entry_change(docs):
    old, new = docs
    assert new["version"] == "1.47.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert {c for c in nb if nb[c] != ob[c]} == {"B1-02"}
    for k in ("candidate", "in_v3_0_candidate", "capability", "item_codes"):
        assert nb["B1-02"][k] == ob["B1-02"][k]
    assert A.METHOD in nb["B1-02"]["opt_in_readers"] and "1.069269 .. 1.176467" in nb["B1-02"]["missing"]
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-497", A.METHOD, "engine/source/arch_v3050.py")
    assert "merge_commit" not in p and FMC.SHA40.match(p["task_commit"])
    for k in ("candidate_state_counts", "capability_counts", "candidate_census", "candidate_packages", "promotion",
              "not_a_boq_line_codes", "in_v3_0_candidate_counts"):
        assert new.get(k) == old.get(k)


def test_equals_its_builder(docs):
    sys.path.insert(0, str(ROOT / "research" / "agents_t497"))
    import build_master_1_47_0 as B
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(docs[1]["pending_packages"][-1]["task_commit"]))


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs, monkeypatch):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3050" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
