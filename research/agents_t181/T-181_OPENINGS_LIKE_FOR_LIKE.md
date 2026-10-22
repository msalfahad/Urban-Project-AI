# T-181: doors and windows comparable like for like (pcs AND m2)

Worker 3, 2026-10-22 21:04 - 22:00 UTC, lane I. Tooling + a new key-map version only: no engine quantity, rule, method,
release or verdict changed. Development villa (Alsenan): diagnostic, not an accuracy claim. Rows are cited by the
committed register ids (research/agents_t150/OPENINGS_T150.csv, T-150 r2, Checker MERGED b35666a) and the committed
freelancer row ids (tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, workbook ALU); no drawing content is copied.

## What changed

- `tools/alsenan_keymap.py`: new opt-in path `--openings-register` (functions `load_openings_key_map`,
  `reference_opening_rows`, `opening_quantities`, `openings_like_for_like`, `openings_markdown`, `main_openings`).
  Without `--openings-register` the v1 / v2 / v2.1 CLI and outputs are unchanged (all 122 scorer tests pass untouched).
- `tests/alsenan/T181_OPENINGS_KEY_MAP.json`: NEW key-map version `URBAN_ALSENAN_OPENINGS_KEY_MAP_V1` (T001B_KEY_MAP.json
  unchanged): 4 opening classes, 21 freelancer rows tied to register scope labels, 1 class-held opening with its
  candidate classes and source, the owner-approved assumption source (Q-55 C).
- `tests/t181_openings_like_for_like/`: 20 tests (synthetic villa, not Alsenan, hand values in the docstring; 10
  refusal cases; one read-only Alsenan register run).

## Rules (general, any villa)

1. pcs and m2 are separate keys (`CLASS[nr]`, `CLASS[m2]`), never converted.
2. A reference row's count / width / height / area are read from its own cells (his header: B number, C length,
   D width / height, H = D*C*B); H must equal B x C x D and the class rows must re-add to his cover total, else refused.
   Notation first: his `=D*C*B` is count x width x height, checked on every row.
3. Per opening: pcs 1 only when the class is settled and no hold cause questions the opening; m2 = width x height only
   for a PRINTED height (DRAWING-CONFIRMED) or an ASSUMED height whose source is owner-approved (Q-55 C, ASSUMED —
   OWNER-APPROVED, WORKFLOW_CONTROLS s.4); a held height, a width range, a missing width or a hold cause -> HELD with
   its candidate, never 0. An ASSUMED height without an approved source is refused.
4. A class-held opening answers each candidate class (key map, with its source) once as HELD, so the class line is
   HELD, not silently compared low.
5. A class with no freelancer row is NOT COMPARABLE (reference-set gap), never a false positive.
6. Scope: each of his rows lists the openings it covers; his count vs tied openings gives AGREES / COUNT HELD /
   DIFFERS; a label ending in `?` is an uncertain tie, listed and not counted.

## Alsenan (register T-150 r2 vs freelancer aluminium workbook; engine = released ARCH_TAKEOFF_V2.9 on P7757.dxf +
## ST7757 dxf.dxf with the M4 route G profile, run this session on head 390fabf4, BOQ_LINES.csv 7d9ccb8a)

Side: opening register T-150 r2 (hand census from the drawings, Checker MERGED b35666a); NOT an engine run. pcs and m2 never converted; HELD is never 0.

| Class | Unit | This side | Evidence split | Held | Freelancer | Outcome | Diff | % |
|---|---|---|---|---|---|---|---|---|
| DOOR.EXTERNAL.ALUMINIUM | nr | 5 settled | DRAWING-CONFIRMED | D-GF-05 (class) | 5.000 | HELD | - | - |
| DOOR.EXTERNAL.ALUMINIUM | m2 | 10.560 on 5 | confirmed 0.000 (0); assumed 10.560 (5) | 0 openings + 1 class held | 12.000 | HELD | - | - |
| DOOR.EXTERNAL.ALUMINIUM same openings | m2 | 10.560 on 5 | - | - | 12.000 | DIAGNOSTIC | -1.440 | -12.00 % |
| WINDOW.ALUMINIUM | nr | 28 settled | DRAWING-CONFIRMED | W02 | 29.000 | HELD | - | - |
| WINDOW.ALUMINIUM | m2 | 56.771 on 8 | confirmed 56.771 (8); assumed 0.000 (0) | 21 openings | 116.900 | HELD | - | - |
| WINDOW.ALUMINIUM same openings | m2 | 56.771 on 8 | - | - | 54.931 | DIAGNOSTIC | +1.840 | +3.35 % |
| DOOR.INTERNAL.PVC | nr | 20 settled | DRAWING-CONFIRMED | D-GF-05 (class) | none | NOT COMPARABLE | - | - |
| DOOR.INTERNAL.PVC | m2 | 36.080 on 19 | confirmed 0.000 (0); assumed 36.080 (19) | 1 openings + 1 class held | none | NOT COMPARABLE | - | - |
| DOOR.MAIN_ENTRANCE | nr | 0 settled | DRAWING-CONFIRMED | D-GF-07 | none | NOT COMPARABLE | - | - |
| DOOR.MAIN_ENTRANCE | m2 | 0.000 on 0 | confirmed 0.000 (0); assumed 0.000 (0) | 1 openings | none | NOT COMPARABLE | - | - |

