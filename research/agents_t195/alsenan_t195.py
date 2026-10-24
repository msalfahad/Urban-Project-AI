"""T-195: the development villa's document / revision register (phase 1) and the citation check over the merged
research ledgers. Builds REGISTER_T195.csv, DRIVE_FILES_T195.csv, CITATIONS_T195.csv, MISSING_T195.csv, summary.json.

Inputs:
  - the register data below: hand / vision reading of every title block and plot stamp on the Drive copies, read
    2026-10-22 by worker 2 (T-195). Only numbers, titles, scales, dates and revisions are recorded: the title blocks
    also carry the owner's name, plot data and the drafters' names, which are NOT recorded anywhere in this repository.
    Plot stamps carry a network path that contains the owner's name: only the layout name and the plot date / time are
    recorded. sha256 values are of the files as downloaded from Drive (all equal tests/alsenan/registers/SOURCE_MANIFEST
    where the manifest lists the file).
  - the merged research folders research/agents_t1* named in PINNED_FOLDERS (all of them were added on or after
    2026-10-20; list pinned at the working branch faa04202 so that later merges do not change this result).
  - T-243: the folder list alone did not pin the CONTENT: a later merge that edits a file inside a pinned folder
    (T-233 / T-234 appended rows to research/agents_t177/CHECKER_VERDICTS_DEV_VILLA.json) changed the scan. The
    scanned files are now pinned one by one in INPUTS_T195.csv (path, bytes, sha256, git blob id at PIN_COMMIT),
    written by `--write-inputs` from git, never by hand. A file whose current bytes still match its sha256 is read
    from the working tree; a file a later merge changed is read from its pinned git blob and its sha256 re-checked;
    if neither is possible the build stops (InputUnavailable): it never scans a different text silently. Files added
    after the pin (new files in a pinned folder, new folders) are not inputs of the snapshot; `--live` sees them.

Usage: python3 -I research/agents_t195/alsenan_t195.py [--check] [--live] [--write-inputs]
  --check         rebuild in memory and compare with the committed files (exit 1 on a difference)
  --live          scan every research/agents_t1* folder present now (not the pinned list) and print the error verdicts
  --write-inputs  (re)write INPUTS_T195.csv from the git tree of PIN_COMMIT
"""
from __future__ import annotations

import csv
import io
import json
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine.source.document_register_v1 import (  # noqa: E402
    NONE_PRINTED, NOT_READ, Carrier, CitationRule, Register, Sheet, check_citation, date_consistency,
    find_citations, missing_sheets, ERROR_VERDICTS)

FOLDER = "Drive 'Urban BOQ private data' / 'Alsenan chalet project'"

