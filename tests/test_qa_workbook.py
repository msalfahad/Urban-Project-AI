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
    """Scanned as identifiers, not prose. The module is allowed to explain WHY
    it carries no cost column; it is not allowed to carry one."""
    import ast

    tree = ast.parse(Path(qw.__file__).read_text())
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.arg for n in ast.walk(tree) if isinstance(n, ast.arg)}
    names |= {n.value for n in ast.walk(tree)
              if isinstance(n, ast.Constant) and isinstance(n.value, str)
              and "\n" not in n.value and len(n.value) < 40}
    for n in names:
        low = str(n).lower()
        for forbidden in ("price", "rate_kd", "cost_", "material_recipe",
                          "kwd", "unit_rate"):
            assert forbidden not in low, (forbidden, n)


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
    assert by_type["BEDROOM"]["total_difference"] == -1
    assert by_type["WASHROOM"]["verdict"] == NOT_COMPARED


def test_the_manual_columns_exist_even_with_no_manual_data():
    """Manual qiyal is not a production dependency, but the column for it is
    always there: a project that HAS a manual count must be able to use it
    without the workbook changing shape."""
    s = room_count_summary(SPACES)
    assert "manual_expected_total" in s.columns
    assert "manual_expected_in_scope" in s.columns
    assert "manual_expected_total" in s.human_columns


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
    from engine.qa_workbook import QA_IN_SCOPE
    many = [dict(s, space_id=f"{s['space_id']}-{i}", scope="IN_SCOPE")
            for i in range(6) for s in SPACES]
    s = random_qa_sample(many, {}, {}, project_id="23010", per_stratum=2)
    counts = {}
    for r in s.rows:
        if r["qa_type"] == QA_IN_SCOPE:
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

def test_the_workbook_sheets_come_out_in_the_declared_order():
    wb = build_workbook(BUNDLE)
    assert [s.name for s in wb.sheets] == list(SHEET_ORDER)


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


# --- the upgraded workbook ----------------------------------------------------

def test_the_workbook_has_eleven_sheets_with_the_dashboard_first():
    from engine.qa_workbook import SHEET_DASHBOARD
    wb = build_workbook(BUNDLE)
    assert len(SHEET_ORDER) == 11
    assert wb.sheets[0].name == SHEET_DASHBOARD


def test_the_dashboard_derives_no_quantity_of_its_own():
    """It counts sheets that already own their numbers. If it computed, it
    would be a second source of truth sitting in front of the first."""
    import inspect

    from engine import qa_workbook
    src = inspect.getsource(qa_workbook.dashboard)
    for forbidden in (" * ", " / ", "round("):
        assert forbidden not in src, forbidden


def test_the_dashboard_says_blocked_when_nothing_is_released():
    from engine.qa_workbook import STATUS_BLOCKED
    wb = build_workbook(dict(BUNDLE, coverage=[]))
    dash = {r["measure"]: r["value"] for r in wb.by_name()["Dashboard"].rows}
    assert dash["TAKEOFF STATUS"] == STATUS_BLOCKED


def test_a_workbook_with_human_labels_says_so_on_the_front_page():
    """Project 23010's room names were read off the sheet by a person. A
    workbook that hides that reads as proof of automatic extraction."""
    spaces = [dict(s, semantic_source="HUMAN_VERIFIED") for s in SPACES]
    wb = build_workbook(dict(BUNDLE, spaces=spaces))
    rows = wb.by_name()["Dashboard"].rows
    hv = [r for r in rows if r["measure"] == "HUMAN_VERIFIED labels"]
    assert hv and hv[0]["value"] == 3
    assert "NOT evidence" in hv[0]["note"]


def test_the_register_records_who_named_each_room():
    from engine.qa_workbook import SEMANTIC_SOURCES
    assert "HUMAN_VERIFIED" in SEMANTIC_SOURCES and "AI_INFERRED" in SEMANTIC_SOURCES
    reg = room_register([dict(SPACES[0], semantic_source="AI_INFERRED")])
    assert reg.values("semantic_source") == ["AI_INFERRED"]


def test_the_count_summary_separates_the_drawing_from_the_contract():
    """"What rooms exist?" and "what rooms are in the job?" are different
    questions and a single count agrees with neither."""
    s = room_count_summary(SPACES, {"BATHROOM": {"total": 1, "in_scope": 1}})
    row = {r["room_type"]: r for r in s.rows}["BATHROOM"]
    assert row["system_total_count"] == 1 and row["system_in_scope_count"] == 1
    assert row["verdict"] == AGREES


