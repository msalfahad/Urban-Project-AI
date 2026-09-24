"""One unanswered question blocks what its answer could change, and nothing else.

R4 blocked every wall line on a floor because one door on that floor had no proved host.  Sixty-one rows were
withheld to protect two of them, which is why nothing could be released at all.
"""

from __future__ import annotations

from engine.qs_core import (dependency as DEP, evidence as EV, geom, invariants, masonry as MA,
                            openings as OP, synthetic as S)
from engine.qs_core.entities import HOST_ASSIGNED

TOL, SPAN = S.TOL, S.MAX_OPENING_SPAN
HEIGHT = EV.resolve("wall height", [EV.Claim(3.0, EV.OWNER_PROJECT_INPUT, "TEST")], TOL)
ANNOTATED = {"MATERIAL": "BLOCKWORK"}


def plan_with_an_ambiguous_door():
    """Two partitions of different thickness meeting at a corner, with a door in the corner itself.

    A door at a junction is genuinely ambiguous: it is in one of the two walls and the geometry does not say
    which.  Far away, a third wall carries a door that is not ambiguous at all.
    """
    along_x = S.wall_band("W-X", (0.0, 0.0, 4.0, 0.20), 0.20, geom.AXIS_X)
    along_y = S.wall_band("W-Y", (0.0, 0.0, 0.20, 4.0), 0.20, geom.AXIS_Y)
    far_a = S.wall_band("W-FAR", (10.0, 0.0, 12.0, 0.15), 0.15, geom.AXIS_X)
    far_b = S.wall_band("W-FAR2", (12.9, 0.0, 16.0, 0.15), 0.15, geom.AXIS_X)
    far_c = S.wall_band("W-FAR3", (10.0, 6.0, 16.0, 6.15), 0.15, geom.AXIS_X)
    # square, at the corner, as deep as both walls and running along neither: the geometry does not say
    corner_door = S.opening("OP-CORNER", (0.0, 0.0, 0.20, 0.20), None, 0.20, 2.10)
    far_door = S.opening("OP-FAR", (12.0, 0.0, 12.9, 0.15), geom.AXIS_X, 0.90, 2.10)
    return [along_x, along_y, far_a, far_b, far_c], [corner_door, far_door]


def build(bands, ops, height=HEIGHT):
    lines, _gaps = OP.build_wall_lines(bands, TOL, SPAN, openings=ops)
    register = OP.build_opening_register(ops, lines, TOL)
    basis = OP.evaluate_opening_basis(lines, ops, TOL)
    ident = MA.classify_wall_identity(lines, TOL,
                                      annotations={ln.component_ref: ANNOTATED for ln in lines},
                                      masonry_materials=("BLOCKWORK",))
    by_ref = {r["COMPONENT_REF"]: r for r in ident["REGISTER"]}
    graph = DEP.build(register, lines, basis, by_ref, EV.established(height), TOL)
    rows = OP.wall_band_quantities(lines, register, height, basis, graph["BLOCKED"], by_ref)
    return lines, register, graph, rows


def test_an_unresolved_host_blocks_its_candidates_and_leaves_the_rest_released():
    bands, ops = plan_with_an_ambiguous_door()
    lines, register, graph, rows = build(bands, ops)
    unresolved = [o for o in register["REGISTER"] if o["HOST_ASSIGNMENT_STATUS"] != HOST_ASSIGNED]
    assert unresolved, "the fixture has to actually produce an ambiguous host"
    blocked = set(graph["BLOCKED_WALL_LINES"])
    candidates = {c["COMPONENT_REF"] for o in unresolved for c in o["HOST_CANDIDATES"]}
    assert blocked >= candidates
    assert graph["RELEASED_WALL_LINES"], "something far away must survive the question"
    assert not (blocked & set(graph["RELEASED_WALL_LINES"]))


