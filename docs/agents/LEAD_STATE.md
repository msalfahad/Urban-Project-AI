# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log ab6bd617..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 16:14Z, rows changed since), then rewrite.

## Last seen
- engine: ab6bd617 (candidate of record ARCH_TAKEOFF_V3.0.42 json 1793266d; released V2.9 + route G unchanged)
- board: this run's final commit (Lead 2026-11-02 16:18, after 922fca97)
- last Lead run: 2026-11-02 16:13-16:25 UTC (session_01E6cPnamaP2wyiegxNGwmzL)

## Live rows (READY 3, CLAIMED 0 at 16:16)
- READY: T-350 (Gate B, V3.0.43 earthworks, 16adf256), T-471 (EIMP part 2, 44a3fdb9), T-475 (lift marble, 2e7be547)
  -> classify WORKED / PARTIAL / FAILED from the Checker verdicts next run. T-471 findings to act on after the verdict:
  2 candidate lines in no family (registry gap -> lane A row), ground slab MEASURED not HELD, line-id map after rebuild.
- TODO 8: worker 1 (stream F) T-422 (build now, READY after T-350 merges), T-476, T-452; worker 2 T-448, T-465 r3,
  T-464; worker 3 (stream S) T-353 (build now, READY after T-350 merges), T-474 part 1
- QUEUED new: T-478 CONC.BLINDING integration (stream S, after T-353)
- IN PROGRESS: T-180 (Checker standing slot). PAUSED: T-450 part 2, T-451, T-472
- MERGED rows kept open: T-449 (wiring, round 3), T-459 (wiring in T-382)
- Lane order: W1 T-422, T-476, T-452, T-443, T-423, T-424, T-310, T-314, T-364, T-363, T-372, T-449, T-457 |
  W2 T-448, T-465, T-464, T-466, T-383, T-461, T-460, T-453..T-455 | W3 T-353, T-474, T-478, T-419, T-382, T-468

## Top 5 priorities
1. T-350 Gate B (first stream S package) -> unblocks T-422 and T-353 READY.
2. T-471 Gate A (EIMP, critical path step 1; target validated by 8 Nov).
3. Stream S T-353 -> T-478 (verified pits 12.734 m3 into the candidate) -> T-419 -> T-382 (+T-459) -> T-474 p2.
4. Stream F T-422 -> T-443 ...; on 4 Nov decide whether to pull T-314 / T-364 / T-363 / T-372 ahead of T-423 / T-424.
5. Materials T-448 (step 5); T-180 closures; restate T-132 after T-350 merges.

## Rules decided (keep)
- Shared files after T-350 merges: T-422 and T-353 build without them; whichever is READY second rebases on the first
  merged candidate; version allotted at merge.
- Queue check reads 'after T-nnn' anywhere in the status cell (history too): write history as 'behind T-nnn'.
- Write stamps from `date -u` at the moment of writing.

## Blockers
- None from the owner. Designer items keep lines HELD, never block integration.
- Watch: Checker slot 15:49 wrote no STARTED line by 16:16 (check RUN_LOG / scheduler next run).

## Open owner items
- Repository privacy switch; released-path PyMuPDF decision (after T-465 r3); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov.
