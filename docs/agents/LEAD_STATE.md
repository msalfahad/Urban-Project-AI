# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log e8709e09..`,
`git -C .work/board log <board commit of this run>..`, `git log 134cd005..` on main, RUN_LOG lines after 08:12Z 8 Nov,
rows changed since), then rewrite.

## Last seen
- engine: e8709e09 (T-619 / T-621 merges; before them T-617 44ee93d5, T-614 r2 a7f1f3af, T-618 85a473ce; candidate of
  record ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged).
- main: 134cd005 (PR #4 allow-list OPEN since 7 Nov 21:05, mergeable clean, owner to merge).
- board: this run's final commit (Lead 2026-11-08 08:2x)
- last Lead run: 2026-11-08 08:12-08:2x UTC (run session_01E6cPneC5s1LkPG8edERsvY)

## Run health
- Since 04:13: 10 runs, all closed except the Verifier 07:51 run (open at 08:19, merged T-619 + T-621 08:01: check its
  final line); 5 merged, 0 rejected. W3 05:00 BLOCKED: setup pip 403 (pypdf wheel), pytest absent; recovered 06:59.
  If it repeats twice, report it under NEEDS FIXING (environment / proxy).
- CRITICAL (owner): PR #4 not merged -> every Gate B + T-525 blocked. Owner told 7 Nov; not re-notified.
- tests/t485 + t374 x2 (order-dependent) red on the working branch = baseline (T-525).

## Live rows (08:19)
- READY 1: T-615 (07:33, CHECKER-RUNS; FIRST in the next Checker run).
- TODO: S: T-623 (FIRST), T-624, T-628; A: T-622 (FIRST), T-625, T-626, T-627; I: T-620 (FIRST), T-629, T-630.
- BLOCKED (PR #4 only): T-525 (W3), T-498 (W3), T-563 (W3, after T-498), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot: P02 GF 11 / 21; light-run option GF-OPEN boundary if T-625 not READY; P04..P09 /
  P12..P14; T-597 trench). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-623, T-624, T-628, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-622, T-625, T-626,
  T-627, T-513, T-314, T-502; I (worker 3): T-620, T-629, T-630, T-525, T-498, T-563, T-509, T-382, T-474.
- Next board refill: when T-615 merges, Q-80 quantities into V15 (T-629); after T-622 / T-626 / T-627 the remaining
  UNKNOWN lines: B5 internal plaster 39 rows, B6 internal paint 41, B7 stair bed 26, B9 blockwork 89 (largest),
  T-573 cove 427.46 lm (engine 0).

## Top 5 priorities
1. PR #4 (owner). The run after it lands: T-525 + T-498 and T-423 r2 FIRST; T-563; T-513; T-314 (external plaster
   1502.84 vs 0 m2); Gate B diff targets = overlay after-totals (V14, V15 when merged).
2. T-615 in the next Checker run; T-623 / T-624 (gate 1 structural) within 2 Checker runs of READY.
3. 10 Nov: T-630 dry run (non-candidate, all trades present / held / missing + aggregation). 12-13 Nov: statement +
   scorecard V11 (T-620); Q-34 raised then with T-541's reconciliation.
4. Lines that can close from drawings: wall tile (T-622), floor tile carry-forward (T-625), waterproofing (T-626),
   openings m2 (T-627), footings (T-628).
5. When a package merges, promote its queued successor in the same run (T-509 / T-563 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Status word FIRST; 'worker N first / second' text matches lane order; 7-cell rows; NEVER a '|' inside a cell text;
  `board check` pulls first: commit before. Lead note stamp must be 'Lead YYYY-MM-DD HH:MM per' (a 'T..Z' stamp is not
  read by queue_check: 08:19 run fixed it).
- A Checker finding gets its fix row in the next Lead run.
- Register (08:19): OPEN-PLAN FLOOR BOUNDARY, 0.15 m BLACK BLOCK MODULE. 04:15: CURVED-BAND OPENING HEAD, LIFT LANDING
  HEAD, BEAM BAND END vs LEDGER EXTENT, FLOOR FINISH PER ROOM / WET-WALL FACE.
- Lessons 08:19: T-614 billing-extent ADOPTED; range = low end + HELD companion ADOPTED (T-619); open-plan side ends at a
  named printed line PROPOSED (T-625).
- F-C-T570-1, F-C-T593-1 (stair skirting one element, range never summed; ORR-007 open with owner).
- Materials: FINISH V7, PLASTER V3; Q-80 A -> UPC-BLACK-BLOCK-001 1.1.0 (T-615 READY).

## Blockers
- PR #4 (owner). Designer items (D-16 / D-63, D-GF-09, D-27, D-33, D-35, D-39, D-43, D-45, D-48, D-53 W02, D-02 CB10
  width, lintel ends, DOME-3 bars, lift-wall height, lift landing head low end, F-T583-1 note 9, F-T589-2, MS1-T winder
  fronts) keep lines HELD, never block integration.

## Open owner items
- PR #4 merge (CRITICAL). ORR-007 stair skirting payable form.
- Freelancer floors / rails workbooks + 1990 spec (owner: coming this week, not blockers); privacy switch; PyMuPDF review after 10 Nov.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone. Stage 2 of the token plan after 10 Nov. Scout paused.