def test_the_far_wall_keeps_its_quantity_while_the_corner_is_open():
    bands, ops = plan_with_an_ambiguous_door()
    _lines, _register, _graph, rows = build(bands, ops)
    far = [r for r in rows if r["THICKNESS_M"] == 0.15]
    assert far and all(r["NET_AREA_M2"] is not None for r in far), [r["STATUS"] for r in far]


def test_every_block_names_the_question_that_caused_it():
    bands, ops = plan_with_an_ambiguous_door()
    _lines, _register, graph, _rows = build(bands, ops)
    for node, rec in graph["BLOCKED"].items():
        assert rec["REASONS"] and all(r.get("KIND") and r.get("WHY") for r in rec["REASONS"]), node


def test_the_graph_runs_from_the_opening_to_the_bill_line():
    bands, ops = plan_with_an_ambiguous_door()
    _lines, _register, graph, _rows = build(bands, ops)
    kinds = {(e["FROM_KIND"], e["TO_KIND"]) for e in graph["EDGES"]}
    assert (DEP.NODE_OPENING, DEP.NODE_WALL_LINE) in kinds
    assert (DEP.NODE_WALL_LINE, DEP.NODE_SUBTOTAL) in kinds
    assert (DEP.NODE_SUBTOTAL, DEP.NODE_BOQ) in kinds


def test_a_thickness_whose_lines_are_all_clear_is_not_blocked_by_another_thickness():
    bands, ops = plan_with_an_ambiguous_door()
    _lines, _register, graph, _rows = build(bands, ops)
    blocked = set(graph["BLOCKED_SUBTOTALS"])
    assert len(graph["SUBTOTALS"]) > 1
    assert len(blocked) < len(graph["SUBTOTALS"]), "not every subtotal can be blocked by one corner door"


def test_an_opening_associated_with_nothing_is_reported_and_blocks_nothing():
    wall = S.wall_band("W-1", (0.0, 0.0, 6.0, 0.20), 0.20, geom.AXIS_X)
    wall2 = S.wall_band("W-2", (0.0, 9.0, 6.0, 9.20), 0.20, geom.AXIS_X)
    stray = S.opening("OP-STRAY", (100.0, 100.0, 100.9, 100.2), geom.AXIS_X, 0.90, 2.10)
    _lines, _register, graph, rows = build([wall, wall2], [stray])
    assert graph["UNASSOCIATED_OPENINGS"][0]["OPENING_REF"] == "OP-STRAY"
    assert graph["BLOCKED_WALL_LINES"] == []
    assert all(r["NET_AREA_M2"] is not None for r in rows)


def test_an_opening_near_a_wall_but_in_none_of_them_blocks_the_walls_it_could_be_in():
    wall = S.wall_band("W-1", (0.0, 0.0, 6.0, 0.20), 0.20, geom.AXIS_X)
    wall2 = S.wall_band("W-2", (0.0, 9.0, 6.0, 9.20), 0.20, geom.AXIS_X)
    near = S.opening("OP-NEAR", (2.0, 0.6, 2.9, 0.8), geom.AXIS_X, 0.90, 2.10)
    _lines, _register, graph, _rows = build([wall, wall2], [near])
    assert graph["BLOCKED_WALL_LINES"], "a wall a hand's breadth away could still be the answer"
    assert len(graph["BLOCKED_WALL_LINES"]) == 1
    assert graph["UNASSOCIATED_OPENINGS"] == []


def test_an_opening_with_no_established_height_blocks_only_its_own_host():
    wall = S.wall_band("W-1", (0.0, 0.0, 6.0, 0.20), 0.20, geom.AXIS_X)
    other = S.wall_band("W-2", (0.0, 9.0, 6.0, 9.20), 0.20, geom.AXIS_X)
    door = S.opening("OP-NOHEIGHT", (2.0, 0.0, 2.9, 0.20), geom.AXIS_X, 0.90, None)
    door.height = None
    _lines, _register, graph, rows = build([wall, other], [door])
    blocked = graph["BLOCKED_WALL_LINES"]
    assert len(blocked) == 1
    assert [r["STATUS"] for r in rows].count("FINAL_QUANTITY_AVAILABLE") == 1


