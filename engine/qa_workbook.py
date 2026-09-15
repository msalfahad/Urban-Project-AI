"""E40 — the read-only QA workbook. A window, never a valve.

This module turns quantities that have ALREADY been established into sheets a
quantity surveyor can check by hand. It is the reporting layer, and the whole
point of a reporting layer is that the arrow only points one way:

    geometry -> semantics -> release -> THIS -> a human reading a spreadsheet

Nothing here may point back. It does not import the geometry, wall, opening or
benchmark engines, and there is a test that fails if it ever does, because the
moment a reported figure can re-enter the calculation the calculation has been
calibrated to its own output. Whoever reads a cell here is reading what the
engine decided, not what the workbook thinks.

FOUR RULES THIS MODULE IS WRITTEN UNDER, all of them from the review:

  1  DO NOT RECALCULATE. Every quantity cell is copied from the bundle it was
     given. No areas are multiplied, no perimeters summed, no heights applied.
     If a figure is not in the bundle it is NOT_ESTABLISHED, not derived here.

  2  ZERO IS A RESULT, NOT A BLANK. Zero means a proved quantity of zero. An
     unknown is NOT_ESTABLISHED. Substituting one for the other turns "we have
     not measured this" into "there is none of it", which is the single most
     expensive mistake a takeoff can make.

  3  NO PROJECT TOTAL THAT LOOKS COMPLETE. Coverage is reported per use, with
     the blocked count beside the ready count. A single "project total" cell
     would be read as a quotation, and this system has released no net
     quantities at all.

  4  NO MATERIALS, NO RECIPES, NO PRICING. Not yet. A sheet that carries a rate
     invites a total, and a total invites a client.
"""

from __future__ import annotations

import hashlib
import random
from collections import Counter, OrderedDict
from dataclasses import dataclass, field

# The one sentinel. It is a string on purpose: a reader must not be able to
# mistake it for a number, sum a column containing it, or coerce it to 0.0.
UNKNOWN = "NOT_ESTABLISHED"

# What a QA row's verdict can be. NOT_COMPARED is not a failure — it is the
# honest state of a row with nothing to compare against.
AGREES = "AGREES"
DIFFERS = "DIFFERS"
NOT_COMPARED = "NOT_COMPARED"

# Sheet names, in the order the review listed them.
SHEET_DASHBOARD = "Dashboard"
SHEET_ROOM_REGISTER = "Room Register"
SHEET_ROOM_COUNTS = "Room Count Summary"
SHEET_FLOORING = "Flooring and Ceramic QA"
SHEET_WALLS = "Wall Quantities"
SHEET_EXCEPTIONS = "Exceptions"
SHEET_SAMPLE = "QA Samples"
SHEET_COVERAGE = "Takeoff Coverage"
SHEET_TRACE = "Quantity Trace"
SHEET_RULES = "Rules and Assemblies"
SHEET_REVISION = "Revision Delta"
SHEET_TOPOLOGY = "Topology QA"
SHEET_WALL_QA = "Wall Extraction QA"
SHEET_PATHS = "Topology Path Comparison"

SHEET_ORDER = (SHEET_DASHBOARD, SHEET_ROOM_REGISTER, SHEET_ROOM_COUNTS,
               SHEET_TRACE, SHEET_FLOORING, SHEET_WALLS, SHEET_EXCEPTIONS,
               SHEET_SAMPLE, SHEET_WALL_QA, SHEET_TOPOLOGY, SHEET_PATHS,
               SHEET_RULES, SHEET_COVERAGE,
               SHEET_REVISION)

# Takeoff status, kept blunt on purpose. A workbook that opens cleanly must not
# read as a finished BOQ.
STATUS_COMPLETE = "COMPLETE"
STATUS_PARTIAL = "VALIDATED_PARTIAL"
STATUS_BLOCKED = "BLOCKED"

# Where a semantic label came from. A workbook carrying HUMAN_VERIFIED labels
# must never be read as proof of automatic semantic extraction.
SEMANTIC_SOURCES = ("AI_INFERRED", "PDF_TEXT", "CAD_TEXT", "HUMAN_VERIFIED",
                    "HUMAN_ASSIGNED", "UNRESOLVED")

# The three QA populations. One stratified sample spends the owner's time
# evenly; these spend it where it is worth something.
QA_IN_SCOPE = "A_IN_SCOPE_STRATIFIED"
QA_RISK = "B_RISK_BASED"
QA_SCOPE_AUDIT = "C_SCOPE_AUDIT"

# A human column is left EMPTY for someone to write in. It is not a missing
# value and it is not zero; it is a blank line on a checking sheet.
FOR_THE_CHECKER = ""


class QaWorkbookError(RuntimeError):
    """The workbook could not be built without misrepresenting something."""


def cell(value, *, allow_zero: bool = True):
    """One quantity cell, with unknown and zero kept apart.

    `None` means nobody established this: NOT_ESTABLISHED. A numeric zero is
    passed through untouched, because a proved zero is a real answer — zero
    ceramic wall in a bedroom is a finding, not a gap.
    """
    if value is None:
        return UNKNOWN
    if isinstance(value, str):
        return value if value else UNKNOWN
    if not allow_zero and value == 0:
        raise QaWorkbookError(
            "a zero was passed where zero cannot be a proved result; pass None "
            "so the cell reads NOT_ESTABLISHED instead of claiming none exists")
    return value


@dataclass(frozen=True)
class Sheet:
    """One worksheet, as data. The writer adds no values of its own."""

    name: str
    columns: tuple[str, ...]
    rows: tuple[dict, ...]
    notes: tuple[str, ...] = ()
    human_columns: tuple[str, ...] = ()

    def __post_init__(self):
        for r in self.rows:
            extra = set(r) - set(self.columns)
            if extra:
                raise QaWorkbookError(
                    f"{self.name}: row carries columns the sheet does not "
                    f"declare: {sorted(extra)}")

    def values(self, column: str) -> list:
        return [r.get(column, UNKNOWN) for r in self.rows]


# ------------------------------------------------------------ 1 room register

ROOM_REGISTER_COLUMNS = (
    "space_id", "name_en", "name_ar", "room_type", "scope", "apartment_id",
    "region_id", "geometry_type", "floor_area_m2", "area_source",
    "measurement_basis", "geometry_status", "semantic_source",
    "label_confidence", "flag")


def room_register(spaces) -> Sheet:
    """Every space the engine knows about, including the ones it cannot use.

    An UNRESOLVED space is listed rather than dropped. A register that quietly
    omits the two rooms the engine failed on is a register that reads as
    complete, and the exceptions sheet exists because it is not.
    """
    rows = tuple(OrderedDict(
        space_id=s["space_id"],
        name_en=cell(s.get("name_en")),
        name_ar=cell(s.get("name_ar")),
        room_type=cell(s.get("room_type")),
        scope=cell(s.get("scope")),
        apartment_id=cell(s.get("apartment_id")),
        region_id=cell(s.get("region")),
        geometry_type=cell(s.get("geometry_type")),
        floor_area_m2=cell(s.get("floor_area_m2")),
        area_source=cell(s.get("area_source")),
        measurement_basis=cell(s.get("measurement_basis")),
        geometry_status=cell(s.get("geometry_status")),
        semantic_source=cell(s.get("semantic_source")),
        label_confidence=cell(s.get("semantic_label_confidence")),
        flag=cell(s.get("flag")),
    ) for s in spaces)
    return Sheet(
        name=SHEET_ROOM_REGISTER, columns=ROOM_REGISTER_COLUMNS, rows=rows,
        notes=(
            "Every space the engine identified, including spaces it could not "
            "measure. NOT_ESTABLISHED means no value was established — it is "
            "not zero.",
            "semantic_source says who named the room. HUMAN_VERIFIED means a "
            "person read it off the sheet — it is NOT evidence that the engine "
            "extracted the label automatically.",
            "Areas are machine-measured and independent of the names.",
        ))


# ------------------------------------------------- 2 room count summary

# §19 — every count column names its BASIS. A generic "system total" that
# duplicated the label count sat beside "validated = 0" for WASHROOM, which is
# easy to read as "1 washroom, one of which failed validation" rather than
# "a label was seen and no washroom was measured".
ROOM_COUNT_COLUMNS = (
    "room_type", "observed_label_count", "validated_physical_count",
    "validated_in_scope_count", "unresolved_physical_count",
    "functional_zone_count", "out_of_scope_count", "ambiguous_scope_count",
    "manual_expected_physical_total", "manual_expected_in_scope",
    "manual_expected_functional",
    "physical_difference", "in_scope_difference", "functional_difference",
    "verdict", "unresolved_reasons", "checker_note")