# ---- Drive files (search_files parentId = the project folder, 2026-10-22 23:42 UTC; 57 files, no subfolder) ------
# (title, id, bytes, kind, sha256 of the downloaded copy or None, what it carries)
ARCH_FULL = "المخطط المعماري p7757.pdf"
DRIVE_FILES = [
    ("P7757 dxf.dxf", "1fW7QqfjtcVATjD3rXJGcX_zAJm3Zj7nD", 17227946, "CAD_EXCHANGE", None,
     "architectural DXF (same bytes as the zip member below; not downloaded: over the connector limit)"),
    ("P7757_DXF_COMPRESSED.zip", "1aFn_W3RV23n3QtRyN-FILRY_CKE8Mj5c", 714410, "CAD_EXCHANGE_ZIP",
     "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4",
     "member P7757.dxf (sha256 given = the member; = SOURCE_MANIFEST P7757.dxf)"),
    ("P7757.dwg", "1vwm_jH416TOfojcYy08xN3j1J7k5_Wid", 2655476, "CAD_NATIVE", None,
     "architectural native DWG (bytes = SOURCE_MANIFEST P7757.dwg)"),
    ("المخطط المعماري - 2026-05-06T113026.059.dwf", "17PQEjZWEZ9vIeix1u7QsvzQMOw2yVtXo", 2655253, "DWF_PUBLISH", None,
     "architectural DWF publish (bytes = SOURCE_MANIFEST P7757_Architectural.dwf)"),
    (ARCH_FULL, "15FHjKyIhGIPO2aitDwLrgD9lk2K1EjnY", 37528314, "PDF_PLOT", None,
     "architectural set ARCH p.1-12 (not downloadable: 37.5 MB; identity by title + size only)"),
    (ARCH_FULL, "1Ceb5X65iLhQU6WpIU-ShgbWD-r4QXuS3", 37528314, "PDF_PLOT", None,
     "SECOND upload, same title and byte size: a duplicate copy (content identity not provable: not downloadable)"),
    ("Alsenan_Architectural_P7757_Pages_01-02.pdf", "1OKpxCbRqGzw_QJg7IGFJBAsA5g8yys8F", 6000352, "PDF_PART",
     "bb2363f2449dc4b0", "ARCH p.1-2"),
    ("Alsenan_Architectural_P7757_Pages_03-04.pdf", "1knf5fABkA4f7lVqDFGQygLBZOgAAN1pT", 6789743, "PDF_PART", None,
     "ARCH p.3-4 (over the connector limit: use p7757_arch_sheet03 / 04)"),
    ("Alsenan_Architectural_P7757_Pages_05-06.pdf", "1gS1g2fhvkzdGd1xXjS4RycqvkR4XoJmC", 6225932, "PDF_PART",
     "d6480919db67c810", "ARCH p.5-6"),
    ("Alsenan_Architectural_P7757_Pages_07-08.pdf", "19bPv9YGx5ArF_zi2TeAEde1jDscdwK0I", 6099455, "PDF_PART",
     "991dc783730ffa93", "ARCH p.7-8"),
    ("Alsenan_Architectural_P7757_Pages_09-10.pdf", "1790-8m9hq9dvM9mceFzEVaFThaSw_PdU", 6371489, "PDF_PART", None,
     "ARCH p.9-10 (over the connector limit: use p7757_arch_sheet09 / 10)"),
    ("Alsenan_Architectural_P7757_Pages_11-12.pdf", "1ToVFztO8uohZqlQsyc4JJHgGcVBUSbGq", 6116815, "PDF_PART",
     "9c72175ccfeb04f2", "ARCH p.11-12"),
    ("p7757_arch_sheet03.pdf", "1aJUU2B_l8O8hrMUJ6PFa4TK5KbFblLCj", 3375172, "PDF_SINGLE", "f12d7db79f650319",
     "ARCH p.3"),
    ("p7757_arch_sheet04.pdf", "1pdA1OJgBKQOb4tcY3qIbkiHDY6AuVg9H", 3415122, "PDF_SINGLE", "c712da4a333815cb",
     "ARCH p.4"),
    ("p7757_arch_sheet09.pdf", "1aXuWRH7Do0Yi8JBxfs0TOvWEKd_bpR2U", 3209545, "PDF_SINGLE", "ff539473477021c3",
     "ARCH p.9"),
    ("p7757_arch_sheet10.pdf", "1JN7vOJaijdC7IZfmbMURxeOkwcTn6euz", 3137565, "PDF_SINGLE", "e20fcf2c5d090d35",
     "ARCH p.10"),
    ("TEST_PAGE_01.pdf", "1fJOhZsVkt1NdwEIldbumknPM-TaJAt8x", 3104229, "PDF_SINGLE", "a61c2a4e9f0a5a32",
     "ARCH p.1 (rendered pixel-identical at 30 dpi to Pages_01-02 page 1: a test split, not another issue)"),
    ("ST7757 dxf.dxf", "1wmgfLZE2YD3oEBnwkQ6e6nT-aEWapPuL", 3153037, "CAD_EXCHANGE",
     "9f9d1179a5d2a663", "structural DXF, 12 model-space frames (= SOURCE_MANIFEST ST7757.dxf)"),
    ("ST7757.dwg", "1Jp4TjIJuWSsf1k49jigJ2pbs0PU8J4sD", 491151, "CAD_NATIVE", None,
     "structural native DWG (bytes = SOURCE_MANIFEST ST7757.dwg)"),
    ("ST7757.pdf", "1U9GMN2bkqlpbdL8Z9QJ3rlJyFYhhlox9", 2219156, "PDF_PLOT", "74da1523f05eb3c6",
     "structural set ST p.1-16 (= SOURCE_MANIFEST ST7757.pdf)"),
    ("sanitary-7757.pdf", "1hiEpFsXzy5G0OxA6vj0_p1LBISJnhIK3", 674366, "PDF_PLOT", "116736870983e63a",
     "sanitary (drainage) set SAN p.1-3 (= SOURCE_MANIFEST sanitary-7757.pdf)"),
    ("حصر خرسانة+الحديد (1).xlsx", "1OJaezzQX0CLKf0UVzZ69IY9AngoKoPKi", 49706, "WORKBOOK", None,
     "freelancer workbook (concrete + rebar): not a drawing"),
    ("الصبغ.xls", "1d9r1IgTJUHHa7_54GDzuPMcXP4Pzl_PR", 106496, "WORKBOOK", None, "freelancer workbook (paint)"),
    ("المساح الداخلى والسجما.xls", "1d_pTXrINhv1HRRRXAratna2sn_Q2uPIp", 117248, "WORKBOOK", None,
     "freelancer workbook (internal plaster + Sigma)"),
    ("الالومنيوم.xlsx", "1stCdLkIrPNhKOuristFCwxnktnEi4lq2", 6152749, "WORKBOOK", None,
     "freelancer workbook (aluminium)"),
    ("المبانى.xlsx", "11YtKkt22-Y7xd4C0RG3ildvDepGz50vU", 6164004, "WORKBOOK", None, "freelancer workbook (blockwork)"),
    ("الارضيات+العازل+الديكور+الرخام (1).xlsx", "1gMr2tCH8d2yoKNMZuLhUtB3YNpAAUm8P", 23654476, "WORKBOOK", None,
     "freelancer workbook (floors, insulation, decor, marble)"),
    ("Alsenan Chalet_by_category.xlsx", "1VQEb8W5Yr7-iThTZx2LB-3rdsmFer2QH", 12550, "WORKBOOK", None,
     "BOQ summary by category: not a drawing"),
    ("Alsenan Chalet_by_category.pdf", "18_6wgLHvCfWYy9k7qoK_CjJ2coY4LDL5", 119987, "REPORT", None,
     "BOQ summary by category: not a drawing"),
]
PHOTOS = (27, "PHOTO-2026-06-15-11-31-14.jpg", "PHOTO",
          "27 site / design images with one shared title, created 2026-10-21 22:50-22:52 (T-161): not drawings")


