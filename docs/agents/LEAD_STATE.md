# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log c814c55d..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 20:14Z, rows changed since), then rewrite.

## Last seen
- engine: c814c55d (T-443 r3 merge; candidate of record ARCH_TAKEOFF_V3.0.47 e86a53a8; registry BOQ_FAMILY_MASTER
  1.44.0; released V2.9 + route G unchanged)
- board: this run's final commit (Lead 2026-11-03 20:18, after 5af7ad16)
- last Lead run: 2026-11-03 20:14-20:30 UTC (run session_01E6cPncTn83HkFBUb42otRP)

## Unclosed runs found 20:18 (INCOMPLETE, cause not known, nothing pushed)
- Worker 3 STARTED 17:03 (T-350 r3 CLAIMED 17:02); lock expired 20:02. Second dead T-350 r3 claim (13:01 too).
- Check next run: did the 20:59 Worker 3 run push stage 1 of T-350 r4 to agents/task-T-350 (head was 438f3b88)?
  If a third run dies with nothing pushed: report as NEEDS FIXING (run reliability) with the evidence.

## Live rows
- READY 1: T-486 (19:11, CHECKER-RUNS).
- TODO 5: W1 T-483 (stream F), T-495 (non-candidate); W2 T-493; W3 T-350 r4 (staged), T-496 (non-candidate).
- QUEUED: W1 T-480, T-423, T-424, T-310, T-314, T-364, T-363, T-372; W2 T-494 (after T-486 MERGED), T-460 (after
  T-483); W3 T-487, T-488, T-382, T-474 p2, T-468.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-483, T-495, T-480, T-423, T-424, T-310, T-314, T-364, T-363, T-372 |
  A (worker 2): T-493, T-494, T-460 | I (worker 3): T-350, T-496, T-487, T-488, T-382, T-474, T-468

## Top 5 priorities
1. T-350 r4 stage pushes (stream S unblocked only by it; 0 packages since T-419 at 09:35).
2. Stream F: T-483 -> T-480 -> T-423 / T-424. 4 Nov review (first run after 00:00 4 Nov): stream F delivered 1
   (T-443) since 22:50 2 Nov; if under 2 by then, move T-310 / T-314 to worker 2 under the merge-order rule.
3. Checker: T-486 then whichever Gate B is READY; T-494 opens when T-486 merges.
4. Materials: T-496 binding map, then a wiring row after T-488 for T-453 / T-454 / T-455 / T-489 tables.
5. T-491 site preparation and T-495 outdoor material rows need an integration row once stream S frees.

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
- F-C-T443-1: a package is 'merged' only when its commit reached the working branch through a merge (T-492 MERGED).
- Long Gate B packages (2026-11-03 20:18): pushed stages, hand back INCOMPLETE below 40 min of lock (T-350 r4).
- Element register rulings 2026-11-03: RC LINTEL vs host masonry; FOUNDATION BACKFILL displacement; TOP-STOREY WALL
  HEIGHT vs ROOF BUILD-UP; ENTRANCE / STAIR-HALL STONE FLOOR; STAIR LANDING at a flight end (B7 owner,
  FLOOR_OR_LANDING); POOL-COURT SLAB WP (B8-06).

## Blockers
- None from the owner. Designer items (D-27, D-33, D-35, D-39, D-43) keep lines HELD, never block integration.

## Open owner items
- Kuwait 1990 spec over the 10 MB connector limit (plastering chapter unread) -> a copy under 6 MB (NEEDS FIXING).
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