def room_count_summary(spaces, manual_expected: dict | None = None,
                       room_counts=None) -> Sheet:
    """Counts the owner can trust, because they say what kind of count they are.

    THE WORKBOOK SAID `WASHROOM = 1`. A human had verified that label, so the
    count looked solid. But the region it is attached to is the hatched shaft
    beside the washroom: geometrically the engine has recovered ZERO validated
    washroom polygons. "1 washroom detected" was being told to an owner who
    would reasonably read it as "we measured a washroom".

    So three counts, not one, because they are three different facts:

        semantic observations       the name was read on the drawing
        validated physical spaces   a polygon is the whole of that room, and
                                    only that room
        unresolved physical spaces  a polygon exists and is not that room

    Plus functional zones, so an open-plan villa can be counted honestly: one
    physical space may hold a dining zone, a saloon zone and a circulation
    zone, and the owner wants all three counted without any of them inventing
    a wall.

    And two manual columns, because "what rooms EXIST on the drawing" and
    "what rooms are in the CONTRACT" are different questions that one count
    agrees with neither of.

    Counting rows is not recalculating a quantity. No area or length is derived.
    """
    expected = manual_expected or {}
    counts = {c["room_type"]: c for c in (room_counts or ())}

    by_type: dict[str, list] = {}
    for sp in spaces:
        by_type.setdefault(sp.get("room_type") or UNKNOWN, []).append(sp)
    for rt in counts:
        by_type.setdefault(rt, [])

    rows = []
    for rt in sorted(by_type):
        group = by_type[rt]
        scopes = Counter(sp.get("scope") for sp in group)
        c = counts.get(rt, {})
        exp = expected.get(rt)
        if isinstance(exp, dict):
            e_phys = exp.get("physical", exp.get("total"))
            e_scope = exp.get("in_scope")
            e_func = exp.get("functional")
        elif exp is None:
            e_phys = e_scope = e_func = None
        else:
            e_phys, e_scope, e_func = exp, None, None

        # Each difference is computed against the count with the SAME basis.
        # Comparing a manual physical count against a label count is the
        # mismatch this sheet exists to prevent.
        validated = c.get("validated_physical_spaces")
        in_scope_validated = c.get("in_scope_validated")
        zones = c.get("functional_zones")

        def diff(expected_value, actual):
            if expected_value is None or actual is None:
                return UNKNOWN
            return actual - expected_value

        d_phys = diff(e_phys, validated)
        d_scope = diff(e_scope, in_scope_validated)
        d_func = diff(e_func, zones)
        compared = [d for d in (d_phys, d_scope, d_func) if d != UNKNOWN]
        if not compared:
            verdict = NOT_COMPARED
        elif all(d == 0 for d in compared):
            verdict = AGREES
        else:
            verdict = DIFFERS

        rows.append(OrderedDict(
            room_type=rt,
            observed_label_count=cell(c.get("semantic_observations")),
            validated_physical_count=cell(validated),
            validated_in_scope_count=cell(in_scope_validated),
            unresolved_physical_count=cell(
                c.get("unresolved_physical_spaces")),
            functional_zone_count=cell(zones),
            out_of_scope_count=scopes.get("OUT_OF_SCOPE", 0),
            ambiguous_scope_count=scopes.get("AMBIGUOUS", 0),
            manual_expected_physical_total=cell(e_phys),
            manual_expected_in_scope=cell(e_scope),
            manual_expected_functional=cell(e_func),
            physical_difference=d_phys, in_scope_difference=d_scope,
            functional_difference=d_func, verdict=verdict,
            unresolved_reasons=cell(", ".join(c.get("unresolved_reasons", []))),
            checker_note=FOR_THE_CHECKER))
    return Sheet(
        name=SHEET_ROOM_COUNTS, columns=ROOM_COUNT_COLUMNS, rows=tuple(rows),
        human_columns=("manual_expected_physical_total",
                       "manual_expected_in_scope",
                       "manual_expected_functional", "checker_note"),
        notes=(
            "EVERY COUNT NAMES ITS BASIS. observed_label_count is names read "
            "off the drawing. validated_physical_count is polygons proved to "
            "be that room. functional_zone_count is uses of space. They are "
            "three different questions and they routinely disagree — the "
            "disagreement is the finding.",
            "Each manual column is compared against the count with the SAME "
            "basis. A manual physical count is never compared to a label "
            "count.",
            "A LABEL IS NOT A ROOM. WASHROOM reading 1 observed / 0 validated "
            "means a name was seen and no washroom was measured.",
            "A count is not a quantity. Nothing on this sheet is measured.",
        ))


# ------------------------------------------- 3 flooring and ceramic QA

FLOORING_COLUMNS = (
    "space_id", "room_type", "scope", "floor_area_m2", "floor_area_basis",
    "ceramic_wall_length_m", "ceramic_wall_height_m", "height_source",
    "height_truth_domain", "ceramic_wall_area_m2",
    "waterproofing_release", "gross_ceramic_release", "net_ceramic_release",
    "primary_blocker", "checker_measurement", "checker_agrees", "checker_note")


def flooring_ceramic_qa(spaces, quantities: dict, releases: dict) -> Sheet:
    """Floor and ceramic-wall figures beside the release status that governs them.

    A quantity is shown with the status that decides whether it may be used. A
    figure printed without its status gets quoted; the pairing is the control.
    Nothing here multiplies a length by a height — if the area was not
    established upstream, the cell says so.
    """
    rows = []
    for s in spaces:
        sid = s["space_id"]
        q = quantities.get(sid, {})
        r = releases.get(sid, {})
        rows.append(OrderedDict(
            space_id=sid, room_type=cell(s.get("room_type")),
            scope=cell(s.get("scope")),
            floor_area_m2=cell(q.get("floor_area_m2")),
            floor_area_basis=cell(q.get("floor_area_basis")),
            ceramic_wall_length_m=cell(q.get("ceramic_wall_length_m")),
            ceramic_wall_height_m=cell(q.get("ceramic_wall_height_m")),
            height_source=cell(q.get("height_source")),
            height_truth_domain=cell(q.get("height_truth_domain")),
            ceramic_wall_area_m2=cell(q.get("ceramic_wall_area_m2")),
            waterproofing_release=cell(r.get("WATERPROOFING_HORIZONTAL")),
            gross_ceramic_release=cell(r.get("GROSS_CERAMIC_WALL")),
            net_ceramic_release=cell(r.get("NET_CERAMIC_WALL")),
            primary_blocker=cell(r.get("primary_blocker")),
            checker_measurement=FOR_THE_CHECKER,
            checker_agrees=FOR_THE_CHECKER, checker_note=FOR_THE_CHECKER))
    return Sheet(
        name=SHEET_FLOORING, columns=FLOORING_COLUMNS, rows=tuple(rows),
        human_columns=("checker_measurement", "checker_agrees", "checker_note"),
        notes=(
            "ceramic_wall_area_m2 is shown only where it was established "
            "upstream. This sheet does not multiply length by height.",
            "A figure beside a blocked release is a diagnostic, not a quantity "
            "to use.",
        ))


# --------------------------------------------------- 4 wall quantities

WALL_COLUMNS = (
    "space_id", "room_type", "scope", "gross_room_perimeter_m",
    "gross_wall_perimeter_m", "physical_wall_m", "open_length_m",
    "opening_count", "segment_count", "internal_segments",
    "external_segments", "unclassified_segments", "gross_perimeter_release",
    "gross_wall_area_release", "blockwork_release", "external_finish_release",
    "primary_blocker", "checker_measurement", "checker_note")


def wall_quantities(records, releases: dict) -> Sheet:
    """Per-space wall figures, gross and net kept visibly apart.

    open_length_m and opening_count are the honest zeros on this sheet: the
    opening engine has validated none, so a zero here means "none proved", and
    the net columns that would depend on them are absent rather than equal to
    the gross ones.
    """
    rows = []
    for rec in records:
        sid = rec["space_id"]
        r = releases.get(sid, {})
        rows.append(OrderedDict(
            space_id=sid, room_type=cell(rec.get("room_type")),
            scope=cell(rec.get("scope")),
            gross_room_perimeter_m=cell(rec.get("gross_room_perimeter_m")),
            gross_wall_perimeter_m=cell(rec.get("gross_wall_perimeter_m")),
            physical_wall_m=cell(rec.get("physical_wall_m")),
            open_length_m=cell(rec.get("open_length_m")),
            opening_count=cell(rec.get("opening_count")),
            segment_count=cell(rec.get("segment_count")),
            internal_segments=cell(rec.get("internal_segments")),
            external_segments=cell(rec.get("external_segments")),
            unclassified_segments=cell(rec.get("unclassified_segments")),
            gross_perimeter_release=cell(r.get("GROSS_PERIMETER")),
            gross_wall_area_release=cell(r.get("GROSS_WALL_AREA")),
            blockwork_release=cell(r.get("BLOCKWORK")),
            external_finish_release=cell(r.get("EXTERNAL_FINISH")),
            primary_blocker=cell(r.get("primary_blocker")),
            checker_measurement=FOR_THE_CHECKER, checker_note=FOR_THE_CHECKER))
    return Sheet(
        name=SHEET_WALLS, columns=WALL_COLUMNS, rows=tuple(rows),
        human_columns=("checker_measurement", "checker_note"),
        notes=(
            "All wall figures on this sheet are GROSS. No opening has been "
            "validated, so no net wall quantity exists to report.",
            "An opening_count of 0 means none was proved on this drawing — not "
            "that the room has no doors.",
        ))


