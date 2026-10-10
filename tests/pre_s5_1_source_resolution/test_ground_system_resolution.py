"""PRE-S5.1 decision rules (engine/source/ground_system_resolution.py) on synthetic evidence."""

from __future__ import annotations

import pytest

from engine.source import ground_system_resolution as GR

COND = {"P13-GB-GT5M": ("GT", 5.0), "P13-GB-LT5M": ("LT", 5.0), "P13-GB-LT2_5M": ("LT", 2.5)}
CLAUSE = ("P13-GB-GT5M", "P13-GB-LT5M")
EXT = "P13-GB-EXTERIOR"


def samples(spec, step=50.0):
    """spec: [(n_stations, element kind or None, exterior class or None, opening)]"""
    out = []
    for n, kind, ext, opening in spec:
        out += [{"len": step, "element": kind, "ext": ext, "opening": opening, "handle": kind}] * n
    return out


# ------------------------------------------------------------------------------------------- support faces / bar run
def test_support_face_to_face_run_is_the_lower_bound():
    r = GR.bar_run(centreline_mm=3000.0, clear_concrete_mm=2700.0, face_start=150.0, face_end=2850.0,
                   bar_lines=[{"offset_mm": -80, "run_mm": 2700.0, "misses": []},
                              {"offset_mm": 80, "run_mm": 2700.0, "misses": []}])
    assert r["SUPPORT_FACE_TO_FACE_RUN_MM"] == 2700.0 and r["BAR_STRAIGHT_RUN_LOWER_BOUND_MM"] == 2700.0
    assert r["LENGTH_STATE"] == "CONSISTENT" and r["BAR_RUN_STATE"] == "LOWER_BOUND"
    assert r["MEMBER_CENTERLINE_LENGTH_MM"] == 3000.0 and r["MEMBER_CLEAR_CONCRETE_LENGTH_MM"] == 2700.0


def test_oblique_support_takes_the_shortest_bar_line_not_a_basis_minimum():
    r = GR.bar_run(centreline_mm=3000.0, clear_concrete_mm=2700.0, face_start=100.0, face_end=2750.0,
                   bar_lines=[{"offset_mm": -80, "run_mm": 2570.0, "misses": []},
                              {"offset_mm": 80, "run_mm": 2730.0, "misses": []}])
    assert r["BAR_STRAIGHT_RUN_LOWER_BOUND_MM"] == 2570.0           # the acute-side bar, not min(clear, c/c)


def test_length_conflicts_withhold_the_run():
    # the concrete piece runs past the support centre (column narrower than the beam)
    r = GR.bar_run(centreline_mm=3750.0, clear_concrete_mm=3850.0, face_start=200.0, face_end=3550.0)
    assert r["LENGTH_STATE"] == "LENGTH_GEOMETRY_CONFLICT" and r["BAR_STRAIGHT_RUN_LOWER_BOUND_MM"] is None
    # face-to-face longer than the centreline
    r = GR.bar_run(centreline_mm=3000.0, clear_concrete_mm=3100.0, face_start=0.0, face_end=3100.0)
    assert r["BAR_RUN_STATE"] == "LENGTH_GEOMETRY_CONFLICT"
    # a bar line that misses its support
    r = GR.bar_run(centreline_mm=3000.0, clear_concrete_mm=2700.0, face_start=150.0, face_end=2850.0,
                   bar_lines=[{"offset_mm": 80, "run_mm": None, "misses": ["start"]}])
    assert r["LENGTH_STATE"] == "LENGTH_GEOMETRY_CONFLICT" and "misses" in r["ISSUES"][0]
    # every bar line longer than the concrete piece
    r = GR.bar_run(centreline_mm=3000.0, clear_concrete_mm=2400.0, face_start=150.0, face_end=2850.0)
    assert r["LENGTH_STATE"] == "LENGTH_GEOMETRY_CONFLICT"


