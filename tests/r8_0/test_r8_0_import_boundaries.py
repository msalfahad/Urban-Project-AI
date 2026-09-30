"""R8.0 import boundaries (R8.0 brief §14, §21, §22; MT-47, MT-48).

Static AST scan of every .py file under engine/. Nothing is imported or run.

  B-1  engine/ never imports research.external_engine_lab
  B-2  engine/ never imports tests (the R8.0 oracles and realiser live there)
  B-3  engine/ never imports an MCP server, donor engine or live-AutoCAD COM
  B-4  engine/source never imports engine.qs_core or engine.ingest (source is upstream)
  B-5  engine/source imports only libraries in the source dependency register (MT-47)
  B-6  engine/source never imports scipy (MT-48)
  B-7  BOUNDARY DEBT: two pre-existing engine -> research.a21 imports are frozen
       by name; no new engine -> research import may appear, and the debt is
       tracked until retired (never 'fixed' silently by this round).
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "engine"
SOURCE = ENGINE / "source"
REG = Path(__file__).parent / "registers" / "R8_0_SOURCE_DEPENDENCY_REGISTER.json"

FORBIDDEN_IN_ENGINE = ("research.external_engine_lab", "tests", "mcp", "fastmcp", "autocad_mcp",
                       "autocad_mcp_pro", "opentakeoff", "win32com", "pythoncom", "comtypes")
FORBIDDEN_IN_SOURCE = ("engine.qs_core", "engine.ingest")

# B-7: frozen on 2026-09-30; see 09_IMPORT_BOUNDARIES.md
RESEARCH_IMPORT_DEBT = {
    ("engine/plaster_trade_engine.py", "research.a21_trace_sufficiency_01.parameters"),
    ("engine/wall_treatment_engine.py", "research.a21_trace_sufficiency_01.parameters"),
}


def imports_of_text(text, module_path=None, members=True):
    """Absolute module names imported by one file (relative imports resolved)."""
    tree = ast.parse(text)
    pkg = None
    if module_path is not None:
        rel = module_path.relative_to(ROOT).with_suffix("")
        parts = list(rel.parts)
        pkg = parts[:-1] if parts[-1] != "__init__" else parts[:-1]
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level and pkg is not None:
                base = pkg[: len(pkg) - (node.level - 1)] if node.level > 1 else pkg
                name = ".".join(base + ([node.module] if node.module else []))
            else:
                name = node.module or ""
            out.add(name)
            if members:
                for a in node.names:
                    out.add(f"{name}.{a.name}")
    return out


def _files(root):
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def _hits(files, prefixes, members=True):
    found = []
    for f in files:
        for name in imports_of_text(f.read_text(encoding="utf-8"), f, members):
            if any(name == p or name.startswith(p + ".") for p in prefixes):
                found.append((str(f.relative_to(ROOT)), name))
    return sorted(set(found))


def _top(name):
    return name.split(".")[0]


def dependency_violations(files, register):
    allowed = set(register["third_party_allowed"])
    forbidden = set(register["forbidden"])
    std = set(sys.stdlib_module_names)
    bad = []
    for f in files:
        for name in imports_of_text(f.read_text(encoding="utf-8"), f):
            top = _top(name)
            if top in forbidden:
                bad.append((str(f.relative_to(ROOT)), name, "FORBIDDEN"))
            elif name == "engine.source" or name.startswith("engine.source.") or top in std or top in allowed or top == "__future__":
                continue
            elif top == "engine":
                bad.append((str(f.relative_to(ROOT)), name, "ENGINE_OUTSIDE_SOURCE"))
            else:
                bad.append((str(f.relative_to(ROOT)), name, "NOT_IN_DEPENDENCY_REGISTER"))
    return sorted(set(bad))


# ------------------------------------------------------------------ B-1..B-3

def test_B1_B2_B3_engine_never_imports_lab_tests_mcp_or_donor_engines():
    assert _hits(_files(ENGINE), FORBIDDEN_IN_ENGINE) == []


def test_B4_engine_source_is_upstream_of_qs_core_and_ingest():
    files = _files(SOURCE) if SOURCE.exists() else []
    assert _hits(files, FORBIDDEN_IN_SOURCE) == []


def test_B4_engine_source_status_recorded():
    """engine/source does not exist yet in R8.0; B-4..B-6 hold vacuously and
    become live the moment the first module is written."""
    assert not SOURCE.exists() or any(SOURCE.rglob("*.py"))


def test_B5_B6_engine_source_dependencies_registered():
    files = _files(SOURCE) if SOURCE.exists() else []
    assert dependency_violations(files, json.loads(REG.read_text())) == []


# ---------------------------------------------------------------------- B-7

def test_B7_research_import_debt_is_frozen():
    found = set(_hits(_files(ENGINE), ("research",), members=False))
    assert found == RESEARCH_IMPORT_DEBT, f"new: {sorted(found - RESEARCH_IMPORT_DEBT)} retired: {sorted(RESEARCH_IMPORT_DEBT - found)}"


def test_B7_engine_imports_nothing_from_research():
    """The goal state. Fails today on the two frozen debt imports."""
    assert _hits(_files(ENGINE), ("research",)) == []


# ------------------------------------------------ checker sensitivity (MT-47/48)

def _violations_for(text):
    f = SOURCE / "cad" / "_probe.py"
    reg = json.loads(REG.read_text())
    std = set(sys.stdlib_module_names)
    bad = []
    for name in imports_of_text(text, f):
        top = _top(name)
        if top in reg["forbidden"]:
            bad.append((name, "FORBIDDEN"))
        elif name == "engine.source" or name.startswith("engine.source.") or top in std or top in reg["third_party_allowed"] or top == "__future__":
            continue
        elif top == "engine":
            bad.append((name, "ENGINE_OUTSIDE_SOURCE"))
        else:
            bad.append((name, "NOT_IN_DEPENDENCY_REGISTER"))
    return bad


def test_MT47_unregistered_library_is_caught():
    assert ("pandas", "NOT_IN_DEPENDENCY_REGISTER") in _violations_for("import pandas\n")


def test_MT48_scipy_is_caught():
    assert _violations_for("from scipy.spatial import cKDTree\n")[0][1] == "FORBIDDEN"


def test_MT_B4_source_importing_qs_core_is_caught():
    assert ("engine.qs_core.evidence", "ENGINE_OUTSIDE_SOURCE") in _violations_for("from engine.qs_core.evidence import Claim\n")


def test_MT_B4_relative_escape_is_caught():
    """`from ...qs_core import x` inside engine/source/cad resolves to engine.qs_core."""
    names = imports_of_text("from ...qs_core import evidence\n", SOURCE / "cad" / "_probe.py")
    assert "engine.qs_core" in names


def test_MT_B1_lab_import_is_caught():
    names = imports_of_text("from research.external_engine_lab.adapters import x\n")
    assert any(n.startswith("research.external_engine_lab") for n in names)
