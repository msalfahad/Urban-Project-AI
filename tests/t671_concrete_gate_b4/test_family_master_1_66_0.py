"""T-671: rules/coverage/BOQ_FAMILY_MASTER_1.66.0.json = 1.65.0 (T-668) + the ARCH_TAKEOFF_V3.0.65 package (T-671) +
the B10-06 / B10-07 text. On the task branch the package is PENDING (candidate of record V3.0.64, census and candidate
blocks unchanged); in the merge the Verifier promotes it with --promote (candidate of record V3.0.65, the package in
candidate_packages with its merge commit and verdict, no pending package). Either state: the file equals its builder
and checks clean. Adverse: a base with a pending package, another candidate of record, a family naming the pending
package, a pending package with a merge commit, the package dropped (stale head), a promotion source that names
another task."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t671", ROOT / "research" / "agents_t485"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import arch_v3065 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402
import build_master_1_66_0 as M  # noqa: E402
import build_master_1_43_0 as B43  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.65.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.66.0.json"
FAMS = {"B10-06", "B10-07"}
TEXT = {"evidence", "opt_in_readers", "missing", "note"}
MOVED_TOP_PENDING = {"version", "supersedes", "source", "pending_packages", "families"}


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def _pending(doc):
    return bool(doc["pending_packages"])


def test_builder_reproduces_the_committed_file(docs):
    new = docs[1]
    tc = M._task_commit(new)
    built = M.build_pending(tc) if _pending(new) else M.build_promoted(tc)
    assert M.text(built) == NEW.read_text(encoding="utf-8")


def test_checks_clean_with_git(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=FMC.git_is_ancestor) == []
    assert B43.census_problems(docs[1]) == []


def test_only_the_named_top_fields_move_while_pending(docs):
    old, new = docs
    assert (old["version"], new["version"]) == ("1.65.0", "1.66.0")
    assert set(new) == set(old)
    if not _pending(new):
        assert new["candidate"]["method_version"] == A.METHOD and new["pending_packages"] == []
        q = new["candidate_packages"][-1]
        assert (q["task"], q["method_version"], q["gate"]) == ("T-671", A.METHOD, "GATE_B") and FMC.SHA40.match(
            q["merge_commit"])
        assert new["candidate_packages"][:-1] == old["candidate_packages"]
        return
    assert {k for k in new if new[k] != old[k]} == MOVED_TOP_PENDING
    for k in ("candidate", "candidate_census", "candidate_packages", "released_configuration", "promotion",
              "capability_counts", "capability_change_counts", "candidate_state_counts", "in_v3_0_candidate_counts",
              "not_a_boq_line_codes"):
        assert new[k] == old[k], k
    assert new["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.64"


def test_only_the_two_families_text_moves(docs):
    old, new = docs
    ob, nb = {f["code"]: f for f in old["families"]}, {f["code"]: f for f in new["families"]}
    assert list(nb) == list(ob)
    for code in FAMS:
        assert A.METHOD in nb[code]["opt_in_readers"]
        assert any("arch_v3065.py:" in e and "test_arch_v3065.py:" in e for e in nb[code]["evidence"])
    if _pending(new):
        assert {c for c in nb if nb[c] != ob[c]} == FAMS
        for code in FAMS:
            assert {k for k in nb[code] if nb[code][k] != ob[code].get(k)} == TEXT and set(ob[code]) <= set(nb[code])
            assert nb[code]["candidate"] == ob[code]["candidate"]
    for code in set(nb) - FAMS:
        assert {k for k in nb[code] if nb[code][k] != ob[code].get(k)} <= {"candidate", "in_v3_0_candidate"}


def test_pending_package(docs):
    new = docs[1]
    if not _pending(new):
        pytest.skip("promoted in the merge")
    q = new["pending_packages"]
    assert [(x["task"], x["method_version"], x["module"], x["status"]) for x in q] == [
        ("T-671", A.METHOD, "engine/source/arch_v3065.py", FMC.PENDING_STATUS)]
    assert "merge_commit" not in q[0] and FMC.SHA40.match(q[0]["task_commit"])
    assert q[0]["integrates"] == ["T-669", "T-647", "T-642"]


def test_adverse_builder_refuses_a_base_with_a_pending_package(docs, monkeypatch, tmp_path):
    bad = copy.deepcopy(docs[0])
    bad["pending_packages"] = [{"task": "T-999"}]
    f = tmp_path / "old.json"
    f.write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setattr(M, "OLD", f)
    with pytest.raises(SystemExit, match="expected none"):
        M.build_pending("0" * 40)


def test_adverse_builder_refuses_another_candidate_of_record(docs, monkeypatch, tmp_path):
    bad = copy.deepcopy(docs[0])
    bad["candidate"]["method_version"] = "ARCH_TAKEOFF_V3.0.61"
    f = tmp_path / "old.json"
    f.write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setattr(M, "OLD", f)
    with pytest.raises(SystemExit, match="expected ARCH_TAKEOFF_V3.0.64"):
        M.build_pending("0" * 40)


def test_adverse_family_naming_the_pending_package_refused(docs):
    bad = M.build_pending(M._task_commit(docs[1]))
    b = next(f for f in bad["families"] if f["code"] == "B10-07")
    b["candidate"]["packages"] = list(b["candidate"]["packages"]) + ["T-671"]
    assert any("pending package T-671" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_adverse_pending_package_with_a_verdict_refused(docs):
    bad = M.build_pending(M._task_commit(docs[1]))
    bad["pending_packages"][-1]["merge_commit"] = "a" * 40
    assert any("pending package T-671" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_adverse_pending_dropped_is_stale(docs, monkeypatch):
    bad = M.build_pending(M._task_commit(docs[1]))
    bad["pending_packages"] = []
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3065" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_adverse_promotion_source_for_another_task_refused(docs, monkeypatch, tmp_path):
    f = tmp_path / "prom.json"
    f.write_text(json.dumps([{"task": "T-999", "merge_commit": "a" * 40, "verdict_time": "x", "board_file": "B",
                              "board_status_head": "MERGED", "board_commit": "abcdef12"}]), encoding="utf-8")
    monkeypatch.setattr(M, "PROMOTIONS", f)
    with pytest.raises(SystemExit, match="expected \\[T-671\\]"):
        M.build_promoted(M._task_commit(docs[1]))
