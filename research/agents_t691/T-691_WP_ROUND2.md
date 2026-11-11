# T-691 waterproofing round 2: F-V685-1 roof membrane, the MEASURABLE NOW pantry pieces, the 18 penetration lines

Worker 2, 2026-11-11 (lane A, research, unwired). Candidate ARCH_TAKEOFF_V3.0.67 (FIN.WP.* lines as V3.0.66). Nothing
wired or released; V2.9 + route G unchanged; no engine module, rule / knowledge version, registry or frozen file
touched. Rules R-T691-1 .. -3 in `t691_rules.py`; builder `t691_alsenan.py` (`--check`; `--dxf <private P7757.dxf>`
re-measures the roof outline, the dome radius and the twin-cell mapping from named handles); outputs
`out/T691_WP_ROUND2.{json,md}`; tests `tests/t691_wp_round2` (12, synthetic villa W691 + development villa pinned).
Drawings by Drive title only: "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55...,
re-checked) and sanitary-7757.pdf (image read: 1F at 300 dpi, the GF wet blocks at 300 dpi, 2F at 40 dpi), own
decode this run.

## (a) F-V685-1: the +9.70 roof membrane released above its own band

**Physical element (ERS s.2.1).** The flat membrane of the +9.70 terraces round the 2F block: inside the parapet /
wall faces where it turns up 0.20 (UP-WP-ROOF-001, Q-24), the two domes open (Q-24 / Q-29: membrane stops at the
dome circle with an upturn). Flat m2 and upturn lm kept apart; the finish hatch (layer 3, 2F21) is the finish extent,
not the membrane outline.

**Own measure (DXF, handles).** Face outline closed on parapets (layer 5), walls (1), windows (W) and the D band
(12E2 / 12E6); the 2F roof door gap closed on the 2F wall's outer face (1280 / 1281); the 2F block excluded.
D-band reading 146.37452 m2, wall-face reading 146.53200 m2 (D strip 0.075 x 2.100 = 0.1575). Domes CIRCLE 12EB / 2F33
r 2.211092 m: pi r^2 = 15.359013 m2 each. Net 115.65649 .. 115.81397 m2 vs the T-321 / T-328 band 115.65646 ..
115.81396 (AGREE +0.00003 / +0.00001).

