"""M9 S6 Phase 1 - the committed notes, tests and new modules carry no drawing identity, no client figure and no
benchmark value; engine/source stays stdlib-only and project-agnostic."""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = [p for p in (ROOT / "research" / "urban_m9_s6" / "phase1").rglob("*") if p.is_file()]
TESTS = [p for p in (ROOT / "tests" / "m9_s6").rglob("*") if p.is_file() and "__pycache__" not in p.parts
         and p.name != Path(__file__).name]
SOURCES = [ROOT / "engine" / "source" / n for n in ("discovery.py", "arch_completeness.py", "opening_gaps.py")] + \
    [ROOT / "tools" / "arch_discovery.py"]
PATTERN = re.compile("YEARS 2013|7757-[A-Z]|[\u0600-\u06FF]{3,}|(?i:als[ey]?n[ya]?an)")   # the package hygiene rule


def test_notes_and_tests_carry_no_identity():
    assert DOCS, "the phase 1 notes are committed"
    for p in DOCS + TESTS + SOURCES:
        text = p.read_text(encoding="utf-8", errors="replace")
        hit = PATTERN.search(text)
        assert hit is None, f"{p.relative_to(ROOT)}: {hit.group(0)!r}"


def test_engine_modules_are_stdlib_only():
    for name in ("discovery.py", "arch_completeness.py", "opening_gaps.py"):
        tree = ast.parse((ROOT / "engine" / "source" / name).read_text(encoding="utf-8"))
        mods = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | \
            {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        assert mods <= {"__future__", "math", "re", "collections", "engine"}, (name, mods)
