# T-611 WIRING MANIFEST V13 + OVERLAY DRY RUN on ARCH_TAKEOFF_V3.0.58

Worker 3 (lane I, non-candidate), 2026-11-07. Not an integration package: nothing is wired; no candidate, released
(V2.9 + route G), rule, knowledge or registry file is touched; no drawing read. Every figure comes from the committed,
Checker-merged T-606 output (1ddf21f4), the Checker's own T-606 verdict components, and the V12 manifest (T-604,
54a713ee), all sha256-pinned. Files: `manifest_v13.py` (R-T611-1), `out/WIRING_MANIFEST_V13.json`,
`tests/t611_manifest_v13/`. Rebuild: `python3 -I research/agents_t611/manifest_v13.py` (`--check`).

## 1. Physical element and rule

The skirting run of the 1F living room line L-ba3599ec on the two walls bounding the printed stair opening (west wall
AF7, south wall AEC) and the column returns inside that span. At +5.50 there is no finished floor against those faces
(the stair void and the arriving-flight stair box), so by UP-SKIRT-001 1.4.0 (skirting only where a finished floor meets
a finished wall) they take no room skirting. None of the line's existing deductions (doors 4.70, passage 1.00, floor
glazing 3.10464, W13 / W25 2.20, dog-leg shaft 9.05) lies on these faces (T-606), so the deduction is not a double one.

## 2. Deducted length (Checker governs)

| Component (Checker own read, T-606 verdict (f)) | lm |
|---|---|
| AF7 west wall, B74 y to AEC | 4.000 |
| AEC south wall, AF7 to stair-box edge AF5 (5.87 + 1.15) | 7.020 |
| column 300E returns inside the span (2 x 0.05) | 0.100 |
| column 3008 west return (straddles AF5; faces the void) | 0.050 |
| **total** | **11.170** |

Worker figure 11.22 = 11.17 + 0.05 (column 3008 east return: faces the 1F floor east of AF5 and keeps skirting; named
by the Checker). The code refuses components that do not re-add, an unnamed difference, or a worker figure that the
named differences do not close exactly.

## 3. Row and overlay

| Fix row | Line | Before (V12 overlay) | After | Evidence | Supersedes |
|---|---|---|---|---|---|
| FR-T606-1 | L-ba3599ec 1F living FIN.SKIRTING | RELEASED 32.38536 lm | RELEASED **21.21536 lm** | PARTIALLY VERIFIED (Checker re-measure of the deducted faces; line status as merged) | F-T606-1 worker proposal 11.22; Checker restatement on V3.0.58 |

The V12 FR-T601-3 TEXT_ONLY label (1F OP-007 PASSAGE -> LIFT LANDING DOOR) sits on the same line: it is ABSORBED into
the V13 row (R-T593-1 (f) precedent; its stated before equals the V13 row's before), so one package writes the line (R1).
The label text is carried unchanged in `absorbs`. GF dining's FR-T601-3 label stays in V12.

A COPY of the V3.0.58 index (4,999 lines) takes V2 .. V12 in the T-604 order (rebuilt: 5,125 lines, every V12 row and
the V12 FIN.SKIRTING totals = the committed V12), then FLOORLESS_FACES (1 op): **5,125 lines, 0 STALE, 0 two-package
lines, 0 unexplained conflicts; every line V13 does not write is identical to the V12 overlay.** The one flagged row is
T-580's own NO_BEFORE (T-498). Totals move on ONE key: FIN.SKIRTING|lm. Stair edge census after V13: 89 edges, 0
doubles / 0 orphans.

## 4. Acceptance figures (hand)

- FIN.SKIRTING released, V12 base: 209.728592 - 11.170 = **198.558592 lm** (-11.17 lm, -5.33 %).
- Checker base V3.0.58: 209.428592 - 11.170 = 198.258592 lm; the two differ by 0.300 = the V12 FR-T601-1 jamb line,
  present on both sides of the deduction (proved in code).
- Released lines 19, held 6 (bounds 0 .. 0), excluded 29: unchanged; no blank became 0.
- 1F living group vs freelancer (T-574 row CER.C21): ours 32.38536 -> 21.21536 lm vs his 43.78 lm; gap -11.39464 ->
  -22.56464 lm. The gap widens on a physical cause (ENGINE_WRONG, Checker CONFIRMED); agreement with him is not the test.
  His outline walks the opening edges B74 / B75 / D24 / AF5 (11.02 lm) where there is a void edge, not a floor-wall
  junction: RULE_DIFFERENCE proposal, no %.

## 5. Sources at claim (R-T611-1 (a))

- MERGED with a fix row: T-606 (FR-T606-1).
- MERGED, no fix row, 0 rows: T-605 (footing overlap; CONC.FOOTING unchanged), T-607 (steps / nosing one cause
  C-T607-1, statement only), T-599 r2 (UP-CONC-JOINT-001 1.0.0 now citable; no manifest line carries a joint row: the
  citation goes to the statement, T-609 r2).
- NOT MERGED, refused: T-610 (TODO at claim).

## 6. Findings

- F-T611-1: the 11.17 lm leave the room line only; whether a balustrade / void-edge item takes the stair-opening edge is
  not a skirting question and is not in the candidate: no line written, none assumed.

## 7. Lesson proposal (ERS s.7)

"A deduction confirmed by the Checker enters the manifest as the Checker's component sum, with the worker's figure
reconciled to it by named differences; it is stated on both the overlay base and the Checker's base, and the two
restatements must differ by exactly the merged moves between them" (any villa on the line-index scheme; T-611;
tests/t611_manifest_v13).
