# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 8ccf69b3..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 04:12Z, rows changed since), then rewrite.

## Last seen
- engine: 8ccf69b3 (candidate of record ARCH_TAKEOFF_V3.0.45 5972888b; released V2.9 + route G unchanged)
- board: this run's final commit (Lead 2026-11-03 04:15, after a89ce88c)
- last Lead run: 2026-11-03 04:12-04:30 UTC (run unknown)

## Open runs at 04:15 (check their final lines next run)
- Worker 3 STARTED 03:00 (T-479 CLAIMED, lock to 06:00, scheduler PENDING). No final line next run = INCOMPLETE.

## Live rows
- READY 2: T-481 (skirting sills census, 02:58), T-457 (wet-wall bed, 04:05). Both Gate A, CHECKER-RUNS.
- CLAIMED: T-479 (worker 3, 03:00).
- TODO 6: W1 T-452 r2 (t212 classification fix), T-443 (stream F Gate B, MUST be next; skipped by the 01:20 and 03:20
  runs), T-482 (new, blockwork wiring conditions); W2 T-461, T-453 part 1; W3 T-419 (build on 8ccf69b3, hand in after T-479).
- QUEUED: T-480 (after T-443), T-423, T-424, T-310, T-314, T-364, T-363, T-372; T-382, T-474 p2, T-468; T-454, T-455, T-460.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472. T-449 MERGED r3; wiring open behind T-482 / T-382.
- Lane order: W1 T-452, T-443, T-482, T-480, T-423, T-424, T-310, T-314, T-364, T-363, T-372, T-457 |
  W2 T-481, T-461, T-453, T-454, T-455, T-460 | W3 T-479, T-419, T-382, T-474, T-468

## Top 5 priorities
1. Stream F: T-443 actually claimed (check worker 1's 05:20 run); then T-480 -> T-423 / T-424; 4 Nov decision on
   pulling T-314 / T-364 / T-363 / T-372 forward.
2. Stream S: T-479 -> T-419 -> T-382 (+T-459) -> T-474 p2.
3. Checker: T-481, T-457 verdicts; SCOREBOARD v2 restatement for V3.0.45 CONC.BLINDING (carried).
4. Materials: T-453 part 1, T-482 before blocks are priced; T-454 / T-455.
5. T-452 r2 (step 6); T-180 closures (CONC.BLINDING pits part closable now).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; whichever is READY second rebases on the first merged
  candidate; version (candidate and BOQ_FAMILY_MASTER) allotted at merge. One package per stream at a time.
- Each worker keeps at least one non-candidate (research / tool) TODO behind its stream package.
- A worker run that skips its first-in-order stream package must state why in its final line (2026-11-03 04:15).
- Queue check reads 'after T-nnn' anywhere in the status cell: write history as 'behind T-nnn'. Status word first
  (T-449 'ROUND 3' flagged UNCLEAR_STATUS).
- `board check` pulls first: commit the edits before running it.
- Write stamps from `date -u` at the moment of writing (this run first wrote 04:25 ahead of the 04:15 clock, corrected).

## Blockers
- None from the owner. Designer items keep lines HELD, never block integration.

## Open owner items
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
