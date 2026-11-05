# T-541 B8-06 roof waterproofing reconciliation vs the freelancer, by component (research, unwired)

Worker 2 (lane A), 2026-11-05, claim 22:43 UTC, run session_01E6cPndu5AvN8qgGWcMDjEd. Files: `t541_reconcile.py`
(R-T541-1, any villa), `t541_inputs.py` (candidate line values + drawing values, no coordinate), `out/T541_ROOF_WP_RECONCILE.json`,
`tests/t541_roof_wp_reconcile/` (19 tests). No engine module, method, rule / knowledge version, registry or candidate
file changed; no quantity moves. Drawing by Drive title and handle only ("Alsenan chalet project",
P7757_DXF_COMPRESSED.zip -> P7757.dxf, decoded this run into .work/private).

## 1. Physical element and the freelancer basis

Every horizontal surface exposed to water that takes the membrane, and its 0.20 m upturns: the three plan roofs inside
the parapet (Q-24), the +5.50 pool-court slab and ledge (T-507 / T-529), the 2F block's own top roof +13.90 (no plan,
Q-34 HELD), the three domes as open skylights (Q-29: membrane stops, 0.20 m ring).

**F-T541-1 (new evidence): his cells are readable.** Earlier rounds (T-321 .. T-536) wrote "cells not read, workbook over
the connector limit". The Drive connector's text reader (read_file_content) returns the workbook's cell values although
the download is over the limit (formulas are not shown). His waterproofing sheet has ONE row for "roofs and annexes":
length 194.00, area 285.00, multiplier 1.00, no sub-rows; the summary rows repeat it (285.00 m2 / 194.00 m.l). Every
other row of that sheet is a measured room to 2 dp (bathroom / kitchen floors 72.01 m2, upturn = room perimeter x 1.00 =
144.61 m.l); the roof row's two whole numbers and the absence of sub-rows say it is a typed lump: **his upturn is the
boundary length of his roof outlines (lm, not m2), and neither figure can be split per roof from his side.** No
roll / lap allowance is in his row (multiplier 1.00): laps are not a cause here.

## 2. Membrane: 285.00 - 209.658440 = 75.341560 m2 (exact, Decimal)

| # | component | m2 | cause class | source |
|---|---|---|---|---|
| 1 | 2F block top roof +13.90 inside the parapet inner faces (7.700 x 6.450 = 49.665000) less the third dome | +34.390242 | HELD (Q-34, parked) | P7757 12B7 / 1292 / 1279 / 1283 re-read; lines L-3e8fe55d / L-aac1f35e HELD, never 0 |
| 2 | third dome footprint (r 2.205018, tangent to the east inner face) | +15.274758 | RULE_DIFFERENCE (Q-29 skylight) inside the HELD roof | P7757 1300 |
| 3 | two +9.70 dome footprints (circles r 2.211092) | +30.718026 | RULE_DIFFERENCE (Q-24 / Q-29: client change, open skylight) | P7757 12EB / 2F33 |
| 4 | engine polygon chords on those deductions (146.532 - 115.832 = 30.700) | -0.018026 | TOLERANCE (0.016 % of the line) | T-321 closure |
| 5 | pool-court slab +5.50 and ledge (4.906867 + 0.639573) | -5.546440 | ENGINE_RIGHT (Checker 4.9069 AGREE; T-529) | lines L-eff54f96 / L-2361d6ec |
| R | residual | **+0.523000** (0.18 % of 285) | UNRESOLVED | his single typed row |

Engine 209.658440 = 32.721 + 55.559 + 115.832 + 4.906867 + 0.639573 (valued lines, T-536 WIRING_MANIFEST_V2 values).

## 3. Upturn: 194.00 - 187.834160 = 6.165840 lm (exact)

| # | component | lm | cause class | source |
|---|---|---|---|---|
| 1 | top roof parapet inner faces 2 x (7.70 + 6.45) | +28.300 | HELD (Q-34) | P7757 re-read; T-311 2F 28.300 |
| 2 | two +9.70 dome rings (circles) | -27.785396 | RULE_DIFFERENCE (Q-24 answer: 0.20 m round a skylight) | 12EB / 2F33 |
| 3 | engine chords on the rings (27.782) | +0.003396 | TOLERANCE | T-071 |
| 4 | pool-court upturns 5.193544 + bath-window face 0.500002 + ledge 0.551614 | -6.245160 | ENGINE_RIGHT | lines L-cf8d5ed4 / L-1954878b / L-d7d1bf8c |
| R | residual | **+11.893000** (6.13 % of 194) | UNRESOLVED | his single typed row |

No upturn lm is converted to m2 anywhere (no printed upturn height in his row; the 0.20 m is the owner's rule, not his).

## 4. How unique is this decomposition (ERS s.2 step 4)

The component VALUES are drawing-derived; only the assignment of the freelancer's lump is a hypothesis. H1 (above):
inner parapet faces everywhere, no dome deducted, pool court not in his row: closes to +0.523 m2 and +11.893 lm, and is
internally consistent (one convention for all four roofs). H2 (outer faces, Q-24 option B 226.21 incl. the dome
deduction, + the top roof outer 55.08 with its dome kept) gives 281.29, residual +3.71 m2, and needs two dome
conventions at once: weaker, not excluded. If the pool court IS in his lump, H1's residuals become -5.023 m2 / +18.138 lm.
Nothing here is proof of his method; a freelancer figure is never proof (ERS s.2). The upturn residual 11.893 lm has no
drawing component left to name: his outline set (whatever it is) has about 12 m more boundary than the four inner
parapet perimeters (182.107 lm = 52.940 + 35.727 + 65.140 + 28.300); integer rounding explains at most 0.5.

## 5. Verdicts (proposals for the Checker)

- Three plan roofs and the pool court: ENGINE_RIGHT (unchanged, earlier hand checks; no ENGINE_WRONG found, so no fix).
- Dome footprints / rings (rows 2-3): RULE_DIFFERENCE (owner Q-29 client change; the design keeps concrete domes).
- Top roof (row 1): HELD, Q-34; when the Lead raises it, the drawing-derived bound is 34.390242 m2 membrane (49.665000
  with the dome kept) and 28.300 + 13.854540 (third ring) = 42.154540 lm upturn.
- Totals: membrane RULE_DIFFERENCE + HELD scope, residual +0.523 m2 UNRESOLVED; upturn UNRESOLVED (+11.893 lm).
- The line's -26.4 % is NOT a measurement gap: 99.3 % of it (74.818560 of 75.341560 m2 net) is HELD scope and an owner
  rule difference.

## 6. Lesson row (proposed, ERS s.7)

| 2026-11-05 | the freelancer's roof row stayed 'cells not read' from T-071 to T-536 and the -28 % gap was carried as one number | the binary download was over the connector limit; the text reader was not tried; the gap was never split into signed components | R-T541-1 (every villa): reconcile a freelancer row by signed physical components in exact decimals, residual as one named UNRESOLVED row, lm never into m2 without a printed height, unknown never 0, no freelancer figure as a component; read a large workbook through the text reader before calling it unreadable | tests/t541_roof_wp_reconcile (R541 by hand; adverse lm->m2, None, freelancer source, mm, unit mismatch, UNRESOLVED misuse) | proposed |

Missing: his roof outline set (no sub-rows; formulas not visible in the text reader), the top roof outline on a plan
(Q-34), the cause of the 11.893 lm.