def _c(title, page, sha=None, size=None):
    fid = next(f[1] for f in DRIVE_FILES if f[0] == title)
    return Carrier(title, fid, page, sha, size)


def _arch_carriers(p):
    out = [Carrier(ARCH_FULL, "15FHjKyIhGIPO2aitDwLrgD9lk2K1EjnY", p, None, 37528314),
           Carrier(ARCH_FULL, "1Ceb5X65iLhQU6WpIU-ShgbWD-r4QXuS3", p, None, 37528314)]
    a = p if p % 2 else p - 1
    part = f"Alsenan_Architectural_P7757_Pages_{a:02d}-{a + 1:02d}.pdf"
    rec = next(f for f in DRIVE_FILES if f[0] == part)
    out.append(Carrier(part, rec[1], 1 if p == a else 2, rec[4], rec[2]))
    if p in (3, 4, 9, 10):
        out.append(_c(f"p7757_arch_sheet{p:02d}.pdf", 1, next(f[4] for f in DRIVE_FILES
                                                             if f[0] == f"p7757_arch_sheet{p:02d}.pdf")))
    if p == 1:
        out.append(_c("TEST_PAGE_01.pdf", 1, "a61c2a4e9f0a5a32"))
    return tuple(out)


ARCH_STAMP = "plot 2026-05-06 11:21, layout Model (P7757.dwg)"
# (page, title as printed, scale, plot stamp, cad frame, keywords)
ARCH = [
    (1, "GROUND FLOOR AREA PLAN + FIRST FLOOR AREA PLAN (area calculation tables)", "1:200", NONE_PRINTED, "NONE",
     ("area plan", "area calculation")),
    (2, "SECOND FLOOR AREA PLAN + TOTAL FLOORS AREA", "1:200", NONE_PRINTED, "NONE",
     ("area plan", "total floors area")),
    (3, "GROUND FLOOR PLAN", "1:100", ARCH_STAMP, "P7757.dxf SH05", ("ground floor plan", "gf plan")),
    (4, "1st FLOOR PLAN", "1:100", ARCH_STAMP, "P7757.dxf SH04", ("1st floor plan", "first floor plan", "1f plan")),
    (5, "2nd FLOOR PLAN", "1:100", ARCH_STAMP, "P7757.dxf SH03", ("2nd floor plan", "second floor plan", "2f plan")),
    (6, "SOUTH EAST ELEVATION", "1:100", NONE_PRINTED, "P7757.dxf SH02",
     ("south east", "se elevation", "se face", "south-east")),
    (7, "SOUTH WEST ELEVATION", "1:100", NONE_PRINTED, "NONE", ("south west", "sw elevation", "sw face", "south-west")),
    (8, "NORTH WEST ELEVATION", "1:100", NONE_PRINTED, "P7757.dxf SH01",
     ("north west", "nw elevation", "nw face", "north-west")),
    (9, "NORTH EAST ELEVATION", "1:100", NONE_PRINTED, "NONE", ("north east", "ne elevation", "ne face", "north-east")),
    (10, "SECTION A-A", "1:100", NONE_PRINTED, "NONE", ("section a-a", "a-a")),
    (11, "SECTION B-B", "1:100", NONE_PRINTED, "NONE", ("section b-b", "b-b")),
    (12, "FENCE PLAN + FENCE ELEVATION + FENCE SECTION", "1:100", NONE_PRINTED, "NONE",
     ("fence", "boundary wall")),
]
ST_PLAN_STAMP = "plot 2026-05-06 12:04"
# (page, title, scale, number printed, date printed, plot stamp, cad frame, keywords)
ST = [
    (1, "COLUMN & AXIS PLAN", "1/100", NONE_PRINTED, "May 06, 2025", ST_PLAN_STAMP + ", layout AXIS", "ST7757.dxf SH12",
     ("column & axis", "axis plan", "column plan")),
    (2, "FOUNDATION PLAN", "1/100", NONE_PRINTED, "May 06, 2025", ST_PLAN_STAMP, "ST7757.dxf SH10",
     ("foundation plan",)),
    (3, "GROUND BEAMS PLAN", "1/100", NONE_PRINTED, "May 06, 2025", ST_PLAN_STAMP, "ST7757.dxf SH08",
     ("ground beams plan", "ground beam plan")),
    (4, "GROUND FLOOR ROOF SLAB (+ sections A-A, C-C, D-D)", "1/100", NONE_PRINTED, "May 06, 2025", ST_PLAN_STAMP,
     "ST7757.dxf SH06", ("ground floor roof slab", "gf roof slab", "gf slab plan", "sections a-a", "c-c", "d-d")),
    (5, "FIRST FLOOR ROOF SLAB (+ section B-B)", "1/100", NONE_PRINTED, "May 06, 2025", ST_PLAN_STAMP,
     "ST7757.dxf SH04", ("first floor roof slab", "1f roof slab", "1f slab plan")),
    (6, "SECOND FLOOR ROOF SLAB", "1/100", NONE_PRINTED, "May 06, 2025", ST_PLAN_STAMP, "ST7757.dxf SH02",
     ("second floor roof slab", "2f roof slab", "2f slab plan")),
    (7, "DETAIL OF SWIMMING POOL + DETAIL OF DOME", "1/100 (details N.I.S)", NONE_PRINTED, "May 06, 2025",
     ST_PLAN_STAMP, "ST7757.dxf SH01", ("pool detail", "detail of swimming pool", "dome detail", "detail of dome")),
    (8, "RECOMMENDATIONS (general notes, raster image)", NOT_READ, NONE_PRINTED, NOT_READ, NONE_PRINTED, "NONE",
     ("note", "recommendation")),
    (9, "SCHEDULES: Schedule of Columns, Schedule of Footings", "N.T.S", NONE_PRINTED, "May 06, 2026",
     NONE_PRINTED, "ST7757.dxf SH11", ("schedule of columns", "schedule of footings", "column schedule",
                                       "footing schedule", "schedule")),
    (10, "SCHEDULES: Schedule of Simple Beams", "N.T.S", NONE_PRINTED, "May 06, 2026", NONE_PRINTED,
     "ST7757.dxf SH09", ("simple beam", "schedule")),
    (11, "SCHEDULE OF CONTINUES BEAMS (2 SPAN) x2", NONE_PRINTED, "Ref. S-2", NONE_PRINTED,
     "plot 2026-05-06 12:04, layout CONTINUOUS BEAMS1 (file named T7757.dwg)", "ST7757.dxf SH03 + SH05",
     ("continuous beam", "continues beam", "2 span", "two-span", "schedule")),
    (12, "SCHEDULE OF CONTINUES BEAMS (THREE SPAN)", NONE_PRINTED, "Ref. S-3", NONE_PRINTED,
     "plot 2026-05-06 12:04, layout CONTINUOUS BEAMS2 (file named T7757.dwg)", "ST7757.dxf SH07",
     ("three span", "3 span", "continuous beam", "continues beam", "schedule")),
    (13, "DETAILS: typical (footing, lintel, ground beams for exterior walls)", "AS SHOWN", NONE_PRINTED,
     "May 06, 2026", "plot 2026-05-06 12:04, layout DETAILS (4)", "NONE (paper space not in the DXF)",
     ("lintel", "exterior walls", "typical footing", "typical detail")),
    (14, "DETAILS: typical (parapet section, lift pit, boundary wall)", "AS SHOWN", NONE_PRINTED, "May 06, 2026",
     "plot 2026-05-06 12:04, layout DETAILS (4)", "NONE (paper space not in the DXF)",
     ("parapet section", "parapet detail", "lift pit", "boundary wall", "typical detail")),
    (15, "DETAILS: typical (twisted columns, slab on beams, beam carrying planted column)", "AS SHOWN",
     NONE_PRINTED, "May 06, 2026", "plot 2026-05-06 12:04, layout DETAILS (4)", "NONE (paper space not in the DXF)",
     ("twisted", "planted", "slab on beams", "typical detail")),
    (16, "DETAILS: typical (stair beam, stair steel layout / section, opening in beam, ribs)", "AS SHOWN",
     NONE_PRINTED, "May 06, 2026", "plot 2026-05-06 12:04, layout DETAILS (4)", "NONE (paper space not in the DXF)",
     ("stair detail", "stair section", "stair beam", "typical detail")),
]
SAN = [
    (1, "GROUND FLOOR DRAINAGE PLAN", ("ground floor drainage", "gf drainage")),
    (2, "FIRST FLOOR DRAINAGE PLAN", ("first floor drainage", "1f drainage")),
    (3, "2nd FLOOR DRAINAGE PLAN", ("2nd floor drainage", "second floor drainage", "2f drainage")),
]
ST_SHA = "74da1523f05eb3c6"
SAN_SHA = "116736870983e63a"


