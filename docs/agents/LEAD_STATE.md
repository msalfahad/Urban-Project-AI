# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log d2de9f31..`,
`git -C .work/board log <board commit of this run>..`, `git log 134cd005..` on main, RUN_LOG lines after 04:13Z 8 Nov,
rows changed since), then rewrite.

## Last seen
- engine: d2de9f31 (T-613 r2 / T-600 r2 / T-616 merges; candidate of record ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER
  1.55.0; released V2.9 + route G unchanged).
- main: 134cd005 (PR #4 allow-list OPEN, mergeable clean, owner to merge; `run` allow-list unchanged).
- board: this run's final commit (Lead 2026-11-08 04:1x)
- last Lead run: 2026-11-08 04:13-04:3x UTC (run session_01E6cPncjG39WhnxxFAXpdTe)

## Run health
- Since 00:15: 10 working runs, all closed; 0 empty; 3 merged; 2 rejected (T-613 r1 -> merged r2; T-614 r1 -> r2 TODO).
- CRITICAL (owner): PR #4 not merged -> every Gate B + T-525 blocked. Owner told 7 Nov; not re-notified.
- tests/t485 + t374 x2 (order-dependent) red on the working branch = baseline (T-525).

## Live rows (04:15)
- READY 1: T-617 (02:52, CHECKER-RUNS; first in next Checker run).
- TODO: S: T-614 r2 (FIRST), T-615, T-623; A: T-618 (FIRST), T-621, T-622; I: T-619 (FIRST), T-620.
- BLOCKED (PR #4 only): T-525 (W3), T-498 (W3), T-563 (W3, after T-498), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot: P02 GF 9/21, B7 SW quarter-ring next; P04..P09 / P12..P14; T-597 trench).
  PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-614, T-615, T-623, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-618, T-621, T-622,
  T-513, T-314, T-502; I (worker 3): T-619, T-620, T-525, T-498, T-563, T-509, T-382, T-474.
- Next board refill: when T-619 / T-614 r2 merge, fix rows into manifest V15 (FR-T614-n, FR-T617-1 for T-558);
  after T-621 / T-622 / T-623, the same per-row evidence for B8 waterproofing (49 UNKNOWN rows) and B12 windows m2.

## Top 5 priorities
1. PR #4 (owner). The run after it lands: T-525 + T-498 and T-423 r2 FIRST; T-563; T-513; T-314 (external plaster
   1502.84 vs 0 m2); Gate B diff targets = overlay after-totals (V14 when merged).
2. T-614 r2 within 2 Checker runs of READY; T-617 in the next Checker run.
3. 12-13 Nov: statement + scorecard V11 (T-620) on V10 tables; Q-34 raised then with T-541's reconciliation.
4. Lines that can close from drawings: floor tile (T-621), wall tile (T-622), beams / columns (T-623); Q-80 175.9 m2 out
   of HELD (T-615).
5. When a package merges, promote its queued successor in the same run (T-509 / T-563 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Status word FIRST; 'worker N first / second' text matches lane order; 7-cell rows; NEVER a '|' inside a cell text
  (T-622 '|delta|' flagged once); `board check` pulls first: commit before.
- A Checker finding gets its fix row in the next Lead run.
- Register (04:15): CURVED-BAND OPENING HEAD, LIFT LANDING HEAD, BEAM BAND END vs LEDGER EXTENT, FLOOR FINISH PER ROOM /
  WET-WALL FACE. 00:15: BEAM END AT NARROW COLUMN, LIFT LANDING DOOR LINTEL.
- UP-CONC-JOINT-001 1.0.0 MERGED (LEAD_ADOPTED). 1F 69D joint >= 0.075 m3 VERIFIED lower bound.
- Lessons 04:15: T-600 node once ADOPTED; T-613 status caps ADOPTED; T-616 count split by opening / curved band ADOPTED;
  T-614 r1 billing inside the line's measured extent PROPOSED; beam band beyond narrow column PROPOSED (T-614 r2).
- F-C-T570-1, F-C-T593-1 (stair skirting one element, range never summed; ORR-007 open with owner).
- Materials: FINISH V7, PLASTER V3; Q-80 A (0.15 block 12.5 / m2) answered 7 Nov -> T-615.

## Blockers
- PR #4 (owner). Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, D-02 CB10
  width, lintel ends, DOME-3 bars, lift-wall height, lift landing head, F-T583-1 note 9, F-T589-2, MS1-T winder fronts)
  keep lines HELD, never block integration.

## Open owner items
- PR #4 merge (CRITICAL). ORR-007 stair skirting payable form.
- Freelancer floors / rails workbooks + 1990 spec (owner: coming this week, not blockers); privacy switch; PyMuPDF review after 10 Nov.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
