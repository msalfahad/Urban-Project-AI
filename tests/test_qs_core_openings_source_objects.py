"""A source object that the drawing names must survive the whole pipeline.

R5 carried thirty-five doors that the CAD file names individually - DOOR-EWAN::BA-OP-001 and its siblings - and
reported them as gaps that "nothing in the source names as an opening".  The mechanism was a single rule:
admission required an opening to overlap wall material.  A door lies in the void BETWEEN two wall ends, so that
rule rejects the normal case and keeps the exceptions.

These eight tests are the contract that replaces it.  None of them asserts a quantity.
"""

from __future__ import annotations

from engine.qs_core import admission as AD, geom, hosting as H, openings as op, synthetic as S, \
    transforms as TR

TOL, RES = S.TOL, S.DRAFTING_RESOLUTION


def admit(candidates, schedule=()):
    return AD.normalize_opening_population(list(candidates), list(schedule), RES, TOL)


def admit_and_host(walls, candidates, schedule=()):
    pop = admit(candidates, schedule)
    hosts = H.resolve_hosts(candidates, walls, TOL)
    return pop, hosts


# 1 ------------------------------------------------------------------
def test_a_named_door_in_a_wall_void_is_admitted_and_hosted_by_the_bracketing_wall():
    walls, doors = S.a_named_door_in_a_wall_void()
    pop, hosts = admit_and_host(walls, doors)
    door = doors[0]
    assert door.existence == AD.EXISTS_CONFIRMED
    assert door.classification == AD.OPENING_CONFIRMED_HOST_CONFIRMED
    assert door.host_record["HOST_SEGMENT_REFS"] == ["V-L", "V-R"]
    assert door.host_record["RELATION"] == H.BRACKETED_BY_TWO_WALL_ENDS
    assert pop["PHYSICAL_OPENING_COUNT"] == 1 and hosts["HOST_CONFIRMED"] == 1


def test_that_door_overlaps_no_wall_material_at_all():
    """The condition R5 treated as disqualifying is the condition the case is defined by."""
    walls, doors = S.a_named_door_in_a_wall_void()
    admit_and_host(walls, doors)
    foot = doors[0].footprint()
    assert foot is not None, "a footprint exists only once a host supplied the depth"
    overlap = sum(geom.intersection_area([foot], w.rects) for w in walls)
    assert overlap < 1e-12, overlap


def test_the_depth_comes_from_the_host_and_not_from_the_extractors_grid():
    walls, doors = S.a_named_door_in_a_wall_void(thickness=0.15)
    admit_and_host(walls, doors)
    assert doors[0].depth == 0.15
    assert doors[0].host_record["DEPTH_SOURCE"].startswith("the host wall's own thickness")


# 2 ------------------------------------------------------------------
def test_the_same_case_survives_translation_and_rotation():
    base_walls, base_doors = S.a_named_door_in_a_wall_void()
    admit_and_host(base_walls, base_doors)
    reference = (base_doors[0].classification, base_doors[0].depth,
                 base_doors[0].host_record["RELATION"], round(base_doors[0].span, 9))

    for dx, dy, turns in ((123.5, -77.25, 0), (0.0, 0.0, 1), (-40.0, 15.0, 2), (9.0, 9.0, 3)):
        walls, doors = S.a_named_door_in_a_wall_void()
        plan = {"COMPONENTS": walls, "CANDIDATES": doors, "BARRIERS": [], "LABELS": []}
        moved = TR.transform_plan(plan, dx=dx, dy=dy, quarter_turns=turns)
        admit_and_host(moved["COMPONENTS"], moved["CANDIDATES"])
        d = moved["CANDIDATES"][0]
        assert (d.classification, d.depth, d.host_record["RELATION"], round(d.span, 9)) == reference, \
            (dx, dy, turns)


# 3 ------------------------------------------------------------------
def test_one_run_two_runs_or_many_segments_give_the_same_answer():
    results = []
    for walls, door in S.the_same_wall_in_three_representations():
        admit_and_host(walls, [door])
        results.append((door.classification, door.depth, round(door.span, 9),
                        door.host_record["HOST_STATUS"]))
    assert len(set(results)) == 1, results
    assert results[0][0] == AD.OPENING_CONFIRMED_HOST_CONFIRMED


def test_the_confirmed_opening_joins_its_two_wall_ends_however_finely_they_are_chopped():
    """The host is proved against runs of material; the wall line has to be built from the same reading.

    Where the bracketing runs are one segment each this is trivially true.  Where the extractor chopped them
    into five, a host record that names all five segments and nothing about which two face the gap leaves the
    wall builder with no pair to join - and the opening ends up hosted by a wall line that does not exist.
    """
    for walls, door in S.the_same_wall_in_three_representations():
        admit_and_host(walls, [door])
        confirmed = AD.admitted_openings([door], TOL)
        lines, gaps = op.build_wall_lines(walls, TOL, 2.0, openings=confirmed)
        register = op.register_from_hosts(confirmed, lines, TOL)
        row = register["REGISTER"][0]
        assert len(lines) == 1, [ln.component_ref for ln in lines]
        assert row["HOST_ASSIGNMENT_STATUS"] == "HOST_ASSIGNED", row["HOST_EVIDENCE"]
        assert row["HOST_COMPONENT_REF"] == lines[0].component_ref
        wide = [g for g in gaps if g["GAP_M"] > TOL]
        assert all(g["BRIDGED"] and g["OPENINGS"] == [door.candidate_ref] for g in wide), wide