def build_register() -> Register:
    sheets = []
    for p, title, scale, stamp, frame, kw in ARCH:
        sheets.append(Sheet("ARCH", p, "ARCHITECTURAL", title, scale, NONE_PRINTED, NONE_PRINTED, NONE_PRINTED,
                            stamp, "FILE_PIN", _arch_carriers(p), frame, kw,
                            "title block prints only the owner box (owner name, plot / block numbers, area): no "
                            "sheet number, no revision, no date, no drawing title; title read from the drawing caption"))
    for p, title, scale, num, date, stamp, frame, kw in ST:
        sheets.append(Sheet("ST", p, "STRUCTURAL", title, scale, num, NONE_PRINTED, date, stamp, "FILE_PIN",
                            (_c("ST7757.pdf", p, ST_SHA, 2219156),), frame, kw,
                            "title block fields SCALE / DATE / FILE NO 'ST - 7757' (no sheet number, no revision field)"
                            if p not in (8, 11, 12) else
                            ("raster page; different title-block layout (designer / drawer / checker / client "
                             "fields): date not read" if p == 8 else
                             "no title block: schedule frame with 'Ref.' box and an embedded plot line")))
    for p, title, kw in SAN:
        sheets.append(Sheet("SAN", p, "SANITARY", title, "1/100", NONE_PRINTED, NONE_PRINTED, NONE_PRINTED,
                            NONE_PRINTED, "FILE_PIN", (_c("sanitary-7757.pdf", p, SAN_SHA, 674366),), "NONE", kw,
                            "title block fields SCALE 1/100 / FILE NO 'SS-7757' / drawn by (no date, no revision)"))
    files = {f.lower(): s for f, s in (("p7757.dxf", ""), ("p7757 dxf.dxf", ""), ("p7757.dwg", ""),
                                        ("p7757.dwf", ""), ("st7757.dxf", ""), ("st7757 dxf.dxf", ""),
                                        ("st7757.dwg", ""), ("st7757.pdf", "ST"), ("sanitary-7757.pdf", "SAN"),
                                        ("test_page_01.pdf", "ARCH"))}
    return Register(sheets, {"ARCH": 12, "ST": 16, "SAN": 3}, files)


