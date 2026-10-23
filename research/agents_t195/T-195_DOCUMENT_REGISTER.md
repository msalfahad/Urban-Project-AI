# T-195: document / revision register, phase 1 (residential review R9; development villa; every villa)

Worker 2, 2026-10-22. Research + one unwired check module + tests. No engine method, rule file or quantity changes;
nothing is released. Development villa: not an accuracy claim. No client name, consultant name, drafter name, plot
number, network path or personal data is recorded: the title blocks carry them; only numbers, titles, scales, dates,
revisions and plot date / layout are kept.

## 1. What was built

- `engine/source/document_register_v1.py` (DOCUMENT_REGISTER_V1, imported by nothing): `Sheet` / `Carrier` / `Register`
  (one row per printed sheet; revision basis PRINTED or FILE_PIN, never an assumed "rev 0"), `find_citations` +
  `check_citation` (a project-supplied citation grammar; verdicts RESOLVED, FILE_ONLY, PART_ONLY, PART_FILE_PAGE,
  NOT_IN_REGISTER, PART_MISMATCH, MULTI_REVISION, CONTENT_REVIEW), `missing_sheets` (checklist of a complete villa set:
  engineering practice, NOT a Kuwait regulation) and `date_consistency` (one set printing two dates).
- `research/agents_t195/alsenan_t195.py` builds, from the hand / vision reading recorded in it:
  REGISTER_T195.csv (31 sheets), DRIVE_FILES_T195.csv (every file in the Drive folder), CITATIONS_T195.csv (543
  citations), MISSING_T195.csv, summary.json. `--check` reproduces them; `--live` scans the research folders present now.
- `tests/t195_document_register/` (22 tests): a non-Alsenan villa V-195 with a sheet issued in two revisions (adverse),
  a set with no printed revision, part / page-in-file / wrong-part citations, a page outside the set, an unknown file,
  shorthand that is arithmetic ('sheet 12 + 11') or a size ('off-sheet 80 x 50'), mixed dates, missing sheets, guards;
  plus the committed Alsenan register reproduces and its invariants hold.

## 2. The register (Drive "Urban BOQ private data" / "Alsenan chalet project", listed 2026-10-22 23:42 UTC)

56 files: 21 drawing files (CAD, PDF sets, parts, single sheets, the zip), 8 workbooks / reports, 27 photos (T-161).
Three issued sets, 31 sheets:

