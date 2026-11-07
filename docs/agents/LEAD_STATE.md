# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 80da26a0..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 08:12Z 7 Nov, rows changed since), then rewrite.

## Last seen
- engine: 80da26a0 (T-581 r2 / T-585 / T-587 r2 / T-588 / T-589 / T-592 merges; candidate of record
  ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh:211 UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-07 08:15)
- last Lead run: 2026-11-07 08:12-08:35 UTC (run session_01E6cPncAnvRfxD7AoDrKCc5)

## Run health
- Since 04:15 every run closed; 0 empty; 6 merged, 1 rework (T-587 gate c, CODEMAP stale; merged r2).
- CRITICAL (owner, notified 04:15 5 Nov, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B + T-525 blocked.
- Worker venv-empty failure did not recur this window.
- tests/t485 still red on the working branch (T-507 stale pending in master 1.55.0).

## Live rows (08:15)
- READY 0.
- TODO: S: T-595 restatement versions (FIRST), T-590 RULE_DIFF provenance S, T-597 B1 plan side P13;
  A: T-591 RULE_DIFF provenance A (FIRST), T-598 nosing 20 HELD edges (feeds T-424);
  I: T-593 manifest V10 (FIRST), T-594 statement V8, T-596 manifest V11 (after T-595 MERGED).
- BLOCKED (wrapper only): T-525 (W3), T-498 (W3), T-563 (W3, after T-498), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot: T-589 packs P01 / P10 / P11 first). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-595, T-590, T-597, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-591, T-598, T-513,
  T-314, T-502; I (worker 3): T-593, T-594, T-596, T-525, T-498, T-563, T-509, T-382, T-474.

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (with T-525 promotion) and T-423 r2 FIRST; T-563; T-513;
   wire from manifests V6..V11 in T-580's order; Gate B diff targets = overlay after-totals (V9, then V10 / V11).
2. 12-13 Nov: statement V8 (T-594) before milestone text; Q-34 raised then with T-541's reconciliation.
3. Scorecard evidence: T-589 packs into the Checker's T-180 slot; T-590 / T-591 RULE_DIFF without a recorded rule ->
   UNRESOLVED (any genuine gap -> owner package only under ERS 2.7).
4. Lessons to adopt on merge: bars on every drawn face (T-595); overlay (T-498 Gate B).
5. 10 Nov: LOW (wrapper). When a package merges, promote its queued successor in the same run
   (T-509 / T-563 after T-498; T-424 after T-423; T-596 when T-595 merges).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least two non-candidate TODO behind its stream package while Gate B is blocked.
- Status word FIRST in the status cell, and its 'worker N first / second' text must match the lane order;
  7-cell rows; `board check` pulls first: commit before.
- A Checker finding that blocks a merge gets its fix row in the next Lead run, first in its lane.
- Register (08:15): EXTERNAL DOOR STEP PAYABLE LENGTH closed (stone in wall gap); GATE STEP = door-step family;
  E1 LANDING SKIRTING = yard criterion, NOT_IN_DRAWING. Earlier: EXTERNAL DOOR STEP one element, YARD SKIRTING,
  LINTEL WIDTH BASIS, 24 earlier.
- F-C-T570-1: return paint stays ENGINE_WRONG in the statement until a candidate FIN.PAINT return line exists.
- Materials: FINISH V7, PLASTER V3 (plaster m2 moves with T-563); sand loose m3, t / loads HELD.

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh). Designer items (D-16 / D-63 incl. 2 GF column CONFLICT positions,
  D-GF-09 frame vs masonry, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, lintel deficit ends, lintel bar ends,
  DOME-3 bars, lift-wall height, F-T583-1 note 9, F-T589-2 court ground-beam zone without its own RFI) keep lines HELD,
  never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15 5 Nov).
- Q-80 15 cm black block face size (owner package; 15 walls 175.9 m2 HELD).
- Freelancer floors / rails workbooks over the 6.2 MB connector limit (zipped / split copy); Kuwait 1990 spec copy under
  6 MB; privacy switch; PyMuPDF decision (F-T465-1); PR #3 clean-up.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
