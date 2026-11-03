# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 1d311ee5..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 12:14Z, rows changed since), then rewrite.

## Last seen
- engine: 1d311ee5 (candidate of record ARCH_TAKEOFF_V3.0.46 35d70129; registry BOQ_FAMILY_MASTER 1.43.0; released
  V2.9 + route G unchanged)
- board: this run's final commit (Lead 2026-11-03 12:20, after ef0f8848)
- last Lead run: 2026-11-03 12:14-12:25 UTC (run unknown)

## Open runs at 12:20 (check their final lines next run)
- Worker 1 STARTED 11:20 (T-443 r2 rebase CLAIMED 11:21). No final line = INCOMPLETE.

## Live rows
- READY 0. CLAIMED: T-443 r2 (worker 1, stream F, rebase onto V3.0.46).
- TODO 6: W1 T-490; W2 T-455, T-489, T-486; W3 T-350 r3, T-491.
- QUEUED: W1 T-483 (after T-443), T-480, T-423, T-424, T-310, T-314, T-364, T-363, T-372; W2 T-460 (after T-443 +
  T-483); W3 T-487 (after T-350 r3), T-488 (after T-487), T-382 (after T-488), T-474 p2, T-468.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-443, T-490, T-483, T-480, T-423, T-424, T-310, T-314, T-364, T-363, T-372 |
  A (worker 2): T-455, T-489, T-486, T-460 | I (worker 3): T-350, T-491, T-487, T-488, T-382, T-474, T-468

## Top 5 priorities
1. Stream F: T-443 r2 -> T-483 -> T-480 -> T-423 / T-424. 4 Nov review (first run after 00:00 4 Nov): stream F has
   delivered 0 packages since 22:50 2 Nov; if still under 2 packages, move T-310 / T-314 to worker 2 under the
   merge-order rule (decide, then record).
2. Stream S: T-350 r3 (earthworks wiring + F-C-T485-1 in its registry version) -> T-487 lintels -> T-488 blockwork
   wiring -> T-382 -> T-474 p2.
3. Checker: Gate B T-443 r2 / T-350 r3 as they come; then Gate A pieces; T-180 slot otherwise.
4. Materials: T-455 tiles, T-489 plaster mix estimate (replaces Q-79); wiring of T-453 / T-454 tables needs a row
   once T-488 lands (not yet written).
5. Missing categories: T-490 B3-03 stone floor, T-491 B1-01 / B1-07 site preparation, T-486 balcony WP.

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; whichever is READY second rebases on the first merged
  candidate; version (candidate and BOQ_FAMILY_MASTER) allotted at merge. One package per stream at a time.
- Each worker keeps at least one non-candidate (research / tool) TODO behind its stream package.
- A worker run that skips its first-in-order stream package must state why in its final line (2026-11-03 04:15).
- Queue check treats any 'after T-nnn' / 'behind T-nnn' and list position as WAITING; status word first.
- `board check` pulls first: commit the edits before running it. Write stamps from `date -u`.
- Owner questions on non-critical material parameters are withdrawn into level-4 estimate tasks unless every source
  was read in full (Q-79 -> T-489, 2026-11-03 12:18).
- Element register rulings 2026-11-03: RC LINTEL vs host masonry; FOUNDATION BACKFILL displacement; TOP-STOREY WALL
  HEIGHT vs ROOF BUILD-UP (structural roof underside, HELD on D-39 where unprinted); ENTRANCE / STAIR-HALL STONE FLOOR
  (one owner trade per space).

## Blockers
- None from the owner. Designer items (D-27, D-33, D-35, D-39, D-43) keep lines HELD, never block integration.

## Open owner items
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
