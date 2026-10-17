"""Phase 2A acceptance: the blind-test scorer (research/urban_m9_p2a_acceptance/blind_test, protocol URBAN_BLIND_V1)
is proven on the synthetic villa before any blind drawing exists - each injected fault is reported exactly once, in
its own category, and no percentage claim is allowed from one project."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("ezdxf")

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "research/urban_m9_p2a_acceptance/blind_test"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def dry():
    return _load("dry_run").run()


def test_every_injected_fault_is_detected_in_its_own_category(dry):
    assert [c["fault"] for c in dry["faults"]] == ["F1_SILENT_OMISSION", "F2_DUPLICATE", "F3_FALSE_POSITIVE_DOOR",
                                                    "F4_QUANTITY_ERROR", "F5_FLAGGED_OMISSION",
                                                    "F6_FALSE_POSITIVE_AREA"]
    assert dry["all_faults_detected"], [c for c in dry["faults"] if not c["pass"]]


def test_one_project_never_allows_a_percentage_claim(dry):
    claims = dry["engine_on_synthetic_villa"]["claims"]
    assert claims and not any(c["claim_allowed"] for c in claims.values())
    assert all(any("project" in w for w in c["why_not"]) for c in claims.values())


def test_the_prediction_is_frozen_before_the_benchmark_is_opened(dry):
    assert len(dry["freeze_digest_before_benchmark_opened"]) == 64 and len(dry["benchmark_commitment"]) == 64


def test_the_scorer_is_stdlib_only():
    import ast
    src = (DIR / "blind_score.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | \
           {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert mods <= {"__future__", "hashlib", "json", "math", "collections", "pathlib"}


def test_an_unscored_item_code_is_reported_not_dropped():
    BS = _load("blind_score")
    pred = BS.export_from_memory({"lines": [{"item_code": "ARCH.WALL_RUN", "location": {"floor": "GF"},
                                             "unit": "lm", "measured_net": 1.0, "evidence_state": "PROVISIONAL",
                                             "line_id": "L1"}]}, {"rooms": [], "openings": []})
    assert pred["unscored_item_codes"] == {"ARCH.WALL_RUN": 1} and pred["rows"] == []
