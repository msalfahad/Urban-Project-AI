# T-395 Beam concrete reconciliation: BM-GF, BM-1F, BM-2F of T-385 r2 traced to their causes

Worker 3 (lane S, backlog-permitted), 2026-10-31 15:05 .. UTC, run session_01E6cPnd5QkK9zCmE9g5m4Zj, branch
`agents/task-T-395`. Research only: no engine, candidate, released line, rule or method version changed; nothing
released. Development villa, not an accuracy claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied.

## 0. Sources and runs

Own Drive copies this run (folder "Alsenan chalet project", decoded into `.work/private` only): 'ST7757 dxf.dxf'
(`9f9d1179`, = manifest) and the concrete + rebar workbook (`ae608411`; its beam sheet, 481 cells, equals the committed
benchmark copy cell for cell). Candidate lines: the 191 STR.CONC.BEAM lines of the committed V3.0.21 file
(`research/agents_t332`), **asserted equal** (ids, element ids, valued m3) to the V3.0.29 binding of the candidate of
record (`research/agents_t387/BINDING_T387.csv`); the Lead states V3.0.31 carries the V3.0.29 structural lines
byte-identical (not re-run here). Families reproduce T-385: GF 104 lines, valued 39.329077 m3; 1F 66 lines, 22.690303;
2F 21 lines, 4.298500. Support geometry: merged T-229 input (piece ends, 36 support gaps, column outlines), T-252 ledger
r2 (runs, marks, held ranges), route G bands re-derived with `research/agents_t110/scripts/bands.py` (fit <= 0.6 mm).

```
python3 -I research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g <tmp>/bands.json
python3 -I research/agents_t395/t395_alsenan.py --freelancer <private>/concrete_rebar.xlsx --bands <tmp>/bands.json --write
python3 -I research/agents_t395/t395_spans.py <private>/ST7757_dxf.dxf <tmp>/bands.json <private>/t395/RUNS_T395.csv \
    <private>/t395/SPANS_T395.json          # then re-run t395_alsenan.py to bind the spans into the summary
```

Outputs: `.work/private/t395/RECON_T395.csv` (per storey x mark, his rows / lengths beside the engine), `RUNS_T395.csv`
(per candidate line: run, mark, section, length, held range), `SPANS_T395.json` (own edge reading), and the tracked
engine-side `summary_t395.json` (engine figures, cause terms in m3; no row, count or length of the workbook). Rules
`t395_rules.py` R-T395-1 .. 5; tests `tests/t395_beam_recon` (24).

## 1. The physical element (ERS s.2.1) and the depth basis (acceptance b, first half)

A beam is its drawn plan between its own edge lines, ended at the faces of the members that own the crossings (columns
to the slab top, T-394 R-T394-1; carrier beams), times a depth. Two readings of the depth are each one solid: FULL
(overall printed depth, slab cut at the beam faces = slab NET of the beam plan) and DOWNSTAND (depth - t, slab GROSS over
the beam plan). R-T395-1 refuses the two mixed readings (FULL + GROSS slab = b L t billed twice; DOWNSTAND + NET slab =
b L t billed nowhere).

| Storey | Engine beam depth | Engine slab | Freelancer beam depth (his column C) | Freelancer slab area vs engine NET / GROSS | Depth-basis term |
|---|---|---|---|---|---|
| GF | schedule overall depth (T-252 ledger) | NET 206.684 m2 (face area, members deducted) | the schedule overall depth on every common mark | NET (within 2.4 m2 of 206.684; GROSS 266.990) | **0.000 m3** |
| 1F | same | NET 123.477 | same | NET (within 3.5 m2; GROSS 165.632) | **0.000** |
| 2F | same | NET 44.885 | same | NET (within 0.4 m2; GROSS 54.630) | **0.000** |

Both sides take FULL depth with a NET slab: the depth basis is **not** a cause of the beam residual. Had either side
read DOWNSTAND, b x L x t on the valued runs would move 9.184 (GF) / 5.631 (1F) / 1.265 (2F) m3 between the beam and slab
families (printed in the summary as the exposure only). The slab thickness used is the printed S.S 16 CM over the beams.
SECTION is 0.000 on every common mark: his b x D equals the engine's drawn (= schedule) section on every row.

## 2. Cause split (acceptance a / c; signs engine - freelancer, m3; R-T395-3 / -4)