| His row | Label | Class | His count x W x H = m2 | Openings covered | Settled pcs | m2 this side | Scope |
|---|---|---|---|---|---|---|---|
| ALU:الكميات:14 | ALU-GF-EXT | DOOR.EXTERNAL.ALUMINIUM | 4 x 1 x 2.4 = 9.600 | D-GF-01, D-GF-03, D-GF-06, D-GF-09 (+? D-GF-05) | 4 | 8.360 | AGREES |
| ALU:الكميات:51 | ALU-2F-DOOR | DOOR.EXTERNAL.ALUMINIUM | 1 x 1 x 2.4 = 2.400 | D-2F-01 | 1 | 2.200 | AGREES |
| ALU:الكميات:15 | ALU-GF-BATH | WINDOW.ALUMINIUM | 4 x 0.6 x 0.8 = 1.920 | W04, W05, W06, W07 | 4 | HELD | AGREES |
| ALU:الكميات:16 | ALU-GF-W6.57 | WINDOW.ALUMINIUM | 1 x 6.57 x 4.3 = 28.251 | W03 | 1 | 28.251 | AGREES |
| ALU:الكميات:17 | ALU-GF-W6.33 | WINDOW.ALUMINIUM | 1 x 6.33 x 4.3 = 27.219 | W02 | 0 | HELD | COUNT HELD |
| ALU:الكميات:18 | ALU-GF-W1.00 | WINDOW.ALUMINIUM | 1 x 1 x 2 = 2.000 | W10 | 1 | HELD | AGREES |
| ALU:الكميات:19 | ALU-GF-W1.50a | WINDOW.ALUMINIUM | 1 x 1.5 x 2 = 3.000 | W08 | 1 | HELD | AGREES |
| ALU:الكميات:20 | ALU-GF-W1.20 | WINDOW.ALUMINIUM | 1 x 1.2 x 2 = 2.400 | W01 | 1 | 2.400 | AGREES |
| ALU:الكميات:21 | ALU-GF-W1.95 | WINDOW.ALUMINIUM | 2 x 1.95 x 2 = 7.800 | W11, W12 | 2 | HELD | AGREES |
| ALU:الكميات:22 | ALU-GF-W1.50b | WINDOW.ALUMINIUM | 1 x 1.5 x 2 = 3.000 | W09 | 1 | HELD | AGREES |
| ALU:الكميات:34 | ALU-1F-W1.00 | WINDOW.ALUMINIUM | 1 x 1 x 2 = 2.000 | W25 | 1 | HELD | AGREES |
| ALU:الكميات:35 | ALU-1F-BATH | WINDOW.ALUMINIUM | 6 x 0.6 x 0.8 = 2.880 | W18, W19, W20, W21, W22, W23 | 6 | HELD | AGREES |
| ALU:الكميات:36 | ALU-1F-W3.15 | WINDOW.ALUMINIUM | 1 x 3.15 x 3 = 9.450 | W17 | 1 | 11.515 | AGREES |
| ALU:الكميات:37 | ALU-1F-W1.55x2 | WINDOW.ALUMINIUM | 2 x 1.55 x 3 = 9.300 | W15, W16 | 2 | HELD | AGREES |
| ALU:الكميات:38 | ALU-1F-W1.55 | WINDOW.ALUMINIUM | 1 x 1.55 x 2 = 3.100 | W24 | 1 | HELD | AGREES |
| ALU:الكميات:39 | ALU-1F-W2.45 | WINDOW.ALUMINIUM | 1 x 2.45 x 2 = 4.900 | W14 | 1 | 3.920 | AGREES |
| ALU:الكميات:40 | ALU-1F-W1.20 | WINDOW.ALUMINIUM | 1 x 1.2 x 2 = 2.400 | W13 | 1 | 2.760 | AGREES |
| ALU:الكميات:48 | ALU-2F-W1.00 | WINDOW.ALUMINIUM | 1 x 1 x 2 = 2.000 | W27 | 1 | HELD | AGREES |
| ALU:الكميات:49 | ALU-2F-W1.20a | WINDOW.ALUMINIUM | 1 x 1.2 x 2 = 2.400 | W26 | 1 | 2.040 | AGREES |
| ALU:الكميات:50 | ALU-2F-BATH | WINDOW.ALUMINIUM | 1 x 0.6 x 0.8 = 0.480 | W28 | 1 | HELD | AGREES |
| ALU:الكميات:52 | ALU-2F-W1.20b | WINDOW.ALUMINIUM | 1 x 1.2 x 2 = 2.400 | W29 | 1 | HELD | AGREES |

