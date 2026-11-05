# T-423: T-246 split remainder (b)-(d) as ARCH_TAKEOFF_V3.0.58 (integration package for Gate B)

Worker 1, 2026-11-04 23:24 .. 2026-11-05 00:50 UTC. Stream F / lane I. Development villa, not an accuracy claim.
Drawings cited by Drive title only ('Alsenan chalet project': P7757.dxf from P7757_DXF_COMPRESSED.zip `ab54dd55`,
'ST7757 dxf.dxf' `9f9d1179`). No quantity moves.

## 1. Reproduced base

Own chain run (research/agents_t167/v304_run.py -> research/agents_t310/v3057_run.py, Python 3.11.18):
V3_0_56 `4e25c54f` -> V3_0_57_BOQ_LINES.json **`25a8b406`** (4,994 lines) = the candidate of record (T-310 r7, merge
87ef8718). V3.0.58 was then produced on those lines by `arch_v3058.changes_for` / `write` directly (the same calls the
hub makes; the full hub run in s.5 gives the same file):
V3_0_58_BOQ_LINES.json `ae938fca`, 4,994 lines: **22 CHANGED_TEXT_ONLY, 4,972 SAME, 0 CHANGED, 0 ADDED;
totals_moved_by_code {}**; every V3.0.10 .. V3.0.57 family check re-run on the result (arch_v3057.integrate) passes.

## 2. What each piece did (line by line in V3_0_58_INTEGRATION_LEDGER.csv, private)

