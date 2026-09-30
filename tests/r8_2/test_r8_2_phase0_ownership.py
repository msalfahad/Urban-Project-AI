"""R8.2 Phase 0 — ownership is established by the source or the entity is UNPLACED (§1, §22),
plus the finding impact model (§2) and source conservation (§21).
"""

from __future__ import annotations

import copy

import pytest

from engine.source import findings as F
from engine.source.cad import kernel, libredwg_map as L
from engine.source.conservation import conservation
from tests.r8_0 import libredwg_builder as B, scenes as S

LINE = {"kind": "LINE", "a": (0, 0), "b": (10, 0)}


def _line_row(dec):
    return next(o for o in dec["OBJECTS"] if o.get("entity") == "LINE")


def _header(dec, name):
    return next(o for o in dec["OBJECTS"] if o.get("type") == 49 and o.get("name") == name)


def realise(dec):
    doc = L.to_document(dec)
    return doc, kernel.realise(doc)


# ---------------------------------------------------------------- the eight owner cases

def test_valid_model_space_owner_by_ownerhandle():
    doc, rg = realise(B.build({"entities": [LINE]}))
    assert len(doc.entities) == 1 and rg.segments and not doc.unplaced


def test_valid_model_space_owner_by_entmode_and_owner_list_without_ownerhandle():
    """How every real R2004 decode stores model space: no ownerhandle, entmode 2,
    listed by *MODEL_SPACE."""
    dec = B.build({"entities": [LINE]})
    row = _line_row(dec)
    del row["ownerhandle"]
    row["entmode"] = 2
    _header(dec, "*MODEL_SPACE")["entities"] = [[3, 1, row["handle"][-1], row["handle"][-1]]]
    doc, rg = realise(dec)
    assert len(doc.entities) == 1 and len(rg.segments) == 1
    assert ("owner", "MODEL", str(_header(dec, "*MODEL_SPACE")["handle"][-1])) in doc.entities[0].provenance


def test_valid_block_owner():
    doc, rg = realise(B.build({"blocks": {"CURVES": S.CURVES_BLOCK}, "entities": [S._insert("CURVES")]}))
    assert sum(len(b.entities) for b in doc.blocks.values()) == 3 and sorted(a.source for a in rg.arcs) == ["ARC", "BULGE"]


def test_valid_paper_space_owner_is_retained_not_realised():
    dec = B.build({"entities": [LINE]})
    dec["OBJECTS"].append({"object": "BLOCK_HEADER", "type": 49, "handle": [0, 1, 800], "name": "*Paper_Space"})
    dec["OBJECTS"].append({"entity": "LINE", "type": 19, "handle": [0, 1, 801], "ownerhandle": [4, 1, 800, 800],
                           "entmode": 1, "start": [0, 0, 0], "end": [5, 0, 0]})
    doc, rg = realise(dec)
    assert len(doc.other_layouts) == 1 and len(rg.segments) == 1 and rg.dispositions["OTHER_LAYOUT"] == 1


def test_missing_owner_evidence_is_unplaced():
    dec = B.build({"entities": [LINE]})
    del _line_row(dec)["ownerhandle"]
    doc, rg = realise(dec)
    assert [u.reason for u in doc.unplaced] == ["NO_OWNER_EVIDENCE"] and rg.segments == []


def test_unknown_owner_handle_is_unplaced_with_its_raw_owner_kept():
    dec = B.build({"entities": [LINE]})
    _line_row(dec)["ownerhandle"] = [4, 1, 424242, 424242]
    doc, rg = realise(dec)
    (u,) = doc.unplaced
    assert u.reason == "OWNER_HANDLE_UNKNOWN" and u.raw_owner == [4, 1, 424242, 424242]
    assert rg.segments == [] and rg.dispositions == {"UNPLACED": 1}
    f = next(f for f in rg.findings if f.code == F.OWNER_UNRESOLVED)
    assert f.obs_id == u.observation.obs_id and f.blocks_final and F.GEOMETRY in f.blocking_domains
    assert u.observation.source_handle in f.detail and "424242" in f.detail and u.observation.source_type in f.detail


def test_owner_is_an_insert_but_entity_is_not_an_attrib_is_unplaced():
    dec = B.build({"blocks": {"CURVES": S.CURVES_BLOCK}, "entities": [S._insert("CURVES")]})
    ins = next(o for o in dec["OBJECTS"] if o.get("entity") == "INSERT")
    dec["OBJECTS"].append({"entity": "LINE", "type": 19, "handle": [0, 1, 990], "ownerhandle": [4, 1, ins["handle"][-1], ins["handle"][-1]],
                           "start": [0, 0, 0], "end": [7, 0, 0]})
    doc, rg = realise(dec)
    assert [u.reason for u in doc.unplaced] == ["OWNER_IS_INSERT"]
    assert all(s.b != (7.0, 0.0) for s in rg.segments)