# 4 ------------------------------------------------------------------
def test_a_door_at_a_junction_is_a_confirmed_opening_with_an_unresolved_host():
    walls, doors = S.a_door_at_a_junction_of_two_thicknesses()
    pop, hosts = admit_and_host(walls, doors)
    door = doors[0]
    assert door.existence == AD.EXISTS_CONFIRMED, "the block names it whatever the geometry says"
    assert door.classification == AD.OPENING_CONFIRMED_HOST_UNRESOLVED
    assert door.host_record["HOST_STATUS"] == H.HOST_UNRESOLVED
    assert pop["PHYSICAL_OPENING_COUNT"] == 1
    assert hosts["HOST_UNRESOLVED"] == 1


def test_an_unresolved_host_publishes_its_competing_groups_and_their_scores():
    walls, doors = S.a_door_at_a_junction_of_two_thicknesses()
    admit_and_host(walls, doors)
    cands = doors[0].host_record["CANDIDATES"]
    assert len(cands) >= 2
    assert all("SCORE" in c and "EVIDENCE" in c for c in cands)
    assert all(set(c["EVIDENCE"]) >= set(H.WEIGHTS) for c in cands)


def test_proximity_alone_never_hosts_an_opening():
    """A door with no wall it fits: the nearest wall is not a reason."""
    wall = S.wall_band("P-W", (0.0, 0.0, 6.0, 0.20), 0.20, geom.AXIS_X)
    stray = S.candidate("P-DOOR", (2.0, 1.4, 2.9, 1.6), geom.AXIS_X)
    admit_and_host([wall], [stray])
    assert stray.classification == AD.OPENING_CONFIRMED_HOST_UNRESOLVED
    assert stray.host_record["HOST_STATUS"] == H.HOST_UNRESOLVED


# 5 ------------------------------------------------------------------
def test_a_gap_nothing_names_does_not_become_a_confirmed_opening():
    walls, cands, _s = S.an_unlabelled_wall_gap()
    pop, _hosts = admit_and_host(walls, cands)
    assert cands[0].classification == AD.OPENING_CANDIDATE_UNRESOLVED
    assert cands[0].existence == AD.EXISTS_UNRESOLVED
    assert pop["PHYSICAL_OPENING_COUNT"] == 0


def test_a_mark_with_neither_a_name_nor_a_pair_of_jambs_is_not_an_opening():
    _walls, cands, _s = S.a_candidate_in_open_space()
    admit(cands)
    assert cands[0].classification == AD.NON_OPENING_GAP


# 6 ------------------------------------------------------------------
def test_a_sub_resolution_gap_is_drawing_noise():
    _walls, cands, _s = S.millimetre_drafting_gap()
    pop = admit(cands)
    assert cands[0].classification == AD.DRAWING_NOISE
    assert cands[0].span < RES
    assert pop["COUNTS"][AD.DRAWING_NOISE] == 1


# 7 ------------------------------------------------------------------
def test_every_named_opening_is_conserved_through_admission_hosting_and_publication():
    walls, doors = S.a_named_door_in_a_wall_void()
    junction_walls, junction_doors = S.a_door_at_a_junction_of_two_thicknesses()
    all_walls = walls + [S.wall_band(w.component_ref + "::J", w.rects[0].as_tuple(), w.thickness, w.axis)
                         for w in junction_walls]
    named = doors + junction_doors
    before = {c.candidate_ref for c in named}
    pop, hosts = admit_and_host(all_walls, named)
    after = {c["CANDIDATE_REF"] for c in pop["POPULATION"]}
    assert before <= after, "a named object disappeared between the source and the register"
    assert set(pop["NAMED_BY_THE_SOURCE"]) == before
    hosted = {r["CANDIDATE_REF"] for r in hosts["REGISTER"]}
    assert hosted == before, "every named opening reaches host resolution, resolved or not"


def test_the_population_accounts_for_every_candidate_offered():
    walls, doors = S.a_named_door_in_a_wall_void()
    _w, bare, _s = S.an_unlabelled_wall_gap()
    _w2, noise, _s2 = S.millimetre_drafting_gap()
    offered = doors + bare + noise
    pop, _hosts = admit_and_host(walls, offered)
    assert pop["CANDIDATES_IN"] == len(pop["POPULATION"]) == len(offered)
    assert sum(pop["COUNTS"].values()) == len(offered)


# 8 ------------------------------------------------------------------
def test_no_admitted_object_disappears_because_host_assignment_failed():
    walls, doors = S.a_door_at_a_junction_of_two_thicknesses()
    pop, hosts = admit_and_host(walls, doors)
    assert hosts["HOST_UNRESOLVED"] == 1
    assert pop["PHYSICAL_OPENING_COUNT"] == 1
    admitted = AD.admitted_openings(doors, TOL)
    assert [o.opening_ref for o in admitted] == ["J-DOOR"], \
        "an opening with an unresolved host is still an opening"


def test_failing_to_overlap_wall_material_is_never_recorded_as_evidence_against_an_opening():
    walls, doors = S.a_named_door_in_a_wall_void()
    pop, _hosts = admit_and_host(walls, doors)
    blob = repr(pop["POPULATION"][0]["EVIDENCE"]).lower()
    assert "no wall material is here" not in blob
    assert "not in a wall" not in blob
    assert AD.normalize_opening_population.__doc__.count("No wall geometry is consulted") == 1
