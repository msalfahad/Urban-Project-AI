"""R8.1 — B-4 / B-5 / B-6 are now LIVE on real engine/source modules.

The R8.0 checks held vacuously while engine/source did not exist. Here they
must see files, must see imports, and must still pass. Mutation copies of a
real K1 module prove each check would fire.
"""

from __future__ import annotations

import ast
import json
import sys

import pytest

from tests.r8_0.test_r8_0_import_boundaries import (FORBIDDEN_IN_ENGINE, FORBIDDEN_IN_SOURCE, REG, ROOT, SOURCE,
                                                    _files, _hits, dependency_violations, imports_of_text)

EXPECTED_MODULES = {"engine/source/__init__.py", "engine/source/findings.py", "engine/source/observations.py",
                    "engine/source/digests.py", "engine/source/cad/__init__.py", "engine/source/cad/affine.py",
                    "engine/source/cad/kernel.py", "engine/source/cad/kernel_ocs.py",
                    "engine/source/cad/libredwg_map.py",
                    # R8.2
                    "engine/source/capability.py", "engine/source/conservation.py", "engine/source/decoder_pins.py",
                    "engine/source/realised.py", "engine/source/reconcile.py", "engine/source/cad/census.py",
                    "engine/source/cad/kernel_ezdxf.py"}


def _is_source(name):
    return name == "engine.source" or name.startswith("engine.source.")


def _rel(p):
    return str(p.relative_to(ROOT))


def test_boundary_scan_is_not_vacuous():
    files = _files(SOURCE)
    assert EXPECTED_MODULES <= {_rel(p) for p in files}
    n_imports = sum(len(imports_of_text(p.read_text(), p)) for p in files)
    assert n_imports >= 30                       # the scan really sees imports


def test_B4_live_engine_source_never_imports_qs_core_or_ingest():
    assert _hits(_files(SOURCE), FORBIDDEN_IN_SOURCE) == []


def test_B1_B3_live_engine_source_never_imports_lab_tests_mcp_or_com():
    assert _hits(_files(SOURCE), FORBIDDEN_IN_ENGINE + ("research",)) == []


def test_B5_B6_live_engine_source_dependencies_registered():
    assert dependency_violations(_files(SOURCE), json.loads(REG.read_text())) == []


def test_k1_is_stdlib_only_in_r8_1():
    """Stronger than B-5: K1 uses no third-party library at all. (R8.2: the K2 route,
    kernel_ezdxf.py, uses ezdxf by design and is covered by B-5's register instead.)"""
    std = set(sys.stdlib_module_names) | {"__future__"}
    for p in _files(SOURCE):
        if p.name == "kernel_ezdxf.py":
            continue
        for name in imports_of_text(p.read_text(), p, members=False):
            assert name.split(".")[0] in std or _is_source(name), (_rel(p), name)


def test_no_engine_claims_or_fact_policy_package():
    assert not (ROOT / "engine" / "claims").exists() and not (ROOT / "engine" / "fact_policy").exists()


def test_nothing_outside_tests_imports_engine_source_yet():
    """cad_adapter migration is R8.2+: no production consumer of K1 in R8.1."""
    engine = ROOT / "engine"
    users = [f for f in _files(engine) if SOURCE not in f.parents
             and any(_is_source(n) for n in imports_of_text(f.read_text(), f))]
    assert users == []


# ---------------------------------------------------------------- live mutations

def _mutant(tmp_path, extra_import):
    """A copy of the real kernel with one injected import, placed at its real
    package path under a temporary root so relative imports resolve alike."""
    src = (SOURCE / "cad" / "kernel.py").read_text()
    dst = tmp_path / "engine" / "source" / "cad" / "kernel.py"
    dst.parent.mkdir(parents=True)
    dst.write_text(extra_import + "\n" + src)
    return dst


@pytest.mark.parametrize("line,kind", [
    ("from engine.qs_core import quantities", "B4"),
    ("from ...qs_core import quantities", "B4"),
    ("import engine.ingest.harness", "B4"),
    ("import scipy.spatial", "FORBIDDEN"),
    ("import pandas", "NOT_IN_DEPENDENCY_REGISTER"),
    ("import requests", "FORBIDDEN"),
    ("import engine.source_coverage", "ENGINE_OUTSIDE_SOURCE"),     # prefix hole fixed in R8.1
    ("from engine import cad_adapter", "ENGINE_OUTSIDE_SOURCE"),
])
def test_live_boundary_checks_fire_on_a_mutated_real_kernel(tmp_path, monkeypatch, line, kind):
    import tests.r8_0.test_r8_0_import_boundaries as IB
    dst = _mutant(tmp_path, line)
    monkeypatch.setattr(IB, "ROOT", tmp_path)
    if kind == "B4":
        assert IB._hits([dst], FORBIDDEN_IN_SOURCE)
    else:
        bad = IB.dependency_violations([dst], json.loads(REG.read_text()))
        assert any(k == kind for _, _, k in bad), bad


# ---------------------------------------------------------------- anti-calibration (gate I)

PROJECT_TOKENS = ("ALRASHED", "AL RASHED", "AL_RASHED", "P7757", "7757", "QORTUBA", "23010", "BA-054")


def _docstring_nodes(tree):
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                out.add(id(first.value))
    return out


def test_project_names_appear_only_as_field_audit_evidence_never_in_logic():
    """engine/source may CITE which real decode verified a field (docstrings and
    FIELD_REGISTER notes). No identifier, comparison or branch may carry a
    project token, and FIELD_REGISTER itself is never read by production code."""
    for p in _files(SOURCE):
        tree = ast.parse(p.read_text())
        allowed = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "FIELD_REGISTER" for t in node.targets):
                allowed |= {id(n) for n in ast.walk(node.value)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if any(t in node.value.upper() for t in PROJECT_TOKENS):
                    assert id(node) in allowed, (_rel(p), node.lineno, node.value[:60])
            elif isinstance(node, (ast.Name, ast.Attribute)):
                ident = node.id if isinstance(node, ast.Name) else node.attr
                assert not any(t.replace(" ", "_") in ident.upper() for t in PROJECT_TOKENS), (_rel(p), ident)
        uses = [n for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "FIELD_REGISTER" and isinstance(n.ctx, ast.Load)]
        assert uses == [], (_rel(p), "FIELD_REGISTER is documentation; production logic must not read it")