def test_nameless_block_header_is_placed_and_identity_flagged():
    dec = B.build({"blocks": {"CURVES": S.CURVES_BLOCK}, "entities": [S._insert("CURVES", at=(10.0, 0.0))]})
    h = _header(dec, "CURVES")
    h["name"], h["object"] = "", ""
    doc, rg = realise(dec)
    (f,) = [f for f in rg.findings if f.code == F.BLOCK_NAME_UNREADABLE]
    assert f.impacts == ((F.IDENTITY, F.REVIEW),) and not f.blocks_final       # geometry established
    assert rg.arcs[0].center == (1010.0, 0.0)


def test_nested_anonymous_block_identity_finding_per_instance_path():
    scene = {"blocks": {"*U5": {"entities": [LINE]},
                        "HOLDER": {"entities": [{"kind": "INSERT", "block": "*U5", "at": (100.0, 0.0)}]}},
             "entities": [{"kind": "INSERT", "block": "HOLDER", "at": (0.0, 0.0)},
                          {"kind": "INSERT", "block": "HOLDER", "at": (0.0, 500.0)}]}
    doc, rg = realise(B.build(scene))
    dyn = [f for f in rg.findings if f.code == F.DYNAMIC_BLOCK_UNRESOLVED]
    assert len(dyn) == 2 and {len(f.instance_path) for f in dyn} == {2}
    assert len({f.instance_path for f in dyn}) == 2
    assert all(f.severity_in(F.IDENTITY) == F.BLOCKING and f.severity_in(F.GEOMETRY) == F.REVIEW for f in dyn)
    assert len(rg.segments) == 2                                              # geometry still realised


# ---------------------------------------------------------------- conflicting / ambiguous evidence

def test_entmode_model_space_but_listed_by_a_block_is_a_conflict_not_a_guess():
    dec = B.build({"blocks": {"CURVES": S.CURVES_BLOCK}, "entities": [S._insert("CURVES"), LINE]})
    row = [o for o in dec["OBJECTS"] if o.get("entity") == "LINE" and o["end"][0] == 10.0][0]
    del row["ownerhandle"]
    row["entmode"] = 2
    _header(dec, "CURVES")["entities"] = [[3, 1, row["handle"][-1], row["handle"][-1]]]
    doc, rg = realise(dec)
    assert [u.reason for u in doc.unplaced] == ["OWNER_EVIDENCE_CONFLICT"]


def test_listed_by_two_headers_without_ownerhandle_is_ambiguous():
    dec = B.build({"blocks": {"A": {"entities": []}, "B2": {"entities": []}}, "entities": [LINE]})
    row = _line_row(dec)
    del row["ownerhandle"]
    for n in ("A", "B2"):
        _header(dec, n)["entities"] = [[3, 1, row["handle"][-1], row["handle"][-1]]]
    doc, _ = realise(dec)
    assert [u.reason for u in doc.unplaced] == ["OWNER_AMBIGUOUS"]


def test_relative_owner_reference_to_a_colliding_value_is_not_trusted_but_the_owner_list_is():
    """LibreDWG truncation: two objects share a printed value. A relative
    ownerhandle to that value cannot be trusted; the absolute owner list can."""
    dec = B.build({"blocks": {"CURVES": S.CURVES_BLOCK}, "entities": [S._insert("CURVES")]})
    blk = _header(dec, "CURVES")
    line = next(o for o in dec["OBJECTS"] if o.get("entity") == "LINE")
    twin = copy.deepcopy(line)
    twin["handle"] = [0, 3, blk["handle"][-1]]                # a truncated twin of the header's value
    twin["ownerhandle"] = [4, 1, 2, 2]
    dec["OBJECTS"].append(twin)
    line["ownerhandle"] = [12, 1, 7, blk["handle"][-1]]       # relative, value now ambiguous
    blk["entities"] = [[3, 1, line["handle"][-1], line["handle"][-1]]]
    doc, rg = realise(dec)
    assert not doc.unplaced
    assert any(o.obs_id == f"D1:{line['handle'][-1]}" for o in doc.blocks[f"H{blk['handle'][-1]}"].entities)
    assert "owner_note:OWNER_BY_HEADER_LIST" in doc.notes


def test_truncated_handles_get_distinct_identity_and_a_finding():
    dec = B.build({"entities": [LINE, {"kind": "LINE", "a": (0, 5), "b": (10, 5)}]})
    ls = [o for o in dec["OBJECTS"] if o.get("entity") == "LINE"]
    ls[1]["handle"] = [0, 3, ls[0]["handle"][-1]]
    doc, rg = realise(dec)
    assert len({o.obs_id for o in doc.entities}) == 2
    f = next(f for f in doc.findings if f.code == F.HANDLE_VALUE_TRUNCATED)
    assert f.impacts == ((F.IDENTITY, F.REVIEW), (F.SOURCE_COMPLETENESS, F.REVIEW))


