"""Round 2: a closed polygon is not a room, and text inside it is not a name.

Round 1 released a 443.841 m² polygon labelled `W.C`. It was the plot. Every
gate passed — complete, identified, undisputed by any dimension — because
none of them asked what KIND of enclosure it was.

These tests hold the two classifiers that now ask, and they check the thing
that actually matters: **what was RELEASED**, not what was labelled. The
first version of the synthetic check looked only at the role, so when the
classifier called a site polygon a room candidate the case passed vacuously
while releasing exactly what it existed to forbid.

No string from any real drawing appears here, and no expected room size —
the classifiers are forbidden to read an area, so a test that stated one
would be testing nothing.
"""

from __future__ import annotations

import pytest

from engine import enclosure_role as roles
from engine import round2_selftest as r2
from engine import semantic_seed as ss
from engine import wall_role as wr


class _Prov:
    def __init__(self, oid, block=()):
        self.object_id = oid
        self.block_path = tuple(block)


class _Text:
    def __init__(self, value, x, y, block=()):
        self.value = value
        self.x = x
        self.y = y
        self.provenance = _Prov(f"CAD-{value}", block)


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


# --------------------------------------------------------- semantic seeds

@pytest.mark.parametrize("text", [
    "31.37", "15.00", "+0.15", "-2.40", "0.00", "%%p0.00", "1200 mm",
    "(3.65)", "  7,25  ",
])
def test_a_number_is_a_measurement_not_a_room_name(text):
    """A room is not named by a numeral, in any language."""
    rep = ss.classify([_Text(text, 0, 0, ("B",))])
    o = rep.observations[0]
    assert o.semantic_class == ss.NON_SPACE_ANNOTATION
    assert ss.R_NUMERIC in o.reasons
    assert not o.may_seed


@pytest.mark.parametrize("text", [
    "SOMETHING PLAN 1:100", "SECTION A-A  1 : 50", "DETAIL 1:5",
])
def test_a_scale_ratio_marks_a_drawing_title(text):
    rep = ss.classify([_Text(text, 0, 0, ("B",))])
    assert rep.observations[0].semantic_class == ss.NON_SPACE_ANNOTATION
    assert ss.R_SCALE in rep.observations[0].reasons


@pytest.mark.parametrize("text", ["ALPHA", "BETA ROOM", "W.C", "UPPER HALL"])
def test_a_name_inside_a_placed_symbol_may_seed(text):
    rep = ss.classify([_Text(text, 0, 0, ("B",))])
    o = rep.observations[0]
    assert o.semantic_class == ss.ROOM_LIKE
    assert o.may_seed


def test_loose_text_is_ambiguous_and_seeds_nothing():
    rep = ss.classify([_Text("ALPHA", 0, 0)])          # no carrier block
    o = rep.observations[0]
    assert o.semantic_class == ss.AMBIGUOUS
    assert ss.R_LOOSE in o.reasons
    assert not o.may_seed
    assert rep.seeds() == []


def test_a_label_outside_the_built_fabric_names_something_outside_it():
    """Decided by geometry the caller supplies, never by the words."""
    inside = lambda x, y: x < 1000        # noqa: E731 - a test stub
    rep = ss.classify([_Text("ALPHA", 0, 0, ("B",)),
                       _Text("BETA", 9000, 0, ("B",))],
                      built_fabric=inside)
    by_text = {o.text: o for o in rep.observations}
    assert by_text["ALPHA"].semantic_class == ss.ROOM_LIKE
    assert by_text["BETA"].semantic_class == ss.NON_SPACE_ANNOTATION
    assert ss.R_OUTSIDE in by_text["BETA"].reasons


# Words from the real drawing. They appear HERE, in the test, precisely so
# they can be shown to receive no special treatment in the classifier.
_REAL_WORDS = ("SALOON", "KITCHEN", "DEWANEYA", "NEIGHBOUR", "SEA VIEW",
               "STREET", "W.C", "PANTRY", "GARDEN", "DRIVER")


