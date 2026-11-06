# T-573: ceilings vs the freelancer by room group and face class, m2 and lm apart, on ARCH_TAKEOFF_V3.0.58

Worker 2, 2026-11-06, lane A, non-candidate (research only; no engine, rule / knowledge version, registry, frozen or
candidate file changed; nothing released; released default V2.9 + route G unchanged). Files: research/agents_t573/*
and tests/t573_ceiling_reconcile/* only. Development villa; not an accuracy claim. His figures are read as numbers
from the merged register tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (sheets keyed by a hash of the title, no
workbook text committed); drawing values are the merged T-271 r2b / T-283 r3 / T-281 / T-431 / T-567 ledgers, cited and
sha256-pinned, not re-measured this run. ERS read: s.2.1, 2.2, 2.4, 2.7 (no owner question: every open item is a
designer item already held or his own unprinted figure), s.3, s.4, s.7.

## 1. Physical element and classes (ERS s.2.1, R-T573-1)

Under each slab face: BOARD = the horizontal decor ceiling at the finished-ceiling level (room polygon less slab
openings and less faces of another class); BULKHEAD = vertical drop faces, run x drop, never inside BOARD;
STAIR_SOFFIT and DOME (own finishes); EXTERIOR_SOFFIT (over outside air); NO_CEILING (slab opening: no finish); COVE
(lm; an area only from a detail); PAINT = BOARD + BULKHEAD per room (Q-57 A mod (6)). Candidate V3.0.58 = the V3.0.57
ceiling lines (arch_v3058 adds only FIN.WP.ROOF lines). Asserted: each of the 31 FIN.PAINT.CEILING lines = its room's
FIN.CEILING + FIN.CEILING.BULKHEAD lines.

His side: decor sheet halls / rooms 337.57 + kitchens / baths 72.01 = **409.58 m2** (his H31 / H65, asserted row by
row); cornice runs 282.85 + 144.61 = **427.46 lm**; his decor paint 452.325 = 409.58 + cove-light strips 0.10 x
(282.85 + 144.60) = 42.745; stair soffits 24.24 + 15.75 = 39.99 sit in his WALL paint rows 18-19; one soffit row
(pool court, 19.154) in his exterior plaster. No bulkhead, dome or other soffit row.

## 2. BOARD (decor ceiling), ours - his, m2, by group (out/T573_CEILING_RECONCILE.json)

| Group | ours | his | gap | causes (close exactly) | % |
|---|---|---|---|---|---|
| GF reception + dining + entrance (incl. pantry 11.755, south dining piece 4.885) | 108.822093 | 147.96 | -39.137907 | no ceiling under light well 13.392 + pocket 1.551: -14.9434 ENGINE_RIGHT (his row ceils slab openings); stair ST-02 zone -11.6255 HELD; garden band P-2 -9.101 HELD (D-48); west strip -0.760 HELD; unlabelled spaces 0 (HELD 0 .. 5.160, location vs his row not established); -2.708007 UNRESOLVED (his row has no dimensions) | none (HELD 0 .. 26.6465) |
| GF stair room ST-01 (line HELD) | 0 | 0 | 0 | stair top 1.750 + soffit pieces HELD (soffits counted in the stair table) | none |
| GF diwaniya / master bed / driver | 49.364972 | 49.37 | -0.005028 | TOLERANCE +0.100 / -0.110 / +0.005 (finish vs structural face) | +0.40 / -0.66 / +0.06 |
| GF wet (kitchen, wash, 8 baths; 10 = 10 rows) | 35.426210 | 35.48 | -0.053790 | TOLERANCE (sum; pairing-invariant) | -0.15 |
| 1F living (group line + 2 blank parents) | 51.0496 | 38.96 | +12.0896 | ENGINE_RIGHT: the double-height ceiling over the light-well footprint, his row omits it (T-271); split not drawn, carried whole; stair 10.725 + B23 0.1725 + east dome 14.0359 HELD in neither | none |
| 1F bedrooms 1-4 | 60.698901 | 74.00 | -13.301099 | domes over the rooms -11.9226 HELD (DCR-4); -1.378499 UNRESOLVED (room sizes, T-208) | none |
| 1F dressing 1.65 x 1.80 | 2.970 | - | +2.970 | ENGINE_RIGHT (drawn, no row of his) | - |
| 1F wet (laundry + 5 baths; 6 = 6) | 28.0336 | 30.91 | -2.8764 | domes over 3 baths -3.1109 HELD; +0.2345 TOLERANCE | none |
| 2F maid / W.C. | 24.900001 | 25.20 | -0.299999 | TOLERANCE -0.230 / -0.070 | -1.17 / -1.25 |
| 2F stair-hall lobby vs his 'corridor' | 5.6258 | 7.70 | -2.0742 | UNRESOLVED (his row has no dimensions); stair box top HELD 0 .. 12.9742 (Q-72), not shown inside his row | none |
| **Total** | **366.891177** | **409.58** | **-42.688823 (-10.42 %, not a verdict)** | ENGINE_RIGHT +0.1162 (-14.9434 + 12.0896 + 2.970); HELD -36.5200; TOLERANCE -0.124317; UNRESOLVED -6.160706 | |

Like for like (groups with no HELD and no scope cause, 6 rooms + 10 GF wet): **109.691183 vs 110.05 m2, -0.358817
(-0.33 %)**. Restated from T-271 (R2 vs V2.9) to the candidate lines; the causes are unchanged, the R2 'pantry wet
+11.701' is now inside the reception group (his pantry is priced in that row).

## 3. Other classes (each its own comparison; never summed with BOARD)

- BULKHEAD vertical faces: ours 27.9345 m2 (13 lines, ASSUMED - OWNER-APPROVED, Q-48 A + Q-43) vs his none:
  NOT_IN_HIS_ROWS; GF-RFD4E1D HELD 0 .. 0.98142 (edge 6.5428 x 0.15). The fixture rule: a drop's vertical face is
  never added into the ceiling area (adverse test).
- COVE / cornice: his 427.46 lm vs ours no line (no detail drawn; T-283 ledger 288.640 m HELD, 6 faces blank): HELD,
  lm only. His 0.10 m paint strip on it is a convention, not a drawn face.
- STAIR soffits: his 39.99 (wall-paint rows) vs ours 2 lines HELD: T-281 true 22.149034 HELD + 17.840966 UNRESOLVED
  (T-561, carried; counted here once, T-561 already took them out of wall paint).
- DOME intrados: 2 lines HELD (DCR-4); he prices none: 0 gap, HELD unbounded.
- EXTERIOR soffits: ours 44.446 (5 lines) vs his plaster row 73 19.154: PL-03 pool court -6.320 ENGINE_RIGHT (his
  2 x 3.14 x 3.05 vs 12.834, T-567) + PL-01 / -02 / -04 / -05 31.612 NOT_IN_HIS_ROWS (drawn soffits over outside air,
  T-121 / T-127). No %.

## 4. Ceiling paint

Ours FIN.PAINT.CEILING 394.825677 vs his 452.325 = **-57.499323 m2** = BOARD gap -42.688823 (by the table above) +
bulkhead faces +27.9345 (he paints none) - his cove strips 42.745 (RULE_DIFFERENCE: no cove detail, owner Q-57 A mod
'actual paintable surfaces') ; GF-RFD4E1D bulkhead paint HELD 0 .. 0.981. His row 50 uses 144.60 m vs his decor
144.61 (0.001 m2, his transcription).

## 5. Verdict proposals, rule, lesson, missing

- ENGINE_RIGHT: no ceiling under slab openings (FREELANCER_WRONG to ceil them), the 1F double-height ceiling, the 1F
  dressing, the pool soffit size; NOT_IN_HIS_ROWS: bulkheads, four exterior soffits; RULE_DIFFERENCE: cove-light
  paint strips; TOLERANCE: 15 rooms and the 1F wet group within 1.6 %; HELD: stair zones, domes, band, unlabelled spaces, stair box, coves;
  UNRESOLVED 6.161 m2 board (reception -2.708, bedrooms -1.378, 2F lobby -2.074: his rows have no dimensions).
- R-T573-1 (t573_rules.py docstring, every villa): classes with their own units; groups use every line / row once;
  causes close exactly with one named remainder; % only without HELD or scope causes; VERIFIED refused; HELD never 0.
- Lesson proposal (ERS s.7): "2026-11-06 | a ceiling total compared with a reference mixes board, bulkhead, cove strip
  and stair soffit areas | each takeoff puts different faces in 'ceiling' (his cove strips and stair soffits, our
  bulkheads) | compare per face class with its own unit, never a single ceiling total | tests/t573_ceiling_reconcile |
  PROPOSED".
- Missing: finished-ceiling level per room (O-P8-02, D-40), cove detail, dome closure (DCR-4), stair soffit finish
  (T-281 HELD rows), band class (D-48), Q-72 stair box top; his room dimensions; an independent re-measure this run.

## 6. For the Checker

1. Rebuild: `python -I research/agents_t573/t573_alsenan.py --check` (byte-identical; pins in the JSON).
2. Pick GF-RC99C2A: 101.137092 + 2.800001 + 4.885 = 108.822093; his D13 137.50 + D15 10.46 = 147.96; light well
   13.392 + pocket 1.551 on the 1F slab plan S-OPENING outlines (Drive 'Alsenan chalet project', ST7757 dxf.dxf).
3. Pick 1F bedrooms: 7.4692 + 18.6747 + 18.215 + 16.34 = 60.6989 vs 17.29 + 19.46 + 18.25 + 19.00 = 74.00; west dome
   disc over 1F-RB72F22 11.5808 (r 2.21109 circle).
4. Paint: 394.825677 - 452.325 = -42.688823 + 27.9345 - 42.745.
