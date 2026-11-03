"""T-466 (owner directive 2026-11-02 D5): the known-failures ledger holds REAL known failures only, so a red test always
means something is wrong.

Normal: the committed ledger names no environment cause; every entry has a diagnosed cause, evidence, first failing
commit and owner; the six formerly listed non-private ids still exist as tests (they left the ledger because they PASS,
not because they were deleted); the 38 formerly failing private-input test files declare their private inputs (T-462),
so a missing private file is a skip, never a ledger entry; a clean run checks green against the ledger.
Adverse: a run with one failure is NEW against the ledger (exit 1); the builder refuses an environment cause and an
undiagnosed failure (never filed under a guess); a ledger entry with an environment cause code is detected."""
from __future__ import annotations

import ast
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t202"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"t466_{name}", HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


KF = _load("known_failures")
BL = _load("build_ledger")

# The six non-private ids of the T-202 ledger (head d699b650): WORKTREE_GITDIR (fixed by T-210 / T-464) and the five
# r8 import-rule ids (fixed by T-465, 0 failures on 1d892eb4).
RESOLVED = (
    "tests/christiannp_blind_process/test_package.py::test_builder_reproduces_outputs_byte_for_byte",
    "tests/r8_0/test_r8_0_import_boundaries.py::test_B5_B6_engine_source_dependencies_registered",
    "tests/r8_1/test_r8_1_boundaries.py::test_B5_B6_live_engine_source_dependencies_registered",
    "tests/r8_1/test_r8_1_boundaries.py::test_k1_is_stdlib_only_in_r8_1",
    "tests/r8_1/test_r8_1_kernel_ocs.py::test_k1_is_independent_of_ezdxf",
    "tests/r8_2/test_r8_2_k2.py::test_k1_does_not_import_ezdxf",
)
# The 38 test files whose 390 ids were PRIVATE_INPUT_ABSENT in the T-202 ledger (SKIPPED since T-462).
FORMER_PRIVATE = (
    "tests/alsenan_control_plane/test_control_plane_r2_gates.py",
    "tests/d1_1_stirrup_authority_audit/test_d1_1_package.py",
    "tests/d1_2_footing_cover_audit/test_d1_2_package.py",
    "tests/ground_slab_s8_1/test_s8_1_package.py",
    "tests/ground_slab_s8_1a/test_s8_1a_package.py",
    "tests/pre_s8_census/test_pre_s8.py",
    "tests/s7a_qa/test_s7a_qa.py",
    "tests/slab_rebar_pre_s7/test_pre_s7_package.py",
    "tests/slab_rebar_pre_s7_1/test_pre_s7_1_package.py",
    "tests/slab_rebar_s7/test_s7_package.py",
    "tests/source_recovery_delta/test_source_recovery_delta.py",
    "tests/structural_s9a/test_s9a_package.py",
    "tests/superstructure_beam_rebar_s6_1/test_alsenan_s6_1_package.py",
    "tests/test_benchmark_protection.py",
    "tests/test_pa08_qortuba_boq_rules.py",
    "tests/test_pa08_qortuba_boq_schema.py",
    "tests/test_pa08_qortuba_ext01.py",
    "tests/test_pa08_qortuba_final_takeoff.py",
    "tests/test_pa08_qortuba_open_passage.py",
    "tests/test_pa08_qortuba_opening_completion.py",
    "tests/test_pa08_qortuba_owner_inputs_v2.py",
    "tests/test_pa08_qortuba_owner_rule_audit.py",
    "tests/test_pa08_qortuba_owner_rules.py",
    "tests/test_pa08_qortuba_pricing.py",
    "tests/test_pa08_qortuba_pricing_audit.py",
    "tests/test_pa08_qortuba_qs01.py",
    "tests/test_pa08_qortuba_question_crops.py",
    "tests/test_pa08_qortuba_workflow_v1.py",
    "tests/test_pa09_alrashed.py",
    "tests/test_pa09_alrashed_amendment.py",
    "tests/test_pa09_alrashed_detailed.py",
    "tests/test_pa09_alrashed_final.py",
    "tests/test_pa09_alrashed_historical.py",
    "tests/test_pa09_alrashed_quantities.py",
    "tests/test_pa09_alrashed_unseal.py",
    "tests/test_pa09_villa_attribution.py",
    "tests/test_pa09_villa_blind_inventory.py",
    "tests/test_pa09_villa_blind_protocol.py",
)

