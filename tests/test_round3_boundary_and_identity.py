"""Round 3: architectural language, bilingual identity, and room boundaries.

Round 2 made the semantic layer blind — a test asserted `KITCHEN` must
classify exactly like `QQZZX` — and blocked every room on the drawing with
`IDENTITY_AMBIGUOUS_MULTIPLE_LABELS` because each stamp carries an English
string and an Arabic one.

Both were wrong, and the invariant that replaces them is narrower:

    NO PROJECT-SPECIFIC STRING MAY BE HARDCODED TO FORCE A P7757 RESULT

which is not the same as knowing no architectural language at all. These
tests hold the difference: the vocabulary is general (it is checked against
terms that appear on no project here), and nothing in it is tuned to make
one drawing come out right.
"""

from __future__ import annotations

import pytest

from engine import architectural_ontology as onto
from engine import boundary_authority as authority
from engine import identity_reconcile as ident
from engine import round3_selftest as r3
from engine import semantic_seed as ss


class _Prov:
    def __init__(self, oid, block=()):
        self.object_id = oid
        self.block_path = tuple(block)


class _Text:
    def __init__(self, value, x=0.0, y=0.0, block=("B",)):
        self.value = value
        self.x = x
        self.y = y
        self.provenance = _Prov(f"CAD-{value}-{x}-{y}", block)


class _Cand:
    def __init__(self, oid, axis, fixed, lo, hi):
        self.object_id = oid
        self.axis = axis
        self.fixed_mm = fixed
        self.start_mm = lo
        self.end_mm = hi

    @property
    def length_mm(self):
        return abs(self.end_mm - self.start_mm)


class _Obs:
    def __init__(self, x, y):
        self.x = x
        self.y = y


# ------------------------------------------------------------- vocabulary

@pytest.mark.parametrize("term,concept_class", [
    ("kitchen", onto.ROOM), ("مطبخ", onto.ROOM),
    ("bedroom", onto.ROOM), ("غرفة نوم", onto.ROOM),
    ("street", onto.SITE_ANNOTATION), ("شارع", onto.SITE_ANNOTATION),
    ("neighbour", onto.SITE_ANNOTATION), ("جار", onto.SITE_ANNOTATION),
    ("garden", onto.EXTERNAL_SPACE), ("حديقة", onto.EXTERNAL_SPACE),
    ("dining area", onto.FUNCTIONAL_ZONE),
    ("section", onto.DRAWING_ANNOTATION), ("قطاع", onto.DRAWING_ANNOTATION),
])
def test_the_vocabulary_places_a_term_in_its_concept_class(term, concept_class):
    assert onto.classify_term(term).concept_class == concept_class


@pytest.mark.parametrize("term", [
    # Standard architectural terms that appear on NO project in this repo.
    # A vocabulary tuned to one drawing would not know them.
    "ward", "classroom", "workshop", "showroom", "plant room", "riser",
    "elevator", "loggia", "atrium", "cloakroom", "larder", "vestibule",
    "مصعد", "عيادة", "ورشة", "بهو", "شرفة", "مستودع",
])
def test_the_vocabulary_is_general_not_one_projects_word_list(term):
    """Breadth is the evidence that this is a vocabulary, not a lookup."""
    assert onto.classify_term(term).is_known, f"{term!r} not recognised"


def test_an_unrecognised_term_is_unknown_and_never_guessed():
    look = onto.classify_term("QQZZX")
    assert look.concept_class == onto.UNKNOWN
    assert not look.is_known


@pytest.mark.parametrize("term,other", [
    ("store", "storey"), ("bath", "bathurst"), ("hall", "hallmark"),
])
def test_matching_is_exact_not_substring(term, other):
    """`STORE` must not match `STOREY`; a substring rule is unpredictable."""
    assert onto.classify_term(term).is_known
    assert not onto.classify_term(other).is_known


