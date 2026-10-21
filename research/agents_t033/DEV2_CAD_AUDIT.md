# T-033: development project 2, read-only CAD audit of its DWG

Worker, 2026-10-19. Read-only. Source: Drive, second subfolder of "Urban BOQ private data", file `20230331-STR.dwg`
and the architectural PDF in the same folder. Both were downloaded to the session scratchpad (outside this clone) and are
not in this repository. No client name, coordinates or drawing content beyond counts and layer / type names below.
Every figure is from a command output of this run (scripts kept in the scratchpad; `dwgread` JSON + a section count of
the DXF + a JSON census in Python).

## Result in one line

**Lossy, and the architectural floor plans of the apartment cannot be confirmed in this DWG.** The pinned LibreDWG DXF
writer drops the whole ENTITIES section and 578 of 1,964 block definitions; the JSON decode succeeds but this file is a
structural set (strengthening / jacketing details, schedules, notes) whose model space carries an architectural
*background* (walls, doors, windows, dimensions) with **no English room labels and only one English plan title
("GROUND FLOOR PLAN")**. The PDF's plot stamp names a **different** source DWG (an architectural plans file), so this
STR file is not the PDF's source. V2.9 was therefore **not** run (task: run only on a lossless conversion).

## Source

| Item | Value |
|---|---|
| DWG | 2,437,120 bytes, sha256 `2635cc50ab5ebc559337684fda64e2d028a6978ae2455e00b36bb4859d00d60b` |
| Format | `AC1021` (AutoCAD 2007 / R2007 encoding) |
| Units | `$INSUNITS = 4` (millimetres), `$LUNITS = 2`, `$DIMSCALE = 150`, `$TILEMODE = 1` |
| Layouts | Model + 2 paper layouts; paper space holds 74 entities (title frame / logo) and 4 viewports |
| PDF | 494,589 bytes, sha256 `bddb175c39834594def9178995b37df78e78df0d8d62ac731be44464a47bfa74`, 2 A3 pages, vector paths only: 0 extractable text characters, 0 raster images (text is outlined, so `pdftotext` returns nothing) |
| PDF sheets | page 1 "SECOND FLOOR PLAN", page 2 "ROOF FLOOR PLAN" (read from the rendered title block) |
| PDF source DWG | plot stamp names an architectural plans DWG in an architecture folder, plotted 2023-03-09: **not** `20230331-STR.dwg` |

Decoder: GNU LibreDWG 0.13.3, built from the release tarball (sha256
`83f1f6e78a744777a481ff4520e4cef3f8ac4b2c1c25671077ca12fe81e8816e`) in the scratchpad, `--disable-bindings`.

## Conversion: per entity type, decode (JSON) vs DXF output

`dwgread -O JSON` -> `SUCCESS`. `dwg2dxf` -> exit 0 but logs
`ERROR: dwg_handle_name: Could not resolve CONTROL object POINT for table BLOCK`; the DXF has sections HEADER,
CLASSES, TABLES, BLOCKS and **no ENTITIES section**; ezdxf 1.4.4 `recover.readfile` raises
`DXFTypeError: name has to be a string, got NoneType` on it.

| Entity type | JSON decode (all spaces + blocks) | DXF (BLOCKS section; no ENTITIES) | Lost |
|---|---:|---:|---:|
| LINE | 16,997 | 4,371 | 12,626 |
| TEXT | 6,183 | 2,458 | 3,725 |
| POINT | 5,802 | 3,806 | 1,996 |
| INSERT | 4,301 | 2,248 | 2,053 |
| LWPOLYLINE | 2,870 | 1,359 | 1,511 |
| BLOCK / ENDBLK | 1,964 / 1,964 | 1,386 / 1,242 | 578 / 722 |
| HATCH | 1,863 | 1,299 | 564 |
| MTEXT | 1,766 | 1,083 | 683 |
| DIMENSION (all kinds) | 1,764 | 206 | 1,558 |
| CIRCLE | 1,631 | 1,263 | 368 |
| ARC | 347 | 64 | 283 |
| LEADER | 320 | 130 | 190 |
| ELLIPSE | 314 | 111 | 203 |
| ATTRIB / ATTDEF | 146 / 18 | 7 / 17 | 139 / 1 |
| VERTEX_2D / POLYLINE_2D / SEQEND | 98 / 37 / 106 | 0 / 0 / 1 | all but 1 |
| MLINE | 31 | 0 | 31 |
| SOLID / REGION | 31 / 16 | 13 / 8 | 18 / 8 |
| VIEWPORT | 5 | 0 | 5 |
| UNKNOWN_ENT (class RTEXT, Express Tools) | 2 | 0 | 2 |
| **Total** | **48,576** | **21,072** | **27,504 (57 %)** |

