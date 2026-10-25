# T-270 Integration package (Gate B): foundation and lift-pit waterproofing as their own line family

## 0. r2 (narrow rework of the Verifier 2026-10-24 22:58 Gate B rejection; this section governs)

Cause (Verifier 22:58): the WP.FOUNDATION.BURIED_LIQUID sub-line 'BURIED-GB' carried the T-263 run-face total
35.404365 m2 as DRAWING-CONFIRMED; T-276 r2 (MERGED 4d88681b, Verifier 22:54 Gate A PASS, own re-measure) traces the
same physical faces once each and shows the 35.404 holds faces that are not earth faces (tees, pool-court side, span
overlaps) and omits traced ones. A total known to contain non-element faces is not DRAWING-CONFIRMED as a total.

r2 change (only this sub-line; every other line byte-for-byte r1):
- BURIED-GB = the 32 GROUND_BEAM DRAWING-CONFIRMED faces of `research/agents_t276/LEDGER_T276.csv` = **45.4682 m2**
  (77.805 m traced; ARC 2 / 5.017465, EXTERIOR MAIN 18 / 29.178205, INTERIOR 10 / 10.49256, PIECE 2 / 0.77997), line
  PARTIALLY VERIFIED. Checker own-checked 5 faces 8.876475 m2: 22:54 ring ARC 158 GS-10 3.6091 + GS-23 1.408365
  (own 5.9055 vs 5.9029 m, -0.04 %) and 170+7C3#2 side A GS-25 1.32413 (own 1.3247, -0.05 %); 17:59 7E9+7EA#1 GS-03 +
  GS-04 2 x 1.26744 (own 2.535, -0.005 %). Not VERIFIED (27 faces not re-measured).
- Delta against r1: **+10.063835 m2** (35.404365 -> 45.4682; +28.4 % on the sub-line), not estimated: the r1 figure
  is replaced by the merged trace, never adjusted.
