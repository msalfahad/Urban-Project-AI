# T-593 WIRING MANIFEST V10 + OVERLAY DRY RUN on ARCH_TAKEOFF_V3.0.58

Worker 3 (lane I, non-candidate), 2026-11-07. Not an integration package: nothing is wired; no candidate, released
(V2.9 + route G), rule, knowledge or registry file is touched; no drawing read (every figure from the committed,
Checker-merged outputs of T-592, T-585, T-501 and the V9 manifest, sha256-pinned in the JSON). Files: `manifest_v10.py`
(R-T593-1), `out/WIRING_MANIFEST_V10.json`, `tests/t593_manifest_v10/` (17). Rebuild:
`python3 -I research/agents_t593/manifest_v10.py` (`--check`).

## 1. Overlay (R-T580-1 / R-T588-1 code, read only)

A COPY of the V3.0.58 index (4,999 lines) takes V2 .. V9 in the T-588 order, then DOOR_STEPS and STAIR_SKIRTING_FORMS:
**5,124 lines, 0 STALE, 0 two-package lines, 0 unexplained conflicts; every line V10 does not write is identical to the
V9 overlay; T-412 stair edge census still 0 doubles / 0 orphans (89 edges).** The one flagged row is T-580's own
NO_BEFORE (L-4ccc5dc2), not a V10 row. One op ABSORBED by name (R-T593-1 (f)): T-423 r2's TEXT_ONLY on the D-GF-05
threshold line L-c8b5c7f7 (no quantity, same before) is carried by the V10 door-step row on that line, so the line has
one Gate B unit (R1 kept); T-423 r2 now 17 ops. New ruling (10 FIN.STAIR conflicts, EXPLAINED): SLOPED and ZIGZAG on
one STAIR-SKIRT piece are the two forms of one skirting (ORR-007).

## 2. Rows (before = the V9 overlay; evidence from the verdict line printed in each row)

| Package | Line(s) | Before | After | Class | Evidence |
|---|---|---|---|---|---|
| DOOR_STEPS FR-T592-1 | 4 house threshold lines (D-GF-01 / 03 / 05 / 09) | 0.2 / 0.18 / 0.2 (R) / 0.18 m2 | unchanged; BESIDE: step **1.000 / 0.900 / 1.000 / 0.900 lm, nr 4 = 3.800 lm**, riser 0.150 / 0.135 / 0.150 / 0.135 = **0.570 m2**, nosing 3.500 lm attribute | as before | VERIFIED (T-592 07:59 (f)), beside figures only |
| DOOR_STEPS FR-T592-2 | D-GF-15 threshold line (HELD blank) | HELD blank | unchanged; BESIDE gate step 1.000 lm / riser 0.150 m2 (nosing 0.900), PARTIAL, own row, not in the house total | HELD | PARTIALLY VERIFIED (outer level not re-read) |
| STAIR_SKIRTING_FORMS | 13 two-form pieces x 2 lines | HELD blank | exact bound per form: SLOPED sum **17.009049**, ZIGZAG sum **23.300481** lm | HELD_RANGE (low = high) | PARTIALLY VERIFIED (T-585 05:58) |
| | MS1-L.W2 / MS1-U.E2 / MS1-U.E3b / MS2-L.W2 / RS-S.S0 (sloped) | HELD blank | 0 .. 1.233936 / 1.052389 / 0.350796 / 1.230432 / 0.232143 | HELD_RANGE | HELD |
| | MS2-TR.N (zigzag, step) | HELD blank | 0 .. 0.168 | HELD_RANGE | HELD |
| | MS1-T.W + MS1-T.N (sloped) | HELD blank | unchanged; pair bound 2.350 .. 2.620191 BESIDE both | HELD | PARTIALLY VERIFIED |
| | the other form of held pieces, RS-C.OUT | HELD blank | unchanged (no bound formed), by name | HELD | HELD |
| NO_LINE | E1 landing skirting | no line | no line: NOT_IN_DRAWING (3.500 lm geometry named only; ENGINE_OMISSION withdrawn, F-C-T585-1) | NO_LINE | register 08:15 |
| NO_LINE | yard skirting (46 faces) | no line | no line: 0 DRAWING-CONFIRMED; wall foot 59.582 lm NOT_IN_DRAWING named; UNRESOLVED 0 .. 11.61 | NO_LINE | T-585 05:58 |

Every house pay length = its T-325 strip width, and pay lm x 0.200 wall depth = the line's own m2 (0.200 / 0.180 /
0.200 / 0.180): the step binds the right line. Replaces FR-T584-2 (3.50 lm edge, 0.390 m2 + D-GF-09 HELD 0 .. 0.270).

Totals moved (V10 vs V9 overlay): only FIN.STAIR.SKIRTING.SLOPED (HELD low 0 -> 17.009049, high 0 -> 21.108745,
blank 22 -> 4) and .ZIGZAG (low 0 -> 23.300481, high 0 -> 23.468481, blank 22 -> 8); released 0 on both, unchanged.
Flight lower bound 17.009049 + winder low 2.350 = 19.359049 lm (= T-585). Door steps move no total (beside figures).

Engine vs freelancer: door steps ours 3.800 lm house (+1.000 gate) vs his 7.70 lm / 6 nr: -3.90 / -2.90 lm, UNRESOLVED
(SCOPE: no door id), no %. Yard skirting 0 vs his 81.32 lm: RULE_DIFFERENCE / FREELANCER_SCOPE. Stair skirting: two
forms, ORR-007 open, no %.

## 3. Findings

- F-T593-1: T-592 prints owning_line null for the gate, but V3.0.58 has a HELD-blank ARCH.THRESHOLD line for D-GF-15
  (L-56acf345); the gate step is beside it as its own row; its strip m2 (1.000 x 0.200 = 0.200) is not wired.
- F-T593-2: the yard porch / pool-court faces UNRESOLVED 0 .. 11.61 lm (OD-1) have no HELD line (absent, not 0): Lead.
- F-T593-3: the house threshold lines hold their m2 as HELD exact bounds (3) or RELEASED (D-GF-05); V10 does not move them.

## 4. Lesson proposal (ERS s.7)

"One element, one line, several measures: a step that is the threshold stone is printed beside the threshold line and
proved to bind it (pay lm x wall depth = the line's m2); two pending packages on one line merge by absorbing the
text-only op by name, never by a second line" (any villa on the line-index scheme; T-592 / T-593; tests/t593_manifest_v10).
