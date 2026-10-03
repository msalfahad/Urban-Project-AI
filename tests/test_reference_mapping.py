"""A reference may only be opened where it maps to exactly one space.

The failure this prevents is quiet and convincing: take a schedule row
labelled "Bedroom", find a bedroom, compare, report agreement. On a floor
with six bedrooms that number looks like validation and is not.
"""

import pytest

from engine import reference_mapping as rm

SPACES = {
    "BED-01": {"name_en": "Bedroom 1", "room_type": "BEDROOM"},
    "BED-02": {"name_en": "Bedroom 2", "room_type": "BEDROOM"},
    "BED-04": {"name_en": "Bedroom 4", "room_type": "BEDROOM"},
    # Name and type deliberately DIFFERENT: a fixture where they coincide
    # cannot tell a name match from a type match.
    "STR-01": {"name_en": "Store Room", "room_type": "STORE"},
}

CLEAR = "CLEAR_INTERNAL_FINISH_FACE"


def _row(label, value=20.0, basis=CLEAR, row_id="R-1"):
    return rm.ReferenceRow(row_id=row_id, label=label, value=value,
                           unit="m2", basis=basis, source="SCHEDULE")


def _one(label, **kw):
    rep = rm.resolve([_row(label, **kw)], SPACES,
                     compatible_bases=(CLEAR,))
    return rep.resolutions[0]


# --- the sealed benchmark -------------------------------------------------

def test_the_sealed_site_benchmark_is_refused_by_name():
    # Enforced in code rather than remembered, so no future caller can reach
    # it by passing a path.
    with pytest.raises(rm.SealedReferenceError) as e:
        rm.refuse_if_sealed("data/golden/23010/site_benchmark.json")
    assert "spend it" in str(e.value)


def test_a_reference_that_is_not_sealed_passes_the_guard():
    rm.refuse_if_sealed("data/golden/23010/topology_overlay.json")


# --- the mapping ----------------------------------------------------------

def test_a_row_naming_one_space_resolves():
    got = _one("Bedroom 1")
    assert got.status == rm.RESOLVED
    assert got.space_id == "BED-01"
    assert got.may_be_compared


def test_a_space_id_resolves_directly():
    assert _one("BED-02").space_id == "BED-02"


def test_matching_is_case_and_spacing_insensitive():
    assert _one("  bedroom   1 ").space_id == "BED-01"


def test_a_generic_room_type_row_is_refused():
    # THE case: "Bedroom" on a floor with three bedrooms.
    got = _one("Bedroom")
    assert got.status == rm.UNRESOLVED
    assert got.reason == rm.AMBIGUOUS_NAME
    assert set(got.candidates) == {"BED-01", "BED-02", "BED-04"}
    assert not got.may_be_compared
    assert "Picking one would manufacture a comparison" in got.why


def test_a_room_type_is_never_a_resolution_even_when_unique():
    # STORE matches exactly one space, and it is still a TYPE, not a name.
    # Letting a unique type resolve would make the rule depend on how many
    # rooms of that type the floor happens to have.
    got = _one("STORE")
    assert got.status == rm.UNRESOLVED
    assert got.reason == rm.AMBIGUOUS_NAME
    assert got.candidates == ("STR-01",)


def test_a_row_matching_nothing_is_not_evidence_about_anything():
    got = _one("Cinema")
    assert got.reason == rm.NO_MATCH


def test_two_rows_claiming_one_space_both_stay_unresolved():
    rep = rm.resolve([_row("Bedroom 1", row_id="R-1"),
                      _row("BED-01", row_id="R-2")],
                     SPACES, compatible_bases=(CLEAR,))
    assert [r.reason for r in rep.resolutions] == [rm.DUPLICATE_CLAIM] * 2
    assert rep.record()["mapped_to_one_space"] == 0


def test_an_alias_can_map_a_row_the_project_knows_by_another_name():
    rep = rm.resolve([_row("Master Bedroom")], SPACES,
                     compatible_bases=(CLEAR,),
                     aliases={"Master Bedroom": "BED-01"})
    assert rep.resolutions[0].space_id == "BED-01"


# --- the basis ------------------------------------------------------------

def test_a_row_without_a_basis_maps_but_is_not_compared():
    got = _one("Bedroom 1", basis="")
    assert got.reason == rm.BASIS_NOT_STATED
    assert got.space_id == "BED-01"          # the mapping IS recorded
    assert not got.may_be_compared
    assert "different quantities of the same room" in got.why


def test_a_row_on_a_different_basis_is_not_compared():
    got = _one("Bedroom 1", basis="STRUCTURAL_OPENING")
    assert got.reason == rm.BASIS_INCOMPATIBLE
    assert "would report the difference between two bases as an error" in \
        got.why


def test_a_row_with_no_value_records_the_mapping_and_no_comparison():
    got = _one("Bedroom 1", value=None)
    assert got.reason == rm.NO_VALUE
    assert got.space_id == "BED-01"
    assert not got.may_be_compared


# --- the report -----------------------------------------------------------

def test_the_report_counts_only_comparable_rows_as_mapped():
    rep = rm.resolve([_row("Bedroom 1", row_id="R-1"),
                      _row("Bedroom", row_id="R-2"),
                      _row("Cinema", row_id="R-3")],
                     SPACES, compatible_bases=(CLEAR,))
    r = rep.record()
    assert r["rows"] == 3
    assert r["mapped_to_one_space"] == 1
    assert r["unresolved"] == 2
    assert r["by_reason"] == {rm.AMBIGUOUS_NAME: 1, rm.NO_MATCH: 1}


def test_the_report_states_why_a_generic_row_is_refused():
    r = rm.resolve([], SPACES).record()
    assert "looks like validation and is not" in r[
        "why_a_generic_row_is_refused"]
    assert "not compared, not averaged and not counted as agreement" in \
        r["rule"]