@pytest.mark.parametrize("word", _REAL_WORDS)
def test_a_real_project_word_is_judged_by_the_general_vocabulary(word):
    """Round 3 corrected this test, and the correction matters.

    It used to demand that `KITCHEN` classify EXACTLY like the nonsense
    word `QQZZX` — no reason may differ. That was the wrong invariant: it
    made the semantic layer blind, so it could not tell a kitchen from a
    street, and a street label seeded a physical room.

    The invariant that replaces it is narrower and is the one that matters:
    a real project's word must be judged by the GENERAL vocabulary, by the
    same lookup as any other term, and never by a rule that names it. So
    each word is required to reach its class through the vocabulary — the
    same path a term from a drawing nobody here has seen would take.
    """
    from engine import architectural_ontology as onto

    o = ss.classify([_Text(word, 0, 0, ("B",))]).observations[0]
    look = onto.classify_term(word)
    if look.is_known:
        # Its class came from the vocabulary's concept class, not from a
        # rule mentioning this string.
        assert ss.R_VOCABULARY in o.reasons
        assert f"CONCEPT_{look.concept}" in o.reasons
        assert o.semantic_class == ss._FROM_ONTOLOGY[look.concept_class]
    else:
        # Unrecognised: it takes the same path as any unknown term.
        made_up = ss.classify([_Text("QQZZX", 0, 0, ("B",))]).observations[0]
        assert o.semantic_class == made_up.semantic_class
        assert o.reasons == made_up.reasons


def test_the_vocabulary_contains_no_rule_naming_one_project(_=None):
    """The hardcoding invariant, stated where it belongs.

    Nothing may branch on a specific project's string. The vocabulary is
    data, applied uniformly, and a term from it is looked up exactly as a
    term from any other drawing would be.
    """
    from engine import architectural_ontology as onto

    for word in _REAL_WORDS:
        look = onto.classify_term(word)
        if not look.is_known:
            continue
        # The concept it reaches must also be reachable by OTHER terms —
        # a concept with exactly one term, matching one project's spelling,
        # would be that project's rule wearing a general name.
        concept = next(c for c in onto.concepts() if c.key == look.concept)
        assert len(concept.terms) > 1, (
            f"concept {concept.key} is named only by {concept.terms}")


def test_no_real_project_string_is_hardcoded_in_the_executable_code():
    """A source check, on code rather than on prose.

    The module's docstring quotes the real strings to explain round 1's
    failure, which is documentation. What must not exist is a string
    literal in the LOGIC that matches one of them.
    """
    import ast
    import pathlib

    tree = ast.parse(
        pathlib.Path("engine/semantic_seed.py").read_text(encoding="utf-8"))
    # Exclude docstring NODES by identity. Comparing against
    # ast.get_docstring() does not work: it returns the cleaned, dedented
    # text while the Constant holds the raw source string, so nothing
    # matched and every docstring was scanned as if it were logic.
    docstring_nodes = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            continue
        body = getattr(node, "body", None)
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            docstring_nodes.add(id(body[0].value))
    literals = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and id(n) not in docstring_nodes]
    joined = "\n".join(literals)
    for word in _REAL_WORDS:
        assert word not in joined, (
            f"{word!r} appears in a string literal the classifier can act on")


# ------------------------------------------------------- enclosure roles

_BIG = "POLYGON ((0 0, 30000 0, 30000 15000, 0 15000, 0 0))"
_SMALL = "POLYGON ((0 0, 5000 0, 5000 4000, 0 4000, 0 0))"
_WITH_VOID = ("POLYGON ((0 0, 20000 0, 20000 14000, 0 14000, 0 0), "
              "(7000 5000, 13000 5000, 13000 9000, 7000 9000, 7000 5000))")


def _obs(x, y, name="A"):
    return ss.SpaceObservation(f"OBS-{name}", name, x, y, ss.ROOM_LIKE, ())


def test_several_observations_with_material_between_them_is_a_super_region():
    """§3's invariant: it can never be released as ONE physical room."""
    wall = _Cand("W1", "V", 15000.0, 0.0, 15000.0)
    rep = roles.classify([("E1", _BIG)],
                         [_obs(5000, 7000, "A"), _obs(25000, 7000, "B")],
                         [wall])
    v = rep.verdicts[0]
    assert v.role == roles.SUPER_REGION
    assert v.separating_partitions >= 1
    assert not v.may_release


def test_two_observations_with_nothing_between_them_is_not_a_super_region():
    """Open plan. The separating-material test is what tells them apart."""
    rep = roles.classify([("E1", _BIG)],
                         [_obs(5000, 7000, "A"), _obs(25000, 7000, "B")], [])
    v = rep.verdicts[0]
    assert v.separating_partitions == 0
    assert v.role != roles.SUPER_REGION
    assert not v.may_release, "unresolved still releases nothing"


