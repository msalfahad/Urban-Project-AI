"""T-488: rules/coverage/BOQ_FAMILY_MASTER_1.52.0.json = 1.51.0 + T-480 (merged 1b66b719) PROMOTED by R-T485-1 + the
pending ARCH_TAKEOFF_V3.0.55 package (T-488) + the B9-01 / B10-12 text; no owner, capability or candidate-state change;
the census moves to V3.0.54 (only B7-09's block); the file equals its builder; checks clean on the head."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3055 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.51.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.52.0.json"


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_b9_01_b10_12_text_and_the_promotion_change(docs):
    old, new = docs
    assert new["version"] == "1.52.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert {c for c in nb if {k: v for k, v in nb[c].items() if k != "candidate"}
            != {k: v for k, v in ob[c].items() if k != "candidate"}} == {"B9-01", "B10-12"}
    assert {c for c in nb if nb[c]["candidate"]["state"] != ob[c]["candidate"]["state"]} == set()
    for c in ("B9-01", "B10-12"):
        for k in ("in_v3_0_candidate", "capability", "item_codes", "v3_0_planned_tasks"):
            assert nb[c][k] == ob[c][k]
        assert A.METHOD in nb[c]["opt_in_readers"]
    assert "HELD ON ROOF DATUM" in nb["B9-01"]["missing"] and "F-T488-1" in nb["B9-01"]["missing"]
    assert [p["task"] for p in old["pending_packages"]] == ["T-480"]
    promoted = new["candidate_packages"][-1]
    assert new["candidate_packages"][:-1] == old["candidate_packages"]
    assert (promoted["task"], promoted["merge_commit"][:8], promoted["gate"]) == ("T-480", "1b66b719", "GATE_B")
    assert promoted["families_changed_by_line_diff"] == ["B7-09"]
    p = new["pending_packages"][-1]
    assert [x["task"] for x in new["pending_packages"]] == ["T-488"]
    assert (p["task"], p["method_version"], p["module"]) == ("T-488", A.METHOD, "engine/source/arch_v3055.py")
    assert p["changes_families_by_item_code"] == ["ARCH.WALL_PANEL", "ARCH.WALL_VOLUME", "MAS.BLOCK", "STR.CONC.PARAPET"]
    assert "merge_commit" not in p and FMC.SHA40.match(p["task_commit"])
    cen, ocen = new["candidate_census"], old["candidate_census"]
    assert cen["method_version"] == "ARCH_TAKEOFF_V3.0.54" and cen["lines"] == 4939 and cen["issue_counts"] == {}
    assert cen["lines_sha256"].startswith("c85c4630")
    assert {c for c in cen["families"] if cen["families"][c] != ocen["families"][c]} <= {"B7-09"}
    for k in ("capability_counts", "not_a_boq_line_codes"):
        assert new.get(k) == old.get(k)


def test_equals_its_builder(docs):
    sys.path.insert(0, str(ROOT / "research" / "agents_t488"))
    import build_master_1_52_0 as B
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(docs[1]["pending_packages"][-1]["task_commit"]))


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs, monkeypatch):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3055" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