CLEAN_RUN = """..........s.....x....
12 passed, 1 skipped, 1 xfailed in 0.50s
"""
ONE_FAIL = """....F
=================================== FAILURES ===================================
_________________________________ test_thing __________________________________
tests/x/test_x.py:3: in test_thing
E   AssertionError: 1 != 2
=========================== short test summary info ============================
FAILED tests/x/test_x.py::test_thing - AssertionError: 1 != 2
1 failed, 4 passed in 0.10s
"""
PRIVATE_FAIL = """....F
=================================== FAILURES ===================================
____________________________ test_rebuild_is_byte_identical ____________________________
tests/structural_s9a/test_s9a_package.py:9: in test_rebuild_is_byte_identical
E   FileNotFoundError: [Errno 2] No such file or directory: 'data/inputs/by_sha256/9f9d1179.dxf'
=========================== short test summary info ============================
FAILED tests/structural_s9a/test_s9a_package.py::test_rebuild_is_byte_identical - FileNotFoundError
1 failed, 4 passed in 0.10s
"""


def _environment_entries(doc):
    return [e["id"] for e in doc["failures"] if e.get("cause_code") in BL.ENVIRONMENT_CODES]


def _test_names(path):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    return {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


# ------------------------------------------------------------------------------------------------------------ normal
def test_committed_ledger_lists_no_environment_failure():
    doc = KF.load_ledger()
    assert doc["schema"] == "URBAN_KNOWN_FAILURES_V1" and re.fullmatch(r"[0-9a-f]{8,40}", doc["head"])
    assert _environment_entries(doc) == []
    for e in doc["failures"]:         # a real failure carries its diagnosis
        for k in ("cause_code", "cause", "evidence", "first_failing", "owner"):
            assert e.get(k), (e["id"], k)


def test_resolved_ids_left_the_ledger_because_they_exist_and_pass():
    ids = {e["id"] for e in KF.load_ledger()["failures"]}
    for nid in RESOLVED:
        assert nid not in ids
        path, _, name = nid.partition("::")
        assert name in _test_names(path), f"{nid} must still be a test (never deleted to leave the ledger)"


@pytest.mark.parametrize("path", FORMER_PRIVATE)
def test_former_private_failures_are_declared_private_inputs(path):
    """No former PRIVATE_INPUT_ABSENT file may fall back to failing: each declares its private inputs (T-462)."""
    text = (ROOT / path).read_text(encoding="utf-8")
    assert re.search(r"^PRIVATE_INPUTS\s*=", text, re.M) or "require_private(" in text, path
    ids = {e["id"].partition("::")[0] for e in KF.load_ledger()["failures"]}
    assert path not in ids


def test_clean_run_checks_green_and_builds_an_empty_ledger(tmp_path):
    run = tmp_path / "run.txt"
    run.write_text(CLEAN_RUN)
    assert KF.main(["check", str(run)]) == 0
    entries, problems = BL.build(CLEAN_RUN, "983b75f4")
    assert entries == [] and problems == []


# ----------------------------------------------------------------------------------------------------------- adverse
def test_adverse_any_failure_is_new_against_the_ledger(tmp_path):
    run = tmp_path / "run.txt"
    run.write_text(ONE_FAIL)
    new, hit, _ = KF.compare(KF.parse(ONE_FAIL), KF.load_ledger())
    assert new == ["tests/x/test_x.py::test_thing"] and hit == []
    assert KF.main(["check", str(run)]) == 1


def test_adverse_builder_refuses_undiagnosed_and_environment_causes(monkeypatch):
    entries, problems = BL.build(PRIVATE_FAIL, "983b75f4")      # no cause covers it: never filed under a guess
    assert entries == [] and problems and "no cause covers" in problems[0]
    env_cause = (r"tests/structural_s9a/.*\.py$", r".*", "PRIVATE_INPUT_ABSENT", "private input absent",
                 r"FileNotFoundError", "e97fa4b9", "nobody")
    monkeypatch.setattr(BL, "CAUSES", (env_cause,))
    entries, problems = BL.build(PRIVATE_FAIL, "983b75f4")
    assert entries == [] and problems and "environment cause" in problems[0]
    real_cause = (r"tests/x/.*\.py$", r"test_thing", "REAL_DEFECT", "a diagnosed defect", r"AssertionError", "abc1234",
                  "task T-999")
    monkeypatch.setattr(BL, "CAUSES", (real_cause,))
    entries, problems = BL.build(ONE_FAIL, "983b75f4")
    assert problems == [] and [e["cause_code"] for e in entries] == ["REAL_DEFECT"]


def test_adverse_environment_entry_in_a_ledger_is_detected(tmp_path):
    p = tmp_path / "l.json"
    p.write_text(json.dumps({"schema": "URBAN_KNOWN_FAILURES_V1", "head": "abcdef12", "failures": [
        {"id": "tests/a.py::t", "kind": "FAILED", "cause_code": "WORKTREE_GITDIR", "cause": "c", "evidence": "e",
         "first_failing": "abc", "owner": "o"}]}))
    assert _environment_entries(KF.load_ledger(p)) == ["tests/a.py::t"]