| Set | Pages | Title block prints | Revision | Date printed | Plot stamp | CAD exchange frame |
|---|---|---|---|---|---|---|
| ARCH (architectural, raster PDF) | 12: area plans GF+1F (1:200), 2F + total, GF / 1F / 2F plans, SE / SW / NW / NE elevations, sections A-A / B-B, fence | owner box only (name, plot, area): no sheet number, no date, no title | NONE PRINTED | NONE | p.3-5 only: 2026-05-06 11:21, layout Model | P7757.dxf has 5 frames: GF, 1F, 2F plans + NW, SE elevations. SW, NE, both sections, fence and area plans are PDF-only |
| ST (structural, vector PDF) | 16: column & axis, foundation, ground beams, GF / 1F / 2F roof slabs, pool + dome, recommendations (raster), schedules x4, typical details x4 | SCALE / DATE / FILE NO 'ST - 7757'; no sheet number, no revision field | NONE PRINTED | p.1-7 'May 06, 2025'; p.9-10, 13-16 'May 06, 2026'; p.8 not read; p.11-12 none | all 2026-05-06 12:04 | ST7757.dxf 12 frames = p.1-7, 9-12; p.8 and the typical details p.13-16 are PDF-only (the DXF's DETAILS layout is empty) |
| SAN (sanitary, vector PDF) | 3: GF / 1F / 2F drainage plans 1:100 | SCALE / FILE NO 'SS-7757' / drawn by | NONE PRINTED | NONE | none | none |

Carriers (REGISTER_T195.csv): each ARCH page is on Drive three to five times: the full 12-page set (37.5 MB, uploaded
TWICE with the same title and byte size, not downloadable: identity by title + size only), a two-page part, and for
pages 3, 4, 9, 10 a single-sheet file; TEST_PAGE_01.pdf renders pixel-identical (30 dpi) to part 01-02 page 1. These are
copies of one issue, not revisions. File identity: the downloaded P7757.dxf (zip member), ST7757 dxf.dxf, ST7757.pdf
and sanitary-7757.pdf hash-equal tests/alsenan/registers/SOURCE_MANIFEST.json, and the DWG / DWF byte sizes match it:
every ledger built on the manifest's files used the files on Drive today.

## 3. Findings (issue rows, never quantities)

| # | Finding | Evidence | BOQ effect | Status |
|---|---|---|---|---|
| D-T195-1 | No sheet of any set prints a revision; the architectural title block prints no number, date or title | title blocks of all 31 pages (section 2) | none today: one issue exists. Revision control can only be by file identity (sha256 / title + size), so the register pins files; a reissue on Drive would be invisible to a ledger that cites "sheet 07" | UNKNOWN which issue is "for construction" (assessment s.6 item 1) |
| D-T195-2 | The structural set prints two title-block dates: May 06, 2025 on p.1-7 (plans, pool / dome), May 06, 2026 on p.9-10 and 13-16 (schedules, typical details); every page was plotted 2026-05-06 12:04 | ST7757.pdf text layer + title blocks | none while one file exists; if a 2025 and a 2026 issue of the plans both existed, slab / beam / pool lines would need the right one | UNKNOWN (designer item: which date is the issue date). The raw ST DXF header records creation 2026-04-29, which a save-as can reset: not proof either way |
| D-T195-3 | ST p.11 / p.12 (continuous-beam schedules) carry no title block, only a 'Ref. S-2' / 'Ref. S-3' box and an embedded plot line naming another drawing file (T7757.dwg, layouts CONTINUOUS BEAMS1 / 2) | ST7757.pdf p.11-12 | the same schedules are frames SH03 / SH05 / SH07 of ST7757.dxf, so the content is in the set; their source drawing is not the structural DWG on Drive | designer item, low |
| D-T195-4 | Typical details (ST p.13-16: lintels, ground beams for exterior walls, parapet, lift pit, boundary wall, twisted / planted columns, stair beam and stair steel) and the recommendations (p.8) exist only in the PDF | ST DXF: DETAILS layout empty, no typical-detail title in model space | any line taken from them (stairs T-184 / T-189, parapets T-172, lintels) has PDF evidence only: CAD geometry cannot confirm it | recorded per sheet (cad_frame column) |
| D-T195-5 | SW / NE elevations, sections A-A / B-B, fence and area plans exist only as raster scans | P7757.dxf frames (T-038) vs the 12 pages | dimensions there are hand readings (T-092 / R-01 scans): never scaled | recorded per sheet |
| D-T195-6 | Two page-numbering bases for the split parts: 29 citations write 'Pages_05-06 p.6' (page of the 12-page set), 5 write 'Pages_05-06 page 1' (page inside the part file) | CITATIONS_T195.csv verdict PART_FILE_PAGE (T-114, T-159, T-173, T-184 x2) | all 5 also name the drawing title, and each resolves to the right sheet (2F plan, SE / SW elevation): no wrong sheet used | convention issue; rule proposed (section 5) |

## 4. Citation check over the merged ledgers (72 folders research/agents_t1*, all added 2026-10-20 .. 22)

543 citations in 85 files: 409 RESOLVED, 101 FILE_ONLY (a CAD / PDF file cited without a page), 14 PART_ONLY, 5
PART_FILE_PAGE, 14 CONTENT_REVIEW, and **0 NOT_IN_REGISTER, 0 PART_MISMATCH, 0 MULTI_REVISION**: every sheet a merged
ledger cites exists in the register, in its single issue. Most cited: ST p.8 (notes, 148), ARCH-03 GF plan (70),
ST7757.dxf (54), ARCH-10 section A-A (43). Citation forms: set page 'ST p.N' 225, shorthand 'sheet NN' 129, file
title 'p7757_arch_sheetNN' 45, part + page 29, part only 14, file only 101.

The 14 CONTENT_REVIEW hints were read one by one: all are sentences that list several sheets (e.g. "B20 40 x 75 (GF
roof slab, ST p.4; schedule ST7757.pdf p.10)"); none is a wrong sheet. The hint stays a hint (never an error).
One false citation found and excluded by the grammar: T-111 "structural GF roof sheet 12 + 11 + landing" is a step
count, not ARCH page 12 (regression test). ROOMS_T112 / RAILINGS_T164 'sheet10' rows all resolve to section A-A.

## 5. Missing from the issued set (MISSING_T195.csv; feeds assessment s.6 items 1-3, not an owner question now)

Present: plans per storey, all four elevations, two sections, structural plans / schedules / details / stair detail,
drainage plans. NOT IN THE SET: site / external-works plan (the 1:200 area plans are municipal area calculations, not a
site plan), top-roof plan (falls, drains), door / window schedule (opening heights stay HELD / ASSUMED: T-144, T-194),
finishes schedule or specification (floor / wall / ceiling / exterior finish types, waterproofing system), reflected
ceiling plan, wet-room / kitchen details, architectural stair details, water supply, electrical, air conditioning.
These stay project-information items (asked only when a quantity needs one and no drawing or rule settles it).

Rule proposal UP-DOCREG-001 v1.0.0 (new rule file, for the Lead / lane I; scope any villa, provenance this task):
(1) every quantity cites a register sheet key (set + page in the set) and, when the set prints one, its revision;
(2) a set without printed revisions is pinned by file sha256 (or title + size when not downloadable), never "rev 0";
(3) a split-part citation uses set pages ('part 05-06 p.6'), never the page inside the part file; (4) a sheet held in
two revision states makes every citation of it MULTI_REVISION until the citation names the issue; (5) two dates in one
set are an issue row, never a reason to pick one.

## 6. Lessons register row (proposed for ENGINEERING_REASONING_STANDARD s.7)

| 2026-10-22 | 5 merged citations read split-part pages in-file ('Pages_05-06 page 1') while 29 read set pages ('p.6') | No page-numbering convention for split PDF parts; the drawings print no sheet number to anchor it | Cite sheets by set + page in the set; a part file is a carrier, not a numbering basis (any villa) | t195 test_part_page_bases (normal set page, adverse in-file page, adverse page outside both) | register + check built (T-195), rule UP-DOCREG-001 proposed |

## 7. For the Checker (re-read two title blocks)

1. ST7757.pdf p.1 (COLUMN & AXIS PLAN): bottom-right title block SCALE 1/100, DATE 'May 06, 2025', FILE NO 'ST - 7757',
   no revision / sheet-number field; plot line 2026-05-06 12:04, layout AXIS. Compare p.13: DATE 'May 06, 2026', SCALE
   'AS SHOWN' (D-T195-2).
2. p7757_arch_sheet03.pdf (= set page 3, GF plan): the title block holds only the owner box; vertical plot line
   2026-05-06 11:21, layout Model; caption 'GROUND FLOOR PLAN 1:100'. Optional: sanitary-7757.pdf p.1 'FILE NO:-SS-7757',
   'SCALE:- 1/100', no date.
3. Optional: the citation check on any merged folder: `python3 -I research/agents_t195/alsenan_t195.py --live`.

## 8. Not done / uncertain

The 37.5 MB full architectural set (two Drive copies) and parts 03-04 / 09-10 are over the connector limit: their
identity rests on title + size and on the single-sheet files. ST p.8 (raster) date not read. CONTENT_REVIEW is a
keyword heuristic (title phrases only); it found no defect here. The checklist is engineering practice, not a Kuwait
regulation (deferred by the owner).