def test_no_support_face_is_unresolved_not_a_guess():
    r = GR.bar_run(centreline_mm=None, clear_concrete_mm=1300.0, face_start=120.0, face_end=None)
    assert r["BAR_RUN_STATE"] == "BAR_RUN_GEOMETRY_UNRESOLVED" and r["BAR_STRAIGHT_RUN_LOWER_BOUND_MM"] is None


# ------------------------------------------------------------------------------------------- architectural overlay
def test_arch_exterior_overlay():
    w = GR.wall_relation(samples([(90, "MASONRY_200", "EXTERIOR", False), (10, None, None, True)]))
    assert w["RELATION"] == "UNDER_EXTERIOR_WALL" and w["OVERLAP_PERCENT"] == pytest.approx(1.0)
    assert w["WALL_LENGTH_MM"] == 4500.0 and w["OPENING_LENGTH_MM"] == 500.0


def test_partial_wall_overlap_is_ambiguous():
    w = GR.wall_relation(samples([(30, "MASONRY_200", "EXTERIOR", False), (70, None, None, False)]))
    assert w["RELATION"] == "AMBIGUOUS_WALL_RELATION" and "partial" in w["WHY"]
    assert GR.wall_relation(samples([(5, "GLAZING", "EXTERIOR", False), (95, None, None, False)]))["RELATION"] == \
        "NO_WALL_ABOVE"
    assert GR.wall_relation(samples([(60, None, None, True), (40, None, None, False)]))["RELATION"] == \
        "AMBIGUOUS_WALL_RELATION"                                       # openings alone are not a wall


def test_exterior_versus_interior_wall():
    assert GR.wall_relation(samples([(100, "MASONRY_150", "INTERIOR", False)]))["RELATION"] == "UNDER_INTERIOR_WALL"
    mixed = GR.wall_relation(samples([(50, "MASONRY_200", "EXTERIOR", False), (50, "MASONRY_200", "INTERIOR", False)]))
    assert mixed["RELATION"] == "AMBIGUOUS_WALL_RELATION" and "mixed" in mixed["WHY"]
    assert GR.side_pair_class("INSIDE", "OUTSIDE") == "EXTERIOR"
    assert GR.side_pair_class("INSIDE", "INSIDE") == "INTERIOR"
    assert GR.side_pair_class("OUTSIDE", "OUTSIDE") == "SITE_BOTH_OUTSIDE"
    assert GR.side_pair_class("INSIDE", "UNKNOWN") == "UNKNOWN_SIDE"


def test_architecture_decides_and_proxies_are_never_voted():
    a = GR.exterior_authority(relation="UNDER_INTERIOR_WALL", slab_edge="INTERNAL", zone_test=True,
                              footprint_test=True)
    assert a["AUTHORITY"] == "INTERIOR_SOURCE_VERIFIED" and a["PROXIES_AGREE_WITH_AUTHORITY"] is False
    a = GR.exterior_authority(relation="UNDER_EXTERIOR_WALL", slab_edge="PERIMETER", zone_test=False,
                              footprint_test=False)
    assert a["AUTHORITY"] == "EXTERIOR_SOURCE_VERIFIED"
    assert GR.exterior_authority(relation="UNDER_EXTERIOR_WALL", slab_edge="INTERNAL", zone_test=True,
                                 footprint_test=True)["AUTHORITY"] == "SOURCE_CONFLICT"
    assert GR.exterior_authority(relation="NO_WALL_ABOVE", slab_edge="PERIMETER", zone_test=True,
                                 footprint_test=True)["AUTHORITY"] == "CANDIDATE_EXTERIOR"
    assert GR.exterior_authority(relation="NO_WALL_ABOVE", slab_edge="INTERNAL", zone_test=True,
                                 footprint_test=False)["AUTHORITY"] == "INTERIOR_SOURCE_VERIFIED"


