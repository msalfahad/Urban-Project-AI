"""T-064 controlled project data file (owner Q-17 A). Synthetic villa SV-PDF (sv_pdf_fixture.json, not a client
project): one record of each status, values typed in m, cm and mm. Every expected quantity is hand-calculated in the
test's docstring. The last tests load the converted development-villa file (research/urban_engine_m4_correctness/
project_data_st7757_t064.json) and check every profile key is present with the status the T-044 audit and the owner
answers give it."""

from __future__ import annotations

import copy
import json
import math
import os

import pytest

from engine.source import project_data_file as P

A = pytest.approx
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIX = os.path.join(HERE, "sv_pdf_fixture.json")
ST_DATA = os.path.join(ROOT, "research", "urban_engine_m4_correctness", "project_data_st7757_t064.json")
ST_PROFILE = os.path.join(ROOT, "research", "urban_engine_m4_correctness", "profile_st7757_m4.json")


def doc():
    with open(FIX, encoding="utf-8") as fh:
        return json.load(fh)


def rec(d, key):
    return next(r for r in d["records"] if r["key"] == key)


def faults_of(d):
    return P.validate(d)


# ---- the fixture itself ----------------------------------------------------------------------------------------------

def test_fixture_loads_with_one_record_of_each_status():
    pdf = P.load(doc())
    s = pdf.summary()
    assert all(s["by_status"][st] >= 1 for st in P.STATUSES)
    assert s["basis"] == P.BASIS
    assert set(s["not_usable"]) == {"NECK_TOP_LEVEL", "FOUNDING_DEPTH"}


@pytest.mark.parametrize("key,unit,typed,metres", [
    ("STOREY_HEIGHT_GF", "cm", 360, 3.60),      # 360 cm = 3.60 m
    ("SLAB_THICKNESS", "mm", 150, 0.15),        # 150 mm = 0.15 m
    ("BLINDING_THICKNESS", "m", 0.10, 0.10),    # already m
    ("BLINDING_PROJECTION", "cm", 10, 0.10),    # 10 cm = 0.10 m
])
def test_units_cm_mm_m_normalised_to_metres(key, unit, typed, metres):
    v = P.load(doc()).value(key, floor="GF", member={"STOREY_HEIGHT_GF": "COLUMN", "SLAB_THICKNESS": "SLAB"}.get(
        key, "FOOTING"))
    assert v["usable"] and v["unit"] == unit and v["value"] == typed
    assert v["value_m"] == A(metres, abs=1e-12)
    assert v["entered_by"] == P.TYPED and v["basis"] == P.BASIS


# ---- quantities: released only on usable values, otherwise HELD (never 0) -----------------------------------------------

def test_column_concrete_from_drawing_verified_height():
    """GF column 0.30 x 0.60 m, height = STOREY_HEIGHT_GF 360 cm = 3.60 m: 0.30 x 0.60 x 3.60 = 0.648 m3."""
    q = P.load(doc()).quantity(["STOREY_HEIGHT_GF"], lambda v: 0.30 * 0.60 * v["STOREY_HEIGHT_GF"],
                               floor="GF", member="COLUMN")
    assert q["state"] == P.RELEASABLE and q["quantity"] == A(0.648)
    assert q["basis"] == P.BASIS


def test_blinding_from_owner_confirmed_thickness_and_drawn_projection():
    """Footing 2.00 x 1.50 m; projection 10 cm each side -> 2.20 x 1.70 m; thickness 0.10 m (OWNER-CONFIRMED):
    2.20 x 1.70 x 0.10 = 0.374 m3."""
    q = P.load(doc()).quantity(
        ["BLINDING_THICKNESS", "BLINDING_PROJECTION"],
        lambda v: (2.00 + 2 * v["BLINDING_PROJECTION"]) * (1.50 + 2 * v["BLINDING_PROJECTION"]) * v["BLINDING_THICKNESS"],
        member="FOOTING")
    assert q["state"] == P.RELEASABLE and q["quantity"] == A(0.374)


