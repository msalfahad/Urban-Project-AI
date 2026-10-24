"""Rebuild a frozen research package in a temporary copy of the repository (T-020).

The `test_rebuild_is_byte_identical` tests used to re-run each package builder in place: the builder rewrote the
committed, frozen package, so any byte difference (e.g. a one-ulp `sum()` change on Python >= 3.12) overwrote the
frozen artefacts and cascaded into every later test and the freeze-integrity guard.

`rebuilt_package(root, builder, *args)` copies the working tree (without `.git`, caches and virtual environments)
into a temporary directory, runs the builder there with the same interpreter, `-I` and the copy as cwd, and yields
the rebuilt package directory. Path arguments that point inside `root` are re-pointed into the copy, so the builder
reads and writes nothing in the real tree. The test then compares the rebuilt bytes with the committed package: a
mismatch fails that one test and writes nothing. The real tree is checked (size, mtime of every file outside
`.git` and caches) before and after the build; any change fails the test and is listed. The copy is deleted on exit.
A builder that exits non-zero raises `subprocess.CalledProcessError`, as `subprocess.run(check=True)` did.
`git=True` is for a builder that only reads history (e.g. `git log -1 -- <path>` for a version stamp): the copy gets a
`.git` file pointing at the real repository's git directory. Such a builder must not run git commands that write.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

SKIP = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv", "node_modules"}


def _tree_state(root: Path) -> dict:
    out = {}
    for dp, dn, fs in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fs:
            p = os.path.join(dp, f)
            try:
                st = os.lstat(p)
            except FileNotFoundError:
                continue
            out[os.path.relpath(p, root)] = (st.st_size, st.st_mtime_ns)
    return out


def _changes(before: dict, after: dict) -> list:
    return ([f"created: {k}" for k in sorted(set(after) - set(before))]
            + [f"deleted: {k}" for k in sorted(set(before) - set(after))]
            + [f"modified: {k}" for k in sorted(set(before) & set(after)) if before[k] != after[k]])


def _remap(arg, root: Path, copy: Path) -> str:
    s = str(arg)
    p = Path(s)
    if p.is_absolute():
        for base in {root, root.resolve()}:
            try:
                return str(copy / p.relative_to(base))
            except ValueError:
                pass
    return s


def _git_dir(root: Path) -> Path:
    """The git directory of `root`: `root/.git` when it is a directory (a normal checkout); when it is a FILE (a linked
    git worktree or a submodule: `gitdir: <path>`), the directory that file names, relative paths taken from `root`
    (T-210: pointing the copy at `root/.git` itself made git fail in a worktree, so a history-reading builder recorded
    UNCOMMITTED instead of the commit)."""
    dot = root / ".git"
    if dot.is_file():
        for line in dot.read_text(encoding="utf-8").splitlines():
            if line.startswith("gitdir:"):
                target = Path(line[len("gitdir:"):].strip())
                return (target if target.is_absolute() else root / target).resolve()
        raise ValueError(f"{dot} is a file without a 'gitdir:' line")
    return dot.resolve()


GIT_ABBREV = "7"  # git's own minimum abbreviation, the length every committed package stamp was written with


def _git_env(base) -> dict:
    """The environment of a history-reading builder (git=True): `base` plus core.abbrev pinned to GIT_ABBREV through
    git's GIT_CONFIG_COUNT mechanism (git >= 2.31; existing GIT_CONFIG_* entries are kept). With the default
    core.abbrev=auto the length of `%h` grows with the object count of the repository (7 -> 8 characters once it holds
    enough objects), so a stamp that was right when it was built would differ on the same commit later (T-210). The
    pin keeps `%h` at least 7 characters and longer only when 7 would be ambiguous, as git guarantees."""
    env = dict(base)
    n = int(env.get("GIT_CONFIG_COUNT") or 0)
    env[f"GIT_CONFIG_KEY_{n}"] = "core.abbrev"
    env[f"GIT_CONFIG_VALUE_{n}"] = GIT_ABBREV
    env["GIT_CONFIG_COUNT"] = str(n + 1)
    return env


@contextmanager
def rebuilt_package(root, builder, *args, git=False):
    """Run `builder` (absolute, or relative to `root`) in a temporary copy of `root`; yield the rebuilt package dir."""
    root = Path(root)
    builder = Path(builder)
    rel = builder.relative_to(root) if builder.is_absolute() else builder
    before = _tree_state(root)
    with tempfile.TemporaryDirectory(prefix="urban_rebuild_") as td:
        copy = Path(td) / root.name
        shutil.copytree(root, copy, symlinks=True, ignore=shutil.ignore_patterns(*SKIP))
        env = None
        if git:
            (copy / ".git").write_text(f"gitdir: {_git_dir(root)}\n", encoding="utf-8")
            env = _git_env(os.environ)
        cmd = [sys.executable, "-I", str(copy / rel), *(_remap(a, root, copy) for a in args)]
        proc = subprocess.run(cmd, capture_output=True, cwd=copy, env=env)
        changed = _changes(before, _tree_state(root))
        assert not changed, "rebuild wrote into the real tree:\n" + "\n".join(changed[:50])
        if proc.returncode:
            sys.stderr.write(proc.stderr.decode("utf-8", "replace")[-4000:])
            raise subprocess.CalledProcessError(proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr)
        yield copy / rel.parent