# ---- the project's citation grammar (most specific first) ---------------------------------------------------------
PAGE = r",?\s*(?:p\.?|page|pp\.?)\s?(?P<page>\d{1,2})\b"
RULES = [
    CitationRule(r"\bp7757_arch_sheet(?P<page>\d{2})(?:\.pdf)?", "SHEET", "ARCH", "FILE_TITLE"),
    CitationRule(r"\b(?:Alsenan_Architectural_P7757_)?Pages_(?P<a>\d{2})-(?P<b>\d{2})(?:\.pdf)?" + PAGE, "PART",
                 "ARCH", "PART_PAGE"),
    CitationRule(r"\b(?:Alsenan_Architectural_P7757_)?Pages_(?P<a>\d{2})-(?P<b>\d{2})(?:\.pdf)?", "PART", "ARCH",
                 "PART"),
    CitationRule(r"\bsanitary[-_ ]?7757(?:\.pdf)?,?\s*(?:p\.?|page|sheet)\s?(?P<page>\d{1,2})\b", "SHEET", "SAN",
                 "SET_PAGE"),
    CitationRule(r"\bST(?:\s?7757)?(?:\.pdf)?" + PAGE, "SHEET", "ST", "SET_PAGE"),
    # 'sheet NN' (two digits) is the team's shorthand for the architectural set page NN (= the p7757_arch_sheetNN
    # file titles). Not a citation when it is arithmetic or a size: 'sheet 12 + 11' (a step count, T-111) or
    # 'off-sheet 80 x 50' (a block size, T-138).
    CitationRule(r"(?<![-\w])sheet\s?(?P<page>\d{2})\b(?!\s*[x×+])", "SHEET", "ARCH", "SHORTHAND"),
    CitationRule(r"\bP7757 ?(?:dxf)?\.dxf\b", "FILE", "p7757.dxf", "FILE"),
    CitationRule(r"\bP7757\.dwg\b", "FILE", "p7757.dwg", "FILE"),
    CitationRule(r"\bP7757(?:_Architectural)?\.dwf\b", "FILE", "p7757.dwf", "FILE"),
    CitationRule(r"\bST7757 ?(?:dxf)?\.dxf\b", "FILE", "st7757.dxf", "FILE"),
    CitationRule(r"\bST7757\.dwg\b", "FILE", "st7757.dwg", "FILE"),
    CitationRule(r"\bST7757\.pdf\b", "FILE", "st7757.pdf", "FILE"),
    CitationRule(r"\bsanitary[-_ ]?7757\.pdf\b", "FILE", "sanitary-7757.pdf", "FILE"),
]

