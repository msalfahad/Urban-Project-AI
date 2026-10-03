"""R8.0 register integrity, donor lock and anti-calibration.

  * the fixture register holds exactly F01..F36, the mutation register
    exactly MT-01..MT-51, and every test they cite exists;
  * every expected-failure entry names a real test (no stale entries);
  * DONORS.lock pins every donor by full commit SHA with licence and status;
  * no R8.0 test logic carries a project identifier (docstrings/comments may
    describe exposure; code and data may not).
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
REG = HERE / "registers"
LOCK = ROOT / "research" / "external_engine_lab" / "DONORS.lock"
PROJECT_TOKENS = ("ALRASHED", "AL RASHED", "AL_RASHED", "P7757", "7757", "QORTUBA", "23010", "BA-054")


@lru_cache(maxsize=1)
def collected():
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider",
                          "-o", "addopts=", str(HERE)], capture_output=True, text=True, cwd=ROOT).stdout
    return {line.strip().replace("\\", "/").split("tests/r8_0/", 1)[1] for line in out.splitlines() if "::" in line}


def _load(name):
    return json.loads((REG / name).read_text())


def test_fixture_register_is_complete_and_resolves():
    fx = _load("R8_0_FIXTURE_REGISTER.json")["fixtures"]
    assert [f["id"] for f in fx] == [f"F{i:02d}" for i in range(1, 37)]
    ids = collected()
    for f in fx:
        assert f["tests"], f["id"]
        assert set(f["tests"]) <= ids, (f["id"], sorted(set(f["tests"]) - ids))


def test_mutation_register_is_complete_and_resolves():
    mt = _load("R8_0_MUTATION_REGISTER.json")["mutations"]
    assert [m["id"] for m in mt] == [f"MT-{i:02d}" for i in range(1, 52)]
    ids = collected()
    for m in mt:
        assert m["tests"], m["id"]
        assert set(m["tests"]) <= ids, (m["id"], sorted(set(m["tests"]) - ids))


def test_expected_failures_name_real_tests_and_valid_classes():
    reg = _load("R8_0_EXPECTED_FAILURES.json")
    ids = collected()
    tests = [e["test"] for e in reg["expected_failures"]]
    assert len(tests) == len(set(tests))
    assert set(tests) <= ids, sorted(set(tests) - ids)
    assert {e["class"] for e in reg["expected_failures"]} <= set(reg["classes"])


def test_known_defects_are_all_backed_by_a_fixture():
    for e in _load("R8_0_EXPECTED_FAILURES.json")["expected_failures"]:
        if e["class"] == "KNOWN_DEFECT":
            assert e.get("fixture") and e.get("defect") and e.get("reason"), e["test"]


def test_mirror_defect_reproduced_by_F02_and_F05():
    ef = _load("R8_0_EXPECTED_FAILURES.json")["expected_failures"]
    mirror = {e["test"] for e in ef if e.get("defect") in ("MIRRORED_ARC_SWEEP", "MIRRORED_BULGE_SIDE")}
    assert any("[F02_" in t for t in mirror) and any("[F05_" in t for t in mirror)


def test_exposure_register_separates_projects_and_records_correction():
    ex = _load("R8_0_EXPOSURE_CENSUS.json")
    srcs = [p["source"] for p in ex["projects"]]
    assert len(srcs) == 2 and len(set(srcs)) == 2
    assert "correction" in ex


def test_donor_lock_pins_every_donor():
    lock = json.loads(LOCK.read_text())
    repos = {d["repo"]: d for d in lock["donors"]}
    assert set(repos) == {"U-C4N/Autocad-MCP", "Kentucky-ai/opentakeoff", "beiming183-cloud/AutoCAD-MCP",
                          "puran-water/autocad-mcp", "Slacker-LLC/autocad-mcp"}
    for d in lock["donors"]:
        assert re.fullmatch(r"[0-9a-f]{40}", d["commit"]), d["repo"]
        assert d["licence"] and d["status"] and d["purpose"]
    refs = {r["repo"]: r["status"] for r in lock["references"]}
    assert refs["ahmetcemkaraca/AutoCAD_MCP"] == "REJECTED_REFERENCE"
    assert refs["vigneshpbmenon/autocad-mcp-server"] == "REJECTED_REFERENCE"
    assert refs["christiannp/autocad"] == "UNRESOLVED_EXTERNAL_REPOSITORY"
    assert refs["datadrivenconstruction/OpenConstructionERP"] == "IDEA_ONLY_AGPL"


def _code_strings_and_names(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                docs.add(id(first.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            yield node.value
        elif isinstance(node, ast.Name):
            yield node.id
        elif isinstance(node, ast.Attribute):
            yield node.attr


def test_no_project_identifier_in_r8_0_test_logic():
    hits = []
    for p in sorted(HERE.glob("*.py")):
        if p.name == "test_r8_0_registers.py":
            continue
        for s in _code_strings_and_names(p):
            if any(tok in s.upper() for tok in PROJECT_TOKENS):
                hits.append((p.name, s[:60]))
    assert hits == []


def test_no_real_source_path_in_fixture_data():
    for p in sorted(HERE.glob("*.py")):
        if p.name == "test_r8_0_registers.py":
            continue
        for s in _code_strings_and_names(p):
            assert "data/runs" not in s and "data/golden" not in s, (p.name, s)
