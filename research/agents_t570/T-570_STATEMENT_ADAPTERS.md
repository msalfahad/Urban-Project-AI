# T-570 reconciled-quantities statement V4 (research, unwired; for the 12-13 Nov milestone)

Worker 3 (lane I, non-candidate, integration dependency, backlog-permitted), 2026-11-06. Files: `t570_adapters.py`
(R-T570-1), `t570_build.py` -> `out/RECONCILED_STATEMENT_T570.json` / `.md` (`--check` rebuilds byte-identical),
`tests/t570_statement_adapters/` (18). The T-548 builder and the T-554 / T-557 / T-562 adapters are imported read only;
the build first rebuilds T-562 and refuses to run unless it equals its committed output. No drawing, workbook or client
data; no candidate, rule, knowledge or registry file; no quantity moves. Statement sign: reference - engine.

## What each merged report changes (every section closes to its source, residual 0)

| Report | Section | Reference | Engine valued | Net | By class (his - engine) |
|---|---|---|---|---|---|
| T-561 | NEW T-561/paint-internal (FIN.PAINT, m2) | 1,209.385 (J28 1,249.375 - soffit rows 39.99) | 217.2081 | +992.1769 | ENGINE_WRONG 23.07 (return omission, fix T-569), RD 69.8451, HELD 856.765, UNRES 46.89, ER -4.3932 |
| T-561 | NEW T-561/stair-soffit (FIN.STAIR.SOFFIT, CEILING class) | 39.99 | 0 | +39.99 | HELD 22.149034, UNRES 17.840966 |
| T-564 | T-553/floor-tile beside only | 409.58 | 387.09405 (unchanged) | +22.48595 | EXPECTED after V7: 387.094 + 2.970 ESTIMATED = 390.064 m2; engine vs reference -5.49 % as valued, -4.765 % expected |
| T-565 | NOT_COMPARABLE block (no section, no %) | NO_ROW | B1-02 225.941333 IN_SITU (+ held 8.333769 .. 9.568217, 8 blank); B1-03 none (held 119.963335 .. 128.643547 COMPACTED, 6 blank); B1-04 none (1 blank) | none | scope ENGINE_RIGHT (Checker), quantity NOT_COMPARABLE |
| T-566 | T-551/columns rows unchanged, CONFLICT beside | 28.5465 | 19.7765 | +8.77 | 4 readings (10AE C3 / C, 10E0 C8 / C7): ER 1.522 .. 1.81375, HELD 10.0575 .. 10.34925, RD -2.66625 and UNRES -0.435 in every reading; GF C3 COUNT 0 .. 0.46875 |
| T-566 | T-545/beams UNTRACED named by mark | 66.093875 | 66.321054 | -0.227179 | UNRESOLVED 0.365289 -> 0.120452 (GF B7); 2F B2 COUNT 0.2 ER (Checker), 0.11276 of it out of THROUGH_SUPPORT RD |
| T-567 | T-552/plaster-external rows restated (T-552 rows SUPERSEDED beside) | 1,502.84 gross | 0 (HELD, T-314) | +1,502.84 | RD 194.64 (domes, soffit), HELD 1,160.366924 (faces row 1,084.651424 exact both passes + boundary 107.24 + plinth -31.5245), UNRES 79.7435 (frames, drip: no line), ER 68.089576 (his rows with no face) |

Net beside, never paired with a gross: his net 1,469.9675 vs our net 1,035.18 .. 1,087.62 m2; like for like gross
1,114.8965 vs 1,166.45 .. 1,185.41 (+4.6 .. +6.3 %), net 1,082.024 vs 1,035.18 .. 1,087.62 (-4.3 .. +0.5 %).

## R-T570-1 (proposed, every villa; module docstring)

(a) a component with NO candidate line is ENGINE_WRONG with its fix row and the omission bound [0, upper] beside, never
HELD without a line (precedent F-T553-1); (b) NO_ROW is a NOT_COMPARABLE block, never 0, a difference or a %; (c) a
CONFLICT keeps the reading of record in the rows and every reading's class totals beside, never resolved; (d) gross with
gross, net with net; ROUNDING -> TOLERANCE by name; (e) EXPECTED is printed beside, never in the valued column.
Reclass tags F-T570-1 .. 7 ride on the rows and in `reclasses`.

## Open, for the Checker

- F-T570-1 classes the return paint 23.07 ENGINE_WRONG (upper bound) rather than HELD: the builder requires a held
  line and none exists until T-569 wires the 30 HELD return lines; then the row becomes HELD.
- The per-reading column classes are adapter arithmetic on the Checker-verified T-566 tables (R-T394-2 on-held rule).
- T-567's faces row merges our gross, his terms on those faces and the UNRESOLVED rows 77 / 78 / 83-84 into one HELD
  row: its split is a pass range (printed beside), the row total is exact.
- Lesson row proposal: "a statement row needs a candidate line to be HELD | an omitted element was shown as HELD
  without a line | class the omission ENGINE_WRONG with fix row and bound until the line exists | tests/t570 | OPEN".
