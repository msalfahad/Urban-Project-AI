"""R8.7 scoped owner claims: an answer applies exactly where it was given (OWNER_SCOPE_MISMATCH elsewhere), a
pending-anchor claim never serves a release, and the historical unit claim is never transferred."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from engine.source import canonical_input as CI, owner_scope as OS

ROOT = Path(__file__).resolve().parents[2]
CLAIMS = json.loads((ROOT / "data/registry/OWNER_PROJECT_CLAIMS.json").read_text())
OLD_DWG = "2ec3a9c8b66eb2e129275b87010f4a8d79d7e5bdcc31c1897c14fd7e5647d355"
NEW_DXF = "df0e1d690285f5455b3b5acebe7e20eaee2d1c8aa3743b633a9fd257c6d6f315"
REGION = "RC:MODEL_SPACE:4267:540:1649"


def claim(cid):
    return OS.from_record(next(c for c in CLAIMS["claims"] if c["claim_id"] == cid))


def q14(**kw):
    use = dict(project="QORTUBA", revision_id="QORTUBA_REV_NEW", purpose=OS.SHADOW_DIAGNOSTIC, region_id=REGION,
               space_id="BATH", item="Q-14|CEILING_BY_AREA")
    use.update(kw)
    return OS.applies(claim("QORTUBA-Q14-CEILING-FOOTPRINT-OWNER-001"), **use)


def test_q14_rule_applies_in_its_scope():
    r = q14()
    assert r["state"] == OS.APPLIES and r["value"]["ceiling_footprint"] == "EQUALS_FLOOR_FOOTPRINT"
    assert set(r["value"]["deductions"].values()) == {"NONE"}


def test_q14_rule_does_not_leak():
    assert q14(region_id="RC:PLAN_VARIANT_3")["state"] == OS.OWNER_SCOPE_MISMATCH                 # another layout / floor
    assert q14(revision_id="QORTUBA_REV_OLD")["state"] == OS.OWNER_SCOPE_MISMATCH                # another revision
    assert q14(project="ANOTHER_PROJECT")["state"] == OS.OWNER_SCOPE_MISMATCH                    # another project
    assert q14(space_id="STAIR")["state"] == OS.OWNER_SCOPE_MISMATCH                             # a stair / core
    assert q14(item="CEILING_NET_PLAN_AREA")["state"] == OS.OWNER_SCOPE_MISMATCH                 # the future method
    assert q14(purpose=OS.RELEASE)["state"] == OS.PURPOSE_NOT_AUTHORISED                         # never a release yet
    c = claim("QORTUBA-Q14-CEILING-FOOTPRINT-OWNER-001")
    assert c.unrestricted == frozenset() and "Urban company rules" in c.value["not_a_rule_for"]


def test_new_revision_unit_claim_is_scoped_correctly():
    c = claim("QORTUBA-NEW-REVISION-NATIVE-UNIT-OWNER-001")
    ok = OS.applies(c, project="QORTUBA", revision_id="QORTUBA_REV_NEW", purpose=OS.SHADOW_DIAGNOSTIC)
    assert ok["state"] == OS.APPLIES and ok["value"]["native_to_mm"] == 10.0
    assert OS.applies(c, project="QORTUBA", revision_id="QORTUBA_REV_OLD", purpose=OS.SHADOW_DIAGNOSTIC)["state"] == \
        OS.OWNER_SCOPE_MISMATCH
    assert OS.applies(c, project="QORTUBA", revision_id="QORTUBA_REV_NEW", purpose=OS.RELEASE)["state"] == \
        OS.PURPOSE_NOT_AUTHORISED
    assert c.anchor_state == "OWNER_CONFIRMED_PENDING_EXACT_SOURCE_ANCHOR" and c.evidence["dxf_sha256"] == NEW_DXF


def test_old_unit_claim_is_unchanged_and_not_transferred():
    old = json.loads((ROOT / "data/registry/OWNER_UNIT_CLAIMS.json").read_text())["claims"]
    assert [(c["evidence_id"], c["source_sha256"], c["native_to_mm"]) for c in old] == [
        ("QORTUBA-NATIVE-UNIT-OWNER-001", OLD_DWG, 10.0)]
    sys.path.insert(0, str(ROOT / "research/external_engine_lab"))
    import r8_7_canonical as R7
    assert R7.unit_for(R7.rev_old()) == (10.0, "QORTUBA-NATIVE-UNIT-OWNER-001")
    assert R7.unit_for(R7.rev_new()) == (10.0, "QORTUBA-NEW-REVISION-NATIVE-UNIT-OWNER-001")
    # a revision the owner said nothing about gets no unit: neither claim transfers
    mm, why = R7.unit_for(CI.SourceRevision("ANOTHER_REVISION", CI.EXACT_SOURCE, "c" * 64))
    assert mm is None and why == OS.OWNER_SCOPE_MISMATCH
    # the new revision re-anchored to another file (e.g. the DWG) needs a re-anchored claim first
    mm, why = R7.unit_for(CI.SourceRevision("QORTUBA_REV_NEW", CI.EXACT_SOURCE, "d" * 64))
    assert mm is None and why.startswith("ANCHOR_MISMATCH")


def test_superseded_claims_never_apply():
    c = claim("QORTUBA-PLAN-SELECTION-OWNER-001")
    from dataclasses import replace
    assert OS.applies(replace(c, status=OS.SUPERSEDED), project="QORTUBA", revision_id="QORTUBA_REV_NEW",
                      purpose=OS.SHADOW_DIAGNOSTIC, region_id=REGION)["state"] == OS.CLAIM_NOT_ACTIVE


def test_every_claim_states_its_scope_and_purposes():
    for c in CLAIMS["claims"]:
        s = c["scope"]
        assert set(s) == {"project", "revision_id", "region_id", "space_ids", "items", "unrestricted"}, c["claim_id"]
        assert c["purposes"] == ["SHADOW_DIAGNOSTIC"] and c["authority"] == "PROJECT_OWNER"
        assert c["anchor_state"] == "OWNER_CONFIRMED_PENDING_EXACT_SOURCE_ANCHOR"