def test_slab_from_designer_confirmed_thickness_in_mm():
    """1F slab panel 3.00 x 4.00 m at 150 mm (DESIGNER-CONFIRMED, applies to ALL floors): 12.00 x 0.15 = 1.80 m3."""
    q = P.load(doc()).quantity(["SLAB_THICKNESS"], lambda v: 3.00 * 4.00 * v["SLAB_THICKNESS"], floor="1F",
                               member="SLAB")
    assert q["quantity"] == A(1.80)


def test_inferred_with_logic_citing_verified_inputs_is_usable():
    """CLEAR_HEIGHT_GF 3.45 = 3.60 - 0.15 (both inputs verified); wall 5.00 m long: 5.00 x 3.45 = 17.25 m2."""
    pdf = P.load(doc())
    st, sl = pdf.value("STOREY_HEIGHT_GF", floor="GF", member="WALL"), pdf.value("SLAB_THICKNESS", floor="GF",
                                                                                  member="SLAB")
    assert st["value_m"] - sl["value_m"] == A(3.45)
    q = pdf.quantity(["CLEAR_HEIGHT_GF"], lambda v: 5.00 * v["CLEAR_HEIGHT_GF"], floor="GF", member="WALL")
    assert q["state"] == P.RELEASABLE and q["quantity"] == A(17.25)


def test_assumed_value_makes_its_quantity_held_and_never_zero():
    """Neck 0.30 x 0.30 m from footing top to NECK_TOP_LEVEL (ASSUMED 0.50 m): the quantity is HELD, None, and
    compute is never called (no number escapes, not even 0)."""
    called = []
    q = P.load(doc()).quantity(["NECK_TOP_LEVEL"], lambda v: called.append(1) or 0.09 * v["NECK_TOP_LEVEL"],
                               member="NECK")
    assert q["state"] == P.HELD and q["quantity"] is None and not called
    assert q["held_by"][0]["key"] == "NECK_TOP_LEVEL" and q["held_by"][0]["status"] == P.ASSUMED


def test_held_value_holds_and_is_shown_not_used():
    pdf = P.load(doc())
    v = pdf.value("FOUNDING_DEPTH", member="NECK")
    assert not v["usable"] and v["value"] is None and v["shown_value"] == 1.50
    assert "excavation" in v["reason"]
    q = pdf.quantity(["FOUNDING_DEPTH", "BLINDING_THICKNESS"], lambda v: 1.0, member="FOOTING")
    assert q["state"] == P.HELD and q["quantity"] is None
    assert [h["key"] for h in q["held_by"]] == ["FOUNDING_DEPTH"]


def test_missing_key_holds_the_quantity():
    q = P.load(doc()).quantity(["STOREY_HEIGHT_1F"], lambda v: 1.0, floor="1F", member="COLUMN")
    assert q["state"] == P.HELD and q["quantity"] is None and q["held_by"][0]["status"] == "MISSING"


def test_no_input_named_holds():
    q = P.load(doc()).quantity([], lambda v: 1.0)
    assert q["state"] == P.HELD and q["quantity"] is None


def test_compute_without_a_number_holds():
    q = P.load(doc()).quantity(["SLAB_THICKNESS"], lambda v: None, floor="GF", member="SLAB")
    assert q["state"] == P.HELD and q["quantity"] is None
    q = P.load(doc()).quantity(["SLAB_THICKNESS"], lambda v: float("nan"), floor="GF", member="SLAB")
    assert q["state"] == P.HELD and q["quantity"] is None


@pytest.mark.parametrize("floor,member,usable", [
    ("GF", "COLUMN", True),
    ("1F", "COLUMN", False),       # typed for GF only
    (None, "COLUMN", False),       # an unscoped call never picks up a floor-scoped value
    ("GF", "SLAB", False),         # member not in the list
    ("GF", None, False),
])
def test_applies_to_scope(floor, member, usable):
    assert P.load(doc()).value("STOREY_HEIGHT_GF", floor=floor, member=member)["usable"] is usable


