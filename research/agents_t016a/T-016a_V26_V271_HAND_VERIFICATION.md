# T-016a: the 10 EXPLAINED_UNVERIFIED changes V2.6 -> V2.7.1, checked by hand on the drawing

Worker 1, 2026-10-20. Docs only; no engine, tool, rule or test file changed. Rule: UP-QTY-STATUS-001.

## Result

**All 10 are VERIFIED by hand reading of the drawing. 0 CONTRADICTED, so no quantity fix task.**
All 10 come from **one** correction record, C27-0007 (DOOR_OPENING, NARROWED_TO_JAMB_SPAN). It is the first-floor
door OP-010 between the Laundry and a Bathroom / W.C.

- V2.6 read the wall gap as 1.023274 m.
- V2.7.1 reads the structural opening as the door frame's jamb span, 0.800 m.
- The other 0.223274 m is masonry. It is a 0.073274 m wall stub plus the 0.150 m body of a cross wall.

The same values are still in the released ARCH_TAKEOFF_V2.11, so later versions have not regressed them.

There is one side finding, and it is not one of the 10. 20 of the 28 measured V2.11 skirting lines have a
deduction list that does not add back up to the net quantity: 17.035 m are taken off without being listed. The
quantities themselves are consistent; the trail is not. A fix task is proposed below.

## How the 10 were found again (reproduction)

| Step | Input | Result |
|---|---|---|
| Drawing | Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, unzipped in the scratchpad | sha256 ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4 (= the board) |
| Runs | `tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V2.6` and `V2.7.1`, on working head c874c7b | exit 0 |
| Mode A | the same with `--facts research/urban_m9_s2/SYNTHETIC_FACTS_S2.json` | 487 V2.7.1 lines (= CAPABILITY_COVERAGE_MATRIX "487 lines") |
| Verifier | `tools/arch_change_verify.py --before V2.6 --after V2.7.1 --dxf ... --facts S2 --layer-roles 1=WALL D=DOOR W=WINDOW S-COL.BON=COLUMN` | **55 differences: 45 VERIFIED, 10 EXPLAINED_UNVERIFIED, 0 / 0**, exactly the N10 report |

Three operating facts the next verifier needs:

1. **Without `--layer-roles` nothing verifies.** The result is 49 differences, 0 VERIFIED and 1 false CONTRADICTED,
   because the reader finds no wall lines (T-P9-03). The roles are on the layer list of the run's own `ARCH_PLAN.json`.
2. **Mode U (no facts) gives 49 differences, 43 VERIFIED and 6 EXPLAINED_UNVERIFIED.** The 6 are a subset of the 10:
   without heights there are no plaster, wall-tile or skirting room lines to differ.
3. **"Mode A" on the reference plan uses the facts of the SYNTHETIC villa S2.** These are test parameters: walls
   3.0 m, wall tile 2.4 m, doors 2.1 m, windows 1.5 m. Its absolute plaster, wall-tile and paint values are **not
   Alsenan quantities**. Only the deltas below come from the drawing; the heights only multiply them.

V2.7 -> V2.7.1 (the review-space ceilings) was re-run the same way. All 3 are now VERIFIED by the tool's independent
face; the 1 EXPLAINED_UNVERIFIED of Phase 2B-8 (D-P8-04) is closed. This was checked by the tool, not by hand.

## The hand reading of OP-010 (drawing units mm; x is relative to the left jamb at x0 = -184595.784364)

The wall is horizontal and 150.000 mm thick: its faces are at y = -793943.540074 (Laundry side) and y = -793793.540074
(W.C. side). Layer roles are read from the layer names (1 = wall, D = door, S-COL.BON = column).

| Handle | Layer | What it is | From x | To x | Length |
|---|---|---|---|---|---|
| C2D | 1 | jamb closing line of the wall end, left | 0.000 | 0.000 | 150.000 (across the wall) |
| ACF / AD3 | 1 | wall faces left of the opening | ... | 0.000 | |
| INSERT 11B4, block D315, x-scale -1 | D | door frame: jamb blocks 0-50 and 750-800, depth 0-150 = wall thickness; leaf arc r 690 | 0.000 | **800.000** | frame 800.000, clear leaf 690 |
| AD2 (Laundry face) / AD7 (W.C. face) | 1 | wall stub, drawn on **both** faces | 800.000 | 873.273773 | **73.273773** |
| B0F (down) / B0E (up) | 1 | face of a cross wall | 873.273773 | | |
| no line on either face between them | | body of the 150 mm cross wall (B08 / B09 at the far side) | 873.273773 | 1023.273773 | **150.000** |

