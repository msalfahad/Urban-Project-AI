# T-557 statement adapters: T-545 beams, T-547 wall tile, T-552 plaster, T-550 on blockwork (research, unwired)

Worker 3 (lane I), 2026-11-06, claim 09:00 UTC. Files: `t557_adapters.py` (R-T557-1, any villa), `t557_build.py` ->
`out/RECONCILED_STATEMENT_T557.{json,md}` (`--check` rebuilds byte-identical), `tests/t557_statement_adapters/` (17
tests). The T-548 builder and the T-554 adapters are imported read only; every section is closed by the T-548 builder
(R-T548-1). No engine module, method, rule / knowledge version, registry or candidate file changed; no quantity moves.
Inputs: the merged report JSONs (T-545 e533bc87, T-547 47d74505, T-550 f052dfeb, T-552 0106dbfb), `t552_inputs.py`
(line split) and LINE_INDEX_V3_0_57 (sha256 in the statement provenance). No drawing, workbook or client data read.

## 1. What each new section is (physical element as the source report defines it; no re-measure here)

| Section | Unit | Reference (freelancer) | Engine valued | Difference | Classes (ref - engine) |
|---|---|---|---|---|---|
| T-545/beams B10-07 | m3 | 66.093875 (row sum; printed 65.965875 beside) | 66.321054 (110 lines) | -0.227179 (-0.34 %) | ER -12.996722, RD +5.027836, HELD +7.376418, UNRES +0.365289 |
| T-547/wall-tile B4 | m2 | 433.83 | 340.3038 (12 lines) | +93.5262 (21.56 %) | ER +30.672, RD -75.5356, HELD +138.39, TOL -0.0002 |
| T-552/plaster-internal B5 | m2 | 1,209.385 gross (net 1,151.1375 beside) | 240.2781 (4 dry + 26 returns) | +969.1069 (80.13 %) | ER -4.3932, EW +1.62315, RD +68.22195, HELD +856.765, UNRES +46.89 |
| T-552/plaster-external B5 | m2 | 1,502.84 gross (net 1,469.9675 beside) | 0 | +1,502.84 | ER +6.32, RD +194.64, HELD +1,128.9865, UNRES +172.8935 |
| T-543/blockwork B9 (restated) | m2 | 1,260.6895 | 467.7925 | +792.897 | ER +109.47008, RD +69.625508, HELD +589.8982755, TOL -2.0193005, UNRES +25.922437 |

Bounded engine ranges (R-T548-1 (f), candidate held bounds only): beams AT_LEAST 74.693883 .. OPEN (5 held lines
unbounded); tile AT_LEAST 340.3038 .. OPEN (the 6 HELD lines carry no candidate bound; T-547's drawing-derived bounds
102.2085 .. 144.1735 are printed beside, never in the range); plaster internal AT_LEAST 728.4791 .. OPEN (the dry held
bounds are at the G1 paint height, the ENGINE_WRONG basis: noted beside); external AT_LEAST 0 .. OPEN.

## 2. Classes as the Checker classed them (R-T557-1 (a)-(c))

- T-545 PARTIAL: COUNT (+9.882457 m3 by floor GF 4.576422 / 1F 5.306035) CHECKER_CONFIRMED (own B27 re-measure, his rows
  read); RUN_COUNT, UPSTAND, DOME_RING, THROUGH_SUPPORT, UNTRACED and the HELD shares WORKER_PROPOSED. HELD rows name the
  floor's held lines carrying his share (GF 6 lines 5.430918, 1F 3 lines 0.808, 2F 4 lines 1.1375; B24 his share ABOVE
  the engine high, F-T545-1).
