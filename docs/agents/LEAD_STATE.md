# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 78196c45..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 12:12Z 7 Nov, rows changed since), then rewrite.

## Last seen
- engine: 78196c45 (T-590 / T-591 / T-593 / T-594 / T-595 / T-598 merges; candidate of record ARCH_TAKEOFF_V3.0.58 /
  BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh:211 UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-07 12:16)
- last Lead run: 2026-11-07 12:12-12:35 UTC (run unknown)

## Run health
- Since 08:12: 10 runs, all closed; 0 empty; 6 merged; 0 rejected.
- CRITICAL (owner, notified 04:15 5 Nov, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B + T-525 blocked.
- tests/t485 still red on the working branch (T-507 stale pending in master 1.55.0; T-525).

## Live rows (12:16)
- READY 0.
- TODO: S: T-599 joint rule version (FIRST), T-597 B1 plan side, T-600 column residuals (after T-599);
  A: T-601 doorless jambs (FIRST), T-602 door-step 2.90 lm (after T-601);
  I: T-596 manifest V11 + nosing rows (FIRST), T-603 statement V9, T-604 manifest V12 (after T-601 MERGED).
- BLOCKED (wrapper only): T-525 (W3), T-498 (W3), T-563 (W3, after T-498), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot: remaining T-589 packs, P01 first). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-599, T-597, T-600, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-601, T-602, T-513,
  T-314, T-502; I (worker 3): T-596, T-603, T-604, T-525, T-498, T-563, T-509, T-382, T-474.
- Board thin after these: next run add 1-2 A rows (A has 2) and refill S / I as rows merge.

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (with T-525 promotion) and T-423 r2 FIRST; T-563; T-513;
   wire from manifests V6..V12 in T-580's order; Gate B diff targets = overlay after-totals (V11, then V12).
2. 12-13 Nov: statement V9 (T-603) before milestone text; Q-34 raised then with T-541's reconciliation.
3. T-599 within 2 Checker runs of READY (reclasses the 38 joint rows); T-600 per-storey residuals to a cause.
4. Lessons to adopt on merge: joint rule version (ADOPTED, test in T-599); doorless jambs (T-601); one skirting form (T-603).
5. When a package merges, promote its queued successor in the same run (T-509 / T-563 after T-498; T-424 after T-423;
   T-604 when T-601 merges).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least two non-candidate TODO behind its stream package while Gate B is blocked.
- Status word FIRST in the status cell, and its 'worker N first / second' text must match the lane order;
  7-cell rows; `board check` pulls first: commit before.
- A Checker finding that blocks a merge gets its fix row in the next Lead run, first in its lane.
- Register (12:16): COLUMN-BEAM JOINT CORRECTED (column owns to the slab top, beam face to face; 11-06 entry wrong);
  DOORLESS OPENING JAMB (B7 skirting, UP-SKIRT-001). Earlier: external door step payable length, gate step = door-step
  family, E1 landing skirting NOT_IN_DRAWING, yard skirting, lintel width basis, 24 earlier.
- F-C-T570-1: return paint stays ENGINE_WRONG in the statement until a candidate FIN.PAINT return line exists.
- F-C-T593-1: stair skirting SLOPED / ZIGZAG = one element; range over forms, never summed (ORR-007 open with owner).
- Materials: FINISH V7, PLASTER V3 (plaster m2 moves with T-563); sand loose m3, t / loads HELD.

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh). Designer items (D-16 / D-63 incl. 2 GF column CONFLICT positions,
  D-GF-09 frame vs masonry, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, lintel deficit ends, lintel bar ends,
  DOME-3 bars, lift-wall height, F-T583-1 note 9, F-T589-2 court ground-beam zone, MS1-T winder fronts) keep lines HELD,
  never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15 5 Nov).
- Q-80 15 cm black block face size (15 walls 175.9 m2 HELD); ORR-007 stair skirting payable form.
- Freelancer floors / rails workbooks over the 6.2 MB connector limit; Kuwait 1990 spec copy under 6 MB; privacy switch;
  PyMuPDF decision (F-T465-1); PR #3 clean-up.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