The DXF route is lossy. The JSON decode itself is not clean either:

- 12,567 handle values occur on more than one object (the known `PINNED_LIBREDWG_DWGREAD_JSON_HANDLE_REPRESENTATION_DEFECT`
  / `CAD_ADAPTER_HANDLE_IDENTITY_COLLISION`), so any split by owner (model / block) below is indicative, not exact.
- 206 UNKNOWN_OBJ, 2 UNKNOWN_ENT (RTEXT), 28 invalid UTF-8 bytes in the JSON text.
- Arabic text is **not Unicode**: 1,603 TEXT/MTEXT use the SHX font `bas-f-n.shx` and decode as Latin-letter / tilde
  sequences. 0 texts contain Unicode Arabic. Reading Arabic labels needs a code map for that font (none in the engine).

## What the drawing holds (JSON decode, counts only)

Model space: about 11,100 entities. Layer groups in model space: architectural `A-*` layers ~7,400 entities
(LINE 5,265, DIMENSION_LINEAR 798, INSERT 398, LWPOLYLINE 218, ARC 162, TEXT 113, HATCH 84, ELLIPSE 38), structural
`S-*` / COL / BEAM / DOWELS / JACK / STIR layers ~2,200, other ~1,500.

| Question | Answer (counts) |
|---|---|
| Layers | 174 defined, 103 used. Architectural: `A-PL-WALL` (6,065 entities: 5,237 LINE), `A-PL-DOOR` (2,361), `ARDOOR` (286, mostly INSERT of block `D1`), `A-PL-WINDOW` (920), `A-PL-TEXT` (3,976: 3,806 TEXT), `A-PL-DIM-INT` (6,854), `A-PL-STAIRS` (899), `A-PL-AXIS`, `A-PL-AREA-LAYOUT`, `A-PL-ELEVATOR`, `A-PL-ROOF`, `A-PL-NEIGHBORS`, `A- BATH-00`, `P-FIXT` (369). Structural: `S-ST` (3,459), `S-TST` (614 TEXT), `COL` (481), `col-hatch` (341), `DOWELS` (366), `JACK` (533), `BEAM` (138, incl. 31 MLINE), `STIR`, `S-RIB`, `S-SLAB- BAR`, `S-SECT-CONC`. Sheet: `FRAME`, `FRAME TEXT 01`, `FRAME LOGO 00`, `G-ANNO-TTLB`, `PLOT` |
| Walls / doors / windows in model space | `A-PL-WALL` 3,389 entities; door layers 206; `A-PL-WINDOW` 688; door block `D1` inserted 163 times in model space |
| Dimensions | 935 DIMENSION entities in model space (917 linear, 16 aligned, 2 diameter); 829 more inside blocks |
| Frames / sheet titles | 19 title-block inserts (`dtitle`) in model space; their title attributes are SHX-font Arabic (not readable as text); Latin detail titles are structural ("TYPICAL DETAIL FOR CONTINUOUS BEAMS", "STAIRS TYPE A/B", "REINF. DETAIL FOR HVAC OPENING IN BEAMS", ...). English plan titles in model space: **1** ("GROUND FLOOR PLAN") |
| Room labels | English room-name texts directly in model space: **0**. 854 English room-name texts and ~1,520 SHX-Arabic texts sit on `A-PL-TEXT` inside block definitions; the English set repeats a fixed vocabulary of ~30 names exactly 14 times each (a room-name library, not one plan), and 765 `A-PL-TEXT` texts are in 59 blocks never inserted anywhere |
| Structural content | notes and schedules ("AS PER SCHEDULE", "STAIRS SCHEDULE", slab / waterproofing notes), strengthening details ("NEW JACKET", "FIXED WITH EPOXY", dowels, jack points) |
| Second-floor / roof plan of the PDF | no English title for either in model space; cannot be identified without reading the SHX-Arabic titles |

## Conclusion for the lead

- Conversion with the pinned LibreDWG is **lossy** (57 % of entities lost in DXF; JSON has 12,567 handle collisions and
  non-Unicode Arabic text). Per the task, V2.9 was not run and no room / opening comparison was made.
- The file is a structural drawing with an architectural background. It does **not** let an agent confirm the
  apartment's architectural floor plans (no plan title for the second floor or roof, no room labels in model space), and
  it is not the PDF's source file.
- Proposed owner question (one sentence): "For development project 2, please export to DXF (SAVEAS DXF 2018) and upload to
  its Drive folder the architectural plans DWG that the PDF's plot stamp names (the second-floor and roof plans), because
  the -STR.dwg is a structural file whose conversion here loses 57 % of its entities: (a) yes, I will upload it,
  (b) only the -STR.dwg exists, so score finishes from the PDF with the plan reader (T-003)."
