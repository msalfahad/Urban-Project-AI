# T-549 WIRING MANIFEST V4 on ARCH_TAKEOFF_V3.0.58 + R-T549-1 manifest coverage

Worker 3 (lane I, non-candidate, backlog-permitted), 2026-11-06, engine base 3f3b580c. Not an integration package:
nothing is wired; no candidate, released (V2.9 + route G), rule, knowledge or registry file is touched. Files:
`manifest_v4.py` (builder; V3 / V2 / V1 builders imported read only), `WIRING_MANIFEST_V4.json`,
`tests/t549_wiring_manifest_v4/` (22 tests). Rebuild: `python3 -I research/agents_t549/manifest_v4.py` (`--check`;
`--stage` prints the T-498 stage check when `origin/agents/task-T-498` is fetched). Every input is a committed,
numbers-only output (sha256 in `inputs`) or the merged piece's own function (T-537 `t537_apply.build`); no drawing read.

## 1. Coverage (R-T549-1)

Range (V3 base 9c160d22, V4 base 3f3b580c] on the first-parent line: 8 merges, all covered: T-534 3c772b79, T-533
93aba0d6, T-541 322c1409, T-539 9b754fad, T-537 ac3c77b2, T-543 8e93e987, T-548 42ae2e5f, T-542 3f3b580c (T-542 / T-543
/ T-548 merged after the row was written; T-540 was already a V3 source). T-541 / T-543 / T-548 are NO_WIRING (move
no line). Rule: every 'Merge agents/task-T-n' in the pinned range is a source with that merge commit or a NO_WIRING
piece with its reason; missing -> MISSING_FROM_MANIFEST, outside / other commit -> OUT_OF_RANGE. The range is pinned,
so a later merge belongs to V5 and never turns this file red (tested on a synthetic repository: T-903 merged after the
head is ignored at the pinned head and refused when the head moves).

## 2. Expectations that change V3 -> V4 (candidate lines moved: 0)

| item | V3 / V2 expectation | V4 expectation | cause / owning package |
|---|---|---|---|
| V7 stair bed area (11 released lines) | HELD_BY_NAME (T-534 unmerged) | **AT_LEAST 35.4313 m2**; V7 1.062939 m3, 10.178704 bags, 1.06028 m3 sand installed; procurement HELD (F-T518-2) | T-534 / F package step 5 |
| stair bed beyond the treads | not stated | 11 parts **20.92611 m2**: 7 HELD riser lines 10.338610 + 4 landings with no line 10.5875; each lifts V7 by its own line (x 0.03 m3; x 9.576 bags; x 0.9975 m3) | T-542 / B7-03 risers, T-502 landings |
| GF hall / lobby floor bed (T-500 rows L-bff6fe38, L-b87fd07d) | 1:4 BOUND (dry floor) | STALE_ON_MIX: finish HELD; at 1:3 0.03 m the sand is 0.183366 m3, 0.018842 below the 1:4 low 0.202208 | F-T542-1 / floor-bed materials step |
| GF glue host (stage L-d14c6c9b) | [23.769, 23.895] kg | **[23.4459, 23.895] kg** = (5.59 - [0.3798, 0.28]) x 4.5 | T-537 r2 / T-498 step 5 |
| 1F glue host (stage L-4b9a29d4) | BOUNDED [443.27313, 451.60893] kg | **HELD blank**, AT_MOST 451.60893 kg (100.35754 x 4.5) beside (F-T537-1) | T-537 r2 / T-498 step 5 |
| AAC glue group | AT_LEAST 35.387755 .. 36.226627 bags (>= 36 .. 37) | **AT_LEAST 17.643906 .. 18.16227 (>= 18 .. 19), HELD** | T-537 r2 / T-498 step 7 |
| column-end ties | +30 nr, NO LINE | **18 measured** (1F-W09 e0, 2F-W00 e1, 2F-W01 e0, 6 each) + **12 HELD by name** (1F-W23, 2F-W08: 0.15 m module) | T-539 / T-363 |
| end V-joint mesh | owner 40.90 / drawing 44.10 m.l | owner 40.90 / drawing **44.20** (+0.10: GF-W16 e0 Sigma side one band 3.75 vs raw 3.65); strip +0 | T-539 / T-363 |
| 0.15 m black units / mortar (6 hosts, 15 walls, 178.571 m2) | HELD (T-506 / T-523 notes) | HELD by R-T533-1 (sourced census); the 12 stage lines L-06e9c608 .. L-fa0fae23 all HELD (checked) | T-533 / T-498 step 2, T-372 |

Proposed new lines (T-539, unwired; no candidate line carries these codes): MAS.TIE.SHARMAT 151 measured + 104
junctions HELD; MAS.MESH.BED_JOINT 175.4844 m.l; MAS.MESH.JOINT per class (owner / drawing bands, Q-77).

## 3. Findings

- **F-T549-1** (for the Checker / Lead): T-541 and the T-548 statement value the roof WP at the F package's EXPECTED
  after (V2), not at V3.0.58: membrane 209.65844 vs candidate 209.018867 (+0.639573, ledge L-2361d6ec HELD 0 .. 0.639573),
  upturn 187.83416 vs 186.782544 (+1.051616: L-1954878b 0.500002, L-d7d1bf8c 0.551614, both HELD). Their roof rows hold
  only once F steps 1-2 (T-522 / T-529) are wired; ENGINE_RIGHT on those rows is conditional on that wiring.
- **F-T549-2**: the V2 glue expectations are stale (table above); a package wiring them would release a low end with
  no proven basis on the 1F host.
- **F-T549-3**: the V3 '+30 ties' would release 12 ties counted on the 0.20 m course over 0.15 m walls.
- T-542's in-wire 35.4325 m2 is printed dimensions; the wire stays on the line nets 35.4313 (0.0012 TOLERANCE, never
  added). T-543: engine 467.7925 m2 = the 13 released MAS.BLOCK lines, 15 HELD lines identical: consistent, no move.

## 4. Engine vs freelancer, verdicts

No new comparison: roof WP RULE_DIFFERENCE + HELD (T-541, residual +0.523 m2 / +11.893 lm UNRESOLVED), blockwork
gap 792.897 m2 (T-543, ENGINE_WRONG none), stair bed RULE_DIFFERENCE + ENGINE_RIGHT (T-534); no freelancer rows for
ties, mesh, glue or stair mortar (UNRESOLVED).

## 5. Lessons row (proposed, ERS s.7)

| 2026-11-06 | three merges (T-542 / T-543 / T-548) landed between the row and the run, and a manifest listing only the
row's pieces would have left them out silently; T-541 / T-548 read post-wiring values as the candidate | a manifest's
scope was a typed list, not the merge range; a reconciliation's engine side was not tied to a candidate version |
R-T549-1: a manifest names its pinned merge range and refuses a merged piece it does not cover; a reconciliation
names whether its engine side is the candidate or an expected after (every villa) | tests/t549_wiring_manifest_v4
(synthetic repo: missing / out of range / later merge) | proposed |
