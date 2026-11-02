"""T-462 (owner D1 2026-11-02): private project inputs SKIP when absent, never fail, never hide a defect.

Synthetic, not the training villa: every case builds its own tiny tree under tmp_path. Normal cases (a present private
file is returned and its test runs; an absent one skips with the owner's reason) and adverse cases (a public path cannot
be declared skippable; a missing file outside the declared roots, a present file that fails, any other exception and the
strict mode on the private machine all stay FAILED).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests import _private_inputs as PI

HERE = Path(__file__).resolve().parent
TESTS = HERE.parent


# ------------------------------------------------------------------ what counts as private
def test_private_roots_are_git_ignored_data_or_outside_the_repository(tmp_path):
    assert PI.private_root("data/experiments/X", tmp_path) == tmp_path / "data/experiments/X"
    assert PI.private_root("data/inputs/by_sha256/abc.dxf", tmp_path) == tmp_path / "data/inputs/by_sha256/abc.dxf"
    outside = tmp_path.parent / "elsewhere" / "upload.pdf"
    assert PI.private_root(outside, tmp_path) == outside


@pytest.mark.parametrize("public", ["engine/arch_v30.py", "tests/t061_room_label_guard", "research/x.json", "data",
                                    "data/registry", "data/registry/space_aliases.json", "data/trade_rules/x.json",
                                    "data/../engine/x.py"])
def test_a_public_path_can_never_be_declared_private(tmp_path, public):
    with pytest.raises(ValueError):
        PI.private_root(public, tmp_path)


def test_the_public_data_subtrees_are_the_ones_gitignore_re_includes():
    gi = (PI.ROOT / ".gitignore").read_text("utf-8")
    assert "/data/*" in gi
    for pub in PI.PUBLIC_DATA:
        assert f"!/{pub}/" in gi, pub


# ------------------------------------------------------------------ require_private
def test_a_present_private_file_is_returned_and_nothing_skips(tmp_path):
    f = tmp_path / "data/inputs/by_sha256/a.dxf"
    f.parent.mkdir(parents=True)
    f.write_text("0\nEOF\n")
    assert PI.require_private("data/inputs/by_sha256/a.dxf", root=tmp_path) == f
    g = tmp_path / "data/inputs/by_sha256/b.pdf"
    g.write_text("%PDF")
    assert PI.require_private("data/inputs/by_sha256/a.dxf", g, root=tmp_path) == [f, g]


def test_an_absent_private_file_skips_with_the_owner_reason(tmp_path, monkeypatch):
    monkeypatch.delenv(PI.STRICT_ENV, raising=False)
    with pytest.raises(pytest.skip.Exception) as e:
        PI.require_private("data/inputs/by_sha256/a.dxf", root=tmp_path)
    assert str(e.value.msg) == "private data not available: data/inputs/by_sha256/a.dxf"


def test_one_absent_file_of_several_is_named(tmp_path, monkeypatch):
    monkeypatch.delenv(PI.STRICT_ENV, raising=False)
    (tmp_path / "data/x").mkdir(parents=True)
    (tmp_path / "data/x/here.json").write_text("{}")
    with pytest.raises(pytest.skip.Exception) as e:
        PI.require_private("data/x/here.json", "data/x/gone.json", root=tmp_path)
    assert e.value.msg == "private data not available: data/x/gone.json"


def test_strict_mode_fails_instead_of_skipping(tmp_path, monkeypatch):
    monkeypatch.setenv(PI.STRICT_ENV, "require")
    with pytest.raises(pytest.fail.Exception) as e:
        PI.require_private("data/x/gone.json", root=tmp_path)
    assert "private data required but not available: data/x/gone.json" in str(e.value)


def test_require_private_refuses_a_public_path_even_when_it_is_missing(tmp_path):
    with pytest.raises(ValueError):
        PI.require_private("research/never_written.json", root=tmp_path)
    with pytest.raises(ValueError):
        PI.require_private(root=tmp_path)


# ------------------------------------------------------------------ the FileNotFoundError rule
def _fnf(path):
    return FileNotFoundError(2, "No such file or directory", str(path))


def test_absent_file_under_a_declared_root_is_recognised(tmp_path):
    roots = (tmp_path / "data/experiments/E",)
    assert PI.absent_private_file(_fnf("data/experiments/E/a/b.json"), roots, cwd=tmp_path, root=tmp_path) == \
        "data/experiments/E/a/b.json"
    assert PI.absent_private_file(_fnf(tmp_path / "data/experiments/E"), roots, cwd=tmp_path, root=tmp_path) == \
        "data/experiments/E"


def test_a_wrapped_missing_file_is_followed_through_the_cause_chain(tmp_path):
    roots = (tmp_path / "data/runs",)
    try:
        try:
            raise _fnf("data/runs/7/r.json")
        except FileNotFoundError as inner:
            raise RuntimeError("builder stopped") from inner
    except RuntimeError as outer:
        assert PI.absent_private_file(outer, roots, cwd=tmp_path, root=tmp_path) == "data/runs/7/r.json"


@pytest.mark.parametrize("make", [
    lambda t: _fnf("data/experiments/OTHER/x.json"),          # outside the declared root
    lambda t: _fnf("research/missing_public.json"),             # a missing PUBLIC file is a defect
    lambda t: _fnf("data/experiments/E_sibling/x.json"),        # prefix of the root name is not inside it
    lambda t: AssertionError("data/experiments/E/x.json"),      # any other exception
    lambda t: FileNotFoundError("no filename attribute"),
])
def test_everything_else_stays_a_failure(tmp_path, make):
    roots = (tmp_path / "data/experiments/E",)
    assert PI.absent_private_file(make(tmp_path), roots, cwd=tmp_path, root=tmp_path) is None


def test_a_file_that_exists_after_the_failure_was_not_the_cause(tmp_path):
    f = tmp_path / "data/experiments/E/x.json"
    f.parent.mkdir(parents=True)
    f.write_text("{}")
    assert PI.absent_private_file(_fnf(f), (tmp_path / "data/experiments/E",), cwd=tmp_path, root=tmp_path) is None


def test_no_declaration_means_no_conversion(tmp_path):
    assert PI.absent_private_file(_fnf("data/experiments/E/x.json"), (), cwd=tmp_path, root=tmp_path) is None


# ------------------------------------------------------------------ end to end through tests/conftest.py
SAMPLE = '''
import json
from pathlib import Path
from tests._private_inputs import require_private

PRIVATE_INPUTS = ("data/experiments/E",)

def test_reads_absent_private():
    json.loads(Path("data/experiments/E/r.json").read_text())

def test_reads_present_private_and_fails():
    assert json.loads(Path("data/experiments/E/here.json").read_text()) == {"ok": False}

def test_reads_present_private_and_passes():
    assert json.loads(Path("data/experiments/E/here.json").read_text()) == {"ok": True}

def test_missing_public_file():
    Path("research/gone.json").read_text()

def test_missing_private_outside_root():
    Path("data/experiments/OTHER/x.json").read_text()

def test_other_error():
    raise KeyError("data/experiments/E/r.json")

def test_explicit_require():
    require_private("data/inputs/by_sha256/abc.dxf")
'''


def _run(tmp_path, env_extra=None, sample=SAMPLE):
    proj = tmp_path / "proj"
    (proj / "tests").mkdir(parents=True)
    for f in ("__init__.py", "conftest.py", "_private_inputs.py"):
        shutil.copy(TESTS / f, proj / "tests" / f)
    (proj / ".gitignore").write_text("/data/*\n!/data/trade_rules/\n!/data/registry/\n")
    (proj / "data/experiments/E").mkdir(parents=True)
    (proj / "data/experiments/E/here.json").write_text('{"ok": true}')
    (proj / "tests" / "test_sample.py").write_text(sample)
    env = {k: v for k, v in os.environ.items() if k != PI.STRICT_ENV}
    env.update(env_extra or {})
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    p = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-rA", "-o", "addopts=",
                        "tests/test_sample.py"], cwd=proj, env=env, capture_output=True, text=True, timeout=120)
    out = p.stdout + p.stderr
    res = {}
    for line in out.splitlines():
        for word in ("PASSED", "FAILED", "SKIPPED", "ERROR"):
            if line.startswith(word + " "):
                rest = line[len(word) + 1:]
                if word == "SKIPPED":  # "SKIPPED [1] tests/test_sample.py:9: reason"
                    res.setdefault("SKIPPED", []).append(rest)
                else:
                    res[rest.split(" - ")[0].split("::")[-1]] = word
    return res, out


def test_end_to_end_only_absent_declared_private_files_skip(tmp_path):
    res, out = _run(tmp_path)
    assert res.get("test_reads_present_private_and_fails") == "FAILED", out
    assert res.get("test_reads_present_private_and_passes") == "PASSED", out
    assert res.get("test_missing_public_file") == "FAILED", out
    assert res.get("test_missing_private_outside_root") == "FAILED", out
    assert res.get("test_other_error") == "FAILED", out
    skipped = res.get("SKIPPED", [])
    assert len(skipped) == 2, out
    assert any("private data not available: data/experiments/E/r.json" in s for s in skipped), out
    assert any("private data not available: data/inputs/by_sha256/abc.dxf" in s for s in skipped), out
    assert "PRIVATE INPUTS: 1 test phase(s) skipped" in out, out


def test_end_to_end_strict_mode_turns_every_skip_into_a_failure(tmp_path):
    res, out = _run(tmp_path, {PI.STRICT_ENV: "require"})
    assert "SKIPPED" not in res, out
    assert res.get("test_reads_absent_private") == "FAILED", out
    assert res.get("test_explicit_require") == "FAILED", out
    assert "private data required but not available: data/experiments/E/r.json" in out, out


def test_end_to_end_a_public_declaration_stops_the_run(tmp_path):
    bad = SAMPLE.replace('PRIVATE_INPUTS = ("data/experiments/E",)', 'PRIVATE_INPUTS = ("engine",)')
    res, out = _run(tmp_path, sample=bad)
    assert "PRIVATE_INPUTS" in out and "not a private input" in out, out
    assert "PASSED" not in res.values(), out


def test_end_to_end_a_private_fixture_read_skips_in_setup(tmp_path):
    sample = SAMPLE + '''
import pytest

@pytest.fixture
def reg():
    return json.loads(Path("data/experiments/E/fixture.json").read_text())

def test_uses_fixture(reg):
    assert reg
'''
    res, out = _run(tmp_path, sample=sample)
    assert sum("data/experiments/E/fixture.json" in s for s in res.get("SKIPPED", [])) == 1, out
    assert "ERROR" not in res.values(), out