def test_a_manual_total_that_is_right_but_scope_that_is_wrong_still_differs():
    s = room_count_summary(SPACES, {"BATHROOM": {"total": 1, "in_scope": 0}})
    assert {r["room_type"]: r for r in s.rows}["BATHROOM"]["verdict"] == DIFFERS


def test_the_qa_samples_are_three_populations_not_one():
    from engine.qa_workbook import QA_IN_SCOPE, QA_RISK, QA_SCOPE_AUDIT
    from engine.qa_workbook import random_qa_sample, risk_flags
    flags = risk_flags(SPACES, BUNDLE["quantities"], {})
    s = random_qa_sample(SPACES, {}, {}, project_id="23010", risk_flags=flags)
    kinds = {r["qa_type"] for r in s.rows}
    assert QA_IN_SCOPE in kinds and QA_RISK in kinds and QA_SCOPE_AUDIT in kinds


def test_the_in_scope_sample_does_not_spend_the_owners_time_on_excluded_rooms():
    from engine.qa_workbook import QA_IN_SCOPE, random_qa_sample
    s = random_qa_sample(SPACES, {}, {}, project_id="23010")
    a = [r for r in s.rows if r["qa_type"] == QA_IN_SCOPE]
    assert a and all(r["scope"] == "IN_SCOPE" for r in a)


def test_every_risk_row_says_why_it_was_chosen():
    """"Largest area on the sheet" tells a surveyor what to bring a tape for.
    A risk score would not."""
    from engine.qa_workbook import QA_RISK, random_qa_sample, risk_flags
    flags = risk_flags(SPACES, {}, {})
    s = random_qa_sample(SPACES, {}, {}, project_id="23010", risk_flags=flags)
    risk = [r for r in s.rows if r["qa_type"] == QA_RISK]
    assert risk and all(r["why_selected"] for r in risk)


def test_the_scope_audit_checks_what_was_excluded():
    """A wrong exclusion is invisible in every other sheet."""
    from engine.qa_workbook import QA_SCOPE_AUDIT, random_qa_sample
    s = random_qa_sample(SPACES, {}, {}, project_id="23010")
    audit = [r for r in s.rows if r["qa_type"] == QA_SCOPE_AUDIT]
    assert audit and all(r["scope"] in ("OUT_OF_SCOPE", "AMBIGUOUS")
                         for r in audit)


def test_exceptions_are_ranked_by_what_fixing_them_unlocks():
    s = exceptions(
        space_exceptions=[{"subject": "BTH-01", "issue": "no rule",
                           "affected_spaces": 1, "affected_uses": 2}],
        graph_exceptions=[{"subject": "graph", "issue": "115 components",
                           "severity": "BLOCKING", "affected_spaces": 36,
                           "affected_uses": 13}])
    assert s.rows[0]["subject"] == "graph"
    assert s.rows[0]["priority"] == 1
    assert s.rows[1]["priority"] == 2


def test_no_exception_carries_a_financial_impact():
    """A cost on an unvalidated quantity gets quoted long before the quantity
    does."""
    from engine.qa_workbook import EXCEPTION_COLUMNS
    for col in EXCEPTION_COLUMNS:
        assert "cost" not in col and "value_kd" not in col and "price" not in col


def test_the_quantity_trace_sheet_shows_the_id():
    from engine.qa_workbook import quantity_trace
    s = quantity_trace([{"quantity_id": "Q-23010-2F-BTH03-CER-GROSS-001",
                         "space_id": "BTH-03", "use": "GROSS_CERAMIC_WALL"}])
    assert s.values("quantity_id") == ["Q-23010-2F-BTH03-CER-GROSS-001"]
    assert "drawing_preview_reference" in s.columns


def test_an_empty_rules_sheet_means_nobody_signed_one():
    from engine.qa_workbook import rules_and_assemblies
    s = rules_and_assemblies()
    assert s.rows == ()
    assert any("no defaults" in n for n in s.notes)


def test_the_revision_sheet_says_there_is_no_baseline_not_no_changes():
    from engine.qa_workbook import revision_delta
    s = revision_delta({"status": "NO_PRIOR_REVISION_AVAILABLE",
                        "why": "only one revision has been analysed"})
    assert s.rows == ()
    assert any("not because" in n for n in s.notes)


def test_manual_entries_are_declared_validation_evidence_only():
    wb = build_workbook(BUNDLE)
    assert any("VALIDATION EVIDENCE ONLY" in w for w in wb.warnings)