def test_arabic_forms_normalise_to_one_term():
    a = onto.classify_term("حديقة")
    b = onto.classify_term("حديقه")          # taa marbuta typed as haa
    assert a.concept == b.concept == "GARDEN"


def test_no_term_is_claimed_by_two_concepts():
    assert onto.collisions() == [], onto.collisions()


# ------------------------------------------------- seeding from the words

@pytest.mark.parametrize("word,expected", [
    ("KITCHEN", ss.ROOM_LIKE), ("مطبخ", ss.ROOM_LIKE),
    ("STREET", ss.NON_SPACE_ANNOTATION),
    ("NEIGHBOUR", ss.NON_SPACE_ANNOTATION),
    ("GARDEN", ss.EXTERNAL_SPACE_LIKE),
    ("DINING AREA", ss.ZONE_LIKE),
    ("QQZZX", ss.ROOM_LIKE),          # unknown, but placed like a stamp
])
def test_the_seed_class_follows_the_concept_class(word, expected):
    assert ss.classify([_Text(word)]).observations[0].semantic_class == expected


def test_only_a_room_like_observation_may_seed():
    rep = ss.classify([_Text("KITCHEN"), _Text("GARDEN"), _Text("STREET"),
                       _Text("DINING AREA")])
    assert sorted(o.text for o in rep.seeds()) == ["KITCHEN"]


def test_an_unknown_term_still_seeds_so_geometry_survives():
    """§10: an unreadable label must not destroy correct geometry."""
    o = ss.classify([_Text("QQZZX")]).observations[0]
    assert o.may_seed
    assert ss.R_UNKNOWN_TERM in o.reasons


# ---------------------------------------------------- bilingual identity

def _obs(text, x=0.0, y=0.0, block="B"):
    return ident.Observation(f"OBS-{text}-{x}", text, x, y,
                             onto.classify_term(text), block)


def test_english_and_arabic_for_one_room_are_one_identity():
    rep = ident.reconcile([_obs("KITCHEN", 0, 0), _obs("مطبخ", 0, -300)])
    assert len(rep.groups) == 1
    g = rep.groups[0]
    assert g.relationship == ident.SAME_CONCEPT
    assert g.identity_status == ident.IDENTITY_ESTABLISHED
    assert g.normalized_identity == "KITCHEN"
    assert g.supporting_observations == 2, "two statements, one identity"
    assert rep.bilingual() == [g]


def test_two_different_room_concepts_in_one_place_conflict():
    rep = ident.reconcile([_obs("KITCHEN", 0, 0), _obs("BEDROOM", 0, -300)])
    g = rep.groups[0]
    assert g.relationship == ident.CONFLICT
    assert g.identity_status == ident.IDENTITY_CONFLICT
    assert not g.is_established


def test_a_known_name_beside_an_unknown_one_is_compatible():
    rep = ident.reconcile([_obs("KITCHEN", 0, 0), _obs("QQZZX", 0, -300)])
    g = rep.groups[0]
    assert g.relationship == ident.COMPATIBLE
    assert g.identity_status == ident.IDENTITY_ESTABLISHED
    assert g.normalized_identity == "KITCHEN"


def test_a_room_and_a_zone_together_are_not_a_conflict():
    rep = ident.reconcile([_obs("KITCHEN", 0, 0), _obs("DINING AREA", 0, -300)])
    g = rep.groups[0]
    assert g.relationship == ident.DIFFERENT_FUNCTIONAL_ZONE
    assert g.identity_status == ident.IDENTITY_ESTABLISHED


def test_two_unknown_labels_leave_the_identity_unknown():
    rep = ident.reconcile([_obs("QQZZX", 0, 0), _obs("ZZQQX", 0, -300)])
    assert rep.groups[0].identity_status == ident.IDENTITY_UNKNOWN
    assert rep.groups[0].relationship == ident.UNKNOWN_REL


def test_labels_far_apart_are_not_merged():
    rep = ident.reconcile([_obs("KITCHEN", 0, 0), _obs("BEDROOM", 50000, 0)])
    assert len(rep.groups) == 2
    assert all(g.is_established for g in rep.groups)


