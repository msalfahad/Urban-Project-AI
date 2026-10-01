"""R8.6 §15-§16: no test may rewrite its own expected truth; the guard detects it."""

from __future__ import annotations

import importlib.util
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def guard():
    spec = importlib.util.spec_from_file_location("urban_root_conftest", ROOT / "conftest.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_the_guard_sees_a_created_a_modified_and_a_deleted_file(tmp_path):
    g = guard()
    (tmp_path / "data").mkdir()
    keep, change, drop = (tmp_path / "data" / n for n in ("keep.json", "change.json", "drop.json"))
    for p in (keep, change, drop):
        p.write_text("{}")
    before = g.truth_snapshot(tmp_path, ("data",))
    time.sleep(0.01)
    change.write_text('{"rewritten": true}')
    os.utime(change, ns=(time.time_ns(), time.time_ns()))
    drop.unlink()
    (tmp_path / "data" / "new.json").write_text("{}")
    d = g.snapshot_diff(before, g.truth_snapshot(tmp_path, ("data",)))
    assert d == {"created": [os.path.join("data", "new.json")], "deleted": [os.path.join("data", "drop.json")],
                 "modified": [os.path.join("data", "change.json")]}


def test_an_identical_rewrite_is_still_a_write(tmp_path):
    """A test that rewrites truth with the same bytes is still a test that writes truth: the next upload turns it
    into a first-run failure that repairs itself (the villa-inventory behaviour)."""
    g = guard()
    (tmp_path / "tests").mkdir()
    p = tmp_path / "tests" / "expected.json"
    p.write_text("{}")
    before = g.truth_snapshot(tmp_path, ("tests",))
    time.sleep(0.01)
    p.write_text("{}")
    assert g.snapshot_diff(before, g.truth_snapshot(tmp_path, ("tests",)))["modified"]


def test_the_guard_is_on_by_default_and_covers_the_truth_roots():
    g = guard()
    assert g.TRUTH_ROOTS == ("data", "tests")
    assert os.environ.get("URBAN_DETERMINISM_GUARD", "enforce") in ("enforce", "report", "off")


def test_the_villa_inventory_test_no_longer_writes():
    import ast
    tree = ast.parse((ROOT / "tests/test_pa09_villa_blind_inventory.py").read_text())
    calls = {f"{n.func.value.id}.{n.func.attr}" for n in ast.walk(tree) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)}
    assert "SI.finish" not in calls and "SI.scan" in calls
