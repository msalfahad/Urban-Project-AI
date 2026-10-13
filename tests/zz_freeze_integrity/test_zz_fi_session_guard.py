"""P2-00 Stage 1 - the immutable baseline of this repository. The folder is named zz_ so that, in a full session, these
tests run after every other test: a test that rewrote a frozen output or manifest in place (finding F-1) fails here.

The root conftest determinism guard watches data/ and tests/ only; this guard covers the frozen research artefacts:
every freeze manifest, every non-code research file a manifest pins, the V1 synthetic snapshot and the owner rule
files, against research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl (append-only, hash-chained)."""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import freeze_verify as FV              # noqa: E402

D = ROOT / "research" / "freeze_integrity"
INDEX, LOCK = D / "FREEZE_BASELINE_INDEX.jsonl", D / "ENVIRONMENT_LOCK.json"
REGISTERS = {D / "ERRATA.jsonl": ("id", "release", "defect", "evidence", "effect_on_frozen_outputs", "corrected_in", "status"),
             D / "ENGINEERING_FINDINGS.jsonl": ("id", "kind", "title", "evidence", "mitigation", "status")}
GIT = (ROOT / ".git").exists() and subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                                  capture_output=True).returncode == 0
needs_git = pytest.mark.skipif(not GIT, reason="prerequisite: the git history")
PATTERN = re.compile("YEARS" + " 2013|7757-[A-Z]|[؀-ۿ]{3,}|(?i:als[ey]?n[ya]?an)")      # the S6 hygiene rule


def _rel(p):
    return str(p.relative_to(ROOT))


def test_every_frozen_artefact_matches_the_baseline_index():
    bad = FV.check_index(ROOT, INDEX)
    assert not bad, "frozen artefacts changed (restore them with git checkout; never re-freeze in place): " + \
        "; ".join(f"{p} {h[:12]} -> {(now or 'missing')[:12]}" for p, h, now in bad[:20])


def test_index_is_a_valid_chain_and_append_only_over_history():
    entries = FV.read_chain(INDEX)
    assert entries and {e["kind"] for e in entries} == {"FREEZE_MANIFEST", "BASELINE"}
    assert len({e["path"] for e in entries}) == len(entries)
    if GIT:
        assert FV.append_only_history(ROOT, _rel(INDEX)) == []


@needs_git
def test_every_committed_freeze_manifest_is_indexed():
    indexed = {e["path"] for e in FV.read_chain(INDEX)}
    missing = sorted({m["path"] for m in FV.manifests(ROOT, "HEAD")} - indexed)
    assert not missing, f"index the new freeze (tools/freeze_verify.py index --write ...): {missing}"


def test_registers_are_append_only_with_unique_ids_and_required_fields():
    for path, fields in REGISTERS.items():
        entries = FV.read_chain(path)
        assert entries
        ids = [e["id"] for e in entries]
        assert len(ids) == len(set(ids)), path.name
        for e in entries:
            assert all(e.get(f) for f in fields), (path.name, e.get("id"))
        if GIT:
            assert FV.append_only_history(ROOT, _rel(path)) == [], path.name


def test_environment_lock_is_well_formed_and_enforced_when_required():
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert lock["schema"] == FV.LOCK_SCHEMA
    assert lock["python"] == {"implementation": "CPython", "version": "3.11.17"}          # owner decision D5
    assert {"ezdxf", "numpy", "shapely", "openpyxl", "pytest"} <= set(lock["packages"])
    assert all(isinstance(v, str) and v for v in lock["packages"].values())
    if os.environ.get("URBAN_REQUIRE_LOCK_ENV") == "1":
        st = FV.env_status(lock, FV.current_env())
        assert st["in_lock"], st


def test_the_verifier_is_stdlib_only_and_nothing_in_production_imports_it():
    tree = ast.parse((ROOT / "tools" / "freeze_verify.py").read_text(encoding="utf-8"))
    mods = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | \
        {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert mods <= {"__future__", "argparse", "ast", "hashlib", "json", "os", "re", "shutil", "subprocess", "sys",
                    "tempfile", "xml", "pathlib"}, mods
    for base in ("engine", "tools", "agents", "pipeline"):
        for f in (ROOT / base).rglob("*.py"):
            if f.name != "freeze_verify.py" and "__pycache__" not in f.parts:
                assert "freeze_verify" not in f.read_text(encoding="utf-8", errors="replace"), _rel(f)


def test_the_stage1_notes_carry_no_identity():
    for p in sorted(D.glob("*")):
        if p.suffix in (".md", ".diff") or p.name in ("ERRATA.jsonl", "ENGINEERING_FINDINGS.jsonl"):
            hit = PATTERN.search(p.read_text(encoding="utf-8", errors="replace"))
            assert hit is None, (p.name, hit.group(0))
