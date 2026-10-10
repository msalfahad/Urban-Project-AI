"""R8.10 §2-§9, §25, §31: owner answers enter only as versioned claims bound to source identity; they change role /
source-completeness authority and nothing else; they never transfer; the four-state xref model."""

from __future__ import annotations

from dataclasses import replace

from engine.source import geometry_role as GR, owner_claims as OC, role_authority as RA, room_topology as RT
from engine.source import topology as T
from tests.r8_8 import helpers as H

LABELS = [H.text(5, "BED.ROOM", 250, 200), H.text(6, "BATH", 750, 200)]


def outer(h0=100):
    return [H.seg(h0, 0, 0, 1000, 0), H.seg(h0 + 1, 1000, 0, 1000, 400), H.seg(h0 + 2, 1000, 400, 0, 400),
            H.seg(h0 + 3, 0, 400, 0, 0)]


def dim_partitions():
    """Two DIM-layer lines, each of which would close a room: A at x = 400, B at x = 700."""
    return outer() + [H.seg(7116, 400, 0, 400, 400, layer="DIM"), H.seg(9001, 700, 0, 700, 400, layer="DIM")]


def part_claim(inp, handles, **kw):
    by = {p.identity.source_handle: p for p in inp.parts}
    parts = tuple((by[h].identity.key, by[h].layer, OC.part_fingerprint(by[h])) for h in handles)
    base = dict(claim_id="OWNER-WALLS", version=1, source_revision_id=inp.revision.revision_id,
                source_anchor_sha256=inp.revision.anchor_sha256, region_id=inp.region_id, frame_id=inp.frame_id,
                parts=parts, role=GR.TOPOLOGY_BOUNDARY, authority=("PROJECT_OWNER", "SOURCE_STRUCTURE_CORROBORATION"),
                statement="these lines are walls")
    base.update(kw)
    return OC.PartRoleClaim(**base)


def run(inp, **kw):
    return RT.run(inp, frame_insert=None, **kw)


# ------------------------------------------------------------------------------- part-scoped wall claims
def test_dim_wall_claim_applies_only_to_the_exact_parts():
    i = H.inp(dim_partitions(), texts=[H.text(5, "BED.ROOM", 200, 200), H.text(6, "BATH", 850, 200)])
    r = run(i, part_claims=[part_claim(i, ["7116"])])
    roles = r["roles"]["roles"]
    k_a, k_b = (p.identity.key for p in i.parts if p.identity.source_handle in ("7116", "9001"))
    k_a = next(p.identity.key for p in i.parts if p.identity.source_handle == "7116")
    k_b = next(p.identity.key for p in i.parts if p.identity.source_handle == "9001")
    assert roles[k_a].role == GR.TOPOLOGY_BOUNDARY and roles[k_a].rule_id == "CLAIM:OWNER-WALLS@v1"
    assert roles[k_b].role == GR.DIMENSION_GRAPHICS                       # the other DIM line is NOT a wall
    assert r["owner_claims"]["part_claims"][0]["state"] == OC.APPLIES


def test_other_dim_layer_parts_stay_excluded_unless_independently_established():
    i = H.inp(dim_partitions(), texts=LABELS)
    r = run(i, part_claims=[part_claim(i, ["7116"])])
    dims = [p for p in i.parts if p.layer == "DIM" and p.identity.source_handle != "7116"]
    assert all(r["roles"]["roles"][p.identity.key].role == GR.DIMENSION_GRAPHICS for p in dims)
    assert not any(p.identity.key in s["boundary_source_ids"] for p in dims for s in r["sites"])


def test_wall_claim_changes_role_authority_only_never_the_source_record():
    i = H.inp(dim_partitions(), texts=LABELS)
    before = [(p.identity, p.layer, p.geometry, p.kind) for p in i.parts]
    r = run(i, part_claims=[part_claim(i, ["7116"])])
    assert [(p.identity, p.layer, p.geometry, p.kind) for p in i.parts] == before
    a = r["roles"]["roles"][next(p.identity.key for p in i.parts if p.identity.source_handle == "7116")]
    assert a.evidence["ROLE_BEFORE"] == GR.DIMENSION_GRAPHICS                # the DIM role is recorded, not erased
    assert next(p for p in i.parts if p.identity.source_handle == "7116").layer == "DIM"


def test_wall_claim_does_not_transfer_to_another_region_or_plan():
    i = H.inp(dim_partitions(), texts=LABELS)
    c = part_claim(i, ["7116"])
    other_region = H.inp(dim_partitions(), texts=LABELS, region_id="R2")
    st = run(other_region, part_claims=[c])["owner_claims"]["part_claims"][0]
    assert st["state"] == OC.REGION_SCOPE_MISMATCH and st["applied_parts"] == []
    other_plan = replace(i, frame_id="MF:ANOTHER_PLAN")
    assert run(other_plan, part_claims=[c])["owner_claims"]["part_claims"][0]["state"] == OC.PLAN_SCOPE_MISMATCH


