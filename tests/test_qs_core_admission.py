"""US-20: the three populations become one physical population, before anything is hosted or deducted.

Every case here is one the R4 build got wrong or never asked.  A 2 mm drafting gap reached host assignment and
was answered confidently.  A 0.60 m object with no host and no height was carried as an opening.  Nothing
reconciled the schedule against the geometry, so a scheduled door nobody drew was silently absent and a door
drawn twice would have been deducted twice.
"""

from __future__ import annotations

from engine.qs_core import admission as AD, synthetic as S

TOL = S.TOL
RES = S.DRAFTING_RESOLUTION


def run(fixture):
    walls, cands, schedule = fixture
    return AD.normalize_opening_population(cands, walls, schedule, RES, TOL), {c.candidate_ref: c
                                                                              for c in cands}


def test_a_millimetre_drafting_gap_is_noise_and_never_reaches_host_assignment():
    pop, by_ref = run(S.millimetre_drafting_gap())
    c = by_ref["CAND-GAP"]
    assert c.classification == AD.DRAWING_NOISE
    assert pop["COUNTS"][AD.CONFIRMED_OPENING] == 0
    assert "did not meet" in c.admission_evidence[0].detail["WHY"]
    assert not AD.admitted_openings([c], TOL)


def test_a_narrow_opening_the_source_vouches_for_is_admitted_not_deleted():
    pop, by_ref = run(S.a_real_narrow_opening())
    c = by_ref["CAND-NARROW"]
    assert c.classification == AD.CONFIRMED_OPENING, c.admission_evidence[0].as_dict()
    assert c.drawn_width < 0.61 and c.drawn_width > RES
    assert pop["SCHEDULE_ROWS_MATCHED"] == 1
    admitted = AD.admitted_openings([c], TOL)
    assert admitted[0].height == 2.10 and admitted[0].height_source == "DRAWING_DIMENSION"


def test_size_alone_never_admits_and_never_rejects_a_vouched_candidate():
    """The two previous cases differ in provenance, not in size - which is the whole rule."""
    noise_pop, noise = run(S.millimetre_drafting_gap())
    real_pop, real = run(S.a_real_narrow_opening())
    assert noise["CAND-GAP"].provenance == []
    assert real["CAND-NARROW"].provenance
    assert noise_pop["RULE"].startswith("a candidate is admitted on provenance")
    assert real_pop["DRAFTING_RESOLUTION_M"] == RES


def test_one_door_drawn_twice_is_one_opening_with_the_other_marked_a_duplicate():
    pop, by_ref = run(S.the_same_door_drawn_twice())
    classes = {r: c.classification for r, c in by_ref.items()}
    assert sorted(classes.values()) == [AD.CONFIRMED_OPENING, AD.DUPLICATE_OF_CONFIRMED_OPENING]
    dup = next(c for c in by_ref.values() if c.classification == AD.DUPLICATE_OF_CONFIRMED_OPENING)
    kept = next(c for c in by_ref.values() if c.classification == AD.CONFIRMED_OPENING)
    assert dup.duplicate_of == kept.candidate_ref
    assert pop["PHYSICAL_OPENING_COUNT"] == 1
    assert len(AD.admitted_openings(list(by_ref.values()), TOL)) == 1


def test_the_representation_that_is_kept_is_the_better_vouched_one():
    _pop, by_ref = run(S.the_same_door_drawn_twice())
    kept = next(c for c in by_ref.values() if c.classification == AD.CONFIRMED_OPENING)
    assert kept.candidate_ref == "CAND-REGISTER"
    assert {p["KIND"] for p in kept.provenance} >= {AD.PROV_BLOCK, AD.PROV_SCHEDULE}


def test_two_different_openings_of_the_same_width_are_two_openings():
    pop, by_ref = run(S.two_different_openings_of_the_same_width())
    assert all(c.classification == AD.CONFIRMED_OPENING for c in by_ref.values())
    assert pop["PHYSICAL_OPENING_COUNT"] == 2
    assert all(c.duplicate_of is None for c in by_ref.values())


def test_an_unlabelled_wall_gap_is_a_question_not_a_deduction():
    pop, by_ref = run(S.an_unlabelled_wall_gap())
    c = by_ref["CAND-UNNAMED"]
    assert c.classification == AD.OPENING_CANDIDATE_UNRESOLVED
    assert pop["COUNTS"][AD.CONFIRMED_OPENING] == 0
    assert "nothing says what fills the gap" in c.admission_evidence[0].detail["WHY"]
    assert c.jamb_evidence, "the reveal is recognised; what fills it is not"


def test_a_candidate_that_is_a_hole_in_nothing_is_not_an_opening():
    _pop, by_ref = run(S.a_candidate_in_open_space())
    c = by_ref["CAND-FLOATING"]
    assert c.classification == AD.NON_OPENING_GAP
    assert c.admission_evidence[0].detail["WALL_MATERIAL_SHARE"] == 0.0


def test_a_scheduled_opening_nobody_drew_is_reported_rather_than_forgotten():
    walls, cands, schedule = S.a_scheduled_opening_nobody_drew()
    pop = AD.normalize_opening_population(cands, walls, schedule, RES, TOL)
    assert pop["SCHEDULE_ROWS_IN"] == 1 and pop["SCHEDULE_ROWS_MATCHED"] == 0
    assert pop["SCHEDULE_ROWS_WITHOUT_GEOMETRY"][0]["SCHEDULE_REF"] == "W-14"


def test_no_candidate_is_ever_deleted_on_the_way_in():
    for fixture in (S.millimetre_drafting_gap(), S.the_same_door_drawn_twice(),
                    S.an_unlabelled_wall_gap(), S.a_candidate_in_open_space()):
        pop, _ = run(fixture)
        assert pop["CANDIDATES_IN"] == len(pop["POPULATION"])
        assert all(c["CLASSIFICATION"] in AD.CLASSES and c["EVIDENCE"] for c in pop["POPULATION"])


def test_an_admitted_opening_carries_width_and_height_evidence_separately():
    _pop, by_ref = run(S.a_real_narrow_opening())
    o = AD.admitted_openings(list(by_ref.values()), TOL)[0]
    w, h = o.admission["WIDTH_EVIDENCE"], o.admission["HEIGHT_EVIDENCE"]
    assert w["STATUS"] == "ESTABLISHED" and h["STATUS"] == "ESTABLISHED"
    assert w["REFERENCE"] != h["REFERENCE"], "width and height must not rest on one fact"


def test_a_candidate_the_source_names_but_draws_below_its_own_resolution_is_a_contradiction():
    walls, _c, _s = S.millimetre_drafting_gap()
    named = S.candidate("CAND-TINY", (3.0, 0.0, 3.002, 0.20), "X")
    pop = AD.normalize_opening_population([named], walls, [], RES, TOL)
    assert named.classification == AD.OPENING_CANDIDATE_UNRESOLVED
    assert pop["COUNTS"][AD.DRAWING_NOISE] == 0
