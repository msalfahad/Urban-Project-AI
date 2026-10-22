"""T-195: the development villa's committed register reproduces from repository files, and its invariants hold:
every Drive drawing page is a register row; no revision is invented (no sheet prints one: all FILE_PIN); the
structural set's two title-block dates are reported; the pinned merged ledgers cite only sheets that exist."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t195"))
sys.path.insert(0, str(ROOT))

import alsenan_t195 as A                                        # noqa: E402

HERE = ROOT / "research" / "agents_t195"


def _rows(name):
    return list(csv.DictReader(open(HERE / name, encoding="utf-8")))


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_every_page_is_a_row_and_no_revision_invented():
    rows = _rows("REGISTER_T195.csv")
    keys = [r["sheet_key"] for r in rows]
    assert keys == [f"ARCH-{p:02d}" for p in range(1, 13)] + [f"ST-{p:02d}" for p in range(1, 17)] + \
        [f"SAN-{p:02d}" for p in range(1, 4)]
    assert {r["revision_printed"] for r in rows} == {"NONE_PRINTED"}
    assert {r["revision_basis"] for r in rows} == {"FILE_PIN"}
    # the single-sheet files and the split parts are carriers of the same pages, not other issues
    arch03 = next(r for r in rows if r["sheet_key"] == "ARCH-03")["carriers"]
    assert "p7757_arch_sheet03.pdf p.1" in arch03 and "Pages_03-04.pdf p.1" in arch03


def test_structural_date_conflict_reported():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    (d,) = s["date_conflicts"]
    assert d["set"] == "ST" and set(d["dates"]) == {"May 06, 2025", "May 06, 2026"}
    assert d["dates"]["May 06, 2025"] == [f"ST-0{p}" for p in range(1, 8)]


def test_pinned_ledgers_cite_only_registered_sheets():
    rows = _rows("CITATIONS_T195.csv")
    assert rows, "no citation found"
    bad = [r for r in rows if r["verdict"] in ("NOT_IN_REGISTER", "PART_MISMATCH", "MULTI_REVISION")]
    assert bad == []
    mixed = [r for r in rows if r["verdict"] == "PART_FILE_PAGE"]
    assert len(mixed) == 5 and {r["resolves_to"] for r in mixed} == {"ARCH-05", "ARCH-06", "ARCH-07"}


def test_every_drawing_file_on_drive_is_listed():
    titles = {r["drive_title"] for r in _rows("DRIVE_FILES_T195.csv")}
    for t in ("P7757.dwg", "P7757 dxf.dxf", "P7757_DXF_COMPRESSED.zip", "ST7757 dxf.dxf", "ST7757.dwg", "ST7757.pdf",
              "sanitary-7757.pdf", "TEST_PAGE_01.pdf", "p7757_arch_sheet03.pdf", "p7757_arch_sheet10.pdf",
              "Alsenan_Architectural_P7757_Pages_11-12.pdf"):
        assert t in titles
