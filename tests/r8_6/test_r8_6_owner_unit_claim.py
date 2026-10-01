"""The Qortuba owner unit claim: exact source only, beside the declaration, never transferred."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLAIMS = json.loads((ROOT / "data/registry/OWNER_UNIT_CLAIMS.json").read_text())
QORTUBA = "2ec3a9c8b66eb2e129275b87010f4a8d79d7e5bdcc31c1897c14fd7e5647d355"
P7757 = "7f61f3acdd62d62dc745f8b522f8136cb41c575df36ec6d9f27c2fe48fea41e3"
ALRASHED = "299c61b1df7660384e027d44c0a29d8b64c92995843c0517cea05d485974660c"


def lab():
    sys.path.insert(0, str(ROOT / "research/external_engine_lab"))
    import r8_6_canonical_rebuild as R
    return R


def test_the_claim_is_complete_versioned_and_for_one_exact_source():
    (c,) = CLAIMS["claims"]
    assert c["source_sha256"] == QORTUBA and c["native_to_mm"] == 10.0 and c["unit"] == "cm"
    assert c["author"] and c["author_role"] == "PROJECT_OWNER" and c["timestamp"] and c["version"] == 1
    assert c["claim_scope"] == ["MODEL_SPACE"] and c["supersedes"] is None


def test_the_claim_is_never_applied_to_another_source():
    R = lab()
    assert [e.evidence_id for e in R.owner_unit_claims(QORTUBA)] == ["QORTUBA-NATIVE-UNIT-OWNER-001"]
    assert R.owner_unit_claims(P7757) == [] and R.owner_unit_claims(ALRASHED) == []


def test_the_frame_policy_confirms_it_and_rejects_it_on_any_other_hash():
    from engine.source import frame as FR
    R = lab()
    (hc,) = R.owner_unit_claims(QORTUBA)
    decl = FR.UnitEvidence("MODEL_SPACE:INSUNITS:LIBREDWG", FR.NATIVE_UNIT, "UNIT_HEADER_DECLARATION", "MODEL_SPACE",
                           ("DECL:INSUNITS",), 10.0, source_sha256=QORTUBA)
    ok = FR.unit_context(QORTUBA, "MODEL_SPACE", FR.MODEL_SPACE, [decl, hc], insunits=5, policy=FR.RELEASE_V3)
    assert ok.status == FR.CONFIRMED_BY_HUMAN and ok.native_to_mm == 10.0
    other = FR.unit_context(P7757, "MODEL_SPACE", FR.MODEL_SPACE, [hc], insunits=5, policy=FR.RELEASE_V3)
    assert other.status != FR.CONFIRMED_BY_HUMAN
    assert ("QORTUBA-NATIVE-UNIT-OWNER-001", "HUMAN_CONFIRMATION_SOURCE_MISMATCH") in other.excluded_evidence


def test_the_source_declaration_is_kept_beside_the_claim():
    proof = json.loads((ROOT / "tests/r8_6/registers/QORTUBA_ROUND1_PROOF.json").read_text())
    ids = [e["evidence_id"] for e in proof["canonical_context"]["unit_evidence"]]
    assert "MODEL_SPACE:INSUNITS:LIBREDWG" in ids and "QORTUBA-NATIVE-UNIT-OWNER-001" in ids
    assert proof["canonical_context"]["owner_claims_applied"] == ["QORTUBA-NATIVE-UNIT-OWNER-001"]


def test_the_region_designation_is_not_touched_by_the_unit_answer():
    proof = json.loads((ROOT / "tests/r8_6/registers/QORTUBA_ROUND1_PROOF.json").read_text())
    assert proof["canonical_context"]["region"] == "UNCONFIRMED" and proof["canonical_context"]["frame"] == "UNCONFIRMED"
    wi = proof["if_designation_accepted_diagnostic"]
    assert wi["frame"] == "CONFIRMED_BY_HUMAN" and wi["release"] == "PREVIEW"
    assert all(b.startswith("D_ROUTES") for b in wi["blockers"])
