# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 37dcc11b..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 16:12Z 7 Nov, rows changed since), then rewrite.

## Last seen
- engine: 37dcc11b (T-596 / T-601 / T-602 / T-597 / T-603 merges; candidate of record ARCH_TAKEOFF_V3.0.58 /
  BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh:211 UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-07 16:20)
- last Lead run: 2026-11-07 16:12-16:40 UTC (run unknown)

## Run health
- Since 12:12: 10 runs, all closed; 0 empty; 5 merged; 1 rejected (T-599 gates F + H).
- CRITICAL (owner, notified 04:15 5 Nov, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B + T-525 blocked.
- tests/t485 still red on the working branch (T-507 stale pending in master 1.55.0; T-525).

## Live rows (16:20)
- READY 0.
- TODO: S: T-599 r2 (FIRST, critical, gate 1), T-605 footing overlap, T-600 (after T-599 r2);
  A: T-606 room skirting 9.693 lm (FIRST), T-607 step / nosing 8.4 lm (after T-606), T-608 lift landing openings (after T-607);
  I: T-604 manifest V12 + FR-T602-1 (FIRST), T-609 statement V10 (after T-604).
- BLOCKED (wrapper only): T-525 (W3), T-498 (W3), T-563 (W3, after T-498), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot: P03 GF next, then P04..P09 / P12..P14; T-597 trench re-measure). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-599, T-605, T-600, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-606, T-607, T-608,
  T-513, T-314, T-502; I (worker 3): T-604, T-609, T-525, T-498, T-563, T-509, T-382, T-474.
- Board thin after these: next run add 1 I row (I has 2) and refill as rows merge.

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (with T-525 promotion) and T-423 r2 FIRST; T-563; T-513;
   wire from manifests V6..V12 in T-580's order; Gate B diff targets = overlay after-totals (V12).
2. T-599 r2 within 2 Checker runs of READY (L4 to the end); then T-600 (residuals + GF joint-head readings).
3. 12-13 Nov: statement V10 (T-609) after V12 (T-604) before milestone text; Q-34 raised then with T-541's reconciliation.
4. Residual hunts by size: T-606 9.693 lm, T-607 8.4 lm (shared step / nosing), T-605 footing overlap.
5. When a package merges, promote its queued successor in the same run (T-509 / T-563 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least two non-candidate TODO behind its stream package while Gate B is blocked.
- Status word FIRST in the status cell, and its 'worker N first / second' text must match the lane order;
  7-cell rows; `board check` pulls first: commit before.
- A Checker finding that blocks a merge gets its fix row in the next Lead run, first in its lane.
- Register (16:20): FOOTING OVERLAP (whole outline owns; drawn, not schedule), LIFT LANDING DOOR (not a passage; supply
  HELD), STAIR STEP / NOSING EDGE (one edge once per line). 12:16: COLUMN-BEAM JOINT CORRECTED, DOORLESS OPENING JAMB.
- GF joint-head matched source = T-551 2.28125 m3 (V9 reading of record); T-572 / T-576 readings go to T-600.
- Lessons 16:20 ADOPTED: matched-part-only reclass; plot-boundary gaps in step census; label not evidence; drawn
  outlines for overlaps; restatement bounds; statement reclass = class move only.
- F-C-T570-1, F-C-T593-1 (stair skirting one element, range never summed; ORR-007 open with owner).
- Materials: FINISH V7, PLASTER V3 (plaster m2 moves with T-563); sand loose m3, t / loads HELD.

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh). Designer items (D-16 / D-63 incl. 2 GF column CONFLICT positions,
  D-GF-09, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, lintel ends, DOME-3 bars, lift-wall height, F-T583-1 note 9,
  F-T589-2, MS1-T winder fronts) keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15 5 Nov).
- Q-80 15 cm black block face size (15 walls 175.9 m2 HELD); ORR-007 stair skirting payable form.
- Freelancer floors / rails workbooks over 6.2 MB; Kuwait 1990 spec copy under 6 MB; privacy switch; PyMuPDF (F-T465-1); PR #3.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
