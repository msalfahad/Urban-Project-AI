"""R8.6 §7: the six Qortuba round-1 rows, rebuilt from canonical source inputs by the frozen method.

same canonical source inputs + same admitted method = same canonical result.

The expected values are regression truth written AFTER the calculation path was frozen. They are compared to a
value computed here and do not enter the computation (canonical_round1 takes no expected value)."""

from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((Path(__file__).parent / "FIXTURE_MANIFEST.json").read_text())
ROWS = ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14")


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def _fixtures_or_skip():
    for path, want in MANIFEST["fixtures"].items():
        if not (ROOT / path).exists():
            pytest.skip(f"declared fixture not present in this checkout: {path}")
        assert _sha(path) == want, f"FIXTURE DRIFT: {path} differs from the declared fixture set"


@pytest.fixture(scope="module")
def lab():
    _fixtures_or_skip()
    sys.path.insert(0, str(ROOT / "research/external_engine_lab"))
    import r8_6_canonical_rebuild as R
    return R


@pytest.fixture(scope="module")
def first(lab):
    return lab.canonical_round1()


@pytest.fixture(scope="module")
def second(lab):
    return lab.canonical_round1()


def test_the_calculation_path_is_the_frozen_one():
    _fixtures_or_skip()
    changed = [p for p, h in MANIFEST["frozen_calculation_path"].items() if _sha(p) != h]
    assert not changed, f"calculation path changed since the freeze, re-freeze deliberately: {changed}"


def test_the_expected_value_cannot_reach_the_computation(lab):
    assert list(inspect.signature(lab.canonical_round1).parameters) == ["can"]
    src = inspect.getsource(lab.canonical_round1) + inspect.getsource(lab.canonical_input)
    assert "APPROVED" not in src and "regression_truth" not in src and "MEASURED_QUANTITY" not in src


@pytest.mark.parametrize("qid", ROWS)
def test_row_is_reproducible_from_canonical_inputs(qid, first, second):
    assert first["six"][qid] == second["six"][qid]
    assert first["six"][qid] == MANIFEST["regression_truth"][qid]


def test_the_rooms_behind_the_rows_are_identical_on_two_runs(first, second):
    assert first["rooms_digest"] == second["rooms_digest"] == MANIFEST["canonical_rooms_digest"]


def test_the_method_ran_at_the_owner_confirmed_unit_and_nothing_is_released(first):
    """The method still reads INSUNITS internally; the owner claim confirms the same 10.0 mm per unit, so the rooms
    are proven at the confirmed unit. The frame stays UNCONFIRMED (CAD drawing-region designation pending)."""
    proof = json.loads((Path(__file__).parent / "registers" / "QORTUBA_ROUND1_PROOF.json").read_text())
    assert proof["canonical_context"]["unit"] == "CONFIRMED_BY_HUMAN"
    assert first["unit"]["UNIT_SCALE_TO_MM"] == proof["canonical_context"]["native_to_mm"] == 10.0
    assert proof["canonical_context"]["frame"] == "UNCONFIRMED"
    for r in proof["rows"]:
        assert r["unit_context"]["method_unit_equals_confirmed_unit"] is True
        assert r["canonical_physical_value"] is None and r["release_eligibility"] == "NOT_ELIGIBLE"
