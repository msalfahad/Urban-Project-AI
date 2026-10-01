"""R8.9 §4-§8, §25-§26: role candidate vs authority, layer-only exclusion answerable to its consequence,
source-scoped claims, building-assembly occurrences, stubs and obstacle interiors."""

from __future__ import annotations

from engine.source import canonical_input as CI, geometry_role as GR, role_authority as RA, room_topology as RT
from engine.source import topology as T
from tests.r8_8 import helpers as H

LABELS = [H.text(5, "BED.ROOM", 250, 200), H.text(6, "BATH", 750, 200)]


def run(parts, texts=(), **kw):
    return RT.run(H.inp(parts, texts=texts), frame_insert=None, **kw)


def outer(h0=100):
    return [H.seg(h0, 0, 0, 1000, 0), H.seg(h0 + 1, 1000, 0, 1000, 400), H.seg(h0 + 2, 1000, 400, 0, 400),
            H.seg(h0 + 3, 0, 400, 0, 0)]


# ------------------------------------------------------------------------------- candidate is not authority
def test_a_floating_wall_layer_line_is_a_candidate_not_a_boundary_and_blocks_its_site():
    stray = H.seg(50, 200, 150, 300, 150)                                   # on WALL, touches nothing
    r = run(H.box(1, 0, 0, 500, 400) + [stray], [H.text(5, "A", 100, 100)])
    key = stray.identity.key
    assert r["roles"]["grades"][key]["grade"] == RA.CANDIDATE
    assert key not in {x for s in r["sites"] for x in s["boundary_source_ids"]}
    (s,) = r["sites"]
    assert key in s["blocked_by"] and s["status"] == T.REVIEW_REQUIRED


def test_a_badly_placed_furniture_line_on_a_wall_layer_cannot_silently_split_a_room():
    # one end on the wall, the other free: a stub - it can never split; it is not a perimeter either
    nib = H.seg(51, 250, 0, 250, 150)
    r = run(H.box(1, 0, 0, 500, 400) + [nib], [H.text(5, "A", 100, 100)])
    (s,) = r["sites"]
    assert r["roles"]["grades"][nib.identity.key]["grade"] == RA.STUB
    assert nib.identity.key in s["interior_stub_source_ids"] and abs(s["area"] - 500 * 400) < 1e-6
    assert abs(s["boundary_perimeter"] - 1800) < 1e-9 and s["perimeter"] > s["boundary_perimeter"]


def test_connected_single_line_partition_is_admitted_with_network_grade():
    r = run(H.two_rooms(), LABELS)
    assert all(s["authority_grade"] == RA.NETWORK and s["status"] == T.CERTIFIED for s in r["sites"])


# ------------------------------------------------------------------------------- layer-only exclusion
def test_a_dimension_layer_line_closing_two_labelled_rooms_is_a_role_conflict_not_silence():
    parts = outer() + [H.seg(104, 500, 0, 500, 400, layer="DIM")]
    r = run(parts, LABELS)
    (s,) = r["sites"]                                                       # the DIM line is excluded ...
    assert RA.ROLE_CONFLICT_SEPARATOR in s["issues"] and s["physical_status"] == T.REVIEW_REQUIRED
    assert s["consequence"]["exclusion"]["effect"] == "SEPARATES_LABELS"     # ... and its consequence is stated


def test_the_silent_case_one_label_and_an_unlabelled_closet_is_caught_too():
    parts = outer() + [H.seg(104, 500, 0, 500, 400, layer="DIM")]
    r = run(parts, [H.text(5, "BED.ROOM", 250, 200)])                       # one label only
    (s,) = r["sites"]
    assert RA.ROLE_CONFLICT_SEPARATOR in s["issues"] and s["consequence"]["exclusion"]["effect"] == "CHANGES_AREA"


def test_a_dimension_line_that_does_not_bridge_the_network_is_harmless():
    parts = outer() + [H.seg(104, 500, 50, 500, 350, layer="DIM")]          # floating dimension line
    r = run(parts, LABELS)
    (s,) = r["sites"]
    assert RA.ROLE_CONFLICT_SEPARATOR not in s["issues"]


def test_furniture_against_walls_is_a_trade_note_and_two_labels_stay_review():
    counter = H.seg(60, 0, 60, 300, 60, layer="FURNITURE")                  # wall to ... nothing: no bridge
    wardrobe = [H.seg(61, 0, 340, 200, 340, layer="FURNITURE"), H.seg(62, 200, 340, 200, 400, layer="FURNITURE")]
    r = run(H.box(1, 0, 0, 500, 400) + [counter] + wardrobe, [H.text(5, "A", 100, 200)])
    (s,) = r["sites"]
    assert s["issues"] == [] and s.get("trade_notes") == [RA.FIXED_OBJECT_AGAINST_BOUNDARY]


def test_unknown_geometry_that_cannot_change_a_site_leaves_the_physical_site_certified():
    stray = H.seg(70, 100, 100, 200, 100, layer="MYSTERY")                  # unknown, dangling inside
    r = run(H.box(1, 0, 0, 500, 400) + [stray], [H.text(5, "A", 300, 300)])
    (s,) = r["sites"]
    assert s["physical_status"] == T.CERTIFIED and s["issues"] == [RA.UNKNOWN_OBJECT_IN_SITE]
    closed = [H.seg(71 + i, *xy) for i, xy in enumerate([(100, 100, 200, 100), (200, 100, 200, 200),
                                                          (200, 200, 100, 200), (100, 200, 100, 100)])]
    closed = [H.seg(71 + i, *g.geometry, layer="MYSTERY") for i, g in enumerate(closed)]
    r = run(H.box(1, 0, 0, 500, 400) + closed, [H.text(5, "A", 300, 300)])
    (s,) = r["sites"]                                                       # a closed unknown outline could be a column
    assert T.TOPOLOGY_ROLE_UNRESOLVED in s["physical_issues"]


