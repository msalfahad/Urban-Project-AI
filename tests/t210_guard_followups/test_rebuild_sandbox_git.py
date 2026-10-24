"""T-210 (c): a history-reading rebuild (rebuilt_package(..., git=True)) reads the right commit in a normal checkout AND in
a linked git worktree, and its `%h` stamp does not depend on the size of the repository.

Synthetic repositories in tmp_path only (git with a fixed identity). Hand truth: the builder writes the output of
`git log -1 --format=%h -- research/pkg/build.py` run from the copy; it must equal the same command on the real tree
with core.abbrev=7, and never `UNCOMMITTED` (the T-202 WORKTREE_GITDIR failure: `.git` of a worktree is a FILE, so the
copy pointed at a file and git failed).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tests.rebuild_sandbox import GIT_ABBREV, _git_dir, _git_env, rebuilt_package

BUILDER = '''
import os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
out = subprocess.run(["git", "log", "-1", "--format=%h", "--", "research/pkg/build.py"], cwd=ROOT,
                     capture_output=True, text=True).stdout.strip()
(HERE / "STAMP.txt").write_text((out or "UNCOMMITTED") + "\\n")
(HERE / "ENV.txt").write_text(os.environ.get("GIT_CONFIG_COUNT", "-") + "\\n")
'''

GIT = ["git", "-c", "user.name=t210", "-c", "user.email=t210@example.invalid", "-c", "commit.gpgsign=false",
       "-c", "init.defaultBranch=main"]


def _git(cwd, *args):
    return subprocess.run([*GIT, *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "research" / "pkg").mkdir(parents=True)
    (root / "research" / "pkg" / "build.py").write_text(BUILDER)
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "builder")
    return root


def expected(root: Path) -> str:
    return _git(root, "-c", "core.abbrev=7", "log", "-1", "--format=%h", "--", "research/pkg/build.py")


def stamp(root: Path) -> str:
    with rebuilt_package(root, "research/pkg/build.py", git=True) as out:
        return (out / "STAMP.txt").read_text().strip()


def test_normal_checkout_reads_the_commit(tmp_path):
    root = make_repo(tmp_path)
    assert (root / ".git").is_dir()
    assert _git_dir(root) == (root / ".git").resolve()
    got = stamp(root)
    assert got == expected(root) and got != "UNCOMMITTED" and len(got) == 7


def test_linked_worktree_reads_the_commit(tmp_path):
    root = make_repo(tmp_path)
    wt = tmp_path / "wt"
    _git(root, "worktree", "add", "-q", "-b", "task", str(wt))
    assert (wt / ".git").is_file()                         # the T-202 case: .git is a FILE in a worktree
    assert _git_dir(wt) == (root / ".git" / "worktrees" / "wt").resolve()
    (wt / "research" / "pkg" / "note.txt").write_text("x\n")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-q", "-m", "worktree commit")     # the builder's file keeps its commit from the main branch
    got = stamp(wt)
    assert got == expected(wt) and got != "UNCOMMITTED"


def test_relative_gitdir_line_is_resolved_from_the_root(tmp_path):
    root = tmp_path / "r"
    (root / "admin").mkdir(parents=True)
    (root / ".git").write_text("gitdir: admin\n")
    assert _git_dir(root) == (root / "admin").resolve()


def test_git_file_without_gitdir_line_is_refused(tmp_path):
    root = tmp_path / "r"
    root.mkdir()
    (root / ".git").write_text("not a gitdir line\n")
    with pytest.raises(ValueError):
        _git_dir(root)


def test_abbrev_is_pinned_over_a_caller_setting(tmp_path, monkeypatch):
    """adverse: a caller environment asking for 12-character abbreviations still gets the pinned 7."""
    root = make_repo(tmp_path)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.abbrev")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "12")
    got = stamp(root)
    assert len(got) == int(GIT_ABBREV) and got == expected(root)


def test_git_env_keeps_existing_entries_and_appends_the_pin():
    env = _git_env({"GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "a.b", "GIT_CONFIG_VALUE_0": "1",
                    "GIT_CONFIG_KEY_1": "c.d", "GIT_CONFIG_VALUE_1": "2", "PATH": os.environ.get("PATH", "")})
    assert env["GIT_CONFIG_COUNT"] == "3"
    assert (env["GIT_CONFIG_KEY_0"], env["GIT_CONFIG_KEY_1"]) == ("a.b", "c.d")
    assert (env["GIT_CONFIG_KEY_2"], env["GIT_CONFIG_VALUE_2"]) == ("core.abbrev", GIT_ABBREV)
    assert _git_env({})["GIT_CONFIG_COUNT"] == "1"


def test_builder_without_git_gets_no_git_and_no_pin(tmp_path, monkeypatch):
    """git=False is unchanged: no .git in the copy (UNCOMMITTED) and the caller's environment as it is."""
    root = make_repo(tmp_path)
    monkeypatch.delenv("GIT_CONFIG_COUNT", raising=False)
    with rebuilt_package(root, "research/pkg/build.py") as out:
        assert not (out.parents[1] / ".git").exists()
        assert (out / "STAMP.txt").read_text().strip() == "UNCOMMITTED"
        assert (out / "ENV.txt").read_text().strip() == "-"