**Cause of the excess (reconciled in m2).** The candidate's EXTERIOR_SPACES_V1 trace flattens every circle into an
inscribed chord polygon at 1 mm sagitta: r 2.211092 -> 105 chords -> 15.349849 m2 per dome, 0.009165 m2 less than the
disc. Two domes under-deducted 0.018329 m2. Released 115.832 - band high 115.81396 = +0.01804 = 0.018329 (named)
- 0.000289 residual (3-decimal rounding of the line; the face's own parapet arcs are chorded too). Nothing else.

**Corrected figure.** 115.81396 m2 on the candidate's own basis (wall / parapet faces, domes as circles): -0.01804 m2
(-0.016 %). Status OPEN_BOUND 115.65646 .. 115.81396 (D-BAND: what the 0.075 band at the 2F west wall foot is -
cladding, moulding or a thicker wall base - is printed nowhere; neither end chosen). The upturn line has the same
cause the other way: released 92.922 lm vs 65.140 + 2 x 13.892701 = 92.925396 lm (two 105-chord rings short 0.002073 m
each): corrected 92.925 lm (+0.0034). Rolls 17 pcs unchanged (whole-roll strips; not re-run).

**Rules.** R-T691-1 (a circular opening is deducted at pi r^2 and ringed at 2 pi r; a chord polygon's residual is
named, never left in a released number) and R-T691-2 (a released value must lie inside its own band; the excess is
reconciled to causes; a hatch on the parapet line adds nothing, a hatch larger than the face is flagged). For every
villa: a 1 mm chord tolerance over-states the net by ~4/3 pi r s per round opening (0.0092 m2 at r 2.2 m), always
upward, so any dome / skylight roof is released slightly above its band. Engine fix proposal (not made: frozen
method): a new method version deducting CIRCLE holes analytically (or adding back the segment area).

## (b) MEASURABLE NOW (pantry GF-07, Q-37 A): re-measured this run, all AGREE with T-685

| line | before | after | status |
|---|---|---|---|
| L-8090ff20 FIN.WP.WALL_UPTURN | blank | 1.400 .. 1.900 m2 (run 10.500 - door 1.000 = 9.500 lm; W10 1.000 + W09 1.500 sills unprinted) | OPEN_BOUND (D-45) |
| MISSING FIN.WP.TERMINATION open side | none | 4.500 lm (B3 4.000 + AD 0.500 = DIM 5E1) | ASSUMED - OWNER-APPROVED Q-37 A |
| MISSING FIN.WP.DOORWAY | none | 0.200 m2 (gap 1.000 x wall 0.200, 158 / 15A) | DRAWING-CONFIRMED |
| MISSING FIN.WP.DOORWAY_TRANSITION_NR | none | 1 pcs (D120 33E) | DRAWING-CONFIRMED; m2 HELD Q-35 C |

## (c) the 18 OPEN_BOUND penetration lines (17 blank + the missing pantry row)

R-T691-3: low = floor drains printed in the room (firm), high = low + W.C. pans drawn (pan outlet floor / wall not
printed). Basin and shower wastes are drawn into the FD (red lines): no extra penetration. Stacks are drawn in walls
or at high level: none in a floor. **F-T685-4 closed:** the 1F west twins (two 2.050 x 2.450 cells) mapped by
geometry: the west dome disc (2F -> 1F shift x(B3E) - x(12C9) = 44.8527 m) covers the WEST cell 1.2403 m2 and the
EAST cell 1.4221 m2; the merged T-283 ledger prints 1F-R48AA46 1.2410 and 1F-R8BDA49 1.4227 -> WEST = 1F-R48AA46
(1 FD 4"), EAST = 1F-R8BDA49 (FD 3" + FD 4" = 2). Doors / windows agree (west cell door top right, east cell door on
its east wall).

Result: 6 lines MEASURED 1 pcs (2 GF washes, basin space, kitchen, pantry, laundry), 11 lines 1 .. 2, 1F-R8BDA49
2 .. 3: total 19 .. 31 pcs (was AT LEAST 18 -> AT LEAST 19 firm, high now bounded). The 1F east bath (1F-R48CDA5) run
is tagged 'B.T.T.S.' (below the slab): the strongest sign for its high end. Missing datum for every high end: the
W.C. pan outlet type (floor S-trap through the slab or wall P-trap), on no sheet. 3 Q-34 lines stay HELD (not asked);
3 pool-court lines stay merged-unwired.

## Engine vs freelancer

Roof membrane 209.018867 -> 209.000827 m2 released (-0.0086 %), freelancer one roof line 285.00 m2 (T-071): gap
unchanged in substance (scope: Q-34 top roof, dome footprints; T-321 decomposition). Penetrations: freelancer rows
not read this run (workbook over the connector limit, T-321 note): UNRESOLVED. WHO IS RIGHT: F-V685-1 ENGINE_WRONG
(chord deduction, 0.018 m2, cause exact); pantry pieces ENGINE_WRONG omission / freelancer RULE_DIFFERENCE (as
T-685); penetrations UNRESOLVED vs freelancer, engine bound from the drawing.

## Lessons-register row (proposed, ERS s.7)

2026-11-11 | a roof membrane released 0.018 m2 above its own measured band | the trace flattened the dome circles to
inscribed 1 mm-chord polygons, which under-deduct pi r^2 by ~4/3 pi r s each, always upward | deduct a circle at pi
r^2 and ring it at 2 pi r; check every released value against its own band before release (every villa) |
tests/t691 (normal: true circle, band, residual named; adverse: hatch on the parapet line, hatch larger than the face,
mm read as m, HELD not 0, missing drain count AT LEAST never 0, unmapped twin) | PROPOSED.
