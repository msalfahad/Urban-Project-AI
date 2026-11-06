# T-580 MANIFEST OVERLAY DRY RUN on ARCH_TAKEOFF_V3.0.58

Worker 3 (lane I, non-candidate, backlog-permitted), 2026-11-06. Not an integration package: nothing is wired; no
candidate, released (V2.9 + route G), rule, knowledge or registry file is touched. No drawing read.

Files: `overlay.py` (R-T580-1, generic: any villa on the line-index scheme), `t580_alsenan.py` (training-villa
normalisers + checks), `in/T498_STAGE_ROWS.json` (numbers-only extract of the unmerged T-498 stage, agents/task-T-498
@ e3e2ebb5 `research/agents_t498/summary_t498.json`, sha256 inside), `out/OVERLAY_T580.json`, tests
`tests/t580_manifest_overlay/` (23). Rebuild: `python3 -I research/agents_t580/t580_alsenan.py` (`--check`).

## 1. What is overlaid

A COPY of the pinned V3.0.58 index (LINE_INDEX_V3_0_57 4,994 lines + the 5 T-507 roof WP lines = 4,999), manifests
V2 / V3 / V4 / V5 / V6 / V7 / V8 pinned by sha256, in the Lead's order. Each manifest row is one op on one line:
ADD / SET / RECODE / RETIRE / TEXT_ONLY / LEDGER / BESIDE, its stated `before` checked against the index at that step.
Refused: two packages on one line id (R1), HELD / missing printed as 0 (R2), a double count (R3). V7
PAINT_RETURN_MISSING is not applied: V8 RETURN_PAINT_FACES supersedes it (same 30 faces).

## 2. Result: 4,999 -> 5,123 lines, 0 STALE, 0 two-package lines, 0 unexplained conflicts

| # | Package (Gate B) | ops | applied | expected after (released / HELD, units) |
|---|---|---|---|---|
| 1 | T-498 (stage 74 + lintels V3 16 + host faces V5 5 + perimeter mortar 2 + lintel bars 2 + lintel end ceilings 4) | 103 | 102 + 1 NO_BEFORE | MAS.UNITS.BLACK 1,075.8 pcs (2) + 18 HELD; MAS.MORTAR.BLACK 1.367589 m3 (= stage 1.269444 + perimeter 0.039291 + 0.058854) + 18 HELD; MAS.GLUE.AAC 20.061 kg + 16 HELD 852.22 .. 885.60 kg; MAS.UNITS.WHITE 17 HELD; STR.CONC.LINTEL released 1.016 -> 0 m3 (6 HELD AT_LEAST 0.502 m3, 1 high open; 10 HELD by name, bounds beside); STR.REBAR HELD +2 AT_LEAST 63.063224 kg (high open) |
| 2 | T-423 r2 | 18 TEXT_ONLY | 18 | no quantity moves (r1: 22 text-only = 16 addressable here (2 face pieces + 14 thresholds) + 6 not (s.4); + its 2 named set-aside ceilings, unchanged) |
| 3 | T-563 PLASTER_HEIGHT_V1 (11 lines) + 11 paint pairs unchanged | 22 | 22 | FIN.PLASTER released 580.5819 -> 363.3738 m2 (4 lines -> HELD); FIN.PAINT 217.2081 unchanged |
| 4 | T-513 | 0 | - | none on this villa (0.000 m2, T-510 generality row) |
| 5 | FLOOR_FINISH_COMPLETENESS (V7) + A08 label (V8) | 4 | 4 | PORCELAIN 305.020973 -> 295.390972; WET_TILE 75.945577 -> 85.575578; FINISH_HELD 6.1275 -> 9.0975; BED.DRY +2.970 m2, m3 HELD +0.0891 .. 0.1188 |
| 6 | RETURN_PAINT_FACES (V8) | 30 | 30 | FIN.PAINT released 217.2081 unchanged; +30 HELD blank, bounds beside (26 valued faces 0 .. 23.070 m2) |
| 7 | PIER_RETURNS_EXT (with T-314) | 1 LEDGER | 1 | L-8bb83e16 stays HELD blank (2 ledger faces) |
| 8 | W17_Q76A | 2 | 2 | ARCH.WINDOW released 76.256 -> 86.126 m2 (+3.29 x 3.00); HELD line retired |
| 9 | REBAR_OMISSION | 6 | 6 | STR.REBAR +6 HELD blank; released 9,375.30576 kg unchanged |
| 10 | F package (no board row: Lead to place) | 11 | 11 | FIN.WP.ROOF 209.018867 -> 209.65844 m2 (= T-541 engine); ROOF_UPTURN 186.782544 -> 187.83416 lm; FIN.ROOF.FINISH +4.519172 m2; 7 build-up lines HELD blank |

