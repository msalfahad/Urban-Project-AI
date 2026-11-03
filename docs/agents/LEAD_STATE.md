# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 983b75f4..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 00:12Z, rows changed since), then rewrite.

## Last seen
- engine: 983b75f4 (candidate of record ARCH_TAKEOFF_V3.0.44 json 8b2fe2b6; released V2.9 + route G unchanged)
- board: this run's final commit (Lead 2026-11-03 00:16, after 303cc3de)
- last Lead run: 2026-11-03 00:12-00:25 UTC (run unknown)

## Open runs at 00:16 (check their final lines next run)
- Verifier STARTED 23:51 (merged T-464 23:56, T-383 23:59; lock still valid). No final line next run = INCOMPLETE.

## Live rows
- READY 2: T-478 r2 (stream S Gate B, V3.0.45 5972888b on V3.0.44), T-452 (generic scorer, 226398b2).
- TODO 9: W1 T-443 (stream F Gate B), T-457, T-449 (Gate A remainder); W2 T-466, T-481 (new), T-461, T-453 part 1;
  W3 T-479 (builds on the T-478 head, hands in after T-478's verdict).
- QUEUED: T-480 (after T-443), T-423 (after T-480), T-424, T-310, T-314, T-364, T-363, T-372; T-419, T-382, T-474 p2,
  T-468; T-454, T-455, T-460.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472. Row kept open: T-449 wiring (stream S after T-382).
- Lane order: W1 T-443, T-457, T-449, T-480, T-423, T-424, T-310, T-314, T-364, T-363, T-372, T-452 |
  W2 T-466, T-481, T-461, T-453, T-454, T-455, T-460 | W3 T-479, T-419, T-382, T-474, T-468

## Top 5 priorities
1. Stream S: T-478 Gate B -> T-479 -> T-419 -> T-382 (+T-459) -> T-474 p2.
2. Stream F: T-443 -> T-480 -> T-423 / T-424; on 4 Nov decide whether to pull T-314 / T-364 / T-363 / T-372 forward.
3. T-466 (P0 known failures, L4) and T-481 (skirting sills / dressing, feeds stream F).
4. Materials: T-453 part 1 ledger (T-448 calculators), then T-454 / T-455; T-452 verdict (step 6).
5. T-180 closures; T-132 restate after T-478 merges; export re-run for the T-383 WP whole lines.

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; whichever is READY second rebases on the first merged
  candidate; version (candidate and BOQ_FAMILY_MASTER) allotted at merge. One package per stream at a time.
- Each worker keeps at least one non-candidate (research / tool) TODO behind its stream package, so a stream wait never
  empties its lane (fault of 2 Nov 20:17).
- Queue check reads 'after T-nnn' anywhere in the status cell: write history as 'behind T-nnn'.
- Write stamps from `date -u` at the moment of writing (this run first wrote 00:20, corrected to 00:16).

## Blockers
- None from the owner. Designer items keep lines HELD, never block integration.

## Open owner items
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1, unblocked); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov.
