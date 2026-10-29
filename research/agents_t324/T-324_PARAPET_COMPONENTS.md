# T-324: PARAPET COMPOSITE COMPONENTS, each its own item, unit, owner trade and line (development villa; every villa by R-T324-1 .. 4)

Worker 2 (lane A), claim 2026-10-29 00:44 UTC, run unknown. Research only: no engine module, rule or knowledge file,
candidate line, released line or V2.9 cell changed; released default stays V2.9 + route G; nothing released. ERS applied:
s.2.1 (the parapet split into its physical components), s.2.2 (owner method beside the drawing method), s.2.3 / 2.4
(reconstructed from the drawn lines, reconciled in units, every residual named), s.2.7 (no owner question: the open
items are designer / specification items already held under Q-65 C, D-39 and the WP edge-detail RFI), s.3 (physical vs
payable; one physical face or edge, one row), s.4 (rules + tests), s.7 (lesson row below).

## 1. Evidence used

- Merged ledgers built on, not re-derived: T-311 run ledger and component owners (bd7b8c23), T-305 items (9d71ef09),
  T-172 / T-162 r2 parapet edges, vertical corners and the freelancer cell readings (merged pair).
- Re-measured in this run: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 `ab54dd55`),
  handles B34, CEC, CED, AC7, B3A, B3C, B35 (annex roof +4.30), B25, B33, BDB, C9E (GF terrace +5.50), 12A7, 12A5 /
  131C / 131B, 12B9, 12E2 and the sea-side outline 1308 .. 1313 (1F roof +9.70). Lengths and relations only:
  `MEASURED_T324.json` (`t324_alsenan.py --measure <dxf>`).
- The freelancer's exterior-plaster workbook (Drive, same folder, 'المساح الداخلى والسجما.xls'), sheet 1 rows 78, 79,
  83, 84, re-read cell by cell (H x F = I, columns A / B): identical to the merged T-162 r2 / T-172 readings.
- T-321 (READY 2269b347) is cited as a source reference only; every T-321 edge used here was re-measured from its handle.

## 2. What a parapet is made of, and who owns each piece