PINNED_FOLDERS = [
    "agents_t100", "agents_t102", "agents_t103", "agents_t104", "agents_t105", "agents_t106", "agents_t107",
    "agents_t109", "agents_t110", "agents_t111", "agents_t112", "agents_t113", "agents_t114", "agents_t116",
    "agents_t117", "agents_t119", "agents_t120", "agents_t122", "agents_t123", "agents_t124", "agents_t125",
    "agents_t126", "agents_t127", "agents_t128", "agents_t129", "agents_t130", "agents_t131", "agents_t133",
    "agents_t134", "agents_t135", "agents_t136", "agents_t137", "agents_t138", "agents_t139", "agents_t140",
    "agents_t141", "agents_t142", "agents_t143", "agents_t144", "agents_t145", "agents_t147", "agents_t148",
    "agents_t149", "agents_t150", "agents_t151", "agents_t152", "agents_t153", "agents_t154", "agents_t155",
    "agents_t157", "agents_t159", "agents_t160", "agents_t161", "agents_t162", "agents_t164", "agents_t165",
    "agents_t166", "agents_t167", "agents_t169", "agents_t171", "agents_t172", "agents_t173", "agents_t175",
    "agents_t177", "agents_t178", "agents_t181", "agents_t182", "agents_t183", "agents_t184", "agents_t185",
    "agents_t186", "agents_t189",
]
EXTS = (".md", ".csv", ".json", ".txt")
PIN_COMMIT = "faa04202"          # research/ at faa04202 = research/ at the T-195 commit 22397715 (no research change)
INPUTS = "INPUTS_T195.csv"
INPUT_COLS = ["path", "bytes", "sha256", "git_blob"]