# ------------------------------------------------------------------------------- source-scoped claims
def _claim(rev_id, sha, review=RA.REVIEWED, layer="FIRNTUR", role=GR.FURNITURE, **kw):
    return RA.SourceLayerRoleClaim("C-1", rev_id, sha, layer, "EFFECTIVE", role, ("evidence",), "SOURCE_STRUCTURE",
                                   review, **kw)


def test_a_source_scoped_layer_claim_applies_only_to_its_own_source():
    parts = H.box(1, 0, 0, 500, 400) + [H.seg(80, 100, 100, 200, 100, layer="FIRNTUR")]
    inp = H.inp(parts, texts=[H.text(5, "A", 300, 300)])
    mine = _claim(H.REV, inp.revision.anchor_sha256)
    r = RT.run(inp, frame_insert=None, claims=[mine])
    a = r["roles"]["roles"][parts[-1].identity.key]
    assert a.role == GR.FURNITURE and a.rule_id == "CLAIM:C-1" and r["sites"][0]["status"] == T.CERTIFIED
    other_rev = _claim("REV_OTHER", inp.revision.anchor_sha256)
    other_sha = _claim(H.REV, "b" * 64)                                    # same id, another anchor: another file
    for c in (other_rev, other_sha):
        r = RT.run(inp, frame_insert=None, claims=[c])
        assert r["roles"]["roles"][parts[-1].identity.key].role == GR.UNKNOWN_PHYSICAL
        assert r["roles"]["claims"][0]["applies"] is False


def test_a_candidate_claim_never_changes_a_role_and_inheritance_must_be_explicit():
    parts = H.box(1, 0, 0, 500, 400) + [H.seg(80, 100, 100, 200, 100, layer="FIRNTUR")]
    inp = H.inp(parts)
    cand = _claim(H.REV, inp.revision.anchor_sha256, review=RA.SOURCE_EVIDENCE_CANDIDATE)
    assert RT.run(inp, frame_insert=None, claims=[cand])["roles"]["roles"][parts[-1].identity.key].role == \
        GR.UNKNOWN_PHYSICAL
    other = CI.SourceRevision("REV_B", CI.EXACT_SOURCE, "c" * 64, None, "T")
    inherited = _claim(H.REV, "a" * 64, inherits_to=(("REV_B", "c" * 64),))
    assert RA.claim_applies(inherited, other)[0] is True
    assert RA.claim_applies(_claim(H.REV, "a" * 64), other)[0] is False


def test_a_claim_changes_role_authority_only_never_geometry():
    parts = H.box(1, 0, 0, 500, 400) + [H.seg(80, 100, 100, 200, 100, layer="FIRNTUR")]
    inp = H.inp(parts)
    r = RT.run(inp, frame_insert=None, claims=[_claim(H.REV, inp.revision.anchor_sha256)])
    assert [p.geometry for p in inp.parts] == [p.geometry for p in parts]
    assert r["sites"][0]["area"] == 500 * 400


# ------------------------------------------------------------------------------- occurrence contexts
def test_a_building_assembly_occurrence_admits_its_wall_children():
    walls = H.box(1, 0, 0, 500, 400, path=("20",))
    tag = H.text(9, "LIVING", 250, 200, path=("20",))                     # room-label child: corroboration
    r = RT.run(H.inp(walls, texts=[tag]), frame_insert=None)
    assert r["roles"]["occurrence_contexts"]["20"]["context"] == RA.BUILDING_ASSEMBLY
    (s,) = r["sites"]
    assert s["status"] == T.CERTIFIED and abs(s["area"] - 500 * 400) < 1e-6
    assert {a.rule_id for k, a in r["roles"]["roles"].items()} == {"GR-05/GR-17"}


def test_a_symbol_occurrence_with_wall_children_and_no_corroboration_fails_closed():
    walls = H.box(1, 0, 0, 500, 400, path=("20",))
    r = RT.run(H.inp(walls, texts=[H.text(9, "LIVING", 250, 200)]), frame_insert=None)
    assert r["roles"]["occurrence_contexts"]["20"]["context"] == RA.UNKNOWN_OCC
    assert {a.role for a in r["roles"]["roles"].values()} == {GR.UNKNOWN_PHYSICAL}
    assert not [s for s in r["sites"] if s["status"] == T.CERTIFIED]


def test_furniture_block_stays_a_symbol_occurrence():
    sofa = H.box(1, 100, 100, 200, 150, layer="FURNITURE", path=("30",))
    r = RT.run(H.inp(H.box(10, 0, 0, 500, 400) + sofa, texts=[H.text(9, "A", 300, 300)]), frame_insert=None)
    assert r["roles"]["occurrence_contexts"]["30"]["context"] == RA.SYMBOL
    assert {r["roles"]["roles"][p.identity.key].role for p in sofa} == {GR.FURNITURE}


# ------------------------------------------------------------------------------- determinism
def test_same_fixture_same_first_run():
    a = run(outer() + [H.seg(104, 500, 0, 500, 400, layer="DIM")], LABELS)
    b = run(outer() + [H.seg(104, 500, 0, 500, 400, layer="DIM")], LABELS)
    assert [T.public(s) for s in a["sites"]] == [T.public(s) for s in b["sites"]]