- **Structural opening = 800.000 mm, jamb to jamb.** The door frame starts exactly on line C2D (-184595.784364) and ends
  exactly where AD2 / AD7 start (-183795.784364).
- **V2.6's 1.023274 m** ran from C2D to the far face of the cross wall (B08 / B09, -183572.510591). That takes in the
  stub and the cross wall's body: 0.073274 + 0.150 = 0.223274 m, which is masonry on both faces.
- **The W.C.** is closed by B05 (x -1108.4 mm from the opening centre), B0E (+361.6), the opening's wall and the wall
  at +1875. Its size is 1.470 x 1.800 = **2.646 m2** and its perimeter is **6.54 m**; both equal the engine.
- **The Laundry** (16.94 m perimeter, 10.151 m2) reaches the opening's wall from below, between B07 / B05 and B0F.
  Both rooms therefore see 0.800 m of door, plus 0.073274 m of stub up to the cross wall at +361.6.

## The 10, one by one (hand value vs V2.7.1)

Heights: in Mode A the door height is 2.10 m (S2 test parameter). The waterproofing upturn is 0.20 m (owner standard,
UP-WP-DOOR-001). The ARCH.* / FIN.WP.* lines need no height.

| # | Line (1F) | V2.6 -> V2.7.1 | Hand calculation from the drawing | Verdict |
|---|---|---|---|---|
| 1 | ARCH.THRESHOLD, unattributed strip OP-010 | held (BLOCKED_RFI, 0.72 m2 measured strip) -> line removed | V2.6's "strip" polygons: one is 0.150 x 1.750 = 0.2625 m2 (x +361.6 ... +511.6, y +75 ... +1825, i.e. between B0E and B09 up to the column) and the other is 0.4575 m2 = 0.150 x 3.050 (B0F, 3050 mm). Together 0.72 m2, which is the **body of the cross wall above and below the opening**, opened up only because V2.6 ran the gap past x +361.6. It is wall, not a threshold. The real threshold inside the wall is 0.800 x 0.150 = 0.120 m2 and is the marble threshold line (VERIFIED by the tool). Removing the held line is right, and nothing released is lost. | VERIFIED |
| 2 | DOOR.INTERNAL.PVC, W.C. | 0 -> 1 nr | One D315 insert, frame 0.800 m, one leaf (r 0.69), between Bathroom / W.C. and Laundry: one internal door. It is PVC by the owner door rule (wet room). V2.6 held it (SYMBOL_FIT_REVIEW: an 0.800 leaf inside a 1.023 m gap); the jamb span settles the fit. | VERIFIED |
| 3 | FIN.WP.WALL_UPTURN, W.C. | 1.133345 -> 1.148 m2 | (6.54 - 0.800 door) x 0.20 = 5.74 x 0.20 = **1.148**. The delta is the stub, 0.073274 x 0.20 = +0.014655. | VERIFIED |
| 4 | FIN.WP.WALL_UPTURN, Laundry | 3.033345 -> 3.048 m2 | (16.94 - 0.900 OP-008 - 0.800 OP-010) x 0.20 = 15.24 x 0.20 = **3.048**. Delta +0.014655 as in #3. | VERIFIED |
| 5 | FIN.WP.DOORWAY, Laundry (both doorways) | 0.333491 -> 0.300 m2 | OP-008 0.900 x 0.200 = 0.180, plus OP-010 0.800 x 0.150 = 0.120, gives **0.300**. The strip is counted once, on the Laundry side: the W.C. has no doorway line, so there is no double count. | VERIFIED |
| 6 | FIN.PLASTER, Laundry | 46.196125 -> 46.350 m2 | 16.94 x 3.0 - (0.900 x 2.1 + 0.800 x 2.1 + 0.600 x 1.5) = 50.82 - 4.47 = **46.35**. Delta = the stub, 0.073274 x 2.1 = +0.153875. | VERIFIED (delta from the drawing; heights are S2 test values) |
| 7 | FIN.WALL.TILE, Laundry | 36.032125 -> 36.186 m2 | 16.94 x 2.4 - 4.47 = 40.656 - 4.47 = **36.186**. Delta +0.153875. | VERIFIED (same note) |
| 8 | FIN.WALL.TILE, W.C. | 12.962125 -> 13.116 m2 | 6.54 x 2.4 - (0.800 x 2.1 + 0.600 x 1.5) = 15.696 - 2.58 = **13.116**. Delta +0.153875. | VERIFIED (same note) |
| 9 | FIN.SKIRTING, Laundry (certain line) | 14.566726 -> 14.640 m | Wall 13.29 + column 1.35 = **14.64**. This is 16.94 - door 1.70 - the 0.60 m window OP-013 edge, which is held in the bounded line [0, 0.60] (sill not drawn). V2.6 credited half of the 0.073274 m stub, 0.036637 m, as door; it is wall, so +0.073274. | VERIFIED |
| 10 | FIN.SKIRTING, W.C. (certain line) | 5.066726 -> 5.140 m | Wall 5.115 + column 0.025 = **5.14**. This is 6.54 - door 0.80 - the 0.60 m window OP-014 edge (bounded [0, 0.60]). Delta +0.073274. | VERIFIED |