# ------------------------------------------------------------------------------------------- FOLLOW ARCH
def test_follow_arch_derivation():
    d = GR.follow_arch_depth(top_ffl_m=1.0, top_source="mark", buildup_known_m=None, bottom_levels_m=[0.0],
                             bottom_source="sections")
    assert d["STATE"] == "BOUNDED" and d["DEPTH_MAX_M"] == pytest.approx(1.0) and d["DEPTH_MIN_M"] is None
    d = GR.follow_arch_depth(top_ffl_m=1.0, top_source="mark", buildup_known_m=0.10, bottom_levels_m=[0.0],
                             bottom_source="sections")
    assert d["STATE"] == "SOURCE_DERIVED" and d["DEPTH_MAX_M"] == pytest.approx(0.90)
    d = GR.follow_arch_depth(top_ffl_m=1.0, top_source="mark", buildup_known_m=0.10, bottom_levels_m=[0.0, 0.15],
                             bottom_source="court")
    assert d["STATE"] == "BOUNDED" and d["DEPTH_MAX_M"] == pytest.approx(1.0)   # outer level not unique
    assert GR.follow_arch_depth(top_ffl_m=None, top_source=None, buildup_known_m=None, bottom_levels_m=[0.0],
                                bottom_source="s")["STATE"] == "UNRESOLVED"


# ------------------------------------------------------------------------------------------- length basis
def test_dual_length_basis_applicability():
    same = GR.length_basis({"CLEAR": 3.2, "CENTRELINE": 3.6}, COND)
    assert same["SAME_RESULT"] and same["DETAIL_BY_CLEAR_LENGTH"] == ["P13-GB-LT5M"]
    diff = GR.length_basis({"CLEAR": 2.2, "CENTRELINE": 2.8}, COND)
    assert not diff["SAME_RESULT"] and diff["UNION"] == ["P13-GB-LT2_5M", "P13-GB-LT5M"]
    on = GR.length_basis({"CLEAR": 5.0004, "CENTRELINE": 5.3}, COND)
    assert not on["SAME_RESULT"] and on["ON_THRESHOLD"]
    assert not GR.length_basis({"CLEAR": 3.0, "CENTRELINE": None}, COND)["SAME_RESULT"]


# ------------------------------------------------------------------------------------------- loads
def test_concentrated_load_unknown_blocks_the_titled_sections_only():
    assert GR.concentrated_load([])["STATE"] == "NO_CONCENTRATED_LOAD_EVIDENCE"
    assert GR.concentrated_load([{"kind": "BEAM_END_REACTION", "ref": "B"}])["STATE"] == "UNKNOWN"
    assert GR.concentrated_load([{"kind": "JUNCTION_AT_SUPPORT", "ref": "B"}])["STATE"] == \
        "NO_CONCENTRATED_LOAD_EVIDENCE"
    assert GR.concentrated_load([{"kind": "PLANTED_COLUMN_ON_SPAN", "ref": "C"},
                                 {"kind": "BEAM_END_REACTION", "ref": "B"}])["STATE"] == "CONCENTRATED_LOAD_PRESENT"
    with pytest.raises(ValueError):
        GR.concentrated_load([{"kind": "GUESS", "ref": "x"}])
    prec = GR.nested_precedence()
    c = GR.candidate_details(authority="INTERIOR_SOURCE_VERIFIED", length_union=["P13-GB-LT5M"], load_state="UNKNOWN",
                             clause_details=CLAUSE, exterior_detail=EXT, basis_same=True, nested=False,
                             precedence=prec)
    assert GR.NO_DETAIL_IF_LOADED in c["CANDIDATES"] and c["STATE"] == "CANDIDATE_DETAIL"
    c = GR.candidate_details(authority="INTERIOR_SOURCE_VERIFIED", length_union=["P13-GB-LT5M"],
                             load_state="CONCENTRATED_LOAD_PRESENT", clause_details=CLAUSE, exterior_detail=EXT,
                             basis_same=True, nested=False, precedence=prec)
    assert c["STATE"] == "NO_APPLICABLE_DETAIL"
    # the < 2.5 m section has no load clause: the loaded case still has a detail
    c = GR.candidate_details(authority="INTERIOR_SOURCE_VERIFIED", length_union=["P13-GB-LT2_5M", "P13-GB-LT5M"],
                             load_state="UNKNOWN", clause_details=CLAUSE, exterior_detail=EXT, basis_same=True,
                             nested=True, precedence=GR.nested_precedence(narrower_condition="P13-GB-LT2_5M"))
    assert GR.NO_DETAIL_IF_LOADED not in c["CANDIDATES"]
    # the exterior section has no clause either
    c = GR.candidate_details(authority="EXTERIOR_SOURCE_VERIFIED", length_union=["P13-GB-LT5M"], load_state="UNKNOWN",
                             clause_details=CLAUSE, exterior_detail=EXT, basis_same=True, nested=False,
                             precedence=prec)
    assert c["CANDIDATES"] == [EXT] and c["STATE"] == "PROJECT_GENERAL_DETAIL"
    c = GR.candidate_details(authority="INTERIOR_SOURCE_VERIFIED", length_union=["P13-GB-LT5M"],
                             load_state="NO_CONCENTRATED_LOAD_EVIDENCE", clause_details=CLAUSE, exterior_detail=EXT,
                             basis_same=True, nested=False, precedence=prec)
    assert c["STATE"] == "EXPLICIT_LENGTH_CONDITION"


