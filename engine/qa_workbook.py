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
SHEET_ROOM_REGISTER = "Room Register"
SHEET_ROOM_COUNTS = "Room Count Summary"
SHEET_FLOORING = "Flooring and Ceramic QA"
SHEET_WALLS = "Wall Quantities"
SHEET_EXCEPTIONS = "Exceptions"
SHEET_SAMPLE = "Random QA Sample"
SHEET_COVERAGE = "Takeoff Coverage"

SHEET_ORDER = (SHEET_ROOM_REGISTER, SHEET_ROOM_COUNTS, SHEET_FLOORING,
               SHEET_WALLS, SHEET_EXCEPTIONS, SHEET_SAMPLE, SHEET_COVERAGE)

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
    "measurement_basis", "geometry_status", "label_confidence", "flag")


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
        label_confidence=cell(s.get("semantic_label_confidence")),
        flag=cell(s.get("flag")),
    ) for s in spaces)
    return Sheet(
        name=SHEET_ROOM_REGISTER, columns=ROOM_REGISTER_COLUMNS, rows=rows,
        notes=(
            "Every space the engine identified, including spaces it could not "
            "measure. NOT_ESTABLISHED means no value was established — it is "
            "not zero.",
            "Room names were read off the rendered sheet by a human; areas are "
            "machine-measured and independent of the names.",
        ))


# ------------------------------------------------- 2 room count summary

ROOM_COUNT_COLUMNS = (
    "room_type", "engine_count", "engine_in_scope", "engine_out_of_scope",
    "engine_ambiguous", "manual_expected_count", "difference", "verdict",
    "checker_note")


