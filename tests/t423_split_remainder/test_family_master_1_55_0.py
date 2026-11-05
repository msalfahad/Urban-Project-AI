"""T-423: rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json = 1.54.0 + the promotion of its merged pending package (T-310
V3.0.57, merge 87ef8718; R-T485-1) with the families it changed (B8-01 / B8-02 / B8-03 / B8-09) re-derived from the
V3.0.57 census and the line diff V3.0.56 -> V3.0.57, + the pending ARCH_TAKEOFF_V3.0.58 package (T-423) and the
B3-01 / B3-04 / B4-01 / B4-03 / B5-01 text. Adverse: a family naming the pending package, a pending package with a
verdict, the pending package dropped (stale head)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t423", ROOT / "research" / "agents_t485", ROOT / "research" / "agents_t479"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import arch_v3058 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402
import build_master_1_55_0 as M  # noqa: E402
import build_master_1_43_0 as B43  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.54.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json"
FAMS = {"B3-01", "B3-04", "B4-01", "B4-03", "B5-01"}
PROMOTED_FAMS = {"B8-01", "B8-02", "B8-03", "B8-09"}
TEXT = ("evidence", "opt_in_readers", "missing", "note")


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_builder_reproduces_the_committed_file(docs):
    assert M.text(M.build(docs[1]["pending_packages"][-1]["task_commit"])) == NEW.read_text(encoding="utf-8")


def test_checks_clean_with_git(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=FMC.git_is_ancestor) == []
    assert B43.census_problems(docs[1]) == []


def test_merged_t310_promoted_and_only_v3058_pending(docs):
    old, new = docs
    assert new["version"] == "1.55.0" and [p["task"] for p in old["pending_packages"]] == ["T-310"]
    p = new["candidate_packages"][-1]
    assert p["task"] == "T-310" and p["merge_commit"].startswith("87ef8718")
    assert new["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.57" and new["candidate"]["as_of_package"] == "T-310"
    q = new["pending_packages"]
    assert [(x["task"], x["method_version"], x["module"]) for x in q] == [("T-423", A.METHOD,
                                                                          "engine/source/arch_v3058.py")]


def test_nothing_released_changed_and_only_named_families_move(docs):
    old, new = docs
    for k in ("capability_counts", "capability_change_counts", "released_configuration", "not_a_boq_line_codes"):
        assert new[k] == old[k]
    ob, nb = {f["code"]: f for f in old["families"]}, {f["code"]: f for f in new["families"]}
    for code, f in nb.items():
        for k, v in f.items():
            if k == "candidate" or (code in FAMS and k in TEXT) or (code in PROMOTED_FAMS and k == "in_v3_0_candidate"):
                continue                        # B8-09 (pool layers, merged by T-310) enters the candidate
            assert v == ob[code][k], (code, k)
        assert f["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.57"
        if code in PROMOTED_FAMS:
            assert "T-310" in f["candidate"]["packages"]
    assert new["candidate_census"]["previous"]["method_version"] == "ARCH_TAKEOFF_V3.0.56"


def test_adverse_family_naming_the_pending_package_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B5-01")
    b["candidate"]["packages"] = list(b["candidate"]["packages"]) + ["T-423"]
    assert any("pending package T-423" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_adverse_pending_package_with_a_verdict_refused(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"][-1]["merge_commit"] = "a" * 40
    assert any("pending package T-423" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_adverse_pending_dropped_is_stale(docs, monkeypatch):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = []
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3058" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
