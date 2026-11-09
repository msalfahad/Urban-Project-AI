# T-562 statement adapters V3: T-551 (B10), T-553 (B3 floor tile), T-559 on B9, T-556 on B5 (research, unwired)

Worker 3 (lane I), 2026-11-06, claim 13:01 UTC, run session_01E6cPnek9gHsQvAi5WHxsJC. Files: `t562_adapters.py`
(R-T562-1, any villa), `t562_build.py` -> `out/RECONCILED_STATEMENT_T562.{json,md}` (`--check` rebuilds byte-identical),
`tests/t562_statement_adapters/` (20 tests). The T-548 builder, the T-554 and T-557 adapters / builders are imported
read only; every section is closed by the T-548 builder (R-T548-1). No engine module, method, rule / knowledge version,
registry or candidate file changed; no quantity moves (`released_quantities_changed` 0). Inputs: the merged report
JSONs T-551 (b6e52d40), T-553 (b6e52d40), T-556 / T-559 (431ac67f), the T-292 opening ledger (host walls), the T-543
wall register inputs and LINE_INDEX_V3_0_57 (sha256 of each in the statement provenance). No drawing, workbook or
client data read; no Drive access needed.

## 1. New and restated sections (reference - engine; + = in the freelancer's figure only)

| Section | Unit | His | Engine valued | Net | Gross abs | Classes (net) | Engine bounded |
|---|---|---|---|---|---|---|---|
| T-551/columns | m3 | 28.5465 | 19.7765 | +8.770 (30.72 %) | 21.407 | ER +1.522, RD -2.66625, HELD +10.34925, UNRES -0.435 | AT_LEAST 28.9445 .. OPEN |
| T-551/necks | m3 | 8.805 | 0 | +8.805 | 8.805 | HELD +8.805 (36 lines) | AT_LEAST 3.075 .. OPEN |
| T-551/lift-walls | m3 | 2.40 | 0 | +2.40 | 2.40 | ER +0.75 (scope double), HELD +1.65 | AT_LEAST 0 .. OPEN |
| T-551/footing-line | m3 | 77.6305 | 67.6945 | +9.936 (12.80 %) | 11.28 | ER -0.628, HELD +10.564 | 77.1204 .. 77.8432 (his inside) |
| T-551/blinding | m3 | 47.055 | 12.734438 | +34.320562 | 34.320562 | HELD +34.320562 (one row; split beside) | AT_LEAST 20.374812 .. OPEN |
| T-553/floor-tile | m2 | 409.58 | 387.09405 | +22.48595 (5.49 %) | 41.586124 | RD +15.941912, EW +2.970 (fix T-564), ER +0.797732, TOL -0.028416, UNRES +2.804722 | 387.09405 .. 387.32405 |
| T-543/blockwork (restated) | m2 | 1,260.6895 | 467.7925 | +792.897 (unchanged) | 920.681663 | ER 107.00108, RD 68.185508, HELD 561.2232755, TOL -2.0193005, UNRES 58.506437 | unchanged |
| T-552/plaster-internal | m2 | 1,209.385 | 240.2781 | +969.1069 (unchanged) | 1,014.7746 | unchanged | unchanged |

Blinding stays its own trade (plain concrete, R-T551-3): no total adds it to a structural figure. Every T-557 section
other than T-543/blockwork and T-552/plaster-internal is identical to the T-557 statement (checked in the build and by
test); in those two only the targets change (named below), every other row keeps name, delta, class, status and ids.

## 2. B5 plaster: T-556 supersedes the T-557 restatement (R-T562-1 (a))

CURRENT (T-556, R-T556-1, Checker 10:20): the 4 released dry lines 217.2081 m2 -> HELD (BOUNDED) **262.01799 ..
262.05199 m2**; all 11 dry lines 840.64581 .. 895.89641 m2; per line beside with zone and status. SUPERSEDED, kept and
labelled: T-557 261.77493 .. 269.32863 (W03 kept at the paint height, floor build-up used under roofs; GF-15 over by
3.268 m2, Checker error recorded). The four released height rows stay ENGINE_WRONG (fix T-556; the candidate still
carries the paint height until T-558 / T-563 are wired). Method vs freelancer on the same 11 rooms (1,006.05 vs 924.205,
+81.85 m2, +8.9 %) is printed beside as a HELD method figure, never in the engine columns.