def room_count_summary(spaces, manual_expected: dict | None = None) -> Sheet:
    """Counts by room type, with the manual columns present and honest.

    The manual columns are here whether or not anybody has filled them in, and
    when they are empty the verdict is NOT_COMPARED. An empty expectation is not
    agreement: a workbook that prints AGREES against a blank column has invented
    a confirmation.

    Counting rows is not recalculating a quantity. No area or length is derived.
    """
    expected = manual_expected or {}
    by_type: dict[str, list] = {}
    for s in spaces:
        by_type.setdefault(s.get("room_type") or UNKNOWN, []).append(s)

    rows = []
    for rt in sorted(by_type):
        group = by_type[rt]
        scopes = Counter(s.get("scope") for s in group)
        exp = expected.get(rt)
        if exp is None:
            diff, verdict = UNKNOWN, NOT_COMPARED
        else:
            diff = len(group) - exp
            verdict = AGREES if diff == 0 else DIFFERS
        rows.append(OrderedDict(
            room_type=rt, engine_count=len(group),
            engine_in_scope=scopes.get("IN_SCOPE", 0),
            engine_out_of_scope=scopes.get("OUT_OF_SCOPE", 0),
            engine_ambiguous=scopes.get("AMBIGUOUS", 0),
            manual_expected_count=cell(exp), difference=diff, verdict=verdict,
            checker_note=FOR_THE_CHECKER))
    return Sheet(
        name=SHEET_ROOM_COUNTS, columns=ROOM_COUNT_COLUMNS, rows=tuple(rows),
        human_columns=("manual_expected_count", "checker_note"),
        notes=(
            "manual_expected_count is for the surveyor to fill in. While it is "
            "empty the verdict is NOT_COMPARED — never AGREES.",
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

EXCEPTION_COLUMNS = ("severity", "scope_of_issue", "subject", "issue", "cause",
                     "effect", "status", "what_would_resolve_it")

# Severity is about consequence, not about how loud the message is.
BLOCKING = "BLOCKING"
UNDERSTATED = "UNDERSTATES_A_QUANTITY"
ADVISORY = "ADVISORY"


def exceptions(*, space_exceptions=(), known_gaps=(), graph_exceptions=(),
               scope_exceptions=()) -> Sheet:
    """Everything that is not right, in one place, with what would fix it.

    A workbook whose other six sheets look tidy needs this one to be believed.
    """
    rows = []
    for g in known_gaps:
        rows.append(OrderedDict(
            severity=UNDERSTATED, scope_of_issue="GEOMETRY",
            subject=cell(g.get("subject")), issue=cell(g.get("item")),
            cause=cell(g.get("cause")), effect=cell(g.get("effect")),
            status=cell(g.get("status")),
            what_would_resolve_it=cell(g.get("resolution"))))
    for e in space_exceptions:
        rows.append(OrderedDict(
            severity=BLOCKING, scope_of_issue="RELEASE",
            subject=cell(e.get("subject")), issue=cell(e.get("issue")),
            cause=cell(e.get("cause")), effect=cell(e.get("effect")),
            status=cell(e.get("status")),
            what_would_resolve_it=cell(e.get("resolution"))))
    for e in scope_exceptions:
        rows.append(OrderedDict(
            severity=BLOCKING, scope_of_issue="SCOPE",
            subject=cell(e.get("subject")), issue=cell(e.get("issue")),
            cause=cell(e.get("cause")), effect=cell(e.get("effect")),
            status=cell(e.get("status")),
            what_would_resolve_it=cell(e.get("resolution"))))
    for e in graph_exceptions:
        rows.append(OrderedDict(
            severity=cell(e.get("severity")) if e.get("severity") else ADVISORY,
            scope_of_issue="TOPOLOGY", subject=cell(e.get("subject")),
            issue=cell(e.get("issue")), cause=cell(e.get("cause")),
            effect=cell(e.get("effect")), status=cell(e.get("status")),
            what_would_resolve_it=cell(e.get("resolution"))))
    return Sheet(
        name=SHEET_EXCEPTIONS, columns=EXCEPTION_COLUMNS, rows=tuple(rows),
        notes=(
            "Read this sheet before any other. The quantities elsewhere are "
            "only as good as this list is short.",
        ))


# ------------------------------------------------- 6 random QA sample

SAMPLE_COLUMNS = ("stratum", "space_id", "room_type", "scope", "what_to_check",
                  "engine_value", "engine_unit", "engine_status",
                  "checker_measurement", "checker_agrees", "checker_note")

# The seed is part of the record. A sample nobody can reproduce is an anecdote.
DEFAULT_SAMPLE_SEED = 23010


def _seed_for(project_id: str, seed: int) -> int:
    """A stable seed per project, so two projects do not draw the same rooms."""
    h = hashlib.sha256(f"{project_id}:{seed}".encode()).hexdigest()
    return int(h[:16], 16)


def random_qa_sample(spaces, quantities: dict, releases: dict, *,
                     project_id: str, per_stratum: int = 2,
                     seed: int = DEFAULT_SAMPLE_SEED,
                     check: str = "floor_area_m2", unit: str = "m2") -> Sheet:
    """A stratified, seeded sample to measure by hand.

    Stratified by room type so the sample cannot land entirely on bathrooms,
    and seeded so the same drawing draws the same rooms every run — otherwise a
    disagreement can be made to disappear by exporting again.

    Blocked spaces are eligible on purpose. Checking only what the engine is
    already confident about measures nothing.
    """
    rng = random.Random(_seed_for(project_id, seed))
    strata: dict[str, list] = {}
    for s in spaces:
        strata.setdefault(s.get("room_type") or UNKNOWN, []).append(s)

    rows = []
    for rt in sorted(strata):
        group = sorted(strata[rt], key=lambda s: s["space_id"])
        picked = group if len(group) <= per_stratum else rng.sample(
            group, per_stratum)
        for s in sorted(picked, key=lambda s: s["space_id"]):
            sid = s["space_id"]
            rows.append(OrderedDict(
                stratum=rt, space_id=sid, room_type=cell(s.get("room_type")),
                scope=cell(s.get("scope")), what_to_check=check,
                engine_value=cell(quantities.get(sid, {}).get(check)),
                engine_unit=unit,
                engine_status=cell(releases.get(sid, {}).get("primary_blocker")),
                checker_measurement=FOR_THE_CHECKER,
                checker_agrees=FOR_THE_CHECKER, checker_note=FOR_THE_CHECKER))
    return Sheet(
        name=SHEET_SAMPLE, columns=SAMPLE_COLUMNS, rows=tuple(rows),
        human_columns=("checker_measurement", "checker_agrees", "checker_note"),
        notes=(
            f"Stratified by room type, {per_stratum} per stratum. Seed "
            f"{seed} on project {project_id}: the same drawing draws the same "
            "rooms every run, so a disagreement cannot be exported away.",
            "Spaces with blocked quantities are included deliberately.",
        ))


# ---------------------------------------------------- 7 takeoff coverage

COVERAGE_COLUMNS = ("use", "basis", "spaces_applicable", "spaces_ready",
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
            use=t["use"], basis=cell(t.get("basis")),
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
        ))


# ----------------------------------------------------------- the workbook

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
    """Assemble the seven sheets from values already established elsewhere.

    `bundle` is data, not engines. That is the whole design: this function
    cannot reach back into geometry even by accident, because it was never
    given anything to reach with.
    """
    for required in ("project_id", "spaces"):
        if required not in bundle:
            raise QaWorkbookError(
                f"the bundle has no {required!r}; a QA workbook without it "
                "would describe a project it cannot name")

    spaces = bundle["spaces"]
    quantities = bundle.get("quantities", {})
    releases = bundle.get("releases", {})
    sheets = (
        room_register(spaces),
        room_count_summary(spaces, bundle.get("manual_expected_counts")),
        flooring_ceramic_qa(spaces, quantities, releases),
        wall_quantities(bundle.get("wall_records", ()), releases),
        exceptions(space_exceptions=bundle.get("space_exceptions", ()),
                   known_gaps=bundle.get("known_gaps", ()),
                   graph_exceptions=bundle.get("graph_exceptions", ()),
                   scope_exceptions=bundle.get("scope_exceptions", ())),
        random_qa_sample(spaces, quantities, releases,
                         project_id=bundle["project_id"],
                         per_stratum=bundle.get("sample_per_stratum", 2),
                         seed=bundle.get("sample_seed", DEFAULT_SAMPLE_SEED)),
        takeoff_coverage(bundle.get("coverage", ())),
    )
    assert [s.name for s in sheets] == list(SHEET_ORDER)
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
        ))
