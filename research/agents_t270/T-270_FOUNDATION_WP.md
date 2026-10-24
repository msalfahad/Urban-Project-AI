# T-270 Integration package (Gate B): foundation and lift-pit waterproofing as their own line family

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
| WP.FOUNDATION.BURIED_LIQUID | m2 | **35.404365** (21 faces) | DRAWING-CONFIRMED (line PARTIALLY VERIFIED: 5.3825 own-checked, 2 runs / 3 faces) | T-263, Verifier 17:59 |
| WP.FOUNDATION.BURIED_LIQUID | m2 | BLANK x 4 (85 held faces; footing tops; necks; boundary G.B / straps) | HELD | Q-21 C, D-33 / D-34, note scope |
| WP.FOUNDATION.PROCUREMENT | item | BLANK | HELD | UP-WP-MAT-001 |

Totals by evidence status: VERIFIED 109.85 m2 membrane + 109.85 m2 / 5.4925 m3 screed + 47.43 / 26.73 m2 pit +
20.70 m2 / 1.035 m3 pit screed; DRAWING-CONFIRMED 35.404365 m2 liquid; HELD 11 lines, all blank (never 0). The held
readings are only in `V3_0_15_SCENARIOS.json` (owner 2026-10-24 10:56): 1B1B 4.55 / 4.64 m2 (screed 0.2275 / 0.232 m3),
footing sides 80.037171 (liquid) / 93.033788 (sheet) m2, pit walls 8.9 m2 per m, footing tops 104.72 .. 104.75 m2
(single detail), necks 55.6 .. 55.8 m2 per m. Engine vs freelancer: -109.85 m2 membrane, -5.4925 m3 screed, -47.43 m2
pit membrane, -26.73 m2 board, -35.404 m2 liquid: drawn scope missing from BOTH released A and the freelancer
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
- Known open delta: T-276 (REJECTED narrow r2 at 20:59) traces the buried faces and moves the 35.404 m2 by +11.1165
  (incl. -1.5158 of faces it reads as not-earth). Not applied here, never estimated; the line stays PARTIALLY VERIFIED
  and joins T-276 as a delta after its Gate A (WAITING `BURIED_FACES_TRACED`).

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
