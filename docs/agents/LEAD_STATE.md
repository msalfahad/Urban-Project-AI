# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 1d311ee5..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 16:15Z, rows changed since), then rewrite.

## Last seen
- engine: 1d311ee5 (unchanged since 12:00; candidate of record ARCH_TAKEOFF_V3.0.46 35d70129; registry
  BOQ_FAMILY_MASTER 1.43.0; released V2.9 + route G unchanged)
- board: this run's final commit (Lead 2026-11-03 16:17, after 89d1d158)
- last Lead run: 2026-11-03 16:14-16:25 UTC (run session_01E6cPnbYqwbqEVPJxD1LUuX)

## Unclosed runs found 16:17 (INCOMPLETE, cause not known, nothing pushed)
- Worker 3 STARTED 13:01 (T-350 r3 CLAIMED 13:02); lock expired 16:01. Verifier STARTED 13:52; lock expired 15:51.
- Check next run that the 16:49 Checker and 16:59 Worker 3 runs started normally (expired locks taken).

## Live rows
- READY 4: T-455 (13:02), T-490 (13:33), T-489 (14:54), T-491 (15:32); all delay CHECKER-RUNS (T-489 + EVIDENCE).
- TODO 4: W1 T-443 r3; W2 T-492 (guard fix), T-486; W3 T-350 r3 (re-claim).
- QUEUED: W1 T-483, T-480, T-423, T-424, T-310, T-314, T-364, T-363, T-372; W2 T-460; W3 T-487, T-488, T-382,
  T-474 p2, T-468.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-443, T-483, T-480, T-423, T-424, T-310, T-314, T-364, T-363, T-372 |
  A (worker 2): T-492, T-486, T-460 | I (worker 3): T-350, T-487, T-488, T-382, T-474, T-468

## Top 5 priorities
1. T-492 guard fix -> unblocks Gate B of T-443 r3 and T-350 r3 (Checker merges T-492 first).
2. Stream F: T-443 r3 -> T-483 -> T-480 -> T-423 / T-424. 4 Nov review (first run after 00:00 4 Nov): stream F has
   delivered 0 packages since 22:50 2 Nov; if still under 2 packages, move T-310 / T-314 to worker 2 under the
   merge-order rule (decide, then record).
3. Stream S: T-350 r3 -> T-487 lintels -> T-488 blockwork wiring -> T-382 -> T-474 p2.
4. Checker: clear the 4 READY (T-455 first); verdicts of T-490 / T-491 may need follow-ups: 1F round-stair quarter
   landing 1.3525 m2 has no B7 line; 2F arrival 4.875 m2 only inside a HELD bound; net fence HELD (no gate source).
5. Materials wiring row for T-453 / T-454 / T-455 / T-489 tables once T-488 lands (not yet written).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; whichever is READY second rebases on the first merged
  candidate; version (candidate and BOQ_FAMILY_MASTER) allotted at merge. One package per stream at a time.
- Each worker keeps at least one non-candidate (research / tool) TODO behind its stream package.
- A worker run that skips its first-in-order stream package must state why in its final line (2026-11-03 04:15).
- Queue check treats any 'after T-nnn' / 'behind T-nnn' and list position as WAITING; status word first; a new row
  needs separate Task and Status cells (9 fields) or the check flags UNCLEAR_STATUS.
- `board check` pulls first: commit the edits before running it. Write stamps from `date -u`.
- Owner questions on non-critical material parameters are withdrawn into level-4 estimate tasks unless every source
  was read in full (Q-79 -> T-489, 2026-11-03 12:18).
- F-C-T443-1 (2026-11-03 16:17): a package is 'merged' only when its commit reached the working branch through a merge;
  guard defects are fixed once (T-492), never by each package; no package edits tests/t485_*.
- Element register rulings 2026-11-03: RC LINTEL vs host masonry; FOUNDATION BACKFILL displacement; TOP-STOREY WALL
  HEIGHT vs ROOF BUILD-UP; ENTRANCE / STAIR-HALL STONE FLOOR (one owner trade per space).

## Blockers
- None from the owner. Designer items (D-27, D-33, D-35, D-39, D-43) keep lines HELD, never block integration.

## Open owner items
- Kuwait 1990 spec over the 10 MB connector limit (plastering chapter unread) -> a copy under 6 MB (NEEDS FIXING).
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