def test_wall_claim_does_not_transfer_to_another_revision_or_anchor():
    i = H.inp(dim_partitions(), texts=LABELS)
    c = part_claim(i, ["7116"])
    for rev in (H.rev("REV_B"), H.rev(sha="b" * 64)):
        j = H.inp(dim_partitions(), texts=LABELS, revision=rev)
        assert OC.part_claim_status(c, j)["state"] == OC.SOURCE_SCOPE_MISMATCH
    j = H.inp(dim_partitions(), texts=LABELS, revision=H.rev(sha="b" * 64))    # same revision id, other anchor
    st = run(j, part_claims=[c])["owner_claims"]["part_claims"][0]
    assert st["state"] == OC.SOURCE_SCOPE_MISMATCH and st["applied_parts"] == []


def test_wall_claim_never_binds_to_whatever_now_occupies_the_coordinates():
    i = H.inp(dim_partitions(), texts=LABELS)
    c = part_claim(i, ["7116"])
    moved = [p if p.identity.source_handle != "7116" else H.seg(7116, 450, 0, 450, 400, layer="DIM")
             for p in dim_partitions()]                                    # same handle, moved geometry
    st = OC.part_claim_status(c, H.inp(moved, texts=LABELS))
    assert st["parts"][0]["state"] == OC.STALE_PART_FINGERPRINT and st["applied_parts"] == []
    gone = [p for p in dim_partitions() if p.identity.source_handle != "7116"]
    replaced = gone + [H.seg(7999, 400, 0, 400, 400, layer="DIM")]          # a new entity on the same coordinates
    st = OC.part_claim_status(c, H.inp(replaced, texts=LABELS))
    assert st["parts"][0]["state"] == OC.PART_NOT_IN_SOURCE
    r = run(H.inp(replaced, texts=LABELS), part_claims=[c])
    k = next(p.identity.key for p in replaced if p.identity.source_handle == "7999")
    assert r["roles"]["roles"][k].role == GR.DIMENSION_GRAPHICS
    walled = gone + [H.seg(7999, 400, 0, 400, 400, layer="WALL")]         # the next revision draws a real wall
    r = run(H.inp(walled, texts=LABELS), part_claims=[c])
    assert r["roles"]["roles"][next(p.identity.key for p in walled if p.identity.source_handle == "7999")].rule_id \
        == "GR-05"                                                          # admitted by its own evidence, not the claim


def test_an_unreviewed_or_inactive_claim_changes_nothing():
    i = H.inp(dim_partitions(), texts=LABELS)
    for c in (part_claim(i, ["7116"], review_state=RA.SOURCE_EVIDENCE_CANDIDATE), part_claim(i, ["7116"], status="X")):
        r = run(i, part_claims=[c])
        assert r["owner_claims"]["part_claims"][0]["applied_parts"] == []
        assert all(a.role != GR.TOPOLOGY_BOUNDARY for k, a in r["roles"]["roles"].items() if "H7116" in k)


def test_owner_claim_enters_a_new_evidence_version_and_triggers_a_rebuild():
    i = H.inp(dim_partitions(), texts=LABELS)
    r0 = run(i)
    r1 = run(i, part_claims=[part_claim(i, ["7116"])])
    assert r0["owner_claims"]["evidence_version"] != r1["owner_claims"]["evidence_version"]
    (s0,) = [s for s in r0["sites"] if s["labels"]]                          # merged, role conflict, before
    assert RA.ROLE_CONFLICT_SEPARATOR in s0["issues"]
    labelled = {tuple(s["labels"]): s for s in r1["sites"] if s["labels"]}   # rebuilt topology, after
    assert set(labelled) == {("E5",), ("E6",)}
    assert abs(labelled[("E5",)]["area"] - 400 * 400) < 1e-6
    assert "value" not in OC.PartRoleClaim.__dataclass_fields__             # a claim carries no quantity


# ------------------------------------------------------------------------------- xref occurrence claims
FACTS = {"501": {"handle": "501", "xref_name": "blk", "xref_path": "..\\a.dwg", "insert": [0.0, 0.0],
                 "scale": [1.0, 1.0], "layer": "X"},
         "502": {"handle": "502", "xref_name": "det", "xref_path": "..\\b.dwg", "insert": [0.0, 0.0],
                 "scale": [1.0, 1.0], "layer": "X"}}


