# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log f3fb62de..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 20:14Z, rows changed since), then rewrite.

## Last seen
- engine: f3fb62de (candidate of record ARCH_TAKEOFF_V3.0.43 json 6f534d5e; released V2.9 + route G unchanged)
- board: this run's final commit (Lead 2026-11-02 20:17, after c35d822b)
- last Lead run: 2026-11-02 20:13-20:30 UTC (session_01E6cPndQBbdi5ERUqjekRPB)

## Open runs at 20:17 (check their final lines next run)
- Worker 1 STARTED 19:21, T-422 CLAIMED 19:27 (lock to 21:20). Verifier STARTED 19:51, T-465 r3 REJECTED 19:57
  committed, no final line yet (lock to 21:50). Either without a final line next run = INCOMPLETE: report it.

## Live rows
- READY 2: T-474 part 1 (formwork census, be354f35), T-448 (materials rulebook, 8179877f) -> classify from verdicts.
- CLAIMED 1: T-422 (stream F, worker 1).
- TODO 5: worker 1 T-452; worker 2 T-465 r4, T-464, T-383; worker 3 T-478.
- QUEUED new: T-479 (registry + verdict binding, after T-478), T-480 (B7-09 handrails, after T-422).
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- MERGED rows kept open: T-449 (wiring, round 3), T-459 (wiring in T-382).
- Lane order: W1 T-422, T-452, T-443, T-480, T-423, T-424, T-310, T-314, T-364, T-363, T-372, T-449, T-457 |
  W2 T-465, T-464, T-383, T-466, T-461, T-460, T-453..T-455 | W3 T-478, T-419, T-479, T-382, T-474 (p2), T-468

## Top 5 priorities
1. Stream S T-478 (verified pits 12.734 m3 into the candidate) -> T-419 -> T-479 -> T-382 (+T-459) -> T-474 p2.
2. Stream F T-422 Gate B (first finishes package) -> T-443 -> T-480; on 4 Nov decide whether to pull T-314 / T-364 /
   T-363 / T-372 ahead of T-423 / T-424.
3. Gate A T-474 p1 (formwork, unblocks p2) and T-448 (materials step 5; check lintel > 4.00 m FLAG vs handoff 3.70 m
   opening threshold, bearing 0.15 min vs 0.20 default).
4. T-465 r4 (fractional /Widths) -> then the owner PyMuPDF decision can be put.
5. T-180 closures; T-132 restate after the next candidate-line move (T-478 or T-422).

## Rules decided (keep)
- Shared files: T-422 and T-478 build without them; whichever is READY second rebases on the first merged candidate;
  version allotted at merge. One package per stream at a time.
- Queue check reads 'after T-nnn' anywhere in the status cell (history too): write history as 'behind T-nnn'.
- Write stamps from `date -u` at the moment of writing.

## Blockers
- None from the owner. Designer items keep lines HELD, never block integration.

## Open owner items
- Repository privacy switch; released-path PyMuPDF decision (after T-465 r4); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov.
