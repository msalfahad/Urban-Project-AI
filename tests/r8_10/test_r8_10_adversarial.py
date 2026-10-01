"""R8.10 §21-§24: adversarial review of the R8.9 role-authority paths (NETWORK grade, consequence analysis, building-
assembly occurrences, room-tag families) and the near-miss silent-error path."""

from __future__ import annotations

from engine.source import canonical_input as CI, geometry_role as GR, role_authority as RA, room_topology as RT
from engine.source import text_role as TX, topology as T
from tests.r8_8 import helpers as H


def run(parts, texts=(), dims=(), **kw):
    return RT.run(H.inp(parts, texts=texts, dims=dims), frame_insert=None, **kw)


def outer(w=1000, h=400, h0=100):
    return [H.seg(h0, 0, 0, w, 0), H.seg(h0 + 1, w, 0, w, h), H.seg(h0 + 2, w, h, 0, h), H.seg(h0 + 3, 0, h, 0, 0)]


def net(r, part):
    return r["network_review"].get(part.identity.key, {}).get("state")


# ------------------------------------------------------------------------------- §21 NETWORK grade
def test_A_dimension_line_on_a_wall_layer_carrying_its_own_length_is_a_role_conflict():
    line = H.seg(50, 400, 0, 400, 400)                                      # WALL layer, wall to wall
    own = H.text(60, "4000", 410, 200, layer="TEXT")                         # 400 units x 10 mm, at its middle
    r = run(outer() + [line], [H.text(5, "BED.ROOM", 700, 200), own])
    assert net(r, line) == RA.NETWORK_ROLE_CONFLICT
    assert all(RA.NETWORK_ROLE_CONFLICT in s["issues"] for s in r["sites"])
    assert not [s for s in r["sites"] if s["status"] == T.CERTIFIED]


def test_a_real_wall_dimensioned_corner_to_corner_is_not_a_conflict():
    # R8.10 finding on the old Qortuba revision: real walls carry DIMENSION entities whose measured points coincide
    # with their ends; being measured is not being a dimension line
    wall = H.seg(56, 500, 0, 500, 400)
    d = H.dim(61, pts=((500.0, 0.0), (500.0, 400.0)), m=400.0)
    r = run(outer() + [wall], [H.text(5, "BED.ROOM", 200, 200), H.text(6, "BATH", 700, 200)], dims=[d])
    assert net(r, wall) == RA.NETWORK_BOUNDARY_ESTABLISHED
    assert all(s["status"] == T.CERTIFIED for s in r["sites"])


def test_a_length_text_far_from_the_line_is_not_self_dimensioning():
    line = H.seg(50, 400, 0, 400, 400)
    r = run(outer() + [line], [H.text(5, "BED.ROOM", 700, 200), H.text(60, "4000", 800, 200, layer="TEXT")])
    assert net(r, line) == RA.NETWORK_BOUNDARY_CANDIDATE


def test_A2_the_same_line_without_its_own_length_text_is_only_a_candidate_documented_residual():
    line = H.seg(50, 400, 0, 400, 400)
    r = run(outer() + [line], [H.text(5, "BED.ROOM", 700, 200)])
    assert net(r, line) == RA.NETWORK_BOUNDARY_CANDIDATE                  # recorded: labelled | unlabelled
    assert r["network_review"][line.identity.key]["evidence"] == {"labelled_sides": 1}


def test_B_furniture_edge_on_a_wall_layer_connected_at_both_ends_is_a_candidate_not_established():
    front = H.seg(51, 0, 340, 1000, 340)                                    # a wardrobe front, 600 from the wall
    r = run(outer() + [front], [H.text(5, "BED.ROOM", 500, 150)])
    assert net(r, front) == RA.NETWORK_BOUNDARY_CANDIDATE


def test_C_centreline_across_a_room_on_a_wall_layer_is_a_candidate():
    centre = H.seg(52, 500, 0, 500, 400)
    r = run(outer() + [centre], [H.text(5, "HALL", 200, 200)])
    assert net(r, centre) == RA.NETWORK_BOUNDARY_CANDIDATE


def test_D_short_bridging_line_between_wall_faces_is_a_candidate_with_its_consequence_stated():
    faces = [H.seg(10, 0, 400, 1000, 400), H.seg(11, 0, 420, 1000, 420), H.seg(12, 0, 0, 0, 420),
             H.seg(13, 0, 0, 1000, 0), H.seg(14, 1000, 0, 1000, 400)]
    cap = H.seg(53, 1000, 400, 1000, 420)
    r = run(faces + [cap], [H.text(5, "HALL", 500, 200)])
    # a cap between the two faces closes the wall band: it separates the band's interior from the OUTSIDE, never
    # one room from another, so it is not a NETWORK separator to review at all
    assert net(r, cap) is None
    assert {round(s["area"]) for s in r["sites"]} == {400000, 20000}


