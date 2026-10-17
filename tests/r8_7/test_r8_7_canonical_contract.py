"""R8.7 CANONICAL_MEASUREMENT_INPUT on synthetic inputs: every declared field fails closed when absent,
duplicated, cross-revision or unresolved; identity is source-derived; region membership is per occurrence."""

from __future__ import annotations

from dataclasses import replace

from engine.source import canonical_build as CB, canonical_input as CI

REV = CI.SourceRevision("REV_A", CI.EXACT_SOURCE, "a" * 64)
OTHER = CI.SourceRevision("REV_B", CI.DERIVED_PENDING_SOURCE, "b" * 64)
STEP = CI.LineageStep("10", "11", "BLOCK")
CONTRACT = CI.MethodContract(
    "TEST_METHOD", "1", input_fields=("revision", "region_id", "unit_native_to_mm", "unit_claim_id"),
    part_fields=("source_revision_id", "source_handle", "instance_path", "block_identity", "source_part_id", "part_index",
                 "layer", "visibility", "curve_kind", "geometry"),
    text_fields=("text_identity", "text_value", "world_placement", "visibility"),
    dimension_fields=("dimension_identity", "placed_points", "measurement", "user_text", "dimlfac"),
    declared_exclusions={"ELLIPTICAL_ARC": "not consumed"})


def part(h="1", path=("10",), idx=0, rev="REV_A", lineage=(STEP,), kind="SEGMENT", geom=(0.0, 0.0, 1.0, 0.0), **kw):
    return CI.CanonicalPart(CI.SourceIdentity(rev, h, path, kind, idx), kind, geom, kw.pop("layer", "WALL"),
                            kw.pop("visibility", CI.VISIBLE), lineage, entity_type="LINE")


def text(x=0.5, y=0.5, value="ROOM", rev="REV_A"):
    return CI.PlacedText(CI.SourceIdentity(rev, "5", (), "TEXT", 0), value, x, y, 1.0, "TEXT", CI.VISIBLE, ())


def dim(pts=((0.0, 0.0), (1.0, 0.0)), m=1.0, rev="REV_A"):
    return CI.PlacedDimension(CI.SourceIdentity(rev, "7", (), "DIMENSION", 0), pts, pts, m, "", 1.0, "21", "DIM",
                              CI.VISIBLE, ())


def inp(parts=None, texts=None, dims=None, **kw):
    base = dict(revision=REV, region_id="R1", frame_id="F1", unit_native_to_mm=10.0, unit_claim_id="C1")
    base.update(kw)
    return CI.CanonicalMeasurementInput(parts=tuple(parts if parts is not None else [part(), part(h="2", idx=0)]),
                                        texts=tuple(texts if texts is not None else [text()]),
                                        dimensions=tuple(dims if dims is not None else [dim()]), **base)


def state(i, **kw):
    return CI.validate(i, CONTRACT, **kw)


def test_complete_input_is_complete():
    v = state(inp(), expected_revision_id="REV_A", selected_region_id="R1")
    assert v["state"] == CI.COMPLETE and not v["missing_fields"] and not v["ambiguous_fields"]


def test_missing_block_identity_fails_closed():
    v = state(inp(parts=[part(lineage=())]))
    assert v["state"] == CI.METHOD_INPUT_INCOMPLETE and v["missing_fields"]["parts.block_identity"] == 1
    v = state(inp(parts=[part(lineage=(CI.LineageStep("10", None, "BLOCK"),))]))      # block record handle missing
    assert v["state"] == CI.METHOD_INPUT_INCOMPLETE and "parts.block_identity" in v["missing_fields"]
    v = state(inp(parts=[part(lineage=(CI.LineageStep("99", "11", "BLOCK"),))]))      # lineage contradicts the path
    assert v["state"] == CI.METHOD_INPUT_INCOMPLETE and "parts.block_identity" in v["ambiguous_fields"]


def test_a_block_name_alone_is_not_block_identity():
    v = state(inp(parts=[part(lineage=(CI.LineageStep("10", "", "BLOCK"),))]))
    assert v["state"] == CI.METHOD_INPUT_INCOMPLETE


def test_missing_and_duplicate_part_identity_fail_closed():
    v = state(inp(parts=[part(idx=None)]))
    assert v["state"] == CI.METHOD_INPUT_INCOMPLETE and "parts.source_part_id" in v["missing_fields"]
    v = state(inp(parts=[part(), part()]))                                              # the same identity twice
    assert v["state"] == CI.METHOD_INPUT_INCOMPLETE and v["ambiguous_fields"]["parts.source_part_id"] == 2


def test_missing_text_placement_fails_closed_only_when_required():
    assert state(inp(texts=[text(x=None)]))["state"] == CI.METHOD_INPUT_INCOMPLETE
    no_text = replace(CONTRACT, text_fields=())
    assert CI.validate(inp(texts=[text(x=None)]), no_text)["state"] == CI.COMPLETE


def test_missing_dimension_evidence_fails_closed_when_required():
    assert state(inp(dims=[dim(pts=None)]))["missing_fields"]["dimensions.placed_points"] == 1
    assert state(inp(dims=[dim(m=None)]))["state"] == CI.METHOD_INPUT_INCOMPLETE
    assert CI.validate(inp(dims=[dim(pts=None)]), replace(CONTRACT, dimension_fields=()))["state"] == CI.COMPLETE


