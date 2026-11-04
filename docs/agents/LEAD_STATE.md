# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 5de697ff..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 00:13Z 4 Nov, rows changed since), then rewrite.

## Last seen
- engine: 5de697ff (T-350 r4 merge; candidate of record ARCH_TAKEOFF_V3.0.48 33a81c53; registry BOQ_FAMILY_MASTER
  1.45.0; released V2.9 + route G unchanged). t485 T-443 stale-pending FAILS on the working branch (fix in T-483 r2).
- board: this run's final commit (Lead 2026-11-04 00:20, after cf49eb27)
- last Lead run: 2026-11-04 00:13-00:35 UTC (run session_01E6cPndgDGLgUD2cFsQG4Gc)

## Run health
- Every run since 20:14 3 Nov closed with a final line. Worker 1 23:20 IDLE-equivalent (0 TODO on the board).
- This Lead session: .work/venv has no pytest (selfcheck t061 FAIL); Verifier 21:52 saw git network hangs > 120 s.
  If a worker or the Checker reports the same venv fault, it is NEEDS FIXING (environment setup).

## Live rows
- READY 1: T-496 (23:14, CHECKER-RUNS).
- TODO 8: W1 T-483 r2 (rebase V3.0.49 + t485 gate fix), T-501, T-503; W2 T-310 (moved), T-494, T-500;
  W3 T-497 (trench fix), T-499.
- QUEUED: W1 T-480, T-423, T-424, T-364, T-363, T-372; W2 T-314 (moved), T-502, T-460; W3 T-487, T-488, T-498,
  T-382, T-474 p2, T-468.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-483, T-501, T-503, T-480, T-423, T-424, T-364, T-363, T-372 |
  A (worker 2): T-310, T-494, T-500, T-314, T-502, T-460 | I (worker 3): T-497, T-499, T-487, T-488, T-498, T-382,
  T-474, T-468

## Top 5 priorities
1. T-483 r2 (stream F + t485 gate fix) and T-497 (stream S trench fix): both Gate B, first in their lanes.
2. T-310 on worker 2 (4 Nov review applied 00:20); then T-314, T-502.
3. Checker: T-496 first, then whichever package is READY (T-483 r2 first).
4. Materials: T-496 verdict -> T-499 / T-500 pieces -> T-498 wiring after T-488 (mortar reconciliation T-367 vs T-453).
5. 10 Nov AT RISK: about 15 candidate packages left; next review 4 Nov 12:00: if fewer than 3 packages merged since
   00:20, propose the owner a scope order for 10 Nov (which trades go in as HELD lines) in the Lead report.

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
- Long Gate B packages: pushed stages, hand back INCOMPLETE below 40 min of lock (worked for T-350 r4).
- Element register rulings 2026-11-03: RC LINTEL vs host masonry; FOUNDATION BACKFILL displacement; TOP-STOREY WALL
  HEIGHT vs ROOF BUILD-UP; ENTRANCE / STAIR-HALL STONE FLOOR; STAIR LANDING (B7 owner, FLOOR_OR_LANDING); POOL-COURT
  SLAB WP (B8-06). 2026-11-04: STAIR SKIRTING vs ROOM SKIRTING (B7-07 / 08 raking, FIN.SKIRTING level);
  EXCAVATION ZONES (one owner zone per m3, others subtract by geometry).
- Lessons row 2026-11-04 (trench zone overlap) PROPOSED, adopted when T-497 merges.

## Blockers
- None from the owner. Designer items (D-27, D-33, D-35, D-39, D-43) keep lines HELD, never block integration.

## Open owner items
- Kuwait 1990 spec over the 10 MB connector limit (plastering chapter unread) -> a copy under 6 MB (NEEDS FIXING).
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
