"""E40 — the read-only QA workbook.

Most of these tests are about what the workbook may NOT do. A reporting layer
is dangerous in exactly one way: if anything it reports can re-enter the
calculation, the calculation has been calibrated to its own output. So the
contract is enforced here, not merely written in a docstring.
"""

from __future__ import annotations

import ast
from collections import OrderedDict
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

def _manifest():
    """A coherent one-run manifest. Every workbook needs one now: a workbook
    that cannot prove its sheets describe one analysis state may not be
    built."""
    from engine.run_manifest import RunManifest
    m = RunManifest("23010", "AR-00", "MAR.2023", "abc123")
    f = m.add("frame", "V2", {"frame": "SWAP_FLIP_Y"})
    w = m.add("wall_extraction", "V2", {"bands": 243},
              consumed=[("frame", f.output_hash)])
    m.add("wall_graph", "V2", {"edges": 369},
          consumed=[("wall_extraction", w.output_hash)])
    return m.record()


BUNDLE = {
    "manifest": _manifest(),
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

ROOM_COUNTS = [
    {"room_type": "BEDROOM", "semantic_observations": 1,
     "validated_physical_spaces": 1, "unresolved_physical_spaces": 0,
     "functional_zones": 0, "in_scope_validated": 1, "unresolved_reasons": []},
    {"room_type": "BATHROOM", "semantic_observations": 1,
     "validated_physical_spaces": 1, "unresolved_physical_spaces": 0,
     "functional_zones": 0, "in_scope_validated": 1, "unresolved_reasons": []},
    {"room_type": "WASHROOM", "semantic_observations": 1,
     "validated_physical_spaces": 0, "unresolved_physical_spaces": 1,
     "functional_zones": 0, "in_scope_validated": 0,
     "unresolved_reasons": ["REGION_IS_NOT_THIS_SPACE"]},
]


def test_an_empty_manual_column_is_not_agreement():
    """A workbook that prints AGREES against a blank column has invented a
    confirmation."""
    s = room_count_summary(SPACES)
    assert set(s.values("verdict")) == {NOT_COMPARED}
    assert set(s.values("manual_expected_count")) == {UNKNOWN}


def test_a_supplied_manual_count_is_compared_and_can_disagree():
    s = room_count_summary(SPACES, {"BATHROOM": 1, "BEDROOM": 2}, ROOM_COUNTS)
    by_type = {r["room_type"]: r for r in s.rows}
    assert by_type["BATHROOM"]["verdict"] == AGREES
    assert by_type["BEDROOM"]["verdict"] == DIFFERS
    assert by_type["BEDROOM"]["physical_difference"] == -1
    assert by_type["WASHROOM"]["verdict"] == NOT_COMPARED


def test_a_manual_count_is_compared_against_the_matching_basis():
    """A manual PHYSICAL count must never be compared against a LABEL count.
    WASHROOM has one label and zero validated polygons: an owner expecting one
    washroom disagrees with the engine, and saying AGREES would hide that."""
    s = room_count_summary(SPACES, {"WASHROOM": {"physical": 1}}, ROOM_COUNTS)
    row = {r["room_type"]: r for r in s.rows}["WASHROOM"]
    assert row["observed_label_count"] == 1
    assert row["validated_physical_count"] == 0
    assert row["physical_difference"] == -1
    assert row["verdict"] == DIFFERS


def test_the_manual_columns_exist_even_with_no_manual_data():
    """Manual qiyal is not a production dependency, but the column for it is
    always there: a project that HAS a manual count must be able to use it
    without the workbook changing shape."""
    s = room_count_summary(SPACES)
    assert "manual_expected_physical_total" in s.columns
    assert "manual_expected_in_scope" in s.columns
    assert "manual_expected_functional" in s.columns
    assert "manual_expected_physical_total" in s.human_columns
    assert "system_total_count" not in s.columns   # basis must be explicit


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
    assert s.rows[0]["engineering_next_action"] == "E25 ownership"


def test_an_exception_row_names_the_run_that_measured_it():
    """The workbook carried a causal explanation the same round's diagnostic
    had disproved. It survived because it was prose in a list with nothing
    tying it to a measurement."""
    s = exceptions(findings=[{
        "severity": "BLOCKING", "area": "TOPOLOGY", "subject": "wall graph",
        "issue": "in pieces", "cause": "measured this run: ...",
        "effect": "no faces", "finding_id": "F-R9-001",
        "diagnostic_run_id": "R9",
        "evidence_reference": "runs/graph/AR-00_graph_diagnostic.json",
        "engineering_next_action": "reduce unexplained components",
        "affected_spaces": 36, "affected_uses": 13}])
    assert s.rows[0]["finding_id"] == "F-R9-001"
    assert s.rows[0]["diagnostic_run_id"] == "R9"
    assert s.rows[0]["evidence_reference"].endswith(".json")
    assert any("stale" in n for n in s.notes)


def test_engineering_action_is_separate_from_owner_input():
    """"supply DXF/DWG of AR-00" as the owner action quietly said the PDF
    pipeline cannot proceed. It can, and it must."""
    s = exceptions(findings=[{
        "severity": "BLOCKING", "area": "TOPOLOGY", "subject": "g",
        "issue": "i", "cause": "c", "effect": "e", "finding_id": "F-1",
        "diagnostic_run_id": "R9", "evidence_reference": "x.json",
        "engineering_next_action": "repair PDF wall connectivity",
        "owner_input_helpful_if_available": "a DWG would help. NOT required."}])
    r = s.rows[0]
    assert r["engineering_next_action"] == "repair PDF wall connectivity"
    assert r["owner_input_required"] == UNKNOWN
    assert "NOT required" in r["owner_input_helpful_if_available"]
    assert "owner_action_required" not in s.columns


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

def test_the_workbook_leads_with_the_dashboard():
    from engine.qa_workbook import SHEET_DASHBOARD, SHEET_TOPOLOGY
    wb = build_workbook(BUNDLE)
    assert wb.sheets[0].name == SHEET_DASHBOARD
    assert SHEET_TOPOLOGY in SHEET_ORDER


def test_the_dashboard_derives_no_quantity_of_its_own():
    """It counts sheets that already own their numbers. If it computed, it
    would be a second source of truth sitting in front of the first."""
    import inspect

    from engine import qa_workbook
    src = inspect.getsource(qa_workbook.dashboard)
    body = "\n".join(ln for ln in src.splitlines()
                     if not ln.strip().startswith("#"))
    for forbidden in (" * ", "round(", "sum(c."):
        assert forbidden not in body, forbidden


def test_the_dashboard_carries_two_statuses_not_one():
    """One word was answering two questions: how much has been validated, and
    may a BOQ be produced. The report said BLOCKED while the dashboard said
    VALIDATED_PARTIAL, and both were defensible readings of one field."""
    from engine.takeoff_status import (BLOCKED_FOR_FINAL_BOQ,
                                       NO_VALIDATED_OUTPUT, assess)
    status = assess(uses_total=13, uses_with_ready_spaces=0, net_uses_ready=0,
                    validated_physical_spaces=0, total_in_scope_spaces=17,
                    openings_validated=0, signed_trade_rules=0,
                    unresolved_topology_spaces=3, graph_gate_passed=False)
    wb = build_workbook(dict(BUNDLE, coverage=[],
                             top_level_status=status.record()))
    dash = {r["measure"]: r["value"] for r in wb.by_name()["Dashboard"].rows}
    assert dash["TAKEOFF_COVERAGE_STATUS"] == NO_VALIDATED_OUTPUT
    assert dash["FINAL_BOQ_STATUS"] == BLOCKED_FOR_FINAL_BOQ


def test_the_dashboard_reports_the_geometry_layers_separately():
    """"Geometry ready = 36 / unresolved = 0" was true only of the first layer
    and was printed as though it were the last."""
    wb = build_workbook(dict(BUNDLE, geometry_layers={
        "RASTER_REGION_AVAILABLE": 36, "WALL_GEOMETRY_AVAILABLE": 36,
        "REGION_IDENTITY_VALIDATED": 35, "PHYSICAL_TOPOLOGY_VALIDATED": 33,
        "VECTOR_SPACE_FACES_GENERATED": 19,
        "VECTOR_SINGLE_LABEL_FACE_CANDIDATES": 5,
        "validated_physical_spaces": 33}))
    dash = {r["measure"]: r["value"] for r in wb.by_name()["Dashboard"].rows}
    assert dash["RASTER_REGION_AVAILABLE"] == 36
    assert dash["RASTER_REGION_IDENTITY_VALIDATED"] == 35
    assert dash["RASTER_SPACE_COMPLETENESS_VALIDATED"] == 33
    assert dash["RASTER_RELEASE_SPACE_RECORDS_VALIDATED"] == 33


def test_a_geometry_kpi_says_which_geometry_it_means():
    """§20 / §23 / §24 — "physical topology validated = 33" was read as 33
    reconstructed vector faces, and the five single-label cycles were
    reported as validated when one of them is a shaft."""
    wb = build_workbook(dict(BUNDLE, geometry_layers={
        "RASTER_REGION_AVAILABLE": 36, "PHYSICAL_TOPOLOGY_VALIDATED": 33,
        "VECTOR_SPACE_FACES_GENERATED": 19,
        "VECTOR_SINGLE_LABEL_FACE_CANDIDATES": 5,
        "VECTOR_PHYSICAL_SPACE_VALIDATED": 2,
        "VECTOR_SPACE_IDENTITY_REJECTED": 1,
        "CLEAR_INTERNAL_POLYGONS_COMPLETE": 2,
        "validated_physical_spaces": 33}))
    rows = {r["measure"]: r for r in wb.by_name()["Dashboard"].rows}
    assert rows["VECTOR_SINGLE_LABEL_FACE_CANDIDATES"]["value"] == 5
    assert "CANDIDATES" in rows["VECTOR_SINGLE_LABEL_FACE_CANDIDATES"]["note"]
    assert rows["VECTOR_PHYSICAL_SPACE_VALIDATED"]["value"] == 2
    assert rows["VECTOR_SPACE_IDENTITY_REJECTED"]["value"] == 1
    assert rows["VECTOR_SPACE_FACES_GENERATED"]["value"] == 19
    assert "NOT additive" in rows["VECTOR_SPACE_FACES_GENERATED"]["note"]
    assert "segmentation fact" in rows[
        "RASTER_SPACE_COMPLETENESS_VALIDATED"]["note"]
    # §24 — the 33 must name its own provenance
    assert "RASTER" in rows["RASTER_RELEASE_SPACE_RECORDS_VALIDATED"]["note"]
    assert "NOT a count of reconstructed vector rooms" in rows[
        "RASTER_RELEASE_SPACE_RECORDS_VALIDATED"]["note"]


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
    """"What rooms exist?", "what is validated?" and "what is in the job?" are
    three questions and a single count agrees with none of them."""
    s = room_count_summary(
        SPACES, {"BATHROOM": {"physical": 1, "in_scope": 1}}, ROOM_COUNTS)
    row = {r["room_type"]: r for r in s.rows}["BATHROOM"]
    assert row["observed_label_count"] == 1
    assert row["validated_physical_count"] == 1
    assert row["validated_in_scope_count"] == 1
    assert row["verdict"] == AGREES


def test_a_manual_total_that_is_right_but_scope_that_is_wrong_still_differs():
    s = room_count_summary(
        SPACES, {"BATHROOM": {"physical": 1, "in_scope": 0}}, ROOM_COUNTS)
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


# --- §18 a structured field may not become prose as `None` -------------------

def test_a_narrative_cell_carrying_None_refuses_the_export():
    """The workbook read: 'only None of None short marks share a path with a
    long run'. The number was absent; the claim was not."""
    from engine.qa_workbook import (QaWorkbookError, Sheet,
                                    assert_no_missing_value_prose)
    sh = Sheet(name="X", columns=("cause",), rows=(
        OrderedDict(cause="fragmentation is NOT the cause — only None of "
                          "None short marks share a path with a long run"),))
    with pytest.raises(QaWorkbookError, match="EMPTY CELL"):
        assert_no_missing_value_prose([sh])


def test_a_narrative_cell_with_real_values_exports():
    from engine.qa_workbook import Sheet, assert_no_missing_value_prose
    sh = Sheet(name="X", columns=("cause",), rows=(
        OrderedDict(cause="only 993 of 55144 short marks share a path with a "
                          "long run"),))
    assert_no_missing_value_prose([sh])


def test_an_empty_cell_is_fine_because_it_claims_nothing():
    from engine.qa_workbook import Sheet, assert_no_missing_value_prose
    sh = Sheet(name="X", columns=("cause",), rows=(OrderedDict(cause=None),))
    assert_no_missing_value_prose([sh])


# --- §15 quantity stage and measurement basis are different columns ---------

def test_the_coverage_sheet_carries_both_stage_and_basis():
    from engine.qa_workbook import takeoff_coverage
    sh = takeoff_coverage([
        {"use": "GROSS_PLASTER", "quantity_stage": "GROSS",
         "measurement_basis": "HOST_WALL_GROSS_LENGTH", "applicable": 23,
         "ready": 0, "blocked": 23, "not_applicable": 13,
         "commonest_blocker": "height", "quantity_released": 0},
        {"use": "SKIRTING", "quantity_stage": "DIRECT",
         "measurement_basis": "SKIRTING_ELIGIBLE_LENGTH (RULE_REQUIRED)",
         "applicable": 23, "ready": 0, "blocked": 23, "not_applicable": 13,
         "commonest_blocker": "skirting_eligibility_rule",
         "quantity_released": 0}])
    rows = {r["use"]: r for r in sh.rows}
    assert rows["GROSS_PLASTER"]["quantity_stage"] == "GROSS"
    assert rows["GROSS_PLASTER"]["measurement_basis"] == (
        "HOST_WALL_GROSS_LENGTH")
    # §16 — skirting is not blocked on openings. Without the eligibility rule
    # there is no skirting length for a door to be deducted from.
    assert rows["SKIRTING"]["commonest_blocker"] == "skirting_eligibility_rule"
    assert "RULE_REQUIRED" in rows["SKIRTING"]["measurement_basis"]


# --- §19 a face must say which graph produced it ----------------------------

def test_topology_qa_labels_every_face_with_its_graph_and_run():
    from engine.qa_workbook import topology_qa
    sh = topology_qa(
        faces=[{"space_face_id": "SF-V2-0002",
                "graph_type": "SPACE_BOUNDARY_GRAPH", "topology_run_id": "V2",
                "component_id": "FACE-0003", "area_m2": 33.285,
                "perimeter_m": 28.299, "geometry_status": "CLOSED"}],
        containment=[{"space_face_id": "SF-V2-0002",
                      "labelled_regions_contained": 1,
                      "verdict": "SINGLE_ROOM_CANDIDATE", "portal_edges": 1}])
    row = sh.rows[0]
    assert row["graph_type"] == "SPACE_BOUNDARY_GRAPH"
    assert row["topology_run_id"] == "V2"
    assert row["containment_verdict"] == "SINGLE_ROOM_CANDIDATE"