# -------------------------------------------------------- 5 exceptions

EXCEPTION_COLUMNS = ("priority", "severity", "scope_of_issue", "subject",
                     "issue", "cause", "effect", "affected_spaces",
                     "affected_uses", "affected_boq_sections",
                     "potential_coverage_unlocked",
                     "engineering_next_action", "owner_input_required",
                     "owner_input_helpful_if_available",
                     "status", "provenance_class", "superseded_because",
                     "finding_id", "diagnostic_run_id", "evidence_reference")

# Severity is about consequence, not about how loud the message is.
BLOCKING = "BLOCKING"
UNDERSTATED = "UNDERSTATES_A_QUANTITY"
ADVISORY = "ADVISORY"


def exceptions(*, space_exceptions=(), known_gaps=(), findings=(),
               graph_exceptions=(), scope_exceptions=()) -> Sheet:
    """Everything that is not right, ranked by what fixing it would unlock.

    A list of forty blockers in arbitrary order is not actionable. Ranked by
    coverage unlocked, it becomes "approve one trade rule and eight spaces
    open" — which is a decision the owner can actually take.

    The ranking is by COUNT of spaces and uses, never by money. No financial
    impact is estimated anywhere: a cost attached to an unvalidated quantity
    would be quoted long before the quantity was.
    """
    rows = []

    def add(severity, area, e):
        rows.append(OrderedDict(
            priority=0,                       # filled in below, once sorted
            severity=severity, scope_of_issue=area,
            subject=cell(e.get("subject")),
            issue=cell(e.get("issue") or e.get("item")),
            cause=cell(e.get("cause")), effect=cell(e.get("effect")),
            affected_spaces=cell(e.get("affected_spaces")),
            affected_uses=cell(e.get("affected_uses")),
            affected_boq_sections=cell(e.get("affected_boq_sections")),
            potential_coverage_unlocked=cell(e.get("coverage_unlocked")),
            # THREE separate actions. Making a stronger source look mandatory
            # when we still have work to do is how the PDF pipeline quietly
            # became optional in a reader's mind.
            engineering_next_action=cell(
                e.get("engineering_next_action") or e.get("resolution")),
            owner_input_required=cell(
                e.get("owner_input_required") or e.get("owner_action")),
            owner_input_helpful_if_available=cell(
                e.get("owner_input_helpful_if_available")),
            status=cell(e.get("status")),
            # §17 — a superseded hypothesis may be kept for history. It may
            # never sit unlabelled where a reader takes it for the reason
            # something is broken.
            provenance_class=cell(e.get("provenance_class")
                                  or "CURRENT_DIAGNOSTIC"),
            superseded_because=cell(e.get("superseded_because")),
            finding_id=cell(e.get("finding_id")),
            diagnostic_run_id=cell(e.get("diagnostic_run_id")),
            evidence_reference=cell(e.get("evidence_reference"))))

    # Findings first: they are generated from the current diagnostic run and
    # carry the run id that proves it.
    for f in findings:
        add(f.get("severity") or ADVISORY, f.get("area") or "TOPOLOGY", f)
    for g in known_gaps:
        add(UNDERSTATED, "GEOMETRY", g)
    for e in scope_exceptions:
        add(BLOCKING, "SCOPE", e)
    for e in graph_exceptions:
        add(e.get("severity") or ADVISORY, "TOPOLOGY", e)
    for e in space_exceptions:
        add(BLOCKING, "RELEASE", e)

    # Rank: most spaces unlocked first, then most uses, then severity. A row
    # with no count sinks — not because it does not matter, but because a row
    # whose impact nobody has established cannot be argued to be urgent.
    order = {BLOCKING: 0, UNDERSTATED: 1, ADVISORY: 2}

    # A legacy or superseded row sinks below every current one, whatever its
    # impact count. It is history, and history does not compete for attention
    # with a live defect.
    current_first = {"CURRENT_DIAGNOSTIC": 0, "GOLDEN_KNOWN_DEFECT": 0,
                     "HUMAN_NOTE": 1, "LEGACY_HYPOTHESIS": 2,
                     "SUPERSEDED": 2}

    def key(r):
        spaces = r["affected_spaces"]
        uses = r["affected_uses"]
        return (current_first.get(r["provenance_class"], 0),
                -(spaces if isinstance(spaces, int) else 0),
                -(uses if isinstance(uses, int) else 0),
                order.get(r["severity"], 9))

    rows.sort(key=key)
    for i, r in enumerate(rows, 1):
        r["priority"] = i
    return Sheet(
        name=SHEET_EXCEPTIONS, columns=EXCEPTION_COLUMNS, rows=tuple(rows),
        notes=(
            "Read this sheet before any other. The quantities elsewhere are "
            "only as good as this list is short.",
            "Ranked by spaces and uses unlocked, never by money. No financial "
            "impact is estimated: a cost on an unvalidated quantity gets "
            "quoted long before the quantity does.",
            "provenance_class says whether a row is a CURRENT cause. A "
            "LEGACY_HYPOTHESIS is kept for history and sorted below every "
            "current row — the washroom's dashed-threshold explanation is one: "
            "this project measured zero dashed strokes on the sheet and found "
            "the nearby marks to be shaft hatch.",
            "finding_id and diagnostic_run_id tie a row to the run that "
            "measured it. A row whose run id is not this run's is stale, and "
            "a superseded explanation must never survive into a new workbook.",
            "THREE action columns. engineering_next_action is what WE do next "
            "and is always present. owner_input_required is what only the "
            "owner can decide. owner_input_helpful_if_available is never a "
            "blocker — the PDF pipeline continues without it.",
        ))


# ------------------------------------------------- 6 random QA sample

# §20 — one "engine_status" column was answering three questions and so
# printed NOT_ESTABLISHED beside a perfectly good 4.174 m2. The three are:
#
#   measurement_role           what KIND of number this is
#   geometry_validation_status how far the polygon behind it is validated
#   quantity_release_status    whether it is a released BOQ quantity at all
#
# Floor area is not one of the thirteen release uses, so its release status is
# NOT_A_RELEASED_BOQ_USE — which is a fact about the use, not a defect in the
# measurement.
NOT_A_RELEASED_BOQ_USE = "NOT_A_RELEASED_BOQ_USE"

SAMPLE_COLUMNS = ("qa_type", "stratum", "why_selected", "space_id",
                  "room_type", "scope", "what_to_check", "engine_value",
                  "engine_unit", "engine_source", "measurement_role",
                  "geometry_validation_status", "quantity_release_status",
                  "checker_measurement", "difference", "difference_pct",
                  "checker_verdict", "checker_note")

# The seed is part of the record. A sample nobody can reproduce is an anecdote.
DEFAULT_SAMPLE_SEED = 23010


def _seed_for(project_id: str, seed: int) -> int:
    """A stable seed per project, so two projects do not draw the same rooms."""
    h = hashlib.sha256(f"{project_id}:{seed}".encode()).hexdigest()
    return int(h[:16], 16)


def _sample_row(qa_type, stratum, why, s, quantities, releases, check, unit):
    """One QA line, with the three status questions kept apart.

    The `difference` columns are left EMPTY for the checker's spreadsheet to
    fill once a measurement is entered. They are QA-only arithmetic on QA-only
    inputs: a manual measurement typed here never reaches a production
    quantity, in either direction.
    """
    sid = s["space_id"]
    validated = s.get("physical_space_validated")
    if validated is True:
        role = "VALIDATED_GEOMETRY_MEASUREMENT"
        geo = "PHYSICAL_SPACE_VALIDATED"
    elif validated is False:
        role = "OBSERVATION"
        geo = s.get("unresolved_reason") or "UNRESOLVED"
    else:
        role = "CANDIDATE_GEOMETRY_MEASUREMENT"
        geo = UNKNOWN
    return OrderedDict(
        qa_type=qa_type, stratum=stratum, why_selected=why, space_id=sid,
        room_type=cell(s.get("room_type")), scope=cell(s.get("scope")),
        what_to_check=check,
        engine_value=cell(quantities.get(sid, {}).get(check)),
        engine_unit=unit,
        engine_source=cell(s.get("area_source")),
        measurement_role=role, geometry_validation_status=geo,
        quantity_release_status=NOT_A_RELEASED_BOQ_USE,
        checker_measurement=FOR_THE_CHECKER, difference=FOR_THE_CHECKER,
        difference_pct=FOR_THE_CHECKER, checker_verdict=FOR_THE_CHECKER,
        checker_note=FOR_THE_CHECKER)