class InputUnavailable(RuntimeError):
    """A pinned input changed after the pin and its pinned bytes cannot be read back (no git object, sha mismatch)."""


def _git(*args, cwd=ROOT) -> bytes:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True).stdout


def write_inputs(commit=PIN_COMMIT, folders=PINNED_FOLDERS):
    """The pinned input list, in the scan order of `scan` (folder order, then sorted path), from the git tree."""
    rows = []
    for d in folders:
        listing = _git("ls-tree", "-r", commit, "--", f"research/{d}/").decode("utf-8").splitlines()
        entries = []
        for ln in listing:
            meta, path = ln.split("\t", 1)
            mode, kind, blob = meta.split()
            if kind == "blob" and Path(path).suffix.lower() in EXTS:
                entries.append((Path(path), blob))
        for path, blob in sorted(entries):
            data = _git("cat-file", "blob", blob)
            rows.append({"path": path.as_posix(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                         "git_blob": blob})
    return _csv(rows, INPUT_COLS)


def pinned_inputs(root=ROOT, manifest=None):
    """[(path, text, origin)] of the pinned inputs; origin WORKTREE or GIT_BLOB (a later merge changed the file)."""
    manifest = HERE / INPUTS if manifest is None else manifest
    out = []
    for r in csv.DictReader(io.StringIO(Path(manifest).read_text(encoding="utf-8"))):
        f = Path(root) / r["path"]
        data = f.read_bytes() if f.is_file() else None
        origin = "WORKTREE"
        if data is None or hashlib.sha256(data).hexdigest() != r["sha256"]:
            origin = "GIT_BLOB"
            try:
                data = _git("cat-file", "blob", r["git_blob"])
            except (OSError, subprocess.CalledProcessError) as e:
                raise InputUnavailable(f"{r['path']}: changed after the pin and git blob {r['git_blob']} not "
                                       f"readable ({e.__class__.__name__})") from None
            if hashlib.sha256(data).hexdigest() != r["sha256"]:
                raise InputUnavailable(f"{r['path']}: git blob {r['git_blob']} does not match the pinned sha256")
        text = data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")  # = read_text
        out.append((r["path"], text, origin))
    return out


def _scan_texts(texts, reg):
    rows = []
    for rel, text in texts:
        for c in find_citations(text, RULES, rel):
            v, why, key = check_citation(c, reg, RULES)
            rows.append({"source": rel, "line": c.line, "citation": c.raw.strip(), "basis": c.basis,
                         "resolves_to": key or "", "verdict": v, "reason": why})
    return rows


def scan(folders, reg):
    """Live scan of the folders as they are now (used by --live)."""
    texts = []
    for d in folders:
        base = ROOT / "research" / d
        if not base.is_dir():
            continue
        for f in sorted(base.rglob("*")):
            if f.suffix.lower() not in EXTS or not f.is_file():
                continue
            texts.append((f.relative_to(ROOT).as_posix(), f.read_text(encoding="utf-8", errors="replace")))
    return _scan_texts(texts, reg)


def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in cols})
    return buf.getvalue()