def test_unplaced_unsupported_object_keeps_its_content_finding():
    dec = B.build({"entities": [LINE]})
    dec["OBJECTS"].append({"entity": "OLE2FRAME", "type": 74, "handle": [0, 1, 998], "ownerhandle": [4, 1, 5555, 5555]})
    _, rg = realise(dec)
    codes = [f.code for f in rg.findings]
    assert F.OWNER_UNRESOLVED in codes and F.SKIPPED in codes


# ---------------------------------------------------------------- impact model

def test_every_finding_code_declares_its_impacts():
    codes = [v for k, v in vars(F).items() if k.isupper() and isinstance(v, str) and k not in
             ("INFO", "REVIEW", "BLOCKING") and v not in F.DOMAINS]
    for c in codes:
        assert c in F.IMPACTS, c


@pytest.mark.parametrize("code,domain,sev", [
    (F.FRAME_UNREADABLE, F.GEOMETRY, F.BLOCKING),
    (F.BLOCK_NAME_UNREADABLE, F.IDENTITY, F.REVIEW),
    (F.DYNAMIC_BLOCK_IDENTITY_UNVERIFIED, F.IDENTITY, F.BLOCKING),
    (F.DYNAMIC_BLOCK_IDENTITY_UNVERIFIED, F.GEOMETRY, F.INFO),
    (F.NON_UNIFORM_SCALE_CURVE, F.GEOMETRY, F.INFO),
    (F.NON_UNIFORM_SCALE_CURVE, F.DOWNSTREAM_SUPPORT, F.REVIEW),
    (F.XREF_NOT_RESOLVED, F.SOURCE_COMPLETENESS, F.BLOCKING),
    (F.OWNER_UNRESOLVED, F.GEOMETRY, F.BLOCKING),
    (F.SKIPPED, F.DOCUMENT_CONTENT, F.BLOCKING),
])
def test_impact_domains_say_what_is_uncertain(code, domain, sev):
    assert F.SourceFinding(code).severity_in(domain) == sev


def test_blocks_final_is_only_the_compatibility_view():
    assert F.SourceFinding(F.BLOCK_NAME_UNREADABLE).blocks_final is False
    assert F.SourceFinding(F.XREF_NOT_RESOLVED).blocks_final is True
    assert F.SourceFinding(F.NON_UNIFORM_SCALE_CURVE).blocks_final is False


def test_explicit_impacts_override_and_are_validated():
    f = F.SourceFinding(F.CUSTOM_CLASS, impacts=((F.PRESENTATION, F.REVIEW),))
    assert f.impacts == ((F.PRESENTATION, F.REVIEW),) and not f.blocks_final
    with pytest.raises(ValueError):
        F.SourceFinding(F.CUSTOM_CLASS, impacts=(("NOT_A_DOMAIN", F.REVIEW),))
    with pytest.raises(KeyError):
        F.SourceFinding("NOT_A_CODE")


# ---------------------------------------------------------------- conservation

ALL = {c[1]: c for c in S.CURVE_CASES + S.BASE_POINT_CASES + S.MINSERT_CASES + S.XREF_CASES + S.SKIP_CASES}


@pytest.mark.parametrize("sid", sorted(ALL))
def test_conservation_balances_on_every_fixture(sid):
    from tests.r8_0.k1_harness import apply_test_schema_extensions
    dec = B.build(ALL[sid][3])
    doc = apply_test_schema_extensions(dec, L.to_document(dec))
    c = conservation(doc, kernel.realise(doc))
    assert c["source_level"]["BALANCED"] and c["observation_level"]["BALANCED"] and c["visit_level"]["BALANCED"]
    assert c["unique_obs_ids"]


def test_conservation_counts_unplaced_and_unreferenced_definitions():
    dec = B.build({"blocks": {"UNUSED": {"entities": [LINE]}}, "entities": [LINE]})
    dec["OBJECTS"].append({"entity": "LINE", "type": 19, "handle": [0, 1, 991], "ownerhandle": [4, 1, 777, 777],
                           "start": [0, 0, 0], "end": [1, 0, 0]})
    doc, rg = realise(dec)
    c = conservation(doc, rg)
    assert c["source_level"]["UNPLACED"] == 1 and c["observation_level"]["UNREFERENCED_DEFINITION"] == 1
    assert c["source_level"]["BALANCED"] and c["observation_level"]["BALANCED"]


def test_conservation_detects_a_dropped_row():
    dec = B.build({"entities": [LINE]})
    doc, rg = realise(dec)
    c = conservation(doc, rg, raw_entity_rows=doc.notes["raw_entity_rows"] + 1)
    assert c["source_level"]["BALANCED"] is False
