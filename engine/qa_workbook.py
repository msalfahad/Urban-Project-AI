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

SHEET_ORDER = (SHEET_DASHBOARD, SHEET_ROOM_REGISTER, SHEET_ROOM_COUNTS,
               SHEET_TRACE, SHEET_FLOORING, SHEET_WALLS, SHEET_EXCEPTIONS,
               SHEET_SAMPLE, SHEET_RULES, SHEET_COVERAGE, SHEET_REVISION)

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

ROOM_COUNT_COLUMNS = (
    "room_type", "system_total_count", "system_in_scope_count",
    "engine_out_of_scope", "engine_ambiguous", "manual_expected_total",
    "manual_expected_in_scope", "total_difference", "in_scope_difference",
    "verdict", "checker_note")


def room_count_summary(spaces, manual_expected: dict | None = None) -> Sheet:
    """Counts by room type, against TWO separate manual checks.

    They answer two different questions and a single count agrees with neither:

        what rooms EXIST on the drawing   -> a drawing question
        what rooms are in the CONTRACT    -> a commercial question

    The manual columns are here whether or not anybody has filled them in, and
    while they are empty the verdict is NOT_COMPARED. An empty expectation is
    not agreement: a workbook that prints AGREES against a blank column has
    invented a confirmation.

    Counting rows is not recalculating a quantity. No area or length is derived.
    """
    expected = manual_expected or {}
    by_type: dict[str, list] = {}
    for sp in spaces:
        by_type.setdefault(sp.get("room_type") or UNKNOWN, []).append(sp)

    rows = []
    for rt in sorted(by_type):
        group = by_type[rt]
        scopes = Counter(sp.get("scope") for sp in group)
        in_scope = scopes.get("IN_SCOPE", 0)
        exp = expected.get(rt)
        if isinstance(exp, dict):
            exp_total, exp_scope = exp.get("total"), exp.get("in_scope")
        elif exp is None:
            exp_total = exp_scope = None
        else:
            exp_total, exp_scope = exp, None

        d_total = UNKNOWN if exp_total is None else len(group) - exp_total
        d_scope = UNKNOWN if exp_scope is None else in_scope - exp_scope
        compared = [d for d in (d_total, d_scope) if d != UNKNOWN]
        if not compared:
            verdict = NOT_COMPARED
        elif all(d == 0 for d in compared):
            verdict = AGREES
        else:
            verdict = DIFFERS

        rows.append(OrderedDict(
            room_type=rt, system_total_count=len(group),
            system_in_scope_count=in_scope,
            engine_out_of_scope=scopes.get("OUT_OF_SCOPE", 0),
            engine_ambiguous=scopes.get("AMBIGUOUS", 0),
            manual_expected_total=cell(exp_total),
            manual_expected_in_scope=cell(exp_scope),
            total_difference=d_total, in_scope_difference=d_scope,
            verdict=verdict, checker_note=FOR_THE_CHECKER))
    return Sheet(
        name=SHEET_ROOM_COUNTS, columns=ROOM_COUNT_COLUMNS, rows=tuple(rows),
        human_columns=("manual_expected_total", "manual_expected_in_scope",
                       "checker_note"),
        notes=(
            "Two manual columns, because they answer two questions: what rooms "
            "EXIST on the drawing, and what rooms are in the CONTRACT.",
            "While both are empty the verdict is NOT_COMPARED — never AGREES.",
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
                     "potential_coverage_unlocked", "owner_action_required",
                     "status", "what_would_resolve_it")

# Severity is about consequence, not about how loud the message is.
BLOCKING = "BLOCKING"
UNDERSTATED = "UNDERSTATES_A_QUANTITY"
ADVISORY = "ADVISORY"


def exceptions(*, space_exceptions=(), known_gaps=(), graph_exceptions=(),
               scope_exceptions=()) -> Sheet:
    """Everything that is not right, ranked by what fixing it would unlock.

    A list of forty blockers in arbitrary order is not actionable. Ranked by
    coverage unlocked, it becomes "approve one trade rule and eight spaces
    open" — which is a decision the owner can actually take.

    The ranking is by COUNT of spaces and uses, never by money. No financial
    impact is estimated anywhere: a cost attached to an unvalidated quantity
    would be quoted long before the quantity was.
    """
    rows = []

    def add(severity, area, e, default_resolution=""):
        spaces = e.get("affected_spaces")
        uses = e.get("affected_uses")
        rows.append(OrderedDict(
            priority=0,                       # filled in below, once sorted
            severity=severity, scope_of_issue=area,
            subject=cell(e.get("subject")), issue=cell(e.get("issue") or e.get("item")),
            cause=cell(e.get("cause")), effect=cell(e.get("effect")),
            affected_spaces=cell(spaces), affected_uses=cell(uses),
            affected_boq_sections=cell(e.get("affected_boq_sections")),
            potential_coverage_unlocked=cell(e.get("coverage_unlocked")),
            owner_action_required=cell(e.get("owner_action")),
            status=cell(e.get("status")),
            what_would_resolve_it=cell(e.get("resolution") or default_resolution
                                       or None)))

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

    def key(r):
        spaces = r["affected_spaces"]
        uses = r["affected_uses"]
        return (-(spaces if isinstance(spaces, int) else 0),
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
        ))