def random_qa_sample(spaces, quantities: dict, releases: dict, *,
                     project_id: str, per_stratum: int = 2,
                     seed: int = DEFAULT_SAMPLE_SEED,
                     check: str = "floor_area_m2", unit: str = "m2",
                     risk_flags: dict | None = None,
                     scope_audit_n: int = 3) -> Sheet:
    """Three QA populations, because one stratified sample spends the owner's
    time evenly and the owner's time is not worth spending evenly.

        A  IN-SCOPE STRATIFIED   contracted work, spread across room kinds
        B  RISK-BASED            the rows most likely to be wrong
        C  SCOPE AUDIT           a few excluded rooms, to check the exclusion

    Seeded on sha256(project:seed), so the same drawing draws the same rooms
    every run and a disagreement cannot be made to disappear by exporting
    again. Blocked spaces stay eligible: checking only what the engine is
    already confident about measures nothing.
    """
    rng = random.Random(_seed_for(project_id, seed))
    flags = risk_flags or {}
    rows = []

    # A — in-scope stratified. Contracted work only: the owner should not spend
    # most of a QA session measuring rooms that are not in the job.
    in_scope = [s for s in spaces if s.get("scope") == "IN_SCOPE"]
    strata: dict[str, list] = {}
    for s in in_scope:
        strata.setdefault(s.get("room_type") or UNKNOWN, []).append(s)
    for rt in sorted(strata):
        group = sorted(strata[rt], key=lambda s: s["space_id"])
        picked = group if len(group) <= per_stratum else rng.sample(
            group, per_stratum)
        for s in sorted(picked, key=lambda s: s["space_id"]):
            rows.append(_sample_row(
                QA_IN_SCOPE, rt, "stratified draw from contracted work",
                s, quantities, releases, check, unit))

    # B — risk-based. Not random: these are chosen BECAUSE something about them
    # is unusual, and an unusual row is where an error hides.
    seen = {r["space_id"] for r in rows}
    for s in sorted(spaces, key=lambda s: s["space_id"]):
        sid = s["space_id"]
        why = flags.get(sid)
        if not why:
            continue
        rows.append(_sample_row(
            QA_RISK, "RISK", "; ".join(why) if isinstance(why, (list, tuple))
            else str(why), s, quantities, releases, check, unit))
        seen.add(sid)

    # C — scope audit. A small sample of what was EXCLUDED, because a wrong
    # exclusion is invisible in every other sheet.
    excluded = sorted([s for s in spaces
                       if s.get("scope") in ("OUT_OF_SCOPE", "AMBIGUOUS")],
                      key=lambda s: s["space_id"])
    if excluded:
        picked = (excluded if len(excluded) <= scope_audit_n
                  else rng.sample(excluded, scope_audit_n))
        for s in sorted(picked, key=lambda s: s["space_id"]):
            rows.append(_sample_row(
                QA_SCOPE_AUDIT, s.get("scope") or UNKNOWN,
                "verify this room really is outside the contract",
                s, quantities, releases, check, unit))

    return Sheet(
        name=SHEET_SAMPLE, columns=SAMPLE_COLUMNS, rows=tuple(rows),
        human_columns=("checker_measurement", "difference", "difference_pct",
                       "checker_verdict", "checker_note"),
        notes=(
            "THREE STATUS COLUMNS, not one. measurement_role says what kind of "
            "number this is; geometry_validation_status says how far the "
            "polygon behind it is validated; quantity_release_status says "
            "whether it is a released BOQ quantity at all. Floor area is not "
            "one of the thirteen release uses, so NOT_A_RELEASED_BOQ_USE is a "
            "fact about the use, not a defect in the measurement.",
            "difference and difference % are yours to compute once you enter a "
            "measurement. That arithmetic is QA-only: nothing typed on this "
            "sheet reaches a production quantity.",
            f"Seed {seed} on project {project_id}. The same drawing draws the "
            "same rooms every run, so a disagreement cannot be exported away.",
            "A: contracted work, stratified. B: chosen because something is "
            "unusual — that is where errors hide. C: a few EXCLUDED rooms, "
            "because a wrong exclusion is invisible everywhere else.",
            "Blocked spaces are included deliberately.",
        ))


def risk_flags(spaces, quantities: dict, releases: dict, *,
               wall_records=()) -> dict:
    """Why each space is worth checking. Reasons, not a score.

    A single risk number would be a proxy standing in for the reason, and the
    reason is the useful part: "largest area on the sheet" tells a surveyor
    what to bring a tape for.
    """
    out: dict[str, list] = {}

    def flag(sid, why):
        out.setdefault(sid, []).append(why)

    areas = [(s["space_id"], s.get("floor_area_m2")) for s in spaces
             if s.get("floor_area_m2") is not None]
    if areas:
        flag(max(areas, key=lambda a: a[1])[0], "largest floor area on the sheet")
    perims = [(r["space_id"], r.get("gross_room_perimeter_m"))
              for r in wall_records if r.get("gross_room_perimeter_m")]
    if perims:
        flag(max(perims, key=lambda a: a[1])[0], "largest perimeter")

    for s in spaces:
        sid = s["space_id"]
        if s.get("geometry_type") not in ("RECTANGLE", None):
            flag(sid, f"irregular geometry ({s.get('geometry_type')})")
        if s.get("geometry_status") and s["geometry_status"] != "VALIDATED":
            flag(sid, f"geometry {s['geometry_status']}")
        if s.get("flag"):
            flag(sid, f"flagged in the space map: {s['flag']}")
        if s.get("semantic_source") in (None, "", "AI_INFERRED"):
            flag(sid, "weakest semantic provenance")
    for r in wall_records:
        if r.get("unclassified_segments"):
            flag(r["space_id"],
                 f"{r['unclassified_segments']} wall segments unclassified")
    return out


# ---------------------------------------------------- 7 takeoff coverage

# QUANTITY_STAGE and MEASUREMENT_BASIS are different facts and the old single
# "basis" column held only the first. GROSS/NET/DIRECT is where a number sits
# in the deduction chain; SPACE_BOUNDARY_LENGTH / HOST_WALL_GROSS_LENGTH /
# MATERIAL_PRESENT_LENGTH / OPENING_LENGTH / SKIRTING_ELIGIBLE_LENGTH is WHAT
# WAS MEASURED. A reader needs both: GROSS_PLASTER is a gross quantity
# measured on the host-wall line THROUGH the door.
COVERAGE_COLUMNS = ("use", "quantity_stage", "measurement_basis",
                    "spaces_applicable", "spaces_ready",
                    "spaces_blocked", "spaces_not_applicable",
                    "commonest_blocker", "quantity_released")


def takeoff_coverage(tallies) -> Sheet:
    """How much of the building each use actually covers — per use, never summed.

    There is no project completeness cell and there will not be one. A single
    percentage would be read as "the takeoff is 62% done" and quoted from, when
    what it would actually mean is that two thirds of the rooms have a GROSS
    figure for one of thirteen uses and no net quantity exists anywhere.
    """
    rows = []
    for t in tallies:
        rows.append(OrderedDict(
            use=t["use"],
            quantity_stage=cell(t.get("quantity_stage") or t.get("basis")),
            measurement_basis=cell(t.get("measurement_basis")),
            spaces_applicable=cell(t.get("applicable")),
            spaces_ready=cell(t.get("ready")),
            spaces_blocked=cell(t.get("blocked")),
            spaces_not_applicable=cell(t.get("not_applicable")),
            commonest_blocker=cell(t.get("commonest_blocker")),
            quantity_released=cell(t.get("quantity_released"))))
    return Sheet(
        name=SHEET_COVERAGE, columns=COVERAGE_COLUMNS, rows=tuple(rows),
        notes=(
            "Per use, per space. There is deliberately NO project total and no "
            "overall completeness figure: this is not a takeoff a client could "
            "be quoted from.",
            "GROSS and NET are different uses. A ready gross figure is not a "
            "ready quantity for a net one.",
            "QUANTITY_STAGE (GROSS / NET / DIRECT) and MEASUREMENT_BASIS are "
            "different facts. GROSS_PLASTER is a gross quantity measured on "
            "HOST_WALL_GROSS_LENGTH — the line that runs THROUGH a doorway.",
            "SKIRTING is measured on SKIRTING_ELIGIBLE_LENGTH, which is "
            "RULE_REQUIRED: no signed project rule says which stretches carry "
            "skirting, so the length is NOT_ESTABLISHED — not zero, and not "
            "the material length.",
        ))