def test_E_duplicate_line_over_an_existing_wall_changes_nothing():
    base = run(outer() + [H.seg(54, 500, 0, 500, 400)], [H.text(5, "A", 200, 200), H.text(6, "B", 700, 200)])
    dup = run(outer() + [H.seg(54, 500, 0, 500, 400), H.seg(55, 500, 0, 500, 400)],
              [H.text(5, "A", 200, 200), H.text(6, "B", 700, 200)])
    assert sorted(round(s["area"], 6) for s in base["sites"]) == sorted(round(s["area"], 6) for s in dup["sites"])


def test_F_real_single_line_partition_between_two_labelled_rooms_is_established():
    wall = H.seg(56, 500, 0, 500, 400)
    r = run(outer() + [wall], [H.text(5, "BED.ROOM", 200, 200), H.text(6, "BATH", 700, 200)])
    assert net(r, wall) == RA.NETWORK_BOUNDARY_ESTABLISHED
    assert all(s["status"] == T.CERTIFIED for s in r["sites"]) and len(r["sites"]) == 2


# ------------------------------------------------------------------------------- §22 consequence is not authority
def test_consequence_analysis_never_admits_what_it_finds_material():
    line = H.seg(57, 500, 0, 500, 400, layer="DIM")
    r = run(outer() + [line], [H.text(5, "BED.ROOM", 200, 200), H.text(6, "BATH", 700, 200)])
    assert r["roles"]["roles"][line.identity.key].role == GR.DIMENSION_GRAPHICS
    (s,) = r["sites"]                                                       # still ONE site: the line is material
    assert s["consequence"]["exclusion"]["effect"] == "SEPARATES_LABELS"   # ... and that is all it establishes
    assert RA.ROLE_CONFLICT_SEPARATOR in s["issues"]


# ------------------------------------------------------------------------------- near-miss silent path
def core_room(cap_short=0.9, cap_layer="DIM"):
    """A 1000 x 400 room under a 20-unit wall band (y 400..420) whose face stops at x = 900; the band is meant to be
    capped at x = 900 but the cap stops `cap_short` units short of the outer face (unit = 10 mm: 0.9 = 9 mm)."""
    return [H.seg(10, 0, 0, 1000, 0), H.seg(11, 1000, 0, 1000, 420), H.seg(12, 1000, 420, 0, 420),
            H.seg(13, 0, 420, 0, 0), H.seg(14, 0, 400, 900, 400),
            H.seg(15, 900, 400, 900, 420 - cap_short, layer=cap_layer)]


def test_a_near_miss_cap_on_a_dimension_layer_no_longer_leaks_a_wall_core_silently():
    r = run(core_room(), [H.text(5, "HALL", 500, 200)])
    (s,) = [z for z in r["sites"] if z["labels"]]
    assert RA.NEAR_MISS_BOUNDARY_GAP in s["issues"] and s["status"] == T.REVIEW_REQUIRED
    assert s["near_miss"][0]["gaps_native"] == [0.9]
    assert abs(s["area"] - 1000 * 420) < 1e-6           # authority area untouched (room + leaked band): review only


def test_a_near_miss_wall_line_into_a_cavity_is_caught_too():
    r = run(core_room(cap_layer="WALL"), [H.text(5, "HALL", 500, 200)])
    (s,) = [z for z in r["sites"] if z["labels"]]
    assert RA.NEAR_MISS_BOUNDARY_GAP in s["issues"]


def test_beyond_the_review_band_a_gap_is_a_real_opening():
    r = run(core_room(cap_short=6.0), [H.text(5, "HALL", 500, 200)])     # 60 mm: a real (if narrow) opening
    (s,) = [z for z in r["sites"] if z["labels"]]
    assert RA.NEAR_MISS_BOUNDARY_GAP not in s["issues"]


def test_an_admitted_authored_gap_between_two_labelled_rooms_keeps_the_r8_8_contract():
    parts = outer() + [H.seg(104, 500, 0, 500, 399.5)]                     # 5 mm gap, unit 10 mm
    r = run(parts, [H.text(5, "A", 200, 200), H.text(6, "B", 700, 200)])
    assert len(r["sites"]) == 1 and r["sites"][0]["issues"] == [T.MULTIPLE_SEMANTIC_LABELS]


# ------------------------------------------------------------------------------- §23 building assemblies
def in_occ(parts, occ="20"):
    return [H.part(p.identity.source_handle, p.kind, p.geometry, layer=p.layer, path=(occ,)) for p in parts]


def ctx(r, occ="20"):
    return r["roles"]["occurrence_contexts"][occ]["context"]


def test_detail_callout_with_wall_like_lines_and_a_title_is_not_a_building_assembly():
    r = run(in_occ(H.box(1, 2000, 0, 2300, 300)), [H.text(9, "DETAIL A", 2150, 150, path=("20",), layer="TEXT")])
    assert ctx(r) == RA.UNKNOWN_OCC


