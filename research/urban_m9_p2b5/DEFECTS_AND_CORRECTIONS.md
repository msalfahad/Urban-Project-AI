# New defects, findings and corrections (Phase 2B-5, the whole program)

**Classes:**

| class | meaning |
|---|---|
| ENGINE DEFECT | the engine is wrong |
| FINDING | a fact about the engine's behaviour that is not wrong but matters |
| RULE CONFLICT / INPUT | not the engine |
| CORRECTION | something this program had stated wrongly and corrected |

"Fixed" always means in the opt-in ARCH_TAKEOFF_V2.6; V1 - V2.5 are unchanged.

## 1. Engine defects

| id | stage | defect | evidence | state |
|---|---|---|---|---|
| D-C1 | C, D | a door drawn two ways at one opening: its leaf closes 0.80 m inside a 1.023 m band opening read as PASSAGE; the two views were not reconciled | instrumented private run + independent reader (`REAL_ROOM_VERIFICATION.md` §7) | **fixed** (D-V26-06): a held DOOR with both widths. Width left for the drawing / owner |
| D-C2 | C | doorway-strip attribution fails at a splayed wall (two doors share one merged strip) and where an opening is read as a passage; 3 of 5 wet doorway thresholds withheld; R-E has no doorway waterproofing line | Stage C sample | open (withheld with RFI); roadmap 1 |
| D-D1 | D | layer roles inferred from a count: a door layer needs two anchored swings, a column layer three filled squares; a single-instance layer is missed | benchmark: 11 single-door drawings, B04 / C03 column +2.18 % | open; `--layer-roles` remedy; roadmap 3 |
| D-D2 | D | an arc-walled room is kept on its chord (polygon, rect, dims); membrane / tile layouts are planned on the chord; the curved wall band is missing from the wall run | B10 (`tests/m9_p2b5/test_p2b5_curved_wall.py`, asserted as found); reference plan 4 / 38 rooms, ~0.7 % of the wall run | open; roadmap 2 |
| F-13 - F-18 | B | V2.5 band planner not least-membrane at wide flanges; roof drain in a lap and aligned splices; seam along a column face; a 0.20 m band piece; a closing joint on a corner; 4 shaped trims not decomposed | `V26_IMPLEMENTATION_REPORT.md` §8 | flagged in V2.6; no quantity change |

## 2. Defects in this program's own work, found and fixed before commit

| id | defect | fix |
|---|---|---|
| H-B1 - H-B9 | Stage B (V2.6 layer): cut ids before sorting, side-lap zone count, run-end corners, duplicate doorway crash, offset search step, fold frame, degenerate ring, float slivers as shaped trims, diagram labels | `V26_IMPLEMENTATION_REPORT.md` §9 |
| E-01 | the first D-V26-06 offered every free swing to the review fit: on the reference plan it merged two bathroom cells (the swing served its own inner doorway) | the CLOSED-swing guard; the independent reader confirmed the two rooms |
| E-02 | a review-fit note was written for a swing that fits strictly | notes only for swings failing a named review test, naming it |
| E-03 | the benchmark's independent reader read mm only, chord-only bulges, no XREF | units, 0.5 mm arc / bulge flattening, XREF refusal |
| E-04 | the skills test spelled a private project code it checks for | split literal; the privacy scan is clean |
| E-05 | Stage B / C reader and prototype defects (closures behind columns, 45-degree grouping, OCS arcs; raster text blobs, column false gaps, deskew noise, OCR false positives, width −1 px, wrong scale silently None; PDF quad columns) | recorded in the working notes; each covered by a benchmark test |

## 3. Corrections to statements

| id | was stated | corrected to |
|---|---|---|
| C-01 | Stage C total "70 checks, 58 pass, 12 fail" | 66 checks, 55 pass, 11 fail (an addition slip; the rows and the stored aggregate were always 66 / 55 / 11) |
| C-02 | Stage C: "three bathroom doors read as passages" (D-C1) | one door drawn two ways at one opening; two doors close their own doorways next to a passage and are correctly separate (PROVISIONAL) |
| C-03 | Phase 2B-4 H-A3 ("V25 selects" for flanges ≥ 0.14 m) | the audit planner's plan, not V2.5's; 19.25 m2 (0.14 - 0.15 m) and 21.10 m2 (0.16 m) for the engine's own plans (V26 report §9) |
| C-04 | Stage B F-17 (best joint order 0.10 m from a corner) | 0.51 m from a corner, 0.29 m from a seam end |
| C-05 | Stage C (an early draft): door feasibility "not reported" | reported for all three doors: ENLARGEMENT_REQUIRED 0.20 m, UNRESOLVED |

## 4. Rule conflicts and inputs (owner side)

| id | content | where |
|---|---|---|
| D-C3 | a doorless lobby merged into a wet room without an attachment note (44 % of the room) | owner scope decision |
| D-C4 | UP-CER-004's skirting exception against "no skirting in wet rooms" (~41 lm in the sample) | owner decision |
| D-C5 | Mode A heights are synthetic test parameters (door 2.10 m against the owner reference 2.20 m) | project values needed |
| S-01 | the synced `quantity-takeoff-rules` skill's skirting rule (perimeter minus doors everywhere) differs from the owner's wet-room rule | the owner's rules govern; the skill is not a rule source |