def test_no_wall_height_blocks_everything_because_everything_depends_on_it():
    bands, ops = plan_with_an_ambiguous_door()
    nothing = EV.resolve("wall height", [], TOL)
    _lines, _register, graph, rows = build(bands, ops, height=nothing)
    assert set(graph["BLOCKED_WALL_LINES"]) == set(graph["NODES"][DEP.NODE_WALL_LINE])
    assert all(r["NET_AREA_M2"] is None for r in rows)


def test_the_invariant_catches_a_row_blocked_for_no_recorded_reason():
    bands, ops = plan_with_an_ambiguous_door()
    _lines, _register, graph, rows = build(bands, ops)
    assert invariants.blocking_is_limited_to_the_affected_scope(graph, rows)["PASS"]
    smuggled = [dict(r, STATUS="BLOCKED_PENDING_ANSWERS", BLOCKED_BY=[]) for r in rows]
    check = invariants.blocking_is_limited_to_the_affected_scope(graph, smuggled)
    assert not check["PASS"] and check["RESULT"]["BLOCKED_WITHOUT_A_GRAPH_REASON"]


def test_a_gap_nobody_has_explained_blocks_the_wall_it_sits_in():
    """Upstream of every host question: if the gap turns out to be a door, this wall's net area moves."""
    from engine.qs_core import admission as AD

    walls, cands, _schedule = S.an_unlabelled_wall_gap()
    pop = AD.normalize_opening_population(cands, walls, [], S.DRAFTING_RESOLUTION, TOL)
    lines, _gaps = OP.build_wall_lines(walls, TOL, SPAN, openings=[])
    register = OP.build_opening_register([], lines, TOL)
    basis = OP.evaluate_opening_basis(lines, [], TOL)
    ident = MA.classify_wall_identity(lines, TOL,
                                      annotations={ln.component_ref: ANNOTATED for ln in lines},
                                      masonry_materials=("BLOCKWORK",))
    by_ref = {r["COMPONENT_REF"]: r for r in ident["REGISTER"]}
    graph = DEP.build(register, lines, basis, by_ref, True, TOL, population=pop)
    assert graph["BLOCKED_WALL_LINES"], "an unexplained hole cannot leave the wall around it final"
    reasons = {r["KIND"] for n in graph["BLOCKED_WALL_LINES"] for r in graph["BLOCKED"][n]["REASONS"]}
    assert DEP.BLOCK_ADMISSION_UNRESOLVED in reasons
    rows = OP.wall_band_quantities(lines, register, HEIGHT, basis, graph["BLOCKED"], by_ref)
    assert all(r["NET_AREA_M2"] is None for r in rows)


def test_a_confirmed_opening_does_not_block_the_wall_it_is_deducted_from():
    """The contrast that makes the previous test mean something: knowing what the hole is releases the wall."""
    from engine.qs_core import admission as AD

    walls, cands, schedule = S.a_real_narrow_opening()
    pop = AD.normalize_opening_population(cands, walls, schedule, S.DRAFTING_RESOLUTION, TOL)
    ops = AD.admitted_openings(cands, TOL)
    lines, _gaps = OP.build_wall_lines(walls, TOL, SPAN, openings=ops)
    register = OP.build_opening_register(ops, lines, TOL)
    basis = OP.evaluate_opening_basis(lines, ops, TOL)
    ident = MA.classify_wall_identity(lines, TOL,
                                      annotations={ln.component_ref: ANNOTATED for ln in lines},
                                      masonry_materials=("BLOCKWORK",))
    by_ref = {r["COMPONENT_REF"]: r for r in ident["REGISTER"]}
    graph = DEP.build(register, lines, basis, by_ref, True, TOL, population=pop)
    assert graph["BLOCKED_WALL_LINES"] == []
    rows = OP.wall_band_quantities(lines, register, HEIGHT, basis, graph["BLOCKED"], by_ref)
    assert all(r["NET_AREA_M2"] is not None for r in rows)
