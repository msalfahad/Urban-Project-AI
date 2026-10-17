# Before / after quantity comparison (deliverable 11)

Before = ARCH_TAKEOFF_V2.2 (frozen behaviour, byte-identical to the Phase 2B-0 snapshot); after = ARCH_TAKEOFF_V2.3
on the same drawings and inputs. Released = SOURCE_DERIVED / MEASURED lines; PROVISIONAL lines are listed apart and
never confirmed. Reference plan: aggregates only. U = no heights; A = the synthetic heights facts (plaster / paint
3.0 m, wall tile 2.4 m, doors 2.1 m). Items not listed are unchanged.

## 1. Synthetic villa

| Item | U before | U after | A before | A after | Rule | Hand check |
|---|---|---|---|---|---|---|
| FIN.WP.FLOOR (m2) | 13.44 | 31.36 | 13.44 | 31.36 | UP-WET-001 | + kitchen 2.8 x 6.4 = 17.92 |
| FIN.WP.UPTURN (m2) | 4.16 | 7.84 | 4.16 | 7.84 | UP-WET-001 / UP-WP-002 | + 2 x (2.8 + 6.4) x 0.20 = 3.68 |
| FIN.WP.DOORWAY (m2) | 0.32 | 0.50 | 0.32 | 0.50 | UP-WP-003 | + kitchen doorway 0.90 x 0.20 |
| FIN.SKIRTING (lm) | 104.20 | 86.70 | unchanged | unchanged | UP-SKIRT-001 / UP-CER-004 | U: kitchen 17.50 lm not applicable (full-height tile); A: the explicit 2.4 m tile is not full height, skirting stays |
| FIN.WALL.TILE (m2) | blocked | blocked | 44.76 | 84.78 | UP-FIN-WALL-001 | A: + kitchen tile at 2.4 m (U: no height) |
| FIN.PAINT (m2) | blocked | blocked | 308.55 | 257.49 | UP-FIN-PAINT-001 | A: kitchen paint replaced by tile + a flagged band |
| FIN.MARBLE.THRESHOLD (m2) | - | 0.50 | - | 0.50 | UP-THR-001 | 0.16 + 0.18 + 0.16 |
| FIN.FLOOR.PORCELAIN (m2) | 141.28 | 141.84 | 141.28 | 141.84 | UP-THR-001 | + dry doorway strips 0.18 + 0.18 + 0.20 |
| FIN.FLOOR.PORCELAIN PROVISIONAL (m2) | - | 0.20 | - | 0.20 | UP-THR-001 | entrance strip 1.00 x 0.20 (external doorway) |
| FIN.PLASTER door jambs PROVISIONAL (m2) | - | 6.34 | - | 6.10 | UP-FIN-PLASTER-001 | 6 doors: 2 x 0.2 x H + 0.2 x w, H = 2.20 / 2.10 |

Lines: 85 -> 95 (both modes). Unresolved items: 51 -> 39 (U), 33 -> 31 (A). Questions an approved rule already answers
(A): 13 -> 0 (U), 9 -> 0 (A).

## 2. Reference plan (aggregate)

| Item | U before | U after | A before | A after |
|---|---|---|---|---|
| FIN.WP.FLOOR (m2) | 53.143 | 62.773 | 53.143 | 62.773 |
| FIN.WP.UPTURN (m2) | 26.045 | 28.945 | 26.045 | 28.945 |
| FIN.WP.DOORWAY (m2) | 1.835 | 2.035 | 1.835 | 2.035 |
| FIN.SKIRTING (lm) | 197.517 | 185.517 | unchanged | unchanged |
| FIN.WALL.TILE (m2) | blocked | blocked | 161.911 | 192.361 |
| FIN.PAINT (m2) | blocked | blocked | 269.484 | 230.334 |
| FIN.MARBLE.THRESHOLD (m2) | - | 0.74 | - | 0.74 |
| FIN.FLOOR.PORCELAIN (m2) | 167.189 | 170.998 | 167.189 | 170.998 |
| FIN.FLOOR.PORCELAIN PROVISIONAL (m2) | 150.180 | 152.493 | 150.180 | 152.493 |
| FIN.PLASTER door jambs PROVISIONAL (m2) | - | 19.32 | - | 18.60 |

Lines: 434 -> 458 (U), 444 -> 469 (A). Unresolved items: 271 -> 213 (U), 230 -> 226 (A). Already-answered questions
(A): 66 -> 0 (U), 47 -> 0 (A). No negative quantity; ledger conservation holds; CONFIRMED_MISSING 0 in every run.

## 3. Doors (scenario views; not BOQ line changes)

Door BOQ lines are unchanged (the drawn doors). The new OWNER_REQUIRED view shows the owner opening standard beside
them: villa +1.00 m of enlargement over 5 doors; reference plan +2.80 m over 16 doors (1.10 internal, 1.40 bathroom,
0.30 external). Door areas move from BLOCKED (no height) to ASSUMED on the owner reference heights, and to CONFIRMED
when a source height is given.

## 4. What did not change (by construction and by test)

- Every line outside the owner wet-area rooms, the doorway strips and the door / passage jamb lines is identical in
  V2.2 and V2.3 (`test_v2_3_changes_only_the_lines_the_registry_names`, both modes).
- Room areas and perimeters, openings and their widths, door elements and their CAD widths are identical
  (`test_no_drawn_dimension_is_replaced`).
- V1, V2, V2.1 and V2.2 outputs: 308 of 308 snapshot files byte-identical (`FROZEN_INTEGRITY.md`).

## 5. Interpretation

The V2.3 changes are owner-rule applications, not accuracy claims: they make the BOQ follow the approved Urban scope
(wet kitchens and pantries, marble thresholds, no paint over porcelain, no skirting on full-height tile, jamb plaster)
and they stop asking questions the owner has answered. Whether the resulting quantities match an independent take-off
is not measured here (blind scoring is not started in this phase).
