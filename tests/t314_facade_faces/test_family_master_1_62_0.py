"""T-314 r2: rules/coverage/BOQ_FAMILY_MASTER_1.62.0.json = 1.61.0 (T-563) + the pending ARCH_TAKEOFF_V3.0.62 package
(T-314) after the pending V3.0.60 / V3.0.61 + the B4-04 / B4-07 text. No promotion: the candidate of record V3.0.59, its
census, the pending T-423 / T-563 packages and every candidate block are unchanged; the file equals its builder; checks
clean on the head. Adverse: a base without the two pending packages, another candidate of record, a family naming the
pending package, a pending package with a merge commit, the pending package dropped (stale head)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t314", ROOT / "research" / "agents_t485"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import arch_v3062 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402
import build_master_1_62_0 as M  # noqa: E402
import build_master_1_43_0 as B43  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.61.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.62.0.json"
FAMS = {"B4-04", "B4-07"}
TEXT = {"evidence", "opt_in_readers", "missing", "note"}
MOVED_TOP = {"version", "supersedes", "source", "pending_packages", "families"}


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_builder_reproduces_the_committed_file(docs):
    assert M.text(M.build(docs[1]["pending_packages"][-1]["task_commit"])) == NEW.read_text(encoding="utf-8")


def test_checks_clean_with_git(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=FMC.git_is_ancestor) == []
    assert B43.census_problems(docs[1]) == []


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_only_the_named_top_fields_move(docs):
    old, new = docs
    assert (old["version"], new["version"]) == ("1.61.0", "1.62.0")
    assert set(new) == set(old)
    assert {k for k in new if new[k] != old[k]} == MOVED_TOP
    for k in ("candidate", "candidate_census", "candidate_packages", "released_configuration", "promotion",
              "capability_counts", "capability_change_counts", "candidate_state_counts", "in_v3_0_candidate_counts",
              "not_a_boq_line_codes"):
        assert new[k] == old[k], k
    assert new["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.59"


def test_only_the_two_families_text_moves(docs):
    old, new = docs
    ob, nb = {f["code"]: f for f in old["families"]}, {f["code"]: f for f in new["families"]}
    assert list(nb) == list(ob)
    assert {c for c in nb if nb[c] != ob[c]} == FAMS
    for code in FAMS:
        assert {k for k in nb[code] if nb[code][k] != ob[code].get(k)} == TEXT and set(ob[code]) <= set(nb[code])
        assert A.METHOD in nb[code]["opt_in_readers"]
        assert any("arch_v3062.py:" in e and "test_arch_v3062.py:" in e for e in nb[code]["evidence"])
        assert nb[code]["candidate"] == ob[code]["candidate"]


def test_pending_package(docs):
    old, new = docs
    assert old["pending_packages"] == new["pending_packages"][:2]
    assert [p["task"] for p in old["pending_packages"]] == ["T-423", "T-563"]
    q = new["pending_packages"]
    assert [(x["task"], x["method_version"], x["module"], x["status"]) for x in q[2:]] == [
        ("T-314", A.METHOD, "engine/source/arch_v3062.py", FMC.PENDING_STATUS)]
    assert "merge_commit" not in q[2] and FMC.SHA40.match(q[2]["task_commit"])


def test_adverse_builder_refuses_a_base_without_the_two_pending(docs, monkeypatch, tmp_path):
    for pend in ([], [{"task": "T-423"}], [{"task": "T-423"}, {"task": "T-999"}], [{"task": "T-563"}, {"task": "T-423"}]):
        bad = copy.deepcopy(docs[0])
        bad["pending_packages"] = pend
        f = tmp_path / "old.json"
        f.write_text(json.dumps(bad), encoding="utf-8")
        monkeypatch.setattr(M, "OLD", f)
        with pytest.raises(SystemExit, match="expected exactly T-423 .V3.0.60. and T-563"):
            M.build("0" * 40)


def test_adverse_builder_refuses_another_candidate_of_record(docs, monkeypatch, tmp_path):
    bad = copy.deepcopy(docs[0])
    bad["candidate"]["method_version"] = "ARCH_TAKEOFF_V3.0.58"
    f = tmp_path / "old.json"
    f.write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setattr(M, "OLD", f)
    with pytest.raises(SystemExit, match="expected ARCH_TAKEOFF_V3.0.59"):
        M.build("0" * 40)


def test_adverse_family_naming_the_pending_package_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B4-07")
    b["candidate"]["packages"] = list(b["candidate"]["packages"]) + ["T-314"]
    assert any("pending package T-314" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_adverse_pending_package_with_a_verdict_refused(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"][-1]["merge_commit"] = "a" * 40
    assert any("pending package T-314" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_adverse_pending_dropped_is_stale(docs, monkeypatch):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:2]
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3062" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
