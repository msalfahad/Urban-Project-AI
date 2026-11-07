# T-604 WIRING MANIFEST V12 + OVERLAY DRY RUN on ARCH_TAKEOFF_V3.0.58

Worker 3 (lane I, non-candidate), 2026-11-07. Not an integration package: nothing is wired; no candidate, released
(V2.9 + route G), rule, knowledge or registry file is touched; no drawing read (every figure from the committed,
Checker-merged outputs of T-601 (2a7ad738) and T-602 (6d211198) and the V10 / V11 manifests, sha256-pinned). Files:
`manifest_v12.py` (R-T604-1), `out/WIRING_MANIFEST_V12.json`, `tests/t604_manifest_v12/` (25). Rebuild:
`python3 -I research/agents_t604/manifest_v12.py` (`--check`).

## 1. Overlay (R-T580-1 / R-T588-1 / R-T593-1 / R-T596-1 code, read only)

A COPY of the V3.0.58 index (4,999 lines) takes V2 .. V11 in the T-596 order (rebuilt: 5,124 lines and every V11 row
state = the committed V11), then DOORLESS_JAMBS (4 ops) and GATE_STEP_G01 (1 op): **5,125 lines, 0 STALE, 0
two-package lines, 0 unexplained conflicts; every line V12 does not write is identical to the V11 overlay.** The one
flagged row is T-580's own NO_BEFORE (T-498), not a V12 row. Totals move on ONE key: FIN.SKIRTING|lm.

## 2. Rows (before = the V11 overlay)

| Fix row | Line | Before | After | Evidence | Supersedes |
|---|---|---|---|---|---|
| FR-T601-1 | NEW:FIN.SKIRTING:SKIRT-T601:1F-R0E919A:OP-011-JAMBS (A-1F-01 arch) | no line | **0.300 lm** (2 masonry jambs x 0.15 wall) | PARTIALLY VERIFIED (jamb DRAWING-CONFIRMED; dry sides on records) | T-574 row 29 UNRESOLVED -0.30; F-T591-1 open name |
| FR-T601-2 | L-6ff876ae SKIRT-T443:GF-ST-HALL:OP-020-JAMBS | HELD blank | EXCLUDED (NOT_APPLICABLE, Q-06 A / UP-THR-001: wet side) | PARTIALLY VERIFIED | candidate HELD jamb line (T-443, RFI b) |
| FR-T601-3 | L-71e2e002 (GF dining) / L-ba3599ec (1F living) skirting | RELEASED 28.571589 / 32.38536 | unchanged; TEXT_ONLY label PASSAGE -> LIFT LANDING DOOR | DRAWING-CONFIRMED | F-T591-1 doorless reading of GF OP-011 / 1F OP-007 |
| FR-T602-1 | BESIDE L-124e0c1c EXT.FENCE.GATE G-01 leaf (HELD, unchanged) | - | step **2.500 lm**, nr 1, riser 0.15 = **0.375 m2**; stone / finish HELD | DRAWING-CONFIRMED | V10 his residual -2.900 lm (2.500 of it) |

The two room lines that deduct the A-1F-01 arch (L-a8aea284 14.3, L-4a85470b 5.1) are byte-equal: they value no jamb,
so the new line is no double count. G-01 has no threshold line (boundary opening): R-T593-1 (a) cannot bind it, so it
sits beside the gate family's own line (R-T604-1 (e)); its edge 10F is claimed by no V10 row (door edge census 6 edges,
0 second readings).

## 3. Acceptance figures (hand)

- FIN.SKIRTING released 209.428592 -> **209.728592 lm** (+0.300 = 2 x 0.15; = T-601). Held lines 7 -> 6, held bounds
  0 .. 0 unchanged (the OP-020 blank left by rule, never 0). His A-1F-01 0.30 = ours: AGREE.
- Door-step family (house + gates, beside figures) 4.800 lm / 0.720 m2 / nr 5 -> **7.300 lm / 1.095 m2 / nr 6**
  (+2.500 lm, +0.375 m2 = 2.500 x 0.15; = T-602 ours); each V10 figure re-checked against T-602. His 7.70 lm nr 6:
  ours - his = -0.400 lm UNRESOLVED (his rows carry no opening id; no %); count FREELANCER_RIGHT.
- Stair census after V12: 89 edges, 0 doubles / 0 orphans (V12 writes no step / nosing line).

## 4. T-599 joint rows

T-599 r2 was not MERGED at claim (REJECTED 13:58Z, TODO r2): no citation, 0 rows; the column / beam joint rows keep
their UNRESOLVED class with the T-599 / T-600 pointer (statement V9). A T-599 row is refused by R-T604-1 (a) (test).

## 5. Findings

- F-T604-1: ARCH.PASSAGE pcs (9) counts the three lift landing doors (GF OP-011, 1F OP-007, 2F OP-002) as passages;
  V12 moves no count (label only); whether they leave ARCH.PASSAGE is a coding question for the Lead.
- F-T604-2: G-01 has no payable line in the candidate: T-424 / the door-step wiring must give it one, or it stays beside.
- F-T604-3: the jamb is its own line (T-443 OP-020-JAMBS precedent), not +0.15 on each room line (unsourced split).

## 6. Lesson proposal (ERS s.7)

"A fix row whose element has no line of its own (a jamb, a boundary-gate step) is never folded into a neighbouring
line's value: it becomes its own line or a beside row on its family's line, the neighbours stay byte-equal, and a row
from an unmerged task is refused" (any villa on the line-index scheme; T-604; tests/t604_manifest_v12).
