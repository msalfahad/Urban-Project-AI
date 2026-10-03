"""R8.11 §19-§21, §25-§28, §39: run manifest + RUN_INPUT_DIGEST, offered vs applied claims, semantic class authority,
object-footprint policy independent of object role."""

from __future__ import annotations

from dataclasses import replace

import pytest

from engine.source import geometry_role as GR, owner_claims as OC, role_authority as RA, room_topology as RT
from engine.source import trade_regions as TR
from tests.r8_8 import helpers as H

LABELS = [H.text(5, "BED.ROOM", 200, 200), H.text(6, "BATH", 850, 200)]


def parts():
    return [H.seg(100, 0, 0, 1000, 0), H.seg(101, 1000, 0, 1000, 400), H.seg(102, 1000, 400, 0, 400),
            H.seg(103, 0, 400, 0, 0), H.seg(7116, 400, 0, 400, 400, layer="DIM")]


def claim(inp, **kw):
    p = next(x for x in inp.parts if x.identity.source_handle == "7116")
    base = dict(claim_id="OWNER-WALL", version=1, source_revision_id=inp.revision.revision_id,
                source_anchor_sha256=inp.revision.anchor_sha256, region_id=inp.region_id, frame_id=inp.frame_id,
                parts=((p.identity.key, p.layer, OC.part_fingerprint(p)),), role=GR.TOPOLOGY_BOUNDARY,
                authority=("PROJECT_OWNER",), statement="wall")
    base.update(kw)
    return OC.PartRoleClaim(**base)


def m(inp, **kw):
    return RT.run(inp, frame_insert=None, **kw)["run_manifest"]


# ------------------------------------------------------------------------------- the digest
def test_same_run_inputs_give_the_same_digest():
    i = H.inp(parts(), texts=LABELS)
    assert m(i)["RUN_INPUT_DIGEST"] == m(i)["RUN_INPUT_DIGEST"]


def test_a_source_sha_change_gives_a_different_digest():
    a = H.inp(parts(), texts=LABELS)
    b = H.inp(parts(), texts=LABELS, revision=H.rev(sha="b" * 64))
    assert m(a)["RUN_INPUT_DIGEST"] != m(b)["RUN_INPUT_DIGEST"]


def test_a_claim_version_change_gives_a_different_digest():
    i = H.inp(parts(), texts=LABELS)
    assert m(i, part_claims=[claim(i)])["RUN_INPUT_DIGEST"] != m(i, part_claims=[claim(i, version=2)])["RUN_INPUT_DIGEST"]


def test_a_policy_digest_change_gives_a_different_digest(monkeypatch):
    i = H.inp(parts(), texts=LABELS)
    before = m(i)
    monkeypatch.setattr(RA, "NEAR_MISS_REVIEW_BAND_MM", 40.0)
    after = m(i)
    assert before["policies"]["near_miss_review_band_mm"] != after["policies"]["near_miss_review_band_mm"]
    assert before["RUN_INPUT_DIGEST"] != after["RUN_INPUT_DIGEST"]


def test_policy_ids_and_digests_are_recorded():
    pol = m(H.inp(parts(), texts=LABELS))["policies"]
    for k in ("geometry_role", "role_authority", "text_role", "topology_tolerance", "owner_claim_binding",
              "trade_treatment", "wall_band", "topology_closure"):
        assert pol[k][0] and len(pol[k][1]) == 64, k
    assert pol["role_authority"][0] == "ROLE_AUTHORITY_POLICY_V2" and pol["text_role"][0] == "TEXT_ROLE_POLICY_V2"


def test_the_code_commit_is_provenance_not_part_of_the_input_digest():
    i = H.inp(parts(), texts=LABELS)
    a, b = m(i, provenance={"code_commit": "aaa"}), m(i, provenance={"code_commit": "bbb"})
    assert a["RUN_INPUT_DIGEST"] == b["RUN_INPUT_DIGEST"] and a["CODE_BOUND_DIGEST"] != b["CODE_BOUND_DIGEST"]
    assert "code_commit" in a["not_in_digest"]


# ------------------------------------------------------------------------------- offered vs applied
def test_claim_offered_and_claim_applied_are_recorded_separately():
    i = H.inp(parts(), texts=LABELS)
    x = m(i, part_claims=[claim(i)])
    assert [c["claim"] for c in x["claims_offered"]] == ["OWNER-WALL@v1"]
    assert [c["claim"] for c in x["claims_applied"]] == ["OWNER-WALL@v1"] and x["claims_rejected"] == []


def test_a_claim_scope_mismatch_appears_in_the_manifest_and_never_as_authority():
    i = H.inp(parts(), texts=LABELS)
    other = claim(i, region_id="R2")
    x = m(i, part_claims=[other])
    assert [c["claim"] for c in x["claims_offered"]] == ["OWNER-WALL@v1"] and x["claims_applied"] == []
    assert x["claims_rejected"][0]["outcome"] == OC.REGION_SCOPE_MISMATCH