- HELD BLANK by name, never 0, never a range in the BOQ: BURIED-GB-HELD = 118 traced faces 244.2827 m (DEPTH_HELD 103,
  PANEL_HELD 10 on GS-12 / GS-16, PANEL_SPLIT_LEVEL 5 on GS-08); BURIED-NECKS = 66 neck faces 33.3488 m on the neck
  height (Q-21 C) together with the necks DC deduction 16.560385 m2 on 13 necks (19 held, 4 lift necks T-219's);
  BURIED-TOPS and BURIED-BOUNDARY unchanged (T-263). Readings (lengths, the deduction) only in V3_0_15_SCENARIOS.json.
- EXCLUDED by name on the line: 17 ground-beam faces 51.771 m above natural ground (no earth), 8 lift-ring faces
  14.9997 m (WP.FOUNDATION.LIFT_PIT_*, T-219: one face once), soffits on blinding 55.002 m2 (T-263).
- The T-263 ledger is SUPERSEDED for this item code / unit (`superseded` in the piece inputs); the engine refuses any
  released WP.FOUNDATION.BURIED_LIQUID record taken from it (arch_v3015.load_inputs), tested on the development villa
  (the 35.404365 total with matching declared totals is refused) and on villa P-270. The WAITING note
  BURIED_FACES_TRACED is removed.
- Rule (any villa, lane I): a merged re-trace that supersedes an older ledger for one item code / unit is carried in
  place of it, and the older total is refused at load, never netted, never kept as a second reading in the BOQ.
- Lessons row (proposed, ERS s.7): 2026-10-25 | an integration carried a merged total its successor trace had shown
  to hold non-earth faces | the superseded ledger stayed a valid source | declare `superseded` per item code / unit and
  refuse its released records at load | tests/t270_foundation_wp_lines (development villa T-263 total refused, P-270
  successor rules) | PROPOSED.
- BOQ_FAMILY_MASTER 1.10.0 rebuilt by its builder (integrates T-219, T-263, T-276), rules manifest by the tool.
- RUN r2 (2026-10-25, Python 3.11.17, Drive P7757.dxf `ab54dd55`, 'ST7757 dxf.dxf' `9f9d1179`): V3.0.4 csv `d86de34a`,
  V3.0.12 `8f80cf5d`, V3.0.13 `6be1bd4e`, V3.0.14 csv `ad893df9` / json `48d7d54b` REPRODUCED; V3.0.15 runner = direct
  step byte-identical (BOQ json `e54cae74`, csv `a4dc01dd`, diff `58c6c52f`, ledger csv `0192ca35`, scenarios
  `a79b865d`); 3,680 -> 3,699 lines, 0 replaced, 19 added, 3,680 byte-identical to V3.0.14 (outside-rows sha256
  de3abfcf..., as r1), 4 blinding lines identical; evidence VERIFIED 7 / DRAWING-CONFIRMED 1 / HELD 11; guard
  held_live_new []; totals moved only on the 10 WP.FOUNDATION keys. r1 code re-run on the same V3.0.14 gives r1's
  json `863bd18e` / csv `2a1757fa`; line by line r1 -> r2: 3,696 byte-identical, 3 changed, all WP.FOUNDATION.BURIED_LIQUID:
  BURIED_GROUND_BEAM_FACES 35.404365 -> 45.4682 m2, BURIED_GROUND_BEAM_FACES_HELD and NECK_FACES text only (still
  BLANK, BLOCKED_RFI).
- FULL SUITE on ea8a9ff9 (5 folder chunks through the wrapper, to the end): 13,013 passed, 363 failed, 34 errors, 218
  skipped, 105 xfailed; the 395 failing / erroring ids are exactly the ones that fail on the working head aba9399a
  (same files re-run there: 395, 0 new, 0 gone; rebuild-from-private-input, dependency-register and pa09 fixture
  tests, none touching this package).

Worker 3 (lane I), 2026-10-24. ARCH_TAKEOFF_V3.0.15 = the V3.0.14 candidate + ONE new line family
WATERPROOFING.FOUNDATION (`engine/source/arch_v3015.py`). Opt-in candidate, NOT the released default (released stays
ARCH_TAKEOFF_V2.9 + route G); nothing released; rollback = run V2.9. Integrates T-219 (MERGED de7c1c4c) and T-263
(MERGED c0ab564d); the extent check reads T-233 (MERGED 2ecb5bf0). Drawings named by Drive folder and title only.

## 1. The physical elements (ERS s.2.1) and the two methods side by side (ERS s.2.2)

| Element | Physical definition (drawing) | Owner manual method | Drawing-derived method (carried) |
|---|---|---|---|
| Footing membrane | the 2 cm layer between the 10 cm blinding and the footing, ST p.13 both typical details; ends at the footing faces | none for foundations (B8-08): the owner's roll / lap / 0.20 upturn method is for wet areas and roofs and is NOT extended | L x W of each drawn footing outline (FN notch deducted once), one layer installed |
| Footing protection screed | 5 cm screed over the membrane, same plan | none | outline m2; m3 = outline x printed 0.05 |
| Footing side faces | p.13 right detail: two layers liquid on P x H; left detail: sheet down the sides P x (H + 0.07) | none | HELD: the founding level selects the detail (Q-21 C) |
| Lift pit membrane / board / screed | ST p.14 lift detail + FF 1B2B / ring 10EB / C9 1090 | none | by component: soffit + base and screed sides + top outside the pit envelope; board on sides and top; screed under the base; walls HELD (pit depth) |
| Buried liquid coating | p.13 note 'all surface in contact with earth', read per face | none | per face with earth against it: interior 2 x (D - 0.10) x L, main exterior inner faces 0.85 x L; plinth faces and soffits on blinding excluded |
| Procurement | product / coats not printed | owner layout rules apply only to a printed sheet product | HELD (UP-WP-MAT-001) |

The blinding (STR.CONC.BLINDING, CONCRETE) is NOT this family: it stays byte-identical (asserted by `integrate`).

## 2. Lines added (V3.0.15 vs V3.0.14 vs released V2.9 + G vs freelancer)

Every line is NEW (not in V3.0.14, not in released V2.9, no freelancer row: his waterproofing is wet areas and roofs
only). Evidence status per WORKFLOW_CONTROLS s.5; release status NOT RELEASED on every line.

| Item code | Unit | V3.0.15 | Evidence | Source / Checker |
|---|---|---|---|---|
| WP.FOUNDATION.FOOTING_MEMBRANE | m2 | **109.850** (24 outlines) | VERIFIED (line PARTIALLY VERIFIED: 24 / 25) | T-219, Verifier 10:40 own schedule x tags + 9 drawn outlines |
| WP.FOUNDATION.FOOTING_MEMBRANE | m2 | BLANK (1B1B F10 / F, two tags) | HELD | Q-31 C |
| WP.FOUNDATION.FOOTING_SCREED | m2 | **109.850** | VERIFIED | T-219 |
| WP.FOUNDATION.FOOTING_SCREED | m3 | **5.4925** | VERIFIED | T-219: 109.85 x 0.05 |
| WP.FOUNDATION.FOOTING_SCREED | m2 / m3 | BLANK (1B1B) x 2 | HELD | Q-31 C |
| WP.FOUNDATION.FOOTING_SIDES | m2 | BLANK | HELD | Q-21 C (detail selection) |
| WP.FOUNDATION.LIFT_PIT_MEMBRANE | m2 | **47.430** (20.700 + 10.920 + 15.810) | VERIFIED (walls HELD) | T-219, Verifier 10:40 own |
| WP.FOUNDATION.LIFT_PIT_MEMBRANE | m2 | BLANK (pit walls) | HELD | pit depth (D-43) |
| WP.FOUNDATION.LIFT_PIT_BOARD | m2 | **26.730** (10.920 + 15.810) | VERIFIED (walls HELD) | T-219 |
| WP.FOUNDATION.LIFT_PIT_BOARD | m2 | BLANK (pit walls) | HELD | D-43 |
| WP.FOUNDATION.LIFT_PIT_SCREED | m2 / m3 | **20.700 / 1.035** | VERIFIED | T-219 |
| WP.FOUNDATION.BURIED_LIQUID | m2 | **45.4682** (32 traced faces; r1 35.404365 superseded) | DRAWING-CONFIRMED (line PARTIALLY VERIFIED: 8.876475 own-checked on 5 faces) | T-276, Verifier 22:54 (+ 17:59) |
| WP.FOUNDATION.BURIED_LIQUID | m2 | BLANK x 4 (118 held faces 244.283 m; footing tops; necks 33.349 m + necks DC deduction; boundary G.B / straps) | HELD | depth / panels (T-276), Q-21 C, note scope |
| WP.FOUNDATION.PROCUREMENT | item | BLANK | HELD | UP-WP-MAT-001 |

Totals by evidence status: VERIFIED 109.85 m2 membrane + 109.85 m2 / 5.4925 m3 screed + 47.43 / 26.73 m2 pit +
20.70 m2 / 1.035 m3 pit screed; DRAWING-CONFIRMED 45.4682 m2 liquid (r2); HELD 11 lines, all blank (never 0). The held
readings are only in `V3_0_15_SCENARIOS.json` (owner 2026-10-24 10:56): 1B1B 4.55 / 4.64 m2 (screed 0.2275 / 0.232 m3),
footing sides 80.037171 (liquid) / 93.033788 (sheet) m2, pit walls 8.9 m2 per m, footing tops 104.72 .. 104.75 m2
(single detail), necks 55.6 .. 55.8 m2 per m. Engine vs freelancer: -109.85 m2 membrane, -5.4925 m3 screed, -47.43 m2
pit membrane, -26.73 m2 board, -45.468 m2 liquid (r2): drawn scope missing from BOTH released A and the freelancer
(FREELANCER_WRONG on scope, per the Checker's T-219 / T-263 verdicts); no % (his figure is 0).

## 3. Run on the development villa

Own run, Python 3.11.17, Drive copies P7757.dxf (`ab54dd55`) and 'ST7757 dxf.dxf' (`9f9d1179`): T-167 chain V3.0.4
csv `d86de34a`, runner chain V3.0.12 csv `8f80cf5d`, V3.0.13 csv `6be1bd4e`, V3.0.14 csv `ad893df9` REPRODUCED (= T-240
WP3_WP4 s.3). V3.0.15 through the runner (`v3015_run.py`, `--method ARCH_TAKEOFF_V3.0.15`) and the step alone
(`v3015_direct.py`) give byte-identical files: BOQ json `863bd18e`, csv `2a1757fa`, diff `321181a5`, ledger csv
`be63471d`, scenarios `da15f896`.

Identity: 3,680 -> 3,699 lines; **0 replaced, 19 added, 3,680 byte-identical to V3.0.14** (outside-rows sha256
de3abfcf...); the 4 STR.CONC.BLINDING lines (15.179437 m3 PROVISIONAL + 3 BOUNDED) byte-identical. Diff vs V3.0.14:
SAME 3,680 / ADDED 19; vs released V2.9: the 19 lines NOT_IN_RELEASED (the other rows as V3.0.14). Evidence status of the
19 rows: VERIFIED 7, DRAWING-CONFIRMED 1, HELD 11 (blank). Guard re-check over 3,699 lines: findings identical to
V3.0.14 (CONVENTION_WHERE_PRINTED 87, PARTIAL_FOOTPRINT 2, PRINTED_VALUES_DISAGREE 75, SEARCH_INCOMPLETE 1,039),
`held_live_new` [] (no silent omission, no hold on an added line). Totals moved by code: only the 10 new
WP.FOUNDATION.* code / unit keys; every other code total unchanged. Released default unchanged; nothing released.

Note for the Checker: the V3.0.14 BOQ json on this head is `48d7d54b` (csv `ad893df9` = T-240's); T-240 recorded json
`98a68b72` on its own head before the later merges; the csv columns agree line for line, so the difference is outside
the quantity columns (not traced here; no V3.0.14 line is touched by this package).

## 4. Gate B notes for the Checker

- Always-by-hand set (WORKFLOW_CONTROLS s.1): every line is a new scope and a new calculation method, and the lift pit
  is structural-adjacent: all 8 released lines are in the mandatory set; re-measure references: footing schedule
  (S-TEXT.SCH FO-TY) x tag count, drawn outlines 1ABF / 180F / 180C (notch 0.40 x 0.35); FF 1B2B 4.600 x 4.500, ring
  10EB 2.200, C9 1090 (envelope 4.890 / 8.900); buried runs 7E9+7EA#1, 7E0+FD#1 (own in 17:59), plus any further face of
  LEDGER_T263.csv. No line is outside the mandatory set, so the 2 random lines rule has L = 0 remaining lines.
- Cross-trade: one face once. Footing sides / underlay / lift are T-219's; T-263 refuses them; the T-263 tops / necks
  are HELD apart from the T-219 sides; the blinding is CONCRETE and untouched.
- r1 text: T-276 was then open; r2 (section 0) carries its merged trace in place of the T-263 total.

## 5. Rule, tests, lessons

Rule (generalised, any villa; scope: printed foundation details): a layer printed between two structural elements is
its own trade's line on the element's outline (never the blinding's); a liquid coating note is a per-face condition;
held parts are blank in the BOQ with the readings in the scenario report; procurement only for a printed product.
Tests `tests/t270_foundation_wp_lines` (villa P-270 by hand: 4 outlines incl. a notch, lift pit 3.00 x 3.00, two
buried faces; adverse: membrane on the blinding area, blinding extent, held as 0, range in the BOQ, scenario reading 0,
component sum, screed at the blinding thickness, mm as m, component twice, VERIFIED without every component, released
procurement, unknown task, declared total, family already present, no blinding line, a change replacing the blinding, a
held line with a figure; development villa pinned to the Checker figures) + BOQ_FAMILY_MASTER 1.10.0 tests.

Lessons row (proposed, ERS s.7): 2026-10-24 | a verified underlay and pit system had no BOQ line in any candidate |
research ledgers merged unwired leave a drawn scope out of the BOQ | integrate a merged ledger as its own family with
held parts blank and readings only in the scenario report; assert the neighbouring structural line byte-identical |
tests/t270_foundation_wp_lines | PROPOSED.
