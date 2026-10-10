"""R8.4 §8-§10, §31 — formal supersession of disputed R8.0 contracts.

The legacy contracts are never edited: their hashes are frozen in
tests/r8_0/registers/R8_CONTRACT_SUPERSESSION.json and checked here; the legacy tests keep
running as strict xfails (class CONTRACT_SUPERSEDED). The superseding expectations are asserted
against production through the same R8.0 adapter (tests/r8_0/frame_harness.py)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from engine.source import frame as FR
from engine.source.cad import unit_evidence as UE
from tests.r8_0 import libredwg_builder as B, targets
from tests.r8_0.scenes import SKIP_CASES
from tests.r8_4 import legacy as L

ROOT = Path(__file__).resolve().parents[2]
REG = json.loads((ROOT / "tests/r8_0/registers/R8_CONTRACT_SUPERSESSION.json").read_text())
BY_ID = {e["legacy_id"]: e for e in REG["entries"]}
EXPECTED = json.loads((ROOT / "tests/r8_0/registers/R8_0_EXPECTED_FAILURES.json").read_text())["expected_failures"]
SHA = "0" * 64
FIELDS = ("legacy_id", "legacy_hash", "legacy_expectation", "legacy_source", "problem", "new_decision",
          "new_expectation", "superseding_authority", "date", "tests", "migration_effect")


def test_register_covers_the_four_reviewed_contracts_with_every_field():
    assert set(BY_ID) == {"F17", "MT-32", "MT-33", "F19"}
    for e in REG["entries"]:
        missing = [f for f in FIELDS if not e.get(f)]
        assert not missing, (e["legacy_id"], missing)


@pytest.mark.parametrize("cid", ["F17", "MT-32", "MT-33", "F19"])
def test_legacy_contract_unchanged(cid):
    """A silent rewrite of the historical contract (inputs, expectation or test source) fails here."""
    got = L.f19_hash() if cid == "F19" else L.row_hash(cid)
    assert got == BY_ID[cid]["legacy_hash"]
    if cid != "F19":
        assert L.contract_row(cid)[3] == BY_ID[cid]["legacy_expectation"]


@pytest.mark.parametrize("cid", ["F17", "MT-32", "MT-33"])
def test_superseded_legacy_test_still_runs_as_strict_xfail(cid):
    e = next(x for x in EXPECTED if x["test"].endswith(f"[{cid}]"))
    assert e["class"] == "CONTRACT_SUPERSEDED" and e["superseded_by"].endswith(f"#{cid}")


def test_f19_is_no_longer_an_expected_failure():
    assert not any("custom_entity_on_wall_layer" in x["test"] for x in EXPECTED)


@pytest.mark.parametrize("cid", ["F17", "MT-32"])
def test_superseding_expectation(cid):
    _, target, inputs, _ = L.contract_row(cid)
    new = BY_ID[cid]["new_expectation"]
    got = targets.call(target, **inputs)
    assert got["status"] == new["status"] == FR.UNCONFIRMED
    assert got["final_allowed"] is False
    assert new["finding_present"] in got["findings"]
    assert got["plausibility_counted_toward_verified"] is False
    # plausibility adds a question, never strength: removing it leaves the status unchanged
    bare = targets.call(target, header=inputs["header"], evidence=[])
    assert bare["status"] == got["status"]


def _dimlfac_candidate(ratio=0.0254):
    """A display/geometry family: display unit not authored -> a SET of interpretations."""
    vals = tuple(ratio * mm for _, mm in UE.STANDARD_DISPLAY_UNITS)
    return FR.UnitEvidence("MODEL:DIMFAMILY", FR.NATIVE_UNIT, FR.DIMENSION_STYLE, "MODEL",
                           (f"AUTHORED:{SHA}:DIMSTYLE:S", FR.family_lineage(FR.DIMENSION_STYLE, SHA),
                            "ASSUMPTION:DISPLAY_IN_STANDARD_UNIT"), None, source_sha256=SHA,
                           producer=FR.ENGINE, review_status=FR.CANDIDATE, derived_set=vals)


def _plaus(i, mm):
    return FR.UnitEvidence(f"P{i}", FR.NATIVE_UNIT, FR.GEOMETRY_PLAUSIBILITY, "MODEL", (f"PLAUSIBILITY:{i}",), mm,
                           source_sha256=SHA)


def test_mt33_superseding_expectation_synthetic():
    """The D-08 shape (declaration inch; display-ratio family + plot-size / wall-spacing plausibility pointing
    at metres) without any project value: candidate and plausibility never enter the admitted set and never
    lift the status to PROVISIONAL."""
    decl = list(FR.declaration_evidence(1, "MODEL", SHA)[0])
    items = [_dimlfac_candidate(), _plaus(1, 1000.0), _plaus(2, 1000.0)]
    rep = FR.independence_report(items, FR.NATIVE_UNIT, SHA)
    assert rep["independent_set_size"] == 0
    for policy in (FR.RELEASE_V1, FR.RELEASE_V2):
        u = FR.unit_context(SHA, "MODEL", FR.MODEL_SPACE, decl + items, insunits=1, policy=policy)
        assert FR.STRENGTH[u.status] < FR.STRENGTH[FR.PROVISIONAL], (policy.policy_id, u.status)
        assert FR.FINAL_MEASUREMENT not in u.allowed_use
        assert not {e.evidence_id for e in items} & set(u.evidence_ids)


@pytest.mark.skipif(not os.environ.get("URBAN_R8_REAL_SOURCE"), reason="real-source row: URBAN_R8_REAL_SOURCE unset")
def test_mt33_superseding_expectation_real_source():
    """Behaviour, never a count: a real D1 decode's evidence without admitted physical evidence gives a
    UNIT_CONTEXT no stronger than UNCONFIRMED."""
    path = Path(os.environ["URBAN_R8_REAL_SOURCE"])
    decode = json.loads(path.read_bytes().decode("utf-8", errors="replace"))
    ex = UE.extract(decode, "REAL")
    u = FR.unit_context("REAL", "MODEL_SPACE", FR.MODEL_SPACE, ex["evidence"],
                        insunits=decode.get("HEADER", {}).get("INSUNITS"))
    physical = [i for i in u.evidence_ids if not i.endswith(("INSUNITS:LIBREDWG", "FULL_SIZE"))]
    if not physical:
        assert FR.STRENGTH[u.status] <= FR.STRENGTH[FR.UNCONFIRMED]
    assert FR.FINAL_MEASUREMENT not in u.allowed_use


F19 = next(s for s in SKIP_CASES if s[0] == "F19")[3]


def test_f19_controls():
    got = targets.call("SOURCE_PROFILE", decode=B.build(F19), profile="CAD_PROFILE")
    assert got["V-CAD-5"] == "FAIL" and got["region_release"] == "BLOCKED"
    without = dict(F19, entities=[e for e in F19["entities"] if e["kind"] != "CUSTOM"])
    got = targets.call("SOURCE_PROFILE", decode=B.build(without), profile="CAD_PROFILE")
    assert got["V-CAD-5"] == "PASS" and got["region_release"] != "BLOCKED"
    other = dict(F19, entities=[dict(F19["entities"][0], layer="L-OTHER"), F19["entities"][1]])
    got = targets.call("SOURCE_PROFILE", decode=B.build(other), profile="CAD_PROFILE")
    assert got["V-CAD-5"] == "PASS"
    assert [f["impacts"] for f in got["region_findings"]] and all(
        all(i["severity"] == "REVIEW" for i in f["impacts"]) for f in got["region_findings"])


def test_v_cad_checks_cover_the_spec_ids():
    from engine.source import cad_profile as P
    assert list(P.V_CAD_CHECKS) == [f"V-CAD-{i}" for i in range(1, 7)]
    assert P.V_CAD_CHECKS["V-CAD-5"][0] == "H_FINDINGS"
