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


@contextmanager
def rebuilt_package(root, builder, *args):
    """Run `builder` (absolute, or relative to `root`) in a temporary copy of `root`; yield the rebuilt package dir."""
    root = Path(root)
    builder = Path(builder)
    rel = builder.relative_to(root) if builder.is_absolute() else builder
    before = _tree_state(root)
    with tempfile.TemporaryDirectory(prefix="urban_rebuild_") as td:
        copy = Path(td) / root.name
        shutil.copytree(root, copy, symlinks=True, ignore=shutil.ignore_patterns(*SKIP))
        cmd = [sys.executable, "-I", str(copy / rel), *(_remap(a, root, copy) for a in args)]
        proc = subprocess.run(cmd, capture_output=True, cwd=copy)
        changed = _changes(before, _tree_state(root))
        assert not changed, "rebuild wrote into the real tree:\n" + "\n".join(changed[:50])
        if proc.returncode:
            sys.stderr.write(proc.stderr.decode("utf-8", "replace")[-4000:])
            raise subprocess.CalledProcessError(proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr)
        yield copy / rel.parent