- T-547: every class CHECKER_CONFIRMED (Checker WHO IS RIGHT; status PARTIALLY VERIFIED, 1F-08 own re-measure).
- T-552: the height rows of the 4 RELEASED dry lines (GF-15 -1.07685, 1F-01 +0.885, 1F-04 +0.870, 2F-03 +0.945) move from
  the report's RULE_DIFFERENCE to **ENGINE_WRONG, fix row T-556** (F-T557-2; Checker: height basis ENGINE_WRONG by own
  check). The point difference shown is against the WRONG engine height; the restated lines are beside as HELD
  (BOUNDED): 217.2081 -> **261.77493 .. 269.32863 m2** (4 lines), all 11 dry lines missing 146.4144 .. 171.2304 m2, never
  in the engine columns. `verify_engine_wrong` refuses a statement where any of the four sits in ENGINE_RIGHT /
  TOLERANCE / RULE_DIFFERENCE or is missing.
- T-550 on T-543: the parapet residual 71.4657775 UNRESOLVED is replaced by T-550's parts (exact); concrete below the
  finished roof 68.4188 ENGINE_RIGHT (engine status NONE: no masonry by scope) with the **F-C-T550-1 wording: the class
  rests on downstand geometry, not the hatch**, and the unchecked point (a released beam line carrying the edge
  downstand) stated; length census +7.44505 / -11.48877 UNRESOLVED; projections 41.25 UNRESOLVED (element not found:
  the only 7.50 printed is the GF glazed facade 4E9); openings -26.284 and wall lengths +15.000157 UNRESOLVED (named).
  The 41.05128 RC upstand row (F-C-T543-1) now records H1 MEASURED. UNRESOLVED 101.4319345 -> **25.922437 m2**.

## 3. Engine side first: the listed moves (R-T557-1 (b); every move rides on its row as `reclass`)

| Tag | Where | Move | m2 | Why |
|---|---|---|---|---|
| F-T557-1 | plaster internal, 7 HELD dry lines | height RD / length ER -> HELD | +78.12695 (13 rows) | component on a HELD line (R-T548-1 (e)) |
| F-T557-2 | plaster internal, 4 released lines | height RD -> ENGINE_WRONG | +1.62315 | Checker ENGINE_WRONG, fix T-556 |
| F-T557-3 | plaster shaft, 3 HELD lines | his box vs drawing ER -> HELD | +13.85 | no shaft face valued |
| F-T557-4 | plaster external, 15 his rows | drawn faces + his vs drawn merged -> HELD | +89.0153 moved (bridge-lo split) | facade lines HELD; merging removes the bridge choice (the two bridges differ only in the split) |
| F-T557-5 | plaster external, rows 61 / 75 / 92 | HELD -> UNRESOLVED | +79.7435 | no candidate line (FIN.EXT.FRAME, FIN.EXT.DRIP absent; R-T554-1 (d)) |
| F-T557-6 | blockwork parapets | per-run height ER 7.6306805, +13.90 length RD 0.75 -> HELD | +8.3806805 | parapet face above the upstand HELD (material Q-65 C), as F-T554-2 |

Each new section's class totals equal its report's own by-cause totals moved exactly by these rows (checked in
`t557_build.check_class_moves`); the blockwork section equals T-554's + T-550's own by-cause change + F-T557-6 (checked);
every other T-554 section is row-for-row unchanged (test).

## 4. What I learned, what is missing

Lesson proposal (ERS s.7): "a reconciliation report's ENGINE_RIGHT on a HELD line (his figure vs the drawing) entered the
statement as engine agreement | the source pairs compared him with the DRAWING, not with a valued engine line | the
statement classes by the engine side first (HELD line -> HELD, no line -> UNRESOLVED), source cause beside |
tests/t557_statement_adapters | CLOSED by R-T557-1 (b)". Missing / for the Checker: the F-T557-1..6 moves are mine, not
the reports' (the source cause is kept on every row); the restated plaster bound waits on T-556 and the build-up b
(D-39); T-551 / T-553 / T-559 / T-560 / T-561 not yet merged (pending in the statement); the frame-band and drip rows
have no candidate line (a scope question for the Lead's element register, not an owner question).