Per storey and mark: SECTION, HELD (held runs at their drawn length and his section), LENGTH (the rest), COUNT (a mark
with no row of his, or no drawn run). LENGTH < 0 (his longer) is THROUGH_SUPPORT up to the drawn support allowance (the
36 interior support gaps + the end support extents along the axis, column extent from its own outline: w = x extent,
d = y extent, checked on all 36 gaps); beyond it UNTRACED. LENGTH > 0 is never a support cause: RUN_COUNT where he prints
fewer rows than the drawn runs (each of his rows takes the drawn run(s) it is closest to; continuous CB marks are one
run; one row may run over contiguous runs), else UNTRACED. A held run left with no row of his leaves the HELD term (no row
on either side, carried as HELD open). Terms re-add to the residual on every mark (bookkeeping remainder 0.000000).

Residual against the sum of his rows (his printed 1F sub-total leaves his own first 1F row out: -0.128 m3, BM-ARITH,
already ENGINE_RIGHT in T-385):

| Cause | GF | 1F | 2F | Family | Verdict proposal |
|---|---|---|---|---|---|
| Labelled drawn marks with no row of his: GF B27 4.1918, B28 0.2121, CA 0.1725; 1F B25 2.8500, B19 1.6236, B5 0.8325 | +4.5764 | +5.3060 | 0 | **+9.8824** | ENGINE_RIGHT (COUNT; = T-241's 'omitted labelled marks 9.883'; B27 / B26 / B28 T-229 merged) |
| Upstand lines B20 / B23 upstand 0.20 x 0.20 x 3.00 | +0.1200 | +0.1200 | 0 | +0.2400 | traced COUNT; ENGINE_RIGHT proposed (drawn upstand, no row of his), Checker to re-look |
| Drawn runs of a mark beyond his rows: GF B1, 1F B4, 1F B6 (two of three B6 runs) | +0.2101 | +1.9089 | 0 | **+2.1191** | ENGINE_RIGHT (RUN_COUNT; labelled drawn runs), run-level binding by length (heuristic, s.6) |
| Through-support length: his rows run through the column / carrier footprint the engine leaves to the support (C1) | -2.9032 | -1.5934 | -0.5328 | **-5.0293** | RULE_DIFFERENCE (length basis; R-T395-2) |
| Dome ring in-bay line (1F, valued 0.7552; his dome rows are in the stair / dome sheet) | 0 | +0.7552 | 0 | +0.7552 | SCOPE -> T-398 (SD-DOME) |
| HELD runs at his section (GF B21 2.5246, B29 1.2640, CB2 0.6820, B24 extension 0.5629, CB3 / B3 stair piece 0.3975; 1F CB10 0.7440, B2 extension 0.0640; 2F B15 south span 0.7440, B1 two pieces 0.2240, B8 extension 0.1695) | -5.4309 | -0.8080 | -1.1375 | **-7.3764** | HELD (D-27 width conflicts, D-02, D-03, D-04; never 0) |
| Untraced: GF B7 -0.1208 (his row with no location, T-252), GF B2 -0.0112, 1F CB12 -0.1610, 2F B2 -0.0872, + rounding of three marks +0.013 | -0.1262 | -0.1535 | -0.0872 | **-0.3670** | UNRESOLVED (s.6) |
| Depth basis; section | 0 | 0 | 0 | 0 | AGREE in basis (not a cause) |
| **Residual vs his rows** | **-3.5538** | **+5.5353** | **-1.7575** | **+0.2240** | |

Closure per storey (R-T395-5): GF traced +2.0034 / HELD -5.4309 / untraced -0.1262; 1F traced +6.4968 / HELD -0.8080 /
untraced -0.1535; 2F traced -0.5328 / HELD -1.1375 / untraced -0.0872. (T-385 r2 carried all three as UNRESOLVED.)

**Column and beam families together (T-394 P3).** The engine's columns own their joint + head to the slab top
(T-394: +2.694 GF, +1.080 1F against his columns); his beams run through those supports (-2.903 GF, -1.593 1F here).
These are the same solids counted in different lines; the through term also contains carrier-beam ends (beam on beam),
which are not column joints, so the two do not pair one for one; the net of the two families' terms on GF + 1F is
-0.722 m3. The pairing per crossing (b x c x D at each column vs A x D_ctrl) is the next step (s.6).

## 3. Own face-to-face spans, 5 largest valued runs per floor (acceptance b, second half)

Own read of the edge lines on the Drive DXF (`t395_spans.py`: LINEs on 1 / 2 / 5 / S-BEAM parallel to the band axis on
its long sides, clipped to the band; S-COL.BON outlines at its ends). Engine L = valued m3 / (b x D).

| Floor | Mark / run | Engine m3 | Engine L | Own edges (handles) | Own f2f | Engine - edges | End supports (handle: extent along axis) | His mark |
|---|---|---|---|---|---|---|---|---|
| GF | B27 BM-GF-048 | 4.1918 | 5.4795 | 325 / 326 | 4.3751 | +1.1044 (= the P.C 329 gap 0.5768, through which B27 runs, + the two oblique ends, T-229 hand 5.4686) | 35C 0.854, 37D 0.854, 329 0.576 | no row |
| GF | B26 BM-GF-047 | 4.0846 | 7.3929 | 387 / 388 | 6.8584 | +0.5345 (P.C 386 gap 0.2102 + T.C end 0.32, T-229) | 371 0.267, 386 0.212, 31B 0.905 | through support |
| GF | B22 BM-GF-045 | 2.9250 | 7.8000 | 28A / 460 | 7.8000 | 0.0000 | none (beam ends) | face to face |
| GF | CB1 span 1 BM-GF-042 | 1.9400 | 7.3905 | 2A8 / 2A9 | 7.3986 | -0.0081 (band fit) | 344 0.500, 347 0.400 | through support |
| GF | B17 BM-GF-044 | 1.7654 | 5.2309 | 2F7 / 42D | 5.0991 | +0.1318 (oblique end 0.0442 m3, T-229) | 37A 1.000 | through support |
| 1F | B25 BM-1F-027 | 2.8500 | 6.9090 | 6BF / 6C0 | 6.8750 | +0.0340 (oblique end, T-229) | none | no row |
| 1F | B18 BM-1F-024 | 1.6538 | 6.3000 | 5CA / 6B0 | 6.2996 | +0.0004 | 679 1.000 | face to face |
| 1F | B19 BM-1F-025 | 1.6236 | 5.4119 | 6B1 / 6B2 | 5.3380 | +0.0739 (oblique + C9 end, T-229) | 667 0.319, 679 0.368 | no row |
| 1F | CB11 span 1 BM-1F-023 | 1.5397 | 6.8429 | 5C1 / 5C5 | 6.7079 | +0.1350 (beside-support pieces, T-229) | 66A 0.700, 69A 0.800 | through support |
| 1F | B23 span 1 BM-1F-026 | 1.1321 | 3.3544 | 5E1 / 5E4 | 2.9987 | +0.3557 (beside-support 0.45 beam at the 0.25 column 68E + oblique end, T-229) | 68E 0.800 | through support |
| 2F | B7 BM-2F-011 | 0.9900 | 6.6000 | 39A / 39B | 6.5993 | +0.0007 | none | face to face |
| 2F | B15 BM-2F-007 | 0.6480 | 2.7000 | 397 / 3AD | 2.6997 | +0.0003 | 40F 0.500, 424 0.500 | through support |
| 2F | B8 BM-2F-002 | 0.5205 | 3.4700 | 38D / 38E | 3.4697 | +0.0003 | 412 0.200, 415 0.600 | through support (incl. the held extension) |
| 2F | B3 BM-2F-010 | 0.2400 | 3.0000 | 399 / 39C | 2.9999 | +0.0001 | 41B 0.500 | through support |
| 2F | B2 BM-2F-008 | 0.2400 | 3.0000 | 398 / 3A2 | 2.9998 | +0.0002 | 418 0.200 | beyond allowance (untraced 1.09 m on the mark) |

Every straight engine length equals its own drawn edges within 0.01 m; the larger 'engine - edges' figures are the
merged T-229 additions (oblique ends, beside-support pieces, runs through carried columns), which a band-clipped edge
reading cannot see, not new differences. **His length basis is not uniform**: 3 of the 12 compared marks are face to face
(B22, B18, 2F B7), the rest run through their supports. A centre-line / overall length on a framed span is refused for
the engine (R-T395-2): the support owns that footprint.

## 4. Intersections, each counted once (against the T-387 census)

| Pair | Evidence | Result |
|---|---|---|
| beam / slab | slab lines are face areas with members deducted (V3.0.21 slab dimensions); T-387 SH04 / SH06 beam-slab items; his slab areas are NET too | counted once (beam owns its plan, full depth) |
| beam / column | T-229 / T-241: columns own their footprint to the slab top; 7 double joints deducted from the beams; T-394 R-T394-1 | counted once in the engine; his columns stop 0.75 below the slab and his beams run through: the same solid on his side in his beam rows (s.2) |
| beam / beam (carrier) | engine runs end at the carrier face (T-229 END_AT_BEAM); T-387 CB8 end DOUBLE 0.002767 + GAP 0.003406 (proposed, not changed here) | counted once; his through length into a carrier is part of THROUGH_SUPPORT |
| ring B7 / slab | T-252: ring 0.499805 billed once by the beam, no slab | counted once |

## 5. Methods side by side (ERS s.2.2)

| Method | GF beams | 1F beams | 2F beams |
|---|---|---|---|
| Owner manual method (URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1: slab net, beam full depth face to face, column to the controlling member) | the same solid as the engine's line split | same | same |
| Drawing-derived (candidate V3.0.29 = V3.0.31 structural lines) | 39.3291 valued + 10 held lines | 22.6903 + 12 held | 4.2985 + 5 held |
| Freelancer (private) | full depth, slab net, lengths through most supports, 6 labelled marks without a row | the same; first-row sub-total slip | the same |

## 6. Proposals (no line edited here) and what is open

- **No quantity change proposed** for the engine's valued beam lines: every difference against the freelancer is a
  count on his side, a length-basis rule difference, a HELD run or the dome-ring scope.
- **P1 (lane I / T-394 follow-up)**: pair each column crossing (b x c x D of the through beam vs A x D_ctrl of the column)
  so the column + beam families close together on GF / 1F (current net -0.722 m3; carrier-beam ends separated).
- **Untraced -0.367 m3** stays UNRESOLVED: GF B7 (one of his B7 rows has no location, T-252), 1F CB12 (his length runs 0.64 m
  beyond the 1.35 m of drawn supports), 2F B2 (1.09 m beyond 1.40 m); not closed by 'closer to the freelancer'.
- RUN_COUNT binds his rows to drawn runs by length (closest first; contiguous runs absorbed); the Checker should re-bind
  1F B6 (one row against three drawn B6 runs + one held) and 1F B4 from the private RECON / RUNS tables.
- **No owner question** (ERS s.2.7 not met: the held runs are designer items already listed, the rest is traced).

## 7. Rules, lessons row (proposed)

R-T395-1 .. 5 (`t395_rules.py`). Lessons row (ERS s.7): | 2026-10-31 | BM-GF -3.554, BM-1F +5.535 and BM-2F -1.758 m3
stood UNRESOLVED (T-385 r2) behind 'depth basis below slab vs full depth' | the suspected depth-basis cause was never
measured: both sides take full depth with a net slab, so the residual is six labelled marks without a row (+9.882), runs
beyond his rows (+2.119), his through-support lengths (-5.029), held runs (-7.376), the dome ring scope (+0.755) and
-0.367 untraced | a beam residual is split per storey and mark into SECTION / HELD / LENGTH / COUNT exactly; the depth
basis is read from both sides' slab areas (NET / GROSS) and depths before it is named; a through-support length is traced
only up to the drawn support allowance, an engine-longer length only by a run count; FULL + GROSS and DOWNSTAND + NET are
refused (every villa; provenance T-395) | tests/t395_beam_recon (hand villa V395 one-way slab on two downstand beams + a
continuous beam: through-support split, centre-line refused, overlap in both refused, gap refused, held as 0 refused,
ratio closure refused, mm refused, run count, section, mirror) | PROPOSED |

## 8. Checker re-measure list

- Edge lines (ST DXF): B22 28A / 460 7.800 (no support at either end, his row face to face); 1F B18 5CA / 6B0 6.2996
  with column 679 1.000 along the axis; 2F B8 38D / 38E 3.4697 + gap 415 0.600 + held BM-2F-015 1.13 + 412 0.200.
- Slab basis: his GF slab area against the engine NET 206.684 / GROSS 266.990 m2 (beam plan 60.305).
- Omitted marks: B27 (4.1918, T-229 hand), B25 / B19 / B5 1F lines in the candidate, no row of his on the beam sheet.
- Re-run section 0; `RECON_T395.csv` prints his rows beside the engine per mark.

## 9. Not done / uncertain

- V3.0.30 / V3.0.31 not reproduced; the lines are bound through the committed V3.0.21 file proven equal to V3.0.29.
- Column extents at OBLIQUE ends take the larger outline side (bound); the 36 orthogonal gaps fix w / d by axis.
- The per-crossing column / beam pairing (P1) is not done; RUN_COUNT is a length binding, not a located one.