def build(folders=PINNED_FOLDERS, root=None):
    """folders = PINNED_FOLDERS: the committed snapshot, from the pinned inputs (INPUTS_T195.csv) under `root`
    (default the repository); any other list: a live scan (--live)."""
    reg = build_register()
    sheet_rows = [{
        "sheet_key": s.key, "discipline": s.discipline, "drawing_title": s.drawing_title, "scale": s.scale,
        "number_printed": s.number_printed, "revision_printed": s.revision_printed, "date_printed": s.date_printed,
        "plot_stamp": s.plot_stamp, "revision_basis": s.revision_basis,
        "carriers": " | ".join(f"{c.file_title} p.{c.page_in_file}" + (f" sha {c.sha256[:16]}" if c.sha256 else
                                                                        f" ({c.bytes} B, not downloaded)")
                               for c in s.carriers),
        "cad_frame": s.cad_frame, "notes": s.notes} for s in reg.sheets]
    file_rows = [{"drive_title": t, "drive_id": i, "bytes": b, "kind": k, "sha256": h or "NOT DOWNLOADED",
                  "carries": what} for t, i, b, k, h, what in DRIVE_FILES]
    file_rows.append({"drive_title": PHOTOS[1], "drive_id": f"{PHOTOS[0]} files (ids: T-161)", "bytes": "",
                      "kind": PHOTOS[2], "sha256": "", "carries": PHOTOS[3]})
    if folders is PINNED_FOLDERS:
        cites = _scan_texts([(p, t) for p, t, _ in pinned_inputs(ROOT if root is None else root)], reg)
    else:
        cites = scan(folders, reg)
    missing = missing_sheets(reg, {"ARCH": "ARCH", "ST": "ST", "SAN": "MEP"})
    dates = date_consistency(reg)
    counts = {}
    for r in cites:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    summary = {
        "task": "T-195", "drive_folder": FOLDER, "drive_files": len(DRIVE_FILES) + PHOTOS[0],
        "drawing_files": sum(1 for f in DRIVE_FILES if f[3] not in ("WORKBOOK", "REPORT")),
        "sheets": {k: n for k, n in reg.set_sizes.items()}, "sheets_total": len(reg.sheets),
        "revision_printed_on_any_sheet": any(s.revision_basis == "PRINTED" for s in reg.sheets),
        "date_conflicts": dates, "folders_scanned": len(folders), "citations": len(cites),
        "verdicts": dict(sorted(counts.items())),
        "missing_from_set": [m["item"] for m in missing if m["status"] == "NOT_IN_SET"],
    }
    out = {
        "REGISTER_T195.csv": _csv(sheet_rows, list(sheet_rows[0])),
        "DRIVE_FILES_T195.csv": _csv(file_rows, list(file_rows[0])),
        "CITATIONS_T195.csv": _csv(cites, ["source", "line", "citation", "basis", "resolves_to", "verdict",
                                           "reason"]),
        "MISSING_T195.csv": _csv(missing, ["discipline", "item", "status", "sheets", "boq_families"]),
        "summary.json": json.dumps(summary, ensure_ascii=False, indent=1) + "\n",
    }
    return out, cites


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--live" in argv:
        folders = sorted(p.name for p in (ROOT / "research").glob("agents_t1*") if p.is_dir() and p.name != "agents_t195")
        _, cites = build(folders)
        bad = [c for c in cites if c["verdict"] in ERROR_VERDICTS]
        for c in bad:
            print(f"{c['verdict']}: {c['source']}:{c['line']} {c['citation']!r} {c['reason']}")
        print(f"{len(folders)} folders, {len(cites)} citations, {len(bad)} error verdicts")
        return 0
    if "--write-inputs" in argv:
        (HERE / INPUTS).write_text(write_inputs(), encoding="utf-8")
        print(f"{INPUTS} written from {PIN_COMMIT}")
        return 0
    try:
        out, _ = build()
    except InputUnavailable as e:
        print(f"differs: pinned input unavailable: {e}")
        return 1
    if "--check" in argv:
        diff = [n for n, t in out.items() if not (HERE / n).is_file() or (HERE / n).read_text(encoding="utf-8") != t]
        drift = [p for p, _, o in pinned_inputs() if o == "GIT_BLOB"]
        print("differs: " + (", ".join(diff) if diff else "none"))
        print(f"pinned inputs changed after {PIN_COMMIT} (read from their pinned git blobs): {len(drift)}"
              + ("".join(f"\n  {p}" for p in drift)))
        return 1 if diff else 0
    for n, t in out.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print(json.dumps(json.loads(out["summary.json"]), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