def xref_claim(inp, handles, **kw):
    base = dict(claim_id="OWNER-XREF", version=1, source_revision_id=inp.revision.revision_id,
                source_anchor_sha256=inp.revision.anchor_sha256, region_id=inp.region_id, frame_id=inp.frame_id,
                occurrences=tuple((h, OC.occurrence_fingerprint(FACTS[h])) for h in handles),
                authority=("PROJECT_OWNER",), statement="these xrefs contribute nothing to this region")
    base.update(kw)
    return OC.XrefScopeClaim(**base)


def missing(h, facts=None):
    return {"code": "XREF_CONTENT_NOT_IN_SOURCE", "obs_id": f"D2:{h}", "layer": "X", "path": [h],
            "xref": facts if facts is not None else FACTS[h]}


def test_xref_claim_applies_only_to_the_exact_occurrences_in_the_selected_region():
    i = H.inp(H.box(1, 0, 0, 500, 400), texts=[H.text(5, "A", 100, 100)])
    r = run(i, unrealised=[missing("501")], xref_claims=[xref_claim(i, ["501"])])
    assert r["unrealised"]["blocking_input"] == [] and r["sites"][0]["status"] == T.CERTIFIED
    rec = r["unrealised"]["recorded"][0]
    assert rec["disposition"] == OC.XREF_MISSING_OWNER_CONFIRMED_NONCONTRIBUTING and rec["claim"] == "OWNER-XREF@v1"
    other = H.inp(H.box(1, 0, 0, 500, 400), texts=[H.text(5, "A", 100, 100)], region_id="R2")
    r = run(other, unrealised=[missing("501")], xref_claims=[xref_claim(i, ["501"])])
    assert r["unrealised"]["blocking_input"][0]["disposition"] == OC.XREF_MISSING_POTENTIALLY_CONTRIBUTING


def test_another_missing_xref_still_blocks():
    i = H.inp(H.box(1, 0, 0, 500, 400), texts=[H.text(5, "A", 100, 100)])
    r = run(i, unrealised=[missing("501"), missing("502")], xref_claims=[xref_claim(i, ["501"])])
    assert [b["obs_id"] for b in r["unrealised"]["blocking_input"]] == ["D2:502"]
    assert r["sites"][0]["status"] == T.REVIEW_REQUIRED
    assert OC.XREF_MISSING_POTENTIALLY_CONTRIBUTING in r["sites"][0]["issues"]


def test_xref_claim_needs_the_same_source_facts_of_the_occurrence():
    i = H.inp(H.box(1, 0, 0, 500, 400), texts=[H.text(5, "A", 100, 100)])
    moved = dict(FACTS["501"], insert=[10.0, 0.0])
    r = run(i, unrealised=[missing("501", moved)], xref_claims=[xref_claim(i, ["501"])])
    assert OC.OCCURRENCE_FACTS_MISMATCH in r["unrealised"]["blocking_input"][0]["why"]


def test_xref_claim_does_not_delete_provenance():
    i = H.inp(H.box(1, 0, 0, 500, 400), texts=[H.text(5, "A", 100, 100)])
    u = missing("501")
    r = run(i, unrealised=[u], xref_claims=[xref_claim(i, ["501"])])
    kept = r["unrealised"]["recorded"]
    assert len(kept) == 1 and kept[0]["obs_id"] == u["obs_id"] and kept[0]["xref"] == FACTS["501"]


def test_xref_four_state_model():
    i = H.inp(H.box(1, 0, 0, 500, 400), texts=[H.text(5, "A", 100, 100)], )
    i = replace(i, notes={"clip_bounds": [0.0, 0.0, 600.0, 500.0]})
    facts = dict(FACTS, **{"503": dict(FACTS["502"], handle="503"), "504": dict(FACTS["502"], handle="504")})
    u = [missing("501"), dict(missing("502"), extent=[5000.0, 5000.0, 5100.0, 5100.0], extent_basis="TEST"),
         missing("503", facts["503"])]
    r = run(i, unrealised=u, xref_claims=[xref_claim(i, ["501"])])
    inv = OC.xref_inventory(facts, r["unrealised"])
    assert {h: v["state"] for h, v in inv.items()} == {
        "501": OC.XREF_MISSING_OWNER_CONFIRMED_NONCONTRIBUTING, "502": OC.XREF_MISSING_BUT_PROVEN_OUTSIDE_REGION,
        "503": OC.XREF_MISSING_POTENTIALLY_CONTRIBUTING, "504": OC.XREF_PRESENT_AND_ADMITTED}
    assert [h for h, v in inv.items() if not v["continues"]] == ["503"]
    assert r["sites"][0]["status"] == T.REVIEW_REQUIRED                      # only three of four states continue


def test_there_is_no_generic_ignore_xref_setting():
    import inspect
    src = inspect.getsource(OC) + inspect.getsource(RT)
    assert "IGNORE_XREF" not in src.replace("no generic IGNORE_XREF", "")
