"""Phase 2B-5 (ARCH_TAKEOFF_V2.6): the expected values do not come from the implementation being tested. The
generalised reference calculator imports only the Phase 2B-4 calculator and the standard library; the case file
imports nothing and holds its expected values as typed literals; only install_engine.py reaches the engine, and it
holds no expected value."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import install_cases as IC                                    # noqa: E402


def _imports(path):
    out = set()
    for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Import):
            out |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            out.add(n.module or "")
    return out


def test_the_reference_imports_no_engine_and_the_cases_import_nothing():
    assert _imports(HERE / "install_reference.py") <= {"__future__", "itertools", "sys", "collections", "pathlib",
                                                       "construct_reference"}
    assert _imports(HERE.parent / "m9_p2b4" / "construct_reference.py") <= {"__future__", "itertools", "collections"}
    assert _imports(HERE / "install_cases.py") == set()


def test_only_the_adapter_reaches_the_engine():
    """of the library modules (the tests aside), only the adapter imports the engine."""
    for p in HERE.glob("*.py"):
        if p.name.startswith("test_"):
            continue
        uses = any(m.startswith("engine") for m in _imports(p))
        assert uses == (p.name == "install_engine.py"), p.name


def _literal(node):
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple)):
        return all(_literal(e) for e in node.elts)
    if isinstance(node, ast.Dict):
        return all(isinstance(k, ast.Constant) for k in node.keys) and all(_literal(v) for v in node.values)
    return False


def test_every_expected_value_is_a_typed_literal():
    tree = ast.parse((HERE / "install_cases.py").read_text(encoding="utf-8"))
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value == "expected":
                    assert _literal(v), f"expected values must be literals (line {v.lineno})"
                    n += 1
    assert n == len(IC.EXAMPLES) == 10


def test_every_example_carries_the_whole_verification_chain():
    for ex in IC.EXAMPLES:
        for k in ("rules", "interpretation", "formula", "hand", "expected", "boq_impact"):
            assert ex.get(k), f"{ex['id']} has no {k}"
        assert ex.get("room") or ex.get("areas"), ex["id"]
