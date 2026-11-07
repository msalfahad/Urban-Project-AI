# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 6d896db0..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 04:13Z 7 Nov, rows changed since), then rewrite.

## Last seen
- engine: 6d896db0 (T-576 / T-582 / T-586 / T-578 / T-583 / T-584 merges; candidate of record
  ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh:211 UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-07 04:15)
- last Lead run: 2026-11-07 04:13-04:35 UTC (run unknown)

## Run health
- Since 00:13 every run closed; 0 empty; 6 merged, 1 rejected (T-581).
- CRITICAL (owner, notified 04:15 5 Nov, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B + T-525 blocked
  (now their ONLY blocker: T-582 merged).
- Recurring, self-repairing: worker venv empty at start ('No module named pytest'), fixed by re-running setup (3 runs).
- tests/t485 still red on the working branch (T-507 stale pending in master 1.55.0).

## Live rows (04:15)
- READY 0.
- TODO: S: T-581 r2 (FIRST, Verifier rework list), T-589 closable pack, T-590 RULE_DIFF provenance S;
  A: T-585 skirting yard / stairs (FIRST), T-592 door-step length + D-GF-09 riser + gate, T-591 RULE_DIFF provenance A;
  I: T-587 statement V7 (FIRST), T-588 manifest V9 + overlay (FR-T584-1 / -3, T-578, T-583 rows; FR-T584-2 waits T-592 -> V10).
- BLOCKED (wrapper only): T-525 (W3), T-498 (W3), T-563 (W3, after T-498), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-581, T-589, T-590, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-585, T-592, T-591,
  T-513, T-314, T-502; I (worker 3): T-587, T-588, T-525, T-498, T-563, T-509, T-382, T-474 (separator ';').

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (with T-525 promotion) and T-423 r2 FIRST; T-563; T-513;
   wire from manifests V6..V9 in T-580's order; Gate B diff targets = T-580 after-totals + T-582 lintel classes.
2. 12-13 Nov: 23 trades closed; open lintel width (T-581 r2), yard / stair skirting (T-585), door-step payable length
   (T-592); T-587 statement V7 before milestone text; Q-34 raised then with T-541's reconciliation.
3. Scorecard evidence: T-589 closable pack -> feed the Checker's T-180 slot; T-590 / T-591 RULE_DIFF without a recorded
   rule -> UNRESOLVED (any genuine gap -> owner package only under ERS 2.7).
4. Lessons to adopt on merge: frame over masonry = DRAWING CONFLICT (T-581 r2); overlay (T-498 Gate B); outline vs
   deduction (T-585); lintel reference row first (T-581 r2); plaster layer height (T-563).
5. 10 Nov: LOW (wrapper). When a package merges, promote its queued successor in the same run
   (T-509 / T-563 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least two non-candidate TODO behind its stream package while Gate B is blocked.
- Status word FIRST in the status cell, and its 'worker N first / second' text must match the lane order;
  7-cell rows; `board check` pulls first: commit before.
- A Checker finding that blocks a merge gets its fix row in the next Lead run, first in its lane.
- Register: EXTERNAL DOOR STEP RULED one element (04:15); YARD SKIRTING, LINTEL WIDTH BASIS (00:15); 24 earlier.
- F-C-T570-1: return paint stays ENGINE_WRONG in the statement until a candidate FIN.PAINT return line exists.
- Materials: FINISH V7, PLASTER V3 (plaster m2 moves with T-563); sand loose m3, t / loads HELD.

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh). Designer items (D-16 / D-63 incl. 2 GF column CONFLICT positions,
  D-GF-09 frame vs masonry, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, lintel deficit ends, lintel bar ends,
  DOME-3 bars, lift-wall height, F-T583-1 note 9) keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15 5 Nov).
- Q-80 15 cm black block face size (owner package; 15 walls 175.9 m2 HELD).
- Freelancer floors / rails workbooks over the 6.2 MB connector limit (zipped / split copy); Kuwait 1990 spec copy under
  6 MB; privacy switch; PyMuPDF decision (F-T465-1); PR #3 clean-up.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