# ------------------------------------------- old path vs new path (§20)

PATHS_COLUMNS = ("measure", "old_graph_path", "new_free_space_path",
                 "what_this_decides")


def path_comparison(old: dict | None, new: dict | None,
                    falsifiers: dict | None = None) -> Sheet:
    """The two geometry paths on the same frozen input, side by side.

    A DIAGNOSTIC sheet. It exists for one round, to show whether the
    replacement spine earns the removal of the custom geometry kernel — and
    the old column is labelled as unable to release geometry, so nobody reads
    its cycle count as a room count.
    """
    old, new = dict(old or {}), dict(new or {})
    fails = (falsifiers or {}).get("failing_invariants", [])

    def row(measure, o, n, decides=""):
        return OrderedDict(measure=measure, old_graph_path=cell(o),
                           new_free_space_path=cell(n),
                           what_this_decides=cell(decides))

    rows = [
        row("mechanism", "custom half-edge planar face walk",
            "GEOS: union of wall polygons, envelope minus barriers",
            "whether this project owns a computational geometry kernel"),
        row("space objects produced", old.get("bounded_cycles"),
            new.get("space_components"),
            "a cycle is not a room; a free-space component is a region"),
        row("single-room candidates", old.get("clear_internal_polygons"),
            new.get("occupiable_candidates")),
        row("overlapping pairs", old.get("overlapping_pairs"),
            new.get("overlapping_pairs"),
            "two bounded faces of a planar subdivision CANNOT overlap. A "
            "non-zero count here is a theorem violation, not a tuning issue"),
        row("clear-internal basis", "by offsetting a centreline face",
            "by construction — the boundary IS the drawn wall face",
            "whether an area needs a conversion with no corner term"),
        row("failing planar invariants",
            ", ".join(i[0] for i in fails) if fails else "none",
            "not applicable — no rotation system exists"),
        row("may release production geometry",
            old.get("may_release_geometry"), new.get("may_release_geometry"),
            "the old path is DIAGNOSTIC_TOPOLOGY_PATH for one round only"),
    ]
    return Sheet(
        name=SHEET_PATHS, columns=PATHS_COLUMNS, rows=tuple(rows),
        notes=(
            "DIAGNOSTIC. Both paths ran on the SAME frozen input. The old "
            "path may not release geometry and its numbers appear here for "
            "comparison only.",
            "The old path fails six invariants of planar embeddings, "
            "including the definitional one: faces are connected components "
            "of the plane minus the graph, and components are disjoint.",
            "The new path's components are connected components of ONE "
            "geometry, so they cannot overlap by construction — which is the "
            "property the old path could not provide.",
        ))


# ----------------------------------------------------------- the workbook

# ------------------------------------------------------------- 0 dashboard

DASHBOARD_COLUMNS = ("section", "measure", "value", "note")


def dashboard(bundle: dict, sheets: dict) -> Sheet:
    """The page that must be understandable in under a minute.

    Every number here is counted from a sheet that already owns it, or a status
    copied from one. The dashboard derives no quantity, which is why it can sit
    in front without becoming a second source of truth.
    """
    spaces = bundle.get("spaces", ())
    scopes = Counter(s.get("scope") for s in spaces)
    sem = Counter(s.get("semantic_source") or UNKNOWN for s in spaces)
    layers = bundle.get("geometry_layers", {})
    cov = bundle.get("coverage", ())
    ready_uses = [c for c in cov if c.get("ready")]
    net_ready = [c for c in cov if c.get("ready")
                 and str(c.get("use", "")).startswith("NET_")]
    counts = sheets.get(SHEET_ROOM_COUNTS)
    mismatches = sum(1 for r in (counts.rows if counts else ())
                     if r.get("verdict") == DIFFERS)
    exc = sheets.get(SHEET_EXCEPTIONS)
    status = bundle.get("top_level_status", {})

    def row(section, measure, value, note=""):
        return OrderedDict(section=section, measure=measure, value=cell(value),
                           note=note)

    rows = [
        row("RUN", "Project", bundle.get("project_id")),
        row("RUN", "Drawing", bundle.get("provenance", {}).get("drawing")),
        row("RUN", "Revision", bundle.get("revision_id")),
        row("RUN", "Run id", bundle.get("run_id")),
        row("RUN", "Analysis state", "COHERENT — one run",
            "Every sheet in this workbook describes the same analysis state. "
            "The export fails rather than mixing runs."),
        row("RUN", "Wall extraction", (bundle.get("manifest", {})
                                       .get("stages", {})
                                       .get("wall_extraction", {})
                                       .get("output_hash"))),
        row("RUN", "Wall graph", (bundle.get("manifest", {}).get("stages", {})
                                  .get("wall_graph", {}).get("output_hash"))),
        row("RUN", "Topology", (bundle.get("manifest", {}).get("stages", {})
                                .get("topology", {}).get("output_hash"))),

        # TWO statuses, because one word was answering two questions. Progress
        # on coverage is not permission to bill.
        row("STATUS", "TAKEOFF_COVERAGE_STATUS",
            status.get("TAKEOFF_COVERAGE_STATUS"),
            status.get("coverage_reason", "")),
        row("STATUS", "FINAL_BOQ_STATUS", status.get("FINAL_BOQ_STATUS"),
            "; ".join(status.get("boq_blockers", ())) or ""),

        row("SPACES", "Spaces on the drawing", len(spaces)),
        row("SPACES", "IN_SCOPE", scopes.get("IN_SCOPE", 0)),
        row("SPACES", "OUT_OF_SCOPE", scopes.get("OUT_OF_SCOPE", 0),
            "Not measured and not blocked: N/A. There is no work queued."),
        row("SPACES", "AMBIGUOUS", scopes.get("AMBIGUOUS", 0),
            "Blocked on an owner scope decision."),

        # FOUR LAYERS, never one "geometry ready" number. The old dashboard
        # said 36 ready / 0 unresolved while the same workbook recorded WSH-01
        # as UNRESOLVED, because "a raster region exists" was being printed as
        # "the physical space is validated".
        row("GEOMETRY", "RASTER_REGION_AVAILABLE",
            layers.get("RASTER_REGION_AVAILABLE"),
            "A raster polygon exists and can be measured. RASTER, not "
            "vector."),
        row("GEOMETRY", "WALL_GEOMETRY_AVAILABLE",
            layers.get("WALL_GEOMETRY_AVAILABLE"),
            "Its boundary was traced and closed."),
        row("GEOMETRY", "RASTER_REGION_IDENTITY_VALIDATED",
            layers.get("REGION_IDENTITY_VALIDATED"),
            "The RASTER region IS the space we named."),
        row("GEOMETRY", "RASTER_SPACE_COMPLETENESS_VALIDATED",
            layers.get("PHYSICAL_TOPOLOGY_VALIDATED"),
            "The RASTER region is the WHOLE of that space and ONLY that "
            "space. This is a segmentation fact: it does NOT mean a vector "
            "face has been reconstructed for it."),
        row("GEOMETRY", "VECTOR_SPACE_FACES_GENERATED",
            layers.get("VECTOR_SPACE_FACES_GENERATED"),
            "Every bounded cycle the space graph produced, including the "
            "building envelope, faces holding several rooms, and faces "
            "holding none. NOT additive: the envelope contains the rest."),
        row("GEOMETRY", "VECTOR_SINGLE_LABEL_FACE_CANDIDATES",
            layers.get("VECTOR_SINGLE_LABEL_FACE_CANDIDATES"),
            "Cycles enclosing exactly one labelled room. CANDIDATES: a face "
            "holding one label can still be a shaft, a closet, an adjacent "
            "enclosure or the wrong side of a wall."),
        row("GEOMETRY", "VECTOR_PHYSICAL_SPACE_VALIDATED",
            layers.get("VECTOR_PHYSICAL_SPACE_VALIDATED"),
            "Faces whose GEOMETRY and whose SPACE IDENTITY both pass. This "
            "is the only vector count that may ever carry a quantity."),
        row("GEOMETRY", "VECTOR_SPACE_IDENTITY_REJECTED",
            layers.get("VECTOR_SPACE_IDENTITY_REJECTED"),
            "Sound polygons whose claim to be the named room is CONTRADICTED "
            "by a stated defect. A valid cycle around a shaft is not the "
            "washroom."),
        row("GEOMETRY", "CLEAR_INTERNAL_POLYGONS_COMPLETE",
            layers.get("CLEAR_INTERNAL_POLYGONS_COMPLETE"),
            "Rooms whose boundary was built from actual room-facing wall "
            "faces. Only these have a measured clear-internal area."),
        row("GEOMETRY", "RASTER_RELEASE_SPACE_RECORDS_VALIDATED",
            layers.get("validated_physical_spaces"),
            "From the RASTER region and topology overlay layers. It is NOT a "
            "count of reconstructed vector rooms, and the vector counts "
            "above are the ones to read for that."),

        row("SEMANTICS", "HUMAN_VERIFIED labels", sem.get("HUMAN_VERIFIED", 0),
            "Read off the rendered sheet by a person. NOT evidence of "
            "automatic semantic extraction, and NOT evidence that the label "
            "belongs to the polygon it sits on."),
        row("SEMANTICS", "AI_INFERRED labels", sem.get("AI_INFERRED", 0)),

        row("QUANTITIES", "Uses with any space ready", len(ready_uses)),
        row("QUANTITIES", "NET quantities released", len(net_ready),
            "Zero net means no opening has been validated anywhere."),

        row("QA", "Exceptions", len(exc.rows) if exc else UNKNOWN,
            "Read the Exceptions sheet before any quantity."),
        row("QA", "Room count mismatches", mismatches),
        row("QA", "QA sample result", bundle.get("qa_sample_result"),
            "NOT_ESTABLISHED until the checker fills in measured values."),
    ]
    return Sheet(
        name=SHEET_DASHBOARD, columns=DASHBOARD_COLUMNS, rows=tuple(rows),
        notes=(
            "Every number here is counted from a sheet that owns it. The "
            "dashboard derives no quantity of its own.",
            "GEOMETRY is four separate layers. \"A raster region exists\" is "
            "not \"the physical space is validated\", and collapsing them once "
            "reported 36 ready spaces while a space was recorded UNRESOLVED.",
            "A workbook that opens cleanly is not a finished BOQ.",
        ))