def test_all_scope_covers_any_floor_but_not_other_members():
    pdf = P.load(doc())
    assert pdf.value("SLAB_THICKNESS", floor="2F", member="SLAB")["usable"]
    assert pdf.value("SLAB_THICKNESS", floor=None, member="SLAB")["usable"]
    assert not pdf.value("SLAB_THICKNESS", floor="2F", member="BEAM")["usable"]


def test_typed_lines_never_count_as_automatic_extraction():
    pdf = P.load(doc())
    typed = pdf.quantity(["SLAB_THICKNESS"], lambda v: 1.8, floor="1F", member="SLAB")
    auto = {"item": "STR.CONC.FOOTING", "quantity": 2.0, "basis": "CAD_GEOMETRY"}
    mixed = {"item": "STR.CONC.COLUMN", "quantity": 0.648, "inputs": [pdf.value("STOREY_HEIGHT_GF", floor="GF",
                                                                                   member="COLUMN")]}
    assert P.is_typed(typed) and P.is_typed(mixed) and not P.is_typed(auto)
    assert P.automatic_only([typed, auto, mixed]) == [auto]


def test_loaded_file_is_a_copy():
    d = doc()
    pdf = P.load(d)
    rec(d, "SLAB_THICKNESS")["value"] = 999
    assert pdf.value("SLAB_THICKNESS", floor="GF", member="SLAB")["value"] == 150


# ---- refusals ----------------------------------------------------------------------------------------------------

def _refused(d, *needles):
    f = P.validate(d)
    assert f, "expected a refusal"
    for n in needles:
        assert any(n in x for x in f), (n, f)
    with pytest.raises(P.ProjectDataFileError):
        P.load(d)


@pytest.mark.parametrize("empty", ["", "   ", None])
def test_record_without_source_is_refused(empty):
    d = doc()
    rec(d, "STOREY_HEIGHT_GF")["reviewer_or_source"] = empty
    _refused(d, "a record without a source is refused")


def test_record_with_source_field_removed_is_refused():
    d = doc()
    del rec(d, "BLINDING_THICKNESS")["reviewer_or_source"]
    _refused(d, "reviewer_or_source missing")


@pytest.mark.parametrize("field", ["drawing_file", "drawing_number", "revision", "sheet", "reference", "applies_to"])
def test_every_drawing_reference_field_is_required(field):
    d = doc()
    del rec(d, "SLAB_THICKNESS")[field]
    _refused(d, field)


def test_inferred_without_logic_is_refused():
    d = doc()
    del rec(d, "CLEAR_HEIGHT_GF")["logic"]
    _refused(d, "INFERRED without documented logic is refused")


def test_inferred_without_inputs_is_refused():
    d = doc()
    rec(d, "CLEAR_HEIGHT_GF")["inferred_from"] = []
    _refused(d, "must cite the verified keys")


def test_inferred_from_an_assumed_value_is_refused():
    d = doc()
    rec(d, "CLEAR_HEIGHT_GF")["inferred_from"] = ["STOREY_HEIGHT_GF", "NECK_TOP_LEVEL"]
    _refused(d, "NECK_TOP_LEVEL, whose status ASSUMED is not a verified input")


def test_inferred_from_another_inferred_or_unknown_or_itself_is_refused():
    d = doc()
    rec(d, "CLEAR_HEIGHT_GF")["inferred_from"] = ["CLEAR_HEIGHT_GF", "NOPE"]
    _refused(d, "INFERRED from itself", "'NOPE', which is not in the file")


def test_inferred_from_on_a_verified_record_is_refused():
    d = doc()
    rec(d, "SLAB_THICKNESS")["inferred_from"] = ["STOREY_HEIGHT_GF"]
    _refused(d, "inferred_from is for INFERRED records only")