The tool already VERIFIED three more lines of the same record. I checked them again by hand:

- marble threshold 0.153491 -> 0.800 x 0.150 = 0.120 m2;
- door reveal plaster 0.783491 -> 2 x 0.150 x 2.1 + 0.150 x 0.800 = 0.75 m2;
- W.C. plaster 16.886125 -> 6.54 x 3.0 - 2.58 = 17.04 m2.

**Who is right (verdict proposals for the verifier):** ENGINE_RIGHT for V2.7.1 on all 10, with the hand calculations
above. The freelancer has no line at this level: the changes are 0.073 m of skirting, 0.15 m2 of plaster or tile and
0.015 m2 of upturn per room, below 0.1 % of any trade total, so no freelancer comparison is affected. The 0.800 m
opening is the door's frame as drawn. No door width is printed in text on the sheets (T-091 census), so the block
geometry is the only source.

## Side finding: the skirting deduction trail does not add up (proposed fix task)

The certain skirting line lists only part of what it takes off. On the released ARCH_TAKEOFF_V2.11 (Mode A, same
drawing), **20 of the 28 measured skirting lines** have `gross - sum(deductions) != measured_net`. The missing
amount totals **17.035 m**:

- In 19 lines, the missing amount equals exactly the `window_threshold` length. For example, the Laundry has gross
  16.94, listed deductions 1.70 + 0.30, which would give 14.94, but its net is 14.64. The unlisted 0.30 m is the second
  half of the 0.60 m window edge. That edge is held in the bounded line [0, 0.60], but the certain line's deduction
  list shows only 0.30 as "glazing edge".
- In 1 line (a 1F Bathroom / W.C., gross 8.70), the missing 0.016349 m is half of an unresolved 0.032698 m
  COLUMN+WINDOW edge.
- Largest gaps: GF Dining + Living 3.916 m, 1F Living 2.652 m, GF Majlis 1.955 m, 1F Master bedrooms 1.645 / 1.225 /
  0.776 m.
- The quantities are internally consistent: net = wall + column edges, and the held range carries the window edges.
  A reviewer who re-adds the printed deductions still gets a number 17.0 m too high, so the BOQ cannot be checked
  from its own trail.
- The same defect is already in V2.7.1 (Mode U: 8 of 11 lines, 11.924 m).

Proposed task: a new skirting output version (frozen methods untouched) that lists every edge taken off the certain
line, with its role and length. This means the window-threshold edge and the unresolved-edge share, each named as
"held in the bounded skirting line". The acceptance test is `gross - sum(deductions) = net` on every skirting line of
the T-019 villas and Alsenan, with 0 quantity change.

## What is not covered

- This checks the record's geometry and arithmetic, not the conventions:
  - the 0.20 m upturn is an owner standard;
  - the Mode U door height of 2.20 m is UP-DOOR-HGT-001 OWNER_STANDARD_ASSUMED, with no door height printed for OP-010;
  - whether the 0.60 m windows are sill windows is not printed, so they stay bounded.
- The V2.8 -> V2.9 14 EXPLAINED_UNVERIFIED changes are T-016b, not done here.