| Piece | Lines | Before (V3.0.57) | After (V3.0.58) | Evidence |
|---|---|---|---|---|
| CEILING_LIST (d) | 5 FIN.CEILING | gross - net = 1.4227 / 11.5808 / 0.341845 / 1.2410 / 0.4472 m2 with an EMPTY list (T-330 FLAG) | ONE deduction each, by id DOME:WEST/EAST:over:<room>, qty = the gap, within 0.00005 of the T-283 dome-table print (0.341845 vs 0.3418: the line's own unrounded gap, never a rounding move) | T-335 FILL (gross / decor), T-283 dome table (ROOMS) |
| set aside (d) | GF open plan L-eb3be58f | gross 126.927696, list 16.005 (void, unit key), net 101.137092: residual 9.785604 | unchanged, named | the gap closes only through still-held stair-zone / no-ceiling pieces (9.8536 + 1.7719 vs 9.7856 + 0.777392 slab): needs a T-284 ledger row by id |
| set aside (d) | 1F open plan L-fc116bb6 | BLOCKED_RFI, no net | unchanged, named | nothing to list |
| FACE_PIECE (b, T-388 F1) | 1F-02 tile L-a34d0920 + backing L-3eba04f2 | D-1F-04 1.760 m2 on face 1F-W23 (3.600), doorway piece 2.5628 | on 1F-02 OFF:DOORWAY: W23 5.360, doorway 0.8028; list item and owner-method record re-faced; room 27.9101 m2 unchanged | T-388 FINDINGS F1, T-312 / T-329 face ledgers |
| F1 HELD | GF-02 / GF-03 / GF-10 / GF-11 tile + backing (8 faces) | lines BLANK (annex room height G2), no face record | unchanged: no hole booked on any face | T-388 F1 rows with no m2 |
| PAINT_NA (b, T-388 F3) | pantry paint L-c3f7e68c | already NOT_APPLICABLE_WITH_EVIDENCE (V3.0.34, T-351 + T-388) | not touched: dropped from the package | candidate line notes |
| THRESHOLD_FIELDS (c, O-T327-1) | 14 FIN.MARBLE.THRESHOLD | 10 BY_SPEC (UP-THR-001 strips) + 4 URBAN_METHOD (R-T327-1 retypes) | all URBAN_METHOD, rule source UP-THR-001 + URBAN-WET-SERVICE-MARBLE-THRESHOLD v1 (OWNER_APPROVED) | T-327 verdict O-T327-1 |
| THRESHOLD_FIELDS (c, O-T327-2) | 14 + the D-1F-03 dry strip (FIN.FLOOR.PORCELAIN) | m.l / pcs only in the formula text (4 + 1) or only as length_m / depth_m inputs (10) | measure_pair {m2, lm, nr, price_one_basis} = the formula print (5) or length x depth = net (10), asserted | T-327 verdict O-T327-2 |

T-330 deductions check (tools/t330_deductions_check.py, own run): FIN.CEILING FLAG **6 -> 1** (the set-aside GF line);
no new FLAG anywhere; one FIN.WP.FLOOR FLAG carried unchanged from V3.0.57 (outside this row, for the Lead).

## 3. Rule (R-T423-1, every villa; in engine/source/arch_v3058.py)

A listing binds to the line content it was read on and stops on a stale line; a listed deduction names what it
deducts with one non-negative qty in the line's unit and the list closes gross to net; a deduction sits on the face
piece its contour segment lies on, and moving it never moves the room total; NOT_APPLICABLE carries no figure and names
its carrying line; one physical item has one material_state; alternative measures are fields equal to the formula or
the line's own inputs, never a second billable quantity; nothing else moves.

## 4. Tests

tests/t423_split_remainder (18): villa V423 by hand (R1 20.000 - dome 3.000 = 17.000; R2 19.016545 - 0.341845 =
18.6747 vs print 0.3418; B1 face 8.400 - 1.680 = 6.720 and doorway 2.520 -> 8.400 / 0.840, room 9.240 unchanged; K1
paint NA; T1 0.80 x 0.20 = 0.16 m2, 0.80 m.l, 1 pc; strip from inputs 0.8 x 0.15 = 0.12). Adverse: dome print off by more
than half a unit, stale binding (net / state / element), list already present, applied twice, hole to a straight face,
hole not on its face, hole larger than the doorway piece, carrying line in another room or blank, valued paint line,
measure pair not the formula, 2 pcs, mm-scale slip, two material states left, set aside AND changed, stale set-aside
name, a quantity moved, unknown code / action, mirrored face order.

## 5. Registry and what is still open

BOQ_FAMILY_MASTER **1.55.0** (research/agents_t423/build_master_1_55_0.py, the T-310 builder re-pointed): 1.54.0 + T-310
V3.0.57 promoted by R-T485-1 (merge 87ef8718 + verdict from the board, out/PROMOTIONS_SOURCE_1_55_0.json; line diff
V3.0.56 -> V3.0.57 = B8-01 / B8-02 / B8-03 / B8-09, out/T423_PACKAGE_FAMILIES.json; census at V3.0.57,
out/LINE_INDEX_V3_0_57.json, issues {}; the same census tool on V3_0_56 reproduces T-310's LINE_INDEX_V3_0_56.json byte
for byte) + pending V3.0.58 + B3-01 / B3-04 / B4-01 / B4-03 / B5-01 text; 0 problems; RULES_MANIFEST by its tool.

Full hub run (research/agents_t423/v3058_run.py on the Drive copies): V3_0_57 `25a8b406` -> V3_0_58_BOQ_LINES.json
**`ae938fca`** (= the direct module run), 22 CHANGED_TEXT_ONLY, 4,972 SAME, totals moved {}; vs released V2.9 + route G:
SAME_QUANTITY 576, QUANTITY_DIFFERS 1,016, NOT_IN_RELEASED 3,402 (as V3.0.57: nothing moves).

## 6. Lessons-register row (proposed)

| 2026-11-05 | 2 of the 4 items of a split remainder (pantry paint NA, the 4 GF face moves) were already done or not applicable on
the candidate of record when the package started | the row was written on V3.0.32 / V3.0.36 lines; later packages changed them | re-read every named line on the candidate of record before writing a piece; drop what is done, name what is held (scope: every integration package; provenance T-423) | the binding of R-T423-1 a | PROPOSED |