def test_entered_by_other_than_typed_is_refused():
    d = doc()
    rec(d, "SLAB_THICKNESS")["entered_by"] = "AUTOMATIC"
    _refused(d, "entered_by must be TYPED")


@pytest.mark.parametrize("bad", ["VERIFIED", "drawing-verified", "PRINTED_VALUE", None])
def test_status_words_are_exact(bad):
    d = doc()
    rec(d, "SLAB_THICKNESS")["status"] = bad
    _refused(d, "status")


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, "16", [16]])
def test_number_value_must_be_finite_number(bad):
    d = doc()
    rec(d, "SLAB_THICKNESS")["value"] = bad
    _refused(d, "not a finite number")


@pytest.mark.parametrize("bad", ["inch", "ft", "M", None])
def test_unknown_unit_is_refused(bad):
    d = doc()
    rec(d, "SLAB_THICKNESS")["unit"] = bad
    _refused(d, "unit")


def test_value_missing_only_allowed_when_held():
    d = doc()
    rec(d, "FOUNDING_DEPTH")["value"] = None
    assert P.validate(d) == []
    rec(d, "SLAB_THICKNESS")["value"] = None
    _refused(d, "only a HELD record may have no value")
    d = doc()
    rec(d, "NECK_TOP_LEVEL")["value"] = None
    _refused(d, "only a HELD record may have no value")


def test_held_without_reason_and_reason_on_released_are_refused():
    d = doc()
    del rec(d, "FOUNDING_DEPTH")["hold_reason"]
    _refused(d, "HELD without hold_reason")
    d = doc()
    rec(d, "SLAB_THICKNESS")["hold_reason"] = "x"
    _refused(d, "hold_reason on a DESIGNER-CONFIRMED record")


def test_duplicate_key_wrong_project_unknown_field_refused():
    d = doc()
    d["records"].append(copy.deepcopy(rec(d, "SLAB_THICKNESS")))
    _refused(d, "duplicate key")
    d = doc()
    rec(d, "SLAB_THICKNESS")["project"] = "another villa"
    _refused(d, "is not the file's project")
    d = doc()
    rec(d, "SLAB_THICKNESS")["guess"] = 0.2
    _refused(d, "unknown field guess")


def test_applies_to_must_name_something():
    d = doc()
    rec(d, "SLAB_THICKNESS")["applies_to"] = {"floors": [], "members": []}
    _refused(d, "applies_to names no floor and no member")
    d = doc()
    rec(d, "SLAB_THICKNESS")["applies_to"] = {"rooms": ["R1"]}
    _refused(d, "applies_to must be")


def test_file_level_refusals():
    _refused({"schema": "X", "project": "p", "records": []}, "schema must be", "records must be a non-empty list")
    assert P.validate([]) == ["the file is not an object"]
    d = doc()
    d["extra"] = 1
    _refused(d, "unknown top-level field extra")


def test_a_refusal_lists_every_fault_and_loads_nothing():
    d = doc()
    rec(d, "SLAB_THICKNESS")["reviewer_or_source"] = ""
    del rec(d, "CLEAR_HEIGHT_GF")["logic"]
    with pytest.raises(P.ProjectDataFileError) as e:
        P.load(d)
    assert len(e.value.faults) == 2


def test_count_unit_must_be_whole():
    d = doc()
    r = rec(d, "SLAB_THICKNESS")
    r["unit"], r["value"] = "count", 2.5
    _refused(d, "a count must be a whole number")


def test_choice_and_table_values():
    d = doc()
    rec(d, "GB_SECTION_CLASS")["value"] = []
    _refused(d, "a table value must be a non-empty list or object")
    d = doc()
    rec(d, "GB_SECTION_CLASS")["unit"] = "m"
    _refused(d, "unit of a table must be 'none'")
    v = P.load(doc()).value("GB_SECTION_CLASS", member="GROUND_BEAM")
    assert v["usable"] and v["value"][0]["H"] == 0.40 and v["conditions"] == ["without concentrated load"]
    assert v["value_m"] is None


