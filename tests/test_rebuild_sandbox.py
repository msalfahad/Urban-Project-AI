"""T-020: the rebuild sandbox never writes into the real tree, and a byte mismatch fails without overwriting.

Synthetic repository in tmp_path: research/pkg/build.py writes OUT.json from an input under research/src/ and,
optionally, from a path argument. Hand truth: the committed OUT.json is b'{"v": 1}\\n'.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.rebuild_sandbox import rebuilt_package

COMMITTED = b'{"v": 1}\n'
BUILDER = '''
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
v = (ROOT / "research" / "src" / "value.txt").read_text().strip()
if v == "fail":
    sys.exit("input missing")
if len(sys.argv) > 1 and sys.argv[1].startswith("LEAK="):
    Path(sys.argv[1][5:]).write_text("leaked\\n")             # adversarial: absolute path the sandbox cannot see
elif len(sys.argv) > 1:
    arg = Path(sys.argv[1])
    v = arg.read_text().strip()
    arg.write_text("touched by the builder\\n")           # adversarial: writes through its argument
    str(arg.relative_to(ROOT))                             # raises if the argument was not re-pointed
(HERE / "OUT.json").write_text('{"v": %s}\\n' % v)
(ROOT / "research" / "src" / "side.txt").write_text("x")  # adversarial: writes outside its package
'''


def make_repo(tmp_path: Path, value: str) -> Path:
    root = tmp_path / "repo"
    (root / "research" / "pkg").mkdir(parents=True)
    (root / "research" / "src").mkdir(parents=True)
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_text("ref: refs/heads/x\n")
    (root / "research" / "pkg" / "build.py").write_text(BUILDER)
    (root / "research" / "pkg" / "OUT.json").write_bytes(COMMITTED)
    (root / "research" / "src" / "value.txt").write_text(value + "\n")
    return root


def state(root: Path) -> dict:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_identical_rebuild_passes_and_real_tree_untouched(tmp_path):
    root = make_repo(tmp_path, "1")
    before = state(root)
    with rebuilt_package(root, "research/pkg/build.py") as out:
        assert (out / "OUT.json").read_bytes() == COMMITTED
        assert (out.parents[1] / "research" / "src" / "side.txt").exists()   # the side write stayed in the copy
        assert out != root / "research" / "pkg"
    assert state(root) == before
    assert not out.exists()                                          # the copy is deleted on exit


def test_mismatch_is_reported_and_committed_bytes_survive(tmp_path):
    root = make_repo(tmp_path, "2")                                  # rebuild gives {"v": 2}: one-ulp stand-in
    before = state(root)
    with rebuilt_package(root, root / "research" / "pkg" / "build.py") as out:
        assert (out / "OUT.json").read_bytes() == b'{"v": 2}\n' != COMMITTED
    assert state(root) == before
    assert (root / "research" / "pkg" / "OUT.json").read_bytes() == COMMITTED


def test_path_argument_inside_root_is_repointed_into_the_copy(tmp_path):
    root = make_repo(tmp_path, "1")
    arg = root / "research" / "src" / "value.txt"
    before = state(root)
    with rebuilt_package(root, "research/pkg/build.py", str(arg)) as out:
        assert (out / "OUT.json").read_bytes() == COMMITTED
    assert state(root) == before


def test_builder_failure_raises_called_process_error_and_writes_nothing(tmp_path):
    root = make_repo(tmp_path, "fail")
    before = state(root)
    with pytest.raises(subprocess.CalledProcessError):
        with rebuilt_package(root, "research/pkg/build.py"):
            pass
    assert state(root) == before


def test_git_and_caches_are_not_copied(tmp_path):
    root = make_repo(tmp_path, "1")
    (root / "research" / "pkg" / "__pycache__").mkdir()
    (root / "research" / "pkg" / "__pycache__" / "x.pyc").write_bytes(b"\0")
    with rebuilt_package(root, "research/pkg/build.py") as out:
        copy = out.parents[1]
        assert not (copy / ".git").exists()
        assert not (out / "__pycache__" / "x.pyc").exists()


def test_a_write_that_escapes_the_copy_fails_the_test(tmp_path):
    root = make_repo(tmp_path, "1")
    target = root / "research" / "pkg" / "OUT.json"
    with pytest.raises(AssertionError, match="rebuild wrote into the real tree"):
        with rebuilt_package(root, "research/pkg/build.py", "LEAK=" + str(target)):
            pass