| Component | Unit | Owner trade | Candidate line | Rule |
|---|---|---|---|---|
| Outer face | m2 | FIN.EXT.FINISH | annex / 2F IN_LINE (GF / 2F finish lines), GF / 1F NO_LINE (T-305 bands; T-314 integrates) | unchanged from T-305 / T-311 |
| Inner face ABOVE the upturn top | m2 | PLASTER_PARAPET_INNER | NO LINE | R-T324-1 |
| Inner face in the UPTURN ZONE (exposed part of the 0.20 m membrane upturn) | m2 | WATERPROOFING edge detail (protection over the membrane) | NO LINE | R-T324-1 |
| Top surface (plain top, section A-A) | m2 | FIN.EXT.FINISH; a printed coping would replace it | NO LINE | R-T324-2 |
| Coping | m.l | COPING | NO LINE, UNKNOWN (none printed; ST p.14 P1 cap 'as per arc.', P2 0.30 x 0.10 cap: not keyed) | R-T324-4 |
| Drip / throat | m.l | FIN.EXT.FINISH | NO LINE, UNKNOWN (none drawn) | R-T324-4 |
| Outer / inner top arris | m.l | CORNERS (own m.l line) | NO LINE | R-T324-3 |
| Corner bead | m.l | accessory ON the arris | UNKNOWN (no specification); same edges, never a second length | R-T324-3 |
| Stop-end (free end only) | m.l | CORNERS | GF passage mouth HELD 0 .. 1.20; every other end abuts | R-T324-3 |
| Inner base junction | m.l | WATERPROOFING (the upturn's base: one edge, the upturn m.l) | IN_LINE (roof upturn lines) | R-T324-3 |
| Vertical external corners at parapet height | m.l | facade vertical-corner line | OTHER_LINE (4.000 DC + 0 .. 11.900 HELD inside the 124.700 m.l) | R-T324-3 |

Ledger: `COMPONENT_LEDGER_T324.csv`, 183 rows (103 DRAWING-CONFIRMED, 67 HELD, 13 UNKNOWN), every component id once and
every physical face / edge once (the book refuses a second row on the same face or edge).

## 3. Drawing corrections found by re-measuring (CORRECTIONS_T324.csv)

| Id | Where | Drawn evidence | Effect |
|---|---|---|---|
| C5 | annex boundary parapet | B34 runs 11.800 m to the divider CEC; T-311 NE-6 stopped at the house wall line B3A (10.400) | NEW run 1.400 m: inner face 0.700 m2, top 0.260 m2, inner arris 1.400 m.l (DC); outer face 0.600 m2 + outer arris 1.200 m.l HELD: it stands on the boundary line AC7, which T-172 reads as the boundary wall's neighbour-side line (owner HELD, Q-65 C) |
| C4 | GF terrace NE-4 | B25 18.970 m ends on the divider's east face CED; T-311 ran 19.170 across the 0.20 divider | inner face -0.100 m2, inner arris / upturn -0.200 m (DC) |
| C3 | 1F roof sea side | the roof plan draws the inner face straight (12A7 11.600 m) and the 0.20 wall line straight (12A5 / 131C / 131B); T-311 carried the 1F floor outline's bay arc NW-2 (inner 3.6931) | arc -> chord 3.2496 (NW-1 + chord + NW-3 + NW-4 + NW-5 = 11.600 exactly): inner face -0.577 m2, top -0.089 m2, inner arris -0.4435 m (DC); the outer edge at parapet level is the frame profile (HELD) |
| C1 / C2 / C6 | annex SW-3, 1F SW-2, GF SW-9 | the inner face line stops on a D band (B35 on B3C, 12B9 on 12E2, BDB on C9E); T-311 ran it to the wall face | ranges 0.200 / 0.075 / 0.405 m (D-BAND: what the band is is not printed, as T-321) |
| divider | between annex roof +4.30 and GF terrace +5.50 | CEC / CED, 0.20 x 1.300 m, in no T-311 run | faces and top UNKNOWN (no top level printed); its upturn 2 x 1.300 m is inside both roof WP lines |

Sea-side plan outline at parapet level (1308 .. 1313): 4.826 m2 over the 11.600 m inner face against 2.320 m2 for a
0.20 m wall; the 2.506 m2 excess is the frame / moulding projection (T-305 / T-172 frames item, HELD on its profile),
never parapet top (R-T324-2).

Independent closure: the drawn inner faces now equal T-321's own roof-level face reading on every roof: annex 29.628,
GF 27.365 (T-321 parapet 26.470 + 'gate stub' 0.894) .. 27.770 (+ the 0.406 D-band part), 1F 48.265, 2F 28.300 m;
divider 1.300 per roof: residual 0.000 m.

## 4. Results by component (COMPONENT_SUMMARY_T324.csv)

| Component | Annex | GF | 1F | 2F | Total | Status |
|---|---|---|---|---|---|---|
| Inner face, total (geometry) | 14.814 .. 14.914 | 13.682 .. 13.885 | 51.477 .. 56.609 | 14.150 | **94.123 .. 99.558 m2** | DC; 1F heights HELD; D-band ranges |
| of which above the upturn top | 8.888 .. 14.914 | 8.209 .. 13.885 | 41.824 .. 56.608 | 8.490 .. 14.150 | 67.411 .. 99.558 m2 | HELD (build-up above the membrane not printed) |
| of which upturn zone | 0 .. 5.966 | 0 .. 5.554 | 0 .. 9.668 | 0 .. 5.660 | 0 .. 26.848 m2 | HELD |
| Top surface | 5.997 .. 6.037 | 5.593 .. 5.674 | 9.832 .. 9.847 | 5.415 | **26.836 .. 26.973 m2** | DC + D-band ranges |
| Outer top arris | 30.542 (1.200 HELD) | 28.770 | 50.290 .. 50.569 | 29.800 | 139.402 .. 139.681 m.l | DC + HELD |
| Inner top arris | 29.628 .. 29.828 | 27.365 .. 27.770 | 48.265 .. 48.340 | 28.300 | 133.558 .. 134.238 m.l | DC + D-band ranges |
| Upturn (m.l, in the roof WP lines) | 29.628 .. 29.828 | 27.365 .. 27.770 | 48.265 .. 48.340 | 28.300 (line BLOCKED_RFI) | + divider 2.600 | IN_LINE |
| Coping, drip, corner beads | - | - | - | - | no number | UNKNOWN |

Owner method beside the drawing method: no answered owner rule measures parapet inner faces, tops, coping or drip
(OWNER_QUESTIONS_ANSWERED searched: Q-65 C material, Q-58 upturn from the same strip, Q-24 membrane inside the
parapet); the owner's notes on corners (2026-10-22 correction) make '2 m = 1 m' a half-rate PAYMENT on the full m.l
line: shown as payable beside the physical length, never converted to m2 (`ml_to_m2` refuses).

## 5. T-305's missing category resolved by component (RECONCILIATION_T324.csv)

| T-305 figure | T-305 | Now | Change and cause |
|---|---|---|---|
| parapet inner faces | 94.431 .. 99.534 m2 | 94.123 .. 99.558 m2 | -0.308 .. +0.024: C5 +0.700, C3 -0.577, C4 -0.100, C1 / C6 / C2 D-band ranges |
| parapet tops | 26.801 m2 | 26.836 .. 26.973 m2 | +0.035 .. +0.172: C5 +0.260, C3 -0.089, D-band ranges |
| 'parapet items' inner + top | 121.232 .. 126.335 m2 | 120.959 .. 126.530 m2 | -0.273 .. +0.195 (sum above); split into 3 items (face above upturn, upturn zone, top) |
| corners 576.872 m.l | parapet top arrises 271.963 + vertical 124.700 + mouth ends 43.100 + openings 137.110 | 272.960 .. 273.919 + 124.700 + 43.100 + 137.110 = 577.870 .. 578.829 | only the parapet top arrises move (+0.998 .. +1.957: C5, C3, C4, D bands); 4.000 m.l of the vertical arrises lie at parapet height and stay in the vertical line |

## 6. Against the freelancer (FREELANCER_T324.csv; comparison only)

| His row (cells) | His figure | Drawing | Difference | Cause / verdict proposal |
|---|---|---|---|---|
| 79 annex: H79 28.40 x F79 0.70 = I79 | 19.880 m2 | inner face + top 20.811 .. 20.951 | -0.931 .. -1.071 m2 | his run 28.40 = the T-311 inner run; he lacks the B34 extension (C5) and takes the top on his run: ENGINE_RIGHT on the run (B34 drawn) |
| 83 + 84 GF + 2F: 63.40 x 0.70 (J84 44.38) | 44.380 m2 | 38.840 .. 39.124 | +5.256 .. +5.540 m2 | +7.130 m of run in his cells that no plan draws (T-162 r2), now 7.5 m after C4 / C6: UNRESOLVED (his 0.70 = 0.50 face + 0.20 top: RULE agrees) |
| 78 1F: 48.47 x 1.70 | 82.399 m2 | 61.308 .. 66.455 | +15.944 .. +21.091 m2 | his 1.70 girth is printed nowhere (drawn 1.30 + 0.20 top max): UNRESOLVED (designer / his height) |
| top-line m.l, A + B of rows 78 / 79 / 83 / 84 | 420.86 m.l | outer + inner top arrises 273.0 .. 273.9 | +147 m.l | he counts 3 lines per metre (2 arrises + the base junction): RULE_DIFFERENCE (T-172) |

He has no coping, drip-on-parapet, upturn-zone or bead row for parapets: NOT COMPARED for those.

## 7. Rules, tests, lesson

- `parapet_components.py`: R-T324-1 (`inner_face_split`), R-T324-2 (`top_surface`), R-T324-3 (`stop_end`,
  `ml_to_m2` refused, `payable_ml`, `Book` edge identity), R-T324-4 (`Book`: UNKNOWN carries no number, HELD never 0).
- `tests/t324_parapet_components/test_t324_rules.py`, NON-Alsenan hand fixture: L parapet 6.00 + 4.00 m outer, 1.10 m
  high, 0.20 m thick, one convex corner, one free end: outer 10.000, inner 9.600, centreline 9.800 m, inner face 10.560
  m2 split 8.640 .. 10.560 / 0 .. 1.920 (printed cover 0.05 -> 9.120 / 1.440), top 1.960 m2, top arrises 19.600 m.l,
  stop-end 2.400 m.l + 0.220 m2; rotation 0 / 30 / -121 / 47 deg, mirror and millimetres do not move it. Adverse: top
  from a default width refused; plan outline narrower than the wall refused; outer face booked in exterior and parapet
  refused; corner bead as a second length refused; base junction as an arris refused; m.l -> m2 refused; coping /
  drip with a number while UNKNOWN refused; HELD as 0 refused; missing run / height / thickness refused.
- `test_t324_alsenan.py`: byte rebuild, every component and physical item once, HELD never 0, UNKNOWN without number,
  upturn closure on the drawn faces, sea-side chord = 12A7, B34 extension, vertical arrises OTHER_LINE.
- ERS s.7 row (proposal): 2026-10-29 | Parapet inner faces taken from the floor outline offset by the wall thickness:
  the roof plan draws the sea-side parapet straight over a 1F bay (-0.444 m), a boundary parapet continues 1.400 m past
  the house wall line, a terrace run crossed a divider (-0.200 m), three runs end on D bands; the inner face and the
  membrane upturn were one undivided m2 | the parapet was located on the storey below instead of on the roof plan that
  draws it; the upturn and the face finish were not split at the upturn top | measure every parapet component on the
  roof plan where the parapet is drawn (inner face line by handle), never as an offset of the storey outline; split the
  inner face at the upturn top (bounded HELD while the build-up above the membrane is unprinted); a plan outline wider
  than the section's wall is a projection item, not the parapet top (every villa) | tests/t324_parapet_components |
  proposed.

## 8. Held / unknown (never 0) and for the Checker

HELD: the split height of every inner face (build-up above the membrane, D-39 / T-321 stack); D bands (3 runs); 1F
heights NE-1 / SW-1 / SW-2; B34 outer face owner (boundary line AC7: T-159 counts 10.8 m of AC7 as the annex face, T-172
reads the whole AC7 as the boundary wall: one physical face in two readings, flagged for the boundary package, Q-65 C);
1F sea-side outer edge at parapet level (frame profile); GF passage-mouth stop-end. UNKNOWN: coping, drip, corner beads
(no specification), divider faces / top (no top level). For T-314: the sea-side parapet outer band of T-305 follows the
1F bay arc (NW-2 3.5283 m) while the roof plan draws the parapet straight (3.2496 m chord at the 0.20 wall line): -0.362
m2 at 1.30 m, HELD with the frame profile.

Checker re-measure list (P7757.dxf): B34 11.800 vs B3A -> CEC 1.400 and AC7 0.200 outside; B25 18.970 from CED; 12A7
11.600 and the NW inner runs; B35 / B3C, 12B9 / 12E2, BDB / C9E (D-band ends); the sea-side outline area (1308 .. 1313)
4.826 m2; freelancer cells H / F / I / A / B of rows 78, 79, 83, 84.

Files: `parapet_components.py`, `t324_alsenan.py`, `MEASURED_T324.json`, `COMPONENT_LEDGER_T324.csv`,
`COMPONENT_SUMMARY_T324.csv`, `CORRECTIONS_T324.csv`, `RECONCILIATION_T324.csv`, `FREELANCER_T324.csv`, `summary.json`;
tests `tests/t324_parapet_components/`.