Engine run (released BOQ lines only; no engine door / window m2 line exists):

| Key | Outcome | Engine | Freelancer | Diff |
|---|---|---|---|---|
| DOOR.EXTERNAL.ALUMINIUM[nr] | COMPARED | 2.000 | 5.000 | -3.000 |
| DOOR.EXTERNAL.ALUMINIUM[m2] | SILENT_OMISSION | no line | 12.000 | - |
| WINDOW.ALUMINIUM[nr] | COMPARED | 27.000 | 29.000 | -2.000 |
| WINDOW.ALUMINIUM[m2] | SILENT_OMISSION | no line | 116.900 | - |

### Reading in engineering terms

- **Aluminium windows, pcs:** register 28 settled + W02 HELD (T-161 F23: rendered as two windows with a pier, count 1
  or 2 not settled) vs his 29 -> HELD (29 or 30 vs 29). T-150 r2 wrote "29 vs 29 AGREE"; under WORKFLOW_CONTROLS s.8 a
  DIFFERS finding that affects a quantity holds that line, and the count is a quantity: proposed for the Checker.
  Released engine V2.9: 27 vs 29 = -2 pcs (-6.9 %): it misses W03 (curved pool glazing 6.57) and W18 (bath 0.50) (T-040
  G4 / G7).
- **Aluminium windows, m2:** 56.771 m2 DRAWING-CONFIRMED on 8 windows, 21 HELD (no printed height) vs his 116.900 ->
  HELD (never 0). Same 8 openings both sides: 56.771 vs 54.931 = +1.840 m2 (+3.35 %); per opening the T-150 r2 verdicts
  stand (W13, W14, W15, W18, W26 ENGINE_RIGHT on printed heights; W17 RULE_DIFFERENCE, Q-39 C / Q-32 A).
  Released engine V2.9: no window m2 line (SILENT_OMISSION of 116.9 m2; the BOQ category does not exist in V2.9).
- **Aluminium doors, pcs:** 5 settled vs his 5, plus D-GF-05 (kitchen to the side passage) class HELD on Q-67 A /
  D-48 -> HELD (5 or 6 vs 5). Scope: his row 14 (4 x 1.00 x 2.40) = D-GF-01, -03, -06, -09 (+? D-GF-05); row 51 = D-2F-01.
  Released engine V2.9: 2 vs 5 = -3 pcs (-60 %): the other three ALU doors are not BOQ lines in V2.9 (class / width
  review in its door schedule).
- **Aluminium doors, m2:** 10.560 m2 ASSUMED — OWNER-APPROVED (widths 4.80 m x Q-55 C 2.20) vs his 12.000 -> HELD (class
  held door). Same 5 openings: -1.440 m2 (-12.00 %): RULE_DIFFERENCE (his 2.40 printed nowhere vs the owner fallback
  2.20; two 0.90 doors vs his 1.00).
- **PVC doors** 20 settled pcs, 36.080 m2 ASSUMED — OWNER-APPROVED on 19 + 1 HELD (width range 0.69 .. 0.80) + the class-
  held D-GF-05; **main entrance** 1 set HELD (T-161 F07c, candidate 5.000 m2): NOT COMPARABLE (no supply line in his
  workbooks), never false positives.
- **Scope ties:** 21 of his rows, 20 AGREES + 1 COUNT HELD (row 17 = W02); no row DIFFERS; no false positive, no
  duplicate opening.

## What is missing

- The V3.0.x candidate has no door / window lines (T-150 is research only): wiring the register's m2 into the candidate
  is a separate integration package (Gate B), not this task.
- 21 window heights (designer D-45), D-GF-05 class (Q-67 A / D-48), W02 count and the main entrance (D-53) stay HELD.
- `--openings-engine-run` scores only the engine's released pcs lines; V2.9's held doors live in its door schedule,
  not in BOQ_LINES, so the -3 pcs is "not released", not "not found".
