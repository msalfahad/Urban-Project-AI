"""E40 — the read-only QA workbook.

Most of these tests are about what the workbook may NOT do. A reporting layer
is dangerous in exactly one way: if anything it reports can re-enter the
calculation, the calculation has been calibrated to its own output. So the
contract is enforced here, not merely written in a docstring.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from engine import qa_workbook as qw
from engine.qa_workbook import (AGREES, DIFFERS, NOT_COMPARED, SHEET_ORDER,
                                UNKNOWN, QaWorkbookError, Sheet,
                                build_workbook, cell, exceptions,
                                flooring_ceramic_qa, random_qa_sample,
                                room_count_summary, room_register,
                                takeoff_coverage, wall_quantities)

SPACES = [
    {"space_id": "BED-01", "name_en": "Bedroom 1", "name_ar": "غرفة",
     "room_type": "BEDROOM", "scope": "IN_SCOPE", "region": 75,
     "geometry_type": "RECTANGLE", "floor_area_m2": 21.4},
    {"space_id": "BTH-01", "name_en": "Bathroom 1", "name_ar": "حمام",
     "room_type": "BATHROOM", "scope": "IN_SCOPE", "region": 88,
     "geometry_type": "RECTANGLE", "floor_area_m2": 4.08},
    {"space_id": "WSH-01", "name_en": "Washroom", "name_ar": "مغاسل",
     "room_type": "WASHROOM", "scope": "AMBIGUOUS", "region": 441,
     "geometry_type": "UNRESOLVED", "floor_area_m2": None},
]

BUNDLE = {
    "project_id": "23010",
    "spaces": SPACES,
    "quantities": {"BED-01": {"floor_area_m2": 21.4},
                   "BTH-01": {"floor_area_m2": 4.08,
                              "ceramic_wall_length_m": 8.6}},
    "releases": {"BED-01": {"GROSS_PERIMETER": "READY", "primary_blocker": ""},
                 "BTH-01": {"GROSS_PERIMETER": "READY",
                            "GROSS_CERAMIC_WALL": "BLOCKED_HEIGHT",
                            "primary_blocker": "height"}},
    "wall_records": [{"space_id": "BED-01", "gross_room_perimeter_m": 18.6,
                      "opening_count": 0, "open_length_m": 0.0}],
    "coverage": [{"use": "FLOORING", "ready": 2, "blocked": 1,
                  "not_applicable": 0, "applicable": 3}],
}


# --- the one-way arrow --------------------------------------------------------

def test_the_data_layer_cannot_reach_an_engine_it_could_write_back_to():
    """Not a convention — checked. The module imports no geometry, wall,
    opening, benchmark or golden module, so a reported figure has no path back
    into a calculation."""
    tree = ast.parse(Path(qw.__file__).read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    assert not [m for m in imported if m.startswith("engine")], imported
    assert not [m for m in imported if m.startswith("agents")], imported


def test_the_data_layer_writes_nothing_at_all():
    """No file handles, no open(), no persistence. It returns data."""
    src = Path(qw.__file__).read_text()
    for forbidden in ("open(", "Path(", "json.dump", "firestore", ".save("):
        assert forbidden not in src, forbidden


def test_the_writer_adds_no_values_of_its_own():
    """Presentation only. If the writer computed, there would be two places a
    quantity could come from and they would have to agree."""
    from engine import qa_writer
    src = Path(qa_writer.__file__).read_text()
    for forbidden in ("round(", " / ", " * len", "sum("):
        assert forbidden not in src, forbidden


def test_no_materials_no_recipes_no_pricing_anywhere():
    src = Path(qa_workbook_path := qw.__file__).read_text().lower()
    for forbidden in ("price", "rate_kd", "cost", "material_recipe", "kwd"):
        assert forbidden not in src, (forbidden, qa_workbook_path)


# --- zero is not unknown ------------------------------------------------------

def test_an_unknown_is_never_written_as_zero():
    """The single most expensive mistake a takeoff can make: turning "we have
    not measured this" into "there is none of it"."""
    assert cell(None) == UNKNOWN
    assert cell("") == UNKNOWN
    assert cell(0) == 0
    assert cell(0.0) == 0.0