def test_one_observation_and_no_structure_is_a_room_candidate():
    rep = roles.classify([("E1", _SMALL)], [_obs(2500, 2000)], [])
    v = rep.verdicts[0]
    assert v.role == roles.PHYSICAL_ROOM
    assert v.may_release


def test_an_interior_void_makes_the_enclosure_unresolved():
    """The flood could not enter something enclosed inside this polygon.

    This is what caught P7757's 443 m2 plot: six interior voids, which are
    the building's own rooms. Deliberately conservative — a room with a
    column in it will not release either, and a false release is worse.
    """
    rep = roles.classify([("E1", _WITH_VOID)], [_obs(2000, 2000)], [])
    v = rep.verdicts[0]
    assert v.interior_voids == 1
    assert v.role == roles.UNRESOLVED
    assert not v.may_release
    assert any("could not enter" in e for e in v.evidence)


def test_an_enclosure_containing_another_is_not_a_leaf():
    rep = roles.classify([("OUTER", _BIG), ("INNER", _SMALL)],
                         [_obs(2500, 2000)], [])
    outer = next(v for v in rep.verdicts if v.enclosure_id == "OUTER")
    assert outer.nested_enclosures == 1
    assert outer.role in (roles.SITE_OR_PLOT, roles.BUILDING_ENVELOPE)
    assert not outer.may_release


def test_an_enclosure_with_no_observation_is_a_void_not_a_room():
    rep = roles.classify([("E1", _SMALL)], [], [])
    assert rep.verdicts[0].role == roles.VOID_OR_SHAFT
    assert not rep.verdicts[0].may_release


def test_only_one_role_is_ever_releasable():
    assert roles.RELEASABLE_ROLE == roles.PHYSICAL_ROOM
    for role in (roles.SITE_OR_PLOT, roles.BUILDING_ENVELOPE,
                 roles.SUPER_REGION, roles.VOID_OR_SHAFT,
                 roles.DETAIL_OR_ANNOTATION, roles.UNRESOLVED):
        assert role != roles.RELEASABLE_ROLE


def test_no_size_test_exists_in_the_role_classifier():
    import pathlib

    src = pathlib.Path("engine/enclosure_role.py").read_text(encoding="utf-8")
    assert "area_m2" not in src, "the role classifier must not read an area"
    assert "no_size_test_exists" in roles.frozen_parameters()["why"]


# ------------------------------------------------------------ wall roles

def test_a_band_with_space_on_both_sides_is_an_internal_partition():
    band = _Cand("B1", "V", 5000.0, 0.0, 4000.0)
    rep = wr.classify([band], interior=lambda x, y: True)
    assert rep.bands[0].role == wr.INTERNAL_PARTITION
    assert rep.bands[0].occupied_sides == 2


def test_a_band_with_nothing_occupied_bounds_ground_not_space():
    band = _Cand("B1", "H", 0.0, 0.0, 30000.0)
    rep = wr.classify([band], interior=lambda x, y: False)
    assert rep.bands[0].role == wr.SITE_BOUNDARY
    assert rep.bands[0].occupied_sides == 0


def test_without_an_occupancy_test_nothing_is_established():
    band = _Cand("B1", "H", 0.0, 0.0, 30000.0)
    rep = wr.classify([band])
    assert rep.bands[0].role == wr.UNRESOLVED


def test_no_layer_name_appears_in_the_wall_role_classifier():
    import pathlib

    src = pathlib.Path("engine/wall_role.py").read_text(encoding="utf-8")
    body = "\n".join(line for line in src.splitlines()
                     if not line.strip().startswith("#"))
    for name in ('"W"', "'W'", '"S-COL.BON"', '"TOI"'):
        assert name not in body


# ----------------------------------------------------------- the freeze

def test_the_twelve_round2_cases_all_hold_the_safety_result():
    rep = r2.assert_frozen()
    assert rep["cases"] == 12
    assert rep["failed"] == 0
    assert "NO site" in rep["safety_result"]


def test_the_freeze_hashes_are_stable():
    a, b = r2.freeze_hash(), r2.freeze_hash()
    assert a == b and len(a) == 24
    assert len(roles.classifier_hash()) == 24
    assert len(ss.classifier_hash()) == 24
    assert len(wr.classifier_hash()) == 24