def test_a_stale_claim_is_rejected_in_the_manifest():
    i = H.inp(parts(), texts=LABELS)
    c = claim(i)
    moved = H.inp([p if p.identity.source_handle != "7116" else H.seg(7116, 410, 0, 410, 400, layer="DIM")
                   for p in parts()], texts=LABELS)
    x = m(moved, part_claims=[c])
    assert x["claims_applied"] == [] and x["claims_rejected"][0]["per_part"][0]["state"] == OC.STALE_PART_FINGERPRINT


# ------------------------------------------------------------------------------- semantic class authority
CLASSES = TR.SemanticClassRule("SEMCLASS-1", 1, "PROJECT_OWNER_RULE", ("P-7",), {"revision": "REV_A"},
                               by_label={"BATH": "WET_ROOM", "PAINTRY": "SERVICE_ROOM"},
                               otherwise_class="DRY_INTERNAL_ROOM", scope_labels=("HALL", "M.B.ROOM", "DRESS"))
BY_CLASS = {"WET_ROOM": "CERAMIC", "SERVICE_ROOM": "CERAMIC", "DRY_INTERNAL_ROOM": "PORCELAIN"}


def test_trade_treatment_goes_through_an_authoritative_class():
    t = TR.class_treatments(["M.B.ROOM", "DRESS", "BATH"], CLASSES, BY_CLASS)
    assert t == {"BATH": ("WET_ROOM", "CERAMIC"), "DRESS": ("DRY_INTERNAL_ROOM", "PORCELAIN"),
                 "M.B.ROOM": ("DRY_INTERNAL_ROOM", "PORCELAIN")}


def test_raw_label_spelling_cannot_become_generic_trade_truth():
    t = TR.class_treatments(["Bath", "BATH ", "M.B ROOM"], CLASSES, BY_CLASS)
    assert all(v == (None, None) for v in t.values())
    rule = TR.class_rule_as_treatment("FLOOR", 1, "FLOOR_FINISH", "OWNER", ("P-14",), CLASSES, BY_CLASS,
                                      TR.POLICY_UNRESOLVED)
    assert TR.zone_decision(["Bath"], rule)["state"] == TR.UNRESOLVED
    assert TR.zone_decision(["M.B.ROOM", "DRESS"], rule)["state"] == TR.NOT_REQUIRED
    assert "SEMCLASS-1@v1" in rule.source_refs


# ------------------------------------------------------------------------------- object role vs footprint
FLOOR = TR.TradeTreatmentRule("FLOOR", 1, "FLOOR_FINISH", "OWNER", (), otherwise="PORCELAIN")
UNKNOWN = {"effect": "CHANGES_AREA", "sources": ["REV_A|H9||SEGMENT|0"]}


def test_floor_object_footprint_unresolved_keeps_the_object_material():
    assert TR.object_materiality(UNKNOWN, FLOOR)["state"] == TR.MATERIAL


def test_a_footprint_policy_answers_the_trade_without_a_final_object_role():
    pol = TR.TradeObjectFootprintPolicy("FP-1", 1, "FLOOR_FINISH", TR.ANY_NON_PARTITION_OBJECT,
                                        TR.FOOTPRINT_INCLUDED, "PROJECT_OWNER", {}, ("Q-x",))
    r = TR.object_materiality(UNKNOWN, FLOOR, [pol])
    assert r["state"] == TR.NON_MATERIAL and r["footprint_policy"] == "FP-1@v1"


def test_a_role_dependent_footprint_policy_keeps_an_unresolved_object_material():
    pol = TR.TradeObjectFootprintPolicy("FP-2", 1, "FLOOR_FINISH", TR.ANY_NON_PARTITION_OBJECT, TR.ROLE_REQUIRED,
                                        "URBAN_METHOD", {}, ())
    assert TR.object_materiality(UNKNOWN, FLOOR, [pol])["state"] == TR.MATERIAL


def test_a_partition_candidate_is_material_whatever_the_footprint_policy():
    pol = TR.TradeObjectFootprintPolicy("FP-1", 1, "FLOOR_FINISH", TR.ANY_NON_PARTITION_OBJECT,
                                        TR.FOOTPRINT_INCLUDED, "PROJECT_OWNER", {}, ())
    sep = {"effect": "SEPARATES_LABELS", "sources": ["X"]}
    assert TR.object_materiality(sep, FLOOR, [pol])["state"] == TR.MATERIAL


def test_a_ceiling_policy_lets_ceiling_continue_while_the_floor_stays_blocked():
    ceil = TR.TradeTreatmentRule("CEIL", 1, "CEILING", "OWNER_CLAIM", (), otherwise="CEILING_BY_AREA")
    pol = TR.TradeObjectFootprintPolicy("FP-C", 1, "CEILING", TR.ANY_NON_PARTITION_OBJECT, TR.FOOTPRINT_INCLUDED,
                                        "OWNER_CLAIM", {}, ())
    assert TR.object_materiality(UNKNOWN, ceil, [pol])["state"] == TR.NON_MATERIAL
    assert TR.object_materiality(UNKNOWN, FLOOR, [pol])["state"] == TR.MATERIAL