def test_labels_from_different_stamps_are_not_merged():
    """Two stamps can fall close together near a shared wall."""
    rep = ident.reconcile([_obs("KITCHEN", 0, 0, block="S1"),
                           _obs("BEDROOM", 500, 0, block="S2")])
    assert len(rep.groups) == 2


# -------------------------------------------------- boundary authority

def _ring(prefix, x0, y0, x1, y1):
    return [_Cand(f"{prefix}-S", "H", y0, x0, x1),
            _Cand(f"{prefix}-N", "H", y1, x0, x1),
            _Cand(f"{prefix}-W", "V", x0, y0, y1),
            _Cand(f"{prefix}-E", "V", x1, y0, y1)]


def test_a_site_ring_the_rooms_do_not_need_may_not_close_a_room():
    site = _ring("SITE", 0, 0, 60000, 40000)
    bldg = _ring("BLDG", 20000, 15000, 40000, 25000)
    rep = authority.classify(site + bldg, [_Obs(30000, 20000)])
    roles = {b.band_id: b.roles for b in rep.bands}
    assert all(authority.SITE_BOUNDARY in roles[b.band_id] for b in rep.bands
               if b.band_id.startswith("SITE"))
    assert not any(b.may_close_a_room for b in rep.bands
                   if b.band_id.startswith("SITE"))
    assert all(b.may_close_a_room for b in rep.bands
               if b.band_id.startswith("BLDG"))


def test_an_envelope_the_rooms_do_need_stays_eligible():
    """§5: overcorrecting would make every corner room unmeasurable."""
    bldg = _ring("BLDG", 0, 0, 20000, 12000)
    rep = authority.classify(bldg, [_Obs(10000, 6000)])
    assert all(b.may_close_a_room for b in rep.bands)
    assert any(authority.BUILDING_ENVELOPE in b.roles for b in rep.bands)


def test_a_band_may_hold_more_than_one_role():
    bldg = _ring("BLDG", 0, 0, 20000, 12000)
    rep = authority.classify(bldg, [_Obs(10000, 6000)])
    b = rep.bands[0]
    assert authority.BUILDING_ENVELOPE in b.roles
    assert authority.ROOM_BOUNDARY_ELIGIBLE in b.roles


def test_a_short_run_is_detail_but_may_still_form_a_room_side():
    """Short is not irrelevant. Excluding these emptied a real drawing."""
    short = _Cand("TICK", "H", 0.0, 0.0, 120.0)
    rep = authority.classify(_ring("B", 0, 0, 9000, 6000) + [short],
                             [_Obs(4500, 3000)])
    tick = next(b for b in rep.bands if b.band_id == "TICK")
    assert authority.DETAIL_GEOMETRY in tick.roles
    assert tick.may_close_a_room


def test_without_a_room_observation_nothing_is_eligible():
    rep = authority.classify(_ring("B", 0, 0, 9000, 6000), [])
    assert rep.eligible() == []
    assert all(authority.UNRESOLVED in b.roles for b in rep.bands)


def test_no_area_is_read_by_the_authority():
    import pathlib

    src = pathlib.Path("engine/boundary_authority.py").read_text(
        encoding="utf-8")
    assert "area_m2" not in src


# ------------------------------------------------------------ the freeze

def test_the_sixteen_round3_cases_hold():
    rep = r3.assert_frozen()
    assert rep["cases"] == 16
    assert rep["failed"] == 0
    assert rep["required_results_held"] is True


def test_round_2_safety_still_holds_under_round_3():
    from engine import round2_selftest as r2

    rep = r2.assert_frozen()
    assert rep["failed"] == 0


def test_the_freeze_hashes_are_stable():
    for fn in (r3.freeze_hash, authority.authority_hash,
               ident.reconciler_hash, onto.ontology_hash):
        assert fn() == fn() and len(fn()) == 24
