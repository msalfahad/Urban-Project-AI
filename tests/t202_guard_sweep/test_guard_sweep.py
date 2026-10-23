"""T-202 guard sweep and known-failures ledger.

Sweep: every engine/ and tools/ .py module touched by the working branch's first-parent history in the fixed window
15fd9132..d699b650 (2026-10-22 00:00 .. 2026-10-23 07:00 UTC) has a registry state read from the registry file and a
default-guard class; the module set is re-derived here independently (one aggregate `git diff --name-only` over the
window, not the per-merge walk the sweep uses). Adverse: an undeclared rebar-naming engine module, an unclassified
module and a non-merge commit in the window are each reported as a problem (never passed silently).

Ledger: the committed ledger is well formed; the check splits a synthetic pytest output into NEW / KNOWN / ABSENT and
exits 1 only on NEW; parametrised ids and collection errors are read; a duplicate ledger id is refused."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t202"
sys.path.insert(0, str(HERE))

import guard_sweep as GS        # noqa: E402
import known_failures as KF     # noqa: E402


def _git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], check=True, capture_output=True, text=True).stdout


@pytest.fixture(scope="module")
def swept():
    return GS.sweep()


def test_window_is_complete_and_clean(swept):
    rows, problems = swept
    assert problems == []
    agg = {p for p in _git("diff", "--name-only", "--no-renames", GS.BASE, GS.HEAD, "--", "engine/", "tools/").split()
           if p.endswith(".py")}
    assert {r["path"] for r in rows} == agg
    assert len(rows) == 22


def test_every_row_has_a_guard_class_and_a_registry_state(swept):
    rows, _ = swept
    reg = GS.registry()
    for r in rows:
        assert r["guard"] in GS.CLASSES and r["guard_why"]
        if r["path"] in reg:
            assert r["registry"] == reg[r["path"]]
        elif r["path"].startswith("engine/"):
            assert not r["names_rebar"]          # an engine module naming rebar must be declared


def test_guard_host_and_unwired_producers(swept):
    rows = {r["path"]: r for r in swept[0]}
    assert rows["engine/source/arch_v306.py"]["guard"] == GS.GUARD_HOST
    assert "engine/source/arch_v306.py" in rows["engine/source/default_guard.py"]["importers"]
    for p in ("engine/source/masonry_centreline_v2.py", "engine/source/opening_scope_v1.py",
              "engine/source/stair_rule_calculator.py"):
        assert rows[p]["guard"] == GS.UNWIRED_PRODUCER and rows[p]["importers"] == []
    assert rows["engine/source/default_guard.py"]["registry"] == "OTHER_REBAR_AWARE"


def test_adverse_undeclared_rebar_module_is_a_problem(monkeypatch):
    real = GS.names_rebar
    monkeypatch.setattr(GS, "names_rebar", lambda p: True if p.endswith("scope_crosswalk_v1.py") else real(p))
    _, problems = GS.sweep()
    assert any("scope_crosswalk_v1.py: names reinforcement and is not declared" in p for p in problems)


def test_adverse_unclassified_module_is_a_problem(monkeypatch):
    g = dict(GS.GUARD)
    del g["engine/source/level_chain_v1.py"]
    monkeypatch.setattr(GS, "GUARD", g)
    _, problems = GS.sweep()
    assert any("level_chain_v1.py: no default-guard classification" in p for p in problems)


def test_adverse_non_merge_commit_in_window_is_a_problem(monkeypatch):
    real = GS.window
    monkeypatch.setattr(GS, "window", lambda b, h: real(b, h) + [("f" * 40, "2026-10-23T08:00:00+00:00", "direct",
                                                                   False, [("M", "engine/source/arch_v306.py")])])
    _, problems = GS.sweep()
    assert any(p.startswith("non-merge first-parent commit ffffffff") for p in problems)


def test_markdown_lists_every_module(swept):
    md = GS.markdown(swept[0])
    assert md.count("\n| ") == 22 + 1          # header row + one row per module (separator starts with |---)


# ------------------------------------------------------------------------------------------------ known failures
def test_committed_ledger_is_well_formed():
    doc = KF.load_ledger()
    assert doc["head"] and doc["failures"]
    for e in doc["failures"]:
        assert e["kind"] in ("FAILED", "ERROR") and "::" in e["id"]


SYNTH = """....F..
=========================== short test summary info ============================
FAILED tests/a/test_x.py::test_known - AssertionError: 1 != 2
FAILED tests/a/test_x.py::test_param[case-1.5] - ValueError
ERROR tests/b/test_y.py - ModuleNotFoundError: No module named 'fitz'
2 failed, 1 error, 40 passed in 1.00s
"""


def _ledger(tmp_path, ids):
    p = tmp_path / "l.json"
    p.write_text(json.dumps({"schema": "URBAN_KNOWN_FAILURES_V1", "head": "x", "failures": [
        {"id": i, "kind": "FAILED", "first_failing": "abc", "cause": "c", "owner": "o"} for i in ids]}))
    return p


def test_check_splits_new_known_absent(tmp_path):
    out = tmp_path / "run.txt"
    out.write_text(SYNTH)
    led = _ledger(tmp_path, ["tests/a/test_x.py::test_known", "tests/c/test_z.py::test_gone"])
    failing = KF.parse(SYNTH)
    assert failing == {"tests/a/test_x.py::test_known": "FAILED", "tests/a/test_x.py::test_param[case-1.5]": "FAILED",
                       "tests/b/test_y.py": "ERROR"}
    new, hit, absent = KF.compare(failing, KF.load_ledger(led))
    assert new == ["tests/a/test_x.py::test_param[case-1.5]", "tests/b/test_y.py"]
    assert [e["id"] for e in hit] == ["tests/a/test_x.py::test_known"]
    assert absent == ["tests/c/test_z.py::test_gone"]
    assert KF.main(["check", str(out), "--ledger", str(led)]) == 1


def test_check_exits_0_when_every_failure_is_known(tmp_path):
    out = tmp_path / "run.txt"
    out.write_text(SYNTH)
    led = _ledger(tmp_path, ["tests/a/test_x.py::test_known", "tests/a/test_x.py::test_param[case-1.5]",
                             "tests/b/test_y.py"])
    assert KF.main(["check", str(out), "--ledger", str(led)]) == 0


def test_adverse_duplicate_or_incomplete_ledger_refused(tmp_path):
    with pytest.raises(ValueError):
        KF.load_ledger(_ledger(tmp_path, ["tests/a.py::t", "tests/a.py::t"]))
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"schema": "URBAN_KNOWN_FAILURES_V1", "failures": [
        {"id": "tests/a.py::t", "kind": "FAILED", "first_failing": "", "cause": "c", "owner": "o"}]}))
    with pytest.raises(ValueError):
        KF.load_ledger(p)
