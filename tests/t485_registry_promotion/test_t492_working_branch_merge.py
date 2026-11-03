"""T-492: the stale-pending guard counts a package as merged only once its task commit reached the WORKING BRANCH
(Lead ruling F-C-T443-1). Synthetic git histories built in a temporary repository (no development-villa data); then
the guard on this checkout."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t485", ROOT / "research" / "agents_t492"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import build_master_1_43_0 as B  # noqa: E402
import working_branch_merge as WBM  # noqa: E402

WB = WBM.WORKING_BRANCH
ENV = dict(os.environ, GIT_AUTHOR_NAME="t492", GIT_AUTHOR_EMAIL="t492@example.invalid", GIT_COMMITTER_NAME="t492",
           GIT_COMMITTER_EMAIL="t492@example.invalid", GIT_CONFIG_NOSYSTEM="1", HOME=os.devnull)


class Repo:
    def __init__(self, path):
        self.path = path
        self.n = 0
        self.git("init", "-q", "-b", WB)

    def git(self, *a):
        r = subprocess.run(["git", "-C", str(self.path), "-c", "commit.gpgsign=false", *a], capture_output=True,
                           text=True, env=ENV)
        assert r.returncode == 0, r.stderr
        return r.stdout.strip()

    def commit(self, msg):
        self.n += 1
        (self.path / f"f{self.n}.txt").write_text(msg, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD")

    def publish(self):
        """origin/<working branch> := the local working branch (what the Verifier's push does)"""
        self.git("update-ref", f"refs/remotes/origin/{WB}", self.git("rev-parse", f"refs/heads/{WB}"))

    def merge(self, ref, msg):
        self.git("merge", "-q", "--no-ff", "-m", msg, ref)
        return self.git("rev-parse", "HEAD")


def _doc(**tasks):
    return {"pending_packages": [{"task": t, "task_commit": c} for t, c in tasks.items()]}


def _stale(repo, doc):
    return B.stale_pending(doc, WBM.make_merged(repo.path))


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "r").mkdir()
    r = Repo(tmp_path / "r")
    r.commit("base")
    r.publish()
    return r


def test_a_normal_task_branch_carrying_its_own_pending_entry_passes(repo):
    repo.git("checkout", "-q", "-b", "agents/task-T-901")
    t = repo.commit("T-901 package")                     # cut straight from W: first parent of its commit IS W
    assert _stale(repo, _doc(**{"T-901": t})) == []
    head = repo.git("rev-parse", "HEAD")
    assert subprocess.run(["git", "-C", str(repo.path), "merge-base", "--is-ancestor", t, head]).returncode == 0
    assert B.stale_pending(_doc(**{"T-901": t}), lambda c: c == t) == ["T-901"]   # the old HEAD predicate's verdict


def test_a_task_branch_that_merged_the_working_branch_in_still_passes(repo):
    """the T-443 shape: task commit, then the latest working branch merged INTO the task branch"""
    repo.git("checkout", "-q", "-b", "agents/task-T-902")
    t = repo.commit("T-902 package")
    repo.git("checkout", "-q", WB)
    repo.commit("another merge on W")
    repo.publish()
    repo.git("checkout", "-q", "agents/task-T-902")
    repo.merge(WB, "merge W into T-902")
    assert _stale(repo, _doc(**{"T-902": t})) == []


def test_b_adverse_package_merged_into_the_working_branch_and_still_pending_fails(repo):
    repo.git("checkout", "-q", "-b", "agents/task-T-903")
    t = repo.commit("T-903 package")
    repo.git("checkout", "-q", WB)
    repo.merge("agents/task-T-903", "Merge agents/task-T-903 (verified)")
    repo.publish()
    repo.git("checkout", "-q", "-b", "agents/task-T-904")            # checked from any later task branch too
    t4 = repo.commit("T-904 package")
    assert _stale(repo, _doc(**{"T-903": t, "T-904": t4})) == ["T-903"]


def test_c_adverse_pending_commit_on_the_first_parent_chain_fails(repo):
    """fast-forwarded / committed directly on the working line: on W's first-parent chain, no merge commit"""
    t = repo.commit("T-905 committed on the working line")
    repo.publish()
    fp = repo.git("rev-list", "--first-parent", "HEAD").split()
    assert t in fp
    repo.git("checkout", "-q", "--detach", "HEAD")
    assert _stale(repo, _doc(**{"T-905": t})) == ["T-905"]


def test_c2_adverse_local_working_branch_ahead_of_origin_counts_its_direct_commits(repo):
    t = repo.commit("T-906 on the local working branch, not yet pushed")      # HEAD -> refs/heads/<WB>, ahead of W
    assert _stale(repo, _doc(**{"T-906": t})) == ["T-906"]
    repo.git("checkout", "-q", "-b", "agents/task-T-907")                    # same graph seen from a task branch
    assert _stale(repo, _doc(**{"T-906": t})) == []                          # unpublished: not merged


def test_trial_merge_of_a_ready_package_does_not_name_it(repo):
    """the Checker's trial merge: HEAD = an unpushed merge of the READY package into W"""
    repo.git("checkout", "-q", "-b", "agents/task-T-908")
    t = repo.commit("T-908 package")
    repo.git("checkout", "-q", "--detach", WB)
    repo.merge("agents/task-T-908", "trial merge T-908")
    assert _stale(repo, _doc(**{"T-908": t})) == []
    repo.git("checkout", "-q", WB)                                           # same on the checked-out working branch
    repo.merge("agents/task-T-908", "trial merge T-908 on the branch")
    assert _stale(repo, _doc(**{"T-908": t})) == []                          # brought in by a merge, not published


def test_unmerged_package_integrated_by_another_task_branch_stays_pending(repo):
    repo.git("checkout", "-q", "-b", "agents/task-T-909")
    t9 = repo.commit("T-909 package")
    repo.git("checkout", "-q", "-b", "agents/task-T-910", WB)
    repo.merge("agents/task-T-909", "T-910 integrates T-909")
    t10 = repo.commit("T-910 package")
    assert _stale(repo, _doc(**{"T-909": t9, "T-910": t10})) == []


def test_adverse_no_working_branch_ref_is_refused_loudly(tmp_path):
    (tmp_path / "x").mkdir()
    r = Repo(tmp_path / "x")
    r.commit("base")
    r.git("branch", "-m", WB, "other")
    with pytest.raises(WBM.WorkingBranchUnavailable):
        WBM.make_merged(r.path)


def test_local_branch_is_used_when_origin_ref_is_absent(tmp_path):
    (tmp_path / "y").mkdir()
    r = Repo(tmp_path / "y")
    t = r.commit("T-911 merged locally")
    r.git("checkout", "-q", "-b", "agents/task-T-912")
    assert _stale(r, _doc(**{"T-911": t})) == ["T-911"]


def test_unknown_commit_is_not_merged(repo):
    assert _stale(repo, _doc(**{"T-913": "f" * 40})) == []


# ---------- this checkout ----------

def test_working_tip_resolves_on_this_checkout():
    assert len(WBM.working_tip(ROOT)) == 40
