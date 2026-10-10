"""Canonical groups: an id is chosen from a registry, never written by a model.

Run 0's comparison reported 0% agreement on apartment_id and zone_id across all
36 spaces. Nothing was wrong with either agent — A1 wrote APT-EAST and A2 wrote
APT-01, and string equality had no way to tell whether those were the same
apartment. These tests hold the fix, and hold the harder half of it: where a
hierarchy does not exist, the registry says so instead of inventing one.
"""

from __future__ import annotations

import pytest

from engine.group_registry import (AMBIGUOUS, APARTMENT, NOT_DEFINED, UNKNOWN,
                                   ZONE, CanonicalGroup, GroupRegistry,
                                   GroupRegistryError, membership)

REAL = GroupRegistry.load("data/registry/23010_groups.json")


def test_the_project_registry_loads_and_names_two_units():
    assert sorted(REAL.apartments) == ["APT-001", "APT-002"]
    assert REAL.project == "23010"


def test_every_group_carries_a_definition_and_a_provenance():
    for g in REAL.apartments.values():
        assert g.definition.strip() and g.provenance


def test_a_group_without_a_definition_is_refused():
    with pytest.raises(GroupRegistryError, match="needs a definition"):
        CanonicalGroup(id="APT-001", kind=APARTMENT, definition="  ",
                       provenance="OWNER_SCOPE_BRIEF")


@pytest.mark.parametrize("bad", ["APT-EAST", "APT-01", "EAST_RESIDENTIAL",
                                 "apt-001", "APT-1", "APARTMENT_ONE"])
def test_a_free_text_group_id_is_refused(bad):
    """Exactly the values Run 0's two agents produced between them."""
    with pytest.raises(GroupRegistryError, match="not a canonical"):
        CanonicalGroup(id=bad, kind=APARTMENT, definition="x",
                       provenance="OWNER_SCOPE_BRIEF")


def test_reserved_answers_cannot_be_group_ids():
    for reserved in (UNKNOWN, AMBIGUOUS):
        with pytest.raises(GroupRegistryError, match="reserved"):
            CanonicalGroup(id=reserved, kind=APARTMENT, definition="x",
                           provenance="OWNER_SCOPE_BRIEF")


def test_unknown_and_ambiguous_are_always_available_answers():
    assert REAL.allowed(APARTMENT) == {"APT-001", "APT-002", UNKNOWN, AMBIGUOUS}


# --- the honest half: no ontology means no field -----------------------------

def test_23010_has_no_zone_ontology_and_says_why():
    assert not REAL.zone_ontology_defined
    assert REAL.zones == NOT_DEFINED
    assert "no approved zone ontology" in REAL.zone_not_defined_reason


def test_with_no_ontology_the_only_zone_answer_is_unknown():
    """Not even AMBIGUOUS: there is nothing to be ambiguous between."""
    assert REAL.allowed(ZONE) == {UNKNOWN}
    with pytest.raises(GroupRegistryError, match="no zone ontology"):
        REAL.validate_assignment(ZONE, AMBIGUOUS, space_id="SPACE-001")


def test_an_undefined_zone_field_is_not_scorable():
    ok, why = REAL.scorable(ZONE)
    assert not ok and "no zone ontology" in why
    assert REAL.scorable(APARTMENT) == (True, "")


def test_a_registry_that_hides_a_missing_ontology_is_refused():
    with pytest.raises(GroupRegistryError, match="no reason is recorded"):
        GroupRegistry(project="X", apartments={})


def test_apartments_can_never_be_not_defined():
    """A floor belongs to at least one dwelling; NOT_DEFINED there is a bug."""
    with pytest.raises(GroupRegistryError, match="cannot be NOT_DEFINED"):
        GroupRegistry.from_dict({"project": "X", "apartments": NOT_DEFINED})


# --- membership is what the id means -----------------------------------------

def test_membership_on_23010_is_deliberately_not_pre_answered():
    """Handing the agents the member list would hand them the acceptance test."""
    for g in REAL.apartments.values():
        assert not g.membership_is_authoritative
        assert g.member_space_ids is None


def test_membership_groups_spaces_by_their_assigned_id():
    class S:
        def __init__(self, sid, apt):
            self.space_id, self.apartment_id = sid, apt
    m = membership([S("A", "APT-001"), S("B", "APT-001"), S("C", "APT-002")],
                   APARTMENT)
    assert m == {"APT-001": {"A", "B"}, "APT-002": {"C"}}