# ------------------------------------------------- 6 random QA sample

SAMPLE_COLUMNS = ("qa_type", "stratum", "why_selected", "space_id",
                  "room_type", "scope", "what_to_check", "engine_value",
                  "engine_unit", "engine_status", "checker_measurement",
                  "checker_agrees", "checker_note")

# The seed is part of the record. A sample nobody can reproduce is an anecdote.
DEFAULT_SAMPLE_SEED = 23010


def _seed_for(project_id: str, seed: int) -> int:
    """A stable seed per project, so two projects do not draw the same rooms."""
    h = hashlib.sha256(f"{project_id}:{seed}".encode()).hexdigest()
    return int(h[:16], 16)


def _sample_row(qa_type, stratum, why, s, quantities, releases, check, unit):
    sid = s["space_id"]
    return OrderedDict(
        qa_type=qa_type, stratum=stratum, why_selected=why, space_id=sid,
        room_type=cell(s.get("room_type")), scope=cell(s.get("scope")),
        what_to_check=check,
        engine_value=cell(quantities.get(sid, {}).get(check)),
        engine_unit=unit,
        engine_status=cell(releases.get(sid, {}).get("primary_blocker")),
        checker_measurement=FOR_THE_CHECKER, checker_agrees=FOR_THE_CHECKER,
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
        human_columns=("checker_measurement", "checker_agrees", "checker_note"),
        notes=(
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
    geom = Counter(s.get("geometry_status") or UNKNOWN for s in spaces)
    sem = Counter(s.get("semantic_source") or UNKNOWN for s in spaces)
    cov = bundle.get("coverage", ())
    ready_uses = [c for c in cov if c.get("ready")]
    net_ready = [c for c in cov if c.get("ready")
                 and str(c.get("use", "")).startswith("NET_")]
    counts = sheets.get(SHEET_ROOM_COUNTS)
    mismatches = sum(1 for r in (counts.rows if counts else ())
                     if r.get("verdict") == DIFFERS)
    exc = sheets.get(SHEET_EXCEPTIONS)

    if net_ready:
        status = STATUS_COMPLETE if len(net_ready) == len(cov) else STATUS_PARTIAL
    elif ready_uses:
        status = STATUS_PARTIAL
    else:
        status = STATUS_BLOCKED

    def row(section, measure, value, note=""):
        return OrderedDict(section=section, measure=measure, value=cell(value),
                           note=note)

    rows = [
        row("RUN", "Project", bundle.get("project_id")),
        row("RUN", "Drawing", bundle.get("provenance", {}).get("drawing")),
        row("RUN", "Revision", bundle.get("revision_id")),
        row("RUN", "Run id", bundle.get("run_id")),
        row("RUN", "TAKEOFF STATUS", status,
            "BLOCKED means no quantity may be used. It is the state of the "
            "measurement, not a delay."),

        row("SPACES", "Spaces on the drawing", len(spaces)),
        row("SPACES", "IN_SCOPE", scopes.get("IN_SCOPE", 0)),
        row("SPACES", "OUT_OF_SCOPE", scopes.get("OUT_OF_SCOPE", 0)),
        row("SPACES", "AMBIGUOUS", scopes.get("AMBIGUOUS", 0),
            "Scope gates every use. An undecided space releases nothing."),

        row("GEOMETRY", "Geometry ready", geom.get("VALIDATED", 0)),
        row("GEOMETRY", "Geometry unresolved",
            len(spaces) - geom.get("VALIDATED", 0)),

        row("SEMANTICS", "HUMAN_VERIFIED labels", sem.get("HUMAN_VERIFIED", 0),
            "Read off the rendered sheet by a person. NOT evidence of "
            "automatic semantic extraction."),
        row("SEMANTICS", "AI_INFERRED labels", sem.get("AI_INFERRED", 0)),
        row("SEMANTICS", "Unresolved labels", sem.get(UNKNOWN, 0)),

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
            "A workbook that opens cleanly is not a finished BOQ.",
        ))


# --------------------------------------------------------- quantity trace

TRACE_COLUMNS = (
    "quantity_id", "floor", "space_id", "room_type", "use", "value", "unit",
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
            use=r.get("use"), value=cell(r.get("value")),
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
            "One row per quantity record. Nothing here is recalculated — every "
            "cell is copied from the trace the engine wrote.",
            "A NOT_ESTABLISHED in a provenance column is a real gap in the "
            "chain, not a missing export.",
            "drawing_preview_reference is reserved for the viewer that will "
            "open the drawing with this geometry highlighted.",
        ))


