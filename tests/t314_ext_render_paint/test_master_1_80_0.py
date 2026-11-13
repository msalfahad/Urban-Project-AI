"""T-314 r4: BOQ_FAMILY_MASTER_1.80.0 promotes the merged-pending T-738 (R-T485-1, the 1.48.0 multi-promotion pattern)
and carries T-314 pending; an unmerged pending package is refused (never promoted, never carried)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t314"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import build_master_1_80_0 as M  # noqa: E402

T738_MERGE = "208c568914d2d90eb383ddc66de5faca495a7b88"
OLD = json.loads(M.OLD.read_text(encoding="utf-8"))


def _always(_commit):
    return True


def test_old_registry_holds_t738_pending_and_is_not_rewritten():
    assert OLD["version"] == "1.79.0"
    assert [p["task"] for p in OLD["pending_packages"]] == ["T-738"]
    assert OLD["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.77"


def test_normal_merged_pending_t738_promoted_and_t314_pending():
    doc = M.build_pending("597d2820d8dd328abb542eee0124858a29e9d3f4", is_ancestor=_always)
    assert doc["version"] == "1.80.0"
    assert doc["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.78"
    assert doc["candidate"]["as_of_package"] == "T-738"
    last = doc["candidate_packages"][-1]
    assert last["task"] == "T-738" and last["merge_commit"] == T738_MERGE and last["gate"] == "GATE_B"
    assert last["verdict"].startswith("MERGED (Verifier 2026-11-13 13:50 UTC, Gate B")
    assert [p["task"] for p in doc["pending_packages"]] == ["T-314"]
    assert doc["pending_packages"][0]["method_version"] == "ARCH_TAKEOFF_V3.0.79"
    assert doc["candidate_census"]["method_version"] == "ARCH_TAKEOFF_V3.0.78"
    assert doc["candidate_census"]["issue_counts"] == {}
    assert doc["promotion"]["promoted"] == ["T-738"] and doc["promotion"]["from_registry"] == "1.79.0"
    fams = {f["code"]: f for f in doc["families"]}
    assert "FIN.EXT.PAINT" in fams["B4-07"]["item_codes"]
    for code in ("B4-01", "B7-02", "B7-03"):
        assert "T-738" in fams[code]["candidate"]["packages"], code
    assert all(f["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.78" for f in doc["families"])
    # nothing was written: the old registry is unchanged on disk
    assert json.loads(M.OLD.read_text(encoding="utf-8")) == OLD


def test_committed_1_80_0_equals_its_builder_with_no_problems():
    cur = json.loads(M.NEW.read_text(encoding="utf-8"))
    assert cur["pending_packages"] or cur["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.79"
    if cur["pending_packages"]:
        doc = M.build_pending(cur["pending_packages"][0]["task_commit"])
        assert M.NEW.read_text(encoding="utf-8") == M.text(doc)
    assert M.problems(cur) == []


def test_adverse_pending_package_without_merge_source_refused():
    with pytest.raises(SystemExit, match="never promoted"):
        M.promote_merged_pending(OLD, merged={}, is_ancestor=_always)


def test_adverse_merge_commit_not_on_head_refused():
    with pytest.raises(SystemExit, match="not an ancestor of the head"):
        M.promote_merged_pending(OLD, is_ancestor=lambda _c: False)


def test_adverse_extra_unmerged_pending_package_refused_not_carried():
    old = copy.deepcopy(OLD)
    extra = dict(old["pending_packages"][0], task="T-999", method_version="ARCH_TAKEOFF_V3.0.99")
    old["pending_packages"] = old["pending_packages"] + [extra]
    with pytest.raises(SystemExit, match="T-999: not merged"):
        M.promote_merged_pending(old, is_ancestor=_always)