Per-step totals (each package's change only) are in `steps[].totals_changed`; every op with its status in `rows`.
Re-run on the overlaid index (all packages together): floor census R-T564-1 C1 only 2F-ST-ARRIVAL (ENGINE_RIGHT),
C2 0, C4 0, C3 COVERED on every storey (GF residual 0.000132 = print rounding) = V7's expected after; R-T569-1 every
plastered return has one HELD paint row; the 132 T-454 / T-489 plaster bindings read their line before (class, net)
and after (HELD range) with 0 mismatches; the 4 T-455 tile bindings 0 mismatches; R-T533-1: the 12 staged material
lines on the 6 0.15 m black hosts are all HELD blank.

## 3. Conflicts (2, both EXPLAINED)

MAS.MORTAR on GF and 1F `walls t=0.20`: panel bed-joint mortar (stage) and the B9-04 perimeter joint mortar (V2) on
one host: own producer key beside, never inside (R-T520-1 / T-526 / T-532); fix row: T-498 step 6 keeps them apart.

## 4. Findings

- F-T580-1 (class not stated): V2 gives the 16 lintel rows a STATE (BOUNDED_MIN_BEARING / HELD_BY_NAME), not an index
  class. Read as HELD, released lintel concrete goes 1.016 -> 0 m3 with 0.502 m3 as the AT_LEAST low of 6 lines; read
  as RELEASED at the low with the high beside it stays 0.502 m3 released. The T-498 package must state the class per
  line before Gate B (no quantity is chosen here).
- F-T580-2 (stale identity): the T-498 stage summary still says method V3.0.58, extends V3.0.57, base 4,994 lines; on
  V3.0.58 (4,999 with T-507) its identity must be regenerated (expected 5,073 after the stage).
- F-T580-3 (NO_BEFORE): V5 glue host L-4ccc5dc2 (2F) has no stated before (the 2 others without one get theirs from
  V5 v4_to_v5); index state HELD blank, after HELD blank + conditional 63.82 .. 71.62 kg beside: state it.
- F-T580-4 (T-423 r2): the r1 branch carries `engine/source/arch_v3058.py` and `BOQ_FAMILY_MASTER_1.55.0.json`,
  both already taken by T-507: renumber (as the board says). 6 of its 22 text-only lines are not addressable from any
  committed file (5 ceiling deduction lines + the D-1F-03 strip: ids only in its private ledger); 16 + 2 set-aside checked.
- F-T580-5: the F package (V2 stream F + T-517 build-up, 11 ops) applies cleanly but has no board row; V4's stair-bed
  producers (beside HELD risers) move no line and are not overlaid.
- Version allotment if merged in this order: T-498 V3.0.59 / 1.56.0 (carries the T-525 promotion), T-423 r2 V3.0.60,
  T-563 V3.0.61, T-513 V3.0.62, then the V7 / V8 rows and F in the Lead's order (each takes the next free number).

## 5. Lesson proposal (ERS s.7)

"Before a run of Gate B packages, overlay every pending wiring row on one copy of the candidate index in merge order:
a row whose before no longer matches, a line written by two packages, a HELD printed as 0 or two trades on one host
surface there, not inside Gate B" (scope: any villa on the engine's line-index scheme; provenance T-530 .. T-569 /
T-580; test tests/t580_manifest_overlay).
