"""US-20: the three populations become one physical population, and admission answers existence only.

Every case here is one the earlier builds got wrong or never asked.  A 2 mm drafting gap reached host assignment
and was answered confidently.  A named door that lay in the void between two wall ends was demoted to an
anonymous gap because it overlapped no material.  Nothing reconciled the schedule against the geometry.
"""

from __future__ import annotations

from engine.qs_core import admission as AD, hosting as H, synthetic as S

TOL = S.TOL
RES = S.DRAFTING_RESOLUTION


def run(fixture):
    walls, cands, schedule = fixture
    pop = AD.normalize_opening_population(cands, schedule, RES, TOL)
    return pop, {c.candidate_ref: c for c in cands}, walls


def test_a_millimetre_drafting_gap_is_noise_and_never_reaches_host_assignment():
    pop, by_ref, _walls = run(S.millimetre_drafting_gap())
    c = by_ref["CAND-GAP"]
    assert c.classification == AD.DRAWING_NOISE and c.existence == AD.DOES_NOT_EXIST
    assert pop["PHYSICAL_OPENING_COUNT"] == 0
    assert "did not meet" in c.admission_evidence[0].detail["WHY"]
    assert not AD.admitted_openings([c], TOL)


def test_a_narrow_opening_the_source_vouches_for_is_admitted_not_deleted():
    pop, by_ref, _walls = run(S.a_real_narrow_opening())
    c = by_ref["CAND-NARROW"]
    assert c.existence == AD.EXISTS_CONFIRMED, c.admission_evidence[0].as_dict()
    assert RES < c.span < 0.61
    assert pop["SCHEDULE_ROWS_MATCHED"] == 1
    admitted = AD.admitted_openings([c], TOL)
    assert admitted[0].height == 2.10 and admitted[0].height_source == "DRAWING_DIMENSION"


def test_size_alone_never_admits_and_never_rejects_a_vouched_candidate():
    _np, noise, _w = run(S.millimetre_drafting_gap())
    real_pop, real, _w2 = run(S.a_real_narrow_opening())
    assert noise["CAND-GAP"].provenance == []
    assert real["CAND-NARROW"].provenance
    assert real_pop["RULE"].startswith("admission decides EXISTENCE only")


def test_admission_consults_no_wall_geometry_at_all():
    """The rule that lost thirty-five named doors is gone, and its absence is testable."""
    walls, cands, schedule = S.a_real_narrow_opening()
    with_walls = AD.normalize_opening_population(list(cands), schedule, RES, TOL)
    moved = S.candidate("CAND-NARROW", (200.0, 200.0, 200.6, 200.2), "X", kind="DOOR")
    without = AD.normalize_opening_population([moved], schedule, RES, TOL)
    assert with_walls["COUNTS"] == without["COUNTS"], \
        "moving a named door a hundred metres from any wall must not change whether it exists"
    del walls


def test_one_door_drawn_twice_is_one_opening_with_the_other_marked_a_duplicate():
    pop, by_ref, _walls = run(S.the_same_door_drawn_twice())
    classes = sorted(c.classification for c in by_ref.values())
    assert classes == [AD.DUPLICATE_OF_CONFIRMED_OPENING, AD.OPENING_CONFIRMED_HOST_UNRESOLVED]
    dup = next(c for c in by_ref.values() if c.existence == AD.IS_A_DUPLICATE)
    kept = next(c for c in by_ref.values() if c.existence == AD.EXISTS_CONFIRMED)
    assert dup.duplicate_of == kept.candidate_ref
    assert pop["PHYSICAL_OPENING_COUNT"] == 1
    assert len(AD.admitted_openings(list(by_ref.values()), TOL)) == 1


def test_the_representation_that_is_kept_is_the_better_vouched_one():
    _pop, by_ref, _walls = run(S.the_same_door_drawn_twice())
    kept = next(c for c in by_ref.values() if c.existence == AD.EXISTS_CONFIRMED)
    assert kept.candidate_ref == "CAND-REGISTER"
    assert {p["KIND"] for p in kept.provenance} >= {AD.PROV_BLOCK, AD.PROV_SCHEDULE}