def test_window_detail_with_linework_and_dimensions_is_not_a_building_assembly():
    d = [H.dim(70, pts=((2000.0, 0.0), (2300.0, 0.0)), m=300.0, path=("20",)),
         H.dim(71, pts=((2000.0, 0.0), (2000.0, 300.0)), m=300.0, path=("20",))]
    r = run(in_occ(H.box(1, 2000, 0, 2300, 300)), dims=d)
    assert ctx(r) == RA.UNKNOWN_OCC


def test_bathroom_fixture_block_with_a_label_is_a_symbol():
    r = run(outer() + in_occ(H.box(1, 100, 100, 160, 140, layer="SANITARY")),
            [H.text(9, "BATH", 130, 120, path=("20",))])
    assert ctx(r) == RA.SYMBOL


def test_room_detail_block_one_room_one_label_fails_closed():
    r = run(in_occ(H.box(1, 0, 0, 500, 400)), [H.text(9, "BEDROOM", 250, 200, path=("20",))])
    assert ctx(r) == RA.UNKNOWN_OCC
    assert not [s for s in r["sites"] if s["status"] == T.CERTIFIED]


def test_full_floor_plan_block_is_a_building_assembly_positive_control():
    r = run(in_occ(H.two_rooms()), [H.text(9, "BEDROOM", 250, 200, path=("20",)),
                                    H.text(10, "BATH", 750, 200, path=("20",))])
    assert ctx(r) == RA.BUILDING_ASSEMBLY
    assert len(r["sites"]) == 2 and all(s["status"] == T.CERTIFIED for s in r["sites"])


def test_bound_xref_floor_plan_is_a_building_assembly_positive_control():
    names = {"20": "XREF$0$SECOND FLOOR PLAN"}
    parts = [H.part(p.identity.source_handle, p.kind, p.geometry, path=("20",), names=names) for p in H.two_rooms()]
    texts = [H.text(9, "BEDROOM", 250, 200, path=("20",), names=names),
             H.text(10, "BATH", 750, 200, path=("20",), names=names)]
    r = run(parts, texts)
    assert ctx(r) == RA.BUILDING_ASSEMBLY


def test_an_assembly_whose_wall_children_close_no_cycle_is_not_a_building():
    loose = in_occ([H.seg(1, 0, 0, 500, 0), H.seg(2, 0, 100, 500, 100)])
    r = run(outer(w=2000, h=2000) + loose, [H.text(9, "BEDROOM", 250, 50, path=("20",)),
                                             H.text(10, "BATH", 250, 70, path=("20",))])
    assert ctx(r) == RA.UNKNOWN_OCC


# ------------------------------------------------------------------------------- §24 room tags
def tag(h, value, x, y, occ):
    return [H.text(h, value, x, y, path=(occ,), layer="TEXT"), H.text(h + 1, "x", x, y - 20, path=(occ,), layer="TEXT")]


FAMILY = tag(300, "HALL", 5000, 5000, "80") + tag(310, "KITCHEN", 5200, 5000, "81")


def test_document_texts_with_room_words_never_become_room_labels():
    for i, v in enumerate(("BATHROOM DETAIL", "BEDROOM FINISH NOTE", "MASTER BEDROOM CEILING DETAIL", "ROOM AREA",
                           "ROOM TYPE")):
        t = tag(400 + 10 * i, v, 250, 200, "9" + str(i))
        r = run(H.box(1, 0, 0, 500, 400), t + FAMILY)                     # even next to a real tag family
        role = r["roles"]["text_roles"][t[0].identity.key]
        assert role.role == TX.ROOM_LABEL_CANDIDATE and role.rule_id == "TR-06", v
        (s,) = r["sites"]
        assert s["labels"] == [] and TX.TEXT_ROLE_UNRESOLVED_IN_SITE in s["issues"], v


def test_vocabulary_alone_never_establishes_a_room_tag():
    t = tag(500, "BEDROOM", 250, 200, "95")
    r = run(H.box(1, 0, 0, 500, 400), t)
    assert r["roles"]["text_roles"][t[0].identity.key].rule_id == "TR-06"


def test_repeated_family_use_establishes_a_tag_positive_control():
    t = tag(500, "BEDROOM", 250, 200, "95")
    r = run(H.box(1, 0, 0, 500, 400), t + FAMILY)
    assert r["roles"]["text_roles"][t[0].identity.key].rule_id == "TR-03"
    assert r["sites"][0]["labels"] == ["I95"] and r["sites"][0]["status"] == T.CERTIFIED


def test_a_family_of_one_room_name_repeated_is_not_a_family():
    t = tag(500, "BEDROOM", 250, 200, "95") + tag(510, "BEDROOM", 5000, 5000, "96")
    r = run(H.box(1, 0, 0, 500, 400), t)
    assert r["roles"]["text_roles"][t[0].identity.key].rule_id == "TR-06"
