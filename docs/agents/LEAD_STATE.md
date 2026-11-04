# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 416392e8..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 04:12Z 4 Nov, rows changed since), then rewrite.

## Last seen
- engine: 416392e8 (T-499 merge; candidate of record ARCH_TAKEOFF_V3.0.50 d40c4ec5; registry BOQ_FAMILY_MASTER
  1.47.0; released V2.9 + route G unchanged). t485 T-443 stale-pending still FAILS on the working branch (fix in T-483 r2).
- board: this run's final commit (Lead 2026-11-04 04:14, after 8ca5d025)
- last Lead run: 2026-11-04 04:12-04:25 UTC (run session_01E6cPncXz8PPBacyuYuPEdV)

## Run health
- Every run since 00:20 closed with a final line. OPEN at 04:14: Worker 1 STARTED 03:21 (T-483 r2 CLAIMED 03:23, lock to
  05:20): if it has no final line by the next run, report INCOMPLETE and check agents/task-T-483 for pushed work.
- This Lead session's venv had pytest (selfcheck PASS); the 00:20 venv fault did not recur.

## Live rows
- READY 0.
- CLAIMED 1: T-483 r2 (worker 1, 03:23; rebase on 416392e8, next free version).
- TODO 7: W1 T-501, T-505; W2 T-310 r3 (rebase only), T-494, T-500; W3 T-487, T-504.
- QUEUED: W1 T-480, T-423, T-424, T-364, T-363, T-372; W2 T-314, T-502, T-460; W3 T-488, T-498, T-382, T-474 p2, T-468.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-483, T-501, T-505, T-480, T-423, T-424, T-364, T-363, T-372 |
  A (worker 2): T-310, T-494, T-500, T-314, T-502, T-460 | I (worker 3): T-487, T-504, T-488, T-498, T-382, T-474, T-468

## Top 5 priorities
1. Stream F: T-483 r2 then T-310 r3 (both rebase on 416392e8; whichever is READY second rebases again). 0 stream F merges
   since 3 Nov 20:12.
2. Stream S: T-487 (B9-02 lintel lines, missing category), then T-488 blockwork wiring.
3. Checker: T-483 r2 -> T-310 r3 -> T-487; Gate A T-494 first among pieces (omission), then T-504.
4. Materials: T-504 (plaster table V3) -> T-498 after T-488; T-500 bed mortar; T-505 disposal loss terms.
5. 10 Nov AT RISK: about 14 packages left. 4 Nov 12:00 review: if fewer than 3 packages merged since 00:20 (count so
   far: 1 package, T-497), propose the owner a scope order for 10 Nov (which trades go in as HELD lines).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; whichever is READY second rebases on the first merged
  candidate; version (candidate and BOQ_FAMILY_MASTER) allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least one non-candidate (research / tool) TODO behind its stream package.
- A worker run that skips its first-in-order stream package must state why in its final line (2026-11-03 04:15).
- Queue check treats any 'after T-nnn' / 'behind T-nnn' and list position as WAITING; status word first; a new row
  needs separate Task and Status cells (9 fields) or the check flags UNCLEAR_STATUS.
- `board check` pulls first: commit the edits before running it. Write stamps from `date -u`.
- Owner questions on non-critical material parameters are withdrawn into level-4 estimate tasks unless every source
  was read in full (Q-79 -> T-489, 2026-11-03 12:18).
- F-C-T443-1: a package is 'merged' only when its commit reached the working branch through a merge.
- Long Gate B packages: pushed stages, hand back INCOMPLETE below 40 min of lock (worked for T-350 r4 and T-310 r2).
- Element register rulings 2026-11-03: RC LINTEL vs host masonry; FOUNDATION BACKFILL displacement; TOP-STOREY WALL
  HEIGHT vs ROOF BUILD-UP; ENTRANCE / STAIR-HALL STONE FLOOR; STAIR LANDING (B7 owner, FLOOR_OR_LANDING); POOL-COURT
  SLAB WP (B8-06). 2026-11-04: STAIR SKIRTING vs ROOM SKIRTING; EXCAVATION ZONES (one owner zone per m3).
- Lessons rows 2026-11-04 ADOPTED: trench zone overlap (T-497), HELD subtotal R-T499-1 (T-499), disposal balance (T-503).
- Wiring of materials reads FINISH_MATERIALS_TABLE_V5 bound_subtotal() (F-C-T499-1) and needs a producer role per
  binding (F-C-T496-1); disposal reuse ends need T-505 loss terms first.

## Blockers
- None from the owner. Designer items (D-27, D-33, D-35, D-39, D-43) keep lines HELD, never block integration.

## Open owner items
- Kuwait 1990 spec over the 10 MB connector limit (plastering chapter unread) -> a copy under 6 MB (NEEDS FIXING).
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
