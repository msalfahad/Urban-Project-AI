# T-642 Checker T-180 P02 / P04 fix rows + B10-12 parapet HELD-blank lines (research, unwired; lane S)

Candidate ARCH_TAKEOFF_V3.0.57 line index (= V3.0.58 for STR.CONC.BEAM / STR.CONC.PARAPET). Drive 'Alsenan chalet
project' / 'ST7757 dxf.dxf' (sha256 9f9d1179..) read only in .work/private. No candidate line moved, nothing released,
no new rule (R-T610-1, R-T624-1 (a) / (b), R-T619-1, UP-CONC-JOINT-001, UP-QTY-STATUS-001 applied). Output:
`out/T642_FIX_ROWS.json / .md` (`bash scripts/agent_env.sh run --tree task-T-642 research/agents_t642/t642_alsenan.py
<dxf> --write`); checks in `t642_rules.py`; tests `tests/t642`. `t642_handles.py`, `t642_block.py`, `t642_texts.py`
are read-only DXF probes (stdout only).

## Method

Each strip was measured from the DXF entities by handle (own construction) before any engine figure was read, then
compared with the candidate LINE: route G rectangle + the named T-229 terms in LEDGER_T252 'adds' (R-T624-1 (b)), never
with the band rectangle alone. Route G frames were fixed on one member per storey and asserted on a second.

## Results

| item | drawing (own) | candidate line | delta own - engine | verdict proposal | fix row |
|---|---|---|---|---|---|
| (a) F-C-P04-1 1F CB12 at column 664 | faces 5DE / 5DF 0.250, column 664 0.20 flush east, 5DF runs on past it; strip 0.05 x 0.90 - B6 square 0.0125 = 0.0325 m2 x 0.75 = 0.024375 m3 | L-076a6d9e (BM-1F-017 .1) 1.079463 = rectangle 1.054688 + T-229 SUPPORT_CUT_BESIDE 0.024763 (gap 664); the rebuilt term region holds the whole strip; no other line bills it; B6 square depth = FR-T610-4 (-0.003125, merged) | -0.000388 vs the term (T-229 fit: width 0.2511 / length 0.8994 / B6 share 0.01294 vs drawn 0.250 / 0.900 / 0.0125) | ENGINE_RIGHT: billed once; NOT an omission (the Checker compared the 5.625 m rectangle, not the line) | FR-T642-1 no change |
| (b) F-C-P02-14 GF strip north of column 353 | faces 2B2 / 2B3 (single LINE entities from CB7 through column 353) to closing line 484 where the B7 arc starts; 0.20 x 0.50 = 0.100 m2 | carried once by HELD line L-efd3f780 (U-C:BEAMS:GF:BAND0030.2, route G mark B4, HELD 0.04 .. 0.12 = any W20 depth 0.40 .. 1.20); no T-229 term | drawing allows only B4 0.50 (its faces, route G mark) or B7 0.75 (arc lead-in) | NOT 'in no band': a HELD line; range narrowed (ENGINE_HELD -> low end) | FR-T642-2: SET 0.050 m3 + HELD companion 0 .. 0.025 (R-T619-1) |
| (c) GF B11 BAND0001 oblique end | faces 28F / 428 to oblique B13 face 427: edges 4.596099 / 4.554065 x 0.20 = 0.915016 m2 x 0.75 = 0.686262 m3 | L-b274a045 (BM-GF-001) 0.68655 = rectangle 0.68311 + T-229 END_SHORT_OBLIQUE 0.00345 | -0.000288 vs the line (T-229 end region 0.0046 m2 on fitted side stations vs drawn 0.004203) | ENGINE_RIGHT on the line; the Checker's -0.003159 is against the rectangle 0.683110 | FR-T642-3 no change |
| (d) F-C-P02-13 GF BAND0049 annex arc | arcs 29F / 2A0, R 1.30 / 1.10, 90 deg: 0.376991 m2; mark **B7 printed**: TEXT 482 inside block 'b7' (INSERT 47D), 0.0995 m outside the outer face at 51 deg, text 8.7 deg off the tangent; nearest member by 1.18 m (B2 band 1.28 m, CB6 face 1.59 m); SBT 1EAF B7 W20 H75 (W = ring width) | L-5bc1baae (P-C:BEAMS:GF:BAND0049) 0.282743 | 0.000000 | ENGINE_RIGHT, depth DRAWING-CONFIRMED; UNRESOLVED 0.150796 .. 0.282743 closes | FR-T642-4 no change |
| (e) 4 STR.CONC.PARAPET lines | runs from the merged T-311 / T-319 / T-324 ledger (25 runs) | blank, no cause in the T-630 table | - | 4 / 4 HELD_WITH_CAUSE: PARAPET_RC_MATERIAL (ST p.14 P1 brick on 0.30 RC upstand + cap 'AS PER ARC.' vs architect sections cast concrete; Q-65 C designer item) + PARAPET_RC_B_EDGE (D-39); at least 8.050943 m3 RC in every printed alternative, shown beside, never summed | class B (named cause) |

Parapet bounds per line (m3): 2F roof at least 1.624500 (all-RC printed part 2.7075, + 5.415 per m b_edge); annex
roof 1.799103 (2.998505 .. 3.018505, + 6.03701; run SW-3 geometry HELD); 1F roof 2.949453 (10.478455 .. 11.53235,
+ 9.84653; NE-1 / SW-1 / SW-2 height HELD); GF terrace 1.677887 (2.796478 .. 2.83699, + 5.67398; SW-9 HELD).

## B10 effect (research, unwired)

One HELD line (0.04 .. 0.12) becomes 0.050 m3 SET + HELD 0 .. 0.025. B10 low end after T-624 66.401795 -> 66.451795
m3; against his 66.093875: +0.357920 m3 (+0.54 %), each term a physical cause. Freelancer rows carry no location, so
his attribution of these strips is UNRESOLVED; his take-off has no parapet concrete row (blockwork 1.00 / 1.80 / 1.00
m): RULE_DIFFERENCE / HELD on the material, not an engine error.

## What I learned (general, every villa)

1. A Checker re-measure of a ledger-run line must read the line value and its named terms; 2 of the 3 'ENGINE_WRONG'
   findings were already billed by T-229 terms that the route G rectangle does not show.
2. A strip 'in no band' may be an unbound route G piece carried by a HELD line: search the HELD lines' plans too.
3. Mark labels can be TEXT inside a block INSERT; a mark census over model-space TEXT only misses them.

## Lessons-register row (ERS s.7, PROPOSED)

| 2026-11-08 | 4 Checker items (2 OMISSION, 1 ENGINE_WRONG, 1 UNRESOLVED depth) re-measured: 3 already billed or sourced, 1 a HELD line whose range the drawing narrows | the band rectangle was compared instead of the line (rectangle + T-229 terms); HELD unbound pieces not searched; a mark drawn as a block INSERT not read | compare a drawn strip with the line's decomposition and every line's plan (RELEASED billed, HELD drawn); read block-inserted mark texts before calling a depth unsourced (every villa) | tests/t642 normal + adverse | PROPOSED |

## Missing / uncertain

FR-T642-2's B4 reading (low end) rests on face continuity + the route G mark; B7 stays as the HELD companion until a
section through the annex corner is read. Residuals (a) -0.000388 and (c) -0.000288 m3 are T-229 fitted-plan effects
inside the 0.001 m3 named-add tolerance; not re-billed. Parapet quantities stay HELD on the designer answer.
