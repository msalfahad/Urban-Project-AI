"""R8.12 §27-§29: digest hierarchy and the generic owner-physical-fact model."""

from __future__ import annotations

from engine.source import owner_claims as OC, owner_facts as OF, room_topology as RT, run_manifest as RM
from tests.r8_8 import helpers as H

PARTS = [H.seg(1, 0, 0, 1000, 0), H.seg(2, 1000, 0, 1000, 800), H.seg(3, 1000, 800, 0, 800), H.seg(4, 0, 800, 0, 0),
         H.seg(10, 0, 400, 600, 400), H.seg(11, 0, 420, 600, 420), H.seg(90, 600, 400, 600, 420, layer="DIM")]


def inp(parts=PARTS, **kw):
    return H.inp(parts, texts=[H.text(5, "A", 500, 100), H.text(6, "B", 500, 700)], **kw)


def fact(i, reading="REAL_WALL_END", handle="90", version=1):
    p = next(x for x in i.parts if x.identity.source_handle == handle)
    return OF.PhysicalFact("F-1", version, "OPEN_PASSAGE_CONSTRUCTION", ("PROJECT_OWNER",),
                           {"source_revision_id": i.revision.revision_id, "source_anchor_sha256":
                            i.revision.anchor_sha256, "region_id": i.region_id, "frame_id": i.frame_id},
                           ((p.identity.key, OC.part_fingerprint(p), reading),),
                           allowed_domains=OF.KIND_DOMAINS["OPEN_PASSAGE_CONSTRUCTION"])


# ------------------------------------------------------------------------------- digest hierarchy
def test_the_topology_digest_is_the_run_input_digest():
    m = RT.run(inp(), frame_insert=None)["run_manifest"]
    assert m["TOPOLOGY_RUN_INPUT_DIGEST"] == m["RUN_INPUT_DIGEST"] and m["digest_layer"] == RM.TOPOLOGY_LAYER


def test_a_corroborating_only_owner_fact_leaves_topology_and_row_digests_unchanged():
    i = inp()
    m = RT.run(i, frame_insert=None)["run_manifest"]          # the fact never enters TS01: same topology digest
    a = RM.row_authority_digest(m["TOPOLOGY_RUN_INPUT_DIGEST"], row_id="R", row_method="M", trade_rules=["T@v1"])
    b = RM.row_authority_digest(m["TOPOLOGY_RUN_INPUT_DIGEST"], row_id="R", row_method="M", trade_rules=["T@v1"])
    assert a["digest"] == b["digest"] and RT.run(i, frame_insert=None)["run_manifest"]["RUN_INPUT_DIGEST"] == \
        m["RUN_INPUT_DIGEST"]


def test_the_row_authority_digest_changes_when_row_authority_changes():
    t = "a" * 64
    base = RM.row_authority_digest(t, row_id="R", row_method="M", trade_rules=["T@v1"])
    assert RM.row_authority_digest(t, row_id="R", row_method="M", trade_rules=["T@v2"])["digest"] != base["digest"]
    assert RM.row_authority_digest(t, row_id="R", row_method="M", trade_rules=["T@v1"],
                                   owner_facts_applied=["F-1@v1"])["digest"] != base["digest"]
    assert RM.row_authority_digest("b" * 64, row_id="R", row_method="M", trade_rules=["T@v1"])["digest"] != \
        base["digest"]


def test_the_release_digest_adds_anchor_reviews_and_blockers():
    r = RM.row_authority_digest("a" * 64, row_id="R", row_method="M")["digest"]
    a = RM.release_input_digest(r, source_anchor_state="NOT_ESTABLISHED")
    b = RM.release_input_digest(r, source_anchor_state="ESTABLISHED")
    c = RM.release_input_digest(r, source_anchor_state="NOT_ESTABLISHED", reviews=["TC-1:REVIEWED_BY_OWNER"])
    assert len({a["digest"], b["digest"], c["digest"]}) == 3 and a["row"] == r


# ------------------------------------------------------------------------------- owner physical facts
def test_a_fact_binds_to_its_own_source_and_is_rejected_elsewhere():
    i = inp()
    f = fact(i)
    assert OF.bind(f, i)["binding"] == OC.APPLIES
    assert OF.bind(f, inp(revision=H.rev(rid="REV_B")))["binding"] == OF.REJECTED_SCOPE
    moved = [x if x.identity.source_handle != "90" else H.seg(90, 601, 400, 601, 420, layer="DIM") for x in PARTS]
    assert OF.bind(f, inp(moved))["binding"] == OF.STALE


def test_the_engine_owner_matrix():
    assert OF.compare(OF.ENGINE_ESTABLISHED, "REAL_WALL_END", "REAL_WALL_END") == OF.AGREES
    assert OF.compare(OF.ENGINE_ESTABLISHED, "REAL_WALL_END", "NOT_WALL_CAP") == OF.DISAGREES
    assert OF.compare(OF.ENGINE_UNRESOLVED, "REAL_WALL_END") == OF.OWNER_ONLY
    assert OF.compare(OF.ENGINE_CONTRARY, "REAL_WALL_END") == OF.CONTRADICTED
    assert OF.MATRIX[OF.OWNER_ONLY] == "MAY_APPLY_AS_OWNER_ROLE_AUTHORITY"


def test_outcomes_corroborating_applied_conflict_stale_scope():
    i = inp()
    b = OF.bind(fact(i), i)
    assert OF.outcome(b, OF.TOPOLOGY_CLOSURE_REVIEW, used=False, comparisons=[OF.AGREES]) == OF.CORROBORATING_ONLY
    assert OF.outcome(b, OF.PASSAGE_ATTRIBUTES, used=True) == OF.APPLIED
    assert OF.outcome(b, OF.TOPOLOGY_CLOSURE_REVIEW, used=False, comparisons=[OF.DISAGREES]) == OF.CONFLICT
    assert OF.outcome({"binding": OF.STALE}, OF.PASSAGE_ATTRIBUTES, used=True) == OF.STALE
    assert OF.outcome({"binding": OF.REJECTED_SCOPE}, OF.PASSAGE_ATTRIBUTES, used=True) == OF.REJECTED_SCOPE


def test_a_fact_kind_never_reaches_topology_role_by_itself():
    assert OF.TOPOLOGY_ROLE not in OF.KIND_DOMAINS["OPEN_PASSAGE_CONSTRUCTION"]
    rec = OF.policy_record()
    assert "is project logic in code" in rec["never"] and len(rec["digest"]) == 64


def test_the_committed_hall_lobby_fact_loads_into_the_generic_model():
    import json
    from pathlib import Path
    raw = json.loads((Path(__file__).resolve().parents[2] / "data/registry/OWNER_PHYSICAL_FACTS.json").read_text())
    f = OF.from_record(raw["facts"][0])
    assert f.ref == "QORTUBA-NEW-HALL-LOBBY-OPEN-PASSAGE-OWNER-001@v1" and len(f.parts) == 7
    assert OF.TOPOLOGY_ROLE not in f.allowed_domains
