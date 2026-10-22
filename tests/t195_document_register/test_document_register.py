"""T-195: DOCUMENT_REGISTER_V1 on a hand-built register of a non-Alsenan villa (V-195), with adverse cases:
a sheet issued in two revisions, a set that prints no revision, a citation on the wrong part, a page-in-file citation,
a page outside the set, an unknown file, shorthand that is arithmetic, mixed title-block dates, missing sheets."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source.document_register_v1 import (  # noqa: E402
    NONE_PRINTED, Carrier, CitationRule, Register, Sheet, check_citation, date_consistency, find_citations,
    missing_sheets)

# Villa V-195 (invented): architectural set A (8 pages) printed with revision letters; structural set S (4 pages)
# with no printed revision (pinned by file hash). A-03 was reissued: rev A (first issue) and rev B (plan change).
A_FILE_A = Carrier("V195_ARCH_revA.pdf", "idA", None, "aaaa", 100)
A_FILE_B = Carrier("V195_ARCH_revB.pdf", "idB", None, "bbbb", 101)
S_FILE = Carrier("V195_ST.pdf", "idS", None, "ssss", 50)


def _a(page, title, rev="A", date="2026-01-10", carrier=A_FILE_A, kw=()):
    return Sheet("A", page, "ARCHITECTURAL", title, "1:100", f"A-{page:02d}", rev, date, NONE_PRINTED, "PRINTED",
                 (Carrier(carrier.file_title, carrier.file_id, page, carrier.sha256, carrier.bytes),), "NONE", kw)


def _s(page, title, date="2026-01-12", kw=()):
    return Sheet("S", page, "STRUCTURAL", title, "1:100", NONE_PRINTED, NONE_PRINTED, date, NONE_PRINTED,
                 "FILE_PIN", (Carrier(S_FILE.file_title, S_FILE.file_id, page, S_FILE.sha256, S_FILE.bytes),),
                 "NONE", kw)


def villa():
    sheets = [
        _a(1, "SITE PLAN", kw=("site plan",)),
        _a(2, "GROUND FLOOR PLAN", kw=("ground floor plan",)),
        _a(3, "FIRST FLOOR PLAN", kw=("first floor plan",)),
        _a(3, "FIRST FLOOR PLAN", rev="B", date="2026-03-02", carrier=A_FILE_B, kw=("first floor plan",)),
        _a(4, "ROOF PLAN", kw=("roof plan",)),
        _a(5, "FRONT ELEVATION", kw=("front elevation",)),
        _a(6, "REAR ELEVATION", kw=("rear elevation",)),
        _a(7, "SECTION A-A", kw=("section a-a",)),
        _a(8, "DOOR AND WINDOW SCHEDULE", kw=("door schedule", "window schedule")),
        _s(1, "FOUNDATION PLAN", kw=("foundation plan",)),
        _s(2, "GROUND FLOOR SLAB", kw=("gf slab",)),
        _s(3, "SCHEDULE OF COLUMNS", date="2026-02-20", kw=("column schedule",)),
        _s(4, "STAIR DETAIL", kw=("stair detail",)),
    ]
    return Register(sheets, {"A": 8, "S": 4}, {"v195_st.pdf": "S", "v195.dxf": ""})


RULES = [
    CitationRule(r"\bV195_ARCH_(?P<a>\d{2})-(?P<b>\d{2})(?:\.pdf)?,?\s*p\.?\s?(?P<page>\d{1,2})\b", "PART", "A",
                 "PART_PAGE"),
    CitationRule(r"\bV195_ARCH_(?P<a>\d{2})-(?P<b>\d{2})(?:\.pdf)?", "PART", "A", "PART"),
    CitationRule(r"\bV195_ST(?:\.pdf)?\s+p\.?\s?(?P<page>\d{1,2})\b", "SHEET", "S", "SET_PAGE"),
    CitationRule(r"(?<![-\w])sheet\s?(?P<page>\d{2})\b(?!\s*[x×+])", "SHEET", "A", "SHORTHAND"),
    CitationRule(r"\bV195\.dxf\b", "FILE", "v195.dxf", "FILE"),
    CitationRule(r"\bV195_MEP\.pdf\b", "FILE", "v195_mep.pdf", "FILE"),
]


def verdicts(text, reg=None):
    reg = reg or villa()
    return [(c.raw, *check_citation(c, reg, RULES)) for c in find_citations(text, RULES, "t")]


def test_normal_citations_resolve():
    out = verdicts("ground floor plan sheet 02; foundation plan V195_ST p.1; geometry from V195.dxf")
    got = {r: (v, k) for r, v, _, k in out}
    assert got["sheet 02"] == ("RESOLVED", "A-02")
    assert got["V195_ST p.1"] == ("RESOLVED", "S-01")
    assert got["V195.dxf"] == ("FILE_ONLY", "v195.dxf")


def test_two_revisions_of_one_sheet_flagged_even_when_right():
    # adverse: the citation names the sheet but not which issue; rev A and rev B both exist
    (raw, v, why, key), = verdicts("first floor plan sheet 03")
    assert v == "MULTI_REVISION" and key == "A-03"
    assert "REV A" in why and "REV B" in why


def test_page_outside_set_and_unknown_file():
    out = {r: v for r, v, _, _ in verdicts("sheet 09 ... V195_ST p.7 ... V195_MEP.pdf")}
    assert out == {"sheet 09": "NOT_IN_REGISTER", "V195_ST p.7": "NOT_IN_REGISTER",
                   "V195_MEP.pdf": "NOT_IN_REGISTER"}


def test_part_page_bases():
    out = {r: (v, k) for r, v, _, k in verdicts(
        "V195_ARCH_05-06 p.5 elevation; V195_ARCH_05-06 p.2 rear; V195_ARCH_05-06 p.4; V195_ARCH_07-08 front")}
    assert out["V195_ARCH_05-06 p.5"] == ("RESOLVED", "A-05")                 # set-page basis
    assert out["V195_ARCH_05-06 p.2"] == ("PART_FILE_PAGE", "A-06")           # page 2 of the part file = set page 6
    assert out["V195_ARCH_05-06 p.4"] == ("PART_MISMATCH", None)              # neither basis fits
    assert out["V195_ARCH_07-08"] == ("PART_ONLY", "A p.7-8")


def test_part_outside_set():
    (raw, v, _, _), = verdicts("V195_ARCH_09-10 p.9")
    assert v == "NOT_IN_REGISTER"


def test_shorthand_arithmetic_and_sizes_are_not_citations():
    # adverse: 'sheet 12 + 11' is a step count, 'off-sheet 80 x 50' a block size: neither cites a sheet
    assert verdicts("structural roof sheet 12 + 11 + landing; an off-sheet 80 x 50 insert; sheet 05 x 3") == []


def test_content_review_is_a_hint_only():
    out = {r: v for r, v, _, _ in verdicts("sheet 05 rear elevation") + verdicts("sheet 05 front elevation")}
    assert out["sheet 05"] in ("RESOLVED", "CONTENT_REVIEW")
    (_, v, why, key), = verdicts("parapet on the rear elevation, sheet 05")
    assert v == "CONTENT_REVIEW" and key == "A-05" and "rear elevation" in why
    (_, v, _, _), = verdicts("sheet 05 (front elevation, compare rear elevation)")
    assert v == "RESOLVED"                                                     # its own title is named


def test_file_pin_revision_state_and_printed_basis():
    reg = villa()
    s = reg.states("S-02")[0]
    assert s.revision_state == "FILE_PIN ssss"
    assert {x.revision_state for x in reg.states("A-03")} == {"REV A", "REV B"}


def test_date_consistency_flags_mixed_dates():
    rows = date_consistency(villa())
    sets = {r["set"]: r for r in rows}
    assert "S" in sets and sets["S"]["dates"]["2026-02-20"] == ["S-03"]
    assert "A" in sets                                                         # rev B carries a later date


def test_missing_sheets():
    rows = {r["item"]: r for r in missing_sheets(villa(), {"A": "ARCH", "S": "ST"})}
    assert rows["door / window schedule"]["status"] == "PRESENT"
    assert rows["roof plan (top roof: falls, drains, parapets, waterproofing)"]["sheets"] == "A-04"
    assert rows["finishes schedule or specification"]["status"] == "NOT_IN_SET"
    assert rows["drainage / sanitary"]["status"] == "NOT_IN_SET"              # no MEP set issued
    # the structural stair detail does not satisfy the architectural stair item
    assert rows["stair details (architectural)"]["status"] == "NOT_IN_SET"
    assert rows["stair structural details"]["sheets"] == "S-04"


def test_line_numbers_and_longest_rule_first():
    cs = find_citations("x\nV195_ARCH_05-06 p.5\n", RULES, "f")
    assert [(c.line, c.basis) for c in cs] == [(2, "PART_PAGE")]               # not also matched as a bare PART


@pytest.mark.parametrize("bad", [
    dict(revision_basis="REV"),                                                # unknown basis
    dict(revision_basis="PRINTED", revision_printed=NONE_PRINTED),             # printed basis, nothing printed
    dict(revision_basis="FILE_PIN", revision_printed="C"),                     # printed revision on a file pin
    dict(page=5),                                                              # outside 1..4
])
def test_guards(bad):
    base = dict(set_id="S", page=1, discipline="STRUCTURAL", drawing_title="X", scale="1:100",
                number_printed=NONE_PRINTED, revision_printed=NONE_PRINTED, date_printed=NONE_PRINTED,
                plot_stamp=NONE_PRINTED, revision_basis="FILE_PIN", carriers=(S_FILE,))
    base.update(bad)
    with pytest.raises(ValueError):
        Register([Sheet(**base)], {"S": 4})


def test_duplicate_row_refused():
    s = _s(1, "FOUNDATION PLAN")
    with pytest.raises(ValueError):
        Register([s, s], {"S": 4})


def test_mm_and_case_variants_do_not_change_resolution():
    # the grammar is case-insensitive; a page written with a leading zero resolves the same
    out = {r: k for r, _, _, k in verdicts("SHEET 02 and v195_st P.01")}
    assert out == {"SHEET 02": "A-02", "v195_st P.01": "S-01"}