# --------------------------------------------------------- quantity trace

TRACE_COLUMNS = (
    "quantity_id", "floor", "space_id", "room_type", "use", "quantity_role",
    "observation_of", "value", "unit",
    "drawing_id", "revision_id", "geometry_source", "boundary_edge_ids",
    "height_source", "opening_ids", "trade_rule_id", "trade_rule_version",
    "assembly_id", "assembly_version", "calculation_reference",
    "validation_status", "release_status", "primary_blocker",
    "drawing_preview_reference")


def quantity_trace(records, spaces=()) -> Sheet:
    """One row per established quantity, with the whole chain behind it.

    This is the sheet that answers "where did this number come from" without
    rerunning anything. Every value is copied from a trace record, so a blank
    here is a real gap in the provenance and not a formatting accident.
    """
    room = {s["space_id"]: s.get("room_type") for s in spaces}
    rows = []
    for r in records:
        rows.append(OrderedDict(
            quantity_id=r["quantity_id"], floor=cell(r.get("floor")),
            space_id=r["space_id"], room_type=cell(room.get(r["space_id"])),
            use=r.get("use"), quantity_role=cell(r.get("quantity_role")),
            observation_of=cell(r.get("observation_of")),
            value=cell(r.get("value")),
            unit=cell(r.get("unit")), drawing_id=cell(r.get("drawing_id")),
            revision_id=cell(r.get("revision_id")),
            geometry_source=cell(r.get("geometry_source")),
            boundary_edge_ids=cell(", ".join(r.get("boundary_edge_ids", []))),
            height_source=cell(r.get("height_source")),
            opening_ids=cell(", ".join(r.get("opening_ids", []))),
            trade_rule_id=cell(r.get("trade_rule_id")),
            trade_rule_version=cell(r.get("trade_rule_version")),
            assembly_id=cell(r.get("assembly_id")),
            assembly_version=cell(r.get("assembly_version")),
            calculation_reference=cell(r.get("calculation_reference")),
            validation_status=cell(r.get("validation_status")),
            release_status=cell(r.get("release_status")),
            primary_blocker=cell(r.get("primary_blocker")),
            drawing_preview_reference=cell(
                r.get("drawing_preview_reference"))))
    return Sheet(
        name=SHEET_TRACE, columns=TRACE_COLUMNS, rows=tuple(rows),
        notes=(
            "quantity_role decides what a number may be USED for. An "
            "OBSERVATION is a real measurement of a raster region attributed "
            "to no room — it keeps its value and may never be released. Only "
            "a RELEASABLE_QUANTITY belongs in a takeoff.",
            "READY never carries a blocker. If you see one, the export is "
            "broken — the type refuses to construct such a row.",
            "One row per quantity record. Nothing here is recalculated — every "
            "cell is copied from the trace the engine wrote.",
            "A NOT_ESTABLISHED in a provenance column is a real gap in the "
            "chain, not a missing export.",
            "drawing_preview_reference is reserved for the viewer that will "
            "open the drawing with this geometry highlighted.",
        ))


# ------------------------------------------------------ rules & assemblies

# §18 — a project-specific ceramic rule is NOT a room template. The taxonomy
# will matter the moment reusable templates actually exist, and calling an E27
# approved project rule a ROOM_TEMPLATE would make the two indistinguishable
# exactly when telling them apart starts to matter.
KIND_PROJECT_TRADE_RULE = "PROJECT_TRADE_RULE"
KIND_ROOM_TEMPLATE = "ROOM_TEMPLATE"
KIND_TRADE_ASSEMBLY = "TRADE_ASSEMBLY"
KIND_HEIGHT_RULE = "HEIGHT_RULE"
KIND_OPENING_RULE = "OPENING_RULE"

RULE_KINDS = (KIND_PROJECT_TRADE_RULE, KIND_ROOM_TEMPLATE,
              KIND_TRADE_ASSEMBLY, KIND_HEIGHT_RULE, KIND_OPENING_RULE)

RULES_COLUMNS = ("kind", "id", "version", "applies_to", "approval_status",
                 "approved_by", "approved_on", "source", "used_by_spaces",
                 "blocked_spaces")


def rules_and_assemblies(rules=(), assemblies=(), usage=None,
                        project_rules=()) -> Sheet:
    """Every rule and assembly the run used, with its version and approval.

    Rule coverage is auditable only if the absent ones are visible too.
    """
    usage = usage or {}
    rows = []
    for kind, items in ((KIND_PROJECT_TRADE_RULE, project_rules),
                        (KIND_ROOM_TEMPLATE, rules),
                        (KIND_TRADE_ASSEMBLY, assemblies)):
        for r in items:
            key = r.get("template_id") or r.get("assembly_id")
            u = usage.get(key, {})
            rows.append(OrderedDict(
                kind=kind, id=key, version=cell(r.get("version")),
                applies_to=cell(r.get("room_type") or r.get("trade")),
                approval_status=cell(r.get("approval_status")),
                approved_by=cell(r.get("approved_by")),
                approved_on=cell(r.get("approved_on")),
                source=cell(r.get("source")),
                used_by_spaces=cell(u.get("used")),
                blocked_spaces=cell(u.get("blocked"))))
    return Sheet(
        name=SHEET_RULES, columns=RULES_COLUMNS, rows=tuple(rows),
        notes=(
            "An empty sheet means no rule or assembly has been approved for "
            "this project. It does NOT mean defaults were used — there are no "
            "defaults.",
            "An LLM may propose a rule. Only a person approves one, and the "
            "approval carries their name and the date.",
            "PROJECT_TRADE_RULE and ROOM_TEMPLATE are different things. A "
            "project's signed ceramic rule is not a reusable room template, "
            "and a template never replaces one.",
        ))


# --------------------------------------------------- wall extraction QA

WALL_QA_COLUMNS = ("space_or_region", "side_or_candidate", "wall_band_id",
                   "representation_type", "face_a", "face_b", "end_caps",
                   "pen_style_evidence", "raster_support_pct",
                   "junction_evidence", "pairing_status", "rejection_reason",
                   "extension_reasons", "space_boundary_length_m",
                   "host_wall_gross_length_m", "material_present_length_m",
                   "opening_length_m",
                   "validation_status", "affected_space_ids", "notes")


