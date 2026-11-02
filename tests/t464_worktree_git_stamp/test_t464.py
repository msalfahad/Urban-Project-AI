"""T-464 (owner directive D3, 2026-11-02): the builder git-stamp works when `.git` is a FILE (linked worktrees).

T-210 made `rebuilt_package(..., git=True)` follow the `gitdir:` line, and its worktree test keeps the builder's file at
its main-branch commit, so it cannot tell "reads the worktree's HEAD" from "reads the main checkout's HEAD". These
tests close that gap and the adverse cases. Synthetic repositories in tmp_path only (git with a fixed identity).

Hand truth per case: the stamp is `git log -1 --format=%h -- research/pkg/build.py` run on the original tree with
core.abbrev=7 (the commit that last changed the builder ON THAT TREE'S BRANCH), never UNCOMMITTED.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.rebuild_sandbox import _git_dir, _readable_git_dir, rebuilt_package

ROOT = Path(__file__).resolve().parents[2]

BUILDER = '''
import subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
out = subprocess.run(["git", "log", "-1", "--format=%h", "--", "research/pkg/build.py"], cwd=ROOT,
                     capture_output=True, text=True).stdout.strip()
(HERE / "STAMP.txt").write_text((out or "UNCOMMITTED") + "\\n")
'''

GIT = ["git", "-c", "user.name=t464", "-c", "user.email=t464@example.invalid", "-c", "commit.gpgsign=false",
       "-c", "init.defaultBranch=main"]

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="prerequisite: git")


def _git(cwd, *args):
    return subprocess.run([*GIT, *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def _expected(tree: Path) -> str:
    return _git(tree, "-c", "core.abbrev=7", "log", "-1", "--format=%h", "--", "research/pkg/build.py")


def _stamp(tree: Path) -> str:
    with rebuilt_package(tree, "research/pkg/build.py", git=True) as out:
        return (out / "STAMP.txt").read_text().strip()


def _repo_with_diverged_worktree(tmp_path: Path):
    """main: builder committed (c1). worktree `wt` on branch task: builder CHANGED and committed (c2 != c1)."""
    root = tmp_path / "repo"
    (root / "research" / "pkg").mkdir(parents=True)
    (root / "research" / "pkg" / "build.py").write_text(BUILDER)
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "c1 builder")
    wt = tmp_path / "wt"
    _git(root, "worktree", "add", "-q", "-b", "task", str(wt))
    (wt / "research" / "pkg" / "build.py").write_text(BUILDER + "# task-branch change\n")
    _git(wt, "commit", "-q", "-am", "c2 builder on the task branch")
    return root, wt


def _state(paths):
    return {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in paths if p.exists()}


def test_worktree_stamp_is_the_worktree_commit_not_the_main_checkout(tmp_path):
    root, wt = _repo_with_diverged_worktree(tmp_path)
    assert (wt / ".git").is_file()
    main_c, task_c = _expected(root), _expected(wt)
    assert main_c != task_c                                   # the case T-210 could not distinguish
    assert _stamp(wt) == task_c                               # worktree HEAD read, not the common dir's HEAD
    assert _stamp(root) == main_c                             # normal checkout (`.git` a directory) unchanged


def test_relative_gitdir_line_end_to_end(tmp_path):
    root, wt = _repo_with_diverged_worktree(tmp_path)
    absolute = _git_dir(wt)
    (wt / ".git").write_text(f"gitdir: {os.path.relpath(absolute, wt)}\n")   # git also accepts a relative line
    assert not Path((wt / ".git").read_text().split(":", 1)[1].strip()).is_absolute()
    assert _git_dir(wt) == absolute
    assert _stamp(wt) == _expected(wt)


def test_stamp_reads_only_never_writes_the_shared_git_dirs(tmp_path):
    root, wt = _repo_with_diverged_worktree(tmp_path)
    admin = _git_dir(wt)
    watched = [admin / "HEAD", admin / "index", admin / "ORIG_HEAD", root / ".git" / "HEAD", root / ".git" / "index",
               root / ".git" / "refs" / "heads" / "main", root / ".git" / "refs" / "heads" / "task",
               root / ".git" / "packed-refs"]
    before = _state(watched)
    _stamp(wt)
    assert _state(watched) == before
    assert not list(admin.glob("*.lock")) and not list((root / ".git").glob("*.lock"))


def test_adverse_pruned_worktree_admin_dir_is_refused_not_stamped_uncommitted(tmp_path):
    root, wt = _repo_with_diverged_worktree(tmp_path)
    shutil.rmtree(_git_dir(wt))                               # e.g. `git worktree prune` / a setup that recreated it
    with pytest.raises(RuntimeError, match="not a readable git directory"):
        with rebuilt_package(wt, "research/pkg/build.py", git=True):
            pass
    assert not (wt / "research" / "pkg" / "STAMP.txt").exists()


def test_adverse_no_git_at_all_is_refused(tmp_path):
    tree = tmp_path / "export"
    (tree / "research" / "pkg").mkdir(parents=True)
    (tree / "research" / "pkg" / "build.py").write_text(BUILDER)
    with pytest.raises(RuntimeError, match="not a readable git directory"):
        with rebuilt_package(tree, "research/pkg/build.py", git=True):
            pass
    with rebuilt_package(tree, "research/pkg/build.py") as out:   # git=False keeps its meaning: no history
        assert (out / "STAMP.txt").read_text().strip() == "UNCOMMITTED"


def test_adverse_git_file_pointing_at_a_plain_directory_is_refused(tmp_path):
    root, wt = _repo_with_diverged_worktree(tmp_path)
    bogus = tmp_path / "not_a_git_dir"
    bogus.mkdir()
    (wt / ".git").write_text(f"gitdir: {bogus}\n")
    with pytest.raises(RuntimeError):
        _readable_git_dir(wt)


@pytest.mark.skipif(not (ROOT / ".git").exists(), reason="prerequisite: this checkout's git metadata")
def test_this_checkout_resolves_to_its_own_head():
    """Every agent checkout is a linked worktree (`.git` a FILE); a normal clone has a directory. Both must resolve to
    the git dir whose HEAD is this checkout's HEAD."""
    gd = _readable_git_dir(ROOT)
    via_dir = subprocess.run(["git", "--git-dir", str(gd), "rev-parse", "HEAD"], capture_output=True, text=True,
                             check=True).stdout.strip()
    via_tree = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    assert via_dir == via_tree