def test_a_proved_zero_survives_as_a_number():
    """Zero openings proved is a finding. It must not be blanked out."""
    sheet = wall_quantities(BUNDLE["wall_records"], BUNDLE["releases"])
    assert sheet.values("opening_count") == [0]
    assert sheet.values("open_length_m") == [0.0]


def test_a_missing_area_reads_not_established_not_zero():
    reg = room_register(SPACES)
    assert reg.values("floor_area_m2") == [21.4, 4.08, UNKNOWN]


def test_zero_can_be_refused_where_it_could_not_be_a_real_result():
    with pytest.raises(QaWorkbookError, match="NOT_ESTABLISHED"):
        cell(0, allow_zero=False)


# --- no recalculation ---------------------------------------------------------

def test_no_quantity_is_derived_from_another():
    """A ceramic wall area is length x height. The exporter has both columns and
    must still leave the area NOT_ESTABLISHED unless it was established
    upstream — deriving it here would be the exporter quoting itself."""
    q = {"BTH-01": {"ceramic_wall_length_m": 8.6, "ceramic_wall_height_m": 2.4}}
    sheet = flooring_ceramic_qa([SPACES[1]], q, {})
    assert sheet.values("ceramic_wall_length_m") == [8.6]
    assert sheet.values("ceramic_wall_height_m") == [2.4]
    assert sheet.values("ceramic_wall_area_m2") == [UNKNOWN]   # not 20.64


# --- manual comparison --------------------------------------------------------

def test_an_empty_manual_column_is_not_agreement():
    """A workbook that prints AGREES against a blank column has invented a
    confirmation."""
    s = room_count_summary(SPACES)
    assert set(s.values("verdict")) == {NOT_COMPARED}
    assert set(s.values("manual_expected_count")) == {UNKNOWN}


def test_a_supplied_manual_count_is_compared_and_can_disagree():
    s = room_count_summary(SPACES, {"BATHROOM": 1, "BEDROOM": 2})
    by_type = {r["room_type"]: r for r in s.rows}
    assert by_type["BATHROOM"]["verdict"] == AGREES
    assert by_type["BEDROOM"]["verdict"] == DIFFERS
    assert by_type["BEDROOM"]["difference"] == -1
    assert by_type["WASHROOM"]["verdict"] == NOT_COMPARED


def test_the_manual_columns_exist_even_with_no_manual_data():
    """Manual qiyal is not a production dependency, but the column for it is
    always there: a project that HAS a manual count must be able to use it
    without the workbook changing shape."""
    s = room_count_summary(SPACES)
    assert "manual_expected_count" in s.columns
    assert "manual_expected_count" in s.human_columns


# --- the sample ---------------------------------------------------------------

def test_the_sample_is_reproducible_for_the_same_project():
    a = random_qa_sample(SPACES, {}, {}, project_id="23010")
    b = random_qa_sample(SPACES, {}, {}, project_id="23010")
    assert a.values("space_id") == b.values("space_id")


def test_two_projects_do_not_draw_the_same_rooms():
    a = random_qa_sample(SPACES * 3, {}, {}, project_id="23010", per_stratum=1)
    b = random_qa_sample(SPACES * 3, {}, {}, project_id="24001", per_stratum=1)
    assert a.name == b.name            # same sheet, different draw is allowed
    assert isinstance(a.rows, tuple)


def test_the_sample_is_stratified_so_it_cannot_land_all_on_bathrooms():
    many = [dict(s, space_id=f"{s['space_id']}-{i}")
            for i in range(6) for s in SPACES]
    s = random_qa_sample(many, {}, {}, project_id="23010", per_stratum=2)
    counts = {}
    for r in s.rows:
        counts[r["stratum"]] = counts.get(r["stratum"], 0) + 1
    assert counts == {"BEDROOM": 2, "BATHROOM": 2, "WASHROOM": 2}


def test_the_seed_is_recorded_in_the_sheet_itself():
    """A sample nobody can reproduce is an anecdote."""
    s = random_qa_sample(SPACES, {}, {}, project_id="23010")
    assert any("Seed" in n or "seed" in n for n in s.notes)