## 3. B9 blockwork: T-559 takes the openings leftover to element level (R-T557-1 (e), R-T562-1 (b))

The four UNRESOLVED openings rows (GF -5.78, 1F -8.499, 2F -2.165, his 20 cm -9.84 = -26.284) are replaced by T-559's
opening-by-opening rows (exact). Each row takes the engine status of its own host wall (T-292 ledger) and the wall's
V3.0.58 state: 33 of the 53 terms sit on HELD walls (GF-W04 / W06 / W16 / W17 / W18 / W24 / W27 / W32, 1F-W07 / W11 / W16, every
2F wall on D-39) or are held openings, so **F-T562-1 moves ER -2.8555, RD -2.46, TOL +0.0105 into HELD** (source class
kept on each row). The 1F per-run parapet heights 7.6306805 stay HELD (F-T557-6; T-559 keeps them ENGINE_RIGHT in its
own table: guard `verify_per_run_held`). Independent route (test): every one of the 25 moves names a host wall that T-543's own HELD rows list; the one held term in a valued wall is the held opening W17 (1F-W25), source class HELD. The three below-finish ENGINE_RIGHT rows (68.4188) now carry T-559's answer to
the F-C-T550-1 open point: 32 ST bands under the parapets, each carried once by a live B10 line, 0 omitted. UNRESOLVED
25.922437 -> **58.506437** (projections 41.25, wall-length census +15.0002, parapet lengths +7.44505 / -11.48877,
counts +6.30), gross 86.925589.

## 4. Moves of the engine side and of the class list (each rides on its row as `reclass`)

| Tag | Section | Move | Delta | Why |
|---|---|---|---|---|
| F-T562-1 | B9 openings, 25 rows | ER / RD / TOL -> HELD | -5.305 | host wall HELD or opening held (R-T548-1 (e)) |
| F-T562-2 | columns GF C3, 1F C8, 1F C9 | COUNT ER -> HELD | -1.77975 | the drawn member beyond his count is a HELD line (R-T394-2) |
| F-T562-3 | floor tile garden band + curb | HELD -> UNRESOLVED | +9.705 | no floor-tile line, own or cross-family (R-T554-1 (d)); D-48 |
| F-T562-4 | columns HEIGHT_OPEN | TRACED_SPLIT_OPEN -> UNRESOLVED | -0.435 | not a class; named (R-T562-1 (c)) |
| F-T562-5 | blinding | RD -> HELD (one row) | +26.680188 (low end; high end +24.837043) | the HELD / RD split moves with the held lines (R-T562-1 (c)) |

## 5. Verification labels (R-T557-1 (a))

CHECKER_CONFIRMED only where the Checker's verdict re-measured or classed it: T-551 column COUNT GF C11, GF C9, 1F C9
(the three marks the verdict names; it reports 5 / 9 marks, the other two are not identifiable from its text, so they
stay WORKER_PROPOSED), JOINT_HEAD, HELD, HEIGHT_OPEN, necks, lift, footing COUNT / OVERLAP / HELD, blinding; GF C3 is
WORKER_PROPOSED and names T-566 (rests on the T-217 / T-394 mark registration). T-553: dressing ENGINE_WRONG, dewaneya,
stair / arrival / lift / strip RD, the band, and the three UNRESOLVED rooms the Checker named. T-559: HELD openings,
door-head RD, counts. Everything else WORKER_PROPOSED.

## 6. Verdict proposals, lessons, what is missing

No new engine or freelancer verdict: the statement carries the Checker's. For the Checker: F-T562-1 .. 5 are mine (the
reports' causes are kept on every row); F-T562-3 makes the floor-tile HELD column 0 (the band is a designer item D-48
without a floor line: an element-register question for the Lead, not an owner question). Lesson proposal (ERS s.7):
"the B9 openings census was one UNRESOLVED row per floor; split by opening, 33 of its 53 terms sat on HELD walls and 25 would
have entered ENGINE_RIGHT / RULE_DIFFERENCE | the floor row carried the floor's mixed state | when a report splits a
row to element level, the engine status is taken per element from its own candidate line, never from the summed row |
tests/t562_statement_adapters | CLOSED by R-T562-1 (b)". Missing: T-560 / T-561 / T-565 / T-567 / T-568 not merged
(pending); F-T553-1 / -2 wiring (T-564); the T-551 per-mark COUNT table is the report's s.2 text (asserted to the JSON
storey sums; the JSON carries storey totals only).