def wall_extraction_qa(bands=(), rejections=(), sides=()) -> Sheet:
    """Why a wall is or is not in the graph, without reading a log.

    This sheet exists because the answer to "why does this room not close"
    turned out to be a single ranking choice buried in a pairing function:
    candidate mates were ranked by GAP, so a 100 mm scrap of fixture linework
    105 mm away beat the actual other face of the wall 151 mm away with 2400 mm
    of overlap. That was invisible in every report until someone went looking
    at raw vectors.

    DIAGNOSTIC ONLY. Nothing here releases a quantity.
    """
    rows = []
    for b in bands:
        pen = ("WALL_PEN" if "DRAWN_WITH_THE_SHEET_WALL_PEN"
               in b.get("supporting_evidence", ()) else "")
        rows.append(OrderedDict(
            space_or_region=cell(None), side_or_candidate="band",
            wall_band_id=b["wall_band_id"],
            representation_type=b["representation_type"],
            face_a=cell(", ".join(b.get("face_a_ids", ()))),
            face_b=cell(", ".join(b.get("face_b_ids", ()))),
            end_caps=len(b.get("cap_ids", ())),
            pen_style_evidence=cell(pen or None),
            raster_support_pct=cell(
                None if b.get("raster_support_ratio") is None
                else round(b["raster_support_ratio"] * 100, 1)),
            junction_evidence=cell(None),
            pairing_status="PAIRED",
            rejection_reason=cell(None),
            extension_reasons=cell(", ".join(
                sorted({e["extension_reason"]
                        for e in b.get("extensions", ())})) or None),
            space_boundary_length_m=cell(None),
            host_wall_gross_length_m=cell(None),
            material_present_length_m=cell(None),
            opening_length_m=cell(None),
            validation_status=b.get("validation_status"),
            affected_space_ids=cell(None),
            notes=cell(b.get("why"))))
    for r in rejections:
        rows.append(OrderedDict(
            space_or_region=cell(None), side_or_candidate="unpaired face",
            wall_band_id=cell(None),
            representation_type=cell(None),
            face_a=r["segment_id"], face_b=cell(None), end_caps=0,
            pen_style_evidence=cell(None), raster_support_pct=cell(None),
            junction_evidence=cell(r.get("candidates_in_window")),
            pairing_status="NOT_PAIRED",
            rejection_reason=r["reason"], extension_reasons=cell(None),
            space_boundary_length_m=cell(None),
            host_wall_gross_length_m=cell(None),
            material_present_length_m=cell(None),
            opening_length_m=cell(None),
            validation_status=cell(None),
            affected_space_ids=cell(None),
            # §18 — a rejection with no best mate has no gap and no overlap
            # to report. "gap None mm" reads as a measurement that was taken.
            notes=cell(
                f"best mate seen: gap {r['best_gap_mm']} mm, "
                f"overlap {r['best_overlap_mm']} mm"
                if r.get("best_gap_mm") is not None
                and r.get("best_overlap_mm") is not None
                else "no candidate mate was found for this face at all")))
    for sd in sides:
        rows.append(OrderedDict(
            space_or_region=sd.get("space_id"),
            side_or_candidate=sd.get("side"),
            wall_band_id=cell(None), representation_type=cell(None),
            face_a=cell(sd.get("nearest_edge_id")), face_b=cell(None),
            end_caps=0, pen_style_evidence=cell(None),
            raster_support_pct=cell(None),
            junction_evidence=cell(sd.get("nearest_stitch_id")),
            pairing_status=sd.get("status"),
            rejection_reason=cell(sd.get("likely_cause")),
            extension_reasons=cell(None),
            space_boundary_length_m=cell(sd.get("space_boundary_length_m")),
            host_wall_gross_length_m=cell(sd.get("host_wall_gross_length_m")),
            material_present_length_m=cell(
                sd.get("material_present_length_m")),
            opening_length_m=cell(sd.get("opening_length_m")),
            validation_status=cell(None),
            affected_space_ids=cell(sd.get("space_id")),
            notes=cell(sd.get("likely_cause"))))
    return Sheet(
        name=SHEET_WALL_QA, columns=WALL_QA_COLUMNS, rows=tuple(rows),
        notes=(
            "DIAGNOSTIC ONLY. Nothing on this sheet releases a quantity.",
            "A wall is a BAND, and it is not always two parallel strokes. "
            "representation_type says how the architect drew it; a drawing "
            "that uses filled bands or single lines must not fail for it.",
            "rejection_reason says why a probable wall face found no mate. "
            "The mate is the face a wall runs ALONGSIDE — ranking candidates "
            "by distance is what let a 100 mm scrap beat a 2400 mm wall face.",
            "A single face is never mirrored by an assumed thickness: its "
            "separation reads NOT_ESTABLISHED.",
            "FOUR LENGTH COLUMNS, because a doorway is four facts: zero "
            "material present, a real opening, a valid space closure, and "
            "part of the gross host-wall line. Every quantity engine declares "
            "which one it consumes — see engine/lengths.py.",
            "extension_reasons says why a band runs past the interval where "
            "both its faces are drawn. No extension may cross a supported "
            "opening as continuous material.",
        ))


# ------------------------------------------------------------ topology QA

# graph_type and topology_run_id are first on purpose. A material-graph face
# and a space-boundary face are produced by DIFFERENT GRAPHS, and a stale
# material face sitting unlabelled in this sheet would read as the new space
# topology result with nothing looking wrong.
# §26 — `component` held FACE-0003. A GRAPH component (GC-), a PLANAR
# component (PC-) and a FACE (FACE-/SF-) are three different things, so each
# gets its own column and its own namespace. An id in the wrong column is a
# diagnostic that quietly points at the wrong object.
TOPOLOGY_COLUMNS = ("face_id", "graph_type", "topology_run_id",
                    "graph_component", "planar_component",
                    "cycle_class", "status", "area_m2", "perimeter_m",
                    "labelled_rooms_inside", "containment_verdict",
                    "portal_edges",
                    "raster_regions", "raster_spaces", "relationship",
                    "overlap_pct", "dependent_probable_edges", "micro_class",
                    "candidate_space_match", "holes", "blocker", "notes")


def topology_qa(faces=(), correspondence=(), containment=()) -> Sheet:
    """The diagnostic face engine's output, where it can be inspected safely.

    Faces appear here and NOWHERE ELSE in the workbook. They do not touch a
    quantity, a coverage count or a release status, because a diagnostic face
    that quietly became the measurement basis would be the worst outcome
    available. Migration is explicit: E31A_CANDIDATE -> independently
    validated -> PHYSICAL_SPACE_GEOMETRY_ACCEPTED.
    """
    corr = {c["face_id"]: c for c in correspondence}
    # Joined by face id. ORDER IS NEVER IDENTITY.
    held = {c["space_face_id"]: c for c in containment}
    rows = []
    for f in faces:
        fid = f.get("face_id") or f.get("space_face_id")
        c = corr.get(fid, {})
        h = held.get(fid, {})
        probable = f.get("edge_validation_summary", {}).get("PROBABLE")
        rows.append(OrderedDict(
            face_id=fid,
            graph_type=cell(f.get("graph_type")),
            topology_run_id=cell(f.get("topology_run_id")),
            graph_component=cell(f.get("component_id")),
            planar_component=cell(f.get("planar_component_id")),
            cycle_class=cell(h.get("cycle_class")),
            status=cell(f.get("status") or f.get("geometry_status")),
            labelled_rooms_inside=cell(h.get("labelled_regions_contained")),
            containment_verdict=cell(h.get("verdict")),
            portal_edges=cell(h.get("portal_edges")),
            area_m2=cell(f.get("area_m2")),
            perimeter_m=cell(f.get("perimeter_m")),
            raster_regions=cell(", ".join(
                str(r) for r in c.get("raster_region_ids", ()))),
            raster_spaces=cell(", ".join(c.get("raster_space_ids", ()))),
            relationship=cell(c.get("relationship")),
            overlap_pct=cell(None if c.get("overlap_ratio") is None
                             else round(c["overlap_ratio"] * 100, 1)),
            dependent_probable_edges=cell(probable),
            micro_class=cell(f.get("micro_class")),
            candidate_space_match=cell(
                (c.get("raster_space_ids") or (None,))[0]),
            holes=len(f.get("holes", ())),
            blocker=cell("; ".join(f.get("blockers", ())) or None),
            notes=cell(c.get("why"))))
    return Sheet(
        name=SHEET_TOPOLOGY, columns=TOPOLOGY_COLUMNS, rows=tuple(rows),
        notes=(
            "DIAGNOSTIC ONLY. Every face here is a hypothesis produced by the "
            "vector wall graph alone. None releases a quantity and none has "
            "replaced the current geometry source.",
            "The raster columns are a COMPARISON made after the face was "
            "generated. The region map was not an input to generating it.",
            "VECTOR_SPLITS_RASTER is the class worth reading first: it may "
            "expose an under-segmented space, and it is equally where a false "
            "split would hide.",
            "GRAPH_TYPE says which graph produced the face. MATERIAL_WALL_GRAPH "
            "is open at every doorway; SPACE_BOUNDARY_GRAPH adds zero-material "
            "closures across geometry-supported openings. They are different "
            "answers to different questions and must never be read as one set.",
            "LABELLED_ROOMS_INSIDE is containment of a labelled region's "
            "centroid in the face POLYGON — not bounding-box overlap. A face "
            "holding more than one labelled room is an ENCLOSURE_CYCLE, and "
            "the cause is not always a missing wall.",
            "GRAPH_COMPONENT (GC-) and PLANAR_COMPONENT (PC-) are different "
            "objects and neither is a face. A blank graph component means no "
            "graph component was supplied, not that there is none.",
            "CYCLE_CLASS is the only column that says whether a cycle is a "
            "room. A BUILDING_ENVELOPE, a HOLE and a WALL_CAVITY are all "
            "bounded counterclockwise walks, and none of them is floor.",
        ))