# ------------------------------------------------------ rules & assemblies

RULES_COLUMNS = ("kind", "id", "version", "applies_to", "approval_status",
                 "approved_by", "approved_on", "source", "used_by_spaces",
                 "blocked_spaces")


def rules_and_assemblies(rules=(), assemblies=(), usage=None) -> Sheet:
    """Every rule and assembly the run used, with its version and approval.

    Rule coverage is auditable only if the absent ones are visible too.
    """
    usage = usage or {}
    rows = []
    for kind, items in (("ROOM_TEMPLATE", rules), ("TRADE_ASSEMBLY", assemblies)):
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
            spaces, bundle.get("manual_expected_counts")),
        SHEET_TRACE: quantity_trace(bundle.get("quantity_traces", ()), spaces),
        SHEET_FLOORING: flooring_ceramic_qa(spaces, quantities, releases),
        SHEET_WALLS: wall_quantities(wall_records, releases),
        SHEET_EXCEPTIONS: exceptions(
            space_exceptions=bundle.get("space_exceptions", ()),
            known_gaps=bundle.get("known_gaps", ()),
            graph_exceptions=bundle.get("graph_exceptions", ()),
            scope_exceptions=bundle.get("scope_exceptions", ())),
        SHEET_SAMPLE: random_qa_sample(
            spaces, quantities, releases, project_id=bundle["project_id"],
            per_stratum=bundle.get("sample_per_stratum", 2),
            seed=bundle.get("sample_seed", DEFAULT_SAMPLE_SEED),
            risk_flags=flags),
        SHEET_RULES: rules_and_assemblies(
            bundle.get("room_templates", ()), bundle.get("assemblies", ()),
            bundle.get("rule_usage")),
        SHEET_COVERAGE: takeoff_coverage(bundle.get("coverage", ())),
        SHEET_REVISION: revision_delta(bundle.get("revision_delta", {})),
    }
    # The dashboard counts the other sheets, so it is built last and placed
    # first. It owns no number of its own.
    built[SHEET_DASHBOARD] = dashboard(bundle, built)

    sheets = tuple(built[name] for name in SHEET_ORDER)
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
