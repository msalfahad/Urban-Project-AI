# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 3c3aa2f8..`,
`git -C .work/board log <board commit of this run>..`, `git log 134cd005..` on main, RUN_LOG lines after 00:12Z 8 Nov,
rows changed since), then rewrite.

## Last seen
- engine: 3c3aa2f8 (T-608 / T-609 r2 / T-612 / T-610 / T-611 / T-607 / T-605 merges; candidate of record
  ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged).
- main: 134cd005 (PR #3 merged by the owner; `run` allow-list UNCHANGED at scripts/agent_env.sh:214; PR #4 = allow-list, owner to merge).
- board: this run's final commit (Lead 2026-11-08 00:1x)
- last Lead run: 2026-11-08 00:12-00:2x UTC (run unknown)

## Run health
- Since 20:15: 10 working runs, all closed; 0 empty; 7 merged; 2 rejected (T-609 r1 -> merged r2; T-600 r1 -> r2 TODO).
- CRITICAL (owner): PR #4 not merged -> every Gate B + T-525 blocked. Owner told on 7 Nov (board note); not re-notified.
- tests/t485 + t374 x2 (order-dependent) red on the working branch = baseline (T-525).

## Live rows (00:15)
- READY 0. TODO: S: T-600 r2 (FIRST), T-614 beam-end census, T-615 Q-80 module; A: T-616 lintel -6 nr (FIRST),
  T-617 lift landing head, T-618 small residuals 2.78 lm; I: T-613 scorecard tables (FIRST), T-619 manifest V14.
- BLOCKED (PR #4 only): T-525 (W3), T-498 (W3), T-563 (W3, after T-498), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot: P02 GF not read; P04..P09 / P12..P14; T-597 trench). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-600, T-614, T-615, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-616, T-617, T-618, T-513, T-314, T-502;
  I (worker 3): T-613, T-619, T-525, T-498, T-563, T-509, T-382, T-474.
- Next board refill: after T-613 a statement V11 row (T-600 r2 / T-608 / T-614 / T-615 / T-616); fix-row rows into manifest V15.

## Top 5 priorities
1. PR #4 (owner). The run after it lands: T-525 + T-498 and T-423 r2 FIRST; T-563; T-513; Gate B diff targets = overlay
   after-totals (V14 when merged).
2. T-600 r2 within 2 Checker runs of READY; then T-613 (12-13 Nov tables).
3. 12-13 Nov: scorecard tables (T-613) -> statement V11; Q-34 raised then with T-541's reconciliation.
4. Line-moving residuals: T-616 lintels -6 nr, T-614 beam ends, T-615 (Q-80) 175.9 m2 out of HELD, T-617 2 x 3.35 m2.
5. When a package merges, promote its queued successor in the same run (T-509 / T-563 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Status word FIRST; 'worker N first / second' text matches lane order; 7-cell rows; `board check` pulls first: commit before.
- A Checker finding gets its fix row in the next Lead run.
- Register (00:15): BEAM END AT NARROW COLUMN (beam owns band beyond column, T-614), LIFT LANDING DOOR LINTEL (per host
  wall, T-616). 20:18: BEAM BAND OVERLAP, SKIRTING AT STAIR-OPENING WALLS. 16:17: FOOTING OVERLAP, LIFT LANDING DOOR,
  STAIR STEP / NOSING EDGE. 12:16: COLUMN-BEAM JOINT CORRECTED, DOORLESS OPENING JAMB.
- UP-CONC-JOINT-001 1.0.0 MERGED (LEAD_ADOPTED). 1F 69D joint >= 0.075 m3 VERIFIED lower bound.
- Lessons 00:15: node capacity once / balancing term never a cause (PROPOSED, T-600 r2); beam band beyond narrow column
  (PROPOSED, T-614); skirting-where-floor and crossing-union ADOPTED.
- F-C-T570-1, F-C-T593-1 (stair skirting one element, range never summed; ORR-007 open with owner).
- Materials: FINISH V7, PLASTER V3; Q-80 A (0.15 block 12.5 / m2) answered 7 Nov -> T-615.

## Blockers
- PR #4 (owner). Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, D-02 CB10
  width, lintel ends, DOME-3 bars, lift-wall height, F-T583-1 note 9, F-T589-2, MS1-T winder fronts) keep lines HELD,
  never block integration.

## Open owner items
- PR #4 merge (CRITICAL). ORR-007 stair skirting payable form.
- Freelancer floors / rails workbooks + 1990 spec (owner: coming this week, not blockers); privacy switch; PyMuPDF review after 10 Nov.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