# --------------------------------------------------------- revision delta

REVISION_COLUMNS = ("entity_type", "entity_id", "change", "matched_by",
                    "prior_id", "detail")


def revision_delta(delta: dict) -> Sheet:
    """What changed since the prior revision, or that there isn't one.

    "Nothing changed" and "nothing to compare" look identical in a table and
    mean opposite things, so with a single revision this sheet says so in words
    and carries no rows at all.
    """
    status = delta.get("status", "NO_PRIOR_REVISION_AVAILABLE")
    rows = tuple(OrderedDict(
        entity_type=c["entity_type"], entity_id=c["entity_id"],
        change=c["change"], matched_by=c["matched_by"],
        prior_id=cell(c.get("prior_id")), detail=cell(c.get("detail")))
        for c in delta.get("entity_changes", ()))
    notes = [f"STATUS: {status}"]
    if delta.get("why"):
        notes.append(delta["why"])
    if not rows:
        notes.append("No rows, because there is no baseline — not because "
                     "nothing changed.")
    return Sheet(name=SHEET_REVISION, columns=REVISION_COLUMNS, rows=rows,
                 notes=tuple(notes))


# §18 — narrative cells may not carry a missing value as if it were a fact.
#
# The last workbook read: "source-path fragmentation is NOT the cause — only
# None of None short marks share a path with a long run." A structured field
# had been formatted straight into prose, and the sentence still read as a
# confident measurement. The number was absent; the claim was not.
#
# Checked at export, on the columns that carry sentences rather than values.
NARRATIVE_COLUMNS = ("issue", "cause", "effect", "why", "notes", "note",
                     "engineering_next_action", "owner_input_required",
                     "owner_input_helpful_if_available", "resolution",
                     "current_diagnostic", "detail", "blocker",
                     "commonest_blocker", "verdict")

FORBIDDEN_IN_PROSE = ("None", "null", "NaN", "nan of", "undefined")


def assert_no_missing_value_prose(sheets) -> None:
    """Refuse to export a workbook whose sentences contain missing values.

    A deliberate quotation is not what this catches: the check is on whole
    words in narrative columns, and a value that is genuinely absent belongs in
    an empty cell — where `cell()` already puts it — not inside a sentence.
    """
    bad = []
    for sh in sheets:
        for i, row in enumerate(sh.rows, 1):
            for col in NARRATIVE_COLUMNS:
                v = row.get(col)
                if not isinstance(v, str):
                    continue
                words = v.replace(",", " ").replace(".", " ").split()
                for token in FORBIDDEN_IN_PROSE:
                    if token in words or (" " in token and token in v):
                        bad.append(f"{sh.name} row {i} column {col!r}: "
                                   f"{v[:120]!r}")
    if bad:
        raise QaWorkbookError(
            "a narrative cell formatted a missing value into prose:\n  - "
            + "\n  - ".join(bad[:20])
            + "\nA structured field that is absent belongs in an EMPTY CELL. "
              "Inside a sentence it still reads as a measurement, and the "
              "reader has no way to tell that the number was never taken.")


@dataclass(frozen=True)
class Workbook:
    project_id: str
    title: str
    sheets: tuple[Sheet, ...]
    provenance: tuple[tuple[str, str], ...] = ()
    warnings: tuple[str, ...] = ()

    def by_name(self) -> dict[str, Sheet]:
        return {s.name: s for s in self.sheets}


def build_workbook(bundle: dict) -> Workbook:
    """Assemble the sheets from values already established elsewhere.

    `bundle` is data, not engines. That is the whole design: this function
    cannot reach back into geometry even by accident, because it was never
    given anything to reach with.
    """
    for required in ("project_id", "spaces"):
        if required not in bundle:
            raise QaWorkbookError(
                f"the bundle has no {required!r}; a QA workbook without it "
                "would describe a project it cannot name")

    # ONE WORKBOOK, ONE ANALYSIS STATE. The previous export carried a V2 wall
    # extraction beside V1 exceptions reporting 115 components and 228 termini,
    # and said planar extraction had not started after it had. Every sheet was
    # internally correct and the workbook as a whole was false — the worst
    # shape a report can take, because nothing in it looks wrong.
    manifest = bundle.get("manifest")
    if manifest is None:
        raise QaWorkbookError(
            "this bundle carries no run manifest. A workbook that cannot "
            "prove its sheets describe one analysis state may not be built: "
            "freshness must be a property of the data, not of which files "
            "happened to be on disk")
    problems = manifest.get("problems") or []
    if problems or not manifest.get("coherent", False):
        raise QaWorkbookError(
            "the workbook would mix analysis runs:\n  - "
            + "\n  - ".join(problems or ["the manifest reports incoherent"])
            + "\nRe-run the stale stages before exporting.")

    spaces = bundle["spaces"]
    quantities = bundle.get("quantities", {})
    releases = bundle.get("releases", {})
    wall_records = bundle.get("wall_records", ())

    flags = bundle.get("risk_flags")
    if flags is None:
        flags = risk_flags(spaces, quantities, releases,
                           wall_records=wall_records)

    built = {
        SHEET_ROOM_REGISTER: room_register(spaces),
        SHEET_ROOM_COUNTS: room_count_summary(
            spaces, bundle.get("manual_expected_counts"),
            bundle.get("room_counts")),
        SHEET_TRACE: quantity_trace(bundle.get("quantity_traces", ()), spaces),
        SHEET_FLOORING: flooring_ceramic_qa(spaces, quantities, releases),
        SHEET_WALLS: wall_quantities(wall_records, releases),
        SHEET_EXCEPTIONS: exceptions(
            space_exceptions=bundle.get("space_exceptions", ()),
            known_gaps=bundle.get("known_gaps", ()),
            # Generated from the CURRENT diagnostic run, never hand-written.
            findings=bundle.get("findings", ()),
            scope_exceptions=bundle.get("scope_exceptions", ())),
        SHEET_SAMPLE: random_qa_sample(
            spaces, quantities, releases, project_id=bundle["project_id"],
            per_stratum=bundle.get("sample_per_stratum", 2),
            seed=bundle.get("sample_seed", DEFAULT_SAMPLE_SEED),
            risk_flags=flags),
        SHEET_RULES: rules_and_assemblies(
            bundle.get("room_templates", ()), bundle.get("assemblies", ()),
            bundle.get("rule_usage"), bundle.get("project_trade_rules", ())),
        SHEET_WALL_QA: wall_extraction_qa(
            bundle.get("wall_bands", ()), bundle.get("wall_rejections", ()),
            bundle.get("wall_sides", ())),
        SHEET_TOPOLOGY: topology_qa(bundle.get("faces", ()),
                                    bundle.get("face_correspondence", ()),
                                    bundle.get("face_containment", ())),
        SHEET_COVERAGE: takeoff_coverage(bundle.get("coverage", ())),
        SHEET_PATHS: path_comparison(
            bundle.get("old_graph_path"), bundle.get("new_free_space_path"),
            bundle.get("old_path_falsifiers")),
        SHEET_REVISION: revision_delta(bundle.get("revision_delta", {})),
    }
    # The dashboard counts the other sheets, so it is built last and placed
    # first. It owns no number of its own.
    built[SHEET_DASHBOARD] = dashboard(bundle, built)

    sheets = tuple(built[name] for name in SHEET_ORDER)
    assert_no_missing_value_prose(sheets)
    return Workbook(
        project_id=bundle["project_id"],
        title=bundle.get("title", f"QA workbook — project {bundle['project_id']}"),
        sheets=sheets,
        provenance=tuple(sorted(bundle.get("provenance", {}).items())),
        warnings=tuple(bundle.get("warnings", ())) + (
            "READ-ONLY. Nothing written in this workbook returns to the engine. "
            "Corrections belong in the source drawing, the space map or a "
            "signed trade rule — not in a cell.",
            "NOT A QUOTATION. No net quantity has been released, and no "
            "material, recipe or rate appears anywhere in this file.",
            "Manual entries are VALIDATION EVIDENCE ONLY. An expected count or "
            "a spot measurement you type here never feeds a production "
            "quantity.",
        ))
