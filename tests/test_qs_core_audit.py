"""The generic core must not know any project.

Not a style rule: an engine that carries a known answer can reproduce it without ever being right, and every
"agreement" it then reports is circular.  This audit reads the production sources and fails on any project name,
any reference from a real drawing, any previously reported total, and any branch on which project is running.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from engine.qs_core import invariants, pipeline, synthetic as syn

CORE = sorted(Path("engine/qs_core").glob("*.py"))

# Known answers, project names and references from the projects this engine has been run on.  They live here,
# in the test, precisely because they may not live in the engine.
FORBIDDEN = [
    "ALRASHED", "AL RASHED", "AL_RASHED", "QORTUBA", "SABAH", "P7757", "7757",
    "3e847af", "ae259eaba3203798",
    "734.638", "931.016", "196.378", "828.493", "14.3301", "12.1257", "2.2044",
    "963.188", "190.289", "1493.945", "1,493.945", "474.693", "155.206", "128.816", "67.563",
    "381.535", "97.355", "349.603", "600.16", "950.22", "91.0604",
    "BA-0", "GR-0", "FI-0", "AR-FL", "AR-BL", "AR-AL", "AR-W-", "AR-01", "AR-06", "US-18", "US-19",
    "16-11-2025", ".dwg", ".pdf",
]


def test_the_core_names_no_project_and_carries_no_known_total():
    check = invariants.no_comparison_input(CORE, FORBIDDEN)
    assert check["PASS"], check["RESULT"]["HITS"]


def test_the_core_has_no_branch_on_which_project_is_running():
    patterns = [r"if\s+project\b", r"project\s*==", r"PROJECT_ID\s*==", r"if\s+.*\bfloor\s*==\s*[\"']",
                r"if\s+.*revision\s*==\s*[\"']"]
    hits = []
    for p in CORE:
        text = p.read_text("utf-8")
        for pat in patterns:
            for m in re.finditer(pat, text):
                hits.append({"FILE": str(p), "PATTERN": pat,
                             "LINE": text.count("\n", 0, m.start()) + 1})
    assert not hits, hits


def test_the_core_imports_nothing_from_a_project_package():
    offenders = []
    for p in CORE:
        for line in p.read_text("utf-8").splitlines():
            if re.match(r"\s*(from|import)\s+(research|agents)\b", line):
                offenders.append({"FILE": str(p), "LINE": line.strip()})
    assert not offenders, offenders


def test_every_tolerance_and_threshold_is_declared_with_a_reason():
    """A tolerance nobody can explain is a tuned constant waiting to happen."""
    named = {
        "engine/qs_core/openings.py": ["DECISIVE_MARGIN"],
        "engine/qs_core/spaces.py": ["MAJORITY"],
        "engine/qs_core/identity.py": ["MIN_IOU_MATCH", "AMBIGUITY_BAND", "SPLIT_SHARE"],
    }
    for path, names in named.items():
        text = Path(path).read_text("utf-8")
        for n in names:
            m = re.search(rf"^{n}\s*=", text, re.M)
            assert m, f"{n} is not declared at module level in {path}"
            preamble = text[:m.start()]
            assert "#" in preamble.split("\n\n")[-1] or '"""' in preamble[-400:], \
                f"{n} in {path} has no stated reason"


def test_a_tolerance_is_always_an_argument_to_the_algorithms():
    """The caller owns the drawing's precision; the engine may not assume it."""
    import inspect
    from engine.qs_core import openings as op, spaces as sp
    assert "tolerance" in inspect.signature(op.assign_opening_host).parameters
    assert "tolerance" in inspect.signature(sp.assemble_semantic_spaces).parameters
    assert "sliver_min_dimension" in inspect.signature(sp.assemble_semantic_spaces).parameters


def test_no_rate_waste_or_amount_is_ever_introduced():
    r = pipeline.run(syn.small_plan(), max_opening_span=syn.MAX_OPENING_SPAN, wall_height=3.0,
                        wall_geometry_includes_openings=syn.WALL_GEOMETRY_SPANS_OPENINGS)
    check = invariants.pricing_fields_separate_and_empty(r["MEASUREMENT_OBJECT_LIST"])
    assert check["PASS"], check["RESULT"]
    for o in r["MEASUREMENT_OBJECTS"]:
        assert set(("WASTE_PERCENT", "PROCUREMENT_QUANTITY", "UNIT_RATE", "AMOUNT")) <= set(o)
        assert o["MEASURED_QUANTITY"] is not None and o["MEASURED_UNIT"]


def test_the_engines_own_checks_do_not_cite_an_expected_answer():
    r = pipeline.run(syn.small_plan(), max_opening_span=syn.MAX_OPENING_SPAN, wall_height=3.0,
                        wall_geometry_includes_openings=syn.WALL_GEOMETRY_SPANS_OPENINGS)
    check = invariants.checks_are_evidence_based(r["INVARIANTS"]["CHECKS"], FORBIDDEN)
    assert check["PASS"], check["RESULT"]