def test_policy_record():
    p = P.policy_record()
    assert p["holds_dependents"] == [P.ASSUMED, P.HELD] and p["entered_by"] == "TYPED"


# ---- the converted development-villa file --------------------------------------------------------------------------

EXPECTED_ST = {
    "STOREY_HEIGHT_GF": ("DRAWING-VERIFIED", 4.5), "STOREY_HEIGHT_1F": ("DRAWING-VERIFIED", 4.2),
    "STOREY_HEIGHT_2F": ("DRAWING-VERIFIED", 4.2), "GB_TYPICAL_SECTIONS": ("DRAWING-VERIFIED", None),
    "FOUNDING_DEPTH_M": ("HELD", None), "NECK_TOP_LEVEL_M": ("INFERRED", 1.0),
    "GF_FLOOR_LEVEL_M": ("DRAWING-VERIFIED", 1.0), "OUTER_GROUND_LEVEL_M": ("DRAWING-VERIFIED", 0.0),
    "GB_EXTERIOR_DETAIL": ("DRAWING-VERIFIED", None), "BLINDING_THICKNESS_M": ("DRAWING-VERIFIED", 0.1),
    "BLINDING_UNDER": ("DRAWING-VERIFIED", None), "CB_SUPPORT_BAR_EXTENT_FRAC": ("HELD", None),
    "CB_SUPPORT_BAR_SPAN_BASIS": ("HELD", None), "CB_BOTTOM_EXTENSION_M": ("DRAWING-VERIFIED", 0.075),
    "SLAB_PROJECT_DEFAULT_THICKNESS_M": ("DRAWING-VERIFIED", 0.16), "BLINDING_PROJECTION_M": ("DRAWING-VERIFIED", 0.1),
    "LINTEL_SCHEDULE": ("DRAWING-VERIFIED", None),
}


def test_st7757_conversion_covers_every_profile_key_with_its_status():
    with open(ST_PROFILE, encoding="utf-8") as fh:
        prof = json.load(fh)
    pdf = P.load_path(ST_DATA)
    assert {c["id"] for c in prof["conventions"]} == set(pdf.keys()) == set(EXPECTED_ST)
    for k, (status, val) in EXPECTED_ST.items():
        r = pdf.records[k]
        assert r["status"] == status, k
        assert r["entered_by"] == "TYPED" and r["reviewer_or_source"].strip()
        if val is not None:
            assert r["value"] == A(val), k
    assert pdf.summary()["by_status"]["DRAWING-VERIFIED"] == 13


def test_st7757_necks_held_columns_and_slab_usable():
    """Owner Q-21 C: no neck on the unresolved founding datum; storey heights and the 0.16 m slab (Q-14) usable."""
    pdf = P.load_path(ST_DATA)
    neck = pdf.dependency(["FOUNDING_DEPTH_M", "NECK_TOP_LEVEL_M"], floor="FOUNDATION", member="NECK")
    assert neck["state"] == P.HELD and [h["key"] for h in neck["held_by"]] == ["FOUNDING_DEPTH_M"]
    for fl, h in (("GF", 4.5), ("1F", 4.2), ("2F", 4.2)):
        v = pdf.value("STOREY_HEIGHT_" + fl, floor=fl, member="COLUMN")
        assert v["usable"] and v["value_m"] == A(h)
    assert pdf.value("SLAB_PROJECT_DEFAULT_THICKNESS_M", floor="1F", member="SLAB")["value_m"] == A(0.16)
    assert not pdf.value("SLAB_PROJECT_DEFAULT_THICKNESS_M", floor="1F", member="STAIR")["usable"]


def test_st7757_profile_file_itself_is_unchanged_shape():
    with open(ST_PROFILE, encoding="utf-8") as fh:
        prof = json.load(fh)
    assert prof["profile"] == "ST7757_M4" and prof["manual_inputs"] == 17 and len(prof["conventions"]) == 17