def test_blocked_spaces_are_eligible_for_the_sample():
    """Checking only what the engine is already confident about measures
    nothing."""
    s = random_qa_sample(SPACES, {}, {}, project_id="23010", per_stratum=3)
    assert "WSH-01" in s.values("space_id")


# --- coverage, and the total that must not exist ------------------------------

def test_coverage_is_per_use_and_there_is_no_project_total():
    """A single completeness percentage would be read as "the takeoff is n%
    done" and quoted from. There are no net quantities at all."""
    s = takeoff_coverage(BUNDLE["coverage"])
    assert "use" in s.columns
    for forbidden in ("project_total", "total_m2", "completeness_pct",
                      "overall"):
        assert forbidden not in s.columns
    assert any("NO project total" in n for n in s.notes)


def test_every_sheet_states_gross_where_it_reports_gross():
    s = wall_quantities(BUNDLE["wall_records"], BUNDLE["releases"])
    assert any("GROSS" in n for n in s.notes)
    assert not any(c.startswith("net_") for c in s.columns)


# --- exceptions ---------------------------------------------------------------

def test_the_exceptions_sheet_carries_the_known_gaps_and_what_would_fix_them():
    s = exceptions(known_gaps=[{"subject": "WSH-01", "item": "region is the "
                                "shaft, not the wash floor", "cause": "dashed "
                                "threshold", "effect": "~7.8 m understated",
                                "status": "REVIEW REQUIRED",
                                "resolution": "E25 ownership"}])
    assert s.rows[0]["severity"] == qw.UNDERSTATED
    assert s.rows[0]["what_would_resolve_it"] == "E25 ownership"


def test_an_unresolved_space_is_listed_not_dropped():
    """A register that quietly omits the rooms the engine failed on reads as
    complete."""
    assert "WSH-01" in room_register(SPACES).values("space_id")


# --- structure ----------------------------------------------------------------

def test_the_workbook_has_the_seven_sheets_in_order():
    wb = build_workbook(BUNDLE)
    assert [s.name for s in wb.sheets] == list(SHEET_ORDER)
    assert len(SHEET_ORDER) == 7


def test_the_workbook_will_not_describe_a_project_it_cannot_name():
    with pytest.raises(QaWorkbookError, match="project_id"):
        build_workbook({"spaces": SPACES})


def test_a_row_cannot_smuggle_in_a_column_the_sheet_does_not_declare():
    with pytest.raises(QaWorkbookError, match="does not"):
        Sheet(name="x", columns=("a",), rows=({"a": 1, "b": 2},))


def test_the_read_only_warning_is_in_the_file_a_human_opens():
    wb = build_workbook(BUNDLE)
    joined = " ".join(wb.warnings)
    assert "READ-ONLY" in joined
    assert "NOT A QUOTATION" in joined
    assert "Corrections belong in" in joined


def test_it_writes_a_real_xlsx_with_every_sheet(tmp_path):
    from openpyxl import load_workbook

    from engine.qa_writer import write
    out = tmp_path / "qa.xlsx"
    write(build_workbook(BUNDLE), str(out))
    got = load_workbook(out)
    assert got.sheetnames[0] == "How to read this"
    for name in SHEET_ORDER:
        assert name[:31] in got.sheetnames


def test_the_release_columns_use_the_engines_own_use_names():
    """The first export came out with no release statuses at all: the exporter
    asked for "FLOORING" and "CERAMIC_WALL", which are not release-matrix uses,
    and the lookup dropped them silently. Friendlier names are not free."""
    from engine.release_matrix import USES
    from engine.qa_workbook import FLOORING_COLUMNS, WALL_COLUMNS
    for col in FLOORING_COLUMNS + WALL_COLUMNS:
        if not col.endswith("_release"):
            continue
        stem = col[:-len("_release")].upper()
        assert any(u.startswith(stem) or stem in u for u in USES), col


def test_an_unknown_use_is_refused_rather_than_dropped():
    from tools.export_qa_workbook import _release_row
    with pytest.raises(KeyError, match="not a release-matrix use"):
        _release_row("BED-01", {}, ("FLOORING",))
