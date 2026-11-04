# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log aa79343a..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 12:15Z 4 Nov, rows changed since), then rewrite.

## Last seen
- engine: aa79343a (T-506 merge; candidate of record ARCH_TAKEOFF_V3.0.53 36863f6c; registry BOQ_FAMILY_MASTER
  1.50.0; released V2.9 + route G unchanged).
- board: this run's final commit (Lead 2026-11-04 12:19, after bfaad368)
- last Lead run: 2026-11-04 12:15-12:30 UTC (run session_01E6cPnanxEpJ1ZJ6ZRdZmXY)

## Run health
- Worker 2 (fired 10:39) and Worker 3 (fired 10:59): scheduler FAILED USAGE_LIMIT_REACHED 11:14, no final line =
  INCOMPLETE, nothing pushed / lost; T-310 r5 and T-468 set back to TODO. Their locks (to 12:40 / 13:00) may make the
  12:39 / 12:59 runs end IDLE on AGENT_ENV LOCKED: expected. If the usage limit recurs, report it (owner cadence choice).
- OPEN at 12:19: Worker 1 STARTED 11:20 (T-460 CLAIMED 11:21, lock to 13:20, scheduler PENDING).

## Live rows
- READY 0. CLAIMED 1: T-460 (worker 1, 11:21).
- TODO 5: W1 T-480; W2 T-310 r5, T-500; W3 T-488, T-468.
- QUEUED: W1 T-508, T-423, T-424, T-364, T-363, T-372; W2 T-507, T-314, T-502; W3 T-498, T-509, T-382, T-474 p2.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-460, T-480, T-508, T-423, T-424, T-364, T-363, T-372 |
  A (worker 2): T-310, T-507, T-500, T-314, T-502 | I (worker 3): T-488, T-468, T-498, T-509, T-382, T-474
- TODO below 8 by design: one candidate package per worker; no other unblocked row moves a line.

## Top 5 priorities
1. Stream S: T-488 blockwork wiring (worker 3, 12:59 or 14:59) -> T-498 materials -> T-509 disposal.
2. Stream F: T-310 r5 (worker 2) and T-480 (worker 1) in parallel, READY second rebases; then T-507, T-508.
3. Checker: T-310 r5, T-488, T-480 as they come (Gate B); T-460 / T-500 / T-468 Gate A; T-180 rest of every run.
4. 10 Nov: about 14 packages / 6 days; watch 2+ Gate B merges per 12 h (3 achieved 00:20-12:19).
5. Usage limit: if another run dies on it, put it in NEEDS FIXING with the count and the slots lost.

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; whichever is READY second rebases on the first merged
  candidate; version (candidate and BOQ_FAMILY_MASTER) allotted at merge. One candidate package per worker at a time.
  Two stream F packages of different workers on the same hub / master are NOT a file conflict (READY second rebases).
- Each worker keeps at least one non-candidate (research / tool) TODO behind its stream package.
- A worker run that skips its first-in-order stream package must state why in its final line (2026-11-03 04:15).
- Queue check treats 'after T-nnn' / list position as WAITING; status word first; 9-field rows; history text in a
  status cell must not say 'after T-nnn' for a met wait (write 'behind ... (history, met)').
- `board check` pulls first: commit the edits before running it. Write stamps from `date -u`.
- Owner questions on non-critical material parameters are withdrawn into level-4 estimate tasks unless every source
  was read in full (Q-79 -> T-489, 2026-11-03 12:18).
- F-C-T443-1: a package is 'merged' only when its commit reached the working branch through a merge.
- Long Gate B packages: pushed stages, hand back INCOMPLETE below 40 min of lock.
- Element register rulings: RC LINTEL vs host masonry; FOUNDATION BACKFILL; TOP-STOREY WALL HEIGHT vs ROOF BUILD-UP;
  ENTRANCE / STAIR-HALL STONE FLOOR; STAIR LANDING; POOL-COURT SLAB WP (B8-06); STAIR SKIRTING vs ROOM SKIRTING;
  EXCAVATION ZONES; SKIRTING BEHIND FITTED JOINERY (T-460 classifies the 2.800 lm).
- Lessons rows 2026-11-04 ADOPTED: trench zone overlap, HELD subtotal R-T499-1, disposal balance, skirting under raised
  sills (T-483); 12:19: one producer per material key (T-506), skirting only on a floor (T-501), WP applicability for
  every exposed slab (T-494).
- Materials wiring reads FINISH_MATERIALS_TABLE_V5 bound_subtotal() and PLASTER_MATERIALS_TABLE_V3; producer roles from
  T-506 (T-453 r2 produces black mortar; T-367 READ / BESIDE); disposal loss never inside payable (F-C-T505-1).
- F-C-T487-1: lintel printed bars stay a named HELD rebar component on B9-02 (carried in T-488).

## Blockers
- None from the owner. Designer items (D-27, D-33, D-35, D-39, D-43) keep lines HELD, never block integration.

## Open owner items
- Kuwait 1990 spec over the 10 MB connector limit (plastering chapter unread) -> a copy under 6 MB (NEEDS FIXING).
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
