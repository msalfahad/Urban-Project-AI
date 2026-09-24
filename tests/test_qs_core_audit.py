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
        "engine/qs_core/openings.py": ["DECISIVE_MARGIN", "GAP_OCCUPANCY", "SPANS_SHARE"],
        "engine/qs_core/spaces.py": ["MAJORITY"],
        "engine/qs_core/identity.py": ["MIN_IOU_MATCH", "AMBIGUITY_BAND", "SPLIT_SHARE"],
        "engine/qs_core/admission.py": ["DUPLICATE_OVERLAP", "WALL_INTERSECTION_SHARE"],
        "engine/qs_core/masonry.py": ["WALL_ASPECT_MIN", "FAMILY_MIN_MEMBERS", "DUPLICATE_SHARE",
                                      "JUNCTION_COVERAGE"],
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
    r = syn.run(syn.small_plan(), wall_height=3.0)
    check = invariants.pricing_fields_separate_and_empty(r["MEASUREMENT_OBJECT_LIST"])
    assert check["PASS"], check["RESULT"]
    for o in r["MEASUREMENT_OBJECTS"]:
        assert set(("WASTE_PERCENT", "PROCUREMENT_QUANTITY", "UNIT_RATE", "AMOUNT")) <= set(o)
        assert o["MEASURED_UNIT"]
        if o["STATUS"] == "FINAL_QUANTITY_AVAILABLE":
            assert o["MEASURED_QUANTITY"] is not None
        else:
            assert o["MEASURED_QUANTITY"] is None, "an unfinished object carries no quantity to be summed"


def test_the_engines_own_checks_do_not_cite_an_expected_answer():
    r = syn.run(syn.small_plan(), wall_height=3.0)
    check = invariants.checks_are_evidence_based(r["INVARIANTS"]["CHECKS"], FORBIDDEN)
    assert check["PASS"], check["RESULT"]


def test_the_facts_only_the_source_knows_have_no_defaults():
    """A default here is a guess about someone else's drawing, made silently and carried into a bill."""
    import inspect
    from engine.qs_core import pipeline as pl

    params = inspect.signature(pl.run).parameters
    for name in ("max_opening_span", "drafting_resolution_m"):
        assert params[name].default is inspect.Parameter.empty, f"{name} has acquired a default"


def test_no_source_wide_opening_basis_survives_anywhere_in_the_core():
    """The Boolean this round replaced: one answer for a whole revision, about a mixed population."""
    offenders = []
    for p in CORE:
        if p.name == "acceptance.py":
            continue          # the gate LOOKS for the old field in a document, and fails the document that has it
        for n, line in enumerate(p.read_text("utf-8").splitlines(), 1):
            if "wall_geometry_includes_openings" in line or "WALL_GEOMETRY_INCLUDES_OPENINGS" in line:
                offenders.append({"FILE": str(p), "LINE": n, "TEXT": line.strip()})
    assert not offenders, offenders


def test_the_engine_holds_no_list_of_acceptable_wall_thicknesses():
    """Identity is established from the drawing; a whitelist would be this project's answer, written down."""
    import re as _re
    offenders = []
    for p in CORE:
        for n, line in enumerate(p.read_text("utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            m = _re.match(r"\s*([A-Z_]*THICKNESS[A-Z_]*)\s*=\s*(.+)", line)
            if m and _re.search(r"\d", m.group(2)):
                offenders.append({"FILE": str(p), "LINE": n, "TEXT": line.strip()})
            if _re.search(r"THICKNESS[A-Z_]*\s*(in|==)\s*[\(\[{]", line):
                offenders.append({"FILE": str(p), "LINE": n, "TEXT": line.strip()})
    assert not offenders, offenders


def test_the_acceptance_gate_touches_no_engine_object():
    """It grades a document.  If it could reach into the engine it would stop being independent."""
    text = Path("engine/qs_core/acceptance.py").read_text("utf-8")
    for line in text.splitlines():
        assert not re.match(r"\s*(from|import)\s+engine\.qs_core", line), line