def test_two_different_openings_of_the_same_width_are_two_openings():
    pop, by_ref, _walls = run(S.two_different_openings_of_the_same_width())
    assert all(c.existence == AD.EXISTS_CONFIRMED for c in by_ref.values())
    assert pop["PHYSICAL_OPENING_COUNT"] == 2
    assert all(c.duplicate_of is None for c in by_ref.values())


def test_an_unlabelled_wall_gap_is_a_question_not_a_deduction():
    pop, by_ref, _walls = run(S.an_unlabelled_wall_gap())
    c = by_ref["CAND-UNNAMED"]
    assert c.classification == AD.OPENING_CANDIDATE_UNRESOLVED
    assert pop["PHYSICAL_OPENING_COUNT"] == 0
    assert "nothing says what fills the gap" in c.admission_evidence[0].detail["WHY"]
    assert c.jamb_points, "the reveal is recognised; what fills it is not"


def test_a_mark_with_no_name_and_no_jambs_is_not_an_opening():
    _pop, by_ref, _walls = run(S.a_candidate_in_open_space())
    c = by_ref["CAND-FLOATING"]
    assert c.classification == AD.NON_OPENING_GAP and c.existence == AD.DOES_NOT_EXIST


def test_a_scheduled_opening_nobody_drew_is_reported_rather_than_forgotten():
    _walls, cands, schedule = S.a_scheduled_opening_nobody_drew()
    pop = AD.normalize_opening_population(cands, schedule, RES, TOL)
    assert pop["SCHEDULE_ROWS_IN"] == 1 and pop["SCHEDULE_ROWS_MATCHED"] == 0
    assert pop["SCHEDULE_ROWS_WITHOUT_GEOMETRY"][0]["SCHEDULE_REF"] == "W-14"


def test_no_candidate_is_ever_deleted_on_the_way_in():
    for fixture in (S.millimetre_drafting_gap(), S.the_same_door_drawn_twice(),
                    S.an_unlabelled_wall_gap(), S.a_candidate_in_open_space()):
        pop, _by_ref, _walls = run(fixture)
        assert pop["CANDIDATES_IN"] == len(pop["POPULATION"])
        assert all(c["CLASSIFICATION"] in AD.CLASSES and c["EVIDENCE"] for c in pop["POPULATION"])


def test_an_admitted_opening_carries_width_and_height_evidence_separately():
    _pop, by_ref, _walls = run(S.a_real_narrow_opening())
    o = AD.admitted_openings(list(by_ref.values()), TOL)[0]
    w, h = o.admission["WIDTH_EVIDENCE"], o.admission["HEIGHT_EVIDENCE"]
    assert w["STATUS"] == "ESTABLISHED" and h["STATUS"] == "ESTABLISHED"
    assert w["REFERENCE"] != h["REFERENCE"], "width and height must not rest on one fact"


def test_a_candidate_named_but_drawn_below_the_sources_own_resolution_is_a_contradiction():
    named = S.candidate("CAND-TINY", (3.0, 0.0, 3.002, 0.20), "X")
    pop = AD.normalize_opening_population([named], [], RES, TOL)
    assert named.classification == AD.OPENING_CANDIDATE_UNRESOLVED
    assert pop["COUNTS"][AD.DRAWING_NOISE] == 0


def test_the_published_classification_is_the_one_the_object_leaves_the_stage_with():
    walls, doors = S.a_named_door_in_a_wall_void()
    pop = AD.normalize_opening_population(doors, [], RES, TOL)
    assert pop["POPULATION"][0]["CLASSIFICATION"] == AD.OPENING_CONFIRMED_HOST_UNRESOLVED
    H.resolve_hosts(doors, walls, TOL)
    refreshed = AD.refresh(pop, doors)
    assert refreshed["POPULATION"][0]["CLASSIFICATION"] == AD.OPENING_CONFIRMED_HOST_CONFIRMED
    assert refreshed["PHYSICAL_OPENING_COUNT"] == 1