def test_unresolved_visibility_fails_closed_when_relevant():
    i = inp(parts=[part(visibility=CI.VISIBILITY_UNRESOLVED)])
    assert state(i)["state"] == CI.METHOD_INPUT_INCOMPLETE and state(i)["visibility_unresolved"] == {
        "parts": {CI.VISIBILITY_UNRESOLVED: 1}}
    assert state(inp(parts=[part(visibility=CI.HIDDEN_DYNAMIC_STATE)]))["state"] == CI.METHOD_INPUT_INCOMPLETE
    assert CI.validate(i, replace(CONTRACT, visibility_relevant=False))["state"] == CI.COMPLETE


def test_revision_mismatch_and_mixed_records_fail_closed():
    assert state(inp(), expected_revision_id="REV_B")["state"] == CI.SOURCE_REVISION_MISMATCH
    mixed = inp(parts=[part(), part(h="2", rev="REV_B")])
    v = state(mixed)
    assert v["state"] == CI.SOURCE_REVISION_MISMATCH and v["revision_conflicts"][0]["record_revision"] == "REV_B"
    assert state(inp(texts=[text(rev="REV_B")]))["state"] == CI.SOURCE_REVISION_MISMATCH


def test_wrong_plan_variant_fails_closed():
    assert state(inp(region_id="R3"), selected_region_id="R1")["state"] == CI.REGION_NOT_SELECTED


def test_missing_input_fields_fail_closed():
    assert state(inp(unit_claim_id=None))["missing_fields"] == {"input.unit_claim_id": 1}
    assert state(inp(revision=None))["state"] == CI.METHOD_INPUT_INCOMPLETE


def test_declared_exclusion_is_counted_and_an_undeclared_kind_fails():
    # SUPERSEDED IN R8.8 (decision R88-D05): a bare declared exclusion carries no authority and now fails closed;
    # the same part is excluded only through a MethodExclusion whose allowed role it positively carries.
    ell = part(h="9", kind="ELLIPTICAL_ARC", geom=(0, 0, 1, 0, 0, 1, 0, 1))
    v = state(inp(parts=[part(), ell]))
    assert v["state"] == CI.METHOD_INPUT_INCOMPLETE
    assert v["exclusion_without_authority"] == {"ELLIPTICAL_ARC:BARE_DECLARATION": 1}
    ex = CI.MethodExclusion("ELLIPTICAL_ARC", "TEST", "not consumed", "test", ("OPENING_SYMBOL",))
    c2 = replace(CONTRACT, declared_exclusions={}, exclusions=(ex,))
    role = type("A", (), {"role": "OPENING_SYMBOL"})()
    v = CI.validate(inp(parts=[part(), ell]), c2, roles={ell.identity.key: role})
    assert v["state"] == CI.COMPLETE and v["excluded_by_declaration"] == {"ELLIPTICAL_ARC": 1}
    spline = part(h="9", kind="SPLINE", geom=(0, 0))
    assert state(inp(parts=[part(), spline]))["unsupported_part_kinds"] == {"SPLINE": 1}


def test_guarded_measure_never_calls_the_method_on_an_incomplete_input():
    called = []
    r = CI.guarded_measure(inp(parts=[part(idx=None)]), CONTRACT, lambda i: called.append(1) or 42)
    assert r["quantity"] is None and r["state"] == CI.METHOD_INPUT_INCOMPLETE and called == []
    assert CI.guarded_measure(inp(), CONTRACT, lambda i: 42)["quantity"] == 42


def test_identity_is_source_derived_and_revision_specific():
    a, b = part(), part(rev="REV_B")
    assert a.identity.key == "REV_A|H1|10|SEGMENT|0" and a.identity.key != b.identity.key
    moved = part(geom=(5.0, 5.0, 6.0, 5.0))                                             # same source, other coordinates
    assert moved.identity.key == a.identity.key                                          # coordinates never identify
    assert CI.SourceIdentity("R", "1", None, "SEGMENT", 0).key is None                   # never a partial key
    assert CI.SourceIdentity("R", "1", (), "SEGMENT", 0).key == "R|H1||SEGMENT|0"         # model space is a real path


def test_region_membership_is_per_occurrence():
    inside, outside = part(h="1", geom=(1, 1, 2, 1)), part(h="2", geom=(50, 1, 60, 1))   # same insert occurrence 10
    i = CB.assemble(REV, "R1", (0, 0, 10, 10), "F1", 10.0, "C1", [inside, outside], [text()], [dim()])
    assert len(i.region_review) == 2 and not i.parts                                     # never cut in two
    assert CI.validate(i, CONTRACT)["state"] == CI.METHOD_INPUT_INCOMPLETE
    whole = CB.assemble(REV, "R1", (0, 0, 100, 10), "F1", 10.0, "C1", [inside, outside], [text()], [dim()])
    assert len(whole.parts) == 2 and not whole.region_review
    top = [part(h="1", path=(), lineage=(), geom=(1, 1, 2, 1)), part(h="2", path=(), lineage=(), geom=(50, 1, 60, 1))]
    j = CB.assemble(REV, "R1", (0, 0, 10, 10), "F1", 10.0, "C1", top, [], [])
    assert len(j.parts) == 1 and j.notes["outside_region"] == {"parts": 1}               # separate entities: clean split
