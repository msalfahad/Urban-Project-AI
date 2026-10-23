"""DOCUMENT_REGISTER_V1 (T-195): one row per issued sheet, and a check that every ledger citation names a sheet that is
in the register, in one revision.

A check piece (residential review R9, PROJECT_UNDERSTANDING_ASSESSMENT section 6): NOT wired into any method version
(ARCH_TAKEOFF_V2.9 .. V3.0.x and route G are unchanged); nothing here is read by a released line and nothing here is a
quantity. Standard library only; imports no engine module. Its findings are issue rows, never quantities.

Why: a quantity is only as good as the sheet it was measured on. When a set is reissued, a ledger that cites "sheet 07"
without a revision can silently mix two issues. The register makes the issue explicit:

  1. SHEET: one row per printed sheet (set id + page in the set) with discipline, drawing title, scale, the number and
     revision PRINTED in the title block (or NONE_PRINTED: never invented), the printed date, the plot stamp, and every
     file that carries the sheet (one sheet is often on Drive several times: a full set, split parts, single pages).
  2. REVISION BASIS per sheet: PRINTED (a revision letter / number is printed) or FILE_PIN (nothing is printed, so the
     only revision control is the identity of the carrier file: its sha256 or its title + byte size). A set with no
     printed revision is recorded as such, never given an assumed "rev 0".
  3. CITATION CHECK: free text (ledgers, reports, CSV cells) is scanned with the project's citation grammar (a list of
     CitationRule supplied by the caller: the module holds no project names). Each citation resolves to a sheet key or a
     file and gets one verdict:
        RESOLVED            the sheet is in the register and has exactly one revision state
        FILE_ONLY           a whole file is cited (no page); resolved to the file, not to a sheet
        PART_ONLY           a split part is cited without a page: resolves to a page range
        NOT_IN_REGISTER     the page or file is not in the register (out of the set's range, unknown file)
        PART_FILE_PAGE      "part 05-06 page 1": the page is not a set page of the part but fits as the page INSIDE
                            the part file (here set page 5). Resolved, but the citation uses the other page basis:
                            an issue row (two numbering bases in one project), never silently re-read
        PART_MISMATCH       "part 07-08 page 11": the page is neither a set page of the part nor a page of the file
        MULTI_REVISION      the sheet exists in two or more revision states in the register: the citation must name
                            which one (flagged even when the citation happens to be right)
        CONTENT_REVIEW      the words around the citation name an element that the register places only on OTHER sheets
                            and nothing the cited sheet carries (a hint for a reviewer, never an error by itself)
  4. MISSING SHEETS: the register is compared with a checklist of what a complete residential set normally holds
     (RESIDENTIAL_SET_CHECKLIST: an engineering-practice list, NOT a Kuwait regulation; provenance stated per item).
     A missing sheet is a project-information item (assessment section 6 list), never a reason to invent its content.

Guards (ValueError): a duplicate (sheet key, revision) row; a page outside 1..n of its set; a revision basis that is
not PRINTED / FILE_PIN; a PRINTED basis with no printed revision; a FILE_PIN basis with a printed revision.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

NONE_PRINTED = "NONE_PRINTED"
NOT_READ = "NOT_READ"
BASES = ("PRINTED", "FILE_PIN")
VERDICTS = ("RESOLVED", "FILE_ONLY", "PART_ONLY", "PART_FILE_PAGE", "NOT_IN_REGISTER", "PART_MISMATCH",
            "MULTI_REVISION", "CONTENT_REVIEW")
ERROR_VERDICTS = ("NOT_IN_REGISTER", "PART_MISMATCH", "MULTI_REVISION")


@dataclass(frozen=True)
class Carrier:
    """A file that carries a sheet: Drive (or other store) title, its id, the page of the sheet inside that file."""
    file_title: str
    file_id: str
    page_in_file: int | None
    sha256: str | None = None          # None when the file could not be downloaded (identity by title + size only)
    bytes: int | None = None


@dataclass(frozen=True)
class Sheet:
    set_id: str                        # e.g. "ARCH", "ST", "SAN": one issued set = one page sequence
    page: int                          # page in the set, 1-based
    discipline: str
    drawing_title: str                 # as printed (caption or title-block title)
    scale: str                         # as printed, or NONE_PRINTED / NOT_READ
    number_printed: str                # sheet / drawing number as printed, or NONE_PRINTED
    revision_printed: str              # revision as printed, or NONE_PRINTED
    date_printed: str                  # title-block date as printed, or NONE_PRINTED / NOT_READ
    plot_stamp: str                    # plot date / layout as printed, or NONE_PRINTED
    revision_basis: str                # PRINTED or FILE_PIN
    carriers: tuple[Carrier, ...] = ()
    cad_frame: str = "NONE"            # the CAD exchange frame that holds the same drawing, or NONE
    keywords: tuple[str, ...] = ()     # title phrases that identify this sheet (lower case), for CONTENT_REVIEW:
                                       # sheet-type words only (an element such as a stair shows on many sheets)
    notes: str = ""

    @property
    def key(self) -> str:
        return f"{self.set_id}-{self.page:02d}"

    @property
    def revision_state(self) -> str:
        """What distinguishes one issue of this sheet from another: the printed revision, or the pinned files."""
        if self.revision_basis == "PRINTED":
            return f"REV {self.revision_printed}"
        pins = sorted({c.sha256 or f"{c.file_title}|{c.bytes}" for c in self.carriers})
        return "FILE_PIN " + ";".join(pins)


@dataclass
class Register:
    sheets: list[Sheet]
    set_sizes: dict[str, int]                       # pages per set
    files: dict[str, str] = field(default_factory=dict)   # cited file name (lower case) -> set id or "" (file only)

    def __post_init__(self):
        seen = set()
        for s in self.sheets:
            if s.revision_basis not in BASES:
                raise ValueError(f"{s.key}: revision basis {s.revision_basis!r} not in {BASES}")
            if s.revision_basis == "PRINTED" and s.revision_printed in (NONE_PRINTED, NOT_READ, ""):
                raise ValueError(f"{s.key}: PRINTED basis without a printed revision")
            if s.revision_basis == "FILE_PIN" and s.revision_printed not in (NONE_PRINTED, NOT_READ):
                raise ValueError(f"{s.key}: a printed revision {s.revision_printed!r} must use the PRINTED basis")
            n = self.set_sizes.get(s.set_id)
            if n is None or not 1 <= s.page <= n:
                raise ValueError(f"{s.key}: page outside 1..{n} of set {s.set_id}")
            k = (s.key, s.revision_state)
            if k in seen:
                raise ValueError(f"duplicate register row {k}")
            seen.add(k)

    def states(self, key: str) -> list[Sheet]:
        return [s for s in self.sheets if s.key == key]

    def keys(self) -> list[str]:
        return sorted({s.key for s in self.sheets})


@dataclass(frozen=True)
class CitationRule:
    """One citation form of the project's grammar.

    pattern: a regular expression; named groups: 'page' (page in the set or in the part), 'a' / 'b' (first / last page
    of a split part). kind: SHEET (page of a set), PART (split part, optional page), FILE (a whole file).
    target: the set id (SHEET / PART) or the file name (FILE). basis: a label kept in the output (how the citation
    names its sheet), e.g. FILE_TITLE, SET_PAGE, SHORTHAND.
    """
    pattern: str
    kind: str
    target: str
    basis: str
    flags: int = re.IGNORECASE


@dataclass(frozen=True)
class Citation:
    source: str
    line: int
    raw: str
    kind: str
    target: str
    basis: str
    sheet_key: str | None
    pages: tuple[int, ...]
    context: str


def find_citations(text: str, rules: Iterable[CitationRule], source: str = "", context_chars: int = 40) -> list[Citation]:
    """All citations in text, longest match first: a span already taken by an earlier (more specific) rule is skipped."""
    out: list[Citation] = []
    taken: list[tuple[int, int]] = []
    line_starts = [0] + [m.end() for m in re.finditer("\n", text)]

    def line_of(pos: int) -> int:
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    for rule in rules:
        for m in re.finditer(rule.pattern, text, rule.flags):
            a, b = m.span()
            if any(a < tb and ta < b for ta, tb in taken):
                continue
            taken.append((a, b))
            g = m.groupdict()
            page = int(g["page"]) if g.get("page") else None
            pages: tuple[int, ...] = ()
            key = None
            if rule.kind == "SHEET" and page is not None:
                pages, key = (page,), f"{rule.target}-{page:02d}"
            elif rule.kind == "PART":
                lo, hi = int(g["a"]), int(g["b"])
                if page is not None:
                    pages, key = (page,), f"{rule.target}-{page:02d}"
                else:
                    pages = tuple(range(lo, hi + 1))
            ctx = text[max(0, a - context_chars): b + context_chars].replace("\n", " ")
            out.append(Citation(source, line_of(a), m.group(0), rule.kind, rule.target, rule.basis, key, pages, ctx))
    out.sort(key=lambda c: (c.source, c.line, c.raw))
    return out


def _part_bounds(raw: str, rules: Iterable[CitationRule]) -> tuple[int, int] | None:
    for rule in rules:
        if rule.kind != "PART":
            continue
        m = re.search(rule.pattern, raw, rule.flags)
        if m and m.groupdict().get("a"):
            return int(m.group("a")), int(m.group("b"))
    return None


def check_citation(c: Citation, reg: Register, rules: Iterable[CitationRule] = ()) -> tuple[str, str, str | None]:
    """(verdict, reason, resolved sheet key or file name or None) for one citation."""
    if c.kind == "FILE":
        name = c.target.lower()
        if name not in reg.files:
            return "NOT_IN_REGISTER", f"file {c.target} is not in the register", None
        return "FILE_ONLY", f"whole file {c.target} (no page named)", c.target
    n = reg.set_sizes.get(c.target)
    if n is None:
        return "NOT_IN_REGISTER", f"set {c.target} is not in the register", None
    if c.kind == "PART":
        bounds = _part_bounds(c.raw, rules)
        if bounds and not 1 <= bounds[0] <= bounds[1] <= n:
            return "NOT_IN_REGISTER", f"part {bounds} outside 1..{n}", None
        if c.sheet_key is None:
            return ("PART_ONLY", f"part pages {c.pages[0]}..{c.pages[-1]} (no page named)",
                    f"{c.target} p.{c.pages[0]}-{c.pages[-1]}")
        if bounds and not bounds[0] <= c.pages[0] <= bounds[1]:
            in_file = c.pages[0]
            if 1 <= in_file <= bounds[1] - bounds[0] + 1:
                set_page = bounds[0] + in_file - 1
                key = f"{c.target}-{set_page:02d}"
                states = reg.states(key)
                if not states:
                    return "NOT_IN_REGISTER", f"{key} has no register row", None
                if len({x.revision_state for x in states}) > 1:
                    return "MULTI_REVISION", f"{key} (page {in_file} of the part file) exists in two or more revision " \
                                             f"states; cite which", key
                s = states[0]
                return "PART_FILE_PAGE", (f"page {in_file} of the part file {bounds[0]:02d}-{bounds[1]:02d} = set page "
                                          f"{set_page} = {key} '{s.drawing_title}' (page-in-file basis, not set page)"), key
            return "PART_MISMATCH", f"page {c.pages[0]} is not in part {bounds[0]:02d}-{bounds[1]:02d}", None
    page = c.pages[0] if c.pages else None
    if page is None or not 1 <= page <= n:
        return "NOT_IN_REGISTER", f"page {page} outside 1..{n} of set {c.target}", None
    states = reg.states(c.sheet_key)
    if not states:
        return "NOT_IN_REGISTER", f"{c.sheet_key} has no register row", None
    if len({s.revision_state for s in states}) > 1:
        revs = ", ".join(sorted(s.revision_state for s in states))
        return "MULTI_REVISION", f"{c.sheet_key} exists in {len(states)} revision states ({revs}); cite which", c.sheet_key
    s = states[0]
    if s.keywords:
        words = c.context.lower()
        own = any(k in words for k in s.keywords)
        others = sorted({k for o in reg.sheets if o.key != s.key for k in o.keywords
                         if k in words and k not in s.keywords})
        if others and not own:
            return "CONTENT_REVIEW", (f"context names {', '.join(others)} (other sheets), nothing of {s.key} "
                                      f"'{s.drawing_title}'"), s.key
    return "RESOLVED", f"{s.key} '{s.drawing_title}' ({s.revision_state.split(' ')[0]})", s.key


# A complete residential (villa) issued set, by what each sheet type prevents in a BOQ. Provenance: common
# consultant practice for permit / construction sets of private villas (engineering practice, not a regulation);
# 'basis' says which BOQ families depend on it. Matching is by the register's drawing titles (lower case words).
RESIDENTIAL_SET_CHECKLIST: tuple[tuple[str, str, tuple[str, ...], str], ...] = (
    ("ARCH", "site / plot layout with external works", ("site plan", "site layout", "external works"),
     "external floors, boundary wall, levels to road (excavation, backfill)"),
    ("ARCH", "floor plan per storey", ("floor plan",), "rooms, walls, finishes, openings"),
    ("ARCH", "roof plan (top roof: falls, drains, parapets, waterproofing)", ("roof plan",),
     "roof waterproofing, screed to falls, parapet finishes"),
    ("ARCH", "elevations (all faces)", ("elevation",), "facades, exterior plaster / paint, openings"),
    ("ARCH", "sections (at least two)", ("section",), "storey heights, levels, stair geometry"),
    ("ARCH", "door / window schedule", ("door schedule", "window schedule", "door and window", "openings schedule"),
     "opening heights and types (otherwise HELD / ASSUMED)"),
    ("ARCH", "finishes schedule or specification", ("finish", "finishing schedule", "specification"),
     "floor, wall, ceiling, exterior finish types; waterproofing system"),
    ("ARCH", "reflected ceiling plan", ("ceiling plan",), "false ceilings, gypsum, cornices"),
    ("ARCH", "wet-room / kitchen details", ("toilet detail", "bathroom detail", "kitchen detail", "wet area"),
     "wall tile heights, upturns, fixtures"),
    ("ARCH", "stair details (architectural)", ("stair detail", "staircase"), "stair finishes, railings"),
    ("ST", "foundation plan", ("foundation",), "footings, excavation"),
    ("ST", "column / axis plan", ("column",), "columns"),
    ("ST", "ground beam plan", ("ground beam",), "ground beams, straps"),
    ("ST", "slab plans per level", ("slab",), "slabs, beams"),
    ("ST", "schedules (columns, footings, beams)", ("schedule",), "bar populations (steel)"),
    ("ST", "typical details and notes", ("detail", "recommendation", "notes"), "covers, laps, lintels, parapets"),
    ("ST", "stair structural details", ("stair",), "stair concrete and steel"),
    ("MEP", "drainage / sanitary", ("drainage", "sanitary"), "wet-room scope, drainage"),
    ("MEP", "water supply", ("water supply", "plumbing"), "plumbing, tanks"),
    ("MEP", "electrical", ("electrical", "lighting", "power"), "electrical"),
    ("MEP", "air conditioning", ("air condition", "hvac", "a/c"), "ducts, soffits, false ceilings"),
)


def missing_sheets(reg: Register, set_discipline: dict[str, str]) -> list[dict]:
    """One row per checklist item: PRESENT (with the sheet keys) or NOT_IN_SET. set_discipline maps set id -> one of
    ARCH / ST / MEP so that, e.g., the structural set's 'stair' detail does not satisfy the architectural stair item."""
    rows = []
    for disc, item, words, basis in RESIDENTIAL_SET_CHECKLIST:
        hits = [s.key for s in reg.sheets if set_discipline.get(s.set_id) == disc
                and any(w in s.drawing_title.lower() for w in words)]
        rows.append({"discipline": disc, "item": item, "status": "PRESENT" if hits else "NOT_IN_SET",
                     "sheets": " ".join(sorted(set(hits))), "boq_families": basis})
    return rows


def date_consistency(reg: Register) -> list[dict]:
    """Within one set, sheets that print different title-block dates (or plot stamps): a set issued as one piece
    normally prints one date. A difference is an issue row (which date is the issue date?), not an error."""
    rows = []
    for set_id in sorted(reg.set_sizes):
        dates: dict[str, list[str]] = {}
        for s in reg.sheets:
            if s.set_id == set_id and s.date_printed not in (NONE_PRINTED, NOT_READ, ""):
                dates.setdefault(s.date_printed, []).append(s.key)
        if len(dates) > 1:
            rows.append({"set": set_id, "dates": {d: sorted(k) for d, k in sorted(dates.items())},
                         "issue": "DIFFERENT_TITLE_BLOCK_DATES_IN_ONE_SET"})
    return rows