# ------------------------------------------------------------------------------------------- precedence
def test_overlapping_detail_precedence():
    p = GR.nested_precedence(narrower_condition="P13-GB-LT2_5M")
    assert p["RULE_PRECEDENCE_SOURCE"] == "SPECIFICITY_CANDIDATE" and not p["RESOLVED"] and p["WINNER"] is None
    assert GR.nested_precedence(explicit_note=True, narrower_condition="X")["RULE_PRECEDENCE_SOURCE"] == \
        "SOURCE_EXPLICIT"
    assert GR.nested_precedence(layout_grouping=True, narrower_condition="X")["RESOLVED"]
    assert GR.nested_precedence()["RULE_PRECEDENCE_SOURCE"] == "UNRESOLVED"
    c = GR.candidate_details(authority="INTERIOR_SOURCE_VERIFIED", length_union=["P13-GB-LT2_5M", "P13-GB-LT5M"],
                             load_state="NO_CONCENTRATED_LOAD_EVIDENCE", clause_details=CLAUSE, exterior_detail=EXT,
                             basis_same=True, nested=True, precedence=p)
    assert c["CANDIDATES"] == ["P13-GB-LT2_5M", "P13-GB-LT5M"] and c["STATE"] == "CANDIDATE_DETAIL"


# ------------------------------------------------------------------------------------------- free ends
def test_free_end_classification_order():
    assert GR.free_end_class(column_gap_mm=20.0, inside_footing="F1")["CLASS"] == "COLUMN"
    assert GR.free_end_class(column_outline_gap_mm=0.0, inside_footing="F1")["CLASS"] == "COLUMN"
    assert GR.free_end_class(column_gap_mm=200.0, inside_footing="F1")["CLASS"] == "FOOTING"
    assert GR.free_end_class(boundary_gap_mm=0.0)["CLASS"] == "BOUNDARY"
    assert GR.free_end_class(band_gap_mm=10.0)["CLASS"] == "DRAWING_BREAK"
    assert GR.free_end_class(arch_wall_beyond_mm=800.0, arch_wall_at_end=True)["CLASS"] == "WALL_RETURN"
    assert GR.free_end_class(arch_wall_at_end=True)["CLASS"] == "ARCHITECTURAL_TERMINATION"
    assert GR.free_end_class()["CLASS"] == "UNRESOLVED"
    assert set(GR.FREE_END_CLASSES) >= {"FOOTING", "COLUMN", "WALL_RETURN", "BOUNDARY", "ARCHITECTURAL_TERMINATION",
                                        "DRAWING_BREAK", "UNRESOLVED"}
